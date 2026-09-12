"""Mission 1.84.10, CI gate 75. The semantic output gate v1.2.0, frozen before the V3 diagnostic replay.

The operator asked for the semantic gate's assertion context to be repaired, and for the repair to be
FROZEN (implementation, versioning, tests and adversarial tests) before the one historical answer it
was prompted by is replayed through it. A gate tuned after seeing how an answer fares is tuned on that
answer, so the order is the whole point, and this gate is what makes it checkable:

* the freeze record is DERIVED from the live code, and must equal what the code derives now;
* the implementation and the frozen test file are pinned by digest HERE, in this script, so a later
  `--write` cannot re-freeze a changed gate without an edit to this file that a reviewer sees;
* the historical modules that v1.0.0 and v1.1.0 run on are pinned to bb0f50a's bytes, so the
  historical verdicts still resolve against the code that produced them;
* the operator's decision, the seven dispositions, the field policy, the forbidden concepts (none
  removed, every v1.0.0 phrase kept, every §20 concept named), the three support channels and the
  trusted-context bound are read from the code and checked against what the brief requires;
* the record states that no V3 text is a test case and no answer is whitelisted, and the frozen test
  file is checked to contain no run of the historical answer.

    uv run python infrastructure/scripts/render_second_opportunity_semantic_gate_v1_2.py --check
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import pathlib
import re
from typing import Any

from sros_opportunity.assertion_context import (
    PROMPT_TEXT_IS_NOT_OBSERVED_EVIDENCE,
    SUPPORT_UNIVERSE_VERSION,
    Disposition,
    Shape,
    SupportCategory,
)
from sros_opportunity.second_opportunity import (
    _FORBIDDEN_PHRASES,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1,
    SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
    SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2,
    SECOND_OPPORTUNITY_SYSTEM_V1_2,
)
from sros_opportunity.second_opportunity_gate_v1_2 import (
    CLASSIFICATION_DISPOSITIONS,
    COMPONENT_VERSIONS_V1_2,
    FORBIDDEN_CONCEPTS_V1_2,
    SECOND_OPPORTUNITY_FIELD_POLICY,
    SECOND_OPPORTUNITY_GATE_VERSION_V1_2,
    SEMANTIC_GATE_REPAIR_DECISION,
    TRUSTED_CONTEXT_VERSION,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"
RECORD = DATA / "second-opportunity-output-gate-v1.2-freeze-v1.json"
RECORD_MD = DATA / "second-opportunity-output-gate-v1.2-freeze-v1.md"
RESPONSE_V3 = DATA / "second-opportunity-synthesis-response-v3.json"
PACKAGE = "packages/opportunity-engine/python/sros_opportunity"
TESTS = "packages/opportunity-engine/python/tests"

MISSION = "mission-1.84.10"
IMPLEMENTATION_FILES = (
    f"{PACKAGE}/assertion_context.py",
    f"{PACKAGE}/second_opportunity_gate_v1_2.py",
)
TEST_FILE = f"{TESTS}/test_semantic_gate_v1_2.py"

#: Pinned at the freeze. Editing either is re-freezing, and re-freezing is a new gate version.
FROZEN_IMPLEMENTATION_SHA256 = "47bbcb459b0b69153d23c7dcc7f273e0e47d0b84a72522d25f773cd462db82b0"
FROZEN_TEST_SHA256 = "c84d99cfe8d43027f89ba5e46ae599b04b5fd786472818c1e014f46343560cf0"

#: bb0f50a's bytes: the modules v1.0.0 and v1.1.0 run on.
HISTORICAL_SHA256 = {
    f"{PACKAGE}/guards.py": "41c732fa3ccc8210cd0131c4ee9bb3ac5f181c6a4a5a68459b71c37a17e5e29c",
    f"{PACKAGE}/validation.py": "c62c3f91bc2255a411435eb8256f4a055c4f816a5172d3496c4382d96ddc8ed6",
    f"{PACKAGE}/second_opportunity.py": (
        "24ba090d3ff750ae95105458ba5528a1597449a902184a1d009b58dc9bc9221b"
    ),
    f"{PACKAGE}/schema_validation.py": (
        "243ef0532deaf6c85c3cee1e3cac50e8bfe356a45061d3f9f1beaf68b09ed790"
    ),
}

OUTPUT_SCHEMA_SHA256 = "ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988"
PROMPT_SHA256 = "1677cbe53e83e644fa15e5492cf88e3ec578538351924f2b3a504e27f3a0878d"

REQUIRED_DECISION = (
    "KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED",
    "KEEP_PROMPT_V1_2_0_UNCHANGED",
    "REPAIR_SEMANTIC_GATE_ASSERTION_CONTEXT",
    "DO_NOT_WHITELIST_THE_V3_ANSWER",
    "DO_NOT_REMOVE_FORBIDDEN_CONCEPTS",
    "DO_NOT_WEAKEN_EVIDENCE_BOUNDARIES",
)
REQUIRED_DISPOSITIONS = (
    "SUPPORTED_ASSERTION",
    "HYPOTHESIS_TO_VALIDATE",
    "EXPLICITLY_NOT_SUPPORTED",
    "UNKNOWN_REQUIRES_EVIDENCE",
    "FUTURE_EVIDENCE_REQUEST",
    "STRUCTURAL_FACT",
    "TRUSTED_LIMITING_FACT",
)
#: §7, the fields the brief names, and the disposition and shape each must have.
REQUIRED_FIELD_CONTEXT = {
    "commercial_claims_supported": ("SUPPORTED_ASSERTION", "FREE"),
    "commercial_claims_not_supported": ("EXPLICITLY_NOT_SUPPORTED", "FREE"),
    "critical_uncertainties": ("UNKNOWN_REQUIRES_EVIDENCE", "UNCERTAINTY"),
    "recommended_next_evidence": ("FUTURE_EVIDENCE_REQUEST", "REQUEST"),
    "supported_dimensions": ("STRUCTURAL_FACT", "ENUMERATION"),
    "unsupported_dimensions": ("EXPLICITLY_NOT_SUPPORTED", "ENUMERATION"),
    "reliability_status": ("STRUCTURAL_FACT", "FREE"),
    "independence_status": ("STRUCTURAL_FACT", "FREE"),
    "hypothesis_statement": ("HYPOTHESIS_TO_VALIDATE", "FREE"),
    "evidence_bound_reasoning_summary": ("SUPPORTED_ASSERTION", "FREE"),
    "observed_need": ("SUPPORTED_ASSERTION", "FREE"),
    "candidate_intervention_class": ("SUPPORTED_ASSERTION", "FREE"),
}
SECTION_20 = (
    "realised spend",
    "actual expenditure",
    "willingness to pay",
    "software demand",
    "product demand",
    "market size",
    "buyer need",
    "unmet need",
    "dissatisfaction",
    "solution gap",
    "competitive gap",
    "product-market fit",
    "profitability",
)
#: The cases the operator's brief states word for word (§5, §12, §13). They are the operator's own
#: inputs, written from the historical refusal, so they may share wording with it by design. They
#: are the ONLY text the frozen tests may share with the historical answer, and the implementation
#: may share none at all.
BRIEF_CASES = (
    "Customers are willing to pay.",
    "The evidence establishes willingness to pay.",
    "Actual expenditure was 10 million EUR.",
    "These Evidence rows are scored.",
    "There is a solution gap.",
    "The procurement values prove market demand.",
    "No evidence establishes willingness to pay.",
    "Willingness to pay is not established.",
    "Actual expenditure is not established by this packet.",
    "No score exists.",
    "These rows are scoring-ready, not scored.",
    "Evidence of actual expenditure would be required.",
    "Customers definitely have an unmet need.",
    "The packet does not establish actual expenditure.",
    "Scoring-ready is not the same as scored, and no score exists.",
    "No evidence establishes willingness to pay. Buyers are willing to pay.",
    "Actual expenditure is not established, but is probably substantial.",
    "These rows are not unscored; they are scored.",
)
SUPPORT_CATEGORIES = (
    "SOURCE_STATEMENTS",
    "PACKET_STRUCTURAL_FACTS",
    "TRUSTED_LIMITING_OR_DEFINITIONAL_CONTEXT",
)
#: The test classes the brief's matrices live in, and the smallest case count each may hold.
MATRIX_CLASSES = {
    "TestSection5AssertionNotTokenPresence": 12,
    "TestSection13SentenceScopedDenial": 6,
    "TestSection14Scored": 12,
    "TestSection11RecommendedNextEvidence": 7,
    "TestSection12CriticalUncertainties": 6,
    "TestSection20ForbiddenConceptsStayForbidden": 13,
    "TestAdversarialAssertions": 16,
}
ZERO_ACCOUNTING = (
    "MODEL_CALLS",
    "PROVIDER_REQUESTS",
    "MESSAGES_API_REQUESTS",
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
    """One digest over the implementation files, path and bytes, in a fixed order."""
    return _sha("".join(f"{p}\x00{file_sha(p)}\n" for p in IMPLEMENTATION_FILES).encode("utf-8"))


def schema_sha256() -> str:
    return _sha(json.dumps(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, sort_keys=True).encode("utf-8"))


def matrix_counts() -> dict[str, int]:
    """How many literal cases each matrix class holds, read from the frozen test file's syntax."""
    tree = ast.parse((ROOT / TEST_FILE).read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name not in MATRIX_CLASSES:
            continue
        total = 0
        for statement in node.body:
            if isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Tuple):
                total += len(statement.value.elts)
        counts[node.name] = total
    return counts


def live_policy() -> list[dict[str, object]]:
    return [
        {
            "field": fc.field_name,
            "disposition": fc.disposition.value if fc.disposition else None,
            "shape": fc.shape.value,
            "label_key": fc.item_label_key,
        }
        for fc in SECOND_OPPORTUNITY_FIELD_POLICY
    ]


def build_record() -> dict[str, Any]:
    """The freeze record, derived from the live code. `--check` requires the committed one to equal it."""
    return {
        "$comment": (
            "Mission 1.84.10. The semantic output gate v1.2.0, derived from the live code and frozen "
            "before the V3 diagnostic replay. CI gate 75 re-derives every field."
        ),
        "record_version": "second-opportunity-output-gate-freeze@1.0.0",
        "mission": MISSION,
        "GATE_VERSION": SECOND_OPPORTUNITY_GATE_VERSION_V1_2,
        "PREDECESSOR_GATE_VERSION": SECOND_OPPORTUNITY_GATE_VERSION_V1_1,
        "PREDECESSOR_GATE_MUTATED": False,
        "COMPONENT_VERSIONS": dict(COMPONENT_VERSIONS_V1_2),
        "OPERATOR_DECISION": list(SEMANTIC_GATE_REPAIR_DECISION),
        "OUTPUT_SCHEMA_VERSION": SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
        "OUTPUT_SCHEMA_SHA256": schema_sha256(),
        "OUTPUT_SCHEMA_CHANGED": False,
        "PROMPT_VERSION": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_2,
        "PROMPT_SHA256": PROMPT_SHA256,
        "SYSTEM_REGION_V1_2_SHA256": _sha(SECOND_OPPORTUNITY_SYSTEM_V1_2.encode("utf-8")),
        "PROMPT_CHANGED": False,
        "HISTORICAL_MODULES": {p: file_sha(p) for p in HISTORICAL_SHA256},
        "IMPLEMENTATION_FILES": {p: file_sha(p) for p in IMPLEMENTATION_FILES},
        "IMPLEMENTATION_SHA256": implementation_sha256(),
        "FROZEN_TEST_FILE": {TEST_FILE: file_sha(TEST_FILE)},
        "DISPOSITIONS": [d.value for d in Disposition],
        "SHAPES": [s.value for s in Shape],
        "FIELD_POLICY": live_policy(),
        "CLASSIFICATION_DISPOSITIONS": {k: v.value for k, v in CLASSIFICATION_DISPOSITIONS.items()},
        "FORBIDDEN_CONCEPTS": [
            {"name": c.name, "phrases": list(c.phrases), "never": c.never}
            for c in FORBIDDEN_CONCEPTS_V1_2
        ],
        "FORBIDDEN_CONCEPTS_REMOVED": 0,
        "SUPPORT_UNIVERSE": {
            "version": SUPPORT_UNIVERSE_VERSION,
            "categories": [c.value for c in SupportCategory],
            "PROMPT_TEXT_IS_NOT_OBSERVED_EVIDENCE": PROMPT_TEXT_IS_NOT_OBSERVED_EVIDENCE,
            "trusted_context_version": TRUSTED_CONTEXT_VERSION,
            "trusted_context_sources": [
                "the packet's own dimension_bounds, each with the mapping version and signal type "
                "that produced it",
                "the establishes side of FORBIDDEN_TRANSFORMATIONS, rendered in prompt 1.2.0",
            ],
            "trusted_context_licenses": "DEFINITIONAL_IDENTIFIERS_ONLY",
            "trusted_context_never_licenses": [
                "its words",
                "its numbers as magnitudes",
                "any concept it limits",
            ],
        },
        "CANONICAL_TERM_POLICY": (
            "the EvidenceDimension enum term in words, derived in code (MARKET_ACTIVITY -> market "
            "activity); licensed as a whole phrase only where the answer declares the dimension "
            "AND the packet supports it; no paraphrase and no single word is licensed"
        ),
        "MATRICES": matrix_counts(),
        "GATE_V1_2_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY": True,
        "V3_DIAGNOSTIC_REPLAY_PERFORMED_BEFORE_FREEZE": False,
        "V3_TEXT_USED_AS_TEST_CASE": False,
        "WHITELIST_ENTRIES": 0,
        "accounting": {key: 0 for key in ZERO_ACCOUNTING},
    }


def _shingles(text: str, width: int = 6) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {" ".join(words[i : i + width]) for i in range(len(words) - width + 1)}


def _answer_shingles() -> set[str]:
    found: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, str):
            found.update(_shingles(value))
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)

    walk(json.loads(RESPONSE_V3.read_text(encoding="utf-8"))["parsed_output"])
    return found


def historical_overlap() -> set[str]:
    """Six-word runs of the historical answer in the frozen gate, or in its tests beyond the brief's."""
    brief: set[str] = set().union(*(_shingles(case) for case in BRIEF_CASES))
    implementation: set[str] = set().union(
        *(_shingles((ROOT / p).read_text(encoding="utf-8")) for p in IMPLEMENTATION_FILES)
    )
    tests = _shingles((ROOT / TEST_FILE).read_text(encoding="utf-8")) - brief
    return _answer_shingles() & (implementation | tests)


def validate() -> dict[str, Any]:
    if not RECORD.exists():
        raise ValidationError(f"{RECORD.name} does not exist")
    record: dict[str, Any] = json.loads(RECORD.read_text(encoding="utf-8"))

    # -- pinned here, not read from the record -----------------------------------------------
    if implementation_sha256() != FROZEN_IMPLEMENTATION_SHA256:
        raise ValidationError(
            "the v1.2.0 implementation is not the one frozen before the V3 diagnostic replay; a "
            "changed gate is a new gate version and needs a new freeze"
        )
    if file_sha(TEST_FILE) != FROZEN_TEST_SHA256:
        raise ValidationError("the frozen test file changed after the freeze")
    for path, digest in HISTORICAL_SHA256.items():
        if file_sha(path) != digest:
            raise ValidationError(
                f"{path} is not bb0f50a's; v1.0.0 and v1.1.0 must run on the code they ran on"
            )
    if schema_sha256() != OUTPUT_SCHEMA_SHA256:
        raise ValidationError("the v1.1.0 output schema moved")

    # -- what the brief requires, against the live code --------------------------------------
    if tuple(SEMANTIC_GATE_REPAIR_DECISION) != REQUIRED_DECISION:
        raise ValidationError("the operator's decision is not carried as it was given")
    if tuple(d.value for d in Disposition) != REQUIRED_DISPOSITIONS:
        raise ValidationError("the seven dispositions are not the ones the brief names")
    policy = {fc.field_name: fc for fc in SECOND_OPPORTUNITY_FIELD_POLICY}
    declared = SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1["properties"]
    properties = set(declared) if isinstance(declared, dict) else set()
    if set(policy) != properties:
        raise ValidationError(
            f"the field policy does not cover the schema: {set(policy) ^ properties}"
        )
    for field, (disposition, shape) in REQUIRED_FIELD_CONTEXT.items():
        fc = policy[field]
        actual = (fc.disposition.value if fc.disposition else None, fc.shape.value)
        if actual != (disposition, shape):
            raise ValidationError(
                f"{field} has context {actual}; the brief requires {(disposition, shape)}"
            )
    labelled = policy["statement_classifications"]
    if labelled.item_label_key != "classification" or {
        k: v.value for k, v in CLASSIFICATION_DISPOSITIONS.items()
    } != {
        "OBSERVED_OR_EVIDENCE_SUPPORTED": "SUPPORTED_ASSERTION",
        "HYPOTHESIS_TO_VALIDATE": "HYPOTHESIS_TO_VALIDATE",
        "UNKNOWN_REQUIRES_EVIDENCE": "UNKNOWN_REQUIRES_EVIDENCE",
    }:
        raise ValidationError("a statement's classification is not its disposition (§10)")
    phrases = {c.name: set(c.phrases) for c in FORBIDDEN_CONCEPTS_V1_2}
    for name, old in _FORBIDDEN_PHRASES.items():
        if not set(old) <= phrases.get(name, set()):
            raise ValidationError(
                f"{name} lost a v1.0.0 phrase: forbidden concepts are never removed"
            )
    every = {p for c in FORBIDDEN_CONCEPTS_V1_2 for p in c.phrases}
    missing = [c for c in SECTION_20 if c not in every]
    if missing:
        raise ValidationError(f"§20 concepts not named: {missing}")
    if tuple(c.value for c in SupportCategory) != SUPPORT_CATEGORIES:
        raise ValidationError("the support universe is not the three separate channels")
    if PROMPT_TEXT_IS_NOT_OBSERVED_EVIDENCE is not True:
        raise ValidationError("prompt text is being treated as observed evidence (§19)")
    counts = matrix_counts()
    for name, minimum in MATRIX_CLASSES.items():
        if counts.get(name, 0) < minimum:
            raise ValidationError(f"{name} holds {counts.get(name, 0)} cases; it needs {minimum}")
    overlap = historical_overlap()
    if overlap:
        raise ValidationError(
            f"a run of the historical answer is in the frozen gate or tests: {sorted(overlap)[:3]}"
        )

    # -- the record is exactly what the code derives -------------------------------------------
    expected = build_record()
    for key, value in expected.items():
        if key == "$comment":
            continue
        if record.get(key) != value:
            raise ValidationError(f"{key} is {record.get(key)!r}; the live code derives {value!r}")
    stray = sorted(set(record) - set(expected))
    if stray:
        raise ValidationError(f"the record carries fields the code does not derive: {stray}")
    return record


def _row(*cells: object) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def render(record: dict[str, Any]) -> str:
    lines = [
        "<!-- Generated by infrastructure/scripts/render_second_opportunity_semantic_gate_v1_2.py."
        " Do not edit by hand. -->",
        "",
        "# Second-Opportunity output gate v1.2.0: frozen before the V3 diagnostic replay",
        "",
        f"Mission {record['mission'].removeprefix('mission-')}. Gate `{record['GATE_VERSION']}`, "
        f"successor of `{record['PREDECESSOR_GATE_VERSION']}`, which is not mutated.",
        "",
        "## The operator's decision",
        "",
        *(f"- `{item}`" for item in record["OPERATOR_DECISION"]),
        "",
        "## What is unchanged",
        "",
        f"- output schema `{record['OUTPUT_SCHEMA_VERSION']}` `{record['OUTPUT_SCHEMA_SHA256']}`",
        f"- prompt `{record['PROMPT_VERSION']}` `{record['PROMPT_SHA256']}`",
        "- the modules v1.0.0 and v1.1.0 run on, byte-identical to bb0f50a:",
        *(f"  - `{p}` `{d}`" for p, d in record["HISTORICAL_MODULES"].items()),
        "",
        "## Components",
        "",
        _row("component", "version"),
        _row("---", "---"),
        *(_row(k, f"`{v}`") for k, v in record["COMPONENT_VERSIONS"].items()),
        "",
        f"Implementation digest `{record['IMPLEMENTATION_SHA256']}`.",
        "",
        "## Field context policy",
        "",
        _row("field", "disposition", "shape"),
        _row("---", "---", "---"),
        *(
            _row(
                f"`{p['field']}`",
                p["disposition"] or f"from `{p['label_key']}`",
                p["shape"],
            )
            for p in record["FIELD_POLICY"]
        ),
        "",
        "## Forbidden concepts, refused as assertions",
        "",
        _row("concept", "phrases"),
        _row("---", "---"),
        *(
            _row(c["name"], ", ".join(f"`{p}`" for p in c["phrases"]))
            for c in record["FORBIDDEN_CONCEPTS"]
        ),
        "",
        f"Removed: {record['FORBIDDEN_CONCEPTS_REMOVED']}.",
        "",
        "## Support universe",
        "",
        *(f"- `{c}`" for c in record["SUPPORT_UNIVERSE"]["categories"]),
        "",
        f"Trusted context `{record['SUPPORT_UNIVERSE']['trusted_context_version']}` licenses "
        f"`{record['SUPPORT_UNIVERSE']['trusted_context_licenses']}`. "
        "PROMPT_TEXT_IS_NOT_OBSERVED_EVIDENCE = "
        f"{str(record['SUPPORT_UNIVERSE']['PROMPT_TEXT_IS_NOT_OBSERVED_EVIDENCE']).lower()}.",
        "",
        f"Canonical term policy: {record['CANONICAL_TERM_POLICY']}.",
        "",
        "## Frozen matrices",
        "",
        _row("test class", "literal cases"),
        _row("---", "---"),
        *(_row(k, v) for k, v in record["MATRICES"].items()),
        "",
        "## The order",
        "",
        "- GATE_V1_2_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY = "
        f"{str(record['GATE_V1_2_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY']).lower()}",
        "- V3_DIAGNOSTIC_REPLAY_PERFORMED_BEFORE_FREEZE = "
        f"{str(record['V3_DIAGNOSTIC_REPLAY_PERFORMED_BEFORE_FREEZE']).lower()}",
        f"- V3_TEXT_USED_AS_TEST_CASE = {str(record['V3_TEXT_USED_AS_TEST_CASE']).lower()}",
        f"- WHITELIST_ENTRIES = {record['WHITELIST_ENTRIES']}",
        "",
        "Model calls, provider requests, Messages API requests, TED bytes and canonical mutations: "
        + ", ".join(str(v) for v in record["accounting"].values())
        + ".",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        RECORD.write_bytes(
            (json.dumps(build_record(), indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        )
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
    print(f"ok: {RECORD.name} is the frozen gate v1.2.0 the live code derives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
