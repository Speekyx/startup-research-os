"""Prompt v1.6.0 of the second-Opportunity synthesis: v1.5.0 with the generation-surface block.

Mission 1.84.23. The operator kept schema v1.2.0, gate v1.4.0, the strict architecture, the timeout,
the cost ceiling and the headroom, and decided to align generation with the bounded forms the gate
already reads rather than to move the gate. Version 1.6.0 is v1.5.0's system region, byte for byte,
followed by one block rendered from the generation-surface policy:

* which fields assert, and where a supported assertion's words may come from;
* that the class of intervention is such a field: naming only the class is not free vocabulary;
* what a request for evidence looks like as a phrase, that it is never an instruction, that it
  leaves its result open, and that it carries no wording of certainty or confirmation.

Everything else is v1.5.0's: the output-contract block, the semantic block, the headroom block, the
trusted context with its SOURCE NAMES section, the untrusted region and the task. This module writes
no number and reads no file.

**Prompt v1.5.0 is not touched**, and neither is anything it rests on. Every historical execution keeps
resolving against the prompt it sent.
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
    unstated_headroom,
)
from .generation_surface_policy import (
    GENERATION_SURFACE_POLICY_VERSION,
    GENERATION_SURFACE_RENDERER_VERSION,
    render_generation_surface_block,
    unstated_surface_rules,
)
from .output_constraints import (
    MUST_BE_EXPLICIT_IN_PROMPT,
    OUTPUT_CONSTRAINT_RENDERER_VERSION,
    constraint_inventory,
    is_explicit,
)
from .packet import OpportunityEvidencePacket
from .second_opportunity import SECOND_OPPORTUNITY_PROCEDURE_VERSION, SECOND_OPPORTUNITY_PROMPT_ID
from .second_opportunity_gate_v1_4 import SECOND_OPPORTUNITY_GATE_VERSION_V1_4
from .second_opportunity_prompt_v1_5 import (
    SECOND_OPPORTUNITY_SYSTEM_V1_5,
    render_second_opportunity_prompt_v1_5,
)
from .second_opportunity_schema_v1_2 import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
)
from .semantic_generation_rules import (
    SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
    SEMANTIC_RULE_CENSUS_VERSION,
    SOURCE_LABEL_BLOCK_RENDERER_VERSION,
    unstated_semantic_rules,
)
from .support_origin import SourceMetadataContext
from .synthesis import SynthesisPromptParts

__all__ = [
    "SECOND_OPPORTUNITY_PROMPT_VERSION_V1_6",
    "PROMPT_V1_6_OUTPUT_SCHEMA",
    "PROMPT_V1_6_OUTPUT_SCHEMA_VERSION",
    "PROMPT_V1_6_SEMANTIC_GATE_VERSION",
    "GENERATION_SURFACE_BLOCK_V1_6",
    "SECOND_OPPORTUNITY_SYSTEM_V1_6",
    "render_second_opportunity_prompt_v1_6",
    "second_opportunity_prompt_hash_v1_6",
    "unstated_constraints_in",
    "unstated_semantic_rules_in",
    "unstated_headroom_in",
    "unstated_surface_rules_in",
]

SECOND_OPPORTUNITY_PROMPT_VERSION_V1_6 = "1.6.0"

#: What this prompt states and what judges the answer: v1.5.0's, unchanged.
PROMPT_V1_6_OUTPUT_SCHEMA = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2
PROMPT_V1_6_OUTPUT_SCHEMA_VERSION = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2
PROMPT_V1_6_SEMANTIC_GATE_VERSION = SECOND_OPPORTUNITY_GATE_VERSION_V1_4

GENERATION_SURFACE_BLOCK_V1_6 = render_generation_surface_block()

#: v1.5.0's system region, byte for byte, then the surface block after one blank line.
SECOND_OPPORTUNITY_SYSTEM_V1_6 = (
    SECOND_OPPORTUNITY_SYSTEM_V1_5 + "\n" + GENERATION_SURFACE_BLOCK_V1_6 + "\n"
)


def render_second_opportunity_prompt_v1_6(
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
    *,
    source_metadata: SourceMetadataContext,
) -> SynthesisPromptParts:
    """The v1.6.0 regions: v1.5.0's trusted context, untrusted region and task, and the v1.6.0
    system region. `source_metadata` stays required, with no default channel."""
    base = render_second_opportunity_prompt_v1_5(
        packet, claim_statements, evidence_to_claim, source_metadata=source_metadata
    )
    return SynthesisPromptParts(
        system_instructions=SECOND_OPPORTUNITY_SYSTEM_V1_6,
        trusted_context=base.trusted_context,
        untrusted=base.untrusted,
        task=base.task,
        metadata={**base.metadata, "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_6},
    )


def second_opportunity_prompt_hash_v1_6(parts: SynthesisPromptParts) -> str:
    """The v1.6.0 digest: v1.5.0's fields, plus the surface policy and its renderer."""
    payload = json.dumps(
        {
            "procedure": SECOND_OPPORTUNITY_PROCEDURE_VERSION,
            "prompt_id": SECOND_OPPORTUNITY_PROMPT_ID,
            "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_6,
            "output_constraint_renderer": OUTPUT_CONSTRAINT_RENDERER_VERSION,
            "semantic_generation_rules_renderer": SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
            "semantic_rule_census": SEMANTIC_RULE_CENSUS_VERSION,
            "source_label_block_renderer": SOURCE_LABEL_BLOCK_RENDERER_VERSION,
            "generation_headroom_renderer": GENERATION_HEADROOM_RENDERER_VERSION,
            "generation_headroom_policy": GENERATION_HEADROOM_POLICY_VERSION,
            "generation_target_ratio": GENERATION_HEADROOM_POLICY.ratio_text,
            "field_role_policy": FIELD_ROLE_POLICY_VERSION,
            "generation_surface_policy": GENERATION_SURFACE_POLICY_VERSION,
            "generation_surface_renderer": GENERATION_SURFACE_RENDERER_VERSION,
            "output_schema_version": PROMPT_V1_6_OUTPUT_SCHEMA_VERSION,
            "semantic_gate": PROMPT_V1_6_SEMANTIC_GATE_VERSION,
            "system_instructions": parts.system_instructions,
            "task": parts.task,
            "trusted_context": parts.trusted_context,
            "untrusted": [list(pair) for pair in parts.untrusted],
            "output_schema": PROMPT_V1_6_OUTPUT_SCHEMA,
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def unstated_constraints_in(parts: SynthesisPromptParts) -> list[str]:
    """Every schema v1.2.0 constraint the prompt must state and the system region leaves unstated."""
    system = str(parts.system_instructions)
    return [
        f"{c.path} {c.keyword}"
        for c in constraint_inventory(PROMPT_V1_6_OUTPUT_SCHEMA)
        if c.constraint_class == MUST_BE_EXPLICIT_IN_PROMPT and not is_explicit(c, system)
    ]


def unstated_semantic_rules_in(parts: SynthesisPromptParts) -> list[str]:
    """Every class-A semantic rule these regions leave unstated."""
    return unstated_semantic_rules(parts.system_instructions, parts.trusted_context, parts.task)


def unstated_headroom_in(parts: SynthesisPromptParts) -> list[str]:
    """Every composed text whose v1.2.0 target and hard maximum the system region leaves unstated."""
    return unstated_headroom(parts.system_instructions, PROMPT_V1_6_OUTPUT_SCHEMA)


def unstated_surface_rules_in(parts: SynthesisPromptParts) -> list[str]:
    """Every generation-surface rule the system region leaves unstated."""
    return unstated_surface_rules(parts.system_instructions)
