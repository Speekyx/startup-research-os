"""Mission 1.42.1 §32. One human decision, carried faithfully.

The reliability value here was supplied by a named person. Software's whole job
was to record it without changing it, so most of this suite asserts that the
persisted-shape artifact still says exactly what the operator said: `0.55`, not
rounded, not derived from the ordinal states, not nudged toward the existing
`0.5`, and `UNSURE` still `UNSURE`.

The rest holds the narrow schema repair. Two nullable columns, **no backfill**,
and both halves or neither — because an id with no version names a moving
target.

Everything reads a checked-in artifact or the model, never the deployment: CI's
integration job starts from an empty database. The live bindings are verified by
`report_convergent_reliability_resolution.py` against the real deployment after
the operator confirms.

`unittest`, not pytest: `run_python_tests.py` discovers this package with
`unittest discover`.
"""

from __future__ import annotations

import ast
import json
import pathlib
import unittest
from datetime import UTC, datetime

from sros_contracts import ClaimType, ReliabilityAssessmentOrigin, ReliabilityBasisType
from sros_evidence_reliability import (
    ReliabilityAssessment,
    ReliabilityBasis,
    ReliabilityScope,
    resolve_reliability,
    rubric,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
REVIEW = DOCS / "second-pilot-convergent-operator-reliability-review-v1.json"
REVIEW_MD = DOCS / "second-pilot-convergent-operator-reliability-review-v1.md"
AUDIT = DOCS / "calibration-feasibility-audit-v1.json"
CONTRACT = REPO_ROOT / "docs" / "CLAUDE.md"
MIGRATION = (
    REPO_ROOT
    / "infrastructure"
    / "db"
    / "migrations"
    / "0032_reliability_review_rubric_provenance.sql"
)
RECORDER = REPO_ROOT / "infrastructure" / "scripts" / "record_reliability_assessment.py"
REPORTER = REPO_ROOT / "infrastructure" / "scripts" / "report_convergent_reliability_resolution.py"

CONVERGENT_KIND = "source_published_classification_value_contrast_witnessed"
DETAILED_KIND = "source_reported_procurement_value_contrast"


def review() -> dict:
    return json.loads(REVIEW.read_text(encoding="utf-8"))


class TheOperatorJudgementIsCarriedVerbatim(unittest.TestCase):
    """§5. The value is the human review result and nothing computed it."""

    def test_reliability_is_exactly_the_supplied_value(self):
        self.assertEqual(review()["reliability"], 0.55)

    def test_the_value_was_not_nudged_toward_either_existing_assessment(self):
        value = review()["reliability"]
        self.assertNotEqual(value, 0.5)
        self.assertNotEqual(value, 0.65)
        # Nor the mean of them, which is the shape an averaging bug would take.
        self.assertNotEqual(value, (0.5 + 0.65) / 2)

    def test_the_reviewer_is_the_named_person(self):
        self.assertEqual(review()["reviewed_by"], "thibchm")

    def test_the_origin_is_human_review(self):
        self.assertEqual(review()["origin"], ReliabilityAssessmentOrigin.HUMAN_REVIEW.value)

    def test_the_ordinal_profile_is_exactly_what_the_operator_assigned(self):
        self.assertEqual(
            {k: v for k, v in review()["rubric_profile"].items() if k != "$comment"},
            {
                "MEASUREMENT_DEFINITION": "PARTIALLY_DOCUMENTED",
                "SOURCE_SIDE_VALIDATION": "DOCUMENTED_WITH_UNBOUNDED_LIMITATION",
                "HISTORICAL_MUTABILITY": "NOT_ESTABLISHED",
                "COMPLETENESS_AND_MISSINGNESS": "PARTIALLY_DOCUMENTED",
                "SOURCE_SIDE_CHECKABILITY": "DOCUMENTED_AND_BOUNDED",
            },
        )

    def test_the_materiality_answers_are_exact_and_unsure_survives(self):
        answers = [u["reviewer_materiality"] for u in review()["material_unknowns"]]
        self.assertEqual(answers, ["YES", "YES", "NO", "UNSURE"])
        # UNSURE is not YES, not NO, not "low confidence", and not a number.
        self.assertIn("UNSURE", rubric.MATERIALITY_ANSWERS)

    def test_the_gate_is_the_operators_and_was_not_recomputed(self):
        self.assertEqual(review()["numeric_judgement_gate"], "NUMERIC_JUDGEMENT_PERMITTED")
        self.assertIs(rubric.NUMERIC_JUDGEMENT_IS_NEVER_REQUIRED, True)

    def test_the_rationale_and_limitation_keep_their_load_bearing_clauses(self):
        rationale = review()["rationale"]
        limitation = review()["stated_limitation"]
        # Not strengthened: the review must not come out claiming the amounts are
        # correct or the Claim probably true.
        self.assertIn("does not establish that a published amount is factually correct", rationale)
        self.assertIn("material unknowns", rationale)
        self.assertIn("conformance rather than factual correctness", limitation)
        self.assertIn("Long-term retrievability", limitation)
        for forbidden in ("probably true", "amounts are correct", "market size"):
            self.assertNotIn(forbidden, rationale.lower())
            self.assertNotIn(forbidden, limitation.lower())


class TheScopeIsTheOneUnderReview(unittest.TestCase):
    """§ scope. Five fields, and no narrowing to what happened to prompt it."""

    def test_the_scope_is_the_exact_five_part_convergent_scope(self):
        self.assertEqual(
            review()["scope"],
            {
                "source_id": "ted-eu",
                "resource_id": "notices/eforms-contract-and-award",
                "record_kind_id": "procurement_notice",
                "claim_type": "OBSERVED",
                "proposition_kind": CONVERGENT_KIND,
            },
        )

    def test_the_scope_was_not_narrowed_to_the_second_pilot(self):
        # Narrowing to CPV 92, to EUR, or to the two multi-Evidence Claims would
        # change the reliability architecture rather than the value.
        scope = review()["scope"]
        for field in ("classification_division", "currency", "notice_class", "claim_id"):
            self.assertNotIn(field, scope)
        covers = review()["covers"]
        self.assertEqual(covers["evidence_rows"], 6)
        self.assertEqual(covers["claims"], 4)
        self.assertGreater(len(covers["classification_divisions"]), 1)
        self.assertGreater(len(covers["currencies"]), 1)

    def test_four_of_five_fields_matching_is_still_no_match(self):
        """The near miss, through the REAL resolver, in both directions."""

        def assessment(kind: str) -> ReliabilityAssessment:
            return ReliabilityAssessment(
                id=f"stand-in-{kind}",
                scope=ReliabilityScope(
                    source_id="ted-eu",
                    resource_id="notices/eforms-contract-and-award",
                    record_kind_id="procurement_notice",
                    claim_type=ClaimType.OBSERVED,
                    proposition_kind=kind,
                ),
                version=1,
                reliability=0.55 if kind == CONVERGENT_KIND else 0.5,
                origin=ReliabilityAssessmentOrigin.HUMAN_REVIEW,
                rationale="(fixture)",
                stated_limitation="(fixture)",
                reviewed_by="thibchm",
                reviewed_at=datetime.now(UTC),
                basis=(
                    ReliabilityBasis(
                        basis_type=ReliabilityBasisType.MEASUREMENT_METHODOLOGY,
                        document_title="eForms SDK 1.15.1",
                        summarized_finding="(fixture)",
                        document_url="https://docs.ted.europa.eu/eforms/latest/",
                        section_reference="BT-161",
                        retrieved_at=datetime(2026, 9, 1, tzinfo=UTC),
                    ),
                ),
                review_rubric_id=rubric.RUBRIC_ID if kind == CONVERGENT_KIND else None,
                review_rubric_version=rubric.RUBRIC_VERSION if kind == CONVERGENT_KIND else None,
            )

        new = assessment(CONVERGENT_KIND)
        old = assessment(DETAILED_KIND)

        self.assertEqual(
            resolve_reliability(scope=new.scope, candidates=[new, old], supplied=None).reliability,
            0.55,
        )
        self.assertEqual(
            resolve_reliability(scope=old.scope, candidates=[new, old], supplied=None).reliability,
            0.5,
        )
        # Neither reaches the other's scope, and no source-level fallback exists.
        self.assertIsNone(
            resolve_reliability(scope=new.scope, candidates=[old], supplied=None).reliability
        )
        self.assertIsNone(
            resolve_reliability(scope=old.scope, candidates=[new], supplied=None).reliability
        )

    def test_the_binding_carries_the_rubric_that_produced_the_value(self):
        assessments = [a for a in (self._new(),) if a.scope.proposition_kind == CONVERGENT_KIND]
        binding = assessments[0].binding()
        self.assertEqual(binding.review_rubric_id, rubric.RUBRIC_ID)
        self.assertEqual(binding.review_rubric_version, rubric.RUBRIC_VERSION)
        self.assertIn("review_rubric_id", binding.to_json())

    @staticmethod
    def _new() -> ReliabilityAssessment:
        return ReliabilityAssessment(
            id="stand-in",
            scope=ReliabilityScope(
                source_id="ted-eu",
                resource_id="notices/eforms-contract-and-award",
                record_kind_id="procurement_notice",
                claim_type=ClaimType.OBSERVED,
                proposition_kind=CONVERGENT_KIND,
            ),
            version=1,
            reliability=0.55,
            origin=ReliabilityAssessmentOrigin.HUMAN_REVIEW,
            rationale="(fixture)",
            stated_limitation="(fixture)",
            reviewed_by="thibchm",
            reviewed_at=datetime.now(UTC),
            basis=(
                ReliabilityBasis(
                    basis_type=ReliabilityBasisType.MEASUREMENT_METHODOLOGY,
                    document_title="eForms SDK 1.15.1",
                    summarized_finding="(fixture)",
                    document_url="https://docs.ted.europa.eu/eforms/latest/",
                    section_reference="BT-161",
                    retrieved_at=datetime(2026, 9, 1, tzinfo=UTC),
                ),
            ),
            review_rubric_id=rubric.RUBRIC_ID,
            review_rubric_version=rubric.RUBRIC_VERSION,
        )


class TheRubricProvenanceRepairIsNarrow(unittest.TestCase):
    """§0, §24. Two nullable columns, and nothing is backfilled."""

    def test_the_migration_adds_two_nullable_columns_and_no_default(self):
        """Over the ADD COLUMN lines, not the whole file.

        The CHECK that enforces both-halves-or-neither necessarily contains
        `IS NOT NULL`, so a file-wide scan for `NOT NULL` fails on the
        constraint doing the work -- `testing-strategy.md` §23 in a new place.
        What must be nullable is the COLUMNS.
        """
        sql = MIGRATION.read_text(encoding="utf-8")
        added = [line.strip() for line in sql.splitlines() if line.strip().startswith("ADD COLUMN")]
        self.assertEqual(len(added), 2)
        for line in added:
            self.assertIn("TEXT", line)
            self.assertNotIn("NOT NULL", line)
            self.assertNotIn("DEFAULT", line)
        self.assertIn("review_rubric_id", added[0])
        self.assertIn("review_rubric_version", added[1])

    def test_the_migration_writes_no_row(self):
        """A backfill would fabricate provenance for reviews that used no rubric."""
        sql = MIGRATION.read_text(encoding="utf-8").upper()
        for statement in ("UPDATE ", "INSERT ", "DELETE "):
            self.assertNotIn(statement, sql)

    def test_the_migration_refuses_half_a_provenance(self):
        sql = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("reliability_assessments_rubric_provenance_check", sql)

    def test_the_model_refuses_half_a_provenance_too(self):
        base = TheScopeIsTheOneUnderReview._new()
        with self.assertRaises(ValueError):
            ReliabilityAssessment(
                **{
                    **base.__dict__,
                    "review_rubric_version": None,
                }
            )

    def test_a_review_without_a_rubric_is_still_representable(self):
        """The two existing assessments predate the rubric, and NULL is true."""
        base = TheScopeIsTheOneUnderReview._new()
        historical = ReliabilityAssessment(
            **{**base.__dict__, "review_rubric_id": None, "review_rubric_version": None}
        )
        self.assertIsNone(historical.review_rubric_id)
        self.assertIsNone(historical.binding().review_rubric_id)

    def test_the_recorder_never_defaults_the_rubric(self):
        """Defaulting to the current rubric would claim a procedure nobody followed."""
        source = RECORDER.read_text(encoding="utf-8")
        self.assertIn('rubric = review.get("review_rubric") or {}', source)
        self.assertNotIn("RUBRIC_ID", source)
        self.assertNotIn("rubric_id or ", source)


class TheReviewConformsToTheRubricItNames(unittest.TestCase):
    """§4. Structural conformance, checked rather than assumed."""

    def test_the_review_names_the_canonical_rubric(self):
        declared = review()["review_rubric"]
        self.assertEqual(declared["id"], rubric.RUBRIC_ID)
        self.assertEqual(declared["version"], rubric.RUBRIC_VERSION)

    def test_every_state_is_a_rubric_state_and_every_dimension_is_answered(self):
        profile = {k: v for k, v in review()["rubric_profile"].items() if k != "$comment"}
        self.assertEqual(set(profile), {d.id for d in rubric.DIMENSIONS})
        for state in profile.values():
            self.assertIn(state, {s.value for s in rubric.ReviewState})

    def test_no_hard_stop_was_triggered_and_none_was_invented(self):
        triggered = review()["hard_stops_triggered"]
        self.assertEqual(triggered, [])
        for stop in triggered:
            self.assertIn(stop, {h.id for h in rubric.HARD_STOPS})

    def test_a_value_exists_because_the_gate_permitted_one(self):
        permitted = rubric.NumericJudgementGate.NUMERIC_JUDGEMENT_PERMITTED.value
        self.assertEqual(review()["numeric_judgement_gate"], permitted)
        self.assertIsNotNone(review()["reliability"])


class TheBasisIsDocumentaryAndFirstParty(unittest.TestCase):
    """§6. Four held documents, and no engineering validation among them."""

    def test_every_basis_row_is_a_real_type_and_document_backed(self):
        rows = review()["basis"]
        self.assertEqual(len(rows), 4)
        for row in rows:
            ReliabilityBasisType(row["basis_type"])
            self.assertTrue(row["document_url"])
            self.assertTrue(row["retrieved_at"])
            self.assertTrue(row["summarized_finding"].strip())

    def test_no_reviewer_judgement_row_stands_alone(self):
        types = {row["basis_type"] for row in review()["basis"]}
        self.assertNotEqual(types, {"REVIEWER_DOCUMENTED_JUDGEMENT"})

    def test_no_sros_engineering_validation_is_used_as_basis(self):
        rendered = json.dumps(review()["basis"])
        for phrase in ("Mission", "extractor", "test suite", "convergence contract"):
            self.assertNotIn(phrase, rendered)

    def test_nothing_new_was_fetched_to_inflate_the_count(self):
        packet = json.loads(
            (DOCS / "second-pilot-convergent-reliability-review-packet-v1.json").read_text(
                encoding="utf-8"
            )
        )
        prepared = {row["document_title"] for row in packet["candidate_basis_rows"]}
        used = {row["document_title"] for row in review()["basis"]}
        self.assertEqual(used, prepared)


class NothingElseWasTouched(unittest.TestCase):
    """§25, §28, §29. One reliability input, and no second act."""

    def test_the_review_does_not_change_either_historical_value(self):
        rendered = json.dumps(review())
        self.assertNotIn('"supersede"', rendered)
        self.assertNotIn("0.65", rendered)
        # 0.5 may not appear as a value anywhere either.
        self.assertNotIn('"reliability": 0.5,', rendered)

    def test_the_review_disclaims_every_thing_it_is_not(self):
        disclaimers = " ".join(review()["what_this_is_not"]).lower()
        for phrase in ("calibration", "probability", "source-wide", "independence"):
            self.assertIn(phrase, disclaimers)

    def test_the_aggregation_profile_is_still_uncalibrated(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        self.assertEqual(audit["profile"]["status"], "UNCALIBRATED")

    def test_the_diagnostic_reporter_creates_no_independence_and_no_score(self):
        source = REPORTER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        written = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        # It reads a deployment and writes one artifact. No INSERT, no UPDATE.
        upper = source.upper()
        for statement in ("INSERT INTO", "UPDATE SCORING", "UPDATE EPISTEMIC"):
            self.assertNotIn(statement, upper)
        self.assertIn("allow_uncalibrated=True", source)
        self.assertIn("independence_groups_created", source)
        self.assertNotIn("commit", written)

    def test_the_diagnostic_is_labelled_uncalibrated_and_not_a_score(self):
        source = REPORTER.read_text(encoding="utf-8")
        for label in ("UNCALIBRATED", "DIAGNOSTIC ONLY", "NOT AN OPPORTUNITY SCORE"):
            self.assertIn(label, source)

    def test_no_calibration_label_or_opportunity_work_appears(self):
        rendered = json.dumps(review()).lower()
        for phrase in ("calibration label", "holdout", "opportunity score", "ranking"):
            self.assertNotIn(phrase, rendered)

    def test_problem_family_is_still_parked(self):
        self.assertIn("PARK_PROBLEM_FAMILY_CLASSIFIER", CONTRACT.read_text(encoding="utf-8"))


class TheHumanConfirmationGuardIsIntact(unittest.TestCase):
    """§7. The value is authorised; the confirmation is still typed."""

    def test_the_recorder_still_refuses_without_a_terminal(self):
        source = RECORDER.read_text(encoding="utf-8")
        self.assertIn("except EOFError", source)
        self.assertIn("no terminal to confirm on", source)
        self.assertIn("input(", source)

    def test_no_module_in_this_mission_patches_the_guard(self):
        for path in (
            REPORTER,
            REPO_ROOT / "infrastructure" / "scripts" / "render_operator_reliability_review.py",
        ):
            source = path.read_text(encoding="utf-8")
            for bypass in ("isatty", "monkeypatch", "builtins.input", "record_reliability"):
                self.assertNotIn(bypass, source)

    def test_the_rendered_review_shows_the_outcome_is_not_yet_persisted(self):
        text = REVIEW_MD.read_text(encoding="utf-8")
        self.assertIn("0.55", text)
        self.assertIn("thibchm", text)
        self.assertIn("UNSURE", text)


if __name__ == "__main__":
    unittest.main()
