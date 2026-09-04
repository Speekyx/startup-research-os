"""Mission 1.42 §29, second half. What preparing a question must NOT move.

The packet tests assert what the document says. These assert what the mission
did to the repository around it, which is the half a reader would otherwise
have to take on trust: **the pilot was not re-selected, nothing was acquired,
the aggregation profile is still uncalibrated, and problem-family inference is
still parked.**

Each of these reads a checked-in artifact rather than the live deployment, on
purpose. CI's integration job starts from an empty database, so a test that
queried one would be permanently red or loosened until it verified nothing
(`testing-strategy.md` §68).
"""

from __future__ import annotations

import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
PACKET = DOCS / "second-pilot-convergent-reliability-review-packet-v1.json"
SELECTION = DOCS / "second-pilot-ted-category-selection-v1.json"
AUDIT = DOCS / "calibration-feasibility-audit-v1.json"
CONTRACT = REPO_ROOT / "docs" / "CLAUDE.md"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class NothingWasAcquiredAndNothingWasReSelected(unittest.TestCase):
    """§26. Zero network requests, and the frozen plan is the frozen plan."""

    def test_the_frozen_selection_is_unchanged_hash_and_all(self):
        selection = load(SELECTION)
        self.assertEqual(
            selection["frozen_selection_sha256"],
            "d473b49e7bdc63dd8e65cce100b74dda84891bf0393158003af3747c2b35aa2f",
        )
        plan = selection["acquisition_plan"]
        self.assertEqual(plan["cpv_division"], "92")
        self.assertEqual(len(plan["windows"]), 2)
        self.assertEqual(plan["route"], "ted-search-api-notices")


class CalibrationDidNotHappen(unittest.TestCase):
    """§24. Reliability review is not calibration and does not become it."""

    def test_the_aggregation_profile_is_still_uncalibrated(self):
        profile = load(AUDIT)["profile"]
        self.assertEqual(profile["status"], "UNCALIBRATED")
        self.assertEqual(profile["half_life_days"], {})

    def test_the_feasibility_audit_still_reports_the_pre_mission_corpus(self):
        # Preparing a question changes no canonical counter, so this artifact is
        # stale only if the mission wrote something. It did not.
        totals = load(AUDIT)["totals"]
        self.assertEqual(totals["claims"], 37)
        self.assertEqual(totals["evidence_rows"], 39)
        self.assertEqual(totals["current_reliability_assessments"], 2)


class BoundariesThatStayWhereTheyWere(unittest.TestCase):
    """§13, §17, §25. What a reliability packet must not reach for."""

    def test_problem_family_inference_is_still_parked(self):
        contract = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("PARK_PROBLEM_FAMILY_CLASSIFIER", contract)
        packet = json.dumps(load(PACKET)).lower()
        for phrase in ("same_problem_family", "problem family", "unpark"):
            self.assertNotIn(phrase, packet)

    def test_no_model_was_involved_in_the_judgement_or_in_the_packet(self):
        # There is no origin for a model-generated reliability, anywhere.
        packet = load(PACKET)
        self.assertEqual(packet["generated_by"], "mission-1.42")
        rendered = json.dumps(packet).lower()
        for phrase in (
            "model_version",
            "prompt_version",
            "model_guessed",
            "model_inferred",
        ):
            self.assertNotIn(phrase, rendered)

    def test_reliability_is_never_offered_as_a_source_wide_coefficient(self):
        # A scope is five fields. `ted-eu` alone matches nothing, by construction.
        packet = load(PACKET)
        excluded = json.dumps(packet["what_reliability_means"]["it_is_not"]).lower()
        self.assertIn("generally trustworthy", excluded)
        for measured in packet["measured_scopes"]:
            self.assertEqual(len(measured["scope"]), 5)
            for value in measured["scope"].values():
                self.assertTrue(str(value).strip())

    def test_source_policy_state_is_absent_from_the_reliability_packet(self):
        # Compliance is not reliability, in both directions.
        rendered = json.dumps(load(PACKET))
        for phrase in (
            "APPROVED_WITH_CONDITIONS",
            "REQUIRES_REVIEW",
            "RESTRICTED",
            "use_profile",
            "eligibility",
        ):
            self.assertNotIn(phrase, rendered)

    def test_overlap_and_independence_are_recorded_and_decide_nothing(self):
        # §10. DISJOINT witnesses are temporally separated, not epistemically
        # independent, and neither state appears as a route to a value.
        packet = load(PACKET)
        for row in packet["affected_rows"]:
            self.assertEqual(row["independence_state"], "UNKNOWN")
            self.assertIsNone(row["independence_group_id"])
        judgement = json.dumps(packet["operator_worksheet"]["judgement"]).lower()
        for phrase in ("disjoint", "overlap", "independence"):
            self.assertNotIn(phrase, judgement)


if __name__ == "__main__":
    unittest.main()
