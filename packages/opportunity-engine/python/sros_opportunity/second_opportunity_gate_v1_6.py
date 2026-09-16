"""The second-Opportunity output gate v1.6.0: gate v1.5.0's verdict, over schema v1.3.0, with the class grounded.

Mission 1.84.27, operator decision D3. Schema v1.3.0 gives `candidate_intervention_class` a first-class
absence and says what an established class is made of. Gate v1.5.0 cannot hold an answer to that: it
reads the class only through its fixed lists, and it validates structure against schema v1.2.0.

**Gate v1.5.0 is not touched**, nor anything it is built from. This module composes the successor beside
it, as gate v1.4.0 composed itself beside v1.3.0:

* gate v1.5.0 is called exactly once, and every reason it gives is kept, in its order;
* its schema v1.2.0 structural reasons are recomputed and compared entry by entry, then replaced by
  schema v1.3.0's. The two schemas differ in one description, which no validator reads, so the reasons
  are the same findings under the successor's name; if gate v1.5.0 ever stops writing them first, this
  gate refuses to run rather than strip what it cannot account for;
* the reasons of `intervention_class_grounding` are appended, one per finding, under this field's name.

Nothing else moves: the assertion scope, the audit, the field policy, the forbidden concepts, the
markers, the trusted context, the source metadata and MARKET_ACTIVITY's licence in the other fields
are gate v1.5.0's, by identity.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .assertion_context import TrustedContext
from .dimensions import EvidenceDimension
from .intervention_class_grounding import (
    INTERVENTION_CLASS_GROUNDING_VERSION,
    class_grounding_findings,
)
from .packet import OpportunityEvidencePacket
from .schema_validation import schema_violations
from .second_opportunity_gate_v1_5 import (
    COMPONENT_VERSIONS_V1_5,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_5,
    evaluate_second_opportunity_output_v1_5,
)
from .second_opportunity_schema_v1_2 import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
)
from .second_opportunity_schema_v1_3 import (
    INTERVENTION_CLASS_FIELD,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_3,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_3,
)
from .support_origin import SourceMetadataContext, build_typed_support_universe
from .synthesis import MANDATORY_UNSUPPORTED_REPORT
from .validation import PersistenceDecision

__all__ = [
    "SECOND_OPPORTUNITY_GATE_VERSION_V1_6",
    "PREDECESSOR_GATE_VERSION",
    "OPERATOR_DECISION_V1_6",
    "COMPONENT_VERSIONS_V1_6",
    "CHANGED_COMPONENTS",
    "STRUCTURAL_REASON_PREFIX",
    "PREDECESSOR_STRUCTURAL_REASON_PREFIX",
    "CLASS_GROUNDING_REASON_PREFIX",
    "PredecessorShapeError",
    "evaluate_second_opportunity_output_v1_6",
]

SECOND_OPPORTUNITY_GATE_VERSION_V1_6 = "second-opportunity-output-gate@1.6.0"
PREDECESSOR_GATE_VERSION = SECOND_OPPORTUNITY_GATE_VERSION_V1_5

#: Mission 1.84.27, the operator's decision D3 and its limits. Carried as data.
OPERATOR_DECISION_V1_6: tuple[str, ...] = (
    "D3_RESOLVE_CANDIDATE_INTERVENTION_CLASS_AT_THE_CONTRACT_LEVEL = true",
    "THE_MODEL_IS_NEVER_FORCED_TO_INVENT_AN_INTERVENTION_CLASS",
    "ABSENCE_OF_AN_INTERVENTION_CLASS_HAS_ONE_DETERMINISTIC_REPRESENTATION",
    "A_SUPPORTED_CLASS_REMAINS_EVIDENCE_BOUND",
    "GENERAL_WORLD_KNOWLEDGE_IS_NEVER_SUPPORT",
    "MARKET_ACTIVITY_DOES_NOT_LICENCE_MARKET_OR_ARBITRARY_PARAPHRASES",
    "NO_BROAD_VOCABULARY_WHITELIST",
    "KEEP_SCHEMA_V1_2_0_PROMPT_V1_6_0_GATES_V1_4_0_AND_V1_5_0_IMMUTABLE",
    "D4_NOT_AUTHORISED",
)

#: Every versioned component of v1.6.0: v1.5.0's, with the gate, the schema and the class grounding moved.
COMPONENT_VERSIONS_V1_6: dict[str, str] = {
    **COMPONENT_VERSIONS_V1_5,
    "gate": SECOND_OPPORTUNITY_GATE_VERSION_V1_6,
    "output_schema": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_3,
    "intervention_class_grounding": INTERVENTION_CLASS_GROUNDING_VERSION,
}
CHANGED_COMPONENTS: tuple[str, ...] = ("gate", "output_schema", "intervention_class_grounding")

STRUCTURAL_REASON_PREFIX = f"{SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_3}: "
PREDECESSOR_STRUCTURAL_REASON_PREFIX = f"{SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2}: "
CLASS_GROUNDING_REASON_PREFIX = (
    f"{INTERVENTION_CLASS_FIELD} refused under {INTERVENTION_CLASS_GROUNDING_VERSION}: "
)


class PredecessorShapeError(RuntimeError):
    """Gate v1.5.0 no longer writes its structural reasons first, so they cannot be replaced safely."""


def evaluate_second_opportunity_output_v1_6(
    output: Mapping[str, object],
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
    *,
    trusted_context: TrustedContext,
    source_metadata: SourceMetadataContext,
    mandatory_unsupported: Sequence[EvidenceDimension] = MANDATORY_UNSUPPORTED_REPORT,
) -> PersistenceDecision:
    """The v1.6.0 gate: gate v1.5.0's verdict, structure read against schema v1.3.0, and the class of
    intervention held to its grounding. Both channels stay required, with no default."""
    predecessor = evaluate_second_opportunity_output_v1_5(
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
        for v in schema_violations(dict(output), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
    )
    if predecessor.refusal_reasons[: len(replaced)] != replaced:
        raise PredecessorShapeError(
            f"{SECOND_OPPORTUNITY_GATE_VERSION_V1_5} did not write its {len(replaced)} structural "
            "reasons first; gate v1.6.0 will not remove reasons it cannot account for"
        )
    semantic = predecessor.refusal_reasons[len(replaced) :]
    structural = tuple(
        f"{STRUCTURAL_REASON_PREFIX}{v}"
        for v in schema_violations(dict(output), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_3)
    )
    universe = build_typed_support_universe(
        packet, claim_statements, trusted_context, source_metadata
    )
    grounding = tuple(
        f"{CLASS_GROUNDING_REASON_PREFIX}{finding}"
        for finding in class_grounding_findings(output, universe, list(packet.claim_ids))
    )
    decision_value = str(output.get("decision") or "")
    if decision_value == "INSUFFICIENT_EVIDENCE":
        grounding = ()
    reasons = (*structural, *semantic, *grounding)
    return PersistenceDecision(
        persist=not reasons,
        gate_version=SECOND_OPPORTUNITY_GATE_VERSION_V1_6,
        refusal_reasons=reasons,
        audit=predecessor.audit,
        notes=predecessor.notes,
    )
