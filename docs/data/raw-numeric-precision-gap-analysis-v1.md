# Raw Numeric Precision Gap Analysis V1

**Status:** Analysis record. Produced by Mission 1.6.1 §3 **before** the
collector was changed, so the fix can be checked against what was measured
rather than against what was assumed.
**Date:** 2026-08-30
**Reads:** the World Bank acquisition path as `world-bank-indicators@1.0.0`
implements it, end to end.
**Related:** [`world-bank-collector-v1.md`](world-bank-collector-v1.md),
[`raw-record-gap-analysis-v1.md`](raw-record-gap-analysis-v1.md),
[`normalized-record-v1.md`](normalized-record-v1.md) §6,
`docs/architecture/mission-1.6-report.md` §8.

---

## 0. Why this document exists, and how it was produced

Mission 1.6 §8 recorded that the collector parses values with `float(...)` and
called it "the open correctness item, belonging to a collector version bump". It
did not measure the exposure.

**Everything below was measured by driving the real `WorldBankCollector` against
a fake transport**, not by reading the code and reasoning. That distinction
earned its keep immediately: the intuition going in was "float destroys
decimals", and that is *wrong* for most values. What float actually destroys is
narrower, stranger, and in one case worse than losing a decimal place.

---

## 1. The path, and where a number changes representation

```text
HTTP bytes
  └─ transport.py         response.text          str, untouched
      └─ world_bank._parse  json.loads(text)     ← int | float          (1)
          └─ _observation    float(raw_value)    ← float, always        (2)
              └─ CollectedObservation.value: float | None               (3)
                  └─ .payload {"value": <float>}
                      └─ canonical_json → json.dumps  ← repr(float)     (4)
                          ├─ content_hash = sha256(that text)
                          └─ repositories → json.dumps → JSONB          (5)
                              └─ normalization reads payload::text
                                 with parse_float=Decimal    exact, but
                                 exact w.r.t. an ALREADY lossy value
```

Five points. **(1)** and **(2)** are where source information is lost; **(4)**
and **(5)** are where the *serialization* can vary; the normalizer is faithful
and inherits whatever arrived.

---

## 2. What is actually lost

Measured, one source literal at a time, through the real collector.

### LOSS 1 — type. `1` and `1.0` become the same record

| source sent | `json.loads` gives | after `float()` | stored |
|---|---|---|---|
| `1` | `1` (int) | `1.0` | `1.0` |
| `1.0` | `1.0` (float) | `1.0` | `1.0` |
| `0` | `0` (int) | `0.0` | `0.0` |
| `67158348` | `67158348` (int) | `67158348.0` | `67158348.0` |

§4 of the mission brief asks the raw layer to distinguish `1`, `1.0`, `1.25`,
`0` and `null`. It currently distinguishes four of the five: **`1` and `1.0` are
indistinguishable once stored.** `json.loads` gets the distinction right and
`float()` throws it away one line later.

This is also the origin of the `.0` artifact Mission 1.6 found at the normalized
layer and stripped there. Stripping it downstream treats the symptom; the
information was destroyed upstream.

### LOSS 2 — magnitude. Integers above 2^53

| source sent | stored | |
|---|---|---|
| `9007199254740992` | `9007199254740992.0` | ok, this is 2^53 |
| `9007199254740993` | `9007199254740992.0` | **corrupted** — off by one |
| `9007199254740995` | `9007199254740996.0` | **corrupted** — rounded up |
| `123456789012345678` | `1.2345678901234568e+17` | **corrupted**, and in scientific notation |

A double holds 53 bits of mantissa. Past 2^53 consecutive integers are no longer
all representable, so the value silently moves to the nearest one that is.

### LOSS 3 — significant digits beyond 17

| source sent | stored | |
|---|---|---|
| `0.1` | `0.1` | ok |
| `1.2345678901234567` | `1.2345678901234567` | ok — 17 significant digits |
| `1.23456789012345678` | `1.2345678901234567` | **corrupted** — 18th digit dropped |
| `82.45609756097561234` | `82.4560975609756` | **corrupted** |
| `2715518274119.719999999` | `2715518274119.72` | **corrupted** |

### Why most decimals survive, and why that is not reassuring

`0.1`, `2.675`, `82.4560975609756` and `2715518274119.71` all round-trip
intact — which contradicts the obvious expectation and is worth understanding,
because it is the reason this defect has stayed invisible.

Python's `repr` of a float has produced **the shortest decimal string that parses
back to the same double** since 3.1. So `float("0.1")` is not 0.1 — it is
0.1000000000000000055511151231257827 — but `json.dumps` writes `0.1`, because
that is the shortest literal that recovers the same double.

The serialization round-trips. **The value never did.** Every arithmetic
consumer of that number gets the double, not the decimal, and the two are not
equal. What shortest-repr guarantees is that the *text* survives, and only up to
17 significant digits.

### LOSS 4 — identity. Distinct observations collapsing into one record

The one that is a correctness bug rather than a fidelity complaint.

| source value A | source value B | stored payload |
|---|---|---|
| `9007199254740993` | `9007199254740992` | **the same** |
| `1` | `1.0` | **the same** |
| `0.30000000000000004` | `0.300000000000000044408920985006…` | **the same** |

`content_hash` is `sha256` over the canonical payload, and the payload holds the
collapsed value. So two genuinely different upstream figures produce **the same
hash**, and `_persist_one` finds the existing row, moves `last_seen_at`, and
returns `UNCHANGED`.

**A real upstream revision would be recorded as "we checked and it had not
changed."** That is the exact failure Mission 1.5 §24 built the revision
machinery to prevent, defeated one layer below it. Nothing raises, nothing logs,
and the history simply does not contain the change.

### LOSS 5 — serialization. The stored text is not the hashed text

`json.dumps` emits scientific notation for large floats. PostgreSQL `JSONB` does
not: it stores numbers as `numeric` and renders them plainly.

```text
python json.dumps  1.2345678901234568e+17
stored in JSONB    123456789012345680
```

The `content_hash` is computed in Python over the first string. Anything that
recomputes it from the stored payload — an integrity check, a re-hash after a
restore — reads the second and gets a different digest. The mission brief asks
for "no accidental scientific-notation variation where semantics are identical"
(§6); this is that variation, already present.

---

## 3. Current exposure of the authorized data

Three indicators are authorized:

| Indicator | Shape | Exposed today? |
|---|---|---|
| `SP.POP.TOTL` | integer population counts, ~1e6 to ~1e9 | **no** — well below 2^53 |
| `NY.GDP.MKTP.CD` | current US$, up to ~1e13 | **no** — below 2^53, though within a factor of ~1000 of it |
| `IT.NET.USER.ZS` | percentage, one or two decimals | **no** — few significant digits |

**The six real records are not corrupted.** Their values are integral, below
2^53, and round-trip exactly; the only visible effect is the `.0` that Mission
1.6 strips at normalization.

So this is not an incident. It is a mechanism that is wrong while the data
happens to be inside its safe range — and LOSS 4 means the failure mode, when it
arrives, is silent and destroys history rather than raising.

Two ways it arrives without anyone changing the collector: an indicator with
more than 17 significant digits (many World Bank series are unrounded ratios),
or a value above 2^53 (a GDP series in a low-value currency unit, or any count
of that magnitude).

---

## 4. What must change

| Change | Closes |
|---|---|
| `json.loads(..., parse_float=Decimal, parse_int=int)` in `_parse` | LOSS 3, and the input half of LOSS 2 |
| `CollectedObservation.value: Decimal \| int \| None` | LOSS 1, LOSS 2 |
| a canonical numeric serialization used for the payload and the hash | LOSS 4, LOSS 5 |
| a collector **version bump** | §5 — the above changes every `content_hash` |

### The serialization has to be defined, not inherited

`json.dumps` cannot serialize a `Decimal` at all, so a canonical form is required
rather than optional. It must be:

- **plain** — never scientific notation, so Python and `JSONB` agree (LOSS 5);
- **exact** — the digits the source sent, neither padded nor rounded;
- **type-preserving** — `1` and `1.0` serialize differently, or LOSS 1 stays;
- **deterministic** — same input, same bytes, on every platform and run.

A decimal **string** satisfies all four, and is what the normalized layer already
uses (`normalized-record-v1.md` §6.1) for the same reasons. Storing the value as
a JSON *number* cannot satisfy the third: JSON has one numeric type and `1` and
`1.0` are the same number in it.

### What deliberately does not change

- **`decimals`** stays an `int`. It is a count of digits, not a measurement.
- **The normalizer** already reads `payload::text` with `parse_float=Decimal` and
  is exact with respect to what it is given. It needs to learn the new payload
  shape, not a new philosophy.
- **Retention, attribution, provenance, the observation key** — untouched. This
  is a numeric-representation change and must not become a redesign.
- **Existing records.** §8: no in-place rewrite, and nothing may claim a `1.0.0`
  record was produced by the new version.

---

## 5. Why this is a version bump and not a fix

Changing the representation changes the canonical payload, which changes
`content_hash`, which changes the record id.

A collector that silently produced different hashes for identical source data
would make every existing record look like it had been revised the next time it
was collected — and `world-bank-collector-v1.md` §7 states that the retrieval
timestamp is kept out of the fingerprint precisely so that re-retrieval is not
mistaken for revision. Quietly changing the *value* representation breaks the
same guarantee from the other direction.

So `1.0.0` records stay as `1.0.0` records, readable and attributable, and the
new behaviour ships as a new version. That is what `collector_version` on every
row is for, and Mission 1.5 §50 wrote it there for this case.
