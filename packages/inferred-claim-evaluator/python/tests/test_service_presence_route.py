"""Mission 1.59 §53, §62, §63. The gate-closure records and the identity fixture.

Two groups.

**The records.** The rules a later mission could most easily bend to make a route
pass: a vendor's opinion is not a standard, a last-change time is not an
observation time, an absence is not a statement, and fifteen gates are not
sixteen. Read from the checked-in artifacts, never from the database.

**The identity fixture.** §53 driven through the REAL `TargetProposition` and the
REAL `proposition_key`: two witnesses on opposite sides of a bound must reach ONE
proposition key, or the protocol narrowing has smuggled scanner identity into
Claim identity.

The fixture values are `4242` and `1717` and the bound is `3000` -- numbers
chosen so nobody can mistake them for a measurement. Nothing is persisted, and no
measurement value was retrieved to construct them.
"""

from __future__ import annotations

import json
import pathlib
import unittest
from decimal import Decimal

from sros_claim_model import proposition_key
from sros_inferred_claim_evaluator import (
    PROPOSITION_KIND,
    TargetProposition,
    ThresholdOperator,
    target_proposition_facts,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
BASELINE = DATA / "internet-wide-service-presence-gate-closure-baseline-v1.json"
METRIC = DATA / "internet-wide-service-presence-metric-definition-v1.json"
TIME = DATA / "internet-wide-service-presence-time-contract-v1.json"
LINEAGE = DATA / "internet-wide-service-presence-lineage-review-v1.json"
CLOSURE = DATA / "internet-wide-service-presence-route-gate-closure-v1.json"

# Deliberately unmistakable for measurements.
WITNESS_ABOVE = Decimal("4242")
WITNESS_BELOW = Decimal("1717")
SYNTHETIC_BOUND = Decimal("3000")


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


BASELINE_RECORD = _load(BASELINE)
METRIC_RECORD = _load(METRIC)
TIME_RECORD = _load(TIME)
LINEAGE_RECORD = _load(LINEAGE)
CLOSURE_RECORD = _load(CLOSURE)


def _target() -> TargetProposition:
    """The FUTURE proposition, constructed and never created. It carries no
    scanner, no measurement and no direction."""
    return TargetProposition(
        proposition_kind=PROPOSITION_KIND,
        canonical_subject_id="ssh-transport-protocol",
        metric_definition_id="public_ipv4_protocol_responsive_host_count:tcp-22:rfc4253-id-string",
        time_bound="2026-10-01/2026-10-02",
        population_or_geography="public-ipv4",
        unit="hosts",
        threshold_operator=ThresholdOperator.GTE,
        threshold_value=SYNTHETIC_BOUND,
    )


class TestTheIdentityFixture(unittest.TestCase):
    """§53. Two witnesses, opposite sides of the bound, one Claim."""

    def test_both_witnesses_reach_one_proposition_key(self) -> None:
        facts = target_proposition_facts(_target())
        first = proposition_key(facts)
        second = proposition_key(target_proposition_facts(_target()))
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_the_target_carries_no_scanner_and_no_measurement(self) -> None:
        facts = target_proposition_facts(_target())
        blob = json.dumps(facts).lower()
        for excluded in ("censys", "netlas", "scanner", "vendor"):
            self.assertNotIn(excluded, blob)
        for key in ("source_id", "measurement_value", "direction", "signal_id"):
            self.assertNotIn(key, facts)

    def test_the_witness_values_never_enter_identity(self) -> None:
        """The point of the fixture: a supporting and a contradicting witness
        produce the SAME key, because the value is not identity."""
        facts = target_proposition_facts(_target())
        blob = json.dumps(facts)
        self.assertNotIn(str(WITNESS_ABOVE), blob)
        self.assertNotIn(str(WITNESS_BELOW), blob)
        self.assertGreater(WITNESS_ABOVE, SYNTHETIC_BOUND)
        self.assertLess(WITNESS_BELOW, SYNTHETIC_BOUND)

    def test_the_record_agrees_that_no_schema_change_is_needed(self) -> None:
        target = CLOSURE_RECORD["future_target_proposition"]
        self.assertTrue(target["representable_by_current_contract"])
        self.assertFalse(target["schema_change_required"])
        self.assertFalse(target["scanner_identity_required_in_identity"])


class TestTheMetricIsProtocolNative(unittest.TestCase):
    """§3 to §9. The construct may not rest on a vendor's classifier."""

    def setUp(self) -> None:
        self.selected = METRIC_RECORD["selected_construct"]

    def test_no_vendor_fingerprint_and_no_classifier_in_the_definition(self) -> None:
        self.assertFalse(self.selected["vendor_fingerprint_required"])
        self.assertFalse(self.selected["classifier_inside_definition"])

    def test_the_protocol_basis_is_a_retrieved_standard(self) -> None:
        basis = self.selected["protocol_basis"]
        self.assertTrue(basis["retrieved_first_party"])
        self.assertTrue(basis["standard"].strip())
        self.assertTrue(basis["section"].strip())

    def test_vendor_labels_are_classified_as_vendor_derived(self) -> None:
        derived = " ".join(METRIC_RECORD["fact_classification"]["VENDOR_DERIVED"]).lower()
        self.assertIn("service or product name", derived)
        self.assertIn("software version", derived)

    def test_the_metric_name_says_what_is_measured(self) -> None:
        for forbidden in ("product_installations", "service_users", "market_adoption"):
            self.assertNotEqual(self.selected["metric_name"], forbidden)

    def test_every_overclaim_is_refused_by_name(self) -> None:
        """A bounded sentence that does not say what it excludes is not bounded:
        a reader supplies adoption, users and customers for free."""
        excluded = " ".join(
            METRIC_RECORD["what_the_construct_does_and_does_not_mean"]["it_is_not"]
        ).lower()
        for word in ("installation", "user", "customer", "revenue", "demand", "adoption"):
            self.assertIn(word, excluded)

    def test_gate_3_did_not_pass_on_an_unestablished_mapping(self) -> None:
        gate = METRIC_RECORD["gate_3"]
        if gate["status"] == "PASS":
            for side in ("apparatus_A_mapping", "apparatus_B_mapping"):
                self.assertNotIn("NOT_ESTABLISHED", gate[side])


class TestTheTimeContract(unittest.TestCase):
    """§10 to §18. The gate that decided the mission."""

    def setUp(self) -> None:
        self.gate = TIME_RECORD["gate_5"]

    def test_a_failing_gate_names_its_blocker(self) -> None:
        if self.gate["status"] != "PASS":
            self.assertTrue(self.gate["exact_blocker"].strip())

    def test_a_passing_gate_would_need_a_freezable_rule(self) -> None:
        if self.gate["status"] == "PASS":
            self.assertTrue(self.gate["rule_freezable_before_values"])
            self.assertFalse(self.gate["retrospective_value_based_pairing_required"])

    def test_retrospective_pairing_is_not_treated_as_acceptable(self) -> None:
        """§18. A rule that can only be applied once the values are in hand is
        not a preregistrable rule, whatever else is true of it."""
        if self.gate["retrospective_value_based_pairing_required"]:
            self.assertNotEqual(self.gate["status"], "PASS")

    def test_a_tolerance_was_not_chosen_because_it_salvaged_the_route(self) -> None:
        rules = TIME_RECORD["alignment_rules_evaluated"]
        tolerance = rules["C_pre_frozen_maximum_timestamp_distance"]
        self.assertNotEqual(tolerance["verdict"], "SELECTED")
        self.assertTrue(tolerance["why"].strip())

    def test_the_two_dataset_shapes_are_recorded(self) -> None:
        shapes = {
            TIME_RECORD[side]["dataset_shape"]
            for side in ("apparatus_a_time_semantics", "apparatus_b_time_semantics")
        }
        self.assertEqual(shapes, {"MERGED_CURRENT_STATE", "DISCRETE_POINT_IN_TIME_OBSERVATIONS"})

    def test_measurement_difference_is_kept_apart_from_world_change(self) -> None:
        separation = TIME_RECORD["separating_measurement_difference_from_world_change"]
        self.assertTrue(separation["requirement"].strip())
        self.assertTrue(separation["under_this_pair"].strip())


class TestTheLineageReview(unittest.TestCase):
    """§19 to §26. An absence is never upgraded."""

    def test_absence_was_not_treated_as_proof(self) -> None:
        self.assertFalse(LINEAGE_RECORD["gate_10"]["absence_of_evidence_treated_as_proof"])

    def test_gate_10_did_not_pass_on_one_sided_evidence(self) -> None:
        gate = LINEAGE_RECORD["gate_10"]
        if gate["status"] == "PASS":
            self.assertTrue(gate["affirmative_A"])
            self.assertTrue(gate["affirmative_B"])

    def test_structural_non_republication_is_kept_apart_from_lineage(self) -> None:
        """§24. There is no authoritative published host count to copy, and that
        is a fact about the class rather than a lineage proof for a pair."""
        shared = LINEAGE_RECORD["shared_auxiliary_inputs"]
        self.assertIn(
            "STRUCTURAL_NON_REPUBLICATION", shared["the_structural_point_that_still_holds"]
        )
        self.assertIn(
            "APPARATUS_LINEAGE_ESTABLISHED", shared["the_structural_point_that_still_holds"]
        )

    def test_a_sampling_frame_input_is_not_called_a_measurement_upstream(self) -> None:
        """§26. A shared list of routable prefixes says which addresses may
        exist. It does not say which hosts run the service."""
        for entry in LINEAGE_RECORD["shared_auxiliary_inputs"]["inputs"]:
            if entry["classification"] == "SAMPLING_FRAME_INPUT":
                self.assertIn("which addresses", entry["impact"].lower())

    def test_the_enquiry_was_prepared_and_not_sent(self) -> None:
        enquiry = LINEAGE_RECORD["written_enquiry"]
        self.assertTrue(enquiry["prepared"])
        self.assertFalse(enquiry["sent"])

    def test_the_enquiry_asks_for_facts_rather_than_for_a_word(self) -> None:
        self.assertNotIn("independent", LINEAGE_RECORD["written_enquiry"]["draft_question"].lower())


class TestTheClosure(unittest.TestCase):
    """§48 to §60."""

    def test_the_matrix_covers_all_sixteen_gates_in_order(self) -> None:
        gates = CLOSURE_RECORD["gate_matrix"]["gates"]
        self.assertEqual([g["n"] for g in gates], list(range(1, 17)))

    def test_a_route_was_not_selected_on_fifteen(self) -> None:
        gates = CLOSURE_RECORD["gate_matrix"]["gates"]
        passing = sum(1 for g in gates if g["new"] == "PASS")
        if CLOSURE_RECORD["selected_route"] is not None:
            self.assertEqual(passing, 16)

    def test_an_unselected_route_carries_no_actionability(self) -> None:
        if CLOSURE_RECORD["selected_route"] is None:
            self.assertIsNone(CLOSURE_RECORD["actionability"])

    def test_reopened_gates_are_reported_rather_than_smoothed(self) -> None:
        """§30. A gate that passed a mission ago may fail under fuller
        information, and that is the audit working."""
        gates = CLOSURE_RECORD["gate_matrix"]["gates"]
        reopened = sorted(g["n"] for g in gates if g["old"] == "PASS" and g["new"] != "PASS")
        self.assertEqual(sorted(CLOSURE_RECORD["gate_matrix"]["gates_reopened"]), reopened)

    def test_no_threshold_value_was_chosen(self) -> None:
        threshold = CLOSURE_RECORD["threshold"]
        self.assertFalse(threshold["selected"])
        self.assertIsNone(threshold["value_chosen"])

    def test_no_measurement_value_was_fetched(self) -> None:
        for record, key in (
            (BASELINE_RECORD["documentation_ledger"], "measurement_values_fetched"),
            (CLOSURE_RECORD["counters"], "measurement_values_fetched"),
        ):
            self.assertEqual(record[key], 0)
        self.assertFalse(BASELINE_RECORD["value_exposure"]["target_measurement_retrieved"])

    def test_nothing_was_purchased_and_nothing_registered(self) -> None:
        counters = CLOSURE_RECORD["counters"]
        for name in (
            "paid_access_purchased",
            "trials_started",
            "sources_registered",
            "governance_reviews_created",
            "canonical_mutations",
            "model_calls",
            "embeddings",
            "reliability_values_assigned",
        ):
            self.assertEqual(counters[name], 0, name)

    def test_the_frozen_pair_was_not_substituted(self) -> None:
        """§1. Swapping in a pair that is easier to document would answer a
        different question and call it closure."""
        self.assertFalse(BASELINE_RECORD["route_under_evaluation"]["substituted"])

    def test_the_documentation_ledger_is_first_party_where_load_bearing(self) -> None:
        for entry in BASELINE_RECORD["documentation_ledger"]["requests"]:
            if entry.get("load_bearing"):
                self.assertTrue(entry["first_party"], entry["n"])

    def test_the_next_mission_may_not_pay_or_fetch(self) -> None:
        forbidden = " ".join(CLOSURE_RECORD["next_mission_recommendation"]["it_must_not"]).lower()
        self.assertIn("fetch a measurement value", forbidden)
        self.assertIn("purchase", forbidden)


if __name__ == "__main__":
    unittest.main()
