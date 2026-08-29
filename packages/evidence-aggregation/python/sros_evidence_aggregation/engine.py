"""`aggregate()` — the whole pipeline, in one readable pass.

Mission 1.1 §4, §26.

    evidence records
      -> per-item contribution q = min(components)          items.py
      -> collapse by provenance, strongest member wins      independence.py
      -> saturate across groups, per direction              saturation.py
      -> decompose into four masses                         masses.py
      -> EvidenceScore, EvidenceLevel                       masses.py / levels.py

Aggregation is **claim-centric**. It answers "how does this evidence bear on
this claim", and nothing else. It does not produce an Opportunity Score, does
not combine claims, and does not rank anything. The chain

    raw -> observation -> signal -> claim -> aggregation -> scored feature

continues past this function, and every later stage is somebody else's mission.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sros_contracts import (
    ClaimTemporality,
    EvidenceAggregationStatus,
    EvidenceDirection,
    EvidenceIndependenceState,
)

from .independence import GroupKind, group_by_independence
from .items import EvidenceItem, ItemContribution, evaluate_item
from .levels import assess_evidence_level
from .masses import decompose
from .profile import EvidenceAggregationProfile
from .result import EvidenceAggregationResult, GroupExplanation, snapshot_digest
from .saturation import saturate

__all__ = ["aggregate"]


def aggregate(
    claim_id: str,
    items: Sequence[EvidenceItem],
    profile: EvidenceAggregationProfile,
    *,
    temporality: ClaimTemporality | None = None,
    claim_feature: str | None = None,
    now: datetime | None = None,
    allow_uncalibrated: bool = False,
) -> EvidenceAggregationResult:
    """Aggregate one claim's evidence under one profile.

    `temporality` and `claim_feature` describe the CLAIM. Recency is a property
    of what is being claimed, not of where the evidence came from (§18), so
    neither is read off an evidence record.

    `allow_uncalibrated` must be passed explicitly to run an UNCALIBRATED
    profile. That is the mechanical form of §41: the equations being defined
    does not make production scoring available, and the caller has to say out
    loud that the numbers are not calibrated.
    """
    profile.require_runnable(allow_uncalibrated=allow_uncalibrated)

    moment = now or datetime.now(UTC)
    claim_temporality = temporality or profile.default_temporality
    half_life = profile.half_life_for(claim_feature)

    # -- per item ------------------------------------------------------------

    contributions: dict[str, ItemContribution] = {}
    for item in items:
        if item.evidence_id in contributions:
            raise ValueError(
                f"duplicate evidence_id {item.evidence_id!r} in the snapshot. Two records "
                "sharing an id cannot be told apart in an explanation, and one would "
                "silently shadow the other"
            )
        contributions[item.evidence_id] = evaluate_item(
            item,
            temporality=claim_temporality,
            now=moment,
            half_life_days=half_life,
            required_components=profile.required_item_fields,
        )

    # NEUTRAL records are separated before scoring. They are evidence -- they
    # bear on the claim, they count towards coverage, they appear in the
    # explanation -- but they move neither strength, by definition (§5).
    neutral = [i for i in items if i.direction is EvidenceDirection.NEUTRAL]
    directional = [i for i in items if i.direction is not EvidenceDirection.NEUTRAL]

    scorable = [i for i in directional if contributions[i.evidence_id].scorable]
    non_scorable = [i for i in directional if not contributions[i.evidence_id].scorable]

    # -- grouping and saturation --------------------------------------------

    support_groups = group_by_independence(items, contributions, EvidenceDirection.SUPPORTS)
    contradiction_groups = group_by_independence(
        items, contributions, EvidenceDirection.CONTRADICTS
    )

    support_strength = saturate(g.strength for g in support_groups)
    contradiction_strength = saturate(g.strength for g in contradiction_groups)
    masses = decompose(support_strength, contradiction_strength)

    # -- level ---------------------------------------------------------------

    thresholds = profile.level_thresholds
    level = assess_evidence_level(
        items,
        contributions,
        support_groups,
        repeated_signal_min_groups=thresholds.repeated_signal_min_groups,
        multi_source_min_groups=thresholds.multi_source_min_groups,
        multi_source_min_families=thresholds.multi_source_min_families,
    )

    # -- status and diagnostics ---------------------------------------------

    if not scorable:
        status = EvidenceAggregationStatus.UNAVAILABLE
    elif non_scorable:
        status = EvidenceAggregationStatus.PARTIAL
    else:
        status = EvidenceAggregationStatus.COMPLETE

    missing: list[str] = []
    for item in non_scorable:
        for reason in contributions[item.evidence_id].non_scorable_reasons:
            entry = f"{item.evidence_id}: {reason}"
            if entry not in missing:
                missing.append(entry)

    warnings: list[str] = []
    if not profile.is_calibrated:
        warnings.append(
            f"profile {profile.profile_id} v{profile.version} is "
            f"{profile.status.value}: its parameters were never fitted to labelled data. "
            "This result is not calibrated and must not be presented as though it were"
        )
    unknown_independence = [
        i for i in scorable if i.independence_state is EvidenceIndependenceState.UNKNOWN
    ]
    if unknown_independence:
        warnings.append(
            f"{len(unknown_independence)} record(s) have unestablished provenance and were "
            "collapsed into one contribution group per direction. They raise observed "
            "volume, not evidence strength"
        )

    return EvidenceAggregationResult(
        claim_id=claim_id,
        aggregation_profile_id=profile.profile_id,
        aggregation_profile_version=profile.version,
        aggregation_profile_status=profile.status.value,
        algorithm_version=profile.algorithm_version,
        masses=masses,
        level=level,
        status=status,
        raw_evidence_count=len(items),
        scorable_evidence_count=len(scorable),
        neutral_evidence_count=len(neutral),
        non_scorable_evidence_count=len(non_scorable),
        independence_group_count=len(support_groups) + len(contradiction_groups),
        support_group_count=len(support_groups),
        contradiction_group_count=len(contradiction_groups),
        unknown_independence_count=len(unknown_independence),
        # Diagnostics only. Neither count is ever multiplied into a score: §24
        # keeps diversity out of the arithmetic and in the explanation, where a
        # reader can weigh it themselves.
        source_count=len({i.source_id for i in scorable if i.source_id}),
        source_family_count=len({i.source_family for i in scorable if i.source_family}),
        missing_requirements=tuple(missing),
        # Sorted, not insertion-ordered. The masses were already independent of
        # input order, but the EXPLANATION was not, so two runs over the same
        # snapshot serialised differently. §30.7 covers the whole result, and a
        # canonical form that depends on argument order is not canonical.
        contributions=tuple(sorted(contributions.values(), key=lambda c: c.evidence_id)),
        groups=GroupExplanation(
            support=tuple(support_groups),
            contradiction=tuple(contradiction_groups),
        ),
        evidence_snapshot_digest=snapshot_digest(list(contributions.values())),
        computed_at=moment,
        calibrated=profile.is_calibrated,
        warnings=tuple(warnings),
    )


# Re-exported for the tests that assert unknown records form ONE group.
UNKNOWN_GROUP_KIND = GroupKind.UNKNOWN
