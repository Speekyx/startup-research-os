-- =============================================================================
-- 0021 — Use-profile-scoped source policy (Mission 1.15.5, ADR-027)
--
-- Every policy review has always answered a question about a USE. The catalog
-- stated it in prose at the top and every review inherited it; what it never
-- had was an IDENTITY, so the question could not be compared, required or
-- matched, and the eligibility gate never saw it.
--
-- After this migration a review's subject is a column, currentness is scoped to
-- (source, profile), and a source may honestly hold REQUIRES_REVIEW under one
-- use and APPROVED_WITH_CONDITIONS under another without contradiction.
--
-- NO VERDICT, ASSESSMENT, CONDITION, EVIDENCE ROW OR REVIEW VERSION CHANGES
-- HERE. Attaching a profile to history is a migration interpretation of what
-- those reviews assessed, not a new policy conclusion — and the interpretation
-- is not a guess: `assessed_use_case` has said "a COMMERCIAL multi-tenant SaaS"
-- on every review since Mission 1.0.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- 1. The registered profiles.
--
-- A table rather than a CHECK constraint, because a profile carries semantics a
-- reviewer has to read — what deployment, whose customers, whether raw data
-- leaves the machine — and a list of bare strings would leave the reviewer
-- guessing what they were approving for.
--
-- Not a closed enum, because we do not branch exhaustively on it; we compare it
-- (docs/CLAUDE.md §Taxonomies). Adding a profile is a governance act, not a
-- migration.
-- -----------------------------------------------------------------------------
CREATE TABLE registry.use_profiles (
    id              TEXT        PRIMARY KEY,
    name            TEXT        NOT NULL,
    description     TEXT        NOT NULL,
    semantic_version INTEGER    NOT NULL DEFAULT 1,
    status          TEXT        NOT NULL DEFAULT 'ACTIVE',

    -- What the profile asserts about the use. Every one of these is a fact a
    -- reviewer needs in order to know what they are approving.
    deployment                    TEXT    NOT NULL,
    operator_scope                TEXT    NOT NULL,
    public_access                 BOOLEAN NOT NULL,
    external_customers            BOOLEAN NOT NULL,
    raw_redistribution            BOOLEAN NOT NULL,
    raw_resale                    BOOLEAN NOT NULL,
    customer_facing_source_access BOOLEAN NOT NULL,
    derived_internal_analysis     BOOLEAN NOT NULL,
    -- TRUE on BOTH registered profiles, and deliberately so: running locally
    -- does not make the use non-commercial, and a commercial-use right still
    -- has to be granted by the source's own evidence (docs/CLAUDE.md
    -- §Deployment model).
    commercial_purpose            BOOLEAN NOT NULL,
    model_inference               BOOLEAN NOT NULL,
    model_training                BOOLEAN NOT NULL,
    embeddings                    BOOLEAN NOT NULL,
    personal_data_posture         TEXT    NOT NULL,
    notes                         TEXT,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- The id carries its own semantic version, so a changed meaning is a
    -- changed identity and no existing review silently follows it.
    CONSTRAINT use_profiles_id_pattern_check
        CHECK (id ~ '^[a-z][a-z0-9-]*-v[0-9]+$'),
    CONSTRAINT use_profiles_status_check
        CHECK (status IN ('ACTIVE', 'RETIRED')),
    CONSTRAINT use_profiles_described_check
        CHECK (btrim(name) <> '' AND btrim(description) <> '')
);

COMMENT ON TABLE registry.use_profiles IS
    'What the system does with a source — the subject of a policy review '
    '(Mission 1.15.5, ADR-027). Not a deployment environment: development and '
    'production say where code runs, a profile says what is being done with '
    'somebody else''s data, and the same binary can be operated under either.';

INSERT INTO registry.use_profiles (
    id, name, description, deployment, operator_scope,
    public_access, external_customers, raw_redistribution, raw_resale,
    customer_facing_source_access, derived_internal_analysis, commercial_purpose,
    model_inference, model_training, embeddings, personal_data_posture, notes
) VALUES
(
    'commercial-multi-tenant-research-v1',
    'Commercial multi-tenant research',
    'Startup Research OS operated as a COMMERCIAL, MULTI-TENANT, customer-facing '
    'service: automated collection of public content for storage, derived analytics '
    'and LLM processing to produce opportunity intelligence offered to external '
    'customers. The profile every review from Mission 1.0 to Mission 1.15.4 actually '
    'assessed, and the one a future public commercial deployment would have to '
    'satisfy. The WIDEST profile: nothing that fails here can be rescued by a '
    'narrower one.',
    'PUBLIC_MULTI_TENANT', 'MULTI_OPERATOR',
    TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, FALSE, FALSE, 'MINIMISED',
    'Attached to historical reviews as a migration interpretation of their scope, '
    'not as a new policy conclusion.'
),
(
    'local-private-research-v1',
    'Local private research',
    'Startup Research OS running LOCALLY for a single operator: not publicly '
    'accessible, no external customers, no redistribution or resale of source data, '
    'no customer-facing access to a source, minimised storage, official access '
    'routes only. LOCAL IS NOT NON-COMMERCIAL: the research produced is used to '
    'discover, evaluate and launch commercial products, so commercial-use rights '
    'must still be positively granted by the source''s own evidence.',
    'LOCAL', 'SINGLE_OPERATOR',
    FALSE, FALSE, FALSE, FALSE, FALSE, TRUE, TRUE, TRUE, FALSE, FALSE, 'MINIMISED',
    'A profile narrows what is done with a source. It never widens what a source '
    'permits, and an approval here never transfers to another profile.'
);

-- -----------------------------------------------------------------------------
-- 2. The review's subject.
--
-- The DEFAULT exists only to fill history in the same statement that adds the
-- column, and is dropped immediately after. A future review that did not say
-- what it assessed would otherwise inherit an answer nobody gave.
-- -----------------------------------------------------------------------------
ALTER TABLE registry.source_policy_reviews
    ADD COLUMN assessed_use_profile TEXT NOT NULL
        DEFAULT 'commercial-multi-tenant-research-v1';

ALTER TABLE registry.source_policy_reviews
    ALTER COLUMN assessed_use_profile DROP DEFAULT;

ALTER TABLE registry.source_policy_reviews
    ADD CONSTRAINT source_policy_reviews_use_profile_fk
        FOREIGN KEY (assessed_use_profile) REFERENCES registry.use_profiles (id);

COMMENT ON COLUMN registry.source_policy_reviews.assessed_use_profile IS
    'WHICH use this review answered about. A verdict with no subject cannot be '
    'transferred, compared or refused correctly, which is why it is NOT NULL and '
    'why the default was dropped the moment history was filled.';

-- -----------------------------------------------------------------------------
-- 3. Currentness is per (source, profile).
--
-- The old uniqueness was (source_id, review_version), which would have made
-- version 1 under a second profile collide with version 1 under the first. Each
-- profile keeps its own append-only version line.
-- -----------------------------------------------------------------------------
ALTER TABLE registry.source_policy_reviews
    DROP CONSTRAINT source_policy_reviews_version_unique;

ALTER TABLE registry.source_policy_reviews
    ADD CONSTRAINT source_policy_reviews_version_unique
        UNIQUE (source_id, assessed_use_profile, review_version);

DROP INDEX IF EXISTS registry.idx_source_policy_reviews_current;
CREATE INDEX idx_source_policy_reviews_current
    ON registry.source_policy_reviews (source_id, assessed_use_profile)
 WHERE superseded_at IS NULL;

-- -----------------------------------------------------------------------------
-- 4. The operational switch names the use it was flipped for.
--
-- `collector_enabled` says "turned on"; it never said turned on FOR WHAT. With
-- two profiles that is no longer answerable by inspection, and a switch whose
-- scope is ambiguous is a switch that grants the widest reading.
-- -----------------------------------------------------------------------------
ALTER TABLE registry.sources
    ADD COLUMN collector_use_profile TEXT
        REFERENCES registry.use_profiles (id);

-- Backfill BEFORE the constraint: any source already enabled was enabled under
-- the only profile that existed, and the check would otherwise refuse the very
-- rows this migration exists to describe.
UPDATE registry.sources
   SET collector_use_profile = 'commercial-multi-tenant-research-v1'
 WHERE collector_enabled IS TRUE;

ALTER TABLE registry.sources
    ADD CONSTRAINT sources_collector_profile_required_check
        CHECK (collector_enabled IS NOT TRUE OR collector_use_profile IS NOT NULL);

COMMENT ON COLUMN registry.sources.collector_use_profile IS
    'The use profile a collector is enabled FOR. Required whenever '
    'collector_enabled is true: an operational switch with no stated scope is a '
    'switch that grants the widest one.';

-- -----------------------------------------------------------------------------
-- 5. The gate, one row per (source, profile).
--
-- Still a VIEW, still derived, still never cached — and now it cannot be read
-- without saying which use is being asked about. A source with no review under
-- a profile does not appear for that profile at all, and a caller that finds no
-- row has found a refusal.
-- -----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_sources_require_eligibility ON registry.sources;
DROP VIEW IF EXISTS registry.source_eligibility;

CREATE VIEW registry.source_eligibility AS
WITH current_review AS (
    SELECT DISTINCT ON (source_id, assessed_use_profile) *
      FROM registry.source_policy_reviews
     WHERE superseded_at IS NULL
     ORDER BY source_id, assessed_use_profile, review_version DESC
)
SELECT
    s.id AS source_id,
    r.assessed_use_profile AS use_profile_id,
    s.canonical_name,
    s.source_family,
    s.lifecycle,
    s.collector_enabled,
    s.collector_use_profile,
    r.approval_state,
    r.reviewed_at,
    r.next_review_at,
    (r.next_review_at IS NOT NULL AND r.next_review_at < now()) AS review_stale,
    (
        SELECT count(*) FROM registry.source_policy_evidence e WHERE e.review_id = r.id
    ) AS evidence_count,
    (
        SELECT count(*) FROM registry.source_review_conditions c
         WHERE c.review_id = r.id
    ) AS condition_count,
    (
        SELECT count(*) FROM registry.source_review_conditions c
         WHERE c.review_id = r.id AND NOT c.satisfied
    ) AS unsatisfied_condition_count,
    array_remove(ARRAY[
        CASE WHEN s.lifecycle <> 'ACTIVE'
             THEN 'source lifecycle is ' || s.lifecycle END,
        CASE WHEN s.suspended
             THEN 'source is suspended: ' || coalesce(s.suspended_reason, 'no reason recorded') END,
        CASE WHEN r.approval_state NOT IN ('APPROVED', 'APPROVED_WITH_CONDITIONS')
             THEN 'policy review for use profile ' || quote_literal(r.assessed_use_profile)
                  || ' is ' || r.approval_state END,
        CASE WHEN NOT EXISTS (
                 SELECT 1 FROM registry.source_policy_evidence e WHERE e.review_id = r.id)
             THEN 'policy review has no evidence' END,
        CASE WHEN r.next_review_at IS NOT NULL AND r.next_review_at < now()
             THEN 'policy review is stale, due ' || to_char(r.next_review_at, 'YYYY-MM-DD') END,
        CASE WHEN NOT EXISTS (SELECT 1 FROM registry.source_access_profiles a WHERE a.source_id = s.id)
             THEN 'no access profile configured' END,
        CASE WHEN EXISTS (
                 SELECT 1 FROM registry.source_access_profiles a
                  WHERE a.source_id = s.id
                    AND (a.requires_api_key OR a.requires_oauth)
                    AND cardinality(a.secret_references) = 0)
             THEN 'an access profile requires a credential with no configuration reference' END,
        CASE WHEN EXISTS (
                 SELECT 1 FROM registry.source_retention_policies p
                  WHERE p.source_id = s.id AND length(btrim(p.basis)) = 0)
             THEN 'retention override has no recorded basis' END,
        -- Mission 1.3 §24, carried forward unchanged: an approving review whose
        -- conditions are not all satisfied still blocks. Rebuilding the view for
        -- profiles must not quietly drop the rule that makes
        -- APPROVED_WITH_CONDITIONS mean something.
        CASE WHEN EXISTS (
                 SELECT 1 FROM registry.source_review_conditions c
                  WHERE c.review_id = r.id AND NOT c.satisfied)
             THEN (
                 SELECT 'review conditions not satisfied: '
                        || string_agg(c.condition_key, ', ' ORDER BY c.condition_key)
                   FROM registry.source_review_conditions c
                  WHERE c.review_id = r.id AND NOT c.satisfied
             ) END
    ], NULL) AS blocking_reasons
  FROM registry.sources s
  JOIN current_review r ON r.source_id = s.id;

-- Re-granted, for the reason migration 0006 wrote down: DROP VIEW discards the
-- view's privileges along with the view, and the runtime role reads this gate on
-- every plan. It failed exactly that way once.
GRANT SELECT ON registry.source_eligibility TO sros_app;

COMMENT ON VIEW registry.source_eligibility IS
    'The collector eligibility gate, one row per (source, use profile) since '
    'Mission 1.15.5. blocking_reasons is empty only when every condition passes. '
    'A source with no review under a profile has NO ROW for it, and an absent row '
    'is a refusal -- never a reason to consult another profile. Derived, never '
    'cached.';

-- -----------------------------------------------------------------------------
-- 6. The trigger asks about the profile the switch was flipped for.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION registry.require_eligibility_for_collector()
    RETURNS trigger
    LANGUAGE plpgsql
    SET search_path = pg_catalog, registry
AS $$
DECLARE
    reasons text[];
    found   boolean;
BEGIN
    IF NEW.collector_enabled IS NOT TRUE THEN
        RETURN NEW;
    END IF;

    IF NEW.collector_use_profile IS NULL THEN
        RAISE EXCEPTION
            'collector cannot be enabled for source %: no use profile declared',
            NEW.id
            USING ERRCODE = 'check_violation';
    END IF;

    SELECT blocking_reasons, TRUE INTO reasons, found
      FROM registry.source_eligibility
     WHERE source_id = NEW.id
       AND use_profile_id = NEW.collector_use_profile;

    IF found IS NOT TRUE OR cardinality(reasons) > 0 THEN
        RAISE EXCEPTION
            'collector cannot be enabled for source % under use profile %: %',
            NEW.id, NEW.collector_use_profile,
            coalesce(array_to_string(reasons, '; '), 'no review for that use profile')
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_sources_require_eligibility
    BEFORE INSERT OR UPDATE OF collector_enabled, collector_use_profile ON registry.sources
    FOR EACH ROW EXECUTE FUNCTION registry.require_eligibility_for_collector();

COMMIT;
