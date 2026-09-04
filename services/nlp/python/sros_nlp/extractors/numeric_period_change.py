"""`numeric-period-change@1.0.0` -- a measured series moved between two periods.

`numeric-period-change-extractor-v1.md`. Mission 1.11.1 §6-§14.

**What it asserts, in full:** the source-measured numeric value of one series
changed by exactly this much between two comparable periods.

**What it does not assert:** market growth, demand, attractiveness, economic
health, or that the change is good. A population going from 82,905,782 to
83,092,962 is a population going up by 187,180. Whether that is an opportunity
is a Claim, and a Claim has its own evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal

from sros_contracts import (
    SignalDerivationKind,
    SignalDirection,
    SignalMagnitudeKind,
    SignalMagnitudeUnitState,
    SignalQuantityFamily,
    SignalRefusalReason,
    SignalRequiredFact,
    SignalTemporalBasis,
)
from sros_signal_model import (
    NUMERIC_OBSERVATION,
    SignalDerivation,
    SignalDerivationRefusal,
    SignalDraft,
    SignalMagnitude,
    SignalRefusedError,
    SignalScope,
    SignalWindow,
    assess_inputs,
    build_signal,
)

from ..observations import NormalizedObservation
from .base import CandidateGroup, DerivationRequest, GroupOutcome, GroupRefusal, group_key_of

__all__ = ["ADJACENT_PERIODS", "PAIRING_STRATEGIES", "NumericPeriodChangeExtractor"]

# The only pairing strategy V1 implements, and it is a PARAMETER rather than a
# constant because it changes which signals exist: over 2018/2019/2020 it emits
# 2018->2019 and 2019->2020, and a strategy that also emitted 2018->2020 would
# produce a different, equally defensible answer. §9 is explicit that a choice
# affecting semantics is persisted, not assumed.
ADJACENT_PERIODS = "adjacent_periods"
PAIRING_STRATEGIES = frozenset({ADJACENT_PERIODS})

_PARAMETER_NAMES = frozenset({"pairing_strategy"})

# Declared once. A derivation over a series whose value cannot be read, whose
# geography was never classified, or whose period has no established instant is
# refused by the MODEL, from the record's own quality reasons -- never by a
# `if quality != VALID` branch here (§12).
_REQUIRED_FACTS = frozenset(
    {
        SignalRequiredFact.EXACT_NUMERIC_VALUE,
        SignalRequiredFact.COMPARABLE_INSTANT,
        SignalRequiredFact.CLASSIFIED_GEOGRAPHY,
    }
)


class NumericPeriodChangeExtractor:
    """Adjacent-period change within one measured series."""

    extractor_id = "numeric-period-change"
    extractor_version = "1.0.0"
    signal_type_id = "numeric_period_change"
    record_kind_id = NUMERIC_OBSERVATION
    family = SignalQuantityFamily.MEASURED_SERIES

    # ------------------------------------------------------------ parameters

    def resolve(self, requested: Mapping[str, object]) -> SignalDerivation:
        strategy = requested.get("pairing_strategy", ADJACENT_PERIODS)
        if strategy not in PAIRING_STRATEGIES:
            raise SignalRefusedError(
                SignalDerivationRefusal(
                    reason=SignalRefusalReason.PARAMETERS_INCOMPLETE,
                    detail=(
                        f"{strategy!r} is not a pairing strategy this extractor implements. "
                        f"Implemented: {sorted(PAIRING_STRATEGIES)}"
                    ),
                )
            )
        unknown = sorted(set(requested) - _PARAMETER_NAMES)
        if unknown:
            raise SignalRefusedError(
                SignalDerivationRefusal(
                    reason=SignalRefusalReason.PARAMETERS_INCOMPLETE,
                    detail=(
                        f"{unknown} affect nothing this extractor computes. A parameter "
                        "that is accepted and ignored is a hidden behaviour with a name"
                    ),
                )
            )
        return SignalDerivation(
            extractor_id=self.extractor_id,
            extractor_version=self.extractor_version,
            kind=SignalDerivationKind.DETERMINISTIC,
            required_facts=_REQUIRED_FACTS,
            parameter_names=_PARAMETER_NAMES,
            parameters={"pairing_strategy": strategy},
        )

    # -------------------------------------------------------------- grouping

    def group_key(
        self, observation: NormalizedObservation, derivation: SignalDerivation
    ) -> str | None:
        """One key per MEASURED SERIES.

        Every field is part of what makes two numbers measurements of the same
        thing. Dropping any one of them would let France's population and
        Germany's population meet, which §7 forbids by name -- and dropping the
        unit would let a figure in thousands be subtracted from one in units.
        """
        if observation.record_kind_id != self.record_kind_id:
            return None
        metric = observation.section("metric")
        geography = observation.section("geography")
        series = observation.section("series")
        return group_key_of(
            [
                ("source_id", observation.source_id),
                ("record_kind_id", observation.record_kind_id),
                ("metric_scheme", metric.get("scheme")),
                ("metric_id", metric.get("id")),
                ("geography_kind", geography.get("kind")),
                ("geography_canonical_scheme", geography.get("canonical_scheme")),
                ("geography_canonical_code", geography.get("canonical_code")),
                ("geography_source_code", geography.get("source_code")),
                ("series_dataset", series.get("dataset")),
                ("series_resource_id", series.get("resource_id")),
                ("series_frequency", series.get("frequency")),
                ("unit_state", observation.unit_state),
                ("unit", observation.unit),
                ("period_type", observation.text("period", "type")),
            ]
        )

    # ---------------------------------------------------------------- derive

    def derive(
        self,
        group: CandidateGroup,
        derivation: SignalDerivation,
        request: DerivationRequest,
    ) -> GroupOutcome:
        homogeneity = self._homogeneous(group, derivation)
        if homogeneity is not None:
            return GroupOutcome(refusals=(homogeneity,))

        ordered, ordering_refusal = self._ordered(group)
        if ordering_refusal is not None:
            return GroupOutcome(refusals=(ordering_refusal,))

        if len(ordered) < 2:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS,
                        detail=(
                            f"{len(ordered)} observation(s) in this series. A change needs "
                            "two periods, and one period restated is not a derivation"
                        ),
                        group_key=group.key,
                        observation_keys=group.observation_keys,
                    ),
                )
            )

        drafts: list[SignalDraft] = []
        refusals: list[GroupRefusal] = []
        # ADJACENT pairs, deliberately not every combination. Over 2018/2019/2020
        # that is 2018->2019 and 2019->2020; 2018->2020 is a different question
        # and would need a strategy that says so.
        for previous, current in zip(ordered, ordered[1:], strict=False):
            outcome = self._pair(previous, current, group, derivation, request)
            drafts.extend(outcome.drafts)
            refusals.extend(outcome.refusals)
        return GroupOutcome(drafts=tuple(drafts), refusals=tuple(refusals))

    # ---------------------------------------------------------------- checks

    def _homogeneous(
        self, group: CandidateGroup, derivation: SignalDerivation
    ) -> GroupRefusal | None:
        """Refuse a group whose members are not one series.

        Grouping already separates them, so this fires only when a CALLER hands
        an explicit pair -- which is exactly the case §7 says must not silently
        compare France with Germany.
        """
        if not group.observations:
            return None
        first = group.observations[0]
        expected = self.group_key(first, derivation)
        for observation in group.observations[1:]:
            if observation.record_kind_id != self.record_kind_id:
                return GroupRefusal(
                    reason=SignalRefusalReason.INCOMPATIBLE_INPUT_KINDS,
                    detail=(
                        f"{observation.normalized_record_id} is a "
                        f"{observation.record_kind_id}; this extractor reads "
                        f"{self.record_kind_id}"
                    ),
                    group_key=group.key,
                    observation_keys=group.observation_keys,
                )
            if self.group_key(observation, derivation) != expected:
                return GroupRefusal(
                    reason=SignalRefusalReason.INCOMPATIBLE_SERIES,
                    detail=(
                        f"{observation.observation_key!r} and {first.observation_key!r} are "
                        "not observations of the same measured series. Metric, geography, "
                        "unit, dataset and period type must all agree; a difference "
                        "between two different series is not a change"
                    ),
                    group_key=group.key,
                    observation_keys=group.observation_keys,
                )
        return None

    def _ordered(
        self, group: CandidateGroup
    ) -> tuple[tuple[NormalizedObservation, ...], GroupRefusal | None]:
        """By canonical period START, ascending. Never by row id or arrival order.

        Input order is part of the derivation identity, so an order that came
        from the database would make the identity depend on a plan the query
        optimiser chose.
        """
        starts: dict[str, datetime] = {}
        for observation in group.observations:
            start = observation.period_start
            if start is None or start.tzinfo is None:
                return (), GroupRefusal(
                    reason=SignalRefusalReason.REQUIRED_FACT_WITHHELD,
                    detail=(
                        f"{observation.observation_key!r} has no timezone-aware canonical "
                        "period start, so it cannot be placed on a shared timeline. "
                        f"Withheld: {SignalRequiredFact.COMPARABLE_INSTANT.value}"
                    ),
                    group_key=group.key,
                    observation_keys=group.observation_keys,
                )
            starts[observation.normalized_record_id] = start

        labels = [o.period_label for o in group.observations]
        duplicates = sorted({label for label in labels if labels.count(label) > 1})
        if duplicates:
            return (), GroupRefusal(
                reason=SignalRefusalReason.AMBIGUOUS_OBSERVATION_LINEAGE,
                detail=(
                    f"period label(s) {duplicates} appear more than once in one series. "
                    "Two rows for one period are one observation under two lineages, and "
                    "choosing between them is D-08"
                ),
                group_key=group.key,
                observation_keys=group.observation_keys,
            )

        ordered = sorted(
            group.observations,
            key=lambda o: (starts[o.normalized_record_id], o.observation_key),
        )
        return tuple(ordered), None

    # ------------------------------------------------------------------ pair

    def _pair(
        self,
        previous: NormalizedObservation,
        current: NormalizedObservation,
        group: CandidateGroup,
        derivation: SignalDerivation,
        request: DerivationRequest,
    ) -> GroupOutcome:
        inputs = (previous.to_input(), current.to_input())
        resolution = previous.period_type
        assert resolution is not None  # noqa: S101 -- _ordered already read it

        # The MODEL decides whether these inputs may contribute, from their own
        # quality reasons. This extractor never inspects a quality string.
        assessment = assess_inputs(inputs, derivation, family=self.family, resolution=resolution)
        if assessment.refusal is not None:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=assessment.refusal.reason,
                        detail=assessment.refusal.detail,
                        group_key=group.key,
                        observation_keys=(previous.observation_key, current.observation_key),
                    ),
                )
            )

        earlier, later = previous.value, current.value
        if earlier is None or later is None:
            # The record's quality said the value was REPORTED and it does not
            # read as an exact decimal. Reported rather than approximated: the
            # two statements contradict each other and a subtraction over a
            # guess would hide that.
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.INPUT_RECORD_INVALID,
                        detail=(
                            "a contributing observation reports a value that does not read "
                            "as an exact decimal, which contradicts its own quality state"
                        ),
                        group_key=group.key,
                        observation_keys=(previous.observation_key, current.observation_key),
                    ),
                )
            )

        change = later - earlier
        window = SignalWindow(
            basis=SignalTemporalBasis.COMPARABLE_INSTANTS,
            period_labels=(previous.period_label, current.period_label),
            resolution=resolution,
            observation_count=2,
            start=previous.period_start,
            end=current.period_end,
        )
        draft = build_signal(
            workspace_id=request.workspace_id,
            signal_type_id=self.signal_type_id,
            observations=inputs,
            derivation=derivation,
            direction=_direction(change),
            magnitude=_magnitude(change, current),
            # DETERMINISTIC arithmetic over exact decimals. It says the
            # subtraction is right, not that the market is moving (§28).
            derivation_confidence=1.0,
            scope=_scope(current),
            window=window,
            derived_at=request.derived_at,
            expires_at=request.expires_at,
            correlation_id=request.correlation_id,
            research_session_id=request.research_session_id,
        )
        return GroupOutcome(drafts=(draft,))


def _direction(change: Decimal) -> SignalDirection:
    """Mechanical, from the sign. Never POSITIVE or NEGATIVE: direction is
    change, and change is not sentiment (§11)."""
    if change > 0:
        return SignalDirection.INCREASING
    if change < 0:
        return SignalDirection.DECREASING
    return SignalDirection.UNCHANGED


def _magnitude(change: Decimal, observation: NormalizedObservation) -> SignalMagnitude:
    """The exact difference, in the inputs' own unit or in none.

    No percentage and no ratio. Both would need a denominator rule and a
    rounding rule, and a repeating decimal rounded to an unstated precision is
    the fake precision §10 forbids. `absolute_change` is exact, always defined,
    and sufficient to state the relation.
    """
    published = observation.unit_state == "PUBLISHED" and bool(observation.unit)
    return SignalMagnitude(
        value=change,
        kind=SignalMagnitudeKind.ABSOLUTE_CHANGE,
        unit=observation.unit if published else None,
        unit_state=(
            SignalMagnitudeUnitState.INHERITED
            if published
            else SignalMagnitudeUnitState.NOT_ESTABLISHED
        ),
    )


def _scope(observation: NormalizedObservation) -> SignalScope:
    """Source, metric and -- where one was canonically established -- geography.

    A geography with no canonical code contributes NO key rather than its source
    code: a field named `geography_codes` means canonical codes, and putting a
    source code in it is the promotion the geography map exists to prevent. The
    source code survives in the lineage's observation keys either way.
    """
    metric_id = observation.text("metric", "id") or ""
    canonical = observation.text("geography", "canonical_code")
    return SignalScope(
        source_ids=(observation.source_id,),
        metric_ids=(metric_id,),
        geography_codes=(canonical,) if canonical else (),
    )
