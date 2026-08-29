# Service Boundaries

Version: 1.3
Status: Accepted
Date: 2026-08-29 (amended in Mission 0.4)

> **Amended in 1.3.** Tenant scoping gains a second enforcement layer
> (row-level security, ADR-012). `research-orchestrator` is now a real package
> and owns `ResearchSession` transition policy; the gateway still persists those
> rows and imports the transition table rather than holding a copy.
>
> **Amended in 1.2.** Research lifecycle terminology canonicalized: the persisted
> execution entity is `ResearchSession`, grouped under a `ResearchProject`, with
> an immutable `ResearchContext` snapshot. `research run` is retired
> (Ontology V2 §11).
>
> **Amended in 1.1.** Runtimes resolved (all backend contexts are Python —
> ADR-004), queue is Celery over Redis, `workspace_id` added as a cross-cutting
> contract (ADR-005), LLM access routed through the gateway (ADR-006).

This document defines the cross-cutting view: how the nine bounded contexts fit
together, what may call what, how they are deployed, and how they map onto the
two pipeline vocabularies in the specifications.

Each context's own responsibility, inputs, outputs, dependencies, future API and
failure modes are documented in its `services/<name>/README.md`. Those READMEs
are normative; this document is the map.

---

## 1. The nine contexts

| Service | Responsibility (one sentence, no "and") | Runtime |
|---------|------------------------------------------|---------|
| `gateway` | Adapt the outside world to the internal contexts | Python / FastAPI |
| `research-orchestrator` | Own the lifecycle of a `ResearchSession` | Python (`sros_orchestrator`, no HTTP surface yet) |
| `acquisition` | Lawfully collect raw external data with full provenance | Python (Playwright Python API) |
| `nlp` | Turn normalized text into structured signals | Python |
| `scoring` | Compute and explain the five score families | Python |
| `market-intelligence` | Describe the market context of an opportunity | Python |
| `competition` | Map competitors and compute the Competition Gap | Python |
| `execution` | Turn a scored opportunity into an actionable plan | Python |
| `workers` | Execute queued work reliably | Python / Celery |

All backend contexts are Python (ADR-004). TypeScript is confined to `apps/web`
and `packages/*`. There is no Node worker tier.

The "no *and*" constraint is the boundary test. `acquisition` collects; it does
not classify. `workers` executes; it does not decide. `gateway` adapts; it does
not compute. Every context whose responsibility needs an "and" has been split.

---

## 2. Deployment topology

`docs/CLAUDE.md` forbids premature microservices. Nine contexts are defined
anyway, because a **boundary is a contract, not a process**
(see `specification-audit.md` C-03).

### Phase 1 — foundation (now)

Four deployable units:

```
web             apps/web                        (Next.js, TypeScript)
api             gateway + research-orchestrator + scoring
                + market-intelligence + competition + execution
                                                (FastAPI, Python)
worker          workers + acquisition + nlp     (Celery, Python)
backing         PostgreSQL + Redis + Qdrant
```

`api` and `worker` share the same Python codebase and import the same context
modules. They differ only in entrypoint: `api` serves HTTP, `worker` consumes
Celery queues. That is a direct consequence of ADR-004 — with a Node worker tier
they would have been two codebases.

Contexts inside `api` talk through their declared interfaces as in-process
module calls. The call sites are identical to what they would be over HTTP; only
the transport differs.

### Phase 2 — extraction when justified

A context is extracted when it has a **different scaling profile, a different
failure domain, or a different resource shape** — not when the diagram looks
tidier.

The three real candidates:

| Context | Why it will need to be extracted |
|---------|----------------------------------|
| `nlp` | GPU/CPU-heavy, large model images, slow cold start. Wrong resource profile to share with a request-serving API |
| `acquisition` | Long-running browser automation, external rate limits, high failure rate. Its failures should not degrade the API |
| `gateway` | Scales with user traffic, which has no relationship to research workload |

Extraction changes deployment, not design, because the contract was fixed first.

### What makes extraction cheap

1. No shared tables across contexts.
2. No context imports another context's internals.
3. All shared types come from `packages/contracts`.
4. Every cross-context call goes through a declared interface with an explicit
   request and response type.

Violating any of these turns a deployment change into a rewrite.

---

## 3. Pipeline mapping (resolves audit C-05)

The specifications contain two pipeline vocabularies that do not reference each
other. They are two views of the same system, at different altitudes.

| Manifest stage (service view) | Data-principles stage (record lifecycle) | Owning context |
|-------------------------------|------------------------------------------|----------------|
| Raw Signals | — (external) | — |
| Data Collection | `raw` | `acquisition` |
| Normalization | `normalized`, `deduplicated` (exact) | `acquisition` |
| NLP | `deduplicated` (near/semantic), `enriched` | `nlp` |
| Signal Extraction | `signal` | `nlp` |
| Opportunity Discovery | `feature` (clustering into seeds) | `nlp` |
| Evidence Evaluation | `feature` (evidence objects) | `scoring` |
| Scoring | `score` | `scoring` |
| Market Intelligence | — (analysis over `signal` + `feature`) | `market-intelligence` |
| Competition Analysis | — (analysis over `signal` + `feature`) | `competition` |
| Execution Planning | — (synthesis over `score`) | `execution` |

Two observations worth recording:

- **Deduplication happens twice, in two contexts.** `acquisition` does exact
  (content-hash) dedup, which needs no semantics. `nlp` does near-duplicate,
  syndication and derivative detection, which does. `data-principles.md` §6
  requires both; they cannot live in the same context.
- **The last three manifest stages have no data-pipeline stage** because they are
  analysis, not transformation. They read the pipeline; they do not extend it.

---

## 4. Dependency matrix

Rows call columns. `→` = allowed. Blank = forbidden.

| from \ to | gateway | orchestr. | acquis. | nlp | scoring | market | compet. | execution | workers |
|-----------|---------|-----------|---------|-----|---------|--------|---------|-----------|---------|
| **apps/web** | → | | | | | | | | |
| **gateway** | | → | | | → | → | → | → | |
| **orchestrator** | | | | | → | | | | → |
| **acquisition** | | | | | | | | | |
| **nlp** | | | | | | | | | |
| **scoring** | | | | → | | → | → | | |
| **market-intel** | | | | → | | | | | |
| **competition** | | | | → | | → | | | |
| **execution** | | | | | → | → | → | | |
| **workers** | | → | → | → | → | → | → | → | |

### Invariants

1. **`apps/web` calls only `gateway`.** No app touches a datastore or another
   service.
2. **`acquisition` and `nlp` call nothing.** They are leaves. This is what makes
   them independently testable, independently deployable, and safe to extract
   first.
3. **`workers` calls everything; nothing calls `workers`.** Work is submitted to
   the queue, not to the worker service. This keeps the queue as the only
   scheduling authority.
4. **The graph is acyclic.** `workers → orchestrator` carries progress events
   only, never work requests — that is the one edge to watch, because turning it
   into a work request creates the cycle.
5. **`gateway` never calls `acquisition`, `nlp` or `workers`.** A user request
   cannot synchronously trigger collection; it starts a run, and the run is
   asynchronous. This is what prevents an HTTP request from being able to spend
   an unbounded amount of money.

---

## 5. Data ownership

A context owns its tables. Other contexts read through its interface, never
through its schema.

| Context | Owns | Tenant-scoped |
|---------|------|---------------|
| `acquisition` | `raw_record`, `normalized_record`, `collection_run` | Yes |
| `acquisition` | `source` registry and its legal-review records | **No — global** |
| `nlp` | `signal`, `classification`, `embedding_ref`, `cluster`, `independence_estimate` | Yes |
| `scoring` | `evidence`, `score`, `score_component` | Yes |
| `scoring` | `scoring_profile`, dimension registry | **No — global** |
| `market-intelligence` | `market_context`, `market_estimate`, `momentum` | Yes |
| `competition` | `competitor`, `competition_gap`, `positioning` | Yes |
| `execution` | `plan`, `risk_register`, `validation_plan` | Yes |
| `research-orchestrator` | `research_project`, `research_session`, `research_plan`, `research_jobs` + `research_job_dependencies` (the task ledger), `research_gap`, `session_budget_entries`, `research_completeness_records` | Yes |
| `scoring` / discovery | opportunity ↔ session observation records (shape is Mission 0.2's choice — Ontology V2 §12) | Yes |
| `gateway` | nothing persistent (cache only — keys workspace-prefixed) | n/a |
| `workers` | `job`, `job_attempt`, `dead_letter` | Yes |

Single PostgreSQL instance in Phase 1, with **schema-per-context**. One database
keeps operations simple; separate schemas keep ownership enforceable and make a
future split mechanical rather than archaeological.

**Tenancy (ADR-005).** Every tenant-scoped table carries `workspace_id NOT NULL`
from its first migration, and composite indexes lead with it. Reference data
(source registry, scoring profiles, model registry, framework versions) is global
and deliberately not tenant-scoped.

Note that the schema axis is used for **contexts**, not for tenants. Tenancy is a
column, not a schema — see ADR-005 §Alternatives for why schema-per-tenant was
rejected.

---

## 6. Cross-cutting contracts

Obligations that hold at **every** boundary, not just at some:

### Provenance propagation

No context may drop the source, timestamp, extraction method or confidence
attached to a value it processes. If a transformation loses provenance, the
transformation is wrong (`evidence-confidence-framework-v1.md` §10).

### Claim typing

Every analytical statement crossing a boundary carries its claim type:
`OBSERVED | INFERRED | PREDICTED | RECOMMENDED | HYPOTHESIS`. There is no untyped
claim. (`evidence-confidence-framework-v1.md` §8; note audit C-02 — the ontology
lists only four.)

### Version stamping

Every derived value carries the versions that produced it: framework version,
profile version, model version, prompt version, evidence snapshot time
(`scoring-framework-v1.1.md` §11, `llm-reasoning-rules.md` §9).

### Insufficiency is a value

Every context must be able to return "insufficient evidence" as a **successful**
response. A context that can only return an answer or an error will eventually
return a fabricated answer, because there is nowhere else for the uncertainty to
go. This is the structural version of the anti-hallucination rule.

### Contradiction preservation

No context discards evidence because it disagrees with other evidence
(`data-principles.md` §10). Contradiction is carried forward as a flag and
reduces Model Confidence downstream.

### Tenant scoping

**Added in 1.1 (ADR-005).** `workspace_id` accompanies every tenant-scoped
operation across every boundary: service call arguments, Celery task payloads,
repository queries, Redis cache keys, Qdrant search filters, and log lines.

It is never inferred, never defaulted in service code, never reconstructed from
another field. A missing `workspace_id` is an error in every environment,
including local development where a default workspace exists.

The two boundaries most easily forgotten are the ones that do not go through SQL:
**cache keys** and **vector search filters**. Both are enforced in their
respective client wrappers rather than at call sites.

**Added in 1.3 (ADR-012): the SQL boundary now has a second layer.** Every
tenant-scoped table carries a row-level-security policy, entered through a
transaction-local tenant context. The explicit repository filter is layer 1 and
stays mandatory; the policy is layer 2. They fail differently on purpose — a
forgotten `WHERE` is caught by the policy, and a missing tenant context returns
no rows rather than wrong ones — so a leak requires defeating both. Deleting
layer 1 because layer 2 exists is a regression, not a cleanup.

Two consequences for anyone crossing this boundary:

- Every tenant-scoped read runs inside a transaction, because the context is
  transaction-local. That is the price of a context that cannot outlive its
  work, and it is the property that stops a pooled connection carrying a tenant
  between users.
- A superuser bypasses the policy entirely. Administrative access, migrations
  and any psql session see every workspace, which is exactly why layer 1
  remains.

### LLM access

**Added in 1.1 (ADR-006).** No context imports a provider SDK. Every LLM call
goes through the LLM Gateway, requesting a logical tier
(`FAST_MODEL` / `BALANCED_MODEL` / `STRONG_MODEL` / `EMBEDDING_MODEL`), never a
provider or model name. The gateway is where budget enforcement, reproducibility
metadata, prompt versioning and structured-output validation happen — once,
rather than per call site.

### Correlation

`workspace_id`, `research_session_id` and `correlation_id` propagate through every
call and every Celery task payload. See `packages/observability`.

**Naming note.** Accepted ADRs (ADR-004, ADR-005, ADR-006) and historical reports
use `run_id`. That field is `research_session_id`. ADRs are append-only, so they
keep the older name; the mapping is stated once in Ontology V2 §11.5 and repeated
here so no reader has to infer it.

### Research lifecycle terminology

**Added in 1.2 (Ontology V2 §11).**

```text
Workspace → ResearchProject → ResearchSession → Evidence / Signals / Opportunities
                                    |
                                    +-- ResearchContext snapshot (immutable)
```

- `ResearchProject` — persistent, workspace-scoped research objective.
- `ResearchSession` — the **only** persisted execution entity.
- `ResearchContext` — an input specification (value object), snapshotted onto the
  session for reproducibility. Not an independent entity.
- `research run` — **retired**. Do not introduce a `ResearchRun` entity.

An `Opportunity` is not owned by the session that found it. Sessions produce
observations about opportunities, and the same opportunity may be rediscovered in
later sessions (Ontology V2 §12). Mission 0.2 chooses the relational form; the
requirement is that provenance can always name the session behind a conclusion.

---

## 7. What is deliberately not decided here

Updated in 1.1. Resolved items removed; what remains is genuinely open.

| Open | Blocks |
|------|--------|
| **D-03** — evidence aggregation formula | **`scoring` implementation — hard blocker** (`scoring-framework-v1.1.md` §13) |
| **D-08** — score recomputation policy | `scoring`, caching, UI |
| **D-11** — observability stack | `packages/observability` |
| **D-12** — embedding re-embedding strategy | `nlp`, Qdrant |
| **A-01** — sparse vs dense scoring-profile weight vectors | `scoring` storage shape |
| **A-12** — non-geographic (audience/segment) scoping vs `MarketScope` | Segment-level scores, if required (Ontology V2 §4.8) |
| — | Opportunity identity resolution: when two discoveries are the same opportunity (Ontology V2 §12.3) |

Resolved in Mission 0.1.1: C-01/D-02 (ADR-004), D-05 (ADR-005), C-02 and C-04
(domain V1.1), D-04 (ADR-006), D-10 (ADR-007), D-06
(`data-retention-policy-v1.md`), D-09 (CODEOWNERS).

Resolved in Mission 1.2: **A-13** (`opportunity-ontology-v2.1.md` §17,
`claim-model-v1.md`, ADR-015). The Claim is a persisted entity and evidence
references it. Ownership follows §1: `research.claims` and its revisions belong
to `research` because a Claim is a domain assertion, while
`scoring.evidence_independence_groups` belongs to `scoring` because it is part
of the evidence model. **Detecting** those provenance relationships is `nlp`'s
work and D-12 is open, so every group is currently written by hand.

Resolved in Mission 1.0: **D-07** (`source-registry-v1.md`, ADR-013). The
registry and its per-source review records exist. `acquisition` is still blocked,
but per source and for a stated reason rather than globally: no candidate has
passed the eligibility gate.

Resolved in Mission 0.1.2: D-01, A-06, A-11, A-05, A-07, A-08 (Ontology V2). See
`mission-0.1.2-decisions.md`.

Remaining items are recorded rather than guessed, per `docs/CLAUDE.md`
§Change control.

---

## 8. Import direction, and how it is kept acyclic (added in 1.3)

Phase 1 deploys `gateway` and `research-orchestrator` in the same process (§2),
which makes an accidental cycle cheap to write and invisible at runtime.

The edge `gateway → orchestrator` is allowed by §4 and is used: the gateway
imports `ALLOWED_TRANSITIONS` and `require_transition` from
`sros_orchestrator.lifecycle`, so there is one transition table rather than a
copy that drifts.

**The reverse edge does not exist, and is prevented structurally rather than by
review.** `sros_orchestrator` imports no database driver and no gateway module:
its repositories take any object exposing `tenant_transaction(workspace_id)`.
The concrete implementation is injected by whoever assembles the application.

That is what lets both contexts share a process today and split without a
rewrite tomorrow (§2 §What makes extraction cheap, rule 2: no context imports
another context's internals).
