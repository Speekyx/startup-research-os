# Mission 0.1.2 — Completion Report

Sprint: 0 (Foundation)
Mission: 0.1.2 — Domain Contract Reconciliation Before Schema Freeze
Date: 2026-08-27
Status: Complete. Mission 0.2 not started.

---

## 1. Domain decisions applied

All six targeted ambiguities are resolved. Every decision in the brief was applied
as written; none was reinterpreted or partially applied.

| # | Decision | Applied as |
|---|----------|-----------|
| §3 | Research lifecycle: `ResearchProject`, `ResearchContext`, `ResearchSession`; `research run` retired | Ontology V2 §11 |
| §4 | Relationship model and cardinality | Ontology V2 §11.1 |
| §5 | `MarketScope` discriminated concept | Ontology V2 §4 |
| §6 | Closed enums vs extensible registries | Ontology V2 §14 |
| §7 | `MONEY` vs `MONEY_MAKING` | Ontology V2 §13 |
| §8 | Opportunity ↔ Research Session relationship as a requirement, not a schema | Ontology V2 §12 |
| §9 | Opportunity Ontology V2 | `docs/domain/opportunity-ontology-v2.md` |
| §10 | Authoritative chain repointed | Manifest v1.2, `docs/CLAUDE.md` v1.2, both READMEs |
| §11 | Terminology reconciliation | Boundaries, three diagrams, five service READMEs, contracts, observability, retention |
| §12 | Contract preparation | `packages/contracts/README.md` rewritten |
| §15 | Decision register | New register + forwarding section in the 0.1.1 register |

### Three judgment calls worth flagging

**V2 preserves V1.1's numbering for §1–§10.** New material is §11–§16. This costs
one aesthetic oddity — "Ontology evolution" sits at §10, before the new sections —
and buys total reference compatibility: every existing
`opportunity-ontology-v1.1.md §N` citation with `N ≤ 10` resolves to the same rule
in V2. In a mission whose whole purpose is contract stability before a schema
freeze, compatibility won.

**`ResearchSessionStatus` was canonicalized, not invented.** The states already
existed in `services/research-orchestrator/README.md` from Mission 0.1
(`pending → planning → … → complete | failed | cancelled`). §6 of the brief
requires lifecycle values to be a closed enum, and closed enums are UPPERCASE
here. No state was added. Two rules were written down explicitly to prevent
future invention: budget exhaustion is `COMPLETED` with reduced Research
Completeness, not a status; and a session that finds nothing is `COMPLETED`, not
`FAILED`.

**Demand signals were split without being enumerated in the brief.** §6 lists
nine registries and does not mention §3.6. Applying the stated principle: the
four signal *families* (`PAIN | DESIRE | BEHAVIORAL | MARKET`) are **closed** —
extraction, scoring and presentation branch exhaustively on them — while the
individual signal *types* within each family are a **registry**. This is marked
in V2 §3.6 as an application of the principle rather than an enumerated decision,
so it is visible and reversible.

---

## 2. Files created (3)

| File | Purpose |
|------|---------|
| `docs/domain/opportunity-ontology-v2.md` | **Authoritative ontology.** Resolves D-01, A-06, A-11, A-05, A-07, A-08 |
| `docs/architecture/mission-0.1.2-decisions.md` | Resolution register, successor to the 0.1.1 register |
| `docs/architecture/mission-0.1.2-report.md` | This report |

## 3. Files modified (22)

### Authoritative specifications

| File | Change |
|------|--------|
| `PROJECT_MANIFEST.md` | → v1.2. Ontology V2 authoritative; V1.1 marked superseded; Product Shape gains canonical lifecycle names; new §Extensible Taxonomies engineering principle |
| `docs/CLAUDE.md` | → v1.2. Boot sequence → V2; canonical invariants gain research lifecycle, `MarketScope`, and taxonomy governance |
| `docs/data/data-retention-policy-v1.md` | Operational-data row renamed to `ResearchSession`; context snapshot expires *with* the session, never before it |

### Architecture

`docs/architecture/service-boundaries.md` (→ v1.2), `specification-audit.md`
(§7 appendix only), `quality-gates.md` (→ v1.2), `testing-strategy.md` (→ v1.2),
`mission-0.1.1-decisions.md` (§5 forwarding section only),
`docs/architecture/README.md`, `diagrams/README.md`, `diagrams/system-overview.md`,
`diagrams/service-communication.md`, `diagrams/data-flow.md`.

### Services, packages, apps, root

`services/README.md`, `services/research-orchestrator/README.md`,
`services/gateway/README.md`, `packages/contracts/README.md`,
`packages/observability/README.md`, `apps/web/README.md`,
`README.md`, `docs/README.md`, `docs/domain/README.md`.

### Not modified, deliberately

- `docs/domain/opportunity-ontology-v1.md`, `opportunity-ontology-v1.1.md` —
  superseded, retained unchanged.
- `docs/domain/scoring-framework-v1.1.md`,
  `evidence-confidence-framework-v1.md`, `docs/ai/llm-reasoning-rules.md`,
  `docs/data/data-principles.md` — remain current, no authorized change.
- `mission-0.1-report.md`, `mission-0.1.1-report.md` — historical.
- `specification-audit.md` §1–§6 — original findings preserved verbatim.
- **ADR-002, ADR-004, ADR-005, ADR-006** — accepted ADRs are append-only. They
  still say "research run" and `run_id`. The mapping to `ResearchSession` /
  `research_session_id` is stated once in Ontology V2 §11.5 and repeated in
  `service-boundaries.md`, `packages/observability` and
  `services/gateway/README.md`, so no reader has to infer it.

---

## 4. Ontology V2 summary

V2 inherits V1.1 in full. §1–§10 keep their numbers and meaning; §11–§16 are new.

| Section | Content | Status |
|---------|---------|--------|
| §1–§2 | Purpose, `Opportunity` core entity | Unchanged |
| §3 | Dimensions, now annotated **CLOSED** or **REGISTRY** | Values unchanged, governance new |
| §4 | **`MarketScope`** — rewritten | New |
| §5 | Behavioral loop | Unchanged |
| §6 | Opportunity representation + workspace + discovery | Extended |
| §7–§9 | Claims taxonomy, distinction, confidence | Unchanged from V1.1 |
| §10 | Ontology evolution | Updated |
| §11 | **Research lifecycle** | New |
| §12 | **Opportunity ↔ ResearchSession** | New |
| §13 | **`MONEY` vs `MONEY_MAKING`** | New |
| §14 | **Taxonomy governance** | New |
| §15 | **`ResearchSessionStatus`** | New |
| §16 | Open items | New |

Not done: no evidence aggregation formula, no decay parameter, no independence
threshold, no scoring weight.

---

## 5. Research lifecycle model

```text
User
  ↓
Workspace                    tenant boundary (ADR-005)
  ↓
ResearchProject              persistent research objective
  ↓
ResearchSession              the only persisted execution
      └── ResearchContext snapshot (immutable)
  ↓
Evidence / Signals / Opportunities
```

A Workspace has many Projects. A Project has many Sessions. A Session belongs to
exactly one Project and one Workspace.

| Concept | Kind | Why |
|---------|------|-----|
| `ResearchProject` | Persisted entity | Gives repeated sessions a shared frame. Without it, two runs of the same investigation three months apart are unrelated rows |
| `ResearchContext` | **Value object** | No identity, no lifecycle: two contexts with identical parameters are the same specification. An id and a table would create a second thing to keep in sync, and would invite mutation — which would silently invalidate the reproducibility the snapshot exists to provide |
| `ResearchSession` | Persisted entity | The one execution record. Carries workspace, project, context snapshot, status, timing, budget, cost, completeness, versions, failures, provenance |

### Why the context snapshot must be immutable

Editing a project's default context must never retroactively change what a past
session says it ran with. That property is the entire reproducibility guarantee;
without it, `llm-reasoning-rules.md` §9 version tracking records *how* a result
was computed but not *what was asked*.

### `research run` retired

There was never a second concept — there were two names for one thing, which is
what A-11 recorded. No `ResearchRun` entity exists. Historical documents and
accepted ADRs keep the old term; in them, "research run" means `ResearchSession`
and `run_id` means `research_session_id`.

---

## 6. MarketScope design

```text
MarketScope =
  | { type: "GLOBAL" }
  | { type: "REGION",        regions:   RegionId[] }
  | { type: "COUNTRY",       countries: [CountryCode] }        // exactly one
  | { type: "MULTI_COUNTRY", countries: CountryCode[] }        // two or more
```

- `CountryCode` — **ISO 3166-1 alpha-2**, uppercase. No proprietary coding
  system, now or later: a standard identifier is what makes external datasets
  joinable without a translation layer that would silently drift.
- `RegionId` — from a **controlled registry**, not hard-coded. Region definitions
  are political and change; they are data, not business logic.

### Invariants (V2 §4.4)

`COUNTRY` carries exactly one code, `MULTI_COUNTRY` two or more, `GLOBAL` none.
Lists are canonicalized — uppercase, deduplicated, sorted — so one scope has
exactly one representation. That canonical form is what makes a scope safe as a
cache key, a dedup key and an equality test. An empty list is invalid; absence of
scope is `GLOBAL`.

### Why `COUNTRY` and `MULTI_COUNTRY` are both needed

They differ in meaning, not cardinality. `COUNTRY` means "about one national
market", and its scores are comparable with other single-country scores —
the comparison `scoring-framework-v1.1.md` §9 exists to support.
`MULTI_COUNTRY` means "aggregate across the listed markets", and its score is not
a per-country score. Rendering one in a per-country column would be exactly the
geographic averaging V2 §4.7 forbids.

### What it does not cover

Only the **geographic axis**. Segment/audience scoping is a different axis,
deliberately not folded in — see §8 and A-12 below.

---

## 7. Enum vs registry policy

**The principle:** closed enums only where code branches exhaustively and an
unhandled value is a bug. Registries for taxonomies expected to evolve.

**Why it matters here specifically:** the engine must support product categories,
motivations and channels that do not exist yet. If those live in database enums,
every new concept needs a migration — and a system that needs a migration to
describe a new kind of product will stop describing new kinds of products.

| Closed enums | Extensible registries |
|--------------|----------------------|
| `ClaimType` | Market Type |
| `MarketScope.type` | Product Type |
| Demand signal family | User Motivation |
| `EvidenceLevel` (0–5) | User Behavior |
| `ResearchSessionStatus` | Value Proposition |
| | Demand signal type |
| | Retention Mechanism |
| | Monetization Model |
| | Distribution Channel |
| | Risk |
| | Region |

Registry entries carry a stable identifier, canonical name, description, version,
`active`/`deprecated` status and aliases. Two consequences stated explicitly:
**deprecation, not deletion** (a deleted entry makes past classifications
unreadable), and **the stable identifier is what gets persisted** (storing a
display name means a rename silently rewrites history).

**One earlier draft was overridden.** `packages/contracts/README.md` had listed
`UserMotivation` as a closed enum. That was a recommendation pending A-07, not an
authorized decision; V2 §3.3 reclassifies it as a registry and the contracts
README now says so, with the change noted rather than quietly applied.

Nothing is implemented. The storage ADR (ADR-008) must honour §14.3: taxonomy
values are rows, not enum types.

---

## 8. Remaining blockers

### Hard blocker — unchanged

| ID | Item | Blocks |
|----|------|--------|
| **D-03 / A-02 / A-03 / A-04** | Evidence aggregation formula, recency decay parameters, independence thresholds, contradiction penalties | **`services/scoring` cannot be implemented** (`scoring-framework-v1.1.md` §13) |

### Open, non-blocking for Mission 0.2

| ID | Item |
|----|------|
| **A-12** | *New.* Non-geographic (audience/segment) scoping and how it composes with `MarketScope` |
| — | Opportunity identity resolution: when two discoveries are the same opportunity (V2 §12.3) |
| A-01 | Sparse vs dense scoring-profile weight vectors |
| D-07 | Source registry and legal review records — blocks `acquisition` |
| D-08 | Score recomputation policy — sharpened by V2 §12 |
| D-11 | Observability stack |
| D-12 | Embedding re-embedding strategy |
| — | Region registry contents |
| — | GDPR/jurisdiction analysis — requires legal input |
| — | LLM budget figures; production deployment target |

### A-12 — the one new finding

V1 and V1.1 §4 allowed analysis to be "global, regional, country-level, or
**segment-level**". The authorized `MarketScope` has no segment type.

Rather than inventing a `SEGMENT` variant (unauthorized) or silently dropping the
requirement, V2 §4.8 states that `MarketScope` covers the geographic axis only and
that segment scoping is a separate axis deliberately not folded in. Folding an
audience dimension into a geographic discriminated union would eventually force a
`COUNTRY_AND_SEGMENT` variant, which makes both axes harder to query and
impossible to combine.

**Severity: ambiguity, not contradiction.** It blocks nothing in Mission 0.2
provided schema design treats scope as geographic. It becomes expensive only if
segment-level scores are required after score rows exist.

---

## 9. Mission 0.2 readiness

### Now unblocked

- `packages/contracts` — every listed type has an authoritative definition.
- Database schema v1 — every entity, identifier, enum and registry boundary is
  specified.
- `research-orchestrator` input contract — `ResearchContext` is defined.
- Gateway API surface — resource names are canonical.

### Ordered work for Mission 0.2

1. **`packages/contracts`** — identifiers, closed enums, registry reference types
   and entry shape, `MarketScope` with its §4.4 validators, `ResearchContext`,
   `ResearchSessionStatus`, `Confidence`/`Probability`/`EvidenceLevel` ranges.
2. **ADR-008 — storage architecture.** Must honour: `workspace_id NOT NULL` with
   composite indexes leading on it; taxonomies as registry **rows, not enum
   types**; the opportunity ↔ session observation relationship (V2 §12); provenance
   NOT NULL by default; `expires_at` computed at write time.
3. **Database schema v1.**
4. **Local Docker Compose** — pinned versions, health checks, Redis AOF, default
   development workspace seeded.
5. **Celery skeleton** — queues, routing, retry policy, Beat. No job bodies.
6. **LLM Gateway skeleton** — tier resolution, telemetry, budget hooks.
7. **CI enablement** — `security.yml` first, then `ci.yml`.
8. **ESLint config** — boundary rules, provider-SDK restriction, local-enum
   restriction, registry-vs-enum lint.

### Sequencing constraints that survive this mission

| Before this | Do this |
|-------------|---------|
| `services/scoring` | `evidence-aggregation-framework-v1.md` (D-03) |
| `services/acquisition` | Source registry (D-07) |
| Segment-scoped scores | Resolve A-12 |
| Any production deployment | Production ADR; GDPR/jurisdiction analysis |

---

## 10. Validation results

| Check | Result |
|-------|--------|
| No current authoritative document uses `ResearchRun` as an entity | **PASS** — 5 occurrences repo-wide, all explicit prohibitions or the A-11 resolution text |
| `research run` absent from current documentation | **PASS** — 10 remaining occurrences are all retirement notices or the historical mapping note. Historical reports and accepted ADRs retain it by design |
| Gateway endpoints renamed | **PASS** — no `/v1/research-runs` or `/internal/runs` remains |
| `run_id` replaced by `research_session_id` in current docs | **PASS** — 6 remaining mentions are the ADR mapping note, stated in five places so no reader has to infer it |
| Ontology V2 exists and is authoritative | **PASS** — boot sequence updated in `PROJECT_MANIFEST.md`, `docs/CLAUDE.md`, `docs/README.md`, root `README.md` |
| V1 and V1.1 ontology files retained | **PASS** — both present, unmodified |
| Closed enums vs registries documented | **PASS** — V2 §14, mirrored in `packages/contracts` and quality gates |
| `MarketScope` explicitly defined | **PASS** — V2 §4, with invariants; 4 embedded JSON examples parse |
| `MONEY` and `MONEY_MAKING` both present, distinctly defined | **PASS** — V2 §3.3, §3.5, §13; neither removed |
| Historical mission reports untouched | **PASS** — 0.1 and 0.1.1 reports unmodified; audit §1–§6 unmodified, §7 appended; 0.1.1 register §1–§4 unmodified, §5 appended |
| Relative Markdown links | **PASS** — 55 checked, 0 broken |
| JSON valid | **PASS** — 6/6 |
| YAML valid | **PASS** — 3/3 |
| Backtick repo-path references | **PASS** — 1 intentional exception: `evidence-aggregation-framework-v1.md` does not exist **by design**; it is the named blocker |

---

## 11. Explicit answers

### Is A-11 resolved?

**Yes.** `ResearchSession` is the canonical persisted execution entity;
`ResearchProject` is the persistent grouping; `ResearchContext` is the input
snapshot. `research run` is retired and **no `ResearchRun` entity is
introduced** — there was never a second concept, only a second name. Endpoints,
correlation fields and service documentation all use the canonical names.
Historical documents keep the old term with the mapping stated explicitly.

### Is `ResearchContext` formally defined?

**Yes** — as a **value object**, not an entity (V2 §11.3). It carries market
scope, market and product types, domains, audience, languages, budget and
technical constraints, desired MVP complexity, research depth, time horizon and
exclusions. It is stored as an **immutable snapshot** on a `ResearchSession` for
reproducibility, and the reason it is not an entity is recorded: no identity, no
lifecycle, and a separate table would invite the mutation that would destroy the
snapshot's purpose.

### Is `ResearchSession` canonical?

**Yes.** It is the only persisted execution entity, belonging to exactly one
Project and one Workspace, with a closed-enum status (V2 §15).

### Is `MarketScope` defined?

**Yes.** `GLOBAL | REGION | COUNTRY | MULTI_COUNTRY`, ISO 3166-1 alpha-2 country
codes, region identifiers from a controlled registry, with invariants that make
scope equality well-defined — which matters because scope is a cache and dedup
key, not just a label. Geographic axis only; segment scoping is A-12.

### Are extensible taxonomies separated from closed enums?

**Yes** (V2 §14). Five closed enums, eleven registries, with the registry entry
contract specified — stable identifier, name, description, version,
active/deprecated, aliases. Nothing implemented. The storage ADR must honour it:
taxonomy values are rows, not enum types.

### Is `MONEY` vs `MONEY_MAKING` resolved?

**Yes.** Not duplicates, neither removed. `MONEY` is a **motivation** — why the
user acts. `MONEY_MAKING` is a **value proposition** — what the product provides.
The axes are independent: a hobbyist print-on-demand tool is motivation
`CREATIVITY` with value proposition `MONEY_MAKING`, and collapsing the axes would
make that opportunity invisible. The general rule — motivation is about the user,
value proposition is about the product — is stated to cover every similar pair.

### Can `packages/contracts` now be safely implemented?

**Yes.** Every type in the brief's §12 list has an authoritative definition:
identifiers, `ClaimType`, `MarketScope`, `ResearchContext`,
`ResearchSessionStatus`, `Confidence`, `Score`, `Probability`, `EvidenceLevel`.

Two boundaries to respect. Registry taxonomies are declared as **reference
types**, never as union types enumerating the values — enumerating them in a
generated type would recreate the migration-per-concept problem the split
prevents. And nothing depending on evidence aggregation may be declared, because
D-03 is still blocked.

### Can database schema v1 now be designed?

**Yes**, with one exclusion and four constraints.

**Exclusion:** no table whose columns depend on evidence aggregation (D-03).

**Constraints:**

1. Taxonomies are registry **rows**, not PostgreSQL enum types (V2 §14.3).
2. `workspace_id NOT NULL` on every tenant-scoped table, composite indexes
   leading with it (ADR-005).
3. The opportunity ↔ session relationship is an **observation record**, not
   ownership. An opportunity is not a row belonging to the session that first
   found it, or rediscovery creates duplicates and cross-session evidence cannot
   accumulate — which would defeat evidence levels 2 and 3 (V2 §12.2).
4. `MarketScope` is stored in canonical form so equality is well-defined
   (V2 §4.4).

**Identity resolution stays out of the schema.** Deciding that two discoveries are
the same opportunity is an analytical problem. It must not be settled implicitly
by a unique constraint chosen for convenience (V2 §12.3).

---

## 12. Mission boundary

**Mission 0.2 was not started.** This mission produced no database schema, SQL
migration, ORM model, authentication, authorization, collector, NLP, scoring,
evidence aggregation constant, Celery job, LLM provider code or Docker Compose
implementation.

Every change was documentation: one new authoritative specification, one decision
register, one report, and terminology reconciliation across 22 existing files.
