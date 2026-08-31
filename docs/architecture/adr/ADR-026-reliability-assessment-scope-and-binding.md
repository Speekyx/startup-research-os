# ADR-026 — Reliability is assessed per measurement-and-purpose, and bound explicitly

**Status:** Accepted
**Date:** 2026-08-31
**Mission:** Sprint 1 / Mission 1.14
**Extends:** [ADR-014](ADR-014-evidence-aggregation-reference-implementation.md)
(the aggregation model reliability feeds),
[ADR-025](ADR-025-claim-interpretation-run-and-considered-inputs.md) (a result
must name what produced it).
**Related:** [`evidence-reliability-contract-v1.md`](../../data/evidence-reliability-contract-v1.md),
[`evidence-reliability-gap-analysis-v1.md`](../../data/evidence-reliability-gap-analysis-v1.md),
[`evidence-reliability-review-guide-v1.md`](../../data/evidence-reliability-review-guide-v1.md).

---

## Context

`evidence-aggregation-framework-v1.md` §3 says reliability is a property of
*this evidence record, against this claim, given how it was collected*. That is
right and it is unscalable: it asks for a human judgement per Evidence row.

The two obvious escapes are both forbidden, and forbidden for the same reason:

```text
source_reliability["world-bank"] = 0.95     a coefficient. A platform is not a
                                            reliability -- the same platform
                                            carries a methodology note and a
                                            rumour

reliability = 0.5 because unknown           a measurement claiming the middle,
                                            entering min() as a real number
```

So the mission needs a **middle term**: a scope broad enough that a reviewer
writes a bounded number of assessments, and narrow enough that it never becomes
a statement about a source.

Three decisions follow, and each is hard to reverse once assessments and results
exist. That is why they are here.

---

## Decision 1 — the assessment scope is (measurement, purpose), never (source)

An assessment applies to a five-part scope:

```text
source_id           who published it
resource_id         which published stream or dataset
record_kind_id      what shape of observation it was normalized into
claim_type          the epistemic type of the claim it bears on
proposition_kind    WHAT KIND of proposition -- the purpose
```

The first three name the **measurement**. The last two name the **purpose**.
Neither half is sufficient and neither is optional.

`proposition_kind` is the key insight, and it was not invented here. Mission
1.13.1 put a discriminator at the head of every `proposition_facts` object so two
proposition shapes could not collide in a hash:

```text
source_reported_metric_period_change
source_reported_term_frequency_change
source_reported_term_frequency_contrast
```

That discriminator names what a claim asserts *in kind*, which is exactly what
"purpose" means in "reliability is purpose-relative". It already exists, it is
already deterministic, and it is already stored.

### Why this is not a source coefficient

`world-bank` alone matches nothing. `world-bank` + `indicator/SP.POP.TOTL` +
`numeric_observation` matches nothing. An assessment applies only when **all
five** parts match, so the framework's own example works out correctly without
any special case:

- a World Bank population record used for
  `source_reported_metric_period_change` may have an assessment;
- the same record used for a demand proposition has a **different**
  `proposition_kind`, matches no assessment, and is `NON_SCORABLE`.

The purpose-relativity is structural. There is no path by which a value assessed
for one purpose reaches another.

### What is deliberately excluded from the scope

| Excluded | Why |
|----------|-----|
| `signal_type_id` | The derivation between measurement and proposition is the interpreter's business, and whether it read the Signal correctly is `extraction_confidence` — a different field with a different meaning |
| `workspace_id` | See Decision 3 |
| The specific claim, revision or Evidence id | That is the per-row judgement this decision exists to avoid requiring |
| Source policy status | Legal permission is not epistemic quality, in either direction |

### Identity

`assessment_key` = sha256 over the canonical JSON of the five scope parts.
Two reviewers assessing the same scope collide on one key; a reviewer revisiting
a scope is recognised as revisiting it. Same construction as `proposition_key`
one layer down, and for the same reason.

The scope key is **not** versioned. `(assessment_key, version)` is the row.

---

## Decision 2 — resolution is late, and the binding is recorded

Reliability for generated Evidence is **resolved at aggregation time**, and the
aggregation records **which assessment id and version it used for each row**.

The two alternatives were rejected as follows.

**Copy the value onto the Evidence row at creation.** History is stable, but the
row can never pick up a correction, and — decisively — nothing records *where the
number came from*. `evidence-aggregation-framework-v1.md` §13 requires that a
score's ingredients be reconstructible, and a bare `0.9` in a column is not
reconstructible.

**Resolve against whatever is current, recording nothing.** Correcting an
assessment tomorrow silently changes yesterday's score. Mission 1.14 §19 forbids
this outright, and it is the same failure `evidence_snapshot_digest` was added to
prevent one layer up.

**Resolve late, record the binding.** A result carries, per contributing row, the
assessment id, its version, its origin and its `reviewed_at`. Re-running against
the recorded bindings reproduces the number exactly. Re-running against current
assessments produces a *different* result with a different digest — identifiable
**as** a recomputation rather than silently replacing the original.

This is deliberately the same shape as D-08's unresolved question and does not
resolve it. What it does is refuse to make it harder: the ingredients for
telling an original result from a recomputed one are recorded rather than
discarded.

### Precedence, so two answers cannot disagree

`scoring.evidence.reliability` is not removed. A human or an importer may state a
value for a specific record with their own basis, and that is more specific than
a class-level assessment.

```text
row.reliability IS NOT NULL   ->  DIRECTLY_SUPPLIED, and no assessment is consulted
row.reliability IS NULL       ->  resolution is attempted
```

The two can never disagree because the second only runs when the first is
absent, and the outcome is recorded either way. This is the lesson of GAP-7 in
Mission 1.13 — two answers to one question eventually disagree — applied before
the second answer exists.

### Zero, one, many

| Applicable current assessments | Outcome |
|--------------------------------|---------|
| 0 | `NO_APPLICABLE_ASSESSMENT`. Reliability stays `NULL`, the row is `NON_SCORABLE`, and the reason is named |
| 1 | `RESOLVED`. The value, with its binding |
| >1 | `AMBIGUOUS_ASSESSMENTS`. **Refused.** Reliability stays `NULL` |

**Never the closest** — "closest" needs a distance nobody defined. **Never the
maximum** — that is optimism with a mechanism. **Never the mean** — averaging two
competing reviewed judgements produces a third judgement nobody made and nobody
can defend.

A partial unique index on the scope where `superseded_at IS NULL` makes the
many-case impossible for current assessments. The resolver refuses anyway,
because a guard that trusts another guard is one schema change away from
trusting nothing.

---

## Decision 3 — assessments are GLOBAL in V1, and the reason is stated

An assessment is a statement about a **published dataset's measurement
contract**, evidenced by the publisher's own documentation. It is not a statement
about a tenant, and making it tenant-scoped would mean every workspace
re-reviewing the same World Bank methodology — producing several answers to one
question, with nothing to say which is right.

So `epistemic.reliability_assessments` is global: no `workspace_id`, no RLS
policy, `SELECT` for the runtime role, administered through a review path rather
than over HTTP. The same argument that makes `registry.sources` global.

**A workspace-scoped assessment is imaginable and is not built.** An operator
with domain knowledge their tenant alone holds could legitimately assess a scope
differently. Adding that later needs a nullable `workspace_id`, an RLS policy,
and a precedence rule (tenant beats global, or tenant refuses to coexist with
global) — a decision with its own consequences, which is why it is named here
rather than pre-empted by a nullable column nothing writes.

Until then: **no tenant data exists in this schema, so no tenant leakage path
exists.** That is a stronger property than a correctly-written policy.

---

## Consequences

**What becomes possible.** A reviewer can write a bounded number of assessments —
one per measurement-and-purpose pair actually in use — and every Evidence row of
that class resolves against it, with the binding recorded. Two assessments exist
per source family today, not seven per Evidence row.

**What stays impossible.** Reliability for a purpose nobody assessed. Reliability
inferred from a source's name, its policy status, its directness, its extraction
confidence or its claim confidence. A score whose coefficients cannot be
reconstructed.

**What it costs.** A schema, a resolver package outside
`packages/evidence-aggregation` (the guard there forbids naming a source), and
the discipline that a scope with no assessment produces no number. The seven real
Evidence rows remain `NON_SCORABLE` after this mission, because no review has
happened — which is the design working, not a shortfall in it.

**What would reverse it.** Nothing cheaply. A scope narrower or broader than
(measurement, purpose) invalidates every assessment written under it, and a
result that recorded no binding cannot be given one retrospectively.
