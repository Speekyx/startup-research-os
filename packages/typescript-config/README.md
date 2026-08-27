# `packages/typescript-config`

Shared TypeScript configurations. JSON only, no code, no dependencies.

## Files

| File | For |
|------|-----|
| `base.json` | Everything. Strict settings live here |
| `library.json` | Buildable packages (`composite`, emits declarations) |
| `nextjs.json` | `apps/web` |

## Usage

```jsonc
// apps/web/tsconfig.json
{ "extends": "@sros/typescript-config/nextjs.json" }
```

## Why these settings

`strict` is the baseline, plus four options that are usually omitted and are the
ones that actually catch bugs in a data-heavy system:

- **`noUncheckedIndexedAccess`** — `arr[i]` is `T | undefined`. In a pipeline that
  indexes into evidence arrays and score vectors, this is the difference between
  a type error and a runtime `undefined` rendered as a score.
- **`exactOptionalPropertyTypes`** — distinguishes "absent" from "explicitly
  undefined". This system must distinguish *no evidence* from *evidence of
  absence*; the type system should too.
- **`noImplicitReturns`** and **`noFallthroughCasesInSwitch`** — a switch over the
  claims taxonomy that silently falls through is exactly the conflation
  `evidence-confidence-framework-v1.md` §8 forbids.

Relaxing any of these requires a comment explaining why, in the file that does it.
