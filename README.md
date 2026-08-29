# Startup Research OS

An evidence-driven AI Opportunity Research Engine.

It discovers, analyzes, scores, validates and plans digital product opportunities
across B2B, B2C, gaming, entertainment, education, AI, creator, developer,
social, utility, marketplace and hobby markets.

**It is not a startup idea generator.** The difference is that every conclusion
carries the evidence that produced it, the confidence attached to it, and a label
saying whether it was observed, inferred, predicted, recommended, or is merely a
hypothesis.

---

## Status

**Sprint 0 — Mission 0.4 complete: row-level security, orchestration, LLM
provider adapters, evaluation framework, web API foundation.**

No business research logic exists: no collectors, no NLP, no scoring, no
dashboards, no authentication, no monetization. That is deliberate
(`PROJECT_MANIFEST.md` §Forbidden During Foundation).

Mission 0.4 added the layers that have to exist *before* research logic can:

- **Two isolation layers.** The repository tenant filter, plus PostgreSQL
  row-level security on all 15 tenant-scoped tables with a transaction-local
  tenant context (ADR-012). A query that forgets its `WHERE workspace_id`
  returns only the current tenant's rows.
- **The research orchestrator as a real package** — session lifecycle, planning,
  a job ledger, dependency ordering, budget accounting, cancellation and
  resumability. It dispatches nothing, because every domain capability is
  blocked, and it says which decision blocks each one.
- **Anthropic and Gemini behind the gateway**, with a normalized error taxonomy,
  a retry policy that refuses to retry deterministic failures, versioned pricing
  configuration and cost telemetry. **No vendor SDK is a dependency, and no test
  needs an API key.**
- **An evaluation framework** with versioned datasets, per-task metrics and
  regression comparison in which cost can never offset quality.
- **A typed web API client** with correlation on every request and one place
  that builds headers.

What runs today:

```bash
python packages/contracts/tools/generate.py --check
```

```bash
python infrastructure/scripts/validate_schema.py
```

```bash
python infrastructure/scripts/run_python_tests.py
```

```bash
node --test --experimental-strip-types packages/contracts/test/conformance.test.ts
```

```bash
docker compose -f infrastructure/compose/docker-compose.yml up -d
```

```bash
uv run python infrastructure/scripts/migrate.py --apply --seed
```

```bash
uv run uvicorn "sros_gateway.app:create_app" --factory --port 8412
```

```bash
uv run python infrastructure/scripts/run_pytest_suites.py
```

```bash
pnpm --filter @sros/web build
```

What exists: the specification audit, the monorepo skeleton, the service
boundaries, the diagrams, **twelve ADRs**, the repository standards, the quality
gates, **Opportunity Ontology V2**, Scoring Framework V1.1, the data retention
policy and the **evaluation framework**.

Start with
[`docs/architecture/mission-0.4-report.md`](docs/architecture/mission-0.4-report.md)
and the decision registers
[`mission-0.1.2-decisions.md`](docs/architecture/mission-0.1.2-decisions.md) /
[`mission-0.1.1-decisions.md`](docs/architecture/mission-0.1.1-decisions.md).
Earlier mission reports remain as historical records.

---

## Read this before contributing

`PROJECT_MANIFEST.md` §Authoritative Documents lists seven documents that define
the project. Read them in order:

1. [`PROJECT_MANIFEST.md`](PROJECT_MANIFEST.md)
2. [`docs/CLAUDE.md`](docs/CLAUDE.md)
3. [`docs/domain/opportunity-ontology-v2.md`](docs/domain/opportunity-ontology-v2.md)
4. [`docs/domain/scoring-framework-v1.1.md`](docs/domain/scoring-framework-v1.1.md)
5. [`docs/domain/evidence-confidence-framework-v1.md`](docs/domain/evidence-confidence-framework-v1.md)
6. [`docs/ai/llm-reasoning-rules.md`](docs/ai/llm-reasoning-rules.md)
7. [`docs/data/data-principles.md`](docs/data/data-principles.md)

Also authoritative:
[`docs/data/data-retention-policy-v1.md`](docs/data/data-retention-policy-v1.md)
and [`docs/ai/evaluation-framework-v1.md`](docs/ai/evaluation-framework-v1.md)
and the accepted ADRs.

Superseded, retained as historical records only: `opportunity-ontology-v1.md`,
`opportunity-ontology-v1.1.md`, `scoring-framework-v1.md`.

Then [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Repository layout

```
apps/              user-facing applications (Next.js console)
services/          nine bounded contexts
packages/          shared libraries — contracts, ui, configs, observability
infrastructure/    Docker, compose, operational scripts
docs/              specifications (authoritative) + architecture (derived)
.github/           CI placeholders, PR template
```

Every directory has a README describing its responsibility.

---

## Architecture in one paragraph

Nine bounded contexts, all Python, deployed initially as four processes.
`gateway` is the only public entry point. `research-orchestrator` owns the
lifecycle of a `ResearchSession` and enqueues work; `workers` executes it on
Celery.
`acquisition` collects raw data with full provenance and interprets nothing.
`nlp` turns text into structured signals. `scoring` computes five separate score
families that are never collapsed into one number. `market-intelligence`,
`competition` and `execution` analyze and plan. Every tenant-scoped resource
carries `workspace_id`. All LLM access goes through a provider-agnostic gateway.
PostgreSQL is the system of record; Redis is the Celery broker and cache; Qdrant
is a derived, rebuildable vector index.

See [`docs/architecture/service-boundaries.md`](docs/architecture/service-boundaries.md)
and the [diagrams](docs/architecture/diagrams/).

---

## Stack

| Layer | Choice | ADR |
|-------|--------|-----|
| Monorepo | Turborepo + pnpm | [ADR-001](docs/architecture/adr/ADR-001-turborepo-monorepo.md) |
| Frontend | Next.js 15, TypeScript, Tailwind, shadcn/ui | [ADR-002](docs/architecture/adr/ADR-002-nextjs-frontend.md) |
| Backend | FastAPI, Python | [ADR-003](docs/architecture/adr/ADR-003-fastapi-backend.md) |
| Jobs | Celery over Redis | [ADR-004](docs/architecture/adr/ADR-004-celery-redis-job-architecture.md) |
| Tenancy | Workspace-scoped multi-tenant | [ADR-005](docs/architecture/adr/ADR-005-workspace-multi-tenancy.md) |
| LLM access | Provider-agnostic gateway | [ADR-006](docs/architecture/adr/ADR-006-provider-agnostic-llm-gateway.md) |
| Deployment | Local-first, Docker Compose | [ADR-007](docs/architecture/adr/ADR-007-local-first-docker-compose-deployment.md) |
| Storage | PostgreSQL, Redis, Qdrant | [ADR-008](docs/architecture/adr/ADR-008-storage-architecture.md) |
| DB access | psycopg 3 + explicit repositories | [ADR-011](docs/architecture/adr/ADR-011-postgresql-access-psycopg.md) |
| Python deps | uv workspace | [ADR-010](docs/architecture/adr/ADR-010-python-dependency-management.md) |
| Contracts | JSON source of truth, generated TS + Python | [ADR-009](docs/architecture/adr/ADR-009-contract-first-code-generation.md) |
| Automation | Playwright (Python API) | — |
| ML | BGE-M3, HDBSCAN | — |

BullMQ was removed from the stack in Mission 0.1.1. It is Node-only and could not
be consumed by the Python workers the ML stack requires (ADR-004).

---

## Setup

Requires **Node 22.11+** (native TypeScript type stripping), **Python 3.12+**
and **Docker**.

```bash
cp infrastructure/compose/.env.example infrastructure/compose/.env
```

```bash
docker compose -f infrastructure/compose/docker-compose.yml up -d
```

```bash
python infrastructure/scripts/migrate.py --apply --seed
```

The contract, schema and test commands above need **no install at all**: they
run on stdlib Python and a bare Node runtime, deliberately (ADR-009).

`pnpm install` is not required yet — no TypeScript application exists.

---

## The four principles that shape every decision here

1. **Evidence before conclusions.** A claim without evidence is labeled a
   hypothesis, or it is omitted.
2. **Explainability.** Every score can be traced to the evidence and the versions
   that produced it.
3. **No fabrication.** Never invent a source, metric, price, market size,
   competitor fact or citation. Not in code, not in a fixture, not in a plan.
4. **Cost awareness.** Use the cheapest reliable method. Rules before models,
   models before LLMs — and the LLM Gateway measures whether that actually holds.

## Canonical invariants

Settled in Mission 0.1.1. Do not redefine these locally:

```text
ClaimType   = OBSERVED | INFERRED | PREDICTED | RECOMMENDED | HYPOTHESIS
MarketScope = GLOBAL | REGION | COUNTRY | MULTI_COUNTRY
confidence  ∈ [0.0, 1.0]         presented as a percentage
scores      ∈ 0–100              presented as integers
tenancy       workspace_id on every primary domain resource
lifecycle     Workspace → ResearchProject → ResearchSession
taxonomies    registries, not database enums (except the closed set)
```
