"""The resource gate: which of a source's resources the approval actually covers.

Mission 1.4 §11 and §12. This is the module that stops a source-level approval
from being read as a resource-level one, and the reason it has to exist is
written into the Mission 1.3 evidence for all three approving sources:

    World Bank   CC-BY 4.0 is the DEFAULT licence. The same platform also
                 distributes Microdata under a research-only licence and
                 third-party data under external terms
    Eurostat     free re-use, EXCEPT material belonging to other sources,
                 non-EU/EFTA country data, and named trade-data exceptions
    FRED         series available through the API may be OWNED BY THIRD PARTIES,
                 and the Bank's provision of the API does not override their
                 copyrights

**Every rule denies; none permits.** `authorize_resource` starts from a refusal
and a resource is allowed only when no rule objected. A descriptor that omits
the field a rule needs is denied by that rule, because an unexamined resource is
not a resource known to be covered (§12).

The rules are a fixed set demanded by the nine conditions, not a general
expression language. A rule language would let a future reviewer encode a legal
sentence as a boolean expression, which §4 exists to prevent.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sros_contracts import ResourceContentOrigin, RightsBasis

from .config import EnumeratedExclusion, ResourceScope

__all__ = ["ResourceAuthorization", "ResourceDescriptor", "authorize_resource"]


@dataclass(frozen=True)
class ResourceDescriptor:
    """What is known about one dataset, series or resource.

    Every field except the two identifiers defaults to "not established", and
    every rule treats "not established" as a refusal. That asymmetry is the
    whole design: a collector that knows nothing about a resource must not be
    able to reach it by knowing nothing.
    """

    source_id: str
    resource_id: str

    licence: str | None = None
    # What kind of thing authorises this resource. `None` is "not established",
    # which every rule that cares about rights treats as a refusal -- the same
    # asymmetry the rest of this descriptor is built on.
    rights_basis: RightsBasis | None = None
    content_origin: ResourceContentOrigin = ResourceContentOrigin.UNKNOWN
    dataset_family: str | None = None
    dataset_doi: str | None = None

    geographies: tuple[str, ...] = ()
    declaring_country: str | None = None
    classifications: tuple[str, ...] = ()
    period_start_year: int | None = None

    notes: str | None = None


@dataclass(frozen=True)
class ResourceAuthorization:
    """Whether one resource may be requested, and every reason against it."""

    source_id: str
    resource_id: str
    allowed: bool
    denial_reasons: tuple[str, ...] = ()
    rules_evaluated: tuple[str, ...] = field(default=())

    def __bool__(self) -> bool:
        return self.allowed

    def to_json(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "resource_id": self.resource_id,
            "allowed": self.allowed,
            "denial_reasons": list(self.denial_reasons),
            "rules_evaluated": list(self.rules_evaluated),
        }


def authorize_resource(
    scope: ResourceScope, descriptor: ResourceDescriptor
) -> ResourceAuthorization:
    """Evaluate every rule and report all refusals, not the first.

    All of them, for the same reason the eligibility gate reports all of its
    blockers: a caller who fixes one and rediscovers the next on the following
    call learns to distrust the gate.
    """
    reasons: list[str] = []
    evaluated: list[str] = []

    if descriptor.source_id != scope.source_id:
        # Not a rule failure -- a mismatched pairing. Reported as a refusal
        # because silently evaluating one source's rules against another
        # source's resource is exactly the sort of thing that passes review.
        return ResourceAuthorization(
            source_id=scope.source_id,
            resource_id=descriptor.resource_id,
            allowed=False,
            denial_reasons=(
                f"resource belongs to {descriptor.source_id!r} but was checked against "
                f"the scope of {scope.source_id!r}",
            ),
        )

    # -- third-party content (§12) ------------------------------------------
    if scope.third_party_denied:
        evaluated.append("content-origin")
        if descriptor.content_origin is ResourceContentOrigin.THIRD_PARTY:
            reasons.append(
                "resource is third-party content; the platform's approval grants no "
                "rights over it and permission must come from the owner"
            )
        elif descriptor.content_origin is ResourceContentOrigin.UNKNOWN:
            reasons.append(
                "resource content origin is UNKNOWN; licensing scope matters here, so "
                "an unestablished origin is denied rather than assumed"
            )

    # -- rights basis (Mission 1.9.2) ---------------------------------------
    #
    # Unconditional, unlike every rule below it. Those answer questions a
    # particular review may or may not have asked -- which licences, which
    # geographies, which families. This one answers "what authorises this at
    # all", and no review can leave that optional.
    #
    # It had been checked only inside the licence-allowlist rule, so a
    # descriptor with NO established basis passed for every source whose scope
    # enumerates no licences -- which is Eurostat, FRED and, pointedly, GDELT,
    # the one source whose resources are authorised by a direct grant rather
    # than by a licence. "Nothing established" read as approval on exactly the
    # source where the basis is the whole story.
    evaluated.append("rights-basis")
    if descriptor.rights_basis is None:
        reasons.append(
            "resource has no established rights basis; a resource that cannot say what "
            "authorises it -- a named licence, or the source's own grant -- is not one "
            "known to be authorised by anything"
        )

    # -- licence allowlist ---------------------------------------------------
    #
    # Mission 1.9.1 §15. A scope that enumerates acceptable LICENCES is asking a
    # question only a NAMED_LICENCE resource can answer. A direct terms grant is
    # a real and often broader authorisation, and it is not a licence -- so it
    # fails this rule rather than passing it by having nothing to compare.
    #
    # Reported as a basis mismatch rather than as a missing licence, because the
    # two call for different fixes and a reader chasing the wrong one loses an
    # afternoon.
    if scope.licence_allowlist is not None:
        evaluated.append("licence-allowlist")
        if descriptor.rights_basis is None:
            reasons.append(
                "resource has no established rights basis; this scope enumerates "
                "acceptable licences, and an unestablished basis is not a basis"
            )
        elif descriptor.rights_basis is not RightsBasis.NAMED_LICENCE:
            reasons.append(
                f"resource is authorised by {descriptor.rights_basis.value} and this "
                f"scope requires a named licence from {sorted(scope.licence_allowlist)}. "
                "A direct grant does not satisfy a licence allowlist"
            )
        elif descriptor.licence is None:
            reasons.append(
                "resource has no recorded licence; the licence is a dataset property "
                f"and must be one of {sorted(scope.licence_allowlist)}"
            )
        elif descriptor.licence not in scope.licence_allowlist:
            reasons.append(
                f"licence {descriptor.licence!r} is not in the approved allowlist "
                f"{sorted(scope.licence_allowlist)}"
            )

    # -- dataset family exclusion -------------------------------------------
    if (
        scope.excluded_dataset_families
        or scope.require_dataset_family
        or scope.allowed_dataset_families is not None
    ):
        evaluated.append("dataset-family")
        if descriptor.dataset_family is None:
            if scope.require_dataset_family or scope.allowed_dataset_families is not None:
                reasons.append(
                    "resource dataset family is unrecorded; an unclassified dataset is "
                    f"not one known to fall outside {sorted(scope.excluded_dataset_families)}"
                )
        elif descriptor.dataset_family in scope.excluded_dataset_families:
            reasons.append(
                f"dataset family {descriptor.dataset_family!r} is excluded by the review"
            )
        elif (
            scope.allowed_dataset_families is not None
            and descriptor.dataset_family not in scope.allowed_dataset_families
        ):
            # Mission 1.9.2 §22. The exclusion list above answers "was this
            # rejected"; this answers "was it ever looked at". Without it a
            # descriptor could name any family it liked and pass, because a
            # string nobody had rejected was indistinguishable from one
            # somebody had approved.
            reasons.append(
                f"dataset family {descriptor.dataset_family!r} is not one this review "
                f"assessed {sorted(scope.allowed_dataset_families)}. An unreviewed family "
                "is not an approved one, whether or not anybody thought to exclude it"
            )

    # -- geography allowlist -------------------------------------------------
    if scope.geography_allowlist is not None:
        evaluated.append("geography-allowlist")
        if not descriptor.geographies:
            reasons.append(
                "resource names no geography; the approval is limited to an enumerated "
                "set of countries and cannot cover an unstated one"
            )
        else:
            outside = sorted(set(descriptor.geographies) - scope.geography_allowlist)
            if outside:
                reasons.append(
                    f"geographies {outside} are outside the approved set for commercial reuse"
                )

    # -- enumerated exclusions ----------------------------------------------
    for exclusion in scope.enumerated_exclusions:
        evaluated.append(f"exclusion:{exclusion.key}")
        matched = _matches_exclusion(exclusion, descriptor)
        if matched is not None:
            reasons.append(f"excluded by {exclusion.key}: {matched}")

    # -- note markers (third-party copyright detection) ----------------------
    if scope.excluded_note_markers:
        evaluated.append("note-markers")
        if descriptor.notes is None:
            if scope.require_notes:
                reasons.append(
                    "resource notes were not read; the terms make copyrighted resources "
                    "identifiable BY their notes, so an absent note is an unanswered "
                    "question rather than a clean answer"
                )
        else:
            lowered = descriptor.notes.lower()
            hits = sorted({m for m in scope.excluded_note_markers if m.lower() in lowered})
            if hits:
                reasons.append(
                    f"resource notes contain {hits}, which marks it as owned by a third "
                    "party. Permission must come from that owner and cannot be granted here"
                )

    return ResourceAuthorization(
        source_id=scope.source_id,
        resource_id=descriptor.resource_id,
        allowed=not reasons,
        denial_reasons=tuple(reasons),
        rules_evaluated=tuple(evaluated),
    )


def _matches_exclusion(
    exclusion: EnumeratedExclusion, descriptor: ResourceDescriptor
) -> str | None:
    """Return why the exclusion applies, or `None` when it does not.

    Each dimension the exclusion states resolves to one of three answers, and
    the combination rule is the part that matters:

        NEGATIVE  the descriptor positively falls outside this dimension.
                  The exclusion does not apply, full stop -- Austrian CN-8
                  data is not excluded by the Liechtenstein rule
        POSITIVE  the descriptor positively falls inside it
        UNKNOWN   the descriptor does not say

    One NEGATIVE answer clears the exclusion. Otherwise, if at least one
    dimension positively matched and any other is UNKNOWN, the exclusion
    applies: a resource that is trade data in an excluded classification and
    does not say who declared it is not a resource known to be declared by
    someone else.

    A descriptor that matches nothing positively -- an ordinary statistics
    dataset with no trade classification -- is not excluded. Denying it would
    turn the rule into a blanket refusal, which is a check that has stopped
    checking anything.
    """
    matched: list[str] = []
    unknown: list[str] = []

    if exclusion.classifications:
        if not descriptor.classifications:
            unknown.append("classification")
        elif set(descriptor.classifications) & exclusion.classifications:
            matched.append("classification")
        else:
            return None

    if exclusion.declaring_countries:
        if descriptor.declaring_country is None:
            unknown.append("declaring country")
        elif descriptor.declaring_country in exclusion.declaring_countries:
            matched.append("declaring country")
        else:
            return None

    if exclusion.from_year is not None:
        if descriptor.period_start_year is None:
            unknown.append("period")
        elif descriptor.period_start_year >= exclusion.from_year:
            matched.append("period")
        else:
            return None

    if not matched:
        return None
    if unknown:
        return (
            f"{', '.join(matched)} matches and {', '.join(unknown)} is unrecorded, so the "
            f"resource cannot be ruled out. {exclusion.reason}"
        )
    return exclusion.reason
