"""Deterministic INFERRED Claim evaluation — the foundation, not the pipeline.

ADR-036 decided that a proposition about the world rather than about a publisher
is an `INFERRED` Claim. ADR-037 specified the contract, and named this package as
its home for one reason worth repeating: `validate_claims.py` fails the build on
any non-OBSERVED `ClaimType` access inside the OBSERVED interpretation package,
and **a guard removed to let new work through is a guard that never was**. So the
evaluator lives here and that guard stays untouched.

    measurement witness
      + target proposition
      + threshold registration
      + reviewed semantic-equivalence decision
        -> SUPPORTS | CONTRADICTS | NOT_APPLICABLE | UNKNOWN
           + an INFERRED Claim draft and an Evidence direction, for the first two
           + a derivation draft, for all four

**Four things this package deliberately cannot do**, each enforced by what it
does not import rather than by a rule somebody must remember:

*It cannot acquire.* No `sros_acquisition`, so a component able to read the
source registry cannot decide its own authorization.

*It cannot call a model.* No Gateway, so `MODEL_CALLS = 0` is a property of the
dependency graph rather than a promise.

*It cannot aggregate.* No `sros_evidence_aggregation`. It emits an Evidence
direction; deciding what that direction is worth is somebody else's layer.

*It cannot score reliability or adjudicate independence.* Neither is an input and
neither is an output. A dependent republication still SUPPORTS the same
proposition; it simply remains one provenance group downstream.

**Nothing here writes to a database.** Every result is a value object, and the
persistence ordering it would need is a contract Mission 1.52 records rather than
implements -- because a refusal cannot currently be stored at all, which is that
mission's primary finding.
"""

from .contracts import (
    ALL_EQUIVALENCE_DIMENSIONS,
    CALIBRATION_ELIGIBLE_STATUSES,
    DerivationDraft,
    EquivalenceDimension,
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
from .threshold_state import (
    DERIVATION_RULE_ID,
    DERIVATION_RULE_VERSION,
    EVALUATOR_VERSION,
    PROPOSITION_KIND,
    evaluate,
    target_proposition_facts,
)

__all__ = [
    "ALL_EQUIVALENCE_DIMENSIONS",
    "CALIBRATION_ELIGIBLE_STATUSES",
    "DERIVATION_RULE_ID",
    "DERIVATION_RULE_VERSION",
    "EVALUATOR_VERSION",
    "PROPOSITION_KIND",
    "DerivationDraft",
    "EquivalenceDimension",
    "EquivalenceVerdict",
    "EvaluationOutcome",
    "EvaluationResult",
    "EvidenceDecision",
    "InferredClaimDraft",
    "MeasurementWitness",
    "SemanticEquivalenceDecision",
    "TargetProposition",
    "ThresholdOperator",
    "ThresholdProvenanceStatus",
    "ThresholdRegistration",
    "evaluate",
    "target_proposition_facts",
]
