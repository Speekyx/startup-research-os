# Mission 1.84.5 — Provider-Native Token Measurement & Thinking Policy V1

**`BOUNDED_SCHEMA_EXCEEDS_OR_APPROACHES_MODEL_CAPABILITY`**

One provider-native count of the bounded contract's maximum valid instance, against the model the
synthesis would run on, estimates **231608 tokens**. The documented maximum output of a single
synchronous request to that model is **128K**. The contract Mission 1.84.4 made finite admits valid
answers the model cannot emit in one request, and Section 21 stops here: no ceiling was selected, no
execution packet was prepared, and the schema was not reduced to make the number fit.

```
START_COMMIT   2159d3f0ff934851d565dfc499f2cfaea9ffdb2a
BRANCH         sprint-1/mission-1.84.5

OPERATOR_DECISION   PROVIDER_NATIVE_TOKEN_MEASUREMENT, claude-sonnet-5
THINKING_POLICY     CLAUDE_SONNET_5_THINKING_POLICY = DISABLED
OPERATOR_REJECTED   an unofficial or local third-party tokenizer
                    an arbitrary 4k, 8k, 16k, 32k or 64k ceiling
                    shrinking the bounded schema for convenience
```

## What was measured, and what it rests on

The measured text is the one Mission 1.84.4 established as the maximum, rebuilt from the live
v1.1.0 schema rather than copied: `json.dumps(instance, sort_keys=True)` with `ensure_ascii`, every
narrative character the non-BMP fill that serializes as a twelve-character surrogate pair.

```
schema        second-opportunity-synthesis-output@1.1.0  ec789d1b...
text          309729 characters, 309729 UTF-8 bytes
text sha256   e1a62b812f115b3549b5c3c5b8605f2c8052b998cce5d89ac7b60cee5af71705
```

The preconditions were verified against merged 1.84.4 before anything else: finite, zero unbounded
paths, the maximum's character count, byte count and digest, prompt v1.1.0, TED representation
`2528a56a...`, and V1 still consumed. The gate re-reads them from the 1.84.4 records rather than
trusting this mission's copy.

## The documentation, first-party only

**18 fetches, all from `platform.claude.com/docs/en/`. 17 answered 200, one 404, 0 third-party
sources.** The 404 is recorded rather than dropped: `pricing.md` does not exist at the root, and
the pricing page lives at `about-claude/pricing.md` (E12). Every entry carries its requested and
final URL, the retrieval instant, its byte count and its SHA-256, and every proposition cites its
fragments by evidence id and line, each fragment a short quotation or one table row.

| | proposition | established |
|---|---|---|
| A | model id | `claude-sonnet-5` |
| B | max output | 128K on the synchronous Messages API; 300k on the Message Batches API behind a beta header |
| C | tokenizer | the tokenizer introduced with Claude Opus 4.7; about 30% more tokens than Sonnet 4.6 |
| D | count behaviour | same inputs as message creation; total input tokens across messages, system and tools |
| E | tokenizer used by the count | the tokenizer of the model named in the request |
| F | count is not message creation | counting happens before a message is sent |
| G | billing | free to use |
| H | rate limits | separate from and independent of message creation |
| I | estimate | an estimate, off by an unquantified small amount, possibly including system-added tokens |
| J | thinking default | adaptive thinking is on by default for Claude Sonnet 5 |
| K | disabling | yes, `thinking: {type: "disabled"}` |
| L | max_tokens | one hard cap on thinking and response text together |
| M | structured output | forced tool use works with adaptive thinking; native structured outputs exist and are not used here |

**F is classified `DOCUMENTED_AS_NOT_MESSAGE_CREATION` and no further.** The pages say counting is
not message creation; they never say the word inference, so the record does not claim they do.
**The seven values the brief expected were each re-established from a live page** rather than taken
from the brief, and all seven agree.

**128K is read as 128000**, the reading under which the same pages write 1M for the context window.
It is also the smaller of the two readings, so any headroom computed from it errs toward too little,
which is the safe direction.

## The thinking control

`AnthropicThinking` is a `StrEnum` with **two members and deliberately no third**.
`PROVIDER_DEFAULT` sends no `thinking` field, so the request body is **byte-identical to what the
adapter sent before the type existed**; `DISABLED` sends `{"type": "disabled"}`. A string, a dict
or `None` is refused with `TypeError`, because a free parameter would let a caller send a
configuration nobody reviewed. **No generic parameter collection, no change to `LlmRequest`** (so
gate 64 is untouched), and **no prompt bump**: thinking is a transport parameter, not prompt text.

Forced tool use with thinking disabled is `NOT_RESTRICTED_BY_DOCUMENTATION`: the define-tools
restriction names manual extended thinking and two other models, neither of which is this
configuration. `FUTURE_V2_THINKING = DISABLED` and `THINKING_TOKENS_SHARE_V2_MAX_TOKENS = false` are
documented (K and L) and tested on the adapter's DISABLED body; **they are not observed at runtime,
because this mission sent no Messages API request.**

## What this says about V1

**`V1_OUTPUT_BUDGET_SHARED_WITH_ADAPTIVE_THINKING = true`.** The adapter that ran V1 never emitted a
thinking field, a request without one runs adaptive thinking on this model (J), forced tool use works
under adaptive thinking (M), and `max_tokens` caps thinking and answer together (L). So V1's 3000
tokens were a shared budget. **`V1_THINKING_TOKENS_CONSUMED = NOT_ESTABLISHED`**: adaptive thinking
decides per request, display defaults to omitted, and the V1 usage record was never retained.

**The Mission 1.84.2 root cause stays `NOT_PROVABLE_FROM_RETAINED_EXECUTION_ARTIFACTS`.** This is a
`CONTRIBUTING_FACTOR_POSSIBILITY`, and a gate check refuses a rewrite of either record.

## The one request

`run_second_opportunity_token_measurement.py` is a one-shot runner. It is a dry run unless
`--execute` is passed; it rebuilds the measured text from the live schema through Mission 1.84.4's
builder and refuses with `BOUNDED_OUTPUT_MAX_INSTANCE_CHANGED` if it differs; and its transport
seam refuses any URL but the count endpoint, a second call, and any body other than the model plus
one user message carrying exactly that text. The credential was read from the compose file **one key
only** (never by sourcing the file) and its value was never printed, logged or recorded. The receipt
is written with an exclusive create, and a second execution is refused with
`TOKEN_MEASUREMENT_ALREADY_PERFORMED`. **There is no retry path to take.**

```
executed        2026-09-12T08:18:27Z .. 08:18:30Z
request         POST https://api.anthropic.com/v1/messages/count_tokens
header names    anthropic-version, x-api-key
body keys       messages, model   (no system, no tools, no thinking, no max_tokens)
response        200  {"input_tokens":231608}
request id      req_011CeyDXXrz9Nc4XTZfPVo4w
credential      LOADED_FROM_COMPOSE_FILE_ONE_KEY_ONLY, value never recorded
```

## The estimate, and what it is not

- **`ESTIMATE_NOT_EXACT = true`**, and `DOCUMENTED_TOKEN_COUNT_MARGIN = NONE`: the page says the count
  may differ by a small amount and quantifies nothing, so there is no margin to apply.
- **`SAME_MODEL_TOKENIZER_MEASUREMENT = true`**: the request named `claude-sonnet-5` (E).
- **`INPUT_TO_OUTPUT_TOKENIZATION_EQUIVALENCE = NOT_ESTABLISHED`.** The count is of INPUT tokens for
  the escaped text in a user message. No page states that the model spends the same number of OUTPUT
  tokens emitting the same object as a tool call; a model need not emit the escaped form it was
  counted in, and tool-call framing is not in the count. Either direction is possible and neither is
  established, which is why the record carries an estimate and **the gate refuses any
  `EXACT_MAX_OUTPUT_TOKEN_COUNT` key anywhere in it**.

## Against the documented maximum

```
documented maximum output   128000   (128K tokens)
adapter default             4096     (ours, not a capability)
estimate                    231608
headroom to the maximum     -103608
estimate over maximum       1.8094
exceeds                     true
batch beta ceiling          300000   (headroom 68392, not adopted)
```

**An estimate compared with a ceiling is arithmetic**, and not evidence that a real output of this
size would or would not fit. What it does settle is that no synchronous request can ask for as many
tokens as this estimate. The batch route has a documented 300k ceiling on this model and was **not
adopted**: it is asynchronous, behind a beta header, and outside what the TED egress review and the
provider posture assessed, so moving to it is an operator decision with its own review.

### The held ratio would have underestimated it

Mission 1.84's 2.1565 characters per token predicts **143626** tokens for this text; the provider
estimates 231608, so the held ratio is short by **87982** (0.3799 of the estimate). This text
measures **1.3373** characters per token. Mission 1.84.3 warned that a ratio too high underestimates
tokens, and on the worst-case text it would have, by more than a third. Recorded to show the
direction of the error and used for nothing.

## Ceiling, packet, cost

```
SELECTED_MAX_OUTPUT_TOKENS    NONE
OPERATOR_HEADROOM_POLICY      NONE_HELD
EXECUTION_PACKET_V2_CREATED   false
SCHEMA_REDUCED                false
TOKEN_COUNT_API_COST          0              (proposition G)
FUTURE_INFERENCE_COST         NOT_COMPUTED   (no ceiling to price)
```

## Operator options, none implemented and none recommended

- **`BOUND_THE_NARRATIVE_FIELDS_FURTHER`**: lowers the maximum where Mission 1.84.4 located it. A
  contract change whose numbers must be the operator's, not derived from this estimate.
- **`RESTRICT_THE_NARRATIVE_CHARACTER_CLASS`**: removes the twelve-character escape that dominates
  the maximum (the ASCII-fill form measured 56929 characters). A contract change, and the restricted
  form's token count is not measured, because a second count request is outside this mission.
- **`CHANGE_THE_ROUTE_TO_THE_BATCHES_300K_BETA`**: a documented 300k ceiling. A beta, asynchronous
  route outside the reviews already done, and an estimate with no margin is still not proof of fit.
- **`SPLIT_THE_SYNTHESIS_ACROSS_CALLS`**: an architecture change to a contract written for one call.
- **`RUN_AT_THE_PROVIDER_MAXIMUM_ACCEPTING_AN_UNREACHABLE_WORST_CASE`**: valid outputs up to the
  ceiling can be emitted and the gate refuses anything truncated; an operator judgement that part of
  the contract is unreachable, which the briefs have so far declined to make.

## The capability register

`provider-model-capability-register-v1.json` keeps the model's documented numbers (128000
synchronous, 300000 batch beta, a 1M context window, thinking on by default and disableable,
`max_tokens` covering both) **beside the adapter's 4096 and never in place of it**, with a field
asserting the two are distinct. Mission 1.84.4's `PROVIDER_MODEL_CAPABILITY` block is left at
`NOT_ESTABLISHED` as history, and gate 69 refuses a rewrite of it.

## Gate 69

`render_second_opportunity_token_measurement.py --check` re-derives what it can: the measured text
from the live schema, the adapter's default budget, thinking configurations and both request bodies
from the live provider, and the headroom, ratio, cross-check and outcome from the estimate. **What it
cannot re-derive it checks only for shape, and says so**: CI has no network, so whether a fragment
is really on its page is checked by refetching against the recorded digest, not by the gate.

## Accounting

```
documentation fetches   18 (17 used, one 404)   third-party sources   0
token count requests    1                       retries               0
messages API requests   0                       model inference       0
TED bytes sent          0                       research bytes sent   0
canonical mutations     0                       Opportunities         0
```

The thirteen counters were recounted after the pytest suites: 325 / 325 / 60 / 91 / 92 / 112 / 4 /
0 / 1 / 2 / 14 / 0 / 71, identical to 1.84.4, and `scoring.scores` is still absent.

## Verification

`ruff format --check` and `ruff check` clean over 1002 files, with three `S105` false positives
suppressed in the gate and the reason stated at each: the flagged strings are output-token budget
states and a citation, not credentials. `mypy` clean over 200 files. Contracts, catalog and source
registry clean; 29 sources, 45 evidence records, 0 warnings.

**3847 bare-python tests across 9 packages. 3719 pytest tests across 9 packages**, 13 skipped, with
the database unchanged across 29 tenant tables and 17 global tables, and 11 rows appended to one
append-only table. **128 new tests**: 16 on the adapter's thinking control and token counting, 24 on
the runner, 88 on the gate. **69 CI gates**, one of them new.

**Probe: 199 violations caught, 0 escaped, 10 of 10 positive controls, every file proved
restored.** 195 were refused by the check written for them, 2 by the runner's named refusal
`BOUNDED_OUTPUT_MAX_INSTANCE_CHANGED` (one schema bound widened by a single character, another
tightened), 2 by render drift, and 0 by a crash. The cases mutate the shipped records, the frozen V1
packet, the 1.84.2 execution record and the 1.84.4 records on disk, and 12 of them edit the live
adapter or the live schema module and run the whole gate in a fresh interpreter started with `-B`,
so no bytecode written during the probe can answer for a restored source. The controls include an
estimate under the maximum recorded with the headroom outcome, and an estimate of exactly 128000
recorded either way: **the gate forces the stop only when the estimate EXCEEDS the maximum**,
because deciding what "approaches" means needs a headroom policy nobody holds, and inventing a
threshold for it would be the arbitrary ceiling the operator rejected. A docstring edit in the
adapter and a comment in the schema module must pass, which shows the gate reads behaviour and
values rather than bytes.

**The first run found a defect in the probe, not in the gate.** One control was vacuous: the
evidence entry it meant to record as redirected already was, so it mutated nothing and passed. It
was replaced by two real controls, one in each direction, and every case now has to move at least
one byte or the probe stops. **Reading every refusal message afterwards found two that named the
wrong defect** (a fragment carrying both a quotation and a table row was reported as carrying
neither, and an empty quotation as too long). Both messages were corrected and no check changed.

## Outcome and next

**`BOUNDED_SCHEMA_EXCEEDS_OR_APPROACHES_MODEL_CAPABILITY`.**

**Next: `OPERATOR_DECISION_ON_A_BOUNDED_CONTRACT_LARGER_THAN_THE_MODEL_CAN_EMIT`.** Mission 1.84.4
left a conversion question; this mission answered it with the provider's own count, and the answer
turns the question into a contract question. The five options above each have a cost, none is
implemented, and none is recommended, because choosing between them is choosing what the second
Opportunity's synthesis is allowed to be.

**Do not execute synthesis, do not call `/v1/messages`, do not retry V1, and do not persist
Opportunity #2.** Mission 1.84.6 was not started.
