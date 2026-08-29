# Evidence schema gap analysis — V1.1 resolution appendix

**Status:** Resolution appendix. Supersedes nothing.
**Version:** 1.1
**Date:** 2026-08-29
**Appends to:** [`evidence-schema-gap-analysis-v1.md`](evidence-schema-gap-analysis-v1.md), which is a record of what was true in Mission 1.1 and is **not rewritten**.
**Resolved by:** migration `0005_claim_evidence_alignment`, [ADR-015](../architecture/adr/ADR-015-claim-persistence-and-versioning.md).

---

## 0. Why an appendix rather than an edit

V1 recorded findings at a point in time and recommended changing nothing. Both
statements were correct then, and editing them to read as though the work had
already been done would destroy the record of the decision. V1 stays as written;
this document says what happened to each item.

---

## 1. Status of every V1 finding

| V1 item | Was | Now |
|---------|-----|-----|
| 6 already-supported fields | Already supported | **Unchanged.** `reliability`, `observed_at`, provenance, source family, `claim_type`, `expires_at` all kept their meaning |
| **A-1** `direction` | Additive | ✅ **RESOLVED** — `TEXT NOT NULL` + CHECK over the three values |
| **A-2** `relevance` | Additive | ✅ **RESOLVED** — unit-interval, nullable |
| **A-3** `directness` | Additive | ✅ **RESOLVED** — unit-interval, nullable |
| **A-4** `observation_category` | Additive | ✅ **RESOLVED** — `TEXT NOT NULL` + CHECK. Gates EvidenceLevel 4 and 5 |
| **A-5** `independence_group_id` | Additive | ✅ **RESOLVED** — with a state column beside it; see I-1 |
| **I-1** scalar `independence` | **Incompatible** | ✅ **RESOLVED** — column dropped, replaced by a three-state model |
| **I-2** no Claim | **Incompatible** | ✅ **RESOLVED** — `research.claims` exists; evidence references it |
| **D-1** aggregation result table | Deferred | ⏸ **STILL DEFERRED** — §3 |
| **D-2** profile storage | Deferred | ⏸ **STILL DEFERRED** — §3 |
| **D-3** `extraction_confidence` vs `confidence` | Deferred | ✅ **RESOLVED** — §4 |
| **A-13** the Claim entity | New open item | ✅ **RESOLVED** — Ontology V2.1 §17, `claim-model-v1.md` |

**Nothing carried forward as still incompatible.** Both Mission 1.1
incompatibilities are closed.

---

## 2. How the two incompatibilities were resolved

### I-1 — the scalar could not express independence

**Dropped, not reinterpreted.**

```sql
ALTER TABLE scoring.evidence DROP COLUMN independence;
```

A number cannot say *which* records share an origin, so grouping had nothing to
group by. Reinterpreting it as "confidence in independence" was the tempting
option — no migration needed — and it would have left a quantitative-looking
column that invites `q × independence`. That is discounting instead of grouping,
and it still lets ten discounted duplicates outweigh one original.

Replaced by:

```sql
independence_state     TEXT NOT NULL DEFAULT 'UNKNOWN'
independence_group_id  UUID REFERENCES scoring.evidence_independence_groups
```

with a CHECK constraint enforcing the shape: `KNOWN_DEPENDENT` must name a group,
the other two must not. A nullable group id alone was never the model — it
cannot distinguish "checked, independent" from "never checked".

The contract's `Independence` numeric type is marked **superseded** rather than
removed, so historical references still resolve. No column uses it.

### I-2 — there was no Claim

`research.claims` plus `research.claim_revisions`, and `scoring.evidence` now
carries `claim_id` with a composite foreign key that also carries
`workspace_id`.

The domain half came first, as V1 said it had to: this was an ontology change
(V2.1 §17) and an ADR before it was a migration.

---

## 3. What is still deferred, and why the reason changed

**D-1 — an aggregation result table.** Still not created, but the reason has
narrowed. V1 deferred it because the *shape* was unknown; the shape is now
documented in `claim-model-v1.md` §11, including the field that makes it honest
(`claim_revision`). What blocks it now is only the gate: persisting a result is
scoring, and scoring requires a `CALIBRATED` profile that does not exist.

**D-2 — profile storage.** Unchanged. One `UNCALIBRATED` profile does not need a
table; several, with historical results resolving against them, will.

---

## 4. D-3 resolved: `confidence` and `extraction_confidence` are different things

V1 flagged the existing `confidence` column as having no pinned referent. Both
now exist, with stated meanings:

| Column | Means |
|--------|-------|
| `extraction_confidence` | Confidence that the extraction **read the record correctly**. An aggregation input |
| `confidence` | The general unit-interval confidence attached to the record (`scoring-framework-v1.1.md` §4.1). **Not** an aggregation input |

The distinction matters because they move independently: an extraction can be
certain about a sentence whose content is doubtful. `min()` consumes the first
and never the second. Both are documented with `COMMENT ON COLUMN`, so the
answer travels with the schema instead of only with this file.

Neither is defaulted when absent. A manually authored record may have no
extraction confidence, and aggregation then reports it non-scorable rather than
inventing one.

---

## 5. What the migration deliberately did not do

- **No aggregation result table** (§3).
- **No change to migration 0001.** Forward-only, always.
- **No reinterpretation** of an existing column's meaning. The one column whose
  meaning could not survive was dropped rather than quietly redefined.
- **No touch to the Source Registry.** Thirteen sources, still zero
  collector-eligible.

---

## 6. New tables, and where they live

| Table | Schema | Why there |
|-------|--------|-----------|
| `claims` | `research` | A domain assertion about an Opportunity. `scoring` evaluates evidence; it does not own the assertions being evaluated (`service-boundaries.md` §1) |
| `claim_revisions` | `research` | Belongs with the claim |
| `claim_session_observations` | `research` | Belongs with the research lifecycle |
| `evidence_independence_groups` | `scoring` | Part of the evidence model, which Evidence Evaluation owns. **Detecting** these relationships is `nlp`'s job and D-12 is open, so every group is currently written by hand |

---

## 7. Remaining open items

- **D-08** — recomputation policy. Untouched, and deliberately: this schema
  records what either answer needs (`claim_revision`,
  `evidence_snapshot_digest`, `material_change`) without choosing one.
- **D-12** — embeddings and semantic deduplication. Independence groups are
  representable but must currently be written by hand.
- **Opportunity identity resolution** — still open. Mission 1.2 did not touch
  it, and inserting opportunities explicitly in tests was the way to avoid
  accidentally settling it.
- **Calibration** — no profile is `CALIBRATED`, so production scoring stays
  unavailable regardless of A-13.
