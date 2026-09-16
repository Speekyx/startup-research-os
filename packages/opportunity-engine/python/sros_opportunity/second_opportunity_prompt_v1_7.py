"""Prompt v1.7.0 of the second-Opportunity synthesis: schema v1.3.0, gate v1.6.0 and the generation contract.

Mission 1.84.27, operator decisions D3 and D5. Prompt v1.6.0 cannot be the prompt of schema v1.3.0: it
states schema v1.2.0's contract, it binds gate v1.4.0, and its surface block tells the model to name a
more neutral class wherever a richer one needs an unsupplied concept, which is the pressure D3 removes.

Version 1.7.0 rebuilds the system region from the same pieces, in the same order, as v1.5.0 did, and
then appends one block, as v1.6.0 did:

* the synthesis system text, v1.3.0's census block and the trusted context, untrusted region and task
  are the objects every earlier version used, unchanged;
* the output-contract block and the generation-headroom block are rendered from schema v1.3.0 by the
  same renderers with the same notes. The one line that moves is the class field's, which now states
  the schema's own sentinel, read from its description; no number moves;
* the generation-surface block is replaced by the generation-contract block
  (`second-opportunity-generation-contract-policy@1.0.0`): the class of intervention's absence and
  grounding (D3), what an answer asserts and what it only names (D5), and the surface policy's own
  request section, unchanged.

This module writes no number and reads no file. **Prompts v1.5.0 and v1.6.0 are not touched**, and
neither is anything they rest on.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from .generation_contract_policy import (
    GENERATION_CONTRACT_POLICY_VERSION,
    GENERATION_CONTRACT_RENDERER_VERSION,
    render_generation_contract_block,
    unstated_contract_rules,
)
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
from .second_opportunity_gate_v1_6 import SECOND_OPPORTUNITY_GATE_VERSION_V1_6
from .second_opportunity_prompt_v1_3 import (
    SEMANTIC_GENERATION_RULES_BLOCK_V1_3,
    render_second_opportunity_prompt_v1_3,
)
from .second_opportunity_schema_v1_3 import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_3,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_3,
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
    "SECOND_OPPORTUNITY_PROMPT_VERSION_V1_7",
    "PROMPT_V1_7_OUTPUT_SCHEMA",
    "PROMPT_V1_7_OUTPUT_SCHEMA_VERSION",
    "PROMPT_V1_7_SEMANTIC_GATE_VERSION",
    "OUTPUT_CONTRACT_BLOCK_V1_7",
    "SEMANTIC_GENERATION_RULES_BLOCK_V1_7",
    "GENERATION_HEADROOM_BLOCK_V1_7",
    "GENERATION_CONTRACT_BLOCK_V1_7",
    "SECOND_OPPORTUNITY_SYSTEM_V1_7",
    "render_second_opportunity_prompt_v1_7",
    "second_opportunity_prompt_hash_v1_7",
    "unstated_constraints_in",
    "unstated_semantic_rules_in",
    "unstated_headroom_in",
    "unstated_contract_rules_in",
]

SECOND_OPPORTUNITY_PROMPT_VERSION_V1_7 = "1.7.0"

#: What this prompt states and what judges the answer. Both are bound into the digest.
PROMPT_V1_7_OUTPUT_SCHEMA = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_3
PROMPT_V1_7_OUTPUT_SCHEMA_VERSION = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_3
PROMPT_V1_7_SEMANTIC_GATE_VERSION = SECOND_OPPORTUNITY_GATE_VERSION_V1_6

OUTPUT_CONTRACT_BLOCK_V1_7 = (
    OUTPUT_CONTRACT_OPENING
    + "\n\n"
    + render_output_constraints(PROMPT_V1_7_OUTPUT_SCHEMA, OUTPUT_CONSTRAINT_NOTES_V1_2)
    + "\n\n"
    + OUTPUT_CONTRACT_CLOSING
)

#: Gate v1.3.0's census, rendered as prompt v1.3.0 rendered it: gate v1.6.0 keeps every rule in it.
SEMANTIC_GENERATION_RULES_BLOCK_V1_7 = SEMANTIC_GENERATION_RULES_BLOCK_V1_3

GENERATION_HEADROOM_BLOCK_V1_7 = render_generation_headroom_block(PROMPT_V1_7_OUTPUT_SCHEMA)

GENERATION_CONTRACT_BLOCK_V1_7 = render_generation_contract_block()

SECOND_OPPORTUNITY_SYSTEM_V1_7 = (
    SECOND_OPPORTUNITY_SYSTEM
    + "\n"
    + OUTPUT_CONTRACT_BLOCK_V1_7
    + "\n"
    + "\n"
    + SEMANTIC_GENERATION_RULES_BLOCK_V1_7
    + "\n"
    + "\n"
    + GENERATION_HEADROOM_BLOCK_V1_7
    + "\n"
    + "\n"
    + GENERATION_CONTRACT_BLOCK_V1_7
    + "\n"
)


def render_second_opportunity_prompt_v1_7(
    packet: OpportunityEvidencePacket,
    claim_statements: Mapping[str, str],
    evidence_to_claim: Mapping[str, str],
    *,
    source_metadata: SourceMetadataContext,
) -> SynthesisPromptParts:
    """The v1.7.0 regions: v1.3.0's trusted context, untrusted region and task, and the v1.7.0
    system region. `source_metadata` stays required, with no default channel."""
    base = render_second_opportunity_prompt_v1_3(
        packet, claim_statements, evidence_to_claim, source_metadata=source_metadata
    )
    return SynthesisPromptParts(
        system_instructions=SECOND_OPPORTUNITY_SYSTEM_V1_7,
        trusted_context=base.trusted_context,
        untrusted=base.untrusted,
        task=base.task,
        metadata={**base.metadata, "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_7},
    )


def second_opportunity_prompt_hash_v1_7(parts: SynthesisPromptParts) -> str:
    """The v1.7.0 digest: v1.5.0's fields over schema v1.3.0 and gate v1.6.0, plus the contract policy."""
    payload = json.dumps(
        {
            "procedure": SECOND_OPPORTUNITY_PROCEDURE_VERSION,
            "prompt_id": SECOND_OPPORTUNITY_PROMPT_ID,
            "prompt_version": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_7,
            "output_constraint_renderer": OUTPUT_CONSTRAINT_RENDERER_VERSION,
            "semantic_generation_rules_renderer": SEMANTIC_GENERATION_RULES_RENDERER_VERSION,
            "semantic_rule_census": SEMANTIC_RULE_CENSUS_VERSION,
            "source_label_block_renderer": SOURCE_LABEL_BLOCK_RENDERER_VERSION,
            "generation_headroom_renderer": GENERATION_HEADROOM_RENDERER_VERSION,
            "generation_headroom_policy": GENERATION_HEADROOM_POLICY_VERSION,
            "generation_target_ratio": GENERATION_HEADROOM_POLICY.ratio_text,
            "field_role_policy": FIELD_ROLE_POLICY_VERSION,
            "generation_contract_policy": GENERATION_CONTRACT_POLICY_VERSION,
            "generation_contract_renderer": GENERATION_CONTRACT_RENDERER_VERSION,
            "output_schema_version": PROMPT_V1_7_OUTPUT_SCHEMA_VERSION,
            "semantic_gate": PROMPT_V1_7_SEMANTIC_GATE_VERSION,
            "system_instructions": parts.system_instructions,
            "task": parts.task,
            "trusted_context": parts.trusted_context,
            "untrusted": [list(pair) for pair in parts.untrusted],
            "output_schema": PROMPT_V1_7_OUTPUT_SCHEMA,
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def unstated_constraints_in(parts: SynthesisPromptParts) -> list[str]:
    """Every schema v1.3.0 constraint the prompt must state and the system region leaves unstated."""
    system = str(parts.system_instructions)
    return [
        f"{c.path} {c.keyword}"
        for c in constraint_inventory(PROMPT_V1_7_OUTPUT_SCHEMA)
        if c.constraint_class == MUST_BE_EXPLICIT_IN_PROMPT and not is_explicit(c, system)
    ]


def unstated_semantic_rules_in(parts: SynthesisPromptParts) -> list[str]:
    """Every class-A semantic rule these regions leave unstated."""
    return unstated_semantic_rules(parts.system_instructions, parts.trusted_context, parts.task)


def unstated_headroom_in(parts: SynthesisPromptParts) -> list[str]:
    """Every composed text whose v1.3.0 target and hard maximum the system region leaves unstated."""
    return unstated_headroom(parts.system_instructions, PROMPT_V1_7_OUTPUT_SCHEMA)


def unstated_contract_rules_in(parts: SynthesisPromptParts) -> list[str]:
    """Every generation-contract rule the system region leaves unstated."""
    return unstated_contract_rules(parts.system_instructions)
