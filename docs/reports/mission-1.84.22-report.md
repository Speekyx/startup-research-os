# Mission 1.84.22: Second Opportunity Synthesis Execution V9

**`EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY`**

The operator approved exactly one execution of packet V9 and accepted, for V9 only, the two risks the
packet had left open: the residual semantic limitation of gate v1.4.0, and the first strict request's
timeout risk. The approval was recorded beside the packet, the 58 pre-network checks passed under a
tripwire, and the one request was made.

- **The provider finished normally.** HTTP 200 in 54.585 s of the 240-second budget, `stop_reason
  tool_use`, and the forced strict tool call parsed.
- **The full schema passed the answer, for the first time since V3.** Exactly the 20 declared root
  keys, no undeclared key, no length bound exceeded.
- **Gate v1.4.0 refused it at stage 6**, on seven reasons over two fields: the word *market* in
  `candidate_intervention_class`, which no supplied statement contains, and all six items of
  `recommended_next_evidence`, written as imperatives the gate does not read as requests.
- **Nothing after the failure ran, and nothing was persisted.** Stages 7 to 10 NOT_REACHED, no
  human-review packet, no retry. The approval and both acceptances are spent, and a second `--execute`
  is refused before any network.
- **It cost 0.062326**, from the reported usage at the held price. The planning estimate (1.316316) and
  the hard ceiling (3.608) were computed before the call, and neither is what it cost.

```
START_COMMIT        5426643d50449a323d416d666486d6cf599a151a
BRANCH              sprint-1/mission-1.84.22

PACKET              SECOND-OPPORTUNITY-SYNTH-EXEC-V9 v9
                    ba681da94b3e89f22c7e39bdb2dc4ef95d0527ca3db561c849eb089652d9425d
APPROVAL            docs/data/second-opportunity-synthesis-execution-approval-v9.json
  file              86f73a61ca8178be3a43708c5e775789c5ffc5a7bb32187f032c8f188ab59854
  statement         de5ee683f0e6a1c64bdc20e04be78a681609e03e8267a1b7754539b4b226c17b
RESIDUAL SEMANTIC RISK ACCEPTED        true, for V9 only; expired with the attempt
STRICT TIMEOUT RISK ACCEPTED           true, for V9 only; expired with the attempt

PRIMARY_OUTCOME     EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY
```

## The approval

The operator's message was extracted by a script rather than retyped: one message, 663 lines
(`5eade97c...`). The approval is every line up to the heading of its section 7, which opens the
mission's instructions: 202 lines, `de5ee683...`, stored verbatim with its lines and its digest.

Before anything was written, 54 values the operator named were compared with the frozen packet and the
predecessor records: the identity, version, digest and decision; the provider, route, model and
thinking; strict mode, mechanism, projection, capability profile and freeze commit; schema, gate and
prompt; the representation's digest and length; the summary bound, target and ratio; max_tokens, model
calls, retries and the 240-second timeout; the body's length and digest; the planning estimate, the
ceiling and its proof; human review and persistence; V1 to V6 consumed, V7 and V8 superseded; the
180-second compilation timeout, the unestablished compilation latency and end-to-end bound, the
uneliminated timeout risk; both acceptances, `V9_ONLY = true` and `INHERITABLE_BY_FUTURE_PACKET = false`.
All 54 matched. The file was written with an exclusive create, and packet V9 still records no approval
(`OPERATOR_EXECUTION_APPROVAL_RECORDED = false`, digest unchanged).

The record carries the residual-risk acceptance with its eight reasons, the timeout-risk acceptance
with what it acknowledges and the four things the 240 seconds are not, the cost acceptance, the 14
prohibitions of the operator's opening paragraph, and `EXECUTIONS_AUTHORISED = 1`.

## Pre-network checks: 58 of 58

Run by a script under a tripwire on `UrllibTransport` and `urllib.request.urlopen`, with the V9 runner's
own verification against the research database, and gates 92, 94, 96 and 97 re-derived in full with the
approval on disk. No tripwire fired.

```
 1 packet id SECOND-OPPORTUNITY-SYNTH-EXEC-V9           30 representation 2528a56a...
 2 packet version 9                                     31 representation 3604 characters
 3 packet digest ba681da9...                            32 provider posture APPROVED
 4 exactly one V9 approval                              33 TED transmission PERMITTED_WITH_CONDITIONS
 5 it names that digest, statement recomputes           34 synchronous Messages API, no beta header
 6 APPROVE_EXACTLY_ONE_EXECUTION                        35 claude-sonnet-5
 7 residual risk accepted for V9                        36 thinking {"type": "disabled"}
 8 strict timeout risk accepted for V9                  37 max_tokens 128000
 9 V1 to V6 refused as consumed                         38 MAX_MODEL_CALLS 1
10 V7 superseded before execution                       39 MAX_RETRIES 0, and 0 in the built request
11 V8 superseded before execution                       40 REQUEST_TIMEOUT 240.0
12 V9 not executed, not consumed                        41 the built request carries 240.0
13 schema second-opportunity-synthesis-output@1.2.0     42 the gateway hands 240.0 to the transport,
14 schema digest 7d67bad3...                               and the transport to urlopen
15 gate second-opportunity-output-gate@1.4.0            43 no gateway cap at 60 (the deployment's 60
16 gate digest eb03899b..., freeze 402a698 ancestor        is not read on this path)
17 prompt second-opportunity-synthesis-prompt@1.5.0     44 body 31326 characters
18 prompt digest 0713eb80...                            45 body 58956019...
19 strict mode, FROZEN_PROJECTION_STRICT_FORCED         46 no timeout field in the body
20 projection 87028f45...                               47 planning estimate 1.316316
21 capability profile 7f3ed845...                       48 hard ceiling 3.608
22 strict freeze 57154af                                49 the ceiling still proven
23 freeze an ancestor of origin/main (fetched)          50 retention ready
24 projected root = the canonical 20 properties         51 stages 5 to 9 preflight ready
25 additionalProperties false at every object           52 a valid synthetic answer reaches stage 9
26 stage 5 is the full v1.2.0 schema, locally           53 1189 characters reaches stage 9
27 summary hard maximum 1500                            54 1500 characters reaches stage 9
28 summary target 1200                                  55 1501 characters stops at stage 5
29 generation ratio 4/5                                 56 an extra root property stops at stage 5
                                                        57 a strict-shaped semantic failure stops at 6
                                                        58 canonical counters unchanged
```

Check 42 was made through the real gateway and the real strict adapter into a capturing transport that
sent nothing, plus a source check that `UrllibTransport.post_json` passes `timeout=timeout_seconds` to
`urlopen`. No real transport was constructed before the one request.

## The one request

```
command                uv run python infrastructure/scripts/run_second_opportunity_execution_v9.py --execute
verification           the runner's own, again, inside --execute: every finding matched, approval RECORDED
provider requests      1        model calls 1        retries 0
fallbacks              0        continuations 0      repair calls 0
route                  POST https://api.anthropic.com/v1/messages, synchronous
model                  claude-sonnet-5 (response: claude-sonnet-5)
thinking               DISABLED, {"type": "disabled"}
strict                 forced tool, strict true, projection 87028f45...
max_tokens             128000
timeout                240.0 s, no retry
request body           31326 characters, 58956019...
started / finished     2026-09-14T17:15:30.971852+00:00 / 2026-09-14T17:16:25.557099+00:00
elapsed                54.585 s (timed out: false)
HTTP status            200
request id             req_011Cf3i6YT9CBbCz4JmhzdGC
message id             msg_011Cf3i6Yy9xeEhPkQodYGei
stop_reason            tool_use -> COMPLETE
```

**Completion was read before parsing.** `stop_reason tool_use` is the only complete value for a forced
tool; `max_tokens`, `model_context_window_exceeded`, `refusal` or any other value would have stopped
the answer at stage 3, unparsed.

## What came back

```
input tokens           12493 (planning estimate 18158; covered: true)
output tokens          3734
thinking tokens        0
total tokens           16227
service tier           standard
inference geo          global (the US-only 1.1 multiplier does not apply)
cache tokens           created 0, read 0
```

**Strict mode, observed?** The request carried the forced tool with `strict: true` over the frozen
projection. The answer arrived with exactly the 20 root keys schema v1.2.0 declares, and no other:
**unknown root properties returned: none**. The full v1.2.0 validator, run locally at stage 5, found no
violation. That strict decoding caused this is not established: one answer is one observation.

## The ten stages

| stage | verdict |
|---|---|
| `1_transport_success` | PASSED |
| `2_provider_response_shape` | PASSED |
| `3_provider_completion` | PASSED |
| `4_structured_output_parse` | PASSED |
| `5_schema_validation_v1_2_0` | PASSED |
| `6_semantic_output_gate_v1_4_0` | FAILED |
| `7_evidence_boundary_and_no_distortion` | NOT_REACHED |
| `8_attribution_and_provenance` | NOT_REACHED |
| `9_persistence_eligibility` | NOT_REACHED |
| `10_human_review` | NOT_REACHED |

A stage that was not reached is not a stage that passed.

## What refused it

Gate v1.4.0's seven reasons, as the execution retained them:

```
candidate_intervention_class audited UNSUPPORTED: 'market' appears in no source content statement,
  compared under opportunity-lexical-inflection@1.0.0; prior knowledge is not available as factual
  support (§7)
recommended_next_evidence[0..5] audited BOUND_EXCEEDED: it is not request-shaped, so it is read as the
  assertion it has become. A FUTURE_EVIDENCE_REQUEST names what would have to be observed
recommended_next_evidence[3] also: ['confirmed'] promote a FUTURE_EVIDENCE_REQUEST to a conclusion
```

Measured again against the answer by gate 98:

| field | what it says | measured |
|---|---|---|
| `candidate_intervention_class` | *An information or analytics offering that aggregates and compares published CPV-9261 procurement notice values for contracting-authority or market-intelligence audiences* | *market* is in the text and in no supplied statement |
| `recommended_next_evidence[0]` | *Identify whether the same contracting authority appears across multiple notices over time to test recurrence.* | opens with *Identify*; not request-shaped |
| `recommended_next_evidence[1]` | *Obtain buyer-level detail (identity, sector, stated purpose) for notices in this CPV class.* | opens with *Obtain* |
| `recommended_next_evidence[2]` | *Observe whether any contracting authority has published a stated problem, requirement, or complaint related to this CPV class.* | opens with *Observe* |
| `recommended_next_evidence[3]` | *Determine whether TOTAL_VALUE figures in this packet were later confirmed as awarded/paid amounts via award outcome or payment records.* | opens with *Determine*; carries *confirmed* |
| `recommended_next_evidence[4]` | *Identify any existing suppliers or contract awardees associated with these notices to assess competitive supply.* | opens with *Identify* |
| `recommended_next_evidence[5]` | *Observe time-series notice volume or value across multiple periods to assess trend or change.* | opens with *Observe* |

The gate reads an item as a request only when it opens with the evidence or observation it names
(*evidence of*, *observation of*, *identification of* and the like); an imperative is read as the
assertion it has become. Prompt v1.5.0 states each rule the gate applied here in words: that prior
knowledge is unavailable as factual support; that `recommended_next_evidence` names what would have to
be observed; that each item *names the evidence or observation that would have to be obtained, and
states no finding*; and that *no adverb of certainty and no wording of confirmation turns one into a
conclusion*.

**Recorded as facts for the operator, with nothing changed on the strength of them and nothing
recommended.** The schema, the gate, the prompt, the strict projection and the timeout stay exactly as
frozen, the answer was not rewritten, and no further request was made.

## The reasoning summary and the targets

```
summary characters     1145
generation target      1200 (within)
hard maximum           1500 (within)
```

Of the twelve composed texts, ten are within their generation target and two are over it and within
their hard maximum (`observed_need` 357 against 320 and 400; `hypothesis_statement` 507 against 480 and
600). None is over a hard maximum, and a target decided nothing.

## Cost accounting

```
PLANNING_COST_ESTIMATE          1.316316   computed before the call; not incurred
HARD_EXECUTION_COST_CEILING     3.608      proven before the call; not incurred
ACTUAL_USAGE                    12493 in, 3734 out, 0 thinking, 16227 total, from the provider
ACTUAL_COST                     0.062326   = 0.024986 input + 0.03734 output, x1, at the held price
ACTUAL_COST <= 3.608            true
BILLED CATEGORY CONTRADICTIONS  none
```

The usage reports service tier `standard`, `inference_geo global`, no cache tokens and no thinking
tokens: every billed category the ceiling was proven under, and none it was not. The ceiling carries the
1.1 US-only multiplier because the workspace default was not visible from the repository; the response
reports `global`, to which that multiplier does not apply. The cost equals the Gateway's telemetry. The
provider's invoice is not observed.

## Retention

The runner wrote `docs/data/second-opportunity-synthesis-response-v9.json` through its normal path, and
the post-call fail-safe was not needed: the raw provider response (`4fe8da96...`, 9218 characters,
recomputable from the kept body), the request id and message id, the stop reason, the usage block, the
parsed answer (`f6ce54b2...`), the timestamps and elapsed time, the stage table and the terminal outcome.
No hidden reasoning was requested or kept, and no credential value is in any file.

## The approval is spent

`docs/data/second-opportunity-synthesis-execution-record-v9.json` records
`EXECUTION_APPROVAL_CONSUMED = true` and `FURTHER_CALLS_AUTHORIZED_BY_V9 = false`, and both acceptances
expired with the attempt. The V9 runner now refuses V9's digest as
`EXECUTION_APPROVAL_ALREADY_CONSUMED`, and its `--execute` stops at that refusal, in its own verification,
before the database is read and before any transport. The guard reads only the record's consumption
flag and digest, so it refuses whatever the terminal outcome: shown for all 16 outcome codes.

## Canonical state

| counter | before | after |
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

Opportunity #2 was not persisted. No human-review packet exists, because stage 6 failed.

## Gate 98

`infrastructure/scripts/render_second_opportunity_execution_record_v9.py`, and its page. It re-derives
the record from what was retained and refuses:

- a record that disagrees with the retained raw response, the parsed answer or the approval, each pinned
  by digest, so an answer rewritten to pass, with every digest recomputed and the record rebound, is
  still refused;
- a stage table that is not what the facts imply. **CI holds no database, so stages 6 to 10 are
  replayed**: the V9 runner's own `validate_execution` runs again over the retained answer under a
  transport tripwire, with the packet rebuilt from Mission 1.84.10's authenticated snapshot, whose
  representation, rendered prompt, trusted context and source-metadata channel must match V9's digests.
  The stage table and all seven reasons come back exactly;
- a semantic refusal that does not measure: a term refused as unsupported must be in the refused text
  and in no supplied statement, an item refused as not request-shaped must not be request-shaped;
- a stage after the failure marked anything but NOT_REACHED, a review packet for a refused answer, a
  ready outcome;
- a cost other than the reported usage at the held price, a cost over the ceiling, and any billed
  category the ceiling was not proven under;
- the approval marked unused, a second request, a retry, a fallback, a continuation or a repair;
- V1 to V6 edited or reset (held to gate 91), V7 or V8 restored, approved or run;
- a runner that would execute V9 again, or whose `--execute` reaches a transport;
- a record, approval or response that is missing, a canonical counter that moved, or a credential shape.

## A defect found in this mission's own gate

Writing the probe's cases found that gate 98 crashed on a missing record instead of refusing it: its
first line loaded the record. The record is the one file the runner's guard reads to see V9 spent, so
its absence is the case that matters most. `validate()` now refuses a missing record, approval or
response by name before anything else, with three tests and a probe case. Without the record,
`--execute` is still refused before any network because the response exists
(`EXECUTION_ALREADY_PERFORMED`), and the probe shows that too.

## Tests re-pointed, and why

Three tests asserted that no V9 approval existed, which was true until the operator gave one. Each was
re-pointed to the property that mattered, never deleted:

- `test_second_opportunity_execution_v9.py`: `test_the_committed_approval_file_does_not_exist` became
  `test_the_committed_approval_names_v9_and_decides_both_risks`;
- `test_second_opportunity_execution_packet_v9.py`: `test_no_approval_exists_beside_the_packet` became
  `test_the_approval_beside_the_packet_is_a_later_missions`;
- `test_second_opportunity_execution_packet_v9.py`: `test_the_shipped_approval_check_decides_both_risks`
  now asserts that the committed approval is left byte for byte as it was, where it asserted there was
  none.

## Post-execution safety

| proof | where |
|---|---|
| V9 cannot execute twice | gate 98 (`refuse_if_consumed` and `--execute` under a tripwire), tests, probe |
| the approval stays consumed after every terminal outcome | tests and probe, 16 outcome codes |
| approval, response and record pinned | gate 98 |
| rewriting the output cannot rescue it | gate 98, a test and a probe case with every digest recomputed |
| V1 to V6 immutable and consumed | gate 98 through gate 91, tests, probe |
| V7 and V8 superseded | gate 98, tests, probe |
| a failed answer gets no review | gate 98, tests, probe |
| no stage after the failure can pass | gate 98's rule, tests, probe |
| canonical counters cannot move | gate 98, probe (read from the database) |

No adversarial test could make a second request: every process had the real transport and urlopen
tripwired, and `--execute` ran with `execute()` itself replaced by a raiser.

## Tests, CI gates, probe

```
bare-python tests      3877, across 9 packages
pytest                 6291 passed, 13 skipped, across 9 packages; the database unchanged by the run
new tests              81, in gate 98's test file; 3 re-pointed
CI gates               98 (gate 98 added after gate 97), all passing locally
ruff, format, mypy     clean
probe                  92 violations caught (91 by rule, 1 by drift), 0 escaped; 25 of 25 positive
                       controls; every file restored and proved; no transport constructed in any
                       process; one run, 191 s
```

## Files

```
docs/data/second-opportunity-synthesis-execution-approval-v9.json    new, the operator's approval
docs/data/second-opportunity-synthesis-response-v9.json              new, written by the runner
docs/data/second-opportunity-synthesis-execution-record-v9.json      new, the execution record
docs/data/second-opportunity-synthesis-execution-record-v9.md        new, rendered by gate 98
infrastructure/scripts/render_second_opportunity_execution_record_v9.py   new, CI gate 98
packages/opportunity-engine/python/tests/test_second_opportunity_execution_record_v9.py   new
packages/opportunity-engine/python/tests/test_second_opportunity_execution_v9.py          re-pointed
packages/opportunity-engine/python/tests/test_second_opportunity_execution_packet_v9.py   re-pointed
.github/workflows/ci.yml                                             gate 98 step
PROJECT_MANIFEST.md (1.156), docs/CLAUDE.md (1.157), this report
```

Packet V9, the runners, the gates before 98, the schema, gate v1.4.0, prompt v1.5.0 and the strict
projection are byte-identical.

## Next

**An operator decision, and nothing was started.** V9 is spent. Any further execution needs a new packet
digest and a new explicit approval naming it. One call establishes that this answer named a word no
statement supplies and wrote its next-evidence items as imperatives, and nothing about how often any
answer would. Whether anything changes first is the operator's to decide, and this mission implemented
and recommended nothing. **Do not re-execute V1 to V9, do not rewrite or rescue the refused answer, do
not treat it as a candidate, and do not persist Opportunity #2.** Mission 1.84.23 was not started.
