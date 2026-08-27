"""Registry references and entries.

Ontology V2 §14: evolving taxonomies are registry rows, not enums. This module
declares the *reference* and *entry* shapes; it never enumerates values. Doing so
would recreate the migration-per-concept problem the registry split exists to
prevent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from .errors import ContractError
from .generated.domain import REGISTRY_NAMES, RegistryStatus

_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")

__all__ = ["RegistryRef", "RegistryEntry", "RegistryStatus", "REGISTRY_NAMES"]


@dataclass(frozen=True, order=True)
class RegistryRef:
    """A reference into an extensible registry.

    Persists the **stable identifier**, never the display name. Storing a display
    name means a rename silently rewrites history (Ontology V2 §14.4).
    """

    registry: str
    id: str

    def __post_init__(self) -> None:
        if self.registry not in REGISTRY_NAMES:
            raise ContractError(
                "registry",
                f"unknown registry {self.registry!r}. "
                f"Closed enums (ClaimType, MarketScopeType, ResearchSessionStatus, "
                f"DemandSignalFamily, ScoreFamily) are not registries. "
                f"Known registries: {', '.join(REGISTRY_NAMES)}",
            )
        if not isinstance(self.id, str) or not _ID.match(self.id):
            raise ContractError(
                f"{self.registry}.id",
                f"registry ids are lowercase stable slugs matching {_ID.pattern}, got {self.id!r}",
            )

    def to_json(self) -> dict[str, str]:
        return {"id": self.id, "registry": self.registry}

    @classmethod
    def from_json(cls, data: object) -> RegistryRef:
        if not isinstance(data, dict):
            raise ContractError("registry_ref", "expected an object")
        unknown = set(data) - {"registry", "id"}
        if unknown:
            raise ContractError("registry_ref", f"unknown fields: {sorted(unknown)}")
        if "registry" not in data or "id" not in data:
            raise ContractError("registry_ref", "requires 'registry' and 'id'")
        return cls(registry=data["registry"], id=data["id"])


@dataclass(frozen=True)
class RegistryEntry:
    """One registry row. Ontology V2 §14.4.

    Deprecation, never deletion: a deprecated entry stops being offered for new
    classification but keeps resolving for historical records.
    """

    registry: str
    id: str
    name: str
    version: int = 1
    status: RegistryStatus = RegistryStatus.ACTIVE
    description: str | None = None
    aliases: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        RegistryRef(registry=self.registry, id=self.id)  # reuse the reference validation
        if not self.name:
            raise ContractError(f"{self.registry}.{self.id}.name", "canonical name is required")
        if not isinstance(self.version, int) or isinstance(self.version, bool) or self.version < 1:
            raise ContractError(f"{self.registry}.{self.id}.version", "version starts at 1")
        if not isinstance(self.status, RegistryStatus):
            raise ContractError(
                f"{self.registry}.{self.id}.status", "status must be a RegistryStatus"
            )

    @property
    def ref(self) -> RegistryRef:
        return RegistryRef(registry=self.registry, id=self.id)

    def to_json(self) -> dict[str, object]:
        return {
            "aliases": list(self.aliases),
            "description": self.description,
            "id": self.id,
            "name": self.name,
            "registry": self.registry,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "version": self.version,
        }
