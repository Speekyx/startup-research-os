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
    "PROJECTS_FROM",
    "PROJECTS_ONTO",
    "CONVERGENT_INTERPRETER_VERSION",
    "convergent_draft",
]

CONVERGENT_INTERPRETER_ID = "observed-convergent-witness"
CONVERGENT_INTERPRETER_VERSION = "1.0.0"

# The detailed proposition kind this projects FROM, and the contract it projects
# ONTO. Stated as a pair so a reader can see that exactly one route exists.
PROJECTS_FROM = "source_reported_procurement_value_contrast"
PROJECTS_ONTO = "source_published_classification_value_contrast_witnessed"

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


def _render(facts: Mapping[str, object]) -> str:
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


def convergent_draft(detailed: ClaimDraft, *, signal_type_id: str) -> ClaimDraft:
    """The broader Claim a detailed cohort draft also witnesses.

    Refuses rather than guesses. A draft whose facts the contract does not
    classify is refused with `PROPOSITION_NOT_IDENTIFIABLE`, because an
    unclassified fact would silently become identity -- the key is built from
    whatever is in the mapping, so a fact nobody placed is a fact that decides.
    """
    facts = dict(detailed.cited_facts)
    if facts.get("proposition") != PROJECTS_FROM:
        raise _refuse(
            ClaimEvidenceRefusalReason.UNSUPPORTED_SIGNAL_TYPE,
            f"this interpreter projects {PROJECTS_FROM!r} and was handed "
            f"{facts.get('proposition')!r}. There is no fallback: a generic projection "
            "over an unknown proposition would emit an assertion nobody specified",
        )

    contract = contract_for(PROJECTS_ONTO)
    if contract is None:
        raise _refuse(
            ClaimEvidenceRefusalReason.PROPOSITION_NOT_IDENTIFIABLE,
            f"no convergence contract is registered for {PROJECTS_ONTO!r}",
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
        statement=_render(projected),
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
