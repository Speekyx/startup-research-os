-- =============================================================================
-- 0009_normalized_record_canonical.sql -- what a normalized observation carries
--
-- Mission 1.6 §57. The first mission that writes to
-- acquisition.normalized_records.
--
-- THE GAP (documented before the migration, per §4 and the convention 1.3 set)
--
-- Full analysis: docs/data/normalized-record-gap-analysis-v1.md. Nine
-- requirements cannot be represented by the existing columns at all:
--
--   1. THERE IS NOWHERE TO PUT THE CANONICAL REPRESENTATION. The table has no
--      payload column at all, and content_hash fingerprints content nothing
--      stores. Without it the row is metadata about a transformation whose
--      output was thrown away, and every downstream stage would have to re-run
--      the normalizer against a raw record that expires in 30 days while this
--      row lives 12 months.
--
--   2. NO RECORD KIND. §11 requires a minimal extensible taxonomy of canonical
--      shapes. Nothing said whether a payload is a numeric observation, a
--      document or a discussion post, so a consumer could not tell whether it
--      was safe to read as a measurement.
--
--   3. ONE VERSION COLUMN FOR TWO INDEPENDENT VERSIONS. §21 requires the
--      normalizer implementation version and the canonical schema version to
--      evolve separately. transformation_version is one TEXT field, so every
--      consumer would have had to parse it -- the same defect §8 names for URLs.
--      There was no normalizer_id either: with one normalizer a bare version
--      reads unambiguously, with two it does not, and the records written in
--      between become unauditable (Mission 1.5 §50, same argument).
--
--   4. A NORMALIZED REPRESENTATION HAD NO STABLE IDENTITY. PRIMARY KEY (id) and
--      no unique constraint over anything meaningful, so running the normalizer
--      twice inserted two rows and nothing noticed (§23).
--
--   5. NO OBSERVATION KEY AND NO REVISION MARKER. §7 and §48 require a revised
--      RawRecord to produce a revised NormalizedRecord with the earlier one
--      intact and distinguishable. Reaching the observation key through
--      raw_record_id works until day 31, when the raw record expires and the
--      lineage is gone -- which data-retention-policy-v1.md §4 exists to
--      prevent. And nothing could say "this is no longer the current
--      representation of its observation".
--
--   6. THE §8 LINEAGE QUESTIONS WERE NOT ANSWERABLE. Nine questions, four
--      answers. Which collector version, which review, which conditions, when
--      normalized -- all missing, and all readable from the raw record only
--      until it expires.
--
--   7. ATTRIBUTION HAD NOWHERE TO SURVIVE TO. §9 and §46: an obligation on the
--      RawRecord must still be on the NormalizedRecord. There was no column it
--      could occupy, so normalizing CC-BY-4.0 data would have produced a row
--      with no credit attached and no way to discover that it should have one.
--
--   8. A CROSS-TENANT REFERENCE WAS STRUCTURALLY POSSIBLE. §31: raw_record_id
--      referenced raw_records (id) alone, and raw_records had no
--      UNIQUE (workspace_id, id), so the composite FK could not even be
--      declared. Mission 1.2 established this pattern for claims and evidence;
--      this applies it.
--
--   9. QUALITY AND ITS REASONS COULD NOT BE RECORDED. §25 and §26 require a
--      structural quality state and, for anything below VALID, the reasons --
--      and forbid discarding a problematic RawRecord. With no column the only
--      options were to drop the record or to store it looking exactly like a
--      clean one.
--
-- WHAT IS DELIBERATELY NOT CHANGED
--
--   * acquisition.raw_records gains ONE unique constraint and nothing else.
--     §27: the raw layer records what the source returned, and normalization
--     does not get to make it more convenient. Its existing
--     UNIQUE (workspace_id, source_id, content_hash) is untouched -- it is what
--     makes raw idempotency and revision work, and replacing it would break
--     both (raw-record-gap-analysis-v1.md §3).
--   * nlp.signals, nlp.embedding_provenance, research.claims and
--     scoring.evidence are untouched. §42, §43 and §44 put signal extraction,
--     embeddings and claims outside this mission. The existing
--     normalized_record_id FKs already point here and need nothing.
--   * The RLS policies are untouched. New columns live in the same row and are
--     therefore already inside the same policy.
--   * No aggregation column anywhere. D-03 stays blocked.
--
-- THE ONE NON-ADDITIVE CHANGE
--
--   transformation_version is RENAMED to normalizer_version. §57 prefers
--   additive structure "unless existing semantics are genuinely incompatible",
--   and they are: one column cannot carry two independently-evolving versions.
--   Keeping the old name beside a new normalizer_version column would put one
--   fact in two places, which drifts. The table holds zero rows and nothing
--   reads the column, so the rename costs nothing and removes a name that would
--   have misled every future reader.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. The composite-FK precondition (GAP 8).
--
-- raw_records has PRIMARY KEY (id) only, so a foreign key carrying workspace_id
-- cannot reference it. research_sessions already gained its equivalent in 0005.
-- -----------------------------------------------------------------------------
ALTER TABLE acquisition.raw_records
    ADD CONSTRAINT raw_records_workspace_id_key UNIQUE (workspace_id, id);

-- -----------------------------------------------------------------------------
-- 2. The record-kind registry entry (GAP 2).
--
-- A registry ROW, not a CHECK list: Ontology V2 §14.3 makes evolving taxonomies
-- rows precisely so a new adapter does not need a migration. One entry, because
-- one adapter exists -- the same rule IMPLEMENTED_COLLECTORS is under.
-- -----------------------------------------------------------------------------
INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('normalization_record_kind', 'numeric_observation', 'Numeric observation',
     'One measured or reported numeric value for one metric, one geography and '
     'one period. The canonical shape produced by a statistical or economic '
     'indicator adapter (normalized-record-v1.md §5).')
ON CONFLICT (registry, id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 3. The canonical normalized record.
-- -----------------------------------------------------------------------------
ALTER TABLE acquisition.normalized_records
    -- GAP 3. One column cannot carry two versions that evolve independently.
    RENAME COLUMN transformation_version TO normalizer_version;

ALTER TABLE acquisition.normalized_records
    -- GAP 1. The canonical representation itself. Inline because a numeric
    -- observation is a few hundred bytes and object storage is D-10, undecided.
    ADD COLUMN payload JSONB NOT NULL,

    -- GAP 2. A registry reference, following nlp.signals exactly.
    ADD COLUMN record_kind_registry TEXT NOT NULL
        DEFAULT 'normalization_record_kind',
    ADD COLUMN record_kind_id TEXT NOT NULL,

    -- GAP 3. Four facts where there was one string.
    ADD COLUMN normalizer_id TEXT NOT NULL,
    ADD COLUMN normalization_schema_id TEXT NOT NULL,
    ADD COLUMN normalization_schema_version INTEGER NOT NULL,

    -- GAP 5. WHICH observation, inherited verbatim from the raw record and
    -- stable across both revisions and normalizer versions. Denormalized on
    -- purpose: the raw record expires eleven months before this one does.
    ADD COLUMN observation_key TEXT NOT NULL,
    -- Set when a LATER raw version of the same observation was normalized under
    -- the same (schema, normalizer) lineage. Never across lineages: writing
    -- schema 2 must not retire schema 1, which would be the selection policy
    -- §49 forbids inventing. The old row is kept either way.
    ADD COLUMN superseded_at TIMESTAMPTZ,

    -- GAP 6. Lineage, promoted where an auditor filters BY it.
    ADD COLUMN normalized_at TIMESTAMPTZ NOT NULL,
    ADD COLUMN correlation_id TEXT NOT NULL,
    ADD COLUMN collector_id TEXT NOT NULL,
    ADD COLUMN collector_version TEXT NOT NULL,
    ADD COLUMN review_version INTEGER NOT NULL,

    -- GAP 6 and GAP 7. Read WITH a record rather than searched across, and
    -- source-shaped: access profile, approval state, resource and dataset
    -- family, licence and its basis, content origin, the RENDERED ATTRIBUTION,
    -- the condition snapshot at collection time, the raw content hash and the
    -- resolved retention basis.
    ADD COLUMN provenance JSONB NOT NULL,

    -- GAP 9. Structural completeness, never an ML confidence: a value on [0,1]
    -- here would invite someone to multiply a parsing outcome by an evidence
    -- weight (§25).
    ADD COLUMN quality TEXT NOT NULL,
    ADD COLUMN quality_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Closed enum, TEXT + CHECK (ADR-008). validate_schema.py compares this
    -- list against the contract source of truth, so a value drifting from
    -- NormalizationQuality fails the build.
    ADD CONSTRAINT normalized_records_quality_check
        CHECK (quality IN ('VALID', 'PARTIAL', 'INVALID')),

    ADD CONSTRAINT normalized_records_observation_key_not_blank_check
        CHECK (length(btrim(observation_key)) > 0),
    ADD CONSTRAINT normalized_records_normalizer_identified_check
        CHECK (length(btrim(normalizer_id)) > 0
           AND length(btrim(normalizer_version)) > 0),
    ADD CONSTRAINT normalized_records_collector_identified_check
        CHECK (length(btrim(collector_id)) > 0
           AND length(btrim(collector_version)) > 0),
    ADD CONSTRAINT normalized_records_schema_version_check
        CHECK (normalization_schema_version >= 1),
    ADD CONSTRAINT normalized_records_review_version_check
        CHECK (review_version >= 1),
    -- A record written with an expiry in the past is a retention policy that
    -- was never applied. Anchored on normalized_at, not collected_at: the
    -- normalized window runs from when this representation was produced
    -- (data-retention-policy-v1.md §2.2).
    ADD CONSTRAINT normalized_records_expiry_after_normalization_check
        CHECK (expires_at > normalized_at),
    -- Normalization cannot precede collection.
    ADD CONSTRAINT normalized_records_normalized_after_collection_check
        CHECK (normalized_at >= collected_at),
    ADD CONSTRAINT normalized_records_quality_reasons_is_array_check
        CHECK (jsonb_typeof(quality_reasons) = 'array'),

    -- GAP 2. The registry is global and its entries are the authority; a kind
    -- nobody registered cannot be written.
    ADD CONSTRAINT normalized_records_record_kind_fkey
        FOREIGN KEY (record_kind_registry, record_kind_id)
        REFERENCES registry.registry_entries (registry, id),

    -- GAP 8. §31: a normalized record in workspace A referencing a raw record
    -- in workspace B is not rejected at runtime -- it cannot be written. The
    -- single-column FKs from 0001 stay: they carry the ON DELETE behaviour, and
    -- removing a guard because a stronger one exists is a regression (ADR-012).
    ADD CONSTRAINT normalized_records_raw_record_tenant_fkey
        FOREIGN KEY (workspace_id, raw_record_id)
        REFERENCES acquisition.raw_records (workspace_id, id) ON DELETE CASCADE,
    -- COLUMN-SPECIFIC, and it has to be. A multi-column ON DELETE SET NULL
    -- nulls EVERY referencing column by default, including workspace_id --
    -- which is NOT NULL, so deleting a session would fail rather than detach
    -- the record. Migration 0005 hit the same thing and resolved it the same
    -- way; PostgreSQL 15 added the column list for exactly this case.
    ADD CONSTRAINT normalized_records_session_tenant_fkey
        FOREIGN KEY (workspace_id, research_session_id)
        REFERENCES research.research_sessions (workspace_id, id)
        ON DELETE SET NULL (research_session_id),

    -- GAP 4. The identity of a normalized REPRESENTATION, and the one
    -- constraint that delivers three requirements at once:
    --
    --   same raw record, same versions        -> collides. Idempotency (§23)
    --   same raw record, other normalizer or
    --     schema version                      -> no collision. Re-normalization
    --                                            coexists (§24, §49)
    --   revised raw record, same versions     -> no collision. The revision is
    --                                            a new row and the old one
    --                                            survives (§7, §48)
    --
    -- A constraint over the OBSERVATION instead would have rejected every one
    -- of the inserts that record a revision or a re-normalization -- the same
    -- trap raw-record-gap-analysis-v1.md §3 documented one level down.
    ADD CONSTRAINT normalized_records_representation_unique
        UNIQUE (workspace_id, raw_record_id, normalization_schema_version,
                normalizer_id, normalizer_version);

COMMENT ON COLUMN acquisition.normalized_records.payload IS
    'The canonical representation of one source observation, in the shape the '
    'record kind declares. Never a source-native structure and never an '
    'interpretation: normalization renames and reshapes, it does not decide.';

COMMENT ON COLUMN acquisition.normalized_records.observation_key IS
    'Stable identity of the source observation, inherited verbatim from the raw '
    'record. Rows sharing one are the same observation at different upstream '
    'values or under different normalizer versions.';

COMMENT ON COLUMN acquisition.normalized_records.content_hash IS
    'sha256 over the canonical semantic payload. Deliberately excludes the '
    'normalization timestamp, the correlation id, the schema version and the '
    'normalizer version: identical content after an upgrade should hash '
    'identically, because that is the question an upgrade raises.';

COMMENT ON COLUMN acquisition.normalized_records.quality IS
    'Structural completeness of the canonical representation. NOT a confidence '
    'and NOT a reliability: those are epistemic judgments on [0,1] that belong '
    'to the evidence model.';

COMMENT ON COLUMN acquisition.normalized_records.provenance IS
    'The lineage read WITH a record rather than filtered by: access profile and '
    'method, approval state, resource and dataset family, licence and basis, '
    'content origin, rendered attribution, condition snapshot at collection, '
    'raw content hash and resolved retention basis.';

-- "Every normalized representation of this observation", newest first. The
-- access path §48 and §49 exist to make possible.
CREATE INDEX idx_normalized_records_observation_history
    ON acquisition.normalized_records
       (workspace_id, source_id, observation_key, normalized_at DESC);

-- "What did this correlation normalize", which is how an operator debugs a job.
CREATE INDEX idx_normalized_records_correlation
    ON acquisition.normalized_records (workspace_id, correlation_id);

-- "Which records did normalizer 1.1 write", which is the §21 audit.
CREATE INDEX idx_normalized_records_normalizer
    ON acquisition.normalized_records (normalizer_id, normalizer_version);

-- "Which raw records in this session have not been normalized yet", which is
-- how a batch job selects its work without scanning the table.
CREATE INDEX idx_normalized_records_raw_record
    ON acquisition.normalized_records (workspace_id, raw_record_id);
