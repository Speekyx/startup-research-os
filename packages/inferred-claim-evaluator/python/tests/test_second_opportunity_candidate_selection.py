"""Mission 1.80. Which held subject is the second-Opportunity candidate, and why none is.

Four things this file defends.

THE UNIVERSE IS THE HELD PACKETS. Nine non-docker packets, each with the rows, scorable
count, dimensions, reliabilities, formability and egress the preparation gives it; nothing
merged, nothing narrowed, docker excluded.

A NOTICE VALUE IS NOT COMMERCE AND A CATEGORY IS NOT A PRODUCT. Procurement semantics are
recorded as boundaries, the CPV division stays a CATEGORY at TOO_BROAD grain, and no
candidate establishes demand.

THE BEST PACKET IS NOT THE BEST CANDIDATE. Division 92 is the best held evidence packet, the
frontier is what the stated dominance rule produces, every candidate is vetoed, and the
outcome is subject narrowing over held data with no egress decision taken.

NOTHING MOVED. One Opportunity at revision 2, zero mission accounting, the parked arc intact.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

SELECTION = DATA / "second-opportunity-candidate-selection-v1.json"
PREPARATION = DATA / "opportunity-preparation-v2.json"
RECONCILIATION = DATA / "opportunity-reliability-reconciliation-v1.json"
GATE = SCRIPTS / "render_second_opportunity_candidate_selection.py"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"

T92 = "ted-eu:CPV-division:92"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location(
        "render_second_opportunity_candidate_selection", GATE
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTheUniverse(unittest.TestCase):
    def setUp(self):
        self.record = load(SELECTION)
        self.preparation = load(PREPARATION)
        self.candidates = {c["subject_key"]: c for c in self.record["candidates"]}

    def test_nine_non_docker_packets_and_docker_excluded(self):
        packets = {p["subject"]: p for p in self.preparation["packets"]}
        self.assertEqual(set(self.candidates), set(packets) - {"subject:docker"})
        self.assertEqual(self.record["candidate_universe"]["count"], 9)
        self.assertEqual(
            [e["subject"] for e in self.record["candidate_universe"]["excluded"]],
            ["subject:docker"],
        )

    def test_every_candidate_carries_its_packets_facts(self):
        packets = {p["subject"]: p for p in self.preparation["packets"]}
        for subject, c in self.candidates.items():
            p = packets[subject]
            self.assertEqual(c["packet_id"], p["packet_id"])
            self.assertEqual(c["evidence_rows"], p["size"])
            self.assertEqual(c["scorable_rows"], p["eligibility_counts"].get("ELIGIBLE_SCORING", 0))
            self.assertEqual(sorted(c["counting_dimensions"]), sorted(p["counting_dimensions"]))
            self.assertEqual(c["egress_state"], p["external_synthesis"]["availability"])
            self.assertEqual(
                c["hypothesis_formable"], p["sufficiency"]["status"] == "HYPOTHESIS_FORMABLE"
            )

    def test_no_subject_is_merged_and_none_is_narrowed(self):
        for subject in self.candidates:
            self.assertNotIn("+", subject)
            self.assertNotIn("CPV-class", subject)

    def test_division_92_is_ten_rows_at_two_reviewed_reliabilities(self):
        c = self.candidates[T92]
        self.assertEqual(c["evidence_rows"], 10)
        self.assertEqual(c["scorable_rows"], 10)
        self.assertEqual(c["reliability_distribution"], {"0.5": 5, "0.55": 5})
        self.assertEqual(
            sorted(c["counting_dimensions"]),
            ["BUYER_OR_BUDGET_EXISTENCE", "ECONOMIC_VALUE", "MARKET_ACTIVITY"],
        )
        self.assertTrue(c["hypothesis_formable"])
        self.assertEqual(c["independence_state"], "UNKNOWN")


class TestProcurementAndGrain(unittest.TestCase):
    def setUp(self):
        self.record = load(SELECTION)
        self.candidates = {c["subject_key"]: c for c in self.record["candidates"]}

    def test_a_notice_value_is_not_spend_or_willingness_to_pay(self):
        for key in (T92, "ted-eu:CPV-division:90"):
            sem = self.candidates[key]["procurement_semantics"]
            self.assertFalse(sem["value_is_realised_spend"])
            self.assertFalse(sem["value_is_willingness_to_pay"])
            self.assertFalse(sem["authority_is_buyer_for_unspecified_product"])
            self.assertNotIn("WILLINGNESS_TO_PAY", self.candidates[key]["counting_dimensions"])

    def test_no_candidate_establishes_product_demand(self):
        for c in self.candidates.values():
            self.assertFalse(c["establishes_product_demand"])

    def test_a_category_is_not_a_product(self):
        c = self.candidates[T92]
        self.assertEqual(c["subject_scope"], "CATEGORY")
        self.assertEqual(c["subject_type"], "CATEGORY")
        self.assertEqual(c["product_intervention_grain"], "TOO_BROAD_TO_BE_ACTIONABLE")
        self.assertEqual(c["actionable_grain"], "REQUIRES_NARROWER_SUBJECT_DISCOVERY")
        self.assertFalse(c["exploratory_category_hypothesis"]["adopted"])
        self.assertGreaterEqual(len(c["held_class_distribution"]["top_cpv_classes"]), 6)

    def test_publication_and_population_carry_no_dimension(self):
        for key, c in self.candidates.items():
            if key.startswith(("gdelt:", "world-bank:")):
                self.assertEqual(c["counting_dimensions"], [])
                self.assertEqual(c["actionable_grain"], "NOT_ACTIONABLE")

    def test_kubernetes_and_podman_are_the_docker_shape_minus_a_dimension(self):
        for key in ("subject:kubernetes", "subject:podman"):
            c = self.candidates[key]
            self.assertEqual(c["counting_dimensions"], ["AUDIENCE_OR_USAGE"])
            self.assertFalse(c["hypothesis_formable"])
            self.assertEqual(c["veto_state"], "VETOED")


class TestDominanceAndOutcome(unittest.TestCase):
    def setUp(self):
        self.record = load(SELECTION)
        self.candidates = {c["subject_key"]: c for c in self.record["candidates"]}

    def test_the_frontier_is_what_the_rule_produces(self):
        module = gate()
        fields = self.record["dominance"]["fields"]
        dominated = {
            s
            for s in self.candidates
            for t in self.candidates
            if t != s and module._dominates(self.candidates[t], self.candidates[s], fields)
        }
        self.assertEqual(
            sorted(self.record["dominance"]["PARETO_FRONTIER"]),
            sorted(set(self.candidates) - dominated),
        )
        self.assertIn("SEMANTIC_SPECIFICITY", fields)
        self.assertIn(T92, self.record["dominance"]["PARETO_FRONTIER"])

    def test_every_candidate_is_vetoed_with_a_reason_and_none_for_egress_alone(self):
        for c in self.candidates.values():
            self.assertEqual(c["veto_state"], "VETOED")
            self.assertTrue(c["veto_reason"].strip())
        self.assertNotIn("egress", self.candidates[T92]["veto_reason"].lower())

    def test_best_packet_is_not_best_candidate(self):
        self.assertEqual(self.record["best_held_evidence_packet"], T92)
        self.assertIsNone(self.record["best_second_opportunity_candidate"])
        self.assertIsNone(self.record["selected_subject"])
        self.assertIsNone(self.record["selected_packet_id"])
        self.assertTrue(self.record["why_they_differ"].strip())

    def test_the_outcome_is_subject_narrowing_over_held_data(self):
        self.assertEqual(
            self.record["primary_outcome"], "SECOND_OPPORTUNITY_REQUIRES_SUBJECT_NARROWING"
        )
        narrowing = self.record["narrowing"]
        self.assertEqual(narrowing["dominant_category"], T92)
        self.assertFalse(narrowing["acquisition_required"])
        self.assertNotIn("egress review", self.record["recommended_next_mission"]["title"].lower())
        self.assertIn("acquire", " ".join(self.record["recommended_next_mission"]["must_not"]))

    def test_egress_is_required_before_synthesis_and_not_decided(self):
        egress = self.record["egress"]
        self.assertTrue(egress["EGRESS_REVIEW_REQUIRED_BEFORE_SYNTHESIS"])
        for key in ("decided_here", "granted", "denied", "source_review_appended"):
            self.assertFalse(egress[key])
        for key in (T92, "ted-eu:CPV-division:90"):
            self.assertFalse(self.candidates[key]["egress_eligible"])
            self.assertTrue(self.candidates[key]["egress_review_required_before_synthesis"])

    def test_representation_was_checked_in_memory_and_sent_nowhere(self):
        rep = self.record["representation_check"]
        self.assertFalse(rep["transmitted"])
        self.assertFalse(rep["model_called"])
        for entry in rep["packets"].values():
            self.assertEqual(entry["violations"], 0)

    def test_no_numeric_priority_anywhere(self):
        for c in self.candidates.values():
            for key, value in c.items():
                if any(k in key.lower() for k in ("score", "weighted", "points", "rank")):
                    self.assertNotIsInstance(value, int | float, key)


class TestNothingMoved(unittest.TestCase):
    def setUp(self):
        self.record = load(SELECTION)
        self.reconciliation = load(RECONCILIATION)

    def test_counters_match_the_reconciled_deployment(self):
        after = self.reconciliation["counters"]["after"]
        state = self.record["current_state"]
        self.assertEqual(state["opportunities"], 1)
        self.assertEqual(state["opportunity_revisions"], after["opportunity_revisions"])
        self.assertEqual(state["opportunity_evidence_links"], after["opportunity_evidence_links"])
        self.assertEqual(state["reliability_assessments"], after["reliability_assessments"])
        self.assertEqual(state["independence_groups"], 0)
        self.assertEqual(state["scores_table"], "ABSENT")
        self.assertEqual(
            state["current_revision_id"], self.reconciliation["revision_2_applied"]["revision_2_id"]
        )

    def test_mission_accounting_is_zero(self):
        self.assertEqual({v for v in self.record["mission_accounting"].values()}, {0})

    def test_the_parked_arc_is_preserved(self):
        parked = self.record["parked_states_preserved"]
        self.assertFalse(parked["changed_by_this_mission"])
        self.assertTrue(parked["q1"]["CLASS_SELECTED"])
        self.assertFalse(parked["q1"]["CONSTRUCT_SELECTED"])
        self.assertEqual(parked["globalping"]["PASS"], 12)


class TestTheGate(unittest.TestCase):
    def test_the_gate_validates_and_renders_the_shipped_record(self):
        module = gate()
        record, _, _ = module.validate()
        rendered = (DATA / "second-opportunity-candidate-selection-v1.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(module.render(record), rendered)

    def test_the_gate_is_registered_in_ci(self):
        text = CI.read_text(encoding="utf-8")
        self.assertIn("render_second_opportunity_candidate_selection.py --check", text)


if __name__ == "__main__":
    unittest.main()
