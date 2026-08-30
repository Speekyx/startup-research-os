-- =============================================================================
-- 0017_interpreter_identity_null_safety.sql -- a CHECK that passed on NULL
--
-- Mission 1.13. Corrects a constraint migration 0016 added in the same mission,
-- forward-only, because 0016 has been applied and a migration is never edited
-- after it has been.
--
-- WHAT 0016 ASSERTED
--
--     CHECK (
--         (interpreter_id IS NULL AND interpreter_version IS NULL
--                                 AND interpretation_kind IS NULL)
--      OR (length(btrim(interpreter_id)) > 0
--          AND length(btrim(interpreter_version)) > 0
--          AND interpretation_kind IS NOT NULL)
--     )
--
-- It reads as "all three or none of the three", and it does not enforce that.
--
-- WHY IT DOES NOT
--
-- SQL three-valued logic. With `interpreter_id = 'x'` and
-- `interpreter_version = NULL`:
--
--     first branch    false        (interpreter_id is not null)
--     second branch   NULL         (length(btrim(NULL)) > 0 is NULL, and
--                                   NULL AND anything is NULL)
--     whole expression  false OR NULL  ->  NULL
--
-- and **a CHECK constraint accepts NULL**. It only rejects a row when the
-- expression evaluates to FALSE. So half an interpreter identity was written
-- without complaint, which is the guard silently not guarding -- found by the
-- probe that was written to believe it rather than by review.
--
-- WHAT REPLACES IT
--
-- `num_nonnulls` is a PostgreSQL built-in that returns a non-null integer, so
-- the arity test can never itself be NULL. The blankness tests are guarded
-- individually and each is written so a NULL input short-circuits to TRUE
-- rather than to NULL.
--
-- Forward-only. 0016 is not edited.
-- =============================================================================

ALTER TABLE research.claims
    DROP CONSTRAINT claims_interpreter_complete_check,
    ADD CONSTRAINT claims_interpreter_complete_check
        CHECK (
            num_nonnulls(interpreter_id, interpreter_version, interpretation_kind)
                IN (0, 3)
            AND (interpreter_id IS NULL OR length(btrim(interpreter_id)) > 0)
            AND (interpreter_version IS NULL OR length(btrim(interpreter_version)) > 0)
        );

COMMENT ON COLUMN research.claims.interpreter_id IS
    'Which interpreter produced this claim. Named in full with its version and '
    'kind, or absent entirely -- half an identity is a version nobody can '
    'resolve. Enforced with num_nonnulls because the obvious spelling of that '
    'rule evaluates to NULL on a half-filled row, and a CHECK accepts NULL.';
