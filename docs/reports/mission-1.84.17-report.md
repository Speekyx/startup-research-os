# Mission 1.84.17: Semantic Gate V1.4 Schema Rebinding, Prompt V1.5 & Execution Packet V6

**`SECOND_OPPORTUNITY_EXECUTION_PACKET_V6_READY_FOR_OPERATOR_APPROVAL`**

Mission 1.84.16 stopped at its section 10: semantic gate v1.3.0 validates structure against schema
v1.1.0 inside its own evaluator, so the operator's 1500-character summary bound was enforced back down
to 900 at stage 6. The operator then decided to create a successor gate bound to schema v1.2.0, keep
v1.3.0 immutable, keep every non-structural behaviour unchanged, and use schema v1.2.0 as the V6
execution contract.

This mission did exactly that and nothing more. **Gate v1.4.0 is gate v1.3.0 called once, with only its
schema v1.1.0 structural reasons replaced by schema v1.2.0's.** It was proved to diverge from v1.3.0
nowhere outside the one bound, frozen, and committed as `402a698` before any V6 artifact was rendered.
Then prompt v1.5.0, the V6 runner and execution packet V6 were built on it. **One precondition was not
met: the freeze commit's push failed and I misread the check after it**, so it reached the remote only
with this mission's final push (section 24 below). **V6 is frozen and
unapproved, and nothing was sent anywhere.**

```
START_COMMIT        08f1a0abbe85f395129c8d06a1a1b345eaf09eaf
BRANCH              sprint-1/mission-1.84.17
FREEZE_COMMIT       402a698f695241801d9cd61fd9f5d444ebb16221   (committed before V6; pushed only at the end)

SCHEMA v1.1.0       second-opportunity-synthesis-output@1.1.0   ec789d1b...  (unchanged)
SCHEMA v1.2.0       second-opportunity-synthesis-output@1.2.0   7d67bad3...  (the V6 contract)
GATE v1.3.0         second-opportunity-output-gate@1.3.0        cc3c4902...  (unchanged)
GATE v1.4.0         second-opportunity-output-gate@1.4.0        eb03899b...  (frozen, test 73796544...)
PROMPT v1.5.0       0713eb80...                                 (v1.4.0 960955f4... unchanged)
PACKET V6           969128dd2453ab2a6907335d9386c9c3f3fac991db91c674b151c9db777aa8a9

PRIMARY_OUTCOME     SECOND_OPPORTUNITY_EXECUTION_PACKET_V6_READY_FOR_OPERATOR_APPROVAL
APPROVAL            NOT RECORDED
```

## The operator's decision (section 0)

Five lines, carried as data in the gate module (`OPERATOR_DECISION_V1_4`) and bound into the V6 digest
as `SEMANTIC_GATE_SUCCESSOR_DECISION`:

```
CREATE_SEMANTIC_GATE_SUCCESSOR_BOUND_TO_OUTPUT_SCHEMA_V1_2_0 = true
KEEP_SEMANTIC_GATE_V1_3_0_IMMUTABLE
KEEP_ALL_NON_STRUCTURAL_SEMANTIC_BEHAVIOR_UNCHANGED
USE_OUTPUT_SCHEMA_V1_2_0_AS_THE_V6_EXECUTION_CONTRACT
DO_NOT_REVERT_TO_OUTPUT_SCHEMA_V1_1_0
```

Nothing else was authorised and nothing else moved: assertion context, denial handling, source origin,
source metadata, lexical inflection, OBSERVED atomicity and disjunction, the commercial-claim
boundaries, `MARKET_ACTIVITY`, BT-161 and trusted context are all gate v1.3.0's, called, not copied.

## History untouched (section 2)

Gate 87 pins 18 historical artifacts by file digest (the V1 to V5 packets, approvals, records and
responses) and records `ARTIFACTS_EDITED = 0`. Schemas v1.0.0 and v1.1.0, gates v1.1.0 to v1.3.0,
prompts v1.0.0 to v1.4.0 and the 1.84.16 decision and record are byte-identical. **V5 was not
revalidated under v1.2.0**, and no historical answer was replayed through gate v1.4.0: every check
here runs on synthetic text over the synthetic fixture's answer.

## The blocker, reconfirmed before anything was built (section 3)

Rerun from scratch on the merged main:

| check | result |
|---|---|
| schema v1.1.0 / v1.2.0 digests | `ec789d1b...` / `7d67bad3...` |
| semantic diff | exactly `properties.evidence_bound_reasoning_summary.maxLength: 900 -> 1500` |
| gate v1.3.0 implementation digest | `cc3c4902...` |
| the fixture's summary repeated 5 times | 1189 characters |
| schema v1.2.0 violations | none |
| gate v1.3.0 on the unchanged answer | 0 reasons |
| gate v1.3.0 on the 1189-character answer | 1 reason, verbatim below |

```
second-opportunity-synthesis-output@1.1.0: evidence_bound_reasoning_summary: 1189 characters exceeds maxLength 900
```

## Gate v1.4.0 (sections 5 and 7)

`sros_opportunity/second_opportunity_gate_v1_4.py` is a new module. **No v1.3.0-pinned file was
modified**, so the section 5 stop condition was never reached.

```
predecessor = evaluate_second_opportunity_output_v1_3(output, ...)       # called exactly once
replaced    = v1.1.0 structural reasons, recomputed by the same validator
if predecessor's leading reasons != replaced: raise PredecessorShapeError   # fail closed
semantic    = every other v1.3.0 reason, in v1.3.0's order
structural  = v1.2.0 structural reasons, prefixed second-opportunity-synthesis-output@1.2.0
decision    = (*structural, *semantic), with v1.3.0's audit and notes
```

- **Removing reasons is only safe when you can account for every one removed.** The v1.1.0 reasons are
  recomputed and compared position by position against the head of v1.3.0's list; if v1.3.0 ever stops
  writing them first, v1.4.0 raises rather than guessing which reasons were structural.
- **The module writes no number.** Gate 87 asserts over the AST that it carries no integer literal,
  calls v1.3.0 exactly once, runs `schema_violations` against exactly schemas v1.1.0 and v1.2.0, and
  defines no function but its evaluator.
- **Component identity moves in exactly two places**: `gate` (v1.3.0 to v1.4.0) and `output_schema`
  (v1.1.0 to v1.2.0). The other nine components are v1.3.0's.
- **Implementation digest `eb03899b...`** over six files: `lexical_inflection`, `support_origin`,
  `assertion_audit_v1_3`, `second_opportunity_gate_v1_3`, `second_opportunity_schema_v1_2` and the new
  module. The frozen test file `test_semantic_gate_v1_4.py` (134 tests) is pinned at `73796544...`.

## Gate v1.3.0 unchanged (section 6)

Gate 77 still validates, gate v1.3.0's implementation still recomputes to `cc3c4902...`, its test file
still hashes to `6d7ad831...`, and gate 87 refuses to derive a record if either moves.

## The differential proof (sections 4 and 8 to 11)

Every case is evaluated by both gates on identical arguments and classified by domain: **COMMON** (a
summary within 900, or not a string), **BAND** (901 to 1500), **ABOVE** (over 1500). The expected
structural difference is computed, not assumed: in COMMON none, in BAND the v1.1.0 bound reason
disappears, above 1500 it is replaced by v1.2.0's. **Semantic reasons, the audit and the notes must be
equal everywhere.**

| corpus | cases | COMMON | BAND | ABOVE | persist changed |
|---|---|---|---|---|---|
| synthetic corpus (census 41, summary 17, sweep 46) | 104 | 90 | 11 | 3 | 7, all in BAND |
| gate v1.3.0's own test file, replayed through both | 15 evaluator calls | 14 | 1 | 0 | 1, in BAND |

```
COMMON_DOMAIN_SEMANTIC_DIVERGENCES              0
NON_STRUCTURAL_SEMANTIC_DIVERGENCES             0
STRUCTURAL_DIVERGENCES_BEYOND_THE_ONE_BOUND     0
INCONSISTENT_V1_4_VERDICTS                      0
```

**The matrix replay runs v1.3.0's 159 tests unmodified** through a pytest plugin that wraps every
module attribute pointing at the v1.3.0 evaluator with a spy: each call runs both gates, records the
pair, and hands the test back v1.3.0's own verdict, so every test asserts exactly what it always did.
159 passed, 0 failed. **Only 15 of the 159 reach the evaluator**; the rest test the shared components,
which v1.4.0 uses by identity rather than by copy, so they are the same code either way.

**The band, shown with the real gates:**

| answer | characters | gate v1.3.0 | gate v1.4.0 |
|---|---|---|---|
| the fixture's own summary repeated | 1189 | refuses on the v1.1.0 bound alone | passes, 0 reasons |
| the same, plus one unsupported sentence | 1216 | (refuses) | refuses on `WILLINGNESS_TO_PAY` only, no bound reason |
| 1501 characters | 1501 | (refuses) | refuses, naming `@1.2.0` and `1500` |

## Historical replays unchanged (section 12)

No historical answer runs in the gate or its tests. The V3, V4 and V5 verdicts are recorded as they
were and are not reclassified (`V3_V4_V5_RECLASSIFIED = false`).

## Schema v1.2.0: digest, finiteness, maximum instance (sections 13 and 14)

Schema v1.2.0 is `7d67bad3...`, finite by Mission 1.84.4's walker with 0 unbounded paths. Its maximum
valid instance, built with the non-BMP fill that costs twelve serialized characters per character and
validated through the repository's own validator:

| | v1.1.0 | v1.2.0 | delta |
|---|---|---|---|
| maximum valid output characters | 309729 | 316929 | +7200 |

**The delta is exactly what the one bound explains**: 600 more characters of fill, each serialized as 12
characters, and every other field's contribution is identical.

## Reachability (section 15)

`CONTRACT_FULL_DOMAIN_REACHABLE = false`, by monotonic reasoning and **with no new token count**.
Schema v1.2.0 relaxes one bound of v1.1.0 and tightens nothing, so everything v1.1.0 admits v1.2.0
admits, v1.1.0's 309729-character maximum included. Mission 1.84.5 counted that instance at 231608
provider-native input tokens against an execution envelope of 128000 output tokens, so v1.2.0's domain
holds an answer the envelope cannot carry, whatever v1.2.0's own maximum would count to.
`V1_2_0_MAXIMUM_TOKEN_ESTIMATE = NOT_COUNTED`, and `TOKEN_COUNT_REQUESTS = 0`.

## Persistence (section 16)

**`COMPATIBLE`**, unchanged since Mission 1.84.16: `OpportunityHypothesis.reasoning_summary` is a plain
`str` with no length bound, migration 0029 declares the column `TEXT NOT NULL`, no later migration names
it, and the live catalog, read again in this mission, reports `text` with no length and type modifier
-1. Gate 88 compares the observed catalog with the one 1.84.16 recorded and refuses any change.

## Generation headroom (section 17)

4/5 unchanged, `ARRAY_HEADROOM_POLICY = NONE`. Of the twelve headroom rows exactly one moves:

| composed text | v1.1.0 hard / target | v1.2.0 hard / target |
|---|---|---|
| `evidence_bound_reasoning_summary` | 900 / 720 | 1500 / 1200 |

`OTHER_HEADROOM_ROW_DRIFT = 0` and `HAND_MAINTAINED_TARGETS = 0`: the 1200 is `floor(1500 x 4/5)`,
derived by the existing renderer from the live bound and written nowhere independently.

## Prompt v1.5.0 (sections 18 to 20)

Rendered only after gate v1.4.0 was frozen: gate 88 reads gate 87's record and pins and refuses to
render the prompt otherwise. The module itself was first written as a draft at 17:14 UTC, after the
gate's content was final and a minute before the pins were written (section 24).

`second_opportunity_prompt_v1_5.py` rebuilds v1.4.0's system region from the same pieces in the same
order, with the schema moved and nothing else. The output-contract block and the headroom block are
rendered from schema v1.2.0 by the same renderers; the semantic-policy block is gate v1.3.0's census
rendered exactly as before, because gate v1.4.0 keeps every rule in it. **The trusted context with its
SOURCE NAMES, the untrusted TED region and the task are v1.3.0's objects, byte-identical.**

**Exactly two system lines move, one per bounded block, and only in their numbers:**

```
line 134  output contract      "    at most 900 characters"  ->  "    at most 1500 characters"
line 269  generation headroom  "...generation target 720 characters; hard maximum 900 characters"
                           ->  "...generation target 1200 characters; hard maximum 1500 characters"
```

| check | v1.5.0 | prompt v1.4.0 under schema v1.2.0 |
|---|---|---|
| unstated generation constraints | 0 | 1 (`evidence_bound_reasoning_summary maxLength`) |
| unstated generation-relevant semantic rules | 0 | 0 |
| unstated generation targets | 0 | 1 (`evidence_bound_reasoning_summary`) |
| the old bound or target anywhere in the regions | 0 | |
| integer literals in the prompt module | 0 | |

**The checks discriminate**: they refuse the predecessor under the new schema. The prompt digest now
also binds the output schema version and the semantic gate version, so the same text judged by a
different gate is a different prompt.

## The V6 runner and stages 5 to 9 (sections 21 to 23)

`run_second_opportunity_execution_v6.py` is V5's runner with counted, reviewed replacements: its
expectations name V6, stage 5 validates against schema v1.2.0, stage 6 is gate v1.4.0 alone and cannot
be injected (`validate_execution(result, context)` takes nothing else), the prompt is v1.5.0, the
contract checks read the summary's bound and target from schema v1.2.0, and the consumed-approval guard
runs V5's guard (which runs V1's to V4's) before its own.

Gate 89 runs the runner's own stages over synthetic answers, with the real transport tripwired:

| fixture | summary | stops at |
|---|---|---|
| A valid | 237 | eligible at stage 9 |
| B, B2 semantic failures | 237 | 6 |
| C evidence boundary | 237 | 7 |
| D attribution | 237 | 8 |
| E persistence eligibility | 235 | 9 |
| **F long summary, positive** | **1189** | **eligible at stage 9** |
| **G long summary, one unsupported sentence** | **1216** | **passes 5, refused at 6** |
| H at the new bound | 1500 | eligible at stage 9 |
| I one over the new bound | 1501 | 5 |

Every one of the 13 retention paths keeps what arrived and persists nothing. Gate 89 also reads the
runner as a syntax tree: stage 5 must call `schema_violations` with schema v1.2.0, stage 6 must be
gate v1.4.0 and never v1.3.0, and the runner must be able to refuse at each of stages 5 to 9.

## Frozen before V6, and not pushed before it (section 24)

**Section 24 is met for the commit and NOT met for the push.** The order, read from the session's own
record (UTC, 2026-09-13):

| time | event |
|---|---|
| 17:10 | gate v1.4.0's implementation reaches its final content |
| 17:12 | its frozen test file reaches its final content |
| 17:14 | the prompt v1.5.0 module is first written, as an uncommitted draft |
| 17:15 | gate 87's pins are written and the freeze record derived |
| 17:21 | `402a698` committed: the gate, its tests, the differential and gate 87, and no V6-path file |
| 17:21 | its push fails: *send-pack: unexpected disconnect while reading sideband packet* |
| 17:21 | the prompt v1.5.0 and capacity records are first rendered |
| 17:28 to 17:40 | the V6 runner, the preflight record and packet V6 are written |

**The push failed and I misread the check that followed it.** That check printed one SHA, which was
`git rev-parse HEAD`'s; `git ls-remote` had printed nothing, meaning the branch was not on the remote.
The failure was found only at the mission's final push, so `402a698` reached the remote together with
the V6 commit, and every document that said *pushed before V6* was corrected before that push.

What still holds: nothing the gate froze changed after the prompt draft appeared; `402a698` is an
ancestor of everything that depends on it and its tree contains none of the V6-path files; and the
packet binds that commit, the freeze record's digest and the frozen test digest, which gate 90 refuses
to see move. What does not: no remote record of the freeze predates V6, and the prompt v1.5.0 module
existed as a draft a minute before the pins were written.

## Representation, route and envelope (sections 25 and 26)

| | V6 |
|---|---|
| representation | `2528a56a...`, 3604 characters, unchanged |
| selected packet | `e218b56a...`, 6 approved Evidence rows |
| route | `anthropic`, `POST https://api.anthropic.com/v1/messages`, synchronous |
| model | `claude-sonnet-5` |
| thinking | `DISABLED`, sent as `{"type": "disabled"}` |
| max_tokens | 128000, the documented synchronous maximum, not based on any observed output (V5's added to the list) |
| calls / retries | 1 / 0 |
| timeout | 60.0 s, unchanged; V5 took 33.836 s and that observation changed nothing |

## Residual semantic limitation (section 27)

`RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V6 = false`. The acceptance given for V4 and V5 expired
with them and is not carried over. An approval of V6 would have to say whether it accepts it again.

## Retention and consumption (sections 28 and 29)

The runner's retention is tested on synthetic transports for every terminal path; nothing is tested
against a provider. **V1 to V5 stay consumed**: the V6 runner refuses each by name with
`EXECUTION_APPROVAL_ALREADY_CONSUMED` before any network, and does not refuse an unseen digest.

## Cost (section 30)

Held pricing `anthropic-published-2026-09-02`, 0.002 / 0.01 per thousand tokens, and the held method:
2.1565 characters per token times 1.25. **Recomputed from V6's own body, not copied from V5.**

| | V5 | V6 |
|---|---|---|
| request body (characters) | 31963 (rebuilt through V5's runner) | 31967 |
| input token estimate | 18528 | 18530 |
| worst-case call cost = ceiling | 1.317056 | **1.31706** |

The body grew by four characters: `1500` and `1200` where `900` and `720` were, in the prompt and in the
tool schema. The ceiling is the worst case itself, with no headroom policy.

## Execution packet V6 (sections 31 to 33)

`docs/data/second-opportunity-synthesis-execution-packet-v6.json`, digest `969128dd...`, prepared by
`mission-1.84.17`. It binds everything V5's digest bound plus V6's identity, V5 as predecessor with its
outcome and spent approval, the five consumed packets, schema v1.2.0, gate v1.4.0 with its freeze record,
test digest and commit, prompt v1.5.0 and its record, the capacity and preflight records, the operator's
reasoning-summary decision and its record, the summary's hard maximum, target and basis, and the gate
successor decision.

```
OPERATOR_EXECUTION_APPROVAL_RECORDED   false
NEW_APPROVAL_REQUIRED                  true
PREVIOUS_APPROVAL_REUSABLE             false
HUMAN_REVIEW_REQUIRED                  true
persist_if_gate_accepts                false
```

## The runner, dry (section 34)

With no approval on disk, the runner verifies everything and stops:

```
12_ALL_BOUND_FIELDS_MATCH   True
13_RETENTION_READY          True
14_STAGES_6_TO_9_READY      True
OPERATOR_APPROVAL           OPERATOR_APPROVAL_NOT_RECORDED
verified. Nothing sent. An approval naming this digest is required to execute.
```

## CI gates 87 to 90, and gate 86 re-pointed

| gate | script | what it re-derives |
|---|---|---|
| 87 | `render_second_opportunity_semantic_gate_v1_4.py` | the freeze record: predecessor, identity, schema, implementation, differential, band, above, matrix replay, history |
| 88 | `render_second_opportunity_prompt_v1_5.py` | prompt v1.5.0 and its differential, and the capacity, reachability, headroom and persistence under v1.2.0 |
| 89 | `render_second_opportunity_stage_6_9_preflight_v2.py` | stages 5 to 9 and every retention path through the V6 runner |
| 90 | `render_second_opportunity_execution_packet_v6.py` | the packet, field by field, and the runner that must execute it |

**Gate 86 had pinned the future to an absence**: Mission 1.84.16 made it refuse a prompt v1.5.0, a V6
runner, a V6 packet or approval existing at all. It now refuses them unless a later mission took the
decision section 10 asked for: a freeze record from a later mission, with `GATE_V1_4_FROZEN = true`,
v1.3.0 as predecessor and schema v1.2.0's digest, and every V6 artifact naming a later mission as its
author. **The 1.84.16 record is unchanged**, and the re-pointing is Mission 1.76.6's shape.

## Probe (section 35)

**123 violations caught, 0 escaped, 22 of 22 positive controls, every file proved restored.**
`VIOLATIONS_ESCAPED = 0`, `POSITIVE_CONTROLS_FAILED = 0`. 118 were refused by the gates' own rules and 5
by render drift, exactly the five hand-edited pages. After the last case, all five gates passed again,
both in process and in a fresh interpreter.

Most packet cases recompute the digest after the edit, so the refusal has to come from the rule that
owns the field and not from the hash; the three that do not are the cases about the hash itself.

**The families, all refused:**
- **Packet V6** (51 cases): the residual risk accepted, an approval said recorded, V5's approval said
  reusable, no new approval, human review dropped, authorship moved to 1.84.16, an approval note that
  forgets the residual risk; the hard maximum back to 900 or made 1501, the target made the bound, the
  schema version or digest back to v1.1.0, the gate back to v1.3.0 or v1.3.0's implementation digest,
  the freeze commit moved, a decision line dropped, the decision basis rewritten, the full domain said
  reachable, truncation or normalisation allowed; prompt v1.4.0's version or digest; the response schema
  back to v1.1.0, max_tokens 64000, thinking enabled, another model, a retry, two calls, a 120-second
  timeout, V4's stage names, a ceiling basis that forgets V5; V5's ceiling copied, a lowered input
  estimate, a moved price, another representation, a dropped Evidence id; V4 as predecessor, V5 dropped
  from the consumed; persistence on acceptance, a retention path no test defines, a preparation model
  call, token count, TED bytes or credential read, a moved counter, a verification saying approved,
  V5's output used to set the bound or its time to set the timeout; a bound field moved with the digest
  kept, V5's spent digest, a field nothing reviews.
- **What V6 rests on** (5): V5's consumption reset, V5's packet edited to record an approval, an
  approval recorded by this mission itself, an approval naming another digest, V5's response truncated.
- **Gate 88's records** (11), **gate 89's record** (6) and **gate 87's record** (10): every one refused
  as not what the live code derives.
- **Gate 86, re-pointed** (8): the freeze claiming 1.84.16, not frozen, bound to schema v1.1.0 or naming
  v1.2.0 as predecessor; the prompt record, the packet or an approval claiming 1.84.16; the 1.84.16
  decision edited.
- **Live code, in a fresh interpreter** (27): gate v1.3.0 edited; gate v1.4.0's prefix moved, its shape
  check dropped, or v1.1.0's reasons kept beside v1.2.0's; its frozen test edited; schema v1.2.0's bound
  made 1400; the assertion audit or lexical inflection edited; the differential made vacuous; prompt
  v1.5.0 with a line added, its semantic rules dropped, schema v1.1.0 stated, a hand-written 1500, or
  gate v1.3.0 in its digest; the headroom ratio made 9/10; the runner with stage 5 back to v1.1.0, stage 6
  back to v1.3.0, the summary truncated before stage 5, an injectable gate, another digest, the old
  bound, V5's ceiling, schema v1.1.0 in the request, or V5's guard dropped; and the runner, prompt v1.5.0
  or gate 90 claiming Mission 1.84.16 as their author.
- **The rendered pages** hand-edited (5).

**The positive controls:** the shipped gates 85 to 90; a comment in the V6 runner, in prompt v1.5.0 and
in the gate 89 and 90 tests; fixtures F, G, H and I through the V6 runner with no transport built; gate
v1.4.0 at 1500 and 1501 characters; V1 to V5 each refused as consumed by the V6 runner; V6's own digest
not refused.

**The probe's own defects came first, and were caught before any file moved.** Its preflight refused
two cases that targeted a field of the wrong shape (a count read as a list, and a component key that did
not exist), because a probe case that changes nothing tests nothing. Both were corrected and the probe
ran from the start. **The vacuous differential is the slow one**: it is refused only after gate 87's full
derivation, by the differential module's digest in the freeze record, which is why that digest is there.

## Accounting (section 39)

```
MODEL_CALLS                0
PROVIDER_REQUESTS          0
MESSAGES_API_REQUESTS      0
TOKEN_COUNT_API_REQUESTS   0
TED_BYTES_SENT             0
CANONICAL_MUTATIONS        0
```

## Canonical state (section 36)

Read from the database before any work and again at the end, and identical:

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

- `ruff format --check` and `ruff check` are clean over 1113 files, and `mypy` over 214.
- Contracts, catalog and source registry are clean.
- **3853 bare-python tests and 5364 pytest tests** pass, 13 skipped. The database is unchanged across
  29 tenant tables; the global tables are unchanged across 17, with 11 rows appended by the suites to
  1 append-only table, as the checker reports.
- **271 new tests**: 134 on gate v1.4.0 (frozen), 69 on the V6 runner, 23 on prompt v1.5.0 and gate 88,
  9 on gate 89, 31 on gate 90, and 5 on gate 86's re-pointed check.
- **90 CI gates**, four of them new, all run locally with no failure; gates 77, 84, 85 and 86 still pass,
  so gate v1.3.0, V5 and the 1.84.16 record did not move.
- The canonical counters were read again at the end, and they are unchanged.

## The approval surface (section 42)

**Stop.** V6 is ready and nothing was executed. What an operator approval would name:

```
packet            SECOND-OPPORTUNITY-SYNTH-EXEC-V6, version 6
digest            969128dd2453ab2a6907335d9386c9c3f3fac991db91c674b151c9db777aa8a9
predecessor       V5 da3e7d09..., EXECUTION_SCHEMA_REJECTED_NO_RETRY, approval spent
route             anthropic, POST https://api.anthropic.com/v1/messages, synchronous
model             claude-sonnet-5, thinking DISABLED, max_tokens 128000
calls             1, retries 0, timeout 60.0 s, no fallback, no continuation, no repair
output contract   schema v1.2.0 (7d67bad3...), summary hard maximum 1500, target 1200
semantic gate     v1.4.0 (eb03899b...), frozen at 402a698, test 73796544...
prompt            v1.5.0 (0713eb80...)
representation    2528a56a..., 3604 characters, 6 Evidence rows
ceiling           1.31706 (input 0.03706 + output 1.28), a worst case, not an expected cost
persistence       nothing persisted; stages 1 to 9 then a separate human approval
residual risk     NOT accepted for V6; the approval must say whether it accepts it again
```

The approval is recorded beside the packet, in
`second-opportunity-synthesis-execution-approval-v6.json`, by a later mission, naming this digest.
**Do not execute V6 without it, do not approve it on the operator's behalf, do not reuse V1's to V5's
approvals, do not revalidate V5 under v1.2.0, and do not persist Opportunity #2.** Mission 1.84.18 was
not started.
