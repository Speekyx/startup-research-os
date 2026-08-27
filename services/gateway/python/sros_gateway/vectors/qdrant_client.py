"""Tenant-safe Qdrant access.

Mission 0.2 identified this wrapper as missing. It closes the leak path that
never appears in a SQL audit: **a vector search without a tenant filter returns
another workspace's research**, and nothing in a query review would show it.

Two design rules, both deliberate:

1. **Callers never build a filter.** `TenantVectorStore` is constructed with a
   workspace and injects the filter itself. There is no parameter through which
   a caller can pass their own filter, because a parameter that can be passed
   can be forgotten.
2. **Qdrant is a DERIVED index** (ADR-008, audit A-09). Everything here can be
   rebuilt from PostgreSQL, and nothing business-canonical may live only here.

Infrastructure only. No embedding is computed, no collection is indexed, and no
NLP runs — that is out of scope (Mission 0.3 §33).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sros_contracts import ContractError, WorkspaceId

__all__ = ["TenantVectorStore", "VectorPayload", "workspace_filter", "ping"]

WORKSPACE_FIELD = "workspace_id"
SESSION_FIELD = "research_session_id"


def workspace_filter(
    workspace_id: str, research_session_id: str | None = None, **extra: Any
) -> dict[str, Any]:
    """The ONLY place a tenant filter is constructed.

    Returns a plain dict rather than a qdrant-client model, so the filter shape
    is inspectable in tests without importing the SDK.
    """
    if not workspace_id:
        raise ContractError(
            WORKSPACE_FIELD,
            "a tenant-scoped vector operation requires an explicit workspace_id "
            "(ADR-005). A vector search without a tenant filter returns another "
            "workspace's research and never appears in a SQL audit.",
        )
    must: list[dict[str, Any]] = [{"key": WORKSPACE_FIELD, "match": {"value": workspace_id}}]
    if research_session_id:
        must.append({"key": SESSION_FIELD, "match": {"value": research_session_id}})
    for key, value in sorted(extra.items()):
        must.append({"key": key, "match": {"value": value}})
    return {"must": must}


@dataclass(frozen=True)
class VectorPayload:
    """Payload stored alongside a vector.

    `workspace_id` is mandatory: a point written without it can never be found
    by a tenant-filtered search, and would be invisible to tenant deletion.
    """

    workspace_id: str
    research_session_id: str | None = None
    normalized_record_id: str | None = None
    embedding_model: str | None = None
    embedding_model_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        if not self.workspace_id:
            raise ContractError(WORKSPACE_FIELD, "vector payloads require a workspace_id")
        payload: dict[str, Any] = {WORKSPACE_FIELD: self.workspace_id}
        if self.research_session_id:
            payload[SESSION_FIELD] = self.research_session_id
        if self.normalized_record_id:
            payload["normalized_record_id"] = self.normalized_record_id
        if self.embedding_model:
            payload["embedding_model"] = self.embedding_model
        if self.embedding_model_version:
            payload["embedding_model_version"] = self.embedding_model_version
        return payload


class TenantVectorStore:
    """Vector access bound to exactly one workspace.

    Every method that touches points applies the workspace filter. No method
    accepts a caller-supplied filter.
    """

    def __init__(self, client: Any, workspace_id: WorkspaceId | str) -> None:
        if not workspace_id:
            raise ContractError(
                WORKSPACE_FIELD,
                "TenantVectorStore requires an explicit workspace_id; there is no default",
            )
        self._client = client
        self._workspace_id = str(workspace_id)

    @property
    def workspace_id(self) -> str:
        return self._workspace_id

    def build_filter(self, research_session_id: str | None = None, **extra: Any) -> dict[str, Any]:
        """Expose the filter this store would apply. For tests and diagnostics."""
        return workspace_filter(self._workspace_id, research_session_id, **extra)

    def upsert(
        self,
        collection: str,
        point_id: str,
        vector: list[float],
        payload: VectorPayload,
    ) -> None:
        """Write a point. The payload's workspace must match this store's."""
        if payload.workspace_id != self._workspace_id:
            raise ContractError(
                WORKSPACE_FIELD,
                f"payload workspace {payload.workspace_id!r} does not match this "
                f"store's workspace {self._workspace_id!r}. Cross-tenant writes "
                "are refused rather than silently re-tagged.",
            )
        from qdrant_client.models import PointStruct

        self._client.upsert(
            collection_name=collection,
            points=[PointStruct(id=point_id, vector=vector, payload=payload.to_dict())],
        )

    def search(
        self,
        collection: str,
        vector: list[float],
        limit: int = 10,
        research_session_id: str | None = None,
    ) -> list[Any]:
        """Search WITHIN this workspace. The filter is not optional."""
        from qdrant_client import models

        hits: list[Any] = self._client.search(
            collection_name=collection,
            query_vector=vector,
            query_filter=models.Filter(**_to_models(self.build_filter(research_session_id))),
            limit=limit,
        )
        return hits

    def count(self, collection: str, research_session_id: str | None = None) -> int:
        from qdrant_client import models

        result = self._client.count(
            collection_name=collection,
            count_filter=models.Filter(**_to_models(self.build_filter(research_session_id))),
            exact=True,
        )
        return int(result.count)

    def delete_workspace(self, collection: str) -> None:
        """Remove every point belonging to this workspace.

        Needed by tenant deletion: deletion must propagate to Qdrant, because a
        vector left behind is still that content in embedded form
        (`data-retention-policy-v1.md` §5.2).
        """
        from qdrant_client import models

        self._client.delete(
            collection_name=collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(**_to_models(self.build_filter()))
            ),
        )


def _to_models(raw: dict[str, Any]) -> dict[str, Any]:
    """Translate the plain filter dict into qdrant-client model kwargs."""
    from qdrant_client import models

    return {
        "must": [
            models.FieldCondition(
                key=cond["key"], match=models.MatchValue(value=cond["match"]["value"])
            )
            for cond in raw["must"]
        ]
    }


def ping(client: Any) -> bool:
    """Readiness probe. Reports state; does not raise."""
    try:
        client.get_collections()
        return True
    except Exception:
        return False
