# `services/research-orchestrator`

**Status:** boundary defined; the **project/session lifecycle now exists** in
`services/gateway` (Mission 0.3) as repositories plus a validated state machine.
Planning, budgeting and job dispatch remain unimplemented.
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

## What exists after Mission 0.3

The persistence and lifecycle rules this context owns are implemented in
`sros_gateway.db.repositories`, so they are testable before the orchestrator is
a separate process:

- `ResearchProjectRepository` and `ResearchSessionRepository`, both requiring an
  explicit `workspace_id`.
- The immutable `ResearchContext` snapshot with its hash and schema version.
- `ALLOWED_TRANSITIONS` — the Ontology V2 §15 state machine, with invalid
  transitions rejected and terminal states terminal.

They move here when this context becomes its own process
(`service-boundaries.md` §2). Nothing plans, budgets or enqueues yet.

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
