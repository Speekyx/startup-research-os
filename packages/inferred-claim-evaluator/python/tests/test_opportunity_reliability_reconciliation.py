"""Mission 1.78. Revision 2 of the docker Opportunity, by supersession.

Four things this file defends.

A HISTORICAL REVISION MAY REMAIN TRUE ABOUT WHAT THE SYSTEM BELIEVED THEN. Revision 1 is
byte-identical after the reconciliation, still carries its stale sentence, and the v1
preparation record still hashes to what it hashed to.

A NEW REVISION MUST BE TRUE ABOUT WHAT THE SYSTEM CAN ESTABLISH NOW. Revision 2's one new
sentence counts the rows the current resolver binds, and says the rest is not scored.

RELIABILITY CHANGES WHETHER A ROW MAY ENTER AGGREGATION, NOT WHAT IT ESTABLISHES. The seven
hypothesis fields are carried verbatim, no model was called, and the cited set is exactly
revision 1's.

SCORABLE IS NOT SCORED. No score table, no independence group, the profile UNCALIBRATED.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
SCRIPTS = REPO_ROOT / "infrastructure" / "scripts"

RECORD = DATA / "opportunity-reliability-reconciliation-v1.json"
PREPARATION_V1 = DATA / "opportunity-preparation-v1.json"
PREPARATION_V2 = DATA / "opportunity-preparation-v2.json"
GATE = SCRIPTS / "render_opportunity_reconciliation.py"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate():
    spec = importlib.util.spec_from_file_location("render_opportunity_reconciliation", GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestHistoryIsUntouched(unittest.TestCase):
    def setUp(self):
        self.record = load(RECORD)

    def test_the_v1_preparation_record_still_hashes_to_its_recorded_value(self):
        recorded = self.record["historical_artifacts"]["preparation_v1"]["sha256"]
        self.assertEqual(hashlib.sha256(PREPARATION_V1.read_bytes()).hexdigest(), recorded)
        historical = load(PREPARATION_V1)
        self.assertEqual(historical["mission"], "1.28")
        self.assertNotIn("supersedes", historical)
        self.assertEqual(historical["totals"]["evidence_rows_inspected"], 28)

    def test_revision_1_is_identical_after_the_reconciliation(self):
        applied = self.record["revision_2_applied"]
        self.assertTrue(applied["revision_1_byte_identical_after"])
        self.assertEqual(self.record["revision_1"], applied["revision_1_after"])
        self.assertEqual(self.record["revision_1"]["revision"], 1)
        self.assertTrue(
            any(
                "no reviewed reliability applies" in s
                for s in self.record["revision_1"]["epistemic_limitations"]
            )
        )


class TestRevisionTwo(unittest.TestCase):
    def setUp(self):
        self.record = load(RECORD)
        self.one = self.record["revision_1"]
        self.two = self.record["revision_2_applied"]["revision_2_row"]

    def test_exactly_one_revision_was_added_and_it_is_the_newest(self):
        counters = self.record["counters"]
        self.assertEqual(
            counters["after"]["opportunity_revisions"],
            counters["before_reconciliation"]["opportunity_revisions"] + 1,
        )
        self.assertEqual(
            counters["after"]["opportunities"], counters["before_reconciliation"]["opportunities"]
        )
        self.assertEqual(self.two["revision"], 2)
        self.assertEqual(
            self.record["revision_2_applied"]["newest_revision_by_index"]["revision"], 2
        )
        self.assertEqual(self.two["opportunity_id"], self.one["opportunity_id"])

    def test_the_seven_hypothesis_fields_are_carried_verbatim(self):
        for field in (
            "target_actor",
            "observed_need_or_change",
            "candidate_intervention",
            "hypothesis_statement",
            "supported_dimensions",
            "unsupported_dimensions",
            "uncertainties",
        ):
            self.assertEqual(self.one[field], self.two[field], field)

    def test_no_model_was_called(self):
        self.assertIsNone(self.two["model_version"])
        self.assertIsNone(self.two["prompt_version"])
        self.assertEqual(self.two["created_by"], "mission-1.78")

    def test_the_stale_sentence_is_gone_and_the_others_survive(self):
        stale = [
            s for s in self.one["epistemic_limitations"] if "no reviewed reliability applies" in s
        ]
        self.assertEqual(len(stale), 1)
        self.assertNotIn(stale[0], self.two["epistemic_limitations"])
        for sentence in self.one["epistemic_limitations"]:
            if sentence is not stale[0]:
                self.assertIn(sentence, self.two["epistemic_limitations"])
        self.assertEqual(
            len(self.two["epistemic_limitations"]), len(self.one["epistemic_limitations"])
        )

    def test_the_new_sentence_counts_the_rows_and_refuses_a_score(self):
        census = self.record["census"]
        new = [
            s
            for s in self.two["epistemic_limitations"]
            if s not in self.one["epistemic_limitations"]
        ][0]
        self.assertIn(f"{census['scorable_linked_evidence']} of {census['linked_evidence']}", new)
        for phrase in ("UNCALIBRATED", "no Score", "no ranking", "NON_SCORABLE"):
            self.assertIn(phrase, new)

    def test_the_provenance_names_revision_1_and_the_reason(self):
        procedure = self.two["procedure_version"]
        self.assertTrue(procedure.startswith("opportunity-reliability-reconciliation@1.0.0"))
        self.assertIn(f"prior_revision={self.one['id']}", procedure)
        self.assertIn("reason=RELIABILITY_APPLICABILITY_RECONCILIATION", procedure)
        self.assertIn(
            "mission_finding=docs/data/wikimedia-measurement-scope-binding-v1.json", procedure
        )
        self.assertIn("preparation=opportunity-preparation@2.0.0", procedure)


class TestTheCitedRows(unittest.TestCase):
    def setUp(self):
        self.record = load(RECORD)
        self.preparation = load(PREPARATION_V2)

    def test_the_cited_set_is_exactly_revision_ones(self):
        before = {link["evidence_id"] for link in self.record["revision_1_links"]}
        after = {link["evidence_id"] for link in self.record["revision_2_applied"]["links_written"]}
        self.assertEqual(before, after)
        self.assertEqual(len(after), 7)

    def test_scorable_means_resolved_and_nothing_else(self):
        rows = {r["evidence_id"]: r for r in self.preparation["rows"]}
        for entry in self.record["current_evidence"]["linked_by_revision_1_and_carried"]:
            row = rows[entry["evidence_id"]]
            resolved = row["reliability_resolution"]["outcome"] == "RESOLVED"
            self.assertEqual(entry["scorable"], resolved)
            self.assertEqual(row["eligibility"] == "ELIGIBLE_SCORING", resolved)
            self.assertEqual(entry["resolved_reliability"] is not None, resolved)
            self.assertEqual(entry["independence_state"], "UNKNOWN")

    def test_stack_exchange_stays_unresolved_and_wikimedia_resolves(self):
        by_source = {}
        for entry in self.record["current_evidence"]["linked_by_revision_1_and_carried"]:
            by_source.setdefault(entry["source_id"], set()).add(entry["reliability_outcome"])
        self.assertEqual(by_source["stack-exchange"], {"NO_APPLICABLE_ASSESSMENT"})
        self.assertEqual(by_source["wikimedia-pageviews"], {"RESOLVED"})

    def test_unlinked_packet_rows_are_not_quietly_linked(self):
        linked = {
            link["evidence_id"] for link in self.record["revision_2_applied"]["links_written"]
        }
        for row in self.record["current_evidence"]["in_current_packet_not_linked"]:
            self.assertNotIn(row["evidence_id"], linked)
            self.assertEqual(
                row["classification"], "REQUIRES_NEW_SEMANTIC_JUDGEMENT_BEFORE_INCLUSION"
            )
        self.assertGreater(len(self.record["current_evidence"]["in_current_packet_not_linked"]), 0)

    def test_nothing_else_moved(self):
        counters = self.record["counters"]
        for key in (
            "evidence",
            "claims",
            "reliability_assessments",
            "independence_groups",
            "embeddings",
            "sources",
        ):
            self.assertEqual(counters["before_reconciliation"][key], counters["after"][key], key)
        self.assertEqual(counters["after"]["scores_table"], "ABSENT")
        self.assertEqual(counters["after"]["independence_groups"], 0)
        self.assertEqual(counters["after"]["evidence_reliability_written"], 0)


class TestThePreparationV2(unittest.TestCase):
    def setUp(self):
        self.preparation = load(PREPARATION_V2)

    def test_it_supersedes_v1_and_resolves_late(self):
        self.assertEqual(
            self.preparation["supersedes"], "docs/data/opportunity-preparation-v1.json"
        )
        self.assertIn("LINEAGE_LATE_RESOLUTION", self.preparation["reliability_resolution_path"])
        self.assertEqual(self.preparation["totals"]["evidence_rows_inspected"], 58)

    def test_scorability_is_the_resolver_and_not_the_column(self):
        for row in self.preparation["rows"]:
            self.assertEqual(
                row["scorable"], row["reliability_resolution"]["outcome"] == "RESOLVED"
            )
        self.assertEqual(
            self.preparation["totals"]["eligible_scoring"],
            sum(
                1
                for r in self.preparation["rows"]
                if r["reliability_resolution"]["outcome"] == "RESOLVED"
            ),
        )

    def test_scoring_ready_follows_the_contract_and_its_sentence(self):
        for packet in self.preparation["packets"]:
            scoring = packet["eligibility_counts"].get("ELIGIBLE_SCORING", 0)
            self.assertEqual(packet["sufficiency"]["scoring_ready"], scoring >= 2)
            if packet["sufficiency"]["status"] == "HYPOTHESIS_FORMABLE":
                reason = packet["sufficiency"]["reasons"][0]
                self.assertEqual(
                    "not scoring-ready" in reason, not packet["sufficiency"]["scoring_ready"]
                )


class TestTheGate(unittest.TestCase):
    def setUp(self):
        self.gate = gate()
        self.record, self.preparation = self.gate.validate()

    def test_a_widened_cited_set_is_refused(self):
        record = copy.deepcopy(self.record)
        extra = self.record["current_evidence"]["in_current_packet_not_linked"][0]
        record["revision_2_applied"]["links_written"].append(
            {
                "evidence_id": extra["evidence_id"],
                "eligibility_at_citation": extra["eligibility_now"],
            }
        )
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_the_evidence_set_is_not_widened(record, self.preparation)

    def test_a_strengthened_hypothesis_is_refused(self):
        record = copy.deepcopy(self.record)
        record["revision_2_applied"]["revision_2_row"]["hypothesis_statement"] += " Buyers exist."
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_the_hypothesis_is_not_strengthened(record)

    def test_revision_1_edited_in_place_is_refused(self):
        record = copy.deepcopy(self.record)
        record["revision_2_applied"]["revision_1_after"]["epistemic_limitations"] = record[
            "revision_2_applied"
        ]["revision_2_row"]["epistemic_limitations"]
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_history_is_untouched(record)

    def test_the_stale_sentence_surviving_is_refused(self):
        record = copy.deepcopy(self.record)
        record["revision_2_applied"]["revision_2_row"]["epistemic_limitations"] = list(
            record["revision_1"]["epistemic_limitations"]
        )
        with self.assertRaises(self.gate.ValidationError):
            self.gate._check_the_limitations(record)

    def test_scoring_ready_false_with_scorable_rows_is_accepted_when_the_contract_says_so(self):
        """Inverted control: a packet with one scorable row is not scoring-ready, and that passes."""
        record = copy.deepcopy(self.record)
        preparation = copy.deepcopy(self.preparation)
        packet = next(
            p
            for p in preparation["packets"]
            if p["packet_id"] == record["current_evidence"]["packet_id_now"]
        )
        packet["eligibility_counts"] = {
            "ELIGIBLE_SCORING": 1,
            "ELIGIBLE_CONTEXT": packet["size"] - 1,
        }
        packet["sufficiency"]["scoring_ready"] = False
        record["current_evidence"]["scoring_ready_now_per_contract"] = False
        self.gate._check_scoring_readiness_and_no_score(record, preparation)

    def test_the_gate_is_registered_in_ci(self):
        self.assertIn(
            "render_opportunity_reconciliation.py --check", CI.read_text(encoding="utf-8")
        )


if __name__ == "__main__":
    unittest.main()
