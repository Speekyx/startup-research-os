#!/usr/bin/env python3
"""Generate TypeScript and Python domain vocabulary from the contract source of truth.

Source of truth : packages/contracts/schema/domain.v1.json
Emits           : packages/contracts/src/generated/domain.ts
                  packages/contracts/python/sros_contracts/generated/domain.py
                  packages/contracts/schema/domain.v1.schema.json

Stdlib only, by design (ADR-009): the generator must run in CI with no install
step, so that a contract check can never be skipped because a dependency failed.

Usage:
    python tools/generate.py            # write
    python tools/generate.py --check    # verify committed output is current (CI)
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "schema" / "domain.v1.json"
TS_OUT = ROOT / "src" / "generated" / "domain.ts"
PY_OUT = ROOT / "python" / "sros_contracts" / "generated" / "domain.py"
JSONSCHEMA_OUT = ROOT / "schema" / "domain.v1.schema.json"

BANNER_LINES = [
    "DO NOT EDIT. GENERATED FILE.",
    "",
    "Source of truth : packages/contracts/schema/domain.v1.json",
    "Generator       : packages/contracts/tools/generate.py",
    "Regenerate      : python packages/contracts/tools/generate.py",
    "",
    "Editing this file by hand will be overwritten and will fail the contract",
    "check in CI. Change the source of truth instead.",
]


def load() -> dict:
    with SOURCE.open(encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- TS


def banner_ts(spec: dict) -> str:
    body = "\n".join(" * " + line if line else " *" for line in BANNER_LINES)
    return (
        "/* eslint-disable */\n"
        "/**\n"
        f"{body}\n"
        " *\n"
        f" * contract_version: {spec['contract_version']}\n"
        f" * ontology_version: {spec['ontology_version']}\n"
        " */\n"
    )


def gen_ts(spec: dict) -> str:
    out: list[str] = [banner_ts(spec), ""]

    out.append(f'export const CONTRACT_VERSION = "{spec["contract_version"]}" as const;')
    out.append(f'export const ONTOLOGY_VERSION = "{spec["ontology_version"]}" as const;')
    out.append(
        f"export const RESEARCH_CONTEXT_SCHEMA_VERSION = "
        f'"{spec["research_context"]["schema_version"]}" as const;'
    )
    out.append("")

    # Branded identifiers -----------------------------------------------------
    out.append("// --- Identifiers -----------------------------------------------------------")
    out.append("// Branded so that a WorkspaceId cannot be passed where an OpportunityId is")
    out.append("// expected. In a multi-tenant system that mix-up has a data-leak shape.")
    out.append("")
    out.append("declare const __brand: unique symbol;")
    out.append("type Brand<T, B extends string> = T & { readonly [__brand]: B };")
    out.append("")
    for ident in spec["identifiers"]:
        out.append(f"/** {ident['description']} (format: {ident['format']}) */")
        out.append(f'export type {ident["name"]} = Brand<string, "{ident["name"]}">;')
    out.append("")
    out.append("export const IDENTIFIER_FORMATS = {")
    for ident in spec["identifiers"]:
        out.append(f'  {ident["name"]}: "{ident["format"]}",')
    out.append("} as const;")
    out.append("")

    # Closed enums ------------------------------------------------------------
    out.append("// --- Closed enums ----------------------------------------------------------")
    out.append("// Changing any of these is a material semantic change: new ontology version,")
    out.append("// plus an ADR where architectural. Ontology V2 §14.2.")
    out.append("")
    for enum in spec["closed_enums"]:
        values = [v["value"] for v in enum["values"]]
        out.append("/**")
        out.append(f" * {enum['description']}")
        out.append(f" * @see {enum['spec']}")
        out.append(" */")
        out.append(f"export const {to_screaming(enum['name'])}_VALUES = [")
        for v in values:
            out.append(f'  "{v}",')
        out.append("] as const;")
        out.append(
            f"export type {enum['name']} = (typeof {to_screaming(enum['name'])}_VALUES)[number];"
        )
        out.append(
            f"export function is{enum['name']}(v: unknown): v is {enum['name']} {{\n"
            f'  return typeof v === "string" && '
            f"({to_screaming(enum['name'])}_VALUES as readonly string[]).includes(v);\n"
            f"}}"
        )
        out.append("")

    # Numeric bounds ----------------------------------------------------------
    out.append("// --- Numeric bounds --------------------------------------------------------")
    out.append("// A field named `confidence` is always [0,1]. A field named `*_score` is")
    out.append("// always 0-100. scoring-framework-v1.1.md §4.1.")
    out.append("")
    out.append("export const NUMERIC_BOUNDS = {")
    for n in spec["numeric_types"]:
        integer = "true" if n.get("integer") else "false"
        out.append(
            f"  {n['name']}: {{ min: {n['min']}, max: {n['max']}, "
            f'integer: {integer}, kind: "{n["kind"]}" }},'
        )
    out.append("} as const;")
    out.append("")
    out.append("export type NumericTypeName = keyof typeof NUMERIC_BOUNDS;")
    out.append("")

    # Registries --------------------------------------------------------------
    out.append("// --- Registry names --------------------------------------------------------")
    out.append("// These are EXTENSIBLE registries, not enums. Ontology V2 §14.3.")
    out.append("// This list names the registries; it never enumerates their entries.")
    out.append("")
    out.append("export const REGISTRY_NAMES = [")
    for r in spec["registries"]:
        out.append(f'  "{r["name"]}",')
    out.append("] as const;")
    out.append("export type RegistryName = (typeof REGISTRY_NAMES)[number];")
    out.append("")

    # MarketScope rules -------------------------------------------------------
    ms = spec["market_scope"]
    out.append("// --- MarketScope rules -----------------------------------------------------")
    out.append(f"// {ms['canonicalization']}")
    out.append("")
    out.append(f"export const COUNTRY_CODE_PATTERN = /{ms['country_code_pattern']}/;")
    out.append(
        "export const MARKET_SCOPE_RULES = "
        + json.dumps(ms["rules"], indent=2, sort_keys=True)
        + " as const;"
    )
    out.append("")

    return "\n".join(out).rstrip() + "\n"


def to_screaming(name: str) -> str:
    result: list[str] = []
    for index, char in enumerate(name):
        if char.isupper() and index > 0:
            result.append("_")
        result.append(char.upper())
    return "".join(result)


# --------------------------------------------------------------------------- PY


def gen_py(spec: dict) -> str:
    out: list[str] = ['"""']
    out.extend(BANNER_LINES)
    out.append("")
    out.append(f"contract_version: {spec['contract_version']}")
    out.append(f"ontology_version: {spec['ontology_version']}")
    out.append('"""')
    out.append("")
    out.append("from __future__ import annotations")
    out.append("")
    out.append("from enum import Enum")
    out.append("from typing import Final")
    out.append("")
    out.append(f'CONTRACT_VERSION: Final[str] = "{spec["contract_version"]}"')
    out.append(f'ONTOLOGY_VERSION: Final[str] = "{spec["ontology_version"]}"')
    out.append(
        "RESEARCH_CONTEXT_SCHEMA_VERSION: Final[str] = "
        f'"{spec["research_context"]["schema_version"]}"'
    )
    out.append("")
    out.append("")

    # Identifier formats ------------------------------------------------------
    out.append("# --- Identifiers -----------------------------------------------------------")
    out.append("# Python has no branded types. The identifier classes in sros_contracts.ids")
    out.append("# wrap these formats; this module only carries the generated vocabulary.")
    out.append("")
    out.append("IDENTIFIER_FORMATS: Final[dict[str, str]] = {")
    for ident in spec["identifiers"]:
        out.append(f'    "{ident["name"]}": "{ident["format"]}",')
    out.append("}")
    out.append("")
    out.append("")

    # Closed enums ------------------------------------------------------------
    out.append("# --- Closed enums ----------------------------------------------------------")
    out.append("# Changing any of these is a material semantic change: new ontology version,")
    out.append("# plus an ADR where architectural. Ontology V2 §14.2.")
    out.append("")
    for enum in spec["closed_enums"]:
        out.append("")
        out.append(f"class {enum['name']}(str, Enum):")
        out.append(f'    """{enum["description"]}')
        out.append("")
        out.append(f"    See {enum['spec']}.")
        out.append('    """')
        out.append("")
        for v in enum["values"]:
            out.append(f'    {v["value"]} = "{v["value"]}"  # {v["description"]}')
        out.append("")
    out.append("")

    # Numeric bounds ----------------------------------------------------------
    out.append("# --- Numeric bounds --------------------------------------------------------")
    out.append("# A field named `confidence` is always [0,1]. A field named `*_score` is")
    out.append("# always 0-100. scoring-framework-v1.1.md §4.1.")
    out.append("")
    out.append("NUMERIC_BOUNDS: Final[dict[str, dict[str, object]]] = {")
    for n in spec["numeric_types"]:
        out.append(
            f'    "{n["name"]}": {{"min": {n["min"]}, "max": {n["max"]}, '
            f'"integer": {bool(n.get("integer"))}, "kind": "{n["kind"]}"}},'
        )
    out.append("}")
    out.append("")
    out.append("")

    # Registries --------------------------------------------------------------
    out.append("# --- Registry names --------------------------------------------------------")
    out.append("# EXTENSIBLE registries, not enums. Ontology V2 §14.3.")
    out.append("# This tuple names the registries; it never enumerates their entries.")
    out.append("")
    out.append("REGISTRY_NAMES: Final[tuple[str, ...]] = (")
    for r in spec["registries"]:
        out.append(f'    "{r["name"]}",')
    out.append(")")
    out.append("")
    out.append("")

    # MarketScope rules -------------------------------------------------------
    ms = spec["market_scope"]
    out.append("# --- MarketScope rules -----------------------------------------------------")
    out.append(f"# {ms['canonicalization']}")
    out.append("")
    out.append(f'COUNTRY_CODE_PATTERN: Final[str] = r"{ms["country_code_pattern"]}"')
    out.append(f'COUNTRY_CODE_STANDARD: Final[str] = "{ms["country_code_standard"]}"')
    out.append("MARKET_SCOPE_RULES: Final[dict[str, dict[str, int]]] = {")
    for key in sorted(ms["rules"]):
        out.append(f'    "{key}": {json.dumps(ms["rules"][key], sort_keys=True)},')
    out.append("}")
    out.append("")

    return "\n".join(out)


# ------------------------------------------------------------------ JSON Schema


def gen_jsonschema(spec: dict) -> str:
    """A JSON Schema view of the vocabulary, for OpenAPI and cross-tool interop."""
    defs: dict = {}

    for ident in spec["identifiers"]:
        fmt = ident["format"]
        schema: dict = {"type": "string", "description": ident["description"]}
        if fmt == "uuid":
            schema["format"] = "uuid"
        elif fmt == "slug":
            schema["pattern"] = "^[a-z0-9][a-z0-9._-]{0,127}$"
        defs[ident["name"]] = schema

    for enum in spec["closed_enums"]:
        defs[enum["name"]] = {
            "type": "string",
            "enum": [v["value"] for v in enum["values"]],
            "description": enum["description"],
        }

    for n in spec["numeric_types"]:
        defs[n["name"]] = {
            "type": "integer" if n.get("integer") else "number",
            "minimum": n["min"],
            "maximum": n["max"],
            "description": n["description"],
        }

    ms = spec["market_scope"]
    country = {"type": "string", "pattern": ms["country_code_pattern"]}
    defs["MarketScope"] = {
        "description": "Geographic scope. See opportunity-ontology-v2.md §4.",
        "oneOf": [
            {
                "type": "object",
                "required": ["type"],
                "additionalProperties": False,
                "properties": {"type": {"const": "GLOBAL"}},
            },
            {
                "type": "object",
                "required": ["type", "regions"],
                "additionalProperties": False,
                "properties": {
                    "type": {"const": "REGION"},
                    "regions": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                },
            },
            {
                "type": "object",
                "required": ["type", "countries"],
                "additionalProperties": False,
                "properties": {
                    "type": {"const": "COUNTRY"},
                    "countries": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 1,
                        "items": country,
                    },
                },
            },
            {
                "type": "object",
                "required": ["type", "countries"],
                "additionalProperties": False,
                "properties": {
                    "type": {"const": "MULTI_COUNTRY"},
                    "countries": {"type": "array", "minItems": 2, "items": country},
                },
            },
        ],
    }

    defs["RegistryRef"] = {
        "type": "object",
        "required": ["registry", "id"],
        "additionalProperties": False,
        "description": "A reference into an extensible registry. Persists the stable id, never the display name.",
        "properties": {
            "registry": {"type": "string", "enum": [r["name"] for r in spec["registries"]]},
            "id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9._-]{0,127}$"},
        },
    }

    defs["RegistryEntry"] = {
        "type": "object",
        "required": ["registry", "id", "name", "version", "status"],
        "additionalProperties": False,
        "description": "Ontology V2 §14.4. Deprecation, never deletion.",
        "properties": {
            "registry": {"type": "string", "enum": [r["name"] for r in spec["registries"]]},
            "id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9._-]{0,127}$"},
            "name": {"type": "string"},
            "description": {"type": ["string", "null"]},
            "version": {"type": "integer", "minimum": 1},
            "status": {"$ref": "#/$defs/RegistryStatus"},
            "aliases": {"type": "array", "items": {"type": "string"}},
        },
    }

    rc_props: dict = {
        "schema_version": {"type": "string"},
        "market_scope": {"$ref": "#/$defs/MarketScope"},
    }
    for field in spec["research_context"]["fields"]:
        if field["name"] == "market_scope":
            continue
        rc_props[field["name"]] = {"description": field["type"]}
    defs["ResearchContext"] = {
        "type": "object",
        "required": ["schema_version", "market_scope"],
        "description": (
            "Value object, not an entity. Serialized as an immutable snapshot on a "
            "ResearchSession. Ontology V2 §11.3."
        ),
        "properties": rc_props,
    }

    doc = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://startup-research-os.local/schema/domain.v1.schema.json",
        "title": "Startup Research OS domain vocabulary",
        "description": (
            "GENERATED FILE. Source of truth: packages/contracts/schema/domain.v1.json. "
            "Regenerate with python packages/contracts/tools/generate.py."
        ),
        "x-contract-version": spec["contract_version"],
        "x-ontology-version": spec["ontology_version"],
        "$defs": dict(sorted(defs.items())),
    }
    return json.dumps(doc, indent=2, sort_keys=False, ensure_ascii=False) + "\n"


# --------------------------------------------------------------------------- IO


def write_or_check(path: pathlib.Path, content: str, check: bool) -> bool:
    """Return True when the file is already up to date."""
    if check:
        if not path.exists():
            print(f"MISSING  {path.relative_to(ROOT.parents[1])}")
            return False
        current = path.read_text(encoding="utf-8")
        if current != content:
            print(f"STALE    {path.relative_to(ROOT.parents[1])}")
            return False
        print(f"ok       {path.relative_to(ROOT.parents[1])}")
        return True

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"wrote    {path.relative_to(ROOT.parents[1])}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed generated files match the source of truth",
    )
    args = parser.parse_args()

    spec = load()
    results = [
        write_or_check(TS_OUT, gen_ts(spec), args.check),
        write_or_check(PY_OUT, gen_py(spec), args.check),
        write_or_check(JSONSCHEMA_OUT, gen_jsonschema(spec), args.check),
    ]

    if args.check and not all(results):
        print(
            "\nGenerated contracts are out of date.\n"
            "Run: python packages/contracts/tools/generate.py",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
