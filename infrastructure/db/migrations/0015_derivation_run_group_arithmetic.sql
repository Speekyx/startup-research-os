-- =============================================================================
-- 0015_derivation_run_group_arithmetic.sql -- a group can derive AND refuse
--
-- Mission 1.12.1. Corrects a constraint migration 0013 added, which encoded an
-- assumption the third extractor falsified.
--
-- WHAT 0013 ASSERTED
--
--     CHECK (groups_derived + groups_refused <= groups_considered)
--
-- It reads as arithmetic and it is really a claim: that a candidate group either
-- produces signals or produces refusals. That was true of both Mission 1.11.1
-- extractors, because each group yielded one outcome.
--
-- WHY IT IS FALSE
--
-- `lexical-frequency-change` pairs ADJACENT buckets within one lexical series,
-- and one series can contain both a contiguous pair and a gap. The first real
-- derivation hit exactly that: three buckets for one term, one adjacent pair
-- emitting a signal and one non-contiguous pair refused. One group, one signal,
-- one refusal -- and 1 + 1 > 1.
--
-- The counters were right and the constraint was wrong. `groups_derived` counts
-- groups that produced at least one signal and `groups_refused` counts groups
-- that produced at least one refusal; those sets OVERLAP, and a partial outcome
-- is the ordinary case for any extractor that pairs within a group.
--
-- WHAT REPLACES IT
--
-- Each counter is bounded by the number of groups considered, separately. That
-- is the invariant that was always true and the only one worth asserting: a
-- group cannot be counted more than once in either column.
--
-- `records_contributed + records_excluded <= records_considered` is UNCHANGED.
-- Those two sets are genuinely disjoint -- Mission 1.11.1 made them so after the
-- same constraint caught a double count -- and the invariant still holds.
--
-- Forward-only. 0013 is not edited.
-- =============================================================================

ALTER TABLE nlp.signal_derivation_runs
    DROP CONSTRAINT signal_derivation_runs_group_arithmetic_check,
    ADD CONSTRAINT signal_derivation_runs_group_arithmetic_check
        CHECK (groups_derived <= groups_considered
           AND groups_refused <= groups_considered);

COMMENT ON COLUMN nlp.signal_derivation_runs.groups_derived IS
    'Candidate groups that produced at least one signal. OVERLAPS '
    'groups_refused: a group pairing within itself can emit a signal for one '
    'pair and refuse another, which is the ordinary case for a sequential '
    'extractor rather than an anomaly.';

COMMENT ON COLUMN nlp.signal_derivation_runs.groups_refused IS
    'Candidate groups that produced at least one refusal. Overlaps '
    'groups_derived; the `refusals` array is what says how many refusals there '
    'were and why, and it is the field an operator reads.';
