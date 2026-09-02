-- =============================================================================
-- 0027 — external model transmission (source activity) and egress (use profile)
--
-- Mission 1.23, ADR-033. TWO columns and no new table.
--
-- WHY A MIGRATION AT ALL. `registry.source_policy_reviews` carries one column
-- per assessed activity and `registry.use_profiles` one per profile property,
-- so a contract that grew a field cannot be loaded until the tables have
-- somewhere to put it. The loader failed with `column
-- "external_model_transmission" does not exist`, which is the schema doing its
-- job rather than a defect.
--
-- WHY TWO COLUMNS AND NOT ONE. They answer different questions and belong to
-- different subjects:
--
--   source_policy_reviews.external_model_transmission
--       may THIS SOURCE's material undergo the activity?  A review fact.
--   use_profiles.external_model_egress
--       does THIS DEPLOYMENT permit that class of egress at all?  A profile fact.
--
-- Runtime authorization requires BOTH, and neither substitutes for the other: a
-- permissive source cannot rescue a silent deployment, and a permissive
-- deployment cannot replace a source review.
--
-- WHY `model_processing` IS UNTOUCHED. It asks whether a model may READ the
-- material and every existing answer to it stays true. The new column asks
-- whether the material may LEAVE the deployment so that a third party's model
-- can read it. Reinterpreting the old column to mean the new thing would grant
-- twenty-nine sources a permission nobody assessed.
--
-- HOW HISTORY IS PRESERVED. Both columns are NULLABLE with NO default, and NO
-- existing row is written. A NULL review column reads as NOT_ASSESSED -- nobody
-- looked -- which is true, and is distinguishable from PERMITTED and from
-- NOT_PERMITTED. A mass UPDATE to any value would be inventing sixty-four
-- answers.
--
-- WHAT THIS DOES NOT DO. It authorises nothing. It gives the model somewhere to
-- record an answer; the answers are review acts, and Mission 1.23 performs one
-- of them for one source and one profile.
--
-- Forward-only. Columns are added, never dropped, so no stored row becomes
-- invalid and no earlier migration is edited.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. The source activity
--
-- NULLABLE ON PURPOSE. Every review written before ADR-033 keeps a NULL here and
-- reads as NOT_ASSESSED, which is exactly what happened: the contract had no
-- slot, so no reviewer could have answered.
-- -----------------------------------------------------------------------------

ALTER TABLE registry.source_policy_reviews
    ADD COLUMN IF NOT EXISTS external_model_transmission TEXT;

COMMENT ON COLUMN registry.source_policy_reviews.external_model_transmission IS
    'Whether material derived from this source may be transmitted OUTSIDE the '
    'local deployment to a third-party model processor (ADR-033). Distinct from '
    'model_processing, which asks whether a model may READ the material: those '
    'are different acts with different exposure, and until this column existed '
    'no review could scope itself to a location. NULL means NOT_ASSESSED -- '
    'nobody looked -- and is deliberately distinguishable from an explicit '
    'permission or refusal. NOT one of rule 8''s materially required activities: '
    'it gates ONE operation, so a deterministic acquisition never fails because '
    'nobody assessed model egress for its source.';

-- -----------------------------------------------------------------------------
-- 2. The deployment posture
--
-- Three states rather than a boolean, because `false` would conflate DECIDED
-- AGAINST with NEVER ASKED -- the two states this registry spends most of its
-- care keeping apart. NULL is read as NOT_ASSESSED and refuses.
-- -----------------------------------------------------------------------------

ALTER TABLE registry.use_profiles
    ADD COLUMN IF NOT EXISTS external_model_egress TEXT;

ALTER TABLE registry.use_profiles
    DROP CONSTRAINT IF EXISTS use_profiles_external_model_egress_check;

ALTER TABLE registry.use_profiles
    ADD CONSTRAINT use_profiles_external_model_egress_check
        CHECK (external_model_egress IS NULL OR external_model_egress IN (
            'NOT_ASSESSED',
            'DENIED',
            'PERMITTED_TO_APPROVED_PROVIDERS'
        ));

COMMENT ON COLUMN registry.use_profiles.external_model_egress IS
    'What this DEPLOYMENT permits by way of sending source-derived content to a '
    'third-party model processor (ADR-033). `model_inference` says the ACTIVITY '
    'is in scope and `deployment` says where SROS runs; neither says where '
    'inference RUNS, which is the gap this column closes. NOT_ASSESSED and '
    'DENIED both refuse, and the distinction between them is why this is not a '
    'boolean: one is a decision, the other is a question nobody asked. A LOCAL '
    'inference provider would need model_inference and NOT this, which is the '
    'clearest statement of why they are two fields.';
