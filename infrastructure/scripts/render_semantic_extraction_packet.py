"""Mission 1.85.4 (N08-B). The frozen evaluation packet for a FUTURE development-split extraction run.

The packet binds everything a run would depend on, and it cannot be executed:

- its `status` is computed from facts, and while human labels, egress decisions, threshold
  authorisation or the retry ratification are missing it is BLOCKED_HUMAN_LABELS; the runner refuses any
  status other than READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL before it reads an approval;
- an approval is never written into the packet (that would change the approved bytes); it is a separate
  file, named by the packet digest, that only the operator creates after the final digest is known;
- the packet carries DEVELOPMENT records only; holdout is never in a prompt-development packet.

Reads committed artifacts only (no database, no network, no model). `--write` renders; `--check` fails
if the committed packet is stale.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
for path in (
    "packages/semantic-extraction-contract/python",
    "packages/semantic-extraction/python",
    "packages/llm-gateway/python",
    "packages/contracts/python",
):
    sys.path.insert(0, str(ROOT / path))

from sros_semantic_extraction import (  # noqa: E402
    CANONICAL_SCHEMA,
    MAX_SCHEMA_RETRIES_PER_RECORD,
    PROMPT_ID,
    PROMPT_VERSION,
    STRICT_SCHEMA,
    TOOL_ID,
    TOOL_VERSION,
    prompt_sha256,
    schema_sha256,
)
from sros_semantic_extraction.prompt import SYSTEM_INSTRUCTIONS, TASK_INSTRUCTIONS  # noqa: E402
from sros_semantic_extraction_contract import (  # noqa: E402
    CONTRACT_ID,
    CONTRACT_VERSION,
    LABEL_SET_ID,
    LABEL_SET_VERSION,
    SURFACE_ID,
    SURFACE_VERSION,
)

DATA = ROOT / "docs" / "data"
PACKET = DATA / "semantic-extraction-evaluation-packet-development-v1.json"
CORPUS = DATA / "stack-overflow-semantic-evaluation-corpus-v1.json"
ELIGIBILITY = DATA / "stack-overflow-semantic-egress-eligibility-development-v1.json"
REQUALIFICATION = DATA / "anthropic-api-route-requalification-v1.json"
CONTRACT = DATA / "first-person-semantic-extraction-contract-v1.json"
CATALOG = DATA / "source-catalog-v1.json"
PROVIDER_POLICY = DATA / "model-provider-policy-v1.json"
COST_CEILING_RECORD = DATA / "second-opportunity-execution-cost-ceiling-v1.json"
ANNOTATION_GLOB = "stack-overflow-semantic-annotations-development-*-v1.json"
ADJUDICATION = DATA / "stack-overflow-semantic-adjudication-development-v1.json"

PACKET_ID = "semantic-extraction-evaluation-packet-development"
PACKET_VERSION = 1
READY = "READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL"
BLOCKED = "BLOCKED_HUMAN_LABELS"
MODEL = "claude-sonnet-5"
MAX_OUTPUT_TOKENS = 4096
TIMEOUT_SECONDS = 240.0
CONTEXT_WINDOW_TOKENS = 1_000_000
MEASURED_CHARACTERS_PER_TOKEN = 1.3373
US_ONLY_RESIDENCY_MULTIPLIER = 1.1
# Fields excluded from the digest: the digest itself, commentary and derived presentation.
UNBOUND = {"$comment", "packet_sha256", "status_note"}


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(packet: dict[str, Any]) -> str:
    bound = {k: v for k, v in packet.items() if k not in UNBOUND}
    return hashlib.sha256(
        json.dumps(bound, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def build() -> dict[str, Any]:
    corpus = json.loads(CORPUS.read_text("utf-8"))
    eligibility = json.loads(ELIGIBILITY.read_text("utf-8"))
    requal = json.loads(REQUALIFICATION.read_text("utf-8"))
    contract = json.loads(CONTRACT.read_text("utf-8"))
    ceiling = json.loads(COST_CEILING_RECORD.read_text("utf-8"))
    prices = ceiling["PROVIDER_FACTS"]["PRICE_USD_PER_MTOK"]["value"]
    catalog = json.loads(CATALOG.read_text("utf-8"))
    source = next(s for s in catalog["sources"] if s["source_id"] == "stack-exchange")
    local_reviews = [
        r
        for r in source.get("reviews", [])
        if r.get("assessed_use_profile") == "local-private-research-v1"
    ]
    source_review_version = max((r.get("review_version", 0) for r in local_reviews), default=None)

    development = [r for r in corpus["records"] if r["split"] == "DEVELOPMENT"]
    states = {r["normalized_record_id"]: r for r in eligibility["records"]}
    approved = [
        r for r in development if states[r["normalized_record_id"]]["state"] == "EGRESS_APPROVED"
    ]
    candidates = [
        r for r in development if states[r["normalized_record_id"]]["state"] != "EGRESS_EXCLUDED"
    ]

    fixed_chars = (
        len(SYSTEM_INSTRUCTIONS) + len(TASK_INSTRUCTIONS) + len(json.dumps(STRICT_SCHEMA)) + 200
    )

    def planning_usd(records: list[dict[str, Any]]) -> float:
        tokens_in = sum(
            (fixed_chars + r["surface_length"]) / MEASURED_CHARACTERS_PER_TOKEN for r in records
        )
        tokens_out = len(records) * MAX_OUTPUT_TOKENS
        return round(
            (tokens_in * prices["input"] + tokens_out * prices["output"])
            / 1_000_000
            * US_ONLY_RESIDENCY_MULTIPLIER,
            4,
        )

    calls_per_record = 1 + MAX_SCHEMA_RETRIES_PER_RECORD
    hard_per_call = (
        (CONTEXT_WINDOW_TOKENS * prices["input"] + MAX_OUTPUT_TOKENS * prices["output"])
        / 1_000_000
        * US_ONLY_RESIDENCY_MULTIPLIER
    )

    annotation_files = sorted(DATA.glob(ANNOTATION_GLOB))
    thresholds_authorised = all(
        i["status"] == "AUTHORISED" for i in contract["proposed_thresholds"]["items"]
    )
    blockers = []
    if len(annotation_files) < 2:
        blockers.append(
            f"HUMAN_LABELS_PENDING: {len(annotation_files)} of at least 2 committed development annotation files"
        )
    if not ADJUDICATION.exists():
        blockers.append("ADJUDICATION_PENDING")
    if not approved:
        blockers.append(
            f"EGRESS_REVIEW_PENDING: 0 EGRESS_APPROVED records ({eligibility['state_counts']})"
        )
    if not thresholds_authorised:
        blockers.append(
            "THRESHOLDS_NOT_AUTHORISED: every evaluation threshold is PROPOSED_NOT_AUTHORISED"
        )
    blockers.append(
        "RETRY_INTERPRETATION_NOT_RATIFIED: the operator has not ratified the schema-failure retry reading"
    )
    blockers.append(
        "COST_CEILING_NOT_ACCEPTED: the hard ceiling rests on the context window and needs operator acceptance"
    )

    packet: dict[str, Any] = {
        "$comment": "FROZEN FUTURE EVALUATION PACKET (N08-B). NOT EXECUTABLE. Its status is computed from committed facts; the runner refuses any status but READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL before reading an approval, and an approval is a separate operator file named by this packet's digest. Merging this packet authorises nothing.",
        "packet_id": PACKET_ID,
        "packet_version": PACKET_VERSION,
        "mission": "1.85.4",
        "status": READY if not blockers else BLOCKED,
        "blockers": blockers,
        "operator_approval_recorded": False,
        "contract": f"{CONTRACT_ID}@{CONTRACT_VERSION}",
        "contract_json_sha256": sha(CONTRACT),
        "surface": f"{SURFACE_ID}@{SURFACE_VERSION}",
        "label_set": f"{LABEL_SET_ID}@{LABEL_SET_VERSION}",
        "validator": f"sros_semantic_extraction_contract.validate_extraction@{CONTRACT_VERSION}",
        "prompt": {"id": PROMPT_ID, "version": PROMPT_VERSION, "sha256": prompt_sha256()},
        "tool": {
            "id": TOOL_ID,
            "version": TOOL_VERSION,
            "strict_schema_sha256": schema_sha256(STRICT_SCHEMA),
            "canonical_schema_sha256": schema_sha256(CANONICAL_SCHEMA),
            "strict_profile": "anthropic-strict-tool-capability@1.0.0",
            "forced": True,
            "strict": True,
            "other_tools": [],
        },
        "provider": {
            "provider_id": "anthropic",
            "route": "commercial API-key route, synchronous POST https://api.anthropic.com/v1/messages",
            "model": MODEL,
            "model_parameters": {
                "max_tokens": MAX_OUTPUT_TOKENS,
                "thinking": {"type": "disabled"},
                "temperature": "NOT_SENT (not carried by LlmRequest)",
                "tool_choice": "forced single tool",
                "service_tier": "NOT_SENT",
                "inference_geo": "NOT_SENT",
                "cache_control": "NOT_SENT",
            },
            "excluded_features": [
                "batch",
                "files_api",
                "mcp_connector",
                "web_search",
                "code_execution",
                "prompt_caching",
                "console_or_playground",
                "feedback",
            ],
            "fallback_provider": None,
            "provider_policy_sha256": sha(PROVIDER_POLICY),
            "requalification": {
                "file": "docs/data/anthropic-api-route-requalification-v1.json",
                "sha256": sha(REQUALIFICATION),
                "verdict": requal["verdict"],
                "retrieved_on": requal["retrieved_on"],
                "review_interval_days": requal["review_interval_days"],
            },
            "retention_bound": "30 days, except longer-retention services, a separate agreement, Usage Policy enforcement (flagged content up to 2 years, classifier scores up to 7 years) and legal compliance; ZDR not assumed",
        },
        "source": {
            "source_id": "stack-exchange",
            "resource_id": corpus["resource_id"],
            "use_profile_id": corpus["use_profile_id"],
            "local_review_version": source_review_version,
            "external_model_transmission": "PERMITTED_WITH_CONDITIONS",
            "catalog_sha256": sha(CATALOG),
        },
        "selection": {
            "split": "DEVELOPMENT",
            "holdout_included": False,
            "corpus": f"{corpus['corpus_id']}@{corpus['corpus_version']}",
            "corpus_sha256": sha(CORPUS),
            "records": [
                {
                    "normalized_record_id": r["normalized_record_id"],
                    "surface_sha256": r["surface_sha256"],
                    "surface_length": r["surface_length"],
                    "egress_state": states[r["normalized_record_id"]]["state"],
                }
                for r in development
            ],
            "egress_eligibility_sha256": sha(ELIGIBILITY),
            "egress_approved_record_ids": [r["normalized_record_id"] for r in approved],
            "egress_excluded_record_ids": [
                r["normalized_record_id"]
                for r in development
                if states[r["normalized_record_id"]]["state"] == "EGRESS_EXCLUDED"
            ],
            "egress_review_required_record_ids": [
                r["normalized_record_id"]
                for r in development
                if states[r["normalized_record_id"]]["state"] == "EGRESS_REVIEW_REQUIRED"
            ],
            "transmitted_fields": [
                "the surface text only, in one untrusted region labelled by an opaque packet-local index"
            ],
            "withheld_fields": [
                "score",
                "view_count",
                "answer_count",
                "is_answered",
                "accepted_answer_id",
                "tags",
                "question_url",
                "question_id",
                "author",
            ],
            "human_annotation_files": [
                {"file": p.name, "sha256": sha(p)} for p in annotation_files
            ],
        },
        "execution_bounds": {
            "transport_retries": 0,
            "schema_failure_retries_per_record": MAX_SCHEMA_RETRIES_PER_RECORD,
            "validator_refusal_retries": 0,
            "timeout_seconds": TIMEOUT_SECONDS,
            "max_calls": len(approved) * calls_per_record,
            "max_input_tokens_per_call": CONTEXT_WINDOW_TOKENS,
            "max_output_tokens_per_call": MAX_OUTPUT_TOKENS,
            "price_usd_per_mtok": prices,
            "price_source": "docs/data/second-opportunity-execution-cost-ceiling-v1.json PROVIDER_FACTS (retrieved 2026-09-14); to be re-verified when the operator approves",
            "residency_multiplier_assumed": US_ONLY_RESIDENCY_MULTIPLIER,
            "planning_cost_estimate_usd_approved": planning_usd(approved),
            "planning_cost_estimate_usd_if_every_reviewable_record_were_approved": planning_usd(
                candidates
            ),
            "planning_basis": f"characters / {MEASURED_CHARACTERS_PER_TOKEN} (the measured Mission 1.84.5 ratio), one call per record, full output bound; an estimate, never a bound",
            "hard_ceiling_usd_approved": round(len(approved) * calls_per_record * hard_per_call, 4),
            "hard_ceiling_basis": "every call at the full 1,000,000-token context window and the output bound, at the stated prices and multiplier; tokens per character are not established, so no smaller input bound is claimed",
        },
        "logging_policy": {
            "provider_error_bodies": "never logged or stored; record HTTP status, error type, request-id header and sha256 of the body only",
            "exception_text": "never logged (the adapter may include provider error detail); record the exception class and a sha256",
            "correlation_ids": "packet id and packet-local index only; never question text or record ids",
            "model_payloads": "stored locally outside the repository with the validation report; they contain verbatim quotes",
        },
        "expected_outputs": {
            "location": "a local directory outside the repository, named at execution",
            "per_record": [
                "normalized_record_id",
                "attempts (outcome, stop_reason, request_id)",
                "validation report",
                "validated extraction or refusal",
            ],
            "run_record": [
                "packet_sha256",
                "approval_sha256",
                "calls made",
                "usage and cost from the gateway",
                "started and finished timestamps",
            ],
            "canonical_writes": "none: no finding, Signal, Claim, Evidence, independence state or score",
        },
        "approval_requirements": {
            "file": "docs/data/semantic-extraction-evaluation-approval-development-v1.json, created only by the operator after this packet's final digest is known",
            "decision": "APPROVE_EXACTLY_ONE_EVALUATION_RUN",
            "must_name": ["packet_id", "packet_version", "packet_sha256"],
            "must_accept": ["hard_ceiling_usd_approved", "retention_bound", "retry_interpretation"],
            "runtime": "--execute --approval-sha256 <sha256 of the approval file>",
            "merge_is_not_approval": True,
        },
    }
    packet["packet_sha256"] = digest(packet)
    return packet


def dump(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    packet = build()
    if args.write:
        PACKET.write_bytes(dump(packet))
        print(f"wrote {PACKET.name}: status {packet['status']}, sha256 {packet['packet_sha256']}")
        return 0
    if not PACKET.exists() or PACKET.read_bytes() != dump(packet):
        print(f"FAIL     {PACKET.name} is stale")
        return 1
    print(f"ok       {PACKET.name} matches (status {packet['status']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
