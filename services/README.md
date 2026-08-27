# `services/` — Bounded contexts

## Responsibility

Each directory here is one **bounded context** with a single responsibility, an
explicit contract, and its own tests. It is the unit of ownership in this system.

## A boundary is not a process

`docs/CLAUDE.md` forbids premature microservices; the architecture defines nine
services. Both are satisfied by separating two decisions
(see `docs/architecture/specification-audit.md` C-03):

- **The boundary is a contract.** Fixed here, in these directories. Crossing it
  requires going through a declared interface.
- **The process count is a deployment choice.** Initially small. Extraction to a
  separate process is a deployment change, not a redesign, precisely because the
  boundary was drawn first.

See `docs/architecture/service-boundaries.md` §2 for the deployment topology.

## The nine contexts

| Service | One-line responsibility | Runtime |
|---------|------------------------|---------|
| `gateway` | The only public entry point | Python / FastAPI |
| `research-orchestrator` | Plans and drives a `ResearchSession` | Python / FastAPI |
| `acquisition` | Lawfully collects raw external data | Python (Playwright) |
| `nlp` | Turns text into structured signals | Python |
| `scoring` | Computes the five score families | Python |
| `market-intelligence` | Market sizing, trends, geography | Python |
| `competition` | Competitor mapping and Competition Gap | Python |
| `execution` | MVP plans and go-to-market strategies | Python |
| `workers` | Executes queued jobs | Python / Celery |

All backend contexts are Python (ADR-004). Jobs run on Celery over Redis. There
is no Node worker tier; TypeScript is confined to `apps/web` and `packages/*`.

## Rules that apply to every service

1. **One responsibility.** If you cannot state it in one sentence without "and",
   the boundary is wrong.
2. **No shared database tables across contexts.** A context owns its tables. Other
   contexts read through its interface, not through its schema.
3. **Contracts come from `packages/contracts`.** No service declares its own copy
   of a domain enum.
4. **Provenance in, provenance out.** No service may drop the source, timestamp,
   extraction method or confidence attached to a value it processes.
5. **No service invents a fact.** A service with insufficient evidence returns a
   hypothesis with low confidence, or an explicit "insufficient evidence" state.
   It never fills the gap (`evidence-confidence-framework-v1.md` §9).
6. **Every service is testable without the network.** I/O is injected at the edge.
7. **Every service declares its failure modes** in its own README before it is
   implemented.
8. **Every tenant-scoped operation takes `workspace_id` explicitly** (ADR-005).
   Required argument, never optional, never defaulted, never resolved inside the
   service. A signature that allows it to be omitted will eventually be called
   without it.
9. **No service imports an LLM provider SDK** (ADR-006). LLM access goes through
   the LLM Gateway, requesting a logical tier rather than a model name.
10. **Claim types and confidence follow the canonical form**: five UPPERCASE
    values, confidence on `[0,1]`. See `docs/CLAUDE.md` §Canonical invariants.
11. **Lifecycle names are canonical** (Ontology V2 §11): `ResearchProject`,
    `ResearchSession`, `ResearchContext`. `research run` is retired and no
    `ResearchRun` entity exists.
12. **Domain taxonomies are registry lookups, not enums** (Ontology V2 §14).
    A service that hard-codes a product type or a distribution channel has
    reintroduced the migration-per-concept problem the registry split prevents.

## Not here

- HTTP presentation → `apps/web`
- Cross-service types → `packages/contracts`
- Dockerfiles and compose → `infrastructure/`
