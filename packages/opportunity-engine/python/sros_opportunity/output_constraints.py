"""The output contract's generation-relevant constraints, rendered from the schema itself.

Mission 1.84.8. Under prompt v1.1.0 the one request Mission 1.84.7 made came back finished and was
refused by the v1.1.0 schema on one field: `evidence_bound_reasoning_summary` exceeded its
`maxLength`. The bound was real and enforced. It reached the model only inside the forced tool's
input schema, because the human-readable block v1.1.0 wrote BY HAND named two narrative bounds and
not this one. A hand-written list of limits is a second copy of the schema, and a second copy drifts.

**So the block is derived.** `render_output_constraints(schema)` reads the schema object it is
given and an explicit rendering policy, and nothing else: not a model output, not an execution
record, not the length any answer happened to have. Change a generation-relevant bound in a future
contract and the rendered text changes with it; a CI gate proves that by mutating the schema.

**Every constraint is classified, and the classification is computed from the schema.**

    A  MUST_BE_EXPLICIT_IN_PROMPT                         rendered
    B  PROVIDED_BY_TOOL_SCHEMA_AND_NOT_USEFUL_AS_PROSE     carried by the tool schema
    C  SEMANTICALLY_REDUNDANT_WITH_EXISTING_INSTRUCTION    another rendered line already bounds it
    D  INTERNAL_VALIDATOR_ONLY                             generation cannot control it

A bound on text the model COMPOSES is A: the model has to control that length or cardinality while
writing, and must not have to infer it from a tool schema. A bound on a value the model COPIES from
what it was given is D, because generation never chooses its length. Regex syntax is B: the block
says which supplied values to copy, and the tool schema carries their canonical form. A count that no
duplicate-free answer can exceed, because the items are drawn from a smaller rendered vocabulary, is
C. Nothing is classified to keep the prompt short.

**The prompt communicates; the validator decides.** Nothing here truncates, drops, rewrites,
splits or summarises an answer. An answer one character over a communicated bound is refused by
`schema_validation` exactly as it was before this module existed.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .schema_validation import SUPPORTED_KEYWORDS

__all__ = [
    "OUTPUT_CONSTRAINT_RENDERER_VERSION",
    "MUST_BE_EXPLICIT_IN_PROMPT",
    "PROVIDED_BY_TOOL_SCHEMA_AND_NOT_USEFUL_AS_PROSE",
    "SEMANTICALLY_REDUNDANT_WITH_EXISTING_INSTRUCTION",
    "INTERNAL_VALIDATOR_ONLY",
    "CONSTRAINT_CLASSES",
    "CONSTRAINT_CLASS_LETTERS",
    "CLASSIFICATION_POLICY",
    "OutputConstraint",
    "constraint_inventory",
    "render_output_constraints",
    "prompt_stanzas",
    "is_explicit",
    "mutated_schema",
]

OUTPUT_CONSTRAINT_RENDERER_VERSION = "output-constraint-renderer@1.0.0"

MUST_BE_EXPLICIT_IN_PROMPT = "MUST_BE_EXPLICIT_IN_PROMPT"
PROVIDED_BY_TOOL_SCHEMA_AND_NOT_USEFUL_AS_PROSE = "PROVIDED_BY_TOOL_SCHEMA_AND_NOT_USEFUL_AS_PROSE"
SEMANTICALLY_REDUNDANT_WITH_EXISTING_INSTRUCTION = (
    "SEMANTICALLY_REDUNDANT_WITH_EXISTING_INSTRUCTION"
)
INTERNAL_VALIDATOR_ONLY = "INTERNAL_VALIDATOR_ONLY"

CONSTRAINT_CLASSES: tuple[str, ...] = (
    MUST_BE_EXPLICIT_IN_PROMPT,
    PROVIDED_BY_TOOL_SCHEMA_AND_NOT_USEFUL_AS_PROSE,
    SEMANTICALLY_REDUNDANT_WITH_EXISTING_INSTRUCTION,
    INTERNAL_VALIDATOR_ONLY,
)
CONSTRAINT_CLASS_LETTERS: dict[str, str] = dict(zip("ABCD", CONSTRAINT_CLASSES, strict=True))

#: Why each kind of constraint lands where it does. Keyed by a rule name; every constraint in an
#: inventory names the rule that classified it, so a reader can argue with the rule rather than
#: with a thousand individual verdicts.
CLASSIFICATION_POLICY: dict[str, tuple[str, str]] = {
    "object_required": (
        MUST_BE_EXPLICIT_IN_PROMPT,
        "omitting a field fails validation, so the block states how many fields there are and that "
        "every one is required",
    ),
    "object_closed": (
        MUST_BE_EXPLICIT_IN_PROMPT,
        "a field outside the contract fails validation, so the block says no other field is allowed",
    ),
    "type": (
        PROVIDED_BY_TOOL_SCHEMA_AND_NOT_USEFUL_AS_PROSE,
        "the tool schema carries every field's JSON type, and the rendered wording (characters, "
        "elements, exactly one of) already presupposes it",
    ),
    "closed_choice": (
        MUST_BE_EXPLICIT_IN_PROMPT,
        "a closed choice whose selection carries meaning; the exact members are rendered",
    ),
    "composed_length": (
        MUST_BE_EXPLICIT_IN_PROMPT,
        "the model composes this text and has to control its length while writing it",
    ),
    "copied_length": (
        INTERNAL_VALIDATOR_ONLY,
        "the value is copied verbatim from what the packet supplies, so generation never chooses "
        "its length; the bound serves the capacity walker and the validator",
    ),
    "identity_grammar": (
        PROVIDED_BY_TOOL_SCHEMA_AND_NOT_USEFUL_AS_PROSE,
        "regex syntax is not useful prose: the block says which supplied values to copy verbatim, "
        "and the tool schema carries their canonical form",
    ),
    "annotation": (
        INTERNAL_VALIDATOR_ONLY,
        "an annotation the local validator does not assert; the pattern beside it does the work",
    ),
    "sentinel": (
        MUST_BE_EXPLICIT_IN_PROMPT,
        "the schema's own description names an exact string the answer must use when the field "
        "has no supported value; that is refusal behaviour, and it is rendered verbatim",
    ),
    "chosen_cardinality": (
        MUST_BE_EXPLICIT_IN_PROMPT,
        "the model chooses how many elements to write and can naturally write too many",
    ),
    "vocabulary_cardinality": (
        SEMANTICALLY_REDUNDANT_WITH_EXISTING_INSTRUCTION,
        "the items are drawn from a closed vocabulary no larger than this bound, and the vocabulary "
        "is rendered, so no duplicate-free answer can exceed it",
    ),
}

#: A description declaring an exact sentinel string, in the schema's own words.
_SENTINEL = re.compile(r"\bthe exact string ([A-Z][A-Z0-9_]+)\b")

#: A stanza header in a rendered block: two spaces, then one or more field names.
_STANZA_HEADER = re.compile(r"^  ([a-z][a-z0-9_]*(?:, [a-z][a-z0-9_]*)*)$")

#: A token that looks like a field name. A rendering note that names one must name a real field.
_FIELD_TOKEN = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")

_ROOT = "<root>"


@dataclass(frozen=True)
class OutputConstraint:
    """One generation-relevant constraint: where it is, what it says, and where it belongs."""

    path: str
    keyword: str
    value: Any
    rule: str

    @property
    def constraint_class(self) -> str:
        return CLASSIFICATION_POLICY[self.rule][0]

    @property
    def rationale(self) -> str:
        return CLASSIFICATION_POLICY[self.rule][1]

    def to_json(self) -> dict[str, object]:
        return {
            "path": self.path,
            "keyword": self.keyword,
            "value": list(self.value) if isinstance(self.value, tuple) else self.value,
            "rule": self.rule,
            "class": self.constraint_class,
        }


# ------------------------------------------------------------------------------ reading a schema


def _ordered_properties(node: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    """The schema's own order: its `required` list first, then any other property by name."""
    properties = node.get("properties")
    if not isinstance(properties, Mapping):
        return []
    required = [str(name) for name in node.get("required") or [] if name in properties]
    rest = sorted(str(name) for name in properties if name not in required)
    return [(name, properties[name]) for name in (*required, *rest)]


def _check_keywords(node: Mapping[str, Any], path: str) -> None:
    unknown = sorted(set(node) - SUPPORTED_KEYWORDS)
    if unknown:
        raise ValueError(
            f"{path}: {unknown} is not a keyword this renderer can classify, and a constraint it "
            "cannot classify is not rendered silently"
        )


def _kind(node: Mapping[str, Any]) -> str:
    kind = node.get("type")
    if kind == "string":
        if "enum" in node:
            return "CLOSED_CHOICE"
        if "pattern" in node:
            return "COPIED_IDENTIFIER"
        return "COMPOSED_TEXT"
    return str(kind).upper()


def _sentinel_of(node: Mapping[str, Any]) -> str | None:
    match = _SENTINEL.search(str(node.get("description") or ""))
    return match.group(1) if match else None


def _max_items_rule(node: Mapping[str, Any]) -> str:
    items = node.get("items")
    if (
        isinstance(items, Mapping)
        and _kind(items) == "CLOSED_CHOICE"
        and int(node["maxItems"]) >= len(items["enum"])
    ):
        return "vocabulary_cardinality"
    return "chosen_cardinality"


def _walk(node: Mapping[str, Any], path: str, out: list[OutputConstraint]) -> None:
    _check_keywords(node, path)
    kind = node.get("type")
    if "type" in node:
        out.append(OutputConstraint(path, "type", str(kind), "type"))

    if kind == "object":
        if "required" in node:
            out.append(
                OutputConstraint(path, "required", tuple(node["required"]), "object_required")
            )
        if node.get("additionalProperties") is False:
            out.append(OutputConstraint(path, "additionalProperties", False, "object_closed"))
        for name, sub in _ordered_properties(node):
            child = name if path == _ROOT else f"{path}.{name}"
            _walk(sub, child, out)
        return

    if kind == "array":
        if "minItems" in node:
            out.append(OutputConstraint(path, "minItems", node["minItems"], "chosen_cardinality"))
        if "maxItems" in node:
            out.append(OutputConstraint(path, "maxItems", node["maxItems"], _max_items_rule(node)))
        items = node.get("items")
        if isinstance(items, Mapping):
            _walk(items, f"{path}[]", out)
        return

    if kind == "string":
        copied = _kind(node) == "COPIED_IDENTIFIER"
        if "enum" in node:
            out.append(OutputConstraint(path, "enum", tuple(node["enum"]), "closed_choice"))
        for keyword in ("minLength", "maxLength"):
            if keyword in node:
                rule = "copied_length" if copied or "enum" in node else "composed_length"
                out.append(OutputConstraint(path, keyword, node[keyword], rule))
        if "pattern" in node:
            out.append(OutputConstraint(path, "pattern", node["pattern"], "identity_grammar"))
        if "format" in node:
            out.append(OutputConstraint(path, "format", node["format"], "annotation"))
        sentinel = _sentinel_of(node)
        if sentinel is not None:
            out.append(OutputConstraint(path, "sentinel", sentinel, "sentinel"))


def constraint_inventory(schema: Mapping[str, Any]) -> tuple[OutputConstraint, ...]:
    """Every constraint the schema states, classified, in the schema's own order."""
    out: list[OutputConstraint] = []
    _walk(schema, _ROOT, out)
    return tuple(out)


# ------------------------------------------------------------------------------ rendering


def _between(low: object, high: object, unit: str) -> str:
    if low is not None and high is not None:
        return f"from {low} to {high} {unit}"
    if high is not None:
        return f"at most {high} {unit}"
    if low is not None:
        return f"at least {low} {unit}"
    return ""


def _object_clause(node: Mapping[str, Any]) -> str:
    properties = _ordered_properties(node)
    required = [str(name) for name in node.get("required") or []]
    clause = f"exactly these {len(properties)} fields"
    if required and len(required) == len(properties):
        clause += ", every one required"
    elif required:
        clause += f", of which {len(required)} are required: {', '.join(required)}"
    if node.get("additionalProperties") is False:
        clause += ", and no other field"
    return clause


def _string_phrases(node: Mapping[str, Any]) -> list[str]:
    phrases: list[str] = []
    if "enum" in node:
        phrases.append("exactly one of: " + ", ".join(str(v) for v in node["enum"]))
    elif _kind(node) == "COMPOSED_TEXT":
        length = _between(node.get("minLength"), node.get("maxLength"), "characters")
        if length:
            phrases.append(length)
    if _sentinel_of(node) is not None:
        phrases.append(str(node["description"]))
    return phrases


def _array_lines(node: Mapping[str, Any]) -> list[str]:
    raw_items = node.get("items")
    items: Mapping[str, Any] = raw_items if isinstance(raw_items, Mapping) else {}
    high = (
        node.get("maxItems")
        if "maxItems" in node and _max_items_rule(node) == "chosen_cardinality"
        else None
    )
    parts = [_between(node.get("minItems"), high, "elements")]
    lines: list[str] = []
    kind = _kind(items)
    if kind == "CLOSED_CHOICE":
        lines.append("exactly these names, spelled exactly: " + ", ".join(items["enum"]))
    elif kind == "COMPOSED_TEXT":
        each = _between(items.get("minLength"), items.get("maxLength"), "characters")
        parts.append(f"each {each}" if each else "")
    elif kind == "OBJECT":
        parts.append(f"each an object with {_object_clause(items)}:")
        for name, sub in _ordered_properties(items):
            phrases = _string_phrases(sub) if sub.get("type") == "string" else []
            lines.append(f"  {name}: " + ("; ".join(phrases) or "no bound beyond its type"))
    first = ", ".join(part for part in parts if part)
    return ([first] if first else []) + lines


def _field_lines(node: Mapping[str, Any]) -> list[str]:
    kind = node.get("type")
    if kind == "array":
        return _array_lines(node)
    if kind == "string":
        return _string_phrases(node)
    if kind == "object":
        return [f"an object with {_object_clause(node)}"]
    return []


def _check_notes(schema: Mapping[str, Any], notes: Mapping[str, str]) -> None:
    fields = {name for name, _ in _ordered_properties(schema)}
    for name, note in notes.items():
        if name not in fields:
            raise ValueError(f"a rendering note names {name!r}, which the schema does not carry")
        if not str(note).strip():
            raise ValueError(f"the rendering note for {name!r} is empty")
        if re.search(r"\d", note):
            raise ValueError(
                f"the rendering note for {name!r} carries a digit. Every number the model is told "
                "comes from the schema, so a note cannot restate a bound and drift from it"
            )
        for token in _FIELD_TOKEN.findall(note):
            if token not in fields:
                raise ValueError(f"the rendering note for {name!r} names {token!r}, not a field")


def render_output_constraints(
    schema: Mapping[str, Any], notes: Mapping[str, str] | None = None
) -> str:
    """The generation-relevant constraints of `schema`, one stanza per field, deterministically.

    Fields follow the schema's `required` order; adjacent fields whose rendered lines are identical
    share one stanza. `notes` is per-field guidance that is not a limit, and may carry no digit.
    """
    guidance = dict(notes or {})
    _check_notes(schema, guidance)
    inventory = constraint_inventory(schema)
    if not any(c.path == _ROOT and c.keyword == "type" for c in inventory):
        raise ValueError("the schema's root declares no type")

    stanzas: list[tuple[list[str], list[str]]] = []
    for name, node in _ordered_properties(schema):
        lines = _field_lines(node) or ["no bound beyond its type, which the tool schema carries"]
        if name in guidance:
            lines = [*lines, guidance[name]]
        if stanzas and stanzas[-1][1] == lines:
            stanzas[-1][0].append(name)
        else:
            stanzas.append(([name], lines))

    out = [
        "Every limit below is read from the output schema the answer is validated against. "
        "Lengths are counted in characters.",
        "",
        f"The answer is one object with {_object_clause(schema)}.",
    ]
    for names, lines in stanzas:
        out.append("")
        out.append("  " + ", ".join(names))
        out.extend(f"    {line}" for line in lines)
    return "\n".join(out)


# ------------------------------------------------------------------------------ reading a prompt


def prompt_stanzas(text: str) -> dict[str, str]:
    """Field name -> the detail lines of the stanza that names it, from any rendered block.

    Works on the v1.1.0 hand-written block and on a derived one alike, which is what lets the same
    rule decide what each of them made explicit.
    """
    found: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in text.splitlines():
        header = _STANZA_HEADER.match(line)
        if header:
            current = []
            for name in header.group(1).split(", "):
                found.setdefault(name, current)
            continue
        if current is not None and line.startswith("    "):
            current.append(line.strip())
            continue
        if line.strip():
            current = None
    return {name: "\n".join(lines) for name, lines in found.items()}


def _scope(constraint: OutputConstraint, text: str) -> str | None:
    if constraint.path == _ROOT:
        return text
    field, _, rest = constraint.path.partition("[]")
    stanza = prompt_stanzas(text).get(field)
    if stanza is None or not rest:
        return stanza
    child = rest.lstrip(".")
    if not child:
        return stanza
    return next((line for line in stanza.splitlines() if line.startswith(f"{child}: ")), None)


def is_explicit(constraint: OutputConstraint, text: str) -> bool:
    """Whether `text` states `constraint` in words, by one rule for every prompt version."""
    keyword, value = constraint.keyword, constraint.value
    if keyword in ("enum", "sentinel"):
        members = value if isinstance(value, tuple) else (value,)
        return all(re.search(rf"\b{re.escape(str(m))}\b", text) for m in members)
    scope = _scope(constraint, text)
    if scope is None:
        return False
    if keyword == "required":
        count = f"exactly these {len(value)} fields"
        return count in scope and "every one required" in scope
    if keyword == "additionalProperties":
        return "no other field" in scope
    unit = "characters" if keyword in ("minLength", "maxLength") else "elements"
    if keyword in ("maxLength", "maxItems"):
        return re.search(rf"\b(?:at most|to) {value} {unit}\b", scope) is not None
    if keyword in ("minLength", "minItems"):
        pattern = rf"\b(?:at least {value}|from {value} to \d+) {unit}\b"
        return re.search(pattern, scope) is not None
    return False


# ------------------------------------------------------------------------------ the drift property


def _locate(schema: dict[str, Any], path: str) -> dict[str, Any]:
    node = schema
    if path == _ROOT:
        return node
    for segment in path.split("."):
        name = segment.removesuffix("[]")
        node = node["properties"][name]
        if segment.endswith("[]"):
            node = node["items"]
    return node


def mutated_schema(
    schema: Mapping[str, Any], constraint: OutputConstraint
) -> dict[str, Any] | None:
    """A copy of `schema` with exactly this constraint changed, or None where no honest change exists.

    Used to prove the drift property: every class-A mutation changes the rendered block, and a
    class-B, C or D mutation that keeps the constraint where it was does not.
    """
    copy: dict[str, Any] = deepcopy(dict(schema))
    node = _locate(copy, constraint.path)
    keyword = constraint.keyword
    if keyword in ("maxLength", "minLength", "maxItems", "minItems"):
        node[keyword] = int(node[keyword]) + 1
    elif keyword == "enum":
        node["enum"] = [*node["enum"], "MUTATED_MEMBER"]
    elif keyword == "required":
        node["required"] = list(node["required"])[:-1]
    elif keyword == "additionalProperties":
        node["additionalProperties"] = True
    elif keyword == "pattern":
        node["pattern"] = "^mutated$"
    elif keyword == "format":
        node["format"] = "mutated"
    elif keyword == "sentinel":
        node["description"] = str(node["description"]).replace(
            str(constraint.value), f"{constraint.value}_MUTATED"
        )
    else:
        return None
    return copy
