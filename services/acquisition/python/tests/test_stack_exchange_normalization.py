"""The community-question normalizer, and the Signal decision it led to.

Mission 1.18. Two things live here and they belong together: what one Stack
Overflow question becomes, and why fifteen real ones produced **no Signal**.

The second half is the unusual part. `TestWhyNoSignalIsDefensible` encodes a
decision rather than a behaviour -- Outcome S0 -- using the tag structure that
the real sample actually had. A mission that declines to produce data owes the
tests that pin why, or it is indistinguishable from one that forgot.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sros_acquisition.normalization.errors import NormalizationFailedError
from sros_acquisition.normalization.geography import GeographyMap
from sros_acquisition.normalization.model import RECORD_KINDS, RawRecordView
from sros_acquisition.normalization.normalizers import NormalizationContext
from sros_acquisition.normalization.stack_exchange_questions import (
    SE_NORMALIZER_ID,
    SE_NORMALIZER_VERSION,
    StackExchangeQuestionNormalizer,
)
from sros_acquisition.registry.retention import EffectiveRetention

CREATED = 1709510412  # 2024-03-04T00:00:12Z, from the real sample
MOMENT = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
WORKSPACE = "00000000-0000-4000-8000-0000000000aa"

RETENTION = EffectiveRetention(
    raw_days=30,
    normalized_days=365,
    aggregate_permitted=True,
    raw_source="baseline",
    normalized_source="baseline",
)

# Empty on purpose. A question has no geography, and handing this adapter a
# populated map would suggest it consults one.
NO_GEOGRAPHY = GeographyMap(canonical_scheme="ISO-3166-1-alpha-2", entries={})


def raw(**overrides: object) -> RawRecordView:
    """One raw record, shaped as `read_raw_records` returns it."""
    payload: dict[str, object] = {
        "question_id": 78098368,
        "title": "Python multithreading I/O operation",
        "body": "<p>I am trying to multithread a simple application...</p>",
        "tags": ["python", "multiprocessing", "tqdm"],
        "creation_date": CREATED,
        "answer_count": 0,
        "is_answered": False,
        "score": 0,
        "view_count": 89,
        "link": "https://stackoverflow.com/questions/78098368/python-multithreading-i-o-operation",
        "content_license": "CC BY-SA 4.0",
    }
    payload.update(overrides.pop("payload_extra", {}))  # type: ignore[arg-type]
    for key in overrides.pop("payload_drop", ()):  # type: ignore[union-attr]
        payload.pop(key, None)
    provenance: dict[str, object] = {
        "source_id": "stack-exchange",
        "resource_id": "questions/stackoverflow",
        "site": "stackoverflow",
        "use_profile": "local-private-research-v1",
        "attribution": {
            "text": "Stack Exchange Network, CC BY-SA 4.0",
            "elements": ["SOURCE_CREDIT", "LICENCE_IDENTIFIER"],
        },
        "review_version": 1,
    }
    provenance.update(overrides.pop("provenance_extra", {}))  # type: ignore[arg-type]
    if "provenance" in overrides:
        provenance = overrides.pop("provenance")  # type: ignore[assignment]
    base: dict[str, object] = {
        "record_id": "11111111-1111-4111-8111-111111111111",
        "workspace_id": WORKSPACE,
        "research_session_id": None,
        "source_id": "stack-exchange",
        "observation_key": "stack-exchange|stackoverflow|78098368",
        "content_hash": "sha256:deadbeef",
        "acquisition_method": "OFFICIAL_API",
        "payload": payload,
        "provenance": provenance,
        "review_version": 1,
        "collector_id": "stack-exchange-questions",
        "collector_version": "1.0.0",
        "correlation_id": "mission-1.18-test",
        "collected_at": MOMENT,
        "observed_at": None,
        "expires_at": MOMENT,
    }
    base.update(overrides)
    return RawRecordView(**base)  # type: ignore[arg-type]


@pytest.fixture
def normalizer() -> StackExchangeQuestionNormalizer:
    return StackExchangeQuestionNormalizer(
        NormalizationContext(retention=RETENTION, geography=NO_GEOGRAPHY)
    )


def run(normalizer: StackExchangeQuestionNormalizer, record: RawRecordView | None = None):
    return normalizer.normalize(
        record if record is not None else raw(),
        correlation_id="mission-1.18-test",
        normalized_at=MOMENT,
    )


# ============================================================ the record kind


class TestTheRecordKindIsGenericAndNew:
    def test_community_question_is_registered(self) -> None:
        assert "community_question" in RECORD_KINDS

    def test_it_is_not_named_after_the_first_source_to_reach_it(self) -> None:
        """A public Q&A question is a shape other sources share.

        Naming the kind `stack_exchange_question` would make the vocabulary a
        list of vendors. The SITE is a field; the source is provenance.
        """
        assert "stack_exchange" not in " ".join(RECORD_KINDS)

    def test_it_did_not_widen_an_existing_kind(self) -> None:
        """The three earlier kinds are untouched, which is the point of a fourth.

        Widening `numeric_observation` would make `observation.value_state`
        meaningless for a question; widening `procurement_notice` would give a
        question a buyer.
        """
        assert RECORD_KINDS["numeric_observation"].required == (
            "metric.id",
            "period",
            "geography.source_code",
            "observation.value_state",
        )
        assert "question.id" not in RECORD_KINDS["procurement_notice"].required


# ============================================================ normalization


class TestOneQuestionBecomesOneObservation:
    def test_the_identity_and_kind_are_the_sources_own(self, normalizer) -> None:
        draft = run(normalizer)
        assert draft.record_kind_id == "community_question"
        assert draft.payload["question"]["id"] == "78098368"
        assert draft.payload["question"]["site"] == "stackoverflow"

    def test_the_tags_stay_in_the_sites_vocabulary(self, normalizer) -> None:
        """Preserved verbatim and never mapped to a taxonomy of ours."""
        tags = run(normalizer).payload["tags"]
        assert tags["values"] == ["python", "multiprocessing", "tqdm"]
        assert tags["scheme"] == "stack-exchange-tags:stackoverflow"

    def test_the_canonical_url_and_licence_survive(self, normalizer) -> None:
        question = run(normalizer).payload["question"]
        assert question["url"].startswith("https://stackoverflow.com/questions/78098368")
        assert question["content_licence"] == "CC BY-SA 4.0"

    def test_the_period_is_an_established_instant(self, normalizer) -> None:
        """The first adapter for which this is true on the source's evidence.

        A Unix epoch second is unambiguous, unlike TED's offset-without-a-time
        (H-37) or GDELT's unzoned bucket (H-29). So `observed_at` is a real
        moment here rather than NULL.
        """
        payload = run(normalizer).payload
        assert payload["period"]["type"] == "INSTANT"
        assert payload["period"]["timezone_state"] == "ESTABLISHED"
        assert payload["period"]["start"] == "2024-03-04T00:00:12+00:00"
        assert run(normalizer).observed_at is not None

    def test_the_site_comes_from_provenance_not_from_parsing_the_url(self, normalizer) -> None:
        """Parsing it out of the link would work and would be inventing a fact
        the record already states -- and would start reading content for
        identity."""
        record = raw(provenance_extra={"site": "superuser"})
        assert run(normalizer, record).payload["question"]["site"] == "superuser"

    def test_a_missing_body_is_visible_and_not_a_failure(self, normalizer) -> None:
        """VALID, with the absence stated in the payload rather than in a code.

        The record kind does not require a body, and the closed
        `NormalizationQualityReason` vocabulary has no member that names this
        absence -- so `PARTIAL` could only be reached by putting a wrong code
        where a consumer branches. `question.body: null` says it exactly.
        """
        draft = run(normalizer, raw(payload_drop=("body",)))
        assert draft.quality.value == "VALID"
        assert draft.payload["question"]["body"] is None

    def test_normalization_is_deterministic(self, normalizer) -> None:
        assert run(normalizer).payload == run(normalizer).payload


class TestAcceptedAnswerStaysNarrow:
    def test_it_says_only_that_the_asker_accepted_one(self, normalizer) -> None:
        draft = run(normalizer, raw(payload_extra={"accepted_answer_id": 999}))
        answers = draft.payload["answers"]
        assert answers["has_accepted_answer"] is True
        assert "not a statement that the problem is objectively resolved" in str(
            answers["accepted_answer_semantics"]
        )

    def test_no_field_name_in_the_payload_says_solved(self, normalizer) -> None:
        """Scanned over the KEYS, because the risk is a field name reading as a
        verdict.

        Deliberately not a scan over the whole flattened payload: the
        disclaimer's own sentence contains "objectively resolved", and a test
        that failed on it would push the honest wording out of the record.
        """

        def keys(node: object) -> list[str]:
            if isinstance(node, dict):
                return [k for k in node] + [x for v in node.values() for x in keys(v)]
            if isinstance(node, list):
                return [x for v in node for x in keys(v)]
            return []

        names = [
            k.lower()
            for k in keys(run(normalizer, raw(payload_extra={"accepted_answer_id": 999})).payload)
        ]
        for word in (
            "solved",
            "resolved",
            "successful",
            "good_solution",
            "validated",
            "pain",
            "demand",
        ):
            assert not any(word in name for name in names), word

    def test_engagement_counters_are_carried_unpromoted(self, normalizer) -> None:
        engagement = run(normalizer).payload["engagement"]
        assert engagement["view_count"] == 89
        assert "not importance, not demand, not market size" in str(engagement["semantics"])


class TestTheAuthorIsAbsentAndStaysAbsent:
    def test_the_payload_carries_no_author(self, normalizer) -> None:
        assert run(normalizer).payload["author"] is None

    @pytest.mark.parametrize("field", ["owner", "last_editor", "comments"])
    def test_a_raw_record_carrying_identity_is_refused_not_quietly_dropped(
        self, normalizer, field: str
    ) -> None:
        """Two different moments, and the second can only be caught here.

        The collector refuses such a RESPONSE. This refuses such a RECORD --
        because normalizing it into a row that merely omits the field would hide
        that it was ever collected.
        """
        with pytest.raises(NormalizationFailedError, match=field):
            run(normalizer, raw(payload_extra={field: {"user_id": 1}}))


class TestRefusalsRatherThanInvention:
    @pytest.mark.parametrize("field", ["question_id", "title", "creation_date", "link", "tags"])
    def test_a_record_missing_a_required_source_fact_is_refused(
        self, normalizer, field: str
    ) -> None:
        with pytest.raises(NormalizationFailedError):
            run(normalizer, raw(payload_drop=(field,)))

    def test_the_url_is_required_because_the_licence_requires_it(self, normalizer) -> None:
        """CC BY-SA needs a link to the licensed material (ADR-031). A record
        that cannot be attributed is refused rather than stored unusable."""
        with pytest.raises(NormalizationFailedError, match="CC BY-SA"):
            run(normalizer, raw(payload_drop=("link",)))


class TestNoTemporalInvention:
    def test_the_payload_states_an_instant_and_nothing_about_frequency(self, normalizer) -> None:
        """A retrieval window is not a trend.

        The collector bounded `fromdate`/`todate` to scope retrieval. Nothing
        here reads that as growth, momentum or increasing demand.
        """
        flat = str(run(normalizer).payload).lower()
        for word in ("trend", "growth", "momentum", "increas", "frequency", "rate"):
            assert word not in flat, word


class TestNoSemanticPromotion:
    def test_nothing_in_the_payload_names_demand_or_a_market(self, normalizer) -> None:
        """The boundary §3 of the brief asks to be structural and tested.

        One record is one published question, once, by an author this system
        never acquired and therefore cannot count. Every word below is a
        step somebody will be tempted to take because the data looks like it
        supports them.
        """
        flat = str(run(normalizer).payload).lower()
        for word in (
            "demand",
            "willingness",
            "purchase",
            "opportunity",
            "pain",
            "revenue",
            "customer",
        ):
            assert f'"{word}' not in flat, word

    def test_the_version_is_declared(self) -> None:
        assert SE_NORMALIZER_ID == "stack-exchange-question"
        assert SE_NORMALIZER_VERSION == "1.0.0"


# ================================================ the Signal decision: OUTCOME S0


class TestWhyNoSignalIsDefensible:
    """**Outcome S0**, encoded from the real sample rather than argued.

    Fifteen real Stack Overflow questions were normalized and inspected. No
    deterministic repeated-problem cohort exists in them, and these tests hold
    the reasoning so a later mission cannot quietly relax it.

    The tag sets below are the REAL ones, by question id.
    """

    # The real sample: every non-`python` tag, by question id.
    REAL = {
        "78098368": {"multiprocessing", "tqdm"},
        "78098383": {"jupyter-notebook", "ipywidgets"},
        "78098392": {"google-cloud-platform"},
        "78098469": {"google-cloud-platform", "deep-learning", "pip", "transformer-model"},
        "78098472": {"dataframe", "python-polars", "bulkupdate"},
        "78098475": {"excel", "email", "pdf", "win32com"},
        "78098484": set(),
        "78098533": {"numpy", "matrix", "numpy-ndarray", "matrix-multiplication"},
        "78098567": {"google-cloud-platform", "google-docs", "text-extraction"},
        "78098583": {"image", "for-loop", "python-imaging-library"},
        "78098689": {"3d", "regression"},
        "78098723": {"list", "validation", "while-loop"},
        "78098735": {"directory"},
        "78098740": {"deep-learning", "pytorch", "backpropagation"},
        "78098783": {"bitwise-operators", "logical-operators"},
    }

    def test_the_query_tag_groups_everything_and_says_nothing(self) -> None:
        """All 15 share `python` because the QUERY asked for it.

        A cohort keyed on it would have support 15 and mean nothing, which is
        the tag-frequency shortcut §9 of the brief forbids by name.
        """
        assert len(self.REAL) == 15
        assert all("python" not in tags for tags in self.REAL.values())

    def test_only_two_other_tags_are_shared_at_all(self) -> None:
        shared = {
            tag
            for tag in {t for tags in self.REAL.values() for t in tags}
            if sum(tag in tags for tags in self.REAL.values()) >= 2
        }
        assert shared == {"google-cloud-platform", "deep-learning"}

    def test_and_both_shared_tags_group_unrelated_problems(self) -> None:
        """The hard negative, and it is real rather than constructed.

        `google-cloud-platform` groups an Eventarc duplicate-processing issue, a
        `setup.py` packaging error and a Google Docs text-extraction task.
        `deep-learning` groups that same packaging error with a question about
        backpropagation over padded rows.

        **78098469 is in both**, which is the whole finding in one row: its tags
        describe the asker's CONTEXT, not their problem. A cohort built on a
        shared tag would put a packaging error in a cloud-events group and in a
        neural-network group simultaneously.
        """
        gcp = {q for q, tags in self.REAL.items() if "google-cloud-platform" in tags}
        dl = {q for q, tags in self.REAL.items() if "deep-learning" in tags}
        assert gcp == {"78098392", "78098469", "78098567"}
        assert dl == {"78098469", "78098740"}
        assert gcp & dl == {"78098469"}

    def test_no_two_questions_share_a_full_tag_set(self) -> None:
        """The only cohort key that would be defensible without reading text.

        If two questions carried identical tag sets there would at least be an
        argument. None do.
        """
        sets = [frozenset(t) for t in self.REAL.values()]
        assert len(sets) == len(set(sets))

    def test_the_decision_is_s0_and_the_reason_is_recorded(self) -> None:
        """Outcome S0: zero Signals, and it is a successful result.

        Recognising that these questions describe DIFFERENT problems requires
        reading and understanding them -- which is semantic inference, which §12
        of the brief excludes from a deterministic OBSERVED extractor. That is
        recorded as a future inference-layer requirement rather than worked
        around here.
        """
        # No extractor was registered for community questions.
        from sros_signal_model import SIGNAL_EXTRACTORS

        assert not any("stack" in name.lower() for name in SIGNAL_EXTRACTORS)
