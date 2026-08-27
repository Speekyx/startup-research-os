"""Gateway configuration.

Validated at startup: a service that boots with a missing DATABASE_URL and
discovers it on the first request has turned a configuration error into a
production incident.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

__all__ = ["Settings", "load_settings", "ConfigurationError"]


class ConfigurationError(RuntimeError):
    """Raised at startup when required configuration is missing."""


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
    qdrant_url: str

    service_name: str = "sros-gateway"
    environment: str = "development"
    log_level: str = "INFO"

    # ADR-005: a convenience for local development, NEVER a code path. No
    # repository may fall back to it; it is resolved once, at the edge, and only
    # while authentication does not exist.
    dev_workspace_id: str | None = None

    db_pool_min: int = 1
    db_pool_max: int = 10

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


REQUIRED = ("DATABASE_URL", "REDIS_URL", "QDRANT_URL")


def load_settings(env: dict[str, str] | None = None) -> Settings:
    source = env if env is not None else dict(os.environ)

    missing = [name for name in REQUIRED if not source.get(name)]
    if missing:
        raise ConfigurationError(
            f"missing required configuration: {missing}. "
            "Copy infrastructure/compose/.env.example and export it."
        )

    environment = source.get("ENVIRONMENT", "development")
    dev_workspace = source.get("DEV_WORKSPACE_ID") or None

    if environment != "development" and dev_workspace:
        raise ConfigurationError(
            "DEV_WORKSPACE_ID is set outside development. The development "
            "workspace is a local convenience and must never resolve tenants "
            "in a deployed environment (ADR-005)."
        )

    return Settings(
        database_url=source["DATABASE_URL"],
        redis_url=source["REDIS_URL"],
        qdrant_url=source["QDRANT_URL"],
        service_name=source.get("SERVICE_NAME", "sros-gateway"),
        environment=environment,
        log_level=source.get("LOG_LEVEL", "INFO"),
        dev_workspace_id=dev_workspace,
        db_pool_min=int(source.get("DB_POOL_MIN", "1")),
        db_pool_max=int(source.get("DB_POOL_MAX", "10")),
    )
