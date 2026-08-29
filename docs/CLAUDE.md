# CLAUDE.md — Startup Research OS

Version: 1.9
Last amended: 2026-08-30 (Sprint 1 / Mission 1.5)

## Boot Sequence

Before performing any task, execute this reading order.

1. PROJECT_MANIFEST.md
2. docs/CLAUDE.md
3. docs/domain/opportunity-ontology-v2.1.md
4. docs/domain/scoring-framework-v1.1.md
5. docs/domain/evidence-confidence-framework-v1.md
6. docs/ai/llm-reasoning-rules.md
7. docs/data/data-principles.md
8. docs/data/data-retention-policy-v1.md
9. docs/data/source-registry-v1.md
10. docs/data/acquisition-authorization-v1.md
11. docs/data/world-bank-collector-v1.md
12. docs/domain/evidence-aggregation-framework-v1.md
13. docs/domain/claim-model-v1.md
14. docs/ai/evaluation-framework-v1.md
15. Relevant ADRs
16. Task-specific specifications

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
| 1.9 | 2026-08-30 | First collector recorded: World Bank only, gated by an AcquisitionAuthorizationContext; raw_records is no longer empty; collector boundary invariant added |
| 1.8 | 2026-08-29 | Compliance capabilities recorded: a condition is cleared by a verifier and by nothing else; two sources are collector-eligible; eligible / enabled / implemented separated (ADR-016) |
| 1.7 | 2026-08-29 | Source review round recorded: three sources APPROVED_WITH_CONDITIONS, none collector-eligible; conditional-eligibility rule added |
| 1.6 | 2026-08-29 | Boot sequence points to Ontology V2.1 and gains the Claim model; Claim invariant added; A-13 removed from blocked work (ADR-015) |
| 1.5 | 2026-08-29 | Boot sequence gains the evidence aggregation framework; evidence-aggregation invariant added; D-03 blocked-work entry rewritten as framework-resolved / parameters-uncalibrated (ADR-014) |
| 1.4 | 2026-08-29 | Boot sequence gains the source registry spec; source-governance invariant added; D-07 removed from blocked work (ADR-013) |
| 1.3 | 2026-08-29 | Boot sequence gains the evaluation framework; tenancy invariant records that row-level security is now enforced (ADR-012) |
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

**Two layers, since Mission 0.4 (ADR-012).** The explicit repository filter is
layer 1 and remains mandatory. PostgreSQL row-level security is layer 2, entered
through a transaction-local tenant context. Neither replaces the other: a
forgotten `WHERE` is caught by the policy, and a missing tenant context returns
no rows rather than wrong ones. Removing the explicit filter because RLS exists
is a regression, not a cleanup.

### Jobs — Celery over Redis

All asynchronous work runs through Celery with Redis as broker. There is no Node
worker tier. Delivery is at-least-once, so every job must be idempotent. See
ADR-004.

### LLM access — through the gateway only

No business service imports a provider SDK. Services request a logical tier
(`FAST_MODEL`, `BALANCED_MODEL`, `STRONG_MODEL`, `EMBEDDING_MODEL`), never a
provider or a model name. See ADR-006.

### Source governance — a gate, not a field

A source becomes collectable only by passing the eligibility gate in
`registry.source_eligibility`, never by any other route. Four rules follow, and
none of them is negotiable (`source-registry-v1.md` §1, ADR-013):

- **Public visibility is not permission.** Reachability is an access-profile
  fact; permission is a review fact; the gate requires the review.
- **Uncertainty is never permission.** Silent, unreachable or ambiguous terms
  produce `NOT_ADDRESSED` / `UNCLEAR` and leave the source `REQUIRES_REVIEW`.
  There is no path from *we could not check* to *we may proceed*.
- **An approval requires retrieved, authoritative evidence** — the source's own
  documents, operator correspondence or a recorded legal review. Never a blog
  post, a tutorial, a forum answer or model recall.
- **No credential is stored in the registry.** Access profiles carry
  configuration key names only.
- **`APPROVED_WITH_CONDITIONS` is not permission to run.** It says a collector
  MAY be designed. Every condition is a checkable row, and the gate blocks until
  all of them are satisfied — where satisfaction is environment state that a
  catalog can never assert about itself.
- **A condition is cleared by a verifier, and by nothing else** (Mission 1.4,
  ADR-016, `acquisition-authorization-v1.md`). A verification records which
  condition, which verifier, at which version, when, the result and why; a
  database trigger refuses `satisfied = TRUE` with no `SATISFIED` record behind
  it. There is no manual boolean, no catalog field and no migration that grants
  it. Results are `SATISFIED | UNSATISFIED | UNKNOWN | NOT_APPLICABLE`, only the
  first clears, and **`UNKNOWN` is never promoted**. No verifier can satisfy a
  `HUMAN_CONFIRMATION` condition, and none in this repository writes one.
- **Eligible, enabled and implemented are three facts.** After Mission 1.4
  `world-bank` and `eurostat` are collector-eligible in any environment where
  the capabilities are verified, and `fred` joins them wherever `FRED_API_KEY`
  is configured — it is design-eligible and blocked everywhere else, including
  CI. **None is enabled and none is implemented.** `sros-source enable` refuses a
  source with no collector, and the orchestrator blocks acquisition under
  `NO-COLLECTOR-IMPLEMENTED` rather than dispatching a job nothing can run.
- **A source-level approval is not a resource-level one.** Each dataset or
  series is authorised separately, and one whose licensing scope was never
  established is refused. A collector receives an
  `AcquisitionAuthorizationContext` or it receives nothing.

### Collection — one collector, and what bounds it

Since Mission 1.5 the World Bank Indicators collector exists
(`world-bank-collector-v1.md`). It is the reference architecture, and five rules
apply to it and to every collector that follows:

- **No authorization, no collection.** `collect` takes an
  `AcquisitionAuthorizationContext` as its first positional parameter, with no
  default and no overload that omits it. A collector that could build its own
  could approve itself.
- **Every resource passes `authorize_resource` before a socket opens**, and a
  refusal costs **zero** network calls.
- **No public signature accepts a URL.** A request names indicators, countries
  and years; the collector composes the path, and the host comes from the access
  profile the review approved. There is no fallback domain and redirects are not
  followed.
- **Retention and attribution come from governance**, not from the collector.
  `build_draft` has no parameter for either, so there is nothing to pass.
- **Exactly one file may import a network client**
  (`collection/transport.py`). The registry and compliance packages decide
  whether collection may happen and stay network-free.

Identity is three separate things and confusing any two is a defect:
`observation_key` says WHICH observation, `content_hash` says WHAT the source
said, and the record id follows from both. The retrieval time is in neither — it
would make every re-retrieval look like an upstream revision.

The registry is **global**: no `workspace_id`, no RLS policy, `SELECT` only for
the runtime role. It is administered by `sros-source`, never over HTTP.

This system is not a legal decision engine and its output is not legal advice.

### Claim — the unit evidence accumulates against

Since Mission 1.2 a **Claim** is a persisted entity (Ontology V2.1 §17,
`claim-model-v1.md`, ADR-015). Five rules follow:

```text
Workspace -> Opportunity -> Claim -> Evidence -> Aggregation
```

- **A Claim is not a `ClaimType`.** `ClaimType` is an epistemic category a claim
  carries; there are exactly five of them and none is an identity. A Claim is an
  assertion with a `ClaimId`.
- **A Claim is not an Opportunity.** One opportunity carries several assertions
  that do not stand or fall together; aggregating at the opportunity level
  averages away what the four masses preserve.
- **Identity is stable; statements are revised append-only.** An aggregation that
  evaluated revision 2 must still be able to read revision 2. The previous
  revision is never modified.
- **Temporality is declared on the Claim, never inferred from the source.** The
  claim names a `claim_feature`; the half-life lives in the profile.
- **`ClaimLifecycle` is editorial, never epistemic.** `ACTIVE` and `WITHDRAWN`
  only. There is no `VALIDATED`: evidence changes, and a lifecycle derived from
  it would freeze a conclusion the evidence no longer supports.

A claim is not owned by the session that first met it (Ontology V2 §12, applied
to Claim). Sessions produce observations; the same claim accumulates evidence
across many of them.

### Evidence aggregation — defined, and not calibrated

Since Mission 1.1 the aggregation algorithm is defined
(`evidence-aggregation-framework-v1.md`, ADR-014). Five rules follow, and none is
negotiable:

- **`q_i = min(components)`.** The weakest required dimension, never a weighted
  average. A high value must not compensate for a critical weak one.
- **Duplicates cannot multiply.** Records sharing an origin form one group and
  the strongest member counts. Unknown provenance forms **one** group per claim
  and direction — it is never promoted to independent.
- **Support and contradiction are aggregated separately** and decomposed into
  four masses that sum to 1. There is no flat contradiction penalty.
- **No invented parameters.** No per-platform reliability coefficient, no
  universal half-life. A temporally sensitive claim with no authorised half-life
  reports `MISSING_TEMPORAL_PARAMETER` and produces no score.
- **`EvidenceScore` is a score, not a probability.** `82` does not mean an 82%
  chance the claim is true, and it is never published without
  `support_strength`, `contradiction_strength`, `conflict_mass` and
  `uncertainty_mass`.

Source POLICY status (Mission 1.0) is not epistemic reliability. An `APPROVED`
source does not produce better evidence.

### Blocked work

**`services/scoring` must not be implemented for production research.** D-03 is
resolved at the *framework* level only: the equations exist, their parameters
were never fitted, and no `CALIBRATED` profile exists. Framework Defined and
Profile Calibrated are separate gates (ADR-014, framework §14). An
`UNCALIBRATED` profile may be run only for synthetic or experimental work, and
only when explicitly labelled as such.

Do not invent a half-life, a damping constant, a per-source weight or a
contradiction penalty to make the engine produce a number. Failing closed is the
designed behaviour, not a gap to fill.

**No collector may be implemented for a source that is not collector-eligible.**
D-07 is resolved and the registry exists. Two sources pass the gate; one has a
collector. The block is per source, and the orchestrator reports each by name
under one of two gates — `SOURCE-REGISTRY-GATE` when nothing is eligible,
`NO-COLLECTOR-IMPLEMENTED` when something is and nothing implements it.

Mission 1.4's debt is paid: `test_collector_conformance.py` asserts structurally
that the collector has no path to a URL outside `authorize_resource`, so the
guarantee is observed rather than architectural.

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
- `evaluation-framework-v1.md` (current)

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
