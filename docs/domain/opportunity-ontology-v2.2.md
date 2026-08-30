# Opportunity Ontology V2.2

**Status:** Authoritative. Supersedes `opportunity-ontology-v2.1.md`.
**Date:** 2026-08-30
**Supersedes:** V2.1 (retained as a historical specification, not deleted)
**Authorized by:** Sprint 1 / Mission 1.13 §41, which requires the interpretation
contract to be written from the pipeline that exists rather than fitted around
the historical schema, and [ADR-024](../architecture/adr/ADR-024-claim-precedes-opportunity.md).

---

## 0. Changes from V2.1

V2.2 **inherits V2.1 in full**, which in turn inherits V2 §1–§16. Section
numbering is preserved, so every existing reference to
`opportunity-ontology-v2.md §N` or `opportunity-ontology-v2.1.md §N` resolves to
the same rule here.

| Change | Section | Reason |
|--------|---------|--------|
| A Claim belongs to **at most one** Opportunity, rather than exactly one | §17.3 | The pipeline runs Signal → Evidence → Claim → Opportunity. Claims precede opportunities, and V2.1's rule made a claim about a source fact unrepresentable until somebody had invented a product for it to be about |

**Nothing else is altered.** No dimension, registry, taxonomy, market scope rule,
confidence rule, research-lifecycle rule or governance rule changed. `ClaimType`
is untouched and remains exactly five values. `ClaimLifecycle`, `ClaimOrigin`,
`ObservationKind` and `ClaimTemporality` are untouched.

**Not resolved here:** opportunity identity resolution (§12.3), A-12
non-geographic scoping (§4.8), D-03, D-08, D-12. Cross-opportunity claim sharing
remains **deliberately not modelled**.

---

## 1–16. Unchanged from V2

See [`opportunity-ontology-v2.md`](opportunity-ontology-v2.md).

## 17.1, 17.2, 17.4, 17.5, 17.6. Unchanged from V2.1

See [`opportunity-ontology-v2.1.md`](opportunity-ontology-v2.1.md). In
particular §17.4 — *a Claim is not owned by a ResearchSession* — is unchanged and
is the rule §17.3 below is now consistent with.

---

## 17.3 An Opportunity may have many Claims; a Claim has at most one

**Amended in V2.2.** V2.1 read:

> An Opportunity may have zero or many Claims. A Claim belongs to **exactly one**
> Opportunity.

It now reads:

> An Opportunity may have zero or many Claims. A Claim belongs to **at most one**
> Opportunity, and may belong to none.

### What is unchanged, and why the A-13 correction survives intact

The reason A-13 gave for moving evidence from the Opportunity to the Claim is
untouched:

> One opportunity carries several assertions that do not stand or fall together —
> one well supported, another contradicted, a third never investigated.
> Aggregating at the opportunity level averages away precisely the distinctions
> the aggregation model preserves.

Aggregation remains **per claim**. An opportunity still carries many claims. A
claim still participates in at most one opportunity's evaluation.
Cross-opportunity sharing is still not modelled, and its questions — whose
evidence set, whose workspace, what happens on delete — are still unanswered and
still not being guessed at.

### What changed, and why

A Claim may now exist **before, and without,** any Opportunity.

V2.1's rule was written when an Opportunity was the thing being described and a
Claim was an assertion about it. Since Mission 1.11 the system derives Signals
from real sources, and the interpretation layer this ontology now has to support
runs the other way:

```text
Signal → Evidence → Claim → … → Opportunity
```

A claim such as

> World Bank reported that Germany's population rose by 187,180 between 2018 and
> 2019.

is a fact about the world that a future opportunity may cite. Requiring an
Opportunity first would mean **inventing a product idea in order to record an
observation** — which inverts the evidence discipline the whole system is built
on, and which `docs/CLAUDE.md` §Core principles forbids in the sentence
*evidence before conclusions*.

`NULL` therefore means *not yet part of any opportunity's evaluation*. It is a
state, not a gap: the ordinary condition of a claim the moment it is derived.

### The cost, stated

An opportunity-scoped consumer must now handle claims that belong to no
opportunity, and a query that assumed every claim had one will need a filter.
That is the honest cost of the ordering being right.
