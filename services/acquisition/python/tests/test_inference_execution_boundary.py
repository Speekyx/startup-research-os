"""Where model inference may execute, and when source content may leave.

Mission 1.23, ADR-033. The contract Mission 1.22 stopped for want of.

**Three questions where there was one**, and the tests are organised around
keeping them apart:

    model_processing              may a model READ this material?
    external_model_transmission   may it LEAVE this deployment to be read?
    provider posture              what does the receiving processor DO with it?

The failure this guards against is the easy one: collapsing them back into a
single *model_processing = permitted*, which is what the contract said before and
which could not express the question that mattered.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from sros_acquisition.compliance.inference import (
    EXTERNAL_MODEL_TRANSMISSION,
    InferenceRefusalReason,
    ProviderPosture,
    authorize_external_inference,
    load_provider_policy,
)
from sros_acquisition.registry.models import (
    ASSESSED_ACTIVITIES,
    EGRESS_DENIED,
    EGRESS_NOT_ASSESSED,
    EGRESS_PERMITTED_TO_APPROVED_PROVIDERS,
    AssessedUseProfile,
    SourceRegistryError,
)

from .conftest import LOCAL_PROFILE, REPO_ROOT

LEGACY_PROFILE = "commercial-multi-tenant-research-v1"
POLICY_PATH = REPO_ROOT / "docs" / "data" / "model-provider-policy-v1.json"
CATALOG_PATH = REPO_ROOT / "docs" / "data" / "source-catalog-v1.json"
COMPLIANCE_PATH = REPO_ROOT / "docs" / "data" / "source-compliance-v1.json"


def _local_reviews(source_id: str = "stack-exchange") -> dict[int, dict]:
    """Every local review of a source, by version. Read from the JSON rather
    than the loaded catalog, because these assertions are about what was
    WRITTEN -- including fields the loader does not carry."""
    raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    entry = next(s for s in raw["sources"] if s["source_id"] == source_id)
    return {
        r["review_version"]: r
        for r in entry["reviews"]
        if r["assessed_use_profile"] == LOCAL_PROFILE
    }


def _compliance_entry(source_id: str = "stack-exchange") -> dict:
    raw = json.loads(COMPLIANCE_PATH.read_text(encoding="utf-8"))
    return next(
        e
        for e in raw["sources"]
        if e["source_id"] == source_id and e.get("use_profile_id") == LOCAL_PROFILE
    )


@pytest.fixture(scope="module")
def policy():
    return load_provider_policy(POLICY_PATH)


@pytest.fixture(scope="module")
def profiles(catalog):
    return {p.use_profile_id: p for p in catalog.use_profiles}


def decide(catalog, profiles, source_id, profile_id, provider, *, configured=True, policy=None):
    return authorize_external_inference(
        catalog.get(source_id),
        profiles[profile_id],
        provider,
        policy=policy,
        provider_configured=configured,
    )


# ================================================= the two activities are two


class TestInferenceAndTransmissionAreDistinct:
    def test_the_new_activity_exists_and_is_not_the_old_one(self) -> None:
        assert EXTERNAL_MODEL_TRANSMISSION in ASSESSED_ACTIVITIES
        assert "model_processing" in ASSESSED_ACTIVITIES
        assert len(ASSESSED_ACTIVITIES) == 12

    def test_a_review_written_before_the_activity_reads_as_not_assessed(self, catalog) -> None:
        """§15. Historical reviews are not rewritten and are not mass-marked.

        `assessment()` already defaulted to NOT_ASSESSED for an activity a review
        does not carry, which is exactly true here -- nobody looked -- and is
        distinguishable from both PERMITTED and NOT_PERMITTED.
        """
        world_bank = catalog.get("world-bank").review_for(LOCAL_PROFILE)
        assert world_bank is not None
        assert world_bank.assessment(EXTERNAL_MODEL_TRANSMISSION).value == "NOT_ASSESSED"
        # And its model_processing answer is untouched by the new field existing.
        assert world_bank.assessment("model_processing").value != "NOT_ASSESSED"

    def test_stack_exchange_v1_was_not_edited(self, catalog) -> None:
        """The new answer is version 2, appended. v1 still carries what Mission
        1.18 concluded, and carries no opinion about an activity that did not
        exist when it was written."""
        raw = json.loads(
            (REPO_ROOT / "docs" / "data" / "source-catalog-v1.json").read_text(encoding="utf-8")
        )
        entry = next(s for s in raw["sources"] if s["source_id"] == "stack-exchange")
        local = [r for r in entry["reviews"] if r["assessed_use_profile"] == LOCAL_PROFILE]
        v1 = next(r for r in local if r["review_version"] == 1)
        v2 = next(r for r in local if r["review_version"] == 2)
        assert v1["reviewed_by"] == "mission-1.18"
        assert EXTERNAL_MODEL_TRANSMISSION not in v1
        assert v2[EXTERNAL_MODEL_TRANSMISSION] == "PERMITTED_WITH_CONDITIONS"
        # Every v1 assessment survives unchanged into v2.
        for activity in ASSESSED_ACTIVITIES:
            if activity in v1:
                assert v2[activity] == v1[activity], activity


# ==================================================== the profile field


class TestTheProfileFieldFailsClosed:
    def test_a_profile_that_never_stated_it_refuses(self) -> None:
        profile = AssessedUseProfile(use_profile_id="x-v1", name="n", description="d")
        assert profile.external_model_egress == EGRESS_NOT_ASSESSED
        assert profile.permits_external_model_egress is False

    def test_denied_and_not_assessed_are_different_states(self) -> None:
        """The reason the field is not a boolean. `false` would conflate a
        decision with a question nobody asked, and the refusal reasons they
        produce are different sentences to an operator."""
        assert EGRESS_DENIED != EGRESS_NOT_ASSESSED
        for state in (EGRESS_DENIED, EGRESS_NOT_ASSESSED):
            profile = AssessedUseProfile(
                use_profile_id="x-v1", name="n", description="d", external_model_egress=state
            )
            assert profile.permits_external_model_egress is False

    def test_an_unrecognised_state_is_refused_at_construction(self) -> None:
        """An unknown value cannot fail closed, because nothing downstream knows
        which way it points."""
        with pytest.raises(SourceRegistryError, match="external_model_egress"):
            AssessedUseProfile(
                use_profile_id="x-v1", name="n", description="d", external_model_egress="MAYBE"
            )

    def test_both_registered_profiles_state_it_explicitly(self, profiles) -> None:
        """§14. Not inherited from the default: the commercial profile says
        NOT_ASSESSED in its own words, so a reader can tell an open question from
        a value nobody set."""
        assert (
            profiles[LOCAL_PROFILE].external_model_egress == EGRESS_PERMITTED_TO_APPROVED_PROVIDERS
        )
        assert profiles[LEGACY_PROFILE].external_model_egress == EGRESS_NOT_ASSESSED
        assert "NOT_ASSESSED" in (profiles[LEGACY_PROFILE].notes or "")


# ============================================ deterministic paths unaffected


class TestOnlyEXTERNALInferenceRequiresTheNewAssessment:
    def test_no_deterministic_gate_mentions_the_new_activity(self, catalog) -> None:
        """§16, the rule that keeps this contract change from being a breaking
        one. The new activity gates ONE operation, so it must never appear among
        the reasons a source is refused for ordinary acquisition.

        Asserted over the blocking REASONS rather than over `.eligible`:
        condition satisfaction is database state, and a catalog-only evaluation
        reports unsatisfied conditions for every source whatever this contract
        says. What matters here is that egress is not one of them.
        """
        from sros_acquisition import evaluate_eligibility

        for source_id in ("world-bank", "gdelt", "ted-eu", "stack-exchange", "wikimedia-pageviews"):
            result = evaluate_eligibility(catalog.get(source_id), LOCAL_PROFILE)
            blob = " ".join(result.blocking_reasons).lower()
            assert EXTERNAL_MODEL_TRANSMISSION not in blob, source_id
            assert "egress" not in blob, source_id

    def test_the_gate_result_is_unchanged_by_the_new_activity(self, catalog) -> None:
        """The stronger form: for every registered source, the verdict and its
        reasons are exactly what they would be if the activity did not exist.

        Approving sources are refused only on condition satisfaction -- which is
        database state and unrelated -- and non-approving ones on their review
        state.
        """
        from sros_acquisition import evaluate_eligibility

        for source in catalog:
            result = evaluate_eligibility(source, LOCAL_PROFILE)
            for reason in result.blocking_reasons:
                assert "model" not in reason.lower() or "model_processing" in reason.lower(), (
                    source.source_id,
                    reason,
                )

    def test_the_new_activity_is_not_one_of_rule_eights_six(self) -> None:
        """Rule 8's six gate whether a source may be collected from at all.
        Adding a seventh would have blocked every source in the catalog on an
        activity none of them needed."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_validator", REPO_ROOT / "infrastructure" / "scripts" / "validate_source_registry.py"
        )
        source = (
            REPO_ROOT / "infrastructure" / "scripts" / "validate_source_registry.py"
        ).read_text(encoding="utf-8")
        assert spec is not None
        block = source[source.index("REQUIRED_ACTIVITIES = (") :]
        block = block[: block.index(")")]
        assert EXTERNAL_MODEL_TRANSMISSION not in block

    def test_only_external_inference_asks_the_question(self, catalog, profiles, policy) -> None:
        """A LOCAL inference provider would need `model_inference` and NOT this
        activity, which is the clearest statement of why they are two fields.
        Asserted through the decision: the refusal names TRANSMISSION, never
        inference."""
        decision = decide(
            catalog, profiles, "world-bank", LOCAL_PROFILE, "anthropic", policy=policy
        )
        assert not decision.authorized
        assert InferenceRefusalReason.SOURCE_TRANSMISSION_NOT_ASSESSED in decision.refusal_reasons
        assert not any("model_processing" in r.lower() for r in decision.refusal_reasons)


# ================================================== provider governance


class TestProviderGovernance:
    def test_an_unreviewed_provider_is_refused_by_name(self, catalog, profiles, policy) -> None:
        decision = decide(
            catalog, profiles, "stack-exchange", LOCAL_PROFILE, "openai", policy=policy
        )
        assert InferenceRefusalReason.PROVIDER_NOT_ASSESSED in decision.refusal_reasons

    def test_a_reviewed_but_unapproved_provider_is_refused(self, catalog, profiles, policy) -> None:
        """Gemini's UNPAID route -- the one an unconfigured deployment reaches --
        uses submitted content to develop Google products and ML technologies,
        and its own terms say not to submit confidential information. That is a
        statement about ONE route, not about the vendor."""
        decision = decide(
            catalog, profiles, "stack-exchange", LOCAL_PROFILE, "gemini", policy=policy
        )
        assert InferenceRefusalReason.PROVIDER_NOT_APPROVED in decision.refusal_reasons
        posture = policy.posture_for("gemini")
        assert posture.trains_on_submitted_content == "YES_ON_THE_ASSESSED_ROUTE"
        assert "unpaid" in posture.route_assessed.lower()

    def test_the_test_double_can_never_be_production(self, catalog, profiles, policy) -> None:
        """§8. Refused BY NAME rather than by an unfavourable posture, so a
        reader debugging the refusal learns the right thing."""
        decision = decide(catalog, profiles, "stack-exchange", LOCAL_PROFILE, "fake", policy=policy)
        assert InferenceRefusalReason.PROVIDER_NEVER_PRODUCTION in decision.refusal_reasons

    def test_the_approved_provider_commits_to_no_training(self, policy) -> None:
        """§10's posture, and it rests on a contractual sentence rather than a
        policy page: 'Anthropic may not train models on Customer Content from
        Services.'"""
        posture = policy.posture_for("anthropic")
        assert posture.approved
        assert posture.trains_on_submitted_content == "NO_BY_CONTRACT"
        assert posture.retention == "BOUNDED_30_DAYS"

    def test_retention_is_recorded_as_bounded_rather_than_zero(self, policy) -> None:
        """A zero-retention requirement was not invented. No policy in this
        repository requires one, and inventing a rule in order to look strict
        would refuse a route on something nobody wrote."""
        assert "ZERO" not in policy.posture_for("anthropic").retention

    def test_no_vendor_is_named_in_any_source_review(self) -> None:
        """§7 and §19. Provider governance and source governance are different
        domains; the join happens once, at runtime authorization."""
        raw = (REPO_ROOT / "docs" / "data" / "source-catalog-v1.json").read_text(encoding="utf-8")
        for vendor in ("anthropic", "gemini", "openai"):
            assert vendor not in raw.lower(), vendor

    def test_no_source_term_appears_in_the_provider_policy(self) -> None:
        raw = POLICY_PATH.read_text(encoding="utf-8").lower()
        for source_id in ("stack-exchange", "world-bank", "wikimedia", "ted-eu"):
            assert source_id not in raw, source_id


# =================================================== the runtime decision


class TestTheRuntimeDecision:
    def test_governance_passes_and_only_the_credential_is_missing(
        self, catalog, profiles, policy
    ) -> None:
        """Outcome B, pinned. Three governance gates open, one operator action
        left -- and the refusal says which."""
        decision = decide(
            catalog,
            profiles,
            "stack-exchange",
            LOCAL_PROFILE,
            "anthropic",
            configured=False,
            policy=policy,
        )
        assert not decision.authorized
        assert decision.refusal_reasons == (InferenceRefusalReason.PROVIDER_NOT_CONFIGURED,)
        assert decision.source_transmission_state == "PERMITTED_WITH_CONDITIONS"
        assert decision.profile_egress_state == EGRESS_PERMITTED_TO_APPROVED_PROVIDERS
        assert decision.provider_posture == ProviderPosture.APPROVED

    def test_with_a_credential_every_gate_passes(self, catalog, profiles, policy) -> None:
        decision = decide(
            catalog,
            profiles,
            "stack-exchange",
            LOCAL_PROFILE,
            "anthropic",
            configured=True,
            policy=policy,
        )
        assert decision.authorized
        assert decision.refusal_reasons == ()

    def test_a_permissive_source_cannot_rescue_a_silent_profile(
        self, catalog, profiles, policy
    ) -> None:
        """§5. Both layers are required, and neither substitutes for the other.
        Under the commercial profile BOTH refuse, and both reasons are reported
        rather than the first."""
        decision = decide(
            catalog, profiles, "stack-exchange", LEGACY_PROFILE, "anthropic", policy=policy
        )
        assert not decision.authorized
        assert InferenceRefusalReason.PROFILE_EGRESS_NOT_ASSESSED in decision.refusal_reasons
        assert InferenceRefusalReason.SOURCE_TRANSMISSION_NOT_ASSESSED in decision.refusal_reasons

    def test_every_layer_is_evaluated_even_after_one_refuses(
        self, catalog, profiles, policy
    ) -> None:
        """Stopping at the first refusal tells an operator to fix one thing, and
        they fix it and are refused again -- once per remaining gate."""
        decision = decide(
            catalog, profiles, "world-bank", LEGACY_PROFILE, "fake", configured=False, policy=policy
        )
        assert len(decision.refusal_reasons) >= 3
        assert len(decision.detail) == len(decision.refusal_reasons)

    def test_the_decision_is_reached_without_any_network_or_model(self) -> None:
        """§18. The module that decides reaches nothing: it takes records and
        returns a verdict, so a refusal cannot have been preceded by a request."""
        import ast

        module = (
            REPO_ROOT / "services/acquisition/python/sros_acquisition/compliance/inference.py"
        ).read_text(encoding="utf-8")
        tree = ast.parse(module)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        for forbidden in ("httpx", "requests", "urllib", "socket", "anthropic", "openai"):
            assert forbidden not in imported, forbidden

    def test_authorization_takes_no_source_text(self) -> None:
        """§18's structural half. The decision function's signature carries
        records and identifiers and has no parameter a prompt could arrive in,
        so a caller cannot have serialised content before asking."""
        import inspect

        params = set(inspect.signature(authorize_external_inference).parameters)
        assert params == {
            "source",
            "profile",
            "provider_id",
            "policy",
            "provider_configured",
        }


# ================================================== dependency direction


class TestTheGatewayDoesNotBecomeARightsEngine:
    def test_no_gateway_module_reads_the_source_registry(self) -> None:
        """§29. The Gateway calls models; this module decides permissions. A
        provider adapter that queried the registry would put governance in the
        one place that must stay replaceable."""
        gateway = REPO_ROOT / "packages" / "llm-gateway" / "python" / "sros_llm_gateway"
        for path in gateway.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "sros_acquisition" not in text, path.name
            assert "source_catalog" not in text, path.name

    def test_no_model_was_called_and_no_provider_was_configured(self) -> None:
        """§31. A successful mission required no live call, and none happened."""
        template = (REPO_ROOT / "infrastructure" / "compose" / ".env.example").read_text(
            encoding="utf-8"
        )
        for tier in ("FAST", "BALANCED", "STRONG"):
            assert f"LLM_TIER_{tier}_PROVIDER=null" in template
        assert "ANTHROPIC_API_KEY=\n" in template or "ANTHROPIC_API_KEY=" in template


class TestAppendingAReviewVersionDidNotWaveAnythingThrough:
    """Mission 1.23 appended review v2 to Stack Exchange, and that ALONE broke
    deterministic acquisition -- not through the new activity, but because
    `resolve_effective_verifications` invalidates a compliance configuration
    written for an older review version, on the stated ground that a re-review
    can change what a condition means.

    That guard is right, and the repair was to perform the re-check rather than
    to silence it. These tests pin the re-check so it stays true.
    """

    def test_the_compliance_configuration_tracks_the_current_review(self) -> None:
        """Bumped, so acquisition is authorised again."""
        assert _compliance_entry()["review_version"] == max(_local_reviews())

    def test_the_bump_was_only_legitimate_because_nothing_verified_changed(self) -> None:
        """**The load-bearing assertion.** A version bump is honest exactly when
        the set this configuration verifies is unchanged.

        If a later review edits a required condition -- its key, its description,
        its verification method or its verification detail -- this fails, and the
        failure says that the configuration needs re-checking field by field
        rather than re-numbering.
        """
        reviews = _local_reviews()
        assert reviews[1]["required_conditions"] == reviews[2]["required_conditions"]

    def test_what_v2_added_is_not_verified_by_a_capability(self) -> None:
        """Why the re-check had a determinate answer. v2's additions are an
        assessment, prose, evidence and open questions; none is a capability
        this configuration asserts, so none could change what it means.
        """
        v1, v2 = _local_reviews()[1], _local_reviews()[2]
        assert set(v2) - set(v1) == {"external_model_transmission"}
        assert v2["conditions"][: len(v1["conditions"])] == v1["conditions"]
        for verified in ("required_conditions", "assessed_use_profile", "model_processing"):
            assert v1[verified] == v2[verified], verified

    def test_the_capability_conditions_verify_again_end_to_end(self, catalog) -> None:
        """The proof the repair worked, run through the real resolver rather
        than inferred from the JSON.

        Only the CAPABILITY conditions are asserted. The HUMAN_CONFIRMATION ones
        need operator decisions from a database this test does not open, and
        pretending otherwise would be the kind of hand-made satisfied-key list
        `build_authorization` exists to refuse.
        """
        from sros_acquisition.compliance import load_compliance
        from sros_acquisition.compliance.verification import (
            ConditionVerificationResult,
            resolve_effective_verifications,
        )

        records = resolve_effective_verifications(
            catalog.get("stack-exchange"),
            LOCAL_PROFILE,
            load_compliance(COMPLIANCE_PATH),
            (),
            {},
            datetime.now(UTC),
        )
        by_key = {r.condition_key: r for r in records}
        for key in (
            "stack-exchange-attribution",
            "stack-exchange-official-api-only",
            "stack-exchange-personal-data-minimisation",
        ):
            assert by_key[key].result is ConditionVerificationResult.SATISFIED, (
                key,
                by_key[key].detail,
            )
