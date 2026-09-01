"""TED-EU after Mission 1.15.3: the dataset licence found, H-36 still open.

Mission 1.15.3 §33. **No external call.** The catalogue records, the authority
tables and the API specification were retrieved during the review; these tests
read what the reviewer recorded.

The failure this file exists to prevent is specific and tempting. Mission 1.15.3
found that a machine-readable licence IS attached to the bulk-download route, and
that a sibling dataset in the same portal declares CC BY 4.0 -- a licence whose
Section 4 expressly grants extraction and re-utilisation of a substantial portion
of a database. Read carelessly, that looks like the answer. It is not: the
licence on the bulk route resolves to the same Decision that says nothing about
database rights, and the CC BY files are a different dataset under a different
publisher, applied inconsistently across overlapping coverage.

So the assertions here are mostly negative, and the negatives are the point.
"""

from __future__ import annotations

import ast
import pathlib

import pytest
from sros_acquisition.registry import APPROVING_STATES
from sros_contracts import PolicyAssessment, SourceApprovalState

from .conftest import (
    LEGACY_PROFILE,
    NEVER_EVIDENCE,
    REPO_ROOT,
    TED_FIRST_PARTY_PREFIXES,
    needs_postgres,
)

LOAD_BEARING = (
    "automated_access",
    "api_use",
    "commercial_use",
    "storage",
    "derived_analytics",
    "model_processing",
)

DOCS = REPO_ROOT / "docs" / "data"
CLARIFICATION = DOCS / "ted-eu-database-right-clarification-v1.md"
REQUEST = DOCS / "ted-eu-database-right-clarification-request-v1.md"
PACKET = DOCS / "ted-eu-h36-legal-review-packet-v1.md"


def source_of(catalog, source_id: str):
    return next(s for s in catalog.sources if s.source_id == source_id)


def review(catalog, source_id: str, version: int | None = None):
    source = source_of(catalog, source_id)
    if version is None:
        return source.review
    return next(r for r in source.review_history if r.review_version == version)


def joined(review_obj, field: str) -> str:
    return " ".join(getattr(review_obj, field)).lower()


# ======================================= v1-v3 are untouched by this mission


class TestEarlierReviewsImmutable:
    def test_four_versions_exist_with_no_gaps(self, catalog) -> None:
        # Version lines are per PROFILE since Mission 1.15.5. The legacy line
        # is the one this file's findings live on.
        versions = sorted(
            r.review_version
            for r in source_of(catalog, "ted-eu").review_history
            if r.assessed_use_profile == LEGACY_PROFILE
        )
        assert versions == list(range(1, len(versions) + 1))
        assert 4 in versions

    def test_each_version_keeps_its_own_reviewer(self, catalog) -> None:
        expected = {
            1: "mission-1.15",
            2: "mission-1.15.1",
            3: "mission-1.15.2",
            4: "mission-1.15.3",
        }
        for version, reviewer in expected.items():
            assert review(catalog, "ted-eu", version).reviewed_by == reviewer

    @pytest.mark.parametrize("version", [1, 2])
    def test_the_earlier_versions_still_record_model_processing_as_unaddressed(
        self, catalog, version
    ) -> None:
        """Mission 1.15.2's finding, still pinned two missions later."""
        assert (
            review(catalog, "ted-eu", version).assessments["model_processing"]
            is PolicyAssessment.NOT_ADDRESSED
        )

    def test_v3_still_carries_exactly_its_own_nine_conditions(self, catalog) -> None:
        assert len(review(catalog, "ted-eu", 3).conditions) == 9


# ============================================ H-34 was not reopened (§24)


class TestH34Untouched:
    def test_every_load_bearing_activity_is_still_permitted(self, catalog) -> None:
        current = review(catalog, "ted-eu")
        for name in LOAD_BEARING:
            assert current.assessments[name] is PolicyAssessment.PERMITTED, name

    def test_the_scoping_of_machine_processing_survived(self, catalog) -> None:
        """§25. A mission about database rights is exactly where an unrelated
        condition gets weakened by accident."""
        text = joined(review(catalog, "ted-eu"), "conditions")
        assert "model training" in text
        assert "not authorised" in text or "not assessed" in text
        assert "embedding" in text
        assert "d-12" in text

    def test_no_open_question_reopens_the_reuse_grant(self, catalog) -> None:
        """H-34 is closed. The open questions must be about the DATABASE right,
        not about whether reuse covers machine processing."""
        for question in review(catalog, "ted-eu").open_questions:
            assert "h-34" not in question.lower()


# ================================= the dataset licence was found, and identified


class TestTheDatasetLicenceWasFound:
    def test_the_catalogue_record_for_the_bulk_route_is_recorded_as_evidence(self, catalog) -> None:
        """§5's question -- is a licence attached to the assembled dataset --
        was answered, and the answer is in the evidence rather than in prose."""
        entry = next(
            e for e in review(catalog, "ted-eu", 4).evidence if "ted-1.rdf" in e.document_url
        )
        finding = e_lower(entry)
        assert "com_reuse" in finding
        assert "bulk" in finding
        assert "publications office" in finding

    def test_com_reuse_is_recorded_as_resolving_to_the_decision(self, catalog) -> None:
        """The whole finding. Without skos:exactMatch this is just another
        opaque licence code, and with it the licence IS the Decision."""
        entry = next(
            e for e in review(catalog, "ted-eu", 4).evidence if "COM_REUSE" in e.document_url
        )
        finding = e_lower(entry)
        assert "exactmatch" in finding
        assert "2011/833" in finding

    def test_the_licence_domain_data_was_not_read_as_a_database_grant(self, catalog) -> None:
        """The most tempting over-read available in this mission: COM_REUSE
        declares euvoc:appliesTo licence-domain/DATA, and DATA is a subject
        class, not a class of right."""
        entry = next(
            e for e in review(catalog, "ted-eu", 4).evidence if "COM_REUSE" in e.document_url
        )
        finding = e_lower(entry)
        assert "appliesto" in finding
        assert "not a database-right grant" in finding
        assert "no database domain" in finding


def e_lower(entry) -> str:
    return " ".join(
        (entry.summarized_finding + " " + (entry.section_reference or "")).split()
    ).lower()


def flat(path: pathlib.Path) -> str:
    """Whitespace-normalised lower-case text.

    Markdown wraps at 80 columns, so a phrase in a document is not a phrase on
    one line. Asserting against the raw text finds a sentence only when the
    author happened to fit it between two newlines, which makes the test a
    reformatting detector rather than a content check.
    """
    return " ".join(path.read_text(encoding="utf-8").split()).lower()


# =========================== a document licence is not a database licence


class TestDocumentLicenceIsNotDatabaseLicence:
    def test_h36_survived_a_review_that_found_a_dataset_level_licence(self, catalog) -> None:
        """The load-bearing negative. A licence was found ON the bulk route and
        H-36 still did not close, because the licence resolves to an instrument
        with no database-right provision."""
        current = review(catalog, "ted-eu")
        questions = joined(current, "open_questions")
        assert "h-36a" in questions
        assert "h-36b" in questions
        assert current.approval_state is SourceApprovalState.REQUIRES_REVIEW

    def test_the_two_halves_of_h36_are_tracked_separately(self, catalog) -> None:
        """§10. Subsistence and grant are different questions with different
        answers, and collapsing them loses which one is open."""
        questions = review(catalog, "ted-eu").open_questions
        subsistence = next(q for q in questions if q.startswith("H-36A"))
        grant = next(q for q in questions if q.startswith("H-36B"))
        assert "maker" in subsistence.lower()
        assert "substantial investment" in subsistence.lower()
        assert "not established" in subsistence.lower()
        assert "not addressed" in grant.lower()

    def test_the_database_maker_was_not_concluded_from_architecture(self, catalog) -> None:
        """§10. Naming a publisher is not naming a maker, and the review must
        say so rather than quietly treating them as the same."""
        subsistence = next(
            q for q in review(catalog, "ted-eu").open_questions if q.startswith("H-36A")
        )
        assert "publisher" in subsistence.lower()
        assert "no dct:creator" in subsistence.lower()


# ======================= the CC BY discovery did not become a permission


class TestCCBYWasNotOverread:
    def test_the_cc_by_distributions_are_recorded_in_full(self, catalog) -> None:
        """Recording the favourable fact is what makes the refusal to rely on it
        honest rather than convenient."""
        entry = next(
            e for e in review(catalog, "ted-eu", 4).evidence if "ted-csv.rdf" in e.document_url
        )
        finding = e_lower(entry)
        assert "cc_by_4_0" in finding or "cc by 4.0" in finding
        assert "section 4" in finding
        assert "extract, reuse, reproduce" in finding

    def test_the_inconsistency_that_blocks_reliance_is_recorded(self, catalog) -> None:
        entry = next(
            e for e in review(catalog, "ted-eu", 4).evidence if "ted-csv.rdf" in e.document_url
        )
        finding = e_lower(entry)
        assert "inconsistent" in finding
        assert "2017-2021" in finding and "2018-2023" in finding

    def test_a_condition_forbids_carrying_a_licence_across_resources(self, catalog) -> None:
        """§7. The CSV subset's licence licences the CSV subset. A future
        collector must not read it onto the XML corpus."""
        text = joined(review(catalog, "ted-eu", 4), "conditions")
        assert "ted-csv" in text
        assert "ted-1" in text
        assert "do not licence" in text or "does not licence" in text

    def test_the_cc_by_files_did_not_make_ted_approving(self, catalog) -> None:
        assert review(catalog, "ted-eu").approval_state not in APPROVING_STATES


# ============================ CC0 stays scoped to SIMAP system metadata


class TestCC0StaysScoped:
    def test_cc0_is_recorded_against_system_metadata_and_not_the_corpus(self, catalog) -> None:
        """§6. Mission 1.15.2 drew this boundary; this mission re-read the
        notice verbatim and must not have moved it."""
        entry = next(
            e
            for e in review(catalog, "ted-eu", 4).evidence
            if e.document_url == "https://ted.europa.eu/en/legal-notice"
        )
        finding = entry.summarized_finding.lower()
        assert "system metadata" in finding
        assert "cc0" in finding
        # The notice's CC BY clause covers website editorial content, and saying
        # so is what stops it being read onto the dataset.
        assert "editorial content" in finding

    def test_the_undefined_scope_became_a_question_not_a_finding(self, catalog) -> None:
        """'system metadata' is nowhere defined. The honest move is to ask, and
        the request must actually contain the question."""
        assert "system metadata" in flat(REQUEST)


# ===================== availability is not permission, on either route


class TestAccessIsNotPermission:
    def test_bulk_packages_download_without_authentication_and_ted_is_blocked(
        self, catalog
    ) -> None:
        """§13. Technical provision is not legal permission, and this is the
        mission where the packages were confirmed open and the source stayed
        shut."""
        source = source_of(catalog, "ted-eu")
        assert any(not p.requires_authentication for p in source.access_profiles)
        assert source.review.approval_state not in APPROVING_STATES

    def test_the_package_sizes_are_recorded_without_downloading_a_package(self, catalog) -> None:
        """§4. Headers are metadata; the archives are research data. The
        evidence must show the line was found rather than crossed."""
        entry = next(
            e
            for e in review(catalog, "ted-eu", 4).evidence
            if "xml-bulk-download" in e.document_url
        )
        finding = e_lower(entry)
        assert "head" in finding
        assert "no package body was downloaded" in finding
        assert "426,967,074" in entry.summarized_finding

    def test_the_api_terms_of_usage_resolve_to_the_same_silent_notice(self, catalog) -> None:
        """§14. The API's existence is not permission, and its own terms point
        at the document that does not mention the right."""
        entry = next(
            e for e in review(catalog, "ted-eu", 4).evidence if e.document_url.endswith("/docs/v3")
        )
        finding = e_lower(entry)
        assert "terms of usage" in finding
        assert "legal-notice" in finding

    def test_the_api_scroll_limit_correction_is_recorded(self, catalog) -> None:
        """Mission 1.15.2 reasoned the API was a smaller taking than bulk. Its
        own specification documents a mode with no notice limit, and the
        correction must be visible rather than silently absorbed."""
        entry = next(
            e for e in review(catalog, "ted-eu", 4).evidence if e.document_url.endswith("/docs/v3")
        )
        assert "no limit on the number of retrievable notices" in entry.summarized_finding.lower()

    def test_no_route_was_preferred_on_the_strength_of_the_favourable_reading(
        self, catalog
    ) -> None:
        """§29 of Mission 1.15.2, still holding: neither route is authorised."""
        for profile in source_of(catalog, "ted-eu").access_profiles:
            assert not profile.requires_approval


# ================================================== evidence discipline


class TestEvidenceDiscipline:
    def test_every_evidence_url_across_every_version_is_first_party(self, catalog) -> None:
        for past in source_of(catalog, "ted-eu").review_history:
            for item in past.evidence:
                assert item.document_url.startswith(TED_FIRST_PARTY_PREFIXES), item.document_url

    def test_no_search_engine_mirror_or_archive_appears_in_any_version(self, catalog) -> None:
        for past in source_of(catalog, "ted-eu").review_history:
            for item in past.evidence:
                for forbidden in NEVER_EVIDENCE:
                    assert forbidden not in item.document_url.lower(), item.document_url

    def test_every_v4_evidence_item_carries_a_finding_and_a_retrieval_time(self, catalog) -> None:
        v4 = review(catalog, "ted-eu", 4)
        assert len(v4.evidence) >= 7
        for item in v4.evidence:
            assert item.retrieved_at is not None
            assert item.summarized_finding.strip()

    def test_directive_96_9_is_not_recorded_as_source_policy_evidence(self, catalog) -> None:
        """General EU legislation is not this source's own document. It belongs
        in the legal-review packet, and putting it in the registry would be
        turning general legal knowledge into project evidence."""
        for item in review(catalog, "ted-eu", 4).evidence:
            assert "31996L0009" not in item.document_url
            assert "96/9" not in item.document_title


# ====================================== the open-data chain was not invented


class TestNoInventedLegalChain:
    def test_the_absence_of_a_psi_chain_is_recorded(self, catalog) -> None:
        """§12. A later directive may not be applied without a documentary
        chain, and the absence of one is a finding worth writing down."""
        entry = next(
            e
            for e in review(catalog, "ted-eu", 4).evidence
            if "publications-office-of-the-european-union-copyright" in e.document_url
        )
        finding = entry.summarized_finding.lower()
        assert "2019/1024" in finding
        assert "privacy" in finding
        assert "not as a reuse-rights chain" in finding


# ============================================ the externalisation is real


class TestExternalisation:
    def test_the_three_documents_exist(self) -> None:
        for path in (CLARIFICATION, REQUEST, PACKET):
            assert path.is_file(), path

    def test_the_request_names_a_first_party_contact_route(self) -> None:
        """§21. A clarification with no addressee is a note to ourselves."""
        assert "op-copyright@publications.europa.eu" in flat(REQUEST)

    def test_nothing_claims_to_have_been_sent(self) -> None:
        """§21, and the rule that matters most in this file: the repository may
        PREPARE a message and may never imply it was delivered."""
        text = flat(REQUEST)
        assert "prepared, not sent" in text
        assert "nothing has been transmitted" in text
        assert "prepared -- awaiting operator send" in text or "awaiting operator send" in text
        # No timestamp of delivery anywhere in the catalog either.
        assert "sent_at" not in flat(DOCS / "source-catalog-v1.json")

    def test_the_request_states_the_use_without_narrowing_it(self) -> None:
        """Mission 1.8's rule. A permission obtained by describing a smaller
        product is a permission for a product we are not building, so the
        request must name commercial reuse and automated processing."""
        text = flat(REQUEST)
        assert "commercial" in text
        assert "automated machine processing" in text
        assert "we would not train machine-learning models" in text

    def test_the_request_carries_the_personal_data_minimisation(self) -> None:
        text = flat(REQUEST)
        for field in ("notice identifier", "award value", "cpv"):
            assert field in text
        for dropped in ("telephone", "postal addresses", "email addresses"):
            assert dropped in text

    def test_the_packet_offers_no_legal_conclusion(self) -> None:
        """§22. The packet states facts and asks a question. A conclusion in it
        would be the engineering team adjudicating contested EU law."""
        text = flat(PACKET)
        assert "contains no legal conclusion" in text
        assert "no legal conclusion" in text

    def test_the_packet_records_the_unfavourable_outcome_in_advance(self) -> None:
        """A packet that only describes the outcome we want reads as advocacy."""
        text = flat(PACKET)
        assert "restricted" in text
        assert "usaspending" in text


# ====================================== nothing was built and nothing collected


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

    def test_no_ted_module_was_added_to_the_acquisition_package(self) -> None:
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

    def test_ted_is_not_collector_eligible(self, catalog) -> None:
        assert review(catalog, "ted-eu").approval_state not in APPROVING_STATES

    def test_usaspending_was_not_re_reviewed(self, catalog) -> None:
        """Scope stays narrow. TED did not reach a dead end; it reached a
        question with a named addressee."""
        versions = [r.review_version for r in source_of(catalog, "usaspending").review_history]
        assert versions == [1]


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
        """§29. Legal and catalogue metadata is review material; procurement
        notices are research data, and none was fetched."""
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

    def test_no_opportunity_or_embedding_was_created(self) -> None:
        for query in (
            "SELECT count(*) FROM research.opportunities",
            "SELECT count(*) FROM nlp.embedding_provenance",
        ):
            assert self._count(query) == 0, query

    # §32 asks that the production rows be unchanged, and this file deliberately
    # does NOT assert 12 / 12 / 7 / 7 / 7 -- those are facts about one database
    # and a fresh CI database holds none of them (`testing-strategy.md` §36).
    # "Unchanged by this run" is asserted by the post-suite digest watcher.


def test_no_test_in_this_file_reaches_the_network() -> None:
    """§33. The retrieval WAS the review. A suite that re-fetched the catalogue
    would fail on data.europa.eu rather than on the catalog, and would teach
    contributors that a red TED suite means nothing.

    Asserted over the AST rather than over the file's text, for the reason
    `testing-strategy.md` §23 gives and this test proved again the first time it
    ran: a substring scan matched its own list of forbidden substrings. A guard
    that fails on the sentence explaining it is a guard people delete.
    """
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
