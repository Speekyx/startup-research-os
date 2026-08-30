-- =============================================================================
-- 0013_signal_derivation_runs.sql -- where a REFUSED derivation goes
--
-- Mission 1.11.1 §4. Governed by docs/data/signal-derivation-runtime-v1.md §1
-- and ADR-021.
--
-- THE PROBLEM
--
-- Mission 1.11 left one question open: a derivation attempt that produces no
-- Signal leaves no durable trace. The forbidden answer is a Signal row that
-- means "no signal" -- a row in a table of signals says a signal exists.
--
-- WHY NOT research.research_jobs
--
-- It was the closest existing mechanism and it has no result column. Using it
-- would mean adding one and wiring a worker to write back into the `research`
-- schema -- plumbing that does not exist -- for a column every job type would
-- then be expected to fill. And it is written in a DIFFERENT transaction from
-- the signals, so "6 emitted, 2 refused" could disagree with what was stored.
--
-- WHAT THIS IS
--
-- One row per extractor EXECUTION, written inside the same transaction as the
-- signals it emitted. Not one row per logical job: delivery is at-least-once
-- (ADR-004), so a redelivery writes a second run row while writing zero new
-- signals, which is the honest record of what happened. The SIGNALS are what is
-- idempotent.
--
-- Operational data: 90 days, like research.research_jobs. A signal is a
-- 12-month artifact; a record of an attempt is not.
--
-- Forward-only. Never edited after it has been applied anywhere.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Two contract values Mission 1.11.1 found it needed
--
-- ABSOLUTE_DIFFERENCE: ABSOLUTE_CHANGE asserts something CHANGED, which is a
-- statement about time. A same-bucket contrast between two lexical terms is a
-- difference between two quantities measured at the same position, and using
-- the temporal value would assert a temporality H-32 says is not established.
--
-- INCOMPATIBLE_SERIES: INCOMPATIBLE_INPUT_KINDS means the inputs disagree on
-- record kind or period resolution. Two World Bank observations of DIFFERENT
-- COUNTRIES disagree on neither, and are still not observations of the same
-- measured series. The contract had no way to say "same kind, different thing".
-- -----------------------------------------------------------------------------
ALTER TABLE nlp.signals
    DROP CONSTRAINT signals_magnitude_kind_check,
    ADD CONSTRAINT signals_magnitude_kind_check
        CHECK (magnitude_kind IN ('ABSOLUTE_CHANGE', 'ABSOLUTE_DIFFERENCE',
                                  'RATIO', 'OBSERVATION_COUNT')),
    -- ABSOLUTE_DIFFERENCE inherits its unit from the inputs exactly as
    -- ABSOLUTE_CHANGE does, so the dimensionless rule is unchanged and is
    -- restated here only because the constraint above was replaced.
    DROP CONSTRAINT signals_dimensionless_kind_check,
    ADD CONSTRAINT signals_dimensionless_kind_check
        CHECK (
            magnitude_kind NOT IN ('RATIO', 'OBSERVATION_COUNT')
         OR magnitude_unit_state = 'DIMENSIONLESS'
        );

ALTER TABLE nlp.signal_inputs
    DROP CONSTRAINT signal_inputs_refusal_reason_check,
    -- The value set comes FIRST and the null branch second, so the schema
    -- validator's `CHECK (column IN (...))` match finds it (Mission 1.11).
    ADD CONSTRAINT signal_inputs_refusal_reason_check
        CHECK (refusal_reason IN (
                   'INPUT_RECORD_INVALID', 'REQUIRED_FACT_WITHHELD',
                   'AMBIGUOUS_OBSERVATION_LINEAGE', 'INCOMPATIBLE_INPUT_KINDS',
                   'INCOMPATIBLE_SERIES', 'INSUFFICIENT_INPUT_OBSERVATIONS',
                   'UNSUPPORTED_SIGNAL_TYPE', 'PARAMETERS_INCOMPLETE')
               OR refusal_reason IS NULL);

-- -----------------------------------------------------------------------------
-- 2. nlp.signal_derivation_runs
--
-- Answers, per workspace and without reading a log file:
--
--   the extractor considered N candidate groups
--   M emitted signals
--   K were refused
--   and why
--
-- WHAT IS DELIBERATELY ABSENT: no duration, no timing histogram, no counter
-- service, no metric names. §4 forbids an observability subsystem, and this is
-- one table with one insert per execution.
-- -----------------------------------------------------------------------------
CREATE TABLE nlp.signal_derivation_runs (
    id                     UUID        PRIMARY KEY,
    workspace_id           UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    research_session_id    UUID        REFERENCES research.research_sessions (id) ON DELETE SET NULL,

    -- Which derivation ran, at what version, over which stated parameters. The
    -- fingerprint is the same one that enters a signal's identity, so a run and
    -- the signals it wrote can be lined up without storing the parameters twice.
    extractor_id           TEXT        NOT NULL,
    extractor_version      TEXT        NOT NULL,
    signal_type_registry   TEXT        NOT NULL DEFAULT 'signal_type',
    signal_type_id         TEXT        NOT NULL,
    parameter_fingerprint  TEXT        NOT NULL,

    -- What the pass saw and what came out of it.
    groups_considered      INTEGER     NOT NULL DEFAULT 0,
    groups_derived         INTEGER     NOT NULL DEFAULT 0,
    groups_refused         INTEGER     NOT NULL DEFAULT 0,
    signals_new            INTEGER     NOT NULL DEFAULT 0,
    signals_unchanged      INTEGER     NOT NULL DEFAULT 0,
    signals_conflicted     INTEGER     NOT NULL DEFAULT 0,
    records_considered     INTEGER     NOT NULL DEFAULT 0,
    records_contributed    INTEGER     NOT NULL DEFAULT 0,
    records_excluded       INTEGER     NOT NULL DEFAULT 0,

    -- One entry per refused group: the canonical reason, the detail naming what
    -- disagreed, the grouping key and the observation keys involved. JSONB
    -- rather than a child table because a refusal is read WITH its run and is
    -- never joined to -- the same argument migration 0009 made for provenance.
    refusals               JSONB       NOT NULL DEFAULT '[]'::jsonb,

    -- Which bound stopped the pass, when one did. NULL means it finished.
    truncated_by           TEXT,

    correlation_id         TEXT        NOT NULL,
    started_at             TIMESTAMPTZ NOT NULL,
    finished_at            TIMESTAMPTZ NOT NULL,
    -- Operational data (data-retention-policy-v1.md §2.5: job records, 90 days).
    -- Deliberately SHORTER than the 12 months a signal gets: a signal is an
    -- artifact and a record of an attempt is not.
    expires_at             TIMESTAMPTZ NOT NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT signal_derivation_runs_extractor_identified_check
        CHECK (length(btrim(extractor_id)) > 0
           AND length(btrim(extractor_version)) > 0),
    CONSTRAINT signal_derivation_runs_correlation_identified_check
        CHECK (length(btrim(correlation_id)) > 0),
    CONSTRAINT signal_derivation_runs_counts_nonnegative_check
        CHECK (groups_considered >= 0 AND groups_derived >= 0 AND groups_refused >= 0
           AND signals_new >= 0 AND signals_unchanged >= 0 AND signals_conflicted >= 0
           AND records_considered >= 0 AND records_contributed >= 0
           AND records_excluded >= 0),
    -- A group is derived or refused; it cannot be both and it cannot be neither
    -- while the pass ran to completion. A run whose arithmetic does not add up
    -- is a run whose numbers nobody can act on.
    CONSTRAINT signal_derivation_runs_group_arithmetic_check
        CHECK (groups_derived + groups_refused <= groups_considered),
    CONSTRAINT signal_derivation_runs_record_arithmetic_check
        CHECK (records_contributed + records_excluded <= records_considered),
    CONSTRAINT signal_derivation_runs_refusals_is_array_check
        CHECK (jsonb_typeof(refusals) = 'array'),
    -- A refused group must be explained. A count with no reasons behind it is
    -- the "something did not happen" this table exists to replace.
    CONSTRAINT signal_derivation_runs_refusals_explained_check
        CHECK (groups_refused = 0 OR jsonb_array_length(refusals) > 0),
    CONSTRAINT signal_derivation_runs_finished_after_start_check
        CHECK (finished_at >= started_at),
    CONSTRAINT signal_derivation_runs_expiry_after_finish_check
        CHECK (expires_at > finished_at),

    CONSTRAINT signal_derivation_runs_signal_type_fkey
        FOREIGN KEY (signal_type_registry, signal_type_id)
        REFERENCES registry.registry_entries (registry, id),
    CONSTRAINT signal_derivation_runs_session_tenant_fkey
        FOREIGN KEY (workspace_id, research_session_id)
        REFERENCES research.research_sessions (workspace_id, id)
        ON DELETE SET NULL (research_session_id)
);

COMMENT ON TABLE nlp.signal_derivation_runs IS
    'One row per extractor EXECUTION, written in the same transaction as the '
    'signals it emitted. Records what was considered, what came out and why the '
    'rest did not -- so a refused derivation has a durable trace WITHOUT a row '
    'in nlp.signals meaning "no signal exists".';

COMMENT ON COLUMN nlp.signal_derivation_runs.refusals IS
    'One entry per refused group: {reason, detail, group_key, observation_keys}. '
    'The reason is a SignalRefusalReason; the detail names the field that '
    'disagreed. A consumer branches on the code, never on the sentence.';

CREATE INDEX idx_signal_derivation_runs_workspace
    ON nlp.signal_derivation_runs (workspace_id, finished_at DESC);

CREATE INDEX idx_signal_derivation_runs_extractor
    ON nlp.signal_derivation_runs (workspace_id, extractor_id, extractor_version,
                                   finished_at DESC);

-- "What did this correlation derive", which is how an operator debugs one pass.
CREATE INDEX idx_signal_derivation_runs_correlation
    ON nlp.signal_derivation_runs (workspace_id, correlation_id);

CREATE INDEX idx_signal_derivation_runs_expiry
    ON nlp.signal_derivation_runs (expires_at);

-- -----------------------------------------------------------------------------
-- 3. Row-level security
--
-- ENABLE plus FORCE. A derivation run names which observations a workspace
-- considered, which is as much a statement about what a tenant is researching
-- as the signals themselves.
-- -----------------------------------------------------------------------------
ALTER TABLE nlp.signal_derivation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE nlp.signal_derivation_runs FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON nlp.signal_derivation_runs
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());
