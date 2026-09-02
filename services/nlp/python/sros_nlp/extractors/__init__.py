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

`lexical-frequency-change` (Mission 1.12.1) is the third, and the first whose
window basis is `ORDERED_PERIODS`. It exists only because Mission 1.12 closed
H-32 on GDELT's own evidence, and it asks the certification rather than
inferring order from a label's shape.
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
from .community_question_volume import CommunityQuestionVolumeExtractor
from .community_question_without_accepted_answer import (
    CommunityQuestionWithoutAcceptedAnswerExtractor,
)
from .content_request_change import ContentRequestChangeExtractor
from .lexical_frequency_change import LexicalFrequencyChangeExtractor
from .lexical_frequency_contrast import LexicalFrequencyContrastExtractor
from .numeric_period_change import NumericPeriodChangeExtractor
from .procurement_value_contrast import ProcurementValueContrastExtractor

__all__ = [
    "EXTRACTOR_REGISTRY",
    "IMPLEMENTED_EXTRACTORS",
    "CandidateGroup",
    "ContentRequestChangeExtractor",
    "DerivationRequest",
    "GroupOutcome",
    "GroupRefusal",
    "LexicalFrequencyChangeExtractor",
    "LexicalFrequencyContrastExtractor",
    "NumericPeriodChangeExtractor",
    "ProcurementValueContrastExtractor",
    "SignalExtractor",
    "group_key_of",
    "select_extractor",
]

_NUMERIC = NumericPeriodChangeExtractor()
_LEXICAL = LexicalFrequencyContrastExtractor()
_LEXICAL_CHANGE = LexicalFrequencyChangeExtractor()
# Mission 1.15.9, ADR-029. The first derivation over a `procurement_notice`, and
# the first in the TRANSACTION_VALUE family.
_PROCUREMENT = ProcurementValueContrastExtractor()
# Mission 1.19, ADR-032. The first derivation over a `content_request_count`,
# and the first in the CONTENT_REQUEST_VOLUME family.
_CONTENT_REQUEST = ContentRequestChangeExtractor()
# Mission 1.30, ADR-034. The first derivation over a `community_question` --
# a record kind that had existed since Mission 1.18 with nothing able to read
# it -- and the first in the COMMUNITY_QUESTION_VOLUME family.
_QUESTION_VOLUME = CommunityQuestionVolumeExtractor()
# Mission 1.32. The second derivation over a `community_question`, reading a
# field Mission 1.18 stored and nothing had ever read.
_QUESTION_UNACCEPTED = CommunityQuestionWithoutAcceptedAnswerExtractor()

EXTRACTOR_REGISTRY: Mapping[str, SignalExtractor] = MappingProxyType(
    {
        _NUMERIC.extractor_id: _NUMERIC,
        _LEXICAL.extractor_id: _LEXICAL,
        _LEXICAL_CHANGE.extractor_id: _LEXICAL_CHANGE,
        _PROCUREMENT.extractor_id: _PROCUREMENT,
        _CONTENT_REQUEST.extractor_id: _CONTENT_REQUEST,
        _QUESTION_VOLUME.extractor_id: _QUESTION_VOLUME,
        _QUESTION_UNACCEPTED.extractor_id: _QUESTION_UNACCEPTED,
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
