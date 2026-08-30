#!/usr/bin/env python3
"""Mechanically enforce the Mission 1.6 normalization boundary.

Runs without a database and without an install (ADR-009 rationale: a check that
cannot run is a check that gets skipped). It reads the source tree and the
contract, and fails when a boundary is crossed -- so the rules live in CI rather
than in someone's memory of a review.

The rules being enforced are the ones a reviewer is least likely to catch,
because crossing them looks like ordinary work:

  1. No network client anywhere in the normalization package (§40).
  2. Not even the sanctioned one -- importing `collection/transport.py` is
     reaching the network through the door that was left open for a collector.
  3. No LLM gateway, no provider SDK (§41).
  4. No embedding, clustering or vector library (§42).
  5. No signal, claim or evidence table (§43, §44, §45).
  6. No aggregation-semantics field (D-03 stays blocked).
  7. The canonical vocabulary in the code matches the contract source of truth.
  8. The record kinds declared in code are the ones the migration seeds.
  9. Every entry in the reviewed geography map records its basis, and no
     aggregate carries a country code.
 10. A registered normalizer exists for every source in IMPLEMENTED_NORMALIZERS
     and for no other.
 11. No `float(` in the World Bank numeric acquisition path (Mission 1.6.1 §21).
 12. No test fixture points a destructive helper at a seeded workspace (§21).

Stdlib only. Usage: python infrastructure/scripts/validate_normalization.py
"""

from __future__ import annotations

import ast
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "services/acquisition/python/sros_acquisition/normalization"
CONTRACT = ROOT / "packages/contracts/schema/domain.v1.json"
MIGRATION = ROOT / "infrastructure/db/migrations/0009_normalized_record_canonical.sql"
GEOGRAPHY = ROOT / "docs/data/geography-mapping-v1.json"
CONFORMANCE = ROOT / "packages/contracts/conformance/cases.json"

# Reaching a network, by any of the names a Python module can use.
NETWORK_MODULES = {
    "httpx",
    "requests",
    "aiohttp",
    "urllib",
    "http",
    "socket",
    "ssl",
    "playwright",
    "selenium",
    "websockets",
}

# Reaching a model. §41: normalization is deterministic, and a model deciding a
# geography would make it neither deterministic nor reproducible.
MODEL_MODULES = {
    "sros_llm_gateway",
    "anthropic",
    "openai",
    "google",
    "cohere",
    "litellm",
}

# NLP, embeddings, clustering. D-12 is open (§42).
ML_MODULES = {
    "sentence_transformers",
    "torch",
    "transformers",
    "sklearn",
    "scipy",
    "hdbscan",
    "umap",
    "qdrant_client",
    "nltk",
    "spacy",
}

# Tables this layer must never write (§43, §44, §45).
FORBIDDEN_TABLES = (
    "nlp.signals",
    "nlp.embedding_provenance",
    "research.claims",
    "scoring.evidence",
)

# The vocabulary that must exist in the contract, and the module that must use
# it. A code path that invented its own strings would drift from the schema
# CHECK constraint and from the TypeScript side at the same time.
REQUIRED_ENUMS = (
    "NormalizedRecordQuality",
    "NormalizationQualityReason",
    "NormalizationErrorCode",
    "NormalizedPeriodType",
    "NormalizedGeographyKind",
    "NormalizedValueState",
    "NormalizedUnitState",
)


def _imported_roots(tree: ast.AST) -> set[str]:
    """Every top-level module name a file imports, however it imports it."""
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def _relative_targets(tree: ast.AST) -> set[str]:
    """Relative import targets, so `from ..collection.transport import X` is seen."""
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level:
            targets.add(node.module or "")
            targets.update(alias.name for alias in node.names)
    return targets


def check_imports(errors: list[str]) -> int:
    files = sorted(PACKAGE.glob("*.py"))
    if not files:
        errors.append(f"no normalization modules found under {PACKAGE}")
        return 0
    for path in files:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        roots = _imported_roots(tree)
        name = path.relative_to(ROOT).as_posix()

        for group, label, rule in (
            (NETWORK_MODULES, "a network client", "§40"),
            (MODEL_MODULES, "an LLM client", "§41"),
            (ML_MODULES, "an NLP or vector library", "§42"),
        ):
            crossed = sorted(roots & group)
            if crossed:
                errors.append(
                    f"{name}: imports {label} ({', '.join(crossed)}). Normalization {rule}: "
                    "everything it needs is already persisted"
                )

        # The narrower half. The blanket ban above would be satisfied by
        # importing the ONE file allowed to hold a client, and reaching the
        # network through the sanctioned door is still reaching the network.
        for target in _relative_targets(tree):
            if "transport" in target.lower():
                errors.append(
                    f"{name}: imports the transport ({target}). §40 forbids reaching a "
                    "network at all, including through collection/transport.py"
                )
    return len(files)


def check_tables(errors: list[str]) -> None:
    for path in sorted(PACKAGE.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        name = path.relative_to(ROOT).as_posix()
        for table in FORBIDDEN_TABLES:
            # A mention in prose is fine and is how the rule gets explained; a
            # mention inside a SQL string is the thing being forbidden.
            if re.search(rf'["\'][^"\']*{re.escape(table)}', source):
                errors.append(
                    f"{name}: references {table} in a string. Normalization creates no "
                    "signal, claim or evidence (§43, §44, §45)"
                )


def check_aggregation_leakage(errors: list[str]) -> None:
    forbidden = json.loads(CONFORMANCE.read_text(encoding="utf-8"))["forbidden_fields"]["names"]
    for path in sorted(PACKAGE.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        leaked = [f for f in forbidden if re.search(rf"\b{f}\b", source)]
        if leaked:
            errors.append(
                f"{path.relative_to(ROOT).as_posix()}: evidence-aggregation leakage "
                f"{leaked}. D-03 is resolved at the framework level only"
            )


def check_vocabulary(errors: list[str]) -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    declared = {e["name"] for e in contract["closed_enums"]}
    for enum in REQUIRED_ENUMS:
        if enum not in declared:
            errors.append(
                f"{enum} is used by normalization and is not in the contract source of "
                "truth. A vocabulary that lives only in Python drifts from the schema "
                "CHECK and from the TypeScript side at the same time"
            )

    registries = {r["name"] for r in contract["registries"]}
    if "normalization_record_kind" not in registries:
        errors.append(
            "normalization_record_kind is not a declared registry. Record kinds are "
            "registry rows, not a database enum (Ontology V2 §14.3)"
        )

    # The quality CHECK in the migration must match the contract exactly.
    quality = next(
        (e for e in contract["closed_enums"] if e["name"] == "NormalizedRecordQuality"), None
    )
    if quality is not None:
        expected = {v["value"] for v in quality["values"]}
        sql = MIGRATION.read_text(encoding="utf-8")
        match = re.search(r"CHECK \(quality IN \(([^)]*)\)", sql)
        if match is None:
            errors.append("migration 0009 declares no CHECK for `quality`")
        else:
            found = set(re.findall(r"'([A-Z_]+)'", match.group(1)))
            if found != expected:
                errors.append(
                    f"migration 0009 quality CHECK {sorted(found)} does not match "
                    f"NormalizedRecordQuality {sorted(expected)}"
                )


def check_record_kinds(errors: list[str]) -> None:
    """The kinds declared in code are the ones the migration seeds.

    Two hand-maintained copies of one fact drift, and the drift is discovered by
    whoever trusted the wrong one.
    """
    model = (PACKAGE / "model.py").read_text(encoding="utf-8")
    block = re.search(r"RECORD_KINDS: dict\[str, RecordKind\] = \{(.*?)\n\}", model, re.DOTALL)
    if block is None:
        errors.append("model.py declares no RECORD_KINDS table")
        return
    declared = set(re.findall(r'^\s{4}"([a-z0-9_]+)": RecordKind', block.group(1), re.MULTILINE))
    if not declared:
        errors.append("RECORD_KINDS is empty; a normalizer with no kind writes an unreadable row")
        return

    sql = MIGRATION.read_text(encoding="utf-8")
    seeded = set(re.findall(r"'normalization_record_kind', '([a-z0-9_]+)'", sql))
    if declared != seeded:
        errors.append(
            f"record kinds declared in code {sorted(declared)} do not match those seeded "
            f"by migration 0009 {sorted(seeded)}"
        )


def check_geography(errors: list[str]) -> int:
    payload = json.loads(GEOGRAPHY.read_text(encoding="utf-8"))
    total = 0
    for block in payload.get("schemes", []):
        for entry in block.get("entries", []):
            total += 1
            code = entry.get("source_code", "?")
            if not str(entry.get("basis", "")).strip():
                errors.append(
                    f"geography entry {code} records no basis. A classification that "
                    "cannot be re-verified is indistinguishable from a guess"
                )
            kind = entry.get("kind")
            canonical = entry.get("canonical_code")
            if kind == "COUNTRY" and not canonical:
                errors.append(f"geography entry {code}: a COUNTRY must carry a canonical code")
            if kind != "COUNTRY" and canonical:
                errors.append(
                    f"geography entry {code}: only a COUNTRY carries a canonical country "
                    "code. An aggregate with one is the 'World is a country' error §15 forbids"
                )
            if kind not in {"COUNTRY", "AGGREGATE", "UNKNOWN"}:
                errors.append(f"geography entry {code}: {kind!r} is not a NormalizedGeographyKind")
    return total


def check_registered_normalizers(errors: list[str]) -> list[str]:
    """The declared adapters, read from the source rather than imported.

    Zero-dependency: this script must run with nothing installed, so it parses
    the registration rather than executing it.
    """
    init = (PACKAGE / "__init__.py").read_text(encoding="utf-8")
    specs = re.findall(r'source_id="([a-z0-9-]+)",\s*\n\s*collector_id="([a-z0-9-]+)"', init)
    if not specs:
        errors.append("no normalizer is registered; supported_sources() would refuse everything")
    return [source for source, _ in specs]


# ------------------------------------------------------------ Mission 1.6.1

# The acquisition modules a source number passes through. A `float(` here is the
# defect `raw-numeric-precision-gap-analysis-v1.md` measured: it collapses `1`
# and `1.0` into one record, rounds integers past 2^53, and truncates beyond 17
# significant digits -- silently, and in a way that makes a real upstream
# revision persist as UNCHANGED.
NUMERIC_PATH = (
    "services/acquisition/python/sros_acquisition/collection/records.py",
    "services/acquisition/python/sros_acquisition/collection/world_bank.py",
)


def check_no_float_in_numeric_path(errors: list[str]) -> int:
    """§21. AST, not grep: `float(` appears in prose and in type annotations.

    What is forbidden is a CALL to `float` on the value path. `float | None` in
    an annotation is a different token and a grep would flag it; a comment
    explaining why float is avoided would flag too, which is how a check gets
    disabled by whoever documents the rule it enforces.
    """
    checked = 0
    for rel in NUMERIC_PATH:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"{rel}: missing from the numeric path")
            continue
        checked += 1
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "float"
            ):
                errors.append(
                    f"{rel}:{node.lineno}: calls float() on the acquisition numeric "
                    "path. Source values are parsed with parse_float=Decimal and stay "
                    "Decimal until canonical_number serialises them "
                    "(raw-numeric-precision-gap-analysis-v1.md)"
                )
    return checked


# Fixtures that create or destroy a workspace must go through the shared guard,
# which refuses the seeded ids. Checked structurally rather than by trusting the
# convention: a helper nobody calls protects nothing.
DESTRUCTIVE_FIXTURES = (
    "services/acquisition/python/tests/conftest.py",
    "services/gateway/python/tests/conftest.py",
)


def check_workspace_guard_is_wired(errors: list[str]) -> int:
    checked = 0
    for rel in DESTRUCTIVE_FIXTURES:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"{rel}: missing")
            continue
        checked += 1
        source = path.read_text(encoding="utf-8")
        if "workspace_guard" not in source:
            errors.append(
                f"{rel}: does not import the shared workspace guard. A conftest that "
                "creates or drops workspaces must refuse the seeded ones "
                "(docs/testing/test-data-isolation-audit-v1.md §5)"
            )
            continue
        if "disposable(" not in source:
            errors.append(
                f"{rel}: imports the guard and never calls disposable(). An unused "
                "guard is a comment"
            )
    return checked


def main() -> int:
    errors: list[str] = []

    modules = check_imports(errors)
    print(f"ok    no network, model or ML import in normalization ({modules} module(s))")

    check_tables(errors)
    print(f"ok    no signal, claim or evidence table ({len(FORBIDDEN_TABLES)} names checked)")

    check_aggregation_leakage(errors)
    print("ok    no evidence-aggregation field (D-03 stays blocked)")

    check_vocabulary(errors)
    print(f"ok    canonical vocabulary matches the contract ({len(REQUIRED_ENUMS)} enums)")

    check_record_kinds(errors)
    print("ok    record kinds in code match the ones the migration seeds")

    entries = check_geography(errors)
    print(f"ok    geography map: every entry has a basis, no aggregate is a country ({entries})")

    sources = check_registered_normalizers(errors)
    print(f"ok    registered normalizers: {', '.join(sources) or 'none'}")

    numeric = check_no_float_in_numeric_path(errors)
    print(f"ok    no float() on the acquisition numeric path ({numeric} module(s))")

    fixtures = check_workspace_guard_is_wired(errors)
    print(f"ok    destructive fixtures go through the workspace guard ({fixtures})")

    print()
    if errors:
        print(f"NORMALIZATION VALIDATION FAILED ({len(errors)} problem(s)):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("normalization validation passed: 9 boundary groups")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
