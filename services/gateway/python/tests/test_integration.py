"""Integration tests against the real stack.

Categories from Mission 0.3 §36: runtime, tenancy, API, lifecycle.

The tenancy tests are the ones that matter most. They all use TWO workspaces,
because an isolation assertion needs something to be isolated from.

Both are this module's own, created before each test and dropped after it by
`own_workspaces` below. The seeded pair is shared with every other suite, and
this module writes on nearly every test -- projects, sessions, opportunities
and observations -- so writing there left all of it behind, run after run.
"""

from __future__ import annotations

import json
import uuid

import psycopg
import pytest
from sros_contracts import ContractError, MarketScope, ResearchContext, ResearchSessionStatus
from sros_gateway.cache.redis_client import GlobalCache, TenantCache, cache_key
from sros_gateway.db.repositories import (
    ALLOWED_TRANSITIONS,
    InvalidTransitionError,
    NotFoundError,
    OpportunityRepository,
    ResearchProjectRepository,
    ResearchSessionRepository,
)
from sros_gateway.vectors.qdrant_client import (
    TenantVectorStore,
    VectorPayload,
    workspace_filter,
)

from tests.conftest import (
    WORKSPACE_INTEGRATION_P,
    WORKSPACE_INTEGRATION_Q,
    header,
    needs_postgres,
    needs_qdrant,
    needs_redis,
)

CONTEXT = {"market_scope": {"type": "COUNTRY", "countries": ["FR"]}}


# ================================================================= workspaces


@pytest.fixture(autouse=True)
def own_workspaces(integration_workspaces) -> None:
    """Every test in this module runs in workspaces of its own.

    Autouse, and it hands nothing back: the tests name WORKSPACE_INTEGRATION_P
    and WORKSPACE_INTEGRATION_Q directly, so what they need is not a value but
    a guarantee -- that the two exist when a test starts and are gone when it
    ends. Requesting it by name in sixty signatures would state the same thing
    sixty times and leave the sixty-first writing into a seeded workspace.

    Autouse over the WHOLE module, including the Redis and Qdrant classes,
    which use a workspace id as an opaque tenant key and store no row against
    it. Two rules are easier to keep than one rule and an exemption, and the
    fixture is a no-op when PostgreSQL is unreachable, so those classes still
    run on a machine with no database.
    """


# ============================================================ runtime: schema


@needs_postgres
class TestSchemaRuntime:
    def test_all_six_schemas_exist(self, database) -> None:
        # privileged_transaction, not connection(): these are administrative
        # queries about the schema itself. Under the application role,
        # information_schema is filtered to what that role holds privileges on,
        # which would make the assertion measure grants rather than existence.
        with database.privileged_transaction() as conn:
            rows = conn.execute(
                """SELECT schema_name FROM information_schema.schemata
                   WHERE schema_name IN
                     ('core','registry','research','acquisition','nlp','scoring')"""
            ).fetchall()
        assert len(rows) == 6

    def test_the_schema_holds_exactly_the_expected_tables(self, database) -> None:
        """The set, not a count. A count that goes from 26 to 27 tells a reader
        the number changed; the set tells them which table appeared."""
        with database.privileged_transaction() as conn:
            rows = conn.execute(
                """SELECT table_schema||'.'||table_name FROM information_schema.tables
                   WHERE table_schema IN
                     ('core','registry','research','acquisition','nlp','scoring')
                     AND table_type = 'BASE TABLE'"""
            ).fetchall()
        assert {r[0] for r in rows} == {
            # 0001_foundation
            "core.schema_migrations",
            "core.users",
            "core.workspace_memberships",
            "core.workspaces",
            "registry.registry_entries",
            "research.research_projects",
            "research.research_sessions",
            "research.research_gaps",
            "research.opportunities",
            "research.opportunity_session_observations",
            "acquisition.raw_records",
            "acquisition.normalized_records",
            "nlp.signals",
            "nlp.embedding_provenance",
            "scoring.evidence",
            "registry.sources",
            # 0002_orchestration
            "research.research_plans",
            "research.research_jobs",
            "research.research_job_dependencies",
            "research.session_budget_entries",
            "research.research_completeness_records",
            # 0004_source_registry
            "registry.source_access_profiles",
            "registry.source_policy_reviews",
            "registry.source_policy_evidence",
            "registry.source_retention_policies",
            "registry.source_capabilities",
            # 0005_claim_evidence_alignment
            "research.claims",
            "research.claim_revisions",
            "research.claim_session_observations",
            "scoring.evidence_independence_groups",
            # 0006_review_conditions
            "registry.source_review_conditions",
            "registry.use_profiles",
            # 0007_condition_verification
            "registry.source_condition_verifications",
            # 0010_source_signal_coverage. GLOBAL reference data like the rest
            # of `registry`: no workspace_id, no RLS policy, SELECT-only at
            # runtime. Listed here by hand on purpose -- a new table SHOULD
            # fail this test until somebody states whether it is tenant data.
            "registry.source_signal_coverage",
            "registry.source_behavior_coverage",
            # 0012_signal_derivation_model. TENANT data, and listed as such in
            # `test_rls.py`: a signal's lineage names which observations a
            # workspace derived from, which is as much a statement about what a
            # tenant is researching as the signal itself.
            "nlp.signal_inputs",
            # 0013_signal_derivation_runs. Tenant data: where a REFUSED
            # derivation goes, so no row in nlp.signals ever means "no signal".
            "nlp.signal_derivation_runs",
            # 0018_claim_interpretation_runs. The same two facts one layer up:
            # where a REFUSED interpretation goes, and which Signals a run
            # CONSIDERED and did not cite (GAP-5, ADR-025).
            "research.claim_interpretation_runs",
            "research.claim_interpretation_inputs",
        }

    def test_the_source_eligibility_view_exists(self, database) -> None:
        """A view, deliberately, not a column. Eligibility stored as a flag can
        drift away from the reasons behind it; derived, it cannot."""
        with database.privileged_transaction() as conn:
            row = conn.execute(
                """SELECT table_type FROM information_schema.tables
                    WHERE table_schema = 'registry'
                      AND table_name = 'source_eligibility'"""
            ).fetchone()
        assert row is not None and row[0] == "VIEW"

    def test_migration_ledger_records_every_applied_migration(self, database) -> None:
        """The ledger matches the migrations on disk, in order.

        Derived rather than listed. An earlier version of this test hard-coded
        the eight migration names that existed when it was written, so every
        mission that added one broke it -- and a test that has to be edited to
        stay green teaches people to edit it rather than read it. That is the
        same defect Mission 1.4 found in six condition tests: it asserted a
        moment instead of a property.

        The property is that nothing was applied out of order and nothing on
        disk was skipped, which is what this now checks.
        """
        import pathlib

        migrations = sorted(
            path.stem
            for path in (
                pathlib.Path(__file__).resolve().parents[4] / "infrastructure" / "db" / "migrations"
            ).glob("*.sql")
        )
        assert migrations, "no migration files found; the check would pass vacuously"

        with database.privileged_transaction() as conn:
            rows = conn.execute(
                "SELECT version, checksum FROM core.schema_migrations ORDER BY version"
            ).fetchall()
        assert [r[0] for r in rows] == migrations
        assert all(len(r[1]) == 64 for r in rows)  # sha256 hex

    def test_every_tenant_table_has_a_workspace_id_leading_index(self, database) -> None:
        with database.privileged_transaction() as conn:
            rows = conn.execute(
                """SELECT tablename, indexdef FROM pg_indexes
                   WHERE schemaname IN ('research','acquisition','nlp','scoring')"""
            ).fetchall()
        by_table: dict[str, list[str]] = {}
        for table, definition in rows:
            by_table.setdefault(table, []).append(definition)
        missing = [t for t, defs in by_table.items() if not any("(workspace_id" in d for d in defs)]
        assert missing == []

    def test_workspace_id_not_null_is_enforced(self, database) -> None:
        # Privileged: a NULL workspace_id can never satisfy an RLS WITH CHECK,
        # so under a tenant transaction the policy would fire first and this
        # test would stop measuring the column constraint it is named after.
        with pytest.raises(Exception) as exc, database.privileged_transaction() as conn:
            conn.execute(
                "INSERT INTO research.research_projects (id, workspace_id, name) "
                "VALUES (%s, NULL, 'x')",
                (uuid.uuid4(),),
            )
        assert "null value" in str(exc.value).lower() or "not-null" in str(exc.value).lower()

    def test_foreign_key_rejects_an_unknown_workspace(self, database) -> None:
        # The tenant context is set to the SAME unknown workspace, so the RLS
        # policy is satisfied and the foreign key is what rejects the row. This
        # is the layering working as intended: a policy that passed did not
        # make an invalid row valid.
        unknown = uuid.uuid4()
        with (
            pytest.raises(Exception) as exc,
            database.tenant_transaction(unknown) as conn,
        ):
            conn.execute(
                "INSERT INTO research.research_projects (id, workspace_id, name) "
                "VALUES (%s, %s, 'x')",
                (uuid.uuid4(), unknown),
            )
        assert "foreign key" in str(exc.value).lower()

    def test_closed_enum_check_rejects_an_invented_status(self, database) -> None:
        """Ontology V2 §15: no state is invented. BUDGET_EXHAUSTED is not one."""
        project = ResearchProjectRepository(database).create(WORKSPACE_INTEGRATION_P, "enum probe")
        with (
            pytest.raises(Exception) as exc,
            database.tenant_transaction(WORKSPACE_INTEGRATION_P) as conn,
        ):
            conn.execute(
                """INSERT INTO research.research_sessions
                       (id, workspace_id, project_id, research_context,
                        research_context_hash, research_context_schema_version,
                        status, contract_version, ontology_version)
                       VALUES (%s,%s,%s,'{}','h','1.0.0','BUDGET_EXHAUSTED','1','2')""",
                (uuid.uuid4(), WORKSPACE_INTEGRATION_P, project.id),
            )
        assert "check constraint" in str(exc.value).lower()

    def test_numeric_range_check_rejects_an_out_of_range_score(self, database) -> None:
        project = ResearchProjectRepository(database).create(WORKSPACE_INTEGRATION_P, "range probe")
        with (
            pytest.raises(Exception) as exc,
            database.tenant_transaction(WORKSPACE_INTEGRATION_P) as conn,
        ):
            conn.execute(
                """INSERT INTO research.research_sessions
                       (id, workspace_id, project_id, research_context,
                        research_context_hash, research_context_schema_version,
                        status, contract_version, ontology_version,
                        research_completeness_score)
                       VALUES (%s,%s,%s,'{}','h','1.0.0','PENDING','1','2',101)""",
                (uuid.uuid4(), WORKSPACE_INTEGRATION_P, project.id),
            )
        assert "check constraint" in str(exc.value).lower()

    def test_evidence_level_range_is_enforced(self, database) -> None:
        claim_id = uuid.uuid4()
        with database.tenant_transaction(WORKSPACE_INTEGRATION_P) as conn:
            # A MANUAL HYPOTHESIS, so the row can stand alone: the evidence
            # requirement added in migration 0016 exempts both, and this test is
            # about `evidence_level`, not about that trigger.
            conn.execute(
                """INSERT INTO research.claims
                       (id, workspace_id, claim_type, temporality, origin)
                   VALUES (%s,%s,'HYPOTHESIS','EVERGREEN','MANUAL')""",
                (claim_id, WORKSPACE_INTEGRATION_P),
            )
            conn.execute(
                """INSERT INTO research.claim_revisions
                       (id, workspace_id, claim_id, revision, statement)
                   VALUES (%s,%s,%s,1,'a claim to hang evidence on')""",
                (uuid.uuid4(), WORKSPACE_INTEGRATION_P, claim_id),
            )
        with (
            pytest.raises(psycopg.errors.CheckViolation) as exc,
            database.tenant_transaction(WORKSPACE_INTEGRATION_P) as conn,
        ):
            conn.execute(
                # `direction` and `observation_category` became NOT NULL in
                # migration 0005, and `claim_id` in 0016; all three are supplied
                # here so the insert fails on the constraint UNDER TEST. Without
                # them it fails on a NOT NULL violation instead, and the test
                # passes while proving nothing. `claim_type` was DROPPED from
                # this table in 0016 -- naming it made the insert fail on an
                # UndefinedColumn error, which the old substring assertion would
                # have caught but a `str(exc.value)` match on a different
                # constraint would not (`testing-strategy.md` §24).
                """INSERT INTO scoring.evidence
                       (id, workspace_id, claim_id, evidence_level, direction,
                        observation_category, collected_at, expires_at)
                       VALUES (%s,%s,%s,6,'SUPPORTS','UNCATEGORISED',
                               now(), now())""",
                (uuid.uuid4(), WORKSPACE_INTEGRATION_P, claim_id),
            )
        assert exc.value.diag.constraint_name == "evidence_level_range_check"
        with database.tenant_transaction(WORKSPACE_INTEGRATION_P) as conn:
            conn.execute("DELETE FROM research.claims WHERE id = %s", (claim_id,))


# ======================================================= tenancy: PostgreSQL


@needs_postgres
class TestDatabaseTenantIsolation:
    def test_repository_fails_closed_without_a_workspace(self, database) -> None:
        repo = ResearchProjectRepository(database)
        with pytest.raises(ContractError):
            repo.list(None)  # type: ignore[arg-type]
        with pytest.raises(ContractError):
            repo.list("")  # type: ignore[arg-type]

    def test_workspace_a_cannot_read_workspace_b_projects(self, database) -> None:
        repo = ResearchProjectRepository(database)
        b_project = repo.create(WORKSPACE_INTEGRATION_Q, "workspace Q private project")

        with pytest.raises(NotFoundError):
            repo.get(WORKSPACE_INTEGRATION_P, b_project.id)

        a_ids = {p.id for p in repo.list(WORKSPACE_INTEGRATION_P, limit=200)}
        assert b_project.id not in a_ids

    def test_workspace_a_cannot_read_workspace_b_sessions(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        b_project = projects.create(WORKSPACE_INTEGRATION_Q, "Q sessions")
        b_session = sessions.create(
            WORKSPACE_INTEGRATION_Q, b_project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )

        with pytest.raises(NotFoundError):
            sessions.get(WORKSPACE_INTEGRATION_P, b_session.id)
        assert sessions.list_for_project(WORKSPACE_INTEGRATION_P, b_project.id) == []

    def test_workspace_a_cannot_read_workspace_b_observations(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        opportunities = OpportunityRepository(database)

        b_project = projects.create(WORKSPACE_INTEGRATION_Q, "Q observations")
        b_session = sessions.create(
            WORKSPACE_INTEGRATION_Q, b_project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )
        b_opportunity = opportunities.create(
            WORKSPACE_INTEGRATION_Q, "Q opportunity", MarketScope.country("FR")
        )
        opportunities.record_observation(
            WORKSPACE_INTEGRATION_Q, b_opportunity, b_session.id, "DISCOVERED", "HYPOTHESIS"
        )

        assert len(opportunities.list_observations(WORKSPACE_INTEGRATION_Q, b_opportunity)) == 1
        # From P: the opportunity is invisible, and so are its observations.
        with pytest.raises(NotFoundError):
            opportunities.get(WORKSPACE_INTEGRATION_P, b_opportunity)
        assert opportunities.list_observations(WORKSPACE_INTEGRATION_P, b_opportunity) == []

    def test_session_cannot_be_created_against_another_workspaces_project(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        b_project = projects.create(WORKSPACE_INTEGRATION_Q, "Q project for cross check")
        with pytest.raises(NotFoundError):
            sessions.create(
                WORKSPACE_INTEGRATION_P,
                b_project.id,
                ResearchContext.from_json(CONTEXT),
                "1.0.0",
                "2",
            )


# ==================================================== lifecycle & immutability


@needs_postgres
class TestResearchSessionLifecycle:
    def test_canonical_initial_status_is_pending(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        project = projects.create(WORKSPACE_INTEGRATION_P, "lifecycle")
        session = sessions.create(
            WORKSPACE_INTEGRATION_P, project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )
        assert session.status is ResearchSessionStatus.PENDING

    def test_context_is_canonicalized_before_persistence(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        project = projects.create(WORKSPACE_INTEGRATION_P, "canonicalization")
        context = ResearchContext.from_json(
            {
                "market_scope": {"type": "MULTI_COUNTRY", "countries": ["us", "FR", "us"]},
                "languages": ["EN", "fr", "en"],
            }
        )
        session = sessions.create(WORKSPACE_INTEGRATION_P, project.id, context, "1.0.0", "2")
        stored = session.research_context
        assert stored["market_scope"]["countries"] == ["FR", "US"]
        assert stored["languages"] == ["en", "fr"]
        assert session.research_context_hash == context.snapshot_hash()

    def test_snapshot_is_immutable_no_update_path_exists(self, database) -> None:
        """Ontology V2 §11.3: a new specification means a new session."""
        assert not hasattr(ResearchSessionRepository, "update_context")
        assert not hasattr(ResearchSessionRepository, "patch_context")

        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        project = projects.create(WORKSPACE_INTEGRATION_P, "immutability")
        original = ResearchContext.from_json(CONTEXT)
        session = sessions.create(WORKSPACE_INTEGRATION_P, project.id, original, "1.0.0", "2")

        # Editing the in-memory context produces a NEW object and leaves the
        # persisted snapshot untouched.
        changed = original.with_changes(audience="indie devs")
        assert changed.snapshot_hash() != original.snapshot_hash()

        reread = sessions.get(WORKSPACE_INTEGRATION_P, session.id)
        assert reread.research_context_hash == original.snapshot_hash()
        assert reread.research_context["audience"] is None

    def test_valid_transition_is_accepted(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        project = projects.create(WORKSPACE_INTEGRATION_P, "transitions")
        session = sessions.create(
            WORKSPACE_INTEGRATION_P, project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )
        moved = sessions.transition(
            WORKSPACE_INTEGRATION_P, session.id, ResearchSessionStatus.PLANNING
        )
        assert moved.status is ResearchSessionStatus.PLANNING
        assert moved.started_at is not None

    def test_invalid_transition_is_rejected(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        project = projects.create(WORKSPACE_INTEGRATION_P, "invalid transitions")
        session = sessions.create(
            WORKSPACE_INTEGRATION_P, project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )
        # PENDING -> COMPLETED skips the whole lifecycle.
        with pytest.raises(InvalidTransitionError):
            sessions.transition(
                WORKSPACE_INTEGRATION_P, session.id, ResearchSessionStatus.COMPLETED
            )

    def test_terminal_states_are_terminal(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        project = projects.create(WORKSPACE_INTEGRATION_P, "terminal")
        session = sessions.create(
            WORKSPACE_INTEGRATION_P, project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )
        sessions.transition(WORKSPACE_INTEGRATION_P, session.id, ResearchSessionStatus.CANCELLED)
        with pytest.raises(InvalidTransitionError):
            sessions.transition(WORKSPACE_INTEGRATION_P, session.id, ResearchSessionStatus.PLANNING)

    def test_scoring_may_reach_completed_budget_exhaustion_is_not_failure(self) -> None:
        """ADR-006 / Ontology V2 §15, asserted on the transition table itself."""
        assert ResearchSessionStatus.COMPLETED in ALLOWED_TRANSITIONS[ResearchSessionStatus.SCORING]
        assert ALLOWED_TRANSITIONS[ResearchSessionStatus.COMPLETED] == frozenset()


# ================================================================ tenancy: API


@needs_postgres
class TestApi:
    def test_health_does_not_depend_on_the_database(self, api_client) -> None:
        response = api_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    def test_ready_reports_dependencies(self, api_client) -> None:
        response = api_client.get("/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["dependencies"]["postgres"] == "ok"
        assert body["dependencies"]["redis"] == "ok"
        assert body["correlation_id"]

    def test_correlation_id_is_echoed_back(self, api_client) -> None:
        response = api_client.get("/ready", headers={"x-correlation-id": "given-id"})
        assert response.headers["x-correlation-id"] == "given-id"
        assert response.json()["correlation_id"] == "given-id"

    def test_missing_workspace_fails_closed(self, api_client) -> None:
        response = api_client.get("/api/v1/research-projects")
        assert response.status_code == 400
        assert response.json()["error"] == "workspace_required"

    def test_project_create_and_read(self, api_client) -> None:
        created = api_client.post(
            "/api/v1/research-projects",
            json={"name": "API project", "description": "d"},
            headers=header(WORKSPACE_INTEGRATION_P),
        )
        assert created.status_code == 201
        project_id = created.json()["id"]

        fetched = api_client.get(
            f"/api/v1/research-projects/{project_id}", headers=header(WORKSPACE_INTEGRATION_P)
        )
        assert fetched.status_code == 200
        assert fetched.json()["name"] == "API project"

    def test_session_create_persists_snapshot_hash_and_version(self, api_client) -> None:
        project_id = api_client.post(
            "/api/v1/research-projects",
            json={"name": "API session project"},
            headers=header(WORKSPACE_INTEGRATION_P),
        ).json()["id"]

        created = api_client.post(
            f"/api/v1/research-projects/{project_id}/sessions",
            json={"research_context": {"market_scope": {"type": "COUNTRY", "countries": ["fr"]}}},
            headers=header(WORKSPACE_INTEGRATION_P),
        )
        assert created.status_code == 201
        body = created.json()
        assert body["status"] == "PENDING"
        assert body["research_context"]["market_scope"]["countries"] == ["FR"]
        assert len(body["research_context_hash"]) == 64
        assert body["research_context_schema_version"] == "1.0.0"
        assert body["research_completeness_score"] is None

    def test_invalid_research_context_is_rejected_with_422(self, api_client) -> None:
        project_id = api_client.post(
            "/api/v1/research-projects",
            json={"name": "invalid context"},
            headers=header(WORKSPACE_INTEGRATION_P),
        ).json()["id"]

        # COUNTRY with two codes is MULTI_COUNTRY (Ontology V2 §4.4).
        response = api_client.post(
            f"/api/v1/research-projects/{project_id}/sessions",
            json={
                "research_context": {"market_scope": {"type": "COUNTRY", "countries": ["FR", "DE"]}}
            },
            headers=header(WORKSPACE_INTEGRATION_P),
        )
        assert response.status_code == 422
        assert response.json()["error"] == "contract_violation"

    def test_segment_scope_is_rejected_a12_stays_open(self, api_client) -> None:
        project_id = api_client.post(
            "/api/v1/research-projects",
            json={"name": "a12"},
            headers=header(WORKSPACE_INTEGRATION_P),
        ).json()["id"]
        response = api_client.post(
            f"/api/v1/research-projects/{project_id}/sessions",
            json={"research_context": {"market_scope": {"type": "SEGMENT"}}},
            headers=header(WORKSPACE_INTEGRATION_P),
        )
        assert response.status_code == 422
        assert "A-12" in response.json()["detail"]

    def test_no_patch_endpoint_for_research_context(self, api_client) -> None:
        """A new specification means a new session, not a mutated snapshot."""
        project_id = api_client.post(
            "/api/v1/research-projects",
            json={"name": "no patch"},
            headers=header(WORKSPACE_INTEGRATION_P),
        ).json()["id"]
        session_id = api_client.post(
            f"/api/v1/research-projects/{project_id}/sessions",
            json={"research_context": CONTEXT},
            headers=header(WORKSPACE_INTEGRATION_P),
        ).json()["id"]

        response = api_client.patch(
            f"/api/v1/research-sessions/{session_id}",
            json={"research_context": {"market_scope": {"type": "GLOBAL"}}},
            headers=header(WORKSPACE_INTEGRATION_P),
        )
        assert response.status_code in (404, 405)

    def test_cross_workspace_read_is_rejected(self, api_client) -> None:
        project_id = api_client.post(
            "/api/v1/research-projects",
            json={"name": "A only"},
            headers=header(WORKSPACE_INTEGRATION_P),
        ).json()["id"]

        response = api_client.get(
            f"/api/v1/research-projects/{project_id}", headers=header(WORKSPACE_INTEGRATION_Q)
        )
        assert response.status_code == 404


# =============================================================== source registry


@needs_postgres
class TestSourceRegistryApi:
    """Mission 1.0 §27. Read only, and global.

    There is deliberately no write path: authentication does not exist, so an
    endpoint able to approve a source or enable a collector would make the whole
    review process optional for anyone who can reach the service.
    """

    def test_the_registry_is_readable_without_a_workspace(self, api_client) -> None:
        """Source definitions are global platform metadata. Demanding a tenant
        header would imply an isolation the registry does not have."""
        response = api_client.get("/api/v1/sources")
        assert response.status_code == 200
        body = response.json()
        assert body["count"] > 0

    def test_the_api_reports_enablement_and_eligibility_separately(self, api_client) -> None:
        """Mission 1.4 made eligibility reachable and Mission 1.5 made enablement
        reachable, so this assertion has been narrowed twice.

        `enabled == 0` was true of every mission until one collector existed. The
        rule that survives is that the two are reported as different facts and
        that the eligible count matches the view's own contract -- both hold
        whether an operator has enabled something or not."""
        body = api_client.get("/api/v1/sources").json()
        for source in body["sources"]:
            assert set(source) >= {"collector_eligible", "collector_enabled"}

        # KNOWN DEFECT, found by Mission 1.15.7 and deliberately not fixed here.
        #
        # `registry.source_eligibility` became one row per (source, PROFILE) in
        # Mission 1.15.5. This endpoint joins it on `source_id` alone, so a
        # source reviewed under two profiles is returned TWICE with two
        # different verdicts -- and `collector_enabled`, which is a column on
        # the source and carries its own `collector_use_profile`, is repeated
        # beside both. `ted-eu` is the first and only such source.
        #
        # So the old assertion here -- enabled implies eligible -- cannot hold
        # against an unscoped read, and it was asserting a property of the
        # DATABASE through an endpoint that does not preserve it. The database
        # itself is correct: `require_eligibility_for_collector` looks up the
        # row for the profile enablement was granted under, and refuses
        # otherwise.
        #
        # This is the third appearance of one defect -- a verdict reported with
        # no subject. ADR-027 gave verdicts a subject, Mission 1.15.6 fixed the
        # CLI reporting commands and 1.15.6.3 fixed readiness. The HTTP layer
        # was not re-checked, and choosing which profile it should answer about
        # is a design decision with no default, so it belongs to a mission that
        # says so rather than to a TED collector mission.
        #
        # Asserted as the DEFECT rather than removed, so it fails the day it is
        # fixed and this comment gets deleted with it.
        duplicated = [
            s["source_id"]
            for s in body["sources"]
            if [o for o in body["sources"] if o["source_id"] == s["source_id"]][1:]
        ]
        assert set(duplicated) == {"ted-eu"}, duplicated
        for source in body["sources"]:
            if source["collector_enabled"] and source["source_id"] not in duplicated:
                assert source["collector_eligible"], source["source_id"]
        assert body["collector_eligible_count"] == sum(
            1 for s in body["sources"] if not s["blocking_reasons"]
        )

    def test_a_source_is_eligible_exactly_when_it_has_no_blocking_reason(self, api_client) -> None:
        """The view's contract, served unchanged: an empty reason array is the
        pass, and a blocked source always says why."""
        for source in api_client.get("/api/v1/sources").json()["sources"]:
            assert source["collector_eligible"] == (not source["blocking_reasons"]), source[
                "source_id"
            ]

    def test_the_eligibility_endpoint_explains_every_condition(self, api_client) -> None:
        """Mission 1.4 §32. Read-only visibility into why a source can or cannot
        be collected from, condition by condition."""
        body = api_client.get("/api/v1/sources/fred/eligibility").json()
        assert body["source_id"] == "fred"
        assert body["approval_state"] == "APPROVED_WITH_CONDITIONS"
        assert len(body["conditions"]) == 3
        keys = {c["condition_key"] for c in body["conditions"]}
        assert keys == {"fred-api-key", "fred-endorsement-notice", "copyrighted-series-excluded"}
        assert body["collector_enabled"] is False
        for condition in body["conditions"]:
            assert condition["description"]
            assert condition["verification"] in {
                "CONFIG_REFERENCE",
                "CAPABILITY",
                "RETENTION_LIMIT",
                "ACCESS_METHOD",
                "HUMAN_CONFIRMATION",
            }

    def test_the_eligibility_endpoint_serves_key_names_never_credentials(self, api_client) -> None:
        """§37. A CONFIG_REFERENCE condition's detail is the configuration KEY
        NAME. The registry never held the value, so this cannot serve it."""
        body = api_client.get("/api/v1/sources/fred/eligibility").json()
        credential = next(c for c in body["conditions"] if c["condition_key"] == "fred-api-key")
        assert credential["verification_detail"] == "FRED_API_KEY"
        blob = json.dumps(body)
        assert "sk-" not in blob
        assert "secret" not in blob.lower()

    def test_the_eligibility_endpoint_cannot_write(self, api_client) -> None:
        """§32. No mutation path. Verification is administered through the CLI,
        which runs as the migration role; the runtime role holds SELECT only."""
        for method in ("post", "put", "patch", "delete"):
            response = getattr(api_client, method)("/api/v1/sources/fred/eligibility")
            assert response.status_code in (404, 405), method

    def test_an_unknown_source_eligibility_is_a_404(self, api_client) -> None:
        assert api_client.get("/api/v1/sources/not-a-source/eligibility").status_code == 404

    def test_a_source_detail_carries_its_evidence_urls(self, api_client) -> None:
        """The point of recording evidence is that it can be re-opened. An
        approval whose basis cannot be re-read cannot be re-verified when the
        platform changes its terms."""
        body = api_client.get("/api/v1/sources/tiktok").json()
        assert body["approval_state"] == "PROHIBITED"
        assert body["evidence"]
        assert all(e["document_url"].startswith("https://") for e in body["evidence"])

    def test_the_api_serves_key_names_never_credentials(self, api_client) -> None:
        body = api_client.get("/api/v1/sources/youtube").json()
        references = [r for p in body["access_profiles"] for r in p["secret_references"]]
        assert references == ["YOUTUBE_API_KEY"]
        assert "value" not in json.dumps(body).lower().split("secret_references")[0][-40:]

    def test_an_unknown_rate_limit_is_served_as_null_not_zero(self, api_client) -> None:
        """A zero would be read as a real limit by whatever consumes this.

        `requests` may legitimately be absent while the limit is known: Steam
        documents a daily quota and no per-period rate. What must never appear
        is a ZERO, in any dimension -- that is the value a consumer would read
        as "no requests allowed" or, worse, divide by.
        """
        for source in api_client.get("/api/v1/sources").json()["sources"]:
            detail = api_client.get(f"/api/v1/sources/{source['source_id']}").json()
            for profile in detail["access_profiles"]:
                limit = profile["rate_limit"]
                if limit is None:
                    continue
                numbers = {k: v for k, v in limit.items() if isinstance(v, int | float)}
                assert numbers, source["source_id"]
                for name, value in numbers.items():
                    assert value > 0, f"{source['source_id']}.{name}"

    def test_an_unknown_source_is_a_404(self, api_client) -> None:
        response = api_client.get("/api/v1/sources/not-a-source")
        assert response.status_code == 404

    def test_there_is_no_write_path(self, api_client) -> None:
        """The absence is the feature. Review is administered through
        `sros-source`, which runs as the migration role."""
        for method, path in (
            ("post", "/api/v1/sources"),
            ("patch", "/api/v1/sources/tiktok"),
            ("put", "/api/v1/sources/tiktok"),
            ("delete", "/api/v1/sources/tiktok"),
        ):
            response = api_client.request(method.upper(), path, json={})
            assert response.status_code in (404, 405), (method, path)


# ============================================================== tenancy: Redis


@needs_redis
class TestRedisTenantIsolation:
    def test_same_logical_key_differs_physically_per_workspace(self) -> None:
        a = cache_key(str(WORKSPACE_INTEGRATION_P), "market", "FR")
        b = cache_key(str(WORKSPACE_INTEGRATION_Q), "market", "FR")
        assert a != b
        assert str(WORKSPACE_INTEGRATION_P) in a and str(WORKSPACE_INTEGRATION_Q) in b

    def test_cache_key_requires_a_workspace(self) -> None:
        with pytest.raises(ContractError):
            cache_key("", "market", "FR")

    def test_tenant_cache_requires_a_workspace(self, redis_client) -> None:
        with pytest.raises(ContractError):
            TenantCache(redis_client, "")

    def test_workspace_a_cannot_read_workspace_b_entry(self, redis_client) -> None:
        a = TenantCache(redis_client, WORKSPACE_INTEGRATION_P)
        b = TenantCache(redis_client, WORKSPACE_INTEGRATION_Q)
        try:
            b.set("probe", "shared-logical-key", value="workspace-b-secret", ttl_seconds=60)
            assert b.get("probe", "shared-logical-key") == b"workspace-b-secret"
            # Same logical key, different tenant: a miss, not a leak.
            assert a.get("probe", "shared-logical-key") is None
        finally:
            b.delete("probe", "shared-logical-key")

    def test_global_cache_is_a_separate_namespace(self, redis_client) -> None:
        tenant = TenantCache(redis_client, WORKSPACE_INTEGRATION_P)
        glob = GlobalCache(redis_client)
        assert not glob.key("registry", "product_type").startswith(
            tenant.key("registry", "product_type")
        )
        assert ":global:" in glob.key("registry", "product_type")


# ============================================================= tenancy: Qdrant


@needs_qdrant
class TestQdrantTenantIsolation:
    COLLECTION = "sros_probe_m03"

    @pytest.fixture(autouse=True)
    def collection(self, qdrant):
        from qdrant_client import models

        qdrant.recreate_collection(
            collection_name=self.COLLECTION,
            vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE),
        )
        yield
        qdrant.delete_collection(self.COLLECTION)

    def test_filter_construction_requires_a_workspace(self) -> None:
        with pytest.raises(ContractError):
            workspace_filter("")

    def test_store_requires_a_workspace(self, qdrant) -> None:
        with pytest.raises(ContractError):
            TenantVectorStore(qdrant, "")

    def test_filter_always_contains_the_workspace_condition(self, qdrant) -> None:
        store = TenantVectorStore(qdrant, WORKSPACE_INTEGRATION_P)
        built = store.build_filter()
        assert built["must"][0]["key"] == "workspace_id"
        assert built["must"][0]["match"]["value"] == str(WORKSPACE_INTEGRATION_P)

    def test_session_scope_is_additive_not_a_replacement(self, qdrant) -> None:
        store = TenantVectorStore(qdrant, WORKSPACE_INTEGRATION_P)
        built = store.build_filter(research_session_id="sess-1")
        keys = [c["key"] for c in built["must"]]
        assert keys == ["workspace_id", "research_session_id"]

    def test_cross_tenant_write_is_refused(self, qdrant) -> None:
        store = TenantVectorStore(qdrant, WORKSPACE_INTEGRATION_P)
        with pytest.raises(ContractError):
            store.upsert(
                self.COLLECTION,
                str(uuid.uuid4()),
                [0.1, 0.2, 0.3, 0.4],
                VectorPayload(workspace_id=str(WORKSPACE_INTEGRATION_Q)),
            )

    def test_workspace_a_search_cannot_return_workspace_b_vectors(self, qdrant) -> None:
        a = TenantVectorStore(qdrant, WORKSPACE_INTEGRATION_P)
        b = TenantVectorStore(qdrant, WORKSPACE_INTEGRATION_Q)

        a_id, b_id = str(uuid.uuid4()), str(uuid.uuid4())
        a.upsert(
            self.COLLECTION,
            a_id,
            [1.0, 0.0, 0.0, 0.0],
            VectorPayload(workspace_id=str(WORKSPACE_INTEGRATION_P)),
        )
        b.upsert(
            self.COLLECTION,
            b_id,
            [1.0, 0.0, 0.0, 0.0],
            VectorPayload(workspace_id=str(WORKSPACE_INTEGRATION_Q)),
        )

        # Identical vectors: only the tenant filter separates them.
        a_hits = {str(p.id) for p in a.search(self.COLLECTION, [1.0, 0.0, 0.0, 0.0], limit=10)}
        b_hits = {str(p.id) for p in b.search(self.COLLECTION, [1.0, 0.0, 0.0, 0.0], limit=10)}

        assert a_id in a_hits and b_id not in a_hits
        assert b_id in b_hits and a_id not in b_hits
        assert a.count(self.COLLECTION) == 1
        assert b.count(self.COLLECTION) == 1

    def test_delete_workspace_removes_only_that_tenant(self, qdrant) -> None:
        a = TenantVectorStore(qdrant, WORKSPACE_INTEGRATION_P)
        b = TenantVectorStore(qdrant, WORKSPACE_INTEGRATION_Q)
        a.upsert(
            self.COLLECTION,
            str(uuid.uuid4()),
            [0.0, 1.0, 0.0, 0.0],
            VectorPayload(workspace_id=str(WORKSPACE_INTEGRATION_P)),
        )
        b.upsert(
            self.COLLECTION,
            str(uuid.uuid4()),
            [0.0, 1.0, 0.0, 0.0],
            VectorPayload(workspace_id=str(WORKSPACE_INTEGRATION_Q)),
        )

        a.delete_workspace(self.COLLECTION)
        assert a.count(self.COLLECTION) == 0
        assert b.count(self.COLLECTION) == 1


# ======================================================== opportunity boundary


@needs_postgres
class TestOpportunityBoundary:
    def test_opportunity_is_not_owned_by_a_session(self, database) -> None:
        """Ontology V2 §12: rediscovery must not create a duplicate."""
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        opportunities = OpportunityRepository(database)

        project = projects.create(WORKSPACE_INTEGRATION_P, "rediscovery")
        first = sessions.create(
            WORKSPACE_INTEGRATION_P, project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )
        second = sessions.create(
            WORKSPACE_INTEGRATION_P, project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )

        opportunity = opportunities.create(
            WORKSPACE_INTEGRATION_P, "rediscovered opportunity", MarketScope.country("FR")
        )
        opportunities.record_observation(
            WORKSPACE_INTEGRATION_P, opportunity, first.id, "DISCOVERED", "HYPOTHESIS"
        )
        opportunities.record_observation(
            WORKSPACE_INTEGRATION_P, opportunity, second.id, "CORROBORATED", "INFERRED"
        )

        observations = opportunities.list_observations(WORKSPACE_INTEGRATION_P, opportunity)
        assert len(observations) == 2
        assert {o["observation_kind"] for o in observations} == {"DISCOVERED", "CORROBORATED"}

    def test_observation_kind_comes_from_the_authoritative_set(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        opportunities = OpportunityRepository(database)
        project = projects.create(WORKSPACE_INTEGRATION_P, "kinds")
        session = sessions.create(
            WORKSPACE_INTEGRATION_P, project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )
        opportunity = opportunities.create(WORKSPACE_INTEGRATION_P, "kinds", MarketScope.global_())
        with pytest.raises(ContractError):
            opportunities.record_observation(
                WORKSPACE_INTEGRATION_P, opportunity, session.id, "SCORED", "OBSERVED"
            )

    def test_no_identity_resolution_helper_exists(self) -> None:
        """§35: deciding two opportunities are identical stays an open problem."""
        forbidden = {"find_similar", "match_by_title", "resolve_identity", "deduplicate"}
        assert forbidden.isdisjoint(dir(OpportunityRepository))
