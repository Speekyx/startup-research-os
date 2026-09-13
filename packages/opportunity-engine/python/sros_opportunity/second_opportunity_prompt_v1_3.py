"""Prompt v1.3.0 of the second-Opportunity synthesis: v1.2.0, plus the gate's semantic rules.

Mission 1.84.12. Prompt v1.2.0 stated every bound the v1.1.0 schema enforces and none of the
semantic rules gate v1.3.0 applies. Version 1.3.0 adds exactly two things and changes nothing else:

* the SYSTEM region gains the semantic-policy block `semantic_generation_rules` renders from
  first-class policy objects, appended after v1.2.0's system region, which stays a byte-identical
  prefix, output-contract block included;
* the TRUSTED CONTEXT region gains a SOURCE NAMES section listing the registry names that occur in
  the supplied statements, appended after v1.2.0's trusted context, which stays a byte-identical
  prefix.

The untrusted region, where the TED-derived statements sit, and the task are v1.2.0's objects
unchanged, so the factual content the model receives is byte-identical and the approved
representation does not move. Every string the SOURCE NAMES section adds already occurs in those
statements; it tells the model which of their words are a name.

**Prompt v1.2.0 is not touched.** `second_opportunity.py` is pinned by digest as a historical module,
and V3's execution keeps resolving against the prompt it sent.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from .output_constraints import OUTPUT_CONSTRAINT_RENDERER_VERSION
from .packet import OpportunityEvidencePacket
from .second_opportunity import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_PROCEDURE_VERSION,
    SECOND_OPPORTUNITY_PROMPT_ID,
    SECOND_OPPORTUNITY_SYSTEM_V1_2,
    render_second_opportunity_prompt_v1_2,
)
from .semantic_generation_rules import (
    SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
    SEMANTIC_RULE_CENSUS_VERSION,
    SOURCE_LABEL_BLOCK_RENDERER_VERSION,
    render_semantic_generation_rules,
    render_source_label_block,
    unstated_semantic_rules,
)
from .support_origin import SourceMetadataContext
from .synthesis import SynthesisPromptParts

__all__ = [
    "SECOND_OPPORTUNITY_PROMPT_VERSION_V1_3",
    "SEMANTIC_GENERATION_RULES_BLOCK_V1_3",
    "SECOND_OPPORTUNITY_SYSTEM_V1_3",
    "render_second_opportunity_prompt_v1_3",
    "second_opportunity_prompt_hash_v1_3",
    "unstated_semantic_rules_in",
]

SECOND_OPPORTUNITY_PROMPT_VERSION_V1_3 = "1.3.0"

SEMANTIC_GENERATION_RULES_BLOCK_V1_3 = render_semantic_generation_rules()

SECOND_OPPORTUNITY_SYSTEM_V1_3 = (
    SECOND_OPPORTUNITY_SYSTEM_V1_2 + "\n" + SEMANTIC_GENERATION_RULES_BLOCK_V1_3 + "\n"
)


def render_second_opportunity_prompt_v1_3(
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
    *,
    source_metadata: SourceMetadataContext,
) -> SynthesisPromptParts:
    """The v1.3.0 regions. `source_metadata` is required: there is no default channel, because a
    default is where a source's name would reach the model as content."""
    base = render_second_opportunity_prompt_v1_2(packet, claim_statements, evidence_to_claim)
    names = render_source_label_block(packet, claim_statements, source_metadata)
    return SynthesisPromptParts(
        system_instructions=SECOND_OPPORTUNITY_SYSTEM_V1_3,
        trusted_context=base.trusted_context + "\n\n" + names,
        untrusted=base.untrusted,
        task=base.task,
        metadata={**base.metadata, "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_3},
    )


def second_opportunity_prompt_hash_v1_3(parts: SynthesisPromptParts) -> str:
    """The v1.3.0 digest: v1.2.0's fields, plus the semantic renderers and the census version.

    Each renderer's version is bound as well as its output, so a change to how rules or names are
    rendered moves the digest even where it leaves this packet's text alone.
    """
    payload = json.dumps(
        {
            "procedure": SECOND_OPPORTUNITY_PROCEDURE_VERSION,
            "prompt_id": SECOND_OPPORTUNITY_PROMPT_ID,
            "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_3,
            "output_constraint_renderer": OUTPUT_CONSTRAINT_RENDERER_VERSION,
            "semantic_generation_rules_renderer": SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
            "semantic_rule_census": SEMANTIC_RULE_CENSUS_VERSION,
            "source_label_block_renderer": SOURCE_LABEL_BLOCK_RENDERER_VERSION,
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


def unstated_semantic_rules_in(parts: SynthesisPromptParts) -> list[str]:
    """Every class-A semantic rule these regions leave unstated. Empty for prompt v1.3.0."""
    return unstated_semantic_rules(parts.system_instructions, parts.trusted_context, parts.task)
