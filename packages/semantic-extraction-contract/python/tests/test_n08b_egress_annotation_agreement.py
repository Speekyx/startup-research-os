"""Mission 1.85.4 (N08-B). Egress eligibility, human annotation import, agreement and adjudication.

Every pack in these tests is SYNTHETIC and says so. They test the machinery; none is a reference label,
and no test writes or reads a real human annotation, because none exists yet.
"""

from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import unittest

from sros_semantic_extraction_contract.agreement import (
    analyse_composition,
    build_adjudication_queue,
    cohen_kappa,
    krippendorff_alpha_nominal,
    reference_labels,
    validate_adjudication,
)
from sros_semantic_extraction_contract.annotation import (
    ATTESTATION_FLAGS,
    ATTESTATION_ID,
    AnnotationOrigin,
    HoldoutAccessError,
    annotator_record_order,
    validate_annotation_pack,
)
from sros_semantic_extraction_contract.egress import (
    EgressDecisionError,
    derive_egress_eligibility,
    load_decisions,
    pattern_table_sha256,
    scan_surface,
    transmission_integrity_problems,
)
from sros_semantic_extraction_contract.labels import LABELS, LabelStatus
from sros_semantic_extraction_contract.surface import render_question_surface, surface_sha256

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DATA = REPO_ROOT / "docs" / "data"
PACKAGE = pathlib.Path(__file__).resolve().parents[1] / "sros_semantic_extraction_contract"
SCAN_ID = "residual-identifier-scan"


def decisions_doc(**extra):
    doc = {
        "scan": f"{SCAN_ID}@1.0.0",
        "pattern_table_sha256": pattern_table_sha256(),
        "surface": "se-question-text-surface@1.0.0",
        "decisions": [],
        "bulk_decisions": [],
    }
    doc.update(extra)
    return doc


class TestEgress(unittest.TestCase):
    def test_the_scan_is_a_trigger_on_the_exact_surface_and_never_alters_it(self) -> None:
        surface = render_question_surface(
            "t", "<p>mail me at someone@example.com from 10.0.0.1 in /home/alice</p>"
        )
        before = surface_sha256(surface)
        found = scan_surface(surface)
        self.assertEqual(len(found["email_like"]), 1)
        self.assertEqual(len(found["ipv4_like"]), 1)
        self.assertEqual(len(found["user_home_path"]), 1)
        self.assertEqual(surface_sha256(surface), before)

    def test_transport_delimiters_exclude_mechanically(self) -> None:
        self.assertTrue(transmission_integrity_problems("t\n\n[CODE]\n>>> print(1)\n[/CODE]"))
        self.assertFalse(transmission_integrity_problems("plain text"))

    def test_no_record_is_approved_without_a_human_decision(self) -> None:
        records = [
            {
                "normalized_record_id": "r1",
                "surface_sha256": "a" * 64,
                "trigger_counts": {"url": 0},
                "transmission_problems": [],
            }
        ]
        [row] = derive_egress_eligibility(
            records,
            load_decisions(decisions_doc(), scan_id=SCAN_ID, pattern_digest=pattern_table_sha256()),
        )
        self.assertEqual(row["state"], "EGRESS_REVIEW_REQUIRED")

    def test_human_decisions_bind_to_the_surface_and_machines_may_only_exclude(self) -> None:
        records = [
            {
                "normalized_record_id": "r1",
                "surface_sha256": "a" * 64,
                "trigger_counts": {"url": 1},
                "transmission_problems": [],
            },
            {
                "normalized_record_id": "r2",
                "surface_sha256": "b" * 64,
                "trigger_counts": {"url": 0},
                "transmission_problems": ["SURFACE_CONTAINS_TRANSPORT_DELIMITER"],
            },
        ]
        human = {
            "decision_origin": "HUMAN_OPERATOR",
            "decided_by": "operator",
            "decided_at": "2026-09-16T00:00:00Z",
        }
        doc = decisions_doc(
            decisions=[
                {
                    "normalized_record_id": "r1",
                    "surface_sha256": "a" * 64,
                    "decision": "EGRESS_APPROVED",
                    "reason": "TRIGGER_REVIEWED_PUBLIC_REFERENCE",
                    **human,
                },
                {
                    "normalized_record_id": "r2",
                    "surface_sha256": "b" * 64,
                    "decision": "EGRESS_APPROVED",
                    "reason": "TRIGGER_REVIEWED_NOT_PERSONAL",
                    **human,
                },
            ]
        )
        rows = derive_egress_eligibility(
            records, load_decisions(doc, scan_id=SCAN_ID, pattern_digest=pattern_table_sha256())
        )
        self.assertEqual([r["state"] for r in rows], ["EGRESS_APPROVED", "EGRESS_EXCLUDED"])
        stale = [dict(records[0], surface_sha256="c" * 64)]
        self.assertEqual(
            derive_egress_eligibility(
                stale, load_decisions(doc, scan_id=SCAN_ID, pattern_digest=pattern_table_sha256())
            )[0]["state"],
            "EGRESS_REVIEW_REQUIRED",
        )

    def test_non_human_origins_and_recorded_review_required_are_refused(self) -> None:
        for bad in (
            {
                "normalized_record_id": "r1",
                "surface_sha256": "a",
                "decision": "EGRESS_APPROVED",
                "reason": "TRIGGER_REVIEWED_NOT_PERSONAL",
                "decision_origin": "LLM",
                "decided_by": "x",
                "decided_at": "t",
            },
            {
                "normalized_record_id": "r1",
                "surface_sha256": "a",
                "decision": "EGRESS_REVIEW_REQUIRED",
                "reason": "OPERATOR_DISCRETION",
                "decision_origin": "HUMAN_OPERATOR",
                "decided_by": "x",
                "decided_at": "t",
            },
            {
                "normalized_record_id": "r1",
                "surface_sha256": "a",
                "decision": "EGRESS_APPROVED",
                "reason": "CONTAINS_PERSONAL_IDENTIFIER",
                "decision_origin": "HUMAN_OPERATOR",
                "decided_by": "x",
                "decided_at": "t",
            },
        ):
            with self.subTest(bad), self.assertRaises(EgressDecisionError):
                load_decisions(
                    decisions_doc(decisions=[bad]),
                    scan_id=SCAN_ID,
                    pattern_digest=pattern_table_sha256(),
                )

    def test_a_bulk_decision_covers_only_listed_zero_trigger_records(self) -> None:
        ids = ["r1", "r2"]
        bulk = {
            "bulk_decision_id": "b1",
            "normalized_record_ids": ids,
            "record_set_sha256": hashlib.sha256("\n".join(ids).encode()).hexdigest(),
            "surface_sha256": {"r1": "a", "r2": "b"},
            "reason": "BULK_ZERO_TRIGGER_ACCEPTED",
            "decision_origin": "HUMAN_OPERATOR",
            "decided_by": "op",
            "decided_at": "t",
        }
        decisions = load_decisions(
            decisions_doc(bulk_decisions=[bulk]),
            scan_id=SCAN_ID,
            pattern_digest=pattern_table_sha256(),
        )
        records = [
            {
                "normalized_record_id": "r1",
                "surface_sha256": "a",
                "trigger_counts": {},
                "transmission_problems": [],
            },
            {
                "normalized_record_id": "r2",
                "surface_sha256": "b",
                "trigger_counts": {"url": 1},
                "transmission_problems": [],
            },
            {
                "normalized_record_id": "r3",
                "surface_sha256": "c",
                "trigger_counts": {},
                "transmission_problems": [],
            },
        ]
        self.assertEqual(
            [r["state"] for r in derive_egress_eligibility(records, decisions)],
            ["EGRESS_APPROVED", "EGRESS_REVIEW_REQUIRED", "EGRESS_REVIEW_REQUIRED"],
        )
        with self.assertRaises(EgressDecisionError):
            load_decisions(
                decisions_doc(bulk_decisions=[dict(bulk, record_set_sha256="0" * 64)]),
                scan_id=SCAN_ID,
                pattern_digest=pattern_table_sha256(),
            )

    def test_committed_egress_artifacts_hold_no_text_and_no_decisions(self) -> None:
        decisions = json.loads(
            (DATA / "stack-overflow-semantic-egress-decisions-development-v1.json").read_text(
                "utf-8"
            )
        )
        self.assertEqual((decisions["decisions"], decisions["bulk_decisions"]), ([], []))
        eligibility = json.loads(
            (DATA / "stack-overflow-semantic-egress-eligibility-development-v1.json").read_text(
                "utf-8"
            )
        )
        self.assertEqual(eligibility["approved_record_ids"], [])
        self.assertNotIn("EGRESS_APPROVED", eligibility["state_counts"])
        scan = json.loads(
            (DATA / "stack-overflow-semantic-egress-scan-development-v1.json").read_text("utf-8")
        )
        self.assertEqual(scan["pattern_table_sha256"], pattern_table_sha256())
        self.assertEqual(len(scan["records"]), 50)
        for record in scan["records"]:
            self.assertEqual(
                set(record),
                {
                    "normalized_record_id",
                    "surface_sha256",
                    "trigger_counts",
                    "transmission_problems",
                },
            )

    def test_no_redaction_function_exists(self) -> None:
        for module in PACKAGE.glob("*.py"):
            names = {
                n.name
                for n in ast.walk(ast.parse(module.read_text("utf-8")))
                if isinstance(n, ast.FunctionDef)
            }
            self.assertFalse(
                {
                    n
                    for n in names
                    if any(w in n for w in ("redact", "mask", "scrub", "sanitize", "anonymi"))
                },
                module.name,
            )


SURFACE = render_question_surface(
    "Build fails",
    "<p>I tried rebuilding the image and it still fails with the same error.</p><p>Honestly Docker Desktop is unusable here.</p>",
)
RID = ["rec-a", "rec-b"]
SURFACES = {
    "rec-a": SURFACE,
    "rec-b": render_question_surface(
        "How to list files", "<p>What is the idiomatic way to list files?</p>"
    ),
}
BLANK = {
    "dataset_id": "d",
    "dataset_version": "1.0.0",
    "corpus": "c@1",
    "label_set": "first-person-semantic-labels@1.0.0",
    "text_surface": "se-question-text-surface@1.0.0",
}


def blank_cells():
    return {
        lab.label_id: (
            {"state": "ABSENT", "evidence": [], "subject": None, "note": None}
            if lab.status is LabelStatus.EXTRACTABLE
            else {"state": "ABSENT", "note": None}
        )
        for lab in LABELS
        if lab.status is not LabelStatus.NOT_SAFE
    }


def synthetic_pack(annotator="human-one", **overrides):
    records = []
    for rid in RID:
        cells = blank_cells()
        if rid == "rec-a":
            cells["REPORTED_FAILED_ATTEMPT"] = {
                "state": "PRESENT",
                "evidence": [
                    {"quote": "I tried rebuilding the image and it still fails", "occurrence": 1}
                ],
                "subject": None,
                "note": None,
            }
        records.append(
            {
                "normalized_record_id": rid,
                "surface_sha256": surface_sha256(SURFACES[rid]),
                "labels": cells,
                "record_note": None,
            }
        )
    pack = {
        **BLANK,
        "split": "DEVELOPMENT",
        "synthetic": False,
        "reference_origin": "HUMAN_OPERATOR",
        "annotator_id": annotator,
        "annotation_started_at": "2026-09-16T10:00:00Z",
        "annotation_completed_at": "2026-09-16T11:00:00Z",
        "record_order": annotator_record_order("DEVELOPMENT", annotator, sorted(RID)),
        "attestation": {
            "attestation_id": ATTESTATION_ID,
            "annotator_id": annotator,
            "attested_at": "2026-09-16T11:00:00Z",
            **dict.fromkeys(ATTESTATION_FLAGS, True),
        },
        "records": records,
    }
    pack.update(overrides)
    return pack


def run(pack):
    return validate_annotation_pack(
        pack,
        split="DEVELOPMENT",
        split_record_ids=set(RID),
        other_split_record_ids={"hold-1"},
        surfaces=SURFACES,
        blank_pack=BLANK,
    )


class TestAnnotationImport(unittest.TestCase):
    def test_a_complete_synthetic_pack_commits_offsets_and_digests_only(self) -> None:
        report = run(synthetic_pack())
        self.assertTrue(report.accepted, report.refusals)
        text = json.dumps(report.committed)
        self.assertNotIn("I tried rebuilding", text)
        cell = next(r for r in report.committed["records"] if r["normalized_record_id"] == "rec-a")[
            "labels"
        ]["REPORTED_FAILED_ATTEMPT"]
        span = cell["spans"][0]
        self.assertEqual(
            SURFACE[span["start"] : span["end"]], "I tried rebuilding the image and it still fails"
        )

    def test_refusals(self) -> None:
        def with_cell(label, cell):
            pack = synthetic_pack()
            pack["records"][0]["labels"][label] = cell
            return pack

        cases = {
            "ORIGIN_NOT_HUMAN": synthetic_pack(reference_origin="AI_ASSISTED_PROVISIONAL"),
            "ORIGIN_MISSING": synthetic_pack(reference_origin=None),
            "ANNOTATOR_ID_NOT_ACCEPTED": synthetic_pack(annotator="claude-helper"),
            "ATTESTATION_INCOMPLETE": synthetic_pack(
                attestation={"attestation_id": ATTESTATION_ID}
            ),
            "UNLABELLED_CELL": with_cell("SWITCHING_INTENT", {"state": "UNLABELLED", "note": None}),
            "PRESENT_WITHOUT_SPAN": with_cell(
                "REPORTED_FAILED_ATTEMPT",
                {"state": "PRESENT", "evidence": [], "subject": None, "note": None},
            ),
            "QUOTE_NOT_IN_SURFACE": with_cell(
                "REPORTED_FAILED_ATTEMPT",
                {
                    "state": "PRESENT",
                    "evidence": [{"quote": "a sentence nobody wrote here", "occurrence": 1}],
                    "subject": None,
                    "note": None,
                },
            ),
            "SUBJECT_REQUIRED": with_cell(
                "NEGATIVE_EVALUATION_OF_NAMED_SOLUTION",
                {
                    "state": "PRESENT",
                    "evidence": [{"quote": "Docker Desktop is unusable here", "occurrence": 1}],
                    "subject": None,
                    "note": None,
                },
            ),
            "UNCERTAIN_WITHOUT_NOTE": with_cell(
                "SWITCHING_INTENT", {"state": "UNCERTAIN", "note": ""}
            ),
            "INCIDENCE_LABEL_WITH_SPAN": with_cell(
                "SWITCHING_INTENT", {"state": "ABSENT", "note": None, "evidence": []}
            ),
            "SPAN_WITH_NON_PRESENT_STATE": with_cell(
                "REPORTED_FAILED_ATTEMPT",
                {
                    "state": "ABSENT",
                    "evidence": [{"quote": "I tried rebuilding the image", "occurrence": 1}],
                    "subject": None,
                    "note": None,
                },
            ),
            "MODEL_FIELD_PRESENT": synthetic_pack(confidence=0.9),
            "SHUFFLE_ORDER_MISMATCH": synthetic_pack(
                record_order=list(
                    reversed(annotator_record_order("DEVELOPMENT", "human-one", sorted(RID)))
                )
            ),
        }
        for code, pack in cases.items():
            with self.subTest(code):
                report = run(pack)
                self.assertFalse(report.accepted)
                self.assertIn(code, {c for c, _ in report.refusals})

    def test_holdout_material_is_refused_before_anything_else(self) -> None:
        with self.assertRaises(HoldoutAccessError):
            run(synthetic_pack(split="HOLDOUT"))
        pack = synthetic_pack()
        pack["records"].append(
            {
                "normalized_record_id": "hold-1",
                "surface_sha256": "x",
                "labels": {},
                "record_note": None,
            }
        )
        with self.assertRaises(HoldoutAccessError):
            run(pack)
        with self.assertRaises(HoldoutAccessError):
            validate_annotation_pack(
                synthetic_pack(),
                split="HOLDOUT",
                split_record_ids=set(RID),
                other_split_record_ids=set(),
                surfaces=SURFACES,
                blank_pack=BLANK,
            )

    def test_no_module_writes_a_label_state(self) -> None:
        for module in ("annotation.py", "agreement.py"):
            tree = ast.parse((PACKAGE / module).read_text("utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (
                            isinstance(target, ast.Subscript)
                            and isinstance(target.slice, ast.Constant)
                            and target.slice.value == "state"
                        ):
                            self.fail(f"{module} assigns a label state")


def committed(annotator, states):
    records = []
    for rid, state in states.items():
        labels = {
            lab.label_id: {"state": "ABSENT", "spans": [], "subject": None, "note_present": False}
            if lab.status is LabelStatus.EXTRACTABLE
            else {"state": "ABSENT", "note_present": False}
            for lab in LABELS
            if lab.status is not LabelStatus.NOT_SAFE
        }
        labels["REPORTED_FAILED_ATTEMPT"] = {
            "state": state,
            "spans": [
                {"start": 0, "end": 10, "occurrence": 1, "quote_sha256": "q", "quote_length": 10}
            ]
            if state == "PRESENT"
            else [],
            "subject": None,
            "note_present": state == "UNCERTAIN",
        }
        records.append({"normalized_record_id": rid, "surface_sha256": "s", "labels": labels})
    return {"annotator_id": annotator, "split": "DEVELOPMENT", "records": records}


CONTRACT = json.loads(
    (DATA / "first-person-semantic-extraction-contract-v1.json").read_text("utf-8")
)


class TestAgreement(unittest.TestCase):
    def test_kappa_and_alpha_on_known_values(self) -> None:
        a = ["PRESENT", "PRESENT", "ABSENT", "ABSENT"]
        b = ["PRESENT", "ABSENT", "ABSENT", "ABSENT"]
        self.assertEqual(cohen_kappa(a, b, ("PRESENT", "ABSENT")), 0.5)
        self.assertEqual(
            cohen_kappa(["ABSENT"] * 4, ["ABSENT"] * 4, ("PRESENT", "ABSENT")), "UNDEFINED"
        )
        self.assertEqual(krippendorff_alpha_nominal([["A", "A"], ["B", "B"]]), 1.0)

    def test_composition_reads_threshold_status_and_issues_no_verdict(self) -> None:
        one = committed("h1", {"r1": "PRESENT", "r2": "ABSENT", "r3": "UNCERTAIN"})
        two = committed("h2", {"r1": "PRESENT", "r2": "PRESENT", "r3": "ABSENT"})
        report = analyse_composition([one, two], CONTRACT)
        self.assertEqual(report["gates"]["composition"]["verdict"], "GATE_NOT_AUTHORISED")
        self.assertEqual(report["gates"]["agreement_floor"]["verdict"], "GATE_NOT_AUTHORISED")
        label = report["labels"]["REPORTED_FAILED_ATTEMPT"]
        self.assertEqual(label["state_counts"]["h1"], {"PRESENT": 1, "ABSENT": 1, "UNCERTAIN": 1})
        self.assertIn("pabak", label["pairwise"])
        with self.assertRaises(ValueError):
            analyse_composition([one], CONTRACT)

    def test_queue_and_reference_never_consult_anything_but_human_files(self) -> None:
        one = committed("h1", {"r1": "PRESENT", "r2": "ABSENT"})
        two = committed("h2", {"r1": "PRESENT", "r2": "PRESENT"})
        queue = build_adjudication_queue([one, two])
        self.assertEqual(
            [(q["label_id"], q["normalized_record_id"]) for q in queue],
            [("REPORTED_FAILED_ATTEMPT", "r2")],
        )
        self.assertEqual(
            reference_labels([one, two], None)["REPORTED_FAILED_ATTEMPT"],
            {"r1": "PRESENT", "r2": "UNCERTAIN"},
        )
        adjudication = {
            "split": "DEVELOPMENT",
            "method": "THIRD_HUMAN",
            "adjudicator_id": "h3",
            "adjudicator_origin": "HUMAN_OPERATOR",
            "model_output_consulted": False,
            "queue_sha256": hashlib.sha256(json.dumps(queue, sort_keys=True).encode()).hexdigest(),
            "items": [
                {
                    "label_id": "REPORTED_FAILED_ATTEMPT",
                    "normalized_record_id": "r2",
                    "resolution": "RESOLVED_TO_EXISTING_STATE",
                    "resolved_state": "ABSENT",
                }
            ],
        }
        self.assertEqual(validate_adjudication(adjudication, [one, two]), [])
        self.assertTrue(validate_adjudication(dict(adjudication, adjudicator_id="h1"), [one, two]))
        self.assertTrue(
            validate_adjudication(dict(adjudication, model_output_consulted=None), [one, two])
        )


class TestN08BState(unittest.TestCase):
    def test_committed_annotations_are_attested_human_development_files_and_the_blank_packs_are_untouched(
        self,
    ) -> None:
        self.assertEqual(list(DATA.glob("stack-overflow-semantic-annotations-holdout-*")), [])
        for path in DATA.glob("stack-overflow-semantic-annotations-*"):
            committed = json.loads(path.read_text("utf-8"))
            self.assertEqual(committed["split"], "DEVELOPMENT", path.name)
            self.assertIn(committed["reference_origin"], {o.value for o in AnnotationOrigin})
            self.assertTrue(
                all(committed["attestation"][flag] is True for flag in ATTESTATION_FLAGS), path.name
            )
            text = path.read_text("utf-8")
            self.assertNotIn('"quote"', text, path.name)
            self.assertNotIn('"note"', text, path.name)
        self.assertEqual(
            list(DATA.glob("stack-overflow-semantic-adjudication-development-v1.json")), []
        )
        pinned = {
            "stack-overflow-semantic-label-pack-development-v1.json": "fdec6ef653dc5b1042efd150c975e3009cae31b5cae250a64be1e0e6342a8a7d",
            "stack-overflow-semantic-label-pack-holdout-v1.json": "ada59b86a12e31f1e4f189c0e5500dfaf26133b8dcb0cfe14d83f4e34fba3e17",
            "stack-overflow-semantic-evaluation-corpus-v1.json": "3e0b0a903a3a976cccc2ecff4721397ff3b85096634c286201b4e7433cb0438c",
        }
        for name, digest in pinned.items():
            self.assertEqual(hashlib.sha256((DATA / name).read_bytes()).hexdigest(), digest, name)

    def test_d12_remains_open_as_recorded(self) -> None:
        audit = (REPO_ROOT / "docs" / "architecture" / "specification-audit.md").read_text("utf-8")
        self.assertIn("| D-12 | Embedding model versioning", audit)
        contract = json.loads(
            (DATA / "first-person-semantic-extraction-contract-v1.json").read_text("utf-8")
        )
        self.assertEqual(contract["d12_decision_map"]["d12"]["status"], "OPEN, never decided")

    def test_the_threshold_package_authorises_nothing(self) -> None:
        package = json.loads(
            (DATA / "semantic-extraction-threshold-decision-package-v1.json").read_text("utf-8")
        )
        self.assertFalse(package["decision_recorded"])
        for item in package["items"]:
            self.assertEqual(item["status"], "PROPOSED_NOT_AUTHORISED")
            for key in (
                "rationale",
                "false_positive_risk",
                "false_negative_risk",
                "development_can_estimate",
                "holdout_can_test",
                "pass",
                "fail",
                "insufficient",
            ):
                self.assertIn(key, item)

    def test_the_requalification_is_a_successor_and_sent_nothing(self) -> None:
        requal = json.loads(
            (DATA / "anthropic-api-route-requalification-v1.json").read_text("utf-8")
        )
        self.assertEqual((requal["inference_calls"], requal["stack_overflow_text_sent"]), (0, 0))
        self.assertFalse(requal["predecessor"]["edited"])
        self.assertEqual(
            requal["predecessor"]["sha256"],
            hashlib.sha256((DATA / "model-provider-policy-v1.json").read_bytes()).hexdigest(),
        )
        self.assertTrue(all(len(e["sha256"]) == 64 for e in requal["evidence"]))
        self.assertIn("error", " ".join(requal["conditions_the_packet_must_bind"]))


if __name__ == "__main__":
    unittest.main()
