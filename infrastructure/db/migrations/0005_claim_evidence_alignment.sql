-- =============================================================================
-- 0005_claim_evidence_alignment.sql -- the Claim entity, and evidence realigned
--
-- Mission 1.2. Resolves A-13, opened by Mission 1.1: evidence aggregation is
-- claim-centric and no persisted Claim existed.
--
-- Governed by opportunity-ontology-v2.1.md §17, claim-model-v1.md,
-- evidence-aggregation-framework-v1.md, and ADR-015.
--
-- What this migration does:
--
--   1. research.claims                       stable identity, one per assertion
--   2. research.claim_revisions              append-only statement history
--   3. research.claim_session_observations   which session met the claim, when
--   4. scoring.evidence_independence_groups  which records share an origin
--   5. scoring.evidence                      realigned to the aggregation model
--
-- What it deliberately does NOT do:
--
--   * store an aggregation result. Persisting one would be scoring, and no
--     CALIBRATED profile exists (evidence-aggregation-framework-v1.md §14).
--     The columns a future result needs are named in claim-model-v1.md §11 so
--     the shape is known; the table is not created;
--   * decide the recomputation policy. D-08 stays open. This schema records
--     enough -- claim revision, evidence snapshot -- for either answer;
--   * touch migration 0001. Forward-only, always.
--
-- Cross-tenant integrity is enforced by COMPOSITE foreign keys carrying
-- workspace_id, not by application checks alone. A claim cannot reference an
-- opportunity in another workspace, evidence cannot reference a claim in
-- another workspace, and an independence group cannot span claims. Those are
-- structural impossibilities here rather than rules somebody has to remember.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. Composite unique keys, so composite foreign keys can reference them
--
-- `(workspace_id, id)` is redundant with the primary key on `id` alone. It
-- exists so a child table can declare a foreign key that carries workspace_id,
-- which is what makes a cross-tenant reference impossible rather than merely
-- forbidden. The redundancy is the price of that guarantee and it is small.
-- -----------------------------------------------------------------------------
ALTER TABLE research.opportunities
    ADD CONSTRAINT opportunities_workspace_id_key UNIQUE (workspace_id, id);

ALTER TABLE research.research_sessions
    ADD CONSTRAINT research_sessions_workspace_id_key UNIQUE (workspace_id, id);

-- =============================================================================
-- 1. research.claims -- the aggregation unit
--
-- Owned by `research` rather than `scoring`: a Claim is a domain assertion
-- about an Opportunity, not a scoring artefact (service-boundaries.md §1).
-- `scoring` reads claims and writes evidence evaluations; it does not own the
-- assertions themselves.
--
-- THE STATEMENT IS NOT HERE. It lives only in claim_revisions, so there is no
-- second copy that can drift from the history. A read joins; that is one join,
-- and it makes the drift structurally impossible rather than merely unlikely.
-- =============================================================================
CREATE TABLE research.claims (
    id                  UUID        PRIMARY KEY,
    workspace_id        UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,

    -- A claim belongs to exactly ONE opportunity in V1 (§9 of the brief).
    -- Cross-opportunity sharing is deliberately not modelled: if deduplication
    -- later shows the same assertion recurring, that is a separate decision and
    -- a shared-claim model would be much harder to reason about first.
    opportunity_id      UUID        NOT NULL,

    -- Epistemic category, NOT identity. A claim carries a ClaimType; a claim is
    -- not a ClaimType. Ontology V2 §7.
    claim_type          TEXT        NOT NULL,

    -- Editorial state. There is deliberately no VALIDATED value: evidence
    -- changes, and a lifecycle derived from EvidenceLevel would freeze a
    -- conclusion the evidence no longer supports (Mission 1.2 §38).
    lifecycle           TEXT        NOT NULL DEFAULT 'ACTIVE',
    withdrawn_reason    TEXT,

    -- Declared, never inferred from the source. The same platform carries an
    -- evergreen fact and a trend stale in a week
    -- (evidence-aggregation-framework-v1.md §9).
    temporality         TEXT        NOT NULL,

    -- The claim feature the aggregation profile keys its half-life on. A claim
    -- NAMES the key; it does not own the number. A TEMPORALLY_SENSITIVE claim
    -- whose feature has no authorised half-life reports
    -- MISSING_TEMPORAL_PARAMETER and produces no score, which is the designed
    -- behaviour rather than a gap.
    claim_feature       TEXT,

    -- What KIND of process produced this claim. Never a model name: those
    -- change constantly and belong in the provenance columns below, where a new
    -- one does not require a contract change.
    origin              TEXT        NOT NULL,

    -- Provenance. Answers: where did this assertion come from, during which
    -- session, by what process, with which model and prompt, and when.
    origin_session_id   UUID,
    origin_detail       TEXT,
    model_version       TEXT,
    prompt_version      TEXT,
    created_by          TEXT,

    -- Points at the live revision. The composite foreign key below guarantees
    -- it names a revision that exists.
    current_revision    INTEGER     NOT NULL DEFAULT 1,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT claims_opportunity_same_workspace_fkey
        FOREIGN KEY (workspace_id, opportunity_id)
        REFERENCES research.opportunities (workspace_id, id) ON DELETE CASCADE,
    -- SET NULL on the SESSION COLUMN ONLY (PostgreSQL 15+).
    --
    -- A bare `ON DELETE SET NULL` on a composite key nulls EVERY column in it,
    -- including workspace_id -- which is NOT NULL, so deleting a research
    -- session would fail with a constraint violation naming a column nobody
    -- touched. Found by the tenant-isolation delete test, not by review.
    --
    -- CASCADE would be worse than the bug: a claim is NOT owned by the session
    -- that first met it (Ontology V2.1 §17.4), so deleting a session must not
    -- delete the claims it discovered.
    CONSTRAINT claims_origin_session_same_workspace_fkey
        FOREIGN KEY (workspace_id, origin_session_id)
        REFERENCES research.research_sessions (workspace_id, id)
        ON DELETE SET NULL (origin_session_id),

    CONSTRAINT claims_claim_type_check
        CHECK (claim_type IN ('OBSERVED', 'INFERRED', 'PREDICTED',
                              'RECOMMENDED', 'HYPOTHESIS')),
    CONSTRAINT claims_lifecycle_check
        CHECK (lifecycle IN ('ACTIVE', 'WITHDRAWN')),
    CONSTRAINT claims_temporality_check
        CHECK (temporality IN ('EVERGREEN', 'TEMPORALLY_SENSITIVE')),
    CONSTRAINT claims_origin_check
        CHECK (origin IN ('MANUAL', 'DETERMINISTIC_EXTRACTION', 'LLM_EXTRACTION',
                          'INFERRED', 'SYSTEM_GENERATED', 'IMPORTED')),
    CONSTRAINT claims_current_revision_positive_check
        CHECK (current_revision >= 1),
    -- A withdrawal with no stated reason is indistinguishable from an accident.
    CONSTRAINT claims_withdrawn_reason_check
        CHECK (lifecycle <> 'WITHDRAWN' OR withdrawn_reason IS NOT NULL),
    -- Referenced by evidence and by observations, carrying workspace_id.
    CONSTRAINT claims_workspace_id_key UNIQUE (workspace_id, id)
);

COMMENT ON TABLE research.claims IS
    'An assertion about an Opportunity that evidence can independently support '
    'or contradict. Identity is stable across statement revisions; the statement '
    'itself lives in research.claim_revisions.';

CREATE INDEX idx_claims_workspace_opportunity
    ON research.claims (workspace_id, opportunity_id, created_at DESC);

CREATE INDEX idx_claims_workspace_lifecycle
    ON research.claims (workspace_id, lifecycle);

-- =============================================================================
-- 2. research.claim_revisions -- append-only statement history
--
-- Why revisions rather than immutable claims linked by supersession: identity
-- must survive a rewrite. Under supersession, revising a claim would produce a
-- new id, and every evidence record attached to the old one would either be
-- orphaned or have to be copied. The evidence set would fragment exactly when
-- the claim is being clarified.
--
-- Rows here are NEVER updated. An aggregation that evaluated revision 2 can
-- always re-read the text of revision 2, which is what makes a historical
-- result reproducible (Mission 1.2 §25).
-- =============================================================================
CREATE TABLE research.claim_revisions (
    id                  UUID        PRIMARY KEY,
    workspace_id        UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    claim_id            UUID        NOT NULL,
    revision            INTEGER     NOT NULL,

    -- The assertion, in words. Explicit and auditable, atomic enough to be
    -- supported or contradicted. Not an opportunity description, and never an
    -- opaque embedding: a claim nobody can read is a claim nobody can dispute.
    statement           TEXT        NOT NULL,

    -- Why the text changed. Free prose, because the useful answers are specific.
    revision_reason     TEXT,

    -- Author-declared: did the MEANING change, or only the wording?
    --
    -- Nothing acts on this automatically in V1, and that is deliberate --
    -- deciding what a material change does to previously attached evidence is
    -- part of D-08, which stays open. It is recorded now because it cannot be
    -- reconstructed later: only the person making the edit knows.
    material_change     BOOLEAN     NOT NULL DEFAULT FALSE,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by          TEXT,
    research_session_id UUID,

    CONSTRAINT claim_revisions_claim_same_workspace_fkey
        FOREIGN KEY (workspace_id, claim_id)
        REFERENCES research.claims (workspace_id, id) ON DELETE CASCADE,
    -- Column-specific, for the same reason as on `claims` above.
    CONSTRAINT claim_revisions_session_same_workspace_fkey
        FOREIGN KEY (workspace_id, research_session_id)
        REFERENCES research.research_sessions (workspace_id, id)
        ON DELETE SET NULL (research_session_id),
    CONSTRAINT claim_revisions_positive_check CHECK (revision >= 1),
    CONSTRAINT claim_revisions_statement_not_blank_check
        CHECK (length(btrim(statement)) > 0),
    CONSTRAINT claim_revisions_unique UNIQUE (workspace_id, claim_id, revision)
);

COMMENT ON TABLE research.claim_revisions IS
    'Append-only statement history. Rows are never updated: an aggregation that '
    'evaluated revision N must still be able to read revision N.';

CREATE INDEX idx_claim_revisions_claim
    ON research.claim_revisions (workspace_id, claim_id, revision DESC);

-- The pointer must name a revision that exists. DEFERRABLE because the claim
-- and its first revision are written in one transaction and each references the
-- other, so the check has to run at COMMIT -- the same pattern migration 0004
-- uses for a policy review and its evidence.
ALTER TABLE research.claims
    ADD CONSTRAINT claims_current_revision_fkey
    FOREIGN KEY (workspace_id, id, current_revision)
    REFERENCES research.claim_revisions (workspace_id, claim_id, revision)
    DEFERRABLE INITIALLY DEFERRED;

-- =============================================================================
-- 3. research.claim_session_observations
--
-- A Claim is NOT owned by the session that first met it, for the same reason an
-- Opportunity is not (Ontology V2 §12). Sessions produce observations; the same
-- claim accumulates evidence across many of them, and duplicating the claim
-- because a second session encountered it would split its evidence in two.
-- =============================================================================
CREATE TABLE research.claim_session_observations (
    id                  UUID        PRIMARY KEY,
    workspace_id        UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    claim_id            UUID        NOT NULL,
    research_session_id UUID        NOT NULL,

    observation_kind    TEXT        NOT NULL,
    notes               TEXT,
    observed_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT claim_observations_claim_same_workspace_fkey
        FOREIGN KEY (workspace_id, claim_id)
        REFERENCES research.claims (workspace_id, id) ON DELETE CASCADE,
    CONSTRAINT claim_observations_session_same_workspace_fkey
        FOREIGN KEY (workspace_id, research_session_id)
        REFERENCES research.research_sessions (workspace_id, id) ON DELETE CASCADE,
    CONSTRAINT claim_observations_kind_check
        CHECK (observation_kind IN ('DISCOVERED', 'CORROBORATED', 'CONTRADICTED')),
    -- Bookkeeping, not semantics: a session observes a given claim at most once.
    CONSTRAINT claim_observations_unique_per_session
        UNIQUE (workspace_id, claim_id, research_session_id)
);

CREATE INDEX idx_claim_observations_claim
    ON research.claim_session_observations (workspace_id, claim_id, observed_at DESC);

CREATE INDEX idx_claim_observations_session
    ON research.claim_session_observations (workspace_id, research_session_id);

-- =============================================================================
-- 4. scoring.evidence_independence_groups
--
-- A group means: these evidence records share an underlying information ORIGIN.
--
-- It does NOT mean they came from the same website. Two independent posts on
-- one platform are two observations; one announcement repeated by a blog and
-- then linked from a forum is three records and one observation. Confusing the
-- two is the failure evidence-confidence-framework-v1.md §4 was written against.
--
-- Owned by `scoring` because it is part of the evidence model that Evidence
-- Evaluation owns (service-boundaries.md §3). DETECTING these relationships is
-- `nlp`'s job and D-12 is open, so every group here is currently written
-- explicitly by a human or a test fixture.
--
-- Claim-scoped, so a group can never span unrelated claims.
-- =============================================================================
CREATE TABLE scoring.evidence_independence_groups (
    id                  UUID        PRIMARY KEY,
    workspace_id        UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    claim_id            UUID        NOT NULL,

    -- Why these records are believed to share an origin. Mandatory: a grouping
    -- with no stated basis collapses evidence strength for a reason nobody can
    -- re-check, and collapsing is the operation with the largest effect on a
    -- result.
    basis               TEXT        NOT NULL,

    -- The shared origin itself, where it is known and addressable -- the URL of
    -- the announcement, the id of the dataset. Optional because the origin is
    -- often inferred from content rather than located.
    origin_reference    TEXT,

    -- How the relationship was established. Free text rather than an enum:
    -- the useful values are unknown until nlp deduplication exists (D-12), and
    -- an enum invented now would be wrong.
    detection_method    TEXT        NOT NULL,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by          TEXT,

    CONSTRAINT independence_groups_claim_same_workspace_fkey
        FOREIGN KEY (workspace_id, claim_id)
        REFERENCES research.claims (workspace_id, id) ON DELETE CASCADE,
    CONSTRAINT independence_groups_basis_not_blank_check
        CHECK (length(btrim(basis)) > 0),
    -- Referenced by evidence, carrying BOTH workspace and claim, so a record
    -- cannot join a group belonging to a different claim.
    CONSTRAINT independence_groups_workspace_claim_id_key
        UNIQUE (workspace_id, claim_id, id)
);

COMMENT ON TABLE scoring.evidence_independence_groups IS
    'Evidence records sharing an underlying information origin. Not "same '
    'website": one announcement repeated by three outlets is one observation.';

CREATE INDEX idx_independence_groups_claim
    ON scoring.evidence_independence_groups (workspace_id, claim_id);

-- =============================================================================
-- 5. scoring.evidence -- realigned to the aggregation model
--
-- Mission 1.1 recorded two incompatibilities. Both are resolved here, cleanly,
-- because the table is empty and nothing writes to it. This is the cheapest it
-- will ever be.
--
-- I-2: evidence pointed at an opportunity, which is not the aggregation unit.
--      One opportunity carries many claims, some contradicted while others are
--      well supported; aggregating at the opportunity level would average away
--      exactly what the four-mass decomposition preserves.
--
-- I-1: `independence DOUBLE PRECISION` could not express independence. A scalar
--      cannot say WHICH records share an origin, so grouping had nothing to
--      group by -- and it invited `q * independence`, which is discounting
--      instead of grouping and lets ten discounted duplicates still outweigh
--      one original. It is DROPPED rather than reinterpreted: leaving a
--      quantitative-looking column beside the state would give two answers to
--      one question, and the numeric one would win.
-- =============================================================================

ALTER TABLE scoring.evidence DROP COLUMN independence;

-- The aggregation unit. Nullable ONLY so this migration can apply to a table
-- that already has rows in some future environment; there are none today, and
-- the repository refuses to write evidence without a claim.
ALTER TABLE scoring.evidence
    ADD COLUMN claim_id UUID,
    ADD COLUMN direction TEXT NOT NULL DEFAULT 'NEUTRAL',
    ADD COLUMN relevance DOUBLE PRECISION,
    ADD COLUMN directness DOUBLE PRECISION,
    ADD COLUMN extraction_confidence DOUBLE PRECISION,
    ADD COLUMN observation_category TEXT NOT NULL DEFAULT 'UNCATEGORISED',
    ADD COLUMN independence_state TEXT NOT NULL DEFAULT 'UNKNOWN',
    ADD COLUMN independence_group_id UUID;

-- The DEFAULT above exists so the ALTER can run; it is not the intended way to
-- write a row. Dropping it makes an omitted direction an error at INSERT rather
-- than a silent NEUTRAL, which would quietly remove a record from both
-- aggregations.
ALTER TABLE scoring.evidence ALTER COLUMN direction DROP DEFAULT;
ALTER TABLE scoring.evidence ALTER COLUMN observation_category DROP DEFAULT;

-- UNKNOWN keeps its default, and that one IS intended: unestablished provenance
-- is the honest starting state for every record, and it is the conservative one
-- (evidence-aggregation-framework-v1.md §7).

ALTER TABLE scoring.evidence
    ADD CONSTRAINT evidence_claim_same_workspace_fkey
        FOREIGN KEY (workspace_id, claim_id)
        REFERENCES research.claims (workspace_id, id) ON DELETE CASCADE,

    -- Carries workspace AND claim: a record cannot join a group belonging to
    -- another claim, in another workspace, or both.
    -- RESTRICT, not SET NULL.
    --
    -- SET NULL was the first attempt and it contradicted the shape CHECK below:
    -- nulling the group leaves a KNOWN_DEPENDENT record depending on nothing,
    -- which the CHECK forbids, so the delete failed with a confusing violation
    -- on a different constraint. A test caught it.
    --
    -- RESTRICT is the honest rule. A grouping with members cannot simply
    -- vanish: deleting one is a decision about every record that declared
    -- itself dependent on it, and those records must be corrected -- to
    -- KNOWN_INDEPENDENT, to UNKNOWN, or to another group -- first. Making the
    -- caller do that is the point; silently nulling would leave evidence whose
    -- provenance claim no longer means anything.
    ADD CONSTRAINT evidence_independence_group_same_claim_fkey
        FOREIGN KEY (workspace_id, claim_id, independence_group_id)
        REFERENCES scoring.evidence_independence_groups (workspace_id, claim_id, id)
        ON DELETE RESTRICT,

    ADD CONSTRAINT evidence_direction_check
        CHECK (direction IN ('SUPPORTS', 'CONTRADICTS', 'NEUTRAL')),
    ADD CONSTRAINT evidence_observation_category_check
        CHECK (observation_category IN ('STATED_OPINION', 'REPORTED_BEHAVIOUR',
                                        'OBSERVED_BEHAVIOUR', 'MARKET_ACTIVITY',
                                        'DIRECT_VALIDATION', 'UNCATEGORISED')),
    ADD CONSTRAINT evidence_independence_state_check
        CHECK (independence_state IN ('KNOWN_INDEPENDENT', 'KNOWN_DEPENDENT', 'UNKNOWN')),

    -- The three-state model, enforced rather than documented. A nullable group
    -- id alone is NOT the independence model: it cannot distinguish "checked,
    -- independent" from "never checked", and those call for different work.
    --
    --   KNOWN_DEPENDENT    must name its group -- dependent on WHAT?
    --   KNOWN_INDEPENDENT  must not, or it claims both at once
    --   UNKNOWN            must not. The engine builds its conservative runtime
    --                      bucket without writing one here, so an unresolved
    --                      question never looks resolved in storage
    ADD CONSTRAINT evidence_independence_shape_check
        CHECK (
            (independence_state = 'KNOWN_DEPENDENT'   AND independence_group_id IS NOT NULL)
         OR (independence_state = 'KNOWN_INDEPENDENT' AND independence_group_id IS NULL)
         OR (independence_state = 'UNKNOWN'           AND independence_group_id IS NULL)
        ),

    ADD CONSTRAINT evidence_relevance_unit_interval_check
        CHECK (relevance IS NULL OR (relevance BETWEEN 0 AND 1)),
    ADD CONSTRAINT evidence_directness_unit_interval_check
        CHECK (directness IS NULL OR (directness BETWEEN 0 AND 1)),
    ADD CONSTRAINT evidence_extraction_confidence_unit_interval_check
        CHECK (extraction_confidence IS NULL
               OR (extraction_confidence BETWEEN 0 AND 1));

COMMENT ON COLUMN scoring.evidence.claim_id IS
    'The aggregation unit. Evidence bears on a CLAIM, not on an Opportunity: one '
    'opportunity carries many claims with different evidence.';

COMMENT ON COLUMN scoring.evidence.reliability IS
    'How much THIS record can be relied on for THIS claim given how it was '
    'collected. Never a source reputation: a platform is not a reliability '
    '(evidence-aggregation-framework-v1.md §3).';

COMMENT ON COLUMN scoring.evidence.extraction_confidence IS
    'Confidence that the extraction read the record correctly. NOT confidence '
    'that the claim is true. May be absent for a manually authored record, in '
    'which case aggregation reports it non-scorable rather than inventing one.';

CREATE INDEX idx_evidence_workspace_claim
    ON scoring.evidence (workspace_id, claim_id, collected_at DESC);

CREATE INDEX idx_evidence_independence_group
    ON scoring.evidence (workspace_id, independence_group_id);

-- =============================================================================
-- 6. Row-level security
--
-- Every table above is tenant data, so every one gets a policy. ENABLE plus
-- FORCE, because ENABLE alone exempts the table owner and in a deployment where
-- the application connects as the owner that exemption is the entire protection
-- (ADR-012).
--
-- The grants come from the ALTER DEFAULT PRIVILEGES in 0003, which covers
-- future tables in research and scoring -- so a new table is not silently
-- unreachable by the runtime after a migration.
-- =============================================================================
ALTER TABLE research.claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.claims FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.claims
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE research.claim_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.claim_revisions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.claim_revisions
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE research.claim_session_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.claim_session_observations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.claim_session_observations
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE scoring.evidence_independence_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE scoring.evidence_independence_groups FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON scoring.evidence_independence_groups
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());
