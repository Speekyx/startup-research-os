"""Source permission is use-profile-specific (Mission 1.15.5, ADR-027).

§39 and §40. **No external call.**

The property this file exists to protect is one sentence: **a verdict has a
subject, and the subject is never guessed.** Every failure mode below is a way
of losing that — a review with no subject, a gate that never asks, a permission
that leaks from one use to another, a runtime that infers its own profile from
the fact that it happens to be running on localhost.

The single most valuable assertion here is the pair in
`TestOneSourceTwoAnswers`: TED is `REQUIRES_REVIEW` under one profile and
`APPROVED_WITH_CONDITIONS` under another **at the same time**, and that is not a
contradiction. Before this mission the registry could not say it.
"""

from __future__ import annotations

import ast
import inspect
import pathlib

import pytest
from sros_acquisition.compliance import (
    USE_PROFILE_ENV_VAR,
    AcquisitionNotAuthorizedError,
    UseProfileNotDeclaredError,
    build_authorization,
    declared_use_profile,
    verify_source,
)
from sros_acquisition.registry import evaluate_eligibility
from sros_acquisition.registry.models import (
    LEGACY_USE_PROFILE,
    AssessedUseProfile,
    PolicyReview,
    SourceRegistryError,
)
from sros_contracts import SourceApprovalState

from .conftest import LEGACY_PROFILE, LOCAL_PROFILE, REPO_ROOT

UNKNOWN_PROFILE = "invented-profile-v1"


@pytest.fixture(scope="module")
def compliance():
    """The real compliance configuration, for the same reason `catalog` is real:
    it is the artefact under review."""
    from sros_acquisition.compliance.config import load_compliance

    return load_compliance(REPO_ROOT / "docs" / "data" / "source-compliance-v1.json")


ACQUISITION = REPO_ROOT / "services" / "acquisition" / "python" / "sros_acquisition"
GATE_MODULES = (
    ACQUISITION / "registry" / "eligibility.py",
    ACQUISITION / "compliance" / "authorization.py",
    ACQUISITION / "compliance" / "verification.py",
)


def source_of(catalog, source_id: str):
    return next(s for s in catalog.sources if s.source_id == source_id)


# ================================ a review cannot exist without its subject


class TestAReviewHasASubject:
    def test_every_review_in_the_catalog_names_a_registered_profile(self, catalog) -> None:
        registered = {p.use_profile_id for p in catalog.use_profiles}
        for source in catalog.sources:
            for past in source.review_history:
                assert past.assessed_use_profile in registered, (
                    source.source_id,
                    past.review_version,
                    past.assessed_use_profile,
                )

    def test_a_review_with_no_profile_is_refused_by_the_model(self) -> None:
        """Not a nicety. A verdict whose subject is unstated cannot be
        transferred, compared or refused correctly, so it may not be built."""
        from datetime import UTC, datetime

        with pytest.raises(SourceRegistryError, match="assessed_use_profile"):
            PolicyReview(
                assessed_use_profile="",
                approval_state=SourceApprovalState.APPROVED,
                assessed_use_case="anything",
                reviewed_by="test",
                reviewed_at=datetime.now(UTC),
            )

    def test_a_profile_id_must_carry_its_semantic_version(self) -> None:
        """§7. Identity is independent of wording and changes when the meaning
        does, so `local-private-research` without a version is refused: a
        profile whose semantics could change under a stable id would silently
        move every review that named it."""
        with pytest.raises(SourceRegistryError, match="use_profile_id"):
            AssessedUseProfile(
                use_profile_id="local-private-research",
                name="No version",
                description="A profile whose meaning could change without notice.",
            )

    def test_an_unregistered_profile_on_a_review_fails_at_load(self, tmp_path) -> None:
        """Refused when the catalog is read, not when the gate is asked. An
        unregistered id is a typo or an invention, and both should fail before
        anything asks it a question."""
        import json

        from sros_acquisition.registry import load_catalog

        payload = json.loads(
            (REPO_ROOT / "docs" / "data" / "source-catalog-v1.json").read_text(encoding="utf-8")
        )
        payload["sources"][0]["reviews"][0]["assessed_use_profile"] = UNKNOWN_PROFILE
        broken = tmp_path / "catalog.json"
        broken.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(SourceRegistryError, match="not a registered use profile"):
            load_catalog(broken)


# ============================== one source, two profiles, two current answers


class TestOneSourceTwoAnswers:
    def test_ted_holds_two_different_current_verdicts_at_once(self, catalog) -> None:
        """§46's success criterion, and the reason this mission exists.

        Before Mission 1.15.5 the registry stored one current answer per source,
        so this state could only be reached by making one of the two answers
        untrue."""
        ted = source_of(catalog, "ted-eu")
        assert set(ted.use_profiles) == {LEGACY_PROFILE, LOCAL_PROFILE}

        legacy = ted.review_for(LEGACY_PROFILE)
        local = ted.review_for(LOCAL_PROFILE)
        assert legacy.approval_state is SourceApprovalState.REQUIRES_REVIEW
        assert local.approval_state is SourceApprovalState.APPROVED_WITH_CONDITIONS

    def test_each_profile_keeps_its_own_append_only_version_line(self, catalog) -> None:
        ted = source_of(catalog, "ted-eu")
        legacy = sorted(
            r.review_version for r in ted.review_history if r.assessed_use_profile == LEGACY_PROFILE
        )
        local = sorted(
            r.review_version for r in ted.review_history if r.assessed_use_profile == LOCAL_PROFILE
        )
        assert legacy == [1, 2, 3, 4, 5]
        # Version 1 under a second profile is a FIRST review of a new question,
        # not a duplicate of the legacy v1. Mission 1.15.6 appended v2, which is
        # what an append-only line is FOR: it reclassified two conditions from
        # HUMAN_CONFIRMATION to CAPABILITY and changed no policy conclusion,
        # rather than editing v1 in place.
        assert local == [1, 2]
        # And the two lines still advance independently: appending to one must
        # never renumber or disturb the other.
        assert legacy[-1] == 5

    def test_exactly_one_current_review_per_source_and_profile(self, catalog) -> None:
        for source in catalog.sources:
            for profile in source.use_profiles:
                versions = [
                    r.review_version
                    for r in source.review_history
                    if r.assessed_use_profile == profile
                ]
                assert len(versions) == len(set(versions)), (source.source_id, profile)
                assert source.review_for(profile).review_version == max(versions)

    def test_the_legacy_line_was_not_touched_by_the_new_one(self, catalog) -> None:
        """§29. Attaching a profile to history is a migration interpretation of
        what those reviews assessed, never a new policy conclusion."""
        ted = source_of(catalog, "ted-eu")
        v5 = ted.review_for(LEGACY_PROFILE)
        assert v5.review_version == 5
        assert v5.reviewed_by == "mission-1.15.2" or v5.reviewed_by == "mission-1.15.4"
        assert len(v5.conditions) == 11
        assert v5.required_conditions == ()


# ==================================== approval never transfers between profiles


class TestCrossProfileIsolation:
    def test_a_local_approval_does_not_authorise_the_commercial_profile(
        self, catalog, compliance
    ) -> None:
        """§16, and the failure that would matter most in practice: deploying
        publicly and inheriting a permission granted for a laptop."""
        ted = source_of(catalog, "ted-eu")
        with pytest.raises(AcquisitionNotAuthorizedError) as caught:
            build_authorization(ted, LEGACY_PROFILE, compliance, environ={})
        reasons = " ".join(caught.value.reasons)
        assert LEGACY_PROFILE in reasons
        assert "REQUIRES_REVIEW" in reasons

    def test_an_unknown_profile_is_refused_and_never_resolved_against_another(
        self, catalog
    ) -> None:
        """§15. No fallback to another profile, and no fallback to the source's
        historical verdict."""
        result = evaluate_eligibility(source_of(catalog, "ted-eu"), UNKNOWN_PROFILE)
        assert not result.eligible
        assert result.use_profile_id == UNKNOWN_PROFILE
        assert any(UNKNOWN_PROFILE in r for r in result.blocking_reasons)
        # Not the legacy answer wearing a different label.
        assert result.approval_state is None

    def test_a_missing_profile_is_refused_rather_than_defaulted(self, catalog) -> None:
        with pytest.raises(SourceRegistryError, match="use_profile_id"):
            evaluate_eligibility(source_of(catalog, "ted-eu"), "")

    def test_compliance_configuration_does_not_leak_across_profiles(
        self, catalog, compliance
    ) -> None:
        """The configuration says what a collector may request. TED's exists for
        the local profile only, and the commercial profile must not borrow it."""
        assert compliance.get("ted-eu", LOCAL_PROFILE) is not None
        assert compliance.get("ted-eu", LEGACY_PROFILE) is None

    def test_an_approving_source_under_one_profile_is_unknown_under_another(self, catalog) -> None:
        """world-bank is approving under the legacy profile and has never been
        reviewed under the local one. Absence is a refusal."""
        world_bank = source_of(catalog, "world-bank")
        assert world_bank.review_for(LEGACY_PROFILE).is_approving
        assert world_bank.review_for(LOCAL_PROFILE) is None
        assert not evaluate_eligibility(world_bank, LOCAL_PROFILE).eligible


# ============================= the gate cannot be asked without a subject


class TestTheGateRequiresAProfile:
    def test_evaluate_eligibility_takes_the_profile_second_and_without_a_default(
        self,
    ) -> None:
        parameters = inspect.signature(evaluate_eligibility).parameters
        assert list(parameters)[1] == "use_profile_id"
        assert parameters["use_profile_id"].default is inspect.Parameter.empty

    @pytest.mark.parametrize(
        "func", [build_authorization, verify_source], ids=["authorization", "verification"]
    )
    def test_the_authorization_path_takes_the_profile_without_a_default(self, func) -> None:
        parameters = inspect.signature(func).parameters
        assert list(parameters)[1] == "use_profile_id"
        assert parameters["use_profile_id"].default is inspect.Parameter.empty

    def test_no_gate_module_reads_the_legacy_scoped_review_attribute(self) -> None:
        """The structural guard, and the one that matters most.

        `SourceRecord.review` survives as the current review UNDER THE LEGACY
        PROFILE, so every document and renderer written before profiles existed
        stays true. A gate module reading it would be the silent fallback to a
        global verdict that §15 forbids -- and it is the single easiest mistake
        to make here, because `.review` reads more naturally than
        `.review_for(profile)`.

        Asserted over the AST rather than the file's text, for the reason
        `testing-strategy.md` §38 gives: a substring scan would match the name
        in this docstring."""
        offenders = []
        for path in GATE_MODULES:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Attribute)
                    and node.attr == "review"
                    and isinstance(node.value, ast.Name)
                    and node.value.id in {"source", "record"}
                ):
                    offenders.append(f"{path.name}:{node.lineno}")
        assert offenders == [], offenders

    def test_the_authorization_context_carries_the_profile(self, catalog, compliance) -> None:
        """§13. A collector holding a context can be asked what it is authorised
        to be DOING, not only which source it may reach."""
        context = build_authorization(
            source_of(catalog, "world-bank"), LEGACY_PROFILE, compliance, environ={}
        )
        assert context.use_profile_id == LEGACY_PROFILE
        assert context.to_json()["use_profile_id"] == LEGACY_PROFILE


# ===================================== the runtime declares, never infers


class TestRuntimeDeclaration:
    def test_a_missing_declaration_refuses_rather_than_defaulting(self) -> None:
        """§12, §35. The convenient default is the narrow local profile, which
        is exactly the one an operator running a public service would most want
        assumed for them. So there is none."""
        with pytest.raises(UseProfileNotDeclaredError, match="not set"):
            declared_use_profile({})

    def test_a_malformed_declaration_refuses(self) -> None:
        with pytest.raises(UseProfileNotDeclaredError):
            declared_use_profile({USE_PROFILE_ENV_VAR: "production"})

    def test_a_declaration_is_returned_verbatim(self) -> None:
        assert declared_use_profile({USE_PROFILE_ENV_VAR: LOCAL_PROFILE}) == LOCAL_PROFILE

    def test_the_profile_is_never_inferred_from_the_environment(self) -> None:
        """§12, structurally. A profile derived from an environment name, a
        host, a container or a user count would be an infrastructural guess
        standing in for a governance decision -- and the same binary in the same
        container can legitimately be operated under either profile."""
        source = (ACQUISITION / "compliance" / "use_profile.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        read_keys = [
            ast.unparse(node.args[0])
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and node.args
        ]
        # Exactly one environment key, named by the module constant rather than
        # by a literal, and nothing resembling an environment-shaped fallback.
        assert read_keys == ["USE_PROFILE_ENV_VAR"], read_keys
        for tell in ("ENV", "ENVIRONMENT", "localhost", "DOCKER", "NODE_ENV", "DEBUG"):
            assert f'"{tell}"' not in source, tell


# ======================================= TED specifics that must not move


class TestTedUnderTheLocalProfile:
    def test_the_local_review_is_approving_with_conditions(self, catalog) -> None:
        ted = source_of(catalog, "ted-eu")
        local = ted.review_for(LOCAL_PROFILE)
        assert local.approval_state is SourceApprovalState.APPROVED_WITH_CONDITIONS
        # The CURRENT local review is v2 (Mission 1.15.6), which reclassified two
        # conditions and reached the same conclusion. Asserted alongside v1's
        # own reviewer rather than instead of it: the append-only guarantee is
        # only worth testing from both sides, and a test that followed the
        # current version alone would pass against a v1 rewritten in place.
        assert local.review_version == 2
        assert local.reviewed_by == "mission-1.15.6"
        v1 = next(
            r
            for r in ted.review_history
            if r.assessed_use_profile == LOCAL_PROFILE and r.review_version == 1
        )
        assert v1.reviewed_by == "mission-1.15.5"
        assert v1.approval_state is local.approval_state

    def test_h36_is_still_open_under_the_local_profile(self, catalog) -> None:
        """§21. Narrowing the use profile changes the EXPOSURE, not the law. A
        review that quietly dropped the open question would be claiming to have
        resolved a database right by choosing a deployment model."""
        questions = " ".join(
            source_of(catalog, "ted-eu").review_for(LOCAL_PROFILE).open_questions
        ).lower()
        assert "h-36a" in questions
        assert "h-36b" in questions
        assert "not established" in questions

    def test_commercial_use_is_permitted_under_the_local_profile(self, catalog) -> None:
        """The rule most easily taken backwards. Running locally does not make
        the use non-commercial, so the commercial-use right still had to be
        granted by the source's own evidence -- and it is, by the Decision."""
        local = source_of(catalog, "ted-eu").review_for(LOCAL_PROFILE)
        assert local.assessments["commercial_use"].value == "PERMITTED"
        for profile in catalog.use_profiles:
            assert profile.commercial_purpose is True, profile.use_profile_id

    def test_redistribution_is_the_activity_the_profile_actually_narrows(self, catalog) -> None:
        """The profile's structural contribution: no redistribution means the
        Article 7(2)(b) re-utilisation limb is not engaged."""
        assert (
            (
                source_of(catalog, "ted-eu").review_for(LOCAL_PROFILE).assessments["redistribution"]
            ).value
            == "NOT_PERMITTED"
        )

    def test_the_bulk_and_csv_routes_are_excluded_by_name(self, compliance) -> None:
        """§24. Profile support must not become a loophole for the route with
        the highest database-right exposure."""
        scope = compliance.get("ted-eu", LOCAL_PROFILE).resource_scope
        excluded = set(scope.excluded_dataset_families)
        assert {"ted-bulk-xml-daily", "ted-bulk-xml-monthly", "ted-csv-historical"} <= excluded
        assert scope.require_dataset_family is True

    def test_every_legacy_condition_survives_into_the_local_review(self, catalog) -> None:
        """§12, §18. A narrower use never relaxes an obligation."""
        ted = source_of(catalog, "ted-eu")
        for condition in ted.review_for(LEGACY_PROFILE).conditions:
            assert condition in ted.review_for(LOCAL_PROFILE).conditions

    def test_model_training_and_embeddings_are_still_blocked(self, catalog) -> None:
        """§26. Neither registered profile permits them, and the review scopes
        machine processing regardless."""
        text = " ".join(source_of(catalog, "ted-eu").review_for(LOCAL_PROFILE).conditions).lower()
        assert "model training" in text
        assert "embedding" in text and "d-12" in text
        for profile in catalog.use_profiles:
            assert profile.model_training is False
            assert profile.embeddings is False

    def test_personal_data_minimisation_is_unchanged_and_at_acquisition(
        self, catalog, compliance
    ) -> None:
        """§25. Local use justifies collecting no more personal data than
        commercial use would."""
        ted = source_of(catalog, "ted-eu")
        assert ted.review_for(LOCAL_PROFILE).contains_user_identifiers is True
        assert ted.review_for(LOCAL_PROFILE).discard_identifiers_after_normalization is True

        minimisation = compliance.get("ted-eu", LOCAL_PROFILE).data_minimisation
        for field in ("notice_id", "monetary_amount", "monetary_amount_type", "currency"):
            assert field in minimisation.allowed, field
        for field in ("contact_email", "contact_telephone", "natural_person_name"):
            assert field in minimisation.excluded, field

    def test_the_monetary_semantic_is_kept_beside_the_amount(self, compliance) -> None:
        """§22 of Mission 1.15.3, still holding: an amount without its semantic
        is the flattening into `price_paid` that nothing downstream can undo."""
        minimisation = compliance.get("ted-eu", LOCAL_PROFILE).data_minimisation
        assert "monetary_amount_type" in minimisation.allowed


# ============================ approving is still not eligible, and says why


class TestApprovingButNotEligible:
    def test_the_context_cannot_be_built_and_names_the_human_decision(
        self, catalog, compliance
    ) -> None:
        """§48. The exact remaining blocker, asserted rather than described.

        **Narrowed by Mission 1.15.6, and narrowed is the right word.** This
        asserted three outstanding HUMAN_CONFIRMATION conditions. Two of them
        described objective properties of the CONFIGURATION -- which route
        acquisition binds to, which fields it requests -- and are now verified
        against it, so exactly one remains.

        Rewritten rather than weakened (`testing-strategy.md` §26). The property
        worth protecting was never "three conditions block"; it is that **the
        refusal names every outstanding condition and nothing satisfies a
        judgement**. The tuple is asserted in full rather than by substring, so
        a condition silently dropping out of the queue fails here.
        """
        with pytest.raises(AcquisitionNotAuthorizedError) as caught:
            build_authorization(source_of(catalog, "ted-eu"), LOCAL_PROFILE, compliance, environ={})
        assert caught.value.reasons == (
            "review conditions not satisfied: ted-database-right-residual-exposure-accepted",
        )

    def test_the_two_reclassified_conditions_are_verified_not_confirmed(
        self, catalog, compliance
    ) -> None:
        """The other half of the assertion above, kept separate because it is a
        different claim: they left the queue by being CHECKED, not by being
        excused. Mission 1.15.6, ADR-028."""
        records = {
            r.condition_key: r
            for r in verify_source(source_of(catalog, "ted-eu"), LOCAL_PROFILE, compliance, {})
        }
        for key in ("ted-official-route-only", "ted-personal-data-minimisation"):
            assert records[key].verification.value == "CAPABILITY", key
            assert records[key].result.value == "SATISFIED", key
        assert (
            records["ted-database-right-residual-exposure-accepted"].verification.value
            == "HUMAN_CONFIRMATION"
        )

    def test_the_machine_checkable_condition_is_satisfied(self, catalog, compliance) -> None:
        """Attribution is verified by capability and passes, so the blocker is
        specifically the human decisions rather than an unbuilt feature."""
        records = {
            r.condition_key: r
            for r in verify_source(source_of(catalog, "ted-eu"), LOCAL_PROFILE, compliance, {})
        }
        assert records["ted-attribution"].result.value == "SATISFIED"

    def test_no_human_confirmation_condition_can_ever_be_machine_satisfied(
        self, catalog, compliance
    ) -> None:
        for record in verify_source(source_of(catalog, "ted-eu"), LOCAL_PROFILE, compliance, {}):
            if record.verification.value == "HUMAN_CONFIRMATION":
                assert record.result.value == "UNKNOWN", record.condition_key

    def test_ted_is_not_collector_eligible_under_either_profile(self, catalog) -> None:
        ted = source_of(catalog, "ted-eu")
        assert not evaluate_eligibility(ted, LEGACY_PROFILE).eligible
        assert not evaluate_eligibility(ted, LOCAL_PROFILE).eligible


# ================================================= nothing was built


class TestNothingWasBuilt:
    def test_the_collector_arrived_two_missions_later_and_no_normalizer_has(self) -> None:
        """Inverted in Mission 1.15.7. A use-profile mission built nothing, and
        the sequence it was asserting -- profile, then route, then resource, then
        code -- is what actually happened over the four missions that followed.

        The normalizer half is untouched and still true.
        """
        from sros_acquisition import IMPLEMENTED_COLLECTORS, IMPLEMENTED_NORMALIZERS

        assert "ted-eu" in IMPLEMENTED_COLLECTORS
        assert "ted-eu" not in IMPLEMENTED_NORMALIZERS
        modules = sorted(
            p.name
            for p in ACQUISITION.rglob("*.py")
            if "ted" in p.stem.lower() or "sparql" in p.stem.lower()
        )
        assert modules == ["ted_search_api.py"], modules

    def test_the_legacy_verdict_distribution_is_unchanged(self, catalog) -> None:
        """§29, §44. Attaching profile identity to history changed no verdict."""
        from collections import Counter

        counts = Counter(
            source.review_for(LEGACY_USE_PROFILE).approval_state.value
            for source in catalog.sources
            if source.review_for(LEGACY_USE_PROFILE)
        )
        assert counts == {
            "REQUIRES_REVIEW": 13,
            "RESTRICTED": 8,
            "APPROVED_WITH_CONDITIONS": 5,
            "PROHIBITED": 3,
        }


def test_no_test_in_this_file_reaches_the_network() -> None:
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
