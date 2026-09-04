"""Mission 1.49. The two-layer decision, exercised where it can be exercised.

The semantic decision is in ADR-036; what this file asserts is the half that can
be RUN. Fixtures A, B and D drive the real aggregator and demonstrate the three
behaviours the decision depends on: two independent supports exceed the
pass-through, a support and a contradiction inhabit ONE Claim and produce
non-zero conflict mass, and a republication stays one group.

Fixtures C and E never reach the aggregator, by design -- a semantic mismatch and
a post-hoc threshold are refused UPSTREAM -- so they are asserted against the
record rather than executed. Saying which is which matters: a test that pretended
to execute them would be testing nothing.

All fixture reliability values are FIXTURE-OWNED (0.6, 0.5). They are not
reviewed values and no reviewed value is copied.

`unittest`, importing only `sros_contracts` and `sros_evidence_aggregation` --
the packages the zero-dependency runner puts on this suite's path (§34).
"""

from __future__ import annotations

import json
import pathlib
import unittest
from datetime import UTC, datetime

from sros_contracts import ClaimTemporality, ClaimType, EvidenceDirection, EvidenceIndependenceState
from sros_evidence_aggregation import REFERENCE_PROFILE_V1, aggregate
from sros_evidence_aggregation.items import EvidenceItem

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
RECORD = REPO_ROOT / "docs" / "data" / "source-independent-claim-semantics-v1.json"
ADR = REPO_ROOT / "docs" / "architecture" / "adr" / "ADR-036-source-independent-claim-semantics.md"

MOMENT = datetime(2026, 9, 4, tzinfo=UTC)
CLAIM = "m-ge-100"


def record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def fixture(name: str) -> dict:
    return record()["fixtures"][name]


def item(
    evidence_id: str,
    direction: EvidenceDirection,
    state: EvidenceIndependenceState,
    reliability: float,
    group: str | None = None,
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        direction=direction,
        relevance=1.0,
        directness=1.0,
        reliability=reliability,
        extraction_confidence=1.0,
        independence_state=state,
        independence_group_id=group,
        observed_at=None,
    )


def run(*items: EvidenceItem):
    return aggregate(
        CLAIM,
        items,
        REFERENCE_PROFILE_V1,
        temporality=ClaimTemporality.EVERGREEN,
        now=MOMENT,
        allow_uncalibrated=True,
    )


SUPPORTS = EvidenceDirection.SUPPORTS
CONTRADICTS = EvidenceDirection.CONTRADICTS
INDEPENDENT = EvidenceIndependenceState.KNOWN_INDEPENDENT
DEPENDENT = EvidenceIndependenceState.KNOWN_DEPENDENT


# ============================================ INFERRED is not a model claim (§3, §4)


class InferredDoesNotImplyAModel(unittest.TestCase):
    """The assumption the mission was told not to make, refused against the
    generated contract rather than against prose."""

    def test_inferred_is_a_claim_type_member(self):
        self.assertIn("INFERRED", {member.value for member in ClaimType})

    def test_the_model_associated_type_is_predicted_not_inferred(self):
        self.assertIn("PREDICTED", {member.value for member in ClaimType})
        self.assertIsNot(ClaimType.INFERRED, ClaimType.PREDICTED)

    def test_the_record_reports_the_two_axes_as_orthogonal(self):
        correction = record()["the_central_correction"]
        self.assertEqual(correction["measured"]["claims_with_model_version"], 0)
        self.assertEqual(correction["measured"]["live_claim_types"], {"OBSERVED": 43})

    def test_a_deterministic_derivation_may_create_a_source_independent_proposition(self):
        kinds = {k["kind"]: k for k in record()["inference_taxonomy"]["kinds"]}
        self.assertEqual(
            kinds["DETERMINISTIC_DERIVATION"]["can_create_source_independent_proposition"], "YES"
        )

    def test_generative_synthesis_may_not(self):
        kinds = {k["kind"]: k for k in record()["inference_taxonomy"]["kinds"]}
        self.assertEqual(
            kinds["GENERATIVE_SYNTHESIS"]["can_create_source_independent_proposition"], "NO"
        )


# ============================================ Fixture A — independent corroboration


class FixtureAIndependentCorroboration(unittest.TestCase):
    def setUp(self):
        self.result = run(
            item("A-110", SUPPORTS, INDEPENDENT, 0.6),
            item("B-105", SUPPORTS, INDEPENDENT, 0.5),
        )

    def test_two_independent_supports_form_two_groups(self):
        self.assertEqual(self.result.support_group_count, 2)

    def test_support_strength_exceeds_the_strongest_member(self):
        """The first shape in this repository that would make the full
        aggregator differ from the B-2 pass-through baseline."""
        self.assertGreater(self.result.masses.support_strength, 0.6)

    def test_the_recorded_fixture_matches_what_the_aggregator_produces(self):
        recorded = fixture("A_independent_corroboration")
        self.assertEqual(recorded["support_groups"], self.result.support_group_count)
        self.assertAlmostEqual(
            recorded["support_strength"], self.result.masses.support_strength, places=9
        )
        self.assertTrue(recorded["exceeds_pass_through"])


# ============================================ Fixture B — contradiction on ONE Claim


class FixtureBContradiction(unittest.TestCase):
    def setUp(self):
        self.result = run(
            item("A-110", SUPPORTS, INDEPENDENT, 0.6),
            item("B-90", CONTRADICTS, INDEPENDENT, 0.5),
        )

    def test_both_witnesses_inhabit_one_claim(self):
        """The architectural point. They share a claim id because the
        measurement VALUE is not proposition identity."""
        self.assertEqual(self.result.claim_id, CLAIM)
        self.assertEqual(self.result.raw_evidence_count, 2)

    def test_one_support_group_and_one_contradiction_group(self):
        self.assertEqual(self.result.support_group_count, 1)
        self.assertEqual(self.result.contradiction_group_count, 1)

    def test_contradiction_strength_and_conflict_mass_are_non_zero(self):
        self.assertGreater(self.result.masses.contradiction_strength, 0)
        self.assertGreater(self.result.masses.conflict_mass, 0)

    def test_the_four_masses_sum_to_one(self):
        masses = self.result.masses
        total = (
            masses.supported_mass
            + masses.contradicted_mass
            + masses.conflict_mass
            + masses.uncertainty_mass
        )
        self.assertAlmostEqual(total, 1.0, places=9)

    def test_the_recorded_fixture_matches_what_the_aggregator_produces(self):
        recorded = fixture("B_contradiction")
        masses = self.result.masses
        self.assertTrue(recorded["same_claim_identity"])
        self.assertAlmostEqual(recorded["masses"]["conflict"], masses.conflict_mass, places=9)
        self.assertAlmostEqual(
            recorded["contradiction_strength"], masses.contradiction_strength, places=9
        )


# ============================================ Fixture D — republication is not corroboration


class FixtureDDependentRepublication(unittest.TestCase):
    def setUp(self):
        self.result = run(
            item("A-110", SUPPORTS, DEPENDENT, 0.6, "shared-lineage"),
            item("B-110-republished", SUPPORTS, DEPENDENT, 0.5, "shared-lineage"),
        )

    def test_a_republication_collapses_into_one_group(self):
        self.assertEqual(self.result.support_group_count, 1)

    def test_it_does_not_exceed_the_strongest_member(self):
        """Republication raises observed volume, never evidence strength.
        Contrast with fixture A, which is the same two rows under established
        independence and DOES exceed it."""
        self.assertAlmostEqual(self.result.masses.support_strength, 0.6, places=9)

    def test_the_contrast_with_fixture_a_is_real(self):
        independent = run(
            item("A-110", SUPPORTS, INDEPENDENT, 0.6),
            item("B-105", SUPPORTS, INDEPENDENT, 0.5),
        )
        self.assertGreater(independent.masses.support_strength, self.result.masses.support_strength)

    def test_the_record_does_not_call_it_corroboration(self):
        self.assertFalse(fixture("D_dependent_republication")["became_corroboration"])


# ==================================== Fixtures C and E — refused upstream, not executed


class FixturesRefusedUpstream(unittest.TestCase):
    """These never reach the aggregator, which is the design. Asserting them
    against the record is honest; pretending to execute them would not be."""

    def test_a_semantic_mismatch_is_not_applicable_rather_than_contradicting(self):
        mismatch = fixture("C_semantic_mismatch")
        self.assertEqual(mismatch["expected"], "NOT_APPLICABLE")
        self.assertEqual(mismatch["not"], "CONTRADICTS")

    def test_the_evaluation_function_refuses_a_mismatch_before_attachment(self):
        rules = {r["outcome"]: r["condition"] for r in record()["evaluation_function"]["rules"]}
        self.assertIn("NOT_APPLICABLE", rules)
        self.assertIn("not", rules["NOT_APPLICABLE"].lower())

    def test_the_evaluation_function_uses_no_model_and_no_probability(self):
        evaluation = record()["evaluation_function"]
        self.assertTrue(evaluation["no_model"])
        self.assertTrue(evaluation["no_probability"])

    def test_a_post_hoc_threshold_is_calibration_ineligible(self):
        self.assertFalse(fixture("E_post_hoc_threshold")["calibration_eligible"])

    def test_unknown_threshold_provenance_is_also_ineligible(self):
        """Uncertainty is never permission: UNKNOWN must not default to
        preregistered."""
        statuses = {
            s["status"]: s["calibration_eligible"]
            for s in record()["threshold_preregistration"]["statuses"]
        }
        self.assertFalse(statuses["UNKNOWN"])
        self.assertFalse(statuses["POST_HOC"])
        self.assertTrue(statuses["PREREGISTERED"])


# ============================================ the decision and its invariants


class TheDecision(unittest.TestCase):
    def test_exactly_one_preferred_model(self):
        preferred = [
            m for m in record()["model_comparison"]["models"] if m["verdict"] == "PREFERRED"
        ]
        self.assertEqual(len(preferred), 1)
        self.assertEqual(preferred[0]["id"], "A")

    def test_cross_source_observed_convergence_was_rejected(self):
        models = {m["id"]: m for m in record()["model_comparison"]["models"]}
        self.assertEqual(models["B"]["verdict"], "REJECTED")
        self.assertIn("fabrication with a citation", models["B"]["why"])

    def test_a_new_claim_type_was_found_unnecessary_not_merely_unwanted(self):
        models = {m["id"]: m for m in record()["model_comparison"]["models"]}
        self.assertEqual(models["C"]["verdict"], "UNNECESSARY")

    def test_deliberate_absence_was_evaluated_and_rejected_with_a_stated_cost(self):
        models = {m["id"]: m for m in record()["model_comparison"]["models"]}
        self.assertEqual(models["D"]["verdict"], "REJECTED")
        self.assertIn("cost", models["D"]["why"])

    def test_all_fifteen_invariants_are_recorded(self):
        recorded = {i["id"] for i in record()["semantic_invariants"]}
        self.assertEqual(recorded, {f"I{n}" for n in range(1, 16)})

    def test_the_adr_exists_and_states_the_decision(self):
        self.assertTrue(ADR.exists())
        text = ADR.read_text(encoding="utf-8")
        self.assertIn("INFERRED", text)
        self.assertIn("Accepted", text)

    def test_reliability_scope_stays_source_relative(self):
        reliability = record()["reliability_semantics"]
        self.assertTrue(reliability["scope_stays_source_relative"])
        self.assertIn("source_id", reliability["scope"])

    def test_measurement_reliability_and_derivation_validity_are_kept_apart(self):
        split = record()["reliability_semantics"]["measurement_reliability_vs_derivation_validity"]
        self.assertNotEqual(split["MEASUREMENT_RELIABILITY"], split["DERIVATION_VALIDITY"])
        self.assertTrue(split["must_not_be_multiplied"].strip())
        self.assertTrue(split["derivation_provenance_required"])


class NothingMoved(unittest.TestCase):
    def test_no_counter_changed(self):
        for name, pair in record()["counters"].items():
            with self.subTest(counter=name):
                self.assertEqual(pair["before"], pair["after"])

    def test_historical_claims_are_unchanged(self):
        history = record()["historical_compatibility"]
        self.assertEqual(history["claims_unchanged"], 43)
        self.assertEqual(history["revisions_unchanged"], 44)
        self.assertEqual(history["evidence_unchanged"], 57)
        self.assertEqual(history["proposition_identities_rewritten"], 0)
        self.assertEqual(history["migrations_recommended"], 0)

    def test_no_source_selected(self):
        self.assertIsNone(record()["source_selected"])

    def test_no_research_or_documentation_requests(self):
        for value in record()["network_budget"].values():
            self.assertEqual(value, 0)

    def test_no_model_call_and_no_embedding(self):
        model_use = record()["model_use"]
        self.assertEqual(model_use["llm_calls"], 0)
        self.assertEqual(model_use["embeddings"], 0)
        self.assertFalse(model_use["semantic_matching_used"])

    def test_problem_family_remains_parked(self):
        self.assertEqual(record()["model_use"]["problem_family_status"], "PARKED")


if __name__ == "__main__":
    unittest.main()
