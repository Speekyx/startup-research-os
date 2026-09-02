-- =============================================================================
-- 0028 — the two egress decisions, written into the seeded profile rows
--
-- Mission 1.23, ADR-033. Follows 0027, which added the column.
--
-- WHY A SECOND MIGRATION. 0027 added `registry.use_profiles.external_model_egress`
-- nullable with no default, because a column addition must not invent answers.
-- Mission 1.23 then MADE two decisions, and they have to land somewhere. They
-- cannot land in 0027: it is applied, and an applied migration is immutable
-- (core.schema_migrations checksums it). So the decision gets its own migration,
-- which is also the honest shape -- adding a slot and filling it are different
-- acts and are legible as two rows in the ledger.
--
-- WHY A MIGRATION AND NOT THE LOADER. `registry.use_profiles` is seeded by
-- migration 0021 and is written by nothing else: `load_catalog_into` loads
-- sources, reviews and conditions, and never touches this table. Its columns
-- -- `deployment`, `model_inference`, `raw_redistribution` -- all arrived the
-- same way. Adding a loader path for one column would make this table half
-- migration-seeded and half catalog-synced, which is worse than either.
--
-- WHAT MAKES THIS NOT AN INVENTION. Both values are decisions Mission 1.23
-- recorded in docs/data/source-catalog-v1.json with their reasoning, and this
-- migration mirrors them. The DB row saying NOT_ASSESSED while the catalog says
-- PERMITTED would be a drifted copy of a governance answer, and a drifted copy
-- of a governance answer is worse than none: it looks authoritative and is wrong.
--
-- FAIL-CLOSED EITHER WAY. Until this ran, both rows read NULL, which the model
-- reads as NOT_ASSESSED and which REFUSES. Nothing was authorised by the column
-- being empty and nothing is authorised by this migration either: egress still
-- requires a source review, an approved provider and a configured one.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- The LOCAL research deployment: permitted, and only to an approved provider.
--
-- `deployment = LOCAL` says where SROS runs and is NOT reinterpreted here as a
-- claim about where inference runs; that conflation is the defect ADR-033
-- exists to fix. This is a separate answer to a separate question.
-- -----------------------------------------------------------------------------

UPDATE registry.use_profiles
   SET external_model_egress = 'PERMITTED_TO_APPROVED_PROVIDERS'
 WHERE id = 'local-private-research-v1'
   AND external_model_egress IS DISTINCT FROM 'PERMITTED_TO_APPROVED_PROVIDERS';

-- -----------------------------------------------------------------------------
-- The COMMERCIAL multi-tenant profile: NOT_ASSESSED, stated rather than inherited.
--
-- Writing the value explicitly is the point. NULL and 'NOT_ASSESSED' both refuse,
-- but they say different things: NULL is a column nobody has reached, and
-- 'NOT_ASSESSED' is a reviewer who reached it and left the question open. Whether
-- a public multi-tenant service may send third-party licensed content to an
-- external processor is a materially harder question than the local one, and a
-- mission that answered it in passing would answer it for a product nobody built.
-- -----------------------------------------------------------------------------

UPDATE registry.use_profiles
   SET external_model_egress = 'NOT_ASSESSED'
 WHERE id = 'commercial-multi-tenant-research-v1'
   AND external_model_egress IS DISTINCT FROM 'NOT_ASSESSED';

-- -----------------------------------------------------------------------------
-- No row is created and no other row is touched. Both UPDATEs are guarded by
-- IS DISTINCT FROM, so re-running writes nothing, and neither statement can
-- reach a profile a later mission adds: an unlisted profile keeps NULL, reads
-- NOT_ASSESSED, and refuses -- which is the correct answer for a deployment
-- whose posture nobody has decided.
-- -----------------------------------------------------------------------------
