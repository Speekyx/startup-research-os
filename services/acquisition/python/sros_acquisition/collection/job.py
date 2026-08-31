"""One acquisition job, from a task payload to persisted records.

Mission 1.5 §26, §29, §30, §31. This is the function a Celery task calls, kept
out of the worker package so it can be tested without a broker.

**Nothing is reconstructed inside the worker.** `workspace_id`,
`research_session_id` and `correlation_id` come from the payload and are refused
if absent. ADR-005 is explicit: a worker that could resolve "the current
workspace" could resolve the wrong one, and a default here would be a
cross-tenant write waiting for a bug upstream.

**The governance gate runs inside the job, not before it.** A payload cannot
carry an authorization: it would be a serialized permission that outlives the
state it was derived from, and a source suspended between planning and execution
would still be collected. The job loads the registry and builds the
authorization itself, every time.

**Duplicate delivery is safe and is not exactly-once.** Celery is at-least-once
(ADR-004) and this does not pretend otherwise. The second delivery re-collects,
finds every observation unchanged, and moves a timestamp instead of writing a
row (§30).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sros_contracts import AcquisitionErrorCode, ConditionVerification

from ..compliance.authorization import (
    AcquisitionNotAuthorizedError,
    build_authorization,
)
from ..compliance.config import ComplianceConfig, load_compliance
from ..compliance.use_profile import UseProfileNotDeclaredError, declared_use_profile
from ..compliance.verification import ConditionVerificationRecord
from ..registry.catalog import SourceCatalog, load_catalog
from ..registry.models import SourceRecord
from .errors import AcquisitionFailedError, AcquisitionFailure
from .gdelt_web_ngram import (
    GRAM_KINDS,
    GdeltWebNgramCollector,
    NgramBounds,
    WebNgramRequest,
)
from .repositories import PersistenceReport, collector_enabled, persist_drafts
from .transport import HttpxTransport, Transport
from .world_bank import CollectionBounds, WorldBankCollector, WorldBankRequest

__all__ = [
    "AcquisitionJobResult",
    "WebNgramJobPayload",
    "WorldBankJobPayload",
    "run_gdelt_web_ngram_job",
    "run_world_bank_job",
]

_REQUIRED_HEADERS = ("workspace_id", "research_session_id", "correlation_id")


@dataclass(frozen=True)
class WorldBankJobPayload:
    """What a task must carry. Every field is required and none is defaulted."""

    workspace_id: str
    research_session_id: str
    correlation_id: str
    indicators: tuple[str, ...]
    countries: tuple[str, ...] = ("all",)
    start_year: int | None = None
    end_year: int | None = None
    per_page: int = 100
    max_pages: int = 10
    max_records: int = 5_000
    source_id: str = "world-bank"

    @classmethod
    def from_payload(cls, payload: object) -> WorldBankJobPayload:
        """Parse and refuse, in that order.

        A payload missing a correlation header fails here rather than being
        completed with a plausible value -- there is no plausible value for a
        workspace.
        """
        if not isinstance(payload, dict):
            raise ValueError("an acquisition task payload must be a mapping")
        missing = [name for name in _REQUIRED_HEADERS if not payload.get(name)]
        if missing:
            raise ValueError(
                f"acquisition payload is missing required headers: {missing}. A worker "
                "never resolves the workspace itself and never falls back to a default "
                "(ADR-005)"
            )
        indicators = tuple(payload.get("indicators") or ())
        if not indicators:
            raise ValueError("an acquisition payload must name at least one indicator")
        return cls(
            workspace_id=str(payload["workspace_id"]),
            research_session_id=str(payload["research_session_id"]),
            correlation_id=str(payload["correlation_id"]),
            indicators=indicators,
            countries=tuple(payload.get("countries") or ("all",)),
            start_year=payload.get("start_year"),
            end_year=payload.get("end_year"),
            per_page=int(payload.get("per_page") or 100),
            max_pages=int(payload.get("max_pages") or 10),
            max_records=int(payload.get("max_records") or 5_000),
            source_id=str(payload.get("source_id") or "world-bank"),
        )

    @property
    def idempotency_key(self) -> str:
        """Stable over what the job WOULD collect, not over when it was sent.

        Two deliveries of the same logical job share this. The retrieval time is
        deliberately absent: including it would make every redelivery a
        different job, which is the opposite of what §30 asks for.
        """
        parts = (
            self.workspace_id,
            self.source_id,
            ",".join(sorted(self.indicators)),
            ",".join(sorted(self.countries)),
            str(self.start_year),
            str(self.end_year),
        )
        return "|".join(parts)


@dataclass(frozen=True)
class AcquisitionJobResult:
    source_id: str
    collector: str
    persisted: PersistenceReport
    requests_made: int
    pages_read: int
    refused_resources: tuple[str, ...] = ()
    failures: tuple[AcquisitionFailure, ...] = field(default=())
    idempotency_key: str = ""
    # Mission 1.9.3 §33. A paginated API reports pages; a bulk-file collector
    # reports files and rows. Both live here rather than in two result types,
    # because a caller counting records should not have to know which shape of
    # source produced them -- and each collector leaves the other half at zero
    # rather than filling it with a number that means nothing.
    files_requested: int = 0
    files_processed: int = 0
    files_failed: int = 0
    rows_scanned: int = 0
    rows_matched: int = 0

    @property
    def succeeded(self) -> bool:
        return not self.failures

    def to_json(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "collector": self.collector,
            "persisted": self.persisted.to_json(),
            "requests_made": self.requests_made,
            "pages_read": self.pages_read,
            "files_requested": self.files_requested,
            "files_processed": self.files_processed,
            "files_failed": self.files_failed,
            "rows_scanned": self.rows_scanned,
            "rows_matched": self.rows_matched,
            "refused_resources": list(self.refused_resources),
            # Already sanitised: a failure carries a message this codebase wrote
            # and safe diagnostic context, never a body or a stack trace (§33).
            "failures": [f.to_json() for f in self.failures],
            "idempotency_key": self.idempotency_key,
            "succeeded": self.succeeded,
        }


def _recorded_decisions(
    source: SourceRecord, use_profile_id: str, connection_factory: Any, workspace_id: str
) -> tuple[ConditionVerificationRecord, ...]:
    """The operator decisions the registry holds for this (source, profile, review).

    Mission 1.15.6.2. A `HUMAN_CONFIRMATION` is satisfied by a persisted row, so
    a job that never read one would refuse every source whose review carries a
    human condition -- including one an operator had already accepted.

    **Read in its own short connection**, before the authorization, for the same
    reason `collector_enabled` is: a transaction must not be held open across a
    network call.

    A source with no human condition reads nothing. A read that fails supplies
    nothing, and the gate then refuses -- fail-closed, because "the database was
    unreachable" is not "the operator decided".
    """
    review = source.review_for(use_profile_id)
    if review is None or not any(
        condition.verification is ConditionVerification.HUMAN_CONFIRMATION
        for condition in review.required_conditions
    ):
        return ()
    from ..compliance.repositories import read_human_decisions

    with connection_factory(workspace_id) as conn:
        return read_human_decisions(conn, source.source_id, use_profile_id, review.review_version)


def run_world_bank_job(
    payload: object,
    connection_factory: Callable[[str], Any],
    *,
    catalog: SourceCatalog | None = None,
    compliance: ComplianceConfig | None = None,
    # The assessed use profile this job runs under. `None` means "ask the
    # runtime declaration", which is what a worker does; a caller that already
    # knows passes it, which is what a test and the CLI do. There is no
    # DEFAULT PROFILE -- `declared_use_profile()` refuses when nothing is set.
    use_profile: str | None = None,
    transport: Transport | None = None,
    collector: WorldBankCollector | None = None,
    cancelled: Callable[[], bool] | None = None,
    now: Callable[[], datetime] | None = None,
) -> AcquisitionJobResult:
    """Collect, then persist, in the caller's tenant transaction.

    `connection_factory` takes the workspace id and returns a context manager
    yielding a connection already inside a tenant transaction. Passed in rather
    than constructed so this function has no opinion about pooling and no import
    of a driver -- and so a test can supply a rolled-back connection.
    """
    job = WorldBankJobPayload.from_payload(payload)
    sources = catalog or load_catalog()
    rules = compliance or load_compliance()
    source = sources.get(job.source_id)

    def refuse(code: AcquisitionErrorCode, detail: str) -> AcquisitionJobResult:
        return AcquisitionJobResult(
            source_id=job.source_id,
            collector="",
            persisted=PersistenceReport(),
            requests_made=0,
            pages_read=0,
            failures=(
                AcquisitionFailure(
                    code=code,
                    detail=detail,
                    source_id=job.source_id,
                    correlation_id=job.correlation_id,
                ),
            ),
            idempotency_key=job.idempotency_key,
        )

    # The gate, at execution time. A plan made ten minutes ago does not
    # authorise a collection now: a source suspended in between must not be
    # collected because the planner had already decided it could be.
    try:
        profile = use_profile or declared_use_profile()
        context = build_authorization(
            source,
            profile,
            rules,
            decisions=_recorded_decisions(source, profile, connection_factory, job.workspace_id),
        )
    except UseProfileNotDeclaredError as exc:
        # The runtime did not say what it is doing with this source. Refused in
        # the same voice as any other authorization failure, because it is one:
        # a permission decision cannot be made without the question.
        return refuse(AcquisitionErrorCode.AUTHORIZATION_REJECTED, str(exc))
    except AcquisitionNotAuthorizedError as exc:
        return refuse(AcquisitionErrorCode.AUTHORIZATION_REJECTED, "; ".join(exc.reasons))

    # The OPERATIONAL switch, which is a different question from eligibility
    # (§27). Eligible says *may we*; `collector_enabled` says *is it turned on*.
    # Checked here, before anything is fetched, and in its own short connection
    # rather than by holding a transaction open across the network.
    with connection_factory(job.workspace_id) as conn:
        if not collector_enabled(conn, job.source_id):
            return refuse(
                AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                (
                    f"{job.source_id} passes the governance gate and its collector is not "
                    "enabled. Enablement is a separate, deliberate decision "
                    "(`sros-source enable`), and a job must not take it on an operator's "
                    "behalf"
                ),
            )

    worker = collector or WorldBankCollector(transport or HttpxTransport(), now=now)
    result = worker.collect(
        context,
        WorldBankRequest(
            indicators=job.indicators,
            countries=job.countries,
            start_year=job.start_year,
            end_year=job.end_year,
            per_page=job.per_page,
        ),
        workspace_id=job.workspace_id,
        correlation_id=job.correlation_id,
        research_session_id=job.research_session_id,
        bounds=CollectionBounds(max_pages=job.max_pages, max_records=job.max_records),
        cancelled=cancelled,
    )

    persisted = PersistenceReport()
    if result.drafts:
        try:
            with connection_factory(job.workspace_id) as conn:
                persisted = persist_drafts(conn, result.drafts)
        except AcquisitionFailedError:
            raise
        except Exception as exc:  # noqa: BLE001 - normalised, see errors.py
            return AcquisitionJobResult(
                source_id=job.source_id,
                collector=f"{worker.collector_id}@{worker.collector_version}",
                persisted=PersistenceReport(),
                requests_made=result.requests_made,
                pages_read=result.pages_read,
                refused_resources=tuple(result.refused_resources),
                failures=(
                    *result.failures,
                    AcquisitionFailure(
                        code=AcquisitionErrorCode.PERSISTENCE_FAILURE,
                        detail=(
                            f"records were acquired and could not be stored "
                            f"({type(exc).__name__}); nothing was committed"
                        ),
                        source_id=job.source_id,
                        correlation_id=job.correlation_id,
                    ),
                ),
                idempotency_key=job.idempotency_key,
            )

    return AcquisitionJobResult(
        source_id=job.source_id,
        collector=f"{worker.collector_id}@{worker.collector_version}",
        persisted=persisted,
        requests_made=result.requests_made,
        pages_read=result.pages_read,
        refused_resources=tuple(result.refused_resources),
        failures=tuple(result.failures),
        idempotency_key=job.idempotency_key,
    )


@dataclass(frozen=True)
class WebNgramJobPayload:
    """What a GDELT WEB-NGRAM task must carry. Every header is required.

    Mission 1.9.3 §41. **No authorization travels in a payload.** A serialized
    permission outlives the state it was derived from, and a source suspended
    between planning and execution would still be collected; the job rebuilds
    the authorization itself, every time.

    The request fields are the collector's own -- gram kinds and exact source
    bucket labels. There is no host, no path and no filename here either, so a
    payload cannot carry an escape the collector's signature refuses.
    """

    workspace_id: str
    research_session_id: str
    correlation_id: str
    buckets: tuple[str, ...]
    grams: tuple[str, ...] = ("1gram",)
    languages: tuple[str, ...] = ()
    ngrams: tuple[str, ...] = ()
    ngram_prefix: str | None = None
    max_records: int = 5_000
    source_id: str = "gdelt"

    @classmethod
    def from_payload(cls, payload: object) -> WebNgramJobPayload:
        if not isinstance(payload, dict):
            raise ValueError("an acquisition task payload must be a mapping")
        missing = [name for name in _REQUIRED_HEADERS if not payload.get(name)]
        if missing:
            raise ValueError(
                f"acquisition payload is missing required headers: {missing}. A worker "
                "never resolves the workspace itself and never falls back to a default "
                "(ADR-005)"
            )
        buckets = tuple(str(b) for b in payload.get("buckets") or ())
        if not buckets:
            raise ValueError(
                "a WEB-NGRAM payload must name at least one source bucket label. There is "
                "no discovery crawl: a job collects the buckets it was told to (§37)"
            )
        grams = tuple(str(g) for g in payload.get("grams") or ("1gram",))
        unknown = [g for g in grams if g not in GRAM_KINDS]
        if unknown:
            raise ValueError(f"{unknown} is not a reviewed gram kind; known: {sorted(GRAM_KINDS)}")
        prefix = payload.get("ngram_prefix")
        return cls(
            workspace_id=str(payload["workspace_id"]),
            research_session_id=str(payload["research_session_id"]),
            correlation_id=str(payload["correlation_id"]),
            buckets=buckets,
            grams=grams,
            languages=tuple(str(x) for x in payload.get("languages") or ()),
            ngrams=tuple(str(x) for x in payload.get("ngrams") or ()),
            ngram_prefix=str(prefix) if prefix else None,
            max_records=int(payload.get("max_records") or 5_000),
            source_id=str(payload.get("source_id") or "gdelt"),
        )

    @property
    def idempotency_key(self) -> str:
        """Stable over what the job WOULD collect, not over when it was sent.

        The local filters are part of it: two jobs over the same files with
        different filters persist different observations, so they are different
        logical jobs even though they download the same bytes.
        """
        return "|".join(
            (
                self.workspace_id,
                self.source_id,
                ",".join(sorted(self.grams)),
                ",".join(sorted(self.buckets)),
                ",".join(sorted(self.languages)),
                ",".join(sorted(self.ngrams)),
                self.ngram_prefix or "",
            )
        )

    def to_request(self) -> WebNgramRequest:
        return WebNgramRequest(
            buckets=self.buckets,
            grams=self.grams,
            languages=self.languages,
            ngrams=self.ngrams,
            ngram_prefix=self.ngram_prefix,
        )


def run_gdelt_web_ngram_job(
    payload: object,
    connection_factory: Callable[[str], Any],
    *,
    catalog: SourceCatalog | None = None,
    compliance: ComplianceConfig | None = None,
    # The assessed use profile this job runs under. `None` means "ask the
    # runtime declaration", which is what a worker does; a caller that already
    # knows passes it, which is what a test and the CLI do. There is no
    # DEFAULT PROFILE -- `declared_use_profile()` refuses when nothing is set.
    use_profile: str | None = None,
    transport: Any | None = None,
    collector: GdeltWebNgramCollector | None = None,
    bounds: NgramBounds | None = None,
    cancelled: Callable[[], bool] | None = None,
    now: Callable[[], datetime] | None = None,
) -> AcquisitionJobResult:
    """Collect WEB-NGRAM rows, then persist, in the caller's tenant transaction.

    The same shape as `run_world_bank_job` and for the same reasons: the
    governance gate runs at execution time, the operational switch is a separate
    question asked before anything is fetched, and persistence happens in one
    transaction the caller owns.

    **Persistence is all-or-nothing across the job; acquisition is per file**
    (§32, §33). A file that violates the documented contract contributes no
    drafts and is reported as failed, while the files that completed still
    persist. Claiming atomicity across eight independent downloads would be
    claiming something the architecture does not provide.
    """
    job = WebNgramJobPayload.from_payload(payload)
    sources = catalog or load_catalog()
    rules = compliance or load_compliance()
    source = sources.get(job.source_id)

    def refuse(code: AcquisitionErrorCode, detail: str) -> AcquisitionJobResult:
        return AcquisitionJobResult(
            source_id=job.source_id,
            collector="",
            persisted=PersistenceReport(),
            requests_made=0,
            pages_read=0,
            failures=(
                AcquisitionFailure(
                    code=code,
                    detail=detail,
                    source_id=job.source_id,
                    correlation_id=job.correlation_id,
                ),
            ),
            idempotency_key=job.idempotency_key,
        )

    try:
        profile = use_profile or declared_use_profile()
        context = build_authorization(
            source,
            profile,
            rules,
            decisions=_recorded_decisions(source, profile, connection_factory, job.workspace_id),
        )
    except UseProfileNotDeclaredError as exc:
        # The runtime did not say what it is doing with this source. Refused in
        # the same voice as any other authorization failure, because it is one:
        # a permission decision cannot be made without the question.
        return refuse(AcquisitionErrorCode.AUTHORIZATION_REJECTED, str(exc))
    except AcquisitionNotAuthorizedError as exc:
        return refuse(AcquisitionErrorCode.AUTHORIZATION_REJECTED, "; ".join(exc.reasons))

    with connection_factory(job.workspace_id) as conn:
        if not collector_enabled(conn, job.source_id):
            return refuse(
                AcquisitionErrorCode.AUTHORIZATION_REJECTED,
                (
                    f"{job.source_id} passes the governance gate and its collector is not "
                    "enabled. Enablement is a separate, deliberate decision "
                    "(`sros-source enable`), and a job must not take it on an operator's "
                    "behalf"
                ),
            )

    worker = collector or GdeltWebNgramCollector(transport or HttpxTransport(), now=now)
    limits = bounds or NgramBounds(max_records=job.max_records)
    result = worker.collect(
        context,
        job.to_request(),
        workspace_id=job.workspace_id,
        correlation_id=job.correlation_id,
        research_session_id=job.research_session_id,
        bounds=limits,
        cancelled=cancelled,
    )

    def outcome(
        persisted: PersistenceReport, extra: tuple[AcquisitionFailure, ...] = ()
    ) -> AcquisitionJobResult:
        return AcquisitionJobResult(
            source_id=job.source_id,
            collector=f"{worker.collector_id}@{worker.collector_version}",
            persisted=persisted,
            requests_made=result.requests_made,
            pages_read=0,
            refused_resources=tuple(result.refused_resources),
            failures=(*result.failures, *extra),
            idempotency_key=job.idempotency_key,
            files_requested=result.files_requested,
            files_processed=result.files_processed,
            files_failed=result.files_failed,
            rows_scanned=result.rows_scanned,
            rows_matched=result.rows_matched,
        )

    persisted = PersistenceReport()
    if result.drafts:
        try:
            with connection_factory(job.workspace_id) as conn:
                persisted = persist_drafts(conn, result.drafts)
        except AcquisitionFailedError:
            raise
        except Exception as exc:  # noqa: BLE001 - normalised, see errors.py
            return outcome(
                PersistenceReport(),
                (
                    AcquisitionFailure(
                        code=AcquisitionErrorCode.PERSISTENCE_FAILURE,
                        detail=(
                            f"records were acquired and could not be stored "
                            f"({type(exc).__name__}); nothing was committed"
                        ),
                        source_id=job.source_id,
                        correlation_id=job.correlation_id,
                    ),
                ),
            )
    return outcome(persisted)


def utc_now() -> datetime:
    return datetime.now(UTC)
