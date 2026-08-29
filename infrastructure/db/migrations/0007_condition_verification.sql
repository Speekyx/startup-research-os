-- =============================================================================
-- 0007_condition_verification.sql -- who decided a condition holds, and why
--
-- Mission 1.4 §18, §40. Migration 0006 gave each review condition a row and a
-- `satisfied` boolean. That was enough to BLOCK; it is not enough to CLEAR.
--
-- THE GAP (documented before the migration, as 1.3 §45 established)
--
-- `registry.source_review_conditions` records satisfaction as three columns:
-- `satisfied`, `satisfied_at`, `satisfied_by`. Those answer "is it satisfied"
-- and "who said so". They cannot answer:
--
--     * which verifier decided it, and at what version;
--     * what the verifier actually looked at;
--     * why -- in words a reader can check;
--     * what the answer was when it was NOT a clean yes. The column is a
--       boolean, so "we could not establish it" and "it does not hold" collapse
--       into the same FALSE, and §19 requires them to stay apart;
--     * what the previous answer was. A boolean has no history, so a condition
--       that silently flipped leaves no trace.
--
-- Every one of those is needed the moment a condition can actually be cleared,
-- because clearing one is the step that makes a source collectable.
--
-- WHAT THIS DOES
--
-- Adds an APPEND-ONLY verification log, and a trigger that makes the boolean
-- unsettable without a record in it. `satisfied` stays where it is and keeps
-- exactly the meaning the eligibility view already gives it -- the view is not
-- touched (§40: do not redesign the registry for convenience).
--
-- WHAT THIS DOES NOT DO
--
--   * it satisfies nothing. Applying this migration changes no condition's
--     state, and a database migrated but never verified is a database where
--     every condition is still unsatisfied;
--   * it does not let a human confirmation be fabricated. A HUMAN_CONFIRMATION
--     condition needs a person to write a record naming themselves; no verifier
--     in this codebase writes one (§21);
--   * it stores no credential. A CONFIG_REFERENCE verification records the KEY
--     NAME it looked for and whether it was present -- never the value, which a
--     CHECK constraint enforces rather than a convention.
-- =============================================================================

CREATE TABLE registry.source_condition_verifications (
    id                  UUID        PRIMARY KEY,

    condition_id        UUID        NOT NULL
        REFERENCES registry.source_review_conditions (id) ON DELETE CASCADE,
    source_id           TEXT        NOT NULL
        REFERENCES registry.sources (id) ON DELETE CASCADE,
    -- Denormalised so the log stays readable after a condition row is gone.
    -- A verification whose subject can no longer be named is not evidence.
    condition_key       TEXT        NOT NULL,

    -- WHO decided. A name, not a person: these are programs. A human decision
    -- is recorded by a human writing a row with their own identifier here.
    verifier            TEXT        NOT NULL,
    -- Verifiers change. A satisfaction recorded by version 1.0.0 of a checker
    -- that has since been rewritten is a fact about the old checker, and a
    -- reader has to be able to see that.
    verifier_version    TEXT        NOT NULL,

    -- Four values, never a boolean (§19). UNKNOWN is not UNSATISFIED: one means
    -- the check ran and failed, the other means it could not run, and they call
    -- for different work. Neither clears the gate.
    result              TEXT        NOT NULL,
    -- In words. A result with no reason is a verdict nobody can argue with,
    -- which is the shape a wrong one keeps for longest.
    reason              TEXT        NOT NULL,
    -- WHAT was looked at: a capability name, a configuration KEY name, an
    -- access-profile label, an evidence URL.
    reference           TEXT,

    verified_at         TIMESTAMPTZ NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT source_condition_verifications_result_check
        CHECK (result IN ('SATISFIED', 'UNSATISFIED', 'UNKNOWN', 'NOT_APPLICABLE')),
    CONSTRAINT source_condition_verifications_verifier_not_blank_check
        CHECK (length(btrim(verifier)) > 0 AND length(btrim(verifier_version)) > 0),
    CONSTRAINT source_condition_verifications_reason_not_blank_check
        CHECK (length(btrim(reason)) > 0),
    -- The registry is not a vault (Mission 1.0 §18, source-registry-v1.md §1.4).
    -- A CONFIG_REFERENCE verifier answers CONFIGURED / NOT_CONFIGURED and must
    -- never carry the value it found. Mechanical rather than remembered: the
    -- same shapes the Python model refuses, refused again here, because this is
    -- the one table a verifier writes free text into.
    CONSTRAINT source_condition_verifications_no_secret_value_check
        CHECK (
            (coalesce(reference, '') || ' ' || reason) !~
            '(-----BEGIN [A-Z ]*PRIVATE KEY-----|\ygh[pousr]_[A-Za-z0-9]{16,}|\ygithub_pat_[A-Za-z0-9_]{20,}|\ysk-[A-Za-z0-9]{20,}|\yxox[baprs]-[A-Za-z0-9-]{10,}|\yAIza[0-9A-Za-z_-]{35}|\yAKIA[0-9A-Z]{16})'
        )
);

COMMENT ON TABLE registry.source_condition_verifications IS
    'Append-only log of every attempt to establish that a review condition '
    'holds. The gate reads source_review_conditions.satisfied; this table is '
    'why that boolean is allowed to be true, and the only thing that can make '
    'it true.';

CREATE INDEX idx_condition_verifications_condition
    ON registry.source_condition_verifications (condition_id, verified_at DESC);

CREATE INDEX idx_condition_verifications_source
    ON registry.source_condition_verifications (source_id, result);

GRANT SELECT ON registry.source_condition_verifications TO sros_app;

-- -----------------------------------------------------------------------------
-- The boolean cannot be set by hand.
--
-- Mission 1.4 §2: "No source may become eligible through a manual boolean, a
-- hard-coded source exception, a test fixture override, a SQL update bypass or
-- a developer-only shortcut."
--
-- Four of those five are addressed in code. This trigger is the one that closes
-- the SQL bypass: an UPDATE setting `satisfied = TRUE` fails unless a
-- verification record for that condition says SATISFIED, whoever issues it and
-- whatever client it comes from.
--
-- Clearing a condition is deliberately NOT guarded. Going back to unsatisfied
-- is always allowed, because failing closed must never need permission.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION registry.require_verification_for_satisfied_condition()
    RETURNS trigger
    LANGUAGE plpgsql
    SET search_path = pg_catalog, registry
AS $$
BEGIN
    IF NEW.satisfied IS NOT TRUE THEN
        RETURN NEW;
    END IF;

    IF NOT EXISTS (
        SELECT 1
          FROM registry.source_condition_verifications v
         WHERE v.condition_id = NEW.id
           AND v.result = 'SATISFIED'
    ) THEN
        RAISE EXCEPTION
            'condition % on source % cannot be marked satisfied with no verification '
            'record. A condition is cleared by a verifier that says what it checked '
            'and why, never by setting a boolean (Mission 1.4 §2, §18).',
            NEW.condition_key, NEW.source_id
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_review_conditions_require_verification
    BEFORE INSERT OR UPDATE OF satisfied ON registry.source_review_conditions
    FOR EACH ROW EXECUTE FUNCTION registry.require_verification_for_satisfied_condition();
