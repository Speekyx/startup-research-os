-- =============================================================================
-- 0026 — the content-request-volume signal family, and one signal type
--
-- Mission 1.19, ADR-032. TWO changes and no new table, the same pairing
-- migration 0023 records for `TRANSACTION_VALUE`.
--
-- WHY A MIGRATION AT ALL. `nlp.signals.quantity_family` carries a CHECK
-- constraint listing the families the earlier migrations knew about, and
-- `signal_type_id` has a foreign key into `registry.registry_entries`. Without
-- both changes here, every insert naming the new family or the new type is
-- refused.
--
-- WHY A FOURTH FAMILY. Migration 0025 added the `content_request_count` record
-- kind, and the Signal contract binds the family to the record kind of every
-- contributing input. Nothing mapped, so a derivation over Wikimedia pageview
-- records was refused with INCOMPATIBLE_INPUT_KINDS before it began.
--
-- `MEASURED_SERIES` was the tempting reuse and is wrong for a DIFFERENT reason
-- than a procurement value was. A request count really is a series, so widening
-- would not have cost `metric` its meaning. It would have cost the FAMILY its
-- meaning: a page-request change and a population change would carry the same
-- family, and no field would be left that says a count of HTTP requests and a
-- measured stock of people are not the same kind of quantity. The field would
-- still validate and would no longer discriminate, which is worse than a field
-- that breaks.
--
-- `LEXICAL_FREQUENCY` is structurally closer than it looks — both count
-- occurrences in a window — and still wrong. That family carries a TERM, a
-- language label and a mapping state. A request count has an ITEM and a
-- REQUESTER CLASS; reusing the lexical family would put an article title where a
-- consumer reads a term and leave the requester class with nowhere to live.
--
-- WHY THE NAME SAYS REQUEST AND VOLUME. The platform's own definition is "a
-- request for content of a page that receives a response of 200 OK or 304 Not
-- Modified". `CONTENT_VIEWS` would put "somebody looked" into the field a
-- consumer branches on; `CONTENT_ATTENTION` and `CONTENT_POPULARITY` would put
-- an interpretation there. The same argument ADR-029 made against a
-- WILLINGNESS_TO_PAY family: the reading somebody wants is exactly the one that
-- must not be written into the vocabulary.
--
-- WHAT THIS IS NOT. A vocabulary, not a claim that a signal exists. It does not
-- assert that a request is a reader, a reader a user, a user a customer, or any
-- number of them interest, demand, adoption, popularity or a market. And the
-- same ENTITY measured repeatedly is not the same USER PROBLEM recurring.
--
-- Forward-only. The CHECK is widened, never narrowed, so no stored row can
-- become invalid.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. The family
--
-- Dropped and re-added rather than altered: PostgreSQL has no ALTER CONSTRAINT
-- for a CHECK expression, and the two statements together are one transaction.
-- -----------------------------------------------------------------------------

ALTER TABLE nlp.signals
    DROP CONSTRAINT IF EXISTS signals_quantity_family_check;

ALTER TABLE nlp.signals
    ADD CONSTRAINT signals_quantity_family_check
        CHECK (quantity_family IN ('LEXICAL_FREQUENCY', 'MEASURED_SERIES', 'TRANSACTION_VALUE', 'CONTENT_REQUEST_VOLUME'));

COMMENT ON COLUMN nlp.signals.quantity_family IS
    'What kind of QUANTITY the derivation is about. Not the demand family '
    '(PAIN/DESIRE/BEHAVIORAL/MARKET), which classifies an Opportunity, and not '
    'the signal_family registry, which says what a SOURCE could expose. '
    'CONTENT_REQUEST_VOLUME added in ADR-032: how many times a named item was '
    'REQUESTED on a platform in a period, by one class of requester, carrying '
    'an item and a requester class and no metric and no geography. The name '
    'says REQUEST rather than VIEW because a field name survives every later '
    'caveat, and it is not attention, popularity, adoption or demand.';

-- -----------------------------------------------------------------------------
-- 2. The signal type
--
-- ONE type, because one derivation is implemented. A registered type with no
-- extractor behind it is a promise the code does not keep.
-- -----------------------------------------------------------------------------

INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('signal_type', 'content_request_change',
     'Content request change',
     'The change in one content item''s request count between two ADJACENT '
     'periods of one platform''s own publication, under one requester class and '
     'one access channel. Both members are the SAME item, so every item-level '
     'confounder cancels: article prominence, title, age and link structure are '
     'identical on both sides of the subtraction. The CALENDAR does not cancel, '
     'and neither do news events -- a weekday-to-weekend difference is a '
     'difference in the calendar, and that makes an inference from this signal '
     'unsound rather than the subtraction untrue. It says a platform counted a '
     'different number of requests on two adjacent days, and says nothing about '
     'readers, users, customers, interest, demand, adoption, popularity, a '
     'trend or a market.')
ON CONFLICT (registry, id) DO NOTHING;
