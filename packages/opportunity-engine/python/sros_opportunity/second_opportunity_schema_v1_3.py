"""Output schema v1.3.0 of the second-Opportunity synthesis: v1.2.0 with the class of intervention's absence.

Mission 1.84.27, operator decision D3. Schema v1.2.0 gives `candidate_intervention_class` a type and a
hard maximum and nothing else, so an answer has no way to say that the supplied statements establish no
class of intervention: every answer that forms a hypothesis has to write one. Its sibling
`target_actor_if_supported` has always had a way out, the exact string `UNKNOWN_NOT_SUPPORTED`, which
the audits already read as asserting nothing.

This successor gives the class the same first-class absence, in the same words, and states in the
field's own description what an established class is made of. **Exactly one leaf moves**: the field's
`description`. The type, the hard maximum, the required list and every other field are v1.2.0's, so
the local validator and the strict projection treat both schemas the same way everywhere else, and the
description is where the output-contract renderer finds a sentinel it must state.

Schema v1.2.0 is not touched. `second_opportunity_schema_v1_2.py` and everything before it stay byte
for byte, so every historical execution keeps resolving against the contract it used.
"""

from __future__ import annotations

import copy
from typing import Any

from .second_opportunity_schema_v1_2 import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
)

__all__ = [
    "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_3",
    "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_3",
    "PREDECESSOR_SCHEMA_VERSION",
    "INTERVENTION_CLASS_FIELD",
    "INTERVENTION_CLASS_NOT_ESTABLISHED",
    "INTERVENTION_CLASS_DESCRIPTION",
]

SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_3 = "second-opportunity-synthesis-output@1.3.0"
PREDECESSOR_SCHEMA_VERSION = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2

INTERVENTION_CLASS_FIELD = "candidate_intervention_class"

#: The one representation of "no class of intervention is established". The contract's existing
#: sentinel, so one absence token serves every field that has one.
INTERVENTION_CLASS_NOT_ESTABLISHED = "UNKNOWN_NOT_SUPPORTED"

INTERVENTION_CLASS_DESCRIPTION = (
    "The class of intervention the supplied statements establish, as one short noun phrase whose "
    "words the statements of the cited claims use, or the exact string "
    f"{INTERVENTION_CLASS_NOT_ESTABLISHED} if they establish none."
)


def _successor() -> dict[str, object]:
    schema: dict[str, Any] = copy.deepcopy(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
    field = schema["properties"][INTERVENTION_CLASS_FIELD]
    if "description" in field:
        raise ValueError(
            f"{INTERVENTION_CLASS_FIELD} already carries a description in the predecessor"
        )
    field["description"] = INTERVENTION_CLASS_DESCRIPTION
    return schema


SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_3: dict[str, object] = _successor()
