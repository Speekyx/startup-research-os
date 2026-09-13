"""Prompt v1.4.0 of the second-Opportunity synthesis: v1.3.0, plus generation headroom and field roles.

Mission 1.84.14. Prompt v1.3.0 stated every hard bound of the v1.1.0 schema and every class-A rule of
semantic gate v1.3.0, and execution V4, sent under it, was refused on two of those hard bounds. The
operator kept the schema and the gate and chose a generation policy. Version 1.4.0 adds exactly one
block and changes nothing else:

* the SYSTEM region gains the generation-headroom block `generation_headroom` renders from the live
  schema and the operator's policy objects, appended after v1.3.0's system region, which stays a
  byte-identical prefix: the output-contract block, the semantic-policy block and every word before
  them;
* the trusted context, with its SOURCE NAMES section, the untrusted region, where the TED-derived
  statements sit, and the task are v1.3.0's, unchanged.

**Prompt v1.3.0 is not touched**, and neither is anything it rests on. V4's execution keeps resolving
against the prompt it sent.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from .generation_headroom import (
    FIELD_ROLE_POLICY_VERSION,
    GENERATION_HEADROOM_POLICY,
    GENERATION_HEADROOM_POLICY_VERSION,
    GENERATION_HEADROOM_RENDERER_VERSION,
    render_generation_headroom_block,
    unstated_headroom,
)
from .output_constraints import OUTPUT_CONSTRAINT_RENDERER_VERSION
from .packet import OpportunityEvidencePacket
from .second_opportunity import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_PROCEDURE_VERSION,
    SECOND_OPPORTUNITY_PROMPT_ID,
)
from .second_opportunity_prompt_v1_3 import (
    SECOND_OPPORTUNITY_SYSTEM_V1_3,
    render_second_opportunity_prompt_v1_3,
)
from .semantic_generation_rules import (
    SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
    SEMANTIC_RULE_CENSUS_VERSION,
    SOURCE_LABEL_BLOCK_RENDERER_VERSION,
)
from .support_origin import SourceMetadataContext
from .synthesis import SynthesisPromptParts

__all__ = [
    "SECOND_OPPORTUNITY_PROMPT_VERSION_V1_4",
    "GENERATION_HEADROOM_BLOCK_V1_4",
    "SECOND_OPPORTUNITY_SYSTEM_V1_4",
    "render_second_opportunity_prompt_v1_4",
    "second_opportunity_prompt_hash_v1_4",
    "unstated_headroom_in",
]

SECOND_OPPORTUNITY_PROMPT_VERSION_V1_4 = "1.4.0"

GENERATION_HEADROOM_BLOCK_V1_4 = render_generation_headroom_block(
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
)

SECOND_OPPORTUNITY_SYSTEM_V1_4 = (
    SECOND_OPPORTUNITY_SYSTEM_V1_3 + "\n" + GENERATION_HEADROOM_BLOCK_V1_4 + "\n"
)


def render_second_opportunity_prompt_v1_4(
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
    *,
    source_metadata: SourceMetadataContext,
) -> SynthesisPromptParts:
    """The v1.4.0 regions: v1.3.0's, with the headroom block appended to the system region."""
    base = render_second_opportunity_prompt_v1_3(
        packet, claim_statements, evidence_to_claim, source_metadata=source_metadata
    )
    return SynthesisPromptParts(
        system_instructions=SECOND_OPPORTUNITY_SYSTEM_V1_4,
        trusted_context=base.trusted_context,
        untrusted=base.untrusted,
        task=base.task,
        metadata={**base.metadata, "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_4},
    )


def second_opportunity_prompt_hash_v1_4(parts: SynthesisPromptParts) -> str:
    """The v1.4.0 digest: v1.3.0's fields, plus the headroom renderer, policy, ratio and roles."""
    payload = json.dumps(
        {
            "procedure": SECOND_OPPORTUNITY_PROCEDURE_VERSION,
            "prompt_id": SECOND_OPPORTUNITY_PROMPT_ID,
            "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_4,
            "output_constraint_renderer": OUTPUT_CONSTRAINT_RENDERER_VERSION,
            "semantic_generation_rules_renderer": SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
            "semantic_rule_census": SEMANTIC_RULE_CENSUS_VERSION,
            "source_label_block_renderer": SOURCE_LABEL_BLOCK_RENDERER_VERSION,
            "generation_headroom_renderer": GENERATION_HEADROOM_RENDERER_VERSION,
            "generation_headroom_policy": GENERATION_HEADROOM_POLICY_VERSION,
            "generation_target_ratio": GENERATION_HEADROOM_POLICY.ratio_text,
            "field_role_policy": FIELD_ROLE_POLICY_VERSION,
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


def unstated_headroom_in(parts: SynthesisPromptParts) -> list[str]:
    """Every composed text whose target and hard maximum the system region leaves unstated."""
    return unstated_headroom(parts.system_instructions, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
