"""The second-Opportunity synthesis contract: prompt, output schema and output gate.

Mission 1.84. One subject, one packet, one call, and every part of it frozen before anything is
sent. Nothing here imports a Gateway or a provider, so this package still cannot call a model by
accident (Mission 1.28).

**The system region is Mission 1.31's, byte for byte.** It is imported rather than copied: a
second copy of an instruction is a second thing to drift, and the sentences that withdraw prior
knowledge have already survived one execution. What this module adds is what the subject makes
necessary and the first subject did not.

**A procurement record invites four specific distortions, and each is named.** TED's own reuse
conditions forbid distorting the meaning of a document (Article 6(2)(b)), and the four ways a
model would distort THIS packet are arithmetic rather than rhetorical:

    a stated total value      ->  money somebody paid
    procurement activity      ->  market demand
    a contracting authority   ->  a buyer for a software product
    an economic value         ->  willingness to pay

Each is refused in the instruction and again in the gate, because an instruction is a request and
a gate is a check.

**The world-knowledge list is the subject's own.** Mission 1.31 froze a container vocabulary,
which is the right check and the wrong list here. A model writing about sports facilities reaches
for pools, gyms, memberships, bookings and councils, and none of those words is in the packet.

**Two fields are added to the schema and neither is a confidence number.**
`recommended_next_evidence` says what would have to be observed next, and
`confidence_classification` is a closed enum whose only member is EXPLORATORY -- a label, not a
probability, because a self-reported certainty is not one.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from .dimensions import EvidenceDimension
from .packet import OpportunityEvidencePacket
from .synthesis import (
    MANDATORY_UNSUPPORTED_REPORT,
    SYNTHESIS_OUTPUT_SCHEMA,
    SYNTHESIS_SYSTEM,
    SynthesisPromptParts,
    render_synthesis_prompt,
)
from .validation import PersistenceDecision, evaluate_persistence

__all__ = [
    "SECOND_OPPORTUNITY_PROCEDURE_VERSION",
    "SECOND_OPPORTUNITY_PROMPT_ID",
    "SECOND_OPPORTUNITY_PROMPT_VERSION",
    "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION",
    "SECOND_OPPORTUNITY_GATE_VERSION",
    "SECOND_OPPORTUNITY_SYSTEM",
    "SECOND_OPPORTUNITY_OUTPUT_SCHEMA",
    "ANTI_DISTORTION_RULES",
    "FORBIDDEN_TRANSFORMATIONS",
    "PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS",
    "CONFIDENCE_CLASSIFICATIONS",
    "render_second_opportunity_prompt",
    "second_opportunity_prompt_hash",
    "evaluate_second_opportunity_output",
]

SECOND_OPPORTUNITY_PROCEDURE_VERSION = "second-opportunity-synthesis@1.0.0"
SECOND_OPPORTUNITY_PROMPT_ID = "second-opportunity-synthesis-prompt"
SECOND_OPPORTUNITY_PROMPT_VERSION = "1.0.0"
SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION = "second-opportunity-synthesis-output@1.0.0"
SECOND_OPPORTUNITY_GATE_VERSION = "second-opportunity-output-gate@1.0.0"

#: The only value `confidence_classification` may take. A closed enum of one, because the field
#: exists to record that the answer is exploratory and not to grade how exploratory it is.
CONFIDENCE_CLASSIFICATIONS: tuple[str, ...] = ("EXPLORATORY",)

#: §19. Each entry is (name, what the packet establishes, what it is NOT). The gate checks the
#: FORBIDDEN side lexically; the instruction states both sides, because a model told only what to
#: avoid does not know what it may say.
FORBIDDEN_TRANSFORMATIONS: tuple[tuple[str, str, str], ...] = (
    (
        "REALISED_SPEND",
        "a stated TOTAL_VALUE at notice scope, which eForms BT-161 defines as the value of all "
        "contracts awarded in the notice INCLUDING OPTIONS AND RENEWALS",
        "money anybody paid, actual expenditure, a budget consumed, or a contract's final cost",
    ),
    (
        "MARKET_DEMAND",
        "that contracting authorities published notices classified under one CPV class",
        "market demand, appetite, interest, adoption, uptake, or a market that wants anything",
    ),
    (
        "SOFTWARE_BUYER",
        "that a contracting authority exists and published a procurement notice",
        "a buyer for a software product, a customer, a prospect, a user, or anybody who would "
        "purchase an intervention nobody has specified",
    ),
    (
        "WILLINGNESS_TO_PAY",
        "an economic value stated in a published notice",
        "willingness to pay, price tolerance, budget for software, or ability to pay for a product",
    ),
    (
        "PRODUCT_MARKET_FIT",
        "that activity exists in a bounded set of notices under one classification",
        "product-market fit, a validated market, a proven need, or a confirmed opportunity",
    ),
)

#: Words a model reaches for when it stops reading THIS packet. Permitted exactly when a supplied
#: statement contains one, which none of these does.
PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS: tuple[str, ...] = (
    "gym",
    "gyms",
    "pool",
    "pools",
    "swimming",
    "stadium",
    "stadiums",
    "arena",
    "arenas",
    "leisure",
    "fitness",
    "membership",
    "memberships",
    "member",
    "members",
    "booking",
    "bookings",
    "scheduling",
    "roster",
    "rostering",
    "maintenance",
    "council",
    "councils",
    "municipality",
    "municipalities",
    "municipal",
    "tender",
    "tenders",
    "tendering",
    "bidder",
    "bidders",
    "supplier",
    "suppliers",
    "vendor",
    "vendors",
    "competitor",
    "competitors",
    "incumbent",
    "incumbents",
    "saas",
    "software",
    "platform",
    "app",
    "subscription",
    "licence",
    "license",
    "sector",
    "industry",
    "market",
    "budget",
    "budgets",
    "spend",
    "spending",
    "revenue",
    "customers",
    "users",
    "demand",
    "popular",
    "widely",
    "typically",
    "usually",
    "often",
)


def _anti_distortion_block() -> str:
    lines = ["WHAT THIS PACKET IS AND IS NOT. Each line is refused by a deterministic gate."]
    for name, establishes, never in FORBIDDEN_TRANSFORMATIONS:
        lines.append(f"  {name}")
        lines.append(f"    the packet establishes: {establishes}")
        lines.append(f"    it is NOT: {never}")
    return "\n".join(lines)


ANTI_DISTORTION_RULES = _anti_distortion_block()


SECOND_OPPORTUNITY_SYSTEM = (
    SYNTHESIS_SYSTEM
    + """
THIS PACKET IS A PUBLIC-PROCUREMENT RECORD, AND IT INVITES FOUR SPECIFIC ERRORS.

"""
    + ANTI_DISTORTION_RULES
    + """

The source's own reuse conditions oblige a reuser NOT TO DISTORT the original meaning of a
document. Every line above is that obligation applied to the exact statements you were given, so
it is a legal condition here as well as an epistemic one.

CLASSIFY EVERY SUBSTANTIVE STATEMENT. Each one is exactly one of:

  OBSERVED_OR_EVIDENCE_SUPPORTED   a supplied statement establishes it
  HYPOTHESIS_TO_VALIDATE           it is worth testing and nothing supplied establishes it
  UNKNOWN_REQUIRES_EVIDENCE        it is not established and no test is proposed here

A hypothesis written as an observation is the failure this task exists to avoid. "Operators need
scheduling software" is refused. "One hypothesis to test is whether operators face scheduling
problems; the supplied statements do not establish that they do" is the shape asked for.

ATTRIBUTION. The supplied statements name their source in their own wording. Keep that: a
derived statement about what a source published is attributed to that source, never asserted as
a fact about the world.

CONFIDENCE. `confidence_classification` is EXPLORATORY and nothing else. There is no numeric
confidence, no probability and no score anywhere in this task.

NEXT EVIDENCE. `recommended_next_evidence` names what would have to be OBSERVED to move any
hypothesis forward. It is not a plan, not a product roadmap and not a research summary.
"""
)


def _extended_schema() -> dict[str, object]:
    """The frozen schema plus two fields, without touching the frozen one."""
    schema: dict[str, Any] = json.loads(json.dumps(SYNTHESIS_OUTPUT_SCHEMA))
    schema["required"] = [
        *schema["required"],
        "recommended_next_evidence",
        "confidence_classification",
        "statement_classifications",
    ]
    schema["properties"]["recommended_next_evidence"] = {
        "type": "array",
        "items": {"type": "string", "maxLength": 300},
        "maxItems": 8,
        "description": (
            "What would have to be OBSERVED next to move a hypothesis forward. Not a plan and "
            "not a roadmap."
        ),
    }
    schema["properties"]["confidence_classification"] = {
        "type": "string",
        "enum": list(CONFIDENCE_CLASSIFICATIONS),
        "description": "EXPLORATORY, and nothing else. A label, never a probability.",
    }
    schema["properties"]["statement_classifications"] = {
        "type": "array",
        "maxItems": 24,
        "items": {
            "type": "object",
            "additionalProperties": False,
            "required": ["statement", "classification"],
            "properties": {
                "statement": {"type": "string", "maxLength": 300},
                "classification": {
                    "type": "string",
                    "enum": [
                        "OBSERVED_OR_EVIDENCE_SUPPORTED",
                        "HYPOTHESIS_TO_VALIDATE",
                        "UNKNOWN_REQUIRES_EVIDENCE",
                    ],
                },
            },
        },
    }
    return schema


SECOND_OPPORTUNITY_OUTPUT_SCHEMA: dict[str, object] = _extended_schema()


def render_second_opportunity_prompt(
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
) -> SynthesisPromptParts:
    """The frozen prompt regions for this packet, composed from the frozen ones."""
    base = render_synthesis_prompt(packet, claim_statements, evidence_to_claim)
    return SynthesisPromptParts(
        system_instructions=SECOND_OPPORTUNITY_SYSTEM,
        trusted_context=base.trusted_context,
        untrusted=base.untrusted,
        task=base.task,
        metadata={
            **base.metadata,
            "procedure": SECOND_OPPORTUNITY_PROCEDURE_VERSION,
            "prompt_id": SECOND_OPPORTUNITY_PROMPT_ID,
            "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION,
            "output_schema_version": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION,
            "gate_version": SECOND_OPPORTUNITY_GATE_VERSION,
        },
    )


def second_opportunity_prompt_hash(parts: SynthesisPromptParts) -> str:
    """A digest over every region, so an execution can prove it sent these bytes."""
    payload = json.dumps(
        {
            "procedure": SECOND_OPPORTUNITY_PROCEDURE_VERSION,
            "prompt_id": SECOND_OPPORTUNITY_PROMPT_ID,
            "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION,
            "system_instructions": parts.system_instructions,
            "task": parts.task,
            "trusted_context": parts.trusted_context,
            "untrusted": [list(pair) for pair in parts.untrusted],
            "output_schema": SECOND_OPPORTUNITY_OUTPUT_SCHEMA,
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _prose_values(output: Mapping[str, object]) -> list[str]:
    values: list[str] = []
    for value in output.values():
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    values.append(item)
                elif isinstance(item, Mapping):
                    values.extend(v for v in item.values() if isinstance(v, str))
    return values


def evaluate_second_opportunity_output(
    output: Mapping[str, object],
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
    mandatory_unsupported: Sequence[EvidenceDimension] = MANDATORY_UNSUPPORTED_REPORT,
) -> PersistenceDecision:
    """The frozen gate, composed rather than rewritten.

    Everything the general gate checks is checked by the general gate, with this subject's own
    world-knowledge markers. What is added is the four transformations a procurement record
    invites, the two new fields, and the classification the instruction demands.

    Lexical filtering does not prove semantic safety, and this gate does not claim it does. It
    refuses what it can name; what it cannot name is why the execution mission stops for a human.
    """
    decision = evaluate_persistence(
        output,
        packet,
        claim_statements,
        evidence_to_claim,
        mandatory_unsupported,
        PROCUREMENT_EXTERNAL_KNOWLEDGE_MARKERS,
    )
    reasons = list(decision.refusal_reasons)
    if str(output.get("decision") or "") == "INSUFFICIENT_EVIDENCE":
        return decision

    classification = str(output.get("confidence_classification") or "")
    if classification not in CONFIDENCE_CLASSIFICATIONS:
        reasons.append(
            f"confidence_classification is {classification!r}; the only permitted value is "
            "EXPLORATORY, and a number here would be a probability nobody calibrated"
        )

    recommended = output.get("recommended_next_evidence")
    if not isinstance(recommended, list) or not recommended:
        reasons.append(
            "recommended_next_evidence is empty. An exploratory hypothesis that names nothing to "
            "observe next is not exploratory, it is finished"
        )

    classifications = output.get("statement_classifications")
    if not isinstance(classifications, list) or not classifications:
        reasons.append(
            "statement_classifications is empty; every substantive statement is one of three"
        )
    else:
        kinds = {
            str(item.get("classification")) for item in classifications if isinstance(item, Mapping)
        }
        if kinds - {
            "OBSERVED_OR_EVIDENCE_SUPPORTED",
            "HYPOTHESIS_TO_VALIDATE",
            "UNKNOWN_REQUIRES_EVIDENCE",
        }:
            reasons.append(f"statement_classifications carries unknown kinds: {sorted(kinds)}")
        if "HYPOTHESIS_TO_VALIDATE" not in kinds and "UNKNOWN_REQUIRES_EVIDENCE" not in kinds:
            reasons.append(
                "every statement is classified as observed. A packet establishing three "
                "dimensions and no problem, intervention or willingness to pay leaves something "
                "unknown, and an output that finds nothing unknown has stopped reading"
            )

    # §19, checked rather than requested. A forbidden transformation is refused wherever it
    # appears in the output, not only in the prose fields the general audit reads.
    haystack = " ".join(_prose_values(output)).lower()
    supplied = " ".join(claim_statements.values()).lower()
    for name, _establishes, never in FORBIDDEN_TRANSFORMATIONS:
        for phrase in _forbidden_phrases(name):
            if phrase in haystack and phrase not in supplied:
                reasons.append(
                    f"{name}: the output contains {phrase!r}, which no supplied statement "
                    f"contains. This packet is not {never}"
                )
    return PersistenceDecision(
        persist=not reasons,
        gate_version=SECOND_OPPORTUNITY_GATE_VERSION,
        refusal_reasons=tuple(reasons),
        audit=decision.audit,
        notes=decision.notes,
    )


#: The exact phrases each forbidden transformation is recognised by. Phrases rather than tokens,
#: because the single words are ordinary and the transformation is the sentence.
_FORBIDDEN_PHRASES: dict[str, tuple[str, ...]] = {
    "REALISED_SPEND": (
        "realised spend",
        "realized spend",
        "actual spend",
        "money spent",
        "amount paid",
        "was paid",
        "they paid",
        "expenditure of",
        "actual expenditure",
    ),
    "MARKET_DEMAND": (
        "market demand",
        "demand for",
        "there is demand",
        "demonstrates demand",
        "shows demand",
        "appetite for",
    ),
    "SOFTWARE_BUYER": (
        "would buy",
        "will buy",
        "are buyers",
        "is a buyer",
        "potential customers",
        "prospective customers",
        "target customers",
    ),
    "WILLINGNESS_TO_PAY": (
        "willingness to pay",
        "willing to pay",
        "able to pay",
        "budget for software",
        "can afford",
    ),
    "PRODUCT_MARKET_FIT": (
        "product-market fit",
        "product market fit",
        "validated market",
        "proven need",
        "confirmed need",
        "confirmed opportunity",
    ),
}


def _forbidden_phrases(name: str) -> tuple[str, ...]:
    return _FORBIDDEN_PHRASES[name]
