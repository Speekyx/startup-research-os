# PROJECT MANIFEST — Startup Research OS

Version: 1.7
Status: Foundation
Owner: Speekyx (GitHub: `@Speekyx`)
Repository: startup-research-os
Last amended: 2026-08-29 (Sprint 1 / Mission 1.4)

---

# Version History

This manifest is amended in place with an explicit version bump and a changelog
entry. Git history plus this section provide the traceability that
`docs/CLAUDE.md` §Change control requires.

## 1.7 — 2026-08-29 (Sprint 1 / Mission 1.4)

Authorized by the Mission 1.4 brief §41 (documentation) and §40 (schema
changes only where the existing model cannot express the requirement).

| Change | Section | Authority |
|--------|---------|-----------|
| `docs/data/acquisition-authorization-v1.md` added to the authoritative chain | Authoritative Documents | Mission 1.4 §41. `source-registry-v1.md` §4 requires conditions to be checkable and specifies no mechanism for checking one; this document specifies it, and every future collector is gated by it |
| **Collector eligibility is reachable, and two sources reach it** | Blocked work | Mission 1.4 §23, [ADR-016](docs/architecture/adr/ADR-016-compliance-capabilities-and-acquisition-authorization.md). `world-bank` and `eurostat` pass the gate in a verified environment; `fred` is design-eligible and blocked on a runtime credential. **No collector is implemented and none is enabled** — three separate facts, and the block on writing a collector moved from "no source has passed" to "this specific source has not" |

## 1.6 — 2026-08-29 (Sprint 1 / Mission 1.2)

Authorized by the Mission 1.2 brief §3 (create Ontology V2.1) and §49
(documentation). A-13 was explicitly authorised for resolution.

| Change | Section | Authority |
|--------|---------|-----------|
| `docs/domain/opportunity-ontology-v2.1.md` becomes the current ontology | Authoritative Documents | Mission 1.2 §3. V2 is retained as a historical record and is not deleted; V2.1 inherits §1–§16 unchanged and adds §17 (Claim) |
| `docs/domain/claim-model-v1.md` added to the authoritative chain | Authoritative Documents | Mission 1.2 §49. The Claim is the unit `evidence-aggregation-framework-v1.md` operates on, so its model is authoritative by construction |
| **A-13 resolved** | Blocked work | Mission 1.2 §44, [ADR-015](docs/architecture/adr/ADR-015-claim-persistence-and-versioning.md). Claim exists as a persisted entity with stable identity and append-only revisions; evidence references it. **Production scoring remains unavailable**: no `CALIBRATED` profile exists, which is a separate gate |

## 1.5 — 2026-08-29 (Sprint 1 / Mission 1.1)

Authorized by the Mission 1.1 brief §48 (documentation) and §40 (D-03 resolution
criteria).

| Change | Section | Authority |
|--------|---------|-----------|
| `docs/domain/evidence-aggregation-framework-v1.md` added to the authoritative chain | Authoritative Documents | Mission 1.1 §48. `scoring-framework-v1.1.md` §13 names this document as the precondition for `services/scoring`, so it is authoritative by construction |
| **D-03 resolved at the FRAMEWORK level** | Blocked work | Mission 1.1 §40, [ADR-014](docs/architecture/adr/ADR-014-evidence-aggregation-reference-implementation.md). The algorithm is defined and has a reference implementation. **No parameter was calibrated**, no profile is `CALIBRATED`, and `services/scoring` stays unavailable for production research. Framework Defined and Profile Calibrated are separate gates |
| **A-13 opened** | Blocked work | Aggregation is claim-centric and no Claim entity exists in the ontology or the schema. Recorded rather than resolved: it requires an ontology version and an ADR |

## 1.4 — 2026-08-29 (Sprint 1 / Mission 1.0)

Authorized by the Mission 1.0 brief §40 (documentation) and §45 (decision
resolution). Additive, plus one resolution.

| Change | Section | Authority |
|--------|---------|-----------|
| `docs/data/source-registry-v1.md` added to the authoritative chain | Authoritative Documents | Mission 1.0 §40. `data-principles.md` §13 requires a pre-integration record for every source and specifies no structure for it; this document specifies it, and every future collector is gated by it |
| **D-07 resolved** | Blocked work | Mission 1.0 §45. The source registry and its per-source review records now exist ([ADR-013](docs/architecture/adr/ADR-013-source-registry-governance.md)). Resolution of the blocker is not approval of any source: thirteen candidates are registered and zero are collector-eligible |

## 1.3 — 2026-08-29 (Sprint 0 / Mission 0.4)

Authorized by the Mission 0.4 brief §24 (create the evaluation framework) and
§39 (documentation). Additive only: no existing statement is changed.

| Change | Section | Authority |
|--------|---------|-----------|
| `docs/ai/evaluation-framework-v1.md` added to the authoritative chain | Authoritative Documents | Mission 0.4 §24. `llm-reasoning-rules.md` §10 requires evaluation datasets and defines none; this document specifies them, so leaving it outside the chain would put an authoritative-by-nature document where the boot sequence never looks |

## 1.2 — 2026-08-27 (Sprint 0 / Mission 0.1.2)

Authorized by explicit human decision. See
`docs/architecture/mission-0.1.2-decisions.md`.

| Change | Section | Authority |
|--------|---------|-----------|
| Authoritative ontology becomes **V2** | Authoritative Documents | Ontology V2 — resolves D-01, A-06, A-11, A-05, A-07, A-08 |
| Research lifecycle named: `ResearchProject` → `ResearchSession` (+ `ResearchContext` snapshot) | Product Shape | Ontology V2 §11 |
| `research run` retired as a domain term | Product Shape | Ontology V2 §11.5 |
| Domain taxonomies split into closed enums and extensible registries | Engineering Principles | Ontology V2 §14 |

## 1.1 — 2026-08-27 (Sprint 0 / Mission 0.1.1)

Authorized by explicit human decision. See
`docs/architecture/mission-0.1.1-decisions.md` for the full register.

| Change | Section | Authority |
|--------|---------|-----------|
| **BullMQ removed** from the locked stack; **Celery** added as the job framework | Technology Stack | ADR-004 — resolves the blocking contradiction C-01 |
| Multi-tenancy stated as a foundational property | Product Shape (new) | ADR-005 |
| Authoritative document chain points to ontology **V1.1** and scoring **V1.1** | Authoritative Documents | Mission 0.1.1 §7–8 |
| Data Retention Policy V1 added as authoritative | Authoritative Documents | Mission 0.1.1 §12 |
| LLM access declared provider-agnostic | Technology Stack | ADR-006 |
| Deployment declared local-first | Technology Stack | ADR-007 |

## 1.0 — initial foundation manifest

---

# Vision

Startup Research OS is an AI-powered Opportunity Research Engine.

Its purpose is to discover, analyze, score, validate and plan digital product opportunities across every major market.

The system must support opportunities in:

- B2B
- B2C
- Gaming
- Entertainment
- Education
- AI
- Creator Economy
- Developer Tools
- Social Products
- Utility Apps
- Marketplaces
- Hobby Products

The system is evidence-driven.

It is NOT a random startup idea generator.

---

# Mission

Transform public market signals into structured opportunity intelligence.

Pipeline:

Raw Signals
→ Data Collection
→ Normalization
→ NLP
→ Signal Extraction
→ Opportunity Discovery
→ Evidence Evaluation
→ Scoring
→ Market Intelligence
→ Competition Analysis
→ Execution Planning

---

# Success Criteria

The platform must eventually be able to:

- discover opportunities automatically
- explain why an opportunity exists
- distinguish observations from hypotheses
- rank opportunities
- adapt scoring to different markets
- generate MVP plans
- generate Go-To-Market strategies
- continuously improve from collected data

---

# Engineering Principles

Every implementation must follow these principles.

## Evidence First

Evidence before conclusions.

## Explainability

Every important score should be explainable.

## Version Everything

Foundational specifications are versioned.

## Modular Design

Every service must have a single responsibility.

## Extensible Taxonomies

Domain taxonomies are registries, not database enums. Adding a product type, a
motivation or a distribution channel must never require a schema migration.
Closed enums are reserved for values that code branches on exhaustively.
See Ontology V2 §14.

## Testability

Every important behavior must be testable.

## Security First

Security cannot be postponed.

## Cost Awareness

Choose the simplest reliable solution before expensive AI calls.

---

# Authoritative Documents

These documents define the project.

1. PROJECT_MANIFEST.md
2. docs/CLAUDE.md
3. docs/domain/opportunity-ontology-v2.1.md
4. docs/domain/scoring-framework-v1.1.md
5. docs/domain/evidence-confidence-framework-v1.md
6. docs/ai/llm-reasoning-rules.md
7. docs/data/data-principles.md

Additionally authoritative:

- docs/data/data-retention-policy-v1.md
- docs/ai/evaluation-framework-v1.md (added in 1.3)
- docs/data/source-registry-v1.md (added in 1.4)
- docs/domain/evidence-aggregation-framework-v1.md (added in 1.5)
- docs/domain/claim-model-v1.md (added in 1.6)
- docs/data/acquisition-authorization-v1.md (added in 1.7)
- Accepted ADRs in docs/architecture/adr/

No implementation may silently contradict them.

## Superseded specifications

The following are **historical records**, retained for traceability. They are no
longer current and must not be used as the basis for implementation:

- `docs/domain/opportunity-ontology-v1.md` — superseded by V1.1
- `docs/domain/opportunity-ontology-v1.1.md` — superseded by V2
- `docs/domain/opportunity-ontology-v2.md` — superseded by V2.1. V2.1 inherits
  §1–§16 unchanged and refers to V2 for their text, so a reference to
  `opportunity-ontology-v2.md §N` with `N <= 16` still resolves correctly
- `docs/domain/scoring-framework-v1.md` — superseded by V1.1

Historical reports and audits (`docs/architecture/mission-0.1-report.md`,
`docs/architecture/specification-audit.md`) legitimately reference V1 and the
pre-1.1 stack. They are records of what was true when they were written and are
not rewritten.

---

# Technology Stack

Frontend:
- Next.js
- TypeScript
- Tailwind
- shadcn/ui

Backend:
- FastAPI
- Python

Jobs and asynchronous work (amended in 1.1 — ADR-004):
- Celery
- Redis as broker and result backend

Infrastructure:
- Docker
- Docker Compose (local-first — ADR-007)
- Turborepo
- pnpm

Storage:
- PostgreSQL
- Redis
- Qdrant

Data:
- Playwright (Python API)

AI access (ADR-006):
- Provider-agnostic LLM Gateway
- No business service depends on a provider-specific SDK
- Logical tiers: FAST_MODEL, BALANCED_MODEL, STRONG_MODEL, EMBEDDING_MODEL

ML:
- BGE-M3
- HDBSCAN

## Runtime boundaries

TypeScript is used for the frontend only (`apps/web`, `packages/*`).

Python is the primary backend, data, jobs and ML runtime. There is no Node
worker tier.

**Removed in 1.1:** BullMQ. It is a Node-only library and could not be consumed
by the Python workers that the ML stack requires. See ADR-004 for the full
rationale.

---

# Product Shape

Added in 1.1.

Startup Research OS is a **multi-tenant SaaS**, designed as such from the
foundation. The tenant boundary is the **Workspace**:

```text
User → Workspace → ResearchProject → ResearchSession → Opportunity
                                          |
                                          +-- ResearchContext snapshot
```

Every primary domain resource carries `workspace_id`. Authentication and
authorization are not yet implemented; the contracts that allow them to be added
without a data migration are established in ADR-005.

**Canonical lifecycle names (Ontology V2 §11).** `ResearchProject` is the
persistent research objective. `ResearchSession` is the **only** persisted
execution entity. `ResearchContext` is an input specification stored as an
immutable snapshot on the session, not an independent entity. The term
`research run` is retired; historical documents that use it mean
`ResearchSession`.

---

# Repository Philosophy

The repository should always remain understandable.

Folders must have clear ownership.

Documentation is considered production code.

Every architectural decision must eventually be documented through ADRs.

---

# Forbidden During Foundation

Until Sprint 0 is complete:

Do NOT implement:

- business logic
- collectors
- NLP pipelines
- scoring algorithms
- dashboards
- authentication features
- monetization
- user-facing workflows

Foundation only.

---

# Required Mindset

Act like a long-term engineering team.

Prioritize maintainability over speed.

When uncertain:

- inspect
- explain
- propose
- document

Never silently invent architecture.