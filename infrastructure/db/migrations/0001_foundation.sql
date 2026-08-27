-- =============================================================================
-- 0001_foundation.sql -- Database schema V1
--
-- Governed by ADR-008. Invariants enforced mechanically by
-- infrastructure/scripts/validate_schema.py:
--
--   * every tenant-scoped table carries workspace_id UUID NOT NULL
--   * composite indexes lead with workspace_id
--   * NO PostgreSQL ENUM type for any evolving taxonomy (Ontology V2 §14.3)
--   * NO evidence-aggregation column (D-03 is blocked)
--   * retention-governed tables carry collected_at and expires_at
--
-- Forward-only. Never edited after it has been applied anywhere.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS registry;
CREATE SCHEMA IF NOT EXISTS research;
CREATE SCHEMA IF NOT EXISTS acquisition;
CREATE SCHEMA IF NOT EXISTS nlp;
CREATE SCHEMA IF NOT EXISTS scoring;

-- -----------------------------------------------------------------------------
-- Migration ledger
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core.schema_migrations (
    version      TEXT        PRIMARY KEY,
    applied_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    checksum     TEXT        NOT NULL
);

-- =============================================================================
-- core -- identity and tenancy (ADR-005)
-- =============================================================================

-- A principal. NOT a tenant. Authentication is deliberately not implemented;
-- this table exists so tenancy can be modelled correctly from day one.
CREATE TABLE core.users (
    id            UUID        PRIMARY KEY,
    email         TEXT        NOT NULL UNIQUE,
    display_name  TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- The tenant boundary. Everything tenant-scoped points here.
CREATE TABLE core.workspaces (
    id            UUID        PRIMARY KEY,
    slug          TEXT        NOT NULL UNIQUE,
    name          TEXT        NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- The indirection that makes teams and organizations possible later without
-- re-owning every row (ADR-005 §Alternatives, rejection of user-as-tenant).
-- Roles are stored as TEXT + CHECK, not ENUM: the role set will grow.
CREATE TABLE core.workspace_memberships (
    workspace_id  UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    user_id       UUID        NOT NULL REFERENCES core.users (id) ON DELETE CASCADE,
    role          TEXT        NOT NULL DEFAULT 'owner',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, user_id)
);

CREATE INDEX idx_workspace_memberships_user
    ON core.workspace_memberships (user_id);

-- =============================================================================
-- registry -- extensible taxonomies (Ontology V2 §14)
--
-- Rows, not enum types. Adding a product category must never need a migration.
-- =============================================================================

CREATE TABLE registry.registry_entries (
    registry      TEXT        NOT NULL,
    id            TEXT        NOT NULL,
    name          TEXT        NOT NULL,
    description   TEXT,
    version       INTEGER     NOT NULL DEFAULT 1,
    status        TEXT        NOT NULL DEFAULT 'ACTIVE',
    aliases       TEXT[]      NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (registry, id),
    CONSTRAINT registry_entries_status_check
        CHECK (status IN ('ACTIVE', 'DEPRECATED')),
    CONSTRAINT registry_entries_version_check
        CHECK (version >= 1),
    CONSTRAINT registry_entries_id_slug_check
        CHECK (id ~ '^[a-z0-9][a-z0-9._-]{0,127}$')
);

CREATE INDEX idx_registry_entries_active
    ON registry.registry_entries (registry, status);

-- Global source references. Contents and legal review records are D-07 and are
-- deliberately NOT populated here. This table exists so provenance can point
-- somewhere stable; acquisition-specific columns arrive with D-07.
CREATE TABLE registry.sources (
    id            TEXT        PRIMARY KEY,
    name          TEXT        NOT NULL,
    source_type   TEXT        NOT NULL,
    status        TEXT        NOT NULL DEFAULT 'PENDING_REVIEW',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT sources_status_check
        CHECK (status IN ('PENDING_REVIEW', 'APPROVED', 'SUSPENDED')),
    CONSTRAINT sources_id_slug_check
        CHECK (id ~ '^[a-z0-9][a-z0-9._-]{0,127}$')
);

-- =============================================================================
-- research -- projects, sessions, opportunities (Ontology V2 §11, §12)
-- =============================================================================

CREATE TABLE research.research_projects (
    id            UUID        PRIMARY KEY,
    workspace_id  UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    name          TEXT        NOT NULL,
    description   TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_research_projects_workspace
    ON research.research_projects (workspace_id, created_at DESC);

-- The ONLY persisted execution entity. There is no ResearchRun.
--
-- research_context is an immutable JSONB snapshot (ADR-008 §ResearchContext
-- persistence). Written once at creation, never updated. The hash gives cheap
-- equality and tamper evidence; the schema version keeps old snapshots
-- interpretable after the context shape evolves.
CREATE TABLE research.research_sessions (
    id                              UUID        PRIMARY KEY,
    workspace_id                    UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    project_id                      UUID        NOT NULL REFERENCES research.research_projects (id) ON DELETE CASCADE,

    research_context                JSONB       NOT NULL,
    research_context_hash           TEXT        NOT NULL,
    research_context_schema_version TEXT        NOT NULL,

    status                          TEXT        NOT NULL DEFAULT 'PENDING',

    created_at                      TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at                      TIMESTAMPTZ,
    completed_at                    TIMESTAMPTZ,

    -- Budget configuration and consumption (ADR-006). Cost units are provider
    -- agnostic on purpose: no product pricing is invented here.
    budget_max_cost_units           NUMERIC(18, 6),
    budget_max_llm_calls            INTEGER,
    actual_cost_units               NUMERIC(18, 6) NOT NULL DEFAULT 0,
    actual_llm_calls                INTEGER     NOT NULL DEFAULT 0,

    -- A score family on 0-100 (scoring-framework-v1.1.md §2, §4.1).
    -- Named *_score because it is a score, not a confidence.
    research_completeness_score     INTEGER,

    -- Reproducibility (llm-reasoning-rules.md §9).
    contract_version                TEXT        NOT NULL,
    ontology_version                TEXT        NOT NULL,

    failure_reason                  TEXT,

    CONSTRAINT research_sessions_status_check
        CHECK (status IN ('PENDING', 'PLANNING', 'COLLECTING', 'ANALYZING',
                          'SCORING', 'COMPLETED', 'FAILED', 'CANCELLED')),
    CONSTRAINT research_sessions_completeness_range_check
        CHECK (research_completeness_score IS NULL
               OR (research_completeness_score BETWEEN 0 AND 100))
);

CREATE INDEX idx_research_sessions_workspace_status
    ON research.research_sessions (workspace_id, status, created_at DESC);

CREATE INDEX idx_research_sessions_project
    ON research.research_sessions (workspace_id, project_id, created_at DESC);

CREATE INDEX idx_research_sessions_context
    ON research.research_sessions USING GIN (research_context);

-- Research gaps: what was intended but not covered, and why. A failed source is
-- a recorded gap, not a session failure.
CREATE TABLE research.research_gaps (
    id                  UUID        PRIMARY KEY,
    workspace_id        UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    research_session_id UUID        NOT NULL REFERENCES research.research_sessions (id) ON DELETE CASCADE,
    source_id           TEXT        REFERENCES registry.sources (id),
    gap_kind            TEXT        NOT NULL,
    detail              TEXT        NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_research_gaps_session
    ON research.research_gaps (workspace_id, research_session_id);

-- A domain hypothesis in its own right. NOT owned by the session that found it.
CREATE TABLE research.opportunities (
    id            UUID        PRIMARY KEY,
    workspace_id  UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    title         TEXT        NOT NULL,
    summary       TEXT,

    -- Canonical MarketScope (Ontology V2 §4). market_scope_key is the canonical
    -- string form, so scope equality is a cheap indexed comparison and two ways
    -- of writing the same scope cannot become two rows.
    market_scope      JSONB   NOT NULL,
    market_scope_key  TEXT    NOT NULL,

    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_opportunities_workspace
    ON research.opportunities (workspace_id, created_at DESC);

CREATE INDEX idx_opportunities_scope
    ON research.opportunities (workspace_id, market_scope_key);

-- The association that makes rediscovery representable (Ontology V2 §12).
--
-- DELIBERATELY ABSENT: any unique constraint that would decide two
-- opportunities are the same. Identity resolution is an analytical problem
-- (Ontology V2 §12.3) and must not be settled by a convenient index.
--
-- The one uniqueness rule below is bookkeeping, not semantics: a session
-- observes a given opportunity at most once.
CREATE TABLE research.opportunity_session_observations (
    id                  UUID        PRIMARY KEY,
    workspace_id        UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    opportunity_id      UUID        NOT NULL REFERENCES research.opportunities (id) ON DELETE CASCADE,
    research_session_id UUID        NOT NULL REFERENCES research.research_sessions (id) ON DELETE CASCADE,

    -- How this session related to the opportunity. Not a scoring judgment.
    observation_kind    TEXT        NOT NULL,
    claim_type          TEXT        NOT NULL,

    observed_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT opportunity_observations_claim_type_check
        CHECK (claim_type IN ('OBSERVED', 'INFERRED', 'PREDICTED',
                              'RECOMMENDED', 'HYPOTHESIS')),
    CONSTRAINT opportunity_observations_kind_check
        CHECK (observation_kind IN ('DISCOVERED', 'CORROBORATED', 'CONTRADICTED')),
    CONSTRAINT opportunity_observations_unique_per_session
        UNIQUE (workspace_id, opportunity_id, research_session_id)
);

CREATE INDEX idx_opportunity_observations_opportunity
    ON research.opportunity_session_observations (workspace_id, opportunity_id, observed_at DESC);

CREATE INDEX idx_opportunity_observations_session
    ON research.opportunity_session_observations (workspace_id, research_session_id);

-- =============================================================================
-- acquisition -- raw and normalized records
--
-- Retention-governed (data-retention-policy-v1.md §2.1, §2.2).
-- expires_at is computed at WRITE time, so the retention decision stays
-- auditable after the policy changes.
-- =============================================================================

CREATE TABLE acquisition.raw_records (
    id                  UUID        PRIMARY KEY,
    workspace_id        UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    research_session_id UUID        REFERENCES research.research_sessions (id) ON DELETE SET NULL,

    -- Provenance (evidence-confidence-framework-v1.md §10). NOT NULL by default
    -- (audit A-10): an exemption must be an explicit, reviewed decision.
    source_id           TEXT        NOT NULL REFERENCES registry.sources (id),
    source_reference    TEXT        NOT NULL,
    acquisition_method  TEXT        NOT NULL,
    content_hash        TEXT        NOT NULL,
    parent_record_id    UUID        REFERENCES acquisition.raw_records (id) ON DELETE SET NULL,

    payload_ref         TEXT        NOT NULL,
    content_language    TEXT,

    collected_at        TIMESTAMPTZ NOT NULL,
    expires_at          TIMESTAMPTZ NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT raw_records_dedup_unique
        UNIQUE (workspace_id, source_id, content_hash)
);

CREATE INDEX idx_raw_records_workspace_collected
    ON acquisition.raw_records (workspace_id, collected_at DESC);

CREATE INDEX idx_raw_records_expiry
    ON acquisition.raw_records (expires_at);

CREATE TABLE acquisition.normalized_records (
    id                  UUID        PRIMARY KEY,
    workspace_id        UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    raw_record_id       UUID        NOT NULL REFERENCES acquisition.raw_records (id) ON DELETE CASCADE,
    research_session_id UUID        REFERENCES research.research_sessions (id) ON DELETE SET NULL,

    source_id           TEXT        NOT NULL REFERENCES registry.sources (id),
    extraction_method   TEXT        NOT NULL,
    transformation_version TEXT     NOT NULL,
    content_hash        TEXT        NOT NULL,
    content_language    TEXT,

    -- Event time, not ingestion time (data-principles.md §9).
    observed_at         TIMESTAMPTZ,
    collected_at        TIMESTAMPTZ NOT NULL,
    expires_at          TIMESTAMPTZ NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_normalized_records_workspace
    ON acquisition.normalized_records (workspace_id, collected_at DESC);

CREATE INDEX idx_normalized_records_expiry
    ON acquisition.normalized_records (expires_at);

-- =============================================================================
-- nlp -- signals and embedding provenance
-- =============================================================================

CREATE TABLE nlp.signals (
    id                    UUID        PRIMARY KEY,
    workspace_id          UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    normalized_record_id  UUID        REFERENCES acquisition.normalized_records (id) ON DELETE SET NULL,
    research_session_id   UUID        REFERENCES research.research_sessions (id) ON DELETE SET NULL,

    -- Closed enum, TEXT + CHECK (ADR-008). Signal TYPE is a registry reference.
    signal_family         TEXT        NOT NULL,
    signal_type_registry  TEXT        NOT NULL DEFAULT 'demand_signal_type',
    signal_type_id        TEXT        NOT NULL,

    -- Unit interval (scoring-framework-v1.1.md §4.1).
    value                 DOUBLE PRECISION,
    confidence            DOUBLE PRECISION,

    -- Reproducibility (llm-reasoning-rules.md §9).
    model_version         TEXT,
    prompt_version        TEXT,
    extraction_method     TEXT        NOT NULL,

    observed_at           TIMESTAMPTZ,
    collected_at          TIMESTAMPTZ NOT NULL,
    expires_at            TIMESTAMPTZ NOT NULL,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT signals_family_check
        CHECK (signal_family IN ('PAIN', 'DESIRE', 'BEHAVIORAL', 'MARKET')),
    CONSTRAINT signals_value_unit_interval_check
        CHECK (value IS NULL OR (value BETWEEN 0 AND 1)),
    CONSTRAINT signals_confidence_unit_interval_check
        CHECK (confidence IS NULL OR (confidence BETWEEN 0 AND 1)),
    FOREIGN KEY (signal_type_registry, signal_type_id)
        REFERENCES registry.registry_entries (registry, id)
);

CREATE INDEX idx_signals_workspace
    ON nlp.signals (workspace_id, collected_at DESC);

CREATE INDEX idx_signals_expiry
    ON nlp.signals (expires_at);

-- Embedding PROVENANCE lives in PostgreSQL; the vectors live in Qdrant.
-- This is what makes Qdrant a derived, rebuildable index (ADR-008, audit A-09).
CREATE TABLE nlp.embedding_provenance (
    id                    UUID        PRIMARY KEY,
    workspace_id          UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    normalized_record_id  UUID        REFERENCES acquisition.normalized_records (id) ON DELETE CASCADE,

    qdrant_collection     TEXT        NOT NULL,
    qdrant_point_id       TEXT        NOT NULL,

    embedding_model       TEXT        NOT NULL,
    embedding_model_version TEXT      NOT NULL,
    content_hash          TEXT        NOT NULL,

    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT embedding_provenance_point_unique
        UNIQUE (workspace_id, qdrant_collection, qdrant_point_id)
);

CREATE INDEX idx_embedding_provenance_workspace
    ON nlp.embedding_provenance (workspace_id, embedding_model_version);

-- =============================================================================
-- scoring -- evidence records
--
-- RAW evidence metadata only. NO aggregation semantics: D-03 is unresolved, so
-- there is no aggregated score, no decay weight, no independence threshold
-- result and no contradiction penalty anywhere in this schema.
-- The schema validator fails the build if one appears.
-- =============================================================================

CREATE TABLE scoring.evidence (
    id                  UUID        PRIMARY KEY,
    workspace_id        UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    opportunity_id      UUID        REFERENCES research.opportunities (id) ON DELETE CASCADE,
    research_session_id UUID        REFERENCES research.research_sessions (id) ON DELETE SET NULL,
    signal_id           UUID        REFERENCES nlp.signals (id) ON DELETE SET NULL,

    claim_type          TEXT        NOT NULL,

    -- Integer 0-5, never rescaled, never averaged into a score.
    evidence_level      SMALLINT    NOT NULL,

    -- Unit interval quantities. Raw metadata; how they combine is D-03.
    reliability         DOUBLE PRECISION,
    independence        DOUBLE PRECISION,
    confidence          DOUBLE PRECISION,

    -- Provenance
    source_id           TEXT        REFERENCES registry.sources (id),
    source_reference    TEXT,
    extraction_method   TEXT,
    model_version       TEXT,
    prompt_version      TEXT,

    -- Event time vs collection time kept distinct (data-principles.md §9).
    observed_at         TIMESTAMPTZ,
    collected_at        TIMESTAMPTZ NOT NULL,
    expires_at          TIMESTAMPTZ NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT evidence_claim_type_check
        CHECK (claim_type IN ('OBSERVED', 'INFERRED', 'PREDICTED',
                              'RECOMMENDED', 'HYPOTHESIS')),
    CONSTRAINT evidence_level_range_check
        CHECK (evidence_level BETWEEN 0 AND 5),
    CONSTRAINT evidence_reliability_unit_interval_check
        CHECK (reliability IS NULL OR (reliability BETWEEN 0 AND 1)),
    CONSTRAINT evidence_independence_unit_interval_check
        CHECK (independence IS NULL OR (independence BETWEEN 0 AND 1)),
    CONSTRAINT evidence_confidence_unit_interval_check
        CHECK (confidence IS NULL OR (confidence BETWEEN 0 AND 1))
);

CREATE INDEX idx_evidence_workspace_opportunity
    ON scoring.evidence (workspace_id, opportunity_id, collected_at DESC);

CREATE INDEX idx_evidence_session
    ON scoring.evidence (workspace_id, research_session_id);

CREATE INDEX idx_evidence_expiry
    ON scoring.evidence (expires_at);
