# Mission 1.84.2 — The call happened, the answer was rejected, and the approval is spent

**Outcome: `SECOND_OPPORTUNITY_EXECUTION_REJECTED_AND_CLOSED_NO_RETRY`.**

One approved provider request was made. The transport succeeded, the provider answered, and the
answer carried **18 of the 20 required fields**. It was refused at validation stage 4. No retry.
Nothing persisted.

**Two things the frozen retention policy required were not retained, and both are defects in this
mission's own runner.** They are repaired for a future separately-approved call, and they are the
reason the root cause can only be strongly supported rather than proven.

---

## Report

```
BRANCH                        sprint-1/mission-1.84.2
START_COMMIT                  9f94263 (main, before the execution attempt)

EXECUTION_PACKET_ID           SECOND-OPPORTUNITY-SYNTH-EXEC-V1  v1
EXECUTION_PACKET_SHA256       570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92
EXECUTION_PACKET_UNCHANGED    true   (approval flag on the packet still false)

EXECUTION_APPROVAL_CONSUMED   true
FURTHER_CALLS_AUTHORIZED_BY_V1 false

PROVIDER_REQUESTS             1        RETRIES 0        SECOND CALLS 0
FALLBACK_MODEL / PROVIDER     false / false
TRANSPORT_RESULT              SUCCESS
VALIDATION_RESULT             REJECTED at 4_schema_validation
FIELDS                        18 of 20 present
MISSING                       confidence_classification, statement_classifications
MISSING_POSITIONS             19 and 20 of 20

RAW_PROVIDER_RESPONSE_RETAINED  false    HASH  NOT_AVAILABLE    RECOVERABLE  false
USAGE_RETAINED                  false
ACTUAL_INPUT_TOKENS             NOT_ESTABLISHED
ACTUAL_OUTPUT_TOKENS            NOT_ESTABLISHED
ACTUAL_EXECUTION_COST           NOT_ESTABLISHED
APPROVED_WORST_CASE_CALL_COST   0.04825      EXECUTION_COST_CEILING 0.10

OUTPUT_CAPACITY_FAILURE_HYPOTHESIS  STRONGLY_SUPPORTED
ROOT_CAUSE                          NOT_PROVABLE_FROM_RETAINED_EXECUTION_ARTIFACTS
OUTPUT_CAPACITY_BOUND_NOT_DERIVED_FROM_SCHEMA  true

CANONICAL_PERSISTENCE          false     OPPORTUNITIES_CREATED 0
HUMAN_OUTPUT_REVIEW_REQUIRED   true      review packet produced false

TOTAL_PROVIDER_REQUESTS_FOR_MISSION_1_84_2          1
ADDITIONAL_PROVIDER_REQUESTS_DURING_FAILURE_CLOSURE 0
REMOTE_TEST_CALLS_DURING_CLOSURE                    0
TED_BYTES_SENT_BY_THE_CONSUMED_CALL                 3604
TED_BYTES_SENT_DURING_CLOSURE                       0
CANONICAL_RESEARCH_MUTATION                         0

RawRecords 325 · NormalizedRecords 325 · Signals 60 · Claims 91 · ClaimRevisions 92
Evidence 112 · ReliabilityAssessments 4 · IndependenceGroups 0
Opportunities 1 · OpportunityRevisions 2 · OpportunityEvidenceLinks 14
Embeddings 0 · Scores absent · SourceReviews 71

VIOLATIONS_CAUGHT / ESCAPED   74 / 0        positive controls 8 of 8
TESTS                         3831 bare-python across 9 packages; 3431 pytest
CI_GATES                      65 -> 66
EXECUTION_RECORD              docs/data/second-opportunity-synthesis-execution-record-v1.json
NEXT                          Mission 1.84.3, and a new operator approval
```

---

## What was approved, and what the eight checks found

The operator approved exactly one execution under the frozen packet, naming its digest, the
provider route, the model, the representation and prompt digests, and every bound limit.

All eight pre-execution checks ran before a socket existed, and all eight passed:

| check | result |
|---|---|
| execution packet digest recomputed | `570657e1…`, matches the approval |
| version 1 unchanged, approval flag still false | true |
| representation digest recomputed | `2528a56a…`, 3604 characters, matches |
| rendered prompt digest recomputed | `af528949…`, matches |
| provider posture | APPROVED |
| TED external model transmission | PERMITTED_WITH_CONDITIONS |
| selected packet gate | AVAILABLE, no refusal reasons |
| every bound execution parameter | matches V1 |

**These establish why the historical call was authorised. They are not current permission for
another one**, and the record says so in a field the gate checks.

---

## What happened

Exactly one provider request. The transport succeeded and the provider answered. The answer was a
structured object carrying 18 of the 20 required fields, and the Gateway refused it:

> task `second-opportunity-synthesis-prompt` structured output is missing required fields:
> `['confidence_classification', 'statement_classifications']`

Stages 1, 2 and 3 passed. **Stage 4 failed.** Stages 5 through 8 never ran, and are recorded as
`NOT_REACHED` rather than as passing — a stage that never executed did not succeed.

**No retry, under any circumstance.** The request carried `max_retries = 0`, so the Gateway's own
retry branch could not be entered, and the runner has exactly one `gateway.complete` call site.
The gate now counts that call site, which is what makes "no retry" structural rather than careful.

---

## The approval is spent, and that is not a judgement call

A failed call spends an approval exactly as a successful one does. **`EXECUTION_APPROVAL_CONSUMED
= true`, `FURTHER_CALLS_AUTHORIZED_BY_V1 = false`.**

The single most tempting error available here is to read a rejected output as unused authority, so
it is refused by a deterministic guard rather than by memory. The consumed-approval fact lives in
a record **beside** the frozen packet — editing the packet to say it had been used would change
the bytes that were approved — and the runner reads it before executing:

```
EXECUTION_APPROVAL_ALREADY_CONSUMED
```

A test drives that refusal against V1's digest, and a second test proves the guard does **not**
refuse a different digest, because a guard that blocked every packet would block the successor too.

---

## Two retention defects, both mine

The frozen retention policy says the raw provider response is RETAINED, because *a gate verdict
over a response nobody kept is unverifiable*. On the consumed call it was not kept.

- **The raw response was discarded.** The Gateway builds its result locally and raises validation
  errors after it; the runner let the exception propagate and registered no transport recorder, so
  the bytes were gone at exactly the moment they were worth most. `RAW_PROVIDER_RESPONSE_RETAINED
  = false`, hash `NOT_AVAILABLE`, recoverable `false`. **No raw response is reconstructed from
  parsed values** — a reconstructed artifact reads exactly like a retained one to whoever comes
  next.
- **The usage record was discarded.** The Gateway emits usage on the failure path as well as the
  success path, carrying the provider-reported token counts, but only to a telemetry sink. The
  runner registered none.

So **`ACTUAL_INPUT_TOKENS`, `ACTUAL_OUTPUT_TOKENS`, `ACTUAL_TOTAL_TOKENS` and
`ACTUAL_EXECUTION_COST` are `NOT_ESTABLISHED`.** The only honest cost statement is
`ACTUAL_COST_UNKNOWN_BUT_EXECUTION_WAS_AUTHORIZED_UNDER_V1_CEILING`: the frozen worst case was
0.04825 cost units against a 0.10 ceiling, and **the worst case is an upper bound computed before
the call, not what the call cost.** No figure here claims otherwise, and the gate refuses a record
that sets the actual cost equal to it.

Parsing failure also cost the 18 fields that *were* returned. Their names survive only through the
validator's error message.

---

## The cause: strongly supported, and not proven

**`OUTPUT_CAPACITY_FAILURE_HYPOTHESIS = STRONGLY_SUPPORTED`.
`ROOT_CAUSE = NOT_PROVABLE_FROM_RETAINED_EXECUTION_ARTIFACTS`.**

The hypothesis is that the frozen `MAX_OUTPUT_TOKENS` of 3000 is too small for the schema Mission
1.84 froze, so serialisation ran out of budget before the trailing fields appeared. Three facts,
all computed without any further model call:

1. The two missing fields are **positions 19 and 20 of 20** in the schema's required order, and
   fields 1 through 18 were present. A model choosing to omit fields would not reliably omit
   exactly the trailing ones.
2. `statement_classifications` is an array with `maxItems: 24` of objects whose statement field
   allows 300 characters. At its documented maximum **that one field serialises to roughly 8160
   characters, about 3784 tokens** at this deployment's measured 2.1565 characters per token —
   larger than the entire 3000-token cap.
3. **Mission 1.31.1 recorded the identical signature for the identical cause**: a cap of 1500
   smaller than the requested schema could serialise, with *the last five required fields
   missing*. Raising it to 3000 fitted the 17-field schema of that day.

**It is not established.** Proving truncation rather than model omission needs the raw bytes and
the output token count, and neither was kept. The evidence above is arithmetic about the schema
plus a matching signature in this repository's own history. **It is not the response.** Byte-level
truncation is explicitly not claimed, and neither is any statement about what the model would have
written under a larger cap.

---

## The defect in Mission 1.84

**`OUTPUT_CAPACITY_BOUND_NOT_DERIVED_FROM_SCHEMA = true`.**

Mission 1.84 froze `second-opportunity-synthesis-output@1.0.0` with 20 required fields, and
independently froze `MAX_OUTPUT_TOKENS` at 3000. It derived the **input** token estimate from a
measured characters-per-token ratio, and derived the worst-case cost from that estimate. It never
derived the **output** ceiling from the maximum valid serialised size of the schema it was
freezing.

Worse: that report cited Mission 1.31.1 by name for having raised the cap to 3000, and did not
re-check that the raised cap still fitted a schema three fields larger — one of them the largest
field in it. **The lesson was quoted and not applied.**

**No corrected ceiling is concluded here.** That belongs to Mission 1.84.3, and a closure mission
that also fixed the thing it was closing would be doing the next mission's reasoning without the
next mission's scrutiny.

---

## What was not changed

The output contract is untouched: `second-opportunity-synthesis-output@1.0.0` keeps its 20
required fields, `second-opportunity-output-gate@1.0.0` is unchanged, `confidence_classification`
is still required, `statement_classifications` keeps `maxItems: 24`, no field was reordered and no
default was invented for a missing one. **The failed response remains invalid**, and 18 of 20
fields is not an Opportunity.

The frozen packet is byte-identical and its own `OPERATOR_EXECUTION_APPROVAL_RECORDED` still reads
false. The representation and prompt digests are the approved ones.

---

## What was repaired, and what was not tested

For a **future separately-approved** execution:

- A recording transport keeps the response bytes as they arrive, so a validation exception can no
  longer destroy provider material the retention policy requires. It lives in the runner rather
  than in the Gateway, because what to retain is a per-mission decision and not a property every
  caller should inherit.
- A telemetry sink captures the usage record the Gateway already emits on the failure path.
- One execution-artifact shape is written on **every** terminal path: success, transport failure,
  provider-shape failure, parse failure, schema failure and timeout.
- Hidden-reasoning keys are stripped at any depth, and none is requested.
- Credential-shaped strings are redacted before anything is written.

**The repair was not exercised against a provider, because a test call is a second call.** It is
exercised by seven synthetic transports — success, missing fields, malformed JSON, provider-shape
failure, timeout, transport exception, and a semantic rejection — each asserting the artifact it
produces. The missing-fields fixture is the consumed call's own shape, and it retains both the raw
response and the token counts, which is precisely what was lost. A further test replaces
`UrllibTransport.__init__` with a tripwire and asserts **no fixture constructs the real
transport**.

---

## Why no second call was made

The approval authorised exactly one execution and one execution happened. A timeout, a malformed
response, a missing retention artifact and uncertainty about the cause **do not create additional
authority**. The closure made zero provider requests, zero remote test calls, and transmitted zero
TED bytes. Repairing the recorder and wanting to see it work is exactly the reasoning that would
have produced a second call, and it was refused.

---

## Adversarial probe

**74 deliberate violations, 74 caught, 0 escaped. 8 positive controls, 8 accepted.**

The violations share one theme: making a failed call cost less than it did. An approval marked
unused, a second request, a fallback, V1's digest repointed, `MAX_OUTPUT_TOKENS` changed inside
V1, a required field made optional, `confidence_classification` removed, `maxItems` changed, a
reconstructed raw-response hash, invented tokens, an invented cost, the worst case recorded as the
actual cost, the hypothesis promoted to ESTABLISHED, truncation claimed, a retention defect erased,
an Opportunity persisted from 18 of 20 fields, a stage that never ran recorded as passing, a
credential in the record, and a provider request during the closure.

The controls prove the honest states stay representable: a consumed approval, a schema rejection,
unknown usage, unknown raw-response bytes, a strongly-supported hypothesis with a fourth
supporting fact, a second consumed approval appended later, stricter closure accounting, and more
repairs recorded. Every case restores the files, and the probe asserts V1's digest is where it
started.

---

## Verification

`ruff format --check` and `ruff check` clean over 984 files. `mypy` clean over 199 files across the
14 CI package paths. Contracts, catalog and review results in sync. Source registry: 29 sources,
45 evidence records, 0 warnings. **All 66 CI gates green locally**, the new one included. 3831
bare-python tests across 9 packages; 3431 pytest, database reported unchanged across 29 tenant
tables.

**Every canonical counter matches the expected state exactly**, measured against the live
database: RawRecords 325, NormalizedRecords 325, Signals 60, Claims 91, ClaimRevisions 92,
Evidence 112, ReliabilityAssessments 4, EvidenceIndependenceGroups 0, Opportunities 1,
OpportunityRevisions 2, OpportunityEvidenceLinks 14, Embeddings 0, Scores absent. Source reviews
71, unchanged since Mission 1.84.1.

---

## Mission 1.84.3 handoff

**Mission 1.84.3 — Second Opportunity Output Capacity Derivation & Execution Packet V2.**

Its job:

- **zero model calls**;
- preserve `second-opportunity-synthesis-output@1.0.0` unless changing it is independently
  justified, with the cost of changing the contract stated;
- derive a worst-case or otherwise defensible maximum serialised output size **from the actual
  schema** rather than from a previous mission's number;
- derive a new output-token ceiling from that size rather than guess one;
- recompute the worst-case cost and the execution cost ceiling from the new ceiling;
- verify the repaired retention path;
- produce a **new** execution packet, compute its **new** digest, and require a **new** operator
  approval.

**None of that was done here.** This mission records the requirement and stops.

---

## Stop

Do not start Mission 1.84.3 from this branch. Do not change the output-token ceiling. Do not create
execution packet V2. Do not seek approval for another call. Do not call the provider, retry the
synthesis, or persist Opportunity #2.

`SECOND-OPPORTUNITY-SYNTH-EXEC-V1` is spent. The next call needs a new packet and a new decision
that is the operator's to make.
