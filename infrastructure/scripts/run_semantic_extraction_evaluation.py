"""Mission 1.85.4 (N08-B). The only execution path for a semantic-extraction evaluation run.

DRY BY DEFAULT. Without `--execute` it verifies the packet and exits having built no transport and sent
nothing. With `--execute` it refuses, in this order and before any transport exists:

    1. a packet whose recomputed digest differs from its recorded digest or from EXPECTED_PACKET_SHA256
    2. an approval flag written into the packet
    3. any packet status other than READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL (before reading an approval)
    4. a missing --approval-sha256, a missing approval file, or an approval file whose sha256 differs
    5. an approval that does not name this packet id, version and digest, or does not accept the ceiling,
       the retention bound and the retry interpretation
    6. an existing attempt record (an approval is spent by the attempt, whatever the outcome)
    7. a failed ADR-033 four-gate authorization

Then it writes an ATTEMPT_STARTED record exclusively BEFORE the first request, and calls the model at most
`max_calls` times through one call site. Provider error bodies and exception text are never written:
only the class, HTTP status, request-id header and sha256s. Outputs go to a directory outside the
repository and nothing is written to the research database.

Merging this script, its packet or any document authorises nothing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
for path in (
    "packages/semantic-extraction-contract/python",
    "packages/semantic-extraction/python",
    "packages/llm-gateway/python",
    "packages/contracts/python",
):
    sys.path.insert(0, str(ROOT / path))

DATA = ROOT / "docs" / "data"
PACKET = DATA / "semantic-extraction-evaluation-packet-development-v1.json"
APPROVAL = DATA / "semantic-extraction-evaluation-approval-development-v1.json"
ATTEMPT = DATA / "semantic-extraction-evaluation-attempt-development-v1.json"
READY = "READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL"
APPROVAL_DECISION = "APPROVE_EXACTLY_ONE_EVALUATION_RUN"
# Pinned, not read from the packet: a runner that took its expectation from the file it checks would
# check nothing. Re-pinned only when a mission deliberately re-renders the packet.
EXPECTED_PACKET_SHA256 = "1ed9faf8b3807599fc346a125f2a9c64912874a5b79408357fae55db498d386b"


class Refused(SystemExit):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"REFUSED  {code}{': ' + detail if detail else ''}")
        self.refusal = code


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_packet(
    packet_path: pathlib.Path = PACKET, expected: str = EXPECTED_PACKET_SHA256
) -> dict[str, Any]:
    from render_semantic_extraction_packet import digest

    packet = json.loads(packet_path.read_text("utf-8"))
    recomputed = digest(packet)
    if recomputed != packet.get("packet_sha256") or recomputed != expected:
        raise Refused("EXECUTION_PACKET_DIGEST_MISMATCH", recomputed)
    if packet.get("operator_approval_recorded") is not False:
        raise Refused("APPROVAL_WRITTEN_INTO_THE_PACKET")
    if (
        packet["selection"]["holdout_included"] is not False
        or packet["selection"]["split"] != "DEVELOPMENT"
    ):
        raise Refused("HOLDOUT_IN_A_DEVELOPMENT_PACKET")
    return packet


def check_approval(
    packet: dict[str, Any], approval_path: pathlib.Path, approval_sha256: str | None
) -> dict[str, Any]:
    if packet.get("status") != READY:
        raise Refused("PACKET_NOT_READY_FOR_APPROVAL", str(packet.get("status")))
    if not approval_sha256:
        raise Refused("APPROVAL_SHA256_NOT_SUPPLIED")
    if not approval_path.exists():
        raise Refused("OPERATOR_APPROVAL_NOT_RECORDED")
    raw = approval_path.read_bytes()
    if _sha(raw) != approval_sha256:
        raise Refused("APPROVAL_FILE_DIGEST_MISMATCH")
    approval = json.loads(raw.decode("utf-8"))
    if (
        approval.get("packet_id"),
        approval.get("packet_version"),
        approval.get("packet_sha256"),
    ) != (packet["packet_id"], packet["packet_version"], packet["packet_sha256"]):
        raise Refused("OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET")
    if (
        approval.get("decision") != APPROVAL_DECISION
        or not str(approval.get("approved_by", "")).strip()
        or not str(approval.get("operator_statement", "")).strip()
    ):
        raise Refused("OPERATOR_APPROVAL_INCOMPLETE")
    for accepted in (
        "accepts_hard_ceiling_usd",
        "accepts_retention_bound",
        "accepts_retry_interpretation",
    ):
        if approval.get(accepted) is not True:
            raise Refused("OPERATOR_APPROVAL_INCOMPLETE", accepted)
    if (
        approval.get("accepted_hard_ceiling_usd")
        != packet["execution_bounds"]["hard_ceiling_usd_approved"]
    ):
        raise Refused("OPERATOR_APPROVAL_INCOMPLETE", "the accepted ceiling is not the packet's")
    return approval


def refuse_if_attempted(attempt_path: pathlib.Path) -> None:
    if attempt_path.exists():
        raise Refused("EVALUATION_APPROVAL_ALREADY_SPENT", attempt_path.name)


def write_attempt_started(
    attempt_path: pathlib.Path, packet: dict[str, Any], approval_sha256: str
) -> None:
    with attempt_path.open("x", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "state": "ATTEMPT_STARTED",
                    "packet_sha256": packet["packet_sha256"],
                    "approval_sha256": approval_sha256,
                    "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
                },
                indent=1,
            )
            + "\n"
        )


@dataclass
class RecordingTransport:
    """Wraps a transport to keep what the adapter does not surface: stop_reason and request-id. It keeps
    no body of an error response, only its digest."""

    inner: Any
    responses: list[dict[str, Any]] = field(default_factory=list)

    def post_json(
        self, url: str, headers: dict[str, str], body: dict[str, Any], timeout_seconds: float
    ) -> Any:
        response = self.inner.post_json(url, headers, body, timeout_seconds)
        entry: dict[str, Any] = {
            "status": response.status,
            "request_id": response.header("request-id"),
            "body_sha256": _sha(response.body),
        }
        if response.status == 200:
            try:
                entry["stop_reason"] = json.loads(response.body.decode("utf-8")).get("stop_reason")
            except (ValueError, UnicodeDecodeError):
                entry["stop_reason"] = None
        self.responses.append(entry)
        return response


def _call_once(gateway: Any, request: Any) -> Any:
    """The ONE model call site in this repository for semantic extraction."""
    return gateway.complete(request)


def execute(
    packet: dict[str, Any],
    surfaces: dict[str, str],
    gateway: Any,
    recorder: RecordingTransport,
    out_dir: pathlib.Path,
    *,
    workspace_id: str,
) -> dict[str, Any]:
    from sros_contracts import LlmTier
    from sros_llm_gateway.providers.anthropic import (
        AnthropicCompletion,
        classify_forced_tool_completion,
    )
    from sros_llm_gateway.types import ProviderError, SchemaValidationError
    from sros_semantic_extraction import (
        AttemptOutcome,
        ExecutionBinding,
        build_extraction_request,
        interpret_payload,
        may_retry,
    )
    from sros_semantic_extraction_contract import ExtractionContext, surface_sha256

    if packet.get("status") != READY:
        raise Refused("PACKET_NOT_READY_FOR_APPROVAL", str(packet.get("status")))
    if out_dir.resolve().is_relative_to(ROOT.resolve()):
        raise Refused("OUTPUT_DIRECTORY_INSIDE_THE_REPOSITORY")
    bounds = packet["execution_bounds"]
    binding = ExecutionBinding(
        packet["packet_id"], workspace_id, LlmTier.STRONG_MODEL, bounds["timeout_seconds"]
    )
    records = [
        r
        for r in packet["selection"]["records"]
        if r["normalized_record_id"] in set(packet["selection"]["egress_approved_record_ids"])
    ]
    calls = 0
    results = []
    for index, record in enumerate(records):
        surface = surfaces[record["normalized_record_id"]]
        if surface_sha256(surface) != record["surface_sha256"]:
            raise Refused("SURFACE_CHANGED_SINCE_THE_PACKET", record["normalized_record_id"])
        context = ExtractionContext(
            workspace_id=workspace_id,
            normalized_record_id=record["normalized_record_id"],
            observation_key="",
            source_id=packet["source"]["source_id"],
            surface=surface,
            expected_surface_sha256=record["surface_sha256"],
            visible_length=len(surface),
            extractor_id="sros_semantic_extraction",
            extractor_version=packet["tool"]["version"],
            prompt_id=packet["prompt"]["id"],
            prompt_version=packet["prompt"]["version"],
            provider=packet["provider"]["provider_id"],
            model=packet["provider"]["model"],
        )
        attempts: list[dict[str, Any]] = []
        schema_retries = 0
        while True:
            if calls >= bounds["max_calls"]:
                raise Refused("MAX_CALLS_REACHED", str(calls))
            request = build_extraction_request(surface, index, binding)
            calls += 1
            seen = len(recorder.responses)
            try:
                response = _call_once(gateway, request)
            except SchemaValidationError as exc:
                outcome, report, payload = AttemptOutcome.SCHEMA_FAILURE, None, None
                error = {"class": type(exc).__name__, "sha256": _sha(str(exc).encode())}
            except ProviderError as exc:
                outcome, report, payload = AttemptOutcome.PROVIDER_ERROR, None, None
                error = {
                    "class": type(exc).__name__,
                    "status": getattr(exc, "status_code", None),
                    "sha256": _sha(str(exc).encode()),
                }
            else:
                error = None
                stop = (
                    recorder.responses[seen]["stop_reason"]
                    if len(recorder.responses) > seen
                    else None
                )
                completion = classify_forced_tool_completion(stop)
                payload = response.structured
                if completion is AnthropicCompletion.OUTPUT_LIMIT_REACHED:
                    outcome, report = AttemptOutcome.OUTPUT_LIMIT_REACHED, None
                elif completion is AnthropicCompletion.REFUSED:
                    outcome, report = AttemptOutcome.MODEL_REFUSED, None
                elif completion is not AnthropicCompletion.COMPLETE:
                    outcome, report = AttemptOutcome.SCHEMA_FAILURE, None
                else:
                    outcome, report = interpret_payload(payload, context)
            attempts.append(
                {"outcome": outcome.value, "error": error, "transport": recorder.responses[seen:]}
            )
            if may_retry(outcome, schema_retries):
                schema_retries += 1
                continue
            break
        results.append(
            {
                "normalized_record_id": record["normalized_record_id"],
                "attempts": attempts,
                "payload": payload,
                "refusals": [list(r) for r in report.refusals] if report else None,
                "accepted": bool(report and report.accepted),
            }
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    run = {
        "packet_sha256": packet["packet_sha256"],
        "calls": calls,
        "records": results,
        "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "canonical_writes": 0,
    }
    (out_dir / f"run-{packet['packet_sha256'][:12]}.json").write_text(
        json.dumps(run, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approval-sha256")
    parser.add_argument("--output-dir")
    args = parser.parse_args(argv)
    sys.path.insert(0, str(ROOT / "infrastructure" / "scripts"))
    packet = verify_packet()
    print(
        f"packet {packet['packet_id']} v{packet['packet_version']} {packet['packet_sha256']} status {packet['status']}"
    )
    for blocker in packet["blockers"]:
        print(f"blocker  {blocker}")
    if not args.execute:
        print("dry run: no transport was built and nothing was sent")
        return 0
    check_approval(packet, APPROVAL, args.approval_sha256)
    refuse_if_attempted(ATTEMPT)
    if not args.output_dir:
        raise Refused("OUTPUT_DIRECTORY_NOT_SUPPLIED")
    import os

    from build_semantic_egress_eligibility import development_surfaces
    from sros_acquisition.compliance.inference import (
        authorize_external_inference,
        load_provider_policy,
    )
    from sros_acquisition.registry.catalog import load_catalog
    from sros_contracts import LlmTier
    from sros_llm_gateway.config import GatewayConfig, TierBinding
    from sros_llm_gateway.gateway import LlmGateway
    from sros_llm_gateway.providers.anthropic import AnthropicThinking
    from sros_llm_gateway.providers.anthropic_strict import AnthropicStrictToolProvider
    from sros_llm_gateway.transport import UrllibTransport

    catalog = load_catalog(DATA / "source-catalog-v1.json")
    profile = next(
        p for p in catalog.use_profiles if p.use_profile_id == packet["source"]["use_profile_id"]
    )
    authorization = authorize_external_inference(
        catalog.get("stack-exchange"),
        profile,
        "anthropic",
        policy=load_provider_policy(DATA / "model-provider-policy-v1.json"),
        provider_configured=bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()),
    )
    if not authorization.authorized:
        raise Refused("EXTERNAL_INFERENCE_NOT_AUTHORIZED", ",".join(authorization.refusal_reasons))
    surfaces = development_surfaces()
    write_attempt_started(ATTEMPT, packet, args.approval_sha256)
    recorder = RecordingTransport(UrllibTransport())
    config = GatewayConfig(
        routing_version=packet["packet_sha256"],
        bindings={
            LlmTier.STRONG_MODEL: TierBinding(
                LlmTier.STRONG_MODEL, "anthropic", packet["provider"]["model"]
            )
        },
    )
    gateway = LlmGateway(config=config)
    gateway.register(
        AnthropicStrictToolProvider(
            transport=recorder,
            thinking=AnthropicThinking.DISABLED,
            max_output_tokens=packet["execution_bounds"]["max_output_tokens_per_call"],
        )
    )
    run = execute(
        packet,
        surfaces,
        gateway,
        recorder,
        pathlib.Path(args.output_dir),
        workspace_id=os.environ.get("SROS_WORKSPACE_ID", "00000000-0000-4000-8000-000000000001"),
    )
    print(f"run finished: {run['calls']} calls; outputs outside the repository")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "infrastructure" / "scripts"))
    sys.exit(main())
