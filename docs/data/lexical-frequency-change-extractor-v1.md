# Lexical Frequency Change Extractor V1

**Status:** **Implemented.** `lexical-frequency-change@1.0.0`, the third
extractor and the first whose window basis is `ORDERED_PERIODS`. **Two real
signals** and **two real gap refusals** from one bounded controlled acquisition.
**Date:** 2026-08-30 (Mission 1.12.1)
**Code:** `sros_nlp.extractors.lexical_frequency_change`
**Related:** [`gdelt-web-ngram-temporal-evidence-v1.md`](gdelt-web-ngram-temporal-evidence-v1.md),
[`lexical-frequency-contrast-extractor-v1.md`](lexical-frequency-contrast-extractor-v1.md),
[`signal-temporal-semantics-v1.md`](signal-temporal-semantics-v1.md),
[ADR-022](../architecture/adr/ADR-022-web-ngram-source-relative-order.md),
[ADR-023](../architecture/adr/ADR-023-source-bucket-adjacency.md).

---

## 0. What it produces

```text
gdelt|web-ngrams/1gram|20260830184500|ENGLISH|climate   count 48
gdelt|web-ngrams/1gram|20260830190000|ENGLISH|climate   count 59
    ↓
signal_type       lexical_frequency_change
quantity_family   LEXICAL_FREQUENCY
magnitude         11   ABSOLUTE_CHANGE   unit_state NOT_ESTABLISHED
direction         INCREASING
temporal_basis    ORDERED_PERIODS
window            20260830184500 → 20260830190000, INTERVAL, 2 observations,
                  NO BOUNDS
scope             gdelt · climate · ENGLISH / cld2-language-name
parameters        {"terms": ["climate","weather"],
                   "pairing_strategy": "adjacent_source_buckets"}
observed_at       NULL
confidence        1.0
```

**What it asserts, in full:** for this term, this source language label and this
gram size, the GDELT source-measured frequency at a bucket differs by exactly
this much from the frequency at the immediately preceding bucket of the same
stream.

**What it does not assert:** that demand, attention, popularity, interest,
momentum or trend strength changed — and not even that the underlying phenomenon
changed. A term frequency moves when coverage moves, and coverage moves for the
reasons Mission 1.11 §25 lists: a news event, a crisis, a celebrity, weather,
politics, a disaster, a sports fixture.

## 1. Identity and versioning

| | |
|---|---|
| extractor | `lexical-frequency-change@1.0.0` |
| signal type | `lexical_frequency_change` (registry entry, migration 0014) |
| quantity family | `LEXICAL_FREQUENCY` |
| reads | `lexical_frequency_observation` |
| derivation kind | `DETERMINISTIC` — no model version, no prompt version, refused by a CHECK |
| schema | `sros.signal/1` |

**What requires a version bump:** a new pairing strategy; any change to the
adjacency rule, the arithmetic, the required facts, the grouping key or the
selection ceiling. Adding a ratio or a percentage is a version bump, not a patch.

## 2. It exists because H-32 closed, and it asks rather than assumes

This is the first extractor to use `SOURCE_RELATIVE_ORDER`, and it could not
have been written while ordering was unestablished.

**It does not infer order from the label's shape.** Before comparing anything it
asks `order_certification(source_id, resource_id)` and checks two things:

- that a certification **covers this stream** — this source and this resource.
  `web-ngrams/chargram` sits in the same directory with the same label shape and
  is not covered, and neither is any other source;
- that the certification's **label scheme is the one whose step arithmetic is
  correct** — `gdelt-web-ngram-bucket`. A certification for the same source
  under a different scheme is refused rather than used, because the 15-minute
  step is a property of the scheme and applying one scheme's step to another
  would be wrong silently.

Either failure is `REQUIRED_FACT_WITHHELD`, naming `SOURCE_RELATIVE_ORDER`.

## 3. H-29 is untouched, and the model enforces it

| | |
|---|---|
| temporal basis | `ORDERED_PERIODS` |
| window bounds | **none** — only `COMPARABLE_INSTANTS` may carry them |
| `observed_at` | **`NULL`** — a database CHECK refuses anything else |
| timezone | never assigned. `astimezone`, `now`, `utcnow`, `localtime` and `tzinfo=` are absent from every extractor, asserted over the **AST** |

The two buckets are ordered **relative to each other**. Neither is on a timeline
shared with anything, so no elapsed wall-clock duration is claimed and no
comparison with World Bank — or any other source — is possible.

## 4. Adjacency — one published step, computed in label space

ADR-023. Two observations pair only when their labels are **exactly one
documented bucket apart**:

```text
20260830184500 → 20260830190000     adjacent        ✅
20260830184500 → 20260830191500     30 minutes      ⛔ NON_CONTIGUOUS_SOURCE_BUCKETS
20260830091500 → 20260830184500     nine hours      ⛔ NON_CONTIGUOUS_SOURCE_BUCKETS
```

**The step is computed in label space from end to end.** The earlier label's own
components are advanced by 15 minutes, formatted back into a label, and compared
as a string. Nothing becomes an instant.

That arithmetic is licensed by the certification rather than by the format:
adding 15 minutes to a wall-clock reading is only sound in a monotonic frame,
and monotonicity is what H-32 established.

## 5. An absent term is absent — never a zero

ADR-023, and the rule most worth stating loudly.

A term with no normalized observation in a bucket did **not** occur zero times
there. GDELT publishing `0` is the source saying "none in this window" and is
subtracted normally; a term simply not appearing says nothing at all.

So a change needs **two actual source observations**, and a sparse series simply
yields fewer signals:

```text
bucket A  term present
bucket B  term absent
bucket C  term present
    ->  no signal. A→C is not adjacent, and B is not a zero
```

Zero-filling is the most natural thing to do to this data and it is wrong in a
way nothing downstream can detect — a signal saying `climate` fell by 55 would be
indistinguishable from a real collapse in coverage.

## 6. Grouping — the mirror image of the contrast extractor

```text
source · record kind · series dataset + resource · period type ·
language scheme + label · gram size · TERM
```

The difference between the two lexical extractors is exactly one field:

| | groups by | varies |
|---|---|---|
| `lexical-frequency-contrast` | the **bucket** | the term |
| `lexical-frequency-change` | the **term** | the bucket |

So `period_label` is absent here and `term_text` is present. Everything else is
what makes two observations the same series: dropping the language label would
subtract a French count from an English one, and dropping the gram size would
subtract a bigram count from a unigram count.

**There is no topic, category or theme in the key** because none exists. A term
is a term.

## 7. Ordering — from the certified label, never from the database

Inputs are ordered by the label's parsed components, ascending; position 0 is
the earlier bucket. Input order is part of the derivation identity, so an order
that came from the database would make the identity depend on a query plan.
Reversing the rows produces the same signal, the same fingerprint and the same
magnitude, and a test asserts it.

Two rows carrying the same bucket label for one term are refused as
`AMBIGUOUS_OBSERVATION_LINEAGE` (D-08).

## 8. Arithmetic — one exact number

```text
absolute_change = later_count − earlier_count
```

Arbitrary-precision `Decimal` on both sides. `9007199254740995 −
9007199254740993 = 2` exactly.

**`ABSOLUTE_CHANGE`, not `ABSOLUTE_DIFFERENCE`**, and the contrast between the
two lexical extractors is the reason both kinds exist. The same-bucket contrast
measures two terms at one moment — nothing changed. This measures one term
across two ordered buckets, so something did, and a consumer branching on the
magnitude kind has to be able to tell a movement from a contrast.

**No percentage and no ratio in V1** (§14). Both need a denominator rule — a term
going from 0 to 5 has no percentage — and a rounding rule, and a repeating
decimal rounded to an unstated precision is fake precision. A later version may
add one explicitly.

**No unit.** GDELT publishes four columns and none is a unit, so the state is
`NOT_ESTABLISHED`. `"mentions"`, `"occurrences"` and `"articles"` appear nowhere.

Direction is mechanical from the sign: `>` `INCREASING`, `<` `DECREASING`, `=`
`UNCHANGED`. Never `POSITIVE` or `NEGATIVE`.

## 9. `terms` is required, and empty means refusal

One bucket holds hundreds of thousands of terms; the two real acquisitions
scanned 223,342 and 370,468 rows. An unattended sweep is not a derivation
anybody asked for.

- `terms` is **required**; a missing or non-list value is `PARAMETERS_INCOMPLETE`
- an **empty** selection is a refusal, not a request for everything
- an operational ceiling of **25 terms** per derivation — ours, and stated as
  ours
- terms are canonically sorted in one place, so any request order is the same
  derivation with the same fingerprint

A group whose term nobody selected is **not** a refusal. It is a derivation
nobody asked for, and it produces neither a signal nor a refusal row.

## 10. Required facts

```text
EXACT_NUMERIC_VALUE · LEXICAL_TERM · SOURCE_PERIOD_LABEL ·
SOURCE_LANGUAGE_LABEL · SOURCE_RELATIVE_ORDER
```

Deliberately **not** `COMPARABLE_INSTANT` (H-29 open), **not**
`CANONICAL_LANGUAGE` (H-30 open), **not** `CLASSIFIED_GEOGRAPHY` (a language is
not a place).

Every real GDELT record is `PARTIAL`, carrying `PERIOD_TIMEZONE_NOT_ESTABLISHED`
and `LANGUAGE_NOT_MAPPED`. Neither is a fact this derivation needs — ordering is
separately certified and exact source-language equality is sufficient — so both
contribute with `withheld_facts` empty. **No quality string is branched on
anywhere in the extractor.**

## 11. Refusals

| Reason | When |
|---|---|
| `REQUIRED_FACT_WITHHELD` | no certification covers the stream, or its label scheme differs, or a record withholds a required fact |
| `NON_CONTIGUOUS_SOURCE_BUCKETS` | the pair is the same series and not one published step apart |
| `INCOMPATIBLE_SERIES` | different term, language label, language scheme, gram size or resource |
| `INCOMPATIBLE_INPUT_KINDS` | not a lexical frequency observation |
| `AMBIGUOUS_OBSERVATION_LINEAGE` | two rows for one bucket in one series |
| `INSUFFICIENT_INPUT_OBSERVATIONS` | fewer than two observations of the term |
| `INPUT_RECORD_INVALID` | an unparseable label, or a value contradicting its own quality state |
| `PARAMETERS_INCOMPLETE` | `terms` missing, empty, oversized, or an unknown parameter |

All go to `nlp.signal_derivation_runs`. **None produces a signal row.**

## 12. The real derivation

One bounded controlled acquisition (§34–§35 of the brief), then one derivation:

```text
acquisition    files 2 · rows scanned 370,468 · rows matched 4 · raw new 4
normalization  input 4 · created 4 · all PARTIAL
derivation     groups 2 · derived 2 · refused 2 · signals new 2
repeat         acquisition 0 new / 4 unchanged · normalization 0 input ·
               derivation 0 new / 2 unchanged
```

| Term | Buckets | Counts | Magnitude | Direction |
|---|---|---|---|---|
| `climate` | `20260830184500` → `20260830190000` | 48 → 59 | `11` | `INCREASING` |
| `weather` | `20260830184500` → `20260830190000` | 33 → 42 | `9` | `INCREASING` |

**And two refusals in the same run**, which is the part worth reading. The
morning bucket `20260830091500` from Mission 1.9.3 is nine hours earlier, so
each term's group held three observations and the extractor derived the adjacent
pair and refused the gap:

```json
{"reason": "NON_CONTIGUOUS_SOURCE_BUCKETS",
 "detail": "20260830091500 and 20260830184500 are the same series and are not
            one published bucket apart …",
 "observation_keys": ["gdelt|web-ngrams/1gram|20260830091500|ENGLISH|climate",
                      "gdelt|web-ngrams/1gram|20260830184500|ENGLISH|climate"]}
```

The gap policy proven on real data, not only in fixtures.

## 13. What it does not do

Interpolate, bridge, zero-fill, smooth, average, roll, accumulate, rank,
classify, embed, cluster, score, contact a network, map a language, assign a
timezone, or turn a term into a topic. It subtracts two exact decimals from two
adjacent buckets of one series and stops.
