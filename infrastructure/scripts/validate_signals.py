#!/usr/bin/env python3
"""The signal derivation boundary, enforced mechanically.

Mission 1.11.1 §5. Runs without a database. It parses `sros_nlp` and
`sros_signal_model` and fails when the deterministic boundary is crossed, so the
rule lives in CI rather than in someone's memory of a review.

Checked:
  1. Neither package imports a network client, a model, an embedder or a vector
     store -- by walking every IMPORT, not by grepping the text. A substring
     scan fails on the docstring that explains the rule, and weakening it until
     it passes is how a structural check stops checking
     (`testing-strategy.md` §23).
  2. `packages/signal-model` contains no extractor. It says what a Signal IS;
     deriving one is a different package, and the dependency runs one way.
  3. Neither package writes a table belonging to a LATER stage.
  4. No extractor names a conclusion. `trend`, `growth`, `momentum`, `demand`,
     `attention` and `sentiment` are readings of a number, not operations over
     it, and an extractor id carrying one would put the interpretation in the
     name (§3).
  5. The registered extractor ids match `signal_type` entries a migration wrote.

Stdlib only. Usage: python infrastructure/scripts/validate_signals.py
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
NLP = ROOT / "services/nlp/python/sros_nlp"
MODEL = ROOT / "packages/signal-model/python/sros_signal_model"
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

# Tables a signal extractor must never write. It derives a Signal and stops:
# Evidence needs a Claim to bear on, an embedding needs D-12 answered, and a
# score needs a CALIBRATED profile that does not exist.
FORBIDDEN_TABLES = (
    "nlp.embedding_provenance",
    "research.claims",
    "research.claim_revisions",
    "research.opportunities",
    "scoring.evidence",
    "scoring.evidence_independence_groups",
)

# Names that assert what a reader is supposed to CONCLUDE rather than what the
# extractor computes. `contrast` and `change` are operations; these are verdicts.
CONCLUSION_WORDS = (
    "trend",
    "growth",
    "momentum",
    "demand",
    "attention",
    "sentiment",
    "popularity",
    "interest",
    "pain",
    "desire",
    "topic",
)


def sources(package: pathlib.Path) -> list[pathlib.Path]:
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


def main() -> int:
    errors: list[str] = []
    checks = 0

    if not NLP.exists():
        print(f"FAIL  {NLP.relative_to(ROOT)} does not exist")
        return 1

    trees: dict[pathlib.Path, ast.AST] = {}
    for package in (NLP, MODEL):
        for path in sources(package):
            trees[path] = ast.parse(path.read_text(encoding="utf-8"))

    # -- 1: no network, no model, no embedder ------------------------------
    forbidden = NETWORK_MODULES | MODEL_MODULES | ML_MODULES
    for path, tree in trees.items():
        crossed = sorted(imported_roots(tree) & forbidden)
        if crossed:
            errors.append(
                f"{path.relative_to(ROOT)} imports {crossed}. Signal derivation is "
                "deterministic and offline: the same inputs, parameters and version must "
                "produce the same signal, which a model or a network call cannot promise"
            )
    print(
        f"ok    no network, model or embedding import ({len(trees)} module(s), "
        f"{len(forbidden)} names)"
    )
    checks += 1

    # -- 2: the model package contains no extractor ------------------------
    #
    # The distinction Mission 1.11 shipped and Mission 1.11.1 must not erode: the
    # model says what a Signal IS, and it is imported by whatever derives one.
    # An extractor living there would make the contract depend on an
    # implementation of itself.
    offenders = []
    for path, tree in trees.items():
        if MODEL not in path.parents and path.parent != MODEL:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.endswith("Extractor"):
                offenders.append(f"{path.relative_to(ROOT)}: {node.name}")
    if offenders:
        errors.append(
            f"packages/signal-model defines an extractor: {offenders}. It defines what a "
            "Signal IS; deriving one belongs to sros_nlp, and the dependency runs one way"
        )
    else:
        print("ok    packages/signal-model contains no extractor")
    checks += 1

    # -- 3: no later-stage table is written --------------------------------
    leaked: list[str] = []
    for path in trees:
        text = path.read_text(encoding="utf-8")
        for table in FORBIDDEN_TABLES:
            if re.search(rf"\b{re.escape(table)}\b", text):
                leaked.append(f"{path.relative_to(ROOT)}: {table}")
    if leaked:
        errors.append(
            f"signal derivation reaches a later stage's table: {leaked}. A Signal is not "
            "Evidence, not a Claim and not a Score; each needs something this layer does "
            "not have"
        )
    else:
        print(f"ok    no later-stage table written ({len(FORBIDDEN_TABLES)} checked)")
    checks += 1

    # -- 4: no extractor names a conclusion --------------------------------
    ids: set[str] = set()
    for path, tree in trees.items():
        if MODEL in path.parents:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for statement in node.body:
                if not isinstance(statement, ast.Assign):
                    continue
                names = [t.id for t in statement.targets if isinstance(t, ast.Name)]
                if "extractor_id" in names and isinstance(statement.value, ast.Constant):
                    ids.add(str(statement.value.value))
    if not ids:
        errors.append("no extractor_id was found: this check measured nothing")
    named = sorted(f"{i} ({word})" for i in ids for word in CONCLUSION_WORDS if word in i.lower())
    if named:
        errors.append(
            f"an extractor id names a conclusion: {named}. `contrast` and `change` are "
            "operations; trend, growth, demand and attention are readings of a number, "
            "and an id carrying one puts the interpretation in the name"
        )
    elif ids:
        print(f"ok    no extractor names a conclusion ({sorted(ids)})")
    checks += 1

    # -- 5: every registered extractor has a migration-written signal type --
    sql = "\n".join(p.read_text(encoding="utf-8") for p in sorted(MIGRATIONS.glob("*.sql")))
    registered = set(re.findall(r"'signal_type',\s*'([a-z0-9_]+)'", sql))
    declared: set[str] = set()
    for path, tree in trees.items():
        if MODEL in path.parents:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for statement in node.body:
                if not isinstance(statement, ast.Assign):
                    continue
                names = [t.id for t in statement.targets if isinstance(t, ast.Name)]
                if "signal_type_id" in names and isinstance(statement.value, ast.Constant):
                    declared.add(str(statement.value.value))
    missing = sorted(declared - registered)
    if missing:
        errors.append(
            f"extractor(s) declare signal type(s) no migration registers: {missing}. The "
            "foreign key would resolve only on a seeded database and fail on the empty "
            "one CI starts from"
        )
    else:
        print(f"ok    every declared signal type is registered by a migration ({sorted(declared)})")
    checks += 1

    print()
    if errors:
        print(f"SIGNAL BOUNDARY VALIDATION FAILED ({len(errors)} problem(s)):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"signal boundary validation passed: {checks} boundary groups")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
