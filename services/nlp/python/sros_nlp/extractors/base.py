"""What every deterministic extractor is, and the machinery all of them share.

`signal-derivation-runtime-v1.md` §3, §4, §6.

An extractor answers three questions and nothing else:

    group_key(observation)   which candidate group does this record belong to
    resolve(parameters)      what are my declared, output-affecting parameters
    derive(group)            what signals -- or what refusal -- comes out

**Grouping is what keeps this tractable.** Production extraction never compares
every record with every other record: a record whose key differs lands in a
different group and never meets the other. The refusal path exists for the
caller who hands an explicit pair anyway, which is exactly what the tests do.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sros_contracts import SignalRefusalReason
from sros_signal_model import (
    SignalDerivation,
    SignalDraft,
    canonical_json,
)

from ..observations import NormalizedObservation

__all__ = [
    "CandidateGroup",
    "DerivationRequest",
    "GroupOutcome",
    "GroupRefusal",
    "SignalExtractor",
    "group_key_of",
]


def group_key_of(fields: Sequence[tuple[str, object]]) -> str:
    """A canonical grouping key.

    Serialised rather than concatenated, so a value containing the separator
    cannot collide with a different grouping -- the escaping lesson the
    observation key learned in Mission 1.9.3, reached here by not building a
    delimited string in the first place.
    """
    return canonical_json(dict(fields))


@dataclass(frozen=True)
class CandidateGroup:
    """Records that MAY be derivable together, and nothing stronger.

    Membership says the grouping key matched. Whether the group actually yields
    a signal is `derive`'s answer, and a group of one is a perfectly ordinary
    outcome that is refused rather than treated as an error.
    """

    key: str
    observations: tuple[NormalizedObservation, ...]

    @property
    def observation_keys(self) -> tuple[str, ...]:
        return tuple(o.observation_key for o in self.observations)


@dataclass(frozen=True)
class GroupRefusal:
    """Why one candidate group produced no Signal.

    Written to `nlp.signal_derivation_runs`, never to `nlp.signals`: a row in a
    table of signals says a signal exists.
    """

    reason: SignalRefusalReason
    detail: str
    group_key: str
    observation_keys: tuple[str, ...] = ()

    def to_json(self) -> dict[str, object]:
        return {
            "reason": self.reason.value,
            "detail": self.detail,
            "group_key": self.group_key,
            "observation_keys": list(self.observation_keys),
        }


@dataclass(frozen=True)
class GroupOutcome:
    """What one group produced. Either drafts, or refusals, or both."""

    drafts: tuple[SignalDraft, ...] = ()
    refusals: tuple[GroupRefusal, ...] = ()


@dataclass(frozen=True)
class DerivationRequest:
    """The tenancy and retention facts a draft needs, and cannot choose.

    Shaped after `build_normalized`, which has no parameter for attribution or
    retention for the same reason: an extractor that could choose its own
    expiry would be setting its own retention policy.
    """

    workspace_id: str
    correlation_id: str
    derived_at: datetime
    expires_at: datetime
    research_session_id: str | None = None


class SignalExtractor(Protocol):
    """A deterministic derivation over canonical observations.

    Implementations must reach no network, no model and no clock beyond the one
    handed to them, and must produce byte-identical output for identical inputs,
    parameters and version.
    """

    extractor_id: str
    extractor_version: str
    signal_type_id: str
    record_kind_id: str

    def resolve(self, requested: Mapping[str, object]) -> SignalDerivation:
        """The derivation identity, with parameters resolved in ONE place.

        Raises `SignalRefusedError` with `PARAMETERS_INCOMPLETE` when a declared
        parameter was not supplied. There is no hidden default: a value that
        affects the output and is not stated makes the version number
        meaningless.
        """
        ...

    def group_key(self, observation: NormalizedObservation) -> str | None:
        """Which candidate group this record belongs to, or `None` to skip it."""
        ...

    def derive(
        self,
        group: CandidateGroup,
        derivation: SignalDerivation,
        request: DerivationRequest,
    ) -> GroupOutcome:
        """The signals this group yields, and the reasons it yields fewer."""
        ...
