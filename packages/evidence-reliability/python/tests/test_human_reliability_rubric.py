"""Mission 1.42a §36. A decision procedure, and the scoring shortcut it is not.

The rubric exists because *choose a number from these documents* was not a
procedure. The failure it must not commit is the mirror image: **replacing
arbitrary numbers with different arbitrary numbers** — a weighted sum, a points
total, a mapping from a review state to a decimal. Most of this suite is the
assertion that no such thing exists, checked over the source with `ast` so that
the paragraph explaining the rule cannot satisfy it.

The rest holds the boundary. Reliability sits beside relevance, directness,
extraction confidence and freshness in `q = min(components)`, and a rubric that
quietly re-scored one of them would make a single weakness count twice.

`unittest`, not pytest: `run_python_tests.py` discovers this package with
`unittest discover`.
"""

from __future__ import annotations

import ast
import json
import pathlib
import unittest

from sros_contracts import ReliabilityAssessmentOrigin
from sros_evidence_reliability import rubric

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
DOCS = REPO_ROOT / "docs" / "data"
RUBRIC_JSON = DOCS / "human-reliability-assessment-rubric-v1.json"
RUBRIC_MD = DOCS / "human-reliability-assessment-rubric-v1.md"
CONTRACT = DOCS / "evidence-reliability-contract-v1.md"
AUDIT = DOCS / "calibration-feasibility-audit-v1.json"
MODULE = pathlib.Path(rubric.__file__)


def doc() -> dict:
    return json.loads(RUBRIC_JSON.read_text(encoding="utf-8"))


def strip_notes(value: object) -> object:
    if isinstance(value, dict):
        return {k: strip_notes(v) for k, v in value.items() if k not in ("$comment", "$note")}
    if isinstance(value, list):
        return [strip_notes(v) for v in value]
    return value


class TheRubricIsVersionedAndGeneric(unittest.TestCase):
    """§25, §26. It has an identity, and it belongs to no publisher."""

    def test_the_rubric_has_an_id_and_a_version(self):
        self.assertTrue(rubric.RUBRIC_ID)
        self.assertRegex(rubric.RUBRIC_VERSION, r"^\d+\.\d+\.\d+$")
        rendered = doc()
        self.assertEqual(rendered["rubric_id"], rubric.RUBRIC_ID)
        self.assertEqual(rendered["rubric_version"], rubric.RUBRIC_VERSION)

    def test_the_rubric_module_names_no_source(self):
        """A rubric mentioning one publisher is a scoring table for that publisher.

        Broader than the package-level guard, which predates TED and Wikimedia
        having assessments.
        """
        registered = {
            "world-bank",
            "gdelt",
            "eurostat",
            "fred",
            "reddit",
            "github",
            "ted-eu",
            "wikimedia-pageviews",
            "stack-exchange",
        }
        tree = ast.parse(MODULE.read_text(encoding="utf-8"))
        docstrings = {
            ast.get_docstring(n)
            for n in ast.walk(tree)
            if isinstance(n, ast.Module | ast.ClassDef | ast.FunctionDef)
        }
        found = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value in registered
            and node.value not in docstrings
        ]
        self.assertEqual(found, [])


class TheMeaningIsUnchanged(unittest.TestCase):
    """§1. The rubric implements the existing definition; it does not restate it."""

    def test_the_reliability_question_is_the_contract_s_own_words(self):
        contract = CONTRACT.read_text(encoding="utf-8")
        self.assertIn(rubric.RELIABILITY_QUESTION, contract)

    def test_the_excluded_concepts_name_every_neighbouring_component(self):
        excluded = " ".join(rubric.EXCLUDED_CONCEPTS).lower()
        for concept in ("independen", "directly", "extractor read", "recently"):
            self.assertIn(concept, excluded)

    def test_source_quality_and_governance_are_excluded(self):
        excluded = " ".join(rubric.EXCLUDED_CONCEPTS).lower()
        self.assertIn("reputation", excluded)
        self.assertIn("legally permitted", excluded)


class NoNeighbouringComponentIsScoredTwice(unittest.TestCase):
    """§4. The boundary is mandatory and is recorded rather than assumed."""

    def test_every_accepted_dimension_says_what_it_is_not(self):
        for dimension in rubric.DIMENSIONS:
            self.assertTrue(dimension.not_to_be_confused_with.strip())
            self.assertTrue(dimension.why_reliability_native.strip())

    def test_directness_is_rejected_rather_than_renamed(self):
        rejected = {r.id: r for r in rubric.REJECTED_DIMENSIONS}
        self.assertIn("MEASUREMENT_TO_PROPOSITION_FIT", rejected)
        self.assertEqual(
            rejected["MEASUREMENT_TO_PROPOSITION_FIT"].verdict,
            rubric.BELONGS_TO_OTHER_COMPONENT,
        )
        self.assertIn("directness", rejected["MEASUREMENT_TO_PROPOSITION_FIT"].reason)

    def test_extraction_confidence_is_not_duplicated_inside_reliability(self):
        boundaries = " ".join(d.not_to_be_confused_with for d in rubric.DIMENSIONS).lower()
        self.assertIn("extraction confidence", boundaries)

    def test_freshness_is_not_duplicated_inside_reliability(self):
        mutability = next(d for d in rubric.DIMENSIONS if d.id == "HISTORICAL_MUTABILITY")
        self.assertIn("freshness", mutability.not_to_be_confused_with)

    def test_independence_is_not_hidden_inside_reliability(self):
        self.assertIn("whether two Evidence rows are independent", rubric.EXCLUDED_CONCEPTS)
        ids = {d.id for d in rubric.DIMENSIONS}
        for name in ids:
            self.assertNotIn("INDEPEND", name)

    def test_source_reputation_is_rejected_with_the_coefficient_reason(self):
        rejected = {r.id: r for r in rubric.REJECTED_DIMENSIONS}
        self.assertIn("SOURCE_REPUTATION", rejected)
        self.assertIn("coefficient", rejected["SOURCE_REPUTATION"].reason)

    def test_every_rejection_carries_a_reason(self):
        for entry in rubric.REJECTED_DIMENSIONS:
            self.assertTrue(entry.reason.strip())
            self.assertIn(
                entry.verdict,
                {
                    rubric.BELONGS_TO_OTHER_COMPONENT,
                    rubric.FOLDED_INTO_ANOTHER_DIMENSION,
                    rubric.REJECTED_AS_DUPLICATE_QUESTION,
                    rubric.RECLASSIFIED_AS_HARD_STOP,
                },
            )


class UnknownIsNotLow(unittest.TestCase):
    """§6. Structural, not a warning in prose."""

    def test_not_established_has_no_ordinal_rank(self):
        self.assertIsNone(rubric.ORDINAL_RANK[rubric.ReviewState.NOT_ESTABLISHED])
        self.assertIsNone(rubric.ORDINAL_RANK[rubric.ReviewState.CONTRADICTED])

    def test_the_ranked_states_are_ranked_and_distinct(self):
        ranks = [
            rubric.ORDINAL_RANK[s] for s in rubric.ReviewState if rubric.ORDINAL_RANK[s] is not None
        ]
        self.assertEqual(len(ranks), 3)
        self.assertEqual(len(set(ranks)), 3)

    def test_no_state_maps_to_a_number_on_the_reliability_scale(self):
        for state in rubric.ReviewState:
            rank = rubric.ORDINAL_RANK[state]
            self.assertNotIsInstance(rank, float)
            if rank is not None:
                self.assertGreater(rank, 1.0 - 1e-9)  # a rank, never a [0,1] value

    def test_every_dimension_defines_the_unknown_state_observably(self):
        for dimension in rubric.DIMENSIONS:
            text = dimension.observable[rubric.ReviewState.NOT_ESTABLISHED].lower()
            self.assertIn("no document", text)


class NoArbitraryScoring(unittest.TestCase):
    """§8, §28. The rubric must not solve arbitrary numbers with new ones."""

    FORBIDDEN_NAMES = (
        "weighted_sum",
        "average_dimension_score",
        "points_total",
        "default_reliability",
        "unknown_to_midpoint",
        "source_coefficient",
        "dimension_weight",
        "score",
    )

    def test_no_scoring_identifier_exists_in_the_module(self):
        tree = ast.parse(MODULE.read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                names.add(node.id.lower())
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                names.add(node.name.lower())
            elif isinstance(node, ast.Attribute):
                names.add(node.attr.lower())
        for forbidden in self.FORBIDDEN_NAMES:
            self.assertNotIn(forbidden, names)

    def test_the_module_performs_no_arithmetic_at_all(self):
        """A rubric with no arithmetic cannot have a hidden formula in it."""
        tree = ast.parse(MODULE.read_text(encoding="utf-8"))
        arithmetic = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Add | ast.Sub | ast.Mult | ast.Div | ast.Pow)
        ]
        self.assertEqual(arithmetic, [])
        self.assertTrue(rubric.ORDINAL_RANKS_ARE_NEVER_SUMMED)

    def test_no_aggregating_builtin_is_called(self):
        tree = ast.parse(MODULE.read_text(encoding="utf-8"))
        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        for builtin in ("sum", "mean", "round", "min", "max"):
            self.assertNotIn(builtin, called)

    def test_no_rendered_key_is_a_scoring_field(self):
        """Over KEYS, not over prose.

        A bare substring scan for `weight` fails on the sentence explaining that
        a measurement cannot *bear the weight* of a proposition -- the
        `testing-strategy.md` §23 shape, met again. What must not exist is a
        FIELD that scores, so the scan is over field names.
        """

        def keys(value: object):
            if isinstance(value, dict):
                for k, v in value.items():
                    yield k
                    yield from keys(v)
            elif isinstance(value, list):
                for item in value:
                    yield from keys(item)

        for key in keys(doc()):
            lowered = key.lower()
            for forbidden in ("weight", "points", "score", "total", "coefficient"):
                self.assertNotIn(forbidden, lowered, f"scoring field: {key}")

    def test_no_scoring_formula_is_described_in_the_rendered_rubric(self):
        rendered = json.dumps(strip_notes(doc())).lower()
        for phrase in (
            "weighted sum",
            "weighted average",
            "points total",
            "point system",
            "midpoint",
            "sum of the",
        ):
            self.assertNotIn(phrase, rendered)

    def test_there_are_no_intermediate_anchors(self):
        # §9. An intermediate anchor would have to be invented.
        self.assertEqual(rubric.INTERMEDIATE_ANCHORS, ())
        self.assertEqual(doc()["scale"]["intermediate_anchors"], [])

    def test_no_default_reliability_exists_anywhere(self):
        rendered = json.dumps(strip_notes(doc())).lower()
        for phrase in ("default reliability", "0.5 because", "assume the middle"):
            self.assertNotIn(phrase, rendered)


class TheAnchorsAreDefinedByArithmeticRoleNotByAdjective(unittest.TestCase):
    """§9. The contract forbids threshold labels; an anchor must not smuggle one."""

    def test_exactly_two_anchors_at_the_ends_of_the_scale(self):
        self.assertEqual({a.value for a in rubric.ANCHORS}, {0.0, 1.0})

    def test_each_anchor_says_what_the_value_does_in_the_aggregation(self):
        joined = " ".join(a.means for a in rubric.ANCHORS)
        self.assertIn("min(components)", joined)

    def test_no_threshold_adjective_is_introduced(self):
        rendered = json.dumps(strip_notes(doc())).lower()
        for phrase in ("high reliability", "medium reliability", "low reliability"):
            self.assertNotIn(phrase, rendered)
        self.assertIsNone(doc()["scale"]["threshold_labels"])

    def test_zero_is_distinguished_from_no_assessment(self):
        zero = next(a for a in rubric.ANCHORS if a.value == 0.0)
        self.assertIn("not the same as having no assessment", zero.justified_when)


class ANumericJudgementMayBeRefused(unittest.TestCase):
    """§7, §13, §14. Producing no assessment is a complete review."""

    def test_the_gate_has_a_refusal_outcome_and_is_not_computed(self):
        outcomes = {g.value for g in rubric.NumericJudgementGate}
        self.assertIn("NUMERIC_JUDGEMENT_NOT_JUSTIFIED", outcomes)
        self.assertIn("DOCUMENTATION_INSUFFICIENT", outcomes)
        self.assertIs(doc()["numeric_judgement_gate"]["is_computed"], False)

    def test_a_numeric_value_is_not_required_for_every_review(self):
        self.assertTrue(rubric.NUMERIC_JUDGEMENT_IS_NEVER_REQUIRED)
        self.assertIs(
            doc()["numeric_judgement_gate"]["numeric_value_required_for_every_review"],
            False,
        )

    def test_material_unknowns_are_defined_and_do_not_auto_refuse(self):
        self.assertIn("could reasonably change", rubric.MATERIAL_UNKNOWN_DEFINITION)
        self.assertIn("not material merely because", rubric.MATERIAL_UNKNOWN_DEFINITION)
        stop_conditions = " ".join(h.condition for h in rubric.HARD_STOPS).lower()
        self.assertNotIn("material unknown", stop_conditions)

    def test_unsure_is_a_permitted_materiality_answer(self):
        self.assertIn("UNSURE", rubric.MATERIALITY_ANSWERS)

    def test_every_hard_stop_says_why_the_question_has_no_answer(self):
        self.assertTrue(rubric.HARD_STOPS)
        for stop in rubric.HARD_STOPS:
            self.assertTrue(stop.condition.strip())
            self.assertTrue(stop.why.strip())


class TheReviewerIsHumanAndAccountable(unittest.TestCase):
    """§16, §19. Software prepares; a person decides."""

    def test_every_judgement_field_is_the_reviewer_s(self):
        blank = rubric.blank_reviewer_fields()
        for field in ("reliability", "numeric_judgement_gate", "reviewed_by", "rationale"):
            self.assertIn(field, blank)
            self.assertIsNone(blank[field])

    def test_fact_and_judgement_are_separated_on_every_worksheet_field(self):
        for field in rubric.WORKSHEET_SCHEMA:
            self.assertIn(
                field.filled_by, (rubric.FilledBy.SOFTWARE_FACT, rubric.FilledBy.REVIEWER_JUDGEMENT)
            )
        software = {
            f.id for f in rubric.WORKSHEET_SCHEMA if f.filled_by is rubric.FilledBy.SOFTWARE_FACT
        }
        self.assertNotIn("reliability", software)
        self.assertNotIn("numeric_judgement_gate", software)

    def test_a_model_may_prepare_material_and_may_not_judge(self):
        may = " ".join(rubric.MODEL_MAY).lower()
        may_not = " ".join(rubric.MODEL_MAY_NOT).lower()
        self.assertIn("retrieve", may)
        self.assertIn("blank", may)
        for forbidden in ("choose a reliability value", "answer the numeric-judgement gate"):
            self.assertIn(forbidden, may_not)
        self.assertIs(doc()["model_use_boundary"]["an_llm_is_not_an_accountable_reviewer"], True)

    def test_there_is_no_origin_a_model_could_be_recorded_under(self):
        origins = {o.value for o in ReliabilityAssessmentOrigin}
        self.assertEqual(origins, {"HUMAN_REVIEW", "DOCUMENTED_METHOD", "CALIBRATED_EMPIRICALLY"})

    def test_software_may_assert_only_the_absence_of_a_document(self):
        self.assertEqual(rubric.SOFTWARE_ASSIGNABLE_STATES, (rubric.ReviewState.NOT_ESTABLISHED,))


class DisagreementIsRepresentedAndNeverAveraged(unittest.TestCase):
    """§18. Semantics defined; multi-review persistence not implemented."""

    def test_the_states_exist_and_averaging_is_refused(self):
        states = {s.value for s in rubric.ReviewAgreement}
        self.assertEqual(
            states, {"AGREEMENT", "DISAGREEMENT_OPEN", "ADJUDICATED", "IRRECONCILABLE"}
        )
        self.assertTrue(rubric.DISAGREEMENT_IS_NEVER_AVERAGED)
        self.assertIs(doc()["disagreement"]["averaging_permitted"], False)

    def test_what_the_existing_architecture_already_answers_is_recorded(self):
        answered = doc()["disagreement"]["already_answered_by_the_existing_architecture"]
        self.assertTrue(answered)
        self.assertTrue(doc()["disagreement"]["not_yet_representable"])


class ReproducibilityAndProvenance(unittest.TestCase):
    """§17, §25. Traceability is required; agreement is not."""

    def test_the_minimum_reproducible_record_names_the_rubric_version(self):
        joined = " ".join(rubric.REPRODUCIBILITY_REQUIREMENTS)
        self.assertIn("rubric id and version", joined)
        self.assertIn("material unknown", joined)

    def test_the_provenance_gap_is_recorded_with_the_narrowest_repair(self):
        gap = doc()["provenance_gap"]
        self.assertEqual(gap["finding"], "RELIABILITY_RUBRIC_PROVENANCE_MODEL_GAP")
        self.assertIn("nullable", gap["narrowest_repair"].lower())
        self.assertIn("basis", gap["why_the_basis_table_is_not_the_answer"].lower())


class HistoricalAssessmentsAreUntouched(unittest.TestCase):
    """§11, §24. Applied structurally, never re-reviewed."""

    def test_both_historical_reviews_are_classified_and_unchanged(self):
        hist = doc()["historical_compatibility"]
        self.assertEqual(len(hist["assessments"]), 2)
        for entry in hist["assessments"]:
            self.assertIs(entry["reliability_unchanged"], True)
            self.assertIn(
                entry["verdict"],
                {
                    "COMPATIBLE",
                    "PARTIALLY_REPRESENTABLE",
                    "HISTORICAL_REVIEW_MISSING_RUBRIC_FIELDS",
                },
            )
            self.assertTrue(entry["dimensions_addressed"])

    def test_neither_historical_value_appears_as_a_recommendation(self):
        rendered = json.dumps(strip_notes(doc()))
        for value in ("0.5", "0.65"):
            self.assertNotIn(f'"reliability": {value}', rendered)
        worked = doc()["worked_example"]
        self.assertIsNone(worked["reviewer_fields"]["reliability"])

    def test_no_anchor_was_derived_from_a_historical_value(self):
        self.assertEqual({a.value for a in rubric.ANCHORS}, {0.0, 1.0})

    def test_the_dimensions_named_by_each_review_are_real_dimensions(self):
        known = {d.id for d in rubric.DIMENSIONS}
        for entry in doc()["historical_compatibility"]["assessments"]:
            for addressed in entry["dimensions_addressed"]:
                self.assertIn(addressed["dimension_id"], known)
            for missing in entry["dimensions_not_addressed"]:
                self.assertIn(missing, known)


class TheTedWorkedExampleIsUnanswered(unittest.TestCase):
    """§20-§23. Facts populated, every judgement blank."""

    def test_the_worked_example_carries_no_value_and_no_reviewer(self):
        worked = doc()["worked_example"]
        self.assertEqual(worked["sufficient_for_numeric_judgement"], "UNANSWERED")
        for key, value in worked["reviewer_fields"].items():
            self.assertIsNone(value, f"{key} must be blank")

    def test_only_not_established_was_assigned_by_software(self):
        for finding in doc()["worked_example"]["dimension_findings"]:
            state = finding["software_assigned_state"]
            if state is not None:
                self.assertEqual(state, rubric.ReviewState.NOT_ESTABLISHED.value)

    def test_every_material_unknown_asks_the_reviewer_and_stays_unanswered(self):
        candidates = doc()["worked_example"]["material_unknown_candidates"]
        self.assertTrue(candidates)
        for candidate in candidates:
            self.assertEqual(candidate["materiality_question"], rubric.MATERIALITY_QUESTION)
            self.assertIsNone(candidate["reviewer_answer"])

    def test_the_correction_and_supersession_unknown_is_preserved(self):
        joined = json.dumps(doc()["worked_example"]["material_unknown_candidates"])
        self.assertIn("corrected", joined)
        self.assertIn("supersedes", joined)

    def test_engineering_validation_and_overlap_are_named_as_non_inputs(self):
        excluded = " ".join(doc()["worked_example"]["not_a_rubric_input"]).lower()
        self.assertIn("engineering validation", excluded)
        self.assertIn("disjoint", excluded)

    def test_no_number_appears_in_the_worked_example(self):
        rendered = json.dumps(strip_notes(doc()["worked_example"]))
        import re

        self.assertIsNone(re.search(r"\b0\.\d+\b", rendered))

    def test_the_markdown_worksheet_is_blank(self):
        text = RUBRIC_MD.read_text(encoding="utf-8")
        self.assertIn("SUFFICIENT_FOR_NUMERIC_JUDGEMENT   UNANSWERED", text)
        self.assertIn("YES / NO / UNSURE   ______", text)
        self.assertIn("reliability                        ______", text)


class NothingElseMoved(unittest.TestCase):
    """§30, §33, §34, §35. A rubric is not a calibration and not an acquisition."""

    def test_the_aggregation_profile_is_still_uncalibrated(self):
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        self.assertEqual(audit["profile"]["status"], "UNCALIBRATED")

    def test_the_rubric_does_not_claim_to_calibrate_anything(self):
        rendered = json.dumps(doc()).lower()
        for phrase in ("calibration label", "profile is calibrated", "fitted parameter"):
            self.assertNotIn(phrase, rendered)

    def test_no_opportunity_score_or_ranking_is_introduced(self):
        rendered = json.dumps(doc()).lower()
        for phrase in ("opportunity score", "ranking", "leaderboard"):
            self.assertNotIn(phrase, rendered)

    def test_the_two_existing_assessments_remain_the_only_ones_referenced(self):
        self.assertEqual(len(doc()["historical_compatibility"]["assessments"]), 2)


if __name__ == "__main__":
    unittest.main()
