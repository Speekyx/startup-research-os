"""The registered signal types, and the fact that no extractor implements one.

`signal-taxonomy-v1.md` §4. Two entries, each justified by records this
repository currently holds -- Mission 1.11 §35 asks for a small extensible V1
and forbids eighty speculative types.

**A registered type is vocabulary, not code.** The same distinction Mission 1.10
drew for record kinds: a registry row lets the model describe a shape and lets
the database refuse a type nobody registered; the claim that code EXISTS is
`SIGNAL_EXTRACTORS`, and it is empty.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from sros_contracts import SignalQuantityFamily

from .facts import (
    COMMUNITY_QUESTION,
    CONTENT_REQUEST_COUNT,
    LEXICAL_FREQUENCY_OBSERVATION,
    NUMERIC_OBSERVATION,
    PROCUREMENT_NOTICE,
)

__all__ = [
    "SIGNAL_EXTRACTORS",
    "SIGNAL_TYPES",
    "SIGNAL_TYPE_REGISTRY",
    "SignalTypeSpec",
    "record_kind_for",
]

# Ontology V2 §14.3: an evolving taxonomy is registry rows, not a database enum.
# NOT `demand_signal_type`, which the table defaulted to and which classifies
# demand -- see `signal-taxonomy-v1.md` §2.
SIGNAL_TYPE_REGISTRY = "signal_type"


@dataclass(frozen=True)
class SignalTypeSpec:
    """A registered type: its family, and what its data shape has to be."""

    id: str
    family: SignalQuantityFamily
    summary: str


SIGNAL_TYPES: Mapping[str, SignalTypeSpec] = MappingProxyType(
    {
        "lexical_frequency_contrast": SignalTypeSpec(
            id="lexical_frequency_contrast",
            family=SignalQuantityFamily.LEXICAL_FREQUENCY,
            summary=(
                "The relation between the frequencies of two or more lexical terms observed "
                "under one identical source period label and one identical source language "
                "label. Says how often tokens occurred in text the source processed, and "
                "nothing about attention, interest or demand."
            ),
        ),
        "lexical_frequency_change": SignalTypeSpec(
            id="lexical_frequency_change",
            family=SignalQuantityFamily.LEXICAL_FREQUENCY,
            summary=(
                "The change in one lexical term's source-measured frequency between two "
                "ADJACENT source buckets of one publication stream, under one source "
                "language label and one gram size. Requires a reviewed temporal order "
                "certification; the buckets are ordered relative to each other and are "
                "NOT placed on any shared timeline. Says the measured frequency "
                "differed, and nothing about attention, interest, demand or trend."
            ),
        ),
        "procurement_value_contrast": SignalTypeSpec(
            id="procurement_value_contrast",
            family=SignalQuantityFamily.TRANSACTION_VALUE,
            summary=(
                "The spread of the values at which several comparable procurement "
                "transactions settled, within one source. Every member shares an amount "
                "semantic, a scope, a currency, a notice class and a procurement "
                "classification. NON-TEMPORAL: nothing here is ordered, compared across "
                "periods or read as a trend. Says what several buyers paid; says nothing "
                "about demand, about what a product could charge, or about willingness to "
                "pay."
            ),
        ),
        # Mission 1.19, ADR-032.
        "content_request_change": SignalTypeSpec(
            id="content_request_change",
            family=SignalQuantityFamily.CONTENT_REQUEST_VOLUME,
            summary=(
                "The change in one content item's request count between two ADJACENT "
                "periods of one platform's own publication, under one requester class and "
                "one access channel. Both members are the SAME item, so every item-level "
                "confounder cancels exactly. The CALENDAR does not, and neither do news "
                "events: a weekday-to-weekend difference is a difference in the calendar, "
                "which makes an INFERENCE from this signal unsound rather than the "
                "subtraction untrue. Says a platform counted a different number of "
                "requests on two adjacent periods; says nothing about readers, users, "
                "customers, interest, demand, adoption, popularity, a trend or a market."
            ),
        ),
        # Mission 1.30, ADR-034.
        "community_question_volume": SignalTypeSpec(
            id="community_question_volume",
            family=SignalQuantityFamily.COMMUNITY_QUESTION_VOLUME,
            summary=(
                "How many public questions carrying one tag from a community site's own "
                "vocabulary were created on that site inside one bounded window, counted "
                "over records this deployment holds. NON-TEMPORAL as a relation: nothing "
                "is ordered, compared across periods or read as a trend -- it is one "
                "count over one window, and a second window would be a second signal "
                "rather than a change. Complete only where the retrieval demonstrably "
                "did not truncate, which the derivation must establish and refuses "
                "without. Says people published that many questions filed under that "
                "tag; says nothing about how many PEOPLE (author identity is never "
                "acquired), nothing about whether the questions share a problem (the "
                "relation Mission 1.27 parked), and nothing about severity, recurrence, "
                "difficulty, demand, adoption, a market or willingness to pay."
            ),
        ),
        # Mission 1.32. Same family as the volume type: still a count of
        # community questions, so no new family is warranted.
        "community_question_without_accepted_answer_volume": SignalTypeSpec(
            id="community_question_without_accepted_answer_volume",
            family=SignalQuantityFamily.COMMUNITY_QUESTION_VOLUME,
            summary=(
                "How many public questions carrying one tag from a community site's own "
                "vocabulary, created inside one bounded window, had NO ACCEPTED ANSWER at "
                "the source state this deployment observed. Acceptance is one person's "
                "action -- only the asker may accept -- and the state is read whenever the "
                "record was collected, which may be long after the question was written. "
                "Says that many askers had not marked an answer accepted when we looked. "
                "Says NOTHING about whether any problem is solved, whether anyone is "
                "dissatisfied, whether existing tools are adequate, whether a solution "
                "gap exists, whether anyone would pay, or whether any two of the questions "
                "concern the same problem -- that last being the relation Mission 1.27 "
                "PARKED. A record carrying no flag WITHHOLDS the fact and is never counted "
                "as unaccepted."
            ),
        ),
        "numeric_period_change": SignalTypeSpec(
            id="numeric_period_change",
            family=SignalQuantityFamily.MEASURED_SERIES,
            summary=(
                "The change in one metric, for one geography, between two periods placed on a "
                "common timeline. A measurement moved; whether that is a market event is a "
                "later stage's question."
            ),
        ),
    }
)

# The record kind each family reads. A family whose inputs are of the other kind
# is INCOMPATIBLE_INPUT_KINDS: a lexical signal reading a geography would be
# reading a key that is not there.
_FAMILY_RECORD_KIND: Mapping[SignalQuantityFamily, str] = MappingProxyType(
    {
        SignalQuantityFamily.LEXICAL_FREQUENCY: LEXICAL_FREQUENCY_OBSERVATION,
        SignalQuantityFamily.MEASURED_SERIES: NUMERIC_OBSERVATION,
        # Mission 1.15.9, ADR-029. A transaction value reads a procurement
        # notice, which carries an amount semantic and a currency and no metric.
        SignalQuantityFamily.TRANSACTION_VALUE: PROCUREMENT_NOTICE,
        # Mission 1.19, ADR-032. A content request count carries an item, a
        # platform and a requester class, and no metric and no geography.
        SignalQuantityFamily.CONTENT_REQUEST_VOLUME: CONTENT_REQUEST_COUNT,
        # Mission 1.30, ADR-034. A question volume reads community questions,
        # which carry a site tag list and a creation instant and no measured
        # value at all.
        SignalQuantityFamily.COMMUNITY_QUESTION_VOLUME: COMMUNITY_QUESTION,
    }
)


def record_kind_for(family: SignalQuantityFamily) -> str:
    return _FAMILY_RECORD_KIND[family]


# Extractors that exist. EMPTY: Mission 1.11 defines the model and stops there,
# and `nlp.signals` holds 0 rows. Mission 1.11.1 is where this stops being empty.
SIGNAL_EXTRACTORS: Mapping[str, str] = MappingProxyType({})
