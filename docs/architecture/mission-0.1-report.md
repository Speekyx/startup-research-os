# Mission 0.1 — Completion Report

Sprint: 0 (Foundation)
Mission: 0.1 — Architectural foundation
Date: 2026-08-27
Status: Complete. **Do not proceed to Mission 0.2 until §6 is answered.**

---

## 1. Repository tree

```
startup-research-os/
├── .editorconfig
├── .gitattributes
├── .gitignore
├── .npmrc
├── .nvmrc
├── CODEOWNERS
├── CONTRIBUTING.md
├── PROJECT_MANIFEST.md            (pre-existing, unmodified)
├── README.md
├── package.json
├── pnpm-workspace.yaml
├── turbo.json
│
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/
│       ├── README.md
│       ├── ci.yml                 (workflow_dispatch only)
│       └── security.yml           (workflow_dispatch only)
│
├── apps/
│   ├── README.md
│   └── web/README.md
│
├── services/
│   ├── README.md
│   ├── gateway/README.md
│   ├── research-orchestrator/README.md
│   ├── acquisition/README.md
│   ├── nlp/README.md
│   ├── scoring/README.md
│   ├── market-intelligence/README.md
│   ├── competition/README.md
│   ├── execution/README.md
│   └── workers/README.md
│
├── packages/
│   ├── README.md
│   ├── contracts/README.md
│   ├── ui/README.md
│   ├── eslint-config/README.md
│   ├── observability/README.md
│   └── typescript-config/
│       ├── README.md
│       ├── package.json
│       ├── base.json
│       ├── library.json
│       └── nextjs.json
│
├── infrastructure/
│   ├── README.md
│   ├── docker/README.md
│   ├── compose/README.md
│   └── scripts/README.md
│
└── docs/
    ├── README.md
    ├── CLAUDE.md                  (pre-existing, unmodified)
    ├── domain/                    (pre-existing specs, unmodified)
    │   ├── README.md
    │   ├── opportunity-ontology-v1.md
    │   ├── scoring-framework-v1.md
    │   └── evidence-confidence-framework-v1.md
    ├── ai/
    │   ├── README.md
    │   └── llm-reasoning-rules.md
    ├── data/
    │   ├── README.md
    │   └── data-principles.md
    └── architecture/
        ├── README.md
        ├── specification-audit.md
        ├── service-boundaries.md
        ├── quality-gates.md
        ├── testing-strategy.md
        ├── mission-0.1-report.md
        ├── adr/
        │   ├── README.md
        │   ├── ADR-TEMPLATE.md
        │   ├── ADR-001-turborepo-monorepo.md
        │   ├── ADR-002-nextjs-frontend.md
        │   └── ADR-003-fastapi-backend.md
        └── diagrams/
            ├── README.md
            ├── system-overview.md
            ├── service-communication.md
            ├── data-flow.md
            └── deployment-view.md
```

**No authoritative specification was modified.** The seven documents listed in
`PROJECT_MANIFEST.md` §Authoritative Documents are byte-identical to how they
were found. Recommended changes to them are recorded in the audit, not applied.

---

## 2. Completed tasks

### Task 1 — Specification audit ✅

`docs/architecture/specification-audit.md`.

Audited all seven documents. Found:

- **6 contradictions** (1 blocking, 3 major, 2 minor)
- **10 ambiguities**
- **12 missing decisions**

The blocking one is **C-01**: BullMQ is a Node library with no supported Python
client, while the backend, the queue consumers and the entire ML stack
(BGE-M3, HDBSCAN) are Python. The manifest requires both. This is not resolvable
by an implementer.

Two other contradictions matter more than their severity suggests, because both
are the *same* structural failure — a domain concept defined twice, in two
documents, with different values:

- **C-02** — the claims taxonomy has 4 categories in the ontology and 5 in the
  evidence framework.
- **C-04** — `confidence` is 0–100 in the scoring framework and 0–1 in the
  evidence framework.

Both become a database enum and an API contract. Guessing either produces a
migration.

### Task 2 — Monorepo ✅

Turborepo + pnpm workspace. `apps/`, `services/`, `packages/`, `infrastructure/`,
`docs/`, `.github/`. **Every directory has a README describing its future
responsibility** — 30 READMEs total, each stating boundaries and what does *not*
belong there.

Root config: `package.json` (pinned `packageManager`, `engines`), `turbo.json`
(task graph with correct cache semantics), `pnpm-workspace.yaml`, `.npmrc`
(strict install), `.nvmrc`. All JSON validated as parseable.

`packages/typescript-config` is scaffolded with real configuration (JSON only, no
dependencies) so the workspace is not empty.

### Task 3 — Service boundaries ✅

`docs/architecture/service-boundaries.md` plus nine service READMEs.

Each of the nine contexts documents: responsibility, inputs, outputs,
dependencies, future API surface, hard constraints traced to specification
sections, and a **failure-mode table**. Those tables are not decoration — the
testing strategy names them as the required test list.

The cross-cutting document adds: deployment topology, the pipeline mapping that
resolves C-05, a full dependency matrix with invariants, data ownership per
context, and the cross-cutting contracts that hold at every boundary.

**Design position recorded (C-03):** the mission requires nine services;
`docs/CLAUDE.md` forbids premature microservices. Resolved as *boundary is a
contract, process count is a deployment choice*: nine bounded contexts, four
deployed processes in Phase 1, with documented extraction triggers.

### Task 4 — Diagrams ✅

`docs/architecture/diagrams/` — four documents, ten Mermaid diagrams:

| File | Diagrams |
|------|----------|
| `system-overview.md` | Layered system view |
| `service-communication.md` | Allowed call graph + full research-run sequence |
| `data-flow.md` | Record lifecycle, provenance accumulation, evidence-level progression, storage responsibilities |
| `deployment-view.md` | Phase 1 topology, Phase 2 extraction, local development |

Undecided items are marked as pending **on the diagram**, with their decision id.

### Task 5 — ADRs ✅

ADR-001 (Turborepo), ADR-002 (Next.js 15), ADR-003 (FastAPI), plus a template and
an index.

Each contains Context, Decision, Alternatives (3–4 credible ones each, with why
they were rejected), Pros, Cons, Future impact, and a compliance section mapping
the decision onto specification sections.

These three record decisions that were **already locked** by the manifest. They
are written anyway because a locked decision with no recorded rationale becomes
unquestionable — nobody knows what it traded off. The Cons and "cost of reversal"
sections are the parts that will matter in two years.

### Task 6 — Repository standards ✅

`.editorconfig`, `.gitattributes`, `.gitignore`, `CODEOWNERS`, `CONTRIBUTING.md`,
plus `.github/PULL_REQUEST_TEMPLATE.md`.

Built for the specific risks of this project rather than copied from a template:

- `.gitignore` puts **secrets first**, then excludes collected data (provenance,
  licensing, privacy constraints), model weights, and local database volumes.
- `.gitattributes` handles the Windows/LF problem (`.sh` must stay LF or scripts
  fail cryptically) and explicitly does *not* mark docs as
  `linguist-documentation`, because the manifest treats documentation as
  production code.
- `CONTRIBUTING.md` leads with seven non-negotiables drawn from the
  specifications, and forbids mixing specification changes with code in one branch.
- The PR template asks the questions automation cannot check: is this claim
  correctly typed, is this confidence justified, is this prompt injection-safe.

### Task 7 — Quality gates ✅

`docs/architecture/quality-gates.md`, `docs/architecture/testing-strategy.md`,
`turbo.json`, `pnpm-workspace.yaml`, two CI placeholder workflows.

The lint strategy lists rules **by what specification violation each one blocks**
rather than by style preference. The testing strategy addresses the problem
specific to this system: its output is an estimate, so tests assert **invariants
and properties**, never exact score values — a suite that pins scores would fail
on every legitimate model improvement.

CI workflows are `workflow_dispatch`-only. Deliberately: there is no lockfile and
no test suite yet, and a CI that fails on every PR from day one is a CI everyone
learns to ignore.

---

## 3. Remaining architecture work

Ordered by what blocks what.

### Before any code (Mission 0.2 entry criteria)

| Item | Blocks |
|------|--------|
| **ADR-004** — queue/runtime split (C-01) | The runtime of `workers` and `acquisition`; the language of half the codebase |
| **D-05** — multi-tenancy model | Every table's primary key. Must be answered before the first migration |
| **Ontology V1.1 erratum** — claims taxonomy (C-02), motivation vs value proposition (A-08) | `packages/contracts` enums |
| **Scoring V1.1 erratum** — numeric scales (C-04) | `packages/contracts` types, every column type |

### Mission 0.2 (foundation completion)

- `packages/contracts` — schema source + TS/Python generation. Highest priority.
- ADR-005 — storage architecture (schema-per-context, Qdrant as derived index,
  migration tooling).
- ADR-006 — LLM provider and cost model (D-04).
- Database schema v1, with provenance fields non-nullable by default (A-10).
- ESLint config with the boundary rules.
- Local Docker Compose stack.
- Enable `security.yml`, then `ci.yml`.
- Replace `@speekyx` in `CODEOWNERS` with a real handle (D-09), then enable
  branch protection.

### Sprint 1 (before scoring exists)

- `evidence-aggregation-v1.md` — the Evidence Score formula, decay parameters,
  independence thresholds (D-03, A-02, A-03, A-04).
- Ontology V2 — `ResearchContext` entity (D-01, A-06).
- Source registry format + §13 legal review records (D-07).
- Observability decision (D-11) and `packages/observability`.
- Retention and deletion policy (D-06).

### Later

- Environment topology and hosting (D-10).
- Score recomputation policy (D-08).
- Embedding version and re-embedding strategy (D-12).
- Scoring profile calibration methodology — the framework itself says the V1
  weights are hypotheses, not truths.

---

## 4. Technical risks

Ranked by expected cost, not by likelihood.

### R-01 — Building scoring before evidence aggregation is defined — **Critical**

The Evidence Score has a name, a purpose and an example value, but no formula.
Recency decay is required with no parameters. The independence threshold that
gates evidence level 3 does not exist.

If `scoring` is implemented anyway, someone picks those numbers. They become
load-bearing. Every score in the system then rests on invented constants
presented as analysis — which is precisely the false precision
`scoring-framework-v1.md` §10 forbids, and it is unfalsifiable after the fact
because nothing records that they were invented.

**Mitigation:** D-03 is a hard prerequisite for `services/scoring`. Recorded in
the service README as a blocker.

### R-02 — Multi-tenancy decided late — **Critical**

Nothing in the specifications says whether this is a personal research tool or a
multi-tenant SaaS. The difference is a tenant column on every table and row-level
security throughout.

Retrofitting a tenant boundary onto a system with production data is among the
most expensive migrations in this class of system, and it cannot be done
incrementally.

**Mitigation:** answer D-05 before the first migration. Cost now: one decision.
Cost in six months: a rewrite of the data layer.

### R-03 — Domain enum drift — **High**

C-02 and C-04 already exist *in the specifications*, before any code. The failure
mode is well understood: the same concept maintained in two places diverges.

**Mitigation:** `packages/contracts` as the single generated source, plus a lint
rule making a locally declared domain enum a build failure. Both are designed;
neither exists yet. Until then the risk is live.

### R-04 — Cost explosion — **High**

An LLM call per collected record, an unbounded queue, or a synchronous research
run each produce an unbounded bill. The architecture defends against all three
(cost ladder, run budgets, async runs, backpressure), but every defense is
currently a document.

**Mitigation:** cost telemetry per run and per job type from the first LLM call,
not after the first surprising invoice. Hard budget enforcement in
`research-orchestrator`.

### R-05 — Monorepo boundary erosion — **Medium-High**

ADR-001 accepted this explicitly. Everything is one import away, and a
cross-context import compiles fine. The dependency matrix exists on paper.

**Mitigation:** `no-restricted-imports` in `packages/eslint-config`, enforced in
CI. Design fixed, not implemented. Every week without it is a week where the
boundaries depend on discipline.

### R-06 — Prompt injection — **Medium-High**

`acquisition` collects adversarial text **by design**. It flows into `nlp` and
`execution`, both of which use LLMs. This is not a hypothetical threat model; it
is the normal operating condition of the system.

**Mitigation:** delimited untrusted-data regions, schema-validated outputs, and
an adversarial fixture corpus maintained as a regression suite
(`testing-strategy.md` §3, `security.yml` injection job). None implemented.

### R-07 — Polyglot toolchain friction — **Medium**

Two languages, two dependency managers, two lint stacks, two test runners, and a
task orchestrator that only natively understands one of them. Accepted in ADR-001
and ADR-003 as an unavoidable consequence of the Python-only ML stack.

**Mitigation:** thin `package.json` script wrappers per Python service; explicit
acceptance that Python task caching is coarse.

### R-08 — Nine contexts, one maintainer — **Medium**

Nine bounded contexts is a lot of surface for one person. The Phase 1 four-process
topology reduces the operational cost, but not the cognitive cost of nine
contracts.

**Mitigation:** boundaries defined as modules, not processes; extraction deferred
until measured. If the context count becomes the bottleneck, contexts can be
merged — which is cheap in a monorepo and expensive in a polyrepo. That was one
reason for ADR-001.

### R-09 — Legal exposure from data acquisition — **Medium**, high variance

Scraping and browser automation carry real terms-of-service and licensing risk.
`data-principles.md` §3 and §13 are strict, but no source registry exists yet, so
there is nothing yet to be strict *about*.

**Mitigation:** D-07 before `acquisition` collects anything. A §13 legal review
record per source, before first collection, including for test fixtures.

### R-10 — Specification drift over time — **Low now, compounding**

`docs/CLAUDE.md` is authoritative but unversioned, which violates the manifest's
own "Version Everything" principle. As architecture documents accumulate, the gap
between what the specifications say and what the system does widens quietly.

**Mitigation:** version `docs/CLAUDE.md`; keep `specification-audit.md` as a
living register; PR template requires naming the governing specification.

---

## 5. Estimated complexity

Rough order of magnitude for a single experienced engineer, assuming the human
decisions in §6 are answered promptly. These are planning aids, not commitments.

### Delivered in Mission 0.1

| Deliverable | Effort |
|-------------|--------|
| Specification audit | 1–2 days |
| Monorepo + standards + quality gates | 1–2 days |
| Service boundaries (9 contexts) | 2–3 days |
| Diagrams | 1 day |
| ADRs | 1 day |
| **Total** | **~1.5 weeks of human-equivalent work** |

### Remaining foundation

| Work | Effort | Confidence |
|------|--------|-----------|
| ADR-004 + runtime split | 2–3 days | High |
| `packages/contracts` + dual generation | 1–1.5 weeks | Medium |
| Database schema v1 with full provenance | 1–1.5 weeks | Medium |
| Local Docker stack | 3–5 days | High |
| CI enablement (both workflows, path filtering) | 3–5 days | High |
| ESLint config + boundary rules | 2–3 days | High |
| **Mission 0.2 total** | **4–6 weeks** | Medium |

### Full system, by context

| Context | Effort | Confidence | Why |
|---------|--------|-----------|-----|
| `gateway` | 1–2 weeks | High | Well-understood adapter |
| `research-orchestrator` | 4–6 weeks | **Low** | Blocked on D-01; planning, budgeting and resumability are genuinely hard |
| `acquisition` | 6–10 weeks | **Low** | Per-source work with no economies of scale; each source is its own project |
| `nlp` | 6–8 weeks | Medium | Well-trodden ML, but independence estimation and injection resistance are not |
| `scoring` | 4–6 weeks | **Low** | Blocked on D-03; calibration is open-ended and never really finishes |
| `market-intelligence` | 4–6 weeks | Low | Market sizing with honest methodology is hard |
| `competition` | 3–5 weeks | Medium | Highest hallucination risk; needs heavy verification |
| `execution` | 3–4 weeks | Medium | Mostly LLM synthesis with strong output constraints |
| `workers` | 2–3 weeks | High | Standard queue mechanics |
| `apps/web` | 6–8 weeks | Medium | The uncertainty-first UI is a genuine design problem, not a CRUD screen |

**Total to a working end-to-end system: roughly 9–15 months** of single-engineer
work, dominated by `acquisition` (per-source, no leverage) and by scoring
calibration (iterative, no natural end).

**The honest caveat:** the low-confidence estimates are low-confidence because
they depend on decisions that have not been made. Any estimate on
`research-orchestrator`, `scoring` or `acquisition` will move substantially once
D-01, D-03 and D-07 are answered. Treat the wide items as ranges that will narrow,
not as commitments.

---

## 6. Questions requiring human decisions

Ordered by urgency. **Q1 and Q2 block Mission 0.2.**

### Q1 — How do BullMQ and Python coexist? (C-01 / D-02) — **BLOCKING**

BullMQ is Node-only. BGE-M3 and HDBSCAN are Python-only. Both are locked in the
manifest. Three options:

| Option | Shape | Trade-off |
|--------|-------|-----------|
| **A (recommended)** | Node/BullMQ worker tier; Python compute services over HTTP | Keeps the locked stack, one queue, one retry semantics. Costs a network hop per ML task and a second language in the repo |
| **B** | Replace BullMQ with Celery/RQ/arq | Simplest architecture, single language for the backend. Contradicts the locked stack |
| **C** | BullMQ for acquisition + a Python queue for ML | Each tool where it fits. Two queues, two dashboards, two retry semantics, permanent operational cost |

**Recommendation: A.** It is the only option that honours the manifest without
duplicating the queue. B is architecturally cleaner and should be chosen if you
are willing to amend the manifest — which is a legitimate choice, and the audit
would rather you amend it explicitly than have an implementer quietly work around
BullMQ.

**Nothing in `workers` or `acquisition` can be written until this is answered.**

### Q2 — Is this single-user or multi-tenant? (D-05) — **BLOCKING**

Is Startup Research OS a personal research tool for one operator, or a
multi-tenant product with customer accounts?

This determines whether every table carries a tenant id and whether row-level
security is needed. Retrofitting it after production data exists is one of the
most expensive migrations possible.

**No recommendation** — this is a product decision, not a technical one. But it
must be answered before the first migration, and "we'll decide later" is
functionally a decision for single-tenant with a very expensive escape hatch.

### Q3 — Do you authorize the ontology and scoring errata? (C-02, C-04)

Two specification changes are needed before `packages/contracts` can freeze its
enums:

1. **Ontology §7** — add `HYPOTHESIS` to the claims taxonomy (the evidence
   framework already treats it as first-class and §9 depends on it), and
   standardize on UPPERCASE.
2. **Scoring §4** — allow unit-interval `[0,1]` storage with 0–100 presentation,
   instead of mandating 0–100 at the dimension level.

`docs/CLAUDE.md` §Change control requires explicit authorization. Both are
recommended; neither has been applied.

### Q4 — Who is `Speekyx` on GitHub? (D-09)

`CODEOWNERS` uses the placeholder `@speekyx`. An unresolvable owner does not
error — GitHub silently assigns no reviewer, so branch protection appears
configured while enforcing nothing.

### Q5 — Which LLM provider, which model tiers, what budget per run? (D-04)

Blocks `nlp` and `execution`. Needed: provider, a cheap tier for
classification/extraction and a strong tier for synthesis, and a hard cost
ceiling per research run.

The cost ladder (`llm-reasoning-rules.md` §8) means most volume should never
reach an LLM at all — but the budget for what does reach one has to be a number,
not an intention.

### Q6 — Where does this run? (D-10)

Local only for now, or is there a target (Vercel + a container host, a single
VPS, a managed Kubernetes)? This shapes `infrastructure/` and the CI deployment
jobs. It can wait until Mission 0.3, but not longer.

### Q7 — What is the retention policy? (D-06)

How long is raw collected content kept? What happens on a deletion request?
This affects the schema (soft vs hard delete, content addressing) and is much
cheaper to design in than to add.

---

## 7. Mission boundary

**Mission 0.1 is complete. Mission 0.2 has not been started**, as instructed.

Nothing in this repository implements business logic, collectors, NLP, scoring,
dashboards, authentication, monetization or user workflows.

Two exceptions worth stating explicitly, both under
`PROJECT_MANIFEST.md` §Forbidden During Foundation:

1. **`packages/typescript-config` contains real configuration** (JSON only, no
   code, no dependencies). A pnpm workspace with zero packages is not a working
   monorepo, and the task asked for a production-ready one.
2. **Baseline security hygiene was delivered** — secret exclusion, secret-handling
   rules, a secret-scanning CI placeholder. The forbidden item is *authentication
   features* (signup, login, sessions, roles); the manifest simultaneously
   requires "Security cannot be postponed". This reading is recorded as audit
   C-06.

Everything else in the repository is architecture, contract, or documentation.
