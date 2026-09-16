"""The second-Opportunity output gate v1.5.0: gate v1.4.0's verdict, with the assertion scope repaired.

Mission 1.84.26. Mission 1.84.25 established that gate v1.4.0 reads two kinds of word as ASSERTED that
its own policy, *assertion, not token presence*, does not assert. The operator decided both, verbatim
as data in `OPERATOR_DECISION_V1_5`:

* D1, a noun list governed by one leading denial or uncertainty stays under that scope when its last
  item is followed by the sentence's predicate, and a genuinely coordinated proposition with its own
  subject still splits;
* D2, a gated modifier inside an explicitly denied subject noun phrase is not asserted, and an asserted
  continuation stays asserted.

**Gate v1.4.0 is not touched**, nor anything it is built from: `assertion_context.py`,
`assertion_audit_v1_3.py`, `second_opportunity_gate_v1_3.py` and `second_opportunity_gate_v1_4.py` are
byte-identical, so every historical verdict still resolves against the code that produced it. This
module composes the successor beside them:

* `assertion_scope_v1_5`, the successor reading of where a denial or an uncertainty reaches;
* `assertion_audit_v1_5`, the v1.3.0 audit re-bound to that reading and to nothing else;
* this evaluator, gate v1.3.0's own, with structure read against schema v1.2.0 exactly as gate v1.4.0
  reads it, so wherever the two readings agree, the reasons are gate v1.4.0's, in its order.

The output schema, the field policy, the forbidden concepts, the markers, the trusted context, the
source metadata, the inflection policy, MARKET_ACTIVITY's licence and the disjunction rule are the
objects gate v1.4.0 uses, imported by identity. Nothing here reads a prompt or an answer's history.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .assertion_audit_v1_5 import (
    ASSERTION_AUDIT_VERSION_V1_5,
    ASSERTION_GUARD_VERSION_V1_5,
    PERSISTENCE_GATE_VERSION_V1_4,
    evaluate_persistence_v1_4,
)
from .assertion_context import TrustedContext
from .assertion_scope_v1_5 import ASSERTION_SCOPE_POLICY_VERSION
from .dimensions import EvidenceDimension
from .packet import OpportunityEvidencePacket
from .schema_validation import schema_violations
from .second_opportunity import CONFIDENCE_CLASSIFICATIONS, PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS
from .second_opportunity_gate_v1_2 import (
    CLASSIFICATION_DISPOSITIONS,
    FORBIDDEN_CONCEPTS_V1_2,
    SECOND_OPPORTUNITY_FIELD_POLICY,
)
from .second_opportunity_gate_v1_4 import (
    COMPONENT_VERSIONS_V1_4,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_4,
)
from .second_opportunity_schema_v1_2 import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
)
from .support_origin import SourceMetadataContext, build_typed_support_universe
from .synthesis import MANDATORY_UNSUPPORTED_REPORT
from .validation import PersistenceDecision

__all__ = [
    "SECOND_OPPORTUNITY_GATE_VERSION_V1_5",
    "PREDECESSOR_GATE_VERSION",
    "OPERATOR_DECISION_V1_5",
    "COMPONENT_VERSIONS_V1_5",
    "CHANGED_COMPONENTS",
    "evaluate_second_opportunity_output_v1_5",
]

SECOND_OPPORTUNITY_GATE_VERSION_V1_5 = "second-opportunity-output-gate@1.5.0"
PREDECESSOR_GATE_VERSION = SECOND_OPPORTUNITY_GATE_VERSION_V1_4

#: Mission 1.84.26, the operator's decisions D1 and D2 and their limits. Carried as data.
OPERATOR_DECISION_V1_5: tuple[str, ...] = (
    "D1_AUTHORISE_A_SUCCESSOR_GATE_FOR_THE_SCOPED_LIST_DEFECT = true",
    "A_NOUN_LIST_GOVERNED_BY_ONE_LEADING_DENIAL_OR_UNCERTAINTY_REMAINS_UNDER_THAT_SCOPE",
    "A_GENUINELY_COORDINATED_PROPOSITION_WITH_ITS_OWN_SUBJECT_STILL_SPLITS",
    "D2_A_GATED_MODIFIER_INSIDE_AN_EXPLICITLY_DENIED_SUBJECT_NOUN_PHRASE_IS_NOT_ASSERTED = true",
    "D2_IS_A_BOUNDED_RULE_OVER_THE_DENIED_SUBJECT_NOUN_PHRASE_NOT_A_LATER_NOT",
    "AN_ASSERTED_CONTINUATION_REMAINS_ASSERTED",
    "KEEP_SEMANTIC_GATE_V1_4_0_AND_EVERYTHING_IT_USES_BYTE_IDENTICAL",
    "WHITELIST_NO_V10_SENTENCE",
    "BROADEN_NO_EVIDENCE_DIMENSION_AND_NO_MARKET_ACTIVITY_LICENCE",
    "REMOVE_OR_WEAKEN_NO_FORBIDDEN_CONCEPT",
    "D3_D4_D5_NOT_IMPLEMENTED",
)

#: Every versioned component of v1.5.0: v1.4.0's, with the reading of assertion scope moved.
COMPONENT_VERSIONS_V1_5: dict[str, str] = {
    **COMPONENT_VERSIONS_V1_4,
    "gate": SECOND_OPPORTUNITY_GATE_VERSION_V1_5,
    "persistence_gate": PERSISTENCE_GATE_VERSION_V1_4,
    "audit": ASSERTION_AUDIT_VERSION_V1_5,
    "claim_guard": ASSERTION_GUARD_VERSION_V1_5,
    "assertion_scope": ASSERTION_SCOPE_POLICY_VERSION,
}
CHANGED_COMPONENTS: tuple[str, ...] = (
    "gate",
    "persistence_gate",
    "audit",
    "claim_guard",
    "assertion_scope",
)


def evaluate_second_opportunity_output_v1_5(
    output: Mapping[str, object],
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
    *,
    trusted_context: TrustedContext,
    source_metadata: SourceMetadataContext,
    mandatory_unsupported: Sequence[EvidenceDimension] = MANDATORY_UNSUPPORTED_REPORT,
) -> PersistenceDecision:
    """The v1.5.0 gate: gate v1.3.0's evaluator, structure read against schema v1.2.0 as gate
    v1.4.0 reads it, over the v1.5.0 audit. Both channels stay required, with no default.

    Structure first, through the same validator against schema v1.2.0; then the persistence gate
    v1.4.0 over the v1.5.0 audit; then v1.0.0's checks on the three fields that version added.
    """
    structural = schema_violations(dict(output), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
    universe = build_typed_support_universe(
        packet, claim_statements, trusted_context, source_metadata
    )
    decision = evaluate_persistence_v1_4(
        output,
        universe,
        evidence_to_claim,
        mandatory_unsupported,
        policy=SECOND_OPPORTUNITY_FIELD_POLICY,
        concepts=FORBIDDEN_CONCEPTS_V1_2,
        markers=PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS,
        label_dispositions=CLASSIFICATION_DISPOSITIONS,
    )
    reasons = [
        *(f"{SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2}: {v}" for v in structural),
        *decision.refusal_reasons,
    ]
    if str(output.get("decision") or "") != "INSUFFICIENT_EVIDENCE":
        classification = str(output.get("confidence_classification") or "")
        if classification not in CONFIDENCE_CLASSIFICATIONS:
            reasons.append(
                f"confidence_classification is {classification!r}; the only permitted value is "
                "EXPLORATORY, and a number here would be a probability nobody calibrated"
            )
        recommended = output.get("recommended_next_evidence")
        if not isinstance(recommended, list) or not recommended:
            reasons.append(
                "recommended_next_evidence is empty. An exploratory hypothesis that names nothing "
                "to observe next is not exploratory, it is finished"
            )
        classifications = output.get("statement_classifications")
        if not isinstance(classifications, list) or not classifications:
            reasons.append(
                "statement_classifications is empty; every substantive statement is one of three"
            )
        else:
            kinds = {
                str(item.get("classification"))
                for item in classifications
                if isinstance(item, Mapping)
            }
            if kinds - set(CLASSIFICATION_DISPOSITIONS):
                reasons.append(f"statement_classifications carries unknown kinds: {sorted(kinds)}")
            if "HYPOTHESIS_TO_VALIDATE" not in kinds and "UNKNOWN_REQUIRES_EVIDENCE" not in kinds:
                reasons.append(
                    "every statement is classified as observed. A packet establishing three "
                    "dimensions and no problem, intervention or willingness to pay leaves "
                    "something unknown, and an output that finds nothing unknown has stopped "
                    "reading"
                )
    return PersistenceDecision(
        persist=not reasons,
        gate_version=SECOND_OPPORTUNITY_GATE_VERSION_V1_5,
        refusal_reasons=tuple(reasons),
        audit=decision.audit,
        notes=decision.notes,
    )
