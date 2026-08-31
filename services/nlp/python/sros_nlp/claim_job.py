"""One claim interpretation job, from a task payload to persisted Claims.

`claim-interpretation-runtime-v1.md`. Mission 1.13.1.

This is the function a Celery task calls, kept out of the worker package so it
can be tested without a broker -- a job whose logic lives inside a task decorator
can only be tested by starting a worker, and a test that needs a worker is a
test that gets skipped.

**Nothing is reconstructed inside the worker.** `workspace_id`,
`research_session_id` and `correlation_id` come from the payload and are refused
if absent (ADR-005).

**The selection is bounded and explicit.** At most 200 Signals per job, filtered
by id, by type or by session. There is no sweep over everything a workspace has
ever derived, no semantic search and no embedding (§23).

**Duplicate delivery is safe and is not exactly-once.** The second delivery
re-reads the same Signals, renders byte-identical statements, finds every
proposition already stored and writes no claim, no revision and no evidence. It
DOES write a second run record, because a run is an execution and two executions
happened.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sros_contracts import ClaimEvidenceRefusalReason, ClaimInterpretationInputRole

from .claim_repositories import (
    ClaimPersistenceReport,
    ConsideredSignal,
    InterpretationRunRecord,
    persist_claims,
    persist_considered,
    persist_interpretation_run,
    read_signal_views,
)
from .interpreters import (
    SUPPORTED_SIGNAL_TYPES,
    InterpretationRequest,
    select_interpreter,
)

__all__ = [
    "CLAIM_RETENTION_DAYS",
    "MAX_INTERPRETED_SIGNALS",
    "ClaimInterpretationJobPayload",
    "ClaimInterpretationJobResult",
    "run_claim_interpretation_job",
]

_REQUIRED_HEADERS = ("workspace_id", "research_session_id", "correlation_id")

# OUR OWN operational bound, not an external limit. It protects a worker slot
# and a single transaction from a job nobody sized.
MAX_INTERPRETED_SIGNALS = 200

# The claim/evidence tier of data-retention-policy-v1.md §2.2 -- twelve months,
# the same window a signal gets. Resolved HERE rather than inside a template,
# for the reason `build_normalized` has no retention parameter: a template that
# could choose its own expiry would be setting its own retention policy.
CLAIM_RETENTION_DAYS = 365

# Operational data, §2.5. Deliberately shorter than a claim's: a record of an
# attempt is not an artifact.
RUN_RETENTION_DAYS = 90


@dataclass(frozen=True)
class ClaimInterpretationJobPayload:
    """What a task must carry. Every tenancy field is required and none defaults."""

    workspace_id: str
    research_session_id: str
    correlation_id: str
    interpreter_id: str
    signal_ids: tuple[str, ...] = ()
    signal_type_ids: tuple[str, ...] = ()
    max_signals: int = MAX_INTERPRETED_SIGNALS
    scope_to_session: bool = False

    @classmethod
    def from_payload(cls, payload: object) -> ClaimInterpretationJobPayload:
        if not isinstance(payload, dict):
            raise ValueError("a claim interpretation task payload must be a mapping")
        missing = [name for name in _REQUIRED_HEADERS if not payload.get(name)]
        if missing:
            raise ValueError(
                f"claim interpretation payload is missing required headers: {missing}. A "
                "worker never resolves the workspace itself and never falls back to a "
                "default (ADR-005)"
            )
        if not payload.get("interpreter_id"):
            raise ValueError(
                "an interpretation job names its interpreter. There is no default: an "
                "interpreter is what decides what a proposition says, and a job that "
                "could pick one could pick the wrong one"
            )
        signals = int(payload.get("max_signals") or MAX_INTERPRETED_SIGNALS)
        if signals < 1:
            raise ValueError("a batch of zero interprets nothing")
        return cls(
            workspace_id=str(payload["workspace_id"]),
            research_session_id=str(payload["research_session_id"]),
            correlation_id=str(payload["correlation_id"]),
            interpreter_id=str(payload["interpreter_id"]),
            signal_ids=tuple(str(i) for i in payload.get("signal_ids") or ()),
            signal_type_ids=tuple(str(i) for i in payload.get("signal_type_ids") or ()),
            # Configurable DOWNWARDS only. A ceiling a caller could raise is not
            # a ceiling.
            max_signals=min(signals, MAX_INTERPRETED_SIGNALS),
            scope_to_session=bool(payload.get("scope_to_session", False)),
        )

    @property
    def idempotency_key(self) -> str:
        """Stable over what the job WOULD interpret, not over when it was sent."""
        return "|".join(
            (
                self.workspace_id,
                self.research_session_id,
                self.interpreter_id,
                ",".join(sorted(self.signal_ids)) or "*",
                ",".join(sorted(self.signal_type_ids)) or "*",
                str(self.max_signals),
            )
        )


@dataclass(frozen=True)
class ClaimInterpretationJobResult:
    interpreter: str
    run: InterpretationRunRecord
    persisted: ClaimPersistenceReport
    considered: tuple[ConsideredSignal, ...] = ()
    run_id: str = ""
    idempotency_key: str = ""

    @property
    def succeeded(self) -> bool:
        """A refusal is an outcome, not a failure. Only a crash is a failure."""
        return True

    def to_json(self) -> dict[str, object]:
        return {
            "interpreter": self.interpreter,
            "run_id": self.run_id,
            "run": self.run.to_json(),
            "persisted": self.persisted.to_json(),
            "considered": [
                {
                    "signal_id": item.signal_id,
                    "signal_type_id": item.signal_type_id,
                    "role": item.role.value,
                    "claim_id": item.claim_id,
                    "reason_code": item.reason_code,
                }
                for item in self.considered
            ],
            "idempotency_key": self.idempotency_key,
        }


def run_claim_interpretation_job(
    payload: object,
    connection_factory: Callable[[str], Any],
    *,
    now: Callable[[], datetime] | None = None,
) -> ClaimInterpretationJobResult:
    """Read, interpret and persist, in the caller's tenant transaction.

    `connection_factory` takes the workspace id and returns a context manager
    yielding a connection already inside a tenant transaction. Passed in rather
    than constructed, so this function has no opinion about pooling and no
    import of a driver.

    Reading, interpreting and persisting happen inside ONE transaction. Claim,
    revision and evidence must land together -- the evidence requirement is a
    deferred trigger firing at COMMIT -- and the run record joins them so its
    counts can never disagree with what was stored.
    """
    job = ClaimInterpretationJobPayload.from_payload(payload)
    clock = now or _utc_now

    interpreter = select_interpreter(job.interpreter_id)
    if interpreter is None:
        raise ValueError(
            f"{job.interpreter_id!r} is not a registered claim interpreter. "
            f"Registered: ['observed-signal-restatement']"
        )

    started_at = clock()
    considered: list[ConsideredSignal] = []
    refusals: list[dict[str, object]] = []
    drafts = []
    truncated_by: str | None = None

    with connection_factory(job.workspace_id) as conn:
        signals = read_signal_views(
            conn,
            job.workspace_id,
            signal_ids=job.signal_ids or None,
            # Bounded by what the interpreter can phrase, unless the caller
            # narrowed it further. Reading types nobody has a template for would
            # inflate `signals_considered` with Signals that were never
            # candidates, which is the denominator GAP-5 exists to keep honest.
            signal_type_ids=job.signal_type_ids or SUPPORTED_SIGNAL_TYPES,
            research_session_id=job.research_session_id if job.scope_to_session else None,
            limit=job.max_signals,
        )
        if len(signals) == job.max_signals:
            truncated_by = "max_signals"

        request = InterpretationRequest(
            workspace_id=job.workspace_id,
            correlation_id=job.correlation_id,
            interpreted_at=started_at,
            research_session_id=job.research_session_id,
        )

        for signal in signals:
            if not interpreter.supports(signal.signal_type_id):
                # EXCLUDED, not REFUSED: never attempted. The distinction is
                # what lets a reader tell "no template exists" from "the model
                # rejected the draft".
                considered.append(
                    ConsideredSignal(
                        signal_id=signal.signal_id,
                        signal_type_id=signal.signal_type_id,
                        role=ClaimInterpretationInputRole.EXCLUDED,
                        reason_code=ClaimEvidenceRefusalReason.UNSUPPORTED_SIGNAL_TYPE.value,
                        detail=f"no template for {signal.signal_type_id!r}",
                    )
                )
                continue
            outcome = interpreter.interpret(signal, request)
            if outcome.draft is not None:
                drafts.append(outcome.draft)
                considered.append(
                    ConsideredSignal(
                        signal_id=signal.signal_id,
                        signal_type_id=signal.signal_type_id,
                        role=ClaimInterpretationInputRole.CITED,
                    )
                )
                continue
            refusal = outcome.refusal
            assert refusal is not None  # noqa: S101 - TemplateOutcome sets exactly one
            considered.append(
                ConsideredSignal(
                    signal_id=signal.signal_id,
                    signal_type_id=signal.signal_type_id,
                    role=ClaimInterpretationInputRole.REFUSED,
                    reason_code=refusal.reason.value,
                    detail=refusal.detail,
                )
            )
            refusals.append(
                {
                    "reason": refusal.reason.value,
                    "detail": refusal.detail,
                    "signal_id": signal.signal_id,
                    "signal_type_id": signal.signal_type_id,
                }
            )

        persisted = persist_claims(conn, drafts) if drafts else ClaimPersistenceReport()

        # The claim id is known only after persistence, so CITED rows are
        # completed here rather than guessed at above.
        considered = [_with_claim(item, persisted) for item in considered]

        finished_at = clock()
        run = InterpretationRunRecord(
            workspace_id=job.workspace_id,
            research_session_id=job.research_session_id,
            interpreter_id=interpreter.interpreter_id,
            interpreter_version=interpreter.interpreter_version,
            interpretation_kind=interpreter.kind.value,
            correlation_id=job.correlation_id,
            started_at=started_at,
            finished_at=finished_at,
            expires_at=finished_at + timedelta(days=RUN_RETENTION_DAYS),
            signals_considered=len(signals),
            signals_cited=_count(considered, ClaimInterpretationInputRole.CITED),
            signals_excluded=_count(considered, ClaimInterpretationInputRole.EXCLUDED),
            signals_refused=_count(considered, ClaimInterpretationInputRole.REFUSED),
            claims_new=persisted.new,
            claims_unchanged=persisted.unchanged,
            revisions_created=persisted.revisions_created,
            evidence_new=persisted.evidence_new,
            evidence_unchanged=persisted.evidence_unchanged,
            refusals=tuple(refusals),
            truncated_by=truncated_by,
        )
        run_id = persist_interpretation_run(conn, run)
        persist_considered(conn, job.workspace_id, run_id, considered)

    return ClaimInterpretationJobResult(
        interpreter=f"{interpreter.interpreter_id}@{interpreter.interpreter_version}",
        run=run,
        run_id=run_id,
        persisted=persisted,
        considered=tuple(considered),
        idempotency_key=job.idempotency_key,
    )


def _with_claim(item: ConsideredSignal, persisted: ClaimPersistenceReport) -> ConsideredSignal:
    if item.role is not ClaimInterpretationInputRole.CITED:
        return item
    claim_id = persisted.claim_by_signal.get(item.signal_id)
    if claim_id is None:  # pragma: no cover -- a cited draft always persists
        return item
    return ConsideredSignal(
        signal_id=item.signal_id,
        signal_type_id=item.signal_type_id,
        role=item.role,
        claim_id=claim_id,
    )


def _count(items: Sequence[ConsideredSignal], role: ClaimInterpretationInputRole) -> int:
    return sum(1 for item in items if item.role is role)


def _utc_now() -> datetime:
    return datetime.now(UTC)
