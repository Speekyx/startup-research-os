# ADR-002 — Use Next.js 15 for the frontend

- **Status:** Accepted
- **Date:** 2026-08-27
- **Deciders:** Project owner (locked in `PROJECT_MANIFEST.md` §Technology Stack)
- **Supersedes:** none
- **Related:** ADR-001, `scoring-framework-v1.md` §2 and §10,
  `evidence-confidence-framework-v1.md` §8, `llm-reasoning-rules.md` §7 and §11

---

## Context

The system needs one human interface: a research console for launching runs,
browsing opportunities, and — critically — **inspecting the evidence behind any
score**. `llm-reasoning-rules.md` §11 makes that inspectability a requirement,
not a feature.

The UI's real difficulty is not rendering. It is that this product is
epistemically unusual: it must display uncertainty as a first-class part of every
value. Five score families that must never collapse into one number
(`scoring-framework-v1.md` §2), five claim types that must never be conflated
(`evidence-confidence-framework-v1.md` §8), per-country divergence that must not
be hidden behind a global average (`opportunity-ontology-v1.md` §4), and no false
precision anywhere (`scoring-framework-v1.md` §10).

Characteristics of the workload: read-heavy, data-dense, moderate interactivity,
large lists with server-side filtering, deeply nested drill-down into evidence,
and eventually SEO-irrelevant authenticated views.

`PROJECT_MANIFEST.md` locks Next.js, TypeScript, Tailwind and shadcn/ui.

## Decision

Build `apps/web` with **Next.js 15 (App Router)**, TypeScript, Tailwind and
shadcn/ui. It consumes only the `gateway` HTTP API and holds no domain logic.

Server Components are the default. Client Components are used only where
interactivity requires them. Domain types come from `packages/contracts`.

## Alternatives considered

### Alternative A — Vite + React SPA

Plausible: simplest possible model, no server runtime, no RSC mental overhead,
fastest dev loop. The console is authenticated and needs no SEO, which removes
Next.js's most-cited advantage.

Rejected as the locked choice, but it was the strongest alternative. Its real
cost is data fetching: opportunity lists with heavy server-side filtering, and
evidence trees that are expensive to assemble, would push the SPA toward a
waterfall of client requests or a bespoke BFF — which is a large part of what
Next.js already provides.

### Alternative B — Next.js Pages Router

Plausible: simpler, extremely well understood, no Server Component model to
reason about.

Rejected: it is the legacy router in Next.js 15. Choosing a deprecating API at
foundation for a system meant to last years is a self-inflicted migration.

### Alternative C — Remix / React Router 7

Plausible: an excellent data model for read-heavy apps, simpler than RSC, strong
progressive enhancement.

Rejected as not the locked choice. No decisive advantage over Next.js for this
workload.

### Alternative D — Server-rendered Python (Jinja + htmx) from FastAPI

Plausible and worth stating seriously: the backend is Python, the console is
mostly reads and drill-downs, and this would eliminate an entire language and
build system from the stack.

Rejected because it contradicts the locked stack, and because shadcn/ui plus the
React ecosystem give a far better starting point for the data-dense components
this product needs (evidence trees, score panels, comparison views). But it is
the option that would have made the repository simplest, and that is worth
recording honestly.

## Pros

- **Server Components fit the workload.** Opportunity lists and evidence trees
  are assembled server-side and streamed. No client-side data waterfall, and no
  bespoke BFF.
- **One language across the frontend and `packages/contracts`.** Contract changes
  surface as type errors at build time rather than as runtime shape mismatches.
- **shadcn/ui is source-in-repo, not a dependency.** The domain components in
  `packages/ui` (`ScoreDisplay`, `ClaimBadge`, `ConfidenceIndicator`) need to
  encode specification rules. Owning the component source instead of overriding a
  library's theming is the difference between enforcing a rule and fighting a
  default.
- **Streaming and Suspense** map naturally to a console where a research run
  completes in stages.
- **Mature, well-documented, deep hiring pool.** For a project meant to run for
  years with a changing cast, this matters more than technical elegance.
- **Route-level code splitting** keeps a data-dense console from shipping one
  large bundle.

## Cons

- **RSC is genuinely complex.** The server/client boundary is a real source of
  bugs, and the failure mode (accidentally shipping server data or a secret into
  a client bundle) is a security issue, not a rendering glitch. `apps/web` must
  never hold a service credential.
- **A Node runtime to operate.** The SPA alternative needs only a static host.
  This is an additional deployment unit, and it is real operational surface.
- **Framework coupling.** Next.js has a history of significant model changes
  between major versions. Budget a migration roughly every 18 months.
- **Vendor gravity.** Next.js is optimized for Vercel. Self-hosting works, but the
  well-trodden path bends toward one provider — a constraint to keep in mind when
  D-10 (hosting) is decided.
- **Build times grow** with the app, and Next.js builds are not fast.
- **Overkill at foundation.** For an internal console with no SEO requirement,
  this is more framework than the current requirements justify. That is an
  accepted cost of the locked stack.

## Future impact

**Becomes easy:** data-dense server-rendered views; adding a public marketing or
sharing surface later without a second stack; incremental adoption of streaming;
end-to-end type safety from contract to pixel.

**Becomes hard:** deploying as a static asset bundle; avoiding Next.js major
migrations; keeping the client bundle small as the console grows; onboarding
contributors unfamiliar with the RSC model.

**Revisit if:** the console stays small and fully authenticated with no
server-rendering benefit realized in practice; or a Next.js major version imposes
a migration cost larger than a rewrite in a simpler framework.

**Cost of reversal:** moderate. React components are portable; routing, data
fetching and the server/client split are not. Assume a rewrite of the routing and
data layer, with the component tree largely preserved. Keeping domain components
in `packages/ui` — free of Next.js imports — is what keeps this cost bounded, and
is a rule worth enforcing from the first component.

## Compliance with authoritative specifications

- `PROJECT_MANIFEST.md` §Technology Stack — locked choice. Satisfied.
- `scoring-framework-v1.md` §2 — the five families must not collapse into one
  number. Enforced structurally by `ScoreFamilyPanel` in `packages/ui`, not by
  convention.
- `scoring-framework-v1.md` §10 — no false precision. Enforced by `ScoreDisplay`.
- `evidence-confidence-framework-v1.md` §8 — claim types never conflated.
  Enforced by `ClaimBadge` plus an exhaustive switch (`switch-exhaustiveness-check`).
- `llm-reasoning-rules.md` §11 — evidence must be inspectable. `EvidenceTrail`
  and `GET /v1/opportunities/{id}/evidence` exist for this.
- `llm-reasoning-rules.md` §7 — external content is untrusted. Scraped text is
  rendered as text, never as HTML (`react/no-danger` enabled), and never
  interpolated into a client-side prompt.
- **Constraint recorded:** `apps/web` holds no service credentials and calls only
  `gateway` (`service-boundaries.md` §4). With RSC this is a rule that must be
  actively maintained, because server code and client code sit in the same file
  tree.
