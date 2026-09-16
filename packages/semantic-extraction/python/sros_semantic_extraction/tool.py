"""The forced strict output tool, `first-person-semantic-extraction-tool@1.0.0`.

Two schemas with two jobs. The STRICT schema is what the provider receives: only keywords the reviewed
strict-tool profile says the provider enforces (types, required, additionalProperties false, enum,
nullable type unions). The CANONICAL schema adds what the provider does not enforce (item and length
bounds). Neither is the authority: the contract validator decides, locally, after the response.

The strict schema is written out here rather than projected at import, so this package imports nothing
from the provider layer. A test proves it is exactly the reviewed projection of the canonical schema,
and the packet pins both digests. It contains no source text, because the provider caches tool schemas.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sros_semantic_extraction_contract.finding import MAX_FINDINGS, MAX_QUOTE, MIN_QUOTE
from sros_semantic_extraction_contract.labels import extractable_labels

__all__ = ["CANONICAL_SCHEMA", "STRICT_SCHEMA", "TOOL_ID", "TOOL_VERSION", "schema_sha256"]

TOOL_ID = "first-person-semantic-extraction-tool"
TOOL_VERSION = "1.0.0"
_STATES = ["FINDINGS_PRESENT", "NO_FINDING_ESTABLISHED", "ABSTAINED_TEXT_INSUFFICIENT"]
_TYPES = [label.label_id for label in extractable_labels()]

STRICT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["extraction_state", "findings"],
    "properties": {
        "extraction_state": {"type": "string", "enum": _STATES},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "finding_type",
                    "evidence_quote",
                    "evidence_occurrence",
                    "subject_quote",
                    "subject_occurrence",
                ],
                "properties": {
                    "finding_type": {"type": "string", "enum": _TYPES},
                    "evidence_quote": {"type": "string"},
                    "evidence_occurrence": {"type": "integer"},
                    "subject_quote": {"type": ["string", "null"]},
                    "subject_occurrence": {"type": ["integer", "null"]},
                },
            },
        },
    },
}

CANONICAL_SCHEMA: dict[str, Any] = json.loads(json.dumps(STRICT_SCHEMA))
CANONICAL_SCHEMA["properties"]["findings"]["maxItems"] = MAX_FINDINGS
_item = CANONICAL_SCHEMA["properties"]["findings"]["items"]["properties"]
_item["evidence_quote"].update({"minLength": MIN_QUOTE, "maxLength": MAX_QUOTE})
_item["evidence_occurrence"]["minimum"] = 1
_item["subject_quote"]["maxLength"] = 120
_item["subject_occurrence"]["minimum"] = 1


def schema_sha256(schema: dict[str, Any]) -> str:
    canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
