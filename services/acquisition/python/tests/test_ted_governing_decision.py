"""TED-EU after Mission 1.15.2: H-34 closed, H-36 not, verdict unmoved.

Mission 1.15.2 §39. **No external call.** The Decision was retrieved and read
during the review; these tests read what the reviewer recorded.

The shape this file protects is unusual and is the whole point: **every
load-bearing activity is now PERMITTED and the source is still blocked.** That is
the state most likely to be "tidied up" by someone who sees six greens and
assumes the verdict lagged behind.
"""

from __future__ import annotations

import pytest
from sros_acquisition.registry import APPROVING_STATES
from sros_contracts import PolicyAssessment, SourceApprovalState

from .conftest import needs_postgres

LOAD_BEARING = (
    "automated_access",
    "api_use",
    "commercial_use",
    "storage",
    "derived_analytics",
    "model_processing",
)

# The Cellar route that worked, and the EUR-Lex one that did not.
CELLAR_HOST = "https://op.europa.eu/o/opportal-service/download-handler"
EURLEX_ELI = "https://eur-lex.europa.eu/eli/dec/2011/833/oj"

FIRST_PARTY_PREFIXES = (
    "https://ted.europa.eu",
    "https://docs.ted.europa.eu",
    "https://eur-lex.europa.eu",
    "https://op.europa.eu",
    "https://publications.europa.eu",
)


def source_of(catalog, source_id: str):
    return next(s for s in catalog.sources if s.source_id == source_id)


def review(catalog, source_id: str, version: int | None = None):
    source = source_of(catalog, source_id)
    if version is None:
        return source.review
    return next(r for r in source.review_history if r.review_version == version)


def assessment(review_obj, activity: str):
    return review_obj.assessments[activity]


# =========================================== v1 and v2 are untouched


class TestEarlierReviewsImmutable:
    def test_three_versions_exist_and_are_contiguous(self, catalog) -> None:
        versions = sorted(r.review_version for r in source_of(catalog, "ted-eu").review_history)
        assert versions == [1, 2, 3]

    @pytest.mark.parametrize("version", [1, 2])
    def test_the_earlier_versions_still_say_model_processing_was_unaddressed(
        self, catalog, version
    ) -> None:
        """The finding that changed. v1 and v2 must still record the state that
        made them right at the time."""
        assert (
            assessment(review(catalog, "ted-eu", version), "model_processing")
            is PolicyAssessment.NOT_ADDRESSED
        )

    def test_the_earlier_reviewers_are_unchanged(self, catalog) -> None:
        assert review(catalog, "ted-eu", 1).reviewed_by == "mission-1.15"
        assert review(catalog, "ted-eu", 2).reviewed_by == "mission-1.15.1"
        assert review(catalog, "ted-eu", 3).reviewed_by == "mission-1.15.2"


# ================================================ H-34 closed permitted


class TestH34Closed:
    def test_model_processing_is_now_permitted(self, catalog) -> None:
        assert (
            assessment(review(catalog, "ted-eu"), "model_processing") is PolicyAssessment.PERMITTED
        )

    def test_every_load_bearing_activity_is_granted(self, catalog) -> None:
        current = review(catalog, "ted-eu")
        for name in LOAD_BEARING:
            assert assessment(current, name) is PolicyAssessment.PERMITTED, name

    def test_the_decision_was_read_and_recorded_as_evidence(self, catalog) -> None:
        """A permission finding must rest on the operative text, not on a
        summary of it."""
        entry = next(
            e for e in review(catalog, "ted-eu").evidence if "2011/833" in e.document_title
        )
        assert entry.document_url.startswith(CELLAR_HOST)
        assert "Articles 1-13" in (entry.section_reference or "")
        finding = entry.summarized_finding.lower()
        assert "read in full" in finding
        assert "other than the initial purpose" in finding

    def test_the_permission_is_scoped_away_from_model_training(self, catalog) -> None:
        """§13. The Decision does not distinguish methods, so a single PERMITTED
        field could be read as authorising training. A condition carries the
        boundary the field cannot."""
        joined = " ".join(review(catalog, "ted-eu").conditions).lower()
        assert "model training" in joined
        assert "not authorised" in joined or "not assessed" in joined

    def test_embeddings_were_not_authorised_by_inheritance(self, catalog) -> None:
        """§14. An inference decision must not be inherited silently."""
        joined = " ".join(review(catalog, "ted-eu").conditions).lower()
        assert "embedding" in joined
        assert "d-12" in joined


# ============================================ H-36 did NOT close


class TestH36Open:
    def test_the_database_right_question_survives(self, catalog) -> None:
        questions = " ".join(review(catalog, "ted-eu").open_questions).lower()
        assert "database" in questions
        assert "sui generis" in questions

    def test_the_open_question_records_that_the_decision_was_searched(self, catalog) -> None:
        """The difference from Mission 1.15.1: an unknown became an established
        absence. The question must say the instrument was read, or a future
        reviewer will retrieve it again."""
        questions = " ".join(review(catalog, "ted-eu").open_questions).lower()
        assert "read in full" in questions
        assert "96/9" in questions or "extraction" in questions

    def test_a_favourable_h34_did_not_override_an_unresolved_h36(self, catalog) -> None:
        """§23, and the property this whole file exists for: six granted
        activities and a blocked source, at the same time."""
        current = review(catalog, "ted-eu")
        assert all(assessment(current, name) is PolicyAssessment.PERMITTED for name in LOAD_BEARING)
        assert current.approval_state is SourceApprovalState.REQUIRES_REVIEW
        assert current.approval_state not in APPROVING_STATES

    def test_database_rights_were_not_inferred_from_the_copyright_permission(self, catalog) -> None:
        """A grant over documents does not carry a right in the collection."""
        assert review(catalog, "ted-eu").open_questions


# ================================================== evidence discipline


class TestEvidenceDiscipline:
    def test_every_evidence_url_is_first_party(self, catalog) -> None:
        for item in review(catalog, "ted-eu").evidence:
            assert item.document_url.startswith(FIRST_PARTY_PREFIXES), item.document_url

    def test_no_search_engine_or_mirror_appears(self, catalog) -> None:
        """§3: mirrors, archives, cached pages, third-party databases and law
        blogs are not evidence, however convenient."""
        for item in review(catalog, "ted-eu").evidence:
            url = item.document_url.lower()
            for forbidden in ("google", "bing", "archive.org", "webcache", "github"):
                assert forbidden not in url, item.document_url

    def test_the_eurlex_failures_are_still_recorded(self, catalog) -> None:
        """The successful route was the Cellar, not EUR-Lex. Recording the
        failures stops a future reviewer repeating five of them."""
        entry = next(e for e in review(catalog, "ted-eu").evidence if e.document_url == EURLEX_ELI)
        assert (entry.section_reference or "").lower() == "retrieval failure"

    def test_every_evidence_item_carries_a_retrieval_time(self, catalog) -> None:
        for item in review(catalog, "ted-eu").evidence:
            assert item.retrieved_at is not None
            assert item.summarized_finding.strip()


# ============================================ conditions carried forward


class TestConditionsPreserved:
    @pytest.mark.parametrize("version", [1, 2])
    def test_every_earlier_condition_survives(self, catalog, version) -> None:
        """§19, §20, §21. A mission about reuse rights is where an unrelated
        condition gets weakened incidentally."""
        earlier = review(catalog, "ted-eu", version)
        current = review(catalog, "ted-eu")
        for condition in earlier.conditions:
            assert condition in current.conditions

    def test_personal_data_minimisation_is_intact(self, catalog) -> None:
        joined = " ".join(review(catalog, "ted-eu").conditions).lower()
        assert "contact" in joined
        assert "minimisation" in joined or "discard" in joined

    def test_authenticity_is_intact(self, catalog) -> None:
        joined = " ".join(review(catalog, "ted-eu").conditions).lower()
        assert "electronically signed" in joined
        assert "authentic" in joined

    def test_third_party_and_industrial_property_exclusions_are_intact(self, catalog) -> None:
        joined = " ".join(review(catalog, "ted-eu").conditions).lower()
        assert "industrial property" in joined

    def test_the_non_distortion_condition_was_added(self, catalog) -> None:
        """Article 6(2)(b). The condition with the most direct bearing on the
        claim layer: an OBSERVED restatement must not change what the notice
        means."""
        joined = " ".join(review(catalog, "ted-eu").conditions).lower()
        assert "distort" in joined

    def test_the_personal_data_classification_did_not_soften(self, catalog) -> None:
        v2, v3 = review(catalog, "ted-eu", 2), review(catalog, "ted-eu")
        assert v3.personal_data_risk == v2.personal_data_risk
        assert v3.contains_user_identifiers is True
        assert v3.discard_identifiers_after_normalization is True


# ============================================ nothing was built or collected


class TestNothingWasBuilt:
    def test_no_ted_collector_or_normalizer_exists(self, catalog) -> None:
        from sros_acquisition import IMPLEMENTED_COLLECTORS, IMPLEMENTED_NORMALIZERS

        assert "ted-eu" not in IMPLEMENTED_COLLECTORS
        assert "ted-eu" not in IMPLEMENTED_NORMALIZERS

    def test_ted_is_not_collector_eligible(self, catalog) -> None:
        assert review(catalog, "ted-eu").approval_state not in APPROVING_STATES

    def test_no_resource_was_authorised(self, catalog) -> None:
        """§28. The narrowest-scope exercise applies only if TED becomes
        approving, and it did not."""
        for profile in source_of(catalog, "ted-eu").access_profiles:
            assert not profile.requires_approval

    def test_usaspending_was_not_re_reviewed(self, catalog) -> None:
        """§43. Scope stays narrow: TED has not reached a dead end."""
        versions = [r.review_version for r in source_of(catalog, "usaspending").review_history]
        assert versions == [1]
        assert review(catalog, "usaspending").reviewed_by == "mission-1.15"


@needs_postgres
class TestNothingReachedTheDatabase:
    @staticmethod
    def _count(query: str) -> int:
        import psycopg

        from .conftest import DATABASE_URL

        with psycopg.connect(DATABASE_URL) as conn:
            row = conn.execute(query).fetchone()
        return int(row[0]) if row else -1

    def test_no_ted_raw_or_normalized_record_exists(self) -> None:
        """§36. Legal document retrieval is review work; procurement notices are
        research data and none was fetched."""
        # Written out rather than interpolated: the table names are literals
        # either way, and a loop over them reads as query construction to the
        # linter, which is a rule worth not teaching people to silence.
        assert (
            self._count("SELECT count(*) FROM acquisition.raw_records WHERE source_id = 'ted-eu'")
            == 0
        )
        assert (
            self._count(
                "SELECT count(*) FROM acquisition.normalized_records WHERE source_id = 'ted-eu'"
            )
            == 0
        )

    def test_no_reliability_assessment_was_created(self) -> None:
        """§37. Permission and reliability remain separate processes."""
        assert self._count("SELECT count(*) FROM epistemic.reliability_assessments") == 0

    def test_no_opportunity_or_embedding_was_created(self) -> None:
        for query in (
            "SELECT count(*) FROM research.opportunities",
            "SELECT count(*) FROM nlp.embedding_provenance",
        ):
            assert self._count(query) == 0, query

    # §34 asks that the production rows be unchanged, and this file deliberately
    # does NOT assert 12 / 12 / 7 / 7 / 7. Those are facts about one database and
    # a fresh CI database holds none of them -- the mistake Mission 1.15.1 made
    # and CI caught. "Unchanged" is a property of a RUN and the post-suite digest
    # watcher already asserts it (`testing-strategy.md` §36).
