# ADR-007 — Local-first deployment with Docker Compose

- **Status:** Accepted
- **Date:** 2026-08-27
- **Deciders:** Project owner (Mission 0.1.1, §11 — explicit human decision)
- **Supersedes:** none
- **Related:** ADR-004, ADR-005, ADR-006, audit **D-10**,
  `infrastructure/README.md`

---

## Context

The audit recorded **D-10**: no environment topology or hosting target had been
chosen, which blocked `infrastructure/` beyond local scaffolding and left the
deployment view marked pending.

The system has zero users and one maintainer. It also has a genuinely
multi-component runtime: FastAPI services, Celery workers, PostgreSQL, Redis,
Qdrant, and eventually a Next.js app. That combination invites premature
platform work — the moment a deployment target is named, its abstractions start
leaking into application code.

## Decision

**Local-first, with Docker Compose as the only defined environment.**

```text
Development   →  Docker Compose
Production    →  TBD, through a future ADR
```

Explicitly **not** introduced now:

- Kubernetes
- AWS-, GCP- or Azure-specific architecture
- any distributed deployment topology

**Every component must remain containerizable**, and no choice may be made that
gratuitously complicates a future cloud deployment.

## The constraint that gives this decision its value

"Local-first" is only useful if it does not become "local-only". The following
are treated as binding portability rules, and they are what a future production
ADR will depend on:

1. **Configuration comes from the environment**, never from a file baked into an
   image and never from code. Twelve-factor in the narrow, practical sense.
2. **No component writes to the local filesystem as a system of record.**
   PostgreSQL is the system of record; large payloads go to an object store
   behind an interface that is filesystem-backed locally and S3-compatible later.
3. **No hard-coded hostnames, ports or connection strings.** Service discovery is
   configuration.
4. **Services are stateless** except the three backing stores. Any state in a
   FastAPI process or a Celery worker is a bug, not a deployment constraint.
5. **No provider-specific SDK anywhere in application code** — the same principle
   as ADR-006, applied to infrastructure. No cloud queue, no cloud secrets
   manager, no cloud-specific storage client in a service.
6. **Migrations run as a discrete step**, before the new version starts, never on
   application boot where replicas race.
7. **Health and readiness endpoints on every service**, because every orchestrator
   that exists needs them.
8. **Pinned image versions.** Never `latest`, in any environment.

A system that honours these eight can be deployed to a single VPS, a container
platform, or Kubernetes without touching application code. A system that violates
any of them has already chosen a target without deciding to.

## Alternatives considered

### Alternative A — Choose a production target now (Kubernetes, ECS, Cloud Run)

Plausible: designing for the real target avoids a later migration.

Rejected. The target's abstractions would immediately shape the code — manifests,
sidecars, provider SDKs, cloud-specific queues — for a system with no users, no
load data and no operational experience. Deployment decisions made without
production telemetry are guesses dressed as architecture, and they are expensive
to unwind precisely because they touch everything.

### Alternative B — Managed PaaS from the start (Vercel + managed Postgres/Redis)

Plausible: near-zero operations, fast to stand up.

Rejected for now, but noted as a strong candidate for the future production ADR.
Two current obstacles: Qdrant and Celery workers with heavy ML dependencies fit
poorly into most PaaS models, and adopting a PaaS early tends to pull
configuration and secrets management into provider-specific shapes.

### Alternative C — No containers, run everything natively

Simplest possible local loop. Rejected: it makes environment reproducibility a
matter of each machine's luck, and it defers containerization to the moment it is
most stressful.

### Alternative D — Docker Compose for backing services only, everything else native

This is in fact the **recommended day-to-day workflow**
(`infrastructure/compose/README.md`), not a competing decision: backing services
in Docker, the service under edit on the host with a debugger attached. Full-stack
compose exists for integration testing and for verifying that the containers
actually work.

## Environments

| Environment | Status | Composition |
|-------------|--------|-------------|
| **Local (default)** | Defined | Backing services in Compose; the service under edit runs natively |
| **Local (full stack)** | Defined | Everything in Compose; used for integration testing and container verification |
| **CI** | Defined | Service containers for PostgreSQL, Redis, Qdrant; pinned versions; no external sources, no live LLM |
| **Staging** | Not defined | Deferred to the production ADR |
| **Production** | Not defined | Deferred to the production ADR |

## Pros

- No premature platform complexity, and no platform abstractions leaking into
  application code before there is anything to deploy.
- Fast, reproducible onboarding: `docker compose up` to a working environment.
- CI mirrors local, so "works on my machine" has a short half-life.
- The portability rules keep every realistic production option open.
- Zero hosting cost during foundation.

## Cons

- **No production path exists yet.** That is a real gap, not a neutral state, and
  it will eventually become urgent under time pressure — which is the worst
  moment to design it.
- **Local Compose does not resemble production** in any of the ways that
  eventually matter: no TLS, no resource limits, no backups, no HA, no secrets
  management. Some failure classes are structurally undiscoverable locally.
- **Portability rules are enforced by discipline**, not by tooling. Nothing fails
  when someone hard-codes a hostname.
- Docker on Windows adds friction (file-watching, volume performance) that the
  primary development machine will encounter.
- Deferring the decision risks it being made implicitly by whoever first needs to
  deploy something.

## Future impact

**Becomes easy:** local development; integration testing; keeping every hosting
option open; migrating to any container platform later.

**Becomes hard:** nothing structural — provided the eight portability rules hold.
If they erode, this decision quietly becomes "local-only" and the future
production ADR inherits a cleanup task.

**Revisit when:** the system needs to run unattended for more than a development
session; or an external user needs access. Either condition triggers the
production ADR.

**Cost of reversal:** low by construction. Adding a production target to a
portable containerized system is additive. The cost only rises if the portability
rules were not enforced — which is why they are enumerated here rather than left
implicit.

## Compliance with authoritative specifications

- `PROJECT_MANIFEST.md` §Required Mindset — "prioritize maintainability over
  speed"; deferring a target until there is evidence to choose it is the
  maintainable move, provided the deferral is explicit (it is, here).
- `docs/CLAUDE.md` §Core principles — "avoid unnecessary complexity and premature
  microservices"; the same reasoning applied to infrastructure.
- `PROJECT_MANIFEST.md` §Security First — secrets never in an image layer, never
  in a committed file; `.env` git-ignored with a placeholder `.env.example`.
- `data-principles.md` §3 — API credentials outside source control, injected at
  runtime.
- ADR-004 — Redis must be configured for broker durability (AOF) even locally, so
  that job-loss behavior is observed in development rather than discovered in
  production.
- **Resolves decision D-10** for the foundation phase. A production ADR remains
  required and is listed in the Mission 0.2 entry criteria as *not* blocking.
