"""Mission 1.84.17, CI gate 87. The semantic output gate v1.4.0, frozen before it is a V6 dependency.

Gate v1.3.0 validates an answer's structure against output schema v1.1.0 inside its own evaluator,
which Mission 1.84.16 found when the operator moved the summary bound: whatever stage 5 admitted,
stage 6 enforced the old number again. The operator decided to create a successor bound to schema
v1.2.0 and to change nothing else. This gate makes that decision checkable:

* the freeze record is DERIVED from the live code, and must equal what the code derives now;
* the v1.4.0 implementation and its frozen test file are pinned by digest HERE, so a later `--write`
  cannot re-freeze a changed gate without an edit to this file that a reviewer sees;
* gate v1.3.0 still validates through CI gate 77, byte for byte its own freeze;
* v1.4.0's component identity differs from v1.3.0's in exactly the gate and the output schema;
* on a synthetic corpus (Mission 1.84.12's census fixtures, a sweep over every field of the schema,
  and the summary around both bounds) the two verdicts differ only where the one moved leaf explains;
* gate v1.3.0's own frozen test file, replayed through both gates by a spy, diverges nowhere;
* no historical answer is replayed through v1.4.0, and the V1 to V5 artifacts are the merged ones.

    uv run python infrastructure/scripts/render_second_opportunity_semantic_gate_v1_4.py --check
"""

from __future__ import annotations

import argparse
import ast
import functools
import hashlib
import importlib.util
import json
import pathlib
import re
from collections.abc import Mapping, Sequence
from typing import Any

from sros_opportunity.second_opportunity import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
)
from sros_opportunity.second_opportunity_gate_v1_2 import build_trusted_context
from sros_opportunity.second_opportunity_gate_v1_3 import (
    COMPONENT_VERSIONS_V1_3,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
    evaluate_second_opportunity_output_v1_3,
)
from sros_opportunity.second_opportunity_gate_v1_4 import (
    COMPONENT_VERSIONS_V1_4,
    OPERATOR_DECISION_V1_4,
    PREDECESSOR_GATE_VERSION,
    PREDECESSOR_STRUCTURAL_REASON_PREFIX,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_4,
    STRUCTURAL_REASON_PREFIX,
    evaluate_second_opportunity_output_v1_4,
)
from sros_opportunity.second_opportunity_schema_v1_2 import (
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
    output_schema_sha256,
    semantic_schema_diff,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
RECORD = DATA / "second-opportunity-output-gate-v1.4-freeze-v1.json"
RECORD_MD = DATA / "second-opportunity-output-gate-v1.4-freeze-v1.md"
GATE_77 = SCRIPTS / "render_second_opportunity_semantic_gate_v1_3.py"
GATE_79 = SCRIPTS / "render_second_opportunity_semantic_prompt_alignment.py"
FIXTURES = SCRIPTS / "second_opportunity_synthetic_fixtures.py"
DIFFERENTIAL = SCRIPTS / "second_opportunity_gate_differential.py"
SUITE = ROOT / "packages" / "opportunity-engine" / "python"
PACKAGE = "packages/opportunity-engine/python/sros_opportunity"
TESTS = "packages/opportunity-engine/python/tests"

MISSION = "mission-1.84.17"
SUCCESSOR_MODULE = f"{PACKAGE}/second_opportunity_gate_v1_4.py"
IMPLEMENTATION_FILES = (
    f"{PACKAGE}/lexical_inflection.py",
    f"{PACKAGE}/support_origin.py",
    f"{PACKAGE}/assertion_audit_v1_3.py",
    f"{PACKAGE}/second_opportunity_gate_v1_3.py",
    f"{PACKAGE}/second_opportunity_schema_v1_2.py",
    SUCCESSOR_MODULE,
)
TEST_FILE = f"{TESTS}/test_semantic_gate_v1_4.py"
PREDECESSOR_TEST_FILE = f"{TESTS}/test_semantic_gate_v1_3.py"
DIFFERENTIAL_FILE = "infrastructure/scripts/second_opportunity_gate_differential.py"

#: Pinned at the freeze. Editing either is re-freezing, and re-freezing is a new gate version.
FROZEN_IMPLEMENTATION_SHA256 = "eb03899bbf7cc56f51994679dc4514f5c3c7ef63f4b6126aeb19ff18ccb160bb"
FROZEN_TEST_SHA256 = "73796544b550a70f09b230b278e45280daebee6385f44d833d05dfb06998c4ab"

#: Gate v1.3.0 as CI gate 77 froze it, and the two schemas as Mission 1.84.16 recorded them.
PREDECESSOR_IMPLEMENTATION_SHA256 = (
    "cc3c490268e6f64a0b2107c2fb0c2fe6a1b1c71ab44c353419cd7d86c4485bf3"
)
PREDECESSOR_TEST_SHA256 = "6d7ad83150323293c78a998f9a880e6abd27e229a576b7b6f4d8fd6b940b80c3"
OUTPUT_SCHEMA_SHA256 = "7d67bad3df06691ba46a4dcc65cbf186bc5825a87719e985637aec68640e1b66"
PREDECESSOR_OUTPUT_SCHEMA_SHA256 = (
    "ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988"
)

REQUIRED_DECISION = (
    "CREATE_SEMANTIC_GATE_SUCCESSOR_BOUND_TO_OUTPUT_SCHEMA_V1_2_0 = true",
    "KEEP_SEMANTIC_GATE_V1_3_0_IMMUTABLE",
    "KEEP_ALL_NON_STRUCTURAL_SEMANTIC_BEHAVIOR_UNCHANGED",
    "USE_OUTPUT_SCHEMA_V1_2_0_AS_THE_V6_EXECUTION_CONTRACT",
    "DO_NOT_REVERT_TO_OUTPUT_SCHEMA_V1_1_0",
)
CHANGED_COMPONENTS = ("gate", "output_schema")
SUMMARY = "evidence_bound_reasoning_summary"
#: Gate 86's demonstration: the fixture's own summary repeated five times, so no word is new.
REPETITIONS = 5
#: A sentence the semantic gate refuses whatever the summary's length: no statement supplies it.
VIOLATION = " Buyers are willing to pay."

#: The execution history this mission must not touch (brief section 2), byte for byte as merged.
HISTORY_SHA256: dict[str, str] = {
    "docs/data/second-opportunity-synthesis-execution-packet-v1.json": (
        "7132fc35ab263b86bbe89016f84fd10e9ed54bcc7fb8b30d072e86279b472241"
    ),
    "docs/data/second-opportunity-synthesis-execution-packet-v2.json": (
        "5a2f5a7ea20c6de9d4f50498f304e59b6918db63e5ccc9814f988fd3d4f14871"
    ),
    "docs/data/second-opportunity-synthesis-execution-packet-v3.json": (
        "096eb1845e55a8792c4de7f07b35319de61b6e1af52bd9c4544bd2205533b130"
    ),
    "docs/data/second-opportunity-synthesis-execution-packet-v4.json": (
        "f398a0d13c4553c8cb212c40a7892bc90cf0b810538c7e7c989548f858490435"
    ),
    "docs/data/second-opportunity-synthesis-execution-packet-v5.json": (
        "18ff43c86f51b6f3afd23f897d2fb9c5e3312aa82eea4b8fec36b65857e359e0"
    ),
    "docs/data/second-opportunity-synthesis-execution-approval-v2.json": (
        "1885358d0b7fde8e95a587f124cf9b85d41b1471ee0aeb4a21cd0a5e2712555c"
    ),
    "docs/data/second-opportunity-synthesis-execution-approval-v3.json": (
        "9f951e64d9bc93e1dfb907763c2fdfedc1f3df46b48e63acf927fef3671d027c"
    ),
    "docs/data/second-opportunity-synthesis-execution-approval-v4.json": (
        "c5cb608e4cf5aac6698ebec005658184e173518bb0ea719ba7e25185d5a73957"
    ),
    "docs/data/second-opportunity-synthesis-execution-approval-v5.json": (
        "df2efd342c4962b1da2acebf6e9c3f4433677c8645112a83ebdb597d6b355873"
    ),
    "docs/data/second-opportunity-synthesis-execution-record-v1.json": (
        "b769ddeb6ea4d4e773640c3ed83caeff52c52c857fd9125325140de4ab38c799"
    ),
    "docs/data/second-opportunity-synthesis-execution-record-v2.json": (
        "3fb8d5bae0cb2c64e165961518d9dfd3b1de98eef5244600ea0e5efc289001a7"
    ),
    "docs/data/second-opportunity-synthesis-execution-record-v3.json": (
        "abb093389664405f80878d2a1963beabfa4c271ed559437384146a92ccfb00a3"
    ),
    "docs/data/second-opportunity-synthesis-execution-record-v4.json": (
        "3e61c2d92df1184aac53f66e5c6e57fc9aeacb4aae4ebe9eb1c68bf774b10e1b"
    ),
    "docs/data/second-opportunity-synthesis-execution-record-v5.json": (
        "42da9819c066e107d4539c1c4a857425e6809c4389ab69249bebec154b51ea7a"
    ),
    "docs/data/second-opportunity-synthesis-response-v2.json": (
        "8f98939afa049ab3089c41304bdc7b4f0ee86788d54425f764fc1375964dbb11"
    ),
    "docs/data/second-opportunity-synthesis-response-v3.json": (
        "cf5eb183aa7d329f29e8c2c0f04e3939f1661e488952acdf414d07ad8f488ed6"
    ),
    "docs/data/second-opportunity-synthesis-response-v4.json": (
        "76ff8155062c44f727afc530e5a8d435d2bd70720bee524baeed0ee5f6e40205"
    ),
    "docs/data/second-opportunity-synthesis-response-v5.json": (
        "7eb7c3f47d15b353228ae5a44d77ee6d31d593080ac5cc6c4ae9934b1bcd79aa"
    ),
}
RESPONSES = tuple(p for p in HISTORY_SHA256 if "-response-" in p)

ZERO_ACCOUNTING = (
    "MODEL_CALLS",
    "PROVIDER_REQUESTS",
    "MESSAGES_API_REQUESTS",
    "TOKEN_COUNT_API_REQUESTS",
    "TED_BYTES_SENT",
    "CANONICAL_MUTATIONS",
)


class ValidationError(RuntimeError):
    """The freeze record disagrees with the live code, or with what the brief requires."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(relative: str) -> str:
    return _sha((ROOT / relative).read_bytes())


def implementation_sha256() -> str:
    """One digest over the implementation files, path and bytes, in a fixed order (gate 77's rule)."""
    return _sha("".join(f"{p}\x00{file_sha(p)}\n" for p in IMPLEMENTATION_FILES).encode("utf-8"))


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@functools.cache
def fixtures() -> Any:
    return _module("synthetic_fixtures_for_gate_87", FIXTURES)


@functools.cache
def differential() -> Any:
    return _module("gate_differential_for_gate_87", DIFFERENTIAL)


@functools.cache
def gate_79() -> Any:
    return _module("gate_79_for_gate_87", GATE_79)


# ============================================================================= the two verdicts

_ARGUMENTS = frozenset({"evidence_packet", "supplied", "names"})


def _arguments(
    fx: Any, output: Mapping[str, Any], arguments: Mapping[str, Any]
) -> tuple[tuple[object, ...], dict[str, object]]:
    """Gate arguments exactly as the synthetic fixtures' `gate` builds them, for either gate."""
    unknown = set(arguments) - _ARGUMENTS
    if unknown:
        raise ValidationError(f"a corpus case names gate arguments nobody reads: {sorted(unknown)}")
    chosen = arguments.get("evidence_packet")
    chosen = chosen if chosen is not None else fx.packet()
    supplied = arguments.get("supplied")
    names = arguments.get("names")
    return (
        output,
        chosen,
        dict(supplied if supplied is not None else fx.statements()),
        {**fx.EVIDENCE_TO_CLAIM, fx.EXTRA_ROW[0]: fx.EXTRA_ROW[1]},
    ), {
        "trusted_context": build_trusted_context(chosen),
        "source_metadata": names if names is not None else fx.metadata(),
    }


def verdicts(fx: Any, output: Mapping[str, Any], arguments: Mapping[str, Any]) -> tuple[Any, Any]:
    args, kwargs = _arguments(fx, output, arguments)
    return (
        evaluate_second_opportunity_output_v1_3(*args, **kwargs),  # type: ignore[arg-type]
        evaluate_second_opportunity_output_v1_4(*args, **kwargs),  # type: ignore[arg-type]
    )


def classify(fx: Any, case: Sequence[Any]) -> dict[str, Any]:
    _case_id, _origin, output, arguments = case
    args, kwargs = _arguments(fx, output, arguments)
    record, _old, _new, _error = differential().pair(
        evaluate_second_opportunity_output_v1_3,
        evaluate_second_opportunity_output_v1_4,
        args,
        kwargs,
    )
    return record


# ============================================================================= the corpus

Case = tuple[str, str, dict[str, Any], dict[str, Any]]


def _schema_sweep(fx: Any) -> list[Case]:
    """Every property of the schema: null, over its length bound, over its count, one item too long.

    A missing property is one of the census's own cases, so it is not repeated here.
    """
    good = fx.good_output()
    properties: Mapping[str, Any] = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]  # type: ignore[assignment]
    cases: list[Case] = []
    for name in sorted(properties):
        node = properties[name]
        cases.append((f"null:{name}", "sweep", fx.good_output(**{name: None}), {}))
        bound = node.get("maxLength")
        if isinstance(bound, int):
            over = fx.good_output(**{name: "y" * (bound + 1)})
            cases.append((f"over-bound:{name}", "sweep", over, {}))
        items = node.get("items") if isinstance(node.get("items"), Mapping) else {}
        value = good.get(name)
        if isinstance(value, list) and value:
            limit = node.get("maxItems")
            if isinstance(limit, int):
                many = fx.good_output(**{name: [value[0]] * (limit + 1)})
                cases.append((f"over-items:{name}", "sweep", many, {}))
            item_bound = items.get("maxLength")
            if isinstance(item_bound, int):
                long_item = fx.good_output(**{name: ["y" * (item_bound + 1)]})
                cases.append((f"over-item-bound:{name}", "sweep", long_item, {}))
    cases.append(("extra-property", "sweep", fx.good_output(unexpected_property="y"), {}))
    return cases


def _summary_cases(fx: Any) -> list[Case]:
    """The summary around both bounds.

    One repeated letter at each edge, and the fixture's own words repeated until they cross the
    v1.2.0 bound: plain every time, with an unsupported sentence once past the v1.1.0 bound, and once
    in the band with a second structural violation beside it.
    """
    diff = differential()
    old, new = diff.bounds()
    base = str(fx.good_output()[SUMMARY])
    cases: list[Case] = [
        (f"summary-letter:{n}", "summary", fx.good_output(**{SUMMARY: "y" * n}), {})
        for n in sorted({old, old + 1, (old + new) // 2, new, new + 1})
    ]
    other_structural = False
    times = 1
    while True:
        text = " ".join([base] * times)
        where = diff.domain({SUMMARY: text})
        cases.append((f"summary-words:{times}", "summary", fx.good_output(**{SUMMARY: text}), {}))
        if where != "COMMON":
            violated = fx.good_output(**{SUMMARY: text + VIOLATION})
            cases.append((f"summary-words-violation:{times}", "summary", violated, {}))
        if where == "BAND" and not other_structural:
            both = fx.good_output(**{SUMMARY: text, "confidence_classification": "HIGH"})
            cases.append((f"summary-words-other-structural:{times}", "summary", both, {}))
            other_structural = True
        if where == "ABOVE":
            return cases
        times += 1


def corpus(fx: Any) -> list[Case]:
    """(case id, origin, answer, gate arguments). Synthetic only, and no historical answer."""
    census: list[Case] = [
        (f"census:{fixture_id}", "census", answer, dict(arguments))
        for fixture_id, answer, arguments, _target in gate_79().corpus(fx)
    ]
    return [*census, *_schema_sweep(fx), *_summary_cases(fx)]


_EVALUATED: dict[str, list[tuple[Case, dict[str, Any], Any, Any]]] = {}


def evaluate_corpus(fx: Any) -> list[tuple[Case, dict[str, Any], Any, Any]]:
    """Every corpus case through both gates, each gate once: (case, record, v1.3.0, v1.4.0).

    An evaluation costs most of a second, so the corpus is evaluated once per process and shared by
    every block and test that reads it.
    """
    if "rows" not in _EVALUATED:
        diff = differential()
        rows: list[tuple[Case, dict[str, Any], Any, Any]] = []
        for case in corpus(fx):
            args, kwargs = _arguments(fx, case[2], case[3])
            record, old, new, _error = diff.pair(
                evaluate_second_opportunity_output_v1_3,
                evaluate_second_opportunity_output_v1_4,
                args,
                kwargs,
            )
            rows.append((case, record, old, new))
        _EVALUATED["rows"] = rows
    return _EVALUATED["rows"]


# ============================================================================= the blocks


def predecessor_block() -> dict[str, Any]:
    """Section 6: gate v1.3.0 is its own freeze, before and after, with the digest it was frozen at."""
    freeze = _module("gate_77_for_gate_87", GATE_77)
    try:
        freeze.validate()
    except freeze.ValidationError as error:
        raise ValidationError(f"gate v1.3.0 is no longer its own freeze: {error}") from error
    implementation = freeze.implementation_sha256()
    test = freeze.file_sha(freeze.TEST_FILE)
    if implementation != PREDECESSOR_IMPLEMENTATION_SHA256 or test != PREDECESSOR_TEST_SHA256:
        raise ValidationError(
            "gate v1.3.0 moved, and KEEP_SEMANTIC_GATE_V1_3_0_IMMUTABLE forbids it"
        )
    return {
        "gate": SECOND_OPPORTUNITY_GATE_VERSION_V1_3,
        "implementation_sha256": implementation,
        "test_sha256": test,
        "files_edited": [],
        "still_validates": True,
    }


def identity_block() -> dict[str, Any]:
    """Section 7: the successor's components are v1.3.0's, with the gate and the schema moved."""
    moved = sorted(
        k
        for k in COMPONENT_VERSIONS_V1_3.keys() | COMPONENT_VERSIONS_V1_4.keys()
        if COMPONENT_VERSIONS_V1_3.get(k) != COMPONENT_VERSIONS_V1_4.get(k)
    )
    if moved != sorted(CHANGED_COMPONENTS):
        raise ValidationError(f"components other than the gate and the schema moved: {moved}")
    if COMPONENT_VERSIONS_V1_4["output_schema"] != SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2:
        raise ValidationError("gate v1.4.0 is not bound to output schema v1.2.0")
    if PREDECESSOR_GATE_VERSION != SECOND_OPPORTUNITY_GATE_VERSION_V1_3:
        raise ValidationError("gate v1.4.0 names another predecessor")
    if tuple(OPERATOR_DECISION_V1_4) != REQUIRED_DECISION:
        raise ValidationError("the operator's decision is not carried as it was given")
    return {
        "COMPONENT_VERSIONS": dict(COMPONENT_VERSIONS_V1_4),
        "COMPONENTS_CHANGED": {
            k: [COMPONENT_VERSIONS_V1_3[k], COMPONENT_VERSIONS_V1_4[k]] for k in sorted(moved)
        },
        "COMPONENTS_UNCHANGED": sorted(set(COMPONENT_VERSIONS_V1_3) - set(moved)),
    }


def schema_block() -> dict[str, Any]:
    new = output_schema_sha256(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2)
    old = output_schema_sha256(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
    if new != OUTPUT_SCHEMA_SHA256 or old != PREDECESSOR_OUTPUT_SCHEMA_SHA256:
        raise ValidationError("an output schema moved since Mission 1.84.16 recorded it")
    diff = semantic_schema_diff(
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2
    )
    if [d[0] for d in diff] != [f"properties.{SUMMARY}.maxLength"]:
        raise ValidationError(f"the schemas differ in more than the one bound: {diff}")
    return {
        "version": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
        "sha256": new,
        "predecessor_version": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
        "predecessor_sha256": old,
        "semantic_diff": [[path, before, after] for path, before, after in diff],
    }


def _calls(tree: ast.AST, name: str) -> list[ast.Call]:
    return [
        n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == name
    ]


def implementation_block() -> dict[str, Any]:
    """The successor module: one call to v1.3.0, the schema v1.2.0 check, and no number of its own."""
    tree = ast.parse((ROOT / SUCCESSOR_MODULE).read_text(encoding="utf-8"))
    numbers = [
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, int)
        and not isinstance(n.value, bool)
    ]
    if numbers:
        raise ValidationError(f"the successor module carries numbers of its own: {numbers}")
    if len(_calls(tree, "evaluate_second_opportunity_output_v1_3")) != 1:
        raise ValidationError("the successor must call gate v1.3.0 exactly once")
    schemas = [
        getattr(c.args[1], "id", None)
        for c in _calls(tree, "schema_violations")
        if len(c.args) == 2
    ]
    if sorted(schemas) != [
        "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1",
        "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2",
    ]:
        raise ValidationError(f"the successor's structural checks read {schemas}")
    functions = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    if functions != ["evaluate_second_opportunity_output_v1_4"]:
        raise ValidationError(f"the successor defines more than its evaluator: {functions}")
    return {
        "IMPLEMENTATION_FILES": {p: file_sha(p) for p in IMPLEMENTATION_FILES},
        "SEMANTIC_GATE_V1_4_IMPLEMENTATION_SHA256": implementation_sha256(),
        "FROZEN_TEST_FILE": {TEST_FILE: file_sha(TEST_FILE)},
        "STRUCTURAL_REPLACEMENT": {
            "predecessor_prefix": PREDECESSOR_STRUCTURAL_REASON_PREFIX,
            "prefix": STRUCTURAL_REASON_PREFIX,
            "rule": (
                "gate v1.3.0's leading schema v1.1.0 reasons are recomputed and compared entry by "
                "entry, removed, and replaced by schema v1.2.0's; every other reason is kept in the "
                "order gate v1.3.0 gives it"
            ),
            "on_a_predecessor_that_stops_writing_them_first": "PredecessorShapeChanged",
        },
        "SUCCESSOR_NUMERIC_LITERALS": 0,
        "SUCCESSOR_CALLS_TO_GATE_V1_3": 1,
    }


def differential_block(fx: Any) -> dict[str, Any]:
    """Sections 8 to 10 over the synthetic corpus: every case classified, and none diverges."""
    diff = differential()
    records: list[dict[str, Any]] = []
    by_origin: dict[str, int] = {}
    for case, record, _old, _new in evaluate_corpus(fx):
        if diff.divergent(record):
            raise ValidationError(f"{case[0]} diverges: {record}")
        records.append(record)
        by_origin[case[1]] = by_origin.get(case[1], 0) + 1
    summary = diff.summarize(records)
    for domain in ("COMMON", "BAND", "ABOVE"):
        if not summary["BY_DOMAIN"][domain]:
            raise ValidationError(f"the corpus reaches no {domain} case")
    return {"CASES": len(records), "BY_ORIGIN": dict(sorted(by_origin.items())), **summary}


def band_block(fx: Any) -> dict[str, Any]:
    """Section 9: in (v1.1.0 bound, v1.2.0 bound], v1.4.0 drops the old reason and nothing else."""
    old, new = differential().bounds()
    base = str(fx.good_output()[SUMMARY])
    positive = fx.good_output(**{SUMMARY: " ".join([base] * REPETITIONS)})
    length = len(positive[SUMMARY])
    stale = f"{PREDECESSOR_STRUCTURAL_REASON_PREFIX}{SUMMARY}: {length} characters exceeds maxLength {old}"
    was, now = verdicts(fx, positive, {})
    if list(was.refusal_reasons) != [stale] or not now.persist or now.refusal_reasons:
        raise ValidationError(f"the band positive is not what section 9 requires: {was}, {now}")
    negative = fx.good_output(**{SUMMARY: positive[SUMMARY] + VIOLATION})
    was_n, now_n = verdicts(fx, negative, {})
    if (
        now_n.persist
        or not now_n.refusal_reasons
        or list(now_n.refusal_reasons) != list(was_n.refusal_reasons[1:])
        or any(r.startswith(STRUCTURAL_REASON_PREFIX) for r in now_n.refusal_reasons)
    ):
        raise ValidationError(f"a semantic violation in the band is not still refused: {now_n}")
    letters = []
    for probe in (old + 1, (old + new) // 2, new):
        was_l, now_l = verdicts(fx, fx.good_output(**{SUMMARY: "y" * probe}), {})
        if was_l.persist or not now_l.persist:
            raise ValidationError(f"a {probe}-character summary is not refused by v1.3.0 only")
        letters.append({"characters": probe, "v1_3_0": "FAIL", "v1_4_0": "PASS"})
    return {
        "V1_1_0_BOUND": old,
        "V1_2_0_BOUND": new,
        "POSITIVE": {
            "answer": "the synthetic fixture's valid answer, its summary its own words repeated",
            "summary_characters": length,
            "gate_v1_3_0_refusal_reasons": list(was.refusal_reasons),
            "gate_v1_4_0_refusal_reasons": [],
            "gate_v1_4_0_persist": True,
        },
        "NEGATIVE": {
            "answer": "the same answer, with one sentence no supplied statement supports",
            "summary_characters": len(negative[SUMMARY]),
            "gate_v1_4_0_refusal_reasons": list(now_n.refusal_reasons),
            "gate_v1_4_0_persist": False,
            "old_bound_reason_in_v1_4_0": False,
        },
        "ONE_LETTER": letters,
    }


def above_block(fx: Any) -> dict[str, Any]:
    """Section 10: above the v1.2.0 bound, v1.4.0 fails and names schema v1.2.0 and its bound."""
    _old, new = differential().bounds()
    output = fx.good_output(**{SUMMARY: "y" * (new + 1)})
    _was, now = verdicts(fx, output, {})
    expected = [
        f"{SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2}: {SUMMARY}: {new + 1} characters "
        f"exceeds maxLength {new}"
    ]
    if list(now.refusal_reasons) != expected or now.persist:
        raise ValidationError(f"one over the v1.2.0 bound is not refused by name: {now}")
    return {
        "summary_characters": new + 1,
        "gate_v1_4_0_refusal_reasons": expected,
        "names_schema": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_2,
        "names_bound": new,
    }


def matrix_block() -> dict[str, Any]:
    """Section 11: gate v1.3.0's frozen test file, replayed through both gates, diverges nowhere."""
    result = differential().replay_matrix(ROOT / PREDECESSOR_TEST_FILE, SUITE)
    tests = result["tests"]
    summary = result["summary"]
    if result["returncode"] or result["exitstatus"] or tests["failed"] or tests["skipped"]:
        raise ValidationError(f"the v1.3.0 matrix did not pass under the spy: {result}")
    required = {"tests.test_semantic_gate_v1_3", "sros_opportunity.second_opportunity_gate_v1_3"}
    if not required <= set(result["patched_modules"]):
        raise ValidationError(
            f"the spy did not replace every reference: {result['patched_modules']}"
        )
    if not summary["EVALUATOR_CALLS"] or summary["DIVERGENCES"]:
        raise ValidationError(f"the matrix replay diverges or reaches nothing: {summary}")
    return {
        "test_file": PREDECESSOR_TEST_FILE,
        "test_file_sha256": file_sha(PREDECESSOR_TEST_FILE),
        "test_file_edited": False,
        "TESTS_PASSED": tests["passed"],
        "TESTS_FAILED": tests["failed"],
        "TESTS_REACHING_THE_EVALUATOR": result["tests_reaching_the_evaluator"],
        "PATCHED_MODULES": result["patched_modules"],
        **summary,
        "note": (
            "every call the v1.3.0 tests make to the v1.3.0 evaluator ran both gates and handed back "
            "v1.3.0's verdict, so each test asserted what it always asserted. The tests that do not "
            "reach the evaluator exercise the audit, the support universe, the inflection policy and "
            "the metadata channel directly, and gate v1.4.0 reaches those only through gate "
            "v1.3.0's own evaluator, never through a copy"
        ),
    }


def _shingles(text: str, width: int = 6) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {" ".join(words[i : i + width]) for i in range(len(words) - width + 1)}


def history_block() -> dict[str, Any]:
    """Section 12: the V1 to V5 artifacts are the merged bytes, and none of their answers is used."""
    for relative, digest in HISTORY_SHA256.items():
        if file_sha(relative) != digest:
            raise ValidationError(f"{relative} is not the file that was merged")
    answers: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, str):
            answers.update(_shingles(value))
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)

    for relative in RESPONSES:
        walk(json.loads((ROOT / relative).read_text(encoding="utf-8")).get("parsed_output"))
    ours = set().union(
        *(
            _shingles((ROOT / p).read_text(encoding="utf-8"))
            for p in (SUCCESSOR_MODULE, TEST_FILE, DIFFERENTIAL_FILE)
        )
    )
    overlap = sorted(answers & ours)
    if overlap:
        raise ValidationError(
            f"a run of a historical answer is in gate v1.4.0 or its tests: {overlap[:3]}"
        )
    return {
        "ARTIFACTS_PINNED": len(HISTORY_SHA256),
        "ARTIFACTS_EDITED": 0,
        "HISTORICAL_ANSWERS_REPLAYED_THROUGH_V1_4_0": 0,
        "HISTORICAL_ANSWER_RUNS_IN_GATE_OR_TESTS": 0,
        "V3_V4_V5_RECLASSIFIED": False,
        "V5_REVALIDATED_UNDER_V1_2_0": False,
    }


def build_record() -> dict[str, Any]:
    """The freeze record, derived from the live code. `--check` requires the committed one to equal it."""
    fx = fixtures()
    return {
        "$comment": (
            "Mission 1.84.17. The semantic output gate v1.4.0, derived from the live code and frozen "
            "before it becomes a dependency of execution packet V6. CI gate 87 re-derives every field."
        ),
        "record_version": "second-opportunity-output-gate-freeze@1.1.0",
        "mission": MISSION,
        "GATE_VERSION": SECOND_OPPORTUNITY_GATE_VERSION_V1_4,
        "PREDECESSOR_GATE_VERSION": PREDECESSOR_GATE_VERSION,
        "PREDECESSOR_GATE_MUTATED": False,
        "PREDECESSOR_FREEZE": predecessor_block(),
        "OPERATOR_DECISION": list(OPERATOR_DECISION_V1_4),
        **identity_block(),
        "OUTPUT_SCHEMA": schema_block(),
        **implementation_block(),
        "DIFFERENTIAL_MODULE_SHA256": file_sha(DIFFERENTIAL_FILE),
        "DIFFERENTIAL": differential_block(fx),
        "BAND": band_block(fx),
        "ABOVE": above_block(fx),
        "MATRIX_PARITY": matrix_block(),
        "HISTORY": history_block(),
        "NON_STRUCTURAL_SEMANTIC_DIVERGENCES": 0,
        "COMMON_DOMAIN_SEMANTIC_DIVERGENCES": 0,
        "SEMANTIC_GATE_V1_4_FROZEN_BEFORE_V6": True,
        "GATE_V1_4_FROZEN": True,
        "accounting": {key: 0 for key in ZERO_ACCOUNTING},
    }


def validate() -> dict[str, Any]:
    if not RECORD.exists():
        raise ValidationError(f"{RECORD.name} does not exist")
    record: dict[str, Any] = json.loads(RECORD.read_text(encoding="utf-8"))
    # -- pinned here, not read from the record ----------------------------------------------
    if implementation_sha256() != FROZEN_IMPLEMENTATION_SHA256:
        raise ValidationError(
            "the v1.4.0 implementation is not the one frozen; a changed gate is a new gate version "
            "and needs a new freeze"
        )
    if file_sha(TEST_FILE) != FROZEN_TEST_SHA256:
        raise ValidationError("the frozen v1.4.0 test file changed after the freeze")
    # -- the record is exactly what the code derives -----------------------------------------
    expected = json.loads(json.dumps(build_record()))
    for key, value in expected.items():
        if key == "$comment":
            continue
        if record.get(key) != value:
            raise ValidationError(f"{key} is {record.get(key)!r}; the live code derives {value!r}")
    stray = sorted(set(record) - set(expected))
    if stray:
        raise ValidationError(f"the record carries fields the code does not derive: {stray}")
    if (
        record["NON_STRUCTURAL_SEMANTIC_DIVERGENCES"]
        or record["COMMON_DOMAIN_SEMANTIC_DIVERGENCES"]
    ):
        raise ValidationError("a divergence is recorded")
    return record


# ============================================================================= rendering


def _row(*cells: object) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def render(record: dict[str, Any]) -> str:
    diff = record["DIFFERENTIAL"]
    matrix = record["MATRIX_PARITY"]
    band = record["BAND"]
    lines = [
        "<!-- Generated by infrastructure/scripts/render_second_opportunity_semantic_gate_v1_4.py."
        " Do not edit by hand. -->",
        "",
        "# Second-Opportunity output gate v1.4.0: frozen before execution packet V6",
        "",
        f"Mission {record['mission'].removeprefix('mission-')}. Gate `{record['GATE_VERSION']}`, "
        f"successor of `{record['PREDECESSOR_GATE_VERSION']}`, which is not mutated: implementation "
        f"`{record['PREDECESSOR_FREEZE']['implementation_sha256']}`, tests "
        f"`{record['PREDECESSOR_FREEZE']['test_sha256']}`.",
        "",
        "## The operator's decision",
        "",
        *(f"- `{item}`" for item in record["OPERATOR_DECISION"]),
        "",
        "## What moved",
        "",
        _row("component", "v1.3.0", "v1.4.0"),
        _row("---", "---", "---"),
        *(_row(k, f"`{a}`", f"`{b}`") for k, (a, b) in record["COMPONENTS_CHANGED"].items()),
        "",
        "Unchanged: " + ", ".join(f"`{k}`" for k in record["COMPONENTS_UNCHANGED"]) + ".",
        "",
        f"Output schema `{record['OUTPUT_SCHEMA']['version']}` `{record['OUTPUT_SCHEMA']['sha256']}`; "
        "its one difference from the predecessor:",
        "",
        *(f"- `{p}`: {a} to {b}" for p, a, b in record["OUTPUT_SCHEMA"]["semantic_diff"]),
        "",
        f"Implementation digest `{record['SEMANTIC_GATE_V1_4_IMPLEMENTATION_SHA256']}` over:",
        "",
        *(f"- `{p}` `{d}`" for p, d in record["IMPLEMENTATION_FILES"].items()),
        "",
        "Frozen tests: "
        + ", ".join(f"`{p}` `{d}`" for p, d in record["FROZEN_TEST_FILE"].items())
        + ".",
        "",
        "## The differential",
        "",
        f"{diff['CASES']} synthetic cases ("
        + ", ".join(f"{k} {v}" for k, v in diff["BY_ORIGIN"].items())
        + "), each run through both gates on the same arguments.",
        "",
        _row("domain", "cases", "persist changed"),
        _row("---", "---", "---"),
        *(
            _row(d, diff["BY_DOMAIN"][d], diff["PERSIST_CHANGED_BY_DOMAIN"][d])
            for d in ("COMMON", "BAND", "ABOVE", "RAISED")
        ),
        "",
        f"- COMMON_DOMAIN_SEMANTIC_DIVERGENCES = {diff['COMMON_DOMAIN_SEMANTIC_DIVERGENCES']}",
        f"- NON_STRUCTURAL_SEMANTIC_DIVERGENCES = {diff['NON_STRUCTURAL_SEMANTIC_DIVERGENCES']}",
        "- STRUCTURAL_DIVERGENCES_BEYOND_THE_ONE_BOUND = "
        f"{diff['STRUCTURAL_DIVERGENCES_BEYOND_THE_ONE_BOUND']}",
        "",
        f"Band ({band['V1_1_0_BOUND']}, {band['V1_2_0_BOUND']}]: a "
        f"{band['POSITIVE']['summary_characters']}-character summary is refused by v1.3.0 with "
        f"`{band['POSITIVE']['gate_v1_3_0_refusal_reasons'][0]}` and passes v1.4.0; the same summary "
        "with one unsupported sentence is refused by v1.4.0 with "
        f"{len(band['NEGATIVE']['gate_v1_4_0_refusal_reasons'])} semantic reason(s) and no structural "
        "one.",
        "",
        f"Above: `{record['ABOVE']['gate_v1_4_0_refusal_reasons'][0]}`.",
        "",
        "## Gate v1.3.0's own test matrix, through both gates",
        "",
        f"`{matrix['test_file']}` (`{matrix['test_file_sha256']}`), unedited: "
        f"{matrix['TESTS_PASSED']} passed, {matrix['TESTS_FAILED']} failed; "
        f"{matrix['TESTS_REACHING_THE_EVALUATOR']} tests reach the evaluator, "
        f"{matrix['EVALUATOR_CALLS']} calls, {matrix['DIVERGENCES']} divergences.",
        "",
        matrix["note"] + ".",
        "",
        "## History",
        "",
        f"{record['HISTORY']['ARTIFACTS_PINNED']} V1 to V5 artifacts byte-identical to the merged ones; "
        "no historical answer replayed through v1.4.0; V3, V4 and V5 not reclassified; V5 not "
        "revalidated under schema v1.2.0.",
        "",
        "Model calls, provider requests, Messages API requests, token-count requests, TED bytes and "
        "canonical mutations: " + ", ".join(str(v) for v in record["accounting"].values()) + ".",
        "",
    ]
    return "\n".join(lines)


def _write_json(path: pathlib.Path, data: dict[str, Any]) -> None:
    path.write_bytes((json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    group.add_argument("--digests", action="store_true", help="print the two freeze digests")
    args = parser.parse_args(argv)
    if args.digests:
        print(f"implementation {implementation_sha256()}")
        print(f"tests          {file_sha(TEST_FILE)}")
        return 0
    if args.write:
        _write_json(RECORD, build_record())
    try:
        record = validate()
    except ValidationError as error:
        print(f"FAIL: {error}")
        return 1
    text = render(record)
    if args.write:
        RECORD_MD.write_bytes(text.encode("utf-8"))
    elif not RECORD_MD.exists() or RECORD_MD.read_text(encoding="utf-8") != text:
        print(f"FAIL: {RECORD_MD.name} is stale; run with --write")
        return 1
    print(f"ok: {RECORD.name} is the frozen gate v1.4.0 the live code derives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
