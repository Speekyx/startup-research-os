"""Which registered resource produced this measurement? Answered from lineage, or not at all.

Mission 1.77. The reliability scope is five facts and the resolver matches all five or
none (ADR-026). Four of them are read off the Claim and the Evidence row. The fifth, the
RESOURCE, is not a proposition fact -- ADR-035 and ADR-036 keep it out of proposition
identity for every kind that converges -- and it is not a column on the Signal either.
It is a persisted acquisition fact: every RawRecord carries `provenance.resource_id`,
written by the collector from the dataset the authorization context authorised, four
gates before any socket, and `nlp.signal_inputs` names the RawRecords a Signal was derived
from.

So the question has one honest answer and this module states the rule once:

    the resource of a measurement is the ONE distinct `resource_id` carried by the
    RawRecords its Signal was derived from. Zero distinct values, or more than one,
    is not a resource -- it is a lineage that cannot say, and no scope is built.

Nothing here names a source, reads a collector, reads the registry or consults an
assessment. A caller that knows a resource from anywhere else -- a collector constant, the
assessment it hopes to match, the only registered resource for the source -- has not
established which resource produced the measurement; it has guessed, and this function
gives it nowhere to put the guess.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from sros_contracts import ClaimType

from .model import ReliabilityScope

__all__ = [
    "BASIS_ABSENT",
    "BASIS_AMBIGUOUS",
    "BASIS_EXPLICIT",
    "LineageScope",
    "scope_from_lineage",
]

#: The resource was read from persisted acquisition provenance reachable through the
#: Signal's inputs. The only basis under which a scope is built.
BASIS_EXPLICIT = "EXPLICIT_PERSISTED_RESOURCE"
#: The reachable RawRecords carry more than one distinct resource, or more than one record
#: kind. Refused rather than picked: a scope chosen from an ambiguous lineage would apply an
#: assessment reviewed for one measurement to a row that may be another.
BASIS_AMBIGUOUS = "NONE_LINEAGE_AMBIGUOUS"
#: The lineage cannot supply a scope fact at all: no reachable RawRecord carries a
#: resource, no signal input names a record kind, or the Claim names no proposition kind.
BASIS_ABSENT = "NONE_LINEAGE_ABSENT"


class LineageScope:
    """The scope built from lineage, and the basis it was built on -- or why it was not."""

    __slots__ = ("basis", "scope")

    def __init__(self, scope: ReliabilityScope | None, basis: str) -> None:
        if (scope is None) == (basis == BASIS_EXPLICIT):
            raise ValueError("a scope is built exactly when the basis is explicit")
        self.scope = scope
        self.basis = basis


def scope_from_lineage(
    *,
    source_id: str,
    claim_type: ClaimType,
    proposition_facts: Mapping[str, object],
    lineage_resource_ids: Iterable[str | None],
    lineage_record_kind_ids: Iterable[str | None],
) -> LineageScope:
    """Build the five-part scope from what the lineage persisted, or refuse.

    `lineage_resource_ids` and `lineage_record_kind_ids` are the values carried by the
    RawRecords and signal-input rows reachable from the Evidence row's Signal. Duplicates
    are fine; what matters is how many DISTINCT non-empty values there are.
    """
    resources = sorted({r for r in lineage_resource_ids if isinstance(r, str) and r.strip()})
    kinds = sorted({k for k in lineage_record_kind_ids if isinstance(k, str) and k.strip()})
    if not resources or not kinds:
        return LineageScope(None, BASIS_ABSENT)
    if len(resources) != 1 or len(kinds) != 1:
        return LineageScope(None, BASIS_AMBIGUOUS)
    kind = proposition_facts.get("proposition")
    if not isinstance(kind, str) or not kind.strip() or not source_id.strip():
        return LineageScope(None, BASIS_ABSENT)
    return LineageScope(
        ReliabilityScope(
            source_id=source_id,
            resource_id=resources[0],
            record_kind_id=kinds[0],
            claim_type=claim_type,
            proposition_kind=kind,
        ),
        BASIS_EXPLICIT,
    )
