"""Mission 1.45 — the Publications Office reply, and what it may not be read as.

The failure mode this file guards is not a crash. It is a generous reading: a
first-party reply that is genuinely favourable being written up as one sentence
stronger than it is, in a repository where the write-up is what later missions
consult. Every negative assertion below names a claim the reply does NOT support.

`pytest`, not unittest: `run_pytest_suites.py` discovers this package.
"""

from __future__ import annotations

import json

import pytest
from sros_contracts import PolicyEvidenceType, SourceApprovalState

from .conftest import (
    LEGACY_PROFILE,
    LOCAL_PROFILE,
    REPO_ROOT,
    current_review_version,
    evidence_is_addressable,
)

DOCS = REPO_ROOT / "docs" / "data"
CATALOG = DOCS / "source-catalog-v1.json"
DOCUMENT = DOCS / "ted-eu-official-reuse-response-v1.md"

REPLY_DATE = "2026-09-04"
CASE_ID = "2026-COP-201"
MAILBOX = "mailto:op-copyright@publications.europa.eu"
FINGERPRINT = "sha256:faee1e541c88bbd254f0660d2ebdb89e70766eb532a2192174e856ec5f922f74"

RESIDUAL = "ted-database-right-residual-exposure-accepted"


def document() -> str:
    return DOCUMENT.read_text(encoding="utf-8")


def source_of(catalog, source_id: str = "ted-eu"):
    return next(s for s in catalog.sources if s.source_id == source_id)


def correspondence(catalog) -> list:
    return [
        item
        for past in source_of(catalog).review_history
        for item in past.evidence
        if item.document_type is PolicyEvidenceType.OPERATOR_CORRESPONDENCE
    ]


def current(catalog, profile: str):
    return source_of(catalog).review_for(profile)


def joined(review, field: str) -> str:
    return " ".join(getattr(review, field)).lower()


# ============================================ the document exists and is provenanced


class TestProvenance:
    def test_the_reply_is_recorded_as_operator_correspondence(self, catalog) -> None:
        rows = correspondence(catalog)
        assert rows, "the reply must be recorded as evidence, not only as prose"
        for item in rows:
            assert item.document_type is PolicyEvidenceType.OPERATOR_CORRESPONDENCE

    def test_the_sender_role_and_organisation_are_preserved(self, catalog) -> None:
        """§ Canonical governance provenance. A reply is authoritative because of
        WHO wrote it, so the role and the office travel with it."""
        text = " ".join(item.section_reference or "" for item in correspondence(catalog))
        assert "Head of Sector" in text
        assert "Copyright and legal issues" in text
        assert "Publications Office of the European Union" in text
        page = document()
        assert "Jose Antonio DOMÍNGUEZ ROJAS" in page
        assert "Head of Sector — Copyright and legal issues" in page
        assert "D.2 Contracts and Copyright" in page

    def test_the_date_and_case_identifier_are_preserved(self, catalog) -> None:
        for item in correspondence(catalog):
            assert CASE_ID in item.document_title
            assert item.retrieved_at.date().isoformat() == REPLY_DATE
        assert CASE_ID in document()
        assert REPLY_DATE in document()

    def test_the_artifact_is_fingerprinted_rather_than_copied(self, catalog) -> None:
        """The original carries a named official's direct telephone number and
        email and the operator's personal address, and this repository is public.
        What is preserved is the checksum and the operative text."""
        for item in correspondence(catalog):
            assert item.document_fingerprint == FINGERPRINT
        assert FINGERPRINT.removeprefix("sha256:") in document()
        assert not list(DOCS.glob("*.pdf")), "the artifact must not be committed"

    def test_correspondence_is_addressed_by_the_first_party_mailbox(self, catalog) -> None:
        """A letter has no URL. It names the mailbox the matter is re-opened
        through -- the address the TED legal notice itself publishes."""
        for item in correspondence(catalog):
            assert item.document_url == MAILBOX
            assert evidence_is_addressable(item)

    def test_the_legal_notice_and_the_reply_are_separate_basis_rows(self, catalog) -> None:
        """§ Legal-notice provenance. They establish related but distinct facts,
        and merging them would let one lend its authority to the other."""
        for profile in (LOCAL_PROFILE, LEGACY_PROFILE):
            rows = current(catalog, profile).evidence
            fresh = [r for r in rows if r.retrieved_at.date().isoformat() == REPLY_DATE]
            kinds = {r.document_type for r in fresh}
            assert PolicyEvidenceType.OPERATOR_CORRESPONDENCE in kinds
            assert PolicyEvidenceType.OFFICIAL_TERMS in kinds
            assert PolicyEvidenceType.OFFICIAL_LICENCE in kinds
            assert len(fresh) == 3, [r.document_title for r in fresh]


# ================================================ what the reply actually said


class TestTheReplyIsCarriedVerbatim:
    def test_commercial_and_non_commercial_reuse_are_both_recorded(self, catalog) -> None:
        for item in correspondence(catalog):
            assert "commercial and non-commercial purposes" in (item.excerpt or "")
        flat = " ".join(document().split())
        assert "both commercial and non-commercial" in flat

    def test_the_attribution_condition_is_recorded(self, catalog) -> None:
        for item in correspondence(catalog):
            assert "provided that the source is acknowledged" in (item.excerpt or "")
        assert "the source is acknowledged" in document()

    def test_the_copyright_notice_condition_is_recorded(self, catalog) -> None:
        for item in correspondence(catalog):
            assert "according to the copyright notice" in (item.excerpt or "")

    def test_the_database_statement_is_recorded_in_its_own_words(self, catalog) -> None:
        for item in correspondence(catalog):
            excerpt = item.excerpt or ""
            assert "Whether or not the European Union asserts copyright over the" in excerpt
            assert "should not prevent citizens or organisations" in excerpt

    def test_the_retrieval_method_statement_is_recorded(self, catalog) -> None:
        for item in correspondence(catalog):
            assert "way in which the data are retrieved is not relevant" in (item.excerpt or "")

    def test_the_excerpt_stays_a_reference_rather_than_a_copy(self, catalog) -> None:
        for item in correspondence(catalog):
            assert len(item.excerpt or "") <= 1000


# =========================================== the claims that may NOT be inferred


class TestNoOverclaim:
    FORBIDDEN = (
        "no database right exists",
        "no sui generis database right exists",
        "no sui generis right exists",
        "all database rights are waived",
        "waives all database rights",
        "all rights waived",
        "all ted data is cc0",
        "all ted content is cc0",
        "all ted fields are cc0",
        "unconditional reuse",
        "no attribution is required",
        "no attribution required",
        "unlimited redistribution",
        "unrestricted redistribution of source records",
        "legally risk-free",
        "legal guarantee",
        "no lawyer is needed",
        "unlimited licence",
        "all ted data is public domain",
        "right to bypass",
        "right to ignore rate limits",
    )

    def test_the_document_makes_none_of_the_forbidden_claims(self) -> None:
        """The document may NAME a claim in order to refuse it, so the scan runs
        over the assertions and not over the list that forbids them
        (`testing-strategy.md` §23)."""
        page = document()
        head, _, refusals = page.partition("**Does NOT establish.")
        refusals = refusals.split("## 5.")[0]
        body = (head + page.split("## 5.")[-1]).lower()
        for phrase in self.FORBIDDEN:
            assert phrase not in body, phrase
        # And the refusal block DOES name them, which is what makes it a refusal.
        assert "no database right exists" in refusals.lower()
        assert "all ted fields are cc0" in refusals.lower()

    def test_the_registry_makes_none_of_them_either(self, catalog) -> None:
        for profile in (LOCAL_PROFILE, LEGACY_PROFILE):
            review = current(catalog, profile)
            blob = (
                joined(review, "open_questions")
                + " "
                + joined(review, "conditions")
                + " "
                + (review.review_notes or "").lower()
            )
            for phrase in self.FORBIDDEN:
                assert phrase not in blob, (profile, phrase)

    def test_the_existence_of_a_database_right_was_not_flipped_to_no_right(self, catalog) -> None:
        """The load-bearing refusal. The reply says COPYRIGHT and says 'whether
        or not', and Directive 96/9/EC creates two different rights."""
        questions = joined(current(catalog, LOCAL_PROFILE), "open_questions")
        assert "not established" in questions
        assert "no_right_exists" not in questions
        assert "sui generis" in questions
        page = document().lower()
        assert "`not_established` was not changed to `no_right_exists`" in page

    def test_no_circumvention_is_authorised(self, catalog) -> None:
        """The reconciled question NAMES `any acquisition method is allowed` in
        order to refuse it, so asserting its absence would fail on the sentence
        doing the work (`testing-strategy.md` §23). What is asserted is the
        refusal."""
        for profile in (LOCAL_PROFILE, LEGACY_PROFILE):
            questions = joined(current(catalog, profile), "open_questions")
            assert "circumvention" in questions
            assert "rate-limit evasion" in questions
            assert "it is not 'any acquisition method is allowed'" in questions
            assert "governance continues to require an authorised technical route" in questions
        page = " ".join(document().split()).lower()
        assert "governance continues to require an authorised technical route" in page

    def test_structured_notice_fields_are_not_classified_cc0(self, catalog) -> None:
        questions = joined(current(catalog, LOCAL_PROFILE), "open_questions")
        assert "cc0 scope unresolved" in questions
        assert "no structured ted notice field is classified cc0" in questions
        assert (
            "no structured ted notice field is classified cc0 by this review" in document().lower()
        )


# ================================================= H-36A and H-36B, reconciled


class TestH36Reconciliation:
    def test_h36a_separates_existence_from_blocker_status(self, catalog) -> None:
        for profile in (LOCAL_PROFILE, LEGACY_PROFILE):
            questions = current(catalog, profile).open_questions
            h36a = next(q for q in questions if q.startswith("H-36A"))
            low = h36a.lower()
            assert "not established" in low
            assert "official first-party guidance indicates not a blocker" in low
            assert "copyright" in low and "sui generis" in low

    def test_h36b_records_retrieval_method_neutrality_and_bounds_it(self, catalog) -> None:
        for profile in (LOCAL_PROFILE, LEGACY_PROFILE):
            questions = current(catalog, profile).open_questions
            h36b = next(q for q in questions if q.startswith("H-36B"))
            low = h36b.lower()
            assert "retrieval-method neutrality for reuse" in low
            assert "not a database-right grant" in low
            assert "any acquisition method is allowed" in low  # named to refuse it

    def test_the_bulk_route_stays_blocked_for_a_new_reason(self, catalog) -> None:
        """The reply weakens the database-right reason and an independent one
        remains: bulk XML has no field selection, so minimisation cannot happen
        at acquisition."""
        questions = joined(current(catalog, LOCAL_PROFILE), "open_questions")
        assert "the bulk route stays blocked" in questions
        assert "no field selection" in questions
        compliance = json.loads((DOCS / "source-compliance-v1.json").read_text(encoding="utf-8"))
        ted = next(s for s in compliance["sources"] if s["source_id"] == "ted-eu")
        routes = ted["route_authorization"]
        blob = json.dumps(routes)
        assert "ted-bulk-xml" not in routes["allowed_labels"]
        assert "ted-bulk-xml" in routes["blocked_labels"], (
            "it must stay blocked BY NAME rather than merely absent"
        )
        assert blob  # the basis prose travels with it

    def test_the_catalogue_licence_mapping_is_not_marked_resolved(self, catalog) -> None:
        questions = joined(current(catalog, LOCAL_PROFILE), "open_questions")
        assert "not fully resolved" in questions
        assert "com_reuse" in questions
        assert "cc by" in questions


# ============================================== the three attribution regimes


class TestAttribution:
    def test_the_three_regimes_are_kept_apart(self, catalog) -> None:
        """No universal rule is invented for notices, editorial content and CC0
        material -- they carry different obligations."""
        conditions = joined(current(catalog, LOCAL_PROFILE), "conditions")
        assert "source acknowledgement is a condition of reuse of the notices" in conditions
        assert "article 6(2)(a)" in conditions
        assert "cc by 4.0 credit plus indication" in conditions
        assert "cc0 material carries no obligation" in conditions

    def test_the_attribution_condition_is_regrounded_not_invented(self, catalog) -> None:
        """`ted-attribution` already existed; what changed is its basis."""
        required = {c.key: c for c in current(catalog, LOCAL_PROFILE).required_conditions}
        assert "ted-attribution" in required
        assert "article 6(2)(a)" in required["ted-attribution"].description.lower()
        assert "stricter governs" in required["ted-attribution"].description.lower()

    def test_the_implementation_requirement_is_named(self) -> None:
        assert "TED_SOURCE_ATTRIBUTION_REQUIRED" in document()


# ============================================ the two profiles, evaluated apart


class TestProfilesAreEvaluatedIndependently:
    def test_the_local_profile_is_still_approving_with_conditions(self, catalog) -> None:
        review = current(catalog, LOCAL_PROFILE)
        assert review.approval_state is SourceApprovalState.APPROVED_WITH_CONDITIONS
        assert review.reviewed_by == "mission-1.45"

    def test_the_commercial_profile_is_still_requires_review(self, catalog) -> None:
        """Commercial purpose is now first-party supported. Commercial purpose is
        not unrestricted redistribution."""
        review = current(catalog, LEGACY_PROFILE)
        assert review.approval_state is SourceApprovalState.REQUIRES_REVIEW
        assert review.reviewed_by == "mission-1.45"

    def test_the_commercial_blocker_changed_identity_and_is_stated(self, catalog) -> None:
        questions = joined(current(catalog, LEGACY_PROFILE), "open_questions")
        assert "raw_redistribution" in questions
        assert "customer_facing_source_access" in questions
        assert "the clarification request enumerated its intended use and named none of them" in (
            questions
        )
        assert "external_model_egress` is not_assessed" in questions

    def test_the_commercial_blocker_is_not_recorded_on_the_local_profile(self, catalog) -> None:
        """The local profile forbids redistribution outright, so the commercial
        blocker is not its blocker and must not be copied into it."""
        questions = joined(current(catalog, LOCAL_PROFILE), "open_questions")
        assert "the commercial profile's blocker" not in questions

    def test_the_required_condition_set_is_unchanged_across_the_bump(self, catalog) -> None:
        """`docs/CLAUDE.md`: bumping a version is honest only when the required
        conditions are unchanged -- assert the equality, do not assume it."""
        history = source_of(catalog).review_history

        def keys(version: int) -> dict[str, str]:
            review = next(
                r
                for r in history
                if r.assessed_use_profile == LOCAL_PROFILE and r.review_version == version
            )
            return {c.key: c.verification.value for c in review.required_conditions}

        assert keys(2) == keys(current_review_version())


# ============================================ nothing downstream was touched


class TestSeparationFromReliability:
    def test_no_reliability_value_moved(self) -> None:
        """A more permissive reuse position must never raise a reliability.
        Reuse asks whether the data may be used; reliability asks how dependably
        a measurement supports a proposition."""
        resolution = json.loads(
            (DOCS / "second-pilot-convergent-reliability-resolution-v1.json").read_text(
                encoding="utf-8"
            )
        )
        values = {a["reliability"] for a in resolution["current_assessments"]}
        assert 0.5 in values
        assert 0.55 in values

    def test_the_ted_assessments_are_still_the_reviewed_ones(self) -> None:
        resolution = json.loads(
            (DOCS / "wikimedia-convergent-reliability-resolution-v1.json").read_text(
                encoding="utf-8"
            )
        )
        ted = [a for a in resolution["current_assessments"] if a["scope"]["source_id"] == "ted-eu"]
        assert sorted(a["reliability"] for a in ted) == [0.5, 0.55]
        for assessment in ted:
            assert assessment["reviewed_by"] == "thibchm"

    def test_the_disclaimer_is_recorded_as_a_future_basis_and_not_a_judgement(
        self, catalog
    ) -> None:
        conditions = joined(current(catalog, LOCAL_PROFILE), "conditions")
        assert "potential_future_reliability_basis" in conditions
        assert "is not a reliability value" in conditions
        assert "reuse rights and measurement dependability are different questions" in conditions

    def test_public_retrievability_is_not_confused_with_preservation(self, catalog) -> None:
        conditions = joined(current(catalog, LOCAL_PROFILE), "conditions")
        assert "public retrievability and internal preservation are different facts" in conditions
        assert "does not withdraw reuse permission for data lawfully obtained earlier" in conditions


class TestNothingWasCollectedOrChanged:
    def test_no_new_ted_resource_or_route_was_authorised(self) -> None:
        compliance = json.loads((DOCS / "source-compliance-v1.json").read_text(encoding="utf-8"))
        ted = next(s for s in compliance["sources"] if s["source_id"] == "ted-eu")
        routes = ted["route_authorization"]
        assert sorted(routes["allowed_labels"]) == ["ted-open-data-sparql", "ted-search-api"]
        assert routes["blocked_labels"] == ["ted-bulk-xml"]

    def test_the_minimisation_profile_was_not_broadened(self) -> None:
        """§ Personal data. This mission must not expand retention."""
        compliance = json.loads((DOCS / "source-compliance-v1.json").read_text(encoding="utf-8"))
        ted = next(s for s in compliance["sources"] if s["source_id"] == "ted-eu")
        minimisation = ted["data_minimisation"]
        for field in (
            "contact_point",
            "contact_name",
            "contact_email",
            "contact_telephone",
            "contact_fax",
            "postal_address",
            "natural_person_name",
            "personal_identifier",
        ):
            assert field in minimisation["excluded"], field
            assert field not in minimisation["allowed"], field

    def test_model_training_and_embeddings_are_unchanged(self, catalog) -> None:
        for profile in (LOCAL_PROFILE, LEGACY_PROFILE):
            conditions = joined(current(catalog, profile), "conditions")
            assert "model training was not assessed and is not authorised" in conditions
            assert "embeddings are likewise unassessed" in conditions
            profile_record = next(p for p in catalog.use_profiles if p.use_profile_id == profile)
            assert profile_record.model_training is False
            assert profile_record.embeddings is False

    def test_external_model_egress_was_not_moved(self, catalog) -> None:
        """§ H-39. Ordinary reuse is not egress to a third-party model provider,
        and this reply says nothing about one."""
        profiles = {p.use_profile_id: p for p in catalog.use_profiles}

        def egress(profile: str) -> str:
            value = profiles[profile].external_model_egress
            return getattr(value, "value", value)

        assert egress(LEGACY_PROFILE) == "NOT_ASSESSED"
        assert egress(LOCAL_PROFILE) == "PERMITTED_TO_APPROVED_PROVIDERS"


# ================================================= history was not rewritten


class TestHistoricalTruth:
    def test_every_earlier_review_is_untouched(self, catalog) -> None:
        history = source_of(catalog).review_history
        earlier = [r for r in history if r.reviewed_by != "mission-1.45"]
        assert len(earlier) == 7, [r.reviewed_by for r in earlier]
        for review in earlier:
            assert review.reviewed_at.date().isoformat() < REPLY_DATE

    def test_the_reply_is_append_only(self, catalog) -> None:
        history = source_of(catalog).review_history
        new = [r for r in history if r.reviewed_by == "mission-1.45"]
        assert {r.assessed_use_profile for r in new} == {LOCAL_PROFILE, LEGACY_PROFILE}
        for review in new:
            line = [
                r.review_version
                for r in history
                if r.assessed_use_profile == review.assessed_use_profile
            ]
            assert review.review_version == max(line)
            assert sorted(line) == list(range(1, len(line) + 1))

    def test_the_unsent_request_document_still_claims_nothing_was_sent(self) -> None:
        """The repository may PREPARE a message and may never imply it delivered
        one. The reply arriving does not retroactively make it the sender."""
        request = (DOCS / "ted-eu-database-right-clarification-request-v1.md").read_text(
            encoding="utf-8"
        )
        # The document itself explains that no `sent_at` is recorded, so scanning
        # for the token fails on the sentence stating the rule -- §23, met for the
        # third time inside this one test file.
        flat = " ".join(request.split())
        assert "Prepared, not sent." in flat
        assert "Nothing has been transmitted." in flat
        assert "No mail connector was used, no `sent_at`" in flat
        assert "AWAITING OPERATOR SEND" in flat
        assert "Nothing was sent, and nothing claims to have been." in flat

    def test_the_timeline_is_stated_rather_than_smoothed(self) -> None:
        page = document()
        assert "before 2026-09-04    no authoritative direct response held" in page
        assert "on     2026-09-04    direct first-party response received" in page


# ================================= the model gap the first correspondence found


class TestCorrespondenceLocator:
    def test_a_correspondence_row_needs_a_fingerprint(self) -> None:
        from datetime import UTC, datetime

        from sros_acquisition.registry.models import PolicyEvidence, SourceRegistryError

        def build(**overrides):
            base = dict(
                document_type=PolicyEvidenceType.OPERATOR_CORRESPONDENCE,
                document_title="t",
                document_url=MAILBOX,
                summarized_finding="f",
                retrieved_at=datetime.now(UTC),
                document_fingerprint=FINGERPRINT,
            )
            base.update(overrides)
            return PolicyEvidence(**base)

        build()  # the permitted shape
        with pytest.raises(SourceRegistryError):
            build(document_fingerprint=None)
        with pytest.raises(SourceRegistryError):
            build(document_fingerprint="   ")

    def test_only_correspondence_may_use_a_mailbox(self) -> None:
        from datetime import UTC, datetime

        from sros_acquisition.registry.models import PolicyEvidence, SourceRegistryError

        with pytest.raises(SourceRegistryError):
            PolicyEvidence(
                document_type=PolicyEvidenceType.OFFICIAL_TERMS,
                document_title="t",
                document_url=MAILBOX,
                summarized_finding="f",
                retrieved_at=datetime.now(UTC),
                document_fingerprint=FINGERPRINT,
            )

    def test_a_published_page_still_needs_no_fingerprint(self) -> None:
        """The rule was not tightened for the types it was already right for: a
        page is identified by its address, and demanding a hash would force a
        re-fetch to prove a row still valid."""
        from datetime import UTC, datetime

        from sros_acquisition.registry.models import PolicyEvidence

        PolicyEvidence(
            document_type=PolicyEvidenceType.OFFICIAL_TERMS,
            document_title="t",
            document_url="https://ted.europa.eu/en/legal-notice",
            summarized_finding="f",
            retrieved_at=datetime.now(UTC),
        )

    def test_the_migration_relaxes_nothing_else(self) -> None:
        sql = (
            REPO_ROOT
            / "infrastructure"
            / "db"
            / "migrations"
            / "0033_correspondence_evidence_locator.sql"
        ).read_text(encoding="utf-8")
        assert "OPERATOR_CORRESPONDENCE" in sql and "LEGAL_REVIEW" in sql
        assert "document_fingerprint IS NOT NULL" in sql
        assert "^https?://" in sql
        for forbidden in ("INSERT", "UPDATE ", "DELETE"):
            assert forbidden not in sql.upper().replace("UPDATED", ""), forbidden
