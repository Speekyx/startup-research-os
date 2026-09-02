"""Whether a semantic-equivalence request could reach an external model at all.

Mission 1.24 §0.A. **Seven gates, and `ANTHROPIC_API_KEY` is only one of them.**

Mission 1.23 built the governance gate and proved it refused on
`PROVIDER_NOT_CONFIGURED`, reading the presence of a credential environment
variable. That is necessary and nowhere near sufficient. Mission 1.22 separately
found **every inference tier bound to `null`**, and a deployment with a valid key
and an unbound tier routes nowhere -- so reducing *provider configured* to *the
key exists* would report ready for a system that cannot make a call.

    intended tier          the component asks for a logical tier, never a provider
    tier is bound          that tier resolves to a provider at all
    tier is anthropic      it resolves to the provider the policy approved
    model is named         ADR-006 forbids a hard-coded model, so config must name one
    credential present     ANTHROPIC_API_KEY is set (its VALUE is never read here)
    source review          external_model_transmission permitted for (source, profile)
    profile egress         external_model_egress permits this class of egress

**Every gate is evaluated even after one fails**, the same rule
`authorize_external_inference` follows and for the same reason: an operator told
only the first failure fixes it and is refused again, once per remaining gate.

**Why this lives in the orchestrator.** It is a JOIN of two facts that belong to
different owners -- Gateway routing configuration and source governance -- and
neither package may import the other. `sources.py` already established the
shape: registry facts are read from the DATABASE rather than by importing
`sros_acquisition`, which computes the same verdicts in Python for review
tooling. A test asserts the two agree rather than assuming it.

**This module calls no model and reads no credential VALUE.** It answers whether
a call would be permitted and routable. Nothing here is an authorization to send:
`authorize_external_inference` remains the decision a caller must hold, and this
check exists so an operator learns what to configure before that refusal.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Protocol

from sros_contracts import LlmTier

__all__ = [
    "SEMANTIC_EQUIVALENCE_TIER",
    "APPROVED_PROVIDER",
    "CREDENTIAL_ENV",
    "ReadinessGate",
    "InferenceReadiness",
    "RegistryDatabase",
    "evaluate_inference_readiness",
]

# ---------------------------------------------------------------------------
# The tier this component asks for, decided ONCE and here.
#
# NOT invented from a mission prompt, and not a preference. ADR-006 defines the
# tiers by the work they serve: FAST_MODEL is "high-volume, cheap, low-latency,
# simple tasks", BALANCED_MODEL is "default reasoning for most analytical work",
# and STRONG_MODEL is "complex synthesis, planning, hard judgment".
#
# Semantic problem equivalence is hard judgment by construction. Its canonical
# hard negatives are three Mission 1.20 questions sharing 182 characters of exact
# runc diagnostic that then diverge into three unrelated failures, and the V1
# acceptance criterion prioritises FALSE-POSITIVE avoidance -- a wrong SAME is
# worse than an ABSTAIN. That is the tier ADR-006 describes, and ADR-006 also
# says never to downgrade a tier silently.
#
# The component still requests a TIER and never a provider or a model. Which
# provider serves this tier is configuration, which is the whole point of the
# indirection.
SEMANTIC_EQUIVALENCE_TIER = LlmTier.STRONG_MODEL

# The provider Mission 1.23's policy approved, for THIS route. Named here only
# so the readiness check can say the configured tier disagrees with the approved
# policy; the classifier never names a provider.
APPROVED_PROVIDER = "anthropic"

# Read for PRESENCE only. The value is never read, printed, logged or returned.
CREDENTIAL_ENV = "ANTHROPIC_API_KEY"

_TIER_ENV_PREFIX = {
    LlmTier.FAST_MODEL: "LLM_TIER_FAST",
    LlmTier.BALANCED_MODEL: "LLM_TIER_BALANCED",
    LlmTier.STRONG_MODEL: "LLM_TIER_STRONG",
    LlmTier.EMBEDDING_MODEL: "LLM_TIER_EMBEDDING",
}


@dataclass(frozen=True)
class ReadinessGate:
    """One gate, its verdict, and what an operator would do about it.

    `operator_action` is empty when the gate passes. It names **non-secret**
    environment variables only: a readiness tool that told an operator to put a
    key somewhere is a tool that will eventually be followed literally into a
    tracked file.
    """

    name: str
    passed: bool
    observed: str
    detail: str
    operator_action: str = ""

    def to_json(self) -> dict[str, object]:
        return {
            "gate": self.name,
            "passed": self.passed,
            "observed": self.observed,
            "detail": self.detail,
            "operator_action": self.operator_action,
        }


@dataclass(frozen=True)
class InferenceReadiness:
    """Whether a semantic-equivalence call could be made, and what blocks it."""

    ready: bool
    source_id: str
    use_profile_id: str
    tier: str
    gates: tuple[ReadinessGate, ...]

    @property
    def failed(self) -> tuple[ReadinessGate, ...]:
        return tuple(g for g in self.gates if not g.passed)

    @property
    def operator_actions(self) -> tuple[str, ...]:
        """The distinct things to configure, in gate order and de-duplicated."""
        seen: list[str] = []
        for gate in self.failed:
            if gate.operator_action and gate.operator_action not in seen:
                seen.append(gate.operator_action)
        return tuple(seen)

    def to_json(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "source_id": self.source_id,
            "use_profile_id": self.use_profile_id,
            "tier": self.tier,
            "gates": [g.to_json() for g in self.gates],
            "operator_actions": list(self.operator_actions),
        }


class RegistryDatabase(Protocol):
    """A non-tenant connection provider.

    Same protocol and same reasoning as `sources.RegistryDatabase`: source
    reviews and use profiles are global platform metadata with no `workspace_id`
    and no row-level security, and reading them through a tenant transaction
    would imply an isolation that does not exist.
    """

    def connection(self) -> AbstractContextManager[Any]: ...


# The assessments that count as permitting. Mirrors
# `sros_acquisition.compliance.inference.APPROVING_ASSESSMENTS`; a test asserts
# the two agree rather than trusting this comment.
_APPROVING = frozenset({"PERMITTED", "PERMITTED_WITH_CONDITIONS"})
_EGRESS_PERMITTED = "PERMITTED_TO_APPROVED_PROVIDERS"


def _tier_gates(env: Mapping[str, str]) -> list[ReadinessGate]:
    prefix = _TIER_ENV_PREFIX[SEMANTIC_EQUIVALENCE_TIER]
    provider = (env.get(f"{prefix}_PROVIDER") or "").strip()
    model = (env.get(f"{prefix}_MODEL") or "").strip()

    # `config.py` treats the literal string "null" as unconfigured, and the
    # shipped .env.example uses it. Reproduced rather than reinvented: a
    # readiness check that disagreed with the loader about what "configured"
    # means would be worse than no check.
    bound = bool(provider) and provider != "null"

    return [
        ReadinessGate(
            name="gateway-tier-bound",
            passed=bound,
            observed=f"{prefix}_PROVIDER={provider or '(unset)'}",
            detail=(
                f"the semantic classifier requests {SEMANTIC_EQUIVALENCE_TIER.value}, and that "
                "tier must resolve to a provider. `null` and empty both mean unconfigured"
            ),
            operator_action=(f"set {prefix}_PROVIDER={APPROVED_PROVIDER}" if not bound else ""),
        ),
        ReadinessGate(
            name="gateway-tier-provider-approved",
            passed=bound and provider == APPROVED_PROVIDER,
            observed=f"{prefix}_PROVIDER={provider or '(unset)'}",
            detail=(
                f"the tier must resolve to {APPROVED_PROVIDER!r}, the only provider whose "
                "data-use posture Mission 1.23 approved for this route. A tier bound to "
                "another provider is a routing decision that bypasses the policy"
            ),
            operator_action=(
                f"set {prefix}_PROVIDER={APPROVED_PROVIDER}"
                if bound and provider != APPROVED_PROVIDER
                else ""
            ),
        ),
        ReadinessGate(
            name="gateway-tier-model-named",
            passed=bool(model),
            observed=f"{prefix}_MODEL={model or '(unset)'}",
            detail=(
                "ADR-006 forbids a hard-coded model name, so the model is configuration and "
                "an unnamed one routes nowhere. The resolved model is recorded on every "
                "response, which is what makes historical results comparable"
            ),
            operator_action=(
                f"set {prefix}_MODEL to the model identifier for this route" if not model else ""
            ),
        ),
        ReadinessGate(
            name="provider-credential-present",
            passed=bool((env.get(CREDENTIAL_ENV) or "").strip()),
            # The NAME only. The value is never read into this string.
            observed=(
                f"{CREDENTIAL_ENV} is set"
                if (env.get(CREDENTIAL_ENV) or "").strip()
                else f"{CREDENTIAL_ENV} is empty or unset"
            ),
            detail=(
                "presence only; this check never reads, prints or returns the value, and no "
                "tracked file in this repository is a place to put one"
            ),
            operator_action=(
                f"provide {CREDENTIAL_ENV} in the local untracked environment"
                if not (env.get(CREDENTIAL_ENV) or "").strip()
                else ""
            ),
        ),
    ]


def _governance_gates(
    db: RegistryDatabase, source_id: str, use_profile_id: str
) -> list[ReadinessGate]:
    """Read the CURRENT review and the profile, from the database.

    Current means `superseded_at IS NULL` for that `(source, profile)` line --
    the same append-only versioning `sros_acquisition` applies, read here rather
    than reimplemented.
    """
    with db.connection() as conn:
        review = conn.execute(
            """SELECT review_version, approval_state, model_processing,
                      external_model_transmission
                 FROM registry.source_policy_reviews
                WHERE source_id = %s
                  AND assessed_use_profile = %s
                  AND superseded_at IS NULL
                ORDER BY review_version DESC
                LIMIT 1""",
            (source_id, use_profile_id),
        ).fetchone()
        profile = conn.execute(
            "SELECT external_model_egress FROM registry.use_profiles WHERE id = %s",
            (use_profile_id,),
        ).fetchone()

    processing = (review[2] if review else None) or "NO_REVIEW"
    transmission = (review[3] if review else None) or "NOT_ASSESSED"
    egress = (profile[0] if profile else None) or "NOT_ASSESSED"

    return [
        ReadinessGate(
            name="source-model-processing-permitted",
            passed=processing in _APPROVING,
            observed=f"model_processing={processing}",
            detail=(
                f"whether a model may READ {source_id!r} material under {use_profile_id!r}. "
                "A NULL column reads NOT_ASSESSED, and unassessed refuses"
            ),
            operator_action=(
                "record a review assessment; this is a governance act, not configuration"
                if processing not in _APPROVING
                else ""
            ),
        ),
        ReadinessGate(
            name="source-external-model-transmission-permitted",
            passed=transmission in _APPROVING,
            observed=f"external_model_transmission={transmission}",
            detail=(
                "whether that material may LEAVE this deployment for a third-party model "
                "processor (ADR-033). A separate act from reading it, and a separate answer"
            ),
            operator_action=(
                "record a review assessment; this is a governance act, not configuration"
                if transmission not in _APPROVING
                else ""
            ),
        ),
        ReadinessGate(
            name="profile-external-model-egress-permitted",
            passed=egress == _EGRESS_PERMITTED,
            observed=f"external_model_egress={egress}",
            detail=(
                f"whether {use_profile_id!r} permits this class of egress at all. "
                "NOT_ASSESSED and DENIED both refuse, and they are not the same fact"
            ),
            operator_action=(
                "record a profile decision; this is a governance act, not configuration"
                if egress != _EGRESS_PERMITTED
                else ""
            ),
        ),
    ]


def evaluate_inference_readiness(
    db: RegistryDatabase,
    source_id: str,
    use_profile_id: str,
    env: Mapping[str, str] | None = None,
) -> InferenceReadiness:
    """Every gate, evaluated, in the order an operator would meet them.

    Configuration gates come first because they are the ones an operator can
    change; governance gates follow because a refusal there is a review act
    rather than a variable. Both are reported whatever the other says.
    """
    environ = env if env is not None else os.environ
    gates = tuple(_tier_gates(environ) + _governance_gates(db, source_id, use_profile_id))
    return InferenceReadiness(
        ready=all(g.passed for g in gates),
        source_id=source_id,
        use_profile_id=use_profile_id,
        tier=SEMANTIC_EQUIVALENCE_TIER.value,
        gates=gates,
    )
