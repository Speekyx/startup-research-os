"""Request construction and response interpretation. Pure functions; no call site.

This module builds an `LlmRequest` and reads what came back. It holds no transport, constructs no
provider and contains no `.complete(` call: the only call site is the approval-guarded runner script.

Retry semantics, as ratified for the packet and no broader than N08-A preregistered:
    transport retries inside the Gateway: 0 (`max_retries=0`; a retry is a second billed call)
    a SCHEMA failure (no tool payload, missing required keys, or a forced tool call that did not
      complete normally): at most ONE further identical request, logged as a possible injection
    a VALIDATOR refusal of a well-formed payload: not retried
    any provider error: not retried, never a fallback provider
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from sros_contracts import LlmTier
from sros_llm_gateway.types import LlmRequest
from sros_semantic_extraction_contract import (
    ExtractionContext,
    ValidationReport,
    validate_extraction,
)

from .prompt import PROMPT_ID, PROMPT_VERSION, build_prompt
from .tool import STRICT_SCHEMA

__all__ = [
    "MAX_SCHEMA_RETRIES_PER_RECORD",
    "AttemptOutcome",
    "ExecutionBinding",
    "build_extraction_request",
    "interpret_payload",
    "may_retry",
]

MAX_SCHEMA_RETRIES_PER_RECORD = 1


@dataclass(frozen=True)
class ExecutionBinding:
    """The packet fields a request needs. Built by the runner from a verified packet only."""

    packet_id: str
    workspace_id: str
    tier: LlmTier
    timeout_seconds: float


class AttemptOutcome(StrEnum):
    ACCEPTED = "ACCEPTED"
    VALIDATOR_REFUSED = "VALIDATOR_REFUSED"
    SCHEMA_FAILURE = "SCHEMA_FAILURE"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    OUTPUT_LIMIT_REACHED = "OUTPUT_LIMIT_REACHED"
    MODEL_REFUSED = "MODEL_REFUSED"


def build_extraction_request(
    surface: str, packet_index: int, binding: ExecutionBinding
) -> LlmRequest:
    return LlmRequest(
        tier=binding.tier,
        task="first-person-semantic-extraction",
        prompt_template_id=PROMPT_ID,
        prompt_template_version=PROMPT_VERSION,
        variables={},
        response_schema=STRICT_SCHEMA,
        prompt=build_prompt(surface, packet_index),
        workspace_id=binding.workspace_id,
        research_session_id="",
        correlation_id=f"{binding.packet_id}#{packet_index}",
        timeout_seconds=binding.timeout_seconds,
        max_retries=0,
        requires_structured_output=True,
    )


def interpret_payload(
    payload: Any, context: ExtractionContext
) -> tuple[AttemptOutcome, ValidationReport]:
    report = validate_extraction(payload, context)
    return (
        AttemptOutcome.ACCEPTED if report.accepted else AttemptOutcome.VALIDATOR_REFUSED
    ), report


def may_retry(outcome: AttemptOutcome, schema_retries_used: int) -> bool:
    return (
        outcome is AttemptOutcome.SCHEMA_FAILURE
        and schema_retries_used < MAX_SCHEMA_RETRIES_PER_RECORD
    )
