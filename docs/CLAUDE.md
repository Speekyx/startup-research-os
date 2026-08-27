# CLAUDE.md — Startup Research OS

Version: 1.2
Last amended: 2026-08-27 (Sprint 0 / Mission 0.1.2)

## Boot Sequence

Before performing any task, execute this reading order.

1. PROJECT_MANIFEST.md
2. docs/CLAUDE.md
3. docs/domain/opportunity-ontology-v2.md
4. docs/domain/scoring-framework-v1.1.md
5. docs/domain/evidence-confidence-framework-v1.md
6. docs/ai/llm-reasoning-rules.md
7. docs/data/data-principles.md
8. docs/data/data-retention-policy-v1.md
9. Relevant ADRs
10. Task-specific specifications

These documents are the authoritative source of truth.

**`opportunity-ontology-v1.md`, `opportunity-ontology-v1.1.md` and
`scoring-framework-v1.md` are superseded.** They remain in the repository as
historical records. Do not use them as the basis for implementation. See
`PROJECT_MANIFEST.md` §Superseded specifications.

Ontology V2 keeps V1.1's numbering for §1–§10, so an existing reference to
`opportunity-ontology-v1.1.md §N` with `N ≤ 10` resolves to the same rule in V2.

## Version history

| Version | Date | Change |
|---------|------|--------|
| 1.2 | 2026-08-27 | Boot sequence points to ontology V2; research lifecycle and taxonomy-governance invariants added |
| 1.1 | 2026-08-27 | Boot sequence points to domain V1.1; canonical domain invariants added (§Canonical invariants); tenancy rule added |
| 1.0 | — | Initial operating contract (was unversioned; versioning added in 1.1 per `specification-audit.md` §4 recommendation 8) |
## Purpose

This repository contains an evidence-driven AI Opportunity Research Engine for discovering, analyzing, scoring, validating, and planning digital product opportunities across B2B, B2C, entertainment, education, gaming, creator, hobby, utility, social, AI, and other markets.

This file is the top-level operating contract for Claude Code.

## Authoritative specifications

Before making architectural or implementation decisions, read the relevant documents in this order:

1. `docs/domain/opportunity-ontology-v2.md`
2. `docs/domain/scoring-framework-v1.1.md`
3. `docs/domain/evidence-confidence-framework-v1.md`
4. `docs/ai/llm-reasoning-rules.md`
5. `docs/data/data-principles.md`
6. `docs/data/data-retention-policy-v1.md`
7. Any relevant Architecture Decision Records (ADRs)
8. Any task-specific specification created later

These documents are authoritative unless a newer, explicitly versioned specification or ADR supersedes them.

## Canonical invariants

Added in 1.1. These are settled. Do not re-derive them, do not redefine them
locally, and do not resolve an apparent conflict with them by guessing.

### Claim taxonomy — exactly five values, UPPERCASE

```text
OBSERVED | INFERRED | PREDICTED | RECOMMENDED | HYPOTHESIS
```

`HYPOTHESIS` is mandatory and first-class. Definitions in
`opportunity-ontology-v2.md` §7. Closed enum: changing it requires a new
ontology version and an ADR.

### Confidence — unit interval

```text
0.0 <= confidence <= 1.0
```

Applies to `confidence`, `reliability`, `independence`, probability and signal
`value`, in the database, in API and domain contracts, and in ML calculations.
Presented to users as a percentage (`0.82` → `82%`).

**Scores are a different quantity** and keep 0–100 semantics. `evidence_level` is
an integer 0–5 and is never rescaled. Never conflate score, confidence,
probability and evidence strength — see `scoring-framework-v1.1.md` §4.1 and
`opportunity-ontology-v2.md` §9.

Naming rule: a field named `confidence` is always `[0,1]`; a field named
`*_score` is always `0–100`.

### Research lifecycle — canonical names

```text
Workspace → ResearchProject → ResearchSession → Evidence / Signals / Opportunities
                                    |
                                    +-- ResearchContext snapshot (immutable)
```

`ResearchSession` is the **only** persisted execution entity. `ResearchContext` is
an input specification (a value object), stored as an immutable snapshot on the
session. `ResearchProject` is the persistent grouping.

**`research run` is retired.** Use `ResearchSession` / `research_session_id`. In
historical documents and accepted ADRs, "research run" means `ResearchSession`
and `run_id` means `research_session_id`. See Ontology V2 §11.

### Market scope

`MarketScope` is a closed discriminated union on `type`:
`GLOBAL | REGION | COUNTRY | MULTI_COUNTRY`. Countries are ISO 3166-1 alpha-2;
regions come from a controlled registry. `COUNTRY` carries exactly one country,
`MULTI_COUNTRY` two or more. See Ontology V2 §4.

### Taxonomies — registries, not database enums

Product Type, Market Type, User Motivation, User Behavior, Value Proposition,
Retention Mechanism, Monetization Model, Distribution Channel, Risk and Region are
**extensible registries**. Adding an entry must never require a migration.

Closed enums are only: `ClaimType`, `MarketScope.type`, demand signal family,
`EvidenceLevel`, `ResearchSessionStatus`, and lifecycle values requiring
exhaustive branching. See Ontology V2 §14.

### Tenancy — workspace-scoped

The tenant boundary is the **Workspace**. Every primary domain resource carries
`workspace_id`, propagated explicitly through every service call, every Celery
task payload, every cache key, every vector-store filter and every log line.

`workspace_id` is never inferred, never defaulted in service code, never
reconstructed from another field. A missing `workspace_id` is an error in every
environment. See ADR-005.

### Jobs — Celery over Redis

All asynchronous work runs through Celery with Redis as broker. There is no Node
worker tier. Delivery is at-least-once, so every job must be idempotent. See
ADR-004.

### LLM access — through the gateway only

No business service imports a provider SDK. Services request a logical tier
(`FAST_MODEL`, `BALANCED_MODEL`, `STRONG_MODEL`, `EMBEDDING_MODEL`), never a
provider or a model name. See ADR-006.

### Blocked work

**`services/scoring` must not be implemented** until
`docs/domain/evidence-aggregation-framework-v1.md` exists and is authorized.
Do not invent the Evidence Score formula, recency decay parameters, independence
thresholds or contradiction penalties. See `scoring-framework-v1.1.md` §13.

## Core principles

- Evidence before conclusions.
- Problem-first is valid, but not mandatory.
- Desire, curiosity, entertainment, creativity, learning, competition, social interaction, and other motivations are first-class opportunity drivers.
- Never treat an LLM opinion as observed market evidence.
- Distinguish observed facts, inferred signals, predictions, and recommendations.
- Preserve provenance for important data.
- Preserve uncertainty and confidence.
- Do not silently redefine domain concepts.
- Do not silently change architecture.
- Prefer small, testable, reversible changes.
- Avoid unnecessary complexity and premature microservices.
- Security, privacy, legal constraints, cost, and data quality are first-class concerns.

## Before implementation

For every non-trivial task:

1. Inspect the repository.
2. Read the relevant specifications and ADRs.
3. Identify dependencies and existing contracts.
4. State any ambiguity or contradiction before implementing.
5. Define acceptance criteria.
6. Implement the smallest coherent change.
7. Add or update tests.
8. Run relevant checks.
9. Update documentation when behavior or contracts change.
10. Summarize assumptions, evidence, tests, and remaining risks.

## Change control

If a requested change conflicts with an authoritative specification:

- Do not silently override the specification.
- Explain the conflict.
- Propose the smallest specification or ADR change needed.
- Wait for explicit authorization before changing foundational behavior.

If a concept must evolve, create a new version rather than mutating history without traceability.

## Evidence discipline

Any research claim presented by the product should, where technically possible, retain:

- source
- source type
- observation time
- extraction method
- provenance
- evidence level
- reliability
- independence
- confidence
- relevant raw/reference identifier

Copied, duplicated, or derivative content must not be counted as independent evidence.

## LLM discipline

LLMs are reasoning and synthesis components, not sources of truth.

When evidence is insufficient, output a hypothesis or uncertainty state rather than inventing a fact.

Never fabricate:

- sources
- metrics
- users
- prices
- market sizes
- competitor facts
- API results
- citations
- research outcomes

## Data collection

Use lawful, permitted, and technically appropriate acquisition methods. Respect source terms, robots directives where applicable, rate limits, authentication requirements, privacy constraints, and platform policies. Do not bypass access controls.

API keys and secrets must never be committed to the repository.

## Versioning

Foundational specifications use explicit versions in the filename, for example:

- `opportunity-ontology-v2.md` (current) — supersedes `opportunity-ontology-v1.1.md`
- `scoring-framework-v1.1.md` (current) — supersedes `scoring-framework-v1.md`
- `evidence-confidence-framework-v1.md` (current)
- `data-retention-policy-v1.md` (current)

Material changes should create a new version and, when architectural, an ADR.

A superseded version is **never deleted**. It is retained as a historical record,
marked as superseded in `PROJECT_MANIFEST.md`, and its successor states in its
own §0 exactly what changed and under whose authority.

## Definition of done

A task is not complete merely because code exists.

It is complete when:

- behavior matches the specification,
- tests cover important behavior,
- failure modes are considered,
- observability is adequate,
- documentation/contracts are current,
- relevant quality checks pass,
- no known critical regression remains.
