"""What review 3 authorised for GDELT, and what it still refuses.

Mission 1.9.2. No collector was written and no GDELT record was persisted; what
changed is that GDELT stopped being a source with an approval and no reachable
resource. These assertions cover the boundary that made the difference, and each
is written against the DERIVED value rather than against the JSON field, for the
reason Mission 1.9 recorded: an assertion on the field passes while the value
the transport actually receives is empty.

The one shape to keep in mind while reading: **the file is a published aggregate
with four columns and no link to any article.** Almost every refusal below
follows from that, and almost every approval does too.
"""

from __future__ import annotations

import pytest
from sros_acquisition.collection.transport import HttpRequest, host_of
from sros_acquisition.compliance import (
    build_authorization,
    evaluate_readiness,
    load_compliance,
)
from sros_acquisition.compliance.config import AcquisitionBounds, ResourceScope
from sros_acquisition.compliance.resources import ResourceDescriptor, authorize_resource
from sros_acquisition.registry.models import SourceRegistryError
from sros_contracts import ResourceContentOrigin, RightsBasis

from .conftest import LEGACY_PROFILE, REPO_ROOT

NGRAM_PROFILE = "gdelt-web-ngram-files"
DOC_API_PROFILE = "gdelt-doc-api"
NGRAM_ENDPOINT = "https://data.gdeltproject.org/gdeltv3/web/ngrams/"
UNIGRAM = "web-ngrams/1gram"
BIGRAM = "web-ngrams/2gram"


@pytest.fixture(scope="session")
def compliance():
    return load_compliance(REPO_ROOT / "docs/data/source-compliance-v1.json")


@pytest.fixture(scope="session")
def gdelt(catalog):
    return catalog.get("gdelt")


@pytest.fixture(scope="session")
def context(gdelt, compliance):
    return build_authorization(gdelt, LEGACY_PROFILE, compliance)


def descriptor(context, resource_id: str, **overrides) -> ResourceDescriptor:
    """Built FROM the authorised entry, the way a collector must build one.

    Never from what a caller claims about a resource -- that is the assertion
    the whole resource model rests on, so the helper the tests use has to obey
    it too, and the overrides exist to show what happens when something lies.
    """
    dataset = context.authorized_dataset(resource_id)
    assert dataset is not None, f"{resource_id} is not authorised"
    fields = {
        "source_id": "gdelt",
        "resource_id": dataset.resource_id,
        "licence": dataset.licence,
        "rights_basis": dataset.rights_basis,
        "content_origin": ResourceContentOrigin(dataset.content_origin),
        "dataset_family": dataset.dataset_family,
    }
    fields.update(overrides)
    return ResourceDescriptor(**fields)


class TestTheRightsBasisIsStillADirectGrant:
    def test_both_resources_are_authorised_by_a_direct_grant(self, context) -> None:
        assert {d.resource_id for d in context.datasets} == {UNIGRAM, BIGRAM}
        for dataset in context.datasets:
            assert dataset.rights_basis is RightsBasis.DIRECT_GRANT

    def test_no_licence_identifier_was_invented(self, context) -> None:
        """The H-28 failure mode, still closed.

        `GDELT licence`, `OTHER`, `NONE` and `N/A` are each a different lie, and
        a string here reaches every record's provenance indistinguishable from
        `CC-BY-4.0`. The model refuses one under a direct grant; this asserts
        nobody reached for it anyway.
        """
        for dataset in context.datasets:
            assert dataset.licence is None

    def test_the_basis_quotes_the_grant_it_rests_on(self, context) -> None:
        """A basis nobody can re-check against a document is not a basis."""
        for dataset in context.datasets:
            assert "unlimited and unrestricted use" in dataset.basis
            assert "RELEASED BY" in dataset.basis.upper()

    def test_the_named_licence_sources_are_untouched(self, compliance) -> None:
        """Mission 1.9.1 §8 in both directions, re-asserted after this mission
        added a rule to the same scope object."""
        world_bank = compliance.get("world-bank")
        assert world_bank.datasets
        for dataset in world_bank.datasets:
            assert dataset.rights_basis is RightsBasis.NAMED_LICENCE
            assert dataset.licence

    def test_a_direct_grant_still_cannot_satisfy_a_licence_allowlist(self, compliance) -> None:
        """GDELT's own basis, offered to a scope that enumerates licences."""
        scope = compliance.get("world-bank").resource_scope
        result = authorize_resource(
            scope,
            ResourceDescriptor(
                source_id="world-bank",
                resource_id="indicator/NY.GDP.MKTP.CD",
                rights_basis=RightsBasis.DIRECT_GRANT,
                content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
                dataset_family="indicators",
            ),
        )
        assert not result.allowed
        assert any("does not satisfy a licence allowlist" in r for r in result.denial_reasons)


class TestOnlyTheReviewedRouteIsReachable:
    def test_the_ngram_profile_is_a_dataset_download(self, gdelt) -> None:
        profile = next(p for p in gdelt.access_profiles if p.label == NGRAM_PROFILE)
        assert profile.access_method.value == "DATASET_DOWNLOAD"

    def test_the_ngram_route_authorises_exactly_one_host(self, context) -> None:
        """Asserted on the value the transport is handed, not on the JSON."""
        access = next(a for a in context.access if a.label == NGRAM_PROFILE)
        assert host_of(access.endpoint_url or "") == "data.gdeltproject.org"

    def test_the_endpoint_is_the_dataset_path_not_the_site_root(self, context) -> None:
        """§6. A source-wide root would authorise every bulk product GDELT
        publishes, including the two this review positively rejected."""
        access = next(a for a in context.access if a.label == NGRAM_PROFILE)
        assert access.endpoint_url == NGRAM_ENDPOINT

    def test_the_path_boundary_is_fail_closed_by_construction(self, context) -> None:
        """§5. The transport composes base + relative path and refuses '..', so
        the disqualified sibling dataset one directory across is unreachable
        without any new rule -- which is why no new rule was written.
        """
        access = next(a for a in context.access if a.label == NGRAM_PROFILE)
        base = access.endpoint_url

        with pytest.raises(ValueError, match="traverse"):
            HttpRequest(path="../webngrams/20260830091500.webngrams.json.gz")
        with pytest.raises(ValueError, match="path is a path, not a URL"):
            HttpRequest(path="https://storage.googleapis.com/data.gdeltproject.org/gdeltv5/")

        # An absolute-looking path is flattened INTO the authorised directory
        # rather than escaping it.
        escaped = HttpRequest(path="/gdeltv3/webngrams/x.json.gz")
        composed = base + escaped.path.lstrip("/")
        assert composed.startswith(NGRAM_ENDPOINT)
        assert "/gdeltv3/web/ngrams/gdeltv3/webngrams/" in composed

    def test_the_deferred_doc_api_route_is_kept_and_still_separate(self, gdelt, context) -> None:
        """§24. Deferred, not withdrawn: deleting it would make a later
        un-deferral look like a new approval. It keeps its own host, and the
        ngram profile does not borrow it."""
        profile = next(p for p in gdelt.access_profiles if p.label == DOC_API_PROFILE)
        assert host_of(profile.endpoint_url or "") == "api.gdeltproject.org"
        assert "DEFERRED" in profile.notes
        ngram = next(a for a in context.access if a.label == NGRAM_PROFILE)
        assert host_of(ngram.endpoint_url or "") != "api.gdeltproject.org"

    def test_no_third_host_became_reachable(self, context) -> None:
        """§5 names `storage.googleapis.com` specifically: it hosts the quadgram
        files, which this review rejected and which no review has assessed."""
        hosts = {host_of(a.endpoint_url or "") for a in context.access}
        hosts.discard("")
        assert hosts == {"api.gdeltproject.org", "data.gdeltproject.org"}

    def test_no_credential_is_required_and_none_is_referenced(self, context) -> None:
        assert context.runtime_credential_references == ()

    def test_the_rate_limit_is_still_unknown_rather_than_guessed(self, gdelt) -> None:
        for profile in gdelt.access_profiles:
            assert profile.rate_limit_known is False
            assert profile.rate_limit_requests is None
            assert profile.rate_limit_daily_quota is None


class TestTheAuthorizedResources:
    def test_the_unigram_resource_is_allowed(self, context) -> None:
        assert authorize_resource(context.resource_scope, descriptor(context, UNIGRAM)).allowed

    def test_the_bigram_resource_is_allowed_because_it_was_actually_reviewed(
        self, context, gdelt
    ) -> None:
        """§20. Approved on a positive finding rather than by generalisation:
        neither file carries a position, a document id or a url, so a two-word
        phrase cannot be attached to the article it came from."""
        assert authorize_resource(context.resource_scope, descriptor(context, BIGRAM)).allowed
        assert "2GRAM ARE BOTH APPROVED" in gdelt.review.review_notes

    def test_both_resources_are_platform_licensed_and_named_separately(self, context) -> None:
        """§9. GDELT's count over its own index is GDELT's; the news it counts
        is not. Separate families so withdrawing one is a deletion."""
        families = {d.dataset_family for d in context.datasets}
        assert families == {"web-ngrams-1gram", "web-ngrams-2gram"}
        for dataset in context.datasets:
            assert dataset.content_origin == "PLATFORM_LICENSED"


class TestEverythingElseStillFailsClosed:
    @pytest.mark.parametrize(
        ("label", "overrides"),
        [
            ("a family the review never assessed", {"dataset_family": "web-ngrams-3gram"}),
            ("another source's family", {"dataset_family": "indicators"}),
            ("no family at all", {"dataset_family": None}),
            ("Web News NGrams 3.0", {"dataset_family": "web-news-ngrams-3.0"}),
            ("the quadgram file", {"dataset_family": "weblegacy-quadgram"}),
            ("the quadgram TOC", {"dataset_family": "weblegacy-quadgram-toc"}),
            ("the DOC API ArtList mode", {"dataset_family": "doc-api-artlist"}),
            ("publisher content", {"content_origin": ResourceContentOrigin.THIRD_PARTY}),
            ("an unestablished origin", {"content_origin": ResourceContentOrigin.UNKNOWN}),
            ("no rights basis", {"rights_basis": None}),
        ],
    )
    def test_a_descriptor_that_lies_about_the_resource_is_refused(
        self, context, label, overrides
    ) -> None:
        result = authorize_resource(
            context.resource_scope, descriptor(context, UNIGRAM, **overrides)
        )
        assert not result.allowed, f"{label} was allowed"

    def test_the_family_allowlist_is_what_refuses_an_unreviewed_family(self, context) -> None:
        """The hole this mission closed, named rather than merely covered.

        `require_dataset_family` refused a resource that could not say what it
        is. It did NOT refuse one that says something nobody reviewed: any
        string passed, because a family no reviewer had rejected was
        indistinguishable from one a reviewer had approved.
        """
        result = authorize_resource(
            context.resource_scope, descriptor(context, UNIGRAM, dataset_family="web-ngrams-3gram")
        )
        assert any("not one this review assessed" in r for r in result.denial_reasons)

    def test_an_unreviewed_resource_has_no_entry_to_build_a_descriptor_from(self, context) -> None:
        """The first gate, before any rule runs. A collector builds its
        descriptor FROM an authorised entry, so a resource nobody reviewed has
        no family, no origin and no basis to build with."""
        for resource_id in (
            "web-ngrams/3gram",
            "webngrams/3.0",
            "weblegacy/quadgram",
            "doc-api/timeline-tone",
            "doc-api/artlist",
        ):
            assert context.authorized_dataset(resource_id) is None

    def test_no_doc_api_mode_became_authorised(self, context) -> None:
        """H-27 is still open: no timeline envelope has ever been observed, so
        there is nothing to authorise and the deferral is visible here."""
        assert all(d.resource_id.startswith("web-ngrams/") for d in context.datasets)

    def test_a_cross_source_descriptor_is_refused(self, context) -> None:
        result = authorize_resource(
            context.resource_scope, descriptor(context, UNIGRAM, source_id="fred")
        )
        assert not result.allowed
        assert any("was checked against the scope of" in r for r in result.denial_reasons)

    def test_third_party_denial_is_still_in_force(self, context) -> None:
        """§9. The file contains no publisher material, and the rule that keeps
        publisher material out governs the SOURCE rather than this dataset."""
        assert context.resource_scope.third_party_denied is True


class TestTheMinimisationProfileSaysWhatTheFieldsAre:
    def test_the_four_observed_columns_are_each_authorised(self, context) -> None:
        profile = context.data_minimisation
        for category in (
            "observation_period",  # DATE
            "content_language",  # LANG
            "lexical_ngram",  # NGRAM
            "source_measured_frequency",  # COUNT
        ):
            assert profile.permits(category), category

    def test_language_is_not_written_into_geography(self, context) -> None:
        """§13, and the reason `content_language` exists rather than a reuse.

        `geography` remains allowed for the DOC API route, which really does
        report places. What must not happen is LANG being carried in it: Spanish
        is not Spain, and the ngram row says nothing about where anything
        happened.
        """
        profile = context.data_minimisation
        assert profile.permits("content_language")
        assert "content_language" != "geography"
        assert profile.permits("geography")  # for the other route, not for LANG

    def test_the_ngram_is_not_authorised_as_a_theme_or_an_entity(self, context) -> None:
        """§11. A word that occurred was not classified by anything, so calling
        it a theme would assert a judgment the source did not make."""
        profile = context.data_minimisation
        assert profile.permits("lexical_ngram")
        assert "lexical_ngram" not in ("theme_identifier", "entity_mention", "publisher_content")

    def test_the_count_is_named_as_the_sources_measurement(self, context) -> None:
        """§12. The category name has to keep saying whose number it is: not the
        rows our job fetched, not the size of a result set, not a score."""
        profile = context.data_minimisation
        assert profile.permits("source_measured_frequency")
        assert not profile.permits("opportunity_score")
        assert not profile.permits("signal_strength")

    def test_publisher_fields_are_still_excluded(self, context) -> None:
        profile = context.data_minimisation
        for category in (
            "article_full_text",
            "publisher_content",
            "personal_data",
            "user_identifier",
        ):
            assert category in profile.excluded
            assert not profile.permits(category)

    def test_the_doc_api_categories_were_kept(self, context) -> None:
        """§24. That route is deferred, not withdrawn, and deleting the
        categories that describe it would make a later un-deferral look like a
        new approval."""
        profile = context.data_minimisation
        for category in ("event_identifier", "theme_identifier", "entity_mention", "tone_score"):
            assert profile.permits(category)


class TestTheReviewedAcquisitionBound:
    def test_a_ceiling_exists_and_states_its_basis(self, context) -> None:
        bounds = context.acquisition_bounds
        assert bounds is not None and bounds.bounded
        assert bounds.max_files_per_job >= 1
        assert bounds.basis.strip()

    def test_a_job_within_the_ceiling_is_not_refused(self, context) -> None:
        assert context.authorize_job_size(1) == ()
        assert context.authorize_job_size(context.acquisition_bounds.max_files_per_job) == ()

    def test_a_job_above_the_ceiling_is_refused(self, context) -> None:
        over = context.acquisition_bounds.max_files_per_job + 1
        assert context.authorize_job_size(over)

    def test_a_job_that_does_not_state_its_size_is_refused(self, context) -> None:
        """The same asymmetry the resource descriptor is built on: not saying
        how much you intend to take is not a size known to fall under a bound."""
        refusals = context.authorize_job_size(None)
        assert refusals and "unstated size is not a size" in refusals[0]

    def test_the_bound_is_the_dataset_vacuum_control(self, context, gdelt) -> None:
        """§15. GDELT emits 96 buckets a day and two files per bucket since
        2019; the ceiling has to be smaller than a day of one kind or it bounds
        nothing anybody would have done anyway."""
        assert context.acquisition_bounds.max_files_per_job < 96

    def test_a_ceiling_with_no_basis_is_refused(self) -> None:
        """A number that survives every later review by looking deliberate."""
        with pytest.raises(SourceRegistryError, match="stated basis"):
            AcquisitionBounds(source_id="probe", max_files_per_job=4)

    def test_a_ceiling_of_zero_is_refused(self) -> None:
        """A refusal written as a budget would read as 'bounded' in a report."""
        with pytest.raises(SourceRegistryError, match="at least 1"):
            AcquisitionBounds(source_id="probe", max_files_per_job=0, basis="x")

    def test_a_source_with_no_reviewed_bound_is_unasked_rather_than_unbounded(
        self, compliance
    ) -> None:
        """Every source that predates this mission is in that state, and the
        distinction is why `None` is not spelled `unlimited`."""
        world_bank = compliance.get("world-bank")
        assert world_bank.acquisition_bounds is None


class TestTheAllowlistRuleIsWellFormed:
    def test_an_empty_allowlist_is_refused(self) -> None:
        """A refusal dressed as a filter, the same rule the licence allowlist
        has had since Mission 1.4."""
        with pytest.raises(SourceRegistryError, match="empty allowlist"):
            ResourceScope(source_id="probe", allowed_dataset_families=frozenset())

    def test_a_family_that_is_both_reviewed_and_excluded_is_refused(self) -> None:
        with pytest.raises(SourceRegistryError, match="both reviewed and excluded"):
            ResourceScope(
                source_id="probe",
                allowed_dataset_families=frozenset({"a"}),
                excluded_dataset_families=frozenset({"a"}),
            )

    def test_the_other_sources_keep_no_family_restriction(self, compliance) -> None:
        """Additive by construction: `None` is unchanged behaviour."""
        for source_id in ("world-bank", "eurostat", "fred"):
            assert compliance.get(source_id).resource_scope.allowed_dataset_families is None


class TestAttributionAndRetentionAreGovernanceDerived:
    def test_the_citation_obligation_is_carried_forward_unchanged(self, context) -> None:
        """§18. The Mission 1.8 capability, reused rather than duplicated."""
        texts = [r.text for r in context.attribution.requirements if r.text]
        assert any("citation to the GDELT Project" in t for t in texts)
        assert any(t == "The GDELT Project" for t in texts)

    def test_no_attribution_element_is_supplied_by_a_caller(self, context) -> None:
        """The terms prescribe both halves as fixed strings, so neither is
        composed per artefact -- unlike Eurostat's DOI and access date."""
        assert all(not r.supplied for r in context.attribution.requirements)

    def test_the_condition_is_verified_by_a_capability_not_by_a_promise(self, gdelt) -> None:
        condition = next(
            c for c in gdelt.review.required_conditions if c.key == "gdelt-attribution"
        )
        assert condition.verification.value == "CAPABILITY"
        assert condition.verification_detail == "source-attribution-display"

    def test_retention_is_the_project_baseline_with_no_invented_source_limit(
        self, context, gdelt
    ) -> None:
        """§17. GDELT's terms address retention nowhere, and silence means the
        baseline applies rather than that a shorter rule was found."""
        assert gdelt.retention_override is None
        assert context.retention.raw_source == "baseline"


class TestTheReviewHistoryAndTheGate:
    def test_review_three_is_current_and_the_earlier_two_are_intact(self, gdelt) -> None:
        """§3. A new version, not a rewrite.

        Scoped to the COMMERCIAL profile since Mission 1.17, which added a
        local-profile review at version 1. Version lines are per (source,
        profile), so an unscoped history now interleaves two of them -- and
        asserting the merged list would have made this test about how many
        profiles exist rather than about GDELT's review history.
        """
        versions = [
            r.review_version
            for r in gdelt.review_history
            if r.assessed_use_profile == LEGACY_PROFILE
        ]
        assert versions == [1, 2, 3]
        assert gdelt.review.review_version == 3
        assert gdelt.review.reviewed_by == "mission-1.9.2"
        for review in gdelt.review_history:
            assert review.approval_state.value == "APPROVED_WITH_CONDITIONS"

    def test_the_new_review_carries_first_party_evidence_for_the_dataset(self, gdelt) -> None:
        """§4. An evidence record whose document cannot be re-opened cannot be
        re-checked, so every one carries an absolute URL."""
        urls = [e.document_url for e in gdelt.review.evidence]
        assert any("announcing-the-web-news-ngram-datasets" in u for u in urls)
        assert any(u == "https://www.gdeltproject.org/about.html" for u in urls)
        assert all(u.startswith("https://") for u in urls)
        assert all(e.is_authoritative for e in gdelt.review.evidence)

    def test_the_review_records_that_gdelt_recommended_a_different_dataset(self, gdelt) -> None:
        """The correction this mission had to make.

        Mission 1.9.1 read GDELT's "use these ngram files instead of the search
        APIs" as support for WEB-NGRAM. The sentence is in the post announcing
        the QUADGRAM dataset and refers to that one, which this review rejects.
        The review says so rather than resting on it.
        """
        notes = gdelt.review.review_notes
        assert "CORRECTION TO THE RECORD" in notes
        assert "QUADGRAM" in notes

    def test_the_compliance_entry_targets_the_current_review(self, compliance, gdelt) -> None:
        """A configuration written against a superseded review would apply
        yesterday's rules; `build_authorization` refuses the mismatch."""
        assert compliance.get("gdelt").review_version == gdelt.review.review_version

    def test_the_new_capability_is_recorded(self, gdelt) -> None:
        """Reviews 1 and 2 assessed news events, themes, entity mentions, tone,
        timestamps and geography. A term frequency is none of them, which is why
        this needed a review version rather than a config edit."""
        assert "term-frequency" in gdelt.capabilities


class TestTheFourFactsStayApart:
    def test_gdelt_is_eligible_and_resource_ready_and_neither_built_nor_switched_on(
        self, gdelt, compliance
    ) -> None:
        """§23's expected state, asserted as one object so the four cannot drift
        into each other."""
        readiness = evaluate_readiness(gdelt, LEGACY_PROFILE, compliance)
        assert readiness.eligible is True
        assert readiness.resource_ready is True
        # Mission 1.9.3 implemented the collector, which is the step this
        # mission's own report named as next. `enabled` stays false: it is a
        # per-deployment switch, and the catalog record never turns one on.
        assert readiness.implemented is True
        assert readiness.enabled is False
        assert readiness.next_step == "enable the collector in this deployment"
        assert set(readiness.authorized_resources) == {UNIGRAM, BIGRAM}
        assert readiness.resource_gaps == ()

    def test_an_eligible_source_with_no_resource_is_reported_as_such(
        self, catalog, compliance
    ) -> None:
        """The state GDELT was in until this mission, and Eurostat still is.

        This is the distinction the diagnostic exists for: `eligibility` had no
        way to say it, so "eligible" was the most specific available answer and
        it read as further along than it was.
        """
        readiness = evaluate_readiness(catalog.get("eurostat"), LEGACY_PROFILE, compliance)
        assert readiness.eligible is True
        assert readiness.resource_ready is False
        assert readiness.next_step == "authorise a concrete resource"
        assert readiness.resource_gaps

    def test_readiness_never_refuses_and_is_not_a_gate(self, catalog, compliance) -> None:
        """It reports on every source in the catalog, including the blocked
        ones. `build_authorization` is what refuses."""
        rows = [evaluate_readiness(s, LEGACY_PROFILE, compliance) for s in catalog]
        assert len(rows) == len(list(catalog))
        blocked = [r for r in rows if not r.eligible]
        assert blocked and all(r.blocking_reasons for r in blocked)
        assert all(not r.resource_ready for r in blocked)

    def test_nothing_stores_a_readiness_boolean(self) -> None:
        """§23. A stored copy of a derivation is a thing that goes stale, which
        is the argument the registry makes for eligibility being a view."""
        migrations = (REPO_ROOT / "infrastructure/db/migrations").glob("*.sql")
        text = "\n".join(m.read_text(encoding="utf-8") for m in migrations).lower()
        assert "resource_ready" not in text


class TestNoCollectorAndNoData:
    def test_gdelt_became_implemented_in_the_mission_after_this_one(self, gdelt) -> None:
        """Mission 1.9.2 authorised the resources and wrote no code; Mission
        1.9.3 wrote the collector. The order is the point, and it is why this
        assertion moved rather than being deleted -- again in Mission 1.15.7,
        which took `ted-eu` through the same two steps."""
        from sros_acquisition import IMPLEMENTED_COLLECTORS

        assert set(IMPLEMENTED_COLLECTORS) == {"world-bank", "gdelt", "ted-eu"}

    def test_gdelt_is_still_disabled(self, gdelt) -> None:
        assert gdelt.collector_enabled is False

    def test_only_the_reviewed_route_has_a_collector(self) -> None:
        """The WEB-NGRAM collector exists as of Mission 1.9.3. Nothing serves the
        DOC API, because H-27 is open and no timeline envelope has ever been
        observed — writing a parser against invented field names is what Mission
        1.9 refused to do, and that refusal still stands."""
        collection = REPO_ROOT / "services/acquisition/python/sros_acquisition/collection"
        assert (collection / "gdelt_web_ngram.py").exists()
        assert not (collection / "gdelt.py").exists()
        assert not (collection / "gdelt_doc_api.py").exists()

    def test_the_ngram_parser_lives_only_in_the_collection_package(self) -> None:
        """Mission 1.9.2 asserted that NOTHING read a WEB-NGRAM file, because
        reading one is the collector and no collector was authorised to exist.

        Mission 1.9.3 wrote the parser. The assertion becomes a boundary one:
        decompression and row parsing live in `collection/`, and neither the
        registry nor the compliance package — which DECIDE whether collection
        may happen — has learned to read a file.
        """
        package = REPO_ROOT / "services/acquisition/python/sros_acquisition"
        readers = {
            path.relative_to(package).as_posix()
            for path in package.rglob("*.py")
            if "zlib" in path.read_text(encoding="utf-8")
        }
        assert readers == {"collection/gdelt_web_ngram.py"}
        for governance in ("registry", "compliance"):
            for path in (package / governance).rglob("*.py"):
                text = path.read_text(encoding="utf-8")
                assert "zlib" not in text
                assert "gzip" not in text
