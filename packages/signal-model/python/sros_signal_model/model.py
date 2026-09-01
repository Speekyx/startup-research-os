"""The Signal contract: a derived statement about a RELATION between observations.

Mission 1.11. Full specification: `docs/data/signal-contract-v1.md`.

**This layer derives. It does not interpret.** A Signal says two observations
stand in a stated relation, computed by a named extractor at a named version
over stated parameters. It does not say the relation means demand, interest,
attention or momentum -- those are Claims, and a Claim is a later stage with its
own evidence and its own confidence.

Three identities are kept apart, as they are at every layer below:

    observation_key          WHICH observation contributed. The distinctness
                             test, because one observation can have several
                             normalized rows and D-08 has not decided which to
                             read
    normalized_record_id     WHICH representation of it was actually read
    derivation_fingerprint   WHICH derivation this is -- inputs, extractor,
                             parameters, window

The derivation time and the correlation id are in none of them, and neither is
the RESULT: a changed magnitude under an unchanged identity means the extractor
is not deterministic or an input changed, and that has to be reportable rather
than absorbed into a new row.

**Nothing here reaches a network, a model, an embedder or a database.** The
package depends on `sros_contracts` and the standard library, and it runs in the
zero-dependency CI job.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from sros_contracts import (
    NormalizationQualityReason,
    NormalizedPeriodType,
    NormalizedRecordQuality,
    SignalDerivationKind,
    SignalDirection,
    SignalInputRole,
    SignalMagnitudeKind,
    SignalMagnitudeUnitState,
    SignalQuantityFamily,
    SignalRefusalReason,
    SignalRequiredFact,
    SignalTemporalBasis,
)

from .facts import withheld_facts
from .types import SIGNAL_TYPE_REGISTRY, SIGNAL_TYPES, record_kind_for

__all__ = [
    "MINIMUM_DISTINCT_OBSERVATIONS",
    "ORDERED_BASES",
    "SIGNAL_NAMESPACE",
    "SIGNAL_SCHEMA_ID",
    "SIGNAL_SCHEMA_VERSION",
    "AssessedInput",
    "InputAssessment",
    "ObservationInput",
    "SignalDerivation",
    "SignalDerivationRefusal",
    "SignalDraft",
    "SignalMagnitude",
    "SignalRefusedError",
    "SignalScope",
    "SignalWindow",
    "assess_inputs",
    "build_signal",
    "canonical_decimal_text",
    "canonical_fingerprint",
    "canonical_json",
]

# The canonical Signal schema, versioned independently of any extractor
# (`signal-contract-v1.md` §8). Bumped when what a Signal MEANS changes, never
# when an extractor is fixed.
SIGNAL_SCHEMA_ID = "sros.signal"
SIGNAL_SCHEMA_VERSION = 1

# Deterministic row ids, so a re-run converges on the row that exists rather than
# inserting a parallel copy. Same argument as the normalized record's namespace.
SIGNAL_NAMESPACE = uuid.UUID("6f2c9a41-38b5-5d07-9e4a-1c8b70d3f562")

# §3, the contrast rule. A derivation over one observation is that observation
# renamed. Two is the floor, not a tuning parameter: an extractor may require
# more, and none may require fewer.
MINIMUM_DISTINCT_OBSERVATIONS = 2

# The bases under which "before" and "after" exist, and therefore the only ones
# under which a direction can be asserted (§6).
ORDERED_BASES = frozenset(
    {
        SignalTemporalBasis.ORDERED_PERIODS,
        SignalTemporalBasis.COMPARABLE_INSTANTS,
    }
)


# ------------------------------------------------------------ canonical forms
#
# Reimplemented rather than imported. `sros_acquisition` is a service package
# and this is a shared model; importing one into the other would run the
# dependency the wrong way and drag a network-capable package into the
# zero-dependency suite. The two definitions are identical by contract and the
# test suite pins the outputs.


def canonical_json(payload: object) -> str:
    """Sorted keys, no incidental whitespace, stable separators."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_fingerprint(payload: object) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def canonical_decimal_text(value: Decimal) -> str:
    """Plain notation, never scientific, no trailing fractional zeros."""
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _serialisable(value: object) -> object:
    """A parameter value in canonical form, or a refusal to guess.

    `Decimal` becomes its exact text rather than a float, for the reason the
    normalization layer never lets a float near a source number. Anything whose
    serialisation would depend on a repr is rejected: a parameter that cannot be
    written down identically twice cannot be part of a fingerprint.
    """
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, Decimal):
        return canonical_decimal_text(value)
    if isinstance(value, (list, tuple)):
        return [_serialisable(item) for item in value]
    if isinstance(value, Mapping):
        return {str(k): _serialisable(v) for k, v in sorted(value.items())}
    raise ValueError(
        f"parameter value of type {type(value).__name__!r} has no canonical form. "
        "A float is refused on purpose: a parameter that round-trips through "
        "IEEE-754 cannot be fingerprinted reproducibly"
    )


# -------------------------------------------------------------------- refusal


class SignalRefusedError(Exception):
    """No Signal exists, and no row is written.

    Carries the refusal so a caller can report it. `signal-contract-v1.md` §11:
    a row in a table of signals says a signal exists, and one meaning "no signal
    exists" is a misleading signal.
    """

    def __init__(self, refusal: SignalDerivationRefusal) -> None:
        super().__init__(f"{refusal.reason.value}: {refusal.detail}")
        self.refusal = refusal


@dataclass(frozen=True)
class SignalDerivationRefusal:
    """Why a derivation produced nothing. A returned value, never persisted."""

    reason: SignalRefusalReason
    detail: str
    withheld: frozenset[SignalRequiredFact] = frozenset()
    excluded_record_ids: tuple[str, ...] = ()

    def to_json(self) -> dict[str, object]:
        return {
            "reason": self.reason.value,
            "detail": self.detail,
            "withheld_facts": sorted(f.value for f in self.withheld),
            "excluded_record_ids": list(self.excluded_record_ids),
        }


# --------------------------------------------------------------------- inputs


@dataclass(frozen=True)
class ObservationInput:
    """One normalized record, as the derivation sees it.

    Deliberately a flat view rather than the record itself: this layer needs the
    identity, the kind, the resolution and the quality, and it must not be able
    to read a payload -- reading one is how a model starts interpreting.
    """

    normalized_record_id: str
    raw_record_id: str
    source_id: str
    observation_key: str
    record_kind_id: str
    period_type: NormalizedPeriodType
    period_label: str
    quality: NormalizedRecordQuality
    quality_reasons: frozenset[NormalizationQualityReason] = frozenset()
    # WHICH published resource this came from. Added in Mission 1.12 so a
    # temporal order certification can be scoped to one publication stream:
    # ordering is a property of a stream, and `source_id` alone would let a
    # future GDELT dataset inherit the WEB-NGRAM finding. Optional, and the
    # default is a REFUSAL -- an observation that cannot say which resource it
    # came from claims no stream's certification.
    resource_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "normalized_record_id",
            "raw_record_id",
            "source_id",
            "observation_key",
            "record_kind_id",
            "period_label",
        ):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required on a signal input")


@dataclass(frozen=True)
class AssessedInput:
    """An input after the required-fact check, with its role and its reason."""

    observation: ObservationInput
    role: SignalInputRole
    refusal_reason: SignalRefusalReason | None = None
    withheld: frozenset[SignalRequiredFact] = frozenset()

    def __post_init__(self) -> None:
        contributed = self.role is SignalInputRole.CONTRIBUTED
        if contributed and self.refusal_reason is not None:
            raise ValueError("a CONTRIBUTED input cannot carry a refusal reason")
        if not contributed and self.refusal_reason is None:
            raise ValueError("an EXCLUDED input must say why it was excluded")

    def to_json(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "normalized_record_id": self.observation.normalized_record_id,
            "raw_record_id": self.observation.raw_record_id,
            "source_id": self.observation.source_id,
            "observation_key": self.observation.observation_key,
            "record_kind_id": self.observation.record_kind_id,
            "resource_id": self.observation.resource_id,
            "period_label": self.observation.period_label,
            "period_type": self.observation.period_type.value,
            "quality": self.observation.quality.value,
            "quality_reasons": sorted(r.value for r in self.observation.quality_reasons),
            "role": self.role.value,
        }
        if self.refusal_reason is not None:
            payload["refusal_reason"] = self.refusal_reason.value
        if self.withheld:
            payload["withheld_facts"] = sorted(f.value for f in self.withheld)
        return payload


@dataclass(frozen=True)
class InputAssessment:
    """The outcome of offering a set of records to a derivation."""

    assessed: tuple[AssessedInput, ...]
    refusal: SignalDerivationRefusal | None = None

    @property
    def contributed(self) -> tuple[AssessedInput, ...]:
        return tuple(a for a in self.assessed if a.role is SignalInputRole.CONTRIBUTED)

    @property
    def excluded(self) -> tuple[AssessedInput, ...]:
        return tuple(a for a in self.assessed if a.role is SignalInputRole.EXCLUDED)


# ---------------------------------------------------------------- derivation


@dataclass(frozen=True)
class SignalDerivation:
    """Who computed this, at what version, over which stated parameters.

    `parameter_names` is the extractor's own declaration of what affects its
    output, and `parameters` must carry exactly those keys. The model does not
    know what any extractor's parameters should be and does not have to; it
    enforces that the extractor said (§7). A hidden default makes a version
    number meaningless.
    """

    extractor_id: str
    extractor_version: str
    kind: SignalDerivationKind
    required_facts: frozenset[SignalRequiredFact]
    parameter_names: frozenset[str] = frozenset()
    parameters: Mapping[str, object] = field(default_factory=dict)
    model_version: str | None = None
    prompt_version: str | None = None

    def __post_init__(self) -> None:
        if not self.extractor_id.strip() or not self.extractor_version.strip():
            raise ValueError("a derivation must name its extractor and its version")
        deterministic = self.kind is SignalDerivationKind.DETERMINISTIC
        if deterministic and (self.model_version or self.prompt_version):
            raise ValueError(
                "a DETERMINISTIC derivation may not carry a model or prompt version. "
                "A signal produced by arithmetic did not consult a model, and a "
                "provenance field saying otherwise would be false"
            )
        if not deterministic and not self.model_version:
            raise ValueError(
                "a MODEL_DERIVED derivation must record its model version "
                "(llm-reasoning-rules.md §9)"
            )

    @property
    def parameter_fingerprint(self) -> str:
        return canonical_fingerprint(_serialisable(dict(self.parameters)))

    def parameters_json(self) -> dict[str, object]:
        serialised = _serialisable(dict(self.parameters))
        if not isinstance(serialised, dict):  # pragma: no cover -- structural
            raise ValueError("parameters must serialise to an object")
        return serialised


# ------------------------------------------------------------------ magnitude


@dataclass(frozen=True)
class SignalMagnitude:
    """How much, exactly, and in what.

    Never a float and never a unit-interval strength. `signal-contract-v1.md`
    §5: a GDELT term frequency and a World Bank population figure are not
    measurements of comparable things, so a shared 0-100 scale would be a
    comparison manufactured by the act of storing them together.
    """

    value: Decimal
    kind: SignalMagnitudeKind
    unit: str | None = None
    unit_state: SignalMagnitudeUnitState = SignalMagnitudeUnitState.NOT_ESTABLISHED

    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal):
            raise ValueError(
                "a magnitude must be an exact Decimal. A float would give back at the "
                "first subtraction the guarantee the normalization layer exists to make"
            )
        if self.value.is_nan() or self.value.is_infinite():
            raise ValueError("a magnitude must be a finite decimal")
        dimensionless_kinds = {
            SignalMagnitudeKind.RATIO,
            SignalMagnitudeKind.OBSERVATION_COUNT,
        }
        if (
            self.kind in dimensionless_kinds
            and self.unit_state is not SignalMagnitudeUnitState.DIMENSIONLESS
        ):
            raise ValueError(f"a {self.kind.value} magnitude is always DIMENSIONLESS")
        if self.unit_state is SignalMagnitudeUnitState.INHERITED:
            if not (self.unit or "").strip():
                raise ValueError("an INHERITED unit state must carry the unit it inherited")
        elif self.unit is not None:
            raise ValueError(
                f"a {self.unit_state.value} magnitude carries no unit. Naming one would "
                "assert the source published something it did not"
            )

    def to_json(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "value": canonical_decimal_text(self.value),
            "kind": self.kind.value,
            "unit_state": self.unit_state.value,
        }
        if self.unit is not None:
            payload["unit"] = self.unit
        return payload


# ---------------------------------------------------------------------- scope


@dataclass(frozen=True)
class SignalScope:
    """What the signal is about.

    A dimension no input carries has **no key at all** in the serialised form --
    never a null. The rule comes from the lexical record kind, which has no
    geography key rather than a null one, and it matters more here because a
    nullable field is an invitation to fill it.
    """

    source_ids: tuple[str, ...]
    terms: tuple[str, ...] = ()
    metric_ids: tuple[str, ...] = ()
    source_language_labels: tuple[str, ...] = ()
    source_language_scheme: str | None = None
    canonical_language_tags: tuple[str, ...] = ()
    geography_codes: tuple[str, ...] = ()
    # Mission 1.15.9, ADR-029. The dimensions a TRANSACTION_VALUE derivation is
    # about. Absent from every other family's scope, which is the same rule the
    # lexical kind follows for geography: a dimension no input carries has no
    # key, never a null.
    amount_types: tuple[str, ...] = ()
    amount_scopes: tuple[str, ...] = ()
    currencies: tuple[str, ...] = ()
    notice_classes: tuple[str, ...] = ()
    classification_codes: tuple[str, ...] = ()
    classification_scheme: str | None = None

    def __post_init__(self) -> None:
        if not self.source_ids:
            raise ValueError("a signal scope must name at least one source")
        # ADR-029. An amount whose kind is unrecorded is the flattening the
        # normalization layer spent a design refusing; a currency with no amount
        # type beside it is a number nobody can read.
        if self.currencies and not self.amount_types:
            raise ValueError(
                "a currency means nothing without the amount semantic it belongs to. A "
                "total value and a framework maximum in EUR are different facts, and a "
                "scope carrying only the currency would make them look like one"
            )
        if self.classification_codes and not self.classification_scheme:
            raise ValueError(
                "a classification code means nothing without the vocabulary it came "
                "from. 90911200 is a CPV code, and a reader cannot know that from the "
                "digits alone"
            )
        if self.source_language_labels and not self.source_language_scheme:
            raise ValueError(
                "a source language label means nothing without the vocabulary it came "
                "from. ENGLISH is a CLD2 name, and a reader cannot know that from the "
                "label alone"
            )

    def to_json(self) -> dict[str, object]:
        payload: dict[str, object] = {"source_ids": list(self.source_ids)}
        for key, values in (
            ("terms", self.terms),
            ("metric_ids", self.metric_ids),
            ("source_language_labels", self.source_language_labels),
            ("canonical_language_tags", self.canonical_language_tags),
            ("geography_codes", self.geography_codes),
            ("amount_types", self.amount_types),
            ("amount_scopes", self.amount_scopes),
            ("currencies", self.currencies),
            ("notice_classes", self.notice_classes),
            ("classification_codes", self.classification_codes),
        ):
            if values:
                payload[key] = list(values)
        if self.source_language_scheme:
            payload["source_language_scheme"] = self.source_language_scheme
        if self.classification_scheme:
            payload["classification_scheme"] = self.classification_scheme
        return payload


# --------------------------------------------------------------------- window


@dataclass(frozen=True)
class SignalWindow:
    """What temporal relation the derivation actually used.

    `signal-temporal-semantics-v1.md`. ORDER and GLOBAL INSTANT are different
    questions, so the basis says which one was available -- and only
    `COMPARABLE_INSTANTS` carries bounds, which is the structural reason a
    signal cannot quietly acquire a timeline its inputs never had.
    """

    basis: SignalTemporalBasis
    period_labels: tuple[str, ...]
    resolution: NormalizedPeriodType
    observation_count: int
    start: datetime | None = None
    end: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.basis, SignalTemporalBasis):
            raise ValueError(f"{self.basis!r} is not a SignalTemporalBasis")
        if not self.period_labels:
            raise ValueError("a window must carry the source period labels it covered")
        if self.observation_count < MINIMUM_DISTINCT_OBSERVATIONS:
            raise ValueError(
                f"a window covers at least {MINIMUM_DISTINCT_OBSERVATIONS} observations"
            )
        if (
            self.basis is SignalTemporalBasis.SAME_PERIOD_LABEL
            and len(set(self.period_labels)) != 1
        ):
            raise ValueError(
                "a SAME_PERIOD_LABEL window covers exactly one distinct source label. "
                "The equality is what makes the derivation valid, so it is checked here "
                "rather than assumed"
            )
        comparable = self.basis is SignalTemporalBasis.COMPARABLE_INSTANTS
        for name in ("start", "end"):
            bound: datetime | None = getattr(self, name)
            if bound is None:
                continue
            if not comparable:
                raise ValueError(
                    f"a {self.basis.value} window carries no {name}. Bounds would place "
                    "observations on a timeline the source never established"
                )
            if bound.tzinfo is None:
                raise ValueError(
                    f"a COMPARABLE_INSTANTS {name} must be timezone-aware. A naive bound "
                    "here is a wall-clock reading presented as a moment"
                )
        if comparable and (self.start is None or self.end is None):
            raise ValueError("a COMPARABLE_INSTANTS window states both bounds")
        if self.start and self.end and self.end < self.start:
            raise ValueError("a window cannot end before it starts")

    @property
    def event_time(self) -> datetime | None:
        """What `observed_at` is set from, or `None` when there is no instant.

        The same answer `CanonicalPeriod.event_time` gives one layer down, and
        for the same reason: an aware datetime here would carry an offset no
        source published.
        """
        return self.end if self.basis is SignalTemporalBasis.COMPARABLE_INSTANTS else None

    def to_json(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "basis": self.basis.value,
            "period_labels": list(self.period_labels),
            "resolution": self.resolution.value,
            "observation_count": self.observation_count,
        }
        if self.start is not None and self.end is not None:
            payload["start"] = self.start.isoformat()
            payload["end"] = self.end.isoformat()
        return payload


# ------------------------------------------------------------------ assessment


def assess_inputs(
    observations: Sequence[ObservationInput],
    derivation: SignalDerivation,
    *,
    family: SignalQuantityFamily,
    resolution: NormalizedPeriodType,
) -> InputAssessment:
    """Which records may contribute, which may not, and whether anything remains.

    Two classes of problem, handled differently on purpose:

        a QUALITY problem is about ONE record -- it is excluded, recorded, and
        the derivation continues with what is left;

        a KIND or RESOLUTION mismatch means the caller is deriving over records
        that do not belong together -- the whole derivation is refused, because
        excluding the odd one out would be the silent coarsening §14 forbids by
        another route.
    """
    expected_kind = record_kind_for(family)
    for observation in observations:
        if observation.record_kind_id != expected_kind:
            return InputAssessment(
                assessed=(),
                refusal=SignalDerivationRefusal(
                    reason=SignalRefusalReason.INCOMPATIBLE_INPUT_KINDS,
                    detail=(
                        f"{observation.normalized_record_id} is a "
                        f"{observation.record_kind_id} and a {family.value} signal reads "
                        f"{expected_kind}"
                    ),
                    excluded_record_ids=(observation.normalized_record_id,),
                ),
            )
        if observation.period_type is not resolution:
            return InputAssessment(
                assessed=(),
                refusal=SignalDerivationRefusal(
                    reason=SignalRefusalReason.INCOMPATIBLE_INPUT_KINDS,
                    detail=(
                        f"{observation.normalized_record_id} covers a "
                        f"{observation.period_type.value} and the window states "
                        f"{resolution.value}. Resampling is an operation with parameters, "
                        "not something a constructor does on the way past"
                    ),
                    excluded_record_ids=(observation.normalized_record_id,),
                ),
            )

    assessed: list[AssessedInput] = []
    for observation in observations:
        if observation.quality is NormalizedRecordQuality.INVALID:
            assessed.append(
                AssessedInput(
                    observation=observation,
                    role=SignalInputRole.EXCLUDED,
                    refusal_reason=SignalRefusalReason.INPUT_RECORD_INVALID,
                )
            )
            continue
        withheld = withheld_facts(
            derivation.required_facts,
            record_kind_id=observation.record_kind_id,
            quality_reasons=observation.quality_reasons,
            source_id=observation.source_id,
            resource_id=observation.resource_id,
        )
        if withheld:
            assessed.append(
                AssessedInput(
                    observation=observation,
                    role=SignalInputRole.EXCLUDED,
                    refusal_reason=SignalRefusalReason.REQUIRED_FACT_WITHHELD,
                    withheld=withheld,
                )
            )
            continue
        assessed.append(AssessedInput(observation=observation, role=SignalInputRole.CONTRIBUTED))

    contributed = [a for a in assessed if a.role is SignalInputRole.CONTRIBUTED]
    keys = [a.observation.observation_key for a in contributed]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        return InputAssessment(
            assessed=tuple(assessed),
            refusal=SignalDerivationRefusal(
                reason=SignalRefusalReason.AMBIGUOUS_OBSERVATION_LINEAGE,
                detail=(
                    f"{len(duplicates)} observation(s) contribute more than one normalized "
                    f"row: {duplicates}. Which representation to read is D-08, which is "
                    "open, and counting both would manufacture a contrast out of one "
                    "observation"
                ),
                excluded_record_ids=tuple(
                    a.observation.normalized_record_id
                    for a in contributed
                    if a.observation.observation_key in set(duplicates)
                ),
            ),
        )

    if len(set(keys)) < MINIMUM_DISTINCT_OBSERVATIONS:
        excluded = tuple(
            a.observation.normalized_record_id
            for a in assessed
            if a.role is SignalInputRole.EXCLUDED
        )
        return InputAssessment(
            assessed=tuple(assessed),
            refusal=SignalDerivationRefusal(
                reason=SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS,
                detail=(
                    f"{len(set(keys))} distinct observation(s) remain and a Signal needs "
                    f"{MINIMUM_DISTINCT_OBSERVATIONS}. One observation restated is not a "
                    "derivation"
                ),
                withheld=frozenset().union(*(a.withheld for a in assessed if a.withheld))
                if any(a.withheld for a in assessed)
                else frozenset(),
                excluded_record_ids=excluded,
            ),
        )

    return InputAssessment(assessed=tuple(assessed))


# ---------------------------------------------------------------------- draft


@dataclass(frozen=True)
class SignalDraft:
    """A Signal, ready to persist. Produced only by `build_signal`."""

    id: str
    workspace_id: str
    research_session_id: str | None
    signal_type_registry: str
    signal_type_id: str
    quantity_family: SignalQuantityFamily
    direction: SignalDirection
    magnitude: SignalMagnitude
    derivation_confidence: float
    scope: SignalScope
    window: SignalWindow
    derivation: SignalDerivation
    inputs: tuple[AssessedInput, ...]
    derivation_fingerprint: str
    parameter_fingerprint: str
    derived_at: datetime
    expires_at: datetime
    correlation_id: str

    @property
    def observed_at(self) -> datetime | None:
        """`NULL` unless the window is on a shared timeline. Never invented."""
        return self.window.event_time

    @property
    def contributed(self) -> tuple[AssessedInput, ...]:
        return tuple(a for a in self.inputs if a.role is SignalInputRole.CONTRIBUTED)

    def lineage_json(self) -> list[dict[str, object]]:
        return [a.to_json() for a in self.inputs]


def _identity_material(
    *,
    workspace_id: str,
    signal_type_id: str,
    quantity_family: SignalQuantityFamily,
    derivation: SignalDerivation,
    contributed: Sequence[AssessedInput],
    window: SignalWindow,
) -> dict[str, object]:
    """What makes two derivations the same derivation.

    Outputs are excluded on purpose: a changed magnitude under an unchanged
    identity is a REPORT, not a new row.
    """
    return {
        "schema": {"id": SIGNAL_SCHEMA_ID, "version": SIGNAL_SCHEMA_VERSION},
        "workspace_id": workspace_id,
        "signal_type": {"registry": SIGNAL_TYPE_REGISTRY, "id": signal_type_id},
        "quantity_family": quantity_family.value,
        "extractor": {
            "id": derivation.extractor_id,
            "version": derivation.extractor_version,
        },
        "inputs": [
            {
                "observation_key": a.observation.observation_key,
                "normalized_record_id": a.observation.normalized_record_id,
            }
            for a in contributed
        ],
        "parameter_fingerprint": derivation.parameter_fingerprint,
        "window": {
            "basis": window.basis.value,
            "period_labels": list(window.period_labels),
            "resolution": window.resolution.value,
        },
    }


def build_signal(
    *,
    workspace_id: str,
    signal_type_id: str,
    observations: Sequence[ObservationInput],
    derivation: SignalDerivation,
    direction: SignalDirection,
    magnitude: SignalMagnitude,
    derivation_confidence: float,
    scope: SignalScope,
    window: SignalWindow,
    derived_at: datetime,
    expires_at: datetime,
    correlation_id: str,
    research_session_id: str | None = None,
) -> SignalDraft:
    """One Signal, or `SignalRefusedError`.

    A `ValueError` means the CALLER is wrong -- a confidence out of range, a
    direction with no order behind it, a lexical scope carrying a geography.
    A `SignalRefusedError` means the DATA does not support a derivation, which is an
    ordinary outcome and not a defect.
    """
    spec = SIGNAL_TYPES.get(signal_type_id)
    if spec is None:
        raise SignalRefusedError(
            SignalDerivationRefusal(
                reason=SignalRefusalReason.UNSUPPORTED_SIGNAL_TYPE,
                detail=(
                    f"{signal_type_id!r} is not a registered signal type. "
                    f"Registered: {sorted(SIGNAL_TYPES)}"
                ),
            )
        )

    supplied = set(derivation.parameters)
    declared = set(derivation.parameter_names)
    if supplied != declared:
        raise SignalRefusedError(
            SignalDerivationRefusal(
                reason=SignalRefusalReason.PARAMETERS_INCOMPLETE,
                detail=(
                    f"the extractor declares {sorted(declared)} and supplied "
                    f"{sorted(supplied)}. A parameter affecting the output that is not "
                    "stated is a hidden default, and a hidden default makes the extractor "
                    "version meaningless"
                ),
            )
        )

    if not 0.0 <= derivation_confidence <= 1.0:
        raise ValueError(
            f"derivation_confidence {derivation_confidence} is outside [0,1]. "
            "Out of range is rejected rather than clamped: it means the producer is on "
            "a different scale, and clamping would hide that behind a plausible result"
        )
    if not workspace_id.strip():
        raise ValueError("a signal is workspace-scoped and workspace_id is never defaulted")
    if not correlation_id.strip():
        raise ValueError("a signal records the correlation that produced it")
    # Awareness FIRST: comparing a naive datetime with an aware one raises a
    # TypeError, so the check below would report the wrong problem -- and a
    # caller reading "can't compare offset-naive and offset-aware" learns
    # nothing about the rule it broke.
    if derived_at.tzinfo is None or expires_at.tzinfo is None:
        raise ValueError("derivation timestamps are timezone-aware")
    if expires_at <= derived_at:
        raise ValueError(
            "expires_at must follow derived_at. A retention window in the past is a "
            "policy that was never applied"
        )

    if direction is not SignalDirection.NOT_APPLICABLE and window.basis not in ORDERED_BASES:
        raise ValueError(
            f"a {window.basis.value} window supports no direction. {direction.value} is a "
            "statement about before and after, and this derivation established no order"
        )

    if spec.family is SignalQuantityFamily.LEXICAL_FREQUENCY:
        if scope.geography_codes:
            raise ValueError(
                "a LEXICAL_FREQUENCY signal carries no geography. A language is not a "
                "place, and the record kind behind it has no geography key at all"
            )
        if not scope.terms:
            raise ValueError("a LEXICAL_FREQUENCY signal states the terms it is about")
    elif spec.family is SignalQuantityFamily.TRANSACTION_VALUE:
        # Mission 1.15.9, ADR-029. The dimensions a transaction signal cannot be
        # read without, and each mirrors a rule one layer down.
        #
        # `metric_ids` is deliberately NOT required and NOT permitted: a
        # procurement value is the amount ONE transaction settled at, with no
        # metric it is an instance of. That absence is why MEASURED_SERIES could
        # not be widened to hold this family.
        if scope.metric_ids or scope.terms:
            raise ValueError(
                "a TRANSACTION_VALUE signal carries no metric and no term. It is the "
                "value one transaction settled at, not an instance of a series and not "
                "a count of tokens"
            )
        if not scope.amount_types:
            raise ValueError(
                "a TRANSACTION_VALUE signal states the monetary semantic it aggregated. "
                "An amount whose kind is unrecorded is the flattening the normalization "
                "layer refuses, one layer up"
            )
        if not scope.currencies:
            raise ValueError(
                "a TRANSACTION_VALUE signal states its currency. A number of money with "
                "no currency is not readable, and no rate exists to supply one"
            )
    elif not scope.metric_ids:
        raise ValueError("a MEASURED_SERIES signal states the metric it is about")

    if scope.canonical_language_tags and (
        SignalRequiredFact.CANONICAL_LANGUAGE not in derivation.required_facts
    ):
        raise ValueError(
            "a canonical language tag may only appear where the derivation required "
            "CANONICAL_LANGUAGE and every input supplied it. Deriving a tag from a "
            "source label is the inference H-30 exists to keep visible"
        )

    assessment = assess_inputs(
        observations,
        derivation,
        family=spec.family,
        resolution=window.resolution,
    )
    if assessment.refusal is not None:
        raise SignalRefusedError(assessment.refusal)

    contributed = assessment.contributed
    if window.observation_count != len(contributed):
        raise ValueError(
            f"the window covers {window.observation_count} observations and "
            f"{len(contributed)} contributed. A window that does not describe the inputs "
            "describes nothing"
        )
    scope_sources = set(scope.source_ids)
    input_sources = {a.observation.source_id for a in contributed}
    if scope_sources != input_sources:
        raise ValueError(
            f"scope names sources {sorted(scope_sources)} and the contributing inputs come "
            f"from {sorted(input_sources)}. The scope is derived from the lineage, never "
            "asserted beside it"
        )

    fingerprint = canonical_fingerprint(
        _identity_material(
            workspace_id=workspace_id,
            signal_type_id=signal_type_id,
            quantity_family=spec.family,
            derivation=derivation,
            contributed=contributed,
            window=window,
        )
    )

    return SignalDraft(
        id=str(uuid.uuid5(SIGNAL_NAMESPACE, fingerprint)),
        workspace_id=workspace_id,
        research_session_id=research_session_id,
        signal_type_registry=SIGNAL_TYPE_REGISTRY,
        signal_type_id=signal_type_id,
        quantity_family=spec.family,
        direction=direction,
        magnitude=magnitude,
        derivation_confidence=derivation_confidence,
        scope=scope,
        window=window,
        derivation=derivation,
        inputs=assessment.assessed,
        derivation_fingerprint=fingerprint,
        parameter_fingerprint=derivation.parameter_fingerprint,
        derived_at=derived_at,
        expires_at=expires_at,
        correlation_id=correlation_id,
    )
