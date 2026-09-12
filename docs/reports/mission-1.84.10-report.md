# Mission 1.84.10: Semantic Assertion-Context Repair, Local Replay and Execution Packet V4

**`V3_DIAGNOSTIC_REVEALED_NEXT_EXECUTION_BLOCKER`**

The operator kept output schema v1.1.0 and prompt v1.2.0 and asked for the semantic gate's assertion
context to be repaired in a general way, with no answer whitelisted, no forbidden concept removed
and no evidence boundary weakened. **Gate v1.2.0 was built beside v1.1.0, tested on synthetic cases
only, frozen, committed and pushed. Then, and only then, V3's retained answer was replayed through
it once, diagnostically.** The five historical refusals no longer fire. **One new refusal does, at
stage 6, and it is a defect of the frozen gate rather than of the answer.** The brief makes V4
conditional on stages 6 to 9 passing, so **no V4 packet, runner or approval surface was created**,
and the gate was not touched after the replay.

```
START_COMMIT       bb0f50a52722b20f12ef77e23eac9155f4217232
BRANCH             sprint-1/mission-1.84.10
FREEZE_COMMIT      3f8c63400d7b7a3e0088e2e1c1c119efd7aa7845   (pushed before the replay)

GATE_V1_2_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY   true
HISTORICAL_V3_GATE_V1_1_VERDICT                        FAILED  (5 reasons, reproduced exactly)
DIAGNOSTIC_GATE_V1_2_VERDICT                           FAILED  (1 reason)
EXECUTION_PACKET_V4                                    NOT_CREATED
PRIMARY_OUTCOME                                        V3_DIAGNOSTIC_REVEALED_NEXT_EXECUTION_BLOCKER
```

## The operator's decision, carried as data

`KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED`, `KEEP_PROMPT_V1_2_0_UNCHANGED`,
`REPAIR_SEMANTIC_GATE_ASSERTION_CONTEXT`, `DO_NOT_WHITELIST_THE_V3_ANSWER`,
`DO_NOT_REMOVE_FORBIDDEN_CONCEPTS`, `DO_NOT_WEAKEN_EVIDENCE_BOUNDARIES`. The tuple lives in
`second_opportunity_gate_v1_2.SEMANTIC_GATE_REPAIR_DECISION`, and gate 75 refuses a copy that is
shortened or reworded.

## V3, reconfirmed and unchanged

Re-read from Mission 1.84.9's artifacts, whose eight files gate 76 pins byte for byte:

```
packet             c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2
outcome            EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY, approval consumed
requests / calls   1 / 1        retries / continuations / repairs   0 / 0 / 0
stop_reason        tool_use
tokens             9491 input, 3880 output, 0 thinking        cost 0.057782
schema             PASSED       semantic gate v1.1.0   FAILED       persistence   false
stages             1-5 PASSED, 6 FAILED, 7-10 NOT_REACHED
```

**The five reasons reproduce exactly under v1.1.0**: first locally with the packet rebuilt from the
research database and a tripwire on the real transport, then again inside the diagnostic replay,
and again in CI from the authenticated snapshot. V3 stays `EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY`
and consumed. No V1, V2 or V3 packet, approval, record or response was rewritten.

## The audit, before any design

What the repository already had, read before anything was written:

- **The claim guard** (`guards.py`, 1.2.0) clears a term under a denial marker earlier in the same
  SENTENCE, or when the term is the subject of its own negated copula. It was the right machinery
  with the wrong scope: a marker anywhere earlier in the sentence cleared everything after it, so
  *these rows are not unscored; they are scored* read as a denial, and `never` matched inside
  *nevertheless*.
- **The audit** (`validation.py`, 1.2.0) reads five prose fields against the supplied statements and
  the packet's structural counts. Its universe had no place for a trusted limiting fact, so `BT-161`,
  which the packet's own dimension bound carries, counted as prior knowledge.
- **The persistence gate** (1.1.0) refused a substring: `"SCORED" in reliability_status`, which
  *not the same as scored* contains.
- **The v1.0.0 phrase scan** refused five transformations wherever they appeared in any field, with
  no notion of denial, of field, or of the answer's own classifications.

All four were reused where their semantics matched and none was edited.

## Gate v1.2.0

**Versioned beside v1.1.0, never over it.** `guards.py`, `validation.py`, `second_opportunity.py`
and `schema_validation.py` are byte-identical to bb0f50a, pinned by digest, so V2's and V3's verdicts
still resolve against the code that produced them. Two new modules carry the successor:

| component | version |
|---|---|
| gate | `second-opportunity-output-gate@1.2.0` |
| output schema | `second-opportunity-synthesis-output@1.1.0` (unchanged, `ec789d1b...`) |
| persistence gate | `opportunity-synthesis-persistence-gate@1.2.0` |
| audit | `opportunity-synthesis-audit@1.3.0` |
| claim guard | `opportunity-claim-guard@1.3.0` |
| field context policy | `second-opportunity-field-context-policy@1.0.0` |
| support universe | `opportunity-support-universe@1.0.0` |
| trusted context | `second-opportunity-trusted-context@1.0.0` |

**Assertion, not token presence.** A concept is refused when it is ASSERTED. It is not refused when
it is denied in its own clause, requested as evidence that would be required, framed as an
uncertainty, listed as not supported, or classified by the answer itself as unknown. Clauses break at
a semicolon, a dash, a contrastive conjunction, a non-restrictive relative clause, a comma splice and
a coordinated clause with its own subject; a plain comma inside a list does not break one, so one
denial still covers *need, gap or willingness to pay*. A denial followed by a contrastive
continuation re-asserts: *actual expenditure is not established, but is probably substantial*.
Intensifiers are not denials, and markers match on token boundaries. **This is not a general
language engine**: every rule is a bounded pattern over the guard's own vocabulary.

**Field context (§7 to §12).** Every property of the v1.1.0 schema has a disposition and a shape,
and a field the policy does not name fails closed:

| field | disposition | shape |
|---|---|---|
| `commercial_claims_supported[]` | SUPPORTED_ASSERTION | FREE, checked strictly |
| `commercial_claims_not_supported[]` | EXPLICITLY_NOT_SUPPORTED | FREE, and an item that says it IS established contradicts its field |
| `critical_uncertainties[]` | UNKNOWN_REQUIRES_EVIDENCE | UNCERTAINTY |
| `recommended_next_evidence[]` | FUTURE_EVIDENCE_REQUEST | REQUEST |
| `statement_classifications[]` | from the label: OBSERVED is asserted, HYPOTHESIS is not promoted, UNKNOWN is not an assertion | LABELLED |
| `supported_dimensions[]` | STRUCTURAL_FACT | ENUMERATION |
| `unsupported_dimensions[]` | EXPLICITLY_NOT_SUPPORTED | ENUMERATION, disjoint from the supported set |
| `reliability_status`, `independence_status` | STRUCTURAL_FACT | FREE |
| `hypothesis_statement` | HYPOTHESIS_TO_VALIDATE | FREE |
| `evidence_bound_reasoning_summary`, `observed_need`, `candidate_intervention_class` | SUPPORTED_ASSERTION | FREE |

A request that stops being request-shaped is read as the assertion it has become, so *actual
expenditure was 10 million EUR* in `recommended_next_evidence` fails there, twice over. The seventh
disposition, `TRUSTED_LIMITING_FACT`, is a support category that no output field may claim.

**The support universe has three separate channels** (§15): the supplied statements, the packet's
structural facts (ids, families, supported and unsupported dimensions, scorability, independence and
subject identity), and trusted limiting or definitional context. **`PROMPT_TEXT_IS_NOT_OBSERVED_EVIDENCE
= true`**: nothing reads a prompt region. A trusted fact is a typed `TrustedFact` with a provenance,
passed through an explicit channel that has no default. `build_trusted_context` derives it from the
packet's own dimension bounds, with the mapping version and signal type that produced each, and from
the establishes side of `FORBIDDEN_TRANSFORMATIONS`, rendered in prompt 1.2.0. It **licenses the
definitional identifiers those facts carry (`BT-161`, `BT-195`, `BT-198`) and nothing else**: never
their words (the bound says *SaaS*, and *SaaS* is still refused), never their numbers as magnitudes
(*161 EUR* is refused), and never a concept they limit. *Per BT-161, the actual expenditure was large*
fails and names the trusted fact it misused. An unknown external definition (*BT-27*, a directive
number) fails.

**`MARKET_ACTIVITY` (§16, §17).** The canonical enum term, in words, is licensed as a whole phrase
where the answer declares the dimension AND the packet supports it: `market activity` is derived from
`EvidenceDimension.MARKET_ACTIVITY` in code, never transcribed. No paraphrase and no single word is
licensed: *the market wants a scheduling platform* and *this market is growing* still fail on
`market`. The choice is recorded in the freeze.

**SCORED (§14)** is refused in any asserted form in any asserting field (*are scored*, *have been
scored*, *carries a score*, *the evidence score is*, *scored rows*) and accepted in any denied one
(*no score exists*, *scoring-ready, not scored*, *neither row has been scored*, *none of them is
scored*). Scorability must still be stated.

**The forbidden concepts stay forbidden as assertions (§20).** Every v1.0.0 phrase is kept, and
market size, buyer need, unmet need, dissatisfaction, solution gap, competitive gap, software and
product demand and profitability are added. Validation vocabulary is still refused unconditionally,
as v1.1.0 did: nothing old was loosened. **Three structural facts v1.1.0 never checked are now
checked**: the subject identity, the source families, and supported/unsupported disjointness.

## Frozen before the replay

`GATE_V1_2_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY = true`, and it is a checkable fact rather than a
claim:

```
implementation digest   47bbcb459b0b69153d23c7dcc7f273e0e47d0b84a72522d25f773cd462db82b0
frozen test file        c84d99cfe8d43027f89ba5e46ae599b04b5fd786472818c1e014f46343560cf0
freeze commit           3f8c634, pushed to origin before the replay ran
```

Gate 75 derives the freeze record from the live code and pins both digests in its own source, so a
later `--write` cannot re-freeze a changed gate. It also refuses any six-word run of the historical
answer in the gate or in its tests beyond the brief's own cases. **That check fired twice during the
design**: once on a synthetic statement of mine that echoed a V3 phrase, and once on a test sentence
modelled on V3's summary. Both were rewritten, and the brief's own verbatim cases are the only text
the tests may share with the historical answer. The tests cover:

- 161 synthetic cases: the §5, §13, §14, §11, §12 and §20 matrices, the structural facts, the trusted
  identifiers, the field policy and the adversarial dressings;
- 29 freeze cases.

## The diagnostic replay

`render_second_opportunity_v3_diagnostic_replay.py --replay` ran once, with the database, against
the freeze commit. It rebuilt V3's packet and wrote an exclusive-create record. **CI re-runs the whole
replay without the database**: the packet snapshot is authenticated by rebuilding, from the snapshot
alone, the approved representation (`2528a56a...`) and the rendered v1.2.0 prompt (`1677cbe5...`).
Stages 1 to 9 are the V3 runner's own `validate_execution`, with nothing swapped but the semantic
gate. The runner's bytes are pinned, and the runner is the machinery a future call would use.

| stage | V3 (v1.1.0) | diagnostic (v1.2.0) |
|---|---|---|
| `1_transport_success` | PASSED | PASSED |
| `2_provider_response_shape` | PASSED | PASSED |
| `3_provider_completion` | PASSED | PASSED |
| `4_structured_output_parse` | PASSED | PASSED |
| `5_schema_validation_v1_1_0` | PASSED | PASSED |
| `6_semantic_output_gate` | FAILED, 5 reasons | **FAILED, 1 reason** |
| `7_evidence_boundary_and_no_distortion` | NOT_REACHED | NOT_REACHED |
| `8_attribution_and_provenance` | NOT_REACHED | NOT_REACHED |
| `9_persistence_eligibility` | NOT_REACHED | NOT_REACHED |
| `10_human_review` | NOT_REACHED | NOT_MANUFACTURED_DIAGNOSTIC_ONLY |

**The five historical refusals no longer fire, each for the general reason built for it:**

- `reliability_status` audits SUPPORTED (the score is denied);
- the summary audits SUPPORTED: `BT-161` is a trusted identifier and `market activity` is the
  canonical term of a supported dimension;
- `actual expenditure` sits in a request-shaped request;
- `willingness to pay` and `willing to pay` sit in denials, in the not-supported list and in an
  UNKNOWN classification.

**The one new refusal**, verbatim:

```
statement_classifications[7].statement audited UNSUPPORTED: 'tender' appears in no supplied
statement; prior knowledge is not available as factual support (§7)
```

The statement is *"Transactions or tenders occur in the bounded scope of CPV class 9261 notices."*,
which the answer classified OBSERVED. **v1.1.0 never read it: v1.2.0 audits every field, where v1.1.0
read five.** The finding is false as worded, because the supplied statements do carry the word:
*Tenders* Electronic Daily. The marker list holds both `tender` and `tenders`:

- `tenders` is licensed, because the supplied tokens contain it exactly;
- `tender` is not, because the supplied check compares exact tokens while the classifier folds
  plurals on the answer's side, so `tenders` in the answer matches the singular marker.

**It is a defect in how gate v1.2.0 applies one rule to two sides**, and a test shows it is general:
on a synthetic packet, any supplied plural refuses its own singular. The replay found it, which is
what the replay was for.

**It was not repaired.** Changing a frozen gate after seeing how V3 fares is tuning the gate on V3,
which §0 and §27 forbid. The probe includes that exact repair, a one-line licence fold, as a case
that gate 75 must refuse, and it does. V3 stays historically rejected:

`V3_HISTORICALLY_REJECTED = true`, `V3_CANDIDATE = false`, `V3_HUMAN_REVIEW_PACKET = NOT_PRODUCED`,
`V3_PERSISTABLE = false`, stage 10 not manufactured, nothing persisted.

## Why there is no V4

§32 creates V4 only if the diagnostic stages 6 to 9 all pass, and stage 6 failed. Stages 7 to 9 were
therefore not reached, and V4 would have been prepared with a gate the diagnostic had just shown to
refuse a supplied word. **No execution packet V4, no V4 runner, no V4 gate and no approval surface
exist**, and no provider was called. A future execution needs a gate that the operator decides on,
frozen and replayed again, before any packet digest can be approved.

The facts the operator's next decision rests on, with nothing recommended:

- the blocker is one rule, the marker licence, applied with plural folding on one side and not the
  other;
- the smallest general change is to license a marker when the supplied tokens contain it under the
  same folding the answer is read with. It is a gate change, so it is a new gate version with its own
  freeze and its own diagnostic replay;
- whether *tenders*, supplied only inside a publisher's name, should license *tenders occur* as an
  observation is a separate question about what a source name supplies, and it was not decided here;
- the stages after 6 (evidence boundary, provenance, persistence eligibility) have not yet been
  exercised on V3's answer under the new gate.

## CI gates 75 and 76

- **Gate 75** (`render_second_opportunity_semantic_gate_v1_2.py`) re-derives the freeze record and
  refuses the following:
  - a changed implementation or frozen test file;
  - a historical module that is not bb0f50a's, or a moved schema;
  - the decision edited, or a required field context moved;
  - a concept removed, a v1.0.0 phrase dropped, or a §20 concept unnamed;
  - prompt text treated as evidence, or a wider trusted licence;
  - a thin matrix;
  - a run of the historical answer;
  - a record field the code does not derive.
- **Gate 76** (`render_second_opportunity_v3_diagnostic_replay.py`) re-derives the replay from the
  authenticated snapshot. It checks that the frozen gate still validates. Where history is present,
  it checks that the freeze commit is an ancestor, carries the freeze record and did not carry the
  replay record. It pins V3's eight artifacts, reconfirms V3's facts and five reasons, and refuses:
  - a tampered snapshot;
  - a stage, verdict, reason or outcome the replay does not derive;
  - V3 made a candidate or persistable, stage 10 manufactured, or a human-review packet;
  - a second replay, or a replay against another commit.

## Probe

**139 violations caught, 0 escaped, 19 of 19 positive
controls, every file proved restored.** The caught violations break down as follows:

- 95 refused by the record gates' own rules;
- 2 refused by render drift;
- 42 refused by the frozen gate's semantics.

The cases, by family:

- **The freeze record** (gate 75): the order flags flipped, an allowlist added, a concept or a
  v1.0.0 phrase dropped, the decision reworded, a disposition softened, prompt text admitted as
  evidence, the trusted licence widened, the canonical-term policy widened, a model call counted.
- **The replay record** (gate 76): V3 made a candidate or persistable, stage 10 manufactured, stages
  6 to 9 marked passed, the reason dropped or reworded, V3's facts rewritten, the snapshot's
  statements, bounds, dimensions, ids or scorability tampered with, the freeze commit or its digest
  changed, an extra `V4_READY` field.
- **History, on disk**: V3's answer rescued consistently in both the parsed output and the retained
  tool input, V3's reasons trimmed, its approval unspent, its packet marked approved inside.
- **Live code, in a fresh interpreter**:
  - an allowlist for the refused sentence;
  - the plural fix the replay suggests;
  - trusted facts licensing their words;
  - denial scope widened back to the sentence;
  - the score check disabled;
  - prompt text treated as evidence;
  - a §20 concept dropped;
  - requests no longer shape-checked;
  - `guards.py`, the v1.1.0 SCORED check or the v1.0.0 phrase scan edited;
  - the V3 runner's stage 7 edited under the replay.
- **Semantics**: a long list of violations over a synthetic answer, every asserting field and every
  shape, all refused. The brief's legitimate forms are all accepted.

## Accounting

```
MODEL_CALLS                0
PROVIDER_REQUESTS          0
MESSAGES_API_REQUESTS      0
TED_BYTES_SENT             0
CANONICAL_MUTATIONS        0
Opportunities persisted    0
```

## Canonical state

| | start | end |
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

- `ruff format --check` and `ruff check` are clean over 1042 files, and `mypy` over
  203.
- Contracts, catalog and source registry are clean.
- **3853 bare-python tests and 4463 pytest tests**, 13 skipped, with the database
  unchanged across 29 tenant tables.
- **219 new tests**: 161 on the gate, 29 on the freeze, 29 on the replay.
- **76 CI gates**, two of them new.

## Outcome and next

**`V3_DIAGNOSTIC_REVEALED_NEXT_EXECUTION_BLOCKER`.**

**Stop.** The diagnostic did its job: it found, at no cost, a defect that would have refused a
future call's answer at stage 6. What happens next is the operator's decision:

- a gate version that fixes the licence fold, frozen and replayed again;
- a decision on what a publisher's name supplies;
- or anything else.

This mission recommends none of them.

**Do not execute anything, do not re-execute V3, do not treat V3's answer as a candidate, and do not
persist Opportunity #2.** Mission 1.84.11 was not started.
