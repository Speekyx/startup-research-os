"""What GDELT's registration must hold before a collector can exist.

Mission 1.9. The collector was NOT built — the audit in
`gdelt-raw-record-gap-analysis-v1.md` found that the authorised data categories
and the reviewed access profile do not intersect, and a parser composed from
invented field names would be validated by fake responses composed from the same
invention.

What this module does cover is the governance the collector will need, including
one defect the audit found by trying to use the registration rather than by
reading it: neither access profile recorded an `endpoint_url`, so the host
allowlist any GDELT collector derives from the registry was **empty**.

These assertions would all have passed vacuously before that fix, which is why
they are written against the derived value rather than against the JSON field.
"""

from __future__ import annotations

import pytest
from sros_acquisition.collection.transport import host_of
from sros_acquisition.compliance import build_authorization, load_compliance
from sros_contracts import SourceApprovalState

from .conftest import LEGACY_PROFILE, REPO_ROOT

DOC_API = "gdelt-doc-api"
# `gdelt-bulk-files` no longer exists. Mission 1.9.2 replaced the placeholder
# with the reviewed route it stood in for -- see the note on
# `test_the_bulk_placeholder_became_a_reviewed_route` below.
BULK = "gdelt-web-ngram-files"


@pytest.fixture(scope="session")
def compliance():
    return load_compliance(REPO_ROOT / "docs/data/source-compliance-v1.json")


@pytest.fixture(scope="session")
def gdelt(catalog):
    return catalog.get("gdelt")


class TestTheRegistrationCanAuthoriseAHost:
    def test_the_reviewed_api_profile_records_where_it_lives(self, gdelt) -> None:
        """The defect Mission 1.9 found.

        The collector derives its allowlist from the registry so that revoking a
        profile revokes the host (Mission 1.5 §10). A profile with no endpoint
        therefore authorises nothing -- fail-closed, and not what Mission 1.7
        intended when it registered the source.
        """
        profile = next(p for p in gdelt.access_profiles if p.label == DOC_API)
        assert profile.endpoint_url, "the reviewed API profile records no endpoint"
        assert profile.endpoint_url.startswith("https://")
        assert host_of(profile.endpoint_url) == "api.gdeltproject.org"

    def test_the_derived_allowlist_is_not_empty(self, gdelt, compliance) -> None:
        """Asserted on the DERIVED value, not on the JSON field.

        This is what the transport is handed, and it is what was broken.

        Mission 1.9.2 added the second host by reviewing the route that reaches
        it. The assertion is still an EQUALITY rather than a containment: a
        third host appearing is exactly what it exists to catch, and §5 names
        `storage.googleapis.com` -- which hosts the quadgram files this review
        rejected -- as the one most likely to turn up.
        """
        context = build_authorization(gdelt, LEGACY_PROFILE, compliance)
        hosts = frozenset(h for a in context.access if (h := host_of(a.endpoint_url or "")))
        assert hosts == {"api.gdeltproject.org", "data.gdeltproject.org"}

    def test_the_bulk_placeholder_became_a_reviewed_route(self, gdelt) -> None:
        """The decision this assertion was waiting for, taken in Mission 1.9.2.

        Mission 1.9 left the bulk profile without an endpoint and asserted the
        absence, so that "adding one is a decision somebody takes rather than a
        line somebody copies". Review 3 is that decision, and what it authorises
        is narrower than what the placeholder was named after: not the bulk
        route, but the one dataset directory the review assessed.
        """
        profile = next(p for p in gdelt.access_profiles if p.label == BULK)
        assert profile.endpoint_url == "https://data.gdeltproject.org/gdeltv3/web/ngrams/"
        assert host_of(profile.endpoint_url) == "data.gdeltproject.org"
        # The placeholder is gone rather than sitting alongside, so nothing is
        # left for a later mission to quietly fill in.
        assert not any(p.label == "gdelt-bulk-files" for p in gdelt.access_profiles)


class TestNoCollectorWasImplemented:
    def test_gdelt_is_eligible_and_now_has_a_collector(self, catalog, gdelt) -> None:
        """Mission 1.9's §52.1 was NOT met and its report said so.

        Mission 1.9.3 met it. What did not change is the order the three facts
        had to arrive in: the approval came first, then a concrete authorised
        resource, then code. This still asserts the approval, because a
        collector on a source whose review lapsed would be the failure the whole
        gate exists to prevent.
        """
        from sros_acquisition import IMPLEMENTED_COLLECTORS

        assert gdelt.review.approval_state is SourceApprovalState.APPROVED_WITH_CONDITIONS
        assert "gdelt" in IMPLEMENTED_COLLECTORS
        # `ted-eu` joined in Mission 1.15.7, by the same route: approval, then a
        # concrete authorised resource, then code.
        assert set(IMPLEMENTED_COLLECTORS) == {"world-bank", "gdelt", "ted-eu", "stack-exchange"}

    def test_gdelt_is_not_enabled(self, gdelt) -> None:
        assert gdelt.collector_enabled is False

    def test_the_collector_that_exists_is_the_web_ngram_one(self) -> None:
        """Mission 1.9 asserted that NO gdelt module existed, because a
        half-written collector reads as available to whoever greps for it.

        Mission 1.9.3 wrote one — for the WEB-NGRAM route. The DOC API collector
        is still not written and H-27 is still why, so the assertion is now that
        the module which exists is the reviewed one and no generic `gdelt.py`
        sits beside it claiming to serve the whole source.
        """
        collection = REPO_ROOT / "services/acquisition/python/sros_acquisition/collection"
        assert (collection / "gdelt_web_ngram.py").exists()
        assert not (collection / "gdelt.py").exists()
        assert not (collection / "gdelt_doc_api.py").exists()


class TestTheResourceModelStillFailsClosed:
    def test_no_doc_api_resource_is_authorised(self, gdelt, compliance) -> None:
        """§9.2 of the audit, answered from the other direction.

        The audit could not say what a GDELT resource IS, because the answer
        depended on which DOC API mode a collector would use and H-27 had never
        let anyone see one. Mission 1.9.2 did not guess: it reviewed a different
        route whose contract was observed. So `datasets` is no longer empty, and
        the thing the audit refused to guess at is still not in it.
        """
        context = build_authorization(gdelt, LEGACY_PROFILE, compliance)
        assert context.datasets
        assert context.authorized_dataset("anything") is None
        for mode in ("doc-api/timeline-tone", "doc-api/timeline-vol-raw", "doc-api/artlist"):
            assert context.authorized_dataset(mode) is None

    def test_the_minimisation_profile_excludes_publisher_content(self, compliance) -> None:
        """The rule that stopped the collector being written against ArtList.

        The observed `ArtList` envelope returns `title` and `socialimage`, which
        are the publisher's text and image, and `url`/`domain`, which the
        profile does not list. What remains is a period and a geography: two
        dimensions and no measurement.
        """
        entry = compliance.get("gdelt")
        assert "publisher_content" in entry.data_minimisation.excluded
        assert "article_full_text" in entry.data_minimisation.excluded
        # The categories ArtList would need in order to be collectable, and does
        # not return.
        for measure in ("tone_score", "theme_identifier", "entity_mention"):
            assert measure in entry.data_minimisation.allowed

    def test_the_rate_limit_is_still_recorded_as_unknown(self, gdelt) -> None:
        """§13. GDELT returned HTTP 429 to a Mission 1.9 probe, which proves a
        limit exists and does not reveal what it is. A number here would be read
        by a collector as the provider's quota."""
        for profile in gdelt.access_profiles:
            assert profile.rate_limit_known is False
            assert profile.rate_limit_requests is None
            assert profile.rate_limit_daily_quota is None
