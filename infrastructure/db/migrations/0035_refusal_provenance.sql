-- 0035 — where a refusal lives, given that it has no Claim to hang from
--
-- ADR-038 decided that a refusal is NOT a derivation of a Claim. A directional
-- derivation answers *why does Signal S support or contradict existing revision
-- R*; a refusal answers *why was Signal S NOT attached to candidate proposition
-- P*. The subject of the first is a revision that exists; the subject of the
-- second is a proposition that does not. This migration creates exactly one
-- table for the second and touches nothing else.
--
-- WHY IT COULD NOT GO IN `research.claim_derivations`. Two reasons, and the
-- second was measured rather than argued.
--
-- First, that table identifies its proposition ONLY through `claim_revision_id`.
-- It carries no descriptor of its own, so with that column NULL a row cannot say
-- what was refused -- which is the one thing a refusal record exists to say.
--
-- Second, `claim_derivations_identity_key` is UNIQUE (workspace_id,
-- claim_revision_id, input_signal_id, derivation_rule_version), and PostgreSQL
-- treats NULLs as distinct. Mission 1.53 built a temp table mirroring that
-- constraint and INSERTED THREE IDENTICAL ROWS with a NULL revision id; the same
-- table refused the duplicate the moment the column was populated. So making
-- `claim_revision_id` nullable would silently remove that table's only
-- idempotency guarantee from exactly the rows the change would have added, and
-- nothing would report it. **Every column of this table's identity key is
-- NOT NULL for that reason.**
--
-- WHAT IS NOT TOUCHED. `research.claim_derivations` keeps its NOT NULL and its
-- meaning: every row there still names a real ClaimRevision.
-- `research.require_evidence_for_generated_claim` is unchanged and gains no
-- INFERRED exemption -- it does not need one, because no Claim is created here.
-- `research.claims`, `research.claim_revisions`, `scoring.evidence`,
-- `research.threshold_registrations` and both interpretation-run tables are
-- unchanged. Nothing is backfilled: the refusals that ephemeral run logs once
-- held expired, and reconstructing them would be inventing history.

-- -----------------------------------------------------------------------------
-- 1. Proposition evaluation refusals
--
-- NAMED FOR WHAT THE ROW IS. Not `claim_evaluation_refusals`: no Claim is
-- evaluated and none exists, and this row is precisely the case where there is
-- none. Mission 1.10's rule that a kind is named for its shape, and that a name
-- may not carry an interpretation, applies to a table as much as to a record
-- kind.
-- -----------------------------------------------------------------------------

CREATE TABLE research.proposition_evaluation_refusals (
    id                            UUID        PRIMARY KEY,
    workspace_id                  UUID        NOT NULL
                                              REFERENCES core.workspaces (id) ON DELETE CASCADE,

    -- THE INPUT. The Signal is the load-bearing witness, exactly as on
    -- claim_derivations. A source-attributed OBSERVED Claim over the same Signal
    -- may or may not exist, and a refusal must not become impossible because it
    -- does not.
    input_signal_id               UUID        NOT NULL,
    input_observed_claim_id       UUID,

    -- THE TARGET, and the reason this table can exist at all.
    --
    -- A refusal has no ClaimRevision, so it cannot point at a proposition; it has
    -- to CARRY one. Both halves are stored: the key, and the exact preimage the
    -- key was computed from. A key alone would identify a proposition nobody can
    -- read, and unlike a Claim there is no row elsewhere to recover the facts
    -- from -- which is precisely what makes a refusal different from a
    -- derivation.
    --
    -- The facts use the SAME vocabulary as `research.claims.proposition_facts`,
    -- so a refused candidate and the Claim it may later become are comparable by
    -- key. That is what makes the UNKNOWN-then-SUPPORTS transition traceable, and
    -- it is why no refusal-specific representation was invented.
    target_proposition_key        TEXT        NOT NULL,
    target_proposition_facts      JSONB       NOT NULL,

    derivation_rule_id            TEXT        NOT NULL,
    derivation_rule_version       TEXT        NOT NULL,
    evaluator_version             TEXT        NOT NULL,

    -- The reviewed basis on which the measurement was judged to bear, or not to
    -- bear, on the target. NOT NULL, and that is a measured contract fact rather
    -- than a convenience: `SemanticEquivalenceDecision` refuses a blank basis id
    -- for EVERY verdict including UNKNOWN, so no evaluation can occur without
    -- one and no placeholder needs inventing.
    semantic_equivalence_basis_id TEXT        NOT NULL,

    -- Nullable, because three of the seven refusals happen BEFORE the
    -- registration is consulted. Where present on such a row it records a
    -- registration SUPPLIED to the attempt, and the reason code -- not this
    -- column -- says whether it was load-bearing.
    threshold_registration_id     UUID,

    evaluation_result             TEXT        NOT NULL,
    reason_code                   TEXT        NOT NULL,

    interpretation_kind           TEXT        NOT NULL,
    model_version                 TEXT,

    -- Human-readable only. Every load-bearing fact above is structured, and
    -- nothing downstream may parse this to recover one.
    rationale                     TEXT        NOT NULL,

    created_at                    TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Semantically vacuous -- `id` is already unique alone -- and added for the
    -- same reason 0034 added it to both of its tables: every workspace-scoped
    -- table in this schema carries it, so a future composite tenant-safe FK is
    -- possible without a migration that looks like a schema change.
    UNIQUE (workspace_id, id),

    -- FK ACTIONS, following 0034 exactly, and for the same reason in both
    -- directions. Not CASCADE: `nlp.signals` carries a populated `expires_at` on
    -- every row, so a retention purge under CASCADE would delete the refusal
    -- along with its witness. Not RESTRICT: RESTRICT is immediate, so deleting a
    -- workspace would fail depending on the order its cascades happened to run
    -- in. NO ACTION alone is not enough either -- an undeferred NO ACTION is
    -- checked at the end of each CASCADING statement, which is the failure 0034
    -- found by watching a tenancy teardown break. DEFERRABLE INITIALLY DEFERRED
    -- moves the check to COMMIT: by then a workspace deletion has removed both
    -- sides, and a lone Signal purge still has a refusal pointing at it.
    CONSTRAINT proposition_evaluation_refusals_signal_tenant_fkey
        FOREIGN KEY (workspace_id, input_signal_id)
        REFERENCES nlp.signals (workspace_id, id)
        ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT proposition_evaluation_refusals_observed_claim_tenant_fkey
        FOREIGN KEY (workspace_id, input_observed_claim_id)
        REFERENCES research.claims (workspace_id, id)
        ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT proposition_evaluation_refusals_threshold_tenant_fkey
        FOREIGN KEY (workspace_id, threshold_registration_id)
        REFERENCES research.threshold_registrations (workspace_id, id)
        ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,

    -- EXACTLY TWO RESULTS. This table is structurally incapable of holding a
    -- directional decision: SUPPORTS and CONTRADICTS belong on
    -- `claim_derivations` with a real ClaimRevision, and NEUTRAL is not a
    -- refusal at all -- it asserts that an observation bears on a Claim without
    -- bearing either way, which is a positive finding and a different thing from
    -- being unable to establish that it bears.
    --
    -- It is also incapable of holding a SYSTEM FAILURE. There is no ERROR,
    -- FAILED, EXCEPTION or TIMEOUT here and no generic status column that could
    -- acquire one: an execution failure is not an epistemic refusal, and it
    -- belongs with `nlp.signal_derivation_runs` and
    -- `research.claim_interpretation_runs`.
    CONSTRAINT proposition_evaluation_refusals_result_check
        CHECK (evaluation_result IN ('NOT_APPLICABLE', 'UNKNOWN')),

    -- The seven codes the evaluator actually raises, read from its own `_refuse`
    -- calls. None invented, none renamed.
    CONSTRAINT proposition_evaluation_refusals_reason_code_check
        CHECK (reason_code IN (
            'SEMANTIC_MISMATCH',
            'EQUIVALENCE_NOT_ESTABLISHED',
            'EQUIVALENCE_DIMENSIONS_INCOMPLETE',
            'THRESHOLD_REGISTRATION_MISMATCH',
            'UNIT_MISMATCH',
            'TIME_BOUND_MISMATCH',
            'PREREGISTRATION_TIMING_INCONSISTENT'
        )),

    -- THE PAIRING, which is what stops a row asserting a shape the evaluator can
    -- never produce -- `UNKNOWN` with `UNIT_MISMATCH`, say. Constraining the two
    -- vocabularies separately would admit all fourteen combinations.
    --
    -- This subsumes the two checks above, and they are kept anyway: when only the
    -- reason code is wrong, a violation named `..._reason_code_check` says so,
    -- where a pairing violation would leave a reader comparing two columns to
    -- find out which one was the typo.
    CONSTRAINT proposition_evaluation_refusals_result_reason_pairing_check
        CHECK ((reason_code, evaluation_result) IN (
            ('SEMANTIC_MISMATCH',                  'NOT_APPLICABLE'),
            ('EQUIVALENCE_NOT_ESTABLISHED',        'UNKNOWN'),
            ('EQUIVALENCE_DIMENSIONS_INCOMPLETE',  'UNKNOWN'),
            ('THRESHOLD_REGISTRATION_MISMATCH',    'NOT_APPLICABLE'),
            ('UNIT_MISMATCH',                      'NOT_APPLICABLE'),
            ('TIME_BOUND_MISMATCH',                'NOT_APPLICABLE'),
            ('PREREGISTRATION_TIMING_INCONSISTENT', 'UNKNOWN')
        )),

    -- A refusal that REACHED the registration gate names the registration it
    -- judged. The three equivalence refusals return before that gate, so for them
    -- the column is optional rather than absent -- the evaluator currently passes
    -- a registration to every refusal, and forbidding it here would require
    -- changing evaluator behaviour to satisfy a constraint.
    CONSTRAINT proposition_evaluation_refusals_threshold_conditional_check
        CHECK (
            reason_code NOT IN (
                'THRESHOLD_REGISTRATION_MISMATCH',
                'UNIT_MISMATCH',
                'TIME_BOUND_MISMATCH',
                'PREREGISTRATION_TIMING_INCONSISTENT'
            )
            OR threshold_registration_id IS NOT NULL
        ),

    -- The same pairing 0016 enforces on claims and 0034 on derivations, so a
    -- deterministic refusal cannot quietly acquire a model.
    CONSTRAINT proposition_evaluation_refusals_interpretation_kind_check
        CHECK (interpretation_kind IN ('DETERMINISTIC', 'MODEL_DERIVED')),
    CONSTRAINT proposition_evaluation_refusals_model_version_pairing_check
        CHECK (
            (interpretation_kind = 'DETERMINISTIC' AND model_version IS NULL)
         OR (interpretation_kind = 'MODEL_DERIVED' AND model_version IS NOT NULL)
        ),

    -- DESCRIPTOR PARITY. `research.claims` requires its proposition_facts to be a
    -- non-empty JSON object and its key to be non-blank; the same three hold
    -- here, unconditionally rather than `OR IS NULL`, because both columns are
    -- NOT NULL on a refusal.
    CONSTRAINT proposition_evaluation_refusals_key_not_blank_check
        CHECK (length(btrim(target_proposition_key)) > 0),
    CONSTRAINT proposition_evaluation_refusals_facts_object_check
        CHECK (jsonb_typeof(target_proposition_facts) = 'object'),
    CONSTRAINT proposition_evaluation_refusals_facts_nonempty_check
        CHECK (target_proposition_facts <> '{}'::jsonb),

    -- ONE CHECK STRICTER THAN `research.claims`, deliberately. A Claim's facts
    -- are the preimage of a key on a row that already declares what it is; a
    -- refusal's facts are the ONLY record of what was refused, so the descriptor
    -- has to say which kind of proposition it describes. Measured before being
    -- required: 43 of 43 live Claims carry `proposition`, and the evaluator
    -- emits it.
    --
    -- A SECOND, STRICTER CHECK WAS CONSIDERED AND REJECTED ON A MEASUREMENT.
    -- Requiring every fact VALUE to be a string would have been enforceable, and
    -- it would have made this table unable to represent a refusal about the
    -- `source_reported_procurement_value_contrast` family -- 6 live Claims whose
    -- `notice_ids` and `classification_codes` are arrays of strings, which is
    -- legitimate cohort identity. Only 37 of 43 live Claims would have passed.
    CONSTRAINT proposition_evaluation_refusals_facts_discriminator_check
        CHECK (target_proposition_facts ? 'proposition'),

    CONSTRAINT proposition_evaluation_refusals_rationale_present_check
        CHECK (length(btrim(rationale)) > 0),

    -- IDENTITY. One evaluation is one workspace, one Signal, one candidate
    -- target, one rule version and one reviewed basis.
    --
    -- The rule version is in the key for the reason it is in the derivation key:
    -- replaying a different rule is different reasoning. The BASIS is in the key
    -- because it is an INPUT to gate 1 and the first thing the evaluator reads --
    -- changing it changes what was evaluated, so it is a new historical
    -- evaluation rather than an update to an old one. One Signal-target pair may
    -- therefore accumulate several refusals over time, which is what an
    -- append-only audit is.
    --
    -- There is no `superseded_at`, no `is_current` and no `replaces_id`. A later
    -- SUPPORTS under a new basis does not make an earlier UNKNOWN false, and
    -- deciding what supersedes what is a judgement nothing here is entitled to
    -- make.
    CONSTRAINT proposition_evaluation_refusals_identity_key
        UNIQUE (
            workspace_id,
            input_signal_id,
            target_proposition_key,
            derivation_rule_version,
            semantic_equivalence_basis_id
        )
);

CREATE INDEX idx_proposition_evaluation_refusals_signal
    ON research.proposition_evaluation_refusals (workspace_id, input_signal_id);
CREATE INDEX idx_proposition_evaluation_refusals_target
    ON research.proposition_evaluation_refusals (workspace_id, target_proposition_key);
CREATE INDEX idx_proposition_evaluation_refusals_threshold
    ON research.proposition_evaluation_refusals (workspace_id, threshold_registration_id);

-- -----------------------------------------------------------------------------
-- 2. Tenancy. Layer one is the repository filter, layer two is RLS, layer three
-- is the composite FK, and none replaces another (ADR-005, ADR-012).
-- -----------------------------------------------------------------------------

ALTER TABLE research.proposition_evaluation_refusals ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.proposition_evaluation_refusals FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.proposition_evaluation_refusals
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

COMMENT ON TABLE research.proposition_evaluation_refusals IS
    'One deterministic evaluation that declined: one rule, one Signal, one '
    'candidate proposition, one reviewed basis, and NOT_APPLICABLE or UNKNOWN. '
    'It creates no Claim and produces no Evidence, and it references no '
    'retention-bounded execution log, so it outlives the run that produced it. '
    'It answers what we tried and declined; it can never answer what we never '
    'considered, because an unreviewed pair produces no evaluation at all.';

COMMENT ON COLUMN research.proposition_evaluation_refusals.target_proposition_facts IS
    'The exact preimage of target_proposition_key, in the same vocabulary as '
    'research.claims.proposition_facts. Stored rather than referenced because no '
    'Claim exists to recover it from. The key is recomputed and compared by the '
    'producer and by tests; the database stores both halves and does not '
    'reimplement the Python canonicalisation to check them against each other.';

COMMENT ON COLUMN research.proposition_evaluation_refusals.threshold_registration_id IS
    'The threshold registration supplied to this evaluation attempt. Its '
    'PRESENCE does not mean the refusal consulted it: three of the seven reason '
    'codes return before the registration gate. The reason code is what says '
    'whether the registration was load-bearing.';

COMMENT ON COLUMN research.proposition_evaluation_refusals.reason_code IS
    'WHY the evaluation declined, where evaluation_result says WHAT happened. '
    'The seven codes the evaluator raises, none invented and none renamed. The '
    'rationale is human-readable and is the authority for neither.';
