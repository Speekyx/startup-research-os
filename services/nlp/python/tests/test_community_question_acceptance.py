"""Mission 1.32 §18. Counting an acceptance state without reading anything into it.

**No network, no database, no model.** Observations are built in the shape
`stack-exchange-question@1.0.0` actually writes, taken from a real normalized
record, so the extractor is exercised against the payload it will meet.

The properties this file exists to protect:

    a missing `has_accepted_answer` is NEVER read as false
    an untagged question is not in the population, whatever else it carries
    the count is of UNACCEPTED questions, not of questions
    the window bounds the counted questions and carries no direction
    a possibly-truncated retrieval is not countable
    one unaccepted question is not a Signal
    and the restatement asserts a SET, never a share of one
"""

from __future__ import annotations

import ast
import pathlib
from datetime import UTC, datetime, timedelta

import pytest
from sros_contracts import (
    NormalizedRecordQuality,
    SignalDirection,
    SignalMagnitudeKind,
    SignalQuantityFamily,
    SignalRefusalReason,
    SignalTemporalBasis,
)
from sros_nlp.extractors import EXTRACTOR_REGISTRY
from sros_nlp.extractors.base import CandidateGroup, DerivationRequest
from sros_nlp.extractors.community_question_without_accepted_answer import (
    CommunityQuestionWithoutAcceptedAnswerExtractor,
)
from sros_nlp.observations import NormalizedObservation
from sros_signal_model import SignalRefusedError

EXTRACTOR_SOURCE = (
    pathlib.Path(__file__).resolve().parents[1]
    / "sros_nlp"
    / "extractors"
    / "community_question_without_accepted_answer.py"
)

MOMENT = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
WORKSPACE = "11111111-1111-1111-1111-111111111111"
SITE = "stackoverflow"
SCHEME = f"stack-exchange-tags:{SITE}"

# The source's own sentence, carried verbatim in every record beside the flag.
# It is the reason this extractor may not say "unsolved", and it is data here so
# the tests reason about what the source published rather than about a paraphrase.
ACCEPTED_SEMANTICS = (
    "the asker marked an answer accepted; not a statement that the problem is objectively resolved"
)


def observation(
    question_id: str,
    created: str,
    *,
    accepted: bool | None = False,
    answers: int = 0,
    tags: tuple[str, ...] = ("docker",),
    scheme: str = SCHEME,
    record_kind_id: str = "community_question",
    quality: NormalizedRecordQuality = NormalizedRecordQuality.VALID,
) -> NormalizedObservation:
    """One normalized question, shaped as `stack-exchange-question@1.0.0` writes it.

    `accepted=None` omits `has_accepted_answer` entirely rather than writing
    null, because that is the case §3 is about: the field is ABSENT, not empty.
    """
    start = datetime.fromisoformat(created).replace(tzinfo=UTC)
    answers_section: dict[str, object] = {
        "count": answers,
        "accepted_answer_id": None,
        "accepted_answer_semantics": ACCEPTED_SEMANTICS,
    }
    if accepted is not None:
        answers_section["has_accepted_answer"] = accepted
    return NormalizedObservation(
        normalized_record_id=f"n-{question_id}",
        raw_record_id=f"r-{question_id}",
        source_id="stack-exchange",
        observation_key=f"stack-exchange|{SITE}|{question_id}",
        record_kind_id=record_kind_id,
        quality=quality,
        quality_reasons=frozenset(),
        payload={
            "record_kind": "community_question",
            "tags": {"scheme": scheme, "values": list(tags)},
            "author": None,
            "period": {
                "type": "INSTANT",
                "label": str(int(start.timestamp())),
                "start": start.isoformat(),
                "end": start.isoformat(),
                "end_inclusive": False,
                "timezone_state": "ESTABLISHED",
            },
            "answers": answers_section,
            "question": {
                "id": question_id,
                "url": f"https://{SITE}.com/questions/{question_id}/x",
                "body": "<p>body</p>",
                "site": SITE,
                "title": "a title",
                "content_licence": "CC BY-SA 4.0",
            },
            "engagement": {
                "score": 1,
                "semantics": (
                    "source counters, carried unpromoted: not importance, not demand, "
                    "not market size"
                ),
                "view_count": 10,
            },
        },
    )


@pytest.fixture
def extractor() -> CommunityQuestionWithoutAcceptedAnswerExtractor:
    return CommunityQuestionWithoutAcceptedAnswerExtractor()


@pytest.fixture
def request_() -> DerivationRequest:
    return DerivationRequest(
        workspace_id=WORKSPACE,
        correlation_id="mission-1.32-test",
        derived_at=MOMENT,
        expires_at=MOMENT + timedelta(days=365),
        research_session_id=None,
    )


def derive(extractor, request_, observations, *, tag="docker", page_size=100):
    derivation = extractor.resolve({"tag": tag, "retrieval_page_size": page_size})
    key = extractor.group_key(observations[0], derivation) or "group"
    group = CandidateGroup(key=key, observations=tuple(observations))
    return extractor.derive(group, derivation, request_)


def refusal(outcome):
    assert not outcome.drafts, "expected a refusal, got a draft"
    assert len(outcome.refusals) == 1
    return outcome.refusals[0]


def draft(outcome):
    assert not outcome.refusals, [r.detail for r in outcome.refusals]
    assert len(outcome.drafts) == 1
    return outcome.drafts[0]


# =========================================================== absence is not false


class TestAMissingFlagIsNotFalse:
    """§3. The single rule most likely to be silently violated."""

    def test_an_absent_flag_refuses_rather_than_counting(self, extractor, request_) -> None:
        outcome = derive(
            extractor,
            request_,
            [
                observation("1", "2024-03-01"),
                observation("2", "2024-03-02"),
                observation("3", "2024-03-03", accepted=None),
            ],
        )
        assert refusal(outcome).reason is SignalRefusalReason.REQUIRED_FACT_WITHHELD

    def test_the_refusal_names_the_records_that_withheld_it(self, extractor, request_) -> None:
        outcome = derive(
            extractor,
            request_,
            [
                observation("1", "2024-03-01"),
                observation("2", "2024-03-02"),
                observation("3", "2024-03-03", accepted=None),
            ],
        )
        assert refusal(outcome).observation_keys == ("stack-exchange|stackoverflow|3",)

    def test_it_refuses_even_though_ignoring_the_record_would_still_count_two(
        self, extractor, request_
    ) -> None:
        """The tempting shortcut: two good records remain, so emit a Signal over
        them. It is refused because the population would then be *the records
        that happened to carry the field*, which is not the population the claim
        names."""
        outcome = derive(
            extractor,
            request_,
            [
                observation("1", "2024-03-01"),
                observation("2", "2024-03-02"),
                observation("3", "2024-03-03", accepted=None),
            ],
        )
        assert "never read as false" in refusal(outcome).detail

    def test_a_non_boolean_value_is_treated_as_absent(self, extractor, request_) -> None:
        odd = observation("3", "2024-03-03", accepted=None)
        odd.payload["answers"]["has_accepted_answer"] = "false"  # a string, not a bool
        outcome = derive(
            extractor,
            request_,
            [observation("1", "2024-03-01"), observation("2", "2024-03-02"), odd],
        )
        assert refusal(outcome).reason is SignalRefusalReason.REQUIRED_FACT_WITHHELD

    def test_an_untagged_record_missing_the_flag_does_not_block(self, extractor, request_) -> None:
        """Withholding matters only inside the population. A question that does
        not carry the tag is not being counted, so its missing flag is not a
        fact this derivation needed."""
        outcome = derive(
            extractor,
            request_,
            [
                observation("1", "2024-03-01"),
                observation("2", "2024-03-02"),
                observation("3", "2024-03-03", accepted=None, tags=("python",)),
            ],
        )
        assert draft(outcome).magnitude.value == 2


# ================================================================ the population


class TestTheCountedPopulation:
    """§2. Exactly the tagged questions whose asker accepted nothing."""

    def test_accepted_questions_are_not_counted(self, extractor, request_) -> None:
        outcome = derive(
            extractor,
            request_,
            [
                observation("1", "2024-03-01"),
                observation("2", "2024-03-02"),
                observation("3", "2024-03-03", accepted=True, answers=3),
            ],
        )
        assert draft(outcome).magnitude.value == 2

    def test_zero_answer_and_answered_unaccepted_are_counted_alike(
        self, extractor, request_
    ) -> None:
        """They are different facts, and this Signal deliberately counts their
        union. `answer-acceptance-semantics-v1.md` records the split precisely
        because the union alone cannot support a solution claim."""
        outcome = derive(
            extractor,
            request_,
            [
                observation("1", "2024-03-01", answers=0),
                observation("2", "2024-03-02", answers=4),
            ],
        )
        assert draft(outcome).magnitude.value == 2

    def test_a_question_without_the_tag_is_outside_the_population(
        self, extractor, request_
    ) -> None:
        outcome = derive(
            extractor,
            request_,
            [
                observation("1", "2024-03-01"),
                observation("2", "2024-03-02"),
                observation("3", "2024-03-03", tags=("kubernetes",)),
            ],
        )
        assert draft(outcome).magnitude.value == 2

    def test_the_tag_is_matched_among_several_the_question_carries(
        self, extractor, request_
    ) -> None:
        outcome = derive(
            extractor,
            request_,
            [
                observation("1", "2024-03-01", tags=("node.js", "docker", "telegraf")),
                observation("2", "2024-03-02", tags=("docker", "docker-network")),
            ],
        )
        assert draft(outcome).magnitude.value == 2

    def test_one_unaccepted_question_is_not_a_signal(self, extractor, request_) -> None:
        """A Signal is a derivation over two or more observations."""
        outcome = derive(
            extractor,
            request_,
            [observation("1", "2024-03-01"), observation("2", "2024-03-02", accepted=True)],
        )
        assert refusal(outcome).reason is SignalRefusalReason.INSUFFICIENT_INPUT_OBSERVATIONS

    def test_the_magnitude_is_a_count_and_carries_no_unit(self, extractor, request_) -> None:
        magnitude = draft(
            derive(
                extractor,
                request_,
                [observation("1", "2024-03-01"), observation("2", "2024-03-02")],
            )
        ).magnitude
        assert magnitude.kind is SignalMagnitudeKind.OBSERVATION_COUNT
        assert magnitude.unit is None


# =================================================================== truncation


class TestTruncationIsRefused:
    """A subset of a truncated retrieval is no more countable than the retrieval."""

    def test_a_full_page_refuses(self, extractor, request_) -> None:
        rows = [observation(str(i), "2024-03-01") for i in range(4)]
        outcome = derive(extractor, request_, rows, page_size=4)
        assert refusal(outcome).reason is SignalRefusalReason.REQUIRED_FACT_WITHHELD
        assert "may have been truncated" in refusal(outcome).detail

    def test_the_bound_is_the_whole_retrieval_not_the_counted_subset(
        self, extractor, request_
    ) -> None:
        """Three of four are unaccepted. The subset is under the bound and the
        retrieval is not, and it is the retrieval that decides."""
        rows = [
            observation("1", "2024-03-01"),
            observation("2", "2024-03-02"),
            observation("3", "2024-03-03"),
            observation("4", "2024-03-04", accepted=True),
        ]
        assert refusal(derive(extractor, request_, rows, page_size=4)).reason is (
            SignalRefusalReason.REQUIRED_FACT_WITHHELD
        )

    def test_a_page_size_is_required(self, extractor) -> None:
        with pytest.raises(SignalRefusedError):
            extractor.resolve({"tag": "docker"})

    def test_a_tag_is_required(self, extractor) -> None:
        with pytest.raises(SignalRefusedError):
            extractor.resolve({"retrieval_page_size": 100})

    def test_an_unknown_parameter_is_refused(self, extractor) -> None:
        with pytest.raises(SignalRefusedError):
            extractor.resolve({"tag": "docker", "retrieval_page_size": 100, "min_score": 1})


# ==================================================================== the window


class TestTheWindowBoundsAndNeverDirects:
    """§5. The questions carry creation instants; the flag is observed late."""

    def test_the_window_has_no_temporal_basis(self, extractor, request_) -> None:
        """NONE. Membership in one window, never an order across two."""
        signal = draft(
            derive(
                extractor,
                request_,
                [observation("1", "2024-03-01"), observation("2", "2024-03-05")],
            )
        )
        assert signal.window.basis is SignalTemporalBasis.NONE

    def test_the_direction_is_not_applicable(self, extractor, request_) -> None:
        signal = draft(
            derive(
                extractor,
                request_,
                [observation("1", "2024-03-01"), observation("2", "2024-03-05")],
            )
        )
        assert signal.direction is SignalDirection.NOT_APPLICABLE

    def test_the_window_bounds_the_counted_questions_only(self, extractor, request_) -> None:
        """The accepted question falls outside the labels, which is exactly why
        the restatement may not present the count as a share of that span."""
        signal = draft(
            derive(
                extractor,
                request_,
                [
                    observation("1", "2024-03-02"),
                    observation("2", "2024-03-04"),
                    observation("3", "2024-03-09", accepted=True),
                ],
            )
        )
        instants = [
            int(datetime.fromisoformat(d).replace(tzinfo=UTC).timestamp())
            for d in ("2024-03-02", "2024-03-04")
        ]
        assert signal.window.period_labels == tuple(str(i) for i in instants)
        assert signal.window.observation_count == 2

    def test_a_naive_timestamp_is_refused(self, extractor, request_) -> None:
        naive = observation("2", "2024-03-02")
        naive.payload["period"]["start"] = "2024-03-02T00:00:00"
        outcome = derive(extractor, request_, [observation("1", "2024-03-01"), naive])
        assert refusal(outcome).reason is SignalRefusalReason.REQUIRED_FACT_WITHHELD

    def test_a_duplicated_observation_key_is_refused(self, extractor, request_) -> None:
        outcome = derive(
            extractor,
            request_,
            [observation("1", "2024-03-01"), observation("1", "2024-03-02")],
        )
        assert refusal(outcome).reason is SignalRefusalReason.AMBIGUOUS_OBSERVATION_LINEAGE


# ============================================================ the scope and family


class TestScopeAndFamily:
    def test_the_scope_carries_the_site_and_the_tag_the_site_owns(
        self, extractor, request_
    ) -> None:
        scope = draft(
            derive(
                extractor,
                request_,
                [observation("1", "2024-03-01"), observation("2", "2024-03-02")],
            )
        ).scope
        assert scope.community_sites == (SITE,)
        assert scope.community_tags == ("docker",)
        assert scope.community_tag_scheme == SCHEME

    def test_it_reuses_the_existing_quantity_family(self, extractor) -> None:
        """§7. A different measurement over the same kind of quantity. ADR-034's
        family already describes it, and a second family for a second count
        would say these numbers are incommensurable when they are not."""
        assert extractor.family is SignalQuantityFamily.COMMUNITY_QUESTION_VOLUME

    def test_it_is_registered_under_its_own_signal_type(self, extractor) -> None:
        assert extractor.signal_type_id == "community_question_without_accepted_answer_volume"
        assert isinstance(EXTRACTOR_REGISTRY[extractor.extractor_id], type(extractor))

    def test_two_sites_are_never_one_group(self, extractor) -> None:
        one = extractor.group_key(
            observation("1", "2024-03-01"),
            extractor.resolve({"tag": "docker", "retrieval_page_size": 100}),
        )
        two = extractor.group_key(
            observation("2", "2024-03-01", scheme="stack-exchange-tags:serverfault"),
            extractor.resolve({"tag": "docker", "retrieval_page_size": 100}),
        )
        assert one != two

    def test_a_record_of_another_kind_has_no_key(self, extractor) -> None:
        assert extractor.group_key(
            observation("1", "2024-03-01", record_kind_id="web_page"),
            extractor.resolve({"tag": "docker", "retrieval_page_size": 100}),
        ) is (None)


# ======================================================= what the code may not do


class TestTheExtractorReachesNothing:
    """§16. Deterministic, offline, and provably so."""

    def _imports(self) -> set[str]:
        tree = ast.parse(EXTRACTOR_SOURCE.read_text(encoding="utf-8"))
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module or "")
        return names

    def test_it_imports_no_client_no_model_and_no_database(self) -> None:
        forbidden = ("httpx", "requests", "psycopg", "sqlalchemy", "openai", "anthropic")
        for name in self._imports():
            assert not any(name.startswith(f) for f in forbidden), name

    def test_it_reaches_no_gateway_and_no_parked_classifier(self) -> None:
        for name in self._imports():
            assert "gateway" not in name, name
            assert "semantic_equivalence" not in name, name

    def test_it_never_claims_the_problem_is_unsolved(self) -> None:
        """The docstring is where a future reader looks for permission, so the
        refusals are written there and this keeps them there."""
        # Whitespace-normalised, because these sentences are wrapped in the
        # docstring and a line break must not be what decides whether the
        # refusal is present.
        text = " ".join(EXTRACTOR_SOURCE.read_text(encoding="utf-8").split())
        assert "Not that any problem is unsolved" in text
        assert "Not that anybody is dissatisfied" in text
        assert "that anyone would pay" in text
        assert "parked" in text

    def test_it_names_acceptance_as_one_person_s_action(self) -> None:
        text = EXTRACTOR_SOURCE.read_text(encoding="utf-8")
        assert "ONE PERSON'S ACTION" in text
        assert "Only the asker may accept" in text
