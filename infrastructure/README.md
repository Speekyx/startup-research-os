# `infrastructure/` — Runtime environment

## Responsibility

Everything needed to **run** the system, and nothing that decides what it does.
Container definitions, local orchestration, database bootstrap, operational
scripts.

Deliberately **not** a pnpm workspace: it holds Dockerfiles, compose files and
scripts, not publishable packages.

## Contents

| Directory | Status | Purpose |
|-----------|--------|---------|
| `compose/` | **implemented** | Local development stack (PostgreSQL, Redis, Qdrant) |
| `db/` | **implemented** | Schema v1 migrations and development seed |
| `scripts/` | **implemented** | Migration runner and the validators CI runs |
| `docker/` | planned | Per-service Dockerfiles |

## Scripts that run today

Zero-dependency (stdlib only — a check that cannot be skipped because an install
failed, ADR-009):

```bash
python infrastructure/scripts/validate_schema.py       # ADR-008 invariants
python infrastructure/scripts/migrate.py --plan        # no database needed
python infrastructure/scripts/run_python_tests.py      # 65 tests, no install
python infrastructure/scripts/check_env_template.py    # no committed secrets
```

Install-dependent (uv workspace, ADR-010):

```bash
uv run python infrastructure/scripts/migrate.py --apply --seed
uv run python infrastructure/scripts/run_pytest_suites.py
```

All of them run in CI.

## Local networking: use 127.0.0.1, not localhost

The `.env.example` hosts are `127.0.0.1` deliberately. On Windows `localhost`
resolves to `::1` first, Docker publishes these ports on IPv4 only, and every
connection then pays an IPv6 timeout before falling back. Measured in Mission
0.3: **0.01s via 127.0.0.1 versus 15.05s via localhost** — enough to time out
the gateway's connection pool during startup.

## Port selection

Ports are 55432 / 55379 / 55333. Windows reserves several ranges for Hyper-V
(`netsh interface ipv4 show excludedportrange protocol=tcp`), and the original
56333/56379 choices fell inside them, so the containers refused to bind. If a
port is refused with a permissions error rather than "already in use", check
that list before assuming something is running on it.

## Backing services

| Service | Role | Notes |
|---------|------|-------|
| PostgreSQL | System of record | Raw, normalized, signals, evidence, scores, run state. Owns provenance |
| Redis | Celery broker + cache | Job queue and result backend (ADR-004), rate-limit accounting, response cache. **Needs AOF persistence** — it holds in-flight job state, not just cache |
| Qdrant | Vector index | **Derived and rebuildable** (audit A-09). Losing Qdrant costs a re-index, never data |

The A-09 position matters operationally: because Qdrant is derived, it needs no
backup strategy and no HA in early environments. If it were a primary store, both
would be mandatory from day one.

## Hard rules

1. **No secret in any committed file.** Compose files reference environment
   variables; `.env` is git-ignored and `.env.example` documents the shape with
   placeholder values only.
2. **Pinned image versions.** `postgres:16.4`, not `postgres:latest`. A base image
   that changes under you is an unreproducible build.
3. **Non-root containers.** Every service image drops to an unprivileged user.
4. **Health checks on every service.** Compose dependencies use
   `condition: service_healthy`, not `depends_on` alone — Postgres accepting TCP
   is not Postgres ready.
5. **Local data volumes are git-ignored** (`.docker-data/`, `pgdata/`,
   `qdrant_storage/`).

## Deployment posture — ADR-007

**D-10 is resolved for the foundation phase: local-first with Docker Compose.**
Production is deliberately deferred to a future ADR.

Eight portability rules are binding, and they are what keeps "local-first" from
becoming "local-only":

1. Configuration from the environment, never baked into an image.
2. No local filesystem as a system of record.
3. No hard-coded hostnames, ports or connection strings.
4. Services stateless except the three backing stores.
5. No cloud-provider SDK in application code.
6. Migrations as a discrete step, before the new version starts.
7. Health and readiness endpoints on every service.
8. Pinned image versions everywhere.

## Retention — ADR / policy

**D-06 is resolved** by `docs/data/data-retention-policy-v1.md`. It drives volume
planning and, eventually, the backup policy. Deletion must propagate to
PostgreSQL, object storage **and Qdrant** — a vector left behind after its source
record is deleted is still that content, in embedded form.

## Open decisions

- **D-11** — observability stack.
- Production topology, TLS, secrets management, backups, HA — the future
  production ADR.
