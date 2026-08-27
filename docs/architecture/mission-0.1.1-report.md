# Mission 0.1.1 — Completion Report

Sprint: 0 (Foundation)
Mission: 0.1.1 — Architecture Decisions & Specification Reconciliation
Date: 2026-08-27
Status: Complete. Mission 0.2 not started.

---

## 1. Decisions applied

All eight decisions in the mission brief were applied in full. None was partially
applied, and none was reinterpreted.

| # | Decision | Applied as |
|---|----------|-----------|
| §3 | Remove BullMQ; Celery + Redis; Python workers; no Node worker tier | ADR-004; `PROJECT_MANIFEST.md` v1.1; every architecture document reconciled |
| §4 | Multi-tenant SaaS, workspace-centric, `workspace_id` propagation, no auth yet | ADR-005; `service-boundaries.md` §5–§6; contracts, testing and observability updated |
| §5 | Five-value UPPERCASE claim taxonomy with `HYPOTHESIS` first-class | `opportunity-ontology-v1.1.md` §7 |
| §6 | Confidence `[0,1]` internally, `[0,100]%` presented; score ≠ confidence ≠ probability ≠ evidence strength | `scoring-framework-v1.1.md` §4.1 |
| §7 | V1.1 specification versioning, V1 retained | Two new spec files, each with a §0 changelog; V1 files untouched |
| §8 | Authoritative chain repointed to V1.1 | `PROJECT_MANIFEST.md`, `docs/CLAUDE.md`, `docs/README.md`, root `README.md` |
| §9 | CODEOWNERS owner is `@Speekyx` | `CODEOWNERS`; syntax validated |
| §10 | Provider-agnostic LLM Gateway, logical tiers, cost ladder formalized | ADR-006 |
| §11 | Local-first + Docker Compose; production deferred | ADR-007 (created — §11 invited a decision record and one was warranted) |
| §12 | Data Retention Policy V1 | `docs/data/data-retention-policy-v1.md` |
| §13 | Evidence aggregation remains blocked | `scoring-framework-v1.1.md` §13 — recorded **normatively**, not as a note |

### Two judgment calls worth flagging

**ADR-007 was created rather than a lighter "documented decision record".** §11
allowed either. Deployment posture touches `infrastructure/`, CI, and the
portability constraints that every service must honour, so it needed the
alternatives-and-costs structure an ADR provides. Its most useful content is the
eight binding portability rules, which are what stop "local-first" from silently
becoming "local-only".

**The manifest was amended in place with a version bump, not forked into a new
file.** Domain specifications are name-versioned (`-v1.1.md`) because the brief
required it; the manifest is not name-versioned and never has been. It now
carries `Version: 1.1` plus a changelog table naming the authority for each
change. Git history plus that table give the traceability `docs/CLAUDE.md`
§Change control requires.

---

## 2. Files created (9 in-repo)

| File | Purpose |
|------|---------|
| `docs/domain/opportunity-ontology-v1.1.md` | Ontology V1.1 — claims taxonomy, confidence representation |
| `docs/domain/scoring-framework-v1.1.md` | Scoring V1.1 — numeric representation, evidence-aggregation blocker |
| `docs/architecture/adr/ADR-004-celery-redis-job-architecture.md` | Queue architecture — resolves C-01 |
| `docs/architecture/adr/ADR-005-workspace-multi-tenancy.md` | Tenancy — resolves D-05 |
| `docs/architecture/adr/ADR-006-provider-agnostic-llm-gateway.md` | LLM access — resolves D-04 |
| `docs/architecture/adr/ADR-007-local-first-docker-compose-deployment.md` | Deployment — resolves D-10 |
| `docs/data/data-retention-policy-v1.md` | Retention — resolves D-06 |
| `docs/architecture/mission-0.1.1-decisions.md` | Resolution register |
| `docs/architecture/mission-0.1.1-report.md` | This report |

## 3. Files modified (40)

### Authoritative specifications

| File | Change |
|------|--------|
| `PROJECT_MANIFEST.md` | → v1.1. Version history; BullMQ removed, Celery added; Product Shape section (multi-tenancy); authoritative chain → V1.1; superseded-specifications section; runtime boundaries |
| `docs/CLAUDE.md` | → v1.1. Boot sequence → V1.1; **§Canonical invariants** (taxonomy, confidence, tenancy, jobs, LLM, blocked work); versioning section updated |

### Architecture

`docs/architecture/service-boundaries.md` (→ v1.1), `specification-audit.md`
(§6 appendix only), `quality-gates.md` (→ v1.1), `testing-strategy.md` (→ v1.1),
`README.md`, `adr/README.md`, and all four diagrams
(`system-overview.md`, `service-communication.md`, `data-flow.md`,
`deployment-view.md`).

### Services (10)

`services/README.md`, `gateway`, `research-orchestrator`, `acquisition`, `nlp`,
`scoring`, `market-intelligence`, `competition`, `execution`, `workers`.

### Packages, apps, infrastructure, root

`packages/contracts`, `packages/ui`, `packages/observability`,
`apps/web`, `infrastructure/README.md`, `infrastructure/docker`,
`infrastructure/compose`, `infrastructure/scripts`,
`docs/README.md`, `docs/domain/README.md`, `docs/ai/README.md`,
`docs/data/README.md`, `README.md`, `CONTRIBUTING.md`, `CODEOWNERS`,
`pnpm-workspace.yaml`, `.github/workflows/ci.yml`,
`.github/workflows/security.yml`.

### Not modified, deliberately

- `docs/domain/opportunity-ontology-v1.md`, `docs/domain/scoring-framework-v1.md`
  — superseded, retained byte-identical.
- `docs/domain/evidence-confidence-framework-v1.md`, `docs/ai/llm-reasoning-rules.md`,
  `docs/data/data-principles.md` — no authorized change applied to them.
- `docs/architecture/mission-0.1-report.md` — completed historical report.
- `docs/architecture/adr/ADR-001`, `ADR-002`, `ADR-003` — accepted ADRs are
  append-only. They still cite V1 filenames; V1.1 preserved V1's section
  numbering, so those references remain semantically correct. Explained in
  `adr/README.md`.
- `specification-audit.md` §1–§5 — original findings preserved verbatim,
  including the C-01 recommendation that the owner ultimately did not take.

---

## 4. Architecture changes

### Queue and runtime — the big one

BullMQ is gone. The backend is entirely Python: FastAPI serving HTTP, Celery
consuming Redis queues, both importing the same context modules and differing
only in entrypoint. TypeScript is confined to `apps/web` and `packages/*`.

Five queues with independent worker pools and concurrency limits
(`acquisition`, `nlp`, `embedding`, `analysis`, `maintenance`), so slow
collection cannot starve fast analysis and per-source rate limiting becomes a
queue configuration rather than something each new collector must remember.

An incidental but real gain: `api` and `worker` would have been two codebases
under the Node-tier option. They are now one.

The cost accepted: at-least-once delivery, so **every job must be idempotent**,
forever. And Redis is now a broker holding in-flight job state, not just a
cache — AOF persistence and `acks_late` must be configured deliberately, including
locally, so job-loss behavior is observed in development rather than discovered
in production.

### Tenancy

`workspace_id` is now a cross-cutting contract alongside provenance, claim
typing, version stamping and correlation. It travels through service calls,
Celery payloads, repository queries, Redis cache keys, Qdrant filters and log
lines.

The two leak paths that get the most attention in the new documentation are the
ones that **never appear in a query review**: cache keys and vector-search
filters. Both are enforced in their client wrappers rather than at call sites.

Data ownership in `service-boundaries.md` §5 now marks each table tenant-scoped
or global. Reference data — source registry, scoring profiles, model registry —
is deliberately global.

### LLM access

A single chokepoint. `nlp` and `execution` reach providers only through the LLM
Gateway, requesting a logical tier. Budget enforcement, prompt versioning,
model-version recording and structured-output validation happen there once,
rather than per call site where each is one hurried commit from being skipped.

Budget refusal is a **first-class successful result**: a run that exhausts its
budget completes with lower Research Completeness rather than overspending.

### Deployment

Local-first Compose, production deferred, eight binding portability rules. The
deployment diagram gained a section explaining *why* production is blank, because
a blank production box invites someone to fill it in under pressure.

---

## 5. Specification changes

Both V1.1 documents inherit V1 in full, preserve section numbering, and open with
a §0 changelog naming every change and its authority.

**Ontology V1.1** — claims taxonomy expanded to five UPPERCASE values with
`HYPOTHESIS` first-class (§7); confidence representation stated (§9, new);
evolution section renumbered §8 → §10. Nothing else touched.

The reason `HYPOTHESIS` mattered: `evidence-confidence-framework-v1.md` §9 tells
the system to "classify it as a hypothesis" when evidence is insufficient. With a
four-value taxonomy there was nowhere for such a claim to go, leaving only
fabrication or silent omission. The fifth value is what makes the
anti-hallucination rule implementable rather than aspirational.

**Scoring V1.1** — confidence on `[0,1]` (§4, §4.1 new); the four-quantity
distinction (score / confidence / probability / evidence strength); score
semantics preserved on 0–100; claim typing of scores (§12, new); evidence
aggregation recorded as **not defined** with a normative blocker (§13, new).

One clarification worth calling out because it will otherwise cause a silent bug:
**`Model Confidence` is a score family on 0–100**, while the `confidence` field
on an evidence object or score component is on `[0,1]`. Same word, two
quantities, two ranges. The naming rule — `confidence` is always `[0,1]`,
`*_score` is always `0–100` — plus range validators in `packages/contracts` are
what keep them apart.

**No new scoring weights were invented. No evidence aggregation formula was
created.**

---

## 6. ADRs created

| ADR | Title | Resolves |
|-----|-------|----------|
| ADR-004 | Celery + Redis job architecture | C-01 / D-02 |
| ADR-005 | Workspace-centric multi-tenancy | D-05 |
| ADR-006 | Provider-agnostic LLM Gateway | D-04 |
| ADR-007 | Local-first Docker Compose deployment | D-10 |

Each carries Context, Decision, Alternatives (4–5 credible ones each, with why
they were rejected), Pros, Cons, Future impact with cost of reversal, and a
compliance section mapping onto specification sections.

ADR-004 records that the Mission 0.1 audit's own recommendation — keep BullMQ,
add a Node tier — was not taken, and why the owner's choice was better. That
correction is in the ADR and in the audit appendix; the original recommendation
stays in the audit as written.

---

## 7. Remaining unresolved issues

### Hard blocker

| ID | Item | Blocks |
|----|------|--------|
| **D-03 / A-02 / A-03 / A-04** | Evidence aggregation formula, recency decay parameters, independence thresholds, contradiction penalties | **`services/scoring` cannot be implemented.** Recorded normatively in `scoring-framework-v1.1.md` §13 |

### Open, non-blocking for Mission 0.2

| ID | Item |
|----|------|
| D-01 / A-06 | `ResearchContext` entity — ontology V2 |
| **A-11** | *New.* "research run" vs "Research Session" vs `ResearchContext` — three names for adjacent concepts |
| D-07 | Source registry and legal review records — blocks `acquisition` and the `retention_override` mechanism |
| D-08 | Score recomputation policy |
| D-11 | Observability stack |
| D-12 | Embedding re-embedding strategy |
| A-01 | Sparse vs dense scoring-profile weight vectors |
| A-05 | Geographic scope granularity |
| A-07 | Which ontology lists are closed enums |
| A-08 | `MONEY` vs `MONEY_MAKING` overlap |
| — | GDPR/jurisdiction analysis — **requires human or legal input** |
| — | Concrete LLM budget figures |
| — | Production deployment target |

### A-11 — the one new finding

The brief said to stop and report a **new contradiction**. A-11 is an
**ambiguity**, not a contradiction, so work continued and it is reported here.

ADR-005 introduces `Research Project` and `Research Session`.
`services/research-orchestrator` owns what it calls a **research run**.
`scoring-framework-v1.1.md` §2 refers to a **research context** (D-01). Nothing
defines whether a research run *is* a Research Session, or whether a session
contains many runs.

It blocks nothing today. It will produce two conflicting tables if it survives
until schema design. Recommendation, not applied: `ResearchSession` as the
persisted entity, `ResearchContext` as its input specification, "research run"
retired as informal usage — reconciled in ontology V2 with D-01.

### Two defects found and fixed during validation

Both pre-existed this mission and were found by the validation step, not by
review:

1. **`.github/workflows/ci.yml` and `security.yml` did not parse as YAML.**
   Eight `run: echo "Mission 0.2: ..."` lines were plain scalars containing
   `": "`, which YAML reads as a mapping indicator. Converted to literal block
   scalars. Both files now parse; had they been enabled as written, every run
   would have failed with a parse error.
2. **A stray `</content>` tag** at the end of `specification-audit.md`, a
   file-write artifact from Mission 0.1. Removed. Not a finding, not content.

---

## 8. Mission 0.2 entry criteria

### Satisfied

- [x] Queue and runtime decided — ADR-004
- [x] Multi-tenancy decided — ADR-005
- [x] Claims taxonomy canonical and consistent
- [x] Confidence representation canonical and consistent
- [x] LLM architecture provider-agnostic — ADR-006
- [x] Deployment posture decided — ADR-007
- [x] Retention policy defined — `data-retention-policy-v1.md`
- [x] CODEOWNERS resolved
- [x] Authoritative chain repointed to V1.1
- [x] Architecture documentation reconciled

### Ordered work for Mission 0.2

1. **`packages/contracts`** — highest priority. Enums and scales are settled;
   nothing blocks freezing them. Include `WorkspaceId`, `ClaimType`, `LlmTier`,
   and range validators for `confidence` / `*_score`.
2. **ADR-008 — storage architecture** — schema-per-context, `workspace_id NOT
   NULL` with composite indexes leading on it, Qdrant as derived index, migration
   tooling.
3. **Database schema v1** — provenance NOT NULL by default; `collected_at` and
   `expires_at` NOT NULL on every retention-governed table, `expires_at` computed
   at write time.
4. **Local Docker Compose** — pinned versions, health checks, Redis AOF, default
   development workspace seeded.
5. **Celery skeleton** — queues, routing, retry policy, Beat. No job bodies.
6. **LLM Gateway skeleton** — tier resolution, telemetry, budget hooks. No
   provider implementation.
7. **CI enablement** — `security.yml` first, then `ci.yml`.
8. **ESLint config** — boundary rules, provider-SDK restriction, local-enum
   restriction.

### Not entry criteria, but must precede specific work

| Before this | Do this |
|-------------|---------|
| `services/scoring` | `evidence-aggregation-framework-v1.md` (D-03) |
| `services/acquisition` | Source registry (D-07) |
| `services/research-orchestrator` contract | `ResearchContext` in ontology V2 (D-01, A-11) |
| Any production deployment | Production ADR; GDPR/jurisdiction analysis |

---

## 9. Updated repository tree

```
startup-research-os/                     107 entries
├── .editorconfig  .gitattributes  .gitignore  .npmrc  .nvmrc
├── CODEOWNERS                           @Speekyx (D-09 resolved)
├── CONTRIBUTING.md                      11 non-negotiables
├── PROJECT_MANIFEST.md                  v1.1
├── README.md                            canonical invariants
├── package.json  pnpm-workspace.yaml  turbo.json
│
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/{README.md, ci.yml, security.yml}     YAML now parses
│
├── apps/web/README.md
│
├── services/                            9 contexts, all Python
│   ├── README.md
│   ├── gateway/  research-orchestrator/  acquisition/  nlp/
│   ├── scoring/                         BLOCKED on D-03
│   ├── market-intelligence/  competition/  execution/
│   └── workers/                         Celery
│
├── packages/
│   ├── contracts/                       unblocked, highest priority
│   ├── ui/  eslint-config/  observability/
│   └── typescript-config/               base, library, nextjs
│
├── infrastructure/{README, docker/, compose/, scripts/}
│
└── docs/
    ├── README.md
    ├── CLAUDE.md                        v1.1 + Canonical invariants
    ├── domain/
    │   ├── opportunity-ontology-v1.1.md         CURRENT
    │   ├── scoring-framework-v1.1.md            CURRENT
    │   ├── evidence-confidence-framework-v1.md  CURRENT
    │   ├── opportunity-ontology-v1.md           superseded, retained
    │   └── scoring-framework-v1.md              superseded, retained
    ├── ai/{README.md, llm-reasoning-rules.md}
    ├── data/
    │   ├── data-principles.md
    │   └── data-retention-policy-v1.md          NEW
    └── architecture/
        ├── README.md
        ├── specification-audit.md               + §6 resolution appendix
        ├── service-boundaries.md                v1.1
        ├── quality-gates.md  testing-strategy.md   v1.1
        ├── mission-0.1-report.md                historical, unmodified
        ├── mission-0.1.1-decisions.md           NEW — resolution register
        ├── mission-0.1.1-report.md              NEW — this file
        ├── adr/  ADR-001 … ADR-007 + template + README
        └── diagrams/  4 files, 10 Mermaid diagrams
```

---

## 10. Validation results

| Check | Result |
|-------|--------|
| Boot sequence points to V1.1 in all four current entry points | **PASS** — manifest, `docs/CLAUDE.md`, `docs/README.md`, root `README.md` |
| No authoritative document presents V1 as current | **PASS** — only superseded-notices and historical documents reference V1 |
| V1 historical specs still exist | **PASS** — both present, byte-identical |
| BullMQ absent from current architecture | **PASS** — 5 remaining mentions, all explicit "removed in 1.1" statements or ADR-004 rationale; plus historical documents, untouched by design |
| Celery + Redis is the current queue architecture | **PASS** — 28 documents |
| Claim taxonomy = 5 UPPERCASE values everywhere current | **PASS** — no 4-value or title-case list outside the superseded V1 file and the audit finding that reported it |
| `confidence ∈ [0,1]` stated consistently | **PASS** — ontology V1.1 §9, scoring V1.1 §4.1, `docs/CLAUDE.md`, `packages/contracts` |
| JSON valid | **PASS** — 6/6 files |
| YAML valid | **PASS** — 3/3, **after fixing 8 broken `run:` lines** (see §7) |
| CODEOWNERS syntax and handle | **PASS** — 26 entries, every pattern has an owner, every owner is `@Speekyx` |
| Relative Markdown links | **PASS** — 48 checked, 0 broken |
| Backtick repo-path references | **PASS** — 1 intentional exception: `evidence-aggregation-framework-v1.md` does not exist **by design**; it is the named blocker |

---

## 11. Explicit answers

### Is C-01 resolved?

**Yes.** BullMQ is removed from the stack. All asynchronous work runs on Celery
over Redis, consumed by Python workers that import the ML stack in-process. There
is no Node worker tier. Recorded in ADR-004 and in `PROJECT_MANIFEST.md` v1.1,
with the alternatives and the accepted costs — chiefly at-least-once delivery
and the resulting per-job idempotency burden.

### Is multi-tenancy resolved?

**Yes, architecturally.** The tenant boundary is the Workspace; `workspace_id` is
required on every primary domain resource and propagates through every call,
task payload, cache key, vector filter and log line. RLS is designed for as
defence-in-depth, not as the primary mechanism.

Authentication and authorization remain unimplemented, deliberately. The measure
of whether ADR-005 did its job: adding authentication later should require **no
change to any tenant-scoped table**.

### Is claim taxonomy consistent?

**Yes.** Five canonical UPPERCASE values — `OBSERVED`, `INFERRED`, `PREDICTED`,
`RECOMMENDED`, `HYPOTHESIS` — identical in `opportunity-ontology-v1.1.md` §7 and
`evidence-confidence-framework-v1.md` §8, and stated in `docs/CLAUDE.md`
§Canonical invariants. Declared a closed enum. Verified: no four-value or
title-case list survives in any current document.

### Is confidence representation consistent?

**Yes.** `confidence`, `reliability`, `independence`, probability and signal
`value` are on `[0.0, 1.0]` in storage, contracts and ML, presented as
percentages. Scores keep 0–100. `evidence_level` stays integer 0–5.

The residual risk is named rather than hidden: `Model Confidence` is a *score
family* on 0–100, not a confidence field. Range validators in
`packages/contracts` plus the naming rule are the mitigation.

### Is the LLM architecture provider-agnostic?

**Yes.** All access goes through the LLM Gateway; no business service imports a
provider SDK; services request a logical tier, never a model name; model names
live in configuration. Routing, fallbacks, timeouts, retries, budget enforcement,
telemetry, prompt versioning and model-version tracking are specified in ADR-006.
Not implemented, by design.

### Is retention policy defined?

**Yes.** `data-retention-policy-v1.md`: raw 30 days, normalized and evidence 12
months maximum target, aggregates longer where lawful, scores versioned and
retained. Per-source `retention_override` with a recorded `basis`. Stricter
constraint always wins. Deletion semantics defined; deletion logic not
implemented.

Two open items are flagged rather than guessed: the GDPR/jurisdiction analysis
requires legal input, and backup-versus-deletion interaction is deferred to the
production ADR.

### Is Mission 0.2 now safe to begin?

**Yes, with one hard exclusion.**

Every blocker Mission 0.1 identified as gating Mission 0.2 is resolved. The
contracts package can be written, the schema can be designed, the Compose stack
and the Celery skeleton can be built.

**`services/scoring` must not be implemented.** Not "should be deprioritized" —
must not, until `docs/domain/evidence-aggregation-framework-v1.md` exists and is
authorized (`scoring-framework-v1.1.md` §13). Building it first means someone
picks the aggregation weights, the decay half-lives and the independence
thresholds. Those constants become load-bearing under every score in the system,
and they are unfalsifiable afterwards because nothing records that they were
guessed.

Two lesser sequencing constraints: `services/acquisition` needs the source
registry (D-07) before it collects anything, and the
`services/research-orchestrator` input contract needs `ResearchContext` (D-01,
A-11).

---

## 12. Mission boundary

**Mission 0.2 was not started.** Nothing in this mission created database
migrations, a production schema, collectors, NLP, embeddings, scoring, Celery
worker implementations, LLM provider implementations, authentication, dashboards
or GTM logic.

The only non-documentation changes were: the `CODEOWNERS` handle, a comment in
`pnpm-workspace.yaml`, and the YAML syntax repair in two CI workflow placeholders
that could not have run as written.
