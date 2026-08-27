# ADR-005 — Workspace-centric multi-tenancy

- **Status:** Accepted
- **Date:** 2026-08-27
- **Deciders:** Project owner (Mission 0.1.1, §4 — explicit human decision)
- **Supersedes:** none
- **Related:** ADR-004, audit **D-05**, `opportunity-ontology-v1.1.md` §6,
  `data-retention-policy-v1.md`

---

## Context

Nothing in the seven authoritative specifications stated whether Startup Research
OS is a personal research tool for one operator or a multi-tenant product with
customer accounts. The specification audit recorded this as **D-05** and flagged
it as the most urgent open decision, for one reason:

**Retrofitting a tenant boundary onto a system that already holds production data
is among the most expensive migrations in this class of system.** It touches every
table, every query, every index, every cache key, every queue payload and every
log line. It cannot be done incrementally, and it cannot be done safely under
time pressure.

Deferring the decision was not neutral. "Decide later" is functionally a decision
for single-tenant, with a very expensive escape hatch.

## Decision

**Startup Research OS is designed as a multi-tenant SaaS from the beginning,
using a workspace-centric model.**

```text
User
  ↓
Workspace          ← the tenant boundary
  ↓
Research Project
  ↓
Research Session
  ↓
Opportunity
```

**`workspace_id` is the tenant boundary.** Every primary domain resource carries
it, from the first migration.

Authentication and authorization are **not implemented** in this mission, and are
explicitly out of scope. What is established now is the domain and architectural
contract that lets them be added later without a data migration.

During local development the system uses a single **default development
workspace** with a fixed, well-known id.

## Tenant boundary

The **Workspace** is the unit of isolation, billing, quota and — eventually —
access control. Not the User, and not the Research Project.

Choosing Workspace rather than User is what makes teams and organizations
possible later without a second migration. A user-scoped model looks simpler
today and forecloses collaboration permanently: converting `user_id`-owned rows
into shared resources means rewriting ownership on every table, which is the
exact migration this decision exists to avoid.

**A user is not a tenant.** A user is a principal that may have access to one or
more workspaces. That indirection costs one join table now and saves a rewrite
later.

## Resource ownership strategy

### Tenant-scoped — carry `workspace_id`, NOT NULL

Everything that represents research output or research state:

| Context | Tenant-scoped resources |
|---------|------------------------|
| `research-orchestrator` | `research_project`, `research_session`, `research_plan`, `task_ledger`, `research_gap` |
| `acquisition` | `raw_record`, `normalized_record`, `collection_run` |
| `nlp` | `signal`, `classification`, `cluster`, `independence_estimate` |
| `scoring` | `evidence`, `score`, `score_component` |
| `market-intelligence` | `market_context`, `market_estimate`, `momentum` |
| `competition` | `competitor`, `competition_gap`, `positioning` |
| `execution` | `plan`, `risk_register`, `validation_plan` |
| `workers` | `job`, `job_attempt`, `dead_letter` |

### Global — no `workspace_id`

Reference data shared by every tenant:

- `source` registry and its legal-review records
- `scoring_profile` and the dimension registry
- model registry (embedding and LLM model versions)
- framework/prompt version records

### The deliberately open question: raw record sharing

Two workspaces researching the same market will collect the same public sources.
Storing a separate copy per workspace is wasteful; sharing one copy across
workspaces leaks the fact that another tenant collected it, and entangles the
retention policies of two tenants in one row.

**Decision for now: raw and normalized records are tenant-scoped.** Duplication
is accepted. Deduplicating across tenants is an optimization that can be added
behind a content-addressed store later; un-sharing data that was shared is not
reversible in the same way.

This is recorded as an explicit trade-off, not an oversight. Revisit it when
storage cost is measured, not before.

## `workspace_id` propagation

The rule: **`workspace_id` is never inferred, never defaulted at a boundary,
never reconstructed from another field.** It is passed explicitly and validated.

```text
HTTP request
  → gateway resolves workspace from the request context
  → passed explicitly to every internal call
  → written into every Celery task payload
  → carried on every log line and metric
  → written to every tenant-scoped row
```

Concretely:

1. **Gateway.** Resolves the workspace once, at the edge. Today from a
   configured default; later from the authenticated session. Every downstream
   call receives it as an explicit parameter.
2. **Service interfaces.** Every tenant-scoped operation takes `workspace_id` as
   a required argument. Not optional, not keyword-with-default. A signature that
   allows it to be omitted will eventually be called without it.
3. **Celery task payloads.** Every task carries `workspace_id` alongside `run_id`
   and `correlation_id` (ADR-004). A worker never resolves the workspace itself —
   a worker that can look up "the current workspace" is a worker that can look up
   the wrong one.
4. **Repository layer.** Every query on a tenant-scoped table filters by
   `workspace_id`. This is enforced at the repository, so that no call site can
   forget it.
5. **Cache keys.** Every Redis key for tenant data is prefixed with the workspace.
   An unprefixed cache key is a cross-tenant data leak with no database
   involvement — and it will not show up in any query audit.
6. **Logs, metrics, traces.** `workspace_id` is a standard field. It must never
   appear in a URL path segment carrying personal data, and it is not a secret.
7. **Vector store.** Qdrant payloads carry `workspace_id` and every search filters
   on it. A vector search without a tenant filter returns another tenant's
   research — this is the least obvious leak path in the system, because it does
   not go through SQL.

## Future row-level security

PostgreSQL RLS is the intended defense-in-depth layer, **not** the primary
mechanism.

Design now so it can be enabled later:

- Every tenant-scoped table has `workspace_id NOT NULL` from its first migration.
  RLS cannot be added to a table where the column is nullable or absent.
- Composite indexes lead with `workspace_id`. Retrofitting index order on a large
  table is expensive and easy to postpone indefinitely.
- The application connects as a role that RLS can constrain — not as the table
  owner, which bypasses RLS silently.
- The session-level tenant context (`SET LOCAL app.workspace_id`) is set by the
  connection layer, so enabling RLS later is a migration plus a policy, not an
  application rewrite.

**RLS is not a substitute for repository-level filtering.** It is the backstop
that catches the query someone forgot. Relying on it alone means every bug is a
production data leak; relying on filtering alone means one forgotten `WHERE` is a
production data leak. Both, or neither is trustworthy.

## Local development strategy

- A single **default development workspace** with a fixed, well-known UUID,
  seeded by `infrastructure/scripts/bootstrap-local.sh`.
- The gateway resolves it from configuration while authentication does not exist.
- **The default is a development convenience, never a code path.** No service,
  repository or task may fall back to a default workspace when one is missing.
  A missing `workspace_id` is an error, in every environment.

That last rule is the one that matters. A convenience default that leaks into
service code becomes the mechanism by which one tenant's data is written into
another tenant's workspace, and it will be invisible until it is not.

Integration tests seed **at least two** workspaces and assert isolation
explicitly. A test suite with one workspace cannot detect a missing tenant filter.

## Future authentication integration

Out of scope for this mission. The contracts established here are what allow it
to be added cleanly:

1. A `user` entity and a `workspace_membership` join table (user, workspace,
   role) — the indirection that makes teams possible.
2. The gateway resolves the workspace from the authenticated session instead of
   from configuration. **No service below the gateway changes**, because it
   already receives `workspace_id` explicitly.
3. Authorization becomes a check at the gateway plus a role model on membership.
4. Organizations, if needed, become a parent of Workspace — an additive change,
   because Workspace is already the tenant boundary rather than the User.

The measure of whether this ADR did its job: adding authentication should require
**no change to any tenant-scoped table**.

## Data isolation risks

Ranked by how easily each one escapes review:

| Risk | Why it is dangerous | Mitigation |
|------|--------------------|-----------|
| **Cache key without workspace prefix** | Leaks across tenants with no database query involved; invisible to any SQL audit | Prefix enforced in the cache client, not at call sites |
| **Vector search without tenant filter** | Returns another tenant's research; does not appear in query review | `workspace_id` in every Qdrant payload; filter enforced in the search wrapper |
| **Celery task missing `workspace_id`** | Worker writes to the wrong tenant, or to the default | Required field in the task contract; validated on receipt, job fails closed |
| **Aggregate/analytics query forgetting the filter** | Cross-tenant totals presented as one tenant's data | Repository-level enforcement; RLS as backstop |
| **Shared raw records** | Reveals collection activity across tenants; entangles retention | Records are tenant-scoped (see above) |
| **Logs and error traces containing another tenant's content** | Leaks through observability rather than through the product | Never log raw collected content (`packages/observability`) |
| **Default workspace fallback in service code** | Silent misattribution; the most likely of all of these | Missing `workspace_id` is an error everywhere, in every environment |

## Alternatives considered

### Alternative A — Single-tenant

Simplest possible model. Rejected: it forecloses the product direction and makes
the eventual migration prohibitive. The cost of the tenant column now is a column;
the cost later is a rewrite of the data layer.

### Alternative B — User as the tenant boundary

Marginally simpler than Workspace. Rejected: it makes teams, shared projects and
organizations impossible without re-owning every row. The workspace indirection
costs one join table and buys the entire collaboration roadmap.

### Alternative C — Database-per-tenant

Strongest isolation, straightforward per-tenant deletion and retention. Rejected
for this stage: operationally heavy (N databases, N migration runs, N connection
pools) and disproportionate for a system with zero users. It also fragments the
cross-tenant reference data (source registry, scoring profiles) that is
genuinely shared. Worth revisiting only if an enterprise customer requires
physical isolation.

### Alternative D — Schema-per-tenant

Between B and C. Rejected for the same operational reasons, plus it conflicts
with the existing schema-per-*context* layout (`service-boundaries.md` §5), which
uses the schema axis for a different purpose.

## Pros

- The expensive migration is avoided permanently.
- Teams, shared projects and organizations remain reachable without re-owning data.
- Per-workspace quota, budget and cost accounting become natural — which matters
  given that research runs cost real money (ADR-006).
- Retention and deletion become tractable: a deletion request is scoped to a
  workspace (`data-retention-policy-v1.md`).
- Isolation is testable from the first integration test.

## Cons

- **Every query, cache key, task payload and log line carries a tenant concern**
  from day one, including while there is exactly one tenant. That is real ongoing
  friction for zero immediate benefit.
- **The failure mode is severe.** A forgotten filter is a cross-tenant data leak,
  not a rendering bug. Single-tenant systems cannot have this class of bug at all.
- Composite indexes leading with `workspace_id` are slightly less efficient for a
  single-tenant workload.
- More schema surface: membership tables, workspace lifecycle, an eventual
  deletion cascade.
- **Discipline is required before there is any feedback.** With one workspace,
  every isolation bug is invisible. Hence the two-workspace test rule.

## Future impact

**Becomes easy:** authentication and authorization; teams and organizations;
per-tenant quotas, budgets and billing; scoped deletion and retention; per-tenant
data export.

**Becomes hard:** cross-tenant analytics (deliberately — it should require
explicit intent); global deduplication of collected content; single-tenant
performance tuning.

**Revisit if:** an enterprise requirement demands physical isolation
(database-per-tenant for that tenant only, as an addition rather than a
replacement); or storage duplication from tenant-scoped raw records becomes
measurably expensive.

**Cost of reversal:** effectively zero in the simplifying direction — a
single-tenant deployment simply uses one workspace, which is exactly the local
development mode. This asymmetry is the whole argument: multi-tenant collapses to
single-tenant for free, single-tenant expands to multi-tenant only through a
migration.

## Compliance with authoritative specifications

- `PROJECT_MANIFEST.md` §Security First — tenant isolation is a security
  property, designed in rather than postponed.
- `PROJECT_MANIFEST.md` §Modular Design — `workspace_id` is a cross-cutting
  contract, documented in `service-boundaries.md` §6, not a per-service
  invention.
- `data-principles.md` §8 (Privacy) — workspace scoping bounds the blast radius
  of any personal data and makes minimization enforceable.
- `data-principles.md` §11 (Lineage) — `workspace_id` joins source, timestamp,
  transformation and version in the provenance chain.
- `docs/CLAUDE.md` §Change control — this ADR records an architectural decision
  that no specification previously covered; it adds a contract rather than
  contradicting one.
- `opportunity-ontology-v1.1.md` §6 — tenancy is deliberately excluded from the
  analytical structure of an Opportunity. The Workspace / Research Project /
  Research Session hierarchy is scheduled for ontology V2.
- **Resolves decision D-05.**
- **Opens audit A-11** — "research run", "Research Session" and `ResearchContext`
  are three names for adjacent concepts across ADR-005, the orchestrator
  contract, and `scoring-framework-v1.1.md` §2. Reconciliation belongs to
  ontology V2 with D-01.
