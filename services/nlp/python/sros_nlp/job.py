"""One signal derivation job, from a task payload to persisted signals.

`signal-derivation-runtime-v1.md`. This is the function a Celery task calls,
kept out of the worker package so it can be tested without a broker -- a job
whose logic lives inside a task decorator can only be tested by starting a
worker, and a test that needs a worker is a test that gets skipped.

**Nothing is reconstructed inside the worker.** `workspace_id`,
`research_session_id` and `correlation_id` come from the payload and are refused
if absent (ADR-005).

**The batch is bounded, and the bound is ours.** At most 500 normalized records
and 200 derived groups per job. Neither is an external limit and neither may be
written down as one; a job that hits one **says which**, and keeps what it
derived.

**Duplicate delivery is safe and is not exactly-once.** The second delivery
re-reads the same records, produces byte-identical signals, finds every identity
already stored and writes no signal. It DOES write a second run record, because
a run is an execution and two executions happened.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sros_contracts import SignalInputRole
from sros_signal_model import SignalDraft, SignalRefusedError

from .extractors import (
    EXTRACTOR_REGISTRY,
    CandidateGroup,
    DerivationRequest,
    GroupRefusal,
    select_extractor,
)
from .extractors import SignalExtractor as Extractor
from .repositories import (
    DerivationRunRecord,
    SignalPersistenceReport,
    persist_run,
    persist_signals,
    read_normalized_observations,
)

__all__ = [
    "MAX_DERIVATION_GROUPS",
    "MAX_DERIVATION_RECORDS",
    "SIGNAL_RETENTION_DAYS",
    "SignalDerivationJobPayload",
    "SignalDerivationJobResult",
    "run_signal_derivation_job",
]

_REQUIRED_HEADERS = ("workspace_id", "research_session_id", "correlation_id")

# OUR OWN operational bounds, not external limits. They protect a worker slot
# and a single transaction from a job nobody sized.
MAX_DERIVATION_RECORDS = 500
MAX_DERIVATION_GROUPS = 200

# The normalized/derived tier of data-retention-policy-v1.md §2.2 -- twelve
# months, the same window a normalized record gets. Resolved HERE rather than
# inside an extractor, for the reason `build_normalized` has no retention
# parameter: an extractor that could choose its own expiry would be setting its
# own retention policy.
SIGNAL_RETENTION_DAYS = 365

# Operational data, §2.5. Deliberately shorter than a signal's: a record of an
# attempt is not an artifact.
RUN_RETENTION_DAYS = 90


@dataclass(frozen=True)
class SignalDerivationJobPayload:
    """What a task must carry. Every tenancy field is required and none defaults."""

    workspace_id: str
    research_session_id: str
    correlation_id: str
    extractor_id: str
    parameters: Mapping[str, object] = field(default_factory=dict)
    normalized_record_ids: tuple[str, ...] = ()
    source_id: str | None = None
    max_records: int = MAX_DERIVATION_RECORDS
    max_groups: int = MAX_DERIVATION_GROUPS
    scope_to_session: bool = False

    @classmethod
    def from_payload(cls, payload: object) -> SignalDerivationJobPayload:
        if not isinstance(payload, dict):
            raise ValueError("a signal derivation task payload must be a mapping")
        missing = [name for name in _REQUIRED_HEADERS if not payload.get(name)]
        if missing:
            raise ValueError(
                f"signal derivation payload is missing required headers: {missing}. A "
                "worker never resolves the workspace itself and never falls back to a "
                "default (ADR-005)"
            )
        if not payload.get("extractor_id"):
            raise ValueError(
                "a derivation job names its extractor. There is no default extractor: a "
                "job that could pick one could pick the wrong one"
            )
        parameters = payload.get("parameters") or {}
        if not isinstance(parameters, Mapping):
            raise ValueError("derivation parameters must be a mapping")
        records = int(payload.get("max_records") or MAX_DERIVATION_RECORDS)
        groups = int(payload.get("max_groups") or MAX_DERIVATION_GROUPS)
        if records < 1 or groups < 1:
            raise ValueError("a batch of zero does nothing")
        return cls(
            workspace_id=str(payload["workspace_id"]),
            research_session_id=str(payload["research_session_id"]),
            correlation_id=str(payload["correlation_id"]),
            extractor_id=str(payload["extractor_id"]),
            parameters=dict(parameters),
            normalized_record_ids=tuple(str(i) for i in payload.get("normalized_record_ids") or ()),
            source_id=str(payload["source_id"]) if payload.get("source_id") else None,
            # Configurable DOWNWARDS only. A ceiling a caller could raise is not
            # a ceiling.
            max_records=min(records, MAX_DERIVATION_RECORDS),
            max_groups=min(groups, MAX_DERIVATION_GROUPS),
            scope_to_session=bool(payload.get("scope_to_session", False)),
        )

    @property
    def idempotency_key(self) -> str:
        """Stable over what the job WOULD derive, not over when it was sent."""
        return "|".join(
            (
                self.workspace_id,
                self.research_session_id,
                self.extractor_id,
                self.source_id or "*",
                ",".join(sorted(self.normalized_record_ids)) or "*",
                str(self.max_records),
            )
        )


@dataclass(frozen=True)
class SignalDerivationJobResult:
    extractor: str
    signal_type_id: str
    run: DerivationRunRecord
    persisted: SignalPersistenceReport
    run_id: str = ""
    idempotency_key: str = ""

    @property
    def succeeded(self) -> bool:
        return self.persisted.conflicted == 0

    def to_json(self) -> dict[str, object]:
        return {
            "extractor": self.extractor,
            "signal_type_id": self.signal_type_id,
            "run_id": self.run_id,
            "run": self.run.to_json(),
            "persisted": self.persisted.to_json(),
            "idempotency_key": self.idempotency_key,
            "succeeded": self.succeeded,
        }


def run_signal_derivation_job(
    payload: object,
    connection_factory: Callable[[str], Any],
    *,
    registry: Mapping[str, Extractor] | None = None,
    now: Callable[[], datetime] | None = None,
) -> SignalDerivationJobResult:
    """Read, group, derive and persist, in the caller's tenant transaction.

    `connection_factory` takes the workspace id and returns a context manager
    yielding a connection already inside a tenant transaction. Passed in rather
    than constructed, so this function has no opinion about pooling and no
    import of a driver.

    Reading, deriving and persisting happen inside ONE transaction. A signal
    whose lineage was committed separately from itself is the orphan §30 exists
    to prevent.
    """
    job = SignalDerivationJobPayload.from_payload(payload)
    table = EXTRACTOR_REGISTRY if registry is None else registry
    clock = now or _utc_now

    extractor = (
        table.get(job.extractor_id) if registry is not None else select_extractor(job.extractor_id)
    )
    if extractor is None:
        raise ValueError(
            f"{job.extractor_id!r} is not a registered signal extractor. "
            f"Registered: {sorted(table)}"
        )

    started_at = clock()
    derivation = extractor.resolve(job.parameters)

    drafts: list[SignalDraft] = []
    refusals: list[GroupRefusal] = []
    considered = derived = refused = 0
    # DISTINCT records, not a sum over drafts. One record legitimately
    # contributes to several signals -- 2019 is in both the 2018->2019 and the
    # 2019->2020 pair -- so summing per draft counts it twice and reports more
    # contributors than there were records. The run table's arithmetic CHECK
    # caught exactly that.
    contributed_ids: set[str] = set()
    excluded_ids: set[str] = set()
    truncated_by: str | None = None

    with connection_factory(job.workspace_id) as conn:
        observations = read_normalized_observations(
            conn,
            job.workspace_id,
            record_kind_id=extractor.record_kind_id,
            record_ids=job.normalized_record_ids or None,
            research_session_id=job.research_session_id if job.scope_to_session else None,
            source_id=job.source_id,
            limit=job.max_records,
        )
        if len(observations) == job.max_records:
            truncated_by = "max_records"

        groups: dict[str, list[Any]] = {}
        for observation in observations:
            key = extractor.group_key(observation, derivation)
            if key is None:
                continue
            groups.setdefault(key, []).append(observation)

        request = DerivationRequest(
            workspace_id=job.workspace_id,
            correlation_id=job.correlation_id,
            derived_at=started_at,
            expires_at=started_at + timedelta(days=SIGNAL_RETENTION_DAYS),
            research_session_id=job.research_session_id,
        )

        # Sorted, so the order groups are derived in -- and therefore the order
        # rows are written in -- does not depend on dict insertion, which depends
        # on the order the database returned rows in.
        for key in sorted(groups):
            if considered >= job.max_groups:
                truncated_by = "max_groups"
                break
            considered += 1
            group = CandidateGroup(key=key, observations=tuple(groups[key]))
            try:
                outcome = extractor.derive(group, derivation, request)
            except SignalRefusedError as refusal:
                refused += 1
                refusals.append(
                    GroupRefusal(
                        reason=refusal.refusal.reason,
                        detail=refusal.refusal.detail,
                        group_key=key,
                        observation_keys=group.observation_keys,
                    )
                )
                continue
            if outcome.drafts:
                derived += 1
            if outcome.refusals:
                refused += 1
            drafts.extend(outcome.drafts)
            refusals.extend(outcome.refusals)
            for draft in outcome.drafts:
                for assessed in draft.inputs:
                    record_id = assessed.observation.normalized_record_id
                    if assessed.role is SignalInputRole.CONTRIBUTED:
                        contributed_ids.add(record_id)
                    else:
                        excluded_ids.add(record_id)

        persisted = persist_signals(conn, drafts) if drafts else SignalPersistenceReport()

        finished_at = clock()
        run = DerivationRunRecord(
            workspace_id=job.workspace_id,
            research_session_id=job.research_session_id,
            extractor_id=extractor.extractor_id,
            extractor_version=extractor.extractor_version,
            signal_type_id=extractor.signal_type_id,
            parameter_fingerprint=derivation.parameter_fingerprint,
            correlation_id=job.correlation_id,
            started_at=started_at,
            finished_at=finished_at,
            expires_at=finished_at + timedelta(days=RUN_RETENTION_DAYS),
            groups_considered=considered,
            groups_derived=derived,
            groups_refused=refused,
            signals_new=persisted.new,
            signals_unchanged=persisted.unchanged,
            signals_conflicted=persisted.conflicted,
            records_considered=len(observations),
            records_contributed=len(contributed_ids),
            # A record excluded from one signal and contributing to another is
            # a CONTRIBUTOR. Counting it in both would make the two numbers
            # overlap, and a reader adding them would get more than were read.
            records_excluded=len(excluded_ids - contributed_ids),
            refusals=tuple(r.to_json() for r in refusals),
            truncated_by=truncated_by,
        )
        run_id = persist_run(conn, run)

    return SignalDerivationJobResult(
        extractor=f"{extractor.extractor_id}@{extractor.extractor_version}",
        signal_type_id=extractor.signal_type_id,
        run=run,
        run_id=run_id,
        persisted=persisted,
        idempotency_key=job.idempotency_key,
    )


def _utc_now() -> datetime:
    return datetime.now(UTC)
