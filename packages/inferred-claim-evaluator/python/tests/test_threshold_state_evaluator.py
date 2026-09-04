"""Mission 1.52 §43. The deterministic evaluator, gate by gate.

The tests that matter most are the ones proving what the evaluator REFUSES to
do. It is easy to write something that turns 110 into SUPPORTS; the work is
making sure it never turns an unestablished correspondence into one, never
converts a unit, never aligns a time window, never invents an interpretation
confidence, and never decides independence.

Pure functions throughout: no database, no network, no clock inside the
predicate. `unittest`, and the package imports only `sros_contracts` and
`sros_claim_model`, both of which the zero-dependency runner puts on its path.
"""

from __future__ import annotations

import unittest
from datetime import UTC, datetime
from decimal import Decimal

from sros_inferred_claim_evaluator import (
    ALL_EQUIVALENCE_DIMENSIONS,
    DERIVATION_RULE_ID,
    DERIVATION_RULE_VERSION,
    EVALUATOR_VERSION,
    PROPOSITION_KIND,
    DerivationDraft,
    EquivalenceVerdict,
    EvaluationResult,
    MeasurementWitness,
    SemanticEquivalenceDecision,
    TargetProposition,
    ThresholdOperator,
    ThresholdProvenanceStatus,
    ThresholdRegistration,
    evaluate,
    target_proposition_facts,
)

RETRIEVED = datetime(2026, 6, 1, tzinfo=UTC)
FROZEN = datetime(2026, 1, 1, tzinfo=UTC)


def target(**overrides) -> TargetProposition:
    fields = {
        "proposition_kind": PROPOSITION_KIND,
        "canonical_subject_id": "subject-1",
        "metric_definition_id": "metric-def-1",
        "time_bound": "2024",
        "population_or_geography": "population-1",
        "unit": "unit-1",
        "threshold_operator": ThresholdOperator.GTE,
        "threshold_value": Decimal("100"),
    }
    fields.update(overrides)
    return TargetProposition(**fields)


def registration(**overrides) -> ThresholdRegistration:
    fields = {
        "registration_id": "reg-1",
        "workspace_id": "ws-1",
        "metric_definition_id": "metric-def-1",
        "scope_subject_id": "subject-1",
        "scope_population": "population-1",
        "scope_time_bound": "2024",
        "unit": "unit-1",
        "threshold_operator": ThresholdOperator.GTE,
        "threshold_value": Decimal("100"),
        "provenance_status": ThresholdProvenanceStatus.PREREGISTERED,
        "recorded_at": FROZEN,
        "recorded_by": "fixture",
        "provenance_reference": "fixture-registration",
    }
    fields.update(overrides)
    return ThresholdRegistration(**fields)


def witness(value: str = "110", **overrides) -> MeasurementWitness:
    fields = {
        "workspace_id": "ws-1",
        "signal_id": "signal-a",
        "source_id": "source-a",
        "resource_id": "resource-a",
        "record_kind_id": "numeric_observation",
        "canonical_subject_id": "subject-1",
        "source_native_metric_id": "NATIVE.M",
        "metric_definition_id": "metric-def-1",
        "measurement_value": Decimal(value),
        "unit": "unit-1",
        "time_bound": "2024",
        "population_or_geography": "population-1",
        "retrieved_at": RETRIEVED,
    }
    fields.update(overrides)
    return MeasurementWitness(**fields)


def equivalent(**overrides) -> SemanticEquivalenceDecision:
    fields = {
        "basis_id": "basis-1",
        "verdict": EquivalenceVerdict.EQUIVALENT,
        "dimensions_checked": frozenset(ALL_EQUIVALENCE_DIMENSIONS),
        "reviewed_by": "reviewer",
        "reviewed_at": FROZEN,
        "interpretation_confidence": 0.8,
    }
    fields.update(overrides)
    return SemanticEquivalenceDecision(**fields)


def run(value: str = "110", **kwargs):
    return evaluate(
        kwargs.pop("witness", None) or witness(value),
        kwargs.pop("target", None) or target(),
        kwargs.pop("registration", None) or registration(),
        kwargs.pop("equivalence", None) or equivalent(),
    )


# ============================================ the predicate


class ThePredicate(unittest.TestCase):
    def test_above_the_bound_supports(self):
        self.assertIs(run("110").result, EvaluationResult.SUPPORTS)

    def test_exactly_at_the_bound_supports_for_gte(self):
        """The boundary case. `>=` is satisfied by equality, and getting this
        wrong is the classic off-by-one of a threshold rule."""
        self.assertIs(run("100").result, EvaluationResult.SUPPORTS)

    def test_below_the_bound_contradicts(self):
        self.assertIs(run("90").result, EvaluationResult.CONTRADICTS)

    def test_strict_greater_than_refuses_equality(self):
        outcome = run(
            "100",
            target=target(threshold_operator=ThresholdOperator.GT),
            registration=registration(threshold_operator=ThresholdOperator.GT),
        )
        self.assertIs(outcome.result, EvaluationResult.CONTRADICTS)

    def test_the_less_than_operators_work(self):
        for operator, value, expected in (
            (ThresholdOperator.LTE, "100", EvaluationResult.SUPPORTS),
            (ThresholdOperator.LTE, "110", EvaluationResult.CONTRADICTS),
            (ThresholdOperator.LT, "100", EvaluationResult.CONTRADICTS),
            (ThresholdOperator.LT, "90", EvaluationResult.SUPPORTS),
        ):
            with self.subTest(operator=operator, value=value):
                outcome = run(
                    value,
                    target=target(threshold_operator=operator),
                    registration=registration(threshold_operator=operator),
                )
                self.assertIs(outcome.result, expected)


class NumericExactness(unittest.TestCase):
    def test_a_float_measurement_is_refused_outright(self):
        with self.assertRaises(TypeError):
            witness(measurement_value=110.0)

    def test_decimal_boundary_is_exact(self):
        """0.1 + 0.2 famously is not 0.3 in binary. Decimal makes the boundary
        mean what it says."""
        outcome = run(
            "0.3",
            target=target(threshold_value=Decimal("0.3")),
            registration=registration(threshold_value=Decimal("0.3")),
        )
        self.assertIs(outcome.result, EvaluationResult.SUPPORTS)

    def test_a_hair_below_the_bound_contradicts(self):
        outcome = run(
            "99.999999999999999999",
            target=target(threshold_value=Decimal("100")),
        )
        self.assertIs(outcome.result, EvaluationResult.CONTRADICTS)


class Determinism(unittest.TestCase):
    def test_the_same_inputs_produce_the_same_outcome(self):
        first, second = run("110"), run("110")
        self.assertEqual(first.result, second.result)
        self.assertEqual(first.rationale, second.rationale)
        self.assertEqual(first.proposition_key, second.proposition_key)
        self.assertEqual(first.derivation, second.derivation)

    def test_the_module_reads_no_clock_and_no_randomness(self):
        import pathlib

        module = __import__(
            "sros_inferred_claim_evaluator.threshold_state", fromlist=["threshold_state"]
        )
        text = pathlib.Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in ("datetime.now", "utcnow", "random.", "time.time"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)


# ============================================ the equivalence gate


class EquivalenceIsRequiredBeforeTheArithmetic(unittest.TestCase):
    def test_not_equivalent_is_not_applicable_and_never_contradicts(self):
        outcome = run("90", equivalence=equivalent(verdict=EquivalenceVerdict.NOT_EQUIVALENT))
        self.assertIs(outcome.result, EvaluationResult.NOT_APPLICABLE)
        self.assertEqual(outcome.refusal_reason, "SEMANTIC_MISMATCH")

    def test_a_mismatch_that_would_have_supported_is_still_not_applicable(self):
        """The direction the arithmetic WOULD have produced is irrelevant once
        the correspondence fails, and testing the supporting case proves the
        gate runs first rather than merely relabelling a refusal."""
        outcome = run("110", equivalence=equivalent(verdict=EquivalenceVerdict.NOT_EQUIVALENT))
        self.assertIs(outcome.result, EvaluationResult.NOT_APPLICABLE)

    def test_unknown_equivalence_is_unknown_and_never_supports(self):
        outcome = run(
            "110",
            equivalence=SemanticEquivalenceDecision(
                basis_id="basis-1",
                verdict=EquivalenceVerdict.UNKNOWN,
                dimensions_checked=frozenset(),
                reviewed_by="reviewer",
                reviewed_at=FROZEN,
            ),
        )
        self.assertIs(outcome.result, EvaluationResult.UNKNOWN)
        self.assertEqual(outcome.refusal_reason, "EQUIVALENCE_NOT_ESTABLISHED")

    def test_equivalence_on_a_partial_dimension_set_is_refused_at_construction(self):
        with self.assertRaises(ValueError) as raised:
            equivalent(dimensions_checked=frozenset(list(ALL_EQUIVALENCE_DIMENSIONS)[:3]))
        self.assertIn("every frozen dimension", str(raised.exception))

    def test_the_evaluator_never_decides_equivalence_itself(self):
        """It consumes a decision. A decision saying NOT_EQUIVALENT over inputs
        that match on every visible field is still honoured, because the reviewer
        knows something the fields do not show."""
        outcome = run("110", equivalence=equivalent(verdict=EquivalenceVerdict.NOT_EQUIVALENT))
        self.assertIs(outcome.result, EvaluationResult.NOT_APPLICABLE)


class NoConversionAndNoAlignment(unittest.TestCase):
    def test_a_different_unit_is_not_applicable(self):
        outcome = run("110", witness=witness("110", unit="unit-2"))
        self.assertIs(outcome.result, EvaluationResult.NOT_APPLICABLE)
        self.assertEqual(outcome.refusal_reason, "UNIT_MISMATCH")

    def test_no_unit_conversion_helper_exists(self):
        module = __import__(
            "sros_inferred_claim_evaluator.threshold_state", fromlist=["threshold_state"]
        )
        for name in dir(module):
            with self.subTest(name=name):
                self.assertNotIn("convert", name.lower())

    def test_a_different_time_bound_is_not_applicable(self):
        outcome = run("110", witness=witness("110", time_bound="2025"))
        self.assertIs(outcome.result, EvaluationResult.NOT_APPLICABLE)
        self.assertEqual(outcome.refusal_reason, "TIME_BOUND_MISMATCH")


# ============================================ the registration gate


class TheRegistrationMustDescribeTheProposition(unittest.TestCase):
    def test_a_mismatched_threshold_value_is_refused(self):
        outcome = run("110", registration=registration(threshold_value=Decimal("50")))
        self.assertIs(outcome.result, EvaluationResult.NOT_APPLICABLE)
        self.assertEqual(outcome.refusal_reason, "THRESHOLD_REGISTRATION_MISMATCH")

    def test_a_mismatched_scope_is_refused(self):
        for field in ("metric_definition_id", "scope_subject_id", "scope_population"):
            with self.subTest(field=field):
                outcome = run("110", registration=registration(**{field: "other"}))
                self.assertIs(outcome.result, EvaluationResult.NOT_APPLICABLE)

    def test_the_evaluator_selects_no_registration_of_its_own(self):
        """`evaluate` takes exactly one registration and never searches. There is
        no collection to scan, so 'whichever bound makes the Claim work' is not
        expressible."""
        import inspect

        signature = inspect.signature(evaluate)
        self.assertIn("registration", signature.parameters)
        self.assertEqual(len(signature.parameters), 4)


# ============================================ threshold provenance


class ThresholdProvenanceChangesEligibilityAndNeverEntailment(unittest.TestCase):
    def test_post_hoc_still_supports(self):
        outcome = run(
            "110",
            registration=registration(
                provenance_status=ThresholdProvenanceStatus.POST_HOC,
                provenance_reference=None,
            ),
        )
        self.assertIs(outcome.result, EvaluationResult.SUPPORTS)

    def test_post_hoc_is_calibration_ineligible(self):
        outcome = run(
            "110",
            registration=registration(
                provenance_status=ThresholdProvenanceStatus.POST_HOC,
                provenance_reference=None,
            ),
        )
        self.assertFalse(outcome.calibration_eligible)

    def test_the_three_eligible_statuses_are_eligible(self):
        for status in (
            ThresholdProvenanceStatus.PREREGISTERED,
            ThresholdProvenanceStatus.SOURCE_NATIVE,
            ThresholdProvenanceStatus.EXTERNAL_NORM,
        ):
            with self.subTest(status=status):
                outcome = run("110", registration=registration(provenance_status=status))
                self.assertTrue(outcome.calibration_eligible)

    def test_unknown_provenance_is_ineligible(self):
        outcome = run(
            "110",
            registration=registration(
                provenance_status=ThresholdProvenanceStatus.UNKNOWN,
                provenance_reference=None,
            ),
        )
        self.assertIs(outcome.result, EvaluationResult.SUPPORTS)
        self.assertFalse(outcome.calibration_eligible)

    def test_a_valid_preregistration_relation_is_accepted(self):
        """recorded_at 2026-01-01 < retrieved_at 2026-06-01."""
        self.assertIs(run("110").result, EvaluationResult.SUPPORTS)

    def test_a_preregistration_recorded_after_retrieval_is_refused(self):
        """Labelled PREREGISTERED but frozen after this system held the
        measurement. That is an inconsistent record, and it is REFUSED rather
        than silently downgraded to POST_HOC -- a downgrade would quietly repair
        somebody's claim about when they decided."""
        outcome = run(
            "110",
            registration=registration(recorded_at=datetime(2026, 9, 1, tzinfo=UTC)),
        )
        self.assertIs(outcome.result, EvaluationResult.UNKNOWN)
        self.assertEqual(outcome.refusal_reason, "PREREGISTRATION_TIMING_INCONSISTENT")

    def test_the_timing_rule_uses_retrieval_and_not_publication(self):
        """There is no published_at anywhere in the witness contract, so the
        wrong comparison is not available to make."""
        self.assertFalse(hasattr(witness(), "published_at"))


# ============================================ proposition identity


class PropositionIdentity(unittest.TestCase):
    def test_two_different_measurements_share_one_proposition_key(self):
        self.assertEqual(run("110").proposition_key, run("105").proposition_key)

    def test_a_contradicting_measurement_shares_it_too(self):
        self.assertEqual(run("110").proposition_key, run("90").proposition_key)

    def test_a_different_source_shares_it(self):
        first = run("110", witness=witness("110", source_id="source-a"))
        second = run("105", witness=witness("105", source_id="source-b", signal_id="signal-b"))
        self.assertEqual(first.proposition_key, second.proposition_key)

    def test_a_different_threshold_is_a_different_proposition(self):
        other = run(
            "110",
            target=target(threshold_value=Decimal("200")),
            registration=registration(threshold_value=Decimal("200")),
        )
        self.assertNotEqual(run("110").proposition_key, other.proposition_key)

    def test_threshold_provenance_status_does_not_change_the_key(self):
        post_hoc = run(
            "110",
            registration=registration(
                provenance_status=ThresholdProvenanceStatus.POST_HOC,
                provenance_reference=None,
            ),
        )
        self.assertEqual(run("110").proposition_key, post_hoc.proposition_key)

    def test_the_identity_facts_exclude_what_they_must(self):
        facts = target_proposition_facts(target())
        for excluded in (
            "source_id",
            "measurement_value",
            "direction",
            "threshold_provenance_status",
            "derivation_rule_version",
            "evaluator_version",
        ):
            with self.subTest(excluded=excluded):
                self.assertNotIn(excluded, facts)

    def test_the_identity_facts_include_the_threshold(self):
        facts = target_proposition_facts(target())
        self.assertEqual(facts["threshold_operator"], "GTE")
        self.assertEqual(facts["threshold_value"], "100")
        self.assertEqual(facts["claim_type"], "INFERRED")

    def test_one_hundred_and_one_hundred_point_zero_are_one_bound(self):
        """Otherwise the same threshold written two ways forks the proposition,
        which is the measurement-value defect one field along."""
        self.assertEqual(
            target_proposition_facts(target(threshold_value=Decimal("100")))["threshold_value"],
            target_proposition_facts(target(threshold_value=Decimal("100.0")))["threshold_value"],
        )


# ============================================ what the outcome carries


class TheOutcome(unittest.TestCase):
    def test_a_directional_result_carries_a_claim_draft_and_an_evidence_decision(self):
        outcome = run("110")
        self.assertTrue(outcome.is_directional)
        self.assertIsNotNone(outcome.claim_draft)
        self.assertEqual(outcome.evidence_decision.direction, "SUPPORTS")

    def test_a_contradiction_carries_the_contradicting_direction(self):
        self.assertEqual(run("90").evidence_decision.direction, "CONTRADICTS")

    def test_a_refusal_carries_no_evidence_decision_and_no_claim(self):
        for equivalence_verdict, expected in (
            (EquivalenceVerdict.NOT_EQUIVALENT, EvaluationResult.NOT_APPLICABLE),
            (EquivalenceVerdict.UNKNOWN, EvaluationResult.UNKNOWN),
        ):
            with self.subTest(verdict=equivalence_verdict):
                decision = SemanticEquivalenceDecision(
                    basis_id="basis-1",
                    verdict=equivalence_verdict,
                    dimensions_checked=frozenset(),
                    reviewed_by="reviewer",
                    reviewed_at=FROZEN,
                )
                outcome = run("110", equivalence=decision)
                self.assertIs(outcome.result, expected)
                self.assertIsNone(outcome.evidence_decision)
                self.assertIsNone(outcome.claim_draft)
                self.assertIsNone(outcome.proposition_key)

    def test_a_refusal_still_carries_a_derivation_draft(self):
        """A refusal that leaves no trace is invisible. ADR-021 and ADR-025 set
        the shape and this keeps it."""
        outcome = run("110", equivalence=equivalent(verdict=EquivalenceVerdict.NOT_EQUIVALENT))
        self.assertIsNotNone(outcome.derivation)
        self.assertIs(outcome.derivation.evaluation_result, EvaluationResult.NOT_APPLICABLE)

    def test_neutral_is_not_reachable(self):
        self.assertNotIn("NEUTRAL", {member.value for member in EvaluationResult})

    def test_the_claim_draft_is_inferred_deterministic_with_no_model(self):
        draft = run("110").claim_draft
        self.assertEqual(draft.claim_type, "INFERRED")
        self.assertEqual(draft.interpretation_kind, "DETERMINISTIC")
        self.assertIsNone(draft.model_version)


class InterpretationConfidence(unittest.TestCase):
    def test_it_comes_from_the_equivalence_decision(self):
        draft = run("110", equivalence=equivalent(interpretation_confidence=0.62)).claim_draft
        self.assertEqual(draft.interpretation_confidence, 0.62)

    def test_it_is_never_set_to_one_by_the_arithmetic(self):
        """The comparison being exact says nothing about whether the wording
        faithfully reads the Signal. A reviewer supplying 0.7 keeps 0.7."""
        draft = run("110", equivalence=equivalent(interpretation_confidence=0.7)).claim_draft
        self.assertNotEqual(draft.interpretation_confidence, 1.0)

    def test_an_equivalent_decision_without_one_is_refused_at_construction(self):
        with self.assertRaises(ValueError) as raised:
            equivalent(interpretation_confidence=None)
        self.assertIn("no honest way to invent it", str(raised.exception))


class OriginDetailKeepsOneResponsibility(unittest.TestCase):
    def test_it_states_origin_and_not_the_audit_trail(self):
        draft = run("110").claim_draft
        self.assertIn("Deterministically derived from Signal", draft.origin_detail)

    def test_it_is_not_the_authority_for_structured_facts(self):
        """The measurement, the threshold, the basis and the result all live in
        the derivation record. `origin_detail` names the evaluator and stops."""
        outcome = run("110")
        for structured in ("110", "100", "basis-1", "SUPPORTS"):
            with self.subTest(structured=structured):
                self.assertNotIn(structured, outcome.claim_draft.origin_detail)


class TheDerivationDraft(unittest.TestCase):
    def test_it_carries_every_field_it_owns(self):
        derivation = run("110").derivation
        self.assertEqual(derivation.derivation_rule_id, DERIVATION_RULE_ID)
        self.assertEqual(derivation.derivation_rule_version, DERIVATION_RULE_VERSION)
        self.assertEqual(derivation.evaluator_version, EVALUATOR_VERSION)
        self.assertEqual(derivation.measurement_value, Decimal("110"))
        self.assertEqual(derivation.threshold_registration_id, "reg-1")
        self.assertEqual(derivation.semantic_equivalence_basis_id, "basis-1")
        self.assertEqual(derivation.interpretation_kind, "DETERMINISTIC")
        self.assertIsNone(derivation.model_version)
        self.assertTrue(derivation.rationale.strip())

    def test_it_carries_no_claim_revision_id(self):
        """By construction. The revision does not exist when the evaluation
        runs, and inventing an id would fabricate the thing the record exists to
        prove."""
        self.assertFalse(hasattr(run("110").derivation, "claim_revision_id"))

    def test_the_rule_version_and_the_evaluator_version_are_two_fields(self):
        """They happen to read 1.0.0 today, which is exactly why the test is
        about the FIELDS rather than the values. Migration 0034's idempotency key
        contains `derivation_rule_version` and not `evaluator_version`: replaying
        a different RULE is different reasoning and earns its own row, while
        rebuilding the same rule under a new evaluator is not. One field could
        not carry both meanings."""
        import dataclasses

        names = {f.name for f in dataclasses.fields(DerivationDraft)}
        self.assertIn("derivation_rule_version", names)
        self.assertIn("evaluator_version", names)
        derivation = run("110").derivation
        self.assertEqual(derivation.derivation_rule_version, DERIVATION_RULE_VERSION)
        self.assertEqual(derivation.evaluator_version, EVALUATOR_VERSION)


# ============================================ what the evaluator must not do


class TheEvaluatorDecidesNeitherIndependenceNorReliability(unittest.TestCase):
    def test_no_independence_appears_anywhere_in_the_outcome(self):
        outcome = run("110")
        text = repr(outcome)
        for forbidden in ("KNOWN_INDEPENDENT", "independence", "INDEPENDEN"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)

    def test_no_reliability_appears_anywhere_in_the_outcome(self):
        self.assertNotIn("reliability", repr(run("110")).lower())

    def test_dependence_does_not_change_the_direction(self):
        """A republication of the same value still SUPPORTS. It stays one
        provenance group downstream, which is the aggregator's business."""
        first = run("110", witness=witness("110", source_id="source-a"))
        republished = run("110", witness=witness("110", source_id="source-b", signal_id="signal-b"))
        self.assertIs(first.result, EvaluationResult.SUPPORTS)
        self.assertIs(republished.result, EvaluationResult.SUPPORTS)


class PackageBoundary(unittest.TestCase):
    FORBIDDEN = (
        "sros_acquisition",
        "sros_llm_gateway",
        "sros_evidence_aggregation",
        "sros_opportunity",
        "sros_nlp",
    )

    def test_the_package_imports_none_of_the_forbidden_packages(self):
        import pathlib

        import sros_inferred_claim_evaluator

        root = pathlib.Path(sros_inferred_claim_evaluator.__file__).parent
        for module in root.glob("*.py"):
            text = module.read_text(encoding="utf-8")
            for forbidden in self.FORBIDDEN:
                with self.subTest(module=module.name, forbidden=forbidden):
                    self.assertNotIn(f"import {forbidden}", text)
                    self.assertNotIn(f"from {forbidden}", text)

    def test_it_can_be_imported_at_all(self):
        import sros_inferred_claim_evaluator

        self.assertTrue(sros_inferred_claim_evaluator.__doc__)


if __name__ == "__main__":
    unittest.main()
