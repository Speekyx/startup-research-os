"""`lexical-frequency-change@1.0.0` -- one term, two adjacent WEB-NGRAM buckets.

`lexical-frequency-change-extractor-v1.md`. Mission 1.12.1.

**What it asserts, in full:** for one lexical term, one source language label and
one gram size, the GDELT source-measured frequency at a bucket differs by
exactly this much from the frequency at the immediately preceding bucket of the
same stream.

**What it does not assert:** that demand, attention, popularity, interest,
momentum or trend strength changed. It does not even assert that the underlying
real-world phenomenon changed -- a term frequency moves when coverage moves, and
coverage moves for reasons Mission 1.11 §25 lists: a news event, a crisis, a
celebrity, weather, politics, a disaster, a sports fixture.

**This is the first extractor whose window basis is `ORDERED_PERIODS`**, and it
exists only because Mission 1.12 closed H-32 on GDELT's own evidence. Two things
follow, and both are enforced rather than intended:

    the ordering is CERTIFIED, never inferred    -- §_certified below
    the ordering is not an INSTANT               -- no bounds, no observed_at,
                                                    no timezone, ever
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
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
    LEXICAL_FREQUENCY_OBSERVATION,
    SignalDerivation,
    SignalDerivationRefusal,
    SignalDraft,
    SignalMagnitude,
    SignalRefusedError,
    SignalScope,
    SignalWindow,
    assess_inputs,
    build_signal,
    order_certification,
)

from ..observations import NormalizedObservation
from .base import CandidateGroup, DerivationRequest, GroupOutcome, GroupRefusal, group_key_of

__all__ = [
    "ADJACENT_SOURCE_BUCKETS",
    "BUCKET_LABEL_FORMAT",
    "BUCKET_STEP",
    "LABEL_SCHEME",
    "MAX_SELECTED_TERMS",
    "PAIRING_STRATEGIES",
    "LexicalFrequencyChangeExtractor",
]

# The label scheme this extractor understands, and the ONLY one whose step
# arithmetic below is correct. Checked against the certification rather than
# assumed: a future certification for the same source under a different scheme
# would make the 15-minute step wrong, and it would be wrong silently.
LABEL_SCHEME = "gdelt-web-ngram-bucket"
BUCKET_LABEL_FORMAT = "%Y%m%d%H%M%S"

# GDELT's documented cadence: "Every 15 minutes two ngram files are produced".
# The step is the SOURCE's, not ours -- a collector or an extractor choosing its
# own interval would be deciding what the publisher publishes.
BUCKET_STEP = timedelta(minutes=15)

ADJACENT_SOURCE_BUCKETS = "adjacent_source_buckets"
PAIRING_STRATEGIES = frozenset({ADJACENT_SOURCE_BUCKETS})

# OUR OWN operational ceiling on how many terms one derivation may select. A
# term selection is a research decision somebody makes by hand; 25 is generous
# for that and far short of the ~223,000 terms one bucket holds. Not a limit
# anybody published, and stated as ours.
MAX_SELECTED_TERMS = 25

_PARAMETER_NAMES = frozenset({"terms", "pairing_strategy"})

# `SOURCE_RELATIVE_ORDER` is the fact this extractor exists to use, and
# `COMPARABLE_INSTANT` is deliberately absent: H-29 is open, the buckets are
# ordered relative to each other, and neither is on a shared timeline.
# `CANONICAL_LANGUAGE` is absent for the same reason under H-30.
_REQUIRED_FACTS = frozenset(
    {
        SignalRequiredFact.EXACT_NUMERIC_VALUE,
        SignalRequiredFact.LEXICAL_TERM,
        SignalRequiredFact.SOURCE_PERIOD_LABEL,
        SignalRequiredFact.SOURCE_LANGUAGE_LABEL,
        SignalRequiredFact.SOURCE_RELATIVE_ORDER,
    }
)


class LexicalFrequencyChangeExtractor:
    """Adjacent-bucket frequency change within one lexical series."""

    extractor_id = "lexical-frequency-change"
    extractor_version = "1.0.0"
    signal_type_id = "lexical_frequency_change"
    record_kind_id = LEXICAL_FREQUENCY_OBSERVATION
    family = SignalQuantityFamily.LEXICAL_FREQUENCY

    # ------------------------------------------------------------ parameters

    def resolve(self, requested: Mapping[str, object]) -> SignalDerivation:
        """`terms` is REQUIRED and an empty selection is a refusal, not "all".

        One WEB-NGRAM bucket holds hundreds of thousands of terms and the
        dataset publishes 96 buckets a day since 2019. An unattended sweep over
        that is not a derivation anybody asked for, and every bounded default --
        "the top 100", "everything above N" -- is a selection threshold nobody
        reviewed. So the caller names the terms, and the names are canonically
        sorted here, in ONE place, so that requesting them in any order is the
        same derivation with the same fingerprint.
        """
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
        strategy = requested.get("pairing_strategy", ADJACENT_SOURCE_BUCKETS)
        if strategy not in PAIRING_STRATEGIES:
            raise SignalRefusedError(
                SignalDerivationRefusal(
                    reason=SignalRefusalReason.PARAMETERS_INCOMPLETE,
                    detail=(
                        f"{strategy!r} is not a pairing strategy this extractor "
                        f"implements. Implemented: {sorted(PAIRING_STRATEGIES)}"
                    ),
                )
            )
        raw = requested.get("terms")
        if not isinstance(raw, Sequence) or isinstance(raw, str | bytes):
            raise SignalRefusedError(
                SignalDerivationRefusal(
                    reason=SignalRefusalReason.PARAMETERS_INCOMPLETE,
                    detail=(
                        "`terms` is required and must be a list of source terms. There "
                        "is no default and an empty selection does NOT mean everything: "
                        "one bucket holds hundreds of thousands of terms, and any bound "
                        "on an unselected sweep would be a threshold nobody reviewed"
                    ),
                )
            )
        terms = sorted({str(term) for term in raw})
        if not terms:
            raise SignalRefusedError(
                SignalDerivationRefusal(
                    reason=SignalRefusalReason.PARAMETERS_INCOMPLETE,
                    detail=(
                        "`terms` is empty. An empty selection is a refusal rather than "
                        "a request for everything"
                    ),
                )
            )
        if len(terms) > MAX_SELECTED_TERMS:
            raise SignalRefusedError(
                SignalDerivationRefusal(
                    reason=SignalRefusalReason.PARAMETERS_INCOMPLETE,
                    detail=(
                        f"{len(terms)} terms selected and this extractor's own ceiling "
                        f"is {MAX_SELECTED_TERMS}. The bound is ours, not GDELT's, and "
                        "a selection larger than a person would write by hand is a "
                        "sweep with a list in front of it"
                    ),
                )
            )
        return SignalDerivation(
            extractor_id=self.extractor_id,
            extractor_version=self.extractor_version,
            kind=SignalDerivationKind.DETERMINISTIC,
            required_facts=_REQUIRED_FACTS,
            parameter_names=_PARAMETER_NAMES,
            parameters={"terms": terms, "pairing_strategy": strategy},
        )

    # -------------------------------------------------------------- grouping

    def group_key(
        self, observation: NormalizedObservation, derivation: SignalDerivation
    ) -> str | None:
        """One key per LEXICAL SERIES -- one term, through time.

        The mirror image of `lexical-frequency-contrast`, and the difference is
        the whole distinction between the two extractors:

            contrast   groups by BUCKET and varies the term
            change     groups by TERM and varies the bucket

        So `period_label` is deliberately absent here and `term` is deliberately
        present. Everything else -- source, resource, language scheme and label,
        gram size -- is what makes two observations the same series, and dropping
        any of them would let a different measurement into the subtraction.

        There is no topic, category or theme in this key because none exists. A
        term is a term.
        """
        if observation.record_kind_id != self.record_kind_id:
            return None
        series = observation.section("series")
        language = observation.section("language")
        term = observation.section("term")
        return group_key_of(
            [
                ("source_id", observation.source_id),
                ("record_kind_id", observation.record_kind_id),
                ("series_dataset", series.get("dataset")),
                ("series_resource_id", series.get("resource_id")),
                ("period_type", observation.text("period", "type")),
                ("language_source_scheme", language.get("source_scheme")),
                ("language_source_label", language.get("source_label")),
                ("term_scheme", term.get("scheme")),
                ("gram_size", term.get("gram_size")),
                ("term_text", term.get("text")),
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

        first = group.observations[0] if group.observations else None
        if first is None:
            return GroupOutcome()

        # Normalised in `resolve`, so this is a list of strings by construction.
        # Narrowed rather than asserted: `parameters` is a Mapping[str, object]
        # because an extractor may declare anything.
        stated = derivation.parameters["terms"]
        selected = [str(term) for term in stated] if isinstance(stated, list) else []
        if first.term_text not in selected:
            # Not asked for. Not a refusal: a group nobody selected is not a
            # derivation that failed.
            return GroupOutcome()

        certified = self._certified(group, first)
        if certified is not None:
            return GroupOutcome(refusals=(certified,))

        ordered, ordering_refusal = self._ordered(group)
        if ordering_refusal is not None:
            return GroupOutcome(refusals=(ordering_refusal,))

        if len(ordered) < 2:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS,
                        detail=(
                            f"{len(ordered)} observation(s) of {first.term_text!r} in this "
                            "stream. A change needs two buckets, and a term ABSENT from a "
                            "bucket is absent -- not a frequency of zero"
                        ),
                        group_key=group.key,
                        observation_keys=group.observation_keys,
                    ),
                )
            )

        drafts: list[SignalDraft] = []
        refusals: list[GroupRefusal] = []
        # ADJACENT pairs only. 09:15 -> 09:30 and 09:30 -> 09:45; never
        # 09:15 -> 09:45, which is a different question a strategy would have to
        # ask for.
        for earlier, later in zip(ordered, ordered[1:], strict=False):
            outcome = self._pair(earlier, later, group, derivation, request)
            drafts.extend(outcome.drafts)
            refusals.extend(outcome.refusals)
        return GroupOutcome(drafts=tuple(drafts), refusals=tuple(refusals))

    # ---------------------------------------------------------------- checks

    def _certified(
        self, group: CandidateGroup, first: NormalizedObservation
    ) -> GroupRefusal | None:
        """The Mission 1.12 certification, checked before any comparison.

        §7. The extractor must not infer order from the label's shape. It asks
        whether THIS stream -- this source, this resource -- is certified, and
        whether the certified scheme is the one whose step arithmetic below is
        correct.

        A certification for the same source under a different label scheme is
        refused rather than used: the 15-minute step is a property of the
        scheme, and applying it to another would be wrong silently.
        """
        certification = order_certification(first.source_id, first.resource_id)
        if certification is None:
            return GroupRefusal(
                reason=SignalRefusalReason.REQUIRED_FACT_WITHHELD,
                detail=(
                    f"no temporal order certification covers {first.source_id!r} / "
                    f"{first.resource_id!r}. Ordering is a reviewed finding about a "
                    "publication stream, and a label that sorts is not one. Withheld: "
                    f"{SignalRequiredFact.SOURCE_RELATIVE_ORDER.value}"
                ),
                group_key=group.key,
                observation_keys=group.observation_keys,
            )
        if certification.label_scheme != LABEL_SCHEME:
            return GroupRefusal(
                reason=SignalRefusalReason.REQUIRED_FACT_WITHHELD,
                detail=(
                    f"the certification covering {first.source_id!r} / "
                    f"{first.resource_id!r} is for label scheme "
                    f"{certification.label_scheme!r}; this extractor reads "
                    f"{LABEL_SCHEME!r}. The bucket step is a property of the scheme, and "
                    "applying one scheme's step to another would be wrong silently"
                ),
                group_key=group.key,
                observation_keys=group.observation_keys,
            )
        return None

    def _homogeneous(
        self, group: CandidateGroup, derivation: SignalDerivation
    ) -> GroupRefusal | None:
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
                        f"{observation.observation_key!r} and {first.observation_key!r} "
                        "are not the same lexical series. The term, the source language "
                        "label and scheme, the gram size and the resource must all "
                        "agree: subtracting one term's frequency from another's, or a "
                        "unigram count from a bigram count, produces a number with no "
                        "referent"
                    ),
                    group_key=group.key,
                    observation_keys=group.observation_keys,
                )
        return None

    def _ordered(
        self, group: CandidateGroup
    ) -> tuple[tuple[NormalizedObservation, ...], GroupRefusal | None]:
        """By the certified source label, ascending. Never by row id or arrival.

        The labels are compared as LABELS, in the scheme's own frame. Nothing
        here converts one to an instant, and the sort is on the parsed
        components rather than on the string so a malformed label is caught
        rather than sorted.
        """
        parsed: dict[str, datetime] = {}
        for observation in group.observations:
            moment = _parse_label(observation.period_label)
            if moment is None:
                return (), GroupRefusal(
                    reason=SignalRefusalReason.INPUT_RECORD_INVALID,
                    detail=(
                        f"{observation.period_label!r} is not a "
                        f"{LABEL_SCHEME} label. Ordering is certified for labels of "
                        "this scheme and for nothing else"
                    ),
                    group_key=group.key,
                    observation_keys=group.observation_keys,
                )
            parsed[observation.normalized_record_id] = moment

        labels = [o.period_label for o in group.observations]
        duplicates = sorted({label for label in labels if labels.count(label) > 1})
        if duplicates:
            return (), GroupRefusal(
                reason=SignalRefusalReason.AMBIGUOUS_OBSERVATION_LINEAGE,
                detail=(
                    f"bucket label(s) {duplicates} appear more than once for this term. "
                    "Two rows for one bucket are one observation under two lineages, and "
                    "choosing between them is D-08"
                ),
                group_key=group.key,
                observation_keys=group.observation_keys,
            )

        ordered = sorted(
            group.observations,
            key=lambda o: (parsed[o.normalized_record_id], o.observation_key),
        )
        return tuple(ordered), None

    # ------------------------------------------------------------------ pair

    def _pair(
        self,
        earlier: NormalizedObservation,
        later: NormalizedObservation,
        group: CandidateGroup,
        derivation: SignalDerivation,
        request: DerivationRequest,
    ) -> GroupOutcome:
        # ADJACENCY, and it is the decision ADR-023 records. Computed in LABEL
        # space: one documented step is added to the earlier label's own
        # components and the result is compared as a LABEL. Nothing becomes an
        # instant, nothing acquires an offset, and the arithmetic is licensed by
        # the same certification that licensed the ordering.
        if not _adjacent(earlier.period_label, later.period_label):
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.NON_CONTIGUOUS_SOURCE_BUCKETS,
                        detail=(
                            f"{earlier.period_label} and {later.period_label} are the same "
                            "series and are not one published bucket apart. Bridging them "
                            "would invent continuity across a bucket nobody read, and a "
                            "term absent from the buckets between is ABSENT rather than "
                            "zero"
                        ),
                        group_key=group.key,
                        observation_keys=(
                            earlier.observation_key,
                            later.observation_key,
                        ),
                    ),
                )
            )

        inputs = (earlier.to_input(), later.to_input())
        resolution = earlier.period_type
        if resolution is None:  # pragma: no cover -- _ordered already parsed it
            resolution = inputs[0].period_type

        # The MODEL decides whether these inputs may contribute, from their own
        # quality reasons and the certification. This extractor inspects no
        # quality string.
        assessment = assess_inputs(inputs, derivation, family=self.family, resolution=resolution)
        if assessment.refusal is not None:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=assessment.refusal.reason,
                        detail=assessment.refusal.detail,
                        group_key=group.key,
                        observation_keys=(
                            earlier.observation_key,
                            later.observation_key,
                        ),
                    ),
                )
            )

        before, after = earlier.value, later.value
        if before is None or after is None:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.INPUT_RECORD_INVALID,
                        detail=(
                            "a contributing observation reports a frequency that does not "
                            "read as an exact decimal, which contradicts its own quality "
                            "state"
                        ),
                        group_key=group.key,
                        observation_keys=(
                            earlier.observation_key,
                            later.observation_key,
                        ),
                    ),
                )
            )

        change = after - before
        window = SignalWindow(
            # ORDERED_PERIODS, and this is the first extractor to use it. The
            # buckets are ordered relative to each other; neither is on a shared
            # timeline, so the window carries NO bounds and the row carries no
            # observed_at. H-29 is untouched.
            basis=SignalTemporalBasis.ORDERED_PERIODS,
            period_labels=(earlier.period_label, later.period_label),
            resolution=resolution,
            observation_count=2,
        )
        draft = build_signal(
            workspace_id=request.workspace_id,
            signal_type_id=self.signal_type_id,
            observations=inputs,
            derivation=derivation,
            direction=_direction(change),
            magnitude=_magnitude(change, later),
            derivation_confidence=1.0,
            scope=_scope(earlier),
            window=window,
            derived_at=request.derived_at,
            expires_at=request.expires_at,
            correlation_id=request.correlation_id,
            research_session_id=request.research_session_id,
        )
        return GroupOutcome(drafts=(draft,))


# ------------------------------------------------------------------- helpers


def _parse_label(label: str) -> datetime | None:
    """The label's own components, as a naive value. Never an instant.

    `strptime` with no `tzinfo` and no conversion: the result is a wall-clock
    reading in the scheme's own frame, which is exactly what the label is. It is
    used for ordering and for the step below, and it never reaches a payload, a
    window bound or `observed_at`.
    """
    try:
        return datetime.strptime(label, BUCKET_LABEL_FORMAT)  # noqa: DTZ007
    except (ValueError, TypeError):
        return None


def _adjacent(earlier: str, later: str) -> bool:
    """Whether two labels are exactly one documented bucket apart.

    ADR-023. `earlier + 15 minutes` is formatted back into a LABEL and compared
    as a string, so the comparison happens in label space from end to end. The
    arithmetic is licensed by the Mission 1.12 certification: it is only sound
    because the frame is monotonic, which is what H-32 established.
    """
    start = _parse_label(earlier)
    if start is None:
        return False
    return (start + BUCKET_STEP).strftime(BUCKET_LABEL_FORMAT) == later


def _direction(change: Decimal) -> SignalDirection:
    """Mechanical, from the sign. Never POSITIVE or NEGATIVE: direction is
    change, and change is not sentiment."""
    if change > 0:
        return SignalDirection.INCREASING
    if change < 0:
        return SignalDirection.DECREASING
    return SignalDirection.UNCHANGED


def _magnitude(change: Decimal, observation: NormalizedObservation) -> SignalMagnitude:
    """`ABSOLUTE_CHANGE`, and the contrast between the two lexical extractors is
    the reason the kind exists.

    `lexical-frequency-contrast` measures two terms in ONE bucket and uses
    `ABSOLUTE_DIFFERENCE`, because nothing changed. This measures ONE term
    across two ordered buckets, so something did: the kind a consumer branches
    on has to tell a contrast from a movement, and here it is a movement.

    No percentage and no ratio in V1. Both need a denominator rule -- a term
    going from 0 to 5 has no percentage -- and a rounding rule, and a repeating
    decimal rounded to an unstated precision is fake precision. A difference is
    exact and always defined.

    GDELT publishes four columns and none is a unit, so the state is
    `NOT_ESTABLISHED` -- inherited from the observation rather than named here.
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
    """One term, the source language label and its scheme, and no geography.

    `canonical_language_tags` is absent and the model refuses one anyway while
    H-30 is open. The term is the source text verbatim -- not trimmed, not
    case-folded, not stemmed, not classified.
    """
    language = observation.section("language")
    scheme = language.get("source_scheme")
    label = language.get("source_label")
    return SignalScope(
        source_ids=(observation.source_id,),
        terms=(observation.term_text or "",),
        source_language_labels=(str(label),) if label else (),
        source_language_scheme=str(scheme) if scheme else None,
    )
