# `packages/llm-gateway` — Provider-agnostic LLM Gateway

**Status:** infrastructure implemented (Mission 0.2); **real provider adapters,
error taxonomy, retry policy, pricing, telemetry, prompt registry and evaluation
framework added in Mission 0.4.**
**Governed by:** [ADR-006](../../docs/architecture/adr/ADR-006-provider-agnostic-llm-gateway.md)

## What exists

```
python/sros_llm_gateway/
├── types.py        LlmRequest, LlmResponse, UsageMetadata, the error taxonomy
├── config.py       tier -> provider/model resolution from the environment
├── pricing.py      versioned provider tariffs. EMPTY by default, on purpose
├── budget.py       per-session and per-workspace-day accounting
├── transport.py    the HTTP seam that makes providers testable without a key
├── gateway.py      routing, retry policy, schema validation, telemetry
├── prompts/
│   ├── rendering.py  the three prompt regions and the injection boundary
│   └── registry.py   versioned templates, looked up by (id, version)
├── providers/
│   ├── anthropic.py  Messages API. Structured output via forced tool use
│   ├── gemini.py     generateContent. Structured output via responseSchema
│   └── fake.py       test doubles
└── evaluation/     datasets, metrics, runner, regression comparison, store
```

**No external API call is made in any test.** Not one requires a credential.

## The contract

Business services request a **logical tier**, never a provider or a model:

```python
response = gateway.complete(
    LlmRequest(
        tier=LlmTier.FAST_MODEL,
        task="classify.signal",
        prompt_template_id="signal-classify",
        prompt_template_version="1.0.0",
        prompt=rendered,  # a RenderedPrompt, regions separated
        workspace_id=workspace_id,
        research_session_id=session_id,
        correlation_id=correlation_id,
    )
)
```

`LlmRequest` has no `provider` and no `model` field, and a test asserts it: an
abstraction that lets callers name a vendor is not an abstraction.

## Providers without a vendor SDK

Both adapters speak their provider's HTTP API through an injectable
`HttpTransport`. ADR-006 permits an SDK inside `providers/`; using none is
stronger and cheaper here:

- `uv.lock` gains no vendor dependency, so a provider's release cadence cannot
  break this repository's install;
- one fake transport is the entire mock surface — no per-SDK stubbing;
- the request each adapter builds is a plain dict a test can assert on.

The cost, stated: streaming and any SDK-provided retry logic must be implemented
here rather than inherited. Neither is needed yet, and the gateway already owns
retry policy.

**Structured output uses each provider's decoder constraint**, not a prose "reply
in JSON" instruction: forced tool use for Anthropic, `responseMimeType` plus
`responseSchema` for Gemini. A prose instruction competes with every other
instruction in the prompt, including any an attacker placed in a data region. A
decoder constraint does not.

Neither provider advertises `EMBEDDING_MODEL`. Embeddings stay on local BGE-M3
(ADR-006), and advertising the tier would let the router send the
highest-volume operation in the system to a paid API.

## Error taxonomy and retry policy

Failures are normalized into categories a business service can branch on. An
`except anthropic.RateLimitError` in a service is a service pinned to one vendor,
and the pin is invisible until the day the provider changes.

| Category | Retried? | Why |
|----------|----------|-----|
| `TIMEOUT` | yes | Transient |
| `RATE_LIMITED` | yes | Backoff, with jitter (ADR-004) |
| `TEMPORARY` | yes | 5xx or transport failure |
| `INVALID_REQUEST` | **no** | Deterministic: the same rejection costs the same twice |
| `AUTHENTICATION` | **no** | Repeated failed auth trips abuse detection and never succeeds |
| `SCHEMA_FAILURE` | **no** | May signal prompt injection — it surfaces |
| `BUDGET` | **no** | Refusal is the answer |
| `NO_PROVIDER` | **no** | The tier cannot be served |

**Changed in Mission 0.4:** exhausted retries now propagate the *original*
error with its category, rather than `NoProviderAvailableError`. A timeout
reported as "no provider available" describes a different operational problem
from the one that occurred.

## Pricing is configuration, and empty by default

`LLM_PRICING_VERSION` and `LLM_PRICING_JSON`, keyed `"<provider>:<model>"`.

**A model with no configured price is UNPRICED, not free**, and the usage record
says so (`priced=False`). Reporting an unpriced call as costing zero would show
every budget untouched while real money was spent.

No tariff is compiled into any module. Provider prices change without notice and
vary by region and contract; a plausible constant would be wrong within months
and would look authoritative. A test fails the build if one appears outside
`pricing.py`.

## Telemetry

Every request emits a `UsageMetadata` to the configured sink — successes **and**
failures, because a provider that fails expensively and invisibly is what the
cost-ladder metric in ADR-006 exists to make visible.

It carries provider, model, tier, routing version, prompt id and version, token
counts, cost and pricing version, latency, retries, outcome, error category, and
the `workspace_id` / `research_session_id` / `correlation_id` triple.

**It carries no content.** No prompt text, no variables, no response body. A
test asserts that a secret placed in a request variable does not appear in the
serialized log fields: telemetry that carried them would put scraped source data
into the log pipeline, where `data-principles.md` §8 says it must never go.

## Prompts and the injection boundary

A rendered prompt has three regions, and content can only enter the one it was
given:

```text
SYSTEM INSTRUCTIONS          ours, from the template, versioned
TRUSTED APPLICATION CONTEXT  our own data: scope, ids, parameters
UNTRUSTED SOURCE DATA        anything that came from outside the system
```

`UntrustedText` is a distinct type, so passing scraped text where an instruction
was expected is a type error a reviewer can see rather than a concatenation that
looks identical to a safe one. Delimiters inside untrusted content are
neutralized, and the neutralization is visible — silently deleting
attacker-controlled text hides that an attempt was made.

**What it defends and what it does not.** Region separation stops the mechanical
attacks: a comment that closes its own fence, a document impersonating a system
turn. It does not make a model immune to persuasion inside a data region;
nothing does. The defences for that are elsewhere — structured output, a schema
failure treated as a signal rather than retried, and the rule that an LLM opinion
is never observed evidence.

**The runtime prompt registry is deliberately empty.** Every context that would
own one is blocked or out of scope, and a prompt written against inputs nothing
produces would be tested only against its own assumptions.

## Evaluation

See [`docs/ai/evaluation-framework-v1.md`](../../docs/ai/evaluation-framework-v1.md).

The framework can load a versioned dataset, run a model, compute per-task
metrics, store the result and compare two runs. **Cost can never offset
quality**: a cheaper, worse candidate is rejected and the report says so.

The shipped dataset is a synthetic fixture and declares itself so, and the flag
travels into the comparison report. Real datasets need labelled examples from
collected sources, which D-07 blocks.

## Configuration

No model name is hard-coded. See `infrastructure/compose/.env.example`
(`LLM_TIER_*`, `LLM_PRICING_*`, `SROS_ENABLE_PROVIDER_SMOKE_TESTS`).

## Tests

```bash
python infrastructure/scripts/run_python_tests.py
```

125 tests, plus 2 opt-in smoke tests that are **skipped unless** both
`SROS_ENABLE_PROVIDER_SMOKE_TESTS=1` and a credential are set. The flag is
separate from the key on purpose: a developer with a key exported for other work
has not thereby consented to spending money on every test run.

## Two rules worth knowing before using it

**Budget exhaustion is a successful outcome.** `BudgetExhaustedError` means the
session completes with reduced Research Completeness. It is never a session
failure (Ontology V2 §15).

**A tier is never silently downgraded.** Serving `STRONG_MODEL` from
`FAST_MODEL` produces a worse answer that looks identical.

## Not implemented

Streaming, full JSON Schema validation beyond required-field checks, circuit
breaker automation (the manual open/close hooks exist), durable budget accounting
(that lives in `sros_orchestrator`), and any real evaluation dataset.
