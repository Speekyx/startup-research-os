# GitHub Actions

**Enabled in Mission 0.2.** Both workflows run on pull request and on push to
`main`. `security.yml` was enabled first: a credential committed on day one is
compromised whether or not a test suite exists.

| Workflow | Jobs | Runs |
|----------|------|------|
| `security.yml` | secret scan (gitleaks, full history), environment-template check | PR, push, nightly |
| `ci.yml` | contract generation check, schema invariants, Python tests, TypeScript conformance, compose config | PR, push |

## The rule these workflows follow

**Every job runs a check that genuinely exists and genuinely passes.** There is
no placeholder job, because a permanently red pipeline teaches people to ignore
all of it (`quality-gates.md` §5).

Checks deliberately not enabled yet, and why:

| Check | Waiting on |
|-------|-----------|
| `pnpm install`, lint, build | A lockfile and a TypeScript app. Neither exists |
| `ruff`, `mypy` | Configured in `pyproject.toml`; enabled with the first service package |
| Dependency audit | `pnpm audit` needs a lockfile; `pip-audit` needs installed requirements |
| CodeQL | Needs compiled application code |
| Integration tests | Need service code, not just a schema |
| Prompt-injection suite | Needs `services/nlp` (`llm-reasoning-rules.md` §7) |

## Why no install step

The contract check, the schema validator and both test suites run on **stdlib
Python and a bare Node runtime**. A check that cannot be skipped because a
dependency failed to install is a check that actually runs (ADR-009).
