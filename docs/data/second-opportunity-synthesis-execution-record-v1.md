# Second Opportunity synthesis execution record

Generated from `second-opportunity-synthesis-execution-record-v1.json`. Do not edit by hand.

**SECOND_OPPORTUNITY_EXECUTION_REJECTED_AND_CLOSED_NO_RETRY**

Mission 1.84.2. The one approved provider request happened, its output was rejected at schema validation, no retry occurred and nothing was persisted. Two things the frozen retention policy required were NOT retained, and both are defects in this mission's own runner rather than properties of the response. This record is also the durable fact the one-call guard reads: an approval is spent by its execution, whatever the output turned out to be.

The transport succeeded and the provider answered. The answer carried 18 of the 20 required fields and was refused at validation stage 4. A refusal is not a provider failure, and it is not a reason to call again.

## The approval, and that it is spent

- packet `SECOND-OPPORTUNITY-SYNTH-EXEC-V1` v1
- digest `570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92`
- **EXECUTION_APPROVAL_CONSUMED = True**
- **FURTHER_CALLS_AUTHORIZED_BY_V1 = False**
- frozen packet unchanged: True

The approval authorised exactly one execution and one execution was performed. A failed call is not an unused approval. Reinterpreting a rejected output as unspent authority is the single most tempting error available here, and it is refused by a deterministic guard rather than by memory.

## The eight pre-execution checks

| check | result |
|---|---|
| 1_execution_packet_sha256_recomputed | `570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92` |
| 1_matches_approval | `True` |
| 2_version_unchanged | `True` |
| 2_packet_approval_flag_still_false | `True` |
| 3_representation_sha256_recomputed | `2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72` |
| 3_representation_characters | `3604` |
| 3_matches_approval | `True` |
| 4_prompt_sha256_recomputed | `af5289494416139d302eed704c12b9c53ab2547dca336e2ca4a834ec936c5080` |
| 4_matches_approval | `True` |
| 5_provider_posture | `APPROVED` |
| 6_ted_external_model_transmission | `PERMITTED_WITH_CONDITIONS` |
| 6_selected_packet_gate | `AVAILABLE` |
| 6_live_gate_refusal_reasons | `[]` |
| 7_all_bound_execution_parameters_matched_v1 | `True` |
| 8_refused_before_sending | `False` |
| verified_at | `2026-09-11T18:01:39.558931+00:00` |

These establish why the **historical** call was authorised. They are not current permission for another one.

## What happened

- provider `anthropic`, model `claude-sonnet-5`
- route Anthropic API under the Commercial Terms
- provider requests **1**, retries **0**
- transport **SUCCESS**, provider answered True
- validation **REJECTED** at **4_schema_validation**
- 18 of 20 required fields present

Missing: `confidence_classification`, `statement_classifications`.

The two missing fields are the LAST TWO in the schema's required order. Fields 1 through 18 were present. Their NAMES survive only through the validator's error message, because the fields themselves were not retained.

| stage | result |
|---|---|
| 1_transport_success | **PASSED** |
| 2_provider_response_shape | **PASSED** |
| 3_exact_structured_output_parse | **PASSED** |
| 4_schema_validation | **FAILED** |
| 5_semantic_output_gate | **NOT_REACHED** |
| 6_evidence_boundary_gate | **NOT_REACHED** |
| 7_attribution_and_no_distortion_gate | **NOT_REACHED** |
| 8_canonical_persistence_eligibility | **NOT_REACHED** |

## What was not retained

- `RAW_PROVIDER_RESPONSE_RETAINED` **False**, hash `NOT_AVAILABLE`, recoverable False
- `USAGE_RETAINED` **False**
- actual tokens and cost: **NOT_ESTABLISHED**

The frozen retention policy says the raw response is RETAINED, because a gate verdict over a response nobody kept is unverifiable. The runner let the Gateway's validation exception propagate, and the Gateway builds its result locally, so the bytes were discarded at exactly the moment they were worth most. No transport recorder was registered on the consumed call. This is a defect in this mission's runner, not a property of the response, and it is an audit limitation rather than a finding about the provider.

The Gateway emits a usage record on the failure path as well as the success path, carrying the provider-reported token counts, but only to a telemetry sink. The runner registered none, so the record went nowhere. A second defect in this mission's runner.

`ACTUAL_COST_UNKNOWN_BUT_EXECUTION_WAS_AUTHORIZED_UNDER_V1_CEILING`. The approved worst case was 0.04825 cost units against a ceiling of 0.1. The frozen worst case is an upper bound computed before the call. It is not what the call cost, and no figure here claims to be.

## The cause, and what it is not

**OUTPUT_CAPACITY_FAILURE_HYPOTHESIS = STRONGLY_SUPPORTED**

**ROOT_CAUSE = NOT_PROVABLE_FROM_RETAINED_EXECUTION_ARTIFACTS**

The frozen MAX_OUTPUT_TOKENS of 3000 is too small for the schema Mission 1.84 froze, so serialisation ran out of budget before the trailing required fields appeared.

- The two missing fields are positions 19 and 20 of 20 in the schema's required order, and fields 1 through 18 were present.
- `statement_classifications` is an array with maxItems 24 of objects whose statement field allows 300 characters. At its documented maximum that one field serialises to roughly 8160 characters, about 3784 tokens at this deployment's measured 2.1565 characters per token, which is larger than the entire 3000-token output cap.
- Mission 1.31.1 recorded the identical signature for the identical cause: an output cap of 1500 smaller than the requested schema could serialise, with the last five required fields missing. Raising it to 3000 fitted the 17-field schema of that day.

Proving that the response was truncated rather than that the model omitted two fields requires the raw bytes and the output token count, and the runner retained neither. The evidence above is arithmetic about the schema plus a matching signature in this repository's own history. It is not the response.

Not claimed:

- that byte-level truncation occurred
- that the model would have produced a valid answer under a larger cap
- that the provider did anything other than return a response

## The defect in Mission 1.84

**OUTPUT_CAPACITY_BOUND_NOT_DERIVED_FROM_SCHEMA = True**

Mission 1.84 froze `second-opportunity-synthesis-output@1.0.0` with 20 required fields, and independently froze MAX_OUTPUT_TOKENS at 3000. It derived the INPUT token estimate from a measured characters-per-token ratio and derived the worst-case cost from that estimate, and it never derived the OUTPUT ceiling from the maximum valid serialised size of the schema it was freezing. The 1.84 report cited Mission 1.31.1 by name for having raised the cap to 3000 and did not re-check that the raised cap still fitted a schema three fields larger, one of them the largest field in it.

## What was repaired, and what was not tested

- A recording transport keeps the response bytes as they arrive, so a validation exception can no longer destroy provider material the retention policy requires.
- A telemetry sink captures the usage record the Gateway already emits on the failure path, so token counts and cost survive a rejected output.
- One execution artifact shape is written on every terminal path: success, transport failure, provider-shape failure, parse failure, schema failure and timeout.
- Hidden-reasoning keys are stripped at any depth, and none is requested.
- Credential-shaped strings are redacted before anything is written.

Exercised against a provider: **False**. Exercised by synthetic transports only, with a test asserting no fixture can reach a network.

## The one-call guard

- mechanism: The runner reads this record's CONSUMED_APPROVALS before executing and refuses a packet digest that already has a provider request against it.
- refusal: `EXECUTION_APPROVAL_ALREADY_CONSUMED`
- depends on human discipline: **False**
- frozen packet modified to achieve it: **False**

The guard lives beside the frozen packet rather than inside it, because editing a frozen document to say it has been used changes the bytes that were approved.

## What was persisted

**PERSIST_NOTHING was the instruction for a failing gate, and it is also what the frozen persistence policy required regardless: nothing persists without a human reading the output first, and there is no valid output to read.**

`canonical_persistence` False, HUMAN_OUTPUT_REVIEW_REQUIRED True, review packet produced False.

There is no valid structured output to review. Assembling a review packet from a response the contract already rejected would ask a person to read something that is not an answer.

## Accounting

| counter | value |
|---|---|
| TOTAL_PROVIDER_REQUESTS_FOR_MISSION_1_84_2 | 1 |
| ADDITIONAL_PROVIDER_REQUESTS_DURING_FAILURE_CLOSURE | 0 |
| REMOTE_TEST_CALLS_DURING_CLOSURE | 0 |
| MODEL_CALLS_DURING_CLOSURE | 0 |
| TED_BYTES_SENT_DURING_CLOSURE | 0 |
| TED_BYTES_SENT_BY_THE_CONSUMED_CALL | 3604 |
| CANONICAL_RESEARCH_MUTATION | 0 |
| CREDENTIAL_VALUES_PRINTED_OR_PERSISTED | 0 |

The approved representation, transmitted once under the approved permission. The first time TED-derived material has left this machine.

**Next: NEW_EXECUTION_PACKET_AND_NEW_OPERATOR_APPROVAL.** MAX_OUTPUT_TOKENS is a field the execution digest BINDS. Changing it produces a different digest, so the approved packet cannot be re-run with a larger cap: that would be a different call wearing an approved packet's name.
