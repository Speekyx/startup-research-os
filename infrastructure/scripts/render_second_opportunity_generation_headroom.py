"""Gate 83: generation headroom from the live schema and the operator's exact ratio, and prompt v1.4.0.

Mission 1.84.14. Execution V4 was refused at stage 5 on two lengths the prompt stated in words. The
operator kept schema v1.1.0, gate v1.3.0 and the representation, forbade raising a bound or fitting an
answer, and chose a generation policy: a target at most 4/5 of each composed text's hard maximum,
stated beside it, plus field roles that keep each field's information in one place. This gate
re-derives both records from the live code:

    uv run python infrastructure/scripts/render_second_opportunity_generation_headroom.py --check

It refuses: a merged artifact that moved, V1 to V4 and Mission 1.84.12's records; V4's historical
facts or its two schema violations not reproduced; the schema, gate v1.3.0 or prompt v1.3.0 changed;
a hard bound equal to a length V4 or V3 returned; a ratio that is not exactly 4/5; a target not
computed by the one function from the live hard bound; a target on a copied value, a closed choice,
the subject identity or an element count; a target the schema validator enforces, or a hard maximum
it does not; a mutated bound or ratio that fails to move exactly its targets, or a copied bound, count
or choice that moves one; the headroom modules reading a file or carrying a length V4 or V3 returned;
prompt v1.4.0 that is not v1.3.0 plus the block, that leaves a target, a schema bound or a class-A
rule unstated, calls a target a limit, drops a role or the quality floor, asks for a scratchpad or
names a historical execution; stages 6 to 9 no longer ready; and a record field the code does not
derive.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import pathlib
import re
import sys
from collections.abc import Mapping
from fractions import Fraction
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
sys.path.insert(0, str(SCRIPTS))

RECORD = DATA / "second-opportunity-generation-headroom-policy-v1.json"
RECORD_MD = DATA / "second-opportunity-generation-headroom-policy-v1.md"
PROMPT_RECORD = DATA / "second-opportunity-synthesis-prompt-v5.json"
PROMPT_RECORD_MD = DATA / "second-opportunity-synthesis-prompt-v5.md"
V4_RECORD = DATA / "second-opportunity-synthesis-execution-record-v4.json"
V4_RESPONSE = DATA / "second-opportunity-synthesis-response-v4.json"
V3_RESPONSE = DATA / "second-opportunity-synthesis-response-v3.json"
CAPABILITY = DATA / "provider-model-capability-register-v1.json"
PACKAGE = ROOT / "packages" / "opportunity-engine" / "python" / "sros_opportunity"
HEADROOM_MODULES = (
    PACKAGE / "generation_headroom.py",
    PACKAGE / "second_opportunity_prompt_v1_4.py",
)
FIXTURES = SCRIPTS / "second_opportunity_synthetic_fixtures.py"
GATE_77 = SCRIPTS / "render_second_opportunity_semantic_gate_v1_3.py"
GATE_80 = SCRIPTS / "render_second_opportunity_stage_6_9_preflight.py"
GATE_81 = SCRIPTS / "render_second_opportunity_execution_packet_v4.py"

MISSION = "mission-1.84.14"
SUBJECT = "ted-eu:CPV-class:9261"
SCHEMA_VERSION = "second-opportunity-synthesis-output@1.1.0"
SCHEMA_SHA256 = "ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988"
GATE_VERSION = "second-opportunity-output-gate@1.3.0"
GATE_IMPLEMENTATION_SHA256 = "cc3c490268e6f64a0b2107c2fb0c2fe6a1b1c71ab44c353419cd7d86c4485bf3"
PROMPT_V1_3_SHA256 = "a62fa218ab04e7da5b050ec40dcf2450c749dafd34262fe8c83e9fbc040acc5a"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"
REPRESENTATION_CHARACTERS = 3604
V4_SHA256 = "7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b"
#: The two violations the live v1.1.0 validator reported on V4's answer, verbatim.
V4_HISTORICAL_VIOLATIONS = (
    "candidate_intervention_class: 316 characters exceeds maxLength 300",
    "evidence_bound_reasoning_summary: 1078 characters exceeds maxLength 900",
)
MUTATED_RATIOS = (Fraction(1, 2), Fraction(3, 4), Fraction(9, 10))
HARD_MAXIMA_CHECKED = 10000

#: Every merged artifact this mission reads and may not rewrite, over its text with LF line ends.
HISTORY_SHA256: dict[str, str] = {
    "docs/data/second-opportunity-semantic-prompt-alignment-v1.json": (
        "dec1cb103020eb8b0bbd4bd67027a5b0178d1f99a54583527db3cbc3ce202f53"
    ),
    "docs/data/second-opportunity-stage-6-9-preflight-v1.json": (
        "4c5564b98cfabd83e7d7029908b50caa8a81dd6907a1a64d56ff4c80b4ab0c00"
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
    "docs/data/second-opportunity-synthesis-prompt-v4.json": (
        "eb5ce92e1b586a4788722a6fc412c7c3245fa0e9cbf259899a7a55d583b17e88"
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
}

ZERO_ACCOUNTING = {
    "MODEL_CALLS": 0,
    "PROVIDER_REQUESTS": 0,
    "MESSAGES_API_REQUESTS": 0,
    "TOKEN_COUNT_API_REQUESTS": 0,
    "TED_BYTES_SENT": 0,
    "DOCUMENTATION_FETCHES": 0,
    "CANONICAL_MUTATIONS": 0,
}

#: The only integers the headroom modules may carry: 0 and 1 for bounds checks and indexing, the
#: ratio's own 4 and 5, and the wrapping width. No bound, no target, no historical length.
ALLOWED_INTEGERS = frozenset({0, 1, 4, 5, 96})

_ROW = re.compile(
    r"^  (.+?): generation target (\d+) characters; hard maximum (\d+) characters$", re.M
)

_FORBIDDEN_CALLS = frozenset(
    {"open", "read_text", "read_bytes", "load", "loads", "glob", "iterdir"}
)


class ValidationError(RuntimeError):
    """The records disagree with the live code, the merged artifacts, or the operator's policy."""


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def text_sha(path: pathlib.Path) -> str:
    return _sha(path.read_text(encoding="utf-8"))


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _schema() -> dict[str, Any]:
    from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1

    return SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1


def _schema_sha(schema: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(schema, sort_keys=True).encode("utf-8")).hexdigest()


# ============================================================================= history and V4


def history() -> dict[str, str]:
    """Every merged artifact this mission reads, byte for byte the one merged."""
    if not HISTORY_SHA256:
        raise ValidationError("no merged artifact is pinned")
    found: dict[str, str] = {}
    for relative, digest in HISTORY_SHA256.items():
        live = text_sha(ROOT / relative)
        if live != digest:
            raise ValidationError(f"{relative} is not the file that was merged")
        found[relative] = live
    return found


def v4_facts() -> dict[str, Any]:
    """§3. V4's retained record and response, and its two violations reproduced by the live validator."""
    from sros_opportunity.schema_validation import schema_violations

    record, response = _load(V4_RECORD), _load(V4_RESPONSE)
    expected = {
        "execution_packet_sha256": V4_SHA256,
        "actual_provider_requests": 1,
        "actual_model_calls": 1,
        "retries": 0,
        "fallbacks": 0,
        "continuation_requests": 0,
        "repair_calls": 0,
        "STOP_REASON": "tool_use",
        "PRIMARY_OUTCOME": "EXECUTION_SCHEMA_REJECTED_NO_RETRY",
        "EXECUTION_APPROVAL_CONSUMED": True,
        "CANONICAL_PERSISTENCE": False,
        "OPPORTUNITY_PERSISTED": False,
        "CANONICAL_MUTATIONS": 0,
        "HUMAN_REVIEW_PACKET": "NOT_PRODUCED",
        "FAILED_STAGE": "5_schema_validation_v1_1_0",
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise ValidationError(f"V4's record gives {key}={record.get(key)!r}, not {value!r}")
    usage = record["ACTUAL_USAGE"]
    if (
        usage["input_tokens"],
        usage["output_tokens"],
        usage["thinking_tokens"],
        usage["total_tokens"],
    ) != (11599, 3950, 0, 15549) or record["ACTUAL_COST"]["cost_units"] != 0.062698:
        raise ValidationError("V4's usage or cost is not the one recorded")
    stages = record["VALIDATION_STAGES"]
    verdicts = list(stages.values())
    if verdicts[:4] != ["PASSED"] * 4 or verdicts[4] != "FAILED":
        raise ValidationError("V4's stages 1 to 5 are not the ones recorded")
    if any(verdict != "NOT_REACHED" for verdict in verdicts[5:]):
        raise ValidationError("a stage after V4's failure is recorded as reached")
    parsed = response["parsed_output"]
    violations = tuple(schema_violations(dict(parsed), _schema()))
    if violations != V4_HISTORICAL_VIOLATIONS or tuple(record["SCHEMA_VIOLATIONS"]) != violations:
        raise ValidationError(f"V4's violations do not reproduce: {violations}")
    v3 = _load(V3_RESPONSE)["parsed_output"]
    fields = ("candidate_intervention_class", "evidence_bound_reasoning_summary")
    return {
        "V4_OUTCOME": record["PRIMARY_OUTCOME"],
        "V4_APPROVAL_CONSUMED": True,
        "V4_PROVIDER_REQUESTS": 1,
        "V4_MODEL_CALLS": 1,
        "V4_RETRIES": 0,
        "V4_FALLBACKS": 0,
        "V4_CONTINUATIONS": 0,
        "V4_REPAIR_CALLS": 0,
        "V4_STOP_REASON": "tool_use",
        "V4_USAGE": {
            "input_tokens": 11599,
            "output_tokens": 3950,
            "thinking_tokens": 0,
            "total_tokens": 15549,
        },
        "V4_ACTUAL_COST": 0.062698,
        "V4_STAGES": stages,
        "V4_HISTORICAL_VIOLATIONS_REPRODUCED": list(violations),
        "V4_CANONICAL_PERSISTENCE": False,
        "V4_CANONICAL_MUTATIONS": 0,
        "V4_CANDIDATE": False,
        "V4_PERSISTABLE": False,
        "V4_HUMAN_REVIEW_PACKET": "NOT_PRODUCED",
        "V4_REVALIDATED_UNDER_PROMPT_V1_4": False,
        "HISTORICAL_OBSERVATIONS": {
            field: {"v4_characters": len(parsed[field]), "v3_characters": len(v3[field])}
            for field in fields
        },
        "HISTORICAL_OBSERVATIONS_USED_TO_DERIVE_HEADROOM": False,
    }


def _historical_lengths() -> frozenset[int]:
    v4 = _load(V4_RESPONSE)["parsed_output"]
    v3 = _load(V3_RESPONSE)["parsed_output"]
    fields = ("candidate_intervention_class", "evidence_bound_reasoning_summary")
    return frozenset(len(answer[field]) for answer in (v4, v3) for field in fields)


# ============================================================================= contract unchanged


def contract() -> dict[str, Any]:
    """§5, §6, §10: the schema, the gate and prompt v1.3.0, unchanged, and no bound from V4."""
    from sros_opportunity.output_constraints import constraint_inventory
    from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1
    from sros_opportunity.second_opportunity_gate_v1_3 import SECOND_OPPORTUNITY_GATE_VERSION_V1_3

    schema = _schema()
    if _schema_sha(schema) != SCHEMA_SHA256 or SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1 != (
        SCHEMA_VERSION
    ):
        raise ValidationError("OUTPUT_SCHEMA_CHANGED: schema v1.1.0 moved")
    implementation = _module("gate_77_for_gate_83", GATE_77).implementation_sha256()
    if implementation != GATE_IMPLEMENTATION_SHA256 or (
        SECOND_OPPORTUNITY_GATE_VERSION_V1_3 != GATE_VERSION
    ):
        raise ValidationError("SEMANTIC_GATE_CHANGED: gate v1.3.0 moved")
    bounds = {
        c.path: int(c.value)
        for c in constraint_inventory(schema)
        if c.keyword in ("maxLength", "maxItems")
    }
    historical = _historical_lengths()
    derived = sorted(path for path, value in bounds.items() if value in historical)
    if derived:
        raise ValidationError(f"a hard bound equals a length a historical answer had: {derived}")
    properties = schema["properties"]
    return {
        "OUTPUT_SCHEMA_VERSION": SCHEMA_VERSION,
        "OUTPUT_SCHEMA_SHA256": SCHEMA_SHA256,
        "OUTPUT_SCHEMA_CHANGED": False,
        "CANDIDATE_INTERVENTION_CLASS_MAX_LENGTH": properties["candidate_intervention_class"][
            "maxLength"
        ],
        "EVIDENCE_BOUND_REASONING_SUMMARY_MAX_LENGTH": properties[
            "evidence_bound_reasoning_summary"
        ]["maxLength"],
        "HARD_BOUND_FROM_A_HISTORICAL_LENGTH": False,
        "SEMANTIC_GATE_VERSION": GATE_VERSION,
        "SEMANTIC_GATE_IMPLEMENTATION_SHA256": implementation,
        "SEMANTIC_GATE_CHANGED": False,
    }


def independence() -> dict[str, Any]:
    """§4: the headroom modules read no file and carry no length a historical answer had."""
    historical = _historical_lengths()
    for path in HEADROOM_MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = {
            id(owner.body[0].value)
            for owner in ast.walk(tree)
            if isinstance(owner, (ast.Module, ast.ClassDef, ast.FunctionDef))
            and owner.body
            and isinstance(owner.body[0], ast.Expr)
            and isinstance(owner.body[0].value, ast.Constant)
        }
        for node in ast.walk(tree):
            if id(node) in docstrings:
                continue
            if (
                isinstance(node, ast.Constant)
                and type(node.value) is int
                and node.value not in ALLOWED_INTEGERS
            ):
                raise ValidationError(
                    f"{path.name} carries the integer {node.value}"
                    + (", a historical length" if node.value in historical else "")
                    + ". Every bound comes from the schema and every target from the ratio, so a "
                    "number written into the policy is a second copy that drifts"
                )
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and re.search(r"docs/data|synthesis-response|execution-record|\.json\b", node.value)
            ):
                raise ValidationError(f"{path.name} names a data file: {node.value!r}")
            if isinstance(node, ast.Call):
                name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                if name in _FORBIDDEN_CALLS:
                    raise ValidationError(f"{path.name} reads something: {name}()")
    return {
        "V4_VALUES_USED_TO_DERIVE_HEADROOM": False,
        "HEADROOM_MODULES_READ_FILES": False,
        "HEADROOM_MODULES_CARRY_A_HISTORICAL_LENGTH": False,
        "RATIO_SELECTED_BY": "OPERATOR",
        "RATIO_DERIVED_FROM_HISTORY": False,
        "FIELD_SPECIFIC_RATIOS": False,
    }


# ============================================================================= the table


def table() -> dict[str, Any]:
    from sros_opportunity.generation_headroom import (
        ARRAY_HEADROOM_POLICY,
        FIELD_ROLES,
        GENERATION_HEADROOM_POLICY,
        GENERATION_HEADROOM_RENDERER_VERSION,
        GENERATION_TARGET_RATIO,
        QUALITY_FLOOR,
        generation_target,
        headroom_policy_digest,
        headroom_table,
        untargeted_bounds,
    )
    from sros_opportunity.output_constraints import constraint_inventory
    from sros_opportunity.semantic_generation_rules import SEMANTIC_RULE_CENSUS

    if Fraction(4, 5) != GENERATION_TARGET_RATIO or not isinstance(
        GENERATION_HEADROOM_POLICY.ratio, Fraction
    ):
        raise ValidationError("the ratio is not the operator's exact 4/5")
    schema = _schema()
    rows = headroom_table(schema)
    census = {rule.rule_id: rule for rule in SEMANTIC_RULE_CENSUS}
    identity = {f for r in GENERATION_HEADROOM_POLICY.identity_rules for f in census[r].fields}
    eligible = [
        c.path
        for c in constraint_inventory(schema)
        if c.keyword == "maxLength"
        and c.rule == "composed_length"
        and c.path.partition("[]")[0].partition(".")[0] not in identity
    ]
    if [row.path for row in rows] != eligible:
        raise ValidationError("the targeted texts are not exactly the composed ones")
    for row in rows:
        exact = math.floor(Fraction(row.hard_maximum) * Fraction(4, 5))
        if row.generation_target != generation_target(row.hard_maximum) or (
            row.generation_target != exact
        ):
            raise ValidationError(f"{row.path}'s target is not floor(hard * 4/5)")
    untargeted = list(untargeted_bounds(schema))
    return {
        "GENERATION_HEADROOM_POLICY": GENERATION_HEADROOM_POLICY.name,
        "GENERATION_HEADROOM_POLICY_VERSION": GENERATION_HEADROOM_POLICY.version,
        "GENERATION_TARGET_RATIO": GENERATION_HEADROOM_POLICY.ratio_text,
        "GENERATION_TARGET_RATIO_DECIMAL": "0.80",
        "RATIO_REPRESENTATION": "fractions.Fraction(4, 5), exact; targets in integer arithmetic",
        "TARGET_FORMULA": "floor(hard_maximum * 4 / 5)",
        "HEADROOM_IS_VALIDATION": False,
        "APPLIES_TO": {
            "keyword": GENERATION_HEADROOM_POLICY.applies_to_keyword,
            "constraint_rule": GENERATION_HEADROOM_POLICY.applies_to_rule,
            "identity_rules_excluded": list(GENERATION_HEADROOM_POLICY.identity_rules),
        },
        "ARRAY_HEADROOM_POLICY": ARRAY_HEADROOM_POLICY,
        "HEADROOM_TABLE": [{**row.to_json(), "label": row.label} for row in rows],
        "TARGETED_TEXTS": len(rows),
        "UNTARGETED_BOUNDS": untargeted,
        "RENDERER": GENERATION_HEADROOM_RENDERER_VERSION,
        "POLICY_DIGEST": headroom_policy_digest(),
        "FIELD_ROLES": [
            {"field": role.field, "intent": role.intent, "lines": list(role.lines)}
            for role in FIELD_ROLES
        ],
        "QUALITY_FLOOR": list(QUALITY_FLOOR),
    }


def exactness() -> dict[str, Any]:
    """§8: no binary rounding can move a target."""
    from sros_opportunity.generation_headroom import generation_target

    for hard in range(1, HARD_MAXIMA_CHECKED + 1):
        exact = math.floor(Fraction(hard) * Fraction(4, 5))
        if generation_target(hard) != exact or (hard * 4) // 5 != exact:
            raise ValidationError(f"the target of {hard} drifts from floor({hard} * 4/5)")
    return {"HARD_MAXIMA_CHECKED": HARD_MAXIMA_CHECKED, "TARGETS_EXACT": True}


def _with_length(output: dict[str, Any], path: str, length: int) -> dict[str, Any]:
    text = "x" * length
    field, marker, rest = path.partition("[]")
    changed = dict(output)
    if not marker:
        changed[field] = text
    elif not rest:
        changed[field] = [text]
    else:
        first = dict(changed[field][0])
        first[rest.lstrip(".")] = text
        changed[field] = [first, *changed[field][1:]]
    return changed


def boundaries() -> list[dict[str, Any]]:
    """§9, §20: target, target + 1 and the hard maximum pass the schema; hard + 1 fails."""
    from sros_opportunity.generation_headroom import headroom_table
    from sros_opportunity.schema_validation import schema_violations

    fx = _module("fixtures_for_gate_83", FIXTURES)
    schema = _schema()
    out: list[dict[str, Any]] = []
    for row in headroom_table(schema):
        verdicts = {}
        for name, length in (
            ("target", row.generation_target),
            ("target_plus_one", row.generation_target + 1),
            ("hard_maximum", row.hard_maximum),
            ("hard_maximum_plus_one", row.hard_maximum + 1),
        ):
            output = _with_length(fx.good_output(), row.path, length)
            verdicts[name] = "SCHEMA_INVALID" if schema_violations(output, schema) else "PASS"
        expected = {
            "target": "PASS",
            "target_plus_one": "PASS",
            "hard_maximum": "PASS",
            "hard_maximum_plus_one": "SCHEMA_INVALID",
        }
        if verdicts != expected:
            raise ValidationError(f"{row.path}: the soft target and the hard validator disagree")
        out.append(
            {
                "field": row.path,
                "generation_target": row.generation_target,
                "hard_maximum": row.hard_maximum,
                "verdicts": verdicts,
            }
        )
    return out


def drift() -> dict[str, Any]:
    """§19: a bound or the ratio moves exactly the targets it should, and nothing else moves one."""
    from sros_opportunity.generation_headroom import (
        ARRAY_HEADROOM_POLICY,
        GENERATION_HEADROOM_POLICY,
        GenerationHeadroomPolicy,
        generation_target,
        headroom_table,
        render_generation_headroom_block,
    )
    from sros_opportunity.output_constraints import constraint_inventory, mutated_schema

    schema = _schema()
    base_rows = {row.path: row for row in headroom_table(schema)}
    base_block = render_generation_headroom_block(schema)
    failures: list[str] = []
    counts = {"TARGETED_BOUND": 0, "RATIO": 0, "UNTARGETED_LENGTH": 0, "COUNT": 0, "CHOICE": 0}
    for constraint in constraint_inventory(schema):
        keyword = constraint.keyword
        if keyword not in ("maxLength", "maxItems", "enum"):
            continue
        mutated = mutated_schema(schema, constraint)
        if mutated is None:
            continue
        rows = {row.path: row for row in headroom_table(mutated)}
        block = render_generation_headroom_block(mutated)
        if keyword == "maxLength" and constraint.path in base_rows:
            counts["TARGETED_BOUND"] += 1
            hard = base_rows[constraint.path].hard_maximum + 1
            moved = rows[constraint.path]
            others = {p: r for p, r in rows.items() if p != constraint.path}
            if (
                moved.hard_maximum != hard
                or moved.generation_target != generation_target(hard)
                or others != {p: r for p, r in base_rows.items() if p != constraint.path}
                or block == base_block
            ):
                failures.append(f"{constraint.path} maxLength did not move exactly its target")
            continue
        kind = {"maxLength": "UNTARGETED_LENGTH", "maxItems": "COUNT", "enum": "CHOICE"}[keyword]
        counts[kind] += 1
        if rows != base_rows or block != base_block:
            failures.append(f"{constraint.path} {keyword} moved a target")

    def rendered_targets_hold(block: str, rows: Any, ratio: Fraction) -> bool:
        rendered = {m.group(1): (int(m.group(2)), int(m.group(3))) for m in _ROW.finditer(block)}
        expected = {
            r.label: ((r.hard_maximum * ratio.numerator) // ratio.denominator, r.hard_maximum)
            for r in rows
        }
        return rendered == expected

    if not rendered_targets_hold(base_block, headroom_table(schema), Fraction(4, 5)):
        failures.append("a rendered target is not floor(hard * 4/5) of its rendered hard maximum")
    for ratio in MUTATED_RATIOS:
        counts["RATIO"] += 1
        policy = GenerationHeadroomPolicy(
            version="mutated",
            name="mutated",
            ratio=ratio,
            applies_to_keyword="maxLength",
            applies_to_rule=GENERATION_HEADROOM_POLICY.applies_to_rule,
            identity_rules=GENERATION_HEADROOM_POLICY.identity_rules,
            array_headroom=ARRAY_HEADROOM_POLICY,
        )
        rows = headroom_table(schema, policy)
        block = render_generation_headroom_block(schema, policy)
        if (
            [r.generation_target for r in rows]
            != [(r.hard_maximum * ratio.numerator) // ratio.denominator for r in rows]
            or block == base_block
            or not rendered_targets_hold(block, rows, ratio)
        ):
            failures.append(f"the ratio {ratio} did not move every target")
    if failures:
        raise ValidationError(f"HEADROOM_TARGET_DRIFT: {failures}")
    return {"MUTATIONS": counts, "HEADROOM_TARGET_DRIFT": 0}


# ============================================================================= prompt v1.4.0


def regions() -> dict[str, Any]:
    from sros_opportunity.second_opportunity_prompt_v1_3 import second_opportunity_prompt_hash_v1_3
    from sros_opportunity.second_opportunity_prompt_v1_4 import (
        render_second_opportunity_prompt_v1_4,
    )

    snap = _module("gate_81_for_gate_83", GATE_81).snapshot()
    if snap.representation_sha256 != REPRESENTATION_SHA256:
        raise ValidationError("APPROVED_TED_EGRESS_REPRESENTATION_CHANGED")
    if second_opportunity_prompt_hash_v1_3(snap.parts_v1_3) != PROMPT_V1_3_SHA256:
        raise ValidationError("prompt v1.3.0 no longer renders to its frozen digest")
    fx = _module("fixtures_for_gate_83_regions", FIXTURES)
    synthetic = render_second_opportunity_prompt_v1_4(
        fx.packet(), fx.statements(), fx.EVIDENCE_TO_CLAIM, source_metadata=fx.metadata()
    )
    return {
        "snap": snap,
        "v1_3": snap.parts_v1_3,
        "v1_4": render_second_opportunity_prompt_v1_4(
            snap.packet, snap.statements, snap.pairs, source_metadata=snap.metadata
        ),
        "synthetic": synthetic,
    }


def _flat(text: str) -> str:
    return " ".join(text.split())


def prompt_checks(parts: Mapping[str, Any]) -> dict[str, Any]:
    from sros_opportunity.generation_headroom import (
        FIELD_ROLES,
        QUALITY_FLOOR,
        headroom_table,
        unstated_headroom,
    )
    from sros_opportunity.output_constraints import (
        MUST_BE_EXPLICIT_IN_PROMPT,
        constraint_inventory,
        is_explicit,
    )
    from sros_opportunity.second_opportunity_prompt_v1_4 import GENERATION_HEADROOM_BLOCK_V1_4
    from sros_opportunity.semantic_generation_rules import unstated_semantic_rules

    schema = _schema()
    v13, v14 = parts["v1_3"], parts["v1_4"]
    system = str(v14.system_instructions)
    if not system.startswith(str(v13.system_instructions)):
        raise ValidationError("prompt v1.3.0's system region is not a byte-identical prefix")
    added = system[len(str(v13.system_instructions)) :]
    if added != "\n" + GENERATION_HEADROOM_BLOCK_V1_4 + "\n":
        raise ValidationError("prompt v1.4.0 adds something other than the headroom block")
    for region in ("trusted_context", "untrusted", "task"):
        if getattr(v14, region) != getattr(v13, region):
            raise ValidationError(f"the {region} moved between v1.3.0 and v1.4.0")
    unstated_schema = [
        f"{c.path} {c.keyword}"
        for c in constraint_inventory(schema)
        if c.constraint_class == MUST_BE_EXPLICIT_IN_PROMPT and not is_explicit(c, system)
    ]
    unstated_rules = unstated_semantic_rules(system, v14.trusted_context, v14.task)
    unstated_targets = unstated_headroom(system, schema)
    unstated_v13 = unstated_headroom(str(v13.system_instructions), schema)
    rows = headroom_table(schema)
    if unstated_schema or unstated_rules or unstated_targets:
        raise ValidationError(
            f"prompt v1.4.0 leaves {unstated_schema + unstated_rules + unstated_targets} unstated"
        )
    if len(unstated_v13) != len(rows):
        raise ValidationError("the headroom check would pass prompt v1.3.0")
    flat = _flat(added)
    phrases = (
        "never a limit of the contract",
        "still valid and is not refused",
        "only a text longer than its hard maximum is refused",
        "write no count, draft or working anywhere in it",
        "it may exceed the target, and it still stays within its hard maximum",
        "more confident than the evidence allows, or harder to audit",
        "element counts keep the exact limits stated above",
    )
    missing = [p for p in phrases if p not in flat]
    missing += [line for role in FIELD_ROLES for line in role.lines if _flat(line) not in flat]
    missing += [item for item in QUALITY_FLOOR if item not in flat]
    if missing:
        raise ValidationError(f"the headroom block no longer says {missing}")
    for row in rows:
        line = next((ln for ln in added.split("\n") if ln.startswith(f"  {row.label}: ")), "")
        if "generation target" not in line or "hard maximum" not in line:
            raise ValidationError(f"{row.path}'s target and hard maximum are not stated distinctly")
    exposure = {
        "HISTORICAL_LENGTH_IN_ADDED_TEXT": any(
            re.search(rf"\b{n}\b", added) for n in _historical_lengths()
        ),
        "HISTORICAL_EXECUTION_NAMED_IN_ADDED_TEXT": re.search(r"\bV[1-4]\b", added) is not None,
        "WORD_TENDER_IN_ADDED_TEXT": "tender" in added.lower(),
        "SOURCE_NAME_HARD_CODED_IN_SYSTEM_REGION": "Tenders Electronic Daily" in system,
        "SYSTEM_REGION_PACKET_INDEPENDENT": system == str(parts["synthetic"].system_instructions),
    }
    if exposure != {
        "HISTORICAL_LENGTH_IN_ADDED_TEXT": False,
        "HISTORICAL_EXECUTION_NAMED_IN_ADDED_TEXT": False,
        "WORD_TENDER_IN_ADDED_TEXT": False,
        "SOURCE_NAME_HARD_CODED_IN_SYSTEM_REGION": False,
        "SYSTEM_REGION_PACKET_INDEPENDENT": True,
    }:
        raise ValidationError(f"the prompt exposes what it must not: {exposure}")
    return {
        "UNSTATED_GENERATION_CONSTRAINTS": 0,
        "UNSTATED_GENERATION_RELEVANT_SEMANTIC_RULES": 0,
        "UNSTATED_GENERATION_TARGETS": 0,
        "PROMPT_V1_3_UNSTATED_GENERATION_TARGETS": len(unstated_v13),
        "SOFT_TARGET_AND_HARD_MAXIMUM_STATED_DISTINCTLY": True,
        "SELF_CHECK_STATED": True,
        "SCRATCHPAD_REQUESTED": False,
        "SEPARATE_SELF_CRITIQUE_CALL": False,
        "EXPOSURE": exposure,
    }


def native() -> dict[str, Any]:
    """§21: what the held register says about native structured outputs, and nothing more."""
    register = _load(CAPABILITY)
    model = register["MODELS"]["claude-sonnet-5"]
    held = json.dumps(register)
    return {
        "NATIVE_STRUCTURED_OUTPUTS_SUPPORTED": model["NATIVE_STRUCTURED_OUTPUTS_SUPPORTED"],
        "NATIVE_PROVIDER_MAX_LENGTH_ENFORCEMENT": (
            "NOT_HELD" if "maxLength" not in held and "constrained" not in held else "SEE_REGISTER"
        ),
        "STRUCTURED_OUTPUT_MECHANISM": "FORCED_TOOL_USE",
        "PROVIDER_MECHANISM_MIGRATED": False,
        "DOCUMENTATION_REFRESHED": False,
        "note": (
            "The capability register records that native structured outputs are supported and "
            "records nothing, from any reviewed page, about whether they enforce maxLength. That "
            "fact is not held, no documentation was fetched, and the forced tool and the local "
            "validator stay the mechanism"
        ),
    }


def stages() -> dict[str, Any]:
    gate_80 = _module("gate_80_for_gate_83", GATE_80)
    try:
        record = gate_80.validate()
    except gate_80.ValidationError as exc:
        raise ValidationError(f"DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY: {exc}") from exc
    if record["OUTCOME"] != gate_80.READY:
        raise ValidationError("DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY")
    return {"STAGE_6_TO_9_PREFLIGHT": record["OUTCOME"], "RUNNER": record["RUNNER"]}


def _untrusted_sha(parts: Any) -> str:
    return _sha(
        json.dumps([list(p) for p in parts.untrusted], ensure_ascii=False, separators=(",", ":"))
    )


def prompt_record(parts: Mapping[str, Any]) -> dict[str, Any]:
    from sros_opportunity.generation_headroom import (
        FIELD_ROLE_POLICY_VERSION,
        GENERATION_HEADROOM_RENDERER_VERSION,
        headroom_policy_digest,
    )
    from sros_opportunity.second_opportunity import (
        SECOND_OPPORTUNITY_PROCEDURE_VERSION,
        SECOND_OPPORTUNITY_PROMPT_ID,
    )
    from sros_opportunity.second_opportunity_prompt_v1_4 import (
        GENERATION_HEADROOM_BLOCK_V1_4,
        SECOND_OPPORTUNITY_PROMPT_VERSION_V1_4,
        second_opportunity_prompt_hash_v1_4,
    )

    v13, v14, snap = parts["v1_3"], parts["v1_4"], parts["snap"]
    system = str(v14.system_instructions)
    added = system[len(str(v13.system_instructions)) :]
    return {
        "$comment": (
            "Mission 1.84.14. The v1.4.0 prompt regions over the authenticated packet snapshot, "
            "frozen and hashed and never transmitted. Prompt v1.3.0 and its record are not edited."
        ),
        "record_version": "second-opportunity-synthesis-prompt@1.4.0",
        "mission": "1.84.14",
        "recorded_by": MISSION,
        "PROMPT_ID": SECOND_OPPORTUNITY_PROMPT_ID,
        "PROMPT_VERSION": SECOND_OPPORTUNITY_PROMPT_VERSION_V1_4,
        "PROCEDURE": SECOND_OPPORTUNITY_PROCEDURE_VERSION,
        "PROMPT_SHA256": second_opportunity_prompt_hash_v1_4(v14),
        "PREDECESSOR_PROMPT_VERSION": "1.3.0",
        "PREDECESSOR_PROMPT_SHA256": PROMPT_V1_3_SHA256,
        "PREDECESSOR_UNCHANGED": True,
        "SUBJECT": SUBJECT,
        "PACKET_ID": snap.packet.packet_id,
        "GENERATION_HEADROOM_RENDERER": GENERATION_HEADROOM_RENDERER_VERSION,
        "FIELD_ROLE_POLICY": FIELD_ROLE_POLICY_VERSION,
        "GENERATION_HEADROOM_POLICY_DIGEST": headroom_policy_digest(),
        "SYSTEM_INSTRUCTION": system,
        "SYSTEM_SHA256": _sha(system),
        "PREDECESSOR_SYSTEM_SHA256": _sha(str(v13.system_instructions)),
        "HEADROOM_BLOCK": GENERATION_HEADROOM_BLOCK_V1_4,
        "HEADROOM_BLOCK_SHA256": _sha(GENERATION_HEADROOM_BLOCK_V1_4),
        "TRUSTED_CONTEXT_SHA256": _sha(str(v14.trusted_context)),
        "TASK_SHA256": _sha(str(v14.task)),
        "UNTRUSTED_SHA256": _untrusted_sha(v14),
        "UNTRUSTED_ITEMS": len(v14.untrusted),
        "REGIONS_IDENTICAL_TO_V1_3_0": ["trusted_context", "untrusted", "task"],
        "REGIONS_EXTENDED_VERBATIM": ["system_instructions"],
        "SEMANTIC_DIFF": {
            "SYSTEM_ADDED_LINES": len([ln for ln in added.split("\n") if ln.strip()]),
            "SYSTEM_REMOVED_LINES": 0,
            "OUTPUT_CONTRACT_BLOCK_UNCHANGED": True,
            "SEMANTIC_BLOCK_UNCHANGED": True,
            "SOURCE_NAMES_SECTION_UNCHANGED": True,
        },
        "OUTPUT_SCHEMA_VERSION": SCHEMA_VERSION,
        "OUTPUT_SCHEMA_SHA256": SCHEMA_SHA256,
        "OUTPUT_GATE_VERSION": GATE_VERSION,
        "TED_REPRESENTATION_SHA256": REPRESENTATION_SHA256,
        "TED_REPRESENTATION_UNCHANGED": True,
        "SENT": False,
        "sent_note": (
            "This document records regions that were frozen and never transmitted. Execution "
            "packet V5 binds this prompt version, no approval names V5, and 0 provider requests "
            "were made by the mission that wrote it"
        ),
    }


def build_records() -> tuple[dict[str, Any], dict[str, Any]]:
    from sros_opportunity.generation_headroom import OPERATOR_DECISION_GENERATION_HEADROOM

    parts = regions()
    prompt = prompt_record(parts)
    record: dict[str, Any] = {
        "$comment": (
            "Mission 1.84.14. The operator's generation-headroom policy, the targets derived from the "
            "live schema, the proofs that a target is not validation and that nothing but a bound or "
            "the ratio moves one, and prompt v1.4.0's checks. CI gate 83 re-derives every field."
        ),
        "record_version": "second-opportunity-generation-headroom-policy-record@1.0.0",
        "mission": MISSION,
        "OPERATOR_DECISION": list(OPERATOR_DECISION_GENERATION_HEADROOM),
        "HISTORY_UNCHANGED": history(),
        "V4": v4_facts(),
        **contract(),
        "PROMPT_V1_3_SHA256": PROMPT_V1_3_SHA256,
        "PROMPT_V1_3_CHANGED": False,
        "INDEPENDENCE": independence(),
        **table(),
        "EXACTNESS": exactness(),
        "BOUNDARIES": boundaries(),
        "DRIFT": drift(),
        "PROMPT": prompt_checks(parts),
        "PROMPT_V1_4_SHA256": prompt["PROMPT_SHA256"],
        "PROMPT_V1_4_RECORD": PROMPT_RECORD.name,
        "NATIVE_STRUCTURED_OUTPUT": native(),
        "STAGES": stages(),
        "REPRESENTATION_SHA256": REPRESENTATION_SHA256,
        "REPRESENTATION_CHARACTERS": REPRESENTATION_CHARACTERS,
        "REPRESENTATION_CHANGED": False,
        "accounting": dict(ZERO_ACCOUNTING),
    }
    return record, prompt


def validate() -> tuple[dict[str, Any], dict[str, Any]]:
    record, prompt = build_records()
    for path, built in ((RECORD, record), (PROMPT_RECORD, prompt)):
        if not path.exists():
            raise ValidationError(f"{path.name} does not exist; run --write")
        if _load(path) != built:
            raise ValidationError(f"{path.name} is not what the live code derives")
    return record, prompt


# ============================================================================= rendering

HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_generation_headroom.py "
    "from {source}. Do not edit by hand; edit the code and re-render. -->\n\n"
)


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def render(record: Mapping[str, Any]) -> str:
    v4 = record["V4"]
    out = [
        HEADER.format(source=RECORD.name),
        "# Second opportunity: generation headroom policy",
        "",
        f"**{record['GENERATION_HEADROOM_POLICY']}**, ratio **{record['GENERATION_TARGET_RATIO']}** "
        f"({record['RATIO_REPRESENTATION']}). Selected by the operator; not derived from any answer.",
        "",
        "## The operator's decision",
        "",
        *[f"- `{line}`" for line in record["OPERATOR_DECISION"]],
        "",
        "## V4, historical and unchanged",
        "",
        f"`{v4['V4_OUTCOME']}`; approval consumed; stages 6 to 10 NOT_REACHED; candidate false. "
        "The live v1.1.0 validator reproduces its two violations:",
        "",
        *[f"- `{v}`" for v in v4["V4_HISTORICAL_VIOLATIONS_REPRODUCED"]],
        "",
        "## Targets, from the live schema",
        "",
        "| field | hard maximum | generation target | classification |",
        "|---|---|---|---|",
        *[
            f"| `{row['field']}` | {row['hard_maximum']} | {row['generation_target']} | "
            f"{row['constraint_classification']} |"
            for row in record["HEADROOM_TABLE"]
        ],
        "",
        "Every target is `floor(hard maximum * 4/5)`, computed by one function in integer "
        "arithmetic. A target is guidance for writing: target, target + 1 and the hard maximum "
        "all pass the schema, and hard maximum + 1 fails, for every row.",
        "",
        "## No target",
        "",
        "| field | bound | why |",
        "|---|---|---|",
        *[
            f"| `{e['field']}` | {e['keyword']} {e['hard_bound']} | {e['reason']} |"
            for e in record["UNTARGETED_BOUNDS"]
        ],
        "",
        f"Array headroom: `{record['ARRAY_HEADROOM_POLICY']}`.",
        "",
        "## Field roles",
        "",
        *[f"- `{role['field']}`: `{role['intent']}`" for role in record["FIELD_ROLES"]],
        "",
        "## Drift",
        "",
        *_code([f"{k:20s} {v}" for k, v in record["DRIFT"]["MUTATIONS"].items()]),
        f"`HEADROOM_TARGET_DRIFT = {record['DRIFT']['HEADROOM_TARGET_DRIFT']}`.",
        "",
        "## Prompt v1.4.0",
        "",
        f"`{record['PROMPT_V1_4_SHA256']}`: v1.3.0 (`{record['PROMPT_V1_3_SHA256'][:8]}...`) byte "
        "for byte, plus the headroom block. Unstated schema bounds, class-A rules and targets: "
        f"{record['PROMPT']['UNSTATED_GENERATION_CONSTRAINTS']}, "
        f"{record['PROMPT']['UNSTATED_GENERATION_RELEVANT_SEMANTIC_RULES']}, "
        f"{record['PROMPT']['UNSTATED_GENERATION_TARGETS']}.",
        "",
        f"Native provider maxLength enforcement: "
        f"`{record['NATIVE_STRUCTURED_OUTPUT']['NATIVE_PROVIDER_MAX_LENGTH_ENFORCEMENT']}`. Stages 6 "
        f"to 9: `{record['STAGES']['STAGE_6_TO_9_PREFLIGHT']}`.",
        "",
        "Accounting: "
        + ", ".join(f"{k.lower()} {v}" for k, v in record["accounting"].items())
        + ".",
        "",
    ]
    return "\n".join(out)


def render_prompt(prompt: Mapping[str, Any]) -> str:
    out = [
        HEADER.format(source=PROMPT_RECORD.name),
        f"# Second opportunity: synthesis prompt v{prompt['PROMPT_VERSION']}",
        "",
        f"`{prompt['PROMPT_SHA256']}`. Predecessor v{prompt['PREDECESSOR_PROMPT_VERSION']} "
        f"`{prompt['PREDECESSOR_PROMPT_SHA256']}`, unchanged. Never sent.",
        "",
        "## The block added to the system region",
        "",
        *_code(str(prompt["HEADROOM_BLOCK"]).split("\n")),
        "The trusted context, the untrusted TED statements and the task are v1.3.0's, byte for byte.",
        "",
    ]
    return "\n".join(out)


def _write_json(path: pathlib.Path, data: Mapping[str, Any]) -> None:
    path.write_bytes((json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write:
            record, prompt = build_records()
            _write_json(RECORD, record)
            _write_json(PROMPT_RECORD, prompt)
            RECORD_MD.write_bytes(render(record).encode("utf-8"))
            PROMPT_RECORD_MD.write_bytes(render_prompt(prompt).encode("utf-8"))
            print(f"wrote    {RECORD.name}, {PROMPT_RECORD.name} and their pages")
        record, prompt = validate()
    except ValidationError as exc:
        print(f"FAIL     {exc}")
        return 1
    for path, text in ((RECORD_MD, render(record)), (PROMPT_RECORD_MD, render_prompt(prompt))):
        if path.read_text(encoding="utf-8") != text:
            print(f"FAIL     {path.name} is not the rendering of its record")
            return 1
    print(
        "ok       every composed text has a target derived from its live hard bound under the "
        "operator's 4/5, and prompt v1.4.0 states each beside its hard maximum"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
