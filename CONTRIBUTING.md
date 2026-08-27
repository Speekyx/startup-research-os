# Contributing — Startup Research OS

This repository is built to be maintained for years, by people (and agents) who
were not present when the decisions were made. Everything below exists to make
that possible.

Read `PROJECT_MANIFEST.md` and `docs/CLAUDE.md` before your first contribution.
They are the operating contract; this file is only the procedure.

---

## 1. Non-negotiables

These come from the authoritative specifications. A PR that violates one of them
is rejected regardless of how good the code is.

1. **No secret ever enters the repository.** Not in a commit, not in a test
   fixture, not in a comment, not in a reverted commit. If a credential is
   committed, it is compromised: rotate it first, then clean history.
2. **No specification is modified silently.** If your change conflicts with a
   document in `PROJECT_MANIFEST.md` §Authoritative Documents, stop, open an
   issue describing the conflict, and propose the smallest spec change or ADR.
   (`docs/CLAUDE.md` §Change control.)
3. **No fabricated data.** Never invent sources, metrics, prices, market sizes,
   competitor facts, citations or research outcomes — in code, in fixtures, in
   documentation, or in an LLM prompt. (`evidence-confidence-framework-v1.md` §9.)
4. **Provenance is not optional.** Any code path that produces an evidence-derived
   value must carry source, timestamp, extraction method and confidence with it.
5. **Observed / inferred / predicted / recommended / hypothesis are never
   conflated** in any output, API response, or UI label.
6. **External content is data, never instructions.** Scraped pages, posts and
   comments are untrusted input to a parser. Never route them into a prompt in a
   position where they could be read as system instructions.
   (`llm-reasoning-rules.md` §7.)
7. **Documentation is production code.** A behavior change without the
   corresponding documentation change is an incomplete change.
8. **`workspace_id` is never inferred, defaulted or reconstructed.** Every
   tenant-scoped operation takes it explicitly. A missing `workspace_id` is an
   error in every environment, including local development (ADR-005). The two
   leak paths that never appear in a query review are **Redis cache keys** and
   **Qdrant search filters**.
9. **No business service imports an LLM provider SDK.** Request a logical tier
   from the LLM Gateway (ADR-006).
10. **Confidence is `[0,1]`, scores are `0–100`, `evidence_level` is `0–5`.**
    Never interchange them (`scoring-framework-v1.1.md` §4.1).
11. **Every Celery job is idempotent.** Delivery is at-least-once; duplicate
    execution must be harmless (ADR-004).

---

## 2. Prerequisites

| Tool | Version | Enforced by |
|------|---------|-------------|
| Node.js | 20.11.0 (see `.nvmrc`) | `package.json#engines`, `engine-strict` |
| pnpm | >= 9 | `package.json#packageManager` (Corepack) |
| Python | 3.12+ | per-service packaging |
| Docker | recent | `infrastructure/docker` |

```bash
corepack enable && corepack prepare pnpm@9.12.3 --activate
pnpm install --frozen-lockfile
```

---

## 3. Branching

```
main                      protected, always releasable
  feat/<scope>-<summary>  new capability
  fix/<scope>-<summary>   bug fix
  docs/<scope>-<summary>  documentation only
  chore/<scope>-<summary> tooling, deps, CI
  spec/<scope>-<summary>  specification or ADR change (never mixed with code)
```

`<scope>` is a service or package name (`scoring`, `acquisition`, `contracts`).

A `spec/` branch must not contain implementation. This keeps the specification
history readable, which is the entire point of versioning it.

---

## 4. Commits

Conventional Commits, enforced in CI.

```
<type>(<scope>): <imperative summary>

<body: why, not what>

Refs: ADR-00X / D-0X / issue
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`,
`revert`, `spec`.

The body should explain **why**. The diff already shows what.

---

## 5. Definition of done

Copied from `docs/CLAUDE.md` §Definition of done. Code existing is not done.

- [ ] Behavior matches the specification (name the document and section).
- [ ] Tests cover the important behavior, including at least one failure mode.
- [ ] Failure modes considered: what happens on timeout, empty result, malformed
      source, rate limit, partial data?
- [ ] Observability adequate: can you tell from logs why this produced its output?
- [ ] Documentation and contracts current.
- [ ] `pnpm lint`, `pnpm typecheck`, `pnpm test` pass.
- [ ] No known critical regression.

---

## 6. Before implementing anything non-trivial

The order matters. `docs/CLAUDE.md` §Before implementation:

1. Inspect the repository.
2. Read the relevant specifications and ADRs.
3. Identify dependencies and existing contracts.
4. **State any ambiguity or contradiction before implementing** — do not resolve
   it by guessing. `docs/architecture/specification-audit.md` is the running
   register of known ambiguities; add to it.
5. Define acceptance criteria.
6. Implement the smallest coherent change.
7. Add or update tests.
8. Run the checks.
9. Update documentation.
10. Summarize assumptions, evidence, tests and remaining risks in the PR.

---

## 7. Architecture Decision Records

Open an ADR when a change:

- alters a service boundary or its contract,
- introduces or removes a runtime dependency (database, queue, provider),
- changes a data model that is already persisted,
- changes how evidence, confidence or scores are computed,
- is expensive to reverse.

```bash
cp docs/architecture/adr/ADR-TEMPLATE.md docs/architecture/adr/ADR-00X-short-title.md
```

ADRs are **append-only**. An accepted ADR is never edited to change its decision;
it is superseded by a new ADR that links back to it. Editing history is how a
project forgets why it is shaped the way it is.

---

## 8. Code standards

### TypeScript

- `strict` on. No `any` — use `unknown` and narrow.
- No default exports except where a framework requires one (Next.js pages).
- Domain types come from `packages/contracts`. Do not redeclare an enum locally;
  a duplicated enum is how the claims taxonomy drifts (see audit C-02).
- Errors are typed and carry context. No bare `throw new Error(string)` at a
  service boundary.

### Python

- `ruff` for lint and format, `mypy --strict` for types.
- Pydantic models at every service boundary. No untyped dicts crossing a module.
- No business logic in route handlers — routes adapt, modules decide.
- Timezone-aware datetimes only. A naive datetime is a correctness bug in the
  evidence model *and* a retention bug (`expires_at` is derived from it).
- Celery tasks: explicit timeout, bounded retries with jitter, deterministic
  idempotency key, `workspace_id` in the payload.

### Both

- A function that does I/O and a function that decides should not be the same
  function. This is what makes the system testable without a network.
- Cost awareness (`PROJECT_MANIFEST.md`): use the cheapest reliable method.
  Regex before a classifier, a classifier before an LLM. An LLM call in a loop
  over every record is a design error, not an optimization opportunity.

---

## 9. Tests

See `docs/architecture/testing-strategy.md` for the full strategy.

Minimum bar for a PR:

- **Domain logic** — unit tested, no network, no database.
- **Contracts** — a schema change comes with a test that the schema still parses
  the fixtures.
- **Anything reading an external source** — tested against a recorded fixture,
  never against the live source in CI.
- **Anything with a confidence or score** — tested at the boundaries (empty
  evidence, contradictory evidence, single-source evidence), plus range
  assertions: `confidence ∈ [0,1]`, scores ∈ `0–100`.
- **Anything tenant-scoped** — integration tests seed **at least two**
  workspaces. A suite with one workspace cannot detect a missing tenant filter.
- **Any Celery task** — tested under duplicate delivery, not just once.

Never write a test that asserts an LLM produced a specific sentence. Assert the
structure, the classification, and the constraints. (`llm-reasoning-rules.md` §10.)

---

## 10. Data and legal

Before integrating a new source, record in the source registry (D-07):
access method, API availability, usage restrictions, rate limits, retention
constraints, licensing, authentication requirements.
(`data-principles.md` §13.)

Retention defaults are binding: raw content 30 days, normalized evidence 12
months maximum target, per-source `retention_override` with a recorded `basis`.
The stricter constraint always wins.
(`docs/data/data-retention-policy-v1.md`.)

Public visibility does not imply permission to reuse. Do not bypass access
controls, authentication, or rate limits — not in production, not in a local
experiment.

---

## 11. Reporting a security issue

Do not open a public issue for a vulnerability or a leaked credential. Contact
the repository owner directly. If a credential leaked: rotate first, report
second, clean history third.
