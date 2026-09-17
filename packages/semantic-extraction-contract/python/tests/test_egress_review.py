"""Mission 1.85.6: the human egress review path, on SYNTHETIC surfaces only.

Every choice below is typed by the test the way the operator would click it. The tests prove the tooling
records only explicit choices, refuses what the contract refuses, and never turns a trigger count, a zero
count or a bulk set into a decision by itself.
"""

from __future__ import annotations

import ast
import copy
import pathlib
import unittest

from sros_semantic_extraction_contract.egress import (
    SCAN_ID,
    SCAN_VERSION,
    derive_egress_eligibility,
    load_decisions,
    pattern_table_sha256,
    scan_surface,
    transmission_integrity_problems,
)
from sros_semantic_extraction_contract.egress_review import (
    CONFIRMATION,
    ChoiceRefusedError,
    blank_working_file,
    committed_decisions,
    make_bulk_decision,
    make_decision,
    record_set_sha256,
    reviewable_records,
    unresolved_record_ids,
    validate_working_decisions,
    zero_trigger_unresolved_ids,
)
from sros_semantic_extraction_contract.surface import render_question_surface, surface_sha256

MODULE = (
    pathlib.Path(__file__).resolve().parents[1]
    / "sros_semantic_extraction_contract"
    / "egress_review.py"
)
SURFACES = {
    "r-zero-1": render_question_surface("Loop question", "<p>How do I loop over a list?</p>"),
    "r-zero-2": render_question_surface("Sort question", "<p>How do I sort a dict by value?</p>"),
    "r-url": render_question_surface("Docs", "<p>See https://docs.python.org/3/ for details.</p>"),
    "r-secret": render_question_surface(
        "Config", "<pre><code>password: hunter2hunter2\n</code></pre>"
    ),
    "r-delim": render_question_surface("Shell", "<pre><code>&gt;&gt;&gt; print(1)\n</code></pre>"),
}
HOLDOUT = {"h-1"}
AT = "2026-09-17T10:00:00+02:00"


def scan_records(surfaces=SURFACES):
    return [
        {
            "normalized_record_id": rid,
            "surface_sha256": surface_sha256(surface),
            "trigger_counts": {name: len(found) for name, found in scan_surface(surface).items()},
            "transmission_problems": sorted(
                {p.split(":")[0] for p in transmission_integrity_problems(surface)}
            ),
        }
        for rid, surface in sorted(surfaces.items())
    ]


def blank_committed():
    return {
        "scan": f"{SCAN_ID}@{SCAN_VERSION}",
        "pattern_table_sha256": pattern_table_sha256(),
        "surface": "se-question-text-surface@1.0.0",
        "policy": "REVIEW_OR_EXCLUDE_NO_REDACTION",
        "decisions": [],
        "bulk_decisions": [],
    }


def setup(operator="operator-a"):
    records = scan_records()
    reviewable = reviewable_records(records, blank_committed())
    working = blank_working_file(operator, reviewable, "scan-digest")
    return records, {r["normalized_record_id"]: r for r in records}, working


def validate(working, records, complete=True):
    return validate_working_decisions(
        working,
        scan_records=records,
        committed_doc=blank_committed(),
        holdout_record_ids=HOLDOUT,
        require_complete=complete,
    )


def codes(problems):
    return {code for code, _ in problems}


def decide(working, by_id, rid, decision, reason):
    working["decisions"].append(
        make_decision(
            working,
            by_id[rid],
            surface_sha256=by_id[rid]["surface_sha256"],
            decision=decision,
            reason=reason,
            decided_at=AT,
        )
    )


def bulk(working, by_id, ids, confirmation=None):
    return make_bulk_decision(
        working,
        by_id,
        record_ids=ids,
        surface_sha256={rid: by_id[rid]["surface_sha256"] for rid in ids},
        record_set_digest=record_set_sha256(ids),
        confirmation=confirmation if confirmation is not None else CONFIRMATION.format(n=len(ids)),
        decided_at=AT,
    )


class TestFixtureShape(unittest.TestCase):
    def test_the_synthetic_scan_has_each_case(self) -> None:
        _, by_id, _ = setup()
        self.assertFalse(any(by_id["r-zero-1"]["trigger_counts"].values()))
        self.assertTrue(by_id["r-url"]["trigger_counts"]["url"])
        self.assertTrue(by_id["r-secret"]["trigger_counts"]["secret_like"])
        self.assertTrue(by_id["r-delim"]["transmission_problems"])


class TestNothingIsDecidedWithoutAnOperatorChoice(unittest.TestCase):
    def test_a_prepared_working_file_holds_no_decision(self) -> None:
        records, _, working = setup()
        self.assertEqual(working["decisions"], [])
        self.assertEqual(working["bulk_decisions"], [])
        self.assertEqual(
            unresolved_record_ids(working), ["r-secret", "r-url", "r-zero-1", "r-zero-2"]
        )
        self.assertIn("REVIEW_INCOMPLETE", codes(validate(working, records)))
        self.assertEqual(validate(working, records, complete=False), [])

    def test_zero_triggers_is_listed_for_review_never_decided(self) -> None:
        _, by_id, working = setup()
        self.assertEqual(zero_trigger_unresolved_ids(working, by_id), ["r-zero-1", "r-zero-2"])
        self.assertEqual(working["decisions"], [])

    def test_the_module_has_no_loop_that_writes_decisions(self) -> None:
        tree = ast.parse(MODULE.read_text("utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.For | ast.comprehension):
                for call in ast.walk(node if isinstance(node, ast.For) else node.iter):
                    if isinstance(call, ast.Call) and getattr(call.func, "id", "") in {
                        "make_decision",
                        "make_bulk_decision",
                    }:
                        self.fail("a decision is constructed inside a loop")

    def test_deterministic_exclusion_dominates_a_human_approval(self) -> None:
        records, by_id, working = setup()
        self.assertNotIn("r-delim", working["reviewable_record_ids"])
        with self.assertRaises(ChoiceRefusedError) as refused:
            decide(working, by_id, "r-delim", "EGRESS_APPROVED", "TRIGGER_REVIEWED_NOT_PERSONAL")
        self.assertEqual(refused.exception.code, "RECORD_NOT_REVIEWABLE")
        forged = blank_committed()
        forged["decisions"] = [
            {
                "normalized_record_id": "r-delim",
                "surface_sha256": by_id["r-delim"]["surface_sha256"],
                "decision": "EGRESS_APPROVED",
                "reason": "TRIGGER_REVIEWED_NOT_PERSONAL",
                "decision_origin": "HUMAN_OPERATOR",
                "decided_by": "operator-a",
                "decided_at": AT,
            }
        ]
        derived = derive_egress_eligibility(
            records,
            load_decisions(forged, scan_id=SCAN_ID, pattern_digest=pattern_table_sha256()),
        )
        row = next(r for r in derived if r["normalized_record_id"] == "r-delim")
        self.assertEqual(row["state"], "EGRESS_EXCLUDED")
        self.assertEqual(row["decision_origin"], "DETERMINISTIC_RULE")
        forged_working = copy.deepcopy(working)
        forged_working["decisions"] = forged["decisions"]
        self.assertIn("RECORD_NOT_REVIEWABLE", codes(validate(forged_working, records, False)))


class TestBulkAndSecretRules(unittest.TestCase):
    def test_bulk_needs_the_exact_confirmation_sentence(self) -> None:
        _, by_id, working = setup()
        for confirmation in ("", "yes", CONFIRMATION.format(n=3)):
            with self.assertRaises(ChoiceRefusedError) as refused:
                bulk(working, by_id, ["r-zero-1", "r-zero-2"], confirmation)
            self.assertEqual(refused.exception.code, "BULK_CONFIRMATION_MISSING")
        self.assertEqual(working["bulk_decisions"], [])

    def test_a_triggered_record_cannot_enter_a_zero_trigger_bulk(self) -> None:
        records, by_id, working = setup()
        with self.assertRaises(ChoiceRefusedError) as refused:
            bulk(working, by_id, ["r-url", "r-zero-1", "r-zero-2"])
        self.assertEqual(refused.exception.code, "BULK_SET_CONTAINS_A_TRIGGERED_OR_UNKNOWN_RECORD")
        with self.assertRaises(ChoiceRefusedError) as refused:
            bulk(working, by_id, ["r-zero-1"])
        self.assertEqual(refused.exception.code, "BULK_SET_IS_NOT_THE_CURRENT_ZERO_TRIGGER_SET")
        forged = copy.deepcopy(working)
        good = bulk(working, by_id, ["r-zero-1", "r-zero-2"])
        ids = ["r-url", "r-zero-1", "r-zero-2"]
        forged["bulk_decisions"] = [
            dict(
                good,
                normalized_record_ids=ids,
                surface_sha256={rid: by_id[rid]["surface_sha256"] for rid in ids},
                record_set_sha256=record_set_sha256(ids),
                confirmation=CONFIRMATION.format(n=3),
            )
        ]
        self.assertIn("BULK_CONTAINS_A_TRIGGERED_RECORD", codes(validate(forged, records, False)))

    def test_secret_like_approval_needs_an_individual_not_personal_review(self) -> None:
        records, by_id, working = setup()
        with self.assertRaises(ChoiceRefusedError) as refused:
            decide(
                working, by_id, "r-secret", "EGRESS_APPROVED", "TRIGGER_REVIEWED_PUBLIC_REFERENCE"
            )
        self.assertEqual(
            refused.exception.code, "SECRET_LIKE_APPROVAL_NEEDS_TRIGGER_REVIEWED_NOT_PERSONAL"
        )
        forged = copy.deepcopy(working)
        forged["decisions"] = [
            {
                "normalized_record_id": "r-secret",
                "surface_sha256": by_id["r-secret"]["surface_sha256"],
                "decision": "EGRESS_APPROVED",
                "reason": "TRIGGER_REVIEWED_PUBLIC_REFERENCE",
                "decision_origin": "HUMAN_OPERATOR",
                "decided_by": "operator-a",
                "decided_at": AT,
            }
        ]
        self.assertIn(
            "SECRET_LIKE_APPROVAL_NEEDS_TRIGGER_REVIEWED_NOT_PERSONAL",
            codes(validate(forged, records, False)),
        )
        decide(working, by_id, "r-secret", "EGRESS_APPROVED", "TRIGGER_REVIEWED_NOT_PERSONAL")
        self.assertEqual(validate(working, records, False), [])


class TestImportValidation(unittest.TestCase):
    def test_a_stale_surface_digest_is_refused(self) -> None:
        records, by_id, working = setup()
        with self.assertRaises(ChoiceRefusedError) as refused:
            make_decision(
                working,
                by_id["r-url"],
                surface_sha256="0" * 64,
                decision="EGRESS_EXCLUDED",
                reason="OPERATOR_DISCRETION",
            )
        self.assertEqual(refused.exception.code, "SURFACE_DIGEST_MISMATCH")
        decide(working, by_id, "r-url", "EGRESS_EXCLUDED", "OPERATOR_DISCRETION")
        changed = {**SURFACES, "r-url": SURFACES["r-url"] + " edited"}
        self.assertIn(
            "SURFACE_DIGEST_STALE", codes(validate(working, scan_records(changed), False))
        )
        # and a committed decision bound to the old surface derives back to review-required
        committed = committed_decisions(working, blank_committed())
        derived = derive_egress_eligibility(
            scan_records(changed),
            load_decisions(committed, scan_id=SCAN_ID, pattern_digest=pattern_table_sha256()),
        )
        row = next(r for r in derived if r["normalized_record_id"] == "r-url")
        self.assertEqual(row["state"], "EGRESS_REVIEW_REQUIRED")
        self.assertEqual(row["basis"], "DECISION_BOUND_TO_A_DIFFERENT_SURFACE")

    def test_holdout_is_refused(self) -> None:
        records, _, working = setup()
        self.assertIn(
            "HOLDOUT_OR_UNKNOWN_SPLIT_REFUSED",
            codes(validate(dict(working, split="HOLDOUT"), records, False)),
        )
        forged = copy.deepcopy(working)
        forged["reviewable_record_ids"].append("h-1")
        self.assertIn("HOLDOUT_RECORD_REFUSED", codes(validate(forged, records, False)))

    def test_invalid_decision_reason_combinations_are_refused_not_repaired(self) -> None:
        records, by_id, working = setup()
        for decision, reason in (
            ("EGRESS_APPROVED", "CONTAINS_PERSONAL_IDENTIFIER"),
            ("EGRESS_APPROVED", "BULK_ZERO_TRIGGER_ACCEPTED"),
            ("EGRESS_EXCLUDED", "TRIGGER_REVIEWED_NOT_PERSONAL"),
            ("EGRESS_REVIEW_REQUIRED", "OPERATOR_DISCRETION"),
        ):
            with self.assertRaises(ChoiceRefusedError):
                make_decision(
                    working,
                    by_id["r-url"],
                    surface_sha256=by_id["r-url"]["surface_sha256"],
                    decision=decision,
                    reason=reason,
                )
            forged = copy.deepcopy(working)
            forged["decisions"] = [
                {
                    "normalized_record_id": "r-url",
                    "surface_sha256": by_id["r-url"]["surface_sha256"],
                    "decision": decision,
                    "reason": reason,
                    "decision_origin": "HUMAN_OPERATOR",
                    "decided_by": "operator-a",
                    "decided_at": AT,
                }
            ]
            found = codes(validate(forged, records, False))
            self.assertTrue(
                found & {"DECISION_REASON_INCOMPATIBLE", "REVIEW_REQUIRED_PERSISTED"}, found
            )
            self.assertEqual(forged["decisions"][0]["reason"], reason)

    def test_origin_operator_timestamp_and_duplicates_are_checked(self) -> None:
        records, by_id, working = setup()
        decide(working, by_id, "r-url", "EGRESS_EXCLUDED", "OPERATOR_DISCRETION")
        cases = {
            "ORIGIN_NOT_HUMAN_OPERATOR": {"decision_origin": "DETERMINISTIC_RULE"},
            "DECIDED_BY_IS_NOT_THE_OPERATOR": {"decided_by": "someone-else"},
            "TIMESTAMP_INVALID": {"decided_at": "yesterday"},
        }
        for code, change in cases.items():
            forged = copy.deepcopy(working)
            forged["decisions"][0].update(change)
            self.assertIn(code, codes(validate(forged, records, False)))
        self.assertIn(
            "OPERATOR_ID_NOT_ACCEPTED",
            codes(validate(dict(working, operator_id="claude-reviewer"), records, False)),
        )
        both = copy.deepcopy(working)
        decide(both, by_id, "r-zero-1", "EGRESS_EXCLUDED", "OPERATOR_DISCRETION")
        forged_bulk = bulk(setup()[2], by_id, ["r-zero-1", "r-zero-2"])
        both["bulk_decisions"] = [forged_bulk]
        self.assertIn(
            "DUPLICATE_INDIVIDUAL_AND_BULK_DECISION", codes(validate(both, records, False))
        )


class TestCompleteReview(unittest.TestCase):
    def test_every_record_decided_leaves_nothing_review_required(self) -> None:
        records, by_id, working = setup()
        decide(working, by_id, "r-url", "EGRESS_APPROVED", "TRIGGER_REVIEWED_PUBLIC_REFERENCE")
        decide(working, by_id, "r-secret", "EGRESS_EXCLUDED", "CONTAINS_SECRET_LIKE_VALUE")
        working["bulk_decisions"].append(bulk(working, by_id, ["r-zero-1", "r-zero-2"]))
        self.assertEqual(validate(working, records), [])
        committed = committed_decisions(working, blank_committed())
        self.assertNotIn("confirmation", committed["bulk_decisions"][0])
        derived = derive_egress_eligibility(
            records,
            load_decisions(committed, scan_id=SCAN_ID, pattern_digest=pattern_table_sha256()),
        )
        states = {r["normalized_record_id"]: r["state"] for r in derived}
        self.assertEqual(
            states,
            {
                "r-delim": "EGRESS_EXCLUDED",
                "r-secret": "EGRESS_EXCLUDED",
                "r-url": "EGRESS_APPROVED",
                "r-zero-1": "EGRESS_APPROVED",
                "r-zero-2": "EGRESS_APPROVED",
            },
        )
        self.assertNotIn("EGRESS_REVIEW_REQUIRED", states.values())
        self.assertTrue(
            all(r["decision_origin"] in {"HUMAN_OPERATOR", "DETERMINISTIC_RULE"} for r in derived)
        )

    def test_exclusion_is_a_complete_answer(self) -> None:
        records, by_id, working = setup()
        for rid in ("r-url", "r-secret", "r-zero-1", "r-zero-2"):
            decide(working, by_id, rid, "EGRESS_EXCLUDED", "OPERATOR_DISCRETION")
        self.assertEqual(validate(working, records), [])


if __name__ == "__main__":
    unittest.main()


class TestCommittedDevelopmentDecisions(unittest.TestCase):
    """The imported operator decisions (Mission 1.85.6 follow-up), read-only."""

    DATA = pathlib.Path(__file__).resolve().parents[4] / "docs" / "data"

    def load(self, name):
        import json

        return json.loads((self.DATA / name).read_text("utf-8"))

    def test_every_decision_is_a_human_operator_choice_and_nothing_is_left_to_review(self) -> None:
        decisions = self.load("stack-overflow-semantic-egress-decisions-development-v1.json")
        eligibility = self.load("stack-overflow-semantic-egress-eligibility-development-v1.json")
        scan = {
            r["normalized_record_id"]: r
            for r in self.load("stack-overflow-semantic-egress-scan-development-v1.json")["records"]
        }
        self.assertEqual(
            {d["decision_origin"] for d in decisions["decisions"]}
            | {b["decision_origin"] for b in decisions["bulk_decisions"]},
            {"HUMAN_OPERATOR"},
        )
        self.assertNotIn("EGRESS_REVIEW_REQUIRED", eligibility["state_counts"])
        for row in eligibility["records"]:
            if scan[row["normalized_record_id"]]["transmission_problems"]:
                self.assertEqual(row["state"], "EGRESS_EXCLUDED")
                self.assertEqual(row["decision_origin"], "DETERMINISTIC_RULE")
            else:
                self.assertEqual(row["decision_origin"], "HUMAN_OPERATOR")
            if row["state"] == "EGRESS_APPROVED" and "secret_like" in row["triggers"]:
                self.assertEqual(row["basis"], "TRIGGER_REVIEWED_NOT_PERSONAL")
        for decision in decisions["decisions"]:
            self.assertEqual(
                decision["surface_sha256"], scan[decision["normalized_record_id"]]["surface_sha256"]
            )
            self.assertFalse(
                set(decision)
                - {
                    "normalized_record_id",
                    "surface_sha256",
                    "decision",
                    "reason",
                    "decision_origin",
                    "decided_by",
                    "decided_at",
                }
            )
