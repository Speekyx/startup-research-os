-- =============================================================================
-- 0014_lexical_frequency_change.sql -- the first source-relative temporal type
--
-- Mission 1.12.1. Governed by docs/data/lexical-frequency-change-extractor-v1.md
-- and ADR-023 (gap semantics).
--
-- WHAT UNBLOCKED THIS
--
-- Mission 1.12 closed H-32 on first-party GDELT evidence: the WEB-NGRAM stream
-- is ordered. This is the first signal type that USES that ordering, and it is
-- the first one whose window basis is ORDERED_PERIODS rather than
-- SAME_PERIOD_LABEL or COMPARABLE_INSTANTS.
--
-- WHAT IS STILL BLOCKED
--
-- H-29 is open, so a signal of this type carries NO event time, NO timezone and
-- NO window bounds -- enforced by the CHECKs migration 0012 already added, which
-- need no change: `observed_at` stays NULL unless the basis is
-- COMPARABLE_INSTANTS, and this basis is not that.
--
-- Forward-only. Never edited after it has been applied anywhere.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. The signal type
--
-- A registry ROW, and vocabulary rather than a claim that code exists -- the
-- same rule migration 0012 registered its two entries under. `SIGNAL_EXTRACTORS`
-- in sros_nlp is what says an extractor exists.
-- -----------------------------------------------------------------------------
INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('signal_type', 'lexical_frequency_change', 'Lexical frequency change',
     'The change in one lexical term''s source-measured frequency between two '
     'ADJACENT source buckets of one WEB-NGRAM stream, under one source language '
     'label and one gram size. Says the measured frequency differed between two '
     'ordered buckets, and nothing about attention, interest, demand or trend. '
     'Requires the Mission 1.12 temporal order certification; the buckets are '
     'ordered relative to each other and are NOT placed on any shared timeline '
     '(lexical-frequency-change-extractor-v1.md).')
ON CONFLICT (registry, id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 2. NON_CONTIGUOUS_SOURCE_BUCKETS joins the refusal vocabulary
--
-- Two observations that ARE the same series, whose labels are not one published
-- step apart. INCOMPATIBLE_SERIES says they are observations of different
-- things and INSUFFICIENT_INPUT_OBSERVATIONS says there are too few; neither can
-- say that there are exactly two compatible ones with a hole between them.
--
-- Treating them as adjacent would invent continuity across a bucket nobody read,
-- and a change computed across an invented gap is indistinguishable from one
-- that happened (ADR-023).
-- -----------------------------------------------------------------------------
ALTER TABLE nlp.signal_inputs
    DROP CONSTRAINT signal_inputs_refusal_reason_check,
    -- The value set comes FIRST and the null branch second, so the schema
    -- validator's `CHECK (column IN (...))` match finds it (Mission 1.11).
    ADD CONSTRAINT signal_inputs_refusal_reason_check
        CHECK (refusal_reason IN (
                   'INPUT_RECORD_INVALID', 'REQUIRED_FACT_WITHHELD',
                   'AMBIGUOUS_OBSERVATION_LINEAGE', 'INCOMPATIBLE_INPUT_KINDS',
                   'INCOMPATIBLE_SERIES', 'NON_CONTIGUOUS_SOURCE_BUCKETS',
                   'INSUFFICIENT_INPUT_OBSERVATIONS', 'UNSUPPORTED_SIGNAL_TYPE',
                   'PARAMETERS_INCOMPLETE')
               OR refusal_reason IS NULL);
