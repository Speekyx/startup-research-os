"""Mission 1.76. Which next evidence move, and why that one.

    MORE ROWS IS NOT MORE INFORMATION.

Four things this file defends.

BREADTH IS A COUNT OF KINDS, NOT OF ROWS. Fifty-eight Evidence rows are ten proposition
kinds across five sources, and the same kind counted twice is still one kind. A move that
adds rows to a lineage the corpus already has is classified as what it is.

THE PRIORITY IS A TIER, NEVER A NUMBER. A ranking score here would be a weighted sum of
judgements nobody calibrated, and it would read as a measurement. The gate refuses a
NUMBER in a scoring-shaped field and permits the record to explain, in words, why it
issues none -- the word is not what is dangerous.

UNKNOWN IS NOT A SMALL GAIN. It is an unbounded one, and ordering it below "a little"
asserts exactly what UNKNOWN denies. So it is excluded from the gain comparison, and a
candidate placed above another across it has to name the criterion that placed it.

NOTHING IS PROMOTED TO MAKE THE ANSWER TIDIER. UNKNOWN independence is not independence,
commercial relevance is not willingness to pay, an UNDETERMINED subject relation is not
DIRECT, and an absent review under one profile is never resolved against another.
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

AUDIT = DATA / "opportunity-evidence-breadth-audit-v1.json"
MOVES = DATA / "evidence-completion-candidate-moves-v1.json"
PRIORITY = DATA / "evidence-completion-priority-v1.json"
QUALIFICATION = DATA / "globalping-counterpart-qualification-v3.json"
RENDERER = SCRIPTS / "render_evidence_breadth_priority.py"
MANIFEST = REPO_ROOT / "PROJECT_MANIFEST.md"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"

PAGES = (
    DATA / "opportunity-evidence-breadth-audit-v1.md",
    DATA / "evidence-completion-candidate-moves-v1.md",
    DATA / "evidence-completion-priority-v1.md",
)


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location("render_evidence_breadth_priority", RENDERER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTheAuditIsMeasuredAndNotCarriedForward(unittest.TestCase):
    def setUp(self):
        self.audit = load(AUDIT)

    def test_it_declares_itself_measured_and_mutates_nothing(self):
        self.assertEqual(self.audit["record_kind"], "EVIDENCE_BREADTH_AUDIT")
        self.assertFalse(self.audit["acquisition_performed"])
        self.assertEqual(self.audit["canonical_mutation"], 0)

    def test_the_lineages_account_for_every_evidence_row(self):
        total = sum(row["evidence_rows"] for row in self.audit["evidence_lineages"])
        self.assertEqual(total, self.audit["canonical_baseline"]["evidence"])

    def test_breadth_is_kinds_and_no_kind_is_counted_twice(self):
        kinds = [row["proposition_kind"] for row in self.audit["evidence_lineages"]]
        self.assertEqual(len(kinds), len(set(kinds)))
        # The headline number a careless reading would use, kept beside the one that matters.
        self.assertGreater(self.audit["canonical_baseline"]["evidence"], len(kinds))

    def test_no_independence_group_exists(self):
        self.assertEqual(self.audit["canonical_baseline"]["evidence_independence_groups"], 0)

    def test_every_evidence_row_is_currently_unscorable(self):
        written = sum(row["with_reliability"] for row in self.audit["evidence_lineages"])
        self.assertEqual(written, 0)

    def test_a_reviewed_reliability_exists_for_the_opportunitys_own_lineage(self):
        """The finding the whole priority turns on: the review is not missing."""
        assessed = {
            (a["source_id"], a["proposition_kind"]) for a in self.audit["reliability_assessments"]
        }
        self.assertIn(("wikimedia-pageviews", "platform_counted_content_request_change"), assessed)
        on_opportunity = [
            row for row in self.audit["evidence_lineages"] if row["on_the_opportunity"]
        ]
        self.assertTrue(on_opportunity)

    def test_the_local_profile_reviews_a_minority_of_registered_sources(self):
        reviewed = [g for g in self.audit["local_governance"] if g["reviewed_under_local"]]
        self.assertLess(len(reviewed), len(self.audit["local_governance"]))
        self.assertEqual(len(reviewed), 8)

    def test_held_records_that_feed_no_signal_are_measured(self):
        unused = {h["source_id"]: h["not_feeding_a_signal"] for h in self.audit["held_records"]}
        self.assertGreater(unused["ted-eu"], 0)
        self.assertGreater(unused["stack-exchange"], 0)


class TestCandidatesAreGeneratedFromHeldFacts(unittest.TestCase):
    def setUp(self):
        self.moves = load(MOVES)
        self.audit = load(AUDIT)
        self.candidates = {c["candidate_id"]: c for c in self.moves["candidates"]}

    def test_every_named_source_is_registered(self):
        known = {row["source_id"] for row in self.audit["local_governance"]}
        for cid, candidate in self.candidates.items():
            for token in str(candidate["candidate_source"]).replace(" or ", ", ").split(", "):
                with self.subTest(candidate=cid, source=token):
                    self.assertIn(token.strip(), known)

    def test_readiness_is_assessed_under_one_profile_only(self):
        for cid, candidate in self.candidates.items():
            with self.subTest(candidate=cid):
                self.assertEqual(candidate["source_use_profile"], "local-private-research-v1")

    def test_no_candidate_claims_documented_independence(self):
        for cid, candidate in self.candidates.items():
            with self.subTest(candidate=cid):
                self.assertNotEqual(
                    candidate["independence_potential"],
                    "ESTABLISHED_DISTINCT_LINEAGE_ALREADY_DOCUMENTED",
                )

    def test_no_candidate_claims_willingness_to_pay(self):
        for cid, candidate in self.candidates.items():
            with self.subTest(candidate=cid):
                self.assertNotIn(
                    candidate["commercial_relevance"],
                    ("DIRECT_COMMERCIAL_SIGNAL", "DIRECT_BUYER_OR_BUDGET_SIGNAL"),
                )

    def test_a_scorability_move_says_it_adds_no_dimension(self):
        for cid, candidate in self.candidates.items():
            if candidate["contribution_class"] == "RELIABILITY_OR_SCORABILITY_COMPLETION":
                with self.subTest(candidate=cid):
                    self.assertIsNone(candidate["target_missing_dimension"])
                    self.assertTrue(candidate["why_no_dimension"].strip())

    def test_every_candidate_says_how_it_could_fail(self):
        for cid, candidate in self.candidates.items():
            with self.subTest(candidate=cid):
                self.assertTrue(candidate["why_it_might_fail"].strip())
                self.assertTrue(candidate["why_it_could_change_a_downstream_decision"].strip())

    def test_the_registered_source_gap_is_recorded_rather_than_filled(self):
        gap = self.moves["registered_source_gap"]
        self.assertTrue(gap["gap_exists"])
        self.assertIn("WILLINGNESS_TO_PAY", gap["unreachable_dimensions"])

    def test_globalping_is_eliminated_before_ranking(self):
        eliminated = {c["candidate_id"] for c in self.moves["eliminated_before_ranking"]}
        self.assertIn("M7", eliminated)


class TestThePriorityIsATierAndNotANumber(unittest.TestCase):
    def setUp(self):
        self.priority = load(PRIORITY)
        self.moves = load(MOVES)
        self.candidates = {c["candidate_id"]: c for c in self.moves["candidates"]}

    def test_no_numeric_score_was_issued(self):
        self.assertTrue(self.priority["no_numeric_score_issued"])
        self.assertTrue(self.priority["why_no_score"].strip())

    def test_no_scoring_shaped_field_holds_a_number(self):
        module = gate()
        for key, value in module._walk_pairs(self.priority):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            with self.subTest(field=key):
                self.assertNotIn(key.lower(), module.FORBIDDEN_SCORE_FIELDS)

    def test_the_word_score_may_still_appear_in_an_explanation(self):
        """The practice is forbidden, not the vocabulary. A gate that refused the
        explanation would make the record unable to say what it does not do."""
        self.assertIn("score", json.dumps(self.priority).lower())

    def test_the_tiers_partition_the_candidates(self):
        tiered = [cid for tier in self.priority["tiers"].values() for cid in tier]
        self.assertEqual(sorted(tiered), sorted(self.candidates))
        self.assertEqual(len(tiered), len(set(tiered)))

    def test_tier_one_is_executable_and_decision_changing(self):
        for cid in self.priority["tiers"]["TIER_1_EXECUTABLE_DECISION_CHANGING"]:
            candidate = self.candidates[cid]
            with self.subTest(candidate=cid):
                self.assertEqual(candidate["expected_information_gain"], "DECISION_CHANGING")
                self.assertFalse(candidate["external_action_required"])
                self.assertIn(
                    candidate["collector_state"],
                    ("HELD_DATA_ALREADY_AVAILABLE", "COLLECTOR_IMPLEMENTED"),
                )

    def test_tier_two_is_empty_and_says_why(self):
        self.assertEqual(self.priority["tiers"]["TIER_2_EXECUTABLE_MAJOR_BREADTH"], [])
        self.assertTrue(self.priority["tier_2_is_empty_because"].strip())

    def test_a_placement_across_an_unbounded_gain_names_its_criterion(self):
        placements = self.priority["tier_placements"]
        for cid, candidate in self.candidates.items():
            if candidate["expected_information_gain"] == "UNKNOWN":
                with self.subTest(candidate=cid):
                    self.assertTrue(placements[cid].strip())


class TestTheWinnerIsNotDominatedAndNotAssumed(unittest.TestCase):
    def setUp(self):
        self.priority = load(PRIORITY)
        self.moves = load(MOVES)
        self.candidates = {c["candidate_id"]: c for c in self.moves["candidates"]}
        self.selection = self.priority["selection"]

    def test_the_outcome_and_the_winner_agree(self):
        self.assertEqual(self.selection["primary_outcome"], "NEXT_BOUNDED_EVIDENCE_MOVE_SELECTED")
        self.assertIn(self.selection["selected_candidate"], self.candidates)

    def test_the_winner_is_not_dominated(self):
        self.assertFalse(self.selection["dominated_by_another"])
        for entry in self.priority["dominance"]:
            if entry["pair"].startswith("anything over"):
                self.assertFalse(entry["dominates"])

    def test_the_winner_shares_the_subject_it_is_selected_against(self):
        winner = self.candidates[self.selection["selected_candidate"]]
        self.assertEqual(winner["subject_relationship"], "DIRECT")

    def test_being_the_only_opportunity_is_not_the_reason(self):
        self.assertTrue(self.selection["not_selected_because_it_is_the_only_opportunity"].strip())

    def test_a_non_dominant_winner_says_so(self):
        self.assertFalse(self.selection["uniquely_dominant"])
        self.assertTrue(self.selection["why_selected_without_being_uniquely_dominant"].strip())

    def test_the_next_mission_is_one_move_with_its_limits_written_down(self):
        nxt = self.priority["next_mission"]
        self.assertTrue(nxt["IT_IS_ONE_MOVE"])
        self.assertTrue(nxt["WHAT_IT_CAN_ESTABLISH"])
        self.assertTrue(nxt["WHAT_IT_CANNOT_ESTABLISH"])
        limits = " ".join(nxt["WHAT_IT_CANNOT_ESTABLISH"]).lower()
        self.assertIn("independence", limits)
        self.assertIn("dimension", limits)

    def test_globalping_is_a_dependency_and_not_a_candidate(self):
        dependency = self.priority["globalping_dependency"]
        gates = {g["dimension"]: g["status"] for g in load(QUALIFICATION)["gates"]}
        self.assertEqual(dependency["c9"], gates["C9_RIGHTS_FEASIBILITY"])
        self.assertNotEqual(dependency["c9"], "PASS")
        self.assertFalse(dependency["selectable_now"])
        self.assertFalse(dependency["checked_externally_by_this_mission"])

    def test_this_mission_mutated_nothing(self):
        for counter, value in self.priority["mission_accounting"].items():
            with self.subTest(counter=counter):
                self.assertEqual(value, 0)


class TestTheGateRefusesTheTemptingReadings(unittest.TestCase):
    """A refusal spelled in a module is not a refusal until something calls it."""

    def setUp(self):
        self.gate = gate()
        self.audit = load(AUDIT)
        self.moves = load(MOVES)
        self.priority = load(PRIORITY)

    def refused_candidates(self, moves):
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_candidates(moves, self.audit)

    def refused_priority(self, priority):
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_priority(priority, self.moves, self.audit)

    def test_the_records_as_committed_pass(self):
        self.gate._check_the_audit_is_measured(self.audit)
        self.gate._check_candidates(self.moves, self.audit)
        self.gate._check_no_fabricated_precision(self.priority, self.moves)
        self.gate._check_priority(self.priority, self.moves, self.audit)

    def test_one_kind_counted_twice_is_refused(self):
        audit = copy.deepcopy(self.audit)
        audit["evidence_lineages"].append(copy.deepcopy(audit["evidence_lineages"][0]))
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_the_audit_is_measured(audit)

    def test_an_unregistered_source_is_refused(self):
        moves = copy.deepcopy(self.moves)
        moves["candidates"][0]["candidate_source"] = "some-new-source"
        self.refused_candidates(moves)

    def test_borrowing_another_profile_is_refused(self):
        moves = copy.deepcopy(self.moves)
        moves["candidates"][0]["source_use_profile"] = "commercial-multi-tenant-research-v1"
        self.refused_candidates(moves)

    def test_calling_a_source_ready_without_a_local_review_is_refused(self):
        moves = copy.deepcopy(self.moves)
        target = next(c for c in moves["candidates"] if c["candidate_id"] == "M6")
        target["governance_state"] = "READY_NOW"
        self.refused_candidates(moves)

    def test_a_prohibited_source_called_executable_is_refused(self):
        moves = copy.deepcopy(self.moves)
        moves["candidates"][0]["governance_state"] = "PROHIBITED"
        self.refused_candidates(moves)

    def test_unknown_independence_promoted_is_refused(self):
        moves = copy.deepcopy(self.moves)
        moves["candidates"][0]["independence_potential"] = (
            "ESTABLISHED_DISTINCT_LINEAGE_ALREADY_DOCUMENTED"
        )
        self.refused_candidates(moves)

    def test_commercial_relevance_promoted_to_wtp_is_refused(self):
        moves = copy.deepcopy(self.moves)
        moves["candidates"][0]["commercial_relevance"] = "DIRECT_BUYER_OR_BUDGET_SIGNAL"
        self.refused_candidates(moves)

    def test_a_numeric_ranking_score_is_refused(self):
        priority = copy.deepcopy(self.priority)
        priority["selection"]["priority_score"] = 87
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_no_fabricated_precision(priority, self.moves)

    def test_a_dominated_winner_is_refused(self):
        priority = copy.deepcopy(self.priority)
        priority["selection"]["dominated_by_another"] = True
        self.refused_priority(priority)

    def test_an_undetermined_subject_relation_cannot_win(self):
        priority = copy.deepcopy(self.priority)
        priority["selection"]["selected_candidate"] = "M6"
        priority["tiers"]["TIER_1_EXECUTABLE_DECISION_CHANGING"] = ["M6"]
        priority["tiers"]["TIER_3_BOUNDED_UNBLOCKING_THEN_HIGH_VALUE"] = ["M1", "M3"]
        self.refused_priority(priority)

    def test_a_different_subject_cannot_win(self):
        priority = copy.deepcopy(self.priority)
        priority["selection"]["selected_candidate"] = "M2"
        priority["tiers"]["TIER_1_EXECUTABLE_DECISION_CHANGING"] = ["M2"]
        priority["tiers"]["TIER_4_USEFUL_BUT_INCREMENTAL"] = ["M1", "M4", "M5"]
        self.refused_priority(priority)

    def test_globalping_selected_while_c9_is_partial_is_refused(self):
        priority = copy.deepcopy(self.priority)
        priority["globalping_dependency"]["selectable_now"] = True
        self.refused_priority(priority)

    def test_an_eliminated_candidate_reappearing_in_a_tier_is_refused(self):
        priority = copy.deepcopy(self.priority)
        priority["tiers"]["TIER_4_USEFUL_BUT_INCREMENTAL"].append("M7")
        self.refused_priority(priority)

    def test_a_moved_counter_is_refused(self):
        priority = copy.deepcopy(self.priority)
        priority["mission_accounting"]["EVIDENCE_CREATED"] = 1
        self.refused_priority(priority)

    def test_an_independence_group_in_the_baseline_is_refused(self):
        audit = copy.deepcopy(self.audit)
        audit["canonical_baseline"]["evidence_independence_groups"] = 1
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_the_audit_is_measured(audit)

    def test_a_missing_field_is_a_refusal_rather_than_a_crash(self):
        self.assertIn('ValidationError(f"the records do not carry', RENDERER.read_text("utf-8"))


class TestTheRendererAndGovernance(unittest.TestCase):
    def test_the_renderer_touches_no_network_and_no_model(self):
        source = RENDERER.read_text(encoding="utf-8")
        for banned in (
            "requests",
            "httpx",
            "urllib",
            "psycopg",
            "openai",
            "anthropic",
            "subprocess",
        ):
            with self.subTest(module=banned):
                self.assertNotIn(f"import {banned}", source)

    def test_the_three_pages_exist_and_say_they_are_generated(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                self.assertTrue(page.exists())
                self.assertIn("Do not edit by hand", page.read_text(encoding="utf-8"))

    def test_the_priority_page_reports_the_outcome_and_the_empty_tier(self):
        text = (DATA / "evidence-completion-priority-v1.md").read_text(encoding="utf-8")
        self.assertIn("NEXT_BOUNDED_EVIDENCE_MOVE_SELECTED", text)
        self.assertIn("Tier 2 is empty", text)
        self.assertIn("COUNTERPART_UNRESOLVED", text)

    def test_ci_runs_the_gate(self):
        self.assertIn(RENDERER.name, CI.read_text(encoding="utf-8"))

    def test_the_manifest_lists_the_records(self):
        text = MANIFEST.read_text(encoding="utf-8")
        for path in (AUDIT, MOVES, PRIORITY, RENDERER):
            with self.subTest(record=path.name):
                self.assertIn(path.name, text)

    def test_the_report_exists(self):
        self.assertTrue((REPO_ROOT / "docs" / "reports" / "mission-1.76-report.md").exists())


if __name__ == "__main__":
    unittest.main()
