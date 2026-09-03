"""Classify one candidate pair, through the Gateway, after authorization.

Mission 1.24 §13 and §14.

**Authorization is resolved before any source text is serialised.** The order is
the whole point: a refused pair must produce no prompt containing question text
and no transport invocation, so the check happens before `render_equivalence_prompt`
is called rather than before the socket. The tempting design -- build the prompt,
hand it to the Gateway, let the Gateway refuse -- has already assembled the text
by the time anything refuses, and leaves only the socket to prevent.

**Provider-agnostic.** This module names no provider and no model. It asks for a
tier; which provider serves that tier is configuration (ADR-006). A test asserts
that no vendor string appears in this package's source.

**The authorization is passed in, never computed here.** A classifier that could
read the source registry could decide its own permission. The caller performs the
join and hands over a decision; this module can only refuse or proceed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from sros_contracts import LlmTier
from sros_llm_gateway.types import LlmRequest, LlmResponse

from .candidates import CandidatePair
from .prompt import (
    OUTPUT_SCHEMA,
    PROMPT_ID,
    PROMPT_VERSION,
    QuestionForPrompt,
    render_equivalence_prompt,
)
from .rubric import RUBRIC_VERSION, EquivalenceDecision, ReasonCode

__all__ = [
    "CLASSIFIER_TASK",
    "SEMANTIC_TIER",
    "ExternalInferenceAuthorization",
    "ClassificationRefusedError",
    "EquivalenceClassification",
    "GatewayCompleter",
    "classify_pair",
]

CLASSIFIER_TASK = "semantic-problem-equivalence"

# The tier this component asks for. Same choice, same reasoning and same ADR as
# `sros_orchestrator.inference_readiness`: ADR-006 defines STRONG_MODEL as
# complex synthesis and hard judgment, and a false SAME is the costly error here.
# A test asserts the two agree, because two constants naming one decision drift.
SEMANTIC_TIER = LlmTier.STRONG_MODEL


@runtime_checkable
class ExternalInferenceAuthorization(Protocol):
    """The decision a caller must hold before any source text is serialised.

    Structural rather than imported: this package must not depend on the source
    registry, and `sros_acquisition.compliance.inference.InferenceAuthorization`
    satisfies this shape. A test in the acquisition suite asserts that it does,
    so the two cannot drift apart silently.
    """

    @property
    def authorized(self) -> bool: ...

    @property
    def source_id(self) -> str: ...

    @property
    def use_profile_id(self) -> str: ...

    @property
    def provider_id(self) -> str: ...

    @property
    def refusal_reasons(self) -> tuple[str, ...]: ...


class ClassificationRefusedError(RuntimeError):
    """Raised before serialisation when the authorization does not permit it.

    An exception rather than a returned value on purpose. A refusal that came
    back as a result object would sit beside real classifications in the same
    list, and the one thing this boundary must guarantee is that a refused pair
    produced nothing at all.
    """

    def __init__(self, reasons: tuple[str, ...]) -> None:
        self.reasons = reasons
        super().__init__(
            "external inference is not authorized for this pair; no prompt was built and "
            "no request was sent. Reasons: " + ("; ".join(reasons) or "unspecified")
        )


@dataclass(frozen=True)
class EquivalenceClassification:
    """One classified pair, with everything needed to audit it later.

    **No copied question body.** The evidence fragments are short verbatim
    references the model chose, capped by the schema; storing the posts here
    would duplicate a licensed corpus into an inference artifact for no gain,
    since both observations are addressable by key.

    **No confidence field.** None is requested from the model (see `prompt.py`),
    so there is nothing to store and nothing for a later reader to multiply by.
    """

    pair_id: str
    a_question_id: str
    b_question_id: str
    a_observation_key: str
    b_observation_key: str

    decision: EquivalenceDecision
    reason_code: ReasonCode
    rationale: str
    evidence: tuple[dict[str, str], ...]

    # Provenance that outlives the current configuration (design §4.5).
    rubric_version: str = RUBRIC_VERSION
    prompt_id: str = PROMPT_ID
    prompt_version: str = PROMPT_VERSION
    candidate_generator_version: str = ""
    provider: str = ""
    model: str = ""
    routing_version: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_units: float = 0.0
    priced: bool = False
    latency_ms: float = 0.0
    inference_run_id: str = ""
    source_id: str = ""
    use_profile_id: str = ""

    # Stated rather than implied. A model judgement has no calibrated
    # probability behind it, and this string is what stops a later stage from
    # inventing one (§18).
    confidence_semantics: str = "UNCALIBRATED_MODEL_JUDGEMENT_NO_NUMERIC_CONFIDENCE"

    def to_json(self) -> dict[str, object]:
        return {
            "pair_id": self.pair_id,
            "a_question_id": self.a_question_id,
            "b_question_id": self.b_question_id,
            "a_observation_key": self.a_observation_key,
            "b_observation_key": self.b_observation_key,
            "decision": self.decision.value,
            "reason_code": self.reason_code.value,
            "rationale": self.rationale,
            "evidence": [dict(e) for e in self.evidence],
            "confidence_semantics": self.confidence_semantics,
            "provenance": {
                "rubric_version": self.rubric_version,
                "prompt_id": self.prompt_id,
                "prompt_version": self.prompt_version,
                "candidate_generator_version": self.candidate_generator_version,
                "provider": self.provider,
                "model": self.model,
                "routing_version": self.routing_version,
                "inference_run_id": self.inference_run_id,
                "source_id": self.source_id,
                "use_profile_id": self.use_profile_id,
            },
            "usage": {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "cost_units": self.cost_units,
                "priced": self.priced,
                "latency_ms": self.latency_ms,
            },
        }


class GatewayCompleter(Protocol):
    """Just the one method this module needs from `LlmGateway`."""

    def complete(self, request: LlmRequest) -> LlmResponse: ...


@dataclass(frozen=True)
class _Parsed:
    decision: EquivalenceDecision
    reason_code: ReasonCode
    rationale: str
    evidence: tuple[dict[str, str], ...] = field(default_factory=tuple)


def _parse(structured: dict[str, Any] | None) -> _Parsed:
    """Turn the validated structured response into rubric values.

    The gateway has already validated the response against `OUTPUT_SCHEMA`, so
    this converts rather than defends. It still refuses an absent body: a
    response with no structured content is not a classification, and treating
    one as ABSTAIN would silently convert a transport or schema failure into a
    real epistemic answer.
    """
    if not structured:
        raise ValueError(
            "the provider returned no structured content. That is a transport or schema "
            "failure and not an ABSTAIN: an ABSTAIN is a judgement the rubric defines, and "
            "a missing answer is the absence of one"
        )
    return _Parsed(
        decision=EquivalenceDecision(str(structured["decision"])),
        reason_code=ReasonCode(str(structured["reason_code"])),
        rationale=str(structured.get("rationale") or ""),
        evidence=tuple(
            {"side": str(item["side"]), "fragment": str(item["fragment"])}
            for item in structured.get("evidence") or ()
        ),
    )


def classify_pair(
    gateway: GatewayCompleter,
    authorization: ExternalInferenceAuthorization,
    pair: CandidatePair,
    a: QuestionForPrompt,
    b: QuestionForPrompt,
    *,
    workspace_id: str,
    inference_run_id: str,
    research_session_id: str = "",
    correlation_id: str = "",
    candidate_generator_version: str = "",
    timeout_seconds: float = 60.0,
) -> EquivalenceClassification:
    """Classify one pair. Refuses before building a prompt if unauthorized.

    The first statement is the gate, and it is first for a reason a test pins:
    `render_equivalence_prompt` is not reached, so no string containing question
    text exists, so there is nothing for a later bug to send.
    """
    if not authorization.authorized:
        raise ClassificationRefusedError(tuple(authorization.refusal_reasons))

    prompt = render_equivalence_prompt(a, b)

    request = LlmRequest(
        tier=SEMANTIC_TIER,
        task=CLASSIFIER_TASK,
        prompt_template_id=PROMPT_ID,
        prompt_template_version=PROMPT_VERSION,
        response_schema=OUTPUT_SCHEMA,
        prompt=prompt,
        workspace_id=workspace_id,
        research_session_id=research_session_id,
        correlation_id=correlation_id or inference_run_id,
        timeout_seconds=timeout_seconds,
        requires_structured_output=True,
    )
    response = gateway.complete(request)
    parsed = _parse(response.structured)

    return EquivalenceClassification(
        pair_id=pair.pair_id,
        a_question_id=pair.a_question_id,
        b_question_id=pair.b_question_id,
        a_observation_key=pair.a_key,
        b_observation_key=pair.b_key,
        decision=parsed.decision,
        reason_code=parsed.reason_code,
        rationale=parsed.rationale,
        evidence=parsed.evidence,
        candidate_generator_version=candidate_generator_version,
        provider=response.usage.provider,
        model=response.usage.model,
        routing_version=response.usage.routing_version,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        cost_units=response.usage.cost_units,
        priced=response.usage.priced,
        latency_ms=response.usage.latency_ms,
        inference_run_id=inference_run_id,
        source_id=authorization.source_id,
        use_profile_id=authorization.use_profile_id,
    )
