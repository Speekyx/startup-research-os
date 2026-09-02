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
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from sros_contracts import AttributionElement, RightsBasis

from ..registry.models import LEGACY_USE_PROFILE, SourceRegistryError

__all__ = [
    "DEFAULT_COMPLIANCE_PATH",
    "AccessRestriction",
    "AcquisitionBounds",
    "ClientIdentification",
    "AuthorizedDataset",
    "AttributionObligation",
    "AttributionRequirement",
    "ComplianceConfig",
    "DataMinimisationProfile",
    "EnumeratedExclusion",
    "ResourceScope",
    "RouteAuthorization",
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
    # The families a review positively assessed. `None` means the review imposed
    # no family restriction; a set means everything outside it is refused.
    #
    # Mission 1.9.2 §22. `require_dataset_family` already refused a resource that
    # could not say what it is, and did NOT refuse one that says something nobody
    # reviewed -- any string passed. The two rules answer different questions:
    # "did you classify this?" and "did a reviewer look at that kind of thing?".
    allowed_dataset_families: frozenset[str] | None = None
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
        if self.allowed_dataset_families is not None:
            if not self.allowed_dataset_families:
                raise SourceRegistryError(
                    f"{self.source_id}.allowed_dataset_families",
                    "an empty allowlist denies everything, which is a refusal dressed as a "
                    "filter. Use null to mean 'the review imposed no family restriction'",
                )
            overlap = self.allowed_dataset_families & self.excluded_dataset_families
            if overlap:
                raise SourceRegistryError(
                    f"{self.source_id}.allowed_dataset_families",
                    f"{sorted(overlap)} is both reviewed and excluded. Which rule applies "
                    "would depend on which the reader checked first",
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
class RouteAuthorization:
    """Which of a source's registered access routes this review authorised.

    Mission 1.15.6 §7, §12, ADR-028. `AccessRestriction` above answers a
    different question and could not be made to answer this one.

    **`AccessRestriction` is about the SOURCE; this is about US.** It verifies
    that the registry records exactly the approved access profiles and no
    others -- a statement about how the source can be reached. TED can be
    reached by bulk XML: the packages are published, documented and downloadable
    without signing in, and `ted-bulk-xml` is in the registry because that is
    true. Deleting it to make an access restriction pass would be falsifying a
    fact about a source in order to obtain a permission, which is the worst
    thing this layer could learn to do.

    What the TED review actually requires is that **our acquisition binds to one
    named route**, and the route we bind to is a property of the configuration
    we supply -- checkable before anything opens a socket, and exactly the sort
    of objective collector property §21 says should not be left to a human
    confirmation nobody can make until the collector exists.

    Every field is a restriction. `allowed_labels` names access-profile labels
    the review assessed; `blocked_labels` names the ones it refused BY NAME, so
    that a refusal reads as a decision rather than as an omission.

    `preferred_label` is an **implementation preference and never a permission**
    (§11). It says which authorised route a first collector should reach for; it
    widens nothing, and a route absent from `allowed_labels` cannot be preferred.
    """

    source_id: str
    allowed_labels: frozenset[str] = frozenset()
    blocked_labels: frozenset[str] = frozenset()
    preferred_label: str | None = None
    basis: str = ""

    def __post_init__(self) -> None:
        if not self.allowed_labels:
            raise SourceRegistryError(
                f"{self.source_id}.route_authorization.allowed_labels",
                "must name at least one authorised access route. An empty allowlist "
                "refuses everything, which is a source-level refusal wearing a route "
                "restriction's name -- omit the key instead",
            )
        overlap = self.allowed_labels & self.blocked_labels
        if overlap:
            raise SourceRegistryError(
                f"{self.source_id}.route_authorization",
                f"{sorted(overlap)} is both authorised and blocked. Which rule applies "
                "would depend on which the reader checked first",
            )
        if not self.blocked_labels:
            raise SourceRegistryError(
                f"{self.source_id}.route_authorization.blocked_labels",
                "must name the routes the review refused. A route authorisation that "
                "names a permitted path without refusing an excluded one records a "
                "preference, not a restriction",
            )
        if self.preferred_label is not None and self.preferred_label not in self.allowed_labels:
            raise SourceRegistryError(
                f"{self.source_id}.route_authorization.preferred_label",
                f"{self.preferred_label!r} is not an authorised route. A preference is an "
                "implementation choice among what the review permitted, and it never "
                "widens what the review permitted",
            )
        if not self.basis.strip():
            raise SourceRegistryError(
                f"{self.source_id}.route_authorization",
                "required: a route authorisation with no stated basis cannot be re-checked "
                "against the review that granted it",
            )

    def refusals(self, label: str | None) -> tuple[str, ...]:
        """Why binding to this route is refused, or nothing.

        Fails closed on an unnamed route: acquisition that does not say how it
        would reach the source has not been shown to use an authorised path,
        and "it will use the right one" is the promise §15 replaces.
        """
        if label is None or not label.strip():
            return (
                "the acquisition configuration names no access route. A route the "
                f"configuration does not state is not one known to be inside "
                f"{sorted(self.allowed_labels)}",
            )
        name = label.strip()
        if name in self.blocked_labels:
            return (
                f"access route {name!r} is refused BY NAME under this review "
                f"{sorted(self.blocked_labels)}. It is not an unreviewed route; it is a "
                "reviewed and rejected one",
            )
        if name not in self.allowed_labels:
            return (
                f"access route {name!r} is not one this review authorised "
                f"{sorted(self.allowed_labels)}. An unreviewed route is not an approved "
                "one, whether or not anybody thought to exclude it",
            )
        return ()

    def to_json(self) -> dict[str, object]:
        return {
            "allowed_labels": sorted(self.allowed_labels),
            "blocked_labels": sorted(self.blocked_labels),
            "preferred_label": self.preferred_label,
            "basis": self.basis or None,
        }


@dataclass(frozen=True)
class ClientIdentification:
    """How this client must identify itself, where the source REQUIRES it.

    Mission 1.19. Wikimedia is the first source in the portfolio whose access
    policy makes identification a **condition of access** rather than a
    courtesy: *"The API requires an HTTP User-Agent header for all requests"*
    and *"Clients making requests without a User-Agent header may be blocked
    without notice"*. The Foundation's User-Agent Policy goes further and
    refuses non-descriptive defaults **by name** -- `python-requests/x` is the
    example it gives -- and directs clients not to copy a browser string.

    **This is an objective property of what a collector is configured to send**,
    so it belongs to a mechanical verification kind rather than to a person
    (ADR-028). Writing it as `HUMAN_CONFIRMATION` would create the bootstrap
    that ADR-028 exists to name: nothing can be authorised until somebody
    confirms behaviour, and nobody can confirm behaviour until the collector
    exists.

    `None` means **no identification obligation was reviewed** for this
    (source, profile), which is not the same as "any string is fine". Every
    entry predating this mission is in that state, and the capability reports
    *unimplemented* rather than *satisfied* when it is absent -- the same shape
    `route_authorization` uses, for the same reason.
    """

    source_id: str
    # The exact string the collector must send. Not a template with holes: a
    # value the capability can inspect, because a pattern nobody instantiated
    # cannot be checked against the policy that refuses generic defaults.
    user_agent: str
    # Where a person can be reached about this client. The policy asks for it
    # explicitly, and a User-Agent that names a client nobody can contact
    # satisfies the letter and defeats the purpose.
    contact: str
    basis: str = ""

    # Refused BY NAME rather than by a cleverness test. The policy names the
    # first; the rest are the shapes a collector reaches for when it wants to
    # look like something it is not.
    FORBIDDEN_PREFIXES = ("python-requests", "curl/", "wget/", "httpx/", "Mozilla/", "Opera/")

    def __post_init__(self) -> None:
        where = f"{self.source_id}.client_identification"
        if not self.user_agent.strip():
            raise SourceRegistryError(
                f"{where}.user_agent",
                "required: an identification obligation with no string to send is a "
                "condition that cannot be checked and an access rule that cannot be met",
            )
        if not self.contact.strip():
            raise SourceRegistryError(
                f"{where}.contact",
                "required: the policy asks for contact information so an operator can be "
                "reached, and a client nobody can contact meets the letter and defeats it",
            )
        if self.contact.strip() not in self.user_agent:
            raise SourceRegistryError(
                f"{where}.user_agent",
                "must contain the declared contact. Two places recording one fact drift, "
                "and the one that drifts is the string actually sent",
            )
        if not self.basis.strip():
            raise SourceRegistryError(
                where,
                "required: an identification rule with no stated basis cannot be "
                "re-checked, and the string would survive every later review by looking "
                "deliberate",
            )

    def refusals(self) -> tuple[str, ...]:
        """Why this declaration would not satisfy the policy. Empty is passing."""
        failures: list[str] = []
        for prefix in self.FORBIDDEN_PREFIXES:
            if self.user_agent.lower().startswith(prefix.lower()):
                failures.append(
                    f"the declared User-Agent begins with {prefix!r}, which the policy "
                    "refuses: a generic library default identifies nobody, and a browser "
                    "string identifies somebody we are not"
                )
        return tuple(failures)


@dataclass(frozen=True)
class AcquisitionBounds:
    """How much of a source one job may take, decided by the review.

    Mission 1.9.2 §15. Every other rule in this module answers *what* may be
    reached; this one answers *how much*, and it exists because GDELT's
    WEB-NGRAM files are a published bulk dataset emitted every fifteen minutes
    since 2019. Nothing in the terms limits how much of it is taken, so a
    limit that exists only as good intentions is no limit -- and "prose nobody
    reads" is the exact failure Mission 1.8 found in *silence is not
    permission*, which had been written down since Mission 1.0.

    **The ceiling belongs to the review, not to the collector.** A collector
    that chose its own bound would be setting its own permissions, which is the
    move the whole authorization layer exists to prevent.

    `None` means **no ceiling was reviewed**, which is not the same as "any size
    is fine": it means nobody has asked the question for this source, and every
    source that predates this mission is in that state deliberately.
    """

    source_id: str
    max_files_per_job: int | None = None
    basis: str = ""

    def __post_init__(self) -> None:
        if self.max_files_per_job is not None:
            if self.max_files_per_job < 1:
                raise SourceRegistryError(
                    f"{self.source_id}.acquisition_bounds.max_files_per_job",
                    "must be at least 1. A ceiling of zero is a refusal written as a "
                    "budget, and it would read as 'bounded' in every report",
                )
            if not self.basis.strip():
                raise SourceRegistryError(
                    f"{self.source_id}.acquisition_bounds",
                    "required: a bound with no stated basis cannot be re-checked, and the "
                    "number would survive every later review by looking deliberate",
                )

    @property
    def bounded(self) -> bool:
        return self.max_files_per_job is not None

    def refusals(self, file_count: int | None) -> tuple[str, ...]:
        """Why this request exceeds the reviewed ceiling, or nothing.

        Fails closed on an unstated count, the same asymmetry `ResourceDescriptor`
        is built on: a job that does not say how much it intends to take has not
        been shown to fall inside the bound.
        """
        if self.max_files_per_job is None:
            return ()
        if file_count is None:
            return (
                "the job does not state how many files it would fetch; the review set a "
                f"ceiling of {self.max_files_per_job}, and an unstated size is not a size "
                "known to fall under it",
            )
        if file_count < 1:
            return (f"a job that fetches {file_count} files is not a job; state a real size",)
        if file_count > self.max_files_per_job:
            return (
                f"{file_count} files exceeds the reviewed ceiling of "
                f"{self.max_files_per_job} for {self.source_id}. Raising it is a review "
                "decision, not a configuration one",
            )
        return ()

    def to_json(self) -> dict[str, object]:
        return {"max_files_per_job": self.max_files_per_job, "basis": self.basis or None}


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

    def refusals(self, requested: Sequence[str] | None) -> tuple[str, ...]:
        """Why this field selection is not the minimised one, or nothing.

        Mission 1.15.6 §8, §9. `permits` answered a question about ONE category
        and nothing called it; this answers the question a request actually
        asks -- *may I ask for these* -- and it is the primary minimisation
        control rather than a filter applied to what came back.

        **Collect-then-filter is not available here** (§9). Where the source
        supports field selection, a request that took everything and discarded
        the contact block afterwards would have retrieved the contact block,
        and the obligation is about what is retrieved.

        Fails closed on an unstated selection, the same asymmetry
        `ResourceDescriptor` and `AcquisitionBounds` are built on: a request
        that does not say which fields it wants has not been shown to want only
        authorised ones.
        """
        if requested is None:
            return (
                "the request does not state which fields it would ask for. Minimisation "
                "happens AT acquisition, so an unstated selection is not a selection known "
                "to be minimised",
            )
        fields = tuple(requested)
        if not fields:
            return ("the request names no field at all, which is not a request",)
        if not self.allowed:
            return (
                "this minimisation profile authorises no field, so nothing may be "
                "requested. An empty allowlist is a refusal, not an absence of rules",
            )

        reasons: list[str] = []
        # Reported separately from the allowlist miss below, and first, because
        # the two call for different fixes: one is a field nobody reviewed, the
        # other is a field a reviewer refused BY NAME, and a reader chasing the
        # wrong one loses an afternoon.
        prohibited = sorted({f for f in fields if f in self.excluded})
        if prohibited:
            reasons.append(
                f"{prohibited} is excluded by name in this minimisation profile. These are "
                "the fields the review requires to be discarded, and requesting one is the "
                "act the obligation forbids"
            )
        unreviewed = sorted({f for f in fields if f not in self.allowed and f not in self.excluded})
        if unreviewed:
            reasons.append(
                f"{unreviewed} is not a field this review authorised "
                f"{sorted(self.allowed)}. An unreviewed field is not an approved one, "
                "whether or not anybody thought to exclude it"
            )
        return tuple(reasons)


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
    content_origin: str
    basis: str
    # What KIND of thing authorises this resource (Mission 1.9.1, ADR-018).
    # Required and never defaulted: inferring NAMED_LICENCE from the presence of
    # a licence string would work for every entry that exists today and would
    # silently classify the first one that forgot the field.
    rights_basis: RightsBasis = RightsBasis.NAMED_LICENCE
    # Conditional on the basis, in BOTH directions -- see __post_init__. `None`
    # under a direct grant rather than a placeholder: a source that names no
    # licence has nothing to put here, and an invented identifier would reach
    # every record's provenance indistinguishable from a real one.
    licence: str | None = None
    indicator: str | None = None
    name: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("resource_id", "dataset_family", "content_origin"):
            if not str(getattr(self, field_name)).strip():
                raise SourceRegistryError(f"dataset.{field_name}", "required")
        if self.rights_basis is RightsBasis.NAMED_LICENCE:
            if not (self.licence or "").strip():
                raise SourceRegistryError(
                    f"dataset.{self.resource_id}.licence",
                    "required under NAMED_LICENCE: the basis says a published instrument "
                    "authorises this resource, so it has an identifier",
                )
        elif (self.licence or "").strip():
            # The fabrication arriving through the other door.
            raise SourceRegistryError(
                f"dataset.{self.resource_id}.licence",
                f"must be absent under {self.rights_basis.value}: the basis says the "
                "source's own terms grant this directly and name no instrument, so a "
                "licence identifier here would be this repository's invention presented "
                "as the source's",
            )
        if not self.basis.strip():
            raise SourceRegistryError(
                f"dataset.{self.resource_id}",
                "required: an authorised dataset with no stated basis cannot be re-checked "
                "against the document that authorised it",
            )


@dataclass(frozen=True)
class SourceCompliance:
    """Everything the compliance layer knows about one source, FOR ONE USE.

    Keyed by (source, use profile) since Mission 1.15.5. A configuration that
    named only the source would be the same defect the reviews had: a resource
    scope, an attribution obligation and a minimisation profile are answers to
    "what may we do with this, for what", and two profiles can legitimately have
    different answers.
    """

    source_id: str
    review_version: int
    evidence_url: str
    attribution: AttributionObligation
    resource_scope: ResourceScope
    data_minimisation: DataMinimisationProfile
    # Defaults to the legacy profile so every existing entry keeps configuring
    # what it has always configured, and a new profile has to say so.
    use_profile_id: str = LEGACY_USE_PROFILE
    evidence_section: str | None = None
    access_restriction: AccessRestriction | None = None
    # Which registered access route acquisition may bind to (Mission 1.15.6).
    # `None` means NO ROUTE RESTRICTION WAS REVIEWED for this (source, profile) —
    # not that every route is fine. Every entry predating this mission is in that
    # state, and the capability that checks it fails rather than passes when it
    # is absent, so a condition can only rest on a restriction that exists.
    route_authorization: RouteAuthorization | None = None
    datasets: tuple[AuthorizedDataset, ...] = ()
    acquisition_bounds: AcquisitionBounds | None = None
    # How this client must identify itself, where the source requires it
    # (Mission 1.19). `None` means unasked, never unrestricted.
    client_identification: ClientIdentification | None = None

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

    def get(
        self, source_id: str, use_profile_id: str = LEGACY_USE_PROFILE
    ) -> SourceCompliance | None:
        """`None` rather than a default. A source with no compliance entry for
        THAT USE has no basis for a request, and the caller must decide -- there
        is no permissive fallback to fall into, and in particular no falling
        back to another profile's configuration."""
        return next(
            (
                s
                for s in self.sources
                if s.source_id == source_id and s.use_profile_id == use_profile_id
            ),
            None,
        )

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
    # Keyed by (source, profile) since Mission 1.15.6. `SourceCompliance` has
    # been keyed that way since 1.15.5 and `get` has looked it up that way since
    # 1.15.5, but this guard still deduplicated on the source alone -- so the
    # second profile's entry for a source, which is the whole point of the key,
    # was refused as a duplicate before anything could read it. TED is the first
    # source that would ever have two.
    seen: set[tuple[str, str]] = set()
    for entry in raw_sources:
        record = _source_from_json(entry)
        key = (record.source_id, record.use_profile_id)
        if key in seen:
            raise SourceRegistryError(
                "compliance.sources",
                f"duplicate entry for {record.source_id!r} under use profile "
                f"{record.use_profile_id!r}; which entry configures that use would be "
                "undefined",
            )
        seen.add(key)
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
    families = scope_raw.get("allowed_dataset_families")
    scope = ResourceScope(
        source_id=source_id,
        licence_allowlist=frozenset(licences) if licences is not None else None,
        allowed_dataset_families=frozenset(families) if families is not None else None,
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

    routes_raw = entry.get("route_authorization")
    routes = (
        RouteAuthorization(
            source_id=source_id,
            allowed_labels=frozenset(routes_raw.get("allowed_labels") or ()),
            blocked_labels=frozenset(routes_raw.get("blocked_labels") or ()),
            preferred_label=routes_raw.get("preferred_label"),
            basis=str(routes_raw.get("basis") or ""),
        )
        if isinstance(routes_raw, dict)
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

    bounds_raw = entry.get("acquisition_bounds")
    bounds = (
        AcquisitionBounds(
            source_id=source_id,
            max_files_per_job=(
                int(bounds_raw["max_files_per_job"])
                if bounds_raw.get("max_files_per_job") is not None
                else None
            ),
            basis=str(bounds_raw.get("basis") or ""),
        )
        if isinstance(bounds_raw, dict)
        else None
    )

    client_raw = entry.get("client_identification")
    client = (
        ClientIdentification(
            source_id=source_id,
            user_agent=str(client_raw.get("user_agent") or ""),
            contact=str(client_raw.get("contact") or ""),
            basis=str(client_raw.get("basis") or ""),
        )
        if isinstance(client_raw, dict)
        else None
    )

    return SourceCompliance(
        source_id=source_id,
        use_profile_id=str(entry.get("use_profile_id") or LEGACY_USE_PROFILE),
        review_version=int(entry.get("review_version") or 0),
        evidence_url=str(entry.get("evidence_url") or ""),
        evidence_section=entry.get("evidence_section"),
        attribution=attribution,
        resource_scope=scope,
        data_minimisation=minimisation,
        access_restriction=restriction,
        route_authorization=routes,
        datasets=datasets,
        acquisition_bounds=bounds,
        client_identification=client,
    )


def _rights_basis(item: dict[str, object], source_id: str) -> RightsBasis:
    """Read the basis. Absent is an error, never a default.

    Mission 1.9.1 §28 requires a missing rights basis to fail. Defaulting it to
    NAMED_LICENCE would be correct for every entry that exists today and would
    silently mis-classify the first one that omitted it -- which is the opposite
    of failing.
    """
    raw = item.get("rights_basis")
    if raw is None:
        raise SourceRegistryError(
            f"{source_id}.datasets.rights_basis",
            "required: state whether a NAMED_LICENCE or a DIRECT_GRANT authorises this "
            "resource. There is no default, because the wrong one is invisible",
        )
    try:
        return RightsBasis(str(raw))
    except ValueError:
        raise SourceRegistryError(
            f"{source_id}.datasets.rights_basis",
            f"{raw!r} is not a rights basis. Known: {', '.join(b.value for b in RightsBasis)}",
        ) from None


def _dataset_from_json(item: object, source_id: str) -> AuthorizedDataset:
    if not isinstance(item, dict):
        raise SourceRegistryError(f"{source_id}.datasets", "each entry must be an object")
    return AuthorizedDataset(
        resource_id=str(item.get("resource_id") or ""),
        dataset_family=str(item.get("dataset_family") or ""),
        rights_basis=_rights_basis(item, source_id),
        licence=(str(item["licence"]).strip() or None) if item.get("licence") else None,
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
