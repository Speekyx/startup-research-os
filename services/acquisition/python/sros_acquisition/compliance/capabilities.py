"""Named compliance capabilities, and what it takes to say one is implemented.

Mission 1.4 §5 and §20. Six of the nine Mission 1.3 conditions are verified by
`CAPABILITY`, whose contract definition is precise: *a named product capability
is implemented and enabled*. This module is what makes that claim checkable.

A capability here is **not a name in a list**. Registering one is not enough:
its check runs the real gate against the source's real configuration and
asserts, for every case the review evidence names, that the gate gives the right
answer — including denying the unknown case. A capability whose check fails is
reported as unimplemented, whatever its entry says.

**The names come from Mission 1.3; the mechanisms are shared.** Three condition
records name a source in their capability (`eurostat-geographic-filter`,
`fred-copyright-series-filter`). Those names are the review's and are not
renamed here — a condition that changed key would look like a new requirement.
What is shared is the implementation: `eurostat-geographic-filter` is a binding
from that name to a generic geography-allowlist check, and a second source
needing one would bind to the same function.

**What a passing check does NOT establish** is stated once, because it is the
load-bearing limitation of this whole layer: seven of the nine conditions are
phrased as claims about a *collector*, and no collector exists. A passing check
says the gate exists, is configured, and refuses what it must. It does not say a
collector went through it. That guarantee is structural — a collector may only
run with an `AcquisitionAuthorizationContext`, and the rules travel inside it —
and it becomes an observed guarantee only when Mission 1.5 adds a conformance
test that its collector has no other path to a resource.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date

from sros_contracts import AttributionElement, ResourceContentOrigin, RightsBasis

from .attribution import AttributionFacts, AttributionIncompleteError, render_attribution
from .config import SourceCompliance
from .resources import ResourceDescriptor, authorize_resource

__all__ = [
    "CAPABILITIES",
    "ComplianceCapability",
    "capability",
    "capability_failures",
]

# A dataset family that no configuration excludes, used to build a probe that
# should pass. Named so a failure message points at the probe rather than
# looking like real data.
_PROBE_FAMILY = "compliance-probe"
_PROBE_GEOGRAPHY_OUTSIDE = "ZZ"


@dataclass(frozen=True)
class ComplianceCapability:
    """One named capability, and the check that decides whether it is real."""

    name: str
    description: str
    check: Callable[[SourceCompliance], tuple[str, ...]]


def _baseline(compliance: SourceCompliance) -> ResourceDescriptor:
    """A descriptor that every rule in this source's scope should allow.

    Built from the configuration rather than hard-coded, so a probe cannot
    accidentally test a scope other than the one in force. It is the control
    case: a check that only ever proves denial would pass just as well against a
    gate that denies everything, which is a refusal, not a filter.
    """
    scope = compliance.resource_scope
    return ResourceDescriptor(
        source_id=compliance.source_id,
        resource_id=f"{compliance.source_id}:probe",
        licence=(sorted(scope.licence_allowlist)[0] if scope.licence_allowlist else None),
        # The basis the scope requires, not a fixed one. A scope enumerating
        # licences can only be satisfied by a NAMED_LICENCE resource
        # (Mission 1.9.1 §15), so the control case has to carry that basis or it
        # would fail for a reason the probe is not testing. Where the scope has
        # no licence rule the basis is left unestablished, exactly as a
        # descriptor built by a caller rather than from a dataset would be.
        rights_basis=(RightsBasis.NAMED_LICENCE if scope.licence_allowlist else None),
        content_origin=ResourceContentOrigin.PLATFORM_LICENSED,
        dataset_family=(
            _PROBE_FAMILY
            if (scope.require_dataset_family or scope.excluded_dataset_families)
            else None
        ),
        geographies=((sorted(scope.geography_allowlist)[0],) if scope.geography_allowlist else ()),
        notes=("compliance probe series" if scope.excluded_note_markers else None),
    )


def _control_passes(compliance: SourceCompliance) -> tuple[str, ...]:
    """The control case, asserted by every resource-gate capability."""
    result = authorize_resource(compliance.resource_scope, _baseline(compliance))
    if not result.allowed:
        return (
            "the resource gate denies its own control case "
            f"({'; '.join(result.denial_reasons)}); a filter that allows nothing is a "
            "refusal, not a filter",
        )
    return ()


# --------------------------------------------------------------- attribution


def _check_attribution_surface(compliance: SourceCompliance) -> tuple[str, ...]:
    """The obligation renders when complete, and refuses when it is not.

    Both halves are asserted. Proving only that it renders would pass against a
    renderer that never checks anything, and the property §8 asks for is that
    required attribution *cannot silently disappear*.
    """
    failures: list[str] = []
    obligation = compliance.attribution

    complete = AttributionFacts(
        licence_identifier="probe-licence",
        dataset_doi="10.0000/probe",
        access_date=date(2026, 1, 1),
        modification_statement="probe modification",
        disclaimer="probe disclaimer",
        modified=True,
    )
    try:
        notice = render_attribution(obligation, complete)
    except AttributionIncompleteError as exc:
        return (f"the obligation cannot be rendered even with every element supplied: {exc}",)

    rendered = {element for element, _ in notice.elements}
    for requirement in obligation.requirements:
        if requirement.element not in rendered:
            failures.append(f"{requirement.element.value} was not rendered")

    # An exact notice must survive verbatim. Compared as a substring of the
    # rendered text rather than trusted, because a renderer that stripped,
    # re-cased or reflowed it would produce a different sentence.
    exact = obligation.requirement(AttributionElement.EXACT_NOTICE)
    if exact is not None and (exact.text or "") not in notice.text:
        failures.append("the exact required notice is not present verbatim in the rendered output")

    # The refusal branch must be live for every element a caller has to supply.
    for requirement in obligation.requirements:
        if not requirement.supplied:
            continue
        partial = _without(complete, requirement.element)
        try:
            render_attribution(obligation, partial)
        except AttributionIncompleteError:
            continue
        failures.append(
            f"{requirement.element.value} is declared as supplied per artefact, but "
            "rendering succeeded without it"
        )

    return tuple(failures)


def _without(facts: AttributionFacts, element: AttributionElement) -> AttributionFacts:
    """The same facts with one supplied element removed.

    Written out rather than driven by a name table: the mapping from element to
    field is the thing that would be wrong if it were wrong, and a table hides
    a missing entry as a silent no-op.
    """
    if element is AttributionElement.LICENCE_IDENTIFIER:
        return replace(facts, licence_identifier=None)
    if element is AttributionElement.DATASET_DOI:
        return replace(facts, dataset_doi=None)
    if element is AttributionElement.ACCESS_DATE:
        return replace(facts, access_date=None)
    if element is AttributionElement.MODIFICATION_STATEMENT:
        return replace(facts, modification_statement=None)
    if element is AttributionElement.DISCLAIMER:
        return replace(facts, disclaimer=None)
    return facts


# ------------------------------------------------------------- resource gates


def _check_licence_allowlist(compliance: SourceCompliance) -> tuple[str, ...]:
    scope = compliance.resource_scope
    if not scope.licence_allowlist:
        return ("no licence allowlist is configured, so no licence restriction is enforced",)

    failures = list(_control_passes(compliance))
    baseline = _baseline(compliance)

    unrecorded = authorize_resource(scope, replace(baseline, licence=None))
    if unrecorded.allowed:
        failures.append("a resource with no recorded licence is allowed; it must fail closed")

    outside = authorize_resource(scope, replace(baseline, licence="License Specified Externally"))
    if outside.allowed:
        failures.append("a licence outside the allowlist is allowed")

    return tuple(failures)


def _check_geography_allowlist(compliance: SourceCompliance) -> tuple[str, ...]:
    scope = compliance.resource_scope
    if not scope.geography_allowlist:
        return ("no geography allowlist is configured, so no geographic restriction applies",)

    failures = list(_control_passes(compliance))
    baseline = _baseline(compliance)

    unstated = authorize_resource(scope, replace(baseline, geographies=()))
    if unstated.allowed:
        failures.append("a resource naming no geography is allowed; it must fail closed")

    outside = authorize_resource(scope, replace(baseline, geographies=(_PROBE_GEOGRAPHY_OUTSIDE,)))
    if outside.allowed:
        failures.append("a geography outside the approved set is allowed")

    return tuple(failures)


def _check_enumerated_exclusions(compliance: SourceCompliance) -> tuple[str, ...]:
    scope = compliance.resource_scope
    if not scope.enumerated_exclusions:
        return ("no enumerated exclusions are configured, so nothing is excluded",)

    failures = list(_control_passes(compliance))
    baseline = _baseline(compliance)

    for exclusion in scope.enumerated_exclusions:
        probe = replace(
            baseline,
            declaring_country=(
                sorted(exclusion.declaring_countries)[0] if exclusion.declaring_countries else None
            ),
            classifications=(
                (sorted(exclusion.classifications)[0],) if exclusion.classifications else ()
            ),
            period_start_year=(exclusion.from_year if exclusion.from_year is not None else None),
        )
        if authorize_resource(scope, probe).allowed:
            failures.append(f"exclusion {exclusion.key!r} does not exclude its own named case")

    return tuple(failures)


def _check_note_marker_exclusion(compliance: SourceCompliance) -> tuple[str, ...]:
    scope = compliance.resource_scope
    if not scope.excluded_note_markers:
        return ("no note markers are configured, so third-party series are not detected",)
    if not scope.require_notes:
        return (
            "notes are not required, so a resource whose notes were never read would pass "
            "the marker check by having nothing to match",
        )

    failures = list(_control_passes(compliance))
    baseline = _baseline(compliance)

    unread = authorize_resource(scope, replace(baseline, notes=None))
    if unread.allowed:
        failures.append("a resource with unread notes is allowed; it must fail closed")

    for marker in scope.excluded_note_markers:
        marked = authorize_resource(
            scope, replace(baseline, notes=f"Series notes. {marker.upper()} 2026 by the owner.")
        )
        if marked.allowed:
            failures.append(f"a resource whose notes contain {marker!r} is allowed")

    return tuple(failures)


# ------------------------------------------------------------------- registry

CAPABILITIES: dict[str, ComplianceCapability] = {
    capability.name: capability
    for capability in (
        ComplianceCapability(
            name="source-attribution-display",
            description=(
                "Resolves a source's attribution obligation into displayable elements, and "
                "refuses to produce output when a required element is missing. Shared by "
                "World Bank, Eurostat and FRED, parameterised by their differing obligations."
            ),
            check=_check_attribution_surface,
        ),
        ComplianceCapability(
            name="dataset-licence-filter",
            description=(
                "Allows only resources whose recorded licence is on the approved allowlist, "
                "and denies a resource whose licence was never recorded."
            ),
            check=_check_licence_allowlist,
        ),
        ComplianceCapability(
            name="eurostat-geographic-filter",
            description=(
                "Allows only resources whose geographies are inside the approved set, and "
                "denies a resource that names none. Generic allowlist mechanism; the name is "
                "the one Mission 1.3 gave the condition."
            ),
            check=_check_geography_allowlist,
        ),
        ComplianceCapability(
            name="eurostat-trade-exclusion",
            description=(
                "Denies the enumerated carve-outs the source's terms name, and denies a "
                "resource that matches one dimension of a carve-out while leaving another "
                "unrecorded."
            ),
            check=_check_enumerated_exclusions,
        ),
        ComplianceCapability(
            name="fred-copyright-series-filter",
            description=(
                "Denies resources whose notes carry a third-party ownership marker, and "
                "denies resources whose notes were never read. Generic marker mechanism; the "
                "name is the one Mission 1.3 gave the condition."
            ),
            check=_check_note_marker_exclusion,
        ),
    )
}


def capability(name: str) -> ComplianceCapability | None:
    """`None` for an unregistered name. The caller reports UNKNOWN, never
    SATISFIED: a condition naming a capability nobody built is not a condition
    that holds (§19)."""
    return CAPABILITIES.get(name)


def capability_failures(name: str, compliance: SourceCompliance) -> tuple[str, ...] | None:
    """Run one capability's check. `None` means the capability is not registered."""
    entry = CAPABILITIES.get(name)
    if entry is None:
        return None
    return entry.check(compliance)
