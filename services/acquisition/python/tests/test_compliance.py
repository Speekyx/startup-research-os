"""Compliance capabilities, verification and the acquisition boundary.

Mission 1.4 §34-§38. Mission 1.3's suite proved the gate blocks; this one covers
the part that had never existed before: a condition can now be **cleared**, and
clearing one is the step that makes a source collectable.

Two tests are worth reading first.

`TestGates.test_authorization_cannot_be_built_for_an_ineligible_source` is the
§27 property in one assertion: an ineligible source produces no authorization,
so a collector that needs one cannot start.

`TestConditions.test_satisfying_a_condition_on_a_prohibited_source_changes_nothing`
is the one a future change is most likely to break. Verification must not become
a way around an approval state, and satisfying every condition on YouTube must
leave YouTube exactly as prohibited as it was.

**Nothing here contacts a platform, and no test supplies a credential value.**
The FRED secret test uses a sentinel and asserts it appears in no output.
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, date, datetime, timedelta

import pytest
from sros_acquisition.compliance import (
    CAPABILITIES,
    AcquisitionNotAuthorizedError,
    AttributedArtifact,
    AttributionFacts,
    AttributionIncompleteError,
    ResourceDescriptor,
    build_authorization,
    capability_failures,
    credential_status,
    design_eligible,
    load_compliance,
    render_attribution,
    satisfied_condition_keys,
    verify_condition,
    verify_source,
)
from sros_acquisition.registry import (
    APPROVING_STATES,
    ReviewCondition,
    SourceRegistryError,
    evaluate_eligibility,
)
from sros_contracts import (
    AttributionElement,
    ConditionVerification,
    ConditionVerificationResult,
    ResourceContentOrigin,
    RightsBasis,
    SourceApprovalState,
)

from .conftest import REPO_ROOT, needs_postgres

APPROVED_IN_1_3 = {"world-bank", "eurostat", "fred"}

# What is expected to become eligible once the capabilities exist, and what
# stays blocked. Written down rather than derived, so an accidental change in
# either direction is a failure rather than a new baseline.
#
# `gdelt` was added in Mission 1.8 and is the acknowledgement this tripwire
# exists to force: the first non-economic source to reach the gate, admitted by
# giving its one reviewed obligation -- cite the project and link to it -- a
# verifier, rather than by relaxing anything. It is eligible with NO credential,
# which is why it belongs in the first set and not the second.
EXPECTED_ELIGIBLE = {"world-bank", "eurostat", "gdelt"}
EXPECTED_BLOCKED_ON_CREDENTIAL = {"fred"}

# Never a real credential, and asserted to appear in no output anywhere.
SENTINEL = "sentinel-value-that-must-never-be-echoed"


@pytest.fixture(scope="session")
def compliance():
    """The real compliance configuration, for the same reason the catalog
    fixture is the real catalog: testing a hand-made copy would leave the
    governed one unchecked."""
    return load_compliance(REPO_ROOT / "docs/data/source-compliance-v1.json")


def _verified(source, compliance, environ=None):
    return verify_source(source, compliance, environ=environ if environ is not None else {})


# ================================================================== conditions


class TestConditions:
    def test_every_approving_source_has_condition_rows(self, catalog) -> None:
        """§34. An approving review with no condition would be an APPROVED in
        all but name, and nothing would stand between it and a collector."""
        for source in catalog:
            if source.review.approval_state in APPROVING_STATES:
                assert source.review.required_conditions, source.source_id

    def test_every_condition_produces_a_verification(self, catalog, compliance) -> None:
        for source in catalog:
            records = _verified(source, compliance)
            assert len(records) == len(source.review.required_conditions), source.source_id

    def test_every_condition_is_attributable_and_distinct(self, catalog) -> None:
        """A condition nobody assessed, or two that cannot be told apart.

        This asserted `total == 9` until Mission 1.7 added nine more. A count is
        the wrong shape for the property: it breaks whenever the catalog grows,
        and it teaches whoever hits it to edit the number rather than to ask
        whether the new condition was reviewed. What must hold is that every
        condition belongs to an approving review, names a verification, and has
        a key unique within its source -- a duplicate key would make the later
        condition silently shadow the earlier when satisfaction is recorded.
        """
        for source in catalog:
            if not source.review:
                continue
            conditions = source.review.required_conditions
            if conditions:
                assert source.review.approval_state in APPROVING_STATES, source.source_id
            keys = [c.key for c in conditions]
            assert len(set(keys)) == len(keys), source.source_id
            for condition in conditions:
                assert condition.key.strip(), source.source_id
                assert condition.description.strip(), condition.key
                assert condition.verification is not None, condition.key

    def test_an_unsatisfied_condition_blocks(self, catalog, compliance) -> None:
        """§34. FRED has every policy capability and no credential, so it is the
        source that proves one unsatisfied condition is enough."""
        fred = catalog.get("fred")
        records = _verified(fred, compliance)
        result = evaluate_eligibility(fred, satisfied_conditions=satisfied_condition_keys(records))
        assert not result.eligible
        assert result.blocking_reasons == ("review conditions not satisfied: fred-api-key",)

    def test_an_unknown_condition_blocks_and_is_never_promoted(self, catalog, compliance) -> None:
        """§19. UNKNOWN is not UNSATISFIED and it is certainly not SATISFIED.
        A RETENTION_LIMIT condition has no verifier, and having none must not
        read as having nothing to check."""
        source = catalog.get("world-bank")
        condition = ReviewCondition(
            key="probe-retention",
            description="A retention limit nothing verifies.",
            verification=ConditionVerification.RETENTION_LIMIT,
            verification_detail="30",
        )
        record = verify_condition(source, condition, compliance.get("world-bank"), {})
        assert record.result is ConditionVerificationResult.UNKNOWN
        assert not record.satisfied
        assert "no verifier is registered" in record.reason
        assert satisfied_condition_keys([record]) == frozenset()

    def test_a_human_condition_can_never_be_machine_satisfied(self, catalog, compliance) -> None:
        """§21. Not merely unsatisfied: no argument reaches any other answer."""
        condition = ReviewCondition(
            key="probe-human",
            description="Something only a person can decide.",
            verification=ConditionVerification.HUMAN_CONFIRMATION,
        )
        for source in catalog:
            record = verify_condition(source, condition, compliance.get(source.source_id), {})
            assert record.result is ConditionVerificationResult.UNKNOWN, source.source_id

    def test_satisfying_one_condition_does_not_ignore_the_others(self, catalog, compliance) -> None:
        """§34. All conditions must pass, not a majority and not the first."""
        fred = catalog.get("fred")
        keys = [c.key for c in fred.review.required_conditions]
        for held_back in keys:
            partial = frozenset(k for k in keys if k != held_back)
            result = evaluate_eligibility(fred, satisfied_conditions=partial)
            assert not result.eligible
            assert held_back in result.blocking_reasons[0]

    def test_a_stale_review_blocks_even_with_every_condition_satisfied(
        self, catalog, compliance
    ) -> None:
        """§34. Conditions are one gate among several, and clearing them does
        not clear the others. An approval nobody has re-checked is a statement
        about the past."""
        for source_id in EXPECTED_ELIGIBLE:
            source = catalog.get(source_id)
            keys = frozenset(c.key for c in source.review.required_conditions)
            future = datetime.now(UTC) + timedelta(days=3650)
            result = evaluate_eligibility(source, now=future, satisfied_conditions=keys)
            assert not result.eligible, source_id
            assert any("stale" in r for r in result.blocking_reasons)

    def test_satisfying_a_condition_on_a_prohibited_source_changes_nothing(self, catalog) -> None:
        """§34, and the property most likely to be broken by accident.

        Verification must not become a route around an approval state. Every
        non-approving source is handed a fully satisfied condition set, and must
        stay blocked by its state."""
        for source in catalog:
            if source.review.approval_state in APPROVING_STATES:
                continue
            everything = frozenset(c.key for c in source.review.required_conditions) | {
                "attribution-surface",
                "fred-api-key",
            }
            result = evaluate_eligibility(source, satisfied_conditions=everything)
            assert not result.eligible, source.source_id
            assert any(r.startswith("policy review is") for r in result.blocking_reasons)

    def test_a_stale_compliance_config_yields_unknown(self, catalog, compliance) -> None:
        """A re-review can change what a condition means, so configuration
        written against an older review version must not silently keep clearing
        it."""
        source = catalog.get("world-bank")
        stale = replace(compliance.get("world-bank"), review_version=99)
        for condition in source.review.required_conditions:
            record = verify_condition(source, condition, stale, {})
            if condition.verification is ConditionVerification.CONFIG_REFERENCE:
                continue
            assert record.result is ConditionVerificationResult.UNKNOWN
            assert "review version" in record.reason

    def test_a_condition_naming_an_unbuilt_capability_is_unknown(self, catalog, compliance) -> None:
        source = catalog.get("world-bank")
        condition = ReviewCondition(
            key="probe-missing",
            description="Names a capability nobody built.",
            verification=ConditionVerification.CAPABILITY,
            verification_detail="capability-that-does-not-exist",
        )
        record = verify_condition(source, condition, compliance.get("world-bank"), {})
        assert record.result is ConditionVerificationResult.UNKNOWN
        assert "no capability named" in record.reason

    def test_every_verification_carries_its_provenance(self, catalog, compliance) -> None:
        """§18. Which condition, which verifier, at which version, when, what,
        and why. A satisfaction with none of that is a boolean with extra steps."""
        for source in catalog:
            for record in _verified(source, compliance):
                assert record.verifier.strip()
                assert record.verifier_version.strip()
                assert record.reason.strip()
                assert record.verified_at.tzinfo is not None
                assert record.condition_key
                assert record.review_version == source.review.review_version


# ================================================================= attribution


class TestAttribution:
    def test_every_approving_source_declares_an_attribution_obligation(
        self, catalog, compliance
    ) -> None:
        """§12 of the Mission 1.3 report: all three require attribution, and
        each requires something different."""
        for source_id in APPROVED_IN_1_3:
            entry = compliance.get(source_id)
            assert entry is not None, source_id
            assert entry.attribution.requirements, source_id

    def test_a_required_element_cannot_be_omitted(self, compliance) -> None:
        """§35. Rendering refuses rather than dropping it. A notice missing half
        its obligation looks like attribution and is not."""
        eurostat = compliance.get("eurostat").attribution
        with pytest.raises(AttributionIncompleteError) as caught:
            render_attribution(eurostat, AttributionFacts(dataset_doi="10.2908/probe"))
        assert "ACCESS_DATE" in str(caught.value)

    def test_the_fred_notice_is_reproduced_byte_for_byte(self, compliance) -> None:
        """§35, and the one requirement in the whole registry with prescribed
        wording. A paraphrase is a different sentence and does not satisfy the
        terms, so this is a literal comparison rather than a fuzzy one."""
        expected = (
            "This product uses the FRED® API but is not endorsed or certified by "
            "the Federal Reserve Bank of St. Louis."
        )
        notice = render_attribution(compliance.get("fred").attribution)
        assert notice.text == expected
        assert "®" in notice.text

    def test_the_exact_notice_cannot_be_supplied_by_a_caller(self, compliance) -> None:
        """Its whole point is that our wording does not enter it."""
        from sros_acquisition.compliance.config import AttributionRequirement

        with pytest.raises(SourceRegistryError, match="prescribed by the source"):
            AttributionRequirement(
                element=AttributionElement.EXACT_NOTICE, supplied=True, text=None
            )

    def test_a_modification_statement_is_required_only_once_modified(self, compliance) -> None:
        """§35. Requiring a statement of a change that did not happen would
        train callers to write "none" into it."""
        world_bank = compliance.get("world-bank").attribution
        unmodified = AttributionFacts(licence_identifier="CC-BY-4.0")
        rendered = render_attribution(world_bank, unmodified)
        assert AttributionElement.MODIFICATION_STATEMENT not in dict(rendered.elements)

        with pytest.raises(AttributionIncompleteError):
            render_attribution(world_bank, replace(unmodified, modified=True))

        complete = replace(unmodified, modified=True, modification_statement="Rebased to 2015 USD.")
        assert "Rebased" in render_attribution(world_bank, complete).text

    def test_the_doi_and_access_date_cannot_be_defaulted(self, compliance) -> None:
        """§35. Both are per-retrieval facts; a default would be a fabrication
        that renders as attribution."""
        eurostat = compliance.get("eurostat").attribution
        for facts in (
            AttributionFacts(access_date=date(2026, 8, 29)),
            AttributionFacts(dataset_doi="10.2908/probe"),
        ):
            with pytest.raises(AttributionIncompleteError):
                render_attribution(eurostat, facts)

    def test_attribution_survives_every_transformation(self, compliance) -> None:
        """§9. Raw -> normalized -> evidence -> claim -> result is a chain in
        which any step could be where the credit was lost. `derive` has no
        parameter that removes an obligation."""
        entry = compliance.get("eurostat")
        facts = AttributionFacts(dataset_doi="10.2908/probe", access_date=date(2026, 8, 29))
        artifact = AttributedArtifact.of("RawRecord", entry.attribution, facts)
        for stage in ("NormalizedRecord", "Evidence", "Claim", "ResearchResult"):
            artifact = artifact.derive(stage)
        assert artifact.kind == "ResearchResult"
        assert artifact.source_ids == ("eurostat",)
        assert artifact.notices()[0].text.startswith("Eurostat")

    def test_merging_two_sources_owes_both(self, compliance) -> None:
        wb = AttributedArtifact.of(
            "RawRecord",
            compliance.get("world-bank").attribution,
            AttributionFacts(licence_identifier="CC-BY-4.0"),
        )
        es = AttributedArtifact.of(
            "RawRecord",
            compliance.get("eurostat").attribution,
            AttributionFacts(dataset_doi="10.2908/probe", access_date=date(2026, 8, 29)),
        )
        merged = wb.derive("Evidence", es)
        assert merged.source_ids == ("eurostat", "world-bank")
        assert len(merged.notices()) == 2

    def test_a_derived_artifact_with_incomplete_facts_refuses_to_render(self, compliance) -> None:
        """The refusal has to survive the chain too, or attribution would be
        enforced at the raw record and lost by the fourth transformation."""
        artifact = AttributedArtifact.of(
            "RawRecord", compliance.get("eurostat").attribution, AttributionFacts()
        )
        with pytest.raises(AttributionIncompleteError):
            artifact.derive("Evidence").notices()


# =============================================================== dataset scope


class TestResourceScope:
    def test_an_explicitly_allowed_resource_passes(self, compliance) -> None:
        """§36. The control case. A gate that only ever denies is a refusal, not
        a filter, and would pass every denial test."""
        scope = compliance.get("world-bank").resource_scope
        from sros_acquisition.compliance import authorize_resource

        allowed = ResourceDescriptor(
            source_id="world-bank",
            resource_id="NY.GDP.MKTP.CD",
            licence="CC-BY-4.0",
            # Added in Mission 1.9.1. A scope that enumerates licences can only
            # be satisfied by a NAMED_LICENCE resource, and this descriptor
            # always meant that -- it just had no way to say so.
            rights_basis=RightsBasis.NAMED_LICENCE,
            content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
            dataset_family="indicators",
        )
        assert authorize_resource(scope, allowed).allowed

    def test_an_excluded_resource_fails(self, catalog, compliance) -> None:
        """§36. The Microdata Library permits statistical and scientific
        research only and forbids redistribution without written agreement."""
        context = _context(catalog, compliance, "world-bank")
        micro = ResourceDescriptor(
            source_id="world-bank",
            resource_id="LSMS-2019",
            licence="CC-BY-4.0",
            rights_basis=RightsBasis.NAMED_LICENCE,
            content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
            dataset_family="microdata",
        )
        result = context.authorize_resource(micro)
        assert not result.allowed
        assert "microdata" in result.denial_reasons[0]

    def test_an_unknown_licence_fails_closed(self, catalog, compliance) -> None:
        """§36. Licensing is per dataset, not per platform, so an unrecorded
        licence is an unanswered question rather than a default."""
        context = _context(catalog, compliance, "world-bank")
        result = context.authorize_resource(
            ResourceDescriptor(
                source_id="world-bank",
                resource_id="unknown",
                # The basis is stated so this exercises the LICENCE rule.
                # Without it the descriptor now fails on the rights basis first
                # (Mission 1.9.1 §15) and the test would pass while proving
                # something else.
                rights_basis=RightsBasis.NAMED_LICENCE,
                content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
                dataset_family="indicators",
            )
        )
        assert not result.allowed
        assert any("no recorded licence" in r for r in result.denial_reasons)

    def test_a_third_party_resource_fails_unless_separately_authorised(
        self, catalog, compliance
    ) -> None:
        """§36. Platform approval grants nothing over material the platform does
        not own, and nothing in this system can grant it."""
        for source_id in APPROVED_IN_1_3:
            context = _context(catalog, compliance, source_id, environ={"FRED_API_KEY": SENTINEL})
            result = context.authorize_resource(
                ResourceDescriptor(
                    source_id=source_id,
                    resource_id="third-party",
                    licence="CC-BY-4.0",
                    content_origin=ResourceContentOrigin.THIRD_PARTY,
                    dataset_family="indicators",
                    geographies=("DE",),
                    notes="clean notes",
                )
            )
            assert not result.allowed, source_id
            assert any("third-party" in r for r in result.denial_reasons)

    def test_unknown_content_origin_fails_closed(self, catalog, compliance) -> None:
        """§12. UNKNOWN is the common case and must not be guessed either way."""
        context = _context(catalog, compliance, "world-bank")
        result = context.authorize_resource(
            ResourceDescriptor(
                source_id="world-bank",
                resource_id="unclassified",
                licence="CC-BY-4.0",
                rights_basis=RightsBasis.NAMED_LICENCE,
                dataset_family="indicators",
            )
        )
        assert not result.allowed
        assert any("UNKNOWN" in r for r in result.denial_reasons)

    def test_source_approval_cannot_override_a_dataset_exclusion(self, catalog, compliance) -> None:
        """§36. world-bank passes the gate; the Microdata Library still does
        not, and holding a valid authorization changes nothing about that."""
        context = _context(catalog, compliance, "world-bank")
        assert context.approval_state is SourceApprovalState.APPROVED_WITH_CONDITIONS
        assert not context.authorize_resource(
            ResourceDescriptor(
                source_id="world-bank",
                resource_id="LSMS",
                licence="CC-BY-4.0",
                rights_basis=RightsBasis.NAMED_LICENCE,
                content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
                dataset_family="microdata",
            )
        ).allowed

    def test_non_eu_geography_is_excluded_from_commercial_reuse(self, catalog, compliance) -> None:
        """The Eurostat copyright notice names the USA, Japan and China as data
        that must be removed before commercial reuse. Ours is commercial."""
        context = _context(catalog, compliance, "eurostat")
        for country in ("US", "JP", "CN"):
            result = context.authorize_resource(
                ResourceDescriptor(
                    source_id="eurostat",
                    resource_id="dataset",
                    content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
                    geographies=(country,),
                )
            )
            assert not result.allowed, country
        assert context.authorize_resource(
            ResourceDescriptor(
                source_id="eurostat",
                resource_id="dataset",
                content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
                geographies=("DE", "FR"),
            )
        ).allowed

    def test_the_named_trade_exclusions_are_enforced(self, catalog, compliance) -> None:
        context = _context(catalog, compliance, "eurostat")
        excluded = ResourceDescriptor(
            source_id="eurostat",
            resource_id="trade",
            content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
            geographies=("CH",),
            declaring_country="CH",
            classifications=("HS",),
            period_start_year=2001,
        )
        assert not context.authorize_resource(excluded).allowed
        # Before 1995 the named exception does not apply, and the rule says so
        # positively rather than denying everything that mentions Switzerland.
        assert context.authorize_resource(replace(excluded, period_start_year=1990)).allowed

    def test_an_exclusion_dimension_left_unrecorded_fails_closed(self, catalog, compliance) -> None:
        """A resource carrying an excluded classification that does not say who
        declared it is not a resource known to be declared by someone else."""
        context = _context(catalog, compliance, "eurostat")
        result = context.authorize_resource(
            ResourceDescriptor(
                source_id="eurostat",
                resource_id="trade",
                content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
                geographies=("DE",),
                classifications=("HS",),
                period_start_year=2001,
            )
        )
        assert not result.allowed
        assert any("unrecorded" in r for r in result.denial_reasons)

    def test_a_copyrighted_series_is_excluded_and_an_unread_one_too(
        self, catalog, compliance
    ) -> None:
        """The terms say copyrighted series are identifiable BY their notes, so
        an absent note is an unanswered question rather than a clean answer."""
        context = _context(catalog, compliance, "fred", environ={"FRED_API_KEY": SENTINEL})
        marked = ResourceDescriptor(
            source_id="fred",
            resource_id="SERIESX",
            content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
            notes="Copyright, 2026, Some Data Provider LLC.",
        )
        assert not context.authorize_resource(marked).allowed
        assert not context.authorize_resource(replace(marked, notes=None)).allowed
        assert context.authorize_resource(
            replace(marked, notes="Units: Billions of Dollars. Source: BEA.")
        ).allowed

    def test_a_resource_checked_against_the_wrong_scope_is_refused(
        self, catalog, compliance
    ) -> None:
        context = _context(catalog, compliance, "world-bank")
        result = context.authorize_resource(
            ResourceDescriptor(source_id="eurostat", resource_id="x")
        )
        assert not result.allowed


# ===================================================================== secrets


class TestSecrets:
    def test_a_secret_reference_is_a_key_name(self, catalog) -> None:
        """§37. The registry stores the name; the value belongs in the
        environment."""
        fred = catalog.get("fred")
        assert fred.access_profiles[0].secret_references == ("FRED_API_KEY",)

    def test_a_credential_value_is_refused_as_a_reference(self) -> None:
        with pytest.raises(SourceRegistryError, match="looks like a credential value"):
            credential_status("ghp_0123456789abcdefghij")

    def test_a_missing_credential_blocks_runtime_eligibility(self, catalog, compliance) -> None:
        """§37, and the §24 distinction. FRED is design-complete and not
        runnable, and those are different statements."""
        fred = catalog.get("fred")
        records = _verified(fred, compliance, environ={})
        assert design_eligible(list(records))
        assert not evaluate_eligibility(
            fred, satisfied_conditions=satisfied_condition_keys(records)
        ).eligible

    def test_a_present_credential_clears_the_last_condition(self, catalog, compliance) -> None:
        """The unblocked branch has to be reachable, or the credential check
        would be a permanent refusal dressed as a check."""
        fred = catalog.get("fred")
        records = _verified(fred, compliance, environ={"FRED_API_KEY": SENTINEL})
        assert evaluate_eligibility(
            fred, satisfied_conditions=satisfied_condition_keys(records)
        ).eligible

    def test_an_empty_variable_counts_as_not_configured(self, catalog, compliance) -> None:
        """An empty variable is what a half-finished deployment leaves behind.
        Treating it as present would move the failure from a gate that explains
        itself to a 401 from a third party."""
        for value in ("", "   "):
            assert not credential_status("FRED_API_KEY", {"FRED_API_KEY": value}).configured

    def test_no_secret_value_appears_in_any_output(self, catalog, compliance) -> None:
        """§37. Verification records, eligibility output and the whole
        authorization context are searched for the sentinel."""
        fred = catalog.get("fred")
        environ = {"FRED_API_KEY": SENTINEL}
        records = _verified(fred, compliance, environ=environ)
        context = build_authorization(fred, compliance, records, environ=environ)
        blob = json.dumps(
            {
                "verifications": [r.to_json() for r in records],
                "eligibility": evaluate_eligibility(
                    fred, satisfied_conditions=satisfied_condition_keys(records)
                ).to_json(),
                "authorization": context.to_json(),
                "status": credential_status("FRED_API_KEY", environ).to_json(),
            }
        )
        assert SENTINEL not in blob
        assert "FRED_API_KEY" in blob

    def test_no_secret_value_appears_in_an_exception(self, catalog, compliance) -> None:
        fred = catalog.get("fred")
        try:
            build_authorization(fred, compliance, environ={"FRED_API_KEY": SENTINEL, "X": "y"})
        except AcquisitionNotAuthorizedError as exc:  # pragma: no cover - not expected
            assert SENTINEL not in str(exc)
        with pytest.raises(SourceRegistryError) as caught:
            credential_status("sk-" + "a" * 24)
        assert SENTINEL not in str(caught.value)

    def test_the_env_example_documents_the_name_and_no_value(self) -> None:
        """§17. `.env.example` is committed, so a value in it is a published
        secret."""
        text = (REPO_ROOT / "infrastructure/compose/.env.example").read_text(encoding="utf-8")
        assert "FRED_API_KEY=" in text
        assert "FRED_API_KEY=\n" in text or text.rstrip().endswith("FRED_API_KEY=")

    def test_the_local_env_file_is_read_and_never_overrides_an_explicit_value(
        self, tmp_path, monkeypatch
    ) -> None:
        """The CLI reads the documented local `.env`, and an exported variable
        wins over it.

        Both halves matter. Without the first, a developer who followed
        `.env.example` gets NOT_CONFIGURED and no indication why -- which reads
        as a policy refusal and is a plumbing gap. Without the second, a stale
        file could override what an operator just set, and a verification would
        record a satisfaction about an environment nobody is running in."""
        from sros_acquisition.cli import _load_local_env

        env_file = tmp_path / "infrastructure" / "compose" / ".env"
        env_file.parent.mkdir(parents=True)
        env_file.write_text(
            "# a comment\n"
            "\n"
            "PROBE_FROM_FILE=file-value\n"
            "PROBE_ALREADY_SET=file-value\n"
            "PROBE_EMPTY=\n"
            'PROBE_QUOTED="quoted-value"\n'
            "export PROBE_EXPORTED=exported-value\n",
            encoding="utf-8",
        )
        monkeypatch.delenv("PROBE_FROM_FILE", raising=False)
        monkeypatch.delenv("PROBE_EMPTY", raising=False)
        monkeypatch.setenv("PROBE_ALREADY_SET", "environment-value")

        loaded = _load_local_env(tmp_path)

        assert loaded == env_file
        import os

        assert os.environ["PROBE_FROM_FILE"] == "file-value"
        assert os.environ["PROBE_QUOTED"] == "quoted-value"
        assert os.environ["PROBE_EXPORTED"] == "exported-value"
        # Explicit wins, and an empty assignment is not a value.
        assert os.environ["PROBE_ALREADY_SET"] == "environment-value"
        assert "PROBE_EMPTY" not in os.environ
        for name in ("PROBE_FROM_FILE", "PROBE_QUOTED", "PROBE_EXPORTED"):
            monkeypatch.delenv(name, raising=False)

    def test_no_local_env_file_is_not_an_error(self, tmp_path) -> None:
        """CI has only `.env.example`, and a contributor may have neither."""
        from sros_acquisition.cli import _load_local_env

        assert _load_local_env(tmp_path) is None

    def test_the_cli_names_the_file_it_read_and_never_its_contents(
        self, tmp_path, monkeypatch, capsys
    ) -> None:
        """§37 applied to the new read path. The provenance of a CONFIGURED
        answer must be visible; the value must not be."""
        from sros_acquisition.cli import main

        env_file = tmp_path / "infrastructure" / "compose" / ".env"
        env_file.parent.mkdir(parents=True)
        env_file.write_text(f"FRED_API_KEY={SENTINEL}\n", encoding="utf-8")
        monkeypatch.delenv("FRED_API_KEY", raising=False)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            "sros_acquisition.cli.find_catalog",
            lambda *a, **k: REPO_ROOT / "docs/data/source-catalog-v1.json",
        )
        monkeypatch.setattr(
            "sros_acquisition.cli.find_compliance_config",
            lambda *a, **k: REPO_ROOT / "docs/data/source-compliance-v1.json",
        )

        main(["conditions", "fred"])

        captured = capsys.readouterr()
        assert "read local configuration from" in captured.err
        assert SENTINEL not in captured.out
        assert SENTINEL not in captured.err
        # The key NAME is what a reader needs; the value is what they must not get.
        assert "FRED_API_KEY" in captured.out
        assert "CONFIGURED" in captured.out
        monkeypatch.delenv("FRED_API_KEY", raising=False)

    def test_the_credential_status_object_has_nowhere_to_put_a_value(self) -> None:
        """Structural, not conventional: code that wanted to leak the secret
        would have to go and read the environment itself."""
        status = credential_status("FRED_API_KEY", {"FRED_API_KEY": SENTINEL})
        assert set(status.to_json()) == {"reference", "status"}
        assert SENTINEL not in repr(status)


# ======================================================================= gates


class TestGates:
    def test_the_expected_sources_become_eligible_and_no_others(self, catalog, compliance) -> None:
        """§23. If one or more become eligible, record exactly which. Written
        down rather than derived, so a change in either direction fails."""
        eligible = set()
        for source in catalog:
            records = _verified(source, compliance)
            if evaluate_eligibility(
                source, satisfied_conditions=satisfied_condition_keys(records)
            ).eligible:
                eligible.add(source.source_id)
        assert eligible == EXPECTED_ELIGIBLE

    def test_the_remaining_approving_source_is_blocked_only_on_its_credential(
        self, catalog, compliance
    ) -> None:
        for source_id in EXPECTED_BLOCKED_ON_CREDENTIAL:
            source = catalog.get(source_id)
            records = _verified(source, compliance)
            result = evaluate_eligibility(
                source, satisfied_conditions=satisfied_condition_keys(records)
            )
            assert len(result.blocking_reasons) == 1
            assert design_eligible(list(records))

    def test_authorization_cannot_be_built_for_an_ineligible_source(
        self, catalog, compliance
    ) -> None:
        """§27, and the whole enforcement mechanism: not a flag a collector is
        asked to check, but the absence of the object it needs."""
        refused = 0
        for source in catalog:
            records = _verified(source, compliance)
            eligible = evaluate_eligibility(
                source, satisfied_conditions=satisfied_condition_keys(records)
            ).eligible
            try:
                build_authorization(source, compliance, records, environ={})
            except AcquisitionNotAuthorizedError as exc:
                refused += 1
                assert not eligible, source.source_id
                assert exc.reasons
            else:
                assert eligible, source.source_id
        assert refused == len(list(catalog)) - len(EXPECTED_ELIGIBLE)

    def test_authorization_recomputes_verification_when_none_is_supplied(
        self, catalog, compliance
    ) -> None:
        """The verifications parameter is a cache for callers that just ran
        them, never a way in: omitting it must not weaken anything."""
        with pytest.raises(AcquisitionNotAuthorizedError):
            build_authorization(catalog.get("fred"), compliance, environ={})

    def test_removing_the_compliance_config_removes_the_authorizations(
        self, catalog, compliance
    ) -> None:
        """Deleting the configuration must not be a way to stop failing checks.

        Every capability condition becomes UNKNOWN with nothing to check
        against, so the gate blocks first -- which is the right order: the
        source stops being eligible rather than becoming unconstrained."""
        from sros_acquisition.compliance.config import ComplianceConfig

        empty = ComplianceConfig(compliance_version="test", sources=())
        for source_id in EXPECTED_ELIGIBLE:
            with pytest.raises(AcquisitionNotAuthorizedError, match="conditions not satisfied"):
                build_authorization(catalog.get(source_id), empty, environ={})

    def test_an_unconditional_approval_with_no_compliance_entry_is_still_refused(self) -> None:
        """An empty scope is not an open one.

        A source could in principle pass every gate with a review that declares
        no condition at all. It still gets no authorization: there would be no
        attribution obligation, no resource rules and no minimisation profile to
        hand a collector, and handing one nothing is not the same as handing it
        permission. Built synthetically because no real source is in this shape,
        and the branch would otherwise never be exercised."""
        from sros_acquisition.compliance.config import ComplianceConfig
        from sros_acquisition.registry import (
            AccessProfile,
            PolicyEvidence,
            PolicyReview,
            SourceRecord,
        )
        from sros_contracts import PolicyEvidenceType, SourceAccessMethod

        source = SourceRecord(
            source_id="synthetic-probe",
            canonical_name="Synthetic probe",
            source_family="economic_data",
            access_profiles=(
                AccessProfile(access_method=SourceAccessMethod.PUBLIC_API, label="probe"),
            ),
            review=PolicyReview(
                approval_state=SourceApprovalState.APPROVED,
                assessed_use_case="a probe, approved with no condition attached",
                reviewed_by="test",
                reviewed_at=datetime.now(UTC),
                evidence=(
                    PolicyEvidence(
                        document_type=PolicyEvidenceType.OFFICIAL_TERMS,
                        document_title="Probe terms",
                        document_url="https://example.invalid/terms",
                        summarized_finding="A synthetic record; no platform was contacted.",
                        retrieved_at=datetime.now(UTC),
                    ),
                ),
            ),
        )
        assert evaluate_eligibility(source).eligible
        with pytest.raises(AcquisitionNotAuthorizedError, match="no compliance configuration"):
            build_authorization(
                source, ComplianceConfig(compliance_version="test", sources=()), environ={}
            )

    def test_the_context_carries_everything_a_collector_must_not_decide(
        self, catalog, compliance
    ) -> None:
        """§26. A collector that had to look any of these up would be forming a
        second opinion about a decision the review already made."""
        context = _context(catalog, compliance, "world-bank")
        assert context.access
        assert context.resource_scope.source_id == "world-bank"
        assert context.retention.raw_days == 30
        assert context.attribution.requirements
        assert context.data_minimisation.allowed and context.data_minimisation.excluded
        assert context.verifications
        assert context.review_version == 2

    def test_rate_limits_are_reported_as_unknown_rather_than_invented(
        self, catalog, compliance
    ) -> None:
        """§29. None of the three approving sources documents a limit. A number
        here would be a guess a collector would then trust."""
        for source_id in EXPECTED_ELIGIBLE:
            context = _context(catalog, compliance, source_id)
            for access in context.access:
                assert not access.rate_limit.known, source_id
                assert access.rate_limit.requests is None

    def test_retention_reaches_the_collector_and_cannot_be_chosen_by_it(
        self, catalog, compliance
    ) -> None:
        """§30. Retention is governance input. The context exposes the resolved
        rule and there is no setter."""
        context = _context(catalog, compliance, "eurostat")
        assert context.retention.raw_days <= 30
        assert context.retention.normalized_days <= 365
        with pytest.raises(FrozenInstanceError):
            context.retention.raw_days = 9999  # type: ignore[misc]

    def test_every_capability_conformance_check_passes(self, catalog, compliance) -> None:
        """§20. Registering a capability is not enough: its check runs the real
        gate against the real configuration."""
        checked = set()
        for source in catalog:
            entry = compliance.get(source.source_id)
            if entry is None:
                continue
            for condition in source.review.required_conditions:
                if condition.verification is not ConditionVerification.CAPABILITY:
                    continue
                name = condition.verification_detail
                checked.add(name)
                assert capability_failures(name, entry) == (), (source.source_id, name)
        assert checked == set(CAPABILITIES)


# ================================================================ the database


@needs_postgres
class TestRecordedVerification:
    def test_a_condition_cannot_be_satisfied_without_a_verification(self, conn) -> None:
        """§2. The SQL bypass, closed by migration 0007. This is the assertion
        that a manual boolean is impossible, whoever issues the UPDATE.

        The probe condition is CREATED here rather than borrowed from the
        catalog. An earlier version targeted `fred-api-key` because it was
        reliably unverified — and then a credential was configured, every
        condition acquired a verification, and the test had no subject left.
        A test that needs a row in a particular state should build it."""
        conn.execute("SAVEPOINT probe")
        condition_id = _unverified_condition(conn)
        with pytest.raises(Exception, match="no verification record"):
            conn.execute(
                """UPDATE registry.source_review_conditions
                      SET satisfied = TRUE, satisfied_at = now(), satisfied_by = 'me'
                    WHERE id = %s""",
                (condition_id,),
            )
        conn.execute("ROLLBACK TO SAVEPOINT probe")

    def test_recording_a_verification_clears_and_unclears_a_condition(
        self, conn, catalog, compliance
    ) -> None:
        """A condition that stops holding must stop clearing the gate. Recorded
        both ways in one transaction, then rolled back."""
        from sros_acquisition.compliance.repositories import record_verifications

        source = catalog.get("world-bank")
        conn.execute("SAVEPOINT probe")
        satisfied = _verified(source, compliance)
        report = record_verifications(conn, satisfied)
        assert report.satisfied == 3
        assert report.missing_conditions == ()
        reasons = conn.execute(
            "SELECT blocking_reasons FROM registry.source_eligibility WHERE source_id = %s",
            ("world-bank",),
        ).fetchone()[0]
        assert reasons == []

        undone = [
            replace(
                record,
                result=ConditionVerificationResult.UNSATISFIED,
                reason="probe: the capability was removed",
            )
            for record in satisfied
        ]
        record_verifications(conn, undone)
        reasons = conn.execute(
            "SELECT blocking_reasons FROM registry.source_eligibility WHERE source_id = %s",
            ("world-bank",),
        ).fetchone()[0]
        assert any("review conditions not satisfied" in r for r in reasons)
        conn.execute("ROLLBACK TO SAVEPOINT probe")

    def test_the_verification_log_is_append_only_in_practice(
        self, conn, catalog, compliance
    ) -> None:
        """Two runs at different moments leave two records. The history of a
        condition is part of what makes its current state trustworthy."""
        from sros_acquisition.compliance.repositories import record_verifications

        source = catalog.get("eurostat")
        conn.execute("SAVEPOINT probe")
        first = datetime(2026, 8, 29, 10, 0, tzinfo=UTC)
        record_verifications(conn, verify_source(source, compliance, {}, first))
        record_verifications(
            conn, verify_source(source, compliance, {}, first + timedelta(hours=1))
        )
        # Matched on the two exact moments, not a range: the database also holds
        # whatever an operator recorded earlier, and a range would count that.
        count = conn.execute(
            "SELECT count(*) FROM registry.source_condition_verifications "
            "WHERE source_id = %s AND verified_at IN (%s, %s)",
            ("eurostat", first, first + timedelta(hours=1)),
        ).fetchone()[0]
        assert count == 6
        conn.execute("ROLLBACK TO SAVEPOINT probe")

    def test_the_database_refuses_a_credential_value_in_a_verification(self, conn) -> None:
        """The one table a verifier writes free text into. Mechanical rather
        than remembered."""
        condition_id = conn.execute(
            "SELECT id FROM registry.source_review_conditions LIMIT 1"
        ).fetchone()[0]
        conn.execute("SAVEPOINT probe")
        with pytest.raises(Exception, match="no_secret_value"):
            conn.execute(
                """INSERT INTO registry.source_condition_verifications
                       (id, condition_id, source_id, condition_key, verifier,
                        verifier_version, result, reason, reference, verified_at)
                   SELECT gen_random_uuid(), id, source_id, condition_key, 'probe', '1',
                          'UNKNOWN', 'found the key ghp_0123456789abcdefghij', NULL, now()
                     FROM registry.source_review_conditions WHERE id = %s""",
                (condition_id,),
            )
        conn.execute("ROLLBACK TO SAVEPOINT probe")

    def test_python_and_sql_agree_on_every_source(self, conn, catalog, compliance) -> None:
        """§38. Two implementations of one rule, compared rather than trusted --
        and now with conditions verified on both sides, which is where they
        could most easily come apart."""
        from sros_acquisition.compliance.repositories import record_verifications
        from sros_acquisition.registry.repositories import read_eligibility

        conn.execute("SAVEPOINT probe")
        divergences = []
        for source in catalog:
            records = _verified(source, compliance)
            record_verifications(conn, records)
        for source in catalog:
            records = _verified(source, compliance)
            from_python = evaluate_eligibility(
                source, satisfied_conditions=satisfied_condition_keys(records)
            )
            from_db = read_eligibility(conn, source.source_id)
            assert from_db is not None
            if from_db.eligible != from_python.eligible or set(from_db.blocking_reasons) != set(
                from_python.blocking_reasons
            ):
                divergences.append(
                    (source.source_id, from_db.blocking_reasons, from_python.blocking_reasons)
                )
        assert divergences == []
        conn.execute("ROLLBACK TO SAVEPOINT probe")

    def test_nothing_is_collected_from_a_source_that_has_no_collector(self, conn) -> None:
        """The RULE, since Mission 1.5 made collection real.

        This assertion used to read `enabled == 0 and raw_records == 0`, which
        was true of every mission up to 1.4 and stopped being a property the
        moment one collector existed. Asserting it still would have been
        asserting a moment.

        What must hold forever is the ordering: nothing is enabled that has no
        collector, and nothing is collected from a source that is not enabled.
        Both hold whether the deployment has collected anything or not.
        """
        import sros_acquisition

        implemented = sros_acquisition.IMPLEMENTED_COLLECTORS

        enabled = {
            row[0]
            for row in conn.execute(
                "SELECT id FROM registry.sources WHERE collector_enabled"
            ).fetchall()
        }
        assert enabled <= implemented, f"enabled with no collector: {enabled - implemented}"

        collected = {
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT source_id FROM acquisition.raw_records"
            ).fetchall()
        }
        assert collected <= implemented, f"collected with no collector: {collected - implemented}"

        # Deliberately NOT `collected <= enabled`. Disabling a collector does
        # not retroactively make what it already collected illegitimate, and an
        # assertion that said so would forbid ever turning one off.

        # NARROWED in Mission 1.6, not deleted. This read
        # `normalized_records == 0`, which was true of every mission until one
        # normalized something -- the same stale absolute the two lines above
        # replaced one mission earlier, in the same test.
        #
        # The rule that survives is the ordering, one link further along:
        # nothing is normalized that no normalizer serves, and nothing is
        # normalized that was not collected first.
        normalizable = sros_acquisition.IMPLEMENTED_NORMALIZERS
        normalized = {
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT source_id FROM acquisition.normalized_records"
            ).fetchall()
        }
        assert normalized <= normalizable, (
            f"normalized with no normalizer: {normalized - normalizable}"
        )
        assert normalized <= collected, f"normalized but never collected: {normalized - collected}"

    def test_collectors_live_only_in_the_collection_package(self) -> None:
        """Mission 1.4 asserted that NO collector existed. Mission 1.5 built
        one, so the assertion was narrowed to *where* a collector may live
        rather than deleted -- the same move Mission 1.2 made with the D-03
        guard. The registry and compliance packages govern collection, and a
        collector inside either would put the decision and its execution in the
        same place."""
        import pathlib

        import sros_acquisition

        root = pathlib.Path(sros_acquisition.__file__).parent
        for package in ("registry", "compliance"):
            assert list((root / package).rglob("*collector*.py")) == []
        assert frozenset({"world-bank"}) == sros_acquisition.IMPLEMENTED_COLLECTORS

    def test_an_eligible_source_with_no_collector_cannot_be_enabled(self, capsys) -> None:
        """§25, restated on the source that still proves it.

        This test used to name `world-bank`, and when Mission 1.5 gave it a
        collector the test stopped asserting a refusal and **enabled a real
        collector as a side effect** -- which is the confusion §27 exists to
        prevent, found by the suite that came after it.

        Eurostat is the case that carries the property now: it passes the
        governance gate and has no collector, so the switch still cannot get
        ahead of the thing it switches."""
        from sros_acquisition.cli import main

        assert main(["enable", "eurostat"]) == 1
        assert "no collector is implemented" in capsys.readouterr().err

    def test_only_a_source_with_a_collector_is_ever_enabled(self, conn) -> None:
        """The invariant a previous version of this suite broke.

        A Mission 1.4 test called `sros-source enable world-bank` to assert a
        refusal; when Mission 1.5 gave World Bank a collector the call stopped
        being refused and enabled it for real. What is asserted now is the rule
        rather than a count, so it holds whether an operator has deliberately
        enabled something or not."""
        import sros_acquisition

        enabled = {
            row[0]
            for row in conn.execute(
                "SELECT id FROM registry.sources WHERE collector_enabled ORDER BY id"
            ).fetchall()
        }
        extra = enabled - sros_acquisition.IMPLEMENTED_COLLECTORS
        assert extra == set(), f"enabled with no collector behind it: {extra}"


def _unverified_condition(conn) -> object:
    """Create a condition with no verification behind it, and return its id.

    Caller is inside a SAVEPOINT and rolls back. Attached to a real review so
    the foreign keys hold; the key is unique so it cannot collide with a
    catalog condition or with a second call.
    """
    row = conn.execute(
        """INSERT INTO registry.source_review_conditions
               (id, review_id, source_id, condition_key, description, verification,
                verification_detail)
           SELECT gen_random_uuid(), r.id, r.source_id,
                  'probe-' || gen_random_uuid()::text,
                  'A probe condition, created inside a savepoint and rolled back.',
                  'HUMAN_CONFIRMATION', NULL
             FROM registry.source_policy_reviews r
            WHERE r.superseded_at IS NULL
            ORDER BY r.source_id
            LIMIT 1
           RETURNING id"""
    ).fetchone()
    assert row is not None
    return row[0]


def _context(catalog, compliance, source_id, environ=None):
    source = catalog.get(source_id)
    environ = environ if environ is not None else {}
    return build_authorization(
        source, compliance, verify_source(source, compliance, environ), environ=environ
    )
