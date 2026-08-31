-- =============================================================================
-- 0019_evidence_reliability_assessments.sql -- where a reviewed reliability
-- lives, and why it is not a source coefficient
--
-- Mission 1.14. Governed by docs/data/evidence-reliability-contract-v1.md and
-- ADR-026.
--
-- THE PROBLEM
--
-- `evidence-aggregation-framework-v1.md` §3 says reliability is a property of
-- THIS evidence record, against THIS claim, given how it was collected. That is
-- right and it is unscalable: it asks for a human judgement per Evidence row.
--
-- The two obvious escapes are both forbidden, and for the same reason:
--
--     source_reliability['world-bank'] = 0.95    a platform is not a
--                                                reliability -- the same
--                                                platform carries a methodology
--                                                note and a rumour
--
--     reliability = 0.5 because unknown          a measurement claiming the
--                                                middle, entering min() as a
--                                                real number
--
-- WHAT THIS IS
--
-- A middle term. An assessment applies to a FIVE-PART scope:
--
--     source_id | resource_id | record_kind_id     the MEASUREMENT
--     claim_type | proposition_kind                the PURPOSE
--
-- `world-bank` alone matches nothing. All five must match, so a value assessed
-- for "restating what World Bank published about a metric between two periods"
-- can never reach a claim about demand -- that claim has a different
-- proposition_kind and matches no assessment at all.
--
-- `proposition_kind` is not invented here. Mission 1.13.1 put a discriminator
-- at the head of every proposition_facts object so two proposition shapes could
-- not collide in a hash. It names what a claim asserts IN KIND, which is
-- exactly what "purpose" means in "reliability is purpose-relative".
--
-- WHY A SEPARATE SCHEMA
--
-- `registry` answers "may we collect this?". This answers "how dependable is
-- this measurement for this purpose?". They are unrelated, and putting an
-- epistemic judgement in registry.source_policy_reviews would make legal
-- permission and measurement quality one row -- the category error the
-- aggregation framework's §3 names in both directions:
--
--     an APPROVED source does not produce more reliable evidence;
--     a RESTRICTED source does not produce less reliable evidence.
--
-- GLOBAL, NOT TENANT
--
-- An assessment is a statement about a published dataset's measurement
-- contract, evidenced by the publisher's own documentation. Making it
-- tenant-scoped would mean every workspace re-reviewing the same methodology,
-- producing several answers to one question with nothing to say which is right.
-- The same argument that makes registry.sources global (ADR-012 §4).
--
-- No workspace_id, no RLS policy, and therefore NO TENANT LEAKAGE PATH -- which
-- is a stronger property than a correctly written policy. A workspace-scoped
-- assessment is imaginable and is NOT built; ADR-026 Decision 3 records what
-- adding one would take.
--
-- Forward-only. Never edited after it has been applied anywhere.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS epistemic;

COMMENT ON SCHEMA epistemic IS
    'Reviewed judgements about how dependable a MEASUREMENT is for a PURPOSE. '
    'Deliberately separate from `registry`, which answers whether the system may '
    'collect a source at all: legal permission and measurement quality are '
    'different concerns, and no formula converts one into the other.';

-- -----------------------------------------------------------------------------
-- 1. The assessment
-- -----------------------------------------------------------------------------
CREATE TABLE epistemic.reliability_assessments (
    id                     UUID        PRIMARY KEY,

    -- sha256 over the canonical JSON of the five scope columns below. Two
    -- reviewers assessing the same scope collide on one key; a reviewer
    -- revisiting a scope is recognised as revisiting it. The same construction
    -- research.claims.proposition_key uses one layer down, for the same reason.
    -- NOT versioned: (assessment_key, version) is the row.
    assessment_key         TEXT        NOT NULL,
    version                INTEGER     NOT NULL,

    -- ---- the MEASUREMENT ----------------------------------------------------
    source_id              TEXT        NOT NULL REFERENCES registry.sources (id)
                                       ON DELETE RESTRICT,
    -- The published stream or dataset. A source with two resources is two
    -- measurements: GDELT publishes `web-ngrams/1gram` beside an unreviewed
    -- `chargram` file, and one assessment must never cover both (ADR-022's
    -- scoping argument, applied to quality instead of ordering).
    resource_id            TEXT        NOT NULL,
    -- What shape of observation it was normalized into. A numeric series and a
    -- lexical frequency are not the same measurement even from one publisher.
    record_kind_registry   TEXT        NOT NULL DEFAULT 'normalization_record_kind',
    record_kind_id         TEXT        NOT NULL,

    -- ---- the PURPOSE --------------------------------------------------------
    -- The epistemic type of the claim this evidence bears on. An OBSERVED
    -- restatement and an INFERRED reading of the same measurement are different
    -- purposes with different dependability.
    claim_type             TEXT        NOT NULL,
    -- The proposition_facts discriminator. THIS is what makes the scope
    -- purpose-relative rather than source-shaped.
    proposition_kind       TEXT        NOT NULL,

    -- ---- the judgement ------------------------------------------------------
    -- [0,1], the scale evidence-aggregation-framework-v1.md §4 already uses.
    -- NOT NULL: an assessment that asserts no value is not an assessment, and
    -- "we do not know" is expressed by there being no row (§10).
    reliability            DOUBLE PRECISION NOT NULL,
    origin                 TEXT        NOT NULL,
    -- Required for CALIBRATED_EMPIRICALLY and refused otherwise. A calibration
    -- nobody can re-run is a claim, not a calibration -- the rule
    -- evidence-aggregation-framework-v1.md §12 already applies to profiles.
    calibration_dataset_ref TEXT,

    -- What the value asserts and what it does not, in the reviewer's words.
    -- Free text, and NOT the basis: the basis is the child table, and a
    -- rationale with no document behind it is an opinion with a citation field.
    rationale              TEXT        NOT NULL,
    -- The limitation the value is bounded BY. Required, because a reliability
    -- with no stated failure mode is a number nobody can argue with.
    stated_limitation      TEXT        NOT NULL,

    reviewed_by            TEXT        NOT NULL,
    reviewed_at            TIMESTAMPTZ NOT NULL,
    review_interval_days   INTEGER,
    next_review_at         TIMESTAMPTZ,
    -- Append-only by supersession, never by update. An aggregation that used
    -- version N must still be able to read version N (§17).
    superseded_at          TIMESTAMPTZ,
    superseded_by          UUID        REFERENCES epistemic.reliability_assessments (id),
    superseded_reason      TEXT,

    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT reliability_assessments_version_positive_check
        CHECK (version >= 1),
    CONSTRAINT reliability_assessments_key_shape_check
        CHECK (assessment_key ~ '^[0-9a-f]{64}$'),
    -- The unit interval, and rejected rather than clamped: a value outside it
    -- means the reviewer is on a different scale, and clamping would hide that
    -- behind a plausible number.
    CONSTRAINT reliability_assessments_unit_interval_check
        CHECK (reliability >= 0 AND reliability <= 1),
    CONSTRAINT reliability_assessments_origin_check
        CHECK (origin IN ('HUMAN_REVIEW', 'DOCUMENTED_METHOD', 'CALIBRATED_EMPIRICALLY')),
    -- No MODEL_GUESSED, and the closed list is what makes that enforceable
    -- rather than merely stated. A model may help a reviewer read a document;
    -- it may not be the epistemic source of the judgement.
    CONSTRAINT reliability_assessments_calibration_ref_check
        CHECK (
            (origin = 'CALIBRATED_EMPIRICALLY' AND calibration_dataset_ref IS NOT NULL)
         OR (origin <> 'CALIBRATED_EMPIRICALLY' AND calibration_dataset_ref IS NULL)
        ),
    CONSTRAINT reliability_assessments_claim_type_check
        CHECK (claim_type IN ('OBSERVED', 'INFERRED', 'PREDICTED', 'RECOMMENDED', 'HYPOTHESIS')),
    CONSTRAINT reliability_assessments_scope_identified_check
        CHECK (length(btrim(resource_id)) > 0
           AND length(btrim(record_kind_id)) > 0
           AND length(btrim(proposition_kind)) > 0),
    CONSTRAINT reliability_assessments_reviewer_identified_check
        CHECK (length(btrim(reviewed_by)) > 0),
    -- A rationale and a limitation are both required and both must say
    -- something. "World Bank is trustworthy" would pass this check and fail the
    -- basis requirement below, which is where it belongs.
    CONSTRAINT reliability_assessments_rationale_check
        CHECK (length(btrim(rationale)) > 0 AND length(btrim(stated_limitation)) > 0),
    -- Supersession is all-or-nothing, spelled so it cannot evaluate to NULL:
    -- the obvious spelling returns NULL on a half-filled row and a CHECK
    -- ACCEPTS NULL (migration 0017's lesson).
    CONSTRAINT reliability_assessments_supersession_complete_check
        CHECK (num_nonnulls(superseded_at, superseded_reason) IN (0, 2)),
    CONSTRAINT reliability_assessments_not_self_superseding_check
        CHECK (superseded_by IS NULL OR superseded_by <> id),

    CONSTRAINT reliability_assessments_version_unique
        UNIQUE (assessment_key, version),
    CONSTRAINT reliability_assessments_record_kind_fkey
        FOREIGN KEY (record_kind_registry, record_kind_id)
        REFERENCES registry.registry_entries (registry, id)
);

-- AT MOST ONE CURRENT assessment per scope. This is what makes the resolver's
-- ambiguous case unreachable through the ordinary path -- and the resolver
-- refuses anyway, because a guard that trusts another guard is one schema
-- change away from trusting nothing.
CREATE UNIQUE INDEX idx_reliability_assessments_current
    ON epistemic.reliability_assessments (assessment_key)
    WHERE superseded_at IS NULL;

-- The resolver's lookup: the full five-part scope, current rows only.
CREATE INDEX idx_reliability_assessments_scope
    ON epistemic.reliability_assessments
       (source_id, resource_id, record_kind_id, claim_type, proposition_kind)
    WHERE superseded_at IS NULL;

CREATE INDEX idx_reliability_assessments_review_due
    ON epistemic.reliability_assessments (next_review_at)
    WHERE superseded_at IS NULL AND next_review_at IS NOT NULL;

COMMENT ON TABLE epistemic.reliability_assessments IS
    'A reviewed statement that a MEASUREMENT (source, resource, record kind) has '
    'reliability R for a PURPOSE (claim type, proposition kind). Never a source '
    'coefficient: all five scope parts must match, so a value assessed for one '
    'purpose cannot reach another. Superseded, never updated.';

COMMENT ON COLUMN epistemic.reliability_assessments.proposition_kind IS
    'The research.claims.proposition_facts discriminator. What makes this scope '
    'purpose-relative rather than source-shaped: the same World Bank record used '
    'for a demand proposition has a different kind and matches nothing.';

COMMENT ON COLUMN epistemic.reliability_assessments.stated_limitation IS
    'What bounds this value -- the failure mode it is discounted FOR. A '
    'reliability with no stated limitation is a number nobody can argue with.';

-- -----------------------------------------------------------------------------
-- 2. The documentary basis
--
-- Shaped after registry.source_policy_evidence, deliberately: the system
-- already has a pattern for "this judgement rests on these retrieved
-- documents", and an epistemic review needs exactly the same discipline.
--
-- Full documents are NOT stored. They are third-party copyrighted text, and
-- copying them wholesale would be the same disregard for source terms the
-- registry exists to prevent. What is stored is a reference, a retrieval time,
-- a section pointer, a short summarized finding and a fingerprint.
-- -----------------------------------------------------------------------------
CREATE TABLE epistemic.reliability_assessment_basis (
    id                   UUID        PRIMARY KEY,
    assessment_id        UUID        NOT NULL
                                     REFERENCES epistemic.reliability_assessments (id)
                                     ON DELETE CASCADE,

    basis_type           TEXT        NOT NULL,
    document_title       TEXT        NOT NULL,
    -- NULL only for REVIEWER_DOCUMENTED_JUDGEMENT, which is reasoning ABOUT the
    -- other rows rather than a document of its own.
    document_url         TEXT,
    section_reference    TEXT,
    -- A short paraphrase of what the document says, in the reviewer's words.
    summarized_finding   TEXT        NOT NULL,
    excerpt              TEXT,
    retrieved_at         TIMESTAMPTZ,
    effective_at         TIMESTAMPTZ,
    document_fingerprint TEXT,

    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT reliability_assessment_basis_type_check
        CHECK (basis_type IN ('SOURCE_DOCUMENTATION', 'DATASET_METHODOLOGY',
                              'MEASUREMENT_METHODOLOGY', 'KNOWN_LIMITATION',
                              'INDEPENDENT_VALIDATION', 'OFFICIAL_STATISTICAL_METHOD',
                              'CORPUS_CONSTRUCTION_METHOD',
                              'REVIEWER_DOCUMENTED_JUDGEMENT')),
    -- A document-backed basis names a retrieved document and when it was
    -- retrieved. Only the reviewer's own reasoning may omit both, and §6 of the
    -- contract forbids it standing alone.
    CONSTRAINT reliability_assessment_basis_document_check
        CHECK (
            basis_type = 'REVIEWER_DOCUMENTED_JUDGEMENT'
         OR (document_url IS NOT NULL AND retrieved_at IS NOT NULL)
        ),
    CONSTRAINT reliability_assessment_basis_url_check
        CHECK (document_url IS NULL OR document_url ~ '^https?://'),
    CONSTRAINT reliability_assessment_basis_finding_check
        CHECK (length(btrim(summarized_finding)) > 0
           AND length(btrim(document_title)) > 0),
    -- A long excerpt is a copy. The cap keeps this a reference, not a mirror --
    -- the same 1000 characters registry.source_policy_evidence allows.
    CONSTRAINT reliability_assessment_basis_excerpt_length_check
        CHECK (excerpt IS NULL OR length(excerpt) <= 1000)
);

CREATE INDEX idx_reliability_assessment_basis_assessment
    ON epistemic.reliability_assessment_basis (assessment_id);

COMMENT ON TABLE epistemic.reliability_assessment_basis IS
    'The retrieved documents a reliability value rests on. `The publisher is '
    'reputable` is not a basis type and cannot be recorded: reputation is not a '
    'property of a measurement. Every assessment needs at least one '
    'document-backed row, enforced by a deferred trigger.';

-- -----------------------------------------------------------------------------
-- 3. An assessment without a document-backed basis may not be stored
--
-- DEFERRABLE INITIALLY DEFERRED, so an assessment and its basis rows are
-- written in one transaction and neither has to exist first -- the same
-- mechanism migration 0016 uses for the evidence requirement, for the same
-- reason.
--
-- The rule is not "at least one basis row". It is "at least one basis row that
-- is not the reviewer's own reasoning": REVIEWER_DOCUMENTED_JUDGEMENT alone is
-- an opinion with a citation field, which is what §7 of the mission brief
-- refuses when it rejects "World Bank is trustworthy".
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION epistemic.require_documented_basis()
RETURNS TRIGGER AS $$
DECLARE
    documented INTEGER;
BEGIN
    SELECT count(*) INTO documented
      FROM epistemic.reliability_assessment_basis b
     WHERE b.assessment_id = NEW.id
       AND b.basis_type <> 'REVIEWER_DOCUMENTED_JUDGEMENT';

    IF documented = 0 THEN
        RAISE EXCEPTION
            'reliability assessment % (%, reliability %) has no document-backed basis. '
            'A reliability value must rest on retrieved first-party material about the '
            'measurement -- source documentation, dataset or measurement methodology, a '
            'stated limitation, a corpus construction method or an independent '
            'validation. Reviewer reasoning is permitted ALONGSIDE those and never '
            'instead of them: on its own it is an opinion with a citation field, which '
            'is what "the publisher is reputable" amounts to (Mission 1.14 §7, §24).',
            NEW.id, NEW.assessment_key, NEW.reliability
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER trg_reliability_assessments_require_basis
    AFTER INSERT OR UPDATE OF reliability, origin ON epistemic.reliability_assessments
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION epistemic.require_documented_basis();

-- -----------------------------------------------------------------------------
-- 4. Grants
--
-- The runtime role READS. Assessments are administered through a review path,
-- never over HTTP and never by a service -- the same posture the source
-- registry takes, for the same reason: a system that can write its own
-- reliability can approve itself.
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sros_app') THEN
        GRANT USAGE ON SCHEMA epistemic TO sros_app;
        GRANT SELECT ON epistemic.reliability_assessments TO sros_app;
        GRANT SELECT ON epistemic.reliability_assessment_basis TO sros_app;
    END IF;
END
$$;
