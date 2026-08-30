# PROJECT MANIFEST — Startup Research OS

Version: 1.12
Status: Foundation
Owner: Speekyx (GitHub: `@Speekyx`)
Repository: startup-research-os
Last amended: 2026-08-30 (Sprint 1 / Mission 1.9.2)

---

# Version History

This manifest is amended in place with an explicit version bump and a changelog
entry. Git history plus this section provide the traceability that
`docs/CLAUDE.md` §Change control requires.

## 1.12 — 2026-08-30 (Sprint 1 / Mission 1.9.2)

Authorized by the Mission 1.9.2 brief §32 (documentation), §3 (a new review
version rather than a rewrite) and §10 (gap analysis before the profile changed).
Additive: reviews 1 and 2 are untouched and no verdict moved.

| Change | Section | Authority |
|--------|---------|-----------|
| **A source has a concrete authorized resource for the second time** | Product Shape | Mission 1.9.2 §7, §22. GDELT review 3 authorises `web-ngrams/1gram` and `web-ngrams/2gram` over a reviewed `DATASET_DOWNLOAD` route on one directory of `data.gdeltproject.org`. `context.datasets` had been empty since Mission 1.7, so every GDELT resource failed closed — correctly, on a question nobody had answered. **No collector was written, none is enabled, and zero GDELT records exist** |
| **Resource-ready is a fourth fact, separate from eligible, implemented and enabled** | Forbidden During Foundation | Mission 1.9.2 §23. A source can pass the eligibility gate while every resource it could ask for is refused, and for two missions "eligible" was the most specific word available for GDELT in exactly that state. `sros-source readiness` derives all four and stores none — a persisted copy of a derivation is the thing `source-registry-v1.md` §3 refuses for eligibility |
| **How much became a governance question, alongside what** | Engineering Principles | Mission 1.9.2 §15. GDELT publishes two files every fifteen minutes since 2019 and its terms limit none of it, so a reviewed ceiling exists in configuration where it can be checked (`max_files_per_job`), and a bound with no stated basis is refused at load time. **`None` means no ceiling was reviewed, not that any size is fine** — every earlier source is in that state, and spelling it `unlimited` would turn an unasked question into an answer |
| **Two silent holes in the resource gate were closed** | Engineering Principles | Mission 1.9.2 §22. An **unestablished rights basis** had been checked only inside the licence-allowlist rule, so a descriptor with no basis passed for every source enumerating no licences — including GDELT, the one source authorised by a direct grant. And `require_dataset_family` refused a resource that could not say what it is while admitting one that said something nobody had reviewed. Both were reachable only by a hand-made descriptor, which is the standing the transport's host check already has |
| **The DOC API route is deferred, not withdrawn** | Blocked work | Mission 1.9.2 §24. **H-27 is still open** and no timeline envelope has ever been observed. The profile, the capture script and the response-contract document are all kept, because deleting them would make a later un-deferral look like a new approval. **H-28 is resolved** in both halves: the model in Mission 1.9.1, the entries here |
| **A first-party claim from Mission 1.9.1 was corrected** | Authoritative Documents | Mission 1.9.2 §4. GDELT does ask researchers to use "these ngram files instead of the search APIs", and Mission 1.9.1 read that as support for WEB-NGRAM. The sentence is in the post announcing the **quadgram** dataset and refers to that one, which review 3 rejects for carrying `title`, `img`, `url` and a per-document `DOCID`. The half that stands is GDELT describing its own legacy search infrastructure as struggling, which is why the DOC API is deferred |

## 1.11 — 2026-08-30 (Sprint 1 / Mission 1.8)

Authorized by the Mission 1.8 brief §3 (PyPI resolution), §4 (do not generalise
the exception) and §30 (documentation).

| Change | Section | Authority |
|--------|---------|-----------|
| **Silence is not permission became a mechanism** | Engineering Principles | Mission 1.8 §4, `source-registry-v1.md` §1 rule 8. The rule had existed as prose since Mission 1.0 and nothing read it; Mission 1.7 approved a source with four of the six materially required activities recorded `NOT_ADDRESSED`, on a review whose own notes described the basis as "the absence of a prohibition covering us plus the presence of a documented API". `validate_source_registry` now enforces it, and the check was written against the uncorrected catalog so it could be seen to fail first |
| **Three Mission 1.7 approvals were withdrawn on audit** | Product Shape | Mission 1.8 §3. `pypi`, `npm-registry` and `wikimedia-pageviews` each rested on silence rather than on a grant. Nothing about the platforms changed; the reading of their documents did. Five sources are approving where eight were, and every superseded review is preserved |
| **A second source became collector-eligible** | Product Shape | Mission 1.8 §7, §18. `gdelt` joins `world-bank`, `eurostat` and `fred` — the first non-economic source to reach the gate. Its one reviewed obligation moved from `HUMAN_CONFIRMATION`, which no verifier can clear, to a `CAPABILITY` checked by the generic attribution verifier Mission 1.4 built. **No gate was relaxed and no collector was implemented** |
| **The portfolio got narrower, and that is reported rather than smoothed** | Product Shape | Mission 1.8 §23. The economic share of approving sources rose from 37% to 60%, `entertainment` lost its only approving source, and eight of sixteen signal families now have none. A coverage number that improves when the governance behind it gets stricter is measuring the wrong thing |

## 1.10 — 2026-08-30 (Sprint 1 / Mission 1.7)

Authorized by the Mission 1.7 brief §48 (documentation) and §47 (schema changes
only after a gap analysis). Additive: no existing verdict was rewritten.

| Change | Section | Authority |
|--------|---------|-----------|
| **The source universe is 27 sources across 14 families, and consumer families are represented** | Product Shape | Mission 1.7 §50. Fourteen candidates were added and every one carries a current review; `gaming`, `creator` and `knowledge` are new families. The registry is no longer biased toward economic and developer data *as a catalog* |
| **Every consumer-facing family is registered and none is approving** | Product Shape | Mission 1.7 §40, and the finding the expansion exists to surface. `social`, `community`, `gaming`, `creator` and `app_store` hold eleven sources between them and not one reaches an approving state. That is a fact about platform terms, not about the review, and it is measurable rather than asserted: `source-signal-coverage-v1.md` is generated from the registry and CI-checked |
| **Source signal coverage is a first-class, non-scoring attribute** | Engineering Principles | Mission 1.7 §4, [ADR-017](docs/architecture/adr/ADR-017-source-signal-coverage.md). Sixteen signal families, each projecting the canonical `user_motivation` entry it corresponds to where one exists. Behaviour coverage reuses Ontology V2 §3.4 unchanged and defines no second vocabulary. **Coverage is potential, never permission, and carries no weight of any kind** — a numeric column here would be D-03 by another name |
| **The canonical taxonomies are fully seeded** | Extensible Taxonomies | Ontology V2 §3.3 and §3.4 specify seventeen motivations and seventeen behaviours as initial canonical entries; migration 0004 had loaded three and one. The remainder arrived in 0010 as `INSERT`s, which is what §14.3 requires of a registry |

**Unchanged, deliberately:** no collector was implemented, no platform content
was collected, no source became collector-eligible, evidence aggregation remains
uncalibrated and D-12 is still open.

## 1.9 — 2026-08-30 (Sprint 1 / Mission 1.6)

Authorized by the Mission 1.6 brief §61 (documentation) and §57 (schema changes
only where the existing semantics are genuinely incompatible).

| Change | Section | Authority |
|--------|---------|-----------|
| `docs/data/normalized-record-v1.md` added to the authoritative chain | Authoritative Documents | Mission 1.6 §5, §61. It defines the canonical observation every later stage reads, so every signal, claim and score eventually rests on it |
| `docs/data/world-bank-normalizer-v1.md` added to the authoritative chain | Authoritative Documents | Mission 1.6 §61. The reference adapter, and the record of what may and may not be inferred while producing a canonical observation |
| **The Raw to Normalized boundary exists, and one source crosses it** | Product Shape | Mission 1.6 §37, §38. `acquisition.normalized_records` holds six canonical numeric observations derived from the six real World Bank raw records. Every one carries complete lineage, its attribution obligation, a governance-resolved expiry and a structural quality state |
| **Normalizable is a fourth fact, separate from eligible, enabled and implemented** | Forbidden During Foundation | Mission 1.6 §36. A collector says what was fetched; a normalizer says what it structurally represents, and one never implies the other. Eurostat is collector-eligible with neither |

## 1.8 — 2026-08-30 (Sprint 1 / Mission 1.5)

Authorized by the Mission 1.5 brief §55 (documentation) and §51 (schema changes
only where the existing model cannot represent the requirement).

| Change | Section | Authority |
|--------|---------|-----------|
| `docs/data/world-bank-collector-v1.md` added to the authoritative chain | Authoritative Documents | Mission 1.5 §55. It is the reference architecture every later collector follows, and the record of what one source's data may be used for |
| **The first collector exists, and one source is collected from** | Forbidden During Foundation | Mission 1.5 §3, §48. Sprint 0 forbade collectors during foundation; Sprint 0 is complete and the governance chain that had to precede one (D-07, the compliance layer, the authorization boundary) is in place. **World Bank only.** Eurostat is collector-eligible and deliberately has no collector |
| **`acquisition.raw_records` is no longer empty** | Product Shape | Mission 1.5 §48, §49. One controlled acquisition of six World Bank observations. Every record carries complete provenance, a governance-derived expiry and its attribution obligation |

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
- docs/data/world-bank-collector-v1.md (added in 1.8)
- docs/data/normalized-record-v1.md (added in 1.9)
- docs/data/world-bank-normalizer-v1.md (added in 1.9)
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

## Status of this list (amended in 1.9)

Sprint 0 is complete, and two entries have been reached in Sprint 1. They are
recorded here rather than struck out, because what unblocked them is specific
and the rest of the list is still in force.

**Collectors.** One exists, for one source, since Mission 1.5. It became
permissible only after the chain that had to precede it: the Source Registry
(D-07, Mission 1.0), the review round that produced an approving verdict on
evidence (1.3), and the compliance capabilities and authorization boundary that
make a collector unable to run without a governance decision behind it (1.4). A
collector for a source that has not been through that chain is still forbidden,
and the orchestrator refuses to plan one.

**Normalization**, added in 1.9, is not on this list and never was: the
forbidden entry is *NLP pipelines*, and normalization is the stage before one.
It maps a source observation to a canonical structure and stops. It performs no
tokenization, no embedding, no classification and no clustering, and CI asserts
each of those mechanically rather than by review.

**Everything else on the list is unchanged.** NLP pipelines are blocked by D-12,
scoring algorithms by the absence of a `CALIBRATED` profile, and authentication
by ADR-005 being unimplemented.

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