-- =============================================================================
-- 0023 — the transaction-value signal family, and one signal type
--
-- Mission 1.15.9, ADR-029. TWO changes and no new table.
--
-- WHY A MIGRATION AT ALL. `nlp.signals.quantity_family` carries a CHECK
-- constraint listing the two families migration 0012 knew about, and
-- `signal_type_id` has a foreign key into `registry.registry_entries`. Without
-- both changes here, every insert naming the new family or the new type is
-- refused -- the same pairing migration 0011 and 0022 record for record kinds.
--
-- WHY A THIRD FAMILY. Mission 1.15.8 added the `procurement_notice` record kind,
-- and the Signal contract binds the family to the record kind of every
-- contributing input. Nothing mapped, so a derivation over TED notices was
-- refused with INCOMPATIBLE_INPUT_KINDS before it began: the Signal layer could
-- not express anything about procurement at all.
--
-- `MEASURED_SERIES` was the tempting reuse and is wrong. A measured series is a
-- quantity a source reports over a period, carrying a metric and a geography. A
-- procurement value is the amount ONE transaction settled at, with no metric it
-- is an instance of. Widening that family would have made `metric` optional for
-- every World Bank signal ever written, to accommodate a family that has none --
-- the existing model getting worse for a new source's sake.
--
-- WHAT THIS IS NOT. A vocabulary, not a claim that a signal exists. It is also
-- NOT willingness-to-pay: that a named buyer paid a named supplier a stated
-- amount is established; that a market exists, or that a comparable buyer would
-- pay a comparable amount for a different product, is not. A family named
-- WILLINGNESS_TO_PAY would put the second reading in the field a consumer
-- branches on (ADR-029 §Decision).
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
        CHECK (quantity_family IN ('LEXICAL_FREQUENCY', 'MEASURED_SERIES', 'TRANSACTION_VALUE'));

COMMENT ON COLUMN nlp.signals.quantity_family IS
    'What kind of QUANTITY the derivation is about. Not the demand family '
    '(PAIN/DESIRE/BEHAVIORAL/MARKET), which classifies an Opportunity, and not '
    'the signal_family registry, which says what a SOURCE could expose. Three '
    'relations, three subjects, three names (signal-taxonomy-v1.md §1). '
    'TRANSACTION_VALUE added in ADR-029: the value a transaction settled at, '
    'carrying an amount semantic and a currency and no metric.';

-- -----------------------------------------------------------------------------
-- 2. The signal type
--
-- A CONTRAST, not a change. The members are related by belonging to one
-- comparable cohort and by nothing temporal: H-37 leaves the meaning of a TED
-- publication date's offset unestablished, so no two notices can be ordered on
-- any timeline, and the derivation asks for no order at all. Its temporal basis
-- is NONE and its direction is NOT_APPLICABLE, which the existing constraints
-- already require of each other.
-- -----------------------------------------------------------------------------
INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('signal_type', 'procurement_value_contrast',
     'Procurement value contrast',
     'The spread of the values at which several comparable procurement '
     'transactions settled, within one source. Every member shares an amount '
     'semantic, a scope, a currency, a notice class and a procurement '
     'classification -- a total value and a framework maximum are different '
     'things, and two currencies are never one distribution. NON-TEMPORAL: the '
     'members are not ordered, compared across periods or read as a trend, '
     'because H-37 leaves TED publication-date semantics unestablished. Says '
     'what several buyers paid; says nothing about demand, about what a product '
     'could charge, or about willingness to pay.')
ON CONFLICT (registry, id) DO NOTHING;
