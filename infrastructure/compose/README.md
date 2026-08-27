# `infrastructure/compose` — Local development stack (planned)

**Status:** not implemented.

## Purpose

One command to get a working local environment. The target is that a new
contributor runs `docker compose up` and has PostgreSQL, Redis and Qdrant
running, with schemas applied, in under two minutes.

## Planned files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Backing services only: PostgreSQL, Redis, Qdrant |
| `docker-compose.services.yml` | Application services, for full-stack local runs |
| `docker-compose.override.yml.example` | Per-developer overrides (git-ignored once copied) |
| `.env.example` | Documented environment shape, placeholder values only |

Splitting backing services from application services matters: day-to-day, a
developer runs the backing services in Docker and the service they are editing on
the host, with a debugger attached. Forcing everything into containers makes that
workflow painful and people stop using compose at all.

## Rules

1. **Pinned versions** — `postgres:16.4`, `redis:7.4`, `qdrant/qdrant:v1.11.0`.
   Never `latest`.
2. **Health checks on every service**, with dependencies expressed as
   `condition: service_healthy`.
3. **Named volumes**, all git-ignored.
4. **No secret in any committed compose file.** Values come from `.env`, which is
   git-ignored; `.env.example` carries placeholders only.
5. **Non-default local ports** where a clash is likely, so the stack does not
   fight a locally installed PostgreSQL.

## Redis is a broker, not just a cache

With Celery (ADR-004), Redis holds in-flight job state. **Enable AOF persistence
locally**, and configure `acks_late` and visibility timeouts deliberately — the
point is to observe job-loss behavior in development rather than discover it in
production. A local Redis with default settings will silently lose jobs on
restart, and that is exactly the lesson worth learning cheaply.

## Seed the development workspace

`bootstrap-local.sh` seeds a single **default development workspace** with a
fixed, well-known UUID (ADR-005). The gateway resolves it from configuration
while authentication does not exist.

It is a development convenience, **never a code path**: no service, repository or
task may fall back to it when `workspace_id` is missing. Integration tests seed
**at least two** workspaces, because a suite with one workspace cannot detect a
missing tenant filter.

## Local is not production

This stack has no persistence guarantees, no backups, no resource limits, no
secrets management and no TLS. It exists for development. Production topology is
deferred to a future ADR (ADR-007), and some failure classes are structurally
undiscoverable here.
