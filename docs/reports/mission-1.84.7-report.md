# Mission 1.84.7 — Second Opportunity Synthesis Execution V2

**`EXECUTION_SCHEMA_REJECTED_NO_RETRY`**

The operator approved exactly one execution of packet V2 by its digest. The approval was recorded
beside the packet, the fifteen pre-execution checks passed with no network, and **exactly one
provider request was made**. The provider finished normally (`stop_reason = tool_use`), the forced
structured output parsed, and the frozen v1.1.0 schema refused it on one field:
`evidence_bound_reasoning_summary` is **1113 characters against a maximum of 900**. Stages 6 to 10
were not reached. **No retry, no second request, nothing persisted, and the approval is spent.**

```
START_COMMIT       a8f7c89233350e00109a9d708cb51dd5fec29636
BRANCH             sprint-1/mission-1.84.7

APPROVAL           second-opportunity-synthesis-execution-approval-v2.json
                   APPROVE_EXACTLY_ONE_EXECUTION of SECOND-OPPORTUNITY-SYNTH-EXEC-V2 v2
                   d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e
                   operator statement sha256 19bf1b16e324b30faf375ceaaca9f46759b8313462dde15fa1c59a7658340d09

PRIMARY_OUTCOME    EXECUTION_SCHEMA_REJECTED_NO_RETRY
runner code        EXECUTION_OUTPUT_REJECTED_AT_SCHEMA_VALIDATION_NO_RETRY
```

## The approval, recorded beside the packet

`second-opportunity-synthesis-execution-approval-v2.json` was written once, with an exclusive
create. It holds the operator's words verbatim, 88 lines with blank lines dropped, and a SHA-256 over
them; it names the packet's id, version and digest and the decision
`APPROVE_EXACTLY_ONE_EXECUTION`; it carries the approved execution field by field and the
operator's 26 prohibitions as data rather than prose. **The frozen packet was not touched**: its
`OPERATOR_EXECUTION_APPROVAL_RECORDED` still reads `false`, because that field says the document
records no approval, never that none exists. Gate 70 accepts the approval because a later mission
recorded it and it names V2's digest; gate 71 checks its words.

## Before any socket

The runner's verification ran twice with no network, once dry and once as the first half of
`--execute`, and every check passed both times:

| # | the brief's check | found |
|---|---|---|
| 1 | V2 digest | `d27f2896…`, recomputed from the bound fields |
| 2 | approval names that digest | `RECORDED` |
| 3 | V1 consumed | `true` |
| 4 | representation | `2528a56a…`, 3604 characters, rebuilt from the database |
| 5 | prompt | `2f60c61f…`, rendered and hashed |
| 6 | schema / gate | `second-opportunity-synthesis-output@1.1.0` `ec789d1b…` / `second-opportunity-output-gate@1.1.0` |
| 7 | provider posture | `APPROVED` |
| 8 | TED transmission / packet | `PERMITTED_WITH_CONDITIONS` / `AVAILABLE` |
| 9 | model | `claude-sonnet-5` |
| 10 | request body | `max_tokens` 128000, `thinking` `{"type": "disabled"}`, 20623 characters |
| 11–12 | calls / retries | 1 / 0 |
| 13 | route | `POST https://api.anthropic.com/v1/messages`, synchronous, no beta header |
| 14 | cost ceiling | worst case 1.303908 = ceiling |
| 15 | retention | ten paths verified, runner tests green |

**What was read in the code before the call, because there is no second chance.** The Gateway's
budget check compares only what a session has already spent, so it could not refuse on the
128000-token worst case. The strong tier is bound to `anthropic` / `claude-sonnet-5`. The request
carries `max_retries = 0`, which overrides the deployment's `LLM_MAX_RETRIES=2`, so the Gateway's
retry branch cannot be entered. The recording transport keeps the response's status, redacted body
and request id and never a request header, so the credential cannot reach an artifact. The
credential is loaded into the runner's own process by its environment loader and was never printed.

## A retention fail-safe, added before the call

The 1.84.6 runner validated the answer and rendered its artifact **before** writing anything. An
exception in a stage, or a value the JSON encoder refused, would have lost the only response of a
spent call, which is exactly how Mission 1.84.2 lost V1's. So before the call, `settle` was added:
it judges and renders as before, and if either fails it writes what the recording transport
captured, as plain redacted data with any reasoning stripped. It does not touch the request, its
parameters or the single call site, and gate 70 still finds one call site reached once. **It was not
needed**: the normal path wrote the artifact. Eight tests exercise it without a transport.

## The one request

```
started / finished   2026-09-12T17:27:01.237296+00:00 / 2026-09-12T17:27:36.725026+00:00
elapsed              35.488 s of a 60.0 s timeout
route                POST https://api.anthropic.com/v1/messages (synchronous)
model                claude-sonnet-5 (the response names claude-sonnet-5)
thinking             DISABLED, {"type": "disabled"}
max_tokens           128000
HTTP status          200
request id           req_011CeywMgAf1zatspVvwd5np
message id           msg_011CeywMh319RG448pcdBSmB
```

## What came back

```
stop_reason       tool_use -> COMPLETE
input tokens      8939   (estimated 11954: the estimate covered it)
output tokens     3914   (ceiling 128000)
total tokens      12853
thinking tokens   0
cost              0.057018 = 0.017878 input + 0.03914 output   (anthropic-published-2026-09-02)
ceiling           1.303908   (the call cost about 4.4% of it)
```

The response reports `thinking_tokens = 0`: **thinking disabled is observed at runtime for the
first time**, where Mission 1.84.6 could only say it was documented and verified locally. The cost
is derived from the usage the provider reported, at the held price, and equals the Gateway's
telemetry; the provider's invoice is not observed. **The worst case of 1.303908 was a bound
computed before the call and is not what the call cost.**

## The ten stages

| stage | verdict |
|---|---|
| `1_transport_success` | PASSED |
| `2_provider_response_shape` | PASSED |
| `3_provider_completion` | PASSED |
| `4_structured_output_parse` | PASSED |
| `5_schema_validation_v1_1_0` | **FAILED** |
| `6_semantic_output_gate_v1_1_0` | NOT_REACHED |
| `7_evidence_boundary_and_no_distortion` | NOT_REACHED |
| `8_attribution_and_provenance` | NOT_REACHED |
| `9_persistence_eligibility` | NOT_REACHED |
| `10_human_review` | NOT_REACHED |

`evidence_bound_reasoning_summary: 1113 characters exceeds maxLength 900`, the only violation.
**A stage that was not reached is not a stage that passed.**

## What the failure is, stated as facts

- **Neither the envelope nor the timeout was the constraint.** The answer used 3914 of 128000 output
  tokens and 35.5 of 60 seconds, and it finished on the provider's own completion signal.
- **The bound that refused it is old.** The 900-character limit on
  `evidence_bound_reasoning_summary` comes from Mission 1.31's base schema, and Mission 1.84.4, which
  bounded the eight unbounded item types, left it unchanged.
- **The prompt text does not state it.** The v1.1.0 prompt's bounded-output block names the
  character limits on `critical_uncertainties` (500) and on the commercial claims (300), and says
  the reasoning belongs in `evidence_bound_reasoning_summary`; it does not state that field's
  900-character limit in words. The limit reached the model inside the forced tool's input schema.
- **The overage was 213 characters.**

These are observations for the operator's decision. Nothing was changed on the strength of them and
nothing is recommended here: the prompt, the schema and the gate stay exactly as frozen, as the
approval requires.

## What the rejected answer said, retained as evidence and not as a candidate

The model returned `FORM_HYPOTHESIS` with confidence `EXPLORATORY`. It named three supported
dimensions (`BUYER_OR_BUDGET_EXISTENCE`, `ECONOMIC_VALUE`, `MARKET_ACTIVITY`) and eleven unsupported
ones, including `PROBLEM_OR_NEED`, `WILLINGNESS_TO_PAY` and `SOLUTION_GAP`. Its hypothesis is an
investigation-stage one: that it is worth finding out why contracting authorities under CPV class
9261 publish varying `TOTAL_VALUE` figures and whether a buyer's needs could be characterised,
stating in the same sentence that the packet establishes no need, gap, dissatisfaction or
willingness to pay. It listed eight commercial claims as not supported, among them market demand and
willingness to pay. It cited six Evidence ids and five Claim ids; checked after the fact, all lie
inside the packet, **which is an observation and not a stage verdict**, because stage 7 never ran.

**The semantic gate never judged this answer, and it is not a candidate for persistence.** The
retained body and the parsed output are in `second-opportunity-synthesis-response-v2.json`.

## Spent, and refused by name

`second-opportunity-synthesis-execution-record-v2.json` records the approval as consumed. V1's guard
reads only V1's record, so the V2 runner's guard now reads V2's record too: the digest it names is
refused and any other is not. **A verification run after the execution refuses V2 before any
network**, with `EXECUTION_APPROVAL_ALREADY_CONSUMED`, and `--execute` is refused as well by the
response artifact already existing. Five tests hold both halves. V1's historical record is
unchanged, byte for byte.

## Gate 71

`render_second_opportunity_execution_record_v2.py --check` re-derives the record from what was kept
rather than reading it:

- the raw response digest from the retained body, re-serialised compactly (9264 characters);
- the stop reason through the adapter's own classifier;
- the schema violation by running the live v1.1.0 validator over the retained answer;
- the cost from the reported usage at the held price, matched against the Gateway's telemetry;
- the stage table from those facts;
- the approval against its own words and digest;
- V1's record against its pinned digest;
- the runner, asked whether it would execute V2 again.

It refuses a human-review packet for an answer the machine stages did not accept, a `NOT_REACHED`
stage counted as passed, a factual outcome that does not follow from the runner's, any persistence
or moved counter, and a credential shape anywhere.

## The execution record, field by field

```
packet V2 digest            d27f2896a99a77958562d85f9262277e1a430cab654d210a0f8d88f36f1db16e
approval                    approval-v2.json 1885358d0b7fde8e95a587f124cf9b85d41b1471ee0aeb4a21cd0a5e2712555c
                            statement 19bf1b16e324b30faf375ceaaca9f46759b8313462dde15fa1c59a7658340d09
request count               1
retry count                 0
provider route              POST https://api.anthropic.com/v1/messages, SYNCHRONOUS_MESSAGES_API
model                       claude-sonnet-5
thinking policy             DISABLED, {"type": "disabled"}
max_tokens                  128000
timeout                     60.0 s
stop reason                 tool_use
raw-response retention      retained, ea887bd6d0963a19731d6ad232d85ff2a28cc6cd3047c5cabdaf9823448a2217
usage retention             retained
actual measured usage       8939 input, 3914 output, 12853 total, 0 thinking
actual measured cost        0.057018
validation stages           1-4 PASSED, 5 FAILED, 6-10 NOT_REACHED
terminal outcome            EXECUTION_SCHEMA_REJECTED_NO_RETRY
human review required       true (no human-review packet: stage 5 refused the answer)
canonical persistence       false
```

## Accounting

```
provider requests        1
model calls              1
retries                  0
fallbacks                0
TED bytes sent           3604   (the approved representation, unchanged, in a 20623-character body)

provider stop reason     tool_use

actual input tokens      8939
actual output tokens     3914
actual total tokens      12853
actual cost              0.057018

validation stages passed 4 (1 to 4)
failed stage             5_schema_validation_v1_1_0

raw response retained    yes
usage retained           yes

Opportunity persistence  false
canonical mutation       0
```

## Canonical state

| | before | after |
|---|---|---|
| RawRecords | 325 | 325 |
| NormalizedRecords | 325 | 325 |
| Signals | 60 | 60 |
| Claims | 91 | 91 |
| ClaimRevisions | 92 | 92 |
| Evidence | 112 | 112 |
| ReliabilityAssessments | 4 | 4 |
| EvidenceIndependenceGroups | 0 | 0 |
| Opportunities | 1 | 1 |
| OpportunityRevisions | 2 | 2 |
| OpportunityEvidenceLinks | 14 | 14 |
| Embeddings | 0 | 0 |
| Scores | absent | absent |
| SourceReviews | 71 | 71 |

Counted before the branch was cut, again straight after the call, and again after the final pytest
run.

## Verification

`ruff format --check` and `ruff check` clean over 1017 files. `mypy` clean over 200 files.
Contracts, catalog and source registry clean; 29 sources, 45 evidence records, 0 warnings.

**3853 bare-python tests across 9 packages. 3956 pytest tests across 9 packages**, 13 skipped, with
the database unchanged across 29 tenant tables and 17 global tables, and 11 rows appended to one
append-only table. **68 new tests**: 8 on the post-call fail-safe, 5 on V2's consumed-approval
guard, 55 on gate 71. **71 CI gates**, one new.

**Probe on gate 71: 116 violations caught, 0 escaped, 6 of 6 positive controls, every file proved
restored**, and `validate()` passing afterwards both in process and in a fresh interpreter. 115
were refused by the check written for them and 1 by render drift.

The cases edit on disk the record, the approval, the response artifact, V1's record and packet V2.
Each record, approval or response edit is followed by rebinding the record's pins, so the content
checks decide. Five cases edit live code and run the whole gate in a fresh interpreter started with
`-B`:

- a runner blind to V2's record;
- a runner whose V2 check is disabled;
- a runner that refuses every digest;
- an adapter that no longer reads `tool_use` as complete;
- a schema whose 900 bound is raised so the retained answer would pass.

The controls: the shipped record validates; a note reworded in the record, the approval or the
artifact binds nothing; and a docstring or comment edit in the adapter or the runner passes.

**The first run found two cases caught by a crash rather than a rule.** A record gave `ACTUAL_USAGE`
or `ACTUAL_COST` as `NOT_ESTABLISHED`, the brief's word for a figure genuinely unavailable, while the
retained response reports the usage. The gate failed with an `AttributeError`. A crash fails CI but
states no reason, so the gate now refuses a non-block where a block belongs and names this case
explicitly. Two tests pin it.

## Outcome and next

**`EXECUTION_SCHEMA_REJECTED_NO_RETRY`.**

**Stop for human review.** V2's approval is spent and the runner refuses its digest by name. No
further call is authorised: any further execution needs a new packet digest and a new explicit
operator approval naming it.

Whether anything changes before then is the operator's decision: the prompt, the schema's
900-character bound, or nothing. This mission implemented none of them and recommends none. The
rejected answer is retained as evidence and is not a candidate for persistence.

**Do not re-execute V2, do not persist Opportunity #2, and do not treat the rejected answer as a
candidate.** Mission 1.84.8 was not started.
