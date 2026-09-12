"""Mission 1.84.10, CI gate 76. V3's retained answer, replayed DIAGNOSTICALLY through gate v1.2.0.

V3 was refused by the v1.1.0 semantic gate at stage 6, and that verdict stands: V3 is historically
rejected, its approval is spent, and nothing here makes its answer a candidate. What this record
answers is a question about the NEXT execution: had gate v1.2.0 been the gate, would the machinery a
future call uses have stopped V3's answer anywhere in stages 6 to 9? A blocker found here costs
nothing; one found after a new call costs the call.

The replay is DIAGNOSTIC_ONLY, it was performed once, and it ran AFTER gate v1.2.0 was frozen and
pushed (`FREEZE_COMMIT`). This gate checks that rather than asserting it:

* the freeze record still validates, so the gate that replayed V3 is the gate that was frozen;
* where git history is available, the freeze commit is an ancestor of this checkout, it carries the
  freeze record this replay names, and it did NOT carry this record (a shallow CI clone says it
  could not look, and the digest chain still holds);
* V3's historical artifacts are byte-identical, and V3's facts and its five v1.1.0 reasons are
  reconfirmed from them, the reasons by re-running v1.1.0;
* the packet snapshot the replay used is authenticated by rebuilding, from it alone, the approved
  TED representation (`2528a56a...`) and the rendered v1.2.0 prompt (`1677cbe5...`), so CI re-runs
  the whole replay without the research database;
* stages 1 to 9 are re-derived through the V3 runner's own `validate_execution`, with nothing swapped
  but the semantic gate, and must equal the record;
* stage 10 is never manufactured, V3 is never a candidate, and no human-review packet exists.

    uv run python infrastructure/scripts/render_second_opportunity_v3_diagnostic_replay.py --check
    uv run python infrastructure/scripts/render_second_opportunity_v3_diagnostic_replay.py \\
        --replay --freeze-commit <sha>    # once, on the operator's machine, with the database
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import pathlib
import subprocess
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"

RECORD = DATA / "second-opportunity-v3-diagnostic-replay-v1.json"
RECORD_MD = DATA / "second-opportunity-v3-diagnostic-replay-v1.md"
FREEZE_RECORD = DATA / "second-opportunity-output-gate-v1.2-freeze-v1.json"
FREEZE_GATE = SCRIPTS / "render_second_opportunity_semantic_gate_v1_2.py"
RUNNER_V3 = SCRIPTS / "run_second_opportunity_execution_v3.py"
PACKET_V3 = DATA / "second-opportunity-synthesis-execution-packet-v3.json"
RESPONSE_V3 = DATA / "second-opportunity-synthesis-response-v3.json"
RECORD_V3 = DATA / "second-opportunity-synthesis-execution-record-v3.json"

MISSION = "mission-1.84.10"
USE_PROFILE = "local-private-research-v1"
#: The commit that froze gate v1.2.0 and was pushed before this replay ran.
FREEZE_COMMIT = "3f8c63400d7b7a3e0088e2e1c1c119efd7aa7845"

#: Mission 1.84.9's artifacts, byte for byte. The replay reads them and changes none.
V3_ARTIFACTS_SHA256 = {
    "docs/data/second-opportunity-synthesis-execution-packet-v3.json": (
        "096eb1845e55a8792c4de7f07b35319de61b6e1af52bd9c4544bd2205533b130"
    ),
    "docs/data/second-opportunity-synthesis-execution-packet-v3.md": (
        "84af84ba91f58460aca2bd9656124299c2a7eb0cd0b62eac55bd6789818ce3d2"
    ),
    "docs/data/second-opportunity-synthesis-execution-record-v3.json": (
        "abb093389664405f80878d2a1963beabfa4c271ed559437384146a92ccfb00a3"
    ),
    "docs/data/second-opportunity-synthesis-execution-record-v3.md": (
        "d48673518c920f1db89ae00e20d45d5f1173e488706bea3b62c0910dbf88c970"
    ),
    "docs/data/second-opportunity-synthesis-response-v3.json": (
        "cf5eb183aa7d329f29e8c2c0f04e3939f1661e488952acdf414d07ad8f488ed6"
    ),
    "docs/data/second-opportunity-synthesis-execution-approval-v3.json": (
        "9f951e64d9bc93e1dfb907763c2fdfedc1f3df46b48e63acf927fef3671d027c"
    ),
    "docs/data/second-opportunity-synthesis-prompt-v3.json": (
        "f8e6610facf5cfba7b7aed2fd4b3b365187a74a01b9490915ab008760688ab4e"
    ),
    "infrastructure/scripts/run_second_opportunity_execution_v3.py": (
        "0a30b4abeef64df565ee1788f561ec97f677ec60ab965677938a49b82bd7c107"
    ),
}

V3_SHA256 = "c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"
PROMPT_SHA256 = "1677cbe53e83e644fa15e5492cf88e3ec578538351924f2b3a504e27f3a0878d"
SELECTED_PACKET_ID = "e218b56a8f938f4d5f7fc961e7f0c2cfe184c4396395334140c6199b48316592"
PARSED_OUTPUT_SHA256 = "973b8ba15158ca8bb94ba0e0040b4d731218c3048b1b15ae12712913f428df0b"
V3_OUTCOME = "EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY"

STAGE_6_V1_1 = "6_semantic_output_gate_v1_1_0"
STAGE_6_V1_2 = "6_semantic_output_gate_v1_2_0"
V3_STAGE_TABLE = {
    "1_transport_success": "PASSED",
    "2_provider_response_shape": "PASSED",
    "3_provider_completion": "PASSED",
    "4_structured_output_parse": "PASSED",
    "5_schema_validation_v1_1_0": "PASSED",
    STAGE_6_V1_1: "FAILED",
    "7_evidence_boundary_and_no_distortion": "NOT_REACHED",
    "8_attribution_and_provenance": "NOT_REACHED",
    "9_persistence_eligibility": "NOT_REACHED",
    "10_human_review": "NOT_REACHED",
}
#: §3. What Mission 1.84.9 recorded, reconfirmed from its record and never rewritten.
V3_FACTS = {
    "PRIMARY_OUTCOME": V3_OUTCOME,
    "execution_packet_sha256": V3_SHA256,
    "actual_provider_requests": 1,
    "actual_model_calls": 1,
    "retries": 0,
    "continuation_requests": 0,
    "repair_calls": 0,
    "STOP_REASON": "tool_use",
    "SCHEMA_VIOLATIONS": [],
    "CANONICAL_PERSISTENCE": False,
    "EXECUTION_APPROVAL_CONSUMED": True,
}
V3_USAGE = {"input_tokens": 9491, "output_tokens": 3880, "thinking_tokens": 0}
V3_COST_UNITS = 0.057782
DIAGNOSTIC_STAGES_JUDGED = (
    STAGE_6_V1_2,
    "7_evidence_boundary_and_no_distortion",
    "8_attribution_and_provenance",
    "9_persistence_eligibility",
)
PASSED_DIAGNOSTIC = "DIAGNOSTIC_STAGES_6_TO_9_PASSED"
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


@contextmanager
def no_transport() -> Iterator[None]:
    """A tripwire: nothing in a diagnostic replay may construct the real transport."""
    from sros_llm_gateway import transport

    original = transport.UrllibTransport.__init__

    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("a diagnostic replay constructed the real transport")

    transport.UrllibTransport.__init__ = refuse  # type: ignore[method-assign]
    try:
        yield
    finally:
        transport.UrllibTransport.__init__ = original  # type: ignore[method-assign]


# ============================================================================= V3, reconfirmed


def reconfirm_v3() -> dict[str, object]:
    """§3. V3's artifacts unchanged, and its facts read back from them."""
    for relative, digest in V3_ARTIFACTS_SHA256.items():
        if _sha((ROOT / relative).read_bytes()) != digest:
            raise ValidationError(f"{relative} is not the file Mission 1.84.9 committed")
    record, response = _load(RECORD_V3), _load(RESPONSE_V3)
    for key, value in V3_FACTS.items():
        if record.get(key) != value:
            raise ValidationError(
                f"V3's record has {key}={record.get(key)!r}; it recorded {value!r}"
            )
    for key, value in V3_USAGE.items():
        if record["ACTUAL_USAGE"].get(key) != value:
            raise ValidationError(f"V3's usage {key} is not {value}")
    if record["ACTUAL_COST"]["cost_units"] != V3_COST_UNITS:
        raise ValidationError("V3's cost is not the one recorded")
    for where, table in (
        ("record", record["VALIDATION_STAGES"]),
        ("response", response["validation"]["stages"]),
    ):
        if table != V3_STAGE_TABLE:
            raise ValidationError(f"V3's stage table in its {where} is not 1-5 PASSED, 6 FAILED")
    reasons = response["validation"]["reasons"]
    if record["SEMANTIC_GATE_REFUSAL_REASONS"] != reasons or len(reasons) != 5:
        raise ValidationError("V3's five semantic reasons are not the ones it retained")
    return {
        **V3_FACTS,
        **V3_USAGE,
        "cost_units": V3_COST_UNITS,
        "schema_validation": "PASSED",
        "semantic_gate_v1_1_0": "FAILED",
        "semantic_reasons": len(reasons),
    }


# ============================================================================= the snapshot


def snapshot_from(
    packet: Any, statements: Mapping[str, str], evidence_to_claim: Mapping[str, str]
) -> dict[str, Any]:
    """Every packet fact the replay reads, and nothing else, as data."""
    return {
        "packet_id": packet.packet_id,
        "packet_version": packet.packet_version,
        "subject": str(packet.subject) if packet.subject is not None else None,
        "subject_label": packet.subject_label,
        "evidence_ids": list(packet.evidence_ids),
        "claim_ids": list(packet.claim_ids),
        "signal_type_ids": list(packet.signal_type_ids),
        "source_ids": list(packet.source_ids),
        "source_families": list(packet.source_families),
        "use_profile_ids": list(packet.use_profile_ids),
        "dimensions": sorted(d.value for d in packet.dimensions),
        "counting_dimensions": sorted(d.value for d in packet.counting_dimensions),
        "dimension_bounds": list(packet.dimension_bounds),
        "eligibility_counts": dict(packet.eligibility_counts),
        "independence_counts": dict(packet.independence_counts),
        "reliability_status_counts": dict(packet.reliability_status_counts),
        "observed_at_present": packet.observed_at_present,
        "procedures": dict(packet.procedures),
        "claim_statements": {cid: statements[cid] for cid in packet.claim_ids},
        "evidence_to_claim": {
            eid: evidence_to_claim[eid] for eid in packet.evidence_ids if eid in evidence_to_claim
        },
    }


def packet_from_snapshot(snapshot: Mapping[str, Any]) -> tuple[Any, dict[str, str], dict[str, str]]:
    from sros_opportunity import EvidenceDimension, OpportunityEvidencePacket

    packet = OpportunityEvidencePacket(
        packet_id=snapshot["packet_id"],
        packet_version=snapshot["packet_version"],
        subject=None,
        subject_label=snapshot["subject_label"],
        evidence_ids=tuple(snapshot["evidence_ids"]),
        claim_ids=tuple(snapshot["claim_ids"]),
        signal_type_ids=tuple(snapshot["signal_type_ids"]),
        source_ids=tuple(snapshot["source_ids"]),
        source_families=tuple(snapshot["source_families"]),
        use_profile_ids=tuple(snapshot["use_profile_ids"]),
        dimensions=frozenset(EvidenceDimension(v) for v in snapshot["dimensions"]),
        counting_dimensions=frozenset(
            EvidenceDimension(v) for v in snapshot["counting_dimensions"]
        ),
        dimension_bounds=tuple(snapshot["dimension_bounds"]),
        eligibility_counts=dict(snapshot["eligibility_counts"]),
        independence_counts=dict(snapshot["independence_counts"]),
        reliability_status_counts=dict(snapshot["reliability_status_counts"]),
        observed_at_present=int(snapshot["observed_at_present"]),
        procedures=dict(snapshot["procedures"]),
    )
    return packet, dict(snapshot["claim_statements"]), dict(snapshot["evidence_to_claim"])


def authenticate(
    packet: Any, statements: Mapping[str, str], evidence_to_claim: Mapping[str, str]
) -> dict[str, str]:
    """The approved representation and the rendered v1.2.0 prompt, rebuilt from the snapshot alone."""
    from sros_opportunity import (
        ExternalSynthesisDecision,
        SynthesisAvailability,
        serialize_packet_for_model,
    )
    from sros_opportunity.second_opportunity import (
        render_second_opportunity_prompt_v1_2,
        second_opportunity_prompt_hash_v1_2,
    )

    measurement = ExternalSynthesisDecision(
        availability=SynthesisAvailability.AVAILABLE,
        packet_id=packet.packet_id,
        refusal_reasons=(),
        per_source=(("ted-eu", "RECOMPUTED_FOR_DIAGNOSTIC_REPLAY"),),
    )
    representation = _sha(
        serialize_packet_for_model(packet, measurement, statements).encode("utf-8")
    )
    prompt = second_opportunity_prompt_hash_v1_2(
        render_second_opportunity_prompt_v1_2(packet, statements, evidence_to_claim)
    )
    found = {
        "packet_id": str(packet.packet_id),
        "representation_sha256": representation,
        "prompt_sha256": prompt,
    }
    expected = {
        "packet_id": SELECTED_PACKET_ID,
        "representation_sha256": REPRESENTATION_SHA256,
        "prompt_sha256": PROMPT_SHA256,
    }
    for key, value in expected.items():
        if found[key] != value:
            raise ValidationError(
                f"the snapshot rebuilds {key} {found[key]}, not V3's {value}: it is not the packet "
                "V3 was sent"
            )
    return found


# ============================================================================= the replay


def reconstructed_result(response: Mapping[str, Any]) -> dict[str, Any]:
    """What the recording transport would hold, rebuilt from the retained body."""
    return {
        "response": None,
        "failure": None,
        "transport_responses": [
            {
                "status": response["RAW_PROVIDER_RESPONSE_STATUS"],
                "body": json.dumps(response["RAW_PROVIDER_RESPONSE_BODY"], ensure_ascii=False),
                "headers": {"request-id": response["PROVIDER_REQUEST_ID"]},
            }
        ],
        "transport_errors": [],
        "telemetry": [],
        "timing": dict(response["timing"]),
    }


def replay(snapshot: Mapping[str, Any]) -> dict[str, object]:
    """Stages 1 to 9 over V3's answer, with only the semantic gate moved to v1.2.0."""
    from sros_opportunity.second_opportunity import evaluate_second_opportunity_output_v1_1
    from sros_opportunity.second_opportunity_gate_v1_2 import (
        build_trusted_context,
        evaluate_second_opportunity_output_v1_2,
    )

    packet, statements, evidence_to_claim = packet_from_snapshot(snapshot)
    auth = authenticate(packet, statements, evidence_to_claim)
    response, packet_file = _load(RESPONSE_V3), _load(PACKET_V3)
    runner = _module("runner_v3_for_diagnostic_replay", RUNNER_V3)

    answer = response["parsed_output"]
    result = reconstructed_result(response)
    parsed, _ = runner.structured_output_of(json.loads(result["transport_responses"][0]["body"]))
    if (
        parsed != answer
        or _sha(json.dumps(answer, sort_keys=True).encode()) != PARSED_OUTPUT_SHA256
    ):
        raise ValidationError("the reconstructed body does not carry the answer V3 retained")

    historical = evaluate_second_opportunity_output_v1_1(
        answer, packet, statements, evidence_to_claim
    )
    trusted = build_trusted_context(packet)
    decisions: list[Any] = []

    def gate_v1_2(output: Mapping[str, Any]) -> Any:
        decision = evaluate_second_opportunity_output_v1_2(
            output, packet, statements, evidence_to_claim, trusted_context=trusted
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
    with no_transport():
        report = runner.validate_execution(result, context, semantic_gate=gate_v1_2)

    stages = {
        (STAGE_6_V1_2 if name == STAGE_6_V1_1 else name): value
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
    failed = report.get("failed_stage")
    return {
        "HISTORICAL_V3_GATE_V1_1_VERSION": historical.gate_version,
        "HISTORICAL_V3_GATE_V1_1_VERDICT": "PASSED" if historical.persist else "FAILED",
        "HISTORICAL_REASONS_REPRODUCED": list(historical.refusal_reasons)
        == response["validation"]["reasons"],
        "HISTORICAL_REASON_COUNT": len(historical.refusal_reasons),
        "DIAGNOSTIC_GATE_VERSION": decision.gate_version if decision is not None else None,
        "DIAGNOSTIC_GATE_V1_2_VERDICT": (
            "PASSED" if decision is not None and decision.persist else "FAILED"
        ),
        "DIAGNOSTIC_GATE_V1_2_REASONS": list(decision.refusal_reasons) if decision else [],
        "DIAGNOSTIC_AUDIT": (
            [{"field": f.field_name, "verdict": f.verdict.value} for f in decision.audit.fields]
            if decision is not None and decision.audit is not None
            else []
        ),
        "DIAGNOSTIC_STAGES": stages,
        "DIAGNOSTIC_STAGE_SUMMARY": summary,
        "DIAGNOSTIC_FAILED_STAGE": (STAGE_6_V1_2 if failed == STAGE_6_V1_1 else failed),
        "DIAGNOSTIC_STAGE_REASONS": list(report.get("reasons") or []),
        "MACHINERY_OUTCOME": report["outcome"],
        "DIAGNOSTIC_OUTCOME": (
            PASSED_DIAGNOSTIC if all(v == "PASSED" for v in summary.values()) else BLOCKER
        ),
        "DIAGNOSTIC_PROVENANCE": report.get("provenance"),
        "TRUSTED_CONTEXT_SHA256": trusted.digest(),
        "TRUSTED_IDENTIFIERS": sorted(trusted.identifiers),
        "SNAPSHOT_AUTHENTICATION": auth,
        "ORIGINAL_RAW_RESPONSE_SHA256": response["RAW_PROVIDER_RESPONSE_SHA256"],
    }


def build_record(snapshot: Mapping[str, Any], replayed_at: str) -> dict[str, Any]:
    freeze_gate = _module("freeze_gate_for_diagnostic_replay", FREEZE_GATE)
    return {
        "$comment": (
            "Mission 1.84.10. V3's retained answer replayed DIAGNOSTICALLY through the frozen gate "
            "v1.2.0 and the V3 runner's own stages. V3 stays historically rejected and is never a "
            "candidate. CI gate 76 re-derives every field from the authenticated snapshot."
        ),
        "record_version": "second-opportunity-v3-diagnostic-replay@1.0.0",
        "mission": MISSION,
        "DIAGNOSTIC_ONLY": True,
        "FREEZE_COMMIT": FREEZE_COMMIT,
        "FREEZE_RECORD_SHA256": text_sha(FREEZE_RECORD),
        "FROZEN_IMPLEMENTATION_SHA256": freeze_gate.FROZEN_IMPLEMENTATION_SHA256,
        "GATE_V1_2_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY": True,
        "V3_EXECUTION_PACKET_SHA256": V3_SHA256,
        "V3_FACTS": reconfirm_v3(),
        "HISTORICAL_V3_STAGE_TABLE": dict(V3_STAGE_TABLE),
        **replay(snapshot),
        "V3_HISTORICALLY_REJECTED": True,
        "V3_HISTORICAL_OUTCOME": V3_OUTCOME,
        "V3_CANDIDATE": False,
        "V3_HUMAN_REVIEW_PACKET": "NOT_PRODUCED",
        "V3_PERSISTABLE": False,
        "STAGE_10_MANUFACTURED": False,
        "PERSISTED": "NOTHING",
        "RECONSTRUCTED_BODY_NOTE": (
            "stage 8 reads a body re-serialised from the retained response, so its raw digest is "
            "of that body; the digest of the bytes that arrived is ORIGINAL_RAW_RESPONSE_SHA256"
        ),
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


# ============================================================================= check


def validate() -> dict[str, Any]:
    if not RECORD.exists():
        raise ValidationError(f"{RECORD.name} does not exist")
    record = _load(RECORD)
    freeze_gate = _module("freeze_gate_for_diagnostic_check", FREEZE_GATE)
    try:
        freeze_gate.validate()
    except freeze_gate.ValidationError as error:
        raise ValidationError(f"the frozen gate no longer validates: {error}") from error
    if record.get("FREEZE_COMMIT") != FREEZE_COMMIT:
        raise ValidationError("the record names a different freeze commit")
    _require_order()
    for key in ("DIAGNOSTIC_ONLY", "V3_HISTORICALLY_REJECTED"):
        if record.get(key) is not True:
            raise ValidationError(f"{key} must be true")
    for key in ("V3_CANDIDATE", "V3_PERSISTABLE", "STAGE_10_MANUFACTURED"):
        if record.get(key) is not False:
            raise ValidationError(f"{key} must be false: V3 is evidence, never a candidate")
    if record.get("V3_HUMAN_REVIEW_PACKET") != "NOT_PRODUCED":
        raise ValidationError("a human-review packet exists for a historically refused answer")
    snapshot = record.get("PACKET_SNAPSHOT")
    if not isinstance(snapshot, dict):
        raise ValidationError("the record carries no packet snapshot")
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
    lines = [
        "<!-- Generated by infrastructure/scripts/render_second_opportunity_v3_diagnostic_replay.py."
        " Do not edit by hand. -->",
        "",
        "# V3's retained answer, replayed diagnostically through gate v1.2.0",
        "",
        f"Mission {str(record['mission']).removeprefix('mission-')}. DIAGNOSTIC_ONLY. The gate was "
        f"frozen at `{record['FREEZE_COMMIT']}` before this replay ran; freeze record "
        f"`{record['FREEZE_RECORD_SHA256']}`, implementation `{record['FROZEN_IMPLEMENTATION_SHA256']}`.",
        "",
        "## V3, as it happened (unchanged)",
        "",
        f"- packet `{record['V3_EXECUTION_PACKET_SHA256']}`, outcome `{record['V3_HISTORICAL_OUTCOME']}`",
        f"- {facts['actual_provider_requests']} request, {facts['actual_model_calls']} call, "
        f"{facts['retries']} retries, {facts['continuation_requests']} continuations, "
        f"{facts['repair_calls']} repairs; stop reason `{facts['STOP_REASON']}`",
        f"- {facts['input_tokens']} input, {facts['output_tokens']} output, "
        f"{facts['thinking_tokens']} thinking tokens; cost {facts['cost_units']}",
        f"- schema {facts['schema_validation']}; semantic gate v1.1.0 {facts['semantic_gate_v1_1_0']} "
        f"on {facts['semantic_reasons']} reasons; approval consumed "
        f"{str(facts['EXECUTION_APPROVAL_CONSUMED']).lower()}",
        "",
        _row("stage", "V3 (v1.1.0)"),
        _row("---", "---"),
        *(_row(k, v) for k, v in record["HISTORICAL_V3_STAGE_TABLE"].items()),
        "",
        f"HISTORICAL_V3_GATE_V1_1_VERDICT = {record['HISTORICAL_V3_GATE_V1_1_VERDICT']}; the five "
        "reasons reproduce exactly: "
        f"{str(record['HISTORICAL_REASONS_REPRODUCED']).lower()}.",
        "",
        "## The diagnostic replay",
        "",
        f"The snapshot rebuilds representation `{record['SNAPSHOT_AUTHENTICATION']['representation_sha256']}` "
        f"and prompt `{record['SNAPSHOT_AUTHENTICATION']['prompt_sha256']}`. Trusted context "
        f"`{record['TRUSTED_CONTEXT_SHA256']}` licenses {', '.join(record['TRUSTED_IDENTIFIERS'])}.",
        "",
        _row("stage", "diagnostic"),
        _row("---", "---"),
        *(_row(k, v) for k, v in record["DIAGNOSTIC_STAGES"].items()),
        "",
        f"DIAGNOSTIC_GATE_V1_2_VERDICT = {record['DIAGNOSTIC_GATE_V1_2_VERDICT']}.",
        "",
        *(f"- {reason}" for reason in record["DIAGNOSTIC_GATE_V1_2_REASONS"]),
        "",
        f"Outcome: `{record['DIAGNOSTIC_OUTCOME']}`. The machinery's own outcome string "
        f"`{record['MACHINERY_OUTCOME']}` confers nothing here: stage 10 is "
        f"`{record['DIAGNOSTIC_STAGES']['10_human_review']}`.",
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
    """Once, with the database: rebuild V3's packet, snapshot it, replay, write the record."""
    if freeze_commit != FREEZE_COMMIT:
        raise ValidationError(f"the replay runs against the frozen commit {FREEZE_COMMIT} only")
    if RECORD.exists():
        raise ValidationError("the diagnostic replay is performed once, and its record exists")
    ordering = _require_order()
    if ordering["state"] != "CHECKED":
        raise ValidationError("the replay must run where git history proves the freeze came first")
    freeze_gate = _module("freeze_gate_for_diagnostic_replay_run", FREEZE_GATE)
    freeze_gate.validate()
    runner = _module("runner_v3_for_diagnostic_rebuild", RUNNER_V3)
    with no_transport():
        packet, statements, evidence_to_claim, _ = runner.v1_runner().rebuild(USE_PROFILE)
    snapshot = snapshot_from(packet, statements, evidence_to_claim)
    rebuilt, _, _ = packet_from_snapshot(snapshot)
    if rebuilt.packet_id != packet.packet_id or rebuilt.dimension_bounds != packet.dimension_bounds:
        raise ValidationError("the snapshot does not round-trip the rebuilt packet")
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
        f"ok: {RECORD.name}: diagnostic gate v1.2.0 {record['DIAGNOSTIC_GATE_V1_2_VERDICT']}, "
        f"{record['DIAGNOSTIC_OUTCOME']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
