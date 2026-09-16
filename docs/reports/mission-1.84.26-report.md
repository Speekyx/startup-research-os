# Mission 1.84.26: Semantic Gate V1.5.0, Assertion-Scope Repairs D1 and D2

**`SEMANTIC_GATE_V1_5_0_D1_D2_IMPLEMENTED_DIVERGENCE_LIMITED_TO_AUTHORISED_REPAIRS`**

The operator authorised two repairs to the assertion scope that Mission 1.84.25 diagnosed, and nothing
else. This mission built them as a successor gate beside the frozen one.

- **D1: a scoped list keeps its scope.** Under a leading *whether* or denial, the last item of a noun
  list is no longer cut off because the sentence's predicate follows it.
  - *Whether a need or software exists is unknown.* now passes.
  - *No evidence establishes software demand, and buyers are willing to pay.* still splits and still
    fails.
- **D2: a modifier inside a denied subject is not asserted.** A gated word that pre-modifies the head of
  an explicitly denied subject noun phrase is no longer read as asserted.
  - *Software gap is not established.* now passes.
  - *…, but software demand probably exists.*, *…, but the market clearly needs a solution.* and
    *…, it exists.* still fail.
- **What the differential shows.** 131 cases ran through both gates.
  - Every divergence is attributed to D1, to D2, or to both.
  - The successor asserts nothing that v1.4.0 did not.
  - It passes nothing the policy refuses.
  - The sweep of every frozen gate-test sentence changes no reading.
- **V10 stays rejected.** Under v1.5.0 it loses its `software` refusal and keeps `market`, so it is no
  candidate for review or persistence. Its record is untouched, and so is V9's.

```
START_COMMIT        5b6417f71318e660436668b62a8039fb3490d19a  (merged main after PR #169)
BRANCH              sprint-1/mission-1.84.26

PROVIDER_CALLS 0   MODEL_INFERENCES 0   TOKEN_COUNTS 0   RETRIES 0   PERSISTENCE 0
NEW_EXECUTION_PACKET NO   V11_CREATION NO   OPPORTUNITY_2_CREATION NO

GATE v1.4.0          eb03899bbf7cc56f51994679dc4514f5c3c7ef63f4b6126aeb19ff18ccb160bb  (unchanged)
GATE v1.5.0          b188ba4c2cfee92fe56d4bda376d69f280e63a39efde13b4c80e14d96975d7df
FROZEN TEST FILE     test_semantic_gate_v1_5.py  f45344d9636fa1132c9f69a08ae90c5cb42ca71659846fa81d80362b858eebf7
ASSERTION SCOPE      second-opportunity-assertion-scope@1.0.0

V10 under v1.5.0     refused on 'market' alone; not eligible, not for review, not for persistence
```

## How the work was divided

Four read-only agents ran in parallel. The main agent was the only writer.

| agent | task | what it delivered |
|---|---|---|
| A, D1 design | strategies to tell a noun list followed by its enclosing predicate from a coordinated clause with its own subject | three strategies, prototyped inline on 59 labelled sentences; the recommended one, "scope saturation", with its failure modes |
| B, D2 design | the smallest grammatical rule over a denied subject noun phrase | the one-modifier-slot rule with a narrow existence-denial ending, prototyped on 52 sentences |
| C, matrix | a successor matrix from Mission 1.84.25's 39 cases | 130 cases, each intended verdict derived from the policy (131 with N104, added by the main agent) |
| D, governance | everything that must not move, and everything a new module can break | every digest pin recomputed; every package-wide scan listed; the safe route for a V9/V10 replay |

No agent wrote a file. Every process ran without the credential, with the transport and `urlopen`
tripwired.

## The design

### Versioned, beside history

Gate v1.4.0 calls v1.3.0, which audits through v1.2.0's clause reader. Nothing in that chain was
edited. Three new modules compose the successor:

| module | what it is |
|---|---|
| `assertion_scope_v1_5.py` | the successor reading: `scoped_clauses` (D1) and `scoped_state` (D2), plus a reading loop that takes the splitter and state reader as arguments |
| `assertion_audit_v1_5.py` | the v1.3.0 audit re-bound to that reading, and nothing else |
| `second_opportunity_gate_v1_5.py` | gate v1.3.0's evaluator, reading structure against schema v1.2.0 as gate v1.4.0 does |

**The audit is re-bound, not rewritten.** The six v1.3.0 functions that read assertion state were
copied by script from v1.3.0's own source segments:
- the concept, score and marker findings;
- `audit_text` and `audit_output`;
- the persistence gate.

Gate 103 requires each one to be v1.3.0's syntax tree with only three renames: the persistence gate's
name and two component versions. The evaluator is v1.3.0's tree with five declared renames. The masks,
the support universe, the inflection policy, the request and uncertainty shapes and the disjunction rule
are v1.3.0's objects, imported by identity. That gives two guarantees:
- **Where the two readings agree, the reasons are gate v1.4.0's, in its order.**
- **The reading loop is a faithful seam.** Run over v1.2.0's own splitter and state reader, it
  reproduces v1.3.0's `classify` exactly: 842 readings, 0 differences.

**Deliberately unchanged.** The disjunction rule for OBSERVED statements and the request and
uncertainty shapes still use v1.2.0's boundaries. D1 and D2 are decisions about assertion scope, not
about what counts as a disjunction or a shape.

### D1: a scoped list keeps its scope

The splitter walks v1.2.0's own boundary matches. At a coordinated-clause boundary only, it vetoes the
split on positive evidence of a list, and every other boundary is v1.2.0's. It keeps one clause only
when all of these hold:

1. **A scope anchor opens the span.** One of:
   - a clause-initial `whether` (a subject phrase awaiting the sentence's predicate);
   - a clause-initial `no`, `none of`, `neither` or `nothing`;
   - a later `whether`;
   - a later `that` or `if` after a denial.
2. **Every comma item is a bare noun**: an optional determiner and exactly one word, not a verb,
   pronoun or negator.
3. **The conjunct is a short noun phrase.** What follows the conjunction, up to the verb v1.2.0's pattern
   found, is one to three words: no pronoun, no negator, no verb (an infinitive such as *to pay* is
   allowed).
4. **The anchored head has not yet had its predicate.**
   - **After a clause-initial `whether`:** no known verb, or exactly one known verb followed by the noun
     phrase the list continues, with the sentence's closing predicate still to come. The rule refuses a
     head the lexicon cannot read.
   - **After any other anchor:** a bare noun, an optional determiner and one word, like every other item.
   - **A lone `, and` or `, or` with no list before it** is always a clause of its own.

The verb test over-counts on purpose: an unknown `-ed` or `-s` word counts as a verb. A list that looks
like a clause splits, which is v1.2.0's reading, and v1.2.0 refuses.

**The operator's invariant, both ways:**

| sentence | v1.4.0 | v1.5.0 |
|---|---|---|
| *Whether a need or software exists is unknown.* | REFUSE | PASS |
| *Whether this reflects a need, problem, or software gap is not established.* | REFUSE | PASS |
| *Whether this reflects a need, problem or software gap is not established.* | REFUSE | PASS |
| *None of the notices show that a need, problem, or software gap exists.* | REFUSE | PASS |
| *No evidence establishes a need, problem, or software gap.* | PASS | PASS |
| *No evidence establishes software demand, and buyers are willing to pay.* | REFUSE | REFUSE |
| *Whether a need exists or software is sold is unknown.* | REFUSE | REFUSE |
| *Whether a need exists is unknown, and software demand exists.* | REFUSE | REFUSE |

**The seventh row was a choice.** Agent A read it as one uncertainty; Agent C read it as a proposition
with its own subject. The operator authorised noun lists only, so it splits and refuses.

### D2: a modifier inside a denied subject

In the successor, a gated word that v1.2.0 reads as ASSERTED becomes DENIED only when all of these hold:

1. **The subject noun phrase opens the clause.** An optional determiner (`a`, `an`, `the`, `any`,
   `this`, `these`, `such`) is allowed.
2. **The phrase is plain words.** Its words are joined by single spaces (a hyphenated compound counts as
   one word), and none of them is a closed-class word: no preposition, conjunction, pronoun, auxiliary,
   hedge or predicating verb.
3. **The head is followed at once by a denial of existence or establishment**:
   - `is/are/remains not established|known|shown…`
   - `is/are unknown|unclear|absent…`
   - `has not been established`
   - `cannot be shown`
   - `does not exist`
   - `: not established`

   `is not large` or `have no budget` do not count, because they say something of a subject that exists.
4. **The gated span fills the one modifier slot**: one word, or exactly the gated phrase.
5. **The answer does not predicate of that subject again.** The rule does not apply when the denial is
   followed:
   - in the same clause, by a pronoun and a verb (*…, it exists*);
   - in the next clause, after any boundary, by a re-predication that is neither a further denial nor a
     remark about evidence (*…, and they are probably large*).

   v1.2.0 re-asserts only after a contrast. For what D2 clears, every boundary counts, so the repair
   never reaches further than v1.2.0 already did.

| sentence | v1.4.0 | v1.5.0 |
|---|---|---|
| *Software gap is not established.* | REFUSE | PASS |
| *Market gap is not established.* / *Underserved segment is not established.* | REFUSE | PASS |
| *The software gap is unknown.* / *A software gap cannot be established from these notices.* | REFUSE | PASS |
| *Software gap is not established, but software demand probably exists.* | REFUSE | REFUSE |
| *No evidence establishes software demand, but buyers are willing to pay.* | REFUSE | REFUSE |
| *Software gap is not established, but the market clearly needs a solution.* | REFUSE | REFUSE, on *market* |
| *Software gap is not established, it exists.* | REFUSE | REFUSE |
| *Software gap is not established, and they are probably large.* | REFUSE | REFUSE |
| *Software gap is not large.* / *Software buyers have no budget.* | REFUSE | REFUSE |
| *A software gap that buyers report is not established.* | REFUSE | REFUSE |

### Alternatives rejected

- **D1, list shape only** (Agent A's S2): it never asks whether the denial's clause already had its
  verb, so *No evidence establishes demand, a need, and buyers are willing to pay.* read *buyers* as
  denied. Five fail-opens.
- **D1, "the tail closes the scope"** (S3): no fail-open, but it repairs V10's own shape and leaves 12
  general over-refusals. It is the invariant for one sentence, not in general.
- **D1, pronoun-led clauses only**: `buyers are` and `software demand exists` are not pronoun-led, so a
  genuine clause would merge.
- **D1, S1 as first recommended**: *No need, people spend, and software exists.* merged. Items are
  therefore one word with an optional determiner.
- **D2, two modifier slots**: *Buyers say gap is not established.* would pass, because *say* cannot be
  told from a noun without a word list.
- **D2, v1.2.0's broad subject-denial ending**: *Software buyers have no budget.* and *Software gap is
  not large.* would pass.
- **D2, "a later `not` clears earlier vocabulary"**: forbidden by the operator.
- **Composition by re-executing v1.3.0's source in a new namespace**: rejected for re-bound copies with a
  syntax-tree proof, which reviewers and mypy can read.
- **Changing the disjunction or shape rules to use the new boundaries**: rejected as a divergence
  neither decision authorises.

**Found during the build, not on V10:**
- *Whether a need exists or software is sold is unknown.* merged under an early draft, which a
  proposition with its own subject must not do.
- *…, it exists* and *…, and they are probably large* passed under an early D2.
- *remains to be seen*, `none of … that`, `willingness to pay` and `underserved` exposed over-refusals
  in the early drafts.

Every one came from the synthetic matrix and was fixed before any record was pinned.

## The differential matrix

131 cases: Mission 1.84.25's 39, verbatim, 91 designed by Agent C, and N104, added when a check of this report found it. They ran on the frozen v1.3.0
fixture, in `observed_need` (in `candidate_intervention_class` for the class cases). The two secondary
fields, `critical_uncertainties` and `commercial_claims_not_supported`, were read at the field audit.

| group | cases |
|---|---|
| LIST_UNDER_ONE_SCOPE | 34 |
| PREMODIFIER_OF_A_DENIED_SUBJECT | 15 |
| SCOPED_CONTROL | 14 |
| ASSERTED_CONTROL | 13 |
| CONTRASTIVE_CONTINUATION | 11 |
| MALICIOUS_NEAR_MATCH | 12 |
| GENUINE_NEW_SUBJECT | 9 |
| CLASS_FIELD | 9 |
| PRONOUN_SUBJECT | 6 |
| COORDINATED_PREDICATE | 4 |
| RELATIVE_OR_NESTED | 4 |

```
AS_INTENDED_UNCHANGED                 81
REPAIRED (REFUSE -> PASS)             46
RESIDUAL_OVER_REFUSAL                  4   N96, N25, N28, N30 (v1.4.0's refusing verdict kept)
REASON_ONLY_CHANGES                    7   N51, N68, N99, N100, N84, N85, N93 (a word cleared, still refused)
SECONDARY FIELD CHANGES                9   critical_uncertainties: L2, L7, L8, N3, N4, N5, N8, N15, N98
DIVERGENCES BY ATTRIBUTION            A 23   B 24   A+B 6
UNATTRIBUTED DIVERGENCES               0
ASSERTIONS ADDED BY THE SUCCESSOR      0
POLICY REFUSALS PASSED BY v1.5.0       0
GENUINE ASSERTIONS STILL REFUSED      44
GENUINE COORDINATED CLAUSES SPLIT      9   the closing proposition still its own clause, word for word
CONTRASTIVE RE-ASSERTIONS REFUSED      8
```

**How a divergence is attributed.** Each case is read four ways:
- v1.2.0's splitter and state reader;
- D1's splitter with v1.2.0's state reader;
- v1.2.0's splitter with D2's state reader;
- both.

A divergence is A if D1 alone clears the word, B if D2 alone does. Gate 103 refuses a case when:
- the successor diverges and neither repair explains it;
- any reading asserts a word that v1.4.0 did not;
- the successor adds a finding;
- a reason outside the audit moves;
- a verdict moves in a case whose class is NONE;
- a case the policy refuses passes.

**The secondary-field changes are Agent C's intended set exactly.** In `critical_uncertainties`, the
field frames only the head clause; D1 keeps a scoped list's last item inside it. The concept findings
run there, the marker findings do not. `commercial_claims_not_supported` moved nowhere.

**The four residual over-refusals** keep v1.4.0's refusing verdict, the safe direction:
- **N96**, *No evidence establishes a need or software gap exists.*: no `that`, so the list has no anchor.
- **N25**, *Customer willingness to pay is not established.*: `to` is a closed-class word inside the
  subject.
- **N28**, *Software supply does not appear in these statements.*: `does not appear` is not an existence
  denial.
- **N30**, *A gap in software supply is not established.*: a prepositional modifier is outside the one
  slot.

## The sweep

Every string in the frozen gate test files for v1.2.0, v1.3.0 and v1.4.0, and in the census fixtures, was
split into sentences. The 148 sentences of three words or more that carry a gated word were each read by
both readers:

```
readings changed 0      clause lists changed 0      unattributed 0      assertions added 0
```

No sentence the earlier gates were built and tested on reads differently under v1.5.0.

## V9 and V10, diagnostically

The replay goes directly through the evaluators, as Agent D established:
- **Inputs**: gate 101's authenticated snapshot, V10's source metadata and the trusted context. V9 and
  V10 share every semantic input; only the prompt digest differs, and the gate does not read it.
- **Runners bypassed**: the V9 and V10 runners bind v1.4.0 by name, and were not used.
- **Stage tables**: not written.

| | V9 | V10 |
|---|---|---|
| historical outcome | `EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY` | `EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY` |
| record, response, approval | unchanged; gate 98 validates | unchanged; gate 101 validates |
| v1.4.0 reproduces the retained reasons | yes, 7 | yes, 2 |
| v1.5.0 would refuse with | the same 7 | 1: `candidate_intervention_class` *market* |
| v1.5.0 would remove | nothing | `observed_need` *software* |
| v1.5.0 would persist | no | no |
| eligible / human-review / persistence candidate | - | no / no / no |

**Chronology, stated plainly.** V9's and V10's retained answers were run through an early draft once,
to check the brief's required outcome for V10. No rule was changed on the strength of either answer,
and no V9 or V10 sentence is special-cased: every later change came from a synthetic case named above.

## Immutable history

| artifact | digest |
|---|---|
| gate v1.4.0 (gate 87) | `eb03899b...`, recomputed |
| gate v1.3.0 (gate 77) | `cc3c4902...`, recomputed |
| gate v1.2.0 (gate 75), clause reader `3afcffc2...` | `47bbcb45...`, recomputed |
| gate 102's record, page and script | `dfc9fde4...`, `bbd267d8...`, `1862a75f...` |
| V10 response / record / approval | `6a9e5d4d...` / `981cfb43...` / `5b0090e2...` |
| V9 response / record / approval | `f129e8ed...` / `6b2eeba7...` / `86f73a61...` |
| packet V10 digest, prompt v1.6.0, schema v1.2.0 | `5ed6771d...`, `a89960ce...`, `7d67bad3...` |

Gates 91, 98, 99, 100, 101 and 102 all pass unchanged. No V11 artifact and no human-review packet exists.

## Governance verification

| check | result |
|---|---|
| V10 consumed, cannot run again | gate 101: runner refuses V10's digest before any transport |
| V1 to V10 immutable | gates 91, 98 and 101; the digests above |
| stages 7 to 10 | NOT_REACHED for V9 and V10, untouched |
| canonical counters | unchanged, read-only, before and after the full verification: RawRecords 325, NormalizedRecords 325, Signals 60, Claims 91, ClaimRevisions 92, Evidence 112, ReliabilityAssessments 4, EvidenceIndependenceGroups 0, Opportunities 1, OpportunityRevisions 2, OpportunityEvidenceLinks 14, Embeddings 0, Scores absent, SourceReviews 71 |
| Opportunity #2 | does not exist |
| no provider path | the successor modules import no network or NLP module (gate 103 parses them); every derivation runs under gate 76's transport tripwire and a `urlopen` tripwire |
| package-wide scans (Agent D) | no ranking-ban name, no 900/720 literal, no forbidden import, no `v11` file name |

## Residual risks

1. **Inherited, not introduced.** A continuation after `, and` that re-predicates through a pronoun still
   does not re-assert a word that is itself the denied subject: *Software is not established, and it is
   probably large.* passes under v1.4.0 and v1.5.0 alike. v1.2.0's documented rule reads a reversal only
   after a contrast. D2 closes this for the modifiers it clears; the head noun is outside D1 and D2.
2. **A bounded grammar.**
   - **Found and closed.** Checking this report's own examples found *No staff bid or buyers are willing
     to pay.* merging, because *bid* is a verb the lexicon does not know. After a denial or a
     complementizer, the list's first item must now be a bare noun, like every other item. The sentence
     refuses again and is matrix case N104.
   - **What stays open.** A verb the lexicon does not know can still sit in a sentence-initial `whether`
     head. There the whole phrase is still read under `whether`, which is uncertainty, not assertion.
     The lexicon, the closed-class list and the existence-denial list are frozen data inside the gate's
     digest. This is the residual limitation the operator accepted for v1.4.0, in a new place.
3. **Over-refusals left by design:**
   - plural nouns in a `whether` head;
   - a comma-free list with no `that`;
   - a prepositional or `to` phrase inside a denied subject;
   - `does not appear`;
   - a `whether` subject made of two propositions;
   - `is not yet established`, which v1.2.0 splits at `yet`.
4. **Shapes and disjunctions keep v1.2.0's boundaries.** An OBSERVED statement written as a scoped list
   is still refused by the disjunction rule.

## Gate 103, tests, probe

`infrastructure/scripts/render_second_opportunity_semantic_gate_v1_5.py` (CI gate 103), its record
`docs/data/second-opportunity-output-gate-v1.5-freeze-v1.json` and its page. It pins:
- the old gate digests, the successor digest and the frozen test file;
- the old clause reader and gate 102's diagnosis;
- the re-binding syntax trees;
- the matrix and its authorised divergence set;
- the sweep and the seam;
- V9's and V10's historical immutability;
- V10 still refused on `market` under v1.5.0;
- the absence of network access.

```
new tests            198: 162 in test_semantic_gate_v1_5.py (frozen), 36 in test_second_opportunity_semantic_gate_v1_5_freeze.py
bare-python tests    3877, across 9 packages
pytest               6940 passed, 13 skipped, across 9 packages; the database unchanged by the run
CI gates             103, all passing locally
ruff, format, mypy   clean
probe                18 violations caught, 0 escaped, 0 setup errors; 2 of 2 positive controls; every file restored
                     and proved by digest; 5 cases re-freeze the pinned digest after breaking a rule
                     (D1 head, D2 re-predication guard, whether head, a re-bound audit function, D2
                     existence denial), each caught by the matrix or the syntax-tree proof; 1183 s
provider requests 0   model calls 0   token counts 0   TED bytes 0   canonical mutation 0
```

## Files

```
packages/opportunity-engine/python/sros_opportunity/assertion_scope_v1_5.py            new
packages/opportunity-engine/python/sros_opportunity/assertion_audit_v1_5.py            new
packages/opportunity-engine/python/sros_opportunity/second_opportunity_gate_v1_5.py    new
packages/opportunity-engine/python/tests/test_semantic_gate_v1_5.py                    new, frozen
packages/opportunity-engine/python/tests/test_second_opportunity_semantic_gate_v1_5_freeze.py   new
infrastructure/scripts/render_second_opportunity_semantic_gate_v1_5.py                 new, CI gate 103
docs/data/second-opportunity-output-gate-v1.5-freeze-v1.json                           new
docs/data/second-opportunity-output-gate-v1.5-freeze-v1.md                             new
.github/workflows/ci.yml                                                               gate 103 step
PROJECT_MANIFEST.md (1.160), docs/CLAUDE.md (1.161), this report
```

No existing module, schema, prompt, projection, runner, packet, approval, response, record or gate was
edited.

## Remaining operator decisions

- **D3, the class field.** Decide whether anything changes for `candidate_intervention_class` before any
  further attempt. V10 is still refused on *market* there.
- **D4, whether to attempt again.** Decide whether second-opportunity synthesis on this packet continues
  at all. If it does, it needs a new packet, digest and approval, and a decision on which gate it binds.
  Gate v1.5.0 exists and binds nothing yet.
- **D5, the prompt stricter than the gate.** Keep prompt v1.6.0's no-exception grounding line, or align
  it, as generation guidance only.
- **An observation for the operator, not a decision taken.** Residual risk 1 is a gap in v1.2.0's
  documented re-assertion rule that neither D1 nor D2 authorised touching.

**Mission 1.84.27 was not started.** No class-field redesign, no prompt change, no V11, no provider call,
no Opportunity #2.
