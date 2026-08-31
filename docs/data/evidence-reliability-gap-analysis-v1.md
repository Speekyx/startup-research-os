# Evidence Reliability Gap Analysis V1

**Analysis.** Mission 1.14 §31. Written **before** any schema change, against the
system as it stands after Mission 1.13.1.

Resolved by: `evidence-reliability-contract-v1.md`,
`evidence-reliability-review-guide-v1.md`, ADR-026, migration 0019.

---

## 0. Method

The seven real Evidence rows are `NON_SCORABLE` for one reason:
`MISSING_RELIABILITY`. That is the designed behaviour and not a defect — Mission
1.13.1 wrote `NULL` deliberately, because reliability is purpose-relative and
D-03 is blocked.

This analysis asks a narrower question than "how do we get a score": **what would
a system need in order to hold a reviewed reliability value honestly?** Each gap
below is stated with what exists, what it cannot express, and what would go wrong
if it were papered over.

Audited: `scoring.evidence`, `packages/evidence-aggregation`,
`REFERENCE_PROFILE_V1`, `registry.sources`, `registry.source_policy_reviews`,
`registry.source_policy_evidence`, `registry.source_capabilities`,
`research.claims` / `claim_revisions`, `nlp.signals`,
`evidence-confidence-framework-v1.md`, `evidence-aggregation-framework-v1.md`,
`scoring-framework-v1.1.md`.

Twelve gaps, in five classes.

---

## 1. The finding that governs the rest

### GAP-1 — reliability is per-pairing, and nothing can hold a per-pairing judgement at scale

**Class:** domain + persistence.

`evidence-aggregation-framework-v1.md` §3 is unambiguous:

> Reliability is a property of **this evidence record, against this claim, given
> how it was collected**.

`scoring.evidence.reliability` is therefore a per-row column, and its comment
says so. That is semantically right and operationally impossible: it requires a
human judgement per Evidence row. Seven rows today; the first source family with
real volume makes it unreviewable, and an unreviewable field gets filled with a
default — which is exactly the `0.5 because unknown` the framework forbids.

**The gap is not that the semantics are wrong. It is that nothing sits between
"a coefficient per source" (forbidden) and "a judgement per row" (unscalable).**

Everything below follows from needing that middle term.

---

## 2. Scope and identity gaps

### GAP-2 — there is no vocabulary for the PURPOSE a piece of evidence serves

**Class:** domain + contract.

"Purpose-relative" appears in three authoritative documents and is defined in
none of them as a thing the system can name. The framework's own example —

> a World Bank population figure is highly reliable evidence about German
> population and nearly worthless evidence about German software spending

— distinguishes two *purposes*, and the schema has no field for either.

What the system does have, since Mission 1.13.1, is `proposition_facts`, whose
first key is a **proposition kind** discriminator:

```text
source_reported_metric_period_change
source_reported_term_frequency_change
source_reported_term_frequency_contrast
```

That is the missing vocabulary, already present and already deterministic. It
names what the claim asserts *in kind*, which is precisely what "purpose" means
here. It was introduced so two proposition shapes could not collide in a hash;
it turns out to be the reusable unit of purpose.

**Why this matters:** without it, any assessment scope collapses to something
source-shaped, and a source-shaped scope is the coefficient the mission forbids.

### GAP-3 — no entity can carry a reviewed reliability judgement

**Class:** persistence.

There is nowhere to record: what was judged, at what value, on what basis, by
whom, when, under which version, and over what scope. The nearest existing
structures are the wrong shape:

| Existing | Why it does not fit |
|----------|---------------------|
| `registry.source_policy_reviews` | Answers *may we collect this*. Overloading it would make legal permission and measurement quality one row, which is the category error `evidence-aggregation-framework-v1.md` §3 names |
| `registry.source_capabilities` | What a source *can* provide. Capability is not quality |
| `registry.source_signal_coverage` | What a source *could* expose. Explicitly carries no weight, no score, no confidence — adding one would reopen D-03 sideways |
| `scoring.evidence.reliability` | The value, with no room for its basis |

### GAP-4 — an assessment would have no deterministic identity

**Class:** contract.

Two reviewers assessing the same scope must produce one assessment, and a
reviewer revisiting a scope must be recognised as revisiting it. Nothing today
defines what makes two assessments *the same assessment at a different version*
rather than two unrelated rows.

The same problem `proposition_key` solved for claims one layer down, unsolved
here.

---

## 3. Basis and authority gaps

### GAP-5 — a reliability value would have no machine-readable basis

**Class:** persistence + contract.

`registry.source_policy_evidence` is the pattern the system already uses for
"this judgement rests on these retrieved documents": review id, document type,
title, URL, section, a short summarized finding, an excerpt capped at 1000
characters, retrieval time and a fingerprint. Full documents are deliberately
not stored.

Nothing equivalent exists for an epistemic judgement, so a reliability value
today could only be a number with a sentence beside it — and
`"World Bank is trustworthy"` is a sentence.

### GAP-6 — nothing distinguishes a reviewed judgement from a guess

**Class:** contract.

`evidence-confidence-framework-v1.md` §3 lists "initial heuristic examples" —
*first-party structured data: high*, *community posts: medium* — and calls them
"starting priors, not immutable constants". Read literally, that is a source-type
coefficient table, and it predates both the aggregation framework's §3 and this
mission's core rule.

Nothing in the schema would prevent a writer from turning that list into stored
values, and nothing would record that they came from a heuristic rather than
from a measurement contract.

**There is also no way to refuse a model-originated value.** An origin
vocabulary with no `MODEL_GUESSED` member is only a guarantee if the vocabulary
is closed and enforced.

---

## 4. Applicability and reproducibility gaps

### GAP-7 — no matcher, so no defined behaviour for zero, one or many

**Class:** aggregation.

Given an Evidence row, nothing decides which assessment applies. The three
outcomes that need defining are exactly the three that get silently wrong
answers when undefined:

| Matches | The tempting wrong answer | Why it is wrong |
|---------|--------------------------|-----------------|
| 0 | fall back to a source default | The forbidden coefficient, arrived at by a different route |
| 1 | — | The only case that is straightforward |
| >1 | take the closest / the max / the mean | "Closest" needs a distance nobody defined; max is optimism; a mean of two competing reviewed judgements is a third judgement nobody made |

### GAP-8 — binding to "latest" would rewrite history silently

**Class:** aggregation.

If reliability is resolved at aggregation time against whatever assessment is
current, then correcting an assessment tomorrow changes yesterday's Evidence
Score with no record that anything moved.

If instead the value is copied onto the Evidence row at creation, history is
stable but the row can never pick up a correction, and **nothing records which
assessment produced the number** — so a score's coefficients cannot be
reconstructed, which `evidence-aggregation-framework-v1.md` §13 requires.

Both horns are wrong. This is a version-selection problem of the same family as
D-08, and it is hard to reverse once results exist.

### GAP-9 — an aggregation result cannot say which coefficients it used

**Class:** aggregation.

`EvidenceAggregationResult` carries `evidence_snapshot_digest` over the
contributions actually used, which captures the *values*. It does not capture
**where a reliability value came from** — assessment id, version, basis, who
reviewed it and when.

§20 of this mission is explicit: *do not produce a score whose coefficients
cannot be reconstructed.* Today one could.

### GAP-10 — the resolver cannot live in the aggregation package

**Class:** architecture.

`validate_evidence_aggregation.py` asserts that **no registered source id
appears anywhere in `packages/evidence-aggregation/`**, and a test asserts that
two evidence sets differing only in `source_id` produce identical numbers.

A resolver matches on source and resource. Putting it in that package would
either break the guard or require weakening it — and the guard is what keeps
source identity out of the mathematics. The resolver needs its own home, on the
same side of the seam as the existing row adapter.

---

## 5. Boundary gaps

### GAP-11 — nothing prevents reliability from being inferred from a neighbour

**Class:** contract.

Four fields on the current Evidence rows are `1.0`, and each is `1.0` for a
reason that says nothing about reliability:

| Field | Value | What it means | What it does not mean |
|-------|-------|---------------|----------------------|
| `relevance` | 1.0 | The claim restates *this* Signal | That the Signal is dependable |
| `directness` | 1.0 | It bears on the claim itself | That the measurement is sound |
| `extraction_confidence` | 1.0 | The interpreter read the Signal correctly | That the source measured correctly |
| `interpretation_confidence` (on the revision) | 1.0 | The sentence restates the Signal correctly | Anything about the world |

A propagation rule — "deterministic interpretation, therefore reliability 1.0" —
is one line of code away and would look reasonable in review. Nothing forbids it
mechanically.

The same holds for policy status: `APPROVED` and `APPROVED_WITH_CONDITIONS` are
legal states, and no formula may convert one into a number.

### GAP-12 — the tenant scope of an assessment is undecided

**Class:** contract.

Evidence is workspace-scoped. An assessment of a public dataset's methodology is
a statement about the dataset, not about a tenant — and making it tenant-scoped
would mean every workspace re-reviewing the same World Bank documentation, with
seven answers and no way to tell which is right.

But a workspace-specific judgement is imaginable (an operator who knows their
own domain), and making everything global forecloses it.

Undecided is the gap; deciding it in passing, in a migration, would be the
mistake.

---

## 6. What is already right, and stays

- **`q_i = min(components)`.** A weak reliability cannot be paid for by a strong
  relevance, which is the whole reason reliability matters.
- **Missing means `NON_SCORABLE`, never `0.5` and never `0.0`.** Already
  enforced in `evaluate_item`, already producing the honest answer on the seven
  real rows.
- **No per-platform coefficient anywhere in the aggregation package**, asserted
  mechanically against the source catalog.
- **Policy status is not reliability**, stated in the framework and kept true by
  the fact that the aggregation package cannot see a source id.
- **`REFERENCE_PROFILE_V1` is `UNCALIBRATED`** with no half-life, and the engine
  refuses to run it without an explicit opt-in.
- **`scoring.evidence.reliability` is nullable and stays nullable.**

None of these needs changing, and this mission changes none of them.

---

## 7. What this analysis does not decide

- **Whether any of the seven rows should receive a value.** That is a review
  outcome, not a schema outcome, and the contract must work identically whether
  the answer is yes or no.
- **What number any particular assessment should carry.** No document produced
  by this mission proposes a value.
- **Whether reliability review counts as calibration.** It does not — §22 — but
  the profile status machinery already says so and needs no change.
- **D-03.** Reliability is one of its blockers, not all of them; §21's inventory
  belongs in the report.
