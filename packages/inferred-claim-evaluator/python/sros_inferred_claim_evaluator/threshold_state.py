"""`threshold-state-evaluator@1.0.0` — the one deterministic rule V1 implements.

    equivalence gate  ->  registration match  ->  provenance check  ->  predicate

Every gate refuses before the next one runs, and the order is the point: the
predicate never sees a measurement whose bearing on the proposition has not been
established. `110 >= 100` is only meaningful once somebody has said that the 110
measures what the proposition is about.

**No clock, no randomness, no model, no network.** `evaluate()` reads nothing
outside its arguments, so the same inputs give the same result forever. The only
non-deterministic values in a persisted row -- ids and timestamps -- are produced
by the caller at write time, outside this function.
"""

from __future__ import annotations

from decimal import Decimal

from sros_claim_model import proposition_key

from .contracts import (
    ALL_EQUIVALENCE_DIMENSIONS,
    DerivationDraft,
    EquivalenceVerdict,
    EvaluationOutcome,
    EvaluationResult,
    EvidenceDecision,
    InferredClaimDraft,
    MeasurementWitness,
    SemanticEquivalenceDecision,
    TargetProposition,
    ThresholdOperator,
    ThresholdProvenanceStatus,
    ThresholdRegistration,
)

__all__ = [
    "DERIVATION_RULE_ID",
    "DERIVATION_RULE_VERSION",
    "EVALUATOR_VERSION",
    "PROPOSITION_KIND",
    "evaluate",
    "target_proposition_facts",
]

# The SEMANTIC rule. It changes only when what the rule MEANS changes.
DERIVATION_RULE_ID = "threshold-state-evaluator"
DERIVATION_RULE_VERSION = "1.0.0"

# The SOFTWARE producing the result. A refactor that preserves the semantics
# bumps this and leaves the rule version alone (ADR-037 §27). They are two facts
# and collapsing them would make a rewrite look like a change of meaning.
EVALUATOR_VERSION = "1.0.0"

PROPOSITION_KIND = "metric_threshold_state"

_INTERPRETATION_KIND = "DETERMINISTIC"

_COMPARISONS = {
    ThresholdOperator.GTE: lambda value, bound: value >= bound,
    ThresholdOperator.GT: lambda value, bound: value > bound,
    ThresholdOperator.LTE: lambda value, bound: value <= bound,
    ThresholdOperator.LT: lambda value, bound: value < bound,
}

_OPERATOR_PROSE = {
    ThresholdOperator.GTE: ">=",
    ThresholdOperator.GT: ">",
    ThresholdOperator.LTE: "<=",
    ThresholdOperator.LT: "<",
}


def target_proposition_facts(target: TargetProposition) -> dict[str, str]:
    """The identity facts of a source-independent threshold proposition.

    Absent by design, and each absence does work: `source_id`, so two publishers
    reach one Claim; `measurement_value`, so 110 and 105 do not fork it;
    `direction`, so a supporting and a contradicting witness share it; and the
    threshold's PROVENANCE, because a preregistered and a post-hoc bound assert
    the same thing about the world.
    """
    return {
        "proposition": target.proposition_kind,
        "claim_type": "INFERRED",
        "canonical_subject_id": target.canonical_subject_id,
        "metric_definition_id": target.metric_definition_id,
        "time_bound": target.time_bound,
        "population_or_geography": target.population_or_geography,
        "unit": target.unit,
        "threshold_operator": target.threshold_operator.value,
        "threshold_value": _canonical(target.threshold_value),
    }


def _canonical(value: Decimal) -> str:
    """A stable decimal rendering, so `100` and `100.0` are one bound.

    Without this the same threshold written two ways would produce two
    proposition keys, which is the measurement-value defect one field along.
    """
    normalized = value.normalize()
    # `normalize()` renders integral values in exponent form (1E+2); expanding
    # it keeps the text a person recognises.
    if normalized == normalized.to_integral_value():
        normalized = normalized.quantize(Decimal(1))
    return format(normalized, "f")


def _refuse(
    result: EvaluationResult,
    reason: str,
    rationale: str,
    witness: MeasurementWitness,
    equivalence: SemanticEquivalenceDecision,
    registration: ThresholdRegistration | None,
) -> EvaluationOutcome:
    """A refusal still produces a derivation draft.

    ADR-021 and ADR-025 set the shape: a refused derivation gets a record and
    never a Signal, a refused interpretation gets a run row and never a Claim.
    A refusal that leaves no trace is invisible, and invisible refusals are how
    a corpus comes to look more complete than it is.
    """
    return EvaluationOutcome(
        result=result,
        rationale=rationale,
        refusal_reason=reason,
        derivation=DerivationDraft(
            workspace_id=witness.workspace_id,
            input_signal_id=witness.signal_id,
            input_observed_claim_id=witness.observed_claim_id,
            derivation_rule_id=DERIVATION_RULE_ID,
            derivation_rule_version=DERIVATION_RULE_VERSION,
            evaluator_version=EVALUATOR_VERSION,
            measurement_value=witness.measurement_value,
            threshold_registration_id=(
                registration.registration_id if registration is not None else None
            ),
            evaluation_result=result,
            semantic_equivalence_basis_id=equivalence.basis_id,
            interpretation_kind=_INTERPRETATION_KIND,
            model_version=None,
            rationale=rationale,
        ),
    )


def evaluate(
    witness: MeasurementWitness,
    target: TargetProposition,
    registration: ThresholdRegistration,
    equivalence: SemanticEquivalenceDecision,
) -> EvaluationOutcome:
    """Evaluate one measurement against one source-independent proposition."""

    # ---------------------------------------------------------------- gate 1
    # Semantic equivalence, first and unconditionally. A measurement whose
    # bearing is not established never reaches the comparison, so the arithmetic
    # cannot lend its exactness to a correspondence nobody checked.
    if equivalence.verdict is EquivalenceVerdict.NOT_EQUIVALENT:
        return _refuse(
            EvaluationResult.NOT_APPLICABLE,
            "SEMANTIC_MISMATCH",
            (
                f"The reviewed basis {equivalence.basis_id} finds this measurement is not "
                f"a measurement of {target.metric_definition_id} under the target's "
                "population, unit and period. It bears on a different proposition."
            ),
            witness,
            equivalence,
            registration,
        )
    if equivalence.verdict is EquivalenceVerdict.UNKNOWN:
        return _refuse(
            EvaluationResult.UNKNOWN,
            "EQUIVALENCE_NOT_ESTABLISHED",
            (
                f"The reviewed basis {equivalence.basis_id} could neither establish nor "
                "refute that this measurement bears on the target proposition."
            ),
            witness,
            equivalence,
            registration,
        )
    if set(equivalence.dimensions_checked) != ALL_EQUIVALENCE_DIMENSIONS:  # pragma: no cover
        # Unreachable while the decision's own constructor enforces it. Kept as
        # the second of two checks on one rule, because this evaluator may one
        # day receive a decision built somewhere else.
        return _refuse(
            EvaluationResult.UNKNOWN,
            "EQUIVALENCE_DIMENSIONS_INCOMPLETE",
            "The equivalence decision did not check every frozen dimension.",
            witness,
            equivalence,
            registration,
        )

    # ---------------------------------------------------------------- gate 2
    # The registration must be the bound this proposition is about. No search,
    # no nearest match, no "whichever makes the Claim work" -- the caller names
    # one registration and it either matches or the evaluation refuses.
    mismatches = _registration_mismatches(target, registration)
    if mismatches:
        return _refuse(
            EvaluationResult.NOT_APPLICABLE,
            "THRESHOLD_REGISTRATION_MISMATCH",
            (
                f"Threshold registration {registration.registration_id} does not describe "
                f"this proposition: {', '.join(mismatches)} differ."
            ),
            witness,
            equivalence,
            registration,
        )

    # Units are checked rather than converted. V1 performs NO unit conversion,
    # so a measurement expressed in another unit bears on another proposition.
    if witness.unit != target.unit:
        return _refuse(
            EvaluationResult.NOT_APPLICABLE,
            "UNIT_MISMATCH",
            (
                f"The measurement is expressed in {witness.unit} and the proposition in "
                f"{target.unit}. This evaluator converts no units."
            ),
            witness,
            equivalence,
            registration,
        )
    if witness.time_bound != target.time_bound:
        return _refuse(
            EvaluationResult.NOT_APPLICABLE,
            "TIME_BOUND_MISMATCH",
            (
                f"The measurement covers {witness.time_bound} and the proposition "
                f"{target.time_bound}. This evaluator aligns no time windows."
            ),
            witness,
            equivalence,
            registration,
        )

    # ---------------------------------------------------------------- gate 3
    # Threshold provenance. A bound labelled PREREGISTERED must actually have
    # been frozen before this system held the measurement; a label that is not
    # true of the timestamps is an inconsistent record, not a weaker one, and it
    # is REFUSED rather than silently downgraded to POST_HOC.
    if registration.provenance_status is ThresholdProvenanceStatus.PREREGISTERED and not (
        registration.recorded_at < witness.retrieved_at
    ):
        return _refuse(
            EvaluationResult.UNKNOWN,
            "PREREGISTRATION_TIMING_INCONSISTENT",
            (
                f"Registration {registration.registration_id} is labelled PREREGISTERED "
                f"but was recorded at {registration.recorded_at.isoformat()}, which is not "
                f"before this system retrieved the measurement at "
                f"{witness.retrieved_at.isoformat()}."
            ),
            witness,
            equivalence,
            registration,
        )

    # ---------------------------------------------------------------- gate 4
    # The predicate. Exact Decimal comparison, and the provenance status is NOT
    # consulted here: a post-hoc bound is still logically satisfied or not.
    satisfied = _COMPARISONS[target.threshold_operator](
        witness.measurement_value, target.threshold_value
    )
    result = EvaluationResult.SUPPORTS if satisfied else EvaluationResult.CONTRADICTS

    operator = _OPERATOR_PROSE[target.threshold_operator]
    rationale = (
        f"Measurement {_canonical(witness.measurement_value)} {witness.unit} "
        f"{'satisfies' if satisfied else 'does not satisfy'} the bound "
        f"{operator} {_canonical(target.threshold_value)} registered as "
        f"{registration.provenance_status.value}, under equivalence basis "
        f"{equivalence.basis_id}."
    )

    facts = target_proposition_facts(target)
    key = proposition_key(facts)

    confidence = equivalence.interpretation_confidence
    if confidence is None:  # pragma: no cover
        # Unreachable while the decision's own constructor refuses EQUIVALENT
        # without a confidence, and gate 1 has already established EQUIVALENT.
        # This is a NARROWING rather than a second policy check: a type checker
        # cannot see across a constructor invariant, and the alternative is a
        # silent `type: ignore` that says nothing about why it is safe.
        raise ValueError(
            "an EQUIVALENT decision reached the evaluator with no interpretation_confidence"
        )

    return EvaluationOutcome(
        result=result,
        rationale=rationale,
        proposition_key=key,
        # Calibration eligibility is DERIVED and reported as a diagnostic. It
        # does not touch the result above, because provenance changes
        # eligibility and never entailment.
        calibration_eligible=registration.calibration_eligible,
        claim_draft=InferredClaimDraft(
            proposition_key=key,
            proposition_facts=facts,
            claim_type="INFERRED",
            interpretation_kind=_INTERPRETATION_KIND,
            model_version=None,
            # Taken from the reviewed equivalence decision, never from the
            # arithmetic. The comparison being exact says nothing about whether
            # the wording faithfully reads the Signal (ADR-037 §17).
            interpretation_confidence=confidence,
            # A minimal ORIGIN statement. The audit trail lives in the derivation
            # record, and `origin_detail` keeps its one responsibility.
            origin_detail=(
                f"Deterministically derived from Signal {witness.signal_id} under "
                f"{DERIVATION_RULE_ID}@{DERIVATION_RULE_VERSION}."
            ),
        ),
        evidence_decision=EvidenceDecision(
            signal_id=witness.signal_id,
            direction=result.value,
            source_id=witness.source_id,
        ),
        derivation=DerivationDraft(
            workspace_id=witness.workspace_id,
            input_signal_id=witness.signal_id,
            input_observed_claim_id=witness.observed_claim_id,
            derivation_rule_id=DERIVATION_RULE_ID,
            derivation_rule_version=DERIVATION_RULE_VERSION,
            evaluator_version=EVALUATOR_VERSION,
            measurement_value=witness.measurement_value,
            threshold_registration_id=registration.registration_id,
            evaluation_result=result,
            semantic_equivalence_basis_id=equivalence.basis_id,
            interpretation_kind=_INTERPRETATION_KIND,
            model_version=None,
            rationale=rationale,
        ),
    )


def _registration_mismatches(
    target: TargetProposition, registration: ThresholdRegistration
) -> list[str]:
    mismatches = []
    if registration.metric_definition_id != target.metric_definition_id:
        mismatches.append("metric definition")
    if registration.scope_subject_id != target.canonical_subject_id:
        mismatches.append("subject scope")
    if registration.scope_population != target.population_or_geography:
        mismatches.append("population scope")
    if registration.scope_time_bound != target.time_bound:
        mismatches.append("time scope")
    if registration.unit != target.unit:
        mismatches.append("unit")
    if registration.threshold_operator is not target.threshold_operator:
        mismatches.append("operator")
    if registration.threshold_value != target.threshold_value:
        mismatches.append("threshold value")
    return mismatches
