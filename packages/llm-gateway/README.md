# `packages/llm-gateway` — Provider-agnostic LLM Gateway

**Status:** infrastructure implemented (Mission 0.2). **No provider implementation.**
**Governed by:** [ADR-006](../../docs/architecture/adr/ADR-006-provider-agnostic-llm-gateway.md)

## What exists

Interfaces, configuration resolution, budget enforcement, retry, timeout,
structured-output validation hooks, and test doubles. **No real external API
call is made anywhere in this package.**

```
python/sros_llm_gateway/
├── types.py        LlmRequest, LlmResponse, UsageMetadata, error taxonomy
├── config.py       tier -> provider/model resolution from environment
├── budget.py       per-session and per-workspace-day accounting
├── gateway.py      routing, retry, circuit breaker, schema validation
└── providers/
    ├── __init__.py the ONLY place a provider SDK may be imported
    └── fake.py     test doubles (EchoProvider, FailingProvider)
```

## The contract

Business services request a **logical tier**, never a provider or a model:

```python
from sros_llm_gateway import LlmGateway, LlmRequest, LlmTier

response = gateway.complete(
    LlmRequest(
        tier=LlmTier.FAST_MODEL,
        task="classify.signal",
        prompt_template_id="signal-classify",
        prompt_template_version="1.0.0",
        workspace_id=workspace_id,
        research_session_id=session_id,
        correlation_id=correlation_id,
    )
)
```

`LlmRequest` has no `provider` and no `model` field. That is enforced by a test:
an abstraction that lets callers name a vendor is not an abstraction.

## Why it is a chokepoint

Six obligations are implemented **once** here. Implemented per call site, each is
one hurried commit from being skipped:

| Obligation | Where | Spec |
|-----------|-------|------|
| Budget enforcement | `budget.py`, checked before dispatch | ADR-006 |
| Prompt versioning | required on every request | `llm-reasoning-rules.md` §9 |
| Model-version recording | `UsageMetadata` on every response | §9 |
| Structured-output validation | `gateway._validate_structured` | §5 |
| Cost telemetry | `UsageMetadata.to_log_fields()` | §8 |
| Tenant attribution | `workspace_id` required | ADR-005 |

## Two rules worth knowing before using it

**Budget exhaustion is a successful outcome.** `BudgetExhausted` means the
session completes with reduced Research Completeness. It is never a session
failure (Ontology V2 §15).

**A schema failure is never retried into a fallback.** It may signal prompt
injection (`llm-reasoning-rules.md` §7), so it surfaces rather than being routed
around. A tier is never silently downgraded either: serving `STRONG_MODEL` from
`FAST_MODEL` produces a worse answer that looks identical.

## Configuration

No model name is hard-coded. See `infrastructure/compose/.env.example`
(`LLM_TIER_*`). Models change faster than release cycles, so a model change is a
configuration change plus a recorded routing version.

## Tests

```bash
python infrastructure/scripts/run_python_tests.py
```

23 tests covering tier resolution, retry, budget refusal, schema validation, and
provider independence (tokenized, so a vendor named in a docstring is not a
false positive).

## Not implemented

Real providers, JSON Schema validation beyond required-field checks, durable
budget accounting (lands with the orchestrator), and evaluation datasets
(`llm-reasoning-rules.md` §10).
