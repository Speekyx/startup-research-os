-- =============================================================================
-- 0002_orchestration.sql -- Research orchestration persistence
--
-- Mission 0.4 §8-§17. Owned by `services/research-orchestrator`
-- (service-boundaries.md §5: research_plan, task_ledger, research_gap).
--
-- Why these tables exist at all: ADR-004 gives at-least-once delivery over a
-- Redis broker, and ADR-008 states Redis is never canonical. Progress that
-- lives only in Celery is therefore progress that a broker restart erases. A
-- session must survive a worker crash, a process restart and a duplicate
-- delivery (§13), so execution state is persisted here and Redis is treated as
-- transport, never as truth.
--
-- Invariants preserved from ADR-008, enforced by
-- infrastructure/scripts/validate_schema.py:
--
--   * every tenant-scoped table carries workspace_id UUID NOT NULL
--   * composite indexes lead with workspace_id
--   * NO PostgreSQL ENUM type (Ontology V2 §14.3); closed sets are TEXT + CHECK
--   * NO evidence-aggregation column anywhere (D-03 stays blocked)
--   * a `*_score` column carries a 0-100 CHECK (scoring-framework-v1.1.md §4.1)
--
-- Forward-only. Never edited after it has been applied anywhere.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- research.research_plans -- the ResearchExecutionPlan (§10)
--
-- An execution structure, NOT a new ontology entity. Ontology V2 does not
-- define a plan, and this table does not invent domain semantics: it records
-- what the orchestrator intended to run, so that "intended vs covered" is
-- answerable and Research Completeness has something to measure against.
--
-- Plans are versioned rather than mutated. A superseded plan is what makes it
-- possible to say why a session did less than a later plan would have.
-- -----------------------------------------------------------------------------
CREATE TABLE research.research_plans (
    id                      UUID        PRIMARY KEY,
    workspace_id            UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    research_session_id     UUID        NOT NULL REFERENCES research.research_sessions (id) ON DELETE CASCADE,

    plan_version            INTEGER     NOT NULL DEFAULT 1,
    status                  TEXT        NOT NULL DEFAULT 'ACTIVE',

    -- Capabilities the planner could not schedule, and why. D-07 (sources) and
    -- D-03 (scoring) are unresolved, so a plan that pretended to cover them
    -- would be a lie told to Research Completeness.
    blocked_capabilities    TEXT[]      NOT NULL DEFAULT '{}',
    blocked_reasons         JSONB       NOT NULL DEFAULT '{}',

    -- Sum of the estimated cost of the plan's jobs at planning time. An
    -- estimate, explicitly: real cost is recorded per job as it is consumed.
    estimated_cost_units    NUMERIC(18, 6) NOT NULL DEFAULT 0,

    planner_version         TEXT        NOT NULL,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Operational retention (data-retention-policy-v1.md §2.5: session state
    -- and plans follow §2.2). Computed at write time so the decision stays
    -- auditable after the policy changes.
    expires_at              TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '365 days'),

    CONSTRAINT research_plans_status_check
        CHECK (status IN ('ACTIVE', 'SUPERSEDED')),
    CONSTRAINT research_plans_version_check
        CHECK (plan_version >= 1),
    CONSTRAINT research_plans_cost_nonnegative_check
        CHECK (estimated_cost_units >= 0),
    CONSTRAINT research_plans_version_unique
        UNIQUE (workspace_id, research_session_id, plan_version)
);

CREATE INDEX idx_research_plans_session
    ON research.research_plans (workspace_id, research_session_id, plan_version DESC);

CREATE INDEX idx_research_plans_expiry
    ON research.research_plans (expires_at);

-- -----------------------------------------------------------------------------
-- research.research_jobs -- the task ledger (§11)
--
-- A GENERIC job description. It is deliberately not tied to a collector, a
-- model or an analysis stage: `job_type` is a string and `payload` is opaque
-- JSONB, so adding a job class later is an INSERT rather than a migration.
--
-- `idempotency_key` is unique per workspace. That is the whole point: ADR-004
-- delivery is at-least-once, and a read-then-write duplicate check without a
-- unique constraint is a race with a longer window. The database absorbs the
-- duplicate.
-- -----------------------------------------------------------------------------
CREATE TABLE research.research_jobs (
    id                      UUID        PRIMARY KEY,
    workspace_id            UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    research_session_id     UUID        NOT NULL REFERENCES research.research_sessions (id) ON DELETE CASCADE,
    research_plan_id        UUID        REFERENCES research.research_plans (id) ON DELETE SET NULL,

    job_type                TEXT        NOT NULL,
    queue                   TEXT        NOT NULL,
    payload                 JSONB       NOT NULL DEFAULT '{}',

    -- Correlation survives the HTTP -> queue -> worker hop (ADR-004, ADR-005).
    correlation_id          TEXT        NOT NULL,
    idempotency_key         TEXT        NOT NULL,

    status                  TEXT        NOT NULL DEFAULT 'PENDING',
    -- Why a job will never run. Set for BLOCKED and for CANCELLED, so a plan
    -- can explain a gap instead of silently omitting work.
    blocked_reason          TEXT,
    last_error              TEXT,

    attempts                INTEGER     NOT NULL DEFAULT 0,
    max_attempts            INTEGER     NOT NULL DEFAULT 1,

    -- Provider-agnostic cost units (ADR-006). No product price is invented
    -- here, and no provider tariff is stored in a business table.
    estimated_cost_units    NUMERIC(18, 6) NOT NULL DEFAULT 0,
    actual_cost_units       NUMERIC(18, 6) NOT NULL DEFAULT 0,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    dispatched_at           TIMESTAMPTZ,
    started_at              TIMESTAMPTZ,
    finished_at             TIMESTAMPTZ,
    -- Operational data (data-retention-policy-v1.md §2.5: job records, 90 days).
    expires_at              TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '90 days'),

    CONSTRAINT research_jobs_status_check
        CHECK (status IN ('PENDING', 'READY', 'DISPATCHED', 'RUNNING',
                          'SUCCEEDED', 'FAILED', 'BLOCKED', 'CANCELLED')),
    CONSTRAINT research_jobs_attempts_check
        CHECK (attempts >= 0 AND max_attempts >= 1),
    CONSTRAINT research_jobs_cost_nonnegative_check
        CHECK (estimated_cost_units >= 0 AND actual_cost_units >= 0),
    -- A blocked job must say why. An unexplained block is indistinguishable
    -- from work that was quietly dropped.
    CONSTRAINT research_jobs_blocked_needs_reason_check
        CHECK (status <> 'BLOCKED' OR blocked_reason IS NOT NULL),
    CONSTRAINT research_jobs_idempotency_unique
        UNIQUE (workspace_id, idempotency_key)
);

CREATE INDEX idx_research_jobs_session_status
    ON research.research_jobs (workspace_id, research_session_id, status);

CREATE INDEX idx_research_jobs_plan
    ON research.research_jobs (workspace_id, research_plan_id);

CREATE INDEX idx_research_jobs_expiry
    ON research.research_jobs (expires_at);

-- -----------------------------------------------------------------------------
-- research.research_job_dependencies -- explicit DAG edges (§12)
--
-- A small, explicit orchestration layer rather than Airflow or Temporal. The
-- system already has Celery; adding a workflow engine to express "B after A"
-- would buy a scheduler, a UI and a second operational surface for a
-- dependency list that fits in one table.
--
-- The point at which a workflow engine becomes justified is recorded in
-- services/research-orchestrator/README.md.
-- -----------------------------------------------------------------------------
CREATE TABLE research.research_job_dependencies (
    workspace_id            UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    job_id                  UUID        NOT NULL REFERENCES research.research_jobs (id) ON DELETE CASCADE,
    depends_on_job_id       UUID        NOT NULL REFERENCES research.research_jobs (id) ON DELETE CASCADE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (workspace_id, job_id, depends_on_job_id),
    -- Self-dependency is the cheapest cycle to create and the easiest to miss.
    CONSTRAINT research_job_dependencies_no_self_edge_check
        CHECK (job_id <> depends_on_job_id)
);

CREATE INDEX idx_research_job_dependencies_depends_on
    ON research.research_job_dependencies (workspace_id, depends_on_job_id);

-- -----------------------------------------------------------------------------
-- research.session_budget_entries -- budget accounting (§15)
--
-- The configured ceiling lives on research_sessions (budget_max_cost_units).
-- This table is the ledger that gives that ceiling a running total, separating
-- the two quantities that a single "spent" column would conflate:
--
--   RESERVATION  cost claimed before dispatch, so two concurrent dispatches
--                cannot both fit under the same remaining budget
--   ACTUAL       cost really consumed, recorded after the call returns
--   RELEASE      a reservation given back when the work did not happen
--
-- `currency` is explicit and defaults to COST_UNIT: cost units are
-- provider-agnostic (ADR-006) and are NOT a currency. Recording which is which
-- is what stops a later report from adding dollars to units.
--
-- Provider tariffs are configuration, never rows in a business table: see
-- packages/llm-gateway/python/sros_llm_gateway/pricing.py.
-- -----------------------------------------------------------------------------
CREATE TABLE research.session_budget_entries (
    id                      UUID        PRIMARY KEY,
    workspace_id            UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    research_session_id     UUID        NOT NULL REFERENCES research.research_sessions (id) ON DELETE CASCADE,
    job_id                  UUID        REFERENCES research.research_jobs (id) ON DELETE SET NULL,

    entry_kind              TEXT        NOT NULL,
    cost_units              NUMERIC(18, 6) NOT NULL,
    currency                TEXT        NOT NULL DEFAULT 'COST_UNIT',

    -- Reproducibility for the spend itself (llm-reasoning-rules.md §9).
    provider                TEXT,
    model                   TEXT,
    tier                    TEXT,
    pricing_version         TEXT,

    correlation_id          TEXT,
    recorded_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at              TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '365 days'),

    CONSTRAINT session_budget_entries_kind_check
        CHECK (entry_kind IN ('RESERVATION', 'ACTUAL', 'RELEASE')),
    CONSTRAINT session_budget_entries_cost_nonnegative_check
        CHECK (cost_units >= 0),
    CONSTRAINT session_budget_entries_tier_check
        CHECK (tier IS NULL OR tier IN ('FAST_MODEL', 'BALANCED_MODEL',
                                        'STRONG_MODEL', 'EMBEDDING_MODEL'))
);

CREATE INDEX idx_session_budget_entries_session
    ON research.session_budget_entries (workspace_id, research_session_id, recorded_at DESC);

CREATE INDEX idx_session_budget_entries_job
    ON research.session_budget_entries (workspace_id, job_id);

CREATE INDEX idx_session_budget_entries_expiry
    ON research.session_budget_entries (expires_at);

-- -----------------------------------------------------------------------------
-- research.research_completeness_records -- §17
--
-- INFRASTRUCTURE ONLY. No formula is defined here, and none may be inferred
-- from this shape. What the table enforces is that a completeness value can
-- never be read without knowing whether it was MEASURED or ESTIMATED, and
-- without the reasons it is not 100.
--
-- `basis` is NOT NULL on purpose: a completeness number with no stated basis
-- reads as a measurement, and an estimate that reads as a measurement is the
-- exact false precision scoring-framework-v1.1.md §10 forbids.
-- -----------------------------------------------------------------------------
CREATE TABLE research.research_completeness_records (
    id                      UUID        PRIMARY KEY,
    workspace_id            UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    research_session_id     UUID        NOT NULL REFERENCES research.research_sessions (id) ON DELETE CASCADE,

    -- Score family on 0-100 (scoring-framework-v1.1.md §2, §4.1). Named
    -- *_score because it is a score, never a confidence.
    measured_score          INTEGER,
    estimated_score         INTEGER,
    basis                   TEXT        NOT NULL,

    -- Why it is not complete, in the system's own words. Free text is
    -- deliberate: these reasons are read by humans, not branched on.
    incompleteness_reasons  TEXT[]      NOT NULL DEFAULT '{}',
    blocked_capabilities    TEXT[]      NOT NULL DEFAULT '{}',

    computed_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at              TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '365 days'),

    CONSTRAINT research_completeness_basis_check
        CHECK (basis IN ('MEASURED', 'ESTIMATED', 'UNKNOWN')),
    CONSTRAINT research_completeness_measured_score_range_check
        CHECK (measured_score IS NULL OR (measured_score BETWEEN 0 AND 100)),
    CONSTRAINT research_completeness_estimated_score_range_check
        CHECK (estimated_score IS NULL OR (estimated_score BETWEEN 0 AND 100)),
    -- MEASURED requires a measurement; ESTIMATED requires an estimate. A row
    -- claiming a basis it has no value for is not a partial record, it is a
    -- wrong one.
    CONSTRAINT research_completeness_basis_has_value_check
        CHECK ((basis = 'MEASURED'  AND measured_score  IS NOT NULL)
            OR (basis = 'ESTIMATED' AND estimated_score IS NOT NULL)
            OR (basis = 'UNKNOWN'))
);

CREATE INDEX idx_research_completeness_session
    ON research.research_completeness_records (workspace_id, research_session_id, computed_at DESC);

CREATE INDEX idx_research_completeness_expiry
    ON research.research_completeness_records (expires_at);

-- -----------------------------------------------------------------------------
-- research.research_gaps gains a job reference.
--
-- ADR-004: a permanently failed job becomes a research gap that lowers Research
-- Completeness rather than failing the session. Without this column the link
-- between the two is folklore.
-- -----------------------------------------------------------------------------
ALTER TABLE research.research_gaps
    ADD COLUMN job_id UUID REFERENCES research.research_jobs (id) ON DELETE SET NULL;

CREATE INDEX idx_research_gaps_job
    ON research.research_gaps (workspace_id, job_id);
