# Evidence schema — gap analysis against Aggregation V1

**Status:** Analysis. **No migration was written and no schema was changed.**
**Version:** 1.0
**Date:** 2026-08-29
**Audits:** `scoring.evidence` (migration `0001_foundation`) against
[`evidence-aggregation-framework-v1.md`](evidence-aggregation-framework-v1.md).

---

## 0. Why this is analysis and not a migration

Mission 1.1 §37 and §38 both say the same thing from different directions:
specify first, and do not let a framework mission become a scoring
implementation. So this document classifies what would have to change and stops
there.

One fact shapes every recommendation below: **`scoring.evidence` and
`nlp.signals` are empty, and nothing writes to either.** Acquisition is blocked
(no source is collector-eligible), NLP is blocked (D-12). Every change discussed
here is therefore cheap *today* and expensive later — which is the argument for
recording it now, not for doing it now.

---

## 1. Summary

| Classification | Count | Meaning |
|----------------|-------|---------|
| Already supported | 6 | The column exists and means what aggregation needs |
| Additive | 5 | A new nullable column. No existing semantics change |
| **Incompatible** | 2 | The existing shape cannot express what the framework needs |
| Deferred | 3 | Out of scope until a later mission authorises it |

**Nothing incompatible was changed.** Both incompatible items are recorded for
explicit authorisation.

---

## 2. Already supported

| Framework input | Column | Note |
|-----------------|--------|------|
| `reliability` | `reliability DOUBLE PRECISION` | Unit interval, CHECK-constrained. Exactly right |
| `observed_at` | `observed_at TIMESTAMPTZ` | Event time, correctly distinct from `collected_at` (`data-principles.md` §9). Freshness depends on this distinction |
| provenance | `source_id`, `source_reference`, `extraction_method`, `model_version`, `prompt_version` | Sufficient for the explanation |
| source family | via `registry.sources.source_family` | A join, not a column. Correct: duplicating it would let it drift from the registry |
| claim type | `claim_type` | The five-value taxonomy. Distinct from evidence *direction*, which is §3 |
| retention | `expires_at` | Aggregation reads a snapshot; expiry is what makes a snapshot a point in time |

---

## 3. Additive — new nullable columns, no existing semantics change

| # | Field | Type | Why |
|---|-------|------|-----|
| A-1 | `direction` | `TEXT NOT NULL` + CHECK | `EvidenceDirection`. Support and contradiction are aggregated separately; without this the two cannot be told apart |
| A-2 | `relevance` | `DOUBLE PRECISION` unit interval | A `q` component. Currently unrepresentable |
| A-3 | `directness` | `DOUBLE PRECISION` unit interval | A `q` component. First-hand versus report-about-a-report |
| A-4 | `observation_category` | `TEXT` + CHECK | `EvidenceObservationCategory`. Gates EvidenceLevel 4 and 5. Without it, no record can ever be Market Evidence |
| A-5 | `independence_group_id` | `TEXT` | Which origin this record derives from. See §4 |

A-1 is additive only because the table is empty. With rows in it, adding a
`NOT NULL` direction would require deciding what every existing record meant —
which is precisely the retrofit `data-principles.md` §11 warns about for
provenance, applied to a different column.

---

## 4. Incompatible — recorded, not changed

### I-1 — `independence DOUBLE PRECISION` cannot express independence

**The problem.** The column stores a scalar `[0,1]` per record. The framework
needs a *relation*: which records share an origin.

A number cannot say that. "Record B is 0.3 independent" does not identify what
it is dependent *on*, so the strongest-member-wins rule (§7) has nothing to
group by, and three copies of one announcement stay three records with three
scalars. The scalar shape makes the central failure of evidence aggregation —
duplicates multiplying strength — unfixable in the schema.

Worse, a scalar invites arithmetic. `q * independence` is the natural next step
and is exactly the discounting-instead-of-grouping approach the framework
rejects: it lets ten discounted duplicates still outweigh one original.

**What the framework needs instead:**

```text
independence_state     TEXT   KNOWN_INDEPENDENT | KNOWN_DEPENDENT | UNKNOWN
independence_group_id  TEXT   required when KNOWN_DEPENDENT, forbidden otherwise
```

`UNKNOWN` must be the default. A NULL that reads as "independent" is the same
silent promotion the framework forbids in code.

**Why it is incompatible rather than additive.** `independence` is declared in
`0001_foundation`, described in `evidence-confidence-framework-v1.md` §4 as "an
`independence` estimate", and appears in the contracts as a numeric type. Adding
state columns beside it leaves two answers to one question, and the one that
looks quantitative will win. Resolving it means either removing the scalar or
formally redefining what it means — both material changes.

**Cost today: near zero.** The table is empty and nothing reads the column. This
is the cheapest it will ever be to fix.

**Authorisation required.** Not done in this mission.

### I-2 — there is no Claim, so there is nothing to aggregate around

**The problem.** Aggregation is claim-centric (§1 of the framework). There is no
`claim` table, no `claim_id`, and no claim entity anywhere in the schema or the
ontology. `scoring.evidence` links to `opportunity_id` and `signal_id` instead.

Those are not substitutes. An Opportunity is a much larger object than a claim —
one opportunity carries many claims, several of which may be contradicted while
others are well supported. Aggregating at the opportunity level would average
exactly the distinctions the four-mass decomposition exists to preserve.

`claim_type` on `scoring.evidence` does not close the gap: it types the record,
it does not identify a proposition that several records bear on.

**What this blocks.** Nothing today — no evidence exists to aggregate. But
`services/scoring` cannot be implemented against this schema regardless of
D-03, because the unit of aggregation has no home.

**This is a domain question before it is a schema question.** Ontology V2 §7
defines a claims *taxonomy* and never defines a Claim *entity*. Introducing one
is an ontology change requiring a new version and an ADR
(`opportunity-ontology-v2.md` §10), not a migration somebody writes.

**Recorded as a new open item.** See §7.

---

## 5. Deferred

| # | Item | Why deferred |
|---|------|--------------|
| D-1 | An `evidence_aggregation_results` table | §37: production score tables are out of scope. It also interacts with D-08 (recomputation policy) — persisting results before deciding whether they are recomputed or immutable would fix that answer by accident |
| D-2 | Aggregation profile storage | The reference profile is a code constant. Persisting profiles matters when several exist and results must resolve historical ones; one `UNCALIBRATED` profile does not need a table |
| D-3 | `extraction_confidence` versus `confidence` | The existing `confidence` column is a unit-interval field whose exact referent is not pinned down. The framework needs *extraction* confidence specifically. Likely a documentation fix rather than a column, but it needs a decision rather than an assumption |

---

## 6. What the D-03 leakage guard should now allow

Migrations and canonical contracts are still forbidden from declaring
`decay_weight`, `contradiction_penalty`, `aggregated_evidence_score`,
`independence_threshold_result` or `evidence_aggregate`. Those names encode the
designs V1 **rejected**: a per-item decay multiplier, a flat penalty, an opaque
aggregate, and a threshold where V1 uses group counts. They stay forbidden
because the framework decided against them, not because D-03 is open.

`decay_half_life` was on the same list and is now legitimate — but only inside a
versioned profile, never as a module-level constant. The guard is updated to
match: the vocabulary V1 authorises is allowed in the reference package, and a
universal half-life constant is detected and refused wherever it appears.

---

## 7. New open item

**A-13 — the Claim entity.** Aggregation is defined around a Claim that the
ontology does not define as an entity. Resolving it requires an ontology version
and an ADR; it is not an implementer's decision. Until then, evidence
aggregation has a specification and a reference implementation but no persisted
unit of aggregation.

Recorded here and in the mission report rather than resolved, per
`docs/CLAUDE.md` §Change control.

---

## 8. Recommendation

**Change nothing now.** Every gap above is cheap while the tables are empty and
will stay cheap until acquisition and NLP unblock. The ordering that follows:

1. **A-13 first** — the Claim entity is a domain decision and everything else
   hangs off it. A schema written before it is decided will be written twice.
2. **I-1 with it** — the independence shape is the framework's most load-bearing
   input and the current column actively works against it.
3. **A-1 to A-5 with the first migration that touches this table** — additive,
   uncontroversial, and pointless to apply on their own while I-1 and A-13 are
   open.
4. **D-1 and D-2 when `services/scoring` is authorised**, which needs a
   `CALIBRATED` profile, which needs the calibration plan executed.
