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
from .output_constraints import OUTPUT_CONSTRAINT_RENDERER_VERSION, render_output_constraints
from .packet import OpportunityEvidencePacket
from .schema_validation import schema_violations
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
    # -- Mission 1.84.4, the bounded successor. The names above stay bound to v1.0.0. --
    "SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1",
    "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1",
    "SECOND_OPPORTUNITY_GATE_VERSION_V1_1",
    "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1",
    "SECOND_OPPORTUNITY_SYSTEM_V1_1",
    "BOUNDED_OUTPUT_CONTRACT_RULES",
    "CANONICAL_UUID_PATTERN",
    "REGISTRY_SLUG_PATTERN",
    "REGISTRY_SLUG_MAX_LENGTH",
    "CRITICAL_UNCERTAINTY_MAX_LENGTH",
    "COMMERCIAL_CLAIM_MAX_LENGTH",
    "BOUNDED_ITEM_TYPES",
    "render_second_opportunity_prompt_v1_1",
    "second_opportunity_prompt_hash_v1_1",
    "evaluate_second_opportunity_output_v1_1",
    # -- Mission 1.84.8, prompt v1.2.0. The schema and gate stay v1.1.0; only the prompt moves. --
    "SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2",
    "OUTPUT_CONSTRAINT_NOTES_V1_2",
    "OUTPUT_CONTRACT_OPENING",
    "OUTPUT_CONTRACT_CLOSING",
    "SECOND_OPPORTUNITY_OUTPUT_CONSTRAINTS_V1_2",
    "SECOND_OPPORTUNITY_OUTPUT_CONTRACT_BLOCK_V1_2",
    "SECOND_OPPORTUNITY_SYSTEM_V1_2",
    "render_second_opportunity_prompt_v1_2",
    "second_opportunity_prompt_hash_v1_2",
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


# =============================================================================================
# Mission 1.84.4 -- the bounded successor contract.
#
# Mission 1.84.3 found that `second-opportunity-synthesis-output@1.0.0` has NO finite maximum
# serialized size: eight required array paths bound how MANY strings they hold and never how LONG
# any of them may be, so a single element could be a megabyte and still satisfy the contract. All
# eight are Mission 1.31's base schema, byte-identically; the three fields Mission 1.84 added are
# the only properly bounded ones in it.
#
# The operator's decision was BOUND_THE_EIGHT_UNBOUNDED_ITEM_TYPES, and explicitly NOT an
# operator-declared arbitrary token ceiling. So a successor exists and v1.0.0 is untouched: the
# historical execution must keep resolving against the exact contract it actually used, and gate
# 64 asserts the frozen prompt document still names v1.0.0's digest.
#
# EACH BOUND MATCHES THE FIELD'S SEMANTICS. One maxLength applied to all eight would be a number
# rather than a contract: a dimension is a member of a closed vocabulary, an Evidence id is a
# UUID, a source family is a registry slug, and only three of the eight are prose.
# =============================================================================================

SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1 = "1.1.0"
SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1 = "second-opportunity-synthesis-output@1.1.0"
SECOND_OPPORTUNITY_GATE_VERSION_V1_1 = "second-opportunity-output-gate@1.1.0"

#: The canonical identity grammar for `ClaimId` and `EvidenceId`. Both are `_UuidId` in
#: `sros_contracts.ids`, whose constructor canonicalises through `str(uuid.UUID(value))` -- so the
#: canonical form is lowercase hex with hyphens, and an uppercase or braced spelling is a
#: DIFFERENT string from the one the packet supplies. `format: "uuid"` is carried beside this for
#: interop, exactly as `gen_jsonschema` emits it, and it is an ANNOTATION: the pattern is what
#: refuses prose. Determined independently for Claim and for Evidence, as sections 7 and 8
#: require; they agree because both subclass the same canonical base, not because current rows
#: happen to look alike.
CANONICAL_UUID_PATTERN = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

#: A UUID in canonical form is exactly 36 characters. Carried as `maxLength` beside the pattern
#: because a recursive capacity walker reads a declared bound and does not reason about a regex.
CANONICAL_UUID_LENGTH = 36

#: `source_family` is a REGISTRY, not a closed enum. `domain.v1.json` lists it under `registries`
#: and not under `closed_enums`; `registry.sources.source_family` carries a foreign key to
#: `registry.registry_entries (registry, id)`; and that table's `registry_entries_id_slug_check`
#: is the canonical grammar. Freezing today's fifteen members into an enum would put an extensible
#: registry inside a frozen contract, and the next registered family would make the schema refuse
#: a true answer.
REGISTRY_SLUG_PATTERN = "^[a-z0-9][a-z0-9._-]{0,127}$"
REGISTRY_SLUG_MAX_LENGTH = 128

#: Section 10, the operator's number. One element is one bounded uncertainty, not an essay.
CRITICAL_UNCERTAINTY_MAX_LENGTH = 500

#: Section 11, the operator's number, and it applies because these fields are genuinely narrative.
#: The historical Mission 1.31.1 output carries sentences -- "That a buyer with budget authority
#: exists in this space" -- and the persistence gate audits them as PROSE through the commercial-
#: vocabulary guard, which needs a sentence to read. They are NOT canonical dimension names.
COMMERCIAL_CLAIM_MAX_LENGTH = 300


def _bounded_schema() -> dict[str, object]:
    """v1.0.0 with the eight unbounded item types bounded, and nothing else changed.

    Built by copying the v1.0.0 schema and REPLACING eight `items` subschemas. No `maxItems` is
    reduced, no field is removed, nothing is reordered and no default is introduced -- section 12
    forbids letting the failed 18/20 response decide any of that, and shrinking the field it
    omitted would not have made the schema finite anyway.
    """
    schema: dict[str, Any] = json.loads(json.dumps(SECOND_OPPORTUNITY_OUTPUT_SCHEMA))
    properties: dict[str, Any] = schema["properties"]

    # Derived from the canonical vocabulary rather than transcribed. Section 6 forbids a
    # manually-maintained second dimension list where a canonical source exists, and
    # `EvidenceDimension` is what the gate itself compares against.
    dimension_values = [dimension.value for dimension in EvidenceDimension]
    for name in ("supported_dimensions", "unsupported_dimensions"):
        properties[name]["items"] = {
            "type": "string",
            "enum": dimension_values,
            "description": (
                "A member of the canonical EvidenceDimension vocabulary. An unknown dimension is "
                "refused however short it is."
            ),
        }

    for name, what in (
        ("supporting_evidence_ids", "Evidence"),
        ("supporting_claim_ids", "Claim"),
    ):
        properties[name]["items"] = {
            "type": "string",
            "format": "uuid",
            "pattern": CANONICAL_UUID_PATTERN,
            "maxLength": CANONICAL_UUID_LENGTH,
            "description": (
                f"A canonical {what} id: the lowercase hyphenated UUID form that "
                "`sros_contracts.ids` produces. Prose is impossible here."
            ),
        }

    properties["source_families"]["items"] = {
        "type": "string",
        "pattern": REGISTRY_SLUG_PATTERN,
        "maxLength": REGISTRY_SLUG_MAX_LENGTH,
        "description": (
            "A `source_family` registry id, under the slug grammar `registry.registry_entries` "
            "enforces. A registry rather than an enum, because a family may be registered "
            "without a contract change."
        ),
    }

    properties["critical_uncertainties"]["items"] = {
        "type": "string",
        "minLength": 1,
        "maxLength": CRITICAL_UNCERTAINTY_MAX_LENGTH,
        "description": "One bounded uncertainty, stated once. Not an essay and not an enum.",
    }

    for name in ("commercial_claims_supported", "commercial_claims_not_supported"):
        properties[name]["items"] = {
            "type": "string",
            "maxLength": COMMERCIAL_CLAIM_MAX_LENGTH,
            "description": (
                "One concise auditable commercial proposition. The explanation belongs in "
                "`evidence_bound_reasoning_summary`, which is already bounded."
            ),
        }

    return schema


SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1: dict[str, object] = _bounded_schema()


#: What each formerly-unbounded path became, and by which method. Kept as data so the decision
#: artifact, the gate and the capacity walker read one table rather than three copies of it.
BOUNDED_ITEM_TYPES: tuple[tuple[str, str], ...] = (
    ("supported_dimensions", "CLOSED_VOCABULARY"),
    ("unsupported_dimensions", "CLOSED_VOCABULARY"),
    ("supporting_evidence_ids", "CANONICAL_IDENTIFIER"),
    ("supporting_claim_ids", "CANONICAL_IDENTIFIER"),
    ("source_families", "BOUNDED_IDENTIFIER"),
    ("critical_uncertainties", "BOUNDED_NARRATIVE"),
    ("commercial_claims_supported", "BOUNDED_NARRATIVE"),
    ("commercial_claims_not_supported", "BOUNDED_NARRATIVE"),
)


def _bounded_output_block() -> str:
    dimensions = ", ".join(dimension.value for dimension in EvidenceDimension)
    return (
        "THE OUTPUT CONTRACT IS BOUNDED, AND AN ANSWER THAT EXCEEDS A BOUND IS REFUSED RATHER "
        "THAN TRIMMED.\n\n"
        "  supported_dimensions, unsupported_dimensions\n"
        f"    exactly these names, spelled exactly: {dimensions}\n\n"
        "  supporting_evidence_ids, supporting_claim_ids\n"
        "    the ids supplied to you, copied verbatim. No prose, no description, no partial id.\n\n"
        "  source_families\n"
        "    the family names supplied to you as a packet fact, copied verbatim.\n\n"
        "  critical_uncertainties\n"
        f"    at most {CRITICAL_UNCERTAINTY_MAX_LENGTH} characters each. One uncertainty per "
        "element.\n\n"
        "  commercial_claims_supported, commercial_claims_not_supported\n"
        f"    at most {COMMERCIAL_CLAIM_MAX_LENGTH} characters each. One proposition per element; "
        "the\n    reasoning belongs in evidence_bound_reasoning_summary.\n\n"
        "These are limits on FORM, never on how much you may refuse to conclude. A shorter answer "
        "that\nnames more unknowns is a better answer here than a longer one that names fewer."
    )


BOUNDED_OUTPUT_CONTRACT_RULES = _bounded_output_block()


SECOND_OPPORTUNITY_SYSTEM_V1_1 = (
    SECOND_OPPORTUNITY_SYSTEM + "\n" + BOUNDED_OUTPUT_CONTRACT_RULES + "\n"
)


def render_second_opportunity_prompt_v1_1(
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
) -> SynthesisPromptParts:
    """The v1.1.0 regions. Only the system region differs from v1.0.0.

    The trusted context, the untrusted region and the task are the v1.0.0 objects unchanged, which
    is what keeps the TED factual content supplied to the model byte-identical across the version
    bump (sections 14 and 15).
    """
    base = render_second_opportunity_prompt(packet, claim_statements, evidence_to_claim)
    return SynthesisPromptParts(
        system_instructions=SECOND_OPPORTUNITY_SYSTEM_V1_1,
        trusted_context=base.trusted_context,
        untrusted=base.untrusted,
        task=base.task,
        metadata={
            **base.metadata,
            "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1,
            "output_schema_version": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
            "gate_version": SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
        },
    )


def second_opportunity_prompt_hash_v1_1(parts: SynthesisPromptParts) -> str:
    """The v1.1.0 digest, over the same regions plus the v1.1.0 schema.

    The schema sits inside the hashed payload exactly as it does for v1.0.0, so bounding the
    contract moves this digest whether or not a rendered byte changed. Pretending the old SHA
    still identifies this execution is what section 13 refuses.
    """
    payload = json.dumps(
        {
            "procedure": SECOND_OPPORTUNITY_PROCEDURE_VERSION,
            "prompt_id": SECOND_OPPORTUNITY_PROMPT_ID,
            "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_1,
            "system_instructions": parts.system_instructions,
            "task": parts.task,
            "trusted_context": parts.trusted_context,
            "untrusted": [list(pair) for pair in parts.untrusted],
            "output_schema": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def evaluate_second_opportunity_output_v1_1(
    output: Mapping[str, object],
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
    mandatory_unsupported: Sequence[EvidenceDimension] = MANDATORY_UNSUPPORTED_REPORT,
) -> PersistenceDecision:
    """The v1.1.0 gate: the v1.0.0 semantic gate, plus the bound it now has to enforce.

    **Structure is checked and the semantic gate still runs.** A short answer naming an unknown
    dimension fails on structure; a well-formed answer saying the packet establishes willingness
    to pay fails on meaning. Reporting only the first would let a caller fix the one they were
    told about and be refused again.

    **Nothing semantic was weakened to make room** (section 16). Every v1.0.0 refusal is reached
    through the v1.0.0 gate itself rather than reimplemented, so the two cannot drift apart.
    """
    structural = schema_violations(dict(output), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    decision = evaluate_second_opportunity_output(
        output, packet, claim_statements, evidence_to_claim, mandatory_unsupported
    )
    reasons = [
        *(f"{SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1}: {v}" for v in structural),
        *decision.refusal_reasons,
    ]
    return PersistenceDecision(
        persist=not reasons,
        gate_version=SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
        refusal_reasons=tuple(reasons),
        audit=decision.audit,
        notes=decision.notes,
    )


# =============================================================================================
# Mission 1.84.8 -- prompt v1.2.0: the output-contract block, derived from the live schema.
#
# Mission 1.84.7's one request came back finished and was refused by the v1.1.0 schema on
# `evidence_bound_reasoning_summary`, whose bound the v1.1.0 block above never stated in words: it
# named two narrative bounds by hand and left the rest to the forced tool's input schema. The
# operator kept the schema and the gate exactly as they are and asked for that drift to be removed
# in a GENERAL way, so what follows is not a corrected copy of the list above. It is rendered from
# `SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1` by `render_output_constraints`, and no bound is written
# here.
#
# v1.1.0 is not touched. `BOUNDED_OUTPUT_CONTRACT_RULES` and `SECOND_OPPORTUNITY_SYSTEM_V1_1` still
# render the bytes Mission 1.84.7 sent, because a historical execution must keep resolving against
# the prompt it actually used.
# =============================================================================================

SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2 = "1.2.0"

#: Per-field guidance that is not a limit, carried from the v1.1.0 block word for word. The
#: renderer refuses a note carrying a digit: every number the model reads comes from the schema.
OUTPUT_CONSTRAINT_NOTES_V1_2: dict[str, str] = {
    "supporting_evidence_ids": (
        "the ids supplied to you, copied verbatim. No prose, no description, no partial id."
    ),
    "supporting_claim_ids": (
        "the ids supplied to you, copied verbatim. No prose, no description, no partial id."
    ),
    "source_families": "the family names supplied to you as a packet fact, copied verbatim.",
    "critical_uncertainties": "One uncertainty per element.",
    "commercial_claims_supported": (
        "One proposition per element; the reasoning belongs in evidence_bound_reasoning_summary."
    ),
    "commercial_claims_not_supported": (
        "One proposition per element; the reasoning belongs in evidence_bound_reasoning_summary."
    ),
}

#: The v1.1.0 block's framing sentences, unchanged: a bound refuses rather than trims, and a bound
#: limits form, never how much may be left unconcluded.
OUTPUT_CONTRACT_OPENING = (
    "THE OUTPUT CONTRACT IS BOUNDED, AND AN ANSWER THAT EXCEEDS A BOUND IS REFUSED RATHER THAN "
    "TRIMMED."
)
OUTPUT_CONTRACT_CLOSING = (
    "These are limits on FORM, never on how much you may refuse to conclude. A shorter answer "
    "that\nnames more unknowns is a better answer here than a longer one that names fewer."
)

SECOND_OPPORTUNITY_OUTPUT_CONSTRAINTS_V1_2 = render_output_constraints(
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, OUTPUT_CONSTRAINT_NOTES_V1_2
)

SECOND_OPPORTUNITY_OUTPUT_CONTRACT_BLOCK_V1_2 = (
    OUTPUT_CONTRACT_OPENING
    + "\n\n"
    + SECOND_OPPORTUNITY_OUTPUT_CONSTRAINTS_V1_2
    + "\n\n"
    + OUTPUT_CONTRACT_CLOSING
)

SECOND_OPPORTUNITY_SYSTEM_V1_2 = (
    SECOND_OPPORTUNITY_SYSTEM + "\n" + SECOND_OPPORTUNITY_OUTPUT_CONTRACT_BLOCK_V1_2 + "\n"
)


def render_second_opportunity_prompt_v1_2(
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
) -> SynthesisPromptParts:
    """The v1.2.0 regions. Only the system region differs from v1.1.0, and only after v1.0.0's part.

    The trusted context, the untrusted region and the task are the v1.1.0 objects unchanged, so the
    TED factual content supplied to the model is byte-identical across the version bump.
    """
    base = render_second_opportunity_prompt_v1_1(packet, claim_statements, evidence_to_claim)
    return SynthesisPromptParts(
        system_instructions=SECOND_OPPORTUNITY_SYSTEM_V1_2,
        trusted_context=base.trusted_context,
        untrusted=base.untrusted,
        task=base.task,
        metadata={**base.metadata, "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2},
    )


def second_opportunity_prompt_hash_v1_2(parts: SynthesisPromptParts) -> str:
    """The v1.2.0 digest: the same regions and the unchanged v1.1.0 schema, plus the renderer.

    The renderer's version is bound as well as its output, so a change to how constraints are
    rendered moves the digest even in the unlikely case that it leaves this schema's text alone.
    """
    payload = json.dumps(
        {
            "procedure": SECOND_OPPORTUNITY_PROCEDURE_VERSION,
            "prompt_id": SECOND_OPPORTUNITY_PROMPT_ID,
            "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2,
            "output_constraint_renderer": OUTPUT_CONSTRAINT_RENDERER_VERSION,
            "system_instructions": parts.system_instructions,
            "task": parts.task,
            "trusted_context": parts.trusted_context,
            "untrusted": [list(pair) for pair in parts.untrusted],
            "output_schema": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
