# Mission 1.85.7 report: final operator decision package and tight cost bound (N08-B-PILOT)

**Outcome: `FINAL_OPERATOR_DECISIONS_PREPARED`.**

Every fact the operator needs for the three remaining decisions is computed, verified and rendered, and every
decision is blank:
- the ten single-human pilot thresholds;
- the retry reading;
- the hard cost ceiling.

The execution size of the pilot was measured from the exact 46 approved requests without sending them. The
provider route was re-verified from current first-party documentation. The ceiling is now proposed at
**$9.000000** instead of the old full-context bound of $206.5452, and **the runner enforces it before every
call**, which it did not do before this mission.

The packet is re-rendered as version 3 (`63c7302d...`) and stays `BLOCKED_OPERATOR_DECISIONS`.

Start: `main` at `f73c200`.

Counters for this mission:
- provider calls 0;
- model inferences 0;
- Stack Overflow text sent to the provider 0;
- token-counting calls 0;
- AI annotations 0;
- holdout records opened 0;
- production findings, Signals, Claims and Evidence 0;
- Opportunity #2: none;
- approvals created 0;
- operator decisions made 0.

## 1. Verified starting state

Recomputed on `main`, not quoted:

| Check | Result |
|---|---|
| `build_semantic_egress_eligibility.py --check` | ok: `EGRESS_APPROVED` 46, `EGRESS_EXCLUDED` 4, review required 0 |
| `render_semantic_extraction_packet.py --check` | ok, packet `9040fd62...`, `BLOCKED_OPERATOR_DECISIONS` |
| Reference strength / result scope / result label | `SINGLE_HUMAN_REFERENCE` / `DEVELOPMENT_PILOT` / `PILOT_NOT_CERTIFICATION` |
| HOLDOUT | `holdout_included` false, `holdout_reference_permitted` false |
| Approval or attempt file | none |

## 2. Human-reference composition

Recomputed from the committed `operator-a` annotation over the 46 approved records (all 50 records in
brackets):

| Label | PRESENT | ABSENT | UNCERTAIN |
|---|---|---|---|
| `REPORTED_FAILED_ATTEMPT` | 15 (15) | 29 (33) | 2 (2) |
| `NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` | 0 (0) | 45 (49) | 1 (1) |

The earlier numbers still hold. **`NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` cannot satisfy a minimum-PRESENT
composition requirement and cannot provide meaningful positive-class recall in this DEVELOPMENT pilot.**
That is not a model failure. `PILOT_INSUFFICIENT_SUPPORT` is a valid outcome, and no threshold was weakened to
avoid it.

## 3. Pilot threshold decisions (A)

The source is the Mission 1.85.5 partition. The values are unchanged and every status stays
`PROPOSED_NOT_AUTHORISED`. Each item offers `AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT`,
`REVISE_BEFORE_THE_PILOT_RUN` or `REJECT_FOR_THE_PILOT`, and every decision is blank. Results would use
`PILOT_WITHIN_PROPOSED_BOUND`, `PILOT_OUTSIDE_PROPOSED_BOUND` or `PILOT_INSUFFICIENT_SUPPORT`.

| Item | Proposed | Current DEVELOPMENT support | Likely reading |
|---|---|---|---|
| false-PRESENT upper 95 / NEGATIVE_EVALUATION | 0.1 | 0 reference PRESENT; needs 30 PRESENT predictions | INSUFFICIENT_SUPPORT |
| false-PRESENT upper 95 / REPORTED_FAILED_ATTEMPT | 0.2 | 15 reference PRESENT; needs 15 PRESENT predictions | any |
| min true PRESENT and ABSENT / each label | 1 | RFA 15 / 29; NEG 0 PRESENT | INSUFFICIENT_SUPPORT for NEG |
| mechanical unsupported assertions | 0 | no reference needed; 46 records | within or outside |
| validator acceptance rate | 0.95 | no reference needed; 46 ≥ 20 | within or outside |
| unnecessary abstention on decided records | 0.1 | decided RFA 44, NEG 45; ≥ 20 | within or outside |
| run-to-run flip rate | 0.1 | needs 3 runs; this is 1 | INSUFFICIENT_SUPPORT |
| composition gate | 4 / 4 | RFA met; NEG not met | REFERENCE_SET_INSUFFICIENT for NEG |
| recall | descriptive | RFA 15 PRESENT; NEG undefined | descriptive |
| cost and latency | recorded | no reference needed | recorded |

**Flip rate.** No second full execution is required for this first pilot, and the budget is not doubled. The
item carries a separate repeatability disposition:
- `DEFER_TO_A_LATER_REPEATABILITY_RUN`;
- `AUTHORISE_A_SEPARATELY_APPROVED_SECOND_RUN_LATER`;
- `REJECT_FOR_THIS_FIRST_PILOT`.

## 4. Retry proposal (B)

Proposed reading, not ratified:
- at most one retry per record;
- only when the forced-tool payload is missing, invalid against the strict schema, or structurally incomplete;
- no retry on a validator refusal;
- no retry on a provider or network error;
- no retry because a schema-valid answer looks wrong;
- no provider or model fallback.

**Inside the retry class:** a `SchemaValidationError`, a missing required key, or a finding without a required
field.

**Outside it:** a schema-valid quote that is not in the surface, an `extraction_state` inconsistent with its
findings, HTTP 400, 429 or 5xx, a timeout or connection error, `stop_reason` `max_tokens` or a refusal, and a
semantically disputed answer.

The implementation is `may_retry`, which retries only `SCHEMA_FAILURE` with no retry used yet. Choices:
`RATIFY`, `REVISE`, `REJECT`. Blank.

## 5. Exact input-size measurement

`infrastructure/scripts/measure_semantic_extraction_request_sizes.py` built each request body offline, through
the runner's own prompt (`prompt_sha256` bound), strict tool and provider body builder, with the runner's
packet-local index and a fake transport. It reads the held records (`DATABASE_URL`) and writes counts only to
`docs/data/semantic-extraction-request-size-development-v1.json`. Its surface character counts equal the
corpus `surface_length` for all 46 records.

| Quantity (46 records) | min | median | p95 (nearest rank) | max | total |
|---|---|---|---|---|---|
| Surface characters | 230 | 1,483.5 | 5,887 | 12,805 | 100,540 |
| Surface UTF-8 bytes | 230 | 1,483.5 | 5,887 | 15,275 | 103,227 |
| Request body UTF-8 bytes | 4,921 | 6,237.5 | 10,747 | 20,532 | 322,746 |
| Body excluding surface bytes | 4,691 | 4,745 | 4,877 | 5,257 | 219,519 |

**Fixed overhead:** the system region is 3,325 JSON bytes, the strict tool definition 879 and `tool_choice` 50.

**No local tokenizer exists for this model, and no count was fabricated.** The token-counting endpoint would
transmit the text, and its counts are documented as estimates, so no token was counted. §7 gives the
conservative method.

## 6. Provider and model verification

`docs/data/anthropic-claude-sonnet-5-pilot-verification-v1.json`, retrieved 2026-09-17:
- **Retrieval:** 16 first-party documents were retrieved, and 9 are committed as evidence rows with URL,
  final URL, bytes, SHA-256 and quotes verified verbatim against the retrieved bytes.
- **What was not called:** no models endpoint, no messages endpoint, no token counting.

| Fact | Value |
|---|---|
| Provider / route | Anthropic Claude API, synchronous `POST /v1/messages` |
| Model bound by the packet | `claude-sonnet-5`, documented API id `claude-sonnet-5` |
| Documented state | **ACTIVE**; retirement not sooner than June 30, 2027; not a Covered Model |
| API availability probe | not performed (a call would be a provider call); rests on documentation |
| Input / output price | **$2 / $10 per MTok**, the standard price |
| Multiplier | 1.1x for US-only inference, **applied** because `inference_geo` is not sent and the workspace default is not observable |
| Prompt caching | not used (no `cache_control`) |
| Context window / max output | 1M tokens / 128K (runner permits 4,096) |
| Tool-use system prompt (`tool_choice: tool`) | 474 tokens |
| Strict-mode injected prompt | documented to exist and be billed; size NOT_ESTABLISHED |
| Training | Customer Content from Services not used for training |
| Retention | deleted within 30 days, except longer-retention services, a separate agreement, Usage Policy enforcement (up to 2 years; scores up to 7 years) and legal compliance |
| ZDR for this account | **NOT_ESTABLISHED** |

**No model was substituted.** A model change would be its own decision, because it changes the packet.

## 7. Cost model

`sros_semantic_extraction.cost` (`semantic-extraction-pilot-cost-model@1.0.0`) uses exact decimals.

| Figure | Value | Basis |
|---|---|---|
| EXPECTED_CALLS | 46 | one call per approved record |
| MAX_CALLS_WITH_RETRY | 92 | one schema retry per record, at most |
| Planning estimate | **$0.838035** | ceil(body bytes × 0.40) + 474 input, 1,000 output per call |
| Conservative bound (one pass) | **$3.032986** | body bytes + 474 + 2,000 strict allowance input, 4,096 output per call |
| Retry worst case | **$6.065972** | every record retried once at the conservative bound |
| One call at the documented maximum | $2.245056 | 1,000,000 input + 4,096 output |
| **Proposed hard ceiling** | **$9.000000** | retry worst case + one documented-maximum call, rounded up to a whole dollar |
| Old full-context bound | $206.5452 | **not reused** |

The 0.40 planning ratio comes from two real strict forced-tool requests to this model in this repository
(12,493 and 13,435 input tokens for about 31.3k and 34.3k characters, provider-side prompts included).

Counting one token per byte over-counts English text and code, which is why that count is the conservative
bound. It remains an estimate.

The ceiling is not the full context window multiplied by 92. The window is used once, as a guard on the next
call.

## 8. Enforcement audit

**Before this mission** the runner enforced `max_calls` and compared the approval's accepted ceiling with the
packet field. **Nothing accumulated spend**, so the ceiling was an approval formality rather than a financial
boundary. That was fixed before proposing anything:

| When | Behaviour | Refusal |
|---|---|---|
| `main`, before any transport | no operator-accepted ceiling | `COST_CEILING_NOT_ACCEPTED` |
| `main`, before any transport | provider verification not VERIFIED or ACTIVE, or past its 180-day interval | `PROVIDER_VERIFICATION_NOT_ESTABLISHED` / `_EXPIRED` |
| preflight, in `main` and `execute` | accepted ceiling < retry worst case + one documented-maximum call | `CEILING_BELOW_BOUNDED_RUN_COST` |
| before every call, including a retry | spent + one documented-maximum call > accepted ceiling | `COST_CEILING_WOULD_BE_CROSSED` |
| after each call | HTTP 200 charged its reported usage (cache fields counted as input); no reported usage charged the documented maximum | none |
| after each call | reported input above the record's conservative bound | `CONSERVATIVE_INPUT_BOUND_EXCEEDED` |

Every stop writes the partial run record, with charges and spend, before refusing.

**A defect was caught by the new tests before merge.** The helper that writes the partial record was named
`stop`, the same name as the retry loop's `stop_reason` variable, so a mid-run stop would have crashed instead
of refusing. It was renamed.

## 9. Packet status

Version 3, `63c7302d64d52aa49e56060de1a2d92ffdb8e2030e9c19ba550acba0cc357993`, runner re-pinned.

Status `BLOCKED_OPERATOR_DECISIONS`, with exactly:
1. `THRESHOLDS_NOT_AUTHORISED: 10 of 10 single-human pilot threshold decisions unmade`;
2. `RETRY_INTERPRETATION_NOT_RATIFIED: the retry decision is blank`;
3. `COST_CEILING_NOT_ACCEPTED: the ceiling decision is blank`.

How the packet stays blocked:
- **Blank decisions are blockers.** The blockers are derived from the operator decisions file, the decision
  package and the provider verification.
- **Other decision states block too:**
  - `REVISE` and a `REJECT` of the retry reading or of the ceiling block;
  - a mismatched accepted ceiling, a missing repeatability disposition and unattributed decisions each block.
- **Provider problems block:** unknown pricing, an unverified or unavailable model, or stale cost facts.
- **The accepted ceiling is empty:** `hard_ceiling_usd_approved` is null until the operator accepts.
- **The runner still refuses** any status other than READY before reading an approval, and requires the
  approval to name the packet digest, the accepted ceiling and the reference strength.

## 10. Remaining operator actions

In `docs/data/semantic-extraction-operator-decisions-development-v1.json`:
1. **A.** A decision for each of the 10 pilot thresholds, and a repeatability disposition if the flip rate is
   authorised.
2. **B.** `RATIFY`, `REVISE` or `REJECT` for the retry reading.
3. **C.** `ACCEPT` (with `accepted_hard_ceiling_usd` `9.000000`), `REVISE` or `REJECT` for the hard ceiling.

Also fill in `decided_by` and `decided_at`, then re-render the package and the packet. A READY packet then
needs a separate packet-scoped approval file. **Merging this mission grants no execution authority.**

## 11. Tests

**New `packages/semantic-extraction/python/tests/test_pilot_decision_package.py`**, with scripted gateways and
synthetic decision copies only:

| Requirement | Test |
|---|---|
| cost from the exact approved set; excluded records cost nothing | `test_cost_is_derived_from_the_exact_approved_set_only` |
| expected calls = approved; retry maximum distinct | `test_expected_calls_and_the_retry_maximum_are_distinct` |
| old $206.5452 not reused | `test_the_old_full_context_bound_is_not_reused` |
| pricing source versioned and digested | `test_the_pricing_source_is_versioned_and_digested` |
| unknown pricing blocks readiness | `test_unknown_pricing_blocks_readiness`, `test_unknown_prices_have_no_default` |
| unavailable model blocks; no substitution | `test_an_unavailable_configured_model_blocks_readiness_and_nothing_is_substituted` |
| unresolved thresholds, retry or ceiling keep the packet blocked | `test_unresolved_decisions_keep_the_packet_blocked`, `test_each_decision_blocks_on_its_own` |
| runner fails closed before crossing the ceiling | `TestLedger`, `test_preflight_refuses_before_any_call`, `test_the_run_stops_before_a_call_that_could_cross_the_ceiling`, `test_input_above_the_conservative_bound_stops_the_run` |
| no approval file created automatically | `test_the_committed_packet_cannot_execute_and_no_approval_exists`, `test_the_new_scripts_build_no_transport_and_count_no_tokens` |
| no provider call | the same syntax-tree checks, plus scripted gateways throughout |

**Updated:**
- runner fixtures now set an accepted ceiling on synthetic READY packets;
- the roadmap test accepts `FINAL_OPERATOR_DECISIONS_PREPARED`;
- CI renders `render_semantic_extraction_decision_package.py --check`.

**Local runs before the pull request**, with CI as the merge gate:
- `ruff format --check`, `ruff check`, and the CI `mypy` invocation over 242 source files: clean;
- bare runner: 3981 tests across 10 packages, all passing;
- pytest:
  - semantic-extraction 57 (23 new);
  - llm-gateway 171 (2 skipped);
  - research-orchestrator 97;
  - inferred-claim-evaluator 2470;
  - evidence-reliability 352;
  - opportunity-engine roadmap 87;
  - acquisition 134;
- `build_semantic_egress_eligibility.py --check` and `measure_semantic_extraction_request_sizes.py --check`
  (database-backed): ok;
- all 100 `--check` render commands named in `ci.yml`, including the new decision-package check, and every
  CI validator: clean.
