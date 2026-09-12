# Mission 1.84.6 — Second Opportunity Execution Envelope & Packet V2

**`SECOND_OPPORTUNITY_EXECUTION_PACKET_V2_READY_FOR_OPERATOR_APPROVAL`**

The operator decided to run the second-opportunity synthesis at the provider's documented
synchronous maximum and to accept that part of the bounded contract cannot be reached in one run.
This mission records that decision as the operator's, prepares the one call it makes possible as
execution packet V2, and stops. **V2 is frozen and unapproved. No synthesis ran, no Messages API
request was made, no TED byte left this machine, and no Opportunity was written.**

```
START_COMMIT        e9440e72eab559537afb4da90fa58d06fdca7e33
BRANCH              sprint-1/mission-1.84.6

OPERATOR_DECISION   RUN_AT_THE_PROVIDER_MAXIMUM_ACCEPTING_AN_UNREACHABLE_WORST_CASE
decision owner      OPERATOR          decision kind    ARCHITECTURE
derived             false             statement sha256 0380a0132249eed44c2c97ab38b102bd667a847c41e9bf197ae0a5df7f445b00
```

## The decision, recorded as the operator's

`second-opportunity-execution-envelope-decision-v1.json` holds the operator's eleven lines from the
brief verbatim, one per sentence, and a SHA-256 over them joined by newlines, so the record names
the words and not a paraphrase. It records the reason, the accepted consequence and the safety
consequence in the operator's terms, the four alternatives the operator rejected (bounding the
narrative fields further, restricting their character class, moving to the batch beta, splitting
the synthesis across calls), and `MATHEMATICALLY_DERIVED = false`. **Gate 70 refuses a record that
calls the decision derived**, because nothing in it follows from arithmetic: the arithmetic only
said the question had to be asked.

The decision keeps two questions apart. The contract answers *what outputs would SROS accept*; the
execution envelope answers *what outputs can this exact provider route produce in this run*. The
first does not shrink to fit a route and the second does not grow to fit the contract.

```
contract maximum            FINITE_BUT_LARGER_THAN_THE_EXECUTION_ENVELOPE
contract maximum            309729 characters (Mission 1.84.4)
provider-native estimate    231608 tokens, exact: false (Mission 1.84.5)
execution route             SYNCHRONOUS_MESSAGES_API
execution maximum           128000 output tokens
full domain reachable       false
state                       CONTRACT_LARGER_THAN_EXECUTION_ENVELOPE
```

**The state is first-class and it is not `ERROR`, `UNKNOWN` or `SCHEMA_INVALID`.** Reading it as an
error would invite repairing the schema; reading it as unknown would hide that the provider's own
count settled it. A valid schema value need not be generatable under every execution configuration,
and the decision says so in the operator's words.

## What V2 rests on, re-read live

Every precondition was verified against merged 1.84.5 on the preparing machine, and none of the
section-level STOPs fired:

```
schema          second-opportunity-synthesis-output@1.1.0
schema sha256   ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988   (unchanged)
finite          true, 0 unbounded paths, maximum 309729 characters
gate            second-opportunity-output-gate@1.1.0
prompt          1.1.0   2f60c61f63cda410b9f60e3eafd9676f983e7ff0220245c03c88136511ac7e82   (rendered bytes unchanged)
representation  2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72   (3604 characters, unchanged)
TED egress      PERMITTED_WITH_CONDITIONS, eligibility ELIGIBLE, live packet gate AVAILABLE
provider        anthropic APPROVED; anthropic-claude-subscription NOT_APPROVED
capability      claude-sonnet-5: 128000 synchronous, 300000 batch beta (not used)
V1              570657e1..., approval consumed, no further calls authorised
```

**231608 is an estimate.** It is Mission 1.84.5's count of the contract's maximum instance as
INPUT tokens: evidence that the theoretical maximum does not fit a synchronous run, and not an exact
count, not an output token count and not an execution limit. The decision records exactly those
three negations and the gate refuses a record that drops any of them, or that carries an
`EXACT_MAX_OUTPUT_TOKEN_COUNT` key anywhere.

## The ceiling is a selection, not a derivation

```
MAX_OUTPUT_TOKENS          128000
basis                      OPERATOR_SELECTED_DOCUMENTED_PROVIDER_MAXIMUM
OUTPUT_TOKEN_CEILING basis OPERATOR_SELECTED_PROVIDER_MAXIMUM
not based on               SCHEMA_DERIVED_MAXIMUM, PROVIDER_NATIVE_TOKEN_ESTIMATE, EMPIRICAL_CHARS_PER_TOKEN
adapter default            4096 (this repository's number, neither a capability nor this ceiling)
```

128000 is the documented synchronous maximum the capability register holds, selected by the
operator. It is not derived from the schema, not the estimate, and not the empirical ratio, and
**the gate refuses a packet that confuses it with the adapter's 4096** in either direction.

## Thinking disabled, and checked by building the body

`THINKING = DISABLED`, sent as exactly `{"type": "disabled"}`. The adapter's typed control from
Mission 1.84.5 is unchanged, and V2 binds exactly two adapter parameters, `max_output_tokens` and
`thinking`. The gate does not trust the record: it builds the request body from the live adapter
with the packet's own parameters and requires the documented object, `max_tokens = 128000` and the
forced structured-output tool, with no native structured-output migration riding along. On the
preparing machine the same body was built and measured: 20623 characters. **Thinking disabled is
documented (propositions K and L) and verified locally; it is not observed at runtime, because no
Messages API request was made.**

## When the answer does not finish

A max-token stop must fail closed on the provider's own signal, so the adapter gained a classifier
and nothing else: `classify_forced_tool_completion` with four verdicts.

```
signal                  stop_reason
complete                tool_use
output limit            max_tokens, model_context_window_exceeded -> EXECUTION_OUTPUT_LIMIT_REACHED_NO_RETRY
refusal                 refusal -> EXECUTION_REFUSED_BY_PROVIDER_NO_RETRY
anything else           EXECUTION_STOP_REASON_UNSUPPORTED_NO_RETRY (end_turn, pause_turn, missing, new)
```

**The completion signal is read at stage 3, from the response the runner retained, before the
structured output is parsed, validated or judged.** A response cut at the limit can carry a
parseable object, every required key, even an object the whole v1.1.0 schema accepts, and none of
it is consulted: stages 4 to 10 are recorded `NOT_REACHED`. The ten stages are, in order,
transport success, response shape, **provider completion**, parse, schema v1.1.0, semantic gate
v1.1.0, evidence boundary and no distortion, attribution and provenance, persistence eligibility,
human review. The gate reads the policy from the adapter's own constants and classifier, and five
first-party fragments cite each documented value by evidence id and line.

## The timeout, disclosed rather than changed

V2 keeps the reviewed 60 seconds. The transport is not streamed, so the timeout covers the wait for
the whole answer, and nothing held documents how many tokens a synchronous request produces in that
time: `OUTPUT_TOKENS_REACHABLE_WITHIN_TIMEOUT = NOT_ESTABLISHED` and
`TIMEOUT_MAY_END_THE_CALL_BEFORE_MAX_TOKENS = true`. A timeout ends the execution fail-closed with
no retry (`EXECUTION_FAILED_TIMEOUT_NO_RETRY`), which is safe, and it means the envelope in
practice may be smaller than 128000. **A changed timeout is a reviewed decision and was not taken
here.**

## Cost

```
input token estimate     11954     (20623 body characters / 2.1565 x 1.25)
output token ceiling     128000
total token ceiling      139954
pricing                  anthropic-published-2026-09-02 (0.002 / 0.01 per 1k), corroborated by the documented 2 / 10 USD per MTok
worst-case input cost    0.023908  (the float the pricing function returns: 0.023908000000000002)
worst-case output cost   1.28
worst-case total cost    1.303908
EXECUTION_COST_CEILING   1.303908  (headroom policy NONE_HELD)
V1's ceiling             0.1       (V2 is 13.04 times it)
```

The input estimate uses the transport's own serialisation of the body, built locally and never
sent. Mission 1.84 recorded 15742 wire characters and not how it counted them; twelve candidate
definitions over the byte-identical v1.0.0 prompt reproduce none of them, so the record says
`v1_definition_recovered = false`. On V1 the definition used here gives 17264, more than 15742, so
it errs toward more tokens. The documented tool-use overhead of 474 tokens sits inside the
multiplier's margin of 2391.

**No general headroom policy exists**, so the ceiling is the worst case itself rather than an
invented multiple: V1's roughly-twice was that packet's own choice. The ceiling is about thirteen
times V1's, almost all of it the 128000 output tokens the operator selected, and the packet states
it so the approval is given against the number and not discovered after it.

## Retention

`RETENTION_REPAIR_VERIFIED = true`. The raw provider response is retained on every path where one
arrived, **including an output-limit stop**, redacted, with any volunteered reasoning block
stripped; so are its digest, the stop reason, the parsed output where one exists and whether any
stage judged it, the request id, the usage from the Gateway's telemetry and from the response's own
usage block, the terminal outcome, cost, timestamps and errors. Each of the ten retention paths is
named by a runner test the gate requires to exist, and every one runs on a synthetic transport; a
tripwire proves no fixture constructs the real one.

## The runner

`run_second_opportunity_execution_v2.py` is dry by default: it re-verifies everything above against
the live database and the live code and reports `OPERATOR_APPROVAL_NOT_RECORDED`. `--execute`
refuses before a transport exists unless an approval beside the packet names V2's digest and is
complete. V1's spent digest is refused under V2 by V1's own guard, which still permits an unseen
digest. **There is one call site and it is reached once.** The artifact is written with an
exclusive create.

## Four gates that pinned the future to an absence

Gates 65, 67, 68 and 69 each recorded that *their* mission created no execution packet V2, and each
asserted it by refusing any V2 file on disk. Left alone they would have refused this mission's V2
and any later one. **Each was re-pointed from "no V2 file exists" to "any V2 file names a later
mission as its author"**: a V2 whose `prepared_by` parses as a mission after the gate's own is that
mission's, and a V2 claiming the historical mission, an earlier one, or nobody is still refused.
Three historical test assertions were re-pointed the same way rather than deleted, and 64
parametrised tests hold both halves across the four gates.

## Gate 70

`render_second_opportunity_execution_packet_v2.py --check` re-derives the packet digest from its
bound fields, the schema digest from the live contract, the request body from the live adapter, the
completion policy from the adapter's classifier, and every cost figure from the held price. What CI
cannot rebuild, the TED representation and the rendered prompt digest from the research database, it
checks for agreement with the approved digests the frozen records carry. It also refuses an approval
of V2 recorded by the mission that prepared it, and an approval on disk naming any digest but V2's.

## The record, field by field

```
START_COMMIT                     e9440e72eab559537afb4da90fa58d06fdca7e33
BRANCH                           sprint-1/mission-1.84.6
OPERATOR_DECISION                RUN_AT_THE_PROVIDER_MAXIMUM_ACCEPTING_AN_UNREACHABLE_WORST_CASE

schema                           second-opportunity-synthesis-output@1.1.0  ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988
schema finite                    true (0 unbounded paths)
contract full domain reachable   false
maximum-instance estimate        231608 tokens, exact false

model                            claude-sonnet-5
route                            POST https://api.anthropic.com/v1/messages, synchronous, Commercial Terms
documented synchronous maximum   128000

thinking policy                  DISABLED, {"type": "disabled"}
completion-limit signal          stop_reason max_tokens | model_context_window_exceeded, fail closed at stage 3

prompt                           1.1.0  2f60c61f63cda410b9f60e3eafd9676f983e7ff0220245c03c88136511ac7e82
representation                   2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72

MAX_OUTPUT_TOKENS                128000, OPERATOR_SELECTED_DOCUMENTED_PROVIDER_MAXIMUM
input token estimate             11954
worst-case input cost            0.023908
worst-case output cost           1.28
worst-case total cost            1.303908
EXECUTION_COST_CEILING           1.303908

retention repair                 verified, ten paths, each named by a runner test
V1                               consumed; 570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92

V2 created                       yes
V2 SHA256                        d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e
V2 approval recorded             false

model calls                      0
provider requests                0
TED bytes                        0

canonical counters               325 / 325 / 60 / 91 / 92 / 112 / 4 / 0 / 1 / 2 / 14 / 0 / 71
tests                            3853 bare-python, 3888 pytest (13 skipped), 169 new
CI gates                         70 (one new, four re-pointed)

PRIMARY_OUTCOME                  SECOND_OPPORTUNITY_EXECUTION_PACKET_V2_READY_FOR_OPERATOR_APPROVAL
NEXT                             Mission 1.84.7, only after a new explicit operator approval
```

## The approval surface

```
EXECUTION_PACKET_ID                   SECOND-OPPORTUNITY-SYNTH-EXEC-V2
VERSION                               2
SHA256                                d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e

provider                              anthropic
route                                 POST https://api.anthropic.com/v1/messages (synchronous, Commercial Terms)
model                                 claude-sonnet-5
thinking                              DISABLED

schema / gate                         second-opportunity-synthesis-output@1.1.0 / second-opportunity-output-gate@1.1.0
prompt sha256                         2f60c61f63cda410b9f60e3eafd9676f983e7ff0220245c03c88136511ac7e82
representation sha256                 2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72

MAX_OUTPUT_TOKENS                     128000
MAX_MODEL_CALLS                       1
MAX_RETRIES                           0
timeout                               60.0 s

WORST_CASE_CALL_COST                  1.303908
EXECUTION_COST_CEILING                1.303908

contract_full_domain_reachable        false
provider_limit_fail_closed            true
retention_repair_verified             true
human_review_required                 true
OPERATOR_EXECUTION_APPROVAL_RECORDED  false
```

**This document records no approval.** An approval lives beside the packet, in
`second-opportunity-synthesis-execution-approval-v2.json`, recorded by the operator and naming V2's
digest. V1's approval is spent and names a different digest, and the TED egress decision permitted
the material to leave, which is a different act from executing this model with this prompt at this
cost.

## Accounting

```
model calls              0     Messages API requests    0
provider inference       0     token-count requests     0
remote test calls        0     TED bytes sent           0
documentation fetches    0     canonical mutations      0
Opportunities created    0     credential values read   0
```

The thirteen counters were recounted after the final pytest run: 325 / 325 / 60 / 91 / 92 / 112 /
4 / 0 / 1 / 2 / 14 / 0 / 71, identical to 1.84.5, and `scoring.scores` is still absent.

## Verification

`ruff format --check` and `ruff check` clean over 1011 files, with one `S105` false positive
suppressed in gate 70 and its reason stated: the flagged string names an output-token basis, not a
credential. `mypy` clean over 200 files. Contracts, catalog and source registry clean; 29 sources,
45 evidence records, 0 warnings.

**3853 bare-python tests across 9 packages. 3888 pytest tests across 9 packages**, 13 skipped, with
the database unchanged across 29 tenant tables and 17 global tables, and 11 rows appended to one
append-only table. **169 new tests**: 6 on the adapter's completion classifier, 40 on the runner, 64
on the four re-pointed historical gates, 59 on gate 70. **70 CI gates**, one new and four
re-pointed.

**Probe, second run: 266 violations caught, 0 escaped, 13 of 13 positive controls, every file
proved restored**, and `validate()` passing afterwards both in process and in a fresh interpreter.
264 were refused by the check written for them and 2 by render drift; none by a crash. Every item
section 27 names is covered, by mutating the decision, the packet, the frozen V1 packet and
execution record, the 1.84.4 and 1.84.5 records, the capability and provider registers,
preparation v5 and the runner's test file on disk, with each packet or decision edit repaired
(decision re-bound, packet digest recomputed, the runner's pinned digest moved to match) so that the
content checks decide rather than the digest guards in front of them. 33 cases edit the live
adapter, the schema module or the runner and run the whole gate in a fresh interpreter started with
`-B`.

The 13 controls show what section 27 asks for: the shipped state validates with the contract larger
than the envelope; a note reworded and the envelope state re-explained both pass, because the gate
reads fields and not prose; a later mission's approval naming V2's digest is accepted; the gate's
live body is `{"type": "disabled"}` at 128000 and forced into its tool; 128000 is the operator's
selection of the documented maximum while 4096 stays the adapter's; `tool_use` proceeds and both
limit values refuse at the adapter; V1's guard refuses V1 and permits V2; the runner refuses V2
until an approval is recorded; the runner's own synthetic cases pass without constructing the real
transport; and a docstring or comment edit in the adapter, the schema module or the runner passes.

**The first run found two holes in this mission's own gate, and both are closed.** It caught 258
and let 2 through:

- **A route sentence naming the batch beta passed** — *"The Anthropic Message Batches beta,
  asynchronous, under the Commercial Terms of Service."* The check looked for the word
  `synchronous`, and `asynchronous` contains it: the substring trap `testing-strategy.md` §23
  describes, met again. **The reviewed route sentence is now pinned whole**, and a subscription
  described as synchronous under the Commercial Terms is refused with it.
- **A retry loop around the runner's single call site passed.** The gate counted the text
  `gateway.complete(` and found one; the runner's own test looked only for `while`. A loop around
  one call site is a second request with no second call site, so **the gate now reads the runner as
  a syntax tree**: exactly one `.complete(` call, inside no loop or comprehension, in a function
  called at most once, never from a loop and never re-entered. The second run adds a `while` loop,
  a comprehension, `execute` called twice, `execute` called from a loop and `execute` calling itself,
  all refused; the last is refused by the call-count rule, which fires first.

Both holes are pinned by gate 70's tests (four route sentences, eight retry shapes), so neither can
reopen without a test failing.

## Outcome and next

**`SECOND_OPPORTUNITY_EXECUTION_PACKET_V2_READY_FOR_OPERATOR_APPROVAL`.**

**Next: one operator decision, and it is not a mission's to take.** Approving
`SECOND-OPPORTUNITY-SYNTH-EXEC-V2` version 2 by its digest
`d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e`, recorded beside the packet by
the operator, authorises **Mission 1.84.7 -- Second Opportunity Synthesis Execution V2**: exactly one
request on the synchronous route with thinking disabled at 128000, the ten ordered stages, a
max-token stop failing closed before any parse, and an Opportunity hypothesis persisted only after
deterministic acceptance and a separate human approval.

**Do not execute V2 without that approval, do not approve it on the operator's behalf, do not reuse
V1's approval, and do not persist Opportunity #2.** Mission 1.84.7 was not started.
