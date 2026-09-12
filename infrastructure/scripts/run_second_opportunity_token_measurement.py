"""Mission 1.84.5. ONE provider-native token count of the synthetic maximum output instance.

**What is measured.** The canonical serialization of the largest instance the bounded output
contract `second-opportunity-synthesis-output@1.1.0` admits, rebuilt from the LIVE schema through
the Mission 1.84.4 gate's own builder. It is synthetic by construction: every narrative character is
one fill code point, every id is the all-zero UUID, every slug is a run of `a`. No TED byte, no
research byte, no prompt, no system text and no tool definition is sent.

**What the number is, and what it is not.** The provider documents the count as an ESTIMATE of
INPUT tokens under the tokenizer of the model named. It is not an exact count, and it is not a
measurement of how many OUTPUT tokens the model would spend emitting the same object inside a tool
call. Recording it is the whole job of this script; turning it into an output ceiling is not.

**The properties this script enforces rather than promises.**

* At most ONE request, ever. A receipt on disk refuses a second measurement, and the receipt is
  opened exclusively so two runs cannot both write one.
* Only the count endpoint. A one-shot transport refuses any other URL and any second call, and it
  checks the text at the socket seam: content that is not the synthetic maximum is refused there.
* No retry. A failure is recorded as `TOKEN_MEASUREMENT_FAILED_NO_RETRY` and the process exits.
* The maximum must reproduce Mission 1.84.4's numbers exactly, or nothing is sent
  (`BOUNDED_OUTPUT_MAX_INSTANCE_CHANGED`).
* The credential is read from the process environment, or from the compose file for that ONE key
  only, and is never printed, logged or written. The receipt records header NAMES, never values.
* The default is a dry run, which makes zero requests.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import sys
from typing import Any

from sros_llm_gateway.providers.anthropic import (
    ANTHROPIC_API_VERSION,
    COUNT_TOKENS_ENDPOINT,
    AnthropicProvider,
)
from sros_llm_gateway.transport import UrllibTransport

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
RECEIPT = DATA / "second-opportunity-token-measurement-receipt-v1.json"
COMPOSE_ENV = ROOT / "infrastructure" / "compose" / ".env"

#: The operator's decision in the Mission 1.84.5 brief, not a routing lookup: the count is only
#: meaningful under the tokenizer of the model the bounded synthesis would run on.
MODEL = "claude-sonnet-5"
MEASUREMENT_SURFACE = "POST /v1/messages/count_tokens"
REQUEST_TIMEOUT_SECONDS = 60.0

#: Mission 1.84.4's measured maximum. Rebuilt live and compared, never copied into a request.
EXPECTED_SCHEMA_ID = "second-opportunity-synthesis-output@1.1.0"
EXPECTED_SCHEMA_SHA256 = "ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988"
EXPECTED_CHARACTERS = 309729
EXPECTED_UTF8_BYTES = 309729
EXPECTED_TEXT_SHA256 = "e1a62b812f115b3549b5c3c5b8605f2c8052b998cce5d89ac7b60cee5af71705"

CREDENTIAL_KEY = "ANTHROPIC_API_KEY"


class RefusedError(RuntimeError):
    """A precondition failed. The code names it; nothing was sent unless the code says so."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _load(name: str, path: pathlib.Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RefusedError("DEPENDENCY_NOT_LOADABLE", f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bounded_contract_gate() -> Any:
    """Gate 68. Its builder is the one whose numbers Mission 1.84.4 recorded."""
    return _load("bounded_contract_gate", SCRIPTS / "render_second_opportunity_bounded_contract.py")


def _redact(text: str) -> str:
    """The Mission 1.84.2 redaction, reused so there is one list of credential shapes."""
    runner = _load("second_opportunity_runner", SCRIPTS / "run_second_opportunity_execution.py")
    return str(runner.redact(text))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- the text


def measurement_text(gate: Any) -> tuple[str, dict[str, Any]]:
    """Rebuild the synthetic maximum and refuse unless it is exactly Mission 1.84.4's.

    Section 9: if any value changed, nothing is counted. A different instance would be a different
    measurement, and a number attached to it could not be compared with anything recorded.
    """
    schema = gate.SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1
    instance = gate.maximum_instance(schema, gate.WORST_FILL)
    violations = gate.schema_violations(instance, schema)
    if violations:
        raise RefusedError(
            "BOUNDED_OUTPUT_MAX_INSTANCE_CHANGED",
            f"the rebuilt maximum no longer validates: {violations[:2]}. No request was sent",
        )
    text = gate._canonical(instance)
    facts = {
        "MEASUREMENT_SCHEMA_ID": gate.SECOND_OPPORTUNITY_OUTPUT_SCHEMA_VERSION_V1_1,
        "MEASUREMENT_SCHEMA_SHA256": _sha(gate._canonical(schema)),
        "MEASUREMENT_TEXT_CHARACTERS": len(text),
        "MEASUREMENT_TEXT_UTF8_BYTES": len(text.encode("utf-8")),
        "MEASUREMENT_TEXT_SHA256": _sha(text),
    }
    expected = {
        "MEASUREMENT_SCHEMA_ID": EXPECTED_SCHEMA_ID,
        "MEASUREMENT_SCHEMA_SHA256": EXPECTED_SCHEMA_SHA256,
        "MEASUREMENT_TEXT_CHARACTERS": EXPECTED_CHARACTERS,
        "MEASUREMENT_TEXT_UTF8_BYTES": EXPECTED_UTF8_BYTES,
        "MEASUREMENT_TEXT_SHA256": EXPECTED_TEXT_SHA256,
    }
    changed = {k: (facts[k], expected[k]) for k in expected if facts[k] != expected[k]}
    if changed:
        raise RefusedError(
            "BOUNDED_OUTPUT_MAX_INSTANCE_CHANGED",
            f"the rebuilt maximum differs from Mission 1.84.4's on {sorted(changed)}. "
            "No request was sent",
        )
    return text, facts


# --------------------------------------------------------------------------- the seam


class OneShotTransport:
    """The only transport the measurement uses. Every refusal happens before the socket.

    It refuses a URL other than the count endpoint, a second call, and a body that is not exactly
    the model plus one user message carrying the synthetic maximum. The provider builds that body;
    this checks it at the last point anything could still stop it.
    """

    def __init__(self, inner: Any, *, allowed_url: str, model: str, content_sha256: str) -> None:
        self.inner = inner
        self.allowed_url = allowed_url
        self.model = model
        self.content_sha256 = content_sha256
        self.calls = 0
        self.request_shape: dict[str, Any] | None = None
        self.response: dict[str, Any] | None = None
        self.transport_error: str | None = None

    def post_json(
        self,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
        timeout_seconds: float,
    ) -> Any:
        if url != self.allowed_url:
            raise RefusedError(
                "ONLY_THE_COUNT_TOKENS_ENDPOINT_IS_AUTHORISED",
                f"refused a request to {url!r}. The Messages API is not called in this mission",
            )
        if self.calls >= 1:
            raise RefusedError(
                "TOKEN_COUNT_API_REQUESTS_MAX_IS_ONE", "a second request is never sent"
            )
        _check_body(body, model=self.model, content_sha256=self.content_sha256)
        self.calls += 1
        self.request_shape = {
            "url": url,
            "header_names": sorted(headers),
            "body_keys": sorted(body),
            "model": body["model"],
            "message_count": len(body["messages"]),
            "message_role": body["messages"][0]["role"],
            "content_type": "string",
            "system_sent": "system" in body,
            "tools_sent": "tools" in body,
            "thinking_sent": "thinking" in body,
            "max_tokens_sent": "max_tokens" in body,
            "timeout_seconds": timeout_seconds,
        }
        try:
            response = self.inner.post_json(url, headers, body, timeout_seconds)
        except Exception as exc:
            self.transport_error = f"{type(exc).__name__}: {_redact(str(exc))}"
            raise
        raw = getattr(response, "body", b"")
        text = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
        header = getattr(response, "header", None)
        self.response = {
            "status": getattr(response, "status", None),
            "body": _redact(text),
            "request_id": header("request-id") if callable(header) else None,
        }
        return response


def _check_body(body: dict[str, Any], *, model: str, content_sha256: str) -> None:
    if set(body) != {"model", "messages"}:
        raise RefusedError(
            "COUNT_REQUEST_IS_NOT_THE_SMALLEST_VALID_REQUEST",
            f"the body carries {sorted(body)}; only the model and one user message are sent",
        )
    if body["model"] != model:
        raise RefusedError(
            "COUNT_REQUEST_NAMES_ANOTHER_MODEL", f"{body['model']!r} is not {model!r}"
        )
    messages = body["messages"]
    if (
        not isinstance(messages, list)
        or len(messages) != 1
        or set(messages[0]) != {"role", "content"}
        or messages[0]["role"] != "user"
        or not isinstance(messages[0]["content"], str)
    ):
        raise RefusedError(
            "COUNT_REQUEST_IS_NOT_THE_SMALLEST_VALID_REQUEST",
            "exactly one user message with string content is sent",
        )
    if _sha(messages[0]["content"]) != content_sha256:
        raise RefusedError(
            "MEASUREMENT_TEXT_IS_NOT_THE_SYNTHETIC_MAXIMUM",
            "the only substantive text that may leave is the canonical synthetic maximum",
        )


# --------------------------------------------------------------------------- the credential


def credential_source(env_file: pathlib.Path = COMPOSE_ENV) -> str:
    """Where the key will come from. Returns a LABEL and never the value.

    The compose file is read for this one key only. Loading every line of it would put unrelated
    configuration into the process for no reason, and the other runners' loader does exactly that.
    """
    if os.environ.get(CREDENTIAL_KEY, "").strip():
        return "PRESENT_IN_PROCESS_ENVIRONMENT"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.strip().partition("=")
            if sep and key.strip() == CREDENTIAL_KEY and value.strip():
                os.environ[CREDENTIAL_KEY] = value.strip()
                return "LOADED_FROM_COMPOSE_FILE_ONE_KEY_ONLY"
    return "ABSENT"


# --------------------------------------------------------------------------- the run


def refuse_if_already_measured(receipt_path: pathlib.Path) -> None:
    if receipt_path.exists():
        raise RefusedError(
            "TOKEN_MEASUREMENT_ALREADY_PERFORMED",
            f"{receipt_path.name} exists. The mission authorises one request and it has been made",
        )


def _now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def execute(
    *,
    transport: Any | None = None,
    receipt_path: pathlib.Path = RECEIPT,
    env_file: pathlib.Path = COMPOSE_ENV,
) -> dict[str, Any]:
    """Send the one request and write the receipt. Every refusal before it sends nothing."""
    refuse_if_already_measured(receipt_path)
    text, facts = measurement_text(bounded_contract_gate())
    source = credential_source(env_file)
    if source == "ABSENT":
        raise RefusedError(
            "PROVIDER_CREDENTIAL_ABSENT", f"{CREDENTIAL_KEY} is not configured. No request was sent"
        )

    seam = OneShotTransport(
        transport if transport is not None else UrllibTransport(),
        allowed_url=COUNT_TOKENS_ENDPOINT,
        model=MODEL,
        content_sha256=facts["MEASUREMENT_TEXT_SHA256"],
    )
    provider = AnthropicProvider(transport=seam)

    started = _now()
    tokens: int | None = None
    failure: dict[str, str] | None = None
    try:
        tokens = provider.count_input_tokens(text, MODEL, REQUEST_TIMEOUT_SECONDS)
    except RefusedError:
        raise
    except Exception as exc:  # noqa: BLE001 -- recorded once, never retried
        failure = {"type": type(exc).__name__, "message": _redact(str(exc))}
    finished = _now()

    if seam.calls != 1:
        # Nothing reached the seam, so nothing was sent and no receipt may claim otherwise.
        raise RefusedError(
            "NO_REQUEST_WAS_SENT",
            f"the provider refused before the transport: {failure}",
        )

    receipt = {
        "$comment": (
            "Written once by run_second_opportunity_token_measurement.py. The one request "
            "Mission 1.84.5 authorises. Header VALUES are never recorded, and nothing here was "
            "retried."
        ),
        "record_version": 1,
        "mission": "1.84.5",
        "OUTCOME": "MEASURED" if tokens is not None else "TOKEN_MEASUREMENT_FAILED_NO_RETRY",
        "started_at": started,
        "finished_at": finished,
        "MODEL": MODEL,
        "MEASUREMENT_SURFACE": MEASUREMENT_SURFACE,
        "endpoint": COUNT_TOKENS_ENDPOINT,
        "anthropic_version": ANTHROPIC_API_VERSION,
        "request_shape": seam.request_shape,
        "credential_source": source,
        "credential_value_recorded": False,
        **facts,
        "response": seam.response,
        "transport_error": seam.transport_error,
        "INPUT_TOKENS": tokens,
        "failure": failure,
        "ACCOUNTING": {
            "TOKEN_COUNT_API_REQUESTS": seam.calls,
            "RETRIES": 0,
            "MESSAGES_API_REQUESTS": 0,
            "MODEL_INFERENCE_REQUESTS": 0,
            "TED_BYTES_SENT": 0,
            "RESEARCH_BYTES_SENT": 0,
        },
    }
    with receipt_path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    return receipt


def dry_run(env_file: pathlib.Path = COMPOSE_ENV) -> dict[str, Any]:
    """Everything the request would be, and no request."""
    text, facts = measurement_text(bounded_contract_gate())
    body = AnthropicProvider(api_key="unused-dry-run-placeholder").count_tokens_body(text, MODEL)
    _check_body(body, model=MODEL, content_sha256=facts["MEASUREMENT_TEXT_SHA256"])
    return {
        "mode": "DRY_RUN_ZERO_REQUESTS",
        "endpoint": COUNT_TOKENS_ENDPOINT,
        "model": MODEL,
        "header_names": ["anthropic-version", "x-api-key"],
        "body_keys": sorted(body),
        "credential_available": credential_source(env_file) != "ABSENT",
        **facts,
    }


def main(
    argv: list[str] | None = None,
    *,
    transport: Any | None = None,
    receipt_path: pathlib.Path = RECEIPT,
    env_file: pathlib.Path = COMPOSE_ENV,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--execute",
        action="store_true",
        help="send the ONE count request. Without it, a dry run that sends nothing.",
    )
    args = parser.parse_args(argv)
    try:
        if not args.execute:
            print(json.dumps(dry_run(env_file), indent=2))
            return 0
        receipt = execute(transport=transport, receipt_path=receipt_path, env_file=env_file)
    except RefusedError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"outcome                  {receipt['OUTCOME']}")
    print(f"input tokens (estimate)  {receipt['INPUT_TOKENS']}")
    print(f"requests                 {receipt['ACCOUNTING']['TOKEN_COUNT_API_REQUESTS']}")
    return 0 if receipt["OUTCOME"] == "MEASURED" else 3


if __name__ == "__main__":
    raise SystemExit(main())
