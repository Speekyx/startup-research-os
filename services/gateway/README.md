# `services/gateway`

**Status:** implemented (Mission 0.3). The only public entry point.
**Runtime:** Python / FastAPI. **Access:** psycopg 3 + explicit repositories (ADR-011).

## Responsibility

An **adapter**, not a brain. It validates at the edge, resolves tenant and
correlation context, and delegates. No domain logic lives here: `MarketScope`
rules, `ResearchContext` validation and canonicalization all come from
`sros_contracts` (ADR-009), and the Pydantic models adapt rather than redefine
them (ADR-003).

## Running it locally

```bash
docker compose -f infrastructure/compose/docker-compose.yml up -d
```

```bash
uv run python infrastructure/scripts/migrate.py --apply --seed
```

```bash
uv run uvicorn "sros_gateway.app:create_app" --factory --host 127.0.0.1 --port 8412
```

Configuration comes from `infrastructure/compose/.env.example`. Hosts are
`127.0.0.1`, never `localhost` — see §Local networking below.

## Endpoints

### Infrastructure (unversioned, deliberately)

```
GET /health   process liveness
GET /ready    dependency readiness
```

**They answer different questions, and conflating them is expensive.**
`/health` consults **no dependency**: a liveness probe wired to PostgreSQL gets
the container killed during a database blip, turning a degradation into an
outage. `/ready` checks PostgreSQL and Redis and returns 503 when either is
down.

Qdrant is reported under `optional_dependencies` but does **not** gate
readiness: no path served today needs it, and a derived index being cold is not
a reason to refuse all traffic (ADR-008).

```json
{
  "status": "ready",
  "dependencies": { "postgres": "ok", "redis": "ok" },
  "optional_dependencies": { "qdrant": "ok" },
  "correlation_id": "…"
}
```

### Business API (`/api/v1`)

```
POST   /api/v1/research-projects
GET    /api/v1/research-projects
GET    /api/v1/research-projects/{project_id}

POST   /api/v1/research-projects/{project_id}/sessions
GET    /api/v1/research-projects/{project_id}/sessions
GET    /api/v1/research-sessions/{research_session_id}
```

**There is deliberately no `PATCH` for `research_context`, and no delete.**
A session's context snapshot is the reproducibility guarantee; a new
specification means a new session (Ontology V2 §11.3). Project deletion waits
until retention semantics for a project are specified.

## Tenant and correlation context

Resolved **once, at the edge**, in the middleware. Nothing below that line
reaches for a workspace (ADR-005).

| Header | Meaning |
|--------|---------|
| `x-workspace-id` | The tenant. Validated as a UUID here, so a malformed value is a 422 rather than a database error three layers down |
| `x-correlation-id` | Accepted if supplied, generated otherwise. Echoed on every response |

While authentication does not exist, a development workspace may be supplied by
configuration — and `load_settings` **refuses to start** if `DEV_WORKSPACE_ID`
is set outside development. A missing workspace on a tenant-scoped route is a
`400 workspace_required`, never a silent default.

`RequestContext.task_headers()` produces exactly the headers
`sros_workers.TaskContext` expects, so correlation survives the
HTTP → queue → worker hop unchanged.

## Error shape

One shape for every failure, always carrying the correlation id:

```json
{ "error": "contract_violation", "detail": "market_scope: …", "correlation_id": "…" }
```

| Status | `error` | When |
|--------|---------|------|
| 400 | `workspace_required` | No workspace in context. Not 401: authentication does not exist, and a misleading 401 helps nobody |
| 404 | `not_found` | Absent **or belonging to another workspace** — the two are indistinguishable on purpose, because saying "exists elsewhere" is itself a cross-tenant disclosure |
| 409 | `invalid_transition` | A session lifecycle transition Ontology V2 §15 does not allow |
| 422 | `contract_violation` | A domain contract rejected the input |

## Repositories

`db/repositories.py`. Explicit repositories, hand-written SQL, no ORM (ADR-011).

**Every tenant-scoped method takes `workspace_id` as a required first argument**
and puts it in the `WHERE` clause. `_require_workspace()` fails closed on `None`
and `""`. There is no ambient tenant and no default — a method that *could* be
called without a workspace eventually will be, and in a multi-tenant system that
is a data leak rather than a bug.

## Wrappers

| Wrapper | Guards |
|---------|--------|
| `cache/redis_client.py` | Tenant-prefixed cache keys. A key without a tenant prefix leaks across workspaces **with no database query involved**, so it never appears in a SQL audit |
| `vectors/qdrant_client.py` | The workspace filter on every vector operation. Callers cannot pass their own filter, because a parameter that can be passed can be forgotten |

Both are covered by two-workspace isolation tests.

## Local networking

Use `127.0.0.1`, not `localhost`. On Windows `localhost` resolves to `::1`
first; Docker publishes these ports on IPv4 only, so every connection pays an
IPv6 timeout before falling back. Measured in Mission 0.3: **0.01s via
127.0.0.1 versus 15.05s via localhost**, which was enough to time out the
connection pool at startup.

## Tests

```bash
uv run python infrastructure/scripts/run_pytest_suites.py
```

46 integration tests: schema runtime, tenant isolation across PostgreSQL, Redis
and Qdrant, the API surface, and the session lifecycle. They skip cleanly when
the stack is not running rather than failing red.

## Not implemented

Authentication, authorization, research execution, scoring (blocked on D-03),
acquisition (blocked on D-07), and any endpoint that would mutate a context
snapshot.
