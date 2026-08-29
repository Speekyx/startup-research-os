# PROJECT MANIFEST — Startup Research OS

Version: 1.3
Status: Foundation
Owner: Speekyx (GitHub: `@Speekyx`)
Repository: startup-research-os
Last amended: 2026-08-29 (Sprint 0 / Mission 0.4)

---

# Version History

This manifest is amended in place with an explicit version bump and a changelog
entry. Git history plus this section provide the traceability that
`docs/CLAUDE.md` §Change control requires.

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
3. docs/domain/opportunity-ontology-v2.md
4. docs/domain/scoring-framework-v1.1.md
5. docs/domain/evidence-confidence-framework-v1.md
6. docs/ai/llm-reasoning-rules.md
7. docs/data/data-principles.md

Additionally authoritative:

- docs/data/data-retention-policy-v1.md
- docs/ai/evaluation-framework-v1.md (added in 1.3)
- Accepted ADRs in docs/architecture/adr/

No implementation may silently contradict them.

## Superseded specifications

The following are **historical records**, retained for traceability. They are no
longer current and must not be used as the basis for implementation:

- `docs/domain/opportunity-ontology-v1.md` — superseded by V1.1
- `docs/domain/opportunity-ontology-v1.1.md` — superseded by V2
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