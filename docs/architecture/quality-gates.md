# Quality Gates

Version: 1.6
Status: Active. Every gate in §1 runs in CI
Date: 2026-08-29 (amended in Mission 1.2)

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

### Status as of Mission 0.4

Every gate above now runs. What changed since the table was written:

| Gate | Now |
|------|-----|
| Lint | **Active.** ruff (11 rule families) and ESLint 9 with type-aware rules over `**/*.ts` **and `**/*.tsx`** — the React components are the newest code in the repository and would otherwise be the only code exempt from the architectural rules |
| Types | **Active.** `mypy --strict` over 58 source files; `tsc` over two projects (contracts, web) plus `next build`, which typechecks generated route types the project-level check cannot see |
| Unit / integration tests | **Active.** 225 zero-dependency tests, 370 pytest tests across five packages, 19 TypeScript conformance tests |
| E2E | Still not implemented. There is no user workflow to walk through |

### Gates added in Mission 0.4

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **Tenant isolation, two workspaces** | `services/gateway/python/tests/test_rls.py` | A query with no `WHERE workspace_id` returns only the current tenant's rows. This is the one gate that catches a *forgotten* filter rather than a wrong one (ADR-012) |
| **Pooled-connection tenant leak** | Same suite, single-connection pool | A session-level `SET` would leak a tenant between borrowers with no bug in any query |
| **No hard-coded provider tariff** | `test_pricing_and_telemetry.py` | A price constant in a module is a decision nobody recorded making (§15). Fails the build if one appears outside `pricing.py` |
| **No content in telemetry** | Same suite | A secret placed in a request variable must not appear in the serialized log fields (`data-principles.md` §8) |
| **Prompt-injection boundary** | `test_prompts.py`, adversarial payloads | No arrangement of attacker-controlled text escapes its region or reaches the system field (`llm-reasoning-rules.md` §7) |
| **No provider credential in CI** | `ci.yml`, integration job | A smoke suite that quietly became enabled would show up as an invoice rather than as a red build (§20) |
| **Retry policy by category** | `test_providers.py` | An authentication error or an invalid request is never retried: it costs the same twice and trips abuse detection (§22) |
| **Blocked work cannot be dispatched** | `test_orchestrator_integration.py` | A `BLOCKED` job has no transition to `READY`, so the source gate and D-03 hold mechanically rather than by memory (§32, §33) |

### Gates added in Mission 1.0

Every one of these guards a rule that would otherwise depend on a reviewer
remembering it under pressure to ship a collector.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **No approval without authoritative evidence** | `registry.require_evidence_for_approval` (deferred constraint trigger) + `test_source_registry.py` | An approving review with no first-party document is refused at COMMIT, whoever writes it. A blog post cannot be recorded as the basis of an approval, because the evidence-type enum has no value for one |
| **No collector on an ineligible source** | `registry.require_eligibility_for_collector` (BEFORE UPDATE trigger) | Even a direct `UPDATE` by the migration role cannot turn a collector on. The database, not the application, has the last word |
| **The Python gate and the SQL view agree** | `test_source_registry.py` | The eligibility rules exist twice by necessity. Two implementations of one rule drift; this compares them on every source rather than trusting they match |
| **No credential in the registry** | `sros_acquisition.registry.models` + `validate_source_registry.py` + `test_source_registry.py` | `secret_references` holds configuration key names. A value that looks like a credential is refused, so a secret cannot reach a file every reader of the repository can open |
| **No source silently approved** | `validate_source_registry.py` (zero dependency) | Runs with no database and no packages installed. A broken environment cannot reduce this check to nothing (ADR-009 rationale) |
| **The rendered catalog matches the JSON** | `sros-source render --check` | Two hand-maintained copies of one fact drift, and the drift is found by whoever trusted the wrong one |
| **CI calls no external platform** | `ci.yml` | A registry job that fetched a platform's terms would be collection, and would make the build depend on a third party's uptime (§43) |
| **Acquisition blocking is registry-derived** | `test_orchestrator_integration.py` | The orchestrator must read its refusal from `registry.source_eligibility`, not restate it in code. A hardcoded reason is a reason nobody notices going false |

### Gates added in Mission 1.1

D-03 is resolved at the framework level, so the old blanket ban on aggregation
vocabulary was replaced rather than deleted. These gates draw the line that
replaces it.

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **Rejected designs stay rejected** | `validate_evidence_aggregation.py` | `contradiction_penalty`, `decay_weight`, `aggregated_evidence_score`, `independence_threshold_result`, `evidence_aggregate` are forbidden everywhere, permanently. Each names a design the framework considered and rejected, so its return is a regression rather than an unblocked feature |
| **V1 vocabulary stays out of production surfaces** | Same script | The authorised names are allowed in the reference package and the contracts, never in a migration or under `services/`. Defining the framework and enabling production scoring are separate gates |
| **No universal half-life** | Same script | A module-level half-life constant is refused anywhere. §9 puts half-lives in versioned profiles; a constant would be the invented universal value, and it would *work*, which is what makes it dangerous |
| **No per-source reliability weight** | Same script + `test_evidence_aggregation.py` | No registered source id appears in the aggregation package. Two evidence sets differing only in `source_id` must produce identical numbers |
| **The shipped profile stays UNCALIBRATED** | Same script | Promotion to `CALIBRATED` requires the calibration plan to have been executed and published. A profile cannot even be constructed as `CALIBRATED` without a `calibration_dataset_ref` |
| **`services/scoring` has no implementation** | Same script | The directory is a boundary README. Code appearing in it means production scoring started without a calibrated profile |
| **The twelve mathematical invariants** | `test_evidence_aggregation.py` | Masses sum to 1; the score stays on 0–100; duplicates cannot inflate; unknown independence cannot stack; adding contradiction cannot raise the score; reordering changes nothing; evergreen evidence does not decay; missing inputs are never defaulted |
| **Aggregation is order-independent end to end** | Same suite | Byte-identical canonical output under reordering. Floating-point addition is not associative, so this is engineered by sorting rather than assumed — and it caught a real defect in the explanation serialisation |
| **The sensitivity report matches the code** | `sensitivity --check` | The report is generated from the implementation, so it cannot describe behaviour the code does not have |

### Gates added in Mission 1.2

| Gate | Mechanism | Guards |
|------|-----------|--------|
| **Cross-tenant references are impossible, not merely forbidden** | Composite foreign keys carrying `workspace_id` (migration 0005) + `test_claims.py` | A claim cannot reference an opportunity in another workspace, evidence cannot reference a claim in another workspace, and an independence group cannot span claims or workspaces. A third layer under the repository filter and the RLS policy, failing differently from both |
| **The independence shape holds without the repository** | `evidence_independence_shape_check` | `KNOWN_DEPENDENT` must name a group, the other two must not. A future writer that bypasses the repository still cannot store an incoherent record |
| **Unknown independence stays unknown in storage** | Same CHECK + `test_claims.py` | The engine builds its conservative runtime bucket without writing one. An unresolved question must not look resolved in the database |
| **The claim revision pointer names a real revision** | Deferred composite foreign key | A pointer to a nonexistent revision would make the current statement unreadable |
| **RLS on every new tenant table** | Migration 0005 + `test_rls.py` + `test_claims.py` | Four new tables, all ENABLE and FORCE, all policy-bearing. A claim visible across workspaces would leak what another tenant is researching, in their own words |
| **No service imports the reference aggregation engine** | `validate_evidence_aggregation.py` | Tests may import it; production modules may not. This is what makes the vocabulary narrowing below safe (ADR-014) |
| **Computed aggregation values stay out of production** | Same script | The guard was NARROWED, not weakened: evidence INPUT fields became legitimate schema columns in Mission 1.2, while the strengths, masses and score remain forbidden in migrations and under `services/` |
| **No aggregation result is persisted** | `test_claims.py` | Storing a result would be scoring, and scoring requires a `CALIBRATED` profile that does not exist |

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
