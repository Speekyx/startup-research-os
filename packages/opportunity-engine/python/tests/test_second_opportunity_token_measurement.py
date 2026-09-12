"""Mission 1.84.5. The one provider-native token count, and everything that stops a second one.

Every test here runs against a scripted transport and a temporary receipt path. None reaches a
network, and a tripwire proves the dry run never constructs the real transport's socket path.

Four things this file defends.

ONLY THE SYNTHETIC MAXIMUM LEAVES. The text is rebuilt from the live schema, it must reproduce
Mission 1.84.4's numbers exactly, and the socket seam checks its digest again before sending.

ONE REQUEST, TO ONE ENDPOINT, NEVER RETRIED. A receipt refuses a second measurement, the seam
refuses a second call and any URL but the count endpoint, and a failure is recorded, not retried.

THE SMALLEST VALID REQUEST. The model and one user message; no system text, no tools, no
max_tokens and no thinking field, because each would add tokens the measurement is not about.

NO CREDENTIAL IN ANY ARTIFACT. Header names are recorded and header values never are.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest
from sros_llm_gateway.providers.anthropic import COUNT_TOKENS_ENDPOINT, DEFAULT_ENDPOINT
from sros_llm_gateway.transport import FakeTransport, HttpResponse, UrllibTransport
from sros_opportunity.schema_validation import schema_violations
from sros_opportunity.second_opportunity import SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
RUNNER_PATH = (
    REPO_ROOT / "infrastructure" / "scripts" / "run_second_opportunity_token_measurement.py"
)

SYNTHETIC_SECRET = "sk-ant-SYNTHETIC-MARKER-0000000000"  # noqa: S105 - a fixture, not a credential


def _runner():
    spec = importlib.util.spec_from_file_location("token_measurement_runner", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runner():
    return _runner()


@pytest.fixture(scope="module")
def measured(runner):
    return runner.measurement_text(runner.bounded_contract_gate())


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """A receipt path nobody else writes, and a credential that is a synthetic marker."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", SYNTHETIC_SECRET)
    env_file = tmp_path / "absent.env"
    return tmp_path / "receipt.json", env_file


def _ok(tokens: int = 1234) -> HttpResponse:
    return HttpResponse(
        200, json.dumps({"input_tokens": tokens}).encode("utf-8"), {"request-id": "req_synthetic"}
    )


# ============================================================ the text that leaves


class TestTheMeasurementText:
    def test_it_reproduces_mission_1_84_4_exactly(self, runner, measured) -> None:
        text, facts = measured
        assert facts["MEASUREMENT_TEXT_CHARACTERS"] == 309729 == len(text)
        assert facts["MEASUREMENT_TEXT_UTF8_BYTES"] == 309729
        assert facts["MEASUREMENT_TEXT_SHA256"] == runner.EXPECTED_TEXT_SHA256
        assert facts["MEASUREMENT_SCHEMA_SHA256"] == runner.EXPECTED_SCHEMA_SHA256
        assert facts["MEASUREMENT_SCHEMA_ID"] == "second-opportunity-synthesis-output@1.1.0"

    def test_it_is_the_maximum_instance_and_validates(self, runner, measured) -> None:
        text, _ = measured
        instance = json.loads(text)
        gate = runner.bounded_contract_gate()
        assert instance == gate.maximum_instance(
            SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, gate.WORST_FILL
        )
        assert schema_violations(instance, SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1) == []

    def test_every_string_leaf_is_synthetic(self, runner, measured) -> None:
        """No TED byte and no research byte: each leaf is a fill run, the zero UUID, a slug run of
        `a`, or a member of a closed vocabulary the schema itself declares."""
        text, _ = measured
        gate = runner.bounded_contract_gate()
        allowed_enum: set[str] = set()

        def enums(node) -> None:
            if isinstance(node, dict):
                if "enum" in node:
                    allowed_enum.update(node["enum"])
                for value in node.values():
                    enums(value)

        enums(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)
        zero_uuid = "00000000-0000-0000-0000-000000000000"

        def leaves(value):
            if isinstance(value, dict):
                for v in value.values():
                    yield from leaves(v)
            elif isinstance(value, list):
                for v in value:
                    yield from leaves(v)
            else:
                yield value

        for leaf in leaves(json.loads(text)):
            assert isinstance(leaf, str)
            assert (
                leaf in allowed_enum
                or leaf == zero_uuid
                or set(leaf) == {"a"}
                or set(leaf) == {gate.WORST_FILL}
            ), leaf[:40]

    def test_the_serialized_text_is_pure_ascii(self, measured) -> None:
        """ensure_ascii, so bytes and characters coincide: the worst case Mission 1.84.4 recorded."""
        text, _ = measured
        assert text.isascii()


# ============================================================ refusals before the socket


class TestRefusalsSendNothing:
    def test_a_changed_maximum_is_refused_before_a_transport_is_asked(
        self, runner, isolated, monkeypatch
    ) -> None:
        receipt, env_file = isolated
        monkeypatch.setattr(runner, "EXPECTED_TEXT_SHA256", "0" * 64)
        transport = FakeTransport.returning(_ok())
        with pytest.raises(runner.RefusedError) as ctx:
            runner.execute(transport=transport, receipt_path=receipt, env_file=env_file)
        assert ctx.value.code == "BOUNDED_OUTPUT_MAX_INSTANCE_CHANGED"
        assert transport.calls == []
        assert not receipt.exists()

    def test_an_existing_receipt_refuses_a_second_measurement(self, runner, isolated) -> None:
        receipt, env_file = isolated
        receipt.write_text("{}", encoding="utf-8")
        transport = FakeTransport.returning(_ok())
        with pytest.raises(runner.RefusedError) as ctx:
            runner.execute(transport=transport, receipt_path=receipt, env_file=env_file)
        assert ctx.value.code == "TOKEN_MEASUREMENT_ALREADY_PERFORMED"
        assert transport.calls == []
        assert receipt.read_text(encoding="utf-8") == "{}"

    def test_a_missing_credential_sends_nothing_and_writes_nothing(
        self, runner, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        receipt = tmp_path / "receipt.json"
        transport = FakeTransport.returning(_ok())
        with pytest.raises(runner.RefusedError) as ctx:
            runner.execute(
                transport=transport, receipt_path=receipt, env_file=tmp_path / "absent.env"
            )
        assert ctx.value.code == "PROVIDER_CREDENTIAL_ABSENT"
        assert transport.calls == []
        assert not receipt.exists()

    def test_the_compose_file_is_read_for_the_one_key_only(
        self, runner, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("SOME_OTHER_SETTING", raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text(
            f"SOME_OTHER_SETTING=x\nANTHROPIC_API_KEY={SYNTHETIC_SECRET}\n", encoding="utf-8"
        )
        assert runner.credential_source(env_file) == "LOADED_FROM_COMPOSE_FILE_ONE_KEY_ONLY"
        import os

        assert "SOME_OTHER_SETTING" not in os.environ


# ============================================================ the one request


class TestTheOneRequest:
    def test_one_request_to_the_count_endpoint_with_the_smallest_body(
        self, runner, measured, isolated
    ) -> None:
        receipt_path, env_file = isolated
        text, _ = measured
        transport = FakeTransport.returning(_ok(4321))
        receipt = runner.execute(transport=transport, receipt_path=receipt_path, env_file=env_file)

        assert len(transport.calls) == 1
        call = transport.calls[0]
        assert call["url"] == COUNT_TOKENS_ENDPOINT
        assert call["body"] == {
            "model": "claude-sonnet-5",
            "messages": [{"role": "user", "content": text}],
        }
        assert set(call["headers"]) == {"x-api-key", "anthropic-version"}

        assert receipt["OUTCOME"] == "MEASURED"
        assert receipt["INPUT_TOKENS"] == 4321
        shape = receipt["request_shape"]
        assert shape["body_keys"] == ["messages", "model"]
        assert not shape["system_sent"] and not shape["tools_sent"]
        assert not shape["thinking_sent"] and not shape["max_tokens_sent"]
        assert receipt["ACCOUNTING"] == {
            "TOKEN_COUNT_API_REQUESTS": 1,
            "RETRIES": 0,
            "MESSAGES_API_REQUESTS": 0,
            "MODEL_INFERENCE_REQUESTS": 0,
            "TED_BYTES_SENT": 0,
            "RESEARCH_BYTES_SENT": 0,
        }
        assert json.loads(receipt_path.read_text(encoding="utf-8")) == receipt

    def test_the_receipt_never_contains_the_credential(self, runner, isolated) -> None:
        receipt_path, env_file = isolated
        echoed = HttpResponse(
            401, json.dumps({"error": {"message": f"bad key {SYNTHETIC_SECRET}"}}).encode("utf-8")
        )
        runner.execute(
            transport=FakeTransport.returning(echoed), receipt_path=receipt_path, env_file=env_file
        )
        written = receipt_path.read_text(encoding="utf-8")
        assert SYNTHETIC_SECRET not in written
        assert "[REDACTED]" in written
        assert json.loads(written)["credential_value_recorded"] is False

    def test_a_failure_is_recorded_and_never_retried(self, runner, isolated) -> None:
        receipt_path, env_file = isolated
        transport = FakeTransport.returning(
            HttpResponse(500, b'{"error": {"message": "overloaded"}}'), _ok()
        )
        receipt = runner.execute(transport=transport, receipt_path=receipt_path, env_file=env_file)
        assert len(transport.calls) == 1
        assert len(transport.responses) == 1, "the second scripted answer is never asked for"
        assert receipt["OUTCOME"] == "TOKEN_MEASUREMENT_FAILED_NO_RETRY"
        assert receipt["INPUT_TOKENS"] is None
        assert receipt["ACCOUNTING"]["RETRIES"] == 0

    def test_a_second_execution_is_refused_after_the_first(self, runner, isolated) -> None:
        receipt_path, env_file = isolated
        runner.execute(
            transport=FakeTransport.returning(_ok()), receipt_path=receipt_path, env_file=env_file
        )
        again = FakeTransport.returning(_ok())
        with pytest.raises(runner.RefusedError) as ctx:
            runner.execute(transport=again, receipt_path=receipt_path, env_file=env_file)
        assert ctx.value.code == "TOKEN_MEASUREMENT_ALREADY_PERFORMED"
        assert again.calls == []


# ============================================================ the seam


class TestTheSeam:
    def _seam(self, runner, measured, inner):
        _, facts = measured
        return runner.OneShotTransport(
            inner,
            allowed_url=COUNT_TOKENS_ENDPOINT,
            model="claude-sonnet-5",
            content_sha256=facts["MEASUREMENT_TEXT_SHA256"],
        )

    def _body(self, measured):
        text, _ = measured
        return {"model": "claude-sonnet-5", "messages": [{"role": "user", "content": text}]}

    def test_it_refuses_the_messages_endpoint(self, runner, measured) -> None:
        inner = FakeTransport.returning(_ok())
        seam = self._seam(runner, measured, inner)
        with pytest.raises(runner.RefusedError) as ctx:
            seam.post_json(DEFAULT_ENDPOINT, {}, self._body(measured), 1.0)
        assert ctx.value.code == "ONLY_THE_COUNT_TOKENS_ENDPOINT_IS_AUTHORISED"
        assert inner.calls == []

    def test_it_refuses_a_second_call(self, runner, measured) -> None:
        inner = FakeTransport.returning(_ok(), _ok())
        seam = self._seam(runner, measured, inner)
        seam.post_json(COUNT_TOKENS_ENDPOINT, {}, self._body(measured), 1.0)
        with pytest.raises(runner.RefusedError) as ctx:
            seam.post_json(COUNT_TOKENS_ENDPOINT, {}, self._body(measured), 1.0)
        assert ctx.value.code == "TOKEN_COUNT_API_REQUESTS_MAX_IS_ONE"
        assert len(inner.calls) == 1

    @pytest.mark.parametrize(
        "mutate",
        [
            lambda b: {**b, "system": "You are a scientist"},
            lambda b: {**b, "tools": []},
            lambda b: {**b, "thinking": {"type": "disabled"}},
            lambda b: {**b, "max_tokens": 1},
            lambda b: {**b, "model": "claude-opus-5"},
            lambda b: {**b, "messages": [{"role": "user", "content": "a research sentence"}]},
            lambda b: {**b, "messages": b["messages"] * 2},
            lambda b: {
                **b,
                "messages": [{"role": "assistant", "content": b["messages"][0]["content"]}],
            },
        ],
    )
    def test_it_refuses_any_body_but_the_smallest_valid_one(self, runner, measured, mutate) -> None:
        inner = FakeTransport.returning(_ok())
        seam = self._seam(runner, measured, inner)
        with pytest.raises(runner.RefusedError):
            seam.post_json(COUNT_TOKENS_ENDPOINT, {}, mutate(self._body(measured)), 1.0)
        assert inner.calls == []


# ============================================================ the dry run and the source


class TestTheDryRunAndTheSource:
    def test_the_dry_run_sends_nothing(self, runner, tmp_path, monkeypatch, capsys) -> None:
        def tripwire(*args, **kwargs):
            raise AssertionError("the dry run reached the real transport")

        monkeypatch.setattr(UrllibTransport, "post_json", tripwire)
        monkeypatch.setenv("ANTHROPIC_API_KEY", SYNTHETIC_SECRET)
        receipt = tmp_path / "receipt.json"
        assert runner.main([], receipt_path=receipt, env_file=tmp_path / "absent.env") == 0
        out = capsys.readouterr().out
        assert "DRY_RUN_ZERO_REQUESTS" in out
        assert SYNTHETIC_SECRET not in out
        assert not receipt.exists()

    def test_the_runner_can_reach_no_other_surface(self) -> None:
        """No Gateway, no `complete`, no Messages API: the only provider method it calls counts."""
        source = RUNNER_PATH.read_text(encoding="utf-8")
        assert ".complete(" not in source
        assert "LlmGateway" not in source
        assert "count_input_tokens(" in source
        assert source.count("count_input_tokens(") == 1
