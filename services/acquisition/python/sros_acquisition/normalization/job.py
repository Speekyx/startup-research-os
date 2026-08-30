"""One normalization job, from a task payload to persisted records.

Mission 1.6 §29, §32–§35. This is the function a Celery task calls, kept out of
the worker package so it can be tested without a broker -- a job whose logic
lives inside a task decorator can only be tested by starting a worker, and a
test that needs a worker is a test that gets skipped.

**Nothing is reconstructed inside the worker.** `workspace_id`,
`research_session_id` and `correlation_id` come from the payload and are refused
if absent. ADR-005: a worker that could resolve "the current workspace" could
resolve the wrong one, and a default here would be a cross-tenant write waiting
for a bug upstream.

**The batch is bounded, and the bound is ours** (§34). At most 500 raw records,
defaulted rather than left to the caller. This is not an external platform limit
and must never be written down as one -- the same distinction request pacing
draws at the acquisition layer.

**Duplicate delivery is safe and is not exactly-once.** Celery is at-least-once
(ADR-004) and this does not pretend otherwise. The second delivery re-reads the
same raw records, produces byte-identical canonical content, finds every
identity already stored and writes nothing (§35).

**The acquisition gate is deliberately NOT re-run here**, and that is a
decision rather than an omission. A raw record's existence is itself the
evidence that acquisition was authorised: the collector could not have written
it without passing the gate, and the row carries the review version and the
condition snapshot that were true at the time. Re-running eligibility would mean
a source suspended after collection leaves lawfully-collected data permanently
unusable while it is still stored, which helps nobody. The remedy for a
licensing problem is deletion of the raw records
(`data-retention-policy-v1.md` §5.1, source-mandated) -- and once they are
deleted there is nothing here to normalize.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sros_contracts import NormalizationErrorCode, NormalizedRecordQuality

from ..registry.catalog import SourceCatalog, load_catalog
from ..registry.retention import resolve_retention
from .errors import NormalizationFailedError, NormalizationFailure
from .geography import GeographyMap, load_geography_map
from .model import NormalizationCounts, NormalizedRecordDraft, RawRecordView
from .normalizers import (
    NORMALIZER_REGISTRY,
    NormalizationContext,
    NormalizerSpec,
    select_normalizer,
)
from .repositories import (
    PersistenceReport,
    persist_normalized,
    read_raw_records,
)

__all__ = [
    "MAX_NORMALIZATION_BATCH",
    "NormalizationJobPayload",
    "NormalizationJobResult",
    "run_normalization_job",
]

_REQUIRED_HEADERS = ("workspace_id", "research_session_id", "correlation_id")

# OUR OWN operational bound (§34), not an external limit. It protects a worker
# slot and a single transaction from a job nobody sized. Chosen conservatively:
# a numeric observation is a few hundred bytes, so 500 is a transaction of a few
# hundred kilobytes, and a session with more records simply takes more jobs.
MAX_NORMALIZATION_BATCH = 500


@dataclass(frozen=True)
class NormalizationJobPayload:
    """What a task must carry. Every tenancy field is required and none defaults."""

    workspace_id: str
    research_session_id: str
    correlation_id: str
    raw_record_ids: tuple[str, ...] = ()
    source_id: str | None = None
    max_records: int = MAX_NORMALIZATION_BATCH
    only_unnormalized: bool = True

    @classmethod
    def from_payload(cls, payload: object) -> NormalizationJobPayload:
        """Parse and refuse, in that order.

        A payload missing a correlation header fails here rather than being
        completed with a plausible value -- there is no plausible value for a
        workspace.
        """
        if not isinstance(payload, dict):
            raise ValueError("a normalization task payload must be a mapping")
        missing = [name for name in _REQUIRED_HEADERS if not payload.get(name)]
        if missing:
            raise ValueError(
                f"normalization payload is missing required headers: {missing}. A worker "
                "never resolves the workspace itself and never falls back to a default "
                "(ADR-005)"
            )
        requested = int(payload.get("max_records") or MAX_NORMALIZATION_BATCH)
        if requested < 1:
            raise ValueError("max_records must be at least 1; a batch of zero does nothing")
        return cls(
            workspace_id=str(payload["workspace_id"]),
            research_session_id=str(payload["research_session_id"]),
            correlation_id=str(payload["correlation_id"]),
            raw_record_ids=tuple(str(i) for i in payload.get("raw_record_ids") or ()),
            source_id=str(payload["source_id"]) if payload.get("source_id") else None,
            # Configurable DOWNWARDS only. A caller asking for a larger batch
            # gets the ceiling, silently in the payload and loudly in the result
            # -- an unbounded batch is exactly what §34 forbids.
            max_records=min(requested, MAX_NORMALIZATION_BATCH),
            only_unnormalized=bool(payload.get("only_unnormalized", True)),
        )

    @property
    def idempotency_key(self) -> str:
        """Stable over what the job WOULD normalize, not over when it was sent.

        Two deliveries of the same logical job share this. The time is
        deliberately absent: including it would make every redelivery a
        different job, which is the opposite of what §35 asks for.
        """
        return "|".join(
            (
                self.workspace_id,
                self.research_session_id,
                self.source_id or "*",
                ",".join(sorted(self.raw_record_ids)) or "*",
                str(self.max_records),
            )
        )


@dataclass(frozen=True)
class NormalizationJobResult:
    source_ids: tuple[str, ...]
    normalizers: tuple[str, ...]
    counts: NormalizationCounts
    persisted: PersistenceReport
    failures: tuple[NormalizationFailure, ...] = field(default=())
    idempotency_key: str = ""

    @property
    def succeeded(self) -> bool:
        return not self.failures

    def to_json(self) -> dict[str, object]:
        return {
            "source_ids": list(self.source_ids),
            "normalizers": list(self.normalizers),
            "counts": self.counts.to_json(),
            "persisted": self.persisted.to_json(),
            # Already sanitised: a failure carries a message this codebase wrote
            # and safe diagnostic context, never a payload or a stack trace.
            "failures": [f.to_json() for f in self.failures],
            "idempotency_key": self.idempotency_key,
            "succeeded": self.succeeded,
        }


def run_normalization_job(
    payload: object,
    connection_factory: Callable[[str], Any],
    *,
    catalog: SourceCatalog | None = None,
    geography: GeographyMap | None = None,
    registry: dict[tuple[str, str], NormalizerSpec] | None = None,
    cancelled: Callable[[], bool] | None = None,
    now: Callable[[], datetime] | None = None,
) -> NormalizationJobResult:
    """Read, normalize and persist, in the caller's tenant transaction.

    `connection_factory` takes the workspace id and returns a context manager
    yielding a connection already inside a tenant transaction. Passed in rather
    than constructed, so this function has no opinion about pooling and no
    import of a driver -- and so a test can supply a rolled-back connection.

    §29: reading, normalizing and persisting happen inside ONE transaction. A
    normalized record whose lineage was committed separately from itself is the
    orphan that section exists to prevent.
    """
    job = NormalizationJobPayload.from_payload(payload)
    sources = catalog or load_catalog()
    geo = geography or load_geography_map()
    clock = now or _utc_now
    table = NORMALIZER_REGISTRY if registry is None else registry

    counts = NormalizationCounts()
    failures: list[NormalizationFailure] = []
    drafts: list[NormalizedRecordDraft] = []
    seen_sources: set[str] = set()
    seen_normalizers: set[str] = set()

    with connection_factory(job.workspace_id) as conn:
        records = _select_records(conn, job, table)
        counts.records_input = len(records)

        for record in records:
            if cancelled is not None and cancelled():
                failures.append(
                    NormalizationFailure(
                        code=NormalizationErrorCode.CANCELLED,
                        detail="the job was cancelled before the next record",
                        source_id=record.source_id,
                        correlation_id=job.correlation_id,
                    )
                )
                break
            seen_sources.add(record.source_id)
            draft = _normalize_one(record, job, sources, geo, table, clock, failures, counts)
            if draft is not None:
                drafts.append(draft)
                seen_normalizers.add(f"{draft.normalizer_id}@{draft.normalizer_version}")

        persisted = PersistenceReport()
        if drafts:
            try:
                persisted = persist_normalized(conn, drafts)
            except Exception as exc:  # noqa: BLE001 - normalised, see errors.py
                # The caller's transaction is not committed, so §29 holds: a
                # storage failure leaves nothing behind rather than half a batch.
                failures.append(
                    NormalizationFailure(
                        code=NormalizationErrorCode.PERSISTENCE_FAILURE,
                        detail=(
                            f"records were normalized and could not be stored "
                            f"({type(exc).__name__}); nothing was committed"
                        ),
                        source_id=next(iter(sorted(seen_sources)), ""),
                        correlation_id=job.correlation_id,
                    )
                )
                persisted = PersistenceReport()

    counts.records_created = persisted.new
    counts.records_revised = persisted.revised
    counts.records_unchanged = persisted.unchanged
    counts.records_conflicted = persisted.conflicted
    for raw_record_id in persisted.conflicts:
        failures.append(
            NormalizationFailure(
                code=NormalizationErrorCode.NON_DETERMINISTIC_OUTPUT,
                detail=(
                    "a normalized record already exists for this exact identity and "
                    "re-running produced different canonical content. The stored record "
                    "stands; changing output requires bumping the normalizer version"
                ),
                source_id=next(iter(sorted(seen_sources)), ""),
                raw_record_id=raw_record_id,
                correlation_id=job.correlation_id,
            )
        )

    return NormalizationJobResult(
        source_ids=tuple(sorted(seen_sources)),
        normalizers=tuple(sorted(seen_normalizers)),
        counts=counts,
        persisted=persisted,
        failures=tuple(failures),
        idempotency_key=job.idempotency_key,
    )


def _select_records(
    conn: Any,
    job: NormalizationJobPayload,
    table: Mapping[tuple[str, str], NormalizerSpec],
) -> list[RawRecordView]:
    """The raw records this pass will read, bounded.

    `only_unnormalized` needs a lineage to be meaningful, and the lineage is a
    property of the normalizer -- so when exactly one is registered the filter
    is scoped to it, and otherwise the pass reads everything in scope and lets
    per-record idempotency classify it. Guessing a lineage from a registry with
    two entries would silently normalize under one adapter's version while
    skipping records another had already done.
    """
    lineage: dict[str, Any] = {}
    if job.only_unnormalized and len(table) == 1:
        spec = next(iter(table.values()))
        lineage = {
            "only_unnormalized": True,
            "normalizer_id": spec.normalizer_id,
            "normalizer_version": spec.normalizer_version,
            "schema_version": spec.schema_version,
        }
    return read_raw_records(
        conn,
        job.workspace_id,
        record_ids=job.raw_record_ids or None,
        research_session_id=None if job.raw_record_ids else job.research_session_id,
        source_id=job.source_id,
        limit=job.max_records,
        **lineage,
    )


def _normalize_one(
    record: RawRecordView,
    job: NormalizationJobPayload,
    sources: SourceCatalog,
    geo: GeographyMap,
    table: Mapping[tuple[str, str], NormalizerSpec],
    clock: Callable[[], datetime],
    failures: list[NormalizationFailure],
    counts: NormalizationCounts,
) -> NormalizedRecordDraft | None:
    try:
        spec = select_normalizer(record, table, correlation_id=job.correlation_id)
    except NormalizationFailedError as exc:
        failures.append(exc.failure)
        counts.records_failed += 1
        return None

    # Retention comes from GOVERNANCE, resolved per source, and the adapter is
    # CONSTRUCTED with it rather than asked for it (§10). There is no setter and
    # no argument on `normalize` through which a longer window could be requested.
    source = sources.get(record.source_id)
    retention = resolve_retention(source.retention_override)
    configured = spec.build(NormalizationContext(retention=retention, geography=geo))

    try:
        draft = configured.normalize(
            record, correlation_id=job.correlation_id, normalized_at=clock()
        )
    except NormalizationFailedError as exc:
        failures.append(exc.failure)
        counts.records_failed += 1
        return None
    except ValueError as exc:
        # §46: a raw record with no attribution obligation is refused rather
        # than normalized into a row with no credit attached. The message is
        # this codebase's own -- `build_normalized` raised it.
        failures.append(
            NormalizationFailure(
                code=NormalizationErrorCode.INVALID_RAW_RECORD,
                detail=str(exc),
                source_id=record.source_id,
                raw_record_id=record.record_id,
                correlation_id=job.correlation_id,
            )
        )
        counts.records_failed += 1
        return None

    counts.records_normalized += 1
    if draft.quality is NormalizedRecordQuality.VALID:
        counts.records_valid += 1
    elif draft.quality is NormalizedRecordQuality.PARTIAL:
        counts.records_partial += 1
    else:
        counts.records_invalid += 1
    for reason in draft.quality_reasons:
        counts.reasons[reason.code.value] = counts.reasons.get(reason.code.value, 0) + 1
    return draft


def _utc_now() -> datetime:
    return datetime.now(UTC)
