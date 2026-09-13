# Mission 1.84.13: Second Opportunity Synthesis Execution V4

**`EXECUTION_SCHEMA_REJECTED_NO_RETRY`**

The operator approved exactly one execution of packet V4 by its digest, and accepted one documented
residual limitation for that one execution. The approval was recorded beside the packet. All 28
pre-network checks passed with no network, and **exactly one provider request was made**.

- **The provider finished normally** (`stop_reason = tool_use`), and the forced structured output
  parsed.
- **The v1.1.0 schema then refused the answer at stage 5.** Two fields exceed length bounds that prompt
  v1.3.0 states in words: the same bounds prompt v1.2.0 stated, and V3 met.
- **Stages 6 to 10 were not reached.** The semantic gate v1.3.0, the evidence boundary, attribution and
  persistence eligibility never judged this answer.
- **No retry, no second request, nothing persisted, no human-review packet, and the approval is
  spent.**

```
START_COMMIT        eae936b76e9aa0144b253fe227822ac0fe9f90d0
BRANCH              sprint-1/mission-1.84.13

APPROVAL            second-opportunity-synthesis-execution-approval-v4.json
                    APPROVE_EXACTLY_ONE_EXECUTION of SECOND-OPPORTUNITY-SYNTH-EXEC-V4 v4
                    7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b
                    file sha256                c5cb608e4cf5aac6698ebec005658184e173518bb0ea719ba7e25185d5a73957
                    operator statement sha256  064b87fce76a5fbbc29ca7b77dc68e0ce13cc661928b2a8f99a94be231488c92

PRIMARY_OUTCOME     EXECUTION_SCHEMA_REJECTED_NO_RETRY
runner code         EXECUTION_OUTPUT_REJECTED_AT_SCHEMA_VALIDATION_NO_RETRY
```

## The approval, recorded beside the packet

`second-opportunity-synthesis-execution-approval-v4.json` was written once, with an exclusive create.

**The operator's words were extracted from the message, not retyped.** The message was found exactly
once in the session's transcript, as 605 non-blank lines with digest `37ce61d5...`. Its opening lines
and sections 1 to 3 are the approval, and its sections 4 to 26 are the Mission 1.84.13 brief. The
recorded statement is the approval: the 160 lines up to the heading of section 4, with blank lines
dropped and a SHA-256 over the lines joined by a newline, as in V3's approval. The whole message's line
count and digest are recorded beside it.

**Before anything was written, the 30 values the operator named were compared with the frozen packet**,
and any difference would have stopped the write. They cover:
- the identity and the decision;
- the provider, route and model;
- thinking and its request value;
- the subject;
- the schema and its digest;
- the semantic gate and its implementation digest;
- the prompt and its digest;
- the representation and its length;
- the token, call, retry and timeout bounds;
- the prepared body length and the input estimate;
- the three worst-case costs and the ceiling;
- human review, and no automatic persistence.

The record also carries, as data:
- the residual-risk acceptance, bounded to this ONE execution, with the five things it does not
  authorise;
- the 13 things no change was approved to;
- the 34 prohibitions.

**Packet V4 was not touched.** Its digest is unchanged, and its `OPERATOR_EXECUTION_APPROVAL_RECORDED`
still reads `false`, because that field says the document records no approval. Gate 81 accepts the
approval because a later mission recorded it and it names V4's digest.

## Before any socket (§5)

The 28 checks ran with the runner's own verification, which rebuilt the representation from the
research database and built the request body with a transport that refuses to send. They ran under a
tripwire on the real transport, and every one passed. The runner's verification then ran again as the
first half of `--execute`.

| # | check | found |
|---|---|---|
| 1 | packet V4 digest | `7832b3bc...`, recomputed from the bound fields and equal to the runner's pin |
| 2 | approval exists exactly once | one approval file names V4's digest |
| 3 | approval names that digest | `APPROVE_EXACTLY_ONE_EXECUTION`; the statement digest recomputes |
| 4, 5, 6 | V1, V2, V3 consumed | each refused with `EXECUTION_APPROVAL_ALREADY_CONSUMED` |
| 7 | V4 not consumed | no V4 record and no V4 response |
| 8 | schema | `second-opportunity-synthesis-output@1.1.0`, `ec789d1b...` |
| 9 | semantic gate | `second-opportunity-output-gate@1.3.0`, implementation `cc3c4902...` |
| 10 | prompt | v1.3.0, `a62fa218...`, rendered and hashed |
| 11, 12 | drift | 0 unstated class-A semantic rules, 0 unstated schema constraints |
| 13, 14 | representation | `2528a56a...`, 3604 characters |
| 15 | provider posture | `APPROVED` |
| 16, 17 | TED transmission / packet | `PERMITTED_WITH_CONDITIONS` / `AVAILABLE` |
| 18 | route | `POST https://api.anthropic.com/v1/messages`: synchronous, no beta header, not streamed; batches and the subscription route not used |
| 19 | model | `claude-sonnet-5`, in the packet and in the body |
| 20, 21 | request body | `thinking {"type": "disabled"}`, `max_tokens 128000`, 27946 characters |
| 22, 23 | calls / retries | 1 / 0 (and 0 in the request) |
| 24 | timeout | 60.0 s |
| 25, 26 | cost | worst case 1.312398 = ceiling |
| 27 | retention | ready |
| 28 | stages 6 to 9 preflight | `DETERMINISTIC_STAGE_6_TO_9_PATH_READY`; gates 79, 80 and 81 validate |

**The credential was never read, printed or written.**
- The runner's own verification loads the local configuration file into its process environment,
  without overriding anything already set. It did the same for V3.
- The preflight printed only whether the adapter would find a credential: `True`.
- The 105 runner and renderer tests were green before the call.

## The one request

```
started / finished   2026-09-13T09:31:58.559005+00:00 / 2026-09-13T09:32:32.687770+00:00
elapsed              34.129 s of a 60.0 s timeout
route                POST https://api.anthropic.com/v1/messages (synchronous)
model                claude-sonnet-5 (the response names claude-sonnet-5)
thinking             DISABLED, {"type": "disabled"}
max_tokens           128000
HTTP status          200
request id           req_011Cf1CwSkhuKpPHFCPSP26m
message id           msg_011Cf1CwTa5ggGGhyRmDvF7d
```

## What came back

```
stop_reason       tool_use -> COMPLETE
input tokens      11599  (estimated 16199: the estimate covered it)
output tokens     3950   (ceiling 128000)
total tokens      15549
thinking tokens   0
cost              0.062698 = 0.023198 input + 0.0395 output   (anthropic-published-2026-09-02)
ceiling           1.312398  (the call cost about 4.8% of it)
```

The cost is derived from the usage the provider reported, at the held price, and it equals the
Gateway's telemetry. The provider's invoice is not observed. **The worst case of 1.312398 was a bound
computed before the call, and it is not what the call cost.**

Compared with V3, the call used:
- 2108 more input tokens, for the 5822 characters prompt v1.3.0 adds;
- 70 more output tokens.

## The ten stages

| stage | verdict |
|---|---|
| `1_transport_success` | PASSED |
| `2_provider_response_shape` | PASSED |
| `3_provider_completion` | PASSED |
| `4_structured_output_parse` | PASSED |
| `5_schema_validation_v1_1_0` | **FAILED** |
| `6_semantic_output_gate_v1_3_0` | NOT_REACHED |
| `7_evidence_boundary_and_no_distortion` | NOT_REACHED |
| `8_attribution_and_provenance` | NOT_REACHED |
| `9_persistence_eligibility` | NOT_REACHED |
| `10_human_review` | NOT_REACHED |

The live v1.1.0 validator's two violations, verbatim:

1. `candidate_intervention_class: 316 characters exceeds maxLength 300`
2. `evidence_bound_reasoning_summary: 1078 characters exceeds maxLength 900`

**A stage that was not reached is not a stage that passed.** Stages 6 to 9 have still never judged a
real answer.

## What the refusal is, stated as facts

| field | characters | bound | over by | stated in prompt v1.3.0 | stated in v1.2.0 | V3 |
|---|---|---|---|---|---|---|
| `candidate_intervention_class` | 316 | 300 | 16 | yes | yes | 224 |
| `evidence_bound_reasoning_summary` | 1078 | 900 | 178 | yes | yes | 868 |

- **Both bounds were stated in words.** The output-contract block of prompt v1.3.0 is byte-identical
  to v1.2.0's, and it says "at most 300 characters" under `candidate_intervention_class` and "at most
  900 characters" under `evidence_bound_reasoning_summary`. Gate 82 re-derives both facts from the
  live renderer's own explicitness test.
- **V3 met both bounds, under prompt v1.2.0.** V4's answer is longer in the prose fields: the summary
  is 1078 characters against V3's 868, and `observed_need` 331 against 276.
- **The answer was judged as it arrived.** Nothing truncated, rewrote, split or dropped anything to
  fit, and no further request was made.
- **Nothing was changed on the strength of any of this, and nothing is recommended here.** The prompt,
  the schema and the gate stay exactly as frozen, as the approval requires.

## What the refused answer said, retained as evidence and not as a candidate

The model returned `FORM_HYPOTHESIS` with confidence `EXPLORATORY` and twelve classified statements:
- five `OBSERVED_OR_EVIDENCE_SUPPORTED`;
- two `HYPOTHESIS_TO_VALIDATE`;
- five `UNKNOWN_REQUIRES_EVIDENCE`.

**Its content was not judged**:
- the semantic gate never ran;
- no statement's support was checked;
- the residual limitation the operator accepted was not exercised.

The retained body and the parsed output are in `second-opportunity-synthesis-response-v4.json`. **The
schema refused this answer, and it is not a candidate for persistence.**

## Human review (§14 to §16)

**No human-review packet was produced.** One is produced only when stages 1 to 9 pass, and stage 5
failed. The residual-limitation notice in §16 belongs in a review packet that does not exist, so it is
not recorded as one. The acceptance itself is recorded in the approval, bounded to this execution.
Gate 82 refuses a review packet for a refused answer.

## Spent, and refused by name (§18)

`second-opportunity-synthesis-execution-record-v4.json` records the approval as consumed:
`EXECUTION_APPROVAL_CONSUMED = true`, `FURTHER_CALLS_AUTHORIZED_BY_V4 = false`. After the record was
written, `--execute` was run once more. The runner refused V4 before any network, at its verification's
consumed-approval check:

```
REFUSED  nothing was sent: EXECUTION_APPROVAL_ALREADY_CONSUMED: the approval for execution packet
7832b3bc... records 1 provider request(s) already made.
```

The V1, V2 and V3 digests are refused as before, and an unseen digest is not. V1's, V2's and V3's
records are unchanged, byte for byte, and gate 82 pins all three.

## Retention (§17)

| retained | value |
|---|---|
| raw response | the provider's message object, 9610 characters, `b526c540...`, recomputable from the kept body |
| request id / message id | `req_011Cf1CwSkhuKpPHFCPSP26m` / `msg_011Cf1CwTa5ggGGhyRmDvF7d` |
| stop reason | `tool_use` |
| usage | the provider's usage block, identical to the Gateway's telemetry |
| parsed output | retained, `2c30d7eb...` |
| stage verdicts, timestamps, cost, terminal outcome | retained |
| hidden reasoning | none requested, none retained |
| credential values | none |

The normal path wrote the artifact, and the post-call fail-safe was not needed. The file carries no
credential-shaped string.

## CI gate 82

`render_second_opportunity_execution_record_v4.py` re-derives the record from what was kept:
- the raw digest, from the retained body;
- the completion, through the adapter's classifier;
- the schema verdict, by running the live v1.1.0 validator over the retained answer;
- each violation's length, measured again and looked up in both prompts;
- the cost, from the reported usage at the held price;
- the stage table, from those facts.

**It pins the raw response, the parsed output and the approval by digest.** A rewrite that trims both
fields and recomputes every digest is still refused, because it is not what arrived.

It also refuses:
- an approval that lost a word, a prohibition, a withheld change or its residual-risk bounds;
- the worst case, a rounded figure or `NOT_ESTABLISHED` in place of the reported usage and cost;
- a stage after the failure marked passed;
- a human-review packet, in the record or on disk, for a refused answer;
- V1's, V2's or V3's record edited or unspent;
- a runner that would execute V1 to V4 again;
- any persistence, mutation or moved counter;
- a credential shape.

31 tests cover it.

## Probe (§23)

**116 violations caught, 0 escaped, 9 of 9 positive controls, every file proved restored.**
`VIOLATIONS_ESCAPED = 0`, `POSITIVE_CONTROLS_FAILED = 0`.

How they were caught:
- 109 by gate 82's own rules, or gate 79's for V3's response;
- 6 by the runner itself;
- 1 by render drift.

**The runner's six refusals, with no request possible.** For the two `--execute` runs, the runner's
`execute()` was replaced by a function that raises, and the real transport was tripwired, so no request
could leave whatever the runner decided. Neither was reached.
- V1, V2, V3 and V4 are each refused with `EXECUTION_APPROVAL_ALREADY_CONSUMED`.
- `--execute` on the shipped state is refused with the same code.
- `--execute` with V4's record deleted and its response kept is refused with
  `EXECUTION_ALREADY_PERFORMED`.

**The families, all refused:**
- **The record** (69 cases):
  - the approval unspent, further calls authorised;
  - a second request, a second call, a retry, a fallback, a continuation, a repair;
  - another route, beta header, model, thinking policy, `max_tokens` or timeout;
  - another prompt, schema, gate or representation;
  - the worst case, a rounded figure or `NOT_ESTABLISHED` in place of the usage and the cost;
  - thinking tokens reported;
  - the timing, the status, the ids, the stop reason or the completion changed;
  - another raw, parsed or file digest;
  - each stage from 5 to 10 marked passed, and the passed count raised;
  - a violation dropped or softened, or its bound said to be unstated;
  - a semantic verdict or reason invented;
  - a review packet, a ready outcome, persistence, a mutation or a moved counter;
  - V3's record digest, the approval block, another packet;
  - a credential shape.
- **The approval** (16 cases): its file digest is pinned, so every edit is a violation, even a
  reworded comment, and each was caught.
- **The response** (13 cases). Among them is the rescue the operator forbade, done carefully: both
  fields trimmed to their bounds, every digest recomputed, the reasons emptied and the record rebound
  to the new file. It is refused, because the pinned raw response and parsed output are not the ones
  that arrived.
- **History** (7 cases): V1's, V2's and V3's consumption reset; a V3 review packet; V3's reasons
  trimmed; packet V4 with an approval written inside, or with a bound field edited.
- **A human-review packet** written to disk for the refused answer (1 case).
- **Live code, in a fresh interpreter** (3 cases): the summary bound raised in the schema; the runner
  blind to V4's record; the runner reading V4's record from elsewhere.

**The positive controls:**
- the shipped gates 79, 81 and 82;
- the record's `$comment` and three of its notes, which gate 82 does not pin;
- a comment in gate 82's tests;
- an unseen digest, which is not refused.

**One state was deliberately not constructed.** With an approval on disk, the runner refuses V4
through two committed files: its record and its response. The probe did not delete both and then ask
the runner to execute, because if its safeguards had failed there, an unapproved request would have
gone out. Removing both files is a visible repository change, and gate 82 refuses it in CI.

## Accounting (§20)

```
provider requests          1
model calls                1
retries                    0
fallbacks                  0
continuations              0
repair calls               0
TED bytes sent             3604  (the approved representation, inside the 27946-character body)
provider stop reason       tool_use
input tokens               11599
output tokens              3950
thinking tokens            0
total tokens               15549
actual cost                0.062698
stages passed              4 (1 to 4)
failed stage               5_schema_validation_v1_1_0
raw response retained      true
usage retained             true
parsed output retained     true
Opportunity persistence    false
canonical mutation         0
```

## Canonical state (§19)

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

- `ruff format --check` and `ruff check` are clean over 1074 files, and `mypy` over 209.
- Contracts, catalog and source registry are clean.
- **3853 bare-python tests and 4843 pytest tests** pass, 13 skipped, with the database unchanged
  across 29 tenant tables.
- **31 new tests**, on gate 82 and the refusals it must make.
- **82 CI gates**, one of them new, all run locally with no failure.
- The canonical counters were read again at the end, and they are unchanged.

## Next (§26)

**Stop.** The one request is spent. Stage 5 failed, so nothing is persisted, no human-review packet
exists, and no further model call is made. The prompt, the schema and the gate stay exactly as frozen.

The facts the operator's next decision rests on, with nothing recommended:

- **V4 is historical and spent.** Any further execution needs a new packet digest and a new explicit
  approval naming it.
- **The stated length bounds were not met on this call.** Prompt v1.3.0 stated them exactly as v1.2.0
  did, which V3 met.
- **Stages 6 to 9 have still never judged a real answer.** The semantic gate v1.3.0 has judged only
  V3's historical answer, diagnostically.
- **One call is one observation.** It establishes that this answer was refused on two length bounds,
  and nothing about how often any prompt meets them.

**Do not execute anything, do not re-execute V1, V2, V3 or V4, do not treat the refused answer as a
candidate, and do not persist Opportunity #2.** Mission 1.84.14 was not started.
