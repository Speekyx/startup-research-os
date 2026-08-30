# Signal Derivation Runtime V1

**Status:** Authoritative for how deterministic signal extraction is executed,
grouped, persisted and observed.
**Date:** 2026-08-30 (Sprint 1 / Mission 1.11.1)
**Code:** `sros_nlp` (`services/nlp/python`)
**Related:** [`signal-contract-v1.md`](signal-contract-v1.md),
[`numeric-period-change-extractor-v1.md`](numeric-period-change-extractor-v1.md),
[`lexical-frequency-contrast-extractor-v1.md`](lexical-frequency-contrast-extractor-v1.md),
[ADR-020](../architecture/adr/ADR-020-signal-derivation-model.md),
[ADR-021](../architecture/adr/ADR-021-signal-derivation-run-log.md).

---

## 1. The §4 decision — where a refused derivation goes

Mission 1.11 left one question open: a derivation attempt that produces no
Signal leaves no durable trace. Mission 1.11.1 §4 requires resolving it **before**
production extraction, and forbids the obvious wrong answer — a Signal row that
means "no signal".

### What already exists, and why none of it is sufficient

| Mechanism | What it holds | Why it does not answer the question |
|---|---|---|
| Celery task return value | The job result JSON | Lives in the result backend (Redis), expires, and is not tenant-scoped or queryable |
| Structured logs | Whatever was logged | Not queryable per workspace, not retained under a data policy, and "grep the logs" is not an operational answer |
| `research.research_jobs` | One row per **planned stage**, with `status`, `blocked_reason`, `last_error` | Written by the orchestrator, and it has no result column. It says a job ran; it cannot say *which candidate groups it considered and why four were refused* |
| `nlp.signals` | Emitted signals | **Forbidden.** A row here says a signal exists |

`research.research_jobs` was the closest and was rejected on two grounds. It has
no result column, so option C would mean adding one and wiring a worker to write
back into the `research` schema — plumbing that does not exist today, for a
column every job type would then be expected to fill. And it is written in a
different transaction from the signals, so "6 emitted, 2 refused" could disagree
with what was actually stored.

### Decision — a run log, written in the derivation transaction

`nlp.signal_derivation_runs`: **one row per extractor execution**, written inside
the same transaction as the signals it emitted. Ten columns and one JSONB list.

```text
extractor_id, extractor_version, signal_type_id, parameter_fingerprint
groups_considered, groups_derived, groups_refused
signals_new, signals_unchanged
records_considered, records_contributed, records_excluded
refusals JSONB   -- [{reason, detail, group_key, observation_keys}]
```

It answers §4's question directly:

```text
extractor considered N candidate groups
M emitted Signals
K were refused
why       -> refusals[].reason and .detail
```

**Why a run and not a job.** A Signal is *not* run-scoped — it converges across
sessions and outlives the one that first derived it (contract §16). A refusal
is: it says *on this pass, over these candidates, nothing came out*. Those are
different lifetimes, so they are different rows, and putting a refusal on a
signal table would have needed a signal that does not exist.

**It records executions, not logical jobs.** Delivery is at-least-once (ADR-004),
so a redelivery writes a second run row while writing zero new signals — which
is the honest record of what happened. The **signals** are what is idempotent;
the run log is an event log, retained 90 days like `research.research_jobs`
rather than 12 months like a signal.

**It is not an observability subsystem.** No metrics, no timers, no counters
service, no dashboard. One table, one insert per execution, and the same JSON
comes back from the Celery task for whoever is reading logs.

---

## 2. Where the code lives

```text
services/nlp/python/sros_nlp/
    extractors/            the two deterministic extractors and their registry
    grouping.py            candidate grouping keys
    repositories.py        reading normalized records, writing signals + lineage + runs
    job.py                 one derivation job, testable without a broker
    errors.py
services/workers/python/sros_workers/signal_tasks.py    the Celery surface only
```

`services/nlp` is the service `service-boundaries.md` already assigns signals to.
Its README described embeddings, clustering and LLM classification as well —
none of which exists, and none of which this mission adds.

**`packages/signal-model` contains no extractor and still does not.** It defines
what a Signal *is*; `sros_nlp` derives one. The dependency runs one way.

### The payload boundary, and why the extractor may cross it

`ObservationInput` — the model's view of a record — deliberately carries no
payload: *"it must not be able to read a payload, reading one is how a model
starts interpreting"*. An extractor obviously must read the value it is
subtracting.

So the repository produces a richer `NormalizedObservation` carrying the payload,
the extractor does arithmetic over it, and hands the model plain
`ObservationInput` objects. The model validates identity, lineage, scope and
temporal shape; the extractor computes. Neither does the other's job.

---

## 3. Candidate grouping

Production extraction never compares every record with every other record.
Records are bucketed by a **deterministic grouping key**, and only records
sharing a key can meet.

| Extractor | Grouping key |
|---|---|
| `numeric-period-change` | source · record kind · metric scheme + id · geography kind + canonical code + source code · unit state + unit · series dataset + resource · period type |
| `lexical-frequency-contrast` | source · record kind · series resource · **exact period label** · language scheme + label · gram size |
| `lexical-frequency-change` | source · record kind · series resource · language scheme + label · gram size · **term** |

The two lexical keys are mirror images and the difference is exactly one field:
the contrast groups by the **bucket** and varies the term; the change groups by
the **term** and varies the bucket.

Both keys are built from canonical payload fields only, sorted, and serialised
canonically, so a key is stable across runs and across machines.

A record whose key differs lands in a different group and **never meets** the
other. Refusals therefore mostly do not arise from grouping — they arise when a
caller hands an explicit pair, which the extractors also accept and check.

---

## 4. Refusals

The extractor reports a refusal per **group**, using the contract's
`SignalRefusalReason` vocabulary. Mission 1.11.1 §34 lists candidate codes; every
one maps onto an existing value except one, which was added:

| §34 candidate | Canonical value |
|---|---|
| `INSUFFICIENT_DISTINCT_OBSERVATIONS` | `INSUFFICIENT_INPUT_OBSERVATIONS` |
| `INCOMPATIBLE_SERIES`, `SOURCE_LANGUAGE_MISMATCH`, `GRAM_SIZE_MISMATCH`, `INCOMPATIBLE_PERIOD` | **`INCOMPATIBLE_SERIES`** — added, see below |
| `TEMPORAL_ORDER_NOT_ESTABLISHED`, `CANONICAL_LANGUAGE_REQUIRED`, `MISSING_REQUIRED_FACT` | `REQUIRED_FACT_WITHHELD`, naming the withheld fact |
| `NON_CONTIGUOUS_SOURCE_BUCKETS` | **added in Mission 1.12.1** — no existing value could say it (ADR-023) |
| `INVALID_INPUT` | `INPUT_RECORD_INVALID` |
| `UNSUPPORTED_RECORD_KIND` | `INCOMPATIBLE_INPUT_KINDS` |

### `INCOMPATIBLE_SERIES` was added, and why it had to be

`INCOMPATIBLE_INPUT_KINDS` means *the inputs disagree on record kind or period
resolution*. Two World Bank observations of **different countries** disagree on
neither: same kind, same `YEAR` resolution, and they are still not observations
of the same measured series. The same holds for two GDELT terms from different
buckets or different language labels.

The contract had no way to say *same kind, different thing*. One value covers
every case — metric, geography, unit, dataset, bucket, language, gram size — and
the `detail` names the field that disagreed. Contract `1.6.0` → `1.7.0`.

---

## 5. Persistence

One transaction per job. A Signal never exists without its lineage:
`nlp.signals`, then its `nlp.signal_inputs` rows, then the run record, and a
rollback leaves none of them.

Three outcomes per signal, mirroring the normalization layer's four:

```text
NEW         the first time this derivation identity was stored
UNCHANGED   this exact derivation fingerprint is already stored, byte-identical.
            Nothing is written -- what makes redelivery safe
CONFLICT    the fingerprint is stored with DIFFERENT content. Nothing is
            written, and it is reported
```

`CONFLICT` means the extractor is not deterministic, or an input it read changed
without the version being bumped. The stored row stands; **bumping the extractor
version is the mechanism by which output is allowed to change**. Exactly the
normalization layer's rule, one level up.

**This is idempotent persistence, not exactly-once delivery.** Celery is
at-least-once and this does not pretend otherwise.

---

## 6. Ordering, and why it never comes from the database

Input order is part of the derivation identity, so an order that came from the
database would make the identity depend on a plan the query optimiser chose.

| Extractor | Canonical order |
|---|---|
| `numeric-period-change` | by canonical period **start**, ascending. Position 0 is the earlier observation |
| `lexical-frequency-contrast` | by **term text**, ascending, using the source text verbatim. Position 0 is the lexicographically first term |

Neither uses `collected_at`, a row id, or insertion order. Reversing the rows a
query returns produces the same signal, the same fingerprint and the same
magnitude, and a test asserts it for both extractors.

---

## 7. Orchestration

A new capability, `SIGNAL_DERIVATION`, sits between normalization and NLP
extraction:

```text
ACQUISITION -> NORMALIZATION -> SIGNAL_DERIVATION -> NLP_EXTRACTION -> ...
```

Its block is **derived**, like `NORMALIZATION`'s: it is unblocked only when some
source is eligible, has a collector, has a normalizer **and** has a registered
extractor. A missing wire reads as a refusal, never as a permission.

`NLP_EXTRACTION` stays statically blocked by **D-12**, and separating the two was
required rather than tidy. Its stated reason is embedding model versioning — true
of classification, embedding and clustering, and **false** of deterministic
arithmetic over canonical decimals. A blocking reason that has become false is
worse than a vague one: it invites someone to conclude the block no longer
applies. Mission 1.6 made the same correction to `NORMALIZATION` and Mission 1.2
to `SCORING`.

`signal.derive` routes to the **acquisition** queue, exactly as `normalize.`
does and for the same reason: bounded, CPU-cheap work over records the
deployment already holds. A queue of its own would split a pool for no measured
reason. The `nlp` queue is described as LLM-backed and budget-consuming, which
this is not.

**The extractor consumes NormalizedRecords only.** It never reads a raw record,
never contacts a source, and has no dependency on acquisition beyond the one it
inherits through normalization.

---

## 8. Bounds

Ours, and labelled as such — no external platform published any of them.

| Bound | Value | Why |
|---|---|---|
| Normalized records read per job | 500 | A transaction of a few hundred kilobytes. A workspace with more takes more jobs |
| Groups derived per job | 200 | A group produces at most a handful of signals; the cap keeps one transaction bounded |
| Terms per lexical contrast | exactly 2 | §9 below |
| Terms per lexical change selection | 25 | Same argument as §9. A selection larger than a person writes by hand is a sweep with a list in front of it |

A job that hits a bound **says which one stopped it**, and keeps what it derived.
Truncation is reported, never silent.

---

## 9. Why the lexical extractor requires its terms to be named

A single GDELT WEB-NGRAM file holds hundreds of thousands of rows — the real
acquisition read 223,342. An unselected all-pairs sweep over one bucket is
O(n²): ~2.5 × 10¹⁰ pairs, none of which anybody asked for.

Every bounded default is an invented threshold — "top 100 by count" is a
selection rule nobody reviewed, and the project's standing rule is that an
invented parameter is worse than a refusal. So the terms are a **required
extractor parameter**, exactly two of them, fingerprinted and persisted like
every other output-affecting value.

That makes the lexical contrast a question someone asks rather than a sweep, and
it is the honest shape: *how often did these two terms occur in this bucket,
relative to each other* is answerable; *contrast everything with everything* is
not a question.

---

## 10. What the runtime does not do

Embed, cluster, classify, call a model, contact a network, read a raw record,
write Evidence, write a Claim, produce an Opportunity, or compute a score.
`validate_signals.py` asserts the first six by parsing every import in the
package.

---

## 11. A group may derive AND refuse (Mission 1.12.1)

`groups_derived` counts candidate groups that produced at least one signal;
`groups_refused` counts those that produced at least one refusal. **The two sets
overlap**, and migration 0013's

```sql
CHECK (groups_derived + groups_refused <= groups_considered)
```

asserted that they do not. It read as arithmetic and was really a claim: that a
group either derives or refuses. True of both Mission 1.11.1 extractors, because
each group yielded one outcome — and false the moment an extractor pairs
*within* a group.

The first real `lexical-frequency-change` derivation hit it: one term, three
buckets, one adjacent pair emitting a signal and one gap refused. One group, one
signal, one refusal, and `1 + 1 > 1`.

Migration 0015 replaced it with the invariant that was always true:

```sql
CHECK (groups_derived <= groups_considered AND groups_refused <= groups_considered)
```

`records_contributed + records_excluded <= records_considered` is unchanged —
those two sets are genuinely disjoint, and Mission 1.11.1 made them so after the
same constraint caught a double count. **That is twice this table's arithmetic
has caught a real modelling error**, and both times the counters were the thing
that was wrong about the world rather than about the code.