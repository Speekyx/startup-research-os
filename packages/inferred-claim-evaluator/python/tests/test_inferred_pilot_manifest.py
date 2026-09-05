"""Mission 1.56 §46. The pilot artifacts, checked against the code that will run.

The manifest is a promise about what one attended execution will do. What can be
tested before the operator approves it is whether the promise is expressible: the
target key must RECOMPUTE through the real claim model, the threshold's
provenance must be the one the real evaluator would accept for these timings, and
the equivalence decision must construct under the real constructor's own rules.

Every fixture is built from the manifest's own values and driven through the real
`evaluate()`. A test that restated the manifest's fields would be checking the
record against itself.

`unittest`, importing only `sros_contracts`, `sros_claim_model` and the evaluator
-- the packages the zero-dependency runner puts on this suite's path.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import unittest
from datetime import datetime
from decimal import Decimal

from sros_claim_model import proposition_key
from sros_inferred_claim_evaluator import (
    ALL_EQUIVALENCE_DIMENSIONS,
    DERIVATION_RULE_ID,
    DERIVATION_RULE_VERSION,
    EVALUATOR_VERSION,
    PROPOSITION_KIND,
    EquivalenceDimension,
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

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SELECTION = DATA / "first-deterministic-inferred-pilot-candidate-selection-v1.json"
EQUIVALENCE = DATA / "first-deterministic-inferred-pilot-equivalence-v1.json"
MANIFEST = DATA / "first-deterministic-inferred-pilot-manifest-v1.json"
EXECUTION = DATA / "first-deterministic-inferred-pilot-v1.json"
RESOLUTION = DATA / "first-deterministic-inferred-pilot-resolution-v1.json"
RENDERER = REPO_ROOT / "infrastructure" / "scripts" / "render_inferred_pilot.py"


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _renderer():
    """Loaded by PATH rather than reimplemented, so the hash the operator
    approves and the hash this suite checks come from one function."""
    spec = importlib.util.spec_from_file_location("render_inferred_pilot", RENDERER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SELECTION_RECORD = _load(SELECTION)
EQUIVALENCE_RECORD = _load(EQUIVALENCE)
MANIFEST_RECORD = _load(MANIFEST)
RECORDED_AT = datetime.fromisoformat(MANIFEST_RECORD["recorded_at"] + "T00:00:00+00:00")


def _target() -> TargetProposition:
    facts = MANIFEST_RECORD["target_proposition"]["facts"]
    return TargetProposition(
        proposition_kind=facts["proposition"],
        canonical_subject_id=facts["canonical_subject_id"],
        metric_definition_id=facts["metric_definition_id"],
        time_bound=facts["time_bound"],
        population_or_geography=facts["population_or_geography"],
        unit=facts["unit"],
        threshold_operator=ThresholdOperator(facts["threshold_operator"]),
        threshold_value=Decimal(facts["threshold_value"]),
    )


def _witness() -> MeasurementWitness:
    signal = MANIFEST_RECORD["selected_signal"]
    facts = MANIFEST_RECORD["target_proposition"]["facts"]
    return MeasurementWitness(
        workspace_id="00000000-0000-0000-0000-000000000000",
        signal_id=signal["signal_id"],
        source_id=signal["source_id"],
        resource_id="metrics/pageviews/per-article",
        record_kind_id=signal["record_kind_id"],
        canonical_subject_id=facts["canonical_subject_id"],
        source_native_metric_id=signal["signal_type_id"],
        metric_definition_id=facts["metric_definition_id"],
        measurement_value=Decimal(signal["measurement_value"]),
        unit=signal["unit"],
        time_bound=facts["time_bound"],
        population_or_geography=facts["population_or_geography"],
        retrieved_at=datetime.fromisoformat(signal["retrieved_at"]),
    )


def _equivalence() -> SemanticEquivalenceDecision:
    return SemanticEquivalenceDecision(
        basis_id=EQUIVALENCE_RECORD["basis_id"],
        verdict=EquivalenceVerdict(EQUIVALENCE_RECORD["verdict"]),
        dimensions_checked=frozenset(
            EquivalenceDimension(entry["dimension"]) for entry in EQUIVALENCE_RECORD["dimensions"]
        ),
        reviewed_by=EQUIVALENCE_RECORD["reviewed_by"],
        reviewed_at=RECORDED_AT,
        interpretation_confidence=EQUIVALENCE_RECORD["interpretation_confidence"]["proposed_value"],
    )


def _registration(
    status: ThresholdProvenanceStatus, recorded_at: datetime
) -> ThresholdRegistration:
    threshold = MANIFEST_RECORD["threshold_registration"]
    return ThresholdRegistration(
        registration_id="00000000-0000-0000-0000-0000000000aa",
        workspace_id="00000000-0000-0000-0000-000000000000",
        metric_definition_id=threshold["metric_definition_id"],
        scope_subject_id=threshold["scope_subject_id"],
        scope_population=threshold["scope_population"],
        scope_time_bound=threshold["scope_time_bound"],
        unit=threshold["unit"],
        threshold_operator=ThresholdOperator(threshold["threshold_operator"]),
        threshold_value=Decimal(threshold["threshold_value"]),
        provenance_status=status,
        recorded_at=recorded_at,
        recorded_by=threshold["recorded_by"],
    )


class TestTheTargetKeyRecomputes(unittest.TestCase):
    """The proposition key is the one thing in the manifest a later mission will
    look rows up by, so it is verified through the real code rather than
    trusted: a key nobody can recompute is a key nobody can join on."""

    def test_the_facts_come_out_of_the_real_rule_module(self) -> None:
        self.assertEqual(
            target_proposition_facts(_target()),
            MANIFEST_RECORD["target_proposition"]["facts"],
        )

    def test_the_key_comes_out_of_the_real_claim_model(self) -> None:
        facts = target_proposition_facts(_target())
        self.assertEqual(
            proposition_key(facts), MANIFEST_RECORD["target_proposition"]["proposition_key"]
        )

    def test_the_proposition_kind_is_the_evaluators_own(self) -> None:
        self.assertEqual(
            MANIFEST_RECORD["target_proposition"]["facts"]["proposition"], PROPOSITION_KIND
        )

    def test_the_target_carries_no_witness_fact(self) -> None:
        """ADR-036: the measurement, the source and the direction are what let
        several witnesses reach ONE Claim, so none of them may be identity."""
        facts = MANIFEST_RECORD["target_proposition"]["facts"]
        for excluded in ("source_id", "signal_id", "measurement_value", "direction"):
            self.assertNotIn(excluded, facts)


class TestPreregistrationIsImpossibleRatherThanUnchosen(unittest.TestCase):
    """The manifest records POST_HOC and says PREREGISTERED was not attempted.
    That is a claim about the code's behaviour, so it is executed."""

    def test_the_real_evaluator_refuses_a_preregistered_label_for_these_timings(self) -> None:
        outcome = evaluate(
            _witness(),
            _target(),
            _registration(ThresholdProvenanceStatus.PREREGISTERED, RECORDED_AT),
            _equivalence(),
        )
        self.assertIs(outcome.result, EvaluationResult.UNKNOWN)
        self.assertEqual(outcome.refusal_reason, "PREREGISTRATION_TIMING_INCONSISTENT")

    def test_it_is_refused_rather_than_downgraded(self) -> None:
        """A silent downgrade would repair somebody's claim about when they
        decided, which is the one thing threshold provenance exists to record."""
        outcome = evaluate(
            _witness(),
            _target(),
            _registration(ThresholdProvenanceStatus.PREREGISTERED, RECORDED_AT),
            _equivalence(),
        )
        self.assertNotIn(outcome.result, (EvaluationResult.SUPPORTS, EvaluationResult.CONTRADICTS))

    def test_the_recorded_provenance_is_a_real_member_and_not_preregistered(self) -> None:
        status = ThresholdProvenanceStatus(
            MANIFEST_RECORD["threshold_registration"]["provenance_status"]
        )
        self.assertIsNot(status, ThresholdProvenanceStatus.PREREGISTERED)

    def test_calibration_eligibility_is_derived_and_not_copied(self) -> None:
        """Migration 0034 stores no `calibration_eligible` column. The manifest's
        `false` has to agree with what the real property derives, or the manifest
        becomes the second authority ADR-037 refused to create."""
        status = ThresholdProvenanceStatus(
            MANIFEST_RECORD["threshold_registration"]["provenance_status"]
        )
        registration = _registration(status, RECORDED_AT)
        self.assertFalse(registration.calibration_eligible)
        self.assertEqual(
            registration.calibration_eligible,
            MANIFEST_RECORD["threshold_registration"]["calibration_eligible"],
        )

    def test_the_retrieval_instant_really_is_before_the_recording_day(self) -> None:
        retrieved = datetime.fromisoformat(MANIFEST_RECORD["selected_signal"]["retrieved_at"])
        arithmetic = MANIFEST_RECORD["threshold_registration"][
            "preregistration_is_arithmetically_impossible"
        ]
        self.assertEqual(datetime.fromisoformat(arithmetic["measurement_retrieved_at"]), retrieved)
        self.assertLess(retrieved, RECORDED_AT)


class TestTheEquivalenceDecisionConstructs(unittest.TestCase):
    def test_the_real_constructor_accepts_it(self) -> None:
        decision = _equivalence()
        self.assertIs(decision.verdict, EquivalenceVerdict.EQUIVALENT)
        self.assertEqual(decision.basis_id, MANIFEST_RECORD["semantic_equivalence"]["basis_id"])

    def test_every_frozen_dimension_was_checked(self) -> None:
        self.assertEqual(_equivalence().dimensions_checked, ALL_EQUIVALENCE_DIMENSIONS)

    def test_an_equivalent_verdict_missing_one_dimension_is_refused(self) -> None:
        """The control. Without it the test above would pass against a
        constructor that checks nothing."""
        dropped = frozenset(sorted(ALL_EQUIVALENCE_DIMENSIONS, key=lambda d: d.value)[1:])
        with self.assertRaises(ValueError):
            SemanticEquivalenceDecision(
                basis_id=EQUIVALENCE_RECORD["basis_id"],
                verdict=EquivalenceVerdict.EQUIVALENT,
                dimensions_checked=dropped,
                reviewed_by="thibchm",
                reviewed_at=RECORDED_AT,
                interpretation_confidence=0.9,
            )

    def test_the_confidence_is_not_one_and_comes_from_the_basis(self) -> None:
        confidence = EQUIVALENCE_RECORD["interpretation_confidence"]
        self.assertNotEqual(confidence["proposed_value"], 1.0)
        self.assertTrue(0.0 < confidence["proposed_value"] < 1.0)
        self.assertTrue(confidence["not_invented_by_the_evaluator"])
        self.assertEqual(
            MANIFEST_RECORD["semantic_equivalence"]["interpretation_confidence"],
            confidence["proposed_value"],
        )

    def test_no_model_produced_the_decision(self) -> None:
        self.assertEqual(EQUIVALENCE_RECORD["model_calls"], 0)
        self.assertEqual(EQUIVALENCE_RECORD["network_requests"], 0)
        self.assertTrue(EQUIVALENCE_RECORD["no_model_generated_approval"])


class TestTheManifestDoesNotKnowTheAnswer(unittest.TestCase):
    def test_it_records_that_the_evaluator_has_not_run(self) -> None:
        self.assertTrue(MANIFEST_RECORD["evaluator_has_not_run"])

    def test_it_carries_no_result_field_of_any_name(self) -> None:
        for banned in ("evaluation_result", "result", "outcome", "supports", "contradicts"):
            self.assertNotIn(banned, MANIFEST_RECORD)

    def test_the_four_results_it_routes_are_exactly_the_evaluators_own(self) -> None:
        routed = {
            r for entry in MANIFEST_RECORD["allowed_persistence_paths"] for r in entry["if_result"]
        }
        self.assertEqual(routed, {member.value for member in EvaluationResult})

    def test_no_result_appears_in_two_paths(self) -> None:
        listed = [
            r for entry in MANIFEST_RECORD["allowed_persistence_paths"] for r in entry["if_result"]
        ]
        self.assertEqual(len(listed), len(set(listed)))

    def test_success_is_not_defined_as_supports(self) -> None:
        self.assertTrue(MANIFEST_RECORD["all_four_results_are_legitimate"])
        self.assertTrue(MANIFEST_RECORD["success_is_not_defined_as_supports"])

    def test_the_evaluation_block_names_the_real_versions(self) -> None:
        evaluation = MANIFEST_RECORD["evaluation"]
        self.assertEqual(evaluation["derivation_rule_id"], DERIVATION_RULE_ID)
        self.assertEqual(evaluation["derivation_rule_version"], DERIVATION_RULE_VERSION)
        self.assertEqual(evaluation["evaluator_version"], EVALUATOR_VERSION)
        self.assertIsNone(evaluation["model_version"])
        self.assertEqual(evaluation["calls_permitted"], 1)


class TestTheThreeArtifactsAgree(unittest.TestCase):
    def test_they_name_one_candidate(self) -> None:
        chosen = SELECTION_RECORD["selected"]["signal_id"]
        self.assertEqual(MANIFEST_RECORD["selected_signal"]["signal_id"], chosen)
        self.assertEqual(EQUIVALENCE_RECORD["measurement"]["signal_id"], chosen)

    def test_the_equivalence_target_matches_the_manifest_target(self) -> None:
        facts = MANIFEST_RECORD["target_proposition"]["facts"]
        target = EQUIVALENCE_RECORD["target"]
        for field in (
            "canonical_subject_id",
            "metric_definition_id",
            "time_bound",
            "population_or_geography",
            "unit",
            "threshold_operator",
            "threshold_value",
        ):
            self.assertEqual(target[field], facts[field], field)

    def test_the_measurement_matches_the_signal(self) -> None:
        self.assertEqual(
            EQUIVALENCE_RECORD["measurement"]["value"],
            MANIFEST_RECORD["selected_signal"]["measurement_value"],
        )
        self.assertEqual(
            EQUIVALENCE_RECORD["measurement"]["unit"],
            MANIFEST_RECORD["selected_signal"]["unit"],
        )


class TestTheSelectionWasMeasured(unittest.TestCase):
    def test_every_family_is_accounted_for(self) -> None:
        self.assertEqual(
            sum(f["count"] for f in SELECTION_RECORD["families"]),
            SELECTION_RECORD["signals_inspected"],
        )

    def test_every_failing_family_names_a_gate(self) -> None:
        for family in SELECTION_RECORD["families"]:
            if family["verdict"] == "FAILS":
                self.assertTrue(family.get("failed_gate") or family.get("failed_gates"), family)

    def test_all_fifteen_gates_are_met_by_something_stated(self) -> None:
        gates = SELECTION_RECORD["hard_gates_for_the_selected_candidate"]
        self.assertEqual(len(gates), 15)
        self.assertEqual([g["n"] for g in gates], list(range(1, 16)))
        for gate in gates:
            self.assertTrue(gate["met"], gate["gate"])
            self.assertTrue(gate["how"].strip(), gate["gate"])

    def test_magnitude_was_excluded_as_a_criterion(self) -> None:
        block = SELECTION_RECORD["magnitude_was_not_a_selection_criterion"]
        self.assertTrue(block["asserted"])
        self.assertIn("measurement magnitude", block["not_used"])

    def test_the_partial_independence_limitation_is_stated_in_both_places(self) -> None:
        """The operator has to meet it before approving, not afterwards in a
        report, so it appears in the selection AND in the manifest."""
        self.assertEqual(
            SELECTION_RECORD["the_limitation_worth_stating_before_approval"]["concern"],
            MANIFEST_RECORD["known_limitation_the_operator_should_weigh"]["flag"],
        )


class TestTheExecutionRecord(unittest.TestCase):
    """What the attended run recorded, once it has run.

    Every assertion reads the frozen file rather than the database, so these are
    deployment-independent: they check that the record is internally honest, not
    that a particular deployment holds particular rows.
    """

    def setUp(self) -> None:
        if not EXECUTION.exists():
            self.skipTest("the pilot has not been executed yet")
        self.record = _load(EXECUTION)

    def test_the_result_is_one_the_evaluator_can_return(self) -> None:
        self.assertIn(
            self.record["evaluation"]["result"], {member.value for member in EvaluationResult}
        )

    def test_the_path_taken_is_the_one_the_manifest_routes_that_result_to(self) -> None:
        routed = {
            r: entry["path"]
            for entry in MANIFEST_RECORD["allowed_persistence_paths"]
            for r in entry["if_result"]
        }
        self.assertEqual(
            self.record["persistence"]["path"], routed[self.record["evaluation"]["result"]]
        )

    def test_the_approval_names_the_manifest_that_is_on_disk(self) -> None:
        module = _renderer()
        self.assertEqual(
            self.record["approval"]["manifest_sha256"], module.manifest_hash(MANIFEST_RECORD)
        )

    def test_the_evaluator_ran_once_and_no_model_ran_at_all(self) -> None:
        evaluation = self.record["evaluation"]
        self.assertEqual(evaluation["calls"], 1)
        self.assertEqual(evaluation["second_call_with_adjusted_inputs"], 0)
        self.assertEqual(evaluation["model_calls"], 0)
        self.assertEqual(evaluation["network_requests"], 0)

    def test_it_evaluated_the_approved_proposition(self) -> None:
        self.assertEqual(
            self.record["evaluation"]["proposition_key"],
            MANIFEST_RECORD["target_proposition"]["proposition_key"],
        )
        self.assertEqual(
            self.record["evaluation"]["target_proposition_facts"],
            MANIFEST_RECORD["target_proposition"]["facts"],
        )

    def test_the_counters_moved_by_exactly_the_authorised_envelope(self) -> None:
        envelope = MANIFEST_RECORD["canonical_mutation_envelope"]
        allowed = dict(
            envelope["directional_maximum"]
            if self.record["persistence"]["path"] == "DIRECTIONAL"
            else envelope["refusal_maximum"]
        )
        allowed["threshold_registrations"] = envelope["threshold_registrations"]
        before, after = self.record["counters"]["before"], self.record["counters"]["after"]
        for name in before:
            self.assertEqual(after[name] - before[name], allowed.get(name, 0), name)

    def test_the_replay_changed_nothing(self) -> None:
        self.assertEqual(self.record["counters"]["after_replay"], self.record["counters"]["after"])
        self.assertEqual(self.record["replay"]["rows_created"], 0)

    def test_a_post_hoc_bound_is_still_not_calibration_eligible_after_running(self) -> None:
        """The outcome does not launder the provenance. Whatever the evaluator
        concluded, the bound was chosen after the measurement was visible."""
        self.assertFalse(self.record["evaluation"]["calibration_eligible"])
        self.assertEqual(self.record["threshold_registration"]["provenance_status"], "POST_HOC")

    def test_the_bound_was_written_before_the_evaluation(self) -> None:
        self.assertTrue(
            self.record["threshold_registration"]["written_before_the_evaluation"].strip()
        )


class TestTheDownstreamResolution(unittest.TestCase):
    def setUp(self) -> None:
        if not RESOLUTION.exists():
            self.skipTest("the pilot has not been executed yet")
        self.record = _load(RESOLUTION)

    def test_no_reliability_was_invented_for_the_new_scope(self) -> None:
        reliability = self.record["reliability"]
        self.assertEqual(reliability["outcome"], "NO_APPLICABLE_ASSESSMENT")
        self.assertIsNone(reliability["reliability"])

    def test_every_reviewed_assessment_was_offered_and_none_reached_it(self) -> None:
        """The leak check. An assessment sharing four of five scope fields is as
        inapplicable as one sharing none, and the way to know is to offer them
        all to the real resolver rather than to filter first."""
        self.assertGreater(len(self.record["reliability"]["nothing_leaked"]), 0)
        for entry in self.record["reliability"]["nothing_leaked"]:
            self.assertTrue(entry["differs_on"], entry)

    def test_the_aggregation_produced_no_number(self) -> None:
        aggregation = self.record["aggregation"]
        self.assertEqual(aggregation["scorable_evidence_count"], 0)
        self.assertIsNone(aggregation["evidence_score"])

    def test_it_wrote_nothing(self) -> None:
        self.assertTrue(self.record["read_only"])
        self.assertEqual(self.record["rows_written"], 0)

    def test_a_contradiction_row_now_exists_and_the_conflict_case_still_does_not(self) -> None:
        """Two facts that must be reported together. Mission 1.48 found every
        one of 57 Evidence rows was SUPPORTS; the INFERRED layer can emit the
        other direction. It does NOT follow that the aggregator's contradiction
        arithmetic has run: that needs one Claim carrying both directions, and
        reporting the first without the second would overstate what changed."""
        direction = self.record["the_direction_that_had_never_existed"]
        self.assertGreater(direction["evidence_by_direction"].get("CONTRADICTS", 0), 0)
        self.assertEqual(direction["claims_carrying_both_directions"], 0)


class TestTheManifestHash(unittest.TestCase):
    def test_it_is_the_sha256_of_the_canonical_manifest(self) -> None:
        module = _renderer()
        payload = json.dumps(
            MANIFEST_RECORD, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        self.assertEqual(
            module.manifest_hash(MANIFEST_RECORD),
            hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        )

    def test_one_changed_byte_changes_the_hash(self) -> None:
        """What makes the approval string worth typing: a manifest edited after
        approval no longer answers to the hash the operator approved."""
        module = _renderer()
        tampered = json.loads(json.dumps(MANIFEST_RECORD))
        tampered["threshold_registration"]["threshold_value"] = "900"
        self.assertNotEqual(module.manifest_hash(tampered), module.manifest_hash(MANIFEST_RECORD))

    def test_key_order_does_not_change_it(self) -> None:
        module = _renderer()
        reversed_order = dict(reversed(list(MANIFEST_RECORD.items())))
        self.assertEqual(
            module.manifest_hash(reversed_order), module.manifest_hash(MANIFEST_RECORD)
        )

    def test_the_manifest_is_awaiting_approval_and_not_approved(self) -> None:
        self.assertEqual(MANIFEST_RECORD["status"], "AWAITING_OPERATOR_APPROVAL")
        self.assertTrue(MANIFEST_RECORD["approval"]["manifest_is_frozen_once_hashed"])


if __name__ == "__main__":
    unittest.main()
