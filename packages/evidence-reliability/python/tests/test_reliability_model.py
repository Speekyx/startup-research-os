"""Reviewed reliability, over synthetic assessments only.

Mission 1.14 §37. **No network, no database, no model.** Every assessment below
is invented, and every reliability VALUE in this file is a test fixture rather
than a reviewed judgement — the suite proves the machinery, and asserting a real
number here would be exactly the fabricated review the mission forbids.

The suite is organised around what must stay impossible:

    §3   a source coefficient, arrived at by any route
    §4   policy approval becoming reliability
    §10  a placeholder standing in for an unknown
    §18  choosing between competing assessments
    §22  human review being called calibration
    §26-§29  reliability inferred from a neighbouring factor
"""

from __future__ import annotations

import unittest
from datetime import UTC, datetime

from sros_contracts import (
    ClaimType,
    ReliabilityAssessmentOrigin,
    ReliabilityBasisType,
    ReliabilityResolutionOutcome,
)
from sros_evidence_reliability import (
    ReliabilityAssessment,
    ReliabilityBasis,
    ReliabilityScope,
    assessment_key,
    resolve_reliability,
    scope_from_claim,
)
from sros_evidence_reliability.model import canonical_json

REVIEWED_AT = datetime(2026, 8, 31, tzinfo=UTC)

# SYNTHETIC, shaped after the real World Bank evidence rows. The scope is real;
# the assessment attached to it below is not, and none like it exists in the
# database.
WB_SCOPE = ReliabilityScope(
    source_id="world-bank",
    resource_id="indicator/SP.POP.TOTL",
    record_kind_id="numeric_observation",
    claim_type=ClaimType.OBSERVED,
    proposition_kind="source_reported_metric_period_change",
)

GDELT_SCOPE = ReliabilityScope(
    source_id="gdelt",
    resource_id="web-ngrams/1gram",
    record_kind_id="lexical_frequency_observation",
    claim_type=ClaimType.OBSERVED,
    proposition_kind="source_reported_term_frequency_change",
)


def basis(**overrides) -> ReliabilityBasis:
    kwargs = {
        "basis_type": ReliabilityBasisType.DATASET_METHODOLOGY,
        "document_title": "A synthetic methodology note",
        "summarized_finding": "States how the dataset is revised.",
        "document_url": "https://example.invalid/methodology",
        "retrieved_at": REVIEWED_AT,
    }
    kwargs.update(overrides)
    return ReliabilityBasis(**kwargs)


def assessment(**overrides) -> ReliabilityAssessment:
    kwargs = {
        "id": "assessment-1",
        "scope": WB_SCOPE,
        "version": 1,
        # A FIXTURE VALUE. Not a judgement about World Bank.
        "reliability": 0.6,
        "origin": ReliabilityAssessmentOrigin.HUMAN_REVIEW,
        "rationale": "A synthetic rationale for a synthetic assessment.",
        "stated_limitation": "Invented for a test; bounded by being invented.",
        "reviewed_by": "test-fixture",
        "reviewed_at": REVIEWED_AT,
        "basis": (basis(),),
    }
    kwargs.update(overrides)
    return ReliabilityAssessment(**kwargs)


# ============================================================= §16 scope identity


class TestScopeIdentity(unittest.TestCase):
    def test_the_key_is_deterministic_over_the_five_scope_parts(self):
        self.assertEqual(WB_SCOPE.key, assessment_key(WB_SCOPE))
        self.assertEqual(len(WB_SCOPE.key), 64)

    def test_every_scope_part_moves_the_key(self):
        """A scope missing one part would match more evidence than it was
        reviewed for, which is how a purpose-relative judgement becomes a
        source coefficient."""
        variants = [
            ReliabilityScope(
                "eurostat",
                *tuple(WB_SCOPE.to_json().values())[1:3],
                ClaimType.OBSERVED,
                WB_SCOPE.proposition_kind,
            ),
            ReliabilityScope(
                WB_SCOPE.source_id,
                "indicator/NY.GDP.MKTP.CD",
                WB_SCOPE.record_kind_id,
                ClaimType.OBSERVED,
                WB_SCOPE.proposition_kind,
            ),
            ReliabilityScope(
                WB_SCOPE.source_id,
                WB_SCOPE.resource_id,
                "lexical_frequency_observation",
                ClaimType.OBSERVED,
                WB_SCOPE.proposition_kind,
            ),
            ReliabilityScope(
                WB_SCOPE.source_id,
                WB_SCOPE.resource_id,
                WB_SCOPE.record_kind_id,
                ClaimType.INFERRED,
                WB_SCOPE.proposition_kind,
            ),
            ReliabilityScope(
                WB_SCOPE.source_id,
                WB_SCOPE.resource_id,
                WB_SCOPE.record_kind_id,
                ClaimType.OBSERVED,
                "asserts_market_demand",
            ),
        ]
        keys = {WB_SCOPE.key} | {v.key for v in variants}
        self.assertEqual(len(keys), 6)

    def test_a_scope_part_may_not_be_blank(self):
        for field in ("source_id", "resource_id", "record_kind_id", "proposition_kind"):
            parts = dict(
                source_id="s",
                resource_id="r",
                record_kind_id="k",
                claim_type=ClaimType.OBSERVED,
                proposition_kind="p",
            )
            parts[field] = "   "
            with self.assertRaises(ValueError):
                ReliabilityScope(**parts)

    def test_the_key_is_stable_under_field_order(self):
        rebuilt = ReliabilityScope(
            **{
                "proposition_kind": WB_SCOPE.proposition_kind,
                "claim_type": WB_SCOPE.claim_type,
                "record_kind_id": WB_SCOPE.record_kind_id,
                "resource_id": WB_SCOPE.resource_id,
                "source_id": WB_SCOPE.source_id,
            }
        )
        self.assertEqual(WB_SCOPE.key, rebuilt.key)

    def test_the_scope_carries_no_volatile_metadata(self):
        """§16. Nothing that changes between runs may enter identity."""
        serialised = canonical_json(WB_SCOPE.to_json())
        for forbidden in ("reviewed_at", "created_at", "workspace", "session", "correlation"):
            self.assertNotIn(forbidden, serialised)

    def test_the_signal_type_is_not_part_of_the_scope(self):
        """The derivation between measurement and proposition is the
        interpreter's business; whether it read the Signal correctly is
        extraction_confidence, a different field."""
        self.assertNotIn("signal_type", canonical_json(WB_SCOPE.to_json()))


# ==================================================== §3 never a source coefficient


class TestNoSourceCoefficient(unittest.TestCase):
    def test_a_source_alone_matches_nothing(self):
        """The whole point. An assessment for World Bank population restatement
        does not apply to a different World Bank resource."""
        other_resource = ReliabilityScope(
            "world-bank",
            "indicator/NY.GDP.MKTP.CD",
            "numeric_observation",
            ClaimType.OBSERVED,
            "source_reported_metric_period_change",
        )
        result = resolve_reliability(scope=other_resource, candidates=[assessment()])
        self.assertIs(result.outcome, ReliabilityResolutionOutcome.NO_APPLICABLE_ASSESSMENT)
        self.assertIsNone(result.reliability)

    def test_the_framework_example_works_out(self):
        """A World Bank population figure is dependable evidence about what
        World Bank reported and worthless evidence of software spending. The
        second has a different proposition kind and matches nothing."""
        demand = ReliabilityScope(
            "world-bank",
            "indicator/SP.POP.TOTL",
            "numeric_observation",
            ClaimType.INFERRED,
            "asserts_willingness_to_pay",
        )
        self.assertIs(
            resolve_reliability(scope=demand, candidates=[assessment()]).outcome,
            ReliabilityResolutionOutcome.NO_APPLICABLE_ASSESSMENT,
        )

    def test_a_different_claim_type_over_the_same_measurement_matches_nothing(self):
        inferred = ReliabilityScope(
            WB_SCOPE.source_id,
            WB_SCOPE.resource_id,
            WB_SCOPE.record_kind_id,
            ClaimType.INFERRED,
            WB_SCOPE.proposition_kind,
        )
        self.assertIs(
            resolve_reliability(scope=inferred, candidates=[assessment()]).outcome,
            ReliabilityResolutionOutcome.NO_APPLICABLE_ASSESSMENT,
        )

    def test_the_package_names_no_source(self):
        """§3, structurally. The resolver matches data against data; a source
        id written into this package would be the coefficient by another name."""
        import ast
        import pathlib

        import sros_evidence_reliability as package

        registered = {"world-bank", "gdelt", "eurostat", "fred", "reddit", "github"}
        found: list[str] = []
        for path in pathlib.Path(package.__file__).parent.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            docstrings = {
                ast.get_docstring(n)
                for n in ast.walk(tree)
                if isinstance(n, ast.Module | ast.ClassDef | ast.FunctionDef)
            }
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and node.value in registered
                    and node.value not in docstrings
                ):
                    found.append(f"{path.name}: {node.value}")
        self.assertEqual(found, [])


# ================================================ §4 policy approval is not reliability


class TestPolicyIsNotReliability(unittest.TestCase):
    def test_the_package_knows_nothing_about_approval_states(self):
        """An APPROVED source does not produce more reliable evidence, and a
        RESTRICTED one does not produce less. There is no field to carry it."""
        import inspect

        import sros_evidence_reliability.model as model

        text = inspect.getsource(model)
        # As tokens in CODE, not in the prose that explains the rule: this file
        # and that module both discuss approval, which must not fail the check.
        import ast

        tree = ast.parse(text)
        docstrings = {
            ast.get_docstring(n)
            for n in ast.walk(tree)
            if isinstance(n, ast.Module | ast.ClassDef | ast.FunctionDef)
        }
        literals = [
            n.value
            for n in ast.walk(tree)
            if isinstance(n, ast.Constant)
            and isinstance(n.value, str)
            and n.value not in docstrings
        ]
        for forbidden in ("APPROVED", "APPROVED_WITH_CONDITIONS", "RESTRICTED", "PROHIBITED"):
            self.assertNotIn(forbidden, literals)

    def test_an_assessment_has_no_field_for_a_policy_state(self):
        from dataclasses import fields

        names = {f.name for f in fields(ReliabilityAssessment)}
        self.assertTrue(names.isdisjoint({"approval_state", "policy_status", "lifecycle"}))


# =========================================================== §7 basis is required


class TestBasisRequirement(unittest.TestCase):
    def test_an_assessment_needs_a_document_backed_basis(self):
        with self.assertRaises(ValueError) as caught:
            assessment(basis=())
        self.assertIn("retrieved document", str(caught.exception))

    def test_reviewer_reasoning_alone_is_not_a_basis(self):
        """ "World Bank is trustworthy" is a sentence, not a basis. Reasoning is
        permitted alongside documents and never instead of them."""
        opinion = ReliabilityBasis(
            basis_type=ReliabilityBasisType.REVIEWER_DOCUMENTED_JUDGEMENT,
            document_title="Reviewer note",
            summarized_finding="The publisher is reputable.",
        )
        with self.assertRaises(ValueError):
            assessment(basis=(opinion,))

    def test_reviewer_reasoning_is_permitted_beside_a_document(self):
        opinion = ReliabilityBasis(
            basis_type=ReliabilityBasisType.REVIEWER_DOCUMENTED_JUDGEMENT,
            document_title="Reviewer note",
            summarized_finding="Reads the revision policy as bounding a snapshot claim.",
        )
        self.assertEqual(len(assessment(basis=(basis(), opinion)).basis), 2)

    def test_a_document_backed_basis_names_a_retrieved_document(self):
        for missing in ({"document_url": None}, {"retrieved_at": None}):
            with self.assertRaises(ValueError):
                basis(**missing)

    def test_a_basis_says_what_it_found(self):
        with self.assertRaises(ValueError):
            basis(summarized_finding="   ")

    def test_a_long_excerpt_is_refused(self):
        """A long excerpt is a copy of third-party text, not a reference."""
        with self.assertRaises(ValueError):
            basis(excerpt="x" * 1001)


# ========================================================== §8 origin and authority


class TestOriginAndAuthority(unittest.TestCase):
    def test_there_is_no_model_originated_value(self):
        """§8, §43. A model may help a reviewer read documentation; it may not
        be the epistemic source. A closed vocabulary with nowhere to record a
        guess is what makes that enforceable rather than merely stated."""
        self.assertEqual(
            {o.value for o in ReliabilityAssessmentOrigin},
            {"HUMAN_REVIEW", "DOCUMENTED_METHOD", "CALIBRATED_EMPIRICALLY"},
        )

    def test_an_assessment_names_its_reviewer(self):
        with self.assertRaises(ValueError):
            assessment(reviewed_by="  ")

    def test_human_review_is_not_calibration(self):
        """§22. However careful a reviewer was, they fitted nothing to data."""
        with self.assertRaises(ValueError) as caught:
            assessment(calibration_dataset_ref="some-dataset")
        self.assertIn("not statistical calibration", str(caught.exception))

    def test_calibrated_empirically_must_name_its_dataset(self):
        with self.assertRaises(ValueError) as caught:
            assessment(origin=ReliabilityAssessmentOrigin.CALIBRATED_EMPIRICALLY)
        self.assertIn("calibration dataset", str(caught.exception))

    def test_a_calibrated_assessment_is_permitted_with_its_dataset(self):
        item = assessment(
            origin=ReliabilityAssessmentOrigin.CALIBRATED_EMPIRICALLY,
            calibration_dataset_ref="labelled-outcomes-v1",
        )
        self.assertIs(item.origin, ReliabilityAssessmentOrigin.CALIBRATED_EMPIRICALLY)


# ================================================ §9-§10 scale and placeholder values


class TestScaleAndPlaceholders(unittest.TestCase):
    def test_reliability_is_on_the_unit_interval(self):
        for value in (-0.1, 1.4):
            with self.assertRaises(ValueError):
                assessment(reliability=value)

    def test_the_endpoints_are_permitted(self):
        for value in (0.0, 1.0):
            self.assertEqual(assessment(reliability=value).reliability, value)

    def test_out_of_range_is_rejected_not_clamped(self):
        with self.assertRaises(ValueError) as caught:
            assessment(reliability=1.4)
        self.assertIn("rather than clamped", str(caught.exception))

    def test_an_assessment_states_what_bounds_it(self):
        """A reliability with no stated limitation is a number nobody can
        argue with."""
        for blank in ({"rationale": "  "}, {"stated_limitation": "  "}):
            with self.assertRaises(ValueError):
                assessment(**blank)

    def test_unknown_is_absence_not_a_number(self):
        """§10. There is no way to express "unknown" as a value: an assessment
        that asserts nothing is not an assessment, and unknown is the absence
        of a row."""
        result = resolve_reliability(scope=GDELT_SCOPE, candidates=[])
        self.assertIsNone(result.reliability)
        self.assertNotIn("reliability", result.to_json())

    def test_no_threshold_labels_exist(self):
        """§9. No 0.9 = authoritative, no 0.7 = good."""
        import inspect

        import sros_evidence_reliability.model as model

        for label in ("authoritative", "excellent", "good", "poor", "medium-high"):
            self.assertNotIn(f'"{label}"', inspect.getsource(model))


# ================================================== §18 applicability, fail-closed


class TestApplicability(unittest.TestCase):
    def test_one_applicable_assessment_resolves(self):
        result = resolve_reliability(scope=WB_SCOPE, candidates=[assessment()])
        self.assertIs(result.outcome, ReliabilityResolutionOutcome.RESOLVED)
        self.assertEqual(result.reliability, 0.6)
        self.assertIsNotNone(result.binding)

    def test_no_applicable_assessment_leaves_reliability_unknown(self):
        result = resolve_reliability(scope=GDELT_SCOPE, candidates=[assessment()])
        self.assertIs(result.outcome, ReliabilityResolutionOutcome.NO_APPLICABLE_ASSESSMENT)
        self.assertIsNone(result.reliability)

    def test_competing_assessments_are_refused(self):
        """§18. Never the closest, never the max, never the mean: averaging two
        competing reviewed judgements produces a third nobody made."""
        result = resolve_reliability(
            scope=WB_SCOPE,
            candidates=[
                assessment(id="a", reliability=0.4),
                assessment(id="b", reliability=0.9, version=2),
            ],
        )
        self.assertIs(result.outcome, ReliabilityResolutionOutcome.AMBIGUOUS_ASSESSMENTS)
        self.assertIsNone(result.reliability)
        self.assertEqual(result.candidates, ("a", "b"))

    def test_a_superseded_assessment_does_not_apply(self):
        superseded = assessment(superseded_at=REVIEWED_AT, superseded_reason="methodology restated")
        result = resolve_reliability(scope=WB_SCOPE, candidates=[superseded])
        self.assertIs(result.outcome, ReliabilityResolutionOutcome.SUPERSEDED_ONLY)
        self.assertIsNone(result.reliability)

    def test_superseded_only_is_distinct_from_never_assessed(self):
        """Somebody reviewed this and withdrew it is a different fact from
        nobody having looked."""
        withdrawn = resolve_reliability(
            scope=WB_SCOPE,
            candidates=[assessment(superseded_at=REVIEWED_AT, superseded_reason="r")],
        ).outcome
        never = resolve_reliability(scope=WB_SCOPE, candidates=[]).outcome
        self.assertIsNot(withdrawn, never)

    def test_the_current_version_wins_over_its_superseded_predecessor(self):
        result = resolve_reliability(
            scope=WB_SCOPE,
            candidates=[
                assessment(
                    id="v1",
                    version=1,
                    reliability=0.4,
                    superseded_at=REVIEWED_AT,
                    superseded_reason="restated",
                ),
                assessment(id="v2", version=2, reliability=0.7),
            ],
        )
        self.assertIs(result.outcome, ReliabilityResolutionOutcome.RESOLVED)
        self.assertEqual(result.reliability, 0.7)
        assert result.binding is not None
        self.assertEqual(result.binding.version, 2)

    def test_versions_coexist_so_history_stays_readable(self):
        """§17. An aggregation that used version 1 must still be able to read
        version 1 after version 2 lands."""
        v1 = assessment(
            id="v1",
            version=1,
            reliability=0.4,
            superseded_at=REVIEWED_AT,
            superseded_reason="restated",
        )
        v2 = assessment(id="v2", version=2, reliability=0.7)
        self.assertEqual(v1.key, v2.key)
        self.assertEqual(v1.reliability, 0.4)
        self.assertEqual(v2.reliability, 0.7)

    def test_half_a_supersession_is_refused(self):
        with self.assertRaises(ValueError):
            assessment(superseded_at=REVIEWED_AT)
        with self.assertRaises(ValueError):
            assessment(superseded_reason="restated")


# ====================================================== §19 precedence and binding


class TestPrecedenceAndBinding(unittest.TestCase):
    def test_a_directly_supplied_value_wins_and_consults_nothing(self):
        """A statement about THAT record is more specific than a class-level
        judgement, and consulting both would create two answers to one
        question."""
        result = resolve_reliability(scope=WB_SCOPE, candidates=[assessment()], supplied=0.3)
        self.assertIs(result.outcome, ReliabilityResolutionOutcome.DIRECTLY_SUPPLIED)
        self.assertEqual(result.reliability, 0.3)
        self.assertIsNone(result.binding)

    def test_a_supplied_value_out_of_range_is_refused(self):
        with self.assertRaises(ValueError):
            resolve_reliability(scope=WB_SCOPE, supplied=1.4)

    def test_the_binding_records_everything_needed_to_reconstruct_the_number(self):
        """§20. Do not produce a score whose coefficients cannot be
        reconstructed."""
        result = resolve_reliability(scope=WB_SCOPE, candidates=[assessment()])
        assert result.binding is not None
        payload = result.binding.to_json()
        self.assertEqual(
            sorted(payload),
            [
                "assessment_id",
                "assessment_key",
                "origin",
                "reliability",
                "reviewed_at",
                "reviewed_by",
                "version",
            ],
        )

    def test_every_outcome_is_reported_even_when_there_is_no_number(self):
        for result in (
            resolve_reliability(scope=WB_SCOPE, candidates=[]),
            resolve_reliability(scope=None),
        ):
            self.assertIn("outcome", result.to_json())
            self.assertTrue(result.to_json()["detail"])


# ============================================ §26-§29 no inference from neighbours


class TestNoPropagation(unittest.TestCase):
    def test_a_claim_with_no_proposition_kind_has_no_scope(self):
        """It cannot state its purpose, so no assessment can apply. A scope
        guessed for it would apply a judgement reviewed for something else."""
        self.assertIsNone(
            scope_from_claim(
                source_id="world-bank",
                resource_id="indicator/SP.POP.TOTL",
                record_kind_id="numeric_observation",
                claim_type=ClaimType.OBSERVED,
                proposition_facts={"metric_id": "SP.POP.TOTL"},
            )
        )

    def test_a_scope_is_built_from_the_claims_own_discriminator(self):
        scope = scope_from_claim(
            source_id="world-bank",
            resource_id="indicator/SP.POP.TOTL",
            record_kind_id="numeric_observation",
            claim_type=ClaimType.OBSERVED,
            proposition_facts={"proposition": "source_reported_metric_period_change"},
        )
        self.assertEqual(scope, WB_SCOPE)

    def test_the_resolver_takes_no_other_factor(self):
        """§26-§29. Relevance, directness, extraction confidence and claim
        confidence are all 1.0 on the real rows, and none of them is an
        argument here. There is no propagation formula because there is
        nowhere to put one."""
        import inspect

        signature = inspect.signature(resolve_reliability)
        self.assertEqual(sorted(signature.parameters), ["candidates", "scope", "supplied"])

    def test_a_deterministic_interpreter_earns_no_reliability(self):
        """The seven real rows carry extraction_confidence 1.0 and
        interpretation confidence 1.0. Neither produces a value here."""
        result = resolve_reliability(scope=WB_SCOPE, candidates=[])
        self.assertIsNone(result.reliability)


if __name__ == "__main__":
    unittest.main()
