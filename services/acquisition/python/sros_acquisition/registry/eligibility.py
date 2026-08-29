"""The collector eligibility gate.

Mission 1.0 §21. This is the function that decides whether a source may be
collected from, and it is the reason the rest of the registry exists.

    collector_eligible(source) =
        source active
        AND an access method is configured
        AND required authentication metadata is defined
        AND the policy review is in an approving state
        AND policy evidence exists
        AND retention is resolved
        AND the review is not stale
        AND the source is not suspended
        AND every required review condition is satisfied

**It fails closed, and it explains itself.** A refusal returns the reasons
rather than a bare `False`, because a gate that will not say why gets worked
around: someone will read the code, decide the condition does not really apply,
and set the flag by hand. A refusal that names "policy review is
REQUIRES_REVIEW; policy review has no evidence" ends that conversation.

The same rules exist twice on purpose, here and as the SQL view
`registry.source_eligibility` (migration 0004 §9). That is not duplication for
its own sake: the SQL version backs a database trigger so no UPDATE can enable a
collector on an ineligible source whoever issues it, and this version runs in
the CLI and the validator with no database at all. A test asserts the two agree.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sros_contracts import SourceApprovalState, SourceLifecycle

from .models import SourceRecord

__all__ = ["EligibilityResult", "evaluate_eligibility", "is_collector_eligible"]


@dataclass(frozen=True)
class EligibilityResult:
    """Whether a source may be collected from, and why not if it may not."""

    source_id: str
    eligible: bool
    blocking_reasons: tuple[str, ...]
    approval_state: SourceApprovalState | None
    review_stale: bool
    evidence_count: int

    def __bool__(self) -> bool:
        return self.eligible

    def to_json(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "eligible": self.eligible,
            "blocking_reasons": list(self.blocking_reasons),
            "approval_state": self.approval_state.value if self.approval_state else None,
            "review_stale": self.review_stale,
            "evidence_count": self.evidence_count,
        }


def evaluate_eligibility(
    source: SourceRecord,
    now: datetime | None = None,
    satisfied_conditions: frozenset[str] = frozenset(),
) -> EligibilityResult:
    """Evaluate every condition and report all failures, not the first.

    Reporting all of them matters: a reviewer who fixes one blocker and
    rediscovers the next on the following run learns to distrust the tool.

    `satisfied_conditions` is deliberately a caller-supplied argument rather
    than something read off the source. Whether a condition holds depends on
    what is deployed and configured, and a catalog that could assert its own
    conditions satisfied would make APPROVED_WITH_CONDITIONS meaningless
    (Mission 1.3 §24). The default is the empty set: nothing is satisfied until
    something says so.
    """
    moment = now or datetime.now(UTC)
    reasons: list[str] = []
    review = source.review

    if source.lifecycle is not SourceLifecycle.ACTIVE:
        reasons.append(f"source lifecycle is {source.lifecycle.value}")

    if source.suspended:
        reasons.append(f"source is suspended: {source.suspended_reason or 'no reason recorded'}")

    if review is None:
        reasons.append("no policy review exists")
    else:
        if not review.is_approving:
            reasons.append(f"policy review is {review.approval_state.value}")
        if not review.evidence:
            reasons.append("policy review has no evidence")
        elif not any(item.is_authoritative for item in review.evidence):
            reasons.append("policy review has no official or authoritative evidence")
        # Mission 1.3 §24. An approving review whose conditions are not all
        # satisfied still blocks. Satisfaction is ENVIRONMENT state, so the
        # catalog cannot supply it — which is the point: APPROVED_WITH_CONDITIONS
        # says a collector MAY be designed, not that one may run.
        unsatisfied = tuple(
            condition.key
            for condition in review.required_conditions
            if condition.key not in satisfied_conditions
        )
        if review.is_approving and unsatisfied:
            reasons.append("review conditions not satisfied: " + ", ".join(sorted(unsatisfied)))
        if review.is_stale(moment):
            # §14: an approval that has gone stale fails closed. Platform terms
            # change, and an approval nobody has re-checked is a statement about
            # the past presented as a statement about now.
            reasons.append(
                f"policy review is stale, due {review.next_review_at.date().isoformat()}"
            )

    if not source.access_profiles:
        reasons.append("no access profile configured")

    if source.has_credentialed_profile_without_reference:
        reasons.append("an access profile requires a credential with no configuration reference")

    # Retention is "resolved" when either an override with a recorded basis
    # exists or the project baseline applies. Absence is resolution, not a gap:
    # `data-retention-policy-v1.md` §2 supplies defaults, and only a *present*
    # override with no basis is a problem -- which the model refuses outright.
    if source.retention_override is not None and not source.retention_override.basis.strip():
        reasons.append("retention override has no recorded basis")

    return EligibilityResult(
        source_id=source.source_id,
        eligible=not reasons,
        blocking_reasons=tuple(reasons),
        approval_state=review.approval_state if review else None,
        review_stale=bool(review and review.is_stale(moment)),
        evidence_count=len(review.evidence) if review else 0,
    )


def is_collector_eligible(
    source: SourceRecord,
    now: datetime | None = None,
    satisfied_conditions: frozenset[str] = frozenset(),
) -> bool:
    return evaluate_eligibility(source, now, satisfied_conditions).eligible
