"""Mission 1.84.5, gate 69. Each mutation must be refused by the check written for it.

The gate is run against temporary copies of its three records, so nothing shipped is touched. A
receipt mutation repairs the measurement record's pointer to the receipt first, so the content
check does the refusing rather than the digest check standing in front of it.

Two controls matter as much as the refusals. An estimate UNDER the documented maximum must still
validate with the headroom-decision outcome, because a gate that could only express "exceeds"
would force the next measurement to be recorded as something it is not. And the shipped records
must validate unmodified.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE_PATH = (
    REPO_ROOT / "infrastructure" / "scripts" / "render_second_opportunity_token_measurement.py"
)

SYNTHETIC_SECRET = "sk-ant-SYNTHETIC-MARKER-0000000000"  # noqa: S105 - a fixture, not a credential


def _gate():
    spec = importlib.util.spec_from_file_location("token_measurement_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate():
    return _gate()


@pytest.fixture
def world(tmp_path, monkeypatch, gate):
    copies = {}
    for attr in ("MEASUREMENT", "REGISTER", "RECEIPT"):
        source = getattr(gate, attr)
        target = tmp_path / source.name
        target.write_bytes(source.read_bytes())
        monkeypatch.setattr(gate, attr, target)
        copies[attr] = target
    monkeypatch.setattr(gate, "PACKET_V2", tmp_path / "absent-packet-v2.json")
    return copies


def _read(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: pathlib.Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _mutate(world, which: str, fn) -> None:
    data = _read(world[which])
    fn(data)
    _write(world[which], data)
    if which == "RECEIPT":
        record = _read(world["MEASUREMENT"])
        record["MEASUREMENT"]["receipt_sha256"] = hashlib.sha256(
            world["RECEIPT"].read_bytes()
        ).hexdigest()
        _write(world["MEASUREMENT"], record)


def _set(path: str, value):
    keys = path.split(".")

    def apply(data: dict) -> None:
        node = data
        for key in keys[:-1]:
            node = node[int(key)] if isinstance(node, list) else node[key]
        last = keys[-1]
        if isinstance(node, list):
            node[int(last)] = value
        else:
            node[last] = value

    return apply


def _drop(path: str):
    keys = path.split(".")

    def apply(data: dict) -> None:
        node = data
        for key in keys[:-1]:
            node = node[key]
        del node[keys[-1]]

    return apply


# ============================================================ controls


class TestControls:
    def test_the_shipped_records_validate_and_render(self, gate) -> None:
        gate.validate()
        assert gate.main(["--check"]) == 0

    def test_an_estimate_under_the_maximum_can_carry_the_headroom_outcome(
        self, gate, world
    ) -> None:
        """The non-exceeding outcome must stay expressible, recomputed end to end."""
        estimate = 100000

        def receipt(data: dict) -> None:
            data["INPUT_TOKENS"] = estimate
            data["response"]["body"] = json.dumps({"input_tokens": estimate})

        _mutate(world, "RECEIPT", receipt)
        record = _read(world["MEASUREMENT"])
        record["PRIMARY_OUTCOME"] = (
            "PROVIDER_NATIVE_TOKEN_ESTIMATE_READY_OPERATOR_HEADROOM_DECISION_REQUIRED"
        )
        record["MEASUREMENT"]["PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE"] = estimate
        capacity = record["CAPACITY_COMPARISON"]
        capacity["HEADROOM_TO_PROVIDER_MAX"] = 128000 - estimate
        capacity["ESTIMATE_OVER_PROVIDER_MAX"] = round(estimate / 128000, 4)
        capacity["EXCEEDS_PROVIDER_MAX"] = False
        capacity["HEADROOM_TO_BATCH_BETA_MAX"] = 300000 - estimate
        cross = record["EMPIRICAL_RATIO_CROSS_CHECK"]
        predicted = round(309729 / 2.1565)
        cross["provider_native_estimate"] = estimate
        cross["held_ratio_underestimates_by_tokens"] = estimate - predicted
        cross["held_ratio_underestimates_by_fraction"] = round((estimate - predicted) / estimate, 4)
        cross["measured_characters_per_token"] = round(309729 / estimate, 4)
        _write(world["MEASUREMENT"], record)
        gate.validate()

    def test_an_estimate_under_the_maximum_may_still_be_called_approaching(
        self, gate, world
    ) -> None:
        estimate = 125000

        def receipt(data: dict) -> None:
            data["INPUT_TOKENS"] = estimate
            data["response"]["body"] = json.dumps({"input_tokens": estimate})

        _mutate(world, "RECEIPT", receipt)
        record = _read(world["MEASUREMENT"])
        record["MEASUREMENT"]["PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE"] = estimate
        capacity = record["CAPACITY_COMPARISON"]
        capacity["HEADROOM_TO_PROVIDER_MAX"] = 128000 - estimate
        capacity["ESTIMATE_OVER_PROVIDER_MAX"] = round(estimate / 128000, 4)
        capacity["EXCEEDS_PROVIDER_MAX"] = False
        capacity["HEADROOM_TO_BATCH_BETA_MAX"] = 300000 - estimate
        cross = record["EMPIRICAL_RATIO_CROSS_CHECK"]
        predicted = round(309729 / 2.1565)
        cross["provider_native_estimate"] = estimate
        cross["held_ratio_underestimates_by_tokens"] = estimate - predicted
        cross["held_ratio_underestimates_by_fraction"] = round((estimate - predicted) / estimate, 4)
        cross["measured_characters_per_token"] = round(309729 / estimate, 4)
        _write(world["MEASUREMENT"], record)
        gate.validate()


# ============================================================ refusals

RECEIPT_CASES = [
    ("outcome failed", _set("OUTCOME", "TOKEN_MEASUREMENT_FAILED_NO_RETRY"), "not MEASURED"),
    ("messages endpoint", _set("endpoint", "https://api.anthropic.com/v1/messages"), "endpoint"),
    ("system sent", _set("request_shape.system_sent", True), "system_sent"),
    ("tools sent", _set("request_shape.tools_sent", True), "tools_sent"),
    ("thinking sent", _set("request_shape.thinking_sent", True), "thinking_sent"),
    ("max_tokens sent", _set("request_shape.max_tokens_sent", True), "max_tokens_sent"),
    (
        "extra header",
        _set("request_shape.header_names", ["anthropic-version", "authorization", "x-api-key"]),
        "header_names",
    ),
    (
        "extra body key",
        _set("request_shape.body_keys", ["messages", "model", "system"]),
        "body_keys",
    ),
    ("another model", _set("request_shape.model", "claude-opus-5"), "request_shape.model"),
    ("credential recorded", _set("credential_value_recorded", True), "no credential value"),
    ("a retry", _set("ACCOUNTING.RETRIES", 1), "accounting"),
    ("a messages request", _set("ACCOUNTING.MESSAGES_API_REQUESTS", 1), "accounting"),
    ("bool tokens", _set("INPUT_TOKENS", True), "positive integer"),
    ("zero tokens", _set("INPUT_TOKENS", 0), "positive integer"),
    ("body disagrees", _set("response.body", '{"input_tokens": 1}'), "response body"),
    ("not a 200", _set("response.status", 500), "not a 200"),
    ("a failure", _set("failure", {"type": "X", "message": "y"}), "carries a failure"),
    ("text digest moved", _set("MEASUREMENT_TEXT_SHA256", "0" * 64), "live rebuild"),
    ("text length moved", _set("MEASUREMENT_TEXT_CHARACTERS", 309728), "live rebuild"),
    ("secret echoed", _set("response.request_id", SYNTHETIC_SECRET), "credential-shaped"),
]

MEASUREMENT_CASES = [
    ("unknown outcome", _set("PRIMARY_OUTCOME", "ALL_GOOD"), "Section 27"),
    (
        "ready while exceeding",
        _set(
            "PRIMARY_OUTCOME",
            "PROVIDER_NATIVE_TOKEN_ESTIMATE_READY_OPERATOR_HEADROOM_DECISION_REQUIRED",
        ),
        "Section 21",
    ),
    ("exact count recorded", _set("MEASUREMENT.EXACT_MAX_OUTPUT_TOKEN_COUNT", 231608), "exact"),
    (
        "estimate moved",
        _set("MEASUREMENT.PROVIDER_NATIVE_MAX_INSTANCE_TOKEN_ESTIMATE", 1),
        "receipt",
    ),
    ("called exact", _set("MEASUREMENT.ESTIMATE_NOT_EXACT", False), "ESTIMATE_NOT_EXACT"),
    (
        "equivalence claimed",
        _set("MEASUREMENT.INPUT_TO_OUTPUT_TOKENIZATION_EQUIVALENCE", "ESTABLISHED"),
        "INPUT_TO_OUTPUT",
    ),
    ("margin invented", _set("MEASUREMENT.DOCUMENTED_TOKEN_COUNT_MARGIN", "5%"), "MARGIN"),
    ("request id moved", _set("MEASUREMENT.request_id", "req_other"), "request id"),
    ("receipt digest moved", _set("MEASUREMENT.receipt_sha256", "0" * 64), "receipt changed"),
    ("max read as 2^17", _set("CAPACITY_COMPARISON.MODEL_MAX_OUTPUT_TOKENS", 131072), "128000"),
    (
        "adapter default promoted",
        _set("CAPACITY_COMPARISON.ADAPTER_DEFAULT_MAX_OUTPUT_TOKENS", 128000),
        "adapter default",
    ),
    ("headroom wrong", _set("CAPACITY_COMPARISON.HEADROOM_TO_PROVIDER_MAX", 0), "HEADROOM"),
    ("ratio wrong", _set("CAPACITY_COMPARISON.ESTIMATE_OVER_PROVIDER_MAX", 1.0), "OVER_PROVIDER"),
    ("exceeds denied", _set("CAPACITY_COMPARISON.EXCEEDS_PROVIDER_MAX", False), "EXCEEDS"),
    ("batch adopted", _set("CAPACITY_COMPARISON.batch_route_adopted", True), "batch route"),
    ("ceiling selected", _set("CEILING.SELECTED_MAX_OUTPUT_TOKENS", 128000), "ceiling"),
    ("headroom policy", _set("CEILING.OPERATOR_HEADROOM_POLICY", "10%"), "headroom policy"),
    ("v2 claimed", _set("EXECUTION_PACKET_V2_CREATED", True), "V2"),
    ("schema reduced", _set("SCHEMA_REDUCED", True), "reduced"),
    (
        "option recommended",
        _set("OPTION_RECOMMENDED", "SPLIT_THE_SYNTHESIS_ACROSS_CALLS"),
        "option",
    ),
    ("option implemented", _set("OPTIONS_IMPLEMENTED", ["X"]), "option"),
    ("option without cost", _set("OPERATOR_OPTIONS.0.cost", ""), "effect or cost"),
    (
        "cross-check forged",
        _set("EMPIRICAL_RATIO_CROSS_CHECK.predicted_tokens_from_held_ratio", 231608),
        "predicted",
    ),
    ("count billed", _set("COST.TOKEN_COUNT_API_COST", 0.01), "counting cost"),
    ("inference priced", _set("COST.FUTURE_INFERENCE_COST", 0.5), "inference cost"),
    ("a second request", _set("ACCOUNTING.TOKEN_COUNT_API_REQUESTS", 2), "accounting"),
    ("a model call", _set("ACCOUNTING.MODEL_INFERENCE_REQUESTS", 1), "accounting"),
    (
        "a counter moved",
        lambda data: data["CANONICAL_COUNTERS"].__setitem__("research.claims", 92),
        "counter",
    ),
    ("start commit", _set("START_COMMIT", "main"), "START_COMMIT"),
    ("precondition moved", _set("PRECONDITIONS_1_84_4.SCHEMA_SHA256", "0" * 64), "SCHEMA_SHA256"),
    (
        "thinking left on",
        _set("THINKING.CLAUDE_SONNET_5_THINKING_POLICY", "PROVIDER_DEFAULT"),
        "POLICY",
    ),
    ("v2 thinking on", _set("THINKING.FUTURE_V2_THINKING", "ADAPTIVE"), "FUTURE_V2"),
    ("shared budget", _set("THINKING.THINKING_TOKENS_SHARE_V2_MAX_TOKENS", True), "SHARE"),
    (
        "architecture needed",
        _set("THINKING.THINKING_CONTROL_REQUIRES_ARCHITECTURE_DECISION", True),
        "ARCHITECTURE",
    ),
    (
        "third member",
        _set("THINKING.ADAPTER_CAPABILITY.members", ["PROVIDER_DEFAULT", "DISABLED", "ADAPTIVE"]),
        "configurations",
    ),
    (
        "generic parameters",
        _set("THINKING.ADAPTER_CAPABILITY.generic_parameter_collection", True),
        "generic",
    ),
    (
        "wrong disabled field",
        _set("THINKING.ADAPTER_CAPABILITY.disabled_request_field", {"type": "off"}),
        "documented object",
    ),
    (
        "native claimed",
        _set("STRUCTURED_OUTPUT.NATIVE_PROVIDER_STRUCTURED_OUTPUT", True),
        "migration",
    ),
    ("root cause rewritten", _set("V1_THINKING_FINDING.V1_ROOT_CAUSE", "TRUNCATION"), "root cause"),
    (
        "shared budget denied",
        _set("V1_THINKING_FINDING.V1_OUTPUT_BUDGET_SHARED_WITH_ADAPTIVE_THINKING", False),
        "SHARED_WITH",
    ),
    (
        "thinking consumption invented",
        _set("V1_THINKING_FINDING.V1_THINKING_TOKENS_CONSUMED", 1200),
        "CONSUMED",
    ),
    ("v1 budget moved", _set("V1_THINKING_FINDING.V1_MAX_OUTPUT_TOKENS", 4096), "frozen packet"),
    (
        "inference claimed",
        _set(
            "DOCUMENTED_PROPOSITIONS.F_COUNT_IS_NOT_MESSAGE_CREATION.classification", "DOCUMENTED"
        ),
        "inference",
    ),
    ("proposition dropped", _drop("DOCUMENTED_PROPOSITIONS.G_BILLING"), "A to M"),
    (
        "no fragment",
        _set("DOCUMENTED_PROPOSITIONS.G_BILLING.fragments", []),
        "cites no fragment",
    ),
    (
        "failed page cited",
        _set("DOCUMENTED_PROPOSITIONS.G_BILLING.fragments.0.evidence", "E03"),
        "not used evidence",
    ),
    (
        "long quotation",
        _set("DOCUMENTED_PROPOSITIONS.G_BILLING.fragments.0.verbatim", "word " * 40),
        "short fragment",
    ),
    (
        "third-party page",
        _set("DOCUMENTATION_EVIDENCE.6.final_url", "https://example.com/token-counting.md"),
        "first-party",
    ),
    ("no instant", _set("DOCUMENTATION_EVIDENCE.6.retrieved_at", "today"), "instant"),
    ("404 used", _set("DOCUMENTATION_EVIDENCE.2.used", True), "did not answer 200"),
    ("third party counted", _set("DOCUMENTATION_FETCHES.third_party_sources", 1), "third-party"),
    ("failure hidden", _set("DOCUMENTATION_FETCHES.failed", []), "non-200"),
    (
        "expectation unsupported",
        _set("BRIEF_EXPECTATIONS_RE_ESTABLISHED.0.agrees", False),
        "unsupported",
    ),
]

REGISTER_CASES = [
    (
        "register max",
        _set("MODELS.claude-sonnet-5.DOCUMENTED_MAX_OUTPUT_TOKENS", 131072),
        "DOCUMENTED_MAX",
    ),
    (
        "thinking not disable-able",
        _set("MODELS.claude-sonnet-5.THINKING_DISABLE_SUPPORTED", False),
        "DISABLE",
    ),
    (
        "budget scope",
        _set("MODELS.claude-sonnet-5.MAX_TOKENS_COVERS", "RESPONSE"),
        "MAX_TOKENS_COVERS",
    ),
    (
        "unknown proposition",
        _set("MODELS.claude-sonnet-5.propositions", ["Z_NOTHING"]),
        "does not hold",
    ),
    (
        "adapter default",
        _set("ADAPTER.ADAPTER_DEFAULT_MAX_OUTPUT_TOKENS", 128000),
        "adapter default",
    ),
    (
        "adapter thinking",
        _set("ADAPTER.THINKING_CONFIGURATIONS", ["DISABLED"]),
        "thinking configurations",
    ),
    ("native used", _set("ADAPTER.NATIVE_STRUCTURED_OUTPUT_USED", True), "native"),
    (
        "endpoint",
        _set("ADAPTER.COUNT_TOKENS_ENDPOINT", "https://api.anthropic.com/v1/messages"),
        "count endpoint",
    ),
    ("merged", _set("DOCUMENTED_MAX_AND_ADAPTER_DEFAULT_DISTINCT", False), "merged"),
    ("another model", _set("provider", "gemini"), "another provider"),
]


@pytest.mark.parametrize(("name", "fn", "match"), RECEIPT_CASES, ids=[c[0] for c in RECEIPT_CASES])
def test_a_receipt_mutation_is_refused(gate, world, name, fn, match) -> None:
    _mutate(world, "RECEIPT", fn)
    with pytest.raises(gate.ValidationError, match=match):
        gate.validate()


@pytest.mark.parametrize(
    ("name", "fn", "match"), MEASUREMENT_CASES, ids=[c[0] for c in MEASUREMENT_CASES]
)
def test_a_measurement_mutation_is_refused(gate, world, name, fn, match) -> None:
    _mutate(world, "MEASUREMENT", fn)
    with pytest.raises(gate.ValidationError, match=match):
        gate.validate()


@pytest.mark.parametrize(
    ("name", "fn", "match"), REGISTER_CASES, ids=[c[0] for c in REGISTER_CASES]
)
def test_a_register_mutation_is_refused(gate, world, name, fn, match) -> None:
    _mutate(world, "REGISTER", fn)
    with pytest.raises(gate.ValidationError, match=match):
        gate.validate()


def test_an_execution_packet_v2_on_disk_is_refused(gate, world, tmp_path, monkeypatch) -> None:
    packet = tmp_path / "second-opportunity-synthesis-execution-packet-v2.json"
    packet.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(gate, "PACKET_V2", packet)
    with pytest.raises(gate.ValidationError, match="V2"):
        gate.validate()


def test_a_hand_edited_rendering_fails_the_check(gate, tmp_path, monkeypatch) -> None:
    for attr in ("MEASUREMENT_MD", "REGISTER_MD"):
        source = getattr(gate, attr)
        target = tmp_path / source.name
        target.write_text(source.read_text(encoding="utf-8") + "edited\n", encoding="utf-8")
        monkeypatch.setattr(gate, attr, target)
    assert gate.main(["--check"]) == 1
