"""Mission 1.85.3 (N08-A). The machine-readable contract, the frozen corpus and the blank label packs.

The corpus was read from the held records once and frozen; CI has no database, so these tests hold the
frozen artifacts to the properties that do not need one: the split recomputes from its seed, the packs are
blank and carry no text, nothing a model produced appears anywhere, and the contract agrees with the code.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import unittest

from sros_semantic_extraction_contract import LABELS, LabelStatus, RefusalReason

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
CONTRACT = json.loads(
    (DATA / "first-person-semantic-extraction-contract-v1.json").read_text("utf-8")
)
CORPUS = json.loads((DATA / "stack-overflow-semantic-evaluation-corpus-v1.json").read_text("utf-8"))
PACKS = {
    "DEVELOPMENT": json.loads(
        (DATA / "stack-overflow-semantic-label-pack-development-v1.json").read_text("utf-8")
    ),
    "HOLDOUT": json.loads(
        (DATA / "stack-overflow-semantic-label-pack-holdout-v1.json").read_text("utf-8")
    ),
}
SEED = "n08a-stack-overflow-semantic-split-v1"
MODEL_FIELD_NAMES = (
    "prediction",
    "model_output",
    "model_label",
    "classifier",
    "confidence",
    "run_id",
)


def walk(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


class TestContract(unittest.TestCase):
    def test_every_counter_is_zero(self) -> None:
        self.assertEqual(set(CONTRACT["counters"].values()), {0})
        self.assertEqual(
            CONTRACT["outcome"], "CONTRACT_PREREGISTERED_HUMAN_LABELS_AND_EGRESS_REQUIRED"
        )

    def test_labels_agree_with_the_code(self) -> None:
        self.assertEqual(
            [label["label_id"] for label in CONTRACT["labels"]],
            [label.label_id for label in LABELS],
        )
        for doc, code in zip(CONTRACT["labels"], LABELS, strict=True):
            self.assertEqual(doc["status"], code.status.value)
            self.assertEqual(doc["evidence_dimension"], code.evidence_dimension)
        self.assertEqual(
            CONTRACT["extraction_schema"]["refusal_reasons"], [r.value for r in RefusalReason]
        )

    def test_only_two_labels_are_extractable_and_every_other_label_names_its_blocker(self) -> None:
        extractable = {
            label.label_id for label in LABELS if label.status is LabelStatus.EXTRACTABLE
        }
        self.assertEqual(
            extractable, {"REPORTED_FAILED_ATTEMPT", "NEGATIVE_EVALUATION_OF_NAMED_SOLUTION"}
        )
        for label in LABELS:
            with self.subTest(label.label_id):
                self.assertTrue(label.does_not_establish)
                if label.status is LabelStatus.EXTRACTABLE:
                    self.assertIsNotNone(label.evidence_dimension)
                    self.assertEqual(label.ontology_fit.value, "SUPPORTED_BY_EXISTING_ONTOLOGY")
                    self.assertIsNone(label.blocker)
                else:
                    self.assertTrue(label.blocker)

    def test_no_label_name_asserts_a_conclusion(self) -> None:
        for label in LABELS:
            for word in (
                "PAIN",
                "DEMAND",
                "MARKET",
                "WILLINGNESS",
                "GAP_PROVEN",
                "VALIDATED",
                "SEVERE",
                "TREND",
            ):
                self.assertNotIn(word, label.label_id)

    def test_willingness_to_pay_is_never_reachable(self) -> None:
        for label in LABELS:
            self.assertNotEqual(label.evidence_dimension, "WILLINGNESS_TO_PAY")
            if label.status is LabelStatus.EXTRACTABLE:
                self.assertNotEqual(label.evidence_dimension, "SOLUTION_GAP")

    def test_every_threshold_is_proposed_not_authorised(self) -> None:
        thresholds = CONTRACT["proposed_thresholds"]
        self.assertEqual(thresholds["status"], "PROPOSED_NOT_AUTHORISED")
        for item in thresholds["items"]:
            self.assertEqual(item["status"], "PROPOSED_NOT_AUTHORISED", item["metric"])
        for item in thresholds["items"]:
            if item.get("required_present_predictions"):
                self.assertGreaterEqual(item["required_present_predictions"] * item["threshold"], 3)

    def test_the_selected_architecture_keeps_the_model_out_of_persistence(self) -> None:
        selected = CONTRACT["selected_architecture"]
        self.assertTrue(selected["model_writes_nothing"])
        self.assertFalse(selected["model_supplies_offsets"])
        self.assertFalse(selected["is_signal"] or selected["is_claim"] or selected["is_evidence"])
        verdicts = {
            k: v["verdict"] for k, v in CONTRACT["architecture_comparison"]["options"].items()
        }
        self.assertEqual(
            sorted(verdicts.values()), ["REJECTED", "REJECTED_FOR_THE_WRITE_PATH", "SELECTED"]
        )

    def test_d12_is_recorded_as_embeddings_and_not_merged_with_other_blockers(self) -> None:
        d12 = CONTRACT["d12_decision_map"]
        self.assertIn("Embedding", d12["d12"]["definition"])
        self.assertFalse(d12["d12"]["conflicts_with_this_contract"])
        self.assertEqual(
            len({b["id"] for b in d12["separate_blockers"]}), len(d12["separate_blockers"])
        )
        self.assertGreaterEqual(len(d12["separate_blockers"]), 9)


class TestFrozenCorpus(unittest.TestCase):
    def test_counts_and_exclusions(self) -> None:
        self.assertEqual(CORPUS["held_records"], 104)
        self.assertEqual(CORPUS["included_records"], len(CORPUS["records"]))
        self.assertEqual(
            CORPUS["held_records"], CORPUS["included_records"] + CORPUS["excluded_records"]
        )
        for excluded in CORPUS["excluded"]:
            self.assertEqual(excluded["reasons"], ["PER_ITEM_CONTENT_LICENCE_NOT_REPORTED"])
        self.assertFalse(CORPUS["model_outputs_used_in_selection"])
        self.assertEqual(
            len({r["normalized_record_id"] for r in CORPUS["records"]}), len(CORPUS["records"])
        )

    def test_only_the_authorised_resource_is_used(self) -> None:
        self.assertEqual(
            (CORPUS["source_id"], CORPUS["resource_id"]),
            ("stack-exchange", "questions/stackoverflow"),
        )
        for record in CORPUS["records"]:
            self.assertTrue(record["observation_key"].startswith("stack-exchange|stackoverflow|"))
            self.assertTrue(
                record["question_url"].startswith("https://stackoverflow.com/questions/")
            )

    def test_the_split_recomputes_from_its_seed(self) -> None:
        by_cohort: dict[str, list[dict]] = {}
        for record in CORPUS["records"]:
            by_cohort.setdefault(record["cohort"], []).append(record)
        for cohort in by_cohort.values():
            ordered = sorted(
                cohort,
                key=lambda r: hashlib.sha256(
                    f"{SEED}|{r['normalized_record_id']}".encode()
                ).hexdigest(),
            )
            half = (len(ordered) + 1) // 2
            for index, record in enumerate(ordered):
                self.assertEqual(record["split"], "DEVELOPMENT" if index < half else "HOLDOUT")

    def test_no_question_text_is_committed(self) -> None:
        keys = set(walk(CORPUS)) | set(walk(PACKS["DEVELOPMENT"])) | set(walk(PACKS["HOLDOUT"]))
        self.assertTrue(keys.isdisjoint({"title", "body", "surface", "text"}))


class TestBlankPacks(unittest.TestCase):
    def test_packs_cover_their_split_exactly(self) -> None:
        for split, pack in PACKS.items():
            expected = {r["normalized_record_id"] for r in CORPUS["records"] if r["split"] == split}
            self.assertEqual({r["normalized_record_id"] for r in pack["records"]}, expected)
            self.assertEqual(pack["split"], split)
            self.assertFalse(pack["synthetic"])

    def test_every_field_is_blank(self) -> None:
        for pack in PACKS.values():
            self.assertIsNone(pack["reference_origin"])
            self.assertIsNone(pack["annotator_id"])
            self.assertNotIn("AI_ASSISTED_PROVISIONAL", pack["reference_origin_allowed"])
            for record in pack["records"]:
                self.assertIsNone(record["record_note"])
                for label_id, cell in record["labels"].items():
                    with self.subTest(record=record["question_id"], label=label_id):
                        self.assertEqual(cell["state"], "UNLABELLED")
                        self.assertIsNone(cell["note"])
                        self.assertEqual(cell.get("evidence", []), [])
                        self.assertIsNone(cell.get("subject"))

    def test_not_safe_labels_are_not_offered_and_no_model_field_exists(self) -> None:
        not_safe = {label.label_id for label in LABELS if label.status is LabelStatus.NOT_SAFE}
        for pack in PACKS.values():
            keys = set(walk(pack))
            self.assertTrue(keys.isdisjoint(not_safe))
            for name in MODEL_FIELD_NAMES:
                self.assertNotIn(name, keys)


if __name__ == "__main__":
    unittest.main()
