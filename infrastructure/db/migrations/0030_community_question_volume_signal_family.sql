-- =============================================================================
-- 0030 — a fifth Signal quantity family, and the sixth signal type
--
-- Mission 1.30, ADR-034. `COMMUNITY_QUESTION_VOLUME` and
-- `community_question_volume`.
--
-- WHY A MIGRATION AT ALL. `nlp.signals.quantity_family` carries a CHECK
-- constraint listing the families, and `signal_type_id` is a foreign key into
-- `registry.registry_entries`. Neither will accept a value nobody declared, so
-- the model can name a fifth family and no row can hold one until this runs.
-- That is the schema doing its job, exactly as it did in Mission 1.19.
--
-- WHY A FIFTH FAMILY RATHER THAN WIDENING ONE THAT EXISTS. Two candidates were
-- available and both were rejected for the same shape of reason ADR-032 gives.
--
--   MEASURED_SERIES asks for a `metric` and a `geography`. A count of questions
--   filed under a tag is an instance of no series anybody publishes and belongs
--   to no place, so widening it would make `metric` optional for every World
--   Bank signal ever written.
--
--   CONTENT_REQUEST_VOLUME is the near miss, and rejecting it is the point of
--   this migration. Both are counts over a bounded period with no metric and no
--   geography, so the fields would have fitted. **A request is something a
--   READER makes of a server; a question is something a PERSON publishes about
--   being stuck.** Widening that family would not have cost a FIELD its meaning,
--   it would have cost the FAMILY its meaning -- a pageview and a request for
--   help would have become the same kind of quantity, and every consumer
--   branching on the family would silently have treated them alike.
--
-- WHAT THE NAME REFUSES. `PROBLEM_VOLUME`, `PROBLEM_FREQUENCY`,
-- `USER_PAIN_VOLUME`, `COMMUNITY_DEMAND` and `UNMET_NEED_VOLUME` were all
-- available and all are wrong. Whether two questions express the same problem
-- is the relation Mission 1.27 PARKED, so this family counts publications and
-- can never count problems. A field name survives every later caveat, which is
-- the same argument that produced `content_request_count` over
-- `wikimedia_pageview`.
--
-- Forward-only. The CHECK is widened, never narrowed, so no stored row can
-- become invalid; a re-run inserts nothing.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- The family.
--
-- PostgreSQL has no ALTER for a CHECK expression, so the constraint is dropped
-- and recreated. Both statements are one transaction, so there is no window in
-- which the column is unconstrained.
-- -----------------------------------------------------------------------------

ALTER TABLE nlp.signals
    DROP CONSTRAINT IF EXISTS signals_quantity_family_check;

ALTER TABLE nlp.signals
    ADD CONSTRAINT signals_quantity_family_check
        CHECK (quantity_family IN ('LEXICAL_FREQUENCY',
                                   'MEASURED_SERIES',
                                   'TRANSACTION_VALUE',
                                   'CONTENT_REQUEST_VOLUME',
                                   'COMMUNITY_QUESTION_VOLUME'));

COMMENT ON COLUMN nlp.signals.quantity_family IS
    'What kind of QUANTITY the signal is about. Five values since ADR-034. NOT the '
    'demand family: PAIN/DESIRE/BEHAVIORAL/MARKET classify demand, and neither a '
    'token count, a request count nor a question count is evidence of demand.';

-- -----------------------------------------------------------------------------
-- The signal type.
--
-- A registered type is VOCABULARY: the row lets a signal name the type and lets
-- the database refuse one nobody registered. The claim that an extractor EXISTS
-- is `SIGNAL_EXTRACTORS`, and it is separate on purpose.
-- -----------------------------------------------------------------------------

INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('signal_type', 'community_question_volume',
     'Community question volume',
     'How many public questions carrying one tag from a community site''s own '
     'vocabulary were created on that site inside one bounded window, counted over '
     'records this deployment holds. NON-TEMPORAL as a relation: one count over one '
     'window, never a change and never a trend. Complete only where the retrieval '
     'demonstrably did not truncate, which the derivation must establish and refuses '
     'without. Says people published that many questions filed under that tag; says '
     'nothing about how many PEOPLE (author identity is never acquired), nothing '
     'about whether the questions share a problem, and nothing about severity, '
     'recurrence, demand, adoption or willingness to pay.')
ON CONFLICT (registry, id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- What this migration does NOT do.
--
-- It creates no Signal, no Claim and no Evidence. It adds no record kind: the
-- `community_question` kind has existed since Mission 1.18 and nothing had
-- derived from it, which is the gap this family closes. And it does not touch
-- `scoring.evidence` or anything downstream -- whether a signal of this type
-- can be scored is a reliability question nobody has answered, and it stays
-- NON_SCORABLE.
-- -----------------------------------------------------------------------------
