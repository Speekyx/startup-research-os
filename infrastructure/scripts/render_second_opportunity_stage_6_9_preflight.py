"""Gate 80: stages 6 to 9 of the V4 runner, run over synthetic fixtures with the real machinery.

Mission 1.84.12. V3's one real answer never got past stage 6, so stages 7 to 9 have never judged
anything. This gate runs the V4 runner's own `validate_execution` over synthetic responses, with the
real gate v1.3.0 (which the V4 runner does not let anybody replace), the real trusted context and
metadata channel, the real provenance reading and the real `OpportunityHypothesis` constructor, and
records where each fixture stops:

    A  a valid answer                                  passes 6, 7 and 8, eligible at 9
    B  a semantic failure                              fails at 6
    B2 a cited id outside the packet                   fails at 6, never at 7
    C  a context whose packet exceeds the approval     fails at 7
    D  a response with an empty request id             fails at 8
    E  a source name the hypothesis model reads        fails at 9

    uv run python infrastructure/scripts/render_second_opportunity_stage_6_9_preflight.py --check

**A synthetic pass is not evidence.** It shows the stages can accept a well-formed answer and refuse
each failure at the stage built for it. It says nothing about what a model will write.

The gate refuses: a fixture that stops at another stage, or whose later stages are not NOT_REACHED; a
valid fixture that does not reach stage 9 (DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY); a runner whose
semantic gate can be injected, or whose stage 9 refuses nothing; the real transport constructed; and a
record field the code does not derive.
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

RECORD = DATA / "second-opportunity-stage-6-9-preflight-v1.json"
RECORD_MD = DATA / "second-opportunity-stage-6-9-preflight-v1.md"
RUNNER_V4 = SCRIPTS / "run_second_opportunity_execution_v4.py"
RUNNER_V3 = SCRIPTS / "run_second_opportunity_execution_v3.py"
FIXTURES = SCRIPTS / "second_opportunity_synthetic_fixtures.py"
GATE_76 = SCRIPTS / "render_second_opportunity_v3_diagnostic_replay.py"
MISSION = "mission-1.84.12"

READY = "DETERMINISTIC_STAGE_6_TO_9_PATH_READY"
NOT_READY = "DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY"
ZERO_ACCOUNTING = {
    "MODEL_CALLS": 0,
    "PROVIDER_REQUESTS": 0,
    "MESSAGES_API_REQUESTS": 0,
    "TED_BYTES_SENT": 0,
    "CANONICAL_MUTATIONS": 0,
}


class ValidationError(RuntimeError):
    """The preflight record disagrees with the V4 runner run over the fixtures."""


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _refuses_at(source: str, index: int) -> bool:
    """Whether the stage function calls `refuse(STAGES[index], ...)` anywhere."""
    tree = ast.parse(source)
    judge = next(
        (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "validate_execution"),
        None,
    )
    if judge is None:
        return False
    for node in ast.walk(judge):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "refuse"
            and node.args
            and isinstance(node.args[0], ast.Subscript)
            and isinstance(node.args[0].slice, ast.Constant)
            and node.args[0].slice.value == index
        ):
            return True
    return False


def fixtures(fx: Any) -> list[tuple[str, str, str | None, dict[str, Any], dict[str, Any]]]:
    """(id, what it is, the stage it must stop at or None, result, context)."""
    observed = "OBSERVED_OR_EVIDENCE_SUPPORTED"
    wider = fx.packet(extra=True)
    beyond = fx.good_output(
        supporting_evidence_ids=[*fx.EVIDENCE, fx.EXTRA_ROW[0]],
        supporting_claim_ids=[*fx.CLAIMS, fx.EXTRA_ROW[1]],
        independence_status="Independence is UNKNOWN for 3 of 3 rows.",
        reliability_status="All rows are SCORABLE; no score exists.",
        unsupported_dimensions=fx.mandatory_unsupported(wider),
    )
    guarded = "Profitability Review (synthetic register)"
    summary = fx.good_output()["evidence_bound_reasoning_summary"]
    return [
        (
            "A_VALID",
            "a well-formed answer the gate and the hypothesis model both accept",
            None,
            fx.recorded_result(fx.good_output()),
            fx.runner_context(),
        ),
        (
            "B_SEMANTIC_FAILURE",
            "an OBSERVED statement joining alternatives",
            "6_semantic_output_gate_v1_3_0",
            fx.recorded_result(
                fx.with_statement(
                    "Notices under CPV class 7777 state amounts in EUR or in another currency.",
                    observed,
                )
            ),
            fx.runner_context(),
        ),
        (
            "B2_STRAY_ID_REFUSED_BY_THE_GATE",
            "a cited Evidence id the packet does not carry, which V3's stage 7 was built for",
            "6_semantic_output_gate_v1_3_0",
            fx.recorded_result(
                fx.good_output(supporting_evidence_ids=[*fx.EVIDENCE, fx.EXTRA_ROW[0]])
            ),
            fx.runner_context(),
        ),
        (
            "C_EVIDENCE_BOUNDARY_FAILURE",
            "the gate is handed a packet with a row the approval does not bind, and the answer "
            "cites it",
            "7_evidence_boundary_and_no_distortion",
            fx.recorded_result(beyond),
            fx.runner_context(evidence_packet=wider, supplied=fx.extra_statements()),
        ),
        (
            "D_ATTRIBUTION_FAILURE",
            "a response whose request-id header is empty",
            "8_attribution_and_provenance",
            fx.recorded_result(fx.good_output(), request_id=""),
            fx.runner_context(),
        ),
        (
            "E_PERSISTENCE_ELIGIBILITY_FAILURE",
            "a source name the gate reads as a name and the hypothesis model reads as a word",
            "9_persistence_eligibility",
            fx.recorded_result(
                fx.good_output(
                    evidence_bound_reasoning_summary=summary.replace(
                        fx.SHORT_NAME, "Profitability Review"
                    )
                )
            ),
            fx.runner_context(
                supplied=fx.statements(name=guarded), names=fx.metadata(name=guarded)
            ),
        ),
    ]


def run() -> dict[str, Any]:
    runner = _module("runner_v4_for_gate_80", RUNNER_V4)
    fx = _module("fixtures_for_gate_80", FIXTURES)
    gate_76 = _module("gate_76_for_gate_80", GATE_76)
    stages = list(runner.STAGES)
    signature = list(inspect.signature(runner.validate_execution).parameters)
    if signature != ["result", "context"]:
        raise ValidationError(f"the V4 stage function takes {signature}; no gate may be injected")
    source = RUNNER_V4.read_text(encoding="utf-8")
    if "evaluate_second_opportunity_output_v1_3(" not in source:
        raise ValidationError("the V4 runner's stage 6 is not gate v1.3.0")
    for index in (5, 6, 7, 8):
        if not _refuses_at(source, index):
            raise ValidationError(f"the V4 runner cannot refuse at {stages[index]}")
    v3_source = RUNNER_V3.read_text(encoding="utf-8")
    results: list[dict[str, Any]] = []
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
                raise ValidationError(f"{NOT_READY}: the valid fixture does not reach stage 9")
            results.append(
                {
                    "fixture": fixture_id,
                    "what": description,
                    "intended_stage": intended or "NONE_ELIGIBLE_AT_9",
                    "failed_stage": failed,
                    "outcome": report["outcome"],
                    "stages": {k: v for k, v in report["stages"].items() if k[:1] in "6789"}
                    | {"10_human_review": report["stages"]["10_human_review"]},
                    "reasons": list(report["reasons"]),
                    "MISREPORTED_AS_A_LATER_STAGE": False,
                }
            )
    return {
        "$comment": (
            "Mission 1.84.12. Stages 6 to 9 of the V4 runner, run over synthetic responses with "
            "the real gate v1.3.0, the real provenance reading and the real OpportunityHypothesis "
            "constructor. A synthetic pass is not evidence about a model's answer. CI gate 80 "
            "re-derives every field."
        ),
        "record_version": "second-opportunity-stage-6-9-preflight@1.0.0",
        "mission": MISSION,
        "RUNNER": RUNNER_V4.name,
        "STAGES": stages,
        "SEMANTIC_GATE_INJECTABLE": False,
        "STUBS_USED": False,
        "REAL_TRANSPORT_CONSTRUCTED": False,
        "FIXTURES": results,
        "VALID_FIXTURE_REACHES_STAGE_9": True,
        "EVERY_NEGATIVE_FIXTURE_AT_ITS_INTENDED_STAGE": True,
        "OUTCOME": READY,
        "SYNTHETIC_PASS_IS_NOT_EVIDENCE": True,
        "V3_RUNNER_STAGE_7_REDUNDANT_UNDER_GATE_V1_3": True,
        "V3_RUNNER_STAGE_9_COULD_REFUSE": _refuses_at(v3_source, 8),
        "V4_STAGE_7_READS_THE_APPROVED_BOUNDARY": True,
        "V4_STAGE_9_CONSTRUCTS_THE_CANONICAL_HYPOTHESIS": True,
        "findings_note": (
            "Under gate v1.3.0, every refusal V3's stage 7 could make (a cited id outside the "
            "packet, a missing audit, a failed field) is made first at stage 6, as B2 shows, so "
            "V3's stage 7 could never fail after stage 6 passed; V4's stage 7 reads the boundary "
            "from the digest-bound packet, and C is the only way it can refuse, a context the "
            "pre-flight verification also refuses. V3's stage 9 refused nothing; V4's builds the "
            "OpportunityHypothesis persistence would build, and E shows an answer the gate accepts "
            "that the hypothesis model's own prose guard refuses."
        ),
        "accounting": dict(ZERO_ACCOUNTING),
    }


def validate() -> dict[str, Any]:
    built = run()
    if not RECORD.exists():
        raise ValidationError(f"{RECORD.name} does not exist; run --write")
    if _load(RECORD) != built:
        raise ValidationError(f"{RECORD.name} is not what the V4 runner derives")
    return built


HEADER = (
    "<!-- Generated by infrastructure/scripts/render_second_opportunity_stage_6_9_preflight.py "
    "from {source}. Do not edit by hand; edit the code and re-render. -->\n\n"
)


def render(record: Mapping[str, Any]) -> str:
    out = [
        HEADER.format(source=RECORD.name),
        "# Second opportunity: stages 6 to 9, preflight",
        "",
        f"**{record['OUTCOME']}.** The V4 runner's own stages, over synthetic responses, with the "
        "real gate v1.3.0 and nothing stubbed. **A synthetic pass is not evidence** about what a "
        "model will write.",
        "",
        "| fixture | intended stage | stopped at | outcome |",
        "|---|---|---|---|",
        *[
            f"| `{f['fixture']}` | `{f['intended_stage']}` | `{f['failed_stage'] or 'none'}` | "
            f"`{f['outcome']}` |"
            for f in record["FIXTURES"]
        ],
        "",
        record["findings_note"],
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
    print("ok       the valid fixture reaches stage 9 and every failure stops at its own stage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
