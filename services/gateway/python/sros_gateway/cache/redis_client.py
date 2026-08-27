"""Tenant-scoped Redis access.

Conceptually separate from the Celery broker configuration (ADR-004): this is
application caching and transient coordination. Redis remains **non-canonical**
(ADR-008) — nothing here is a source of truth, and losing all of it costs a cold
cache.

**Why a wrapper.** A cache key without a tenant prefix leaks across workspaces
with no database query involved, so it never appears in a SQL audit. That makes
it one of the two least visible leak paths in the system (the other is vector
search). The prefix is therefore built here, once, and callers never concatenate
keys themselves.
"""

from __future__ import annotations

from typing import Any

from sros_contracts import ContractError, WorkspaceId

__all__ = ["TenantCache", "GlobalCache", "cache_key"]

_NAMESPACE = "sros"


def cache_key(workspace_id: str, namespace: str, *parts: str) -> str:
    """Build a tenant-scoped physical key.

    Shape: ``sros:ws:<workspace_id>:<namespace>:<parts...>``

    The workspace comes first so that a `SCAN` by tenant is possible and a
    mis-scoped key is visible at a glance in `redis-cli --scan`.
    """
    if not workspace_id:
        raise ContractError(
            "workspace_id",
            "a tenant-scoped cache key requires an explicit workspace_id (ADR-005)",
        )
    if not namespace:
        raise ContractError("namespace", "a cache namespace is required")
    for part in parts:
        if not part:
            raise ContractError("key", "empty cache key segment")
    tail = ":".join(parts)
    return (
        f"{_NAMESPACE}:ws:{workspace_id}:{namespace}:{tail}"
        if tail
        else (f"{_NAMESPACE}:ws:{workspace_id}:{namespace}")
    )


class TenantCache:
    """Cache access bound to exactly one workspace.

    The workspace is supplied when the accessor is built, and every key it
    produces carries it. There is no method that reaches outside the tenant.
    """

    def __init__(self, client: Any, workspace_id: WorkspaceId | str) -> None:
        if not workspace_id:
            raise ContractError(
                "workspace_id",
                "TenantCache requires an explicit workspace_id; there is no default",
            )
        self._client = client
        self._workspace_id = str(workspace_id)

    @property
    def workspace_id(self) -> str:
        return self._workspace_id

    def key(self, namespace: str, *parts: str) -> str:
        return cache_key(self._workspace_id, namespace, *parts)

    def get(self, namespace: str, *parts: str) -> bytes | None:
        result: bytes | None = self._client.get(self.key(namespace, *parts))
        return result

    def set(
        self, namespace: str, *parts: str, value: bytes | str, ttl_seconds: int | None = None
    ) -> None:
        self._client.set(self.key(namespace, *parts), value, ex=ttl_seconds)

    def delete(self, namespace: str, *parts: str) -> int:
        return int(self._client.delete(self.key(namespace, *parts)))

    def exists(self, namespace: str, *parts: str) -> bool:
        return bool(self._client.exists(self.key(namespace, *parts)))

    def scan_workspace(self, namespace: str | None = None) -> list[str]:
        """List this workspace's keys. Used by tests and by tenant deletion."""
        pattern = (
            f"{_NAMESPACE}:ws:{self._workspace_id}:{namespace}:*"
            if namespace
            else f"{_NAMESPACE}:ws:{self._workspace_id}:*"
        )
        return [
            k.decode() if isinstance(k, bytes) else str(k)
            for k in self._client.scan_iter(match=pattern)
        ]


class GlobalCache:
    """Non-tenant cache, for genuinely global reference data only.

    Registries and the source registry are global (ADR-008). Everything else is
    tenant-scoped, and using this class for tenant data is a leak — hence the
    separate, deliberately awkward name.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    def key(self, namespace: str, *parts: str) -> str:
        tail = ":".join(parts)
        return (
            f"{_NAMESPACE}:global:{namespace}:{tail}"
            if tail
            else (f"{_NAMESPACE}:global:{namespace}")
        )

    def get(self, namespace: str, *parts: str) -> bytes | None:
        result: bytes | None = self._client.get(self.key(namespace, *parts))
        return result

    def set(
        self, namespace: str, *parts: str, value: bytes | str, ttl_seconds: int | None = None
    ) -> None:
        self._client.set(self.key(namespace, *parts), value, ex=ttl_seconds)


def ping(client: Any) -> bool:
    """Readiness probe. Reports state; does not raise."""
    try:
        return bool(client.ping())
    except Exception:
        return False
