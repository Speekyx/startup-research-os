"""MarketScope: the canonical geographic scope of an analysis.

Ontology V2 §4. Geographic axis only -- audience/segment scoping is A-12 and is
deliberately NOT modelled here.

Canonicalization matters more than it looks: a scope is used as a cache key, a
dedup key and an equality test, so the same scope written two ways must produce
one representation. That is why construction normalizes rather than merely
validating.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import ContractError
from .generated.domain import COUNTRY_CODE_PATTERN, MarketScopeType

_COUNTRY = re.compile(COUNTRY_CODE_PATTERN)
_REGION = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")

__all__ = ["MarketScope", "MarketScopeType"]


@dataclass(frozen=True)
class MarketScope:
    """An immutable, canonicalized geographic scope.

    Construct through the classmethods, or through :meth:`from_json`.
    """

    type: MarketScopeType
    countries: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()

    # -- constructors -------------------------------------------------------

    @classmethod
    def global_(cls) -> MarketScope:
        return cls(type=MarketScopeType.GLOBAL)

    @classmethod
    def country(cls, code: str) -> MarketScope:
        return cls.from_json({"type": "COUNTRY", "countries": [code]})

    @classmethod
    def multi_country(cls, codes: list[str]) -> MarketScope:
        return cls.from_json({"type": "MULTI_COUNTRY", "countries": list(codes)})

    @classmethod
    def region(cls, regions: list[str]) -> MarketScope:
        return cls.from_json({"type": "REGION", "regions": list(regions)})

    # -- validation ---------------------------------------------------------

    def __post_init__(self) -> None:
        if not isinstance(self.type, MarketScopeType):
            raise ContractError("market_scope.type", f"unknown scope type {self.type!r}")

        for code in self.countries:
            if not _COUNTRY.match(code):
                raise ContractError(
                    "market_scope.countries",
                    f"{code!r} is not an ISO 3166-1 alpha-2 code (pattern {COUNTRY_CODE_PATTERN})",
                )
        for region in self.regions:
            if not _REGION.match(region):
                raise ContractError(
                    "market_scope.regions", f"{region!r} is not a valid region identifier"
                )

        n_countries, n_regions = len(self.countries), len(self.regions)

        if self.type is MarketScopeType.GLOBAL:
            if n_countries or n_regions:
                raise ContractError(
                    "market_scope",
                    "GLOBAL carries no members. Absence of scope is GLOBAL, "
                    "never an empty list on another type.",
                )
        elif self.type is MarketScopeType.COUNTRY:
            if n_regions:
                raise ContractError("market_scope", "COUNTRY carries no regions")
            if n_countries != 1:
                raise ContractError(
                    "market_scope",
                    f"COUNTRY carries exactly one country code, got {n_countries}. "
                    "Two or more is MULTI_COUNTRY.",
                )
        elif self.type is MarketScopeType.MULTI_COUNTRY:
            if n_regions:
                raise ContractError("market_scope", "MULTI_COUNTRY carries no regions")
            if n_countries < 2:
                raise ContractError(
                    "market_scope",
                    f"MULTI_COUNTRY carries two or more country codes, got {n_countries}. "
                    "One is COUNTRY.",
                )
        elif self.type is MarketScopeType.REGION:
            if n_countries:
                raise ContractError("market_scope", "REGION carries no countries")
            if n_regions < 1:
                raise ContractError("market_scope", "REGION carries at least one region")

    # -- serialization ------------------------------------------------------

    @classmethod
    def from_json(cls, data: object) -> MarketScope:
        if not isinstance(data, dict):
            raise ContractError("market_scope", "expected an object")

        unknown = set(data) - {"type", "countries", "regions"}
        if unknown:
            raise ContractError("market_scope", f"unknown fields: {sorted(unknown)}")

        raw_type = data.get("type")
        if raw_type is None:
            raise ContractError("market_scope.type", "discriminator 'type' is required")
        try:
            scope_type = MarketScopeType(raw_type)
        except ValueError:
            known = ", ".join(m.value for m in MarketScopeType)
            hint = ""
            if isinstance(raw_type, str) and raw_type.upper() == "SEGMENT":
                hint = (
                    " Segment scoping is A-12 and is not implemented; "
                    "MarketScope is geographic only."
                )
            raise ContractError(
                "market_scope.type", f"unknown scope type {raw_type!r}. Known: {known}.{hint}"
            ) from None

        countries = _canonical_countries(data.get("countries", []))
        regions = _canonical_regions(data.get("regions", []))
        return cls(type=scope_type, countries=countries, regions=regions)

    def to_json(self) -> dict[str, object]:
        out: dict[str, object] = {"type": self.type.value}
        if self.countries:
            out["countries"] = list(self.countries)
        if self.regions:
            out["regions"] = list(self.regions)
        return out

    # -- identity -----------------------------------------------------------

    def key(self) -> str:
        """A stable cache/dedup key. Equal scopes always produce equal keys."""
        if self.type is MarketScopeType.GLOBAL:
            return "GLOBAL"
        members = self.countries or self.regions
        return f"{self.type.value}:{','.join(members)}"

    def __str__(self) -> str:
        return self.key()


def _canonical_countries(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ContractError("market_scope.countries", "expected a list")
    codes = []
    for item in value:
        if not isinstance(item, str):
            raise ContractError("market_scope.countries", "country codes must be strings")
        codes.append(item.strip().upper())
    return tuple(sorted(set(codes)))


def _canonical_regions(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ContractError("market_scope.regions", "expected a list")
    regions = []
    for item in value:
        if not isinstance(item, str):
            raise ContractError("market_scope.regions", "region ids must be strings")
        regions.append(item.strip().lower())
    return tuple(sorted(set(regions)))
