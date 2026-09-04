"""`observed-convergent-witness@1.0.0` -- the broader proposition a cohort witnesses.

Mission 1.39. **A projection, never a second reading.** It takes a draft the
detailed interpreter already produced and projects its facts onto a
convergence contract, so the two propositions are derived from one reading of
one Signal. A second extraction path would be a second place for the same fact
to live, and the two would eventually disagree about what a cohort said.

**What it produces.** A DIFFERENT proposition from the detailed one, not a
weakened version of it:

    detailed   "within a bounded set of 3 notices {N1,N2,N3} ... the largest
                exceeded the smallest by 686545.02"      -> about THOSE notices
    convergent "published at least one bounded set of notices ... whose stated
                amounts differ"                          -> about the DIVISION

The second is entailed by the first and asserts less. That is why it is a new
proposition kind rather than an edit: Mission 1.39 §2 forbids removing
`notice_ids` from the existing kind, and this does not touch it.

**Why OBSERVED.** `claim-epistemic-semantics-v1.md` §2 asks: *does a source
report this, such that a person could go and read it there?* Yes -- a reader
opens the notices and sees the differing totals. §3 asks whether the truth
condition is about the publication: it is, and the claim stays true if TED's
figures were wrong, because it asserts what TED STATED. No sample is
generalised, no prevalence is estimated, no latent phenomenon is inferred.

**The objection this template must answer.** The detailed template's own
docstring says *"a proposition that cannot say WHICH notices is not checkable"*.
It is right, and the answer is that checkability MOVES rather than disappearing:
the notice ids are witness facts, carried on the Evidence and reachable through
Evidence -> Signal -> signal_inputs -> normalized_records. A reader can still go
and read exactly which notices. What they cannot do is read the cohort off the
Claim's identity, which is the point -- a second cohort must be able to witness
the same assertion.

**NOT WIRED INTO THE PRODUCTION JOB.** `INTERPRETERS` does not include it and
`run_claim_interpretation_job` never calls it. Mission 1.39 settles the contract;
running it against live records is a later mission's decision, and until then no
Signal can witness two Claims in this deployment. That is §19's double-counting
boundary, enforced by absence rather than by a rule.
"""

from __future__ import annotations

from collections.abc import Mapping

from sros_claim_model import (
    ClaimDraft,
    ClaimInterpretation,
    ClaimRefusal,
    ClaimRefusedError,
    PropositionConvergenceContract,
    QualificationOutcome,
    build_claim,
    contract_for,
    qualify,
    witness_facts,
    witness_key,
)
from sros_contracts import (
    ClaimEvidenceRefusalReason,
    ClaimInterpretationKind,
    ClaimOrigin,
    ClaimType,
)

__all__ = [
    "CONVERGENT_INTERPRETER_ID",
    "PROJECTION_ROUTES",
    "PROJECTS_FROM",
    "PROJECTS_ONTO",
    "CONVERGENT_INTERPRETER_VERSION",
    "convergent_draft",
]

CONVERGENT_INTERPRETER_ID = "observed-convergent-witness"
CONVERGENT_INTERPRETER_VERSION = "1.0.0"

# The detailed proposition kinds this projects FROM, each with the contract it
# projects ONTO. Mission 1.39 wrote this as a single pair so a reader could see
# that exactly one route existed; Mission 1.43 added a second, so it is a TABLE
# and a reader can still see every route at once.
#
# **There is still no fallback.** A detailed kind absent from this table has no
# broader claim to make, which is the state five of the seven historical kinds
# remain in. A generic projection over an unregistered proposition would emit an
# assertion nobody specified.
PROJECTION_ROUTES: dict[str, str] = {
    "source_reported_procurement_value_contrast": (
        "source_published_classification_value_contrast_witnessed"
    ),
    "platform_counted_content_request_change": (
        "platform_counted_content_request_change_witnessed"
    ),
}

# Kept as names because Mission 1.39's tests and Mission 1.40's wiring read them,
# and because the procurement route is still the one the production job was first
# built around. They name ONE route, never the whole table.
PROJECTS_FROM = "source_reported_procurement_value_contrast"
PROJECTS_ONTO = PROJECTION_ROUTES[PROJECTS_FROM]

_CLAIM_TYPE = ClaimType.OBSERVED
_ORIGIN = ClaimOrigin.DETERMINISTIC_EXTRACTION

# 1.0 for the same reason the detailed interpreter's is: a projection either read
# the facts or raised. It is confidence in the READING and says nothing about
# whether the proposition is worth much.
_INTERPRETATION_CONFIDENCE = 1.0

_DETERMINISTIC = ClaimInterpretation(
    interpreter_id=CONVERGENT_INTERPRETER_ID,
    interpreter_version=CONVERGENT_INTERPRETER_VERSION,
    kind=ClaimInterpretationKind.DETERMINISTIC,
)


def _refuse(reason: ClaimEvidenceRefusalReason, detail: str) -> ClaimRefusedError:
    return ClaimRefusedError(ClaimRefusal(reason=reason, detail=detail))


def _project(
    contract: PropositionConvergenceContract, facts: Mapping[str, object]
) -> dict[str, object]:
    """The detailed fact set, renamed onto the contract's proposition kind.

    Every other value is carried across unchanged. A projection that recomputed
    anything would be a second reading wearing a projection's name.
    """
    projected = dict(facts)
    projected["proposition"] = contract.proposition_kind
    return projected


def _render_procurement(facts: Mapping[str, object]) -> str:
    """The sentence, bounded in its own wording.

    *"at least one bounded set"* is the whole of §6 in four words. Without it the
    sentence reads as a statement about the division, which is a population
    nobody sampled -- the exact failure the detailed template's docstring names.
    """
    relation = facts["relation"]
    verb = "differ from one another" if relation == "DIFFERS" else "are all equal"
    return (
        f'The source "{facts["source_id"]}" published, in its "{facts["resource_id"]}" '
        f'resource, at least one bounded set of "{facts["notice_class"]}" notices '
        f'classified under "{facts["classification_scheme"]}" division '
        f'"{facts["classification_division"]}" whose stated "{facts["amount_type"]}" '
        f'amounts at "{facts["amount_scope"]}" scope in "{facts["currency"]}" {verb}.'
    )


_REQUEST_DIRECTION_VERB = {
    "INCREASING": "were higher in the later bucket than in the earlier one",
    "DECREASING": "were lower in the later bucket than in the earlier one",
    "UNCHANGED": "were the same in both buckets",
}


def _render_content_request(facts: Mapping[str, object]) -> str:
    """The sentence, carrying every bound the detailed template earned.

    *"at least one pair"* does the same work *"at least one bounded set"* does
    for procurement: without it the sentence reads as a claim about the item's
    history, which is a population nobody sampled.

    Three bounds are carried across verbatim rather than summarised away, because
    the detailed template established each of them and a broader claim inherits
    every one. **COUNTED, not viewed** -- the platform's own definition is a
    request receiving a 200 or 304, and every other verb would suggest it saw a
    person. **The requester class is IN THE SENTENCE**, because a reader who
    meets this claim without it cannot know whether bots are included, and the
    platform refuses to call its own heuristic "human". And **adjacent published
    day buckets**, which ADR-023 guarantees: a pair derives only when the labels
    are exactly one published bucket apart, so nothing here spans a gap nobody
    read.
    """
    direction = str(facts["direction"])
    verb = _REQUEST_DIRECTION_VERB.get(direction)
    if verb is None:
        raise _refuse(
            ClaimEvidenceRefusalReason.PROPOSITION_NOT_IDENTIFIABLE,
            f"no wording is registered for direction {direction!r}. A projection that "
            "invented one would assert a relation nobody specified",
        )
    return (
        f'The source "{facts["source_id"]}" counted, on "{facts["content_platform"]}", '
        f"at least one pair of adjacent published day buckets in which requests for "
        f'"{facts["content_id"]}" under its own requester class '
        f'"{facts["audience_class"]}" {verb}.'
    )


# One renderer per route. A route with no renderer cannot be projected: the
# sentence is where every bound the detailed template earned is carried, so a
# generic sentence would be a proposition nobody wrote.
_RENDERERS = {
    "source_published_classification_value_contrast_witnessed": _render_procurement,
    "platform_counted_content_request_change_witnessed": _render_content_request,
}


def convergent_draft(detailed: ClaimDraft, *, signal_type_id: str) -> ClaimDraft:
    """The broader Claim a detailed cohort draft also witnesses.

    Refuses rather than guesses. A draft whose facts the contract does not
    classify is refused with `PROPOSITION_NOT_IDENTIFIABLE`, because an
    unclassified fact would silently become identity -- the key is built from
    whatever is in the mapping, so a fact nobody placed is a fact that decides.
    """
    facts = dict(detailed.cited_facts)
    detailed_kind = facts.get("proposition")
    onto = PROJECTION_ROUTES.get(str(detailed_kind))
    if onto is None:
        raise _refuse(
            ClaimEvidenceRefusalReason.UNSUPPORTED_SIGNAL_TYPE,
            f"this interpreter projects {sorted(PROJECTION_ROUTES)} and was handed "
            f"{detailed_kind!r}. There is no fallback: a generic projection "
            "over an unknown proposition would emit an assertion nobody specified",
        )

    contract = contract_for(onto)
    if contract is None:
        raise _refuse(
            ClaimEvidenceRefusalReason.PROPOSITION_NOT_IDENTIFIABLE,
            f"no convergence contract is registered for {onto!r}",
        )

    render = _RENDERERS.get(onto)
    if render is None:
        raise _refuse(
            ClaimEvidenceRefusalReason.PROPOSITION_NOT_IDENTIFIABLE,
            f"no wording is registered for {onto!r}. The sentence carries the bounds "
            "the detailed template earned, so a generic one would drop them silently",
        )

    projected = _project(contract, facts)
    outcome, detail = qualify(contract, projected, signal_type_id=signal_type_id)
    if outcome is not QualificationOutcome.QUALIFIES:
        raise _refuse(
            ClaimEvidenceRefusalReason.PROPOSITION_NOT_IDENTIFIABLE, f"{outcome}: {detail}"
        )

    if not detailed.evidence:
        raise _refuse(
            ClaimEvidenceRefusalReason.NO_SUPPORTING_SIGNAL,
            "a convergent claim cites the same Signal the detailed one did, and there "
            "is none to cite",
        )

    # The facts handed to `build_claim` are the IDENTITY facts alone, so the key
    # is the convergent one. The witness facts are not discarded: they go into
    # the rationale, and they remain on the Signal and reachable through the
    # Evidence, which is where §3 says a witness fact belongs.
    identity = {name: projected[name] for name in contract.identity_fields}
    witness = witness_facts(contract, projected)

    return build_claim(
        workspace_id=detailed.workspace_id,
        claim_type=_CLAIM_TYPE,
        temporality=contract.temporality,
        origin=_ORIGIN,
        statement=render(projected),
        facts=identity,
        evidence=list(detailed.evidence),
        interpretation=_DETERMINISTIC,
        interpretation_confidence=_INTERPRETATION_CONFIDENCE,
        research_session_id=detailed.research_session_id,
        rationale=(
            f"Witnessed by observation {witness_key(contract, projected)} "
            f"under contract {contract.contract_id}@{contract.version}; "
            f"witness facts {sorted(witness)}."
        ),
    )
