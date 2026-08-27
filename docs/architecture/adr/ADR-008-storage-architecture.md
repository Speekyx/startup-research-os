# ADR-008 — Storage architecture

- **Status:** Accepted
- **Date:** 2026-08-27
- **Deciders:** Implemented in Mission 0.2 under brief §9
- **Supersedes:** none
- **Related:** ADR-004, ADR-005, ADR-006, ADR-007, ADR-009, Ontology V2 §12 §14,
  `data-retention-policy-v1.md`, audit **A-09**, **A-10**

---

## Context

Mission 0.2 writes the first real schema. Schema decisions are the least
reversible decisions in the project: once rows exist, a wrong tenancy model, a
wrong taxonomy representation or a missing provenance column costs a migration
against production data.

Four invariants from earlier missions constrain the design, and each one has a
specific failure mode if ignored:

1. **Tenancy** (ADR-005) — a missing `workspace_id` filter is a cross-tenant data
   leak, not a rendering bug.
2. **Taxonomy governance** (Ontology V2 §14) — a taxonomy stored as a PostgreSQL
   `ENUM` needs a migration for every new product category, so the system stops
   describing new kinds of products.
3. **Opportunity rediscovery** (Ontology V2 §12) — an opportunity owned by the
   session that found it makes rediscovery a duplicate and makes cross-session
   evidence accumulation impossible, which defeats evidence levels 2 and 3.
4. **Blocked aggregation** (D-03) — a column named `aggregated_evidence_score`
   would bake in a formula nobody has defined.

## Decision

### PostgreSQL is the system of record

Everything canonical lives in PostgreSQL: raw and normalized records, signals,
evidence, scores, sessions, opportunities, registries, provenance. Single
instance, **schema-per-context** (`acquisition`, `nlp`, `scoring`,
`research`, `registry`, `core`), matching `service-boundaries.md` §5.

One database keeps operations simple; separate schemas keep ownership
enforceable and make a future service split mechanical rather than
archaeological.

### Redis is never canonical

Redis carries the Celery broker and result backend (ADR-004), caches,
rate-limit accounting and transient coordination. **Nothing in Redis is a source
of truth.** Losing Redis costs in-flight jobs and a cold cache, never data.

Broker durability still matters: AOF is enabled, `acks_late` is on, so a restart
does not silently drop work (ADR-004). Redis being non-canonical is not the same
as Redis being disposable mid-flight.

### Qdrant is a derived index

Qdrant holds embedding vectors and their payloads. **PostgreSQL holds the
embedding provenance** — model, model version, prompt version, source record,
timestamp — so the index is fully rebuildable.

Consequences, stated because they are the point:

- Qdrant needs **no backup strategy**. A total loss costs a re-index.
- Qdrant must **never** be the only place a business fact lives.
- **Every tenant-scoped vector search requires a `workspace_id` filter.** This is
  the least obvious leak path in the system because it never appears in a SQL
  audit, so the filter is enforced in the search wrapper, not at call sites.

### Tenant isolation

Every tenant-scoped table carries `workspace_id UUID NOT NULL` from its first
migration, with a foreign key to `core.workspaces`.

Composite indexes lead with `workspace_id` where the query pattern is
tenant-scoped — which is nearly all of them. Retrofitting index order on a large
table is expensive and easy to postpone indefinitely, so it is done now.

Reference data is deliberately **global**: registries, source registry, model
registry, scoring profiles. Those carry no `workspace_id`.

RLS is designed for but not enabled: the columns are `NOT NULL`, the application
connects as a non-owner role, and the tenant context is set per transaction. RLS
is the backstop for the query someone forgets, never the primary mechanism —
relying on it alone means every bug is a leak, relying on filtering alone means
one forgotten `WHERE` is a leak.

### Registries are rows, not enum types

**No PostgreSQL `ENUM` type is created for any evolving taxonomy.** Registries
live in `registry.registry_entries`, keyed by `(registry, id)`, carrying
canonical name, description, version, `ACTIVE`/`DEPRECATED` status and aliases
(Ontology V2 §14.4).

Closed semantic types (`ClaimType`, `MarketScopeType`, `ResearchSessionStatus`,
`DemandSignalFamily`) use `TEXT` with a `CHECK` constraint listing the values.
That is deliberate over a native `ENUM`: a `CHECK` is visible in the schema
dump, alterable in one statement, and diffable in review, whereas altering an
`ENUM` type is awkward and its ordering leaks into comparisons.

Registry references persist the **stable identifier**, never the display name.
Storing a display name means a rename silently rewrites history.

### Opportunity rediscovery

`research.opportunity_session_observations` associates an opportunity with a
session:

```text
opportunities            (workspace-scoped domain hypothesis)
        |
        |  1..n
opportunity_session_observations   (which session observed it, when, with what claim type)
        |  n..1
research_sessions
```

An `Opportunity` is **not** owned by the session that first found it. Sessions
produce observations. The same conceptual opportunity may be observed by many
sessions.

**Deliberately absent: any unique constraint that decides two opportunities are
the same.** Identity resolution is an analytical problem (Ontology V2 §12.3). The
only uniqueness is `(workspace_id, opportunity_id, research_session_id)` — one
observation per opportunity per session, which is a bookkeeping rule, not a
semantic judgment.

### ResearchContext persistence

Stored as **`JSONB` on `research_sessions`**, plus a `research_context_hash` and
a `research_context_schema_version` column. Trade-off analysis in §Alternatives.

### Transactional boundaries

- A record and its provenance are written in **one transaction**. A row without
  provenance must not be observable, even transiently.
- Job side effects use a deterministic idempotency key with a unique constraint,
  so at-least-once delivery (ADR-004) is absorbed by the database rather than by
  a read-then-write race.
- No transaction spans a queue publish and a business write without an outbox;
  where ordering matters, the outbox pattern is the intended answer (not
  implemented here).

### Database access strategy

**SQLAlchemy Core with a repository layer**, not a full ORM mapping.

Reasons: migrations stay reviewable SQL; queries stay explicit, which matters for
a workload where an accidental cross-tenant join is a security issue; and the
repository is where the `workspace_id` filter is enforced once rather than at
every call site. Lazy loading and identity maps buy little here and hide query
shape.

### Migrations

**Plain, numbered, forward-only SQL files** with a `core.schema_migrations`
ledger, applied by `infrastructure/scripts/migrate.py`.

Not Alembic, for now: no ORM models exist to autogenerate from, the schema is
small, and reviewable SQL is worth more at foundation than autogeneration. The
ledger table is Alembic-compatible in spirit, so adopting it later is additive.

Every migration is validated by `infrastructure/scripts/validate_schema.py`,
which mechanically enforces the invariants above.

### Indexes

- Every tenant-scoped table: composite index leading with `workspace_id`.
- Foreign keys are indexed.
- Retention-governed tables index `expires_at` for the lifecycle sweep.
- Registry entries: unique `(registry, id)`.

### Backup portability

PostgreSQL is the only thing that needs backing up. `pg_dump` of a single
database restores the whole system of record; Qdrant is re-indexed and Redis is
repopulated by re-running work. No cloud-provider-specific backup mechanism is
assumed (ADR-007 portability rules).

### Schema evolution

Forward-only migrations, additive by default. Nullable-then-backfill-then-
constrain for new required columns. A destructive migration requires an ADR.

## Alternatives considered

### ResearchContext storage: JSONB (chosen) vs normalized tables vs opaque blob

| Option | Why not / why |
|--------|---------------|
| **Normalized tables** | Fully queryable, but the context is a *value object* with an extensible `filters` map (Ontology V2 §11.3). Normalizing it creates the `ResearchContext` entity V2 explicitly forbids, and every new context field becomes a migration |
| **Opaque TEXT blob** | Immutable and simple, but not queryable at all: "which sessions targeted France?" becomes a full scan and a JSON parse in application code |
| **JSONB (chosen)** | Immutable in practice (written once at session creation, never updated), queryable via GIN for operational needs, no separate entity, no migration per field. Costs: no column-level constraints, so validation lives in the contracts package, and the schema version must be stored alongside to make old snapshots interpretable |

The deciding factor is that the snapshot's job is **reproducibility**, not
relational querying. Its canonical JSON is byte-stable across languages
(ADR-009), so `research_context_hash` gives cheap equality and tamper evidence,
and the operational queries that matter are satisfied by a GIN index.

### Tenancy: column (chosen) vs schema-per-tenant vs database-per-tenant

Settled in ADR-005 §Alternatives. Restated here only because the schema axis is
already used for *contexts*: tenancy is a column, contexts are schemas, and
conflating the two would collapse both.

### Migrations: plain SQL (chosen) vs Alembic

Alembic is the standard and is already available. Rejected for now because its
main advantage — autogeneration from ORM models — does not apply when there are
no ORM models, and its migration files are less readable than the SQL they wrap.
Revisit when the schema is large enough that hand-written SQL becomes the
bottleneck.

## Pros

- The expensive migrations (tenancy, taxonomy representation, opportunity
  ownership) are avoided permanently.
- Invariants are **mechanically enforced** by a schema validator, not by review.
- One thing to back up.
- Qdrant and Redis are disposable, which removes two operational burdens.
- Reviewable SQL keeps the schema legible to anyone.

## Cons

- **JSONB context is not column-constrained.** A malformed snapshot is prevented
  by the contracts package, not by the database. If a writer bypasses the
  contracts, the database will accept it.
- **Plain SQL migrations have no autogeneration and no downgrade path.**
  Forward-only is a deliberate simplification that will occasionally be
  inconvenient.
- **SQLAlchemy Core is more verbose** than an ORM for simple CRUD.
- **Schema-per-context adds ceremony** for a single-process deployment.
- **RLS is designed for but not enabled**, so today the only real defense is the
  repository layer plus the validator.
- **Single PostgreSQL instance** is a single point of failure. Acceptable at
  foundation (ADR-007), not in production.

## Future impact

**Becomes easy:** adding a registry entry (a row); adding a context field (no
migration); extracting a context to its own service; enabling RLS; rebuilding
Qdrant.

**Becomes hard:** querying deeply into context snapshots relationally; rolling a
migration back; sharding.

**Revisit if:** the schema outgrows hand-written SQL (adopt Alembic); an
enterprise requires physical isolation (per-tenant database as an addition);
or read load justifies a replica.

**Cost of reversal:** moderate and front-loaded. The choices that would be
expensive to reverse are exactly the ones fixed here on purpose.

## Compliance with authoritative specifications

- **ADR-005** — `workspace_id NOT NULL` everywhere tenant-scoped, indexes leading
  with it, RLS-ready, vector search filtered.
- **Ontology V2 §14.3** — no `ENUM` type for any evolving taxonomy; registries are
  rows. Enforced by the schema validator.
- **Ontology V2 §12** — observation model; no unique constraint deciding
  opportunity identity.
- **Ontology V2 §11.3** — context stored as an immutable versioned snapshot, no
  separate entity.
- **`data-retention-policy-v1.md`** — `collected_at` and `expires_at` explicit on
  retention-governed tables, `expires_at` computed at write time; per-source
  override (D-07) can be added without a schema change.
- **`evidence-confidence-framework-v1.md` §10 / audit A-10** — provenance columns
  are `NOT NULL` by default.
- **`scoring-framework-v1.1.md` §13 / D-03** — no aggregation column exists.
  Enforced by the schema validator, which fails on the forbidden names.
- **ADR-007** — no cloud-provider-specific storage feature is used.
