# `infrastructure/db` — Schema and migrations

**Governed by:** [ADR-008](../../docs/architecture/adr/ADR-008-storage-architecture.md)

```
db/
├── migrations/   forward-only numbered SQL, immutable once applied
└── seed/         idempotent development seed, NEVER for production
```

## Applying migrations

```bash
python infrastructure/scripts/migrate.py --plan
```

```bash
uv run python infrastructure/scripts/migrate.py --apply --seed
```

`--plan` needs no database and no driver. `--apply` needs `DATABASE_URL` and
`psycopg` (provided by the uv workspace, ADR-010).

## Verified against a real database (Mission 0.3)

Mission 0.2 could not run these; Mission 0.3 did:

| Check | Result |
|-------|--------|
| Migration applies to an EMPTY PostgreSQL 16.4 | Applied |
| 6 schemas, 16 tables, 31 foreign keys, 128 CHECK constraints, 42 indexes | Present |
| Ledger records version + sha256 checksum | Present |
| Schema survives a full container restart | Survived |
| Re-running `--apply` is a no-op | `skip … (already applied)` |
| A modified applied migration is REJECTED | Rejected, then the file was restored |
| Every tenant table has a `workspace_id`-leading index | Confirmed in `pg_indexes` |

The checksum test appended a comment to the applied migration, observed the
refusal, and restored the file. The migration is byte-identical to what the
ledger recorded.

Each migration commits **together with its ledger row**, so a half-applied
migration is not a reachable state. A migration whose checksum changed after it
was applied is refused: they are forward-only and immutable, so the fix is a new
migration.

## Validation

```bash
python infrastructure/scripts/validate_schema.py
```

Enforces the ADR-008 invariants mechanically, without a database:

| Invariant | Why it is checked rather than reviewed |
|-----------|----------------------------------------|
| `workspace_id UUID NOT NULL` on every tenant-scoped table | A missing filter is a cross-tenant leak, not a rendering bug |
| Composite indexes lead with `workspace_id` | Retrofitting index order on a large table is expensive and gets postponed |
| No PostgreSQL `ENUM` type | An enum'd taxonomy needs a migration per new product category (Ontology V2 §14.3) |
| No evidence-aggregation column | D-03 is unresolved; a column name would bake in an undefined formula |
| `collected_at` + `expires_at` on retention-governed tables | Retention decided at write time stays auditable |
| Closed-enum `CHECK` values match `packages/contracts` | The database and the contracts cannot drift |
| `confidence` is `[0,1]`, `*_score` is `0–100` | The most likely silent numeric bug in the system |

## Schema v1 at a glance

| Schema | Tables |
|--------|--------|
| `core` | `users`, `workspaces`, `workspace_memberships`, `schema_migrations` |
| `registry` | `registry_entries`, `sources` |
| `research` | `research_projects`, `research_sessions`, `research_gaps`, `opportunities`, `opportunity_session_observations` |
| `acquisition` | `raw_records`, `normalized_records` |
| `nlp` | `signals`, `embedding_provenance` |
| `scoring` | `evidence` |

## Two things deliberately absent

**No unique constraint decides opportunity identity.** Whether two discoveries
are the same opportunity is an analytical problem (Ontology V2 §12.3), not
something a convenient index should settle.

**No aggregation column.** D-03 is blocked; `scoring.evidence` stores raw
metadata only, and how it combines is a future specification.
