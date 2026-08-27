# Specification Audit — Sprint 0 / Mission 0.1

Version: 1.0 (findings), + §6 resolution appendix added 2026-08-27
Status: Partially resolved — see §6 (Mission 0.1.1) and §7 (Mission 0.1.2)
Date: 2026-08-27
Scope: audit of the 7 authoritative documents listed in `PROJECT_MANIFEST.md`

> **The findings in §1–§5 below are the original Mission 0.1 audit and have not
> been rewritten.** Several were resolved by explicit human decision in Mission
> 0.1.1; §6 records what each one resolved to. A contradiction that was real and
> then resolved is more useful history than a document that reads as though it
> never existed.

---

## 0. Method

Documents audited, in boot-sequence order:

| # | Document | Version | Role |
|---|----------|---------|------|
| 1 | `PROJECT_MANIFEST.md` | 1.0 | Vision, stack, principles |
| 2 | `docs/CLAUDE.md` | unversioned | Operating contract |
| 3 | `docs/domain/opportunity-ontology-v1.md` | V1 | Domain vocabulary |
| 4 | `docs/domain/scoring-framework-v1.md` | V1 | Ranking model |
| 5 | `docs/domain/evidence-confidence-framework-v1.md` | V1 | Evidence model |
| 6 | `docs/ai/llm-reasoning-rules.md` | V1 | LLM discipline |
| 7 | `docs/data/data-principles.md` | V1 | Data governance |

No specification was modified. This document only records findings.

Severity scale used below:

- **BLOCKING** — cannot be resolved by an implementer without a human decision; will produce incompatible code if guessed.
- **MAJOR** — resolvable by an ADR, but the wrong guess is expensive to reverse.
- **MINOR** — editorial or low-cost to fix later.

---

## 1. Contradictions

### C-01 — BLOCKING — BullMQ (Node) vs Python workers

**Where:** `PROJECT_MANIFEST.md` §Technology Stack — `Backend: FastAPI, Python` and `Data: Playwright, BullMQ`.

**Problem:** BullMQ is a Node/TypeScript library built on a Redis data layout that has no supported, stable Python client. The manifest simultaneously requires:

- a Python backend (FastAPI),
- an NLP/ML stack that is Python-only (BGE-M3, HDBSCAN),
- BullMQ as the queue.

A Python worker cannot natively consume a BullMQ queue. The three viable resolutions are mutually exclusive and have very different architectural consequences:

1. **Node worker tier** — BullMQ workers in TypeScript that orchestrate Playwright acquisition, and call Python services over HTTP for NLP/scoring. Queue stays BullMQ. Adds a network hop on every ML task.
2. **Python queue** — replace BullMQ with Celery/RQ/arq. Contradicts the locked stack.
3. **Dual queue** — BullMQ for acquisition/browser jobs, a Python queue for ML jobs, bridged by an event contract. Highest operational cost, two dashboards, two retry semantics.

**Impact:** determines the language of the `workers` service, the deployment topology, and whether `nlp` and `scoring` are HTTP services or in-process libraries.

**Recommendation:** option 1 (Node/BullMQ orchestration tier + Python compute services over HTTP). It preserves the locked stack, keeps a single queue and a single retry semantics, and keeps Python confined to what only Python can do. **Requires human confirmation — see ADR-004 (deferred to Mission 0.2).**

---

### C-02 — MAJOR — Claims taxonomy has two incompatible definitions

**Where:**

- `opportunity-ontology-v1.md` §7 — four categories: `Observed`, `Inferred`, `Predicted`, `Recommended`.
- `evidence-confidence-framework-v1.md` §8 — five categories: `OBSERVED`, `INFERRED`, `PREDICTED`, `RECOMMENDED`, `HYPOTHESIS`.

**Problem:** the ontology says these categories "must not be conflated in user-facing output" but omits `HYPOTHESIS`, which the evidence framework treats as a first-class claim type and which `§9 Anti-hallucination rule` depends on ("classify it as a hypothesis"). Casing also differs (`Observed` vs `OBSERVED`), which matters because both will become a persisted enum.

**Impact:** a database enum, an API contract, and a UI label set. Getting it wrong means a migration.

**Recommendation:** treat the evidence framework's 5-value UPPERCASE set as normative, and issue an ontology V1.1 erratum (or V2) aligning §7. The ontology's own §8 forbids silently adding a fundamental category, so this must be an explicit, traceable edit — not an implementer's assumption.

---

### C-03 — MAJOR — "Avoid premature microservices" vs a 9-service decomposition

**Where:**

- `docs/CLAUDE.md` §Core principles — "Avoid unnecessary complexity and premature microservices."
- Mission 0.1 Task 3 — requires `gateway`, `research-orchestrator`, `acquisition`, `nlp`, `scoring`, `market-intelligence`, `competition`, `execution`, `workers`.
- `PROJECT_MANIFEST.md` §Engineering Principles — "Every service must have a single responsibility."

**Problem:** the mission asks for nine services. The operating contract forbids premature microservices. Both are authoritative. A literal reading produces nine independently deployed processes for a project with zero users, which contradicts CLAUDE.md; ignoring the task contradicts the mission.

**Resolution applied in this mission (documented, not silent):** service boundaries are defined as **logical bounded contexts with hard module boundaries and explicit contracts**, deployed initially as a **small number of processes** (see `service-boundaries.md` §2, Deployment Topology). The boundary is the contract; the process count is a deployment decision that can change without changing the contract.

**Impact:** none if the contracts are respected. This is the standard "modular monolith first, extract later" position and satisfies both documents.

---

### C-04 — MAJOR — Numeric scale inconsistency (0–100 vs 0–1 vs 0–5)

**Where:**

- `scoring-framework-v1.md` §4 — "Dimension scores are normalized to 0–100."
- `evidence-confidence-framework-v1.md` §6 — evidence object uses `value: 0.87`, `independence: 0.91`, `reliability: 0.75`, `confidence: 0.82` (0–1 floats).
- `scoring-framework-v1.md` §7 — `Model Confidence: 74` (0–100).

**Problem:** `confidence` exists in both frameworks with different ranges. The same field name carries two scales depending on which document you read. `evidence_level` is a third scale (integer 0–5).

**Impact:** silent numeric bugs (a 0.82 confidence rendered as 82% in one place and 0.82% in another), and a wrong column type.

**Recommendation:** adopt one rule and state it in a shared contract package:

- **storage** — all unit-interval quantities stored as `float [0,1]` (`confidence`, `reliability`, `independence`, `value`),
- **presentation** — scores and confidences displayed as integers 0–100,
- **`evidence_level`** — integer 0–5, never rescaled.

Requires an explicit erratum in the scoring framework, since §4 currently mandates 0–100 at the dimension level.

---

### C-05 — MINOR — Two different pipeline vocabularies

**Where:**

- `PROJECT_MANIFEST.md` §Mission — `Raw Signals → Data Collection → Normalization → NLP → Signal Extraction → Opportunity Discovery → Evidence Evaluation → Scoring → Market Intelligence → Competition Analysis → Execution Planning` (11 stages, service-shaped).
- `data-principles.md` §4 — `raw → normalized → deduplicated → enriched → signal → feature → score` (7 stages, data-shaped).

**Problem:** neither document maps to the other. `deduplicated`, `enriched` and `feature` have no counterpart in the manifest; `Opportunity Discovery`, `Market Intelligence`, `Competition Analysis`, `Execution Planning` have no counterpart in the data pipeline.

**Impact:** low, but it will produce inconsistent table and stage naming if left implicit.

**Recommendation:** treat the manifest pipeline as the **service/orchestration** view and the data-principles pipeline as the **record lifecycle** view, and publish the mapping. A first mapping is proposed in `service-boundaries.md` §3.

---

### C-06 — MINOR — "Security cannot be postponed" vs "do not implement authentication"

**Where:** `PROJECT_MANIFEST.md` §Engineering Principles (`Security First`) vs §Forbidden During Foundation (`authentication features`) and Mission 0.1's forbidden list.

**Problem:** read literally, the foundation must be secure but may not implement any authentication.

**Resolution applied:** "authentication features" is read as *user-facing* auth (signup, login, sessions, roles, billing identity). Baseline security hygiene is **not** postponed and is delivered in this mission as: secret exclusion (`.gitignore`), no credentials in source, a documented secret-handling rule (`CONTRIBUTING.md`), and a placeholder secret-scanning gate in CI. No conflict remains under this reading.

---

## 2. Ambiguities

### A-01 — Scoring profile weight vectors have a variable dimension set

`scoring-framework-v1.md` §3 lists 12 candidate dimensions, then adds "Education-oriented profiles may also explicitly score Learning Value" — a 13th dimension available only to some profiles. §6 requires that weights "sum to 100% for each scoring profile."

Unresolved: does a profile weight every dimension (with zeros), or only its own subset? These produce different storage shapes (dense vector vs sparse map) and different comparability guarantees between profiles.

**Recommendation:** sparse map (`dimension → weight`), validated to sum to 1.0, with the dimension registry versioned separately from the profile. Preserves the ability to add dimensions without rewriting every profile.

### A-02 — "Evidence Score" is named but never defined

§2 of the scoring framework defines the *purpose* of the Evidence Score ("how strong and sufficiently diverse the supporting evidence is") and §7 shows an example value of 61. No aggregation function is specified. The evidence framework §11 lists six aggregation inputs (reliability, independence, recency, relevance, evidence level, contradiction) but no formula, no weights, and no decay function.

**Recommendation:** define `evidence-aggregation-v1.md` in Sprint 1 before any scoring code exists. Flagged as missing decision D-03.

### A-03 — Recency decay is required but unparameterized

`evidence-confidence-framework-v1.md` §5 requires domain-dependent decay ("fast-moving social trends: rapid decay") without half-lives, a decay family (exponential? step?), or a domain taxonomy to attach them to.

**Recommendation:** a versioned `decay-profiles` registry keyed by source family, with explicit half-lives. Human input needed on the initial priors.

### A-04 — "Sufficiently independent sources" is undefined at Level 3

Evidence Level 3 requires sources "sufficiently independent". §4 lists detectable duplication classes but no threshold. `independence: 0.91` in the example object implies a continuous estimate; Level 3 implies a boolean gate.

**Recommendation:** define the gate as a function of the continuous estimate (e.g. `n_sources >= 3 AND min_pairwise_independence >= t`), with `t` versioned. Needs a decision.

### A-05 — Geographic scope granularity is open

Ontology §4 allows "global, regional, country-level, or segment-level" analysis, and scoring §9 shows per-country scores. Unresolved: is a score row keyed by an ISO-3166 country code, an arbitrary region string, or a free-form segment? This determines the primary key of the score table and whether scores are comparable across rows.

**Recommendation:** typed `MarketScope` discriminated union (`global | region | country | segment`), with `country` constrained to ISO-3166-1 alpha-2.

### A-06 — "Research context" is referenced but never modeled

Scoring §2 defines the Opportunity Score as attractiveness "given the selected research context", and §9 says scores are "calculated for the selected market context". `Research Completeness` measures coverage of "the relevant research space". Neither the research context nor the research space is defined as an entity anywhere in the ontology.

**Impact:** this is the input contract of the `research-orchestrator`. It cannot be designed beyond its boundary until modeled.

**Recommendation:** add a `ResearchContext` entity to ontology V2 (market scope, profile, time window, source families, depth/budget). Flagged as missing decision D-01.

### A-07 — Ontology §3 lists are "examples", not closed enums

Every §3 sub-list is introduced with "Examples:". §8 then forbids silently adding "a new fundamental category". It is unclear which lists are closed enums (persisted, migration-bearing) and which are open vocabularies (extensible at runtime).

**Recommendation:** declare `user_motivation`, `claim_type` and `evidence_level` as **closed** (V1 change requires a version bump), and `product_type`, `distribution_channel`, `retention_mechanism`, `monetization_model` as **open registries** with a curated seed list. Needs confirmation.

### A-08 — `MONEY` motivation overlaps `MONEY_MAKING` / `MONEY_SAVING` value propositions

Ontology §3.3 vs §3.5. Motivation and value proposition are different axes, but a classifier will confuse them without a disambiguation rule.

**Recommendation:** documentation-level fix — motivation describes *why the user acts*, value proposition describes *what the product delivers*. Add examples to the ontology.

### A-09 — Vector store role vs PostgreSQL role is unstated

Qdrant and PostgreSQL are both mandated. Which system owns the canonical embedding, whether Qdrant is a derived index (rebuildable) or a primary store, and what happens on divergence are unspecified. `pgvector` is not mentioned either way.

**Recommendation:** Qdrant as a **derived, rebuildable index**; PostgreSQL as the system of record for everything including embedding provenance. Makes Qdrant loss non-fatal. Needs an ADR in Mission 0.2.

### A-10 — "Where technically possible" weakens the provenance requirement

`docs/CLAUDE.md` §Evidence discipline and `evidence-confidence-framework-v1.md` §10 both qualify provenance retention with "where technically possible" / "where lawful and appropriate". As written this is unenforceable — an implementer can always claim infeasibility.

**Recommendation:** invert it. Provenance fields are **NOT NULL by default**; any exemption must be an explicit, enumerated, documented case in the source registry. Cheap now, very expensive to retrofit.

---

## 3. Missing decisions

These are absent from all seven documents and block later sprints. Each needs a human decision or an ADR.

| ID | Missing decision | Blocks | Suggested owner |
|----|------------------|--------|-----------------|
| D-01 | `ResearchContext` entity — what a research run takes as input | `research-orchestrator` API | Domain (ontology V2) |
| D-02 | Queue/runtime split (see C-01) | `workers`, deployment topology | Architecture (ADR-004) |
| D-03 | Evidence aggregation formula | `scoring`, Evidence Score | Domain (new spec) |
| D-04 | LLM provider, model tiers, and cost budget per research run | `nlp`, `scoring`, all LLM call sites | Architecture + product |
| D-05 | Multi-tenancy model (single-user tool vs multi-tenant SaaS) | every table's primary key, row-level security | Product — **decide before the first migration** |
| D-06 | Data retention & deletion policy (raw content, PII, right-to-erasure) | storage schema, legal | Legal + architecture |
| D-07 | Source registry format and the §13 legal review record | `acquisition` | Data engineering |
| D-08 | Score recomputation policy — are scores immutable snapshots or recomputed on new evidence? | `scoring`, caching, UI | Domain |
| D-09 | Identity of `Owner: Speekyx` as a GitHub handle/team | `CODEOWNERS` | Human |
| D-10 | Environment topology (local / staging / production) and hosting target | `infrastructure`, CI | Architecture |
| D-11 | Observability stack (logs, traces, metrics) | every service | Architecture |
| D-12 | Embedding model versioning & re-embedding strategy on model change | `nlp`, Qdrant | ML |

**D-05 is the most urgent.** Adding a tenant boundary after the first production data exists is one of the most expensive migrations in this class of system, and nothing in the manifest states whether this is a personal research tool or a multi-tenant product.

---

## 4. Recommendations (ordered)

1. **Resolve C-01 before Mission 0.2.** No service can be scaffolded until the queue/runtime split is decided; it determines the language of half the codebase.
2. **Answer D-05 (multi-tenancy) before any database migration is written.**
3. **Publish a shared contracts package as the single source of enums and scales** (`packages/contracts`), generated once and consumed by both TypeScript and Python. This is the only durable fix for C-02 and C-04 — prose in two documents will drift, a generated type will not.
4. **Issue an ontology V1.1 erratum** covering C-02 (claims taxonomy) and A-08 (motivation vs value proposition), and a scoring V1.1 erratum covering C-04 (scales). Per `docs/CLAUDE.md` §Change control these must be explicit versioned edits, not implementer assumptions.
5. **Make provenance fields non-nullable by default** (A-10) in the first schema, with an explicit exemption list.
6. **Write `evidence-aggregation-v1.md` before `scoring` implementation** (A-02, A-03, A-04). Scoring without a defined evidence aggregation would produce exactly the false precision the framework §10 forbids.
7. **Do not collapse the five score families into one number anywhere** — not in the API, not in a sort key, not in a UI badge. Scoring §2 forbids it and a single sortable number is the most likely accidental violation in the whole system.
8. **Version the documents that lack versions.** `docs/CLAUDE.md` is authoritative but unversioned, which breaks the manifest's own "Version Everything" principle.

---

## 5. What this audit did not do

- It did not modify any specification.
- It did not resolve C-01, C-02 or C-04 — those are recorded as requiring human authorization per `docs/CLAUDE.md` §Change control.
- It did not audit for legal compliance of any specific data source (out of scope until the source registry exists, D-07).

---

# 6. Resolution appendix — Mission 0.1.1

**Added 2026-08-27.** Nothing in §1–§5 was rewritten. This appendix records the
status of each finding after the human decisions taken in Mission 0.1.1.

Full register with governing documents: `mission-0.1.1-decisions.md`.

## 6.1 Contradictions

| ID | Original finding | Status | Resolution |
|----|------------------|--------|-----------|
| **C-01** | BLOCKING — BullMQ (Node) vs Python workers | **RESOLVED** | BullMQ removed from the stack. Celery + Redis, all-Python backend, no Node worker tier. **ADR-004**, `PROJECT_MANIFEST.md` v1.1 |
| **C-02** | Claims taxonomy defined twice, incompatibly | **RESOLVED** | Five canonical UPPERCASE values including `HYPOTHESIS`. `opportunity-ontology-v1.1.md` §7, identical to `evidence-confidence-framework-v1.md` §8 |
| **C-03** | "Avoid premature microservices" vs nine services | **RESOLVED (Mission 0.1)** | Boundary is a contract, process count is a deployment choice. `service-boundaries.md` §2. Unchanged by 0.1.1 |
| **C-04** | Numeric scale inconsistency (0–100 vs 0–1 vs 0–5) | **RESOLVED** | `confidence` and kin on `[0,1]`; scores on `0–100`; `evidence_level` integer `0–5`. `scoring-framework-v1.1.md` §4.1 |
| **C-05** | Two pipeline vocabularies | **RESOLVED (Mission 0.1)** | Mapping published in `service-boundaries.md` §3 |
| **C-06** | "Security first" vs "no authentication" | **RESOLVED (Mission 0.1)** | Read as *user-facing auth* deferred, baseline hygiene delivered. Reinforced by ADR-005: tenancy contracts exist so auth can be added without a data migration |

### A note on the C-01 recommendation

§1 recommended **option 1** — keeping BullMQ and adding a Node orchestration
tier. The owner chose **option 2**, amending the locked stack instead. That was
the better call, and the audit's recommendation weighted "the manifest says so"
too heavily against the engineering cost of a permanent two-language backend with
split failure semantics. ADR-004 §Alternatives records the full reasoning.

The recommendation is left in §1 as written. An audit that quietly revises its
own advice after the fact is less trustworthy, not more.

## 6.2 Ambiguities

| ID | Status | Note |
|----|--------|------|
| **A-01** — sparse vs dense profile weight vectors | **OPEN** | `scoring-framework-v1.1.md` §6 records it as open. Sparse map still recommended |
| **A-02** — Evidence Score undefined | **OPEN — hard blocker** | `scoring-framework-v1.1.md` §13. `services/scoring` must not be implemented until the aggregation framework exists |
| **A-03** — recency decay unparameterized | **OPEN — hard blocker** | Same |
| **A-04** — independence threshold undefined | **OPEN — hard blocker** | Same |
| **A-05** — geographic scope granularity | **OPEN** | `MarketScope` discriminated union recommended; to be fixed in `packages/contracts` |
| **A-06** — `ResearchContext` unmodeled | **OPEN** | Scheduled for ontology V2 (D-01). Deliberately not added in V1.1 — §7 authorized only the taxonomy and scale corrections |
| **A-07** — closed enums vs open registries | **OPEN** | `ClaimType` is now explicitly closed (`opportunity-ontology-v1.1.md` §7). The rest remain undeclared |
| **A-08** — `MONEY` vs `MONEY_MAKING` overlap | **OPEN** | Documentation-level fix, deferred. Mission 0.1.1 §7 restricted V1.1 to authorized changes only |
| **A-09** — Qdrant role | **RESOLVED (Mission 0.1)** | Derived, rebuildable index. Reinforced by the retention policy: deletion must propagate to Qdrant |
| **A-10** — "where technically possible" weakens provenance | **RESOLVED in principle** | Provenance fields NOT NULL by default; `data-retention-policy-v1.md` §4 defines the one lawful exception and requires it to be recorded as an explicit gap marker |
| **A-11** — *new* | **OPEN** | See §6.4 |

## 6.3 Missing decisions

| ID | Status | Governing document |
|----|--------|-------------------|
| **D-01** — `ResearchContext` entity | OPEN | Ontology V2 |
| **D-02** — queue/runtime split | **RESOLVED** | ADR-004 |
| **D-03** — evidence aggregation formula | **OPEN — hard blocker** | `scoring-framework-v1.1.md` §13 |
| **D-04** — LLM provider, tiers, budget | **RESOLVED (architecture)** | ADR-006. Concrete budget figures remain a Mission 0.2 configuration decision |
| **D-05** — multi-tenancy | **RESOLVED** | ADR-005 |
| **D-06** — retention & deletion | **RESOLVED** | `data-retention-policy-v1.md` |
| **D-07** — source registry | OPEN | Blocks `acquisition`, and blocks the `retention_override` the retention policy depends on |
| **D-08** — score recomputation policy | OPEN | — |
| **D-09** — CODEOWNERS identity | **RESOLVED** | `@Speekyx` |
| **D-10** — environment topology | **RESOLVED (foundation)** | ADR-007: local-first Compose. Production deferred to a future ADR |
| **D-11** — observability stack | OPEN | `packages/observability` conventions are fixed regardless |
| **D-12** — embedding re-embedding strategy | OPEN | Made tractable by ADR-006 model-version tracking |

**§3's "D-05 is the most urgent" assessment held.** It was answered before any
migration was written, which is the outcome that mattered.

## 6.4 New findings opened in Mission 0.1.1

### A-11 — Three names for adjacent concepts

**Where:** ADR-005 defines the hierarchy
`User → Workspace → Research Project → Research Session → Opportunity`.
`services/research-orchestrator` owns what it calls a **research run**.
`scoring-framework-v1.1.md` §2 refers to a **research context**, tracked as D-01.

**Problem:** "Research Session", "research run" and `ResearchContext` are three
names for concepts that are adjacent and possibly identical. Nothing defines
whether a research run *is* a Research Session, or whether a session contains
many runs.

**Severity:** ambiguity, not contradiction. It does not block Mission 0.1.1
documentation work, but it will produce two conflicting tables if left implicit
until schema design.

**Recommendation:** reconcile in ontology V2, together with D-01. The likely
shape is `ResearchSession` as the persisted entity and `ResearchContext` as its
input specification, with "research run" retired as informal usage — but that is
a decision, not an assumption, and it is not made here.

### Documentation defect corrected

A stray `</content>` tag at the end of this file, left by the Mission 0.1 file
write, was removed. It was an artifact, not a finding.

## 6.5 What this appendix did not do

- It did not rewrite, soften or delete any original finding.
- It did not resolve A-01, A-02, A-03, A-04, A-05, A-06, A-07, A-08 or A-11.
- It did not invent an evidence aggregation formula, decay parameter,
  independence threshold or contradiction penalty. Those remain the single
  hardest blocker in the project, and guessing them is explicitly forbidden.

---

# 7. Resolution appendix — Mission 0.1.2

**Added 2026-08-27.** Nothing in §1–§6 was rewritten. This appendix records the
status of the remaining findings after the domain decisions taken in Mission
0.1.2 and published as **Opportunity Ontology V2**.

Full register: `mission-0.1.2-decisions.md`.

## 7.1 Findings resolved

| ID | Original finding | Resolution |
|----|------------------|-----------|
| **D-01** | `ResearchContext` entity — what an execution takes as input | Defined as an **input value object**, not an entity, snapshotted immutably onto a `ResearchSession`. Ontology V2 §11.3 |
| **A-06** | `ResearchContext` referenced but unmodeled | Same. §6.2 recorded this as "deliberately not added in V1.1"; V2 was the authorized place |
| **A-11** | Three names for adjacent concepts (opened in §6.4) | `ResearchSession` is canonical; `ResearchProject` groups; `ResearchContext` is the input snapshot; `research run` retired with no `ResearchRun` entity. Ontology V2 §11 |
| **A-05** | Geographic scope granularity | `MarketScope` closed union: `GLOBAL \| REGION \| COUNTRY \| MULTI_COUNTRY`, ISO 3166-1 alpha-2, region registry. Ontology V2 §4 |
| **A-07** | Closed enums vs open registries | Explicit split with the reasoning stated: taxonomies that must grow are registries, so a new product category never needs a migration. Ontology V2 §14 |
| **A-08** | `MONEY` vs `MONEY_MAKING` overlap | Two axes, not duplicates: motivation is about the user, value proposition is about the product. Ontology V2 §13 |

### A note on the A-05 recommendation

§2 recommended a `global \| region \| country \| segment` union. The authorized
`MarketScope` replaces `segment` with `MULTI_COUNTRY`.

That is a better geographic model — `MULTI_COUNTRY` expresses an aggregate across
named markets, which the original four could not — but it leaves segment scoping
without a home. That gap is opened as **A-12** rather than papered over. The §2
recommendation stays as written.

## 7.2 Still open after Mission 0.1.2

| ID | Status |
|----|--------|
| **D-03 / A-02 / A-03 / A-04** | **OPEN — hard blocker.** Evidence aggregation, decay, independence thresholds, contradiction penalties. `services/scoring` remains unimplementable |
| **A-01** | OPEN — sparse vs dense scoring-profile weight vectors |
| **A-12** | OPEN — *new*, see §7.3 |
| **D-07** | OPEN — source registry |
| **D-08** | OPEN — score recomputation policy. Sharpened by Ontology V2 §12: an opportunity now accumulates evidence across sessions |
| **D-11** | OPEN — observability stack |
| **D-12** | OPEN — embedding re-embedding strategy |
| — | OPEN — opportunity identity resolution (Ontology V2 §12.3) |

## 7.3 New finding opened in Mission 0.1.2

### A-12 — Non-geographic (segment) scope has no representation

**Where:** V1 and V1.1 §4 allowed analysis to be "global, regional, country-level,
or **segment-level**". The authorized `MarketScope` (V2 §4.1) has no segment type.

**Problem:** audience/segment scoping is unrepresented. It is either intentionally
out of scope or belongs on a second axis that nothing defines.

**How it was handled:** V2 §4.8 states that `MarketScope` covers the geographic
axis only, and that segment scoping is a separate axis deliberately not folded
into it — a `COUNTRY_AND_SEGMENT` variant being the shape the alternative would
eventually force.

**Severity:** ambiguity. Blocks nothing in Mission 0.2 provided schema design
treats scope as geographic. Expensive only if segment-level scores are required
after score rows exist.

**Not resolved.** Recorded for a future decision.

## 7.4 What this appendix did not do

- It did not rewrite, soften or delete any finding in §1–§6.
- It did not resolve D-03, A-01, A-12, D-07, D-08, D-11 or D-12.
- It did not invent an evidence aggregation formula, decay parameter,
  independence threshold or contradiction penalty.
