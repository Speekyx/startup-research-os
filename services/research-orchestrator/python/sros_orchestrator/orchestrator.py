"""The orchestrator: coordination, never analysis.

Mission 0.4 §8. It owns the ResearchSession execution lifecycle, the plan, the
budget, job dispatch, progress, failure, resumability and Research Completeness
coordination.

It owns none of the work. There is no scraping here, no embedding, no scoring
formula, no competitor logic and no market analysis — those belong to the
contexts that answer questions. The orchestrator decides which questions to ask
(`services/research-orchestrator/README.md` §Responsibility).

**Nothing in this module can dispatch blocked work.** `dispatchable` filters on
the ledger status, and a job the planner marked BLOCKED never becomes READY.
That is the mechanical guard behind §32 and §33: D-07 and D-03 are not enforced
by remembering.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from sros_contracts import ResearchContext, ResearchSessionStatus

from .budget import BudgetEntryKind, BudgetGuard
from .completeness import CompletenessRecord
from .dag import blocked_by_dependencies, ready_job_ids
from .jobs import JobSpec, JobStatus
from .lifecycle import (
    cancellation_target,
    is_terminal,
    require_transition,
)
from .plan import ResearchExecutionPlan, ResearchPlanner
from .repositories import (
    BudgetLedgerRepository,
    CompletenessRepository,
    JobLedgerRepository,
    JobRow,
    OrchestratorNotFoundError,
    ResearchPlanRepository,
    TenantDatabase,
)
from .sources import RegistrySourceAvailability, SourceAvailabilityProvider

__all__ = [
    "Dispatcher",
    "RecordingDispatcher",
    "CeleryDispatcher",
    "AdvanceReport",
    "SessionStateRepository",
    "ResearchOrchestrator",
]


class Dispatcher(Protocol):
    """Hands a job to the queue and returns the transport's task id."""

    def dispatch(self, job: JobRow, headers: dict[str, str]) -> str: ...


@dataclass
class RecordingDispatcher:
    """Records what would be dispatched. Sends nothing.

    The default. While every domain capability is blocked there is no worker
    that could execute a real job, and a dispatcher that silently dropped
    messages onto a queue nobody consumes would look like progress.
    """

    dispatched: list[tuple[uuid.UUID, dict[str, str]]] = field(default_factory=list)

    def dispatch(self, job: JobRow, headers: dict[str, str]) -> str:
        self.dispatched.append((job.id, headers))
        return f"recorded:{job.id}"


class CeleryDispatcher:
    """Sends a job to its queue over Celery.

    Celery is imported lazily so the orchestrator stays importable — and
    testable — without a broker, exactly as `sros_workers.queues` does.
    """

    def __init__(self, app: Any | None = None) -> None:
        self._app = app

    def _resolve(self) -> Any:
        if self._app is None:
            from sros_workers.celery_app import create_celery_app

            self._app = create_celery_app()
        return self._app

    def dispatch(self, job: JobRow, headers: dict[str, str]) -> str:
        result = self._resolve().send_task(
            job.job_type,
            kwargs={"headers": headers, "payload": job.payload},
            queue=job.queue,
            # The ledger id travels as the Celery task id so a worker's report
            # can be matched back to a row without a second lookup.
            task_id=str(job.id),
        )
        return str(result.id)


@dataclass(frozen=True)
class AdvanceReport:
    """What one scheduling pass did, and what it deliberately did not do.

    Refusals are returned rather than logged and dropped: a job that was not
    dispatched becomes a research gap, and a gap with no recorded cause is the
    silent partial coverage that inflates every downstream confidence.
    """

    dispatched: tuple[uuid.UUID, ...] = ()
    refused_for_budget: tuple[tuple[uuid.UUID, str], ...] = ()
    blocked: tuple[tuple[uuid.UUID, str], ...] = ()
    unreachable: tuple[uuid.UUID, ...] = ()

    @property
    def made_progress(self) -> bool:
        return bool(self.dispatched)


class SessionStateRepository:
    """ResearchSession status, owned by the orchestrator (§9).

    The gateway still exposes read endpoints over the same rows. What moved here
    is the authority to change `status`: `service-boundaries.md` §5 assigns
    `research_session` to this context, and a transition decided in two places
    is a transition decided in neither.
    """

    def __init__(self, db: TenantDatabase) -> None:
        self._db = db

    def status(
        self, workspace_id: uuid.UUID | str, research_session_id: uuid.UUID
    ) -> ResearchSessionStatus:
        with self._db.tenant_transaction(workspace_id) as conn:
            row = conn.execute(
                "SELECT status FROM research.research_sessions WHERE workspace_id = %s AND id = %s",
                (_ws(workspace_id), research_session_id),
            ).fetchone()
        if row is None:
            raise OrchestratorNotFoundError(
                f"research session {research_session_id} not found in this workspace"
            )
        return ResearchSessionStatus(row[0])

    def transition(
        self,
        workspace_id: uuid.UUID | str,
        research_session_id: uuid.UUID,
        target: ResearchSessionStatus,
        *,
        failure_reason: str | None = None,
    ) -> ResearchSessionStatus:
        ws = _ws(workspace_id)
        with self._db.tenant_transaction(ws) as conn:
            current = conn.execute(
                "SELECT status FROM research.research_sessions "
                "WHERE workspace_id = %s AND id = %s FOR UPDATE",
                (ws, research_session_id),
            ).fetchone()
            if current is None:
                raise OrchestratorNotFoundError(
                    f"research session {research_session_id} not found in this workspace"
                )
            require_transition(ResearchSessionStatus(current[0]), target)

            conn.execute(
                """UPDATE research.research_sessions
                   SET status = %(status)s,
                       failure_reason = COALESCE(%(failure_reason)s, failure_reason),
                       started_at = CASE WHEN %(status)s = 'PLANNING'
                                         THEN COALESCE(started_at, now()) ELSE started_at END,
                       completed_at = CASE WHEN %(status)s IN ('COMPLETED','FAILED','CANCELLED')
                                           THEN now() ELSE completed_at END
                   WHERE workspace_id = %(workspace_id)s AND id = %(session_id)s""",
                {
                    "status": target.value,
                    "failure_reason": failure_reason,
                    "workspace_id": ws,
                    "session_id": research_session_id,
                },
            )
        return target

    def research_context(
        self, workspace_id: uuid.UUID | str, research_session_id: uuid.UUID
    ) -> ResearchContext:
        """The immutable snapshot the session was created with.

        Re-planning reads the snapshot rather than a project default, so a
        resumed session plans the specification it actually ran with
        (Ontology V2 §11.3).
        """
        with self._db.tenant_transaction(workspace_id) as conn:
            row = conn.execute(
                "SELECT research_context FROM research.research_sessions "
                "WHERE workspace_id = %s AND id = %s",
                (_ws(workspace_id), research_session_id),
            ).fetchone()
        if row is None:
            raise OrchestratorNotFoundError(
                f"research session {research_session_id} not found in this workspace"
            )
        return ResearchContext.from_json(row[0])


def _registry_for(db: Any) -> SourceAvailabilityProvider | None:
    """Use the real Source Registry when the given database can reach it.

    The registry is global and carries no `workspace_id`, so it is read over a
    plain connection rather than a tenant transaction (Mission 1.0 §25).
    `TenantDatabase` does not promise one, hence the check: a database that
    cannot open a non-tenant connection yields `None`, the planner falls back
    to `UnconsultedRegistry`, and acquisition stays blocked. Failing that way
    round is the point — an unwired registry must never read as permission.
    """
    if hasattr(db, "connection"):
        return RegistrySourceAvailability(db)
    return None


class ResearchOrchestrator:
    """Coordinates one workspace's research sessions."""

    def __init__(
        self,
        db: TenantDatabase,
        dispatcher: Dispatcher | None = None,
        planner: ResearchPlanner | None = None,
        sources: SourceAvailabilityProvider | None = None,
        # The second acquisition gate (Mission 1.5) and the normalization gate
        # (Mission 1.6). Supplied by the composition root, never imported: a
        # service may not import another service's package
        # (`service-boundaries.md`). Both empty by default, so a caller that
        # forgets to wire one gets a refusal rather than a permission.
        implemented_collectors: frozenset[str] = frozenset(),
        implemented_normalizers: frozenset[str] = frozenset(),
    ) -> None:
        self._db = db
        self._dispatcher = dispatcher or RecordingDispatcher()
        self._planner = planner or ResearchPlanner(
            sources=sources or _registry_for(db),
            implemented_collectors=implemented_collectors,
            implemented_normalizers=implemented_normalizers,
        )
        self.plans = ResearchPlanRepository(db)
        self.jobs = JobLedgerRepository(db)
        self.budgets = BudgetLedgerRepository(db)
        self.completeness = CompletenessRepository(db)
        self.sessions = SessionStateRepository(db)

    # -- planning -----------------------------------------------------------

    def plan_session(
        self,
        workspace_id: uuid.UUID | str,
        research_session_id: uuid.UUID,
        correlation_id: str,
        context: ResearchContext | None = None,
    ) -> ResearchExecutionPlan:
        """Build and persist the plan, and move the session to PLANNING.

        Safe to call twice. Job ids are deterministic and the plan insert is
        conditional, so a replan after a crash converges on the ledger that
        already exists rather than duplicating it (§13).
        """
        ws = _ws(workspace_id)
        resolved = context or self.sessions.research_context(ws, research_session_id)

        current = self.sessions.status(ws, research_session_id)
        if current is ResearchSessionStatus.PENDING:
            self.sessions.transition(ws, research_session_id, ResearchSessionStatus.PLANNING)

        plan = self._planner.plan(
            workspace_id=str(ws),
            research_session_id=str(research_session_id),
            correlation_id=correlation_id,
            context=resolved,
        )
        self.plans.save(plan)
        return plan

    # -- scheduling ---------------------------------------------------------

    def advance(
        self,
        workspace_id: uuid.UUID | str,
        research_session_id: uuid.UUID,
    ) -> AdvanceReport:
        """One scheduling pass: promote what is ready, dispatch what fits.

        Ordering inside the pass matters. Dependencies are resolved first,
        budget second, dispatch last — so a job that cannot be afforded is never
        handed to a queue, and the ceiling is checked before the money is spent
        rather than after (§16).
        """
        ws = _ws(workspace_id)
        ledger = self.jobs.list_for_session(ws, research_session_id)
        if not ledger:
            return AdvanceReport()

        dependencies = self.jobs.dependencies_for_session(ws, research_session_id)
        specs = [_spec_from_row(row, dependencies.get(row.id, ())) for row in ledger]
        statuses = {row.id: row.status for row in ledger}

        # 1. Dependencies satisfied -> READY. A blocked or failed dependency
        #    never satisfies anything, so its dependents stay where they are and
        #    are reported as unreachable below.
        for job_id in ready_job_ids(specs, statuses):
            self.jobs.transition(ws, job_id, JobStatus.READY)
            statuses[job_id] = JobStatus.READY

        unreachable = tuple(sorted(blocked_by_dependencies(specs, statuses), key=str))

        # 2. Budget, then dispatch.
        account = self.budgets.account_for_session(ws, research_session_id)
        guard = BudgetGuard(account)

        dispatched: list[uuid.UUID] = []
        refused: list[tuple[uuid.UUID, str]] = []
        blocked: list[tuple[uuid.UUID, str]] = []

        for row in self.jobs.list_for_session(ws, research_session_id):
            if row.status is JobStatus.BLOCKED:
                blocked.append((row.id, row.blocked_reason or "blocked"))
                continue
            if row.status is not JobStatus.READY:
                continue

            decision = guard.evaluate(row.estimated_cost_units)
            if not decision.allowed:
                # NOT a failure and NOT a new status. The session will complete
                # with reduced Research Completeness (Ontology V2 §15).
                refused.append((row.id, decision.reason))
                continue

            # Reserve BEFORE dispatch. Two passes racing on the same remaining
            # budget would otherwise both fit and together overshoot.
            self.budgets.record(
                ws,
                research_session_id,
                BudgetEntryKind.RESERVATION,
                row.estimated_cost_units,
                job_id=row.id,
                correlation_id=row.correlation_id,
            )
            self.jobs.transition(ws, row.id, JobStatus.DISPATCHED, increment_attempt=True)
            self._dispatcher.dispatch(
                row,
                {
                    "workspace_id": str(ws),
                    "research_session_id": str(research_session_id),
                    "correlation_id": row.correlation_id,
                },
            )
            dispatched.append(row.id)

            account = self.budgets.account_for_session(ws, research_session_id)
            guard = BudgetGuard(account)

        return AdvanceReport(
            dispatched=tuple(dispatched),
            refused_for_budget=tuple(refused),
            blocked=tuple(blocked),
            unreachable=unreachable,
        )

    # -- progress reporting -------------------------------------------------

    def report_started(self, workspace_id: uuid.UUID | str, job_id: uuid.UUID) -> JobRow:
        return self.jobs.transition(workspace_id, job_id, JobStatus.RUNNING)

    def report_success(
        self,
        workspace_id: uuid.UUID | str,
        job_id: uuid.UUID,
        actual_cost_units: float = 0.0,
        *,
        provider: str | None = None,
        model: str | None = None,
        tier: str | None = None,
        pricing_version: str | None = None,
    ) -> JobRow:
        """Record success and convert the reservation into an actual."""
        ws = _ws(workspace_id)
        row = self.jobs.get(ws, job_id)
        self.budgets.record(
            ws,
            row.research_session_id,
            BudgetEntryKind.RELEASE,
            row.estimated_cost_units,
            job_id=job_id,
            correlation_id=row.correlation_id,
        )
        self.budgets.record(
            ws,
            row.research_session_id,
            BudgetEntryKind.ACTUAL,
            actual_cost_units,
            job_id=job_id,
            provider=provider,
            model=model,
            tier=tier,
            pricing_version=pricing_version,
            correlation_id=row.correlation_id,
        )
        return self.jobs.transition(
            ws, job_id, JobStatus.SUCCEEDED, actual_cost_units=actual_cost_units
        )

    def report_failure(
        self,
        workspace_id: uuid.UUID | str,
        job_id: uuid.UUID,
        error: str,
        *,
        retryable: bool,
    ) -> JobRow:
        """Record a failure and decide whether the job returns to the pool.

        A retryable failure with attempts left goes back to READY; anything else
        is FAILED. A permanently failed job becomes a research gap and lowers
        Research Completeness — it does not fail the session (ADR-004).
        """
        ws = _ws(workspace_id)
        row = self.jobs.get(ws, job_id)

        # The reservation is released either way: work that did not happen must
        # not keep holding budget that other work could use.
        self.budgets.record(
            ws,
            row.research_session_id,
            BudgetEntryKind.RELEASE,
            row.estimated_cost_units,
            job_id=job_id,
            correlation_id=row.correlation_id,
        )

        if retryable and row.retryable:
            return self.jobs.transition(ws, job_id, JobStatus.READY, last_error=error)
        return self.jobs.transition(ws, job_id, JobStatus.FAILED, last_error=error)

    # -- cancellation (§14) -------------------------------------------------

    def cancel(
        self, workspace_id: uuid.UUID | str, research_session_id: uuid.UUID
    ) -> AdvanceReport:
        """Stop a session, honestly.

        What this DOES do:
          * moves the session to CANCELLED where the lifecycle allows it,
          * cancels every job that has not yet been handed to a worker, so no
            further work is dispatched.

        What it does NOT do, and does not pretend to: stop work already running
        inside a worker. Celery revocation is advisory, a process mid-HTTP-call
        does not observe it, and `task_acks_late` means a killed worker returns
        the job to the queue. Claiming instant distributed cancellation would
        make callers believe a resource was freed when it was not.

        DISPATCHED and RUNNING jobs are therefore left to finish or fail. Their
        results are still recorded: a cancelled session with three completed
        jobs did three jobs, and hiding that would make the ledger wrong.
        """
        ws = _ws(workspace_id)
        cancelled = self.jobs.cancel_pending(ws, research_session_id)

        current = self.sessions.status(ws, research_session_id)
        target = cancellation_target(current)
        if target is not None:
            self.sessions.transition(
                ws, research_session_id, target, failure_reason="cancelled on request"
            )

        in_flight = [
            row.id
            for row in self.jobs.list_for_session(ws, research_session_id)
            if row.status in (JobStatus.DISPATCHED, JobStatus.RUNNING)
        ]
        return AdvanceReport(
            blocked=tuple((row.id, "cancelled before dispatch") for row in cancelled),
            unreachable=tuple(sorted(in_flight, key=str)),
        )

    # -- resumability (§13) -------------------------------------------------

    def resume(
        self, workspace_id: uuid.UUID | str, research_session_id: uuid.UUID
    ) -> AdvanceReport:
        """Continue a session after a crash or a restart.

        There is no in-memory state to restore, which is the point. Everything
        the scheduler needs — plan, ledger, dependency edges, budget entries —
        is in PostgreSQL, so resuming is `advance()` and nothing else.

        Jobs left DISPATCHED or RUNNING by a dead worker are returned to READY
        if they have attempts left. That is safe precisely because delivery is
        at-least-once and every job is idempotent (ADR-004): the worst case is
        the work happening twice and the second result colliding on the
        idempotency key.
        """
        ws = _ws(workspace_id)
        for row in self.jobs.list_for_session(ws, research_session_id):
            if row.status in (JobStatus.DISPATCHED, JobStatus.RUNNING) and row.retryable:
                self.jobs.transition(
                    ws,
                    row.id,
                    JobStatus.READY,
                    last_error="reclaimed after restart: no worker reported an outcome",
                )
        return self.advance(ws, research_session_id)

    # -- completion ---------------------------------------------------------

    def finalize(
        self,
        workspace_id: uuid.UUID | str,
        research_session_id: uuid.UUID,
        plan: ResearchExecutionPlan | None = None,
    ) -> CompletenessRecord:
        """Record Research Completeness for a session that has stopped working.

        No score is computed. With capabilities blocked there is nothing to
        measure and no basis on which to estimate, so the record is UNKNOWN and
        carries the reasons (§17). A number here would be an invention.
        """
        ws = _ws(workspace_id)
        rows = self.jobs.list_for_session(ws, research_session_id)

        blocked_capabilities = sorted(
            {
                str(row.payload.get("capability"))
                for row in rows
                if row.status is JobStatus.BLOCKED and row.payload.get("capability")
            }
        )
        reasons = list(plan.incompleteness_reasons()) if plan else []
        reasons.extend(
            f"job {row.job_type} failed: {row.last_error}"
            for row in rows
            if row.status is JobStatus.FAILED and row.last_error
        )
        if not reasons and blocked_capabilities:
            reasons = [f"{name} was not executed" for name in blocked_capabilities]

        record = CompletenessRecord.unknown(
            research_session_id=str(research_session_id),
            incompleteness_reasons=tuple(reasons),
            blocked_capabilities=tuple(blocked_capabilities),
        )
        self.completeness.record(ws, record)
        return record

    def session_is_finished(
        self, workspace_id: uuid.UUID | str, research_session_id: uuid.UUID
    ) -> bool:
        ws = _ws(workspace_id)
        if is_terminal(self.sessions.status(ws, research_session_id)):
            return True
        rows = self.jobs.list_for_session(ws, research_session_id)
        return bool(rows) and all(
            row.status
            in (JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.BLOCKED, JobStatus.CANCELLED)
            for row in rows
        )


def _spec_from_row(row: JobRow, dependencies: Sequence[uuid.UUID]) -> JobSpec:
    """Rebuild a spec from the ledger so the DAG helpers can be reused.

    The ledger is the source of truth after planning, so the graph the scheduler
    reasons about is read back from the database rather than kept in memory.
    That is what makes a resumed pass identical to a fresh one.
    """
    return JobSpec(
        job_id=row.id,
        job_type=row.job_type,
        workspace_id=str(row.workspace_id),
        research_session_id=str(row.research_session_id),
        correlation_id=row.correlation_id,
        payload=dict(row.payload),
        dependencies=tuple(dependencies),
        queue=row.queue,
        estimated_cost_units=row.estimated_cost_units,
        max_attempts=row.max_attempts,
        status=row.status,
        blocked_reason=row.blocked_reason,
    )


def _ws(workspace_id: uuid.UUID | str) -> uuid.UUID:
    if workspace_id is None or workspace_id == "":
        raise ValueError(
            "a tenant-scoped orchestrator call requires an explicit workspace_id; "
            "there is no default (ADR-005)"
        )
    if isinstance(workspace_id, uuid.UUID):
        return workspace_id
    return uuid.UUID(str(workspace_id))
