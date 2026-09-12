"""The second-Opportunity output gate v1.2.0: the v1.1.0 schema, and assertions read in context.

Mission 1.84.10. The operator's decision, verbatim as data in `SEMANTIC_GATE_REPAIR_DECISION`: keep
the output schema v1.1.0 and the prompt v1.2.0 unchanged, repair the semantic gate's assertion
context, whitelist nothing, remove no forbidden concept and weaken no evidence boundary.

**v1.0.0 and v1.1.0 are not touched.** `second_opportunity.py`, `guards.py` and `validation.py` are
byte-identical, so V2's and V3's verdicts still resolve against the code that produced them: V3's five
reasons reproduce under v1.1.0 exactly. This module composes a successor beside them:

* the same v1.1.0 schema validation, first, through the same validator;
* `opportunity-synthesis-persistence-gate@1.2.0`: v1.1.0's structural checks unchanged in meaning,
  plus the subject identity, the source families and supported/unsupported disjointness, with the
  lexical SCORED check replaced by an assertion-aware one;
* `opportunity-synthesis-audit@1.3.0` over EVERY field under an explicit field-context policy,
  where v1.1.0 read five prose fields and scanned the rest for phrases with no notion of denial;
* the forbidden transformations as ASSERTIONS, with the §20 concepts the v1.0.0 phrase list lacked;
* the v1.0.0 checks on confidence, next evidence and statement classifications, unchanged.

**Trusted context is an explicit channel** (§18, §19). `evaluate_second_opportunity_output_v1_2`
requires a `TrustedContext`, which `build_trusted_context` derives from the packet's own dimension
bounds and from the "establishes" side of `FORBIDDEN_TRANSFORMATIONS`, each with its provenance. It
licenses the definitional identifiers those facts carry, such as eForms `BT-161`, and nothing else.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .assertion_context import (
    ASSERTION_AUDIT_VERSION,
    ASSERTION_GUARD_VERSION,
    PERSISTENCE_GATE_VERSION_V1_2,
    SUPPORT_UNIVERSE_VERSION,
    Disposition,
    FieldContext,
    ForbiddenConcept,
    Shape,
    TrustedContext,
    TrustedFact,
    TrustedFactKind,
    _phrase_tokens,
    _spans,
    build_support_universe,
    evaluate_persistence_v1_2,
)
from .dimensions import EvidenceDimension
from .mapping import DIMENSION_MAP_VERSION, SIGNAL_DIMENSION_MAP
from .packet import OpportunityEvidencePacket
from .schema_validation import schema_violations
from .second_opportunity import (
    _FORBIDDEN_PHRASES,
    CONFIDENCE_CLASSIFICATIONS,
    FORBIDDEN_TRANSFORMATIONS,
    PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
    SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2,
)
from .synthesis import MANDATORY_UNSUPPORTED_REPORT
from .validation import PersistenceDecision

__all__ = [
    "SECOND_OPPORTUNITY_GATE_VERSION_V1_2",
    "SECOND_OPPORTUNITY_FIELD_POLICY_VERSION",
    "TRUSTED_CONTEXT_VERSION",
    "SEMANTIC_GATE_REPAIR_DECISION",
    "COMPONENT_VERSIONS_V1_2",
    "FORBIDDEN_CONCEPTS_V1_2",
    "CLASSIFICATION_DISPOSITIONS",
    "SECOND_OPPORTUNITY_FIELD_POLICY",
    "build_trusted_context",
    "evaluate_second_opportunity_output_v1_2",
]

SECOND_OPPORTUNITY_GATE_VERSION_V1_2 = "second-opportunity-output-gate@1.2.0"
SECOND_OPPORTUNITY_FIELD_POLICY_VERSION = "second-opportunity-field-context-policy@1.0.0"
TRUSTED_CONTEXT_VERSION = "second-opportunity-trusted-context@1.0.0"

#: §0, as the operator decided it. Carried as data so a record can be checked against it.
SEMANTIC_GATE_REPAIR_DECISION: tuple[str, ...] = (
    "KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED",
    "KEEP_PROMPT_V1_2_0_UNCHANGED",
    "REPAIR_SEMANTIC_GATE_ASSERTION_CONTEXT",
    "DO_NOT_WHITELIST_THE_V3_ANSWER",
    "DO_NOT_REMOVE_FORBIDDEN_CONCEPTS",
    "DO_NOT_WEAKEN_EVIDENCE_BOUNDARIES",
)

#: Every versioned component the v1.2.0 gate is made of.
COMPONENT_VERSIONS_V1_2: dict[str, str] = {
    "gate": SECOND_OPPORTUNITY_GATE_VERSION_V1_2,
    "output_schema": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
    "persistence_gate": PERSISTENCE_GATE_VERSION_V1_2,
    "audit": ASSERTION_AUDIT_VERSION,
    "claim_guard": ASSERTION_GUARD_VERSION,
    "field_context_policy": SECOND_OPPORTUNITY_FIELD_POLICY_VERSION,
    "support_universe": SUPPORT_UNIVERSE_VERSION,
    "trusted_context": TRUSTED_CONTEXT_VERSION,
}

#: v1.0.0's phrases, every one kept, plus the forms that express the same transformation.
_ADDED_PHRASES: dict[str, tuple[str, ...]] = {
    "REALISED_SPEND": (
        "realised expenditure",
        "realized expenditure",
        "actually spent",
        "actually paid",
    ),
    "MARKET_DEMAND": ("software demand", "product demand"),
    "WILLINGNESS_TO_PAY": ("willingness to spend", "willing to spend"),
}

#: §20's concepts that v1.0.0's phrase list did not name at all.
_ADDED_CONCEPTS: tuple[ForbiddenConcept, ...] = (
    ForbiddenConcept(
        "MARKET_SIZE",
        ("market size", "size of the market", "addressable market"),
        "the size of any market, which no observation here measures",
    ),
    ForbiddenConcept("BUYER_NEED", ("buyer need",), "a need that any buyer has"),
    ForbiddenConcept(
        "UNMET_NEED", ("unmet need", "underserved", "unserved need"), "an unmet or underserved need"
    ),
    ForbiddenConcept(
        "SOLUTION_DISSATISFACTION",
        ("dissatisfaction", "dissatisfied"),
        "dissatisfaction with any existing solution",
    ),
    ForbiddenConcept(
        "SOLUTION_GAP",
        ("solution gap", "market gap", "gap in the market"),
        "a gap no solution fills",
    ),
    ForbiddenConcept(
        "COMPETITIVE_GAP",
        ("competitive gap", "competitor weakness", "weak competition", "weak competitors"),
        "a weakness in whoever already serves the need",
    ),
    ForbiddenConcept(
        "PROFITABILITY", ("profitability", "profitable", "profit margin"), "profit for anybody"
    ),
)

FORBIDDEN_CONCEPTS_V1_2: tuple[ForbiddenConcept, ...] = (
    *(
        ForbiddenConcept(name, (*_FORBIDDEN_PHRASES[name], *_ADDED_PHRASES.get(name, ())), never)
        for name, _establishes, never in FORBIDDEN_TRANSFORMATIONS
    ),
    *_ADDED_CONCEPTS,
)

#: The classification a statement carries is its disposition. OBSERVED must be supported; a
#: hypothesis is not promoted; an unknown is not an assertion (§10).
CLASSIFICATION_DISPOSITIONS: dict[str, Disposition] = {
    "OBSERVED_OR_EVIDENCE_SUPPORTED": Disposition.SUPPORTED_ASSERTION,
    "HYPOTHESIS_TO_VALIDATE": Disposition.HYPOTHESIS_TO_VALIDATE,
    "UNKNOWN_REQUIRES_EVIDENCE": Disposition.UNKNOWN_REQUIRES_EVIDENCE,
}

_D, _S = Disposition, Shape

#: §7. Every property of the v1.1.0 schema, and nothing else, with what its text does.
SECOND_OPPORTUNITY_FIELD_POLICY: tuple[FieldContext, ...] = (
    FieldContext("decision", _D.STRUCTURAL_FACT, _S.ENUMERATION, "one of two permitted values"),
    FieldContext("subject", _D.STRUCTURAL_FACT, _S.ENUMERATION, "must equal the packet's identity"),
    FieldContext(
        "target_actor_if_supported",
        _D.SUPPORTED_ASSERTION,
        _S.FREE,
        "names an actor as supported, or the sentinel",
    ),
    FieldContext("observed_need", _D.SUPPORTED_ASSERTION, _S.FREE, "states what was observed"),
    FieldContext(
        "candidate_intervention_class",
        _D.SUPPORTED_ASSERTION,
        _S.FREE,
        "states an intervention class the evidence supports",
    ),
    FieldContext(
        "hypothesis_statement",
        _D.HYPOTHESIS_TO_VALIDATE,
        _S.FREE,
        "prose: each clause is read on its own terms, and a hypothesis is framed or it is an "
        "assertion",
    ),
    FieldContext(
        "supported_dimensions",
        _D.STRUCTURAL_FACT,
        _S.ENUMERATION,
        "canonical dimension names; each must be a packet dimension",
    ),
    FieldContext(
        "unsupported_dimensions",
        _D.EXPLICITLY_NOT_SUPPORTED,
        _S.ENUMERATION,
        "canonical dimension names reported as unsupported; disjoint from the supported ones",
    ),
    FieldContext("supporting_evidence_ids", _D.STRUCTURAL_FACT, _S.ENUMERATION, "packet ids"),
    FieldContext("supporting_claim_ids", _D.STRUCTURAL_FACT, _S.ENUMERATION, "packet ids"),
    FieldContext("source_families", _D.STRUCTURAL_FACT, _S.ENUMERATION, "packet families"),
    FieldContext(
        "independence_status",
        _D.STRUCTURAL_FACT,
        _S.FREE,
        "restates the packet's independence fact",
    ),
    FieldContext(
        "reliability_status",
        _D.STRUCTURAL_FACT,
        _S.FREE,
        "restates the packet's scorability; a score may be denied and never asserted",
    ),
    FieldContext(
        "evidence_bound_reasoning_summary",
        _D.SUPPORTED_ASSERTION,
        _S.FREE,
        "asserted reasoning, which may deny and may restate trusted limiting facts",
    ),
    FieldContext(
        "critical_uncertainties",
        _D.UNKNOWN_REQUIRES_EVIDENCE,
        _S.UNCERTAINTY,
        "each item states what is not known and must stay uncertainty-shaped",
    ),
    FieldContext(
        "commercial_claims_supported",
        _D.SUPPORTED_ASSERTION,
        _S.FREE,
        "each item is asserted as supported and is checked strictly (§9)",
    ),
    FieldContext(
        "commercial_claims_not_supported",
        _D.EXPLICITLY_NOT_SUPPORTED,
        _S.FREE,
        "each item names a claim this packet does NOT support (§9)",
    ),
    FieldContext(
        "recommended_next_evidence",
        _D.FUTURE_EVIDENCE_REQUEST,
        _S.REQUEST,
        "each item names what would have to be observed and must stay request-shaped (§11)",
    ),
    FieldContext("confidence_classification", _D.STRUCTURAL_FACT, _S.ENUMERATION, "EXPLORATORY"),
    FieldContext(
        "statement_classifications",
        None,
        _S.LABELLED,
        "each statement takes the disposition of the classification it carries (§10)",
        item_label_key="classification",
        item_text_key="statement",
    ),
)


def _concepts_named_in(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    return tuple(
        sorted(
            {
                c.name
                for c in FORBIDDEN_CONCEPTS_V1_2
                for p in c.phrases
                if _phrase_tokens(p) and _spans(lowered, p)
            }
        )
    )


def build_trusted_context(packet: OpportunityEvidencePacket) -> TrustedContext:
    """C, for one packet: its own dimension bounds and the establishes side of the transformations.

    Both are frozen repository text with a provenance -- the mapping that produced the bound and
    the prompt version that rendered it -- and neither is the prompt as a whole. The never-side of
    a transformation is not included: it licenses a denial, and a denial needs no licence.
    """
    bound_owner = {m.bound: sid for sid, m in SIGNAL_DIMENSION_MAP.items() if m.bound}
    facts: list[TrustedFact] = []
    for index, bound in enumerate(packet.dimension_bounds):
        signal = bound_owner.get(bound, "UNREGISTERED")
        facts.append(
            TrustedFact(
                fact_id=f"DIMENSION_BOUND:{signal}",
                kind=TrustedFactKind.LIMITING,
                text=bound,
                provenance=(
                    f"{DIMENSION_MAP_VERSION} bound for signal type {signal!r}, carried on the "
                    f"packet as dimension_bounds[{index}] and rendered into the trusted_context "
                    f"region of prompt {SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2}"
                ),
                never_supports=_concepts_named_in(bound),
            )
        )
    for name, establishes, never in FORBIDDEN_TRANSFORMATIONS:
        facts.append(
            TrustedFact(
                fact_id=f"FORBIDDEN_TRANSFORMATION:{name}:ESTABLISHES",
                kind=TrustedFactKind.DEFINITIONAL,
                text=establishes,
                provenance=(
                    "FORBIDDEN_TRANSFORMATIONS, the side the packet establishes, rendered into the "
                    f"system region of prompt {SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2}"
                ),
                never_supports=tuple(sorted({name, *_concepts_named_in(never)})),
            )
        )
    return TrustedContext(version=TRUSTED_CONTEXT_VERSION, facts=tuple(facts))


def evaluate_second_opportunity_output_v1_2(
    output: Mapping[str, object],
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
    *,
    trusted_context: TrustedContext,
    mandatory_unsupported: Sequence[EvidenceDimension] = MANDATORY_UNSUPPORTED_REPORT,
) -> PersistenceDecision:
    """The v1.2.0 gate. `trusted_context` is required: there is no default channel.

    Structure first, through the v1.1.0 validator, and the semantic gate still runs, so a caller
    learns every reason at once. Then the persistence gate v1.2.0 with its audit, then v1.0.0's
    checks on the three fields that version added.
    """
    structural = schema_violations(dict(output), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    universe = build_support_universe(packet, claim_statements, trusted_context)
    decision = evaluate_persistence_v1_2(
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
        *(f"{SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1}: {v}" for v in structural),
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
        gate_version=SECOND_OPPORTUNITY_GATE_VERSION_V1_2,
        refusal_reasons=tuple(reasons),
        audit=decision.audit,
        notes=decision.notes,
    )
