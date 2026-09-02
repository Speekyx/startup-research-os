"""Whether an Evidence row may enter an opportunity packet, and in which role.

Mission 1.28 §5. Deterministic, total, and it returns a REASON in every branch.

Four states, and the important one is the middle pair:

- `ELIGIBLE_SCORING`  -- may contribute to a future score.
- `ELIGIBLE_CONTEXT`  -- may be shown and cited, and may never be scored.
- `REQUIRES_REVIEW`   -- a question nobody has answered.
- `INELIGIBLE`        -- a decision somebody made, or a structural defect.

**`ELIGIBLE_CONTEXT` is not a weaker `ELIGIBLE_SCORING`.** It is the state that
lets non-scorable evidence stay visible without leaking into arithmetic, and the
whole point is that nothing promotes across the line. There is no threshold, no
override and no `force_scoring` parameter; the only route to `ELIGIBLE_SCORING`
is a reliability that a reviewed assessment actually resolved.

**`REQUIRES_REVIEW` is never treated as permission.** It is the source-registry
rule one layer out: *uncertainty is never permission*. An unregistered signal
type, an unknown use profile or a policy question nobody asked all land here, and
a packet builder must exclude them rather than guess.

**Policy is passed in, never looked up.** This package does not import
`sros_acquisition`, because an engine that could read the source registry could
decide its own authorization -- the argument Mission 1.24 made for the classifier,
unchanged. The caller resolves the source's standing and hands over a
`SourcePolicyStanding`; a source with no entry is `REQUIRES_REVIEW`, not allowed.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from .facets import EvidenceFacets
from .mapping import map_signal_type

__all__ = [
    "ELIGIBILITY_PROCEDURE_VERSION",
    "PacketEligibility",
    "SourcePolicyStanding",
    "EligibilityDecision",
    "assess_eligibility",
]

ELIGIBILITY_PROCEDURE_VERSION = "opportunity-input-eligibility@1.0.0"


class PacketEligibility(enum.Enum):
    ELIGIBLE_SCORING = "ELIGIBLE_SCORING"
    ELIGIBLE_CONTEXT = "ELIGIBLE_CONTEXT"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    INELIGIBLE = "INELIGIBLE"


@dataclass(frozen=True)
class SourcePolicyStanding:
    """What the caller established about one source under one use profile.

    A value object, resolved outside this package and handed in. It carries no
    verdict enum from the registry on purpose: importing one would couple the
    opportunity layer to the registry's vocabulary and make this package
    upgrade whenever that one did.
    """

    source_id: str
    use_profile_id: str
    #: Whether the reviewed profile permits the processing an opportunity packet
    #: performs: reading, relating and citing evidence already held locally.
    permits_local_processing: bool
    #: Whether the source's review permits this deployment to transmit its
    #: material to a third-party model. `None` means NOT_ASSESSED -- nobody
    #: looked -- which is a state and never a default that decides.
    permits_external_model_transmission: bool | None
    #: Why, in the caller's own words. Required, so a refusal can be cited.
    basis: str
    #: The registry's OWN value for the transmission activity, quoted rather
    #: than re-encoded (Mission 1.29). The boolean above decides; this says what
    #: the reviewer actually recorded, so the engine can report UNCLEAR as
    #: unresolved instead of flattening it to "refused" -- the same distinction
    #: ADR-033 draws for NOT_ASSESSED, one state further along. Empty means the
    #: caller did not supply it, and the message falls back to the boolean.
    transmission_state: str = ""

    def __post_init__(self) -> None:
        if not self.basis.strip():
            raise ValueError(
                f"{self.source_id}: basis is required. A standing with no stated basis "
                "is a permission nobody can re-check."
            )


@dataclass(frozen=True)
class EligibilityDecision:
    eligibility: PacketEligibility
    reasons: tuple[str, ...]

    @property
    def may_enter_packet(self) -> bool:
        return self.eligibility in (
            PacketEligibility.ELIGIBLE_CONTEXT,
            PacketEligibility.ELIGIBLE_SCORING,
        )


def assess_eligibility(
    facets: EvidenceFacets,
    standing: SourcePolicyStanding | None,
) -> EligibilityDecision:
    """Apply `opportunity-input-eligibility@1.0.0`.

    Every blocking condition is evaluated and every reason is returned, not just
    the first. An operator told only the first failure fixes it and is refused
    again -- the lesson ADR-033's four gates already recorded.
    """
    blocking: list[str] = []
    review: list[str] = []

    # --- the claim must exist and be current ------------------------------
    if facets.claim_lifecycle != "ACTIVE":
        blocking.append(
            f"claim lifecycle is {facets.claim_lifecycle}; a withdrawn claim's "
            "evidence may not enter a packet"
        )
    if facets.claim_type not in ("OBSERVED", "INFERRED", "PREDICTED", "RECOMMENDED", "HYPOTHESIS"):
        blocking.append(f"claim_type {facets.claim_type!r} is not in the closed taxonomy")

    # --- the evidence relation must be valid ------------------------------
    if facets.direction not in ("SUPPORTS", "CONTRADICTS"):
        blocking.append(f"direction {facets.direction!r} is not a valid evidence relation")

    # --- epistemic provenance must be preserved ---------------------------
    if not facets.source_id.strip():
        blocking.append("no source_id; evidence with no origin cannot be cited")
    if facets.extraction_method is None:
        review.append("extraction_method is absent; how this row was produced is unrecorded")

    # --- source and use profile must permit the processing ----------------
    if standing is None:
        review.append(
            f"no policy standing supplied for source {facets.source_id!r}; "
            "uncertainty is never permission"
        )
    else:
        if standing.source_id != facets.source_id:
            blocking.append(
                f"policy standing is for {standing.source_id!r} but the row is from "
                f"{facets.source_id!r}"
            )
        if standing.use_profile_id != facets.use_profile_id:
            blocking.append(
                f"policy standing was assessed under {standing.use_profile_id!r} but the "
                f"row declares {facets.use_profile_id!r}; approval never transfers "
                "between profiles"
            )
        if not standing.permits_local_processing:
            blocking.append(
                f"the reviewed profile does not permit this processing: {standing.basis}"
            )

    # --- the dimension mapping must be a decision somebody made -----------
    mapping = map_signal_type(facets.signal_type_id)
    if mapping is None:
        review.append(
            f"signal type {facets.signal_type_id!r} has no registered dimension "
            "mapping; nobody has decided what it bears on"
        )

    if blocking:
        return EligibilityDecision(PacketEligibility.INELIGIBLE, tuple(blocking))
    if review:
        return EligibilityDecision(PacketEligibility.REQUIRES_REVIEW, tuple(review))

    # --- scoring needs a reviewed reliability, and nothing else grants it --
    if not facets.is_scorable:
        return EligibilityDecision(
            PacketEligibility.ELIGIBLE_CONTEXT,
            (
                "no reviewed reliability resolves for this row's measurement-by-purpose "
                f"scope ({facets.reliability_status.value}), so the row is NON_SCORABLE. "
                "It may be cited as context and may never contribute to a score.",
            ),
        )
    return EligibilityDecision(
        PacketEligibility.ELIGIBLE_SCORING,
        ("claim current, relation valid, profile permits, reliability resolved",),
    )
