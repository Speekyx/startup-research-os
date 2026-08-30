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

from .facts import LEXICAL_FREQUENCY_OBSERVATION, NUMERIC_OBSERVATION

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
    }
)


def record_kind_for(family: SignalQuantityFamily) -> str:
    return _FAMILY_RECORD_KIND[family]


# Extractors that exist. EMPTY: Mission 1.11 defines the model and stops there,
# and `nlp.signals` holds 0 rows. Mission 1.11.1 is where this stops being empty.
SIGNAL_EXTRACTORS: Mapping[str, str] = MappingProxyType({})
