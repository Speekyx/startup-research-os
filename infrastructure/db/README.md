# `infrastructure/db` — Schema and migrations

**Governed by:** [ADR-008](../../docs/architecture/adr/ADR-008-storage-architecture.md)
and, for row-level security,
[ADR-012](../../docs/architecture/adr/ADR-012-row-level-security.md)

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

---

## Row-level security (migration 0003)

Full rationale in ADR-012. What an operator needs to know:

**Fifteen tenant-scoped tables carry `ENABLE` + `FORCE ROW LEVEL SECURITY`** and
one policy each, `tenant_isolation`, with the same predicate in `USING` and
`WITH CHECK`. Six tables in `core` and `registry` deliberately carry none: they
are global reference data, and `core.workspace_memberships` in particular is the
table that will *define* access once authentication exists.

**The tenant context is transaction-local:**

```sql
SET LOCAL ROLE sros_app;
SELECT set_config('app.workspace_id', '<uuid>', true);
```

Unset, empty and malformed all resolve to `NULL` through
`core.current_workspace_id()`, and `workspace_id = NULL` is not `TRUE`, so every
policy fails closed. There is no fallback workspace.

### Two things that will surprise you

**A superuser still sees everything.** `FORCE` binds the table owner, not a
superuser. `psql -U sros` shows all workspaces, and that is not a bug — it is why
the repository filter remains mandatory.

**"No rows" now has two causes.** Either there are none, or no tenant context was
set. Check with:

```sql
SELECT current_user, core.current_workspace_id();
```

### Applying migrations after 0003

Nothing changes: `migrate.py` connects as the owning role and issues DDL only. It
does not assume `sros_app`, which holds DML privileges exclusively — so a runtime
connection cannot alter the schema even by accident.

A future migration that must **modify tenant rows** needs a tenant context per
workspace, or must run before the policies apply to it. Forward-only DDL is
unaffected.

### Verifying

```bash
docker exec sros-dev-postgres-1 psql -U sros -d sros -c   "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class c
   JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname = 'research' AND c.relkind = 'r' ORDER BY 1;"
```

The authoritative check is the test suite:
`services/gateway/python/tests/test_rls.py`, 41 tests over two workspaces.
