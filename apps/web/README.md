# `apps/web` — Research console (planned)

**Status:** not implemented. Scaffolding is Mission 0.2 or later.
Dashboards and user workflows are explicitly forbidden during Sprint 0
(`PROJECT_MANIFEST.md` §Forbidden During Foundation).

## Future responsibility

The single human interface to the Opportunity Research Engine:

- create Research Projects and launch Research Sessions within them,
- monitor a session's status and coverage,
- browse and filter opportunities,
- inspect the evidence behind any score,
- compare an opportunity across `MarketScope` values, including per-country,
- see which sessions discovered or corroborated an opportunity (Ontology V2 §12),
- review low-confidence conclusions flagged for human review
  (`llm-reasoning-rules.md` §11).

## Stack (locked)

Next.js 15 (App Router) · TypeScript · Tailwind · shadcn/ui. See
`docs/architecture/adr/ADR-002-nextjs-frontend.md`.

## Boundaries

**Inputs:** the gateway HTTP API only. All requests are workspace-scoped
(ADR-005); the workspace is resolved at the gateway, never chosen by the client.

**Outputs:** rendered UI. No writes to any datastore.

**Dependencies:** `services/gateway`, `packages/contracts`, `packages/ui`.

## Design constraints inherited from the specifications

1. **No single ranking number.** The five score families (Opportunity, Evidence,
   Execution, Research Completeness, Model Confidence) must never be collapsed
   into one displayed value or one sort key
   (`scoring-framework-v1.1.md` §2). A default sort by Opportunity Score alone,
   without the Evidence Score visible beside it, is the most likely accidental
   violation in the entire product.
2. **Evidence is always reachable.** Every score must be one interaction away
   from the evidence that produced it (`llm-reasoning-rules.md` §11).
3. **No false precision.** Display rounded integers. `82.37` is forbidden
   (`scoring-framework-v1.1.md` §10).
4. **Country scores are not decoration.** A global score must not hide
   meaningful country-level divergence (`opportunity-ontology-v1.1.md` §4).
5. **Confidence is presented as a percentage, stored as a unit interval.**
   `0.82` → `82%` (`scoring-framework-v1.1.md` §4.1). Scores render on 0–100.
   `Model Confidence` is a *score family* on 0–100, not a confidence field — the
   UI must not render the two identically.
6. **Claim types are always visible.** Five values, never conflated:
   `OBSERVED`, `INFERRED`, `PREDICTED`, `RECOMMENDED`, `HYPOTHESIS`.
   `HYPOTHESIS` in particular must be visually distinct — it is the label that
   stops a plausible idea from reading as a finding.
7. **Untrusted content rendering.** Opportunity text derives from scraped
   sources. It is rendered as text, never as HTML, and never interpolated into a
   client-side prompt.
8. **Expired evidence renders as expired.** Under
   `data-retention-policy-v1.md`, a score outlives the evidence that produced it.
   A dangling evidence reference shows "evidence expired" — never an error, and
   never silently as "no evidence".
