-- =============================================================================
-- 0008_raw_record_provenance.sql -- what a collected observation has to carry
--
-- Mission 1.5 §51. The first mission that writes to acquisition.raw_records.
--
-- THE GAP (documented before the migration, per §51 and the convention 1.3 set)
--
-- Full analysis: docs/data/raw-record-gap-analysis-v1.md. Four requirements
-- cannot be represented by the existing columns at all:
--
--   1. A LOGICAL OBSERVATION HAS NO IDENTITY. §23/§24 require telling "the same
--      observation retrieved again unchanged" apart from "the source revised
--      it". Economic data is revised. With only content_hash, a revision lands
--      as a row unrelated to the one it revises, and "what has this source said
--      about FR GDP for 2020, and when did it change" cannot be asked.
--      parent_record_id exists and means *derivative of*, which is a different
--      relationship: a revision replaces its predecessor, it is not derived
--      from it.
--
--   2. NO EVENT TIME. data-principles.md §9: prefer event time over ingestion
--      time, because trend analysis on ingestion timestamps produces artifacts
--      that look exactly like real market movements -- and once the
--      ingestion-time column is the only one kept, it cannot be recovered.
--      normalized_records has observed_at; the raw layer did not.
--
--   3. PROVENANCE IS NOT ANSWERABLE. §19 lists fourteen things an analyst must
--      establish without inferring them from a URL string. The table answered
--      four. Packing the other ten into source_reference would be precisely the
--      inference §19 forbids.
--
--   4. NO COLLECTOR ATTRIBUTION. §50: a record must be traceable to the
--      implementation that produced it, so changing a collector does not make
--      old records unauditable.
--
-- WHAT IS DELIBERATELY NOT CHANGED
--
--   * UNIQUE (workspace_id, source_id, content_hash) STAYS. The first design
--     considered here replaced it, which would have been a mistake. The
--     fingerprint covers the canonical payload, and the payload contains the
--     observation's identifying facts -- so an unchanged re-retrieval collides
--     (idempotency, §23) while a revised value does not (revision, §24). A
--     unique constraint over the observation key would have REJECTED the very
--     insert that records a revision.
--   * normalized_records is untouched. Mission 1.6 owns normalization, and §36
--     is explicit that parsing a response into raw records is not that.
--   * The RLS policies are untouched. New columns live in the same row and are
--     therefore already inside the same policy.
-- =============================================================================

ALTER TABLE acquisition.raw_records
    -- 1. The stable identity of the source observation: source, resource,
    --    indicator, geography, period. Deliberately NOT over the value and NOT
    --    over the retrieval time -- either would make every revision a
    --    different observation, which is the bug this closes.
    ADD COLUMN observation_key   TEXT        NOT NULL,
    --    Set when a later retrieval of the SAME observation carried a different
    --    value. The old row is kept: "do not silently overwrite history" (§24).
    ADD COLUMN superseded_at     TIMESTAMPTZ,
    --    An unchanged re-retrieval produces no row. It moves this instead, so
    --    "we checked and it had not changed" is still recorded (§23).
    ADD COLUMN last_seen_at      TIMESTAMPTZ NOT NULL,

    -- 2. Event time. Nullable because some sources genuinely have none; for an
    --    indicator series it is the observation period and is always present.
    ADD COLUMN observed_at       TIMESTAMPTZ,

    -- 3. Provenance. The four promoted to columns are the ones an auditor
    --    filters BY -- which collector version wrote this, which review
    --    authorised it, what did this correlation produce. The rest is read
    --    WITH a record rather than searched across, and differs per source: an
    --    indicator id means nothing to a forum collector, and promoting it now
    --    would bake one source's shape into a table five more have to share.
    ADD COLUMN provenance        JSONB       NOT NULL,
    ADD COLUMN review_version    INTEGER     NOT NULL,
    ADD COLUMN correlation_id    TEXT        NOT NULL,

    -- 4. §50.
    ADD COLUMN collector_id      TEXT        NOT NULL,
    ADD COLUMN collector_version TEXT        NOT NULL,

    -- The payload itself, where it is small enough to be worth keeping inline.
    -- Object storage is D-10, undecided and unimplemented; payload_ref keeps its
    -- meaning by recording that the payload is here rather than pointing at a
    -- store that does not exist.
    ADD COLUMN payload           JSONB,

    ADD CONSTRAINT raw_records_observation_key_not_blank_check
        CHECK (length(btrim(observation_key)) > 0),
    ADD CONSTRAINT raw_records_collector_identified_check
        CHECK (length(btrim(collector_id)) > 0 AND length(btrim(collector_version)) > 0),
    ADD CONSTRAINT raw_records_review_version_check
        CHECK (review_version >= 1),
    -- A record that outlives its retention window by being written with an
    -- expiry in the past is a retention policy that was never applied.
    ADD CONSTRAINT raw_records_expiry_after_collection_check
        CHECK (expires_at > collected_at),
    ADD CONSTRAINT raw_records_last_seen_not_before_collection_check
        CHECK (last_seen_at >= collected_at);

COMMENT ON COLUMN acquisition.raw_records.observation_key IS
    'Stable identity of the source observation, over its identifying facts only. '
    'Two rows sharing one are the same observation at different upstream values.';

COMMENT ON COLUMN acquisition.raw_records.provenance IS
    'The Mission 1.5 §19 provenance set that is read with a record rather than '
    'searched across: access profile, resource and dataset identity, licence, '
    'content origin, attribution obligation, request and page identity.';

-- The access path for "the history of this observation", newest first.
CREATE INDEX idx_raw_records_observation_history
    ON acquisition.raw_records (workspace_id, source_id, observation_key, collected_at DESC);

-- "What did this correlation collect", which is how an operator debugs one job.
CREATE INDEX idx_raw_records_correlation
    ON acquisition.raw_records (workspace_id, correlation_id);

-- "Which records did this collector version write", which is the §50 audit.
CREATE INDEX idx_raw_records_collector
    ON acquisition.raw_records (collector_id, collector_version);
