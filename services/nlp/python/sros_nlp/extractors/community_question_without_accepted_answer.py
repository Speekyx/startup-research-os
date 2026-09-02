"""`community-question-without-accepted-answer@1.0.0` -- an acceptance state, counted.

Mission 1.32, `answer-acceptance-semantics-v1.md`.

**What it asserts, in full:** exactly this many public questions carrying one tag
from one community site's own vocabulary, created inside one bounded window, had
no accepted answer at the source state SROS observed.

**What it does not assert, and the list is the reason this extractor is written
so narrowly.** Not that any problem is unsolved -- the normalizer says so in the
payload itself, beside the value: *"the asker marked an answer accepted; not a
statement that the problem is objectively resolved"*. Not that anybody is
dissatisfied; nobody in these records evaluates anything. Not that existing tools
are inadequate, that a commercial gap exists, that anyone would pay, or that any
two of these questions concern the same problem -- that last is the relation
Mission 1.27 **parked**.

**Acceptance is ONE PERSON'S ACTION.** Only the asker may accept, so a `false`
here reports a decision by exactly one participant. An asker who solved the
problem elsewhere, lost interest, or never returned leaves it `false` whatever
answers arrived.

**The state is OBSERVED LATE and the wording must say so.** The questions carry
their own creation instants; the acceptance flag is whatever it was when SROS
collected the record. A claim phrased *"N had no accepted answer during March"*
would be false. The claim this feeds says *at the observed source state*, and the
window and the observation are named separately.

**A missing flag is not `false`** (§3). A record whose payload omits
`has_accepted_answer` withholds the fact rather than supplying a negative, and the
derivation refuses rather than counting it as unaccepted -- the same rule ADR-023
applied to an absent lexical term, one field along.

**Completeness is a precondition**, exactly as for `community-question-volume`:
the caller supplies the retrieval's page size and this refuses unless the count
came back short of it. A subset of a truncated retrieval is no more countable
than the retrieval was.
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
from .community_question_volume import PAGE_SIZE_PARAMETER, TAG_PARAMETER, _tags_of

__all__ = ["CommunityQuestionWithoutAcceptedAnswerExtractor"]

_PARAMETER_NAMES = frozenset({TAG_PARAMETER, PAGE_SIZE_PARAMETER})

# As for the volume extractor: no `EXACT_NUMERIC_VALUE`, because a question
# carries no measured value and the count is a property of the group.
_REQUIRED_FACTS = frozenset({SignalRequiredFact.COMPARABLE_INSTANT})


class CommunityQuestionWithoutAcceptedAnswerExtractor:
    """A count of tagged questions with no accepted answer at the observed state."""

    extractor_id = "community-question-without-accepted-answer"
    extractor_version = "1.0.0"
    signal_type_id = "community_question_without_accepted_answer_volume"
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
                        f"{TAG_PARAMETER!r} is required and has no default, for the reason "
                        "the volume extractor gives: a sweep over every tag would emit a "
                        "signal for subjects nobody asked about"
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
                        "integer. A subset of a possibly-truncated retrieval is no more "
                        "countable than the retrieval was"
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
        """One key per SITE and TAG VOCABULARY, as for the volume extractor.

        The tag and the acceptance state are both applied as FILTERS inside
        `derive`: a question carries several tags, so keying on one would put a
        record in several groups.
        """
        if observation.record_kind_id != self.record_kind_id:
            return None
        tags = observation.section("tags")
        return group_key_of(
            [
                ("source_id", observation.source_id),
                ("record_kind_id", observation.record_kind_id),
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

        tagged = tuple(o for o in group.observations if tag in _tags_of(o))

        # §3. A record that does not carry the flag WITHHOLDS the fact. Counting
        # it as unaccepted would manufacture the very number this measures, so
        # the derivation refuses instead -- an absent value is never a negative.
        withheld = [o.observation_key for o in tagged if _acceptance_of(o) is None]
        if withheld:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.REQUIRED_FACT_WITHHELD,
                        detail=(
                            f"{len(withheld)} question(s) carry no `has_accepted_answer` "
                            "value. An absent flag withholds the fact and is never read as "
                            "false; counting it as unaccepted would manufacture the number "
                            "this derivation measures"
                        ),
                        group_key=group.key,
                        observation_keys=tuple(sorted(withheld)),
                    ),
                )
            )

        if len(group.observations) >= page_size:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.REQUIRED_FACT_WITHHELD,
                        detail=(
                            f"{len(group.observations)} records arrived on one page of size "
                            f"{page_size}. A retrieval at or above its own bound may have "
                            "been truncated, and a subset of a truncated retrieval is no "
                            "more countable than the retrieval was"
                        ),
                        group_key=group.key,
                        observation_keys=group.observation_keys,
                    ),
                )
            )

        unaccepted = tuple(o for o in tagged if _acceptance_of(o) is False)
        if len(unaccepted) < 2:
            return GroupOutcome(
                refusals=(
                    GroupRefusal(
                        reason=SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS,
                        detail=(
                            f"{len(unaccepted)} question(s) carry the tag {tag!r} with no "
                            "accepted answer. A count is a derivation over two or more "
                            "observations"
                        ),
                        group_key=group.key,
                        observation_keys=group.observation_keys,
                    ),
                )
            )

        ordered, refusal = self._ordered(unaccepted, group)
        if refusal is not None:
            return GroupOutcome(refusals=(refusal,))

        inputs = tuple(o.to_input() for o in ordered)
        keys = tuple(o.observation_key for o in ordered)
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
            # NONE. One count over one window, related by membership and not by
            # order. Nothing here may be read as a change.
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
            direction=SignalDirection.NOT_APPLICABLE,
            derivation_confidence=1.0,
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
                        f"{observation.observation_key!r} and {first.observation_key!r} "
                        "are not questions from the same site and tag vocabulary"
                    ),
                    group_key=group.key,
                    observation_keys=group.observation_keys,
                )
        return None

    def _ordered(
        self, observations: Sequence[NormalizedObservation], group: CandidateGroup
    ) -> tuple[tuple[NormalizedObservation, ...], GroupRefusal | None]:
        """By creation instant, then observation key, so identity is reproducible."""
        starts: dict[str, datetime] = {}
        for observation in observations:
            start = observation.period_start
            if start is None or start.tzinfo is None:
                return (), GroupRefusal(
                    reason=SignalRefusalReason.REQUIRED_FACT_WITHHELD,
                    detail=(
                        f"{observation.observation_key!r} has no timezone-aware canonical "
                        "period start, so it cannot be placed in a bounded window"
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
                    f"observation key(s) {duplicates} appear more than once; counting both "
                    "would inflate the count by a normalizer upgrade"
                ),
                group_key=group.key,
                observation_keys=group.observation_keys,
            )
        return (
            tuple(
                sorted(
                    observations, key=lambda o: (starts[o.normalized_record_id], o.observation_key)
                )
            ),
            None,
        )


def _acceptance_of(observation: NormalizedObservation) -> bool | None:
    """The acceptance flag, or None where the record does not carry one.

    **None is not False.** A record omitting the field withholds the fact, and
    the caller refuses rather than counting it as unaccepted.
    """
    value = observation.section("answers").get("has_accepted_answer")
    return value if isinstance(value, bool) else None


def _scope(observation: NormalizedObservation, tag: str) -> SignalScope:
    scheme = observation.section("tags").get("scheme")
    scheme_text = str(scheme) if isinstance(scheme, str) else ""
    site = scheme_text.split(":", 1)[1] if ":" in scheme_text else ""
    return SignalScope(
        source_ids=(observation.source_id,),
        community_sites=(site,) if site else (),
        community_tags=(tag,),
        community_tag_scheme=scheme_text or None,
    )
