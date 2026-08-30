# ADR-023 — A gap is never bridged, and an absent term is not a zero

**Status:** Accepted
**Date:** 2026-08-30
**Mission:** Sprint 1 / Mission 1.12.1
**Extends:** [ADR-022](ADR-022-web-ngram-source-relative-order.md) (the ordering
this depends on), [ADR-020](ADR-020-signal-derivation-model.md) (a Signal is a
derivation), [ADR-021](ADR-021-signal-derivation-run-log.md) (where a refusal
goes).
**Related:** [`lexical-frequency-change-extractor-v1.md`](../../data/lexical-frequency-change-extractor-v1.md),
[`signal-derivation-runtime-v1.md`](../../data/signal-derivation-runtime-v1.md).

---

## Context

ADR-022 closed H-32: WEB-NGRAM bucket labels are ordered within their stream.
Mission 1.12's report was explicit that this moved the problem rather than
solving it — *temporally permitted is not extractor specified* — and named four
things a sequential extractor would have to decide. Two of them are semantic and
this ADR settles both, because both affect every future temporal derivation and
both are hard to reverse once signals exist.

```text
what does ADJACENT mean when a bucket is missing?
what does it mean for a term to be ABSENT from a bucket?
```

Neither is a question about arithmetic. Getting either wrong produces signals
that look correct.

---

## Decision 1 — adjacency is exactly one published bucket step

Two observations may form a change signal only when their source labels are
**exactly one documented bucket apart**. GDELT publishes a WEB-NGRAM bucket every
15 minutes, so `20260830184500` and `20260830190000` are adjacent and
`20260830184500` and `20260830191500` are not.

Anything else is refused with `NON_CONTIGUOUS_SOURCE_BUCKETS`, a new value on
`SignalRefusalReason`. It could not reuse an existing one: `INCOMPATIBLE_SERIES`
says the observations are of different things and they are not, and
`INSUFFICIENT_INPUT_OBSERVATIONS` says there are too few and there are exactly
two. What was missing was a way to say *these two belong together and the
interval between them is not the one the source publishes*.

**The step is computed in label space, end to end.** The earlier label's own
components are advanced by 15 minutes and formatted back into a label, and the
comparison is a string comparison. Nothing becomes an instant, nothing acquires
an offset, and `validate_signals.py` fails the build if an extractor calls
`astimezone`, `now`, `utcnow` or passes `tzinfo=`.

That arithmetic is **licensed by ADR-022's certification**, not by the label's
shape. Adding 15 minutes to a wall-clock reading is only sound in a monotonic
frame, and monotonicity is exactly what H-32 established. An extractor asks the
certification for its stream and for its label scheme before it compares
anything.

### Cost accepted

A sparse series produces fewer signals, and a stream with a publication outage
produces none across it. That is the intended behaviour: a change computed
across a bucket nobody read is indistinguishable from one that happened, and the
run log records every refusal with the two labels that were not adjacent.

Interpolation, bridging and "nearest available bucket" were all considered and
rejected. Each would produce a number, and none of them a measurement.

---

## Decision 2 — a term absent from a bucket has no frequency

If a lexical term has no normalized observation in a bucket, that bucket is
**not** a bucket where the term occurred zero times.

The distinction is the normalization layer's own — *missing is never zero, zero
is a measurement and absence is not* — carried up one level. GDELT publishing
`0` for a term is the source saying "none in this window", and it is subtracted
normally. A term simply not appearing in the file says nothing at all.

So a frequency change requires **two actual source observations**. There is no
synthesis, no zero-fill and no `55 -> 0` produced by a term dropping out of a
selection.

### Why it is worth an ADR rather than a code comment

Zero-filling a sparse series is the single most natural thing to do to this
data, it makes every chart look complete, and it is wrong in a way nothing
downstream can detect. A signal saying `climate` fell by 55 is indistinguishable
from a real collapse in coverage, and the record that would have disproved it is
the one that was never read.

### Cost accepted

Sparse terms are under-represented relative to common ones, because a rare term
appears in fewer consecutive buckets and therefore yields fewer adjacent pairs.
That is a real sampling property of the output and it is recorded rather than
corrected.

---

## Decision 3 — a selection is required, and empty does not mean everything

The extractor requires an explicit `terms` parameter. One WEB-NGRAM bucket holds
hundreds of thousands of terms — the real acquisitions scanned 223,342 and
370,468 rows — and the dataset publishes 96 buckets a day since 2019.

An empty selection is a **refusal**, not a request for everything, and there is
an operational ceiling of 25 terms per derivation. Both bounds are ours and are
stated as ours; no external limit is implied.

### Cost accepted

Nothing derives GDELT change signals unattended. That is deliberate: every
bounded default — "the top 100 by count", "everything above N" — is a selection
threshold nobody reviewed, and the project's standing rule is that an invented
parameter is worse than a refusal.

---

## Consequences

**Positive**

- The first source-relative temporal signal type exists and produced **two real
  signals** from a bounded controlled acquisition, alongside **two real gap
  refusals** in the same run — the policy proven on real data rather than only
  in fixtures.
- H-29 is untouched: the window carries no bounds, `observed_at` is null, and
  no timezone appears anywhere.

**Negative, and accepted**

- Sparse and interrupted series yield fewer signals than a bridging extractor
  would produce. The difference is entirely signals that would have been
  invented.
- A future extractor wanting a rolling window over a gappy stream has to decide
  what a gap means *for that operation*, and this ADR does not pre-decide it. It
  settles adjacency for pairwise change and nothing wider.

**Neutral**

- `NON_CONTIGUOUS_SOURCE_BUCKETS` is available to any future extractor over any
  stream with a documented step; nothing about it is GDELT-specific.
