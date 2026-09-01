-- =============================================================================
-- 0022 — the procurement-notice record kind
--
-- Mission 1.15.8. ONE registry row and NO schema change, for the reason
-- migration 0011 records: `acquisition.normalized_records` already carries
-- `payload JSONB` and a `record_kind_id` with a foreign key to
-- `registry.registry_entries`, so the storage exists and what is missing is
-- permission to use it. Without this row every insert naming the kind is
-- refused, and `validate_normalization.py` asserts that the kinds declared in
-- `RECORD_KINDS` are exactly those a migration inserts, so the declaration and
-- the row cannot drift.
--
-- WHY A THIRD KIND rather than widening one that exists. A procurement notice
-- is neither a measured metric nor a counted term. It is a DOCUMENT a public
-- body published, whose content is a set of TYPED monetary facts, organisations
-- in roles, classification codes and several distinct dates. Widening
-- `numeric_observation` to hold it would give a World Bank population figure an
-- award status and a currency; widening `lexical_frequency_observation` would
-- give a GDELT term a buyer. The existing kinds getting worse for a new
-- source's sake is the failure the registry exists to prevent
-- (`normalized-record-v1.md` §5.1).
--
-- WHAT THIS ROW IS NOT. A vocabulary entry, not a claim that anything downstream
-- exists. No TED Signal, Claim or Evidence is created by Mission 1.15.8, and
-- `SIGNAL_EXTRACTORS` gains nothing.
--
-- Forward-only. Reversing it is deleting one row, safe for as long as no
-- normalized record references it.
-- =============================================================================

INSERT INTO registry.registry_entries (registry, id, name, description) VALUES
    ('normalization_record_kind', 'procurement_notice',
     'Procurement notice',
     'One procurement notice a contracting authority published, as the source '
     'published it. Source data: the monetary amounts are TYPED and '
     'unconverted -- a total value, a tender value, an estimated value and a '
     'framework maximum are four different things and are never flattened into '
     'one -- the organisations are multilingual and role-scoped, and nothing '
     'here is a transaction, a price or a market signal. A normalized notice '
     'supports the claim that the source REPORTED something, never that the '
     'procurement occurred as described (ted-eu-normalization-v1.md).')
ON CONFLICT (registry, id) DO NOTHING;
