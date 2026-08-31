"""The Mission 1.15 demand-side round, as properties of the reviewed catalog.

Mission 1.15 §37. **Nothing here contacts a platform.** Retrieving the documents
was the review; these tests read the recorded result of it, so CI never depends
on a third party being reachable — which is exactly the failure this round hit
live, with Reddit and Stack Exchange.

Two things the suite is built to catch:

    a verdict changing without evidence behind it
    a blocked source being counted as coverage
"""

from __future__ import annotations

import pytest
from sros_acquisition.registry import APPROVING_STATES
from sros_contracts import PolicyAssessment, SourceApprovalState

# Reviewed this round, with the verdict each ended at.
REVIEWED_IN_1_15 = {
    "pinterest": SourceApprovalState.RESTRICTED,
    "hacker-news": SourceApprovalState.RESTRICTED,
    "bluesky": SourceApprovalState.REQUIRES_REVIEW,
    "ted-eu": SourceApprovalState.REQUIRES_REVIEW,
    "usaspending": SourceApprovalState.REQUIRES_REVIEW,
}

# Registered by this round. Both carry TRANSACTION-class evidence, which is the
# family that had no candidate at all before.
NEW_IN_1_15 = {"ted-eu", "usaspending"}

# Unreachable from the review environment. Their reviews must be UNCHANGED: a
# failed retrieval is not evidence and does not justify a version.
UNREACHABLE_IN_1_15 = {"reddit", "stack-exchange"}

# The six activities an approving review must positively grant (Mission 1.8).
LOAD_BEARING = (
    "automated_access",
    "api_use",
    "commercial_use",
    "storage",
    "derived_analytics",
    "model_processing",
)


def source_of(catalog, source_id: str):
    return next(s for s in catalog.sources if s.source_id == source_id)


def review(catalog, source_id: str, version: int | None = None):
    """The current review, or a named earlier version.

    `review_history` is every version; `review` is the one in force. Both are
    needed here: the point of an append-only history is that the superseded
    reasoning stays readable.
    """
    source = source_of(catalog, source_id)
    if version is None:
        return source.review
    return next(r for r in source.review_history if r.review_version == version)


def assessment(review_obj, activity: str):
    """Activity assessments live in a mapping, not as attributes."""
    return review_obj.assessments[activity]


# ==================================================== review history is append-only


class TestReviewHistory:
    def test_every_re_reviewed_source_kept_its_earlier_versions(self, catalog) -> None:
        """A verdict that changed must leave the reasoning that preceded it
        readable. Rewriting v1 would make the change invisible."""
        for source_id in ("pinterest", "hacker-news", "bluesky"):
            versions = [r.review_version for r in source_of(catalog, source_id).review_history]
            assert versions == sorted(versions)
            assert versions[0] == 1
            assert len(versions) >= 2, source_id

    def test_versions_are_contiguous_from_one(self, catalog) -> None:
        # Per PROFILE since Mission 1.15.5: each profile keeps its own
        # append-only line, and version 1 under a second profile is a first
        # review of a new question rather than a duplicate.
        for source in catalog.sources:
            for profile in source.use_profiles:
                versions = sorted(
                    r.review_version
                    for r in source.review_history
                    if r.assessed_use_profile == profile
                )
                assert versions == list(range(1, len(versions) + 1)), (
                    source.source_id,
                    profile,
                )

    def test_the_earlier_pinterest_review_still_says_it_was_unassessed(self, catalog) -> None:
        """v1 recorded NOT_ASSESSED because the document could not be retrieved.
        That is a different statement from v2's NOT_PERMITTED, and both stay."""
        assert assessment(review(catalog, "pinterest", 1), "storage") is (
            PolicyAssessment.NOT_ASSESSED
        )
        assert assessment(review(catalog, "pinterest", 2), "storage") is (
            PolicyAssessment.NOT_PERMITTED
        )

    def test_the_earlier_hacker_news_reviews_still_say_requires_review(self, catalog) -> None:
        for version in (1, 2):
            assert (
                review(catalog, "hacker-news", version).approval_state
                is SourceApprovalState.REQUIRES_REVIEW
            )
        assert review(catalog, "hacker-news", 3).approval_state is SourceApprovalState.RESTRICTED


# ================================================ a verdict change needs evidence


class TestEvidenceBackedVerdicts:
    @pytest.mark.parametrize("source_id", sorted(REVIEWED_IN_1_15))
    def test_the_current_review_carries_retrieved_evidence(self, catalog, source_id) -> None:
        current = review(catalog, source_id)
        assert current.evidence, source_id
        for item in current.evidence:
            assert item.document_url.startswith("https://"), source_id
            assert item.summarized_finding.strip(), source_id
            assert item.retrieved_at is not None, source_id

    @pytest.mark.parametrize("source_id", sorted(REVIEWED_IN_1_15))
    def test_the_current_review_reaches_the_expected_verdict(self, catalog, source_id) -> None:
        assert review(catalog, source_id).approval_state is REVIEWED_IN_1_15[source_id]

    def test_a_restricted_verdict_names_what_prohibits_it(self, catalog) -> None:
        """RESTRICTED must rest on a finding, not on an absence. Both sources
        restricted this round record NOT_PERMITTED on named activities."""
        for source_id in ("pinterest", "hacker-news"):
            current = review(catalog, source_id)
            refused = [
                name
                for name in LOAD_BEARING
                if assessment(current, name) is PolicyAssessment.NOT_PERMITTED
            ]
            assert refused, source_id

    def test_pinterest_records_the_storage_prohibition(self, catalog) -> None:
        """The decisive clause: information accessed through the API may not be
        stored. This engine's first layer preserves what arrived."""
        current = review(catalog, "pinterest")
        assert assessment(current, "storage") is PolicyAssessment.NOT_PERMITTED
        # The verbatim clause, not the word "store": the finding says
        # "storing", and a test that matched the stem would pass on prose that
        # merely mentioned storage rather than prohibiting it.
        assert any(
            "call the api on each access" in e.summarized_finding.lower() for e in current.evidence
        )

    def test_hacker_news_records_the_data_mining_prohibition(self, catalog) -> None:
        current = review(catalog, "hacker-news")
        assert assessment(current, "automated_access") is PolicyAssessment.NOT_PERMITTED
        assert any("data mining" in e.summarized_finding.lower() for e in current.evidence)


# =============================== technical access is not permission, still


class TestAccessIsNotPermission:
    def test_hacker_news_has_an_open_api_and_is_restricted(self, catalog) -> None:
        """The sharpest case in the catalog: a documented API, no key, and the
        API's own page states there is currently no rate limit -- while the
        governing terms prohibit both halves of the assessed use."""
        source = source_of(catalog, "hacker-news")
        assert any(not p.requires_api_key for p in source.access_profiles)
        assert review(catalog, source.source_id).approval_state is (SourceApprovalState.RESTRICTED)

    def test_bluesky_has_a_keyless_public_api_and_is_not_approving(self, catalog) -> None:
        source = source_of(catalog, "bluesky")
        assert any(not p.requires_api_key for p in source.access_profiles)
        assert review(catalog, "bluesky").approval_state not in APPROVING_STATES

    def test_ted_is_freely_downloadable_and_is_not_approving(self, catalog) -> None:
        """Bulk XML with no sign-in, and still blocked. Five of six activities
        granted does not make six."""
        source = source_of(catalog, "ted-eu")
        assert any(not p.requires_authentication for p in source.access_profiles)
        assert review(catalog, "ted-eu").approval_state not in APPROVING_STATES


# ================================ silence is not permission, on the new sources


class TestSilenceStillBlocks:
    def test_ted_granted_five_activities_and_was_blocked_by_the_sixth_at_v1(self, catalog) -> None:
        """The whole shape of Mission 1.15's finding, pinned to the version that
        made it. A single NOT_ADDRESSED activity blocked whatever the other five
        said (Mission 1.8, rule 8).

        Mission 1.15.2 read the governing Decision and granted the sixth, so
        this tracks v1 rather than the current review -- what v1 found remains
        true of v1, and that is what an append-only history is for."""
        current = review(catalog, "ted-eu", 1)
        granted = [
            name for name in LOAD_BEARING if assessment(current, name) is PolicyAssessment.PERMITTED
        ]
        unaddressed = [
            name
            for name in LOAD_BEARING
            if assessment(current, name) is PolicyAssessment.NOT_ADDRESSED
        ]
        assert sorted(granted) == sorted(set(LOAD_BEARING) - {"model_processing"})
        assert unaddressed == ["model_processing"]
        assert current.approval_state is SourceApprovalState.REQUIRES_REVIEW

    def test_ted_named_the_single_missing_grant_at_v1(self, catalog) -> None:
        """A blocked source must say what is missing, specifically enough that
        somebody could go and get it. Somebody did: Mission 1.15.2 retrieved the
        Decision and closed that question, so this pins v1."""
        questions = " ".join(review(catalog, "ted-eu", 1).open_questions).lower()
        assert "machine-learning" in questions or "machine learning" in questions

    def test_ted_is_still_blocked_and_still_says_why(self, catalog) -> None:
        """The durable property, at whatever the current version is: a blocked
        source names what is missing. Today that is the database right."""
        current = review(catalog, "ted-eu")
        assert current.approval_state not in APPROVING_STATES
        assert current.open_questions

    def test_bluesky_remains_silent_on_every_load_bearing_activity(self, catalog) -> None:
        current = review(catalog, "bluesky")
        for name in LOAD_BEARING:
            assert assessment(current, name) is PolicyAssessment.NOT_ADDRESSED, name

    def test_usaspending_publication_is_not_a_reuse_grant(self, catalog) -> None:
        """The DATA Act requires the data to be publicly ACCESSIBLE. That is a
        statement about publication, not a grant to a commercial product."""
        current = review(catalog, "usaspending")
        for name in LOAD_BEARING:
            assert assessment(current, name) is PolicyAssessment.NOT_ADDRESSED, name
        assert current.approval_state is SourceApprovalState.REQUIRES_REVIEW


# ===================================== a retrieval failure changes nothing


class TestRetrievalFailure:
    @pytest.mark.parametrize("source_id", sorted(UNREACHABLE_IN_1_15))
    def test_an_unreachable_source_gained_no_review_version(self, catalog, source_id) -> None:
        """Reddit and Stack Exchange could not be reached. A failed retrieval is
        not evidence, so neither review moved -- in either direction."""
        versions = [r.review_version for r in source_of(catalog, source_id).review_history]
        assert max(versions) == 2, source_id
        assert review(catalog, source_id).reviewed_by != "mission-1.15", source_id

    @pytest.mark.parametrize("source_id", sorted(UNREACHABLE_IN_1_15))
    def test_an_unreachable_source_stays_blocked(self, catalog, source_id) -> None:
        assert review(catalog, source_id).approval_state not in APPROVING_STATES

    def test_bluesky_records_the_failed_retrieval_as_evidence(self, catalog) -> None:
        """The developer guidelines exist and could not be fetched. Recording
        the failure is what keeps the question visibly open rather than
        forgotten."""
        current = review(catalog, "bluesky")
        assert any(
            "empty body" in e.summarized_finding.lower()
            or "retrieval failure" in (e.section_reference or "").lower()
            for e in current.evidence
        )


# ============================ restricted and prohibited stay where they were


class TestExistingVerdictsPreserved:
    def test_no_prohibited_source_was_softened(self, catalog) -> None:
        for source_id in ("youtube", "tiktok", "spotify"):
            assert review(catalog, source_id).approval_state is SourceApprovalState.PROHIBITED

    def test_restricted_sources_stay_restricted_without_a_new_grant(self, catalog) -> None:
        """A different endpoint under the same governing terms does not change a
        policy restriction. None of these was re-opened."""
        for source_id in (
            "github",
            "apple-app-store",
            "google-play",
            "product-hunt",
            "steam",
            "meta-instagram",
        ):
            assert review(catalog, source_id).approval_state is SourceApprovalState.RESTRICTED, (
                source_id
            )

    def test_the_approving_set_was_not_disturbed(self, catalog) -> None:
        approving = {
            s.source_id for s in catalog.sources if s.review.approval_state in APPROVING_STATES
        }
        assert approving == {"world-bank", "eurostat", "fred", "gdelt", "openalex"}


# ================================ coverage is potential, never permission


class TestCoverageIsNotPermission:
    def test_the_new_sources_record_coverage_while_being_blocked(self, catalog) -> None:
        """Coverage IS recorded for a blocked source, because the portfolio
        analysis has to show what a blocked source would have contributed
        (ADR-017). It has never been permission."""
        for source_id in NEW_IN_1_15:
            source = source_of(catalog, source_id)
            assert source.signal_coverage, source_id
            assert review(catalog, source_id).approval_state not in APPROVING_STATES

    def test_no_approving_source_covers_the_commercial_family_from_this_round(
        self, catalog
    ) -> None:
        """The WTP finding, as a property: both transaction-class candidates
        record `commercial` coverage and neither is approving, so the family
        gained candidates and no usable source."""
        commercial = {
            s.source_id
            for s in catalog.sources
            if any(c.signal_family == "commercial" for c in s.signal_coverage)
        }
        assert commercial >= NEW_IN_1_15
        for source_id in NEW_IN_1_15:
            assert review(catalog, source_id).approval_state not in APPROVING_STATES


# =========================================== no collector, no acquisition


class TestNoCollectorWasBuilt:
    def test_the_new_sources_have_no_implemented_collector(self, catalog) -> None:
        from sros_acquisition import IMPLEMENTED_COLLECTORS

        for source_id in NEW_IN_1_15:
            assert source_id not in IMPLEMENTED_COLLECTORS, source_id

    def test_the_new_sources_have_no_implemented_normalizer(self, catalog) -> None:
        from sros_acquisition import IMPLEMENTED_NORMALIZERS

        for source_id in NEW_IN_1_15:
            assert source_id not in IMPLEMENTED_NORMALIZERS, source_id

    def test_no_source_reviewed_this_round_became_collector_eligible(self, catalog) -> None:
        """§39's success criterion is honest review, not an approval. Nothing
        this round produced an eligible source, and the tests say so rather
        than leaving it to a report."""
        for source_id in REVIEWED_IN_1_15:
            assert review(catalog, source_id).approval_state not in APPROVING_STATES
