"""FastAPI application factory.

The gateway is an **adapter**, not a brain (service-boundaries.md). It validates
at the edge, resolves tenant and correlation context, and delegates. No domain
logic lives here.

Two endpoint families, deliberately different:

  /health  -- is this process alive? Does NOT depend on PostgreSQL. A liveness
              probe that fails when a database blips gets the container killed
              during an outage, which turns a degradation into an outage.
  /ready   -- can this process serve traffic? Checks PostgreSQL and Redis.

Business APIs live under /api/v1.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sros_contracts import CONTRACT_VERSION, ONTOLOGY_VERSION, ContractError, WorkspaceId

from .config import Settings, load_settings
from .context import RequestContext, TenantContextMissingError
from .db.pool import Database, TenantScopeError
from .db.repositories import InvalidTransitionError, NotFoundError

CORRELATION_HEADER = "x-correlation-id"
WORKSPACE_HEADER = "x-workspace-id"

log = logging.getLogger("sros.gateway")


def _configure_logging(settings: Settings) -> None:
    """Structured logs carrying correlation, never raw research content."""
    logging.basicConfig(
        level=settings.log_level,
        format='{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or load_settings()
    _configure_logging(resolved)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> Any:
        database = Database(
            resolved.database_url,
            min_size=resolved.db_pool_min,
            max_size=resolved.db_pool_max,
            app_role=resolved.app_db_role,
        )
        database.open()
        app.state.settings = resolved
        app.state.db = database

        import redis as redis_lib

        app.state.redis = redis_lib.Redis.from_url(resolved.redis_url)
        app.state.qdrant_url = resolved.qdrant_url
        log.info("gateway started environment=%s", resolved.environment)
        try:
            yield
        finally:
            database.close()
            app.state.redis.close()
            log.info("gateway stopped")

    app = FastAPI(
        title="Startup Research OS — Gateway",
        version=CONTRACT_VERSION,
        description=(
            "The only public entry point. Contract version "
            f"{CONTRACT_VERSION}, ontology V{ONTOLOGY_VERSION}."
        ),
        lifespan=lifespan,
    )

    # ------------------------------------------------------ error shaping

    def _error(request: Request, status: int, error: str, detail: str) -> JSONResponse:
        context = getattr(request.state, "context", None)
        correlation_id = context.correlation_id if context else "unknown"
        log.warning(
            "request failed error=%s status=%s correlation_id=%s",
            error,
            status,
            correlation_id,
        )
        return JSONResponse(
            status_code=status,
            content={"error": error, "detail": detail, "correlation_id": correlation_id},
            headers={CORRELATION_HEADER: correlation_id},
        )

    # ---------------------------------------------------------- middleware

    @app.middleware("http")
    async def correlation_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Any]]
    ) -> Any:
        """Assign or accept a correlation id, and resolve tenant context.

        The workspace is resolved HERE, once, at the edge. Nothing below this
        line reaches for it (ADR-005).
        """
        correlation_id = request.headers.get(CORRELATION_HEADER) or str(uuid.uuid4())

        raw_workspace = request.headers.get(WORKSPACE_HEADER)
        if not raw_workspace and resolved.is_development and resolved.dev_workspace_id:
            # Development convenience only. `load_settings` refuses to carry a
            # dev workspace outside development, so this branch cannot fire in
            # a deployed environment.
            raw_workspace = resolved.dev_workspace_id

        workspace_id: WorkspaceId | None = None
        if raw_workspace:
            # Validated at the edge. A malformed header becomes a 422 here
            # rather than a database error three layers down.
            try:
                workspace_id = WorkspaceId(raw_workspace)
            except ContractError as exc:
                return _error(request, 422, "contract_violation", f"{exc.field}: {exc.reason}")

        request.state.context = RequestContext(
            correlation_id=correlation_id,
            workspace_id=workspace_id,
            service_name=resolved.service_name,
        )

        response = await call_next(request)
        response.headers[CORRELATION_HEADER] = correlation_id
        return response

    # ------------------------------------------------------ error handlers

    @app.exception_handler(ContractError)
    async def _contract_error(request: Request, exc: ContractError) -> JSONResponse:
        return _error(request, 422, "contract_violation", f"{exc.field}: {exc.reason}")

    @app.exception_handler(TenantContextMissingError)
    async def _tenant_missing(request: Request, exc: TenantContextMissingError) -> JSONResponse:
        # 400, not 401: authentication does not exist yet. What is missing is a
        # workspace, and saying so is more useful than a misleading 401.
        return _error(request, 400, "workspace_required", str(exc))

    @app.exception_handler(TenantScopeError)
    async def _tenant_scope(request: Request, exc: TenantScopeError) -> JSONResponse:
        # Same shape as a missing workspace: the caller's request could not be
        # attributed to a tenant. 400 rather than 500 -- this is a bad request,
        # not a broken server.
        return _error(request, 400, "workspace_required", str(exc))

    @app.exception_handler(NotFoundError)
    async def _not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return _error(request, 404, "not_found", str(exc))

    @app.exception_handler(InvalidTransitionError)
    async def _invalid_transition(request: Request, exc: InvalidTransitionError) -> JSONResponse:
        return _error(request, 409, "invalid_transition", str(exc))

    # ------------------------------------------------------------- routes

    from .api import health, projects, sessions

    app.include_router(health.router)
    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(sessions.router, prefix="/api/v1")

    return app
