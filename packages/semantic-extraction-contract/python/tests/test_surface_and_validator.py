"""Mission 1.85.3 (N08-A). The text surface and the deterministic validator.

The validator is the only way a model's interpretation enters anything. These tests hold it to three
properties: a span must be the held text itself, every failure is reported at once, and a finding never
becomes more than one witness of one record.
"""

from __future__ import annotations

import ast
import json
import pathlib
import sys
import unittest

from sros_semantic_extraction_contract import (
    DERIVATION_KIND,
    ExtractionContext,
    RefusalReason,
    marker_regions,
    render_question_surface,
    surface_sha256,
    validate_extraction,
)
from sros_semantic_extraction_contract.finding import MAX_FINDINGS

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
FIXTURES = json.loads(
    (REPO_ROOT / "docs" / "data" / "first-person-semantic-extraction-fixtures-v1.json").read_text(
        "utf-8"
    )
)
PACKAGE = pathlib.Path(__file__).resolve().parents[1] / "sros_semantic_extraction_contract"
FA, NE = "REPORTED_FAILED_ATTEMPT", "NEGATIVE_EVALUATION_OF_NAMED_SOLUTION"


def context(surface: str, **overrides) -> ExtractionContext:
    values = dict(
        workspace_id="00000000-0000-4000-8000-000000000001",
        normalized_record_id="synthetic-record",
        observation_key="synthetic|fixture",
        source_id="stack-exchange",
        surface=surface,
        expected_surface_sha256=surface_sha256(surface),
        visible_length=len(surface),
        extractor_id="synthetic-extractor",
        extractor_version="0.0.0",
        prompt_id="synthetic-prompt",
        prompt_version="0.0.0",
        provider="synthetic-provider",
        model="synthetic-model",
    )
    values.update(overrides)
    return ExtractionContext(**values)


def finding(finding_type, quote, occurrence=1, subject=None, subject_occurrence=None):
    return {
        "finding_type": finding_type,
        "evidence_quote": quote,
        "evidence_occurrence": occurrence,
        "subject_quote": subject,
        "subject_occurrence": subject_occurrence,
    }


def reasons(report) -> set[RefusalReason]:
    return {reason for reason, _ in report.refusals}


SURFACE = render_question_surface(
    "Build keeps failing",
    "<p>I tried rebuilding with no cache and it still fails.</p>"
    "<p>Honestly Docker Desktop is unusable on this machine.</p>"
    "<blockquote><p>Podman is a nightmare to configure</p></blockquote>"
    "<pre><code>ERROR: this is awful, everything broke\n</code></pre>",
)


class TestSurface(unittest.TestCase):
    def test_rendering_is_deterministic_and_lf_only(self) -> None:
        body = "<p>a &amp; b</p>\r\n<pre><code>x\r\n  y\r\n</code></pre>"
        first = render_question_surface("T &lt;1&gt;", body)
        self.assertEqual(first, render_question_surface("T &lt;1&gt;", body))
        self.assertNotIn("\r", first)
        self.assertTrue(first.startswith("T <1>\n\na & b"))
        self.assertIn("[CODE]\nx\n  y\n[/CODE]", first)

    def test_empty_body_is_the_title_alone_and_empty_title_is_refused(self) -> None:
        self.assertEqual(render_question_surface("Only a title", None), "Only a title")
        with self.assertRaises(ValueError):
            render_question_surface("  ", "<p>x</p>")

    def test_regions_are_scanned_with_nesting_and_code_cannot_open_a_quote(self) -> None:
        surface = render_question_surface(
            "t",
            "<blockquote><p>q</p><pre><code>inner\n</code></pre></blockquote>"
            "<pre><code>[QUOTE]\nnot a quote\n</code></pre>",
        )
        kinds = [kind for kind, _, _ in marker_regions(surface)]
        self.assertEqual(kinds, ["QUOTE", "CODE", "CODE"])
        for kind, start, end in marker_regions(surface):
            self.assertTrue(surface[start:end].startswith(f"[{kind}]"))


class TestValidator(unittest.TestCase):
    def test_a_valid_extraction_carries_offsets_the_model_never_supplied(self) -> None:
        quote = "I tried rebuilding with no cache and it still fails"
        report = validate_extraction(
            {"extraction_state": "FINDINGS_PRESENT", "findings": [finding(FA, quote)]},
            context(SURFACE),
        )
        self.assertTrue(report.accepted, report.refusals)
        extracted = report.extraction.findings[0]
        self.assertEqual(SURFACE[extracted.evidence_start : extracted.evidence_end], quote)
        self.assertEqual(extracted.evidence_dimension, "PROBLEM_OR_NEED")
        self.assertIn("independence from any other finding", extracted.does_not_establish)

    def test_an_extraction_is_one_witness_and_never_a_signal(self) -> None:
        report = validate_extraction(
            {
                "extraction_state": "FINDINGS_PRESENT",
                "findings": [
                    finding(FA, "I tried rebuilding with no cache and it still fails"),
                    finding(
                        NE, "Docker Desktop is unusable on this machine", 1, "Docker Desktop", 1
                    ),
                ],
            },
            context(SURFACE),
        )
        self.assertTrue(report.accepted, report.refusals)
        self.assertEqual(report.extraction.derivation_kind, DERIVATION_KIND)
        self.assertEqual(DERIVATION_KIND, "MODEL_DERIVED")
        self.assertFalse(report.extraction.is_signal)
        self.assertEqual(report.extraction.independent_witness_count, 1)
        self.assertEqual(
            {f.observation_category for f in report.extraction.findings},
            {"REPORTED_BEHAVIOUR", "STATED_OPINION"},
        )

    def test_zero_findings_is_a_valid_answer(self) -> None:
        report = validate_extraction(
            {"extraction_state": "NO_FINDING_ESTABLISHED", "findings": []}, context(SURFACE)
        )
        self.assertTrue(report.accepted)
        self.assertEqual(report.extraction.findings, ())

    def test_every_failure_is_reported_together_and_nothing_is_kept(self) -> None:
        payload = {
            "extraction_state": "NO_FINDING_ESTABLISHED",
            "findings": [
                finding(FA, "I tried rebuilding with no cache and it still fails"),
                finding(FA, "this sentence was never written by anyone"),
                finding("STATED_HYPOTHETICAL_PAYMENT", "I tried rebuilding with no cache"),
                finding(NE, "Podman is a nightmare to configure", 1, "Podman", 1),
                finding(NE, "this is awful, everything broke", 1, "Docker Desktop", 1),
            ],
        }
        report = validate_extraction(payload, context(SURFACE, model=" "))
        self.assertFalse(report.accepted)
        self.assertIsNone(report.extraction)
        self.assertTrue(
            {
                RefusalReason.STATE_FINDINGS_MISMATCH,
                RefusalReason.QUOTE_NOT_IN_SURFACE,
                RefusalReason.LABEL_NOT_EXTRACTABLE,
                RefusalReason.SPAN_IN_QUOTED_MATERIAL,
                RefusalReason.SPAN_IN_CODE_NOT_PERMITTED,
                RefusalReason.PROVENANCE_INCOMPLETE,
            }
            <= reasons(report)
        )

    def test_quote_boundaries(self) -> None:
        cases = {
            "short": (finding(FA, "I tried"), RefusalReason.QUOTE_INVALID),
            "marker": (
                finding(FA, "[CODE]\nERROR: this is awful"),
                RefusalReason.QUOTE_CONTAINS_MARKER,
            ),
            "occurrence": (
                finding(FA, "I tried rebuilding with no cache", 2),
                RefusalReason.OCCURRENCE_INVALID,
            ),
            "bool occurrence": (
                finding(FA, "I tried rebuilding with no cache", True),
                RefusalReason.OCCURRENCE_INVALID,
            ),
            "whitespace drift": (
                finding(FA, "I tried  rebuilding with no cache"),
                RefusalReason.QUOTE_NOT_IN_SURFACE,
            ),
        }
        for name, (item, expected) in cases.items():
            with self.subTest(name):
                report = validate_extraction(
                    {"extraction_state": "FINDINGS_PRESENT", "findings": [item]}, context(SURFACE)
                )
                self.assertIn(expected, reasons(report))

    def test_structure_limits(self) -> None:
        good = finding(FA, "I tried rebuilding with no cache and it still fails")
        checks = [
            (
                [],
                {"extraction_state": "FINDINGS_PRESENT", "findings": [good], "confidence": 0.9},
                RefusalReason.UNKNOWN_OR_MISSING_KEY,
            ),
            (
                [],
                {"extraction_state": "MAYBE", "findings": []},
                RefusalReason.UNKNOWN_EXTRACTION_STATE,
            ),
            (
                [],
                {"extraction_state": "FINDINGS_PRESENT", "findings": [good, dict(good)]},
                RefusalReason.DUPLICATE_FINDING,
            ),
            (
                [],
                {"extraction_state": "FINDINGS_PRESENT", "findings": [dict(good, rationale="x")]},
                RefusalReason.UNKNOWN_OR_MISSING_KEY,
            ),
            (
                [],
                {"extraction_state": "FINDINGS_PRESENT", "findings": [good] * (MAX_FINDINGS + 1)},
                RefusalReason.TOO_MANY_FINDINGS,
            ),
            ([], "FINDINGS_PRESENT", RefusalReason.PAYLOAD_NOT_AN_OBJECT),
        ]
        for _, payload, expected in checks:
            with self.subTest(expected):
                self.assertIn(expected, reasons(validate_extraction(payload, context(SURFACE))))

    def test_spans_past_what_the_model_saw_and_a_changed_surface_are_refused(self) -> None:
        payload = {
            "extraction_state": "FINDINGS_PRESENT",
            "findings": [
                finding(NE, "Docker Desktop is unusable on this machine", 1, "Docker Desktop", 1)
            ],
        }
        self.assertIn(
            RefusalReason.SPAN_BEYOND_VISIBLE_TEXT,
            reasons(validate_extraction(payload, context(SURFACE, visible_length=40))),
        )
        self.assertIn(
            RefusalReason.SURFACE_DIGEST_MISMATCH,
            reasons(
                validate_extraction(payload, context(SURFACE, expected_surface_sha256="0" * 64))
            ),
        )

    def test_subject_rules(self) -> None:
        with_subject = finding(
            FA, "I tried rebuilding with no cache and it still fails", 1, "Docker Desktop", 1
        )
        without = finding(NE, "Docker Desktop is unusable on this machine")
        self.assertIn(
            RefusalReason.SUBJECT_NOT_PERMITTED,
            reasons(
                validate_extraction(
                    {"extraction_state": "FINDINGS_PRESENT", "findings": [with_subject]},
                    context(SURFACE),
                )
            ),
        )
        self.assertIn(
            RefusalReason.SUBJECT_REQUIRED,
            reasons(
                validate_extraction(
                    {"extraction_state": "FINDINGS_PRESENT", "findings": [without]},
                    context(SURFACE),
                )
            ),
        )

    def test_identity_includes_the_model_and_excludes_nothing_the_model_chose_to_hide(self) -> None:
        payload = {
            "extraction_state": "FINDINGS_PRESENT",
            "findings": [finding(FA, "I tried rebuilding with no cache and it still fails")],
        }
        one = validate_extraction(payload, context(SURFACE)).extraction
        again = validate_extraction(payload, context(SURFACE)).extraction
        other_model = validate_extraction(
            payload, context(SURFACE, model="another-model")
        ).extraction
        self.assertEqual(one.extraction_id, again.extraction_id)
        self.assertEqual(one.findings[0].finding_id, again.findings[0].finding_id)
        self.assertNotEqual(one.extraction_id, other_model.extraction_id)


class TestAdversarialFixtures(unittest.TestCase):
    def test_every_required_case_is_present_and_synthetic(self) -> None:
        self.assertTrue(FIXTURES["synthetic"])
        required = {
            "plain_factual_question",
            "explicit_failure",
            "failed_workaround",
            "successful_workaround",
            "complaint_about_named_tool",
            "feature_request",
            "hypothetical_future_purchase",
            "explicit_past_payment",
            "negated_pain",
            "quoted_complaint_of_someone_else",
            "emotional_words_in_error_text",
            "prompt_injection_text",
            "multiple_distinct_problems",
            "ambiguous_subject",
            "no_usable_semantic_finding",
            "accepted_answer_metadata_present",
            "high_score_no_business_signal",
        }
        self.assertEqual({case["case_id"] for case in FIXTURES["cases"]}, required)
        zero = [case for case in FIXTURES["cases"] if not case["expected_labels"]]
        self.assertGreaterEqual(len(zero), len(FIXTURES["cases"]) // 2)

    def test_each_trap_is_caught_where_a_deterministic_check_can_catch_it(self) -> None:
        for case in FIXTURES["cases"]:
            with self.subTest(case["case_id"]):
                surface = render_question_surface(case["record"]["title"], case["record"]["body"])
                report = validate_extraction(case["trap"]["payload"], context(surface))
                self.assertEqual(
                    report.accepted, not case["trap"]["refused_by_validator"], report.refusals
                )
                if case["trap"]["refused_by_validator"]:
                    self.assertIn(RefusalReason(case["trap"]["caught_by"]), reasons(report))

    def test_semantic_errors_the_validator_cannot_see_are_named_as_evaluation_work(self) -> None:
        passed = {
            case["case_id"]
            for case in FIXTURES["cases"]
            if not case["trap"]["refused_by_validator"]
            and case["trap"]["caught_by"] != "EXPECTED_VALID"
        }
        self.assertEqual(
            passed, {"plain_factual_question", "negated_pain", "prompt_injection_text"}
        )


class TestPackageBoundary(unittest.TestCase):
    def test_imports_only_the_standard_library_and_contracts(self) -> None:
        allowed = set(sys.stdlib_module_names) | {"sros_contracts", "__future__"}
        for module in PACKAGE.glob("*.py"):
            tree = ast.parse(module.read_text("utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [node.module or ""]
                for name in names:
                    with self.subTest(module=module.name, name=name):
                        self.assertIn(name.split(".")[0], allowed)


if __name__ == "__main__":
    unittest.main()
