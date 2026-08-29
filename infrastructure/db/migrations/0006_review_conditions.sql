-- =============================================================================
-- 0006_review_conditions.sql -- conditions that can actually be checked
--
-- Mission 1.3 §24. Three sources became APPROVED_WITH_CONDITIONS in this
-- mission, which exposed a gap the earlier model could not close.
--
-- THE GAP (documented before the migration, per §45)
--
-- `registry.source_policy_reviews.conditions` is `TEXT[]` -- prose. It records
-- what a reviewer wrote, and nothing can evaluate it. That was adequate while
-- every review was blocking anyway: a source with no approving state never
-- reached the point where its conditions mattered.
--
-- It stops being adequate the moment a review IS approving. §24 requires that
-- APPROVED_WITH_CONDITIONS must not silently mean "collector may run", and the
-- only way to enforce that is for each condition to be individually
-- representable and individually satisfiable. A sentence in an array cannot be
-- marked satisfied, cannot say WHO satisfied it, and cannot be checked by the
-- eligibility gate.
--
-- The prose column is NOT removed. It stays as the reviewer's own summary,
-- which is worth keeping: the structured rows are what the machine checks, the
-- prose is what a human reads.
--
-- WHAT THIS DOES NOT DO
--
--   * it does not make any source collector-eligible. Every condition created
--     here starts UNSATISFIED, and three of the five verification kinds cannot
--     be satisfied at all until a collector exists;
--   * it does not encode legal prose as executable logic. A condition names a
--     MECHANICAL fact -- a config key is present, a capability is enabled, a
--     retention limit is configured -- or it is marked HUMAN_CONFIRMATION and
--     stays a human's decision (§24).
-- =============================================================================

CREATE TABLE registry.source_review_conditions (
    id                      UUID        PRIMARY KEY,
    review_id               UUID        NOT NULL
        REFERENCES registry.source_policy_reviews (id) ON DELETE CASCADE,
    source_id               TEXT        NOT NULL
        REFERENCES registry.sources (id) ON DELETE CASCADE,

    -- Stable across review versions, so "the attribution condition" can be
    -- followed from one review to the next rather than looking like a new
    -- requirement every time a review is redone.
    condition_key           TEXT        NOT NULL,

    -- What must be true, in words, for a human reading the registry.
    description             TEXT        NOT NULL,

    -- HOW it can be checked. This is the field that keeps §24 honest: a
    -- condition that cannot be mechanically verified must say so rather than
    -- pretending, and HUMAN_CONFIRMATION is a real answer.
    verification            TEXT        NOT NULL,

    -- What the verification looks at: a configuration key name, a capability
    -- name, a number of days, or the reference to a recorded human decision.
    -- Never a credential value -- the registry is not a vault (Mission 1.0 §18).
    verification_detail     TEXT,

    -- Environment state, not catalog state. The catalog DECLARES conditions;
    -- whether they hold depends on what is deployed and configured, which is
    -- why a catalog load must never be able to set this true.
    satisfied               BOOLEAN     NOT NULL DEFAULT FALSE,
    satisfied_at            TIMESTAMPTZ,
    satisfied_by            TEXT,
    satisfaction_reference  TEXT,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT source_review_conditions_verification_check
        CHECK (verification IN ('CONFIG_REFERENCE', 'CAPABILITY', 'RETENTION_LIMIT',
                                'ACCESS_METHOD', 'HUMAN_CONFIRMATION')),
    CONSTRAINT source_review_conditions_key_not_blank_check
        CHECK (length(btrim(condition_key)) > 0),
    CONSTRAINT source_review_conditions_description_not_blank_check
        CHECK (length(btrim(description)) > 0),
    -- A satisfied condition must say who decided that and when. "Satisfied by
    -- nobody, at no time" is the shape an accidental UPDATE leaves behind.
    CONSTRAINT source_review_conditions_satisfaction_provenance_check
        CHECK (NOT satisfied OR (satisfied_at IS NOT NULL AND satisfied_by IS NOT NULL)),
    CONSTRAINT source_review_conditions_unique UNIQUE (review_id, condition_key)
);

COMMENT ON TABLE registry.source_review_conditions IS
    'Individually checkable conditions attached to an approving review. '
    'APPROVED_WITH_CONDITIONS does not mean a collector may run: every '
    'condition must be satisfied first, and the eligibility view enforces it.';

CREATE INDEX idx_review_conditions_review
    ON registry.source_review_conditions (review_id);

CREATE INDEX idx_review_conditions_source
    ON registry.source_review_conditions (source_id, satisfied);

GRANT SELECT ON registry.source_review_conditions TO sros_app;

-- -----------------------------------------------------------------------------
-- The eligibility view gains one blocking reason.
--
-- Rebuilt rather than altered: a view cannot have a column list changed in
-- place, and rewriting it whole keeps the whole rule readable in one place
-- instead of split across two migrations.
-- -----------------------------------------------------------------------------
DROP VIEW registry.source_eligibility;

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
        CASE WHEN EXISTS (
                 SELECT 1 FROM registry.source_retention_policies p
                  WHERE p.source_id = s.id AND length(btrim(p.basis)) = 0)
             THEN 'retention override has no recorded basis' END,
        -- NEW in Mission 1.3. An approving review whose conditions are not all
        -- satisfied blocks, which is what stops APPROVED_WITH_CONDITIONS from
        -- silently meaning "collector may run" (§24).
        CASE WHEN r.id IS NOT NULL AND EXISTS (
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
LEFT JOIN current_review r ON r.source_id = s.id;

-- Re-granted. DROP VIEW discards the view's privileges along with the view, and
-- migration 0004 granted SELECT on it to sros_app. Without this line the runtime
-- role silently loses the ability to read its own eligibility gate -- which the
-- orchestrator does on every plan, and which failed exactly that way once.
GRANT SELECT ON registry.source_eligibility TO sros_app;

COMMENT ON VIEW registry.source_eligibility IS
    'Derived collector eligibility. An empty blocking_reasons array is the pass. '
    'Never a stored flag: a boolean can drift away from the reasons behind it.';
