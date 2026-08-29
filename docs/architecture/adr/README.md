# Architecture Decision Records

`PROJECT_MANIFEST.md` §Repository Philosophy: "Every architectural decision must
eventually be documented through ADRs."

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](ADR-001-turborepo-monorepo.md) | Turborepo + pnpm monorepo | Accepted |
| [ADR-002](ADR-002-nextjs-frontend.md) | Next.js 15 for the frontend | Accepted |
| [ADR-003](ADR-003-fastapi-backend.md) | FastAPI for backend services | Accepted |
| [ADR-004](ADR-004-celery-redis-job-architecture.md) | Celery + Redis job architecture | Accepted — resolves C-01 / D-02 |
| [ADR-005](ADR-005-workspace-multi-tenancy.md) | Workspace-centric multi-tenancy | Accepted — resolves D-05 |
| [ADR-006](ADR-006-provider-agnostic-llm-gateway.md) | Provider-agnostic LLM Gateway | Accepted — resolves D-04 |
| [ADR-007](ADR-007-local-first-docker-compose-deployment.md) | Local-first Docker Compose deployment | Accepted — resolves D-10 |
| [ADR-008](ADR-008-storage-architecture.md) | Storage architecture | Accepted — Mission 0.2 |
| [ADR-009](ADR-009-contract-first-code-generation.md) | Contract-first domain vocabulary with stdlib code generation | Accepted — Mission 0.2 |
| [ADR-010](ADR-010-python-dependency-management.md) | uv workspace for Python dependencies | Accepted — Mission 0.3 |
| [ADR-011](ADR-011-postgresql-access-psycopg.md) | psycopg 3 + explicit repositories | Accepted — Mission 0.3. **Supersedes ADR-008 §Database access strategy** |
| [ADR-012](ADR-012-row-level-security.md) | Row-level security with transaction-local tenant context | Accepted — Mission 0.4. **Completes ADR-005 §Future row-level security** |
| ADR-013 | Production deployment target | Required — deferred by ADR-007 |

> **Numbering note.** The production-deployment slot was previously listed as
> ADR-012. It was a placeholder with no file and no decision, so the number went
> to the first ADR actually written. A reserved number is not an ADR; renumbering
> a row that recorded a TODO breaks no reference and supersedes nothing.

## Status values

| Status | Meaning |
|--------|---------|
| Proposed | Written, not yet decided |
| Accepted | In force |
| Superseded by ADR-00X | Replaced; kept for history |
| Deprecated | No longer applies, nothing replaced it |

## Rules

**Append-only.** An accepted ADR is never edited to change its decision. It is
superseded by a new ADR that links back to it. Editing an ADR to match what the
code does now is how a project forgets why it is shaped the way it is.

**Correcting a typo is fine. Changing a decision is not.**

## When to write one

- A service boundary or contract changes.
- A runtime dependency is added or removed (database, queue, provider, model).
- A persisted data model changes.
- The computation of evidence, confidence or a score changes.
- The change is expensive to reverse.

```bash
cp docs/architecture/adr/ADR-TEMPLATE.md docs/architecture/adr/ADR-00X-short-title.md
```

## Domain references in ADR-001 to ADR-003

These three were written in Mission 0.1, when `opportunity-ontology-v1.md` and
`scoring-framework-v1.md` were current, and they still cite those filenames. That
is deliberate: **accepted ADRs are append-only**, and the references remain
semantically correct because V1.1 preserved V1's section numbering. A reference to
`scoring-framework-v1.md` §2 points at the same rule as
`scoring-framework-v1.1.md` §2.

ADR-003's compliance section also predates ADR-004. Its observation that the
Python-only ML stack makes the BullMQ contradiction unavoidable is not stale — it
is the antecedent ADR-004 acted on.

## A note on ADR-001 to ADR-003

These three record decisions that were **already locked** by
`PROJECT_MANIFEST.md` before this sprint began. Writing them is still worth the
effort, for one reason: a locked decision with no recorded rationale becomes
unquestionable, because nobody knows what it was trading off. These ADRs record
the reasoning and, more importantly, the **costs accepted** — so that when a cost
starts hurting, the team can tell whether it is a surprise or a known price.
