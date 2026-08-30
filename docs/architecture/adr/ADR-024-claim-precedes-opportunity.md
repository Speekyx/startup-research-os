# ADR-024 — A Claim precedes its Opportunity, and cannot be stored unsupported

**Status:** Accepted
**Date:** 2026-08-30
**Mission:** Sprint 1 / Mission 1.13
**Amends:** Ontology V2.1 §17.3, superseded by
[Ontology V2.2](../../domain/opportunity-ontology-v2.2.md).
**Extends:** [ADR-015](ADR-015-claim-persistence-and-versioning.md) (claim
persistence and versioning), [ADR-014](ADR-014-evidence-aggregation-reference-implementation.md)
(the aggregation unit), [ADR-020](ADR-020-signal-derivation-model.md) (a Signal
is a derivation).
**Related:** [`claim-evidence-interpretation-gap-analysis-v1.md`](../../data/claim-evidence-interpretation-gap-analysis-v1.md),
[`claim-evidence-interpretation-contract-v1.md`](../../data/claim-evidence-interpretation-contract-v1.md).

---

## Context

Mission 1.2 built the Claim model to resolve A-13: evidence pointed at an
Opportunity, which is the wrong aggregation unit. That correction was right and
is untouched here.

What it also encoded, from the domain model of Mission 0.1, is an **ordering**:

```sql
opportunity_id UUID NOT NULL
```

> Ontology V2.1 §17.3 — *A Claim belongs to exactly one Opportunity.*

At the time an Opportunity was the thing being described and a Claim was an
assertion about it. Since Mission 1.11 the system derives Signals from real
sources, and the interpretation layer Mission 1.13 defines runs the other way:

```text
Signal → Evidence → Claim → … → Opportunity
```

The contradiction is mechanical rather than a matter of taste. Mission 1.13 §43
proposes that Mission 1.13.1 begin with deterministic `OBSERVED` claim
generation. Against this schema that is impossible: there are **zero**
opportunities, and creating one would be generating a product idea from nothing —
which the same mission forbids in §51.

Two further rules were missing, and both bear on whether this layer can be
trusted at all.

---

## Decision 1 — a Claim may exist before, and without, an Opportunity

`opportunity_id` becomes **nullable**. `NULL` means *not yet part of any
opportunity's evaluation*, which is the ordinary condition of a claim the moment
it is derived.

Everything §17.3 actually argued for survives: aggregation stays per claim, an
opportunity still carries many claims, a claim still participates in at most one
opportunity's evaluation, and **cross-opportunity sharing is still not
modelled**. Only the existence requirement moves, from *exactly one* to *at most
one*.

A claim such as *"World Bank reported that Germany's population rose by 187,180
between 2018 and 2019"* is a fact about the world that a future opportunity may
cite. Requiring an Opportunity first would mean inventing a product idea in order
to record an observation — the inversion of *evidence before conclusions*.

### Cost accepted

An opportunity-scoped consumer must handle claims belonging to no opportunity,
and a query that assumed every claim had one needs a filter. Ontology V2.2
carries the change with V2.1 retained; this is a material ontology change and it
gets the version bump the change-control rule requires.

---

## Decision 2 — an automatically generated Claim cannot be stored without Evidence

A `DEFERRABLE INITIALLY DEFERRED` constraint trigger refuses a claim at COMMIT
when it has no evidence row, unless it is a `HYPOTHESIS` or its origin is
`MANUAL`.

Deferred because a claim, its first revision and its evidence are written in one
transaction and each references the others — the same reason
`claims_current_revision_fkey` is deferred, and the same mechanism migration 0007
used to refuse a satisfied condition with no verification behind it.

**`HYPOTHESIS` is exempt, and the exemption is the category's definition rather
than a loophole.** A hypothesis is a proposition worth testing and not yet
supported; requiring evidence for one would make the type unusable and would
push unsupported ideas into `INFERRED`, which is precisely the failure this rule
exists to prevent. It remains visibly and machine-readably `HYPOTHESIS`.

**`MANUAL` is exempt** because a person asserting something and then looking for
evidence is the ordinary research motion. The rule is about what a **machine**
may store unsupported.

### Cost accepted

The trigger fires on writes to `research.claims`, so it cannot catch evidence
being deleted afterwards. That is a real limit and it is recorded rather than
papered over: the invariant is enforced where a claim is created, which is where
an unsupported assertion would be introduced.

---

## Decision 3 — the interpreter is identified, and determinism is enforced

`interpreter_id` and `interpreter_version` become the producer's identity, and a
closed `ClaimInterpretationKind` (`DETERMINISTIC` | `MODEL_DERIVED`) governs the
model columns with a CHECK: a deterministic interpretation may carry **no** model
or prompt version, and a model-derived one may not omit the model version.

This is the defect `nlp.signals` carried before Mission 1.11, in the same shape.
A table whose only producer identity is a model version reads as a table of model
outputs, and a deterministic interpreter would have had to name itself by writing
free text into `origin_detail` — the field that decides whether a result is
reproducible.

`origin` is **kept**. It answers *who asserted this* — `MANUAL`, `IMPORTED`,
`SYSTEM_GENERATED` — which is a different and still useful question from *how*.

### Cost accepted

Two columns describe the producer where one used to. That is the point: they were
answering different questions and one of them was answering both badly.

---

## Consequences

**Positive**

- Mission 1.13.1 can generate deterministic `OBSERVED` claims from the seven real
  Signals without inventing an opportunity, and therefore without generating a
  product idea from nothing.
- An automatically generated market assertion with nothing behind it cannot be
  stored. That is the single rule this layer's trustworthiness rests on.
- Two pre-existing defects are closed on the way past: `evidence.claim_id` was
  nullable although evidence is claim-relative by definition, and
  `evidence.claim_type` duplicated the claim's own type in a column the
  aggregation framework never reads.

**Negative, and accepted**

- An ontology version for one sentence. The alternative was leaving a rule in
  force that the pipeline contradicts, which is worse.
- The evidence-required trigger has a blind spot on evidence deletion.
- Claims with no opportunity will accumulate before any opportunity engine
  exists. They are facts waiting for a consumer, which is the correct state, and
  they carry the ordinary 12-month retention of the tier they sit in.

**Neutral**

- No Claim, no Evidence and no Opportunity was created. All three tables hold 0
  rows.
- D-03, D-08, D-12 and A-12 are untouched, and claim identity is defined so that
  it can never depend on an embedding.
