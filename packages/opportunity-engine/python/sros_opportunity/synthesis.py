"""The bounded synthesis prompt, as data rather than as a Gateway call.

Mission 1.31 §4, §5, §7, §8.

**This module imports no Gateway and no provider**, which is the Mission 1.28
boundary and is not weakened here: it returns the prompt REGIONS as plain
strings, and the runner wraps them in `RenderedPrompt` and `UntrustedText`. A
package that cannot import a provider cannot call one by accident, and the
versioned prompt text still lives with the engine that owns it rather than in a
script.

**The task is not "give me a SaaS idea about Docker".** It is: given this bounded
packet, construct the NARROWEST hypothesis the evidence supports, and name every
commercial dimension that remains unsupported. The reasoning runs

    evidence -> supported observation -> bounded need -> intervention CLASS

and never topic -> brainstormed product.

**Prior knowledge is withdrawn, explicitly and repeatedly.** The model certainly
knows a great deal about Docker. None of it is supplied by this packet, so none
of it may support a factual claim -- and this is the property the mission exists
to test, so the instruction is stated in the system region, restated in the task,
and checked deterministically afterwards by `validation.py` rather than trusted.

**No numeric confidence is requested**, in keeping with the standing invariant
that a self-reported certainty is not a probability.

**Every claim statement is `UntrustedText` in the runner.** The statements are
this repository's own sentences, but they contain source-derived values and the
region boundary is not something to relax because the text looks safe.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass

from .dimensions import DIMENSION_DEFINITIONS, EvidenceDimension
from .packet import OpportunityEvidencePacket

__all__ = [
    "SYNTHESIS_PROCEDURE_VERSION",
    "SYNTHESIS_PROMPT_VERSION",
    "SYNTHESIS_PROMPT_ID",
    "SYNTHESIS_SYSTEM",
    "SYNTHESIS_OUTPUT_SCHEMA",
    "MANDATORY_UNSUPPORTED_REPORT",
    "SynthesisPromptParts",
    "render_synthesis_prompt",
    "synthesis_prompt_hash",
]

SYNTHESIS_PROCEDURE_VERSION = "opportunity-synthesis@1.0.0"
SYNTHESIS_PROMPT_VERSION = "1.0.0"
SYNTHESIS_PROMPT_ID = "opportunity-synthesis"

#: §6. Dimensions the model must explicitly report on, whether or not the packet
#: supports them. Listing them makes the absence machine-readable instead of
#: leaving it to whether the model happened to mention one.
MANDATORY_UNSUPPORTED_REPORT: tuple[EvidenceDimension, ...] = (
    EvidenceDimension.RECURRENCE_OR_FREQUENCY,
    EvidenceDimension.ECONOMIC_VALUE,
    EvidenceDimension.WILLINGNESS_TO_PAY,
    EvidenceDimension.BUYER_OR_BUDGET_EXISTENCE,
    EvidenceDimension.MARKET_ACTIVITY,
    EvidenceDimension.SOLUTION_GAP,
    EvidenceDimension.SOLUTION_DISSATISFACTION,
    EvidenceDimension.COMPETITIVE_SUPPLY,
    EvidenceDimension.DISTRIBUTION_SIGNAL,
    EvidenceDimension.REGULATORY_OR_STRUCTURAL_DRIVER,
    EvidenceDimension.FEASIBILITY_SIGNAL,
)


SYNTHESIS_SYSTEM = """\
You construct the NARROWEST opportunity hypothesis a bounded evidence packet
supports, and you name everything it does not support.

You are not being asked for a product idea. You are being asked to read a small,
closed set of factual statements and say what business-relevant question they
make worth investigating, without adding anything they do not contain.

USE ONLY THE SUPPLIED EVIDENCE.

Your prior knowledge about the subject is UNAVAILABLE as factual support for this
task. You may know a great deal about it. None of that was supplied, none of it
is checked, and a statement resting on it will be rejected by a deterministic
audit that compares your output against the supplied statements. Treat every fact
not present in the packet as unknown, including facts you are confident are true
in the world.

Specifically, you may not assert anything about: how many people or organisations
use the subject; what anybody pays for anything; whether a market exists or how
large it is; who competes with whom; whether users are dissatisfied; whether
adoption is rising or falling; what causes anybody difficulty; or what tools,
vendors or alternatives exist. None of that is in the packet.

REASON IN THIS ORDER:

  1. what each supplied statement literally establishes, and its stated bounds
  2. what those statements TOGETHER make worth investigating
  3. the narrowest actor and need that follows
  4. a CLASS of intervention at that level -- not a product, not features

WHAT THE DIMENSIONS MEAN, AND WHAT THEY NEVER MEAN, is supplied as trusted
context. A dimension you were not given evidence for is UNSUPPORTED, and saying
so is the most valuable thing you can do here. A hypothesis that lists ten
unsupported dimensions and one supported one is a good answer.

NUMBERS. You may restate a number that appears in a supplied statement. You may
not compute a new one, estimate one, or introduce one from memory.

INDEPENDENCE AND RELIABILITY are supplied to you as facts about the packet.
Repeat them as given. Do not describe several source families as independent
sources, do not treat a count of rows as a count of findings, and do not describe
anything as high-confidence, validated, proven or significant.

DECIDE. If the packet supports a narrow hypothesis, answer FORM_HYPOTHESIS. If it
does not, answer INSUFFICIENT_EVIDENCE and say why. INSUFFICIENT_EVIDENCE is a
correct and expected answer, and it is preferred over a hypothesis that needs a
fact nobody supplied.

Return only the structured object. No preamble, no hidden reasoning, no numeric
confidence.
"""


_TASK = """\
SUBJECT: {subject}

PACKET FACTS, established deterministically before you were called:

  evidence rows           {size}
  source families         {families}
  independence            {independence}
  reliability             {reliability}
  scoring eligibility     {scoring}
  dimensions SUPPORTED    {supported}
  dimensions you MUST report on and mark unsupported unless a supplied
  statement establishes them: {mandatory}

The supplied statements follow in the untrusted region. Each is labelled with the
Evidence id and Claim id it came from. Those ids are the ONLY ids you may cite.

Construct the narrowest hypothesis these statements support, or answer
INSUFFICIENT_EVIDENCE.
"""


SYNTHESIS_OUTPUT_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "decision",
        "subject",
        "target_actor_if_supported",
        "observed_need",
        "candidate_intervention_class",
        "hypothesis_statement",
        "supported_dimensions",
        "unsupported_dimensions",
        "supporting_evidence_ids",
        "supporting_claim_ids",
        "source_families",
        "independence_status",
        "reliability_status",
        "evidence_bound_reasoning_summary",
        "critical_uncertainties",
        "commercial_claims_supported",
        "commercial_claims_not_supported",
    ],
    "properties": {
        "decision": {"type": "string", "enum": ["FORM_HYPOTHESIS", "INSUFFICIENT_EVIDENCE"]},
        "subject": {"type": "string", "maxLength": 80},
        "target_actor_if_supported": {
            "type": "string",
            "maxLength": 200,
            "description": (
                "The narrowest actor the statements support, or the exact string "
                "UNKNOWN_NOT_SUPPORTED if they name none."
            ),
        },
        "observed_need": {"type": "string", "maxLength": 400},
        "candidate_intervention_class": {"type": "string", "maxLength": 300},
        "hypothesis_statement": {"type": "string", "maxLength": 600},
        "supported_dimensions": {"type": "array", "items": {"type": "string"}, "maxItems": 14},
        "unsupported_dimensions": {"type": "array", "items": {"type": "string"}, "maxItems": 14},
        "supporting_evidence_ids": {"type": "array", "items": {"type": "string"}, "maxItems": 20},
        "supporting_claim_ids": {"type": "array", "items": {"type": "string"}, "maxItems": 20},
        "source_families": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
        "independence_status": {"type": "string", "maxLength": 300},
        "reliability_status": {"type": "string", "maxLength": 300},
        "evidence_bound_reasoning_summary": {"type": "string", "maxLength": 900},
        "critical_uncertainties": {"type": "array", "items": {"type": "string"}, "maxItems": 12},
        "commercial_claims_supported": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 8,
        },
        "commercial_claims_not_supported": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 14,
        },
    },
}


@dataclass(frozen=True)
class SynthesisPromptParts:
    """The prompt regions, kept apart. The runner builds the Gateway objects."""

    system_instructions: str
    trusted_context: str
    #: (content, label) pairs. Every one becomes `UntrustedText` in the runner.
    untrusted: tuple[tuple[str, str], ...]
    task: str
    metadata: dict[str, str]


def _dimension_reference(dimensions: tuple[EvidenceDimension, ...]) -> str:
    """The taxonomy's own questions and refusals, as trusted context.

    The `never_means` lines are the load-bearing half: they are what stops
    `AUDIENCE_OR_USAGE` being read as demand inside the model's own reasoning,
    and they are supplied rather than assumed because the model has no other way
    to know what this repository means by the word.
    """
    lines = []
    for dimension in dimensions:
        definition = DIMENSION_DEFINITIONS[dimension]
        lines.append(f"{dimension.value}")
        lines.append(f"  asks: {definition.question}")
        for never in definition.never_means:
            lines.append(f"  never means: {never}")
    return "\n".join(lines)


def render_synthesis_prompt(
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
) -> SynthesisPromptParts:
    """Build the prompt regions for one packet.

    `evidence_to_claim` is required rather than derived: the model may cite only
    ids it was given, and pairing each statement with BOTH ids is what lets the
    deterministic audit check that a cited pair actually belongs together.
    """
    supported = sorted(d.value for d in packet.counting_dimensions)
    mandatory = sorted(d.value for d in MANDATORY_UNSUPPORTED_REPORT if d not in packet.dimensions)

    trusted = "\n\n".join(
        (
            "DIMENSION REFERENCE. What each name asks, and what it never means.",
            _dimension_reference(
                tuple(sorted(packet.dimensions, key=lambda d: d.value))
                + MANDATORY_UNSUPPORTED_REPORT
            ),
            "SOURCE-BOUNDED MEANING of the measurements in this packet:",
            "\n\n".join(f"- {bound}" for bound in packet.dimension_bounds),
        )
    )

    untrusted: list[tuple[str, str]] = []
    for evidence_id in packet.evidence_ids:
        claim_id = evidence_to_claim.get(evidence_id, "")
        statement = claim_statements.get(claim_id, "")
        if not statement:
            continue
        untrusted.append((statement, f"evidence={evidence_id} claim={claim_id}"))

    task = _TASK.format(
        subject=packet.subject_label,
        size=packet.size,
        families=", ".join(packet.source_families),
        independence=packet.independence_summary(),
        reliability=(
            "every row is NON_SCORABLE with MISSING_RELIABILITY: no reviewed "
            "reliability applies to any of these measurements"
        ),
        scoring=(
            f"{packet.scoring_eligible_count} of {packet.size} rows are scoring-eligible; "
            "this packet cannot contribute to any score"
        ),
        supported=", ".join(supported),
        mandatory=", ".join(mandatory),
    )

    return SynthesisPromptParts(
        system_instructions=SYNTHESIS_SYSTEM,
        trusted_context=trusted,
        untrusted=tuple(untrusted),
        task=task,
        metadata={
            "procedure": SYNTHESIS_PROCEDURE_VERSION,
            "prompt_version": SYNTHESIS_PROMPT_VERSION,
            "packet_id": packet.packet_id,
        },
    )


def synthesis_prompt_hash() -> str:
    """sha256 over the system text, the task template and the output schema.

    A later run producing a different hash is running a different procedure,
    whatever its version string says -- the rule Mission 1.27 froze its candidate
    under, applied to the first production prompt.
    """
    return hashlib.sha256(
        (
            SYNTHESIS_SYSTEM
            + "\x00"
            + _TASK
            + "\x00"
            + json.dumps(SYNTHESIS_OUTPUT_SCHEMA, sort_keys=True)
        ).encode()
    ).hexdigest()
