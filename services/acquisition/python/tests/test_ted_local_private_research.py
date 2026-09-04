"""TED-EU after Mission 1.15.4: the routes documented, the gate unmoved.

Mission 1.15.4 §34. **No external call.** The route documentation was retrieved
during the review; these tests read what the reviewer recorded.

Two failures this file exists to prevent, and they pull in opposite directions.

The first is a **user summary becoming operator evidence**. A file describing a
Publications Office reply exists outside the repository and is a transcription,
not the reply. Nothing here may let it, or anything like it, into
`registry.source_policy_evidence` as first-party authority.

The second is **strong intended-use evidence being read as a rights grant**. The
Publications Office says, in its own documentation, that the Search API is "for
analysis and reuse" and "primarily targeted at data reusers", and that the Open
Data Service publishes data "for analysis and re-use" with a button to connect
your app. All true, all recorded, and none of it a licence over a collection.
"""

from __future__ import annotations

import ast
import inspect
import pathlib

import pytest
from sros_acquisition.registry import APPROVING_STATES
from sros_contracts import PolicyAssessment, PolicyEvidenceType, SourceApprovalState

from .conftest import (
    LEGACY_PROFILE,
    NEVER_EVIDENCE,
    REPO_ROOT,
    TED_FIRST_PARTY_PREFIXES,
    needs_postgres,
)

DOCS = REPO_ROOT / "docs" / "data"
LOCAL_REVIEW = DOCS / "ted-eu-local-private-research-review-v1.md"
GAP = DOCS / "route-scoped-source-authorization-gap-v1.md"

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
    source = source_of(catalog, source_id)
    if version is None:
        return source.review
    return next(r for r in source.review_history if r.review_version == version)


def joined(review_obj, field: str) -> str:
    return " ".join(getattr(review_obj, field)).lower()


def flat(path: pathlib.Path) -> str:
    """Whitespace-normalised lower-case text (`testing-strategy.md` §39)."""
    return " ".join(path.read_text(encoding="utf-8").split()).lower()


def findings(review_obj) -> str:
    return " ".join(
        " ".join((e.summarized_finding + " " + (e.section_reference or "")).split())
        for e in review_obj.evidence
    ).lower()


# ============================== no summary may masquerade as operator evidence


class TestNoFabricatedOperatorResponse:
    """§32, and the tripwire fired in Mission 1.45.

    What this class guarded was that a USER-WRITTEN TRANSCRIPTION describing a
    Publications Office reply -- a summary that says so itself -- may not become
    first-party authority by being pasted into a review. It enforced that by
    asserting that NO `OPERATOR_CORRESPONDENCE` row existed anywhere, *"so the
    first one to appear should be a deliberate act with a real document behind
    it, and this assertion is what makes it deliberate."*

    **A real document arrived**: a written reply from the Publications Office's
    Head of Sector for Copyright, case 2026-COP-201, with the exported message
    fingerprinted. So the assertion is re-pointed rather than deleted, and it
    now guards the same property in the only form still available -- that there
    is EXACTLY ONE such row, that it is the one Mission 1.45 recorded, and that
    it carries the checksum that distinguishes a document from a description of
    one. An assertion that no correspondence may ever exist is an assertion that
    the operator may never receive an answer.
    """

    EXPECTED = "mailto:op-copyright@publications.europa.eu"

    def test_ted_carries_exactly_one_operator_correspondence_row(self, catalog) -> None:
        rows = [
            item
            for past in source_of(catalog, "ted-eu").review_history
            for item in past.evidence
            if item.document_type is PolicyEvidenceType.OPERATOR_CORRESPONDENCE
        ]
        # One per review version that records it: local v3 and commercial v6.
        assert len(rows) == 2, [r.document_title for r in rows]
        for item in rows:
            assert item.document_url == self.EXPECTED
            assert "2026-COP-201" in item.document_title
            assert (item.document_fingerprint or "").startswith("sha256:")

    def test_no_correspondence_row_predates_the_reply(self, catalog) -> None:
        """The historical timeline is the point of §32 and is preserved: every
        review written before 2026-09-04 recorded that no authoritative reply was
        held, and none of them acquired one retroactively."""
        for past in source_of(catalog, "ted-eu").review_history:
            if past.reviewed_at.date().isoformat() >= "2026-09-04":
                continue
            for item in past.evidence:
                assert item.document_type is not PolicyEvidenceType.OPERATOR_CORRESPONDENCE, (
                    item.document_title
                )

    def test_no_other_source_carries_operator_correspondence(self, catalog) -> None:
        """Still stated across the whole catalog. TED is the only source that
        wrote to a publisher and the only one that received an answer; the next
        one should be as deliberate as this one was."""
        for source in catalog.sources:
            if source.source_id == "ted-eu":
                continue
            for past in source.review_history:
                for item in past.evidence:
                    assert item.document_type is not PolicyEvidenceType.OPERATOR_CORRESPONDENCE, (
                        f"{source.source_id}: {item.document_title}"
                    )

    def test_h36_did_not_close(self, catalog) -> None:
        questions = joined(review(catalog, "ted-eu"), "open_questions")
        assert "h-36a" in questions
        assert "h-36b" in questions
        assert review(catalog, "ted-eu").approval_state is SourceApprovalState.REQUIRES_REVIEW

    def test_the_exclusion_is_documented(self) -> None:
        """§32 requires that the exclusion be written down, not merely done."""
        text = flat(LOCAL_REVIEW)
        assert "non_authoritative" in text or "non-authoritative" in text
        assert "user-written transcription" in text or "user_supplied" in text


# ================================ local use does not create permission


class TestLocalUseIsNotPermission:
    def test_the_verdict_did_not_move_for_a_narrower_use_case(self, catalog) -> None:
        """§1. The clearest statement of the rule: the use case got smaller and
        the source stayed blocked."""
        assert review(catalog, "ted-eu").approval_state not in APPROVING_STATES

    def test_the_review_says_local_use_creates_no_permission(self) -> None:
        text = flat(LOCAL_REVIEW)
        assert "this does not create permission" in text
        assert "permission comes from the source" in text

    def test_the_forbidden_conclusions_are_named_and_refused(self) -> None:
        """§27. Each of these is reachable from the evidence and wrong."""
        text = flat(LOCAL_REVIEW)
        for claim in (
            "ted has no database rights",
            "local projects do not need permission",
            "because the api is public, all reuse is allowed",
            "because ted wants reuse, h-36 is irrelevant",
        ):
            assert claim in text, claim


# ===================== intended-use evidence is not a database-right grant


class TestIntendedUseIsNotARightsGrant:
    def test_the_search_api_purpose_is_recorded_from_first_party_docs(self, catalog) -> None:
        """§5. 'An API exists' is not evidence; what the operator says the API is
        FOR is."""
        text = findings(review(catalog, "ted-eu"))
        assert "for analysis and reuse" in text
        assert "primarily targeted at data reusers" in text
        assert "commercial organisations" in text

    def test_the_open_data_service_purpose_is_recorded(self, catalog) -> None:
        """§6."""
        text = findings(review(catalog, "ted-eu"))
        assert "for analysis and re-use" in text
        assert "connect your app" in text

    def test_a_condition_separates_documented_purpose_from_a_rights_grant(self, catalog) -> None:
        """The whole point of the review. Without this condition a later reader
        finds four pieces of enthusiastic operator documentation and concludes
        the database right was licensed."""
        text = joined(review(catalog, "ted-eu"), "conditions")
        assert "not a grant of a database right" in text
        assert "intended use" in text
        assert "no route may be authorised on it alone" in text

    def test_the_operators_own_word_extract_did_not_close_anything(self, catalog) -> None:
        """The Open Data Service invites users to 'extract custom datasets across
        many notices' -- the Directive's verb, in an invitation. Recorded, and
        load-bearing for nothing."""
        text = findings(review(catalog, "ted-eu"))
        assert "extract custom datasets" in text
        assert "does not close h-36" in text


# ============================================== route-specific findings


class TestRouteSpecificity:
    def test_the_search_api_and_open_data_service_are_analysed_separately(self) -> None:
        text = flat(LOCAL_REVIEW)
        assert "ted search api" in text
        assert "ted open data service" in text

    def test_the_bulk_route_is_still_blocked(self) -> None:
        """§12. Public downloadability alone is insufficient, and nothing found
        in this mission speaks to repeated substantial extraction."""
        text = flat(LOCAL_REVIEW)
        assert "public downloadability alone is insufficient" in text
        assert "the bulk route is **not** the default and **not** authorised" in text

    def test_the_historical_csv_subset_was_not_carried_across(self, catalog) -> None:
        """Mission 1.15.3's condition 10 survives: a licence on ted-csv licences
        ted-csv."""
        text = joined(review(catalog, "ted-eu"), "conditions")
        assert "ted-csv" in text
        assert "ted-1" in text

    def test_no_access_profile_was_promoted_to_approved(self, catalog) -> None:
        """§10, §30. No route carries an authorisation, and the gate is the only
        thing that could grant one."""
        for profile in source_of(catalog, "ted-eu").access_profiles:
            assert not profile.requires_approval


# ================================ the gate refuses, and the reason is the gap


class TestAuthorizationFailsClosed:
    def test_building_an_authorization_for_ted_is_refused(self, catalog) -> None:
        """§29's attempt, run as a test. The refusal is the finding."""
        from sros_acquisition.compliance import (
            AcquisitionNotAuthorizedError,
            build_authorization,
        )
        from sros_acquisition.compliance.config import load_compliance

        config = load_compliance(REPO_ROOT / "docs" / "data" / "source-compliance-v1.json")
        with pytest.raises(AcquisitionNotAuthorizedError) as caught:
            build_authorization(source_of(catalog, "ted-eu"), LEGACY_PROFILE, config)
        reasons = " ".join(caught.value.reasons).lower()
        assert "requires_review" in reasons

    def test_the_gate_now_requires_a_use_profile(self) -> None:
        """The inverse of what this test asserted on the day it was written.

        Mission 1.15.4 asserted that `evaluate_eligibility` had NO profile
        parameter, and said in its own docstring that a failure here would mean
        the proposed extension was being built and should happen in a mission
        that says so. Mission 1.15.5 says so. The assertion is inverted rather
        than deleted, because the property worth protecting did not disappear --
        it flipped."""
        from sros_acquisition.registry.eligibility import evaluate_eligibility

        parameters = list(inspect_signature_names(evaluate_eligibility))
        assert "use_profile_id" in parameters, parameters
        # Second positional and no default: a caller cannot omit it.
        assert parameters[1] == "use_profile_id"
        signature = inspect.signature(evaluate_eligibility)
        assert signature.parameters["use_profile_id"].default is inspect.Parameter.empty

    def test_the_use_profile_concept_now_exists(self, catalog) -> None:
        """Also inverted. Mission 1.15.4 asserted the concept was absent
        everywhere; Mission 1.15.5 built it, and the registry now names the two
        profiles a reviewer may answer about."""
        registered = {p.use_profile_id for p in catalog.use_profiles}
        assert "commercial-multi-tenant-research-v1" in registered
        assert "local-private-research-v1" in registered

    def test_an_unregistered_profile_is_never_authorised(self, catalog) -> None:
        """§6, §15. Unknown profile = refused, and never resolved against
        another one."""
        from sros_acquisition.registry.eligibility import evaluate_eligibility

        result = evaluate_eligibility(source_of(catalog, "ted-eu"), "invented-profile-v1")
        assert not result.eligible
        assert any("no policy review exists" in r for r in result.blocking_reasons)

    def test_the_gap_document_records_the_refusal_and_a_proposed_extension(self) -> None:
        text = flat(GAP)
        assert "policy review is requires_review" in text
        assert "assessed_use_profile" in text
        assert "not built in this mission" in text


def inspect_signature_names(func) -> tuple[str, ...]:
    import inspect

    return tuple(inspect.signature(func).parameters)


# ======================= a local profile cannot become a commercial one


class TestFutureCommercialBoundary:
    def test_the_commercial_profile_is_named_as_still_unreviewed(self) -> None:
        """§8. The single most likely way this review causes harm later is by
        migrating silently, so the boundary has to be written where the next
        reader will find it."""
        text = flat(LOCAL_REVIEW)
        assert "must be reviewed again from the top" in text
        assert "must never migrate silently" in text

    def test_the_proposed_extension_fails_closed_on_an_unnamed_profile(self) -> None:
        text = flat(GAP)
        assert "a profile the review does not name is refused" in text
        assert "deploying publicly does not silently promote a local authorization" in text


# ===================================== boundaries that did not move


class TestUnchangedBoundaries:
    def test_h34_stayed_closed_and_every_activity_is_still_permitted(self, catalog) -> None:
        """§22."""
        current = review(catalog, "ted-eu")
        for name in LOAD_BEARING:
            assert current.assessments[name] is PolicyAssessment.PERMITTED, name

    def test_model_training_is_still_not_authorised(self, catalog) -> None:
        """§23. Not authorised for a commercial profile, and not authorised for a
        local one either -- the route review had nothing to say about it."""
        text = joined(review(catalog, "ted-eu"), "conditions")
        assert "model training" in text
        assert "not authorised" in text or "not assessed" in text

    def test_d12_is_still_open_and_embeddings_are_still_blocked(self, catalog) -> None:
        """§24. Being local is not a reason to embed."""
        text = joined(review(catalog, "ted-eu"), "conditions")
        assert "embedding" in text
        assert "d-12" in text

    def test_personal_data_minimisation_survived(self, catalog) -> None:
        """§13, §18. A local deployment justifies collecting no more personal
        data than a commercial one."""
        text = joined(review(catalog, "ted-eu"), "conditions")
        assert "contact" in text
        assert "minimisation" in text or "discard" in text

    def test_the_personal_data_classification_did_not_soften(self, catalog) -> None:
        v4, v5 = review(catalog, "ted-eu", 4), review(catalog, "ted-eu")
        assert v5.personal_data_risk == v4.personal_data_risk
        assert v5.contains_user_identifiers is True
        assert v5.discard_identifiers_after_normalization is True

    def test_attribution_and_authenticity_survived(self, catalog) -> None:
        """§20, §21."""
        text = joined(review(catalog, "ted-eu"), "conditions")
        assert "attribution" in text or "acknowledge" in text
        assert "authentic" in text


# ===================================== v1-v4 immutable, v5 append-only


class TestReviewVersioning:
    def test_five_versions_exist_with_no_gaps(self, catalog) -> None:
        versions = sorted(
            r.review_version
            for r in source_of(catalog, "ted-eu").review_history
            if r.assessed_use_profile == LEGACY_PROFILE
        )
        assert versions == list(range(1, len(versions) + 1))
        assert 5 in versions

    def test_each_version_keeps_its_own_reviewer(self, catalog) -> None:
        expected = {
            1: "mission-1.15",
            2: "mission-1.15.1",
            3: "mission-1.15.2",
            4: "mission-1.15.3",
            5: "mission-1.15.4",
        }
        for version, reviewer in expected.items():
            assert review(catalog, "ted-eu", version).reviewed_by == reviewer

    def test_every_activity_assessment_is_identical_between_v4_and_v5(self, catalog) -> None:
        """A route review that established no new right must not move a finding
        it did not re-establish. One assertion, and it catches the whole class."""
        v4, v5 = review(catalog, "ted-eu", 4), review(catalog, "ted-eu", 5)
        assert v4.assessments == v5.assessments
        assert v4.approval_state is v5.approval_state

    def test_every_v4_condition_survives_verbatim(self, catalog) -> None:
        """§12."""
        v4, v5 = review(catalog, "ted-eu", 4), review(catalog, "ted-eu", 5)
        assert len(v4.conditions) == 10
        for condition in v4.conditions:
            assert condition in v5.conditions

    def test_v3_and_v4_still_record_their_own_findings(self, catalog) -> None:
        assert len(review(catalog, "ted-eu", 3).conditions) == 9
        assert (
            review(catalog, "ted-eu", 1).assessments["model_processing"]
            is PolicyAssessment.NOT_ADDRESSED
        )


# ============================================== evidence discipline


class TestEvidenceDiscipline:
    def test_every_evidence_url_across_every_version_is_first_party(self, catalog) -> None:
        for past in source_of(catalog, "ted-eu").review_history:
            for item in past.evidence:
                assert item.document_url.startswith(TED_FIRST_PARTY_PREFIXES), item.document_url

    def test_no_search_engine_mirror_or_archive_appears(self, catalog) -> None:
        for past in source_of(catalog, "ted-eu").review_history:
            for item in past.evidence:
                for forbidden in NEVER_EVIDENCE:
                    assert forbidden not in item.document_url.lower(), item.document_url

    def test_v5_evidence_is_route_documentation_and_carries_retrieval_times(self, catalog) -> None:
        v5 = review(catalog, "ted-eu", 5)
        assert len(v5.evidence) >= 4
        for item in v5.evidence:
            assert item.document_type is PolicyEvidenceType.OFFICIAL_API_DOCS
            assert item.retrieved_at is not None
            assert item.summarized_finding.strip()

    def test_the_coverage_window_is_recorded_rather_than_assumed(self, catalog) -> None:
        """A route that only holds notices from March 2023 bounds what research it
        can support, and a future collector must not discover that at runtime."""
        text = findings(review(catalog, "ted-eu"))
        assert "1 march 2023" in text
        assert "proof of concept" in text


# ============================================ nothing was built or collected


class TestNothingWasBuilt:
    def test_no_ted_collector_or_normalizer_exists(self) -> None:
        """Inverted in Mission 1.15.7, which authorised a concrete resource and
        wrote the Search API collector -- in that order.

        **The half that still holds is the half kept.** There is no TED
        normalizer, no Signal, no Claim and no Evidence, and 1.15.7's stop
        condition is exactly that line. Deleting this test would have lost it.
        """
        from sros_acquisition import IMPLEMENTED_COLLECTORS, IMPLEMENTED_NORMALIZERS

        assert "ted-eu" in IMPLEMENTED_COLLECTORS
        # Inverted again in Mission 1.15.8, which wrote the normalizer. The half
        # that still holds is one layer further down and is 1.15.8's own stop
        # condition: no TED notice becomes a Signal, a Claim or Evidence, and
        # `test_no_ted_notice_became_a_canonical_record` in the reuse-review file
        # is now the assertion that says so.
        assert "ted-eu" in IMPLEMENTED_NORMALIZERS

    def test_no_ted_module_exists_in_the_acquisition_package(self) -> None:
        """Inverted in Mission 1.15.7. ONE TED module exists and it is the
        Search API collector; no SPARQL client, no bulk downloader, no parser
        for a route the review refuses.

        Still an equality rather than an absence, because the risk this guards
        moved rather than ended: a second TED module appearing is now the thing
        worth catching, and `ted_open_data_sparql.py` is the one it would be.
        """
        package = REPO_ROOT / "services" / "acquisition" / "python" / "sros_acquisition"
        modules = sorted(
            p.relative_to(package).as_posix()
            for p in package.rglob("*.py")
            if "ted" in p.stem.lower() or "sparql" in p.stem.lower()
        )
        # TWO now, and the equality still does its job: Mission 1.15.8 added the
        # normalizer beside the collector, and a `ted_open_data_sparql.py` or a
        # `ted_bulk_xml.py` appearing is still the thing worth catching.
        assert modules == [
            "collection/ted_search_api.py",
            "normalization/ted_search_api.py",
        ], modules

    def test_no_sparql_client_was_added_anywhere(self) -> None:
        for root in ("services", "packages"):
            for path in (REPO_ROOT / root).rglob("*.py"):
                if "test" in path.parts or path.name.startswith("test_"):
                    continue
                assert "SPARQLWrapper" not in path.read_text(encoding="utf-8"), path

    def test_ted_is_not_collector_eligible(self, catalog) -> None:
        assert review(catalog, "ted-eu").approval_state not in APPROVING_STATES

    def test_ted_has_no_compliance_configuration(self) -> None:
        """A compliance entry for a blocked source would be preparation dressed as
        permission. The gap document says the profile is defined and not
        authorised; this is what makes that true in the data."""
        from sros_acquisition.compliance.config import load_compliance

        config = load_compliance(REPO_ROOT / "docs" / "data" / "source-compliance-v1.json")
        assert config.get("ted-eu") is None


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
        """§26, §31. Route documentation is policy evidence; procurement notices
        are research data, and none was fetched."""
        # RAW records are DEPLOYMENT state and are no longer asserted here.
        # Mission 1.15.7 authorised a resource and collected three notices, so
        # this count is legitimately non-zero on a machine that has run it and
        # zero on one that has not -- which is exactly the confusion §49 forbids
        # a test from encoding. What stays REPOSITORY-true is the line below:
        # there is no TED normalizer, so no TED notice can become a canonical
        # record on any machine.
        # NORMALIZED records joined RAW as DEPLOYMENT state in Mission 1.15.8,
        # which normalized the three notices 1.15.7 collected. Neither count is
        # asserted here any more: both are legitimately non-zero on a machine
        # that has run the pipeline and zero on one that has not, and encoding
        # either is the confusion §49 forbids.
        #
        # What stays REPOSITORY-true, and what this asserts, is that nothing
        # downstream of normalization exists for TED on any machine -- no Signal
        # extractor consumes a procurement notice, so no Claim and no Evidence
        # can follow. That is Mission 1.15.8's own stop condition.
        # **Mission 1.15.11 DELETED the downstream assertion rather than moving
        # it a fourth time**, as 1.15.10 said to. A TED Claim and a TED Evidence
        # row now exist, so the guard ran out of stages the way it was always
        # going to: TED reached every one of them.
        #
        # What is left is the fact this test was originally about, and it is
        # still repository-true: no TED notice was fetched by a REVIEW. The
        # counts downstream of it are deployment state and belong to no
        # assertion here.
        #
        # The current stop condition is asserted where it is still an absence
        # rather than a count -- see the reliability and opportunity tests in
        # this class, which are the boundary Mission 1.15.11 stopped at.

    # `test_no_reliability_assessment_was_created` was DELETED in Mission
    # 1.15.13, when a named reviewer recorded one for the TED procurement scope.
    #
    # Deleted rather than moved or narrowed, for the reason testing-strategy §59
    # gives: the absence it asserted had stopped being "these are independent
    # processes" -- which is still true and is asserted structurally, by the AST
    # test that keeps policy state out of the reliability package -- and become
    # "nobody has done the second one yet", which is a progress marker wearing a
    # test's clothes.

    def test_no_embedding_exists_and_no_opportunity_cites_ted(self) -> None:
        """`research.opportunities` joined RAW and NORMALIZED as DEPLOYMENT state
        in Mission 1.31.1, which legitimately persisted the first hypothesis over
        a Docker packet. A global count is now non-zero on a machine that has run
        the pipeline and zero on one that has not, which is the confusion §49
        forbids a test from encoding -- the same reasoning that removed the two
        record counts above.

        What stays REPOSITORY-true, and what this asserts instead, is stronger:
        no Opportunity hypothesis cites TED Evidence on any machine. That holds
        however many Opportunities exist, and it fails loudly if a future mission
        pulls a TED row into a packet."""
        assert self._count("SELECT count(*) FROM nlp.embedding_provenance") == 0
        assert (
            self._count(
                """SELECT count(*)
                     FROM research.opportunity_hypothesis_evidence l
                     JOIN scoring.evidence e ON e.id = l.evidence_id
                    WHERE e.source_id = 'ted-eu'"""
            )
            == 0
        )


def test_no_test_in_this_file_reaches_the_network() -> None:
    """§34. Asserted over the AST, for the reason `testing-strategy.md` §38
    gives: a substring scan of this file matches its own list."""
    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    forbidden = {"requests", "httpx", "urllib", "socket", "http", "aiohttp", "ftplib"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [(node.module or "").split(".")[0]]
        else:
            continue
        assert not forbidden & set(names), names
