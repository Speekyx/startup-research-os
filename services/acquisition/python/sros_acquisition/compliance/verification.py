"""Running a verifier against a review condition, and recording what it found.

Mission 1.4 §18, §19, §20, §21. Mission 1.3 defined the condition; this defines
the act of checking one.

Four rules shape every function here.

**Use the existing model.** Verification dispatches on the
`ConditionVerification` value Mission 1.3 recorded. There is no second
vocabulary and no parallel boolean: a condition says how it can be checked, and
that is what decides which verifier runs.

**Four results, never a boolean.** `UNKNOWN` is not `UNSATISFIED` -- one means
the check ran and failed, the other means it could not run -- and neither clears
the gate. Only `SATISFIED` does. A verifier that cannot reach what it needs
returns `UNKNOWN` and says so.

**No verifier can satisfy a human condition.** `HUMAN_CONFIRMATION` exists
precisely for what a program cannot establish, so the branch for it returns
`UNKNOWN` unconditionally and names what a person would have to record. There is
no code path in this repository that writes a human confirmation.

**A verification carries its provenance.** Which condition, which verifier, at
which version, when, what result, why, and what it looked at. A satisfaction
with none of that is a boolean with extra steps, and the reason migration 0007
exists is that the boolean could not carry any of it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from sros_contracts import ConditionVerification, ConditionVerificationResult

from ..registry.models import ReviewCondition, SourceRecord
from .capabilities import capability_failures
from .config import ComplianceConfig, SourceCompliance
from .credentials import credential_status

__all__ = [
    "RUNTIME_VERIFICATIONS",
    "VERIFIER_VERSION",
    "ConditionVerificationRecord",
    "design_eligible",
    "satisfied_condition_keys",
    "verify_condition",
    "verify_source",
]

# Bumped when a verifier's meaning changes, not when a message is reworded. A
# satisfaction recorded by an older version stays readable as a fact about that
# older version.
VERIFIER_VERSION = "1.0.0"

# The verification kinds whose answer depends on the deployment rather than on
# the code. §24: a source may have every policy capability in place and still
# not be runnable, and the two must stay tellable apart.
RUNTIME_VERIFICATIONS = frozenset({ConditionVerification.CONFIG_REFERENCE})


@dataclass(frozen=True)
class ConditionVerificationRecord:
    """One attempt to establish that one condition holds."""

    source_id: str
    review_version: int
    condition_key: str
    verification: ConditionVerification
    verifier: str
    verifier_version: str
    result: ConditionVerificationResult
    reason: str
    verified_at: datetime
    reference: str | None = None

    @property
    def satisfied(self) -> bool:
        return self.result is ConditionVerificationResult.SATISFIED

    @property
    def runtime_dependent(self) -> bool:
        return self.verification in RUNTIME_VERIFICATIONS

    def to_json(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "review_version": self.review_version,
            "condition_key": self.condition_key,
            "verification": self.verification.value,
            "verifier": self.verifier,
            "verifier_version": self.verifier_version,
            "result": self.result.value,
            "reason": self.reason,
            "reference": self.reference,
            "verified_at": self.verified_at.isoformat(),
        }


@dataclass(frozen=True)
class _Finding:
    """What a verifier concluded, before it is stamped with a time and a subject."""

    verifier: str
    result: ConditionVerificationResult
    reason: str
    reference: str | None = None


def verify_source(
    source: SourceRecord,
    config: ComplianceConfig,
    environ: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> tuple[ConditionVerificationRecord, ...]:
    """Verify every condition on a source's current review.

    A source with no review, or one whose review declares no condition, produces
    no records. That is not a pass: the eligibility gate blocks such a source
    for its own reasons, and an empty result must never be read as "nothing
    objected, therefore authorised".
    """
    review = source.review
    if review is None:
        return ()
    moment = now or datetime.now(UTC)
    compliance = config.get(source.source_id)
    return tuple(
        verify_condition(source, condition, compliance, environ, moment)
        for condition in review.required_conditions
    )


def verify_condition(
    source: SourceRecord,
    condition: ReviewCondition,
    compliance: SourceCompliance | None,
    environ: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> ConditionVerificationRecord:
    """Run the verifier the condition names, and stamp the result."""
    finding = _find(source, condition, compliance, environ)
    return ConditionVerificationRecord(
        source_id=source.source_id,
        review_version=source.review.review_version if source.review else 0,
        condition_key=condition.key,
        verification=condition.verification,
        verifier=finding.verifier,
        verifier_version=VERIFIER_VERSION,
        result=finding.result,
        reason=finding.reason,
        reference=finding.reference,
        verified_at=now or datetime.now(UTC),
    )


def _find(
    source: SourceRecord,
    condition: ReviewCondition,
    compliance: SourceCompliance | None,
    environ: Mapping[str, str] | None,
) -> _Finding:
    """Dispatch on how the condition itself says it can be checked."""
    if condition.verification is ConditionVerification.HUMAN_CONFIRMATION:
        # §21. Deliberately unconditional, and deliberately not reachable from
        # any argument: a program that could decide this would be the system
        # granting itself permission.
        return _Finding(
            "human-confirmation",
            ConditionVerificationResult.UNKNOWN,
            "this condition requires a person to record a decision and a reference to it. "
            "No verifier can establish it, and none in this repository writes one",
        )

    if condition.verification is ConditionVerification.CONFIG_REFERENCE:
        reference = (condition.verification_detail or "").strip()
        status = credential_status(reference, environ)
        return _Finding(
            "credential-availability",
            (
                ConditionVerificationResult.SATISFIED
                if status.configured
                else ConditionVerificationResult.UNSATISFIED
            ),
            f"configuration key {reference} is {status.status}. Its value was not read, "
            "logged or returned",
            reference,
        )

    # Everything below inspects the compliance configuration, so its absence or
    # staleness is UNKNOWN rather than a failure: nothing was checked.
    review_version = source.review.review_version if source.review else 0
    if compliance is None:
        return _Finding(
            "compliance-config",
            ConditionVerificationResult.UNKNOWN,
            f"no compliance configuration exists for {source.source_id}. The condition was "
            "not checked, and an unchecked condition is not a satisfied one",
            condition.verification_detail,
        )
    if compliance.review_version != review_version:
        return _Finding(
            "compliance-config",
            ConditionVerificationResult.UNKNOWN,
            f"the compliance configuration was written for review version "
            f"{compliance.review_version} and the current review is version "
            f"{review_version}. A re-review can change what a condition means, so the "
            "configuration has to be re-checked against it before this can be verified",
            condition.verification_detail,
        )

    if condition.verification is ConditionVerification.CAPABILITY:
        return _verify_capability(condition, compliance)

    if condition.verification is ConditionVerification.ACCESS_METHOD:
        return _verify_access_method(source, condition, compliance)

    # RETENTION_LIMIT. The value exists in the contract; none of the nine
    # conditions uses it, so no verifier was built for it (§5: no unused
    # abstractions). UNKNOWN is the honest answer, and it blocks.
    return _Finding(
        "unregistered",
        ConditionVerificationResult.UNKNOWN,
        f"no verifier is registered for {condition.verification.value}. A condition whose "
        "verifier does not exist has not been checked",
        condition.verification_detail,
    )


def _verify_capability(condition: ReviewCondition, compliance: SourceCompliance) -> _Finding:
    name = (condition.verification_detail or "").strip()
    verifier = f"capability:{name}"
    failures = capability_failures(name, compliance)

    if failures is None:
        return _Finding(
            verifier,
            ConditionVerificationResult.UNKNOWN,
            f"no capability named {name!r} is registered. The condition names something "
            "that does not exist, which is not the same as something that was checked "
            "and failed",
            name,
        )
    if failures:
        return _Finding(
            verifier,
            ConditionVerificationResult.UNSATISFIED,
            f"capability {name!r} is registered and its conformance check failed: "
            + "; ".join(failures),
            name,
        )
    return _Finding(
        verifier,
        ConditionVerificationResult.SATISFIED,
        f"capability {name!r} is implemented and its conformance check passes against the "
        f"configuration recorded for review version {compliance.review_version}. This "
        "establishes that the gate exists and refuses what it must; it does not observe a "
        "collector using it, because no collector exists",
        name,
    )


def _verify_access_method(
    source: SourceRecord, condition: ReviewCondition, compliance: SourceCompliance
) -> _Finding:
    name = (condition.verification_detail or "").strip()
    verifier = f"access-restriction:{name}"
    restriction = compliance.access_restriction

    if restriction is None or restriction.name != name:
        return _Finding(
            verifier,
            ConditionVerificationResult.UNKNOWN,
            f"no access restriction named {name!r} is configured for {source.source_id}. "
            "The condition names a restriction that nothing enforces",
            name,
        )

    # The registry is the authority on how a source may be reached. A
    # restriction holds when the source has the named profiles AND NO OTHERS: a
    # second profile appearing -- a bulk download, a browser path -- is exactly
    # the case this condition exists to catch.
    labels = {profile.label for profile in source.access_profiles}
    methods = {profile.access_method.value for profile in source.access_profiles}
    problems: list[str] = []

    missing_labels = sorted(restriction.profile_labels - labels)
    if missing_labels:
        problems.append(f"the registry has no access profile named {missing_labels}")

    extra_labels = sorted(labels - restriction.profile_labels)
    if extra_labels:
        problems.append(
            f"the source has additional access profiles {extra_labels}, so collection is "
            "not restricted to the approved path"
        )

    if restriction.access_methods:
        extra_methods = sorted(methods - restriction.access_methods)
        if extra_methods:
            problems.append(
                f"the source offers access methods {extra_methods} outside the restriction"
            )

    # The permitted path is only half the condition. The other half is that the
    # excluded material is refused, and a restriction that excluded nothing
    # would leave the exclusion unenforced.
    scope = compliance.resource_scope
    if not scope.excluded_dataset_families:
        problems.append(
            "no dataset family is excluded, so the restriction names a permitted path "
            "without refusing the excluded one"
        )
    elif not scope.require_dataset_family:
        problems.append(
            "an unclassified dataset is allowed, so a resource whose family was never "
            "recorded would pass the exclusion by having no family to match"
        )

    if problems:
        return _Finding(
            verifier, ConditionVerificationResult.UNSATISFIED, "; ".join(problems), name
        )

    return _Finding(
        verifier,
        ConditionVerificationResult.SATISFIED,
        f"the registry records exactly the approved access profile(s) "
        f"{sorted(restriction.profile_labels)} for {source.source_id}, and the resource "
        f"gate refuses dataset families {sorted(scope.excluded_dataset_families)}, "
        "including resources whose family is unrecorded",
        name,
    )


def satisfied_condition_keys(
    records: tuple[ConditionVerificationRecord, ...] | list[ConditionVerificationRecord],
) -> frozenset[str]:
    """The keys the eligibility gate may treat as satisfied.

    Only `SATISFIED` counts. `UNKNOWN` is excluded here rather than filtered by
    each caller, so that promoting it would mean editing this function rather
    than forgetting a condition in one of several call sites.
    """
    return frozenset(record.condition_key for record in records if record.satisfied)


def design_eligible(
    records: tuple[ConditionVerificationRecord, ...] | list[ConditionVerificationRecord],
) -> bool:
    """Whether every condition that does NOT depend on the deployment is satisfied.

    Mission 1.4 §24, and for reporting only. A source can be design-complete --
    every policy capability in place -- while a runtime credential is absent,
    and a reader deserves to be told which of the two is missing.

    It is **not** a gate. Nothing consults it before building an authorization,
    and the canonical gate still requires every condition, runtime ones
    included.
    """
    considered = [r for r in records if not r.runtime_dependent]
    return bool(considered) and all(r.satisfied for r in considered)
