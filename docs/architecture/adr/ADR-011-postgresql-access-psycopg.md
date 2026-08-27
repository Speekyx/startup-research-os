# ADR-011 — PostgreSQL access with psycopg 3 and explicit repositories

- **Status:** Accepted
- **Date:** 2026-08-27
- **Deciders:** Implemented in Mission 0.3 under brief §29
- **Supersedes:** the *Database access strategy* section of
  [ADR-008](ADR-008-storage-architecture.md). Everything else in ADR-008 stands.
- **Related:** ADR-005, ADR-008, ADR-010

---

## Context

ADR-008 §Database access strategy chose **SQLAlchemy Core with a repository
layer**, for three stated reasons: migrations stay reviewable SQL, queries stay
explicit, and the repository is where the `workspace_id` filter is enforced once.

Mission 0.3 §29 asks for that choice to be made concretely and documented, and
authorizes justifying an ORM or query builder if one materially improves the
architecture. Implementing the layer made it clear that SQLAlchemy Core earns
none of the three reasons: **psycopg 3 delivers all of them directly, with one
fewer dependency and one fewer abstraction between a reviewer and the SQL.**

This ADR therefore supersedes that one section rather than editing ADR-008,
which is append-only.

## Decision

**psycopg 3** with `psycopg_pool.ConnectionPool`, wrapped by a thin `Database`
class, with explicit hand-written SQL inside per-resource repositories. **No
ORM, no query builder.**

### Connection pooling

`psycopg_pool.ConnectionPool`, opened at application startup and closed at
shutdown via the FastAPI lifespan. `min_size=1`, `max_size=10`, configurable.
A 5-second acquisition timeout so a request fails fast rather than queueing
behind a dead database.

### Transactions

`Database.transaction()` yields a connection inside an explicit transaction:
commit on clean exit, **rollback on any exception**. Nothing uses autocommit.

That is not a style preference. A record and its provenance must be written
together — a row observable without its provenance, even transiently, violates
`evidence-confidence-framework-v1.md` §10. The session-creation path also reads
the parent project and inserts the session in one transaction, so a project
deleted concurrently cannot leave an orphan.

### Rollback behavior

Any exception inside the `with` block rolls the whole transaction back. Repository
methods raise `ContractError`, `NotFoundError` or `InvalidTransitionError`, and
each aborts the transaction it is inside.

### Tenant propagation

**Every tenant-scoped repository method takes `workspace_id` as a required first
argument**, validates it through `_require_workspace()` (which fails closed on
`None` or `""`), and puts it in the `WHERE` clause. There is no ambient tenant,
no session-scoped variable, and no default.

`NotFoundError` is deliberately raised both when a row does not exist and when it
belongs to another workspace: telling a caller that an id exists elsewhere is
itself a cross-tenant disclosure.

### Migrations versus runtime access

Strictly separate. Migrations are forward-only SQL applied by
`infrastructure/scripts/migrate.py` (ADR-008), which is the only thing that
issues DDL. The runtime connects as an application role and issues DML only.
Nothing in the request path can alter the schema.

### Why no ORM

An accidental cross-tenant join is a security issue in this system, not a
performance one. Explicit SQL means a reviewer sees the `WHERE workspace_id = %s`
in the query. Lazy loading and identity maps hide query shape, which is exactly
what must stay visible here. The repositories are small and the queries are
simple; there is no mapping problem for an ORM to solve.

## Alternatives considered

### Alternative A — SQLAlchemy Core (the ADR-008 choice)

Its advantages are composable query building and dialect portability. Neither
applies: the queries are fixed and simple, and portability away from PostgreSQL
is not a goal (JSONB, GIN and array columns are used deliberately). It would add
a dependency and put a builder between the reviewer and the SQL, weakening the
one property that matters most — that the tenant filter is visible.

Rejected, and this ADR supersedes that section.

### Alternative B — SQLAlchemy ORM

Rejected for the reasons in §Why no ORM, plus it invites entity-level thinking
that conflicts with Ontology V2 §12: an `Opportunity` is not owned by a session,
and a naive relationship mapping would suggest it is.

### Alternative C — asyncpg

Faster, async-native, a good fit for FastAPI. Rejected for now: psycopg 3
supports both sync and async with the same API, so async can be adopted later
without changing the driver, and psycopg's `dict_row`/`COPY` support and error
taxonomy are better documented. Revisit if profiling shows the sync pool is a
bottleneck.

### Alternative D — Databases/encode or SQLModel

Extra layers over the same drivers. No benefit here.

## Pros

- The tenant filter is visible in the SQL, in the repository, in review.
- One fewer dependency and one fewer abstraction.
- Explicit transactions with predictable rollback.
- psycopg 3 supports async with the same API, so the async migration is open.
- Hand-written SQL matches hand-written migrations: one language for schema and
  queries.

## Cons

- **More verbose** than an ORM for simple CRUD. Every column is listed twice
  (INSERT and RETURNING).
- **No compile-time check that a query matches the schema.** A renamed column is
  a runtime error, caught by integration tests rather than by a type checker.
  This is the real cost, and it is why the integration suite runs against a real
  PostgreSQL.
- **Row-to-dataclass mapping is manual** and positional, so reordering a
  `SELECT` list silently misassigns fields unless tests catch it.
- **No dialect portability.** Deliberate, but it is a door closed.
- **An ADR section superseded within one mission**, which is churn. The
  justification is that implementing the layer produced information the original
  decision did not have.

## Future impact

**Becomes easy:** reviewing tenant safety; adopting async psycopg; using
PostgreSQL-specific features (JSONB operators, `FOR UPDATE SKIP LOCKED` for an
outbox).

**Becomes hard:** switching databases; generating queries dynamically; auto-
generating migrations from models (already ruled out by ADR-008).

**Revisit if:** the repository layer grows past roughly a thousand lines of SQL,
or dynamic query composition (faceted opportunity search) becomes a real
requirement — at which point SQLAlchemy Core for that subset, alongside plain
SQL elsewhere, is the likely answer.

**Cost of reversal:** low. The repositories are the only thing that touches the
driver, and their interfaces would not change.

## Compliance

- **ADR-005** — `workspace_id` required and explicit on every tenant-scoped
  method; verified by tenant-isolation integration tests using two workspaces.
- **ADR-008** — PostgreSQL remains the system of record; schema-per-context,
  migrations forward-only, registries as rows. Only the *access library* section
  is superseded.
- **ADR-010** — `psycopg[binary,pool]` is a `sros-gateway` dependency.
- **`evidence-confidence-framework-v1.md` §10** — provenance and record written
  in one transaction.
