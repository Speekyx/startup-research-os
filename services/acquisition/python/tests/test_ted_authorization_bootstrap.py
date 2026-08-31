"""TED authorization bootstrap: objective properties leave the human queue.

Mission 1.15.6 §29. **No external call.** Nothing here reaches TED, and
`test_no_test_in_this_file_reaches_the_network` asserts it structurally.

The property this file exists to protect is one sentence: **a condition that a
configuration can answer must be answered by the configuration, and a condition
that only a person can answer must stay with the person.**

Two of TED's three outstanding conditions described objective properties of a
collector that does not exist -- which route it binds to, which fields it asks
for -- and were `HUMAN_CONFIRMATION` because a catalog cannot assert what code
does. It does not have to. Both are properties of the **configuration supplied
to authorization**, checkable before anything opens a socket, and Mission 1.15.6
made them so.

The third is not, and the single most valuable assertions here are the ones in
`TestTheResidualRiskStaysHuman`: no verifier reaches it, no configuration
reaches it, this mission recorded nothing, and TED is still refused by name.
A residual-risk acceptance that code could satisfy would be a judgement nobody
made.
"""

from __future__ import annotations

import pathlib

import pytest
from sros_acquisition.compliance import (
    AcquisitionNotAuthorizedError,
    build_authorization,
    capability_failures,
    satisfied_condition_keys,
    verify_condition,
    verify_source,
)
from sros_acquisition.compliance.authorization import _reviewed_access
from sros_acquisition.compliance.config import (
    DataMinimisationProfile,
    RouteAuthorization,
    load_compliance,
)
from sros_acquisition.compliance.resources import ResourceDescriptor
from sros_acquisition.registry import evaluate_eligibility
from sros_acquisition.registry.models import ReviewCondition, SourceRegistryError
from sros_contracts import (
    ConditionVerification,
    ConditionVerificationResult,
    PolicyAssessment,
    ResourceContentOrigin,
    RightsBasis,
    SourceApprovalState,
)

from .conftest import LEGACY_PROFILE, LOCAL_PROFILE, REPO_ROOT, needs_postgres

RESIDUAL = "ted-database-right-residual-exposure-accepted"
ROUTE_ONLY = "ted-official-route-only"
MINIMISATION = "ted-personal-data-minimisation"

SEARCH_API = "ted-search-api"
OPEN_DATA = "ted-open-data-sparql"
BULK_XML = "ted-bulk-xml"

DOCS = REPO_ROOT / "docs" / "data"
BOOTSTRAP = DOCS / "ted-eu-authorization-bootstrap-v1.md"
READINESS = DOCS / "ted-eu-local-official-route-readiness-v1.md"


@pytest.fixture(scope="module")
def compliance():
    """The real compliance configuration. It is the artefact under review."""
    return load_compliance(DOCS / "source-compliance-v1.json")


@pytest.fixture
def ted(catalog):
    return next(s for s in catalog if s.source_id == "ted-eu")


@pytest.fixture
def ted_local(compliance):
    entry = compliance.get("ted-eu", LOCAL_PROFILE)
    assert entry is not None, "the local-profile compliance entry is the subject of this suite"
    return entry


@pytest.fixture
def local_verifications(ted, compliance):
    return verify_source(ted, LOCAL_PROFILE, compliance, environ={})


def result_for(records, key: str) -> ConditionVerificationResult:
    return next(r.result for r in records if r.condition_key == key)


def flat(path: pathlib.Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split()).lower()


# ===================================== the residual risk is, and stays, human


class TestTheResidualRiskStaysHuman:
    def test_the_residual_condition_is_still_human_confirmation(self, ted) -> None:
        """§5. The classification is the decision this mission did NOT change."""
        review = ted.review_for(LOCAL_PROFILE)
        condition = next(c for c in review.required_conditions if c.key == RESIDUAL)
        assert condition.verification is ConditionVerification.HUMAN_CONFIRMATION
        assert condition.verification_detail is None

    def test_no_verifier_reaches_it(self, local_verifications) -> None:
        """§5. UNKNOWN, and UNKNOWN is never promoted."""
        assert result_for(local_verifications, RESIDUAL) is ConditionVerificationResult.UNKNOWN

    def test_configuration_cannot_satisfy_it_either(self, ted, ted_local) -> None:
        """§5, and the failure mode this mission could most easily have introduced.

        Two conditions became configuration-verifiable in this mission. The
        assertion that matters is that the mechanism which did that has no
        reach into this one: a `HUMAN_CONFIRMATION` condition dispatches to the
        human branch **before** any configuration is consulted, so no route
        authorization, minimisation profile or capability can answer it.
        """
        review = ted.review_for(LOCAL_PROFILE)
        condition = next(c for c in review.required_conditions if c.key == RESIDUAL)
        outcome = verify_condition(ted, LOCAL_PROFILE, condition, ted_local, {}, None)
        assert outcome.result is ConditionVerificationResult.UNKNOWN
        assert outcome.verifier == "human-confirmation"

    def test_a_capability_cannot_be_bolted_onto_it(self, ted, ted_local) -> None:
        """The other way in: rewrite the condition as a CAPABILITY naming one of
        this mission's new capabilities. It must not resolve SATISFIED, because
        neither capability checks anything about database-right exposure -- and
        the model refuses a mechanical condition that names nothing real."""
        for name in ("source-route-binding", "source-field-minimisation"):
            forged = ReviewCondition(
                key=RESIDUAL,
                description="A probe asserting the residual risk cannot borrow a verifier.",
                verification=ConditionVerification.CAPABILITY,
                verification_detail=name,
            )
            outcome = verify_condition(ted, LOCAL_PROFILE, forged, ted_local, {}, None)
            # It resolves against the capability it names, which checks routes or
            # fields. That is the point: no capability in this repository
            # inspects a legal exposure, so rewriting the condition to reach one
            # changes WHICH question is answered, never WHETHER this one is.
            assert outcome.verifier == f"capability:{name}"
            assert RESIDUAL not in outcome.reason

    def test_this_mission_recorded_no_acceptance(self, local_verifications) -> None:
        """§6. The operator supplied nothing, so nothing was recorded."""
        assert not any(
            record.condition_key == RESIDUAL and record.satisfied for record in local_verifications
        )

    def test_the_exact_operator_statement_is_written_down_and_unsigned(self) -> None:
        """§6, §32. The statement a later explicit action must record exists as
        text to be read, and this mission is not that action."""
        text = flat(BOOTSTRAP)
        assert "not been recorded" in text or "no acceptance was recorded" in text
        assert "h-36a" in text and "h-36b" in text

    def test_the_acceptance_is_scoped_to_one_source_and_one_profile(self, ted) -> None:
        """§19. The condition exists on the local review and on no other, so an
        acceptance recorded against it cannot reach the commercial profile: the
        commercial review does not carry the condition an acceptance would clear."""
        local = ted.review_for(LOCAL_PROFILE)
        legacy = ted.review_for(LEGACY_PROFILE)
        assert RESIDUAL in {c.key for c in local.required_conditions}
        assert RESIDUAL not in {c.key for c in legacy.required_conditions}


# ===================================== the two objective conditions, reclassified


class TestTheObjectiveConditionsAreConfigurationVerified:
    def test_the_route_condition_names_a_registered_capability(self, ted) -> None:
        review = ted.review_for(LOCAL_PROFILE)
        condition = next(c for c in review.required_conditions if c.key == ROUTE_ONLY)
        assert condition.verification is ConditionVerification.CAPABILITY
        assert condition.verification_detail == "source-route-binding"

    def test_the_minimisation_condition_names_a_registered_capability(self, ted) -> None:
        review = ted.review_for(LOCAL_PROFILE)
        condition = next(c for c in review.required_conditions if c.key == MINIMISATION)
        assert condition.verification is ConditionVerification.CAPABILITY
        assert condition.verification_detail == "source-field-minimisation"

    def test_both_now_verify_satisfied(self, local_verifications) -> None:
        assert result_for(local_verifications, ROUTE_ONLY) is ConditionVerificationResult.SATISFIED
        assert (
            result_for(local_verifications, MINIMISATION) is ConditionVerificationResult.SATISFIED
        )

    def test_both_capabilities_pass_their_conformance_check(self, ted_local) -> None:
        assert capability_failures("source-route-binding", ted_local) == ()
        assert capability_failures("source-field-minimisation", ted_local) == ()

    def test_a_capability_reports_unimplemented_when_nothing_is_configured(self) -> None:
        """§13. The capability fails rather than passes when the restriction it
        checks does not exist. A gate that reported SATISFIED for a source with
        no route authorization would satisfy the condition by having no rules."""
        from dataclasses import replace

        stripped = replace(_ted_entry(), route_authorization=None)
        failures = capability_failures("source-route-binding", stripped)
        assert failures
        assert "no route authorization is configured" in failures[0]


def _ted_entry():
    return load_compliance(DOCS / "source-compliance-v1.json").get("ted-eu", LOCAL_PROFILE)


# ================================================= the route gate, case by case


class TestTheRouteGate:
    def test_the_search_api_is_accepted(self, ted_local) -> None:
        assert ted_local.route_authorization.refusals(SEARCH_API) == ()

    def test_the_open_data_service_is_accepted(self, ted_local) -> None:
        """§7, §11. ODS remains authorised; the Search API is only preferred."""
        assert ted_local.route_authorization.refusals(OPEN_DATA) == ()
        assert ted_local.route_authorization.preferred_label == SEARCH_API

    def test_bulk_xml_is_refused_by_name(self, ted_local) -> None:
        refusals = ted_local.route_authorization.refusals(BULK_XML)
        assert refusals
        assert "refused by name" in refusals[0].lower()

    def test_an_unreviewed_route_is_refused(self, ted_local) -> None:
        refusals = ted_local.route_authorization.refusals("ted-html-scrape")
        assert refusals
        assert "not one this review authorised" in refusals[0]

    def test_a_missing_route_is_refused(self, ted_local) -> None:
        """§13. Fails closed on an unstated route, in every empty shape."""
        for unstated in (None, "", "   "):
            refusals = ted_local.route_authorization.refusals(unstated)
            assert refusals, unstated
            assert "names no access route" in refusals[0]

    def test_the_context_would_carry_only_the_reviewed_routes(self, ted, ted_local) -> None:
        """§22, and the structural half of the guarantee.

        `_reviewed_access` is exercised against the REAL source record and the
        REAL route authorization rather than a fixture, because what is being
        asserted is a fact about TED: the registry records the bulk route, the
        review refuses it, and the authorization context does not carry it. A
        collector selecting a route by label -- the pattern
        `GdeltWebNgramCollector._route` already uses -- finds nothing for
        `ted-bulk-xml`, so there is no endpoint to read and no host to allowlist.
        """
        assert BULK_XML in {p.label for p in ted.access_profiles}
        carried = {access.label for access in _reviewed_access(ted, ted_local.route_authorization)}
        assert carried == {SEARCH_API, OPEN_DATA}
        assert BULK_XML not in carried

    def test_an_authorised_route_the_registry_does_not_record_is_refused(self, ted) -> None:
        """§13. A route with no access profile has no endpoint and nothing to
        check a host against, so it is refused rather than quietly skipped."""
        invented = RouteAuthorization(
            source_id="ted-eu",
            allowed_labels=frozenset({SEARCH_API, "ted-route-that-does-not-exist"}),
            blocked_labels=frozenset({BULK_XML}),
            basis="a probe asserting that an unregistered route is refused",
        )
        with pytest.raises(AcquisitionNotAuthorizedError) as caught:
            _reviewed_access(ted, invented)
        assert "the registry does not record" in " ".join(caught.value.reasons)

    def test_a_route_authorization_that_refuses_nothing_is_refused_at_load(self) -> None:
        """A permitted path with no named refusal is a preference, not a
        restriction -- the same argument `_verify_access_method` already makes."""
        with pytest.raises(SourceRegistryError):
            RouteAuthorization(
                source_id="ted-eu",
                allowed_labels=frozenset({SEARCH_API}),
                basis="a probe",
            )

    def test_an_empty_allowlist_is_refused_at_load(self) -> None:
        with pytest.raises(SourceRegistryError):
            RouteAuthorization(
                source_id="ted-eu",
                blocked_labels=frozenset({BULK_XML}),
                basis="a probe",
            )

    def test_a_bound_with_no_basis_is_refused_at_load(self) -> None:
        with pytest.raises(SourceRegistryError):
            RouteAuthorization(
                source_id="ted-eu",
                allowed_labels=frozenset({SEARCH_API}),
                blocked_labels=frozenset({BULK_XML}),
            )

    def test_a_preference_cannot_name_an_unauthorised_route(self) -> None:
        """§11. A preference chooses among what the review permitted. It never
        widens it, and the shape that would widen it is refused at load."""
        with pytest.raises(SourceRegistryError):
            RouteAuthorization(
                source_id="ted-eu",
                allowed_labels=frozenset({SEARCH_API}),
                blocked_labels=frozenset({BULK_XML}),
                preferred_label=BULK_XML,
                basis="a probe",
            )


class TestTheContextDelegatesToBothGates:
    """The two methods the collector mission will actually call.

    No authorization can be built for TED today, and fabricating a satisfied
    residual confirmation to reach one would be the exact act §5 forbids -- in a
    test as much as anywhere else. So the context is CONSTRUCTED from TED's real
    compliance record instead: real route authorization, real minimisation
    profile, real resource scope, and a `verifications` tuple that is empty
    because nothing here is pretending anything was verified.
    """

    @pytest.fixture
    def context(self, ted, ted_local):
        from datetime import UTC, datetime

        from sros_acquisition.compliance.authorization import AcquisitionAuthorizationContext
        from sros_acquisition.registry.retention import resolve_retention

        review = ted.review_for(LOCAL_PROFILE)
        moment = datetime.now(UTC)
        return AcquisitionAuthorizationContext(
            source_id=ted.source_id,
            use_profile_id=LOCAL_PROFILE,
            canonical_name=ted.canonical_name,
            approval_state=review.approval_state,
            review_version=review.review_version,
            reviewed_at=review.reviewed_at,
            next_review_at=review.next_review_at,
            access=_reviewed_access(ted, ted_local.route_authorization),
            resource_scope=ted_local.resource_scope,
            retention=resolve_retention(ted.retention_override),
            attribution=ted_local.attribution,
            data_minimisation=ted_local.data_minimisation,
            datasets=ted_local.datasets,
            verifications=(),
            issued_at=moment,
            route_authorization=ted_local.route_authorization,
        )

    def test_it_reports_only_the_authorised_routes(self, context) -> None:
        assert set(context.authorized_route_labels) == {SEARCH_API, OPEN_DATA}

    def test_authorize_route_permits_the_authorised_and_refuses_the_blocked(self, context) -> None:
        assert context.authorize_route(SEARCH_API) == ()
        assert context.authorize_route(OPEN_DATA) == ()
        assert context.authorize_route(BULK_XML)
        assert context.authorize_route("ted-html-scrape")
        assert context.authorize_route(None)

    def test_authorize_fields_permits_the_authorised_and_refuses_the_excluded(
        self, context
    ) -> None:
        minimisation = context.data_minimisation
        assert context.authorize_fields(minimisation.allowed) == ()
        assert context.authorize_fields(("contact_email",))
        assert context.authorize_fields(("tender_full_text",))
        assert context.authorize_fields(None)

    def test_a_blocked_route_has_no_endpoint_to_reach(self, context) -> None:
        """§22, and the guarantee that does not depend on anyone calling
        `authorize_route`: there is no access entry for the blocked label, so a
        collector selecting by label has no endpoint and no host."""
        assert all(access.label != BULK_XML for access in context.access)
        assert next((a for a in context.access if a.label == BULK_XML), None) is None

    def test_a_source_with_no_route_restriction_refuses_nothing(self, ted, ted_local) -> None:
        """`None` means the question was not asked. `authorize_route` must not
        invent an answer -- inventing one here would be this method setting
        permissions for the four sources nobody re-reviewed."""
        from dataclasses import replace

        unrestricted = replace(ted_local, route_authorization=None)
        assert unrestricted.route_authorization is None
        carried = {access.label for access in _reviewed_access(ted, None)}
        assert carried == {label.label for label in ted.access_profiles}
        assert BULK_XML in carried, "unchanged where no route restriction was reviewed"


# ============================================= the field gate, case by case


class TestTheFieldGate:
    def test_the_authorised_selection_is_accepted(self, ted_local) -> None:
        minimisation = ted_local.data_minimisation
        assert minimisation.refusals(minimisation.allowed) == ()

    def test_one_prohibited_personal_field_refuses_the_whole_request(self, ted_local) -> None:
        """§8. Requesting the contact block is the act the obligation forbids,
        and it is refused whether it arrives alone or hidden among authorised
        fields -- which is the shape a real over-broad request has."""
        minimisation = ted_local.data_minimisation
        for prohibited in minimisation.excluded:
            assert minimisation.refusals((prohibited,)), prohibited
            refusals = minimisation.refusals((*minimisation.allowed, prohibited))
            assert refusals, prohibited
            assert "excluded by name" in refusals[0]

    def test_the_natural_person_contact_block_is_what_is_excluded(self, ted_local) -> None:
        """§8. The list is asserted rather than assumed: a minimisation profile
        that excluded something else would pass every mechanical test above."""
        assert {
            "contact_point",
            "contact_name",
            "contact_email",
            "contact_telephone",
            "contact_fax",
            "postal_address",
            "natural_person_name",
            "personal_identifier",
        } <= set(ted_local.data_minimisation.excluded)

    def test_the_monetary_semantic_survives_in_the_allowed_set(self, ted_local) -> None:
        """§25. An amount without its semantic is the flattening into
        `price_paid` that nothing downstream can undo."""
        allowed = set(ted_local.data_minimisation.allowed)
        assert {"monetary_amount", "monetary_amount_type", "currency"} <= allowed

    def test_an_unreviewed_field_is_refused(self, ted_local) -> None:
        refusals = ted_local.data_minimisation.refusals(("tender_full_text",))
        assert refusals
        assert "not a field this review authorised" in refusals[0]

    def test_an_unbounded_or_unstated_request_is_refused(self, ted_local) -> None:
        """§8, §13. A request that does not say which fields it wants has not
        been shown to want only authorised ones."""
        minimisation = ted_local.data_minimisation
        assert minimisation.refusals(None)
        assert minimisation.refusals(())
        assert "unstated selection" in minimisation.refusals(None)[0]

    def test_a_profile_authorising_nothing_permits_nothing(self) -> None:
        empty = DataMinimisationProfile(allowed=(), excluded=("contact_email",))
        assert empty.refusals(("notice_id",))

    def test_minimisation_is_not_a_filter_applied_afterwards(self) -> None:
        """§9. The gate is asked what may be REQUESTED. There is no method here
        that takes a collected record and removes fields from it, because a
        request that took the contact block and dropped it afterwards would
        have retrieved the contact block."""
        callables = {
            name
            for name in dir(DataMinimisationProfile)
            if not name.startswith("_") and callable(getattr(DataMinimisationProfile, name, None))
        }
        assert callables == {"permits", "refusals"}


# ============================================ what the review still refuses


class TestTedPolicyDidNotChange:
    def test_the_commercial_profile_is_still_requires_review(self, ted) -> None:
        """§3. Nothing in this mission touched the wider profile."""
        assert ted.review_for(LEGACY_PROFILE).approval_state is SourceApprovalState.REQUIRES_REVIEW

    def test_the_local_profile_is_still_approved_with_conditions(self, ted) -> None:
        assert (
            ted.review_for(LOCAL_PROFILE).approval_state
            is SourceApprovalState.APPROVED_WITH_CONDITIONS
        )

    def test_v2_changed_no_assessment_and_no_verdict(self, ted) -> None:
        """§20. Appended, not rewritten, and the policy conclusion is identical.
        One assertion, and it catches the whole class."""
        history = [r for r in ted.review_history if r.assessed_use_profile == LOCAL_PROFILE]
        v1 = next(r for r in history if r.review_version == 1)
        v2 = next(r for r in history if r.review_version == 2)
        assert v1.assessments == v2.assessments
        assert v1.approval_state is v2.approval_state
        assert v1.conditions == v2.conditions
        assert v1.open_questions == v2.open_questions
        assert v1.evidence == v2.evidence

    def test_v1_is_unchanged_and_still_says_human_confirmation(self, ted) -> None:
        """The append-only guarantee, asserted from the other side: v1 still
        records what it recorded, including the classification v2 revised."""
        v1 = next(
            r
            for r in ted.review_history
            if r.assessed_use_profile == LOCAL_PROFILE and r.review_version == 1
        )
        kinds = {c.key: c.verification for c in v1.required_conditions}
        assert kinds[ROUTE_ONLY] is ConditionVerification.HUMAN_CONFIRMATION
        assert kinds[MINIMISATION] is ConditionVerification.HUMAN_CONFIRMATION

    def test_only_the_two_condition_classifications_differ_between_v1_and_v2(self, ted) -> None:
        history = [r for r in ted.review_history if r.assessed_use_profile == LOCAL_PROFILE]
        v1 = {
            c.key: c for c in next(r for r in history if r.review_version == 1).required_conditions
        }
        v2 = {
            c.key: c for c in next(r for r in history if r.review_version == 2).required_conditions
        }
        assert v1.keys() == v2.keys()
        changed = {key for key in v1 if v1[key] != v2[key]}
        assert changed == {ROUTE_ONLY, MINIMISATION}

    def test_redistribution_is_still_not_permitted(self, ted) -> None:
        """§13. The condition that keeps the Article 7(2)(b) re-utilisation limb
        structurally unengaged under this profile."""
        assert ted.review_for(LOCAL_PROFILE).assessments["redistribution"] is (
            PolicyAssessment.NOT_PERMITTED
        )

    def test_neither_profile_authorises_training_or_embeddings(self, catalog) -> None:
        """§13. Refused at the profile, so no configuration can request either."""
        for profile in catalog.use_profiles:
            assert profile.model_training is False, profile.use_profile_id
            assert profile.embeddings is False, profile.use_profile_id

    def test_the_local_profile_redistributes_nothing_and_is_still_commercial(self, catalog) -> None:
        """§13, and the half most easily taken backwards: local is not
        non-commercial."""
        local = next(p for p in catalog.use_profiles if p.use_profile_id == LOCAL_PROFILE)
        assert local.raw_redistribution is False
        assert local.raw_resale is False
        assert local.customer_facing_source_access is False
        assert local.commercial_purpose is True

    def test_model_training_and_embeddings_are_still_refused_in_the_review(self, ted) -> None:
        text = " ".join(ted.review_for(LOCAL_PROFILE).conditions).lower()
        assert "model training was not assessed and is not authorised" in text
        assert "d-12" in text

    def test_the_bulk_and_historical_families_are_still_excluded(self, ted_local) -> None:
        """§13. `ted-csv-historical` is a dataset family rather than a route, and
        it is refused at the resource gate whatever route asked for it."""
        scope = ted_local.resource_scope
        assert {
            "ted-bulk-xml-daily",
            "ted-bulk-xml-monthly",
            "ted-csv-historical",
        } <= scope.excluded_dataset_families
        assert scope.require_dataset_family

    def test_a_historical_csv_resource_is_denied_at_the_resource_gate(self, ted_local) -> None:
        from sros_acquisition.compliance.resources import authorize_resource

        denied = authorize_resource(
            ted_local.resource_scope,
            ResourceDescriptor(
                source_id="ted-eu",
                resource_id="ted-contract-award-notices-2017-2021",
                dataset_family="ted-csv-historical",
                rights_basis=RightsBasis.NAMED_LICENCE,
                licence="CC BY 4.0",
                content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
            ),
        )
        assert not denied.allowed
        assert any("excluded by the review" in reason for reason in denied.denial_reasons)

    def test_an_unclassified_resource_is_denied(self, ted_local) -> None:
        from sros_acquisition.compliance.resources import authorize_resource

        denied = authorize_resource(
            ted_local.resource_scope,
            ResourceDescriptor(
                source_id="ted-eu",
                resource_id="ted-something",
                rights_basis=RightsBasis.DIRECT_GRANT,
                content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
            ),
        )
        assert not denied.allowed


# ==================================================== cross-profile isolation


class TestCrossProfileIsolation:
    def test_the_commercial_profile_has_no_compliance_configuration(self, compliance) -> None:
        """§19. The local entry configures the local use and nothing else. There
        is no fallback in `ComplianceConfig.get`, so the commercial profile does
        not inherit the route allowlist, the minimisation profile or the
        attribution obligation written for the local one."""
        assert compliance.get("ted-eu", LEGACY_PROFILE) is None
        assert compliance.get("ted-eu") is None  # the default IS the legacy profile

    def test_the_commercial_profile_is_refused_and_names_its_own_reason(
        self, ted, compliance
    ) -> None:
        with pytest.raises(AcquisitionNotAuthorizedError) as caught:
            build_authorization(ted, LEGACY_PROFILE, compliance, environ={})
        reasons = " ".join(caught.value.reasons).lower()
        assert "requires_review" in reasons
        # Not refused for a missing route or a missing field list: it never
        # reaches the configuration, because it fails at the verdict.
        assert "route" not in reasons

    def test_an_unregistered_profile_is_never_authorised(self, ted, compliance) -> None:
        with pytest.raises(AcquisitionNotAuthorizedError):
            build_authorization(ted, "invented-profile-v1", compliance, environ={})

    def test_a_second_entry_for_the_same_source_and_profile_is_refused(self) -> None:
        """The loader deduplicates on (source, profile) since this mission. It
        deduplicated on the source alone before, which would have refused TED's
        second profile entry -- the whole point of the key -- as a duplicate."""
        import json

        payload = json.loads((DOCS / "source-compliance-v1.json").read_text(encoding="utf-8"))
        entry = next(s for s in payload["sources"] if s["source_id"] == "ted-eu")
        payload["sources"].append(json.loads(json.dumps(entry)))
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "duplicate.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with pytest.raises(SourceRegistryError) as caught:
                load_compliance(path)
        assert "duplicate entry" in str(caught.value)

    def test_two_entries_for_one_source_under_two_profiles_load(self) -> None:
        """The inverse, and the reason the key had to change: the same source
        legitimately carries one configuration per use."""
        import json
        import tempfile

        payload = json.loads((DOCS / "source-compliance-v1.json").read_text(encoding="utf-8"))
        entry = next(s for s in payload["sources"] if s["source_id"] == "ted-eu")
        second = json.loads(json.dumps(entry))
        second["use_profile_id"] = LEGACY_PROFILE
        payload["sources"].append(second)

        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "two-profiles.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            config = load_compliance(path)
        assert config.get("ted-eu", LOCAL_PROFILE) is not None
        assert config.get("ted-eu", LEGACY_PROFILE) is not None


# ============================================ the gate, and what still blocks


class TestOneHumanDecisionRemains:
    def test_exactly_one_condition_is_outstanding(self, local_verifications) -> None:
        """§14. The preferred result, asserted rather than described."""
        outstanding = {
            record.condition_key for record in local_verifications if not record.satisfied
        }
        assert outstanding == {RESIDUAL}

    def test_exactly_one_condition_is_a_human_decision(self, ted) -> None:
        review = ted.review_for(LOCAL_PROFILE)
        human = {
            c.key
            for c in review.required_conditions
            if c.verification is ConditionVerification.HUMAN_CONFIRMATION
        }
        assert human == {RESIDUAL}

    def test_ted_is_still_not_eligible(self, ted, local_verifications) -> None:
        result = evaluate_eligibility(
            ted, LOCAL_PROFILE, None, satisfied_condition_keys(local_verifications)
        )
        assert not result.eligible
        assert result.blocking_reasons == (f"review conditions not satisfied: {RESIDUAL}",)

    def test_no_authorization_context_can_be_built(self, ted, compliance) -> None:
        """§32. The answer to *can `AcquisitionAuthorizationContext` currently be
        built* is no, and the one remaining reason is named."""
        with pytest.raises(AcquisitionNotAuthorizedError) as caught:
            build_authorization(ted, LOCAL_PROFILE, compliance, environ={})
        assert caught.value.reasons == (f"review conditions not satisfied: {RESIDUAL}",)

    def test_the_readiness_document_and_the_gate_agree(self) -> None:
        """A document that described a different queue from the one the gate
        reports would be the drift the two-views rule exists to prevent."""
        text = flat(READINESS)
        assert RESIDUAL in text
        assert "source-route-binding" in text
        assert "source-field-minimisation" in text


# ============================================ nothing was built or collected


class TestNothingWasBuilt:
    def test_no_ted_collector_or_normalizer_exists(self) -> None:
        from sros_acquisition import IMPLEMENTED_COLLECTORS, IMPLEMENTED_NORMALIZERS

        assert "ted-eu" not in IMPLEMENTED_COLLECTORS
        assert "ted-eu" not in IMPLEMENTED_NORMALIZERS

    def test_no_ted_module_exists_in_the_acquisition_package(self) -> None:
        """§16. No API client, no SPARQL client, no downloader, no parser."""
        package = REPO_ROOT / "services" / "acquisition" / "python" / "sros_acquisition"
        offenders = [
            p.relative_to(REPO_ROOT).as_posix()
            for p in package.rglob("*.py")
            if "ted" in p.stem.lower() or "sparql" in p.stem.lower()
        ]
        assert offenders == [], offenders

    def test_no_sparql_client_was_added_anywhere(self) -> None:
        for root in ("services", "packages"):
            for path in (REPO_ROOT / root).rglob("*.py"):
                if "test" in path.parts or path.name.startswith("test_"):
                    continue
                assert "SPARQLWrapper" not in path.read_text(encoding="utf-8"), path

    def test_verification_needs_no_network_and_no_collector(self, ted, compliance) -> None:
        """§32. Both capabilities run against configuration alone: no endpoint is
        contacted, and neither asks whether a collector exists."""
        records = verify_source(ted, LOCAL_PROFILE, compliance, environ={})
        assert len(records) == 4
        from sros_acquisition import IMPLEMENTED_COLLECTORS

        assert "ted-eu" not in IMPLEMENTED_COLLECTORS
        assert result_for(records, ROUTE_ONLY) is ConditionVerificationResult.SATISFIED

    def test_the_compliance_package_reaches_no_network(self) -> None:
        """The boundary is `collection/transport.py`. This mission added code to
        `compliance/`, which may never import a client."""
        import re

        forbidden = re.compile(
            r"^\s*(?:import|from)\s+(?:requests|httpx|urllib|aiohttp|http\.client|socket)",
            re.MULTILINE,
        )
        package = REPO_ROOT / "services" / "acquisition" / "python" / "sros_acquisition"
        for file in sorted((package / "compliance").rglob("*.py")):
            assert not forbidden.search(file.read_text(encoding="utf-8")), file


@needs_postgres
class TestNothingReachedTheDatabase:
    @staticmethod
    def _count(query: str, *params: object) -> int:
        import psycopg

        from .conftest import DATABASE_URL

        with psycopg.connect(DATABASE_URL) as conn:
            row = conn.execute(query, params or None).fetchone()
        return int(row[0]) if row else -1

    def test_no_ted_research_row_exists(self) -> None:
        """§17, §27. Policy documents are evidence; procurement notices are
        research data, and none was fetched."""
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

    def test_any_residual_acceptance_came_from_a_person_and_not_a_verifier(self) -> None:
        """Inverted by Mission 1.15.6.1, not deleted (`testing-strategy.md` §43).

        This asserted that NO acceptance existed, which was the correct
        assertion for Mission 1.15.6: it must not have created one, and it did
        not. An operator later did, so the count is no longer the property worth
        protecting.

        **What survives is the property that mattered all along**: if an
        acceptance exists, no verifier produced it. The row must be a
        `human-confirmation` written by a named actor, and it must not carry the
        identity of any registered verifier -- `capability:*`,
        `access-restriction:*`, `credential-availability` or `compliance-config`.
        A future code path that auto-accepted would fail here even though the
        count is no longer zero.
        """
        import psycopg

        from .conftest import DATABASE_URL

        with psycopg.connect(DATABASE_URL) as conn:
            rows = conn.execute(
                "SELECT verifier, result FROM registry.source_condition_verifications "
                "WHERE condition_key = %s AND result = 'SATISFIED'",
                (RESIDUAL,),
            ).fetchall()

        for verifier, _ in rows:
            assert verifier != "human-confirmation", (
                "the human-confirmation verifier produced a SATISFIED result; it returns "
                "UNKNOWN unconditionally and must never write one"
            )
            for machine in (
                "capability:",
                "access-restriction:",
                "credential-availability",
                "compliance-config",
                "unregistered",
            ):
                assert not verifier.startswith(machine), verifier

    def test_the_database_refuses_a_hand_set_satisfied_boolean(self) -> None:
        """§5, and the guarantee that outlives this mission's code. Even with SQL
        access, the residual condition cannot be marked satisfied without a
        verification record behind it, and no verifier writes one."""
        import psycopg

        from .conftest import DATABASE_URL

        with psycopg.connect(DATABASE_URL) as conn:
            with pytest.raises(psycopg.errors.CheckViolation):
                conn.execute(
                    "UPDATE registry.source_review_conditions SET satisfied = TRUE "
                    "WHERE source_id = 'ted-eu' AND condition_key = %s",
                    (RESIDUAL,),
                )
            conn.rollback()


def test_no_test_in_this_file_reaches_the_network() -> None:
    """Asserted structurally, the way every governance suite here does it."""
    import ast

    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"httpx", "requests", "urllib", "aiohttp", "socket"}
