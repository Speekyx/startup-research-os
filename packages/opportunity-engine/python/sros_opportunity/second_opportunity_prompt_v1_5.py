"""Prompt v1.5.0 of the second-Opportunity synthesis: v1.4.0 rebound to schema v1.2.0 and gate v1.4.0.

Mission 1.84.17. The operator moved one hard bound of the output contract in Mission 1.84.16 and
decided in 1.84.17 that schema v1.2.0 is the V6 execution contract, judged by gate v1.4.0. Prompt
v1.4.0 states schema v1.1.0's bounds, so it cannot be the V6 prompt. Version 1.5.0 rebuilds v1.4.0's
system region from the same pieces, in the same order, with the schema moved and nothing else:

* the output-contract block is rendered from schema v1.2.0 by the same renderer, with v1.2.0's notes,
  opening and closing sentences unchanged;
* the semantic-policy block is gate v1.3.0's census rendered exactly as before: gate v1.4.0 keeps
  every non-structural rule, and the block names no gate identity, so its bytes do not move;
* the generation-headroom block is rendered from schema v1.2.0 by the same renderer, policy objects,
  ratio and field roles.

So the only lines that move are the ones stating the reasoning summary's hard maximum and its
generation target, and both are read from schema v1.2.0: this module writes no number. The trusted
context with its SOURCE NAMES section, the untrusted region where the TED-derived statements sit, and
the task are v1.3.0's objects, which v1.4.0 also used, unchanged.

**Prompt v1.4.0 is not touched**, and neither is anything it rests on. V5's execution keeps resolving
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
from .output_constraints import (
    MUST_BE_EXPLICIT_IN_PROMPT,
    OUTPUT_CONSTRAINT_RENDERER_VERSION,
    constraint_inventory,
    is_explicit,
    render_output_constraints,
)
from .packet import OpportunityEvidencePacket
from .second_opportunity import (
    OUTPUT_CONSTRAINT_NOTES_V1_2,
    OUTPUT_CONTRACT_CLOSING,
    OUTPUT_CONTRACT_OPENING,
    SECOND_OPPORTUNITY_PROCEDURE_VERSION,
    SECOND_OPPORTUNITY_PROMPT_ID,
    SECOND_OPPORTUNITY_SYSTEM,
)
from .second_opportunity_gate_v1_4 import SECOND_OPPORTUNITY_GATE_VERSION_V1_4
from .second_opportunity_prompt_v1_3 import (
    SEMANTIC_GENERATION_RULES_BLOCK_V1_3,
    render_second_opportunity_prompt_v1_3,
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
    "SECOND_OPPORTUNITY_PROMPT_VERSION_V1_5",
    "PROMPT_V1_5_OUTPUT_SCHEMA",
    "PROMPT_V1_5_OUTPUT_SCHEMA_VERSION",
    "PROMPT_V1_5_SEMANTIC_GATE_VERSION",
    "OUTPUT_CONTRACT_BLOCK_V1_5",
    "SEMANTIC_GENERATION_RULES_BLOCK_V1_5",
    "GENERATION_HEADROOM_BLOCK_V1_5",
    "SECOND_OPPORTUNITY_SYSTEM_V1_5",
    "render_second_opportunity_prompt_v1_5",
    "second_opportunity_prompt_hash_v1_5",
    "unstated_constraints_in",
    "unstated_semantic_rules_in",
    "unstated_headroom_in",
]

SECOND_OPPORTUNITY_PROMPT_VERSION_V1_5 = "1.5.0"

#: What this prompt states and what judges the answer. Both are bound into the digest.
PROMPT_V1_5_OUTPUT_SCHEMA = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2
PROMPT_V1_5_OUTPUT_SCHEMA_VERSION = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2
PROMPT_V1_5_SEMANTIC_GATE_VERSION = SECOND_OPPORTUNITY_GATE_VERSION_V1_4

OUTPUT_CONTRACT_BLOCK_V1_5 = (
    OUTPUT_CONTRACT_OPENING
    + "\n\n"
    + render_output_constraints(PROMPT_V1_5_OUTPUT_SCHEMA, OUTPUT_CONSTRAINT_NOTES_V1_2)
    + "\n\n"
    + OUTPUT_CONTRACT_CLOSING
)

#: Gate v1.3.0's census, rendered as prompt v1.3.0 rendered it: gate v1.4.0 keeps every rule in it.
SEMANTIC_GENERATION_RULES_BLOCK_V1_5 = SEMANTIC_GENERATION_RULES_BLOCK_V1_3

GENERATION_HEADROOM_BLOCK_V1_5 = render_generation_headroom_block(PROMPT_V1_5_OUTPUT_SCHEMA)

SECOND_OPPORTUNITY_SYSTEM_V1_5 = (
    SECOND_OPPORTUNITY_SYSTEM
    + "\n"
    + OUTPUT_CONTRACT_BLOCK_V1_5
    + "\n"
    + "\n"
    + SEMANTIC_GENERATION_RULES_BLOCK_V1_5
    + "\n"
    + "\n"
    + GENERATION_HEADROOM_BLOCK_V1_5
    + "\n"
)


def render_second_opportunity_prompt_v1_5(
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
    *,
    source_metadata: SourceMetadataContext,
) -> SynthesisPromptParts:
    """The v1.5.0 regions: v1.3.0's trusted context, untrusted region and task, and the v1.5.0
    system region. `source_metadata` stays required, with no default channel."""
    base = render_second_opportunity_prompt_v1_3(
        packet, claim_statements, evidence_to_claim, source_metadata=source_metadata
    )
    return SynthesisPromptParts(
        system_instructions=SECOND_OPPORTUNITY_SYSTEM_V1_5,
        trusted_context=base.trusted_context,
        untrusted=base.untrusted,
        task=base.task,
        metadata={**base.metadata, "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_5},
    )


def second_opportunity_prompt_hash_v1_5(parts: SynthesisPromptParts) -> str:
    """The v1.5.0 digest: v1.4.0's fields over schema v1.2.0, plus the schema and gate identities."""
    payload = json.dumps(
        {
            "procedure": SECOND_OPPORTUNITY_PROCEDURE_VERSION,
            "prompt_id": SECOND_OPPORTUNITY_PROMPT_ID,
            "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_5,
            "output_constraint_renderer": OUTPUT_CONSTRAINT_RENDERER_VERSION,
            "semantic_generation_rules_renderer": SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
            "semantic_rule_census": SEMANTIC_RULE_CENSUS_VERSION,
            "source_label_block_renderer": SOURCE_LABEL_BLOCK_RENDERER_VERSION,
            "generation_headroom_renderer": GENERATION_HEADROOM_RENDERER_VERSION,
            "generation_headroom_policy": GENERATION_HEADROOM_POLICY_VERSION,
            "generation_target_ratio": GENERATION_HEADROOM_POLICY.ratio_text,
            "field_role_policy": FIELD_ROLE_POLICY_VERSION,
            "output_schema_version": PROMPT_V1_5_OUTPUT_SCHEMA_VERSION,
            "semantic_gate": PROMPT_V1_5_SEMANTIC_GATE_VERSION,
            "system_instructions": parts.system_instructions,
            "task": parts.task,
            "trusted_context": parts.trusted_context,
            "untrusted": [list(pair) for pair in parts.untrusted],
            "output_schema": PROMPT_V1_5_OUTPUT_SCHEMA,
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
        for c in constraint_inventory(PROMPT_V1_5_OUTPUT_SCHEMA)
        if c.constraint_class == MUST_BE_EXPLICIT_IN_PROMPT and not is_explicit(c, system)
    ]


def unstated_semantic_rules_in(parts: SynthesisPromptParts) -> list[str]:
    """Every class-A semantic rule these regions leave unstated."""
    return unstated_semantic_rules(parts.system_instructions, parts.trusted_context, parts.task)


def unstated_headroom_in(parts: SynthesisPromptParts) -> list[str]:
    """Every composed text whose v1.2.0 target and hard maximum the system region leaves unstated."""
    return unstated_headroom(parts.system_instructions, PROMPT_V1_5_OUTPUT_SCHEMA)
