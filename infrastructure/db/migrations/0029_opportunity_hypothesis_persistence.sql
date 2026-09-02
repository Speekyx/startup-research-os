-- =============================================================================
-- 0029 — the Opportunity as a versioned HYPOTHESIS, never a conclusion
--
-- Mission 1.28 §14 and §18. Forward-only, non-destructive: four nullable columns
-- on an EMPTY table, one new append-only revision table, one link table. No
-- column is dropped, no constraint is loosened, and no existing row is written
-- (there are none: `research.opportunities` holds 0 rows and this migration
-- creates none).
--
-- WHY THE EXISTING TABLE IS EXTENDED RATHER THAN REPLACED. `research.opportunities`
-- has existed since Mission 0.1 with identity, workspace, title, summary and a
-- canonical MarketScope, and `research.claims.opportunity_id` already points at
-- it. A second table would be a second place an opportunity can live, and one
-- that lives outside `research.opportunities` escapes the row-level-security
-- policy, the composite workspace foreign keys and every rule written about it.
-- That is the argument ADR-024 made when it refused a candidate-claim table, and
-- it holds unchanged one layer down.
--
-- WHY `status` IS THE POINT OF THIS MIGRATION. Mission 1.28 §18 requires that
-- OPPORTUNITY_HYPOTHESIS and VALIDATED_OPPORTUNITY be kept apart "in code/tests,
-- not merely prose". A CHECK constraint is the strongest available form of that:
-- three hypothesis-grade values, and `VALIDATED_OPPORTUNITY`, `PROVEN_MARKET`,
-- `WINNING_IDEA`, `PRODUCT_MARKET_FIT` and `HIGH_CONFIDENCE_BUSINESS` are not
-- members. A future mission that wants one has to write a migration adding it,
-- which is a visible, reviewable act rather than a string a caller passes.
--
-- WHY THE DEFAULT IS SAFE. `DEFAULT 'OPPORTUNITY_HYPOTHESIS'` on a NOT NULL
-- column would normally be the silent-migration hazard §8 of the source-registry
-- spec warns about -- a default that decides. It is safe here for a reason that
-- must be re-checked before it is ever relied on again: the table is empty, so
-- the default writes nothing, and every row it will ever apply to is a row this
-- engine creates, for which hypothesis IS the correct state.
--
-- WHY REVISIONS ARE A SEPARATE TABLE. §14 requires that a hypothesis not be
-- overwritten in place. `research.opportunity_hypothesis_revisions` is
-- append-only with `(opportunity_id, revision)` unique, mirroring
-- `research.claim_revisions` exactly -- an earlier revision stays readable, so a
-- report that quoted revision 1 can still be checked against it.
--
-- WHY THE EVIDENCE LINKS ARE EXPLICIT ROWS. A hypothesis cites Evidence, and
-- Evidence is claim-relative. Storing the ids as a jsonb array on the revision
-- would make "which hypotheses cite this Evidence row" unanswerable without a
-- scan, and would let an id survive the deletion of the row it names. A link
-- table with real foreign keys cannot.
--
-- WHAT THIS MIGRATION DOES NOT CREATE. No score, no rank, no weight, no priority
-- and no numeric aggregate of any kind (§15). `scoring.scores` is untouched and
-- still holds 0 rows. The dimensions and the sufficiency model come first;
-- ranking before them is what would make a ranking meaningless.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- research.opportunities — the hypothesis facts
-- -----------------------------------------------------------------------------

ALTER TABLE research.opportunities
    ADD COLUMN status TEXT NOT NULL DEFAULT 'OPPORTUNITY_HYPOTHESIS',
    -- Which procedure, at which version, produced this record. A hypothesis
    -- whose procedure is unrecorded cannot be re-derived or superseded on
    -- purpose, and this repository versions every procedure that decides
    -- anything.
    ADD COLUMN creation_procedure TEXT,
    -- The packet this hypothesis was formed over. Deterministic
    -- (`opportunity-evidence-packet@1.0.0` hashes its inputs), so the same
    -- packet id names the same evidence under the same procedures.
    ADD COLUMN packet_id TEXT,
    -- The use profile under which the evidence was gathered and the hypothesis
    -- formed. Never inferred: approval never transfers between profiles
    -- (ADR-027), and a hypothesis that could not say which profile it was
    -- formed under could not be re-checked against that profile's review.
    ADD COLUMN use_profile_id TEXT;

ALTER TABLE research.opportunities
    ADD CONSTRAINT opportunities_status_check
        CHECK (status IN ('OPPORTUNITY_HYPOTHESIS',
                          'HYPOTHESIS_WITHDRAWN',
                          'HYPOTHESIS_SUPERSEDED'));

COMMENT ON COLUMN research.opportunities.status IS
    'Hypothesis-grade states only. There is deliberately no VALIDATED_OPPORTUNITY, '
    'PROVEN_MARKET, WINNING_IDEA, PRODUCT_MARKET_FIT or HIGH_CONFIDENCE_BUSINESS: '
    'validation is a separate act nobody has performed, and a state that does not '
    'exist cannot be reached by a caller passing a string (Mission 1.28 §18).';

COMMENT ON COLUMN research.opportunities.packet_id IS
    'The OpportunityEvidencePacket this hypothesis was formed over. Derived by '
    'sha256 over the procedure versions and the ordered evidence ids, so it is '
    'stable across rebuilds and changes when the evidence or a procedure changes.';

-- -----------------------------------------------------------------------------
-- research.opportunity_hypothesis_revisions — append-only statements
-- -----------------------------------------------------------------------------

CREATE TABLE research.opportunity_hypothesis_revisions (
    id                      UUID        PRIMARY KEY,
    workspace_id            UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    opportunity_id          UUID        NOT NULL,
    revision                INTEGER     NOT NULL,

    -- The hypothesis in the shape Mission 1.28 §10 specifies. Kept as columns
    -- rather than one blob so a guard, a query and a reviewer can each reach the
    -- part they care about.
    target_actor            TEXT        NOT NULL,
    observed_need_or_change TEXT        NOT NULL,
    candidate_intervention  TEXT        NOT NULL,
    hypothesis_statement    TEXT        NOT NULL,
    reasoning_summary       TEXT        NOT NULL,

    -- Dimension sets, as sorted arrays of the taxonomy's own value strings.
    -- `unsupported_dimensions` is NOT NULL and constrained non-empty: a
    -- hypothesis supported on every dimension is not a hypothesis, and a record
    -- that listed only its support would be a sales document.
    supported_dimensions    TEXT[]      NOT NULL DEFAULT '{}',
    unsupported_dimensions  TEXT[]      NOT NULL,

    -- What bounds this hypothesis. Required for the same reason
    -- `epistemic.reliability_assessments.stated_limitation` is: a conclusion
    -- with no stated failure mode is one nobody can argue with.
    epistemic_limitations   TEXT[]      NOT NULL,
    uncertainties           TEXT[]      NOT NULL DEFAULT '{}',

    -- Provenance. Absent model_version means deterministic, and
    -- claim-model-v1.md's rule applies unchanged: DETERMINISTIC forbids a model
    -- version, because "deterministic" promises the record can be regenerated.
    procedure_version       TEXT        NOT NULL,
    model_version           TEXT,
    prompt_version          TEXT,
    research_session_id     UUID,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by              TEXT,

    CONSTRAINT opportunity_revisions_opportunity_same_workspace_fkey
        FOREIGN KEY (workspace_id, opportunity_id)
        REFERENCES research.opportunities (workspace_id, id) ON DELETE CASCADE,
    CONSTRAINT opportunity_revisions_session_same_workspace_fkey
        FOREIGN KEY (workspace_id, research_session_id)
        REFERENCES research.research_sessions (workspace_id, id)
        ON DELETE SET NULL (research_session_id),

    CONSTRAINT opportunity_revisions_unique
        UNIQUE (workspace_id, opportunity_id, revision),
    CONSTRAINT opportunity_revisions_positive_check
        CHECK (revision >= 1),
    CONSTRAINT opportunity_revisions_unsupported_not_empty_check
        CHECK (cardinality(unsupported_dimensions) > 0),
    CONSTRAINT opportunity_revisions_limitations_not_empty_check
        CHECK (cardinality(epistemic_limitations) > 0),
    -- A model version with no prompt version cannot be reproduced.
    CONSTRAINT opportunity_revisions_model_provenance_check
        CHECK (model_version IS NULL OR prompt_version IS NOT NULL),
    -- Referenced by the evidence link table, carrying workspace_id.
    CONSTRAINT opportunity_revisions_workspace_id_key
        UNIQUE (workspace_id, id)
);

CREATE INDEX idx_opportunity_revisions_opportunity
    ON research.opportunity_hypothesis_revisions
       (workspace_id, opportunity_id, revision DESC);

-- -----------------------------------------------------------------------------
-- research.opportunity_hypothesis_evidence — what each revision actually cites
--
-- `scoring.evidence` carries no UNIQUE (workspace_id, id) yet, so the composite
-- foreign key below could not be declared against it. Adding one is the same
-- additive step migrations 0009 and 0012 took for raw_records, normalized_records
-- and signals, and for the same reason: a tenant-scoped reference must be
-- provably tenant-scoped at the schema level, not by convention at the caller.
-- -----------------------------------------------------------------------------

ALTER TABLE scoring.evidence
    ADD CONSTRAINT evidence_workspace_id_key UNIQUE (workspace_id, id);

CREATE TABLE research.opportunity_hypothesis_evidence (
    id                  UUID        PRIMARY KEY,
    workspace_id        UUID        NOT NULL REFERENCES core.workspaces (id) ON DELETE CASCADE,
    revision_id         UUID        NOT NULL,
    evidence_id         UUID        NOT NULL,
    claim_id            UUID        NOT NULL,

    -- The eligibility this row held AT CITATION TIME. Stored rather than
    -- resolved later, because eligibility depends on a reliability that may be
    -- assessed after the fact -- and a hypothesis formed over context-only
    -- evidence must keep saying so even once that evidence becomes scorable.
    eligibility_at_citation TEXT     NOT NULL,
    dimensions          TEXT[]      NOT NULL DEFAULT '{}',

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT opportunity_evidence_revision_same_workspace_fkey
        FOREIGN KEY (workspace_id, revision_id)
        REFERENCES research.opportunity_hypothesis_revisions (workspace_id, id)
        ON DELETE CASCADE,
    CONSTRAINT opportunity_evidence_evidence_same_workspace_fkey
        FOREIGN KEY (workspace_id, evidence_id)
        REFERENCES scoring.evidence (workspace_id, id) ON DELETE CASCADE,
    CONSTRAINT opportunity_evidence_claim_same_workspace_fkey
        FOREIGN KEY (workspace_id, claim_id)
        REFERENCES research.claims (workspace_id, id) ON DELETE CASCADE,
    CONSTRAINT opportunity_evidence_unique
        UNIQUE (workspace_id, revision_id, evidence_id),
    CONSTRAINT opportunity_evidence_eligibility_check
        CHECK (eligibility_at_citation IN ('ELIGIBLE_CONTEXT', 'ELIGIBLE_SCORING'))
);

CREATE INDEX idx_opportunity_evidence_revision
    ON research.opportunity_hypothesis_evidence (workspace_id, revision_id);
CREATE INDEX idx_opportunity_evidence_evidence
    ON research.opportunity_hypothesis_evidence (workspace_id, evidence_id);

-- -----------------------------------------------------------------------------
-- Tenancy. Both new tables carry workspace_id and both get the policy: layer 1
-- is the repository filter, layer 2 is RLS, and neither replaces the other.
-- -----------------------------------------------------------------------------

ALTER TABLE research.opportunity_hypothesis_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.opportunity_hypothesis_revisions FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.opportunity_hypothesis_revisions
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

ALTER TABLE research.opportunity_hypothesis_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE research.opportunity_hypothesis_evidence FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON research.opportunity_hypothesis_evidence
    FOR ALL
    USING (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());

COMMENT ON TABLE research.opportunity_hypothesis_revisions IS
    'Append-only hypothesis statements. A revision is never modified: a report '
    'that quoted revision 1 must still be checkable against revision 1 '
    '(Mission 1.28 §14).';

COMMENT ON TABLE research.opportunity_hypothesis_evidence IS
    'Which Evidence and Claim rows one hypothesis revision cites, with the '
    'eligibility each held at citation time. Real foreign keys rather than a '
    'jsonb array, so a cited id cannot outlive the row it names.';
