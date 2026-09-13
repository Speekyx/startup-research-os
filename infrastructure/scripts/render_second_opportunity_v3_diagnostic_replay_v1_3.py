"""Mission 1.84.11, CI gate 78. V3's retained answer, replayed DIAGNOSTICALLY through gate v1.3.0.

V3 was refused by the v1.1.0 semantic gate at stage 6, and that verdict stands: V3 is historically
rejected, its approval is spent, and nothing here makes its answer a candidate. Mission 1.84.10
replayed it through gate v1.2.0 and found one refusal that was a defect of that gate. This record
answers the next question for the NEXT execution: had gate v1.3.0 been the gate, where would the
machinery a future call uses have stopped V3's answer?

The replay is DIAGNOSTIC_ONLY, performed once, AFTER gate v1.3.0 was frozen and pushed
(`FREEZE_COMMIT`). It needs no database: its packet is the snapshot Mission 1.84.10 recorded, which CI
gate 76 authenticates by rebuilding the approved TED representation and the rendered prompt from it
alone. This gate checks, rather than asserts:

* gate v1.3.0's freeze still validates (CI gate 77), and so do gate v1.2.0's freeze (75) and its
  diagnostic replay (76), whose record this one reads and never rewrites;
* where git history is available, the freeze commit is an ancestor, carries the freeze record this
  replay names, and did NOT carry this record;
* V3's facts and its five v1.1.0 reasons are reconfirmed, and v1.2.0's one diagnostic reason is
  reproduced by re-running v1.2.0, so no historical verdict drifted;
* the source-metadata channel is rebuilt from the registry documents (`source-catalog-v1.json`,
  `source-compliance-v1.json`) and must equal what the record carries;
* stages 1 to 9 are re-derived through the V3 runner's own `validate_execution`, with nothing swapped
  but the semantic gate, and must equal the record;
* stage 10 is never manufactured, V3 is never a candidate, no human-review packet exists, and no V4
  packet exists unless stages 6 to 9 all passed.

    uv run python infrastructure/scripts/render_second_opportunity_v3_diagnostic_replay_v1_3.py --check
    uv run python infrastructure/scripts/render_second_opportunity_v3_diagnostic_replay_v1_3.py \\
        --replay --freeze-commit <sha>    # once, after the freeze commit is pushed
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import pathlib
import re
import subprocess
from collections.abc import Mapping
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"

RECORD = DATA / "second-opportunity-v3-diagnostic-replay-gate-v1.3-v1.json"
RECORD_MD = DATA / "second-opportunity-v3-diagnostic-replay-gate-v1.3-v1.md"
FREEZE_RECORD = DATA / "second-opportunity-output-gate-v1.3-freeze-v1.json"
FREEZE_GATE = SCRIPTS / "render_second_opportunity_semantic_gate_v1_3.py"
REPLAY_V1_2_GATE = SCRIPTS / "render_second_opportunity_v3_diagnostic_replay.py"
REPLAY_V1_2_RECORD = DATA / "second-opportunity-v3-diagnostic-replay-v1.json"
CATALOG = DATA / "source-catalog-v1.json"
COMPLIANCE = DATA / "source-compliance-v1.json"

MISSION = "mission-1.84.11"
USE_PROFILE = "local-private-research-v1"
#: The commit that froze gate v1.3.0 and was pushed before this replay ran.
FREEZE_COMMIT = "0fe38227f46bc1b851faf24cb014bef20d23490b"
#: Mission 1.84.10's replay record, read and never rewritten.
REPLAY_V1_2_RECORD_SHA256 = "43ec43831229bd7afc91910bbe371c275f4c1f3a1f4663332b49d90d50f8fb15"

STAGE_6_V1_1 = "6_semantic_output_gate_v1_1_0"
STAGE_6_V1_3 = "6_semantic_output_gate_v1_3_0"
DIAGNOSTIC_STAGES_JUDGED = (
    STAGE_6_V1_3,
    "7_evidence_boundary_and_no_distortion",
    "8_attribution_and_provenance",
    "9_persistence_eligibility",
)
PASSED_DIAGNOSTIC = "DIAGNOSTIC_STAGES_6_TO_9_PASSED"
GENUINE_FAILURE = "V3_DIAGNOSTIC_REVEALED_GENUINE_OUTPUT_SUPPORT_FAILURE"
DISJUNCTION_ONLY = "DISJUNCTIVE_OBSERVED_STATEMENT_REQUIRES_EXPLICIT_SUPPORT_POLICY"
BLOCKER = "V3_DIAGNOSTIC_REVEALED_NEXT_EXECUTION_BLOCKER"
ZERO_ACCOUNTING = (
    "MODEL_CALLS",
    "PROVIDER_REQUESTS",
    "MESSAGES_API_REQUESTS",
    "TED_BYTES_SENT",
    "CANONICAL_MUTATIONS",
)


class ValidationError(RuntimeError):
    """The replay record disagrees with what V3 kept, with the freeze, or with the re-derivation."""


def _load(path: pathlib.Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_sha(path: pathlib.Path) -> str:
    """A document's digest over its text with LF line ends, whatever the checkout wrote."""
    return _sha(path.read_text(encoding="utf-8").encode("utf-8"))


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValidationError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _replay_v1_2() -> Any:
    return _module("replay_v1_2_for_v1_3_replay", REPLAY_V1_2_GATE)


# ============================================================================= metadata


def registry_entries(source_ids: list[str]) -> list[dict[str, object]]:
    """Each packet source's names, read from the registry documents and from nothing else."""
    catalog = {s["source_id"]: s for s in _load(CATALOG)["sources"]}
    compliance = [
        s
        for s in _load(COMPLIANCE)["sources"]
        if s.get("use_profile_id") == USE_PROFILE and s.get("source_id") in source_ids
    ]
    entries: list[dict[str, object]] = []
    for source_id in source_ids:
        if source_id not in catalog:
            raise ValidationError(f"{source_id} is not in the source catalog")
        datasets = [
            {"resource_id": d.get("resource_id"), "name": d.get("name")}
            for entry in compliance
            if entry["source_id"] == source_id
            for d in entry.get("datasets") or []
        ]
        entries.append(
            {
                "source_id": source_id,
                "canonical_name": catalog[source_id]["canonical_name"],
                "datasets": datasets,
                "provenance": (
                    f"docs/data/{CATALOG.name} and docs/data/{COMPLIANCE.name} ({USE_PROFILE})"
                ),
            }
        )
    return entries


# ============================================================================= the replay


def _text_at(answer: Mapping[str, Any], field: str) -> str | None:
    """The answer's text at an audited field path such as `statement_classifications[7].statement`."""
    match = re.fullmatch(r"([a-z_]+)(?:\[(\d+)\])?(?:\.([a-z_]+))?", field)
    if match is None:
        return None
    value: Any = answer.get(match.group(1))
    if match.group(2) is not None:
        value = value[int(match.group(2))] if isinstance(value, list) else None
    if match.group(3) is not None:
        value = value.get(match.group(3)) if isinstance(value, Mapping) else None
    return value if isinstance(value, str) else None


def classify_outcome(summary: Mapping[str, str], reasons: list[str]) -> str:
    """The diagnostic outcome, by rule: which kind of refusal stopped the answer, if any."""
    from sros_opportunity.assertion_audit_v1_3 import (
        DISJUNCTIVE_OBSERVED_STATEMENT,
        SOURCE_METADATA_NOT_FACTUAL_SUPPORT,
    )

    if all(value == "PASSED" for value in summary.values()):
        return PASSED_DIAGNOSTIC
    if summary[STAGE_6_V1_3] == "FAILED":
        if any(SOURCE_METADATA_NOT_FACTUAL_SUPPORT in r for r in reasons):
            return GENUINE_FAILURE
        if reasons and all(DISJUNCTIVE_OBSERVED_STATEMENT in r for r in reasons):
            return DISJUNCTION_ONLY
    return BLOCKER


def replay(snapshot: Mapping[str, Any]) -> dict[str, object]:
    """Stages 1 to 9 over V3's answer, with only the semantic gate moved to v1.3.0."""
    from sros_opportunity.second_opportunity import evaluate_second_opportunity_output_v1_1
    from sros_opportunity.second_opportunity_gate_v1_2 import (
        build_trusted_context,
        evaluate_second_opportunity_output_v1_2,
    )
    from sros_opportunity.second_opportunity_gate_v1_3 import (
        build_source_metadata_context,
        evaluate_second_opportunity_output_v1_3,
    )

    v1_2 = _replay_v1_2()
    packet, statements, evidence_to_claim = v1_2.packet_from_snapshot(snapshot)
    auth = v1_2.authenticate(packet, statements, evidence_to_claim)
    response, packet_file = _load(v1_2.RESPONSE_V3), _load(v1_2.PACKET_V3)
    runner = _module("runner_v3_for_v1_3_diagnostic_replay", v1_2.RUNNER_V3)
    answer = response["parsed_output"]
    result = v1_2.reconstructed_result(response)
    parsed, _ = runner.structured_output_of(json.loads(result["transport_responses"][0]["body"]))
    if (
        parsed != answer
        or _sha(json.dumps(answer, sort_keys=True).encode()) != v1_2.PARSED_OUTPUT_SHA256
    ):
        raise ValidationError("the reconstructed body does not carry the answer V3 retained")

    trusted = build_trusted_context(packet)
    historical = evaluate_second_opportunity_output_v1_1(
        answer, packet, statements, evidence_to_claim
    )
    diagnostic_v1_2 = evaluate_second_opportunity_output_v1_2(
        answer, packet, statements, evidence_to_claim, trusted_context=trusted
    )
    recorded_v1_2 = _load(REPLAY_V1_2_RECORD)["DIAGNOSTIC_GATE_V1_2_REASONS"]
    metadata = build_source_metadata_context(registry_entries(list(packet.source_ids)))
    decisions: list[Any] = []

    def gate_v1_3(output: Mapping[str, Any]) -> Any:
        decision = evaluate_second_opportunity_output_v1_3(
            output,
            packet,
            statements,
            evidence_to_claim,
            trusted_context=trusted,
            source_metadata=metadata,
        )
        decisions.append(decision)
        return decision

    context = {
        "packet_file": packet_file,
        "packet": packet,
        "statements": statements,
        "evidence_to_claim": evidence_to_claim,
        "representation": auth["representation_sha256"],
        "prompt_hash": auth["prompt_sha256"],
    }
    with v1_2.no_transport():
        report = runner.validate_execution(result, context, semantic_gate=gate_v1_3)

    stages = {
        (STAGE_6_V1_3 if name == STAGE_6_V1_1 else name): value
        for name, value in report["stages"].items()
    }
    stages["10_human_review"] = "NOT_MANUFACTURED_DIAGNOSTIC_ONLY"
    summary = {
        name: "PASSED"
        if stages[name] in ("PASSED", "ELIGIBLE_FOR_HUMAN_REVIEW_ONLY")
        else stages[name]
        for name in DIAGNOSTIC_STAGES_JUDGED
    }
    decision = decisions[0] if decisions else None
    reasons = list(decision.refusal_reasons) if decision is not None else []
    failed = report.get("failed_stage")
    unsupported = (
        [
            {
                "field": f.field_name,
                "verdict": f.verdict.value,
                "text": _text_at(answer, f.field_name),
                "findings": list(f.findings),
            }
            for f in decision.audit.failed
        ]
        if decision is not None and decision.audit is not None
        else []
    )
    outcome = classify_outcome(summary, reasons)
    return {
        "HISTORICAL_V3_GATE_V1_1_VERSION": historical.gate_version,
        "HISTORICAL_V3_GATE_V1_1_VERDICT": "PASSED" if historical.persist else "FAILED",
        "HISTORICAL_V3_GATE_V1_1_REASONS_REPRODUCED": list(historical.refusal_reasons)
        == response["validation"]["reasons"],
        "HISTORICAL_V3_GATE_V1_1_REASON_COUNT": len(historical.refusal_reasons),
        "HISTORICAL_DIAGNOSTIC_GATE_V1_2_VERSION": diagnostic_v1_2.gate_version,
        "HISTORICAL_DIAGNOSTIC_GATE_V1_2_VERDICT": (
            "PASSED" if diagnostic_v1_2.persist else "FAILED"
        ),
        "HISTORICAL_DIAGNOSTIC_GATE_V1_2_REASONS": list(diagnostic_v1_2.refusal_reasons),
        "HISTORICAL_DIAGNOSTIC_GATE_V1_2_REASONS_REPRODUCED": list(diagnostic_v1_2.refusal_reasons)
        == recorded_v1_2,
        "DIAGNOSTIC_GATE_VERSION": decision.gate_version if decision is not None else None,
        "DIAGNOSTIC_GATE_V1_3_VERDICT": (
            "PASSED" if decision is not None and decision.persist else "FAILED"
        ),
        "DIAGNOSTIC_GATE_V1_3_REASONS": reasons,
        "DIAGNOSTIC_AUDIT": (
            [{"field": f.field_name, "verdict": f.verdict.value} for f in decision.audit.fields]
            if decision is not None and decision.audit is not None
            else []
        ),
        "UNSUPPORTED_PROPOSITIONS": unsupported,
        "DIAGNOSTIC_STAGES": stages,
        "DIAGNOSTIC_STAGE_SUMMARY": summary,
        "DIAGNOSTIC_FAILED_STAGE": (STAGE_6_V1_3 if failed == STAGE_6_V1_1 else failed),
        "DIAGNOSTIC_STAGE_REASONS": list(report.get("reasons") or []),
        "MACHINERY_OUTCOME": report["outcome"],
        "DIAGNOSTIC_OUTCOME": outcome,
        "DIAGNOSTIC_PROVENANCE": report.get("provenance"),
        "TRUSTED_CONTEXT_SHA256": trusted.digest(),
        "SOURCE_METADATA_CONTEXT": metadata.as_data(),
        "SOURCE_METADATA_CONTEXT_SHA256": metadata.digest(),
        "SNAPSHOT_AUTHENTICATION": auth,
        "ORIGINAL_RAW_RESPONSE_SHA256": response["RAW_PROVIDER_RESPONSE_SHA256"],
        "V4_CREATION_CONDITION_MET": outcome == PASSED_DIAGNOSTIC,
        "EXECUTION_PACKET_V4": "NOT_CREATED" if outcome != PASSED_DIAGNOSTIC else "REACHABLE",
    }


def build_record(snapshot: Mapping[str, Any], replayed_at: str) -> dict[str, Any]:
    freeze_gate = _module("freeze_gate_v1_3_for_diagnostic_replay", FREEZE_GATE)
    return {
        "$comment": (
            "Mission 1.84.11. V3's retained answer replayed DIAGNOSTICALLY through the frozen gate "
            "v1.3.0 and the V3 runner's own stages. V3 stays historically rejected and is never a "
            "candidate. CI gate 78 re-derives every field from Mission 1.84.10's authenticated "
            "snapshot."
        ),
        "record_version": "second-opportunity-v3-diagnostic-replay@1.0.0",
        "mission": MISSION,
        "DIAGNOSTIC_ONLY": True,
        "FREEZE_COMMIT": FREEZE_COMMIT,
        "FREEZE_RECORD_SHA256": text_sha(FREEZE_RECORD),
        "FROZEN_IMPLEMENTATION_SHA256": freeze_gate.FROZEN_IMPLEMENTATION_SHA256,
        "GATE_V1_3_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY": True,
        "REPLAY_V1_2_RECORD_SHA256": text_sha(REPLAY_V1_2_RECORD),
        "V3_EXECUTION_PACKET_SHA256": _replay_v1_2().V3_SHA256,
        "V3_FACTS": _replay_v1_2().reconfirm_v3(),
        **replay(snapshot),
        "V3_HISTORICALLY_REJECTED": True,
        "V3_HISTORICAL_OUTCOME": _replay_v1_2().V3_OUTCOME,
        "V3_CANDIDATE": False,
        "V3_HUMAN_REVIEW_PACKET": "NOT_PRODUCED",
        "V3_PERSISTABLE": False,
        "V3_APPROVAL_CONSUMED": True,
        "STAGE_10_MANUFACTURED": False,
        "PERSISTED": "NOTHING",
        "PACKET_SNAPSHOT": dict(snapshot),
        "accounting": {key: 0 for key in ZERO_ACCOUNTING},
        "replayed_at": replayed_at,
    }


# ============================================================================= the order


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 -- fixed git arguments, no shell
        ["git", *args],  # noqa: S607 -- the git on PATH, as every other check here uses it
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def git_ordering() -> dict[str, object]:
    """Whether the freeze preceded this replay, from git history where the checkout holds it."""
    if _git("cat-file", "-e", f"{FREEZE_COMMIT}^{{commit}}").returncode != 0:
        return {"state": "NOT_AVAILABLE_IN_THIS_CHECKOUT"}
    frozen = _git("show", f"{FREEZE_COMMIT}:docs/data/{FREEZE_RECORD.name}")
    return {
        "state": "CHECKED",
        "freeze_commit_is_ancestor": _git(
            "merge-base", "--is-ancestor", FREEZE_COMMIT, "HEAD"
        ).returncode
        == 0,
        "freeze_record_matches": frozen.returncode == 0
        and _sha(frozen.stdout.replace("\r\n", "\n").encode("utf-8")) == text_sha(FREEZE_RECORD),
        "replay_record_absent_at_freeze": _git(
            "cat-file", "-e", f"{FREEZE_COMMIT}:docs/data/{RECORD.name}"
        ).returncode
        != 0,
    }


def _require_order() -> dict[str, object]:
    ordering = git_ordering()
    if ordering["state"] == "CHECKED":
        for key, value in ordering.items():
            if key != "state" and value is not True:
                raise ValidationError(
                    f"git history says {key} is {value}: the freeze did not precede"
                )
    return ordering


def _require_history() -> None:
    """The three gates this replay stands on must still stand."""
    for name, path in (("77", FREEZE_GATE), ("76", REPLAY_V1_2_GATE)):
        gate = _module(f"gate_{name}_under_v1_3_replay", path)
        try:
            gate.validate()
        except gate.ValidationError as error:
            raise ValidationError(f"CI gate {name} no longer validates: {error}") from error
    if text_sha(REPLAY_V1_2_RECORD) != REPLAY_V1_2_RECORD_SHA256:
        raise ValidationError("Mission 1.84.10's replay record is not the one it committed")


# ============================================================================= check


def validate() -> dict[str, Any]:
    if not RECORD.exists():
        raise ValidationError(f"{RECORD.name} does not exist")
    record = _load(RECORD)
    _require_history()
    if record.get("FREEZE_COMMIT") != FREEZE_COMMIT:
        raise ValidationError("the record names a different freeze commit")
    _require_order()
    for key in ("DIAGNOSTIC_ONLY", "V3_HISTORICALLY_REJECTED", "V3_APPROVAL_CONSUMED"):
        if record.get(key) is not True:
            raise ValidationError(f"{key} must be true")
    for key in ("V3_CANDIDATE", "V3_PERSISTABLE", "STAGE_10_MANUFACTURED"):
        if record.get(key) is not False:
            raise ValidationError(f"{key} must be false: V3 is evidence, never a candidate")
    if record.get("V3_HUMAN_REVIEW_PACKET") != "NOT_PRODUCED":
        raise ValidationError("a human-review packet exists for a historically refused answer")
    snapshot = record.get("PACKET_SNAPSHOT")
    if snapshot != _load(REPLAY_V1_2_RECORD).get("PACKET_SNAPSHOT"):
        raise ValidationError("the snapshot is not the one Mission 1.84.10 authenticated")
    expected = build_record(snapshot, str(record.get("replayed_at")))
    for key, value in expected.items():
        if key == "$comment":
            continue
        if record.get(key) != value:
            raise ValidationError(f"{key} is {record.get(key)!r}; the replay derives {value!r}")
    stray = sorted(set(record) - set(expected))
    if stray:
        raise ValidationError(f"the record carries fields the replay does not derive: {stray}")
    return record


def _row(*cells: object) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def render(record: Mapping[str, Any]) -> str:
    facts = record["V3_FACTS"]
    auth = record["SNAPSHOT_AUTHENTICATION"]
    lines = [
        "<!-- Generated by infrastructure/scripts/render_second_opportunity_v3_diagnostic_replay_v1_3.py."
        " Do not edit by hand. -->",
        "",
        "# V3's retained answer, replayed diagnostically through gate v1.3.0",
        "",
        f"Mission {str(record['mission']).removeprefix('mission-')}. DIAGNOSTIC_ONLY. The gate was "
        f"frozen at `{record['FREEZE_COMMIT']}` before this replay ran; freeze record "
        f"`{record['FREEZE_RECORD_SHA256']}`, implementation "
        f"`{record['FROZEN_IMPLEMENTATION_SHA256']}`.",
        "",
        "## V3, as it happened (unchanged)",
        "",
        f"- packet `{record['V3_EXECUTION_PACKET_SHA256']}`, outcome `{record['V3_HISTORICAL_OUTCOME']}`",
        f"- {facts['actual_provider_requests']} request, {facts['actual_model_calls']} call, "
        f"{facts['retries']} retries; stop reason `{facts['STOP_REASON']}`; approval consumed "
        f"{str(record['V3_APPROVAL_CONSUMED']).lower()}",
        "",
        "## The historical gates, reproduced",
        "",
        _row("gate", "verdict", "reasons", "reproduced"),
        _row("---", "---", "---", "---"),
        _row(
            f"`{record['HISTORICAL_V3_GATE_V1_1_VERSION']}` (V3, historical)",
            record["HISTORICAL_V3_GATE_V1_1_VERDICT"],
            record["HISTORICAL_V3_GATE_V1_1_REASON_COUNT"],
            str(record["HISTORICAL_V3_GATE_V1_1_REASONS_REPRODUCED"]).lower(),
        ),
        _row(
            f"`{record['HISTORICAL_DIAGNOSTIC_GATE_V1_2_VERSION']}` (Mission 1.84.10, diagnostic)",
            record["HISTORICAL_DIAGNOSTIC_GATE_V1_2_VERDICT"],
            len(record["HISTORICAL_DIAGNOSTIC_GATE_V1_2_REASONS"]),
            str(record["HISTORICAL_DIAGNOSTIC_GATE_V1_2_REASONS_REPRODUCED"]).lower(),
        ),
        "",
        "## The diagnostic replay through v1.3.0",
        "",
        f"The snapshot rebuilds representation `{auth['representation_sha256']}` and prompt "
        f"`{auth['prompt_sha256']}`. Source metadata `{record['SOURCE_METADATA_CONTEXT_SHA256']}`, "
        "built from the registry: "
        + ", ".join(f"`{lb['text']}`" for lb in record["SOURCE_METADATA_CONTEXT"]["labels"])
        + ".",
        "",
        _row("stage", "diagnostic"),
        _row("---", "---"),
        *(_row(k, v) for k, v in record["DIAGNOSTIC_STAGES"].items()),
        "",
        f"DIAGNOSTIC_GATE_V1_3_VERDICT = {record['DIAGNOSTIC_GATE_V1_3_VERDICT']}.",
        "",
        *(f"- {reason}" for reason in record["DIAGNOSTIC_GATE_V1_3_REASONS"]),
        "",
        "## The unsupported propositions, exactly",
        "",
        *(
            f"- `{p['field']}` ({p['verdict']}): “{p['text']}”"
            for p in record["UNSUPPORTED_PROPOSITIONS"]
        ),
        "",
        f"Outcome: `{record['DIAGNOSTIC_OUTCOME']}`. The machinery's own outcome string "
        f"`{record['MACHINERY_OUTCOME']}` confers nothing here: stage 10 is "
        f"`{record['DIAGNOSTIC_STAGES']['10_human_review']}`. Execution packet V4: "
        f"`{record['EXECUTION_PACKET_V4']}`.",
        "",
        "## V3 stays what it was",
        "",
        f"- V3_HISTORICALLY_REJECTED = {str(record['V3_HISTORICALLY_REJECTED']).lower()}",
        f"- V3_CANDIDATE = {str(record['V3_CANDIDATE']).lower()}",
        f"- V3_HUMAN_REVIEW_PACKET = {record['V3_HUMAN_REVIEW_PACKET']}",
        f"- V3_PERSISTABLE = {str(record['V3_PERSISTABLE']).lower()}",
        f"- PERSISTED = {record['PERSISTED']}",
        "",
        "Model calls, provider requests, Messages API requests, TED bytes and canonical mutations: "
        + ", ".join(str(v) for v in record["accounting"].values())
        + ".",
        "",
    ]
    return "\n".join(lines)


# ============================================================================= entry point


def run_replay(freeze_commit: str) -> dict[str, Any]:
    """Once, after the freeze is pushed: replay the authenticated snapshot and write the record."""
    if freeze_commit != FREEZE_COMMIT:
        raise ValidationError(f"the replay runs against the frozen commit {FREEZE_COMMIT} only")
    if RECORD.exists():
        raise ValidationError("the diagnostic replay is performed once, and its record exists")
    ordering = _require_order()
    if ordering["state"] != "CHECKED":
        raise ValidationError("the replay must run where git history proves the freeze came first")
    _require_history()
    snapshot = _load(REPLAY_V1_2_RECORD)["PACKET_SNAPSHOT"]
    record = build_record(snapshot, dt.datetime.now(dt.UTC).isoformat())
    with RECORD.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    group.add_argument("--replay", action="store_true")
    parser.add_argument("--freeze-commit", default="")
    args = parser.parse_args(argv)
    try:
        if args.replay:
            run_replay(args.freeze_commit)
        record = validate()
    except ValidationError as error:
        print(f"FAIL: {error}")
        return 1
    text = render(record)
    if args.write or args.replay:
        RECORD_MD.write_bytes(text.encode("utf-8"))
    elif not RECORD_MD.exists() or RECORD_MD.read_text(encoding="utf-8") != text:
        print(f"FAIL: {RECORD_MD.name} is stale; run with --write")
        return 1
    print(
        f"ok: {RECORD.name}: diagnostic gate v1.3.0 {record['DIAGNOSTIC_GATE_V1_3_VERDICT']}, "
        f"{record['DIAGNOSTIC_OUTCOME']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
