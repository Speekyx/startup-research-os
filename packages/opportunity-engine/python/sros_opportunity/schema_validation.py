"""A deterministic structural validator for the synthesis output contracts.

**Why this exists at all.** `LlmGateway._validate_structured` checks that every `required` key is
PRESENT and stops there -- its own docstring says full JSON Schema validation "arrives with the
first real provider". So until Mission 1.84.4 nothing in this repository enforced a `maxLength`,
an `enum`, a `maxItems` or a `pattern` on a model's answer. Mission 1.84.4 bounds the output
contract, and a bound nobody checks is a sentence in a document rather than a constraint: the
provider is TOLD the schema and the provider decides what to do with it.

**No dependency was added.** `jsonschema` is not in this workspace and Mission 1.84.4 §21 forbids
installing an unreviewed package for a convenient answer. What is implemented here is exactly the
keyword set the two output schemas use, and `unsupported_keywords` names anything outside it, so a
future schema keyword cannot be silently ignored by a validator that looks like it checked.

**One authority.** This validates an instance AGAINST A SCHEMA OBJECT rather than against a copy of
the rules, so the schema constant stays the single place a bound is stated.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

__all__ = [
    "SUPPORTED_KEYWORDS",
    "schema_violations",
    "unsupported_keywords",
]

#: Every keyword this validator understands. A schema using anything else is reported by
#: `unsupported_keywords` rather than quietly accepted.
SUPPORTED_KEYWORDS: frozenset[str] = frozenset(
    {
        "type",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "maxItems",
        "minItems",
        "enum",
        "maxLength",
        "minLength",
        "pattern",
        # Annotations. `format` is an ANNOTATION in JSON Schema rather than an assertion, so a
        # schema relying on it for a bound is relying on the reader; every `format` in these
        # contracts sits beside a `pattern` that does the work. Listed here so
        # `unsupported_keywords` does not report them as an unchecked constraint.
        "description",
        "format",
    }
)


def unsupported_keywords(schema: Mapping[str, object], path: str = "") -> list[str]:
    """Every `path: keyword` this validator would ignore. Empty for the shipped contracts."""
    found: list[str] = []

    def walk(node: Mapping[str, object], here: str) -> None:
        for keyword in node:
            if keyword not in SUPPORTED_KEYWORDS:
                found.append(f"{here or '<root>'}: {keyword}")
        properties = node.get("properties")
        if isinstance(properties, Mapping):
            for name, sub in properties.items():
                if isinstance(sub, Mapping):
                    walk(sub, f"{here}.{name}" if here else str(name))
        items = node.get("items")
        if isinstance(items, Mapping):
            walk(items, f"{here}[]")

    walk(schema, path)
    return sorted(found)


def schema_violations(instance: object, schema: Mapping[str, object], path: str = "") -> list[str]:
    """Every way `instance` fails `schema`, in a deterministic order.

    Every violation is reported rather than the first, because a caller told only the first
    failure fixes it and is refused again -- the same reasoning ADR-033 applies to its four gates.
    """
    where = path or "<root>"
    kind = schema.get("type")

    if kind == "object":
        if not isinstance(instance, Mapping):
            return [f"{where}: expected an object, got {type(instance).__name__}"]
        return _object_violations(instance, schema, path, where)

    if kind == "array":
        if isinstance(instance, (str, bytes)) or not isinstance(instance, Sequence):
            return [f"{where}: expected an array, got {type(instance).__name__}"]
        return _array_violations(instance, schema, path, where)

    if kind == "string":
        if not isinstance(instance, str):
            return [f"{where}: expected a string, got {type(instance).__name__}"]
        return _string_violations(instance, schema, where)

    return [f"{where}: this validator does not understand type {kind!r}"]


def _object_violations(
    instance: Mapping[str, object], schema: Mapping[str, object], path: str, where: str
) -> list[str]:
    violations: list[str] = []
    properties = schema.get("properties")
    known = properties if isinstance(properties, Mapping) else {}

    required = schema.get("required")
    if isinstance(required, Sequence) and not isinstance(required, (str, bytes)):
        for name in required:
            if name not in instance:
                violations.append(f"{where}: missing required field {name!r}")

    if schema.get("additionalProperties") is False:
        for name in sorted(str(k) for k in instance):
            if name not in known:
                violations.append(f"{where}: unknown field {name!r}; additionalProperties is false")

    for name in sorted(str(k) for k in instance):
        sub = known.get(name)
        if isinstance(sub, Mapping):
            child = f"{path}.{name}" if path else name
            violations.extend(schema_violations(instance[name], sub, child))
    return violations


def _array_violations(
    instance: Sequence[object], schema: Mapping[str, object], path: str, where: str
) -> list[str]:
    violations: list[str] = []
    max_items = schema.get("maxItems")
    if isinstance(max_items, int) and len(instance) > max_items:
        violations.append(f"{where}: {len(instance)} items exceeds maxItems {max_items}")
    min_items = schema.get("minItems")
    if isinstance(min_items, int) and len(instance) < min_items:
        violations.append(f"{where}: {len(instance)} items is below minItems {min_items}")
    items = schema.get("items")
    if isinstance(items, Mapping):
        for index, element in enumerate(instance):
            violations.extend(schema_violations(element, items, f"{path}[{index}]"))
    return violations


def _string_violations(instance: str, schema: Mapping[str, object], where: str) -> list[str]:
    violations: list[str] = []

    enum = schema.get("enum")
    if isinstance(enum, Sequence) and not isinstance(enum, (str, bytes)) and instance not in enum:
        violations.append(f"{where}: {instance!r} is not one of the {len(enum)} permitted values")

    # Length is counted in CHARACTERS, which is what JSON Schema's maxLength means and what the
    # capacity analysis measures. Bytes are a different number and are reported separately there.
    max_length = schema.get("maxLength")
    if isinstance(max_length, int) and len(instance) > max_length:
        violations.append(f"{where}: {len(instance)} characters exceeds maxLength {max_length}")

    min_length = schema.get("minLength")
    if isinstance(min_length, int) and len(instance) < min_length:
        violations.append(f"{where}: {len(instance)} characters is below minLength {min_length}")

    pattern = schema.get("pattern")
    if isinstance(pattern, str) and re.search(pattern, instance) is None:
        violations.append(f"{where}: {instance!r} does not match {pattern}")

    return violations
