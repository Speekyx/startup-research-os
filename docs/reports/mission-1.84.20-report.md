# Mission 1.84.20: True Execution Cost Ceiling, V7 Supersession & Execution Packet V8

**`SECOND_OPPORTUNITY_EXECUTION_PACKET_V8_READY_FOR_OPERATOR_APPROVAL`**

The operator accepted the provider-strict architecture of Mission 1.84.19 and refused to approve V7 on
one ground: V7 called a body-based input estimate plus the output maximum its `EXECUTION_COST_CEILING`
(1.316316), while recording that strict tool use makes the provider add a system prompt whose token
count is not documented. That figure proves nothing about what the call can cost. The defect was one of
governance and accounting, not of the strict-tool architecture.

- **A hard ceiling was proven from the provider's own documentation, and nothing estimated or observed
  enters it.** Every input the request can be billed for, the provider's own additions included, counts
  toward `claude-sonnet-5`'s 1M-token context window, and input alone may not exceed it. Output is at
  most `max_tokens`, 128000. The request leaves `inference_geo` to a workspace default this repository
  cannot see, so the 1.1 US-only multiplier is included. **HARD_EXECUTION_COST_CEILING = 3.608.**
- **V7's 1.316316 is kept, under the name of what it is**: a planning estimate, never a worst case and
  never a ceiling.
- **V7 was superseded before execution.** It was never approved, never executed and never consumed. Its
  packet is untouched, and its runner now refuses its digest as
  `EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION`, before its approval is read and before any transport
  exists.
- **Packet V8 is V7's request, byte for byte**, under the proven ceiling, frozen and unapproved. Both
  disclosed risks are left for the operator to decide.
- **Nothing was sent.** 0 model calls, 0 provider requests, 0 token-count requests, 0 TED bytes, 0
  canonical mutation. 12 first-party documentation pages were read, one request each.

```
START_COMMIT        a570561002bcdf8c05dcdf26073e16e546ba881f
BRANCH              sprint-1/mission-1.84.20

PACKET              SECOND-OPPORTUNITY-SYNTH-EXEC-V8 v8
                    583946460c6cf68c1be5519916f92d268e36ed65924aeb24901731439586c399
APPROVAL            none recorded; NEW_APPROVAL_REQUIRED = true

PRIMARY_OUTCOME     SECOND_OPPORTUNITY_EXECUTION_PACKET_V8_READY_FOR_OPERATOR_APPROVAL
```

## The operator's decision

Carried as data in gate 94's record and in V7's supersession:

```
ACCEPT_THE_PROVIDER_STRICT_ARCHITECTURE_OF_MISSION_1_84_19
KEEP_OUTPUT_SCHEMA_V1_2_0
KEEP_SEMANTIC_GATE_V1_4_0
KEEP_PROMPT_V1_5_0
KEEP_PROVIDER_STRICT_MODE_TRUE
KEEP_STRICT_PROJECTION_V1_0_0
KEEP_STRICT_CAPABILITY_PROFILE_V1_0_0
KEEP_STRICT_PROJECTION_FREEZE_COMMIT_57154AFF
KEEP_TED_REPRESENTATION_2528A56A
KEEP_GENERATION_HEADROOM_4_OVER_5
KEEP_SUMMARY_HARD_MAXIMUM_1500_AND_TARGET_1200
DO_NOT_APPROVE_V7
V7_EXECUTION_COST_CEILING_PROVEN = false
V7_APPROVAL_AUTHORISED = false
DEFECT_CLASS = GOVERNANCE_ACCOUNTING, NOT_STRICT_TOOL_ARCHITECTURE
```

## V7, reconfirmed

Recomputed from the committed packet (its digest by gate 93's own function) and from the body rebuilt
through the V7 runner over the authenticated snapshot, never sent:

```
packet                               SECOND-OPPORTUNITY-SYNTH-EXEC-V7 v7
sha256                               51023d0d2ed780db4c7d5018a289939e7c9c83061f8768051ef1cd7b8ae674e8
packet file bytes                    f5fbb440e1188afcb35bd6085d2e7d15691fb7c96cd31ee6851379cada3298f8
approval recorded                    false
provider strict mode                 true
request body                         31326 characters, 58956019f78f414ee11392bee5e99eedda4eb1b4deb20d3f20219dfc60739842
body-based input token estimate      18158
output token ceiling                 128000
input cost it called "worst case"    0.036316
output worst-case cost               1.28
its EXECUTION_COST_CEILING           1.316316
strict injected prompt tokens        NOT_ESTABLISHED
```

**The precise defect.** V7 treated `BODY_BASED_INPUT_ESTIMATE + MAX_OUTPUT_TOKEN_COST` as its ceiling.
With provider-side input of undocumented size, that establishes neither
`ACTUAL_BILLABLE_INPUT_TOKENS <= 18158` nor `ACTUAL_CALL_COST <= 1.316316`.
`V7_COST_NUMBER_CLASSIFICATION = ESTIMATE_NOT_PROVEN_HARD_CEILING`. It is not a provider billing error,
and the unknown size was not estimated from anything.

## Three quantities, kept apart

| quantity | what it is | never called |
|---|---|---|
| `BODY_BASED_INPUT_TOKEN_ESTIMATE` | an engineering estimate from the serialised body | a bound |
| `PLANNING_COST_ESTIMATE` | a non-authoritative figure, for comparison with earlier runs | a worst case, a ceiling |
| `HARD_EXECUTION_COST_CEILING` | a value resting on a documented hard upper bound on billable usage | an estimate |

`ESTIMATE != CEILING`, and gate 94 refuses any record where one stands for the other.

## What the provider documents

Twelve first-party pages, each requested once on 2026-09-14 and kept outside the repository, identified
by final URL, retrieval instant and SHA-256. Gate 94 records 65 fragments, each checked verbatim against
the bytes on its line before the record was written. D04 and D07 are byte-identical to Mission 1.84.19's
E01 and E02.

| id | page | bytes | sha256 |
|---|---|---|---|
| D01 | `models/overview.md` | 16851 | `b2ae2923...` |
| D02 | `build-with-claude/context-windows.md` | 15957 | `e4c7bfac...` |
| D03 | `about-claude/pricing.md` | 45051 | `d79ad285...` |
| D04 | `build-with-claude/structured-outputs.md` | 110492 | `4e500fed...` |
| D05 | `build-with-claude/prompt-caching.md` | 157448 | `89fd9a1e...` |
| D06 | `api/messages/create.md` | 131067 | `2f5a9f6e...` |
| D07 | `agents-and-tools/tool-use/strict-tool-use.md` | 40202 | `96c6f324...` |
| D08 | `models/sonnet-5/overview.md` | 13348 | `6ca17e31...` |
| D09 | `build-with-claude/token-counting.md` | 43398 | `05c17f1a...` |
| D10 | `api/errors.md` | 28513 | `0481d4df...` |
| D11 | `api/service-tiers.md` | 8807 | `90d1a568...` |
| D12 | `manage-claude/data-residency.md` | 14916 | `8ca6a408...` |

What they establish:

```
MODEL_CONTEXT_WINDOW_TOKENS                        1000000   (1M, the default, no beta header; the
                                                              pages count in decimal: a 200k window
                                                              is given to the model as 200000)
MAX_OUTPUT_TOKENS                                  128000    (max_tokens is an absolute maximum)
everything in the request counts toward the window           system prompt, messages, tool definitions,
                                                              and all three input fields of usage
input alone over the window                        a 400 invalid_request_error, before generation
STRICT_INTERNAL_PROMPT_TOKENS                      NOT_ESTABLISHED
STRICT_INTERNAL_PROMPT_INCLUDED_IN_CONTEXT_BOUND   true
STRICT_INTERNAL_PROMPT_INCLUDED_IN_BILLABLE_USAGE  true
MAX_BILLABLE_INPUT_TOKENS                          1000000
CACHE_BILLING_APPLICABLE                           false     (only cache_control enables it; the body has none)
long-context premium                               none      (1M at standard pricing on this model)
data residency                                     1.1 on every token category for inference_geo "us";
                                                   the body sets none, so the workspace default decides
Priority Tier                                      not available on claude-sonnet-5
price                                              2 and 10 USD per million tokens, now the standard price
```

**Why the strict prompt is inside the bound.** Strict tool use is a structured-outputs feature; the
structured-outputs page says Claude receives an additional system prompt, that the input token count is
slightly higher, and that the injected prompt costs tokens like any other system prompt. The
context-windows page says the window is all the text the model can reference, that everything in the
request counts toward it, that the three input fields of usage all count toward it, and that input
alone over the window is refused. Whatever the injected prompt's size, it is inside the 1M bound.

**One tension, recorded and resolved conservatively.** The token-counting page says tokens added for
system optimisations are not billed; the structured-outputs page says the injected prompt costs tokens.
The ceiling takes the dearer reading, and holds under either, because billed or not those tokens are
inside the window.

**The output is not subtracted from the input bound.** The documentation does not make the relationship
unambiguous for billing, and a larger bound is never a wrong one.

## Every billing category

| category | disposition |
|---|---|
| base input tokens, tool definitions, the tool-use system prompt (474), the strict format prompt, the context-awareness tags | inside the input bound |
| output tokens, thinking tokens (disabled; would be output inside `max_tokens`) | inside the output bound |
| data residency, US-only | included as a multiplier, 1.1 |
| prompt cache writes (5 minutes, 1 hour) and reads | not applicable: the body carries no `cache_control` |
| long-context premium | not applicable: standard pricing across 1M |
| Priority Tier | not applicable: not available on `claude-sonnet-5` |
| Batch pricing | not applicable: another route, and a discount |
| fast mode | not applicable: Opus 5 and Opus 4.8 only; the body carries no `speed` |
| server-tool fees | not applicable: the one tool is a client tool |
| a strict-schema compilation fee | not a published charge: the full price list names none, and the structured-outputs page's own cost section names only the injected prompt's input tokens |
| a request refused for length | not a published charge: refused with a 400 before generation |

`UNKNOWN_COST_CATEGORIES = []`. Each "not applicable" is checked against the request body the V7 runner
builds: no `cache_control` anywhere, no `inference_geo`, no `service_tier`, no `speed`, no server tool.

## The ceiling

In exact decimal arithmetic, from the documented bounds and the held table (`anthropic-published-2026-09-02`,
0.002 and 0.01 per 1000 tokens, which the pages corroborate):

```
1000000 / 1000 x 0.002 x 1.1   = 2.2      HARD_INPUT_COST_CEILING
 128000 / 1000 x 0.01  x 1.1   = 1.408    HARD_OUTPUT_COST_CEILING
                                 3.608    HARD_EXECUTION_COST_CEILING
HARD_EXECUTION_COST_CEILING_PROVEN = true
```

It rests on no estimate and no observation: not the 18158 body estimate, not the planning cost, not
V7's figure, and not V2's to V6's usage (V6 used 12903 input and 3637 output tokens, one observation
that bounds nothing). The planning figures stay beside it:

```
REQUEST_BODY_CHARACTERS            31326
BODY_BASED_INPUT_TOKEN_ESTIMATE    18158      ceil(31326 / 2.1565 x 1.25)
PLANNING_INPUT_COST_ESTIMATE       0.036316
PLANNING_COST_ESTIMATE             1.316316   PLANNING_ESTIMATE, not a worst case, not a ceiling
```

## V7's supersession

`second-opportunity-synthesis-execution-supersession-v7.json`, beside the packet as V1's to V6's records
are beside theirs:

```
STATUS                          SUPERSEDED_BEFORE_EXECUTION
REASON                          COST_CEILING_SEMANTICS_NOT_PROVEN
V7_EXECUTED                     false
V7_APPROVED                     false
V7_APPROVAL_CONSUMED            false
V7_PACKET_MODIFIED              false   (its bytes pinned by gate 94)
NOT_DESCRIBED_AS                FAILED, CONSUMED, REJECTED_BY_PROVIDER
REFUSAL_OUTCOME                 EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION
REFUSAL_IS_NOT                  EXECUTION_APPROVAL_ALREADY_CONSUMED
```

**One Mission 1.84.19 file was changed, and only to make V7 non-executable.** The V7 runner is the only
code that can send V7, so it now reads the supersession record: `refuse_if_superseded` is called first
in `execute()`, before the approval is read and before a transport exists, and inside
`refuse_if_consumed`, which verification and `--execute` call. V7's packet, its record set and every
frozen artifact are untouched, and gate 93 and the V7 runner's own 84 tests still pass unchanged. Run
against the research database with every network path tripwired, V7's verification and its `--execute`
both stop at the guard:

```
REFUSED  nothing was sent: EXECUTION_PACKET_SUPERSEDED_BEFORE_EXECUTION: execution packet 51023d0d...
         was superseded before it was approved or executed (COST_CEILING_SEMANTICS_NOT_PROVEN)
```

V1 to V6 are still refused as `EXECUTION_APPROVAL_ALREADY_CONSUMED`, and an unseen digest is not refused.

## What did not move

```
output schema          second-opportunity-synthesis-output@1.2.0     7d67bad3...
semantic gate          second-opportunity-output-gate@1.4.0          eb03899b...
prompt                 second-opportunity-synthesis-prompt@1.5.0     0713eb80...
strict mode            true, FORCED_STRICT_TOOL_USE, one tool, forced tool_choice
strict projection      second-opportunity-provider-strict-input-schema@1.0.0   87028f45...
capability profile     anthropic-strict-tool-capability@1.0.0      7f3ed845...
projector              4eef60b0...          projection tests   fe4abd1c...
freeze commit          57154affb934516650b84480c2438a75c9b9a5a5  (an ancestor of origin/main)
TED representation     2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72
route                  anthropic, POST https://api.anthropic.com/v1/messages, Commercial Terms, synchronous
model                  claude-sonnet-5, thinking DISABLED, max_tokens 128000, 1 call, 0 retries
timeout                60.0 s, unchanged
summary                hard maximum 1500, target 1200, ratio 4/5
stages                 the ten ordered stages; stage 5 the full schema v1.2.0, locally
```

**The request body is V7's, byte for byte**: V7's runner and V8's build the same 31326 characters over
the same snapshot, `58956019...`, `REQUEST_BODY_DIFFERENCES_V7_TO_V8 = 0`.

## Two risks, not accepted here

- **Residual semantic limitation.** Gate v1.4.0 is vocabulary-bounded. The earlier acceptances expired
  with the executions they were given for. `RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V8 = false`.
- **First strict request's timeout.** The provider compiles a grammar on the first request with a
  schema, for an undocumented time, caches it for 24 hours, and times compilation out at 180 seconds.
  The one attempt times out at 60 seconds with no retry, so V8's only call may end before anything is
  generated. The timeout was not changed. `STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8 = false`.

The V8 runner refuses any approval that does not decide both, explicitly and as booleans, and executes
only if both are accepted; gate 95 exercises that check on synthetic approvals written to a temporary
directory.

## V8's stages, on synthetic answers

Through the V8 runner's own `validate_execution`, with no transport:

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

## Packet V8

```
EXECUTION_PACKET_ID                 SECOND-OPPORTUNITY-SYNTH-EXEC-V8
VERSION                             8
SHA256                              583946460c6cf68c1be5519916f92d268e36ed65924aeb24901731439586c399
immediate predecessor               V7 51023d0d...  SUPERSEDED_BEFORE_EXECUTION (not executed, not
                                    approved, not consumed)
last executed predecessor           V6 969128dd...  EXECUTION_SCHEMA_REJECTED_NO_RETRY, UNKNOWN_ROOT_PROPERTY
output schema / gate / prompt       v1.2.0 / v1.4.0 / v1.5.0
strict                              true, projection v1.0.0, profile v1.0.0, freeze 57154aff...
summary                             hard maximum 1500, target 1200, headroom 4/5
provider / model / route / thinking unchanged
MAX_OUTPUT_TOKENS / CALLS / RETRIES 128000 / 1 / 0
timeout                             60.0 s
PLANNING_INPUT_TOKEN_ESTIMATE       18158
PLANNING_COST_ESTIMATE              1.316316
HARD_EXECUTION_COST_CEILING         3.608
HARD_EXECUTION_COST_CEILING_PROVEN  true
human review                        required
canonical persistence               only after stages 1 to 9 and a separate human approval
RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V8        false
STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8   false
OPERATOR_EXECUTION_APPROVAL_RECORDED                false
NEW_APPROVAL_REQUIRED                               true
PREVIOUS_APPROVAL_REUSABLE                          false
```

The digest binds V7's fields without V7's cost figures, predecessor outcome, schema violation and
residual-risk flag; with V7 as the superseded predecessor, V6 as the last executed one, the six consumed
packets, V7's supersession and its record's digest, the request body's digest and length, gate 94's
planning estimate and hard ceiling with every term of its derivation and the record's digest, and both
risk flags. None of V7's cost field names (`EXECUTION_COST_CEILING`, `WORST_CASE_CALL_COST` and the
rest) exists in V8, and gate 95 refuses one that returns.

**The V8 runner's verification ran once against the research database, with every network path
tripwired, and sent nothing.** It found exactly what the packet records: digest `58394646...`, V1 to V6
consumed, V7 superseded before execution, representation `2528a56a...` (3604 characters), prompt
`0713eb80...`, 0/0/0 unstated constraints, rules and targets, `FROZEN_PROJECTION_STRICT_FORCED`, a
31326-character body hashing to `58956019...`, a hard ceiling of 3.608 and a planning estimate of
1.316316 at the configured price, and `OPERATOR_APPROVAL_NOT_RECORDED`. Its `--execute` refused there.

## CI gates 94 and 95

**Gate 94** (`render_second_opportunity_execution_cost_ceiling.py`) re-derives the cost record and V7's
supersession, and refuses: an estimate or planning cost called a ceiling; a provider fact resting on no
quoted fragment, or a page that is not first-party; a context window the quotes do not state; the strict
prompt's unknown size said covered; a billing category dropped, or called inapplicable while the body
selects it; the residency multiplier left out; an input bound taken from the body estimate or from
observed usage; a ceiling replaced by an incurred cost, or one the decimal derivation does not give;
V7's figure called proven; V7 edited, approved, executed, or recorded as consumed, failed or refused by
the provider; and a V7 runner that no longer refuses V7, by name, before its approval and any transport.

**Gate 95** (`render_second_opportunity_execution_packet_v8.py`) re-derives packet V8, reusing gate 93's
checks of what did not move, and refuses: bound fields that do not hash to the digest, a spent or
superseded digest, an unreviewed field, an approval recorded by the preparing mission or either risk
accepted by it; V1 to V6 edited or their consumption reset, V7 described as anything but superseded
before execution; a contract, gate, prompt, projection, freeze, route, model, thinking, max_tokens,
timeout, retention or persistence policy moved; a body that is not V7's bytes; a cost figure that is not
gate 94's, or V7's cost fields back; a synthetic answer that does not stop where it must; a runner whose
guard renames V7's refusal, whose approval check does not demand and exercise both risk decisions, or
that would execute V1 to V7; and any preparation call, TED byte or canonical counter that moved.

## Probe (section 26)

**One run, and it is the one that counts.** The real transport's constructor and `urlopen` were
tripwired for the whole run, in the probe's own process and in every child interpreter.

**99 violations caught, 0 escaped, 27 of 27 positive controls, every file proved restored.**
`VIOLATIONS_ESCAPED = 0`, `POSITIVE_CONTROLS_FAILED = 0`. 97 were refused by a named rule of gate 94 or
gate 95, 2 by render drift, 0 by a crash. No transport was constructed anywhere.

**Data, edited on disk and judged by gate 94's and then gate 95's full validation** (78 cases; every
bound edit to packet V8 was re-digested, so the digest could not be what refused it):
- the cost record (25): the estimate called the ceiling or the planning figure labelled one, the
  strict prompt's size said known or covered, the input bound set to the body estimate or to V6's
  observed usage, the ceiling replaced with V6's incurred cost, the residency multiplier dropped or
  called inapplicable, the residency, compilation-fee and 1-hour cache categories dropped, a cache
  charge ignored while the request caches, the context window invented, a fact resting on nothing, a
  page that is not first-party, the strict prompt placed outside the bound, an unbounded category
  under a proven ceiling, V7's figure called proven, the defect called a billing error, the timeout
  risk accepted, a provider or token-count request, observed usage used, an undocumented price;
- V7's supersession (9): called consumed, failed or rejected by the provider, refused as a spent
  approval, marked executed, approved or consumed, the record deleted, another digest named;
- V7 on disk (5): an execution record or a response appearing, an approval fabricated by a later
  mission, its packet edited with and without a new digest;
- packet V8 (34): each cost figure moved or V7's field back, V7 called consumed or executed, the
  supersession omitted, the body identity moved, strict mode off, the projection, contract, gate and
  representation digests moved, the prompt said changed, unknown fields filtered, stage 5 handed to
  the provider, the timeout changed, the timeout risk or the residual risk accepted, V7's risk flag
  carried, the freeze moved, another model, a retry, a provider, model or token-count call, V8 marked
  approved or a previous approval reusable, a counter moved, V7's digest replayed, a bound field moved
  without its digest;
- history and approvals (5): V6's consumption reset, V6's packet edited, V6's approval placed beside
  V8, V8 approved by this mission, gate 92's record claiming a provider-enforced length.

**Live code, edited and judged by gate 95 in a fresh interpreter** (19 cases): the V7 runner's
supersession guard made a no-op, `execute()` no longer refusing a superseded packet first, V7 refused
under the consumed name; the V8 runner's local stage 5 removed, unknown keys filtered before it, the
approval check no longer demanding the risk decisions, V7's refusal renamed, the guard no longer
reading V7's, the body changed, the ceiling pinned at the estimate, the timeout changed, a cache
selector allowed; the strict adapter's flag set false, `cache_control` added to the tool; the projector
edited after the freeze; schema v1.2.0's 1500 moved to 1100; the shared validator's closed-object check
removed; prompt v1.5.0 extended; gate v1.4.0 edited.

**The rendered pages**, hand-edited (2 cases, by drift).

**Four cases were caught by a neighbouring named rule rather than the most specific one**, and are
reported as such rather than recounted. The ceiling replaced with V6's incurred cost was refused by the
rule that an estimate may not exceed its ceiling, which runs first. An execution record, a response and
a fabricated approval appearing beside V7 were refused by gate 94's reconfirmation, which records their
absence, before the live check that names them. V6's approval placed beside V8 was refused by the rule
that any approval not recorded by a later mission is refused, whose message speaks of the preparing
mission. Separately, one code case took 1046 seconds where the others took 1 to 22; run again on its
own it took 13 seconds with the same verdict, so the delay was the machine's and not the case's.

**The 27 positive controls:**
- the shipped gates 92, 93, 94 and 95, a comment in the V8 runner and one in gate 95's tests;
- V7's digest and file bytes unchanged, V7 unexecuted and unapproved, V7 refused by its own runner as
  superseded;
- V1 to V6 each refused as consumed through the V8 runner, and the unseen V8 digest awaiting approval;
- the strict freeze exact (projection, profile, projector, tests, commit);
- V7's and V8's bodies byte-identical at `58956019...`;
- the planning estimate apart from the ceiling, every cost category accounted for, the ceiling's
  derivation recomputed exactly at 3.608;
- the synthetic path: valid and 1189 and 1500 characters to stage 9, semantic to 6, boundary to 7,
  provenance to 8, persistence to 9, 1501 and an extra root property to 5;
- a V8 `--execute` refused as `OPERATOR_APPROVAL_NOT_RECORDED` and a V7 `--execute` refused as
  superseded, both before any network, with `execute()` replaced by a function that raises;
- no transport constructed in the probe or in any child;
- the freeze commit found on origin by `git ls-remote` and `git merge-base --is-ancestor` against the
  fetched `main`, never read from local HEAD.

## Technical debt, recorded and not changed

The frozen projector test `test_anthropic_strict.py::test_no_beta_header_is_added` builds
`AnthropicProvider(api_key="k")` without a transport, so the adapter constructs a real `UrllibTransport`
it never uses. It sends nothing and runs only in the unit suite. The file is part of the strict freeze
(`fe4abd1c...`); editing it would move a pinned digest that V7 and V8 both bind. It is not part of V8's
correctness. A later mission may fix it under a new freeze.

## Accounting

```
MODEL_CALLS                0
PROVIDER_REQUESTS          0
MESSAGES_API_REQUESTS      0
TOKEN_COUNT_API_REQUESTS   0
TED_BYTES_SENT             0
CANONICAL_MUTATIONS        0
documentation requests     12 (12 first-party pages, one request each)
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

- `ruff format --check` and `ruff check` are clean over 1138 files, and `mypy` over 215.
- Contracts, catalog and source registry are clean.
- **3877 bare-python tests and 5925 pytest tests** pass, 13 skipped. The database is unchanged across
  29 tenant tables; the global tables are unchanged across 17, with 11 rows appended by the suites to
  1 append-only table, as the checker reports.
- **282 new tests**: 71 on gate 94, 120 on the V8 runner (every V7 runner test kept and run against V8's
  runner, and V8's governance: V1 to V6 spent and V7 superseded under their own names, both risk
  decisions demanded, V7's body, the billing selectors, the ceiling computed apart from the estimate)
  and 91 on gate 95. **No test was re-pointed**: the V7 runner's 84 tests and gate 93's 58 pass unchanged
  after the guard was added.
- **95 CI gates**, two of them new (94 and 95), all run locally with no failure.
- The V8 runner's verification ran once against the research database and sent nothing; V7's
  verification and `--execute` were refused as superseded.
- The canonical counters were read before and after the full run, and they are unchanged. No new or
  edited file carries a carriage return.

## Next

**Stop.** V8 is frozen and unapproved, and this mission authorised no inference.

Approving `SECOND-OPPORTUNITY-SYNTH-EXEC-V8` by its digest `58394646...`, recorded beside the packet by
a later mission, authorises exactly one request: V7's body, byte for byte, on the synchronous route with
a strict forced tool over the frozen projection, thinking disabled at 128000 output tokens, the ten
ordered stages with the full schema v1.2.0 at stage 5, under a hard execution cost ceiling of 3.608, and
an Opportunity hypothesis persisted only after deterministic acceptance and a separate human approval.
The approval must decide, explicitly and for V8 only, `RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V8`
and `STRICT_FIRST_REQUEST_TIMEOUT_RISK_ACCEPTED_FOR_V8`; the runner executes nothing unless both are
`true`.

**Do not execute V8 without that approval, do not approve it on the operator's behalf, do not reuse V1's
to V6's approvals, do not execute V7, and do not persist Opportunity #2.** Mission 1.84.21 was not
started.
