# ADR-001 — Use a Turborepo + pnpm monorepo

- **Status:** Accepted
- **Date:** 2026-08-27
- **Deciders:** Project owner (locked in `PROJECT_MANIFEST.md` §Technology Stack)
- **Supersedes:** none
- **Related:** `PROJECT_MANIFEST.md` §Repository Philosophy, `docs/CLAUDE.md`
  §Core principles, audit C-01 and C-03

---

## Context

The system spans nine bounded contexts, a Next.js frontend, shared domain
contracts, and infrastructure definitions. It is built by a very small team
(currently one person) but must remain understandable for years.

Three forces apply:

1. **The domain contracts must not drift.** The specification audit found the
   same domain concept defined twice with different values in two documents
   (C-02: claims taxonomy; C-04: numeric scales). The structural fix is one
   generated contracts package consumed by every service. That fix only works if
   a contract change and its consumers can move in **one atomic commit**.
2. **The repository must stay understandable** (`PROJECT_MANIFEST.md`
   §Repository Philosophy): clear folder ownership, documentation as production
   code.
3. **The repository is polyglot.** TypeScript for the frontend, Python for the
   backend and the ML stack, and — pending ADR-004 — possibly Node for the worker
   tier (audit C-01).

`PROJECT_MANIFEST.md` locks Turborepo and pnpm. This ADR records the rationale
and, more usefully, the costs being accepted.

## Decision

A single repository, managed as a **pnpm workspace** with **Turborepo** as the
task orchestrator, containing `apps/`, `services/`, `packages/`,
`infrastructure/` and `docs/`.

pnpm workspaces cover the JavaScript/TypeScript packages. Python services live in
`services/` alongside them but are **not** pnpm workspaces; they are managed by
Python packaging, and Turborepo invokes their tasks through per-service scripts.

## Alternatives considered

### Alternative A — Polyrepo (one repository per service)

Plausible: strongest possible enforcement of boundaries, independent release
cadences, smaller checkouts, no tooling required to explain the structure.

Rejected because it makes the one thing that must be atomic — a contracts change
plus its nine consumers — into a nine-PR coordination problem. For a
single-maintainer project at foundation stage, that is not boundary enforcement,
it is a permanent tax. It also fragments the documentation that
`PROJECT_MANIFEST.md` treats as production code.

### Alternative B — Nx

Plausible: a stronger feature set than Turborepo — generators, dependency-graph
constraints (`@nx/enforce-module-boundaries`, which would enforce the
`service-boundaries.md` §4 matrix mechanically), and first-class polyglot
plugins.

Rejected because it was not the locked choice, and because its configuration
surface is significantly larger. Nx's module-boundary enforcement is a real loss
and is recorded in Cons below; it is partially recoverable via ESLint
`no-restricted-imports` (`packages/eslint-config`).

### Alternative C — pnpm workspaces with no task orchestrator

Plausible: fewer moving parts. `pnpm -r run build` already exists.

Rejected because there is no task graph and no caching. Every CI run would
rebuild and re-test everything. That cost is small today with two packages and
becomes the dominant CI cost within a year.

### Alternative D — Separate TypeScript and Python repositories

Plausible: each language uses its native tooling with no impedance mismatch.

Rejected for the same reason as A, sharpened: the contracts package generates
**both** TypeScript types and Python Pydantic models from one schema. Splitting
the repository splits the generator from half its output, which is precisely the
drift this architecture is built to prevent.

## Pros

- **Atomic cross-cutting changes.** A contract change and all its consumers land
  in one commit, one review, one CI run. This is the mitigation for audit C-02
  and C-04 and it is the main reason for the decision.
- **One source of truth for domain types**, mechanically shared rather than
  copied.
- **Task graph and caching.** Turborepo only rebuilds and retests what changed.
  With nine contexts this is the difference between a fast CI and an ignored one.
- **One place for standards.** `.editorconfig`, lint config, CI, and
  `CONTRIBUTING.md` apply everywhere by construction.
- **Documentation next to the code it describes**, which is what
  `PROJECT_MANIFEST.md` §Repository Philosophy requires.
- **Refactoring across boundaries is possible.** Moving a responsibility between
  contexts is a normal PR, not a migration project — this matters a lot while
  boundaries are still being validated.

## Cons

Stated concretely, because these are the costs being accepted:

- **Turborepo is a JavaScript-first tool in a majority-Python repository.**
  Python tasks are invoked through shell scripts wrapped in `package.json`
  scripts. Turborepo's input hashing does not understand Python imports, so
  Python task caching will be coarser and occasionally wrong-in-the-safe-direction
  (cache miss, not stale hit). This is real friction, not a theoretical one.
- **No mechanical enforcement of the dependency matrix.** Nx would enforce
  `service-boundaries.md` §4 through configuration. Here it is enforced by lint
  rules and review, both of which can be bypassed by someone in a hurry.
- **Boundaries are easier to violate.** Everything is one import away. In a
  polyrepo, calling another service's internals is impossible; here it is a typo
  away from compiling. This is the single largest risk of the decision.
- **CI must be path-filtered or it becomes slow.** Without filtering, every PR
  runs every job.
- **The repository will get large** — Playwright, ML dependencies, model
  references. Checkout and CI setup time grow.
- **Node is required to build a Python service.** A backend-only contributor
  still needs pnpm and Node installed to run the standard task commands.

## Future impact

**Becomes easy:** changing a contract across all consumers; extracting a context
into its own process (the code already sits behind an interface); adding a new
context; keeping documentation and code in sync.

**Becomes hard:** enforcing boundaries mechanically; per-service independent
release cadence; keeping the repository small; onboarding someone who only needs
one service.

**Revisit if:** the team grows past roughly ten people with distinct service
ownership; CI time exceeds ~15 minutes on a typical PR even with filtering; or
the Python-side Turborepo friction becomes a daily complaint rather than an
occasional one.

**Cost of reversal:** moderate and decreasing over time. Splitting a monorepo is
mechanical (`git filter-repo` preserves history); the hard part is that
`packages/contracts` must then become a published, versioned artifact with its
own release process, and every service must handle version skew. Budget weeks,
not months — and note that the reverse direction (merging polyrepos later) is
cheaper still, which is a further argument for starting here.

## Compliance with authoritative specifications

- `PROJECT_MANIFEST.md` §Technology Stack — Turborepo and pnpm are the locked
  choices. Satisfied.
- `PROJECT_MANIFEST.md` §Repository Philosophy — clear folder ownership
  (`CODEOWNERS`, per-folder READMEs), documentation as production code.
  Satisfied.
- `docs/CLAUDE.md` §Core principles — "avoid premature microservices". The
  monorepo actively supports the modular-monolith-first topology in
  `service-boundaries.md` §2, because deployment grouping is independent of
  repository layout. Satisfied.
- **Tension recorded:** the "everything is one import away" risk works against
  "do not silently change architecture". Mitigated by the dependency matrix
  (`service-boundaries.md` §4), planned `no-restricted-imports` lint rules, and
  `CODEOWNERS` on cross-cutting paths. Mitigation is partial and known.
