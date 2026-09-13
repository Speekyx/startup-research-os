# Mission 1.84.18: Second Opportunity Synthesis Execution V6

**`EXECUTION_SCHEMA_REJECTED_NO_RETRY`**

The operator approved exactly one execution of packet V6 by its digest. The approval accepted the
recorded V6 process deviation for V6 only, and renewed the residual semantic-limitation acceptance for
this one attempt only. Neither is a precedent, and both expired with the attempt. The approval was
recorded beside the packet. All 50 pre-network checks passed with no network, and **exactly one provider
request was made**.

- **The provider finished normally** (`stop_reason = tool_use`), and the forced structured output
  parsed.
- **The v1.2.0 schema refused the answer at stage 5, on one violation, and it was not a length.** The
  tool input carries a key schema v1.2.0 does not declare, `"parameter name"`, with the string value
  `"value"`, as the first of its 21 keys. All 20 declared fields are present beside it. Schema v1.2.0 is
  a closed object, so an undeclared field is refused whatever it holds.
- **No length bound was exceeded.** The summary came back at 1169 characters, within the operator's
  1500 and within the 1200 target.
- **Stages 6 to 10 were not reached.** The semantic gate v1.4.0, the evidence boundary, attribution and
  persistence eligibility never judged this answer.
- **No retry, no second request, nothing persisted, no human-review packet, and the approval is
  spent.**

```
START_COMMIT        24f12ff69c83c1ca59724dbab2859e330a5ade75
BRANCH              sprint-1/mission-1.84.18

PACKET              SECOND-OPPORTUNITY-SYNTH-EXEC-V6 v6
                    969128dd2453ab2a6907335d9386c9c3f3fac991db91c674b151c9db777aa8a9
APPROVAL            second-opportunity-synthesis-execution-approval-v6.json
                    APPROVE_EXACTLY_ONE_EXECUTION
                    file sha256                dfe8a9e69c7dfcbbcc8dcf6f849b3b22b1a93230db2f38e03f0f76eaf4701553
                    operator statement sha256  c6b6602c32815b2325c5dcc23733638567b64d2abb531ca4a5c17c23de775973
RESPONSE            second-opportunity-synthesis-response-v6.json
                    e8a13d7da4be4167162f4e45a1dc5328bbd550493386fe5dd58069897d0879c4
RECORD              second-opportunity-synthesis-execution-record-v6.json
                    77f4f27dc72d39a58175e61132b81178d85e7fefc85e7fd669c8bac438c1e6a4

PRIMARY_OUTCOME     EXECUTION_SCHEMA_REJECTED_NO_RETRY
runner code         EXECUTION_OUTPUT_REJECTED_AT_SCHEMA_VALIDATION_NO_RETRY
```

## The approval, recorded beside the packet

`second-opportunity-synthesis-execution-approval-v6.json` was written once, with an exclusive create.

**The operator's words were extracted from the message, not retyped.** The message was found exactly
once in the session's transcript, as 719 non-blank lines with digest `ba802f6e...`. Its opening lines
and sections 1 to 7 are the approval, and its sections 8 to 31 are the Mission 1.84.18 brief. The
recorded statement is the approval: the 228 lines up to the heading of section 8, with blank lines
dropped and a SHA-256 over the lines joined by a newline, as in V3's to V5's approvals. The whole
message's line count and digest are recorded beside it.

**Before anything was written, the 34 values the operator named were compared with the frozen packet**,
and any difference would have stopped the write: the identity and the decision, the provider, route
and model, thinking, the schema and its digest, the summary's hard maximum and target, the semantic gate
and its implementation digest, the freeze commit, the prompt and its digest, the representation and its
length, the token, call, retry and timeout bounds, the body length (31967), the costs and the ceiling,
human review, and no automatic persistence.

The record also carries, as data:
- **the output-contract successor**: the six things the operator understood about schema v1.2.0, and
  `V5_REVALIDATED_UNDER_V1_2_0 = false`;
- **the semantic gate v1.4.0**: the thirteen points of approved semantic intent, and
  `GATE_MODIFICATION_AFTER_APPROVAL_AUTHORISED = false`;
- **`PROCESS_DEVIATION_ACCEPTED_FOR_V6 = true`**, with its ten acknowledgements, its five reasons,
  `PRECEDENT = false`, `EXPIRES_WITH_V6_EXECUTION_AUTHORITY = true` and
  `INHERITABLE_BY_A_FUTURE_PACKET = false`;
- **`RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V6 = true`**, for this one inference attempt, with its
  six reasons, `PRE_AUTHORISES_PERSISTENCE = false` and `EXPIRES_WITH_THIS_ATTEMPT = true`;
- the 36 kinds of further authority the operator did not grant;
- `EXECUTIONS_AUTHORISED = 1`, V1's to V5's approvals not reused, `PACKET_V6_MODIFIED = false` and
  `OPPORTUNITY_PERSISTENCE_AUTHORISED = false`.

**Packet V6 was not touched.** Its digest is unchanged, and its `OPERATOR_EXECUTION_APPROVAL_RECORDED`
still reads `false`, because that field says the document records no approval. The gate 90 test that
asserted no approval file existed was re-pointed to what is now true: the approval lives beside the
packet, was recorded by this mission and names the packet's digest.

## Before any socket: the 50 checks

The 50 checks ran under a tripwire on the real transport, with the V6 runner's own verification, which
rebuilt the representation from the research database and built the request body with a transport that
refuses to send. Every one passed. Gates 77, 87, 88, 89 and 90 were re-derived in full among them. The
runner's verification then ran again as the first half of `--execute`, and matched.

| # | check | found |
|---|---|---|
| 1 | packet V6 digest | `969128dd...` |
| 2 | exactly one V6 approval exists | one approval file |
| 3 | the approval names that exact digest | the statement digest recomputes |
| 4 | decision | `APPROVE_EXACTLY_ONE_EXECUTION` |
| 5 | the process deviation accepted for V6 | true |
| 6 | the residual semantic risk renewed for V6 | true |
| 7 to 11 | V1, V2, V3, V4, V5 consumed | each refused with `EXECUTION_APPROVAL_ALREADY_CONSUMED` |
| 12 | V6 not consumed | no V6 record and no V6 response |
| 13, 14 | schema | `second-opportunity-synthesis-output@1.2.0`, `7d67bad3...` |
| 15, 16, 17 | summary bound | hard maximum 1500, target 1200, ratio `Fraction(4, 5)` |
| 18, 19 | semantic gate | `second-opportunity-output-gate@1.4.0`, implementation `eb03899b...` |
| 20 | freeze commit | `402a698` is an ancestor of HEAD and on `origin/main` |
| 21 | frozen gate test digest | `73796544...` |
| 22 | gate v1.3.0 unchanged | `cc3c4902...` |
| 23, 24, 25 | differential | 0 common-domain, 0 non-structural, 0 structural beyond the one bound |
| 26, 27 | prompt | v1.5.0, `0713eb80...` |
| 28, 29, 30 | drift | 0 unstated schema constraints, 0 unstated class-A rules, 0 unstated targets |
| 31, 32 | representation | `2528a56a...`, 3604 characters |
| 33 | persistence compatibility | `COMPATIBLE` |
| 34 | provider posture | `APPROVED` |
| 35, 36 | TED transmission / packet | `PERMITTED_WITH_CONDITIONS` / `AVAILABLE` |
| 37 | route | `POST https://api.anthropic.com/v1/messages`, no beta header |
| 38 | model | `claude-sonnet-5` |
| 39, 40 | request body | `thinking {"type": "disabled"}`, `max_tokens 128000` |
| 41, 42 | calls / retries | 1 / 0 |
| 43 | timeout | 60.0 s |
| 44 | frozen request | the body rebuilds to 31967 characters, the packet's |
| 45 | cost ceiling | 1.31706 |
| 46 | retention | ready |
| 47 | stages 6 to 9 preflight | `DETERMINISTIC_STAGE_6_TO_9_PATH_READY` |
| 48 | long-summary positive | a 1189-character summary still reaches stage 9 |
| 49 | long-summary semantic negative | still fails at stage 6 |
| 50 | canonical research state | all 14 counters as expected |

**The credential was never read, printed or written.** The runner's verification loads the local
configuration file into its own process environment, as it did for V3 to V5; the preflight printed only
whether the adapter would find a credential: `True`. The compose file was never sourced into a shell.

## The one request

```
started / finished   2026-09-13T18:59:51.437351+00:00 / 2026-09-13T19:00:24.563347+00:00
elapsed              33.126 s of a 60.0 s timeout
route                POST https://api.anthropic.com/v1/messages (synchronous)
model                claude-sonnet-5 (the response names claude-sonnet-5)
thinking             DISABLED, {"type": "disabled"}
max_tokens           128000
HTTP status          200
request id           req_011Cf1xF6ofhz7ANL8KTpLST
message id           msg_011Cf1xF7mDGyrcSEUxTZytf
```

The completion was read before anything was parsed: `stop_reason tool_use`, which the adapter's
classifier reads as `COMPLETE`.

## What came back

```
stop_reason       tool_use -> COMPLETE
input tokens      12903  (estimated 18530: the estimate covered it)
output tokens     3637   (ceiling 128000)
total tokens      16540
thinking tokens   0
cost              0.062176 = 0.025806 input + 0.03637 output   (anthropic-published-2026-09-02)
ceiling           1.31706  (the call cost about 4.7% of it)
```

The cost is derived from the usage the provider reported, at the held price, and it equals the
Gateway's telemetry. The provider's invoice is not observed. **The worst case of 1.31706 was a bound
computed before the call, and it is not what the call cost.**

Compared with V5, the call used 4 more input tokens, for a request body 4 characters longer, and 160
fewer output tokens.

## The ten stages

| stage | verdict |
|---|---|
| `1_transport_success` | PASSED |
| `2_provider_response_shape` | PASSED |
| `3_provider_completion` | PASSED |
| `4_structured_output_parse` | PASSED |
| `5_schema_validation_v1_2_0` | **FAILED** |
| `6_semantic_output_gate_v1_4_0` | NOT_REACHED |
| `7_evidence_boundary_and_no_distortion` | NOT_REACHED |
| `8_attribution_and_provenance` | NOT_REACHED |
| `9_persistence_eligibility` | NOT_REACHED |
| `10_human_review` | NOT_REACHED |

The live v1.2.0 validator's one violation, verbatim:

1. `<root>: unknown field 'parameter name'; additionalProperties is false`

**A stage that was not reached is not a stage that passed.** Stages 6 to 9 have still never judged a
real answer.

## The refusal, stated as facts

- **The undeclared key is the literal string `parameter name`, and its value is the literal string
  `value`.** It is the first of the tool input's 21 keys. The other 20 are exactly schema v1.2.0's
  declared fields, all present.
- **The string occurs nowhere in prompt v1.5.0's source, the schema modules or the V6 runner.**
- **Schema v1.2.0 inherits `additionalProperties: false` from v1.1.0**, and moves only the summary's
  bound. **Prompt v1.5.0 states the closed object in words**, rendered from the live schema: *"The
  answer is one object with exactly these 20 fields, every one required, and no other field."*
- **The answer was judged as it arrived.** The key was not removed to make the answer pass, and no
  further request was made.
- **Nothing was changed on the strength of this, and nothing is recommended here.** The schema, the
  prompt, the semantic gate and the headroom policy stay exactly as frozen, as the brief requires.

## The summary and the generation targets

```
evidence_bound_reasoning_summary    1169 characters
generation target                   1200   within
hard maximum (v1.2.0)               1500   within
schema v1.1.0's 900                 over, and it is not the V6 contract: it decides nothing here
```

Every composed text, measured in the retained answer. For an array, each element is listed.

| composed text | target | hard maximum | returned characters | within target | within hard maximum |
|---|---|---|---|---|---|
| `target_actor_if_supported` | 160 | 200 | 180 | **no** | yes |
| `observed_need` | 320 | 400 | 292 | yes | yes |
| `candidate_intervention_class` | 240 | 300 | 199 | yes | yes |
| `hypothesis_statement` | 480 | 600 | 438 | yes | yes |
| `independence_status` | 240 | 300 | 167 | yes | yes |
| `reliability_status` | 240 | 300 | 216 | yes | yes |
| `evidence_bound_reasoning_summary` | 1200 | 1500 | 1169 | yes | yes |
| `critical_uncertainties[]` | 400 | 500 | 148, 140, 118, 118, 108, 90, 109 | yes | yes |
| `commercial_claims_supported[]` | 240 | 300 | 152, 138 | yes | yes |
| `commercial_claims_not_supported[]` | 240 | 300 | 84, 94, 82, 83, 80, 80, 80, 86 | yes | yes |
| `recommended_next_evidence[]` | 240 | 300 | 125, 145, 134, 101, 114 | yes | yes |
| `statement_classifications[].statement` | 240 | 300 | 141, 147, 137, 138, 134, 101, 119, 107, 98, 91 | yes | yes |

- **11 of 12 texts are within their target, 1 is over its target and within its hard maximum, and 0 is
  over its hard maximum.** `target_actor_if_supported` came back at 180 against 160 and 200, and the
  schema did not refuse it. The targets decided nothing, as in V5.
- **The generation-target diagnostics are diagnostic only.** They are recorded, and no stage verdict
  reads them.
- **The historical v1.1.0 diagnostic is not a verdict.** Run over the same answer, schema v1.1.0 would
  report two violations: the same undeclared field, and the summary over 900. The record carries them
  with `IS_A_VERDICT = false`.

## What the refused answer said, retained as evidence and not as a candidate

The model returned `FORM_HYPOTHESIS` with confidence `EXPLORATORY` and ten classified statements:
- five `OBSERVED_OR_EVIDENCE_SUPPORTED`;
- two `HYPOTHESIS_TO_VALIDATE`;
- three `UNKNOWN_REQUIRES_EVIDENCE`.

It names three supported dimensions and eight unsupported ones, and cites six Evidence ids with five
distinct Claims, all from `public_procurement`.

**Its content was not judged**:
- the semantic gate never ran;
- no statement's support was checked;
- the residual limitation the operator accepted was not exercised.

The retained body and the parsed output are in `second-opportunity-synthesis-response-v6.json`. **The
schema refused this answer, and it is not a candidate for persistence.**

## Human review

**No human-review packet was produced.** One is produced only when stages 1 to 9 pass, and stage 5
failed. The terminal state `SECOND_OPPORTUNITY_SYNTHESIS_V6_READY_FOR_HUMAN_REVIEW` was not reached.
Gate 91 refuses a review packet for a refused answer, in the record or on disk.

## Spent, and refused by name

`second-opportunity-synthesis-execution-record-v6.json` records the approval as consumed:
`EXECUTION_APPROVAL_CONSUMED = true` and `FURTHER_CALLS_AUTHORIZED_BY_V6 = false`, with
`PROCESS_DEVIATION_ACCEPTANCE_EXPIRED = true` and `RESIDUAL_RISK_ACCEPTANCE_EXPIRED = true`.

After the record was written, the V6 runner's `--execute` was run once more. It ran in process, with
its `execute()` replaced by a function that raises and the real transport tripwired, so no request
could have left whatever the runner decided. Its verification ran, and it refused V6 at the
consumed-approval check:

```
REFUSED  nothing was sent: EXECUTION_APPROVAL_ALREADY_CONSUMED: the approval for execution packet
969128dd... records 1 provider request(s) already made.
EXIT 1 | execute reached False
```

The V1 to V5 digests are refused as before, and an unseen digest is not. V1's to V5's records,
responses and approvals are unchanged, byte for byte: gate 91 checks the 18 digests gate 87 pins.

## Retention

| retained | value |
|---|---|
| raw response | the provider's message object, 8904 characters, `4c63becd...`, recomputable from the kept body |
| request id / message id | `req_011Cf1xF6ofhz7ANL8KTpLST` / `msg_011Cf1xF7mDGyrcSEUxTZytf` |
| stop reason | `tool_use` |
| usage | the provider's usage block, identical to the Gateway's telemetry |
| parsed output | retained, `e8332db8...` |
| stage verdicts, timestamps, cost, terminal outcome | retained |
| hidden reasoning | none requested, none retained |
| credential values | none |

The normal path wrote the artifact, and the post-call fail-safe was not needed. The file carries no
credential-shaped string.

## CI gate 91

`render_second_opportunity_execution_record_v6.py` re-derives the record from what was kept:
- the raw digest, from the retained body;
- the completion, through the adapter's classifier;
- the schema verdict, by running the live v1.2.0 validator over the retained answer, and each violation's
  details: its kind, path, field, value, position, and that it is undeclared in a closed object;
- the summary against its target, its hard maximum and v1.1.0's 900, and the historical v1.1.0
  diagnostic, which may never be a verdict;
- **every composed text's length against its generation target and its hard maximum**;
- the cost, from the reported usage at the held price;
- the stage table, from those facts.

**It pins the raw response, the parsed output, the response file, the approval, the operator statement
and the record itself by digest.** The record's own pin is checked last, so every rule speaks first. An
answer with the undeclared key removed, with or without a summary cut to 900, with every digest
recomputed and the record rebound to the new file, is still refused, because it is not what arrived.

It also refuses:
- an approval that lost a word or a prohibition, or whose deviation acceptance became a precedent,
  inheritable, or live after the attempt;
- a record that says the targets decide, that the hard verdict passed, or that schema v1.1.0 is a
  verdict;
- the worst case, a rounded figure or `NOT_ESTABLISHED` in place of the reported usage and cost;
- a stage after the failure marked passed;
- a human-review packet, in the record or on disk, for a refused answer;
- V1's to V5's artifacts edited;
- a runner that would execute V1 to V6 again, or that refuses an unseen digest;
- any persistence, mutation or moved counter;
- a credential shape.

CI runs it as a new step after gate 90. **79 tests cover it**, among them the proofs section 28 asks
for.

## Post-execution safety (section 28)

| required proof | how it is proved |
|---|---|
| V6 cannot execute twice | the runner's `--execute` refuses V6 before any network, above; the tests and the probe call `refuse_if_consumed` on V6's digest and on V1's to V5's |
| the approval stays consumed after every terminal outcome | the record says so, gate 91 refuses it said otherwise, and the runner reads the record, not the outcome |
| the retained response, the approval and the record are pinned | gate 91's digests, each attacked by the tests and the probe |
| a modified or truncated output cannot become a candidate, even with digests recomputed | the undeclared key removed, alone and with the summary cut to 900, every digest recomputed and the record rebound: refused |
| V1 to V5 stay immutable | the 18 digests gate 87 pins, checked by gate 91; V5's and V1's records, V5's response and approval edited in the probe: refused |
| no failed answer gets a review packet | a review packet written to disk for this answer: refused |
| stages after a failure cannot be PASS | each of stages 6 to 10 marked passed: refused |
| canonical counters cannot move | a counter moved before or after, a mutation or a persistence recorded: refused |
| no adversarial test risks a real provider request | every runner execution in the tests and the probe had `execute()` replaced by a function that raises and the real transport tripwired |

## Probe

**95 violations caught, 0 escaped, 13 of 13 positive controls, every file proved restored.**
`VIOLATIONS_ESCAPED = 0`, `POSITIVE_CONTROLS_FAILED = 0`. No provider, token-count or network call was
made.

How they were caught:
- 94 by a rule of gate 91, or of gate 87 for the frozen gate: 71 by a specific rule, and 23 by a digest
  pin (the approval's 8, the response's 10, V1's and V5's 4 artifacts, and the one record edit no rule
  reads, a rewritten note, which the record's own pin refuses last, as designed);
- 1 by render drift.

**The families, all refused:**
- **The record** (63 cases): the approval said unused or further calls authorised; a retry, a second
  request or model call, a fallback, a continuation or a repair call; the worst case as the cost, usage
  called unestablished, tokens rounded, thinking tokens reported, the ceiling or the estimate misstated;
  each of stages 6 to 10 marked passed, the passed count grown, the failed stage moved; the violation
  dropped, the field said declared or renamed, the hard verdict said passed, a semantic verdict or
  reasons invented, the outcome made the semantic one or ready for review; the targets said to decide,
  a diagnostic softened, the summary said over its bound, schema v1.1.0 said to apply or made a verdict,
  one of its violations hidden; a review packet said produced, persistence, a mutation, a counter moved
  before or after; either acceptance said live or not accepted; 49 of 50 checks; another start commit,
  recorder, model, thinking, schema or freeze commit; the timing, the timeout, the HTTP status, the
  request and message ids, the stop reason or the TED bytes edited; credentials recorded, a credential
  shape, and the rewritten note.
- **The approval** (8 cases): its file digest is pinned, so every edit is a violation. They include a
  prohibition removed, the deviation made a precedent, the residual risk made inheritable, persistence
  authorised and one line of the statement changed.
- **The response** (10 cases). Among them is the rescue the brief forbids, done carefully and twice: the
  undeclared key removed, alone and with the summary cut to 900, every digest recomputed, the reasons
  emptied, stage 5 marked passed and the record rebound to the new file. Both are refused, because the
  pinned response is not the one that arrived.
- **History and the packet** (6 cases): V5's consumption reset, V5's answer truncated, V5's approval
  edited and V1's record edited, each refused against gate 87's pins; packet V6 with a bound field moved
  or an approval written inside it.
- **A human-review packet** written to disk for the refused answer (1 case).
- **The rendered page** hand-edited (1 case, by drift).
- **Live code, in a fresh interpreter** (6 cases): the runner without V6's own consumed guard; the runner
  consulting V4's guard instead of V5's; schema v1.2.0 opened to unknown fields; its summary bound
  lowered to 1100; the headroom ratio moved to 9/10; gate v1.4.0 edited after the execution, refused by
  gate 87.

**The positive controls:**
- the shipped gates 91 and 90;
- a comment in the V6 runner and in gate 91's tests;
- a second `--execute`, with `execute()` replaced by a function that raises and the real transport
  tripwired, refused before any network;
- V1, V2, V3, V4, V5 and V6 each refused as consumed, and an unseen digest not refused;
- the live v1.2.0 validator reproducing the one refusal, verbatim.

**One state was deliberately not constructed.** The probe did not delete V6's record and response and
then ask the runner to execute: the approval is on disk, and if the safeguards had failed there an
unapproved request would have gone out. Removing both files is a visible repository change, and gate 91
refuses it in CI.

## Accounting

```
provider requests          1
model calls                1
retries                    0
fallbacks                  0
continuations              0
repair calls               0
TED bytes sent             3604  (the approved representation, inside the 31967-character body)
provider stop reason       tool_use
HTTP status                200
elapsed                    33.126 s
input tokens               12903
output tokens              3637
thinking tokens            0
total tokens               16540
actual cost                0.062176  (ceiling 1.31706)
summary                    1169 characters (target 1200, hard maximum 1500)
generation targets         11 of 12 within; 1 over target and within bound; 0 over bound
                           (diagnostic only: no verdict reads them)
hard schema                FAILED on one undeclared field; no length bound exceeded
stages passed              4 (1 to 4)
failed stage               5_schema_validation_v1_2_0
raw response retained      true
usage retained             true
parsed output retained     true
human-review packet        not produced
Opportunity persistence    false
approval consumed          true
canonical mutation         0
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

The counters were read before the approval was written, right after the call, and again at the end.

## Verification

- `ruff format --check` and `ruff check` are clean over 1117 files, and `mypy` over 214.
- Contracts, catalog and source registry are clean.
- **3853 bare-python tests and 5444 pytest tests** pass, 13 skipped. The database is unchanged across
  29 tenant tables; the global tables are unchanged across 17, with 11 rows appended by the suites to
  1 append-only table, as the checker reports.
- **80 new tests**: 79 on gate 91 and the refusals it must make, and 1 in the gate 90 suite, which
  replaced an assertion that no V6 approval existed with the approval's real properties.
- **91 CI gates**, one of them new, all run locally with no failure.
- The canonical counters were read again at the end, and they are unchanged.

## Next

**Stop.** The one request is spent. Stage 5 failed, so nothing is persisted, no human-review packet
exists, and no further model call is made. The schema, the prompt, the semantic gate and the headroom
policy stay exactly as frozen.

The facts the operator's next decision rests on, with nothing recommended:

- **V6 is historical and spent**, and both acceptances attached to it expired with it: the process
  deviation and the residual semantic limitation. Any further execution needs a new packet digest and a
  new explicit approval naming it.
- **The operator's length decision held on this answer.** The summary came back at 1169 characters,
  within the 1500 and within the 1200 target, and no composed text exceeded its hard maximum.
- **The answer was refused on its shape, not its length.** It carried one key outside the closed
  object, `"parameter name": "value"`, beside all twenty declared fields. That string occurs in none of
  the prompt, the schema or the runner.
- **Stages 6 to 9 have still never judged a real answer.** The semantic gate v1.4.0 has judged only
  synthetic answers.
- **One call is one observation.** It establishes that this answer carried an undeclared key, and
  nothing about how often any answer would.

**Do not execute anything, do not re-execute V1 to V6, do not treat the refused answer as a candidate,
and do not persist Opportunity #2.** Mission 1.84.19 was not started.
