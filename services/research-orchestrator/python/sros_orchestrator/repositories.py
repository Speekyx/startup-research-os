"""Persistence for orchestration state.

Mission 0.4 §13. **Redis is not canonical** (ADR-008), so progress that lives
only in Celery is progress a broker restart erases. Everything the orchestrator
needs to answer "what has run, what is left, what did it cost" is written here.

**No database driver is imported.** The repositories take a `TenantDatabase`:
anything exposing `tenant_transaction(workspace_id)`. That is what keeps this
package from importing `sros_gateway`, which would invert the dependency
direction `service-boundaries.md` §4 fixes and make the graph cyclic.

**Every method takes `workspace_id` explicitly** and every query filters on it,
exactly as ADR-011 requires. RLS (ADR-012) is the second layer, entered by the
`tenant_transaction` these methods run inside, and it does not excuse the first.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterator, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from .budget import COST_UNIT, BudgetAccount, BudgetEntryKind
from .completeness import CompletenessBasis, CompletenessRecord
from .jobs import JobSpec, JobStatus, require_job_transition
from .plan import ResearchExecutionPlan

__all__ = [
    "TenantDatabase",
    "JobRow",
    "PlanRow",
    "ResearchPlanRepository",
    "JobLedgerRepository",
    "BudgetLedgerRepository",
    "CompletenessRepository",
    "OrchestratorNotFoundError",
]


class OrchestratorNotFoundError(LookupError):
    """A resource does not exist *within the requested workspace*.

    Same rule as the gateway repositories: indistinguishable from "belongs to
    another workspace", because saying an id exists elsewhere is itself a
    cross-tenant disclosure.
    """


class TenantDatabase(Protocol):
    """The only thing this package needs from a database.

    Narrow on purpose. A wider protocol would let a repository reach for a
    non-tenant connection, and the one thing every method here must not be able
    to do is run outside a tenant context.
    """

    def tenant_transaction(self, workspace_id: uuid.UUID | str) -> AbstractContextManager[Any]: ...


@dataclass(frozen=True)
class PlanRow:
    id: uuid.UUID
    workspace_id: uuid.UUID
    research_session_id: uuid.UUID
    plan_version: int
    status: str
    blocked_capabilities: tuple[str, ...]
    estimated_cost_units: float
    planner_version: str
    created_at: datetime


@dataclass(frozen=True)
class JobRow:
    id: uuid.UUID
    workspace_id: uuid.UUID
    research_session_id: uuid.UUID
    research_plan_id: uuid.UUID | None
    job_type: str
    queue: str
    payload: dict[str, Any]
    correlation_id: str
    idempotency_key: str
    status: JobStatus
    blocked_reason: str | None
    last_error: str | None
    attempts: int
    max_attempts: int
    estimated_cost_units: float
    actual_cost_units: float

    @property
    def retryable(self) -> bool:
        return self.attempts < self.max_attempts


_JOB_COLUMNS = """id, workspace_id, research_session_id, research_plan_id,
                  job_type, queue, payload, correlation_id, idempotency_key,
                  status, blocked_reason, last_error, attempts, max_attempts,
                  estimated_cost_units, actual_cost_units"""


def _job_row(row: Sequence[Any]) -> JobRow:
    return JobRow(
        id=row[0],
        workspace_id=row[1],
        research_session_id=row[2],
        research_plan_id=row[3],
        job_type=row[4],
        queue=row[5],
        payload=row[6],
        correlation_id=row[7],
        idempotency_key=row[8],
        status=JobStatus(row[9]),
        blocked_reason=row[10],
        last_error=row[11],
        attempts=row[12],
        max_attempts=row[13],
        estimated_cost_units=float(row[14]),
        actual_cost_units=float(row[15]),
    )


class ResearchPlanRepository:
    """Plans and the jobs they declare, written together."""

    def __init__(self, db: TenantDatabase) -> None:
        self._db = db

    def save(self, plan: ResearchExecutionPlan) -> PlanRow:
        """Persist a plan, its jobs and its dependency edges in ONE transaction.

        Idempotent by construction. Job ids are derived from idempotency keys
        (`jobs.deterministic_job_id`), so re-saving after a crash collides on
        the existing rows and the dependency edges still point at them. A plan
        saved twice is one plan, not two — which is what makes resumption safe
        to retry rather than something that must be attempted exactly once.
        """
        workspace = uuid.UUID(plan.workspace_id)
        session = uuid.UUID(plan.research_session_id)

        with self._db.tenant_transaction(workspace) as conn:
            existing = conn.execute(
                """SELECT id, plan_version FROM research.research_plans
                   WHERE workspace_id = %s AND research_session_id = %s AND status = 'ACTIVE'
                   ORDER BY plan_version DESC LIMIT 1""",
                (workspace, session),
            ).fetchone()

            if existing is not None:
                plan_id, version = existing[0], existing[1]
            else:
                plan_id, version = plan.plan_id, 1
                conn.execute(
                    """INSERT INTO research.research_plans
                           (id, workspace_id, research_session_id, plan_version, status,
                            blocked_capabilities, blocked_reasons,
                            estimated_cost_units, planner_version)
                       VALUES (%s, %s, %s, %s, 'ACTIVE', %s, %s, %s, %s)""",
                    (
                        plan_id,
                        workspace,
                        session,
                        version,
                        list(plan.blocked_capability_names),
                        json.dumps(plan.blocked_reasons_json(), sort_keys=True),
                        plan.estimated_cost_units,
                        plan.planner_version,
                    ),
                )

            for job in plan.ordered_jobs():
                conn.execute(
                    """INSERT INTO research.research_jobs
                           (id, workspace_id, research_session_id, research_plan_id,
                            job_type, queue, payload, correlation_id, idempotency_key,
                            status, blocked_reason, max_attempts, estimated_cost_units)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (workspace_id, idempotency_key) DO NOTHING""",
                    (
                        job.job_id,
                        workspace,
                        session,
                        plan_id,
                        job.job_type,
                        job.queue,
                        json.dumps(job.payload, sort_keys=True, default=str),
                        job.correlation_id,
                        job.idempotency_key(),
                        job.status.value,
                        job.blocked_reason,
                        job.max_attempts,
                        job.estimated_cost_units,
                    ),
                )

            for job in plan.jobs:
                for dependency in job.dependencies:
                    conn.execute(
                        """INSERT INTO research.research_job_dependencies
                               (workspace_id, job_id, depends_on_job_id)
                           VALUES (%s, %s, %s)
                           ON CONFLICT DO NOTHING""",
                        (workspace, job.job_id, dependency),
                    )

            row = conn.execute(
                """SELECT id, workspace_id, research_session_id, plan_version, status,
                          blocked_capabilities, estimated_cost_units, planner_version, created_at
                   FROM research.research_plans
                   WHERE workspace_id = %s AND id = %s""",
                (workspace, plan_id),
            ).fetchone()

        if row is None:  # pragma: no cover - the insert above guarantees it
            raise OrchestratorNotFoundError(f"plan {plan_id} vanished during save")
        return PlanRow(
            id=row[0],
            workspace_id=row[1],
            research_session_id=row[2],
            plan_version=row[3],
            status=row[4],
            blocked_capabilities=tuple(row[5]),
            estimated_cost_units=float(row[6]),
            planner_version=row[7],
            created_at=row[8],
        )

    def active_for_session(
        self, workspace_id: uuid.UUID | str, research_session_id: uuid.UUID
    ) -> PlanRow:
        with self._db.tenant_transaction(workspace_id) as conn:
            row = conn.execute(
                """SELECT id, workspace_id, research_session_id, plan_version, status,
                          blocked_capabilities, estimated_cost_units, planner_version, created_at
                   FROM research.research_plans
                   WHERE workspace_id = %s AND research_session_id = %s AND status = 'ACTIVE'
                   ORDER BY plan_version DESC LIMIT 1""",
                (_ws(workspace_id), research_session_id),
            ).fetchone()
        if row is None:
            raise OrchestratorNotFoundError(
                f"no active plan for session {research_session_id} in this workspace"
            )
        return PlanRow(
            id=row[0],
            workspace_id=row[1],
            research_session_id=row[2],
            plan_version=row[3],
            status=row[4],
            blocked_capabilities=tuple(row[5]),
            estimated_cost_units=float(row[6]),
            planner_version=row[7],
            created_at=row[8],
        )


class JobLedgerRepository:
    """The task ledger: what ran, what is running, what failed and why."""

    def __init__(self, db: TenantDatabase) -> None:
        self._db = db

    def list_for_session(
        self, workspace_id: uuid.UUID | str, research_session_id: uuid.UUID
    ) -> list[JobRow]:
        with self._db.tenant_transaction(workspace_id) as conn:
            rows = conn.execute(
                f"""SELECT {_JOB_COLUMNS} FROM research.research_jobs
                    WHERE workspace_id = %s AND research_session_id = %s
                    ORDER BY created_at, id""",  # noqa: S608 - column list is a module constant
                (_ws(workspace_id), research_session_id),
            ).fetchall()
        return [_job_row(row) for row in rows]

    def get(self, workspace_id: uuid.UUID | str, job_id: uuid.UUID) -> JobRow:
        with self._db.tenant_transaction(workspace_id) as conn:
            row = conn.execute(
                f"SELECT {_JOB_COLUMNS} FROM research.research_jobs "  # noqa: S608
                "WHERE workspace_id = %s AND id = %s",
                (_ws(workspace_id), job_id),
            ).fetchone()
        if row is None:
            raise OrchestratorNotFoundError(f"job {job_id} not found in this workspace")
        return _job_row(row)

    def statuses_for_session(
        self, workspace_id: uuid.UUID | str, research_session_id: uuid.UUID
    ) -> dict[uuid.UUID, JobStatus]:
        return {
            job.id: job.status for job in self.list_for_session(workspace_id, research_session_id)
        }

    def dependencies_for_session(
        self, workspace_id: uuid.UUID | str, research_session_id: uuid.UUID
    ) -> dict[uuid.UUID, tuple[uuid.UUID, ...]]:
        with self._db.tenant_transaction(workspace_id) as conn:
            rows = conn.execute(
                """SELECT d.job_id, d.depends_on_job_id
                   FROM research.research_job_dependencies d
                   JOIN research.research_jobs j
                     ON j.workspace_id = d.workspace_id AND j.id = d.job_id
                   WHERE d.workspace_id = %s AND j.research_session_id = %s""",
                (_ws(workspace_id), research_session_id),
            ).fetchall()
        edges: dict[uuid.UUID, list[uuid.UUID]] = {}
        for job_id, depends_on in rows:
            edges.setdefault(job_id, []).append(depends_on)
        return {job_id: tuple(sorted(deps, key=str)) for job_id, deps in edges.items()}

    def transition(
        self,
        workspace_id: uuid.UUID | str,
        job_id: uuid.UUID,
        target: JobStatus,
        *,
        last_error: str | None = None,
        blocked_reason: str | None = None,
        increment_attempt: bool = False,
        actual_cost_units: float | None = None,
    ) -> JobRow:
        """Move a job, or refuse.

        The read and the write share one transaction, so two concurrent
        dispatchers cannot both observe READY and both dispatch. `FOR UPDATE`
        is what makes that a lock rather than a hope.
        """
        ws = _ws(workspace_id)
        with self._db.tenant_transaction(ws) as conn:
            current = conn.execute(
                f"SELECT {_JOB_COLUMNS} FROM research.research_jobs "  # noqa: S608
                "WHERE workspace_id = %s AND id = %s FOR UPDATE",
                (ws, job_id),
            ).fetchone()
            if current is None:
                raise OrchestratorNotFoundError(f"job {job_id} not found in this workspace")

            job = _job_row(current)
            require_job_transition(job.status, target)

            row = conn.execute(
                f"""UPDATE research.research_jobs
                    SET status = %(status)s,
                        last_error = COALESCE(%(last_error)s, last_error),
                        blocked_reason = COALESCE(%(blocked_reason)s, blocked_reason),
                        attempts = attempts + CASE WHEN %(bump)s THEN 1 ELSE 0 END,
                        actual_cost_units = COALESCE(%(actual)s, actual_cost_units),
                        dispatched_at = CASE WHEN %(status)s = 'DISPATCHED'
                                             THEN now() ELSE dispatched_at END,
                        started_at = CASE WHEN %(status)s = 'RUNNING'
                                          THEN COALESCE(started_at, now()) ELSE started_at END,
                        finished_at = CASE WHEN %(status)s IN
                                             ('SUCCEEDED','FAILED','BLOCKED','CANCELLED')
                                           THEN now() ELSE finished_at END,
                        updated_at = now()
                    WHERE workspace_id = %(workspace_id)s AND id = %(job_id)s
                    RETURNING {_JOB_COLUMNS}""",  # noqa: S608 - column list is a module constant
                {
                    "status": target.value,
                    "last_error": last_error,
                    "blocked_reason": blocked_reason,
                    "bump": increment_attempt,
                    "actual": actual_cost_units,
                    "workspace_id": ws,
                    "job_id": job_id,
                },
            ).fetchone()
        return _job_row(row)

    def mark_ready(
        self, workspace_id: uuid.UUID | str, job_ids: Sequence[uuid.UUID]
    ) -> list[JobRow]:
        return [self.transition(workspace_id, job_id, JobStatus.READY) for job_id in job_ids]

    def cancel_pending(
        self, workspace_id: uuid.UUID | str, research_session_id: uuid.UUID
    ) -> list[JobRow]:
        """Cancel everything not already terminal or already handed to a worker.

        DISPATCHED and RUNNING jobs are deliberately left alone: see
        `orchestrator.ResearchOrchestrator.cancel` for why this system does not
        claim it can stop work that is already outside its process.
        """
        cancelled: list[JobRow] = []
        for job in self.list_for_session(workspace_id, research_session_id):
            if job.status in (JobStatus.PENDING, JobStatus.READY):
                cancelled.append(
                    self.transition(
                        workspace_id,
                        job.id,
                        JobStatus.CANCELLED,
                        blocked_reason="session cancelled before dispatch",
                    )
                )
        return cancelled


class BudgetLedgerRepository:
    """Reservations and actuals, per session and per job."""

    def __init__(self, db: TenantDatabase) -> None:
        self._db = db

    def account_for_session(
        self,
        workspace_id: uuid.UUID | str,
        research_session_id: uuid.UUID,
    ) -> BudgetAccount:
        """Read the configured ceiling and fold the ledger into an account.

        RELEASE entries subtract from reservations rather than being deleted:
        an audit that cannot see a released reservation cannot explain why a
        session's committed total went down.
        """
        ws = _ws(workspace_id)
        with self._db.tenant_transaction(ws) as conn:
            session = conn.execute(
                """SELECT budget_max_cost_units, budget_max_llm_calls
                   FROM research.research_sessions
                   WHERE workspace_id = %s AND id = %s""",
                (ws, research_session_id),
            ).fetchone()
            if session is None:
                raise OrchestratorNotFoundError(
                    f"research session {research_session_id} not found in this workspace"
                )
            totals = conn.execute(
                """SELECT entry_kind, COALESCE(SUM(cost_units), 0), COUNT(*)
                   FROM research.session_budget_entries
                   WHERE workspace_id = %s AND research_session_id = %s
                   GROUP BY entry_kind""",
                (ws, research_session_id),
            ).fetchall()

        by_kind = {kind: (float(total), int(count)) for kind, total, count in totals}
        reserved = by_kind.get(BudgetEntryKind.RESERVATION.value, (0.0, 0))[0]
        released = by_kind.get(BudgetEntryKind.RELEASE.value, (0.0, 0))[0]
        actual, actual_count = by_kind.get(BudgetEntryKind.ACTUAL.value, (0.0, 0))

        return BudgetAccount(
            research_session_id=str(research_session_id),
            configured_cost_units=(float(session[0]) if session[0] is not None else None),
            configured_llm_calls=(int(session[1]) if session[1] is not None else None),
            # A reservation that became an actual is released at the same time,
            # so outstanding reservations are reservations minus releases.
            reserved_cost_units=max(0.0, reserved - released),
            actual_cost_units=actual,
            llm_calls=actual_count,
        )

    def record(
        self,
        workspace_id: uuid.UUID | str,
        research_session_id: uuid.UUID,
        kind: BudgetEntryKind,
        cost_units: float,
        *,
        job_id: uuid.UUID | None = None,
        provider: str | None = None,
        model: str | None = None,
        tier: str | None = None,
        pricing_version: str | None = None,
        correlation_id: str | None = None,
    ) -> uuid.UUID:
        ws = _ws(workspace_id)
        entry_id = uuid.uuid4()
        with self._db.tenant_transaction(ws) as conn:
            conn.execute(
                """INSERT INTO research.session_budget_entries
                       (id, workspace_id, research_session_id, job_id, entry_kind,
                        cost_units, currency, provider, model, tier, pricing_version,
                        correlation_id)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    entry_id,
                    ws,
                    research_session_id,
                    job_id,
                    kind.value,
                    cost_units,
                    COST_UNIT,
                    provider,
                    model,
                    tier,
                    pricing_version,
                    correlation_id,
                ),
            )
        return entry_id

    def entries_for_session(
        self, workspace_id: uuid.UUID | str, research_session_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        ws = _ws(workspace_id)
        with self._db.tenant_transaction(ws) as conn:
            rows = conn.execute(
                """SELECT id, job_id, entry_kind, cost_units, currency, provider,
                          model, tier, pricing_version, recorded_at
                   FROM research.session_budget_entries
                   WHERE workspace_id = %s AND research_session_id = %s
                   ORDER BY recorded_at, id""",
                (ws, research_session_id),
            ).fetchall()
        return [
            {
                "id": r[0],
                "job_id": r[1],
                "entry_kind": r[2],
                "cost_units": float(r[3]),
                "currency": r[4],
                "provider": r[5],
                "model": r[6],
                "tier": r[7],
                "pricing_version": r[8],
                "recorded_at": r[9],
            }
            for r in rows
        ]


class CompletenessRepository:
    """Research Completeness observations. No formula, only the record."""

    def __init__(self, db: TenantDatabase) -> None:
        self._db = db

    def record(self, workspace_id: uuid.UUID | str, record: CompletenessRecord) -> uuid.UUID:
        ws = _ws(workspace_id)
        record_id = uuid.uuid4()
        with self._db.tenant_transaction(ws) as conn:
            conn.execute(
                """INSERT INTO research.research_completeness_records
                       (id, workspace_id, research_session_id, measured_score,
                        estimated_score, basis, incompleteness_reasons, blocked_capabilities)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    record_id,
                    ws,
                    uuid.UUID(record.research_session_id),
                    record.measured_score,
                    record.estimated_score,
                    record.basis.value,
                    list(record.incompleteness_reasons),
                    list(record.blocked_capabilities),
                ),
            )
        return record_id

    def latest_for_session(
        self, workspace_id: uuid.UUID | str, research_session_id: uuid.UUID
    ) -> CompletenessRecord | None:
        ws = _ws(workspace_id)
        with self._db.tenant_transaction(ws) as conn:
            row = conn.execute(
                """SELECT measured_score, estimated_score, basis,
                          incompleteness_reasons, blocked_capabilities
                   FROM research.research_completeness_records
                   WHERE workspace_id = %s AND research_session_id = %s
                   ORDER BY computed_at DESC, id DESC LIMIT 1""",
                (ws, research_session_id),
            ).fetchone()
        if row is None:
            return None
        return CompletenessRecord(
            research_session_id=str(research_session_id),
            basis=CompletenessBasis(row[2]),
            measured_score=row[0],
            estimated_score=row[1],
            incompleteness_reasons=tuple(row[3]),
            blocked_capabilities=tuple(row[4]),
        )


def _ws(workspace_id: uuid.UUID | str) -> uuid.UUID:
    """Fail closed. No default, in any environment (ADR-005)."""
    if workspace_id is None or workspace_id == "":
        raise ValueError(
            "a tenant-scoped orchestrator call requires an explicit workspace_id; "
            "there is no default (ADR-005)"
        )
    if isinstance(workspace_id, uuid.UUID):
        return workspace_id
    return uuid.UUID(str(workspace_id))


def _iter_specs(jobs: Sequence[JobSpec]) -> Iterator[JobSpec]:  # pragma: no cover - helper
    yield from jobs
