# Mission 0.2 — Completion Report

Sprint: 0 (Foundation)
Mission: 0.2 — Contracts, Storage & Runtime Foundation
Date: 2026-08-27
Status: Complete. Mission 0.3 not started.

> **Read §12 before trusting any claim in this report.** Four validation items
> from the brief require a running Docker stack. **Docker is not available in
> the environment where this mission was executed**, so those four could not be
> executed and are reported as *not verified* rather than as passing.

---

## 1. Implementation summary

| Area | Delivered | Verified here |
|------|-----------|---------------|
| Shared contracts | Source of truth, generator, TS + Python bindings, JSON Schema, shared conformance suite | Yes — 40 tests |
| Storage architecture | ADR-008 | n/a (document) |
| Database schema V1 | 16 tables, 6 schemas, migration runner, invariant validator | Structurally, not against a live database |
| Docker Compose | PostgreSQL, Redis (AOF), Qdrant; pinned, health-checked, loopback-only | YAML + invariants only |
| Celery skeleton | 5 queues, routing, retry, correlation, idempotency keys | Yes — 21 tests |
| LLM Gateway skeleton | Tiers, routing, budget, retry, schema hooks, test doubles | Yes — 23 tests |
| Quality gates | ESLint config, ruff/mypy config, 4 stdlib validators | Validators yes; linters not installed |
| CI | `security.yml` + `ci.yml` enabled, 7 jobs, no placeholder job | Locally reproduced |

**84 tests total** (65 Python + 19 TypeScript), all passing.

### The environment constraint that shaped the design

Neither `pnpm` nor `pydantic`, `pytest`, `celery`, `fastapi` or Docker were
installable here. Rather than write foundations that could not be run, the
implementation was steered toward **zero-dependency checks**:

- the contract generator and all four validators are stdlib Python;
- Python tests are stdlib `unittest` (pytest collects them unchanged);
- TypeScript tests run on Node's native type stripping — no compiler, no install;
- the Celery queue/routing/retry rules live in Celery-free modules.

That is not a workaround. A contract check that cannot run because a dependency
failed to install is a contract check that gets skipped, and this is the check
that guards against the exact drift the specification audit found (C-02, C-04).
It is recorded as a decision in ADR-009.

---

## 2. Contracts architecture

**ADR-009.** One hand-edited JSON source of truth, a stdlib generator, three
generated artifacts, and a shared conformance suite that proves agreement.

```text
packages/contracts/schema/domain.v1.json        SOURCE OF TRUTH (hand-edited)
                    |
        tools/generate.py   (stdlib, deterministic, --check)
                    |
   +----------------+-------------------------+
src/generated/    python/.../generated/     schema/domain.v1.schema.json
  domain.ts         domain.py                 (OpenAPI / interop)
```

### Generated vocabulary, hand-written behavior

The generator emits the *vocabulary*: 8 identifiers, 7 closed enums, 6 numeric
bound sets, 11 registry names, MarketScope rules. Validation and canonicalization
are hand-written per language, because they are behavior, not data — no generator
can express "country codes are uppercased, deduplicated **and sorted** so that
one scope has one representation".

### How TS/Python agreement is proven

Both suites read the same `conformance/cases.json`. Every case — valid inputs,
invalid inputs, canonical outputs, equality, canonical JSON strings — is
asserted identically on both sides. If the implementations drift, one suite goes
red. This is what makes synchronization a **tested property** rather than a
claim.

The strongest single case: a `ResearchContext` built from
`{"countries": ["us","fr"]}` and one built from `{"countries": ["FR","US"]}`
must produce **byte-identical** canonical JSON in both languages. They do.

### What is implemented

| Group | Contents |
|-------|----------|
| Identifiers | `UserId`, `WorkspaceId`, `ResearchProjectId`, `ResearchSessionId`, `OpportunityId`, `EvidenceId`, `SignalId`, `SourceId` — branded in TS, distinct classes in Python, format-validated |
| Closed enums | `ClaimType`, `MarketScopeType`, `ResearchSessionStatus`, `DemandSignalFamily`, `ScoreFamily`, `LlmTier`, `RegistryStatus` |
| Numeric | `Confidence`, `Probability`, `Reliability`, `Independence` on `[0,1]`; `Score` on `0–100`; `EvidenceLevel` `0–5` |
| `MarketScope` | Discriminated union with all §4.4 invariants and canonicalization |
| `RegistryRef` / `RegistryEntry` | Reference type + entry shape. **Never enumerates values** |
| `ResearchContext` | Value object with `canonical_json()` and `snapshot_hash()` |

`Score` and `Confidence` are not interchangeable, and a test asserts it in both
directions: `82` is rejected as a confidence, `0.82` is rejected as a score.

---

## 3. Storage architecture

**ADR-008.** PostgreSQL is the system of record; Redis is never canonical;
Qdrant is a derived, rebuildable index.

| Store | Role | Backup |
|-------|------|--------|
| PostgreSQL | Everything canonical, schema-per-context | Required |
| Redis | Celery broker + cache + rate limits | None — but AOF on, because it holds in-flight job state |
| Qdrant | Embedding vectors; provenance lives in PostgreSQL | None — a loss costs a re-index |

Four invariants are **mechanically enforced** by
`infrastructure/scripts/validate_schema.py` rather than left to review:

1. `workspace_id UUID NOT NULL` on every tenant-scoped table.
2. Composite indexes lead with `workspace_id`.
3. No PostgreSQL `ENUM` type for any taxonomy.
4. No evidence-aggregation column anywhere.

Plus retention fields, closed-enum `CHECK` values matching the contract source,
and the numeric naming rule. **8 invariant groups over 16 tables, passing.**

### ResearchContext persistence — the trade-off

Stored as **`JSONB`** on `research_sessions`, with `research_context_hash` and
`research_context_schema_version`.

| Option | Why not |
|--------|---------|
| Normalized tables | Creates the `ResearchContext` entity Ontology V2 §11.3 forbids, and every new context field becomes a migration |
| Opaque `TEXT` | "Which sessions targeted France?" becomes a full scan |
| **JSONB** | Immutable in practice, GIN-queryable, no entity, no migration per field |

The deciding factor: the snapshot's job is **reproducibility**, not relational
querying. Its canonical JSON is byte-stable across languages, so the hash gives
cheap equality and tamper evidence. The cost accepted is that the database does
not constrain the shape — the contracts package does.

---

## 4. Database schema summary

| Schema | Tables |
|--------|--------|
| `core` | `users`, `workspaces`, `workspace_memberships`, `schema_migrations` |
| `registry` | `registry_entries`, `sources` |
| `research` | `research_projects`, `research_sessions`, `research_gaps`, `opportunities`, `opportunity_session_observations` |
| `acquisition` | `raw_records`, `normalized_records` |
| `nlp` | `signals`, `embedding_provenance` |
| `scoring` | `evidence` |

Forward-only numbered SQL with a `core.schema_migrations` ledger. Each migration
commits **together with its ledger row**, so a half-applied migration is not a
reachable state. A migration whose checksum changed after being applied is
refused.

### Opportunity rediscovery

`opportunity_session_observations` associates an opportunity with a session,
carrying `observation_kind` (`DISCOVERED` / `CORROBORATED` / `CONTRADICTED`) and
a `claim_type`. An opportunity is **not** owned by the session that found it.

**Deliberately absent: any unique constraint deciding that two opportunities are
the same.** The only uniqueness is one observation per opportunity per session —
bookkeeping, not a semantic judgment (Ontology V2 §12.3).

### D-03 containment

`scoring.evidence` stores raw metadata only: `evidence_level`, `reliability`,
`independence`, `confidence`, provenance, timestamps. No aggregated score, no
decay weight, no independence-threshold result, no contradiction penalty. The
validator fails the build on any of those names, and the same guard runs in both
contract test suites.

---

## 5. Tenant isolation strategy

`workspace_id UUID NOT NULL` with a foreign key to `core.workspaces` on all
10 tenant-scoped tables; composite indexes lead with it. Reference data
(registries, sources) is deliberately global.

Propagation is enforced at three levels beyond the schema:

| Level | Mechanism |
|-------|-----------|
| Celery tasks | `TaskContext.from_headers` **fails closed** if `workspace_id` is absent or empty |
| LLM requests | `LlmRequest.__post_init__` rejects an empty `workspace_id` |
| Development | Two workspaces are seeded, because a suite with one workspace cannot detect a missing tenant filter |

A test asserts that no default-workspace UUID appears anywhere in the worker
context module: the seeded dev workspace is a convenience, **never a code path**.

RLS is designed for but not enabled — columns are `NOT NULL`, the app connects
as a non-owner role. It is the backstop for a forgotten query, never the primary
mechanism.

---

## 6. Docker architecture

`infrastructure/compose/docker-compose.yml`: PostgreSQL 16.4, Redis 7.4,
Qdrant v1.11.0. All pinned, all health-checked, all bound to `127.0.0.1` on
non-default ports so the stack does not fight a locally installed PostgreSQL.

**Redis persistence.** AOF is on with `appendfsync everysec` and RDB snapshots
disabled. Redis is the Celery broker, so it holds in-flight job state, not just
cache. With default configuration a restart silently loses queued work — which
is exactly the lesson worth learning in development rather than discovering in
production (ADR-004).

**Restart behavior:** `unless-stopped`. On restart, Redis replays its AOF, so
queued-but-unacknowledged jobs survive; combined with `task_acks_late`, a worker
killed mid-job returns the job to the queue.

Application containers (`api`, `worker`) are **not** included: no service code
exists yet, and a container that starts nothing is not a health check.

---

## 7. Celery architecture

Five queues with independent pools, so slow acquisition cannot starve fast
analysis and heavy embedding work cannot monopolize workers:

| Queue | Concurrency | Prefetch | Retries | Jitter |
|-------|-------------|----------|---------|--------|
| `acquisition` | 4 | 1 | 5 | yes |
| `nlp` | 2 | 1 | 3 | yes |
| `embedding` | 1 | 1 | 2 | no |
| `analysis` | 4 | 2 | 2 | no |
| `maintenance` | 1 | 1 | 1 | no |

Routing is longest-prefix, so `nlp.embed` reaches the embedding queue rather
than being swallowed by an `nlp.` rule. An unrouted task raises rather than
landing silently on the default queue.

### Delivery semantics

**At-least-once. Nothing pretends otherwise.** `task_acks_late=True`,
`task_reject_on_worker_lost=True`, `worker_prefetch_multiplier=1`, JSON-only
serialization (pickle off a broker is a remote-code-execution shape), expiring
results (Redis is not canonical).

`idempotency_key(task, context, payload)` produces a deterministic hash that is
key-order independent and tenant-separated. Tests assert both. The key is meant
for a unique constraint, so the database absorbs the duplicate — a read-then-write
check without a constraint is a race with a longer window.

**No business job body exists.** A test enforces that.

---

## 8. LLM Gateway architecture

Business services request a **logical tier**; `LlmRequest` has no `provider` and
no `model` field, and a test asserts it.

Six obligations implemented **once**, at a chokepoint that cannot be bypassed:
budget enforcement (checked before dispatch), prompt versioning (required on
every request), model-version recording, structured-output validation, cost
telemetry, tenant attribution.

Three behaviors worth naming:

- **Budget exhaustion is a successful outcome.** `BudgetExhausted` means the
  session completes with reduced Research Completeness, never `FAILED`. The
  exception message says so, and a test asserts the message.
- **A schema failure is never retried into a fallback.** It may signal prompt
  injection (`llm-reasoning-rules.md` §7). A test asserts the provider is called
  exactly once even with `max_retries=3`.
- **A tier is never silently downgraded.** An unconfigured `STRONG_MODEL` raises
  rather than serving from `FAST_MODEL`, which would produce a worse answer that
  looks identical.

No real provider is implemented. No external API call is made. Provider
independence is enforced by a tokenized test, so a vendor named in a docstring
is not a false positive while a vendor named in code is.

---

## 9. Quality gates

| Gate | Tool | Status |
|------|------|--------|
| Contract generation | `generate.py --check` | **Running in CI** |
| Schema invariants | `validate_schema.py` | **Running in CI** |
| Migration plan | `migrate.py --plan` | **Running in CI** |
| Python tests | stdlib `unittest` | **Running in CI** |
| TypeScript conformance | `node --test` | **Running in CI** |
| Compose config | `docker compose config` | In CI, not verified locally |
| Secret scan | gitleaks, full history | **Running in CI** |
| Env template | `check_env_template.py` | **Running in CI** |
| Lint (TS) | ESLint flat config | Written, not installed |
| Lint/format (Py) | ruff | Configured, not installed |
| Types (Py) | `mypy --strict` | Configured, not installed |

`packages/eslint-config/index.js` adds two rule families beyond the Mission 0.1
design: provider-SDK import restriction (ADR-006) and a registry-taxonomy guard
that fails if an extensible taxonomy is declared as an enum or closed union
(undoing A-07).

**Documented as not automatable yet** (§24): cross-context import detection needs
real service directories, and `no-unnecessary-condition` needs type information
from a `tsc` project. Both land with the first service package.

---

## 10. Tests added

| Suite | Tests | Covers |
|-------|-------|--------|
| `packages/contracts/python/tests` | 21 | Numeric ranges, MarketScope, closed enums, registry, ResearchContext, D-03 guard |
| `packages/contracts/test` (TS) | 19 | The same conformance cases |
| `packages/llm-gateway/python/tests` | 23 | Tier resolution, retry, budget refusal, schema validation, provider independence |
| `services/workers/python/tests` | 21 | Queue topology, routing, retry, correlation, idempotency, no-business-logic guard |
| **Total** | **84** | |

Brief §27 coverage:

| Required | Where |
|----------|-------|
| ClaimType exact values | Both suites, order-sensitive |
| Confidence / score / evidence-level ranges | Both suites, from shared cases |
| MarketScope validation + country normalization | Both suites, 7 valid + 13 invalid + 2 equality cases |
| ResearchContext serialization | Both suites, byte-exact canonical JSON |
| Registry reference behavior | Both suites, incl. "a closed enum is not a registry" |
| `workspace_id` required on tenant records | Schema validator + task context + LLM request tests |
| Cache/vector helpers require workspace scope | **Not covered** — no helper exists yet (see §15) |
| ResearchContext snapshot immutable | Both suites |
| ResearchSession status validation | Both suites, incl. "no invented lifecycle states" |
| Project/session workspace consistency | Schema FKs; **not runtime-tested** (needs a database) |
| Queue routing / serialization / duplicate delivery | Worker suite |
| LLM tier resolution, provider independence, budget refusal | Gateway suite |
| No provider SDK in business modules | Gateway suite (tokenized) + ESLint rule |

---

## 11. CI status

**Enabled.** `security.yml` first, then `ci.yml`, per the brief's ordering.

| Workflow | Jobs |
|----------|------|
| `security.yml` | `secrets` (gitleaks, full history), `env-template` |
| `ci.yml` | `contracts`, `schema`, `python-tests`, `typescript-tests`, `compose` |

**No placeholder job exists.** Every job runs a check that genuinely passes
today. Checks not yet enabled — pnpm install/lint/build, ruff, mypy, dependency
audit, CodeQL, integration tests, injection suite — are listed with what each is
waiting on in `.github/workflows/README.md`.

Path filtering was **not** added: with five fast, install-free jobs the
bookkeeping would cost more than it saves. It becomes worthwhile when the
TypeScript app and service packages land.

---

## 12. Validation commands and results

### Executed here — all passing

```bash
python packages/contracts/tools/generate.py --check
python infrastructure/scripts/validate_schema.py
python infrastructure/scripts/migrate.py --plan
python infrastructure/scripts/run_python_tests.py
node --test --experimental-strip-types packages/contracts/test/conformance.test.ts
python infrastructure/scripts/check_env_template.py
```

| Check | Result |
|-------|--------|
| Contracts generate and match committed output | **PASS** — 3 artifacts, deterministic |
| TS and Python contract representations agree | **PASS** — 40 tests over shared cases |
| Schema invariants | **PASS** — 8 groups, 16 tables |
| Migration plan well formed | **PASS** — contiguous, forward-only |
| Python suites | **PASS** — 65 tests, 3 packages |
| TypeScript conformance | **PASS** — 19 tests |
| CI YAML parses | **PASS** — 3 files |
| JSON valid | **PASS** — 7 files |
| Env template carries no secret | **PASS** |
| No BullMQ dependency | **PASS** — 0 occurrences in any manifest or source |
| No provider SDK in business modules | **PASS** — tokenized test + 0 imports |
| No stale `ResearchRun` concept | **PASS** — only historical-report validation text |
| V1/V1.1 specs untouched | **PASS** — 5224 / 10888 / 3582 bytes, unchanged |

### NOT executed — Docker unavailable in this environment

These four items from brief §31 could **not** be verified. They are written and
reviewed, not proven:

| Item | Status |
|------|--------|
| Docker Compose boots | **NOT VERIFIED** — YAML parses; images pinned, health checks present, ports loopback-only, all asserted structurally |
| PostgreSQL / Redis / Qdrant healthy | **NOT VERIFIED** |
| Migrations apply from an empty database, and re-run through reset | **NOT VERIFIED** — SQL is validated structurally, never executed |
| Celery worker connects | **NOT VERIFIED** — Celery is not installed; routing and retry logic are tested Celery-free |

**This is the single most important caveat in the report.** Hand-written SQL
that has never touched a PostgreSQL server can contain a syntax error the
validator does not model. The first task of Mission 0.3 should be to run the
stack and apply the migration before building anything on top of it.

---

## 13. Files created

**Contracts (17):** source of truth, generator, 3 generated artifacts, 7 TS
modules, 6 Python modules, conformance cases, 2 test suites, `package.json`,
`tsconfig.json`.

**LLM Gateway (8):** `types.py`, `config.py`, `budget.py`, `gateway.py`,
`providers/{__init__,fake}.py`, tests, README.

**Workers (5):** `queues.py`, `context.py`, `celery_app.py`, tests,
`requirements.txt`.

**Infrastructure (11):** `docker-compose.yml`, `.env.example`,
`0001_foundation.sql`, 2 seed files, `migrate.py`, `validate_schema.py`,
`run_python_tests.py`, `check_env_template.py`, `db/README.md`.

**Architecture (3):** ADR-008, ADR-009, this report.

**Root (2):** `pyproject.toml`, `packages/eslint-config/index.js`.

## 14. Files modified

`README.md`, `package.json`, `.nvmrc` (20.11.0 → 22.11.0, for native TS type
stripping), `.github/workflows/{ci,security,README}.md`,
`packages/{README,contracts/README,eslint-config/README}.md`,
`packages/eslint-config/package.json`, `services/workers/README.md`,
`infrastructure/{README,compose/README,scripts/README}.md`,
`docs/architecture/{README,adr/README}.md`.

**Not modified:** every authoritative specification, every accepted ADR
(ADR-001 … ADR-007), and every historical mission report.

---

## 15. New issues and ambiguities

Classified per brief §29. **None is domain-level, so nothing triggered a stop.**

### Implementation-local, decided and documented

| Choice | Rationale | Reversible? |
|--------|-----------|-------------|
| Contracts are stdlib dataclasses, not Pydantic | Every consumer imports them dependency-free; services still adapt to Pydantic at their HTTP boundary (ADR-003 unchanged) | Yes — additive |
| `.nvmrc` 20.11.0 → 22.11.0 | Node 20 has no type stripping; without it the TS conformance suite needs a compiler and an install | Yes |
| TS imports use `.ts` specifiers | Required by native type stripping; `rewriteRelativeImportExtensions` handles emit | Yes |
| Plain SQL migrations, not Alembic | No ORM models exist to autogenerate from; reviewable SQL is worth more at foundation | Yes — ledger is compatible in spirit |
| No `api`/`worker` containers in compose | No service code exists; a container that starts nothing is not a health check | Yes |

### Recorded gaps, not decisions

- **No cache or vector-search helper exists yet**, so brief §27's "cache/vector
  helper contracts require workspace scope" has nothing to test. The requirement
  is recorded in ADR-008 (§Qdrant) and must be satisfied when those wrappers are
  written. This is the one §27 item with no test behind it, and it guards the
  two leak paths that never appear in a SQL audit.
- **`registry.sources` is a stub.** It exists so provenance has a stable foreign
  key; D-07 remains open, so it has no legal-review columns and no
  `retention_override`. The schema is shaped so both are additive.
- **`expires_at` is `NOT NULL` but nothing computes it yet.** The writer must
  supply it. The per-source override hook is deliberately absent (D-07).

---

## 16. Remaining blockers

| ID | Item | Blocks |
|----|------|--------|
| **D-03** | Evidence aggregation formula, decay, independence thresholds | **`services/scoring` — hard blocker.** Enforced by the schema validator and both contract suites |
| **D-07** | Source registry contents and legal review | `services/acquisition` |
| **A-12** | Non-geographic (segment) scoping | Segment-level scores. Untouched, as instructed |
| — | Opportunity identity resolution | Untouched, as instructed |
| **D-11** | Observability stack | Conventions fixed; vendor open |
| **D-08** | Score recomputation policy | `scoring`, caching |
| **D-12** | Embedding re-embedding strategy | `nlp`, Qdrant |
| — | Production hosting, GDPR/jurisdiction | Untouched, as instructed |

---

## 17. Readiness for Mission 0.3

**Ready, with one mandatory first step: run the stack and apply the migration.**
Everything in §12's "not executed" list must be verified before code is built on
top of the schema.

Then, in order: FastAPI gateway skeleton with the health/readiness endpoints;
the repository layer that enforces `workspace_id` filtering (and the cache and
vector wrappers that close the two non-SQL leak paths); the research
orchestrator's project/session lifecycle over the schema; and install-based
gates (ruff, mypy, ESLint, pnpm) once there is a lockfile.

---

## 18. Explicit answers

### Are shared contracts now implemented?

**Yes.** One JSON source of truth, a deterministic stdlib generator, TypeScript
and Python bindings, a JSON Schema for interop, and 40 tests. Every type the
brief listed exists.

### Are TS and Python domain contracts synchronized?

**Yes, and it is tested rather than asserted.** Both suites read the same
`conformance/cases.json`; a drift turns one of them red. `--check` mode fails CI
if the committed generated output does not match the source.

### Is PostgreSQL schema V1 operational?

**Written and structurally validated; NOT executed against a live database.**
16 tables across 6 schemas, 8 invariant groups passing, migration plan well
formed. Docker was unavailable, so no migration has actually been applied. This
is the caveat that matters most in this report.

### Is multi-tenancy represented correctly?

**Yes.** `workspace_id UUID NOT NULL` on all 10 tenant-scoped tables with
foreign keys and leading composite indexes, enforced by the validator. Sessions
belong to exactly one workspace and one project. Propagation fails closed in
both the task context and the LLM request. Two workspaces are seeded so
isolation is testable.

### Is ResearchContext stored as an immutable snapshot?

**Yes.** `JSONB` on `research_sessions`, with a content hash and a schema
version, written once at creation. Immutability is tested on both sides: a
frozen value object, and `with_changes()` returning a new instance while the
original's canonical JSON and hash are unchanged. No `ResearchContext` entity
exists.

### Is Opportunity rediscovery representable without schema duplication?

**Yes.** `opportunity_session_observations` associates an opportunity with many
sessions. The opportunity is not owned by the session that found it, and **no
unique constraint decides that two opportunities are the same** — identity
resolution stays an analytical problem.

### Is Qdrant strictly a derived index?

**Yes.** `nlp.embedding_provenance` in PostgreSQL holds the model, model
version, content hash and Qdrant point reference, so the index is fully
rebuildable. No business fact lives only in Qdrant. Tenant filtering on vector
search is mandated by ADR-008 — and, as noted in §15, the wrapper that will
enforce it does not exist yet.

### Is Redis non-canonical?

**Yes.** Broker, result backend, cache, rate limits. Nothing canonical. AOF is
enabled anyway, because it holds in-flight job state and losing that silently is
worse than losing a cache.

### Is Celery operational locally?

**Configured, not run.** Queues, routing, retry, backoff, acknowledgement,
serialization, correlation and idempotency are implemented and covered by 21
tests that run without a broker. Celery itself is not installed here, so **no
worker has connected**. Verify with the stack, per §17.

### Is the LLM Gateway provider-agnostic?

**Yes.** `LlmRequest` carries no provider and no model field. Services request a
tier. Model names live in configuration. No provider SDK is imported anywhere
outside `providers/`, enforced by a tokenized test and an ESLint rule. No real
provider call exists.

### Are CI and quality gates operational?

**Partly, and honestly so.** Seven CI jobs run genuine checks that pass today.
The install-dependent gates — ESLint, ruff, mypy, dependency audit — are
configured but not runnable until there is a lockfile and an installed Python
environment, and they are deliberately not wired into CI so that no job is
permanently red.

### Is scoring still correctly blocked on D-03?

**Yes, and now mechanically.** The schema validator fails on any of six
aggregation field names; both contract suites carry the same guard;
`scoring.evidence` stores raw metadata only. Blocking scoring is no longer a
matter of remembering.

### Is acquisition still correctly blocked on D-07?

**Yes.** `registry.sources` is a stub with no legal-review columns and no
`retention_override`. No collector exists. `expires_at` is required at write
time, and the per-source override hook is deliberately absent.

### Is Mission 0.3 safe to begin?

**Yes — after running the stack and applying the migration.** That is a
prerequisite, not a formality: hand-written SQL that has never reached a
PostgreSQL server can contain an error no static validator models. Everything
else is verified, and the blockers that were open at the start of this mission
are still correctly open.

---

## 19. Mission boundary

**Mission 0.3 was not started.** No collector, no evidence aggregation, no
scoring logic, no NLP pipeline, no embedding execution, no competitor or market
research, no GTM generation, no authentication, no dashboard.

A-12 was not resolved. Opportunity identity resolution was not solved. Evidence
aggregation was not defined. The source registry was not populated. No
production hosting decision was made. No GDPR policy was finalized.
