"""The interactive annotation form (N08-B follow-up), driven by a SCRIPTED synthetic annotator.

Every answer below is typed by the test, the way a person would type it. The form must store exactly
what was typed, refuse quotes the validator would refuse, save after every record, and produce a pack
the import validator accepts. It must never supply an answer of its own.
"""

from __future__ import annotations

import ast
import pathlib
import unittest

from sros_semantic_extraction_contract.annotation import (
    ATTESTATION_FLAGS,
    ATTESTATION_ID,
    annotator_record_order,
    validate_annotation_pack,
)
from sros_semantic_extraction_contract.annotation_session import SessionQuit, run_session
from sros_semantic_extraction_contract.labels import LABELS, LabelStatus
from sros_semantic_extraction_contract.surface import render_question_surface, surface_sha256

MODULE = (
    pathlib.Path(__file__).resolve().parents[1]
    / "sros_semantic_extraction_contract"
    / "annotation_session.py"
)
LABEL_IDS = [lab.label_id for lab in LABELS if lab.status is not LabelStatus.NOT_SAFE]
SURFACES = {
    "rec-a": render_question_surface(
        "Build fails",
        "<p>I tried rebuilding the image and it still fails. Honestly Docker Desktop is unusable here.</p>"
        "<blockquote><p>Podman is a nightmare to configure</p></blockquote>"
        "<pre><code>ERROR: this is awful, everything broke\n</code></pre>",
    ),
    "rec-b": render_question_surface(
        "List files", "<p>How do I list files? How do I list files fast?</p>"
    ),
}
BLANK = {
    "dataset_id": "d",
    "dataset_version": "1.0.0",
    "corpus": "c@1",
    "label_set": "first-person-semantic-labels@1.0.0",
    "text_surface": "se-question-text-surface@1.0.0",
}


def blank_cells() -> dict:
    return {
        lab.label_id: (
            {"state": "UNLABELLED", "evidence": [], "subject": None, "note": None}
            if lab.status is LabelStatus.EXTRACTABLE
            else {"state": "UNLABELLED", "note": None}
        )
        for lab in LABELS
        if lab.status is not LabelStatus.NOT_SAFE
    }


def working_pack() -> dict:
    order = annotator_record_order("DEVELOPMENT", "human-one", sorted(SURFACES))
    return {
        **BLANK,
        "split": "DEVELOPMENT",
        "synthetic": False,
        "reference_origin": "HUMAN_OPERATOR",
        "annotator_id": "human-one",
        "annotation_started_at": None,
        "annotation_completed_at": None,
        "record_order": order,
        "attestation": {
            "attestation_id": ATTESTATION_ID,
            "annotator_id": "human-one",
            "attested_at": None,
            **dict.fromkeys(ATTESTATION_FLAGS),
        },
        "records": [
            {
                "normalized_record_id": rid,
                "surface_sha256": surface_sha256(SURFACES[rid]),
                "labels": blank_cells(),
                "record_note": None,
            }
            for rid in order
        ],
    }


class Script:
    def __init__(self, answers: list[str]):
        self.answers, self.prompts, self.said, self.saves = list(answers), [], [], 0

    def ask(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self.answers:
            raise AssertionError(f"unscripted prompt: {prompt}")
        return self.answers.pop(0)

    def say(self, text: str) -> None:
        self.said.append(text)

    def save(self, pack: dict) -> None:
        self.saves += 1


def answers_for(rid: str) -> list[str]:
    if rid == "rec-a":
        return [
            "o",
            "this sentence is not in the text at all",
            "I tried rebuilding the image and it still fails",
            "n",
            "o",
            "ERROR: this is awful, everything broke",
            "Podman is a nightmare to configure",
            "Docker Desktop is unusable here",
            "n",
            "Docker Desktop",
            "n",
            "n",
            "?",
            "",
            "je ne sais pas si c'est répété",
            "n",
            "n",
            "n",
            "o",
        ]
    return ["n", "n", "t", "n", "n", "n", "n", "n", "n", "o"]


def full_script(pack: dict, attest: str = "o") -> Script:
    answers = []
    for rid in pack["record_order"]:
        answers += answers_for(rid)
    answers += [attest] * len(ATTESTATION_FLAGS)
    return Script(answers)


class TestAnnotationSession(unittest.TestCase):
    def test_a_scripted_human_produces_a_pack_the_validator_accepts(self) -> None:
        pack = working_pack()
        script = full_script(pack)
        self.assertEqual(
            run_session(pack, SURFACES, script.ask, script.say, script.save), "COMPLETE"
        )
        report = validate_annotation_pack(
            pack,
            split="DEVELOPMENT",
            split_record_ids=set(SURFACES),
            other_split_record_ids=set(),
            surfaces=SURFACES,
            blank_pack=BLANK,
        )
        self.assertTrue(report.accepted, report.refusals)
        cells = next(r for r in pack["records"] if r["normalized_record_id"] == "rec-a")["labels"]
        self.assertEqual(
            cells["REPORTED_FAILED_ATTEMPT"]["evidence"],
            [{"quote": "I tried rebuilding the image and it still fails", "occurrence": 1}],
        )
        self.assertEqual(
            cells["NEGATIVE_EVALUATION_OF_NAMED_SOLUTION"]["subject"],
            {"quote": "Docker Desktop", "occurrence": 1},
        )
        self.assertEqual(
            cells["REPEATED_DIFFICULTY_SAME_AUTHOR"],
            {"state": "UNCERTAIN", "note": "je ne sais pas si c'est répété"},
        )
        self.assertGreaterEqual(script.saves, 4)
        joined = "\n".join(script.said)
        self.assertIn("n'existe pas exactement", joined)
        self.assertIn("[CODE]", joined)
        self.assertIn("[QUOTE]", joined)

    def test_attestation_is_only_true_when_the_person_says_so(self) -> None:
        pack = working_pack()
        script = full_script(pack, attest="n")
        run_session(pack, SURFACES, script.ask, script.say, script.save)
        self.assertTrue(all(pack["attestation"][flag] is False for flag in ATTESTATION_FLAGS))
        report = validate_annotation_pack(
            pack,
            split="DEVELOPMENT",
            split_record_ids=set(SURFACES),
            other_split_record_ids=set(),
            surfaces=SURFACES,
            blank_pack=BLANK,
        )
        self.assertIn("ATTESTATION_INCOMPLETE", {code for code, _ in report.refusals})

    def test_quitting_keeps_confirmed_records_and_resuming_skips_them(self) -> None:
        pack = working_pack()
        first = pack["record_order"][0]
        script = Script([*answers_for(first), "q"])
        with self.assertRaises(SessionQuit):
            run_session(pack, SURFACES, script.ask, script.say, script.save)
        done = next(r for r in pack["records"] if r["normalized_record_id"] == first)
        self.assertTrue(all(c["state"] != "UNLABELLED" for c in done["labels"].values()))
        started = pack["annotation_started_at"]
        second = pack["record_order"][1]
        resume = Script([*answers_for(second), *["o"] * len(ATTESTATION_FLAGS)])
        run_session(pack, SURFACES, resume.ask, resume.say, resume.save)
        self.assertEqual(pack["annotation_started_at"], started)
        self.assertNotIn(
            f"QUESTION 1/{len(SURFACES)}",
            "\n".join(resume.said) if pack["record_order"][0] == first else "",
        )

    def test_a_repeated_quote_asks_which_occurrence_and_redo_discards_answers(self) -> None:
        pack = working_pack()
        pack["record_order"] = ["rec-b", "rec-a"]
        pack["records"] = [next(r for r in pack["records"] if r["normalized_record_id"] == "rec-b")]
        pack["record_order"] = ["rec-b"]
        script = Script(
            ["o", "How do I list files", "2", "n", *["n"] * 7, "r", *["n"] * 8, "o", *["o"] * 4]
        )
        run_session(pack, {"rec-b": SURFACES["rec-b"]}, script.ask, script.say, script.save)
        cells = pack["records"][0]["labels"]
        self.assertEqual(cells["REPORTED_FAILED_ATTEMPT"]["state"], "ABSENT")
        self.assertTrue(any("apparaît 2 fois" in p for p in script.prompts))

    def test_the_form_contains_no_default_answer(self) -> None:
        tree = ast.parse(MODULE.read_text("utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in {
                "_read",
                "_text",
                "_quote",
                "_cell",
            }:
                for arg in node.args.defaults + node.args.kw_defaults:
                    self.assertIsNone(arg, f"{node.name} has a default argument")


if __name__ == "__main__":
    unittest.main()
