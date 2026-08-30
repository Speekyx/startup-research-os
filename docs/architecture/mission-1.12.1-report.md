# Mission 1.12.1 — GDELT Sequential Lexical Frequency Change V1

**Sprint:** 1
**Date:** 2026-08-30
**Status:** Complete. **`lexical-frequency-change@1.0.0` implemented**, with
**two real signals** and **two real gap refusals** from one bounded controlled
acquisition. No Claims, no Evidence, no Opportunities, no embeddings, no scores.
**Specifications:** [`lexical-frequency-change-extractor-v1.md`](../data/lexical-frequency-change-extractor-v1.md),
[ADR-023](adr/ADR-023-source-bucket-adjacency.md).

---

## 1. What was delivered

| | |
|---|---|
| Extractor | `lexical-frequency-change@1.0.0` — the third, and the first using `ORDERED_PERIODS` |
| Signal type | `lexical_frequency_change` (migration 0014) |
| Contract | `1.7.0` → **`1.8.0`**: `NON_CONTIGUOUS_SOURCE_BUCKETS` |
| Migrations | `0014` (type + refusal vocabulary), `0015` (a group may derive **and** refuse) |
| Guard | `validate_signals.py` gains a timezone check, probed against 2 violations |
| Tests | **49 new**, synthetic only |
| Controlled acquisition | 2 files · 370,468 rows scanned · 4 matched · 4 raw · 4 normalized |
| **Real signals** | **2 emitted, 2 gaps refused** |

```text
climate   20260830184500 → 20260830190000   48 → 59   +11   INCREASING
weather   20260830184500 → 20260830190000   33 → 42    +9   INCREASING
```

---

## 2. §48 — the questions, answered

### Is `lexical_frequency_change` implemented? What extractor/version?

Yes. **`lexical-frequency-change@1.0.0`**, reading
`lexical_frequency_observation`, family `LEXICAL_FREQUENCY`.

### Is it deterministic? Does it make network/model calls?

`derivation_kind = DETERMINISTIC`, with no model version and no prompt version —
refused by a database CHECK if it tried. It imports no network client, no model
and no embedder, asserted by `validate_signals.py` walking every import.

### What exactly does the Signal assert?

> For one lexical term, one source language label and one gram size, the GDELT
> source-measured frequency at a bucket differs by exactly this much from the
> frequency at the immediately preceding bucket of the same stream.

### What does it explicitly NOT assert?

That demand, attention, popularity, interest, momentum, trend strength or
opportunity strength changed — and not even that the underlying phenomenon
changed. A term frequency moves when coverage moves, and coverage moves for a
news event, a crisis, a celebrity, weather, politics, a disaster or a sports
fixture.

The words `demand`, `attention`, `popularity`, `interest`, `momentum`, `trend`,
`growth`, `velocity`, `topic` and `sentiment` appear nowhere in the serialised
output, asserted over the payload rather than field by field.

### What temporal basis is used? Is H-32 respected?

`ORDERED_PERIODS`, and yes — **by asking, not by assuming.** Before comparing
anything the extractor calls `order_certification(source_id, resource_id)` and
checks two things:

- a certification **covers this stream** — this source and this resource.
  `web-ngrams/chargram` sits in the same directory with the same label shape and
  is refused, as is any other source;
- the certification's **label scheme** is `gdelt-web-ngram-bucket`, the one whose
  15-minute step is correct. A certification for the same source under another
  scheme is refused rather than used.

Either failure is `REQUIRED_FACT_WITHHELD` naming `SOURCE_RELATIVE_ORDER`.

### Is H-29 still open? Is UTC assigned anywhere? Can `observed_at` be populated?

**Open. No. No.**

The window carries **no bounds** — only `COMPARABLE_INSTANTS` may — and
`observed_at` is `NULL`, which a database CHECK enforces independently of the
model. A new AST gate fails the build if any extractor calls `astimezone`,
`now`, `utcnow`, `utcfromtimestamp`, `today`, `localtime` or `fromtimestamp`, or
passes `tzinfo=`. It was probed against two deliberate violations.

### How are input series grouped?

```text
source · record kind · series dataset + resource · period type ·
language scheme + label · gram size · TERM
```

The mirror image of the contrast extractor, and the difference is exactly one
field: the contrast groups by the **bucket** and varies the term; this groups by
the **term** and varies the bucket. There is no topic, category or theme in the
key because none exists.

### What is the pairing strategy? What counts as adjacent? Are gaps bridged?

`adjacent_source_buckets`, an explicit parameter because it changes which signals
exist. Over 09:15, 09:30, 09:45 it emits 09:15→09:30 and 09:30→09:45, never
09:15→09:45.

**Adjacent means exactly one published bucket step** — 15 minutes, GDELT's
documented cadence. Anything else is `NON_CONTIGUOUS_SOURCE_BUCKETS`.

**Gaps are never bridged.** No existing refusal reason could say it:
`INCOMPATIBLE_SERIES` says the observations are of different things and they are
not; `INSUFFICIENT_INPUT_OBSERVATIONS` says there are too few and there are
exactly two. What was missing was *these two belong together and the interval
between them is not the one the source publishes*.

**The step is computed in label space from end to end** — the earlier label's own
components advanced by 15 minutes, formatted back into a label, compared as a
string. Nothing becomes an instant. That arithmetic is licensed by the Mission
1.12 certification rather than by the format: adding 15 minutes to a wall-clock
reading is only sound in a monotonic frame.

### Does an absent term become zero? Can sparse series produce Signals?

**No**, and **yes, fewer of them.**

A term with no observation in a bucket did not occur zero times there. GDELT
publishing `0` is the source saying "none in this window" and is subtracted
normally; a term simply not appearing says nothing at all. A change requires two
**actual** source observations, and there is no synthesis anywhere.

A sparse series yields only its contiguous pairs. Zero-filling is the most
natural thing to do to this data and it is wrong in a way nothing downstream can
detect — a signal saying `climate` fell by 55 would be indistinguishable from a
real collapse in coverage, and the record that would disprove it is the one
never read.

### How are LANG values matched? Is H-30 respected?

By **exact source label and scheme**: `cld2-language-name` / `ENGLISH` equals
`cld2-language-name` / `ENGLISH`, and that asserts nothing about what either maps
to. `ENGLISH` and `FRENCH` are `INCOMPATIBLE_SERIES`.
`canonical_language_tags` is absent from the scope and the model refuses one.
**H-30 open.**

### Can 1gram and 2gram mix?

**No.** `gram_size` is in the grouping key and a cross-gram pair is
`INCOMPATIBLE_SERIES`. It is read from the canonical payload, never from spaces.

### What arithmetic is emitted? Is percentage growth calculated? How is direction derived? What magnitude kind?

`absolute_change = later − earlier`, arbitrary-precision `Decimal` on both sides.
`9007199254740995 − 9007199254740993 = 2` exactly.

**No percentage and no ratio in V1.** Both need a denominator rule — a term going
from 0 to 5 has no percentage — and a rounding rule, and a repeating decimal
rounded to an unstated precision is fake precision.

Direction is mechanical from the sign: `>` `INCREASING`, `<` `DECREASING`, `=`
`UNCHANGED`. Never `POSITIVE`/`NEGATIVE`.

**`ABSOLUTE_CHANGE`, not `ABSOLUTE_DIFFERENCE`.** The same-bucket contrast
measures two terms at one moment and uses the difference kind because nothing
changed; this measures one term across two ordered buckets, so something did, and
a consumer branching on the kind must be able to tell a movement from a contrast.

### What required facts are declared? Can PARTIAL GDELT records participate?

```text
EXACT_NUMERIC_VALUE · LEXICAL_TERM · SOURCE_PERIOD_LABEL ·
SOURCE_LANGUAGE_LABEL · SOURCE_RELATIVE_ORDER
```

Not `COMPARABLE_INSTANT`, not `CANONICAL_LANGUAGE`, not `CLASSIFIED_GEOGRAPHY`.

**Yes.** All six real GDELT records are `PARTIAL` with
`PERIOD_TIMEZONE_NOT_ESTABLISHED` and `LANGUAGE_NOT_MAPPED`, neither is a fact
this derivation needs, and every contributing input recorded `withheld_facts`
empty. **No quality string is branched on anywhere in the extractor.**

### How are refusals recorded?

As `GroupRefusal` entries in the run's `refusals` array in
`nlp.signal_derivation_runs`, with the reason, the detail, the grouping key and
the observation keys. **No refusal produces a signal row.**

### Is Signal identity deterministic? Is extraction idempotent?

Yes, and yes. Identity is the Mission 1.11 material — schema, workspace, type,
family, extractor and version, ordered contributing inputs, parameter
fingerprint, window — excluding magnitude, direction, confidence, `derived_at`
and `correlation_id`.

All three stages were re-run:

```text
acquisition     0 new · 4 unchanged
normalization   0 records input
derivation      0 new · 2 unchanged
```

### Did current real data permit a real sequential GDELT Signal?

**Not before this mission.** The two existing observations were from **one**
bucket, so a sequential derivation over them was impossible — §33 anticipated
exactly that and forbade weakening the extractor to manufacture one.

The optional §34 controlled acquisition was performed instead, and it stayed
inside every stated bound.

### If controlled acquisition was performed, how many new Raw/Normalized/Signals were created?

```text
files requested          2      (reviewed ceiling: 8)
files processed          2
rows scanned       370,468
rows matched             4
RawRecords          4 new,  0 unchanged
NormalizedRecords   4 new,  0 revised, all PARTIAL
Signals             2 new
```

One gram kind (`1gram`), one language (`ENGLISH`), two named terms, two
consecutive reviewed bucket labels. No sweep, no crawl, no new source, no new
resource, no attempt to bypass a missing bucket.

**The bucket labels came from GDELT's own `LASTUPDATE` pointer, stepped back in
label space** — not computed from this machine's clock, which would have assumed
the frame H-29 leaves unestablished.

**Deployment state changed:** `sros-source enable gdelt` was run, as Mission
1.9.3 did before its own controlled acquisition. GDELT's collector is left
enabled and that is recorded here rather than silently reverted.

### Did the original 5 Signals remain unchanged?

**Yes.** All five identities were **recomputed from their stored lineage** and
reproduce byte-for-byte, and the original 8 raw and 8 normalized records carry
the unchanged Mission 1.11 digest:

```text
5/5 original signal identities reproduce
original raw 8 · normalized 8 · digest d8cf83214a930be6…  UNCHANGED
```

No historical signal was rewritten into the new type. The one
`lexical_frequency_contrast` signal is still `SAME_PERIOD_LABEL` /
`NOT_APPLICABLE` / magnitude `19`.

### Were any Claims/Evidence created? Embeddings? Scoring?

**None**, **none**, **none**. All zero, and `validate_signals.py` fails the build
if the package names `scoring.evidence`, `research.claims`,
`research.opportunities` or `nlp.embedding_provenance`.

### Is the project ready to move to Signal → Evidence / Claim generation?

**Yes.** See §5.

---

## 3. The gap policy proven on real data

The most useful thing about the real derivation is what it **refused**.

Each term's group held three observations: the Mission 1.9.3 bucket
`20260830091500` and the two new consecutive ones. So each group derived the
adjacent pair and refused the nine-hour gap:

```json
{"reason": "NON_CONTIGUOUS_SOURCE_BUCKETS",
 "detail": "20260830091500 and 20260830184500 are the same series and are not
            one published bucket apart. Bridging them would invent continuity
            across a bucket nobody read, and a term absent from the buckets
            between is ABSENT rather than zero",
 "observation_keys": ["gdelt|web-ngrams/1gram|20260830091500|ENGLISH|climate",
                      "gdelt|web-ngrams/1gram|20260830184500|ENGLISH|climate"]}
```

A bridging extractor would have emitted `55 → 48` for `climate` across nine
hours and 35 unread buckets, and it would have looked entirely reasonable.

---

## 4. The second time a CHECK caught the model rather than the code

The real derivation failed on its first attempt, on a constraint migration 0013
added as belt-and-braces:

```sql
CHECK (groups_derived + groups_refused <= groups_considered)
```

It reads as arithmetic and is really a **claim about the domain**: that a
candidate group either derives or refuses. True of both Mission 1.11.1
extractors, because each group produced one outcome — and false for any extractor
that pairs *within* a group. One term, three buckets, one signal, one refusal:
`1 + 1 > 1`.

**This time the code was right and the constraint was wrong.** `testing-strategy.md`
§25 recorded the opposite case, where the counters double-counted; the reflex to
fix the code would here have made the counters lie to preserve an assumption
nobody had noticed making.

Migration 0015 replaces it forward with the invariant that was always true —
each counter bounded by the groups considered, separately — and 0013 is not
edited. Recorded as `testing-strategy.md` §27.

A third defect surfaced alongside it: `validate_schema.py`'s `strip_constraint`
matched a constraint name inside a `DROP CONSTRAINT` statement. With one drop it
did not matter; a second migration dropping the same constraint left a
**superseded** value set in the parsed body, which then failed against the
contract as drift that did not exist.

---

## 5. Scope discipline, and what Mission 1.13 should be

| Forbidden by the brief | State |
|---|---|
| Moving averages, rolling windows, momentum | Not implemented |
| Semantic topic selection | Not implemented; a term is a term |
| `trend`, `growth`, `attention`, `demand`, `popularity`, `velocity`, `acceleration` types | None registered; `validate_signals.py` fails the build on such an extractor id |
| Claims, Evidence, Opportunities, embeddings, scores | All 0 |
| Cross-source comparison | Impossible: no `COMPARABLE_INSTANT` for GDELT |

### The pipeline is complete through Signals

```text
acquisition → normalization → signal derivation
   12 raw       12 normalized      7 signals
```

Three extractors, three signal types, two sources, two quantity families, and
every temporal question either answered or explicitly open.

**The next boundary is Signal → Evidence, and it is the one this whole layer has
been refusing to cross.** Evidence is claim-scoped, so it means deciding how a
Claim comes into existence — which is where interpretation has to start being
done deliberately, with its own confidence and its own provenance. Everything
built since Mission 1.11 exists to make that step honest: a Claim will cite
Signals whose arithmetic is exact, whose lineage reaches the raw records, and
whose refusals are on the record.

Two smaller things are worth doing first or alongside:

1. **Ask GDELT about H-29.** It is now the only temporal blocker. One first-party
   sentence unblocks cross-source alignment, `observed_at` and every "as of"
   claim.
2. **More real data, not more extractor types.** Seven signals over two sources
   is thin ground for designing Evidence. The extractors are source-agnostic, so
   more data needs no new code.

---

## 6. Validation

```text
zero-dependency suites   417 tests across 6 packages
pytest suites            1,376 tests + 233 subtests across 7 packages (49 new)
schema validation        9 invariant groups, 36 tables
signal boundary guard    6 boundary groups, probed against 2 new violations
normalization guard      9 boundary groups
evidence aggregation     8 checks; production scoring still blocked
source registry          27 sources, 33 evidence records
contracts --check        3 generated artifacts current
TypeScript conformance   21/21
mypy strict              130 source files
ruff + ruff format       clean
```

Post-suite: 22 tenant and 14 global tables unchanged by the run.

**Data, before → after:**

```text
raw          8 → 12    (4 added by the controlled acquisition)
normalized   8 → 12    (4 added; all PARTIAL)
signals      5 →  7    (2 added; the original 5 byte-identical)
inputs      10 → 14
runs         4 →  6
embeddings, claims, evidence, opportunities: 0 → 0
```

---

## 7. Risks left open

- **A gappy stream produces few signals, by design.** A future rolling-window
  extractor will face the same question and ADR-023 deliberately does not
  pre-answer it: adjacency is settled for pairwise change and nothing wider.
- **Sparse terms are under-represented.** A rare term appears in fewer
  consecutive buckets and therefore yields fewer pairs. That is a real sampling
  property of the output, recorded rather than corrected.
- **GDELT's collector is left enabled.** A deliberate, recorded deployment act;
  no scheduler runs, and disabling it would make the acquisition harder to
  reproduce.
- **`terms` being required makes the extractor unsweepable**, deliberately.
  Nothing derives GDELT change signals unattended and nothing should until
  somebody reviews a selection rule.
- **The 25-term ceiling is ours and is arbitrary within an order of magnitude.**
  It is labelled as ours and no external limit is implied.
- D-03, D-08, D-10, D-12, H-12, H-13, H-22 to H-27, H-29, H-30,
  PROFILE-NOT-CALIBRATED unchanged.
