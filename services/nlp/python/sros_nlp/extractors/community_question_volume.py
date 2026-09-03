"""`community-question-volume@1.0.0` -- how many questions a site filed under one tag.

Mission 1.30, ADR-034.

**What it asserts, in full:** exactly this many public questions carrying one
identifier from one community site's own tag vocabulary were created on that site
inside one bounded window, counted over records this deployment holds.

**What it does not assert.** How many PEOPLE: author identity is never acquired
(Mission 1.18), so distinct askers cannot be counted and one person may have
asked several times. That the questions share a problem: that is
`SAME_PROBLEM_FAMILY`, which Mission 1.27 **parked**, and this extractor operates
without it and must never look like it answered it. Recurrence, frequency in the
world, severity, difficulty, whether anything is unsolved, demand, adoption,
buyers, market size or willingness to pay: none of those is measured by anybody
publishing a question.

**A tag is a SUBJECT, not a problem** (Mission 1.18). It identifies the area a
question was filed under, in the site's own vocabulary, and nothing finer. The
scope records the scheme for exactly that reason.

**Completeness is a PRECONDITION, not a caveat.** A count is meaningless if the
retrieval that produced it was truncated by our own bound, so this refuses rather
than qualifying: `RETRIEVAL_MAY_BE_TRUNCATED` produces no Signal at all. That is
ADR-021's rule -- a blocked derivation produces no Signal, never a Signal with a
warning attached -- applied to a failure mode counting introduces and change
never had.

**The completeness proof is structural, and the caller supplies its inputs
rather than its verdict.** An extractor never reads a RawRecord, so the page
facts cannot come from the observations: the caller passes `retrieval_page_size`,
and THIS decides. If the count came back SHORT of the page size the result set
was exhausted, because a full page would have been exactly `page_size`. A count
at or above it is refused.

That split is the point. A caller handing over a number is doing something a
caller handing over a verdict is not, and the number enters the parameter
fingerprint -- so a signal derived under a different claimed bound is a different
signal rather than the same one with a different story.

**A truncated count is not merely imprecise, it is anti-informative.** If a
retrieval capped at 100 returns 100, the magnitude is OUR BOUND and carries no
information about the world at all -- and it would read as a larger number than a
complete count of 89. That is why this refuses instead of reporting a floor.

**One count over one window is not a change and is not a trend.** The window
basis is `NONE`: nothing here is ordered, compared across periods, or read as
movement. A second window would be a second Signal, and comparing them would be a
different derivation with its own decisions about what a gap means.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal

from sros_contracts import (
    NormalizedPeriodType,
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
    COMMUNITY_QUESTION,
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

__all__ = ["CommunityQuestionVolumeExtractor", "PAGE_SIZE_PARAMETER", "TAG_PARAMETER"]

#: The tag to count is a REQUIRED parameter, never a default.
#:
#: One month of Stack Overflow carries thousands of tags, and a sweep over all of
#: them would emit a Signal per tag whether or not anybody had asked a question
#: about that subject -- the same objection that made `terms` required for the
#: lexical contrast in Mission 1.11.1. It also keeps the derivation honest about
#: what it counted: a tag chosen by the caller appears in the parameter
#: fingerprint and therefore in the signal's identity.
TAG_PARAMETER = "tag"

#: The page size the retrieval asked for, supplied by the caller from the
#: acquisition provenance. Required: without it, whether the count is the
#: window's or our bound's cannot be established, and a count that might be
#: our own ceiling is not a count.
PAGE_SIZE_PARAMETER = "retrieval_page_size"

_PARAMETER_NAMES = frozenset({TAG_PARAMETER, PAGE_SIZE_PARAMETER})

# Declared once. Note what is NOT here: `EXACT_NUMERIC_VALUE`. A question carries
# no measured value -- there is nothing to read out of it -- and the count is a
# property of the GROUP rather than of any member. A derivation asking for it
# would be refused by the MODEL, because `community_question` does not supply it.
_REQUIRED_FACTS = frozenset({SignalRequiredFact.COMPARABLE_INSTANT})


class CommunityQuestionVolumeExtractor:
    """A count of questions filed under one site tag inside one bounded window."""

    extractor_id = "community-question-volume"
    extractor_version = "1.0.0"
    signal_type_id = "community_question_volume"
    record_kind_id = COMMUNITY_QUESTION
    family = SignalQuantityFamily.COMMUNITY_QUESTION_VOLUME

    # ------------------------------------------------------------ parameters

    def resolve(self, requested: Mapping[str, object]) -> SignalDerivation:
        tag = requested.get(TAG_PARAMETER)
        if not isinstance(tag, str) or not tag.strip():
            raise SignalRefusedError(
                SignalDerivationRefusal(
                    reason=SignalRefusalReason.PARAMETERS_INCOMPLETE,
                    detail=(
                        f"{TAG_PARAMETER!r} is required and has no default. A sweep over "
                        "every tag a site publishes would emit a signal for subjects "
                        "nobody asked about, and the tag counted belongs in the "
                        "derivation identity"
                    ),
                )
            )
        page_size = requested.get(PAGE_SIZE_PARAMETER)
        if isinstance(page_size, bool) or not isinstance(page_size, int) or page_size < 1:
            raise SignalRefusedError(
                SignalDerivationRefusal(
                    reason=SignalRefusalReason.PARAMETERS_INCOMPLETE,
                    detail=(
                        f"{PAGE_SIZE_PARAMETER!r} is required and must be a positive "
                        "integer. It is the bound the retrieval asked for, and without it "
                        "a count cannot be told apart from our own ceiling"
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
            parameters={TAG_PARAMETER: tag, PAGE_SIZE_PARAMETER: page_size},
        )

    # -------------------------------------------------------------- grouping

    def group_key(self, observation: NormalizedObservation) -> str | None:
        """One key per SITE and TAG VOCABULARY.

        The tag itself is deliberately NOT in the key. A question carries several
        tags, so grouping by tag would put one record in several groups and the
        same record would contribute to several counts -- which is correct for
        counting, and wrong for a group key, whose job is to say which records
        could meet. The tag is applied as a FILTER inside `derive`, from the
        parameter, so the count is over records the group already contains.

        The site IS in the key: the same tag string means different things on
        different sites, and a group that mixed them would count two
        vocabularies as one.
        """
        if observation.record_kind_id != self.record_kind_id:
            return None
        tags = observation.section("tags")
        return group_key_of(
            [
                ("source_id", observation.source_id),
                ("record_kind_id", observation.record_kind_id),
                # The scheme IS the site discriminator: it is
                # `stack-exchange-tags:<site>`, so one key covers both and
                # there is no second field to fall out of step with it.
                ("tag_scheme", tags.get("scheme")),
            ]
        )

    # ---------------------------------------------------------------- derive

    def derive(
        self,
        group: CandidateGroup,
        derivation: SignalDerivation,
        request: DerivationRequest,
    ) -> GroupOutcome:
        tag = str(derivation.parameters[TAG_PARAMETER])

        raw_page_size = derivation.parameters[PAGE_SIZE_PARAMETER]
        page_size = raw_page_size if isinstance(raw_page_size, int) else 0

        homogeneity = self._homogeneous(group)
        if homogeneity is not None:
            return GroupOutcome(refusals=(homogeneity,))

        matching = tuple(
            observation for observation in group.observations if tag in _tags_of(observation)
        )
        if len(matching) < 2:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS,
                        detail=(
                            f"{len(matching)} question(s) carry the tag {tag!r}. A count is "
                            "a derivation over two or more observations; one question "
                            "restated is that question renamed"
                        ),
                        group_key=group.key,
                        observation_keys=group.observation_keys,
                    ),
                )
            )

        truncation = self._retrieval_is_complete(group, page_size)
        if truncation is not None:
            return GroupOutcome(refusals=(truncation,))

        ordered, ordering_refusal = self._ordered(matching, group)
        if ordering_refusal is not None:
            return GroupOutcome(refusals=(ordering_refusal,))

        inputs = tuple(observation.to_input() for observation in ordered)
        keys = tuple(observation.observation_key for observation in ordered)
        # Every community question is an INSTANT: Stack Exchange publishes a
        # Unix epoch second, which Mission 1.18 established as the first
        # ESTABLISHED period in this repository.
        resolution = NormalizedPeriodType.INSTANT
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

        first, last = ordered[0], ordered[-1]
        window = SignalWindow(
            # NONE, deliberately. One count over one window relates its members
            # by membership and not by order, so nothing here may be read as a
            # change -- and a basis that claimed an order would license a
            # direction the derivation never established.
            basis=SignalTemporalBasis.NONE,
            period_labels=(first.period_label, last.period_label),
            resolution=resolution,
            observation_count=len(ordered),
        )
        draft = build_signal(
            workspace_id=request.workspace_id,
            signal_type_id=self.signal_type_id,
            observations=inputs,
            derivation=derivation,
            # NOT_APPLICABLE, and the model enforces it: a direction is a
            # statement about before and after, and a count has neither.
            direction=SignalDirection.NOT_APPLICABLE,
            # DETERMINISTIC counting over exact records. It says the count is
            # right, not that anything about the world is.
            derivation_confidence=1.0,
            # OBSERVATION_COUNT already existed and is exactly this: how many
            # observations satisfied the derivation's condition. The model
            # requires it DIMENSIONLESS, which is right -- "89 questions" carries
            # its unit in the signal TYPE, and a unit string here would claim the
            # source published one.
            magnitude=SignalMagnitude(
                value=Decimal(len(ordered)),
                kind=SignalMagnitudeKind.OBSERVATION_COUNT,
                unit=None,
                unit_state=SignalMagnitudeUnitState.DIMENSIONLESS,
            ),
            scope=_scope(first, tag),
            window=window,
            derived_at=request.derived_at,
            expires_at=request.expires_at,
            correlation_id=request.correlation_id,
            research_session_id=request.research_session_id,
        )
        return GroupOutcome(drafts=(draft,))

    # ---------------------------------------------------------------- checks

    def _homogeneous(self, group: CandidateGroup) -> GroupRefusal | None:
        """Refuse a group whose members are not one site and one vocabulary."""
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
                        f"{observation.observation_key!r} and {first.observation_key!r} are "
                        "not questions from the same site and tag vocabulary. The same tag "
                        "string means different things on different sites, and a count "
                        "across two vocabularies is two counts wearing one name"
                    ),
                    group_key=group.key,
                    observation_keys=group.observation_keys,
                )
        return None

    def _retrieval_is_complete(self, group: CandidateGroup, page_size: int) -> GroupRefusal | None:
        """Refuse unless the retrieval demonstrably did not truncate.

        A SHORT page proves exhaustion: a full page would have been exactly
        `page_size`, so fewer than that means the source had nothing more to
        give. At or above it, the magnitude would be our own bound rather than
        the window's content -- which is not a weaker fact, it is a different
        one, and it would read as a larger number than a complete count.

        The comparison is against the GROUP, not against the tag-matching
        subset: the bound applied to the retrieval, and every record it returned
        counts toward whether that retrieval was full.
        """
        retrieved = len(group.observations)
        if retrieved >= page_size:
            return GroupRefusal(
                reason=SignalRefusalReason.REQUIRED_FACT_WITHHELD,
                detail=(
                    f"{retrieved} record(s) were retrieved against a page size of "
                    f"{page_size}. A retrieval at or above its own bound may have been "
                    "truncated, so this count would be of what the bound allowed through "
                    "rather than of what the window holds"
                ),
                group_key=group.key,
                observation_keys=group.observation_keys,
            )
        return None

    def _ordered(
        self, observations: Sequence[NormalizedObservation], group: CandidateGroup
    ) -> tuple[tuple[NormalizedObservation, ...], GroupRefusal | None]:
        """By creation instant, ascending, then by observation key.

        Input order enters the derivation identity, so an order that came from
        the database would make the identity depend on a plan the query
        optimiser chose. The ORDER is not part of what the signal asserts -- the
        window basis is NONE -- it is only what makes the identity reproducible.
        """
        starts: dict[str, datetime] = {}
        for observation in observations:
            start = observation.period_start
            if start is None or start.tzinfo is None:
                return (), GroupRefusal(
                    reason=SignalRefusalReason.REQUIRED_FACT_WITHHELD,
                    detail=(
                        f"{observation.observation_key!r} has no timezone-aware canonical "
                        "period start, so it cannot be placed in a bounded window. "
                        f"Withheld: {SignalRequiredFact.COMPARABLE_INSTANT.value}"
                    ),
                    group_key=group.key,
                    observation_keys=group.observation_keys,
                )
            starts[observation.normalized_record_id] = start

        keys = [o.observation_key for o in observations]
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        if duplicates:
            return (), GroupRefusal(
                reason=SignalRefusalReason.AMBIGUOUS_OBSERVATION_LINEAGE,
                detail=(
                    f"observation key(s) {duplicates} appear more than once. Two rows for "
                    "one question are one observation under two lineages, and counting "
                    "both would inflate the count by a normalizer upgrade"
                ),
                group_key=group.key,
                observation_keys=group.observation_keys,
            )

        ordered = sorted(
            observations,
            key=lambda o: (starts[o.normalized_record_id], o.observation_key),
        )
        return tuple(ordered), None


def _tags_of(observation: NormalizedObservation) -> tuple[str, ...]:
    """The site's own tag list, verbatim.

    Read from the record's `tags.values` and never from the acquisition query.
    Mission 1.30 found a question returned by a `tagged=docker` query whose own
    tag list does not contain `docker`, so *what the query asked for* and *what
    the site says* are different facts. The site's answer is the one a claim
    about the site's tag can rest on.
    """
    values = observation.section("tags").get("values")
    if not isinstance(values, (list, tuple)):
        return ()
    return tuple(str(value) for value in values)


def _scope(observation: NormalizedObservation, tag: str) -> SignalScope:
    """The site comes from the tag SCHEME, split on a format this repository owns.

    The payload has no `site` field; the scheme is `stack-exchange-tags:<site>`,
    a string the normalizer constructs. Splitting our own format is
    deterministic; guessing at a scheme of another shape would not be, so an
    unrecognised scheme yields no site and the model refuses the signal.
    """
    scheme = observation.section("tags").get("scheme")
    scheme_text = str(scheme) if isinstance(scheme, str) else ""
    site = scheme_text.split(":", 1)[1] if ":" in scheme_text else ""
    return SignalScope(
        source_ids=(observation.source_id,),
        community_sites=(site,) if site else (),
        community_tags=(tag,),
        community_tag_scheme=scheme_text or None,
    )
