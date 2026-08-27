# Opportunity Ontology V1.1

**Status:** Authoritative. Supersedes `opportunity-ontology-v1.md`.
**Date:** 2026-08-27
**Supersedes:** V1 (retained as a historical specification, not deleted)
**Authorized by:** Sprint 0 / Mission 0.1.1, §5

---

## 0. Changes from V1

V1.1 inherits V1 in full. Only the following changes are authorized, and only
they were applied. Section numbering is preserved so V1 references remain valid.

| Change | Section | Reason |
|--------|---------|--------|
| Claims taxonomy expanded from four to five values; `HYPOTHESIS` added as first-class | §7 | Resolves audit **C-02** — V1 §7 listed four categories while `evidence-confidence-framework-v1.md` §8 listed five, and its §9 anti-hallucination rule depends on `HYPOTHESIS` existing |
| Claim values standardized to UPPERCASE canonical form | §7 | Resolves audit **C-02** — V1 used `Observed`, the evidence framework used `OBSERVED`. Both become a persisted enum |
| Explicit compatibility statement with Evidence & Confidence Framework V1 | §7 | Prevents the taxonomy from drifting again across two documents |
| Confidence representation stated explicitly | §9 (new) | Resolves audit **C-04** — aligns the ontology with `scoring-framework-v1.1.md` §4 |
| Ontology evolution section renumbered §8 → §10 | §10 | Consequence of adding §9 |

**No other change was made.** Motivation lists, product types, value
propositions, demand signals, retention mechanisms, monetization models,
distribution channels, risks, geographic dimensions and the behavioral loop are
identical to V1.

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

### 3.1 Market type

Examples:

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

### 3.2 Product type

Examples:

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

### 3.3 User motivation

First-class motivation categories include:

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

### 3.4 User behavior

Examples:

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

### 3.5 Value proposition

Examples:

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

### 3.6 Demand signals

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

### 3.7 Retention mechanisms

Examples:

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

### 3.8 Monetization models

Examples:

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

### 3.9 Distribution channels

Examples:

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

### 3.10 Risks

Examples:

- TECHNICAL_RISK
- DATA_DEPENDENCY
- PLATFORM_DEPENDENCY
- LEGAL_RISK
- COMPETITION_RISK
- ACQUISITION_RISK
- MONETIZATION_RISK
- RETENTION_RISK

## 4. Geographic market

Market analysis may be global, regional, country-level, or segment-level.

Relevant dimensions include:

- market size
- interest
- growth
- purchasing power
- competition
- local alternatives
- language
- payment methods
- distribution channels
- cultural factors
- regulatory factors

A global score must not erase meaningful country-level differences.

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
├── Market
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
└── Scores
```

> **Note (V1.1):** an `Opportunity` also belongs to a tenant boundary
> (`workspace_id`) per ADR-005. Tenancy is an architectural ownership concern,
> not an analytical dimension of the opportunity itself, so it is deliberately
> **not** added to this structure. The Workspace / Research Project /
> Research Session hierarchy is defined in ADR-005 and is scheduled for
> ontology V2 alongside `ResearchContext` (audit A-06 / D-01).

## 7. Claims taxonomy

**Changed in V1.1.** This section resolves audit finding C-02.

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
and the form used in every internal document. User-facing presentation may render
a localized or capitalized label, but the underlying value is the uppercase
token.

### `HYPOTHESIS` is mandatory and first-class

V1 omitted it. That omission was incoherent: `evidence-confidence-framework-v1.md`
§9 instructs the system, when a claim cannot be supported by collected evidence,
to "classify it as a hypothesis". Without `HYPOTHESIS` in the taxonomy there was
nowhere for such a claim to go, and the only remaining options were to fabricate
support or to drop the claim silently.

A system that cannot say *"this is a plausible idea we have not established"* will
eventually say something stronger than its evidence supports. `HYPOTHESIS` is the
release valve that makes the anti-hallucination rule implementable.

### These categories must not be conflated

In user-facing output, in API responses, in stored records, or in logs. A
`PREDICTED` value rendered indistinguishably from an `OBSERVED` one is a
specification violation regardless of whether the number happens to be correct.

### Compatibility with the Evidence & Confidence Framework

This taxonomy is **identical** to `evidence-confidence-framework-v1.md` §8. That
document remains authoritative for evidence levels, source reliability,
independence, recency and provenance. Where both documents mention claim types,
they now agree by construction.

`ClaimType` is a **closed enum**. Adding, removing or renaming a value is a
material semantic change and requires a new ontology version plus an ADR.

## 8. Important distinction

The system must distinguish observed facts, analytical inferences, model
predictions, system recommendations, and unsupported hypotheses, per §7.

These categories must not be conflated in user-facing output.

> V1 numbered this distinction §7 and the taxonomy was implicit in it. V1.1 makes
> the taxonomy explicit in §7 and retains this section as the behavioral rule.

## 9. Confidence representation

**New in V1.1.** Aligns the ontology with `scoring-framework-v1.1.md` §4 and
resolves audit finding C-04 at the ontology level.

Any confidence, reliability, independence or probability quantity attached to an
ontology object is represented internally as a **unit interval**:

```text
0.0 <= value <= 1.0
```

Presentation layers may render it as a percentage (`0.82` → `82%`).

**`confidence` and `score` are different concepts and must not be interchanged.**
See `scoring-framework-v1.1.md` §4.1 for the full distinction between score,
confidence, probability and evidence strength.

`evidence_level` remains an integer `0–5` and is never rescaled.

## 10. Ontology evolution

> Renumbered from V1 §8. Content unchanged apart from the version references.

V1.1 is the current baseline. Material semantic changes require V2 or an explicit
extension/ADR.

Do not silently add a new fundamental category if doing so changes scoring,
storage, or interpretation contracts.

### Known scheduled work for V2

Recorded here so it is not forgotten, and deliberately **not** resolved in V1.1:

- `ResearchContext` entity (audit A-06 / decision D-01) — referenced by the
  scoring framework but modeled nowhere.
- Workspace / Research Project / Research Session hierarchy (ADR-005).
- Naming reconciliation between "research run", "Research Session" and
  "ResearchContext" (audit A-11, opened in Mission 0.1.1).
- Which §3 lists are closed enums and which are open registries (audit A-07).
