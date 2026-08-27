# `packages/observability` — Logging and tracing conventions (planned)

**Status:** not implemented.
**Blocked on:** D-11 — no observability stack has been chosen. The *conventions*
below are fixed regardless of which stack is picked.

## Responsibility

Shared conventions and helpers for structured logging, tracing and metrics, so
that every service emits telemetry the same way.

## Why this is a package and not a per-service concern

`docs/CLAUDE.md` §Definition of done requires that "observability is adequate"
before a task is complete. In a pipeline where a single opportunity score depends
on dozens of collection, extraction and scoring steps across several contexts,
"adequate" has one specific meaning: **you can reconstruct why a given score came
out the way it did, from logs alone, without a debugger.** Concretely: given any
score, the logs must name the `ResearchSession` that produced it
(Ontology V2 §12.1).

That requires a correlation id that survives every hop — HTTP, queue, and back.
A correlation scheme that each service invents independently does not survive
hops. Hence one package.

## Conventions it will own

**Correlation.** Every log line carries `workspace_id`, `research_session_id`,
`opportunity_id` and `correlation_id` where applicable. Generated at the gateway,
propagated through HTTP headers and Celery task payloads. `workspace_id` is
mandatory on every tenant-scoped operation (ADR-005).

`research_session_id` is the canonical name (Ontology V2 §11.5). Accepted ADRs
written before V2 call this field `run_id`; they are append-only, so the mapping
is stated rather than retrofitted.

**Structured logs.** JSON. No string interpolation of variable data into the
message field — the message is a stable key, the data is fields.

**Never logged.** Credentials, API keys, full raw scraped content (volume and
licensing), personal data (`data-principles.md` §8). Note that observability is a
tenant-leak path in its own right: another workspace's content appearing in an
error trace leaks it just as effectively as a missing SQL filter (ADR-005).

**Cost telemetry.** LLM calls, tokens and estimated cost are metrics, per run and
per job type. `PROJECT_MANIFEST.md` makes cost awareness an engineering
principle; a principle without a meter is a preference.

**Standard metrics per service:** request/job rate, error rate, latency
distribution, queue depth **and age**, external-source quota consumption, LLM
spend.

Queue *age* matters more than depth (ADR-004): a queue of 10 jobs that has not
moved in an hour is a worse signal than a queue of 10,000 moving steadily.

**LLM Gateway metrics** (ADR-006): provider, model, tier, tokens, estimated and
actual cost, retries, fallbacks, and **cost-ladder compliance** — what fraction
of work reached an LLM at all. That last one is the economic health metric of the
whole system; `llm-reasoning-rules.md` §8 says most volume should never reach an
LLM, and without a meter that is an intention rather than a property.

**Standard events:** ResearchSession started/completed/failed, source unavailable,
contract violation, dead-letter entry created, budget exhausted, provider circuit
opened, low-confidence conclusion flagged for human review
(`llm-reasoning-rules.md` §11).
