"""Silence is not permission, and what it took to make that mechanical.

Mission 1.8. Two things are covered here and they are the same thing seen from
opposite ends.

**The rule.** An approving review must positively PERMIT every activity the
assessed use materially requires. Mission 1.7 approved `pypi` with four of the
six recorded `NOT_ADDRESSED`, on a review whose own notes described the basis as
"the absence of a prohibition covering us plus the presence of a documented
API". The prose rule forbidding exactly that had existed since Mission 1.0 and
did not stop it, because nothing read the prose.

**The exception that proves it.** `gdelt` is the only source added in Mission
1.7 whose approval survives the rule, and it became collector-eligible in the
same mission that downgraded three others -- by having its one real obligation
made verifiable, not by anything being relaxed.
"""

from __future__ import annotations

import pytest
from sros_acquisition.compliance import build_authorization, load_compliance, verify_source
from sros_acquisition.compliance.resources import ResourceDescriptor
from sros_acquisition.registry import APPROVING_STATES, evaluate_eligibility
from sros_contracts import (
    ConditionVerification,
    ConditionVerificationResult,
    PolicyAssessment,
    ResourceContentOrigin,
    RightsBasis,
    SourceApprovalState,
)

from .conftest import LEGACY_PROFILE, REPO_ROOT, needs_postgres, recorded_satisfied_keys

# The activities the assessed use case names in so many words: automated
# collection by a COMMERCIAL multi-tenant SaaS for STORAGE, DERIVED ANALYTICS
# and LLM PROCESSING. Duplicated from the validator on purpose and asserted
# equal to it below, so the two cannot drift apart silently.
REQUIRED_ACTIVITIES = (
    "automated_access",
    "api_use",
    "commercial_use",
    "storage",
    "derived_analytics",
    "model_processing",
)
GRANTING = {PolicyAssessment.PERMITTED, PolicyAssessment.PERMITTED_WITH_CONDITIONS}


@pytest.fixture(scope="session")
def compliance():
    return load_compliance(REPO_ROOT / "docs/data/source-compliance-v1.json")


class TestSilenceIsNotPermission:
    def test_no_approving_review_rests_on_an_unaddressed_required_activity(self, catalog) -> None:
        """The rule itself, over the real catalog.

        Not "pypi is not approving" -- that would pass the day somebody
        approved a different source the same way.
        """
        for source in catalog:
            review = source.review
            if review is None or review.approval_state not in APPROVING_STATES:
                continue
            ungranted = [a for a in REQUIRED_ACTIVITIES if review.assessment(a) not in GRANTING]
            assert not ungranted, (
                f"{source.source_id} is {review.approval_state.value} while "
                f"{', '.join(ungranted)} has no grant behind it"
            )

    def test_a_documented_api_alone_does_not_grant_commercial_use(self, catalog) -> None:
        """§4's precise wording, asserted as a property of the catalog.

        `automated_access` and `api_use` being permitted is what a documented,
        unprohibited API buys. It buys nothing else, and a source holding only
        those two must not be approving.
        """
        for source in catalog:
            review = source.review
            if review is None:
                continue
            api_only = (
                review.assessment("api_use") in GRANTING
                and review.assessment("commercial_use") not in GRANTING
            )
            if api_only:
                assert review.approval_state not in APPROVING_STATES, (
                    f"{source.source_id}: api_use is permitted and commercial_use is "
                    f"{review.assessment('commercial_use').value}, yet the source is "
                    f"{review.approval_state.value}"
                )

    def test_the_validator_and_this_test_check_the_same_activities(self) -> None:
        """Two copies of one list drift, and the drift is silent.

        The validator runs with nothing installed (ADR-009) so it cannot import
        this module; the lists are compared instead of shared.
        """
        source = (REPO_ROOT / "infrastructure/scripts/validate_source_registry.py").read_text(
            encoding="utf-8"
        )
        block = source.split("REQUIRED_ACTIVITIES = (")[1].split(")")[0]
        in_validator = tuple(
            line.strip().strip('",') for line in block.strip().splitlines() if line.strip()
        )
        assert in_validator == REQUIRED_ACTIVITIES

    def test_pypi_is_no_longer_approving_and_its_history_survives(self, catalog) -> None:
        """The specific case, and the history that explains it.

        Version 1 is kept because the useful record is that the reasoning was
        written down correctly and acted on incorrectly.
        """
        pypi = catalog.get("pypi")
        assert pypi.review.approval_state is SourceApprovalState.REQUIRES_REVIEW
        versions = [r.review_version for r in pypi.review_history]
        assert versions == [1, 2]
        first = pypi.review_history[0]
        assert first.approval_state is SourceApprovalState.APPROVED_WITH_CONDITIONS
        assert first.reviewed_by == "mission-1.7"

    def test_a_downgraded_source_carries_no_conditions_and_states_what_is_missing(
        self, catalog
    ) -> None:
        for source_id in ("pypi", "npm-registry", "wikimedia-pageviews"):
            review = catalog.get(source_id).review
            assert review.approval_state is SourceApprovalState.REQUIRES_REVIEW, source_id
            assert not review.required_conditions, (
                f"{source_id}: a non-approving review must not carry conditions -- "
                "a condition is what an approving review depends on"
            )
            assert review.open_questions, source_id


class TestGdeltIsConfiguredFromItsEvidenceAndNothingElse:
    def test_every_reviewed_condition_is_represented(self, catalog) -> None:
        """One obligation, one condition.

        §6 forbids inferring conditions that merely sound sensible. GDELT's
        review states exactly one: cite the project and link to it. An access
        restriction and a dataset allowlist would both have been plausible and
        neither is in the evidence, so neither is here.
        """
        review = catalog.get("gdelt").review
        assert [c.key for c in review.required_conditions] == ["gdelt-attribution"]
        (condition,) = review.required_conditions
        assert condition.verification is ConditionVerification.CAPABILITY
        assert condition.verification_detail == "source-attribution-display"

    def test_attribution_reuses_the_shared_capability(self, catalog, compliance) -> None:
        entry = compliance.get("gdelt")
        assert entry is not None
        elements = {r.element.value for r in entry.attribution.requirements}
        assert elements == {"SOURCE_CREDIT", "EXACT_NOTICE"}

    def test_the_exact_notice_is_preserved_verbatim(self, catalog, compliance) -> None:
        """§8: where wording must be exact, preserve it exactly.

        The notice has to appear in the evidence that prescribed it, or it was
        composed here -- which is the one thing a required notice may not be.
        """
        from sros_contracts import AttributionElement

        entry = compliance.get("gdelt")
        requirement = entry.attribution.requirement(AttributionElement.EXACT_NOTICE)
        assert requirement is not None and requirement.text
        corpus = " ".join(
            (item.summarized_finding or "") + " " + (item.excerpt or "")
            for item in catalog.get("gdelt").review.evidence
        )
        for fragment in ("citation to the GDELT Project", "gdeltproject.org"):
            assert fragment in corpus, fragment

    def test_no_rate_limit_was_invented(self, catalog) -> None:
        """§11. GDELT publishes none, so both profiles say so.

        The temptation is a "reasonable default"; a collector would read it as
        the provider's number.
        """
        for profile in catalog.get("gdelt").access_profiles:
            assert profile.rate_limit_known is False
            assert profile.rate_limit_requests is None
            assert profile.rate_limit_daily_quota is None
            assert profile.rate_limit_origin is None

    def test_no_credential_condition_was_manufactured(self, catalog) -> None:
        """§12. GDELT needs no key, so it gets no CONFIG_REFERENCE condition."""
        for profile in catalog.get("gdelt").access_profiles:
            assert profile.secret_references == ()
            assert profile.requires_api_key is False
            assert profile.requires_authentication is False
        kinds = {c.verification for c in catalog.get("gdelt").review.required_conditions}
        assert ConditionVerification.CONFIG_REFERENCE not in kinds

    def test_only_the_reviewed_access_methods_appear(self, catalog) -> None:
        """§9. Two documented routes, and nothing that would need circumvention.

        The bulk profile was renamed in Mission 1.9.2. It had been a placeholder
        naming the bulk route in general and carrying no endpoint, so it
        authorised no host; review 3 assessed ONE dataset family on ONE path and
        the profile now records that path, which a label reading "bulk files"
        would have misdescribed.
        """
        methods = {(p.access_method.value, p.label) for p in catalog.get("gdelt").access_profiles}
        assert methods == {
            ("PUBLIC_API", "gdelt-doc-api"),
            ("DATASET_DOWNLOAD", "gdelt-web-ngram-files"),
        }
        for profile in catalog.get("gdelt").access_profiles:
            assert profile.access_method.value not in ("BROWSER_AUTOMATION", "PUBLIC_WEB")

    def test_the_condition_is_satisfied_by_a_real_verifier(self, catalog, compliance) -> None:
        """§17. No boolean was flipped; a verifier ran and recorded what it found."""
        records = verify_source(catalog.get("gdelt"), LEGACY_PROFILE, compliance, environ={})
        (record,) = records
        assert record.condition_key == "gdelt-attribution"
        assert record.result is ConditionVerificationResult.SATISFIED
        assert record.verifier == "capability:source-attribution-display"
        assert record.reason


class TestGdeltResourceScopeFailsClosed:
    """§10, §21. The grant is over datasets GDELT RELEASES.

    It aggregates worldwide news, so a record can reference material the project
    holds no rights over -- which is why an unestablished origin is refused
    rather than assumed to be covered.
    """

    @pytest.fixture()
    def context(self, catalog, compliance):
        return build_authorization(catalog.get("gdelt"), LEGACY_PROFILE, compliance)

    @pytest.mark.parametrize(
        ("origin", "allowed"),
        [
            (ResourceContentOrigin.PLATFORM_LICENSED, True),
            (ResourceContentOrigin.THIRD_PARTY, False),
            (ResourceContentOrigin.UNKNOWN, False),
        ],
    )
    def test_content_origin_decides(self, context, origin, allowed) -> None:
        """With everything else established, origin is what decides.

        "Everything else" grew in Mission 1.9.2: a resource must now carry an
        established rights basis, and its family must be one review 3 actually
        assessed. Both are supplied here so that origin is still the variable
        under test -- `events` was a family nobody had reviewed, and left in
        place it would have made every case refuse for the wrong reason.
        """
        result = context.authorize_resource(
            ResourceDescriptor(
                source_id="gdelt",
                resource_id="web-ngrams/1gram",
                rights_basis=RightsBasis.DIRECT_GRANT,
                content_origin=origin,
                dataset_family="web-ngrams-1gram",
            )
        )
        assert result.allowed is allowed
        if not allowed:
            assert result.denial_reasons

    def test_an_unclassified_resource_is_refused_even_when_the_origin_is_right(
        self, context
    ) -> None:
        """§21's second half, and the rule GDELT's scope rests on.

        The review assessed the DOC API and the bulk files for a specific set of
        capabilities. GDELT publishes more than that. A resource that cannot say
        which family it belongs to has not been assessed, and an unassessed
        resource is refused rather than assumed to be one of the reviewed ones.
        """
        result = context.authorize_resource(
            ResourceDescriptor(
                source_id="gdelt",
                resource_id="something-nobody-reviewed",
                content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
                dataset_family=None,
            )
        )
        assert not result.allowed
        assert any("dataset family" in reason for reason in result.denial_reasons)

    def test_every_rule_reports_rather_than_short_circuiting(self, context) -> None:
        """A caller who fixes one refusal and meets the next learns to distrust
        the gate, so every rule reports.

        Asserted as a property rather than as the number 2. Mission 1.9.2 added
        a third rule to this scope, and a test that counted refusals would have
        failed for saying "two" while the behaviour it names -- report all of
        them, not the first -- was working exactly as before.
        """
        result = context.authorize_resource(
            ResourceDescriptor(
                source_id="gdelt",
                resource_id="unknown",
                rights_basis=None,
                content_origin=ResourceContentOrigin.UNKNOWN,
                dataset_family=None,
            )
        )
        assert not result.allowed
        assert len(result.denial_reasons) == len(result.rules_evaluated)
        assert {"content-origin", "dataset-family", "rights-basis"} <= set(result.rules_evaluated)

    def test_another_sources_resource_is_refused(self, context) -> None:
        result = context.authorize_resource(
            ResourceDescriptor(
                source_id="world-bank",
                resource_id="SP.POP.TOTL",
                content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
            )
        )
        assert not result.allowed


class TestTheAuthorizationContextIsComplete:
    """§20. Built with no network request, from governance alone."""

    def test_gdelt_context_carries_everything_a_collector_would_need(
        self, catalog, compliance
    ) -> None:
        context = build_authorization(catalog.get("gdelt"), LEGACY_PROFILE, compliance)
        payload = context.to_json()

        assert payload["source_id"] == "gdelt"
        assert payload["review_version"] == catalog.get("gdelt").review.review_version
        assert {a["label"] for a in payload["access"]} == {
            "gdelt-doc-api",
            "gdelt-web-ngram-files",
        }
        # Retention comes from governance, never from the collector.
        assert payload["retention"]["raw_days"] == 30
        assert payload["retention"]["normalized_days"] == 365
        assert payload["resource_scope"]["third_party_denied"] is True
        assert [r["element"] for r in payload["attribution"]["requirements"]]
        assert [(v["condition_key"], v["result"]) for v in payload["verifications"]] == [
            ("gdelt-attribution", "SATISFIED")
        ]
        # No credential is required, so none is referenced.
        assert context.runtime_credential_references == ()

    def test_a_downgraded_source_cannot_produce_a_context(self, catalog, compliance) -> None:
        """The gate, from the other side. Wikimedia has a compliance need and
        no compliance entry, and would fail on its review state regardless."""
        from sros_acquisition.compliance import AcquisitionNotAuthorizedError

        for source_id in ("wikimedia-pageviews", "pypi", "npm-registry"):
            with pytest.raises(AcquisitionNotAuthorizedError):
                build_authorization(catalog.get(source_id), LEGACY_PROFILE, compliance)


class TestWikimediaIsBlockedForTheRecordedReason:
    """§18: if it stays blocked, record exactly why.

    Not "it is blocked" -- which would pass if it were blocked for any reason at
    all, including a reason nobody intended.
    """

    def test_it_is_blocked_on_its_review_state_not_on_a_condition(self, catalog) -> None:
        source = catalog.get("wikimedia-pageviews")
        result = evaluate_eligibility(source, LEGACY_PROFILE)
        assert not result.eligible
        assert any("REQUIRES_REVIEW" in reason for reason in result.blocking_reasons)

    def test_the_licence_retrieved_this_mission_is_recorded(self, catalog) -> None:
        """Recorded rather than relied on: CC BY-SA grants reproduction and
        adaptation, and whether pageview COUNTS are Licensed Material is H-24,
        which this mission did not answer in its own favour."""
        titles = [
            item.document_title for item in catalog.get("wikimedia-pageviews").review.evidence
        ]
        assert any("Attribution-ShareAlike 4.0" in title for title in titles)

    def test_no_capability_was_built_for_a_source_that_cannot_use_one(self) -> None:
        """§7, §13: do not build unused abstractions.

        A request-identification capability is what Wikimedia's User-Agent
        condition would need. Building it now would register a capability no
        condition on any approving source names, which the compliance validator
        rejects outright.
        """
        from sros_acquisition.compliance.capabilities import CAPABILITIES

        assert not [
            name for name in CAPABILITIES if "user-agent" in name or "identification" in name
        ]


@needs_postgres
class TestEligibilityAgreesEverywhere:
    def test_python_and_sql_agree_across_every_source(self, conn, catalog) -> None:
        """§18. Both implementations, same inputs, all 27 sources.

        The expected outcome is not written down here: the point is that the two
        agree, whatever they say.
        """
        from sros_acquisition.registry.repositories import read_eligibility

        divergences = []
        for source in catalog:
            satisfied = recorded_satisfied_keys(conn, source.source_id)
            from_python = evaluate_eligibility(
                source, LEGACY_PROFILE, satisfied_conditions=satisfied
            )
            from_db = read_eligibility(conn, source.source_id, LEGACY_PROFILE)
            assert from_db is not None, source.source_id
            if from_db.eligible != from_python.eligible or set(from_db.blocking_reasons) != set(
                from_python.blocking_reasons
            ):
                divergences.append(source.source_id)
        assert divergences == []

    def test_gdelt_is_eligible_and_the_prohibited_sources_are_not(self, conn, catalog) -> None:
        eligible = {
            s.source_id
            for s in catalog
            if evaluate_eligibility(
                s, LEGACY_PROFILE, satisfied_conditions=recorded_satisfied_keys(conn, s.source_id)
            ).eligible
        }
        assert "gdelt" in eligible
        for source_id in ("spotify", "youtube", "tiktok", "steam", "meta-instagram"):
            assert source_id not in eligible, source_id

    def test_eligibility_did_not_enable_anything(self, conn) -> None:
        """§19. Eligible, enabled and implemented stay three separate facts.

        Asserted as a RELATION, not as a list. Which sources are enabled is an
        environment fact: `world-bank` is switched on wherever Mission 1.5's
        enablement was run, and NOTHING is switched on in CI, where the catalog
        load writes `collector_enabled = FALSE` and `sros-source enable` never
        runs. This assertion was first written as `== ["world-bank"]`, which
        passed on a developer machine and failed on the fresh one CI starts
        from -- testing-strategy.md §10's whole subject, walked into again.

        What must hold in every environment is that the switch never gets ahead
        of an implementation.
        """
        from sros_acquisition import IMPLEMENTED_COLLECTORS

        enabled = {
            r[0]
            for r in conn.execute(
                "SELECT id FROM registry.sources WHERE collector_enabled"
            ).fetchall()
        }
        assert enabled <= set(IMPLEMENTED_COLLECTORS), (
            "collector_enabled is set on a source with no implemented collector: "
            f"{sorted(enabled - set(IMPLEMENTED_COLLECTORS))}"
        )

    def test_the_implemented_collectors_are_the_two_that_were_authorised(self) -> None:
        """Mission 1.8 asserted that GDELT was eligible with NO collector, which
        was the whole point of that mission: eligibility is not implementation.

        Mission 1.9.2 authorised its resources and Mission 1.9.3 wrote the
        collector, in that order. The assertion moved rather than being deleted,
        because the sequence it records is the thing worth keeping.
        """
        from sros_acquisition import IMPLEMENTED_COLLECTORS

        assert set(IMPLEMENTED_COLLECTORS) == {"world-bank", "gdelt"}
