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

**Sprint 1 — Mission 1.15.6 complete: reviewed route binding, and
configuration-verified conditions.** Sprint 0 closed at Mission 0.4.

The pipeline runs end to end on real data, for two sources, at small volume:
raw record → normalized record → signal → claim → evidence. Everything past that
point is still blocked, deliberately: no reliability assessments, no scoring, no
opportunities, no embeddings, no dashboards, no authentication, no monetization
(`PROJECT_MANIFEST.md` §Forbidden During Foundation).

### What Sprint 1 built

- **A source registry that is a governance record, not a configuration file.**
  Twenty-nine sources, forty-two evidence records, every review versioned and
  append-only, every superseded review preserved. Three Mission 1.7 approvals
  were **withdrawn** on audit in Mission 1.8 because each rested on the absence
  of a prohibition rather than on a grant; *silence is not permission* stopped
  being prose and became `validate_source_registry`.
- **Two collectors, and only two.** World Bank (Mission 1.5) and GDELT WEB-NGRAM
  (Mission 1.9.3). Eurostat is collector-eligible and deliberately has no
  collector: eligible, enabled, implemented and normalizable are four separate
  facts, and none implies the next.
- **Raw → Normalized (Mission 1.6).** Every canonical observation carries
  complete lineage, its attribution obligation, a governance-resolved expiry and
  a structural quality state.
- **Signals (Missions 1.11–1.12.1).** Deterministic extractors only, each with a
  run log, and a signal is a *derivation*: at least two distinct source
  observations must contribute (ADR-020). Mission 1.12 closed H-32 and granted
  GDELT `SOURCE_RELATIVE_ORDER`, which is what made the sequential lexical
  frequency change extractor possible in 1.12.1. H-29 still withholds
  `COMPARABLE_INSTANT`.
- **Signal → Claim → Evidence (Missions 1.13–1.13.1)**, deterministic `OBSERVED`
  claims, followed by **evidence reliability governance (Mission 1.14)**, which
  scoring cannot proceed without.
- **A verdict has a subject (Mission 1.15.5, ADR-027).** Every review had always
  answered a question about a specific *use*, in a required `assessed_use_case`
  field — but that answer had no identity, so it could not be required, compared
  or matched, and the gate never saw it. `AssessedUseProfile` gives it one. Two
  profiles are registered, `commercial-multi-tenant-research-v1` and
  `local-private-research-v1`; fifty-five historical reviews were migrated to
  the first with the verdict distribution asserted unchanged. The profile is now
  a **required positional argument** on `evaluate_eligibility`,
  `build_authorization` and `verify_source`, with no default and no fallback of
  any kind. `SROS_USE_PROFILE` declares it at the entry point and is never
  inferred from an environment name, a host or a container.
- **The route is a fact about us, not about the source (Mission 1.15.6,
  ADR-028).** An authorization carried *every* access profile the registry
  recorded, because an access profile says how a source **can** be reached and
  the context had nothing to filter it with. TED is the first approving source
  whose review refuses one of its own real routes by name — the bulk packages,
  which are genuinely published and genuinely downloadable — so its context
  would have handed a collector the refused route with its endpoint, and the
  transport's host allowlist is derived from that. A `(source, profile)` may now
  declare a **route authorization**, and the context carries those routes and no
  others: a blocked route has no endpoint to reach.

The concrete result: `ted-eu` holds two current verdicts at once,
`REQUIRES_REVIEW` under the commercial profile and `APPROVED_WITH_CONDITIONS`
under the local one, both true. Deploying this system publicly can no longer
inherit a permission granted for a laptop.

And the same mission answered the question that had been left to a person.
Two of TED's conditions described what a collector would do — which route it
binds to, which fields it requests — and were `HUMAN_CONFIRMATION` because a
catalog cannot assert what code does. That produced a **bootstrap**: nothing
could be authorised until somebody confirmed behaviour, and nobody could confirm
behaviour until the collector existed. Neither was ever about code. Both are
properties of the **configuration** authorization is handed, both are now checked
against it, and TED went from three outstanding human confirmations to **one**.

**The one that remains is a judgement, and it stays one.** A residual-risk
acceptance that code could satisfy would be a judgement nobody made.

### What is blocked, and by what

- **TED-EU, on one human decision.** H-36A (whether a sui generis database
  right subsists) is NOT ESTABLISHED and H-36B (whether the right holder grants
  the extraction the engine needs) is NOT ADDRESSED, under **both** profiles. A
  profile changes the exposure and the acts performed; it does not change the
  law.

  ```text
  build_authorization('ted-eu', 'local-private-research-v1')
    review conditions not satisfied:
      ted-database-right-residual-exposure-accepted
  ```

  Nothing in this repository can satisfy that condition, and nothing ever will:
  a `HUMAN_CONFIRMATION` reaches the human branch before any configuration is
  consulted, and the database refuses a hand-set boolean with no verification
  behind it. The exact statement an operator would have to record is written
  down in
  [`ted-eu-authorization-bootstrap-v1.md`](docs/data/ted-eu-authorization-bootstrap-v1.md)
  §6.2 — and **writing it down is not signing it**.
- **GDELT.** H-29 and H-30 are open. Every GDELT normalized record is `PARTIAL`
  in consequence, stated per record rather than smoothed away: H-29 withholds a
  comparable global instant, and H-30 leaves `content_language` `NULL` because
  mapping the payload's CLD2 language *name* to a canonical tag is not
  established.
- **Scoring.** Reliability assessments are 0. Nothing downstream of evidence has
  been implemented.

### Counts

**There is no number to put here, and that is the honest answer.**

The mission reports state 12 raw records, 12 normalized records, 7 signals,
7 claims, 7 claim revisions and 7 evidence rows. Those figures are true of the
database those missions ran in. **They are not a property of this repository**,
they are not asserted by any test, and a clone that has never run a collector
holds none of them — which is exactly what
[§Research data does not travel either](#research-data-does-not-travel-either)
says and why that section exists.

What *is* fixed, checked and reproducible anywhere: **0 reliability assessments,
0 opportunities, 0 embeddings, 0 scores, 0 TED rows.** Those are zero because
nothing may produce them yet, not because nobody has run anything.

Whether a source may be collected from at all — eligible, resource-ready,
implemented, enabled — is derived rather than stored, and this is the current
answer on your machine:

```bash
uv run sros-source readiness
```

It reports the legacy profile by default and takes `--use-profile`, because a
verdict without its profile is a naked verdict.

### What runs today

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
uv run sros-source load
```

```bash
uv run python infrastructure/scripts/validate_source_registry.py
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
boundaries, the diagrams, **twenty-eight ADRs**, the repository standards, the
quality gates, **Opportunity Ontology V2.2**, Scoring Framework V1.1, the
evidence confidence and aggregation frameworks, the claim model, the source
registry and acquisition authorization contracts, the signal and claim
interpretation contracts, the evidence reliability contract, the data retention
policy and the evaluation framework.

Start with
[`docs/architecture/mission-1.15.6-report.md`](docs/architecture/mission-1.15.6-report.md)
and the decision registers
[`mission-0.1.2-decisions.md`](docs/architecture/mission-0.1.2-decisions.md) /
[`mission-0.1.1-decisions.md`](docs/architecture/mission-0.1.1-decisions.md).
Earlier mission reports remain as historical records.

---

## After every pull

**`git pull` alone is never enough.** Five things this project needs do not
travel through git, and all five are silent when they are stale: the code runs,
and it runs against the wrong environment.

| Not in git | Where it actually lives | Symptom when stale |
|------------|-------------------------|--------------------|
| Python dependencies | `.venv/`, not versioned | `ModuleNotFoundError` on a package that exists in the tree |
| Node dependencies | `node_modules/`, not versioned | `Cannot find module 'next'`, and `tsc` reporting a hundred JSX errors |
| Applied migrations | the local PostgreSQL | a migration file that exists but was applied nowhere |
| `registry.*` contents | loaded from the catalog JSON, not by git | the previous catalog: missing use profiles, missing reviews |
| `infrastructure/compose/.env` | git-ignored (`.gitignore:6`) | a key with no default refuses the command outright |

One script does all five, stopping at the first thing it cannot fix and naming
the fix:

```bash
git checkout main && git pull
```

```bash
python infrastructure/scripts/sync.py --verify
```

It never runs git, so pull first. Drop `--verify` to skip the suites, or pass
`--check` to see what it would change. The rest of this section is what it does,
step by step, for when one of them fails.

---

**1. Take the code and both sets of dependencies.** The Node half is the one
that gets skipped, because the Python side goes green without it and the failure
then looks like a broken TypeScript configuration rather than a missing install.

```bash
git checkout main && git pull
```

```bash
uv sync --all-packages --frozen
```

```bash
pnpm install --frozen-lockfile
```

**2. Start the backing services.**

```bash
docker compose -f infrastructure/compose/docker-compose.yml up -d
```

**3. Reconcile `.env` against the template, before running anything that reads
it.** `.env.example` is committed and gains keys as missions add them; your
`.env` is not and does not. This prints every key the template has and yours
lacks:

```bash
comm -23 <(grep -oE '^[A-Z_0-9]+=' infrastructure/compose/.env.example | sort -u) <(grep -oE '^[A-Z_0-9]+=' infrastructure/compose/.env | sort -u)
```

Add each one with the template's value. `SROS_USE_PROFILE` is the one that stops
the day: it has **deliberately no default**, so every acquisition command
refuses to run until the deployment declares which use profile it operates
under. On a developer machine that is:

```bash
echo "SROS_USE_PROFILE=local-private-research-v1" >> infrastructure/compose/.env
```

**4. Fold `.env` into the shell.** `migrate.py` and `run_pytest_suites.py` read
`os.environ`; they do not read the file for you, and without this step the next
command exits with `DATABASE_URL is not set` while the value sits in the file:

```bash
set -a && source infrastructure/compose/.env && set +a
```

The CLI is the exception. `sros-source` folds the file in itself and names it on
stderr. The acquisition suite does the same, deliberately, so a verification
means the same thing whether the CLI or `pytest` recorded it
(`services/acquisition/python/tests/conftest.py`).

**5. Bring the database and the registry up to the tree.**

```bash
uv run python infrastructure/scripts/migrate.py --apply
```

```bash
uv run sros-source load
```

**6. Verify, in one command.**

```bash
uv run python infrastructure/scripts/run_pytest_suites.py
```

It ends with `all pytest suites passed across 7 packages`, plus the two leak
checks that assert the run left the tenant tables and the `registry.*` tables as
it found them. That covers the Python half; `sync.py --verify` follows it with
`tsc`, `eslint` and the two Node test files, which are what a skipped
`pnpm install` breaks.

### Research data does not travel either

The catalog is governance data, and `sros-source load` reproduces it exactly on
any machine. Collected research is not: raw records, normalized records,
signals, claims and evidence live in whichever local PostgreSQL produced them.
A second machine has whatever its own database holds, usually nothing.

That is harmless for governance work, which only touches the registry. It
matters the day a report states counts: **those numbers describe one database,
not the repository.** Reproducing them elsewhere means re-running collection,
normalization, derivation and interpretation there.

### The one thing that travels by neither, and what to do about it

A **human decision** is regenerable by nothing. `registry.source_condition_verifications`
holds the operator's acceptance of the residual TED database-right exposure, and
on a second machine that row does not exist, so `ted-eu` is not eligible there.

There is deliberately **no `decide` verb** (Mission 1.15.6): a decision that is
routine to record is not a decision. What there is, for this one already-made and
already documented acceptance, is a replay with no parameters (ADR-030):

```bash
python infrastructure/scripts/record_ted_operator_acceptance.py
```

It prints the acknowledgement in full and writes nothing. Re-run it with
`--apply` and it asks you to type a confirmation before recording one row. It
refuses if the condition is missing, if this deployment carries a different
review version, if the condition is not `HUMAN_CONFIRMATION`, or if the row is
already there.

**This is once per machine, not once per pull.** `sync.py` covers every pull.

---

## Read this before contributing

`PROJECT_MANIFEST.md` §Authoritative Documents lists seven documents that define
the project. Read them in order:

1. [`PROJECT_MANIFEST.md`](PROJECT_MANIFEST.md)
2. [`docs/CLAUDE.md`](docs/CLAUDE.md)
3. [`docs/domain/opportunity-ontology-v2.2.md`](docs/domain/opportunity-ontology-v2.2.md)
4. [`docs/domain/scoring-framework-v1.1.md`](docs/domain/scoring-framework-v1.1.md)
5. [`docs/domain/evidence-confidence-framework-v1.md`](docs/domain/evidence-confidence-framework-v1.md)
6. [`docs/ai/llm-reasoning-rules.md`](docs/ai/llm-reasoning-rules.md)
7. [`docs/data/data-principles.md`](docs/data/data-principles.md)

Also authoritative, in the order the manifest added them:

- [`docs/data/data-retention-policy-v1.md`](docs/data/data-retention-policy-v1.md)
- [`docs/ai/evaluation-framework-v1.md`](docs/ai/evaluation-framework-v1.md)
- [`docs/data/source-registry-v1.md`](docs/data/source-registry-v1.md)
- [`docs/domain/evidence-aggregation-framework-v1.md`](docs/domain/evidence-aggregation-framework-v1.md)
- [`docs/domain/claim-model-v1.md`](docs/domain/claim-model-v1.md)
- [`docs/data/acquisition-authorization-v1.md`](docs/data/acquisition-authorization-v1.md)
- [`docs/data/world-bank-collector-v1.md`](docs/data/world-bank-collector-v1.md)
- [`docs/data/normalized-record-v1.md`](docs/data/normalized-record-v1.md)
- [`docs/data/world-bank-normalizer-v1.md`](docs/data/world-bank-normalizer-v1.md)
- the accepted ADRs in [`docs/architecture/adr/`](docs/architecture/adr/)

`docs/CLAUDE.md` §Boot Sequence lists a longer reading order — twenty-three
entries — that adds the signal, claim-interpretation and evidence-reliability
contracts. It is the one to follow before touching the acquisition or NLP
services.

Superseded, retained as historical records only: `opportunity-ontology-v1.md`,
`opportunity-ontology-v1.1.md`, `opportunity-ontology-v2.md`,
`opportunity-ontology-v2.1.md`, `scoring-framework-v1.md`.

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

**The deployment model is local-first and single-operator**, recorded in
`PROJECT_MANIFEST.md` 1.28 by operator directive. Local deployment does **not**
imply non-commercial use: the research this system produces is used to launch
commercial products, so the deployment is local and the purpose is commercial,
and commercial-use rights are still reviewed wherever they apply. Public
redistribution and customer-facing rights are out of scope unless the deployment
model changes — and if it ever does, the commercial profile must be reviewed
again from the top rather than reached by drift. Workspace tenancy and row-level
security are kept regardless (ADR-005, ADR-012): one operator today is not a
reason to remove a boundary that is far more expensive to re-add.

---

## Setup

Requires **Node 22.11+** (native TypeScript type stripping), **Python 3.12+**
and **Docker**.

```bash
uv sync --all-packages --frozen
```

```bash
pnpm install --frozen-lockfile
```

```bash
cp infrastructure/compose/.env.example infrastructure/compose/.env
```

```bash
docker compose -f infrastructure/compose/docker-compose.yml up -d
```

```bash
set -a && source infrastructure/compose/.env && set +a
```

```bash
uv run python infrastructure/scripts/migrate.py --apply --seed
```

```bash
uv run sros-source load
```

The last step is the one a fresh clone most easily forgets. The `registry.*`
tables are loaded from the catalog JSON, not by git, so without it the database
has no sources, no reviews and no use profiles while the tree looks complete.

`.env.example` carries `SROS_USE_PROFILE=local-private-research-v1`. It has
**deliberately no default in code**, so every acquisition command refuses to run
until the deployment declares which use profile it operates under (ADR-027).

The contract, schema and test commands above need **no install at all**: they
run on stdlib Python and a bare Node runtime, deliberately (ADR-009).

`pnpm install` **is** required for anything touching `apps/web`, which is now a
real Next.js application with a typed API client and its own tests. Skipping it
fails in a misleading way: the Python side still goes green, and `tsc` reports a
hundred JSX errors that look like a broken TypeScript configuration.

For an existing clone, prefer [§After every pull](#after-every-pull) over these
steps — `git pull` alone leaves the dependencies, the migrations and the
registry stale, all three silently.

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
