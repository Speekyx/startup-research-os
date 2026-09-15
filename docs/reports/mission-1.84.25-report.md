# Mission 1.84.25: Stage 6 Diagnostic of V10

**`STAGE_6_ROOT_CAUSE_ESTABLISHED_OPERATOR_DECISION_REQUIRED`**

A diagnostic mission only. V10's one request was refused at stage 6 by gate v1.4.0 on two words, and
this mission establishes why, from the retained answer, the frozen code and the frozen policies. It
repaired nothing. It made no provider call, created no packet and no V11, and left V10's verdict as it
was recorded.

- **The two refusals have different causes.** The two words were refused for different reasons, and
  the classification says which.
- **`software` in `observed_need` is a `GATE_DEFECT`.** The clause reader cuts the last item of a list
  off from the leading *Whether* that questions the whole list. It does this because a verb follows that
  item within three tokens. In the detached clause the word stands without its scope, so it reads as
  asserted. The documented policy refuses a word only where it is asserted, keeps a list under its one
  scope, and splits only a coordinated clause with its own subject.
- **`market` in `candidate_intervention_class` is a `GENUINE_OUTPUT_DEFECT`.** The class is one clause
  with no denial, uncertainty or request. *market* is split from *market-observation* because hyphens
  split tokens, and it is asserted. No supplied statement carries it, and the one structural fact that
  contains it, MARKET_ACTIVITY, licenses its canonical phrase whole and no single word of it. Prompt
  v1.6.0 states the class rule; V9 was refused on the same word under v1.5.0.
- **V10 stays rejected whatever the gate defect.** The `market` refusal stands on its own, in another
  field.
- **A synthetic matrix of 39 general cases reproduces the divergence.** It covers the operator's eight
  shapes, controls and minimal pairs, all run through the frozen gate. It finds 10 divergences from the
  documented policy, all of one shape. The smallest is *Whether a need or software exists is unknown.*,
  which is refused, while *Whether software exists is unknown.* passes.
- **A second attempt is not recommended.** Under an unchanged prompt, schema and gate, the evidence
  does not justify another generation attempt, and this mission recommends no V11. Five decisions are
  the operator's.

```
START_COMMIT        91cbb19f12eb408a14f4fbe97e7d7add9999975f  (merged main after PR #168)
BRANCH              sprint-1/mission-1.84.25

PROVIDER_CALLS 0   MODEL_INFERENCES 0   RETRIES 0   PERSISTENCE 0
NEW_EXECUTION_PACKET NO   V11_CREATION NO   OPPORTUNITY_2_CREATION NO
HISTORICAL_VERDICTS_MUTABLE NO   V10_REEXECUTION FORBIDDEN   V10_OUTPUT_REWRITE_OR_REPAIR FORBIDDEN

GATE v1.4.0         eb03899bbf7cc56f51994679dc4514f5c3c7ef63f4b6126aeb19ff18ccb160bb  (unchanged)
CLAUSE READER       assertion_context.py 3afcffc2..., inside gate v1.2.0's 47bbcb45... (unchanged)

observed_need / software                 GATE_DEFECT
candidate_intervention_class / market    GENUINE_OUTPUT_DEFECT

PRIMARY_OUTCOME     STAGE_6_ROOT_CAUSE_ESTABLISHED_OPERATOR_DECISION_REQUIRED
```

## How the diagnosis was run

Four read-only agents worked in parallel. The main agent was the only writer.

| agent | question | method |
|---|---|---|
| A, semantic gate | how the frozen gate reads the two refused words | V10's inputs rebuilt through gate 101's snapshot; the gate's own functions called step by step; minimal variants |
| B, contract and policy | what the frozen contract intends, apart from what the code does | reports, ADRs, module docstrings, frozen tests, the approval, the prompt |
| C, synthetic matrix | whether the behaviour is general, not V10's | the frozen v1.3.0 test fixture, never V10's answer; three fields |
| D, governance | that nothing moved and nothing was called | gates 91, 98, 99, 100 and 101 `--check`; digests; the research database read-only |

No agent wrote a file. Every Python process ran without the credential and with the transport and
`urlopen` tripwired. The database was read with `default_transaction_read_only=on`. The main agent then
reproduced the two refusals and both traces itself before writing anything, and gate 102 re-derives all
of it in CI.

## The two refusals, reproduced

Gate v1.4.0 was run over V10's retained answer, with the packet, trusted context and source-metadata
channel rebuilt from Mission 1.84.10's authenticated snapshot as gate 101 rebuilds them. It returns
exactly the two reasons the execution retained, and no other:

```
observed_need audited UNSUPPORTED: 'software' appears in no source content statement, compared under
  opportunity-lexical-inflection@1.0.0; prior knowledge is not available as factual support (§7)
candidate_intervention_class audited UNSUPPORTED: 'market' appears in no source content statement,
  compared under opportunity-lexical-inflection@1.0.0; prior knowledge is not available as factual
  support (§7)
```

Both come from the same audit path:
- `second_opportunity_gate_v1_4` keeps v1.3.0's semantic reasons;
- `assertion_audit_v1_3.audit_text` reads each field by its disposition;
- `_marker_findings` refuses a marker that no source content statement carries, **and only where it is
  asserted**: `if universe.content_carries(marker) or not is_asserted(text, marker): continue`.

Both refused fields are `SUPPORTED_ASSERTION / FREE`. Neither word is supplied: not by a content
statement, not by a source-metadata label.

## `software`: the list loses its *Whether*

The sentence is *Whether this reflects any underlying need, problem, or software gap is not
established by these statements.* The gate reads it in four steps:

| step | what the code does | where |
|---|---|---|
| clauses | `_CLAUSE_BOUNDARY` matches once, as its `coord` alternative, on `, or ` at 50: an optional comma, `and`/`or`/`so`/`then`, then a lookahead for 1 to 3 tokens and a verb. `software gap is` satisfies it. | `assertion_context.py:229-231` |
| result | clause 0 `whether this reflects any underlying need, problem`; clause 1 `software gap is not established by these statements.` | `_clauses`, `:362-379` |
| state | in clause 1 no marker precedes `software` (`_marker_before`: none) and no negator heads it. The trailing denial does not clear it, because `_SUBJECT_DENIAL` needs the copula immediately after the word, and the head noun `gap` sits between. **ASSERTED** | `_state`, `:434-447`; `:238-247` |
| refusal | asserted, in an asserting field, carried by no content statement | `assertion_audit_v1_3.py:293` |

So the hypothesis in the brief is confirmed. The `, or software gap is ...` construction is split into a
coordinated clause, and that clause loses the leading `Whether`. The regex takes the sentence's main
verb, whose subject is the whole `Whether` clause, for the third list item's own verb.

**Two conditions make the refusal, and the first is the cause.**
1. The split. Without it, `Whether` precedes the word in one clause and the word is UNCERTAIN. The
   same sentence with a single item passes (matrix S5).
2. After the split, nothing in the detached clause clears the word. If the gated word is the head noun,
   the clause's own denial rescues it: *..., or software is not established* passes (L11). As a
   modifier of *gap*, it is not rescued.

**The code knows the split.** `assertion_audit_v1_3.disjunctive_connectives` says v1.2.0's splitter
"also breaks at a comma-less `or` followed by a subject and a verb (`no X or Y were ...`); that is
still one clause here, read under its denial". That correction was made for the disjunction rule
only. The assertion reading still calls v1.2.0's `_clauses`, and no frozen test pins a list item
followed by the sentence's own predicate.

## `market`: an asserted word, supplied nowhere

The class is *An evidence-gathering or market-observation exercise directed at procurement activity
classified under CPV class 9261.*

- **One clause.** The `or` is not followed by a verb within three tokens, so there is no boundary.
- **Tokens.** `[a-z0-9]+` splits `market-observation` into `market` and `observation`. guards.py
  documents this: "Hyphens and slashes split".
- **No scope.** No denial, uncertainty or request applies. **ASSERTED.**
- **No licence.** MARKET_ACTIVITY is declared and supported, and `_mask_dimension_terms` licenses
  exactly its canonical phrase, *market activity*, contiguous. *market-observation* is not that phrase,
  and the word survives the mask. Mission 1.84.10 decided this: "No paraphrase and no single word is
  licensed".
- **No support.** No content statement carries the word; no metadata label does either.

V9's class, *... for contracting-authority or market-intelligence audiences*, was refused by the same
path with the same reason, under prompt v1.5.0.

## What the contract intends

Agent B read the frozen policies apart from the code's behaviour.

- **A word is refused only where it is asserted, in every field, the asserting ones included.**
  - Mission 1.84.10: "A concept is refused when it is ASSERTED. It is not refused when it is denied in
    its own clause, requested as evidence that would be required, framed as an uncertainty, ...".
  - The field policy says `evidence_bound_reasoning_summary` is "asserted reasoning, which may deny".
  - The frozen v1.2.0 test `test_denied_it_passes` requires *The packet does not establish software
    demand.* and *... market size.* to pass in that asserting field. Both carry a gated marker.
  - ADR-040 and the audit code gate the marker check by assertion state.
  - Nothing documented says an asserting field may carry no unsupported word at all.
- **A list stays under its one scope.** The clause reader's docstring says "a plain comma inside a list
  does not break one, so *does not establish need, gap or willingness to pay* stays one denial". A
  clause breaks at "a coordinated clause with its own subject". In V10's sentence, *software gap* is an
  object of *reflects*, not the subject of *is not established*.
- **A trailing denial clears only its subject.** guards.py: "Only `<term> (is|are|was|were|has|have|had)
  (not|never|no)` clears". The principle says a word denied in its own clause is not asserted. For a
  gated word that pre-modifies the denied head noun, these two give different answers. The contract
  does not settle which governs (matrix M1 to M3, left UNDETERMINED).
- **Where the contract is silent:**
  - Oxford commas (they are irrelevant to the behaviour: `,?`);
  - hyphenated compounds (the implementation splits them);
  - a list followed by the sentence's main verb.
- **The prompt is stricter than the gate.**
  - Prompt v1.6.0 says that in each asserting field "every substantive concept that describes the domain
    comes from" the supplied channels, with no denial exception.
  - Its own module says it is "generation guidance and nothing else" and that "the gate is unchanged".
  - A stricter prompt cannot cause a refusal. It is recorded as decision D5.
- **The accepted limitation is the other direction.**
  - V10's approval accepted that the gate "is not a complete natural-language proof system", and that a
    proposition outside its grammar "may theoretically survive". That is under-refusal.
  - The `software` refusal is over-refusal. No record accepts or names over-refusal.

## Classification

| refusal | classification | the other three, and why not |
|---|---|---|
| `observed_need` / *software* | **GATE_DEFECT** | not **GENUINE_OUTPUT_DEFECT**: the answer frames the word as an uncertainty in its own sentence, and the documented policy does not refuse that. Not **PROMPT_GATE_ALIGNMENT_DEFECT**: the refusal comes from the clause reader, not from a form the prompt failed to state. Not **SOURCE_SUPPORT_GAP**: nothing about software is asserted, so no support is missing. |
| `candidate_intervention_class` / *market* | **GENUINE_OUTPUT_DEFECT** | not **GATE_DEFECT**: every step is a documented rule. Not **PROMPT_GATE_ALIGNMENT_DEFECT** (see below). Not **SOURCE_SUPPORT_GAP**: the boundary that leaves the single word unlicensed was decided (1.84.10 §16, §17), and widening it would be a boundary change, not a gap. |

**Why `market` is not a prompt-gate alignment defect.** Prompt v1.6.0 states, in the system region the
model received:
- the class names "the class and only the class, and NAME_THE_CLASS_ONLY does not mean free vocabulary";
- "name a more neutral class grounded in what they do supply";
- "General knowledge of the world is not support";
- that *whether a market exists* is outside what the packet establishes.

It also tells the model to name the class "in terms the supplied statements and the packet's structural
facts already use". It does not say that a dimension name licenses only its whole phrase
(`DIMENSION_NAME_WHOLE_PHRASE_BOUNDARY_STATED = false`). That gap is real. It cannot be shown to have
caused the word: V9 used *market* under v1.5.0, which had no structural-channel sentence at all. It is
recorded as an open observation under decision D3, not as a classification.

## The synthetic matrix

The matrix is 39 general sentences, none of them V10's. The only shared text is the operator's own
cases, and one of them, *Software gap is not established.*, happens to occur inside V10's sentence.
Each sentence was run on the frozen v1.3.0 fixture's good answer, replacing one field:
- `observed_need` (SUPPORTED_ASSERTION);
- `critical_uncertainties[0]` (UNKNOWN_REQUIRES_EVIDENCE);
- `commercial_claims_not_supported[0]` (EXPLICITLY_NOT_SUPPORTED).

No gated word under test is in the fixture's statements; gate 102 checks this. The intended verdict is
the documented policy's for an asserting field, where it gives one.

| group | cases | observed_need | intended | agree |
|---|---|---|---|---|
| asserted controls (A1-A9) | *Software gap is established.*, *The buyers need software.*, *A software gap exists, and it is not established by these statements.*, *The class is a market-analysis service.*, *A software gap is not established, but it probably exists.* ... | all REFUSE | REFUSE | 9 of 9 |
| scoped controls (S1-S13) | *Software gap* denied or questioned in one clause: *Whether a software gap exists is unknown.*, *Whether this reflects a software gap is not established.*, *No evidence establishes a need, problem, or software gap.*, *It is not established whether this reflects a need, problem, or software gap.*, *The packet does not establish need, gap or willingness to pay.* ... | all PASS | PASS | 13 of 13 |
| list under one scope (L1-L14) | a list inside a leading `whether` or denial, its last item followed by a verb | L1-L10 REFUSE, L11-L14 PASS | PASS | **4 of 14** |
| pre-modifier of a denied subject (M1-M3) | *Software gap is not established.*, *Market gap is not established.*, *Underserved segment is not established.* | all REFUSE | UNDETERMINED | not counted |

**The ten divergences (L1-L10) are one shape.**

| case | sentence | observed_need |
|---|---|---|
| L1 | *Whether a need or software exists is unknown.* | REFUSE |
| L2 | *Whether a need or dissatisfaction exists is unknown.* | REFUSE |
| L3 | *Whether this reflects a need, problem, or software gap is not established.* | REFUSE |
| L4 | the same without the Oxford comma | REFUSE |
| L5 | *Whether this reflects a need or software gap is not established.* | REFUSE |
| L6 | *... or software gap is unknown.* | REFUSE |
| L7 | *... or dissatisfaction remains to be seen.* | REFUSE |
| L8 | *... or underserved segment is not established.* | REFUSE |
| L9 | *None of the notices show that a need, problem, or software gap exists.* | REFUSE |
| L10 | *... or competitor weakness is not established.* | REFUSE |

And the four that agree show the boundaries of the defect:
- **L11** (*..., or software is not established*) and **L12** (*..., or market is not established*)
  are split, but the gated word is the head noun, and the detached clause's own denial clears it.
- **L13** (*..., or a gap in software*) and **L14** (*..., or any underlying software gap*) put four
  tokens before the verb, past the `{1,3}` window, so nothing is split.

**The smallest general failing pattern:**

```
refused   Whether a need or software exists is unknown.
passes    Whether software exists is unknown.
```

Put a `whether` or denial marker before a noun list, then `and`/`or` before the last item, then that
item in one to three tokens, then a verb. The last item leaves the marker's scope, and a gated word in it
is asserted, unless it is itself the head noun of a trailing subject-denial.

What matters and what does not:
- The Oxford comma is irrelevant (the comma is optional).
- Two items or three makes no difference.
- *by these statements* makes no difference.
- *any underlying* matters only by the token count before the verb.
- A denial-led list fails the same way as a `whether` list (L9).
- For the forbidden concepts, the split reaches the uncertainty field as well. L2, L7 and L8 are
  refused in `critical_uncertainties`, a field whose items the policy says are never assertions of
  their content. The field frames only the head clause, and the detached item is outside it.

**Secondary observations**, recorded and not classified. None bears on V10.
- A8 and A9 are refused in `commercial_claims_not_supported` with *it says the claim is 'established'*.
  The contrastive re-assertion rule is applied to the predicate word *established*, and the text does
  not say it is established.
- In L10 the same span is read two ways: the phrase *competitor weakness* is the denied subject, and
  the term *competitors*, folded from the modifier, is asserted.
- The uncertainty-shape rule does not count a plain denial (*No software gap is established.*, S2) as
  uncertainty-shaped in `critical_uncertainties`.

## A correction to earlier wording, kept where it was written

Three texts from Mission 1.84.24 describe the `software` refusal as a field-level rule, that a gated
word in a supported-assertion field is refused wherever it stands:
- the V10 record's `semantic_note`: "refuses a substantive word in a supported-assertion field when no
  supplied statement carries it, and it did so here wherever the word stood";
- the Mission 1.84.24 report: "the word stands in an asserted field";
- docs/CLAUDE.md 1.159: "A WORD IN A DENIAL IS STILL A WORD IN AN ASSERTED FIELD".

The documented policy is clause-level assertion. The refusal came from the clause split, not from the
field. The V10 record is pinned and its verdict is immutable, so none of the three was edited. This
report and gate 102's record carry the correction.

## Is another generation attempt justified?

**Not on the current evidence, and no V11 is recommended.**
- **The class vocabulary has not moved.** It named an unsupplied word in both answers that reached
  stage 6: under v1.5.0, which stated the class rule as a proposition, and under v1.6.0, which stated it
  as a surface rule with the neutral fallback.
- **The request form did move, but that says nothing about the class.** It went from 0 of 6 to 7 of 7,
  and two answers establish no rate.
- **The gate would still misread sound answers.** Gate v1.4.0 still refuses a gated word that ends a
  scoped list, so an answer sound under the policy can still be refused at stage 6.
- **An attempt under an unchanged prompt, schema and gate** would test the same class vocabulary against
  the same misreading. Nothing in the repository predicts a different result.

Whether anything changes first, and whether synthesis on this packet continues at all, is the
operator's decision.

## Governance verification

| check | result |
|---|---|
| V10 consumed | record: `EXECUTION_APPROVAL_CONSUMED true`, `FURTHER_CALLS_AUTHORIZED_BY_V10 false` |
| V10 cannot execute again | runner `refuse_if_consumed(5ed6771d...)` → `EXECUTION_APPROVAL_ALREADY_CONSUMED` under a tripwire; gate 101's `--execute` check passes |
| V1 to V10 immutable | all 70 `second-opportunity-synthesis-*` files identical to 91cbb19. 69 are unchanged since the commit that added them; V1's record was closed by its own mission. Gates 91, 98, 99, 100 and 101 `--check` pass and write nothing |
| stages 7 to 10 | NOT_REACHED for V9 and V10; both `EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY` |
| canonical counters | @@COUNTERS@@ |
| Opportunity #2 | does not exist: one row in `research.opportunities` (`06113a8b...`), 2 revisions |
| no provider path | the gate modules import no transport or HTTP module; every process tripwired; no credential in any environment |
| frozen digests | gate v1.4.0 `eb03899b...`, prompt v1.6.0 `a89960ce...`, schema v1.2.0 `7d67bad3...`, packet V10 `5ed6771d...`, approval `5b0090e2...`, response `6a9e5d4d...`, record `981cfb43...`: all unchanged |

## Operator decisions required

1. **D1, successor gate for the list-scope defect.** Authorise, or not, a separate successor-gate
   mission: a gate v1.5.0 beside v1.4.0, in which the last item of a list stays inside the leading
   `whether` or denial that scopes it. It would be frozen and tested on synthetic cases before any
   replay. Constraints:
   - gate v1.4.0 stays byte for byte, and V10's verdict stays as recorded;
   - nothing is whitelisted, and no concept or marker is removed;
   - a conjunct with its own subject (*..., and buyers are willing to pay*) must still split.
2. **D2, a gated pre-modifier of a denied subject** (*Software gap is not established.*). Decide which
   the contract means: the principle, or the bounded subject-denial rule. Either a successor gate
   carries it, or it is recorded as accepted narrowness. Decide it as policy, never from how V10 would
   fare.
3. **D3, the class field.** Decide whether anything changes for `candidate_intervention_class` before
   any further attempt:
   - nothing;
   - a structural constraint on the field (a schema or contract change);
   - more prompt wording, knowing the rule has been stated twice and the word came back twice;
   - or widening the MARKET_ACTIVITY whole-phrase licence, which would widen an evidence boundary.

   The whole-phrase boundary is unstated in the prompt.
4. **D4, whether to attempt again at all.** If synthesis on this packet continues, it needs a new
   packet, digest and explicit approval, after D1 to D3. If not, it stops with V10.
5. **D5, the prompt stricter than the gate.** Keep the prompt's no-exception grounding line, or align
   it, as generation guidance only. The gate is not changed to match the prompt.

## Gate 102

`infrastructure/scripts/render_second_opportunity_stage6_diagnostic_v10.py` and its record and page:
`docs/data/second-opportunity-stage6-diagnostic-v10.json` and `.md`. It makes no production semantic
change and no network call. Its record is fully derived and compared at every run. It refuses:
- the frozen gate no longer returning V10's retained reasons;
- a trace no longer showing `software` split off its `whether` by the `coord` pattern, or `market`
  asserted in one clause and supplied nowhere;
- a classification outside the four categories, not set against the other three, or resting on a
  policy sentence no longer found in its file (14 quotes);
- a matrix whose divergences are not exactly L1 to L10, or whose smallest failing pattern and control
  no longer differ;
- gate v1.4.0, gate v1.2.0 (the clause reader) or the fixture moved;
- prompt v1.6.0 no longer stating the class rule, or v1.5.0 stating what v1.6.0 added;
- V10 not held to gate 101;
- earlier wording it corrects that is no longer where it was written (three quotes);
- a record or page that is not what the diagnosis re-derives.

## Tests, CI gates, probe

```
new tests            43, in test_second_opportunity_stage6_diagnostic_v10.py (one full derivation, tripwired)
bare-python tests    @@BARE@@
pytest               @@PYTEST@@
CI gates             102 (gate 102 added after gate 101), @@GATES@@
ruff, format, mypy   @@LINT@@
probe                15 violations caught, 0 escaped; 2 of 2 positive controls; every file restored and
                     proved by digest; each run in a child with the transport and urlopen tripwired and
                     no credential; 668 s. A first run stopped on a setup error of the probe itself (a
                     quoted sentence spanning a line break) after 6 caught, restored every file, and
                     was fixed and run again in full
provider requests    0        model calls 0        token counts 0        TED bytes 0
canonical mutation   0
```

## Files

```
infrastructure/scripts/render_second_opportunity_stage6_diagnostic_v10.py   new, CI gate 102
docs/data/second-opportunity-stage6-diagnostic-v10.json                     new, derived record
docs/data/second-opportunity-stage6-diagnostic-v10.md                       new, rendered by gate 102
packages/opportunity-engine/python/tests/test_second_opportunity_stage6_diagnostic_v10.py   new
.github/workflows/ci.yml                                                    gate 102 step
PROJECT_MANIFEST.md (1.159), docs/CLAUDE.md (1.160), this report
```

The semantic gate, the clause reader, the schema, the prompt, the strict projection, the runners,
packet V10, its approval, response and record, and every earlier gate are byte-identical.

## Next

**The operator decides, and nothing was started.** V10 stays rejected and spent. A successor gate, a
change to the class field, and any further attempt are each an operator decision (D1 to D5). None of
them may be taken on the strength of how V10 would fare. **Do not re-execute V1 to V10, do not rewrite
or rescue V10's answer, do not create V11 or a packet, do not persist Opportunity #2, and do not modify
gate v1.4.0.** Mission 1.84.26 was not started.
