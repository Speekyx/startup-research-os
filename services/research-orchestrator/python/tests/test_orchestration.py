"""Orchestration rules, tested without a database.

Mission 0.4 §36. Everything here is pure: lifecycle, job states, dependency
ordering, planning, budget and completeness. It runs under stdlib `unittest`
with nothing installed, for the reason ADR-009 gives — a check that cannot run
is a check that gets skipped.

The database-backed half (persistence, resumption, duplicate delivery,
correlation across a real transaction) lives in
`services/gateway/python/tests/test_orchestrator_integration.py`, where the
stack fixtures already are.
"""

from __future__ import annotations

import unittest
import uuid

from sros_contracts import MarketScope, ResearchContext, ResearchSessionStatus
from sros_contracts.research_context import BudgetConstraints
from sros_orchestrator import (
    ALLOWED_TRANSITIONS,
    BLOCKED_CAPABILITIES,
    BudgetAccount,
    BudgetGuard,
    BudgetRefusedError,
    Capability,
    CompletenessBasis,
    CompletenessRecord,
    DependencyCycleError,
    InvalidJobTransitionError,
    InvalidTransitionError,
    JobSpec,
    JobStatus,
    ResearchPlanner,
    SourceAvailability,
    StaticSourceAvailability,
    UnconsultedRegistry,
    UnknownDependencyError,
    acquisition_block,
    blocked_by_dependencies,
    can_transition,
    cancellation_target,
    dependency_closure,
    deterministic_job_id,
    is_terminal,
    ready_job_ids,
    require_job_transition,
    require_transition,
    topological_order,
)

WORKSPACE = "00000000-0000-4000-8000-000000000001"
SESSION = "00000000-0000-4000-8000-0000000000aa"
CORRELATION = "corr-0001"


def _context(**overrides: object) -> ResearchContext:
    payload: dict[str, object] = {
        "market_scope": {"type": "COUNTRY", "countries": ["FR"]},
        "domains": ["developer tools"],
    }
    payload.update(overrides)
    return ResearchContext.from_json(payload)


def _job(name: str, deps: tuple[uuid.UUID, ...] = (), **kwargs: object) -> JobSpec:
    return JobSpec(
        job_type=kwargs.pop("job_type", "maintenance.probe") or "maintenance.probe",  # type: ignore[arg-type]
        workspace_id=WORKSPACE,
        research_session_id=SESSION,
        correlation_id=CORRELATION,
        job_id=uuid.uuid5(uuid.NAMESPACE_OID, name),
        dependencies=deps,
        **kwargs,  # type: ignore[arg-type]
    )


# ============================================================ session lifecycle


class TestSessionLifecycle(unittest.TestCase):
    def test_the_canonical_happy_path_is_permitted_end_to_end(self) -> None:
        sequence = [
            ResearchSessionStatus.PENDING,
            ResearchSessionStatus.PLANNING,
            ResearchSessionStatus.COLLECTING,
            ResearchSessionStatus.ANALYZING,
            ResearchSessionStatus.SCORING,
            ResearchSessionStatus.COMPLETED,
        ]
        for current, target in zip(sequence, sequence[1:], strict=False):
            require_transition(current, target)

    def test_skipping_a_stage_is_refused(self) -> None:
        with self.assertRaises(InvalidTransitionError):
            require_transition(ResearchSessionStatus.PENDING, ResearchSessionStatus.COLLECTING)

    def test_going_backwards_is_refused(self) -> None:
        with self.assertRaises(InvalidTransitionError):
            require_transition(ResearchSessionStatus.SCORING, ResearchSessionStatus.COLLECTING)

    def test_terminal_states_are_terminal(self) -> None:
        for terminal in (
            ResearchSessionStatus.COMPLETED,
            ResearchSessionStatus.FAILED,
            ResearchSessionStatus.CANCELLED,
        ):
            self.assertTrue(is_terminal(terminal))
            self.assertEqual(ALLOWED_TRANSITIONS[terminal], frozenset())
            for target in ResearchSessionStatus:
                self.assertFalse(can_transition(terminal, target))

    def test_scoring_reaches_completed_because_partial_coverage_is_a_result(self) -> None:
        """Ontology V2 §15: budget exhaustion is COMPLETED with reduced Research
        Completeness, never FAILED."""
        self.assertTrue(
            can_transition(ResearchSessionStatus.SCORING, ResearchSessionStatus.COMPLETED)
        )

    def test_no_lifecycle_state_is_invented(self) -> None:
        """Every state in the table is a contract enum value, and every contract
        value appears in the table. A state added on one side only is how an
        invented status enters the system."""
        self.assertEqual(set(ALLOWED_TRANSITIONS), set(ResearchSessionStatus))
        for targets in ALLOWED_TRANSITIONS.values():
            for target in targets:
                self.assertIsInstance(target, ResearchSessionStatus)

    def test_there_is_no_budget_exhausted_status(self) -> None:
        self.assertNotIn("BUDGET_EXHAUSTED", {s.value for s in ResearchSessionStatus})

    def test_cancellation_target_is_none_once_terminal(self) -> None:
        self.assertEqual(
            cancellation_target(ResearchSessionStatus.COLLECTING),
            ResearchSessionStatus.CANCELLED,
        )
        self.assertIsNone(cancellation_target(ResearchSessionStatus.COMPLETED))
        self.assertIsNone(cancellation_target(ResearchSessionStatus.CANCELLED))


# =================================================================== job states


class TestJobStates(unittest.TestCase):
    def test_a_dispatched_job_can_return_to_ready_for_a_retry(self) -> None:
        require_job_transition(JobStatus.DISPATCHED, JobStatus.READY)
        require_job_transition(JobStatus.RUNNING, JobStatus.READY)

    def test_a_succeeded_job_is_terminal(self) -> None:
        with self.assertRaises(InvalidJobTransitionError):
            require_job_transition(JobStatus.SUCCEEDED, JobStatus.READY)

    def test_a_blocked_job_can_never_become_ready(self) -> None:
        """The mechanical guard behind §32 and §33: blocked work cannot be
        dispatched by any code path, not merely by convention."""
        for target in JobStatus:
            with self.assertRaises(InvalidJobTransitionError):
                require_job_transition(JobStatus.BLOCKED, target)

    def test_a_blocked_spec_requires_a_reason(self) -> None:
        with self.assertRaises(ValueError):
            JobSpec(
                job_type="maintenance.probe",
                workspace_id=WORKSPACE,
                research_session_id=SESSION,
                correlation_id=CORRELATION,
                status=JobStatus.BLOCKED,
            )

    def test_a_job_requires_a_workspace(self) -> None:
        with self.assertRaises(ValueError):
            JobSpec(
                job_type="maintenance.probe",
                workspace_id="",
                research_session_id=SESSION,
                correlation_id=CORRELATION,
            )

    def test_the_queue_is_resolved_from_the_worker_routing_table(self) -> None:
        self.assertEqual(_job("a", job_type="acquire.collect").queue, "acquisition")
        self.assertEqual(_job("b", job_type="nlp.extract.signals").queue, "nlp")
        # Longest prefix wins: nlp.embed must not be swallowed by `nlp.`.
        self.assertEqual(_job("c", job_type="nlp.embed.batch").queue, "embedding")
        self.assertEqual(_job("d", job_type="score.opportunity").queue, "analysis")

    def test_an_unroutable_job_type_is_refused_at_construction(self) -> None:
        with self.assertRaises(KeyError):
            _job("e", job_type="totally.unknown")

    def test_correlation_travels_in_the_task_headers(self) -> None:
        headers = _job("f").task_headers()
        self.assertEqual(set(headers), {"workspace_id", "research_session_id", "correlation_id"})
        self.assertEqual(headers["correlation_id"], CORRELATION)
        self.assertEqual(headers["workspace_id"], WORKSPACE)


class TestIdempotency(unittest.TestCase):
    def test_the_same_work_produces_the_same_key(self) -> None:
        first = _job("g", payload={"a": 1, "b": 2})
        second = _job("g", payload={"b": 2, "a": 1})
        self.assertEqual(first.idempotency_key(), second.idempotency_key())

    def test_a_different_workspace_produces_a_different_key(self) -> None:
        other = JobSpec(
            job_type="maintenance.probe",
            workspace_id="00000000-0000-4000-8000-000000000003",
            research_session_id=SESSION,
            correlation_id=CORRELATION,
        )
        self.assertNotEqual(_job("h").idempotency_key(), other.idempotency_key())

    def test_the_correlation_id_does_not_enter_the_key(self) -> None:
        """The same work requested twice under two correlation ids is still the
        same work. Including it would defeat the constraint it exists to trip."""
        a = JobSpec(
            job_type="maintenance.probe",
            workspace_id=WORKSPACE,
            research_session_id=SESSION,
            correlation_id="corr-one",
        )
        b = JobSpec(
            job_type="maintenance.probe",
            workspace_id=WORKSPACE,
            research_session_id=SESSION,
            correlation_id="corr-two",
        )
        self.assertEqual(a.idempotency_key(), b.idempotency_key())

    def test_the_job_id_is_a_function_of_the_key(self) -> None:
        key = _job("i").idempotency_key()
        self.assertEqual(deterministic_job_id(key), deterministic_job_id(key))
        self.assertNotEqual(deterministic_job_id(key), deterministic_job_id(key + "x"))


# ============================================================= dependency graph


class TestDependencyOrdering(unittest.TestCase):
    def test_a_chain_is_ordered_by_its_dependencies(self) -> None:
        a = _job("chain-a")
        b = _job("chain-b", (a.job_id,))
        c = _job("chain-c", (b.job_id,))
        order = [job.job_id for job in topological_order([c, a, b])]
        self.assertEqual(order, [a.job_id, b.job_id, c.job_id])

    def test_ordering_is_deterministic_across_input_orders(self) -> None:
        a = _job("det-a")
        b = _job("det-b", (a.job_id,))
        c = _job("det-c", (a.job_id,))
        first = [j.job_id for j in topological_order([a, b, c])]
        second = [j.job_id for j in topological_order([c, b, a])]
        self.assertEqual(first, second)

    def test_a_cycle_is_detected_at_planning_time(self) -> None:
        left = uuid.uuid4()
        right = uuid.uuid4()
        a = JobSpec(
            job_type="maintenance.probe",
            workspace_id=WORKSPACE,
            research_session_id=SESSION,
            correlation_id=CORRELATION,
            job_id=left,
            dependencies=(right,),
        )
        b = JobSpec(
            job_type="maintenance.probe",
            workspace_id=WORKSPACE,
            research_session_id=SESSION,
            correlation_id=CORRELATION,
            job_id=right,
            dependencies=(left,),
        )
        with self.assertRaises(DependencyCycleError):
            topological_order([a, b])

    def test_a_dependency_outside_the_graph_is_refused(self) -> None:
        a = _job("orphan", (uuid.uuid4(),))
        with self.assertRaises(UnknownDependencyError):
            topological_order([a])

    def test_only_jobs_with_satisfied_dependencies_are_ready(self) -> None:
        a = _job("ready-a")
        b = _job("ready-b", (a.job_id,))
        self.assertEqual(ready_job_ids([a, b], {}), [a.job_id])
        self.assertEqual(ready_job_ids([a, b], {a.job_id: JobStatus.SUCCEEDED}), [b.job_id])

    def test_a_failed_dependency_does_not_make_a_dependent_ready(self) -> None:
        a = _job("fail-a")
        b = _job("fail-b", (a.job_id,))
        self.assertEqual(ready_job_ids([a, b], {a.job_id: JobStatus.FAILED}), [])

    def test_a_dependent_of_failed_work_is_reported_as_unreachable(self) -> None:
        """Not ready and not failed: it is a gap with a named cause. Reporting
        it is what turns a stalled plan into a gap report instead of a queue
        that quietly stops moving."""
        a = _job("dead-a")
        b = _job("dead-b", (a.job_id,))
        dead_ends = blocked_by_dependencies([a, b], {a.job_id: JobStatus.BLOCKED})
        self.assertEqual(dead_ends, {b.job_id: [a.job_id]})

    def test_the_transitive_closure_of_a_dependency_is_reported(self) -> None:
        a = _job("clo-a")
        b = _job("clo-b", (a.job_id,))
        c = _job("clo-c", (b.job_id,))
        self.assertEqual(dependency_closure([a, b, c], c.job_id), {a.job_id, b.job_id})


# ====================================================================== planning


class TestPlanning(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = ResearchPlanner().plan(WORKSPACE, SESSION, CORRELATION, _context())

    def test_every_domain_capability_is_currently_blocked(self) -> None:
        self.assertEqual(set(self.plan.blocked_capability_names), {c.value for c in Capability})
        self.assertEqual(self.plan.dispatchable_jobs, ())

    def test_acquisition_is_not_in_the_static_register(self) -> None:
        """Mission 1.0 §22. D-07 is resolved, so a hardcoded acquisition block
        would be a stale reason nobody would notice going false. Its block is
        derived from the registry per plan."""
        self.assertNotIn(Capability.ACQUISITION, BLOCKED_CAPABILITIES)

    def test_an_unconsulted_registry_blocks_acquisition(self) -> None:
        """Fail closed. A planner wired to no registry must refuse, not permit:
        Mission 1.0 §31 forbids converting an unknown into a permission."""
        block = acquisition_block(UnconsultedRegistry().source_availability())
        assert block is not None
        self.assertEqual(block.decision_id, "SOURCE-REGISTRY-GATE")
        self.assertIn("not consulted", block.reason)
        self.assertEqual(block.source_states, ())

    def test_a_registry_with_no_eligible_source_blocks_and_names_each_one(self) -> None:
        report = StaticSourceAvailability(
            (
                SourceAvailability("reddit", "REQUIRES_REVIEW", False, ("no evidence",)),
                SourceAvailability("tiktok", "PROHIBITED", False, ("policy review is PROHIBITED",)),
            )
        ).source_availability()
        block = acquisition_block(report)
        assert block is not None
        self.assertIn("0 collector-eligible", block.reason)
        self.assertEqual({s.source_id for s in block.source_states}, {"reddit", "tiktok"})
        # The per-source reason survives into the persisted plan payload, which
        # is the whole point: a stored plan must still explain itself later.
        self.assertIn("source_states", block.to_json())

    def test_one_eligible_source_lifts_the_acquisition_block(self) -> None:
        """The unblocked branch must be reachable, or the gate would be a
        permanent refusal dressed as a check. Eligibility comes from a reviewed
        registry row in production; here it is a test double, never a real
        platform approval."""
        report = StaticSourceAvailability(
            (SourceAvailability("fixture-source", "APPROVED", True),)
        ).source_availability()
        self.assertIsNone(acquisition_block(report))

    def test_an_empty_registry_says_so_rather_than_blaming_review(self) -> None:
        """ "Nothing registered" and "nothing approved" have different remedies."""
        block = acquisition_block(StaticSourceAvailability(()).source_availability())
        assert block is not None
        self.assertIn("empty", block.reason)

    def test_scoring_is_blocked_on_calibration_not_on_the_formula(self) -> None:
        """Mission 1.2. The formula exists since Mission 1.1, so the old reason
        went false. A false blocking reason invites someone to decide the block
        no longer applies; what blocks scoring now is the second gate."""
        blocked = BLOCKED_CAPABILITIES[Capability.SCORING]
        self.assertEqual(blocked.decision_id, "PROFILE-NOT-CALIBRATED")
        self.assertIn("CALIBRATED", blocked.reason)
        self.assertNotIn("undefined", blocked.reason)

    def test_every_blocked_job_carries_the_deciding_reference(self) -> None:
        for job in self.plan.blocked_jobs:
            self.assertIsNotNone(job.blocked_reason)
            self.assertTrue(
                any(
                    job.blocked_reason.startswith(d)
                    for d in (
                        "D-12",
                        "NO-COLLECTOR",
                        "SOURCE-REGISTRY-GATE",
                        "PROFILE-NOT-CALIBRATED",
                    )
                ),
                job.blocked_reason,
            )

    def test_a_blocked_plan_costs_nothing(self) -> None:
        """Reserving budget for work that will not run would understate what
        remains for work that will."""
        self.assertEqual(self.plan.estimated_cost_units, 0.0)

    def test_the_plan_graph_is_acyclic_and_ordered(self) -> None:
        order = [job.payload["capability"] for job in self.plan.ordered_jobs()]
        self.assertEqual(
            order,
            [
                Capability.ACQUISITION.value,
                Capability.NORMALIZATION.value,
                Capability.NLP_EXTRACTION.value,
                Capability.OPPORTUNITY_DISCOVERY.value,
                Capability.SCORING.value,
            ],
        )

    def test_planning_the_same_session_twice_produces_the_same_job_ids(self) -> None:
        """Resumability (§13): a replan after a crash must converge on the
        ledger that already exists rather than inserting a parallel copy."""
        again = ResearchPlanner().plan(WORKSPACE, SESSION, "another-correlation", _context())
        self.assertEqual(
            [j.job_id for j in self.plan.ordered_jobs()],
            [j.job_id for j in again.ordered_jobs()],
        )

    def test_a_different_scope_produces_a_different_plan(self) -> None:
        other = ResearchPlanner().plan(
            WORKSPACE, SESSION, CORRELATION, _context(market_scope={"type": "GLOBAL"})
        )
        self.assertNotEqual({j.job_id for j in self.plan.jobs}, {j.job_id for j in other.jobs})

    def test_the_incompleteness_reasons_name_the_open_decisions(self) -> None:
        reasons = " ".join(self.plan.incompleteness_reasons())
        self.assertIn("SOURCE-REGISTRY-GATE", reasons)
        self.assertIn("PROFILE-NOT-CALIBRATED", reasons)
        self.assertIn("D-12", reasons)

    def test_a_plan_records_the_availability_it_was_built_from(self) -> None:
        """A plan read back later must show the sources available THEN, not the
        ones available when someone happens to read it."""
        planner = ResearchPlanner(
            sources=StaticSourceAvailability(
                (SourceAvailability("fixture-source", "APPROVED", True),)
            )
        )
        plan = planner.plan(WORKSPACE, SESSION, CORRELATION, _context())
        self.assertEqual(plan.eligible_source_ids, ("fixture-source",))
        self.assertNotIn(Capability.ACQUISITION.value, plan.blocked_capability_names)

    def test_blocked_source_reasons_are_reported_per_source(self) -> None:
        planner = ResearchPlanner(
            sources=StaticSourceAvailability(
                (
                    SourceAvailability(
                        "tiktok", "PROHIBITED", False, ("policy review is PROHIBITED",)
                    ),
                )
            )
        )
        plan = planner.plan(WORKSPACE, SESSION, CORRELATION, _context())
        self.assertEqual(
            plan.blocked_source_reasons(),
            ("tiktok (PROHIBITED): policy review is PROHIBITED",),
        )
        self.assertEqual(plan.eligible_source_ids, ())

    def test_the_planner_records_the_scope_it_would_have_covered(self) -> None:
        scope = MarketScope.country("FR").key()
        for job in self.plan.jobs:
            self.assertEqual(job.payload["market_scope_key"], scope)

    def test_planning_requires_a_workspace(self) -> None:
        with self.assertRaises(ValueError):
            ResearchPlanner().plan("", SESSION, CORRELATION, _context())


# ======================================================================= budget


class TestBudgetGuard(unittest.TestCase):
    def test_a_job_that_fits_is_allowed(self) -> None:
        guard = BudgetGuard(BudgetAccount(SESSION, 100.0, None))
        self.assertTrue(guard.evaluate(10.0).allowed)

    def test_the_check_uses_committed_not_merely_actual(self) -> None:
        """Two concurrent dispatches both checking `actual` would both fit and
        together overshoot. Reservations are what close that."""
        account = BudgetAccount(SESSION, 100.0, None, reserved_cost_units=95.0)
        self.assertFalse(BudgetGuard(account).evaluate(10.0).allowed)

    def test_the_inequality_is_estimate_plus_committed_against_configured(self) -> None:
        account = BudgetAccount(
            SESSION, 100.0, None, reserved_cost_units=40.0, actual_cost_units=50.0
        )
        guard = BudgetGuard(account)
        self.assertTrue(guard.evaluate(10.0).allowed)
        self.assertFalse(guard.evaluate(10.001).allowed)

    def test_a_refusal_carries_a_reason_fit_for_a_gap_report(self) -> None:
        decision = BudgetGuard(BudgetAccount(SESSION, 5.0, None)).evaluate(10.0)
        self.assertFalse(decision.allowed)
        self.assertIn("exceeds", decision.reason)
        self.assertIn(
            "Research Completeness",
            decision.reason + " ",
        )

    def test_call_count_is_a_separate_ceiling(self) -> None:
        account = BudgetAccount(SESSION, None, 2, llm_calls=2)
        decision = BudgetGuard(account).evaluate(0.0)
        self.assertFalse(decision.allowed)
        self.assertIn("call budget exhausted", decision.reason)

    def test_a_non_llm_job_is_not_stopped_by_the_call_ceiling(self) -> None:
        account = BudgetAccount(SESSION, None, 2, llm_calls=2)
        self.assertTrue(BudgetGuard(account).evaluate(0.0, llm_backed=False).allowed)

    def test_no_ceiling_means_no_cost_refusal(self) -> None:
        self.assertTrue(BudgetGuard(BudgetAccount(SESSION, None, None)).evaluate(1e9).allowed)

    def test_require_raises_only_where_a_caller_asked_to_spend(self) -> None:
        with self.assertRaises(BudgetRefusedError):
            BudgetGuard(BudgetAccount(SESSION, 1.0, None)).require(2.0)

    def test_a_negative_estimate_is_a_programming_error(self) -> None:
        with self.assertRaises(ValueError):
            BudgetGuard(BudgetAccount(SESSION, 1.0, None)).evaluate(-1.0)

    def test_budget_constraints_come_from_the_research_context(self) -> None:
        context = _context(budget_constraints={"max_cost_units": 25.0, "max_llm_calls": 7})
        self.assertIsInstance(context.budget_constraints, BudgetConstraints)
        assert context.budget_constraints is not None
        self.assertEqual(context.budget_constraints.max_cost_units, 25.0)


# =============================================================== completeness


class TestCompleteness(unittest.TestCase):
    def test_a_blocked_session_cannot_report_a_measured_value(self) -> None:
        with self.assertRaises(ValueError):
            CompletenessRecord(
                research_session_id=SESSION,
                basis=CompletenessBasis.MEASURED,
                measured_score=40,
                blocked_capabilities=("SCORING",),
                incompleteness_reasons=("scoring blocked",),
            )

    def test_a_blocked_session_cannot_claim_one_hundred(self) -> None:
        with self.assertRaises(ValueError):
            CompletenessRecord.estimated(
                SESSION, 100, ("scoring blocked",), blocked_capabilities=("SCORING",)
            )

    def test_blocked_capabilities_require_a_stated_reason(self) -> None:
        with self.assertRaises(ValueError):
            CompletenessRecord(
                research_session_id=SESSION,
                basis=CompletenessBasis.UNKNOWN,
                blocked_capabilities=("SCORING",),
            )

    def test_unknown_is_the_honest_record_for_a_fully_blocked_session(self) -> None:
        record = CompletenessRecord.unknown(
            SESSION,
            incompleteness_reasons=("ACQUISITION unavailable (D-07)",),
            blocked_capabilities=("ACQUISITION",),
        )
        self.assertIsNone(record.value)
        self.assertFalse(record.claims_complete)
        self.assertEqual(record.basis, CompletenessBasis.UNKNOWN)

    def test_an_estimate_must_say_why_it_is_not_a_measurement(self) -> None:
        with self.assertRaises(ValueError):
            CompletenessRecord.estimated(SESSION, 60, ())

    def test_a_score_is_an_integer_on_zero_to_one_hundred(self) -> None:
        for bad in (-1, 101):
            with self.assertRaises(ValueError):
                CompletenessRecord.measured(SESSION, bad)
        with self.assertRaises(ValueError):
            CompletenessRecord.measured(SESSION, 82.37)  # type: ignore[arg-type]

    def test_the_basis_is_always_carried_alongside_the_value(self) -> None:
        payload = CompletenessRecord.measured(SESSION, 80).to_json()
        self.assertEqual(payload["basis"], "MEASURED")
        self.assertEqual(payload["measured_score"], 80)
        self.assertIsNone(payload["estimated_score"])


if __name__ == "__main__":
    unittest.main()
