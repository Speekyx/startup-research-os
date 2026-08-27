# ADR-010 — uv workspace for Python dependency management

- **Status:** Accepted
- **Date:** 2026-08-27
- **Deciders:** Implemented in Mission 0.3 under brief §25
- **Related:** ADR-001, ADR-003, ADR-009

---

## Context

Mission 0.2 deliberately used zero-dependency checks because no package manager
was available in that environment. Mission 0.3 establishes the real one.

The repository has **four Python packages** that depend on each other:

```text
sros-contracts      (no dependencies, by design -- ADR-009)
sros-llm-gateway    -> sros-contracts
sros-workers        -> sros-contracts, celery, redis
sros-gateway        -> sros-contracts, sros-llm-gateway, fastapi, psycopg, ...
```

Requirements from the brief: lockable and reproducible, works in CI, supports
multiple backend packages, supports dev/test dependencies. Plus one from ADR-001:
a contract change and its consumers must land in one commit, which means local
path dependencies have to resolve without publishing.

## Decision

**`uv` with a workspace**, one `pyproject.toml` per package plus a root
workspace member list, and a single committed `uv.lock`.

```toml
# pyproject.toml (root)
[tool.uv.workspace]
members = [
    "packages/contracts/python",
    "packages/llm-gateway/python",
    "services/workers/python",
    "services/gateway/python",
]

[dependency-groups]
dev = ["pytest", "ruff", "mypy", "httpx", "pip-audit"]
```

```bash
uv sync --all-packages
uv run pytest
```

Cross-package dependencies are declared normally (`dependencies = ["sros-contracts"]`)
and resolved from the workspace via `[tool.uv.sources]`, so a contract change is
visible to every consumer immediately with no publish step.

## Alternatives considered

### Alternative A — pip + pinned `requirements.txt` per package

Simplest, no new tool. Rejected: pinning direct dependencies is not a lock —
transitive versions still float, so "reproducible" would be aspirational. It
also has no first-class way to express four interdependent local packages
without `-e ../..` path entries that break in CI, and dev/test dependencies
become a naming convention.

### Alternative B — Poetry

Mature, lockfile, dev groups. Rejected: no real workspace/monorepo support (its
path dependencies work but each package needs its own lock, so the four can
drift), and it is slow enough that people skip running it.

### Alternative C — PDM

Closer to uv in capability, PEP-621 native. Rejected on adoption and speed
rather than capability; uv covers the same ground and installs an order of
magnitude faster, which matters because a slow install is an install that gets
skipped in CI.

### Alternative D — Hatch

Good environment management, weaker locking story for a multi-package workspace.

### Alternative E — Keep zero-dependency everywhere

Not viable past Mission 0.2: FastAPI, Celery, psycopg and Qdrant are real
dependencies. But see below — the zero-dependency checks were not thrown away.

## ADR-009 is unaffected

**The dependency-free contract generator and conformance checks stay exactly as
they are.** They are not a workaround that real tooling replaces; they are a
property worth keeping:

- `packages/contracts/tools/generate.py` runs on stdlib Python alone.
- `infrastructure/scripts/run_python_tests.py` runs 65 tests with no install.
- The TypeScript conformance suite runs on a bare Node runtime.
- `validate_schema.py`, `migrate.py --plan` and `check_env_template.py` need
  nothing installed.

That means a broken or unavailable dependency environment cannot silently reduce
the contract and schema checks to nothing. Mission 0.3 added the install-based
suites *alongside* them, not instead of them, and CI runs both.

## Pros

- One lockfile for four interdependent packages; one `uv sync` reproduces the
  whole backend.
- Cross-package changes stay atomic (ADR-001's central argument).
- Dev/test dependencies are a first-class group, not a second requirements file.
- Fast enough that running it is never the slow step.
- PEP-621 `pyproject.toml` throughout, so migrating away later is mostly
  deleting `[tool.uv.*]` blocks.

## Cons

- **uv is young.** It moves quickly, and a breaking change in its workspace
  semantics would be disruptive. Mitigated by standard `pyproject.toml` metadata:
  the packages are portable even if the tool is not.
- **A second package manager in the repo** alongside pnpm. Two lockfiles, two
  install commands, two caches in CI.
- **Less familiar than pip or Poetry**, so a contributor may need to install it
  before they can install anything else.
- **The lockfile is uv-specific.** `uv.lock` is not a `requirements.txt`; a
  consumer wanting plain pip needs `uv export`.

## Future impact

**Becomes easy:** adding a Python package; changing a shared contract; keeping
CI reproducible; pinning a transitive dependency after a CVE.

**Becomes hard:** using a tool that expects `requirements.txt` without an export
step.

**Revisit if:** uv's workspace model changes incompatibly, or the project drops
to a single Python package (at which point plain pip would suffice).

**Cost of reversal:** low. `uv export --format requirements-txt` produces a
pinned file per package, and the `pyproject.toml` metadata is standard.

## Compliance

- **ADR-001** — atomic cross-package changes preserved.
- **ADR-003** — Pydantic is a `sros-gateway` dependency, at the HTTP boundary
  only; `sros-contracts` stays dependency-free.
- **ADR-009** — explicitly unaffected. The zero-dependency checks remain and are
  still wired into CI.
- **`quality-gates.md`** — `ruff`, `mypy` and `pytest` live in the dev group and
  are now genuinely runnable, so the gates that were configured-but-unwired in
  Mission 0.2 are active.
