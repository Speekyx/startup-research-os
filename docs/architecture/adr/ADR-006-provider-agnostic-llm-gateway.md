# ADR-006 — Provider-agnostic LLM Gateway

- **Status:** Accepted
- **Date:** 2026-08-27
- **Deciders:** Project owner (Mission 0.1.1, §10 — explicit human decision)
- **Supersedes:** none
- **Related:** ADR-003, ADR-004, audit **D-04**, `llm-reasoning-rules.md`
  (all sections), `PROJECT_MANIFEST.md` §Cost Awareness

---

## Context

Two contexts use LLMs heavily (`nlp` for extraction and classification,
`execution` for synthesis and planning), and more will. The audit recorded
**D-04** as blocking both: no provider, model tier or cost budget had been chosen.

Three forces shape the answer:

1. **Model churn is faster than release cycles.** Model names, versions,
   capabilities and prices change on a timescale of weeks. Any code that names a
   specific model in a business service is code that will be edited for reasons
   that have nothing to do with the business.
2. **Provider risk is real.** Outages, rate limits, deprecations, regional
   availability and pricing changes all originate outside this system. A hard
   dependency on one SDK converts each of those into an outage of the research
   engine.
3. **`llm-reasoning-rules.md` imposes obligations that are per-call, not
   per-provider** — reproducibility metadata (§9), structured outputs (§5), the
   cost ladder (§8), injection handling (§7), evaluation (§10). Implementing them
   once at a chokepoint is the only way they hold everywhere; implementing them
   per call site means they hold until someone is in a hurry.

## Decision

**All LLM access goes through a single internal LLM Gateway. No business service
depends on a provider-specific SDK.**

```text
Application services  (nlp, execution, future AI contexts)
        ↓            logical tier + task, never a model name
    LLM Gateway
        ↓
 ┌──────┬──────┬──────┬────────────┬───────────────┐
Anthropic Gemini OpenAI OpenRouter  Local providers
```

Services request a **logical tier**, never a provider or a model:

```text
FAST_MODEL        high-volume, cheap, low-latency, simple tasks
BALANCED_MODEL    default reasoning for most analytical work
STRONG_MODEL      complex synthesis, planning, hard judgment
EMBEDDING_MODEL   vector embeddings
```

### Initial intended strategy

- Primary high-quality reasoning: **Claude**
- Cheap / high-volume and secondary provider: **Gemini**
- Embeddings: **local BGE-M3**
- OpenAI, OpenRouter and future local providers remain pluggable

**No model name is hard-coded.** The tier → provider → model mapping lives in
configuration (environment plus a versioned configuration contract), so changing
a model is a configuration change and a version record, never a code change.

`EMBEDDING_MODEL` defaulting to local BGE-M3 is deliberate: embeddings are the
highest-volume LLM-adjacent operation in the system, and running them locally
removes both the dominant recurring cost and a network dependency from the hot
path.

**This ADR does not implement the gateway.** It fixes the contract.

## Provider abstraction

The gateway exposes a narrow, provider-neutral interface:

- **complete** — a structured request with a response schema
- **embed** — text to vectors
- **stream** — where a caller genuinely needs incremental output

The request carries: logical tier, task identifier, prompt template id and
version, input variables, response schema, budget context (`workspace_id`,
`run_id`), and timeout. It **never** carries a provider, a model name, or a
provider-specific parameter.

The response carries: the validated structured output, plus the full
reproducibility record (below), plus cost and latency.

### What the abstraction deliberately does not expose

Provider-specific features that cannot be expressed across providers are not
surfaced. A leaky abstraction that passes through vendor-specific parameters
recreates the coupling it exists to prevent — the second service that uses such a
parameter has silently pinned the whole system to that provider.

Where a capability is genuinely required and not universal, it is modeled as an
explicit **capability requirement** on the request, and the router selects a
provider that satisfies it. The caller states what it needs, not who provides it.

## Routing

Resolution order for a request:

1. Logical tier → the candidate provider/model list for that tier, from
   configuration.
2. Filter by declared capability requirements (structured output, context window,
   modality).
3. Filter by health: providers in an open circuit-breaker state are skipped.
4. Select by configured preference (cost, latency, or quality weighting per tier).

Routing configuration is **versioned**, and the resolved routing version is
recorded with every response. Without that, a routing change silently alters
historical comparability and nothing records why results shifted.

## Fallbacks

Fallback is permitted **only where it is semantically safe**, and that is a
per-task property, not a global setting.

| Situation | Behavior |
|-----------|----------|
| Provider timeout or 5xx | Retry once on the same provider, then fall back to the next candidate in the tier |
| Rate limited | Backoff with jitter; fall back if the budget for waiting is exhausted |
| Provider outage (circuit open) | Route to the next candidate immediately |
| Structured-output validation failure | Retry once with the same provider; **never** silently fall back — a schema failure may indicate prompt injection (`llm-reasoning-rules.md` §7) and must be logged as such |
| All candidates exhausted | **Fail the job.** Never degrade to an unvalidated response, never fabricate |

Two hard rules:

1. **A fallback changes the model, so it changes the result.** The response
   records which provider actually served it. Comparing outputs across a silent
   fallback is comparing two different models, and evaluation data that does not
   record this is worthless.
2. **Never fall back for evaluation runs.** Benchmarks pin a provider and model
   explicitly, or they measure nothing.

## Timeouts

- Every request carries an explicit timeout. There is no unbounded LLM call.
- Timeouts are set per tier: `FAST_MODEL` short, `STRONG_MODEL` longer.
- The timeout budget is bounded by the enclosing Celery job timeout (ADR-004),
  which is itself bounded by the research run budget. A request cannot outlive
  its job; a job cannot outlive its run.

## Retries

- Retries are **budget-aware**: a retry consumes cost budget and is accounted for.
- Exponential backoff with jitter. Synchronized retries across workers are how a
  rate limit becomes a ban (ADR-004).
- **Only retry what is retryable.** A refusal, a context-length error, or a
  malformed prompt is deterministic — retrying burns money and hides the bug.
- Retry count is bounded per job and per run.

## Budget enforcement

The gateway is the only place where money is spent, which makes it the only
place budget can be enforced honestly.

- **Per-request:** an estimated cost ceiling; requests projected to exceed it are
  rejected before dispatch.
- **Per-run:** each research run carries a cost budget
  (`research-orchestrator`). The gateway decrements it and **refuses** calls once
  it is exhausted. The run then completes with lower Research Completeness rather
  than overspending — an explicitly incomplete result is a valid outcome, an
  unbounded invoice is not.
- **Per-workspace:** aggregate ceilings per tenant (ADR-005), for quota and
  eventual billing.
- **Refusal is a first-class result**, surfaced as an explicit
  budget-exhausted state. It is never silently swallowed and never replaced by a
  fabricated answer.

## Telemetry

Per call, recorded and emitted (`packages/observability`):

- provider, model, logical tier, routing version
- input and output tokens, estimated and actual cost
- latency, retry count, fallback occurrences
- `workspace_id`, `run_id`, `correlation_id`, task identifier
- outcome: success, schema failure, refusal, timeout, budget exhausted

Aggregated: cost per run, per workspace, per task type, per provider; error rate
and latency distribution per provider; **cost-ladder compliance** — what fraction
of work reached an LLM at all.

That last metric is the one that matters economically. `llm-reasoning-rules.md`
§8 says most volume should never reach an LLM; without a meter, that is an
intention rather than a property.

**Never logged:** API keys, full raw scraped content, personal data.

## Prompt versioning

- Every prompt is a **versioned template artifact** with an id and a version.
  Prompts are never assembled ad hoc at a call site.
- The template id and version are recorded with every response
  (`llm-reasoning-rules.md` §9).
- A prompt change is a version bump, reviewed like code — because it changes
  system behavior as much as code does.
- Untrusted content is interpolated only into designated **data regions** of a
  template, never into an instruction region (§7).

## Model version tracking

Every stored LLM-derived value records: provider, model identifier, model version
where the provider exposes one, prompt template id and version, parameters,
routing version, input evidence references, and timestamp.

This is what makes a model upgrade survivable. Without it, upgrading a model
silently invalidates every historical signal with no way to identify which ones —
and re-deriving them is impossible because nothing records how they were derived.

The same requirement applies to `EMBEDDING_MODEL`, where it additionally drives
the re-embedding strategy (decision **D-12**, still open).

## Provider outages

- **Circuit breaker per provider.** Consecutive failures open the circuit;
  routing skips it; a half-open probe closes it again.
- **Degraded mode** is explicit: if no provider in a tier is available, jobs
  requiring it fail and are dead-lettered (ADR-004), becoming research gaps that
  lower Research Completeness. The system reports reduced coverage; it does not
  invent output.
- **Never downgrade a tier silently.** Serving a `STRONG_MODEL` request from
  `FAST_MODEL` because the strong provider is down produces a worse answer that
  looks identical. If a tier downgrade is ever permitted for a task, it is
  declared on the request and recorded on the response.

## Future evaluation requirements

`llm-reasoning-rules.md` §10 requires explicit evaluation datasets. The gateway is
what makes this feasible:

- A recorded request/response corpus (with reproducibility metadata) is the raw
  material for evaluation sets.
- Because callers request a tier rather than a model, **the same task can be
  replayed across providers** to compare precision, recall, F1, calibration,
  consistency, cost and latency.
- Evaluation runs pin provider and model explicitly and disable fallback.
- A provider or model change should be justified by evaluation results, not by a
  release announcement. The gateway is what makes that comparison possible at all.

## Alternatives considered

### Alternative A — Direct provider SDK in each service

Simplest, no abstraction, full access to provider features. Rejected: it
scatters the cost ladder, reproducibility metadata, budget enforcement and
injection handling across every call site, where each is one hurried commit from
being skipped. It also makes provider substitution a refactor of the business
services.

### Alternative B — A third-party abstraction library (LiteLLM, LangChain, etc.)

Plausible: the provider-normalization work already exists and is maintained.

Rejected as the primary interface, though not forbidden as an *implementation
detail inside* the gateway. The reason is that this system's requirements are not
generic: budget enforcement tied to research runs, reproducibility fields
required by `llm-reasoning-rules.md` §9, structured-output validation treated as
a security signal, and cost-ladder telemetry. A general-purpose library provides
none of those, so the gateway would exist anyway — and building it on top of a
large abstraction adds a dependency with its own churn and its own opinions.

### Alternative C — Single provider, no abstraction

Cheapest to build. Rejected: it converts every provider outage, price change and
deprecation into a system outage or an emergency migration, and it makes
cross-provider evaluation impossible.

### Alternative D — OpenRouter as the only provider

Plausible: one API, many models, routing already solved. Rejected as the sole
path — it is a single point of failure and adds a margin on every call — but it
is retained as a **pluggable provider**, which is genuinely useful for reaching
models that are not worth a direct integration.

## Pros

- Provider substitution is configuration, not a refactor.
- The cost ladder, budget enforcement, reproducibility metadata, prompt
  versioning and injection handling are implemented **once**, at a chokepoint
  that cannot be bypassed.
- Cross-provider evaluation becomes possible, which is what §10 requires.
- Local providers (including local embeddings today) are a first-class case, not
  a special case.
- Cost is measurable per run, per workspace and per task type — turning "cost
  awareness" from a principle into a number.
- Model churn stops touching business code.

## Cons

- **An abstraction layer with a maintenance cost**, ahead of a proven need. The
  justification is the obligations above, not provider-switching in the abstract.
- **The narrowest-common-denominator risk.** Provider-specific capabilities are
  harder to exploit. Mitigated by capability requirements, but it is a real
  constraint and it will occasionally be annoying.
- **A single point of failure by construction.** A bug in the gateway affects
  every LLM call in the system.
- **Fallback makes results non-comparable** unless the provider is recorded —
  which is why recording it is mandatory rather than best practice.
- **Configuration surface grows:** tiers × providers × models × routing
  preferences, all versioned. Misconfiguration is a plausible failure mode.
- **Cost estimation is approximate** before a call completes, so per-request
  ceilings are a guard rather than a guarantee. Per-run budgets are the real
  control.

## Future impact

**Becomes easy:** adding or replacing a provider; changing a model; running
cross-provider evaluations; enforcing per-tenant budgets; auditing why a
conclusion was reached; migrating embeddings to a different model with a recorded
re-embedding path.

**Becomes hard:** using a provider's most exotic features; achieving the absolute
lowest latency (one extra hop); reasoning about behavior without consulting the
routing configuration.

**Revisit if:** a single provider becomes strategically locked in for business
reasons; or the abstraction is demonstrably preventing a capability the product
needs.

**Cost of reversal:** low. Removing an abstraction is easier than introducing one
— call sites would inline the provider SDK. The obligations it centralizes would
then have to be re-implemented per call site, which is the real reason not to.

## Compliance with authoritative specifications

- `llm-reasoning-rules.md` §1 — LLMs remain reasoning components. The gateway
  transports; it never elevates an LLM output to observed evidence.
- §5 — structured outputs enforced at the gateway, validated before return.
- §6 — tool/data access remains the caller's concern; the gateway does not fetch
  external data on a model's behalf.
- §7 — untrusted content confined to template data regions; a schema-validation
  failure is logged as a possible injection attempt, never retried blindly into a
  fallback.
- §8 — the cost ladder is preserved and **measured**. The gateway is the last
  rung, not the default one.
- §9 — full reproducibility record on every response.
- §10 — the recorded corpus and tier-based routing are what make evaluation
  possible.
- §11 — low-confidence conclusions remain eligible for human review; the gateway
  records what is needed to inspect them.
- `PROJECT_MANIFEST.md` §Cost Awareness — budget enforcement and cost-ladder
  telemetry.
- `evidence-confidence-framework-v1.md` §9 — budget exhaustion and provider
  outage produce explicit failure states, never a fabricated answer.
- **Resolves decision D-04** (architecture and tiering). Concrete per-run budget
  figures remain a configuration decision for Mission 0.2.
