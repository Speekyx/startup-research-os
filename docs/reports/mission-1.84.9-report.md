# Mission 1.84.9: Second Opportunity Synthesis Execution V3

**`EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY`**

The operator approved exactly one execution of packet V3 by its digest. The approval was recorded
beside the packet, every pre-network check passed with no network, and **exactly one provider
request was made**. The provider finished normally (`stop_reason = tool_use`) and the forced
structured output parsed. **This time the v1.1.0 schema passed the answer**: the prompt alignment
did what Mission 1.84.8 built it for, and the 900-character bound V2 was refused on was met. The
frozen v1.1.0 semantic gate then refused the answer at stage 6, on five reasons. Stages 7 to 10 were
not reached. **No retry, no second request, nothing persisted, and the approval is spent.**

```
START_COMMIT       e26265a19dcd56e232c61b04d0dba0b558d43095
BRANCH             sprint-1/mission-1.84.9

APPROVAL           second-opportunity-synthesis-execution-approval-v3.json
                   APPROVE_EXACTLY_ONE_EXECUTION of SECOND-OPPORTUNITY-SYNTH-EXEC-V3 v3
                   c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2
                   operator statement sha256 d8a1de699bde030777da1a4169d515d951ad0e392d89737019db9ebdc542a3d6

PRIMARY_OUTCOME    EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY
runner code        EXECUTION_OUTPUT_REJECTED_AT_SEMANTIC_GATE_NO_RETRY
```

## The approval, recorded beside the packet

`second-opportunity-synthesis-execution-approval-v3.json` was written once, with an exclusive
create. It holds the operator's words verbatim, extracted from the message rather than retyped:
108 lines with blank lines dropped, and a SHA-256 over them. It names the packet's id, version and
digest and the decision `APPROVE_EXACTLY_ONE_EXECUTION`. It also carries, as data:

- the approved execution, field by field;
- the operator's explicit approval of the prompt v1.2.0 alignment;
- the nine things no change was approved to, the 900 bound first;
- the 32 prohibitions.

**Before writing anything, the script compared every value the operator named with the frozen
packet and would have refused on any difference.** The packet itself was not touched: its
`OPERATOR_EXECUTION_APPROVAL_RECORDED` still reads `false`, because that field says the document
records no approval, never that none exists. Gate 73 accepts the approval because a later mission
recorded it and it names V3's digest; gate 74 checks its words.

## Before any socket

The runner's verification ran twice with no network, once dry and once as the first half of
`--execute`. A separate preflight covered what the runner does not check itself. Every item of the
brief's list passed both times:

| # | the brief's check | found |
|---|---|---|
| 1 | V3 digest | `c7b8553d...`, recomputed from the bound fields |
| 2 | approval names that digest | `RECORDED` |
| 3, 4 | V1 and V2 consumed | `true`, `true` |
| 5 | V3 approval recorded exactly once | one approval file names V3's digest |
| 6 | representation | `2528a56a...`, 3604 characters, rebuilt from the database |
| 7 | prompt | `1677cbe5...`, rendered and hashed |
| 8, 9 | schema | `second-opportunity-synthesis-output@1.1.0`, `ec789d1b...` |
| 10 | gate | `second-opportunity-output-gate@1.1.0` |
| 11 | prompt drift | `UNSTATED_GENERATION_CONSTRAINTS = 0` |
| 12 | provider posture | `APPROVED` |
| 13, 14 | TED transmission / packet | `PERMITTED_WITH_CONDITIONS` / `AVAILABLE` |
| 15 | model | `claude-sonnet-5` |
| 16 | route | `POST https://api.anthropic.com/v1/messages`, synchronous, no beta header |
| 17 | request body | `max_tokens` 128000, `thinking` `{"type": "disabled"}`, 22124 characters |
| 18, 19 | calls / retries | 1 / 0 |
| 20 | timeout | 60.0 s |
| 21 | cost | worst case 1.30565 = ceiling |
| 22 | retention | ready; 214 runner and gate tests green before the call |

**One false alarm, and why it was not one.** The preflight script first reported the approval file
missing. The shared shell's working directory had been moved by a test command running beside it,
so the script had looked in the wrong directory, where V2's approval was absent too. The file was
intact at its first digest, `9f951e64...`. The preflight was re-run alone with absolute paths and
passed.

## The one request

```
started / finished   2026-09-12T20:03:01.233247+00:00 / 2026-09-12T20:03:35.590818+00:00
elapsed              34.358 s of a 60.0 s timeout
route                POST https://api.anthropic.com/v1/messages (synchronous)
model                claude-sonnet-5 (the response names claude-sonnet-5)
thinking             DISABLED, {"type": "disabled"}
max_tokens           128000
HTTP status          200
request id           req_011Cez9FYuKnuu1zASuK1KS3
message id           msg_011Cez9FZnQuRzvQup34Qay2
```

## What came back

```
stop_reason       tool_use -> COMPLETE
input tokens      9491   (estimated 12825: the estimate covered it)
output tokens     3880   (ceiling 128000)
total tokens      13371
thinking tokens   0
cost              0.057782 = 0.018982 input + 0.0388 output   (anthropic-published-2026-09-02)
ceiling           1.30565   (the call cost about 4.4% of it)
```

The cost is derived from the usage the provider reported, at the held price, and equals the
Gateway's telemetry; the provider's invoice is not observed. **The worst case of 1.30565 was a bound
computed before the call and is not what the call cost.** V2 used 8939 input and 3914 output tokens
on the v1.1.0 prompt. V3 used 552 more input tokens, for the longer system region, and 34 fewer
output tokens.

## The ten stages

| stage | verdict |
|---|---|
| `1_transport_success` | PASSED |
| `2_provider_response_shape` | PASSED |
| `3_provider_completion` | PASSED |
| `4_structured_output_parse` | PASSED |
| `5_schema_validation_v1_1_0` | **PASSED** |
| `6_semantic_output_gate_v1_1_0` | **FAILED** |
| `7_evidence_boundary_and_no_distortion` | NOT_REACHED |
| `8_attribution_and_provenance` | NOT_REACHED |
| `9_persistence_eligibility` | NOT_REACHED |
| `10_human_review` | NOT_REACHED |

The gate's five reasons, verbatim:

1. `reliability_status contains 'SCORED'. Scoring-ready is not scored, no score exists in this
   repository, and REFERENCE_PROFILE_V1 is UNCALIBRATED`
2. `evidence_bound_reasoning_summary audited UNSUPPORTED: the number 161 appears in no supplied
   statement and in no structural fact about the packet; 'market' appears in no supplied statement;
   prior knowledge is not available as factual support (§7)`
3. `REALISED_SPEND: the output contains 'actual expenditure', which no supplied statement contains.
   This packet is not money anybody paid, actual expenditure, a budget consumed, or a contract's
   final cost`
4. `WILLINGNESS_TO_PAY: the output contains 'willingness to pay', which no supplied statement
   contains. This packet is not willingness to pay, price tolerance, budget for software, or
   ability to pay for a product`
5. `WILLINGNESS_TO_PAY: the output contains 'willing to pay', which no supplied statement contains.
   This packet is not willingness to pay, price tolerance, budget for software, or ability to pay
   for a product`

**A stage that was not reached is not a stage that passed.**

## What the refusal is, stated as facts

- **The schema passed.** Every one of the 32 generation-relevant constraints was met, the
  `evidence_bound_reasoning_summary` included, at 868 characters against 900. The prompt
  alignment did what it was built for on the one call it got.
- **Where each refused term occurs in the answer**, recomputed by gate 74 from the retained output:

  | term | occurs in | how the answer uses it |
  |---|---|---|
  | `SCORED` | `reliability_status` | "scoring-ready is not the same as scored, and no score exists for any row" |
  | `161` | `evidence_bound_reasoning_summary` | "TOTAL_VALUE includes options and renewals per BT-161" |
  | `market` | the summary, `supported_dimensions[2]`, `commercial_claims_not_supported[2]` | the summary asserts "market activity in the classified scope" |
  | `actual expenditure` | `recommended_next_evidence[2]` | "Evidence of actual expenditure or payment rather than published award ceilings" |
  | `willingness to pay` | `hypothesis_statement`, the summary | "do not establish any need, gap, dissatisfaction, or willingness to pay"; "It does not establish ... willingness to pay" |
  | `willing to pay` | `commercial_claims_not_supported[1]`, `statement_classifications[9]` | listed as not supported; classified `UNKNOWN_REQUIRES_EVIDENCE` |

- **Three of the refused terms appear in the prompt the model was sent.** `willingness to pay`,
  `actual expenditure` and `BT-161` all occur in the v1.2.0 system region, in the passages that tell
  the model what this packet is NOT and what BT-161 defines. `willing to pay` and `scored` do not
  occur there.
- **How the gate reached each reason.** The forbidden-phrase check refuses a phrase wherever it
  appears in the output unless a supplied statement contains it; its own comment says so. The
  general audit reads the six supplied TED statements, not the system region. It clears a term
  only where the answer denies it, which is why it flagged `market`, asserted in the summary, and
  `161`, a number no supplied statement carries.
- **The verdict was re-derived without a provider.** Re-running the live v1.1.0 gate locally over
  the retained answer, with the evidence packet rebuilt from the research database and a tripwire
  on the real transport, reproduced the five reasons exactly. No transport was constructed.

These are observations for the operator's decision. **Nothing was changed on the strength of them,
and nothing is recommended here**: the prompt, the schema and the gate stay exactly as frozen, as
the approval requires.

## What the refused answer said, retained as evidence and not as a candidate

The model returned `FORM_HYPOTHESIS` with confidence `EXPLORATORY`. It named:

- three supported dimensions: `BUYER_OR_BUDGET_EXISTENCE`, `ECONOMIC_VALUE`, `MARKET_ACTIVITY`;
- eleven unsupported ones, including `PROBLEM_OR_NEED`, `WILLINGNESS_TO_PAY` and `SOLUTION_GAP`.

Its hypothesis is an investigation-stage one: it is worth finding out whether the contracting
authorities publishing CPV-9261 notices form a buyer population worth characterising, and the same
sentence says the statements establish no need, gap, dissatisfaction or willingness to pay. It
listed ten commercial claims as not supported and nine critical uncertainties, among them whether
TOTAL_VALUE reflects money actually paid. It cited all six Evidence ids and all five Claim ids of
the packet; checked after the fact, all lie inside the packet. **That is an observation and not a
stage verdict**, because stage 7 never ran.

**The semantic gate refused this answer, and it is not a candidate for persistence.** The retained
body and the parsed output are in `second-opportunity-synthesis-response-v3.json`.

## Spent, and refused by name

`second-opportunity-synthesis-execution-record-v3.json` records the approval as consumed. After it
was written, `--execute` was run once more, and the runner refused V3 before any network:
`EXECUTION_APPROVAL_ALREADY_CONSUMED`. V1's and V2's digests are refused as before, and an unseen
digest is not. V1's and V2's records are unchanged, byte for byte.

## Gate 74

`render_second_opportunity_execution_record_v3.py --check` re-derives the record from what was kept
rather than reading it:

- the raw response digest from the retained body, re-serialised compactly (9542 characters);
- the stop reason through the adapter's own classifier;
- the schema verdict by running the live v1.1.0 validator over the retained answer (no violation);
- the cost from the reported usage at the held price, matched against the Gateway's telemetry;
- the stage table from those facts;
- the approval against its own words, its digest, its prohibitions and what it withholds a change to;
- V1's and V2's records against their pinned digests;
- the runner, asked whether it would execute V3, V2 or V1 again.

The semantic gate needs the evidence packet, which lives in the research database and not in the
repository. So gate 74 checks the refusal the other way round: every retained reason must name text
the retained answer contains, and where each flagged term occurs is recomputed from the answer. **A
refusal that names nothing the answer says is refused**, and so is a record that moves a term, drops
a reason or counts a `NOT_REACHED` stage as passed. It also refuses a human-review packet for an
answer the machine stages did not accept, any persistence or moved counter, and a credential shape
anywhere.

## The execution record, field by field

```
packet V3 digest            c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2
approval                    approval-v3.json 9f951e64d9bc93e1dfb907763c2fdfedc1f3df46b48e63acf927fef3671d027c
                            statement d8a1de699bde030777da1a4169d515d951ad0e392d89737019db9ebdc542a3d6
request count               1
retry / continuation / repair   0 / 0 / 0
provider route              POST https://api.anthropic.com/v1/messages, SYNCHRONOUS_MESSAGES_API
model                       claude-sonnet-5
thinking                    DISABLED, {"type": "disabled"}
max_tokens                  128000
timeout                     60.0 s
prompt                      1.2.0 1677cbe53e83e644fa15e5492cf88e3ec578538351924f2b3a504e27f3a0878d
schema / gate               second-opportunity-synthesis-output@1.1.0 / second-opportunity-output-gate@1.1.0
representation              2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72
stop reason                 tool_use
raw-response retention      retained, 5bb5dde55437689296e7963787f711555529a0db865809c550be41ba15f5374d
usage retention             retained
actual measured usage       9491 input, 3880 output, 13371 total, 0 thinking
actual measured cost        0.057782
validation stages           1-5 PASSED, 6 FAILED, 7-10 NOT_REACHED
terminal outcome            EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY
human review                required; no human-review packet, stage 6 refused the answer
canonical persistence       false
```

## Probe

**152 violations caught, 0 escaped, 6 of 6 positive controls, every file proved
restored**, and `validate()` passing afterwards both in process and in a fresh interpreter.
151 were refused by the check written for them and 1 by render drift.

The 145 record cases edit on disk the record, the approval, the response artifact, V1's and V2's
records and packet V3. Each record, approval or response edit is followed by rebinding the
record's pins, so the content checks decide. They include:

- the answer rewritten consistently in both the parsed output and the retained tool input, so it
  no longer carries the refused phrase;
- the summary truncated;
- a reason dropped, invented or reworded to name nothing;
- a term moved;
- the operator's words edited and rehashed, including dropping the digest line or the alignment
  sentence;
- the prohibitions on a second request, a retry after a semantic failure, rewriting to fit, a
  repair model and V2's approval removed;
- the 900 bound and the gate released.

Six cases edit live code and run the whole gate in a fresh interpreter started with `-B`:

- the V3 runner blind to its own record, its V3 check disabled, or refusing every digest;
- V2's guard disabled;
- an adapter that no longer reads `tool_use` as complete;
- the schema's 900 bound lowered under the answer.

The controls: the shipped record validates; a note reworded in the record, the approval or the
artifact binds nothing; and a docstring or comment edit in the adapter or the runner passes.

## Accounting

```
provider requests        1
model calls              1
retries                  0
fallbacks                0
continuations            0
repair calls             0
TED bytes sent           3604   (the approved representation, unchanged, in a 22124-character body)

provider stop reason     tool_use

actual input tokens      9491
actual output tokens     3880
actual thinking tokens   0
actual total tokens      13371
actual cost              0.057782

validation stages passed 5 (1 to 5)
failed stage             6_semantic_output_gate_v1_1_0

raw response retained    yes
usage retained           yes
parsed output retained   yes

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

Counted before the branch's first write, again straight after the call, and again after the final
pytest run.

## Verification

`ruff format --check` and `ruff check` clean over 1032 files. `mypy` clean over 201 files.
Contracts, catalog and source registry clean.

**3853 bare-python tests. 4244 pytest tests**, 13 skipped, with the database unchanged across
29 tenant tables. **74 new tests**, all on gate 74. **74 CI gates**, one new.

## Outcome and next

**`EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY`.**

**Stop.** V3's approval is spent, and the runner refuses its digest by name. No further call is
authorised: any further execution needs a new packet digest and a new explicit operator approval
naming it.

Whether anything changes before then is the operator's decision. The options are the gate's phrase
and audit checks, the prompt, or nothing. This mission implemented none of them and recommends
none. The refused answer is retained as evidence and is not a candidate for persistence.

**Do not re-execute V3, do not persist Opportunity #2, and do not treat the refused answer as a
candidate.** Mission 1.84.10 was not started.
