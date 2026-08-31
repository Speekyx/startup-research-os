#!/usr/bin/env python3
"""The claim interpretation boundary, enforced mechanically.

Mission 1.13.1. Runs without a database. It parses `sros_nlp.interpreters` and
`sros_claim_model` and fails when the interpretation boundary is crossed, so the
rule lives in CI rather than in someone's memory of a review.

Checked:
  1. Neither the interpreter package nor `packages/claim-model` imports a
     network client, a model, an embedder or a vector store -- by walking every
     IMPORT, not by grepping the text. A substring scan fails on the docstring
     that explains the rule, and weakening it until it passes is how a
     structural check stops checking (`testing-strategy.md` §23).
  2. `packages/claim-model` contains no template. It says what a Claim IS;
     rendering one is a different package, and the dependency runs one way.
  3. No interpreter constructs a claim type other than `OBSERVED`. Mission
     1.13.1 §5: structurally incapable, not merely defaulted.
  4. No template reads a canonical language tag. **H-30 is open**, so reading
     the mapping would assert one that does not exist (§26).
  5. No template reads a timezone-bearing period bound or converts one.
     **H-29 is open**, and a GDELT bucket is on no shared timeline (§25).
  6. `packages/claim-model` writes no table, and the interpreter writes no table
     belonging to a LATER stage -- no Opportunity, no score, no embedding.
  7. The interpreter's supported signal types are all registered by a migration.

Stdlib only. Usage: python infrastructure/scripts/validate_claims.py
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
INTERPRETERS = ROOT / "services/nlp/python/sros_nlp/interpreters"
CLAIM_JOB = ROOT / "services/nlp/python/sros_nlp/claim_job.py"
CLAIM_REPOSITORIES = ROOT / "services/nlp/python/sros_nlp/claim_repositories.py"
MODEL = ROOT / "packages/claim-model/python/sros_claim_model"
MIGRATIONS = ROOT / "infrastructure/db/migrations"

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

MODEL_MODULES = {
    "sros_llm_gateway",
    "anthropic",
    "openai",
    "google",
    "cohere",
    "litellm",
}

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

# Tables the interpretation layer must never write. A Claim precedes an
# Opportunity (ADR-024), so grouping claims into one is a later decision; an
# embedding needs D-12 answered; a score needs a CALIBRATED profile that does
# not exist.
FORBIDDEN_TABLES = (
    "nlp.embedding_provenance",
    "research.opportunities",
    "research.opportunity_session_observations",
    "scoring.opportunity_scores",
    "scoring.scores",
)

# Payload fields that would assert a reviewed mapping (H-30) or place an unzoned
# label on a timeline (H-29). Read as CALL ARGUMENTS or SUBSCRIPTS, never as
# text: the modules explain both rules in prose and must not fail for it.
FORBIDDEN_PAYLOAD_FIELDS = frozenset(
    {
        "canonical_tag",
        "canonical_scheme",
        # `period.start` / `period.end` are the canonical bounds. For a GDELT
        # record they are NAIVE wall-clock values whose frame is unestablished
        # (ADR-019), and a claim that named one would be stating a time.
        "observed_at",
    }
)

# Assigning or converting a timezone, by any of the names Python offers. Scoped
# to the templates: `claim_job.py` legitimately calls `datetime.now(UTC)` for a
# run timestamp, which is our clock and not a source label's frame.
TIMEZONE_CALLS = frozenset(
    {"astimezone", "utcnow", "utcfromtimestamp", "now", "today", "localtime", "fromtimestamp"}
)


def sources(package: pathlib.Path) -> list[pathlib.Path]:
    if package.is_file():
        return [package]
    return sorted(p for p in package.rglob("*.py") if "__pycache__" not in p.parts)


def imported_roots(tree: ast.AST) -> set[str]:
    """Every top-level module name this file imports.

    Walks the AST rather than scanning text, so a docstring naming a forbidden
    module cannot fail the check and a `getattr`-flavoured dodge cannot pass it.
    """
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def string_literals_in_calls(tree: ast.AST) -> list[tuple[int, str]]:
    """String constants passed to a call or used as a subscript key.

    Deliberately NOT every string in the file. `lineage_fact(signal, "language",
    "canonical_tag")` and `payload["canonical_tag"]` are reads; a sentence in a
    docstring saying the tag is never read is not.
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for argument in [*node.args, *(k.value for k in node.keywords)]:
                if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                    found.append((node.lineno, argument.value))
        elif (
            isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        ):
            found.append((node.lineno, node.slice.value))
    return found


def main() -> int:
    errors: list[str] = []
    checks = 0

    # -- 1. no network, no model, no embedder ---------------------------------
    for label, package in (
        ("sros_nlp.interpreters", INTERPRETERS),
        ("sros_claim_model", MODEL),
        ("claim_job.py", CLAIM_JOB),
        ("claim_repositories.py", CLAIM_REPOSITORIES),
    ):
        forbidden = NETWORK_MODULES | MODEL_MODULES | ML_MODULES
        for path in sources(package):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            crossed = imported_roots(tree) & forbidden
            if crossed:
                errors.append(f"{path.relative_to(ROOT)} imports {sorted(crossed)}")
        checks += 1
        print(f"ok    {label} reaches no network, model or embedder")

    # -- 2. the model package holds no template -------------------------------
    template_markers = 0
    for path in sources(MODEL):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.endswith("Template"):
                template_markers += 1
                errors.append(f"{path.relative_to(ROOT)} defines a template class {node.name}")
            if isinstance(node, ast.FunctionDef) and node.name.startswith("render"):
                template_markers += 1
                errors.append(f"{path.relative_to(ROOT)} defines a renderer {node.name}")
    checks += 1
    print(f"ok    packages/claim-model contains no template ({template_markers} found)")

    # -- 3. OBSERVED only, structurally ---------------------------------------
    other_types: list[str] = []
    for path in sources(INTERPRETERS):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "ClaimType"
                and node.attr != "OBSERVED"
            ):
                other_types.append(f"{path.relative_to(ROOT)}:{node.lineno} ClaimType.{node.attr}")
    errors.extend(other_types)
    checks += 1
    print("ok    no interpreter constructs a claim type other than OBSERVED")

    # -- 4 & 5. H-30 and H-29 -------------------------------------------------
    payload_reads: list[str] = []
    for path in sources(INTERPRETERS):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for line, literal in string_literals_in_calls(tree):
            if literal in FORBIDDEN_PAYLOAD_FIELDS:
                payload_reads.append(f"{path.relative_to(ROOT)}:{line} reads {literal!r}")
    errors.extend(payload_reads)
    checks += 1
    print(
        "ok    no template reads a canonical language tag or an instant "
        f"({sorted(FORBIDDEN_PAYLOAD_FIELDS)})"
    )

    timezone_calls: list[str] = []
    for path in sources(INTERPRETERS):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.attr if isinstance(node.func, ast.Attribute) else None
                if name in TIMEZONE_CALLS:
                    timezone_calls.append(f"{path.relative_to(ROOT)}:{node.lineno} .{name}()")
                if any(k.arg == "tzinfo" for k in node.keywords):
                    timezone_calls.append(f"{path.relative_to(ROOT)}:{node.lineno} tzinfo=")
    errors.extend(timezone_calls)
    checks += 1
    print("ok    no template converts a timezone or reads a clock (H-29)")

    # -- 6. no later-stage table ---------------------------------------------
    written: list[str] = []
    for package in (MODEL, INTERPRETERS, CLAIM_JOB, CLAIM_REPOSITORIES):
        for path in sources(package):
            text = path.read_text(encoding="utf-8")
            for table in FORBIDDEN_TABLES:
                if re.search(rf"\b(INSERT INTO|UPDATE|DELETE FROM)\s+{re.escape(table)}\b", text):
                    written.append(f"{path.relative_to(ROOT)} writes {table}")
    errors.extend(written)
    checks += 1
    print(f"ok    the interpretation layer writes no later-stage table ({len(FORBIDDEN_TABLES)})")

    # `packages/claim-model` writes NOTHING at all. It validates a draft; a
    # driver call in it would be the model reaching past its own boundary.
    model_sql: list[str] = []
    for path in sources(MODEL):
        text = path.read_text(encoding="utf-8")
        if re.search(r"\b(INSERT INTO|UPDATE\s+\w+\.\w+|DELETE FROM|SELECT\s+.+\bFROM)\b", text):
            model_sql.append(f"{path.relative_to(ROOT)} contains SQL")
    errors.extend(model_sql)
    checks += 1
    print("ok    packages/claim-model reaches no database")

    # -- 7. supported signal types are registered -----------------------------
    supported = _supported_signal_types()
    registered = _registered_signal_types()
    unregistered = sorted(set(supported) - registered)
    if unregistered:
        errors.append(f"the interpreter names signal types no migration registered: {unregistered}")
    checks += 1
    print(f"ok    every supported signal type is registered by a migration ({sorted(supported)})")

    print()
    if errors:
        for error in errors:
            print(f"FAIL  {error}")
        print(f"\nclaim interpretation boundary FAILED: {len(errors)} problem(s)")
        return 1
    print(f"claim interpretation boundary validation passed: {checks} boundary groups")
    return 0


def _supported_signal_types() -> tuple[str, ...]:
    """Read from the module's AST, so the validator needs no import path."""
    tree = ast.parse((INTERPRETERS / "observed_restatement.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "SUPPORTED_SIGNAL_TYPES"
            and isinstance(node.value, ast.Tuple)
        ):
            return tuple(
                e.value
                for e in node.value.elts
                if isinstance(e, ast.Constant) and isinstance(e.value, str)
            )
    return ()


def _registered_signal_types() -> set[str]:
    registered: set[str] = set()
    pattern = re.compile(r"\('signal_type',\s*'([a-z0-9_]+)'", re.IGNORECASE)
    for path in sorted(MIGRATIONS.glob("*.sql")):
        registered.update(pattern.findall(path.read_text(encoding="utf-8")))
    return registered


if __name__ == "__main__":
    sys.exit(main())
