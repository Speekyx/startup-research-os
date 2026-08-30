-- =============================================================================
-- 0016_claim_interpretation_alignment.sql -- a Claim precedes its Opportunity
--
-- Mission 1.13. Governed by docs/data/claim-evidence-interpretation-gap-analysis-v1.md
-- (written BEFORE this file, per §41), the interpretation contract, Ontology
-- V2.2 and ADR-024.
--
-- WHY THE EXISTING SHAPE COULD NOT BE KEPT
--
-- `research.claims`, `research.claim_revisions` and `scoring.evidence` were
-- designed in Mission 0.1 and realigned in Mission 1.2 -- both BEFORE any Signal
-- existed. They encode an ordering the pipeline now contradicts:
--
--     the schema says      Opportunity first, Claims are assertions about it
--     the pipeline runs    Signal -> Evidence -> Claim -> ... -> Opportunity
--
-- The contradiction is mechanical rather than aesthetic. A deterministic
-- OBSERVED claim -- "World Bank reported Germany's population rose by 187,180
-- between 2018 and 2019" -- is a fact a future opportunity may CITE. Requiring
-- an opportunity first would mean inventing a product idea in order to record an
-- observation, which is the inversion of `evidence before conclusions`.
--
-- All three tables are EMPTY and nothing writes to them. Migration 0005 said the
-- thing worth repeating: this is the cheapest it will ever be.
--
-- WHAT THIS FILE DOES NOT DO
--
-- No Claim, no ClaimRevision and no Evidence row is created. This makes an
-- interpretation REPRESENTABLE; all three tables still hold 0 rows afterwards,
-- and they must.
--
-- Forward-only. Never edited after it has been applied anywhere.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. A Claim may exist before, and without, an Opportunity (GAP-1)
--
-- Ontology V2.2 §17.3, ADR-024 Decision 1. NULL means "not yet part of any
-- opportunity's evaluation", which is the ordinary condition of a claim the
-- moment it is derived.
--
-- Everything V2.1 §17.3 argued for survives: aggregation stays per claim, an
-- opportunity still carries many claims, a claim still participates in at most
-- one, and cross-opportunity sharing is still not modelled. Only the EXISTENCE
-- requirement moves, from "exactly one" to "at most one".
--
-- The composite foreign key is unchanged and still refuses a claim naming an
-- opportunity in another workspace.
-- -----------------------------------------------------------------------------
ALTER TABLE research.claims
    ALTER COLUMN opportunity_id DROP NOT NULL;

COMMENT ON COLUMN research.claims.opportunity_id IS
    'The opportunity whose evaluation this claim participates in, or NULL for '
    'one that participates in none yet. NULL is a STATE and not a gap: the '
    'pipeline runs Signal -> Evidence -> Claim -> Opportunity, so a claim about '
    'a source fact exists before anybody has thought of the product that cites '
    'it (Ontology V2.2 §17.3, ADR-024).';

-- -----------------------------------------------------------------------------
-- 2. The interpreter is identified, and determinism is enforced (GAP-4)
--
-- The defect nlp.signals carried before Mission 1.11, in the same shape:
-- `model_version` and `prompt_version` were the only producer identity, so a
-- DETERMINISTIC interpreter would have named itself by writing free text into
-- `origin_detail` -- the field that decides whether a result is reproducible.
--
-- `origin` is KEPT. It answers WHO asserted this (MANUAL, IMPORTED,
-- SYSTEM_GENERATED); the columns below answer HOW, and they were different
-- questions all along.
-- -----------------------------------------------------------------------------
ALTER TABLE research.claims
    ADD COLUMN interpreter_id TEXT,
    ADD COLUMN interpreter_version TEXT,
    ADD COLUMN interpretation_kind TEXT,

    ADD CONSTRAINT claims_interpretation_kind_check
        CHECK (interpretation_kind IN ('DETERMINISTIC', 'MODEL_DERIVED')
               OR interpretation_kind IS NULL),

    -- An interpreter is named in full or not at all. Half an identity is a
    -- version nobody can resolve.
    ADD CONSTRAINT claims_interpreter_complete_check
        CHECK (
            (interpreter_id IS NULL AND interpreter_version IS NULL
                                    AND interpretation_kind IS NULL)
         OR (length(btrim(interpreter_id)) > 0
             AND length(btrim(interpreter_version)) > 0
             AND interpretation_kind IS NOT NULL)
        ),

    -- Mission 1.13 §20, as a constraint rather than a sentence. A DETERMINISTIC
    -- interpretation did not consult a model, and a provenance field saying
    -- otherwise would be false; a MODEL_DERIVED one may not omit what produced
    -- it (llm-reasoning-rules.md §9).
    ADD CONSTRAINT claims_interpretation_provenance_check
        CHECK (
            interpretation_kind IS NULL
         OR (interpretation_kind = 'DETERMINISTIC'
             AND model_version IS NULL AND prompt_version IS NULL)
         OR (interpretation_kind = 'MODEL_DERIVED' AND model_version IS NOT NULL)
        ),

    -- WHICH observation this claim is about, canonically and WITHOUT PROSE.
    -- Two sessions that both derive "World Bank reported Germany's population
    -- rose in 2019" have produced the same claim and must not produce two.
    --
    -- Built from the structured facts the proposition asserts -- source, metric,
    -- geography, period labels, direction -- so the sentence may be rewritten
    -- without the key moving. NEVER from an embedding: D-12 is open, and an
    -- identity that depended on a vector would change when the model did.
    ADD COLUMN proposition_key TEXT,
    ADD CONSTRAINT claims_proposition_key_not_blank_check
        CHECK (proposition_key IS NULL OR length(btrim(proposition_key)) > 0),
    -- One claim per proposition per workspace. Deliberately NOT unique across
    -- workspaces: two tenants deriving the same fact hold two claims, because a
    -- shared one would leak what the other is researching.
    ADD CONSTRAINT claims_proposition_unique
        UNIQUE (workspace_id, proposition_key);

COMMENT ON COLUMN research.claims.proposition_key IS
    'Canonical identity of the PROPOSITION, from the structured facts it '
    'asserts and never from its prose or an embedding. Two revisions may reword '
    'a claim without moving it; two claims whose facts differ are different '
    'claims however similar they read.';

COMMENT ON COLUMN research.claims.interpretation_kind IS
    'How the claim was produced. DETERMINISTIC may carry no model or prompt '
    'version; MODEL_DERIVED may not omit the model version. NULL where no '
    'interpreter was involved -- a manually authored claim.';

-- -----------------------------------------------------------------------------
-- 3. How sure the interpreter was that the sentence says what the Signals showed
--    (GAP-2)
--
-- On the REVISION, not the claim: a rewording can change how confident a reader
-- should be that this sentence is a faithful reading, and the claim's identity
-- does not move when it does.
--
-- It is NOT an EvidenceScore, NOT an evidence strength and NOT a signal's
-- derivation confidence. An interpreter can be certain it read a Signal
-- correctly while the Signal is weak evidence for anything, and Mission 1.13
-- §16 and §38 exist to keep those apart.
-- -----------------------------------------------------------------------------
ALTER TABLE research.claim_revisions
    ADD COLUMN interpretation_confidence DOUBLE PRECISION,
    ADD CONSTRAINT claim_revisions_interpretation_confidence_unit_interval_check
        CHECK (interpretation_confidence IS NULL
               OR (interpretation_confidence BETWEEN 0 AND 1));

COMMENT ON COLUMN research.claim_revisions.interpretation_confidence IS
    'Confidence that THIS WORDING faithfully states what the cited Signals '
    'showed. Never a market confidence and never an EvidenceScore: an '
    'interpretation may be certainly correct about weak evidence.';

-- -----------------------------------------------------------------------------
-- 4. Evidence is claim-relative by definition (GAP-6, GAP-7)
--
-- `claim_id` was nullable "ONLY so this migration can apply to a table that
-- already has rows in some future environment" (migration 0005). There are still
-- none, and the condition never arose. Direction, relevance and directness are
-- all RELATIVE TO A PROPOSITION, so a row without one is not evidence.
--
-- `claim_type` predates `claim_id`: in migration 0001 evidence pointed at an
-- OPPORTUNITY and this column carried the epistemic weight. A-13 gave evidence a
-- claim and the claim carries the type, so two columns now answer one question
-- and can disagree. The aggregation framework reads NEITHER -- its item inputs
-- are relevance, directness, reliability, extraction confidence, freshness,
-- direction, observation category and independence.
-- -----------------------------------------------------------------------------
ALTER TABLE scoring.evidence
    ALTER COLUMN claim_id SET NOT NULL;

ALTER TABLE scoring.evidence
    DROP CONSTRAINT evidence_claim_type_check,
    DROP COLUMN claim_type;

COMMENT ON COLUMN scoring.evidence.claim_id IS
    'The proposition this record bears on. NOT NULL since Mission 1.13: '
    'direction, relevance and directness are relative to a claim, so a row '
    'without one is a dangling measurement rather than evidence.';

-- -----------------------------------------------------------------------------
-- 5. An automatically generated Claim cannot be stored unsupported (GAP-3)
--
-- Mission 1.13 §22, ADR-024 Decision 2. The single rule this layer's
-- trustworthiness rests on: a machine may not store a market assertion with
-- nothing behind it.
--
-- DEFERRABLE INITIALLY DEFERRED, because a claim, its first revision and its
-- evidence are written in ONE transaction and each references the others -- the
-- same reason `claims_current_revision_fkey` is deferred, and the same mechanism
-- migration 0007 used to refuse a satisfied condition with no verification.
--
-- TWO EXEMPTIONS, both deliberate:
--
--   HYPOTHESIS  is BY DEFINITION a proposition worth testing and not yet
--               supported. Requiring evidence would make the type unusable and
--               would push unsupported ideas into INFERRED, which is exactly the
--               failure this rule exists to prevent. It stays visibly and
--               machine-readably HYPOTHESIS.
--
--   MANUAL      a person asserting something and then looking for evidence is
--               the ordinary research motion. The rule is about what a MACHINE
--               may store unsupported.
--
-- KNOWN LIMIT, recorded rather than papered over: the trigger fires on writes to
-- research.claims, so it cannot catch evidence being deleted afterwards. The
-- invariant is enforced where an unsupported assertion would be INTRODUCED.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION research.require_evidence_for_generated_claim()
    RETURNS trigger
    LANGUAGE plpgsql
    SET search_path = pg_catalog, research
AS $$
BEGIN
    IF NEW.lifecycle = 'WITHDRAWN' THEN
        RETURN NEW;
    END IF;
    IF NEW.claim_type = 'HYPOTHESIS' OR NEW.origin = 'MANUAL' THEN
        RETURN NEW;
    END IF;

    IF NOT EXISTS (
        SELECT 1
          FROM scoring.evidence e
         WHERE e.workspace_id = NEW.workspace_id
           AND e.claim_id = NEW.id
    ) THEN
        RAISE EXCEPTION
            'claim % (% / %) has no evidence. An automatically generated claim '
            'must cite at least one evidence record; a proposition a machine '
            'asserts with nothing behind it is the unsupported market claim this '
            'system exists to prevent. HYPOTHESIS is exempt BY DEFINITION and is '
            'where an unsupported proposition belongs (Mission 1.13 §22, ADR-024).',
            NEW.id, NEW.claim_type, NEW.origin
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_claims_require_evidence
    AFTER INSERT OR UPDATE OF claim_type, origin, lifecycle ON research.claims
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION research.require_evidence_for_generated_claim();

COMMENT ON FUNCTION research.require_evidence_for_generated_claim() IS
    'Refuses an automatically generated claim with no evidence, at COMMIT. '
    'HYPOTHESIS and MANUAL origin are exempt: the first because an unsupported '
    'proposition is what that type IS, the second because a person may assert '
    'first and look for evidence after.';

-- -----------------------------------------------------------------------------
-- 6. Access paths the interpretation layer needs
-- -----------------------------------------------------------------------------

-- "Which claims has nobody attached to an opportunity yet", which is the queue
-- a future opportunity engine reads.
CREATE INDEX idx_claims_unattached
    ON research.claims (workspace_id, created_at DESC)
    WHERE opportunity_id IS NULL;

-- "Which claims did this interpreter version write", which is the audit a
-- version bump raises.
CREATE INDEX idx_claims_interpreter
    ON research.claims (interpreter_id, interpreter_version);

-- "Which claims cite this signal", the reverse of the evidence link and the
-- question an operator asks when a signal turns out to be wrong.
CREATE INDEX idx_evidence_signal_claim
    ON scoring.evidence (workspace_id, signal_id, claim_id);
