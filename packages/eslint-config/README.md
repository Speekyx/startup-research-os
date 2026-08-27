# `packages/eslint-config` — Shared lint rules

**Status:** config written (`index.js`). Not yet runnable: ESLint and
`typescript-eslint` are not installed, and there is no lockfile. The rules are
fixed so the config implements a decision rather than a default.

**Cannot be automated yet, so it stays in review** (documented per Mission 0.2
§24): cross-context import detection needs real service directories to match
against, and `no-unnecessary-condition` needs type information, which needs a
`tsc` project — both land with the first service package.

See `docs/architecture/quality-gates.md` §3 for the full lint strategy.

## Planned entry points

| Export | For |
|--------|-----|
| `base` | Any TypeScript |
| `library` | `packages/*` |
| `next` | `apps/web` |

## Rules that carry specification weight

Most lint rules are style. These are not — each one blocks a specific
specification violation, which is why they belong in a shared config rather than
in a review checklist:

| Rule | Blocks |
|------|--------|
| `no-restricted-imports` on cross-service paths | A service importing another service's internals instead of its contract |
| `no-restricted-syntax` on locally declared domain enums | The C-02 drift: a domain enum redeclared outside `packages/contracts` |
| `no-restricted-syntax` on registry taxonomies declared as unions/enums | Undoing A-07: encoding an extensible registry as a closed type reintroduces migration-per-concept (Ontology V2 §14.3) |
| `no-restricted-imports` on provider SDKs | A business service importing Anthropic/OpenAI/Gemini instead of using the LLM Gateway (ADR-006) |
| `@typescript-eslint/no-explicit-any` | Untyped data crossing a boundary where provenance should be attached |
| `@typescript-eslint/no-floating-promises` | Silently dropped async work — in a pipeline, a lost job is lost evidence |
| `@typescript-eslint/switch-exhaustiveness-check` | An unhandled claim type or score family |
| `no-restricted-globals` on `process.env` outside config modules | Environment access scattered through domain code |
| `react/no-danger` | Rendering scraped content as HTML |

## Deliberate omissions

- **No formatting rules.** Prettier owns formatting. Overlapping the two produces
  conflicts nobody wants to debug.
- **No rule that can only be satisfied by disabling it.** A rule that gets a
  blanket `eslint-disable` at the top of half the files is worse than no rule.
