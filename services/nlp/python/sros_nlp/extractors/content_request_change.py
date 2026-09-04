"""`content-request-change@1.0.0` -- one item's request count moved between two adjacent periods.

Mission 1.19, ADR-032.

**What it asserts, in full:** the platform counted exactly this many more (or
fewer) requests for one content item on one period than on the immediately
preceding one, under one requester class and one access channel.

**What it does not assert:** readers, people, users, customers, interest,
curiosity, desire, demand, adoption, popularity, a trend, or a market. Kubernetes
going from 1,139 requests to 2,051 is Kubernetes going up by 912 requests.
Whether that is an opportunity is a Claim, and a Claim has its own evidence.

**The confounders, stated because the data shows them immediately.** Both members
are the SAME item, so every item-level confounder cancels exactly: prominence,
title, age, link structure and disambiguation are identical on both sides of the
subtraction. That is the reason this derivation was implemented and the
cross-item contrast was not.

**What does NOT cancel is the calendar.** The mission's own sample makes it
unmissable: 2024-03-02 and 2024-03-03 are a Saturday and a Sunday, and both
Docker and Kubernetes fall roughly 40 per cent across them and recover on the
Monday. A Sunday-to-Monday change in this series is mostly a statement about the
week. News events do not cancel either.

**Neither confounder makes the subtraction untrue.** They make an INFERENCE from
it unsound, which is a different failure at a different layer -- and the reason
this signal type's summary and every Claim built on it say so in their own words
rather than relying on a reader's caution.

**Adjacency is exact and a gap is never bridged** (ADR-023). Two periods must be
consecutive; anything else is `NON_CONTIGUOUS_SOURCE_BUCKETS`, because a change
computed across a period nobody read is indistinguishable from one that happened.
And an item absent from a period is ABSENT, never a count of zero -- the
collector already refuses to write one.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
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
    CONTENT_REQUEST_COUNT,
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

__all__ = ["ADJACENT_PERIODS", "PAIRING_STRATEGIES", "ContentRequestChangeExtractor"]

# The only pairing strategy V1 implements, and a PARAMETER rather than a
# constant because it changes which signals exist: over three consecutive days
# it emits day1->day2 and day2->day3, and a strategy that also emitted
# day1->day3 would produce a different, equally defensible answer.
ADJACENT_PERIODS = "adjacent_periods"
PAIRING_STRATEGIES = frozenset({ADJACENT_PERIODS})

_PARAMETER_NAMES = frozenset({"pairing_strategy"})

# Declared once. Note what is NOT here: `CLASSIFIED_GEOGRAPHY`, which this record
# kind cannot supply and which a derivation asking for it would be refused over
# by the MODEL rather than by a branch in this file.
_REQUIRED_FACTS = frozenset(
    {
        SignalRequiredFact.EXACT_NUMERIC_VALUE,
        SignalRequiredFact.COMPARABLE_INSTANT,
    }
)

# How long each period type lasts, for the adjacency test. Only the resolutions
# a source actually publishes at this kind are here: a period type absent from
# this map is refused rather than given a guessed length.
_PERIOD_LENGTHS: Mapping[str, timedelta] = {
    "DAY": timedelta(days=1),
}


class ContentRequestChangeExtractor:
    """Adjacent-period change within one item's request series."""

    extractor_id = "content-request-change"
    extractor_version = "1.0.0"
    signal_type_id = "content_request_change"
    record_kind_id = CONTENT_REQUEST_COUNT
    family = SignalQuantityFamily.CONTENT_REQUEST_VOLUME

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
        """One key per REQUEST SERIES.

        Every field is part of what makes two counts measurements of the same
        thing. The **requester class** is the one that would be easiest to drop
        and worst to drop: the same item on the same day carries a different
        count for `user` than for `all-agents`, and a group that mixed them
        would subtract one population from another and call the difference a
        change. The access channel is here for the same reason at a smaller
        scale.
        """
        if observation.record_kind_id != self.record_kind_id:
            return None
        content = observation.section("content")
        audience = observation.section("audience")
        return group_key_of(
            [
                ("source_id", observation.source_id),
                ("record_kind_id", observation.record_kind_id),
                ("content_id", content.get("id")),
                ("content_platform", content.get("platform")),
                ("audience_class", audience.get("class")),
                ("access_channel", audience.get("access_channel")),
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
        an explicit pair -- which is exactly the case that must not silently
        subtract one article's count from another's.
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
                        "not observations of the same request series. Item, platform, "
                        "requester class, access channel and period type must all agree; a "
                        "difference between two different series is not a change"
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
        keys = (previous.observation_key, current.observation_key)
        inputs = (previous.to_input(), current.to_input())
        resolution = previous.period_type
        if resolution is None or resolution.value not in _PERIOD_LENGTHS:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.INPUT_RECORD_INVALID,
                        detail=(
                            f"period type {resolution.value if resolution else None!r} has "
                            "no reviewed length, so adjacency cannot be tested. A guessed "
                            "length would let a gap look contiguous"
                        ),
                        group_key=group.key,
                        observation_keys=keys,
                    ),
                )
            )

        # ADR-023, and the rule that matters most for a daily series: EXACTLY
        # one period apart. A change computed across a day nobody read is
        # indistinguishable from one that happened, and a daily series has gaps
        # whenever an item drew no requests at all.
        expected = previous.period_start + _PERIOD_LENGTHS[resolution.value]  # type: ignore[operator]
        if current.period_start != expected:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.NON_CONTIGUOUS_SOURCE_BUCKETS,
                        detail=(
                            f"{previous.period_label!r} and {current.period_label!r} are not "
                            "consecutive periods. A gap is never bridged: the periods "
                            "between them were not read, and an item absent from a period "
                            "is ABSENT rather than a count of zero"
                        ),
                        group_key=group.key,
                        observation_keys=keys,
                    ),
                )
            )

        assessment = assess_inputs(inputs, derivation, family=self.family, resolution=resolution)
        if assessment.refusal is not None:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=assessment.refusal.reason,
                        detail=assessment.refusal.detail,
                        group_key=group.key,
                        observation_keys=keys,
                    ),
                )
            )

        earlier, later = _count_of(previous), _count_of(current)
        if earlier is None or later is None:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.INPUT_RECORD_INVALID,
                        detail=(
                            "a contributing observation carries no readable integer count, "
                            "which contradicts its own quality state"
                        ),
                        group_key=group.key,
                        observation_keys=keys,
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
            # DETERMINISTIC arithmetic over exact integers. It says the
            # subtraction is right, not that anything about the world moved.
            derivation_confidence=1.0,
            magnitude=SignalMagnitude(
                value=change,
                kind=SignalMagnitudeKind.ABSOLUTE_CHANGE,
                unit="requests",
                unit_state=SignalMagnitudeUnitState.INHERITED,
            ),
            scope=_scope(current),
            window=window,
            derived_at=request.derived_at,
            expires_at=request.expires_at,
            correlation_id=request.correlation_id,
            research_session_id=request.research_session_id,
        )
        return GroupOutcome(drafts=(draft,))


def _count_of(observation: NormalizedObservation) -> Decimal | None:
    """The count, read from `observation.count`.

    Not `observation.value`: this record kind names the field `count` because
    what it holds is a count of requests, and a normalizer that had called it
    `value` would have made it look like a measurement of something.
    """
    raw = observation.section("observation").get("count")
    if isinstance(raw, bool) or not isinstance(raw, int):
        return None
    return Decimal(raw)


def _direction(change: Decimal) -> SignalDirection:
    """Mechanical, from the sign. Never POSITIVE or NEGATIVE: direction is
    change, and change is not sentiment."""
    if change > 0:
        return SignalDirection.INCREASING
    if change < 0:
        return SignalDirection.DECREASING
    return SignalDirection.UNCHANGED


def _scope(observation: NormalizedObservation) -> SignalScope:
    """The item, the platform, the requester class and the access channel.

    No metric and no geography: a request count is not an instance of a measured
    series and carries no place. `SignalScope` refuses a `metric_ids` here by
    construction, which is the enforcement rather than this comment.
    """
    content = observation.section("content")
    audience = observation.section("audience")
    channel = audience.get("access_channel")
    return SignalScope(
        source_ids=(observation.source_id,),
        content_ids=(str(content.get("id") or ""),),
        content_platforms=(str(content.get("platform") or ""),),
        audience_classes=(str(audience.get("class") or ""),),
        access_channels=(str(channel),) if isinstance(channel, str) and channel else (),
    )
