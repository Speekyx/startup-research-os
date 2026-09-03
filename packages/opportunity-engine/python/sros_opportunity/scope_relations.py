"""Relations between scopes, and the roles Evidence may take because of one.

Mission 1.34 §4 to §7. The procedure is `scope-relation-registry@1.0.0`.

**A relation is an edge somebody drew, not a fact the data implies.** Nothing in
this module derives a relation: no distance, no token overlap, no stem, no
synonym table, no embedding, no model. A relation exists because a source's own
vocabulary states it or because a person read two identifiers and recorded that
one contains the other, with a basis.

**The registry ships EMPTY, and that is the mission's result rather than an
oversight** (§29, §33). Mission 1.33 refused to assert which commercial category
contains Docker, and Mission 1.34 preserves that refusal: the capability to
represent such an edge exists, and no edge is invented to demonstrate it.

**NO TRANSITIVE EXPANSION IN V1** (§4). If a product is within a category and
that category is within a market, this module does not conclude that the product
is within the market. Each edge is asked for by name. Transitivity looks free and
is not: it silently multiplies what a single reviewed edge licenses, and the
review that authorised the first edge never saw the third.

**A relation asserts the named relation and nothing more** (§5). `WITHIN` says
the narrower scope falls inside the broader one. It does not say they are
interchangeable, that what is true of one is true of the other, or that the
narrower is representative of the broader. §7's whole argument is that the
containment holds and the inference does not.
"""

from __future__ import annotations

import enum
import json
import pathlib
from dataclasses import dataclass

from .scopes import ObservationScope, ScopeOrigin, SubjectScopeType

__all__ = [
    "SCOPE_RELATION_REGISTRY_VERSION",
    "ScopeRelationType",
    "ScopeRelationStatus",
    "ScopeRelation",
    "ScopeRelationRegistry",
    "EvidenceSupportRole",
    "load_scope_relations",
]

SCOPE_RELATION_REGISTRY_VERSION = "scope-relation-registry@1.0.0"


class ScopeRelationType(enum.Enum):
    """The three containments §4 names, each between a stated pair of levels.

    The pairs are enforced rather than documented: a relation claiming a PRODUCT
    is within a PRODUCT, or a CATEGORY within a GEOGRAPHY under
    `CATEGORY_WITHIN_MARKET`, is refused at construction. A typed edge whose
    endpoints are not of its declared types is an edge that means something else.
    """

    SUBJECT_WITHIN_CATEGORY = "SUBJECT_WITHIN_CATEGORY"
    CATEGORY_WITHIN_MARKET = "CATEGORY_WITHIN_MARKET"
    SCOPE_WITHIN_GEOGRAPHY = "SCOPE_WITHIN_GEOGRAPHY"

    @property
    def permitted_endpoints(self) -> tuple[frozenset[SubjectScopeType], SubjectScopeType]:
        """(permitted narrower types, required broader type)."""
        if self is ScopeRelationType.SUBJECT_WITHIN_CATEGORY:
            return frozenset({SubjectScopeType.PRODUCT}), SubjectScopeType.CATEGORY
        if self is ScopeRelationType.CATEGORY_WITHIN_MARKET:
            return frozenset({SubjectScopeType.CATEGORY}), SubjectScopeType.MARKET
        return (
            frozenset(
                {
                    SubjectScopeType.PRODUCT,
                    SubjectScopeType.CATEGORY,
                    SubjectScopeType.MARKET,
                }
            ),
            SubjectScopeType.GEOGRAPHY,
        )


class ScopeRelationStatus(enum.Enum):
    """`ACTIVE` alone licenses anything. A withdrawn edge is kept, not deleted,
    for the reason a superseded review is kept: the useful history is that
    somebody concluded it and then did not."""

    ACTIVE = "ACTIVE"
    WITHDRAWN = "WITHDRAWN"


class EvidenceSupportRole(enum.Enum):
    """§6. Why one Evidence row is in one Opportunity's packet.

    The distinction the whole mission turns on. A contextual row must never
    become a direct one by being counted, aggregated or serialised, and these are
    separate members rather than a flag so that no default lands on the
    permissive value.
    """

    #: The row's observation scope IS the Opportunity's subject scope. The only
    #: role that says anything about the subject itself.
    DIRECT_SUBJECT_EVIDENCE = "DIRECT_SUBJECT_EVIDENCE"
    #: The row observes a broader scope that an ACTIVE reviewed relation says
    #: contains the Opportunity's subject. It bears on that broader scope and on
    #: nothing narrower.
    BROADER_SCOPE_CONTEXT = "BROADER_SCOPE_CONTEXT"
    #: The row observes a place rather than the subject. Kept apart from
    #: `BROADER_SCOPE_CONTEXT` because a country is not a bigger version of a
    #: product, and merging them would let a macroeconomic series read as
    #: category context.
    GEOGRAPHIC_CONTEXT = "GEOGRAPHIC_CONTEXT"

    @property
    def is_direct(self) -> bool:
        return self is EvidenceSupportRole.DIRECT_SUBJECT_EVIDENCE


@dataclass(frozen=True)
class ScopeRelation:
    """One reviewed edge, carrying everything needed to re-check it."""

    narrower_scope_id: str
    narrower_scope_type: SubjectScopeType
    broader_scope_id: str
    broader_scope_type: SubjectScopeType
    relation_type: ScopeRelationType
    origin: ScopeOrigin
    #: What a person read, or which published vocabulary states the containment.
    basis: str
    reviewed_by: str
    reviewed_at: str
    status: ScopeRelationStatus = ScopeRelationStatus.ACTIVE
    procedure_version: str = SCOPE_RELATION_REGISTRY_VERSION

    def __post_init__(self) -> None:
        permitted_narrower, required_broader = self.relation_type.permitted_endpoints
        if self.narrower_scope_type not in permitted_narrower:
            raise ValueError(
                f"{self.relation_type.value} cannot take a "
                f"{self.narrower_scope_type.value} as its narrower endpoint. A typed "
                "edge whose endpoints are not of its declared types is an edge that "
                "means something else."
            )
        if self.broader_scope_type is not required_broader:
            raise ValueError(
                f"{self.relation_type.value} requires a {required_broader.value} as its "
                f"broader endpoint, not {self.broader_scope_type.value}."
            )
        if self.narrower_scope_id == self.broader_scope_id:
            raise ValueError(
                f"{self.narrower_scope_id!r} cannot contain itself. A reflexive edge "
                "would make every scope its own broader context and admit every row."
            )
        if not self.basis.strip():
            raise ValueError(
                f"{self.narrower_scope_id!r} -> {self.broader_scope_id!r}: no basis. §5 "
                "requires a relation to say how it was established; an edge nobody can "
                "re-check is an assertion wearing a data structure."
            )
        if self.origin is ScopeOrigin.HUMAN_REVIEWED and not self.reviewed_by.strip():
            raise ValueError(
                f"{self.narrower_scope_id!r} -> {self.broader_scope_id!r}: "
                "HUMAN_REVIEWED with nobody named. A human review is attributable or it "
                "is not a human review."
            )

    @property
    def active(self) -> bool:
        return self.status is ScopeRelationStatus.ACTIVE


@dataclass(frozen=True)
class ScopeRelationRegistry:
    """Edges, matched by exact scope-id equality and by nothing else."""

    registry_version: str
    relations: tuple[ScopeRelation, ...]

    def __post_init__(self) -> None:
        seen: set[tuple[str, str, str]] = set()
        for relation in self.relations:
            token = (
                relation.narrower_scope_id,
                relation.broader_scope_id,
                relation.relation_type.value,
            )
            if token in seen:
                raise ValueError(
                    f"{token} appears twice. One edge is one decision, and two rows for "
                    "it is two answers to one question."
                )
            seen.add(token)

    def relation_between(
        self, narrower: ObservationScope, broader: ObservationScope
    ) -> ScopeRelation | None:
        """The ACTIVE edge saying `broader` contains `narrower`, or None.

        **Exact equality on both endpoints, and no transitive search** (§4). This
        walks nothing: an edge is present or it is absent, and absence is the
        answer rather than a prompt to look further.
        """
        if not (narrower.resolved and broader.resolved):
            return None
        for relation in self.relations:
            if not relation.active:
                continue
            if (
                relation.narrower_scope_id == narrower.scope_id
                and relation.broader_scope_id == broader.scope_id
                and relation.narrower_scope_type is narrower.scope_type
                and relation.broader_scope_type is broader.scope_type
            ):
                return relation
        return None


def _scope_type(raw: object, where: str) -> SubjectScopeType:
    try:
        return SubjectScopeType(str(raw))
    except ValueError as exc:
        raise ValueError(f"{where}: {raw!r} is not a SubjectScopeType") from exc


def load_scope_relations(path: pathlib.Path) -> ScopeRelationRegistry:
    """Read the reviewed relation registry. An empty registry is a valid one."""
    document = json.loads(path.read_text(encoding="utf-8"))
    version = str(document.get("registry_version", ""))
    if not version:
        raise ValueError(
            f"{path.name}: no registry_version. A registry that cannot name its own "
            "procedure cannot be cited by a packet that used it."
        )

    relations: list[ScopeRelation] = []
    for index, row in enumerate(document.get("relations", [])):
        where = f"{path.name} relation {index}"
        relations.append(
            ScopeRelation(
                narrower_scope_id=str(row["narrower_scope_id"]),
                narrower_scope_type=_scope_type(row["narrower_scope_type"], where),
                broader_scope_id=str(row["broader_scope_id"]),
                broader_scope_type=_scope_type(row["broader_scope_type"], where),
                relation_type=ScopeRelationType(str(row["relation_type"])),
                origin=ScopeOrigin(str(row["origin"])),
                basis=str(row["basis"]),
                reviewed_by=str(row.get("reviewed_by", "")),
                reviewed_at=str(row.get("reviewed_at", "")),
                status=ScopeRelationStatus(str(row.get("status", "ACTIVE"))),
            )
        )
    return ScopeRelationRegistry(registry_version=version, relations=tuple(relations))
