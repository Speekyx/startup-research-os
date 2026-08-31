"""TED-EU as Mission 1.15.1 left it, pinned to review v2.

Mission 1.15.2 read the governing Decision and appended v3, which closed H-34.
These assertions therefore name **v2 explicitly** wherever they record what
1.15.1 established. They failed first when v3 landed -- correctly, because they
were written against "the current review" and the current review had moved.

Pinning is the right fix rather than deleting them: what v2 found remains true of
v2, and an append-only history is worth nothing if nothing checks that the
superseded versions still say what they said.

Mission 1.15.1 §33. **No third-party network call.** Retrieving the documents was
the review; these tests read what the reviewer recorded — the rule
`testing-strategy.md` §34 states, and the one this mission proves again: the
governing instrument itself would not render, and a suite that fetched it would
fail on EUR-Lex rather than on the catalog.

The property this file exists to protect is the negative one. TED would be the
portfolio's first transaction-class source, the project wants it badly, and
nothing here may drift toward letting it through.
"""

from __future__ import annotations

import pytest
from sros_acquisition.registry import APPROVING_STATES
from sros_contracts import PolicyAssessment, SourceApprovalState

from .conftest import needs_postgres

# The instrument TED's own legal notice names. Establishing it was this
# mission's one real advance; reading it was not possible.
GOVERNING_INSTRUMENT_URL = "https://eur-lex.europa.eu/eli/dec/2011/833/oj"

LOAD_BEARING = (
    "automated_access",
    "api_use",
    "commercial_use",
    "storage",
    "derived_analytics",
    "model_processing",
)

# Kept apart on purpose (§3). None may inherit another's finding.
DISTINCT_ML_ACTIVITIES = ("model_processing",)


def source_of(catalog, source_id: str):
    return next(s for s in catalog.sources if s.source_id == source_id)


def review(catalog, source_id: str, version: int | None = None):
    source = source_of(catalog, source_id)
    if version is None:
        return source.review
    return next(r for r in source.review_history if r.review_version == version)


def assessment(review_obj, activity: str):
    return review_obj.assessments[activity]


# ============================================ the earlier review is untouched


class TestPriorReviewImmutable:
    def test_version_one_is_still_present_and_unchanged(self, catalog) -> None:
        """Mission 1.15's review is authoritative and was not rewritten."""
        v1 = review(catalog, "ted-eu", 1)
        assert v1.approval_state is SourceApprovalState.REQUIRES_REVIEW
        assert v1.reviewed_by == "mission-1.15"
        assert assessment(v1, "model_processing") is PolicyAssessment.NOT_ADDRESSED

    def test_the_first_two_versions_still_exist_and_are_contiguous(self, catalog) -> None:
        versions = sorted(r.review_version for r in source_of(catalog, "ted-eu").review_history)
        assert versions[:2] == [1, 2]
        assert versions == list(range(1, len(versions) + 1))

    def test_version_two_carries_every_v1_activity_forward_unchanged(self, catalog) -> None:
        """A re-review that could not close its question must not quietly move
        findings it did not re-establish."""
        v1, v2 = review(catalog, "ted-eu", 1), review(catalog, "ted-eu", 2)
        assert v1.assessments == v2.assessments


# ============================================== the verdict did not move


class TestVerdictUnchanged:
    def test_ted_is_still_requires_review(self, catalog) -> None:
        assert review(catalog, "ted-eu").approval_state is SourceApprovalState.REQUIRES_REVIEW

    def test_ted_is_not_approving(self, catalog) -> None:
        assert review(catalog, "ted-eu").approval_state not in APPROVING_STATES

    def test_five_activities_granted_did_not_make_six_at_v2(self, catalog) -> None:
        """Rule 8 as it applied at v2: one NOT_ADDRESSED load-bearing activity
        blocked whatever the others said. Mission 1.15.2 later granted the
        sixth, and v2 must still record the state that made it right."""
        current = review(catalog, "ted-eu", 2)
        granted = {n for n in LOAD_BEARING if assessment(current, n) is PolicyAssessment.PERMITTED}
        unaddressed = {
            n for n in LOAD_BEARING if assessment(current, n) is PolicyAssessment.NOT_ADDRESSED
        }
        assert granted == set(LOAD_BEARING) - {"model_processing"}
        assert unaddressed == {"model_processing"}
        assert current.approval_state is SourceApprovalState.REQUIRES_REVIEW

    def test_model_processing_was_not_inferred_from_the_broad_grant_at_v2(self, catalog) -> None:
        """The grant says notices "can be freely reused". With the instrument
        unread, treating that as covering ML inference would have meant assuming
        a definition. Mission 1.15.2 read the definition and it turned out to be
        broad -- which vindicates the reasoning rather than retiring it."""
        assert (
            assessment(review(catalog, "ted-eu", 2), "model_processing")
            is PolicyAssessment.NOT_ADDRESSED
        )


# ====================================== a version needs evidence behind it


class TestEvidence:
    def test_the_new_review_carries_retrieved_evidence(self, catalog) -> None:
        current = review(catalog, "ted-eu")
        assert len(current.evidence) >= 3
        for item in current.evidence:
            assert item.document_url.startswith("https://")
            assert item.summarized_finding.strip()
            assert item.retrieved_at is not None

    def test_the_governing_instrument_is_named_with_its_canonical_url(self, catalog) -> None:
        """The one thing this mission established. v1 guessed at "the
        Publications Office's reuse decision, or another first-party
        instrument"; v2 names it."""
        urls = {e.document_url for e in review(catalog, "ted-eu").evidence}
        assert GOVERNING_INSTRUMENT_URL in urls

    def test_the_retrieval_failure_is_recorded_as_evidence(self, catalog) -> None:
        """An unread document must stay visibly unread. Recording the failure is
        what stops the next reader assuming it was read."""
        entry = next(
            e
            for e in review(catalog, "ted-eu", 2).evidence
            if e.document_url == GOVERNING_INSTRUMENT_URL
        )
        assert "empty body" in entry.summarized_finding.lower()
        assert (entry.section_reference or "").lower() == "retrieval failure"

    def test_no_search_engine_summary_was_used_as_evidence(self, catalog) -> None:
        """§4. A summary of a legal instrument must not stand in for it."""
        for item in review(catalog, "ted-eu").evidence:
            assert "google" not in item.document_url
            assert "bing" not in item.document_url
            assert item.document_url.startswith(
                (
                    "https://ted.europa.eu",
                    "https://eur-lex.europa.eu",
                    "https://op.europa.eu",
                    "https://docs.ted.europa.eu",
                )
            ), item.document_url


# ================================= technical access is still not permission


class TestAccessIsNotPermission:
    def test_bulk_download_needs_no_authentication_and_ted_is_still_blocked(self, catalog) -> None:
        source = source_of(catalog, "ted-eu")
        assert any(not p.requires_authentication for p in source.access_profiles)
        assert review(catalog, "ted-eu").approval_state not in APPROVING_STATES

    def test_no_access_profile_requires_a_credential(self, catalog) -> None:
        """Nothing about the route is gated. Everything about the permission is."""
        for profile in source_of(catalog, "ted-eu").access_profiles:
            assert not profile.requires_api_key
            assert not profile.secret_references


# ======================================= the ML activities stay distinct


class TestActivitiesStayDistinct:
    def test_model_processing_is_a_single_named_assessment(self, catalog) -> None:
        current = review(catalog, "ted-eu")
        for activity in DISTINCT_ML_ACTIVITIES:
            assert activity in current.assessments

    def test_training_and_embeddings_were_not_folded_into_inference(self, catalog) -> None:
        """§3, §14, §15. Nothing in the review claims a training or embedding
        permission, and neither may inherit an inference decision."""
        notes = (review(catalog, "ted-eu", 2).review_notes or "").lower()
        assert "not_addressed" in notes or "could not be retrieved" in notes
        assert (
            assessment(review(catalog, "ted-eu", 2), "model_processing")
            is not PolicyAssessment.PERMITTED
        )


# ===================================== the conditions were preserved


class TestConditionsPreserved:
    def test_every_v1_condition_survives_into_v2(self, catalog) -> None:
        """§12, §13. Minimisation and authenticity may not be weakened
        incidentally by a mission about reuse rights."""
        v1, v2 = review(catalog, "ted-eu", 1), review(catalog, "ted-eu", 2)
        for condition in v1.conditions:
            assert condition in v2.conditions

    def test_the_personal_data_minimisation_condition_is_intact(self, catalog) -> None:
        joined = " ".join(review(catalog, "ted-eu").conditions).lower()
        assert "contact" in joined
        assert "minimisation" in joined or "discard" in joined

    def test_the_authenticity_condition_is_intact(self, catalog) -> None:
        joined = " ".join(review(catalog, "ted-eu").conditions).lower()
        assert "electronically signed" in joined
        assert "authentic" in joined

    def test_the_personal_data_risk_classification_did_not_soften(self, catalog) -> None:
        v1, v2 = review(catalog, "ted-eu", 1), review(catalog, "ted-eu", 2)
        assert v2.personal_data_risk == v1.personal_data_risk
        assert v2.contains_user_identifiers is True
        assert v2.discard_identifiers_after_normalization is True


# ============================================ the open questions are precise


class TestOpenQuestions:
    def test_h34_names_the_instrument_to_retrieve(self, catalog) -> None:
        questions = " ".join(review(catalog, "ted-eu").open_questions)
        assert "2011/833" in questions
        assert "reuse" in questions.lower()

    def test_the_database_right_question_was_recorded(self, catalog) -> None:
        """H-36. New this round, and it could block TED even if H-34 closes
        favourably."""
        questions = " ".join(review(catalog, "ted-eu").open_questions).lower()
        assert "database" in questions
        assert "extraction" in questions or "re-utilisation" in questions

    def test_a_blocked_source_still_states_what_is_missing(self, catalog) -> None:
        assert review(catalog, "ted-eu").open_questions


# ================================= nothing was collected, built or claimed


class TestNothingWasBuilt:
    def test_no_ted_collector_exists(self, catalog) -> None:
        from sros_acquisition import IMPLEMENTED_COLLECTORS

        assert "ted-eu" not in IMPLEMENTED_COLLECTORS

    def test_no_ted_normalizer_exists(self, catalog) -> None:
        from sros_acquisition import IMPLEMENTED_NORMALIZERS

        assert "ted-eu" not in IMPLEMENTED_NORMALIZERS

    def test_ted_is_not_collector_eligible(self, catalog) -> None:
        """An authorization context cannot be built for a source that does not
        pass the gate, which is the gate working rather than a limitation."""
        assert review(catalog, "ted-eu").approval_state not in APPROVING_STATES

    @pytest.mark.parametrize("source_id", ["ted-eu", "usaspending"])
    def test_the_procurement_sources_remain_blocked(self, catalog, source_id) -> None:
        assert review(catalog, source_id).approval_state is (SourceApprovalState.REQUIRES_REVIEW)

    def test_the_approving_set_was_not_disturbed(self, catalog) -> None:
        approving = {
            s.source_id for s in catalog.sources if s.review.approval_state in APPROVING_STATES
        }
        assert approving == {"world-bank", "eurostat", "fred", "gdelt", "openalex"}


# ================================ and nothing reached the database either


@needs_postgres
class TestNothingWasCollected:
    """§28. Retrieving legal documents is review work; procurement notices are
    research data and none was fetched. The assertion is cheap and it is the one
    a future mission is most likely to violate by accident."""

    @staticmethod
    def _count(query: str) -> int:
        import psycopg

        from .conftest import DATABASE_URL

        with psycopg.connect(DATABASE_URL) as conn:
            row = conn.execute(query).fetchone()
        return int(row[0]) if row else -1

    def test_no_raw_record_has_source_id_ted_eu(self) -> None:
        assert (
            self._count("SELECT count(*) FROM acquisition.raw_records WHERE source_id = 'ted-eu'")
            == 0
        )

    def test_no_normalized_record_has_source_id_ted_eu(self) -> None:
        assert (
            self._count(
                "SELECT count(*) FROM acquisition.normalized_records WHERE source_id = 'ted-eu'"
            )
            == 0
        )

    def test_no_reliability_assessment_was_created(self) -> None:
        """§30. Source review asks whether we MAY use TED; reliability review
        asks how dependable its measurements are. Different processes, and this
        mission is not the second one."""
        assert self._count("SELECT count(*) FROM epistemic.reliability_assessments") == 0

    def test_no_opportunity_or_embedding_was_created(self) -> None:
        for query in (
            "SELECT count(*) FROM research.opportunities",
            "SELECT count(*) FROM nlp.embedding_provenance",
        ):
            assert self._count(query) == 0, query

    # §27 asks that the production rows be unchanged, and this file deliberately
    # does NOT assert 12 / 12 / 7 / 7 / 7 to check it. Those are facts about one
    # developer's database, not invariants of the system: a fresh CI database
    # holds none of them, and a test that pinned them would fail everywhere the
    # data has not been loaded -- which it did, on the first CI run.
    #
    # "Unchanged" is a property of a RUN rather than of a row count, and the
    # pytest post-suite watcher already asserts it properly by comparing content
    # digests before and after across every tenant and global table. The
    # assertions above are the ones that hold in EVERY environment, because they
    # follow from there being no TED collector rather than from what somebody
    # happens to have collected (`testing-strategy.md` §36).
