"""CI gate 92. Mission 1.84.19. The provider-strict projection of output schema v1.2.0, frozen.

    uv run python infrastructure/scripts/render_second_opportunity_provider_strict_projection.py --write
    uv run python infrastructure/scripts/render_second_opportunity_provider_strict_projection.py --check

Execution V6 was refused at stage 5 on one key its closed contract does not declare. The operator
kept the contract, the gate, the prompt and the headroom policy exactly as they are, and asked for
the provider's strict tool use over a deterministic projection of the contract onto what strict
mode documents enforcing, with the full contract still deciding stage 5 locally.

This gate re-derives that projection and everything said about it:

* the provider capability, as the first-party documentation states it, with each quoted fragment
  located by line in bytes whose digest is recorded;
* the projection itself, by `project_strict_input_schema(canonical, profile)` and nothing else;
* **every one of the contract's constraints accounted for**, joined with the repository's own
  constraint inventory: provider-enforced, local-only, or carried in a description, and whether the
  prompt states it in words;
* the invariants: the same property names and required names at every object, every object
  closed, the same types and enums, no keyword added, no local-only keyword sent, and no property
  named by any earlier answer;
* local simulations: an extra root key fails both schemas, and a 1501-character summary passes the
  projection and fails the contract, which is why the contract keeps deciding.

**It pins the capability profile, the projection, the projector and the tests by digest**, so a
change to any of them after this freeze is a new projection version, not an edit. The freeze commit
and its remote verification are recorded by the V7 packet, which is prepared only after them.

No provider, token-count or network request is made here.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import pathlib
import re
from typing import Any

from sros_llm_gateway.providers.anthropic_strict import (
    ANTHROPIC_STRICT_TOOL_PROFILE_V1,
    DISPOSITIONS,
    LOCAL_ONLY,
    PROVIDER_ENFORCED,
    REPRESENTED_IN_DESCRIPTION_AND_LOCAL_ONLY,
    STRICT_PROJECTOR_VERSION,
    STRICT_TOOL_FLAG,
    UNSUPPORTED_ARCHITECTURE_BLOCKER,
    canonical_json_sha256,
    project_strict_input_schema,
    strict_incompatibilities,
)
from sros_opportunity.output_constraints import (
    MUST_BE_EXPLICIT_IN_PROMPT,
    constraint_inventory,
    is_explicit,
)
from sros_opportunity.schema_validation import SUPPORTED_KEYWORDS, schema_violations
from sros_opportunity.second_opportunity_prompt_v1_5 import SECOND_OPPORTUNITY_SYSTEM_V1_5
from sros_opportunity.second_opportunity_schema_v1_2 import (
    EVIDENCE_BOUND_REASONING_SUMMARY_HARD_MAX,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"
SCRIPTS = ROOT / "infrastructure" / "scripts"
RECORD = DATA / "second-opportunity-provider-strict-projection-v1.json"
RECORD_MD = DATA / "second-opportunity-provider-strict-projection-v1.md"
FREEZE_GATE_V1_4 = SCRIPTS / "render_second_opportunity_semantic_gate_v1_4.py"

PROJECTOR_FILE = "packages/llm-gateway/python/sros_llm_gateway/providers/anthropic_strict.py"
TEST_FILES = (
    "packages/llm-gateway/python/tests/test_anthropic_strict.py",
    "packages/opportunity-engine/python/tests/test_second_opportunity_provider_strict_projection.py",
)

STRICT_PROJECTION_ID = "second-opportunity-provider-strict-input-schema@1.0.0"
RECORD_VERSION = "second-opportunity-provider-strict-projection-record@1.0.0"

#: The contract Mission 1.84.16 recorded, and the gate Mission 1.84.17 froze. Neither may move.
CANONICAL_SCHEMA_SHA256 = "7d67bad3df06691ba46a4dcc65cbf186bc5825a87719e985637aec68640e1b66"
SEMANTIC_GATE_V1_4_IMPLEMENTATION_SHA256 = (
    "eb03899bbf7cc56f51994679dc4514f5c3c7ef63f4b6126aeb19ff18ccb160bb"
)

#: The freeze. Written once the projection, the projector and the tests were final.
FROZEN_CAPABILITY_PROFILE_SHA256 = (
    "7f3ed84547d163c330d637f6a0171b527017399bb6738cdcccc55cad08b24313"
)
FROZEN_STRICT_PROJECTION_SHA256 = "87028f451205494a948e83740e73b9ca59ce3243f54e24c123b7cc2354c69783"
FROZEN_PROJECTOR_SHA256 = "4eef60b03ac48caf72e337af7e9e1ad07b05d3fe3d14412dfe7ce7287679f02e"
FROZEN_TEST_SHA256 = "fe4abd1cd6512ef70f237bb9ab5dbfc19a657bc5983436fe04ec6c21e0f115d9"

OPERATOR_DECISION = (
    "KEEP_OUTPUT_SCHEMA_V1_2_0_UNCHANGED",
    "KEEP_SEMANTIC_GATE_V1_4_0_UNCHANGED",
    "KEEP_PROMPT_V1_5_0_SEMANTICS_UNCHANGED",
    "KEEP_GENERATION_HEADROOM_4_OVER_5_UNCHANGED",
    "DO_NOT_REMOVE_ADDITIONAL_PROPERTIES_FALSE",
    "DO_NOT_ALLOW_UNKNOWN_FIELDS",
    "DO_NOT_POST_PROCESS_UNKNOWN_FIELDS_AWAY",
    "INVESTIGATE_AND_PREPARE_PROVIDER_STRICT_TOOL_USE",
    "USE_A_DETERMINISTIC_PROVIDER_STRICT_SCHEMA_PROJECTION_IF_REQUIRED",
    "KEEP_THE_FULL_LOCAL_SCHEMA_V1_2_0_AS_THE_AUTHORITATIVE_STAGE_5_CONTRACT",
)

#: The first-party pages, fetched once as the published markdown on 2026-09-13 (UTC). The pages
#: publish no version number; each is identified by its final URL, its retrieval instant and the
#: SHA-256 of the bytes retrieved.
DOCUMENTATION_EVIDENCE: tuple[dict[str, object], ...] = (
    {
        "id": "E01",
        "requested_url": "https://platform.claude.com/docs/en/build-with-claude/structured-outputs.md",
        "final_url": "https://platform.claude.com/docs/en/build-with-claude/structured-outputs.md",
        "redirected": False,
        "http_status": 200,
        "retrieved_at": "2026-09-13T20:12:13Z",
        "bytes": 110492,
        "sha256": "4e500fed30c759764ba06bcd96b9df7160ecb8e5e7611aae9bc229086e0b9204",
        "first_party": True,
    },
    {
        "id": "E02",
        "requested_url": (
            "https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use.md"
        ),
        "final_url": "https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use.md",
        "redirected": False,
        "http_status": 200,
        "retrieved_at": "2026-09-13T20:12:14Z",
        "bytes": 40202,
        "sha256": "96c6f3246a419d99bad3266755ca942160e56cbbc24fb4c84c0a6bc86eaaed9a",
        "first_party": True,
    },
    {
        "id": "E03",
        "requested_url": (
            "https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use.md"
        ),
        "final_url": "https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools.md",
        "redirected": True,
        "http_status": 200,
        "retrieved_at": "2026-09-13T20:12:14Z",
        "bytes": 37555,
        "sha256": "58d22e8fdeebaf5874019f7aa06bb2950423ef42c0c0043d6ee65a583c172f85",
        "first_party": True,
    },
    {
        "id": "E04",
        "requested_url": "https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview.md",
        "final_url": "https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview.md",
        "redirected": False,
        "http_status": 200,
        "retrieved_at": "2026-09-13T20:12:15Z",
        "bytes": 38176,
        "sha256": "87e737a50fa73fe6b55fad499a2b23f16e6c4e1fffad818197e0c112ecb5aae7",
        "first_party": True,
    },
)

DOCUMENTATION_FETCHES = {
    "requests": 8,
    "pages": 4,
    "failed": [],
    "third_party_sources": 0,
    "note": (
        "Each page was read twice: once to review it, and once by the script that recorded the "
        "rows above. Both reads of each page gave the same SHA-256. E03 was requested at the path "
        "the platform's own pages link to and redirected to define-tools; the redirect is recorded."
    ),
}

#: Each proposition, and the fragments of the retrieved bytes it rests on, located by line.
DOCUMENTED_PROPOSITIONS: dict[str, list[tuple[str, int, str]]] = {
    "STRICT_TOOL_USE_SUPPORTED": [
        ("E01", 9, "Supported models: `claude-fable-5-1`"),
        ("E01", 9, "`claude-sonnet-5`"),
        (
            "E01",
            16,
            "* **Strict tool use** (`strict: true`): Guarantee schema validation on tool names and inputs",
        ),
        ("E01", 10, "- Platforms: Claude API"),
    ],
    "NO_BETA_HEADER": [("E01", 21, "beta headers are no longer required")],
    "STRICT_FLAG_LOCATION": [
        (
            "E02",
            375,
            'Set `"strict": true` as a top-level property in your tool definition, alongside `name`, `description`, and `input_schema`.',
        ),
    ],
    "STRICT_TOOL_USE_GUARANTEES_INPUT_SCHEMA_COMPLIANCE": [
        ("E02", 364, "* Tool `input` strictly follows the `input_schema`"),
        (
            "E01",
            2906,
            "While structured outputs guarantee schema compliance in most cases, there are scenarios where the output may not match your schema:",
        ),
    ],
    "SUBSET_SHARED": [
        (
            "E01",
            2816,
            "Structured outputs support standard JSON Schema with some limitations. Both JSON outputs and strict tool use share these limitations.",
        ),
    ],
    "TYPES_SUPPORTED": [
        ("E01", 2819, "* All basic types: object, array, string, integer, number, boolean, null")
    ],
    "ENUM_SUPPORTED": [
        ("E01", 2820, "* `enum` (strings, numbers, bools, or nulls only - no complex types")
    ],
    "CONST_SUPPORTED": [("E01", 2821, "* `const`")],
    "REQUIRED_AND_ADDITIONAL_PROPERTIES_FALSE_SUPPORTED": [
        (
            "E01",
            2825,
            "* `required` and `additionalProperties` (must be set to `false` for objects)",
        ),
    ],
    "FORMATS_SUPPORTED": [
        (
            "E01",
            2826,
            "* String formats: `date-time`, `time`, `date`, `duration`, `email`, `hostname`, `uri`, `ipv4`, `ipv6`, `uuid`",
        ),
    ],
    "MIN_ITEMS_0_OR_1": [("E01", 2827, "* Array `minItems` (only values 0 and 1 supported)")],
    "STRING_LENGTH_NOT_SUPPORTED": [
        ("E01", 2835, "* String constraints (`minLength`, `maxLength`)")
    ],
    "ARRAY_MAX_ITEMS_NOT_SUPPORTED": [
        ("E01", 2836, "* Array constraints beyond `minItems` of 0 or 1")
    ],
    "NUMERICAL_NOT_SUPPORTED": [
        ("E01", 2834, "* Numerical constraints (such as `minimum`, `maximum`, `multipleOf`)")
    ],
    "ADDITIONAL_PROPERTIES_OTHER_THAN_FALSE_NOT_SUPPORTED": [
        ("E01", 2837, "* `additionalProperties` set to anything other than `false`"),
    ],
    "UNSUPPORTED_FEATURE_IS_A_400": [
        (
            "E01",
            2839,
            "If you use an unsupported feature, you'll receive a 400 error with details.",
        ),
    ],
    "PATTERN_PARTIAL": [
        ("E01", 2846, "* Quantifiers: `*`, `+`, `?`, simple `{n,m}` cases"),
        ("E01", 2855, "* Complex `{n,m}` quantifiers with large ranges"),
        (
            "E01",
            2857,
            "Simple regex patterns work well. Complex patterns may result in 400 errors.",
        ),
    ],
    "SDK_DESCRIPTION_TRANSFORMATION": [
        ("E01", 1387, "2. **Update descriptions** with constraint info"),
        (
            "E01",
            1390,
            "5. **Validate responses** against your original schema (with all constraints)",
        ),
    ],
    "ENUM_CAPITALIZATION_NOT_GUARANTEED": [
        (
            "E01",
            2927,
            "Structured outputs don't guarantee the capitalization of string `enum` and `const` values",
        ),
        ("E01", 2936, "This applies to both JSON outputs and strict tool use."),
    ],
    "REFUSAL_AND_MAX_TOKENS_MAY_NOT_MATCH": [
        (
            "E01",
            2915,
            "* The output may not match your schema because the refusal message takes precedence over schema constraints",
        ),
        ("E01", 2922, "* The output may be incomplete and not match your schema"),
    ],
    "COMPLEXITY_LIMITS": [
        ("E01", 2948, "| Strict tools per request    | 20    |"),
        ("E01", 2949, "| Optional parameters         | 24    |"),
        ("E01", 2950, "| Parameters with union types | 16    |"),
        (
            "E01",
            2960,
            'you\'ll receive a 400 error with the message "Schema is too complex for compilation."',
        ),
        ("E01", 2960, "**compilation timeout of 180 seconds**"),
    ],
    "FIRST_REQUEST_COMPILATION_LATENCY": [
        (
            "E01",
            2796,
            "* **First request latency:** The first time you use a specific schema, there is additional latency while the grammar compiles",
        ),
        (
            "E01",
            2798,
            "* **Automatic caching:** Compiled grammars are cached for 24 hours from last use",
        ),
    ],
    "INJECTED_FORMAT_PROMPT": [
        (
            "E01",
            2808,
            "When using structured outputs, Claude automatically receives an additional system prompt explaining the expected output format.",
        ),
    ],
    "SCHEMA_CACHED_24H": [
        (
            "E02",
            1120,
            "Tool schemas are temporarily cached for up to 24 hours since last use. Prompts and responses are not retained beyond the API response.",
        ),
    ],
    "FORCED_TOOL_USE_RESTRICTIONS": [
        ("E03", 557, "Not every model and setting supports forced tool use."),
        ("E03", 561, "| Manual [extended thinking]"),
        ("E03", 562, "| Claude Fable 5.1 and [Claude Mythos 5.1]"),
    ],
    "FORCED_TOOL_USE_WITH_STRICT": [
        ("E03", 867, 'combine `tool_choice: {"type": "any"}` with [strict tool use]'),
        (
            "E03",
            860,
            "Note that when you have `tool_choice` as `any` or `tool`, the API prefills the assistant message to force a tool to be used.",
        ),
    ],
    "OVERVIEW_STRICT": [
        (
            "E04",
            749,
            "Add `strict: true` to your custom tool definitions to ensure Claude's tool calls always match your schema exactly.",
        ),
    ],
}

#: What the documentation establishes, in the brief's own terms. Each value rests on the
#: propositions named beside it.
CAPABILITY_FINDINGS: dict[str, dict[str, object]] = {
    "STRICT_TOOL_USE_SUPPORTED": {
        "value": True,
        "scope": "claude-sonnet-5 on the Claude API",
        "rests_on": ["STRICT_TOOL_USE_SUPPORTED", "OVERVIEW_STRICT"],
    },
    "STRICT_TOOL_USE_GUARANTEES_INPUT_SCHEMA_COMPLIANCE": {
        "value": "WITHIN_THE_SUPPORTED_SUBSET_WITH_DOCUMENTED_EXCEPTIONS",
        "exceptions": [
            "a refusal (stop_reason refusal) may not match the schema",
            "an output cut at max_tokens may not match the schema",
            "the capitalization of enum and const values is not guaranteed",
        ],
        "rests_on": [
            "STRICT_TOOL_USE_GUARANTEES_INPUT_SCHEMA_COMPLIANCE",
            "REFUSAL_AND_MAX_TOKENS_MAY_NOT_MATCH",
            "ENUM_CAPITALIZATION_NOT_GUARANTEED",
        ],
    },
    "ADDITIONAL_PROPERTIES_FALSE_SUPPORTED": {
        "value": True,
        "note": "must be false for every object; any other value is not supported",
        "rests_on": [
            "REQUIRED_AND_ADDITIONAL_PROPERTIES_FALSE_SUPPORTED",
            "ADDITIONAL_PROPERTIES_OTHER_THAN_FALSE_NOT_SUPPORTED",
        ],
    },
    "REQUIRED_SUPPORTED": {
        "value": True,
        "rests_on": ["REQUIRED_AND_ADDITIONAL_PROPERTIES_FALSE_SUPPORTED"],
    },
    "STRING_MAX_LENGTH_SUPPORTED": {
        "value": False,
        "note": "minLength and maxLength are not supported; using one is a 400 error",
        "rests_on": ["STRING_LENGTH_NOT_SUPPORTED", "UNSUPPORTED_FEATURE_IS_A_400"],
    },
    "ARRAY_MAX_ITEMS_SUPPORTED": {
        "value": False,
        "note": "only minItems of 0 or 1 is supported",
        "rests_on": ["ARRAY_MAX_ITEMS_NOT_SUPPORTED", "MIN_ITEMS_0_OR_1"],
    },
    "PATTERN_SUPPORTED": {
        "value": "PARTIAL_DOCUMENTED_REGEX_SUBSET",
        "note": (
            "anchors, *, +, ?, character classes, ., \\d, \\w, \\s and groups are listed; simple "
            "{n,m} cases are supported and complex ones with large ranges are not, and neither is "
            "defined. A pattern carrying a counted quantifier is therefore not established as "
            "supported, and all three of the contract's patterns carry one"
        ),
        "rests_on": ["PATTERN_PARTIAL"],
    },
    "ENUM_SUPPORTED": {
        "value": True,
        "note": "string, number, boolean or null members; capitalization not guaranteed",
        "rests_on": ["ENUM_SUPPORTED", "ENUM_CAPITALIZATION_NOT_GUARANTEED"],
    },
    "CONST_SUPPORTED": {"value": True, "rests_on": ["CONST_SUPPORTED"]},
    "FORMAT_UUID_SUPPORTED": {"value": True, "rests_on": ["FORMATS_SUPPORTED"]},
    "BETA_HEADER_REQUIRED": {"value": False, "rests_on": ["NO_BETA_HEADER"]},
    "STRICT_FLAG_LOCATION": {
        "value": "TOOL_DEFINITION_TOP_LEVEL",
        "note": "beside name, description and input_schema, never inside input_schema",
        "rests_on": ["STRICT_FLAG_LOCATION"],
    },
    "FORCED_TOOL_CHOICE_COMPATIBLE": {
        "value": True,
        "note": (
            "forced tool_choice is restricted only under manual extended thinking and on Claude "
            "Fable 5.1 and Mythos 5.1; claude-sonnet-5 with thinking disabled is neither, and the "
            "documentation describes combining forced tool choice with strict tool use"
        ),
        "rests_on": ["FORCED_TOOL_USE_RESTRICTIONS", "FORCED_TOOL_USE_WITH_STRICT"],
    },
    "SYNCHRONOUS_MESSAGES_API_COMPATIBLE": {
        "value": True,
        "note": (
            "strict is a property of a tool definition in a Messages API request; the "
            "documentation's examples use POST https://api.anthropic.com/v1/messages"
        ),
        "rests_on": ["STRICT_FLAG_LOCATION", "STRICT_TOOL_USE_SUPPORTED"],
    },
    "COMMERCIAL_TERMS_ROUTE": {
        "value": "UNCHANGED",
        "note": (
            "strict mode is a request property on the route the provider register already "
            "approves, not a new route, a new product or a new data flow"
        ),
        "rests_on": [],
    },
}

#: What the documentation says could still go wrong, and what this repository does about it.
CAVEATS: tuple[dict[str, str], ...] = (
    {
        "caveat": "ENUM_CAPITALIZATION_NOT_GUARANTEED",
        "handling": "local stage 5 compares enum members exactly, so a case variant is refused",
    },
    {
        "caveat": "REFUSAL_OR_MAX_TOKENS_MAY_NOT_MATCH",
        "handling": "the completion is read from stop_reason before any parse, unchanged",
    },
    {
        "caveat": "INTERNAL_COMPLEXITY_LIMITS_NOT_VERIFIABLE_WITHOUT_A_PROVIDER_REQUEST",
        "handling": (
            "the explicit limits hold (1 strict tool, 0 optional parameters, 0 union types); the "
            "internal grammar-size limits are undocumented, and a schema too complex to compile is "
            "a 400 error the one approved request would spend"
        ),
    },
    {
        "caveat": "FIRST_REQUEST_COMPILATION_LATENCY_NOT_ESTABLISHED",
        "handling": (
            "the first request with a schema waits while its grammar compiles, for an undocumented "
            "time up to a 180-second compilation timeout; the 60-second request timeout is kept "
            "as frozen, so a long compilation would end the one call"
        ),
    },
    {
        "caveat": "INJECTED_FORMAT_PROMPT_TOKENS_NOT_ESTABLISHED",
        "handling": (
            "the documentation says structured outputs add a system prompt explaining the format; "
            "its size is not documented and it is not in the request body the estimate measures"
        ),
    },
    {
        "caveat": "TOOL_SCHEMA_CACHED_24_HOURS",
        "handling": (
            "the projected schema is cached by the provider for up to 24 hours; it carries no TED "
            "value, no identifier and no subject, which this gate checks"
        ),
    },
)

DESCRIPTION_POLICY = {
    "DESCRIPTION_TRANSFORMATION": "NOT_APPLIED",
    "why": (
        "the provider's SDKs can move removed constraints into descriptions; that is a client "
        "convenience, not an API requirement. Every removed bound on text the model composes is "
        "already stated in words by prompt v1.5.0, rendered from the same schema, so a description "
        "copy would be a second rendering of the same number. The contract's own descriptions are "
        "sent unchanged, and none is rewritten or weakened"
    ),
}

TERMINOLOGY = {
    "PROVIDER_STRICT_SUBSET_COMPLIANCE": (
        "what strict mode can guarantee: a tool input that satisfies the projected schema, within "
        "the documented exceptions"
    ),
    "FULL_CANONICAL_SCHEMA_COMPLIANCE": "LOCAL_STAGE_5_ONLY",
    "not_claimed": "strict mode does not guarantee output schema v1.2.0",
}

WHAT_THE_PROJECTION_IS_NOT = (
    "a successor output contract",
    "a weaker replacement for stage 5",
    "a persistence contract",
    "a semantic gate",
    "authority to discard an unsupported constraint",
)

#: A synthetic answer built from the contract's own vocabularies. It is not V6's answer and reads
#: nothing from any execution. The ids carry hex letters, so an uppercase variant differs.
SYNTHETIC_UUIDS = ("0000000a-0000-4000-8000-00000000000a", "0000000b-0000-4000-8000-00000000000b")


class ValidationError(Exception):
    """The committed projection record disagrees with what the code derives, or with its freeze."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(relative: str) -> str:
    return _sha((ROOT / relative).read_bytes())


def tests_sha256() -> str:
    """One digest over the test files, path and bytes, in a fixed order (gate 77's rule)."""
    return _sha("".join(f"{p}\x00{file_sha(p)}\n" for p in TEST_FILES).encode("utf-8"))


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------------------------ derivation


def projection() -> Any:
    return project_strict_input_schema(
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2, ANTHROPIC_STRICT_TOOL_PROFILE_V1
    )


def _nodes(schema: dict[str, Any], path: str = "<root>") -> list[tuple[str, dict[str, Any]]]:
    out = [(path, schema)]
    if schema.get("type") == "object":
        for name, sub in schema.get("properties", {}).items():
            out.extend(_nodes(sub, name if path == "<root>" else f"{path}.{name}"))
    if schema.get("type") == "array" and isinstance(schema.get("items"), dict):
        out.extend(_nodes(schema["items"], f"{path}[]"))
    return out


def accounting(canonical: dict[str, Any], strict: Any) -> list[dict[str, object]]:
    """Every constraint of the repository's inventory, and what the projection did with it."""
    by_key: dict[tuple[str, str], list[Any]] = {}
    for row in strict.rows:
        by_key.setdefault((row.path, row.keyword), []).append(row)
    rows: list[dict[str, object]] = []
    for constraint in constraint_inventory(canonical):
        value = list(constraint.value) if isinstance(constraint.value, tuple) else constraint.value
        if constraint.keyword == "sentinel":
            matched = by_key.get((constraint.path, "description"), [])
            disposition = REPRESENTED_IN_DESCRIPTION_AND_LOCAL_ONLY
            projected: object = matched[0].projected_value if matched else None
            reason = (
                "the contract states the sentinel in a description and asserts nothing; the "
                "description is sent unchanged"
            )
        else:
            matched = by_key.get((constraint.path, constraint.keyword), [])
            if len(matched) != 1:
                raise ValidationError(
                    f"{constraint.path} {constraint.keyword}: {len(matched)} projection rows, not 1"
                )
            disposition = matched[0].disposition
            projected = matched[0].projected_value
            reason = matched[0].reason
        asserted = constraint.keyword in SUPPORTED_KEYWORDS - {"description", "format"}
        rows.append(
            {
                "path": constraint.path,
                "keyword": constraint.keyword,
                "canonical_value": value,
                "canonical_value_sha256": canonical_json_sha256(value),
                "disposition": disposition,
                "projected_value": projected,
                "local_enforcement": (
                    "LOCAL_STAGE_5_ASSERTS"
                    if asserted
                    else "NOT_A_SCHEMA_ASSERTION_IN_EITHER_SCHEMA"
                ),
                "prompt_states_it": is_explicit(constraint, SECOND_OPPORTUNITY_SYSTEM_V1_5),
                "constraint_class": constraint.constraint_class,
                "basis": reason,
            }
        )
    return rows


def structure(strict: Any) -> list[dict[str, object]]:
    return [
        row.to_json() | {"canonical_value": row.canonical_value}
        for row in strict.rows
        if row.keyword in ("properties", "items", "description")
    ]


def invariants(canonical: dict[str, Any], projected: dict[str, Any]) -> dict[str, object]:
    canon_nodes = dict(_nodes(canonical))
    proj_nodes = dict(_nodes(projected))
    objects = [p for p, n in canon_nodes.items() if n.get("type") == "object"]
    serialized = json.dumps(projected)
    return {
        "SAME_NODE_PATHS": list(canon_nodes) == list(proj_nodes),
        "ROOT_CANONICAL_PROPERTY_NAMES": list(canonical["properties"]),
        "ROOT_PROVIDER_STRICT_PROPERTY_NAMES": list(projected["properties"]),
        "ROOT_PROPERTY_SETS_EQUAL": list(canonical["properties"]) == list(projected["properties"]),
        "ROOT_PROPERTY_COUNT": len(projected["properties"]),
        "OBJECTS": len(objects),
        "EVERY_OBJECT_SAME_PROPERTY_NAMES": all(
            list(canon_nodes[p]["properties"]) == list(proj_nodes[p]["properties"]) for p in objects
        ),
        "EVERY_OBJECT_SAME_REQUIRED": all(
            canon_nodes[p].get("required") == proj_nodes[p].get("required") for p in objects
        ),
        "EVERY_OBJECT_ADDITIONAL_PROPERTIES_FALSE": all(
            proj_nodes[p].get("additionalProperties") is False for p in objects
        ),
        "SAME_TYPES": all(
            canon_nodes[p].get("type") == proj_nodes[p].get("type") for p in canon_nodes
        ),
        "SAME_ENUMS": all(
            canon_nodes[p].get("enum") == proj_nodes[p].get("enum") for p in canon_nodes
        ),
        "NO_KEYWORD_ADDED": all(set(proj_nodes[p]) <= set(canon_nodes[p]) for p in canon_nodes),
        "NO_LOCAL_ONLY_KEYWORD_SENT": strict_incompatibilities(
            projected, ANTHROPIC_STRICT_TOOL_PROFILE_V1
        )
        == [],
        "NO_PROPERTY_NAMED_BY_AN_EARLIER_ANSWER": "parameter name" not in serialized,
        "STRICT_FLAG_NOT_INSIDE_THE_SCHEMA": f'"{STRICT_TOOL_FLAG}"' not in serialized,
        "CARRIES_NO_IDENTIFIER_OR_SUBJECT": (
            re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-", serialized) is None
            and "ted-eu" not in serialized
            and "9261" not in serialized
        ),
    }


def synthetic_valid(canonical: dict[str, Any]) -> dict[str, Any]:
    props = canonical["properties"]
    dimensions = props["supported_dimensions"]["items"]["enum"]
    return {
        "decision": props["decision"]["enum"][0],
        "subject": "synthetic:subject",
        "target_actor_if_supported": "UNKNOWN_NOT_SUPPORTED",
        "observed_need": "A synthetic need.",
        "candidate_intervention_class": "A synthetic class.",
        "hypothesis_statement": "A synthetic hypothesis.",
        "supported_dimensions": [dimensions[0]],
        "unsupported_dimensions": [dimensions[1]],
        "supporting_evidence_ids": [SYNTHETIC_UUIDS[0]],
        "supporting_claim_ids": [SYNTHETIC_UUIDS[1]],
        "source_families": ["public_procurement"],
        "independence_status": "Synthetic.",
        "reliability_status": "Synthetic.",
        "evidence_bound_reasoning_summary": "A synthetic summary.",
        "critical_uncertainties": ["A synthetic uncertainty."],
        "commercial_claims_supported": [],
        "commercial_claims_not_supported": ["A synthetic claim."],
        "recommended_next_evidence": ["Synthetic evidence."],
        "confidence_classification": props["confidence_classification"]["enum"][0],
        "statement_classifications": [
            {
                "statement": "A synthetic statement.",
                "classification": props["statement_classifications"]["items"]["properties"][
                    "classification"
                ]["enum"][0],
            }
        ],
    }


def _variant(base: dict[str, Any], change: Any) -> dict[str, Any]:
    instance = copy.deepcopy(base)
    change(instance)
    return instance


def simulations(canonical: dict[str, Any], projected: dict[str, Any]) -> list[dict[str, object]]:
    """Each case, what strict decoding would accept (the projection) and what stage 5 decides."""
    base = synthetic_valid(canonical)
    hard = EVIDENCE_BOUND_REASONING_SUMMARY_HARD_MAX
    cases: list[tuple[str, Any, bool, bool]] = [
        ("a valid synthetic answer", lambda o: None, True, True),
        (
            "an extra root key, 'parameter name': 'value'",
            lambda o: o.update({"parameter name": "value"}),
            False,
            False,
        ),
        ("a required field missing", lambda o: o.pop("subject"), False, False),
        (
            "a wrong type",
            lambda o: o.update({"supported_dimensions": "MARKET_ACTIVITY"}),
            False,
            False,
        ),
        (
            "an enum member outside the vocabulary",
            lambda o: o.update({"decision": "MAYBE"}),
            False,
            False,
        ),
        (
            "an extra key inside a classified statement",
            lambda o: o["statement_classifications"][0].update({"note": "x"}),
            False,
            False,
        ),
        (
            f"a {hard}-character summary",
            lambda o: o.update({"evidence_bound_reasoning_summary": "s" * hard}),
            True,
            True,
        ),
        (
            f"a {hard + 1}-character summary",
            lambda o: o.update({"evidence_bound_reasoning_summary": "s" * (hard + 1)}),
            True,
            False,
        ),
        (
            "25 classified statements against maxItems 24",
            lambda o: o.update({"statement_classifications": o["statement_classifications"] * 25}),
            True,
            False,
        ),
        (
            "an empty uncertainty against minLength 1",
            lambda o: o.update({"critical_uncertainties": [""]}),
            True,
            False,
        ),
        (
            "a source family outside the slug grammar",
            lambda o: o.update({"source_families": ["Not A Slug"]}),
            True,
            False,
        ),
        (
            "an uppercase Evidence id against the lowercase pattern",
            lambda o: o.update({"supporting_evidence_ids": [SYNTHETIC_UUIDS[0].upper()]}),
            True,
            False,
        ),
    ]
    out: list[dict[str, object]] = []
    for name, change, projection_passes, canonical_passes in cases:
        instance = _variant(base, change)
        strict_violations = schema_violations(instance, projected)
        canonical_violations = schema_violations(instance, canonical)
        out.append(
            {
                "case": name,
                "projection_expected": "PASS" if projection_passes else "FAIL",
                "projection_observed": "FAIL" if strict_violations else "PASS",
                "canonical_expected": "PASS" if canonical_passes else "FAIL",
                "canonical_observed": "FAIL" if canonical_violations else "PASS",
                "canonical_violations": canonical_violations,
            }
        )
    return out


def _visible(row: dict[str, object]) -> bool:
    """Whether the model still sees this constraint: sent to the provider, or stated in the prompt."""
    return row["disposition"] == PROVIDER_ENFORCED or row["prompt_states_it"] is True


def build_record() -> dict[str, Any]:
    canonical = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2
    profile = ANTHROPIC_STRICT_TOOL_PROFILE_V1
    strict = projection()
    if not strict.ready:
        raise ValidationError(
            f"STRICT_TOOL_SCHEMA_PROJECTION_REQUIRES_ARCHITECTURE_DECISION: {strict.blockers}"
        )
    projected = strict.schema
    rows = accounting(canonical, strict)
    totals = {d: sum(1 for r in rows if r["disposition"] == d) for d in DISPOSITIONS[:4]}
    gate_v1_4 = _module("gate_87_for_gate_92", FREEZE_GATE_V1_4).implementation_sha256()
    return {
        "$comment": (
            "Mission 1.84.19. The provider-strict projection of output schema v1.2.0 and everything "
            "said about it, re-derived by CI gate 92. The contract keeps deciding stage 5 locally; "
            "this projection is what a strict tool would carry, and nothing more."
        ),
        "record_version": RECORD_VERSION,
        "mission": "1.84.19",
        "recorded_by": "mission-1.84.19",
        "recorded_on": "2026-09-14",
        "OPERATOR_DECISION": list(OPERATOR_DECISION),
        "DOCUMENTATION_EVIDENCE": [dict(row) for row in DOCUMENTATION_EVIDENCE],
        "DOCUMENTATION_FETCHES": DOCUMENTATION_FETCHES,
        "DOCUMENTED_PROPOSITIONS": {
            name: [{"evidence": e, "line": line, "verbatim": text} for e, line, text in fragments]
            for name, fragments in DOCUMENTED_PROPOSITIONS.items()
        },
        "CAPABILITY_FINDINGS": CAPABILITY_FINDINGS,
        "CAVEATS": list(CAVEATS),
        "CAPABILITY_PROFILE_ID": profile.profile_id,
        "CAPABILITY_PROFILE": profile.to_json(),
        "CAPABILITY_PROFILE_SHA256": canonical_json_sha256(profile.to_json()),
        "CANONICAL_OUTPUT_SCHEMA": {
            "id": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
            "sha256": canonical_json_sha256(canonical),
            "characters": len(json.dumps(canonical)),
            "authority": "decides stage 5 locally, unchanged",
        },
        "PROVIDER_STRICT_INPUT_SCHEMA": {
            "id": STRICT_PROJECTION_ID,
            "sha256": canonical_json_sha256(projected),
            "characters": len(json.dumps(projected)),
            "is_not": list(WHAT_THE_PROJECTION_IS_NOT),
            "schema": projected,
        },
        "PROJECTOR": {
            "version": STRICT_PROJECTOR_VERSION,
            "file": PROJECTOR_FILE,
            "implementation_sha256": file_sha(PROJECTOR_FILE),
            "inputs": ["the canonical schema", "the capability profile"],
            "reads": "no file, no model output, no execution record",
        },
        "TESTS": {"files": {p: file_sha(p) for p in TEST_FILES}, "sha256": tests_sha256()},
        "CONSTRAINT_ACCOUNTING": {
            "base": "sros_opportunity.output_constraints.constraint_inventory over schema v1.2.0",
            "constraints": len(rows),
            "totals": totals,
            "CANONICAL_CONSTRAINTS_ACCOUNTED_FOR": (
                "100_PERCENT" if sum(totals.values()) == len(rows) else "INCOMPLETE"
            ),
            "rows": rows,
        },
        "REMOVED_AND_NOT_STATED_IN_THE_PROMPT": {
            "count": len(unstated := [r for r in rows if not _visible(r)]),
            "rows": [
                {"path": r["path"], "keyword": r["keyword"], "class": r["constraint_class"]}
                for r in unstated
            ],
            "note": (
                "V6's tool schema carried these bounds; the strict tool schema does not, and the "
                "prompt states none of them, by the classification Mission 1.84.8 made of what the "
                "prompt must state. A class C bound cannot be exceeded by a duplicate-free answer "
                "drawn from a rendered vocabulary; a class D bound sits on a value the model "
                "copies; a class B pattern fixes the canonical form of a copied identifier, which "
                "the descriptions sent unchanged describe in words and format uuid still "
                "constrains for the two id arrays. Local stage 5 enforces every one of them "
                "unchanged"
            ),
        },
        "STRUCTURE_AND_ANNOTATIONS": structure(strict),
        "KEYWORD_OCCURRENCES": {d: strict.count(d) for d in DISPOSITIONS},
        "INVARIANTS": invariants(canonical, projected),
        "DESCRIPTION_POLICY": DESCRIPTION_POLICY,
        "COMPLEXITY": {
            "strict_tools": 1,
            "optional_parameters": strict.optional_parameters,
            "union_parameters": strict.union_parameters,
            "limits": {
                "strict_tools": profile.max_strict_tools,
                "optional_parameters": profile.max_optional_parameters,
                "union_parameters": profile.max_union_parameters,
            },
            "internal_limits": "NOT_VERIFIABLE_WITHOUT_A_PROVIDER_REQUEST",
        },
        "SIMULATIONS": simulations(canonical, projected),
        "SIMULATION_NOTE": (
            "The projection is simulated with the local validator, which treats format as an "
            "annotation; the provider documents enforcing uuid. Nothing here stands in for a "
            "provider request."
        ),
        "TERMINOLOGY": TERMINOLOGY,
        "UNCHANGED": {
            "OUTPUT_SCHEMA_CHANGED": canonical_json_sha256(canonical) != CANONICAL_SCHEMA_SHA256,
            "OUTPUT_SCHEMA_SHA256": canonical_json_sha256(canonical),
            "SEMANTIC_GATE_CHANGED": gate_v1_4 != SEMANTIC_GATE_V1_4_IMPLEMENTATION_SHA256,
            "SEMANTIC_GATE_IMPLEMENTATION_SHA256": gate_v1_4,
            "PERSISTENCE_CONTRACT_CHANGED": False,
            "PROMPT_SEMANTICS_CHANGED": False,
            "ADDITIONAL_PROPERTIES_FALSE_KEPT_IN_THE_CONTRACT": canonical["additionalProperties"]
            is False,
            "UNKNOWN_FIELDS_POST_PROCESSED": False,
            "REASONING_SUMMARY_HARD_MAX": EVIDENCE_BOUND_REASONING_SUMMARY_HARD_MAX,
        },
        "V6": {
            "replayed_through_the_projection": False,
            "note": (
                "V6's retained answer is evidence and is not run through this projection, repaired "
                "or reclassified. The synthetic extra-key case reproduces its shape, not its bytes"
            ),
        },
        "FREEZE": {
            "CAPABILITY_PROFILE_SHA256": FROZEN_CAPABILITY_PROFILE_SHA256,
            "STRICT_PROJECTION_SHA256": FROZEN_STRICT_PROJECTION_SHA256,
            "PROJECTOR_IMPLEMENTATION_SHA256": FROZEN_PROJECTOR_SHA256,
            "TEST_SHA256": FROZEN_TEST_SHA256,
            "commit": (
                "recorded by the V7 packet, which is prepared only after this freeze is committed, "
                "pushed and found on the remote"
            ),
        },
        "ACCOUNTING": {
            "MODEL_CALLS": 0,
            "PROVIDER_REQUESTS": 0,
            "MESSAGES_API_REQUESTS": 0,
            "TOKEN_COUNT_API_REQUESTS": 0,
            "TED_BYTES_SENT": 0,
            "CANONICAL_MUTATIONS": 0,
            "DOCUMENTATION_REQUESTS": DOCUMENTATION_FETCHES["requests"],
        },
    }


# ------------------------------------------------------------------------------ checking


def _check_invariants(record: dict[str, Any]) -> None:
    values = record["INVARIANTS"]
    for key, value in values.items():
        if isinstance(value, bool) and value is not True:
            raise ValidationError(f"invariant {key} does not hold")
    if values["ROOT_PROPERTY_COUNT"] != 20:
        raise ValidationError("the projected root does not carry exactly 20 properties")


def _check_accounting(record: dict[str, Any]) -> None:
    block = record["CONSTRAINT_ACCOUNTING"]
    if block["CANONICAL_CONSTRAINTS_ACCOUNTED_FOR"] != "100_PERCENT":
        raise ValidationError("a canonical constraint disappeared without a recorded disposition")
    if block["totals"].get(UNSUPPORTED_ARCHITECTURE_BLOCKER, 0):
        raise ValidationError("STRICT_TOOL_SCHEMA_PROJECTION_REQUIRES_ARCHITECTURE_DECISION")
    for row in block["rows"]:
        if row["disposition"] not in DISPOSITIONS[:4]:
            raise ValidationError(f"{row['path']} {row['keyword']}: no disposition")
        if row["disposition"] == LOCAL_ONLY and row["local_enforcement"] != "LOCAL_STAGE_5_ASSERTS":
            raise ValidationError(
                f"{row['path']} {row['keyword']} is not sent and is not enforced locally either"
            )
        if row["disposition"] == PROVIDER_ENFORCED and row["keyword"] in (
            "maxLength",
            "minLength",
            "maxItems",
        ):
            raise ValidationError(f"{row['path']} {row['keyword']} is claimed as provider-enforced")
        if (
            row["constraint_class"] == MUST_BE_EXPLICIT_IN_PROMPT
            and row["disposition"] != PROVIDER_ENFORCED
            and not row["prompt_states_it"]
        ):
            raise ValidationError(
                f"{row['path']} {row['keyword']} is neither enforced by the provider nor stated "
                "in the prompt"
            )


def _check_simulations(record: dict[str, Any]) -> None:
    for case in record["SIMULATIONS"]:
        if case["projection_expected"] != case["projection_observed"]:
            raise ValidationError(f"simulation {case['case']!r}: the projection disagrees")
        if case["canonical_expected"] != case["canonical_observed"]:
            raise ValidationError(f"simulation {case['case']!r}: stage 5 disagrees")
    stricter = [
        c
        for c in record["SIMULATIONS"]
        if c["projection_observed"] == "PASS" and c["canonical_observed"] == "FAIL"
    ]
    if not stricter:
        raise ValidationError("no case shows the contract stricter than the projection")


def _check_unchanged(record: dict[str, Any]) -> None:
    unchanged = record["UNCHANGED"]
    if unchanged["OUTPUT_SCHEMA_CHANGED"] or unchanged["SEMANTIC_GATE_CHANGED"]:
        raise ValidationError("the contract or the frozen gate moved")
    if record["TERMINOLOGY"]["FULL_CANONICAL_SCHEMA_COMPLIANCE"] != "LOCAL_STAGE_5_ONLY":
        raise ValidationError("full canonical compliance is attributed to the provider")


def _check_freeze(record: dict[str, Any]) -> None:
    live = {
        "CAPABILITY_PROFILE_SHA256": record["CAPABILITY_PROFILE_SHA256"],
        "STRICT_PROJECTION_SHA256": record["PROVIDER_STRICT_INPUT_SCHEMA"]["sha256"],
        "PROJECTOR_IMPLEMENTATION_SHA256": record["PROJECTOR"]["implementation_sha256"],
        "TEST_SHA256": record["TESTS"]["sha256"],
    }
    for key, value in live.items():
        if record["FREEZE"][key] != value:
            raise ValidationError(
                f"{key} is not the frozen one; a changed profile, projection, projector or test "
                "is a new projection version and needs a new freeze"
            )


def validate() -> dict[str, Any]:
    expected = json.loads(json.dumps(build_record()))
    _check_invariants(expected)
    _check_accounting(expected)
    _check_simulations(expected)
    _check_unchanged(expected)
    _check_freeze(expected)
    if not RECORD.exists():
        raise ValidationError(f"{RECORD.name} does not exist")
    committed = json.loads(RECORD.read_text(encoding="utf-8"))
    for key in sorted(set(expected) | set(committed)):
        if committed.get(key) != expected.get(key):
            raise ValidationError(f"{RECORD.name} {key} is not what the code derives")
    return committed


# ------------------------------------------------------------------------------ rendering


def render(record: dict[str, Any]) -> str:
    accounting_block = record["CONSTRAINT_ACCOUNTING"]
    lines = [
        "# Second Opportunity: provider-strict projection of output schema v1.2.0",
        "",
        "Generated by `infrastructure/scripts/render_second_opportunity_provider_strict_projection.py`"
        " (CI gate 92). Do not edit by hand.",
        "",
        "Mission 1.84.19. The contract keeps deciding stage 5 locally. This projection is what a "
        "strict tool would carry, and nothing more: "
        + "; ".join(record["PROVIDER_STRICT_INPUT_SCHEMA"]["is_not"])
        + " are all things it is not.",
        "",
        "## Identities",
        "",
        "```",
        f"canonical output schema   {record['CANONICAL_OUTPUT_SCHEMA']['id']}",
        f"                          {record['CANONICAL_OUTPUT_SCHEMA']['sha256']}",
        f"provider strict schema    {record['PROVIDER_STRICT_INPUT_SCHEMA']['id']}",
        f"                          {record['PROVIDER_STRICT_INPUT_SCHEMA']['sha256']}",
        f"capability profile        {record['CAPABILITY_PROFILE_ID']}",
        f"                          {record['CAPABILITY_PROFILE_SHA256']}",
        f"projector                 {record['PROJECTOR']['version']}",
        f"                          {record['PROJECTOR']['implementation_sha256']}",
        f"tests                     {record['TESTS']['sha256']}",
        f"semantic gate v1.4.0      {record['UNCHANGED']['SEMANTIC_GATE_IMPLEMENTATION_SHA256']}",
        "```",
        "",
        "## What the provider documents",
        "",
        "| finding | value |",
        "|---|---|",
    ]
    for name, finding in record["CAPABILITY_FINDINGS"].items():
        lines.append(f"| `{name}` | `{finding['value']}` |")
    lines += [
        "",
        "Every value rests on fragments quoted verbatim from the retrieved pages, located by line:",
        "",
        "| page | final URL | retrieved | SHA-256 |",
        "|---|---|---|---|",
    ]
    for row in record["DOCUMENTATION_EVIDENCE"]:
        lines.append(
            f"| {row['id']} | {row['final_url']} | {row['retrieved_at']} | `{row['sha256'][:16]}...` |"
        )
    lines += ["", "## The constraints, every one accounted for", ""]
    totals = accounting_block["totals"]
    lines += [
        f"{accounting_block['constraints']} constraints in the repository's inventory of schema "
        f"v1.2.0: {totals[PROVIDER_ENFORCED]} provider-enforced, {totals[LOCAL_ONLY]} local-only, "
        f"{totals[REPRESENTED_IN_DESCRIPTION_AND_LOCAL_ONLY]} carried in a description, "
        f"{totals[UNSUPPORTED_ARCHITECTURE_BLOCKER]} blockers. "
        f"`CANONICAL_CONSTRAINTS_ACCOUNTED_FOR = {accounting_block['CANONICAL_CONSTRAINTS_ACCOUNTED_FOR']}`.",
        "",
        "| path | keyword | canonical | disposition | local stage 5 | prompt states it |",
        "|---|---|---|---|---|---|",
    ]
    for row in accounting_block["rows"]:
        value = json.dumps(row["canonical_value"])
        if len(value) > 40:
            value = f"sha256 {row['canonical_value_sha256'][:12]}..."
        lines.append(
            f"| `{row['path']}` | {row['keyword']} | `{value}` | {row['disposition']} | "
            f"{row['local_enforcement']} | {'yes' if row['prompt_states_it'] else 'no'} |"
        )
    removed = record["REMOVED_AND_NOT_STATED_IN_THE_PROMPT"]
    lines += [
        "",
        "## What the model no longer sees",
        "",
        f"{removed['count']} bounds were visible in V6's tool schema and are neither sent to the "
        "provider nor stated in the prompt: "
        + ", ".join(f"`{r['path']}` {r['keyword']} ({r['class']})" for r in removed["rows"])
        + f". {removed['note']}.",
    ]
    lines += ["", "## Invariants", ""]
    for key, value in record["INVARIANTS"].items():
        if isinstance(value, int):
            lines.append(f"- `{key}` = `{value}`")
    lines += [
        "",
        "## Simulations",
        "",
        "| case | projection | stage 5 (canonical) |",
        "|---|---|---|",
    ]
    for case in record["SIMULATIONS"]:
        lines.append(
            f"| {case['case']} | {case['projection_observed']} | {case['canonical_observed']} |"
        )
    lines += ["", record["SIMULATION_NOTE"], "", "## Caveats", ""]
    for caveat in record["CAVEATS"]:
        lines.append(f"- **{caveat['caveat']}**: {caveat['handling']}.")
    lines += [
        "",
        "## Description policy",
        "",
        f"`DESCRIPTION_TRANSFORMATION = {record['DESCRIPTION_POLICY']['DESCRIPTION_TRANSFORMATION']}`: "
        f"{record['DESCRIPTION_POLICY']['why']}.",
        "",
        "## Terminology",
        "",
        f"`FULL_CANONICAL_SCHEMA_COMPLIANCE = {record['TERMINOLOGY']['FULL_CANONICAL_SCHEMA_COMPLIANCE']}`. "
        f"Strict mode gives `PROVIDER_STRICT_SUBSET_COMPLIANCE`: "
        f"{record['TERMINOLOGY']['PROVIDER_STRICT_SUBSET_COMPLIANCE']}.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        record = json.loads(json.dumps(build_record()))
        RECORD.write_bytes(
            (json.dumps(record, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        )
        RECORD_MD.write_bytes(render(record).encode("utf-8"))
        print(f"wrote {RECORD.name} and {RECORD_MD.name}")
        return 0
    try:
        record = validate()
    except ValidationError as exc:
        print(f"FAIL     {exc}")
        return 1
    if RECORD_MD.read_text(encoding="utf-8") != render(record):
        print(f"FAIL     {RECORD_MD.name} is not the rendering of its record")
        return 1
    print(
        "ok       the provider-strict projection is the frozen one, and schema v1.2.0 still decides"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
