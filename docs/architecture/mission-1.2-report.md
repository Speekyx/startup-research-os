# Mission 1.2 — Completion Report

**Mission:** Claim Entity, Evidence Persistence & Aggregation Schema Alignment
**Sprint:** 1
**Date:** 2026-08-29
**Branch:** `sprint-1/mission-1.2`
**Resolves:** **A-13** — evidence aggregation is claim-centric and no persisted Claim existed
**Introduces:** Ontology **V2.1**, `claim-model-v1.md`, [ADR-015](adr/ADR-015-claim-persistence-and-versioning.md), migration `0005_claim_evidence_alignment`, `ClaimId` and three closed enums

---

## 1. Claim model

A **Claim** is an assertion about an Opportunity that evidence can independently
support or contradict.

```text
Workspace -> Opportunity -> Claim -> Evidence -> Aggregation
```

Mission 1.1 defined aggregation around this unit and then found the system had
none. Evidence pointed at an Opportunity, which is the wrong granularity:

> "Users love this, will pay €20, and competition is low."

One opportunity, three assertions, and they do not stand or fall together.
Aggregating them as one thing averages away exactly what the four-mass
decomposition preserves.

Fields and their rationale: [`claim-model-v1.md`](../domain/claim-model-v1.md) §2.
Nothing was added because relational schemas usually have it.

## 2. Claim identity

`ClaimId`, a UUID, declared once in `packages/contracts` and generated to both
languages (ADR-009).

**Stable across statement revisions.** The text may be rewritten; the identity
may not, or every evidence record attached to the old wording would be orphaned.

**Not a `ClaimType`.** `ClaimType` is an epistemic category a claim *carries* —
five values, none of them an identity. A system that used one as the other would
have exactly five claims. `ClaimId("INFERRED")` raises, and a test asserts it.

**Not the claim text.** Text evolves; identity does not.

## 3. Claim ↔ Opportunity

One opportunity, zero-to-many claims; each claim belongs to exactly one
opportunity. Enforced by a composite foreign key carrying `workspace_id`.

Cross-opportunity claim sharing is **deliberately not modelled**. If
deduplication later shows the same assertion recurring, that raises its own
questions — whose evidence set, whose workspace — and answering them before the
simple model has been used would be guessing.

## 4. ResearchSession provenance

A claim is **not owned** by the session that first met it, the rule Ontology V2
§12 established for Opportunity, applied unchanged.

```text
ResearchSession -> claim_session_observations -> Claim
```

`ObservationKind` (`DISCOVERED` / `CORROBORATED` / `CONTRADICTED`) was promoted
to a contract enum in the process: it already governed opportunity observations
as a SQL CHECK plus a Python frozenset, which is the drift ADR-009 exists to
prevent. Mission 1.2 removed that drift rather than adding more.

The same claim accumulates evidence across sessions, and is never duplicated
because a second session encountered it — that would split its evidence in two.

## 5. Claim temporality

Every claim declares `EVERGREEN` or `TEMPORALLY_SENSITIVE`. Required, with no
default, and **never inferred from the source**: the same platform carries an
evergreen fact and a trend stale in a week.

A claim **names** a `claim_feature`; it does not own a half-life. That number
lives in a versioned aggregation profile, and no profile has one — so a
temporally sensitive claim still yields `MISSING_TEMPORAL_PARAMETER` and no
score. Resolving A-13 did not weaken that.

`claim_feature` is deliberately **not** an enum: the useful set of features is
unknown until calibration runs.

## 6. Claim versioning

Stable identity plus **append-only** `claim_revisions`. Revising appends a row
and moves a pointer; the previous revision is never modified.

The statement is **not** on `claims` at all. A denormalised copy would save one
join and add a value that can drift from the history; keeping the text in one
place makes drift impossible rather than unlikely.

The pointer is a `DEFERRABLE INITIALLY DEFERRED` composite foreign key, so it
always names a revision that exists while still allowing a claim and its first
revision to be written together.

Rejected: immutable claims linked by supersession. Identity would change on
every edit, orphaning attached evidence exactly when the claim is being
clarified (ADR-015).

Each revision records a mandatory `revision_reason` and an author-declared
`material_change`. **Nothing acts on that flag**, deliberately — see §17.

## 7. Evidence schema changes

| | |
|---|---|
| Added | `claim_id`, `direction`, `relevance`, `directness`, `extraction_confidence`, `observation_category`, `independence_state`, `independence_group_id` |
| **Dropped** | `independence DOUBLE PRECISION` |
| Documented | `reliability`, `extraction_confidence` and `confidence` now carry `COMMENT ON COLUMN` stating what each means |

`direction` and `observation_category` are `NOT NULL` with their `ALTER`-time
defaults **dropped afterwards**, so an omitted direction is an error rather than
a silent `NEUTRAL` — which would quietly remove a record from both aggregations.

`independence_state` keeps its `UNKNOWN` default, and that one is intended:
unestablished provenance is the honest starting state.

## 8. Independence persistence

`scoring.evidence_independence_groups`, claim-scoped, with a mandatory `basis`.

A group means these records **share an underlying information origin** — not
that they came from the same website. Grouping is the operation with the largest
single effect on a result, so one with no stated reason cannot be re-checked.

The three states are enforced by CHECK, not only by the repository:

```text
KNOWN_DEPENDENT    must name a group   -- dependent on WHAT?
KNOWN_INDEPENDENT  must not            -- or it claims both at once
UNKNOWN            must not            -- and stays UNKNOWN in storage
```

A nullable group id alone was never the model: it cannot distinguish "checked,
independent" from "never checked", and those call for different work.

**Unknown stays unknown.** The engine builds its conservative single-bucket
grouping at runtime and writes nothing. Ten UNKNOWN records are stored as ten
unknowns and aggregate as one contribution; neither layer pretends the question
was answered.

## 9. Tenant isolation

Three layers, failing differently on purpose.

| Layer | Mechanism |
|---|---|
| 1 | explicit `WHERE workspace_id = %s` in every repository query |
| 2 | RLS policy — all four new tables ENABLE + FORCE |
| **3 (new)** | **composite foreign keys carrying `workspace_id`** |

Layer 3 is what makes a cross-tenant reference **structurally impossible**
rather than forbidden. A claim cannot reference another workspace's opportunity;
evidence cannot reference another workspace's claim; an independence group
cannot span claims *or* workspaces. The group key carries `claim_id` too, so a
record cannot join a group belonging to a different claim — the failure that
would silently collapse unrelated evidence.

Cost: two redundant `UNIQUE (workspace_id, id)` constraints so the composite keys
have something to reference.

## 10. Database migration

`0005_claim_evidence_alignment` — four new tables, `scoring.evidence` realigned,
four RLS policies. Forward-only; migration 0001 untouched.

Verified from an **empty database**: five migrations apply clean, two seeds run,
every suite passes against the result.

## 11. Contracts

| Added | |
|---|---|
| `ClaimId` | a UUID identifier, TS + Python |
| `ClaimOrigin` | `MANUAL`, `DETERMINISTIC_EXTRACTION`, `LLM_EXTRACTION`, `INFERRED`, `SYSTEM_GENERATED`, `IMPORTED` |
| `ClaimLifecycle` | `ACTIVE`, `WITHDRAWN` |
| `ObservationKind` | promoted from a SQL CHECK plus a Python frozenset |

`ClaimTemporality`, `EvidenceDirection`, `EvidenceIndependenceState` and
`EvidenceObservationCategory` already existed from Mission 1.1 and were **not
redefined** — §13 of the brief says to use the framework's vocabulary if
present, and it was. The canonical spellings are `OBSERVED_BEHAVIOUR` and
`MARKET_ACTIVITY`; other wordings in briefs refer to these same values.

The `Independence` numeric type is marked **superseded**, not removed, so
historical references resolve. No column uses it.

`ClaimOrigin` carries no model name: models change constantly and a contract
must not. A test asserts no member contains `GPT`, `CLAUDE` or a hyphen.

Contract version **1.2.0**. Shared conformance cases cover all of it in both
languages.

## 12. Repositories and API

**`ClaimRepository`** — create, get, list-for-opportunity, revise, withdraw,
record-observation, revisions, `statement_at`, observations.
**`EvidenceRepository`** — create, list-for-claim, create-independence-group,
independence-groups.

**API** — `GET /opportunities/{id}/claims`, `GET /claims/{id}`,
`GET /claims/{id}/evidence`, plus `POST /claims` and
`POST /claims/{id}/revisions`.

The writes exist and **are not authorised**. There is no authentication
(ADR-005), so `x-workspace-id` says which tenant you are working in, never that
you are entitled to — the same caveat as the existing project and session
endpoints. Contrast the Source Registry API, which is read-only because a write
there could approve a source for collection; a claim write creates content
inside one workspace.

**Nothing aggregates.** No score is computed or served, and no service imports
the reference engine — a CI guard asserts it.

## 13. Aggregation compatibility

`sros_evidence_aggregation.adapters` maps a documented row-dict shape to
`EvidenceItem`. It imports no database driver and knows no SQL; the gateway does
not import it. **A test wires the two together**, which is what keeps an
uncalibrated engine out of every production path.

Proven end to end: five persisted records — one independent, three sharing a
declared origin, one contradicting — load through the repository and aggregate
to two support groups and one contradiction group, with the dependent trio
collapsed to its strongest member. Ten persisted `UNKNOWN` records stay ten
unknowns in storage and become one runtime contribution.

Also proven: revising a claim does not change the evidence set, and the
aggregation over `claim@r1` is byte-identical before and after.

## 14. Tests

| Suite | Count | New |
|---|---|---|
| `test_claims.py` | 48 | all new |
| Gateway total | 210 | up from 158 |
| Contracts conformance (Python) | 27 + 177 subtests | +6 |
| Contracts conformance (TS) | 21 | +2 |
| Zero-dependency total | 310 | up from 304 |
| Every other suite | unchanged | all green |

The cross-tenant tests assert on the **constraint name**, not on any exception.
That is not pedantry — see §16.

## 15. CI and quality gates

No new job. The existing schema, source-registry and aggregation-guard jobs pick
up the migration and the new code, and `quality-gates.md` §1 records eight new
gates.

**The aggregation guard was narrowed, not weakened.** The single "authorised
vocabulary" list conflated two different things:

| Tier | Rule |
|---|---|
| **Evidence inputs** — `independence_state`, `observation_category`, `extraction_confidence`, `directness`, `independence_group_id` | **Now authorised** as schema columns. Recording what was observed is not aggregating it |
| **Computed outputs** — the strengths, the four masses, `evidence_score`, `aggregation_profile_id`, `algorithm_version` | **Still forbidden** in migrations and under `services/`. A column holding one would mean scoring had started without a calibrated profile |

A new check makes the narrowing safe: **no service may import
`sros_evidence_aggregation`.** Tests may; production modules may not.

## 16. Issues found

**A real bug in this mission's own migration.** `ON DELETE SET NULL` on a
**composite** foreign key nulls *every* column in it — including `workspace_id`,
which is `NOT NULL`. Deleting a research session therefore failed with a
violation naming a column nobody had touched. Found by the existing
tenant-isolation delete test, not by review.

Fixed with `ON DELETE SET NULL (origin_session_id)` (PostgreSQL 15+). `CASCADE`
would have been *worse than the bug*: a claim is not owned by the session that
discovered it, so deleting a session must not delete the claim. Regression test
added.

**A contradiction between my own constraint and my own comment.** The same fix
applied to the evidence→group key produced a record that was `KNOWN_DEPENDENT`
with no group — which the shape CHECK forbids, so the delete failed on a
different constraint. The migration comment had been arguing for behaviour the
CHECK already ruled out.

Resolved with `ON DELETE RESTRICT`: a grouping with members cannot simply
vanish. Deleting one is a decision about every record that declared itself
dependent on it, and the database should make somebody take it.

**A test that would have passed while proving nothing.** An insert meant to
exercise the `evidence_level` CHECK began failing on a `NOT NULL` violation
instead, because migration 0005 made `direction` required. A blind
`pytest.raises(Exception)` reported green. Every such assertion in the new suite
now matches on the constraint name.

**A blocking reason that had gone false.** The orchestrator still said SCORING
was blocked because "the aggregation formula is undefined". Mission 1.1 defined
it. Corrected to `PROFILE-NOT-CALIBRATED` with the real reason — the same stale
-reason problem Mission 1.1 fixed for D-07, caught this time by reading the
output.

**ADR numbering, for the last time.** The production-deployment placeholder had
moved once per mission — 012, 013, 014, 015. Mission 1.1 said that if it moved
again the answer was to stop reserving the number, so the reserved row is gone.
Production deployment is still required, still deferred by ADR-007, and will
take whatever number is next.

## 17. Remaining blockers

| Blocker | Status |
|---|---|
| **Calibration** | **Open.** No `CALIBRATED` profile. This is what blocks production scoring now |
| **D-08** | Open. Recomputation policy. This schema records what either answer needs (`claim_revision`, `evidence_snapshot_digest`, `material_change`) without choosing one |
| **D-12** | Open. Untouched. Independence groups are representable but written by hand |
| **Opportunity identity resolution** | Open. Tests insert opportunities explicitly, precisely to avoid settling it |
| **A-12** | Open. `MarketScope` untouched |
| **A-01**, **D-11** | Open |
| Source review | 13 candidates, still zero collector-eligible |
| Jurisdiction / GDPR | Requires human or legal input |

**Nothing new opened.**

## 18. A-13 resolution status

Against the fifteen criteria in §44:

| # | Criterion | |
|---|---|---|
| 1 | Claim defined in authoritative ontology | ✅ V2.1 §17 |
| 2 | Stable identity | ✅ `ClaimId`, survives revision |
| 3 | Belongs to an Opportunity | ✅ composite FK |
| 4 | Tenant scoped | ✅ `workspace_id NOT NULL` + RLS |
| 5 | Temporality explicit | ✅ required, never inferred |
| 6 | Provenance explicit | ✅ origin, session, model, prompt, author, time |
| 7 | Version semantics defined | ✅ append-only revisions, ADR-015 |
| 8 | Evidence references Claim | ✅ `claim_id` |
| 9 | Direction persisted | ✅ CHECK over three values |
| 10 | Independence state persisted | ✅ three states, shape enforced |
| 11 | Groups representable | ✅ claim-scoped, with mandatory basis |
| 12 | Unknown stays explicit | ✅ no synthetic group is written |
| 13 | RLS protects the new tables | ✅ four tables, ENABLE + FORCE |
| 14 | Aggregation retrieves a complete set reproducibly | ✅ repository → adapter → engine, byte-identical |
| 15 | Opportunity not substituted for Claim | ✅ distinct tables, distinct ids |

**A-13 is RESOLVED.** All fifteen hold.

## 19. Production scoring status

**Still blocked, and A-13 did not change that.**

```text
Framework Defined     ✅  Mission 1.1
Claim entity          ✅  Mission 1.2
Profile Calibrated    ❌  no labelled dataset exists
services/scoring      ❌  a boundary README, no implementation
D-08                  ❌  open
```

Resolving A-13 gave aggregation a unit to operate on. It calibrated nothing. The
guard asserting `services/scoring` has no implementation still passes, and the
orchestrator still refuses to dispatch a scoring stage.

## 20. Mission 1.3 readiness

Safe to begin. Nothing half-applied: the database rebuilds from empty, every
gate is green, no external data was collected, and the three defects found were
fixed rather than noted.

---

## Explicit answers

| Question | Answer |
|---|---|
| Does Claim exist as a persisted domain entity? | **Yes.** `research.claims` + `research.claim_revisions`, Ontology V2.1 §17 |
| Is Claim different from ClaimType? | **Yes.** `ClaimType` is an epistemic category a claim carries; five values, no identity. `ClaimId("INFERRED")` raises |
| Can one Opportunity carry multiple independently evaluated Claims? | **Yes**, and a test builds one opportunity with a supported claim and a contradicted one |
| Can a Claim accumulate evidence across ResearchSessions? | **Yes.** Sessions produce observations; the claim is never duplicated |
| Is Claim temporality explicit? | **Yes.** Required, no default, never inferred from the source |
| Can historical Claim revisions be reproduced? | **Yes.** Append-only; `statement_at(claim, n)` returns what revision *n* said |
| Does Evidence reference Claim rather than Opportunity? | **Yes.** `claim_id`, with a composite FK carrying `workspace_id` |
| Is scalar independence removed or superseded? | **Removed** from the schema; the contract type is marked superseded so history resolves |
| Can dependent evidence be grouped? | **Yes.** Claim-scoped groups with a mandatory basis; members collapse to their strongest |
| Does UNKNOWN independence remain unknown? | **Yes.** No synthetic group is written. The engine's bucket is runtime-only |
| Can cross-tenant Evidence/Claim relationships occur? | **No.** Structurally impossible — composite FKs carry `workspace_id`, under RLS and the repository filter |
| Is RLS active on all new tenant data? | **Yes.** Four tables, ENABLE + FORCE, one policy each |
| Can the Mission 1.1 reference engine aggregate repository-loaded evidence? | **Yes**, through an adapter that imports no driver, wired only in tests |
| Is A-13 resolved? | **Yes.** All fifteen §44 criteria hold |
| Is Evidence Aggregation calibrated? | **No.** No parameter was fitted; no labelled dataset exists |
| Is production scoring still blocked? | **Yes.** No `CALIBRATED` profile, no `services/scoring` implementation, D-08 open |
| Was any external source data collected? | **No.** 13 sources, 0 eligible, 0 collectors, **0 raw records** — asserted in CI |
| Is Mission 1.3 safe to begin? | **Yes**, with calibration and D-08 carried forward as known state |

---

## Validation

Run against a database rebuilt from empty. Every command passed.

| Check | Result |
|---|---|
| `migrate.py --apply --seed` on an **empty** database | 5 migrations, 2 seeds |
| `run_python_tests.py` (zero-dep) | **310 tests across 5 packages** |
| `run_pytest_suites.py` | all 6 packages |
| `validate_schema.py` | 8 invariant groups, **30 tables** |
| `validate_source_registry.py` | 13 sources, 0 warnings — **unchanged** |
| `validate_evidence_aggregation.py` | 8 checks, 0 warnings |
| `assert_registry_grants_nothing.py` | 13 registered, 0 eligible, 0 enabled, **0 raw records** |
| `sensitivity --check` | report matches the implementation |
| `generate.py --check` | 3 artefacts current, contract **1.2.0** |
| `ruff check` / `format --check` | clean, 209 files |
| `mypy` (7 packages) | no issues in **84 source files** |
| `tsc` contracts + web, `eslint`, `next build` | clean |
| TS conformance + web API client | 21 + 18 tests |
| RLS suite | 45 tests, four new tables included |

## Mission boundary

Stopped here, as §51 requires. **Mission 1.3 was not begun.** Production scoring
was not enabled, no external data was collected, no NLP or embeddings ran, no
aggregation result was persisted, and the Source Registry is byte-identical to
how Mission 1.0 left it.

The honest one-line summary: evidence aggregation now has something to aggregate
around, and still nothing calibrated to aggregate with.
