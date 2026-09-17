"""Mission 1.85.4 (N08-B), reference strength added in Mission 1.85.5, operator decisions and the measured
cost model in Mission 1.85.7, recorded operator decisions and a bound retry policy in Mission 1.85.8. The frozen
evaluation packet for a FUTURE development-split extraction run.

The packet binds everything a run would depend on, and it cannot be executed:

- its `status` is computed from facts: BLOCKED_HUMAN_LABELS while no human reference gate is satisfied,
  BLOCKED_OPERATOR_DECISIONS while a human reference exists but egress decisions, threshold authorisation,
  the retry ratification or the ceiling are missing; the runner refuses any status other than
  READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL before it reads an approval;
- its `reference` block states what a result could claim. Exactly one genuine human annotation is a
  SINGLE_HUMAN_REFERENCE: RESULT_SCOPE DEVELOPMENT_PILOT, result label PILOT_NOT_CERTIFICATION, and only
  the pilot-valid thresholds are read. Two or more plus adjudication is the unchanged
  MULTI_HUMAN_REFERENCE path;
- an approval is never written into the packet (that would change the approved bytes); it is a separate
  file, named by the packet digest, that only the operator creates after the final digest is known;
- the packet carries DEVELOPMENT records only; holdout is never in a prompt-development packet;
- (Mission 1.85.8) it binds the operator's recorded decisions by digest: the decisions file, a digest of the
  threshold decisions alone, and a retry policy block whose digest covers the ratified reading and the file
  implementing it. Changing any bound artifact changes the packet digest, so an approval for an earlier
  digest cannot unlock a later packet.

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
from sros_semantic_extraction.decisions import (  # noqa: E402
    accepted_ceiling,
    operator_decision_blockers,
    provider_blockers,
)
from sros_semantic_extraction_contract import (  # noqa: E402
    CONTRACT_ID,
    CONTRACT_VERSION,
    LABEL_SET_ID,
    LABEL_SET_VERSION,
    SURFACE_ID,
    SURFACE_VERSION,
)
from sros_semantic_extraction_contract.reference import (  # noqa: E402
    HOLDOUT_POLICY,
    PILOT_ROADMAP_STATUS,
    PROHIBITED_PILOT_CLAIMS,
    REFERENCE_MODEL_ID,
    ReferenceStrength,
    assess_reference,
    holdout_reference_permitted,
)

DATA = ROOT / "docs" / "data"
RETRY_IMPLEMENTATION = (
    ROOT / "packages" / "semantic-extraction" / "python" / "sros_semantic_extraction" / "request.py"
)
PACKET = DATA / "semantic-extraction-evaluation-packet-development-v1.json"
CORPUS = DATA / "stack-overflow-semantic-evaluation-corpus-v1.json"
ELIGIBILITY = DATA / "stack-overflow-semantic-egress-eligibility-development-v1.json"
REQUALIFICATION = DATA / "anthropic-api-route-requalification-v1.json"
CONTRACT = DATA / "first-person-semantic-extraction-contract-v1.json"
CATALOG = DATA / "source-catalog-v1.json"
PROVIDER_POLICY = DATA / "model-provider-policy-v1.json"
VERIFICATION = DATA / "anthropic-claude-sonnet-5-pilot-verification-v1.json"
DECISION_PACKAGE = DATA / "semantic-extraction-operator-decision-package-development-v1.json"
DECISIONS = DATA / "semantic-extraction-operator-decisions-development-v1.json"
ANNOTATION_GLOB = "stack-overflow-semantic-annotations-development-*-v1.json"
ADJUDICATION = DATA / "stack-overflow-semantic-adjudication-development-v1.json"
THRESHOLD_PARTITION = DATA / "semantic-extraction-threshold-partition-v1.json"

PACKET_ID = "semantic-extraction-evaluation-packet-development"
PACKET_VERSION = 4
RETRY_POLICY_ID = "semantic-extraction-schema-failure-retry-policy"
RETRY_POLICY_VERSION = "1.0.0"
READY = "READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL"
BLOCKED = "BLOCKED_HUMAN_LABELS"
BLOCKED_DECISIONS = "BLOCKED_OPERATOR_DECISIONS"
MODEL = "claude-sonnet-5"
MAX_OUTPUT_TOKENS = 4096
TIMEOUT_SECONDS = 240.0
CONTEXT_WINDOW_TOKENS = 1_000_000
# Fields excluded from the digest: the digest itself, commentary and derived presentation.
UNBOUND = {"$comment", "packet_sha256", "status_note"}


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


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
    verification = json.loads(VERIFICATION.read_text("utf-8"))
    package = json.loads(DECISION_PACKAGE.read_text("utf-8"))
    decisions = json.loads(DECISIONS.read_text("utf-8"))
    cost = package["C_hard_ceiling"]
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
    calls_per_record = 1 + MAX_SCHEMA_RETRIES_PER_RECORD
    cost_facts_current = cost["approved_record_count"] == len(approved) and set(
        cost["per_record_conservative_input_tokens"]
    ) == {r["normalized_record_id"] for r in approved}

    annotation_files = sorted(DATA.glob(ANNOTATION_GLOB))
    reference = assess_reference(
        [(p.name, json.loads(p.read_text("utf-8"))) for p in annotation_files],
        split_record_ids={r["normalized_record_id"] for r in development},
        surface_sha256_by_id={r["normalized_record_id"]: r["surface_sha256"] for r in development},
        adjudication_present=ADJUDICATION.exists(),
    )
    single = reference.strength is ReferenceStrength.SINGLE_HUMAN_REFERENCE
    blockers = []
    for name, problems in reference.refused_files:
        blockers.append(f"HUMAN_ANNOTATION_FILE_REFUSED: {name} ({', '.join(problems[:5])})")
    if not single and len(reference.human_files) < 2:
        blockers.append(
            f"HUMAN_LABELS_PENDING: {len(reference.human_files)} valid committed development annotation files (exactly 1 for a SINGLE_HUMAN_REFERENCE pilot, at least 2 plus adjudication for MULTI_HUMAN_REFERENCE)"
        )
    if not single and not ADJUDICATION.exists():
        blockers.append("ADJUDICATION_PENDING")
    if (
        len(reference.human_files) >= 2
        and ADJUDICATION.exists()
        and not reference.refused_files
        and not reference.multi_human_gate
    ):
        blockers.append("MULTI_HUMAN_REFERENCE_INVALID: duplicate annotator ids")
    if not approved:
        blockers.append(
            f"EGRESS_REVIEW_PENDING: 0 EGRESS_APPROVED records ({eligibility['state_counts']})"
        )
    if approved and not cost_facts_current:
        blockers.append(
            "COST_FACTS_STALE: the decision package does not cover exactly the approved records; re-measure and re-render"
        )
    blockers.extend(provider_blockers(verification, MODEL))
    if single:
        # The pilot reads only the thresholds that need neither a second human nor holdout, and each is
        # the operator's decision in the decisions file; the partition statuses are never edited.
        blockers.extend(operator_decision_blockers(package, decisions))
    else:
        if not all(i["status"] == "AUTHORISED" for i in contract["proposed_thresholds"]["items"]):
            blockers.append(
                "THRESHOLDS_NOT_AUTHORISED: every evaluation threshold is PROPOSED_NOT_AUTHORISED"
            )
        blockers.append(
            "RETRY_INTERPRETATION_NOT_RATIFIED: the operator has not ratified the schema-failure retry reading"
        )
        blockers.append("COST_CEILING_NOT_ACCEPTED: the multi-human path has no accepted ceiling")
    accepted = accepted_ceiling(package, decisions) if single else None
    threshold_decisions = [
        {
            key: d.get(key)
            for key in (
                "item_id",
                "operator_decision",
                "revised_value",
                "repeatability_disposition",
            )
            if key in d
        }
        for d in decisions.get("A_pilot_thresholds", [])
    ]
    retry = package["B_retry"]
    retry_rule = {
        "max_schema_retries_per_record": MAX_SCHEMA_RETRIES_PER_RECORD,
        "reading": retry["proposed_reading"],
        "inside_the_retry_class": retry["inside_the_retry_class"],
        "outside_the_retry_class": retry["outside_the_retry_class"],
        "implemented_as": retry["implemented_as"],
    }

    if reference.strength is ReferenceStrength.NO_HUMAN_REFERENCE:
        status = BLOCKED
    else:
        status = BLOCKED_DECISIONS if blockers else READY
    packet: dict[str, Any] = {
        "$comment": "FROZEN FUTURE EVALUATION PACKET (N08-B). NOT EXECUTABLE. Its status is computed from committed facts; the runner refuses any status but READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL before reading an approval, and an approval is a separate operator file named by this packet's digest. Merging this packet authorises nothing. The reference block states what a result could claim: a SINGLE_HUMAN_REFERENCE result is a DEVELOPMENT_PILOT and PILOT_NOT_CERTIFICATION.",
        "packet_id": PACKET_ID,
        "packet_version": PACKET_VERSION,
        "mission": "1.85.8",
        "status": status,
        "blockers": blockers,
        "reference": {
            "model": REFERENCE_MODEL_ID,
            "REFERENCE_STRENGTH": reference.strength.value,
            "RESULT_SCOPE": reference.result_scope,
            "result_label": reference.result_label,
            "pilot_gate_satisfied": reference.pilot_gate,
            "multi_human_gate_satisfied": reference.multi_human_gate,
            "human_annotation_files": list(reference.human_files),
            "refused_annotation_files": [name for name, _ in reference.refused_files],
            "ai_annotations_used_as_reference": 0,
            "inter_annotator_agreement": reference.inter_annotator_agreement,
            "prohibited_claims": list(PROHIBITED_PILOT_CLAIMS) if single else [],
            "holdout_policy": HOLDOUT_POLICY,
            "holdout_reference_permitted": holdout_reference_permitted(reference.strength),
            "threshold_partition": {
                "file": "docs/data/semantic-extraction-threshold-partition-v1.json",
                "sha256": sha(THRESHOLD_PARTITION),
                "thresholds_read": "SINGLE_HUMAN_PILOT_VALID"
                if single
                else "contract proposed_thresholds, every item",
            },
            "roadmap_status_when_ready": PILOT_ROADMAP_STATUS if single else None,
        },
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
            "verification": {
                "file": "docs/data/anthropic-claude-sonnet-5-pilot-verification-v1.json",
                "sha256": sha(VERIFICATION),
                "status": verification.get("status"),
                "model_state": (verification.get("model") or {}).get("documented_state"),
                "retrieved_on": verification.get("retrieved_on"),
                "review_interval_days": verification.get("review_interval_days"),
                "zero_data_retention_for_this_account": (verification.get("data_use") or {}).get(
                    "zero_data_retention_for_this_account"
                ),
            },
        },
        "operator_decisions": {
            "package": "docs/data/semantic-extraction-operator-decision-package-development-v1.json",
            "package_sha256": sha(DECISION_PACKAGE),
            "decisions": "docs/data/semantic-extraction-operator-decisions-development-v1.json",
            "decisions_sha256": sha(DECISIONS),
            "decided_by": decisions.get("decided_by"),
            "decided_at": decisions.get("decided_at"),
            "threshold_decisions": threshold_decisions,
            "threshold_decisions_sha256": canonical_sha(threshold_decisions),
            "thresholds_authorised": [
                d["item_id"]
                for d in threshold_decisions
                if d.get("operator_decision") == "AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT"
            ],
            "thresholds_rejected_for_the_pilot": [
                d["item_id"]
                for d in threshold_decisions
                if d.get("operator_decision") == "REJECT_FOR_THE_PILOT"
            ],
            "retry_decision": decisions["B_retry"].get("operator_decision"),
            "ceiling_decision": decisions["C_hard_ceiling"].get("operator_decision"),
            "accepted_hard_ceiling_usd": decisions["C_hard_ceiling"].get(
                "accepted_hard_ceiling_usd"
            ),
            "additional_repeatability_runs_authorised": 0,
        },
        "retry_policy": {
            "id": RETRY_POLICY_ID,
            "version": RETRY_POLICY_VERSION,
            **retry_rule,
            "provider_fallback": None,
            "model_fallback": None,
            "implementation_file": "packages/semantic-extraction/python/sros_semantic_extraction/request.py",
            "implementation_sha256": sha(RETRY_IMPLEMENTATION),
            "rule_sha256": canonical_sha(retry_rule),
            "operator_decision": decisions["B_retry"].get("operator_decision"),
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
            "EXPECTED_CALLS": cost["EXPECTED_CALLS"],
            "MAX_CALLS_WITH_RETRY": cost["MAX_CALLS_WITH_RETRY"],
            "context_window_tokens": CONTEXT_WINDOW_TOKENS,
            "max_output_tokens_per_call": MAX_OUTPUT_TOKENS,
            "price_usd_per_mtok": {
                "input": cost["pricing"]["input_usd_per_mtok"],
                "output": cost["pricing"]["output_usd_per_mtok"],
            },
            "price_multiplier": cost["pricing"]["multiplier_applied"],
            "price_source": f"{cost['pricing']['source']} (retrieved {cost['pricing']['retrieved_on']})",
            "cost_model": cost["token_estimation_methodology"]["cost_model"],
            "planning_estimate_usd": cost["planning_estimate_usd"],
            "conservative_bound_usd": cost["conservative_bound_usd"],
            "retry_worst_case_usd": cost["retry_worst_case_usd"],
            "per_call_documented_maximum_usd": cost["per_call_documented_maximum_usd"],
            "per_record_conservative_input_tokens": cost["per_record_conservative_input_tokens"],
            "proposed_hard_ceiling_usd": cost["proposed_hard_ceiling_usd"],
            "hard_ceiling_usd_approved": accepted,
            "hard_ceiling_basis": cost["token_estimation_methodology"]["ceiling_rule"],
            "enforcement": cost["enforcement"],
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
                "REFERENCE_STRENGTH, RESULT_SCOPE and result_label copied from this packet",
            ],
            "canonical_writes": "none: no finding, Signal, Claim, Evidence, independence state or score",
        },
        "approval_requirements": {
            "file": "docs/data/semantic-extraction-evaluation-approval-development-v1.json, created only by the operator after this packet's final digest is known",
            "decision": "APPROVE_EXACTLY_ONE_EVALUATION_RUN",
            "must_name": ["packet_id", "packet_version", "packet_sha256"],
            "must_accept": [
                "hard_ceiling_usd_approved",
                "retention_bound",
                "retry_interpretation",
                "reference strength: accepted_reference_strength equals REFERENCE_STRENGTH",
            ],
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
