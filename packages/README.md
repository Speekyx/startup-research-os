# `packages/` — Shared libraries

## Responsibility

Code shared across more than one app or service. A package exists because
duplicating it would cause drift, not because it seemed reusable.

## Rules

1. **A package has no side effects at import time.** No database connection, no
   environment read, no network call.
2. **A package never imports a service.** Dependencies point from services to
   packages, never the reverse. A cycle here is an architectural failure.
3. **A package that only one consumer uses is not a package.** Move it back into
   the consumer until a second one needs it.
4. **`contracts` is special.** It is the only place a domain type is declared.

## Contents

| Package | Status | Purpose |
|---------|--------|---------|
| `contracts/` | **implemented** | Domain vocabulary, single source of truth (ADR-009) |
| `llm-gateway/` | **implemented (skeleton)** | Provider-agnostic LLM access (ADR-006) |
| `eslint-config/` | **implemented** | Shared lint rules |
| `evidence-aggregation/` | **implemented** | The aggregation reference implementation (ADR-014) |
| `signal-model/` | **implemented** | What a Signal is, and what it may not assert (ADR-020) |
| `claim-model/` | **implemented** | The interpretation boundary: how a Signal may become a Claim, and may not (ADR-024) |
| `typescript-config/` | scaffolded | Shared `tsconfig` bases |
| `ui/` | planned | shadcn/ui-based component library |
| `observability/` | planned | Logging, tracing and correlation conventions |

> Three rows were missing from this table until Mission 1.13 —
> `evidence-aggregation` (1.1), `signal-model` (1.11) and, on the same pass,
> `claim-model`. An index that omits what exists is a worse guide than no index.

## Why `contracts` matters more than the rest

The specification audit found two contradictions
(C-02 claims taxonomy, C-04 numeric scales) caused by the same domain concept
being defined in two documents with different values. Prose in two places drifts.
A generated type does not.

`packages/contracts` is the mitigation: one schema source, generating both
TypeScript types and Python Pydantic models. Any service that redeclares a domain
enum locally has reintroduced the drift the package exists to prevent.
