"""Mission 1.85.7 (N08-B-PILOT), decisions mirrored in Mission 1.85.8. The final operator decision package for
the DEVELOPMENT pilot.

Computes, from committed artifacts only (no database, no network, no model), the facts behind the three
decisions the operator still has to make, and renders them. It never makes a decision:

- A. each single-human pilot threshold, individually;
- B. the retry reading;
- C. the hard cost ceiling.

The decisions themselves live in a separate operator-owned file that this script creates BLANK once and
never writes again. `decision_state` mirrors what that file records and every problem
`decision_record_problems` finds in it, so a recorded decision re-renders the package:

    docs/data/semantic-extraction-operator-decisions-development-v1.json   (operator-owned)
    docs/data/semantic-extraction-operator-decision-package-development-v1.json   (rendered)
    docs/data/semantic-extraction-operator-decision-package-development-v1.md     (rendered)

    uv run python infrastructure/scripts/render_semantic_extraction_decision_package.py --write
    uv run python infrastructure/scripts/render_semantic_extraction_decision_package.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from collections import Counter
from decimal import Decimal
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
for path in (
    "packages/semantic-extraction/python",
    "packages/semantic-extraction-contract/python",
    "packages/llm-gateway/python",
    "packages/contracts/python",
):
    sys.path.insert(0, str(ROOT / path))

from sros_semantic_extraction.cost import (  # noqa: E402
    COST_MODEL_ID,
    PLANNING_OUTPUT_TOKENS_PER_CALL,
    PLANNING_TOKENS_PER_BODY_BYTE,
    STRICT_PROMPT_ALLOWANCE_TOKENS,
    CostModel,
    Prices,
    money,
    proposed_hard_ceiling,
)
from sros_semantic_extraction.decisions import decision_record_problems  # noqa: E402

DATA = ROOT / "docs" / "data"
PACKAGE = DATA / "semantic-extraction-operator-decision-package-development-v1.json"
PAGE = DATA / "semantic-extraction-operator-decision-package-development-v1.md"
DECISIONS = DATA / "semantic-extraction-operator-decisions-development-v1.json"
PARTITION = DATA / "semantic-extraction-threshold-partition-v1.json"
VERIFICATION = DATA / "anthropic-claude-sonnet-5-pilot-verification-v1.json"
SIZES = DATA / "semantic-extraction-request-size-development-v1.json"
ELIGIBILITY = DATA / "stack-overflow-semantic-egress-eligibility-development-v1.json"
REFERENCE = DATA / "stack-overflow-semantic-annotations-development-operator-a-v1.json"
OLD_FULL_CONTEXT_BOUND_USD = "206.5452"
SCHEMA_RETRIES_PER_RECORD = 1

THRESHOLD_CHOICES = (
    "AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT",
    "REVISE_BEFORE_THE_PILOT_RUN",
    "REJECT_FOR_THE_PILOT",
)
REPEATABILITY_CHOICES = (
    "DEFER_TO_A_LATER_REPEATABILITY_RUN",
    "AUTHORISE_A_SEPARATELY_APPROVED_SECOND_RUN_LATER",
    "REJECT_FOR_THIS_FIRST_PILOT",
)
RETRY_CHOICES = ("RATIFY", "REVISE", "REJECT")
CEILING_CHOICES = ("ACCEPT", "REVISE", "REJECT")
RESULT_VOCABULARY = (
    "PILOT_WITHIN_PROPOSED_BOUND",
    "PILOT_OUTSIDE_PROPOSED_BOUND",
    "PILOT_INSUFFICIENT_SUPPORT",
)
EXTRACTABLE = ("REPORTED_FAILED_ATTEMPT", "NEGATIVE_EVALUATION_OF_NAMED_SOLUTION")


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: pathlib.Path) -> Any:
    return json.loads(path.read_text("utf-8"))


def item_id(entry: dict[str, Any]) -> str:
    return f"{entry['metric']}::{entry['label']}"


def reference_counts() -> dict[str, dict[str, int]]:
    approved = set(load(ELIGIBILITY)["approved_record_ids"])
    reference = load(REFERENCE)
    out = {}
    for label in EXTRACTABLE:
        counts = Counter(
            r["labels"][label]["state"]
            for r in reference["records"]
            if r["normalized_record_id"] in approved
        )
        out[label] = {s: counts.get(s, 0) for s in ("PRESENT", "ABSENT", "UNCERTAIN")}
    return out


def threshold_items(counts: dict[str, dict[str, int]], approved: int) -> list[dict[str, Any]]:
    rfa, neg = counts["REPORTED_FAILED_ATTEMPT"], counts["NEGATIVE_EVALUATION_OF_NAMED_SOLUTION"]
    facts: dict[str, dict[str, Any]] = {
        "false_present_rate_upper_95::NEGATIVE_EVALUATION_OF_NAMED_SOLUTION": {
            "why": "a false PRESENT writes a dissatisfaction nobody expressed into a counting dimension",
            "can_measure": "how many of the model's PRESENT calls on this label the one human did not mark PRESENT, and the Clopper-Pearson upper bound on that rate",
            "cannot_establish": "a certified false-PRESENT rate, which needs adjudicated gold and holdout",
            "current_support": f"reference PRESENT {neg['PRESENT']}, ABSENT {neg['ABSENT']}, UNCERTAIN {neg['UNCERTAIN']} over {approved} approved records; the bound needs at least 30 PRESENT predictions, and with 0 reference PRESENT every PRESENT prediction would count as a false PRESENT",
            "expected_result": "PILOT_INSUFFICIENT_SUPPORT is the likely outcome unless the model makes at least 30 PRESENT calls",
        },
        "false_present_rate_upper_95::REPORTED_FAILED_ATTEMPT": {
            "why": "a false PRESENT asserts a failure the asker did not report",
            "can_measure": "the false-PRESENT rate among the model's PRESENT calls against the one human's cells, with its upper bound",
            "cannot_establish": "a certified rate against adjudicated gold or on holdout",
            "current_support": f"reference PRESENT {rfa['PRESENT']}, ABSENT {rfa['ABSENT']}, UNCERTAIN {rfa['UNCERTAIN']} over {approved} approved records; the bound needs at least 15 PRESENT predictions",
            "expected_result": "any of the three pilot readings; depends on how many PRESENT calls the model makes",
        },
        "min_true_present_and_min_true_absent::each extractable label": {
            "why": "a classifier that always answers ABSENT, always PRESENT or always abstains must not pass",
            "can_measure": "whether the model finds at least one PRESENT and one ABSENT the human also marked, per label",
            "cannot_establish": "anything about labels the reference has no PRESENT for",
            "current_support": f"REPORTED_FAILED_ATTEMPT has {rfa['PRESENT']} PRESENT and {rfa['ABSENT']} ABSENT; NEGATIVE_EVALUATION_OF_NAMED_SOLUTION has {neg['PRESENT']} PRESENT, so its true-PRESENT half cannot be satisfied in this pilot",
            "expected_result": "PILOT_INSUFFICIENT_SUPPORT for NEGATIVE_EVALUATION_OF_NAMED_SOLUTION by construction; either reading for REPORTED_FAILED_ATTEMPT",
        },
        "mechanical_unsupported_assertions_accepted::all": {
            "why": "an accepted quote that is not in the surface would be a validator defect",
            "can_measure": "accepted findings whose quote is not the surface text at the computed offsets",
            "cannot_establish": "semantic support, which needs a human reading",
            "current_support": f"needs no reference; {approved} records would be attempted",
            "expected_result": "PILOT_WITHIN_PROPOSED_BOUND or PILOT_OUTSIDE_PROPOSED_BOUND; never insufficient",
        },
        "validator_acceptance_rate::all": {
            "why": "a refusal is a failure, never an abstention",
            "can_measure": "accepted extractions over records attempted",
            "cannot_establish": "that accepted extractions are correct",
            "current_support": f"needs no reference; {approved} records attempted against a minimum of 20",
            "expected_result": "PILOT_WITHIN_PROPOSED_BOUND or PILOT_OUTSIDE_PROPOSED_BOUND",
        },
        "unnecessary_abstention_rate_on_gold_decided::all": {
            "why": "abstention is benign but must not replace answering",
            "can_measure": "how often the model abstains on records the one human decided",
            "cannot_establish": "that the human's decided records are decidable for another reader",
            "current_support": f"records the human decided (not UNCERTAIN): REPORTED_FAILED_ATTEMPT {rfa['PRESENT'] + rfa['ABSENT']}, NEGATIVE_EVALUATION_OF_NAMED_SOLUTION {neg['PRESENT'] + neg['ABSENT']}; minimum 20",
            "expected_result": "PILOT_WITHIN_PROPOSED_BOUND or PILOT_OUTSIDE_PROPOSED_BOUND",
        },
        "run_to_run_label_flip_rate::each extractable label": {
            "why": "a result that changes on re-run cannot be audited",
            "can_measure": "nothing in one run: it compares repeated runs",
            "cannot_establish": "repeatability, from a single run",
            "current_support": "requires 3 pinned runs; the current packet and ceiling cover one run with at most one schema retry per record, and the budget is NOT doubled automatically",
            "expected_result": "PILOT_INSUFFICIENT_SUPPORT for a single run; see repeatability_disposition",
            "repeatability_choices": list(REPEATABILITY_CHOICES),
        },
        "composition_gate::each extractable label, each split": {
            "why": "a split without enough of both states cannot test anything",
            "can_measure": "whether the one human's cells hold at least 4 PRESENT and 4 ABSENT per label",
            "cannot_establish": "a gold composition, which needs adjudication",
            "current_support": f"REPORTED_FAILED_ATTEMPT {rfa['PRESENT']} PRESENT / {rfa['ABSENT']} ABSENT (met); NEGATIVE_EVALUATION_OF_NAMED_SOLUTION {neg['PRESENT']} PRESENT / {neg['ABSENT']} ABSENT (not met)",
            "expected_result": "REFERENCE_SET_INSUFFICIENT for NEGATIVE_EVALUATION_OF_NAMED_SOLUTION in this pilot",
        },
        "recall::each extractable label": {
            "why": "descriptive only; conservative misses are tolerated",
            "can_measure": "the share of the one human's PRESENT cells the model also marks PRESENT",
            "cannot_establish": "recall against gold; for a label with no reference PRESENT, anything at all",
            "current_support": f"REPORTED_FAILED_ATTEMPT {rfa['PRESENT']} reference PRESENT; NEGATIVE_EVALUATION_OF_NAMED_SOLUTION {neg['PRESENT']}, so positive-class recall is UNDEFINED there",
            "expected_result": "descriptive; UNDEFINED for NEGATIVE_EVALUATION_OF_NAMED_SOLUTION",
        },
        "cost_and_latency::all": {
            "why": "cost is bounded by the accepted ceiling; latency is recorded, never quality",
            "can_measure": "actual usage and elapsed time",
            "cannot_establish": "quality",
            "current_support": "needs no reference",
            "expected_result": "recorded; not a quality criterion",
        },
    }
    items = []
    for entry in load(PARTITION)["buckets"]["SINGLE_HUMAN_PILOT_VALID"]:
        key = item_id(entry)
        items.append(
            {
                "item_id": key,
                "metric": entry["metric"],
                "label": entry["label"],
                "proposed_value": entry["proposed"],
                "status": entry["status"],
                "reference_needed": entry["reference_needed"],
                **facts[key],
                "result_vocabulary": list(RESULT_VOCABULARY),
                "operator_choices": list(THRESHOLD_CHOICES),
            }
        )
    return items


def retry_section() -> dict[str, Any]:
    return {
        "proposed_reading": [
            "at most ONE retry per record",
            "retry ONLY when the forced-tool payload is missing, is not valid against the strict schema, or is structurally incomplete",
            "no retry on a deterministic validator refusal of a schema-valid payload",
            "no retry on a provider or network error",
            "no retry because a schema-valid semantic answer appears wrong",
            "no provider or model fallback",
        ],
        "inside_the_retry_class": [
            "the gateway raises SchemaValidationError: no tool_use payload, or one failing the strict schema",
            "a required key such as extraction_state or findings is missing",
            "a finding object lacks a required field",
        ],
        "outside_the_retry_class": [
            "a schema-valid payload whose quote is not in the surface (validator refusal)",
            "a payload whose extraction_state disagrees with its findings, refused by the validator",
            "HTTP 400/429/5xx, a timeout or a connection error",
            "stop_reason max_tokens (output limit reached) or a refusal",
            "a schema-valid answer the operator believes is semantically wrong",
        ],
        "implemented_as": "sros_semantic_extraction.may_retry: only AttemptOutcome.SCHEMA_FAILURE with 0 retries used is retried",
        "cost_consequence": "the retry worst case (every record retried once) is covered by the proposed ceiling",
        "operator_choices": list(RETRY_CHOICES),
    }


def ceiling_section() -> dict[str, Any]:
    verification = load(VERIFICATION)
    sizes = load(SIZES)
    pricing = verification["pricing"]
    limits = verification["limits"]
    prices = Prices(
        Decimal(pricing["input_usd_per_mtok"]),
        Decimal(pricing["output_usd_per_mtok"]),
        Decimal(pricing["us_only_inference_multiplier"]),
    )
    model = CostModel(
        prices=prices,
        context_window_tokens=limits["context_window_tokens"],
        max_output_tokens=limits["max_output_tokens_permitted_by_runner"],
        tool_use_system_prompt_tokens=limits["tool_use_system_prompt_tokens_tool_choice_tool"],
        schema_retries_per_record=SCHEMA_RETRIES_PER_RECORD,
    )
    run = model.run(
        (r["normalized_record_id"], r["request_body_utf8_bytes"]) for r in sizes["records"]
    )
    ceiling = proposed_hard_ceiling(run)
    return {
        "provider": verification["provider_id"],
        "model": verification["model"]["bound_by_packet"],
        "model_state": verification["model"]["documented_state"],
        "approved_record_count": sizes["record_count"],
        "EXPECTED_CALLS": run.expected_calls,
        "MAX_CALLS_WITH_RETRY": run.max_calls_with_retry,
        "planning_estimate_usd": money(run.planning_estimate_usd),
        "conservative_bound_usd": money(run.conservative_bound_usd),
        "retry_worst_case_usd": money(run.retry_worst_case_usd),
        "per_call_documented_maximum_usd": money(run.per_call_documented_maximum_usd),
        "proposed_hard_ceiling_usd": money(ceiling),
        "old_full_context_window_bound_usd": OLD_FULL_CONTEXT_BOUND_USD,
        "old_bound_reused": False,
        "pricing": {
            "input_usd_per_mtok": pricing["input_usd_per_mtok"],
            "output_usd_per_mtok": pricing["output_usd_per_mtok"],
            "multiplier_applied": pricing["us_only_inference_multiplier"],
            "source": "docs/data/anthropic-claude-sonnet-5-pilot-verification-v1.json",
            "source_sha256": sha(VERIFICATION),
            "retrieved_on": verification["retrieved_on"],
        },
        "token_estimation_methodology": {
            "cost_model": COST_MODEL_ID,
            "measured": f"exact UTF-8 bytes of each of the {sizes['record_count']} request bodies, built offline by the runner's own prompt, strict tool and body builder (docs/data/semantic-extraction-request-size-development-v1.json)",
            "no_local_tokenizer": limits["local_tokenizer"],
            "conservative_input_tokens_per_call": f"request body bytes + {limits['tool_use_system_prompt_tokens_tool_choice_tool']} documented tool-use system prompt tokens + {STRICT_PROMPT_ALLOWANCE_TOKENS} policy allowance for the undocumented strict prompt; counting a byte as a token over-counts English text and code, and two real strict requests in this repository reported about 0.40 tokens per character",
            "conservative_output_tokens_per_call": limits["max_output_tokens_permitted_by_runner"],
            "planning_input_tokens_per_call": f"ceil(body bytes x {PLANNING_TOKENS_PER_BODY_BYTE}) + {limits['tool_use_system_prompt_tokens_tool_choice_tool']}",
            "planning_output_tokens_per_call": PLANNING_OUTPUT_TOKENS_PER_CALL,
            "multiplier": "the US-only 1.1x is applied because inference_geo is not sent and the workspace default is not observable",
            "ceiling_rule": "retry worst case + one call at the documented maximum (full context window and the runner's output bound), rounded up to a whole dollar",
        },
        "enforcement": {
            "preflight": "the runner refuses before any transport if the accepted ceiling is below retry worst case + one documented-maximum call",
            "before_each_call": "including a retry: refused if spent + one documented-maximum call would exceed the accepted ceiling",
            "accumulation": "each HTTP 200 adds its reported usage at the verified prices and multiplier; any call without reported usage is charged at the documented maximum",
            "estimate_check": "a call whose reported input tokens exceed that record's conservative bound stops the run, fail-closed",
        },
        "operator_choices": list(CEILING_CHOICES),
        "per_record_conservative_input_tokens": run.per_record_conservative_input_tokens,
    }


def blank_decisions(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "$comment": "OPERATOR DECISIONS for the DEVELOPMENT pilot. Filled only by the operator. Every field is blank until the operator supplies it; no script, model or mission writes a decision here. REVISE carries a revised value and a reason, and a revision needs the package re-rendered before it can count.",
        "decisions_id": "semantic-extraction-operator-decisions-development",
        "version": "1.0.0",
        "decided_by": None,
        "decided_at": None,
        "A_pilot_thresholds": [
            {
                "item_id": item["item_id"],
                "operator_decision": None,
                "revised_value": None,
                "operator_note": None,
                **({"repeatability_disposition": None} if "repeatability_choices" in item else {}),
            }
            for item in items
        ],
        "B_retry": {"operator_decision": None, "revised_reading": None, "operator_note": None},
        "C_hard_ceiling": {
            "operator_decision": None,
            "accepted_hard_ceiling_usd": None,
            "revised_hard_ceiling_usd": None,
            "operator_note": None,
        },
    }


def decision_state(
    decisions: dict[str, Any], items: list[dict[str, Any]], package: dict[str, Any]
) -> dict[str, Any]:
    by_id = {d["item_id"]: d for d in decisions.get("A_pilot_thresholds", [])}
    recorded = [by_id.get(i["item_id"]) or {"item_id": i["item_id"]} for i in items]
    unmade = [d["item_id"] for d in recorded if d.get("operator_decision") is None]
    return {
        "decisions_file": "docs/data/semantic-extraction-operator-decisions-development-v1.json",
        "decisions_sha256": sha(DECISIONS),
        "decided_by": decisions.get("decided_by"),
        "decided_at": decisions.get("decided_at"),
        "thresholds_unmade": len(unmade),
        "thresholds": [
            {
                "item_id": d["item_id"],
                "operator_decision": d.get("operator_decision"),
                **(
                    {"repeatability_disposition": d.get("repeatability_disposition")}
                    if "repeatability_disposition" in d
                    else {}
                ),
            }
            for d in recorded
        ],
        "retry_decision": decisions["B_retry"]["operator_decision"],
        "ceiling_decision": decisions["C_hard_ceiling"]["operator_decision"],
        "accepted_hard_ceiling_usd": decisions["C_hard_ceiling"].get("accepted_hard_ceiling_usd"),
        "record_problems": decision_record_problems(package, decisions),
    }


def build() -> tuple[dict[str, Any], dict[str, Any] | None]:
    counts = reference_counts()
    approved = len(load(ELIGIBILITY)["approved_record_ids"])
    items = threshold_items(counts, approved)
    created = None
    if not DECISIONS.exists():
        created = blank_decisions(items)
        decisions = created
        DECISIONS.write_bytes(dump(created))
    else:
        decisions = load(DECISIONS)
    package = {
        "$comment": "FINAL OPERATOR DECISION PACKAGE (prepared in Mission 1.85.7). Facts behind the operator's three decisions, rendered from committed artifacts. The decisions live in the operator-owned decisions file; decision_state only mirrors it. Rendering decides nothing, and neither recording a decision nor merging authorises a provider call.",
        "package_id": "semantic-extraction-operator-decision-package-development",
        "version": "1.0.0",
        "mission": "1.85.7",
        "reference_strength": "SINGLE_HUMAN_REFERENCE",
        "result_scope": "DEVELOPMENT_PILOT",
        "result_label": "PILOT_NOT_CERTIFICATION",
        "inputs": {
            "threshold_partition_sha256": sha(PARTITION),
            "reference_sha256": sha(REFERENCE),
            "eligibility_sha256": sha(ELIGIBILITY),
            "request_sizes_sha256": sha(SIZES),
            "provider_verification_sha256": sha(VERIFICATION),
        },
        "reference_composition_on_approved_records": {"approved_records": approved, **counts},
        "composition_consequence": "NEGATIVE_EVALUATION_OF_NAMED_SOLUTION has no PRESENT cell in the single-human reference, so it cannot satisfy a minimum-PRESENT composition requirement and cannot provide meaningful positive-class recall in this pilot. That is not a model failure; PILOT_INSUFFICIENT_SUPPORT is a valid outcome, and no threshold is weakened to avoid it.",
        "A_pilot_thresholds": items,
        "B_retry": retry_section(),
        "C_hard_ceiling": ceiling_section(),
    }
    package["decision_state"] = decision_state(decisions, items, package)
    return package, created


def dump(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def page(package: dict[str, Any]) -> bytes:
    c = package["C_hard_ceiling"]
    state = package["decision_state"]
    recorded = {t["item_id"]: t for t in state["thresholds"]}

    def shown(value: Any) -> str:
        return f"`{value}`" if value is not None else "blank"

    if state["decided_by"]:
        who = f"Decisions recorded by `{state['decided_by']}` at `{state['decided_at']}`, in `semantic-extraction-operator-decisions-development-v1.json` (sha256 `{state['decisions_sha256']}`), which only the operator fills in. Recording them authorises no evaluation run."
    else:
        who = "No decision is recorded yet. The decisions live in `semantic-extraction-operator-decisions-development-v1.json`, which only the operator fills in."
    problems = (
        ["", "Problems in the recorded decisions: " + "; ".join(state["record_problems"]) + "."]
        if state["record_problems"]
        else []
    )
    lines = [
        "# Semantic extraction pilot: operator decision package (v1)",
        "",
        "> Generated by `infrastructure/scripts/render_semantic_extraction_decision_package.py` from committed artifacts. Do not edit by hand.",
        "",
        f"Prepared in Mission 1.85.7. {who}",
        *problems,
        "",
        f"Reference strength `{package['reference_strength']}`, result scope `{package['result_scope']}`, result label `{package['result_label']}`.",
        "",
        "## A. Pilot thresholds",
        "",
        "Each item is decided on its own: `AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT`, `REVISE_BEFORE_THE_PILOT_RUN` or `REJECT_FOR_THE_PILOT`. Results use `PILOT_WITHIN_PROPOSED_BOUND`, `PILOT_OUTSIDE_PROPOSED_BOUND` or `PILOT_INSUFFICIENT_SUPPORT`.",
        "",
        package["composition_consequence"],
        "",
        "| Item | Proposed | Current support | Decision |",
        "|---|---|---|---|",
    ]
    for item in package["A_pilot_thresholds"]:
        lines.append(
            f"| `{item['item_id']}` | `{json.dumps(item['proposed_value'])}` | {item['current_support']} | {shown(recorded[item['item_id']].get('operator_decision'))}"
            + (
                f", disposition {shown(recorded[item['item_id']]['repeatability_disposition'])}"
                if "repeatability_disposition" in recorded[item["item_id"]]
                else ""
            )
            + " |"
        )
    lines += [
        "",
        "The run-to-run flip rate also takes a repeatability disposition: defer to a later repeatability run, authorise a separately approved second run later, or reject it for this first pilot. The budget is not doubled automatically.",
        "",
        "## B. Retry reading",
        "",
        *[f"- {line}" for line in package["B_retry"]["proposed_reading"]],
        "",
        f"Decision (`RATIFY`, `REVISE` or `REJECT`): {shown(state['retry_decision'])}.",
        "",
        "## C. Hard cost ceiling",
        "",
        "| Fact | Value |",
        "|---|---|",
        f"| Provider / model | {c['provider']} / `{c['model']}` ({c['model_state']}) |",
        f"| Approved records | {c['approved_record_count']} |",
        f"| EXPECTED_CALLS | {c['EXPECTED_CALLS']} |",
        f"| MAX_CALLS_WITH_RETRY | {c['MAX_CALLS_WITH_RETRY']} |",
        f"| Planning estimate | ${c['planning_estimate_usd']} |",
        f"| Conservative bound (one pass) | ${c['conservative_bound_usd']} |",
        f"| Retry worst case | ${c['retry_worst_case_usd']} |",
        f"| One call at the documented maximum | ${c['per_call_documented_maximum_usd']} |",
        f"| **Proposed hard ceiling** | **${c['proposed_hard_ceiling_usd']}** |",
        f"| Old full-context bound (not reused) | ${c['old_full_context_window_bound_usd']} |",
        f"| Pricing | ${c['pricing']['input_usd_per_mtok']} / ${c['pricing']['output_usd_per_mtok']} per MTok, x{c['pricing']['multiplier_applied']}, retrieved {c['pricing']['retrieved_on']} |",
        "",
        f"Token methodology: {c['token_estimation_methodology']['conservative_input_tokens_per_call']}.",
        "",
        f"Enforcement: {c['enforcement']['preflight']}; {c['enforcement']['before_each_call']}.",
        "",
        f"Decision (`ACCEPT`, `REVISE` or `REJECT`): {shown(state['ceiling_decision'])}"
        + (
            f", accepted hard ceiling ${state['accepted_hard_ceiling_usd']}."
            if state["accepted_hard_ceiling_usd"]
            else "."
        ),
        "",
    ]
    return ("\n".join(lines)).encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check and not DECISIONS.exists():
        print(f"FAIL     {DECISIONS.name} is missing")
        return 1
    package, created = build()
    targets = {PACKAGE: dump(package), PAGE: page(package)}
    if args.write:
        for path, content in targets.items():
            path.write_bytes(content)
        print(
            f"wrote {PACKAGE.name} and {PAGE.name}"
            + (f"; created blank {DECISIONS.name}" if created else "")
        )
        return 0
    stale = [p.name for p, c in targets.items() if not p.exists() or p.read_bytes() != c]
    for name in stale:
        print(f"FAIL     {name} is stale")
    if not stale:
        print(f"ok       {PACKAGE.name} matches")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
