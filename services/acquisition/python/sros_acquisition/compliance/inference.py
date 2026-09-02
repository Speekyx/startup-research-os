"""Whether source-derived content may be sent to an external model provider.

`model-inference-execution-governance-v1.md`. Mission 1.23, ADR-033.

**One boundary, four layers, decided before any source text is serialised.** The
architecture this replaces is the tempting one: build the prompt, hand it to the
Gateway, let the Gateway notice the provider is forbidden. By then the text has
been assembled and the only thing left to prevent is the socket.

    source review     external_model_transmission PERMITTED for (source, profile)
        AND
    use profile       external_model_egress PERMITTED_TO_APPROVED_PROVIDERS
        AND
    provider policy   the provider's posture is APPROVED
        AND
    runtime           that provider is the configured one, and it is configured
        → authorized

**Every layer refuses with its own reason.** An operator who cannot tell a
governance refusal from a missing credential will change the wrong thing, and
collapsing all four into `MODEL_NOT_AVAILABLE` is how a governance decision comes
to look like an outage.

**The dependency direction is deliberate** (§29 of the mission brief). This module
reads the source registry and the provider policy and produces a decision. The
Gateway knows nothing about sources, and no provider adapter queries the
registry: the join happens here, once.

**This module reaches no network and calls no model.** It answers a question
about permissions; the answer is what a caller must hold before it may build a
request.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Any

from sros_contracts import PolicyAssessment

from ..registry.models import (
    EGRESS_DENIED,
    EGRESS_NOT_ASSESSED,
    AssessedUseProfile,
    SourceRecord,
)

__all__ = [
    "DEFAULT_PROVIDER_POLICY_PATH",
    "InferenceRefusalReason",
    "InferenceAuthorization",
    "ProviderPolicy",
    "ProviderPosture",
    "authorize_external_inference",
    "load_provider_policy",
]

DEFAULT_PROVIDER_POLICY_PATH = "docs/data/model-provider-policy-v1.json"

# The activity ADR-033 added. Named once here so a typo is an import error
# rather than a permission that silently reads as NOT_ASSESSED.
EXTERNAL_MODEL_TRANSMISSION = "external_model_transmission"

APPROVING_ASSESSMENTS = frozenset(
    {PolicyAssessment.PERMITTED, PolicyAssessment.PERMITTED_WITH_CONDITIONS}
)


class InferenceRefusalReason:
    """Why external inference was refused, one code per gate.

    Strings rather than an enum in `sros_contracts`: these are refusal reasons
    for one operation in one service, not a value any contract stores. When a
    later mission persists them, that is the moment they earn a generated enum.
    """

    SOURCE_TRANSMISSION_NOT_ASSESSED = "SOURCE_EXTERNAL_MODEL_TRANSMISSION_NOT_ASSESSED"
    SOURCE_TRANSMISSION_REFUSED = "SOURCE_EXTERNAL_MODEL_TRANSMISSION_REFUSED"
    SOURCE_REVIEW_MISSING = "SOURCE_REVIEW_MISSING_FOR_PROFILE"
    PROFILE_EGRESS_NOT_ASSESSED = "PROFILE_EXTERNAL_MODEL_EGRESS_NOT_ASSESSED"
    PROFILE_EGRESS_DENIED = "PROFILE_EXTERNAL_MODEL_EGRESS_DENIED"
    PROVIDER_NOT_ASSESSED = "PROVIDER_DATA_USE_POSTURE_NOT_ASSESSED"
    PROVIDER_NOT_APPROVED = "PROVIDER_NOT_APPROVED"
    PROVIDER_NEVER_PRODUCTION = "PROVIDER_IS_A_TEST_DOUBLE"
    PROVIDER_NOT_CONFIGURED = "PROVIDER_NOT_CONFIGURED"


@dataclass(frozen=True)
class ProviderPosture:
    """What one provider contractually does with content sent to it.

    A fact about the PROVIDER. No source term appears here and no vendor name
    appears in a source review; the two domains meet once, in
    `authorize_external_inference`.
    """

    provider_id: str
    posture: str
    route_assessed: str
    trains_on_submitted_content: str
    retention: str
    operator_action_required: str
    notes: str = ""

    APPROVED = "APPROVED"
    NOT_APPROVED = "NOT_APPROVED"
    NOT_ASSESSED = "NOT_ASSESSED"
    NEVER_PRODUCTION = "NEVER_PRODUCTION"

    @property
    def approved(self) -> bool:
        return self.posture == self.APPROVED


@dataclass(frozen=True)
class ProviderPolicy:
    """Every reviewed provider. An unlisted provider is NOT_ASSESSED."""

    policy_version: int
    reviewed_at: str
    postures: dict[str, ProviderPosture] = field(default_factory=dict)

    def posture_for(self, provider_id: str) -> ProviderPosture:
        """The reviewed posture, or a synthesised NOT_ASSESSED one.

        **Never `None`.** A caller that had to handle absence would eventually
        handle it by continuing, and the whole point is that an unreviewed
        provider refuses for a reason that names itself.
        """
        existing = self.postures.get(provider_id)
        if existing is not None:
            return existing
        return ProviderPosture(
            provider_id=provider_id,
            posture=ProviderPosture.NOT_ASSESSED,
            route_assessed="",
            trains_on_submitted_content="UNKNOWN",
            retention="UNKNOWN",
            operator_action_required=(
                "Review this provider's data-use posture and record it in "
                f"{DEFAULT_PROVIDER_POLICY_PATH} before it can receive source content."
            ),
        )


@dataclass(frozen=True)
class InferenceAuthorization:
    """The decision, and everything a caller needs to explain it.

    `authorized` is the only field a caller may branch on to proceed. The rest
    exists so an operator can see WHICH gate refused -- four layers collapsed
    into one boolean is a support ticket nobody can answer.
    """

    authorized: bool
    source_id: str
    use_profile_id: str
    provider_id: str
    refusal_reasons: tuple[str, ...] = ()
    detail: tuple[str, ...] = ()

    # What each layer answered, recorded whether or not it refused, so a
    # decision can be audited without re-running it.
    source_transmission_state: str = ""
    profile_egress_state: str = ""
    provider_posture: str = ""
    provider_configured: bool = False

    def to_json(self) -> dict[str, object]:
        return {
            "authorized": self.authorized,
            "source_id": self.source_id,
            "use_profile_id": self.use_profile_id,
            "provider_id": self.provider_id,
            "refusal_reasons": list(self.refusal_reasons),
            "detail": list(self.detail),
            "layers": {
                "source_transmission": self.source_transmission_state,
                "profile_egress": self.profile_egress_state,
                "provider_posture": self.provider_posture,
                "provider_configured": self.provider_configured,
            },
        }


def load_provider_policy(path: str | pathlib.Path | None = None) -> ProviderPolicy:
    raw: dict[str, Any] = json.loads(
        pathlib.Path(path or DEFAULT_PROVIDER_POLICY_PATH).read_text(encoding="utf-8")
    )
    postures = {}
    for entry in raw.get("providers") or ():
        posture = ProviderPosture(
            provider_id=str(entry["provider_id"]),
            posture=str(entry["posture"]),
            route_assessed=str(entry.get("route_assessed") or ""),
            trains_on_submitted_content=str(entry.get("trains_on_submitted_content") or "UNKNOWN"),
            retention=str(entry.get("retention") or "UNKNOWN"),
            operator_action_required=str(entry.get("operator_action_required") or ""),
            notes=str(entry.get("notes") or ""),
        )
        postures[posture.provider_id] = posture
    return ProviderPolicy(
        policy_version=int(raw.get("policy_version") or 0),
        reviewed_at=str(raw.get("reviewed_at") or ""),
        postures=postures,
    )


def authorize_external_inference(
    source: SourceRecord,
    profile: AssessedUseProfile,
    provider_id: str,
    *,
    policy: ProviderPolicy,
    provider_configured: bool,
) -> InferenceAuthorization:
    """The single decision point, before any source text is serialised.

    **Every layer is evaluated even after one refuses.** Stopping at the first
    would tell an operator to fix one thing, and they would fix it and be
    refused again -- three times, once per remaining gate.

    `provider_configured` is passed in rather than read here: whether a
    credential exists is a fact about the runtime environment, and a governance
    module that read environment variables would be two things at once.
    """
    reasons: list[str] = []
    detail: list[str] = []

    # ------------------------------------------------------------ 1. source
    review = source.review_for(profile.use_profile_id)
    if review is None:
        transmission = "NO_REVIEW"
        reasons.append(InferenceRefusalReason.SOURCE_REVIEW_MISSING)
        detail.append(
            f"{source.source_id!r} has no review under {profile.use_profile_id!r}. "
            "Approval never transfers between profiles (ADR-027)"
        )
    else:
        assessment = review.assessment(EXTERNAL_MODEL_TRANSMISSION)
        transmission = assessment.value
        if assessment is PolicyAssessment.NOT_ASSESSED:
            reasons.append(InferenceRefusalReason.SOURCE_TRANSMISSION_NOT_ASSESSED)
            detail.append(
                f"the review of {source.source_id!r} under {profile.use_profile_id!r} has "
                "not assessed whether material may be transmitted to a third-party model "
                "processor. Model INFERENCE being permitted is a different activity "
                "(ADR-033)"
            )
        elif assessment not in APPROVING_ASSESSMENTS:
            reasons.append(InferenceRefusalReason.SOURCE_TRANSMISSION_REFUSED)
            detail.append(
                f"the review records external model transmission as {assessment.value} "
                f"for {source.source_id!r}"
            )

    # ----------------------------------------------------------- 2. profile
    if profile.external_model_egress == EGRESS_NOT_ASSESSED:
        reasons.append(InferenceRefusalReason.PROFILE_EGRESS_NOT_ASSESSED)
        detail.append(
            f"{profile.use_profile_id!r} has not stated whether this deployment permits "
            "source-derived content to leave for a model processor. Unassessed refuses; "
            "it is not the same as decided-against, and the field distinguishes them"
        )
    elif profile.external_model_egress == EGRESS_DENIED:
        reasons.append(InferenceRefusalReason.PROFILE_EGRESS_DENIED)
        detail.append(f"{profile.use_profile_id!r} denies external model egress")

    # ---------------------------------------------------------- 3. provider
    posture = policy.posture_for(provider_id)
    if posture.posture == ProviderPosture.NEVER_PRODUCTION:
        reasons.append(InferenceRefusalReason.PROVIDER_NEVER_PRODUCTION)
        detail.append(
            f"{provider_id!r} is a test double and cannot be a production route, however "
            "it is configured"
        )
    elif posture.posture == ProviderPosture.NOT_ASSESSED:
        reasons.append(InferenceRefusalReason.PROVIDER_NOT_ASSESSED)
        detail.append(
            f"{provider_id!r} has no reviewed data-use posture. " + posture.operator_action_required
        )
    elif not posture.approved:
        reasons.append(InferenceRefusalReason.PROVIDER_NOT_APPROVED)
        detail.append(
            f"{provider_id!r} is reviewed and NOT approved for the route assessed: "
            f"{posture.route_assessed}"
        )

    # ----------------------------------------------------------- 4. runtime
    if not provider_configured:
        reasons.append(InferenceRefusalReason.PROVIDER_NOT_CONFIGURED)
        detail.append(
            f"{provider_id!r} is not configured in this deployment. "
            + (posture.operator_action_required or "No credential or tier binding is set.")
        )

    return InferenceAuthorization(
        authorized=not reasons,
        source_id=source.source_id,
        use_profile_id=profile.use_profile_id,
        provider_id=provider_id,
        refusal_reasons=tuple(reasons),
        detail=tuple(detail),
        source_transmission_state=transmission,
        profile_egress_state=profile.external_model_egress,
        provider_posture=posture.posture,
        provider_configured=provider_configured,
    )
