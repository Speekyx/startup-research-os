"""Orchestration against a real PostgreSQL.

Mission 0.4 §36, the half that needs a database: persistence, duplicate
delivery, resumption after a restart, budget accounting and cancellation.

It lives in the gateway suite because the stack fixtures are here and because
`sros_gateway.db.pool.Database` is the concrete `TenantDatabase` the
orchestrator was written against. The orchestrator itself imports nothing from
this package — the dependency runs one way only (`service-boundaries.md` §4).

Every test runs through `tenant_transaction`, so every assertion below is also
an assertion that the RLS policies do not get in the way of legitimate work.

The two workspaces are this module's own, created before each test and dropped
after it by `own_workspaces` below. Nearly every test here starts by creating a
project and a session, and the seeded workspaces kept every one of them.
"""

from __future__ import annotations

import uuid

import pytest
from sros_contracts import CONTRACT_VERSION, ONTOLOGY_VERSION, ResearchContext
from sros_contracts import ResearchSessionStatus as Status
from sros_gateway.db.repositories import ResearchProjectRepository, ResearchSessionRepository
from sros_orchestrator import BudgetEntryKind, Capability, CompletenessBasis, JobSpec, JobStatus
from sros_orchestrator.orchestrator import RecordingDispatcher, ResearchOrchestrator
from sros_orchestrator.repositories import OrchestratorNotFoundError

from .conftest import WORKSPACE_ORCH_P, WORKSPACE_ORCH_Q, needs_postgres

CORRELATION = "corr-orchestration"


@pytest.fixture(autouse=True)
def own_workspaces(orchestration_workspaces) -> None:
    """Every test in this module runs in workspaces of its own.

    Autouse, and it hands nothing back: `_new_session` already defaults to
    WORKSPACE_ORCH_P, so what a test needs is not a value but a guarantee --
    that the workspaces exist when it starts and are gone when it ends.
    """


def _context(**overrides: object) -> ResearchContext:
    payload: dict[str, object] = {"market_scope": {"type": "COUNTRY", "countries": ["FR"]}}
    payload.update(overrides)
    return ResearchContext.from_json(payload)


def _new_session(database, workspace=WORKSPACE_ORCH_P, context: ResearchContext | None = None):
    project = ResearchProjectRepository(database).create(workspace, f"orch-{uuid.uuid4().hex[:8]}")
    return ResearchSessionRepository(database).create(
        workspace_id=workspace,
        project_id=project.id,
        context=context or _context(),
        contract_version=CONTRACT_VERSION,
        ontology_version=ONTOLOGY_VERSION,
    )


@pytest.fixture
def orchestrator(database) -> ResearchOrchestrator:
    return ResearchOrchestrator(database, dispatcher=RecordingDispatcher())


def _probe_job(session_row, **kwargs: object) -> JobSpec:
    """A routable infrastructure job.

    Every DOMAIN job type is blocked, so the dispatch machinery is exercised
    with a maintenance-queue probe. That is the same separation the planner
    makes: the mechanism is real, the domain stages are not runnable.
    """
    return JobSpec(
        job_type="maintenance.probe",
        workspace_id=str(session_row.workspace_id),
        research_session_id=str(session_row.id),
        correlation_id=CORRELATION,
        **kwargs,  # type: ignore[arg-type]
    )


def _save_jobs(orchestrator: ResearchOrchestrator, session_row, jobs: list[JobSpec]) -> None:
    """Persist an ad-hoc job set through the plan repository."""
    from sros_orchestrator.plan import ResearchExecutionPlan

    plan = ResearchExecutionPlan(
        workspace_id=str(session_row.workspace_id),
        research_session_id=str(session_row.id),
        correlation_id=CORRELATION,
        jobs=tuple(jobs),
        blocked=(),
    )
    orchestrator.plans.save(plan)


# ================================================================== planning


@needs_postgres
class TestPlanPersistence:
    def test_a_plan_and_its_jobs_are_persisted_together(self, database, orchestrator) -> None:
        session = _new_session(database)
        plan = orchestrator.plan_session(WORKSPACE_ORCH_P, session.id, CORRELATION)

        row = orchestrator.plans.active_for_session(WORKSPACE_ORCH_P, session.id)
        assert row.plan_version == 1
        assert row.planner_version == plan.planner_version
        assert set(row.blocked_capabilities) == {c.value for c in Capability}

        ledger = orchestrator.jobs.list_for_session(WORKSPACE_ORCH_P, session.id)
        assert len(ledger) == len(plan.jobs)

    def test_planning_moves_the_session_out_of_pending(self, database, orchestrator) -> None:
        session = _new_session(database)
        assert session.status is Status.PENDING
        orchestrator.plan_session(WORKSPACE_ORCH_P, session.id, CORRELATION)
        assert orchestrator.sessions.status(WORKSPACE_ORCH_P, session.id) is Status.PLANNING

    def test_replanning_converges_on_the_existing_ledger(self, database, orchestrator) -> None:
        """§13. A replan after a crash must not insert a parallel copy of the
        plan and orphan the one already in flight."""
        session = _new_session(database)
        orchestrator.plan_session(WORKSPACE_ORCH_P, session.id, CORRELATION)
        first = {j.id for j in orchestrator.jobs.list_for_session(WORKSPACE_ORCH_P, session.id)}

        orchestrator.plan_session(WORKSPACE_ORCH_P, session.id, "a-different-correlation")
        second = orchestrator.jobs.list_for_session(WORKSPACE_ORCH_P, session.id)

        assert {j.id for j in second} == first
        assert len(second) == len(first)
        assert orchestrator.plans.active_for_session(WORKSPACE_ORCH_P, session.id).plan_version == 1

    def test_the_dependency_edges_are_persisted(self, database, orchestrator) -> None:
        session = _new_session(database)
        plan = orchestrator.plan_session(WORKSPACE_ORCH_P, session.id, CORRELATION)
        edges = orchestrator.jobs.dependencies_for_session(WORKSPACE_ORCH_P, session.id)
        expected = {job.job_id: job.dependencies for job in plan.jobs if job.dependencies}
        assert edges == {k: tuple(sorted(v, key=str)) for k, v in expected.items()}

    def test_a_plan_belongs_to_one_workspace_only(self, database, orchestrator) -> None:
        session = _new_session(database)
        orchestrator.plan_session(WORKSPACE_ORCH_P, session.id, CORRELATION)
        with pytest.raises(OrchestratorNotFoundError):
            orchestrator.plans.active_for_session(WORKSPACE_ORCH_Q, session.id)


# ============================================== blocked work is never dispatched


@needs_postgres
class TestBlockedWorkIsNeverDispatched:
    def test_a_planned_session_dispatches_nothing(self, database) -> None:
        """§32 and §33, mechanically. Every domain stage is blocked, so a full
        scheduling pass over a real plan hands nothing to any queue."""
        dispatcher = RecordingDispatcher()
        orchestrator = ResearchOrchestrator(database, dispatcher=dispatcher)
        session = _new_session(database)
        orchestrator.plan_session(WORKSPACE_ORCH_P, session.id, CORRELATION)

        report = orchestrator.advance(WORKSPACE_ORCH_P, session.id)

        assert report.dispatched == ()
        assert dispatcher.dispatched == []
        assert len(report.blocked) == len(Capability)

    def test_the_acquisition_block_comes_from_the_real_registry(
        self, database, orchestrator
    ) -> None:
        """Mission 1.0 §22, end to end. D-07 is resolved, so the reason must be
        read from `registry.source_eligibility` rather than restated in code.

        Since Mission 1.4 acquisition has two gates and which one answers
        depends on the database this runs against -- whether anyone has recorded
        a condition verification. The expectation is therefore DERIVED from what
        the registry said rather than hard-coded, so the test asserts the rule
        instead of asserting one deployment's state."""
        session = _new_session(database)
        plan = orchestrator.plan_session(WORKSPACE_ORCH_P, session.id, CORRELATION)
        rows = orchestrator.jobs.list_for_session(WORKSPACE_ORCH_P, session.id)
        acquisition = next(r for r in rows if r.job_type == "acquire.collect")
        assert acquisition.status is JobStatus.BLOCKED
        assert acquisition.blocked_reason is not None
        assert "D-07" not in acquisition.blocked_reason

        # The registry WAS consulted: a fallback to "not consulted" would also
        # block, and would look identical unless the test insists on the
        # difference.
        assert plan.source_availability is not None
        assert plan.source_availability.consulted

        expected = (
            "NO-COLLECTOR-IMPLEMENTED" if plan.eligible_source_ids else "SOURCE-REGISTRY-GATE"
        )
        assert acquisition.blocked_reason.startswith(expected), acquisition.blocked_reason

    def test_the_acquisition_block_names_each_refused_source(self, database, orchestrator) -> None:
        """A blocker a reader can act on: which source, and what stopped it.

        The refused sources are still named when other sources have passed. A
        block whose explanation got worse as the registry got better would be a
        regression, so this holds under either acquisition gate."""
        session = _new_session(database)
        plan = orchestrator.plan_session(WORKSPACE_ORCH_P, session.id, CORRELATION)
        per_source = plan.blocked_source_reasons()
        assert per_source, "the gate must name the sources it refused"
        assert any(r.startswith("tiktok (PROHIBITED)") for r in per_source), per_source
        assert any("REQUIRES_REVIEW" in r for r in per_source), per_source

    def test_the_persisted_plan_keeps_the_per_source_reasons(self, database, orchestrator) -> None:
        """A plan read back must still explain itself. Reasons that live only in
        memory are reasons nobody can audit after the process exits."""
        session = _new_session(database)
        orchestrator.plan_session(WORKSPACE_ORCH_P, session.id, CORRELATION)
        with database.tenant_transaction(WORKSPACE_ORCH_P) as conn:
            row = conn.execute(
                """SELECT blocked_reasons FROM research.research_plans
                    WHERE research_session_id = %s""",
                (session.id,),
            ).fetchone()
        assert row is not None
        states = row[0]["ACQUISITION"]["source_states"]
        assert {s["source_id"] for s in states} >= {"tiktok", "reddit"}
        assert all(s["eligible"] is False for s in states)
        assert all(s["blocking_reasons"] for s in states)

    def test_the_scoring_block_names_d03(self, database, orchestrator) -> None:
        session = _new_session(database)
        orchestrator.plan_session(WORKSPACE_ORCH_P, session.id, CORRELATION)
        rows = orchestrator.jobs.list_for_session(WORKSPACE_ORCH_P, session.id)
        scoring = next(r for r in rows if r.job_type == "score.opportunity")
        assert scoring.status is JobStatus.BLOCKED
        assert scoring.blocked_reason is not None
        assert scoring.blocked_reason.startswith("PROFILE-NOT-CALIBRATED")

    def test_the_database_refuses_a_blocked_job_with_no_reason(self, database) -> None:
        session = _new_session(database)
        with pytest.raises(Exception) as exc, database.tenant_transaction(WORKSPACE_ORCH_P) as conn:
            conn.execute(
                """INSERT INTO research.research_jobs
                       (id, workspace_id, research_session_id, job_type, queue,
                        correlation_id, idempotency_key, status)
                   VALUES (%s,%s,%s,'maintenance.probe','maintenance','c',%s,'BLOCKED')""",
                (uuid.uuid4(), WORKSPACE_ORCH_P, session.id, uuid.uuid4().hex),
            )
        assert "check constraint" in str(exc.value).lower()


# ============================================================ dispatch and DAG


@needs_postgres
class TestDispatchOrdering:
    def test_only_dependency_free_jobs_are_dispatched_first(self, database) -> None:
        dispatcher = RecordingDispatcher()
        orchestrator = ResearchOrchestrator(database, dispatcher=dispatcher)
        session = _new_session(database)

        first = _probe_job(session)
        second = _probe_job(session, payload={"step": 2}, dependencies=(first.job_id,))
        _save_jobs(orchestrator, session, [first, second])

        report = orchestrator.advance(WORKSPACE_ORCH_P, session.id)
        assert report.dispatched == (first.job_id,)

    def test_a_dependent_becomes_dispatchable_once_its_dependency_succeeds(
        self, database, orchestrator
    ) -> None:
        session = _new_session(database)
        first = _probe_job(session)
        second = _probe_job(session, payload={"step": 2}, dependencies=(first.job_id,))
        _save_jobs(orchestrator, session, [first, second])

        orchestrator.advance(WORKSPACE_ORCH_P, session.id)
        orchestrator.report_started(WORKSPACE_ORCH_P, first.job_id)
        orchestrator.report_success(WORKSPACE_ORCH_P, first.job_id, actual_cost_units=1.0)

        report = orchestrator.advance(WORKSPACE_ORCH_P, session.id)
        assert report.dispatched == (second.job_id,)

    def test_a_dependent_of_failed_work_is_reported_unreachable(
        self, database, orchestrator
    ) -> None:
        session = _new_session(database)
        first = _probe_job(session)
        second = _probe_job(session, payload={"step": 2}, dependencies=(first.job_id,))
        _save_jobs(orchestrator, session, [first, second])

        orchestrator.advance(WORKSPACE_ORCH_P, session.id)
        orchestrator.report_failure(
            WORKSPACE_ORCH_P, first.job_id, "deterministic parse error", retryable=False
        )

        report = orchestrator.advance(WORKSPACE_ORCH_P, session.id)
        assert report.dispatched == ()
        assert second.job_id in report.unreachable

    def test_correlation_reaches_the_dispatcher_intact(self, database) -> None:
        dispatcher = RecordingDispatcher()
        orchestrator = ResearchOrchestrator(database, dispatcher=dispatcher)
        session = _new_session(database)
        _save_jobs(orchestrator, session, [_probe_job(session)])

        orchestrator.advance(WORKSPACE_ORCH_P, session.id)

        _job_id, headers = dispatcher.dispatched[0]
        assert headers == {
            "workspace_id": str(WORKSPACE_ORCH_P),
            "research_session_id": str(session.id),
            "correlation_id": CORRELATION,
        }


# ================================================================ duplicates


@needs_postgres
class TestDuplicateDelivery:
    def test_the_same_work_saved_twice_is_one_ledger_row(self, database, orchestrator) -> None:
        """ADR-004 delivery is at-least-once. The unique constraint on
        (workspace_id, idempotency_key) is what absorbs the duplicate."""
        session = _new_session(database)
        job = _probe_job(session)
        _save_jobs(orchestrator, session, [job])
        _save_jobs(orchestrator, session, [job])

        rows = orchestrator.jobs.list_for_session(WORKSPACE_ORCH_P, session.id)
        assert len(rows) == 1

    def test_the_same_key_in_another_workspace_is_a_different_row(self, database) -> None:
        """Tenant separation of the key: two workspaces doing identical work
        must not collide on each other's constraint."""
        orchestrator = ResearchOrchestrator(database)
        session_a = _new_session(database, WORKSPACE_ORCH_P)
        session_b = _new_session(database, WORKSPACE_ORCH_Q)

        _save_jobs(orchestrator, session_a, [_probe_job(session_a)])
        _save_jobs(orchestrator, session_b, [_probe_job(session_b)])

        assert len(orchestrator.jobs.list_for_session(WORKSPACE_ORCH_P, session_a.id)) == 1
        assert len(orchestrator.jobs.list_for_session(WORKSPACE_ORCH_Q, session_b.id)) == 1

    def test_a_direct_duplicate_insert_is_refused_by_the_constraint(
        self, database, orchestrator
    ) -> None:
        session = _new_session(database)
        job = _probe_job(session)
        _save_jobs(orchestrator, session, [job])

        with pytest.raises(Exception) as exc, database.tenant_transaction(WORKSPACE_ORCH_P) as conn:
            conn.execute(
                """INSERT INTO research.research_jobs
                       (id, workspace_id, research_session_id, job_type, queue,
                        correlation_id, idempotency_key, status)
                   VALUES (%s,%s,%s,'maintenance.probe','maintenance','c',%s,'PENDING')""",
                (uuid.uuid4(), WORKSPACE_ORCH_P, session.id, job.idempotency_key()),
            )
        assert "unique" in str(exc.value).lower() or "duplicate" in str(exc.value).lower()


# ============================================================ failure handling


@needs_postgres
class TestFailureHandling:
    def test_a_retryable_failure_returns_the_job_to_the_pool(self, database, orchestrator) -> None:
        session = _new_session(database)
        job = _probe_job(session, max_attempts=3)
        _save_jobs(orchestrator, session, [job])
        orchestrator.advance(WORKSPACE_ORCH_P, session.id)

        row = orchestrator.report_failure(
            WORKSPACE_ORCH_P, job.job_id, "connection reset", retryable=True
        )
        assert row.status is JobStatus.READY
        assert row.last_error == "connection reset"
        assert row.attempts == 1

    def test_a_permanent_failure_ends_the_job(self, database, orchestrator) -> None:
        session = _new_session(database)
        job = _probe_job(session, max_attempts=3)
        _save_jobs(orchestrator, session, [job])
        orchestrator.advance(WORKSPACE_ORCH_P, session.id)

        row = orchestrator.report_failure(
            WORKSPACE_ORCH_P, job.job_id, "invalid request", retryable=False
        )
        assert row.status is JobStatus.FAILED

    def test_a_retryable_failure_out_of_attempts_ends_the_job(self, database, orchestrator) -> None:
        """Retrying past the budget of attempts is how a poison message blocks a
        queue forever (ADR-004 §Dead-letter)."""
        session = _new_session(database)
        job = _probe_job(session, max_attempts=1)
        _save_jobs(orchestrator, session, [job])
        orchestrator.advance(WORKSPACE_ORCH_P, session.id)

        row = orchestrator.report_failure(WORKSPACE_ORCH_P, job.job_id, "timeout", retryable=True)
        assert row.status is JobStatus.FAILED

    def test_a_failed_job_does_not_fail_the_session(self, database, orchestrator) -> None:
        """ADR-004: a permanently failed job becomes a research gap and lowers
        Research Completeness. It does not fail the run."""
        session = _new_session(database)
        job = _probe_job(session)
        _save_jobs(orchestrator, session, [job])
        orchestrator.advance(WORKSPACE_ORCH_P, session.id)
        orchestrator.report_failure(WORKSPACE_ORCH_P, job.job_id, "boom", retryable=False)

        assert orchestrator.sessions.status(WORKSPACE_ORCH_P, session.id) is Status.PENDING


# ================================================================ resumability


@needs_postgres
class TestResumability:
    def test_execution_state_survives_a_new_orchestrator_instance(self, database) -> None:
        """The restart test. Nothing is carried in memory: a second instance
        reads the same ledger and continues."""
        session = _new_session(database)
        first = ResearchOrchestrator(database, dispatcher=RecordingDispatcher())
        job = _probe_job(session, max_attempts=3)
        _save_jobs(first, session, [job])
        first.advance(WORKSPACE_ORCH_P, session.id)

        # The process dies here. Nothing was flushed, nothing was checkpointed.
        del first

        second = ResearchOrchestrator(database, dispatcher=RecordingDispatcher())
        rows = second.jobs.list_for_session(WORKSPACE_ORCH_P, session.id)
        assert [r.status for r in rows] == [JobStatus.DISPATCHED]

    def test_resume_reclaims_work_no_worker_reported_on(self, database) -> None:
        session = _new_session(database)
        dispatcher = RecordingDispatcher()
        orchestrator = ResearchOrchestrator(database, dispatcher=dispatcher)
        job = _probe_job(session, max_attempts=3)
        _save_jobs(orchestrator, session, [job])
        orchestrator.advance(WORKSPACE_ORCH_P, session.id)

        resumed = ResearchOrchestrator(database, dispatcher=dispatcher)
        report = resumed.resume(WORKSPACE_ORCH_P, session.id)

        assert job.job_id in report.dispatched
        row = resumed.jobs.get(WORKSPACE_ORCH_P, job.job_id)
        assert row.attempts == 2

    def test_resume_does_not_reclaim_work_that_is_out_of_attempts(self, database) -> None:
        """Otherwise a crash loop re-dispatches the same poison message forever."""
        session = _new_session(database)
        orchestrator = ResearchOrchestrator(database)
        job = _probe_job(session, max_attempts=1)
        _save_jobs(orchestrator, session, [job])
        orchestrator.advance(WORKSPACE_ORCH_P, session.id)

        report = ResearchOrchestrator(database).resume(WORKSPACE_ORCH_P, session.id)
        assert report.dispatched == ()

    def test_redis_is_not_the_source_of_progress_truth(self, database, orchestrator) -> None:
        """§13. Every field the scheduler needs is readable from PostgreSQL
        alone, with no broker involved."""
        session = _new_session(database)
        job = _probe_job(session)
        _save_jobs(orchestrator, session, [job])
        orchestrator.advance(WORKSPACE_ORCH_P, session.id)

        with database.tenant_transaction(WORKSPACE_ORCH_P) as conn:
            row = conn.execute(
                """SELECT status, attempts, dispatched_at, correlation_id, idempotency_key
                   FROM research.research_jobs WHERE workspace_id = %s AND id = %s""",
                (WORKSPACE_ORCH_P, job.job_id),
            ).fetchone()
        assert row is not None
        assert row[0] == "DISPATCHED"
        assert row[1] == 1
        assert row[2] is not None
        assert row[3] == CORRELATION
        assert row[4] == job.idempotency_key()


# ===================================================================== budget


@needs_postgres
class TestBudgetEnforcement:
    def test_a_job_beyond_the_ceiling_is_not_dispatched(self, database) -> None:
        dispatcher = RecordingDispatcher()
        orchestrator = ResearchOrchestrator(database, dispatcher=dispatcher)
        session = _new_session(
            database, context=_context(budget_constraints={"max_cost_units": 5.0})
        )
        job = _probe_job(session, estimated_cost_units=50.0)
        _save_jobs(orchestrator, session, [job])

        report = orchestrator.advance(WORKSPACE_ORCH_P, session.id)

        assert report.dispatched == ()
        assert dispatcher.dispatched == []
        assert len(report.refused_for_budget) == 1
        assert "exceeds the remaining" in report.refused_for_budget[0][1]

    def test_a_refusal_does_not_create_a_new_session_status(self, database, orchestrator) -> None:
        """There is no BUDGET_EXHAUSTED. Ontology V2 §15."""
        session = _new_session(
            database, context=_context(budget_constraints={"max_cost_units": 1.0})
        )
        _save_jobs(orchestrator, session, [_probe_job(session, estimated_cost_units=99.0)])
        orchestrator.advance(WORKSPACE_ORCH_P, session.id)
        assert orchestrator.sessions.status(WORKSPACE_ORCH_P, session.id) is Status.PENDING

    def test_a_reservation_is_recorded_before_dispatch(self, database, orchestrator) -> None:
        session = _new_session(
            database, context=_context(budget_constraints={"max_cost_units": 100.0})
        )
        _save_jobs(orchestrator, session, [_probe_job(session, estimated_cost_units=10.0)])
        orchestrator.advance(WORKSPACE_ORCH_P, session.id)

        entries = orchestrator.budgets.entries_for_session(WORKSPACE_ORCH_P, session.id)
        assert [e["entry_kind"] for e in entries] == [BudgetEntryKind.RESERVATION.value]
        assert entries[0]["cost_units"] == 10.0
        assert entries[0]["currency"] == "COST_UNIT"

    def test_reservations_accumulate_so_a_second_job_can_be_refused(
        self, database, orchestrator
    ) -> None:
        """The concurrency case: two jobs that each fit against `actual` but not
        against `committed`."""
        session = _new_session(
            database, context=_context(budget_constraints={"max_cost_units": 15.0})
        )
        first = _probe_job(session, estimated_cost_units=10.0)
        second = _probe_job(session, payload={"n": 2}, estimated_cost_units=10.0)
        _save_jobs(orchestrator, session, [first, second])

        report = orchestrator.advance(WORKSPACE_ORCH_P, session.id)

        # WHICH of the two goes first is ledger ordering and is not the point.
        # What the guard must guarantee is that the second one does not also
        # fit: against `actual` alone both would, and together they would
        # overshoot a 15-unit ceiling by 5.
        assert len(report.dispatched) == 1
        assert len(report.refused_for_budget) == 1
        dispatched_id = report.dispatched[0]
        refused_id = report.refused_for_budget[0][0]
        assert {dispatched_id, refused_id} == {first.job_id, second.job_id}
        assert "exceeds the remaining" in report.refused_for_budget[0][1]

    def test_success_converts_a_reservation_into_an_actual(self, database, orchestrator) -> None:
        session = _new_session(
            database, context=_context(budget_constraints={"max_cost_units": 100.0})
        )
        job = _probe_job(session, estimated_cost_units=10.0)
        _save_jobs(orchestrator, session, [job])
        orchestrator.advance(WORKSPACE_ORCH_P, session.id)
        orchestrator.report_started(WORKSPACE_ORCH_P, job.job_id)
        orchestrator.report_success(
            WORKSPACE_ORCH_P, job.job_id, actual_cost_units=7.5, provider="fake", tier="FAST_MODEL"
        )

        account = orchestrator.budgets.account_for_session(WORKSPACE_ORCH_P, session.id)
        assert account.reserved_cost_units == 0.0
        assert account.actual_cost_units == 7.5
        assert account.remaining_cost_units == 92.5

    def test_a_failure_releases_the_reservation(self, database, orchestrator) -> None:
        """Work that did not happen must not keep holding budget other work
        could use."""
        session = _new_session(
            database, context=_context(budget_constraints={"max_cost_units": 100.0})
        )
        job = _probe_job(session, estimated_cost_units=10.0)
        _save_jobs(orchestrator, session, [job])
        orchestrator.advance(WORKSPACE_ORCH_P, session.id)
        orchestrator.report_failure(WORKSPACE_ORCH_P, job.job_id, "boom", retryable=False)

        account = orchestrator.budgets.account_for_session(WORKSPACE_ORCH_P, session.id)
        assert account.committed_cost_units == 0.0

    def test_the_spend_record_carries_its_reproducibility_metadata(
        self, database, orchestrator
    ) -> None:
        session = _new_session(
            database, context=_context(budget_constraints={"max_cost_units": 100.0})
        )
        job = _probe_job(session, estimated_cost_units=1.0)
        _save_jobs(orchestrator, session, [job])
        orchestrator.advance(WORKSPACE_ORCH_P, session.id)
        orchestrator.report_success(
            WORKSPACE_ORCH_P,
            job.job_id,
            actual_cost_units=2.0,
            provider="anthropic",
            model="a-model",
            tier="STRONG_MODEL",
            pricing_version="2026.08",
        )

        actuals = [
            e
            for e in orchestrator.budgets.entries_for_session(WORKSPACE_ORCH_P, session.id)
            if e["entry_kind"] == BudgetEntryKind.ACTUAL.value
        ]
        assert actuals[0]["provider"] == "anthropic"
        assert actuals[0]["model"] == "a-model"
        assert actuals[0]["tier"] == "STRONG_MODEL"
        assert actuals[0]["pricing_version"] == "2026.08"

    def test_the_database_refuses_an_unknown_tier(self, database, orchestrator) -> None:
        session = _new_session(database)
        with pytest.raises(Exception) as exc, database.tenant_transaction(WORKSPACE_ORCH_P) as conn:
            conn.execute(
                """INSERT INTO research.session_budget_entries
                       (id, workspace_id, research_session_id, entry_kind, cost_units, tier)
                   VALUES (%s,%s,%s,'ACTUAL',1.0,'GENIUS_MODEL')""",
                (uuid.uuid4(), WORKSPACE_ORCH_P, session.id),
            )
        assert "check constraint" in str(exc.value).lower()


# =============================================================== cancellation


@needs_postgres
class TestCancellation:
    def test_cancelling_stops_future_dispatch(self, database) -> None:
        dispatcher = RecordingDispatcher()
        orchestrator = ResearchOrchestrator(database, dispatcher=dispatcher)
        session = _new_session(database)
        _save_jobs(orchestrator, session, [_probe_job(session)])

        orchestrator.cancel(WORKSPACE_ORCH_P, session.id)
        report = orchestrator.advance(WORKSPACE_ORCH_P, session.id)

        assert report.dispatched == ()
        assert dispatcher.dispatched == []

    def test_cancelling_moves_the_session_to_the_canonical_state(
        self, database, orchestrator
    ) -> None:
        session = _new_session(database)
        orchestrator.cancel(WORKSPACE_ORCH_P, session.id)
        assert orchestrator.sessions.status(WORKSPACE_ORCH_P, session.id) is Status.CANCELLED

    def test_in_flight_work_is_reported_rather_than_claimed_stopped(
        self, database, orchestrator
    ) -> None:
        """§14. Celery revocation is advisory and a process mid-call does not
        observe it. Claiming instant distributed cancellation would tell callers
        a resource was freed when it was not."""
        session = _new_session(database)
        job = _probe_job(session)
        _save_jobs(orchestrator, session, [job])
        orchestrator.advance(WORKSPACE_ORCH_P, session.id)

        report = orchestrator.cancel(WORKSPACE_ORCH_P, session.id)

        assert job.job_id in report.unreachable
        assert orchestrator.jobs.get(WORKSPACE_ORCH_P, job.job_id).status is JobStatus.DISPATCHED

    def test_cancelling_a_terminal_session_is_a_no_op(self, database, orchestrator) -> None:
        session = _new_session(database)
        orchestrator.cancel(WORKSPACE_ORCH_P, session.id)
        orchestrator.cancel(WORKSPACE_ORCH_P, session.id)
        assert orchestrator.sessions.status(WORKSPACE_ORCH_P, session.id) is Status.CANCELLED


# ================================================================ completeness


@needs_postgres
class TestCompletenessRecording:
    def test_a_fully_blocked_session_records_unknown_with_reasons(
        self, database, orchestrator
    ) -> None:
        session = _new_session(database)
        plan = orchestrator.plan_session(WORKSPACE_ORCH_P, session.id, CORRELATION)
        orchestrator.advance(WORKSPACE_ORCH_P, session.id)

        record = orchestrator.finalize(WORKSPACE_ORCH_P, session.id, plan)

        assert record.basis is CompletenessBasis.UNKNOWN
        assert record.value is None
        assert set(record.blocked_capabilities) == {c.value for c in Capability}
        # Acquisition names one of its two gates. Which one depends on whether
        # any condition verification has been recorded against this database, so
        # asserting a specific id here would make the test a statement about a
        # deployment rather than about the recorded reasons.
        assert any(
            "SOURCE-REGISTRY-GATE" in reason or "NO-COLLECTOR-IMPLEMENTED" in reason
            for reason in record.incompleteness_reasons
        )
        assert any("PROFILE-NOT-CALIBRATED" in reason for reason in record.incompleteness_reasons)

    def test_the_record_is_persisted_and_readable(self, database, orchestrator) -> None:
        session = _new_session(database)
        plan = orchestrator.plan_session(WORKSPACE_ORCH_P, session.id, CORRELATION)
        orchestrator.advance(WORKSPACE_ORCH_P, session.id)
        orchestrator.finalize(WORKSPACE_ORCH_P, session.id, plan)

        stored = orchestrator.completeness.latest_for_session(WORKSPACE_ORCH_P, session.id)
        assert stored is not None
        assert stored.basis is CompletenessBasis.UNKNOWN
        assert stored.incompleteness_reasons

    def test_the_database_refuses_a_measured_basis_with_no_measurement(
        self, database, orchestrator
    ) -> None:
        session = _new_session(database)
        with pytest.raises(Exception) as exc, database.tenant_transaction(WORKSPACE_ORCH_P) as conn:
            conn.execute(
                """INSERT INTO research.research_completeness_records
                       (id, workspace_id, research_session_id, basis)
                   VALUES (%s,%s,%s,'MEASURED')""",
                (uuid.uuid4(), WORKSPACE_ORCH_P, session.id),
            )
        assert "check constraint" in str(exc.value).lower()

    def test_the_database_refuses_an_out_of_range_completeness_score(
        self, database, orchestrator
    ) -> None:
        session = _new_session(database)
        with pytest.raises(Exception) as exc, database.tenant_transaction(WORKSPACE_ORCH_P) as conn:
            conn.execute(
                """INSERT INTO research.research_completeness_records
                       (id, workspace_id, research_session_id, basis, measured_score)
                   VALUES (%s,%s,%s,'MEASURED',101)""",
                (uuid.uuid4(), WORKSPACE_ORCH_P, session.id),
            )
        assert "check constraint" in str(exc.value).lower()


# ============================================================ tenant isolation


@needs_postgres
class TestOrchestrationIsTenantScoped:
    def test_one_workspace_cannot_read_another_workspaces_ledger(self, database) -> None:
        orchestrator = ResearchOrchestrator(database)
        session = _new_session(database, WORKSPACE_ORCH_P)
        _save_jobs(orchestrator, session, [_probe_job(session)])

        assert orchestrator.jobs.list_for_session(WORKSPACE_ORCH_Q, session.id) == []

    def test_a_job_cannot_be_transitioned_from_another_workspace(self, database) -> None:
        orchestrator = ResearchOrchestrator(database)
        session = _new_session(database, WORKSPACE_ORCH_P)
        job = _probe_job(session)
        _save_jobs(orchestrator, session, [job])

        with pytest.raises(OrchestratorNotFoundError):
            orchestrator.jobs.transition(WORKSPACE_ORCH_Q, job.job_id, JobStatus.READY)

    def test_a_missing_workspace_is_refused(self, database) -> None:
        orchestrator = ResearchOrchestrator(database)
        session = _new_session(database, WORKSPACE_ORCH_P)
        with pytest.raises(ValueError):
            orchestrator.jobs.list_for_session("", session.id)
