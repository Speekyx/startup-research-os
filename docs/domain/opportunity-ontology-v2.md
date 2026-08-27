# Opportunity Ontology V2

**Status:** Authoritative. Supersedes `opportunity-ontology-v1.1.md`.
**Date:** 2026-08-27
**Supersedes:** V1.1, which superseded V1. Both retained as historical specifications.
**Authorized by:** Sprint 0 / Mission 0.1.2
**Resolves:** D-01, A-06, A-11, A-05, A-07, A-08

---

## 0. Changes from V1.1

V2 inherits V1.1 in full. **Sections §1–§10 keep their V1.1 numbers and meaning**,
so every existing reference to `opportunity-ontology-v1.1.md §N` remains valid
against V2 for `N ≤ 10`. New material is appended as §11–§16.

| Change | Section | Resolves |
|--------|---------|----------|
| §3 taxonomies annotated as **closed enum** or **extensible registry** | §3, §14 | **A-07** |
| §4 replaced with a canonical `MarketScope` discriminated union | §4 | **A-05** |
| §6 Opportunity representation gains workspace and discovery relationships | §6 | — |
| Research lifecycle defined: `ResearchProject`, `ResearchContext`, `ResearchSession` | §11 (new) | **D-01**, **A-06**, **A-11** |
| `Opportunity` ↔ `ResearchSession` relationship stated as a requirement | §12 (new) | — |
| `MONEY` vs `MONEY_MAKING` disambiguated | §13 (new) | **A-08** |
| Taxonomy extensibility rules | §14 (new) | **A-07** |
| `ResearchSessionStatus` canonicalized as a closed enum | §15 (new) | — |
| Ontology evolution updated; open items refreshed | §10, §16 | — |

**Unchanged from V1.1:** the claims taxonomy (§7), confidence representation
(§9), the behavioral loop (§5), and every taxonomy *value* in §3. V2 changes how
those values are *governed*, not what they are.

**Not done here:** no evidence aggregation formula, no decay parameter, no
independence threshold, no scoring weight. D-03 remains blocked
(`scoring-framework-v1.1.md` §13).

---

## 1. Purpose

The Opportunity Ontology defines the domain vocabulary used by the Startup
Research OS.

The system does not define a good opportunity solely as a painful problem. An
opportunity can exist because users want to solve a problem, accomplish a goal,
have fun, create something, learn, compete, socialize, explore, express
themselves, or experience something novel.

## 2. Core entity

An `Opportunity` is a structured, evidence-backed hypothesis that a digital
product could create meaningful value for a defined audience in a defined market
under a plausible product and distribution model.

An opportunity is not automatically:

- a validated business,
- a guaranteed successful startup,
- a proven product-market fit,
- or a prediction of future revenue.

## 3. Opportunity dimensions

**Governance note (new in V2).** Each taxonomy below is marked **REGISTRY**
(extensible, versioned entries) or **CLOSED** (fixed enum, changing it requires a
new ontology version). The values listed remain exactly those of V1/V1.1 and
become the **initial canonical registry entries** where marked REGISTRY. See §14
for the full policy.

### 3.1 Market type — **REGISTRY**

Examples (initial entries):

- B2B
- B2C
- B2B2C
- Prosumer
- Creator
- Developer
- Student
- Professional
- Hobbyist
- Community
- Enterprise

Multiple labels may apply.

### 3.2 Product type — **REGISTRY**

Examples (initial entries):

- SaaS
- Web App
- AI Application
- Marketplace
- Social Platform
- Community
- Tool
- Game
- Educational Product
- Content Platform
- Generator
- Tracker
- Assistant
- Automation
- Browser Extension
- API

Multiple labels may apply.

### 3.3 User motivation — **REGISTRY**

First-class motivation categories (initial entries):

- PROBLEM
- UTILITY
- ENTERTAINMENT
- CREATIVITY
- CURIOSITY
- LEARNING
- COMPETITION
- SOCIAL
- EXPRESSION
- STATUS
- DISCOVERY
- EMOTION
- ACHIEVEMENT
- COLLECTION
- PERSONALIZATION
- EXPERIENCE
- MONEY

A motivation can be primary or secondary.

> **Changed in V2.** V1.1 draft guidance in `packages/contracts` treated
> `UserMotivation` as a closed enum. The A-07 resolution reclassifies it as a
> **registry**: the engine must support new motivation categories without a
> database migration. See §13 for `MONEY` specifically.

### 3.4 User behavior — **REGISTRY**

Initial entries:

- CREATE
- DISCOVER
- CONSUME
- PLAY
- LEARN
- COMPARE
- PREDICT
- COLLECT
- SHARE
- COMPETE
- CUSTOMIZE
- TRACK
- DISCUSS
- BUY
- SELL
- COLLABORATE
- AUTOMATE

### 3.5 Value proposition — **REGISTRY**

Initial entries:

- TIME_SAVING
- MONEY_SAVING
- MONEY_MAKING
- CONVENIENCE
- KNOWLEDGE
- ENTERTAINMENT
- CREATIVITY
- SOCIAL_CONNECTION
- STATUS
- PERSONAL_GROWTH
- DISCOVERY
- EXPERIENCE

See §13 for `MONEY_MAKING` specifically.

### 3.6 Demand signals

**Signal family — CLOSED.** Exactly four families. Extraction, scoring and
presentation all branch exhaustively on them, so adding a fifth changes
interpretation contracts and requires a new ontology version.

```text
PAIN | DESIRE | BEHAVIORAL | MARKET
```

**Signal type within a family — REGISTRY.** The individual types below are
expected to grow as new sources and extraction methods appear.

> This split applies the §14 principle to a taxonomy that the A-07 resolution did
> not enumerate explicitly. It is recorded here so it is visible and reversible,
> rather than assumed silently.

#### Pain signals

- complaint
- frustration
- repeated problem
- workaround
- manual process
- expensive solution
- missing feature

#### Desire signals

- explicit request
- wish statement
- product request
- curiosity
- expressed intent
- positive reaction
- desire to try

#### Behavioral signals

- engagement
- repeated usage
- shares
- comments
- searches
- communities
- purchases
- subscriptions
- downloads where reliable

#### Market signals

- new competitors
- product launches
- funding
- search growth
- category growth
- technology changes
- regulatory changes
- platform changes

### 3.7 Retention mechanisms — **REGISTRY**

Initial entries:

- HABIT
- NEW_CONTENT
- PROGRESSION
- COLLECTION
- COMPETITION
- SOCIAL_GRAPH
- PERSONALIZATION
- EVENTS
- UTILITY
- WORKFLOW
- COMMUNITY
- CURIOSITY

### 3.8 Monetization models — **REGISTRY**

Initial entries:

- SUBSCRIPTION
- FREEMIUM
- CREDITS
- ONE_TIME_PURCHASE
- ADVERTISING
- AFFILIATE
- MARKETPLACE_FEE
- TRANSACTION_FEE
- SPONSORSHIP
- API_USAGE
- B2B_LICENSE
- DONATION

### 3.9 Distribution channels — **REGISTRY**

Initial entries:

- SEO
- SOCIAL
- VIRAL
- COMMUNITY
- CONTENT
- APP_STORE
- PRODUCT_HUNT
- WORD_OF_MOUTH
- PAID_ADS
- PARTNERSHIP
- MARKETPLACE
- EXTENSION_STORE
- DIRECT_SALES

### 3.10 Risks — **REGISTRY**

Initial entries:

- TECHNICAL_RISK
- DATA_DEPENDENCY
- PLATFORM_DEPENDENCY
- LEGAL_RISK
- COMPETITION_RISK
- ACQUISITION_RISK
- MONETIZATION_RISK
- RETENTION_RISK

## 4. Market scope

**Rewritten in V2. Resolves A-05.**

`MarketScope` is the canonical, explicit representation of the **geographic
scope** of an analysis. It is a discriminated union on `type`.

### 4.1 Scope types — CLOSED enum

```text
GLOBAL | REGION | COUNTRY | MULTI_COUNTRY
```

Closed, because every consumer branches exhaustively on it: scoring, market
intelligence, competition, storage keys and presentation.

### 4.2 Shape

```text
MarketScope =
  | { type: "GLOBAL" }
  | { type: "REGION",        regions:   RegionId[] }
  | { type: "COUNTRY",       countries: [CountryCode] }        // exactly one
  | { type: "MULTI_COUNTRY", countries: CountryCode[] }        // two or more
```

Examples:

```json
{ "type": "GLOBAL" }
```

```json
{ "type": "COUNTRY", "countries": ["FR"] }
```

```json
{ "type": "MULTI_COUNTRY", "countries": ["US", "FR", "DE"] }
```

```json
{ "type": "REGION", "regions": ["EUROPE"] }
```

### 4.3 Identifiers

- **`CountryCode`** — **ISO 3166-1 alpha-2**, uppercase. No proprietary country
  coding system is introduced, now or later. Using a standard identifier is what
  makes external datasets joinable without a translation layer that would
  silently drift.
- **`RegionId`** — an identifier from a **controlled region registry** (§14).
  `EUROPE` is an illustrative entry, not a hard-coded constant. Region membership
  is registry data, not business logic, because region definitions are political
  and change.

**No geographic data is implemented in this mission.** The registry contract is
specified; its contents are Data Engineering work.

### 4.4 Invariants

1. `COUNTRY` carries **exactly one** country code. `MULTI_COUNTRY` carries **two
   or more**. A one-element `MULTI_COUNTRY` is invalid, and so is a two-element
   `COUNTRY`. Without this rule the two types overlap and the same scope has two
   representations.
2. `GLOBAL` carries no members.
3. Country and region lists are **canonicalized**: uppercase, deduplicated,
   sorted. One scope therefore has exactly one representation — which is what
   makes it safe as a cache key, a dedup key and an equality test.
4. An empty `regions` or `countries` list is invalid. Absence of scope is
   expressed as `GLOBAL`, never as an empty list.

### 4.5 Why `COUNTRY` and `MULTI_COUNTRY` are distinct

They differ in meaning, not just in cardinality.

- **`COUNTRY`** — the analysis is *about one national market*. Its scores are
  directly comparable with other single-country scores, which is the comparison
  `scoring-framework-v1.1.md` §9 exists to support.
- **`MULTI_COUNTRY`** — the analysis is an *aggregate across the listed markets*.
  Its scores are not a per-country score and must never be presented as one.

A `MULTI_COUNTRY` score displayed in a per-country column would be exactly the
kind of geographic averaging §4.7 forbids.

### 4.6 Relationship to scoring

Scores are computed per `MarketScope`
(`scoring-framework-v1.1.md` §9). Each scope carries **its own evidence and
confidence**. A country score derived from global evidence is a fabrication, not
a projection.

### 4.7 Aggregation is lossy and must say so

A global score must not erase meaningful country-level differences. Where an
aggregate hides material divergence between its members, that divergence is
reported alongside the aggregate rather than discarded.

### 4.8 Non-geographic scope — OPEN (A-12)

V1 and V1.1 §4 listed "segment-level" alongside global, regional and
country-level. The authorized `MarketScope` covers the **geographic axis only**.

Audience or segment scoping (for example "indie game developers", "K-12
teachers") is a **different axis** and is deliberately **not** folded into
`MarketScope`. Combining an audience dimension into a geographic discriminated
union would make both harder to query and impossible to combine.

Whether segment-scoped scores are required, and if so how they compose with
`MarketScope`, is recorded as **open item A-12**. It is not resolved here and
must not be resolved by an implementer choosing a shape.

Other market dimensions from V1 §4 — market size, interest, growth, purchasing
power, competition, local alternatives, language, payment methods, distribution
channels, cultural and regulatory factors — remain properties analyzed *within* a
scope by `services/market-intelligence`. They are not part of the scope
identifier.

## 5. Behavioral loop

A product should be modeled as a possible user loop when appropriate:

`trigger → action → value → reward → reason to return`

Examples:

### Creative product

`discover → create → result → share → create again`

### Competitive product

`predict → result → compare → compete → predict again`

### Productivity product

`problem → workflow → saved effort → habit → workflow`

The presence and quality of a loop are signals, not guarantees of retention.

## 6. Opportunity representation

Conceptually:

```text
Opportunity
├── Workspace            (tenant boundary — ADR-005)
├── Market Scope         (§4)
├── Product Type
├── Target Users
├── Motivations
├── Behaviors
├── Value Proposition
├── Demand Signals
├── Retention Mechanisms
├── Monetization
├── Distribution
├── Competition
├── Market Intelligence
├── Risks
├── Evidence
├── Scores
└── Discovery            (which Research Sessions observed it — §12)
```

> **Changed in V2.** V1.1 deliberately excluded tenancy and research linkage,
> deferring both to this version. `workspace_id` is an ownership property, not an
> analytical dimension: it does not participate in scoring or interpretation, but
> no opportunity exists outside a workspace.

## 7. Claims taxonomy

Unchanged from V1.1. Resolves audit C-02.

Every important analytical statement must be classified as exactly one of five
canonical values:

| Value | Definition |
|-------|------------|
| `OBSERVED` | Directly supported by collected evidence |
| `INFERRED` | Derived analytically from one or more observations |
| `PREDICTED` | A model-generated estimate concerning an unknown or future outcome |
| `RECOMMENDED` | A proposed action or decision generated by the system |
| `HYPOTHESIS` | A plausible proposition that currently lacks sufficient evidence |

### Canonical form

Values are **UPPERCASE**. This is the persisted enum form, the API contract form,
and the form used in every internal document.

### `HYPOTHESIS` is mandatory and first-class

`evidence-confidence-framework-v1.md` §9 instructs the system, when a claim
cannot be supported by collected evidence, to classify it as a hypothesis.
Without `HYPOTHESIS` in the taxonomy there is nowhere for such a claim to go, and
the only remaining options are fabrication or silent omission.

### These categories must not be conflated

In user-facing output, in API responses, in stored records, or in logs. A
`PREDICTED` value rendered indistinguishably from an `OBSERVED` one is a
specification violation regardless of whether the number happens to be correct.

### Compatibility

Identical to `evidence-confidence-framework-v1.md` §8, which remains authoritative
for evidence levels, source reliability, independence, recency and provenance.

`ClaimType` is a **CLOSED enum** (§14). Adding, removing or renaming a value is a
material semantic change requiring a new ontology version and an ADR.

## 8. Important distinction

The system must distinguish observed facts, analytical inferences, model
predictions, system recommendations, and unsupported hypotheses, per §7.

These categories must not be conflated in user-facing output.

## 9. Confidence representation

Unchanged from V1.1. Aligns with `scoring-framework-v1.1.md` §4.1 and resolves
audit C-04.

Any confidence, reliability, independence or probability quantity attached to an
ontology object is represented internally as a **unit interval**:

```text
0.0 <= value <= 1.0
```

Presentation layers may render it as a percentage (`0.82` → `82%`).

**`confidence` and `score` are different concepts and must not be interchanged.**
A field named `confidence` is always `[0,1]`; a field named `*_score` is always
`0–100`. `evidence_level` remains an integer `0–5` and is never rescaled.

## 10. Ontology evolution

V2 is the current baseline. Material semantic changes require V3 or an explicit
extension/ADR.

Do not silently add a new fundamental category if doing so changes scoring,
storage, or interpretation contracts. Note that under §14 this constraint now
applies to **closed enums**; registry entries are added through the registry's own
versioned process, which is precisely why the split exists.

Historical versions are retained and never deleted:

- `opportunity-ontology-v1.md` — superseded by V1.1
- `opportunity-ontology-v1.1.md` — superseded by V2

Open items are listed in §16.

---

# New in V2

## 11. Research lifecycle

**Resolves D-01, A-06 and A-11.**

### 11.1 Canonical hierarchy

```text
User
  ↓
Workspace                    tenant boundary (ADR-005)
  ↓
ResearchProject              persistent research objective
  ↓
ResearchSession              persisted execution
      └── ResearchContext snapshot
  ↓
Evidence / Signals / Opportunities
```

Cardinality:

- A Workspace contains many Research Projects.
- A Research Project contains many Research Sessions.
- A Research Session belongs to **exactly one** Research Project and **exactly
  one** Workspace.

Workspace isolation remains mandatory at every level (ADR-005).

### 11.2 `ResearchProject`

A **persistent, workspace-scoped container** representing a user's broader
research objective. It is a durable grouping, not an execution.

Examples:

- "Find B2C gaming opportunities in Europe"
- "Analyze AI creator tools"
- "Research education opportunities in India"

A project exists independently of whether any session has run. It is what gives
repeated sessions a shared frame of reference: without it, two runs of the same
investigation three months apart are unrelated rows.

### 11.3 `ResearchContext` — a value object, not an entity

`ResearchContext` is the **structured research specification**: what should be
researched, under what constraints, at what scope.

```text
ResearchContext = Research Intent + Constraints + Scope
```

**It is NOT a persisted execution record.** It is an **input specification / value
object**. It may be stored *as part of a Research Session snapshot* for
reproducibility, but it is not an independent business entity unless a later
implementation constraint justifies persistence — and that would require an ADR.

Parameters it carries:

| Parameter | Notes |
|-----------|-------|
| `market_scope` | A `MarketScope` (§4). This is the canonical geographic axis; it replaces free-text "target markets" and "target countries" |
| `market_types` | Registry references (§3.1) |
| `product_types` | Registry references (§3.2) |
| `domains` / categories | Subject areas to investigate |
| `audience` | Target audience description |
| `languages` | Locale-aware processing (`data-principles.md` §7) |
| `budget_constraints` | Cost ceiling for the session (ADR-006 enforces it) |
| `technical_constraints` | Constraints on feasible solutions |
| `desired_mvp_complexity` | Feeds the Execution Score |
| `research_depth` | How deep to go before stopping |
| `time_horizon` | Observation window for evidence |
| `excluded_markets` / `excluded_categories` | Explicit exclusions |
| additional research filters | Extensible |

**Why a value object and not an entity.** A `ResearchContext` has no identity of
its own and no lifecycle: two contexts with identical parameters are the same
specification. Giving it an id and a table would create a second thing to keep in
sync with the session that used it, and would invite mutation — which would
silently invalidate the reproducibility the snapshot exists to provide.

**The snapshot is immutable.** A session's stored context is what it actually ran
with. Editing a project's default context must never retroactively change what a
past session says it did.

### 11.4 `ResearchSession` — the canonical persisted execution

`ResearchSession` is **the** persisted execution entity. There is no other.

It contains or references:

| Field | Purpose |
|-------|---------|
| `workspace_id` | Tenant boundary — required (ADR-005) |
| `project_id` | Owning Research Project |
| `research_context` | Immutable snapshot (§11.3) |
| `status` | `ResearchSessionStatus` (§15) |
| `created_at`, `started_at`, `completed_at` | Timezone-aware timestamps |
| budget configuration | Cost ceiling for this session |
| actual cost | Consumed budget (ADR-006 telemetry) |
| research completeness | `scoring-framework-v1.1.md` §2 |
| model / prompt / config versions | Reproducibility (`llm-reasoning-rules.md` §9) |
| failures | Research gaps and dead-lettered work (ADR-004) |
| provenance | Lineage of what was collected and how |
| resulting opportunities | Via the discovery relationship (§12) |

### 11.5 `research run` is retired

**"Research run" is no longer a canonical domain term.**

Current and future authoritative documentation uses **`ResearchSession`** when
referring to a persisted execution. Code uses canonical names such as
`ResearchSession` and `research_session_id`.

**No separate `ResearchRun` entity is introduced.** There was never a second
concept; there were two names for one thing, which is what A-11 recorded.

Historical documents legitimately retain the old term:

- `docs/architecture/mission-0.1-report.md`, `mission-0.1.1-report.md`
- `specification-audit.md` §1–§6 findings
- Accepted ADRs (ADR-002, ADR-004, ADR-005, ADR-006), which are append-only

In those documents, **"research run" means `ResearchSession`**, and the
correlation field they call `run_id` is `research_session_id`. This mapping is
stated once here so no reader has to guess.

## 12. Opportunity ↔ Research Session relationship

**Requirement, not a schema.** Mission 0.2 chooses the relational form.

### 12.1 The requirement

```text
Opportunity
    ↕
OpportunityObservation / Discovery
    ↕
ResearchSession
```

1. **An `Opportunity` is a domain hypothesis/entity in its own right.** It is not
   a row belonging to one execution.
2. **A `ResearchSession` produces evidence** supporting or contradicting an
   opportunity.
3. **The same conceptual opportunity may be rediscovered** in later sessions,
   within the same project or a different one.
4. **Provenance must allow tracing which session produced which conclusion.**
   Given any score, rationale or claim, it must be possible to identify the
   session that produced it.

### 12.2 Why the indirection exists

If an opportunity belonged permanently to the session that first found it, then:

- rediscovery would create duplicates that no query could reconcile;
- evidence accumulated across sessions could not be combined, which defeats
  evidence levels 2 and 3 (`evidence-confidence-framework-v1.md` §2), both of
  which are defined by corroboration across observations;
- contradiction across sessions would be invisible, and `data-principles.md` §10
  requires contradictions to be preserved rather than overwritten.

The observation record is what lets an opportunity accumulate evidence over time
while every individual conclusion stays traceable to the execution that produced
it.

### 12.3 Constraints on whatever schema Mission 0.2 chooses

- An opportunity is workspace-scoped; an observation never crosses workspaces.
- An observation references exactly one session and one opportunity.
- Deleting a session must not orphan an opportunity's history — retention rules
  apply per `data-retention-policy-v1.md`, and an expired reference renders as
  "expired", never as absence.
- Identity resolution — deciding that two discoveries are the *same* opportunity —
  is an analytical problem, not a schema problem. It is **not solved here**, and
  it must not be solved implicitly by a unique constraint chosen for convenience.

## 13. `MONEY` versus `MONEY_MAKING`

**Resolves A-08. They are not duplicates and neither is removed.**

They sit on two different axes. Confusing them produces a classifier that cannot
tell why a user acts from what a product delivers.

### `MONEY` — a **user motivation** (§3.3)

Represents **why the user acts**. It answers: *"Why does the user want this?"*

Examples: desire to earn money; desire to improve financial outcomes; interest in
financial gain.

### `MONEY_MAKING` — a **value proposition** (§3.5)

Represents **what the product provides**. It answers: *"What value does the
product create?"*

### Worked example

A freelance lead-discovery tool:

```text
User Motivation:      MONEY          (the user wants to earn more)
Value Proposition:    MONEY_MAKING   (the product helps them earn)
```

### The axes are independent

They frequently co-occur but neither implies the other:

- A budgeting app: motivation `MONEY`, value proposition `MONEY_SAVING`.
- A hobbyist print-on-demand tool: motivation `CREATIVITY`, value proposition
  `MONEY_MAKING`.

The second case is the one that matters: a user acting from creative motivation
can still be served by a money-making product, and collapsing the two axes would
make that opportunity invisible.

### General rule

**Motivation is about the user. Value proposition is about the product.** This
rule applies to every pair that looks superficially duplicated across §3.3 and
§3.5, not only to this one.

## 14. Taxonomy governance — closed enums vs extensible registries

**Resolves A-07.**

### 14.1 The principle

**Closed enum** — use only where semantic stability and exhaustive interpretation
are required. A closed enum is one that code branches on exhaustively, where an
unhandled value is a bug rather than a gap.

**Extensible registry** — use for domain taxonomies expected to evolve. Registry
values are data, not code.

**Why this matters here specifically:** the Opportunity Research Engine must
support product categories, motivations and channels that do not exist yet. If
those live in database enums, every new concept requires a migration — and a
system that needs a migration to describe a new kind of product will stop
describing new kinds of products.

### 14.2 Closed enums

| Enum | Defined in |
|------|-----------|
| `ClaimType` | §7 |
| `MarketScope.type` | §4.1 |
| Demand signal family | §3.6 |
| `EvidenceLevel` (categorical, 0–5) | `evidence-confidence-framework-v1.md` §2 |
| `ResearchSessionStatus` | §15 |
| Lifecycle/status values generally | wherever exhaustive branching is required |

Changing any of these is a material semantic change: new ontology version, plus
an ADR where architectural.

### 14.3 Extensible registries

| Registry | Defined in |
|----------|-----------|
| Market Type | §3.1 |
| Product Type | §3.2 |
| User Motivation | §3.3 |
| User Behavior | §3.4 |
| Value Proposition | §3.5 |
| Demand signal type (within a family) | §3.6 |
| Retention Mechanism | §3.7 |
| Monetization Model | §3.8 |
| Distribution Channel | §3.9 |
| Opportunity Risk | §3.10 |
| Region (`RegionId`) | §4.3 |

The V1/V1.1/V2 values are the **initial canonical registry entries**, not
immutable database enums.

### 14.4 Registry entry contract

Every registry entry should eventually carry:

| Field | Purpose |
|-------|---------|
| stable identifier | Never reused, never renamed. This is what is persisted |
| canonical name | Human-readable label |
| description | What it means, so classification is consistent |
| version | When the entry's meaning changed |
| status | `active` / `deprecated` |
| aliases | Where appropriate, for extraction and matching |

Two consequences worth stating:

- **Deprecation, not deletion.** A deprecated entry stops being offered for new
  classification but keeps resolving for historical records. Deleting an entry
  would make past classifications unreadable.
- **The stable identifier is what gets stored.** Storing the display name means a
  rename silently rewrites history.

### 14.5 Not implemented here

**No registry is implemented in this mission.** Only the contract is documented.
Registry storage, seeding and administration are Mission 0.2 or later, and the
storage ADR must honour §14.3: taxonomy values are rows, not enum types.

## 15. `ResearchSessionStatus` — CLOSED enum

Canonicalizes the lifecycle already documented in
`services/research-orchestrator/README.md` (Mission 0.1) into the UPPERCASE form
required for a persisted enum. No new state is invented.

```text
PENDING → PLANNING → COLLECTING → ANALYZING → SCORING → COMPLETED
                                                      ↘ FAILED
                                                      ↘ CANCELLED
```

| Value | Meaning |
|-------|---------|
| `PENDING` | Accepted, not yet planned |
| `PLANNING` | Building the research plan and budget |
| `COLLECTING` | Acquisition in progress |
| `ANALYZING` | NLP, market intelligence, competition |
| `SCORING` | Score families being computed |
| `COMPLETED` | Finished, whether coverage was complete or partial |
| `FAILED` | Could not produce a usable result |
| `CANCELLED` | Stopped on request |

### Two rules that prevent invented states

1. **Budget exhaustion is not a status.** A session that exhausts its budget
   reaches `COMPLETED` with a reduced Research Completeness and recorded gaps
   (ADR-006). Partial coverage is a *result*, not a failure mode.
2. **A session that finds nothing is `COMPLETED`, not `FAILED`.** Producing no
   opportunity is a valid research outcome. `FAILED` means the system could not
   run the research, not that the market was empty.

## 16. Open items

Not resolved by V2. None may be resolved by an implementer choosing a value.

| ID | Item | Status |
|----|------|--------|
| **D-03 / A-02 / A-03 / A-04** | Evidence aggregation formula, recency decay, independence threshold, contradiction penalties | **BLOCKED — hard blocker.** `services/scoring` cannot be implemented (`scoring-framework-v1.1.md` §13) |
| **A-12** | *New in V2.* Non-geographic (audience/segment) scoping and how it composes with `MarketScope` | OPEN — §4.8 |
| **A-01** | Sparse vs dense scoring-profile weight vectors | OPEN |
| **D-07** | Source registry and per-source legal review records | OPEN |
| **D-08** | Score recomputation policy — immutable snapshots or recomputed on new evidence | OPEN. Interacts with §12: an opportunity accumulates evidence across sessions |
| **D-12** | Embedding model versioning and re-embedding | OPEN |
| — | Opportunity identity resolution — when two discoveries are the same opportunity | OPEN — §12.3 |
| — | Region registry contents | OPEN — Data Engineering |

Resolved by V2: **D-01**, **A-06**, **A-11**, **A-05**, **A-07**, **A-08**.
