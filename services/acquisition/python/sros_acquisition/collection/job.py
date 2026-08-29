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

from sros_contracts import AcquisitionErrorCode

from ..compliance.authorization import (
    AcquisitionNotAuthorizedError,
    build_authorization,
)
from ..compliance.config import ComplianceConfig, load_compliance
from ..registry.catalog import SourceCatalog, load_catalog
from .errors import AcquisitionFailedError, AcquisitionFailure
from .repositories import PersistenceReport, collector_enabled, persist_drafts
from .transport import HttpxTransport, Transport
from .world_bank import CollectionBounds, WorldBankCollector, WorldBankRequest

__all__ = ["AcquisitionJobResult", "WorldBankJobPayload", "run_world_bank_job"]

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
            "refused_resources": list(self.refused_resources),
            # Already sanitised: a failure carries a message this codebase wrote
            # and safe diagnostic context, never a body or a stack trace (§33).
            "failures": [f.to_json() for f in self.failures],
            "idempotency_key": self.idempotency_key,
            "succeeded": self.succeeded,
        }


def run_world_bank_job(
    payload: object,
    connection_factory: Callable[[str], Any],
    *,
    catalog: SourceCatalog | None = None,
    compliance: ComplianceConfig | None = None,
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
        context = build_authorization(source, rules)
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


def utc_now() -> datetime:
    return datetime.now(UTC)
