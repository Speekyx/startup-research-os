"""CI gate 96. Mission 1.84.21. The operator's client-timeout decision, and execution packet V8
superseded before it was approved or executed.

    uv run python infrastructure/scripts/render_second_opportunity_execution_timeout_decision.py --write
    uv run python infrastructure/scripts/render_second_opportunity_execution_timeout_decision.py --check

V8 kept the reviewed 60-second client timeout, while the provider documents that strict tool use may
compile a grammar on the first request for a schema, for an undocumented time, with a compilation
timeout of 180 seconds. The client could therefore give up while the provider was still allowed to be
compiling. The operator accepted everything else in V8 and set the client timeout of its successor to
240 seconds: an operator availability budget, not a provider guarantee, not a latency prediction, not
a statistical estimate and not a billing bound.

This gate re-derives:

* V8 as it stands: digest, bytes, no approval, no execution record, no response, its 60-second
  timeout, its cost figures and its request body, rebuilt through the V8 runner and never sent;
* the mismatch, from the first-party fragments CI gate 94 already holds, with no new request: a
  possibility, never a frequency, and never a claim that a request will take longer than 60 seconds;
* the decision, owned by the operator and derived from nothing, with what it reduces and what it does
  not establish;
* that the timeout enters neither the provider body nor the cost derivation, gate 94's record being
  unchanged and re-derived;
* V8's supersession, and a V8 runner that refuses V8 by name before its approval and any transport.

No provider, token-count or network request is made here.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import sys
import tempfile
from decimal import Decimal
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
sys.path.insert(0, str(SCRIPTS))

RECORD = DATA / "second-opportunity-execution-timeout-decision-v1.json"
RECORD_MD = DATA / "second-opportunity-execution-timeout-decision-v1.md"
SUPERSESSION = DATA / "second-opportunity-synthesis-execution-supersession-v8.json"
PACKET_V8 = DATA / "second-opportunity-synthesis-execution-packet-v8.json"
APPROVAL_V8 = DATA / "second-opportunity-synthesis-execution-approval-v8.json"
RECORD_V8 = DATA / "second-opportunity-synthesis-execution-record-v8.json"
RESPONSE_V8 = DATA / "second-opportunity-synthesis-response-v8.json"
GATE_94 = SCRIPTS / "render_second_opportunity_execution_cost_ceiling.py"
GATE_95 = SCRIPTS / "render_second_opportunity_execution_packet_v8.py"
RUNNER_V8 = SCRIPTS / "run_second_opportunity_execution_v8.py"

RECORD_VERSION = "second-opportunity-execution-timeout-decision-record@1.0.0"
SUPERSESSION_VERSION = "second-opportunity-execution-packet-supersession@1.0.0"
MISSION = "1.84.21"
RECORDED_BY = "mission-1.84.21"
RECORDED_ON = "2026-09-14"
READY = "CLIENT_TIMEOUT_ALIGNED_BY_OPERATOR_DECISION"

V8_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V8"
V8_SHA256 = "583946460c6cf68c1be5519916f92d268e36ed65924aeb24901731439586c399"
#: The bytes of packet V8 as Mission 1.84.20 committed them. Superseding V8 edits nothing in it.
V8_PACKET_FILE_SHA256 = "4ec6c6bf91fdd88ae9c374336b74880cc7c6a24386850cc2a1df297c1de549da"
V8_REQUEST_BODY_SHA256 = "58956019f78f414ee11392bee5e99eedda4eb1b4deb20d3f20219dfc60739842"
V8_REQUEST_BODY_CHARACTERS = 31326
#: Gate 94's record as Mission 1.84.20 committed it. A timeout decision moves nothing in it.
COST_CEILING_RECORD_SHA256 = "2184ff405cd8edd8766da4fc03bd64218c7b554da141d6e7589c5515c31a0d0b"
V7_SHA256 = "51023d0d2ed780db4c7d5018a289939e7c9c83061f8768051ef1cd7b8ae674e8"
V9_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V9"
SHAS = (
    "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92",
    "d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e",
    "c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2",
    "7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b",
    "da3e7d09d97c30cd02859eaee729b6bd164cd99812feac34572a0e1d93aa511a",
    "969128dd2453ab2a6907335d9386c9c3f3fac991db91c674b151c9db777aa8a9",
)
SUPERSEDED = "EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION"
CONSUMED = "EXECUTION_APPROVAL_ALREADY_CONSUMED"
V8_TIMEOUT = 60.0
V9_TIMEOUT = 240.0

#: The operator's decision that opened this mission, carried as data.
OPERATOR_DECISION = (
    "ACCEPT_ALL_V8_ARCHITECTURE_AND_GOVERNANCE_EXCEPT_THE_60_SECOND_CLIENT_TIMEOUT",
    "KEEP_OUTPUT_SCHEMA_V1_2_0",
    "KEEP_SEMANTIC_GATE_V1_4_0",
    "KEEP_PROMPT_V1_5_0",
    "KEEP_PROVIDER_STRICT_MODE_TRUE",
    "KEEP_STRICT_PROJECTION_V1_0_0",
    "KEEP_STRICT_CAPABILITY_PROFILE_V1_0_0",
    "KEEP_STRICT_PROJECTION_FREEZE_COMMIT_57154AFF",
    "KEEP_TED_REPRESENTATION_2528A56A",
    "KEEP_GENERATION_HEADROOM_4_OVER_5",
    "KEEP_SUMMARY_HARD_MAXIMUM_1500_AND_TARGET_1200",
    "KEEP_HARD_EXECUTION_COST_CEILING_3_608_PROVEN",
    "KEEP_PLANNING_COST_ESTIMATE_1_316316",
    "DO_NOT_APPROVE_V8",
    "SUPERSEDE_V8_BEFORE_EXECUTION",
    "CREATE_V9_WITH_ONLY_CLIENT_TIMEOUT_CHANGE",
    "REQUEST_TIMEOUT 60.0 -> 240.0 SECONDS",
    "240_SECONDS_IS_AN_OPERATOR_AVAILABILITY_BUDGET",
)

#: What the operator says about a FUTURE approval. It is not an approval, and it is recorded nowhere
#: as one: V9's packet carries the acceptance as false, and only V9's approval may set it.
OPERATOR_STATED_INTENTIONS = {
    "RESIDUAL_SEMANTIC_LIMITATION_INTENDED_FOR_V9_APPROVAL": "ACCEPT",
    "IS_AN_APPROVAL": False,
    "RECORDED_AS_ACCEPTED": False,
}

TIMEOUT_DECISION = {
    "REQUEST_TIMEOUT_V8_SECONDS": V8_TIMEOUT,
    "REQUEST_TIMEOUT_V9_SECONDS": V9_TIMEOUT,
    "DECISION_OWNER": "OPERATOR",
    "DECISION_TYPE": "EXECUTION_AVAILABILITY",
    "BASIS": "OPERATOR_AVAILABILITY_BUDGET",
    "MATHEMATICALLY_DERIVED": False,
    "STATISTICALLY_ESTIMATED": False,
    "PROVIDER_GUARANTEED": False,
    "LATENCY_PREDICTION": False,
    "BILLING_BOUND": False,
    "DERIVED_FROM_OBSERVED_ELAPSED_TIMES": False,
    "GUARANTEES_SUCCESSFUL_COMPLETION": False,
    "reasoning": (
        "a client-side budget beyond the documented 180-second provider grammar compilation "
        "timeout, with additional operational margin. It was chosen by the operator; it predicts no "
        "latency, rests on no measurement, and does not make the one attempt succeed"
    ),
    "RETRY_ADDED_TO_OFFSET_THE_RISK": False,
    "MAX_RETRIES_V9": 0,
    "TIMEOUT_MISMATCH_REDUCED": True,
    "TIMEOUT_RISK_ELIMINATED": False,
    "END_TO_END_LATENCY_BOUND": "NOT_ESTABLISHED",
    "GENERATION_RATE_DOCUMENTED": False,
    "OUTPUT_TOKENS_REACHABLE_WITHIN_TIMEOUT": "NOT_ESTABLISHED",
    "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9": False,
    "CLIENT_TIMEOUT_MECHANISM": (
        "the value travels unchanged from the request to urllib.request.urlopen(timeout=...), a "
        "socket timeout on the blocking operations of one non-streamed request. The gateway applies "
        "no ceiling of its own, and the deployment's LLM_REQUEST_TIMEOUT_SECONDS is not read on this "
        "path"
    ),
}


class ValidationError(RuntimeError):
    """The timeout decision, V8's supersession or the V8 guard disagrees with what the code derives."""


def _module(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _serialise(doc: dict[str, Any]) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(path: pathlib.Path) -> str:
    return _sha(path.read_text(encoding="utf-8"))


def gate_94() -> Any:
    return _module("gate_94_for_gate_96", GATE_94)


def gate_95() -> Any:
    return _module("gate_95_for_gate_96", GATE_95)


def cost_record() -> tuple[dict[str, Any], dict[str, Any]]:
    """Gate 94's validated cost record and V7's supersession. Its refusal is named as this gate's."""
    g94 = gate_94()
    try:
        return g94.validate()
    except g94.ValidationError as exc:
        raise ValidationError(f"gate 94 no longer validates: {exc}") from exc


def runner_v8() -> Any:
    return _module("runner_v8_for_gate_96", RUNNER_V8)


# ------------------------------------------------------------------------------ derivation


def v8_body() -> dict[str, Any]:
    """V8's request body, built through the V8 runner over the authenticated snapshot, never sent."""
    g95 = gate_95()
    try:
        _snap, parts, _ = g95.snapshot()
    except g95.ValidationError as exc:
        raise ValidationError(f"gate 95's snapshot no longer builds: {exc}") from exc
    return g95.runner().request_body(parts, _load(PACKET_V8))


def body_keys(node: object) -> list[str]:
    """Every key anywhere in a request body."""
    if isinstance(node, dict):
        return [str(k) for k in node] + [k for v in node.values() for k in body_keys(v)]
    if isinstance(node, list):
        return [k for v in node for k in body_keys(v)]
    return []


def v8_reconfirmation(v8: dict[str, Any], body: dict[str, Any]) -> dict[str, object]:
    wire = json.dumps(body)
    return {
        "EXECUTION_PACKET_ID": v8["EXECUTION_PACKET_ID"],
        "EXECUTION_PACKET_VERSION": v8["EXECUTION_PACKET_VERSION"],
        "EXECUTION_PACKET_SHA256_RECOMPUTED": gate_95().packet_digest(v8),
        "EXECUTION_PACKET_FILE_SHA256": file_sha(PACKET_V8),
        "approval_recorded": v8["OPERATOR_EXECUTION_APPROVAL_RECORDED"],
        "approval_file_exists": APPROVAL_V8.exists(),
        "execution_record_exists": RECORD_V8.exists(),
        "response_artifact_exists": RESPONSE_V8.exists(),
        "provider_requests": 0 if not RECORD_V8.exists() else "RECORDED",
        "REQUEST_TIMEOUT": v8["REQUEST_TIMEOUT"],
        "MAX_RETRIES": v8["MAX_RETRIES"],
        "HARD_EXECUTION_COST_CEILING": v8["HARD_EXECUTION_COST_CEILING"],
        "HARD_EXECUTION_COST_CEILING_PROVEN": v8["HARD_EXECUTION_COST_CEILING_PROVEN"],
        "PLANNING_COST_ESTIMATE": v8["PLANNING_COST_ESTIMATE"],
        "request_body_characters": len(wire),
        "request_body_sha256": _sha(wire),
        "provider_strict_mode": v8["PROVIDER_STRICT_MODE"],
        "timeout_in_the_provider_body": any("timeout" in k.lower() for k in body_keys(body)),
    }


def mismatch(v8: dict[str, Any], cost: dict[str, Any]) -> dict[str, object]:
    """The mismatch, from gate 94's first-party fragments and V8's own figures: a possibility."""
    compile_timeout = cost["PROVIDER_FACTS"]["PROVIDER_COMPILATION_TIMEOUT_SECONDS"]["value"]
    latency = cost["PROVIDER_FACTS"]["FIRST_REQUEST_GRAMMAR_COMPILATION_LATENCY"]["value"]
    page = next(r for r in cost["DOCUMENTATION_EVIDENCE"] if r["id"] == "D04")
    return {
        "STRICT_GRAMMAR_COMPILATION": "MAY_OCCUR_ON_THE_FIRST_REQUEST_FOR_A_SCHEMA",
        "STRICT_GRAMMAR_COMPILATION_LATENCY": latency,
        "PROVIDER_GRAMMAR_COMPILATION_TIMEOUT_SECONDS": compile_timeout,
        "CURRENT_CLIENT_REQUEST_TIMEOUT_SECONDS": v8["REQUEST_TIMEOUT"],
        "MAX_RETRIES": v8["MAX_RETRIES"],
        "CLIENT_TIMEOUT_IS_SHORTER_THAN_PROVIDER_COMPILATION_TIMEOUT": (
            Decimal(str(v8["REQUEST_TIMEOUT"])) < Decimal(str(compile_timeout))
        ),
        "CLAIMS_A_REQUEST_WILL_EXCEED_60_SECONDS": False,
        "ISSUE": "POSSIBILITY_NOT_FREQUENCY",
        "documentation": cost["DOCUMENTED_PROPOSITIONS"]["GRAMMAR_COMPILATION"],
        "documentation_page": {k: page[k] for k in ("id", "final_url", "retrieved_at", "sha256")},
        "documentation_source": (
            "CI gate 94's record, which quotes the fragments from bytes read on 2026-09-14; no page "
            "was requested again"
        ),
    }


def cost_equality(cost: dict[str, Any]) -> dict[str, object]:
    derivation = cost["HARD_CEILING_DERIVATION"]
    return {
        "COST_CEILING_RECORD_SHA256": text_sha(gate_94().RECORD),
        "HARD_EXECUTION_COST_CEILING": cost["COST_RECORD"]["HARD_EXECUTION_COST_CEILING"],
        "HARD_EXECUTION_COST_CEILING_PROVEN": cost["COST_RECORD"][
            "HARD_EXECUTION_COST_CEILING_PROVEN"
        ],
        "PLANNING_COST_ESTIMATE": cost["COST_RECORD"]["PLANNING_COST_ESTIMATE"],
        "TIMEOUT_ENTERS_THE_COST_DERIVATION": any(
            "TIMEOUT" in str(term) for term in derivation["rests_on_facts"]
        ),
        "TIMEOUT_CHANGES_BILLING": False,
        "TIMEOUT_RELATED_PROVIDER_FEE": (
            "NONE_PUBLISHED"
            if not any("TIMEOUT" in str(r["category"]) for r in cost["COST_CATEGORIES"])
            else "LISTED"
        ),
        "RE_DERIVED_BY_GATE_94": True,
    }


def build_record() -> dict[str, Any]:
    v8 = _load(PACKET_V8)
    cost, _ = cost_record()
    body = v8_body()
    return {
        "$comment": (
            "Mission 1.84.21. The operator's client-timeout decision for V8's successor, the "
            "mismatch it answers, and what it leaves unestablished. Re-derived by CI gate 96."
        ),
        "record_version": RECORD_VERSION,
        "mission": MISSION,
        "recorded_by": RECORDED_BY,
        "recorded_on": RECORDED_ON,
        "PRIMARY_OUTCOME": READY,
        "OPERATOR_DECISION": list(OPERATOR_DECISION),
        "OPERATOR_STATED_INTENTIONS": OPERATOR_STATED_INTENTIONS,
        "V8_RECONFIRMATION": v8_reconfirmation(v8, body),
        "TIMEOUT_MISMATCH": mismatch(v8, cost),
        "TIMEOUT_DECISION": {
            **TIMEOUT_DECISION,
            "CLIENT_TIMEOUT_EXCEEDS_PROVIDER_COMPILATION_TIMEOUT": Decimal(str(V9_TIMEOUT))
            > Decimal(str(cost["PROVIDER_FACTS"]["PROVIDER_COMPILATION_TIMEOUT_SECONDS"]["value"])),
        },
        "COST_EQUALITY": cost_equality(cost),
        "ACCOUNTING": {
            "MODEL_CALLS": 0,
            "PROVIDER_REQUESTS": 0,
            "MESSAGES_API_REQUESTS": 0,
            "TOKEN_COUNT_API_REQUESTS": 0,
            "TED_BYTES_SENT": 0,
            "CANONICAL_MUTATIONS": 0,
            "DOCUMENTATION_REQUESTS": 0,
        },
    }


def build_supersession(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "$comment": (
            "Mission 1.84.21. Execution packet V8 superseded before it was approved or executed. "
            "The packet is left exactly as Mission 1.84.20 froze it; the V8 runner reads this record "
            "and refuses the digest it names, by name, before its approval and any transport."
        ),
        "record_version": SUPERSESSION_VERSION,
        "recorded_by": RECORDED_BY,
        "recorded_on": RECORDED_ON,
        "SUPERSEDED_EXECUTION_PACKET_ID": V8_ID,
        "SUPERSEDED_EXECUTION_PACKET_VERSION": 8,
        "SUPERSEDED_EXECUTION_PACKET_SHA256": V8_SHA256,
        "SUPERSEDED_EXECUTION_PACKET_FILE_SHA256": V8_PACKET_FILE_SHA256,
        "STATUS": "SUPERSEDED_BEFORE_EXECUTION",
        "REASON": "CLIENT_TIMEOUT_SHORTER_THAN_PROVIDER_STRICT_COMPILATION_TIMEOUT",
        "V8_EXECUTED": False,
        "V8_APPROVED": False,
        "V8_APPROVAL_CONSUMED": False,
        "V8_PROVIDER_REQUESTS": 0,
        "V8_MODEL_CALLS": 0,
        "V8_PACKET_MODIFIED": False,
        "NOT_DESCRIBED_AS": ["FAILED", "CONSUMED", "REJECTED_BY_PROVIDER"],
        "REFUSAL_OUTCOME": SUPERSEDED,
        "REFUSAL_IS_NOT": CONSUMED,
        "GUARD": {
            "runner": "infrastructure/scripts/run_second_opportunity_execution_v8.py",
            "function": "refuse_if_superseded",
            "called_from": [
                "refuse_if_consumed, which execute calls before the approval is read and before any "
                "transport exists, and which verification and --execute call"
            ],
        },
        "TIMEOUT_DECISION_RECORD_VERSION": RECORD_VERSION,
        "TIMEOUT_DECISION_RECORD_SHA256": _sha(_serialise(record)),
        "SUCCESSOR_EXECUTION_PACKET_ID": V9_ID,
        "OPERATOR_DECISION": list(OPERATOR_DECISION),
        "note": (
            "No inference occurred under V8, so it did not fail, was not consumed and was not refused "
            "by the provider. Its 60-second client timeout was shorter than the provider's documented "
            "180-second grammar compilation timeout, and the operator did not approve it. V1 to V6 "
            "stay consumed, V7 stays superseded, and a successor needs an approval naming its own "
            "digest"
        ),
    }


# ------------------------------------------------------------------------------ checking


def _fixed(block: dict[str, Any], expected: dict[str, object], where: str) -> None:
    for key, value in expected.items():
        if block.get(key) != value:
            raise ValidationError(f"{where}.{key} is {block.get(key)!r}; it must be {value!r}")


def _check_decision(record: dict[str, Any]) -> None:
    decision = record["TIMEOUT_DECISION"]
    if decision.get("REQUEST_TIMEOUT_V9_SECONDS") != V9_TIMEOUT:
        raise ValidationError(
            f"TIMEOUT_POLICY_REQUIRES_ARCHITECTURE_DECISION: the operator decided {V9_TIMEOUT} "
            f"seconds, and the record says {decision.get('REQUEST_TIMEOUT_V9_SECONDS')!r}"
        )
    _fixed(
        decision,
        {
            "REQUEST_TIMEOUT_V8_SECONDS": V8_TIMEOUT,
            "DECISION_OWNER": "OPERATOR",
            "DECISION_TYPE": "EXECUTION_AVAILABILITY",
            "BASIS": "OPERATOR_AVAILABILITY_BUDGET",
            "MATHEMATICALLY_DERIVED": False,
            "STATISTICALLY_ESTIMATED": False,
            "PROVIDER_GUARANTEED": False,
            "LATENCY_PREDICTION": False,
            "BILLING_BOUND": False,
            "DERIVED_FROM_OBSERVED_ELAPSED_TIMES": False,
            "GUARANTEES_SUCCESSFUL_COMPLETION": False,
            "RETRY_ADDED_TO_OFFSET_THE_RISK": False,
            "MAX_RETRIES_V9": 0,
            "TIMEOUT_MISMATCH_REDUCED": True,
            "TIMEOUT_RISK_ELIMINATED": False,
            "END_TO_END_LATENCY_BOUND": "NOT_ESTABLISHED",
            "OUTPUT_TOKENS_REACHABLE_WITHIN_TIMEOUT": "NOT_ESTABLISHED",
            "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9": False,
            "CLIENT_TIMEOUT_EXCEEDS_PROVIDER_COMPILATION_TIMEOUT": True,
        },
        "TIMEOUT_DECISION",
    )
    _fixed(
        record["OPERATOR_STATED_INTENTIONS"],
        {"IS_AN_APPROVAL": False, "RECORDED_AS_ACCEPTED": False},
        "OPERATOR_STATED_INTENTIONS",
    )


def _check_mismatch(record: dict[str, Any], cost: dict[str, Any]) -> None:
    block = record["TIMEOUT_MISMATCH"]
    _fixed(
        block,
        {
            "STRICT_GRAMMAR_COMPILATION": "MAY_OCCUR_ON_THE_FIRST_REQUEST_FOR_A_SCHEMA",
            "STRICT_GRAMMAR_COMPILATION_LATENCY": "NOT_ESTABLISHED",
            "PROVIDER_GRAMMAR_COMPILATION_TIMEOUT_SECONDS": cost["PROVIDER_FACTS"][
                "PROVIDER_COMPILATION_TIMEOUT_SECONDS"
            ]["value"],
            "CURRENT_CLIENT_REQUEST_TIMEOUT_SECONDS": V8_TIMEOUT,
            "MAX_RETRIES": 0,
            "CLIENT_TIMEOUT_IS_SHORTER_THAN_PROVIDER_COMPILATION_TIMEOUT": True,
            "CLAIMS_A_REQUEST_WILL_EXCEED_60_SECONDS": False,
            "ISSUE": "POSSIBILITY_NOT_FREQUENCY",
            "documentation": cost["DOCUMENTED_PROPOSITIONS"]["GRAMMAR_COMPILATION"],
        },
        "TIMEOUT_MISMATCH",
    )
    if block["PROVIDER_GRAMMAR_COMPILATION_TIMEOUT_SECONDS"] != 180:
        raise ValidationError(
            "the provider's compilation timeout is not the documented 180 seconds"
        )
    if not any("180 seconds" in str(f["verbatim"]) for f in block["documentation"]):
        raise ValidationError("the 180-second compilation timeout rests on no quoted fragment")


def _check_cost(record: dict[str, Any]) -> None:
    _fixed(
        record["COST_EQUALITY"],
        {
            "COST_CEILING_RECORD_SHA256": COST_CEILING_RECORD_SHA256,
            "HARD_EXECUTION_COST_CEILING": "3.608",
            "HARD_EXECUTION_COST_CEILING_PROVEN": True,
            "PLANNING_COST_ESTIMATE": "1.316316",
            "TIMEOUT_ENTERS_THE_COST_DERIVATION": False,
            "TIMEOUT_CHANGES_BILLING": False,
            "TIMEOUT_RELATED_PROVIDER_FEE": "NONE_PUBLISHED",
            "RE_DERIVED_BY_GATE_94": True,
        },
        "COST_EQUALITY",
    )


def _check_v8(record: dict[str, Any]) -> None:
    _fixed(
        record["V8_RECONFIRMATION"],
        {
            "EXECUTION_PACKET_ID": V8_ID,
            "EXECUTION_PACKET_VERSION": 8,
            "EXECUTION_PACKET_SHA256_RECOMPUTED": V8_SHA256,
            "EXECUTION_PACKET_FILE_SHA256": V8_PACKET_FILE_SHA256,
            "approval_recorded": False,
            "approval_file_exists": False,
            "execution_record_exists": False,
            "response_artifact_exists": False,
            "provider_requests": 0,
            "REQUEST_TIMEOUT": V8_TIMEOUT,
            "MAX_RETRIES": 0,
            "HARD_EXECUTION_COST_CEILING": "3.608",
            "HARD_EXECUTION_COST_CEILING_PROVEN": True,
            "PLANNING_COST_ESTIMATE": "1.316316",
            "request_body_characters": V8_REQUEST_BODY_CHARACTERS,
            "request_body_sha256": V8_REQUEST_BODY_SHA256,
            "provider_strict_mode": True,
            "timeout_in_the_provider_body": False,
        },
        "V8_RECONFIRMATION",
    )


def _check_live_v8() -> None:
    """V8 is on disk as Mission 1.84.20 left it: unapproved, unexecuted, its bytes unchanged."""
    if file_sha(PACKET_V8) != V8_PACKET_FILE_SHA256:
        raise ValidationError("packet V8 was edited; superseding it changes nothing in it")
    if APPROVAL_V8.exists():
        raise ValidationError(
            "V8_APPROVAL_FABRICATED: an approval of V8 exists, and a superseded packet can never be "
            "approved"
        )
    for path in (RECORD_V8, RESPONSE_V8):
        if path.exists():
            raise ValidationError(f"V8_EXECUTED: {path.name} exists, and V8 was never executed")


def _check_supersession(doc: dict[str, Any], record: dict[str, Any]) -> None:
    _fixed(
        doc,
        {
            "SUPERSEDED_EXECUTION_PACKET_ID": V8_ID,
            "SUPERSEDED_EXECUTION_PACKET_VERSION": 8,
            "SUPERSEDED_EXECUTION_PACKET_SHA256": V8_SHA256,
            "SUPERSEDED_EXECUTION_PACKET_FILE_SHA256": V8_PACKET_FILE_SHA256,
            "STATUS": "SUPERSEDED_BEFORE_EXECUTION",
            "REASON": "CLIENT_TIMEOUT_SHORTER_THAN_PROVIDER_STRICT_COMPILATION_TIMEOUT",
            "V8_EXECUTED": False,
            "V8_APPROVED": False,
            "V8_APPROVAL_CONSUMED": False,
            "V8_PROVIDER_REQUESTS": 0,
            "V8_MODEL_CALLS": 0,
            "V8_PACKET_MODIFIED": False,
            "NOT_DESCRIBED_AS": ["FAILED", "CONSUMED", "REJECTED_BY_PROVIDER"],
            "REFUSAL_OUTCOME": SUPERSEDED,
            "REFUSAL_IS_NOT": CONSUMED,
            "TIMEOUT_DECISION_RECORD_SHA256": _sha(_serialise(record)),
        },
        "V8_SUPERSESSION_MISRECORDED: supersession",
    )


def _check_v8_guard() -> None:
    """The V8 runner refuses V8 by name before its approval and any transport; V1 to V6 as spent, V7
    as superseded, and nothing else."""
    module = runner_v8()
    for index, digest in enumerate(SHAS):
        try:
            module.refuse_if_consumed(digest)
        except module.RefusedError as exc:
            if exc.code != CONSUMED:
                raise ValidationError(f"the V8 runner refuses V{index + 1} as {exc.code}") from exc
        else:
            raise ValidationError(f"the V8 runner would execute V{index + 1}'s spent digest")
    for label, digest in (("V7", V7_SHA256), ("V8", V8_SHA256)):
        try:
            module.refuse_if_consumed(digest)
        except module.RefusedError as exc:
            if exc.code != SUPERSEDED:
                raise ValidationError(
                    f"{label} is refused as {exc.code}; it was superseded, and it never had an "
                    "approval to spend"
                ) from exc
        else:
            raise ValidationError(
                f"{label}_STILL_EXECUTABLE: the V8 runner's guard lets it through"
            )
    try:
        module.refuse_if_consumed("0" * 64)
    except module.RefusedError as exc:
        raise ValidationError("the V8 runner's guard refuses an unseen digest") from exc

    class _Tripwire:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("a transport was constructed")

    with tempfile.TemporaryDirectory() as tmp:
        forged = pathlib.Path(tmp) / APPROVAL_V8.name
        forged.write_text(
            json.dumps(
                {
                    "EXECUTION_PACKET_ID": V8_ID,
                    "EXECUTION_PACKET_VERSION": 8,
                    "EXECUTION_PACKET_SHA256": V8_SHA256,
                    "decision": "APPROVE_EXACTLY_ONE_EXECUTION",
                    "approved_by": "gate 96",
                    "operator_statement": "forged in a temporary directory, never beside the packet",
                    "RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V8": True,
                    "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8": True,
                }
            ),
            encoding="utf-8",
        )
        for approval in (pathlib.Path(tmp) / "absent.json", forged):
            module.APPROVAL_FILE = approval
            try:
                module.execute(
                    {"packet_file": {"EXECUTION_PACKET_SHA256": V8_SHA256}, "parts": None},
                    transport=_Tripwire,
                )
            except module.RefusedError as exc:
                if exc.code != SUPERSEDED:
                    raise ValidationError(
                        f"V8_STILL_EXECUTABLE: execute() refuses V8 as {exc.code}, not as "
                        "superseded before its approval is read"
                    ) from exc
            else:
                raise ValidationError("V8_STILL_EXECUTABLE: execute() accepted V8")


def _check_accounting(record: dict[str, Any]) -> None:
    for key, value in record["ACCOUNTING"].items():
        if value != 0:
            raise ValidationError(f"{key} is {value}, and preparing this record makes none")


def check_record(record: dict[str, Any], cost: dict[str, Any]) -> None:
    _check_decision(record)
    _check_mismatch(record, cost)
    _check_cost(record)
    _check_v8(record)
    _check_accounting(record)


def validate() -> tuple[dict[str, Any], dict[str, Any]]:
    cost, _ = cost_record()
    expected = json.loads(json.dumps(build_record()))
    check_record(expected, cost)
    for path in (RECORD, SUPERSESSION):
        if not path.exists():
            raise ValidationError(
                f"{path.name} does not exist"
                + ("; V8_SUPERSESSION_OMITTED" if path == SUPERSESSION else "")
            )
    committed = _load(RECORD)
    check_record(committed, cost)
    for key in sorted(set(expected) | set(committed)):
        if committed.get(key) != expected.get(key):
            raise ValidationError(f"{RECORD.name} {key} is not what the code derives")
    supersession = _load(SUPERSESSION)
    _check_supersession(supersession, committed)
    derived = json.loads(json.dumps(build_supersession(committed)))
    for key in sorted(set(derived) | set(supersession)):
        if supersession.get(key) != derived.get(key):
            raise ValidationError(f"{SUPERSESSION.name} {key} is not what the code derives")
    _check_live_v8()
    _check_v8_guard()
    return committed, supersession


# ------------------------------------------------------------------------------ rendering


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def _flag(value: object) -> str:
    return str(value).lower()


def render(record: dict[str, Any], supersession: dict[str, Any]) -> str:
    decision = record["TIMEOUT_DECISION"]
    gap = record["TIMEOUT_MISMATCH"]
    v8 = record["V8_RECONFIRMATION"]
    cost = record["COST_EQUALITY"]
    lines = [
        "# Second Opportunity: client-timeout decision and V8's supersession",
        "",
        "Generated by `infrastructure/scripts/render_second_opportunity_execution_timeout_decision.py`"
        " (CI gate 96) from `second-opportunity-execution-timeout-decision-v1.json` and "
        "`second-opportunity-synthesis-execution-supersession-v8.json`. Do not edit by hand.",
        "",
        f"**{record['PRIMARY_OUTCOME']}.**",
        "",
        "## The mismatch: a possibility, not a frequency",
        "",
        *_code(
            [
                f"strict grammar compilation          {gap['STRICT_GRAMMAR_COMPILATION']}",
                f"its latency                         {gap['STRICT_GRAMMAR_COMPILATION_LATENCY']}",
                "provider compilation timeout        "
                f"{gap['PROVIDER_GRAMMAR_COMPILATION_TIMEOUT_SECONDS']} s",
                f"V8's client timeout                 {gap['CURRENT_CLIENT_REQUEST_TIMEOUT_SECONDS']} s",
                f"retries                             {gap['MAX_RETRIES']}",
                "client shorter than compilation     "
                f"{_flag(gap['CLIENT_TIMEOUT_IS_SHORTER_THAN_PROVIDER_COMPILATION_TIMEOUT'])}",
                "a request will take longer than 60  "
                f"not claimed ({_flag(gap['CLAIMS_A_REQUEST_WILL_EXCEED_60_SECONDS'])})",
            ]
        ),
        "Quoted from the first-party structured-outputs page CI gate 94 holds:",
        "",
        *[f"- line {f['line']}: {f['verbatim']}" for f in gap["documentation"]],
        "",
        "## The operator's decision",
        "",
        *_code(
            [
                f"REQUEST_TIMEOUT                     {decision['REQUEST_TIMEOUT_V8_SECONDS']} s -> "
                f"{decision['REQUEST_TIMEOUT_V9_SECONDS']} s",
                f"DECISION_OWNER                      {decision['DECISION_OWNER']}",
                f"DECISION_TYPE                       {decision['DECISION_TYPE']}",
                f"BASIS                               {decision['BASIS']}",
                f"MATHEMATICALLY_DERIVED              {_flag(decision['MATHEMATICALLY_DERIVED'])}",
                f"STATISTICALLY_ESTIMATED             {_flag(decision['STATISTICALLY_ESTIMATED'])}",
                f"PROVIDER_GUARANTEED                 {_flag(decision['PROVIDER_GUARANTEED'])}",
                f"GUARANTEES_SUCCESSFUL_COMPLETION    "
                f"{_flag(decision['GUARANTEES_SUCCESSFUL_COMPLETION'])}",
                f"TIMEOUT_MISMATCH_REDUCED            {_flag(decision['TIMEOUT_MISMATCH_REDUCED'])}",
                f"TIMEOUT_RISK_ELIMINATED             {_flag(decision['TIMEOUT_RISK_ELIMINATED'])}",
                f"END_TO_END_LATENCY_BOUND            {decision['END_TO_END_LATENCY_BOUND']}",
                f"MAX_RETRIES_V9                      {decision['MAX_RETRIES_V9']}",
                "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9 "
                f"{_flag(decision['STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9'])}",
            ]
        ),
        f"{decision['reasoning'][:1].upper()}{decision['reasoning'][1:]}. "
        f"{decision['CLIENT_TIMEOUT_MECHANISM'][:1].upper()}"
        f"{decision['CLIENT_TIMEOUT_MECHANISM'][1:]}.",
        "",
        "## Cost, unchanged",
        "",
        *_code(
            [
                f"hard execution cost ceiling         {cost['HARD_EXECUTION_COST_CEILING']} (proven "
                f"{_flag(cost['HARD_EXECUTION_COST_CEILING_PROVEN'])})",
                f"planning cost estimate              {cost['PLANNING_COST_ESTIMATE']}",
                "timeout in the cost derivation      "
                f"{_flag(cost['TIMEOUT_ENTERS_THE_COST_DERIVATION'])}",
                f"timeout changes billing             {_flag(cost['TIMEOUT_CHANGES_BILLING'])}",
                f"timeout-related provider fee        {cost['TIMEOUT_RELATED_PROVIDER_FEE']}",
            ]
        ),
        "## V8, reconfirmed and superseded",
        "",
        *_code(
            [
                f"packet                              {v8['EXECUTION_PACKET_ID']} v"
                f"{v8['EXECUTION_PACKET_VERSION']}",
                f"sha256                              {v8['EXECUTION_PACKET_SHA256_RECOMPUTED']}",
                f"approval / record / response        {_flag(v8['approval_file_exists'])} / "
                f"{_flag(v8['execution_record_exists'])} / {_flag(v8['response_artifact_exists'])}",
                f"request body                        {v8['request_body_characters']} characters, "
                f"{v8['request_body_sha256']}",
                f"timeout in the provider body        {_flag(v8['timeout_in_the_provider_body'])}",
                "",
                f"status                              {supersession['STATUS']}",
                f"reason                              {supersession['REASON']}",
                f"executed / approved / consumed      {_flag(supersession['V8_EXECUTED'])} / "
                f"{_flag(supersession['V8_APPROVED'])} / "
                f"{_flag(supersession['V8_APPROVAL_CONSUMED'])}",
                f"refused as                          {supersession['REFUSAL_OUTCOME']}",
            ]
        ),
        f"{supersession['note']}.",
        "",
        "## Accounting",
        "",
        *_code([f"{key:28s} {value}" for key, value in record["ACCOUNTING"].items()]),
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        record = json.loads(json.dumps(build_record()))
        RECORD.write_bytes(_serialise(record).encode("utf-8"))
        SUPERSESSION.write_bytes(_serialise(build_supersession(record)).encode("utf-8"))
    try:
        record, supersession = validate()
    except ValidationError as exc:
        print(f"FAIL     {exc}")
        return 1
    text = render(record, supersession)
    if args.write:
        RECORD_MD.write_bytes(text.encode("utf-8"))
        print(f"wrote    {RECORD.name}, {SUPERSESSION.name}, {RECORD_MD.name}")
    if not RECORD_MD.exists() or RECORD_MD.read_text(encoding="utf-8") != text:
        print(f"FAIL     {RECORD_MD.name} is not the rendering of its records")
        return 1
    print(
        "ok       client timeout 240.0 s decided by the operator; the mismatch reduced, latency "
        "unbounded; V8 superseded before execution and refused by name"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
