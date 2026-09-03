"""A dimension that cannot be read without the scope it was observed at.

Mission 1.34 §6 to §8, §15, §16, §25, §26. The procedure is
`scope-aware-evidence@1.0.0`.

**The flattening this exists to make impossible.** `OpportunityHypothesis`
carries `supported_dimensions` as a bare `frozenset[EvidenceDimension]`, so a
`MARKET_ACTIVITY` observed of a procurement CATEGORY and a `PROBLEM_OR_NEED`
observed of the PRODUCT are the same shape in the same set, and *Docker supports
MARKET_ACTIVITY* is one `in` away. A `ScopedDimension` is a triple -- dimension,
scope, role -- and the triple has no accessor that returns the dimension without
its scope.

**NO FACTUAL DIMENSION PROPAGATION** (§25). Nothing here converts a dimension
observed at a broader scope into a dimension of a narrower one. There is no
inheritance, no promotion, no "with lower confidence" variant, and no parameter
that would enable one. A broader observation is retained AT ITS OWN SCOPE and
described as such, which is the only honest thing to do with it:

    CATEGORY:X has MARKET_ACTIVITY   stays   context(CATEGORY:X).MARKET_ACTIVITY
                                     never   product(docker).MARKET_ACTIVITY

**What may propagate is exactly nothing factual.** One thing travels and it is
not a dimension: the RELATION, which is why the row is in the packet at all, and
which is carried on the row so a reader can see the containment that admitted it.
Naming that as propagation would be generous -- it is provenance.

**Scope laundering is a shape, not a wording** (§16). Every refusal in this
module names the scope the conclusion moved to, because a message saying only
*not permitted* leaves a reader to guess which half was wrong.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dimensions import DIMENSION_DEFINITIONS, EvidenceDimension
from .facets import EvidenceFacets
from .scope_relations import (
    EvidenceSupportRole,
    ScopeRelation,
    ScopeRelationRegistry,
)
from .scopes import ObservationScope, SubjectScopeType

__all__ = [
    "SCOPE_AWARE_EVIDENCE_VERSION",
    "ScopedDimension",
    "ScopedEvidence",
    "ContextAdmission",
    "ContextRefusalReason",
    "admit_evidence",
]

SCOPE_AWARE_EVIDENCE_VERSION = "scope-aware-evidence@1.0.0"


@dataclass(frozen=True)
class ScopedDimension:
    """One dimension, at one scope, in one role. Never separable.

    There is deliberately no `.dimension` shortcut that drops the scope, and no
    `__str__` that renders the dimension alone: the two most convenient ways to
    lose the qualifier are the two this class does not offer.
    """

    dimension: EvidenceDimension
    scope: ObservationScope
    role: EvidenceSupportRole

    def __post_init__(self) -> None:
        if not self.scope.resolved:
            raise ValueError(
                f"{self.dimension.value} carried at an UNDETERMINED scope. A dimension "
                "whose scope nobody established is a dimension attached to no subject, "
                "and the first reader to see it will supply the Opportunity's."
            )
        if self.role.is_direct and self.scope.scope_type is not SubjectScopeType.PRODUCT:
            # Not a rule about products as such: DIRECT means the row observes the
            # Opportunity's own subject, and every Opportunity subject in this
            # repository is a PRODUCT. `admit_evidence` checks the identity
            # properly; this catches a hand-built triple that skipped it.
            raise ValueError(
                f"{self.dimension.value}: DIRECT_SUBJECT_EVIDENCE at scope type "
                f"{self.scope.scope_type.value if self.scope.scope_type else 'NONE'}. "
                "Direct means the row observes the subject itself."
            )

    def statement(self) -> str:
        """The sentence a report or a prompt may use, with the scope inside it.

        §26's wording contract. The scope is in the SUBJECT of the sentence
        rather than in a trailing qualifier, because a qualifier is what a
        summariser drops.
        """
        if self.role.is_direct:
            return (
                f'{self.dimension.value} is observed of "{self.scope.display_name}", '
                f"which is the subject of this Opportunity."
            )
        if self.role is EvidenceSupportRole.BROADER_SCOPE_CONTEXT:
            return (
                f'{self.dimension.value} is observed of "{self.scope.display_name}", a '
                f"broader {self.scope.scope_type.value} that contains this "
                f"Opportunity's subject. It is not observed of the subject."
                if self.scope.scope_type
                else ""
            )
        return (
            f'{self.dimension.value} is observed of "{self.scope.display_name}", the '
            f"geography this Opportunity is considered in. It is not observed of the "
            f"subject."
        )

    def limitation(self) -> str:
        """What this triple does not establish, quoting the taxonomy first."""
        never = DIMENSION_DEFINITIONS[self.dimension].never_means
        base = "; ".join(f"not {phrase}" for phrase in never)
        if self.role.is_direct:
            return base
        return (
            f"{base}. And, because this is {self.role.value}: nothing about the "
            f"Opportunity's own subject. An observation of "
            f'"{self.scope.display_name}" establishes a property of '
            f'"{self.scope.display_name}" and of nothing inside it.'
        )


class ContextRefusalReason:
    """Why one row may not join one Opportunity's packet. Strings, so a refusal
    reads as a sentence in a report rather than as a code somebody must look up."""

    SCOPE_UNDETERMINED = "SCOPE_UNDETERMINED"
    OPPORTUNITY_SCOPE_UNDETERMINED = "OPPORTUNITY_SCOPE_UNDETERMINED"
    NO_PERMITTED_RELATION = "NO_PERMITTED_RELATION"
    NO_DIMENSION = "NO_DIMENSION"
    GOVERNANCE_NOT_ESTABLISHED = "GOVERNANCE_NOT_ESTABLISHED"


@dataclass(frozen=True)
class ScopedEvidence:
    """One admitted Evidence row, with the role and relation that admitted it."""

    facets: EvidenceFacets
    scope: ObservationScope
    role: EvidenceSupportRole
    #: `None` for DIRECT rows: no edge is needed to observe your own subject.
    admitting_relation: ScopeRelation | None
    scoped_dimensions: tuple[ScopedDimension, ...]

    def __post_init__(self) -> None:
        if not self.role.is_direct and self.admitting_relation is None:
            raise ValueError(
                f"{self.facets.evidence_id}: {self.role.value} with no admitting "
                "relation. §15 admits a contextual row only through an explicit edge, "
                "and a row that cannot name the edge that let it in did not come "
                "through the gate."
            )
        if self.role.is_direct and self.admitting_relation is not None:
            raise ValueError(
                f"{self.facets.evidence_id}: DIRECT with an admitting relation. A row "
                "observing the subject itself is not admitted BY a containment, and "
                "recording one would suggest the subject is inside something."
            )


@dataclass(frozen=True)
class ContextAdmission:
    """The gate's answer: an admitted row, or a refusal that says which clause."""

    admitted: ScopedEvidence | None
    refusal_reason: str | None
    detail: str

    @property
    def ok(self) -> bool:
        return self.admitted is not None


def admit_evidence(
    facets: EvidenceFacets,
    evidence_scope: ObservationScope,
    opportunity_scope: ObservationScope,
    relations: ScopeRelationRegistry,
    *,
    governance_permits_processing: bool,
) -> ContextAdmission:
    """§15's gate, evaluated in order, failing closed on every clause.

    Six conditions. The order is deliberate: scope before relation before
    dimension before governance, so a refusal names the FIRST thing missing
    rather than the last, and an operator fixing them works from the outside in.

    **The sixth is enforced upstream, and is not re-checked.** `EvidenceFacets`
    refuses dimensions with no bound and `ObservationScope` refuses a resolved
    scope with no basis, so provenance is preserved before a row reaches this
    function. A duplicate check here could never fire, and an unreachable guard
    reads as protection while protecting nothing.

    **Two of the remaining five are CONTEXT conditions and are applied only to
    contextual rows.** §15 states its list for broader-scope inclusion, and a direct row is
    not being included on the strength of anything: it observes the subject. So a
    direct row needs a resolved scope on both sides, scope identity, governance
    and provenance -- and needs neither a relation (there is nothing to relate)
    nor a dimension (Mission 1.32 put a deliberately dimensionless row in the
    Docker packet and it belongs there).

    **Absence is refusal, never a prompt to search.** There is no fallback to a
    broader relation, no transitive walk, no nearest-scope match and no
    similarity anywhere in this function.
    """
    if not evidence_scope.resolved:
        return ContextAdmission(
            None,
            ContextRefusalReason.SCOPE_UNDETERMINED,
            f"{facets.evidence_id}: this row's observation scope is UNDETERMINED. §12 "
            "forbids manufacturing one, so it is not attached -- to this Opportunity or "
            "to any other.",
        )
    if not opportunity_scope.resolved:
        return ContextAdmission(
            None,
            ContextRefusalReason.OPPORTUNITY_SCOPE_UNDETERMINED,
            f"{facets.evidence_id}: the Opportunity's own subject scope is "
            "UNDETERMINED. Nothing can be related to a scope nobody established.",
        )

    direct = evidence_scope.describes_same_scope_as(opportunity_scope)
    relation: ScopeRelation | None = None
    role = EvidenceSupportRole.DIRECT_SUBJECT_EVIDENCE

    if not direct:
        relation = relations.relation_between(opportunity_scope, evidence_scope)
        if relation is None:
            return ContextAdmission(
                None,
                ContextRefusalReason.NO_PERMITTED_RELATION,
                f"{facets.evidence_id}: observes {evidence_scope.scope_id!r} while this "
                f"Opportunity is about {opportunity_scope.scope_id!r}, and no ACTIVE "
                "reviewed relation says the second is contained in the first. §15 "
                "admits nothing on resemblance, so this row is refused rather than "
                "attached weakly.",
            )
        role = (
            EvidenceSupportRole.GEOGRAPHIC_CONTEXT
            if evidence_scope.scope_type is SubjectScopeType.GEOGRAPHY
            else EvidenceSupportRole.BROADER_SCOPE_CONTEXT
        )

    # §15's dimension clause is a CONTEXT condition and is applied only to
    # contextual rows. A DIRECT row with no dimension is still a row about the
    # subject: Mission 1.32 created exactly one, deliberately mapped it to
    # `frozenset()`, and deliberately left it in the packet. Refusing it here
    # would make the scoped packet quietly disagree with the packet it must
    # remain compatible with, which is the opposite of what §10 and §11 ask.
    if not direct and not facets.dimensions:
        return ContextAdmission(
            None,
            ContextRefusalReason.NO_DIMENSION,
            f"{facets.evidence_id}: offered as {role.value} and carries no Opportunity "
            "dimension, so there is nothing for a scope to qualify. A row with no "
            "dimension is not made useful by observing a broader scope.",
        )
    if not governance_permits_processing:
        return ContextAdmission(
            None,
            ContextRefusalReason.GOVERNANCE_NOT_ESTABLISHED,
            f"{facets.evidence_id}: the governance standing for its source does not "
            "establish the intended processing under the active use profile. A scope "
            "relation is not a permission (§28).",
        )
    # §15's sixth clause -- provenance is preserved -- is enforced UPSTREAM and is
    # deliberately not re-checked here. `EvidenceFacets.__post_init__` already
    # refuses dimensions carried with no bound, and `ObservationScope` already
    # refuses a RESOLVED scope with no basis, so a row reaching this line has
    # both. Writing the check again would be a guard that cannot fire, which is
    # worse than no guard: it reads as protection and protects nothing. The
    # tests assert the two upstream constructors instead.

    return ContextAdmission(
        ScopedEvidence(
            facets=facets,
            scope=evidence_scope,
            role=role,
            admitting_relation=relation,
            scoped_dimensions=tuple(
                ScopedDimension(dimension=d, scope=evidence_scope, role=role)
                for d in sorted(facets.dimensions, key=lambda d: d.value)
            ),
        ),
        None,
        f"{facets.evidence_id}: admitted as {role.value} at {evidence_scope.scope_id!r}.",
    )
