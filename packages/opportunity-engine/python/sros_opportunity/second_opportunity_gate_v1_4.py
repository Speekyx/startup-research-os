"""The second-Opportunity output gate v1.4.0: gate v1.3.0's semantics, with structure read against v1.2.0.

Mission 1.84.17. Gate v1.3.0 validates an answer's structure against output schema v1.1.0 inside its
own evaluator, so the summary bound the operator moved in Mission 1.84.16 was still enforced at stage
6 whatever stage 5 admitted. The operator decided, verbatim as data in `OPERATOR_DECISION_V1_4`, to
create a successor bound to schema v1.2.0 and to keep every other behaviour exactly as it is.

**Gate v1.3.0 is not touched.** None of the four files its frozen digest covers is edited. This module
composes the successor beside it, and it changes one thing:

* the structural check reads schema v1.2.0 instead of schema v1.1.0, through the same validator;
* everything else is gate v1.3.0 itself, called, not copied: the persistence gate over its audit,
  the field policy, the forbidden concepts, trusted context, source metadata, the inflection policy,
  the disjunction rule and v1.0.0's checks on the three fields that version added.

So the semantic half of a v1.4.0 verdict IS the semantic half of the v1.3.0 verdict on the same
arguments, by construction rather than by a copy that could drift. What is replaced is exactly the
block of structural reasons gate v1.3.0 writes first. That block is recomputed and compared entry by
entry before it is removed; if gate v1.3.0 ever stops writing it first, this gate refuses to run
rather than strip something it cannot account for.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .assertion_context import TrustedContext
from .dimensions import EvidenceDimension
from .packet import OpportunityEvidencePacket
from .schema_validation import schema_violations
from .second_opportunity import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
)
from .second_opportunity_gate_v1_3 import (
    COMPONENT_VERSIONS_V1_3,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
    evaluate_second_opportunity_output_v1_3,
)
from .second_opportunity_schema_v1_2 import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
)
from .support_origin import SourceMetadataContext
from .synthesis import MANDATORY_UNSUPPORTED_REPORT
from .validation import PersistenceDecision

__all__ = [
    "SECOND_OPPORTUNITY_GATE_VERSION_V1_4",
    "PREDECESSOR_GATE_VERSION",
    "OPERATOR_DECISION_V1_4",
    "COMPONENT_VERSIONS_V1_4",
    "STRUCTURAL_REASON_PREFIX",
    "PREDECESSOR_STRUCTURAL_REASON_PREFIX",
    "PredecessorShapeError",
    "evaluate_second_opportunity_output_v1_4",
]

SECOND_OPPORTUNITY_GATE_VERSION_V1_4 = "second-opportunity-output-gate@1.4.0"
PREDECESSOR_GATE_VERSION = SECOND_OPPORTUNITY_GATE_VERSION_V1_3

#: Mission 1.84.17 section 0, as the operator decided it. Carried as data so a record can be checked.
OPERATOR_DECISION_V1_4: tuple[str, ...] = (
    "CREATE_SEMANTIC_GATE_SUCCESSOR_BOUND_TO_OUTPUT_SCHEMA_V1_2_0 = true",
    "KEEP_SEMANTIC_GATE_V1_3_0_IMMUTABLE",
    "KEEP_ALL_NON_STRUCTURAL_SEMANTIC_BEHAVIOR_UNCHANGED",
    "USE_OUTPUT_SCHEMA_V1_2_0_AS_THE_V6_EXECUTION_CONTRACT",
    "DO_NOT_REVERT_TO_OUTPUT_SCHEMA_V1_1_0",
)

#: Every versioned component of v1.4.0: v1.3.0's, with the gate and the output schema moved.
COMPONENT_VERSIONS_V1_4: dict[str, str] = {
    **COMPONENT_VERSIONS_V1_3,
    "gate": SECOND_OPPORTUNITY_GATE_VERSION_V1_4,
    "output_schema": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
}

STRUCTURAL_REASON_PREFIX = f"{SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2}: "
PREDECESSOR_STRUCTURAL_REASON_PREFIX = f"{SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1}: "


class PredecessorShapeError(RuntimeError):
    """Gate v1.3.0 no longer writes its structural reasons first, so they cannot be replaced safely."""


def evaluate_second_opportunity_output_v1_4(
    output: Mapping[str, object],
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
    *,
    trusted_context: TrustedContext,
    source_metadata: SourceMetadataContext,
    mandatory_unsupported: Sequence[EvidenceDimension] = MANDATORY_UNSUPPORTED_REPORT,
) -> PersistenceDecision:
    """The v1.4.0 gate: gate v1.3.0's verdict, with its schema v1.1.0 structural reasons replaced by
    schema v1.2.0's. Both channels stay required, with no default, exactly as in v1.3.0.

    Structure first, through the same validator against schema v1.2.0; then every reason gate v1.3.0
    gives that is not one of its own structural reasons, in the order it gives them.
    """
    predecessor = evaluate_second_opportunity_output_v1_3(
        output,
        packet,
        claim_statements,
        evidence_to_claim,
        trusted_context=trusted_context,
        source_metadata=source_metadata,
        mandatory_unsupported=mandatory_unsupported,
    )
    replaced = tuple(
        f"{PREDECESSOR_STRUCTURAL_REASON_PREFIX}{v}"
        for v in schema_violations(dict(output), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    )
    if predecessor.refusal_reasons[: len(replaced)] != replaced:
        raise PredecessorShapeError(
            f"{SECOND_OPPORTUNITY_GATE_VERSION_V1_3} did not write its {len(replaced)} structural "
            "reasons first; gate v1.4.0 will not remove reasons it cannot account for"
        )
    semantic = predecessor.refusal_reasons[len(replaced) :]
    structural = tuple(
        f"{STRUCTURAL_REASON_PREFIX}{v}"
        for v in schema_violations(dict(output), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
    )
    reasons = (*structural, *semantic)
    return PersistenceDecision(
        persist=not reasons,
        gate_version=SECOND_OPPORTUNITY_GATE_VERSION_V1_4,
        refusal_reasons=reasons,
        audit=predecessor.audit,
        notes=predecessor.notes,
    )
