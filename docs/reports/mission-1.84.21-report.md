# Mission 1.84.21: Strict First-Request Timeout Alignment, V8 Supersession & Execution Packet V9

**`SECOND_OPPORTUNITY_EXECUTION_PACKET_V9_READY_FOR_OPERATOR_APPROVAL`**

The operator accepted every architecture and governance decision in V8 except its 60-second client
timeout. The provider documents that strict tool use may compile a grammar on the first request for a
schema, for an undocumented time, with a compilation timeout of 180 seconds: V8's one attempt could
give up while the provider was still allowed to be compiling.

- **The operator set V9's client timeout to 240 seconds**, as an availability budget. It is not a
  provider guarantee, not a latency prediction, not a statistical estimate and not a billing bound.
- **V8 was superseded before execution.** It was never approved, never executed and never consumed.
  Its packet is untouched, and its runner now refuses its digest as
  `EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION` before its approval is read and before any transport.
- **Packet V9 is V8 with that timeout and nothing else.** The timeout is no part of the provider body,
  so the body is V8's bytes; it enters neither cost figure, so the ceiling is still 3.608. V9 is frozen
  and unapproved, and both risks are left for the operator to decide.
- **Nothing was sent.** 0 model calls, 0 provider requests, 0 token-count requests, 0 TED bytes, 0
  canonical mutation, and no documentation page requested: the provider facts are those gate 94 holds.

```
START_COMMIT        3c5bcaf3bb36dcd0f19f9f48ed9447f4afac1eff
BRANCH              sprint-1/mission-1.84.21

PACKET              SECOND-OPPORTUNITY-SYNTH-EXEC-V9 v9
                    ba681da94b3e89f22c7e39bdb2dc4ef95d0527ca3db561c849eb089652d9425d
APPROVAL            none recorded; NEW_APPROVAL_REQUIRED = true

PRIMARY_OUTCOME     SECOND_OPPORTUNITY_EXECUTION_PACKET_V9_READY_FOR_OPERATOR_APPROVAL
```

## The operator's decision

Carried as data in gate 96's record and in V8's supersession:

```
ACCEPT_ALL_V8_ARCHITECTURE_AND_GOVERNANCE_EXCEPT_THE_60_SECOND_CLIENT_TIMEOUT
KEEP_OUTPUT_SCHEMA_V1_2_0, KEEP_SEMANTIC_GATE_V1_4_0, KEEP_PROMPT_V1_5_0
KEEP_PROVIDER_STRICT_MODE_TRUE, KEEP_STRICT_PROJECTION_V1_0_0, KEEP_STRICT_CAPABILITY_PROFILE_V1_0_0
KEEP_STRICT_PROJECTION_FREEZE_COMMIT_57154AFF, KEEP_TED_REPRESENTATION_2528A56A
KEEP_GENERATION_HEADROOM_4_OVER_5, KEEP_SUMMARY_HARD_MAXIMUM_1500_AND_TARGET_1200
KEEP_HARD_EXECUTION_COST_CEILING_3_608_PROVEN, KEEP_PLANNING_COST_ESTIMATE_1_316316
DO_NOT_APPROVE_V8
SUPERSEDE_V8_BEFORE_EXECUTION
CREATE_V9_WITH_ONLY_CLIENT_TIMEOUT_CHANGE
REQUEST_TIMEOUT 60.0 -> 240.0 SECONDS
240_SECONDS_IS_AN_OPERATOR_AVAILABILITY_BUDGET
```

The operator also stated a future preference, `RESIDUAL_SEMANTIC_LIMITATION_INTENDED_FOR_V9_APPROVAL =
ACCEPT`. It is recorded as an intention, with `IS_AN_APPROVAL = false`; the packet carries the
acceptance as `false`, and only V9's approval may set it.

## V8, reconfirmed

Recomputed from the committed packet (its digest by gate 95's own function) and from the body rebuilt
through the V8 runner, never sent:

```
packet                         SECOND-OPPORTUNITY-SYNTH-EXEC-V8 v8
sha256                         583946460c6cf68c1be5519916f92d268e36ed65924aeb24901731439586c399
packet file bytes              4ec6c6bf91fdd88ae9c374336b74880cc7c6a24386850cc2a1df297c1de549da
approval recorded              false (no approval file)
execution record / response    absent / absent
provider requests              0
REQUEST_TIMEOUT                60.0
HARD_EXECUTION_COST_CEILING    3.608 (proven)
PLANNING_COST_ESTIMATE         1.316316
request body                   31326 characters, 58956019f78f414ee11392bee5e99eedda4eb1b4deb20d3f20219dfc60739842
provider strict mode           true
timeout in the provider body   false
```

## The mismatch: a possibility, not a frequency

From the first-party fragments gate 94 already holds (the structured-outputs page, D04, read on
2026-09-14), with no new request:

```
STRICT_GRAMMAR_COMPILATION                                MAY_OCCUR_ON_THE_FIRST_REQUEST_FOR_A_SCHEMA
STRICT_GRAMMAR_COMPILATION_LATENCY                        NOT_ESTABLISHED
PROVIDER_GRAMMAR_COMPILATION_TIMEOUT                      180 seconds
CURRENT_CLIENT_REQUEST_TIMEOUT                            60 seconds
MAX_RETRIES                                               0
CLIENT_TIMEOUT_IS_SHORTER_THAN_PROVIDER_COMPILATION_TIMEOUT   true
CLAIMS_A_REQUEST_WILL_EXCEED_60_SECONDS                   false
```

Nothing here says a request will take longer than 60 seconds. V2 to V6 finished in 33 to 36 seconds,
and none of those observations entered the decision.

## The decision

```
REQUEST_TIMEOUT                   60.0 s -> 240.0 s
DECISION_OWNER                    OPERATOR
DECISION_TYPE                     EXECUTION_AVAILABILITY
BASIS                             OPERATOR_AVAILABILITY_BUDGET
MATHEMATICALLY_DERIVED            false
STATISTICALLY_ESTIMATED           false
PROVIDER_GUARANTEED               false
LATENCY_PREDICTION / BILLING_BOUND   false / false
GUARANTEES_SUCCESSFUL_COMPLETION  false
CLIENT_TIMEOUT_EXCEEDS_PROVIDER_COMPILATION_TIMEOUT   true
TIMEOUT_MISMATCH_REDUCED          true
TIMEOUT_RISK_ELIMINATED           false
END_TO_END_LATENCY_BOUND          NOT_ESTABLISHED
RETRY_ADDED_TO_OFFSET_THE_RISK    false   (MAX_RETRIES stays 0)
```

The reasoning is the operator's: a client-side budget beyond the documented 180-second compilation
timeout, with additional operational margin. It predicts no latency and does not make the one attempt
succeed: compilation and generation together are bounded by nothing documented.

**The 240 seconds reach the wire.** The value travels unchanged from the request to
`urllib.request.urlopen(timeout=...)`, a socket timeout on the blocking operations of one non-streamed
request. The gateway applies no ceiling of its own, and the deployment's `LLM_REQUEST_TIMEOUT_SECONDS`,
which still says 60, is not read on this path. Gate 97 checks the timeout the runner's built request
carries, not only the packet's field, and that the request carries no retry.

## Cost, unchanged

The timeout is no part of the provider body, no term of gate 94's derivation, and no published charge.
Gate 94's record is unchanged (`2184ff40...`) and re-derived inside gate 96:

```
HARD_EXECUTION_COST_CEILING         3.608   proven
PLANNING_COST_ESTIMATE              1.316316
TIMEOUT_ENTERS_THE_COST_DERIVATION  false
TIMEOUT_CHANGES_BILLING             false
TIMEOUT_RELATED_PROVIDER_FEE        NONE_PUBLISHED
```

## V8's supersession

`second-opportunity-synthesis-execution-supersession-v8.json`, beside V8's packet as V7's is beside
V7's:

```
STATUS                  SUPERSEDED_BEFORE_EXECUTION
REASON                  CLIENT_TIMEOUT_SHORTER_THAN_PROVIDER_STRICT_COMPILATION_TIMEOUT
V8_EXECUTED             false
V8_APPROVED             false
V8_APPROVAL_CONSUMED    false
V8_PACKET_MODIFIED      false   (its bytes pinned by gate 96)
NOT_DESCRIBED_AS        FAILED, CONSUMED, REJECTED_BY_PROVIDER
REFUSAL_OUTCOME         EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION
```

**One Mission 1.84.20 file was changed, and only to make V8 non-executable.** The V8 runner is the only
code that can send V8, so it now reads the supersession record: `refuse_if_superseded` is called inside
`refuse_if_consumed`, which `execute()` calls before the approval is read and before a transport
exists, and which verification and `--execute` call. V8's packet and every frozen artifact are
untouched, and gate 95 and the V8 runner's own tests still pass unchanged. Gate 96 exercises the guard
with no approval and with a forged one written to a temporary directory: V8 is refused as superseded
both times, before any transport. Run against the research database with every network path
tripwired, V8's verification and its `--execute` both stop there:

```
REFUSED  nothing was sent: EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION: execution packet 58394646...
         was superseded before it was approved or executed
         (CLIENT_TIMEOUT_SHORTER_THAN_PROVIDER_STRICT_COMPILATION_TIMEOUT)
```

V1 to V6 are still refused as `EXECUTION_APPROVAL_ALREADY_CONSUMED`, V7 as superseded, and an unseen
digest is not refused.

## What did not move

```
output schema          second-opportunity-synthesis-output@1.2.0     7d67bad3...
semantic gate          second-opportunity-output-gate@1.4.0          eb03899b...
prompt                 second-opportunity-synthesis-prompt@1.5.0     0713eb80...
strict mode            true, FORCED_STRICT_TOOL_USE, one tool, forced tool_choice
strict projection      87028f451205494a948e83740e73b9ca59ce3243f54e24c123b7cc2354c69783
capability profile     7f3ed84547d163c330d637f6a0171b527017399bb6738cdcccc55cad08b24313
projector              4eef60b03ac48caf72e337af7e9e1ad07b05d3fe3d14412dfe7ce7287679f02e
projection tests       fe4abd1cd6512ef70f237bb9ab5dbfc19a657bc5983436fe04ec6c21e0f115d9
freeze commit          57154affb934516650b84480c2438a75c9b9a5a5  (an ancestor of origin/main)
TED representation     2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72
route                  anthropic, POST https://api.anthropic.com/v1/messages, Commercial Terms, synchronous
model                  claude-sonnet-5, thinking DISABLED, max_tokens 128000, 1 call, 0 retries
summary                hard maximum 1500, target 1200, ratio 4/5
completion, retention  V8's exactly: completion read before any parse; tool_use complete; max_tokens,
                       context-window exceeded, refusal and any other value fail closed; raw response,
                       usage, ids, cost and stage verdicts kept; the post-call fail-safe; no fallback,
                       continuation or repair
```

Among the fields V8's digest bound, V9 differs from V8 in its identity, its predecessor, the
superseded list, `REQUEST_TIMEOUT`, the generation parameters' `timeout_seconds`, and the body
differential's own labels, and nowhere else; a gate 97 test pins that list.

**The request body is V8's, byte for byte**: V8's runner and V9's build the same 31326 characters over
the same snapshot, `58956019...`, `REQUEST_BODY_DIFFERENCES_V8_TO_V9 = 0`, and no key in it names a
timeout.

## Two risks, not accepted here

- **Residual semantic limitation.** `RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V9 = false`. The operator
  intends to accept it; only V9's approval may.
- **First strict request's timeout.** 240 seconds exceeds the documented 180-second compilation limit,
  so the mismatch is reduced; compilation and generation together are bounded by nothing documented,
  so the one attempt, with no retry, may still end before an answer arrives.
  `STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9 = false`, `TIMEOUT_RISK_ELIMINATED = false`,
  `END_TO_END_LATENCY_BOUND = NOT_ESTABLISHED`.

The V9 runner refuses any approval that does not decide both, explicitly and as booleans, under V9's
own names (V8's names decide nothing), and executes only if both are accepted. Gate 97 exercises that
check on synthetic approvals written to a temporary directory.

## V9's stages, on synthetic answers

Through the V9 runner's own `validate_execution`, with no transport:

| fixture | summary | must stop at | stopped at |
|---|---|---|---|
| A_VALID | 237 | stage 9 | stage 9, accepted for human review only |
| B_SEMANTIC_FAILURE | 237 | 6 | 6 |
| B2_STRAY_ID_REFUSED_BY_THE_GATE | 237 | 6 | 6 |
| C_EVIDENCE_BOUNDARY_FAILURE | 237 | 7 | 7 |
| D_ATTRIBUTION_FAILURE | 237 | 8 | 8 |
| E_PERSISTENCE_ELIGIBILITY_FAILURE | 235 | 9 | 9 |
| F_LONG_SUMMARY_POSITIVE | 1189 | stage 9 | stage 9 |
| G_LONG_SUMMARY_SEMANTIC_NEGATIVE | 1216 | 6 | 6 |
| H_SUMMARY_AT_THE_NEW_BOUND | 1500 | stage 9 | stage 9 |
| I_SUMMARY_ONE_OVER_THE_NEW_BOUND | 1501 | 5 | 5 |
| J_EXTRA_ROOT_PROPERTY_REFUSED_AT_LOCAL_STAGE_5 | 237 | 5 | 5 |

Strict mode is not a numbered stage.

## Packet V9

```
EXECUTION_PACKET_ID                 SECOND-OPPORTUNITY-SYNTH-EXEC-V9
VERSION                             9
SHA256                              ba681da94b3e89f22c7e39bdb2dc4ef95d0527ca3db561c849eb089652d9425d
immediate predecessor               V8 58394646...  SUPERSEDED_BEFORE_EXECUTION
previous predecessor                V7 51023d0d...  SUPERSEDED_BEFORE_EXECUTION
last executed predecessor           V6 969128dd...  EXECUTION_SCHEMA_REJECTED_NO_RETRY
schema / gate / prompt              v1.2.0 / v1.4.0 / v1.5.0
strict                              true, projection v1.0.0, freeze 57154aff...
provider / route / model / thinking unchanged
MAX_OUTPUT_TOKENS / CALLS / RETRIES 128000 / 1 / 0
REQUEST_TIMEOUT                     240.0 s   OPERATOR_AVAILABILITY_BUDGET
REQUEST_BODY_SHA256                 58956019...
PLANNING_COST_ESTIMATE              1.316316
HARD_EXECUTION_COST_CEILING         3.608, proven
human review                        required
canonical persistence               only after stages 1 to 9 and a separate human approval
RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V9        false
STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9   false
OPERATOR_EXECUTION_APPROVAL_RECORDED                false
NEW_APPROVAL_REQUIRED                               true
PREVIOUS_APPROVAL_REUSABLE                          false
```

**The V9 runner's verification ran against the research database, with every network path tripwired,
and sent nothing.** It found exactly what the packet records: digest `ba681da9...`, V1 to V6 consumed,
V7 and V8 superseded, representation `2528a56a...` (3604 characters), prompt `0713eb80...`, 0/0/0
unstated constraints, rules and targets, `FROZEN_PROJECTION_STRICT_FORCED`, a 31326-character body
hashing to `58956019...`, a request waiting 240.0 seconds, a hard ceiling of 3.608 and a planning
estimate of 1.316316, and `OPERATOR_APPROVAL_NOT_RECORDED`. Its `--execute` refused there.

**Its first run did not get that far, and the defect was the gate's.** The V9 runner asks its packet
authority, gate 97, for `freeze_gate()`, as the V8 runner asks gate 95; gate 97 did not define it, and
verification stopped with an `AttributeError` before any transport existed. Gate 97 now defines it,
checks that the runner's packet authority exposes every function the runner calls on it, so the same
omission fails in CI rather than on the preparing machine, and a test covers it. Preparing the probe
also showed that nothing checked the retry count of the request the runner builds, as distinct from the
packet's field: gate 97 now refuses a runner whose built request would retry.

## CI gates 96 and 97

**Gate 96** (`render_second_opportunity_execution_timeout_decision.py`) re-derives the timeout decision
and V8's supersession, and refuses: a timeout other than 240, or one called provider-guaranteed,
derived, estimated, a latency prediction or a billing bound; an end-to-end latency bound claimed or the
risk said eliminated; a retry added to offset it; the mismatch misstated, or a request claimed to take
longer than 60 seconds; the timeout said to enter the body or the cost, or a timeout fee invented; the
operator's intention recorded as an approval; V8 edited, approved, executed, or recorded as consumed,
failed or refused by the provider; and a V8 runner that no longer refuses V8, by name, before its
approval and any transport.

**Gate 97** (`render_second_opportunity_execution_packet_v9.py`) re-derives packet V9, reusing gate 93's
checks of what did not move and gate 95's of the cost, and refuses: bound fields that do not hash to
the digest, a spent or superseded digest, an unreviewed field, an approval recorded by the preparing
mission or either risk accepted by it; V1 to V6 edited or their consumption reset, V7 or V8 described
as anything but superseded before execution; a timeout other than 240 in the packet, the request
parameters, the TIMEOUT block or the built request, or one misdescribed or offset by a retry; a
contract, gate, prompt, projection, freeze, route, model, thinking, max_tokens, retention, completion
or persistence policy moved; a body that is not V8's bytes; a cost figure moved; a synthetic answer
that does not stop where it must; a runner whose guard renames a refusal, whose approval check does not
demand and exercise both of V9's risk decisions, or that would execute V1 to V8; and any preparation
call, documentation read, TED byte or canonical counter.

## Probe (section 19)

**The probe's first run found a defect in gate 96, and it was fixed before the run that counts.** Five
violations were refused, but by gate 94's rule raised through gate 96 under gate 94's exception type,
which the probe counted as unnamed: the cost ceiling moved, V7 restored by deleting or editing its
supersession, an approval of V7 appearing, and V6's consumption reset. Gate 96 called gate 94's
`validate()` without naming its refusal, the defect Mission 1.84.19 fixed in gate 93. Gate 96 now
reports a refusal of gate 94, or of gate 95's snapshot, as its own (`gate 94 no longer validates:
...`), and a test covers it. Nothing escaped in the first run (95 caught, 0 escaped, 30 of 30 controls).
**The second run refused all 95 violations by a named rule, and one positive control failed on the
network.** The control that finds the freeze commit on origin got nothing from `git ls-remote`, and
`git fetch` and `git merge-base` both exited 128: git could not reach origin at that moment. The same
three commands, run by hand at once, succeeded (`ls-remote` printed `3c5bcaf`, the freeze an ancestor
of the fetched `main`). The probe did not record git's error output; it now does. It was run a third
time rather than the control being counted as passed.

**The third run counts: 95 violations caught, 0 escaped, 30 of 30 positive controls, every file proved
restored.** `VIOLATIONS_ESCAPED = 0`, `POSITIVE_CONTROLS_FAILED = 0`. 93 were refused by a named rule of
gate 96 or gate 97, 2 by render drift, 0 by a crash. The real transport's constructor and `urlopen`
were tripwired for the whole run, in the probe's process and every child, and no transport was
constructed.

**Data, edited on disk and judged by gate 96's and then gate 97's full validation** (74 cases; every
bound edit to packet V9 was re-digested, so the digest could not be what refused it):
- V8 (11): an approval, an execution record or a response appearing; V8 called consumed or failed, its
  refusal named as a spent approval, marked approved, its supersession deleted or given another reason,
  its packet edited with and without a new digest;
- the timeout decision (17): 240 called provider-guaranteed, statistically or mathematically derived,
  an end-to-end latency bound claimed, the risk said eliminated, a retry added, a timeout of 300, the
  timeout risk accepted, the intention recorded as an approval or as the acceptance, a request claimed
  to exceed 60 seconds, the compilation latency claimed known, the timeout said to change billing, a
  timeout fee invented, a timeout said to be in V8's body, a provider or token-count request;
- the cost record and V7 (4): the ceiling moved, V7 restored by deleting or editing its supersession, an
  approval of V7 appearing;
- packet V9 (39): the timeout left at 60 or changed to 180 or 300, in the packet, the request
  parameters or the TIMEOUT block; 240 called guaranteed or derived, a latency bound claimed, the risk
  said eliminated, billing said to change, a retry in the packet or the parameters, another basis; the
  body identity, strict mode, the mechanism, the contract, gate, prompt and representation digests, the
  ceiling and the estimate moved; V8 called consumed or its approval consumed, its supersession
  omitted, V7 restored; either risk accepted, in the packet or in TIMEOUT, the intention recorded as an
  approval, V8's risk flags carried; a provider, model or token-count call; V9 marked approved or a
  previous approval reusable; V8's digest replayed; a bound field moved without its digest; the freeze
  moved;
- history and approvals (3): V6's consumption reset, V6's approval placed beside V9, V9 approved by the
  mission that prepared it.

**Live code, edited and judged by gate 97 in a fresh interpreter** (19 cases): the V8 runner's
supersession guard made a no-op or no longer called, V8 refused under the consumed name; the V7
runner's guard made a no-op; the V9 runner's timeout back to 60, its request built with another
timeout or with a retry, its guard no longer reading V8's, a superseded refusal renamed, its approval
check no longer demanding the risk decisions, its body changed, its ceiling pinned at the estimate, its
local stage 5 removed; the strict adapter's flag set false; the projector edited after the freeze;
schema v1.2.0's 1500 moved to 1100; the shared validator's closed-object check removed; prompt v1.5.0
extended; gate v1.4.0 edited.

**The rendered pages**, hand-edited (2 cases, by drift).

**The 30 positive controls:**
- the shipped gates 92 to 97, a comment in the V9 runner and one in gate 97's tests;
- V8's digest and bytes unchanged, V8 unapproved and unexecuted, V8 and V7 each refused by their own
  runners as superseded;
- V1 to V6 each refused as consumed through the V9 runner, and the unseen V9 digest awaiting approval;
- V8's and V9's bodies byte-identical at `58956019...`, with no timeout in them;
- the cost record unchanged and V9's cost figures V8's;
- the strict freeze exact;
- the timeout exactly 240 in the packet, the runner and the request it builds, with no retry;
- the mismatch reduced and no end-to-end latency bound established;
- the synthetic path: valid, 1189 and 1500 characters to stage 9, semantic to 6, boundary to 7,
  provenance to 8, persistence to 9, 1501 and an extra root property to 5;
- a V9 `--execute` refused as `OPERATOR_APPROVAL_NOT_RECORDED` and a V8 `--execute` refused as
  superseded, both before any network, with `execute()` replaced by a function that raises;
- no transport constructed in the probe or in any child;
- the freeze commit found on origin by `git ls-remote` and `git merge-base --is-ancestor` against the
  fetched `main`, never read from local HEAD.

## Technical debt, recorded and not changed

The frozen projector test `test_anthropic_strict.py::test_no_beta_header_is_added` still builds
`AnthropicProvider(api_key="k")` without a transport, so the adapter constructs a real `UrllibTransport`
it never uses. It sends nothing. The file is part of the strict freeze (`fe4abd1c...`), which V7, V8
and V9 bind, and this mission changes no frozen artifact. The deployment's `LLM_REQUEST_TIMEOUT_SECONDS`
still says 60; this path does not read it, and it was left alone.

## Accounting

```
MODEL_CALLS                0
PROVIDER_REQUESTS          0
MESSAGES_API_REQUESTS      0
TOKEN_COUNT_API_REQUESTS   0
TED_BYTES_SENT             0
CANONICAL_MUTATIONS        0
documentation requests     0
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

## Verification

- `ruff format --check` and `ruff check` are clean over 1147 files, and `mypy` over 215.
- Contracts, catalog and source registry are clean.
- **3877 bare-python tests and 6210 pytest tests** pass, 13 skipped. The database is unchanged across
  29 tenant tables; the global tables are unchanged across 17, with 11 rows appended by the suites to
  1 append-only table, as the checker reports.
- **285 new tests**: 69 on gate 96, 120 on the V9 runner (every V8 runner test kept and run against
  V9's runner with the timeout at 240, and V9's governance: V1 to V6 spent and V7 and V8 superseded
  under their own names, both of V9's risk decisions demanded, the 240-second wait on the transport, no
  timeout in the body, V8's bytes, V8's cost figures) and 96 on gate 97. **No test was re-pointed**: the
  V8 runner's 120 tests and gate 95's 91 pass unchanged after the guard was added.
- **97 CI gates**, two of them new (96 and 97), all run locally with no failure.
- The V8 and V9 runners' verification ran against the research database with every network path
  tripwired, and sent nothing: V8's verification and `--execute` were refused as superseded, V9's
  verification found what the packet records and its `--execute` refused as
  `OPERATOR_APPROVAL_NOT_RECORDED`; no tripwire fired.
- The canonical counters were read before and after the full run, and they are unchanged. No new or
  edited file carries a carriage return.

## Next

**Stop.** V9 is frozen and unapproved, and this mission authorised no inference.

Approving `SECOND-OPPORTUNITY-SYNTH-EXEC-V9` by its digest `ba681da9...`, recorded beside the packet by
a later mission, authorises exactly one request: V8's body, byte for byte, on the synchronous route with
a strict forced tool over the frozen projection, thinking disabled at 128000 output tokens, a client
timeout of 240 seconds and no retry, the ten ordered stages with the full schema v1.2.0 at stage 5,
under a hard execution cost ceiling of 3.608, and an Opportunity hypothesis persisted only after
deterministic acceptance and a separate human approval. The approval must decide, explicitly and for V9
only, `RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V9` and
`STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V9`, the latter acknowledging that 240 seconds is not a
provider-guaranteed end-to-end latency bound and that the one attempt has no retry; the runner executes
nothing unless both are `true`.

**Do not execute V9 without that approval, do not approve it or accept either risk on the operator's
behalf, do not execute V7 or V8, do not reuse V1's to V6's approvals, and do not persist Opportunity
#2.** Mission 1.84.22 was not started.
