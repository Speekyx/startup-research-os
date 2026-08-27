# ADR-003 — Use FastAPI for backend services

- **Status:** Accepted
- **Date:** 2026-08-27
- **Deciders:** Project owner (locked in `PROJECT_MANIFEST.md` §Technology Stack)
- **Supersedes:** none
- **Related:** ADR-001, ADR-004 (required, not written — audit C-01),
  `evidence-confidence-framework-v1.md` §6 and §10, `llm-reasoning-rules.md` §5

---

## Context

Seven of the nine bounded contexts do work that is Python-shaped: NLP,
embeddings, clustering, statistics, and LLM orchestration. Two of the locked ML
dependencies — **BGE-M3** and **HDBSCAN** — exist only in the Python ecosystem.
That is not a preference; it decides the language of the analytical core.

The backend's central obligation is not throughput. It is that **every value
crossing a boundary carries its provenance, confidence and claim type**
(`evidence-confidence-framework-v1.md` §6, §10;
`llm-reasoning-rules.md` §5 requires structured outputs rather than prose). A
backend where an evidence object can lose a field in transit silently violates
the specification, and the violation is invisible until someone audits a score.

So the framework requirement is: **schema validation at every boundary, enforced
by the type system, not by discipline.**

`PROJECT_MANIFEST.md` locks FastAPI and Python.

## Decision

All Python backend services use **FastAPI** with **Pydantic** models at every
boundary — HTTP routes, inter-context interfaces, LLM structured outputs, and job
payloads.

Route handlers adapt; they do not decide. Domain logic lives in modules that can
be tested with no HTTP layer present. No untyped `dict` crosses a module
boundary.

## Alternatives considered

### Alternative A — Django + Django REST Framework

Plausible: batteries included, mature ORM and migrations, admin interface,
strong ecosystem. The admin alone would be genuinely useful for inspecting
evidence records during development.

Rejected as not the locked choice, and because the request model is
synchronous-first. Much of this backend's work is I/O-bound orchestration —
concurrent source fetches, concurrent LLM calls — which fits an async framework
better. DRF serializers are also weaker than Pydantic for the nested,
deeply-typed evidence and score objects this domain requires.

### Alternative B — Flask / Litestar / Starlette directly

Plausible: minimal, unopinionated, no framework magic. Litestar in particular is
a credible modern alternative with arguably better DI ergonomics.

Rejected as not the locked choice. Flask specifically would mean building
validation and OpenAPI generation by hand, which is exactly the discipline-based
enforcement this decision is trying to avoid.

### Alternative C — Node/TypeScript backend (one language across the stack)

Plausible and worth stating: it would eliminate the polyglot cost entirely, make
`packages/contracts` a single-target generator, and resolve audit C-01 (BullMQ)
outright.

Rejected because BGE-M3 and HDBSCAN have no equivalent in the Node ecosystem.
A TypeScript backend would need a Python sidecar for ML anyway — which is
precisely the split ADR-004 has to decide, arrived at from the opposite
direction. Python for the analytical core is not a stylistic choice.

### Alternative D — Go for services, Python only for ML

Plausible: excellent concurrency, small containers, fast startup, strong for a
gateway and worker tier.

Rejected: a third language for a one-person team at foundation stage. The
concurrency advantage does not apply to a workload dominated by waiting on
external I/O, which async Python already handles adequately.

## Pros

- **Pydantic makes the provenance requirement structural.** An evidence object
  with a missing source or timestamp fails validation at the boundary rather than
  producing a plausible-looking score three stages later. This is the single
  strongest argument for the choice, and it maps directly onto
  `evidence-confidence-framework-v1.md` §10 and the audit A-10 recommendation to
  make provenance fields non-nullable by default.
- **Pydantic is also the LLM structured-output layer.** `llm-reasoning-rules.md`
  §5 requires structured objects rather than unconstrained prose. The same model
  class that validates an HTTP boundary validates an LLM response — one schema,
  two enforcement points, no drift.
- **Native access to the ML ecosystem**: BGE-M3, HDBSCAN, scikit-learn, pandas,
  the NLP tooling. No bridge, no serialization boundary in the hot path.
- **Async by default**, which suits concurrent source collection and concurrent
  LLM calls.
- **OpenAPI generated from the code**, which keeps the `gateway` contract and the
  frontend types honest — and makes contract drift detectable in CI rather than
  in production.
- **Dependency injection** that makes I/O injectable, which is what allows every
  context to be tested with no network (`services/README.md` rule 6).
- **Low ceremony.** A small team can add a context without a large amount of
  framework scaffolding.

## Cons

Concretely:

- **Polyglot repository.** Two toolchains, two dependency managers, two lint
  stacks, two test runners, two CI paths. `packages/contracts` must generate for
  both targets, and the generator becomes load-bearing infrastructure. This is
  the largest ongoing cost of the decision.
- **Turborepo does not natively understand Python** (ADR-001). Python tasks are
  wrapped in `package.json` scripts and cached coarsely.
- **Python performance.** For CPU-bound work this is slower than the
  alternatives. Largely irrelevant here — the workload is I/O-bound and the ML
  libraries drop into native code — but it will show up in bulk data
  transformation if that is ever written in pure Python.
- **Async correctness is easy to get wrong.** A synchronous library call inside
  an async handler silently blocks the event loop, and the symptom (unexplained
  latency under load) is far from the cause. This needs an explicit lint rule and
  a review habit, not good intentions.
- **FastAPI's DI is request-scoped**, which fits HTTP well and job execution
  poorly. Worker code will need its own composition root rather than reusing the
  route dependencies.
- **Dependency weight.** The `nlp` service image will be large (model
  dependencies, torch). Build and deploy times suffer; see
  `infrastructure/docker`.
- **Runtime typing only.** `mypy --strict` in CI is not optional — without it,
  Pydantic validates the edges while the interior stays effectively untyped, and
  the guarantee this decision was made for stops at the boundary.

## Future impact

**Becomes easy:** adding an analytical context; enforcing structured LLM outputs;
keeping API documentation accurate; testing domain logic without a network;
integrating any Python ML library that appears later.

**Becomes hard:** eliminating the polyglot cost; sharing runtime code with the
frontend (only schemas are shared, never logic); keeping container images small;
onboarding contributors who know only one of the two languages.

**Revisit if:** the ML dependencies stop being Python-exclusive (unlikely); or
the operational cost of two toolchains exceeds the value of native ML access
(also unlikely, since that value is structural).

**Cost of reversal:** high, and it grows. Rewriting the analytical contexts in
another language means reimplementing embedding, clustering and scoring on a
different ecosystem, then revalidating the outputs against the old ones. This is
effectively a permanent decision, which is why the alternatives are recorded in
detail.

## Compliance with authoritative specifications

- `PROJECT_MANIFEST.md` §Technology Stack — locked choice. Satisfied.
- `PROJECT_MANIFEST.md` §Testability — DI makes I/O injectable; every context is
  testable without a network. Satisfied.
- `evidence-confidence-framework-v1.md` §6, §10 — Pydantic models enforce the
  evidence shape and provenance fields at every boundary. Satisfied, and this is
  the primary reason the decision is a good one independent of it being locked.
- `llm-reasoning-rules.md` §5 — structured outputs enforced by the same models.
  Satisfied.
- `llm-reasoning-rules.md` §7 — external content is untrusted. Scraped content is
  validated as data and never placed where it can be read as an instruction;
  structured-output validation failure is treated as a possible injection attempt.
- `docs/CLAUDE.md` §Definition of done — OpenAPI generation keeps contracts
  current by construction rather than by discipline.
- **Dependency recorded:** this ADR constrains ADR-004. The Python-only ML stack
  is precisely what makes the BullMQ contradiction (audit C-01) unavoidable
  rather than a matter of taste.
