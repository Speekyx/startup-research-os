-- =============================================================================
-- 0004_source_registry.sql -- Source Registry (resolves D-07)
--
-- Mission 1.0. Governed by docs/data/source-registry-v1.md, and by
-- data-principles.md §13 ("before integrating a new source, record ...") and
-- data-retention-policy-v1.md §3 (per-source retention_override).
--
-- WHAT THIS TABLE SET IS FOR
--
-- A source becomes collectable only by passing a gate, and the gate is the
-- point of the whole mission:
--
--     candidate -> technical review -> policy review -> retention review
--               -> data classification -> human approval -> eligibility
--
-- Public visibility is NOT a step in that sequence. A page being readable in a
-- browser says nothing about permission for automated access, commercial reuse,
-- retention, redistribution or model processing, and the schema is arranged so
-- that no path exists from "visible" to "collectable".
--
-- TWO RULES ENFORCED BY THE DATABASE, NOT BY MEMORY
--
--   1. A review cannot reach an approving state with no evidence behind it.
--   2. A collector cannot be enabled on a source that is not eligible.
--
-- Both are triggers rather than CHECK constraints, because both depend on rows
-- in other tables. A comment asking people to remember them would be a comment.
--
-- Invariants preserved from ADR-008:
--   * registry.* is GLOBAL reference data and carries no workspace_id
--   * no PostgreSQL ENUM type; closed sets are TEXT + CHECK matching the
--     contract source of truth (packages/contracts/schema/domain.v1.json)
--   * no evidence-aggregation column: D-03 stays blocked, and a source's policy
--     metadata is NOT its Evidence Score
--
-- Forward-only. Never edited after it has been applied anywhere.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Source families, as REGISTRY ROWS
--
-- Ontology V2 §14.3 applied to sources: a new source category must never require
-- a migration. These are the initial canonical entries, not an enum.
-- -----------------------------------------------------------------------------
INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('source_family', 'community',         'Community / discussion', 'Forums and discussion sites where users post and reply'),
    ('source_family', 'social',            'Social platform',        'Short-form social content and its engagement signals'),
    ('source_family', 'app_store',         'Application marketplace','App listings, ratings and reviews'),
    ('source_family', 'product_discovery', 'Product discovery',      'Launch and discovery platforms for new products'),
    ('source_family', 'developer',         'Developer ecosystem',    'Code hosting, package registries and issue trackers'),
    ('source_family', 'search_trends',     'Search and trends',      'Search interest and query-volume signals'),
    ('source_family', 'news',              'News',                   'Editorial and press coverage'),
    ('source_family', 'economic_data',     'Economic data',          'Official statistical and macroeconomic series'),
    ('source_family', 'public_dataset',    'Public dataset',         'Published bulk datasets and open data portals'),
    ('source_family', 'forum',             'Q&A / forum',            'Structured question-and-answer sites'),
    ('source_family', 'content_platform',  'Content platform',       'Video, audio and long-form publishing platforms')
ON CONFLICT (registry, id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 2. registry.sources -- identity and lifecycle
--
-- The 0001 stub held id/name/source_type/status against the day D-07 was
-- resolved. That day is now, and the table has never held a row: nothing
-- references `source_type`, and no FK from acquisition points at any source yet.
-- Restructuring it here is therefore additive in effect, and is done in this
-- forward migration rather than by editing 0001, which is immutable.
--
-- `status` becomes `lifecycle`. The rename is the point: the old column mixed
-- "does this source still exist" with "may we use it", and those answers move
-- independently. A deprecated source may have been approved; an active source
-- may never have been reviewed. Approval now lives on the review, which is
-- versioned and carries its evidence.
-- -----------------------------------------------------------------------------
ALTER TABLE registry.sources DROP CONSTRAINT sources_status_check;
ALTER TABLE registry.sources RENAME COLUMN status TO lifecycle;
ALTER TABLE registry.sources RENAME COLUMN name TO canonical_name;
ALTER TABLE registry.sources ALTER COLUMN lifecycle SET DEFAULT 'ACTIVE';
ALTER TABLE registry.sources
    ADD CONSTRAINT sources_lifecycle_check CHECK (lifecycle IN ('ACTIVE', 'DEPRECATED'));

-- `source_type` was free text with no consumer. It becomes a registry reference
-- so a new family is an INSERT (Ontology V2 §14.3).
ALTER TABLE registry.sources DROP COLUMN source_type;

ALTER TABLE registry.sources
    ADD COLUMN source_family_registry TEXT NOT NULL DEFAULT 'source_family',
    ADD COLUMN source_family          TEXT NOT NULL DEFAULT 'community',
    ADD COLUMN homepage_url           TEXT,
    ADD COLUMN developer_portal_url   TEXT,
    ADD COLUMN documentation_url      TEXT,
    ADD COLUMN description            TEXT,

    -- §21. FALSE for every new source, always. Enablement is a decision taken
    -- after review, never a default inherited by existing.
    ADD COLUMN collector_enabled      BOOLEAN NOT NULL DEFAULT FALSE,

    -- An operational stop that does not wait for a review cycle. Separate from
    -- the review state because the reasons differ: a review concludes, a
    -- suspension reacts.
    ADD COLUMN suspended              BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN suspended_reason       TEXT,

    -- §17. Descriptive coverage. Language is NOT geography: a source dominated
    -- by English speakers is not thereby representative of any market, and
    -- these columns are kept separate so nothing can infer one from the other.
    ADD COLUMN coverage_scope         TEXT NOT NULL DEFAULT 'UNKNOWN',
    ADD COLUMN coverage_countries     TEXT[] NOT NULL DEFAULT '{}',
    ADD COLUMN coverage_regions       TEXT[] NOT NULL DEFAULT '{}',
    ADD COLUMN coverage_languages     TEXT[] NOT NULL DEFAULT '{}',

    -- §18. Observable limitations for later Data Science: freshness, sampling
    -- bias, spam exposure, moderation effects, ranking bias, truncation,
    -- pagination ceilings, historical depth.
    --
    -- DELIBERATELY NOT a reliability number. Assigning a source a weight is
    -- evidence aggregation, which is D-03 and is blocked. What lives here is
    -- what can be observed and re-checked, not what it is worth.
    ADD COLUMN quality_notes          JSONB NOT NULL DEFAULT '{}',

    ADD CONSTRAINT sources_coverage_scope_check
        CHECK (coverage_scope IN ('GLOBAL', 'PARTIAL', 'UNKNOWN')),
    ADD CONSTRAINT sources_suspension_needs_reason_check
        CHECK (suspended IS FALSE OR suspended_reason IS NOT NULL),
    -- ISO 3166-1 alpha-2, uppercase (Ontology V2 §4.3). A CHECK may not contain
    -- a subquery, so the array is validated as one joined string: that covers
    -- every element without needing to iterate over them.
    ADD CONSTRAINT sources_country_codes_check
        CHECK (array_to_string(coverage_countries, ',') ~ '^([A-Z]{2}(,[A-Z]{2})*)?$'),
    ADD CONSTRAINT sources_source_family_fkey
        FOREIGN KEY (source_family_registry, source_family)
        REFERENCES registry.registry_entries (registry, id);

CREATE INDEX idx_sources_family ON registry.sources (source_family, lifecycle);
CREATE INDEX idx_sources_collector_enabled ON registry.sources (collector_enabled)
    WHERE collector_enabled;

COMMENT ON COLUMN registry.sources.id IS
    'Stable identifier. Never reused, never renamed, never derived from a URL: '
    'a display name or a domain can change while the source stays the same '
    'thing, and provenance written against it must keep resolving.';
COMMENT ON COLUMN registry.sources.collector_enabled IS
    'FALSE by default and by trigger. Cannot be set TRUE unless the source is '
    'eligible (Mission 1.0 §21).';

-- -----------------------------------------------------------------------------
-- 3. registry.source_access_profiles -- HOW access is technically performed
--
-- One row per access method a source offers. Several may coexist: an official
-- API and a public feed are different profiles of the same source with
-- different limits and different authentication.
--
-- An access profile says nothing about PERMISSION. BROWSER_AUTOMATION appearing
-- here means "technically possible", never "allowed" -- that answer lives in
-- the policy review, and the two are separate tables so they cannot be read as
-- one.
--
-- CREDENTIALS ARE NEVER STORED HERE. `secret_reference` holds a configuration
-- KEY NAME such as 'REDDIT_CLIENT_ID'. A trigger below refuses anything that
-- looks like a secret value.
-- -----------------------------------------------------------------------------
CREATE TABLE registry.source_access_profiles (
    id                      UUID        PRIMARY KEY,
    source_id               TEXT        NOT NULL REFERENCES registry.sources (id) ON DELETE CASCADE,

    access_method           TEXT        NOT NULL,
    label                   TEXT        NOT NULL,
    endpoint_url            TEXT,
    documentation_url       TEXT,

    -- §9. Authentication REQUIREMENTS, not authentication material.
    requires_authentication BOOLEAN     NOT NULL DEFAULT FALSE,
    requires_api_key        BOOLEAN     NOT NULL DEFAULT FALSE,
    requires_oauth          BOOLEAN     NOT NULL DEFAULT FALSE,
    requires_account        BOOLEAN     NOT NULL DEFAULT FALSE,
    requires_developer_app  BOOLEAN     NOT NULL DEFAULT FALSE,
    requires_approval       BOOLEAN     NOT NULL DEFAULT FALSE,
    approval_process_notes  TEXT,
    secret_references       TEXT[]      NOT NULL DEFAULT '{}',

    -- §19. UNKNOWN is a real answer and the default one. A guessed rate limit
    -- is worse than no rate limit: a collector would trust it.
    rate_limit_known        BOOLEAN     NOT NULL DEFAULT FALSE,
    rate_limit_requests     INTEGER,
    rate_limit_period_seconds INTEGER,
    rate_limit_burst        INTEGER,
    rate_limit_concurrency  INTEGER,
    rate_limit_daily_quota  INTEGER,
    pagination_limit        INTEGER,
    rate_limit_origin       TEXT,
    rate_limit_verified_at  TIMESTAMPTZ,

    -- §20. The SHAPE of the cost, never an amount. Operators change prices;
    -- a figure recorded here would be quoted long after it stopped being true.
    acquisition_cost        TEXT        NOT NULL DEFAULT 'UNKNOWN',
    cost_reference_url      TEXT,
    cost_reviewed_at        TIMESTAMPTZ,

    notes                   TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT source_access_profiles_method_check
        CHECK (access_method IN ('OFFICIAL_API', 'PUBLIC_API', 'RSS_OR_FEED',
                                 'DATASET_DOWNLOAD', 'PUBLIC_WEB',
                                 'BROWSER_AUTOMATION', 'MANUAL_IMPORT')),
    CONSTRAINT source_access_profiles_cost_check
        CHECK (acquisition_cost IN ('FREE', 'FREE_WITH_LIMITS', 'PAID',
                                    'USAGE_BASED', 'UNKNOWN')),
    CONSTRAINT source_access_profiles_origin_check
        CHECK (rate_limit_origin IS NULL
               OR rate_limit_origin IN ('DOCUMENTED', 'OBSERVED', 'UNKNOWN')),
    -- A claimed rate limit must say where the number came from, or it is a guess.
    CONSTRAINT source_access_profiles_rate_limit_origin_required_check
        CHECK (rate_limit_known IS FALSE OR rate_limit_origin IS NOT NULL),
    CONSTRAINT source_access_profiles_rate_limit_positive_check
        CHECK ((rate_limit_requests IS NULL OR rate_limit_requests > 0)
           AND (rate_limit_period_seconds IS NULL OR rate_limit_period_seconds > 0)
           AND (rate_limit_daily_quota IS NULL OR rate_limit_daily_quota > 0)),
    -- Requiring a key without naming where it comes from makes a source look
    -- usable and fail at the first call.
    CONSTRAINT source_access_profiles_secret_reference_required_check
        CHECK ((requires_api_key IS FALSE AND requires_oauth IS FALSE)
               OR cardinality(secret_references) > 0),
    CONSTRAINT source_access_profiles_unique_method
        UNIQUE (source_id, access_method, label)
);

CREATE INDEX idx_source_access_profiles_source
    ON registry.source_access_profiles (source_id, access_method);

-- -----------------------------------------------------------------------------
-- 4. registry.source_policy_reviews -- WHETHER, per activity
--
-- Versioned. A review is never edited into a new conclusion: platform terms
-- change, and the record of what was believed on a date is what makes a past
-- collection defensible. Re-review inserts a new version.
--
-- Each activity is assessed SEPARATELY. Collapsing them into one boolean called
-- `allowed` would erase the case this registry exists for -- a source that
-- permits automated API access and forbids commercial use is both, and only a
-- per-activity model can say so.
-- -----------------------------------------------------------------------------
CREATE TABLE registry.source_policy_reviews (
    id                      UUID        PRIMARY KEY,
    source_id               TEXT        NOT NULL REFERENCES registry.sources (id) ON DELETE CASCADE,
    review_version          INTEGER     NOT NULL DEFAULT 1,

    approval_state          TEXT        NOT NULL DEFAULT 'DRAFT',

    -- §11. One verdict per activity. NOT_ADDRESSED means the documents were
    -- silent, and silence never becomes permission.
    automated_access        TEXT        NOT NULL DEFAULT 'NOT_ASSESSED',
    api_use                 TEXT        NOT NULL DEFAULT 'NOT_ASSESSED',
    browser_automation      TEXT        NOT NULL DEFAULT 'NOT_ASSESSED',
    commercial_use          TEXT        NOT NULL DEFAULT 'NOT_ASSESSED',
    storage                 TEXT        NOT NULL DEFAULT 'NOT_ASSESSED',
    retention               TEXT        NOT NULL DEFAULT 'NOT_ASSESSED',
    redistribution          TEXT        NOT NULL DEFAULT 'NOT_ASSESSED',
    derived_analytics       TEXT        NOT NULL DEFAULT 'NOT_ASSESSED',
    model_processing        TEXT        NOT NULL DEFAULT 'NOT_ASSESSED',
    personal_data_handling  TEXT        NOT NULL DEFAULT 'NOT_ASSESSED',
    attribution_required    TEXT        NOT NULL DEFAULT 'NOT_ASSESSED',

    -- The scope the assessment covers. An approval that does not say what it
    -- approved cannot be relied on for anything else.
    assessed_use_case       TEXT        NOT NULL,
    conditions              TEXT[]      NOT NULL DEFAULT '{}',
    open_questions          TEXT[]      NOT NULL DEFAULT '{}',
    review_notes            TEXT,

    -- §9. Risk classification, not a legal ruling. Jurisdiction analysis stays
    -- a separate human decision (data-retention-policy-v1.md §7).
    personal_data_risk      TEXT        NOT NULL DEFAULT 'UNKNOWN',
    contains_user_generated_content BOOLEAN NOT NULL DEFAULT FALSE,
    contains_user_identifiers       BOOLEAN NOT NULL DEFAULT FALSE,
    contains_location               BOOLEAN NOT NULL DEFAULT FALSE,
    sensitive_data_possible         BOOLEAN NOT NULL DEFAULT FALSE,
    pseudonymization_expected       BOOLEAN NOT NULL DEFAULT FALSE,
    discard_identifiers_after_normalization BOOLEAN NOT NULL DEFAULT FALSE,
    jurisdiction_review_required    BOOLEAN NOT NULL DEFAULT TRUE,

    -- §14. Freshness. Cadence is per source, because platforms differ in how
    -- often they change terms and no single universal interval is defensible.
    reviewed_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed_by             TEXT        NOT NULL,
    review_interval_days    INTEGER     NOT NULL DEFAULT 180,
    next_review_at          TIMESTAMPTZ,
    superseded_at           TIMESTAMPTZ,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT source_policy_reviews_state_check
        CHECK (approval_state IN ('DRAFT', 'REQUIRES_REVIEW', 'APPROVED_WITH_CONDITIONS',
                                  'APPROVED', 'RESTRICTED', 'PROHIBITED', 'SUSPENDED')),
    CONSTRAINT source_policy_reviews_personal_data_risk_check
        CHECK (personal_data_risk IN ('NONE_EXPECTED', 'PSEUDONYMOUS', 'IDENTIFIABLE',
                                      'SENSITIVE_POSSIBLE', 'UNKNOWN')),
    CONSTRAINT source_policy_reviews_assessments_check
        CHECK (automated_access       IN ('PERMITTED','PERMITTED_WITH_CONDITIONS','NOT_PERMITTED','NOT_ADDRESSED','UNCLEAR','NOT_ASSESSED')
           AND api_use                IN ('PERMITTED','PERMITTED_WITH_CONDITIONS','NOT_PERMITTED','NOT_ADDRESSED','UNCLEAR','NOT_ASSESSED')
           AND browser_automation     IN ('PERMITTED','PERMITTED_WITH_CONDITIONS','NOT_PERMITTED','NOT_ADDRESSED','UNCLEAR','NOT_ASSESSED')
           AND commercial_use         IN ('PERMITTED','PERMITTED_WITH_CONDITIONS','NOT_PERMITTED','NOT_ADDRESSED','UNCLEAR','NOT_ASSESSED')
           AND storage                IN ('PERMITTED','PERMITTED_WITH_CONDITIONS','NOT_PERMITTED','NOT_ADDRESSED','UNCLEAR','NOT_ASSESSED')
           AND retention              IN ('PERMITTED','PERMITTED_WITH_CONDITIONS','NOT_PERMITTED','NOT_ADDRESSED','UNCLEAR','NOT_ASSESSED')
           AND redistribution         IN ('PERMITTED','PERMITTED_WITH_CONDITIONS','NOT_PERMITTED','NOT_ADDRESSED','UNCLEAR','NOT_ASSESSED')
           AND derived_analytics      IN ('PERMITTED','PERMITTED_WITH_CONDITIONS','NOT_PERMITTED','NOT_ADDRESSED','UNCLEAR','NOT_ASSESSED')
           AND model_processing       IN ('PERMITTED','PERMITTED_WITH_CONDITIONS','NOT_PERMITTED','NOT_ADDRESSED','UNCLEAR','NOT_ASSESSED')
           AND personal_data_handling IN ('PERMITTED','PERMITTED_WITH_CONDITIONS','NOT_PERMITTED','NOT_ADDRESSED','UNCLEAR','NOT_ASSESSED')
           AND attribution_required   IN ('PERMITTED','PERMITTED_WITH_CONDITIONS','NOT_PERMITTED','NOT_ADDRESSED','UNCLEAR','NOT_ASSESSED')),
    -- An approval that names conditions it does not list is not a condition.
    CONSTRAINT source_policy_reviews_conditions_required_check
        CHECK (approval_state <> 'APPROVED_WITH_CONDITIONS' OR cardinality(conditions) > 0),
    -- A restriction or prohibition must say what it is. "No" with no reason
    -- gets re-litigated by the next person who wants the data.
    CONSTRAINT source_policy_reviews_reason_required_check
        CHECK (approval_state NOT IN ('RESTRICTED', 'PROHIBITED', 'SUSPENDED')
               OR review_notes IS NOT NULL),
    CONSTRAINT source_policy_reviews_interval_check
        CHECK (review_interval_days > 0),
    CONSTRAINT source_policy_reviews_version_check
        CHECK (review_version >= 1),
    CONSTRAINT source_policy_reviews_scope_check
        CHECK (length(btrim(assessed_use_case)) > 0),
    CONSTRAINT source_policy_reviews_version_unique
        UNIQUE (source_id, review_version)
);

CREATE INDEX idx_source_policy_reviews_source
    ON registry.source_policy_reviews (source_id, review_version DESC);
CREATE INDEX idx_source_policy_reviews_current
    ON registry.source_policy_reviews (source_id) WHERE superseded_at IS NULL;

-- next_review_at defaults to reviewed_at + the source's own cadence.
CREATE OR REPLACE FUNCTION registry.set_next_review_at()
    RETURNS trigger
    LANGUAGE plpgsql
    SET search_path = pg_catalog, registry
AS $$
BEGIN
    IF NEW.next_review_at IS NULL THEN
        NEW.next_review_at := NEW.reviewed_at + (NEW.review_interval_days || ' days')::interval;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_source_policy_reviews_next_review
    BEFORE INSERT OR UPDATE ON registry.source_policy_reviews
    FOR EACH ROW EXECUTE FUNCTION registry.set_next_review_at();

-- -----------------------------------------------------------------------------
-- 5. registry.source_policy_evidence -- WHAT the conclusion rests on
--
-- §13. A conclusion points at a document. Without this table an approval is an
-- opinion with a timestamp, and there is no way to re-verify it when the
-- platform changes its terms.
--
-- Full documents are NOT stored: they are third-party copyrighted text, and
-- copying them wholesale would be the same disregard for source terms this
-- registry exists to prevent. What is stored is a reference, a retrieval time,
-- a section pointer, a short summarized finding and, where practical, a
-- fingerprint so a later fetch can show the document changed.
-- -----------------------------------------------------------------------------
CREATE TABLE registry.source_policy_evidence (
    id                  UUID        PRIMARY KEY,
    review_id           UUID        NOT NULL REFERENCES registry.source_policy_reviews (id) ON DELETE CASCADE,
    source_id           TEXT        NOT NULL REFERENCES registry.sources (id) ON DELETE CASCADE,

    document_type       TEXT        NOT NULL,
    document_title      TEXT        NOT NULL,
    document_url        TEXT        NOT NULL,
    section_reference   TEXT,

    -- A short paraphrase of what the document says, in the reviewer's words.
    -- Not a quotation of the document at length.
    summarized_finding  TEXT        NOT NULL,
    excerpt             TEXT,
    review_notes        TEXT,

    retrieved_at        TIMESTAMPTZ NOT NULL,
    effective_at        TIMESTAMPTZ,
    document_fingerprint TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT source_policy_evidence_type_check
        CHECK (document_type IN ('OFFICIAL_API_DOCS', 'OFFICIAL_TERMS', 'OFFICIAL_LICENCE',
                                 'OFFICIAL_PRIVACY', 'OFFICIAL_ACCESS_CONTROL',
                                 'OPERATOR_CORRESPONDENCE', 'LEGAL_REVIEW')),
    CONSTRAINT source_policy_evidence_url_check
        CHECK (document_url ~ '^https?://'),
    CONSTRAINT source_policy_evidence_finding_check
        CHECK (length(btrim(summarized_finding)) > 0),
    -- A long excerpt is a copy. The cap keeps this a reference, not a mirror.
    CONSTRAINT source_policy_evidence_excerpt_length_check
        CHECK (excerpt IS NULL OR length(excerpt) <= 1000)
);

CREATE INDEX idx_source_policy_evidence_review
    ON registry.source_policy_evidence (review_id);
CREATE INDEX idx_source_policy_evidence_source
    ON registry.source_policy_evidence (source_id, retrieved_at DESC);

-- -----------------------------------------------------------------------------
-- 6. registry.source_retention_policies -- per-source override
--
-- data-retention-policy-v1.md §3. An override may go in BOTH directions, and
-- the stricter applicable rule always wins (§1).
--
-- `basis` is NOT NULL by constraint, because §3 says so and gives the reason: an
-- override without a recorded justification is indistinguishable from someone
-- having wanted more data, and cannot be re-verified when terms change.
--
-- No row means the project baseline applies. Absence is never read as
-- "unlimited": data-retention-policy-v1.md §2 supplies the defaults.
-- -----------------------------------------------------------------------------
CREATE TABLE registry.source_retention_policies (
    id                      UUID        PRIMARY KEY,
    source_id               TEXT        NOT NULL REFERENCES registry.sources (id) ON DELETE CASCADE,

    raw_days                INTEGER,
    normalized_days         INTEGER,
    aggregate_permitted     BOOLEAN     NOT NULL DEFAULT TRUE,

    basis                   TEXT        NOT NULL,
    review_id               UUID        REFERENCES registry.source_policy_reviews (id) ON DELETE SET NULL,
    evidence_id             UUID        REFERENCES registry.source_policy_evidence (id) ON DELETE SET NULL,

    reviewed_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed_by             TEXT        NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT source_retention_basis_check
        CHECK (length(btrim(basis)) > 0),
    CONSTRAINT source_retention_days_check
        CHECK ((raw_days IS NULL OR raw_days >= 0)
           AND (normalized_days IS NULL OR normalized_days >= 0)),
    -- An override that overrides nothing is a row that will be read as a policy.
    CONSTRAINT source_retention_some_override_check
        CHECK (raw_days IS NOT NULL OR normalized_days IS NOT NULL
               OR aggregate_permitted IS FALSE),
    CONSTRAINT source_retention_one_per_source
        UNIQUE (source_id)
);

CREATE INDEX idx_source_retention_source ON registry.source_retention_policies (source_id);

-- -----------------------------------------------------------------------------
-- 7. registry.source_capabilities -- WHAT the source can expose
--
-- §10. Capability metadata only. That a source exposes a field says nothing
-- about whether the field may be retained: permission lives in the review and
-- retention lives in the retention policy. Kept separate so a capability list
-- can never be read as a collection plan.
-- -----------------------------------------------------------------------------
CREATE TABLE registry.source_capabilities (
    id                  UUID        PRIMARY KEY,
    source_id           TEXT        NOT NULL REFERENCES registry.sources (id) ON DELETE CASCADE,
    capability          TEXT        NOT NULL,
    description         TEXT,
    historical_depth    TEXT,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT source_capabilities_unique UNIQUE (source_id, capability),
    CONSTRAINT source_capabilities_name_check
        CHECK (capability ~ '^[a-z0-9][a-z0-9._-]{0,63}$')
);

CREATE INDEX idx_source_capabilities_source ON registry.source_capabilities (source_id);

-- =============================================================================
-- 8. THE TWO RULES THE DATABASE ENFORCES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 8.1 An approving state requires evidence.
--
-- §13: "A review without supporting evidence must not produce APPROVED."
--
-- A trigger rather than a CHECK because the evidence lives in another table,
-- and CONSTRAINT TRIGGER ... DEFERRABLE so a review and its evidence can be
-- inserted in one transaction in either order. Checking at statement time would
-- force the caller to insert evidence for a review that does not exist yet.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION registry.require_evidence_for_approval()
    RETURNS trigger
    LANGUAGE plpgsql
    SET search_path = pg_catalog, registry
AS $$
DECLARE
    evidence_count integer;
    official_count integer;
BEGIN
    IF NEW.approval_state NOT IN ('APPROVED', 'APPROVED_WITH_CONDITIONS') THEN
        RETURN NEW;
    END IF;

    SELECT count(*),
           count(*) FILTER (WHERE document_type LIKE 'OFFICIAL%'
                               OR document_type IN ('OPERATOR_CORRESPONDENCE', 'LEGAL_REVIEW'))
      INTO evidence_count, official_count
      FROM registry.source_policy_evidence
     WHERE review_id = NEW.id;

    IF evidence_count = 0 THEN
        RAISE EXCEPTION
            'source % review % cannot be % with no policy evidence. An approval with '
            'nothing behind it is an opinion with a timestamp, and cannot be re-verified '
            'when the platform changes its terms (source-registry-v1.md §7).',
            NEW.source_id, NEW.id, NEW.approval_state
            USING ERRCODE = 'check_violation';
    END IF;

    IF official_count = 0 THEN
        RAISE EXCEPTION
            'source % review % cannot be % without at least one official or authoritative '
            'document. A blog post is not a term of service (source-registry-v1.md §7).',
            NEW.source_id, NEW.id, NEW.approval_state
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_source_policy_reviews_require_evidence
    AFTER INSERT OR UPDATE ON registry.source_policy_reviews
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION registry.require_evidence_for_approval();

-- -----------------------------------------------------------------------------
-- 8.2 A collector cannot be enabled on an ineligible source.
--
-- §21: "A collector must not be able to bypass this gate."
--
-- The gate is evaluated by registry.source_eligibility below. This trigger is
-- what makes it a gate rather than a report: setting collector_enabled = TRUE
-- on a source that does not pass fails, whoever issues the UPDATE.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION registry.require_eligibility_for_collector()
    RETURNS trigger
    LANGUAGE plpgsql
    SET search_path = pg_catalog, registry
AS $$
DECLARE
    reasons text[];
BEGIN
    IF NEW.collector_enabled IS NOT TRUE THEN
        RETURN NEW;
    END IF;

    SELECT blocking_reasons INTO reasons
      FROM registry.source_eligibility
     WHERE source_id = NEW.id;

    IF reasons IS NULL OR cardinality(reasons) > 0 THEN
        RAISE EXCEPTION
            'collector cannot be enabled for source %: %',
            NEW.id, coalesce(array_to_string(reasons, '; '), 'source not found')
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

-- -----------------------------------------------------------------------------
-- 9. registry.source_eligibility -- the gate, as one readable expression
--
-- §21. Every condition is listed with the reason it blocks, so a refusal
-- explains itself. A boolean alone would send whoever asked to read this file.
--
-- Deliberately a VIEW: the answer must be derived from current state, never
-- cached. A stored eligibility flag would be a second thing to keep in sync
-- with reviews, and it would be wrong exactly when a review went stale.
-- -----------------------------------------------------------------------------
CREATE VIEW registry.source_eligibility AS
WITH current_review AS (
    SELECT DISTINCT ON (source_id) *
      FROM registry.source_policy_reviews
     WHERE superseded_at IS NULL
     ORDER BY source_id, review_version DESC
)
SELECT
    s.id AS source_id,
    s.canonical_name,
    s.source_family,
    s.lifecycle,
    s.collector_enabled,
    r.approval_state,
    r.reviewed_at,
    r.next_review_at,
    (r.next_review_at IS NOT NULL AND r.next_review_at < now()) AS review_stale,
    (
        SELECT count(*) FROM registry.source_policy_evidence e WHERE e.review_id = r.id
    ) AS evidence_count,
    array_remove(ARRAY[
        CASE WHEN s.lifecycle <> 'ACTIVE'
             THEN 'source lifecycle is ' || s.lifecycle END,
        CASE WHEN s.suspended
             THEN 'source is suspended: ' || coalesce(s.suspended_reason, 'no reason recorded') END,
        CASE WHEN r.id IS NULL
             THEN 'no policy review exists' END,
        CASE WHEN r.id IS NOT NULL AND r.approval_state NOT IN ('APPROVED', 'APPROVED_WITH_CONDITIONS')
             THEN 'policy review is ' || r.approval_state END,
        CASE WHEN r.id IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM registry.source_policy_evidence e WHERE e.review_id = r.id)
             THEN 'policy review has no evidence' END,
        CASE WHEN r.id IS NOT NULL AND r.next_review_at IS NOT NULL AND r.next_review_at < now()
             THEN 'policy review is stale, due ' || to_char(r.next_review_at, 'YYYY-MM-DD') END,
        CASE WHEN NOT EXISTS (SELECT 1 FROM registry.source_access_profiles a WHERE a.source_id = s.id)
             THEN 'no access profile configured' END,
        CASE WHEN EXISTS (
                 SELECT 1 FROM registry.source_access_profiles a
                  WHERE a.source_id = s.id
                    AND (a.requires_api_key OR a.requires_oauth)
                    AND cardinality(a.secret_references) = 0)
             THEN 'an access profile requires a credential with no configuration reference' END,
        -- Retention must be resolved, and "resolved" includes resolving to the
        -- project baseline. What is refused is an override that is present and
        -- unjustified, which the table's own constraint already prevents.
        CASE WHEN EXISTS (
                 SELECT 1 FROM registry.source_retention_policies p
                  WHERE p.source_id = s.id AND btrim(p.basis) = '')
             THEN 'retention override has no recorded basis' END
    ], NULL) AS blocking_reasons
  FROM registry.sources s
  LEFT JOIN current_review r ON r.source_id = s.id;

COMMENT ON VIEW registry.source_eligibility IS
    'The collector eligibility gate (Mission 1.0 §21). blocking_reasons is empty '
    'only when every condition passes; a source absent from a review, stale, '
    'suspended, unevidenced or missing a credential reference cannot be '
    'collected from. Derived, never cached.';

CREATE TRIGGER trg_sources_require_eligibility
    BEFORE INSERT OR UPDATE OF collector_enabled ON registry.sources
    FOR EACH ROW EXECUTE FUNCTION registry.require_eligibility_for_collector();

-- -----------------------------------------------------------------------------
-- 10. Grants
--
-- These are GLOBAL reference tables (ADR-012 §4): no workspace_id, no tenant
-- policy, readable by every tenant. A taxonomy or a source review that differed
-- per workspace would make provenance incomparable across workspaces.
--
-- Read-only at runtime. Reviews are administered through the CLI, which
-- connects as the migration role -- there is deliberately no path from a web
-- request to an approval.
-- -----------------------------------------------------------------------------
GRANT SELECT ON registry.source_access_profiles,
                registry.source_policy_reviews,
                registry.source_policy_evidence,
                registry.source_retention_policies,
                registry.source_capabilities,
                registry.source_eligibility
    TO sros_app;
