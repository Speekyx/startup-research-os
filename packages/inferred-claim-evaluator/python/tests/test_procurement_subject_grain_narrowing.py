"""Mission 1.81. The division narrowed into groups from held data, and no group selected.

Four things this file defends.

THE GRAIN IS THE EXTRACTOR'S. The narrowing level, its name and the floor come from the
procedure's own source, and the held token carries no check digit and no label.

MEMBERSHIP IS DECIDED BY CODES, NOT VALUES. Every held group appears as a cohort, ambiguous
notices join none, value-missing notices stay in the membership, and the census is the
audit's.

THE DERIVATION IS A RE-DERIVATION. Every division Signal spans several groups, so nothing
was reused or filtered; the new rows are the run record's, scorable under the existing TED
scopes, and the second run persisted nothing.

NARROWER IS NOT ACTIONABLE. Every group is a category at a finer grain with no held label;
the re-selection over v3 vetoes every candidate, the parent packet survives, and nothing
canonical moved beyond the derivation.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

RECORD = DATA / "procurement-subject-grain-narrowing-v1.json"
AUDIT = DATA / "procurement-division-92-notice-audit-v1.json"
RUN = DATA / "procurement-grain-derivation-run-v1.json"
RERUN = DATA / "procurement-grain-derivation-rerun-v1.json"
V3 = DATA / "opportunity-preparation-v3.json"
GATE = SCRIPTS / "render_procurement_subject_grain_narrowing.py"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location(
        "render_procurement_subject_grain_narrowing", GATE
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTheGrain(unittest.TestCase):
    def setUp(self):
        self.record = load(RECORD)

    def test_the_level_is_the_group_and_the_token_is_bare(self):
        token = self.record["cpv_token"]
        self.assertEqual(token["CPV_NARROWING_LEVEL"], 3)
        self.assertEqual(token["CPV_NARROWING_LEVEL_NAME"], "group")
        self.assertFalse(token["check_digit_present"])
        self.assertFalse(token["label_held"])
        self.assertTrue(token["CPV_IDENTITY_STABLE"])

    def test_the_level_names_and_floor_are_the_extractors(self):
        levels, minimum = gate()._extractor_constants()
        self.assertEqual(levels, {2: "division", 3: "group", 4: "class", 5: "category"})
        self.assertEqual(minimum, 2)
        self.assertEqual(self.record["derivation"]["MINIMUM_REQUIRED_BY_PROCEDURE"], minimum)


class TestMembership(unittest.TestCase):
    def setUp(self):
        self.record = load(RECORD)
        self.audit = load(AUDIT)

    def test_the_census_is_the_audits(self):
        notices = self.audit["notices"]
        self.assertEqual(self.record["census"]["DIVISION_92_HELD_NOTICES"], len(notices))
        self.assertEqual(len(notices), 177)
        self.assertEqual(self.record["census"]["PRIMARY_OR_ADDITIONAL_CPV_STATUS"], "UNAVAILABLE")

    def test_the_model_refuses_ambiguity_rather_than_inventing_primacy(self):
        m = self.record["membership"]
        self.assertEqual(m["MEMBERSHIP_MODEL_SELECTED"], "C4_REFUSE_AMBIGUOUS_NOTICE")
        self.assertFalse(m["multi_membership_allowed"])
        self.assertFalse(m["deduplicated_to_sum_to_177"])
        self.assertEqual(m["tally_at_group_grain"]["AMBIGUOUS_ACROSS_DIVISIONS"], 88)
        self.assertEqual(m["tally_at_group_grain"]["AMBIGUOUS_ACROSS_GROUPS"], 3)

    def test_every_held_group_is_a_cohort_and_small_ones_are_kept(self):
        ids = [c["CPV_ID"] for c in self.record["cohorts"]]
        self.assertEqual(ids, ["921", "922", "923", "924", "925", "926"])
        for c in self.record["cohorts"]:
            self.assertTrue(c["value_missing_notices_kept_in_membership"])
            self.assertEqual(c["AMBIGUOUS_MEMBERSHIP_COUNT"], 0)
            self.assertIsNone(c["LABEL_IF_HELD"])
        self.assertEqual(
            self.record["narrow_subjects_refused_for_insufficient_input"],
            ["ted-eu:CPV-group:922", "ted-eu:CPV-group:924"],
        )


class TestTheDerivation(unittest.TestCase):
    def setUp(self):
        self.record = load(RECORD)
        self.run = load(RUN)
        self.rerun = load(RERUN)

    def test_it_is_a_re_derivation_because_every_division_signal_spans_groups(self):
        d = self.record["derivation"]
        self.assertEqual(d["DERIVATION_MODEL"], "C_RE_DERIVE_FROM_HELD_NORMALIZED_RECORDS")
        for span in d["division_92_signals_span_several_groups"].values():
            self.assertGreaterEqual(len(span["groups_spanned"]), 2)
        self.assertEqual(d["division_claims_copied_onto_children"], 0)
        self.assertFalse(d["NEW_SIGNAL_TYPE_CREATED"])

    def test_the_new_rows_are_the_run_records(self):
        d = self.record["derivation"]
        self.assertEqual(d["NEW_SIGNALS"], len(self.run["signals"]))
        self.assertEqual(d["NEW_SIGNALS"], 13)
        self.assertEqual(d["NEW_CLAIMS"], 21)
        self.assertEqual(d["NEW_EVIDENCE"], 26)
        for s in self.run["signals"]:
            self.assertEqual(s["classification_level"], "group")
            self.assertGreaterEqual(s["contributing_records"], 2)
            self.assertEqual(s["magnitude_unit"], s["currency"])

    def test_every_new_row_resolves_under_the_existing_ted_scopes(self):
        r = self.record["reliability"]
        self.assertEqual(r["SCORABLE_NEW_EVIDENCE"], 26)
        self.assertEqual(r["NONSCORABLE_NEW_EVIDENCE"], 0)
        self.assertFalse(r["scope_broadened"])
        self.assertEqual(r["assessments_created"], 0)
        self.assertEqual({row["RELIABILITY"] for row in r["rows"]}, {0.5, 0.55})

    def test_the_second_run_persisted_nothing(self):
        self.assertEqual(self.rerun["signals_persisted"], 0)
        self.assertEqual(self.rerun["interpretation"]["claims_new"], 0)
        self.assertEqual(self.rerun["interpretation"]["evidence_new"], 0)
        self.assertEqual(len(self.rerun["skipped_as_existing_witness"]), 13)
        self.assertTrue(self.record["counters"]["IDEMPOTENT_SECOND_RUN"])

    def test_no_currency_was_crossed_and_no_notice_class_merged(self):
        self.assertFalse(self.record["currency_semantics"]["cross_currency_contrast_performed"])
        self.assertFalse(self.record["currency_semantics"]["fx_conversion_performed"])
        self.assertFalse(
            self.record["notice_type_semantics"][
                "CONTRACT_NOTICE_and_CONTRACT_AWARD_NOTICE_combined"
            ]
        )


class TestTheReselection(unittest.TestCase):
    def setUp(self):
        self.record = load(RECORD)
        self.v3 = load(V3)
        self.candidates = {c["subject_key"]: c for c in self.record["reselection"]["candidates"]}

    def test_the_universe_is_v3_without_docker(self):
        subjects = {p["subject"] for p in self.v3["packets"]} - {"subject:docker"}
        self.assertEqual(set(self.candidates), subjects)
        self.assertEqual(len(subjects), 13)

    def test_the_parent_packet_survives_beside_the_groups(self):
        subjects = {p["subject"] for p in self.v3["packets"]}
        self.assertIn("ted-eu:CPV-division:92", subjects)
        self.assertTrue(self.record["preparation"]["division_92_packet_retained"])
        self.assertEqual(self.record["preparation"]["division_92_packet"]["size_after"], 10)

    def test_no_group_is_actionable_and_none_is_a_product(self):
        for key, c in self.candidates.items():
            if ":CPV-group:" in key:
                self.assertEqual(c["subject_type"], "CATEGORY")
                self.assertEqual(c["actionable_grain"], "REQUIRES_NARROWER_SUBJECT_DISCOVERY")
                self.assertNotEqual(c["product_intervention_grain"], "DIRECTLY_SUPPORTED")
                self.assertEqual(c["product_relevance"], "UNKNOWN")
                self.assertEqual(c["veto_state"], "VETOED")
                self.assertFalse(c["buyer_semantics"]["BUYER_FOR_PROPOSED_INTERVENTION"])

    def test_the_groups_join_the_frontier_on_specificity_and_lose_nothing_to_the_division(self):
        frontier = set(self.record["reselection"]["dominance"]["PARETO_FRONTIER"])
        for key in (
            "ted-eu:CPV-group:921",
            "ted-eu:CPV-group:923",
            "ted-eu:CPV-group:925",
            "ted-eu:CPV-group:926",
        ):
            self.assertIn(key, frontier)
        self.assertIn("ted-eu:CPV-division:92", frontier)
        self.assertEqual(
            set(self.record["reselection"]["dominance"]["VETOED_CANDIDATES"]), set(self.candidates)
        )

    def test_nothing_was_selected_and_the_outcomes_correspond(self):
        sel = self.record["reselection"]
        self.assertIsNone(sel["selected_subject"])
        self.assertEqual(sel["primary_outcome"], "SECOND_OPPORTUNITY_REQUIRES_SUBJECT_NARROWING")
        self.assertEqual(
            self.record["primary_outcome"], "PROCUREMENT_NARROWING_REQUIRES_DEEPER_CPV_GRAIN"
        )
        self.assertFalse(self.record["selection"]["value_used_to_select"])
        self.assertTrue(self.record["egress"]["EGRESS_REVIEW_REQUIRED_BEFORE_SYNTHESIS"])
        self.assertFalse(self.record["egress"]["decided_here"])

    def test_the_next_mission_carries_the_semantic_input(self):
        title = self.record["recommended_next_mission"]["title"].lower()
        self.assertIn("semantic", title)
        self.assertNotIn("egress review", title)
        self.assertFalse(self.record["information_gain_test"]["labels_held_at_any_level"])


class TestNothingElseMoved(unittest.TestCase):
    def setUp(self):
        self.record = load(RECORD)

    def test_only_the_derivation_moved(self):
        deltas = self.record["counters"]["deltas"]
        self.assertEqual(
            {k: v for k, v in deltas.items() if v},
            {"signals": 13, "claims": 21, "claim_revisions": 21, "evidence": 26},
        )
        self.assertEqual(self.record["counters"]["after"]["opportunities"], 1)
        self.assertEqual(self.record["counters"]["after"]["opportunity_revisions"], 2)
        self.assertEqual(self.record["counters"]["after"]["opportunity_evidence_links"], 14)
        self.assertEqual(self.record["counters"]["after"]["scores_table"], "ABSENT")

    def test_no_external_action(self):
        acc = self.record["mission_accounting"]
        for key in (
            "api_calls",
            "ted_api_calls",
            "web_requests",
            "model_calls",
            "embeddings",
            "raw_records_created",
            "opportunities_created",
            "scores_persisted",
        ):
            self.assertEqual(acc[key], 0, key)


class TestTheGate(unittest.TestCase):
    def test_the_gate_validates_and_renders_the_shipped_record(self):
        module = gate()
        record = module.validate()
        rendered = (DATA / "procurement-subject-grain-narrowing-v1.md").read_text(encoding="utf-8")
        self.assertEqual(module.render(record), rendered)

    def test_the_gate_is_registered_in_ci(self):
        self.assertIn(
            "render_procurement_subject_grain_narrowing.py --check", CI.read_text(encoding="utf-8")
        )


if __name__ == "__main__":
    unittest.main()
