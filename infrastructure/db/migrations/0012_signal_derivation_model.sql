-- =============================================================================
-- 0012_signal_derivation_model.sql -- a Signal is a DERIVATION, not a label
--
-- Mission 1.11. Governed by docs/data/signal-model-gap-analysis-v1.md (written
-- BEFORE this file, per §32), docs/data/signal-contract-v1.md and ADR-020.
--
-- WHY THE EXISTING TABLE COULD NOT BE KEPT
--
-- `nlp.signals` was created in Mission 0.1, before any source existed, and it
-- encodes three assumptions that the two sources which now exist all falsify:
--
--   1. a signal comes from exactly ONE normalized record  -> one nullable FK
--   2. a signal is a DEMAND signal                        -> PAIN/DESIRE/...
--   3. a signal is produced by a LANGUAGE MODEL           -> model_version,
--                                                            prompt_version, and
--                                                            no extractor id
--
-- Plus one arithmetic problem: `value DOUBLE PRECISION CHECK (value BETWEEN 0
-- AND 1)` cannot hold a change from 55 to 81, and is a float in a system that
-- parses source numbers with `parse_float=Decimal` precisely so IEEE-754 never
-- touches them.
--
-- The table is EMPTY, nothing writes to it and nothing reads it. Migration 0005
-- made the same correction to `scoring.evidence` and said the thing worth
-- repeating: this is the cheapest it will ever be.
--
-- WHAT THIS FILE DOES NOT DO
--
-- No extractor exists and no Signal is created. This migration makes a Signal
-- REPRESENTABLE; `nlp.signals` still holds 0 rows afterwards, and it must.
--
-- Two pre-existing defects are closed on the way past, and both are named in the
-- gap analysis rather than smuggled in: `scoring.evidence.signal_id` was not
-- tenant-safe (GAP-12), and the signal type registry had no entries any
-- migration wrote (GAP-13) -- which made this table unwritable on the empty
-- database CI and every real deployment start from.
--
-- Forward-only. Never edited after it has been applied anywhere.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. The signal_type registry (GAP-13, signal-taxonomy-v1.md §4)
--
-- Written HERE, not in a seed. `signal_type_registry` defaulted to
-- `demand_signal_type`, whose only two entries live in
-- `infrastructure/db/seed/0002_registry_seed.sql` -- development-only, and run
-- AFTER every migration. So an INSERT into nlp.signals succeeded on a
-- developer's seeded machine and failed everywhere else. `validate_schema.py`
-- catches a MIGRATION that depends on a seed; it does not catch a table whose
-- RUNTIME WRITES do.
--
-- Two entries, each justified by records this repository currently holds
-- (Mission 1.11 §35). A registry row is VOCABULARY: it lets the model describe
-- a shape and lets this table refuse a type nobody registered. The claim that
-- CODE exists is `SIGNAL_EXTRACTORS`, and it is empty.
-- -----------------------------------------------------------------------------
INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('signal_type', 'lexical_frequency_contrast', 'Lexical frequency contrast',
     'The relation between the frequencies of two or more lexical terms observed '
     'under one identical source period label and one identical source language '
     'label. Says how often tokens occurred in text the source processed, and '
     'nothing about attention, interest or demand (signal-taxonomy-v1.md §4).'),
    ('signal_type', 'numeric_period_change', 'Numeric period change',
     'The change in one metric, for one geography, between two periods placed on '
     'a common timeline. A measurement moved; whether that is a market event is a '
     'later stage''s question (signal-taxonomy-v1.md §4).')
ON CONFLICT (registry, id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 2. Composite keys the child references need
--
-- `raw_records` gained one in migration 0009 for the same reason. A composite
-- foreign key needs a composite unique target, and without it a cross-tenant
-- link is rejected at runtime by a repository filter rather than being
-- impossible to write (ADR-012, §31 of the normalized-record gap analysis).
-- -----------------------------------------------------------------------------
ALTER TABLE acquisition.normalized_records
    ADD CONSTRAINT normalized_records_workspace_id_key UNIQUE (workspace_id, id);

ALTER TABLE nlp.signals
    ADD CONSTRAINT signals_workspace_id_key UNIQUE (workspace_id, id);

-- -----------------------------------------------------------------------------
-- 3. nlp.signals -- reshaped
-- -----------------------------------------------------------------------------

-- GAP-2. The family classified DEMAND. Neither derivation the two real sources
-- support is a demand signal: a contrast between two GDELT term frequencies may
-- equally be a news event, a crisis, a celebrity, weather, politics, a disaster
-- or a sports fixture, and a World Bank population delta is a demographic
-- measurement. Forcing either into MARKET puts an interpretation in the one
-- field a consumer branches on.
--
-- RENAMED rather than re-CHECKed in place: three different things were called
-- "signal family" -- the demand enum, the ADR-017 source-coverage registry, and
-- this. Now they have three names (signal-taxonomy-v1.md §1).
--
-- Ontology V2 §3.6 is NOT amended. The demand families remain four and closed.
-- What stops being true is the claim that every row here carries one.
ALTER TABLE nlp.signals
    RENAME COLUMN signal_family TO quantity_family;

-- GAP-15. A Signal is not collected. Its inputs were, at various times, from
-- possibly several sources, so a single `collected_at` on the derived row has no
-- referent. `normalized_records` already anchors its retention CHECK on
-- `normalized_at` for the same reason.
ALTER TABLE nlp.signals
    RENAME COLUMN collected_at TO derived_at;

-- Renamed for precision, not rescaled. It is confidence that this DERIVATION
-- computed what it says it computed -- not that the phenomenon is real, not an
-- evidence strength, not an EvidenceScore input. A deterministic extractor's is
-- 1.0, and that is a statement about arithmetic (signal-contract-v1.md §12).
ALTER TABLE nlp.signals
    RENAME COLUMN confidence TO derivation_confidence;

ALTER TABLE nlp.signals
    DROP CONSTRAINT signals_family_check,
    DROP CONSTRAINT signals_confidence_unit_interval_check,
    DROP CONSTRAINT signals_value_unit_interval_check;

-- GAP-3. The worst column in the table, for two independent reasons: bounded to
-- the unit interval, so a change from 55 to 81 does not fit; and a float, which
-- would give back at the first subtraction the exactness the normalization layer
-- exists to guarantee. NO 0-100 strength replaces it -- a GDELT term frequency
-- and a World Bank population figure are not comparable measurements, and a
-- shared scale would be a comparison manufactured by storing them together
-- (Mission 1.11 §8, §30).
ALTER TABLE nlp.signals DROP COLUMN value;

-- GAP-1. A signal derives from TWO OR MORE observations, so a single nullable
-- column could not hold one valid Signal. ON DELETE SET NULL compounded it: a
-- nulled lineage is a signal claiming to be derived from nothing.
ALTER TABLE nlp.signals DROP COLUMN normalized_record_id;

ALTER TABLE nlp.signals
    -- GAP-3.
    ADD COLUMN magnitude NUMERIC NOT NULL,
    ADD COLUMN magnitude_kind TEXT NOT NULL,
    ADD COLUMN magnitude_unit TEXT,
    ADD COLUMN magnitude_unit_state TEXT NOT NULL,

    ADD COLUMN direction TEXT NOT NULL,

    -- GAP-4. Three versions, independent on purpose: the schema changes when
    -- what a Signal MEANS changes, the extractor version when its derivation
    -- changes, the model version when a provider ships a model. One column could
    -- not carry three things that move separately.
    ADD COLUMN extractor_id TEXT NOT NULL,
    ADD COLUMN extractor_version TEXT NOT NULL,
    ADD COLUMN signal_schema_id TEXT NOT NULL DEFAULT 'sros.signal',
    ADD COLUMN signal_schema_version INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN derivation_kind TEXT NOT NULL,

    -- GAP-6. A signal is not reproducible if a value affecting its output is a
    -- hidden default (Mission 1.11 §29).
    ADD COLUMN parameters JSONB NOT NULL,
    ADD COLUMN parameter_fingerprint TEXT NOT NULL,

    -- GAP-5. Deterministic identity, so a re-run converges on the row that
    -- exists. Two rows for one derivation are indistinguishable from two
    -- independent findings, which is the one shape evidence aggregation must
    -- never be handed (evidence-aggregation-framework-v1.md §7).
    ADD COLUMN derivation_fingerprint TEXT NOT NULL,

    -- GAP-7 and GAP-8. What the signal is about, and what temporal relation it
    -- actually used. A dimension no input carries has NO KEY in `scope` -- never
    -- a null, the rule the lexical record kind already follows for geography.
    ADD COLUMN scope JSONB NOT NULL,
    ADD COLUMN temporal_basis TEXT NOT NULL,
    ADD COLUMN temporal_window JSONB NOT NULL,

    ADD COLUMN correlation_id TEXT NOT NULL,

    -- Closed enums, TEXT + CHECK (ADR-008). validate_schema.py compares each
    -- list against the contract source of truth, so a value drifting from the
    -- generated vocabulary fails the build.
    ADD CONSTRAINT signals_quantity_family_check
        CHECK (quantity_family IN ('LEXICAL_FREQUENCY', 'MEASURED_SERIES')),
    ADD CONSTRAINT signals_direction_check
        CHECK (direction IN ('INCREASING', 'DECREASING', 'UNCHANGED',
                             'INDETERMINATE', 'NOT_APPLICABLE')),
    ADD CONSTRAINT signals_magnitude_kind_check
        CHECK (magnitude_kind IN ('ABSOLUTE_CHANGE', 'RATIO', 'OBSERVATION_COUNT')),
    ADD CONSTRAINT signals_magnitude_unit_state_check
        CHECK (magnitude_unit_state IN ('INHERITED', 'DIMENSIONLESS', 'NOT_ESTABLISHED')),
    ADD CONSTRAINT signals_derivation_kind_check
        CHECK (derivation_kind IN ('DETERMINISTIC', 'MODEL_DERIVED')),

    ADD CONSTRAINT signals_derivation_confidence_unit_interval_check
        CHECK (derivation_confidence BETWEEN 0 AND 1),

    -- Mission 1.11 §23, as a constraint rather than a sentence. A Signal is not
    -- inherently LLM-generated: a DETERMINISTIC row may not carry model
    -- provenance, and a MODEL_DERIVED one may not omit it.
    ADD CONSTRAINT signals_derivation_kind_provenance_check
        CHECK (
            (derivation_kind = 'DETERMINISTIC'
             AND model_version IS NULL AND prompt_version IS NULL)
         OR (derivation_kind = 'MODEL_DERIVED' AND model_version IS NOT NULL)
        ),

    -- A unit is INHERITED from the inputs or it does not exist. GDELT publishes
    -- four columns and none is a unit, so a change over GDELT counts is
    -- NOT_ESTABLISHED -- the normalizer's own answer, carried up rather than
    -- resolved. A ratio and a count are dimensionless by construction.
    ADD CONSTRAINT signals_magnitude_unit_shape_check
        CHECK (
            (magnitude_unit_state = 'INHERITED' AND magnitude_unit IS NOT NULL)
         OR (magnitude_unit_state <> 'INHERITED' AND magnitude_unit IS NULL)
        ),
    ADD CONSTRAINT signals_dimensionless_kind_check
        CHECK (
            magnitude_kind NOT IN ('RATIO', 'OBSERVATION_COUNT')
         OR magnitude_unit_state = 'DIMENSIONLESS'
        ),

    -- H-29, enforced by the database. `observed_at` exists only where the
    -- derivation placed its inputs on a shared timeline. Every GDELT
    -- observation is PERIOD_TIMEZONE_NOT_ESTABLISHED, so this refuses a GDELT
    -- signal with an event time in the same place the normalizer refuses one.
    ADD CONSTRAINT signals_observed_at_requires_comparable_instants_check
        CHECK (observed_at IS NULL OR temporal_basis = 'COMPARABLE_INSTANTS'),
    ADD CONSTRAINT signals_temporal_basis_check
        CHECK (temporal_basis IN ('NONE', 'SAME_PERIOD_LABEL',
                                  'ORDERED_PERIODS', 'COMPARABLE_INSTANTS')),
    -- Promoted to a column because a CHECK and a query filter both read it, the
    -- way migration 0009 promoted the lineage fields an auditor filters BY. It
    -- is pinned to the serialised window so the two can never disagree: two
    -- answers to one question is how the numeric one silently wins.
    ADD CONSTRAINT signals_temporal_basis_matches_window_check
        CHECK (temporal_basis = temporal_window ->> 'basis'),

    -- "Increasing" is a statement about before and after. A derivation that
    -- established no order cannot make it -- which, while H-29 and H-32 are
    -- open, means no GDELT signal can carry a direction.
    ADD CONSTRAINT signals_direction_requires_order_check
        CHECK (
            direction = 'NOT_APPLICABLE'
         OR temporal_basis IN ('ORDERED_PERIODS', 'COMPARABLE_INSTANTS')
        ),

    ADD CONSTRAINT signals_extractor_identified_check
        CHECK (length(btrim(extractor_id)) > 0
           AND length(btrim(extractor_version)) > 0),
    ADD CONSTRAINT signals_schema_version_check
        CHECK (signal_schema_version >= 1),
    ADD CONSTRAINT signals_correlation_identified_check
        CHECK (length(btrim(correlation_id)) > 0),
    -- GAP-15. Anchored on derived_at, not on a collection time this row does not
    -- have. A record written with an expiry in the past is a retention policy
    -- that was never applied.
    ADD CONSTRAINT signals_expiry_after_derivation_check
        CHECK (expires_at > derived_at),

    -- GAP-5. Idempotency: the same inputs, extractor, parameters and window
    -- converge on one row. The row id is a UUIDv5 over the same material, so a
    -- re-run does not even attempt a parallel insert.
    ADD CONSTRAINT signals_derivation_unique
        UNIQUE (workspace_id, derivation_fingerprint),

    -- Tenant-safe session link. COLUMN-SPECIFIC ON DELETE SET NULL: a
    -- multi-column SET NULL nulls every referencing column including
    -- workspace_id, which is NOT NULL, so deleting a session would fail rather
    -- than detach the signal. Migrations 0005 and 0009 hit the same thing.
    ADD CONSTRAINT signals_session_tenant_fkey
        FOREIGN KEY (workspace_id, research_session_id)
        REFERENCES research.research_sessions (workspace_id, id)
        ON DELETE SET NULL (research_session_id);

-- GAP-13. The registry a signal type comes from. `demand_signal_type`
-- classifies demand; a signal type says what was derived.
ALTER TABLE nlp.signals
    ALTER COLUMN signal_type_registry SET DEFAULT 'signal_type';

-- The DEFAULTs above exist so the ALTER can run against a table that might have
-- rows in some future environment. They are not the intended way to write a row:
-- an omitted schema id or version should be an error at INSERT rather than a
-- silent guess about which contract produced the signal.
ALTER TABLE nlp.signals ALTER COLUMN signal_schema_id DROP DEFAULT;
ALTER TABLE nlp.signals ALTER COLUMN signal_schema_version DROP DEFAULT;

COMMENT ON COLUMN nlp.signals.quantity_family IS
    'What kind of QUANTITY this signal is about. Deliberately not the demand '
    'family: PAIN/DESIRE/BEHAVIORAL/MARKET classify demand, and a count of how '
    'often a token occurred in news text is not evidence of demand.';

COMMENT ON COLUMN nlp.signals.magnitude IS
    'The derived quantity, exact. NUMERIC and never DOUBLE PRECISION: the '
    'observations behind it are exact decimals, and a float here would give that '
    'back at the first subtraction. Never a 0-100 strength -- signals from '
    'different sources are not comparable measurements.';

COMMENT ON COLUMN nlp.signals.derivation_confidence IS
    'Confidence that this DERIVATION computed what it says it computed, given '
    'the inputs it used. NOT confidence that the phenomenon is real, not an '
    'evidence strength, and not an EvidenceScore input. A deterministic '
    'extractor reports 1.0, which is a statement about arithmetic.';

COMMENT ON COLUMN nlp.signals.temporal_basis IS
    'What temporal relation the derivation actually used. ORDER and GLOBAL '
    'INSTANT are different questions needing different evidence, and only '
    'COMPARABLE_INSTANTS may leave observed_at non-null or carry a direction.';

COMMENT ON COLUMN nlp.signals.temporal_window IS
    'The temporal relation the derivation actually used: basis, the source '
    'period labels verbatim, the resolution and the observation count. Bounds '
    'appear only under COMPARABLE_INSTANTS, so a signal cannot acquire a '
    'timeline its inputs never had.';

COMMENT ON COLUMN nlp.signals.derivation_fingerprint IS
    'sha256 over workspace, type, family, extractor and version, schema version, '
    'the ordered contributing inputs, the parameter fingerprint and the window. '
    'Excludes the OUTPUTS: a changed magnitude under an unchanged identity means '
    'the extractor is not deterministic, and that must be reportable rather than '
    'absorbed into a new row.';

-- `idx_signals_workspace` from migration 0001 followed the rename above and is
-- now `(workspace_id, derived_at DESC)`. A second index over the same two
-- columns is not a safety net, it is a write cost nobody chose.

CREATE INDEX idx_signals_type
    ON nlp.signals (workspace_id, signal_type_registry, signal_type_id, derived_at DESC);

CREATE INDEX idx_signals_extractor
    ON nlp.signals (extractor_id, extractor_version);

-- "Which signals could survive H-29 being answered", and the filter every
-- temporal consumer needs before it reads a window.
CREATE INDEX idx_signals_temporal_basis
    ON nlp.signals (workspace_id, temporal_basis);

-- -----------------------------------------------------------------------------
-- 4. nlp.signal_inputs -- the lineage, one row per record considered
--
-- GAP-1 and GAP-16. Every CONTRIBUTING and every EXCLUDED input, because "we
-- looked at ten and used six" must be visible: a signal that quietly used six of
-- ten is indistinguishable from one that was offered six.
--
-- Denormalized on purpose. `source_id`, `raw_record_id` and `observation_key`
-- are copied rather than joined, for the reason migration 0009 copied provenance
-- onto the normalized record: raw records expire eleven months before the rows
-- that reference them.
--
-- WHAT IS DELIBERATELY ABSENT: no independence state, no group id, no
-- reliability and no weight. Mission 1.11 §22 -- two signals are not independent
-- merely because they came from two records. This layer preserves the FACTS and
-- evidence aggregation makes the judgement with them, relative to a claim this
-- layer does not have.
-- -----------------------------------------------------------------------------
CREATE TABLE nlp.signal_inputs (
    id                    UUID        PRIMARY KEY,
    workspace_id          UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    signal_id             UUID        NOT NULL,
    normalized_record_id  UUID        NOT NULL,

    -- Lineage that must survive the row it came from.
    raw_record_id         UUID        NOT NULL,
    source_id             TEXT        NOT NULL REFERENCES registry.sources (id),
    observation_key       TEXT        NOT NULL,
    record_kind_registry  TEXT        NOT NULL DEFAULT 'normalization_record_kind',
    record_kind_id        TEXT        NOT NULL,
    period_label          TEXT        NOT NULL,
    period_type           TEXT        NOT NULL,

    -- The quality the input HAD when it was read, so the required-fact check can
    -- be re-run at audit time without re-reading a record that may have expired.
    input_quality         TEXT        NOT NULL,
    input_quality_reasons JSONB       NOT NULL DEFAULT '[]'::jsonb,

    role                  TEXT        NOT NULL,
    refusal_reason        TEXT,
    withheld_facts        JSONB       NOT NULL DEFAULT '[]'::jsonb,

    -- The derivation order. Part of what makes the fingerprint reproducible, and
    -- the difference between "A then B" and "B then A" for an ordered basis.
    input_position        INTEGER     NOT NULL,

    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT signal_inputs_role_check
        CHECK (role IN ('CONTRIBUTED', 'EXCLUDED')),
    CONSTRAINT signal_inputs_input_quality_check
        CHECK (input_quality IN ('VALID', 'PARTIAL', 'INVALID')),
    -- The value set comes FIRST and the null branch second. Both orders are
    -- equivalent to PostgreSQL and only one is found by the schema validator's
    -- `CHECK (column IN (...))` match, so a closed enum written the other way
    -- round would silently stop being compared against the contract.
    CONSTRAINT signal_inputs_refusal_reason_check
        CHECK (refusal_reason IN (
                   'INPUT_RECORD_INVALID', 'REQUIRED_FACT_WITHHELD',
                   'AMBIGUOUS_OBSERVATION_LINEAGE', 'INCOMPATIBLE_INPUT_KINDS',
                   'INSUFFICIENT_INPUT_OBSERVATIONS', 'UNSUPPORTED_SIGNAL_TYPE',
                   'PARAMETERS_INCOMPLETE')
               OR refusal_reason IS NULL),

    -- A CONTRIBUTED input has no reason to give and an EXCLUDED one owes the
    -- reason it was set aside. Enforced rather than documented, for the reason
    -- migration 0005 enforced the independence shape: a nullable column alone
    -- cannot distinguish "checked and fine" from "never asked".
    CONSTRAINT signal_inputs_role_reason_shape_check
        CHECK (
            (role = 'CONTRIBUTED' AND refusal_reason IS NULL)
         OR (role = 'EXCLUDED'    AND refusal_reason IS NOT NULL)
        ),

    CONSTRAINT signal_inputs_observation_key_not_blank_check
        CHECK (length(btrim(observation_key)) > 0),
    CONSTRAINT signal_inputs_position_check
        CHECK (input_position >= 0),
    CONSTRAINT signal_inputs_reasons_are_arrays_check
        CHECK (jsonb_typeof(input_quality_reasons) = 'array'
           AND jsonb_typeof(withheld_facts) = 'array'),

    -- Tenant-safe on both sides. A signal input in workspace A cannot reference
    -- a signal or a normalized record in workspace B: not rejected at runtime,
    -- but impossible to write.
    CONSTRAINT signal_inputs_signal_tenant_fkey
        FOREIGN KEY (workspace_id, signal_id)
        REFERENCES nlp.signals (workspace_id, id) ON DELETE CASCADE,
    -- RESTRICT, not CASCADE and not SET NULL. Deleting a normalized record that
    -- a signal was derived from is a decision about that signal, and the caller
    -- must make it: nulling would leave a derivation citing nothing, and
    -- cascading would silently delete a finding. Migration 0005 reached the same
    -- conclusion for independence groups.
    CONSTRAINT signal_inputs_record_tenant_fkey
        FOREIGN KEY (workspace_id, normalized_record_id)
        REFERENCES acquisition.normalized_records (workspace_id, id) ON DELETE RESTRICT,
    CONSTRAINT signal_inputs_record_kind_fkey
        FOREIGN KEY (record_kind_registry, record_kind_id)
        REFERENCES registry.registry_entries (registry, id),

    -- One row per record per signal. A record offered twice to one derivation is
    -- a caller error, not two inputs.
    CONSTRAINT signal_inputs_unique
        UNIQUE (workspace_id, signal_id, normalized_record_id)
);

COMMENT ON TABLE nlp.signal_inputs IS
    'Every normalized record a derivation considered, contributing or not. An '
    'excluded input is recorded rather than dropped: a signal that quietly used '
    'six of ten is indistinguishable from one that was offered six.';

COMMENT ON COLUMN nlp.signal_inputs.observation_key IS
    'WHICH observation contributed, inherited verbatim. The distinctness test '
    'for the two-observation rule is over THIS, never over normalized_record_id: '
    'one observation can have several normalized rows, D-08 has not decided '
    'which to read, and counting rows would let a normalizer upgrade manufacture '
    'a contrast out of one observation.';

CREATE INDEX idx_signal_inputs_workspace_signal
    ON nlp.signal_inputs (workspace_id, signal_id, input_position);

CREATE INDEX idx_signal_inputs_record
    ON nlp.signal_inputs (workspace_id, normalized_record_id);

-- "Every signal derived from this observation", which is the audit an open D-08
-- makes necessary.
CREATE INDEX idx_signal_inputs_observation
    ON nlp.signal_inputs (workspace_id, source_id, observation_key);

-- -----------------------------------------------------------------------------
-- 5. GAP-12 -- scoring.evidence.signal_id becomes tenant-safe
--
-- Pre-existing. Migration 0005 made `claim_id` and `independence_group_id`
-- composite for precisely this reason and left this one as it was, because no
-- signal existed to point at. One does now.
--
-- The single-column FK from 0001 STAYS. It carries the ON DELETE behaviour, and
-- removing a guard because a stronger one exists is a regression (ADR-012).
-- -----------------------------------------------------------------------------
ALTER TABLE scoring.evidence
    ADD CONSTRAINT evidence_signal_tenant_fkey
        FOREIGN KEY (workspace_id, signal_id)
        REFERENCES nlp.signals (workspace_id, id)
        ON DELETE SET NULL (signal_id);

-- -----------------------------------------------------------------------------
-- 6. Row-level security
--
-- ENABLE plus FORCE, because ENABLE alone exempts the table owner and in a
-- deployment where the application connects as the owner that exemption is the
-- entire protection (ADR-012). Grants come from the ALTER DEFAULT PRIVILEGES in
-- 0003, which covers future tables in nlp.
-- -----------------------------------------------------------------------------
ALTER TABLE nlp.signal_inputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE nlp.signal_inputs FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON nlp.signal_inputs
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());
