# Numeric Period Change Extractor V1

**Status:** **Implemented.** `numeric-period-change@1.0.0`, the first signal
extractor. **Four real signals** derived from the six real World Bank
observations.
**Date:** 2026-08-30 (Mission 1.11.1)
**Code:** `sros_nlp.extractors.numeric_period_change`
**Related:** [`signal-contract-v1.md`](signal-contract-v1.md),
[`signal-derivation-runtime-v1.md`](signal-derivation-runtime-v1.md),
[`world-bank-normalizer-v1.md`](world-bank-normalizer-v1.md),
[ADR-020](../architecture/adr/ADR-020-signal-derivation-model.md).

---

## 0. What it produces

```text
world-bank|indicator/SP.POP.TOTL|DEU|2018   value 82905782
world-bank|indicator/SP.POP.TOTL|DEU|2019   value 83092962
    ↓
signal_type       numeric_period_change
quantity_family   MEASURED_SERIES
magnitude         187180   ABSOLUTE_CHANGE   unit_state NOT_ESTABLISHED
direction         INCREASING
temporal_basis    COMPARABLE_INSTANTS
window            2018 → 2019, YEAR, 2 observations, 2018-01-01 .. 2020-01-01
scope             world-bank · SP.POP.TOTL · DE
parameters        {"pairing_strategy": "adjacent_periods"}
confidence        1.0
```

**What it asserts, in full:** the source-measured numeric value of this series
changed by exactly this much between these two periods.

**What it does not assert:** market growth, demand, attractiveness, economic
health, or that the change is good. A population of 82,905,782 becoming
83,092,962 is a population going up by 187,180. Whether that is an opportunity
is a Claim, and a Claim has its own evidence.

## 1. Identity and versioning

| | |
|---|---|
| extractor | `numeric-period-change@1.0.0` |
| signal type | `numeric_period_change` (registry entry, migration 0012) |
| quantity family | `MEASURED_SERIES` |
| reads | `numeric_observation` |
| derivation kind | `DETERMINISTIC` — no model version, no prompt version, refused by a CHECK |
| schema | `sros.signal/1` |

**What requires a version bump:** a new pairing strategy becoming the default;
any change to the arithmetic, to the required facts, to the grouping key or to
what enters the scope. **Not** a reworded refusal message, a refactor or a new
test.

A `1.1.0` writes rows **beside** the `1.0.0` ones; neither supersedes the other,
and which a consumer should read is **D-08**, still open.

## 2. What makes two observations one measured series

Grouping is by a canonical key over eleven canonical fields:

```text
source · record kind · metric scheme + id · geography kind + canonical scheme +
canonical code + source code · series dataset + resource + frequency ·
unit state + unit · period type
```

Every one of them is load-bearing. Dropping the geography would let France's
population meet Germany's, which §7 forbids by name. Dropping the **unit** would
let a figure in thousands be subtracted from one in units, and the result would
look entirely reasonable.

Records with different keys land in different groups and **never meet**. A
caller handing an explicit incompatible pair is refused with
`INCOMPATIBLE_SERIES`, and the detail names what disagreed.

## 3. Pairing — adjacent, and it is a parameter

```text
2018 · 2019 · 2020   ->   2018→2019 and 2019→2020
```

Not `2018→2020`. That is a different question with a different answer, and a
strategy emitting it would have to say so.

`pairing_strategy` is a **parameter**, not a constant, because it changes which
signals exist. It is canonically serialised, fingerprinted and persisted, and it
enters the derivation identity — so the same records under a different strategy
are different signals rather than one overwriting the other. `adjacent_periods`
is the only value V1 implements; anything else is `PARAMETERS_INCOMPLETE`, and
so is a parameter the extractor does not read.

## 4. Ordering — from the period, never from the database

Inputs are ordered by **canonical period start, ascending**. Position 0 is the
earlier observation.

Input order is part of the derivation identity, so an order that came from the
database would make the identity depend on a plan the query optimiser chose.
Reversing the rows a query returns produces the same signal, the same
fingerprint and the same magnitude, and a test asserts it.

Two rows carrying the same period label in one series are refused as
`AMBIGUOUS_OBSERVATION_LINEAGE`: one observation under two lineages, and
choosing between them is D-08.

## 5. Arithmetic — one number, exact

```text
absolute_change = current − previous
```

An arbitrary-precision `Decimal` on both sides. `9007199254740995 −
9007199254740993 = 2` exactly, where a float round-trip would not.

**No percentage and no ratio.** Both need a denominator rule (what does a change
from zero mean) and a rounding rule, and a repeating decimal rounded to an
unstated precision is fake precision. A difference is exact, always defined, and
sufficient to state the relation. §10's instruction — *the simplest sufficient
Signal is preferred* — points here.

**The unit is inherited or absent.** `PUBLISHED` on the inputs gives
`INHERITED` with the unit verbatim; anything else gives `NOT_ESTABLISHED` and no
unit. World Bank publishes no unit on this endpoint, so every real signal is
`NOT_ESTABLISHED` — the normalizer's own answer, carried up rather than resolved.

## 6. Direction — mechanical, and not sentiment

```text
current > previous  ->  INCREASING
current < previous  ->  DECREASING
current = previous  ->  UNCHANGED
```

Never `POSITIVE` or `NEGATIVE`, which are not in the enum: direction is change,
and a falling unemployment figure is `DECREASING` whatever anyone thinks of it.

## 7. Required facts, and why quality is never branched on

```text
EXACT_NUMERIC_VALUE · COMPARABLE_INSTANT · CLASSIFIED_GEOGRAPHY
```

Declared once, and evaluated by the **model** against each record's own quality
reasons. There is no `if quality != VALID` anywhere in the extractor — Mission
1.11 rejected that model explicitly, and a `PARTIAL` record missing a fact this
derivation never asks for contributes normally.

`CLASSIFIED_GEOGRAPHY` is required and that is a decision worth stating. A
change in a series whose geography was never classified is still arithmetically
true, and its **scope could not say where the measurement is from** — "population
changed by 139,000, somewhere" is not an assertion anything downstream can use.
An `AGGREGATE` geography is classified and passes; only a genuinely unclassified
code is refused.

## 8. Scope

```text
source_ids       ["world-bank"]
metric_ids       ["SP.POP.TOTL"]
geography_codes  ["DE"]        <- canonical only
```

A geography with no canonical code contributes **no key at all** rather than its
source code: a field named `geography_codes` means canonical codes, and putting
a source code in it is the promotion the geography map exists to prevent. The
source code survives in the lineage's observation keys either way.

## 9. The four real signals

Derived from the six stored World Bank observations, in one pass, acquiring
nothing:

| Series | Periods | Magnitude | Direction |
|---|---|---|---|
| `SP.POP.TOTL` · DE | 2018 → 2019 | `187180` | `INCREASING` |
| `SP.POP.TOTL` · DE | 2019 → 2020 | `67909` | `INCREASING` |
| `SP.POP.TOTL` · FR | 2018 → 2019 | `223713` | `INCREASING` |
| `SP.POP.TOTL` · FR | 2019 → 2020 | `219049` | `INCREASING` |

```text
records considered 6 · groups 2 · derived 2 · refused 0 · signals new 4
repeat pass        signals new 0 · unchanged 4
```

**Two groups, not one.** Germany and France are two series, and the count
follows from the grouping key rather than from anything anybody decided in
advance.

## 10. What it does not do

Interpret, classify, embed, cluster, score, contact a network, read a raw
record, or produce a claim, an evidence row or an opportunity. It subtracts two
exact decimals from one series and stops.
