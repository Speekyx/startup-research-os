"""Compliance configuration: the parameters of an obligation, as data.

Mission 1.4 §5 and §7. The rule this module exists to enforce is that a
compliance obligation is **configuration, not a branch**. There is no
`if source_id == "fred"` anywhere in this package; there is a JSON file holding
FRED's exact required notice, and code that renders whatever notice a source's
entry names.

Two consequences follow, and both are the point:

* **exact wording survives.** Where the terms prescribe a sentence, the sentence
  is stored verbatim and rendered unmodified. Composing one would produce a
  different sentence, which does not satisfy the requirement;
* **a source with no entry is denied.** Nothing here grants anything. Every
  field describes a restriction, and the absence of an entry means the resource
  gate has no basis on which to allow a request.

The file lives in `docs/data/` for the same reason the catalog does: it is a
governance record a reviewer reads and edits, not runtime configuration.

**Dependency-free**, like the rest of the registry model (ADR-009).
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Any

from sros_contracts import AttributionElement

from ..registry.models import SourceRegistryError

__all__ = [
    "DEFAULT_COMPLIANCE_PATH",
    "AccessRestriction",
    "AuthorizedDataset",
    "AttributionObligation",
    "AttributionRequirement",
    "ComplianceConfig",
    "DataMinimisationProfile",
    "EnumeratedExclusion",
    "ResourceScope",
    "SourceCompliance",
    "find_compliance_config",
    "load_compliance",
]

DEFAULT_COMPLIANCE_PATH = pathlib.Path("docs/data/source-compliance-v1.json")

# An element whose text is prescribed by the terms can never be supplied by a
# caller: the whole requirement is that OUR wording does not enter it.
_CONFIGURED_TEXT_ONLY = frozenset({AttributionElement.EXACT_NOTICE})


def find_compliance_config(start: pathlib.Path | None = None) -> pathlib.Path:
    current = (start or pathlib.Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        path = candidate / DEFAULT_COMPLIANCE_PATH
        if path.exists():
            return path
    raise SourceRegistryError("compliance", f"no {DEFAULT_COMPLIANCE_PATH} found above {current}")


@dataclass(frozen=True)
class AttributionRequirement:
    """One required part of a source's attribution.

    `supplied` is the load-bearing flag. A requirement that is NOT supplied
    carries its text here and is identical for every artefact. A requirement
    that IS supplied has to come from whoever produced the artefact -- a dataset
    DOI, an access date, a description of what was changed -- and rendering
    fails without it. That is what stops attribution from quietly degrading into
    whatever happened to be available.
    """

    element: AttributionElement
    text: str | None = None
    supplied: bool = False
    when_modified: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.element, AttributionElement):
            raise SourceRegistryError("attribution.element", "must be an AttributionElement")
        if self.supplied and (self.text or "").strip():
            raise SourceRegistryError(
                f"attribution.{self.element.value}",
                "a supplied requirement must not also carry fixed text: one of the two "
                "would silently win and a reader could not tell which",
            )
        if not self.supplied and not (self.text or "").strip():
            raise SourceRegistryError(
                f"attribution.{self.element.value}",
                "a requirement that is not supplied per artefact must state its text. "
                "An empty obligation renders as nothing and looks satisfied",
            )
        if self.element in _CONFIGURED_TEXT_ONLY and self.supplied:
            raise SourceRegistryError(
                f"attribution.{self.element.value}",
                "an exact notice is prescribed by the source's terms. It is configuration, "
                "never something a caller supplies, or its wording would be ours",
            )

    @property
    def required_always(self) -> bool:
        return not self.when_modified


@dataclass(frozen=True)
class AttributionObligation:
    """What attribution follows this source's data, and what it rests on."""

    source_id: str
    evidence_url: str
    requirements: tuple[AttributionRequirement, ...] = ()
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.requirements:
            raise SourceRegistryError(
                f"{self.source_id}.attribution",
                "an attribution obligation with no requirements is an obligation that "
                "renders as nothing. Omit the source instead",
            )
        elements = [r.element for r in self.requirements]
        if len(set(elements)) != len(elements):
            raise SourceRegistryError(
                f"{self.source_id}.attribution",
                "an element is required twice; which text applies would be undefined",
            )

    def requirement(self, element: AttributionElement) -> AttributionRequirement | None:
        return next((r for r in self.requirements if r.element is element), None)

    @property
    def elements(self) -> tuple[AttributionElement, ...]:
        return tuple(r.element for r in self.requirements)


@dataclass(frozen=True)
class EnumeratedExclusion:
    """A named exclusion the source's own terms spell out.

    Deliberately not a general rule language. These are the specific carve-outs
    a review found written down -- declaring country, classification, year --
    and encoding them as data rather than as an expression grammar keeps the
    configuration checkable against the document it came from.
    """

    key: str
    declaring_countries: frozenset[str] = frozenset()
    classifications: frozenset[str] = frozenset()
    from_year: int | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise SourceRegistryError("exclusion.key", "required")
        if not self.declaring_countries and not self.classifications:
            raise SourceRegistryError(
                f"exclusion.{self.key}",
                "an exclusion that names neither a country nor a classification matches "
                "nothing, and would read as a rule that is being enforced",
            )
        if not self.reason.strip():
            raise SourceRegistryError(
                f"exclusion.{self.key}",
                "required: an exclusion with no stated reason cannot be re-checked "
                "against the document it came from",
            )


@dataclass(frozen=True)
class ResourceScope:
    """Which of a source's resources the reviewed terms actually cover.

    Mission 1.4 §10 and §12. A source-level approval is not a resource-level
    one: the platforms here republish material they do not own, and a licence is
    a property of a dataset rather than of a host.

    Every field is a restriction. The default of every optional field is the
    strict one, so a scope built from an empty configuration denies rather than
    permits.
    """

    source_id: str
    licence_allowlist: frozenset[str] | None = None
    excluded_dataset_families: frozenset[str] = frozenset()
    require_dataset_family: bool = False
    geography_allowlist: frozenset[str] | None = None
    enumerated_exclusions: tuple[EnumeratedExclusion, ...] = ()
    excluded_note_markers: tuple[str, ...] = ()
    require_notes: bool = False
    third_party_denied: bool = True

    def __post_init__(self) -> None:
        if self.licence_allowlist is not None and not self.licence_allowlist:
            raise SourceRegistryError(
                f"{self.source_id}.licence_allowlist",
                "an empty allowlist denies everything, which is a refusal dressed as a "
                "filter. Use null to mean 'the terms impose no licence restriction'",
            )
        if self.geography_allowlist is not None and not self.geography_allowlist:
            raise SourceRegistryError(
                f"{self.source_id}.geography_allowlist",
                "an empty allowlist denies everything. Use null for 'no restriction'",
            )
        if self.require_notes and not self.excluded_note_markers:
            raise SourceRegistryError(
                f"{self.source_id}.require_notes",
                "requiring notes with no marker to look for makes the notes mandatory "
                "and unread, which is cost with no protection",
            )


@dataclass(frozen=True)
class AccessRestriction:
    """A named restriction on HOW a source may be reached.

    Verified against the registry rather than against a collector: the check is
    that the source's registered access profiles are exactly the named ones. A
    second profile appearing -- a bulk download, a browser path -- fails it,
    which is the behaviour that makes the restriction mean something.
    """

    name: str
    access_methods: frozenset[str] = frozenset()
    profile_labels: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise SourceRegistryError("access_restriction.name", "required")
        if not self.profile_labels:
            raise SourceRegistryError(
                f"access_restriction.{self.name}",
                "must name at least one permitted access profile, or it restricts nothing",
            )


@dataclass(frozen=True)
class DataMinimisationProfile:
    """What a collector may ask for, and what it must not (§31)."""

    allowed: tuple[str, ...] = ()
    excluded: tuple[str, ...] = ()
    notes: str | None = None

    def __post_init__(self) -> None:
        overlap = set(self.allowed) & set(self.excluded)
        if overlap:
            raise SourceRegistryError(
                "data_minimisation",
                f"{sorted(overlap)} is both allowed and excluded. A category that is both "
                "will be read as whichever the reader checked first",
            )

    def permits(self, category: str) -> bool:
        return category in self.allowed and category not in self.excluded


@dataclass(frozen=True)
class AuthorizedDataset:
    """One resource a collector may request, and the facts that authorise it.

    Mission 1.5 §7. A collector builds its `ResourceDescriptor` **from** an entry
    here, never from what a caller claims. Letting the requester supply the
    licence would make "this dataset is CC-BY 4.0" an assertion the requester
    makes about itself, which is the failure mode the whole review model exists
    to prevent.

    A resource with no entry therefore has no licence, no dataset family and no
    content origin — and the resource gate denies exactly that.
    """

    resource_id: str
    dataset_family: str
    licence: str
    content_origin: str
    basis: str
    indicator: str | None = None
    name: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("resource_id", "dataset_family", "licence", "content_origin"):
            if not str(getattr(self, field_name)).strip():
                raise SourceRegistryError(f"dataset.{field_name}", "required")
        if not self.basis.strip():
            raise SourceRegistryError(
                f"dataset.{self.resource_id}",
                "required: an authorised dataset with no stated basis cannot be re-checked "
                "against the document that authorised it",
            )


@dataclass(frozen=True)
class SourceCompliance:
    """Everything the compliance layer knows about one source."""

    source_id: str
    review_version: int
    evidence_url: str
    attribution: AttributionObligation
    resource_scope: ResourceScope
    data_minimisation: DataMinimisationProfile
    evidence_section: str | None = None
    access_restriction: AccessRestriction | None = None
    datasets: tuple[AuthorizedDataset, ...] = ()

    def dataset(self, resource_id: str) -> AuthorizedDataset | None:
        """`None` for an unauthorised resource. The caller must refuse, not
        default: there is no permissive fallback to fall into."""
        return next((d for d in self.datasets if d.resource_id == resource_id), None)

    def dataset_for_indicator(self, indicator: str) -> AuthorizedDataset | None:
        return next((d for d in self.datasets if d.indicator == indicator), None)

    def __post_init__(self) -> None:
        if self.review_version < 1:
            raise SourceRegistryError(f"{self.source_id}.review_version", "must be at least 1")
        if not self.evidence_url.startswith(("http://", "https://")):
            raise SourceRegistryError(
                f"{self.source_id}.evidence_url",
                "must be the absolute URL of the reviewed document. A compliance rule "
                "whose source cannot be re-opened cannot be re-checked",
            )


@dataclass(frozen=True)
class ComplianceConfig:
    compliance_version: str
    sources: tuple[SourceCompliance, ...] = ()
    catalog_version: str | None = None
    review_round: str | None = None
    path: pathlib.Path | None = field(default=None, compare=False)

    def get(self, source_id: str) -> SourceCompliance | None:
        """`None` rather than a default. A source with no compliance entry has
        no basis for a request, and the caller must decide -- there is no
        permissive fallback to fall into."""
        return next((s for s in self.sources if s.source_id == source_id), None)

    def __iter__(self) -> Any:
        return iter(self.sources)

    def __len__(self) -> int:
        return len(self.sources)


def load_compliance(path: pathlib.Path | str | None = None) -> ComplianceConfig:
    file = pathlib.Path(path) if path else find_compliance_config()
    try:
        payload = json.loads(file.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise SourceRegistryError("compliance", f"{file} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SourceRegistryError("compliance", "the compliance config must be a JSON object")

    raw_sources = payload.get("sources")
    if not isinstance(raw_sources, list):
        raise SourceRegistryError("compliance.sources", "must be a list")

    sources: list[SourceCompliance] = []
    seen: set[str] = set()
    for entry in raw_sources:
        record = _source_from_json(entry)
        if record.source_id in seen:
            raise SourceRegistryError(
                "compliance.sources", f"duplicate entry for {record.source_id!r}"
            )
        seen.add(record.source_id)
        sources.append(record)

    derived = payload.get("derived_from") or {}
    return ComplianceConfig(
        compliance_version=str(payload.get("compliance_version") or "0"),
        sources=tuple(sources),
        catalog_version=derived.get("catalog_version"),
        review_round=derived.get("review_round"),
        path=file,
    )


def _source_from_json(entry: object) -> SourceCompliance:
    if not isinstance(entry, dict):
        raise SourceRegistryError("compliance.sources", "each entry must be an object")
    source_id = str(entry.get("source_id") or "")
    if not source_id:
        raise SourceRegistryError("compliance.sources", "source_id is required")

    attribution_raw = entry.get("attribution") or {}
    requirements = tuple(
        _requirement_from_json(item, source_id)
        for item in attribution_raw.get("requirements") or ()
    )
    attribution = AttributionObligation(
        source_id=source_id,
        evidence_url=str(entry.get("evidence_url") or ""),
        requirements=requirements,
        notes=attribution_raw.get("notes"),
    )

    scope_raw = entry.get("resource_scope") or {}
    licences = scope_raw.get("licence_allowlist")
    geographies = scope_raw.get("geography_allowlist")
    scope = ResourceScope(
        source_id=source_id,
        licence_allowlist=frozenset(licences) if licences is not None else None,
        excluded_dataset_families=frozenset(scope_raw.get("excluded_dataset_families") or ()),
        require_dataset_family=bool(scope_raw.get("require_dataset_family", False)),
        geography_allowlist=frozenset(geographies) if geographies is not None else None,
        enumerated_exclusions=tuple(
            _exclusion_from_json(item) for item in scope_raw.get("enumerated_exclusions") or ()
        ),
        excluded_note_markers=tuple(scope_raw.get("excluded_note_markers") or ()),
        require_notes=bool(scope_raw.get("require_notes", False)),
        # Defaults to the strict answer: a configuration that forgot to say
        # must not thereby permit third-party material.
        third_party_denied=bool(scope_raw.get("third_party_denied", True)),
    )

    restriction_raw = entry.get("access_restriction")
    restriction = (
        AccessRestriction(
            name=str(restriction_raw.get("name") or ""),
            access_methods=frozenset(restriction_raw.get("access_methods") or ()),
            profile_labels=frozenset(restriction_raw.get("profile_labels") or ()),
        )
        if isinstance(restriction_raw, dict)
        else None
    )

    minimisation_raw = entry.get("data_minimisation") or {}
    minimisation = DataMinimisationProfile(
        allowed=tuple(minimisation_raw.get("allowed") or ()),
        excluded=tuple(minimisation_raw.get("excluded") or ()),
        notes=minimisation_raw.get("note"),
    )

    datasets = tuple(_dataset_from_json(item, source_id) for item in entry.get("datasets") or ())
    ids = [d.resource_id for d in datasets]
    if len(set(ids)) != len(ids):
        raise SourceRegistryError(
            f"{source_id}.datasets",
            "a resource_id appears twice; which entry authorises it would be undefined",
        )

    return SourceCompliance(
        source_id=source_id,
        review_version=int(entry.get("review_version") or 0),
        evidence_url=str(entry.get("evidence_url") or ""),
        evidence_section=entry.get("evidence_section"),
        attribution=attribution,
        resource_scope=scope,
        data_minimisation=minimisation,
        access_restriction=restriction,
        datasets=datasets,
    )


def _dataset_from_json(item: object, source_id: str) -> AuthorizedDataset:
    if not isinstance(item, dict):
        raise SourceRegistryError(f"{source_id}.datasets", "each entry must be an object")
    return AuthorizedDataset(
        resource_id=str(item.get("resource_id") or ""),
        dataset_family=str(item.get("dataset_family") or ""),
        licence=str(item.get("licence") or ""),
        content_origin=str(item.get("content_origin") or ""),
        basis=str(item.get("basis") or ""),
        indicator=item.get("indicator"),
        name=item.get("name"),
    )


def _requirement_from_json(item: object, source_id: str) -> AttributionRequirement:
    if not isinstance(item, dict):
        raise SourceRegistryError(f"{source_id}.attribution", "each requirement is an object")
    return AttributionRequirement(
        element=AttributionElement(item.get("element")),
        text=item.get("text"),
        supplied=bool(item.get("supplied", False)),
        when_modified=bool(item.get("when_modified", False)),
    )


def _exclusion_from_json(item: object) -> EnumeratedExclusion:
    if not isinstance(item, dict):
        raise SourceRegistryError("compliance.enumerated_exclusions", "each entry is an object")
    year = item.get("from_year")
    return EnumeratedExclusion(
        key=str(item.get("key") or ""),
        declaring_countries=frozenset(item.get("declaring_countries") or ()),
        classifications=frozenset(item.get("classifications") or ()),
        from_year=int(year) if year is not None else None,
        reason=str(item.get("reason") or ""),
    )
