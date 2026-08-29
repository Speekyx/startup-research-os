-- =============================================================================
-- 0003_row_level_security.sql -- PostgreSQL RLS as defence in depth
--
-- Mission 0.4 §3-§7. Governed by ADR-005 (§Future row-level security) and
-- ADR-012.
--
-- ADR-005 designed for RLS and Mission 0.3 deliberately did not enable it, so
-- isolation has rested on one layer: the repository `WHERE workspace_id = %s`.
-- That layer is good and stays mandatory. It is also one forgotten clause away
-- from a cross-tenant read, and a forgotten clause is invisible in review
-- precisely because the query still looks correct.
--
-- This migration adds the second layer. After it, a leak requires bypassing
-- BOTH the repository filter AND a database policy.
--
--   Layer 1  explicit repository tenant filtering   (unchanged, still required)
--   Layer 2  PostgreSQL row-level security          (this migration)
--
-- RLS is NOT a licence to drop layer 1. Relying on RLS alone means every
-- application bug is a database-enforced 404 instead of a leak, which sounds
-- fine until a report is written with a service role. Relying on filtering
-- alone means one missing WHERE is a leak. Both, or neither is trustworthy.
--
-- Forward-only. Never edited after it has been applied anywhere.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Transaction-local tenant context
--
-- The context lives in a custom GUC, `app.workspace_id`, set with SET LOCAL so
-- it is bound to the TRANSACTION and disappears when the transaction ends.
--
-- Transaction-local rather than session-local is the whole design. Connections
-- are pooled (ADR-011): a session-level SET would survive the connection's
-- return to the pool and the next borrower would inherit the previous tenant's
-- context. That is a cross-tenant read with no bug in any query.
--
-- The helper below FAILS CLOSED three ways:
--
--   * GUC never set        -> current_setting(..., true) is NULL -> NULL
--   * GUC set to ''        -> does not match the pattern         -> NULL
--   * GUC set to garbage   -> does not match the pattern         -> NULL
--
-- and `workspace_id = NULL` is NULL, which is not TRUE, so no row passes. The
-- regex guard rather than a bare cast is deliberate: a bare `::uuid` on a
-- malformed value raises, and an error path is a worse failure mode than an
-- empty result when the alternative is a policy that cannot be evaluated.
--
-- There is deliberately NO fallback workspace. ADR-005: a missing workspace_id
-- is an error in every environment, including local development.
-- -----------------------------------------------------------------------------
CREATE FUNCTION core.current_workspace_id() RETURNS uuid
    LANGUAGE sql
    STABLE
    -- Pinned search_path: the body must not resolve through a caller-supplied
    -- one, which is the standard hardening for a function used inside a policy.
    SET search_path = pg_catalog
AS $$
    SELECT CASE
        WHEN current_setting('app.workspace_id', true) ~
             '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        THEN current_setting('app.workspace_id', true)::uuid
        ELSE NULL
    END
$$;

COMMENT ON FUNCTION core.current_workspace_id() IS
    'Transaction-local tenant context for RLS. Returns NULL when unset, empty '
    'or malformed, so every tenant policy fails closed. Set with '
    'SET LOCAL app.workspace_id — never SET, which would survive into the next '
    'borrower of a pooled connection.';

-- -----------------------------------------------------------------------------
-- 2. The application role
--
-- RLS is bypassed by two kinds of role: a SUPERUSER, and the table OWNER
-- (unless the table also has FORCE ROW LEVEL SECURITY). The local development
-- stack connects as the database superuser, so enabling policies without
-- addressing that would produce tests that pass while proving nothing.
--
-- `sros_app` is NOLOGIN, NOSUPERUSER and explicitly NOBYPASSRLS. The runtime
-- assumes it per transaction with SET LOCAL ROLE, so policies apply even when
-- the underlying connection belongs to a privileged role.
--
-- NOLOGIN is deliberate: no password exists, therefore no password can be
-- committed in a migration. A dedicated LOGIN role with its own credential is
-- the production path, and it is deployment configuration rather than schema —
-- see ADR-012 §Deployment.
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sros_app') THEN
        CREATE ROLE sros_app NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
    END IF;
END
$$;

COMMENT ON ROLE sros_app IS
    'Runtime role for tenant-scoped access. NOBYPASSRLS. Assumed per '
    'transaction via SET LOCAL ROLE (ADR-012).';

GRANT USAGE ON SCHEMA core, registry, research, acquisition, nlp, scoring TO sros_app;

-- Global reference data: readable, never writable at runtime. Registry contents
-- and the source registry are administered by migrations and seeds, and D-07
-- keeps the source registry a stub.
GRANT SELECT ON core.users, core.workspaces, core.workspace_memberships TO sros_app;
GRANT SELECT ON registry.registry_entries, registry.sources TO sros_app;
-- Readable so a running service can report which schema version it is speaking
-- to. Writable only by the migration runner, which does not assume this role.
GRANT SELECT ON core.schema_migrations TO sros_app;

-- Tenant-scoped data: full DML, constrained by the policies below.
GRANT SELECT, INSERT, UPDATE, DELETE
    ON ALL TABLES IN SCHEMA research, acquisition, nlp, scoring TO sros_app;

-- Future tables created by this owner inherit the same grants, so a new table
-- is not silently unreachable by the runtime after the next migration.
ALTER DEFAULT PRIVILEGES IN SCHEMA research, acquisition, nlp, scoring
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sros_app;

-- Membership so the connecting role may SET ROLE. A superuser needs no grant;
-- a non-superuser production owner does.
DO $$
BEGIN
    EXECUTE format('GRANT sros_app TO %I', current_user);
END
$$;

-- -----------------------------------------------------------------------------
-- 3. Policies
--
-- One policy per tenant-scoped table, FOR ALL, with the same predicate in USING
-- and WITH CHECK:
--
--   USING       what may be read, updated or deleted
--   WITH CHECK  what may be written
--
-- Both matter. USING alone would let a workspace INSERT a row tagged with
-- another workspace's id — visible to nobody who wrote it, and to exactly the
-- wrong tenant.
--
-- FORCE ROW LEVEL SECURITY is applied alongside ENABLE so that the table owner
-- is also constrained. ENABLE alone exempts the owner, and in a deployment
-- where the application connects as the owner that exemption is the entire
-- protection, silently absent.
-- -----------------------------------------------------------------------------

-- research ---------------------------------------------------------------
ALTER TABLE research.research_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.research_projects FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.research_projects
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE research.research_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.research_sessions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.research_sessions
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE research.research_gaps ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.research_gaps FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.research_gaps
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE research.opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.opportunities FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.opportunities
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE research.opportunity_session_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.opportunity_session_observations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.opportunity_session_observations
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE research.research_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.research_plans FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.research_plans
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE research.research_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.research_jobs FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.research_jobs
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE research.research_job_dependencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.research_job_dependencies FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.research_job_dependencies
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE research.session_budget_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.session_budget_entries FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.session_budget_entries
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE research.research_completeness_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.research_completeness_records FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.research_completeness_records
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

-- acquisition ------------------------------------------------------------
ALTER TABLE acquisition.raw_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE acquisition.raw_records FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON acquisition.raw_records
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE acquisition.normalized_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE acquisition.normalized_records FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON acquisition.normalized_records
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

-- nlp --------------------------------------------------------------------
ALTER TABLE nlp.signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE nlp.signals FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON nlp.signals
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE nlp.embedding_provenance ENABLE ROW LEVEL SECURITY;
ALTER TABLE nlp.embedding_provenance FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON nlp.embedding_provenance
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

-- scoring ----------------------------------------------------------------
-- The table stores RAW evidence metadata only. D-03 is unresolved and this
-- migration adds nothing to that: RLS governs who may read a row, never how
-- rows combine.
ALTER TABLE scoring.evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE scoring.evidence FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON scoring.evidence
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

-- -----------------------------------------------------------------------------
-- 4. Tables that deliberately receive NO policy
--
-- Applying a tenant policy to a table that is not tenant-scoped is worse than
-- leaving it alone: it makes the schema look uniformly protected while the rows
-- that matter are unreachable or the policy is a no-op nobody re-reads.
--
--   core.schema_migrations       operational ledger, no tenant dimension
--   core.users                   a principal is NOT a tenant (ADR-005). A user
--                                may belong to several workspaces
--   core.workspaces              the tenant list itself. A policy here would
--                                have to be evaluated before a tenant context
--                                exists, which is a circular requirement
--   core.workspace_memberships   carries workspace_id, and still gets no
--                                policy: this is the table that will DEFINE
--                                access once authentication exists, and
--                                "which workspaces may this user enter?" is
--                                asked before any workspace is chosen. Gating
--                                it on the answer makes the question
--                                unanswerable. It is protected by being
--                                read-only to sros_app
--   registry.registry_entries    global taxonomy rows (Ontology V2 §14.3)
--   registry.sources             global source registry, D-07
--
-- Reference data being globally readable is the intended design, not an
-- oversight: a taxonomy that differed per tenant would make classifications
-- incomparable across workspaces.
-- -----------------------------------------------------------------------------
