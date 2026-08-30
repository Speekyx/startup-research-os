# Signal Temporal Semantics V1

**Status:** Authoritative for the Signal layer. Defines what a derivation may
assert about time, and what it may not while **H-29** and the new **H-32** are
open.
**Date:** 2026-08-30 (Sprint 1 / Mission 1.11)
**Related:** [`signal-contract-v1.md`](signal-contract-v1.md),
[`gdelt-web-ngram-normalizer-v1.md`](gdelt-web-ngram-normalizer-v1.md),
[`normalized-record-v1.md`](normalized-record-v1.md) §7.1,
[ADR-019](../architecture/adr/ADR-019-lexical-frequency-observation.md),
[ADR-020](../architecture/adr/ADR-020-signal-derivation-model.md).

---

## 1. The one thing this document exists to keep apart

```text
ORDER            which of these two observations came first
GLOBAL INSTANT   what moment each of them corresponds to
```

They are different questions, they need different evidence, and collapsing them
is how a timezone gets invented. A source can make the first answerable while
leaving the second open, and it can do the reverse.

The normalization layer already keeps a weaker version of this distinction:
`NormalizedTimezoneState` says whether a period's bounds are timezone-aware, and
a `NOT_ESTABLISHED` period carries naive wall-clock bounds and no `observed_at`.
That answers *is there an instant*. It does not answer *is there an order*, and
Mission 1.11 §13 is right that the two must be assessed separately.

---

## 2. `SignalTemporalBasis` — four states, each with a different requirement

```text
NONE | SAME_PERIOD_LABEL | ORDERED_PERIODS | COMPARABLE_INSTANTS
```

| Basis | What the derivation used | Required fact | Window carries |
|---|---|---|---|
| `NONE` | No temporal relation between inputs at all | — | labels, resolution, count |
| `SAME_PERIOD_LABEL` | Every input carries the **identical** source period label | `SOURCE_PERIOD_LABEL` | one label, resolution, count |
| `ORDERED_PERIODS` | The inputs are placed in sequence within one source stream | `SOURCE_RELATIVE_ORDER` | labels in derivation order, resolution, count |
| `COMPARABLE_INSTANTS` | The inputs are placed on a shared timeline | `COMPARABLE_INSTANT` | labels, resolution, count, **aware `start` and `end`** |

Two structural rules, both enforced rather than documented:

- **`start` and `end` exist only under `COMPARABLE_INSTANTS`**, and are
  timezone-aware there. Any other basis carries no bounds at all. This is
  `CanonicalPeriod`'s aware/naive rule carried one layer up, and it is the
  reason a Signal cannot quietly acquire a timeline its inputs never had.
- **`observed_at` on the row is `NULL` unless the basis is
  `COMPARABLE_INSTANTS`**, enforced by a database CHECK. So the database
  refuses a GDELT signal with an event time, in the same place and for the same
  reason the normalizer refuses one.

`SAME_PERIOD_LABEL` is worth its own value rather than being folded into `NONE`.
A contrast between two terms in one bucket is valid *because* they share a
bucket, and a reader must be able to see that the equality was checked.

---

## 3. What a GDELT WEB-NGRAM observation actually gives

```text
period.label           "20260830091500"     the source's own 14 digits, verbatim
period.type            INTERVAL             a 15-minute bucket
period.start / end     naive wall clock     2026-08-30T09:15:00 .. 09:30:00
period.timezone_state  NOT_ESTABLISHED
observed_at            NULL
```

Three questions, and they have three different answers.

### 3.1 Equality — established

Two observations carrying the identical label, from the identical source and
resource, are observations of the same bucket. This needs no timezone: it is
string equality over a value the source published, in one publication stream.

**Available today. `SAME_PERIOD_LABEL` is granted for GDELT.**

### 3.2 A global instant — not established (H-29)

No first-party document read in review 3 states a zone for `DATE`. Mission 1.9.1
recorded UTC; that was not established and review 3 does not assert it. Without
it, `20260830091500` cannot be placed on a timeline shared with any other
source.

**`COMPARABLE_INSTANT` is refused for GDELT. Blocked by H-29.**

### 3.3 Order within the stream — not established either, and this is new (H-32)

This is the question Mission 1.11 §13 asks, and it deserves the argument rather
than a verdict.

**The case for granting it.** `YYYYMMDDHHMMSS` is fixed-width, so lexicographic
order equals chronological order *within any single fixed offset*. The label is
also the published filename, and two files in one directory cannot share a name
— so a repeated label would be a collision a system publishing every fifteen
minutes for years would not survive unnoticed. On that reasoning the stamps come
from a monotonic, non-repeating clock, and ordering is sound without knowing
which clock.

**Why that is not enough.** It is an inference about the publisher's mechanism,
not a retrieved statement about the data. If the stamps were local time in a
zone observing daylight saving, one hour per year would repeat and order would
invert inside it — and the filename argument only says GDELT would have noticed
*something*, not that this system may assume what they did about it. This is the
same class of reasoning `geography-mapping-v1.json` exists to replace: a code's
shape and a label's plausibility are not a basis, and the first case that
differs is silently wrong.

**Decision.** `SOURCE_RELATIVE_ORDER` is **defined** in the model and **not
granted** to GDELT. Recorded as **H-32**.

### 3.4 Why H-32 is separate from H-29, and why that matters

H-32 is **strictly weaker** than H-29 and separately answerable:

- a first-party page stating the zone answers **both**;
- a first-party page stating only that the stamps are monotonic and
  non-repeating answers **H-32 alone**, and unblocks every within-stream
  sequential derivation without anyone asserting UTC.

Folding the two together would make the cheap question wait for the expensive
one. Keeping them apart is the practical payoff of §1's distinction, and it is
why the model carries two required facts instead of one timezone flag.

---

## 4. Which operations are safe, and which are blocked

**Legend.** ✅ available now · ⛔ blocked, with what would unblock it.

### 4.1 GDELT WEB-NGRAM

| Operation | Basis needed | Status |
|---|---|---|
| Read one record's frequency | — | Not a Signal at all (contract §3) |
| Contrast two terms' frequencies within one bucket, one language label | `SAME_PERIOD_LABEL` | ✅ |
| Count the distinct buckets a term appears in | `NONE` — a set cardinality, no order | ✅ |
| Compare the same term across two buckets | `ORDERED_PERIODS` | ⛔ **H-32** |
| Frequency change, growth rate, moving average, momentum, trend | `ORDERED_PERIODS` | ⛔ **H-32** |
| Rolling or baseline window over buckets | `ORDERED_PERIODS` | ⛔ **H-32** |
| Align a GDELT bucket with a World Bank year, or with any other source | `COMPARABLE_INSTANTS` | ⛔ **H-29** |
| Compare against a differently zoned source | `COMPARABLE_INSTANTS` | ⛔ **H-29** |
| Anything reported "as of" a wall-clock time | `COMPARABLE_INSTANTS` | ⛔ **H-29** |

**Closing H-32 alone unblocks six of these. Closing H-29 alone unblocks all
nine**, since a stated zone establishes order too.

### 4.2 World Bank Indicators

Periods are `YEAR` with `timezone_state = ESTABLISHED` and aware bounds, so both
temporal facts are available.

| Operation | Basis | Status |
|---|---|---|
| Read one year's value | — | Not a Signal (contract §3) |
| Change in one metric, one geography, between two years | `COMPARABLE_INSTANTS` | ✅ |
| Contrast two geographies at the same year | `SAME_PERIOD_LABEL` | ✅ |
| Multi-year sequence over one metric and geography | `COMPARABLE_INSTANTS` | ✅ |

**The source with six `VALID` records supports more temporal derivations than
the source with two `PARTIAL` ones, and the whole difference is H-29 and H-32.**
That is the shape of the finding worth carrying into Mission 1.11.1.

---

## 5. Resolution, and the trap it avoids

The window records the **period type of the inputs**, and every input must
agree. A derivation mixing a `YEAR` and an `INTERVAL` is refused
(`INCOMPATIBLE_INPUT_KINDS`) rather than resolved to the coarser of the two.

Silently coarsening is how a fifteen-minute bucket becomes "2026" and a
comparison between two very different measurements starts looking reasonable.
Resampling is a real operation with real parameters; it is not something a
constructor should do on the way past.

---

## 6. What this document does not do

- **It does not answer H-29.** Mission 1.11 §12 says not to, and nothing here
  assigns, infers or defaults a zone.
- **It does not answer H-32.** It states it, and states exactly what would close
  it.
- **It defines no window sizes, no baselines and no minimum spans.** Those are
  extractor parameters (Mission 1.11 §28), and picking one here would be a
  production threshold chosen in a model document.
- **It does not decide recency or decay.** Evidence freshness is
  `evidence-aggregation-framework-v1.md` §9's, computed from a claim's
  temporality and a profile half-life. A Signal has neither, and inventing one
  here would be the universal half-life that framework forbids.
