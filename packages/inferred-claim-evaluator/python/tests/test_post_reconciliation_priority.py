"""Mission 1.79. What is the next bounded move, and why is it not the leftover row.

Four things this file defends.

SIX SCORABLE ROWS ARE ONE SHAPE. One source, one family, one counting dimension, one
provenance shape; scoring-ready is a packet property and none of calibrated, authorised,
independent or validated.

A DIMENSION IS SUPPORTED BY A ROW OR IT IS NOT SUPPORTED. A question count supports nothing
about recurrence or severity, and TED's commercial rows belong to other subjects.

A CANDIDATE DOES NOT WIN BY BEING EASY OR BY BEING LEFT OVER. The winner is on the recomputed
frontier and carries no veto; the Stack Exchange bottleneck is BOTH, and adding rows to a
saturated shape is vetoed.

THE FIRST OPPORTUNITY IS NOT ENTITLED TO THE BUDGET. Its marginal value is recorded LOW on
stated grounds, sunk effort counts for nothing, and the parked arc did not move.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

PRIORITY = DATA / "post-reconciliation-evidence-priority-v1.json"
RECONCILIATION = DATA / "opportunity-reliability-reconciliation-v1.json"
PREPARATION = DATA / "opportunity-preparation-v2.json"
GATE = SCRIPTS / "render_post_reconciliation_priority.py"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location("render_post_reconciliation_priority", GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTheScorableShape(unittest.TestCase):
    def setUp(self):
        self.record = load(PRIORITY)
        self.reconciliation = load(RECONCILIATION)

    def test_the_seven_described_rows_are_revision_twos_links(self):
        written = {
            link["evidence_id"]
            for link in self.reconciliation["revision_2_applied"]["links_written"]
        }
        described = {row["evidence_id"] for row in self.record["current_linked_evidence"]}
        self.assertEqual(described, written)
        self.assertEqual(len(described), 7)

    def test_six_scorable_rows_are_one_shape(self):
        shape = self.record["scorable_shape"]
        self.assertEqual(shape["SCORABLE_ROWS"], 6)
        self.assertEqual(shape["SCORABLE_SOURCES"], 1)
        self.assertEqual(shape["SCORABLE_SOURCE_FAMILIES"], 1)
        self.assertEqual(shape["SCORABLE_COUNTING_DIMENSIONS"], 1)
        self.assertEqual(shape["SCORABLE_PROVENANCE_GROUPS"], 1)
        self.assertFalse(shape["SCORABLE_DIMENSION_DIVERSITY"])

    def test_scoring_ready_is_kept_apart_from_everything_it_is_not(self):
        flags = self.record["scoring_ready_is_not_production_scoring"]
        self.assertTrue(flags["PACKET_SCORING_READY"])
        for key in (
            "AGGREGATION_PROFILE_CALIBRATED",
            "PERSISTED_SCORING_AUTHORIZED",
            "INDEPENDENCE_ESTABLISHED",
            "COMMERCIAL_VALIDATION_ESTABLISHED",
        ):
            self.assertFalse(flags[key], key)

    def test_every_row_says_what_it_does_not_establish(self):
        for row in self.record["current_linked_evidence"]:
            self.assertTrue(row["does_not_establish"].strip())
            self.assertEqual(row["independence_state"], "UNKNOWN")


class TestTheDimensionMatrix(unittest.TestCase):
    def setUp(self):
        self.matrix = load(PRIORITY)["dimension_matrix"]

    def test_only_audience_and_trend_are_scorable_and_problem_is_context(self):
        self.assertEqual(
            sorted(self.matrix["supported_scorable"]), ["AUDIENCE_OR_USAGE", "TREND_OR_CHANGE"]
        )
        self.assertEqual(self.matrix["supported_context_only"], ["PROBLEM_OR_NEED"])

    def test_recurrence_and_solution_gap_are_inferences_not_support(self):
        by_name = {e["dimension"].split(" ")[0]: e["classification"] for e in self.matrix["rows"]}
        self.assertEqual(by_name["RECURRENCE_OR_FREQUENCY"], "UNSUPPORTED_INFERENCE")
        self.assertEqual(by_name["SOLUTION_GAP"], "UNSUPPORTED_INFERENCE")
        self.assertEqual(by_name["WILLINGNESS_TO_PAY"], "ABSENT")
        self.assertEqual(by_name["MARKET_ACTIVITY"], "ABSENT")


class TestTheCandidates(unittest.TestCase):
    def setUp(self):
        self.record = load(PRIORITY)
        self.candidates = {c["candidate_id"]: c for c in self.record["candidates"]}

    def test_all_six_candidates_are_evaluated(self):
        self.assertEqual(
            sorted(self.candidates),
            [
                "M1_STACK_EXCHANGE_RELIABILITY",
                "M2_PROBLEM_STRENGTH",
                "M3_COMMERCIAL_BUYER_WTP",
                "M4_HELD_UNUSED_EVIDENCE",
                "M5_Q1_INDEPENDENCE",
                "M6_SECOND_OPPORTUNITY",
            ],
        )

    def test_the_stack_exchange_bottleneck_is_both_and_it_does_not_win(self):
        test = self.record["special_tests"]["stack_exchange"]
        self.assertEqual(test["D_bottleneck"], "BOTH")
        self.assertFalse(test["remaining_non_scorable_row_implies_next_fix"])
        self.assertFalse(
            test[
                "C_changes_the_product_decision_more_than_a_commercial_or_problem_strength_dimension"
            ]
        )
        m1 = self.candidates["M1_STACK_EXCHANGE_RELIABILITY"]
        self.assertEqual(m1["dominance_result"], "VETOED")
        self.assertTrue(m1["new_human_review_required"])
        self.assertNotIn("0.", json.dumps(m1.get("recommended_reliability", "")))

    def test_ted_is_not_attached_to_docker(self):
        m3 = self.candidates["M3_COMMERCIAL_BUYER_WTP"]
        self.assertFalse(m3["held_subject_matched_commercial_evidence"])
        self.assertFalse(m3["ted_attached_to_docker"])
        self.assertFalse(m3["cross_subject_transfer_used"])

    def test_more_wikimedia_is_dominated_and_the_uncited_rows_add_nothing(self):
        self.assertTrue(
            self.record["special_tests"]["wikimedia_saturation"]["more_wikimedia_dominated"]
        )
        m4 = self.candidates["M4_HELD_UNUSED_EVIDENCE"]
        self.assertEqual(m4["dominance_result"], "VETOED")
        for row in m4["rows"]:
            self.assertFalse(row["new_dimension"])
            self.assertFalse(row["new_provenance"])
            self.assertTrue(row["human_judgement_required"])

    def test_q1_stays_parked_and_qualification_is_not_independence(self):
        m5 = self.candidates["M5_Q1_INDEPENDENCE"]
        self.assertEqual(m5["status"], "PARKED")
        self.assertFalse(m5["deciding_predicate_emerged"])
        self.assertFalse(m5["globalping_qualification_solves_independence"])
        self.assertNotEqual(m5["independence_gain"], "ESTABLISHED_IF_EXECUTED")

    def test_the_winner_is_the_second_opportunity_on_the_frontier_without_a_veto(self):
        self.assertEqual(self.record["selected_next_move"], "M6_SECOND_OPPORTUNITY")
        self.assertEqual(
            self.record["primary_outcome"], "SECOND_OPPORTUNITY_EXPLORATION_IS_NEXT_BOUNDED_MOVE"
        )
        m6 = self.candidates["M6_SECOND_OPPORTUNITY"]
        self.assertEqual(m6["dominance_result"], "SELECTED")
        self.assertEqual(m6["veto_reason"], "")
        self.assertEqual(m6["status"], "EXECUTABLE_NOW_HELD_DATA_ONLY")
        self.assertTrue(m6["not_selected_for_row_count"])
        self.assertIn("M6_SECOND_OPPORTUNITY", self.record["dominance"]["PARETO_FRONTIER"])
        self.assertIn("M3_COMMERCIAL_BUYER_WTP", self.record["dominance"]["PARETO_FRONTIER"])
        leading = [c for c in m6["held_candidates"] if c["verdict"] == "LEADING"]
        self.assertEqual([c["subject"] for c in leading], ["ted-eu:CPV-division:92"])

    def test_the_first_opportunity_is_at_diminishing_returns_and_sunk_effort_counts_for_nothing(
        self,
    ):
        second = self.record["special_tests"]["second_opportunity"]
        self.assertEqual(second["CURRENT_OPPORTUNITY_MARGINAL_INFORMATION_VALUE"], "LOW")
        self.assertEqual(second["SECOND_OPPORTUNITY_EXPLORATION_VALUE"], "MEDIUM")
        self.assertTrue(second["diminishing_returns"])
        self.assertFalse(second["sunk_effort_counted_as_value"])

    def test_no_candidate_carries_a_numeric_score(self):
        for c in self.record["candidates"]:
            for key, value in c.items():
                if isinstance(value, int | float) and not isinstance(value, bool):
                    self.fail(f"{c['candidate_id']}.{key} is a number")

    def test_mission_accounting_is_zero(self):
        self.assertEqual({k: v for k, v in self.record["mission_accounting"].items() if v}, {})


class TestTheGate(unittest.TestCase):
    def setUp(self):
        self.gate = gate()
        self.record, self.reconciliation, self.preparation = self.gate.validate()

    def test_six_rows_read_as_six_observations_is_refused(self):
        record = copy.deepcopy(self.record)
        record["scorable_shape"]["SCORABLE_PROVENANCE_GROUPS"] = 6
        rows = self.gate._linked_rows(record, self.reconciliation, self.preparation)
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_the_scorable_shape(record, rows, self.reconciliation)

    def test_scoring_ready_read_as_calibrated_is_refused(self):
        record = copy.deepcopy(self.record)
        record["scoring_ready_is_not_production_scoring"]["AGGREGATION_PROFILE_CALIBRATED"] = True
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_scoring_ready_is_not_scoring(
                record, self.reconciliation, self.preparation
            )

    def test_a_question_count_read_as_recurrence_is_refused(self):
        record = copy.deepcopy(self.record)
        entry = next(
            e
            for e in record["dimension_matrix"]["rows"]
            if e["dimension"] == "RECURRENCE_OR_FREQUENCY"
        )
        entry["classification"] = "SUPPORTED_CONTEXT_ONLY"
        record["dimension_matrix"]["supported_context_only"].append("RECURRENCE_OR_FREQUENCY")
        rows = self.gate._linked_rows(record, self.reconciliation, self.preparation)
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_the_dimension_matrix(record, rows)

    def test_stack_exchange_winning_as_the_leftover_row_is_refused(self):
        record = copy.deepcopy(self.record)
        m1 = next(
            c for c in record["candidates"] if c["candidate_id"] == "M1_STACK_EXCHANGE_RELIABILITY"
        )
        m6 = next(c for c in record["candidates"] if c["candidate_id"] == "M6_SECOND_OPPORTUNITY")
        m1["dominance_result"], m1["veto_reason"] = "SELECTED", ""
        m6["dominance_result"] = "FRONTIER"
        record["selected_next_move"] = "M1_STACK_EXCHANGE_RELIABILITY"
        record["primary_outcome"] = "STACK_EXCHANGE_SCORABILITY_IS_NEXT_BOUNDED_MOVE"
        rows = self.gate._linked_rows(record, self.reconciliation, self.preparation)
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_the_candidates(record, rows, self.preparation)

    def test_a_valid_no_move_outcome_is_accepted(self):
        """Inverted control: the gate can express that nothing worth doing exists."""
        record = copy.deepcopy(self.record)
        m6 = next(c for c in record["candidates"] if c["candidate_id"] == "M6_SECOND_OPPORTUNITY")
        m6["dominance_result"] = "FRONTIER"
        record["selected_next_move"] = None
        record["primary_outcome"] = "NO_HIGH_INFORMATION_BOUNDED_MOVE_AVAILABLE"
        rows = self.gate._linked_rows(record, self.reconciliation, self.preparation)
        self.gate._check_the_candidates(record, rows, self.preparation)

    def test_the_gate_is_registered_in_ci(self):
        self.assertIn(
            "render_post_reconciliation_priority.py --check", CI.read_text(encoding="utf-8")
        )


if __name__ == "__main__":
    unittest.main()
