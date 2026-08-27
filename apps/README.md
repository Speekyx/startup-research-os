# `apps/` — User-facing applications

## Responsibility

Deployable applications that a human interacts with directly. An app is a
**consumer** of the system, never a place where domain logic lives.

## Rules

- An app may call `services/gateway`. It may **not** call any other service
  directly, and it may **not** connect to PostgreSQL, Redis or Qdrant.
- An app contains presentation logic, routing, and state management. Scoring,
  evidence evaluation and research orchestration are service concerns.
- Domain types are imported from `packages/contracts`. An app never redeclares a
  domain enum.
- Any value rendered to a user that derives from evidence must carry its claim
  type (`OBSERVED` / `INFERRED` / `PREDICTED` / `RECOMMENDED` / `HYPOTHESIS`) and
  its confidence. Rendering a bare number is a specification violation
  (`evidence-confidence-framework-v1.md` §8).

## Contents

| Directory | Status | Purpose |
|-----------|--------|---------|
| `web/` | planned | Next.js 15 research console |

## Not here

- Background jobs → `services/workers`
- Shared React components → `packages/ui`
- API route logic → `services/gateway`
