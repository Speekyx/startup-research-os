# `docs/domain/` — Domain specifications

**Authoritative.** These define the vocabulary and the analytical model of the
system. Code conforms to them; they do not conform to code.

| Document | Status | Defines |
|----------|--------|---------|
| `opportunity-ontology-v2.1.md` | **Current** | V2 plus the Claim entity (§17). Resolves A-13 |
| `claim-model-v1.md` | **Current** | The Claim: identity, statement revision, temporality, origin, lifecycle, evidence relationship |
| `opportunity-ontology-v2.md` | Superseded by V2.1 | Historical record. §1–§16 are unchanged and V2.1 refers to it for them |
| `scoring-framework-v1.1.md` | **Current** | The five score families, dimensions, profiles, normalization, numeric representation |
| `evidence-confidence-framework-v1.md` | **Current** | Evidence levels, reliability, independence, recency, provenance, claim types |
| `evidence-aggregation-framework-v1.md` | **Current** | How several Evidence records combine into support, contradiction and an Evidence Score. Resolves D-03 at the framework level |
| `evidence-aggregation-calibration-plan-v1.md` | Plan | How the parameters will be fitted once labelled data exists. **Not executed** |
| `evidence-aggregation-sensitivity-v1.md` | **Generated** | Synthetic behaviour analysis. Rendered from the reference implementation and checked in CI |
| `evidence-schema-gap-analysis-v1.md` | Analysis | What `scoring.evidence` would need. **No migration was written** |
| `evidence-schema-gap-analysis-v1.1.md` | **Current** | Resolution appendix. Both Mission 1.1 incompatibilities are closed |
| `opportunity-ontology-v1.1.md` | Superseded by V2 | Historical record |
| `opportunity-ontology-v1.md` | Superseded by V1.1 | Historical record |
| `scoring-framework-v1.md` | Superseded by V1.1 | Historical record |

Each successor document opens with a §0 changelog stating exactly what changed and
under whose authority. Nothing else was altered.

**Ontology V2 keeps V1.1's numbering for §1–§10**, so an existing reference to
`opportunity-ontology-v1.1.md §N` with `N ≤ 10` resolves to the same rule in V2.
New material is §11–§16.

## Rules

1. **Never edit in place to change meaning.** A material semantic change creates
   a new version (`-v2.md`) and, when architectural, an ADR
   (`docs/CLAUDE.md` §Versioning).
2. **Never silently add a fundamental category** if it changes scoring, storage
   or interpretation contracts (`opportunity-ontology-v2.md` §10). Note that this
   binds **closed enums**; registry entries are added through the registry's own
   versioned process (§14) — which is exactly why the split exists.
3. **These documents are the source for `packages/contracts`.** A domain enum
   declared anywhere else is drift.

## Known open items

### Resolved in Mission 0.1.1

- **C-02** — claims taxonomy. Now five canonical UPPERCASE values including
  `HYPOTHESIS`, identical in `opportunity-ontology-v1.1.md` §7 and
  `evidence-confidence-framework-v1.md` §8.
- **C-04** — numeric scales. Confidence on `[0,1]`, scores on `0–100`,
  `evidence_level` integer `0–5`. See `scoring-framework-v1.1.md` §4.1.

### Resolved in Mission 1.2

- **A-13** — the **Claim entity**. Ontology V2.1 §17 defines it, `claim-model-v1.md`
  specifies it, migration `0005` persists it, and evidence now references a claim
  rather than an opportunity. The two Mission 1.1 schema incompatibilities are
  closed with it (`evidence-schema-gap-analysis-v1.1.md`).

  Resolving A-13 gave aggregation a unit to operate on. It calibrated nothing:
  **production scoring remains unavailable** for the separate reason that no
  `CALIBRATED` profile exists.

### Resolved in Mission 1.1

- **D-03 / A-02 / A-03 / A-04 — at the framework level only.**
  `evidence-aggregation-framework-v1.md` defines the aggregation formula, the
  recency **function**, provenance-based independence handling and continuous
  contradiction. It fits **no parameter**: no half-life is assigned, no profile
  is `CALIBRATED`, and **`services/scoring` remains unavailable for production
  research**. Framework Defined and Profile Calibrated are separate gates
  (ADR-014).

### Resolved in Mission 0.1.2 (Ontology V2)

- **D-01 / A-06** — `ResearchContext` formally defined as an input value object
  snapshotted onto a `ResearchSession` (V2 §11.3).
- **A-11** — `ResearchSession` is the canonical persisted execution;
  `research run` retired (V2 §11.5).
- **A-05** — `MarketScope` discriminated union (V2 §4).
- **A-07** — closed enums vs extensible registries (V2 §14).
- **A-08** — `MONEY` (motivation) vs `MONEY_MAKING` (value proposition) (V2 §13).

### Still open — recorded in `docs/architecture/specification-audit.md`

- **A-12** — *new in V2.* Non-geographic (audience/segment) scoping and how it
  composes with `MarketScope` (V2 §4.8).
- **A-01** — whether a scoring profile weights all dimensions or a subset.
- **D-08** — score recomputation policy.
- Opportunity identity resolution — when two discoveries are the same opportunity
  (V2 §12.3).

Each requires an authorized specification change. None may be resolved by an
implementer choosing a value.
