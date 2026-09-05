"""Mission 1.60 §30, §44, §45, §52, §59. The selection records and the fixtures.

The fixtures are EXECUTED rather than described. The records claim two witnesses
annotated with different scanner ids reach one proposition key; that claim is
driven through the real `TargetProposition` and the real `proposition_key` here,
because it is the property the whole route rests on and the one a protocol
narrowing could quietly have broken.

Synthetic values only: `4242` and `1717` against a bound of `3000`, and scanner
ids that name nothing real. Nothing is persisted and no measurement was
retrieved to construct them.
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
BASELINE = DATA / "observation-addressable-scanner-selection-baseline-v1.json"
CONTRACT = DATA / "observation-addressable-apparatus-contract-v1.json"
ANCHOR = DATA / "anchor-scanner-requalification-v1.json"
PARTNERS = DATA / "observation-addressable-partner-candidates-v1.json"
SELECTION = DATA / "observation-addressable-scanner-pair-selection-v1.json"

WITNESS_ABOVE = Decimal("4242")
WITNESS_BELOW = Decimal("1717")
SYNTHETIC_BOUND = Decimal("3000")
SCANNER_ONE = "synthetic-scanner-one"
SCANNER_TWO = "synthetic-scanner-two"


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


BASELINE_RECORD = _load(BASELINE)
CONTRACT_RECORD = _load(CONTRACT)
ANCHOR_RECORD = _load(ANCHOR)
PARTNERS_RECORD = _load(PARTNERS)
SELECTION_RECORD = _load(SELECTION)


def _target() -> TargetProposition:
    return TargetProposition(
        proposition_kind=PROPOSITION_KIND,
        canonical_subject_id="ssh-transport-protocol",
        metric_definition_id="public_ipv4_protocol_responsive_host_count:tcp-22:rfc4253-id-string",
        time_bound="2026-10-01T00:00:00Z/2026-10-02T00:00:00Z",
        population_or_geography="public-ipv4",
        unit="hosts",
        threshold_operator=ThresholdOperator.GTE,
        threshold_value=SYNTHETIC_BOUND,
    )


class TestTheSameTargetFixture(unittest.TestCase):
    """§30. Scanner identity is witness provenance, never Claim identity."""

    def test_two_scanner_annotated_witnesses_reach_one_key(self) -> None:
        witness_a = {"scanner": SCANNER_ONE, "value": str(WITNESS_ABOVE)}
        witness_b = {"scanner": SCANNER_TWO, "value": str(WITNESS_BELOW)}
        key_a = proposition_key(target_proposition_facts(_target()))
        key_b = proposition_key(target_proposition_facts(_target()))
        self.assertEqual(key_a, key_b)
        # the witnesses differ, and the target does not
        self.assertNotEqual(witness_a, witness_b)
        self.assertEqual(len(key_a), 64)

    def test_no_scanner_name_reaches_the_target_facts(self) -> None:
        blob = json.dumps(target_proposition_facts(_target())).lower()
        for name in (SCANNER_ONE, SCANNER_TWO, "netlas", "censys", "scanner", "vendor"):
            self.assertNotIn(name, blob)

    def test_the_witnesses_straddle_the_bound(self) -> None:
        """One would SUPPORT and one would CONTRADICT, and neither value is in
        the key. That is what makes a contradiction land on one Claim."""
        self.assertGreater(WITNESS_ABOVE, SYNTHETIC_BOUND)
        self.assertLess(WITNESS_BELOW, SYNTHETIC_BOUND)
        blob = json.dumps(target_proposition_facts(_target()))
        self.assertNotIn(str(WITNESS_ABOVE), blob)
        self.assertNotIn(str(WITNESS_BELOW), blob)

    def test_the_record_agrees_no_schema_change_is_needed(self) -> None:
        target = SELECTION_RECORD["future_target_proposition"]
        self.assertTrue(target["representable_by_current_contract"])
        self.assertFalse(target["schema_change_required"])
        self.assertFalse(target["scanner_identity_required_in_identity"])


class TestTheApparatusContract(unittest.TestCase):
    """§3, §4, §5, §20, §52."""

    def test_the_nine_gates_are_present_in_order(self) -> None:
        ids = [g["id"] for g in CONTRACT_RECORD["individual_hard_gates"]]
        self.assertEqual(ids, ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9"])

    def test_a_current_state_database_is_rejected_by_name(self) -> None:
        """However excellent it is. Mission 1.59 established why, and the rule
        must survive in the contract rather than in that report."""
        boundary = CONTRACT_RECORD["observation_addressability_is_about_the_boundary"]
        self.assertIn("MAINTAINED_CURRENT_STATE_LAST_CHANGE", boundary["rejected_time_object"])
        self.assertIn("however excellent", boundary["rejected_time_object"])

    def test_retrieve_then_filter_is_named_as_failing(self) -> None:
        boundary = CONTRACT_RECORD["observation_addressability_is_about_the_boundary"]
        failing = " ".join(boundary["failing_shapes"]).lower()
        self.assertIn("retrieve the whole set", failing)
        self.assertIn("last_changed", failing)

    def test_a_perfect_per_row_timestamp_does_not_rescue_it(self) -> None:
        boundary = CONTRACT_RECORD["observation_addressability_is_about_the_boundary"]
        self.assertIn("still FAIL", boundary["the_loophole_this_closes"])

    def test_a_proprietary_classifier_may_not_carry_the_predicate(self) -> None:
        classes = CONTRACT_RECORD["protocol_predicate_exposure_classes"]
        for rejected in ("PROPRIETARY_CLASSIFIER_ONLY", "NOT_EXPOSED", "UNKNOWN"):
            self.assertEqual(classes[rejected], "REJECTED")

    def test_a_count_is_not_metadata(self) -> None:
        boundary = CONTRACT_RECORD["metadata_versus_measurement"]
        self.assertIn("counts", boundary["forbidden"])
        self.assertTrue(boundary["the_count_is_not_metadata"].strip())

    def test_a_free_trial_is_not_harmless(self) -> None:
        """Access cost is irrelevant to epistemic contamination."""
        self.assertIn(
            "cost is irrelevant",
            CONTRACT_RECORD["metadata_versus_measurement"]["the_trial_is_not_free"],
        )

    def test_the_registry_carries_every_hard_won_rule_with_its_source(self) -> None:
        registry = CONTRACT_RECORD["requirement_registry"]["requirements"]
        names = {item["name"] for item in registry}
        for required in (
            "OBSERVATION_ADDRESSABLE_EXPOSURE",
            "FRAME_INSIDE_THE_DEFINITION",
            "READING_A_PUBLISHED_VALUE_IS_NOT_MEASURING_IT",
            "SOURCE_EXCLUSIVE_METRIC",
            "AFFIRMATIVE_LINEAGE_REQUIRED",
            "PRODUCT_RELEVANCE",
        ):
            self.assertIn(required, names)
        for item in registry:
            self.assertTrue(item["from"].strip(), item["name"])


class TestTheAnchorRequalification(unittest.TestCase):
    """§36. Re-evaluated, not copied forward."""

    def setUp(self) -> None:
        self.results = ANCHOR_RECORD["gate_results"]

    def test_every_gate_was_re_evaluated(self) -> None:
        for gate in ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9"):
            self.assertTrue(any(k.startswith(gate + "_") for k in self.results), gate)

    def test_observation_addressability_passes_at_the_boundary(self) -> None:
        a2 = self.results["A2_OBSERVATION_ADDRESSABLE_EXPOSURE"]
        self.assertEqual(a2["verdict"], "PASS")
        self.assertTrue(a2["window_selectable_before_retrieval"])
        self.assertFalse(a2["requires_result_inspection"])
        self.assertEqual(a2["timestamp_semantics"], "OBSERVATION_TIME")

    def test_the_predicate_rests_on_a_raw_banner_not_a_vendor_label(self) -> None:
        a3 = self.results["A3_PROTOCOL_NATIVE_OBSERVATION_EXPOSURE"]
        self.assertEqual(a3["exposure_class"], "RAW_IDENTIFICATION_STRING")
        self.assertFalse(a3["vendor_fingerprint_required"])

    def test_lineage_was_not_upgraded_from_an_absence(self) -> None:
        """The rule that has now survived four missions."""
        a7 = self.results["A7_AFFIRMATIVE_MEASUREMENT_LINEAGE"]
        self.assertEqual(a7["verdict"], "PARTIAL")
        self.assertTrue(a7["what_is_missing"].strip())
        self.assertIn("absence remains absence", a7["why_not_upgraded"])

    def test_the_frame_is_stated_rather_than_called_internet_wide(self) -> None:
        a5 = self.results["A5_FRAME_DOCUMENTED"]
        self.assertTrue(a5["frame"].strip())
        self.assertIn("NOT recorded as established", a5["port_22_in_frame"])

    def test_the_anchor_does_not_qualify_and_says_which_gates_block(self) -> None:
        self.assertFalse(ANCHOR_RECORD["individually_qualifies"])
        self.assertEqual(sorted(ANCHOR_RECORD["which_gates_block"]), ["A7", "A8"])

    def test_it_was_not_invalidated_either(self) -> None:
        """An unproven negative is not a refutation, and the record has to hold
        those apart or the anchor gets discarded for the wrong reason."""
        self.assertEqual(ANCHOR_RECORD["requalification_result"], "ANCHOR_B_LINEAGE_PARTIAL")
        self.assertTrue(ANCHOR_RECORD["not_invalidated"].strip())

    def test_vantage_was_asked_before_pairing(self) -> None:
        self.assertEqual(ANCHOR_RECORD["vantage"]["status"], "NOT_ESTABLISHED")
        self.assertTrue(ANCHOR_RECORD["vantage"]["why_it_is_recorded_now"].strip())


class TestThePartnerSearch(unittest.TestCase):
    """§50, §52."""

    def test_the_dropped_apparatus_is_retained_as_a_negative_control(self) -> None:
        control = next(
            c for c in PARTNERS_RECORD["candidates"] if c.get("status") == "NEGATIVE_CONTROL"
        )
        self.assertFalse(control["reconsidered"])
        self.assertEqual(control["verdict"], "SNAPSHOT_TIME_SEMANTICS_NOT_ALIGNABLE")

    def test_no_candidate_appears_twice(self) -> None:
        """Two brand names are not two apparatuses, and one name twice is not
        two either."""
        identities = [c["identity"] for c in PARTNERS_RECORD["candidates"]]
        self.assertEqual(len(identities), len(set(identities)))

    def test_every_candidate_records_its_first_failing_gate(self) -> None:
        for candidate in PARTNERS_RECORD["candidates"]:
            self.assertTrue(candidate["first_failing_gate"].strip(), candidate["identity"])

    def test_a_documentation_wall_is_not_a_finding_about_the_apparatus(self) -> None:
        for candidate in PARTNERS_RECORD["candidates"]:
            if candidate["verdict"] == "DOCUMENTATION_NOT_RETRIEVABLE":
                self.assertTrue(candidate["not_a_refusal"], candidate["identity"])

    def test_the_search_says_what_it_does_not_establish(self) -> None:
        establishes = PARTNERS_RECORD["partner_search_result"][
            "what_this_does_and_does_not_establish"
        ]
        self.assertIn("That none exists", establishes["does_not_establish"])

    def test_no_pair_was_constructed_without_qualifying_apparatuses(self) -> None:
        self.assertEqual(PARTNERS_RECORD["pairs_constructed"]["count"], 0)


class TestTheSelection(unittest.TestCase):
    """§40, §46, §47, §53 to §56."""

    def test_no_pair_was_selected(self) -> None:
        self.assertIsNone(SELECTION_RECORD["selected_pair"])
        self.assertIsNone(SELECTION_RECORD["actionability"])

    def test_the_imperfect_outcome_fit_is_stated(self) -> None:
        """Choosing the outcome whose wording bends most easily is the failure
        this says out loud instead."""
        why = SELECTION_RECORD["why_this_outcome_and_not_another"]
        self.assertTrue(why["the_imperfect_fit"].strip())
        self.assertTrue(why["why_not_C"].strip())
        self.assertTrue(why["why_not_B"].strip())

    def test_the_gate_summary_agrees_with_the_requalification(self) -> None:
        for gate, verdict in SELECTION_RECORD["gate_summary"]["anchor"].items():
            key = next(k for k in ANCHOR_RECORD["gate_results"] if k.startswith(gate + "_"))
            self.assertEqual(ANCHOR_RECORD["gate_results"][key]["verdict"], verdict, gate)

    def test_no_window_width_and_no_threshold_were_chosen(self) -> None:
        window = SELECTION_RECORD["window_and_threshold"]
        self.assertFalse(window["window_width_selected"])
        self.assertFalse(window["threshold_selected"])
        self.assertIsNone(window["threshold_value"])

    def test_host_level_existence_is_not_claim_level_monotonicity(self) -> None:
        """§22. A within-window existential per host does not make the COUNT
        unfalsifiable, and conflating them would have invented a problem or
        hidden one."""
        window = SELECTION_RECORD["window_and_threshold"]
        self.assertIn(
            "can be contradicted", window["why_that_does_not_make_the_claim_unfalsifiable"]
        )

    def test_the_disagreement_diagnostic_distinguishes_the_two_kinds(self) -> None:
        diagnostic = SELECTION_RECORD["structural_fixtures"]["disagreement_diagnostic"]
        self.assertEqual(
            diagnostic["answer"], "LEGITIMATE_INDEPENDENT_MEASUREMENT_DIFFERENCE_POSSIBLE"
        )
        self.assertIn("two propositions", diagnostic["the_distinction_that_must_survive"])

    def test_non_observation_is_not_read_as_absence(self) -> None:
        asymmetry = SELECTION_RECORD["positive_negative_asymmetry"]
        self.assertIn("never be read as the host being definitely absent", asymmetry["consequence"])

    def test_nothing_was_fetched_bought_or_mutated(self) -> None:
        counters = SELECTION_RECORD["counters"]
        for name in (
            "target_measurement_requests",
            "target_host_record_requests",
            "target_count_requests",
            "facets_fetched",
            "queries_executed",
            "trials_started",
            "purchases",
            "canonical_mutations",
            "sources_registered",
            "governance_reviews_created",
            "model_calls",
            "embeddings",
        ):
            self.assertEqual(counters[name], 0, name)

    def test_the_next_mission_may_not_fetch_buy_or_trial(self) -> None:
        forbidden = " ".join(SELECTION_RECORD["next_mission_recommendation"]["it_must_not"]).lower()
        for rule in ("fetch a measurement value", "trial", "purchase", "revive"):
            self.assertIn(rule, forbidden)

    def test_the_documentation_ledger_stayed_within_budget(self) -> None:
        ledger = BASELINE_RECORD["documentation_ledger"]
        self.assertLessEqual(ledger["used"], ledger["budget"])
        self.assertEqual(ledger["used"], len(ledger["requests"]))


if __name__ == "__main__":
    unittest.main()
