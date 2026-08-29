"""Turning persisted evidence rows into aggregation inputs.

Mission 1.2 §47. The reference engine must be able to aggregate evidence that
came out of the database, or the specification is only ever tested against
hand-built objects and nothing proves the persisted model actually feeds it.

**This module imports no database driver and knows no SQL.** It maps a
documented dict shape — the one `EvidenceRepository.list_for_claim` returns — to
`EvidenceItem`. The dependency runs one way and only at the seam: the gateway
does not import this package, and this package does not import the gateway. A
test wires the two together, which is what keeps an uncalibrated engine out of
every production path (ADR-014, Mission 1.2 §39).

The mapping is deliberately strict. A row missing `claim_id` or `direction` is
an error rather than a defaulted value: those are the two fields that decide
what a record is evidence *for* and *which way it points*, and guessing either
would silently move a record into the wrong aggregation.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from sros_contracts import (
    EvidenceDirection,
    EvidenceIndependenceState,
    EvidenceObservationCategory,
)

from .errors import AggregationError
from .items import EvidenceItem

__all__ = ["evidence_item_from_row", "evidence_items_from_rows", "UNKNOWN_GROUP_PLACEHOLDER"]

# What the engine substitutes when a stored record says UNKNOWN. Storage keeps
# the record's group id NULL -- an unresolved question must not look resolved in
# the database (Mission 1.2 §18) -- and the conservative single-bucket grouping
# happens at runtime, inside `group_by_independence`.
UNKNOWN_GROUP_PLACEHOLDER = None


def _required(row: Mapping[str, Any], key: str) -> Any:
    if key not in row or row[key] is None:
        raise AggregationError(
            f"evidence row is missing {key!r}. Aggregation cannot infer it: "
            "claim_id decides what the record is evidence FOR, and direction decides "
            "which way it points"
        )
    return row[key]


def _optional_unit(row: Mapping[str, Any], key: str) -> float | None:
    """A missing factor stays missing.

    Not 0.5, not 0.0. `evaluate_item` will mark the record NON_SCORABLE and name
    the field, which is the behaviour the framework requires (§6). Substituting
    anything here would defeat it at the boundary.
    """
    value = row.get(key)
    return None if value is None else float(value)


def evidence_item_from_row(row: Mapping[str, Any]) -> EvidenceItem:
    """Map one persisted evidence row to an aggregation input.

    `EvidenceItem.__post_init__` re-validates the independence shape, so an
    inconsistent row raises here even though the database CHECK constraint
    should already have refused to store it. Two checks on one rule, because
    the rows may one day arrive from somewhere other than that table.
    """
    state = EvidenceIndependenceState(row.get("independence_state") or "UNKNOWN")
    group_id = row.get("independence_group_id")

    return EvidenceItem(
        evidence_id=str(_required(row, "evidence_id")),
        direction=EvidenceDirection(_required(row, "direction")),
        relevance=_optional_unit(row, "relevance"),
        directness=_optional_unit(row, "directness"),
        reliability=_optional_unit(row, "reliability"),
        extraction_confidence=_optional_unit(row, "extraction_confidence"),
        observation_category=EvidenceObservationCategory(
            row.get("observation_category") or "UNCATEGORISED"
        ),
        independence_state=state,
        # Only a KNOWN_DEPENDENT record carries one. The other two states must
        # not, and the model refuses the combination outright.
        independence_group_id=(
            str(group_id)
            if state is EvidenceIndependenceState.KNOWN_DEPENDENT and group_id
            else None
        ),
        observed_at=row.get("observed_at"),
        source_id=row.get("source_id"),
        source_family=row.get("source_family"),
    )


def evidence_items_from_rows(rows: Iterable[Mapping[str, Any]]) -> list[EvidenceItem]:
    """Map a claim's whole evidence set.

    Order is preserved but carries no meaning: aggregation is order-independent
    by construction and a test asserts it end to end.
    """
    return [evidence_item_from_row(row) for row in rows]
