# Mission 1.11.1 — First Deterministic Signal Extractors

**Sprint:** 1
**Date:** 2026-08-30
**Status:** Complete. **Five real Signals** — four `numeric_period_change`, one
`lexical_frequency_contrast`. No Claims, no Evidence, no Opportunities, no
embeddings, no scores.
**Specifications:** [`signal-derivation-runtime-v1.md`](../data/signal-derivation-runtime-v1.md),
[`numeric-period-change-extractor-v1.md`](../data/numeric-period-change-extractor-v1.md),
[`lexical-frequency-contrast-extractor-v1.md`](../data/lexical-frequency-contrast-extractor-v1.md),
[ADR-021](adr/ADR-021-signal-derivation-run-log.md).

---

## 1. What was delivered

| | |
|---|---|
| Extractors | `numeric-period-change@1.0.0`, `lexical-frequency-contrast@1.0.0` |
| Package | `services/nlp/python/sros_nlp` — 8 modules, no model, no network |
| Migration | `0013_signal_derivation_runs.sql` — the run log, plus two contract values |
| Contracts | `1.6.0` → **`1.7.0`**: `ABSOLUTE_DIFFERENCE`, `INCOMPATIBLE_SERIES` |
| Celery | `signal.derive`, routed to the **acquisition** queue |
| Orchestrator | `SIGNAL_DERIVATION` capability with a derived block; planner `1.3.0` |
| Guard | `validate_signals.py` — 5 boundary groups, probed against 3 deliberate violations |
| Tests | 51 synthetic + 21 integration, all new |
| **Real Signals** | **5** |

```text
numeric-period-change@1.0.0   records 6 · groups 2 · derived 2 · refused 0 · new 4
lexical-frequency-contrast    records 2 · groups 1 · derived 1 · refused 0 · new 1
repeat pass, both             new 0 · unchanged 5 · conflicted 0
```

---

## 2. §4 — where a refused derivation goes

Resolved **before** implementing, as required. Four candidates, and only one
survives the operational question *"N considered, M emitted, K refused, why"*:

| Candidate | Verdict |
|---|---|
| Celery return value | Redis-backed, expires, not tenant-scoped, not queryable |
| Structured logs | "Grep the logs" is not an operational answer |
| `research.research_jobs` | **Closest, and rejected.** No result column, and it is written in a *different transaction* from the signals — so "6 emitted, 2 refused" could disagree with what was stored |
| `nlp.signals` | Forbidden. A row there says a signal exists |

**Decision: `nlp.signal_derivation_runs`** — one row per extractor **execution**,
written inside the same transaction as its signals. Ten counters, a JSONB
refusal list, a truncation reason, 90-day operational retention, RLS.

**An execution, not a logical job.** Delivery is at-least-once, so a redelivery
writes a second run row while writing zero new signals — which is the honest
record of what happened. The repeat pass above produced exactly that: 4 run rows
from 2 executions × 2 extractors, and 5 signals unchanged.

Not an observability subsystem: one table, one insert per execution, no metrics,
no timers, no dashboard.

---

## 3. §53 — the questions, answered

### Is `numeric_period_change` implemented? What extractor/version?

Yes. **`numeric-period-change@1.0.0`**, reading `numeric_observation`, family
`MEASURED_SERIES`.

### Is `lexical_frequency_contrast` implemented? What extractor/version?

Yes. **`lexical-frequency-contrast@1.0.0`**, reading
`lexical_frequency_observation`, family `LEXICAL_FREQUENCY`.

### Are both fully deterministic? Does either make network/model calls?

Both are `derivation_kind = DETERMINISTIC`, and the database refuses a
deterministic signal that carries a model or prompt version.

Neither imports a network client, a model, an embedder or a vector store —
asserted by `validate_signals.py` walking **every import** in `sros_nlp` and
`sros_signal_model`, over 26 forbidden module names. AST, not grep: a docstring
naming a module must not be able to fail the check.

### Can one observation produce a Signal?

No. The contract's rule is unchanged and the extractors inherit it: a single
World Bank observation is refused as `INSUFFICIENT_INPUT_OBSERVATIONS`, and the
run log records why.

### How are distinct observations enforced?

Over `observation_key`, never over `normalized_record_id`. Two normalized rows of
one observation are refused as `AMBIGUOUS_OBSERVATION_LINEAGE` — by the model,
and separately by each extractor when it finds a duplicate period label or a
duplicate term in one group. The repository additionally excludes `superseded_at
IS NOT NULL` rows, which is a retired raw version rather than a lineage choice;
**D-08 is not solved.**

### How are candidate inputs grouped?

By a canonically serialised key, so only records sharing one can meet.

```text
numeric   source · kind · metric scheme+id · geography kind+canonical+source code ·
          series dataset+resource+frequency · unit state+unit · period type
lexical   source · kind · series resource · EXACT period label ·
          language scheme+label · gram size
```

Every field is load-bearing. Dropping the geography lets France meet Germany;
dropping the unit lets thousands be subtracted from units.

### What pairing strategy does `numeric_period_change` use?

`adjacent_periods`, and it is a **parameter** rather than a constant because it
changes which signals exist. Over 2018/2019/2020 it emits 2018→2019 and
2019→2020, not 2018→2020. Fingerprinted, persisted, and part of the derivation
identity.

### What exact arithmetic does it emit? How is zero handled?

`absolute_change = current − previous`, arbitrary-precision `Decimal` on both
sides. `9007199254740995 − 9007199254740993 = 2` exactly.

**No percentage and no ratio**, so there is no denominator and no zero-denominator
case. Both would need a rounding rule, and a repeating decimal rounded to an
unstated precision is fake precision. A zero *value* is a measurement and is
subtracted normally; a zero *change* is `UNCHANGED`.

### How is `SignalDirection` derived? Does numeric change mean market growth?

Mechanically from the sign: `>` → `INCREASING`, `<` → `DECREASING`, `=` →
`UNCHANGED`. Never `POSITIVE`/`NEGATIVE`, which are not in the enum.

**No.** A population of 82,905,782 becoming 83,092,962 is a population going up
by 187,180. Whether that is market growth is a Claim, and a Claim has its own
evidence.

### What temporal basis does World Bank use?

`COMPARABLE_INSTANTS`. Its periods are `YEAR` with `timezone_state ESTABLISHED`
and aware bounds, so the window carries `start` and `end` and `observed_at` is
set.

### What compatibility rules does lexical contrast require?

Same source, same record kind, same series resource, **same exact period label**,
same source language label and scheme, same gram size — and two different terms
with distinct observation keys. Anything else is `INCOMPATIBLE_SERIES` naming
the field that disagreed.

### Can different GDELT buckets be compared? Is H-32 respected?

**No, and yes.** The grouping key carries the exact bucket label, so two buckets
never share a group and no ordering between them is required, asserted or
possible. There is no frequency change, growth, decline, moving average or
rolling window in this extractor.

Two labels that *look* ordered are refused, and a test asserts it. The database
adds a second, independent guard: a direction other than `NOT_APPLICABLE`
requires an ordered temporal basis, so **no GDELT signal can carry one**.

### Can unmapped CLD2 labels participate? Can different labels be combined?

Yes, and no. Equality of the exact source label and its scheme is sufficient
within one source — `ENGLISH` from `cld2-language-name` equals `ENGLISH` from
`cld2-language-name`, asserting nothing about what either maps to.

`ENGLISH` and `FRENCH` are refused. `canonical_language_tags` is absent from the
scope, and the model refuses one anyway while H-30 is open.

### Can 1gram and 2gram be compared?

**No.** §19 asked for the decision explicitly: a unigram count and a bigram count
are counts of different kinds of thing. `gram_size` is in the grouping key and a
cross-gram pair is `INCOMPATIBLE_SERIES`.

### Is lexical contrast treated as attention or demand?

No. The magnitude is `ABSOLUTE_DIFFERENCE` with no unit; the scope carries the
terms verbatim and no topic, category, market or motivation; the words
`attention`, `demand`, `trend`, `topic`, `sentiment` and `growth` appear nowhere
in the serialised output, asserted by a test over the payload rather than
field-by-field.

### What is derivation confidence? Does it incorporate source coverage?

`1.0` for both, and **no**. It says the arithmetic was deterministic and valid
under its declared facts. It is not evidence strength, not an `EvidenceScore`
input, and it is not derived from a magnitude or a record count. The coverage
facts sit beside it in the run log, unweighted.

### How are refusals recorded?

A `GroupRefusal` per candidate group — reason, detail, grouping key, observation
keys — collected into the run's `refusals` array, and returned in the task
result. A refused group **never** produces a signal row, and the table refuses a
non-zero `groups_refused` with an empty reason list.

### How is Signal identity computed? Are derivations idempotent?

Exactly as Mission 1.11 defined it: schema, workspace, type, family, extractor
and version, the **ordered contributing inputs**, the parameter fingerprint and
the window. Magnitude, direction, confidence, `derived_at` and `correlation_id`
are excluded.

Idempotent: the repeat pass produced `new 0 · unchanged 5`, with no duplicate
signal rows and no duplicate lineage rows. That is idempotent **persistence**,
not exactly-once delivery.

### How many real Signals were created?

**Four** World Bank, **one** GDELT.

| Series | Periods | Magnitude | Direction |
|---|---|---|---|
| `SP.POP.TOTL` · DE | 2018 → 2019 | `187180` | `INCREASING` |
| `SP.POP.TOTL` · DE | 2019 → 2020 | `67909` | `INCREASING` |
| `SP.POP.TOTL` · FR | 2018 → 2019 | `223713` | `INCREASING` |
| `SP.POP.TOTL` · FR | 2019 → 2020 | `219049` | `INCREASING` |
| `climate` vs `weather` | bucket `20260830091500` | `19` | `NOT_APPLICABLE` |

Two World Bank groups because Germany and France are two series — the count
follows from the grouping key, not from anything decided in advance.

### Did repeated extraction create duplicates?

No. 5 signals, 10 lineage rows, 4 run rows (2 executions × 2 extractors).

### Did all Raw/Normalized records remain byte-for-byte unchanged?

Yes. 8 raw and 8 normalized, `(source_id, observation_key, content_hash)` digest
identical to the Mission 1.11 baseline:

```text
d8cf83214a930be67f42f018224a657cdb0fdb8028f9f5414eccbd507e55140c
```

### Were any Evidence rows, Claims, embeddings, Opportunities or scores created?

**None.** All zero, and `validate_signals.py` fails the build if the package
even names `scoring.evidence`, `research.claims`, `research.opportunities` or
`nlp.embedding_provenance`.

### What should Mission 1.12 implement next?

See §6.

---

## 4. Two decisions the contract could not express

Both were found while implementing, and both are contract changes rather than
workarounds. `1.6.0` → `1.7.0`.

### `ABSOLUTE_DIFFERENCE`

`ABSOLUTE_CHANGE` asserts that something **changed**, which is a statement about
time. A same-bucket contrast between two lexical terms is a difference between
two quantities measured at the same position — nothing changed, and using the
temporal kind would have asserted a temporality H-32 says is not established.

Storing `climate − weather = 19` as an `ABSOLUTE_CHANGE` would have been the
mission's own §16 violated in the one field a consumer branches on to decide how
to read the number.

### `INCOMPATIBLE_SERIES`

`INCOMPATIBLE_INPUT_KINDS` means *the inputs disagree on record kind or period
resolution*. Two World Bank observations of **different countries** disagree on
neither — same kind, same `YEAR` — and are still not observations of the same
measured series.

§34 offered four candidate codes for this (`INCOMPATIBLE_SERIES`,
`SOURCE_LANGUAGE_MISMATCH`, `GRAM_SIZE_MISMATCH`, `INCOMPATIBLE_PERIOD`). One
value carries them all and the `detail` names the field: four codes for one
question would make a consumer branch on *which* field happened to differ, which
is not a decision anything downstream makes differently.

---

## 5. The defect the database caught

Migration 0013 gave the run log two arithmetic constraints, written as
belt-and-braces. The second failed on the third integration test, and the defect
was real:

```python
for draft in outcome.drafts:
    contributed += len(draft.contributed)  # wrong
```

Over 2018/2019/2020 that produces two signals and counts **four** contributors
from **three** records, because 2019 belongs to both pairs. The run log would
have reported more contributing records than it read.

**No unit test would have caught it.** Every extractor test asserted the signals,
which were correct; the counters are diagnostics nobody branches on, so nothing
asserted their relationship to each other — and the wrong number would have sat
there being quietly believed by whoever read it during an incident.

It now counts **distinct** records, and a record excluded from one signal while
contributing to another counts as a contributor. Recorded as
`testing-strategy.md` §25: *when two stored numbers have an arithmetic
relationship, put it in a CHECK.*

---

## 6. Scope discipline, and what comes next

| Forbidden by the brief | State |
|---|---|
| GDELT temporal change / growth | Not implemented, and structurally impossible: the grouping key carries the exact bucket label |
| Claims | 0 |
| Evidence | 0 |
| Opportunities | 0 |
| Embeddings | 0. Nothing loads BGE-M3, writes a vector or touches Qdrant. D-12 untouched |
| Scoring | 0. D-03 untouched |
| LLM calls | None. `DETERMINISTIC` is enforced by a CHECK |

**H-29, H-30 and H-32 all remain open**, and each still blocks exactly what it
blocked before.

### Mission 1.12

The pipeline now runs `acquisition → normalization → signals` end to end on real
data, and stops. Three things are worth weighing, in this order:

1. **Ask GDELT the two questions.** H-32 is one first-party sentence away and
   unblocks every within-stream sequential derivation; H-29 unblocks that plus
   cross-source alignment. Both are cheaper than any code in this mission and
   they gate more.
2. **The Signal → Evidence boundary.** Five signals exist and nothing consumes
   them. Evidence is claim-scoped, so this means deciding how a Claim comes into
   existence — which is where the interpretation this whole layer refuses to do
   has to start being done deliberately, with its own confidence.
3. **A third source, or more of the two.** Four of the five signals are one
   metric in two countries. The extractors are source-agnostic — they read
   record kinds — so more data needs no new extractor, and one more numeric
   source would exercise `numeric-period-change` against a series it was not
   written beside.

**Not** embeddings or clustering: D-12 is open and nothing here needs them.

---

## 7. Validation

```text
zero-dependency suites   405 tests across 6 packages
pytest suites            288 tests across 7 packages  (72 new)
schema validation        9 invariant groups, 36 tables
signal boundary guard    5 boundary groups, probed against 3 violations
normalization guard      9 boundary groups
evidence aggregation     8 checks; production scoring still blocked
source registry          27 sources, 33 evidence records
contracts --check        3 generated artifacts current
TypeScript conformance   21/21
mypy strict              129 source files
ruff + ruff format       clean, 346 files
```

Post-suite: **22 tenant and 14 global tables unchanged by the run** — every
integration test writes into a disposable workspace and removes it.

---

## 8. Risks left open

- **`terms` being required makes the lexical extractor unsweepable**, by design.
  Nothing derives GDELT signals unattended, and nothing should until somebody
  reviews a selection rule.
- **The run log grows per execution.** Bounded by 90-day retention and by
  nothing else; a scheduler running the same job hourly writes a row an hour.
- **Four of five signals are one metric in two countries.** The extractors are
  source-agnostic, but they have only been exercised against one real numeric
  series and one real bucket.
- **`CLASSIFIED_GEOGRAPHY` being required is the numeric decision to disagree
  with.** A change in an unclassified series is arithmetically true and its scope
  could not say where the measurement is from. That is defensible and it does
  refuse work that is not wrong.
- **D-08 is more visible again.** A second extractor version writes rows beside
  the first; which to read is still undecided.
- D-03, D-10, D-12, H-12, H-13, H-22 to H-27, H-29, H-30, H-31, H-32,
  PROFILE-NOT-CALIBRATED unchanged.
