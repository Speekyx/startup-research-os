# ADR-012 — Row-level security with transaction-local tenant context

- **Status:** Accepted
- **Date:** 2026-08-29
- **Deciders:** Implemented in Mission 0.4 under brief §3–§7
- **Supersedes:** none. Completes the *Future row-level security* section of
  [ADR-005](ADR-005-workspace-multi-tenancy.md), which designed for RLS without
  enabling it.
- **Related:** ADR-005, ADR-008, ADR-011

---

## Context

ADR-005 §Future row-level security called RLS "the intended defense-in-depth
layer" and listed four preconditions: `workspace_id NOT NULL` everywhere,
composite indexes leading with it, an application role RLS can constrain, and a
session-level tenant context set by the connection layer. Missions 0.2 and 0.3
satisfied the first two and left the last two, so isolation has rested on one
layer:

```text
Layer 1   the explicit WHERE workspace_id = %s in every repository query
```

That layer is good. It is also one forgotten clause away from a cross-tenant
read, and a forgotten clause is invisible in review precisely because the query
still looks correct. ADR-005 said it plainly: *"relying on filtering alone means
one forgotten `WHERE` is a production data leak."*

Mission 0.3 closed the two non-SQL leak paths — cache keys and vector filters —
by putting the tenant scope inside a wrapper no caller can bypass. The SQL path
had no equivalent, because SQL is written per query.

### The two obstacles that had to be resolved first

Neither is obvious, and either one silently produces a system that looks
protected and is not.

**A superuser and a table owner bypass RLS.** The local stack connects as the
database superuser created by the `postgres` image. Enabling policies without
addressing that produces isolation tests that pass while proving nothing, which
is worse than no tests: it converts an open question into a false answer.

**A session-level tenant context leaks through a connection pool.** ADR-005
suggested `SET LOCAL app.workspace_id`, and ADR-011 pools connections. A plain
`SET` survives the connection's return to the pool, so the next borrower
inherits the previous tenant's context — a cross-tenant read with no bug in any
query, reachable only under concurrency, and effectively undetectable in review.

## Decision

**Enable and FORCE row-level security on every tenant-scoped table, with a
transaction-local tenant context and a non-bypassing application role.**

```text
Layer 1   explicit repository tenant filtering        (unchanged, still required)
Layer 2   PostgreSQL row-level security               (this ADR)
```

A leak now requires defeating both.

### The tenant context

A custom GUC, `app.workspace_id`, set **per transaction**:

```sql
SELECT set_config('app.workspace_id', $1, true);   -- is_local => true
```

`set_config` with a bound parameter rather than `SET LOCAL app.workspace_id =
'…'`, because a tenant id interpolated into a statement is the one place this
system must not take a shortcut.

Policies read it through a helper that **fails closed three ways**:

```sql
CREATE FUNCTION core.current_workspace_id() RETURNS uuid
    LANGUAGE sql STABLE SET search_path = pg_catalog
AS $$
    SELECT CASE
        WHEN current_setting('app.workspace_id', true) ~ '^[0-9a-fA-F]{8}-…$'
        THEN current_setting('app.workspace_id', true)::uuid
        ELSE NULL
    END
$$;
```

Unset, empty and malformed all resolve to `NULL`; `workspace_id = NULL` is
`NULL`, which is not `TRUE`, so no row passes. The regex guard rather than a
bare `::uuid` is deliberate: a bare cast raises inside the query plan, and an
error there is a worse failure mode than an empty result when the alternative is
a policy that cannot be evaluated at all.

**There is no fallback workspace, and no `COALESCE` to a default.** A policy
written that way would satisfy every isolation test while making one workspace
universally visible. A test asserts the policy expression contains no
`COALESCE`.

### The application role

```sql
CREATE ROLE sros_app NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
```

Assumed per transaction with `SET LOCAL ROLE sros_app`, so policies apply even
when the underlying connection belongs to a privileged role. `NOBYPASSRLS` and
`NOSUPERUSER` are the two attributes that make the policies mean anything, and a
test asserts both.

`NOLOGIN` is the part worth explaining: **no password exists, therefore no
password can be committed in a migration.** A dedicated LOGIN role with its own
credential is the production path, and it is deployment configuration rather
than schema (§Deployment below).

A side effect worth having: `sros_app` holds DML privileges only, so a runtime
connection cannot issue DDL. ADR-011 said migrations and runtime access are
strictly separate; the database now enforces it rather than the code intending
it.

### FORCE, not merely ENABLE

`ENABLE ROW LEVEL SECURITY` exempts the table owner. In a deployment where the
application connects as the owner — the obvious way to deploy this today — that
exemption *is* the entire protection, silently absent. `FORCE` closes it, and
costs nothing.

### Policies

One policy per tenant-scoped table, `FOR ALL`, with the same predicate in both
clauses:

```sql
CREATE POLICY tenant_isolation ON research.research_sessions
    FOR ALL
    USING      (workspace_id = core.current_workspace_id())
    WITH CHECK (workspace_id = core.current_workspace_id());
```

`WITH CHECK` is not optional. `USING` alone would let a workspace INSERT a row
tagged with another workspace's id: invisible to whoever wrote it, and visible
to exactly the wrong tenant.

**Fifteen tenant-scoped tables** receive it: the ten in `research`, two in
`acquisition`, two in `nlp`, and `scoring.evidence`.

### Tables that deliberately receive no policy

| Table | Why not |
|-------|---------|
| `core.schema_migrations` | Operational ledger, no tenant dimension |
| `core.users` | A principal is not a tenant (ADR-005). One user, many workspaces |
| `core.workspaces` | The tenant list itself. A policy would have to be evaluated before a tenant context exists |
| `core.workspace_memberships` | **Carries `workspace_id` and still gets none.** This is the table that will *define* access once authentication exists, and "which workspaces may this user enter?" is asked before any workspace is chosen. Gating it on the answer makes the question unanswerable. It is protected by being read-only to `sros_app` |
| `registry.registry_entries`, `registry.sources` | Global taxonomies (Ontology V2 §14.3). A taxonomy that differed per tenant would make classifications incomparable across workspaces |

Applying a tenant policy to a table that is not tenant-scoped is worse than
leaving it alone: it makes the schema look uniformly protected while the rows
that matter are unreachable, or the policy is a no-op nobody re-reads.

## Alternatives considered

### Alternative A — Repository filtering only (the Mission 0.3 state)

Simplest, already working, zero migration. Rejected: it makes every application
bug a production data leak, which ADR-005 identified as the reason to add RLS in
the first place. The cost of adding it later grows with the number of tables and
the amount of data.

### Alternative B — RLS instead of repository filtering

Tempting: delete the `WHERE` clauses and let the database do it. Rejected, and
the reason is specific. Layer 1 and layer 2 fail differently, and that is the
point of having both:

- A forgotten `WHERE` is caught by the policy.
- A connection that never established a tenant context returns **no** rows
  rather than **wrong** rows, which is a visible failure instead of a silent one.
- Any path that legitimately runs without the application role — a migration, an
  administrative export, a future reporting job — has no policy protecting it,
  and the repository filter still does.

Removing layer 1 later would be a regression rather than a cleanup, and a
reviewer looking at a query with no tenant predicate cannot tell "deliberate"
from "forgotten".

### Alternative C — A separate login role with its own password, created outside migrations

The textbook answer, and the right one for production. Rejected as the *default*
for the foundation phase: it adds a credential to provision, a variable to every
environment, and a failure mode where the local stack does not start because a
role was not created. `SET LOCAL ROLE` from a role that already has membership
achieves the same enforcement with no new secret.

Retained as the production path, not discarded.

### Alternative D — Schema-per-tenant or database-per-tenant

Settled in ADR-005 §Alternatives, for reasons unchanged: operationally heavy,
and the schema axis is already used for contexts.

### Alternative E — Session-level `SET` instead of `SET LOCAL`

Marginally cheaper (one statement per connection rather than per transaction).
Rejected outright: with a connection pool it is a cross-tenant read waiting for
concurrency. The test `test_context_does_not_survive_into_the_next_borrower`
exists specifically because this alternative is the one someone will propose as
an optimization.

## Deployment

The production path, recorded so the NOLOGIN choice does not silently become
permanent:

1. Create a dedicated **login** role with a credential from the environment:
   `CREATE ROLE sros_runtime LOGIN PASSWORD … IN ROLE sros_app;`
2. Point `DATABASE_URL` at it.
3. Leave `APP_DB_ROLE=sros_app` — `SET LOCAL ROLE` still applies, and it is
   harmless when the connecting role already has those privileges.

`APP_DB_ROLE` may be blanked, which disables layer 2. `load_settings` **refuses
to start** when it is blank outside development, for the same reason it refuses
a development workspace outside development: a deployed environment running with
one isolation layer should not be reachable by omitting a variable.

## Pros

- A forgotten `WHERE` is no longer a leak.
- An aggregate query written without a tenant predicate returns that tenant's
  data, which is the failure mode ADR-005 ranked as hardest to catch in review.
- The tenant context cannot outlive its transaction, so a pooled connection
  cannot carry a tenant between users.
- Cross-tenant writes are refused by the database, not merely by convention.
- The runtime loses the ability to issue DDL, for free.
- `/ready` reports whether policies are active, so "designed for RLS" and "RLS
  enabled" stop being indistinguishable from outside.

## Cons

Stated concretely, because these are the costs accepted:

- **Every tenant-scoped read now runs inside a transaction.** That is a real
  change: reads that were single statements now open and commit a transaction to
  carry `SET LOCAL`. The overhead is small and the alternative is a context that
  outlives the work it was set for.
- **`SET LOCAL ROLE` is one more thing that must not be forgotten.** It is
  centralized in `Database`, exactly like the cache prefix and the vector
  filter, and a connection that skips it is a connection with no tenant context
  — which fails closed rather than open. But the property is enforced in one
  place, not by the database.
- **A superuser still bypasses everything.** `FORCE` binds the owner, not a
  superuser. Anyone connecting as one — a DBA, a migration, a psql session — sees
  every workspace. That is unavoidable and is why layer 1 remains.
- **Policies are invisible in application code.** A developer reading a
  repository method sees the `WHERE` clause and not the policy, so a query that
  behaves unexpectedly has a cause that is not in the file being read.
- **Debugging gets harder.** "No rows" now has two possible causes: there are
  none, or the tenant context was not set. `privileged_transaction()` exists for
  exactly that diagnosis and is named awkwardly so it does not drift into a
  request path.
- **`ON CONFLICT` and RLS interact subtly.** A conflicting row that the policy
  hides is still a conflict. Nothing in this system depends on the difference
  today; something eventually will.
- **A migration that must touch tenant rows now needs a tenant context**, or the
  privileged path. Forward-only migrations that only issue DDL are unaffected.

## Future impact

**Becomes easy:** trusting an ad-hoc query; adding a reporting path without
auditing every join; onboarding someone who has not memorised the tenant rule.

**Becomes hard:** cross-tenant administrative queries through the normal path
(deliberately — they should require explicit intent); reasoning about an empty
result without checking the context.

**Revisit if:** a legitimate cross-tenant workload appears — global
deduplication of collected content is the plausible one (ADR-005 §The
deliberately open question) — at which point it needs its own role and its own
policy rather than an exemption bolted onto this one.

**Cost of reversal:** low. Dropping the policies is one migration, and the
repository filter alone is exactly the Mission 0.3 behaviour. The asymmetry is
the argument: adding RLS to a system with rows is cheap now and expensive later.

## Compliance with authoritative specifications

- **ADR-005 §Future row-level security** — all four preconditions now satisfied:
  `NOT NULL` columns, leading composite indexes, a role RLS can constrain, and a
  connection-layer tenant context. The ADR's own framing is honoured: RLS is the
  backstop, never the primary mechanism.
- **ADR-005 §Data isolation risks** — the "aggregate/analytics query forgetting
  the filter" row listed RLS as the backstop. It now exists.
- **ADR-008 §Tenant isolation** — "RLS is designed for but not enabled" is
  superseded by this ADR. Everything else in ADR-008 stands.
- **ADR-011** — the repository layer is unchanged and still filters explicitly;
  `tenant_transaction` is where the policies are entered.
- **`data-retention-policy-v1.md` §5.2** — deletion scoped by `workspace_id`
  becomes enforceable at the database level, not only in application code.
- **`docs/CLAUDE.md` §Canonical invariants (Tenancy)** — `workspace_id` is still
  never inferred and never defaulted. The policy fails closed rather than
  supplying one.
