# Mission 1.84.27: The Intervention-Class Contract, Operator Decisions D3 and D5

**`INTERVENTION_CLASS_CONTRACT_IMPLEMENTED_OFFLINE_SENTINEL_AND_CITED_CLAIM_GROUNDING`**

The operator asked for two decisions to be resolved at the contract level, offline, with no synthesis:

- **D3.** `candidate_intervention_class` must stop pushing a model to invent a class when the supplied
  statements establish none.
- **D5.** The prompt must say what the gate treats as an assertion, and what it treats as a denial,
  an uncertainty, an unsupported concept or a request for evidence.

This mission built one design, **design E**, as successors beside the frozen contract:

- **Schema v1.3.0** changes one leaf: the class field's description. The description now states the
  contract's existing sentinel, `UNKNOWN_NOT_SUPPORTED`.
- **Gate v1.6.0** calls gate v1.5.0 once and keeps every reason it gives. It then adds one check on the
  class: it must be exactly the sentinel, or one short noun phrase whose words appear in the statements
  of the claims the answer cites.
- **Prompt v1.7.0** states that contract. It drops the v1.6.0 sentence that asked for "a more neutral
  class", and says which of its instructions the gate enforces and which it does not.

Nothing is bound to the successors. No packet exists, no runner uses them, and D4 is still not
authorised.

```
START_COMMIT        e29b3b437c7e869017bd76066ad118286875b4e0  (merged main after PR #170)
BRANCH              sprint-1/mission-1.84.27

PROVIDER_CALLS 0   MODEL_INFERENCES 0   TOKEN_COUNTS 0   RETRIES 0   PERSISTENCE 0
NEW_EXECUTION_PACKET NO   V11_CREATION NO   OPPORTUNITY_2_CREATION NO   RUNNER_BOUND NO   D4 NOT AUTHORISED

schema v1.3.0       1e5e8624...  (v1.2.0 7d67bad3... unchanged)
strict projection   cf98958a... over v1.3.0  (87028f45... over v1.2.0 unchanged; profile unchanged)
gate v1.6.0         contract implementation 0e3db2d2...  (gate v1.5.0 b188ba4c... unchanged)
prompt v1.7.0       16117619... over the V10 snapshot  (v1.6.0 a89960ce... unchanged)
gate 104            render_second_opportunity_intervention_class_contract.py
```

## How the work was divided

Four read-only agents worked in parallel, and the main agent was the only writer.

| Agent | Role | What it established |
|---|---|---|
| A | Contract historian | Why the field exists and who reads it |
| B | Schema architect | Designs A, B and C, plus two more |
| C | Adversarial contract tester | Smuggling, look-alike and paraphrase cases |
| D | D5 alignment | Where prompt v1.6.0 and gate v1.5.0 disagree |

The main agent chose the design, wrote every module, the tests and gate 104, and checked each agent's
claims against the code before relying on them.

## The role of the class field

**The ontology never required a class.**

- `opportunities.candidate_intervention` is `TEXT NOT NULL` with no `CHECK`.
- Opportunity #1 was persisted with a declined class.
- Nothing downstream reads the field as a category: no enum, no join and no human-review consumer.

**The field names the kind of intervention a hypothesis would test.** It is a supported assertion
under the field policy (`SUPPORTED_ASSERTION`, free text). That means its words must be supplied, not
brought in from outside knowledge.

**The pressure came from two places.**

1. Schema v1.2.0 gave the field a type and a hard maximum, and nothing else. Its sibling
   `target_actor_if_supported` has always had the sentinel. The class had no way to say "none", so
   every hypothesis had to name one.
2. Prompt v1.6.0's surface block told the model to *name a more neutral class grounded in what they do
   supply*. V9 (*An information or analytics offering ...*) and V10 (*An evidence-gathering or
   market-observation exercise ...*) both followed it, and both were refused for words no statement
   supplied.

## The designs compared

| Design | What it is | Why kept or rejected |
|---|---|---|
| A | Sentinel only, in the schema description | **Rejected alone.** Absence becomes representable, but a stated class is still held only by the denylist, so an unlisted invented word passes. |
| B | Structured object: class plus cited claim ids | **Rejected.** It breaks the persisted `TEXT` column, the strict projection and every consumer. It needs a new reference column for a guarantee that the cited ids already give. |
| C | Per-packet dynamic enum of allowed classes | **Rejected.** The schema would differ per packet, so digests and the frozen projection model fail. Building the enum needs a vocabulary whitelist or NLP. |
| D1 | Closed enum of classes | **Rejected.** A class the evidence does establish cannot be represented, and it is a broad vocabulary whitelist. |
| D2 | Force `INSUFFICIENT_EVIDENCE` when no class is supported | **Rejected.** It throws away a legitimate hypothesis only because no class is established, and the ontology does not require one. |
| **E** | **Sentinel plus grounding in the cited claims' statements** | **Selected.** See below. |

**Why E.** It meets every constraint the brief set:

- **Never forced to invent.** Absence is a complete and correct value, and the prompt says so.
- **One deterministic absence.** The exact sentinel, compared byte for byte. Empty, blank, re-cased,
  padded and prose-for-none values are refused and pointed at it.
- **Evidence-bound.** Every content word must occur, under the one inflection policy, in the content of
  the statements of the claims the answer cites, outside their quoted literals.
- **World knowledge is never support.** No word list licenses a word, and nor do source names, dimension
  names, trusted identifiers or claims the answer does not cite.
- **MARKET_ACTIVITY licenses nothing in the class.** A dimension classifies evidence; it does not
  describe an intervention.
- **No vocabulary whitelist.** The only lists are closed grammatical ones: articles, prepositions,
  conjunctions and negators, plus the reader's existing verb list.
- **No in-place edit.** Everything is a new module.
- **Works for future candidates.** Grounding reads whatever statements a packet cites, and nothing in it
  is specific to procurement.

## What changed, and what did not

**Schema: yes, one description.** `second_opportunity_schema_v1_3.py` deep-copies v1.2.0 and sets
`properties.candidate_intervention_class.description`:

> The class of intervention the supplied statements establish, as one short noun phrase whose words the
> statements of the cited claims use, or the exact string UNKNOWN_NOT_SUPPORTED if they establish none.

The type, the hard maximum, the required list and every other field are v1.2.0's.
`semantic_schema_diff` finds exactly that one leaf. The output-contract renderer reads the sentinel
from the description, as it already did for the target actor, so the prompt states it with no new
renderer.

**Projection: no code change.** `project_strict_input_schema` is pure, and descriptions pass through
unchanged. Over v1.3.0 it has the same profile, the same optional and union accounting, no blockers,
and the same single leaf moved, with a new digest (`cf98958a...`). Projection v1.0.0 over v1.2.0 still
hashes to `87028f45...`.

**Gate: yes, a successor.** `second_opportunity_gate_v1_6.py` works in four steps:

1. It calls `evaluate_second_opportunity_output_v1_5` exactly once.
2. It recomputes the schema v1.2.0 structural reasons, checks that v1.5.0 wrote them first, and
   replaces them with schema v1.3.0's. The only difference between the schemas is a description, which
   no validator reads. If v1.5.0 ever stops writing those reasons first, v1.6.0 raises
   `PredecessorShapeError` rather than drop reasons it cannot account for.
3. It appends the findings of `intervention_class_grounding@1.0.0`, one reason per finding.
4. It skips class grounding when the decision is `INSUFFICIENT_EVIDENCE`.

Gate v1.5.0, the field policy, the audit, the forbidden concepts, the markers and MARKET_ACTIVITY's
licence in the other fields are untouched.

**The grounding rules** (`intervention_class_grounding.py`) apply in this order:

1. **Absence.** The exact sentinel is accepted. A blank value, a letters-only spelling of an absence
   (`NOT_ESTABLISHED`, `None`, `N/A`, ...) or any value containing the sentinel is refused.
2. **Shape.** Plain ASCII letters in words joined by single spaces or hyphens. That excludes digits,
   punctuation, underscores and every other character, so no code, no clause and no look-alike or
   invisible character can pass.
3. **Length.** At most six words.
4. **Form.** The phrase may contain none of the following:
   - a negator;
   - a finite verb from the reader's list;
   - a past form followed by a determiner (*notices exceeded the smallest amount*);
   - a code written in capitals (*CPV*).
5. **Content.** At least one word must be a content word.
6. **Citation.** At least one of the answer's `supporting_claim_ids` must be a claim of this packet.
7. **Grounding.** Every content word must occur in those claims' statement content, with quoted literals
   masked. Without the mask, `"contract_notice"` would license *contract*, a trusted identifier leaking
   in; gate 104 pins that case as CH-06.

**Prompt: yes, a successor.** `second_opportunity_prompt_v1_7.py` builds its system region from
v1.5.0's pieces in the same order:

- the synthesis system text;
- the output contract rendered from schema v1.3.0;
- v1.3.0's census block;
- the headroom block rendered from schema v1.3.0.

It then appends a new generation-contract block, where v1.6.0 had appended its surface block. The
trusted context, the untrusted region and the task are byte for byte v1.6.0's over the V10 snapshot.
The system region grows from 19930 to 21318 characters.

## The D5 decision

**What was misaligned.** Agent D found the prompt and the gate disagreeing in both directions:

- **Prompt stricter than the gate.** Prompt v1.6.0 told the model to keep unsupplied concepts out of
  asserting fields entirely. The gate refuses them only when asserted. That was undocumented.
- **Gate stricter than the prompt.** The gate refuses validation words in asserting fields even when
  they are denied, and the prompt never said so.
- **A gap in both.** Neither says that the gate does not read the second clause of a request for
  evidence.

**Decision: state the gate's rules, and label the one instruction that goes beyond them.** The new
block, from `second-opportunity-generation-contract-policy@1.0.0`, tags every rule with how it is held:

| Rule | Held by |
|---|---|
| An unsupplied concept is refused where the answer asserts it | GATE_ENFORCED |
| A supported assertion's words come from the supplied statements | GATE_ENFORCED |
| Validation words are refused in asserting fields, even denied | GATE_ENFORCED |
| The class field is a supported assertion | GATE_ENFORCED |
| The class's absence is exactly `UNKNOWN_NOT_SUPPORTED`, a complete and correct value | GATE_ENFORCED |
| The class's words come from the cited claims' statements; never a dimension's name | GATE_ENFORCED |
| The class is one short noun phrase, at most six words | GATE_ENFORCED |
| The request surface forms (from the v1.6.0 surface policy, unchanged) | GATE_ENFORCED / GUIDANCE_ONLY as before |
| Denials belong in the framed fields (`commercial_claims_not_supported`, `critical_uncertainties`) | **INSTRUCTION_BEYOND_THE_GATE**, stated as deliberately stricter than the audit |
| Unsupported concepts have framed fields; guidance is not a guarantee | GUIDANCE_ONLY |

**What the block deliberately does not do.**

- It does not publish the parser's private patterns.
- It writes no digit, so no number can drift from the schema.
- It does not weaken any evidence requirement: every rule the gate enforced before, it still enforces.

**The structural guarantee is the gate, not the wording.** A model that ignores the block still meets
gate v1.6.0's grounding. The wording's job is to make the correct answer the obvious one, and in
particular to make the sentinel a normal answer rather than a failure.

## Synthetic results

Gate 104 runs everything below on the frozen Mission 1.84.11 fixture (`test_semantic_gate_v1_3.py`).
The fixture supplies MARKET_ACTIVITY, and no statement in it carries *market*.

**Class matrix: 61 cases, every one as intended.**

| Group | Cases | Result under v1.6.0 |
|---|---|---|
| Absence (the sentinel) | 1 | accepted, as under v1.5.0 |
| Absence near-misses (empty, blank, padded, re-cased, `NOT_ESTABLISHED`, `None`, sentinel plus label) | 8 | all refused; v1.5.0 accepted all 8 |
| Grounded (*published notices*, *stated amounts of notices*, *notice amounts*, *classified notices*, *set of notices from the resource*) | 5 | all accepted |
| Citation (a word cited only by an uncited claim, no claim, a foreign claim) | 3 | all refused |
| Invented vocabulary (*notice monitoring*, *procurement analytics*, *software platform*, ...) | 6 | all refused |
| MARKET_ACTIVITY (*market activity*, *market-observation exercise*, *marketplace for notices*, ...) | 8 | all refused, each by class grounding |
| Channels (source name *register*, *daily*, *synthetic*; dimension *economic value*, *buyer budget*; quoted literal *contract*, *awards*) | 7 | all refused |
| Identifiers and numbers (*CPV*, *TOTAL_VALUE*, *BT-161*, *5555*, *120000 EUR*) | 7 | all refused |
| Characters (accented, spaced, capitals, zero-width, Cyrillic, full-width, soft hyphen) | 8 | all refused |
| Denials and clauses | 6 | all refused |
| Shape (too long, only grammatical words) | 2 | all refused |

- **44 cases move from accepted to refused.** Nothing v1.5.0 refused is accepted.
- **Every divergence is a class-grounding reason.** For every case, v1.6.0's reasons are v1.5.0's
  (structure renamed to v1.3.0), followed only by reasons under the class-grounding prefix. Gate 104
  checks this case by case.

**Every other field reads exactly as before.** All 131 sentences of gate 103's matrix were placed in
`observed_need` with the class set to the sentinel. Gate v1.6.0 returns exactly v1.5.0's reasons for
every one.

**Smuggling through the new representation: none.**

- The sentinel is an exact string, so nothing can ride along with it: `UNKNOWN_NOT_SUPPORTED: notice
  review` is refused.
- Absence adds no new field and no new free text anywhere.

**Displacement into other fields: unchanged, recorded as debt.** Eight cases leave the class absent
and write intervention vocabulary elsewhere. Examples:

- *Contracting authorities could adopt a notice monitoring service.* (`hypothesis_statement`)
- *Authorities need a notice monitoring service.* (`observed_need`)
- *The notices record market activity.* (`observed_need`)

All eight pass both gates identically. Design E does not claim to fix this, and neither would A to D.

**Tests.** `test_intervention_class_contract_v1_3.py`, 72 tests, covers:

- the schema's single leaf and its projection;
- absence and its near-misses;
- grounding, including an uncited claim, a source name and a quoted literal;
- gate composition: one call, structure renamed, every other field unchanged;
- prompt v1.7.0: nothing unstated, the contract rules unstated by v1.6.0, the forcing sentence gone, no
  digit, the one stricter instruction labelled, and the gate doing what the block says.

## Historical immutability

**V1 to V10 artifacts and verdicts are untouched.**

- Gate 104 re-runs gates 98 and 101's validation, so V9's and V10's records still stand as recorded.
- It pins their retained responses and records by file digest.
- Gate v1.5.0 still gives exactly the reasons gate 103 recorded for each.

**Diagnostic projection only, never written over the records.** What gate v1.6.0 would say is recorded
beside the history:

| Execution | Class | v1.5.0 reasons | v1.6.0 would refuse with |
|---|---|---|---|
| V9 | *An information or analytics offering that aggregates and compares published CPV-9261 procurement notice values ...* | 7 | 8: the same 7, plus the class is not one plain-word noun phrase |
| V10 | *An evidence-gathering or market-observation exercise directed at procurement activity classified under CPV class 9261.* | 1 (`market`) | 2: `market`, plus the same shape finding |

Both stay refused, and neither is a candidate for review or persistence.

**Every predecessor recomputes to its pin:**

- gates v1.2.0 `47bbcb45...`, v1.3.0 `cc3c4902...`, v1.4.0 `eb03899b...` and v1.5.0 `b188ba4c...`;
- gate 102's diagnosis and gate 103's record, byte for byte;
- schema v1.2.0 `7d67bad3...` and projection `87028f45...`;
- prompt v1.6.0, rendered over the V10 snapshot, still `a89960ce...`.

No file named `*v11*` exists. No script other than gate 104 imports schema v1.3.0, gate v1.6.0 or
prompt v1.7.0.

## Provider counts and canonical counters

```
provider requests 0   model inferences 0   token counts 0   retries 0   TED bytes 0   persistence 0
```

Network tripwires are active throughout gate 104: gate 76's transport tripwire, plus `urlopen` patched
to raise.

The canonical counters were read locally, read-only, before and after the full verification, and are
unchanged:

```
raw_records 325   normalized_records 325   signals 60   claims 91   claim_revisions 92
evidence 112   reliability_assessments 4   evidence_independence_groups 0   opportunities 1
opportunity_hypothesis_revisions 2   opportunity_hypothesis_evidence 14   embedding_provenance 0
scores absent   source_policy_reviews 71
```

## Remaining semantic debt

1. **Displacement across fields.**
   - **Risk:** intervention vocabulary written in `hypothesis_statement`, `observed_need`,
     `target_actor_if_supported` or the list fields is held only by the denylist audit.
   - **What would close it:** a cross-field rule, and an operator decision on how a hypothesis may
     describe what it would test (Agent C's SMG-06).
2. **Lexical grounding is not semantic validity.**
   - **Risk:** a class built from cited words can restate the evidence (*published notices*) rather
     than name an intervention.
   - **What would close it:** nothing in the gate. Human review stays mandatory.
3. **Characters in other fields.**
   - **Risk:** the class refuses look-alike and invisible characters, but the other fields' tokenizer
     does not.
4. **Inherited pronoun case (out of scope).**
   - **Risk:** *Software is not established, and it is probably large.* still passes under v1.2.0's
     rule, in every gate version.
5. **Census coverage.**
   - **Risk:** `ADDED_CONCEPTS_NOT_ASSERTED` is not checked on free-text not-supported items or on
     HYPOTHESIS and UNKNOWN statement classifications.

## Gate 104, verification, probe

**Gate 104** re-derives the whole record under network tripwires:

- predecessor pins;
- the schema and projection diff;
- the prompt checks over the V10 snapshot;
- the class matrix with intended verdicts and the case-by-case differential;
- every other field unchanged;
- V9 and V10 diagnostically;
- no V11 file and no binding.

The committed JSON must equal the derivation, and the Markdown must be its rendering.

**Local verification**, the same checks CI runs:

- ruff format and check clean; mypy clean over 225 source files;
- contracts, `sros-source` and the source registry pass;
- **104 of 104 gates** pass;
- the bare runner passes 3877 tests; the pytest suites pass 7012 (72 new), with the database and global
  tables unchanged by the run;
- canonical counters identical before and after; no CR in any new or edited file.

**Probe: 18 caught, 0 escaped, 2 of 2 controls**, in one run of 981 s, every file restored and checked by
digest before anything was committed.

| Mutation | Caught by |
|---|---|
| Schema v1.3.0, grounding or contract test file edited, pin kept | the implementation or test pin |
| Gate v1.5.0 edited; prompt v1.6.0's surface sentence edited; gate 103's record edited | the predecessor pins |
| Record: V10 would persist; displacement debt erased; a displacement case dropped | record not what the code derives |
| Page edited | not the rendering of its record |
| V10 response rewritten to the sentinel | gate 101's validation |
| Re-frozen: quoted literals not masked | CH-06 *contract notices* accepted, intended REFUSE |
| Re-frozen: uncited claims license words | REF-01 accepted, intended REFUSE |
| Re-frozen: grounding never applied | NE-01 accepted, intended REFUSE |
| Re-frozen: last predecessor reason dropped | the case-by-case differential |
| Re-frozen: schema moves a second leaf | the one-leaf schema diff |
| Re-frozen: contract block brings the forcing sentence back | the forcing-sentence check |
| Re-frozen: twelve words allowed | **an exception** (`KeyError: 12`): the contract renderer writes the limit as a word and has none for twelve. Caught, but not by a rule |

## Files

**New:**

- `packages/opportunity-engine/python/sros_opportunity/second_opportunity_schema_v1_3.py`
- `packages/opportunity-engine/python/sros_opportunity/intervention_class_grounding.py`
- `packages/opportunity-engine/python/sros_opportunity/second_opportunity_gate_v1_6.py`
- `packages/opportunity-engine/python/sros_opportunity/generation_contract_policy.py`
- `packages/opportunity-engine/python/sros_opportunity/second_opportunity_prompt_v1_7.py`
- `packages/opportunity-engine/python/tests/test_intervention_class_contract_v1_3.py`
- `infrastructure/scripts/render_second_opportunity_intervention_class_contract.py` (gate 104)
- `docs/data/second-opportunity-intervention-class-contract-v1.json` and `.md`
- `docs/reports/mission-1.84.27-report.md`

**Edited:**

- `.github/workflows/ci.yml` (gate 104 step)
- `PROJECT_MANIFEST.md` (1.161)
- `docs/CLAUDE.md` (1.162)

**Not touched:** schema v1.2.0, prompts v1.5.0 and v1.6.0, gates v1.2.0 to v1.5.0, the strict projector
and profile, the field policy, every V1 to V10 artifact, and the database.

## D4 recommendation

**D4 is not authorised, and this mission does not recommend authorising it yet.** The contract makes a
future synthesis able to answer honestly, but four things should come first:

1. **An operator decision on cross-field displacement.** Without it, a model told that the class may be
   absent can move the same vocabulary into `hypothesis_statement`, where only the denylist reads it.
2. **A review of the prompt v1.7.0 wording on its own terms.** Is the sentinel presented as a normal
   answer, and is the one INSTRUCTION_BEYOND_THE_GATE line wanted?
3. **A decision on which gate a future execution binds.** v1.6.0 is the only gate that reads schema
   v1.3.0, and nothing binds it now.
4. **Only then, if D4 is authorised,** a new packet under its own mission, with its own approval, never
   by editing V10.

**Stopped here.** No V11, no approval, no runner binding, no Opportunity #2, and no evidence
acquisition was started.
