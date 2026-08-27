# Quality Gates

Version: 1.2
Status: Strategy fixed, tooling partially scaffolded
Date: 2026-08-27 (amended in Mission 0.1.2)

What must be true for a change to reach `main`. `docs/CLAUDE.md` §Definition of
done is the requirement; this document is the mechanism.

The organising principle: **a rule that is only in a document is a rule that will
be broken.** Every specification obligation that can be moved into a type, a lint
rule, a schema, or a test should be.

---

## 1. Gate summary

| Gate | Tool | Status | Blocking |
|------|------|--------|----------|
| Formatting | Prettier (TS/MD/JSON/YAML), ruff format (Python) | Scaffolded | Yes |
| Lint | ESLint, ruff | Strategy fixed, config pending | Yes |
| Types | `tsc --noEmit`, `mypy --strict` | Config scaffolded | Yes |
| Unit tests | Vitest, pytest | Pending | Yes |
| Contract tests | Schema validation against fixtures | Pending | Yes |
| Integration tests | pytest + testcontainers | Pending | Yes |
| E2E | Playwright | Pending | Nightly, not per-PR |
| Secret scan | gitleaks | Pending | Yes |
| Dependency audit | `pnpm audit`, `pip-audit` | Pending | Warn, then block |
| Diagram/doc sync | Manual (review checklist) | Active | Review |
| Spec compliance | Manual (PR checklist) | Active | Review |

"Pending" means the strategy below is decided and the tool is installed in
Mission 0.2. Nothing in this table is undecided.

---

## 2. Turborepo task graph

Defined in `turbo.json`.

| Task | Depends on | Cached | Notes |
|------|-----------|--------|-------|
| `build` | `^build` | Yes | Excludes test files from the input hash |
| `lint` | `^build` | Yes | |
| `typecheck` | `^build` | Yes | Needs upstream declarations |
| `test` | `build` | Yes | Own package's build, not just upstream |
| `test:unit` | `^build` | Yes | Fast path, no local build |
| `test:e2e` | `build` | **No** | Real browser, real time |
| `dev` | — | No | Persistent |

Caching rules that matter:

- **`test:e2e` is never cached.** An E2E result is a statement about a running
  system at a moment in time, not a pure function of the source.
- **`build` excludes test files from its inputs.** Editing a test must not
  invalidate the build cache.
- **`globalDependencies`** includes `.editorconfig`, `.nvmrc` and
  `packages/typescript-config/base.json` — changing a toolchain-wide file
  correctly busts everything.

### Python and Turborepo

Turborepo does not understand Python imports (ADR-001, Cons). Each Python service
exposes its tasks through a thin `package.json` script layer:

```jsonc
// services/scoring/package.json
{
  "name": "@sros/scoring",
  "scripts": {
    "lint": "ruff check .",
    "typecheck": "mypy --strict src",
    "test": "pytest",
    "build": "python -m build"
  }
}
```

Turborepo hashes the whole service directory rather than a precise import graph,
so Python caching is coarse. It errs toward cache misses, never stale hits.

---

## 3. Lint strategy

### Principles

1. **Lint catches correctness, not style.** Prettier and ruff format own style.
   Overlapping the two produces conflicts that get resolved by disabling rules.
2. **Every rule blocks something real.** A rule that produces noise gets disabled
   in bulk, taking the useful rules with it.
3. **No blanket `eslint-disable` at file scope.** A disable is one line, one
   rule, with a reason.

### TypeScript — rules with specification weight

These are not preferences. Each blocks a specific specification violation.

| Rule | Blocks |
|------|--------|
| `no-restricted-imports` (cross-service paths) | A context importing another's internals instead of its contract (`service-boundaries.md` §4) |
| `no-restricted-syntax` (local domain enums) | The C-02 drift: a domain enum declared outside `packages/contracts` |
| `no-restricted-imports` (LLM provider SDKs) | A business service importing a provider SDK instead of using the LLM Gateway (ADR-006) |
| `@typescript-eslint/switch-exhaustiveness-check` | An unhandled claim type or score family — the conflation §8 forbids |
| `@typescript-eslint/no-floating-promises` | Silently dropped async work; in a pipeline, a lost job is lost evidence |
| `@typescript-eslint/no-explicit-any` | Untyped data crossing a boundary where provenance must be attached |
| `react/no-danger` | Rendering scraped content as HTML |
| `no-restricted-globals` on `process.env` outside config | Environment access scattered through domain code |

### Python — ruff

Enabled rule families: `E`/`W` (pycodestyle), `F` (pyflakes), `I` (isort),
`N` (naming), `UP` (pyupgrade), `B` (bugbear), `ASYNC` (async correctness),
`S` (bandit security), `DTZ` (timezone-aware datetimes), `RET`, `SIM`, `PTH`.

Two of these are load-bearing rather than cosmetic:

- **`ASYNC`** — catches blocking calls inside async handlers. ADR-003 records
  this as the failure mode whose symptom is furthest from its cause.
- **`DTZ`** — forbids naive datetimes. Every observation in this system carries a
  timestamp (`data-principles.md` §9), and recency decay is computed from them.
  A naive datetime is a silent correctness bug in the evidence model. It is also a
  retention bug: `expires_at` is computed from these timestamps
  (`data-retention-policy-v1.md` §6).

### Tenancy and numeric-scale checks

Two classes of bug are severe enough to deserve their own automated checks
(Mission 0.2), because review does not reliably catch either:

| Check | Catches |
|-------|---------|
| Repository/query lint for tenant-scoped tables | A query on a tenant-scoped table with no `workspace_id` filter — a cross-tenant data leak, not a rendering bug (ADR-005) |
| Cache-key and vector-filter enforcement in client wrappers | The two leak paths that do not go through SQL and so never appear in a query audit |
| Contract range validators | A `confidence` outside `[0,1]` or a `*_score` outside `0–100` (`scoring-framework-v1.1.md` §4.1) |
| `MarketScope` shape validators | A `COUNTRY` scope with two countries, an empty list, or an uncanonicalized list — all of which break scope equality and therefore cache and dedup keys (Ontology V2 §4.4) |
| Registry-vs-enum lint | A domain taxonomy declared as a union type or a database enum instead of a registry reference (Ontology V2 §14.3) |

`mypy --strict` is required, not optional: without it Pydantic validates the
edges while the interior stays untyped, and the guarantee ADR-003 was made for
stops at the boundary.

---

## 4. Formatting strategy

| Files | Tool |
|-------|------|
| `.ts .tsx .js .jsx .json .md .yml .yaml` | Prettier |
| `.py` | ruff format |
| Whitespace baseline for everything | `.editorconfig` |

Rules:

- **Formatting is never a review comment.** If a human mentions formatting in a
  review, the automation has failed.
- **CI checks, it does not fix.** `format:check` fails the build; a bot pushing
  format commits makes history unreadable.
- **One formatter per file type.** No exceptions.
- **Markdown is formatted too.** Documentation is production code
  (`PROJECT_MANIFEST.md` §Repository Philosophy).

---

## 5. CI pipeline (planned)

Placeholders in `.github/workflows/`. They are `workflow_dispatch`-only until
Mission 0.2, so they cannot fail on a repository that has no lockfile yet.

```
PR opened
  ├─ changed-paths detection        (avoid running everything on every PR)
  ├─ secret scan                    ALWAYS runs, never path-filtered
  ├─ format:check                   fast fail
  ├─ lint            ─┐
  ├─ typecheck        ├─ parallel
  ├─ test:unit       ─┘
  ├─ contract tests                 schemas still parse the fixtures
  ├─ integration tests              testcontainers: postgres, redis, qdrant
  └─ build

main (post-merge)
  ├─ everything above
  ├─ dependency audit
  └─ image build

nightly
  ├─ E2E (Playwright)
  ├─ full integration suite
  └─ dependency audit
```

### Rules

1. **The secret scan is never path-filtered and never skipped.** It is the one
   gate whose failure is unrecoverable: a leaked credential is compromised the
   moment it is pushed, and reverting the commit does not un-leak it.
2. **Path filtering everywhere else.** ADR-001 accepted "CI must be path-filtered
   or it becomes slow" as a known cost; this is the payment.
3. **E2E is nightly, not per-PR.** Flaky per-PR E2E teaches people to re-run
   failing jobs without reading them, which destroys the value of every other
   gate.
4. **No test in CI touches a live external source.** Recorded fixtures only.
   Otherwise the build depends on a third party's uptime and rate limits, and
   `data-principles.md` §3 gets violated by a CI run.
5. **CI has no production credentials.**

---

## 6. Branch protection (when the remote exists)

- `main` protected, no direct pushes.
- Required status checks: format, lint, typecheck, unit, contract, integration,
  secret scan.
- Required review via `CODEOWNERS` — **D-09 resolved**: the owner is `@Speekyx`
  and `CODEOWNERS` is updated accordingly. Note for any future change: GitHub
  does not error on an unresolvable owner. It silently assigns no reviewer, so
  branch protection would appear configured while enforcing nothing.
- Linear history, no merge commits from feature branches.
- Conversation resolution required.

---

## 7. What automation cannot check

These stay in human review, and they are the ones that matter most in this
system:

| Check | Why a machine cannot do it |
|-------|---------------------------|
| Is this claim correctly typed as `OBSERVED` vs `INFERRED`? | Requires knowing what the data actually supports |
| Is this confidence value justified? | Requires judgment about the evidence |
| Does this contradict an authoritative specification? | Requires reading both |
| Is this LLM prompt injection-safe? | Requires adversarial thinking |
| Is this source's usage lawful? | Requires reading terms of service |
| Is the evidence aggregation sound? | Requires domain reasoning |
| Is this retention period justified by the source terms? | Requires reading the terms and recording a `basis` (`data-retention-policy-v1.md` §3) |
| Is this job genuinely idempotent? | Requires reasoning about at-least-once delivery (ADR-004) |
| Are these two discoveries the same opportunity? | Identity resolution is an analytical judgment, not a unique constraint (Ontology V2 §12.3) |
| Should this taxonomy value be a new registry entry or an alias of an existing one? | Requires domain judgment |

The PR template (`.github/PULL_REQUEST_TEMPLATE.md`) asks about these explicitly,
because a checklist item is the cheapest available prompt to think about them.
