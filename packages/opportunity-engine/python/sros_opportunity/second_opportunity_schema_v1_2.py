"""Output schema v1.2.0 of the second-Opportunity synthesis: v1.1.0 with one bound moved by the operator.

Mission 1.84.16. The operator changed exactly one hard bound of the output contract,
`evidence_bound_reasoning_summary.maxLength`. The basis is the operator's semantic budget for a field
with three responsibilities: what the supplied evidence establishes, why the candidate stays
exploratory, and the most important evidence boundary. It is a judgement, not a measurement: no
historical answer's length set it, and nothing here derives it.

Schema v1.1.0 is not touched. `second_opportunity.py` stays byte-identical, so every historical
execution keeps resolving against the contract it used. This module deep-copies v1.1.0 and moves one
number, and `semantic_schema_diff` is how anyone checks that one number is all that moved.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from .second_opportunity import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
)

__all__ = [
    "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2",
    "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2",
    "REASONING_SUMMARY_FIELD",
    "EVIDENCE_BOUND_REASONING_SUMMARY_HARD_MAX",
    "REASONING_SUMMARY_DECISION_BASIS",
    "PREDECESSOR_SCHEMA_VERSION",
    "MISSING",
    "semantic_schema_diff",
    "output_schema_sha256",
]

SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2 = "second-opportunity-synthesis-output@1.2.0"
PREDECESSOR_SCHEMA_VERSION = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1

REASONING_SUMMARY_FIELD = "evidence_bound_reasoning_summary"

#: The operator's number (Mission 1.84.16, section 0). A semantic budget, owned by the operator.
EVIDENCE_BOUND_REASONING_SUMMARY_HARD_MAX = 1500
REASONING_SUMMARY_DECISION_BASIS = "OPERATOR_SEMANTIC_BUDGET"

#: The marker for a key or element one side of a diff does not have.
MISSING = "<absent>"


def _successor() -> dict[str, object]:
    schema: dict[str, Any] = copy.deepcopy(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    field = schema["properties"][REASONING_SUMMARY_FIELD]
    if not isinstance(field.get("maxLength"), int):
        raise ValueError(f"{REASONING_SUMMARY_FIELD} carries no integer bound in the predecessor")
    field["maxLength"] = EVIDENCE_BOUND_REASONING_SUMMARY_HARD_MAX
    return schema


SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2: dict[str, object] = _successor()


def _walk(old: object, new: object, path: tuple[str, ...]) -> list[tuple[str, object, object]]:
    if isinstance(old, Mapping) and isinstance(new, Mapping):
        out: list[tuple[str, object, object]] = []
        for key in sorted(set(old) | set(new)):
            here = (*path, str(key))
            if key not in old:
                out.append((".".join(here), MISSING, new[key]))
            elif key not in new:
                out.append((".".join(here), old[key], MISSING))
            else:
                out.extend(_walk(old[key], new[key], here))
        return out
    if isinstance(old, list) and isinstance(new, list):
        out = []
        for index in range(max(len(old), len(new))):
            here = (*path, f"[{index}]")
            if index >= len(old):
                out.append((".".join(here), MISSING, new[index]))
            elif index >= len(new):
                out.append((".".join(here), old[index], MISSING))
            else:
                out.extend(_walk(old[index], new[index], here))
        return out
    if type(old) is not type(new) or old != new:
        return [(".".join(path), old, new)]
    return []


def semantic_schema_diff(
    old: Mapping[str, object], new: Mapping[str, object]
) -> list[tuple[str, object, object]]:
    """Every leaf where two schemas differ, as (dotted path, old value, new value), sorted by path.

    Every keyword counts, descriptions included: a reworded description is a difference too, and a
    diff that skipped prose could not say that one number is all that moved. A key or element one
    side lacks is reported against `MISSING`. `True` and `1` differ, because the type is compared.
    """
    return _walk(old, new, ())


def output_schema_sha256(schema: Mapping[str, object]) -> str:
    """The repository's schema digest: sha256 over the schema serialized with sorted keys."""
    return hashlib.sha256(json.dumps(schema, sort_keys=True).encode("utf-8")).hexdigest()
