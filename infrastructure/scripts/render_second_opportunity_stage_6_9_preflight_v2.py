"""Mission 1.84.17, CI gate 89: stages 5 to 9 of the V6 runner, and every retention path, synthetic.

Gate 80 proved stages 6 to 9 of the V4 runner on synthetic answers. The V6 runner judges at stage 5
with schema v1.2.0 and at stage 6 with gate v1.4.0, so its path is proved again, with the real
machinery and nothing stubbed:

    gate 80's fixtures (A to E), each at the stage it was written for under the V6 stage names;
    F  the fixture's own summary, repeated past v1.1.0's bound   passes 5 to 8, eligible at 9
    G  the same summary with one unsupported sentence            passes 5, refused at 6
    H  a summary at exactly v1.2.0's bound                       passes 5 to 8, eligible at 9
    I  one character over v1.2.0's bound                         refused at 5

and then `settle`, the path that keeps what arrived, over every terminal path an execution can take:
a complete response, a timeout, a provider refusal, both output-limit stops, an unsupported stop, a
parse, schema or semantic failure, a stage 7, 8 or 9 failure, and an answer ready for human review.

    uv run python infrastructure/scripts/render_second_opportunity_stage_6_9_preflight_v2.py --check

**A synthetic pass is not evidence.** It shows the stages accept a well-formed answer, including one
the old bound refused, and refuse each failure at the stage built for it. It says nothing about what a
model will write.

The gate refuses: a fixture that stops at another stage, or whose later stages are not NOT_REACHED; a
long summary within the new bound that does not reach stage 9, or one with a semantic violation that
is not refused at 6; a runner whose stage 5 is not schema v1.2.0 or whose stage 6 is not gate v1.4.0,
whose gate can be injected, or which cannot refuse at stages 5 to 9; a retention path whose artifact
does not carry its terminal outcome, loses the response that arrived, or persists anything; the real
transport constructed; and a record field the code does not derive.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import inspect
import json
import pathlib
import sys
from collections.abc import Mapping
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
sys.path.insert(0, str(SCRIPTS))

RECORD = DATA / "second-opportunity-stage-6-9-preflight-v2.json"
RECORD_MD = DATA / "second-opportunity-stage-6-9-preflight-v2.md"
RUNNER_V6 = SCRIPTS / "run_second_opportunity_execution_v6.py"
FIXTURES = SCRIPTS / "second_opportunity_synthetic_fixtures.py"
GATE_76 = SCRIPTS / "render_second_opportunity_v3_diagnostic_replay.py"
GATE_80 = SCRIPTS / "render_second_opportunity_stage_6_9_preflight.py"
MISSION = "mission-1.84.17"
SUMMARY = "evidence_bound_reasoning_summary"
#: A sentence the semantic gate refuses whatever the summary's length: no statement supplies it.
VIOLATION = " Buyers are willing to pay."
#: Gate 86's demonstration: the fixture's own summary repeated five times, so no word is new.
REPETITIONS = 5

READY = "DETERMINISTIC_STAGE_6_TO_9_PATH_READY"
NOT_READY = "DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY"
RETENTION_READY = "RETENTION_PATH_READY_FOR_NEXT_EXECUTION"
ZERO_ACCOUNTING = {
    "MODEL_CALLS": 0,
    "PROVIDER_REQUESTS": 0,
    "MESSAGES_API_REQUESTS": 0,
    "TOKEN_COUNT_API_REQUESTS": 0,
    "TED_BYTES_SENT": 0,
    "CANONICAL_MUTATIONS": 0,
}


class ValidationError(RuntimeError):
    """The preflight record disagrees with the V6 runner run over the fixtures."""


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bounds() -> tuple[int, int]:
    from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
    from sros_opportunity.second_opportunity_schema_v1_2 import (
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2,
    )

    def bound(schema: Mapping[str, Any]) -> int:
        return int(schema["properties"][SUMMARY]["maxLength"])

    return bound(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1), bound(
        SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2
    )


def _judge(source: str) -> ast.FunctionDef:
    tree = ast.parse(source)
    judge = next(
        (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "validate_execution"),
        None,
    )
    if judge is None:
        raise ValidationError("the V6 runner has no validate_execution")
    return judge


def _structure(source: str, stages: list[str]) -> dict[str, Any]:
    """What stages 5 and 6 are, read from the syntax of the stage function, and where it refuses."""
    gate_80 = _module("gate_80_for_gate_89", GATE_80)
    judge = _judge(source)
    calls = {
        getattr(node.func, "id", None): node
        for node in ast.walk(judge)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    schema = calls.get("schema_violations")
    schema_name = getattr(schema.args[1], "id", None) if schema and len(schema.args) == 2 else None
    if schema_name != "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2":
        raise ValidationError(f"the V6 runner's stage 5 validates against {schema_name}")
    if "evaluate_second_opportunity_output_v1_4" not in calls or (
        "evaluate_second_opportunity_output_v1_3" in calls
    ):
        raise ValidationError("the V6 runner's stage 6 is not gate v1.4.0 alone")
    refusing = [index for index in range(4, 9) if gate_80._refuses_at(source, index)]
    if refusing != [4, 5, 6, 7, 8]:
        raise ValidationError(f"the V6 runner refuses only at {[stages[i] for i in refusing]}")
    return {
        "STAGE_5_SCHEMA": "SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_2",
        "STAGE_6_GATE": "evaluate_second_opportunity_output_v1_4",
        "REFUSES_AT": [stages[i] for i in refusing],
    }


def fixtures(fx: Any) -> list[tuple[str, str, str | None, dict[str, Any], dict[str, Any]]]:
    """(id, what it is, the stage it must stop at or None, result, context)."""
    gate_80 = _module("gate_80_fixtures_for_gate_89", GATE_80)
    renamed = {"6_semantic_output_gate_v1_3_0": "6_semantic_output_gate_v1_4_0"}
    out = [
        (fixture_id, what, renamed.get(stage, stage) if stage else None, result, context)
        for fixture_id, what, stage, result, context in gate_80.fixtures(fx)
    ]
    _old, new = _bounds()
    long_summary = " ".join([fx.good_output()[SUMMARY]] * REPETITIONS)
    out += [
        (
            "F_LONG_SUMMARY_POSITIVE",
            "the fixture's own summary repeated, longer than v1.1.0's bound and within v1.2.0's",
            None,
            fx.recorded_result(fx.good_output(**{SUMMARY: long_summary})),
            fx.runner_context(),
        ),
        (
            "G_LONG_SUMMARY_SEMANTIC_NEGATIVE",
            "the same long summary with one sentence no supplied statement supports",
            "6_semantic_output_gate_v1_4_0",
            fx.recorded_result(fx.good_output(**{SUMMARY: long_summary + VIOLATION})),
            fx.runner_context(),
        ),
        (
            "H_SUMMARY_AT_THE_NEW_BOUND",
            "a summary of exactly v1.2.0's bound",
            None,
            fx.recorded_result(fx.good_output(**{SUMMARY: "y" * new})),
            fx.runner_context(),
        ),
        (
            "I_SUMMARY_ONE_OVER_THE_NEW_BOUND",
            "a summary one character over v1.2.0's bound",
            "5_schema_validation_v1_2_0",
            fx.recorded_result(fx.good_output(**{SUMMARY: "y" * (new + 1)})),
            fx.runner_context(),
        ),
    ]
    return out


def retention_cases(fx: Any) -> list[tuple[str, str, dict[str, Any], dict[str, Any], bool]]:
    """(path, the terminal outcome it must carry, result, context, whether a response arrived)."""
    by_id = {f[0]: f for f in fixtures(fx)}
    good = fx.good_output()
    timeout = {
        "response": None,
        "failure": TimeoutError("synthetic timeout"),
        "transport_responses": [],
        "transport_errors": ["TimeoutError: synthetic timeout"],
        "telemetry": [],
        "timing": {"started_at": "synthetic", "finished_at": "synthetic", "elapsed_seconds": 0.0},
    }

    def fixture(fixture_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        return by_id[fixture_id][3], by_id[fixture_id][4]

    context = fx.runner_context()
    return [
        ("success", "EXECUTION_OUTPUT_ACCEPTED_AWAITING_HUMAN_REVIEW", *fixture("A_VALID"), True),
        ("timeout", "EXECUTION_FAILED_TIMEOUT_NO_RETRY", timeout, context, False),
        (
            "provider_refusal",
            "EXECUTION_REFUSED_BY_PROVIDER_NO_RETRY",
            fx.recorded_result(good, stop_reason="refusal"),
            context,
            True,
        ),
        (
            "provider_output_limit_max_tokens",
            "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY",
            fx.recorded_result(good, stop_reason="max_tokens"),
            context,
            True,
        ),
        (
            "provider_output_limit_context_window",
            "EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY",
            fx.recorded_result(good, stop_reason="model_context_window_exceeded"),
            context,
            True,
        ),
        (
            "unsupported_stop_reason",
            "EXECUTION_STOP_REASON_UNSUPPORTED_NO_RETRY",
            fx.recorded_result(good, stop_reason="end_turn"),
            context,
            True,
        ),
        (
            "parse_failure",
            "EXECUTION_OUTPUT_REJECTED_AT_STRUCTURED_PARSE_NO_RETRY",
            fx.recorded_result(None),
            context,
            True,
        ),
        (
            "schema_failure",
            "EXECUTION_OUTPUT_REJECTED_AT_SCHEMA_VALIDATION_NO_RETRY",
            *fixture("I_SUMMARY_ONE_OVER_THE_NEW_BOUND"),
            True,
        ),
        (
            "semantic_failure",
            "EXECUTION_OUTPUT_REJECTED_AT_SEMANTIC_GATE_NO_RETRY",
            *fixture("G_LONG_SUMMARY_SEMANTIC_NEGATIVE"),
            True,
        ),
        (
            "evidence_boundary_failure",
            "EXECUTION_OUTPUT_REJECTED_AT_EVIDENCE_BOUNDARY_NO_RETRY",
            *fixture("C_EVIDENCE_BOUNDARY_FAILURE"),
            True,
        ),
        (
            "provenance_failure",
            "EXECUTION_OUTPUT_REJECTED_AT_ATTRIBUTION_NO_RETRY",
            *fixture("D_ATTRIBUTION_FAILURE"),
            True,
        ),
        (
            "persistence_eligibility_failure",
            "EXECUTION_OUTPUT_REJECTED_AT_PERSISTENCE_ELIGIBILITY_NO_RETRY",
            *fixture("E_PERSISTENCE_ELIGIBILITY_FAILURE"),
            True,
        ),
        (
            "human_review_ready_success",
            "EXECUTION_OUTPUT_ACCEPTED_AWAITING_HUMAN_REVIEW",
            *fixture("F_LONG_SUMMARY_POSITIVE"),
            True,
        ),
    ]


def run() -> dict[str, Any]:
    runner = _module("runner_v6_for_gate_89", RUNNER_V6)
    fx = _module("fixtures_for_gate_89", FIXTURES)
    gate_76 = _module("gate_76_for_gate_89", GATE_76)
    stages = list(runner.STAGES)
    if stages[4:6] != ["5_schema_validation_v1_2_0", "6_semantic_output_gate_v1_4_0"]:
        raise ValidationError(f"the V6 runner's stages 5 and 6 are {stages[4:6]}")
    signature = list(inspect.signature(runner.validate_execution).parameters)
    if signature != ["result", "context"]:
        raise ValidationError(f"the V6 stage function takes {signature}; no gate may be injected")
    structure = _structure(RUNNER_V6.read_text(encoding="utf-8"), stages)
    old, new = _bounds()
    results: list[dict[str, Any]] = []
    retention: dict[str, dict[str, Any]] = {}
    with gate_76.no_transport():
        for fixture_id, description, intended, result, context in fixtures(fx):
            report = runner.validate_execution(result, context)
            failed = report["failed_stage"]
            if failed != intended:
                raise ValidationError(f"{fixture_id} stopped at {failed}, not {intended}")
            if intended is not None:
                after = stages[stages.index(intended) + 1 :]
                if any(report["stages"][s] != "NOT_REACHED" for s in after):
                    raise ValidationError(f"{fixture_id}: a stage after {intended} was reached")
            elif (
                report["stages"]["9_persistence_eligibility"] != "ELIGIBLE_FOR_HUMAN_REVIEW_ONLY"
                or report["stages"]["10_human_review"] != "REQUIRED_NOT_PERFORMED"
            ):
                raise ValidationError(f"{NOT_READY}: {fixture_id} does not reach stage 9")
            summary = str(
                json.loads(result["transport_responses"][0]["body"])["content"][1]["input"][SUMMARY]
            )
            if fixture_id.startswith(("F_", "G_", "H_")) and (
                report["stages"]["5_schema_validation_v1_2_0"] != "PASSED"
            ):
                raise ValidationError(
                    f"{fixture_id}: a summary within v1.2.0's bound fails stage 5"
                )
            if fixture_id.startswith("G_") and any("maxLength" in r for r in report["reasons"]):
                raise ValidationError(
                    "the long negative is refused for its length, not its content"
                )
            results.append(
                {
                    "fixture": fixture_id,
                    "what": description,
                    "summary_characters": len(summary),
                    "intended_stage": intended or "NONE_ELIGIBLE_AT_9",
                    "failed_stage": failed,
                    "outcome": report["outcome"],
                    "stages": {k: v for k, v in report["stages"].items() if k[:1] in "56789"}
                    | {"10_human_review": report["stages"]["10_human_review"]},
                    "reasons": list(report["reasons"]),
                    "MISREPORTED_AS_A_LATER_STAGE": False,
                }
            )
        for path, expected, result, context, arrived in retention_cases(fx):
            report, text = runner.settle(result, context)
            artifact = json.loads(text)
            if report["outcome"] != expected or artifact.get("TERMINAL_OUTCOME") != expected:
                raise ValidationError(
                    f"RETENTION_PATH_NOT_READY_FOR_NEXT_EXECUTION: {path} ends "
                    f"{report['outcome']}, not {expected}"
                )
            if artifact.get("POST_CALL_HANDLING_FAILED"):
                raise ValidationError(
                    f"RETENTION_PATH_NOT_READY_FOR_NEXT_EXECUTION: {path} fell back"
                )
            if artifact.get("RAW_PROVIDER_RESPONSE_RETAINED") is not arrived:
                raise ValidationError(
                    f"RETENTION_PATH_NOT_READY_FOR_NEXT_EXECUTION: {path} does not keep what arrived"
                )
            if artifact.get("PERSISTED") != "NOTHING":
                raise ValidationError(f"{path} persists something")
            retention[path] = {
                "terminal_outcome": expected,
                "raw_response_retained": arrived,
                "stop_reason": artifact.get("STOP_REASON"),
                "persisted": "NOTHING",
            }
    by_id = {r["fixture"]: r for r in results}
    return {
        "$comment": (
            "Mission 1.84.17. Stages 5 to 9 of the V6 runner and every retention path, run over "
            "synthetic responses with schema v1.2.0, gate v1.4.0, the real provenance reading and "
            "the real OpportunityHypothesis constructor. A synthetic pass is not evidence about a "
            "model's answer. CI gate 89 re-derives every field."
        ),
        "record_version": "second-opportunity-stage-6-9-preflight@2.0.0",
        "mission": MISSION,
        "RUNNER": RUNNER_V6.name,
        "STAGES": stages,
        "STRUCTURE": structure,
        "SEMANTIC_GATE_INJECTABLE": False,
        "STUBS_USED": False,
        "REAL_TRANSPORT_CONSTRUCTED": False,
        "SUMMARY_BOUNDS": {"v1_1_0": old, "v1_2_0": new},
        "FIXTURES": results,
        "VALID_FIXTURE_REACHES_STAGE_9": True,
        "EVERY_NEGATIVE_FIXTURE_AT_ITS_INTENDED_STAGE": True,
        "LONG_SUMMARY": {
            "POSITIVE_CHARACTERS": by_id["F_LONG_SUMMARY_POSITIVE"]["summary_characters"],
            "POSITIVE_REACHES_STAGE_9": True,
            "NEGATIVE_CHARACTERS": by_id["G_LONG_SUMMARY_SEMANTIC_NEGATIVE"]["summary_characters"],
            "NEGATIVE_PASSES_STAGE_5": True,
            "NEGATIVE_REFUSED_AT_STAGE_6": True,
            "AT_THE_NEW_BOUND_REACHES_STAGE_9": True,
            "ONE_OVER_THE_NEW_BOUND_REFUSED_AT_STAGE_5": True,
        },
        "RETENTION_PATHS": retention,
        "RETENTION_OUTCOME": RETENTION_READY,
        "OUTCOME": READY,
        "SYNTHETIC_PASS_IS_NOT_EVIDENCE": True,
        "accounting": dict(ZERO_ACCOUNTING),
    }


def validate() -> dict[str, Any]:
    built = run()
    if not RECORD.exists():
        raise ValidationError(f"{RECORD.name} does not exist; run --write")
    if _load(RECORD) != json.loads(json.dumps(built)):
        raise ValidationError(f"{RECORD.name} is not what the V6 runner derives")
    return built


HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_stage_6_9_preflight_v2.py "
    "from {source}. Do not edit by hand; edit the code and re-render. -->\n\n"
)


def render(record: Mapping[str, Any]) -> str:
    out = [
        HEADER.format(source=RECORD.name),
        "# Second opportunity: stages 5 to 9 of the V6 runner, preflight",
        "",
        f"**{record['OUTCOME']}; {record['RETENTION_OUTCOME']}.** The V6 runner's own stages, over "
        "synthetic responses, with schema v1.2.0 at stage 5, gate v1.4.0 at stage 6 and nothing "
        "stubbed. **A synthetic pass is not evidence** about what a model will write.",
        "",
        "| fixture | summary characters | intended stage | stopped at | outcome |",
        "|---|---|---|---|---|",
        *[
            f"| `{f['fixture']}` | {f['summary_characters']} | `{f['intended_stage']}` | "
            f"`{f['failed_stage'] or 'none'}` | `{f['outcome']}` |"
            for f in record["FIXTURES"]
        ],
        "",
        "| retention path | terminal outcome | response kept |",
        "|---|---|---|",
        *[
            f"| `{path}` | `{r['terminal_outcome']}` | {str(r['raw_response_retained']).lower()} |"
            for path, r in record["RETENTION_PATHS"].items()
        ],
        "",
        "Accounting: "
        + ", ".join(f"{k.lower()} {v}" for k, v in record["accounting"].items())
        + ".",
        "",
    ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write:
            built = run()
            RECORD.write_bytes((json.dumps(built, indent=2, ensure_ascii=False) + "\n").encode())
            RECORD_MD.write_bytes(render(built).encode("utf-8"))
            print(f"wrote    {RECORD.name} and {RECORD_MD.name}")
        record = validate()
    except ValidationError as exc:
        print(f"FAIL     {exc}")
        return 1
    if RECORD_MD.read_text(encoding="utf-8") != render(record):
        print(f"FAIL     {RECORD_MD.name} is not the rendering of its record")
        return 1
    print("ok       the V6 path reaches stage 9, refuses at each stage, and keeps what arrived")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
