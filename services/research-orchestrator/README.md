# `services/research-orchestrator`

**Status:** **implemented as a package** (Mission 0.4). `sros_orchestrator`
owns the session lifecycle, planning, the job ledger, dependency ordering,
budget accounting, cancellation, resumability and Research Completeness
recording. It dispatches nothing today, because every domain capability is
blocked — see §What is blocked, and why nothing runs.
**Runtime:** Python. No database driver: the repositories take any object
exposing `tenant_transaction(workspace_id)`, so this package never imports
`sros_gateway` and the dependency graph stays acyclic (`service-boundaries.md`
§4).
**Unblocked:** D-01, A-06 and A-11 were resolved by Ontology V2 §11.
`ResearchSession` is the canonical persisted execution, `ResearchContext` is its
immutable input snapshot, and `ResearchProject` is the persistent grouping.

## Responsibility

Owns the **lifecycle of a `ResearchSession`**. It decides what to research, in
what order, how deep to go, when there is enough evidence, and when to stop.

It is the only context that holds the plan. Every other context answers a
question; the orchestrator decides which questions to ask.

It owns three entities (Ontology V2 §11): `ResearchProject` (persistent
objective), `ResearchSession` (the only persisted execution), and the immutable
`ResearchContext` snapshot stored on each session.

## Why it exists

Without it, research depth is an emergent property of whatever the collectors
happen to return. With it, `Research Completeness`
(`scoring-framework-v1.1.md` §2) becomes a measurable quantity, because something
in the system knows what the intended search space was.

## Inputs

- A `ResearchContext` (Ontology V2 §11.3): `market_scope` (§4), market types,
  product types, domains, audience, languages, budget and technical constraints,
  desired MVP complexity, research depth, time horizon, exclusions — always
  within a `workspace_id` and a `project_id`.
- Progress events from `workers`.
- Evidence sufficiency reports from `scoring`.

## Outputs

- A **research plan**: an ordered, budgeted set of acquisition and analysis tasks.
- Jobs enqueued for `workers`.
- `ResearchSessionStatus` (closed enum, Ontology V2 §15):
  `PENDING → PLANNING → COLLECTING → ANALYZING → SCORING → COMPLETED | FAILED | CANCELLED`.
- An immutable `ResearchContext` snapshot written at session creation.
- Per-run cost budget accounting, decremented by the LLM Gateway (ADR-006).
- A `Research Completeness` estimate with its rationale.
- A **research gap report**: what was intended but not covered, and why.

## Dependencies

- Celery over Redis (ADR-004) — job dispatch, Beat for scheduled maintenance
- PostgreSQL — run state, plan, task ledger (all tenant-scoped)
- `services/scoring` — evidence sufficiency feedback
- `packages/contracts`

## Future API surface

```
POST   /internal/projects                       create a ResearchProject
GET    /internal/projects/{id}                  project + its sessions
POST   /internal/sessions                       create a ResearchSession
                                                (project_id + ResearchContext)
GET    /internal/sessions/{id}                  status, progress, cost consumed
GET    /internal/sessions/{id}/context          the immutable context snapshot
POST   /internal/sessions/{id}/cancel           cooperative cancellation
GET    /internal/sessions/{id}/plan             the plan and its task ledger
GET    /internal/sessions/{id}/gaps             intended vs covered search space
POST   /internal/sessions/{id}/events           progress callback from workers
```

## Modules

```
services/research-orchestrator/python/sros_orchestrator/
├── lifecycle.py     session status transitions -- the ONLY place they are decided
├── jobs.py          the generic job description and its ledger states
├── dag.py           dependency ordering, without a workflow engine
├── plan.py          the ResearchExecutionPlan and the blocked-capability register
├── budget.py        configured / reserved / actual accounting and the guard
├── completeness.py  the Research Completeness record. No formula
├── repositories.py  persistence over a duck-typed tenant database
└── orchestrator.py  the coordinator
```

`sros_gateway.db.repositories` still holds the project and session *persistence*
Mission 0.3 wrote, and now imports `ALLOWED_TRANSITIONS` and
`require_transition` from `lifecycle.py`. There is one transition table, not a
copy that drifts: the policy decision moved here, the storage did not.

## What is blocked, and why nothing runs

Every domain capability the planner enumerates is currently unavailable:

| Capability | Blocked by | Reason |
|------------|-----------|--------|
| `ACQUISITION` | **D-07** | No source registry and no per-source legal review record, so no source may lawfully be collected from |
| `NORMALIZATION` | D-07 | Nothing to normalize while acquisition is blocked |
| `NLP_EXTRACTION` | D-12 | Embedding versioning undecided; NLP execution out of scope |
| `OPPORTUNITY_DISCOVERY` | D-12 | Consumes NLP signals, which are not produced |
| `SCORING` | **D-03** | The evidence aggregation rules are undefined; implementing scoring would mean choosing them |

So `plan_session` produces a plan whose stages are **all** `BLOCKED`, each
carrying the decision id that governs it, and `advance` dispatches nothing.
That is the honest output, not a limitation of the implementation.

**The guard is mechanical.** A `BLOCKED` job has no permitted transition to
`READY`, and only `READY` jobs are dispatched. There is no code path that can
dispatch blocked work, so §32 and §33 hold without anyone remembering them.

The dispatch, retry, resumption and budget machinery is nonetheless real and
tested: it is exercised with job specs supplied directly by a caller, which is
what a capability will do once it is unblocked.

## Cancellation semantics, stated honestly

`cancel()` moves the session to `CANCELLED` where the lifecycle allows it and
cancels every job not yet handed to a worker, so no further work is dispatched.

**It does not stop work already running inside a worker, and does not pretend
to.** Celery revocation is advisory, a process mid-HTTP-call does not observe
it, and `task_acks_late` means a killed worker returns the job to the queue.
Claiming instant distributed cancellation would make a caller believe a resource
was freed when it was not. In-flight jobs are reported, and their results are
still recorded — a cancelled session that completed three jobs did three jobs,
and hiding that would make the ledger wrong.

## Resumability

There is no in-memory state to restore, which is the design. Plan, ledger,
dependency edges and budget entries are all in PostgreSQL (ADR-008: Redis is
never canonical), so `resume()` is `advance()` plus one step: jobs left
`DISPATCHED` or `RUNNING` by a dead worker return to `READY` if they have
attempts left.

That reclaim is safe **because** delivery is at-least-once and every job is
idempotent (ADR-004). The worst case is the work happening twice and the second
result colliding on the idempotency key.

Job ids are derived from the idempotency key (`deterministic_job_id`), so a
replan after a crash converges on the ledger that already exists instead of
inserting a parallel copy.

## When a workflow engine becomes justified

`dag.py` is about a hundred lines: a dependency list and a rule for when a job
becomes runnable. Celery already provides the queue, retry, routing and
dead-letter path (ADR-004), so a workflow engine would add a second scheduler
competing for authority over what runs.

Recorded so the decision has a trigger rather than a preference. Adopt one when:

1. **Dynamic fan-out** — the number of downstream jobs is unknown until an
   upstream finishes, and large enough that materialising edges eagerly is
   impractical.
2. **Long-running human-in-the-loop steps** (`llm-reasoning-rules.md` §11) that
   must survive days, where a durable timer beats a database poll.
3. **Cross-session workflows** spanning several ResearchSessions, which have no
   single owner row to hang state on.
4. **More than one operator**, at which point a shared UI stops being a
   convenience.

None is true today. Two are plausible within a year, which is why the dependency
data lives in a table rather than in code.

## Core design constraints

1. **Bounded cost per session.** `data-principles.md` §12 and the Cost Awareness
   principle require incremental collection. A session carries an explicit budget
   and stops when it is exhausted, reporting lower Research Completeness rather
   than overspending silently.
2. **Selective depth.** Deep research is triggered by signal, not applied
   uniformly. Cheap breadth first, expensive depth only where breadth found
   something.
3. **Idempotent and resumable.** A session interrupted at 80% resumes; it does
   not re-collect what it already has (`data-principles.md` §12, "avoid
   repeatedly collecting identical data").
4. **Incompleteness is a first-class output.** A session that could not cover a
   source family reports that fact. Silent partial coverage inflates every
   downstream confidence. A session with partial coverage is `COMPLETED`, not
   `FAILED` (Ontology V2 §15).
5. **The context snapshot is immutable.** Editing a project's default context
   must never retroactively change what a past session says it ran with. That
   immutability is the reproducibility guarantee (Ontology V2 §11.3).

## Failure modes to design for

| Failure | Required behavior |
|---------|-------------------|
| Source family unavailable | Continue, record the gap, lower Research Completeness |
| Budget exhausted mid-session | Stop cleanly, mark `COMPLETED` with explicit partial coverage and recorded gaps |
| Worker crash | Task retried with backoff; after N failures, recorded as a gap, not a session failure |
| Zero evidence found | Valid outcome — a session producing no opportunity is `COMPLETED`, not `FAILED` |
| Cancellation | Cooperative: in-flight tasks finish or abort cleanly, no orphaned jobs |
| LLM budget exhausted mid-session | Gateway refuses further calls; session reaches `COMPLETED` with explicitly lower Research Completeness rather than overspending (ADR-006) |
