# `packages/contracts` — Domain contracts (planned)

**Status:** **IMPLEMENTED** (Mission 0.2). Source of truth, generator, both
language bindings, and a shared conformance suite.
**Governed by:** [ADR-009](../../docs/architecture/adr/ADR-009-contract-first-code-generation.md)

```
schema/domain.v1.json          <- hand-edited SOURCE OF TRUTH
tools/generate.py              <- stdlib generator, deterministic, --check mode
src/generated/domain.ts        <- GENERATED
python/sros_contracts/generated/domain.py  <- GENERATED
schema/domain.v1.schema.json   <- GENERATED (JSON Schema, for OpenAPI/interop)
conformance/cases.json         <- shared cases, read by BOTH test suites
```

```bash
python packages/contracts/tools/generate.py          # regenerate
python packages/contracts/tools/generate.py --check  # CI: output is current
node --test --experimental-strip-types packages/contracts/test/conformance.test.ts
python infrastructure/scripts/run_python_tests.py
```

**How TS/Python agreement is proven:** both suites read the same
`conformance/cases.json`. If the implementations drift, one suite goes red.
19 TypeScript tests, 21 Python tests, same cases.

**Fully unblocked as of Mission 0.1.2.** C-02 and C-04 were resolved in Mission
0.1.1; D-01, A-06, A-11, A-05, A-07 and A-08 were resolved by **Opportunity
Ontology V2**. Every type listed below now has an authoritative definition.

## Responsibility

The **single source of truth** for every type that crosses a boundary: domain
enums, evidence and score shapes, and API request/response contracts.

One schema source generates both:

- TypeScript types for `apps/web`, `packages/ui`, and any Node service,
- Python Pydantic models for the FastAPI services.

## Why it exists

The specification audit found the same domain concept defined twice with
different values:

- **C-02** — the claims taxonomy had 4 categories in the ontology and 5 in the
  evidence framework.
- **C-04** — `confidence` was 0–1 in one document and 0–100 in another.

Both were the same failure: a domain concept maintained in two places. Both are
now resolved **in the specifications** (domain V1.1). This package is what stops
them recurring **in code** — documents drift, a generated type cannot.

## What it will contain

### Closed enums — A-07 resolved (Ontology V2 §14.2)

A change requires a new ontology version, and an ADR where architectural.

- `ClaimType` — `OBSERVED | INFERRED | PREDICTED | RECOMMENDED | HYPOTHESIS`
- `MarketScopeType` — `GLOBAL | REGION | COUNTRY | MULTI_COUNTRY`
- `EvidenceLevel` — integer 0–5
- `DemandSignalFamily` — `PAIN | DESIRE | BEHAVIORAL | MARKET`
- `ResearchSessionStatus` — `PENDING | PLANNING | COLLECTING | ANALYZING | SCORING | COMPLETED | FAILED | CANCELLED`
- `ScoreFamily` — the 5 families of `scoring-framework-v1.1.md` §2

### Extensible registries — NOT enums (Ontology V2 §14.3)

`MarketType`, `ProductType`, `UserMotivation`, `UserBehavior`,
`ValuePropositionType`, `DemandSignalType`, `RetentionMechanism`,
`MonetizationModel`, `DistributionChannel`, `RiskType`, `RegionId`.

**These are typed identifier references into a registry, not union types.**
The contracts package declares the *reference type* and the registry entry
shape; it does not enumerate the values, because enumerating them in a generated
type would recreate the migration-per-concept problem the split exists to
prevent.

> **Changed in Mission 0.1.2.** An earlier draft of this file listed
> `UserMotivation` as a closed enum. The A-07 resolution reclassifies it as a
> registry. That draft was a recommendation pending A-07, not an authorized
> decision; Ontology V2 §3.3 is now authoritative.

Registry entry shape (Ontology V2 §14.4): stable identifier, canonical name,
description, version, `active`/`deprecated` status, aliases. The **stable
identifier is what gets persisted** — storing a display name means a rename
silently rewrites history.

### Identifiers

Distinct types, not bare strings. A `WorkspaceId` accepted where an
`OpportunityId` was meant is a bug the type system should catch, and in a
multi-tenant system it is a bug with a data-leak shape.

```text
WorkspaceId
ResearchProjectId
ResearchSessionId
OpportunityId
EvidenceId
SignalId
```

`WorkspaceId` is required on every tenant-scoped contract (ADR-005).

### Core objects

| Type | Definition |
|------|-----------|
| `MarketScope` | Discriminated union on `type` (Ontology V2 §4), with the §4.4 invariants enforced as validators: `COUNTRY` exactly one code, `MULTI_COUNTRY` two or more, lists canonicalized, no empty lists |
| `ResearchContext` | **Value object**, not an entity (V2 §11.3). No identity, no lifecycle. Snapshotted onto a session |
| `ResearchSessionStatus` | Closed enum (V2 §15) |
| `Evidence` | Mandatory provenance, non-nullable by default (audit A-10), including `workspace_id` and `expires_at` |
| `Score` | Value, rationale, evidence refs, confidence, versions |
| `Confidence` | `float [0.0, 1.0]` |
| `Probability` | `float [0.0, 1.0]` |
| `EvidenceLevel` | Integer `0–5` |
| `LlmTier` | `FAST_MODEL \| BALANCED_MODEL \| STRONG_MODEL \| EMBEDDING_MODEL` (ADR-006). Provider and model names are configuration, never contract values |
| `Opportunity` | The V2 §6 aggregate |

### Deliberately not declared here

- **The opportunity ↔ session join shape.** Ontology V2 §12 states the
  requirement; Mission 0.2 chooses the relational form.
- **Registry contents.** Only the reference type and entry shape.
- **Anything depending on evidence aggregation.** D-03 is still blocked.

## Scale convention — SETTLED (`scoring-framework-v1.1.md` §4.1)

| Quantity | Storage / contract | Presentation |
|----------|--------------------|--------------|
| `confidence`, `reliability`, `independence`, probability, signal `value` | `float [0.0, 1.0]` | percentage, e.g. `82%` |
| Score families and dimension scores | `0–100` semantics | integer `0–100` |
| `evidence_level` | integer `0–5` | level label, never rescaled |

**Naming rule, enforced by validators:** a field named `confidence` is always
`[0,1]`; a field named `*_score` is always `0–100`.

The collision to guard: **`Model Confidence` is a score family on 0–100**, while
the `confidence` field on an evidence object or score component is on `[0,1]`.
Same word, different quantity. Declaring both here with their range validators is
the only reliable way to keep them apart.

## Rules

- No runtime logic. Types, schemas and validators only.
- No dependency on any service.
- Generated output is committed (so consumers do not need the generator) and
  marked `linguist-generated` in `.gitattributes`.
- A breaking contract change requires an ADR.
