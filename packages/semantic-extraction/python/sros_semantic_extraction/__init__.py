"""N08-B offline extractor for per-record semantic extraction (Mission 1.85.4).

    held NormalizedRecord -> se-question-text-surface@1.0.0
      -> trusted instructions + one isolated untrusted region (the surface, byte for byte)
      -> exactly one forced strict tool
      -> closed payload -> contract validator -> non-canonical validated extraction

This package cannot reach a provider. It holds no transport, constructs no provider, contains no call
site and reads no credential; a test enforces each of those over its syntax tree. Execution exists only
in `infrastructure/scripts/run_semantic_extraction_evaluation.py`, which refuses to run without a
verified packet, an unblocked status and a separate packet-scoped operator approval.
"""

from .prompt import (
    PROMPT_ID,
    PROMPT_VERSION,
    SurfaceNotTransmittableError,
    build_prompt,
    prompt_sha256,
)
from .request import (
    MAX_SCHEMA_RETRIES_PER_RECORD,
    AttemptOutcome,
    ExecutionBinding,
    build_extraction_request,
    interpret_payload,
    may_retry,
)
from .tool import CANONICAL_SCHEMA, STRICT_SCHEMA, TOOL_ID, TOOL_VERSION, schema_sha256

__all__ = [
    "CANONICAL_SCHEMA",
    "MAX_SCHEMA_RETRIES_PER_RECORD",
    "PROMPT_ID",
    "PROMPT_VERSION",
    "STRICT_SCHEMA",
    "TOOL_ID",
    "TOOL_VERSION",
    "AttemptOutcome",
    "ExecutionBinding",
    "SurfaceNotTransmittableError",
    "build_extraction_request",
    "build_prompt",
    "interpret_payload",
    "may_retry",
    "prompt_sha256",
    "schema_sha256",
]
