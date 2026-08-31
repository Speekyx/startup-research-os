-- =============================================================================
-- 0018_claim_interpretation_runs.sql -- where a REFUSED interpretation goes,
-- and what the interpreter looked at and did not use
--
-- Mission 1.13.1 §21 and §22. Governed by
-- docs/data/claim-interpretation-runtime-v1.md and ADR-025.
--
-- THREE THINGS THIS ADDS
--
-- 1. research.claims.proposition_facts
--
--    Migration 0016 gave a claim a `proposition_key` -- a sha256 over the facts
--    the proposition asserts -- and nowhere to keep the facts. A hash with no
--    preimage cannot be verified, cannot be explained to a reader, and cannot
--    be recomputed when somebody asks why two claims are the same claim. The
--    key answers WHICH proposition; the facts are what makes that answer
--    auditable.
--
-- 2. research.claim_interpretation_runs
--
--    Mission 1.13 made this a precondition for 1.13.1 and did not build it,
--    because there was no interpreter to write one. There is now. One row per
--    interpreter EXECUTION, written in the SAME transaction as the claims it
--    emitted -- exactly the argument nlp.signal_derivation_runs makes one layer
--    down (ADR-021), and for exactly the same reason: an interpretation that
--    produced nothing must leave a durable trace WITHOUT a claim row meaning
--    "no claim".
--
-- 3. research.claim_interpretation_inputs
--
--    GAP-5. "Three supporting Signals exist" and "three of forty considered
--    were supporting" are different facts, and an aggregator that cannot tell
--    them apart reads a selection as a census. One row per (run, Signal)
--    CONSIDERED, carrying its role and why -- ids, roles and reasons, never a
--    copy of the Signal.
--
-- WHY THE INPUTS HANG OFF THE RUN AND NOT THE CLAIM
--
-- A Signal that was considered and NOT cited has no claim to hang off. Putting
-- the record on the claim would keep only the half that needs it least, which
-- is the gap rather than a fix for it. And a Signal excluded by version 1.0.0
-- and cited by 1.1.0 is two facts about two executions, which is what a
-- per-run row says and a per-claim row cannot.
--
-- Operational data: 90 days, like nlp.signal_derivation_runs. A Claim is a
-- durable artifact; a record of an attempt is not.
--
-- Forward-only. Never edited after it has been applied anywhere.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. The preimage of the proposition key
-- -----------------------------------------------------------------------------
ALTER TABLE research.claims
    ADD COLUMN proposition_facts JSONB,
    -- Paired presence, spelled so it cannot evaluate to NULL. Migration 0017
    -- exists because the obvious spelling of "both or neither" returns NULL on
    -- a half-filled row and a CHECK accepts NULL; `num_nonnulls` returns an
    -- integer whatever the inputs are.
    ADD CONSTRAINT claims_proposition_facts_paired_check
        CHECK (num_nonnulls(proposition_key, proposition_facts) IN (0, 2)),
    -- An object, not an array and not a scalar. The key is a hash over a
    -- canonical JSON object; a facts value of a different shape could not have
    -- produced it.
    ADD CONSTRAINT claims_proposition_facts_object_check
        CHECK (proposition_facts IS NULL OR jsonb_typeof(proposition_facts) = 'object'),
    -- An empty object identifies every proposition equally, which is no
    -- identity -- the model refuses it as PROPOSITION_NOT_IDENTIFIABLE and the
    -- database refuses it too, because a future writer is not this writer.
    ADD CONSTRAINT claims_proposition_facts_nonempty_check
        CHECK (proposition_facts IS NULL OR proposition_facts <> '{}'::jsonb);

COMMENT ON COLUMN research.claims.proposition_facts IS
    'The canonical fact object proposition_key is the sha256 of. Stored so the '
    'identity can be verified and explained: a hash with no preimage cannot '
    'answer why two claims are the same claim. Never the prose, never the '
    'research session, never an embedding (D-12 is open).';

-- -----------------------------------------------------------------------------
-- 2. One interpreter execution
-- -----------------------------------------------------------------------------
CREATE TABLE research.claim_interpretation_runs (
    id                      UUID        PRIMARY KEY,
    workspace_id            UUID        NOT NULL
                                        REFERENCES core.workspaces (id) ON DELETE CASCADE,
    research_session_id     UUID        REFERENCES research.research_sessions (id)
                                        ON DELETE SET NULL,

    -- Which interpreter ran, at what version, by what method. The same three
    -- facts research.claims carries, so a run and the claims it wrote can be
    -- lined up without a join table.
    interpreter_id          TEXT        NOT NULL,
    interpreter_version     TEXT        NOT NULL,
    interpretation_kind     TEXT        NOT NULL,

    -- What the pass saw and what came out of it. `signals_considered` is the
    -- denominator GAP-5 exists to preserve.
    signals_considered      INTEGER     NOT NULL DEFAULT 0,
    signals_cited           INTEGER     NOT NULL DEFAULT 0,
    signals_excluded        INTEGER     NOT NULL DEFAULT 0,
    signals_refused         INTEGER     NOT NULL DEFAULT 0,
    claims_new              INTEGER     NOT NULL DEFAULT 0,
    claims_unchanged        INTEGER     NOT NULL DEFAULT 0,
    revisions_created       INTEGER     NOT NULL DEFAULT 0,
    evidence_new            INTEGER     NOT NULL DEFAULT 0,
    evidence_unchanged      INTEGER     NOT NULL DEFAULT 0,

    -- One entry per refused Signal: {reason, detail, signal_id, signal_type_id}.
    -- JSONB rather than a child table for the reason migration 0009 gave for
    -- provenance -- a refusal is read WITH its run and is never joined to. The
    -- CONSIDERED set is a child table because it IS joined to: "which claims
    -- came from Signals this run also excluded" is the question GAP-5 asks.
    refusals                JSONB       NOT NULL DEFAULT '[]'::jsonb,

    truncated_by            TEXT,

    correlation_id          TEXT        NOT NULL,
    started_at              TIMESTAMPTZ NOT NULL,
    finished_at             TIMESTAMPTZ NOT NULL,
    -- Operational data (data-retention-policy-v1.md §2.5), 90 days.
    expires_at              TIMESTAMPTZ NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT claim_interpretation_runs_interpreter_identified_check
        CHECK (length(btrim(interpreter_id)) > 0
           AND length(btrim(interpreter_version)) > 0),
    CONSTRAINT claim_interpretation_runs_kind_check
        CHECK (interpretation_kind IN ('DETERMINISTIC', 'MODEL_DERIVED')),
    CONSTRAINT claim_interpretation_runs_correlation_identified_check
        CHECK (length(btrim(correlation_id)) > 0),
    CONSTRAINT claim_interpretation_runs_counts_nonnegative_check
        CHECK (signals_considered >= 0 AND signals_cited >= 0 AND signals_excluded >= 0
           AND signals_refused >= 0 AND claims_new >= 0 AND claims_unchanged >= 0
           AND revisions_created >= 0 AND evidence_new >= 0 AND evidence_unchanged >= 0),

    -- EACH outcome is bounded by what was considered, and their SUM is NOT.
    --
    -- `cited + excluded + refused <= considered` would be true of this
    -- interpreter and it is a model of how the counters relate, not arithmetic.
    -- Migration 0013 asserted exactly that shape one layer down and migration
    -- 0015 had to undo it, because the third extractor derived one pair and
    -- refused another from a single group. An interpreter that cites a Signal
    -- for one proposition and excludes it from another would falsify the sum
    -- the same way, and the counters would be right. Write the invariant you
    -- can defend (testing-strategy.md §27).
    CONSTRAINT claim_interpretation_runs_outcome_bounds_check
        CHECK (signals_cited <= signals_considered
           AND signals_excluded <= signals_considered
           AND signals_refused <= signals_considered),

    CONSTRAINT claim_interpretation_runs_refusals_is_array_check
        CHECK (jsonb_typeof(refusals) = 'array'),
    -- A refused Signal must be explained. A count with no reasons behind it is
    -- the "something did not happen" this table exists to replace.
    CONSTRAINT claim_interpretation_runs_refusals_explained_check
        CHECK (signals_refused = 0 OR jsonb_array_length(refusals) > 0),
    CONSTRAINT claim_interpretation_runs_finished_after_start_check
        CHECK (finished_at >= started_at),
    CONSTRAINT claim_interpretation_runs_expiry_after_finish_check
        CHECK (expires_at > finished_at),

    CONSTRAINT claim_interpretation_runs_workspace_id_key
        UNIQUE (workspace_id, id),
    CONSTRAINT claim_interpretation_runs_session_tenant_fkey
        FOREIGN KEY (workspace_id, research_session_id)
        REFERENCES research.research_sessions (workspace_id, id)
        ON DELETE SET NULL (research_session_id)
);

COMMENT ON TABLE research.claim_interpretation_runs IS
    'One row per interpreter EXECUTION, written in the same transaction as the '
    'claims it emitted. A redelivery writes a second run row while writing zero '
    'new claims -- the CLAIMS are what is idempotent, and two executions are two '
    'things that happened (ADR-004, ADR-021).';

COMMENT ON COLUMN research.claim_interpretation_runs.signals_considered IS
    'The denominator GAP-5 exists to preserve. Three cited out of forty '
    'considered is not the same finding as three cited out of three.';

CREATE INDEX idx_claim_interpretation_runs_workspace
    ON research.claim_interpretation_runs (workspace_id, finished_at DESC);

CREATE INDEX idx_claim_interpretation_runs_interpreter
    ON research.claim_interpretation_runs (workspace_id, interpreter_id,
                                           interpreter_version, finished_at DESC);

CREATE INDEX idx_claim_interpretation_runs_correlation
    ON research.claim_interpretation_runs (workspace_id, correlation_id);

CREATE INDEX idx_claim_interpretation_runs_expiry
    ON research.claim_interpretation_runs (expires_at);

-- -----------------------------------------------------------------------------
-- 3. GAP-5: every Signal the run CONSIDERED, and what became of it
-- -----------------------------------------------------------------------------
CREATE TABLE research.claim_interpretation_inputs (
    id                      UUID        PRIMARY KEY,
    workspace_id            UUID        NOT NULL
                                        REFERENCES core.workspaces (id) ON DELETE CASCADE,
    run_id                  UUID        NOT NULL,

    -- The Signal considered. NOT NULL: a row here says "the run looked at this
    -- Signal", and a row that cannot name one says nothing.
    signal_id               UUID        NOT NULL,
    signal_type_registry    TEXT        NOT NULL DEFAULT 'signal_type',
    signal_type_id          TEXT        NOT NULL,

    -- CITED | EXCLUDED | REFUSED. The distinction between the last two is the
    -- one worth keeping: EXCLUDED was never attempted (no template for its
    -- type, lineage unreadable); REFUSED was attempted and the model rejected
    -- the draft. Collapsing them loses which of the two happened.
    role                    TEXT        NOT NULL,
    -- The Claim, when one was emitted. NULL for every other role by the
    -- coherence CHECK below.
    claim_id                UUID,
    -- A ClaimEvidenceRefusalReason. Required for EXCLUDED and REFUSED: a
    -- Signal passed over without a reason is the gap this table closes,
    -- reopened.
    reason_code             TEXT,
    detail                  TEXT,

    input_position          INTEGER     NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT claim_interpretation_inputs_role_check
        CHECK (role IN ('CITED', 'EXCLUDED', 'REFUSED')),
    -- Every branch tests with IS NULL / IS NOT NULL, which are never NULL, and
    -- `role` is NOT NULL -- so the whole expression is TRUE or FALSE and never
    -- the third thing a CHECK silently accepts (migration 0017).
    CONSTRAINT claim_interpretation_inputs_role_coherent_check
        CHECK (
            (role = 'CITED'    AND claim_id IS NOT NULL AND reason_code IS NULL)
         OR (role = 'EXCLUDED' AND claim_id IS NULL     AND reason_code IS NOT NULL)
         OR (role = 'REFUSED'  AND claim_id IS NULL     AND reason_code IS NOT NULL)
        ),
    -- One row per Signal per run. A Signal considered twice in one execution is
    -- the same consideration counted twice, and it would corrupt the
    -- denominator this table exists to hold.
    CONSTRAINT claim_interpretation_inputs_once_per_run_key
        UNIQUE (run_id, signal_id),

    CONSTRAINT claim_interpretation_inputs_run_tenant_fkey
        FOREIGN KEY (workspace_id, run_id)
        REFERENCES research.claim_interpretation_runs (workspace_id, id)
        ON DELETE CASCADE,
    -- Composite, so a run in workspace A can never name a Signal in B. The
    -- explicit filter is layer one, RLS is layer two and this is layer three
    -- (ADR-012), and none replaces another.
    CONSTRAINT claim_interpretation_inputs_signal_tenant_fkey
        FOREIGN KEY (workspace_id, signal_id)
        REFERENCES nlp.signals (workspace_id, id) ON DELETE CASCADE,
    CONSTRAINT claim_interpretation_inputs_claim_tenant_fkey
        FOREIGN KEY (workspace_id, claim_id)
        REFERENCES research.claims (workspace_id, id) ON DELETE CASCADE,
    CONSTRAINT claim_interpretation_inputs_signal_type_fkey
        FOREIGN KEY (signal_type_registry, signal_type_id)
        REFERENCES registry.registry_entries (registry, id)
);

COMMENT ON TABLE research.claim_interpretation_inputs IS
    'GAP-5. One row per Signal a run CONSIDERED, with its role and why. Ids, '
    'roles and reasons -- never a copy of the Signal. Answers "which Signals '
    'were considered, which were cited, which were not, and for what reason", '
    'which no count of emitted claims can answer.';

CREATE INDEX idx_claim_interpretation_inputs_run
    ON research.claim_interpretation_inputs (workspace_id, run_id, input_position);

CREATE INDEX idx_claim_interpretation_inputs_signal
    ON research.claim_interpretation_inputs (workspace_id, signal_id, created_at DESC);

-- "Which Signals did this run consider and NOT cite", the GAP-5 question, as
-- one index scan.
CREATE INDEX idx_claim_interpretation_inputs_not_cited
    ON research.claim_interpretation_inputs (workspace_id, run_id, reason_code)
    WHERE role <> 'CITED';

CREATE INDEX idx_claim_interpretation_inputs_claim
    ON research.claim_interpretation_inputs (workspace_id, claim_id)
    WHERE claim_id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- 4. Row-level security
--
-- ENABLE plus FORCE on both. An interpretation run names which Signals a
-- workspace considered and which propositions it drew from them, which is as
-- much a statement about what a tenant is researching as the claims themselves.
-- -----------------------------------------------------------------------------
ALTER TABLE research.claim_interpretation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.claim_interpretation_runs FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.claim_interpretation_runs
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE research.claim_interpretation_inputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.claim_interpretation_inputs FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.claim_interpretation_inputs
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());
