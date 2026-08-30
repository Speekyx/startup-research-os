# Claim Model V1

**Status:** Authoritative. Created in Mission 1.2, resolving **A-13**.
**Version:** 1.0
**Date:** 2026-08-29
**Extends:** [`opportunity-ontology-v2.1.md`](opportunity-ontology-v2.1.md) §17, which defines the Claim entity.
**Consumed by:** [`evidence-aggregation-framework-v1.md`](evidence-aggregation-framework-v1.md) — the Claim is its unit of aggregation.
**Implemented by:** migration `0005_claim_evidence_alignment`, [ADR-015](../architecture/adr/ADR-015-claim-persistence-and-versioning.md).

---

## 1. Why a Claim exists

Mission 1.1 defined evidence aggregation around a Claim and then found the
system had none. Evidence pointed at an Opportunity, which is the wrong unit:

> "Users love this, will pay €20, and competition is low."

That is one opportunity and at least three assertions, and they do not stand or
fall together. The first may be well supported, the second contradicted, the
third never investigated. Aggregating them as one thing averages away exactly
what the four-mass decomposition exists to preserve.

```text
Workspace
  └── Opportunity
        └── Claim              ← the unit evidence accumulates against
              └── Evidence
                    └── Evidence Aggregation
```

**A Claim is not an Opportunity.** An opportunity is a hypothesis about a
product; a claim is a single assertion that evidence can bear on.

**A Claim is not a `ClaimType`.** `ClaimType` — `OBSERVED`, `INFERRED`,
`PREDICTED`, `RECOMMENDED`, `HYPOTHESIS` — is an epistemic category a claim
*carries*. It was never an identity, and a system that used one as the other
would have exactly five claims.

| | Claim | ClaimType |
|---|---|---|
| Example | "Users want AI-assisted match predictions" | `INFERRED` |
| Cardinality | unbounded | exactly five |
| Identity | `ClaimId`, a UUID | none |

---

## 2. Fields, and why each exists

Every field has a purpose. None is present because relational schemas usually
have one.

| Field | Why it exists |
|-------|---------------|
| `claim_id` | Stable identity, survives statement revision (§4) |
| `workspace_id` | Tenant boundary. `NOT NULL`, always (ADR-005) |
| `opportunity_id` | What the claim is about, if anything yet. **At most one, possibly none** since Mission 1.13 (§3) |
| `claim_type` | Epistemic category. Not identity |
| `lifecycle` | Editorial state. Never epistemic (§8) |
| `temporality` | Whether the claim decays. Required by aggregation (§5) |
| `claim_feature` | Names the profile key a half-life would be looked up under. The claim does not own the number (§5) |
| `origin` | What kind of process produced it (§6) |
| `origin_session_id`, `origin_detail`, `model_version`, `prompt_version`, `created_by` | Provenance (§9) |
| `current_revision` | Points at the live statement (§4) |
| `created_at`, `updated_at` | When |

The **statement is not on this table**. It lives only in `claim_revisions`, so
the current text and the history cannot disagree.

---

## 3. At most one Opportunity, many Claims

A claim belongs to **at most one** opportunity, and may belong to none. An
opportunity may have zero or many claims.

> **Amended in Mission 1.13** (ADR-024, Ontology V2.2 §17.3). This section
> originally said *exactly one*, and `claims.opportunity_id` was `NOT NULL`. The
> pipeline runs Signal → Claim → Opportunity: a claim about a source fact exists
> before anybody has conceived of the product it might justify, so the original
> rule made the intended pipeline unrepresentable. Migration 0016 drops the
> constraint. Everything else in this document is unchanged.

Cross-opportunity claim sharing is still deliberately not modelled. If
deduplication later shows the same assertion recurring across opportunities,
that raises its own questions — whose evidence set, whose workspace, what
happens when one opportunity is deleted — and answering them before the simple
model has been used would be guessing. The first model has to be one people can
reason about.

An **unattached** claim is a different situation from a shared one, and is now
the normal state of a freshly interpreted claim rather than an anomaly.
`idx_claims_unattached` exists to find them (migration 0016).

---

## 4. Statements, atomicity and revision

### The statement

Human-readable, explicit, auditable, and atomic enough to be supported or
contradicted. Not an opportunity description, and never an opaque embedding: a
claim nobody can read is a claim nobody can dispute.

### Atomicity

Bad — at least three claims:

> "Users love this, will pay €20, and competition is low."

Better:

| Claim | |
|---|---|
| A | "Users show strong interest in this product category." |
| B | "A meaningful segment expresses willingness to pay." |
| C | "The market has relatively few direct alternatives." |

Each will attract different evidence, and B may be contradicted while A is
confirmed.

**Atomicity is not machine-checkable here, and V1 does not pretend otherwise.**
Splitting compound assertions needs NLP, which is out of scope and blocked by
D-12. No heuristic rejects a claim for containing the word "and" — "users want
import and export in one step" is a single, perfectly atomic assertion. This
section is guidance for whoever writes claims and for the extraction system that
will eventually propose them.

### Revision

Claims are edited: narrowed, clarified, corrected. Revisions are **append-only**.

```text
claims.current_revision ──> claim_revisions (claim_id, revision) [append-only]
```

Revising appends a row and moves the pointer. **The previous revision is never
modified.** An aggregation that evaluated revision 2 must still be able to read
revision 2 years later, or every historical result becomes unreproducible the
moment somebody fixes a typo.

Identity is stable across revisions. Under an immutable-claim-plus-supersession
model the id would change on every edit, orphaning every attached evidence
record exactly when the claim is being clarified (ADR-015).

Each revision records a mandatory `revision_reason` and an author-declared
`material_change`: did the *meaning* change, or only the wording? Nothing acts
on that flag in V1 — see §12.

---

## 5. Temporality

Every claim declares one:

| Value | Meaning |
|-------|---------|
| `EVERGREEN` | Does not decay. `freshness = 1.0` |
| `TEMPORALLY_SENSITIVE` | Loses force as its evidence ages |

**Declared, never inferred from the source.** The same platform carries a
pricing figure stale in a month and a workflow observation still true in three
years; a temporality read off the source would be wrong for one of them with no
way to tell which.

**A claim does not own a half-life.** It names a `claim_feature`; the
`EvidenceAggregationProfile` supplies the number, per feature, versioned. No
profile has one today, so a `TEMPORALLY_SENSITIVE` claim yields
`MISSING_TEMPORAL_PARAMETER` and no score — the designed behaviour, not a gap
(`evidence-aggregation-framework-v1.md` §9).

---

## 6. Origin

`MANUAL`, `DETERMINISTIC_EXTRACTION`, `LLM_EXTRACTION`, `INFERRED`,
`SYSTEM_GENERATED`, `IMPORTED`.

What **kind** of process produced the claim. **No model, provider or prompt name
appears in this enum**: those change constantly and a contract must not. They go
in `model_version` and `prompt_version`, where a new model needs no contract
change.

No extraction is implemented in this mission. Every claim today is `MANUAL` or a
test fixture.

---

## 7. Observation category

Not on the Claim. It is a property of an **evidence record** — what kind of
thing was observed — and Mission 1.1 already defined it as
`EvidenceObservationCategory`, gating EvidenceLevel 4 and 5.

Mission 1.2 promotes that existing enum through contracts rather than inventing
a second classification beside it. Note the canonical spellings are
`OBSERVED_BEHAVIOUR` and `MARKET_ACTIVITY`; other wordings that appear in
mission briefs refer to these same values.

Sessions relate to claims through `claim_session_observations`, using the same
`ObservationKind` vocabulary — `DISCOVERED`, `CORROBORATED`, `CONTRADICTED` —
that already governed opportunity observations, now promoted to a contract enum
so the two cannot drift.

---

## 8. Lifecycle — editorial, never epistemic

`ACTIVE` and `WITHDRAWN`. That is the whole enum, and the absence is the
feature.

**There is no `VALIDATED` and no `REJECTED`.** A lifecycle state derived from
`EvidenceLevel` or from an Evidence Score would freeze a conclusion that later
evidence could contradict, and it would keep being read as authoritative after
the evidence moved. What a claim is worth is read from its aggregation, every
time.

`WITHDRAWN` means the claim left circulation — malformed, duplicated, out of
scope — and requires a stated reason. Its evidence and revision history are
retained: deleting them would destroy the record of what was once believed.

---

## 9. Provenance

A claim answers, without reaching outside itself:

- where did the assertion come from — `origin`, `origin_detail`;
- during which ResearchSession was it introduced — `origin_session_id`;
- what process created it — `origin`;
- which model and prompt, if AI-generated — `model_version`, `prompt_version`;
- when — `created_at`.

**Raw source content is not stored here.** It belongs to the evidence and
acquisition records, under their own retention rules
(`data-retention-policy-v1.md`). A claim references; it does not copy.

A claim is **not owned by the session that first met it**, for the same reason
an Opportunity is not (Ontology V2 §12). Sessions produce observations; the same
claim accumulates evidence across many of them. Duplicating a claim because a
second session encountered it would split its evidence in two.

---

## 10. Evidence and independence

Evidence references `claim_id`. It carries `direction`
(`SUPPORTS` / `CONTRADICTS` / `NEUTRAL`), the aggregation input factors, an
`observation_category`, and a three-state independence model:

| State | Group id |
|-------|----------|
| `KNOWN_DEPENDENT` | **required** — dependent on *what*? |
| `KNOWN_INDEPENDENT` | must be absent |
| `UNKNOWN` | must be absent, and stays UNKNOWN in storage |

Enforced by a CHECK constraint, not only by the repository.

A group means these records **share an underlying information origin** — not
that they came from the same website. Two independent posts on one platform are
two observations; one announcement repeated by a blog and linked from a forum is
three records and one observation. Every group records a mandatory `basis`,
because collapsing evidence is the operation with the largest effect on a result
and one with no stated reason cannot be re-checked.

**Unknown stays unknown.** The aggregation engine builds its conservative
single-bucket grouping at runtime; nothing is written. An unresolved question
must not look resolved in the database.

---

## 11. What a future aggregation record will reference

Not implemented. Storing an aggregation result would be scoring, and scoring
requires a `CALIBRATED` profile that does not exist (ADR-014). The shape is
recorded so it is not re-derived later:

```text
claim_id                    which claim
claim_revision              which STATEMENT was evaluated
evidence_snapshot_digest    which evidence set
aggregation_profile_id      which parameters
aggregation_profile_version
algorithm_version           which equations
computed_at
```

`claim_revision` is the field that makes a historical result honest: without it,
a result computed against revision 1 becomes indistinguishable from one computed
against revision 3.

---

## 12. D-08 is not resolved here

D-08 — the score recomputation policy — remains **open**. This model does not
decide it, and deliberately does not force an answer.

What it provides is the input either answer needs:

- `claim_revision` distinguishes what was evaluated from what the claim says now;
- `evidence_snapshot_digest` distinguishes the evidence set that was evaluated;
- `material_change` records whether a revision changed the meaning, which only
  the editor knows and cannot be reconstructed later.

Conceptually a future result will be either an `ORIGINAL_AGGREGATION` or a
`RECOMPUTED_AGGREGATION`. **Naming the distinction is not resolving it**: when
recomputation is triggered, whether an original is retained, and what a material
revision does to already-attached evidence are all still open.

---

## 13. Boundaries

**Not decided here:** cross-opportunity claim sharing; automated atomicity
checking; claim extraction of any kind; opportunity identity resolution (still
open); D-08; D-12.

**Production scoring remains unavailable.** Resolving A-13 gave aggregation a
unit to operate on. It did not calibrate anything, and the second gate —
Profile Calibrated — is untouched.
