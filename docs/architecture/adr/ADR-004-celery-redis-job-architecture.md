# ADR-004 — Celery + Redis for asynchronous job architecture

- **Status:** Accepted
- **Date:** 2026-08-27
- **Deciders:** Project owner (Mission 0.1.1, §3 — explicit human decision)
- **Supersedes:** none
- **Related:** ADR-001, ADR-003, ADR-007, audit **C-01** / decision **D-02**,
  `PROJECT_MANIFEST.md` v1.1 §Technology Stack

---

## Context

### The original conflict

`PROJECT_MANIFEST.md` v1.0 locked a stack that could not be built. It required
simultaneously:

- **FastAPI / Python** as the backend,
- **BGE-M3** and **HDBSCAN** for embeddings and clustering — both Python-only,
- **BullMQ** as the queue.

BullMQ is a Node/TypeScript library implemented on a bespoke Redis key layout
and Lua script set. There is no supported, stable Python client for it. A Python
worker therefore cannot consume a BullMQ queue, and seven of the nine bounded
contexts do Python-shaped work.

The specification audit recorded this as **C-01 (BLOCKING)** and listed three
mutually exclusive resolutions, each with materially different architectural
consequences. It explicitly refused to resolve it, because the choice determines
the language of roughly half the codebase and `docs/CLAUDE.md` §Change control
requires human authorization for that class of change.

### The decision context

The owner reviewed the three options and chose to **amend the locked stack**
rather than build around it. That is the more honest of the two available moves:
the alternative — keeping BullMQ and adding a Node tier whose only purpose is to
satisfy a line in the manifest — would have shaped the architecture around a
documentation artifact rather than around the work.

One fact made the amendment cheaper than it first appeared: **Playwright has a
first-class Python API** (`playwright-python`). BullMQ was the only genuine
reason to keep Node on the backend. Removing it removes Node from the backend
entirely.

## Decision

**Remove BullMQ from the architecture.** Use **Celery** with **Redis** as broker
and result backend for all asynchronous backend and research work.

```text
FastAPI
   ↓  (enqueue)
Celery
   ↓  (broker)
Redis
   ↓  (consume)
Python Workers
   ├── Acquisition jobs      (Playwright, API collection)
   ├── NLP jobs              (extraction, classification)
   ├── Embedding jobs        (BGE-M3)
   ├── Clustering jobs       (HDBSCAN)
   ├── Research jobs         (orchestration steps, scoring, analysis)
   └── Future AI jobs
```

**Next.js remains TypeScript.** It is the only TypeScript runtime in the system,
and it consumes the gateway API. **Python is the primary backend, data and ML
runtime.** There is no Node worker tier.

## Alternatives considered

### Alternative A — Node/BullMQ worker tier + Python compute over HTTP

BullMQ workers in TypeScript orchestrating jobs, calling Python services over
HTTP for every NLP, embedding, clustering and scoring task.

This was the audit's recommendation, on the narrow grounds that it preserved the
locked stack. It was rejected in favour of amending the stack, and on reflection
the audit's recommendation weighted "the manifest says so" too heavily against
the engineering cost:

- a network hop, serialization and deserialization on **every** ML task, in the
  hottest part of the pipeline;
- two languages, two dependency managers, two test runners and two deployment
  paths on the backend, for one person;
- job state in BullMQ and compute state in Python, with failure semantics split
  across the boundary — a worker that dies mid-HTTP-call leaves the job's truth in
  one system and the work's truth in another;
- retries expressed in TypeScript for work executed in Python, so the code that
  decides whether something is retryable is not the code that knows why it failed.

### Alternative B — Dual queue (BullMQ for acquisition, Python queue for ML)

Each tool where it fits. Rejected: two queues means two retry semantics, two
dead-letter mechanisms, two dashboards, two backpressure models, and a bridge
between them that becomes the least-tested component in the system. Permanent
operational cost, for no capability gain.

### Alternative C — Python queue, but RQ instead of Celery

RQ is genuinely simpler and easier to reason about. Rejected because it lacks
what this workload specifically needs: mature scheduled/periodic tasks (Celery
Beat, for maintenance jobs like decay recomputation and re-embedding), workflow
primitives (chains, groups, chords) for the multi-stage research pipeline, and
per-queue routing with distinct concurrency limits — which is how per-source rate
limiting is enforced at the queue level rather than trusted to each collector.

### Alternative D — arq / Dramatiq

Both are credible modern alternatives with cleaner async ergonomics than Celery.
Rejected for ecosystem maturity and operational tooling: for a system that will
run unattended research jobs for years, Celery's monitoring surface (Flower,
mature event stream, well-understood failure modes) outweighs a nicer API.

### Alternative E — Postgres-backed queue (no Redis for queueing)

Fewer moving parts, transactional enqueue with the data write. Rejected: Redis is
already in the stack for caching and rate-limit accounting, so the queue adds no
new infrastructure. Postgres-as-queue also puts pipeline throughput in contention
with the analytical read workload on the same instance.

## Retry semantics

Retry policy is defined **per job type**, never globally. A global retry policy
is either too aggressive for a rate-limited source or too timid for a transient
network blip.

| Job class | Retries | Backoff | Notes |
|-----------|---------|---------|-------|
| Acquisition | 3–5 | Exponential with jitter, respecting `Retry-After` | Never retry aggressively; never rotate identity to evade a limit (`data-principles.md` §3) |
| NLP / embedding / clustering | 2–3 | Exponential | Usually deterministic; a repeated failure is a bug, not bad luck |
| LLM-backed jobs | 2–3 | Exponential with jitter | Budget-aware: a retry consumes budget (ADR-006) |
| Scoring / analysis | 2 | Linear | Pure computation over stored inputs |
| Maintenance (Beat) | 1 | — | Next scheduled run is the retry |

Rules:

1. **Only retry what is retryable.** A parse failure, a schema violation or a
   403 is not retried — it is recorded. Retrying a deterministic failure burns
   budget and hides the bug.
2. **Jitter is mandatory** on any retry that touches an external source.
   Synchronized retries across workers are how a rate limit becomes a ban.
3. **`acks_late = True`** with visibility timeouts sized above the job's p99
   duration. A worker that dies mid-job must not silently acknowledge the work.
4. **The retry budget is bounded by the run budget.** Retries cannot extend a
   research run past its cost ceiling.

## Job idempotency expectations

Redis-brokered Celery gives **at-least-once** delivery. Exactly-once is not
available, so every job must make duplicate execution harmless.

Required of every job:

1. **A deterministic idempotency key** derived from its inputs — for acquisition,
   `(source_id, resource_ref, collection_window)`; for NLP,
   `(record_id, model_version, prompt_version)`.
2. **Upsert, never blind insert**, on the key.
3. **No unguarded side effect.** A job that spends money (an LLM call) or hits an
   external source checks for an existing result first.
4. **Provenance is written with the result in one transaction.** A record without
   its provenance must not be observable, even transiently.
5. **Safe resumption**, not just safe repetition: a job interrupted at 80% must
   be re-runnable without duplicating the 80%.

An "already processed?" check that reads then writes without a uniqueness
constraint is **not** idempotency — it is a race with a longer window. The
constraint belongs in the database.

## Backpressure

The failure mode this system must not have is an unbounded queue feeding an
expensive consumer. That is how a research run becomes a surprise invoice.

- **Bounded concurrency per queue.** Separate queues per job class
  (`acquisition`, `nlp`, `embedding`, `analysis`, `maintenance`) with independent
  worker pools and prefetch limits. Slow acquisition must not starve fast
  analysis, and heavy NLP must not monopolize workers.
- **Per-source concurrency limits** enforced at the queue level, not inside each
  collector. Rate-limit compliance is a queue configuration, so it cannot be
  forgotten in a new collector.
- **Run-level budget enforcement** in `research-orchestrator`: enqueueing stops
  when a run's cost ceiling is reached. This is the primary defense; queue limits
  are the backstop.
- **Depth and age alerting.** Queue *age* matters more than depth — a queue of
  10 jobs that has not moved in an hour is a worse signal than a queue of 10,000
  moving steadily.
- **No fallback to in-process execution when Redis is unavailable.** Fail fast
  and loudly. An in-process fallback silently removes every guarantee the queue
  provides, at exactly the moment the system is already degraded.

## Dead-letter and failure strategy

There is no built-in dead-letter queue in Celery. It is implemented explicitly:

1. Exhausted retries route to a `dead_letter` table in PostgreSQL, with the job
   payload, the full exception chain, the attempt history, and the correlation
   ids (`run_id`, `workspace_id`).
2. **A permanently failed job becomes a research gap**, reported to
   `research-orchestrator`, which lowers `Research Completeness` for the run. It
   does not fail the run.
3. **A poison message never blocks a queue.** After N attempts it is
   dead-lettered and the queue moves on.
4. Dead-lettered jobs are replayable after a fix, using the stored payload.
5. **Failures are counted, not swallowed.** A silent absence of data inflates
   every downstream confidence value — which is the specific failure mode this
   whole architecture is built to avoid.

## Observability expectations

Per `packages/observability` and `docs/CLAUDE.md` §Definition of done:

- **Correlation propagation.** `run_id`, `workspace_id` and `correlation_id`
  travel in every task payload and appear on every log line. A research run must
  be reconstructable from logs alone, across the HTTP → queue → worker → queue
  boundary.
- **Per-queue metrics:** depth, age of oldest message, throughput, failure rate,
  retry rate, latency distribution.
- **Per-job-type metrics:** duration, failure reason breakdown, cost consumed
  (tokens and money for LLM-backed jobs).
- **Structured JSON logs.** Never log credentials, full raw scraped content, or
  personal data.
- **Celery event stream** consumed for task lifecycle visibility; Flower or an
  equivalent for local and operational inspection.
- **Alert on queue age and dead-letter rate**, not only on error rate. A system
  that quietly stops making progress is worse than one that visibly fails.

## Pros

- **One language on the backend.** One dependency manager, one test runner, one
  deployment path, one set of failure semantics. For a single maintainer this is
  the decisive practical benefit.
- **No serialization boundary in the ML hot path.** Workers call BGE-M3 and
  HDBSCAN in-process.
- **Job state and compute state live in the same runtime**, so retry decisions
  are made by code that can see why the work failed.
- **Celery Beat covers scheduled maintenance** (decay recomputation,
  re-embedding, incremental refresh) with no extra component.
- **Workflow primitives** (chain, group, chord) map directly onto the multi-stage
  research pipeline.
- **Per-queue routing** makes per-source rate limiting a configuration rather
  than a discipline.
- **No new infrastructure.** Redis was already in the stack.

## Cons

Stated concretely, because these are the costs being accepted:

- **Celery is operationally heavy** and its configuration surface is large. Many
  of its defaults are wrong for this workload (`acks_late`, prefetch,
  visibility timeout, result expiry all need deliberate setting). Getting them
  wrong produces silent job loss, which is the worst possible failure mode here.
- **Redis as a broker is not durable by default.** Without AOF persistence and
  correct `acks_late`, a Redis restart loses in-flight jobs. This must be
  configured explicitly and verified, not assumed.
- **At-least-once only.** Every job must carry the idempotency burden described
  above. That is real per-job design work, forever.
- **Celery's async story is awkward.** FastAPI is async; Celery workers are
  process/thread-based. The two concurrency models coexist rather than compose,
  and a blocking call in the wrong place is easy to write.
- **The manifest changed.** A locked stack element was removed. That is a
  precedent, and it should stay a rare one — the value of a locked stack is that
  it is not renegotiated per sprint.
- **Turborepo now orchestrates almost nothing on the backend.** With no Node
  services, its role shrinks to `apps/web` and `packages/*`. ADR-001 remains
  valid — the monorepo's value was always atomic contract changes, not task
  running — but the task-graph benefit is smaller than it looked.
- **BullMQ's dashboard is lost.** Flower is serviceable but less pleasant.

## Future impact

**Becomes easy:** adding a job type; running ML in-process; scheduled maintenance
work; scaling worker pools independently per queue; keeping one mental model of
retries and failures.

**Becomes hard:** introducing a Node-based background component later (it would
need its own queue or an HTTP bridge); exactly-once semantics (permanently
unavailable — the design must live with idempotency); using Celery's async
features fluently alongside FastAPI's.

**Revisit if:** Redis broker durability proves insufficient in practice (move the
broker to RabbitMQ, keeping Celery — a configuration change, not a rewrite); or
the workload becomes streaming rather than batch, which is a different
architecture entirely.

**Cost of reversal:** low-to-moderate, and asymmetric. Swapping the *broker*
(Redis → RabbitMQ/SQS) is a configuration change. Swapping the *framework*
(Celery → another Python queue) means rewriting task definitions and retry
configuration, but the job bodies — where the actual work lives — are ordinary
Python functions and port unchanged. Returning to BullMQ would mean
reintroducing the Node tier and is not a realistic path.

## Compliance with authoritative specifications

- `PROJECT_MANIFEST.md` v1.1 §Technology Stack — BullMQ removed, Celery added by
  this ADR. The manifest records the change and its authorization.
- `PROJECT_MANIFEST.md` §Modular Design — per-queue separation reinforces the
  single-responsibility boundary of each context.
- `PROJECT_MANIFEST.md` §Cost Awareness / `data-principles.md` §12 — run budgets,
  bounded concurrency, and retry-budget accounting are the mechanisms.
- `data-principles.md` §3 — per-source concurrency limits enforced at the queue
  level; no aggressive retry, no rate-limit evasion.
- `docs/CLAUDE.md` §Definition of done — observability requirements above.
- `docs/CLAUDE.md` §Change control — this ADR is the explicit, traceable record
  of a change to a locked specification, authorized in Mission 0.1.1 §3.
- **Resolves audit C-01 and decision D-02.**
