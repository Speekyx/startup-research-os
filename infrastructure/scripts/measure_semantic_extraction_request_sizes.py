"""Mission 1.85.7 (N08-B-PILOT). Exact size of the requests a future DEVELOPMENT pilot run would send.

Reads the held records (DATABASE_URL), renders the surfaces, and for every EGRESS_APPROVED record builds
the exact request body the runner would build -- same prompt, same strict tool, same packet-local index
-- with the offline provider body builder. Nothing is transmitted: no transport is constructed and no
token-counting endpoint is called (that endpoint would send the text). Writes counts only, never text:

    docs/data/semantic-extraction-request-size-development-v1.json

    uv run python infrastructure/scripts/measure_semantic_extraction_request_sizes.py --write
    uv run python infrastructure/scripts/measure_semantic_extraction_request_sizes.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import statistics
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
for path in (
    "packages/semantic-extraction-contract/python",
    "packages/semantic-extraction/python",
    "packages/llm-gateway/python",
    "packages/contracts/python",
    "infrastructure/scripts",
):
    sys.path.insert(0, str(ROOT / path))

from sros_contracts import LlmTier  # noqa: E402
from sros_llm_gateway.providers.anthropic import AnthropicThinking  # noqa: E402
from sros_llm_gateway.providers.anthropic_strict import AnthropicStrictToolProvider  # noqa: E402
from sros_llm_gateway.transport import FakeTransport  # noqa: E402
from sros_semantic_extraction import (  # noqa: E402
    PROMPT_ID,
    PROMPT_VERSION,
    TOOL_ID,
    TOOL_VERSION,
    ExecutionBinding,
    build_extraction_request,
    prompt_sha256,
)
from sros_semantic_extraction_contract import surface_sha256  # noqa: E402

DATA = ROOT / "docs" / "data"
OUT = DATA / "semantic-extraction-request-size-development-v1.json"
PACKET = DATA / "semantic-extraction-evaluation-packet-development-v1.json"
CORPUS = DATA / "stack-overflow-semantic-evaluation-corpus-v1.json"
ELIGIBILITY = DATA / "stack-overflow-semantic-egress-eligibility-development-v1.json"
MAX_OUTPUT_TOKENS = 4096


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values: list[int], q: float) -> int:
    """Nearest-rank percentile: the smallest value with at least q of the values at or below it."""
    ordered = sorted(values)
    rank = max(1, -(-len(ordered) * int(q * 100) // 100))
    return ordered[rank - 1]


def distribution(values: list[int]) -> dict[str, Any]:
    return {
        "min": min(values),
        "median": statistics.median(values),
        "p95_nearest_rank": percentile(values, 0.95),
        "max": max(values),
        "total": sum(values),
    }


def approved_in_run_order() -> list[dict[str, Any]]:
    """The records the runner would call, in the runner's own order (packet selection order)."""
    packet = json.loads(PACKET.read_text("utf-8"))
    approved = set(json.loads(ELIGIBILITY.read_text("utf-8"))["approved_record_ids"])
    return [r for r in packet["selection"]["records"] if r["normalized_record_id"] in approved]


def build(surfaces: dict[str, str]) -> dict[str, Any]:
    packet = json.loads(PACKET.read_text("utf-8"))
    provider = AnthropicStrictToolProvider(
        api_key="measurement-only-never-sent",
        transport=FakeTransport(),
        thinking=AnthropicThinking.DISABLED,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )
    binding = ExecutionBinding(
        packet["packet_id"], "00000000-0000-4000-8000-000000000001", LlmTier.STRONG_MODEL, 240.0
    )
    rows = []
    fixed = None
    for index, record in enumerate(approved_in_run_order()):
        rid = record["normalized_record_id"]
        surface = surfaces[rid]
        if surface_sha256(surface) != record["surface_sha256"]:
            raise SystemExit(f"FAIL     surface {rid} does not match the packet")
        body = provider.build_body(
            build_extraction_request(surface, index, binding), packet["provider"]["model"]
        )
        body_bytes = len(json.dumps(body, ensure_ascii=False).encode("utf-8"))
        rows.append(
            {
                "normalized_record_id": rid,
                "packet_local_index": index,
                "surface_sha256": record["surface_sha256"],
                "surface_characters": len(surface),
                "surface_utf8_bytes": len(surface.encode("utf-8")),
                "request_body_utf8_bytes": body_bytes,
            }
        )
        if fixed is None:
            fixed = {
                "system_json_utf8_bytes": len(
                    json.dumps(body["system"], ensure_ascii=False).encode("utf-8")
                ),
                "tools_json_utf8_bytes": len(
                    json.dumps(body["tools"], ensure_ascii=False).encode("utf-8")
                ),
                "tool_choice_json_utf8_bytes": len(
                    json.dumps(body["tool_choice"], ensure_ascii=False).encode("utf-8")
                ),
            }
    body_overhead = [r["request_body_utf8_bytes"] - r["surface_utf8_bytes"] for r in rows]
    return {
        "$comment": "EXACT REQUEST SIZES for the EGRESS_APPROVED DEVELOPMENT records (Mission 1.85.7). Counts only: no surface text. Each request body was built offline by the same prompt, strict tool and provider body builder the runner uses, with the runner's packet-local index. Nothing was transmitted and no token-counting endpoint was called. Token counts are NOT measured here: Anthropic publishes no local tokenizer, and its token-counting endpoint would transmit the text.",
        "measurement_id": "semantic-extraction-request-size-development",
        "version": "1.0.0",
        "mission": "1.85.7",
        "split": "DEVELOPMENT",
        "eligibility_sha256": sha(ELIGIBILITY),
        "corpus_sha256": sha(CORPUS),
        "prompt": {"id": PROMPT_ID, "version": PROMPT_VERSION, "sha256": prompt_sha256()},
        "tool": {"id": TOOL_ID, "version": TOOL_VERSION},
        "model": packet["provider"]["model"],
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "record_count": len(rows),
        "surface_characters": distribution([r["surface_characters"] for r in rows]),
        "surface_utf8_bytes": distribution([r["surface_utf8_bytes"] for r in rows]),
        "request_body_utf8_bytes": distribution([r["request_body_utf8_bytes"] for r in rows]),
        "fixed_overhead": {
            **(fixed or {}),
            "request_body_bytes_excluding_surface_bytes": distribution(body_overhead),
            "note": "the body excluding the surface's own bytes: system region, task region, untrusted-region framing, JSON escaping of the surface, the strict tool definition and tool_choice",
        },
        "transmitted": False,
        "provider_calls": 0,
        "records": rows,
    }


def dump(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    from build_semantic_egress_eligibility import development_surfaces

    doc = build(development_surfaces())
    if args.write:
        OUT.write_bytes(dump(doc))
        print(
            f"wrote {OUT.name}: {doc['record_count']} records, body bytes {doc['request_body_utf8_bytes']}"
        )
        return 0
    if not OUT.exists() or OUT.read_bytes() != dump(doc):
        print(f"FAIL     {OUT.name} is stale")
        return 1
    print(f"ok       {OUT.name} matches ({doc['record_count']} records)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
