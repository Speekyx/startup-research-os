"""Mapping an Evidence row to evidence dimensions, deterministically.

Mission 1.28 §3. The procedure is `signal-type-dimension-map@1.0.0` and it maps
from the **signal type** an Evidence row was derived through, because that is
what fixes the measurement's meaning. Not from the source: `world-bank` could
publish an indicator that maps somewhere and one that maps nowhere, and mapping
by publisher would give both the same answer.

**Zero dimensions is a real answer and is the answer twice here.** Two of the
five implemented signal types map to nothing at all, each for a stated reason.
The brief permits zero; this module treats it as the default and requires a
positive argument for every member it adds.

Three rules govern every entry, and they are the reason this file is prose as
much as data.

**A mapping preserves the source-bounded meaning.** A Wikimedia pageview change
is a change in requests for one article, and it does not become "demand
increased". A GDELT lexical change is a change in how often a term appeared in a
news stream, and it does not become "customers want this". A TED award total is a
published figure including options and renewals, and it does not become
willingness to pay for anything. Each of those is written as a `bound` on the
mapping, carried onto the packet, and no consumer can read the dimension without
it.

**`TREND_OR_CHANGE` never counts toward evidence diversity.** In this repository
a Signal *is* a derivation over two or more observations
(`docs/CLAUDE.md` §Signal), so **every** Evidence row here describes a change by
construction. A dimension the whole corpus carries separates nothing, and letting
it satisfy a two-dimension requirement would mean one measurement, repeated,
could look like two kinds of evidence. It is a qualifier on another dimension,
and `COUNTING_DIMENSIONS` excludes it.

**A mapping is not a promotion.** Mapping to `MARKET_ACTIVITY` says the evidence
bears on that question. It says nothing about how strongly, and nothing about
whether the evidence is scorable -- that is `eligibility.py`, and every row in
the current corpus fails it.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dimensions import EvidenceDimension

__all__ = [
    "DIMENSION_MAP_VERSION",
    "COUNTING_DIMENSIONS",
    "SignalDimensionMapping",
    "SIGNAL_DIMENSION_MAP",
    "map_signal_type",
    "counting_dimensions",
]

DIMENSION_MAP_VERSION = "signal-type-dimension-map@1.0.0"

#: Dimensions that count toward the §12 diversity requirement.
#:
#: **`TREND_OR_CHANGE` is deliberately excluded.** See the module docstring: it
#: is a property of the derivation shape rather than of the subject, and every
#: Evidence row in this repository has it. `sufficiency.py` counts over this set,
#: and `mission-1.28-report.md` reports the result under both readings, because
#: the exclusion is decisive for the current corpus and was chosen with that
#: corpus visible.
COUNTING_DIMENSIONS = frozenset(EvidenceDimension) - {EvidenceDimension.TREND_OR_CHANGE}


@dataclass(frozen=True)
class SignalDimensionMapping:
    """What one signal type bears on, and what it must never be read as saying."""

    signal_type_id: str
    dimensions: frozenset[EvidenceDimension]
    #: Why these dimensions and not others. Required.
    rationale: str
    #: The source-bounded meaning that travels with the dimensions. Required
    #: whenever any dimension is assigned: a dimension detached from the
    #: sentence that bounds it is the interpretation-becoming-fact failure this
    #: whole layer exists to prevent.
    bound: str = ""

    def __post_init__(self) -> None:
        if not self.rationale.strip():
            raise ValueError(f"{self.signal_type_id}: rationale is required")
        if self.dimensions and not self.bound.strip():
            raise ValueError(
                f"{self.signal_type_id}: a mapping that assigns dimensions must state "
                "the source-bounded meaning that travels with them"
            )
        if self.dimensions == {EvidenceDimension.TREND_OR_CHANGE}:
            raise ValueError(
                f"{self.signal_type_id}: TREND_OR_CHANGE may not stand alone. Every "
                "Signal in this repository is a derivation over two or more "
                "observations, so change is universal here and on its own it "
                "identifies nothing about an opportunity."
            )


_D = EvidenceDimension

SIGNAL_DIMENSION_MAP: dict[str, SignalDimensionMapping] = {
    m.signal_type_id: m
    for m in (
        SignalDimensionMapping(
            signal_type_id="content_request_change",
            dimensions=frozenset({_D.AUDIENCE_OR_USAGE, _D.TREND_OR_CHANGE}),
            rationale=(
                "A count of requests for one named item is evidence that something "
                "attends to that subject, which is what AUDIENCE_OR_USAGE asks. It is "
                "not evidence of a problem, of a buyer, or of money: nothing in a "
                "request count names any of those. TREND_OR_CHANGE rides along "
                "because the signal is a day-over-day difference, and does not count "
                "toward diversity."
            ),
            bound=(
                "A count of HTTP requests for one encyclopedia article on one wiki in "
                "one day, under the platform's own requester class. A request is not a "
                "reader: the operator documents its own automated-traffic "
                "classification as heuristic. Adjacent days do not cancel the "
                "calendar, and both larger articles in the Mission 1.19 sample fall "
                "about 40 per cent across a weekend."
            ),
        ),
        SignalDimensionMapping(
            signal_type_id="procurement_value_contrast",
            dimensions=frozenset(
                {_D.MARKET_ACTIVITY, _D.BUYER_OR_BUDGET_EXISTENCE, _D.ECONOMIC_VALUE}
            ),
            rationale=(
                "A contract award notice is a public record that a procuring body "
                "ran a procedure and awarded a contract, which is MARKET_ACTIVITY in "
                "the bounded scope, BUYER_OR_BUDGET_EXISTENCE because such a body "
                "demonstrably exists and had authority to award, and ECONOMIC_VALUE "
                "because a monetary figure was published for that activity. "
                "**WILLINGNESS_TO_PAY is deliberately absent**: it is the mapping a "
                "reader most wants and the one the source does not support."
            ),
            bound=(
                "Published award totals for a bounded set of notices in one CPV "
                "division. eForms BT-161 is the value of all contracts awarded in the "
                "notice INCLUDING OPTIONS AND RENEWALS -- not money paid, not "
                "necessarily one supplier, not realised expenditure, and not a price. "
                "It may be lawfully withheld under BT-195 to BT-198, so any cohort "
                "covers the published subset only and no proportion may be computed "
                "from it. It is not willingness to pay for a SaaS product, or for any "
                "product."
            ),
        ),
        SignalDimensionMapping(
            signal_type_id="numeric_period_change",
            dimensions=frozenset(),
            rationale=(
                "UNMAPPED, and the reason is that the signal type is the wrong "
                "granularity here. What a period change over an economic series bears "
                "on depends entirely on WHICH indicator moved: a series of business "
                "registrations and a series of total population are the same signal "
                "type and different evidence. No reviewed indicator-to-dimension map "
                "exists, and inventing one for the two indicators this deployment "
                "happens to hold would be a taxonomy fitted to a sample. The only "
                "indicator present is SP.POP.TOTL, a demographic stock that names no "
                "actor, no need, no buyer and no activity."
            ),
        ),
        SignalDimensionMapping(
            signal_type_id="lexical_frequency_change",
            dimensions=frozenset(),
            rationale=(
                "UNMAPPED. A change in how often a term appears in a news corpus "
                "measures what media organisations published, which is producer "
                "behaviour and not audience behaviour -- so it is not "
                "AUDIENCE_OR_USAGE, whose question is about who attends. The standing "
                "invariant is stronger than a caution: GDELT lexical frequency alone "
                "never satisfies a demand claim, not weakly, not with low relevance "
                "and not with a caveat. No dimension in this taxonomy asks about media "
                "publication volume, and adding one to give this source somewhere to "
                "land would be adding a dimension to fit a source."
            ),
        ),
        SignalDimensionMapping(
            signal_type_id="lexical_frequency_contrast",
            dimensions=frozenset(),
            rationale=(
                "UNMAPPED, for the same reason as lexical_frequency_change. A "
                "within-bucket contrast between two terms compares two things "
                "journalists wrote, and the comparison being internally sound does not "
                "make it evidence about a market."
            ),
        ),
    )
}


def map_signal_type(signal_type_id: str | None) -> SignalDimensionMapping | None:
    """The mapping for a signal type, or None where the type is unregistered.

    **None is not the empty mapping.** An unregistered signal type means nobody
    has decided what it bears on, and a caller must treat it as REQUIRES_REVIEW
    rather than as evidence bearing on nothing. A registered type mapping to
    `frozenset()` is a decision somebody made and wrote a rationale for.
    """
    if signal_type_id is None:
        return None
    return SIGNAL_DIMENSION_MAP.get(signal_type_id)


def counting_dimensions(
    dimensions: frozenset[EvidenceDimension],
) -> frozenset[EvidenceDimension]:
    """The subset that may satisfy a diversity requirement."""
    return dimensions & COUNTING_DIMENSIONS
