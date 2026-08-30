"""Row-level security: the second isolation layer.

Mission 0.4 §6 and §35. Governed by ADR-012.

Every test here uses **two workspaces**. A tenancy suite with one workspace
cannot detect a missing tenant filter, because there is nothing for the filter
to exclude (ADR-005).

Both are this module's own -- P and Q, created before each test and dropped
after it by `own_workspaces` below -- rather than the seeded pair. Against a
seeded workspace `test_a_delete_cannot_reach_another_workspace` is not a test
but a demolition: the DELETE with no WHERE that the test exists to survive
takes every project in that workspace with it, and every session that cascades
from one.

The test that justifies the whole migration is
`TestDirectSqlWithoutWorkspaceFilter`. Every other layer in this system depends
on someone remembering something: the repository filter, the cache key prefix,
the vector-store filter. That one proves the database refuses to serve another
tenant's rows to a query that asked for everything.
"""

from __future__ import annotations

import uuid

import pytest
from sros_gateway.db.pool import Database, TenantScopeError
from sros_gateway.db.repositories import ResearchProjectRepository

from .conftest import DATABASE_URL, WORKSPACE_RLS_P, WORKSPACE_RLS_Q, needs_postgres

TENANT_TABLES = [
    "research.research_projects",
    "research.research_sessions",
    "research.research_gaps",
    "research.opportunities",
    "research.opportunity_session_observations",
    "research.research_plans",
    "research.research_jobs",
    "research.research_job_dependencies",
    "research.session_budget_entries",
    "research.research_completeness_records",
    "acquisition.raw_records",
    "acquisition.normalized_records",
    "nlp.signals",
    "nlp.embedding_provenance",
    "scoring.evidence",
    # Added in Mission 1.2. The aggregation unit and its provenance groups are
    # tenant data like everything else above; a claim visible across workspaces
    # would leak what another tenant is researching, in their own words.
    "research.claims",
    "research.claim_revisions",
    "research.claim_session_observations",
    "scoring.evidence_independence_groups",
    # Added in Mission 1.11. A signal's lineage names which observations a
    # workspace derived from, which is as much a statement about what a tenant
    # is researching as the signal itself.
    "nlp.signal_inputs",
    # Added in Mission 1.11.1. A derivation run names which observations a
    # workspace considered, which says as much about what a tenant is
    # researching as the signals it produced.
    "nlp.signal_derivation_runs",
]

# Deliberately NOT policy-bearing. Listed here so that adding a policy to one of
# them fails a test rather than passing silently, and so the reason survives in
# a place someone will read.
GLOBAL_TABLES = [
    "core.users",
    "core.workspaces",
    "core.workspace_memberships",
    "core.schema_migrations",
    "registry.registry_entries",
    "registry.sources",
]


@pytest.fixture(autouse=True)
def own_workspaces(rls_workspaces) -> None:
    """Every test in this module runs in workspaces of its own.

    Autouse, and it hands nothing back, because no test here needs to be handed
    a workspace: they name WORKSPACE_RLS_P and WORKSPACE_RLS_Q directly, so
    what they need is not a value but a guarantee -- that the two exist when a
    test starts and are gone when it ends. Requesting it by name in thirty
    signatures would state the same thing thirty times and leave the
    thirty-first test writing into a seeded workspace.
    """


@pytest.fixture
def probe_projects(database: Database, own_workspaces: None) -> tuple[uuid.UUID, uuid.UUID]:
    """One project in each workspace, created through the repository.

    `own_workspaces` is named here as well as being autouse, because this
    fixture writes rows into the workspaces it creates and so must be ordered
    after it rather than merely alongside it.
    """
    repo = ResearchProjectRepository(database)
    a = repo.create(WORKSPACE_RLS_P, f"rls-p-{uuid.uuid4().hex[:8]}")
    b = repo.create(WORKSPACE_RLS_Q, f"rls-q-{uuid.uuid4().hex[:8]}")
    return a.id, b.id


# ==================================================== the policies are present


@needs_postgres
class TestPolicyCoverage:
    def test_every_tenant_table_has_row_security_enabled_and_forced(
        self, database: Database
    ) -> None:
        """ENABLE alone exempts the table owner, which in a deployment where the
        application connects as the owner is the entire protection, silently
        absent. FORCE is what closes that."""
        with database.privileged_transaction() as conn:
            rows = conn.execute(
                """SELECT n.nspname || '.' || c.relname, c.relrowsecurity, c.relforcerowsecurity
                   FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                   WHERE n.nspname IN ('core','registry','research','acquisition','nlp','scoring')
                     AND c.relkind = 'r'"""
            ).fetchall()
        state = {name: (enabled, forced) for name, enabled, forced in rows}

        for table in TENANT_TABLES:
            assert state.get(table) == (True, True), f"{table} is not ENABLE+FORCE RLS"

    def test_global_reference_tables_carry_no_tenant_policy(self, database: Database) -> None:
        """A tenant policy on a global table is worse than no policy: it makes
        the schema look uniformly protected while the rows nobody can reach are
        the shared taxonomy every workspace needs."""
        with database.privileged_transaction() as conn:
            rows = conn.execute(
                """SELECT n.nspname || '.' || c.relname, c.relrowsecurity
                   FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                   WHERE n.nspname IN ('core','registry') AND c.relkind = 'r'"""
            ).fetchall()
        for name, enabled in rows:
            if name in GLOBAL_TABLES:
                assert enabled is False, f"{name} is global reference data and must not carry RLS"

    def test_every_tenant_table_has_exactly_one_policy(self, database: Database) -> None:
        with database.privileged_transaction() as conn:
            rows = conn.execute(
                """SELECT n.nspname || '.' || c.relname, p.polname
                   FROM pg_policy p
                   JOIN pg_class c ON c.oid = p.polrelid
                   JOIN pg_namespace n ON n.oid = c.relnamespace"""
            ).fetchall()
        by_table: dict[str, list[str]] = {}
        for table, policy in rows:
            by_table.setdefault(table, []).append(policy)

        assert sorted(by_table) == sorted(TENANT_TABLES)
        for table, policies in by_table.items():
            assert policies == ["tenant_isolation"], f"{table} has unexpected policies {policies}"

    def test_the_application_role_cannot_bypass_row_security(self, database: Database) -> None:
        """NOBYPASSRLS and NOSUPERUSER are the two attributes that make the
        policies mean anything. A role with either would satisfy every other
        test in this file while enforcing nothing."""
        with database.privileged_transaction() as conn:
            row = conn.execute(
                "SELECT rolbypassrls, rolsuper, rolcanlogin FROM pg_roles WHERE rolname = %s",
                (database.app_role,),
            ).fetchone()
        assert row is not None, f"role {database.app_role} does not exist"
        assert row[0] is False, "the application role must not have BYPASSRLS"
        assert row[1] is False, "the application role must not be a superuser"
        assert row[2] is False, (
            "the application role must not be a login role (no committed secret)"
        )


# ================================================================== isolation


@needs_postgres
class TestTenantIsolation:
    def test_workspace_a_sees_its_own_rows(
        self, database: Database, probe_projects: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        project_a, _ = probe_projects
        with database.tenant_transaction(WORKSPACE_RLS_P) as conn:
            ids = {r[0] for r in conn.execute("SELECT id FROM research.research_projects")}
        assert project_a in ids

    def test_workspace_a_cannot_see_workspace_b_rows(
        self, database: Database, probe_projects: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        _, project_b = probe_projects
        with database.tenant_transaction(WORKSPACE_RLS_P) as conn:
            ids = {r[0] for r in conn.execute("SELECT id FROM research.research_projects")}
        assert project_b not in ids

    def test_workspace_b_cannot_see_workspace_a_rows(
        self, database: Database, probe_projects: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        project_a, _ = probe_projects
        with database.tenant_transaction(WORKSPACE_RLS_Q) as conn:
            ids = {r[0] for r in conn.execute("SELECT id FROM research.research_projects")}
        assert project_a not in ids

    def test_the_two_workspaces_see_disjoint_row_sets(
        self, database: Database, probe_projects: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        with database.tenant_transaction(WORKSPACE_RLS_P) as conn:
            seen_a = {r[0] for r in conn.execute("SELECT id FROM research.research_projects")}
        with database.tenant_transaction(WORKSPACE_RLS_Q) as conn:
            seen_b = {r[0] for r in conn.execute("SELECT id FROM research.research_projects")}
        assert seen_a & seen_b == set()
        assert seen_a and seen_b, "both workspaces must have rows for this to mean anything"

    def test_a_cross_tenant_write_is_refused_by_the_policy(self, database: Database) -> None:
        """USING without WITH CHECK would allow a workspace to INSERT a row
        tagged with another workspace's id: invisible to whoever wrote it, and
        visible to exactly the wrong tenant."""
        with pytest.raises(Exception) as exc, database.tenant_transaction(WORKSPACE_RLS_P) as conn:
            conn.execute(
                "INSERT INTO research.research_projects (id, workspace_id, name) "
                "VALUES (%s, %s, 'cross-tenant write')",
                (uuid.uuid4(), WORKSPACE_RLS_Q),
            )
        assert "row-level security" in str(exc.value).lower()

    def test_an_update_cannot_move_a_row_into_another_workspace(
        self, database: Database, probe_projects: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        project_a, _ = probe_projects
        with pytest.raises(Exception) as exc, database.tenant_transaction(WORKSPACE_RLS_P) as conn:
            conn.execute(
                "UPDATE research.research_projects SET workspace_id = %s WHERE id = %s",
                (WORKSPACE_RLS_Q, project_a),
            )
        assert "row-level security" in str(exc.value).lower()

    def test_a_delete_cannot_reach_another_workspace(
        self, database: Database, probe_projects: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        """A DELETE with no WHERE, from P. Q's row must survive.

        The statement stays unscoped on purpose: a WHERE clause here would
        make the test pass while proving nothing, since the missing tenant
        filter IS what the policy is being asked to survive. What moved is
        the workspace, not the query -- P is this module's own, so the only
        rows an unscoped DELETE can reach are rows the fixture created."""
        _, project_b = probe_projects
        with database.tenant_transaction(WORKSPACE_RLS_P) as conn:
            conn.execute("DELETE FROM research.research_projects")
        with database.tenant_transaction(WORKSPACE_RLS_Q) as conn:
            still_there = conn.execute(
                "SELECT 1 FROM research.research_projects WHERE id = %s", (project_b,)
            ).fetchone()
        assert still_there is not None


# ====================================== the reason RLS exists at all (§6, §7)


@needs_postgres
class TestDirectSqlWithoutWorkspaceFilter:
    """Queries that forget the tenant filter entirely.

    Layer 1 cannot help here by construction: the WHERE clause is what is
    missing. If these pass, the database is doing the work.
    """

    def test_a_select_with_no_where_clause_returns_only_the_current_tenant(
        self, database: Database, probe_projects: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        project_a, project_b = probe_projects
        with database.tenant_transaction(WORKSPACE_RLS_P) as conn:
            rows = conn.execute(
                "SELECT id, workspace_id FROM research.research_projects"
            ).fetchall()
        workspaces = {r[1] for r in rows}
        assert workspaces == {WORKSPACE_RLS_P}
        assert project_a in {r[0] for r in rows}
        assert project_b not in {r[0] for r in rows}

    def test_an_unfiltered_count_is_a_per_tenant_count(
        self, database: Database, probe_projects: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        """The aggregate case from ADR-005 §Data isolation risks: cross-tenant
        totals presented as one tenant's data."""
        with database.privileged_transaction() as conn:
            everything = conn.execute("SELECT count(*) FROM research.research_projects").fetchone()
        with database.tenant_transaction(WORKSPACE_RLS_P) as conn:
            tenant_view = conn.execute("SELECT count(*) FROM research.research_projects").fetchone()
        assert everything is not None and tenant_view is not None
        assert tenant_view[0] < everything[0], (
            "an unfiltered count under a tenant context must not equal the global count; "
            "if it does, the policy is not being applied"
        )

    def test_an_unfiltered_join_cannot_cross_the_tenant_boundary(self, database: Database) -> None:
        """A join between two tenant tables with no workspace predicate at all."""
        with database.tenant_transaction(WORKSPACE_RLS_P) as conn:
            rows = conn.execute(
                """SELECT p.workspace_id, s.workspace_id
                   FROM research.research_projects p
                   LEFT JOIN research.research_sessions s ON s.project_id = p.id"""
            ).fetchall()
        for project_ws, session_ws in rows:
            assert project_ws == WORKSPACE_RLS_P
            assert session_ws is None or session_ws == WORKSPACE_RLS_P

    @pytest.mark.parametrize("table", TENANT_TABLES)
    def test_every_tenant_table_is_empty_without_a_tenant_context(
        self, database: Database, table: str
    ) -> None:
        """Fail closed, on every table, not just the ones with a repository.

        `connection()` assumes the application role and sets no workspace, which
        is the state a forgotten `tenant_transaction` would produce.
        """
        with database.connection() as conn:
            # The table name comes from this module's own constant list, never
            # from input. Parameterising an identifier is not possible in SQL.
            count = conn.execute(f"SELECT count(*) FROM {table}").fetchone()  # noqa: S608
        assert count is not None
        assert count[0] == 0, f"{table} returned rows with no tenant context"


# ======================================================= pooled-connection leak


@needs_postgres
class TestPooledConnectionContext:
    """The failure mode that a session-level SET would have created.

    A single-connection pool guarantees the same physical connection is reused,
    which is what makes these assertions meaningful rather than lucky.
    """

    def test_context_does_not_survive_into_the_next_borrower(self) -> None:
        db = Database(DATABASE_URL, min_size=1, max_size=1)
        db.open()
        try:
            with db.tenant_transaction(WORKSPACE_RLS_P) as conn:
                first = conn.execute("SELECT core.current_workspace_id()").fetchone()
            # Same connection, no tenant context requested this time.
            with db.connection() as conn:
                after = conn.execute("SELECT core.current_workspace_id()").fetchone()
            assert first is not None and after is not None
            assert first[0] == WORKSPACE_RLS_P
            assert after[0] is None, "tenant context leaked into the next use of the connection"
        finally:
            db.close()

    def test_a_second_tenant_replaces_rather_than_inherits(self) -> None:
        db = Database(DATABASE_URL, min_size=1, max_size=1)
        db.open()
        try:
            with db.tenant_transaction(WORKSPACE_RLS_P) as conn:
                conn.execute("SELECT 1")
            with db.tenant_transaction(WORKSPACE_RLS_Q) as conn:
                seen = conn.execute("SELECT core.current_workspace_id()").fetchone()
                rows = conn.execute(
                    "SELECT DISTINCT workspace_id FROM research.research_projects"
                ).fetchall()
            assert seen is not None and seen[0] == WORKSPACE_RLS_Q
            assert {r[0] for r in rows} <= {WORKSPACE_RLS_Q}
        finally:
            db.close()

    def test_the_role_is_also_transaction_local(self) -> None:
        db = Database(DATABASE_URL, min_size=1, max_size=1)
        db.open()
        try:
            with db.tenant_transaction(WORKSPACE_RLS_P) as conn:
                during = conn.execute("SELECT current_user").fetchone()
            with db.privileged_transaction() as conn:
                after = conn.execute("SELECT current_user").fetchone()
            assert during is not None and after is not None
            assert during[0] == "sros_app"
            assert after[0] != "sros_app", "SET LOCAL ROLE leaked past its transaction"
        finally:
            db.close()

    def test_a_rolled_back_transaction_also_clears_the_context(self) -> None:
        db = Database(DATABASE_URL, min_size=1, max_size=1)
        db.open()
        try:
            with (  # noqa: PT012 - the raise inside the block IS the fixture
                pytest.raises(RuntimeError),
                db.tenant_transaction(WORKSPACE_RLS_P) as conn,
            ):
                conn.execute("SELECT 1")
                raise RuntimeError("forced rollback")
            with db.connection() as conn:
                after = conn.execute("SELECT core.current_workspace_id()").fetchone()
            assert after is not None and after[0] is None
        finally:
            db.close()


# ============================================== missing / malformed context


@needs_postgres
class TestFailsClosed:
    def test_a_missing_workspace_is_refused_before_a_statement_is_issued(
        self, database: Database
    ) -> None:
        """Raising beats returning nothing. An empty result set from a missing
        tenant is safe and silent, and silence is what lets the bug survive."""
        for missing in (None, ""):
            with (
                pytest.raises(TenantScopeError),
                database.tenant_transaction(missing) as conn,  # type: ignore[arg-type]
            ):
                conn.execute("SELECT 1")

    def test_a_malformed_workspace_is_refused(self, database: Database) -> None:
        with (
            pytest.raises(TenantScopeError),
            database.tenant_transaction("not-a-uuid") as conn,
        ):
            conn.execute("SELECT 1")

    def test_an_empty_tenant_guc_yields_no_context_rather_than_an_error(
        self, database: Database
    ) -> None:
        """Defence in depth for the case the wrapper does not catch: something
        setting the GUC directly to a value the helper cannot parse. The policy
        must evaluate to "no rows", never raise inside a query plan."""
        for raw in ("", "not-a-uuid", "00000000-0000-4000-8000"):
            with database.privileged_transaction() as conn:
                conn.execute("SELECT set_config('app.workspace_id', %s, true)", (raw,))
                resolved = conn.execute("SELECT core.current_workspace_id()").fetchone()
            assert resolved is not None
            assert resolved[0] is None, f"{raw!r} must resolve to NULL, not to a workspace"

    def test_an_insert_without_a_tenant_context_is_refused(self, database: Database) -> None:
        with pytest.raises(Exception) as exc, database.transaction() as conn:
            conn.execute(
                "INSERT INTO research.research_projects (id, workspace_id, name) "
                "VALUES (%s, %s, 'no context')",
                (uuid.uuid4(), WORKSPACE_RLS_P),
            )
        assert "row-level security" in str(exc.value).lower()

    def test_there_is_no_fallback_workspace(self, database: Database) -> None:
        """A policy written with COALESCE to a default would pass every
        isolation test above while making one workspace universally visible."""
        with database.privileged_transaction() as conn:
            row = conn.execute(
                "SELECT pg_get_expr(polqual, polrelid) FROM pg_policy p "
                "JOIN pg_class c ON c.oid = p.polrelid "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'research' AND c.relname = 'research_projects'"
            ).fetchone()
        assert row is not None
        expression = row[0].lower()
        assert "coalesce" not in expression
        assert "current_workspace_id" in expression


# ================================================ layers 1 and 2 agree (§7)


@needs_postgres
class TestRepositoryAndPolicyAgree:
    def test_the_repository_filter_and_the_policy_return_the_same_rows(
        self, database: Database, probe_projects: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        repo = ResearchProjectRepository(database)
        via_repository = {row.id for row in repo.list(WORKSPACE_RLS_P, limit=200)}
        with database.tenant_transaction(WORKSPACE_RLS_P) as conn:
            via_policy = {
                r[0]
                for r in conn.execute(
                    "SELECT id FROM research.research_projects ORDER BY created_at DESC LIMIT 200"
                )
            }
        assert via_repository == via_policy

    def test_the_repository_still_filters_explicitly(self) -> None:
        """Layer 1 must not be deleted because layer 2 exists.

        This reads the source rather than the behaviour on purpose: the
        behaviour is now indistinguishable with RLS on, which is exactly how a
        removed filter would go unnoticed until someone ran a report with a
        privileged role.
        """
        import inspect

        from sros_gateway.db import repositories

        source = inspect.getsource(repositories)
        tenant_methods = source[source.index("class ResearchProjectRepository") :]
        assert tenant_methods.count("workspace_id = %s") >= 6, (
            "tenant-scoped queries must keep their explicit workspace filter (ADR-012 layer 1)"
        )

    def test_a_repository_read_for_another_workspace_finds_nothing(
        self, database: Database, probe_projects: tuple[uuid.UUID, uuid.UUID]
    ) -> None:
        from sros_gateway.db.repositories import NotFoundError

        _, project_b = probe_projects
        repo = ResearchProjectRepository(database)
        with pytest.raises(NotFoundError):
            repo.get(WORKSPACE_RLS_P, project_b)
