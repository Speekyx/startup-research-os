# Lexical Frequency Contrast Extractor V1

**Status:** **Implemented.** `lexical-frequency-contrast@1.0.0`. **One real
signal** derived from the two real GDELT observations, both `PARTIAL`.
**Date:** 2026-08-30 (Mission 1.11.1)
**Code:** `sros_nlp.extractors.lexical_frequency_contrast`
**Related:** [`signal-contract-v1.md`](signal-contract-v1.md),
[`signal-temporal-semantics-v1.md`](signal-temporal-semantics-v1.md),
[`gdelt-web-ngram-normalizer-v1.md`](gdelt-web-ngram-normalizer-v1.md),
[ADR-020](../architecture/adr/ADR-020-signal-derivation-model.md).

---

## 0. What it produces

```text
gdelt|web-ngrams/1gram|20260830091500|ENGLISH|climate   count 55
gdelt|web-ngrams/1gram|20260830091500|ENGLISH|weather   count 36
    ↓
signal_type       lexical_frequency_contrast
quantity_family   LEXICAL_FREQUENCY
magnitude         19   ABSOLUTE_DIFFERENCE   unit_state NOT_ESTABLISHED
direction         NOT_APPLICABLE
temporal_basis    SAME_PERIOD_LABEL
window            20260830091500, INTERVAL, 2 observations, NO BOUNDS
scope             gdelt · terms [climate, weather] · ENGLISH / cld2-language-name
parameters        {"terms": ["climate", "weather"]}
observed_at       NULL
confidence        1.0
```

**What it asserts, in full:** within one source period label and one exact source
language label, these two terms occurred with measured frequencies differing by
exactly 19.

**What it does not assert:** that `climate` is more important, more popular, more
in demand, trending, or that `weather` is declining. Mission 1.11 §25 lists what
else a term frequency can be — a news event, a crisis, a celebrity, weather
itself, politics, a disaster, a sports fixture. It is a source-frequency
relation between two tokens in text GDELT processed, and nothing more.

## 1. Identity and versioning

| | |
|---|---|
| extractor | `lexical-frequency-contrast@1.0.0` |
| signal type | `lexical_frequency_contrast` (registry entry, migration 0012) |
| quantity family | `LEXICAL_FREQUENCY` |
| reads | `lexical_frequency_observation` |
| derivation kind | `DETERMINISTIC` |
| schema | `sros.signal/1` |

## 2. H-32 is respected by construction, not by a check that could be removed

The grouping key carries the **exact source period label**. Two buckets never
share a key, so they never meet, so **no ordering between them is required,
asserted or possible**.

There is no frequency change, no growth, no decline, no moving average and no
rolling window in this extractor, and none may be added while H-32 is open. The
temporal basis is `SAME_PERIOD_LABEL`, the window carries **no bounds**, and
`observed_at` is `NULL` — which the database enforces independently.

Two labels that look ordered are still not ordered. `20260830091500` and
`20260830093000` are refused as `INCOMPATIBLE_SERIES`, and a test asserts it.

## 3. H-30 — the label, never the tag

Both inputs must share the **exact source language label and its scheme**.
`ENGLISH` from `cld2-language-name` equals `ENGLISH` from `cld2-language-name`,
and that asserts nothing about what either maps to.

`canonical_language_tags` is absent from the scope, and the model refuses one
anyway: a tag may appear only where the derivation required `CANONICAL_LANGUAGE`
and every input supplied it, which no GDELT record does. `ENGLISH` and `FRENCH`
are different labels and are refused rather than aggregated.

## 4. Gram size — same only, and here is the decision (§19)

**A unigram count and a bigram count are counts of different kinds of thing.**
`climate` in the 1gram file counts occurrences of one token; `climate change` in
the 2gram file counts occurrences of an adjacent pair. Subtracting one from the
other produces a number with no referent.

So `gram_size` is part of the grouping key. The resource id already differs
between `web-ngrams/1gram` and `web-ngrams/2gram`, and the gram size is checked
as well — so a future source publishing both from one resource cannot silently
merge them. A cross-gram pair is `INCOMPATIBLE_SERIES`.

`1gram vs 1gram` ✅ · `2gram vs 2gram` ✅ · `1gram vs 2gram` ⛔

## 5. `terms` is required, and that is the design

One WEB-NGRAM file holds hundreds of thousands of rows — the real acquisition
read **223,342**. An unselected all-pairs sweep over one bucket is O(n²):
roughly 2.5 × 10¹⁰ pairs, none of which anybody asked for.

Every bounded default is an invented threshold. "Top 100 by count" is a
selection rule nobody reviewed, and the project's standing rule is that an
invented parameter is worse than a refusal.

So the caller **names exactly two terms**, and the names are canonically sorted
in one place, fingerprinted and persisted like any other output-affecting value.
`["weather", "climate"]` and `["climate", "weather"]` are the same derivation
with the same fingerprint.

Three terms is a different assertion with a different magnitude shape, and it is
a version bump rather than a loosened check.

## 6. Ordering — by the term text, verbatim

Position 0 is the lexicographically first term, using the **source text
unchanged** — not trimmed, not case-folded, not normalised. Reversing the rows a
query returns produces the same signal, the same fingerprint and the same
magnitude, and a test asserts it with `"  spaced  "` and `"climat\e|d"` among
the fixtures.

## 7. Magnitude — a difference, and why not a ratio

```text
magnitude = count(first term) − count(second term)
kind      = ABSOLUTE_DIFFERENCE
```

**`ABSOLUTE_DIFFERENCE`, never `ABSOLUTE_CHANGE`.** Nothing changed: both counts
were measured in the same bucket. The temporal kind would assert a movement over
time that H-32 leaves unestablished, and a consumer branching on magnitude kind
has to be able to tell a contrast from a movement. The value was added to the
contract for this (`1.6.0` → `1.7.0`).

**A ratio was considered and rejected.** `55/36` does not terminate, so an exact
`Decimal` division needs a precision — and a precision nobody stated is the fake
precision Mission 1.11 §8 forbids. A difference is exact, always defined, and
has no denominator to special-case.

**No unit.** GDELT publishes four columns and none is a unit, so the state is
`NOT_ESTABLISHED`. `"mentions"`, `"occurrences"` and `"articles"` appear nowhere
in this extractor, exactly as they appear nowhere in the normalizer.

**No 0–100 attention score, and none deferred pending a formula.**

## 8. Direction — `NOT_APPLICABLE`, and it has to be

A same-bucket contrast is not temporal change. `INCREASING` because one term's
count is larger would say the frequency *rose*, which is a statement about time
nothing here established. The database refuses it independently: a direction
other than `NOT_APPLICABLE` requires an ordered temporal basis.

## 9. Required facts — the first production proof that PARTIAL is usable

```text
EXACT_NUMERIC_VALUE · LEXICAL_TERM · SOURCE_PERIOD_LABEL · SOURCE_LANGUAGE_LABEL
```

Deliberately **not** `COMPARABLE_INSTANT` and **not** `CANONICAL_LANGUAGE`.

Every real GDELT record is `PARTIAL`, carrying `PERIOD_TIMEZONE_NOT_ESTABLISHED`
and `LANGUAGE_NOT_MAPPED`. Neither is a fact this derivation needs, so both
records contribute with `withheld_facts` empty — and the signal exists.

That is Mission 1.11's central quality rule finally exercised in production:
**`PARTIAL` is not a verdict on usability.** What matters is whether the
*specific* missing fact matters to the *specific* derivation. No quality string
is branched on anywhere in the extractor; the model evaluates the required facts
against each record's own reasons.

## 10. The one real signal

```text
records considered 2 · groups 1 · derived 1 · refused 0 · signals new 1
repeat pass        signals new 0 · unchanged 1
```

| | |
|---|---|
| magnitude | `19` (`55 − 36`) |
| kind | `ABSOLUTE_DIFFERENCE`, `NOT_ESTABLISHED` unit |
| direction | `NOT_APPLICABLE` |
| basis | `SAME_PERIOD_LABEL`, no bounds |
| `observed_at` | `NULL` |
| inputs | both `PARTIAL`, both `CONTRIBUTED`, `withheld_facts` empty |

## 11. What it does not do

Interpret, classify, rank, embed, cluster, score, contact a network, map a
language, assign a timezone, compare buckets, or turn a term into a topic.
