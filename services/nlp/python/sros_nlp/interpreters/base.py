"""What every deterministic claim interpreter is, and the shared machinery.

`claim-interpretation-runtime-v1.md` §3. Mission 1.13.1.

An interpreter answers two questions and nothing else:

    supports(signal_type_id)   is there a template for this kind of Signal
    interpret(signal)          what proposition -- or what refusal -- comes out

**The interpreter computes; `sros_claim_model` checks.** The same division
`signal-derivation-runtime-v1.md` §3 draws one layer down: an extractor reads
payloads and subtracts, the model validates what comes back. Here a template
reads a `SignalView` and renders a sentence and a fact set; `build_claim`
decides whether the result may be stored. Neither does the other's job, and
`packages/claim-model` still contains no template.

**Nothing here reaches a network, a model or an embedder.** A template is a
literal in this package applied to structured facts. `validate_claims.py`
asserts it over the AST rather than over the file's text -- a substring scan
fails on the docstring explaining the rule, which is how a structural check
stops checking (`testing-strategy.md` §23).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol

from sros_claim_model import ClaimDraft, ClaimRefusal
from sros_contracts import ClaimEvidenceRefusalReason, SignalDirection

__all__ = [
    "InterpretationRefusedError",
    "InterpretationRequest",
    "SignalLineage",
    "SignalView",
    "TemplateOutcome",
    "ClaimTemplate",
    "lineage_fact",
]


class InterpretationRefusedError(Exception):
    """This Signal yields no Claim, and no row of any kind is written."""

    def __init__(self, refusal: ClaimRefusal) -> None:
        super().__init__(f"{refusal.reason.value}: {refusal.detail}")
        self.refusal = refusal


def _refuse(reason: ClaimEvidenceRefusalReason, detail: str) -> InterpretationRefusedError:
    return InterpretationRefusedError(ClaimRefusal(reason=reason, detail=detail))


@dataclass(frozen=True)
class SignalLineage:
    """One contributing normalized record, as the interpreter reads it.

    §44 is explicit that the interpreter consumes **Signals** and does not read
    RawRecords as its semantic source. It reads normalized records for one thing
    only: the **attribution facts the Signal's scope does not carry** -- which
    published resource, what the source itself called the geography, which term
    scheme. Attribution is what separates OBSERVED from INFERRED, and an
    interpreter that guessed it would be asserting.

    Nothing here changes WHAT is asserted. The proposition comes from the
    Signal; these fields say whose it is.
    """

    normalized_record_id: str
    raw_record_id: str
    source_id: str
    observation_key: str
    record_kind_id: str
    period_label: str | None
    role: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def section(self, name: str) -> Mapping[str, Any]:
        value = self.payload.get(name)
        return value if isinstance(value, Mapping) else {}

    def text(self, section: str, key: str) -> str | None:
        value = self.section(section).get(key)
        return None if value is None else str(value)


@dataclass(frozen=True)
class SignalView:
    """One Signal and its lineage, as an interpreter sees it.

    Not the database row. `nlp.signals` stores the derivation; this is the
    projection an interpreter needs, and keeping them apart is what lets the
    signal schema move without every template moving with it -- the argument
    `EvidenceItem` makes for aggregation.
    """

    signal_id: str
    signal_type_id: str
    source_ids: tuple[str, ...]
    magnitude: Decimal
    magnitude_kind: str
    magnitude_unit: str | None
    magnitude_unit_state: str
    direction: SignalDirection
    derivation_confidence: float
    extractor_id: str
    extractor_version: str
    scope: Mapping[str, Any]
    # The registry's canonical name for the source, read from
    # `registry.sources` by the repository. `None` where the registry has
    # not named it, and the source id is used instead -- terser, never wrong.
    source_name: str | None
    temporal_basis: str
    temporal_window: Mapping[str, Any]
    inputs: tuple[SignalLineage, ...] = ()

    @property
    def contributing(self) -> tuple[SignalLineage, ...]:
        return tuple(i for i in self.inputs if i.role == "CONTRIBUTED")

    @property
    def period_labels(self) -> tuple[str, ...]:
        labels = self.temporal_window.get("period_labels")
        return tuple(str(x) for x in labels) if isinstance(labels, Sequence) else ()

    def scope_list(self, name: str) -> tuple[str, ...]:
        value = self.scope.get(name)
        if isinstance(value, Sequence) and not isinstance(value, str | bytes):
            return tuple(str(x) for x in value)
        return ()

    def scope_text(self, name: str) -> str | None:
        value = self.scope.get(name)
        return None if value is None else str(value)

    def single_source(self) -> str:
        """The one source this proposition is attributed to.

        A Signal whose inputs span two sources cannot be restated as "X reported
        …", and choosing one silently is how an attribution becomes wrong. No
        current extractor produces one -- every group key starts with
        `source_id` -- so this is a guard against a future one, not a live case.
        """
        sources = {i.source_id for i in self.contributing} | set(self.source_ids)
        if len(sources) != 1:
            raise _refuse(
                ClaimEvidenceRefusalReason.AMBIGUOUS_SIGNAL_LINEAGE,
                f"this Signal's contributing records name {sorted(sources)}. An OBSERVED "
                "claim says what ONE source reported, and picking one of several would "
                "attribute a statement to a publisher that did not make it",
            )
        return sources.pop()


def lineage_fact(signal: SignalView, section: str, key: str, *, label: str) -> str:
    """One attribution fact, agreed by every contributing record, or a refusal.

    The agreement check is the point. Two records disagreeing on the resource,
    the language label or the geography name means the proposition would have to
    pick one, and this layer refuses rather than picks.
    """
    contributing = signal.contributing
    if not contributing:
        raise _refuse(
            ClaimEvidenceRefusalReason.SIGNAL_LINEAGE_UNAVAILABLE,
            f"this Signal has no readable contributing records, so {label} cannot be "
            "stated. An OBSERVED claim without attribution is an assertion with a "
            "citation-shaped hole",
        )
    values = {record.text(section, key) for record in contributing}
    if None in values:
        raise _refuse(
            ClaimEvidenceRefusalReason.SIGNAL_LINEAGE_UNAVAILABLE,
            f"a contributing record does not publish {label} ({section}.{key}). It is "
            "not inferred from a key, a file name or a sibling record",
        )
    if len(values) != 1:
        raise _refuse(
            ClaimEvidenceRefusalReason.AMBIGUOUS_SIGNAL_LINEAGE,
            f"contributing records disagree on {label}: {sorted(v for v in values if v)}",
        )
    return str(values.pop())


@dataclass(frozen=True)
class InterpretationRequest:
    """Tenancy and correlation, carried explicitly and never reconstructed."""

    workspace_id: str
    correlation_id: str
    interpreted_at: datetime
    research_session_id: str | None = None


@dataclass(frozen=True)
class TemplateOutcome:
    """What one Signal produced. Exactly one of the two is set."""

    draft: ClaimDraft | None = None
    refusal: ClaimRefusal | None = None


class ClaimTemplate(Protocol):
    """One proposition shape, for one Signal type."""

    signal_type_id: str

    def render(self, signal: SignalView, request: InterpretationRequest) -> ClaimDraft: ...
