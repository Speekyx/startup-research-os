-- =============================================================================
-- 0011 — the lexical-frequency record kind
--
-- Mission 1.10 §14. ONE registry row and NO schema change.
-- `acquisition.normalized_records` already carries `payload JSONB` and a
-- `record_kind_id` referencing this registry, so the storage the new kind needs
-- exists. What it does not have is permission to be stored: `record_kind_id`
-- has a foreign key to `registry.registry_entries`, and without this row every
-- insert naming the kind is refused.
--
-- WHY A MIGRATION AT ALL, given 0009's comment says a new adapter does not need
-- one. Two rules together make that claim false in practice, and both rules are
-- worth keeping:
--
--   * the FK above -- a kind the registry does not know cannot be persisted;
--   * `validate_normalization.py` asserts that the kinds declared in
--     `RECORD_KINDS` are exactly those a migration inserts, so the code
--     declaration and the row cannot drift.
--
-- The inconsistency is recorded in
-- `gdelt-normalized-record-gap-analysis-v1.md` §6.1 rather than fixed by
-- rewriting 0009, which is history and whose own row is correct.
--
-- WHAT THIS ROW IS NOT. It is a VOCABULARY entry, not a claim that an adapter
-- exists. `NORMALIZER_REGISTRY` and `IMPLEMENTED_NORMALIZERS` gain nothing in
-- Mission 1.10, and no GDELT record is normalized. The standing rule that a
-- name is added as the LAST step of building something applies to ADAPTERS --
-- `IMPLEMENTED_COLLECTORS`, `NORMALIZER_REGISTRY` -- and this is the row that
-- lets the model describe a shape, which is what Mission 1.10 is for.
--
-- Forward-only, like every migration here. Reversing it is deleting one row,
-- and it is safe to delete for as long as no normalized record references it.
-- =============================================================================

INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('normalization_record_kind', 'lexical_frequency_observation',
     'Lexical frequency observation',
     'One occurrence count the source measured for one lexical term, in one '
     'language, over one period. Source data: the term carries no '
     'classification -- it is not a theme, an entity or a topic -- and the '
     'count is not a signal, a score or a rank. Has no geography, because a '
     'language is not a place (normalized-record-v1.md §5.1).')
ON CONFLICT (registry, id) DO NOTHING;
