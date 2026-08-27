# `services/workers`

**Status:** infrastructure skeleton implemented (Mission 0.2). **No business job
body exists, and none may be added until the context that owns the work is
implemented.**
**Runtime:** Python / **Celery** with **Redis** as broker and result backend
(ADR-004). Audit C-01 is resolved: BullMQ was removed from the stack rather than
worked around, and there is no Node worker tier.

## Responsibility

Execute queued work reliably: retries, backoff, concurrency limits, scheduling,
dead-lettering, and progress reporting.

Workers own **execution mechanics**, not decisions. A worker never decides what
to research (`research-orchestrator`), how to interpret data (`nlp`), or what a
score means (`scoring`). It runs a job and reports what happened.

## Inputs

- Jobs enqueued by `research-orchestrator`
- Scheduled/recurring jobs (incremental refresh, decay recomputation)

## Outputs

- Job execution: invocations of `acquisition`, `nlp`, `scoring`,
  `market-intelligence`, `competition`, `execution`
- Progress events back to `research-orchestrator`
- Failure records and dead-letter entries
- Queue telemetry: depth, throughput, failure rate, latency per job type

## Dependencies

- Redis — Celery broker and result backend
- Celery — task framework, routing, scheduling (Beat)
- All compute contexts, imported in-process (same Python codebase as `api`)
- `packages/contracts`

## Queue topology (ADR-004)

Separate Celery queues per job class, each with its own worker pool, concurrency
limit and prefetch setting:

| Queue | Job classes | Why separate |
|-------|-------------|--------------|
| `acquisition` | Source collection, browser automation | Network-bound, slow, external rate limits |
| `nlp` | Extraction, classification | LLM-backed, budget-consuming |
| `embedding` | BGE-M3 embedding, clustering | Compute-heavy, batched |
| `analysis` | Scoring, market, competition, execution | Fast, pure computation over stored inputs |
| `maintenance` | Celery Beat jobs: decay, re-embedding, refresh | Must never be starved by research load |

Slow acquisition must not starve fast analysis, and heavy embedding work must not
monopolize the pool. Per-source concurrency limits live here too, which is how
rate-limit compliance becomes a queue configuration rather than something each
new collector has to remember.

`workers` and `api` share the same Python codebase and import the same context
modules. They differ only in entrypoint.

## Implementation notes (Mission 0.2)

```
python/sros_workers/
├── queues.py      queue topology, routing, retry policy  (NO Celery import)
├── context.py     correlation headers, idempotency keys  (NO Celery import)
└── celery_app.py  application factory                    (imports Celery lazily)
```

`queues` and `context` are deliberately Celery-free, so the rules that matter —
routing, backoff, tenant propagation, idempotency keys — are tested without a
broker, a worker, or even the Celery package installed. 21 tests.

Configuration choices that are deliberate rather than default, because the
defaults are wrong for this workload and getting them wrong loses jobs silently:
`task_acks_late`, `task_reject_on_worker_lost`, `worker_prefetch_multiplier=1`,
JSON-only serialization (pickle off a broker is a remote-code-execution shape),
and expiring results (Redis is not canonical).

## Future job types

```
acquire.source          collect from one source
normalize.batch         raw -> normalized
nlp.extract             normalized -> signals
nlp.embed               text -> embeddings (batched)
nlp.cluster             embeddings -> opportunity seeds
score.opportunity       evidence -> five score families
market.analyze          opportunity -> market context
competition.map         opportunity -> competitor set + gap
execution.plan          opportunity -> MVP + GTM plan
maintenance.decay       recompute evidence recency decay
maintenance.reembed     re-embed after a model change (D-12)
maintenance.retention   expire records per data-retention-policy-v1.md
```

## Hard constraints

1. **Idempotent jobs.** Every job must be safe to run twice. Celery over Redis
   gives **at-least-once** delivery; exactly-once is not available. Each job
   carries a deterministic idempotency key, upserts rather than blind-inserts,
   and guards any side effect that spends money or touches an external source.
   An "already processed?" read-then-write without a uniqueness constraint is a
   race, not idempotency — the constraint belongs in the database.
2. **Bounded cost per job.** Timeouts and budgets are enforced by the worker, not
   trusted to the callee (`data-principles.md` §12).
3. **Rate limits are respected at the queue level**, not only inside
   `acquisition`. Concurrency per source is a queue configuration.
4. **Failures are recorded, not swallowed.** A job that fails permanently becomes
   a research gap in `research-orchestrator`, not a silent absence of data.
5. **Backpressure is real.** An unbounded queue with an expensive consumer is how
   this system would generate a surprise LLM bill.

## Failure modes to design for

| Failure | Required behavior |
|---------|-------------------|
| Job times out | Fail with a timeout reason, retry with backoff, then dead-letter |
| Poison message | Dead-letter after N attempts; never block the queue |
| Worker crash mid-job | Job returns to the queue; idempotency makes the retry safe |
| Queue backlog growing | Alert on depth and age, not only on failure rate |
| Redis unavailable | Fail fast and loudly. Do not fall back to in-process execution — that silently removes every guarantee the queue provides, at the moment the system is already degraded |
| Task payload missing `workspace_id` | Fail closed. Never resolve a workspace inside a worker, never fall back to a default (ADR-005) |
| Duplicate delivery | Absorbed by idempotency; never by an "already processed?" check that races |
