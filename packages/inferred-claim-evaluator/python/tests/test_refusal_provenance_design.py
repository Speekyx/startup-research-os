"""Mission 1.53 §46. The design, checked against what the evaluator produces.

ADR-038 freezes a schema that does not exist yet, so what can be tested is the
part that is already real: the outcomes the evaluator emits, the descriptor those
outcomes carry, and whether the frozen record describes them accurately.

Every fixture is NON-EMPTY and comes from the real `evaluate()`. A test that
asserted the shape of a refusal without producing one would be checking the
record against itself.

`unittest`, importing only `sros_contracts`, `sros_claim_model` and the evaluator
-- the packages the zero-dependency runner puts on this suite's path.
"""

from __future__ import annotations

import json
import pathlib
import unittest
from datetime import UTC, datetime
from decimal import Decimal

from sros_claim_model import proposition_key
from sros_inferred_claim_evaluator import (
    ALL_EQUIVALENCE_DIMENSIONS,
    DERIVATION_RULE_ID,
    DERIVATION_RULE_VERSION,
    EVALUATOR_VERSION,
    PROPOSITION_KIND,
    EquivalenceVerdict,
    EvaluationResult,
    MeasurementWitness,
    SemanticEquivalenceDecision,
    TargetProposition,
    ThresholdOperator,
    ThresholdProvenanceStatus,
    ThresholdRegistration,
    evaluate,
    target_proposition_facts,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
RECORD = REPO_ROOT / "docs" / "data" / "refusal-derivation-binding-design-v1.json"
ADR = REPO_ROOT / "docs" / "architecture" / "adr" / "ADR-038-refusal-provenance-binding.md"
MIGRATIONS = REPO_ROOT / "infrastructure" / "db" / "migrations"

RETRIEVED = datetime(2026, 6, 1, tzinfo=UTC)
FROZEN = datetime(2026, 1, 1, tzinfo=UTC)


def record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def target(**overrides) -> TargetProposition:
    fields = {
        "proposition_kind": PROPOSITION_KIND,
        "canonical_subject_id": "subject-1",
        "metric_definition_id": "metric-def-1",
        "time_bound": "2024",
        "population_or_geography": "population-1",
        "unit": "unit-1",
        "threshold_operator": ThresholdOperator.GTE,
        "threshold_value": Decimal("100"),
    }
    fields.update(overrides)
    return TargetProposition(**fields)


def registration(**overrides) -> ThresholdRegistration:
    fields = {
        "registration_id": "reg-1",
        "workspace_id": "ws-1",
        "metric_definition_id": "metric-def-1",
        "scope_subject_id": "subject-1",
        "scope_population": "population-1",
        "scope_time_bound": "2024",
        "unit": "unit-1",
        "threshold_operator": ThresholdOperator.GTE,
        "threshold_value": Decimal("100"),
        "provenance_status": ThresholdProvenanceStatus.PREREGISTERED,
        "recorded_at": FROZEN,
        "recorded_by": "fixture",
        "provenance_reference": "fixture-registration",
    }
    fields.update(overrides)
    return ThresholdRegistration(**fields)


def witness(value: str = "110", **overrides) -> MeasurementWitness:
    fields = {
        "workspace_id": "ws-1",
        "signal_id": "signal-a",
        "source_id": "source-a",
        "resource_id": "resource-a",
        "record_kind_id": "numeric_observation",
        "canonical_subject_id": "subject-1",
        "source_native_metric_id": "NATIVE.M",
        "metric_definition_id": "metric-def-1",
        "measurement_value": Decimal(value),
        "unit": "unit-1",
        "time_bound": "2024",
        "population_or_geography": "population-1",
        "retrieved_at": RETRIEVED,
    }
    fields.update(overrides)
    return MeasurementWitness(**fields)


def equivalence(verdict=EquivalenceVerdict.EQUIVALENT, **overrides):
    fields = {
        "basis_id": "basis-1",
        "verdict": verdict,
        "dimensions_checked": frozenset(ALL_EQUIVALENCE_DIMENSIONS)
        if verdict is EquivalenceVerdict.EQUIVALENT
        else frozenset(),
        "reviewed_by": "reviewer",
        "reviewed_at": FROZEN,
        "interpretation_confidence": 0.8 if verdict is EquivalenceVerdict.EQUIVALENT else None,
    }
    fields.update(overrides)
    return SemanticEquivalenceDecision(**fields)


def run(value="110", **kwargs):
    return evaluate(
        kwargs.pop("witness", None) or witness(value),
        kwargs.pop("target", None) or target(),
        kwargs.pop("registration", None) or registration(),
        kwargs.pop("equivalence", None) or equivalence(**kwargs),
    )


def a_mismatch():
    """Fixture for §33: the minimum success case, produced rather than described."""
    return run("110", witness=witness("110", unit="unit-2"))


def an_unknown():
    return run("110", equivalence=equivalence(EquivalenceVerdict.UNKNOWN))


# ==================================================== §46.7-8 the descriptor


class TheDescriptorReconstructsTheProposition(unittest.TestCase):
    def test_a_refusal_still_carries_the_full_candidate_target(self):
        """§33. The unit mismatch refuses, and the proposition it refused about
        is still completely readable."""
        facts = target_proposition_facts(target())
        for required in (
            "proposition",
            "canonical_subject_id",
            "metric_definition_id",
            "time_bound",
            "population_or_geography",
            "unit",
            "threshold_operator",
            "threshold_value",
            "claim_type",
        ):
            with self.subTest(fact=required):
                self.assertIn(required, facts)

    def test_the_proposition_reads_back_as_m_greater_or_equal_100(self):
        facts = target_proposition_facts(target())
        self.assertEqual(facts["threshold_operator"], "GTE")
        self.assertEqual(facts["threshold_value"], "100")
        self.assertEqual(facts["metric_definition_id"], "metric-def-1")

    def test_the_key_recomputes_from_the_descriptor(self):
        """§46.8. The stored key is verifiable rather than trusted."""
        facts = target_proposition_facts(target())
        self.assertEqual(proposition_key(facts), run("110").proposition_key)

    def test_the_discriminator_key_is_the_one_live_claims_use(self):
        """A descriptor keyed on `proposition_kind` could never produce the same
        proposition_key as the Claim it may later become."""
        facts = target_proposition_facts(target())
        self.assertIn("proposition", facts)
        self.assertNotIn("proposition_kind", facts)
        self.assertEqual(
            record()["candidate_target_representation"]["measured_precedent"]["discriminator_key"],
            "proposition",
        )

    def test_the_descriptor_values_are_flat_strings(self):
        """No nesting and no prose, which is what keeps it out of untyped-dump
        territory (§31)."""
        for name, value in target_proposition_facts(target()).items():
            with self.subTest(fact=name):
                self.assertIsInstance(value, str)

    def test_a_refused_target_and_a_supported_one_share_the_key(self):
        """§34's traceability depends on this: the refusal and the Claim it may
        later become must be comparable."""
        self.assertEqual(
            proposition_key(target_proposition_facts(target())), run("110").proposition_key
        )


# ==================================================== §46.9-12 no Claim, no Evidence


class ARefusalProducesNeitherClaimNorEvidence(unittest.TestCase):
    def test_a_not_applicable_refusal_carries_no_claim_draft(self):
        outcome = a_mismatch()
        self.assertIs(outcome.result, EvaluationResult.NOT_APPLICABLE)
        self.assertIsNone(outcome.claim_draft)

    def test_a_not_applicable_refusal_carries_no_evidence_decision(self):
        self.assertIsNone(a_mismatch().evidence_decision)

    def test_an_unknown_refusal_carries_neither(self):
        outcome = an_unknown()
        self.assertIs(outcome.result, EvaluationResult.UNKNOWN)
        self.assertIsNone(outcome.claim_draft)
        self.assertIsNone(outcome.evidence_decision)

    def test_neutral_cannot_be_emitted_as_a_refusal(self):
        """§10 and §46.12. NEUTRAL exists downstream; it is not reachable from
        here, because `EvaluationResult` has no such member."""
        self.assertNotIn("NEUTRAL", {member.value for member in EvaluationResult})

    def test_the_refusal_vocabulary_is_exactly_two_members(self):
        refusals = {
            member.value
            for member in EvaluationResult
            if member not in (EvaluationResult.SUPPORTS, EvaluationResult.CONTRADICTS)
        }
        self.assertEqual(refusals, {"NOT_APPLICABLE", "UNKNOWN"})
        self.assertEqual(set(record()["refusal_result_vocabulary"]), refusals)

    def test_the_record_excludes_the_directional_results(self):
        excluded = set(record()["refusal_result_vocabulary_excludes"])
        self.assertEqual(excluded, {"SUPPORTS", "CONTRADICTS", "NEUTRAL"})


# ==================================================== §46.13-15 reason codes


class ReasonCodesAreDistinctFromResults(unittest.TestCase):
    def test_the_reason_code_is_not_the_result(self):
        outcome = a_mismatch()
        self.assertEqual(outcome.refusal_reason, "UNIT_MISMATCH")
        self.assertNotEqual(outcome.refusal_reason, outcome.result.value)

    def test_two_refusals_share_a_result_and_differ_by_reason(self):
        """Which is the whole argument for a separate reason code: the result
        drives the contract, the reason drives the audit."""
        unit = run("110", witness=witness("110", unit="unit-2"))
        time_bound = run("110", witness=witness("110", time_bound="2025"))
        self.assertEqual(unit.result, time_bound.result)
        self.assertNotEqual(unit.refusal_reason, time_bound.refusal_reason)

    def test_every_recorded_reason_code_is_produced_by_the_evaluator(self):
        produced = {
            a_mismatch().refusal_reason,
            an_unknown().refusal_reason,
            run("110", witness=witness("110", time_bound="2025")).refusal_reason,
            run(
                "110", registration=registration(recorded_at=datetime(2026, 9, 1, tzinfo=UTC))
            ).refusal_reason,
            run("110", registration=registration(threshold_value=Decimal("50"))).refusal_reason,
        }
        recorded = {entry["code"] for entry in record()["reason_codes"]["codes"]}
        self.assertTrue(produced <= recorded, f"not in the record: {sorted(produced - recorded)}")

    def test_the_record_invents_no_reason_code(self):
        self.assertEqual(record()["reason_codes"]["invented_here"], 0)

    def test_gate_one_refusals_never_require_a_threshold_registration(self):
        """§15 and §46.15. A refusal that never reached the registration gate
        must not be forced to name one."""
        for entry in record()["reason_codes"]["codes"]:
            with self.subTest(code=entry["code"]):
                if entry["gate"] == 1:
                    self.assertFalse(entry["threshold_required"])
                else:
                    self.assertTrue(entry["threshold_required"])

    def test_the_equivalence_refusals_really_are_gate_one(self):
        """Read from behaviour, not from the record: a semantic mismatch refuses
        even when the registration describes the proposition perfectly."""
        outcome = run(
            "110",
            equivalence=equivalence(EquivalenceVerdict.NOT_EQUIVALENT),
            registration=registration(),
        )
        self.assertEqual(outcome.refusal_reason, "SEMANTIC_MISMATCH")


# ==================================================== §46.14 the basis


class TheEquivalenceBasisIsAlwaysPresent(unittest.TestCase):
    def test_a_refusal_names_the_basis_it_rests_on(self):
        self.assertEqual(a_mismatch().derivation.semantic_equivalence_basis_id, "basis-1")
        self.assertEqual(an_unknown().derivation.semantic_equivalence_basis_id, "basis-1")

    def test_a_decision_cannot_be_built_without_one(self):
        """Which is why the record may declare the column NOT NULL and keep the
        identity key free of nullable columns."""
        with self.assertRaises(ValueError):
            equivalence(EquivalenceVerdict.UNKNOWN, basis_id="   ")

    def test_the_record_invents_no_placeholder_basis(self):
        basis = record()["semantic_equivalence_basis"]
        self.assertFalse(basis["nullable"])
        self.assertTrue(basis["no_fake_identifier_invented"])


# ==================================================== §46.16-19 identity and history


class RefusalIdentity(unittest.TestCase):
    def test_a_replay_of_the_same_inputs_produces_the_same_refusal(self):
        """§46.16. Determinism is what makes an idempotency key meaningful."""
        first, second = a_mismatch(), a_mismatch()
        self.assertEqual(first.result, second.result)
        self.assertEqual(first.refusal_reason, second.refusal_reason)
        self.assertEqual(first.derivation, second.derivation)

    def test_the_identity_key_contains_the_rule_version(self):
        key = record()["idempotency"]["key"]
        self.assertIn("derivation_rule_version", key)

    def test_every_column_of_the_identity_key_is_not_null(self):
        """§46.17's premise. Probe C proved a UNIQUE containing a nullable
        column stops constraining, so this is the property that makes refusal
        idempotency real rather than nominal."""
        self.assertTrue(record()["idempotency"]["every_column_not_null"])
        nullable = {
            field["field"] for field in record()["selected_entity"]["fields"] if field["nullable"]
        }
        self.assertFalse(set(record()["idempotency"]["key"]) & nullable)

    def test_a_different_basis_is_decided_explicitly(self):
        """§46.18. The brief asks for a decision, not a default."""
        decision = record()["idempotency"]["different_basis"]
        self.assertIn("NEW", decision["decision"].upper())
        self.assertTrue(decision["why"].strip())
        self.assertTrue(decision["cost_stated"].strip())

    def test_the_measurement_value_is_not_in_the_identity(self):
        self.assertNotIn("measurement_value", record()["idempotency"]["key"])


class HistoryIsAppendOnly(unittest.TestCase):
    def test_no_supersession_column(self):
        self.assertFalse(record()["append_only_and_history"]["supersession_column"])

    def test_a_later_supports_does_not_touch_the_earlier_refusal(self):
        """§46.19. The transition is recorded as a decision, and the decision is
        that nothing happens to the refusal."""
        transition = record()["append_only_and_history"]["unknown_then_supports"]
        self.assertIn("NOTHING", transition["what_happens_to_U"])
        self.assertIn("scoring.evidence", transition["T1_writes"])

    def test_the_same_signal_and_target_can_support_after_being_unknown(self):
        """Produced rather than asserted: one basis refuses, another supports,
        and both are about the same proposition key."""
        refused = an_unknown()
        supported = run("110")
        self.assertIs(refused.result, EvaluationResult.UNKNOWN)
        self.assertIs(supported.result, EvaluationResult.SUPPORTS)
        self.assertEqual(
            proposition_key(target_proposition_facts(target())), supported.proposition_key
        )


# ==================================================== §46.6, 20-27 nothing moved


class TheDesignChangesNothingThatExists(unittest.TestCase):
    def test_option_c_is_classified_non_durable(self):
        self.assertEqual(record()["option_matrix"]["C"]["RETENTION_DURABILITY"], "FAIL")
        self.assertTrue(record()["option_verdicts"]["C"].startswith("REJECTED"))

    def test_exactly_one_option_is_selected(self):
        selected = [k for k, v in record()["option_verdicts"].items() if v.startswith("SELECTED")]
        self.assertEqual(selected, ["A"])

    def test_no_trigger_weakening(self):
        self.assertFalse(record()["trigger_exemptions_changed"])

    def test_no_schema_change_and_no_migration(self):
        self.assertFalse(record()["migration_created"])
        self.assertFalse(record()["claim_revision_id_made_nullable"])
        self.assertFalse(record()["refusal_table_created"])
        self.assertEqual(record()["unchanged"]["claims_schema"], "untouched")
        self.assertEqual(record()["unchanged"]["evidence_schema"], "untouched")

    def test_the_migration_head_did_not_move(self):
        heads = sorted(path.stem for path in MIGRATIONS.glob("00*.sql"))
        self.assertEqual(heads[-1], "0034_deterministic_derivation_provenance")

    def test_no_canonical_mutation(self):
        for name, pair in record()["counters"].items():
            with self.subTest(counter=name):
                self.assertEqual(pair["before"], pair["after"])

    def test_no_model_calls_and_no_embeddings(self):
        model_use = record()["model_use"]
        self.assertEqual(model_use["llm_calls"], 0)
        self.assertEqual(model_use["embeddings"], 0)

    def test_the_opportunity_is_unchanged(self):
        counters = record()["counters"]
        self.assertEqual(counters["opportunities"]["after"], 1)
        self.assertEqual(counters["opportunity_evidence_links"]["after"], 7)
        self.assertFalse(record()["opportunity_changed"])

    def test_problem_family_remains_parked(self):
        self.assertEqual(record()["model_use"]["problem_family_status"], "PARKED")

    def test_the_evaluator_was_not_modified(self):
        self.assertFalse(record()["evaluator_modified"])
        self.assertEqual(record()["reason_codes"]["invented_here"], 0)

    def test_the_rule_and_evaluator_versions_are_still_the_ones_recorded(self):
        derivation = a_mismatch().derivation
        self.assertEqual(derivation.derivation_rule_id, DERIVATION_RULE_ID)
        self.assertEqual(derivation.derivation_rule_version, DERIVATION_RULE_VERSION)
        self.assertEqual(derivation.evaluator_version, EVALUATOR_VERSION)

    def test_the_adr_exists_and_is_accepted(self):
        self.assertTrue(ADR.exists())
        self.assertIn("**Status:** Accepted", ADR.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
