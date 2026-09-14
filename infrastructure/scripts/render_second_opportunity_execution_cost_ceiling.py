"""CI gate 94. Mission 1.84.20. The execution cost ceiling, proven from the provider's own
documentation, and execution packet V7 superseded before it was approved or executed.

    uv run python infrastructure/scripts/render_second_opportunity_execution_cost_ceiling.py --write
    uv run python infrastructure/scripts/render_second_opportunity_execution_cost_ceiling.py --check

Packet V7 recorded `EXECUTION_COST_CEILING = 1.316316`: a body-based input estimate plus all 128000
output tokens at the held price. The same packet recorded that strict tool use makes the provider add
a system prompt whose token count is not documented. The figure therefore bounds nothing, and the
operator refused to approve V7 on that ground. The defect is one of governance and accounting; the
strict-tool architecture is not in question.

This gate re-derives:

* the provider facts, from first-party pages identified by the SHA-256 of the bytes retrieved, each
  fragment quoted verbatim and located by line;
* three cost quantities kept apart: a body-based input estimate, a planning cost, and a hard ceiling
  that rests on a documented upper bound and on nothing estimated or observed;
* every billing category the request could incur, each either inside the ceiling or shown not to
  apply to this request, read against the request body the V7 runner builds;
* the ceiling itself, in exact decimal arithmetic;
* V7's figure reclassified as an estimate, and V7 superseded before execution: never approved, never
  executed, never consumed, its packet untouched, and its runner refusing its digest by name before
  any transport exists.

No provider, token-count or network request is made here.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import pathlib
import sys
from decimal import Decimal
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "infrastructure" / "scripts"
DATA = ROOT / "docs" / "data"
sys.path.insert(0, str(SCRIPTS))

RECORD = DATA / "second-opportunity-execution-cost-ceiling-v1.json"
RECORD_MD = DATA / "second-opportunity-execution-cost-ceiling-v1.md"
SUPERSESSION = DATA / "second-opportunity-synthesis-execution-supersession-v7.json"
PACKET_V7 = DATA / "second-opportunity-synthesis-execution-packet-v7.json"
APPROVAL_V7 = DATA / "second-opportunity-synthesis-execution-approval-v7.json"
RECORD_V7 = DATA / "second-opportunity-synthesis-execution-record-v7.json"
RESPONSE_V7 = DATA / "second-opportunity-synthesis-response-v7.json"
OBSERVED_RECORDS = tuple(
    DATA / f"second-opportunity-synthesis-execution-record-v{n}.json" for n in range(2, 7)
)
CAPABILITY = DATA / "provider-model-capability-register-v1.json"
GATE_93 = SCRIPTS / "render_second_opportunity_execution_packet_v7.py"
RUNNER_V7 = SCRIPTS / "run_second_opportunity_execution_v7.py"

RECORD_VERSION = "second-opportunity-execution-cost-ceiling-record@1.0.0"
SUPERSESSION_VERSION = "second-opportunity-execution-packet-supersession@1.0.0"
MISSION = "1.84.20"
RECORDED_BY = "mission-1.84.20"
RECORDED_ON = "2026-09-14"
MODEL = "claude-sonnet-5"

V7_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V7"
V7_SHA256 = "51023d0d2ed780db4c7d5018a289939e7c9c83061f8768051ef1cd7b8ae674e8"
#: The bytes of packet V7 as Mission 1.84.19 committed them. Superseding V7 edits nothing in it.
V7_PACKET_FILE_SHA256 = "f5fbb440e1188afcb35bd6085d2e7d15691fb7c96cd31ee6851379cada3298f8"
V7_REQUEST_BODY_SHA256 = "58956019f78f414ee11392bee5e99eedda4eb1b4deb20d3f20219dfc60739842"
V7_REQUEST_BODY_CHARACTERS = 31326
V7_COST_NUMBER = "1.316316"
V8_ID = "SECOND-OPPORTUNITY-SYNTH-EXEC-V8"
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
READY = "HARD_EXECUTION_COST_CEILING_ESTABLISHED"
NOT_ESTABLISHED = "TRUE_EXECUTION_COST_CEILING_NOT_ESTABLISHED"

#: The operator's decision that opened this mission, carried as data.
OPERATOR_DECISION = (
    "ACCEPT_THE_PROVIDER_STRICT_ARCHITECTURE_OF_MISSION_1_84_19",
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
    "DO_NOT_APPROVE_V7",
    "V7_EXECUTION_COST_CEILING_PROVEN = false",
    "V7_APPROVAL_AUTHORISED = false",
    "DEFECT_CLASS = GOVERNANCE_ACCOUNTING, NOT_STRICT_TOOL_ARCHITECTURE",
)

#: Three quantities, and the rule that keeps them apart.
TERMINOLOGY = {
    "BODY_BASED_INPUT_TOKEN_ESTIMATE": (
        "an engineering estimate of input tokens from the locally serialised request body"
    ),
    "PLANNING_COST_ESTIMATE": "a non-authoritative estimate, for comparison with earlier runs",
    "HARD_EXECUTION_COST_CEILING": (
        "a value supported by a documented hard upper bound on billable usage, and on nothing "
        "estimated or observed"
    ),
    "ESTIMATE_IS_NOT_A_CEILING": True,
    "rule": (
        "an estimate or a planning cost is never called a ceiling or a worst case; a ceiling is "
        "only what a proof establishes"
    ),
}

#: The first-party pages, each fetched ONCE on 2026-09-14 (UTC) as the published markdown and kept
#: outside the repository. Identified by final URL, retrieval instant and the SHA-256 of the bytes.
#: D04 and D07 are byte-identical to Mission 1.84.19's E01 and E02.
DOCUMENTATION_EVIDENCE: tuple[dict[str, object], ...] = tuple(
    {
        "id": ident,
        "requested_url": f"https://platform.claude.com/docs/en/{path}.md",
        "final_url": f"https://platform.claude.com/docs/en/{path}.md",
        "redirected": False,
        "http_status": 200,
        "retrieved_at": at,
        "bytes": size,
        "sha256": digest,
        "first_party": True,
    }
    for ident, path, at, size, digest in (
        ("D01", "models/overview", "2026-09-14T05:10:43Z", 16851,
         "b2ae292320b5d068b20c426e6e4e0333d1a11e25c8457748ca39de25de283c27"),
        ("D02", "build-with-claude/context-windows", "2026-09-14T05:10:44Z", 15957,
         "e4c7bfac8865c5ad159c66bcc6a2e606ceb6cd922b1c1ceb2e5cf9bff093fcd0"),
        ("D03", "about-claude/pricing", "2026-09-14T05:10:44Z", 45051,
         "d79ad28567196bd55dd50e2fd89341b9da9774a45c1d02fcf387078507fd15e0"),
        ("D04", "build-with-claude/structured-outputs", "2026-09-14T05:10:45Z", 110492,
         "4e500fed30c759764ba06bcd96b9df7160ecb8e5e7611aae9bc229086e0b9204"),
        ("D05", "build-with-claude/prompt-caching", "2026-09-14T05:10:46Z", 157448,
         "89fd9a1e988ae4902de1047706ee788003060cb232e444ad4cf37a11421d42a4"),
        ("D06", "api/messages/create", "2026-09-14T05:10:46Z", 131067,
         "2f5a9f6e527971ee7b91c63c810cbc50b5826bac9c7891e0e522c06b27ff82c2"),
        ("D07", "agents-and-tools/tool-use/strict-tool-use", "2026-09-14T05:10:47Z", 40202,
         "96c6f3246a419d99bad3266755ca942160e56cbbc24fb4c84c0a6bc86eaaed9a"),
        ("D08", "models/sonnet-5/overview", "2026-09-14T05:10:47Z", 13348,
         "6ca17e3121ec558ce10f405145ed9df26ba18bc7ac4cee5d42cc16feefe2bd38"),
        ("D09", "build-with-claude/token-counting", "2026-09-14T05:10:48Z", 43398,
         "05c17f1ab73c1b6e24afe1480b6fe03fdee276444b90b22c1915740793265c06"),
        ("D10", "api/errors", "2026-09-14T05:12:38Z", 28513,
         "0481d4df7934f8415b27cfa59d7669888740975bf0b7818fb003128fb2650d11"),
        ("D11", "api/service-tiers", "2026-09-14T05:12:39Z", 8807,
         "90d1a56809bc7fa1030ac3314b60111e69b767d776b869b50e0414796e9452f2"),
        ("D12", "manage-claude/data-residency", "2026-09-14T05:12:39Z", 14916,
         "8ca6a4088fb762b9856249fb1a72365049c6dbdf5a47335e77c00c938a5d8b76"),
    )
)  # fmt: skip
DOCUMENTATION_FETCHES = {
    "requests": 12,
    "pages": 12,
    "failed": [],
    "third_party_sources": 0,
    "note": (
        "Each page was requested once and its bytes kept for review; every fragment below was "
        "checked against those bytes, on its line, before this record was written. D07 was "
        "reviewed and supplies no cost fact; it is recorded because it was read. No Messages API, "
        "token-count or other provider request was made."
    ),
}

#: The fragments, quoted verbatim, each located by page and line.
DOCUMENTED_PROPOSITIONS: dict[str, tuple[tuple[str, int, str], ...]] = {
    "SONNET_5_CONTEXT_WINDOW": (
        ("D08", 13, "Context window: 1M tokens"),
        ("D02", 36, "Claude Sonnet 5"),
        ("D02", 36, "have a 1M-token context window"),
    ),
    "ONE_MILLION_IS_THE_DEFAULT": (
        (
            "D02",
            38,
            "For every model with a 1M-token context window, 1M is the default: you don't need a "
            "beta header",
        ),
    ),
    "TOKEN_COUNTS_ARE_DECIMAL": (
        ("D02", 111, "<budget:token_budget>200000</budget:token_budget>"),
        (
            "D02",
            114,
            "The budget matches the context window available to your request: 1M tokens for "
            "Claude Sonnet 5",
        ),
        ("D02", 114, "200k tokens for Claude Sonnet 4.5 and Claude Haiku 4.5"),
    ),
    "MAX_OUTPUT_128K": (
        ("D08", 13, "Max output: 128K tokens"),
        (
            "D02",
            36,
            "A single request to any of them can generate up to 128k output tokens (`max_tokens`).",
        ),
    ),
    "MAX_TOKENS_IS_AN_ABSOLUTE_MAXIMUM": (
        (
            "D06",
            30,
            "This parameter only specifies the absolute maximum number of tokens to generate.",
        ),
    ),
    "THE_WINDOW_HOLDS_EVERYTHING_THE_MODEL_READS": (
        (
            "D02",
            11,
            'The "context window" refers to all the text a language model can reference when '
            "generating a response, including the response itself.",
        ),
    ),
    "EVERYTHING_IN_THE_REQUEST_COUNTS": (
        (
            "D02",
            32,
            "Everything in the request counts toward the context window: the system prompt, every "
            "message in `messages` (including tool results, images, and documents), and your tool "
            "definitions.",
        ),
        (
            "D02",
            32,
            "the input count is split across `input_tokens`, `cache_read_input_tokens`, and "
            "`cache_creation_input_tokens`, and all three count toward the window.",
        ),
    ),
    "INPUT_OVER_THE_WINDOW_IS_REFUSED": (
        (
            "D02",
            145,
            "If the input alone already exceeds the model's context window, the API returns a 400 "
            '`invalid_request_error` ("prompt is too long") on every model.',
        ),
    ),
    "GENERATION_STOPS_AT_THE_WINDOW": (
        (
            "D02",
            147,
            "If generation then reaches the context window limit, it stops with "
            '`stop_reason: "model_context_window_exceeded"`.',
        ),
    ),
    "STRICT_INJECTS_A_SYSTEM_PROMPT": (
        (
            "D04",
            2808,
            "When using structured outputs, Claude automatically receives an additional system "
            "prompt explaining the expected output format.",
        ),
        ("D04", 2810, "Your input token count is slightly higher"),
        ("D04", 2811, "The injected prompt costs you tokens like any other system prompt"),
    ),
    "STRICT_TOOL_USE_IS_A_STRUCTURED_OUTPUT": (
        (
            "D04",
            16,
            "**Strict tool use** (`strict: true`): Guarantee schema validation on tool names and "
            "inputs",
        ),
        ("D04", 2816, "Both JSON outputs and strict tool use share these limitations."),
    ),
    "SYSTEM_ADDED_TOKENS_NOT_BILLED": (
        (
            "D09",
            28,
            "Token counts may include tokens added automatically by Anthropic for system "
            "optimizations.",
        ),
        (
            "D09",
            28,
            "**You are not billed for system-added tokens**. Billing reflects only your content.",
        ),
    ),
    "CONTEXT_AWARENESS_IS_INJECTED": (
        (
            "D02",
            104,
            "Claude Sonnet 5, Claude Sonnet 4.6, Claude Sonnet 4.5, and Claude Haiku 4.5 have "
            "**context awareness:**",
        ),
        (
            "D02",
            108,
            "In the system prompt of every request, the API gives Claude its total context window:",
        ),
    ),
    "TOOL_USE_SYSTEM_PROMPT": (
        (
            "D03",
            230,
            "When you use `tools`, the API also automatically includes a special system prompt for "
            "the model that enables tool use.",
        ),
        ("D03", 241, "Claude Sonnet 5"),
        ("D03", 241, "354 tokens***474 tokens"),
        (
            "D03",
            248,
            "These token counts are added to your normal input and output tokens to calculate the "
            "total cost of a request.",
        ),
    ),
    "TOOL_USE_PRICING_BASIS": (
        (
            "D03",
            218,
            "The total number of input tokens sent to the model (including in the `tools` "
            "parameter)",
        ),
        ("D03", 219, "The number of output tokens generated"),
        (
            "D03",
            220,
            "For server-side tools, additional usage-based pricing (for example, web search "
            "charges per search performed)",
        ),
        ("D03", 222, "Client-side tools are priced the same as any other Claude API request"),
    ),
    "SONNET_5_BASE_PRICE": (
        ("D08", 56, "$2 / MTok"),
        ("D08", 57, "$10 / MTok"),
        ("D03", 28, "Claude Sonnet 5"),
        ("D03", 28, "$2 / MTok"),
        ("D03", 28, "$10 / MTok"),
    ),
    "THE_PRICE_IS_STANDARD": (
        ("D03", 38, "The $2/$10 per million input/output token pricing for Claude Sonnet 5"),
        ("D03", 38, "is now the standard price."),
        ("D03", 38, "will not occur."),
    ),
    "FULL_PRICE_LIST": (("D08", 62, "Full price list"),),
    "NO_LONG_CONTEXT_PREMIUM": (
        ("D02", 38, "long-context requests are billed at [standard pricing]"),
        (
            "D03",
            212,
            "(A 900k-token request is billed at the same per-token rate as a 9k-token request.)",
        ),
    ),
    "CACHING_IS_ENABLED_BY_CACHE_CONTROL": (
        ("D05", 13, "There are two ways to enable prompt caching:"),
        ("D05", 15, "Add a single `cache_control` field at the top level of your request."),
        ("D03", 141, "Place `cache_control` directly on individual content blocks"),
    ),
    "CACHE_WRITE_RATES": (
        ("D03", 147, "1.25x base input price"),
        ("D03", 148, "2x base input price"),
    ),
    "INFERENCE_GEO_DEFAULTS_TO_THE_WORKSPACE": (
        ("D06", 1194, "If not specified, the workspace's `default_inference_geo` is used."),
        ("D12", 237, "Sets the fallback geo when `inference_geo` is omitted from a request."),
        ("D12", 277, '`default_inference_geo: "us"`'),
    ),
    "INFERENCE_GEO_VALUES": (
        ("D12", 307, '**Inference geo:** Only `"us"` and `"global"` are available.'),
    ),
    "US_ONLY_INFERENCE_MULTIPLIER": (
        (
            "D03",
            159,
            "specifying US-only inference through the `inference_geo` parameter incurs a 1.1x "
            "multiplier on all token pricing categories, including input tokens, output tokens, "
            "cache writes, and cache reads.",
        ),
    ),
    "PRIORITY_TIER_NOT_ON_SONNET_5": (
        ("D11", 230, "Priority Tier is supported on all available Claude models except"),
        ("D11", 230, "Claude Opus 5, and Claude Sonnet 5."),
        (
            "D11",
            185,
            "Uses the Priority Tier capacity if available, falling back to your other capacity if "
            "not",
        ),
    ),
    "FAST_MODE_MODELS": (
        (
            "D03",
            167,
            "provides significantly faster output for Claude Opus 5 and Claude Opus 4.8 at premium "
            "pricing",
        ),
    ),
    "BATCH_IS_ANOTHER_ROUTE": (
        (
            "D03",
            186,
            "The Batch API allows asynchronous processing of large volumes of requests with a 50% "
            "discount on both input and output tokens.",
        ),
    ),
    "THINKING_IS_OUTPUT_INSIDE_MAX_TOKENS": (
        (
            "D02",
            48,
            "Thinking tokens are a subset of your `max_tokens` parameter, are billed as output "
            "tokens",
        ),
    ),
    "STRICT_COSTS_ARE_TOKENS": (
        ("D04", 2806, "### Prompt modification and token costs"),
        ("D04", 2792, "### Grammar compilation and caching"),
    ),
    "GRAMMAR_COMPILATION": (
        (
            "D04",
            2796,
            "**First request latency:** The first time you use a specific schema, there is "
            "additional latency while the grammar compiles",
        ),
        (
            "D04",
            2798,
            "**Automatic caching:** Compiled grammars are cached for 24 hours from last use",
        ),
        ("D04", 2960, "the API also enforces a **compilation timeout of 180 seconds**"),
    ),
    "A_REFUSED_REQUEST": (
        (
            "D10",
            11,
            "400 - `invalid_request_error`: There was an issue with the format or content of your "
            "request.",
        ),
    ),
}

#: What the propositions establish. Every value rests on named propositions and on nothing else.
PROVIDER_FACTS: dict[str, dict[str, object]] = {
    "MODEL_CONTEXT_WINDOW_TOKENS": {
        "value": 1_000_000,
        "documented_form": "1M tokens",
        "rests_on": [
            "SONNET_5_CONTEXT_WINDOW",
            "ONE_MILLION_IS_THE_DEFAULT",
            "TOKEN_COUNTS_ARE_DECIMAL",
        ],
        "note": (
            "claude-sonnet-5's window is 1M tokens by default, with no beta header. The pages count "
            "tokens in decimal: the 200k window is given to the model as 200000, so 1M is read as "
            "1000000"
        ),
    },
    "MAX_OUTPUT_TOKENS": {
        "value": 128_000,
        "rests_on": ["MAX_OUTPUT_128K", "MAX_TOKENS_IS_AN_ABSOLUTE_MAXIMUM"],
        "note": "max_tokens is an absolute maximum, and 128000 is the synchronous limit",
    },
    "THE_WINDOW_CONTAINS_ALL_INPUT": {
        "value": True,
        "rests_on": [
            "THE_WINDOW_HOLDS_EVERYTHING_THE_MODEL_READS",
            "EVERYTHING_IN_THE_REQUEST_COUNTS",
        ],
        "note": (
            "the system prompt, every message and the tool definitions count, and the three input "
            "fields of usage all count toward the window"
        ),
    },
    "INPUT_OVER_THE_WINDOW": {
        "value": "REFUSED_WITH_A_400_BEFORE_GENERATION",
        "rests_on": ["INPUT_OVER_THE_WINDOW_IS_REFUSED", "A_REFUSED_REQUEST"],
    },
    "STRICT_INTERNAL_PROMPT_TOKENS": {
        "value": "NOT_ESTABLISHED",
        "rests_on": ["STRICT_INJECTS_A_SYSTEM_PROMPT"],
        "note": "the provider documents that the prompt exists and is billed, and not its size",
    },
    "STRICT_INTERNAL_PROMPT_INCLUDED_IN_CONTEXT_BOUND": {
        "value": True,
        "rests_on": [
            "STRICT_INJECTS_A_SYSTEM_PROMPT",
            "STRICT_TOOL_USE_IS_A_STRUCTURED_OUTPUT",
            "THE_WINDOW_HOLDS_EVERYTHING_THE_MODEL_READS",
            "EVERYTHING_IN_THE_REQUEST_COUNTS",
        ],
        "note": (
            "strict tool use is a structured-outputs feature; Claude receives the injected prompt, "
            "which raises the input token count; every input token field counts toward the window, "
            "and the window is all the text the model can reference. Whatever its size, it is "
            "inside the 1M bound"
        ),
    },
    "STRICT_INTERNAL_PROMPT_INCLUDED_IN_BILLABLE_USAGE": {
        "value": True,
        "rests_on": ["STRICT_INJECTS_A_SYSTEM_PROMPT"],
        "tension": {
            "with": "SYSTEM_ADDED_TOKENS_NOT_BILLED",
            "resolution": (
                "the token-counting page says system-added tokens are not billed; the "
                "structured-outputs page says the injected prompt costs tokens like any other "
                "system prompt. The ceiling takes the dearer reading, and holds under either, "
                "because billed or not those tokens are inside the window"
            ),
        },
    },
    "MAX_BILLABLE_INPUT_TOKENS": {
        "value": 1_000_000,
        "basis": "DOCUMENTED_MODEL_CONTEXT_WINDOW",
        "rests_on": [
            "SONNET_5_CONTEXT_WINDOW",
            "THE_WINDOW_HOLDS_EVERYTHING_THE_MODEL_READS",
            "EVERYTHING_IN_THE_REQUEST_COUNTS",
            "INPUT_OVER_THE_WINDOW_IS_REFUSED",
        ],
        "note": (
            "every input the request could be billed for, the provider's own additions included, "
            "counts toward a 1M window that input alone may not exceed. The output is not "
            "subtracted from it, which makes the bound larger than it needs to be and never smaller"
        ),
    },
    "CACHE_BILLING_APPLICABLE": {
        "value": False,
        "rests_on": ["CACHING_IS_ENABLED_BY_CACHE_CONTROL"],
        "request_selector": "cache_control",
        "note": "caching is enabled only by cache_control, and the request carries none",
    },
    "LONG_CONTEXT_PREMIUM_APPLICABLE": {
        "value": False,
        "rests_on": ["NO_LONG_CONTEXT_PREMIUM", "ONE_MILLION_IS_THE_DEFAULT"],
    },
    "DATA_RESIDENCY_MULTIPLIER": {
        "value": "1.1",
        "applied_to_the_ceiling": True,
        "rests_on": [
            "INFERENCE_GEO_DEFAULTS_TO_THE_WORKSPACE",
            "INFERENCE_GEO_VALUES",
            "US_ONLY_INFERENCE_MULTIPLIER",
        ],
        "request_selector": "inference_geo",
        "note": (
            "the request sets no inference_geo, so the workspace's default decides, and that setting "
            "is not visible from this repository. Only us and global exist, and us costs 1.1x on "
            "every token category, so the ceiling takes 1.1"
        ),
    },
    "PRIORITY_TIER_APPLICABLE": {
        "value": False,
        "rests_on": ["PRIORITY_TIER_NOT_ON_SONNET_5"],
        "note": "service_tier defaults to auto, and claude-sonnet-5 is excluded from Priority Tier",
    },
    "PRICE_USD_PER_MTOK": {
        "value": {"input": 2, "output": 10},
        "rests_on": ["SONNET_5_BASE_PRICE", "THE_PRICE_IS_STANDARD"],
        "note": "the standard price; the increase once scheduled for 2026-09-01 will not occur",
    },
    "FIRST_REQUEST_GRAMMAR_COMPILATION_LATENCY": {
        "value": "NOT_ESTABLISHED",
        "rests_on": ["GRAMMAR_COMPILATION"],
    },
    "PROVIDER_COMPILATION_TIMEOUT_SECONDS": {
        "value": 180,
        "rests_on": ["GRAMMAR_COMPILATION"],
    },
}

INSIDE_INPUT = "INSIDE_THE_INPUT_BOUND"
INSIDE_OUTPUT = "INSIDE_THE_OUTPUT_BOUND"
MULTIPLIER = "INCLUDED_AS_A_MULTIPLIER"
NOT_APPLICABLE = "NOT_APPLICABLE_TO_THIS_REQUEST"
NOT_PUBLISHED = "NOT_A_PUBLISHED_CHARGE"
UNBOUNDED = "UNBOUNDED"
ACCOUNTED = (INSIDE_INPUT, INSIDE_OUTPUT, MULTIPLIER, NOT_APPLICABLE, NOT_PUBLISHED)

#: Every billing category the request could incur, and what happens to it.
COST_CATEGORIES: tuple[dict[str, object], ...] = (
    {
        "category": "BASE_INPUT_TOKENS",
        "disposition": INSIDE_INPUT,
        "rests_on": ["SONNET_5_BASE_PRICE", "EVERYTHING_IN_THE_REQUEST_COUNTS"],
    },
    {
        "category": "TOOL_DEFINITIONS",
        "disposition": INSIDE_INPUT,
        "rests_on": ["TOOL_USE_PRICING_BASIS", "EVERYTHING_IN_THE_REQUEST_COUNTS"],
    },
    {
        "category": "TOOL_USE_SYSTEM_PROMPT",
        "disposition": INSIDE_INPUT,
        "rests_on": ["TOOL_USE_SYSTEM_PROMPT"],
        "note": "474 tokens under a forced tool choice",
    },
    {
        "category": "STRICT_FORMAT_SYSTEM_PROMPT",
        "disposition": INSIDE_INPUT,
        "rests_on": [
            "STRICT_INJECTS_A_SYSTEM_PROMPT",
            "THE_WINDOW_HOLDS_EVERYTHING_THE_MODEL_READS",
        ],
        "note": "its count is NOT_ESTABLISHED, and it is inside the window whatever it is",
    },
    {
        "category": "CONTEXT_AWARENESS_TAGS",
        "disposition": INSIDE_INPUT,
        "rests_on": ["CONTEXT_AWARENESS_IS_INJECTED", "SYSTEM_ADDED_TOKENS_NOT_BILLED"],
    },
    {
        "category": "OUTPUT_TOKENS",
        "disposition": INSIDE_OUTPUT,
        "rests_on": ["MAX_OUTPUT_128K", "MAX_TOKENS_IS_AN_ABSOLUTE_MAXIMUM", "SONNET_5_BASE_PRICE"],
    },
    {
        "category": "THINKING_TOKENS",
        "disposition": INSIDE_OUTPUT,
        "rests_on": ["THINKING_IS_OUTPUT_INSIDE_MAX_TOKENS"],
        "note": "thinking is disabled, and would be output inside max_tokens if it were not",
    },
    {
        "category": "PROMPT_CACHE_WRITE_5M",
        "disposition": NOT_APPLICABLE,
        "rests_on": ["CACHING_IS_ENABLED_BY_CACHE_CONTROL", "CACHE_WRITE_RATES"],
        "request_selector": "cache_control",
    },
    {
        "category": "PROMPT_CACHE_WRITE_1H",
        "disposition": NOT_APPLICABLE,
        "rests_on": ["CACHING_IS_ENABLED_BY_CACHE_CONTROL", "CACHE_WRITE_RATES"],
        "request_selector": "cache_control",
    },
    {
        "category": "PROMPT_CACHE_READ",
        "disposition": NOT_APPLICABLE,
        "rests_on": ["CACHING_IS_ENABLED_BY_CACHE_CONTROL"],
        "request_selector": "cache_control",
    },
    {
        "category": "LONG_CONTEXT_PREMIUM",
        "disposition": NOT_APPLICABLE,
        "rests_on": ["NO_LONG_CONTEXT_PREMIUM"],
    },
    {
        "category": "DATA_RESIDENCY_US_ONLY",
        "disposition": MULTIPLIER,
        "rests_on": [
            "INFERENCE_GEO_DEFAULTS_TO_THE_WORKSPACE",
            "INFERENCE_GEO_VALUES",
            "US_ONLY_INFERENCE_MULTIPLIER",
        ],
        "request_selector": "inference_geo",
        "note": "1.1 on every token category, because the workspace default is not established",
    },
    {
        "category": "PRIORITY_TIER",
        "disposition": NOT_APPLICABLE,
        "rests_on": ["PRIORITY_TIER_NOT_ON_SONNET_5"],
        "request_selector": "service_tier",
    },
    {
        "category": "BATCH_PRICING",
        "disposition": NOT_APPLICABLE,
        "rests_on": ["BATCH_IS_ANOTHER_ROUTE"],
        "note": "another route, and a discount",
    },
    {
        "category": "FAST_MODE_PREMIUM",
        "disposition": NOT_APPLICABLE,
        "rests_on": ["FAST_MODE_MODELS"],
        "request_selector": "speed",
    },
    {
        "category": "SERVER_TOOL_USAGE_FEES",
        "disposition": NOT_APPLICABLE,
        "rests_on": ["TOOL_USE_PRICING_BASIS"],
        "request_selector": "server_tools",
    },
    {
        "category": "STRICT_SCHEMA_COMPILATION_FEE",
        "disposition": NOT_PUBLISHED,
        "rests_on": ["FULL_PRICE_LIST", "STRICT_COSTS_ARE_TOKENS"],
        "note": (
            "the full price list names no such charge, and the structured-outputs page's own "
            "section on token costs names only the injected prompt's input tokens"
        ),
    },
    {
        "category": "REQUEST_REFUSED_FOR_LENGTH",
        "disposition": NOT_PUBLISHED,
        "rests_on": ["INPUT_OVER_THE_WINDOW_IS_REFUSED", "A_REFUSED_REQUEST"],
        "note": "refused with a 400 before generation; the price list publishes no charge for it",
    },
)
REQUIRED_CATEGORIES = tuple(str(row["category"]) for row in COST_CATEGORIES)

#: What the request body must say for each selector-dependent disposition to hold.
SELECTORS_REQUIRED = {
    "cache_control": False,
    "inference_geo": "ABSENT",
    "service_tier": "ABSENT",
    "speed": "ABSENT",
    "server_tools": 0,
}

CHARS_PER_TOKEN = 2.1565
CONSERVATIVE_MULTIPLIER = 1.25


class ValidationError(RuntimeError):
    """The cost record, the supersession or the V7 guard disagrees with what the code derives."""


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


def decimal_text(value: Decimal) -> str:
    """An exact decimal, written without trailing zeros."""
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def tokens_from_form(form: str) -> int:
    """`1M tokens` -> 1000000, `128K tokens` -> 128000: the pages' own decimal convention."""
    number = form.split()[0]
    scale = {"K": 1_000, "M": 1_000_000}[number[-1].upper()]
    return int(Decimal(number[:-1]) * scale)


def gate_93() -> Any:
    return _module("gate_93_for_gate_94", GATE_93)


def runner_v7() -> Any:
    return _module("runner_v7_for_gate_94", RUNNER_V7)


# ------------------------------------------------------------------------------ derivation


def v7_body() -> dict[str, Any]:
    """V7's request body, built through the V7 runner over the authenticated snapshot, never sent."""
    g93 = gate_93()
    _snap, parts, _ = g93.snapshot()
    return g93.runner().request_body(parts, _load(PACKET_V7))


def billing_selectors(body: dict[str, Any]) -> dict[str, object]:
    """What in the body could select a billing category."""
    wire = json.dumps(body)
    tools = body.get("tools") or []
    return {
        "cache_control": "cache_control" in wire,
        "inference_geo": body.get("inference_geo", "ABSENT"),
        "service_tier": body.get("service_tier", "ABSENT"),
        "speed": body.get("speed", "ABSENT"),
        "server_tools": sum(1 for tool in tools if "type" in tool),
        "tools": len(tools),
        "model": body.get("model"),
        "max_tokens": body.get("max_tokens"),
        "thinking": body.get("thinking"),
        "body_characters": len(wire),
        "body_sha256": _sha(wire),
    }


def observed_usage() -> dict[str, dict[str, int]]:
    """V2's to V6's actual usage, kept only so the ceiling can be shown not to rest on it."""
    out: dict[str, dict[str, int]] = {}
    for path in OBSERVED_RECORDS:
        usage = _load(path).get("ACTUAL_USAGE") or {}
        out[path.stem.rsplit("-", 1)[-1].upper()] = {
            key: int(usage[key]) for key in ("input_tokens", "output_tokens") if key in usage
        }
    return out


def cost_block(v7: dict[str, Any], selectors: dict[str, object]) -> dict[str, object]:
    """The estimate, the planning cost and the hard ceiling, each by its own method."""
    price = v7["PRICE_PER_1K"]
    in_price, out_price = Decimal(str(price["input"])), Decimal(str(price["output"]))
    wire = int(str(selectors["body_characters"]))
    estimate = math.ceil(wire / CHARS_PER_TOKEN * CONSERVATIVE_MULTIPLIER)
    window = int(str(PROVIDER_FACTS["MAX_BILLABLE_INPUT_TOKENS"]["value"]))
    output = int(str(PROVIDER_FACTS["MAX_OUTPUT_TOKENS"]["value"]))
    multiplier = Decimal(str(PROVIDER_FACTS["DATA_RESIDENCY_MULTIPLIER"]["value"]))
    thousand = Decimal(1000)
    planning_input = Decimal(estimate) / thousand * in_price
    output_base = Decimal(output) / thousand * out_price
    input_base = Decimal(window) / thousand * in_price
    hard_input = input_base * multiplier
    hard_output = output_base * multiplier
    return {
        "REQUEST_BODY_CHARACTERS": wire,
        "BODY_BASED_INPUT_TOKEN_ESTIMATE": estimate,
        "BODY_BASED_INPUT_TOKEN_ESTIMATE_METHOD": (
            f"ceil({wire} / {CHARS_PER_TOKEN} x {CONSERVATIVE_MULTIPLIER}), the held ratio over "
            "the serialised body"
        ),
        "BODY_BASED_ESTIMATE_COVERS_THE_STRICT_PROMPT": False,
        "PLANNING_INPUT_COST_ESTIMATE": decimal_text(planning_input),
        "PLANNING_COST_ESTIMATE": decimal_text(planning_input + output_base),
        "PLANNING_COST_ESTIMATE_METHOD": (
            "the body-based input estimate and all 128000 output tokens at the held base price"
        ),
        "PLANNING_COST_ESTIMATE_CLASSIFICATION": "PLANNING_ESTIMATE",
        "PLANNING_COST_ESTIMATE_IS_NOT": ["WORST_CASE", "CEILING"],
        "OUTPUT_TOKEN_HARD_MAXIMUM": output,
        "OUTPUT_HARD_COST_COMPONENT_AT_BASE_PRICE": decimal_text(output_base),
        "MAX_BILLABLE_INPUT_TOKENS": window,
        "MAX_BILLABLE_INPUT_TOKENS_BASIS": "DOCUMENTED_MODEL_CONTEXT_WINDOW",
        "INPUT_HARD_COST_COMPONENT_AT_BASE_PRICE": decimal_text(input_base),
        "DATA_RESIDENCY_MULTIPLIER": decimal_text(multiplier),
        "HARD_INPUT_COST_CEILING": decimal_text(hard_input),
        "HARD_OUTPUT_COST_CEILING": decimal_text(hard_output),
        "HARD_EXECUTION_COST_CEILING": decimal_text(hard_input + hard_output),
        "HARD_EXECUTION_COST_CEILING_PROVEN": True,
        "UNKNOWN_COST_CATEGORIES": [
            str(row["category"]) for row in COST_CATEGORIES if row["disposition"] == UNBOUNDED
        ],
        "PRICING_VERSION": v7["PRICING_VERSION"],
        "PRICE_PER_1K": dict(price),
        "PRICING_SOURCE": (
            "the deployment's configured pricing table, corroborated by D03 line 28 and D08 lines "
            "56 and 57, retrieved 2026-09-14: 2 and 10 USD per million tokens, the standard price"
        ),
        "COST_UNIT_NOTE": (
            "cost units are provider-agnostic by ADR-006, and the held table's are USD at this "
            "tariff. The ceiling is in the units the budget ledger compares"
        ),
    }


def derivation(block: dict[str, Any]) -> dict[str, object]:
    window, output = block["MAX_BILLABLE_INPUT_TOKENS"], block["OUTPUT_TOKEN_HARD_MAXIMUM"]
    price, multiplier = block["PRICE_PER_1K"], block["DATA_RESIDENCY_MULTIPLIER"]
    return {
        "method": (
            "MAX_BILLABLE_INPUT_TOKENS at the held input price plus the output hard maximum at the "
            "held output price, both times the data-residency multiplier, in exact decimal "
            "arithmetic"
        ),
        "input_side": (
            f"{window} / 1000 x {price['input']} x {multiplier} = {block['HARD_INPUT_COST_CEILING']}"
        ),
        "output_side": (
            f"{output} / 1000 x {price['output']} x {multiplier} = "
            f"{block['HARD_OUTPUT_COST_CEILING']}"
        ),
        "total": (
            f"{block['HARD_INPUT_COST_CEILING']} + {block['HARD_OUTPUT_COST_CEILING']} = "
            f"{block['HARD_EXECUTION_COST_CEILING']}"
        ),
        "output_subtracted_from_the_input_bound": False,
        "rests_on_facts": [
            "MAX_BILLABLE_INPUT_TOKENS",
            "MAX_OUTPUT_TOKENS",
            "DATA_RESIDENCY_MULTIPLIER",
            "PRICE_USD_PER_MTOK",
        ],
        "not_derived_from": [
            "BODY_BASED_INPUT_TOKEN_ESTIMATE",
            "PLANNING_COST_ESTIMATE",
            "V7_EXECUTION_COST_CEILING",
            "V2_TO_V6_OBSERVED_USAGE",
        ],
    }


def v7_reconfirmation(v7: dict[str, Any], selectors: dict[str, object]) -> dict[str, object]:
    """V7's figures, recomputed from its committed packet and its rebuilt body."""
    basis = v7["TOKEN_ESTIMATION_BASIS"]
    return {
        "EXECUTION_PACKET_ID": v7["EXECUTION_PACKET_ID"],
        "EXECUTION_PACKET_VERSION": v7["EXECUTION_PACKET_VERSION"],
        "EXECUTION_PACKET_SHA256_RECOMPUTED": gate_93().packet_digest(v7),
        "EXECUTION_PACKET_FILE_SHA256": file_sha(PACKET_V7),
        "approval_recorded": v7["OPERATOR_EXECUTION_APPROVAL_RECORDED"],
        "approval_file_exists": APPROVAL_V7.exists(),
        "execution_record_exists": RECORD_V7.exists(),
        "response_artifact_exists": RESPONSE_V7.exists(),
        "provider_strict_mode": v7["PROVIDER_STRICT_MODE"],
        "request_body_characters": selectors["body_characters"],
        "request_body_sha256": selectors["body_sha256"],
        "body_based_input_token_estimate": v7["INPUT_TOKEN_ESTIMATE"],
        "output_token_ceiling": v7["OUTPUT_TOKEN_CEILING"],
        "input_cost_called_worst_case": v7["INPUT_WORST_CASE_COST"],
        "output_worst_case_cost": v7["OUTPUT_WORST_CASE_COST"],
        "packet_execution_cost_ceiling": v7["EXECUTION_COST_CEILING"],
        "strict_mode_injected_system_prompt_tokens": basis["strict_format_prompt_tokens"],
    }


def build_record() -> dict[str, Any]:
    v7 = _load(PACKET_V7)
    selectors = billing_selectors(v7_body())
    block = cost_block(v7, selectors)
    return {
        "$comment": (
            "Mission 1.84.20. What one execution of the second-Opportunity synthesis can cost at "
            "most, proven from the provider's own documentation, kept apart from what it is "
            "expected to cost; and V7's figure reclassified. Re-derived by CI gate 94."
        ),
        "record_version": RECORD_VERSION,
        "mission": MISSION,
        "recorded_by": RECORDED_BY,
        "recorded_on": RECORDED_ON,
        "PRIMARY_OUTCOME": READY
        if block["HARD_EXECUTION_COST_CEILING_PROVEN"]
        else NOT_ESTABLISHED,
        "OPERATOR_DECISION": list(OPERATOR_DECISION),
        "TERMINOLOGY": TERMINOLOGY,
        "DEFECT": {
            "class": "GOVERNANCE_ACCOUNTING",
            "not": "STRICT_TOOL_ARCHITECTURE",
            "not_a_provider_billing_error": True,
            "statement": (
                "V7 called BODY_BASED_INPUT_ESTIMATE + MAX_OUTPUT_TOKEN_COST its "
                "EXECUTION_COST_CEILING while recording that strict mode adds provider-side input "
                "whose count is NOT_ESTABLISHED. That establishes neither ACTUAL_BILLABLE_INPUT_TOKENS "
                "<= 18158 nor ACTUAL_CALL_COST <= 1.316316"
            ),
        },
        "V7_COST_RECONFIRMATION": v7_reconfirmation(v7, selectors),
        "V7_COST_NUMBER_CLASSIFICATION": "ESTIMATE_NOT_PROVEN_HARD_CEILING",
        "V7_EXECUTION_COST_CEILING_PROVEN": False,
        "V7_APPROVAL_AUTHORISED": False,
        "DOCUMENTATION_EVIDENCE": [dict(row) for row in DOCUMENTATION_EVIDENCE],
        "DOCUMENTATION_FETCHES": DOCUMENTATION_FETCHES,
        "DOCUMENTED_PROPOSITIONS": {
            name: [{"evidence": e, "line": line, "verbatim": text} for e, line, text in fragments]
            for name, fragments in DOCUMENTED_PROPOSITIONS.items()
        },
        "PROVIDER_FACTS": PROVIDER_FACTS,
        "REQUEST_BODY_BILLING_SELECTORS": selectors,
        "COST_CATEGORIES": [dict(row) for row in COST_CATEGORIES],
        "COST_RECORD": block,
        "HARD_CEILING_DERIVATION": derivation(block),
        "OBSERVED_USAGE_NOT_USED": {
            "usage": observed_usage(),
            "USED_FOR_THE_HARD_CEILING": False,
            "USED_FOR_THE_PLANNING_ESTIMATE": False,
            "note": (
                "five completed calls are five observations. None of them bounds the next one, and "
                "none enters either number"
            ),
        },
        "STRICT_FIRST_REQUEST_TIMEOUT": {
            "REQUEST_TIMEOUT_SECONDS": v7["REQUEST_TIMEOUT"],
            "TIMEOUT_CHANGED": False,
            "FIRST_REQUEST_GRAMMAR_COMPILATION_LATENCY": "NOT_ESTABLISHED",
            "PROVIDER_COMPILATION_TIMEOUT_SECONDS": PROVIDER_FACTS[
                "PROVIDER_COMPILATION_TIMEOUT_SECONDS"
            ]["value"],
            "STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8": False,
            "note": (
                "an availability risk, apart from the semantic one: the first request with this "
                "schema compiles a grammar for an undocumented time the provider limits at 180 "
                "seconds, and the one approved attempt, with no retry, times out at 60"
            ),
        },
        "ACCOUNTING": {
            "MODEL_CALLS": 0,
            "PROVIDER_REQUESTS": 0,
            "MESSAGES_API_REQUESTS": 0,
            "TOKEN_COUNT_API_REQUESTS": 0,
            "TED_BYTES_SENT": 0,
            "CANONICAL_MUTATIONS": 0,
            "DOCUMENTATION_REQUESTS": DOCUMENTATION_FETCHES["requests"],
        },
    }


def build_supersession(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "$comment": (
            "Mission 1.84.20. Execution packet V7 superseded before it was approved or executed. "
            "The packet is left exactly as Mission 1.84.19 froze it; the V7 runner reads this "
            "record and refuses the digest it names, by name, before any transport exists."
        ),
        "record_version": SUPERSESSION_VERSION,
        "recorded_by": RECORDED_BY,
        "recorded_on": RECORDED_ON,
        "SUPERSEDED_EXECUTION_PACKET_ID": V7_ID,
        "SUPERSEDED_EXECUTION_PACKET_VERSION": 7,
        "SUPERSEDED_EXECUTION_PACKET_SHA256": V7_SHA256,
        "SUPERSEDED_EXECUTION_PACKET_FILE_SHA256": V7_PACKET_FILE_SHA256,
        "STATUS": "SUPERSEDED_BEFORE_EXECUTION",
        "REASON": "COST_CEILING_SEMANTICS_NOT_PROVEN",
        "V7_EXECUTED": False,
        "V7_APPROVED": False,
        "V7_APPROVAL_CONSUMED": False,
        "V7_PROVIDER_REQUESTS": 0,
        "V7_MODEL_CALLS": 0,
        "V7_PACKET_MODIFIED": False,
        "V7_COST_NUMBER": V7_COST_NUMBER,
        "V7_COST_NUMBER_CLASSIFICATION": record["V7_COST_NUMBER_CLASSIFICATION"],
        "V7_EXECUTION_COST_CEILING_PROVEN": record["V7_EXECUTION_COST_CEILING_PROVEN"],
        "V7_APPROVAL_AUTHORISED": record["V7_APPROVAL_AUTHORISED"],
        "NOT_DESCRIBED_AS": ["FAILED", "CONSUMED", "REJECTED_BY_PROVIDER"],
        "REFUSAL_OUTCOME": SUPERSEDED,
        "REFUSAL_IS_NOT": CONSUMED,
        "GUARD": {
            "runner": "infrastructure/scripts/run_second_opportunity_execution_v7.py",
            "function": "refuse_if_superseded",
            "called_from": [
                "execute, before the approval is read and before any transport exists",
                "refuse_if_consumed, which verification and --execute call",
            ],
        },
        "COST_CEILING_RECORD_VERSION": RECORD_VERSION,
        "COST_CEILING_RECORD_SHA256": _sha(_serialise(record)),
        "SUCCESSOR_EXECUTION_PACKET_ID": V8_ID,
        "OPERATOR_DECISION": list(OPERATOR_DECISION),
        "note": (
            "No inference occurred under V7, so it did not fail, was not consumed and was not "
            "refused by the provider. Its cost figure was an estimate it called a ceiling, and the "
            "operator did not approve it. V1 to V6 stay consumed, and a successor needs an approval "
            "naming its own digest"
        ),
    }


# ------------------------------------------------------------------------------ checking


def _check_terminology(record: dict[str, Any]) -> None:
    block = record["COST_RECORD"]
    if record["TERMINOLOGY"].get("ESTIMATE_IS_NOT_A_CEILING") is not True:
        raise ValidationError(
            "ESTIMATE_CALLED_HARD_CEILING: the terminology no longer keeps them apart"
        )
    for key, value in block.items():
        if "ESTIMATE" in key and ("CEILING" in str(value) or "WORST" in str(value)):
            if key == "PLANNING_COST_ESTIMATE_IS_NOT":
                continue
            raise ValidationError(f"ESTIMATE_CALLED_HARD_CEILING: {key} is {value!r}")
    if block["PLANNING_COST_ESTIMATE_CLASSIFICATION"] != "PLANNING_ESTIMATE" or block[
        "PLANNING_COST_ESTIMATE_IS_NOT"
    ] != ["WORST_CASE", "CEILING"]:
        raise ValidationError("ESTIMATE_CALLED_HARD_CEILING: the planning cost is labelled a bound")
    hard = Decimal(str(block["HARD_EXECUTION_COST_CEILING"]))
    for key in ("PLANNING_COST_ESTIMATE", "PLANNING_INPUT_COST_ESTIMATE"):
        if Decimal(str(block[key])) == hard:
            raise ValidationError(f"ESTIMATE_CALLED_HARD_CEILING: the hard ceiling is the {key}")
    if Decimal(str(block["PLANNING_COST_ESTIMATE"])) > hard:
        raise ValidationError("the planning estimate exceeds the ceiling that is said to bound it")


def _check_propositions(record: dict[str, Any]) -> None:
    pages = {str(row["id"]) for row in record["DOCUMENTATION_EVIDENCE"]}
    if any(row.get("first_party") is not True for row in record["DOCUMENTATION_EVIDENCE"]):
        raise ValidationError("a provider fact rests on a page that is not first-party")
    for name, fragments in record["DOCUMENTED_PROPOSITIONS"].items():
        if not fragments:
            raise ValidationError(f"proposition {name} quotes nothing")
        for fragment in fragments:
            if fragment["evidence"] not in pages or not str(fragment["verbatim"]).strip():
                raise ValidationError(f"proposition {name} cites a page that was not retrieved")
    propositions = record["DOCUMENTED_PROPOSITIONS"]
    for name, fact in record["PROVIDER_FACTS"].items():
        if not fact.get("rests_on") or any(p not in propositions for p in fact["rests_on"]):
            raise ValidationError(f"the provider fact {name} rests on no quoted proposition")
    for row in record["COST_CATEGORIES"]:
        if not row.get("rests_on") or any(p not in propositions for p in row["rests_on"]):
            raise ValidationError(
                f"the cost category {row['category']} rests on no quoted proposition"
            )


def _check_facts(record: dict[str, Any]) -> None:
    facts = record["PROVIDER_FACTS"]
    propositions = record["DOCUMENTED_PROPOSITIONS"]
    window = facts["MODEL_CONTEXT_WINDOW_TOKENS"]
    form = str(window.get("documented_form", ""))
    quoted = " ".join(
        str(f["verbatim"]) for name in window["rests_on"] for f in propositions.get(name, [])
    )
    if not form or form.split()[0] not in quoted or window["value"] != tokens_from_form(form):
        raise ValidationError(
            "CONTEXT_WINDOW_INVENTED: the context window is not the one the quoted pages state"
        )
    capability = _load(CAPABILITY)["MODELS"][MODEL]
    if window["value"] != capability["CONTEXT_WINDOW_TOKENS"]:
        raise ValidationError("the context window disagrees with the held capability register")
    if facts["MAX_OUTPUT_TOKENS"]["value"] != capability["DOCUMENTED_MAX_OUTPUT_TOKENS"]:
        raise ValidationError("the output maximum disagrees with the held capability register")
    if facts["MAX_BILLABLE_INPUT_TOKENS"]["value"] != window["value"]:
        raise ValidationError(
            "MAX_BILLABLE_INPUT_TOKENS is not the documented context window, which is the only "
            "documented bound on billable input"
        )
    if facts["STRICT_INTERNAL_PROMPT_TOKENS"]["value"] != "NOT_ESTABLISHED":
        raise ValidationError(
            "UNKNOWN_STRICT_TOKENS_SAID_COVERED: the injected prompt's size is not documented"
        )
    if record["COST_RECORD"]["BODY_BASED_ESTIMATE_COVERS_THE_STRICT_PROMPT"] is not False:
        raise ValidationError(
            "UNKNOWN_STRICT_TOKENS_SAID_COVERED: the body-based estimate is said to cover a prompt "
            "whose size nobody knows"
        )
    for key in (
        "STRICT_INTERNAL_PROMPT_INCLUDED_IN_CONTEXT_BOUND",
        "STRICT_INTERNAL_PROMPT_INCLUDED_IN_BILLABLE_USAGE",
        "THE_WINDOW_CONTAINS_ALL_INPUT",
    ):
        if facts[key]["value"] is not True:
            raise ValidationError(f"{key} is {facts[key]['value']!r}, and the ceiling rests on it")
    held = record["COST_RECORD"]["PRICE_PER_1K"]
    documented = facts["PRICE_USD_PER_MTOK"]["value"]
    for side in ("input", "output"):
        if Decimal(str(held[side])) * 1000 != Decimal(str(documented[side])):
            raise ValidationError(
                f"MODEL_COST_BASIS_CHANGED: the held {side} price is not documented"
            )
    if record["STRICT_FIRST_REQUEST_TIMEOUT"]["STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8"]:
        raise ValidationError(
            "STRICT_FIRST_REQUEST_TIMEOUT_RISK accepted by the mission that found it"
        )


def _check_categories(record: dict[str, Any]) -> None:
    rows = {str(row["category"]): row for row in record["COST_CATEGORIES"]}
    missing = [name for name in REQUIRED_CATEGORIES if name not in rows]
    if missing:
        raise ValidationError(f"UNDOCUMENTED_BILLING_CATEGORY_IGNORED: {missing} not accounted for")
    selectors = record["REQUEST_BODY_BILLING_SELECTORS"]
    block = record["COST_RECORD"]
    unknown = [name for name, row in rows.items() if row["disposition"] == UNBOUNDED]
    for name, row in rows.items():
        if row["disposition"] not in (*ACCOUNTED, UNBOUNDED):
            raise ValidationError(f"{name} has no disposition")
        selector = row.get("request_selector")
        if (
            row["disposition"] == NOT_APPLICABLE
            and selector is not None
            and selectors.get(str(selector)) != SELECTORS_REQUIRED[str(selector)]
        ):
            raise ValidationError(
                f"CACHE_OR_BILLING_CHARGE_IGNORED: {name} is called inapplicable while the "
                f"request carries {selector}={selectors.get(str(selector))!r}"
            )
    if (
        rows["DATA_RESIDENCY_US_ONLY"]["disposition"] != MULTIPLIER
        and selectors["inference_geo"] != "global"
    ):
        raise ValidationError(
            "UNDOCUMENTED_BILLING_CATEGORY_IGNORED: the request leaves inference_geo to the "
            "workspace default, and the 1.1 US-only multiplier is not in the ceiling"
        )
    if Decimal(str(block["DATA_RESIDENCY_MULTIPLIER"])) < Decimal("1.1"):
        raise ValidationError("the ceiling drops the data-residency multiplier it must carry")
    if record["PROVIDER_FACTS"]["CACHE_BILLING_APPLICABLE"]["value"] is not (
        selectors["cache_control"] is True
    ):
        raise ValidationError("CACHE_BILLING_APPLICABLE disagrees with the request body")
    if block["UNKNOWN_COST_CATEGORIES"] != unknown:
        raise ValidationError("UNKNOWN_COST_CATEGORIES is not the list of unbounded categories")
    if unknown and (
        block["HARD_EXECUTION_COST_CEILING_PROVEN"] is not False
        or block["HARD_EXECUTION_COST_CEILING"] != "NOT_ESTABLISHED"
    ):
        raise ValidationError(f"{NOT_ESTABLISHED}: {unknown} cannot be bounded")


def _check_arithmetic(record: dict[str, Any]) -> None:
    block = record["COST_RECORD"]
    if block["HARD_EXECUTION_COST_CEILING_PROVEN"] is not True:
        raise ValidationError(f"{NOT_ESTABLISHED}: the ceiling is not proven")
    window = int(block["MAX_BILLABLE_INPUT_TOKENS"])
    if window == int(block["BODY_BASED_INPUT_TOKEN_ESTIMATE"]):
        raise ValidationError(
            "the body-based estimate is treated as the maximum billable input: it is an estimate"
        )
    observed = record["OBSERVED_USAGE_NOT_USED"]["usage"]
    seen = {n for usage in observed.values() for n in usage.values()}
    if window in seen or int(block["OUTPUT_TOKEN_HARD_MAXIMUM"]) in seen:
        raise ValidationError("the hard ceiling rests on usage an earlier call reported")
    if record["OBSERVED_USAGE_NOT_USED"]["USED_FOR_THE_HARD_CEILING"] is not False:
        raise ValidationError("the hard ceiling rests on usage an earlier call reported")
    if window != record["PROVIDER_FACTS"]["MAX_BILLABLE_INPUT_TOKENS"]["value"]:
        raise ValidationError("MAX_BILLABLE_INPUT_TOKENS is not the documented bound")
    if (
        int(block["OUTPUT_TOKEN_HARD_MAXIMUM"])
        != record["PROVIDER_FACTS"]["MAX_OUTPUT_TOKENS"]["value"]
    ):
        raise ValidationError("the output hard maximum is not max_tokens")
    actual = [
        Decimal(str(_load(path)["ACTUAL_COST"]["cost_units"]))
        for path in OBSERVED_RECORDS
        if "ACTUAL_COST" in _load(path)
    ]
    if Decimal(str(block["HARD_EXECUTION_COST_CEILING"])) in actual:
        raise ValidationError("the hard ceiling is replaced with a cost an earlier call incurred")
    price = block["PRICE_PER_1K"]
    multiplier = Decimal(str(block["DATA_RESIDENCY_MULTIPLIER"]))
    thousand = Decimal(1000)
    hard_input = Decimal(window) / thousand * Decimal(str(price["input"])) * multiplier
    hard_output = (
        Decimal(int(block["OUTPUT_TOKEN_HARD_MAXIMUM"])) / thousand * Decimal(str(price["output"]))
    ) * multiplier
    expected = {
        "HARD_INPUT_COST_CEILING": decimal_text(hard_input),
        "HARD_OUTPUT_COST_CEILING": decimal_text(hard_output),
        "HARD_EXECUTION_COST_CEILING": decimal_text(hard_input + hard_output),
    }
    for key, value in expected.items():
        if block[key] != value:
            raise ValidationError(f"{key} is {block[key]!r}; the derivation gives {value}")
    derivation_block = record["HARD_CEILING_DERIVATION"]
    if "V2_TO_V6_OBSERVED_USAGE" not in derivation_block["not_derived_from"] or (
        derivation_block["output_subtracted_from_the_input_bound"] is not False
    ):
        raise ValidationError("the derivation no longer excludes estimates and observations")


def _check_v7(record: dict[str, Any]) -> None:
    live = record["V7_COST_RECONFIRMATION"]
    fixed = {
        "EXECUTION_PACKET_ID": V7_ID,
        "EXECUTION_PACKET_VERSION": 7,
        "EXECUTION_PACKET_SHA256_RECOMPUTED": V7_SHA256,
        "EXECUTION_PACKET_FILE_SHA256": V7_PACKET_FILE_SHA256,
        "approval_recorded": False,
        "approval_file_exists": False,
        "execution_record_exists": False,
        "response_artifact_exists": False,
        "provider_strict_mode": True,
        "request_body_characters": V7_REQUEST_BODY_CHARACTERS,
        "request_body_sha256": V7_REQUEST_BODY_SHA256,
        "body_based_input_token_estimate": 18158,
        "output_token_ceiling": 128000,
        "input_cost_called_worst_case": 0.036316,
        "output_worst_case_cost": 1.28,
        "packet_execution_cost_ceiling": 1.316316,
        "strict_mode_injected_system_prompt_tokens": "NOT_ESTABLISHED",
    }
    for key, value in fixed.items():
        if live.get(key) != value:
            raise ValidationError(
                f"V7_COST_RECONFIRMATION.{key} is {live.get(key)!r}, not {value!r}"
            )
    if (
        record["V7_COST_NUMBER_CLASSIFICATION"] != "ESTIMATE_NOT_PROVEN_HARD_CEILING"
        or record["V7_EXECUTION_COST_CEILING_PROVEN"] is not False
        or record["V7_APPROVAL_AUTHORISED"] is not False
    ):
        raise ValidationError(
            "ESTIMATE_CALLED_HARD_CEILING: V7's figure is called a proven ceiling"
        )
    if Decimal(str(live["packet_execution_cost_ceiling"])) != Decimal(
        str(record["COST_RECORD"]["PLANNING_COST_ESTIMATE"])
    ):
        raise ValidationError("V7's figure is not the planning estimate it is reclassified as")
    defect = record["DEFECT"]
    if (
        defect["class"] != "GOVERNANCE_ACCOUNTING"
        or defect["not_a_provider_billing_error"] is not True
    ):
        raise ValidationError("the defect is described as something other than accounting")


def _check_live_v7() -> None:
    """V7 is on disk as Mission 1.84.19 left it: unapproved, unexecuted, its bytes unchanged."""
    if file_sha(PACKET_V7) != V7_PACKET_FILE_SHA256:
        raise ValidationError("packet V7 was edited; superseding it changes nothing in it")
    if APPROVAL_V7.exists():
        raise ValidationError(
            "V7_APPROVAL_FABRICATED: an approval of V7 exists, and a superseded packet can never be "
            "approved"
        )
    for path in (RECORD_V7, RESPONSE_V7):
        if path.exists():
            raise ValidationError(f"V7_EXECUTED: {path.name} exists, and V7 was never executed")


def _check_supersession(doc: dict[str, Any], record: dict[str, Any]) -> None:
    fixed = {
        "SUPERSEDED_EXECUTION_PACKET_ID": V7_ID,
        "SUPERSEDED_EXECUTION_PACKET_VERSION": 7,
        "SUPERSEDED_EXECUTION_PACKET_SHA256": V7_SHA256,
        "SUPERSEDED_EXECUTION_PACKET_FILE_SHA256": V7_PACKET_FILE_SHA256,
        "STATUS": "SUPERSEDED_BEFORE_EXECUTION",
        "REASON": "COST_CEILING_SEMANTICS_NOT_PROVEN",
        "V7_EXECUTED": False,
        "V7_APPROVED": False,
        "V7_APPROVAL_CONSUMED": False,
        "V7_PROVIDER_REQUESTS": 0,
        "V7_MODEL_CALLS": 0,
        "V7_PACKET_MODIFIED": False,
        "V7_COST_NUMBER_CLASSIFICATION": "ESTIMATE_NOT_PROVEN_HARD_CEILING",
        "V7_EXECUTION_COST_CEILING_PROVEN": False,
        "V7_APPROVAL_AUTHORISED": False,
        "NOT_DESCRIBED_AS": ["FAILED", "CONSUMED", "REJECTED_BY_PROVIDER"],
        "REFUSAL_OUTCOME": SUPERSEDED,
        "REFUSAL_IS_NOT": CONSUMED,
        "COST_CEILING_RECORD_SHA256": _sha(_serialise(record)),
    }
    for key, value in fixed.items():
        if doc.get(key) != value:
            raise ValidationError(
                f"V7_SUPERSESSION_MISRECORDED: {key} is {doc.get(key)!r}; it must be {value!r}"
            )


def _check_v7_guard() -> None:
    """The V7 runner refuses V7 by name before any transport, V1 to V6 as spent, and nothing else."""
    module = runner_v7()
    for index, digest in enumerate(SHAS):
        try:
            module.refuse_if_consumed(digest)
        except module.RefusedError as exc:
            if exc.code != CONSUMED:
                raise ValidationError(
                    f"the V7 runner refuses V{index + 1} for the wrong reason"
                ) from exc
        else:
            raise ValidationError(f"the V7 runner would execute V{index + 1}'s spent digest")
    try:
        module.refuse_if_consumed(V7_SHA256)
    except module.RefusedError as exc:
        if exc.code != SUPERSEDED:
            raise ValidationError(
                f"V7 is refused as {exc.code}; it was superseded, and it never had an approval to "
                "spend"
            ) from exc
    else:
        raise ValidationError("V7_STILL_EXECUTABLE: the V7 runner's guard does not refuse V7")
    try:
        module.refuse_if_consumed("0" * 64)
    except module.RefusedError as exc:
        raise ValidationError("the V7 runner's guard refuses an unseen digest") from exc

    class _Tripwire:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("a transport was constructed")

    try:
        module.execute(
            {"packet_file": {"EXECUTION_PACKET_SHA256": V7_SHA256}, "parts": None},
            transport=_Tripwire,
        )
    except module.RefusedError as exc:
        if exc.code != SUPERSEDED:
            raise ValidationError(
                f"V7_STILL_EXECUTABLE: execute() refuses V7 as {exc.code}, not as superseded, and "
                "only after something else was read"
            ) from exc
    else:
        raise ValidationError("V7_STILL_EXECUTABLE: execute() accepted V7")
    tree = ast.parse(RUNNER_V7.read_text(encoding="utf-8"))
    execute = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "execute")
    calls = [
        (node.lineno, node.func.id)
        for node in ast.walk(execute)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    first = {name: line for line, name in sorted(calls, reverse=True)}
    if "refuse_if_superseded" not in first or first["refuse_if_superseded"] > min(
        first.get("check_approval", 10**9), first.get("UrllibTransport", 10**9)
    ):
        raise ValidationError(
            "V7_STILL_EXECUTABLE: execute() does not refuse a superseded packet before its approval "
            "and its transport"
        )


def _check_accounting(record: dict[str, Any]) -> None:
    for key, value in record["ACCOUNTING"].items():
        if key != "DOCUMENTATION_REQUESTS" and value != 0:
            raise ValidationError(f"{key} is {value}, and preparing this record makes none")


def check_record(record: dict[str, Any]) -> None:
    _check_terminology(record)
    _check_propositions(record)
    _check_facts(record)
    _check_categories(record)
    _check_arithmetic(record)
    _check_v7(record)
    _check_accounting(record)


def validate() -> tuple[dict[str, Any], dict[str, Any]]:
    expected = json.loads(json.dumps(build_record()))
    check_record(expected)
    for path in (RECORD, SUPERSESSION):
        if not path.exists():
            raise ValidationError(
                f"{path.name} does not exist"
                + ("; V7_SUPERSESSION_OMITTED" if path == SUPERSESSION else "")
            )
    committed = _load(RECORD)
    check_record(committed)
    for key in sorted(set(expected) | set(committed)):
        if committed.get(key) != expected.get(key):
            raise ValidationError(f"{RECORD.name} {key} is not what the code derives")
    supersession = _load(SUPERSESSION)
    _check_supersession(supersession, committed)
    derived = json.loads(json.dumps(build_supersession(committed)))
    for key in sorted(set(derived) | set(supersession)):
        if supersession.get(key) != derived.get(key):
            raise ValidationError(f"{SUPERSESSION.name} {key} is not what the code derives")
    _check_live_v7()
    _check_v7_guard()
    return committed, supersession


# ------------------------------------------------------------------------------ rendering


def _code(lines: list[str]) -> list[str]:
    return ["```", *lines, "```", ""]


def render(record: dict[str, Any], supersession: dict[str, Any]) -> str:
    block = record["COST_RECORD"]
    facts = record["PROVIDER_FACTS"]
    v7 = record["V7_COST_RECONFIRMATION"]
    lines = [
        "# Second Opportunity: execution cost ceiling and V7's supersession",
        "",
        "Generated by `infrastructure/scripts/render_second_opportunity_execution_cost_ceiling.py`"
        " (CI gate 94) from `second-opportunity-execution-cost-ceiling-v1.json` and "
        "`second-opportunity-synthesis-execution-supersession-v7.json`. Do not edit by hand.",
        "",
        f"**{record['PRIMARY_OUTCOME']}.** {record['DEFECT']['statement']}.",
        "",
        "## Three quantities, kept apart",
        "",
        *_code(
            [
                f"request body                      {block['REQUEST_BODY_CHARACTERS']} characters",
                f"BODY_BASED_INPUT_TOKEN_ESTIMATE   {block['BODY_BASED_INPUT_TOKEN_ESTIMATE']}  "
                f"({block['BODY_BASED_INPUT_TOKEN_ESTIMATE_METHOD']})",
                f"PLANNING_INPUT_COST_ESTIMATE      {block['PLANNING_INPUT_COST_ESTIMATE']}",
                f"PLANNING_COST_ESTIMATE            {block['PLANNING_COST_ESTIMATE']}  "
                f"({block['PLANNING_COST_ESTIMATE_CLASSIFICATION']}, not a worst case, not a ceiling)",
                "",
                f"MAX_BILLABLE_INPUT_TOKENS         {block['MAX_BILLABLE_INPUT_TOKENS']}  "
                f"({block['MAX_BILLABLE_INPUT_TOKENS_BASIS']})",
                f"OUTPUT_TOKEN_HARD_MAXIMUM         {block['OUTPUT_TOKEN_HARD_MAXIMUM']}",
                f"DATA_RESIDENCY_MULTIPLIER         {block['DATA_RESIDENCY_MULTIPLIER']}",
                f"HARD_INPUT_COST_CEILING           {block['HARD_INPUT_COST_CEILING']}",
                f"HARD_OUTPUT_COST_CEILING          {block['HARD_OUTPUT_COST_CEILING']}",
                f"HARD_EXECUTION_COST_CEILING       {block['HARD_EXECUTION_COST_CEILING']}",
                "HARD_EXECUTION_COST_CEILING_PROVEN "
                f"{str(block['HARD_EXECUTION_COST_CEILING_PROVEN']).lower()}",
                f"UNKNOWN_COST_CATEGORIES           {block['UNKNOWN_COST_CATEGORIES']}",
                f"pricing                           {block['PRICING_VERSION']}, "
                f"{block['PRICE_PER_1K']['input']} / {block['PRICE_PER_1K']['output']} per 1000",
            ]
        ),
        "The derivation, in exact decimal arithmetic, and nothing estimated or observed in it:",
        "",
        *_code(
            [
                record["HARD_CEILING_DERIVATION"]["input_side"],
                record["HARD_CEILING_DERIVATION"]["output_side"],
                record["HARD_CEILING_DERIVATION"]["total"],
            ]
        ),
        "## What the provider documents",
        "",
        "| fact | value | rests on |",
        "|---|---|---|",
        *[
            f"| {name} | {fact['value']} | {', '.join(fact['rests_on'])} |"
            for name, fact in facts.items()
        ],
        "",
        "Every value rests on fragments quoted verbatim from first-party pages, located by line, in "
        "bytes whose SHA-256 is recorded:",
        "",
        "| id | page | bytes | sha256 |",
        "|---|---|---|---|",
        *[
            f"| {row['id']} | `{str(row['final_url']).rsplit('/docs/en/', 1)[-1]}` | "
            f"{row['bytes']} | `{str(row['sha256'])[:8]}...` |"
            for row in record["DOCUMENTATION_EVIDENCE"]
        ],
        "",
        "## Every billing category",
        "",
        "| category | disposition | request |",
        "|---|---|---|",
        *[
            f"| {row['category']} | {row['disposition']} | "
            + (
                f"{row['request_selector']} = "
                f"{record['REQUEST_BODY_BILLING_SELECTORS'][row['request_selector']]}"
                if row.get("request_selector")
                else ""
            )
            + " |"
            for row in record["COST_CATEGORIES"]
        ],
        "",
        "## V7, reconfirmed and superseded",
        "",
        *_code(
            [
                f"packet                            {v7['EXECUTION_PACKET_ID']} v"
                f"{v7['EXECUTION_PACKET_VERSION']}",
                f"sha256                            {v7['EXECUTION_PACKET_SHA256_RECOMPUTED']}",
                f"approval recorded                 {str(v7['approval_recorded']).lower()}",
                f"request body                      {v7['request_body_characters']} characters",
                f"body-based input estimate         {v7['body_based_input_token_estimate']}",
                f"input cost it called worst case   {v7['input_cost_called_worst_case']}",
                f"output worst-case cost            {v7['output_worst_case_cost']}",
                f"its EXECUTION_COST_CEILING        {v7['packet_execution_cost_ceiling']}",
                "strict injected prompt tokens     "
                f"{v7['strict_mode_injected_system_prompt_tokens']}",
                f"classification                    {record['V7_COST_NUMBER_CLASSIFICATION']}",
                "",
                f"status                            {supersession['STATUS']}",
                f"reason                            {supersession['REASON']}",
                f"executed / approved / consumed    {str(supersession['V7_EXECUTED']).lower()} / "
                f"{str(supersession['V7_APPROVED']).lower()} / "
                f"{str(supersession['V7_APPROVAL_CONSUMED']).lower()}",
                f"refused as                        {supersession['REFUSAL_OUTCOME']}",
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
        f"ok       hard execution cost ceiling {record['COST_RECORD']['HARD_EXECUTION_COST_CEILING']}"
        " proven from documented bounds; V7 superseded before execution and refused by name"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
