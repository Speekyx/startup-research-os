"""Strict tool use for the Anthropic adapter, over the provider-supported subset of a schema.

Mission 1.84.19. Execution V6 came back finished and parsed, with every declared field present, and
was refused at stage 5 on one key its closed output contract does not declare. Nothing in the
request asked the provider to hold the tool input to its schema: the tool was forced, not strict.
The provider documents a stronger mode, `strict: true` on the tool definition, which constrains
sampling to schema-valid tool inputs (grammar-constrained sampling).

**Strict mode enforces a documented SUBSET of JSON Schema, not the output contract.** The provider
supports types, `required`, `additionalProperties: false`, `enum`, `const`, a list of string
formats and `minItems` of 0 or 1. It rejects `minLength`, `maxLength`, `maxItems` and every
numerical constraint with a 400 error, and supports regular expressions only in part. So the tool
schema a strict request carries cannot be the contract: it is a PROJECTION of the contract onto
what this capability profile says the provider enforces. The full contract keeps deciding stage 5,
locally, exactly as before.

    canonical output schema ----> authoritative local stage 5, unchanged
            |
            +--> project_strict_input_schema(canonical, profile)
                    |
                    +--> the tool's input_schema, with "strict": true beside it

**The projector is a pure function of the schema and the profile.** It reads no file, no model
output and no execution record, and it never adds a property, drops a required name, widens a type
or edits an enum. Every keyword occurrence gets exactly one disposition:

    PROVIDER_ENFORCED                           sent, and the provider documents enforcing it
    LOCAL_ONLY                                  not sent; the local validator still enforces it
    REPRESENTED_IN_DESCRIPTION_AND_LOCAL_ONLY   not a schema assertion; carried in a description
    UNSUPPORTED_ARCHITECTURE_BLOCKER            no faithful projection exists; nothing is built
    ANNOTATION_CARRIED_UNCHANGED                a description, which constrains nothing

The last is not a constraint class. It is listed so that every keyword is accounted for.

**No description is rewritten.** The provider's SDKs can move removed constraints into field
descriptions; that is a client convenience, not an API requirement, and this projector does not do
it. Where a removed bound matters to the text the model composes, the prompt already states it in
words, rendered from the same schema.

**A strict body is built only from a schema inside the subset.** `AnthropicStrictToolProvider`
refuses, before any body exists, a response schema that would send a keyword the profile does not
list as enforced. Adding `strict: true` to an arbitrary schema is therefore not expressible here.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ..types import LlmRequest, ProviderInvalidRequestError
from .anthropic import AnthropicProvider

__all__ = [
    "ANNOTATION_CARRIED_UNCHANGED",
    "ANTHROPIC_STRICT_TOOL_PROFILE_V1",
    "AnthropicStrictToolProvider",
    "DISPOSITIONS",
    "LOCAL_ONLY",
    "PROVIDER_ENFORCED",
    "REPRESENTED_IN_DESCRIPTION_AND_LOCAL_ONLY",
    "STRICT_PROJECTOR_VERSION",
    "STRICT_TOOL_FLAG",
    "UNSUPPORTED_ARCHITECTURE_BLOCKER",
    "ProjectionRow",
    "StrictProjection",
    "StrictToolCapabilityProfile",
    "canonical_json_sha256",
    "pattern_within_documented_subset",
    "project_strict_input_schema",
    "strict_incompatibilities",
]

STRICT_PROJECTOR_VERSION = "anthropic-strict-input-schema-projector@1.0.0"

#: The tool-definition property the provider reads, beside `name`, `description` and
#: `input_schema`, and never inside `input_schema`.
STRICT_TOOL_FLAG = "strict"

PROVIDER_ENFORCED = "PROVIDER_ENFORCED"
LOCAL_ONLY = "LOCAL_ONLY"
REPRESENTED_IN_DESCRIPTION_AND_LOCAL_ONLY = "REPRESENTED_IN_DESCRIPTION_AND_LOCAL_ONLY"
UNSUPPORTED_ARCHITECTURE_BLOCKER = "UNSUPPORTED_ARCHITECTURE_BLOCKER"
ANNOTATION_CARRIED_UNCHANGED = "ANNOTATION_CARRIED_UNCHANGED"

DISPOSITIONS: tuple[str, ...] = (
    PROVIDER_ENFORCED,
    LOCAL_ONLY,
    REPRESENTED_IN_DESCRIPTION_AND_LOCAL_ONLY,
    UNSUPPORTED_ARCHITECTURE_BLOCKER,
    ANNOTATION_CARRIED_UNCHANGED,
)

_ROOT = "<root>"


@dataclass(frozen=True)
class StrictToolCapabilityProfile:
    """What the reviewed provider documentation says strict tool use enforces, and nothing more.

    Every set here is a transcription of a documented list, and `basis` names the documented
    sentence each disposition rests on. A keyword absent from every set is not assumed supported:
    the projector refuses it.
    """

    profile_id: str
    reviewed_on: str
    documentation: tuple[str, ...]
    supported_types: frozenset[str]
    structural_keywords: frozenset[str]
    enforced_keywords: frozenset[str]
    annotation_keywords: frozenset[str]
    local_only_keywords: frozenset[str]
    supported_formats: frozenset[str]
    supported_min_items: frozenset[int]
    max_strict_tools: int
    max_optional_parameters: int
    max_union_parameters: int
    strict_flag_location: str
    beta_header_required: bool
    enum_capitalization_guaranteed: bool
    basis: tuple[tuple[str, str], ...]

    def basis_for(self, keyword: str) -> str:
        return dict(self.basis).get(keyword, "")

    def to_json(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "reviewed_on": self.reviewed_on,
            "documentation": list(self.documentation),
            "supported_types": sorted(self.supported_types),
            "structural_keywords": sorted(self.structural_keywords),
            "enforced_keywords": sorted(self.enforced_keywords),
            "annotation_keywords": sorted(self.annotation_keywords),
            "local_only_keywords": sorted(self.local_only_keywords),
            "supported_formats": sorted(self.supported_formats),
            "supported_min_items": sorted(self.supported_min_items),
            "max_strict_tools": self.max_strict_tools,
            "max_optional_parameters": self.max_optional_parameters,
            "max_union_parameters": self.max_union_parameters,
            "strict_flag_location": self.strict_flag_location,
            "beta_header_required": self.beta_header_required,
            "enum_capitalization_guaranteed": self.enum_capitalization_guaranteed,
            "basis": {keyword: text for keyword, text in self.basis},
        }


_STRUCTURED_OUTPUTS = "https://platform.claude.com/docs/en/build-with-claude/structured-outputs"
_STRICT_TOOL_USE = "https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use"

#: The profile Mission 1.84.19 reviewed, from the provider's own documentation retrieved on
#: 2026-09-13 (UTC).
ANTHROPIC_STRICT_TOOL_PROFILE_V1 = StrictToolCapabilityProfile(
    profile_id="anthropic-strict-tool-capability@1.0.0",
    reviewed_on="2026-09-13",
    documentation=(_STRUCTURED_OUTPUTS, _STRICT_TOOL_USE),
    supported_types=frozenset(
        {"object", "array", "string", "integer", "number", "boolean", "null"}
    ),
    structural_keywords=frozenset({"properties", "items"}),
    enforced_keywords=frozenset(
        {"type", "required", "additionalProperties", "enum", "const", "format", "minItems"}
    ),
    annotation_keywords=frozenset({"description"}),
    local_only_keywords=frozenset(
        {
            "maxLength",
            "minLength",
            "maxItems",
            "minimum",
            "maximum",
            "exclusiveMinimum",
            "exclusiveMaximum",
            "multipleOf",
        }
    ),
    supported_formats=frozenset(
        {
            "date-time",
            "time",
            "date",
            "duration",
            "email",
            "hostname",
            "uri",
            "ipv4",
            "ipv6",
            "uuid",
        }
    ),
    supported_min_items=frozenset({0, 1}),
    max_strict_tools=20,
    max_optional_parameters=24,
    max_union_parameters=16,
    strict_flag_location="TOOL_DEFINITION_TOP_LEVEL",
    beta_header_required=False,
    enum_capitalization_guaranteed=False,
    basis=(
        ("type", "All basic types: object, array, string, integer, number, boolean, null"),
        ("required", "`required` and `additionalProperties` (must be set to `false` for objects)"),
        (
            "additionalProperties",
            "`required` and `additionalProperties` (must be set to `false` for objects)",
        ),
        ("enum", "`enum` (strings, numbers, bools, or nulls only - no complex types"),
        ("const", "`const`"),
        (
            "format",
            "String formats: `date-time`, `time`, `date`, `duration`, `email`, `hostname`, `uri`, "
            "`ipv4`, `ipv6`, `uuid`",
        ),
        ("minItems", "Array `minItems` (only values 0 and 1 supported)"),
        ("maxLength", "String constraints (`minLength`, `maxLength`)"),
        ("minLength", "String constraints (`minLength`, `maxLength`)"),
        ("maxItems", "Array constraints beyond `minItems` of 0 or 1"),
        ("minimum", "Numerical constraints (such as `minimum`, `maximum`, `multipleOf`)"),
        ("maximum", "Numerical constraints (such as `minimum`, `maximum`, `multipleOf`)"),
        ("multipleOf", "Numerical constraints (such as `minimum`, `maximum`, `multipleOf`)"),
        (
            "pattern",
            "Quantifiers: `*`, `+`, `?`, simple `{n,m}` cases; NOT supported: Complex `{n,m}` "
            "quantifiers with large ranges",
        ),
        ("description", "a description constrains nothing and is sent unchanged"),
        ("properties", "an object's property set, sent exactly"),
        ("items", "an array's element schema, projected recursively"),
    ),
)


@dataclass(frozen=True)
class ProjectionRow:
    """One keyword occurrence of the canonical schema, and what the projection did with it."""

    path: str
    keyword: str
    canonical_value: Any
    disposition: str
    projected_value: Any
    reason: str

    def to_json(self) -> dict[str, object]:
        return {
            "path": self.path,
            "keyword": self.keyword,
            "canonical_value": self.canonical_value,
            "disposition": self.disposition,
            "projected_value": self.projected_value,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class StrictProjection:
    """The projected schema, every row that produced it, and anything that blocks it."""

    schema: dict[str, Any] | None
    rows: tuple[ProjectionRow, ...]
    blockers: tuple[str, ...]
    optional_parameters: int
    union_parameters: int

    @property
    def ready(self) -> bool:
        return self.schema is not None and not self.blockers

    def count(self, disposition: str) -> int:
        return sum(1 for row in self.rows if row.disposition == disposition)


def canonical_json_sha256(value: object) -> str:
    """The digest this repository gives a schema: sorted keys, default separators, UTF-8."""
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def pattern_within_documented_subset(pattern: str) -> tuple[bool, str]:
    """Whether a regular expression uses only the regex features the documentation lists.

    Listed: anchors, `*`, `+`, `?`, character classes, `.`, `\\d`, `\\w`, `\\s` and groups. A counted
    quantifier is documented only as "simple {n,m} cases" beside "complex {n,m} quantifiers with
    large ranges", and neither is defined, so a pattern carrying one is not established as
    supported. Alternation and `(?` constructs are not listed either.
    """
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "\\":
            following = pattern[index + 1 : index + 2]
            if following in ("d", "w", "s") or (following and not following.isalnum()):
                index += 2
                continue
            return False, f"the escape \\{following} is not among the documented regex features"
        if char == "{":
            return False, (
                "a counted quantifier: the documentation supports simple {n,m} cases and excludes "
                "complex ones with large ranges without defining either, so support is not "
                "established"
            )
        if char == "|":
            return False, "alternation is not among the documented regex features"
        if char == "(" and pattern[index + 1 : index + 2] == "?":
            return False, "a (? group construct is not among the documented regex features"
        if char == "[":
            close = _class_end(pattern, index)
            if close < 0:
                return False, "an unterminated character class"
            index = close + 1
            continue
        index += 1
    return True, "uses only documented regex features"


def _class_end(pattern: str, start: int) -> int:
    index = start + 1
    while index < len(pattern):
        if pattern[index] == "\\":
            index += 2
            continue
        if pattern[index] == "]":
            return index
        index += 1
    return -1


def _child(path: str, name: str) -> str:
    return name if path == _ROOT else f"{path}.{name}"


def _primitive(value: object) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _classify(
    keyword: str, value: object, node: Mapping[str, Any], profile: StrictToolCapabilityProfile
) -> tuple[str, str]:
    basis = profile.basis_for(keyword)
    if keyword in profile.annotation_keywords:
        return ANNOTATION_CARRIED_UNCHANGED, basis
    if keyword in profile.structural_keywords:
        if keyword == "items" and not isinstance(value, Mapping):
            return UNSUPPORTED_ARCHITECTURE_BLOCKER, "a tuple-form `items` is not projected"
        if keyword == "properties" and not isinstance(value, Mapping):
            return UNSUPPORTED_ARCHITECTURE_BLOCKER, "`properties` is not an object"
        return PROVIDER_ENFORCED, basis
    if keyword == "pattern":
        if not isinstance(value, str):
            return UNSUPPORTED_ARCHITECTURE_BLOCKER, "`pattern` is not a string"
        supported, reason = pattern_within_documented_subset(value)
        return (PROVIDER_ENFORCED if supported else LOCAL_ONLY), f"{reason}. Basis: {basis}"
    if keyword in profile.local_only_keywords:
        return LOCAL_ONLY, basis
    if keyword not in profile.enforced_keywords:
        return UNSUPPORTED_ARCHITECTURE_BLOCKER, (
            f"`{keyword}` is not in the reviewed profile, so it is neither sent nor dropped"
        )
    if keyword == "type":
        members = value if isinstance(value, list) else [value]
        if all(isinstance(m, str) and m in profile.supported_types for m in members):
            return PROVIDER_ENFORCED, basis
        return UNSUPPORTED_ARCHITECTURE_BLOCKER, f"type {value!r} is not a supported basic type"
    if keyword == "additionalProperties":
        if value is False:
            return PROVIDER_ENFORCED, basis
        return UNSUPPORTED_ARCHITECTURE_BLOCKER, (
            "an object that admits other properties has no strict projection that keeps its meaning"
        )
    if keyword == "required":
        if isinstance(value, list) and all(isinstance(m, str) for m in value):
            return PROVIDER_ENFORCED, basis
        return UNSUPPORTED_ARCHITECTURE_BLOCKER, "`required` is not a list of names"
    if keyword == "enum":
        if isinstance(value, list) and value and all(_primitive(m) for m in value):
            return PROVIDER_ENFORCED, basis
        return UNSUPPORTED_ARCHITECTURE_BLOCKER, "an enum with complex members is not supported"
    if keyword == "const":
        if _primitive(value):
            return PROVIDER_ENFORCED, basis
        return UNSUPPORTED_ARCHITECTURE_BLOCKER, "a complex const is not supported"
    if keyword == "format":
        if value in profile.supported_formats:
            return PROVIDER_ENFORCED, basis
        return LOCAL_ONLY, f"the format {value!r} is not in the documented list. Basis: {basis}"
    if keyword == "minItems":
        if value in profile.supported_min_items:
            return PROVIDER_ENFORCED, basis
        return LOCAL_ONLY, basis
    return UNSUPPORTED_ARCHITECTURE_BLOCKER, f"`{keyword}` has no projection rule"


def _project(
    node: Mapping[str, Any],
    path: str,
    profile: StrictToolCapabilityProfile,
    rows: list[ProjectionRow],
    blockers: list[str],
    counts: dict[str, int],
) -> dict[str, Any]:
    projected: dict[str, Any] = {}
    if node.get("type") == "object":
        if node.get("additionalProperties") is not False:
            blockers.append(f"{path}: an object whose additionalProperties is not false")
        properties = node.get("properties")
        required = node.get("required")
        names = list(properties) if isinstance(properties, Mapping) else []
        required_names = list(required) if isinstance(required, list) else []
        counts["optional"] += sum(1 for name in names if name not in required_names)
    if isinstance(node.get("type"), list):
        counts["union"] += 1
    for keyword, value in node.items():
        disposition, reason = _classify(keyword, value, node, profile)
        if disposition == UNSUPPORTED_ARCHITECTURE_BLOCKER:
            blockers.append(f"{path}: {keyword}: {reason}")
            rows.append(ProjectionRow(path, keyword, value, disposition, None, reason))
            continue
        if disposition == LOCAL_ONLY:
            rows.append(ProjectionRow(path, keyword, value, disposition, None, reason))
            continue
        if keyword == "properties":
            children = {
                str(name): _project(sub, _child(path, str(name)), profile, rows, blockers, counts)
                for name, sub in value.items()
            }
            projected[keyword] = children
            rows.append(
                ProjectionRow(path, keyword, list(value), disposition, list(children), reason)
            )
            continue
        if keyword == "items":
            projected[keyword] = _project(value, f"{path}[]", profile, rows, blockers, counts)
            rows.append(ProjectionRow(path, keyword, "<schema>", disposition, "<schema>", reason))
            continue
        copied = json.loads(json.dumps(value))
        projected[keyword] = copied
        rows.append(ProjectionRow(path, keyword, value, disposition, copied, reason))
    return projected


def project_strict_input_schema(
    schema: Mapping[str, Any], profile: StrictToolCapabilityProfile
) -> StrictProjection:
    """The provider-supported projection of `schema` under `profile`, and how every keyword fared.

    Pure: the result depends on the two arguments and on nothing else, and `schema` is not
    modified. Key order is the schema's own, minus what is not sent.
    """
    rows: list[ProjectionRow] = []
    blockers: list[str] = []
    counts = {"optional": 0, "union": 0}
    projected = _project(schema, _ROOT, profile, rows, blockers, counts)
    if counts["optional"] > profile.max_optional_parameters:
        blockers.append(
            f"{counts['optional']} optional parameters exceed the documented limit of "
            f"{profile.max_optional_parameters}"
        )
    if counts["union"] > profile.max_union_parameters:
        blockers.append(
            f"{counts['union']} union-typed parameters exceed the documented limit of "
            f"{profile.max_union_parameters}"
        )
    return StrictProjection(
        schema=None if blockers else projected,
        rows=tuple(rows),
        blockers=tuple(blockers),
        optional_parameters=counts["optional"],
        union_parameters=counts["union"],
    )


def strict_incompatibilities(
    schema: Mapping[str, Any], profile: StrictToolCapabilityProfile
) -> list[str]:
    """Why `schema` may not be sent as a strict tool's input_schema. Empty when it may.

    A schema may be sent only if projecting it changes nothing: every keyword is enforced by the
    provider or is an annotation, and the documented limits hold.
    """
    projection = project_strict_input_schema(schema, profile)
    problems = list(projection.blockers)
    problems.extend(
        f"{row.path}: {row.keyword} is {row.disposition} and would be sent anyway"
        for row in projection.rows
        if row.disposition == LOCAL_ONLY
    )
    if projection.schema is not None and projection.schema != dict(schema):
        problems.append("the schema is not its own strict projection")
    return problems


@dataclass
class AnthropicStrictToolProvider(AnthropicProvider):
    """The Anthropic adapter with `strict: true` on its one forced tool.

    Everything else is the parent's: the endpoint, the headers (no beta header), the forced
    `tool_choice`, the thinking control, response normalization and the completion reading of
    `stop_reason`. Strict mode changes what the provider may sample, not how this adapter reads
    what came back.
    """

    capability_profile: StrictToolCapabilityProfile = ANTHROPIC_STRICT_TOOL_PROFILE_V1

    def build_body(self, request: LlmRequest, model: str) -> dict[str, Any]:
        if request.response_schema is None:
            raise ProviderInvalidRequestError(
                "strict tool use needs a tool, and this request carries no response schema",
                provider=self.name,
            )
        problems = strict_incompatibilities(request.response_schema, self.capability_profile)
        if problems:
            raise ProviderInvalidRequestError(
                "the response schema is not inside the reviewed strict subset "
                f"({self.capability_profile.profile_id}): " + "; ".join(problems),
                provider=self.name,
            )
        body = super().build_body(request, model)
        tools: Sequence[Mapping[str, Any]] = body["tools"]
        if len(tools) != 1:
            raise ProviderInvalidRequestError(
                "a strict synthesis request carries exactly one tool", provider=self.name
            )
        tool = tools[0]
        body["tools"] = [
            {
                "name": tool["name"],
                "description": tool["description"],
                STRICT_TOOL_FLAG: True,
                "input_schema": tool["input_schema"],
            }
        ]
        return body
