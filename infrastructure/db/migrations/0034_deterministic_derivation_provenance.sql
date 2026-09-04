-- 0034 — where the reasoning lives, and why it could not live anywhere existing
--
-- ADR-037 decided that a deterministic INFERRED Claim needs two additive
-- records, and that neither of them already exists. This migration creates
-- exactly those two and touches nothing else.
--
-- WHAT WAS ALREADY SUFFICIENT. `research.claims` already carries `claim_type`,
-- `interpretation_kind`, `proposition_key` and `proposition_facts`, so an
-- INFERRED Claim needs no new column. `scoring.evidence` already carries
-- `signal_id`, `claim_id`, `direction`, `independence_state` and `source_id`,
-- so the attachment needs none either. Neither table is altered here.
--
-- WHY THE REASONING COULD NOT REUSE AN EXISTING TABLE. The closest existing
-- structure is `research.claim_interpretation_inputs`: one row per (run,
-- signal) carrying a role, a claim id and a reason code. It cannot hold durable
-- derivation provenance, and the reason is a measured fact rather than a
-- preference -- every row of its parent `research.claim_interpretation_runs`
-- carries a populated `expires_at`, and the inputs foreign key is ON DELETE
-- CASCADE. When a run expires, every input row goes with it, and A CLAIM WOULD
-- OUTLIVE THE RECORD OF HOW IT WAS DERIVED. A retention-bounded execution log
-- is the right shape for *what did this run consider and refuse* (ADR-025) and
-- the wrong shape for *why is this Claim true*. Those two tables are NOT
-- touched here, and nothing below references them.
--
-- `origin_detail` is also left exactly as it is. It answers *where did this
-- Claim come from* on all 43 existing Claims, and a reasoning step answers a
-- different question. One free-text field holding both is the failure shape
-- Mission 1.15.4 named.
--
-- NOTHING IS BACKFILLED AND NOTHING IS DELETED. No existing row is read, and
-- both tables are empty when this migration finishes.

-- -----------------------------------------------------------------------------
-- 0. One vacuous unique constraint, so a composite tenant-safe FK is possible
--
-- `research.claim_revisions` has PRIMARY KEY (id) and UNIQUE (workspace_id,
-- claim_id, revision) and no UNIQUE (workspace_id, id). A composite foreign key
-- needs one. The addition is SEMANTICALLY VACUOUS -- `id` is already unique on
-- its own, so `(workspace_id, id)` cannot constrain anything new -- and it is
-- what lets a derivation row be structurally unable to cite a revision in
-- another workspace. Every other table this migration references
-- (`nlp.signals`, `research.claims`) already has the same constraint, so this
-- brings claim_revisions into line rather than inventing a pattern.
-- -----------------------------------------------------------------------------

ALTER TABLE research.claim_revisions
    ADD CONSTRAINT claim_revisions_workspace_id_key UNIQUE (workspace_id, id);

-- -----------------------------------------------------------------------------
-- 1. Threshold registrations
--
-- A threshold has its own lifecycle, independent of any Claim: it must be
-- frozen BEFORE the measurements it will be compared against, and one bound may
-- be referenced by many derivations. Putting it on the Claim would tie a
-- parameter's registration moment to a Claim that does not exist yet.
--
-- THE VALUE IS PROPOSITION IDENTITY LATER; THE REGISTRATION IS PROVENANCE.
-- `M >= 100` frozen in advance and `M >= 100` chosen afterwards are THE SAME
-- PROPOSITION with the same falsifier. What differs is calibration eligibility.
-- So nothing here is a Claim identity, this table stores no proposition key,
-- and the uniqueness rule below deliberately permits one logical bound to hold
-- several registrations with different provenance.
-- -----------------------------------------------------------------------------

CREATE TABLE research.threshold_registrations (
    id                      UUID        PRIMARY KEY,
    workspace_id            UUID        NOT NULL
                                        REFERENCES core.workspaces (id) ON DELETE CASCADE,

    -- The bound itself. NUMERIC and never a float: a threshold compared against
    -- an exact decimal measurement must not acquire a binary artifact
    -- (`normalized-record-v1.md`, numbers are exact decimals).
    threshold_operator      TEXT        NOT NULL,
    threshold_value         NUMERIC     NOT NULL,
    unit                    TEXT        NOT NULL,

    -- What the bound is a bound ON, and over what. Without these a threshold is
    -- a number with no proposition attached.
    metric_definition_id    TEXT        NOT NULL,
    scope_subject_id        TEXT        NOT NULL,
    scope_population        TEXT        NOT NULL,
    scope_time_bound        TEXT        NOT NULL,

    -- Provenance. `recorded_at` is the timestamp the preregistration rule
    -- compares, and it is retained precisely so that comparison remains
    -- possible later (ADR-037 §23).
    provenance_status       TEXT        NOT NULL,
    recorded_at             TIMESTAMPTZ NOT NULL,
    recorded_by             TEXT        NOT NULL,
    provenance_reference    TEXT,

    -- EXTERNAL_NORM only. A norm that cannot be identified is not a norm.
    norm_issuer             TEXT,
    norm_document_id        TEXT,
    norm_version            TEXT,
    norm_section            TEXT,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Composite target, so a derivation in workspace A can never cite a
    -- registration in B (ADR-012 layer three).
    UNIQUE (workspace_id, id),

    CONSTRAINT threshold_registrations_operator_check
        CHECK (threshold_operator IN ('GTE', 'GT', 'LTE', 'LT')),

    -- Exactly five statuses. A sixth would be a state nobody defined, and
    -- calibration eligibility is DERIVED from this column rather than stored
    -- beside it: two authorities for one fact eventually disagree.
    CONSTRAINT threshold_registrations_provenance_status_check
        CHECK (provenance_status IN (
            'PREREGISTERED', 'SOURCE_NATIVE', 'EXTERNAL_NORM', 'POST_HOC', 'UNKNOWN'
        )),

    -- A bound this system froze, or one a source published, must say where it
    -- came from. POST_HOC and UNKNOWN need no reference -- their whole content
    -- is that the origin is late or unestablished -- and forcing one would
    -- invite a fabricated citation.
    CONSTRAINT threshold_registrations_reference_required_check
        CHECK (
            provenance_status IN ('POST_HOC', 'UNKNOWN')
            OR (provenance_reference IS NOT NULL
                AND length(btrim(provenance_reference)) > 0)
        ),

    -- An external norm is identified in full or it is not an external norm.
    CONSTRAINT threshold_registrations_external_norm_check
        CHECK (
            provenance_status <> 'EXTERNAL_NORM'
            OR (norm_issuer IS NOT NULL
                AND norm_document_id IS NOT NULL
                AND norm_version IS NOT NULL
                AND norm_section IS NOT NULL)
        ),

    -- Norm fields belong to an external norm and nowhere else, so a POST_HOC
    -- bound cannot borrow an issuer's authority by filling one in.
    CONSTRAINT threshold_registrations_norm_fields_scoped_check
        CHECK (
            provenance_status = 'EXTERNAL_NORM'
            OR (norm_issuer IS NULL
                AND norm_document_id IS NULL
                AND norm_version IS NULL
                AND norm_section IS NULL)
        ),

    -- IDEMPOTENCY. The same bound over the same scope under the same provenance
    -- status is one registration. It deliberately INCLUDES the status, so the
    -- same logical bound may be registered once as PREREGISTERED and once as
    -- EXTERNAL_NORM without being merged -- those are two provenance facts, and
    -- ADR-037 §3 forbids equating threshold provenance with Claim identity.
    CONSTRAINT threshold_registrations_identity_key
        UNIQUE (workspace_id, metric_definition_id, scope_subject_id,
                scope_population, scope_time_bound,
                threshold_operator, threshold_value, provenance_status)
);

CREATE INDEX idx_threshold_registrations_scope
    ON research.threshold_registrations
       (workspace_id, metric_definition_id, scope_subject_id);

-- -----------------------------------------------------------------------------
-- 2. Claim derivations
--
-- One row per EVALUATION: one deterministic rule applied to one Signal for one
-- ClaimRevision. Not one row per Claim -- a single prose rationale cannot
-- explain both why one source supports a proposition and why another
-- contradicts it, and the moment two sources disagree a Claim-level record
-- becomes unable to say anything true about either (ADR-037 §20).
--
-- IT BINDS TO THE REVISION, NOT THE CLAIM. A threshold proposition can stay the
-- same while the rule version, the inputs or the rationale change. Binding to
-- the Claim would let a later derivation silently rewrite the reasoning behind
-- an earlier revision, which is the rewrite the append-only revision model
-- exists to prevent.
--
-- APPEND-ONLY. There is no supersession column and no `is_current` flag. Rule
-- v2 re-evaluating the same Signal against the same revision creates a SECOND
-- row and leaves the first intact, because two rule versions disagreeing is a
-- finding worth seeing rather than a conflict to resolve by overwriting. What
-- this deliberately does NOT decide is whether a re-evaluation may change an
-- existing Evidence row; that is evaluator behaviour and belongs to the mission
-- that writes one.
-- -----------------------------------------------------------------------------

CREATE TABLE research.claim_derivations (
    id                            UUID        PRIMARY KEY,
    workspace_id                  UUID        NOT NULL
                                              REFERENCES core.workspaces (id) ON DELETE CASCADE,

    claim_revision_id             UUID        NOT NULL,
    input_signal_id               UUID        NOT NULL,
    -- Optional context. The Signal is the load-bearing input, because Evidence
    -- attaches Signal to Claim; a source-attributed OBSERVED Claim over the same
    -- Signal may or may not exist, and a derivation must not become impossible
    -- because it does not.
    input_observed_claim_id       UUID,

    derivation_rule_id            TEXT        NOT NULL,
    derivation_rule_version       TEXT        NOT NULL,
    evaluator_version             TEXT        NOT NULL,

    -- The value compared, stored HERE rather than only on the Signal, so the
    -- reasoning stays explicable in its own right.
    measurement_value             NUMERIC     NOT NULL,
    threshold_registration_id     UUID,

    evaluation_result             TEXT        NOT NULL,

    -- An opaque durable identifier for the reviewed basis on which this
    -- measurement was judged to bear on this proposition. ADR-037 §13 chose
    -- option B: the authoritative basis stays a reviewed artifact, as the
    -- canonical subject registry already is, and no third table is created.
    semantic_equivalence_basis_id TEXT        NOT NULL,

    interpretation_kind           TEXT        NOT NULL,
    model_version                 TEXT,

    -- Human-readable only. Every load-bearing fact above is structured, and
    -- nothing downstream may parse this to recover one.
    rationale                     TEXT        NOT NULL,

    created_at                    TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (workspace_id, id),

    -- FK ACTIONS. `NO ACTION` rather than `CASCADE` or `RESTRICT`, and the
    -- choice is load-bearing in both directions.
    --
    -- Not CASCADE: `nlp.signals` and `scoring.evidence` both carry a populated
    -- `expires_at` on every row, so a future retention purge under CASCADE would
    -- delete the reasoning along with its input -- which is exactly the failure
    -- ADR-037 found in the interpretation-run tables and exactly what this table
    -- exists to avoid.
    --
    -- Not RESTRICT: RESTRICT is checked immediately, so deleting a workspace
    -- would fail depending on the order its cascades happened to run in.
    --
    -- NO ACTION alone is not enough either, and this was found by the tenancy
    -- teardown rather than reasoned about: an undeferred NO ACTION is checked at
    -- the end of each cascading statement, and the cascade that removes
    -- `claim_revisions` runs before the one that removes the derivations citing
    -- them. So the constraints are DEFERRABLE INITIALLY DEFERRED, which moves
    -- the check to COMMIT -- by which time a workspace deletion has removed both
    -- sides and a lone Signal purge still has a derivation pointing at it.
    -- Tenant deletion works; silent retention of a cited Signal does not.
    CONSTRAINT claim_derivations_revision_tenant_fkey
        FOREIGN KEY (workspace_id, claim_revision_id)
        REFERENCES research.claim_revisions (workspace_id, id)
        ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT claim_derivations_signal_tenant_fkey
        FOREIGN KEY (workspace_id, input_signal_id)
        REFERENCES nlp.signals (workspace_id, id)
        ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT claim_derivations_observed_claim_tenant_fkey
        FOREIGN KEY (workspace_id, input_observed_claim_id)
        REFERENCES research.claims (workspace_id, id)
        ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT claim_derivations_threshold_tenant_fkey
        FOREIGN KEY (workspace_id, threshold_registration_id)
        REFERENCES research.threshold_registrations (workspace_id, id)
        ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,

    -- Exactly four results. NOT_APPLICABLE is a semantic mismatch and is never
    -- CONTRADICTS; UNKNOWN is an unestablished equivalence and is never
    -- SUPPORTS; and NEUTRAL is deliberately absent, because a NEUTRAL row would
    -- assert that an observation bears on the Claim without bearing either way,
    -- which is a positive finding and a different thing from not knowing.
    CONSTRAINT claim_derivations_evaluation_result_check
        CHECK (evaluation_result IN ('SUPPORTS', 'CONTRADICTS', 'NOT_APPLICABLE', 'UNKNOWN')),

    -- The same pairing migration 0016 enforces on claims: DETERMINISTIC carries
    -- no model version, MODEL_DERIVED must carry one. One distinction, one
    -- place, so a deterministic derivation cannot quietly acquire a model.
    CONSTRAINT claim_derivations_interpretation_kind_check
        CHECK (interpretation_kind IN ('DETERMINISTIC', 'MODEL_DERIVED')),
    CONSTRAINT claim_derivations_model_version_pairing_check
        CHECK (
            (interpretation_kind = 'DETERMINISTIC' AND model_version IS NULL)
         OR (interpretation_kind = 'MODEL_DERIVED' AND model_version IS NOT NULL)
        ),

    -- A directional result compared something, so it names what it compared
    -- against. NOT_APPLICABLE and UNKNOWN stop before the comparison and need no
    -- threshold, which is why the column is nullable rather than the constraint
    -- being unconditional.
    CONSTRAINT claim_derivations_threshold_required_check
        CHECK (
            evaluation_result IN ('NOT_APPLICABLE', 'UNKNOWN')
            OR threshold_registration_id IS NOT NULL
        ),

    CONSTRAINT claim_derivations_rationale_present_check
        CHECK (length(btrim(rationale)) > 0),

    -- IDEMPOTENCY, and it deliberately differs from Evidence's.
    --
    -- Evidence is idempotent on (workspace, claim, signal): Mission 1.41 REMOVED
    -- the procedure version from that key, because Evidence identity is
    -- epistemic and a version bump must not INSERT a second row for the same
    -- relation.
    --
    -- A derivation record includes `derivation_rule_version` and MUST, because
    -- replaying a different rule over the same input is DIFFERENT REASONING
    -- about the same relation. One relation, several reasonings, and both facts
    -- stay visible.
    CONSTRAINT claim_derivations_identity_key
        UNIQUE (workspace_id, claim_revision_id, input_signal_id, derivation_rule_version)
);

CREATE INDEX idx_claim_derivations_revision
    ON research.claim_derivations (workspace_id, claim_revision_id);
CREATE INDEX idx_claim_derivations_signal
    ON research.claim_derivations (workspace_id, input_signal_id);
CREATE INDEX idx_claim_derivations_threshold
    ON research.claim_derivations (workspace_id, threshold_registration_id);

-- -----------------------------------------------------------------------------
-- 3. Tenancy. Both tables carry workspace_id and both get the policy: layer one
-- is the repository filter, layer two is RLS, layer three is the composite FK,
-- and none replaces another (ADR-005, ADR-012).
-- -----------------------------------------------------------------------------

ALTER TABLE research.threshold_registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.threshold_registrations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.threshold_registrations
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE research.claim_derivations ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.claim_derivations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.claim_derivations
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

COMMENT ON TABLE research.threshold_registrations IS
    'A bound, frozen with its provenance. The VALUE and OPERATOR become part of '
    'an INFERRED Claim''s proposition identity; the REGISTRATION does not, so '
    '`M >= 100` preregistered and `M >= 100` chosen afterwards are one '
    'proposition that differ only in calibration eligibility (ADR-037).';

COMMENT ON COLUMN research.threshold_registrations.recorded_at IS
    'When this system froze the bound. The preregistration rule compares it '
    'against an observation''s RETRIEVAL time, never its publication time: the '
    'bias guarded against is the analyst''s, and an analyst can only be '
    'influenced by data that reached them. The comparison is necessary and NOT '
    'sufficient -- it proves this system did not hold the measurement, never '
    'that nobody knew it.';

COMMENT ON COLUMN research.threshold_registrations.provenance_status IS
    'PREREGISTERED, SOURCE_NATIVE and EXTERNAL_NORM are calibration-eligible; '
    'POST_HOC and UNKNOWN are not. Eligibility is DERIVED from this column and '
    'never stored beside it. A post-hoc bound still permits logical support: '
    'provenance changes eligibility, never entailment.';

COMMENT ON TABLE research.claim_derivations IS
    'One deterministic evaluation: one rule, one Signal, one ClaimRevision, one '
    'result. Durable by design -- it is the record of WHY a Claim is true, and '
    'ADR-037 established that the retention-bounded interpretation-run tables '
    'cannot hold it because a Claim would outlive its own reasoning.';

COMMENT ON COLUMN research.claim_derivations.rationale IS
    'Human-readable explanation, generated deterministically from the '
    'structured fields by the evaluator''s own template. It may restate a '
    'structured fact and may never be the only record of one, and nothing '
    'downstream parses it to recover data.';

COMMENT ON COLUMN research.claim_derivations.semantic_equivalence_basis_id IS
    'The reviewed basis on which this measurement was judged to bear on this '
    'proposition. An opaque durable identifier into a reviewed artifact rather '
    'than a table (ADR-037 §13): equivalence is a documentary judgement a person '
    'makes, and no schema here infers it from matching strings.';
