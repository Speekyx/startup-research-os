"""Infrastructure endpoints. Deliberately unversioned.

/health and /ready answer different questions, and conflating them is a common
and expensive mistake:

  /health -- is this PROCESS alive? It must NOT fail because PostgreSQL is
             temporarily unavailable. A liveness probe wired to a dependency
             gets the container killed during a database blip, converting a
             degradation into an outage.
  /ready  -- can this process SERVE traffic? PostgreSQL and Redis are required,
             so their failure means "stop sending me requests".

Qdrant is reported but does NOT gate readiness: no path served today needs it,
and a derived index being cold is not a reason to refuse all traffic (ADR-008).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request, Response

from ..cache import redis_client
from ..config import Settings

router = APIRouter(tags=["infrastructure"])


@router.get("/health")
def health(request: Request) -> dict[str, Any]:
    """Process liveness. No dependency is consulted, on purpose."""
    settings: Settings = request.app.state.settings
    return {
        "status": "alive",
        "service": settings.service_name,
        "environment": settings.environment,
    }


@router.get("/ready")
def ready(request: Request, response: Response) -> dict[str, Any]:
    """Dependency readiness. 503 when a required dependency is down."""
    context = request.state.context
    app_state = request.app.state

    dependencies: dict[str, str] = {
        "postgres": "ok" if app_state.db.ping() else "unavailable",
        "redis": "ok" if redis_client.ping(app_state.redis) else "unavailable",
    }

    # Reported separately: informational, never gating.
    optional: dict[str, str] = {"qdrant": _qdrant_state(app_state.qdrant_url)}

    required_ok = all(state == "ok" for state in dependencies.values())
    if not required_ok:
        response.status_code = 503

    return {
        "status": "ready" if required_ok else "not_ready",
        "dependencies": dependencies,
        "optional_dependencies": optional,
        "correlation_id": context.correlation_id,
    }


def _qdrant_state(url: str) -> str:
    """Never raises, never leaks a URL or a credential into the response."""
    try:
        import urllib.request

        with urllib.request.urlopen(f"{url}/healthz", timeout=2) as resp:  # noqa: S310
            return "ok" if resp.status == 200 else "unavailable"
    except Exception:
        return "unavailable"
