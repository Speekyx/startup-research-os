"""The signal extractor registry.

`signal-derivation-runtime-v1.md`. Two entries, and both are deterministic.

**A registered extractor is CODE**, and that is what separates this table from
`SIGNAL_TYPES` in `sros_signal_model`, which is vocabulary. Mission 1.10 drew
the same line between a record kind and a normalizer; Mission 1.11 registered
two signal types with no extractor behind them, and this is the mission that
fills them in.

No `trend`, `growth`, `momentum`, `demand`, `pain`, `desire`, `attention`,
`sentiment` or `topic` extractor exists. Each of those names a conclusion rather
than an operation, and none is derivable from the data this system holds.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from .base import (
    CandidateGroup,
    DerivationRequest,
    GroupOutcome,
    GroupRefusal,
    SignalExtractor,
    group_key_of,
)
from .lexical_frequency_contrast import LexicalFrequencyContrastExtractor
from .numeric_period_change import NumericPeriodChangeExtractor

__all__ = [
    "EXTRACTOR_REGISTRY",
    "IMPLEMENTED_EXTRACTORS",
    "CandidateGroup",
    "DerivationRequest",
    "GroupOutcome",
    "GroupRefusal",
    "LexicalFrequencyContrastExtractor",
    "NumericPeriodChangeExtractor",
    "SignalExtractor",
    "group_key_of",
    "select_extractor",
]

_NUMERIC = NumericPeriodChangeExtractor()
_LEXICAL = LexicalFrequencyContrastExtractor()

EXTRACTOR_REGISTRY: Mapping[str, SignalExtractor] = MappingProxyType(
    {
        _NUMERIC.extractor_id: _NUMERIC,
        _LEXICAL.extractor_id: _LEXICAL,
    }
)

# What a planner reads to decide whether signal derivation can run at all. The
# counterpart of `IMPLEMENTED_NORMALIZERS`, and it names extractors rather than
# sources because an extractor reads a RECORD KIND, not a platform.
IMPLEMENTED_EXTRACTORS: frozenset[str] = frozenset(EXTRACTOR_REGISTRY)


def select_extractor(extractor_id: str) -> SignalExtractor | None:
    """The extractor with this id, or `None`.

    Fails closed: an unknown id is never handed to whichever extractor happens
    to exist, the same rule `select_normalizer` follows one layer down.
    """
    return EXTRACTOR_REGISTRY.get(extractor_id)
