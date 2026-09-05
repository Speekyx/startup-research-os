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
  3. Every module under `sros_nlp` is classified as signal-layer or
     claim-layer. The package held one layer when this file was written and
     holds two since Mission 1.13.1, so the SUBJECT of check 3b had to be
     named -- and an unclassified module would be scanned by neither
     validator (`testing-strategy.md` §19).
  3b. The SIGNAL layer writes no table belonging to a LATER stage. The claim
     interpreter writes Claims and Evidence because that is what it is for,
     and `validate_claims.py` holds it to its own boundary.
  4. No extractor names a conclusion. `trend`, `growth`, `momentum`, `demand`,
     `attention` and `sentiment` are readings of a number, not operations over
     it, and an extractor id carrying one would put the interpretation in the
     name (§3).
  5. The registered extractor ids match `signal_type` entries a migration wrote.
  6. No EXTRACTOR converts a timezone or reads a clock. Mission 1.12.1 gave one
     of them datetime arithmetic over unzoned source labels, and the one place
     a UTC offset could enter the layer H-29 keeps clean is there.

Stdlib only. Usage: python infrastructure/scripts/validate_signals.py
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
NLP = ROOT / "services/nlp/python/sros_nlp"
EXTRACTORS = NLP / "extractors"
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
# `sros_nlp` held ONE layer when this file was written and holds TWO since
# Mission 1.13.1. The later-stage-table rule below is about the SIGNAL layer:
# an extractor must never write a Claim. The claim interpreter must, because
# writing one is what it is for.
#
# So the layers are named rather than the rule relaxed -- and the naming is
# EXHAUSTIVE. A new module under `sros_nlp` that belongs to neither list fails
# check 3a, so it has to be classified rather than silently escape the scan.
# An exclusion that grows by adding a file is not an exclusion.
SIGNAL_MODULES = frozenset(
    {
        "__init__.py",
        "observations.py",
        "repositories.py",
        "job.py",
    }
)
CLAIM_MODULES = frozenset(
    {
        "claim_job.py",
        "claim_repositories.py",
        # Mission 1.55. The deterministic-evaluation persistence orchestrator
        # belongs to the CLAIM layer: it writes Claims, revisions, Evidence,
        # derivations and refusals, and reads no normalized record. It is
        # classified here rather than left out because this guard's own rule is
        # that a module in neither list is checked by neither validator -- and it
        # caught this module the first time CI saw it.
        "inferred_persistence.py",
    }
)

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
# Assigning a timezone, by any of the names Python offers. Scoped to the
# EXTRACTORS: `job.py` legitimately calls `datetime.now(UTC)` for a derivation
# timestamp, which is our clock and not a source label's frame.
#
# H-29 is open. A GDELT bucket label is a wall-clock reading in a frame nobody
# has established, and Mission 1.12.1's adjacency check does arithmetic on one --
# in LABEL space, deliberately. A single `.astimezone()` or `tzinfo=` here would
# turn that into an instant, silently, in the field a consumer trusts most.
TIMEZONE_CALLS = frozenset(
    {"astimezone", "utcnow", "utcfromtimestamp", "now", "today", "localtime", "fromtimestamp"}
)

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


def is_signal_layer(path: pathlib.Path) -> bool:
    """Whether this module belongs to the SIGNAL layer of `sros_nlp`.

    Everything under `extractors/` is, plus the four top-level modules named
    above. `packages/signal-model` is too. The claim interpreter is not, and
    `validate_claims.py` holds it to its own boundary.
    """
    if MODEL in path.parents or path.parent == MODEL:
        return True
    if EXTRACTORS in path.parents or path.parent == EXTRACTORS:
        return True
    if path.parent == NLP:
        return path.name in SIGNAL_MODULES
    # A subpackage of sros_nlp that is not `extractors` -- `interpreters` today.
    return False


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

    # -- 3: every module under sros_nlp is CLASSIFIED ----------------------
    #
    # Before check 3b narrows to the signal layer, this makes the narrowing
    # honest: a module belonging to neither list is an unclassified module, and
    # an unclassified module would be scanned by nothing.
    unclassified = [
        path.relative_to(ROOT).as_posix()
        for path in trees
        if path.parent == NLP and path.name not in SIGNAL_MODULES | CLAIM_MODULES
    ]
    if unclassified:
        errors.append(
            f"{unclassified} belongs to neither SIGNAL_MODULES nor CLAIM_MODULES. "
            "`sros_nlp` holds two layers and each has its own boundary rules; a module "
            "in neither list is checked by neither validator"
        )
    else:
        print(
            f"ok    every sros_nlp module is classified "
            f"({len(SIGNAL_MODULES)} signal, {len(CLAIM_MODULES)} claim)"
        )
    checks += 1

    # -- 3b: no later-stage table is written by the SIGNAL layer -----------
    leaked: list[str] = []
    for path in trees:
        if not is_signal_layer(path):
            continue
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
        print(f"ok    no later-stage table written by the signal layer ({len(FORBIDDEN_TABLES)})")
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

    # -- 6: no extractor converts a timezone or reads a clock ---------------
    tz_offenders: list[str] = []
    for path, tree in trees.items():
        if EXTRACTORS not in path.parents:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in TIMEZONE_CALLS:
                tz_offenders.append(f"{path.relative_to(ROOT)}: .{node.attr}")
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == "tzinfo":
                        tz_offenders.append(f"{path.relative_to(ROOT)}: tzinfo=")
    if tz_offenders:
        errors.append(
            f"an extractor converts a timezone or reads a clock: {sorted(set(tz_offenders))}. "
            "H-29 is open: a GDELT bucket label is a wall-clock reading in a frame nobody "
            "has established, and an offset entering here would be invented"
        )
    else:
        print(
            f"ok    no extractor converts a timezone or reads a clock "
            f"({len(TIMEZONE_CALLS)} names, tzinfo= keyword)"
        )
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
