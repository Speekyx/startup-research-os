"""Classifying a source geography code, from reviewed data and nothing else.

Mission 1.6 §15.

**The problem this solves is that a code does not say what it is.** The World
Bank Indicators API returns `FRA` for France and `WLD` for the world in the same
field, both three uppercase letters. Nothing about the string distinguishes a
country from an aggregate, so any rule based on its shape is wrong for one of
them, and mapping the wrong one produces "the population of the country World".

**Three ways to decide, and two of them are forbidden.** Guessing from the shape
is out for the reason above. Guessing from the accompanying label -- `"World"`
does not look like a country -- is inference, and §41 forbids reaching for a
model to do it; a hand-written rule doing the same thing by string matching is
the same guess with worse provenance.

What is left is data: `docs/data/geography-mapping-v1.json`, one reviewed entry
per code, each carrying the `basis` that establishes it. Exactly the discipline
the authorized dataset list is under, and for the same reason -- a bulk import
of 250 codes would be 250 assertions nobody checked.

**A code with no entry is `UNKNOWN`**, keeps its source form, gets no canonical
country code, and marks its record `PARTIAL`. That is the safe failure and it is
never promoted: an unclassified code does not become a country because the
alternative was inconvenient.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

from sros_contracts import NormalizedGeographyKind

from ..registry.models import SourceRegistryError

__all__ = [
    "DEFAULT_GEOGRAPHY_MAP_PATH",
    "GeographyEntry",
    "GeographyMap",
    "find_geography_map",
    "load_geography_map",
]

DEFAULT_GEOGRAPHY_MAP_PATH = "docs/data/geography-mapping-v1.json"


def find_geography_map(start: pathlib.Path | None = None) -> pathlib.Path:
    current = (start or pathlib.Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        path = candidate / DEFAULT_GEOGRAPHY_MAP_PATH
        if path.exists():
            return path
    raise SourceRegistryError("geography", f"no {DEFAULT_GEOGRAPHY_MAP_PATH} found above {current}")


@dataclass(frozen=True)
class GeographyEntry:
    """One reviewed classification.

    `basis` is mandatory and is not decoration -- the same rule `PacingPolicy`
    is under. A mapping with no recorded reason cannot be re-verified when
    somebody asks where `DEU -> DE` came from, and "it looks right" is how a
    wrong entry survives a review.
    """

    source_code: str
    kind: NormalizedGeographyKind
    canonical_code: str | None
    name: str | None
    basis: str

    def __post_init__(self) -> None:
        if not self.source_code.strip():
            raise SourceRegistryError("geography.entry", "source_code is required")
        if not self.basis.strip():
            raise SourceRegistryError(
                f"geography.{self.source_code}",
                "a classification must record why it was made, or it cannot be re-verified",
            )
        if self.kind is NormalizedGeographyKind.COUNTRY and not self.canonical_code:
            raise SourceRegistryError(
                f"geography.{self.source_code}",
                "a COUNTRY entry must carry a canonical code; without one it classifies "
                "without resolving, which is the half-answer this file exists to avoid",
            )
        if self.kind is not NormalizedGeographyKind.COUNTRY and self.canonical_code:
            raise SourceRegistryError(
                f"geography.{self.source_code}",
                "only a COUNTRY carries a canonical country code. An aggregate with one "
                "would be exactly the 'World is a country' error this file prevents",
            )


@dataclass(frozen=True)
class GeographyMap:
    """The reviewed classifications, per source.

    Per source rather than global: two sources may use the same string for
    different entities, and a shared table would make one of them wrong with no
    way to notice.
    """

    canonical_scheme: str
    entries: dict[str, dict[str, GeographyEntry]]

    def classify(self, source_id: str, source_code: str) -> GeographyEntry | None:
        """The reviewed entry, or `None`.

        `None` is a refusal the caller must handle, not a default to fill in.
        There is no permissive fallback because an unreviewed code has no
        established meaning.
        """
        return self.entries.get(source_id, {}).get(source_code.strip().upper())

    def codes_for(self, source_id: str) -> tuple[str, ...]:
        return tuple(sorted(self.entries.get(source_id, {})))


def load_geography_map(path: pathlib.Path | str | None = None) -> GeographyMap:
    file = pathlib.Path(path) if path else find_geography_map()
    try:
        payload = json.loads(file.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise SourceRegistryError("geography", f"{file} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SourceRegistryError("geography", "the geography map must be a JSON object")

    scheme = str(payload.get("canonical_scheme") or "")
    if not scheme:
        raise SourceRegistryError(
            "geography.canonical_scheme",
            "the map must name the scheme its canonical codes belong to; an unlabelled "
            "code cannot be joined to anything",
        )

    raw_schemes = payload.get("schemes")
    if not isinstance(raw_schemes, list):
        raise SourceRegistryError("geography.schemes", "must be a list")

    entries: dict[str, dict[str, GeographyEntry]] = {}
    for block in raw_schemes:
        if not isinstance(block, dict):
            raise SourceRegistryError("geography.schemes", "each entry must be an object")
        source_id = str(block.get("source_id") or "")
        if not source_id:
            raise SourceRegistryError("geography.schemes", "source_id is required")
        per_source: dict[str, GeographyEntry] = {}
        for item in block.get("entries") or ():
            entry = _entry_from_json(item, source_id)
            if entry.source_code in per_source:
                raise SourceRegistryError(
                    f"geography.{source_id}",
                    f"{entry.source_code} is classified twice; two answers is worse than none",
                )
            per_source[entry.source_code] = entry
        entries[source_id] = per_source

    return GeographyMap(canonical_scheme=scheme, entries=entries)


def _entry_from_json(item: object, source_id: str) -> GeographyEntry:
    if not isinstance(item, dict):
        raise SourceRegistryError(f"geography.{source_id}", "each entry must be an object")
    raw_kind = str(item.get("kind") or "")
    try:
        kind = NormalizedGeographyKind(raw_kind)
    except ValueError as exc:
        raise SourceRegistryError(
            f"geography.{source_id}",
            f"{raw_kind!r} is not a NormalizedGeographyKind. Adding one is an ontology "
            "change, not a data entry",
        ) from exc
    canonical = item.get("canonical_code")
    return GeographyEntry(
        source_code=str(item.get("source_code") or "").strip().upper(),
        kind=kind,
        canonical_code=str(canonical) if canonical else None,
        name=str(item["name"]) if item.get("name") else None,
        basis=str(item.get("basis") or ""),
    )
