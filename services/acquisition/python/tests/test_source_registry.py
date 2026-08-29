"""Source Registry: governance, not collection.

Mission 1.0 §34. These tests are about one question -- *may this source be
collected from, and on what recorded basis* -- and about the machinery that
makes the answer hard to fake.

They deliberately assert on the REAL catalog rather than a fixture. The
artefact under review is `docs/data/source-catalog-v1.json`; a suite that
checked a hand-made copy would leave the reviewed file unchecked, which is
exactly the failure these tests exist to prevent.

**Nothing here contacts a platform.** No HTTP client is imported, no endpoint is
opened, no record is collected. §5 forbids collection in this mission, and a
test that reached a real API would be collection.
"""

from __future__ import annotations

import json
import subprocess
import sys
import uuid

import pytest
from sros_acquisition.registry import (
    APPROVING_STATES,
    ASSESSED_ACTIVITIES,
    AUTHORITATIVE_EVIDENCE_TYPES,
    BASELINE_NORMALIZED_DAYS,
    BASELINE_RAW_DAYS,
    AccessProfile,
    RetentionOverride,
    SourceRegistryError,
    evaluate_eligibility,
    resolve_retention,
)
from sros_acquisition.registry.repositories import load_catalog_into, read_eligibility
from sros_contracts import SourceAccessMethod

from .conftest import REPO_ROOT, needs_postgres

CATALOG_PATH = REPO_ROOT / "docs/data/source-catalog-v1.json"


# ====================================================================== identity


class TestSourceIdentity:
    def test_source_ids_are_unique(self, catalog) -> None:
        ids = [s.source_id for s in catalog]
        assert len(ids) == len(set(ids))

    def test_source_ids_are_stable_slugs(self, catalog) -> None:
        """The id is a cross-system key: it appears in evidence provenance, in
        job payloads and in blocking reasons. A display name that could be
        retitled would silently break every one of those references."""
        for source in catalog:
            assert source.source_id == source.source_id.lower()
            assert source.source_id.replace("-", "").isalnum(), source.source_id
            assert not source.source_id.startswith("-")

    def test_every_source_belongs_to_a_registered_family(self, catalog) -> None:
        migration = (REPO_ROOT / "infrastructure/db/migrations/0004_source_registry.sql").read_text(
            encoding="utf-8"
        )
        for source in catalog:
            # The family registry is seeded by the migration; an unseeded family
            # would fail the foreign key at load time, and failing here first
            # says which family is missing rather than which constraint fired.
            assert f"'{source.source_family}'" in migration, source.source_family


# ================================================================ policy review


class TestPolicyReview:
    def test_every_source_carries_a_review(self, catalog) -> None:
        for source in catalog:
            assert source.review is not None, source.source_id

    def test_every_activity_is_assessed_separately(self, catalog) -> None:
        """§11. A single verdict for a whole platform hides the common case:
        automated API access permitted, commercial use not."""
        for source in catalog:
            for activity in ASSESSED_ACTIVITIES:
                assert source.review.assessment(activity) is not None, (
                    source.source_id,
                    activity,
                )

    def test_an_approving_state_requires_authoritative_evidence(self, catalog) -> None:
        for source in catalog:
            if source.review.approval_state in APPROVING_STATES:
                authoritative = [
                    e
                    for e in source.review.evidence
                    if e.document_type in AUTHORITATIVE_EVIDENCE_TYPES
                ]
                assert authoritative, (
                    f"{source.source_id} is {source.review.approval_state.value} with no "
                    "authoritative evidence"
                )

    def test_every_evidence_record_names_a_retrievable_document(self, catalog) -> None:
        """An approval whose basis cannot be re-opened cannot be re-verified when
        the platform changes its terms, which is the moment it matters."""
        for source in catalog:
            for item in source.review.evidence:
                assert item.document_url.startswith("https://"), item.document_url
                assert item.summarized_finding.strip()
                assert item.retrieved_at is not None

    def test_no_source_claims_a_permission_its_evidence_does_not_support(self, catalog) -> None:
        """§30. A PERMITTED verdict on an activity must rest on a retrieved
        document. Without one the honest value is NOT_ADDRESSED or UNCLEAR."""
        for source in catalog:
            review = source.review
            permitted = [
                a for a in ASSESSED_ACTIVITIES if review.assessment(a).value.startswith("PERMITTED")
            ]
            if permitted:
                assert review.evidence, (
                    f"{source.source_id} records {permitted} as permitted with no evidence"
                )

    def test_the_catalog_records_what_it_could_not_check(self, catalog) -> None:
        """§39. Unreachable terms are named, not silently dropped. Without this
        a reader cannot tell an unchecked source from a checked one."""
        assert catalog.known_limitations


# ================================================================== eligibility


class TestEligibility:
    def test_no_source_is_collector_eligible(self, catalog) -> None:
        """§31 states the standard: correctness over the number of approvals. A
        registry where every platform came back approved would mean the gate did
        nothing. Zero is the honest first-pass result, not a failure."""
        eligible = [s.source_id for s in catalog if evaluate_eligibility(s).eligible]
        assert eligible == []

    def test_the_gate_reports_every_reason_not_the_first(self, catalog) -> None:
        for source in catalog:
            result = evaluate_eligibility(source)
            if not result.eligible:
                assert result.blocking_reasons, source.source_id

    def test_public_visibility_is_never_a_reason_to_be_eligible(self, catalog) -> None:
        """§7. Publicly reachable data is not permitted data. A source whose only
        access method is the open web must still be blocked."""
        for source in catalog:
            methods = {p.access_method.value for p in source.access_profiles}
            if methods and methods <= {"PUBLIC_WEB", "RSS_OR_FEED"}:
                assert not evaluate_eligibility(source).eligible, source.source_id

    def test_the_catalog_format_carries_no_collector_switch(self, catalog) -> None:
        """A JSON file is not a review. Loading a catalog must never be the act
        that enables a collector, so the field does not exist to be set."""
        raw = CATALOG_PATH.read_text(encoding="utf-8")
        assert "collector_enabled" not in raw


# =================================================================== retention


class TestRetention:
    def test_the_baseline_applies_when_there_is_no_override(self) -> None:
        effective = resolve_retention(None)
        assert effective.raw_days == BASELINE_RAW_DAYS
        assert effective.normalized_days == BASELINE_NORMALIZED_DAYS

    def test_an_override_can_only_shorten_retention(self) -> None:
        """`data-retention-policy-v1.md` §1: the stricter applicable rule wins.
        An override asking for longer would be a platform's terms being used to
        weaken our own policy."""
        longer = RetentionOverride(
            basis="a source asking to keep data longer",
            reviewed_by="test",
            raw_days=BASELINE_RAW_DAYS + 900,
            normalized_days=BASELINE_NORMALIZED_DAYS + 900,
        )
        effective = resolve_retention(longer)
        assert effective.raw_days == BASELINE_RAW_DAYS
        assert effective.normalized_days == BASELINE_NORMALIZED_DAYS

    def test_an_override_that_shortens_is_applied(self) -> None:
        shorter = RetentionOverride(basis="platform cap", reviewed_by="test", raw_days=7)
        assert resolve_retention(shorter).raw_days == 7

    def test_an_override_must_state_its_basis(self) -> None:
        with pytest.raises(SourceRegistryError):
            RetentionOverride(basis="   ", reviewed_by="test", raw_days=7)

    def test_an_override_that_overrides_nothing_is_refused(self) -> None:
        """A row that changes nothing would still be read as a policy."""
        with pytest.raises(SourceRegistryError):
            RetentionOverride(basis="none", reviewed_by="test")

    def test_every_override_in_the_catalog_is_stricter_than_the_baseline(self, catalog) -> None:
        for source in catalog:
            if source.retention_override is None:
                continue
            effective = resolve_retention(source.retention_override)
            assert effective.raw_days <= BASELINE_RAW_DAYS
            assert effective.normalized_days <= BASELINE_NORMALIZED_DAYS
            assert effective.basis, source.source_id


# ============================================================== access metadata


class TestAccessMetadata:
    def test_no_credential_value_is_stored_anywhere(self) -> None:
        """§18. The registry is not a vault. A secret written here would reach
        every reader of the catalog, including a public repository."""
        blob = CATALOG_PATH.read_text(encoding="utf-8")
        for marker in ("-----BEGIN", "Bearer ", "sk-", "ghp_", "AIza", "AKIA", "xox"):
            assert marker not in blob, marker

    def test_secret_references_are_configuration_key_names(self, catalog) -> None:
        for source in catalog:
            for profile in source.access_profiles:
                for reference in profile.secret_references:
                    assert reference == reference.upper(), reference
                    assert reference.replace("_", "").isalnum(), reference

    def test_a_credential_looking_reference_is_refused(self) -> None:
        with pytest.raises(SourceRegistryError):
            AccessProfile(
                access_method=SourceAccessMethod.OFFICIAL_API,
                label="fixture",
                secret_references=("ghp_thislookslikearealtokenvalue",),
            )

    def test_an_unknown_rate_limit_is_recorded_as_unknown(self, catalog) -> None:
        """§19. A number with no stated origin is a guess a collector would
        trust. UNKNOWN is a real answer and must stay expressible."""
        for source in catalog:
            for profile in source.access_profiles:
                if profile.rate_limit_known:
                    assert profile.rate_limit_origin in ("DOCUMENTED", "OBSERVED")
                    assert profile.rate_limit_requests is not None
                else:
                    assert profile.rate_limit_requests is None

    def test_no_access_profile_describes_circumvention(self, catalog) -> None:
        """§21. Login walls, CAPTCHAs and anti-automation measures are limits,
        not obstacles. A profile describing how to get around one would be a
        design for doing it.

        Scoped to the access profiles on purpose. Reviewer notes must stay free
        to say "the undocumented endpoint is not an option": a blanket ban on the
        word would forbid recording the refusal, which is the opposite of what
        §21 asks for.
        """
        forbidden = (
            "captcha",
            "bypass",
            "circumvent",
            "evade",
            "rotate proxies",
            "anti-bot",
            "undocumented endpoint",
            "spoof",
        )
        for source in catalog:
            for profile in source.access_profiles:
                text = " ".join(
                    part.lower()
                    for part in (
                        profile.label,
                        profile.endpoint_url,
                        profile.documentation_url,
                        profile.approval_process_notes,
                        profile.notes,
                    )
                    if part
                )
                for term in forbidden:
                    assert term not in text, (source.source_id, profile.label, term)


# ============================================================ database contract


@needs_postgres
class TestDatabaseRules:
    def test_the_registry_carries_no_row_level_security(self, conn) -> None:
        """§25. Source metadata is GLOBAL. A per-workspace source review would
        make provenance incomparable between workspaces, so there is deliberately
        no policy here, and no `workspace_id` for one to filter on."""
        rows = conn.execute(
            """SELECT c.relname, c.relrowsecurity,
                      (SELECT count(*) FROM pg_policy p WHERE p.polrelid = c.oid)
                 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'registry' AND c.relkind = 'r'"""
        ).fetchall()
        assert rows
        for name, rls_enabled, policies in rows:
            assert not rls_enabled, name
            assert policies == 0, name

    def test_no_registry_table_has_a_workspace_column(self, conn) -> None:
        rows = conn.execute(
            """SELECT table_name FROM information_schema.columns
                WHERE table_schema = 'registry' AND column_name = 'workspace_id'"""
        ).fetchall()
        assert rows == []

    def test_the_registry_is_readable_with_no_tenant_context(self, conn) -> None:
        """Global metadata must not need a workspace to be read. Requiring one
        would imply an isolation that does not exist."""
        count = conn.execute("SELECT count(*) FROM registry.sources").fetchone()[0]
        assert count > 0

    def test_the_database_refuses_an_approval_with_no_evidence(self, conn) -> None:
        """The DEFERRABLE constraint trigger. Approval and evidence are written
        in one transaction, so the check runs at COMMIT -- but it does run."""
        conn.execute("SAVEPOINT probe")
        with pytest.raises(Exception) as exc:
            conn.execute(
                """INSERT INTO registry.source_policy_reviews
                       (id, source_id, review_version, approval_state,
                        assessed_use_case, reviewed_by)
                   VALUES (%s, 'reddit', 99, 'APPROVED', 'test fixture', 'test')""",
                (uuid.uuid4(),),
            )
            conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
        assert "evidence" in str(exc.value).lower(), str(exc.value)
        conn.execute("ROLLBACK TO SAVEPOINT probe")

    def test_an_approval_is_accepted_when_evidence_lands_in_the_same_transaction(
        self, conn
    ) -> None:
        """The deferral is not a loophole; it is what lets a legitimate review be
        written atomically. Both halves must be present by COMMIT."""
        conn.execute("SAVEPOINT probe")
        review_id = uuid.uuid4()
        conn.execute(
            """INSERT INTO registry.source_policy_reviews
                   (id, source_id, review_version, approval_state,
                    assessed_use_case, reviewed_by)
               VALUES (%s, 'reddit', 98, 'APPROVED', 'test fixture', 'test')""",
            (review_id,),
        )
        conn.execute(
            """INSERT INTO registry.source_policy_evidence
                   (id, review_id, source_id, document_type, document_title,
                    document_url, summarized_finding, retrieved_at)
               VALUES (%s, %s, 'reddit', 'OFFICIAL_TERMS', 'Fixture terms',
                       'https://example.invalid/terms', 'fixture', now())""",
            (uuid.uuid4(), review_id),
        )
        conn.execute("SET CONSTRAINTS ALL IMMEDIATE")  # must not raise
        conn.execute("ROLLBACK TO SAVEPOINT probe")

    def test_the_database_refuses_a_collector_on_an_ineligible_source(self, conn) -> None:
        """The last line of defence. Even a direct UPDATE by the migration role
        cannot turn on a collector for a source that has not passed the gate."""
        conn.execute("SAVEPOINT probe")
        with pytest.raises(Exception) as exc:
            conn.execute("UPDATE registry.sources SET collector_enabled = TRUE WHERE id = 'tiktok'")
        assert "eligib" in str(exc.value).lower(), str(exc.value)
        conn.execute("ROLLBACK TO SAVEPOINT probe")

    def test_the_python_gate_and_the_sql_view_agree(self, conn, catalog) -> None:
        """Two implementations of one rule is a real risk. The answer is to
        compare them on every source rather than to trust that they match.

        Since Mission 1.4 the Python side is given the satisfaction the database
        holds. Condition satisfaction is environment state, so evaluating
        without it would compare the same rule on different inputs and report a
        divergence that is really a missing argument."""
        from .conftest import recorded_satisfied_keys

        divergences = []
        for source in catalog:
            from_db = read_eligibility(conn, source.source_id)
            assert from_db is not None, source.source_id
            from_python = evaluate_eligibility(
                source, satisfied_conditions=recorded_satisfied_keys(conn, source.source_id)
            )
            if from_db.eligible != from_python.eligible:
                divergences.append(source.source_id)
        assert divergences == []

    def test_loading_the_catalog_twice_changes_nothing(self, conn, catalog) -> None:
        """Deterministic uuid5 row ids. A second load must converge on the rows
        that exist rather than inserting a parallel copy of the registry."""
        conn.execute("SAVEPOINT probe")
        before = load_catalog_into(conn, catalog)
        reviews_before = conn.execute(
            "SELECT count(*) FROM registry.source_policy_reviews"
        ).fetchone()[0]
        after = load_catalog_into(conn, catalog)
        reviews_after = conn.execute(
            "SELECT count(*) FROM registry.source_policy_reviews"
        ).fetchone()[0]
        assert before == after
        assert reviews_before == reviews_after
        conn.execute("ROLLBACK TO SAVEPOINT probe")

    def test_no_source_in_the_database_has_a_collector_enabled(self, conn) -> None:
        row = conn.execute(
            "SELECT count(*) FROM registry.sources WHERE collector_enabled"
        ).fetchone()
        assert row[0] == 0

    def test_no_raw_record_was_collected(self, conn) -> None:
        """§36. This mission acquires nothing. An empty `raw_records` is evidence
        that the prohibition held, not an assumption that it did."""
        assert conn.execute("SELECT count(*) FROM acquisition.raw_records").fetchone()[0] == 0


# ==================================================================== contracts


class TestContractAgreement:
    """The enums exist in three places. They must say the same thing."""

    REGISTRY_ENUMS = (
        "SourceApprovalState",
        "SourceAccessMethod",
        "PolicyAssessment",
        "PolicyEvidenceType",
        "SourceLifecycle",
        "SourceAcquisitionCost",
        "PersonalDataRisk",
    )

    @staticmethod
    def _closed_enums() -> dict[str, list[str]]:
        """`domain.v1.json` is the single source of truth ADR-009 names. Both
        generated languages are checked against it, never against each other."""
        document = json.loads(
            (REPO_ROOT / "packages/contracts/schema/domain.v1.json").read_text(encoding="utf-8")
        )
        return {
            entry["name"]: [
                # A value is recorded with its definition. Only the symbol is
                # compared here: the prose is for humans, the symbol is the
                # contract both languages have to honour.
                item["value"] if isinstance(item, dict) else item
                for item in entry["values"]
            ]
            for entry in document["closed_enums"]
        }

    def test_python_enums_match_the_contract_source(self) -> None:
        from sros_contracts import (
            PersonalDataRisk,
            PolicyAssessment,
            PolicyEvidenceType,
            SourceAccessMethod,
            SourceAcquisitionCost,
            SourceApprovalState,
            SourceLifecycle,
        )

        schema = self._closed_enums()
        pairs = {
            "SourceApprovalState": SourceApprovalState,
            "SourceAccessMethod": SourceAccessMethod,
            "PolicyAssessment": PolicyAssessment,
            "PolicyEvidenceType": PolicyEvidenceType,
            "SourceLifecycle": SourceLifecycle,
            "SourceAcquisitionCost": SourceAcquisitionCost,
            "PersonalDataRisk": PersonalDataRisk,
        }
        for name, enum in pairs.items():
            assert [m.value for m in enum] == schema[name], name

    def test_the_typescript_generation_matches_the_contract_source(self) -> None:
        """Read as text rather than executed: this suite has no Node runtime, and
        an unchecked generated file is how the two languages drift apart."""
        generated = (REPO_ROOT / "packages/contracts/src/generated/domain.ts").read_text(
            encoding="utf-8"
        )
        schema = self._closed_enums()
        for name in self.REGISTRY_ENUMS:
            assert name in generated, name
            for value in schema[name]:
                assert f'"{value}"' in generated, (name, value)


# ========================================================================== CLI


class TestCommandLine:
    """The review tooling must run. A governance process nobody can execute is
    a document, not a process."""

    @staticmethod
    def _run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603 - this interpreter, fixed args, no shell
            [sys.executable, "-m", "sros_acquisition.cli", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_validate_passes_on_the_real_catalog(self) -> None:
        result = self._run("validate")
        assert result.returncode == 0, result.stdout + result.stderr

    def test_list_shows_every_source_and_its_state(self) -> None:
        result = self._run("list")
        assert result.returncode == 0, result.stderr
        assert "tiktok" in result.stdout
        assert "PROHIBITED" in result.stdout

    def test_render_is_in_sync_with_the_catalog(self) -> None:
        """The markdown catalog is generated. Two hand-maintained copies of one
        fact drift, and the drift is found by whoever trusted the wrong one."""
        result = self._run("render", "--check")
        assert result.returncode == 0, result.stdout + result.stderr

    def test_enable_refuses_an_ineligible_source(self) -> None:
        """The CLI is the only write path. It must refuse for the same reason the
        database does, so a reviewer meets the rule before the trigger fires."""
        result = self._run("enable", "tiktok")
        assert result.returncode != 0
        assert "tiktok" in (result.stdout + result.stderr)
