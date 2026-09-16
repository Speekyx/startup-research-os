"""Mission 1.85.5: the SINGLE_HUMAN_REFERENCE pilot mode, without a fabricated second human.

The real committed operator-a file is used read-only as the one genuine human reference. Every OTHER
annotation below is a synthetic structural copy made inside the test to exercise a gate; none is written
to the repository and none is a label anyone gave.
"""

from __future__ import annotations

import copy
import fnmatch
import hashlib
import inspect
import json
import pathlib
import unittest

from sros_semantic_extraction_contract.agreement import (
    analyse_composition,
    analyse_single_human_reference,
)
from sros_semantic_extraction_contract.annotation import (
    ATTESTATION_FLAGS,
    AnnotationOrigin,
    HoldoutAccessError,
    validate_annotation_pack,
)
from sros_semantic_extraction_contract.provisional import (
    HUMAN_ANNOTATION_GLOB,
    PROVISIONAL_ANNOTATION_GLOB,
    diagnostic_disagreements,
    provisional_annotation_problems,
)
from sros_semantic_extraction_contract.reference import (
    HOLDOUT_POLICY,
    INTER_ANNOTATOR_METRICS,
    NOT_APPLICABLE_SINGLE_ANNOTATOR,
    PILOT_NOT_CERTIFICATION,
    ReferenceStrength,
    assess_reference,
    holdout_reference_permitted,
    single_annotator_agreement,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
CORPUS = json.loads((DATA / "stack-overflow-semantic-evaluation-corpus-v1.json").read_text("utf-8"))
CONTRACT = json.loads(
    (DATA / "first-person-semantic-extraction-contract-v1.json").read_text("utf-8")
)
DEVELOPMENT = [r for r in CORPUS["records"] if r["split"] == "DEVELOPMENT"]
SPLIT_IDS = {r["normalized_record_id"] for r in DEVELOPMENT}
DIGESTS = {r["normalized_record_id"]: r["surface_sha256"] for r in DEVELOPMENT}
HUMAN_FILES = sorted(DATA.glob(HUMAN_ANNOTATION_GLOB))
OPERATOR_A = json.loads(
    (DATA / "stack-overflow-semantic-annotations-development-operator-a-v1.json").read_text("utf-8")
)


def assess(files, adjudication_present=False):
    return assess_reference(
        files,
        split_record_ids=SPLIT_IDS,
        surface_sha256_by_id=DIGESTS,
        adjudication_present=adjudication_present,
    )


def structural_copy(annotator_id: str) -> dict:
    """A synthetic second file for gate tests only: same shape, different id. Never committed."""
    doc = copy.deepcopy(OPERATOR_A)
    doc["annotator_id"] = annotator_id
    doc["attestation"]["annotator_id"] = annotator_id
    return doc


def as_ai(doc: dict) -> dict:
    ai = copy.deepcopy(doc)
    ai["reference_origin"] = "AI_ASSISTED_PROVISIONAL"
    return ai


def numbers_in(value) -> list:
    if isinstance(value, bool):
        return []
    if isinstance(value, int | float):
        return [value]
    if isinstance(value, dict):
        return [n for v in value.values() for n in numbers_in(v)]
    if isinstance(value, list):
        return [n for v in value for n in numbers_in(v)]
    return []


class TestHumanReferenceGates(unittest.TestCase):
    def test_exactly_one_committed_human_file_exists_and_it_is_not_a_model(self) -> None:
        self.assertEqual(
            [p.name for p in HUMAN_FILES],
            ["stack-overflow-semantic-annotations-development-operator-a-v1.json"],
        )
        self.assertIn(OPERATOR_A["reference_origin"], {o.value for o in AnnotationOrigin})
        self.assertTrue(all(OPERATOR_A["attestation"][f] is True for f in ATTESTATION_FLAGS))

    def test_one_real_human_satisfies_only_the_pilot_gate(self) -> None:
        result = assess([("operator-a", OPERATOR_A)])
        self.assertEqual(result.strength, ReferenceStrength.SINGLE_HUMAN_REFERENCE)
        self.assertTrue(result.pilot_gate)
        self.assertFalse(result.multi_human_gate)
        self.assertEqual(result.result_scope, "DEVELOPMENT_PILOT")
        self.assertEqual(result.result_label, PILOT_NOT_CERTIFICATION)

    def test_one_human_cannot_satisfy_the_multi_human_gate_even_with_an_adjudication_file(
        self,
    ) -> None:
        result = assess([("operator-a", OPERATOR_A)], adjudication_present=True)
        self.assertFalse(result.multi_human_gate)
        self.assertNotEqual(result.strength, ReferenceStrength.MULTI_HUMAN_REFERENCE)

    def test_ai_provisional_satisfies_neither_human_gate(self) -> None:
        alone = assess([("ai", as_ai(OPERATOR_A))], adjudication_present=True)
        self.assertEqual(alone.strength, ReferenceStrength.NO_HUMAN_REFERENCE)
        self.assertFalse(alone.pilot_gate or alone.multi_human_gate)
        self.assertIn(
            "AI_ASSISTED_PROVISIONAL_IS_NEVER_A_HUMAN_REFERENCE", alone.refused_files[0][1]
        )
        # beside the human, it does not become the "second annotator", and it blocks the pilot too
        paired = assess(
            [("operator-a", OPERATOR_A), ("ai", as_ai(structural_copy("second")))],
            adjudication_present=True,
        )
        self.assertFalse(paired.pilot_gate or paired.multi_human_gate)
        self.assertEqual(paired.strength, ReferenceStrength.NO_HUMAN_REFERENCE)

    def test_an_edited_or_incomplete_committed_file_counts_for_nothing(self) -> None:
        unattested = copy.deepcopy(OPERATOR_A)
        unattested["attestation"]["no_model_assistance_used"] = False
        unlabelled = copy.deepcopy(OPERATOR_A)
        first = unlabelled["records"][0]
        first["labels"]["REPORTED_FAILED_ATTEMPT"]["state"] = "UNLABELLED"
        moved = copy.deepcopy(OPERATOR_A)
        moved["records"][0]["surface_sha256"] = "0" * 64
        for doc, problem in (
            (unattested, "ATTESTATION_INVALID"),
            (unlabelled, "CELL_NOT_LABELLED"),
            (moved, "SURFACE_DIGEST_MISMATCH"),
        ):
            result = assess([("x", doc)])
            self.assertFalse(result.pilot_gate)
            self.assertTrue(any(p.startswith(problem) for p in result.refused_files[0][1]))

    def test_a_model_like_annotator_id_is_still_refused_by_the_human_importer(self) -> None:
        pack = {
            "split": "DEVELOPMENT",
            "synthetic": False,
            "reference_origin": "HUMAN_OPERATOR",
            "annotator_id": "claude-labeller",
            "records": [],
        }
        report = validate_annotation_pack(
            pack,
            split="DEVELOPMENT",
            split_record_ids=set(),
            other_split_record_ids=set(),
            surfaces={},
            blank_pack={},
        )
        codes = {code for code, _ in report.refusals}
        self.assertIn("ANNOTATOR_ID_NOT_ACCEPTED", codes)
        self.assertFalse(report.accepted)
        ai_pack = dict(pack, annotator_id="operator-b", reference_origin="AI_ASSISTED_PROVISIONAL")
        report = validate_annotation_pack(
            ai_pack,
            split="DEVELOPMENT",
            split_record_ids=set(),
            other_split_record_ids=set(),
            surfaces={},
            blank_pack={},
        )
        self.assertIn("ORIGIN_NOT_HUMAN", {code for code, _ in report.refusals})
        doc = structural_copy("gpt-helper")
        self.assertIn("ANNOTATOR_ID_NOT_ACCEPTED", assess([("x", doc)]).refused_files[0][1])

    def test_multi_human_behaviour_is_unchanged(self) -> None:
        one, two = structural_copy("human-one"), structural_copy("human-two")
        self.assertEqual(
            assess([("1", one), ("2", two)], adjudication_present=True).strength,
            ReferenceStrength.MULTI_HUMAN_REFERENCE,
        )
        without = assess([("1", one), ("2", two)], adjudication_present=False)
        self.assertFalse(without.multi_human_gate or without.pilot_gate)
        duplicate = assess([("1", one), ("2", structural_copy("human-one"))], True)
        self.assertFalse(duplicate.multi_human_gate)
        with self.assertRaises(ValueError):
            analyse_composition([OPERATOR_A], CONTRACT)
        report = analyse_composition([one, two], CONTRACT)
        pairwise = report["labels"]["REPORTED_FAILED_ATTEMPT"]["pairwise"]
        self.assertNotIn(NOT_APPLICABLE_SINGLE_ANNOTATOR, json.dumps(report))
        self.assertIn("cohen_kappa_three_state", pairwise)


class TestSingleAnnotatorMetrics(unittest.TestCase):
    def test_inter_annotator_metrics_are_not_applicable_and_never_zero(self) -> None:
        agreement = single_annotator_agreement()
        self.assertEqual(set(agreement), set(INTER_ANNOTATOR_METRICS))
        self.assertTrue(all(v == NOT_APPLICABLE_SINGLE_ANNOTATOR for v in agreement.values()))
        report = analyse_single_human_reference(OPERATOR_A, CONTRACT)
        for label in report["labels"].values():
            self.assertEqual(label["inter_annotator_agreement"], agreement)
            self.assertEqual(numbers_in(label["inter_annotator_agreement"]), [])
        self.assertEqual(
            report["gates"]["agreement_floor"]["verdict"], NOT_APPLICABLE_SINGLE_ANNOTATOR
        )
        self.assertEqual(report["adjudication_queue_size"], NOT_APPLICABLE_SINGLE_ANNOTATOR)
        self.assertEqual(report["reference_strength"], "SINGLE_HUMAN_REFERENCE")
        self.assertEqual(report["result_label"], PILOT_NOT_CERTIFICATION)
        self.assertNotIn("pairwise", json.dumps(report))

    def test_the_committed_single_human_composition_is_current(self) -> None:
        path = (
            DATA / "stack-overflow-semantic-single-human-reference-composition-development-v1.json"
        )
        expected = json.dumps(
            analyse_single_human_reference(OPERATOR_A, CONTRACT), indent=1, ensure_ascii=False
        )
        self.assertEqual(path.read_bytes(), (expected + "\n").encode("utf-8"))
        self.assertFalse(
            (DATA / "stack-overflow-semantic-adjudication-queue-development-v1.json").exists()
        )
        self.assertFalse(
            (DATA / "stack-overflow-semantic-annotation-composition-development-v1.json").exists()
        )


class TestHoldoutAndProvisional(unittest.TestCase):
    def test_holdout_stays_blocked_by_default(self) -> None:
        self.assertEqual(HOLDOUT_POLICY, "HOLDOUT_REQUIRES_MULTI_HUMAN_OR_NEW_OPERATOR_DECISION")
        for strength in ReferenceStrength:
            self.assertEqual(
                holdout_reference_permitted(strength),
                strength is ReferenceStrength.MULTI_HUMAN_REFERENCE,
            )
        self.assertEqual(
            list(inspect.signature(holdout_reference_permitted).parameters), ["strength"]
        )
        with self.assertRaises(HoldoutAccessError):
            validate_annotation_pack(
                {"split": "HOLDOUT"},
                split="HOLDOUT",
                split_record_ids=set(),
                other_split_record_ids=set(),
                surfaces={},
                blank_pack={},
            )
        self.assertEqual(list(DATA.glob("stack-overflow-semantic-annotations-holdout-*")), [])

    def test_provisional_annotations_are_stored_apart_and_none_exists(self) -> None:
        name = "stack-overflow-semantic-provisional-ai-annotations-development-model-x-v1.json"
        self.assertTrue(fnmatch.fnmatch(name, PROVISIONAL_ANNOTATION_GLOB))
        self.assertFalse(fnmatch.fnmatch(name, HUMAN_ANNOTATION_GLOB))
        self.assertEqual(list(DATA.glob(PROVISIONAL_ANNOTATION_GLOB)), [])
        self.assertEqual(list(DATA.glob("*provisional*")), [])

    def test_a_provisional_annotation_is_diagnostic_only_and_never_changes_the_human(self) -> None:
        provisional = {
            "reference_origin": "AI_ASSISTED_PROVISIONAL",
            "reference_strength": "AI_ASSISTED_PROVISIONAL",
            "use": "DIAGNOSTIC_ONLY",
            "split": "DEVELOPMENT",
            "records": [
                {
                    "normalized_record_id": r["normalized_record_id"],
                    "labels": {
                        lid: {"state": "PRESENT" if c["state"] != "PRESENT" else "ABSENT"}
                        for lid, c in r["labels"].items()
                    },
                }
                for r in OPERATOR_A["records"][:2]
            ],
        }
        name = "stack-overflow-semantic-provisional-ai-annotations-development-synthetic-v1.json"
        before = hashlib.sha256(json.dumps(OPERATOR_A, sort_keys=True).encode()).hexdigest()
        result = diagnostic_disagreements(OPERATOR_A, provisional, provisional_file_name=name)
        self.assertIs(result["is_human_agreement"], False)
        self.assertEqual(result["inter_annotator_agreement"], single_annotator_agreement())
        self.assertEqual(result["human_labels_changed"], 0)
        self.assertEqual(len(result["disagreements"]), 2 * 8)
        self.assertEqual(
            hashlib.sha256(json.dumps(OPERATOR_A, sort_keys=True).encode()).hexdigest(), before
        )
        refusals = {
            "AI_ANNOTATION_CLAIMS_A_HUMAN_ORIGIN": dict(
                provisional, reference_origin="HUMAN_OPERATOR"
            ),
            "A_MODEL_CANNOT_ATTEST": dict(provisional, attestation={}),
            "USE_NOT_DIAGNOSTIC_ONLY": dict(provisional, use="REFERENCE"),
        }
        for code, doc in refusals.items():
            self.assertIn(
                code,
                provisional_annotation_problems(doc, file_name=name, split_record_ids=SPLIT_IDS),
            )
        human_named = "stack-overflow-semantic-annotations-development-model-x-v1.json"
        self.assertIn(
            "NOT_STORED_SEPARATELY_FROM_HUMAN_REFERENCE",
            provisional_annotation_problems(
                provisional, file_name=human_named, split_record_ids=SPLIT_IDS
            ),
        )
        with self.assertRaises(ValueError):
            diagnostic_disagreements(as_ai(OPERATOR_A), provisional, provisional_file_name=name)


class TestThresholdPartition(unittest.TestCase):
    PACKAGE_PATH = DATA / "semantic-extraction-threshold-decision-package-v1.json"
    PARTITION = json.loads(
        (DATA / "semantic-extraction-threshold-partition-v1.json").read_text("utf-8")
    )

    def test_every_package_item_is_partitioned_with_its_value_unchanged(self) -> None:
        package = json.loads(self.PACKAGE_PATH.read_text("utf-8"))
        self.assertEqual(
            self.PARTITION["source_package_sha256"],
            hashlib.sha256(self.PACKAGE_PATH.read_bytes()).hexdigest(),
        )
        proposed = {(i["metric"], i["label"]): i["proposed"] for i in package["items"]}
        seen = set()
        for bucket in self.PARTITION["buckets"].values():
            for entry in bucket:
                key = (entry["metric"], entry["label"])
                self.assertEqual(entry["proposed"], proposed[key], key)
                self.assertEqual(entry["status"], "PROPOSED_NOT_AUTHORISED")
                seen.add(key)
        self.assertEqual(seen, set(proposed))
        self.assertIs(self.PARTITION["values_changed"], False)
        self.assertIs(self.PARTITION["decision_recorded"], False)

    def test_agreement_thresholds_never_enter_the_pilot(self) -> None:
        pilot = {e["metric"] for e in self.PARTITION["buckets"]["SINGLE_HUMAN_PILOT_VALID"]}
        multi = {e["metric"] for e in self.PARTITION["buckets"]["REQUIRES_MULTI_HUMAN_REFERENCE"]}
        self.assertNotIn("inter_annotator_kappa_per_extractable_label", pilot)
        self.assertIn("inter_annotator_kappa_per_extractable_label", multi)
        self.assertEqual(self.PARTITION["pilot_result_label"], PILOT_NOT_CERTIFICATION)
        for entry in self.PARTITION["buckets"]["SINGLE_HUMAN_PILOT_VALID"]:
            self.assertIn(entry["reference_needed"], {"NONE", "SINGLE_HUMAN_REFERENCE"})
        certified_on_holdout = {e["metric"] for e in self.PARTITION["buckets"]["REQUIRES_HOLDOUT"]}
        self.assertIn("false_present_rate_upper_95", certified_on_holdout)


if __name__ == "__main__":
    unittest.main()
