"""Proposition convergence: when two distinct observations witness one Claim.

Mission 1.39. **The rule exists before any observation is processed**, which is
the whole of §4: convergence defined as *drop some fields until the hashes match*
is not a contract, it is a coincidence with a procedure.

**The distinction this module introduces.**

    PROPOSITION IDENTITY FACTS   what exact assertion is this Claim?
    WITNESS OBSERVATION FACTS    which observation demonstrates that assertion?

A witness fact is **not discarded**. It stays on the Signal, on the Evidence and
in provenance; it simply does not decide which Claim the observation lands on.
The test is stated once and applied field by field:

> If changing field F changes WHAT the Claim asserts, F is proposition identity.
> If changing F only changes WHICH observation witnesses the same assertion, F
> may be witness identity.

**What this module does not do.** It cannot decide that two observations are
*about the same thing* by resemblance. Qualification is a deterministic predicate
over persisted bounded facts -- no embedding, no cosine, no fuzzy match, no
model, and no `SAME_PROBLEM_FAMILY`, which asks a different question entirely
(§13, §14).

**Convergence is not independence** (§11). Two disjoint cohorts are two
observations; they may still share a collection mechanism, a methodology, a
publisher and an underlying population. Observation overlap and epistemic
independence are different axes, and this module models only the first.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from sros_contracts import ClaimTemporality, ClaimType

from .model import canonical_json, proposition_key

__all__ = [
    "CONVERGENCE_CONTRACTS",
    "ObservationOverlap",
    "PropositionConvergenceContract",
    "QualificationOutcome",
    "SourceBoundary",
    "contract_for",
    "identity_facts",
    "qualify",
    "witness_facts",
    "witness_key",
]


class SourceBoundary(StrEnum):
    """How far a single convergent proposition may reach across sources.

    `SAME_SOURCE_AND_RESOURCE` is the only V1 value, and the narrowness is the
    point (§7). Two observations converge only when they come from one source
    AND one measurement contract, because an `OBSERVED` claim asserts what a
    named source reported: *"Wikimedia counted X"* and *"TED reported Z"* are
    different propositions with different falsifiers, and rendering them into
    similar English does not make them one.

    A cross-source value is deliberately absent rather than present-and-unused.
    An enum member nobody may pass is an invitation.
    """

    SAME_SOURCE_AND_RESOURCE = "SAME_SOURCE_AND_RESOURCE"


class ObservationOverlap(StrEnum):
    """Whether two witness sets share underlying source records.

    **This is not `EvidenceIndependenceState` and must never be mapped onto it.**
    `DISJOINT` says the two witnesses read different records. It does not say the
    two Evidence rows are independent corroboration: they can still share the
    publisher, the collection mechanism, the methodology and the population the
    records were drawn from. §11 keeps the two axes apart, and §12 requires
    independence to stay `UNKNOWN` until provenance establishes otherwise.
    """

    DISJOINT = "DISJOINT"
    OVERLAPPING = "OVERLAPPING"
    # NOT `UNKNOWN`. `EvidenceIndependenceState` already has a member by that
    # name, and two vocabularies sharing a member name is how a mapping between
    # them gets written by accident -- which is the one thing §11 forbids. The
    # collision was found by the test that asserts the two share no member.
    UNESTABLISHED = "UNESTABLISHED"


class QualificationOutcome(StrEnum):
    """Whether a fact set may witness a contract's proposition."""

    QUALIFIES = "QUALIFIES"
    DOES_NOT_QUALIFY = "DOES_NOT_QUALIFY"
    MISSING_REQUIRED_FACT = "MISSING_REQUIRED_FACT"


@dataclass(frozen=True)
class PropositionConvergenceContract:
    """One convergence-enabled proposition kind, declared in full.

    Every field is required to be stated rather than defaulted. A contract that
    could be written without saying which facts are identity would let the
    question go unanswered, and the question is the mission.
    """

    contract_id: str
    version: str
    proposition_kind: str
    claim_type: ClaimType
    temporality: ClaimTemporality
    source_boundary: SourceBoundary

    # Ordered so the documentation and the key preimage read the same way twice.
    identity_fields: tuple[str, ...]
    witness_fields: tuple[str, ...]
    qualifying_signal_types: tuple[str, ...]

    establishes: str
    does_not_establish: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.claim_type is not ClaimType.OBSERVED:
            raise ValueError(
                f"{self.contract_id}: V1 authorises convergence for OBSERVED claims only. "
                "An INFERRED convergence needs the interpretation layer that does not "
                "exist, and adding one here would build it by accident"
            )
        if "proposition" not in self.identity_fields:
            raise ValueError(
                f"{self.contract_id}: `proposition` is always identity. Two different "
                "propositions sharing every other fact are still two propositions"
            )
        if "source_id" not in self.identity_fields:
            raise ValueError(
                f"{self.contract_id}: `source_id` is always identity for an OBSERVED "
                "claim. Attribution is part of the proposition, and a claim that drops "
                "it asserts something about the world rather than about a publication"
            )
        overlap = set(self.identity_fields) & set(self.witness_fields)
        if overlap:
            raise ValueError(
                f"{self.contract_id}: {sorted(overlap)} are declared both identity and "
                "witness. A fact decides which Claim this is, or which observation "
                "witnesses it, and never both"
            )
        if not self.witness_fields:
            raise ValueError(
                f"{self.contract_id}: a contract with no witness fields cannot converge. "
                "Two observations agreeing on every fact are the same observation"
            )
        if not self.qualifying_signal_types:
            raise ValueError(f"{self.contract_id}: no Signal type may witness this proposition")
        if not self.establishes.strip() or not self.does_not_establish:
            raise ValueError(
                f"{self.contract_id}: an existential proposition must say what it does "
                "NOT establish. Prevalence is what a reader supplies when nobody said "
                "otherwise"
            )

    @property
    def declared_fields(self) -> tuple[str, ...]:
        return tuple(self.identity_fields) + tuple(self.witness_fields)

    def to_json(self) -> dict[str, object]:
        return {
            "contract_id": self.contract_id,
            "version": self.version,
            "proposition_kind": self.proposition_kind,
            "claim_type": self.claim_type.value,
            "temporality": self.temporality.value,
            "source_boundary": self.source_boundary.value,
            "identity_fields": list(self.identity_fields),
            "witness_fields": list(self.witness_fields),
            "qualifying_signal_types": list(self.qualifying_signal_types),
            "establishes": self.establishes,
            "does_not_establish": list(self.does_not_establish),
        }


def qualify(
    contract: PropositionConvergenceContract,
    facts: Mapping[str, object],
    *,
    signal_type_id: str,
) -> tuple[QualificationOutcome, str]:
    """`(outcome, detail)`. Deterministic, over persisted bounded facts only.

    Three answers rather than a boolean, because *this observation is not about
    that proposition* and *this observation did not carry the facts to tell* are
    different situations and only the second is fixable upstream.
    """
    if signal_type_id not in contract.qualifying_signal_types:
        return (
            QualificationOutcome.DOES_NOT_QUALIFY,
            f"signal type {signal_type_id!r} is not a declared witness of "
            f"{contract.proposition_kind!r}",
        )
    if facts.get("proposition") != contract.proposition_kind:
        return (
            QualificationOutcome.DOES_NOT_QUALIFY,
            f"these facts state proposition {facts.get('proposition')!r}, not "
            f"{contract.proposition_kind!r}",
        )
    missing = [name for name in contract.declared_fields if name not in facts]
    if missing:
        return (
            QualificationOutcome.MISSING_REQUIRED_FACT,
            f"the contract declares {missing} and this observation does not carry them. "
            "An absent fact is not a wildcard: it would let this observation witness "
            "every proposition that differs only in what it failed to state",
        )
    undeclared = [name for name in facts if name not in set(contract.declared_fields)]
    if undeclared:
        return (
            QualificationOutcome.DOES_NOT_QUALIFY,
            f"these facts carry {undeclared}, which the contract does not classify as "
            "identity or witness. An unclassified fact would silently become identity, "
            "because the key is built from whatever is in the mapping",
        )
    return QualificationOutcome.QUALIFIES, "every declared fact is present and classified"


def identity_facts(
    contract: PropositionConvergenceContract, facts: Mapping[str, object]
) -> dict[str, object]:
    """The sub-mapping that decides WHICH Claim this is."""
    return {name: facts[name] for name in contract.identity_fields if name in facts}


def witness_facts(
    contract: PropositionConvergenceContract, facts: Mapping[str, object]
) -> dict[str, object]:
    """The sub-mapping that decides WHICH observation witnesses it.

    Returned so a caller can persist it. §3: information does not stop being
    worth keeping because it stopped being part of an identity.
    """
    return {name: facts[name] for name in contract.witness_fields if name in facts}


def convergent_proposition_key(
    contract: PropositionConvergenceContract, facts: Mapping[str, object]
) -> str:
    """The Claim key: `proposition_key` over the identity facts alone.

    The same hash function the seven existing propositions use, applied to a
    smaller mapping. Nothing about the historical procedure changes -- a
    different set of facts in, a different key out, which is what it has always
    done.
    """
    return proposition_key(identity_facts(contract, facts))


def witness_key(contract: PropositionConvergenceContract, facts: Mapping[str, object]) -> str:
    """A stable identifier for the OBSERVATION, from its witness facts.

    §19's duplicate-witness guard rests on this. Two Evidence rows supporting one
    Claim must differ in what they observed, not merely in a generated id, and a
    guard that compared uuids would agree that the same cohort inserted twice is
    two witnesses.
    """
    return proposition_key(
        {"witness_of": contract.proposition_kind, **witness_facts(contract, facts)}
    )


def distinct_witnesses(
    contract: PropositionConvergenceContract, fact_sets: Sequence[Mapping[str, object]]
) -> bool:
    """Whether every fact set names a different observation."""
    keys = [witness_key(contract, facts) for facts in fact_sets]
    return len(set(keys)) == len(keys)


def overlap_between(
    contract: PropositionConvergenceContract,
    left: Mapping[str, object],
    right: Mapping[str, object],
    *,
    membership_field: str,
) -> ObservationOverlap:
    """`DISJOINT`, `OVERLAPPING`, or `UNESTABLISHED` from declared cohort membership.

    `UNESTABLISHED` whenever either side does not state its membership. That is the
    conservative answer and the honest one: a cohort that did not say which
    records it read has not established that it read different ones.

    **The result says nothing about independence.** It is recorded beside the
    Evidence, and `independence_state` stays `UNKNOWN` until provenance is
    actually traced (§12).
    """
    if membership_field not in contract.witness_fields:
        raise ValueError(
            f"{membership_field!r} is not a witness field of {contract.contract_id}; "
            "overlap is a property of what an observation read"
        )
    left_members = left.get(membership_field)
    right_members = right.get(membership_field)
    if not isinstance(left_members, (list, tuple)) or not isinstance(right_members, (list, tuple)):
        return ObservationOverlap.UNESTABLISHED
    if not left_members or not right_members:
        return ObservationOverlap.UNESTABLISHED
    shared = set(map(canonical_json, left_members)) & set(map(canonical_json, right_members))
    return ObservationOverlap.OVERLAPPING if shared else ObservationOverlap.DISJOINT


# --------------------------------------------------------------------- registry

# One contract. §15: generic machinery with a single narrow proposition to prove
# it, rather than a TED-shaped branch or a universal ontology of convergence.
_PROCUREMENT_VALUE_CONTRAST_WITNESSED = PropositionConvergenceContract(
    contract_id="source-published-value-contrast-witnessed",
    version="1.0.0",
    proposition_kind="source_published_classification_value_contrast_witnessed",
    claim_type=ClaimType.OBSERVED,
    # EVERGREEN because the proposition carries no period. H-37 is open: a TED
    # notice publishes an offset without a time, so the source establishes no
    # instant this claim could be bounded by. An existential over a publication
    # does not need one -- once witnessed, it stays witnessed.
    temporality=ClaimTemporality.EVERGREEN,
    source_boundary=SourceBoundary.SAME_SOURCE_AND_RESOURCE,
    identity_fields=(
        "proposition",
        # Attribution. The claim is about what THIS source published.
        "source_id",
        # The measurement contract: a different resource is a different
        # publication with different semantics.
        "resource_id",
        # What kind of thing was published, and what was measured on it. Change
        # any of these and the assertion changes.
        "notice_class",
        "amount_type",
        "amount_scope",
        "currency",
        "classification_scheme",
        "classification_division",
        # The property asserted: that some published amounts differ, or that
        # they were equal. Two different assertions.
        "relation",
    ),
    witness_fields=(
        # WHICH notices were read. Changing this changes which observation
        # demonstrates the assertion, never the assertion. This is the field the
        # detailed proposition keeps as identity and this one does not, which is
        # exactly why they are two propositions rather than one weakened.
        "notice_ids",
        # The cohort members' own codes beneath the division. Two cohorts in one
        # division legitimately carry different codes.
        "classification_codes",
    ),
    qualifying_signal_types=("procurement_value_contrast",),
    establishes=(
        "that the named source published, in the named resource, at least one bounded "
        "set of notices of the named class under the named classification division "
        "whose stated amounts of the named type, scope and currency stand in the named "
        "relation"
    ),
    does_not_establish=(
        "how many such sets exist",
        "what proportion of the division's notices they are",
        "that the relation is typical, representative or usual for the division",
        "any trend, growth or change over time",
        "demand, market size, buyer preference or willingness to pay",
        "that the amounts are prices, or that anybody paid them",
        "that the witnesses are independent of one another",
    ),
)


_CONTENT_REQUEST_CHANGE_WITNESSED = PropositionConvergenceContract(
    contract_id="platform-counted-content-request-change-witnessed",
    version="1.0.0",
    proposition_kind="platform_counted_content_request_change_witnessed",
    claim_type=ClaimType.OBSERVED,
    # EVERGREEN for the same reason the procurement one is, reached from the
    # opposite direction. Wikimedia's day bucket IS documented -- the Analytics
    # API states UTC partitioning, which is why the detailed claim may name its
    # days at all. The existential still carries no period: once the platform has
    # published a qualifying pair of buckets, it has published one, and that does
    # not stop being true. **A source with established timestamps does not make a
    # claim temporal**; what would is a proposition whose truth decays, and a
    # statement about what a platform once counted is not one.
    temporality=ClaimTemporality.EVERGREEN,
    source_boundary=SourceBoundary.SAME_SOURCE_AND_RESOURCE,
    identity_fields=(
        "proposition",
        # Attribution. The claim is about what THIS platform counted.
        "source_id",
        # Which platform's counts. A different wiki is a different population.
        "content_platform",
        # Which item was counted. Docker, Podman and Kubernetes are three
        # subjects and merging them is the Mission 1.38 failure by another route.
        "content_id",
        # WHOSE requests were counted. Mission 1.19 made this REQUIRED on the
        # record kind precisely because the same item over the same period
        # carries a different number per requester class -- two measurements
        # wearing one name is what that decision refused, and dropping it here
        # would undo it.
        "audience_class",
        # The property asserted: that requests rose, fell, or held. Three
        # different assertions, exactly as the procurement contract's `relation`.
        "direction",
    ),
    witness_fields=(
        # WHICH pair of buckets was read. Changing these changes which
        # observation demonstrates the assertion, never the assertion -- the
        # ADR-035 test, and the same role `notice_ids` plays for procurement.
        # They stay on the Signal and in provenance, so the witness remains
        # recoverable; they stop being identity.
        "period_label_from",
        "period_label_to",
    ),
    qualifying_signal_types=("content_request_change",),
    establishes=(
        "that the named platform counted, for the named item under the named requester "
        "class, at least one pair of adjacent published day buckets whose request counts "
        "stand in the named direction"
    ),
    does_not_establish=(
        "how many such pairs exist",
        "what proportion of the item's history they are",
        "that the direction is typical, usual or continuing",
        "any trend, growth, decline or momentum",
        "that a person read anything, since a request is what a reader makes of a server",
        "audience size, interest, demand or adoption",
        "that the witnesses are independent of one another",
        "that the calendar is controlled for, since a weekday and a weekend are "
        "different days and the pairs are not matched on that",
    ),
)

CONVERGENCE_CONTRACTS: Mapping[str, PropositionConvergenceContract] = MappingProxyType(
    {
        contract.proposition_kind: contract
        for contract in (
            _PROCUREMENT_VALUE_CONTRAST_WITNESSED,
            _CONTENT_REQUEST_CHANGE_WITNESSED,
        )
    }
)


def contract_for(proposition_kind: str) -> PropositionConvergenceContract | None:
    """The contract, or `None`. Never a default, and never a fallback contract.

    A proposition kind with no contract does not converge, which is the state
    every one of the seven historical kinds is in and stays in.
    """
    return CONVERGENCE_CONTRACTS.get(proposition_kind)
