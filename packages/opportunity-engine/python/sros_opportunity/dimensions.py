"""The evidence-dimension taxonomy, versioned.

Mission 1.28 §3. A dimension names **a question an opportunity hypothesis needs
answered**, so that "we have evidence" can never again be a single undifferentiated
word. Fourteen questions, and the current corpus answers two of them.

**A dimension is not a score and not a weight.** It carries no number, no
ordering and no importance. `WILLINGNESS_TO_PAY` is not worth more than
`AUDIENCE_OR_USAGE`; it is a different question. Mission 1.28 §15 forbids the
arithmetic that would make one worth more than another, and giving a dimension a
coefficient here is how that arithmetic would arrive without an ADR.

**Every dimension states what it never means.** That is the whole reason this
module is more than an enum. The repository's standing failure mode is an
interpretation acquiring the status of a fact one layer at a time -- a pageview
becoming a reader, a term count becoming a want, a published contract total
becoming a price somebody paid. `never_means` puts the refusal beside the
definition, where a person adding a mapping has to read it.

The taxonomy is `opportunity-evidence-dimensions@1.0.0`. Adding, removing or
redefining a member is a version bump, because a stored packet names the version
it was built under and a silently redefined dimension makes an old packet mean
something nobody wrote.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

__all__ = [
    "DIMENSION_TAXONOMY_VERSION",
    "COMMERCIAL_DIMENSIONS",
    "EvidenceDimension",
    "DimensionDefinition",
    "DIMENSION_DEFINITIONS",
    "define",
]

DIMENSION_TAXONOMY_VERSION = "opportunity-evidence-dimensions@1.0.0"


class EvidenceDimension(enum.Enum):
    """What question a piece of evidence bears on.

    Closed for this version. A source observation that fits none of these maps
    to the empty set, which is a legitimate and common answer -- see
    `mapping.py`, where four of the five implemented signal types map to fewer
    than two members and one maps to none at all.
    """

    PROBLEM_OR_NEED = "PROBLEM_OR_NEED"
    RECURRENCE_OR_FREQUENCY = "RECURRENCE_OR_FREQUENCY"
    ECONOMIC_VALUE = "ECONOMIC_VALUE"
    WILLINGNESS_TO_PAY = "WILLINGNESS_TO_PAY"
    BUYER_OR_BUDGET_EXISTENCE = "BUYER_OR_BUDGET_EXISTENCE"
    MARKET_ACTIVITY = "MARKET_ACTIVITY"
    TREND_OR_CHANGE = "TREND_OR_CHANGE"
    SOLUTION_GAP = "SOLUTION_GAP"
    SOLUTION_DISSATISFACTION = "SOLUTION_DISSATISFACTION"
    COMPETITIVE_SUPPLY = "COMPETITIVE_SUPPLY"
    AUDIENCE_OR_USAGE = "AUDIENCE_OR_USAGE"
    DISTRIBUTION_SIGNAL = "DISTRIBUTION_SIGNAL"
    REGULATORY_OR_STRUCTURAL_DRIVER = "REGULATORY_OR_STRUCTURAL_DRIVER"
    FEASIBILITY_SIGNAL = "FEASIBILITY_SIGNAL"


#: The dimensions that carry a commercial assertion. Mission 1.28 §11 forbids a
#: hypothesis from asserting any of these unless eligible evidence maps to that
#: exact dimension, and `guards.py` enforces it over the vocabulary rather than
#: over intent. Kept as data here so the guard and the taxonomy cannot disagree.
COMMERCIAL_DIMENSIONS = frozenset(
    {
        EvidenceDimension.ECONOMIC_VALUE,
        EvidenceDimension.WILLINGNESS_TO_PAY,
        EvidenceDimension.BUYER_OR_BUDGET_EXISTENCE,
        EvidenceDimension.MARKET_ACTIVITY,
        EvidenceDimension.COMPETITIVE_SUPPLY,
    }
)


@dataclass(frozen=True)
class DimensionDefinition:
    """One dimension, its question, and the readings it forbids."""

    dimension: EvidenceDimension
    question: str
    #: Interpretations this dimension must never be read as licensing. Required
    #: and non-empty: a dimension with no stated over-reading is a dimension
    #: nobody thought about, and the over-readings are the failure mode.
    never_means: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.question.strip():
            raise ValueError(f"{self.dimension.value}: question is required")
        if not self.never_means:
            raise ValueError(
                f"{self.dimension.value}: never_means is required and may not be empty. "
                "A dimension with no stated over-reading is one nobody has thought "
                "about, and the over-readings are what this taxonomy exists to stop."
            )


def define(dimension: EvidenceDimension, question: str, *never_means: str) -> DimensionDefinition:
    return DimensionDefinition(dimension, question, tuple(never_means))


_D = EvidenceDimension

DIMENSION_DEFINITIONS: dict[EvidenceDimension, DimensionDefinition] = {
    definition.dimension: definition
    for definition in (
        define(
            _D.PROBLEM_OR_NEED,
            "Is there evidence that some actor is blocked, burdened or unserved?",
            "that the actor would pay to have it removed",
            "that the problem is frequent",
            "that the actor is a buyer",
        ),
        define(
            _D.RECURRENCE_OR_FREQUENCY,
            "Is there evidence the same problem or need arises repeatedly?",
            "that the same PERSON met it twice -- a repeated observation of a "
            "stream is not a repeated observation of a user (Mission 1.19 §0)",
            "that recurrence implies severity",
        ),
        define(
            _D.ECONOMIC_VALUE,
            "Is there evidence that money moves in the bounded activity observed?",
            "that the money would move toward a new product",
            "that the observed amount is a price",
            "that the amount was paid rather than published",
        ),
        define(
            _D.WILLINGNESS_TO_PAY,
            "Is there evidence a specific actor paid, or committed to pay, for "
            "something addressing this need?",
            "a listed price, which is an ask and not a transaction",
            "a budget line, which is a capacity and not a decision",
            "a public contract total, which includes options and renewals and "
            "may be lawfully withheld (Mission 1.15.12)",
        ),
        define(
            _D.BUYER_OR_BUDGET_EXISTENCE,
            "Is there evidence that an actor with authority to buy exists in this space?",
            "that the buyer would buy THIS",
            "how many such buyers there are",
            "what any of them would pay",
        ),
        define(
            _D.MARKET_ACTIVITY,
            "Is there evidence of transactions, tenders or commercial exchange in "
            "the bounded scope observed?",
            "market SIZE, which no observation here measures",
            "growth",
            "that the activity is unmet by existing supply",
        ),
        define(
            _D.TREND_OR_CHANGE,
            "Is there evidence that a measured quantity moved between two "
            "observations of the same source stream?",
            "that the movement will continue",
            "that the movement was caused by anything in particular",
            "that a movement in attention is a movement in demand",
        ),
        define(
            _D.SOLUTION_GAP,
            "Is there evidence that no adequate solution exists for the need?",
            "that a gap is an opportunity",
            "that absence of evidence of a solution is evidence of its absence",
        ),
        define(
            _D.SOLUTION_DISSATISFACTION,
            "Is there evidence that actors are dissatisfied with what they use today?",
            "that they would switch",
            "that a complaint is representative",
        ),
        define(
            _D.COMPETITIVE_SUPPLY,
            "Is there evidence about who already serves this need?",
            "that competitors are weak",
            "that a crowded space is closed or an empty one is open",
        ),
        define(
            _D.AUDIENCE_OR_USAGE,
            "Is there evidence that people or systems attend to, or use, the subject?",
            "that an attender is a customer",
            "that a request is a reader -- the operator's own requester "
            "classification is heuristic (Mission 1.19)",
            "that attention to a topic is intent to buy anything",
        ),
        define(
            _D.DISTRIBUTION_SIGNAL,
            "Is there evidence of a reachable channel through which such actors could be served?",
            "that the channel is available to us",
            "that reach implies conversion",
        ),
        define(
            _D.REGULATORY_OR_STRUCTURAL_DRIVER,
            "Is there evidence of a rule, mandate or structural condition that "
            "forces or shapes the activity?",
            "that a mandate creates a budget",
            "that a driver names a product",
        ),
        define(
            _D.FEASIBILITY_SIGNAL,
            "Is there evidence bearing on whether an intervention could be built and operated?",
            "that feasible means worth doing",
            "an estimate of cost or effort",
        ),
    )
}
