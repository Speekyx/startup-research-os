"""What LEVEL OF THING an observation is about, kept apart from WHERE it is.

Mission 1.34 §1 to §3. The procedure is `observation-scope@1.0.0`.

**The assumption this exists to break.** Before this module, `build_packet` took a
set of Evidence rows and unioned their dimensions with no scope term in the
expression, so any row in a packet contributed its dimensions to that packet's
subject unconditionally. Membership WAS the claim of aboutness. That is fine
while every row observes the packet's own subject, and it is exactly wrong the
moment a procurement notice about a purchasing CATEGORY sits beside a question
about a PRODUCT.

**Subject scope is not geographic scope, and merging them would be the Mission
1.15.4 shape again** -- one field answering a question that is two.
`MarketScope` (Ontology V2 §4) says WHERE an Opportunity applies:
`GLOBAL | REGION | COUNTRY | MULTI_COUNTRY`. `SubjectScopeType` says what level
of thing an observation is about. They are orthogonal, and a CATEGORY observed
in one COUNTRY is an ordinary combination rather than a contradiction.

**GEOGRAPHY appears in both vocabularies and means different things in each**,
which is worth stating rather than leaving to a reader. As a `MarketScope` it
answers *where does this Opportunity apply*. As a `SubjectScopeType` it answers
*what is this observation about*, and the answer is a place: a World Bank
population series is an observation whose SUBJECT is Germany. §17 keeps them
orthogonal and this module never converts one into the other.

**Scope identity is deterministic or reviewed, and never resembled** (§3). There
is no string distance, no token overlap, no stem, no synonym table, no embedding
and no model matching anywhere in this module -- the same rule the canonical
subject registry has carried since Mission 1.30, applied one level out.

**A scope that cannot be established is UNDETERMINED, and UNDETERMINED fails
closed** (§12). It is a state, not a type: adding a fifth scope type to hold the
rows nobody has classified would put an absence into the vocabulary, where every
consumer branching exhaustively would treat it as a kind of thing. Nothing is
mass-labelled `PRODUCT` to make the corpus tidy.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

__all__ = [
    "OBSERVATION_SCOPE_VERSION",
    "SubjectScopeType",
    "ScopeStatus",
    "ScopeOrigin",
    "ObservationScope",
    "SCOPE_TYPE_DEFINITIONS",
]

OBSERVATION_SCOPE_VERSION = "observation-scope@1.0.0"


class SubjectScopeType(enum.Enum):
    """Four levels, each with a meaning rather than a position in a hierarchy.

    §1 forbids defining `PRODUCT` merely as *narrower than CATEGORY*. A vocabulary
    whose members are defined by their neighbours cannot say whether a new case
    belongs to it, and cannot refuse one.
    """

    PRODUCT = "PRODUCT"
    CATEGORY = "CATEGORY"
    MARKET = "MARKET"
    GEOGRAPHY = "GEOGRAPHY"


@dataclass(frozen=True)
class ScopeTypeDefinition:
    scope_type: SubjectScopeType
    means: str
    #: What a reader would otherwise take this level to be. Non-empty by
    #: construction, for the reason `EvidenceDimension` carries `never_means`.
    never_means: tuple[str, ...]
    example_in_this_repository: str

    def __post_init__(self) -> None:
        if not self.never_means:
            raise ValueError(
                f"{self.scope_type.value}: a scope type with no stated confusion is a "
                "label. The confusions are the definition's working part."
            )


SCOPE_TYPE_DEFINITIONS: dict[SubjectScopeType, ScopeTypeDefinition] = {
    SubjectScopeType.PRODUCT: ScopeTypeDefinition(
        scope_type=SubjectScopeType.PRODUCT,
        means=(
            "One bounded, separately identifiable thing that somebody built and "
            "publishes under a name: a product, project, platform or application. "
            "It is identifiable independently of any classification it happens to "
            "fall into, and a person can point at it."
        ),
        never_means=(
            "the organisation that publishes it -- a vendor is a different subject, "
            "and the canonical registry says so of `docker` in its own words",
            "the category it belongs to, even where the product dominates that category",
            "the market it is sold into",
        ),
        example_in_this_repository="subject:docker, subject:kubernetes, subject:podman",
    ),
    SubjectScopeType.CATEGORY: ScopeTypeDefinition(
        scope_type=SubjectScopeType.CATEGORY,
        means=(
            "A published classification whose members are several distinct things. "
            "Its identity comes from the classification that defines it -- somebody "
            "else's vocabulary, with its own rules for what falls inside -- and not "
            "from any one member."
        ),
        never_means=(
            "any particular member of it, however typical",
            "that every member shares the properties observed of the category",
            "a market; a classification is how a publisher files things, and a market "
            "is where they are exchanged",
        ),
        example_in_this_repository="ted-eu:CPV-division:90, a Common Procurement Vocabulary division",
    ),
    SubjectScopeType.MARKET: ScopeTypeDefinition(
        scope_type=SubjectScopeType.MARKET,
        means=(
            "A bounded space of economic activity -- buyers, sellers and exchange -- "
            "broader than one classification, identified by the activity rather than "
            "by a filing rule. A market exists because things are traded in it, not "
            "because a taxonomy has a row for it."
        ),
        never_means=(
            "a classification that happens to be broad; CPV division 72 is a CATEGORY "
            "however wide it is",
            "a market SIZE, which no observation in this repository measures",
            "that the market is addressable, open or growing",
        ),
        example_in_this_repository=(
            "none. No registered source observes a market in this sense, and none is "
            "invented so the vocabulary looks complete."
        ),
    ),
    SubjectScopeType.GEOGRAPHY: ScopeTypeDefinition(
        scope_type=SubjectScopeType.GEOGRAPHY,
        means=(
            "A place, jurisdiction or region that is itself the SUBJECT of the "
            "observation. A World Bank population series is about Germany; Germany is "
            "the thing observed, and the indicator says what was measured of it."
        ),
        never_means=(
            "where an Opportunity applies -- that is `MarketScope` (Ontology V2 §4), a "
            "separate and orthogonal question this vocabulary never answers",
            "a market in that place",
            "that anything observed of the place is true of anything sold there",
        ),
        example_in_this_repository="world-bank:metric-geography:SP.POP.TOTL|DE",
    ),
}


class ScopeStatus(enum.Enum):
    """Whether the scope of an observation was established.

    `UNDETERMINED` is deliberately not a fifth `SubjectScopeType`: a state saying
    *nobody classified this* is a different kind of thing from a level, and a
    consumer branching exhaustively over levels must not silently acquire a
    branch for an absence.
    """

    RESOLVED = "RESOLVED"
    UNDETERMINED = "UNDETERMINED"


class ScopeOrigin(enum.Enum):
    """How a scope was established. §5's vocabulary, one level in.

    There is no `MODEL_INFERRED`, in this enum or anywhere else in the mission.
    """

    #: The source's own vocabulary says what kind of thing it publishes -- CPV
    #: calls itself a procurement classification, so a CPV division is a CATEGORY
    #: on the publisher's authority rather than on ours.
    SOURCE_NATIVE = "SOURCE_NATIVE"
    #: A person read the identifier and recorded what it names, in a registry,
    #: with a stated basis. The canonical subject registry's own mechanism.
    HUMAN_REVIEWED = "HUMAN_REVIEWED"
    #: Derived by an exact, versioned rule over identifiers already held. No
    #: distance, no threshold, no resemblance.
    DETERMINISTIC_REGISTRY = "DETERMINISTIC_REGISTRY"


@dataclass(frozen=True)
class ObservationScope:
    """What one Evidence row observes, and on whose authority.

    `geography` is OPTIONAL and independent (§3, §17). A CATEGORY observed within
    one country carries both; a PRODUCT observed with no geographic restriction
    carries the scope type and no geography, and the absence is not GLOBAL.
    """

    scope_type: SubjectScopeType | None
    #: Stable and addressable by equality. `subject:docker`,
    #: `ted-eu:CPV-division:90`. Never a display name.
    scope_id: str
    display_name: str
    status: ScopeStatus
    origin: ScopeOrigin | None
    #: The source-native identifiers this scope was established from, verbatim.
    source_native_identifiers: tuple[str, ...]
    #: Why this identifier names this level of thing. A scope with no basis is a
    #: classification nobody can re-check.
    basis: str
    procedure_version: str = OBSERVATION_SCOPE_VERSION
    #: An ISO 3166-1 alpha-2 code or a reviewed region token, where the
    #: observation is geographically bounded and that bound is separately known.
    #: `None` means UNASKED, and never GLOBAL.
    geography: str | None = None

    def __post_init__(self) -> None:
        if not self.scope_id.strip():
            raise ValueError("an ObservationScope with no scope_id addresses nothing")
        if self.status is ScopeStatus.RESOLVED:
            if self.scope_type is None:
                raise ValueError(
                    f"{self.scope_id!r}: RESOLVED with no scope type. A resolution that "
                    "produced no level did not resolve."
                )
            if self.origin is None:
                raise ValueError(
                    f"{self.scope_id!r}: RESOLVED with no origin. §5 requires a scope to "
                    "say how it was established, because a scope nobody can attribute "
                    "cannot be argued with."
                )
            if not self.basis.strip():
                raise ValueError(
                    f"{self.scope_id!r}: RESOLVED with no basis. The basis is what makes "
                    "the classification re-checkable by somebody who reads the same "
                    "identifier."
                )
        else:
            if self.scope_type is not None:
                raise ValueError(
                    f"{self.scope_id!r}: UNDETERMINED with a scope type. Carrying a level "
                    "beside a status that says nobody established one is how a guess "
                    "becomes a fact one refactor later."
                )
            if self.origin is not None:
                raise ValueError(
                    f"{self.scope_id!r}: UNDETERMINED with an origin. Nothing established "
                    "it, so nothing established it in a particular way."
                )

    @property
    def resolved(self) -> bool:
        return self.status is ScopeStatus.RESOLVED

    def describes_same_scope_as(self, other: ObservationScope) -> bool:
        """Equality of scope IDENTITY, by exact string equality and nothing else.

        Two UNDETERMINED scopes are never the same scope, however identical their
        ids: neither has been established, so there is nothing to compare.
        """
        if not (self.resolved and other.resolved):
            return False
        return self.scope_id == other.scope_id and self.scope_type is other.scope_type


def undetermined(scope_id: str, display_name: str, reason: str) -> ObservationScope:
    """The honest answer where no rule and no registry entry reaches an identifier.

    §12: do not manufacture scopes. A row that cannot be classified says so, and
    §15's gate refuses to attach it as context.
    """
    return ObservationScope(
        scope_type=None,
        scope_id=scope_id,
        display_name=display_name,
        status=ScopeStatus.UNDETERMINED,
        origin=None,
        source_native_identifiers=(scope_id,),
        basis=reason,
    )
