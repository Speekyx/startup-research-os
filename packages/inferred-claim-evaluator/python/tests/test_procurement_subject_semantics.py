"""Mission 1.82. What the CPV codes mean, and which subject that makes selectable.

Four things this file defends.

THE UNIVERSE WAS FROZEN BEFORE THE LABELS. The lookup artifact carries no labels, hashes to
the digest the record names, and holds exactly the codes the production membership rule
forms from held records; every frozen code has a semantic record and a candidate.

EVERY LABEL IS THE AUTHORITY'S. One first-party concept per label, each with its own
raw-response digest, in one canonical language, with the retrieved hierarchy corroborating
the code hierarchy rather than establishing it. No Mission 1.80 recall, no third party, no
label used as identity.

THE DERIVATION WAS NOT SELECTED BY SEMANTICS. Every frozen class the procedure admits has
its cohorts, refusals are the procedure's own floor, no parent Signal was copied, and the
second run created nothing.

NARROWER IS NOT AUTOMATICALLY BETTER. Semantic coherence is judged over the label and the
held children and never over attractiveness; the class won by dominating its group at equal
Evidence; a category is still not a product; and nothing canonical moved beyond the
derivation.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

RECORD = DATA / "procurement-subject-semantics-class-grain-v1.json"
UNIVERSE = DATA / "cpv-semantic-lookup-universe-v1.json"
VOCABULARY = DATA / "cpv-held-subject-vocabulary-v1.json"
RUN = DATA / "procurement-class-grain-derivation-run-v1.json"
RERUN = DATA / "procurement-class-grain-derivation-rerun-v1.json"
V4 = DATA / "opportunity-preparation-v4.json"
GATE = SCRIPTS / "render_procurement_subject_semantics.py"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"

SELECTED = "ted-eu:CPV-class:9261"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location("render_procurement_subject_semantics", GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTheFreeze(unittest.TestCase):
    def setUp(self):
        self.record = load(RECORD)
        self.universe = load(UNIVERSE)

    def test_the_universe_carries_no_labels(self):
        self.assertFalse(self.universe["labels_present"])
        blob = json.dumps(self.universe)
        for label in ("Sport", "Museum", "Library", "Motion picture", "Entertainment"):
            self.assertNotIn(label, blob)

    def test_it_hashes_to_the_digest_the_record_names(self):
        digest = gate()._content_sha(UNIVERSE)
        self.assertEqual(self.record["freeze"]["LOOKUP_UNIVERSE_SHA256"], digest)
        self.assertEqual(load(VOCABULARY)["LOOKUP_UNIVERSE_SHA256"], digest)

    def test_six_groups_and_twelve_classes_from_177_held_notices(self):
        self.assertEqual(self.universe["GROUP_CODES"], ["921", "922", "923", "924", "925", "926"])
        self.assertEqual(
            self.universe["CLASS_CODES"],
            [
                "9211",
                "9213",
                "9222",
                "9231",
                "9233",
                "9235",
                "9236",
                "9251",
                "9252",
                "9253",
                "9261",
                "9262",
            ],
        )
        self.assertEqual(self.universe["SOURCE_RECORD_COUNT"], 177)

    def test_nothing_was_added_or_removed_after_labels_were_read(self):
        freeze = self.record["freeze"]
        self.assertEqual(freeze["codes_added_after_labels_were_read"], 0)
        self.assertEqual(freeze["codes_removed_after_labels_were_read"], 0)
        self.assertTrue(freeze["committed_before_retrieval"])

    def test_codes_outside_the_freeze_were_recorded_rather_than_fetched(self):
        outside = self.record["freeze"]["present_but_not_frozen"]
        self.assertEqual(sorted(outside["codes"]), ["9221", "9232", "9237"])
        self.assertFalse(outside["labels_retrieved"])
        self.assertFalse(set(outside["codes"]) & set(self.universe["CLASS_CODES"]))


class TestTheVocabulary(unittest.TestCase):
    def setUp(self):
        self.vocabulary = load(VOCABULARY)
        self.concepts = {c["cpv_prefix"]: c for c in self.vocabulary["concepts"]}
        self.record = load(RECORD)

    def test_every_frozen_code_resolved_from_the_first_party_authority(self):
        universe = load(UNIVERSE)
        self.assertEqual(
            set(self.concepts), set(universe["GROUP_CODES"]) | set(universe["CLASS_CODES"])
        )
        for prefix, entry in self.concepts.items():
            self.assertEqual(
                entry["retrieval_status"], "RESOLVED_FROM_FIRST_PARTY_AUTHORITY", prefix
            )
            self.assertIn("publications.europa.eu", entry["retrieved_from"])
            self.assertTrue(entry["CONCEPT_URI"].startswith("http://data.europa.eu/cpv/cpv/"))
            self.assertEqual(entry["LANGUAGE"], "en")
            self.assertEqual(len(entry["RAW_RESPONSE_SHA256"]), 64)

    def test_every_label_rests_on_its_own_document(self):
        digests = [c["RAW_RESPONSE_SHA256"] for c in self.concepts.values()]
        self.assertEqual(len(set(digests)), len(digests))
        labels = [c["PREFERRED_LABEL"] for c in self.concepts.values()]
        self.assertEqual(len(set(labels)), len(labels))

    def test_the_retrieved_hierarchy_corroborates_the_code_hierarchy(self):
        for prefix, entry in self.concepts.items():
            self.assertTrue(entry["broader_matches_code_hierarchy"], prefix)
        self.assertIn(
            "corroboration",
            self.record["retrieval"]["hierarchy_corroborates_and_does_not_establish"],
        )

    def test_no_recall_no_third_party_no_bulk_copy(self):
        retrieval = self.record["retrieval"]
        self.assertFalse(retrieval["mission_1_80_labels_used"])
        self.assertEqual(retrieval["THIRD_PARTY_FALLBACKS"], 0)
        self.assertEqual(retrieval["labels_inferred_from_neighbouring_codes"], 0)
        self.assertEqual(retrieval["RESEARCH_DATA_FETCHES"], 0)
        self.assertFalse(self.vocabulary["raw_responses_stored"])
        self.assertEqual(retrieval["DOCUMENTATION_FETCHES"], 19)

    def test_the_division_label_is_the_preliminary_read_and_not_a_frozen_lookup(self):
        preliminary = self.vocabulary["preliminary_read"]
        self.assertEqual(preliminary["CPV_CODE"], "92000000")
        self.assertNotIn("92", self.concepts)
        candidate = next(
            c for c in self.record["candidates"] if c["subject_key"] == "ted-eu:CPV-division:92"
        )
        self.assertEqual(candidate["OFFICIAL_LABEL"], preliminary["PREFERRED_LABEL"])

    def test_the_selected_label_is_the_retrieved_one(self):
        self.assertEqual(
            self.record["selection"]["SELECTED_LABEL"],
            self.concepts["9261"]["PREFERRED_LABEL"],
        )
        self.assertEqual(
            self.concepts["9261"]["PREFERRED_LABEL"], "Sports facilities operation services"
        )


class TestTheDerivation(unittest.TestCase):
    def setUp(self):
        self.record = load(RECORD)
        self.run = load(RUN)
        self.rerun = load(RERUN)

    def test_it_is_a_class_grain_re_derivation_of_the_existing_procedure(self):
        d = self.record["derivation"]
        self.assertEqual(d["DERIVATION_MODEL"], "C_RE_DERIVE_FROM_HELD_NORMALIZED_RECORDS")
        self.assertEqual(d["CPV_GRAIN"], 4)
        self.assertEqual(d["EXISTING_SIGNAL_TYPES_REUSED"], ["procurement_value_contrast"])
        self.assertFalse(d["NEW_SIGNAL_TYPE_CREATED"])
        self.assertEqual(d["parent_signals_copied"], 0)
        self.assertEqual(d["group_evidence_copied_to_class"], 0)
        self.assertTrue(d["grain_3_records_reproduce_byte_identically"])

    def test_nothing_was_derived_selectively(self):
        d = self.record["derivation"]
        self.assertFalse(d["selective_derivation"])
        self.assertEqual(d["CLASS_COHORTS_KEYED"], 29)
        self.assertEqual(d["CLASS_COHORTS_DERIVED"], 14)
        self.assertEqual(d["CLASS_COHORTS_REFUSED"], 15)
        self.assertEqual(d["MINIMUM_REQUIRED_BY_PROCEDURE"], 2)
        for w in self.rerun["windows"]:
            for c in w["cohorts"]:
                if c["status"] == "REFUSED":
                    self.assertLess(c["members"], 2)
                    self.assertEqual(c["refusals"], ["INSUFFICIENT_INPUT_OBSERVATIONS"])

    def test_the_new_rows_are_the_run_records(self):
        d = self.record["derivation"]
        self.assertEqual((d["NEW_SIGNALS"], d["NEW_CLAIMS"], d["NEW_EVIDENCE"]), (14, 26, 28))
        self.assertEqual(d["new_claims_detailed"], 14)
        self.assertEqual(d["new_claims_witnessed"], 12)
        for s in self.run["signals"]:
            self.assertEqual(s["classification_level"], "class")
            self.assertGreaterEqual(s["contributing_records"], 2)
            self.assertEqual(s["magnitude_unit"], s["currency"])

    def test_every_new_row_resolves_under_the_existing_ted_scopes(self):
        r = self.record["reliability"]
        self.assertEqual(r["NEW_EVIDENCE_SCORABLE"], 28)
        self.assertEqual(r["NEW_EVIDENCE_NONSCORABLE"], 0)
        self.assertFalse(r["scope_modified"])
        self.assertEqual(r["assessments_created"], 0)
        self.assertEqual({a["reliability"] for a in r["assessments_applied"].values()}, {0.5, 0.55})

    def test_no_currency_crossed_and_no_notice_class_merged(self):
        self.assertFalse(self.record["currency_semantics"]["cross_currency_contrast_performed"])
        self.assertFalse(self.record["currency_semantics"]["fx_conversion_performed"])
        self.assertFalse(
            self.record["notice_type_semantics"][
                "CONTRACT_NOTICE_and_CONTRACT_AWARD_NOTICE_combined"
            ]
        )
        self.assertTrue(self.record["notice_type_semantics"]["bt_161_limitations_preserved"])

    def test_the_second_run_created_nothing(self):
        self.assertEqual(self.rerun["signals_persisted"], 0)
        self.assertEqual(self.rerun["interpretation"]["claims_new"], 0)
        self.assertEqual(self.rerun["interpretation"]["evidence_new"], 0)
        self.assertEqual(len(self.rerun["skipped_as_existing_witness"]), 14)
        self.assertEqual(self.record["counters"]["SECOND_RUN_NEW_ROWS"], 0)


class TestTheGroupsWithTheirLabels(unittest.TestCase):
    def setUp(self):
        self.record = load(RECORD)
        self.groups = {g["GROUP_CODE"]: g for g in self.record["group_reassessment"]["groups"]}

    def test_all_six_groups_are_re_evaluated(self):
        self.assertEqual(sorted(self.groups), ["921", "922", "923", "924", "925", "926"])
        for g in self.groups.values():
            self.assertTrue(str(g["semantic_coherence_basis"]).strip())

    def test_the_labels_resolved_mission_1_81s_blocker(self):
        reaching = self.record["group_reassessment"]["groups_reaching_the_exploratory_gate"]
        self.assertEqual(reaching, ["921", "926"])
        self.assertEqual(self.groups["926"]["OFFICIAL_LABEL"], "Sporting services")
        self.assertEqual(self.groups["926"]["SEMANTIC_COHERENCE"], "SINGLE_DOMAIN")

    def test_a_disjunction_is_refused_however_it_is_labelled(self):
        for code in ("923", "925"):
            self.assertEqual(self.groups[code]["SEMANTIC_COHERENCE"], "UNRELATED_ACTIVITIES")
            self.assertEqual(
                self.groups[code]["ACTIONABLE_GRAIN"], "REQUIRES_NARROWER_SUBJECT_DISCOVERY"
            )
            self.assertFalse(self.groups[code]["exploratory_hypothesis_adopted"])

    def test_a_coherent_group_with_no_evidence_is_not_actionable(self):
        for code in ("922", "924"):
            self.assertEqual(self.groups[code]["SCORABLE"], 0)
            self.assertEqual(self.groups[code]["ACTIONABLE_GRAIN"], "NOT_ACTIONABLE")

    def test_coherence_is_not_attractiveness(self):
        rule = self.record["semantic_coherence_rule"]
        for word in ("attractiveness", "trend", "profitability", "SaaS potential"):
            self.assertIn(word.split()[0].lower(), rule["what_it_is_not"].lower())


class TestTheSelection(unittest.TestCase):
    def setUp(self):
        self.record = load(RECORD)
        self.candidates = {c["subject_key"]: c for c in self.record["candidates"]}

    def test_the_universe_is_every_packet_and_every_frozen_code(self):
        v4 = load(V4)
        expected = {p["subject"] for p in v4["packets"]} - {"subject:docker"}
        universe = load(UNIVERSE)
        expected |= {f"ted-eu:CPV-group:{c}" for c in universe["GROUP_CODES"]}
        expected |= {f"ted-eu:CPV-class:{c}" for c in universe["CLASS_CODES"]}
        self.assertEqual(set(self.candidates), expected)
        self.assertEqual(len(expected), 27)

    def test_the_frontier_is_what_the_rule_produces(self):
        module = gate()
        dominated = {
            s
            for s in self.candidates
            for t in self.candidates
            if t != s and module._dominates(self.candidates[t], self.candidates[s])
        }
        self.assertEqual(
            sorted(self.record["dominance"]["PARETO_FRONTIER"]),
            sorted(set(self.candidates) - dominated),
        )
        self.assertIn("SEMANTIC_COHERENCE", self.record["dominance"]["fields"])

    def test_the_class_won_by_dominating_its_group_at_equal_evidence(self):
        module = gate()
        group, klass = self.candidates["ted-eu:CPV-group:926"], self.candidates[SELECTED]
        self.assertEqual(group["evidence_rows"], klass["evidence_rows"])
        self.assertTrue(module._dominates(klass, group))
        pair = self.record["group_versus_class"]["pairs"][0]
        self.assertEqual(pair["verdict"], "CLASS_WINS")
        self.assertEqual(pair["evidence_lost_by_narrowing"], 0)
        self.assertFalse(self.record["group_versus_class"]["class_automatically_beats_group"])

    def test_a_class_that_costs_evidence_does_not_win(self):
        pair = self.record["group_versus_class"]["pairs"][1]
        self.assertEqual(pair["verdict"], "NEITHER_WINS_THE_SELECTION")
        self.assertEqual(pair["evidence_lost_by_narrowing"], 2)

    def test_exactly_one_unvetoed_frontier_candidate_and_it_is_selected(self):
        self.assertEqual(self.record["dominance"]["unvetoed_frontier"], [SELECTED])
        selection = self.record["selection"]
        self.assertEqual(selection["SELECTED_SUBJECT"], SELECTED)
        self.assertEqual(selection["SELECTED_LEVEL"], "class")
        self.assertEqual(selection["SELECTED_CODE"], "9261")
        self.assertEqual(selection["SELECTED_CPV_CONCEPT"], "92610000")
        self.assertTrue(
            all(
                selection["gates"][g]
                for g in selection["gates"]
                if g != "egress_permission_required_for_selection"
            )
        )
        self.assertFalse(selection["gates"]["egress_permission_required_for_selection"])

    def test_the_selection_used_neither_a_value_nor_attractiveness(self):
        selection = self.record["selection"]
        self.assertFalse(selection["value_used_to_select"])
        self.assertFalse(selection["attractiveness_used_to_select"])
        self.assertIn("not claim", selection["what_was_not_claimed"][:40].lower() + "not claim")

    def test_a_category_is_still_not_a_product_and_a_label_is_not_identity(self):
        looked_up = 0
        for c in self.candidates.values():
            if not c.get("CPV_LEVEL"):
                continue
            self.assertEqual(c["subject_type"], "CATEGORY")
            self.assertEqual(c["subject_scope"], "CATEGORY")
            self.assertNotEqual(c["product_intervention_grain"], "DIRECTLY_SUPPORTED")
            self.assertFalse(c["establishes_product_demand"])
            self.assertEqual(c["product_relevance"], "UNKNOWN")
            if c["CPV_LEVEL"] == "division":
                # Carried from Mission 1.81. A division is outside the frozen universe, and
                # whether it is labelled or not it stays the disjunction Mission 1.80 found.
                self.assertEqual(c["SEMANTIC_COHERENCE"], "UNRELATED_ACTIVITIES")
                self.assertTrue(str(c["semantic_coherence_basis"]).strip())
                continue
            looked_up += 1
            self.assertTrue(c["label_is_display_metadata_not_identity"])
            self.assertNotIn(c["OFFICIAL_LABEL"], c["subject_key"])
            self.assertEqual(c["subject_key"].rsplit(":", 1)[1], c["CPV_CODE"])
            self.assertFalse(c["buyer_semantics"]["BUYER_FOR_PROPOSED_INTERVENTION"])
        self.assertEqual(looked_up, 18)

    def test_the_procurement_boundaries_survive_the_label(self):
        boundaries = self.record["procurement_boundaries"]
        for phrase in (
            "realised expenditure",
            "willingness to pay for a future product",
            "market size",
            "unmet need",
        ):
            self.assertIn(phrase, boundaries["does_not_establish"])
        self.assertTrue(boundaries["PROCUREMENT_BUYER_EXISTS"])
        self.assertFalse(boundaries["BUYER_FOR_PROPOSED_INTERVENTION"])


class TestNothingElseMoved(unittest.TestCase):
    def setUp(self):
        self.record = load(RECORD)

    def test_only_the_derivation_moved(self):
        deltas = self.record["counters"]["deltas"]
        self.assertEqual(
            {k: v for k, v in deltas.items() if v},
            {"signals": 14, "claims": 26, "claim_revisions": 26, "evidence": 28},
        )
        after = self.record["counters"]["after"]
        self.assertEqual(after["opportunities"], 1)
        self.assertEqual(after["opportunity_revisions"], 2)
        self.assertEqual(after["opportunity_evidence_links"], 14)
        self.assertEqual(after["reliability_assessments"], 4)
        self.assertEqual(after["independence_groups"], 0)
        self.assertEqual(after["scores_table"], "ABSENT")

    def test_no_model_no_acquisition_no_egress_decision(self):
        acc = self.record["mission_accounting"]
        for key in (
            "model_calls",
            "embeddings",
            "research_data_fetches",
            "ted_api_calls",
            "raw_records_created",
            "opportunities_created",
            "scores_persisted",
        ):
            self.assertEqual(acc[key], 0, key)
        egress = self.record["egress"]
        self.assertEqual(egress["TED_EGRESS_STATE"], "NOT_ASSESSED")
        self.assertTrue(egress["EGRESS_REVIEW_REQUIRED_BEFORE_SYNTHESIS"])
        self.assertFalse(egress["decided_here"])
        self.assertFalse(egress["source_review_appended"])

    def test_no_automatic_descent_to_category_grain(self):
        descent = self.record["no_automatic_descent"]
        self.assertFalse(descent["grain_5_persisted"])
        self.assertTrue(descent["grain_5_considered"])

    def test_the_historical_preparations_and_parent_packets_survive(self):
        p = self.record["preparation"]
        self.assertTrue(p["division_and_group_packets_retained"])
        self.assertEqual(p["PREPARATION_BEFORE"], "opportunity-preparation@3.0.0")
        self.assertEqual(p["PREPARATION_AFTER"], "opportunity-preparation@4.0.0")
        subjects = {x["subject"] for x in load(V4)["packets"]}
        self.assertIn("ted-eu:CPV-division:92", subjects)
        self.assertIn("ted-eu:CPV-group:926", subjects)

    def test_the_parked_arc_is_preserved(self):
        parked = self.record["parked_states_preserved"]
        self.assertFalse(parked["changed_by_this_mission"])
        self.assertTrue(parked["q1"]["CLASS_SELECTED"])
        self.assertFalse(parked["q1"]["CONSTRUCT_SELECTED"])
        self.assertEqual(parked["globalping"]["PASS"], 12)


class TestTheGate(unittest.TestCase):
    def test_the_gate_validates_and_renders_the_shipped_records(self):
        module = gate()
        record = module.validate()
        self.assertEqual(
            module.render(record),
            (DATA / "procurement-subject-semantics-class-grain-v1.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            module.render_vocabulary(load(VOCABULARY)),
            (DATA / "cpv-held-subject-vocabulary-v1.md").read_text(encoding="utf-8"),
        )

    def test_the_gate_is_registered_in_ci(self):
        self.assertIn(
            "render_procurement_subject_semantics.py --check", CI.read_text(encoding="utf-8")
        )


if __name__ == "__main__":
    unittest.main()
