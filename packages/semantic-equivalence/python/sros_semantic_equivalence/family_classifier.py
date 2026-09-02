"""Classify one candidate pair for the FAMILY relation, after authorization.

Mission 1.25. Same boundary and same ordering as `classifier.py`: the
authorization is resolved before any source text is serialised, not before the
socket, so a refused pair produces no prompt containing question text and no
transport invocation.

**A separate function rather than a relation parameter.** The two classifiers
build different prompts, validate different schemas and produce different
propositions; a single function taking a relation would branch four times and
would eventually take the wrong branch silently, because both inputs are a pair
of questions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sros_llm_gateway.types import LlmRequest

from .candidates import CandidatePair
from .classifier import (
    SEMANTIC_TIER,
    ClassificationRefusedError,
    ExternalInferenceAuthorization,
    GatewayCompleter,
)
from .family_prompt import (
    FAMILY_OUTPUT_SCHEMA,
    FAMILY_PROMPT_ID,
    FAMILY_PROMPT_VERSION,
    render_family_prompt,
)
from .family_rubric import FAMILY_RUBRIC_VERSION, FamilyDecision, FamilyReasonCode
from .prompt import QuestionForPrompt
from .relations import EquivalenceRelation

__all__ = [
    "FAMILY_CLASSIFIER_TASK",
    "FamilyClassification",
    "classify_family_pair",
]

FAMILY_CLASSIFIER_TASK = "semantic-problem-family"


@dataclass(frozen=True)
class FamilyClassification:
    """One classified pair, with everything needed to audit it later.

    Carries `relation` explicitly. Two pairwise judgements with different
    meanings and the same shape are indistinguishable in storage without it, and
    the cost of that confusion is a family judgement read as an equivalence.
    """

    pair_id: str
    a_question_id: str
    b_question_id: str
    a_observation_key: str
    b_observation_key: str

    relation: str
    decision: FamilyDecision
    reason_code: FamilyReasonCode
    blocked_goal_a: str
    blocked_goal_b: str
    rationale: str

    rubric_version: str = FAMILY_RUBRIC_VERSION
    prompt_id: str = FAMILY_PROMPT_ID
    prompt_version: str = FAMILY_PROMPT_VERSION
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

    confidence_semantics: str = "UNCALIBRATED_MODEL_JUDGEMENT_NO_NUMERIC_CONFIDENCE"

    @property
    def proposition(self) -> str:
        """The only sentence this classification licenses.

        Rendered from the relation rather than written here, so the claim and
        the relation cannot drift apart.
        """
        return EquivalenceRelation.SAME_PROBLEM_FAMILY.proposition_template.format(
            procedure=f"{self.rubric_version} via {self.prompt_id}@{self.prompt_version}",
            a=self.a_question_id,
            b=self.b_question_id,
        )

    def to_json(self) -> dict[str, object]:
        return {
            "pair_id": self.pair_id,
            "relation": self.relation,
            "a_question_id": self.a_question_id,
            "b_question_id": self.b_question_id,
            "a_observation_key": self.a_observation_key,
            "b_observation_key": self.b_observation_key,
            "decision": self.decision.value,
            "reason_code": self.reason_code.value,
            "blocked_goal_a": self.blocked_goal_a,
            "blocked_goal_b": self.blocked_goal_b,
            "rationale": self.rationale,
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


def _parse(structured: dict[str, Any] | None) -> dict[str, Any]:
    if not structured:
        raise ValueError(
            "the provider returned no structured content. That is a transport or schema "
            "failure and not an ABSTAIN: an ABSTAIN is a judgement the rubric defines, and "
            "a missing answer is the absence of one"
        )
    return {
        "decision": FamilyDecision(str(structured["decision"])),
        "reason_code": FamilyReasonCode(str(structured["reason_code"])),
        "blocked_goal_a": str(structured.get("blocked_goal_a") or ""),
        "blocked_goal_b": str(structured.get("blocked_goal_b") or ""),
        "rationale": str(structured.get("rationale") or ""),
    }


def classify_family_pair(
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
) -> FamilyClassification:
    """Classify one pair. Refuses before building a prompt if unauthorized."""
    if not authorization.authorized:
        raise ClassificationRefusedError(tuple(authorization.refusal_reasons))

    prompt = render_family_prompt(a, b)
    request = LlmRequest(
        tier=SEMANTIC_TIER,
        task=FAMILY_CLASSIFIER_TASK,
        prompt_template_id=FAMILY_PROMPT_ID,
        prompt_template_version=FAMILY_PROMPT_VERSION,
        response_schema=FAMILY_OUTPUT_SCHEMA,
        prompt=prompt,
        workspace_id=workspace_id,
        research_session_id=research_session_id,
        correlation_id=correlation_id or inference_run_id,
        timeout_seconds=timeout_seconds,
        requires_structured_output=True,
    )
    response = gateway.complete(request)
    parsed = _parse(response.structured)

    return FamilyClassification(
        pair_id=pair.pair_id,
        a_question_id=pair.a_question_id,
        b_question_id=pair.b_question_id,
        a_observation_key=pair.a_key,
        b_observation_key=pair.b_key,
        relation=EquivalenceRelation.SAME_PROBLEM_FAMILY.value,
        decision=parsed["decision"],
        reason_code=parsed["reason_code"],
        blocked_goal_a=parsed["blocked_goal_a"],
        blocked_goal_b=parsed["blocked_goal_b"],
        rationale=parsed["rationale"],
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
