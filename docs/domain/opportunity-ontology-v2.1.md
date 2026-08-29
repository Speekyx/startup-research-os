# Opportunity Ontology V2.1

**Status:** Authoritative. Supersedes `opportunity-ontology-v2.md`.
**Date:** 2026-08-29
**Supersedes:** V2 (retained as a historical specification, not deleted)
**Authorized by:** Sprint 1 / Mission 1.2, which explicitly authorises resolving **A-13**

---

## 0. Changes from V2

V2.1 **inherits V2 in full**. Section numbering is preserved, so every existing
reference to `opportunity-ontology-v2.md §N` resolves to the same rule here.
Only the following changes are authorised, and only they were applied.

| Change | Section | Reason |
|--------|---------|--------|
| **Claim** defined as a persisted domain entity | §17 (new) | Resolves **A-13**. Mission 1.1 defined evidence aggregation around a Claim and found the system had none: evidence pointed at an Opportunity, which is the wrong unit |
| `ClaimId` added to the identifier set | §17.2 | A Claim needs identity that survives a statement rewrite |
| Claim ↔ Opportunity and Claim ↔ ResearchSession relationships | §17.3, §17.4 | The same non-ownership rule §12 established for Opportunity, applied to Claim |
| `ClaimLifecycle`, `ClaimOrigin` and `ObservationKind` added to the closed-enum register | §14.2 | Each requires exhaustive branching |
| Evidence recorded as claim-scoped | §17.6 | Consequence of A-13. `scoring.evidence` referenced an opportunity; it now references a claim |

**Nothing in V2 §1–§16 is altered.** No dimension, registry, taxonomy, market
scope rule, confidence rule, research-lifecycle rule or governance rule changed.
`ClaimType` is untouched and remains exactly five values.

**Not resolved here:** opportunity identity resolution (§12.3), A-12
non-geographic scoping (§4.8), D-08, D-12.

---

## 1–16. Unchanged from V2

See [`opportunity-ontology-v2.md`](opportunity-ontology-v2.md), which remains
the text for these sections. It is retained as a historical record and is not
deleted.

Two rules from V2 are restated here because §17 depends directly on them:

- **§7 Claims taxonomy.** `ClaimType` is a CLOSED enum of five UPPERCASE values:
  `OBSERVED`, `INFERRED`, `PREDICTED`, `RECOMMENDED`, `HYPOTHESIS`.
- **§12 Opportunity ↔ Research Session.** An Opportunity is not owned by the
  session that first found it; sessions produce *observations*.

---

# New in V2.1

## 17. Claim — a persisted entity

### 17.1 Definition

A **Claim** is an assertion about an Opportunity that can be independently
evaluated through evidence.

```text
Workspace
  └── Opportunity
        └── Claim              ← the unit evidence accumulates against
              └── Evidence
```

It is the unit `evidence-aggregation-framework-v1.md` operates on. Before V2.1
that framework had no unit: it was executable and unusable.

### 17.2 A Claim is not a ClaimType

This is the distinction the entity exists to make, and it is easy to lose.

| | Claim | `ClaimType` |
|---|---|---|
| What | an assertion: *"Users want AI-assisted match predictions"* | an epistemic category: `INFERRED` |
| How many | unbounded | exactly five (§7) |
| Identity | `ClaimId`, a UUID | none — it is a label, not a thing |

A Claim **carries** a `ClaimType`. A system that used one as the other would
have exactly five claims.

`ClaimId` joins the identifier set alongside `OpportunityId` and `EvidenceId`,
declared once in `packages/contracts` (ADR-009). It is **not** an
`OpportunityId`, and the claim text is **not** its identity: the text may be
rewritten, the identity may not.

### 17.3 One Opportunity, many Claims

An Opportunity may have zero or many Claims. A Claim belongs to **exactly one**
Opportunity.

This is the correction A-13 names. One opportunity carries several assertions
that do not stand or fall together — one well supported, another contradicted, a
third never investigated. Aggregating at the opportunity level averages away
precisely the distinctions the aggregation model preserves.

Cross-opportunity claim sharing is **deliberately not modelled**. If
deduplication later shows the same assertion recurring, that is a separate
decision with its own questions, and it is not answered by guessing now.

### 17.4 A Claim is not owned by a ResearchSession

The rule §12 established for Opportunity, applied unchanged.

```text
ResearchSession
      ↓
ClaimSessionObservation
      ↓
Claim
```

Sessions produce **observations** using the same `ObservationKind` vocabulary as
opportunity observations. The same Claim may receive new evidence in later
sessions, and must **not** be duplicated because a second session encountered
it — that would split its evidence in two.

### 17.5 Temporality is declared on the Claim

Every Claim declares `ClaimTemporality`: `EVERGREEN` or `TEMPORALLY_SENSITIVE`.

**Declared, never inferred from the source.** The same platform carries an
evergreen fact and a trend stale in a week, so a temporality read off the source
would be wrong for one of them with no way to tell which.

A Claim **names** a `claim_feature`; it does **not** own a half-life. That
number belongs to a versioned `EvidenceAggregationProfile`, and no profile has
one (`evidence-aggregation-framework-v1.md` §9).

### 17.6 Evidence is claim-scoped

Evidence references a Claim, not an Opportunity. It carries an
`EvidenceDirection`, an `EvidenceObservationCategory`, and an
`EvidenceIndependenceState` — all defined by the aggregation framework and
promoted to contracts, not redefined here.

### 17.7 Statement revision

A Claim's statement may be revised. Revisions are **append-only** and identity
is stable across them.

An aggregation that evaluated revision 2 must still be able to read revision 2.
Without that, every historical result becomes unreproducible the moment somebody
fixes a typo.

Full model: [`claim-model-v1.md`](claim-model-v1.md).
Persistence rationale: [ADR-015](../architecture/adr/ADR-015-claim-persistence-and-versioning.md).

### 17.8 Lifecycle is editorial, never epistemic

`ClaimLifecycle` has two values: `ACTIVE` and `WITHDRAWN`.

**There is no `VALIDATED` and no `REJECTED`.** A lifecycle state derived from
evidence would freeze a conclusion that later evidence could contradict. What a
claim is worth is read from its aggregation, every time; the lifecycle says only
whether the claim is in circulation.

### 17.9 Governance

`ClaimLifecycle`, `ClaimOrigin` and `ObservationKind` are **CLOSED enums** under
§14.2: each requires exhaustive branching. Adding a value is a material semantic
change requiring a new ontology version and, where architectural, an ADR.

`claim_feature` is **not** an enum. It is a free key that an aggregation profile
looks a half-life up under, and the useful set of features is unknown until
calibration has run — inventing a closed list now would be exactly the guess
§14.1 exists to prevent.
