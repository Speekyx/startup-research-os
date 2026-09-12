"""Render and validate the Claude subscription route feasibility record (Mission 1.84.1).

A route that shares a vendor with an approved one is the easiest kind of permission to acquire by
accident. The gate refuses:

    A ROUTE INHERITING A POSTURE. The subscription route is its own provider id, its posture is
    not APPROVED, and the API route's assessment still excludes consumer products by name. A
    record claiming the existing posture covers the subscription route is refused.

    A PROVIDER APPROVAL NOBODY EARNED. The subscription posture must rest on retrieved
    first-party evidence with dates, exactly as every other posture does, and the set of APPROVED
    providers must not have grown.

    A BILLING CLAIM WITH NO BASIS. Subscription usage is recorded as limited and not free, no
    dollar saving is claimed, and no quota percentage is invented.

    A CHANGED RESEARCH PAYLOAD. The representation digest, the prompt digest, the subject, the
    output schema and the output gate are the frozen ones, and V1 is byte-identical with its
    approval flag still false.

    A V2 PRODUCED ANYWAY. A record may only claim V2 exists when every one of section 20's nine
    conditions is met, and a failed condition must be named.

    A SECRET. No token, key, cookie or credential value appears in the record, and the counters
    that say none was read stay zero.

    AN EXECUTION. Model calls, transmitted TED bytes and remote test calls are all zero.

    uv run python infrastructure/scripts/render_claude_subscription_route_feasibility.py
    uv run python infrastructure/scripts/render_claude_subscription_route_feasibility.py --check

Deterministic from repository files, so it is safe in CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "docs" / "data"

RECORD = DATA / "claude-subscription-route-feasibility-v1.json"
RECORD_MD = DATA / "claude-subscription-route-feasibility-v1.md"
REGISTER = DATA / "model-provider-policy-v1.json"
PACKET_V1 = DATA / "second-opportunity-synthesis-execution-packet-v1.json"
DECISION_PACKET = DATA / "ted-selected-candidate-egress-decision-packet-v1.json"

SUBSCRIPTION_PROVIDER_ID = "anthropic-claude-subscription"
API_PROVIDER_ID = "anthropic"

#: The digest V1 was frozen at in Mission 1.84. Pinned, because a route experiment that moved it
#: would have changed the thing it was supposed to leave alone.
V1_SHA256 = "570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92"
REPRESENTATION_SHA256 = "2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72"
PROMPT_SHA256 = "af5289494416139d302eed704c12b9c53ab2547dca336e2ca4a834ec936c5080"

#: Section 2, checked here rather than left to Mission 1.84's gate. Swapping V1's provider or
#: model moves its digest, so that gate would catch it -- and a gate that relies on a sibling to
#: enforce its OWN rule stops working the moment the sibling is skipped. The probe found both
#: escapes, which is what a probe is for.
V1_ROUTE = {
    "PROVIDER_ID": "anthropic",
    "PROVIDER_POSTURE": "APPROVED",
    "MODEL_ID": "claude-sonnet-5",
    "MODEL_TIER": "STRONG_MODEL",
}

#: Section 25. What a feasibility mission spends.
ZERO_ACCOUNTING = (
    "REMOTE_TEST_CALLS",
    "TED_BYTES_SENT",
    "OPPORTUNITY_MODEL_CALLS",
    "ALL_REMOTE_MODEL_CALLS",
    "canonical_research_mutation",
    "opportunities_created",
    "credential_values_exposed",
)

#: Section 19. Shapes a credential takes when it leaks into a record by accident.
SECRET_PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"\bey[JI][A-Za-z0-9_\-]{20,}\."),
    re.compile(r"[A-Za-z0-9_\-]{0,8}oauth[A-Za-z0-9_\-]*\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}"),
)

#: Section 26. Exactly one primary outcome, from the list the brief fixes.
ACCEPTABLE_OUTCOMES = (
    "CLAUDE_MAX_SUBSCRIPTION_EXECUTION_PACKET_READY",
    "CLAUDE_MAX_ROUTE_REQUIRES_PROVIDER_GOVERNANCE_REVIEW",
    "CLAUDE_MAX_ROUTE_REQUIRES_OPERATOR_AUTHORIZED_TEST_CALL",
    "CLAUDE_MAX_ROUTE_NOT_SUPPORTED_FOR_SROS_EXECUTION",
    "CLAUDE_MAX_ROUTE_BILLING_AMBIGUOUS",
    "CLAUDE_MAX_ROUTE_MODEL_SELECTION_REQUIRES_OPERATOR_DECISION",
)


class ValidationError(RuntimeError):
    """The record disagrees with the register, with the frozen packet, or with itself."""


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def approved_providers(register: dict) -> list[str]:
    return sorted(
        str(entry["provider_id"])
        for entry in register["providers"]
        if str(entry.get("posture")) == "APPROVED"
    )


def _entry(register: dict, provider_id: str) -> dict:
    for entry in register["providers"]:
        if entry["provider_id"] == provider_id:
            return entry
    raise ValidationError(f"the register has no provider {provider_id!r}")


def _check_no_secret(record: dict) -> None:
    text = json.dumps(record, ensure_ascii=False)
    for pattern in SECRET_PATTERNS:
        found = pattern.search(text)
        if found:
            raise ValidationError(
                f"§19: something shaped like a credential is in the record, matching {pattern.pattern!r}"
            )
    tooling = record["LOCAL_TOOLING"]
    for key in (
        "credential_values_read",
        "credential_values_printed",
        "credential_values_persisted",
    ):
        if tooling[key] != 0:
            raise ValidationError(f"{key} is {tooling[key]}")
    if record["ENVIRONMENT_COLLISION"]["value_read"]:
        raise ValidationError("§6: the API key's value was read; only its presence may be")


def _check_the_route_did_not_inherit(record: dict, register: dict) -> None:
    """§10. No inheritance merely because both routes are Anthropic."""
    blocker = record["BLOCKER_3_PROVIDER_GOVERNANCE"]
    if blocker["CAN_EXISTING_ANTHROPIC_PROVIDER_POSTURE_COVER_SUBSCRIPTION_ROUTE"]:
        raise ValidationError(
            "the record claims the API route's posture covers the subscription route. It does "
            "not, and the register's own entry says so"
        )
    api = _entry(register, API_PROVIDER_ID)
    scope = api["route_assessed"]
    for word in ("Free", "Pro", "Max"):
        if word not in scope:
            raise ValidationError(
                f"the API route's assessment no longer excludes {word} by name, so a consumer "
                "route could read as covered"
            )
    if "not assessed here" not in scope:
        raise ValidationError("the API route's assessment no longer says what it does not cover")
    if api["posture"] != "APPROVED":
        raise ValidationError("the API route's posture moved, which this mission may not do")

    subscription = _entry(register, SUBSCRIPTION_PROVIDER_ID)
    if subscription["provider_id"] == API_PROVIDER_ID:
        raise ValidationError("the subscription route reuses the API route's provider id")
    if subscription["posture"] == "APPROVED":
        raise ValidationError(
            "§24: a provider approval was manufactured. The subscription route's own terms make "
            "training an account setting rather than a commitment"
        )
    if subscription["posture"] not in {"NOT_APPROVED", "NOT_ASSESSED"}:
        raise ValidationError(f"posture {subscription['posture']!r} is not a refusing state")
    if not subscription.get("evidence"):
        raise ValidationError(
            "a posture with no retrieved first-party evidence, which every other posture carries"
        )
    for item in subscription["evidence"]:
        for key in ("document_url", "summarized_finding", "retrieved_at"):
            if not str(item.get(key) or "").strip():
                raise ValidationError(f"an evidence row missing {key}")
        if not str(item["document_url"]).startswith("https://"):
            raise ValidationError("an evidence row that is not a retrievable first-party address")

    if approved_providers(register) != [API_PROVIDER_ID]:
        raise ValidationError(
            f"the approved provider set grew to {approved_providers(register)}. A feasibility "
            "mission may record a refusal and may not widen an approval"
        )
    if blocker["PROVIDER_GOVERNANCE_STATE"] != subscription["posture"]:
        raise ValidationError("the record and the register disagree about the posture")


def _check_the_required_property(record: dict, decision: dict) -> None:
    """§11. TED's own condition names the property, and it is quoted rather than paraphrased."""
    blocker = record["BLOCKER_3_PROVIDER_GOVERNANCE"]
    quoted = blocker["required_property"]
    condition = next(
        (c for c in decision["CONDITIONS"] if c.startswith("PROVIDER-BOUND")),
        None,
    )
    if condition is None:
        raise ValidationError("the frozen decision packet no longer carries a provider condition")
    fragment = "its own terms commit"
    if fragment not in quoted or fragment not in condition:
        raise ValidationError(
            "the record does not quote the condition's own load-bearing phrase, so a reader "
            "cannot see that a setting is not a term"
        )


def _check_the_blockers(record: dict) -> None:
    """§16 and §20. Two of the three are properties of the surface, not of an account."""
    prompt = record["BLOCKER_1_PROMPT_IDENTITY"]
    if prompt["FROZEN_PROMPT_SHA256"] != PROMPT_SHA256:
        raise ValidationError("the record names a prompt digest that is not the frozen one")
    if prompt["can_the_frozen_bytes_be_transmitted"]:
        raise ValidationError(
            "the record claims an agent harness can transmit the frozen prompt bytes. §16 makes "
            "that a STOP rather than a detail"
        )
    if prompt["operator_decision_can_clear_this"]:
        raise ValidationError("a surface property recorded as an operator decision")

    calls = record["BLOCKER_2_EXACTLY_ONE_CALL"]
    if calls["FROZEN_MAX_MODEL_CALLS"] != 1:
        raise ValidationError("the frozen call limit moved")
    if calls["can_exactly_one_call_be_enforced"]:
        raise ValidationError(
            "the record claims an agent loop can be held to one model request; §20 condition 8 "
            "asks whether it can be ENFORCED"
        )
    if calls["installed_cli_flags_that_would_bound_it"]:
        raise ValidationError(
            "a flag is claimed to bound the call count; then the blocker is not a blocker and the "
            "record must say so"
        )
    if calls["operator_decision_can_clear_this"]:
        raise ValidationError("a surface property recorded as an operator decision")


def _check_the_billing(record: dict) -> None:
    """§4 and §14. Neither route is free, and no saving is invented."""
    billing = record["BILLING"]
    if billing["subscription_is_free"] or billing["subscription_is_unlimited"]:
        raise ValidationError("§4: a subscription recorded as free or unlimited")
    if not billing["SUBSCRIPTION_USAGE_LIMITED"]:
        raise ValidationError("§14: subscription usage recorded as unlimited")
    if not billing["no_dollar_saving_is_claimed"]:
        raise ValidationError("§14: a dollar saving was claimed")
    if billing["quota_percentage_invented"]:
        raise ValidationError("§15: a quota percentage was invented")
    if not billing["V1_API_PAYG"]:
        raise ValidationError(
            "§28: PAYG marked false for V1 without evidence. V1 is the API route and is metered"
        )
    if not str(billing["evidence"]).strip():
        raise ValidationError("a billing claim with no stated basis")

    tier = record["premise_correction"]
    if (
        tier["MAX_TIER"] in {"MAX_5X", "MAX_20X"}
        and not str(tier.get("LOCALLY_HELD_SUBSCRIPTION_TYPE") or "").strip()
    ):
        raise ValidationError("a Max tier asserted with nothing establishing it")


def _check_the_payload_is_untouched(record: dict, packet: dict) -> None:
    """§2 and §16. The route experiment changed no research semantics and no frozen packet."""
    semantics = record["RESEARCH_SEMANTICS_UNCHANGED"]
    if semantics["REPRESENTATION_SHA256"] != REPRESENTATION_SHA256:
        raise ValidationError("the approved representation digest moved")
    if semantics["PROMPT_SHA256"] != PROMPT_SHA256:
        raise ValidationError("the frozen prompt digest moved")
    if not semantics["REPRESENTATION_UNCHANGED"] or not semantics["PROMPT_UNCHANGED"]:
        raise ValidationError("the record itself says the research payload changed")
    if semantics["REPRESENTATION_SHA256"] != packet["REPRESENTATION_SHA256"]:
        raise ValidationError("the record and V1 name different representations")

    v1 = record["V1_UNTOUCHED"]
    if v1["EXECUTION_PACKET_SHA256"] != V1_SHA256:
        raise ValidationError(
            f"§2: V1's digest is recorded as {v1['EXECUTION_PACKET_SHA256']} and was frozen at "
            f"{V1_SHA256}"
        )
    if packet["EXECUTION_PACKET_SHA256"] != V1_SHA256:
        raise ValidationError("§2: the frozen V1 packet on disk has been edited")
    for key, expected in V1_ROUTE.items():
        if packet[key] != expected:
            raise ValidationError(
                f"§2: V1's {key} is {packet[key]!r} and was frozen at {expected!r}. The API "
                "packet is the fallback and this mission may not repoint it at another route"
            )
    if packet["OPERATOR_EXECUTION_APPROVAL_RECORDED"]:
        raise ValidationError("§21: V1 was marked approved")
    if v1["OPERATOR_EXECUTION_APPROVAL_RECORDED"]:
        raise ValidationError("§21: the record claims V1 carries an approval")
    for key in ("edited_by_this_mission", "provider_changed", "model_changed", "approval_invented"):
        if v1[key]:
            raise ValidationError(f"§2: {key} is true")


PACKET_V2 = DATA / "second-opportunity-synthesis-execution-packet-v2.json"

#: Mission 1.84.6. This mission recorded that IT created no execution packet V2. A V2 that a later
#: mission prepared does not make that false, so the check reads the packet's author instead of
#: requiring the file to be absent: a check pinned to an absence pins the repository's future to
#: one mission's verdict.
THIS_MISSION = (1, 84, 1)


def _v2_prepared_by_a_later_mission() -> bool:
    try:
        prepared_by = json.loads(PACKET_V2.read_text(encoding="utf-8")).get("prepared_by")
    except (OSError, ValueError, AttributeError):
        return False
    if not isinstance(prepared_by, str) or not prepared_by.startswith("mission-"):
        return False
    try:
        return tuple(int(part) for part in prepared_by.removeprefix("mission-").split(".")) > (
            THIS_MISSION
        )
    except ValueError:
        return False


def _check_no_v2_was_forced(record: dict) -> None:
    """§20 and §23. Nine conditions or no packet."""
    v2 = record["EXECUTION_PACKET_V2"]
    met, required = int(v2["conditions_met"]), int(v2["conditions_required"])
    if required != 9:
        raise ValidationError("§20 fixes nine conditions")
    if v2["EXECUTION_PACKET_V2_CREATED"]:
        if met != required:
            raise ValidationError(
                f"a V2 packet with {met} of {required} conditions met. A packet produced anyway "
                "is an executable record of a call that may not be made"
            )
        if not (DATA / "second-opportunity-synthesis-execution-packet-v2.json").exists():
            raise ValidationError("the record claims a V2 packet that is not on disk")
    else:
        if met >= required:
            raise ValidationError(
                "every condition is recorded as met and no V2 exists; one of the two is wrong"
            )
        if not v2["conditions_failed"]:
            raise ValidationError("no V2, and no failed condition named")
        if PACKET_V2.exists() and not _v2_prepared_by_a_later_mission():
            raise ValidationError(
                "a V2 packet exists that the record says was not created, and it does not name "
                "a later mission as its author"
            )

    recommended = record["RECOMMENDED_EXECUTION_PACKET"]
    if recommended not in {"V1", "V2", "NONE"}:
        raise ValidationError(f"recommendation {recommended!r}")
    if recommended == "V2" and not v2["EXECUTION_PACKET_V2_CREATED"]:
        raise ValidationError("a recommendation for a packet that does not exist")
    if not str(record["recommendation_basis"]).strip():
        raise ValidationError("a recommendation with no basis")


def _check_the_fail_closed_position(record: dict) -> None:
    """§18. The invariant is recorded even though the route is refused."""
    collision = record["ENVIRONMENT_COLLISION"]
    if not collision["ANTHROPIC_API_KEY_PRESENT_IN_THE_DEPLOYMENT_ENV"]:
        raise ValidationError(
            "the deployment is recorded as carrying no API key. §6 turns on the collision being "
            "real, and a record that denies it removes the reason the invariant exists"
        )
    if collision["SUBSCRIPTION_ROUTE_FAILS_CLOSED_TODAY"]:
        raise ValidationError(
            "the Gateway is recorded as failing closed on a route it cannot express. There is "
            "nothing to fail closed until a route concept exists"
        )
    if "never execute through ANTHROPIC_PLATFORM_API" not in collision["required_future_invariant"]:
        raise ValidationError("§18: the fail-closed invariant is not stated")
    architecture = record["GATEWAY_ARCHITECTURE_REQUIRED"]
    if architecture["implemented_by_this_mission"]:
        raise ValidationError("an adapter was built for a route whose posture is NOT_APPROVED")
    if architecture["forbidden_shape"] != "try subscription, then API":
        raise ValidationError("§17: the forbidden fallback shape is not named")


def _check_the_accounting(record: dict) -> None:
    accounting = record["ACCOUNTING"]
    for key in ZERO_ACCOUNTING:
        if accounting[key] != 0:
            raise ValidationError(f"{key} is {accounting[key]}, and a feasibility mission does 0")
    if accounting["documentation_requests"] <= 0:
        raise ValidationError(
            "§3 requires current first-party documentation, and none was retrieved"
        )
    models = record["MODEL_AVAILABILITY"]
    if (
        models["SELECTED_SUBSCRIPTION_MODEL"]
        and not record["EXECUTION_PACKET_V2"]["EXECUTION_PACKET_V2_CREATED"]
    ):
        raise ValidationError("a model selected for a route no packet uses")
    if models["AVAILABLE_SUBSCRIPTION_MODELS"] != "NOT_ESTABLISHED" and not str(
        models.get("why") or ""
    ):
        raise ValidationError("a model list with no stated basis")


def validate() -> tuple[dict, dict]:
    record = _load(RECORD)
    register = _load(REGISTER)
    packet = _load(PACKET_V1)
    decision = _load(DECISION_PACKET)

    if record["PRIMARY_OUTCOME"] not in ACCEPTABLE_OUTCOMES:
        raise ValidationError(f"outcome {record['PRIMARY_OUTCOME']!r} is not one of the six")
    if not str(record["outcome_basis"]).strip():
        raise ValidationError("an outcome with no stated basis")
    if (
        record["PRIMARY_OUTCOME"] == "CLAUDE_MAX_SUBSCRIPTION_EXECUTION_PACKET_READY"
        and not record["EXECUTION_PACKET_V2"]["EXECUTION_PACKET_V2_CREATED"]
    ):
        raise ValidationError("the READY outcome with no packet")

    _check_no_secret(record)
    _check_the_route_did_not_inherit(record, register)
    _check_the_required_property(record, decision)
    _check_the_blockers(record)
    _check_the_billing(record)
    _check_the_payload_is_untouched(record, packet)
    _check_no_v2_was_forced(record)
    _check_the_fail_closed_position(record)
    _check_the_accounting(record)

    if (
        record["SELECTED_SUBSCRIPTION_ROUTE"] is not None
        and record["PRIMARY_OUTCOME"] != "CLAUDE_MAX_SUBSCRIPTION_EXECUTION_PACKET_READY"
    ):
        raise ValidationError("a route selected while the outcome refuses it")
    ids = {route["route_id"] for route in record["ROUTES"]}
    for candidate in record["CANDIDATE_SUBSCRIPTION_ROUTES"]:
        if candidate not in ids:
            raise ValidationError(f"candidate {candidate!r} is not described in ROUTES")
    return record, register


def _sentence(text: str) -> str:
    """One trailing period, whatever the source field ended with."""
    return str(text).rstrip().rstrip(".") + "."


def render(record: dict) -> str:
    prompt = record["BLOCKER_1_PROMPT_IDENTITY"]
    calls = record["BLOCKER_2_EXACTLY_ONE_CALL"]
    governance = record["BLOCKER_3_PROVIDER_GOVERNANCE"]
    switch = record["THE_SWITCH"]
    tooling = record["LOCAL_TOOLING"]
    collision = record["ENVIRONMENT_COLLISION"]
    billing = record["BILLING"]
    tier = record["premise_correction"]
    v2 = record["EXECUTION_PACKET_V2"]

    lines = [
        "# Claude subscription route feasibility",
        "",
        "Generated from `claude-subscription-route-feasibility-v1.json`. Do not edit by hand.",
        "",
        f"**{record['PRIMARY_OUTCOME']}**",
        "",
        record["$comment"],
        "",
        _sentence(record["outcome_basis"]),
        "",
        f"Recorded beside it: **{record['secondary_outcome']}**. "
        + _sentence(record["secondary_outcome_basis"]),
        "",
        "## The premise, corrected",
        "",
        f"The mission is written about a **{tier['BRIEF_ASSUMED']}** subscription. The "
        f"subscription this machine holds reports `{tier['LOCALLY_HELD_SUBSCRIPTION_TYPE']}` at "
        f"rate-limit tier `{tier['LOCALLY_HELD_RATE_LIMIT_TIER']}`, so **MAX_TIER = "
        f"{tier['MAX_TIER']}**.",
        "",
        tier["note"],
        "",
        "## Three blockers, and only one is a governance question",
        "",
        "### 1. The frozen prompt bytes cannot be transmitted",
        "",
        f"`PROMPT_SHA256` {prompt['FROZEN_PROMPT_SHA256']} covers {prompt['what_the_digest_covers']}.",
        "",
        f"An agent harness sends {prompt['what_an_agent_harness_sends']}.",
        "",
        _sentence(prompt["why"]),
        "",
        f"Cleared by an operator decision: **{prompt['operator_decision_can_clear_this']}**.",
        "",
        "### 2. Exactly one model call cannot be enforced",
        "",
        f"The frozen packet binds MAX_MODEL_CALLS {calls['FROZEN_MAX_MODEL_CALLS']}, max_retries "
        f"{calls['FROZEN_MAX_RETRIES']}, MAX_OUTPUT_TOKENS {calls['FROZEN_MAX_OUTPUT_TOKENS']} and "
        f"a timeout of {calls['FROZEN_REQUEST_TIMEOUT']}s. One invocation is "
        f"{calls['one_invocation_is']}.",
        "",
        "Flags checked and absent: "
        + ", ".join(f"`{flag}`" for flag in calls["flags_checked_and_absent"])
        + ".",
        "",
    ]
    lines.extend(
        f"- Present but the wrong unit: {item}." for item in calls["flags_present_but_wrong_unit"]
    )
    lines += [
        "",
        f"Cleared by an operator decision: **{calls['operator_decision_can_clear_this']}**.",
        "",
        "### 3. The provider posture does not satisfy TED's own condition",
        "",
        _sentence(governance["why_not_inherited"]),
        "",
        f"The condition, quoted: {governance['required_property']}",
        "",
        f"What the subscription route offers instead: {governance['what_the_subscription_route_offers_instead']}.",
        "",
        f"**PROVIDER_GOVERNANCE_STATE = {governance['PROVIDER_GOVERNANCE_STATE']}**, registered as "
        f"`{governance['provider_id_registered']}`. {governance['why_a_separate_provider_id']}.",
        "",
        f"Cleared by an operator decision: {governance['operator_decision_can_clear_this']}.",
        "",
        "## The switch",
        "",
        f"`{switch['flag']}` is documented as: {switch['documented_as']}",
        "",
        switch["also_documented_as"],
        "",
        _sentence(switch["consequence"]),
        "",
        "## Routes",
        "",
        "| route | auth | usage model | governed by | posture | shape |",
        "|---|---|---|---|---|---|",
    ]
    for route in record["ROUTES"]:
        lines.append(
            f"| `{route['route_id']}` | {route['authentication']} | {route['usage_model']} | "
            f"{route['governed_by']} | **{route['posture']}** | {route['shape']} |"
        )
    lines += [
        "",
        f"**SELECTED_SUBSCRIPTION_ROUTE = {record['SELECTED_SUBSCRIPTION_ROUTE']}**",
        "",
        "## Local tooling",
        "",
        f"- Claude CLI present: {tooling['CLAUDE_CLI_PRESENT']}, version "
        f"`{tooling['CLAUDE_CLI_VERSION']}`",
        f"- Agent SDK present: {tooling['AGENT_SDK_PRESENT']}",
        f"- Subscription auth supported: {tooling['SUBSCRIPTION_AUTH_SUPPORTED']} "
        f"({tooling['subscription_auth_mechanism']})",
        f"- Non-interactive supported: {tooling['NON_INTERACTIVE_SUPPORTED']} "
        f"({tooling['non_interactive_mechanism']})",
        f"- Credential values read / printed / persisted: "
        f"{tooling['credential_values_read']} / {tooling['credential_values_printed']} / "
        f"{tooling['credential_values_persisted']}",
        "",
        _sentence(tooling["agent_sdk_note"]),
        "",
        "## The environment collision",
        "",
        f"- `ANTHROPIC_API_KEY` in this agent's process: "
        f"{collision['ANTHROPIC_API_KEY_PRESENT_IN_THIS_AGENT_PROCESS']}",
        f"- `ANTHROPIC_API_KEY` in the deployment environment: "
        f"**{collision['ANTHROPIC_API_KEY_PRESENT_IN_THE_DEPLOYMENT_ENV']}** "
        f"(`{collision['deployment_env_file']}`, {collision['value_class_only']}, value read: "
        f"{collision['value_read']})",
        "",
        _sentence(collision["why_the_two_differ_matters"]),
        "",
        f"**SUBSCRIPTION_ROUTE_FAILS_CLOSED_TODAY = "
        f"{collision['SUBSCRIPTION_ROUTE_FAILS_CLOSED_TODAY']}.** {collision['why_not']}.",
        "",
        f"Required future invariant: {collision['required_future_invariant']}.",
        "",
        "## Billing",
        "",
        f"- V1: `{billing['V1_BILLING_CLASS']}`, API_PAYG {billing['V1_API_PAYG']}",
        f"- Subscription: `{billing['SUBSCRIPTION_BILLING_CLASS']}`, usage limited "
        f"{billing['SUBSCRIPTION_USAGE_LIMITED']}, free {billing['subscription_is_free']}, "
        f"unlimited {billing['subscription_is_unlimited']}",
        "",
        _sentence(billing["evidence"]),
        "",
        "## Models",
        "",
        f"**AVAILABLE_SUBSCRIPTION_MODELS = {record['MODEL_AVAILABILITY']['AVAILABLE_SUBSCRIPTION_MODELS']}.** "
        f"{record['MODEL_AVAILABILITY']['why']}.",
        "",
        f"Not assumed: {record['MODEL_AVAILABILITY']['what_was_NOT_assumed']}.",
        "",
        "## No V2",
        "",
        f"**EXECUTION_PACKET_V2_CREATED = {v2['EXECUTION_PACKET_V2_CREATED']}**, "
        f"{v2['conditions_met']} of {v2['conditions_required']} conditions met.",
        "",
    ]
    lines.extend(f"- Failed: {item}" for item in v2["conditions_failed"])
    lines += [
        "",
        v2["why_not"] + ".",
        "",
        f"**RECOMMENDED_EXECUTION_PACKET = {record['RECOMMENDED_EXECUTION_PACKET']}.** "
        f"{record['recommendation_basis']}.",
        "",
        "## What this mission spent",
        "",
        "| counter | value |",
        "|---|---|",
    ]
    for key, value in record["ACCOUNTING"].items():
        if key.endswith("_note"):
            continue
        lines.append(f"| {key} | {value} |")
    lines += [
        "",
        _sentence(record["ACCOUNTING"]["documentation_requests_note"]),
        "",
        f"**Next: {record['NEXT_ACTION']}**",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        record, register = validate()
    except ValidationError as error:
        print(f"REFUSED  claude subscription route feasibility: {error}")
        return 1
    text = render(record)
    if args.check:
        if not RECORD_MD.exists():
            print(f"DRIFT    {RECORD_MD.name} does not exist")
            return 1
        if RECORD_MD.read_text(encoding="utf-8") != text:
            print(f"DRIFT    {RECORD_MD.name} does not match its record")
            return 1
        print("ok       the subscription route feasibility record matches its own")
        return 0
    RECORD_MD.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote    {RECORD_MD.name} ({len(text.splitlines())} lines)")
    print(f"outcome  {record['PRIMARY_OUTCOME']}")
    print(f"approved {approved_providers(register)}")
    print(
        f"v1       unchanged at {record['V1_UNTOUCHED']['EXECUTION_PACKET_SHA256'][:8]}…, "
        f"recommended {record['RECOMMENDED_EXECUTION_PACKET']}"
    )
    print(f"sent     0 bytes; {hashlib.sha256(RECORD.read_bytes()).hexdigest()[:8]}… record")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
