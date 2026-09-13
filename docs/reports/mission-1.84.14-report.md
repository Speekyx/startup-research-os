# Mission 1.84.14: Generation Headroom Policy, Non-Redundant Field Guidance and Execution Packet V5

**`SECOND_OPPORTUNITY_EXECUTION_PACKET_V5_READY_FOR_OPERATOR_APPROVAL`**

The operator accepted V4's historical result, `EXECUTION_SCHEMA_REJECTED_NO_RETRY`, and made a set of
decisions:
- keep schema v1.1.0, semantic gate v1.3.0 and the TED representation unchanged;
- never raise a bound because of V4, never truncate and never post-process to fit;
- adopt a generation policy of their own choosing: a target at most 4/5 of each composed text's hard
  maximum, stated beside it, plus field roles so that each field carries its own information once.

**The ratio was selected by the operator. Nothing here derives it from V4.**

- **Prompt v1.4.0** is v1.3.0 byte for byte, plus one block rendered from the live schema and the
  operator's policy objects. It states twelve generation targets beside their hard maxima.
- **Every target is `floor(hard maximum x 4/5)`**, computed by one function in integer arithmetic.
- **A target is not a limit.** One character over a target passes the schema, and one character over
  the hard maximum fails, for every one of the twelve texts.
- **Packet V5 is frozen and unapproved.** No model was called.

```
START_COMMIT                        a5679d9b1b3550bfeb1a02f5e72c974035af7707
BRANCH                              sprint-1/mission-1.84.14

V4                                  EXECUTION_SCHEMA_REJECTED_NO_RETRY, approval consumed, stages 6-10 NOT_REACHED
SCHEMA                              second-opportunity-synthesis-output@1.1.0  ec789d1b...  changed: false
SEMANTIC GATE                       second-opportunity-output-gate@1.3.0       cc3c4902...  changed: false
PROMPT (old / new)                  1.3.0 a62fa218...  /  1.4.0 960955f44a7ac0b95c995941aeac6ca772e196f4e6cb309b44ecfaa741bd6f46
GENERATION_HEADROOM_POLICY          TARGET_AT_MOST_80_PERCENT_OF_HARD_MAX_LENGTH
GENERATION_TARGET_RATIO             4/5 (fractions.Fraction, exact)
ARRAY_HEADROOM_POLICY               NONE
V4_VALUES_USED_TO_DERIVE_HEADROOM   false
HEADROOM_TARGET_DRIFT               0
REPRESENTATION_SHA256               2528a56a... (3604 characters, unchanged)
EXECUTION_PACKET_V5_SHA256          da3e7d09d97c30cd02859eaee729b6bd164cd99812feac34572a0e1d93aa511a
EXECUTION_COST_CEILING_V5           1.317056
OPERATOR_EXECUTION_APPROVAL_RECORDED false
PRIMARY_OUTCOME                     SECOND_OPPORTUNITY_EXECUTION_PACKET_V5_READY_FOR_OPERATOR_APPROVAL
```

## The operator's decision, carried as data (§0)

`generation_headroom.OPERATOR_DECISION_GENERATION_HEADROOM` carries the ten lines verbatim. The headroom
record carries them, packet V5 binds them in its digest, and gates 83 and 84 refuse a copy that is
shortened or reworded:

- `KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED`
- `KEEP_SEMANTIC_GATE_V1_3_0_UNCHANGED`
- `KEEP_TED_REPRESENTATION_UNCHANGED`
- `DO_NOT_RAISE_MAX_LENGTHS_FROM_V4`
- `DO_NOT_TRUNCATE_MODEL_OUTPUT`
- `DO_NOT_POST_PROCESS_MODEL_OUTPUT_TO_FIT`
- `ADD_SCHEMA_DERIVED_GENERATION_HEADROOM`
- `ADD_NON_REDUNDANT_FIELD_GUIDANCE`
- `GENERATION_HEADROOM_POLICY = TARGET_AT_MOST_80_PERCENT_OF_HARD_MAX_LENGTH`
- `GENERATION_TARGET_RATIO = 0.80`

## V4, historical and unchanged (§2 to §4, §23)

**Gate 83 pins seventeen merged artifacts by their text digest:**
- V1's packet and record;
- V2's packet, approval, record and response;
- V3's and V4's packets, approvals, records and responses;
- prompt v1.3.0's record;
- Mission 1.84.12's alignment and preflight records.

V1 has no separate approval file. Its packet and its record are both pinned.

**V4's facts are read back from its retained record, not restated:**

| fact | value |
|---|---|
| provider requests / model calls | 1 / 1 |
| retries, fallbacks, continuations, repair calls | 0 |
| stop reason | `tool_use` |
| tokens (input / output / thinking / total) | 11599 / 3950 / 0 / 15549 |
| actual cost | 0.062698 |
| stages | 1 to 4 PASSED, 5 FAILED, 6 to 10 NOT_REACHED |
| canonical persistence / mutation | false / 0 |
| approval consumed | true |

**The live v1.1.0 validator, run again locally over V4's retained answer, reproduces the two violations
exactly:**
- `candidate_intervention_class: 316 characters exceeds maxLength 300`
- `evidence_bound_reasoning_summary: 1078 characters exceeds maxLength 900`

**V4 was not touched, and it stays refused.** It was not truncated, summarised, revalidated under
prompt v1.4.0, made a candidate or given a review packet: `V4_CANDIDATE = false`, `V4_PERSISTABLE =
false`, `V4_HUMAN_REVIEW_PACKET = NOT_PRODUCED`.

**Four historical values are recorded as observations and nothing more:** V4's 316 and 1078, and V3's
224 and 868. `V4_VALUES_USED_TO_DERIVE_HEADROOM = false`, and gate 83 enforces it:
- the two headroom modules read no file;
- they carry no integer other than 0, 1, 4, 5 and the wrapping width 96, so no bound, no target and no
  historical length can be written into them;
- no hard bound of the schema equals a length a historical answer had.

## The hard contract and the gate, unchanged (§5, §6)

- **Schema v1.1.0** is unchanged: `ec789d1b...`. `candidate_intervention_class.maxLength` is still
  300 and `evidence_bound_reasoning_summary.maxLength` is still 900. `OUTPUT_SCHEMA_CHANGED = false`.
- **Gate v1.3.0** is unchanged: `cc3c4902...`, confirmed by gate 77. No change to its semantic rules,
  source metadata, disjunction policy or lexical normalisation. `SEMANTIC_GATE_CHANGED = false`.
- **Prompt v1.3.0** still renders to `a62fa218...`.

## Which texts get a target (§7)

`generation_headroom.headroom_table` reads two existing classifications, and nothing new.

- **The output-constraint classification of Mission 1.84.8.** A `maxLength` with rule
  `composed_length` is text the model composes. A copied identifier, a closed choice or a sentinel
  carries another rule, and gets no target.
- **The semantic census of Mission 1.84.12.** Its rule `SUBJECT_IS_THE_PACKET_IDENTITY` fixes `subject`
  to the packet identity, copied exactly.

**The two classifications disagree on one field, `subject`.** The output-constraint classifier reads it
as composed because its schema carries no pattern, but the census says it is copied exactly. The policy
takes the strict reading: an identity copy gets no target. The census rule is named in the policy, and
the field is not hard-coded. This lowers the number of targets and never touches a hard bound.

**Twelve composed texts get a target:**

| field | hard maximum | generation target | classification |
|---|---|---|---|
| `target_actor_if_supported` | 200 | 160 | composed_length (A) |
| `observed_need` | 400 | 320 | composed_length (A) |
| `candidate_intervention_class` | **300** | **240** | composed_length (A) |
| `hypothesis_statement` | 600 | 480 | composed_length (A) |
| `independence_status` | 300 | 240 | composed_length (A) |
| `reliability_status` | 300 | 240 | composed_length (A) |
| `evidence_bound_reasoning_summary` | **900** | **720** | composed_length (A) |
| `critical_uncertainties[]` | 500 | 400 | composed_length (A) |
| `commercial_claims_supported[]` | 300 | 240 | composed_length (A) |
| `commercial_claims_not_supported[]` | 300 | 240 | composed_length (A) |
| `recommended_next_evidence[]` | 300 | 240 | composed_length (A) |
| `statement_classifications[].statement` | 300 | 240 | composed_length (A) |

Every row records its target source, `floor(hard * 4/5) under TARGET_AT_MOST_80_PERCENT_OF_HARD_MAX_LENGTH`,
and its hard-bound source, the schema path's `maxLength`. The table is generated from the live objects
and is never maintained by hand.

**Fourteen bounds get no target:**
- `subject` (80), an identity copy;
- `supporting_evidence_ids[]` (36), `supporting_claim_ids[]` (36) and `source_families[]` (128),
  all `copied_length`;
- the ten `maxItems` counts, under `ARRAY_HEADROOM_POLICY = NONE`.

Closed choices (`decision`, `confidence_classification`, the dimension names) carry no `maxLength` at
all.

## One derivation, exact (§8)

```
generation_target(max_length, ratio = Fraction(4, 5)) = (max_length * 4) // 5
```

- **The ratio is held as `fractions.Fraction(4, 5)`.** A float ratio is refused at construction, and
  so is a ratio outside (0, 1).
- **Gate 83 checks every hard maximum from 1 to 10000** against `floor(Fraction(n) * 4/5)`, and all
  are exact.
- **No target is written anywhere as a number.** All twelve derive from the live bound and the ratio.

## A target is not validation (§9, §20)

Gate 83 runs the live v1.1.0 validator for each of the twelve rows, at four lengths:

| length | verdict |
|---|---|
| target | PASS |
| target + 1 | PASS (`ABOVE_GENERATION_TARGET`, still schema-valid) |
| hard maximum | PASS |
| hard maximum + 1 | `SCHEMA_INVALID` |

For `candidate_intervention_class`, that means 240, 241 and 300 pass and 301 fails. For the summary,
720, 721 and 900 pass and 901 fails.

**Nothing downstream enforces a target.**
- The schema validator, the semantic gate and the persistence model do not know targets exist.
- Gate 84 proves it through the V5 runner's own stages. One character over a target passes stage 5,
  and one character over the hard maximum fails stage 5, for both fields V4 exceeded.
- A V5 runner test does the same at 241 characters.

## Prompt v1.4.0 (§10 to §18)

```
system    = prompt v1.3.0's system region + "\n" + the generation-headroom block + "\n"
trusted   = v1.3.0's, unchanged (SOURCE NAMES included)
untrusted = v1.3.0's, unchanged (the TED statements)
task      = v1.3.0's, unchanged
```

**Unchanged, byte for byte:**
- the output-contract block;
- the semantic-policy block;
- the SOURCE NAMES section;
- every word before them.

The block adds 51 non-blank lines, and its digest is `e10ee2b3...`.

**Nothing is left unstated.** For v1.4.0 the counts are:
- 0 unstated schema bounds;
- 0 unstated class-A semantic rules;
- 0 unstated generation targets.

The same headroom check finds 12 unstated targets in prompt v1.3.0.

What the block says, in substance:

- **The hard maxima are what the validator enforces.**
  - The model's own count of characters is approximate, so each composed text has a target at 4/5 of
    its hard maximum, rounded down.
  - A text over its target and within its hard maximum is still valid and is not refused for that.
  - The target is "guidance for writing, never a limit of the contract".
- **Each of the twelve texts is stated on its own line**, as "generation target N characters; hard
  maximum M characters". The two numbers are distinct, and both come from the schema.
- **No target applies to element counts**, which keep their exact limits.
- **No target applies to copied values or closed choices.**
- **Each field carries its own information once.** Two roles follow:
  - `candidate_intervention_class` (`NAME_THE_CLASS_ONLY`) names the class of intervention, and only
    the class. It is not a business plan, a product description, a justification, an evidence summary,
    an account of the target actor or a list of features. The reasons belong in the summary, and the
    actor in `target_actor_if_supported`.
  - `evidence_bound_reasoning_summary` (`COMPACT_SYNTHESIS_NOT_DUPLICATE_LEDGER`) is a synthesis, not a
    ledger. It covers what the evidence establishes, why the hypothesis remains exploratory, and the
    most important evidence boundary, and it stays substantive. It does not repeat item by item what
    the uncertainty, not-supported, next-evidence and classification lists carry. It does not enumerate
    every Evidence and Claim id, and it may still name the Evidence a point rests on.
- **Concision never costs information.** Being concise never removes:
  - an uncertainty;
  - an unsupported claim;
  - a source's provenance;
  - a relevant limitation;
  - the difference between observed and unknown;
  - a needed Evidence reference.

  It never raises the confidence or makes the answer harder to audit. A field that needs more than its
  target to stay complete may exceed the target, and still stays within its hard maximum.
- **Before submitting, reread and prefer concise wording.** Keep each text within its target where
  possible, and never over its hard maximum. That reread happens inside the one answer: "write no
  count, draft or working anywhere in it". There is no scratchpad, no hidden reasoning and no second
  call.

**The roles were written from the schema's field names and the existing semantic policy.** No answer
was read to write them. Gate 83 checks that the block never names a historical execution, carries none
of the four historical lengths, and never contains the word "tender". It also checks that the system
region is identical for the synthetic packet and for TED.

## No array headroom (§17)

`ARRAY_HEADROOM_POLICY = NONE`. Gate 83 mutates each of the ten `maxItems` bounds, and none moves a
target or the block. `maxItems` 10 stays 10, and nothing becomes 8.

## Drift (§19)

Gate 83 mutates the live schema and the policy, and then requires each change to move exactly the
targets it should:

| mutation | count | what must happen |
|---|---|---|
| a targeted `maxLength` + 1 | 12 | that hard maximum and its target move, nothing else moves, the block changes |
| the ratio (1/2, 3/4, 9/10) | 3 | every target becomes `floor(hard x ratio)`, in the table and as rendered |
| a copied or identity `maxLength` + 1 | 4 | no target appears, the block is identical |
| a `maxItems` + 1 | 10 | no target appears, the block is identical |
| an enum member added | 5 | no target appears, the block is identical |

**`HEADROOM_TARGET_DRIFT = 0`.** The rendered targets are parsed back out of the block and checked
under each ratio, so a target hard-coded in the rendering is refused too.

## Native structured outputs (§21)

**`NATIVE_PROVIDER_MAX_LENGTH_ENFORCEMENT = NOT_HELD`.**
- The capability register holds `NATIVE_STRUCTURED_OUTPUTS_SUPPORTED = true`, and nothing, from any
  reviewed page, about whether native structured outputs enforce `maxLength`.
- No documentation was fetched and no provider was asked.
- Nothing migrated: the forced tool and the local validator stay the mechanism.

## Stages 6 to 9 (§22)

**The preflight of Mission 1.84.12 ran unchanged**, and the result is still
`DETERMINISTIC_STAGE_6_TO_9_PATH_READY`.

**Gate 84 also runs the same six fixtures through the V5 runner.** Each stops at its own stage: the
valid answer is eligible at 9, and the failures stop at 6, 6, 7, 8 and 9.

**The prompt change touches no stage.** The semantic gate, the evidence boundary, provenance and
persistence eligibility are all V4's code.

## Consumed guards (§24)

- The V5 runner reads V1's to V4's records through V4's guard, then its own.
- The V1, V2, V3 and V4 digests are each refused with `EXECUTION_APPROVAL_ALREADY_CONSUMED`.
- V5's unseen digest is not refused.

## Execution packet V5 (§25 to §30)

`SECOND-OPPORTUNITY-SYNTH-EXEC-V5`, version 5. It is V4's call with prompt v1.4.0. It was built from
packet V4, with only the fields V5 changes rewritten.

```
EXECUTION_PACKET_ID                 SECOND-OPPORTUNITY-SYNTH-EXEC-V5
VERSION                             5
SHA256                              da3e7d09d97c30cd02859eaee729b6bd164cd99812feac34572a0e1d93aa511a
predecessor                         SECOND-OPPORTUNITY-SYNTH-EXEC-V4 7832b3bc... (EXECUTION_SCHEMA_REJECTED_NO_RETRY, consumed)
subject                             ted-eu:CPV-class:9261

provider / route                    anthropic, POST https://api.anthropic.com/v1/messages
                                    (synchronous Messages API, Commercial Terms, no beta header)
model                               claude-sonnet-5
thinking                            DISABLED ({"type": "disabled"})
max_tokens / calls / retries        128000 / 1 / 0
timeout                             60.0 s, not streamed

schema                              second-opportunity-synthesis-output@1.1.0  ec789d1b...
semantic gate                       second-opportunity-output-gate@1.3.0      cc3c4902...
prompt                              second-opportunity-synthesis-prompt@1.4.0 960955f4...
generation headroom                 TARGET_AT_MOST_80_PERCENT_OF_HARD_MAX_LENGTH, ratio 4/5
array headroom                      NONE
headroom record / policy digest     91a71efa... / c53ce0e9...
representation                      2528a56a...  3604 characters

human review required               true
canonical persistence               ONLY_AFTER_DETERMINISTIC_STAGES_1_TO_9_AND_SEPARATE_HUMAN_APPROVAL
OPERATOR_EXECUTION_APPROVAL_RECORDED false
NEW_APPROVAL_REQUIRED               true
PREVIOUS_APPROVAL_REUSABLE          false
```

**Cost, recomputed from the new request body (§27).** No token-count call was made, and V4's 1.312398
was not copied:

```
REQUEST_BODY_CHARACTERS_V5   31963   (V4 27946, rebuilt exactly, + 4017 from the headroom block)
INPUT_TOKEN_ESTIMATE_V5      18528   (ceil(31963 / 2.1565 x 1.25))
OUTPUT_TOKEN_CEILING         128000
TOTAL_TOKEN_CEILING          146528
pricing                      anthropic-published-2026-09-02, 0.002 / 0.01 per 1k (held)
WORST_CASE_INPUT_COST_V5     0.037056
WORST_CASE_OUTPUT_COST_V5    1.28
WORST_CASE_CALL_COST_V5      1.317056
EXECUTION_COST_CEILING_V5    1.317056   (headroom policy: NONE_HELD)
V4's ceiling                 1.312398   (+0.004658, x1.0035)
```

**V4's usage was observed and not used.**
- V4 estimated 16199 input tokens and used 11599, so the held method covered it and is unchanged.
- V4's 3950 output tokens do not size V5, and neither does any V4 length.
- V4 took 34.129 s, and the timeout stays 60.0 s.

**The digest binds V4's 101 fields plus nine headroom fields:**
- the decision and its record;
- the policy, the ratio and the array policy;
- the renderer, the field-role policy and the policy digest;
- the native enforcement status.

The key set is closed, as V4's was.

## The V5 runner (§31)

`run_second_opportunity_execution_v5.py` is derived from the V4 runner by counted, exact replacements.
**It verifies by default and executes only with `--execute`.** Its stage function, call site and
retention path are V4's, byte for byte.

**Before any socket, it checks everything the brief lists:**
- the packet digest;
- the approval;
- V1 to V4 spent;
- the schema and gate digests;
- the v1.4.0 prompt digest;
- schema-bound, semantic-rule and headroom drift, all 0;
- the headroom policy fields;
- the representation;
- the provider posture;
- TED egress;
- the route, model, thinking and `max_tokens`;
- calls, retries and the timeout;
- the cost ceiling;
- retention;
- stages 6 to 9 readiness.

Its dry verification ran against the research database:

```
01 packet digest                 da3e7d09...
03 V1 / V2 / V3 / V4 consumed    True / True / True / True     V5 consumed   False
04 representation                2528a56a...  3604 characters, 6 approved Evidence rows
05 prompt                        960955f4...
05 unstated bounds / rules / targets   0 / 0 / 0
06 schema / gate implementation  ec789d1b... / cc3c4902...
07 provider posture              APPROVED
08 TED transmission / live gate  PERMITTED_WITH_CONDITIONS / AVAILABLE
09 request thinking / max_tokens {"type": "disabled"} / 128000, body 31963 characters
11 worst case                    1.317056
13 retention ready / 14 stages 6-9 ready   True / True
OPERATOR_APPROVAL                OPERATOR_APPROVAL_NOT_RECORDED
```

**`--execute` refuses with `OPERATOR_APPROVAL_NOT_RECORDED` before a transport is constructed.**

## CI gates 83 and 84

- **Gate 83** (`render_second_opportunity_generation_headroom.py`) re-derives the headroom record and
  the prompt v1.4.0 record whole, with every check described above.
- **Gate 84** (`render_second_opportunity_execution_packet_v5.py`) re-derives packet V5. It reuses gate
  81's frozen helpers: the snapshot, the body builder, the single-call-site and no-post-processing
  checks, and the stages and retention paths. It compares everything with V4, and requires gates 79,
  80 and 83 to validate. It also checks the V5 runner's stages 6 to 9 and the target-is-not-a-bound
  property through the runner.

## Probe (§32)

**127 violations caught, 0 escaped, 31 of 31 positive controls, every file proved restored.**
`VIOLATIONS_ESCAPED = 0`, `POSITIVE_CONTROLS_FAILED = 0`.

What caught the violations:

- 120 were refused by the rules of gates 83 and 84.
- 3 were refused by render drift.
- 4 were refused by an exception outside the attacked gate's error class:
  - the two schema edits and the representation edit broke gate 76's snapshot authentication, which
    gate 83 stands on;
  - a float ratio is refused as soon as the policy object is built.

The families, all refused:

- **The headroom record** (gate 83, 41 cases). It is derived whole, and the cases covered:
  - the ratio (3/4, a moved decimal);
  - the ratio said to come from V4 or from history, and field-specific ratios;
  - V4's values said to derive the headroom, and the target treated as validation;
  - targets chosen from 316 and 1078;
  - a target added for a copied id, an enum or `maxItems`;
  - array headroom turned on, and the subject given a target;
  - 241 refused at 300, and 901 accepted at 900;
  - drift or a float error admitted;
  - V4's violations rewritten, V4 revalidated, made a candidate, given a review packet or unspent;
  - 300 raised to 316 and 900 to 1078;
  - the gate, schema or representation said changed;
  - native enforcement claimed, or the mechanism said migrated;
  - a model call or provider request counted;
  - a target left unstated, a scratchpad or a self-critique call;
  - the class role widened to rationale, the summary role dropped, uncertainty dropped from the floor;
  - stages 6 to 9 said not ready, its comment reworded, an extra field.
- **Prompt v1.4.0's record** (6 cases).
- **Packet V5** (gate 84, 46 cases). Each edit was re-digested, so the substantive rule had to catch it.
  The cases covered:
  - V5 marked approved, or said executed;
  - human review dropped;
  - another ratio, policy, array policy, record or policy digest;
  - native enforcement claimed, the decision shortened;
  - prompt v1.3.0 named;
  - another model, adaptive thinking;
  - a retry, two calls, a continuation or a repair model;
  - the provider mechanism migrated, native structured output;
  - truncation, rewriting or splitting allowed;
  - V4's ceiling, estimate or body length copied;
  - V4's approval unspent, V4 dropped from the consumed, V4's outcome rewritten;
  - V4's output used for headroom;
  - the schema or gate changed, gate v1.1.0, another representation;
  - an unreviewed field;
  - a model call, provider request or TED bytes counted;
  - `max_tokens`, the timeout or the route moved;
  - persistence enabled, V4's timing used;
  - V4's digest carried, a bound field edited with the digest left.
- **Approvals** (2 cases): V5 marked approved by this mission; V4's approval reused for V5.
- **V4's history** (7 cases):
  - its consumption reset;
  - its violations emptied;
  - an approval written into V4's packet;
  - **V4's answer truncated to fit, with every digest recomputed**;
  - V4's answer summarised;
  - V4's answer revalidated as a candidate;
  - V4's approval reused.
- **Rendered pages** (3 cases).
- **Live code, in a fresh interpreter** (22 cases):
  - maxLength 300 and 900 raised to V4's lengths;
  - the ratio moved to 3/4, held as a float, or derived from 316;
  - a field-specific ratio;
  - 80% applied to copied ids and to `maxItems`;
  - a target hard-coded in the rendering, or a target table maintained by hand;
  - a floating-point drift;
  - uncertainty omitted to satisfy a target;
  - Evidence references removed for brevity;
  - the class still told to carry its rationale;
  - the summary told to duplicate every list;
  - the semantic gate or the representation changed;
  - in the runner: the target enforced as a bound, the answer trimmed to fit, a retry, V4's spent
    approval made reusable, and another digest pinned.

**The positive controls:**
- the shipped gates 83 and 84;
- four notes of packet V5 that its digest does not bind;
- the hard schema and gate v1.3.0 unchanged;
- the ratio exactly 4/5;
- 240 derived from 300, and 720 from 900;
- for both fields: target + 1 schema-valid, the hard maximum schema-valid, hard maximum + 1 failing;
- copied fields, enums and `maxItems` receiving no target;
- prompt v1.4.0 stating the soft target and the hard maximum distinctly;
- stages 6 to 9 ready;
- comments in the headroom tests and in the V5 runner;
- the V1 to V4 guards active;
- V5's unseen digest awaiting approval, with no approval recorded;
- no real transport without an approval.

**Three gaps were found while designing the probe and closed before either run:**
- gate 83 now allows the headroom modules no integer beyond 0, 1, 4, 5 and 96, so a hard-coded target,
  a maintained table or a V4 value is refused;
- gate 83 parses the rendered targets back out of the block under every ratio;
- gate 84 proves, through the V5 runner's own stages, that one character over a target passes stage 5
  and one over the hard maximum fails it.

**The first run reported one escape, and it was the probe's own defect.** Its case "80% applied to
maxItems" opened only the keyword filter. The next filter, on the constraint rule, still excluded every
count, because no `maxItems` carries `composed_length`: they are `chosen_cardinality` and
`vocabulary_cardinality`. The mutated code produced the identical table, and gate 83 correctly passed
it. The case was corrected to open both filters and the whole probe was run again. The corrected case
is refused ("the targeted texts are not exactly the composed ones"), and the figures above are that
second run's. The first run gave 126 caught, 1 escaped and 31 of 31 controls. It is reported here, not
re-run away.

## Accounting (§36)

```
MODEL_CALLS                0
PROVIDER_REQUESTS          0
MESSAGES_API_REQUESTS      0
TOKEN_COUNT_API_REQUESTS   0
TED_BYTES_SENT             0
DOCUMENTATION_FETCHES      0
CANONICAL_MUTATIONS        0
```

## Canonical state (§33)

| | value |
|---|---|
| RawRecords | 325 |
| NormalizedRecords | 325 |
| Signals | 60 |
| Claims | 91 |
| ClaimRevisions | 92 |
| Evidence | 112 |
| ReliabilityAssessments | 4 |
| EvidenceIndependenceGroups | 0 |
| Opportunities | 1 |
| OpportunityRevisions | 2 |
| OpportunityEvidenceLinks | 14 |
| Embeddings | 0 |
| Scores | absent |
| SourceReviews | 71 |

The counters were read during the mission and again at the end, with no difference.

## Verification

- `ruff format --check` and `ruff check` are clean over 1085 files, and `mypy` over 211.
- Contracts, catalog and source registry are clean.
- **3853 bare-python tests and 4946 pytest tests** pass, 13 skipped, with the database unchanged
  across 29 tenant tables.
- **103 new tests**:
  - 38 on the headroom policy and prompt v1.4.0;
  - 65 on the V5 runner, including a class at 241 characters passing stage 5.
- **84 CI gates**, two of them new, all run locally with no failure, after both probe runs.

## Outcome and stop (§34, §39)

**`SECOND_OPPORTUNITY_EXECUTION_PACKET_V5_READY_FOR_OPERATOR_APPROVAL`.** No blocker was found. The
policy's surface was sufficient, with the one resolution recorded above for `subject`. The
representation did not move, the route and TED egress stand, stages 6 to 9 are ready, retention is
ready, and the V1 to V4 guards are active.

**What the operator would be approving, stated plainly:**
- **One call, with no retry, at a worst case of 1.317056.** V3 cost 0.057782, and V4 cost 0.062698.
- **The same TED bytes as V4.** The prompt is longer by 4017 characters, all of them targets, roles and
  the reread instruction.
- **A target is a request, not a guarantee.** The prompt asks for margin, and the schema still refuses
  an answer over a hard maximum, as it refused V4's. One call is one observation.
- **The semantic gate's documented limit is unchanged.** The residual limitation accepted for V4 is not
  carried over: an approval of V5 would say whether it accepts it again.
- **A pass is not a persistence.** An answer that passes stages 1 to 9 becomes eligible for human
  review only.

**V5 was not executed, and no approval was recorded.** An approval would be a separate record,
`second-opportunity-synthesis-execution-approval-v5.json`, naming V5's id, version and digest.
Mission 1.84.15 was not started.
