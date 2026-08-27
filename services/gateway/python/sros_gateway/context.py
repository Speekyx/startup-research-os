"""Request and tenant context.

Two rules govern this module, and both come from ADR-005:

  1. `workspace_id` is resolved ONCE, at the edge, and passed explicitly
     downwards. Repository code never reaches for it.
  2. Absence fails closed. There is no implicit global workspace, in any
     environment, including local development.

The development workspace exists as a *seed convenience*. It is resolved here,
at the boundary, and never inside a repository -- that separation is what stops
it from becoming the mechanism by which one tenant's data lands in another's.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sros_contracts import WorkspaceId

__all__ = ["RequestContext", "TenantContextMissingError"]


class TenantContextMissingError(RuntimeError):
    """Raised when a tenant-scoped operation has no workspace."""


@dataclass(frozen=True)
class RequestContext:
    """Everything an inbound request carries downstream.

    Mirrors `sros_workers.TaskContext` so that correlation survives the
    HTTP -> queue -> worker hop unchanged.
    """

    correlation_id: str
    workspace_id: WorkspaceId | None = None
    research_session_id: str | None = None
    service_name: str = "sros-gateway"
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def require_workspace(self) -> WorkspaceId:
        """Return the workspace, or fail closed.

        Every tenant-scoped path goes through here rather than reading the
        optional attribute, so a missing tenant is impossible to ignore.
        """
        if self.workspace_id is None:
            raise TenantContextMissingError(
                "no workspace in request context. A tenant-scoped operation "
                "requires an explicit workspace_id; there is no default (ADR-005)."
            )
        return self.workspace_id

    def log_fields(self) -> dict[str, str]:
        """Correlation fields for structured logs. Never raw research content."""
        fields = {
            "service": self.service_name,
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
        }
        if self.workspace_id is not None:
            fields["workspace_id"] = str(self.workspace_id)
        if self.research_session_id is not None:
            fields["research_session_id"] = self.research_session_id
        return fields

    def task_headers(self) -> dict[str, str]:
        """Headers for a Celery task payload (ADR-004 correlation contract)."""
        return {
            "workspace_id": str(self.require_workspace()),
            "research_session_id": self.research_session_id or "",
            "correlation_id": self.correlation_id,
        }
