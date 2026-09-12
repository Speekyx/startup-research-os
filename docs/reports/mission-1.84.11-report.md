# Mission 1.84.11: Symmetric Lexical Normalization, Source-Metadata Evidence Boundary and V3 Replay

**`V3_DIAGNOSTIC_REVEALED_GENUINE_OUTPUT_SUPPORT_FAILURE`**

The operator made two decisions. First, the inflection asymmetry that Mission 1.84.10's replay found
in gate v1.2.0 is a gate defect and must be repaired generally. Second, a source name, publisher name,
registry display label or provenance label is **not** factual support merely because a domain word
occurs inside it.

**Gate v1.3.0 was built beside v1.1.0 and v1.2.0, tested on synthetic cases only, frozen, committed and
pushed. Then, and only then, V3's retained answer was replayed through it once, diagnostically.** The
historical verdicts of v1.1.0 and v1.2.0 reproduce exactly. Under v1.3.0, **V3 stops at stage 6 on one
statement, for a reason that is now true**:
- the statement asserts a word that its sources supplied only inside the publisher's name;
- it also joins two alternatives under one OBSERVED classification.

That is a genuine support failure of the answer, not another defect of the gate. **No V4 was created**,
and the gate was not touched after the replay.

```
START_COMMIT       714906f69c38d120070654ac421a4105d0d25bd9
BRANCH             sprint-1/mission-1.84.11
FREEZE_COMMIT      0fe38227f46bc1b851faf24cb014bef20d23490b   (pushed before the replay)

INFLECTION_NORMALIZATION_ASYMMETRY (gate v1.2.0)       ESTABLISHED
GATE_V1_3_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY    true
HISTORICAL_V3_GATE_V1_1_VERDICT                        FAILED  (5 reasons, reproduced exactly)
HISTORICAL_DIAGNOSTIC_GATE_V1_2_VERDICT                FAILED  (1 reason, reproduced exactly)
DIAGNOSTIC_GATE_V1_3_VERDICT                           FAILED  (1 field, 2 findings, both true)
DIAGNOSTIC STAGES 7 / 8 / 9                            NOT_REACHED
EXECUTION_PACKET_V4                                    NOT_CREATED
PRIMARY_OUTCOME                                        V3_DIAGNOSTIC_REVEALED_GENUINE_OUTPUT_SUPPORT_FAILURE
```

## The operator's decisions, carried as data

The nine lines of §0 are carried verbatim in `second_opportunity_gate_v1_3.OPERATOR_DECISION_V1_3`,
and CI gate 77 refuses a copy that is shortened or reworded:

- `FIX_SYMMETRIC_INFLECTION_NORMALIZATION = true`
- `SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT = false`
- `SOURCE_METADATA_MUST_NOT_LICENSE_DOMAIN_ASSERTIONS = true`
- `KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED`
- `KEEP_PROMPT_V1_2_0_UNCHANGED`
- `KEEP_HISTORICAL_GATE_V1_1_0_UNCHANGED`
- `KEEP_FROZEN_GATE_V1_2_0_UNCHANGED`
- `DO_NOT_WHITELIST_THE_V3_ANSWER`
- `DO_NOT_WEAKEN_EVIDENCE_BOUNDARIES`

## §3: the 1.84.10 blocker, reconfirmed before anything was written

Under frozen gate v1.2.0, `statement_classifications[7]`, classified `OBSERVED_OR_EVIDENCE_SUPPORTED`,
is refused with `'tender' appears in no supplied statement`. The condition behind it was checked on its
own:

- on the answer side, v1.2.0's `_spans` folds `tenders` onto the marker `tender`;
- on the support side, the supplied statements carry `Tenders`, which stays the exact token `tenders`,
  and `tender` is not among the supplied tokens.

So the marker `tender` never matches the supplied `tenders`. **`INFLECTION_NORMALIZATION_ASYMMETRY =
ESTABLISHED`**. CI gate 77 re-derives that fact on a synthetic packet at every run, so a later edit to
v1.2.0 that removed it would show.

## Gate v1.3.0

**Versioned beside v1.1.0 and v1.2.0, never over them.**
- `assertion_context.py` and `second_opportunity_gate_v1_2.py` are byte-identical to the v1.2.0
  freeze, and CI gate 75 still validates.
- `guards.py`, `validation.py`, `second_opportunity.py` and `schema_validation.py` are byte-identical
  to bb0f50a.
- Four new modules carry the successor.

| component | v1.2.0 | v1.3.0 |
|---|---|---|
| gate | `second-opportunity-output-gate@1.2.0` | `second-opportunity-output-gate@1.3.0` |
| output schema | `second-opportunity-synthesis-output@1.1.0` | unchanged (`ec789d1b...`) |
| persistence gate | `opportunity-synthesis-persistence-gate@1.2.0` | `opportunity-synthesis-persistence-gate@1.3.0` |
| audit | `opportunity-synthesis-audit@1.3.0` | `opportunity-synthesis-audit@1.4.0` |
| claim guard | `opportunity-claim-guard@1.3.0` | `opportunity-claim-guard@1.4.0` |
| field context policy | `second-opportunity-field-context-policy@1.0.0` | unchanged, the same object |
| support universe | `opportunity-support-universe@1.0.0` | `opportunity-support-universe@2.0.0` |
| trusted context | `second-opportunity-trusted-context@1.0.0` | unchanged |
| source metadata | none | `second-opportunity-source-metadata@1.0.0` |
| lexical inflection | none | `opportunity-lexical-inflection@1.0.0` |
| observed-statement disjunction | none | `observed-statement-disjunction-policy@1.0.0` |

The prompt v1.2.0 (`1677cbe5...`) and the TED representation (`2528a56a...`) did not move.

### One inflection policy, both sides

`lexical_inflection.normalize_token` is the only function in the gate that takes a token apart. Every
comparison between the answer's gated vocabulary and the supplied statements goes through it, on both
sides. It is **not a stemmer**, it adds no dependency and it reads no locale. It covers English noun
number in five written rules:

| rule | matches | produces | example |
|---|---|---|---|
| `REGULAR_IES_PLURAL` | 5+ letters, consonant + `ies` | consonant + `y` | industries -> industry |
| `IE_SINGULAR` | 4+ letters, consonant + `ie` | consonant + `y` | movie -> movy |
| `REGULAR_SSES_PLURAL` | 6+ letters, `sses` | `ss` | weaknesses -> weakness |
| `SSE_SINGULAR` | 5+ letters, `sse` | `ss` | finesse -> finess |
| `REGULAR_S_PLURAL` | 4+ letters, `s` but not `ss`, `us` or `is` | drop the `s` | contracts -> contract |

**Each rule was justified by the gated vocabulary, not added by taste**, as §6 required:

- **`-s`** is the fold that v1.2.0 already applied to the answer. It now applies to the support too.
- **`-ies`**: gated terms end in consonant + `y` (`industry`, `municipality`, `opportunity`,
  `profitability`), and under v1.2.0 the answer's `industries` escaped the marker `industry`.
- **`-sses`**: gated nouns end in `ss` (`weakness`, `willingness`, `fitness`), and under v1.2.0
  `competitor weaknesses` escaped the phrase `competitor weakness`.
- **The two singular rules** exist only so the two plural rules do not split a noun whose singular ends
  in `ie` or `sse` from its own plural (`movie`/`movies`, `finesse`/`finesses`). v1.2.0's answer-side
  fold kept those together.

**What is not covered, and why:**
- **Other `-es` plurals** (after x, ch, sh, z or a single s): no gated term needs them, and each would
  collide with a common singular (`size`/`sizes`, `niche`/`niches`, `axe`/`axes`).
- **Irregular morphology is never guessed**, so `analysis`/`analyses`, `person`/`people` and
  `money`/`monies` stay apart.
- **Derivation is not inflection**, so `market`/`marketing`, `pay`/`payment`, `score`/`scoring` and
  `value`/`valuable` stay apart.
- **A known over-fold is kept and recorded.** A singular that ends in a lone `s` (`news`, `means`) folds
  as if it were a plural, exactly as v1.2.0's answer-side fold already did.

**Verbs stay verbatim.** The one list of gated vocabulary that is made of verb forms is
`SUPPORT_PREDICATES`: `establishes`, `supports`, `evidences` and so on, which a NOT-supported item may
not claim. It is matched form by form, as written. Folding noun number onto it would read the noun
*evidence* as the verb *evidences*, and would refuse a NOT-supported item that merely names support. That
would be a new false refusal, and it is exactly what v1.2.0 did not do.

**§7, the invariant, held by behaviour and not only by name:**
- `ANSWER_MARKER_NORMALIZATION_POLICY == SUPPORT_TOKEN_NORMALIZATION_POLICY ==
  opportunity-lexical-inflection@1.0.0`.
- Both bindings are the same function object.
- CI gate 77 runs every gated term through both sides:
  - **46 markers** and **60 concept phrases**, each supplied and asserted in both of its numbers;
  - each also absent, and each also inside a source's name;
  - result: **0 asymmetries, 0 missed absences, 0 metadata leaks**.
- A change that folds one side and not the other fails there. The probe does exactly that, on each
  side.
- No v1.3.0 module other than `lexical_inflection.py` takes a token apart, and none imports v1.2.0's
  span or classifier functions.

**Stricter in places, weaker nowhere.** Folding both directions means the answer's singular now matches
a gated term that is listed only in the plural: `user` for `users`, `customer` for `customers`,
`competitor` for `competitors`. The answer's `industries` and `competitor weaknesses` are now caught
too. Every such change refuses more, never less.

### Four support origins

The support universe of v1.2.0 had one channel, `SOURCE_STATEMENTS`, and it was one undifferentiated
string. In v1.3.0 the supplied statements are split by origin:

| origin | licenses |
|---|---|
| `SOURCE_CONTENT_STATEMENT` | what a source reported: lexical support for markers, concepts and numbers, under the existing rules only |
| `SOURCE_METADATA_LABEL` | where the data came from: the label's own whole occurrence, read as a name, and nothing else |
| `PACKET_STRUCTURAL_FACT` | ids, families, dimensions, scorability, identity (unchanged, no label moved into it) |
| `TRUSTED_LIMITING_OR_DEFINITIONAL_FACT` | definitional identifiers only (unchanged) |

**The source-metadata policy:**
- **Labels arrive through an explicit channel with no default.** `SourceMetadataContext` is built from
  registry entries, never from an answer or a prompt. For each packet source it holds:
  - the source identifier;
  - the catalog's `canonical_name`, and that name without its trailing qualifier (`X (Y)` also yields
    `X`);
  - each dataset's `resource_id` and name from the compliance record;
  - for each label, the document it came from.
- **A label never becomes content silently.** A packet source with no declaration is refused by name,
  because its statements cannot be split.
- **A name used as a name is a provenance reference.** *"The source is Tenders Electronic Daily."*
  passes (§19). Its words never license anything outside it, whether rearranged, inflected or repeated.
- **A label that IS a gated term never masks.** A provider literally named *Market Demand* cannot be
  told apart from the term.
- **A figure inside a label licenses no number.**

**The publisher-name policy is first class and independent of the V3 answer (§16):**
- `docs/architecture/adr/ADR-040-source-metadata-is-provenance-not-factual-support.md`;
- `docs/data/source-metadata-evidence-boundary-decision-v1.json`: decision owner **OPERATOR**, decision
  type **EVIDENCE_BOUNDARY**, **mathematically derived false**. CI gate 77 re-derives it from the code.

**How "Tenders Electronic Daily" behaves:**
- As a registry label, *Tenders Electronic Daily (EU public procurement)* and *Tenders Electronic Daily*
  name a source.
- Inside a claim statement, it is split out of the content.
- In an answer, as a name, it is a provenance reference.
- Its word *tenders* licenses nothing. *"Tenders occur."* fails unless a source content statement
  independently carries the word, and then it passes: *"Published tenders were observed for CPV class
  9261."* (§14, §18).

### The disjunction policy (§15)

The gate evaluates vocabulary, never the truth of a proposition. A per-marker check is conservative
for a disjunction, because every alternative's gated words must be supported. But it cannot say which
alternative one OBSERVED classification is about. **So an OBSERVED statement that joins alternatives
fails closed**, under `DISJUNCTIVE_OBSERVED_STATEMENT_REQUIRES_EXPLICIT_SUPPORT_POLICY`:

- **What counts:** `or` / `either` outside a denial.
- **What does not count:** alternatives denied or questioned together (*no X or Y*, *not X or Y*,
  *whether X or Y*). Nothing is observed there.
- **Scope:** the statements the answer itself classifies `OBSERVED_OR_EVIDENCE_SUPPORTED`, the one place
  a single label claims a single observation.
- **Prose fields are not refused by this rule.** They are still checked marker by marker.

### Lexical match is not factual support (§13)

`LEXICAL_MATCH_IS_FACTUAL_SUPPORT = False`. A lexical licence answers one question: whether the
vocabulary is present in an eligible support channel. It clears one finding, the marker's. The same
text still goes through every other rule: numbers, forbidden concepts, SCORED, validation words,
certainty markers, request and uncertainty shapes, structural facts. The tests show each of them still
refusing a text whose marker is licensed.

## Frozen before the replay (§20)

`GATE_V1_3_DESIGN_FROZEN_BEFORE_V3_DIAGNOSTIC_REPLAY = true`, and it is a checkable fact:

```
implementation digest   cc3c490268e6f64a0b2107c2fb0c2fe6a1b1c71ab44c353419cd7d86c4485bf3
frozen test file        6d7ad83150323293c78a998f9a880e6abd27e229a576b7b6f4d8fd6b940b80c3
freeze commit           0fe3822, pushed to origin before the replay ran
```

The freeze was checked in three ways:
- CI gate 77 derives the freeze record from the live code and pins both digests in its own source.
- CI gate 78 checks, where history is present, that the freeze commit is an ancestor, carries the
  freeze record, and did not carry the replay record.
- **V3's answer was not read during the design.** The only V3 text the design used is the one statement
  the brief itself quotes. The anti-whitelist check (no six-word run of the historical answer in the
  gate or its tests beyond the brief's own cases) passed first time.

The frozen tests (`test_semantic_gate_v1_3.py`, 159 cases) cover:
- the §6 policy (36 literal cases);
- the §17 inflection matrix;
- the §18 metadata matrix;
- the §19 provenance cases;
- the §13 lexical-match cases;
- the §15 disjunction matrix;
- adversarial names;
- parity with v1.2.0's reading on the brief's own cases from Mission 1.84.10;
- the §12 no-special-case scan;
- versioning.

## §21: the historical gates still reproduce

Before the replay, and again inside it:
- **Gate v1.1.0** reproduces V3's five historical reasons exactly.
- **Gate v1.2.0** reproduces Mission 1.84.10's one diagnostic reason exactly: `'tender' appears in no
  supplied statement`.
- **Nothing historical drifted.** CI gates 75 and 76 still validate, and gate 78 refuses a rewritten
  Mission 1.84.10 replay record by digest.

## The diagnostic replay through v1.3.0 (§22)

`render_second_opportunity_v3_diagnostic_replay_v1_3.py --replay` ran **once**, DIAGNOSTIC_ONLY,
against the freeze commit. **It needed no database.** Its packet is the snapshot Mission 1.84.10
recorded, which CI gate 76 authenticates by rebuilding the approved representation and the rendered
prompt from it alone. The metadata channel was rebuilt from `source-catalog-v1.json` and
`source-compliance-v1.json`. Stages 1 to 9 are the V3 runner's own `validate_execution`, with nothing
swapped but the semantic gate, and a tripwire on the real transport.

| stage | V3 (v1.1.0) | 1.84.10 (v1.2.0) | 1.84.11 (v1.3.0) |
|---|---|---|---|
| `1_transport_success` | PASSED | PASSED | PASSED |
| `2_provider_response_shape` | PASSED | PASSED | PASSED |
| `3_provider_completion` | PASSED | PASSED | PASSED |
| `4_structured_output_parse` | PASSED | PASSED | PASSED |
| `5_schema_validation_v1_1_0` | PASSED | PASSED | PASSED |
| `6_semantic_output_gate` | FAILED, 5 reasons | FAILED, 1 reason | **FAILED, 1 field** |
| `7_evidence_boundary_and_no_distortion` | NOT_REACHED | NOT_REACHED | NOT_REACHED |
| `8_attribution_and_provenance` | NOT_REACHED | NOT_REACHED | NOT_REACHED |
| `9_persistence_eligibility` | NOT_REACHED | NOT_REACHED | NOT_REACHED |
| `10_human_review` | NOT_REACHED | NOT_MANUFACTURED | NOT_MANUFACTURED_DIAGNOSTIC_ONLY |

**Every other field of V3's answer audits clean under v1.3.0.** The one refusal, verbatim:

```
statement_classifications[7].statement audited UNSUPPORTED:
SOURCE_METADATA_LABEL_IS_NOT_FACTUAL_SUPPORT: 'tender' is asserted, and its only supplied occurrence
is inside the source metadata label(s) ['ted-eu:REGISTRY_DISPLAY_NAME:1']. A source's name identifies
where the data came from and does not establish a domain fact, and no source content statement carries
the word (opportunity-lexical-inflection@1.0.0);
DISJUNCTIVE_OBSERVED_STATEMENT_REQUIRES_EXPLICIT_SUPPORT_POLICY: this statement is classified OBSERVED
and joins alternatives with ['or'] outside any denial. One classification cannot say which alternative
the evidence supports, and the gate evaluates no disjunction, so it fails closed
(observed-statement-disjunction-policy@1.0.0)
```

**The exact unsupported proposition (§23, §39):**

> *"Transactions or tenders occur in the bounded scope of CPV class 9261 notices."*,
> classified `OBSERVED_OR_EVIDENCE_SUPPORTED`.

**The refusal is now true, and it names the right reason.**
- **In 1.84.10 the finding was false as worded**, because the word was supplied.
- **In v1.3.0 it says where the word was supplied and why that does not count.** Three of the five
  supplied claim statements open with the publisher's registry name, *Tenders Electronic Daily (EU
  public procurement)*, and that name is the only place the word occurs. The other two name the source
  by its identifier, `ted-eu`. None of the five carries the word in what the source reported: the
  counts, the classes, the amounts.
- **The statement also joins two alternatives under one OBSERVED label.** That would fail closed on its
  own.

**Why this is not another gate bug (§23):**
- The symmetric fold was applied, and it matched: `tenders` in the answer and `Tenders` in the name are
  one form now.
- The finding exists because the operator decided a name is not evidence. It did not come from a
  mismatch the gate introduced.
- The gate refuses the statement for what it asserts. Nothing was weakened to rescue V3, and nothing
  would rescue it without the source content saying so.

## Diagnostic stages 7, 8 and 9

**NOT_REACHED.** The V3 runner stops at the first failing stage, and §24 runs stages 7 to 9 only if
stage 6 passes. They have still not been exercised on V3's answer under any gate. Stage 10 remains
`NOT_MANUFACTURED_DIAGNOSTIC_ONLY`.

## V3 remains historical (§26)

`V3_HISTORICALLY_REJECTED = true`, `V3_CANDIDATE = false`, `V3_HUMAN_REVIEW_PACKET = NOT_PRODUCED`,
`V3_PERSISTABLE = false`, and V3's approval stays consumed. The runner's guard still refuses the V1, V2
and V3 digests before any network, and an unseen digest is not refused. No V1, V2 or V3 packet,
approval, record or response was rewritten, and neither were Mission 1.84.10's freeze and replay
records.

## V4 (§27 to §31)

**Not created.** §27 creates V4 only if stages 6 to 9 all pass under frozen gate v1.3.0, and stage 6
failed. There is no V4 packet, no V4 digest, no V4 approval surface, no request bytes rebuilt and no
cost recomputed. `OPERATOR_EXECUTION_APPROVAL_RECORDED` does not exist for a V4 that does not exist.
The operator decision behind this mission authorised the local semantic-gate work only.

## CI gates 77 and 78

- **Gate 77** (`render_second_opportunity_semantic_gate_v1_3.py`) re-derives the freeze record and the
  evidence-boundary decision. It refuses:
  - a changed implementation or frozen test file;
  - gate v1.2.0 no longer being its own freeze;
  - a moved output schema;
  - the operator's decision or the evidence-boundary decision not carried as given;
  - a second normalizer, or a symmetry matrix with one asymmetry or one metadata leak;
  - unrelated morphology collapsing;
  - a gated term that needs an `-es` rule the policy lacks;
  - a lexical match treated as proof;
  - a thin matrix;
  - a run of the historical answer;
  - a record field the code does not derive.
- **Gate 78** (`render_second_opportunity_v3_diagnostic_replay_v1_3.py`) re-derives the replay from
  Mission 1.84.10's authenticated snapshot. It checks that gates 77 and 76 still validate, and it pins
  Mission 1.84.10's replay record by digest. It refuses:
  - a different freeze commit, or a freeze that did not precede the replay;
  - V3's reasons or v1.2.0's reason no longer reproducing;
  - a metadata channel the registry does not give;
  - a stage, verdict, reason, unsupported proposition or outcome it does not derive;
  - stage 10 manufactured;
  - V3 made a candidate or persistable;
  - a human-review packet;
  - a V4 packet while stage 6 fails.

## Probe (§32)

**195 violations caught, 0 escaped, 28 of 29 positive controls, every file proved restored.** The
caught violations break down as follows:

- 145 refused by the gates' own rules;
- 3 refused by render drift;
- 44 refused by the frozen gate's semantics;
- 2 refused by the replay itself (a second replay, a replay against the pre-freeze commit);
- 1 refused by a crash: the transport tripwire, when a model call was attempted during the replay.

The cases, by family, all refused:

- **The freeze record** (gate 77, 44 cases): the order flags flipped; an allowlist added; `tender`
  special-cased; v1.1.0 or v1.2.0 mutated; the schema, prompt or TED representation changed; the
  decision shortened or reworded so that a source name counts; the asymmetry denied; a derivation rule
  added; market/marketing recorded as collapsing; an NLP dependency or a stemmer; two policies or two
  functions; a second normalizer; the symmetry matrix edited; the metadata origin dropped; labels
  licensing their words; metadata moved into structural facts; undeclared sources read as content; a
  lexical match treated as proof; disjunctions evaluated; a model call or TED bytes counted.
- **The evidence-boundary decision** (gate 77, 13 cases): a source name counting as support, metadata
  licensing domain assertions, an owner other than the operator, a derived decision, a moved ADR.
- **The replay record** (gate 78, 55 cases): V3 made a candidate, persisted, reviewed or unspent; stage
  6 hidden; stages 7 to 9 marked passed without execution; the genuine failure relabelled a gate defect;
  the false v1.2.0 reason restored; the proposition hidden or reworded; V4 created or approved while
  stage 6 fails; v1.1.0's or v1.2.0's reasons changed; a replay dated before the freeze; the metadata
  channel edited; the snapshot tampered with; a model call, provider request or TED bytes counted.
- **History on disk** (9 cases): V3's answer rescued consistently, its reasons trimmed, its approval
  unspent or reused, its packet approved inside; Mission 1.84.10's tender reason changed; V3 made a
  candidate in 1.84.10's record; v1.2.0's order flag flipped.
- **Live code, in a fresh interpreter** (25 cases): v1.2.0 mutated in place with the plural licence
  fold; `guards.py`, the schema, the prompt, the TED serialization or the V3 runner edited; plural
  folding on the answer only and on the support only; broad stemming, market/marketing, pay/payment;
  a source name read as a statement; a publisher label, a dataset title or a provenance label as domain
  evidence, WTP or market demand; "Tenders Electronic Daily" licensing "tenders occur"; metadata moved
  into structural facts; a lexical match treated as proof, by the flag and by skipping every other rule;
  `tender` special-cased; the V3 sentence allowlisted; the disjunction policy disabled; a model call
  during the replay; the replay pointed at the pre-freeze commit.
- **Semantics** (44 cases): 31 answers through the whole gate and 13 audited texts, including every
  metadata case of the brief, a disjunctive OBSERVED statement, `competitor weaknesses` and `several
  industries`, all refused.

**The positive controls:**
- the shipped gates 75 to 78;
- `$comment` and timestamp edits in the freeze and replay records;
- comments in unpinned files;
- regular plural folding in both directions;
- a label supporting a provenance-only proposition;
- independent content supporting the normalized form;
- the source family as a provenance statement;
- the brief's legitimate denials, requests and uncertainties;
- the runner refusing the V1, V2 and V3 digests while an unseen digest is not refused;
- the transport tripwire.

**The one failed control is the probe's own error, not the gate's.** It reworded the `$comment` of the
evidence-boundary decision and expected gate 77 to accept it. Gate 77 refused, because the freeze record
pins that document's text digest: the decision is an input to the freeze, and even its comment cannot
move without a new freeze. It is the same chain by which gate 78 pins the freeze record. The control was
mis-specified, and the refusal is correct. It is reported as a failed control rather than re-run away.

## Accounting (§36)

```
MODEL_CALLS                0
PROVIDER_REQUESTS          0
MESSAGES_API_REQUESTS      0
TED_BYTES_SENT             0
CANONICAL_MUTATIONS        0
Opportunities persisted    0
```

## Canonical state (§33)

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

- `ruff format --check` and `ruff check` are clean over 1056 files, and `mypy` over 207.
- Contracts, catalog and source registry are clean.
- **3853 bare-python tests and 4707 pytest tests**, 13 skipped, with the database unchanged across 29
  tenant tables.
- **244 new tests**: 159 on the gate (the frozen file), 45 on the freeze, 40 on the replay.
- **78 CI gates**, two of them new, all run locally with no failure.

## Outcome and next

**`V3_DIAGNOSTIC_REVEALED_GENUINE_OUTPUT_SUPPORT_FAILURE`.** The same statement also carries
`DISJUNCTIVE_OBSERVED_STATEMENT_REQUIRES_EXPLICIT_SUPPORT_POLICY`. It is recorded, not promoted to the
primary outcome, because the support failure would refuse the statement on its own.

**Stop (§39).** The gate is repaired. It now refuses V3's one remaining statement for a reason that is
true, and nothing else in V3's answer fails it. The facts the operator's next decision rests on, with
nothing recommended:

- **V3 is historical and spent.** A future execution needs a new packet digest, a new approval and an
  answer whose OBSERVED statements assert what the source content says. A name is no longer enough.
- **Stages 7 to 9 are still untested on a real answer under v1.3.0.** Only an answer that passes stage
  6 reaches them.
- **Prompt v1.2.0 says nothing about source names or disjunctions.** Changing that would be a new prompt
  version, and it is the operator's to decide.
- **Disjunctions are refused, not evaluated.** An explicit support policy for them (for example, that
  each alternative must be supported by content) would be a decision, and none was taken here.
- **The ADR index in `docs/architecture/adr/README.md` stops before ADR-036.** ADR-036 to ADR-040 are
  not listed. This mission added ADR-040 and did not rewrite the index.

**Do not execute anything, do not re-execute V3, do not treat its answer as a candidate, and do not
persist Opportunity #2.** Mission 1.84.12 was not started.
