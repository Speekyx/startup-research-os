"""Mission 1.85.4 (N08-B). The only execution path for a semantic-extraction evaluation run.

DRY BY DEFAULT. Without `--execute` it verifies the packet and exits having built no transport and sent
nothing. With `--execute` it refuses, in this order and before any transport exists:

    1. a packet whose recomputed digest differs from its recorded digest or from EXPECTED_PACKET_SHA256
    2. an approval flag written into the packet, or a reference block that is not a human reference
       (Mission 1.85.5: a SINGLE_HUMAN_REFERENCE must carry RESULT_SCOPE DEVELOPMENT_PILOT and
       PILOT_NOT_CERTIFICATION, and never reach holdout)
    3. any packet status other than READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL (before reading an approval)
    4. a missing --approval-sha256, a missing approval file, or an approval file whose sha256 differs
    5. an approval that does not name this packet id, version and digest, or does not accept the ceiling,
       the retention bound, the retry interpretation and the packet's reference strength
    6. an existing attempt record (an approval is spent by the attempt, whatever the outcome)
    7. (Mission 1.85.7) no operator-accepted hard ceiling, provider documentation that is not verified or
       is past its review interval, or an accepted ceiling below the retry worst case plus one call at the
       documented maximum
    8. a failed ADR-033 four-gate authorization

During the run (Mission 1.85.7) a call, including a retry, starts only if what has been spent plus one call
at the documented maximum stays within the accepted ceiling. Each HTTP 200 is charged its reported usage;
a call without reported usage is charged the documented maximum; a reported input above the record's
conservative bound stops the run. Every stop writes the partial run record first.

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
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
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
EXPECTED_PACKET_SHA256 = "63c7302d64d52aa49e56060de1a2d92ffdb8e2030e9c19ba550acba0cc357993"
HUMAN_REFERENCE_STRENGTHS = ("SINGLE_HUMAN_REFERENCE", "MULTI_HUMAN_REFERENCE")


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
    check_reference(packet)
    return packet


def check_reference(packet: dict[str, Any]) -> None:
    reference = packet.get("reference") or {}
    strength = reference.get("REFERENCE_STRENGTH")
    if packet.get("status") == READY and strength not in HUMAN_REFERENCE_STRENGTHS:
        raise Refused("READY_WITHOUT_A_HUMAN_REFERENCE", str(strength))
    if strength == "SINGLE_HUMAN_REFERENCE" and (
        reference.get("RESULT_SCOPE") != "DEVELOPMENT_PILOT"
        or reference.get("result_label") != "PILOT_NOT_CERTIFICATION"
        or reference.get("holdout_reference_permitted") is not False
        or reference.get("ai_annotations_used_as_reference") != 0
    ):
        raise Refused("SINGLE_HUMAN_REFERENCE_OVERCLAIMED")


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
    if packet["execution_bounds"].get("hard_ceiling_usd_approved") in (None, ""):
        raise Refused("COST_CEILING_NOT_ACCEPTED")
    if (
        approval.get("accepted_hard_ceiling_usd")
        != packet["execution_bounds"]["hard_ceiling_usd_approved"]
    ):
        raise Refused("OPERATOR_APPROVAL_INCOMPLETE", "the accepted ceiling is not the packet's")
    if approval.get("accepted_reference_strength") != (packet.get("reference") or {}).get(
        "REFERENCE_STRENGTH"
    ):
        raise Refused(
            "OPERATOR_APPROVAL_INCOMPLETE", "the accepted reference strength is not the packet's"
        )
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
                parsed = json.loads(response.body.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                parsed = {}
            entry["stop_reason"] = parsed.get("stop_reason") if isinstance(parsed, dict) else None
            usage = parsed.get("usage") if isinstance(parsed, dict) else None
            if isinstance(usage, dict) and all(
                isinstance(usage.get(k), int) for k in ("input_tokens", "output_tokens")
            ):
                # Numbers only. Cache fields are charged as input: the request sends no cache_control,
                # and a cache token that did appear is still a billed token.
                entry["usage"] = {
                    "input_tokens": usage["input_tokens"]
                    + int(usage.get("cache_creation_input_tokens") or 0)
                    + int(usage.get("cache_read_input_tokens") or 0),
                    "output_tokens": usage["output_tokens"],
                }
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
    from sros_semantic_extraction.cost import CeilingRefusalError
    from sros_semantic_extraction_contract import ExtractionContext, surface_sha256

    if packet.get("status") != READY:
        raise Refused("PACKET_NOT_READY_FOR_APPROVAL", str(packet.get("status")))
    if out_dir.resolve().is_relative_to(ROOT.resolve()):
        raise Refused("OUTPUT_DIRECTORY_INSIDE_THE_REPOSITORY")
    bounds = packet["execution_bounds"]
    ledger = cost_ledger(packet)
    try:
        ledger.preflight(Decimal(bounds["retry_worst_case_usd"]))
    except CeilingRefusalError as exc:
        raise Refused(exc.code, str(exc)) from None
    input_bounds = bounds["per_record_conservative_input_tokens"]
    binding = ExecutionBinding(
        packet["packet_id"], workspace_id, LlmTier.STRONG_MODEL, bounds["timeout_seconds"]
    )
    records = [
        r
        for r in packet["selection"]["records"]
        if r["normalized_record_id"] in set(packet["selection"]["egress_approved_record_ids"])
    ]
    calls = 0
    results: list[dict[str, Any]] = []
    reference = packet.get("reference") or {}

    def write_run(stopped: str | None) -> dict[str, Any]:
        out_dir.mkdir(parents=True, exist_ok=True)
        run = {
            "packet_sha256": packet["packet_sha256"],
            "REFERENCE_STRENGTH": reference.get("REFERENCE_STRENGTH"),
            "RESULT_SCOPE": reference.get("RESULT_SCOPE"),
            "result_label": reference.get("result_label"),
            "calls": calls,
            "stopped": stopped,
            "cost": {
                "accepted_hard_ceiling_usd": bounds["hard_ceiling_usd_approved"],
                "spent_usd": str(ledger.spent_usd),
                "charges": ledger.charges,
            },
            "records": results,
            "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "canonical_writes": 0,
        }
        (out_dir / f"run-{packet['packet_sha256'][:12]}.json").write_text(
            json.dumps(run, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return run

    def halt(code: str, detail: str) -> Refused:
        write_run(code)
        return Refused(code, detail)

    for index, record in enumerate(records):
        surface = surfaces[record["normalized_record_id"]]
        if surface_sha256(surface) != record["surface_sha256"]:
            raise halt("SURFACE_CHANGED_SINCE_THE_PACKET", record["normalized_record_id"])
        input_bound = input_bounds.get(record["normalized_record_id"])
        if not isinstance(input_bound, int):
            raise halt("RECORD_WITHOUT_A_COST_BOUND", record["normalized_record_id"])
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
                raise halt("MAX_CALLS_REACHED", str(calls))
            try:
                ledger.authorise_next_call()
            except CeilingRefusalError as exc:
                raise halt(exc.code, str(exc)) from None
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
            usages = [e["usage"] for e in recorder.responses[seen:] if "usage" in e]
            if usages:
                for usage in usages:
                    ledger.charge_usage(usage["input_tokens"], usage["output_tokens"])
                if any(u["input_tokens"] > input_bound for u in usages):
                    results.append(
                        {
                            "normalized_record_id": record["normalized_record_id"],
                            "attempts": attempts,
                        }
                    )
                    raise halt(
                        "CONSERVATIVE_INPUT_BOUND_EXCEEDED",
                        f"reported input exceeded {input_bound} tokens; the cost model is wrong",
                    )
            else:
                ledger.charge_unknown()
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
    return write_run(None)


def cost_ledger(packet: dict[str, Any]) -> Any:
    """The ledger for this packet, or a refusal. The accepted ceiling is the operator's; nothing defaults it."""
    from sros_semantic_extraction.cost import CostLedger, Prices

    bounds = packet["execution_bounds"]
    accepted = bounds.get("hard_ceiling_usd_approved")
    if accepted in (None, ""):
        raise Refused("COST_CEILING_NOT_ACCEPTED")
    try:
        prices = Prices(
            Decimal(str(bounds["price_usd_per_mtok"]["input"])),
            Decimal(str(bounds["price_usd_per_mtok"]["output"])),
            Decimal(str(bounds["price_multiplier"])),
        )
        return CostLedger(
            prices=prices,
            ceiling_usd=Decimal(str(accepted)),
            per_call_maximum_usd=Decimal(str(bounds["per_call_documented_maximum_usd"])),
        )
    except (KeyError, TypeError, ValueError, ArithmeticError):
        raise Refused("PROVIDER_PRICING_NOT_ESTABLISHED") from None


def check_provider_verification(packet: dict[str, Any], today: date) -> None:
    verification = (packet.get("provider") or {}).get("verification") or {}
    if verification.get("status") != "VERIFIED" or verification.get("model_state") != "ACTIVE":
        raise Refused("PROVIDER_VERIFICATION_NOT_ESTABLISHED")
    try:
        retrieved = date.fromisoformat(str(verification["retrieved_on"]))
        interval = int(verification["review_interval_days"])
    except (KeyError, TypeError, ValueError):
        raise Refused("PROVIDER_VERIFICATION_NOT_ESTABLISHED") from None
    if today > retrieved + timedelta(days=interval):
        raise Refused("PROVIDER_VERIFICATION_EXPIRED", str(retrieved))


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
    check_provider_verification(packet, datetime.now(UTC).date())
    cost_ledger(packet).preflight(Decimal(packet["execution_bounds"]["retry_worst_case_usd"]))
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
