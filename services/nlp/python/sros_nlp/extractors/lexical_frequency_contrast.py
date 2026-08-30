"""`lexical-frequency-contrast@1.0.0` -- two terms, one bucket, one language label.

`lexical-frequency-contrast-extractor-v1.md`. Mission 1.11.1 §15-§22.

**What it asserts, in full:** within one source period label and one exact source
language label, these two lexical terms occurred with measured frequencies that
differ by exactly this much.

**What it does not assert:** that one term is more important, more popular, more
in demand, trending, rising or declining. It is a source-frequency relation
between two tokens in text the source processed, and Mission 1.11 §25 lists what
else a term frequency can be -- a news event, a crisis, a celebrity, weather, a
sports fixture.

**H-32 is respected by construction.** Every input must carry the IDENTICAL
source period label, so no ordering between buckets is required, asserted or
possible. There is no frequency change, no growth, no decline and no window.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
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
    SignalMagnitude,
    SignalRefusedError,
    SignalScope,
    SignalWindow,
    assess_inputs,
    build_signal,
)

from ..observations import NormalizedObservation
from .base import CandidateGroup, DerivationRequest, GroupOutcome, GroupRefusal, group_key_of

__all__ = ["TERMS_PER_CONTRAST", "LexicalFrequencyContrastExtractor"]

# Exactly two. A contrast of three is a different assertion with a different
# magnitude shape, and it is a version bump rather than a loosened check.
TERMS_PER_CONTRAST = 2

_PARAMETER_NAMES = frozenset({"terms"})

# `SOURCE_PERIOD_LABEL` and `SOURCE_LANGUAGE_LABEL`, deliberately NOT
# `COMPARABLE_INSTANT` or `CANONICAL_LANGUAGE`. Every GDELT record is PARTIAL
# because H-29 and H-30 are open, and neither missing fact is one this
# derivation needs -- which is the first production proof that PARTIAL does not
# mean unusable (§22).
_REQUIRED_FACTS = frozenset(
    {
        SignalRequiredFact.EXACT_NUMERIC_VALUE,
        SignalRequiredFact.LEXICAL_TERM,
        SignalRequiredFact.SOURCE_PERIOD_LABEL,
        SignalRequiredFact.SOURCE_LANGUAGE_LABEL,
    }
)


class LexicalFrequencyContrastExtractor:
    """Same bucket, same language label, two named terms."""

    extractor_id = "lexical-frequency-contrast"
    extractor_version = "1.0.0"
    signal_type_id = "lexical_frequency_contrast"
    record_kind_id = LEXICAL_FREQUENCY_OBSERVATION
    family = SignalQuantityFamily.LEXICAL_FREQUENCY

    # ------------------------------------------------------------ parameters

    def resolve(self, requested: Mapping[str, object]) -> SignalDerivation:
        """`terms` is REQUIRED, and that is the whole design.

        One WEB-NGRAM file holds hundreds of thousands of rows -- the real
        acquisition read 223,342. An unselected all-pairs sweep over one bucket
        is ~2.5e10 pairs nobody asked for, and every bounded default ("top 100
        by count") is a selection threshold nobody reviewed. So the caller names
        the terms, and the names are fingerprinted like any other parameter.

        Sorted here, in ONE place, so `["weather", "climate"]` and
        `["climate", "weather"]` are the same derivation with the same
        fingerprint (§27).
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
        raw = requested.get("terms")
        if not isinstance(raw, Sequence) or isinstance(raw, str | bytes):
            raise SignalRefusedError(
                SignalDerivationRefusal(
                    reason=SignalRefusalReason.PARAMETERS_INCOMPLETE,
                    detail=(
                        "`terms` is required and must be a list of exactly "
                        f"{TERMS_PER_CONTRAST} source terms. There is no default: an "
                        "unselected sweep over a bucket is quadratic in its term count, "
                        "and any bound on it would be a threshold nobody reviewed"
                    ),
                )
            )
        terms = tuple(str(term) for term in raw)
        if len({*terms}) != TERMS_PER_CONTRAST or len(terms) != TERMS_PER_CONTRAST:
            raise SignalRefusedError(
                SignalDerivationRefusal(
                    reason=SignalRefusalReason.PARAMETERS_INCOMPLETE,
                    detail=(
                        f"`terms` names {len(terms)} term(s), {len({*terms})} distinct; "
                        f"a contrast is between exactly {TERMS_PER_CONTRAST} different "
                        "terms. Contrasting a term with itself is not a derivation"
                    ),
                )
            )
        return SignalDerivation(
            extractor_id=self.extractor_id,
            extractor_version=self.extractor_version,
            kind=SignalDerivationKind.DETERMINISTIC,
            required_facts=_REQUIRED_FACTS,
            parameter_names=_PARAMETER_NAMES,
            parameters={"terms": sorted(terms)},
        )

    # -------------------------------------------------------------- grouping

    def group_key(self, observation: NormalizedObservation) -> str | None:
        """One key per bucket, per exact source language label, per gram size.

        **The period label is EXACT and that is what respects H-32.** Two buckets
        never share a key, so they never meet, so no ordering between them is
        ever needed.

        **The language is the source label and its scheme, never a canonical
        tag.** `ENGLISH` from `cld2-language-name` equals `ENGLISH` from
        `cld2-language-name` and asserts nothing about what either maps to
        (H-30).

        **Gram size separates**, and §19 asks for the decision explicitly: a
        unigram count and a bigram count are counts of different kinds of thing,
        so `climate` (1gram) and `climate change` (2gram) are not comparable
        frequencies. The resource id already differs; the gram size is checked
        as well so a future source publishing both from one resource does not
        silently merge them.
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
                ("period_label", observation.period_label),
                ("language_source_scheme", language.get("source_scheme")),
                ("language_source_label", language.get("source_label")),
                ("term_scheme", term.get("scheme")),
                ("gram_size", term.get("gram_size")),
            ]
        )

    # ---------------------------------------------------------------- derive

    def derive(
        self,
        group: CandidateGroup,
        derivation: SignalDerivation,
        request: DerivationRequest,
    ) -> GroupOutcome:
        homogeneity = self._homogeneous(group)
        if homogeneity is not None:
            return GroupOutcome(refusals=(homogeneity,))

        # The parameter is normalised in `resolve`, so this is a list of two
        # strings by construction. Narrowed rather than asserted: `parameters`
        # is a Mapping[str, object] because an extractor may declare anything.
        stated = derivation.parameters["terms"]
        wanted = [str(term) for term in stated] if isinstance(stated, list) else []
        selected: list[NormalizedObservation] = []
        for term in wanted:
            matches = [o for o in group.observations if o.term_text == term]
            if len(matches) > 1:
                return GroupOutcome(
                    refusals=(
                        GroupRefusal(
                            reason=SignalRefusalReason.AMBIGUOUS_OBSERVATION_LINEAGE,
                            detail=(
                                f"term {term!r} has {len(matches)} normalized rows in this "
                                "bucket. Two rows for one observation is D-08, and counting "
                                "both would manufacture a contrast out of one observation"
                            ),
                            group_key=group.key,
                            observation_keys=group.observation_keys,
                        ),
                    )
                )
            if matches:
                selected.append(matches[0])

        if len(selected) < TERMS_PER_CONTRAST:
            missing = sorted(set(wanted) - {o.term_text for o in selected if o.term_text})
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS,
                        detail=(
                            f"{len(selected)} of {TERMS_PER_CONTRAST} named term(s) are "
                            f"present in this bucket; missing {missing}. A term the source "
                            "did not publish in this bucket is absent, and absence is not "
                            "a frequency of zero"
                        ),
                        group_key=group.key,
                        observation_keys=group.observation_keys,
                    ),
                )
            )

        # By TERM TEXT, ascending, on the source text verbatim. Deterministic and
        # independent of the order a query returned the rows in (§27).
        ordered = tuple(sorted(selected, key=lambda o: (o.term_text or "", o.observation_key)))
        return self._contrast(ordered, group, derivation, request)

    # ---------------------------------------------------------------- checks

    def _homogeneous(self, group: CandidateGroup) -> GroupRefusal | None:
        if not group.observations:
            return None
        first = group.observations[0]
        expected = self.group_key(first)
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
            if self.group_key(observation) != expected:
                return GroupRefusal(
                    reason=SignalRefusalReason.INCOMPATIBLE_SERIES,
                    detail=(
                        f"{observation.observation_key!r} and {first.observation_key!r} do "
                        "not share a bucket, a source language label and a gram size. A "
                        "contrast across buckets would need an ordering H-32 leaves "
                        "unestablished, and one across language labels would need the "
                        "mapping H-30 leaves unestablished"
                    ),
                    group_key=group.key,
                    observation_keys=group.observation_keys,
                )
        return None

    # ------------------------------------------------------------- contrast

    def _contrast(
        self,
        ordered: tuple[NormalizedObservation, ...],
        group: CandidateGroup,
        derivation: SignalDerivation,
        request: DerivationRequest,
    ) -> GroupOutcome:
        first, second = ordered
        inputs = tuple(o.to_input() for o in ordered)
        resolution = first.period_type
        if resolution is None:  # pragma: no cover -- refused by the model below
            resolution = inputs[0].period_type

        assessment = assess_inputs(inputs, derivation, family=self.family, resolution=resolution)
        if assessment.refusal is not None:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=assessment.refusal.reason,
                        detail=assessment.refusal.detail,
                        group_key=group.key,
                        observation_keys=group.observation_keys,
                    ),
                )
            )

        left, right = first.value, second.value
        if left is None or right is None:
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
                        observation_keys=group.observation_keys,
                    ),
                )
            )

        window = SignalWindow(
            # The equality IS the basis. Both inputs carry the identical source
            # label, and the model re-checks that rather than trusting grouping.
            basis=SignalTemporalBasis.SAME_PERIOD_LABEL,
            period_labels=(first.period_label, second.period_label),
            resolution=resolution,
            observation_count=2,
            # No bounds. A SAME_PERIOD_LABEL window carries none, so nothing
            # here can place an unzoned bucket on a timeline (H-29).
        )
        draft = build_signal(
            workspace_id=request.workspace_id,
            signal_type_id=self.signal_type_id,
            observations=inputs,
            derivation=derivation,
            # A same-bucket contrast is not temporal change. Using INCREASING
            # because one term's count is larger would say the frequency rose,
            # which is a statement about time nothing here established (§21).
            direction=SignalDirection.NOT_APPLICABLE,
            magnitude=_magnitude(left - right, first),
            derivation_confidence=1.0,
            scope=_scope(ordered),
            window=window,
            derived_at=request.derived_at,
            expires_at=request.expires_at,
            correlation_id=request.correlation_id,
            research_session_id=request.research_session_id,
        )
        return GroupOutcome(drafts=(draft,))


def _magnitude(difference: Decimal, observation: NormalizedObservation) -> SignalMagnitude:
    """The exact difference between the two frequencies.

    `ABSOLUTE_DIFFERENCE`, never `ABSOLUTE_CHANGE`: nothing changed. Both counts
    were measured in the same bucket, and the temporal kind would assert a
    movement over time that H-32 leaves unestablished.

    A RATIO was considered and rejected. 55/36 does not terminate, so an exact
    Decimal division needs a precision, and a precision nobody stated is the
    fake precision Mission 1.11 §8 forbids. A difference is exact and always
    defined.

    GDELT publishes four columns and none is a unit, so the unit state is
    `NOT_ESTABLISHED` -- inherited from the observation rather than named here.
    """
    published = observation.unit_state == "PUBLISHED" and bool(observation.unit)
    return SignalMagnitude(
        value=difference,
        kind=SignalMagnitudeKind.ABSOLUTE_DIFFERENCE,
        unit=observation.unit if published else None,
        unit_state=(
            SignalMagnitudeUnitState.INHERITED
            if published
            else SignalMagnitudeUnitState.NOT_ESTABLISHED
        ),
    )


def _scope(ordered: tuple[NormalizedObservation, ...]) -> SignalScope:
    """Terms verbatim, source language label and scheme, and no geography.

    `canonical_language_tags` is absent and the model refuses one anyway: a tag
    may only appear where the derivation required `CANONICAL_LANGUAGE` and every
    input supplied it, which no GDELT record does while H-30 is open.
    """
    first = ordered[0]
    language = first.section("language")
    scheme = language.get("source_scheme")
    label = language.get("source_label")
    return SignalScope(
        source_ids=(first.source_id,),
        terms=tuple(o.term_text or "" for o in ordered),
        source_language_labels=(str(label),) if label else (),
        source_language_scheme=str(scheme) if scheme else None,
    )
