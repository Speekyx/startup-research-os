# Mission 1.84.15: Second Opportunity Synthesis Execution V5

**`EXECUTION_SCHEMA_REJECTED_NO_RETRY`**

The operator approved exactly one execution of packet V5 by its digest. They accepted the
generation-headroom policy and its two field roles, and renewed the residual semantic-limitation
acceptance for this one attempt only. The approval was recorded beside the packet. All 38 pre-network
checks passed with no network, and **exactly one provider request was made**.

- **The provider finished normally** (`stop_reason = tool_use`), and the forced structured output
  parsed.
- **The v1.1.0 schema then refused the answer at stage 5, on one field.**
  `evidence_bound_reasoning_summary` is 1031 characters against a hard maximum of 900, which prompt
  v1.4.0 states in words beside a generation target of 720.
- **Every other composed text is within its hard maximum**, including the class V4 was refused on. Two
  texts exceed their target and stay within their bound, and the schema did not refuse them.
- **Stages 6 to 10 were not reached.** The semantic gate v1.3.0, the evidence boundary, attribution and
  persistence eligibility never judged this answer.
- **No retry, no second request, nothing persisted, no human-review packet, and the approval is
  spent.**

```
START_COMMIT        dca098939fabd4b9ddc21ce69f4fad8a019e79ed
BRANCH              sprint-1/mission-1.84.15

PACKET              SECOND-OPPORTUNITY-SYNTH-EXEC-V5 v5
                    da3e7d09d97c30cd02859eaee729b6bd164cd99812feac34572a0e1d93aa511a
APPROVAL            second-opportunity-synthesis-execution-approval-v5.json
                    APPROVE_EXACTLY_ONE_EXECUTION
                    file sha256                df2efd342c4962b1da2acebf6e9c3f4433677c8645112a83ebdb597d6b355873
                    operator statement sha256  60beeb267a28cd4dfa59880448a138efc5cfce108b9e2026f6be8b173551c082
RECORD              second-opportunity-synthesis-execution-record-v5.json
                    42da9819c066e107d4539c1c4a857425e6809c4389ab69249bebec154b51ea7a

PRIMARY_OUTCOME     EXECUTION_SCHEMA_REJECTED_NO_RETRY
runner code         EXECUTION_OUTPUT_REJECTED_AT_SCHEMA_VALIDATION_NO_RETRY
```

## The approval, recorded beside the packet (§6)

`second-opportunity-synthesis-execution-approval-v5.json` was written once, with an exclusive create.

**The operator's words were extracted from the message, not retyped.** The message was found exactly
once in the session's transcript, as 674 non-blank lines with digest `5b52ae03...`. Its opening lines
and sections 1 to 6 are the approval, and its sections 7 to 30 are the Mission 1.84.15 brief. The
recorded statement is the approval: the 214 lines up to the heading of section 7, with blank lines
dropped and a SHA-256 over the lines joined by a newline, as in V3's and V4's approvals. The whole
message's line count and digest are recorded beside it.

**Before anything was written, the 33 values the operator named were compared with the frozen packet**,
and any difference would have stopped the write. They cover:
- the identity and the decision;
- the provider, route and model;
- thinking and its request value;
- the subject;
- the schema and its digest;
- the semantic gate and its implementation digest;
- the prompt and its digest;
- **the generation-headroom policy, the ratio `4/5` and the array headroom policy `NONE`**;
- the representation and its length;
- the token, call, retry and timeout bounds;
- the prepared body length (31963) and the input estimate;
- the three worst-case costs and the ceiling;
- human review, and no automatic persistence.

The record also carries, as data:
- **the headroom acceptance**: the seven things the operator understood about the 4/5 target (prompt
  guidance only, not part of the schema, not a validation bound, not a provider guarantee, not derived
  from V4, valid above the target and within the hard maximum, invalid above the hard maximum), the two
  field roles `NAME_THE_CLASS_ONLY` and `COMPACT_SYNTHESIS_NOT_DUPLICATE_LEDGER`, and
  `AUTHORISES_REMOVING_NECESSARY_INFORMATION = false`;
- **the residual semantic-limitation acceptance**, renewed for this one V5 inference attempt, with its
  four reasons, the seven things it does not authorise, and `EXPIRES_WITH_THIS_ATTEMPT = true`;
- the 18 things no change was approved to, and the 10 the operator specifically did not authorise;
- the 6 reuses of an earlier execution refused, and the 25 kinds of further model authority refused.

A bullet the message wraps over two lines is recorded as one item, joined by a single space; the
verbatim statement keeps both lines, and gate 85 matches each item against the statement that way.

**Packet V5 was not touched.** Its digest is unchanged, and its `OPERATOR_EXECUTION_APPROVAL_RECORDED`
still reads `false`, because that field says the document records no approval.

## Before any socket (§7, §8)

The 38 checks ran with the V5 runner's own verification, which rebuilt the representation from the
research database and built the request body with a transport that refuses to send. They ran under a
tripwire on the real transport, and every one passed. The runner's verification then ran again as the
first half of `--execute`.

| # | check | found |
|---|---|---|
| 1 | packet V5 digest | `da3e7d09...`, recomputed from the bound fields and equal to the runner's pin |
| 2 | approval exists exactly once | one approval file names V5's digest |
| 3 | approval names that digest | recorded by mission-1.84.15; the statement digest recomputes |
| 4 | decision | `APPROVE_EXACTLY_ONE_EXECUTION` |
| 5 to 8 | V1, V2, V3, V4 consumed | each refused with `EXECUTION_APPROVAL_ALREADY_CONSUMED` |
| 9 | V5 not consumed | no V5 record and no V5 response |
| 10, 11 | schema | `second-opportunity-synthesis-output@1.1.0`, `ec789d1b...` |
| 12, 13 | semantic gate | `second-opportunity-output-gate@1.3.0`, implementation `cc3c4902...` |
| 14, 15 | prompt | v1.4.0, `960955f4...`, rendered and hashed |
| 16, 17, 18 | drift | 0 unstated schema constraints, 0 unstated class-A rules, 0 unstated generation targets |
| 19 | headroom policy | `TARGET_AT_MOST_80_PERCENT_OF_HARD_MAX_LENGTH` |
| 20 | ratio | `Fraction(4, 5)`, and `4/5` in the packet |
| 21 | array headroom | `NONE` |
| 22 | headroom drift | `HEADROOM_TARGET_DRIFT = 0`, gate 83's record revalidated |
| 23, 24 | representation | `2528a56a...`, 3604 characters |
| 25 | provider posture | `APPROVED` |
| 26, 27 | TED transmission / packet | `PERMITTED_WITH_CONDITIONS` / `AVAILABLE` |
| 28 | route | `POST https://api.anthropic.com/v1/messages`: synchronous, no beta header, not streamed; batches and the subscription route not used |
| 29 | model | `claude-sonnet-5`, in the packet and in the body |
| 30, 31 | request body | `thinking {"type": "disabled"}`, `max_tokens 128000` |
| 32, 33 | calls / retries | 1 / 0 (and 0 in the request) |
| 34 | timeout | 60.0 s |
| 35 | frozen request | the body rebuilds to 31963 characters, the packet's |
| 36 | cost | worst case 1.317056 = ceiling |
| 37 | retention | ready |
| 38 | stages 6 to 9 preflight | `DETERMINISTIC_STAGE_6_TO_9_PATH_READY`; gates 80, 83 and 84 validate |

**The credential was never read, printed or written.**
- The runner's own verification loads the local configuration file into its process environment,
  without overriding anything already set. It did the same for V3 and V4.
- The preflight printed only whether the adapter would find a credential: `True`.
- The 134 runner, headroom and record tests were green before the call.

## The one request (§9)

```
started / finished   2026-09-13T12:25:09.607279+00:00 / 2026-09-13T12:25:43.443672+00:00
elapsed              33.836 s of a 60.0 s timeout
route                POST https://api.anthropic.com/v1/messages (synchronous)
model                claude-sonnet-5 (the response names claude-sonnet-5)
thinking             DISABLED, {"type": "disabled"}
max_tokens           128000
HTTP status          200
request id           req_011Cf1S9QabAndSNwfBmwPyC
message id           msg_011Cf1S9RNhwa1qCs6adyRV3
```

## What came back (§10)

```
stop_reason       tool_use -> COMPLETE
input tokens      12899  (estimated 18528: the estimate covered it)
output tokens     3797   (ceiling 128000)
total tokens      16696
thinking tokens   0
cost              0.063768 = 0.025798 input + 0.03797 output   (anthropic-published-2026-09-02)
ceiling           1.317056  (the call cost about 4.8% of it)
```

The cost is derived from the usage the provider reported, at the held price, and it equals the
Gateway's telemetry. The provider's invoice is not observed. **The worst case of 1.317056 was a bound
computed before the call, and it is not what the call cost.**

Compared with V4, the call used 1300 more input tokens, for the headroom block prompt v1.4.0 adds, and
153 fewer output tokens.

## The ten stages (§11)

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

The live v1.1.0 validator's one violation, verbatim:

1. `evidence_bound_reasoning_summary: 1031 characters exceeds maxLength 900`

**A stage that was not reached is not a stage that passed.** Stages 6 to 9 have still never judged a
real answer.

## The hard schema and the generation targets (§12, §24)

Every composed text, measured in the retained answer. For an array, each element is listed.

| composed text | target | hard maximum | returned characters | within target | within hard maximum |
|---|---|---|---|---|---|
| `target_actor_if_supported` | 160 | 200 | 128 | yes | yes |
| `observed_need` | 320 | 400 | 358 | **no** | yes |
| `candidate_intervention_class` | 240 | 300 | 133 | yes | yes |
| `hypothesis_statement` | 480 | 600 | 529 | **no** | yes |
| `independence_status` | 240 | 300 | 167 | yes | yes |
| `reliability_status` | 240 | 300 | 216 | yes | yes |
| `evidence_bound_reasoning_summary` | 720 | 900 | 1031 | **no** | **no** |
| `critical_uncertainties[]` | 400 | 500 | 179, 199, 186, 147, 129, 148 | yes | yes |
| `commercial_claims_supported[]` | 240 | 300 | 127, 131 | yes | yes |
| `commercial_claims_not_supported[]` | 240 | 300 | 96, 83, 68, 68, 61, 59, 72, 91, 89, 89, 95, 80 | yes | yes |
| `recommended_next_evidence[]` | 240 | 300 | 116, 139, 107, 139, 154, 104 | yes | yes |
| `statement_classifications[].statement` | 240 | 300 | 137, 143, 137, 138, 134, 111, 93, 89, 131, 83 | yes | yes |

- **The hard schema decided stage 5, and nothing else did.** Nine texts are within their target. Two
  are over their target and within their hard maximum, `observed_need` and `hypothesis_statement`, and
  the schema refused neither. One is over its hard maximum, and it is the one the schema refused. Gate
  85 requires exactly this correspondence, and its tests prove it for all twelve texts on the retained
  answer: target + 1 and the hard maximum pass, hard + 1 fails.
- **The summary**: 1031 characters, 131 over the hard maximum and 311 over the target. V4's was 1078
  and V3's 868. Prompt v1.4.0 states both the 900 and the 720 beside it, and gate 85 re-derives that
  both are stated.
- **The class**: 133 characters against a target of 240. V4's was 316, one of its two violations.
- **The generation-target diagnostics are diagnostic only.** They are recorded, and no stage verdict
  reads them.
- **The answer was judged as it arrived.** Nothing truncated, rewrote, summarised, split or dropped
  anything to fit, and no further request was made.
- **Nothing was changed on the strength of any of this, and nothing is recommended here.** The prompt,
  the schema, the gate and the headroom policy stay exactly as frozen, as the approval requires.

## What the refused answer said, retained as evidence and not as a candidate

The model returned `FORM_HYPOTHESIS` with confidence `EXPLORATORY` and ten classified statements:
- five `OBSERVED_OR_EVIDENCE_SUPPORTED`;
- one `HYPOTHESIS_TO_VALIDATE`;
- four `UNKNOWN_REQUIRES_EVIDENCE`.

It names three supported dimensions and eleven unsupported ones, and cites six Evidence ids with five
distinct Claims.

**Its content was not judged**:
- the semantic gate never ran;
- no statement's support was checked;
- the residual limitation the operator accepted was not exercised.

The retained body and the parsed output are in `second-opportunity-synthesis-response-v5.json`. **The
schema refused this answer, and it is not a candidate for persistence.**

## Human review (§18 to §20)

**No human-review packet was produced.** One is produced only when stages 1 to 9 pass, and stage 5
failed. The `RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_EXECUTION_V5` notice belongs in a review packet
that does not exist, so it is not recorded as one. The acceptance itself is recorded in the approval,
bounded to this attempt, and it expired with it. Gate 85 refuses a review packet for a refused answer.

## Spent, and refused by name (§22)

`second-opportunity-synthesis-execution-record-v5.json` records the approval as consumed:
`EXECUTION_APPROVAL_CONSUMED = true`, `FURTHER_CALLS_AUTHORIZED_BY_V5 = false`, and
`RESIDUAL_RISK_ACCEPTANCE_EXPIRED = true`.

After the record was written, the V5 runner's `--execute` was run once more. It ran in process, with
its `execute()` replaced by a function that raises and the real transport tripwired, so no request
could have left whatever the runner decided. Its verification ran, and it refused V5 at the
consumed-approval check:

```
REFUSED  nothing was sent: EXECUTION_APPROVAL_ALREADY_CONSUMED: the approval for execution packet
da3e7d09... records 1 provider request(s) already made.
EXIT 1 | execute reached False
```

The V1 to V4 digests are refused as before, and an unseen digest is not. V1's to V4's records are
unchanged, byte for byte, and gate 85 pins all four, with V4's response and approval.

## Retention (§21)

| retained | value |
|---|---|
| raw response | the provider's message object, 9420 characters, `cd9ddf67...`, recomputable from the kept body |
| request id / message id | `req_011Cf1S9QabAndSNwfBmwPyC` / `msg_011Cf1S9RNhwa1qCs6adyRV3` |
| stop reason | `tool_use` |
| usage | the provider's usage block, identical to the Gateway's telemetry |
| parsed output | retained, `fc303141...` |
| stage verdicts, timestamps, cost, terminal outcome | retained |
| hidden reasoning | none requested, none retained |
| credential values | none |

The normal path wrote the artifact, and the post-call fail-safe was not needed. The file carries no
credential-shaped string.

## CI gate 85 (§26, §27)

`render_second_opportunity_execution_record_v5.py` re-derives the record from what was kept:
- the raw digest, from the retained body;
- the completion, through the adapter's classifier;
- the schema verdict, by running the live v1.1.0 validator over the retained answer;
- the violation's length, measured again beside its target and looked up in prompts v1.4.0 and v1.3.0;
- **every composed text's length against its generation target and its hard maximum**, with the texts
  over a hard maximum required to be exactly the texts refused;
- the cost, from the reported usage at the held price;
- the stage table, from those facts.

**It pins the raw response, the parsed output and the approval by digest.** A summary truncated to 900
or to 720 characters, with every digest recomputed and the record rebound to the new file, is still
refused, because it is not what arrived.

It also refuses:
- an approval that lost a word, a prohibition, a withheld change, its headroom acceptance, a field role
  or its residual-risk bounds;
- another headroom policy, ratio or array policy;
- a record that says the targets decide, or that the hard verdict passed;
- the worst case, a rounded figure or `NOT_ESTABLISHED` in place of the reported usage and cost;
- a stage after the failure marked passed;
- a human-review packet, in the record or on disk, for a refused answer;
- V1's to V4's records, V4's response or V4's approval edited;
- a runner that would execute V1 to V5 again;
- any persistence, mutation or moved counter;
- a credential shape.

75 tests cover it, among them the proofs §27 asks for: a soft target exceeded on each of the twelve
texts is not a schema failure, the hard maximum itself is not one, and hard + 1 is.

## Probe

**151 violations caught, 0 escaped, 10 of 10 positive controls, every file proved restored.**
`VIOLATIONS_ESCAPED = 0`, `POSITIVE_CONTROLS_FAILED = 0`.

How they were caught:
- 143 by gate 85's own rules;
- 7 by the runner itself;
- 1 by render drift.

**The runner's seven refusals, with no request possible.** For the two `--execute` runs, the runner's
`execute()` was replaced by a function that raises, and the real transport was tripwired. Neither was
reached.
- V1, V2, V3, V4 and V5 are each refused with `EXECUTION_APPROVAL_ALREADY_CONSUMED`.
- `--execute` on the shipped state is refused with the same code.
- `--execute` with V5's record deleted and its response kept is refused with
  `EXECUTION_ALREADY_PERFORMED`.

**The families, all refused:**
- **The record** (89 cases): everything gate 82's probe attacked, carried over to V5, plus the headroom
  policy, the ratio, the array policy and the headroom digest changed; the targets said to decide; the
  hard verdict said to pass; 37 pre-network checks or a pre-network problem; another start commit or
  branch; the violation's target said unstated, or V4's length misstated; and the diagnostics edited:
  the summary said within its bound or its target, its length edited, `observed_need` said within its
  target or over its bound, the class target moved, an array element or a whole row dropped.
- **The approval** (25 cases): its file digest is pinned, so every edit is a violation, even a
  reworded comment, and each was caught; they include removing "truncating output", "raising maxLength
  900 because V4 returned 1078" and "it is not a validation bound", and making the residual risk never
  expire.
- **The response** (14 cases). Among them is the rescue the operator forbade, done carefully and twice:
  the summary truncated to 900 and to 720, every digest recomputed, the reasons emptied and the record
  rebound to the new file, its diagnostics recomputed. Both are refused, because the pinned raw
  response and parsed output are not the ones that arrived.
- **History** (10 cases): V1's to V4's consumption reset; a V4 review packet; V4's reasons trimmed;
  V4's approval with a prohibition dropped; packet V5 with an approval written inside, a bound field
  edited, or another ratio.
- **A human-review packet** written to disk for the refused answer (1 case).
- **Live code, in a fresh interpreter** (4 cases): the summary bound raised in the schema; the ratio
  moved to 9/10; the runner blind to V5's record; the runner reading V5's record from elsewhere.

**The positive controls:**
- the shipped gates 82, 84 and 85;
- the record's `$comment` and four of its notes, which gate 85 does not pin;
- a comment in gate 85's tests;
- an unseen digest, which is not refused.

**One state was deliberately not constructed.** With an approval on disk, the runner refuses V5
through two committed files: its record and its response. The probe did not delete both and then ask
the runner to execute, because if its safeguards had failed there, an unapproved request would have
gone out. Removing both files is a visible repository change, and gate 85 refuses it in CI.

## Accounting (§24)

```
provider requests          1
model calls                1
retries                    0
fallbacks                  0
continuations              0
repair calls               0
TED bytes sent             3604  (the approved representation, inside the 31963-character body)
provider stop reason       tool_use
input tokens               12899
output tokens              3797
thinking tokens            0
total tokens               16696
actual cost                0.063768
generation targets         9 of 12 within; 2 over target and within bound; 1 over bound
                           (diagnostic only: no verdict reads them)
hard schema                11 of 12 composed texts within bound; FAILED on the summary
stages passed              4 (1 to 4)
failed stage               5_schema_validation_v1_1_0
raw response retained      true
usage retained             true
parsed output retained     true
Opportunity persistence    false
canonical mutation         0
```

## Canonical state (§23)

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

- `ruff format --check` and `ruff check` are clean over 1088 files, and `mypy` over 211.
- Contracts, catalog and source registry are clean.
- **3853 bare-python tests and 5021 pytest tests** pass, 13 skipped. The database is unchanged across
  29 tenant tables; the global tables are unchanged across 17, with 11 rows appended by the suites to
  1 append-only table, as the checker reports.
- **75 new tests**, on gate 85 and the refusals it must make.
- **85 CI gates**, one of them new, all run locally with no failure.
- The canonical counters were read again at the end, and they are unchanged.

## Next (§30)

**Stop.** The one request is spent. Stage 5 failed, so nothing is persisted, no human-review packet
exists, and no further model call is made. The prompt, the schema, the gate and the headroom policy
stay exactly as frozen.

The facts the operator's next decision rests on, with nothing recommended:

- **V5 is historical and spent**, and the residual semantic-limitation acceptance expired with it. Any
  further execution needs a new packet digest and a new explicit approval naming it.
- **The stated target was not met on the summary, and the stated bound was not met either.** Prompt
  v1.4.0 stated 720 as the target and 900 as the hard maximum, and the summary came back at 1031.
- **The other composed texts met their hard maxima**, including the class V4 was refused on. Two
  exceeded their target within their bound, which is valid by the policy's own terms.
- **Stages 6 to 9 have still never judged a real answer.** The semantic gate v1.3.0 has judged only
  V3's historical answer, diagnostically.
- **One call is one observation.** It establishes that this answer's summary exceeded its hard maximum
  under a prompt stating a target below it, and nothing about how often any prompt meets it.

**Do not execute anything, do not re-execute V1, V2, V3, V4 or V5, do not treat the refused answer as a
candidate, and do not persist Opportunity #2.** Mission 1.84.16 was not started.
