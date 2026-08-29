"""The generic orchestrator job description.

Mission 0.4 §11. Deliberately **not** tied to any collector, model or analysis
stage: `job_type` is a string and `payload` is an opaque mapping. A schema
shaped around today's first collector is a schema that needs a migration for the
second one.

Two properties carry weight beyond bookkeeping:

**`idempotency_key`.** ADR-004 delivery is at-least-once. The key is
deterministic in the job's inputs and unique per workspace, so a duplicate
delivery collides on a database constraint rather than on a read-then-write
check, which is a race with a longer window.

**`dependencies`.** Job ordering is data, not code. §12 keeps the orchestration
layer small and explicit rather than adding a workflow engine to express
"B after A".
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum

from sros_workers import Queue, TaskContext, idempotency_key, route_task

__all__ = [
    "JobStatus",
    "JOB_ID_NAMESPACE",
    "deterministic_job_id",
    "JobSpec",
    "TERMINAL_JOB_STATUSES",
    "DISPATCHABLE_JOB_STATUSES",
    "ALLOWED_JOB_TRANSITIONS",
    "InvalidJobTransitionError",
    "require_job_transition",
    "build_idempotency_key",
]


class JobStatus(StrEnum):
    """Job lifecycle. Matches the CHECK constraint on research.research_jobs.

    `BLOCKED` is distinct from `FAILED` on purpose. A blocked job never ran
    because a capability is unavailable (D-07, D-03); a failed job ran and did
    not succeed. Collapsing them would make "we could not do this" and "we tried
    and it broke" indistinguishable in every gap report.
    """

    PENDING = "PENDING"
    READY = "READY"
    DISPATCHED = "DISPATCHED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


TERMINAL_JOB_STATUSES: frozenset[JobStatus] = frozenset(
    {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.BLOCKED, JobStatus.CANCELLED}
)

DISPATCHABLE_JOB_STATUSES: frozenset[JobStatus] = frozenset({JobStatus.READY})


ALLOWED_JOB_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    # PENDING means "declared, dependencies not yet satisfied".
    JobStatus.PENDING: frozenset({JobStatus.READY, JobStatus.BLOCKED, JobStatus.CANCELLED}),
    JobStatus.READY: frozenset({JobStatus.DISPATCHED, JobStatus.BLOCKED, JobStatus.CANCELLED}),
    # DISPATCHED -> READY is the retry edge: the worker never picked it up, or
    # it failed retryably and returns to the pool.
    #
    # DISPATCHED -> SUCCEEDED skips RUNNING deliberately. A progress event is
    # just another at-least-once message (ADR-004), so it can be lost or
    # reordered; requiring RUNNING first would let a dropped "started" event
    # permanently block the success report for work that actually completed.
    # The ledger would then show a job stuck in flight forever, which is worse
    # than a missing intermediate timestamp.
    JobStatus.DISPATCHED: frozenset(
        {
            JobStatus.RUNNING,
            JobStatus.SUCCEEDED,
            JobStatus.READY,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        }
    ),
    JobStatus.RUNNING: frozenset(
        {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.READY, JobStatus.CANCELLED}
    ),
    JobStatus.SUCCEEDED: frozenset(),
    JobStatus.FAILED: frozenset(),
    JobStatus.BLOCKED: frozenset(),
    JobStatus.CANCELLED: frozenset(),
}


class InvalidJobTransitionError(ValueError):
    """A job status transition the ledger does not allow."""


def require_job_transition(current: JobStatus, target: JobStatus) -> None:
    if target not in ALLOWED_JOB_TRANSITIONS[current]:
        allowed = sorted(s.value for s in ALLOWED_JOB_TRANSITIONS[current])
        raise InvalidJobTransitionError(
            f"job {current.value} -> {target.value} is not permitted. "
            f"Allowed from {current.value}: {allowed or 'none (terminal)'}"
        )


def build_idempotency_key(
    job_type: str,
    workspace_id: str,
    research_session_id: str,
    payload: object,
) -> str:
    """Derive the deterministic key a duplicate delivery must collide on.

    Reuses `sros_workers.idempotency_key` rather than hashing here, so the
    orchestrator and the worker compute the same key for the same work. Two
    implementations of "the same key" is how at-least-once quietly becomes
    at-least-twice.

    **The session is part of the key, and it has to be.** `sros_workers`
    hashes the task name, the workspace and the payload — it is tenant-separated
    but not session-separated, because it was written before sessions had a
    ledger. With a unique constraint on (workspace_id, idempotency_key), a
    workspace could then hold exactly one job of a given type and payload
    forever, and the second session to plan the same stage would silently insert
    nothing. It is folded into the hashed material rather than into the worker's
    signature so the worker contract that Mission 0.3 verified stays unchanged.

    Two sessions collecting the same source are not the same unit of work: they
    may want data from different moments. Avoiding a *re-collection* is a
    caching decision (`data-principles.md` §12), not an idempotency one, and
    conflating them here would make freshness impossible to ask for.
    """
    context = TaskContext(
        workspace_id=workspace_id,
        research_session_id=research_session_id,
        # The correlation id deliberately does NOT enter the key: the same work
        # requested twice under two correlation ids is still the same work, and
        # including it would defeat the constraint it exists to trip.
        correlation_id="",
    )
    return idempotency_key(
        job_type,
        context,
        {"research_session_id": research_session_id, "payload": payload},
    )


# A fixed namespace so a job id is a pure function of the work it describes.
# Never regenerate this value: doing so would make every future replan produce
# new ids for work already in the ledger, and resumption would duplicate it.
JOB_ID_NAMESPACE = uuid.UUID("6f2d4a10-7b3c-5e91-a4d8-3c9b1e6f0a25")


def deterministic_job_id(key: str) -> uuid.UUID:
    """Derive a job id from its idempotency key.

    Resumability depends on this (§13). A replan after a crash recomputes the
    same keys, therefore the same ids, so re-saving the plan is a no-op on the
    ledger and the dependency edges still point at the rows that already exist.
    With random ids, every resume would insert a parallel copy of the plan and
    the first one would be orphaned mid-flight.
    """
    return uuid.uuid5(JOB_ID_NAMESPACE, key)


@dataclass(frozen=True)
class JobSpec:
    """A unit of orchestrated work, before it reaches a queue.

    Immutable: a spec is what was decided, and the mutable part (status,
    attempts, cost consumed) lives in the ledger row, not here.
    """

    job_type: str
    workspace_id: str
    research_session_id: str
    correlation_id: str

    job_id: uuid.UUID = field(default_factory=uuid.uuid4)
    payload: dict[str, object] = field(default_factory=dict)
    dependencies: tuple[uuid.UUID, ...] = ()

    queue: str | None = None
    estimated_cost_units: float = 0.0
    max_attempts: int = 1

    status: JobStatus = JobStatus.PENDING
    blocked_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.job_type:
            raise ValueError("job_type is required")
        if not self.workspace_id:
            raise ValueError(
                "workspace_id is required on every job: a worker never resolves "
                "the workspace itself (ADR-005)"
            )
        if not self.research_session_id:
            raise ValueError("research_session_id is required: cost and gaps attach to a session")
        if self.estimated_cost_units < 0:
            raise ValueError("estimated_cost_units must not be negative")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.status is JobStatus.BLOCKED and not self.blocked_reason:
            raise ValueError(
                "a BLOCKED job must carry a reason. An unexplained block is "
                "indistinguishable from work that was quietly dropped"
            )
        if self.job_id in self.dependencies:
            raise ValueError("a job cannot depend on itself")

        if self.queue is None:
            # Routing comes from the worker package so the orchestrator and the
            # broker cannot disagree about where a task lands.
            object.__setattr__(self, "queue", route_task(self.job_type).value)

    @property
    def resolved_queue(self) -> Queue:
        # `queue` is Optional in the signature so a caller may omit it and let
        # routing decide; __post_init__ has filled it by the time anything can
        # read this, and the assertion states that rather than assuming it.
        if self.queue is None:  # pragma: no cover - unreachable after __post_init__
            raise ValueError("queue was not resolved")
        return Queue(self.queue)

    def idempotency_key(self) -> str:
        return build_idempotency_key(
            self.job_type, self.workspace_id, self.research_session_id, self.payload
        )

    def task_headers(self) -> dict[str, str]:
        """The correlation contract a Celery payload must carry (ADR-004)."""
        return {
            "workspace_id": self.workspace_id,
            "research_session_id": self.research_session_id,
            "correlation_id": self.correlation_id,
        }

    def blocked(self, reason: str) -> JobSpec:
        """Return a blocked copy. The original is never mutated."""
        from dataclasses import replace

        return replace(self, status=JobStatus.BLOCKED, blocked_reason=reason)
