"""Mission 1.50 §41.9-29. The contract, exercised where it can be exercised.

Fixtures A, B and E drive the real aggregator. C, D and F are refused UPSTREAM
by design — a semantic mismatch, an unestablished equivalence and a post-hoc
bound never produce a directional Evidence row — so they are asserted against
the contract rather than executed, and the tests say which is which.

The identity half lives in `claim-model`
(`test_threshold_state_identity.py`), because that package owns
`proposition_key`. §38 also forbids creating the evaluator package merely to
host tests, so the contract's own invariants are proved here, against the
package that owns aggregation and against the repository files themselves.

`unittest`, importing only `sros_contracts` and `sros_evidence_aggregation`.
"""

from __future__ import annotations

import json
import pathlib
import unittest
from datetime import UTC, datetime

from sros_contracts import ClaimTemporality, EvidenceDirection, EvidenceIndependenceState
from sros_evidence_aggregation import REFERENCE_PROFILE_V1, aggregate
from sros_evidence_aggregation.items import EvidenceItem

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
CONTRACT = REPO_ROOT / "docs" / "data" / "deterministic-inferred-claim-contract-v1.json"
ADR = (
    REPO_ROOT / "docs" / "architecture" / "adr" / "ADR-037-deterministic-inferred-claim-contract.md"
)
VALIDATE_CLAIMS = REPO_ROOT / "infrastructure" / "scripts" / "validate_claims.py"

MOMENT = datetime(2026, 9, 4, tzinfo=UTC)
CLAIM = "m-ge-100"

SUPPORTS = EvidenceDirection.SUPPORTS
CONTRADICTS = EvidenceDirection.CONTRADICTS
INDEPENDENT = EvidenceIndependenceState.KNOWN_INDEPENDENT
DEPENDENT = EvidenceIndependenceState.KNOWN_DEPENDENT


def contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def fixture(name: str) -> dict:
    return contract()["fixtures"][name]


def item(evidence_id, direction, state, reliability, group=None) -> EvidenceItem:
    """One SYNTHETIC item. Fixture-owned reliability, never a reviewed value."""
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


# ==================================================== §41.16 two independent supports


class FixtureATwoIndependentSupports(unittest.TestCase):
    def setUp(self):
        self.result = run(
            item("A-110", SUPPORTS, INDEPENDENT, 0.6),
            item("B-105", SUPPORTS, INDEPENDENT, 0.5),
        )

    def test_two_support_groups(self):
        self.assertEqual(self.result.support_group_count, 2)

    def test_support_exceeds_the_strongest_member(self):
        self.assertGreater(self.result.masses.support_strength, 0.6)

    def test_the_contract_matches_the_aggregator(self):
        recorded = fixture("A_two_independent_supports")
        self.assertEqual(recorded["support_groups"], self.result.support_group_count)
        self.assertAlmostEqual(
            recorded["support_strength"], self.result.masses.support_strength, places=9
        )
        self.assertTrue(recorded["same_proposition_key"])


# ==================================================== §41.17 contradiction path


class FixtureBContradiction(unittest.TestCase):
    def setUp(self):
        self.result = run(
            item("A-110", SUPPORTS, INDEPENDENT, 0.6),
            item("B-90", CONTRADICTS, INDEPENDENT, 0.5),
        )

    def test_both_witnesses_reach_one_claim(self):
        self.assertEqual(self.result.claim_id, CLAIM)
        self.assertEqual(self.result.raw_evidence_count, 2)

    def test_the_real_contradiction_path_is_reached(self):
        self.assertEqual(self.result.contradiction_group_count, 1)
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

    def test_the_contract_matches_the_aggregator(self):
        recorded = fixture("B_contradiction")
        self.assertTrue(recorded["same_claim_identity"])
        self.assertAlmostEqual(
            recorded["contradiction_strength"], self.result.masses.contradiction_strength, places=9
        )
        self.assertAlmostEqual(
            recorded["masses"]["conflict"], self.result.masses.conflict_mass, places=9
        )


# ==================================================== §41.15 republication


class FixtureEDependentRepublication(unittest.TestCase):
    def setUp(self):
        self.result = run(
            item("A-110", SUPPORTS, DEPENDENT, 0.6, "shared-lineage"),
            item("B-110-republished", SUPPORTS, DEPENDENT, 0.5, "shared-lineage"),
        )

    def test_one_provenance_group(self):
        self.assertEqual(self.result.support_group_count, 1)

    def test_it_does_not_exceed_the_strongest_member(self):
        self.assertAlmostEqual(self.result.masses.support_strength, 0.6, places=9)

    def test_the_contrast_with_independence_is_real(self):
        """Otherwise the assertion above passes for an unrelated reason."""
        independent = run(
            item("A-110", SUPPORTS, INDEPENDENT, 0.6),
            item("B-105", SUPPORTS, INDEPENDENT, 0.5),
        )
        self.assertGreater(independent.masses.support_strength, self.result.masses.support_strength)

    def test_the_contract_does_not_call_it_corroboration(self):
        self.assertFalse(fixture("E_dependent_republication")["became_independent_corroboration"])


# ==================================================== §41.10-14 refused upstream


class RefusedUpstream(unittest.TestCase):
    """These never reach the aggregator, and the tests say so rather than
    pretending to execute them."""

    def test_semantic_mismatch_is_not_applicable_with_no_evidence_row(self):
        mismatch = fixture("C_semantic_mismatch")
        self.assertEqual(mismatch["evaluation_result"], "NOT_APPLICABLE")
        self.assertEqual(mismatch["evidence_rows"], 0)

    def test_unknown_equivalence_produces_no_directional_evidence(self):
        unknown = fixture("D_unknown_equivalence")
        self.assertEqual(unknown["evaluation_result"], "UNKNOWN")
        self.assertEqual(unknown["evidence_rows"], 0)

    def test_both_refusals_are_still_recorded(self):
        """A refusal that leaves no trace is invisible. ADR-021 and ADR-025 use
        the same shape: a refused derivation gets a run record and no Signal."""
        for name in ("C_semantic_mismatch", "D_unknown_equivalence"):
            with self.subTest(fixture=name):
                self.assertTrue(fixture(name)["derivation_record"])

    def test_support_maps_to_supports(self):
        results = {r["result"]: r for r in contract()["evaluation_result_vocabulary"]["results"]}
        self.assertEqual(results["SUPPORTS"]["evidence"], "EvidenceDirection.SUPPORTS")

    def test_contradict_maps_to_contradicts(self):
        results = {r["result"]: r for r in contract()["evaluation_result_vocabulary"]["results"]}
        self.assertEqual(results["CONTRADICTS"]["evidence"], "EvidenceDirection.CONTRADICTS")

    def test_unknown_never_becomes_neutral(self):
        vocabulary = contract()["evaluation_result_vocabulary"]
        self.assertIn("NEUTRAL", vocabulary["unknown_is_not_neutral"].upper())
        results = {r["result"]: r for r in vocabulary["results"]}
        self.assertNotIn("EvidenceDirection", results["UNKNOWN"]["evidence"])

    def test_post_hoc_is_logically_valid_and_calibration_ineligible(self):
        """§5. Provenance changes eligibility, never entailment."""
        post_hoc = fixture("F_post_hoc_threshold")
        self.assertEqual(post_hoc["evaluation_result"], "SUPPORTS")
        self.assertTrue(post_hoc["logically_valid"])
        self.assertFalse(post_hoc["calibration_eligible"])


# ==================================================== §41.9, 18-20 the records


class DerivationProvenanceIsComplete(unittest.TestCase):
    LOAD_BEARING = (
        "derivation_rule_id",
        "derivation_rule_version",
        "evaluator_version",
        "claim_revision_id",
        "input_signal_id",
        "measurement_value",
        "threshold_registration_id",
        "evaluation_result",
        "semantic_equivalence_basis_id",
        "interpretation_kind",
        "rationale",
        "created_at",
    )

    def setUp(self):
        self.record = contract()["derivation_provenance_record"]
        self.fields = {f["field"] for f in self.record["fields"]}

    def test_every_load_bearing_field_is_present(self):
        for field in self.LOAD_BEARING:
            with self.subTest(field=field):
                self.assertIn(field, self.fields)

    def test_every_field_answers_a_named_audit_question(self):
        for field in self.record["fields"]:
            with self.subTest(field=field["field"]):
                self.assertTrue(field["audit_question"].strip())

    def test_no_confidence_on_an_exact_entailment(self):
        self.assertNotIn("derivation_confidence", self.fields)
        absent = {f["field"] for f in self.record["deliberately_absent"]}
        self.assertIn("derivation_confidence", absent)

    def test_reliability_and_independence_are_not_derivation_facts(self):
        for field in ("reliability", "independence"):
            with self.subTest(field=field):
                self.assertNotIn(field, self.fields)

    def test_it_binds_to_the_revision_not_the_claim(self):
        """§19. Binding to the Claim would let a later derivation rewrite the
        reasoning behind an earlier revision."""
        self.assertEqual(self.record["binds_to"], "CLAIM_REVISION")
        self.assertIn("claim_revision_id", self.fields)

    def test_granularity_is_one_rule_and_many_evaluations(self):
        """§20. One prose rationale cannot explain both why A supports and why
        C contradicts."""
        self.assertEqual(self.record["granularity"], "ONE_RULE_PLUS_MANY_EVALUATIONS")

    def test_source_provenance_survives_the_attachment(self):
        """§41.9. The Claim is source-independent; the witness is not."""
        layers = contract()["layer_separation"]
        self.assertEqual(layers["claim_identity"], "SOURCE_INDEPENDENT")
        self.assertEqual(layers["evidence_witness"], "SOURCE_SPECIFIC")
        sources = {w["source"] for w in layers["worked_example"]["witnesses"]}
        self.assertEqual(len(sources), 3)


class ProseIsNeverTheOnlyAuthority(unittest.TestCase):
    """§41.19, §41.20."""

    def test_rationale_alone_cannot_carry_a_load_bearing_fact(self):
        prose = contract()["structured_versus_prose"]
        self.assertTrue(prose["machine_auditable_facts"])
        self.assertIn("ONE", prose["rule"])

    def test_the_machine_auditable_facts_are_structured_fields(self):
        structured = set(contract()["structured_versus_prose"]["machine_auditable_facts"])
        fields = {f["field"] for f in contract()["derivation_provenance_record"]["fields"]}
        registration = {f["field"] for f in contract()["threshold_registration_record"]["fields"]}
        for fact in ("derivation_rule_id", "measurement_value", "evaluation_result"):
            with self.subTest(fact=fact):
                self.assertIn(fact, structured)
                self.assertTrue(fact in fields or fact in registration)

    def test_origin_detail_keeps_one_responsibility(self):
        """§18. The Mission 1.15.4 shape, refused explicitly."""
        selected = contract()["Q1_derivation_provenance"]["selected_model"]
        self.assertEqual(selected, "B")
        models = {m["id"]: m for m in contract()["Q1_derivation_provenance"]["models_considered"]}
        self.assertEqual(models["A"]["verdict"], "REJECTED")
        self.assertIn("two independent questions", models["A"]["why"])

    def test_the_rationale_is_not_model_generated(self):
        self.assertIn("template-owned", contract()["structured_versus_prose"]["no_llm_rationale"])


class ThresholdRegistration(unittest.TestCase):
    def test_post_hoc_and_unknown_are_never_calibration_eligible(self):
        statuses = {s["status"]: s for s in contract()["threshold_registration_record"]["statuses"]}
        for status in ("POST_HOC", "UNKNOWN"):
            with self.subTest(status=status):
                self.assertFalse(statuses[status]["calibration_eligible"])

    def test_the_three_eligible_statuses_exist(self):
        statuses = {s["status"]: s for s in contract()["threshold_registration_record"]["statuses"]}
        for status in ("PREREGISTERED", "SOURCE_NATIVE", "EXTERNAL_NORM"):
            with self.subTest(status=status):
                self.assertTrue(statuses[status]["calibration_eligible"])

    def test_preregistration_compares_retrieval_not_publication(self):
        rule = contract()["threshold_registration_record"]["preregistration_temporal_rule"]
        self.assertIn("retrieved_at", rule["rule"])
        self.assertNotIn("published_at", rule["rule"])

    def test_the_foreknowledge_limit_is_stated(self):
        """The rule is necessary and not sufficient, and says so."""
        rule = contract()["threshold_registration_record"]["preregistration_temporal_rule"]
        self.assertIn("not mean", rule["the_limit_stated_rather_than_hidden"].lower())

    def test_a_held_measurement_is_post_hoc_by_construction(self):
        rule = contract()["threshold_registration_record"]["preregistration_temporal_rule"]
        self.assertTrue(rule["a_measurement_already_held_is_post_hoc_by_construction"])


# ==================================================== §41.21 the guard is untouched


class InterpreterGuardRemainsUntouched(unittest.TestCase):
    def test_validate_claims_still_restricts_the_interpreter_to_observed(self):
        """§10. If this ever fails, the evaluator has been let into the
        interpretation package and the OBSERVED contract has been widened."""
        text = VALIDATE_CLAIMS.read_text(encoding="utf-8")
        self.assertIn("OBSERVED", text)
        self.assertIn("ClaimType", text)

    def test_the_contract_places_the_evaluator_outside_that_package(self):
        boundary = contract()["Q3_evaluator_boundary"]
        self.assertEqual(boundary["selected_model"], "A")
        self.assertNotIn("sros_nlp", boundary["proposed_package"])

    def test_the_evaluator_may_not_import_the_gateway_or_the_registry(self):
        forbidden = {
            d["package"] for d in contract()["Q3_evaluator_boundary"]["forbidden_dependencies"]
        }
        self.assertIn("sros_llm_gateway", forbidden)
        self.assertIn("sros_acquisition", forbidden)

    def test_the_boundary_is_zero_dependency_compatible(self):
        self.assertTrue(contract()["Q3_evaluator_boundary"]["zero_dependency_compatible"])

    def test_the_evaluator_sits_where_the_contract_named_it(self):
        """Mission 1.50 asserted this package DID NOT EXIST, which was true of a
        contract mission that wrote no code. Mission 1.52 created it, and a test
        asserting 0 forever is a test asserting the contract is never implemented
        -- the repair shape of Missions 1.31.1, 1.40, 1.41 and 1.44.1.

        What survives is the boundary, which is what this class is actually for:
        the evaluator lives at the path Q3 named."""
        proposed = REPO_ROOT / contract()["Q3_evaluator_boundary"]["proposed_package"]
        self.assertTrue(proposed.is_dir())

    def test_it_was_not_hosted_in_the_interpretation_package(self):
        """The load-bearing half. Hosting it in `sros_nlp/interpreters` would
        require weakening `validate_claims.py`, and a guard removed to let new
        work through is a guard that never was."""
        interpreters = REPO_ROOT / "services" / "nlp" / "python" / "sros_nlp" / "interpreters"
        for module in interpreters.glob("*.py"):
            with self.subTest(module=module.name):
                self.assertNotIn(
                    "sros_inferred_claim_evaluator", module.read_text(encoding="utf-8")
                )


# ==================================================== §41.22-28 nothing moved


class NothingMoved(unittest.TestCase):
    def test_no_canonical_data_changed(self):
        for name, pair in contract()["counters"].items():
            with self.subTest(counter=name):
                self.assertEqual(pair["before"], pair["after"])

    def test_no_inferred_claim_was_created(self):
        counters = contract()["counters"]
        self.assertEqual(counters["inferred_claims"]["before"], 0)
        self.assertEqual(counters["inferred_claims"]["after"], 0)

    def test_no_migration_was_created(self):
        self.assertFalse(contract()["migration_created"])
        self.assertEqual(contract()["historical_compatibility"]["migrations_created"], 0)

    def test_no_reliability_assessment(self):
        self.assertEqual(contract()["counters"]["reliability_assessments"]["after"], 4)

    def test_reliability_scope_is_unchanged_and_resolves_to_nothing_yet(self):
        reliability = contract()["reliability_and_derivation"]
        self.assertEqual(len(reliability["reliability_scope_unchanged"]), 5)
        self.assertIn("NO_APPLICABLE_ASSESSMENT", reliability["initial_resolution"])

    def test_no_calibration(self):
        statuses = {s["status"]: s for s in contract()["threshold_registration_record"]["statuses"]}
        self.assertFalse(statuses["POST_HOC"]["calibration_eligible"])

    def test_no_model_call_and_no_embedding(self):
        model_use = contract()["model_use"]
        self.assertEqual(model_use["llm_calls"], 0)
        self.assertEqual(model_use["embeddings"], 0)
        self.assertFalse(model_use["semantic_matching_used"])

    def test_no_source_selected_and_no_research_requests(self):
        self.assertIsNone(contract()["source_selected"])
        for value in contract()["network_budget"].values():
            self.assertEqual(value, 0)

    def test_opportunity_unchanged(self):
        counters = contract()["counters"]
        self.assertEqual(counters["opportunities"]["after"], 1)
        self.assertEqual(counters["opportunity_revisions"]["after"], 1)
        self.assertEqual(counters["opportunity_evidence_links"]["after"], 7)

    def test_problem_family_remains_parked(self):
        self.assertEqual(contract()["model_use"]["problem_family_status"], "PARKED")

    def test_the_adr_exists_and_is_accepted(self):
        self.assertTrue(ADR.exists())
        self.assertIn("**Status:** Accepted", ADR.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
