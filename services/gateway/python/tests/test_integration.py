"""Integration tests against the real stack.

Categories from Mission 0.3 §36: runtime, tenancy, API, lifecycle.

The tenancy tests are the ones that matter most. They all use TWO workspaces,
because an isolation assertion needs something to be isolated from.
"""

from __future__ import annotations

import uuid

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
    WORKSPACE_A,
    WORKSPACE_B,
    header,
    needs_postgres,
    needs_qdrant,
    needs_redis,
)

CONTEXT = {"market_scope": {"type": "COUNTRY", "countries": ["FR"]}}


# ============================================================ runtime: schema


@needs_postgres
class TestSchemaRuntime:
    def test_all_six_schemas_exist(self, database) -> None:
        with database.connection() as conn:
            rows = conn.execute(
                """SELECT schema_name FROM information_schema.schemata
                   WHERE schema_name IN
                     ('core','registry','research','acquisition','nlp','scoring')"""
            ).fetchall()
        assert len(rows) == 6

    def test_all_sixteen_tables_exist(self, database) -> None:
        with database.connection() as conn:
            rows = conn.execute(
                """SELECT table_schema||'.'||table_name FROM information_schema.tables
                   WHERE table_schema IN
                     ('core','registry','research','acquisition','nlp','scoring')"""
            ).fetchall()
        assert len(rows) == 16, sorted(r[0] for r in rows)

    def test_migration_ledger_records_the_applied_migration(self, database) -> None:
        with database.connection() as conn:
            rows = conn.execute("SELECT version, checksum FROM core.schema_migrations").fetchall()
        assert [r[0] for r in rows] == ["0001_foundation"]
        assert len(rows[0][1]) == 64  # sha256 hex

    def test_every_tenant_table_has_a_workspace_id_leading_index(self, database) -> None:
        with database.connection() as conn:
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
        with pytest.raises(Exception) as exc, database.transaction() as conn:
            conn.execute(
                "INSERT INTO research.research_projects (id, workspace_id, name) "
                "VALUES (%s, NULL, 'x')",
                (uuid.uuid4(),),
            )
        assert "null value" in str(exc.value).lower() or "not-null" in str(exc.value).lower()

    def test_foreign_key_rejects_an_unknown_workspace(self, database) -> None:
        with pytest.raises(Exception) as exc, database.transaction() as conn:
            conn.execute(
                "INSERT INTO research.research_projects (id, workspace_id, name) "
                "VALUES (%s, %s, 'x')",
                (uuid.uuid4(), uuid.uuid4()),
            )
        assert "foreign key" in str(exc.value).lower()

    def test_closed_enum_check_rejects_an_invented_status(self, database) -> None:
        """Ontology V2 §15: no state is invented. BUDGET_EXHAUSTED is not one."""
        project = ResearchProjectRepository(database).create(WORKSPACE_A, "enum probe")
        with pytest.raises(Exception) as exc, database.transaction() as conn:
            conn.execute(
                """INSERT INTO research.research_sessions
                       (id, workspace_id, project_id, research_context,
                        research_context_hash, research_context_schema_version,
                        status, contract_version, ontology_version)
                       VALUES (%s,%s,%s,'{}','h','1.0.0','BUDGET_EXHAUSTED','1','2')""",
                (uuid.uuid4(), WORKSPACE_A, project.id),
            )
        assert "check constraint" in str(exc.value).lower()

    def test_numeric_range_check_rejects_an_out_of_range_score(self, database) -> None:
        project = ResearchProjectRepository(database).create(WORKSPACE_A, "range probe")
        with pytest.raises(Exception) as exc, database.transaction() as conn:
            conn.execute(
                """INSERT INTO research.research_sessions
                       (id, workspace_id, project_id, research_context,
                        research_context_hash, research_context_schema_version,
                        status, contract_version, ontology_version,
                        research_completeness_score)
                       VALUES (%s,%s,%s,'{}','h','1.0.0','PENDING','1','2',101)""",
                (uuid.uuid4(), WORKSPACE_A, project.id),
            )
        assert "check constraint" in str(exc.value).lower()

    def test_evidence_level_range_is_enforced(self, database) -> None:
        with pytest.raises(Exception) as exc, database.transaction() as conn:
            conn.execute(
                """INSERT INTO scoring.evidence
                       (id, workspace_id, claim_type, evidence_level,
                        collected_at, expires_at)
                       VALUES (%s,%s,'OBSERVED',6, now(), now())""",
                (uuid.uuid4(), WORKSPACE_A),
            )
        assert "check constraint" in str(exc.value).lower()


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
        b_project = repo.create(WORKSPACE_B, "workspace B private project")

        with pytest.raises(NotFoundError):
            repo.get(WORKSPACE_A, b_project.id)

        a_ids = {p.id for p in repo.list(WORKSPACE_A, limit=200)}
        assert b_project.id not in a_ids

    def test_workspace_a_cannot_read_workspace_b_sessions(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        b_project = projects.create(WORKSPACE_B, "B sessions")
        b_session = sessions.create(
            WORKSPACE_B, b_project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )

        with pytest.raises(NotFoundError):
            sessions.get(WORKSPACE_A, b_session.id)
        assert sessions.list_for_project(WORKSPACE_A, b_project.id) == []

    def test_workspace_a_cannot_read_workspace_b_observations(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        opportunities = OpportunityRepository(database)

        b_project = projects.create(WORKSPACE_B, "B observations")
        b_session = sessions.create(
            WORKSPACE_B, b_project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )
        b_opportunity = opportunities.create(
            WORKSPACE_B, "B opportunity", MarketScope.country("FR")
        )
        opportunities.record_observation(
            WORKSPACE_B, b_opportunity, b_session.id, "DISCOVERED", "HYPOTHESIS"
        )

        assert len(opportunities.list_observations(WORKSPACE_B, b_opportunity)) == 1
        # From A: the opportunity is invisible, and so are its observations.
        with pytest.raises(NotFoundError):
            opportunities.get(WORKSPACE_A, b_opportunity)
        assert opportunities.list_observations(WORKSPACE_A, b_opportunity) == []

    def test_session_cannot_be_created_against_another_workspaces_project(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        b_project = projects.create(WORKSPACE_B, "B project for cross check")
        with pytest.raises(NotFoundError):
            sessions.create(
                WORKSPACE_A, b_project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
            )


# ==================================================== lifecycle & immutability


@needs_postgres
class TestResearchSessionLifecycle:
    def test_canonical_initial_status_is_pending(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        project = projects.create(WORKSPACE_A, "lifecycle")
        session = sessions.create(
            WORKSPACE_A, project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )
        assert session.status is ResearchSessionStatus.PENDING

    def test_context_is_canonicalized_before_persistence(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        project = projects.create(WORKSPACE_A, "canonicalization")
        context = ResearchContext.from_json(
            {
                "market_scope": {"type": "MULTI_COUNTRY", "countries": ["us", "FR", "us"]},
                "languages": ["EN", "fr", "en"],
            }
        )
        session = sessions.create(WORKSPACE_A, project.id, context, "1.0.0", "2")
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
        project = projects.create(WORKSPACE_A, "immutability")
        original = ResearchContext.from_json(CONTEXT)
        session = sessions.create(WORKSPACE_A, project.id, original, "1.0.0", "2")

        # Editing the in-memory context produces a NEW object and leaves the
        # persisted snapshot untouched.
        changed = original.with_changes(audience="indie devs")
        assert changed.snapshot_hash() != original.snapshot_hash()

        reread = sessions.get(WORKSPACE_A, session.id)
        assert reread.research_context_hash == original.snapshot_hash()
        assert reread.research_context["audience"] is None

    def test_valid_transition_is_accepted(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        project = projects.create(WORKSPACE_A, "transitions")
        session = sessions.create(
            WORKSPACE_A, project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )
        moved = sessions.transition(WORKSPACE_A, session.id, ResearchSessionStatus.PLANNING)
        assert moved.status is ResearchSessionStatus.PLANNING
        assert moved.started_at is not None

    def test_invalid_transition_is_rejected(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        project = projects.create(WORKSPACE_A, "invalid transitions")
        session = sessions.create(
            WORKSPACE_A, project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )
        # PENDING -> COMPLETED skips the whole lifecycle.
        with pytest.raises(InvalidTransitionError):
            sessions.transition(WORKSPACE_A, session.id, ResearchSessionStatus.COMPLETED)

    def test_terminal_states_are_terminal(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        project = projects.create(WORKSPACE_A, "terminal")
        session = sessions.create(
            WORKSPACE_A, project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )
        sessions.transition(WORKSPACE_A, session.id, ResearchSessionStatus.CANCELLED)
        with pytest.raises(InvalidTransitionError):
            sessions.transition(WORKSPACE_A, session.id, ResearchSessionStatus.PLANNING)

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
            headers=header(WORKSPACE_A),
        )
        assert created.status_code == 201
        project_id = created.json()["id"]

        fetched = api_client.get(
            f"/api/v1/research-projects/{project_id}", headers=header(WORKSPACE_A)
        )
        assert fetched.status_code == 200
        assert fetched.json()["name"] == "API project"

    def test_session_create_persists_snapshot_hash_and_version(self, api_client) -> None:
        project_id = api_client.post(
            "/api/v1/research-projects",
            json={"name": "API session project"},
            headers=header(WORKSPACE_A),
        ).json()["id"]

        created = api_client.post(
            f"/api/v1/research-projects/{project_id}/sessions",
            json={"research_context": {"market_scope": {"type": "COUNTRY", "countries": ["fr"]}}},
            headers=header(WORKSPACE_A),
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
            headers=header(WORKSPACE_A),
        ).json()["id"]

        # COUNTRY with two codes is MULTI_COUNTRY (Ontology V2 §4.4).
        response = api_client.post(
            f"/api/v1/research-projects/{project_id}/sessions",
            json={
                "research_context": {"market_scope": {"type": "COUNTRY", "countries": ["FR", "DE"]}}
            },
            headers=header(WORKSPACE_A),
        )
        assert response.status_code == 422
        assert response.json()["error"] == "contract_violation"

    def test_segment_scope_is_rejected_a12_stays_open(self, api_client) -> None:
        project_id = api_client.post(
            "/api/v1/research-projects",
            json={"name": "a12"},
            headers=header(WORKSPACE_A),
        ).json()["id"]
        response = api_client.post(
            f"/api/v1/research-projects/{project_id}/sessions",
            json={"research_context": {"market_scope": {"type": "SEGMENT"}}},
            headers=header(WORKSPACE_A),
        )
        assert response.status_code == 422
        assert "A-12" in response.json()["detail"]

    def test_no_patch_endpoint_for_research_context(self, api_client) -> None:
        """A new specification means a new session, not a mutated snapshot."""
        project_id = api_client.post(
            "/api/v1/research-projects",
            json={"name": "no patch"},
            headers=header(WORKSPACE_A),
        ).json()["id"]
        session_id = api_client.post(
            f"/api/v1/research-projects/{project_id}/sessions",
            json={"research_context": CONTEXT},
            headers=header(WORKSPACE_A),
        ).json()["id"]

        response = api_client.patch(
            f"/api/v1/research-sessions/{session_id}",
            json={"research_context": {"market_scope": {"type": "GLOBAL"}}},
            headers=header(WORKSPACE_A),
        )
        assert response.status_code in (404, 405)

    def test_cross_workspace_read_is_rejected(self, api_client) -> None:
        project_id = api_client.post(
            "/api/v1/research-projects",
            json={"name": "A only"},
            headers=header(WORKSPACE_A),
        ).json()["id"]

        response = api_client.get(
            f"/api/v1/research-projects/{project_id}", headers=header(WORKSPACE_B)
        )
        assert response.status_code == 404


# ============================================================== tenancy: Redis


@needs_redis
class TestRedisTenantIsolation:
    def test_same_logical_key_differs_physically_per_workspace(self) -> None:
        a = cache_key(str(WORKSPACE_A), "market", "FR")
        b = cache_key(str(WORKSPACE_B), "market", "FR")
        assert a != b
        assert str(WORKSPACE_A) in a and str(WORKSPACE_B) in b

    def test_cache_key_requires_a_workspace(self) -> None:
        with pytest.raises(ContractError):
            cache_key("", "market", "FR")

    def test_tenant_cache_requires_a_workspace(self, redis_client) -> None:
        with pytest.raises(ContractError):
            TenantCache(redis_client, "")

    def test_workspace_a_cannot_read_workspace_b_entry(self, redis_client) -> None:
        a = TenantCache(redis_client, WORKSPACE_A)
        b = TenantCache(redis_client, WORKSPACE_B)
        try:
            b.set("probe", "shared-logical-key", value="workspace-b-secret", ttl_seconds=60)
            assert b.get("probe", "shared-logical-key") == b"workspace-b-secret"
            # Same logical key, different tenant: a miss, not a leak.
            assert a.get("probe", "shared-logical-key") is None
        finally:
            b.delete("probe", "shared-logical-key")

    def test_global_cache_is_a_separate_namespace(self, redis_client) -> None:
        tenant = TenantCache(redis_client, WORKSPACE_A)
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
        store = TenantVectorStore(qdrant, WORKSPACE_A)
        built = store.build_filter()
        assert built["must"][0]["key"] == "workspace_id"
        assert built["must"][0]["match"]["value"] == str(WORKSPACE_A)

    def test_session_scope_is_additive_not_a_replacement(self, qdrant) -> None:
        store = TenantVectorStore(qdrant, WORKSPACE_A)
        built = store.build_filter(research_session_id="sess-1")
        keys = [c["key"] for c in built["must"]]
        assert keys == ["workspace_id", "research_session_id"]

    def test_cross_tenant_write_is_refused(self, qdrant) -> None:
        store = TenantVectorStore(qdrant, WORKSPACE_A)
        with pytest.raises(ContractError):
            store.upsert(
                self.COLLECTION,
                str(uuid.uuid4()),
                [0.1, 0.2, 0.3, 0.4],
                VectorPayload(workspace_id=str(WORKSPACE_B)),
            )

    def test_workspace_a_search_cannot_return_workspace_b_vectors(self, qdrant) -> None:
        a = TenantVectorStore(qdrant, WORKSPACE_A)
        b = TenantVectorStore(qdrant, WORKSPACE_B)

        a_id, b_id = str(uuid.uuid4()), str(uuid.uuid4())
        a.upsert(
            self.COLLECTION,
            a_id,
            [1.0, 0.0, 0.0, 0.0],
            VectorPayload(workspace_id=str(WORKSPACE_A)),
        )
        b.upsert(
            self.COLLECTION,
            b_id,
            [1.0, 0.0, 0.0, 0.0],
            VectorPayload(workspace_id=str(WORKSPACE_B)),
        )

        # Identical vectors: only the tenant filter separates them.
        a_hits = {str(p.id) for p in a.search(self.COLLECTION, [1.0, 0.0, 0.0, 0.0], limit=10)}
        b_hits = {str(p.id) for p in b.search(self.COLLECTION, [1.0, 0.0, 0.0, 0.0], limit=10)}

        assert a_id in a_hits and b_id not in a_hits
        assert b_id in b_hits and a_id not in b_hits
        assert a.count(self.COLLECTION) == 1
        assert b.count(self.COLLECTION) == 1

    def test_delete_workspace_removes_only_that_tenant(self, qdrant) -> None:
        a = TenantVectorStore(qdrant, WORKSPACE_A)
        b = TenantVectorStore(qdrant, WORKSPACE_B)
        a.upsert(
            self.COLLECTION,
            str(uuid.uuid4()),
            [0.0, 1.0, 0.0, 0.0],
            VectorPayload(workspace_id=str(WORKSPACE_A)),
        )
        b.upsert(
            self.COLLECTION,
            str(uuid.uuid4()),
            [0.0, 1.0, 0.0, 0.0],
            VectorPayload(workspace_id=str(WORKSPACE_B)),
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

        project = projects.create(WORKSPACE_A, "rediscovery")
        first = sessions.create(
            WORKSPACE_A, project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )
        second = sessions.create(
            WORKSPACE_A, project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )

        opportunity = opportunities.create(
            WORKSPACE_A, "rediscovered opportunity", MarketScope.country("FR")
        )
        opportunities.record_observation(
            WORKSPACE_A, opportunity, first.id, "DISCOVERED", "HYPOTHESIS"
        )
        opportunities.record_observation(
            WORKSPACE_A, opportunity, second.id, "CORROBORATED", "INFERRED"
        )

        observations = opportunities.list_observations(WORKSPACE_A, opportunity)
        assert len(observations) == 2
        assert {o["observation_kind"] for o in observations} == {"DISCOVERED", "CORROBORATED"}

    def test_observation_kind_comes_from_the_authoritative_set(self, database) -> None:
        projects = ResearchProjectRepository(database)
        sessions = ResearchSessionRepository(database)
        opportunities = OpportunityRepository(database)
        project = projects.create(WORKSPACE_A, "kinds")
        session = sessions.create(
            WORKSPACE_A, project.id, ResearchContext.from_json(CONTEXT), "1.0.0", "2"
        )
        opportunity = opportunities.create(WORKSPACE_A, "kinds", MarketScope.global_())
        with pytest.raises(ContractError):
            opportunities.record_observation(
                WORKSPACE_A, opportunity, session.id, "SCORED", "OBSERVED"
            )

    def test_no_identity_resolution_helper_exists(self) -> None:
        """§35: deciding two opportunities are identical stays an open problem."""
        forbidden = {"find_similar", "match_by_title", "resolve_identity", "deduplicate"}
        assert forbidden.isdisjoint(dir(OpportunityRepository))
