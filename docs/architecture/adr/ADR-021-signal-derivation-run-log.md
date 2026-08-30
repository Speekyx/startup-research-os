# ADR-021 — A refused derivation gets a run record, never a Signal

**Status:** Accepted
**Date:** 2026-08-30
**Mission:** Sprint 1 / Mission 1.11.1
**Extends:** [ADR-020](ADR-020-signal-derivation-model.md) (a Signal is a
derivation), [ADR-004](ADR-004-celery-over-redis.md) (at-least-once delivery),
[ADR-012](ADR-012-row-level-security.md) (two tenancy layers).
**Related:** [`signal-derivation-runtime-v1.md`](../../data/signal-derivation-runtime-v1.md),
[`signal-contract-v1.md`](../../data/signal-contract-v1.md).

---

## Context

ADR-020 decided that a derivation which cannot run produces **no Signal** — a
row in a table of signals says a signal exists, and one meaning "no signal
exists" is a misleading signal. Mission 1.11 recorded the consequence as an open
question: an attempt that produced nothing then left no durable trace outside
job logs.

Mission 1.11.1 §4 requires resolving it before production extraction, and the
operational question is specific:

```text
the extractor considered N candidate groups
M emitted Signals
K were refused
and why
```

Four candidate homes existed.

| Mechanism | Why it does not answer it |
|---|---|
| The Celery return value | Lives in the Redis result backend, expires, is not tenant-scoped and is not queryable |
| Structured logs | "Grep the logs" is not an operational answer, and nothing retains them under a data policy |
| `research.research_jobs` | The orchestrator's ledger. It has **no result column**, and it is written in a different transaction from the signals |
| `nlp.signals` | Forbidden by ADR-020 |

---

## Decision

**`nlp.signal_derivation_runs` — one row per extractor EXECUTION, written inside
the same transaction as the signals it emitted.**

Ten counters, a JSONB refusal list, a truncation reason and the correlation id.
Tenant-scoped, RLS `ENABLE` and `FORCE`, retained **90 days** as operational
data rather than the 12 months a signal gets.

### Why not `research.research_jobs`

It was the closest and it fails on two counts. Adding a result column would mean
wiring a worker to write back into the `research` schema — plumbing that does
not exist today, for a column every job type would then be expected to fill.
And a ledger update is a *different transaction* from the signal writes, so
"6 emitted, 2 refused" could disagree with what was actually stored.

### Why an execution and not a logical job

Delivery is at-least-once (ADR-004). A redelivery writes a **second run row**
while writing **zero new signals**, and that is the honest record: two
executions happened, and exactly one of them had work to do.

The alternative — keying the run on the job's idempotency key so a redelivery
overwrites — would make the table smaller and would erase the fact that the job
ran twice, which is precisely the operational question this table exists to
answer.

**The signals are what is idempotent. The run log is an event log.**

### Why a refusal count must carry its reasons

`CHECK (groups_refused = 0 OR jsonb_array_length(refusals) > 0)`. A count with
no reasons behind it is the "something did not happen" this table replaces.

---

## Consequences

**Positive**

- A refused derivation is durable, tenant-scoped and queryable, with no
  misleading row in `nlp.signals`.
- Counts and signals are written atomically, so they cannot disagree.
- The table's own arithmetic constraints caught a real defect during
  implementation: `records_contributed` was summed per draft, and one record
  legitimately contributes to several signals — 2019 belongs to both the
  2018→2019 and the 2019→2020 pair — so the run reported more contributors than
  there were records. It now counts **distinct** records.

**Negative, and accepted**

- A twelfth table, and a second thing to retain.
- Rows accumulate per execution. Bounded by the 90-day window and by nothing
  else; a scheduler running the same job hourly writes a row an hour.
- It records what the *extractor* refused. A job that never started, or a worker
  that died mid-transaction, leaves nothing — that is the orchestrator's ledger's
  job, and this does not duplicate it.

**Neutral**

- No metrics, no timers, no counter service, no dashboard. §4 forbids an
  observability subsystem and this is one table with one insert per execution.
- The same JSON comes back from the Celery task, so a log reader sees it too.
