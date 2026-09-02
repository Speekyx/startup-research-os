# Answer acceptance semantics, and what they cannot support

Version: 1.0
Status: Authoritative
Created: 2026-09-03 (Sprint 1 / Mission 1.32)
Subject: canonical `docker`
Field: `answers.has_accepted_answer` on the `community_question` record kind

**This document was written before any Signal, Claim, Evidence or dimension
mapping was created.** Mission 1.32 §0 requires the assessment frozen first, and
§18 requires a test that the dimension decision preceded any inspection of
whether the packet passed. Recording it first is what makes both checkable.

---

## §0.A What the field actually means in the stored source

`answers.has_accepted_answer` is Stack Exchange's own acceptance state for one
question, as it stood **at the moment SROS collected the record**. Mission 1.18's
normalizer already wrote the meaning into the payload beside the value:

> *"the asker marked an answer accepted; not a statement that the problem is
> objectively resolved"*

Three properties follow from the platform's own model, and each bounds it
further.

- **It is one person's action.** Only the asker may accept, so the field reports a
  decision by exactly one participant, not a community judgement and not a
  verdict about the answers.
- **It is an interaction state, not a resolution state.** An asker who solved
  their problem elsewhere, lost interest, or never returned leaves the field
  `false` regardless of whether good answers arrived.
- **It is observed late.** These questions were created between 2024-03-01 and
  2024-03-31 and the state was read on **2026-09-02**, about two and a half years
  later. Any statement built on it is about the state at that observation, never
  about March 2024.

### The measured distribution, over the 88 eligible questions

| state | n |
|---|---|
| accepted answer present | **34** |
| answers received, none accepted | **38** |
| **zero answers received** | **16** |
| no accepted answer (the two rows above) | **54** |

The split matters more than the total. *Nobody answered* and *somebody answered
and the asker did not click accept* are different facts about the world, and a
single count of 54 conflates them.

---

## §0.B What it does not mean

- **Not that the problem is unsolved.** The normalizer says so in the payload.
- **Not that the asker is dissatisfied.** Nothing in the record is an evaluation
  of anything.
- **Not that existing tools are inadequate.** No tool is named or judged.
- **Not a commercial solution gap**, not willingness to pay, not a buyer.
- **Not recurrence.** Whether any two of these questions concern the same problem
  is the relation Mission 1.27 **parked**.
- **Not a count of people.** Author identity was never acquired.

---

## §0.C Sufficient for `SOLUTION_GAP`? **No.**

The dimension asks: *is there evidence that no adequate solution exists for the
need?* Its own `never_means` list settles this:

> *never means: that absence of evidence of a solution is evidence of its absence*

"No accepted answer" **is** absence of evidence of a solution, on one site, for
one question, as one person left it. Reading it as `SOLUTION_GAP` is the exact
inference the dimension was written to forbid.

**The sharper subset does not rescue it.** The 16 questions that received **zero
answers** are a stronger observation — nobody responded at all, and two and a half
years have passed — and they still fall short. Nobody answering on Stack Overflow
is consistent with a poorly framed question, a niche configuration, an answer
that already exists in documentation, or an asker who solved it and never came
back. None of those is *no adequate solution exists*, and the distance between
them is exactly what the dimension's guard names.

## §0.D Sufficient for `SOLUTION_DISSATISFACTION`? **No, and more plainly.**

The dimension asks: *is there evidence that actors are dissatisfied with what
they use today?*

There is no dissatisfaction datum anywhere in the record. **The asker is not
evaluating a product; they are asking a question.** Acceptance state reports
whether one person clicked a button, and no reading of that button produces an
opinion about any tool. Mapping it here would not be a stretch of the evidence —
it would be a different subject entirely.

---

## The decision: `NO_EXISTING_DIMENSION`

The **measurement** is valid: a complete, bounded, deterministic count over
records already held, with the field present on all 88 and none missing. The
**mapping** is not. So the Signal, Claim and Evidence are created and map to
`frozenset()` — which Mission 1.28 established as a real answer rather than a gap,
and which four of the six registered signal types already return.

**No new dimension is invented so this measurement has somewhere to go.** Mission
1.32 §9 forbids it, and a taxonomy extended to fit a source is a taxonomy fitted
to a sample.

### What would reach these dimensions

Recorded so a later mission does not have to rediscover it.

- `SOLUTION_DISSATISFACTION` needs an actor **evaluating** something: a review, a
  rating, a comparison, a migration statement. No source in the portfolio
  publishes one for developer tooling today.
- `SOLUTION_GAP` needs evidence about what solutions **exist**, not about whether
  one question got an answer. A package registry, a documentation index or a
  competitive catalogue would speak to it; an acceptance flag cannot.
- **The zero-answer subset (16) is the most promising thing here and is still not
  either dimension.** It is worth a future look as a distinct measurement — a
  question nobody answered in two and a half years says more than one whose asker
  did not click accept — but it needs its own bound, and it would still not
  establish that no solution exists.
