# Mission 1.84.16: Reasoning-Summary Contract V1.2, Persistence Compatibility & Execution Packet V6

**`DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY`**, blocker **`SEMANTIC_GATE_V1_3_0_BINDS_OUTPUT_SCHEMA_V1_1_0`**

The operator moved one hard bound of the output contract: `evidence_bound_reasoning_summary.maxLength`,
from 900 to 1500, as a semantic budget they own. This mission recorded that decision, reconfirmed V5
as it was, created schema v1.2.0 as a successor with exactly that one change, and established that
canonical persistence can hold the new bound.

**Then section 10 stopped it.** Semantic gate v1.3.0 validates every answer against schema v1.1.0
inside its own evaluator, so the 900 is enforced again at stage 6 whatever stage 5 admits. A synthetic
summary of 1189 characters that schema v1.2.0 admits is refused by the gate with exactly one reason:
v1.1.0's bound. Admitting a longer summary through stage 6 needs a gate with another identity, and the
brief forbids mutating v1.3.0 in place. **So no prompt v1.5.0, no V6 runner and no packet V6 were
prepared, and nothing was sent anywhere.**

```
START_COMMIT        f3ff867f7b83c32324f148860940cbfa6f26746a
BRANCH              sprint-1/mission-1.84.16

DECISION            second-opportunity-reasoning-summary-contract-decision-v1.json
                    file sha256                f8aa8b525b87cf561b7a8eb181d6fb68ffe50da10a62cd153af37137ecee0886
                    operator statement sha256  84c83f92204dcb10dabff8a44a2c8cddc03f600fb5456e1616bd539b460691d3
SCHEMA v1.1.0       second-opportunity-synthesis-output@1.1.0   ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988  (unchanged)
SCHEMA v1.2.0       second-opportunity-synthesis-output@1.2.0   7d67bad3df06691ba46a4dcc65cbf186bc5825a87719e985637aec68640e1b66
GATE                second-opportunity-output-gate@1.3.0        cc3c490268e6f64a0b2107c2fb0c2fe6a1b1c71ab44c353419cd7d86c4485bf3  (unchanged)

PRIMARY_OUTCOME     DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY
BLOCKER             SEMANTIC_GATE_V1_3_0_BINDS_OUTPUT_SCHEMA_V1_1_0 (brief section 10)
V6                  NOT CREATED
```

The brief's list of outcomes names no separate code for the section 10 stop. The listed outcome it
produces is `DETERMINISTIC_STAGE_6_TO_9_PATH_NOT_READY`, because under schema v1.2.0 stage 6 refuses a
valid answer whose summary is over 900. The record carries both names so neither hides the other.

## The operator's contract decision (§0, §6)

`second-opportunity-reasoning-summary-contract-decision-v1.json` was written once, with an exclusive
create. **The operator's words were extracted from the message, not retyped.** The message was found
exactly once in the session's transcript, as 868 non-blank lines with digest `c329e908...`. The
recorded statement is its heading lines and section 0: 44 lines up to the heading of section 1, with a
SHA-256 over the lines joined by a newline, as in every earlier operator statement.

Before the file was written, the statement was read back for the values it names: the hard maximum
1500, the basis `OPERATOR_SEMANTIC_BUDGET`, `MATHEMATICALLY_DERIVED = false`,
`HISTORICAL_OUTPUT_LENGTH_DERIVED = false`, the old and new bounds, the three historical observations
and the three responsibilities.

| field | value |
|---|---|
| decision owner / type | `OPERATOR` / `OUTPUT_CONTRACT` |
| field | `evidence_bound_reasoning_summary.maxLength` |
| old / new hard maximum | 900 / 1500 |
| basis | `OPERATOR_SEMANTIC_BUDGET` |
| mathematically derived | false |
| derived from a historical output length | false |
| statistically estimated / proven optimal | false / false |
| historical observations | V3 868, V4 1078, V5 1031 |
| historical observations used to derive 1500 | false |
| generation target ratio | 4/5, kept |

**1500 is not described as derived from 868, 1078 or 1031 anywhere**, and gate 86 refuses a decision
that says it was, that calls it estimated or optimal, or that moves the number. The reason recorded is
the operator's: the field has three substantive responsibilities, and prompt-only control proved
insufficiently reliable at the old contract.

## V5, reconfirmed and left as it was (§2, §3, §7)

| | V5 |
|---|---|
| outcome | `EXECUTION_SCHEMA_REJECTED_NO_RETRY` |
| provider requests / model calls / retries / fallbacks / continuations / repairs | 1 / 1 / 0 / 0 / 0 / 0 |
| stop reason | `tool_use` |
| input / output / thinking / total tokens | 12899 / 3797 / 0 / 16696 |
| actual cost | 0.063768 |
| stages | 1 to 4 PASSED, 5 FAILED, 6 to 10 NOT_REACHED |
| persistence / canonical mutation | false / 0 |
| approval consumed | true |
| human-review packet | none |

**The historical refusal replays exactly.** The live schema v1.1.0 validator, run over the retained
answer, reports `evidence_bound_reasoning_summary: 1031 characters exceeds maxLength 900` and nothing
else. V5's record and response are pinned by file digest in gate 86, so a trimmed or rescued V5 is
refused.

**V5 is not revalidated under v1.2.0**, anywhere in the committed code or record:
`V5_HISTORICAL_VERDICT_UNCHANGED = true`, `REVALIDATED_UNDER_V1_2_0 = false`, `CANDIDATE = false`,
`PERSISTABLE = false`. Every length check under v1.2.0 runs on synthetic text over the synthetic
fixture's answer.

One correction to my own working, stated so nobody finds it later: during exploration, a scratch
measurement of the new boundaries used V5's parsed answer as the base document. Nothing from it was
recorded or committed, and every check that is recorded uses the synthetic fixture, as §7 requires.

## Schema v1.2.0 (§4, §5, §16)

`sros_opportunity/second_opportunity_schema_v1_2.py` deep-copies schema v1.1.0 and moves one number.
**`second_opportunity.py` and `synthesis.py` are byte-identical**, and v1.1.0 still hashes to
`ec789d1b...`.

A deterministic semantic diff, which compares every keyword including descriptions and compares
types, finds exactly one difference:

```
properties.evidence_bound_reasoning_summary.maxLength: 900 -> 1500
```

| check | result |
|---|---|
| schema fields added / removed | 0 / 0 |
| requiredness, enums, maxItems, minItems, patterns, additionalProperties changed | no |
| other maxLength changed | 0 |
| constraints | 75, of which 1 changed |
| metadata differences | 0 |
| finite (Mission 1.84.4's walker) | true; 0 unbounded required paths, 0 unbounded reachable paths |

**The walker is shown to work before it is believed.** Given a copy of v1.2.0 with `observed_need`'s
bound removed, it must name exactly that path; a vacuous walker that always found nothing would
otherwise have let an unbounded schema pass. That check was added while designing the probe, and the
probe confirms it.

## Generation headroom (§11, §12, §19)

The 4/5 policy is unchanged: `TARGET_AT_MOST_80_PERCENT_OF_HARD_MAX_LENGTH`, `Fraction(4, 5)`,
`ARRAY_HEADROOM_POLICY = NONE`. Under schema v1.2.0 the headroom table has the same twelve rows, and
**exactly one moves**:

| composed text | v1.1.0 hard / target | v1.2.0 hard / target |
|---|---|---|
| `evidence_bound_reasoning_summary` | 900 / 720 | 1500 / 1200 |

The 1200 is derived by `headroom_table` from the live v1.2.0 bound and the existing policy, and is
written nowhere independently. The other eleven rows are identical in classification, hard maximum and
target; `candidate_intervention_class` stays 300 / 240 with its role unchanged.

Through the live v1.2.0 validator, on the synthetic answer:

| summary characters | schema v1.2.0 | above the target |
|---|---|---|
| 1199 | PASS | no |
| 1200 | PASS | no |
| 1201 | PASS | yes (soft only) |
| 1499 | PASS | yes |
| 1500 | PASS | yes |
| 1501 | **FAIL** | yes |

Schema v1.1.0 still refuses 901, 1031 and 1500, and every other composed field's boundary is where it
was under both schemas.

## Persistence compatibility (§8, §9)

**`COMPATIBLE`.** The maximum is `NONE_BELOW_THE_POSTGRESQL_TEXT_LIMIT`. Each layer was inspected, and
gate 86 re-derives every layer it can read from the repository:

| layer | finding | source |
|---|---|---|
| A. model / validator | `OpportunityHypothesis.reasoning_summary: str`; `__post_init__` measures no length and slices nothing | `sros_opportunity/hypothesis.py` |
| B. ORM | none; the write paths are SQL through psycopg | `run_opportunity_synthesis.py`, `reconcile_opportunity_reliability.py` |
| C. database column | `reasoning_summary TEXT NOT NULL`, and no later migration names the column | migration 0029 |
| D. database checks | no CHECK names the column; observed live: `text`, type modifier -1, no length, no trigger, PostgreSQL 16.4 | the deployment's catalog, 2026-09-13 |
| E. serialization | both write paths and stage 9 pass the summary as it is, with no slice | the two write paths, the V5 runner |
| F. API / domain | the summary appears in no generated contract and no gateway module | `packages/contracts`, `services/gateway` |
| G. prose guard | measures no length and carries no length-sized number | `sros_opportunity/guards.py` |
| H. hidden 900 | two literals, neither on the v1.2.0 path; and the gate's coupling below | the scan below |

The two literal 900s on the audited paths:
- `sros_opportunity/synthesis.py:200`: the summary bound of historical schema v1.0.0, which v1.2.0 does
  not read;
- `run_opportunity_synthesis.py:549`: an output-token count in Mission 1.31's cost estimate, not a
  character bound.

**The column already holds longer summaries.** The two revisions of Opportunity #1 carry reasoning
summaries, the longest 1456 characters, observed in the live catalog. So storage above 900 is a fact,
not an assumption. No persistence model, ORM or database change was made or needed.

## The semantic gate, and the coupling that stopped V6 (§10)

`second-opportunity-output-gate@1.3.0` is unchanged: its implementation digest still recomputes to
`cc3c4902...` through gate 77. `SEMANTIC_GATE_CHANGED = false`.

**Its evaluator is bound to schema v1.1.0.** In `sros_opportunity/second_opportunity_gate_v1_3.py`:
- line 225, inside `evaluate_second_opportunity_output_v1_3`:
  `structural = schema_violations(dict(output), SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1)`, whose
  violations become refusal reasons prefixed with `second-opportunity-synthesis-output@1.1.0`;
- `COMPONENT_VERSIONS_V1_3["output_schema"]` names `second-opportunity-synthesis-output@1.1.0`;
- its operator decision carries `KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED`;
- gate 77 pins that schema's digest, `ec789d1b...`.

The binding is by import, not by a literal: the four files in gate v1.3.0's implementation digest
contain no 900, and a search for literals alone would have missed it.

**Shown on the synthetic answer, with the real gate:**

| answer | schema v1.2.0 | gate v1.3.0 |
|---|---|---|
| the fixture's valid answer, unchanged | admits | passes, 0 reasons |
| the same answer, its own summary repeated 5 times (1189 characters, no new word) | admits | refuses, 1 reason |

The one reason, verbatim:

```
second-opportunity-synthesis-output@1.1.0: evidence_bound_reasoning_summary: 1189 characters exceeds maxLength 900
```

That is section 10's case exactly: a schema-version binding that requires a successor identity without
any change of semantic behaviour. **The mission stopped there and reported it.** Gate v1.3.0 was not
mutated in place.

## What was not prepared (§13 to §33)

| section | item | state |
|---|---|---|
| 13 to 15, 20 | prompt v1.5.0 | not created; prompt v1.4.0 (`960955f4...`) unchanged |
| 17 | exact maximum serialized size under v1.2.0 | not recorded |
| 18 | execution envelope restated | not restated; the existing decision stands unchanged |
| 21, 22 | stages 6 to 9 through a V6 runner, and the over-900 synthetic positive | not ready: the positive is refused at stage 6, as shown above |
| 25 | TED representation reconstructed for V6 | not reconstructed for V6; gate 84, which rebuilds V5's request, still passes |
| 28 | request body and cost for V6 | not computed |
| 29 to 32 | execution packet V6, its runner, its approval surface | not created |

- `V6_CREATED = false`, no V6 digest, `OPERATOR_EXECUTION_APPROVAL_RECORDED = false`.
- `RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V6 = false`: V5's acceptance expired with V5 and was not
  carried anywhere.
- Gate 86 refuses any of the six V6-path files existing while this record stands.

## CI gate 86

`render_second_opportunity_reasoning_summary_contract.py` rebuilds the record from the live code and
the committed artifacts, and the file must equal the rebuild. It checks the decision's words and
digest; V5's record and response, its replayed refusal, and the absence of a V5 review packet; schema
v1.1.0's digest, v1.2.0's one-leaf diff and digest, its finiteness through a walker it first proves
non-vacuous, and its one-row headroom change with the target derived; the boundaries 1199 to 1501; every
persistence layer and every literal 900 or 720 on the audited paths; gate v1.3.0's digest, its coupling
and the demonstration; that no V6-path file exists; and zero accounting.

65 new tests cover the schema module and the gate. Writing them found one defect in the gate before
the probe ran: it derived repository-relative paths from the file it was pointed at, so a check of a
copy crashed instead of refusing. It now names the canonical locations fixed at load.

## Probe (§33)

**66 violations caught, 0 escaped, 15 of 15 positive controls, every file proved restored.**
`VIOLATIONS_ESCAPED = 0`, `POSITIVE_CONTROLS_FAILED = 0`.

How they were caught: 65 by gate 86's own rules, 1 by render drift.

**The families, all refused:**
- **The decision** (10 cases): 1500 called mathematically derived, derived from historical lengths,
  statistically estimated or proven optimal; the observations used; the bound made 1078; owned by the
  mission; execution authorised; a word of the statement changed; its comment reworded.
- **The record** (32 cases): V6 said ready; the blocker dropped; persistence assumed, a layer dropped, the
  model bound hidden, a 900 dropped from the audit, the column said varchar(900); the gate said changed,
  the coupling said absent, the demonstration said to pass; the target written as 1250, the ratio made
  9/10, another row or another maxLength said to move, the diff edited, v1.1.0 said edited, finiteness
  denied, 1501 said to pass; V5 revalidated, made a candidate, or its verdict changed; V6 created or
  approved; the residual risk inherited; an option recommended; a model call, a provider request, a
  Messages API request, a token-count request, TED bytes, a canonical mutation, a counter moved.
- **V5** (3 cases): its consumption reset; its summary truncated to 900 and rescued; a review packet
  created.
- **Section 10** (6 cases): prompt v1.5.0, a V6 runner, a V6 packet gate, and the V6 prompt, packet
  and approval records, each created.
- **Live code, in a fresh interpreter** (14 cases): schema v1.1.0's 900 moved in place; the new bound
  made 1031, 1078, or 1178 (the historical maximum plus a margin); a second maxLength changed; a field
  made unbounded; the ratio moved to 9/10; gate v1.3.0 changed; the model given a 900 bound; the column
  made varchar(900); a later migration altering the column; a write path or stage 9 truncating the
  summary; the finite walker made vacuous.
- **The rendered page** hand-edited (1 case).

**The positive controls:** the shipped gates 77, 84, 85 and 86; a comment in gate 86's tests and one in
the schema v1.2.0 module; a 1201- and a 1500-character summary admitted and a 1501-character one
refused by v1.2.0; V1 to V5 each refused as consumed by the V5 runner, with no transport built; an
unseen digest not refused.

## Accounting (§37)

```
MODEL_CALLS                0
PROVIDER_REQUESTS          0
MESSAGES_API_REQUESTS      0
TOKEN_COUNT_API_REQUESTS   0
TED_BYTES_SENT             0
CANONICAL_MUTATIONS        0
```

## Canonical state (§34)

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

- `ruff format --check` and `ruff check` are clean over 1094 files, and `mypy` over 212.
- Contracts, catalog and source registry are clean.
- **3853 bare-python tests and 5086 pytest tests** pass, 13 skipped. The database is unchanged across
  29 tenant tables; the global tables are unchanged across 17, with 11 rows appended by the suites to
  1 append-only table, as the checker reports.
- **65 new tests**, on schema v1.2.0 and on gate 86 and the refusals it must make.
- **86 CI gates**, one of them new, all run locally with no failure; gates 77, 83, 84 and 85 still pass,
  so the new schema module moved neither gate v1.3.0, nor the headroom record, nor V5.
- The canonical counters were read again at the end, and they are unchanged.

## Next (§40)

**Stop.** Persistence can represent the new contract; the semantic gate cannot admit it. That is the
blocker presented, and no provider call was spent to find it.

The facts the operator's next decision rests on, with nothing recommended:

- **Schema v1.2.0 exists, is exactly the operator's change, and is finite.** Persistence holds 1500 and
  more today.
- **Stage 6 still enforces 900**, because gate v1.3.0 validates structure against schema v1.1.0 inside
  its evaluator. Any execution under v1.2.0 needs a gate with another identity.
- **Two paths, recorded without a preference:**
  - a gate successor whose only change is the schema it validates against, bound to v1.2.0, frozen with
    its own implementation digest, and shown to judge every case of v1.3.0's test matrix exactly as
    v1.3.0 does; then prompt v1.5.0 and packet V6 as this brief describes them;
  - keep schema v1.1.0 as the execution contract, with v1.2.0 recorded and unused.
- **V1 to V5 stay consumed, and V5's verdict under v1.1.0 stands.**

**Do not execute anything, do not mutate gate v1.3.0, do not revalidate V5 under v1.2.0, and do not
persist Opportunity #2.** Mission 1.84.17 was not started.
