# `packages/ui` — Component library (planned)

**Status:** not implemented. UI work is forbidden during Sprint 0.

## Responsibility

Presentational React components shared by `apps/web` and any future frontend,
built on shadcn/ui and Tailwind.

## Rules

- Components are **presentational**. No data fetching, no business logic, no
  direct service calls.
- Props are typed from `packages/contracts`, never redeclared.
- Accessible by default: keyboard navigable, correct roles, sufficient contrast.
- Theme-aware (light and dark).

## Domain-specific components this library will own

These carry specification obligations, which is why they belong in a shared
library rather than being re-implemented per page:

| Component | Obligation it enforces |
|-----------|------------------------|
| `ScoreDisplay` | Renders a rounded integer, never `82.37` (`scoring-framework-v1.1.md` §10) |
| `ScoreFamilyPanel` | Shows all five families together; makes collapsing them into one number structurally awkward (§2) |
| `ClaimBadge` | Always labels `OBSERVED` / `INFERRED` / `PREDICTED` / `RECOMMENDED` / `HYPOTHESIS` (`evidence-confidence-framework-v1.md` §8) |
| `ConfidenceIndicator` | Renders uncertainty visibly rather than as a number in small text |
| `EvidenceTrail` | Makes evidence reachable from any score (`llm-reasoning-rules.md` §11) |
| `MarketScopeSelector` | Prevents a global score from hiding country divergence (`opportunity-ontology-v1.1.md` §4) |

The point of putting these here: a specification rule enforced by a component is
enforced everywhere the component is used. A specification rule enforced by
convention is enforced until someone is in a hurry.
