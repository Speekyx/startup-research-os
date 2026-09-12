# Mission 1.84.8: Output-Constraint Prompt Alignment and Execution Packet V3

**`SECOND_OPPORTUNITY_EXECUTION_PACKET_V3_READY_FOR_OPERATOR_APPROVAL`**

The operator kept the v1.1.0 output schema and gate, kept the 900-character bound, and asked for the
drift between the prompt and the schema to be removed in a general way. Prompt v1.1.0 stated 8 of
the schema's 32 generation-relevant constraints in words. The 900 on
`evidence_bound_reasoning_summary`, the bound V2 was refused on, was one of the 24 it left to the
forced tool's input schema, and nine other narrative lengths were missing with it. **Prompt v1.2.0
states all 32, rendered by one function from the live schema**, and the schema still decides: 900
characters pass, 901 are refused, and nothing is trimmed to fit. Execution packet V3 is V2's call
with that prompt and nothing else changed. Its digest is `c7b8553d...` and no approval is recorded.
**Zero model calls, zero provider requests, zero TED bytes, zero canonical mutation.**

```
START_COMMIT       02f6f42e6d04c0dcc6ae8aafcd44370e55bcc0be
BRANCH             sprint-1/mission-1.84.8

OPERATOR DECISION  KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED
                   KEEP_OUTPUT_GATE_V1_1_0_UNCHANGED
                   DO_NOT_RAISE_EVIDENCE_BOUND_REASONING_SUMMARY_MAX_LENGTH
                   CORRECT_PROMPT_SCHEMA_CONSTRAINT_ALIGNMENT
                   statement sha256 ce84b610853144936088842119ccde2280e55815bbeca88fdc0cbf803ddbf413

PRIMARY_OUTCOME    SECOND_OPPORTUNITY_EXECUTION_PACKET_V3_READY_FOR_OPERATOR_APPROVAL
```

## The operator's decision, and what it is not

The operator's words are recorded verbatim in
`second-opportunity-output-constraint-alignment-v1.json`, 20 lines, with a digest. The decision is
about how the prompt communicates the contract, and the record says what it does not do:
`V2_ANSWER_RESCUED false`, `V2_VALUE_USED_TO_CHOOSE_A_MAXIMUM false`,
`AUTHORISES_A_SCHEMA_CHANGE false`, `AUTHORISES_AN_INFERENCE false`.

V2's answer was used to establish exactly one thing: *that a schema violation occurred, on one
field, against a bound the v1.1.0 prompt did not state in words.* It chose no length, no count, no
field order, no requiredness rule, no semantic allowance and no Evidence interpretation. **One
rejected generation is not a contract-design distribution.** Gate 72 now holds that sentence word
for word, because the first probe run showed a second line could be appended beside it.

## V2, reconfirmed from what it retained

| fact | value |
|---|---|
| outcome | `EXECUTION_SCHEMA_REJECTED_NO_RETRY` |
| approval consumed | **true** |
| provider requests / model calls / retries / fallbacks | 1 / 1 / 0 / 0 |
| stop reason | `tool_use` |
| usage | 8939 input, 3914 output, 0 thinking |
| cost | 0.057018 |
| failed stage | `5_schema_validation_v1_1_0` |
| violation | `evidence_bound_reasoning_summary: 1113 characters exceeds maxLength 900` |
| stages 6 to 10 | NOT_REACHED |
| canonical persistence | false |

Gate 72 recomputes every row from V2's record, response and packet: the violation through the live
v1.1.0 validator over the retained answer, the cost from the reported usage at the held price. It
refuses a record that differs. **It also pins the history itself.** Prompts v1 and v2, packets V1
and V2, V2's approval, both execution records and V2's response must hash to what Mission 1.84.7
left, and the rejected answer may carry no human-review packet, no persisted Opportunity and no
candidate marker. Both rules came from the second probe run.

## The contract, unchanged

```
schema                 second-opportunity-synthesis-output@1.1.0
                       ec789d1be7d525bf6e498bf61e8a0596ac4582e24e8b45073b3f9ac1cca8b988
schema changed         false
gate                   second-opportunity-output-gate@1.1.0
gate changed           false

evidence_bound_reasoning_summary.maxLength   900
source                 the live schema's properties.evidence_bound_reasoning_summary.maxLength,
                       inherited byte-identically from Mission 1.31's base schema
                       through v1.0.0 and v1.1.0
critical_uncertainties[] maxLength           500   (kept)
commercial claim items maxLength             300   (kept)
```

**The 1113 characters chose nothing.** No new maximum was proposed, recommended or recorded.

## The audit: every constraint, classified

The live schema carries **75** constraints. The mission classified each one by a rule, not case by
case, and gate 72 recomputes the classification from the schema.

| rule | class | why |
|---|---|---|
| `object_required` | A must be explicit | omitting a field fails validation |
| `object_closed` | A | a field outside the contract fails validation |
| `closed_choice` | A | a closed choice whose selection carries meaning |
| `composed_length` | A | the model composes the text and must control its length while writing |
| `sentinel` | A | the schema's own description names an exact string |
| `chosen_cardinality` | A | the model chooses how many elements to write |
| `type` | B provided by the tool schema | the rendered wording already implies the type |
| `identity_grammar` | B | a regex is not useful prose; the block says to copy supplied ids verbatim |
| `vocabulary_cardinality` | C redundant | the vocabulary is stated and is no larger than the bound |
| `copied_length` | D validator only | the value is copied from the packet, never composed |
| `annotation` | D | the validator does not assert it; the pattern beside it does the work |

**A 32, B 36, C 2, D 5.** "Explicit" means stated as a limit in a field stanza of the system
region. The same rule is applied to v1.1.0 and to v1.2.0.

### The 32 generation-relevant constraints

| constraint | value | v1.1.0 | v1.2.0 |
|---|---|---|---|
| `<root>` required | all 20 fields | not stated | stated |
| `<root>` additionalProperties | false | not stated | stated |
| `decision` enum | FORM_HYPOTHESIS, INSUFFICIENT_EVIDENCE | stated | stated |
| `subject` maxLength | 80 | not stated | stated |
| `target_actor_if_supported` maxLength | 200 | not stated | stated |
| `target_actor_if_supported` sentinel | UNKNOWN_NOT_SUPPORTED | not stated | stated |
| `observed_need` maxLength | 400 | not stated | stated |
| `candidate_intervention_class` maxLength | 300 | not stated | stated |
| `hypothesis_statement` maxLength | 600 | not stated | stated |
| `supported_dimensions[]` enum | 14 dimension names | stated | stated |
| `unsupported_dimensions[]` enum | 14 dimension names | stated | stated |
| `supporting_evidence_ids` maxItems | 20 | not stated | stated |
| `supporting_claim_ids` maxItems | 20 | not stated | stated |
| `source_families` maxItems | 10 | not stated | stated |
| `independence_status` maxLength | 300 | not stated | stated |
| `reliability_status` maxLength | 300 | not stated | stated |
| **`evidence_bound_reasoning_summary` maxLength** | **900** | **not stated** | **stated** |
| `critical_uncertainties` maxItems | 12 | not stated | stated |
| `critical_uncertainties[]` minLength | 1 | not stated | stated |
| `critical_uncertainties[]` maxLength | 500 | stated | stated |
| `commercial_claims_supported` maxItems | 8 | not stated | stated |
| `commercial_claims_supported[]` maxLength | 300 | stated | stated |
| `commercial_claims_not_supported` maxItems | 14 | not stated | stated |
| `commercial_claims_not_supported[]` maxLength | 300 | stated | stated |
| `recommended_next_evidence` maxItems | 8 | not stated | stated |
| `recommended_next_evidence[]` maxLength | 300 | not stated | stated |
| `confidence_classification` enum | EXPLORATORY | stated | stated |
| `statement_classifications` maxItems | 24 | not stated | stated |
| `statement_classifications[]` required | statement, classification | not stated | stated |
| `statement_classifications[]` additionalProperties | false | not stated | stated |
| `statement_classifications[].statement` maxLength | 300 | not stated | stated |
| `statement_classifications[].classification` enum | 3 classifications | stated | stated |

**Explicit in v1.1.0: 8. Missing from v1.1.0: 24.**

**`WERE_OTHER_SCHEMA_BOUNDS_MISSING_FROM_PROMPT = true`.** Beside the 900, v1.1.0 omitted 18 other
bounds. Nine of them are narrative lengths: `subject` 80, `target_actor_if_supported` 200,
`observed_need` 400, `candidate_intervention_class` 300, `hypothesis_statement` 600,
`independence_status` 300, `reliability_status` 300, `recommended_next_evidence[]` 300 and
`statement_classifications[].statement` 300. The other nine are eight maxItems and one minLength.
It also omitted five other generation constraints: the 20-field required set, the refusal of any
other field, the `UNKNOWN_NOT_SUPPORTED` sentinel, and the required, closed shape of a classified
statement. **Adding only the 900 would have left every one of these in place.**

**Cardinality.** Every array's maximum is stated, except where the schema itself makes it
non-binding: an array drawn from a closed vocabulary no larger than its maxItems cannot exceed it
without a duplicate, and the vocabulary is stated. The identifier arrays are stated too, although
this packet supplies fewer ids than their maximum, because that margin is a fact about one packet
and not about the contract.

## How v1.2.0 derives them

`render_output_constraints(schema, notes)` in
`packages/opportunity-engine/python/sros_opportunity/output_constraints.py`,
`output-constraint-renderer@1.0.0`, is the only source of the block:

- **Inputs:** the live schema object and the explicit rendering policy.
- **Not inputs:** model output, execution history, any response artifact, any record.
- **Deterministic:** fields in the schema's own required order, adjacent identical stanzas merged.
- **Notes carry guidance that is not a limit, and may carry no digit.** Every number the model reads
  therefore comes from the schema.

Gate 72 reads the renderer and the v1.2.0 section of `second_opportunity.py` as syntax trees. The
renderer imports nothing that could reach a file, record or model, and its only integer constants
are 0 and 1. The v1.2.0 section carries no numeric literal, and its block is assigned from exactly
one call, `render_output_constraints(SECOND_OPPORTUNITY_OUTPUT_SCHEMA_V1_1, OUTPUT_CONSTRAINT_NOTES_V1_2)`.
A `PROMPT_MAX_REASONING_LENGTH = 900` beside the schema is refused by name.

**The drift property, recomputed by the gate:**

- Each of the 32 class-A constraints, mutated in a copy of the schema, moved the rendered prompt.
- Each of the 10 constraints of another class, mutated within its class, moved nothing.
- Both vocabulary bounds, pushed below their vocabulary, became binding and appeared.
- Rewording all 10 field descriptions changed nothing.
- The 33 type constraints were not mutated, because changing a type turns the field into a
  different contract.

### The block v1.2.0 carries

```
THE OUTPUT CONTRACT IS BOUNDED, AND AN ANSWER THAT EXCEEDS A BOUND IS REFUSED RATHER THAN TRIMMED.

Every limit below is read from the output schema the answer is validated against. Lengths are counted in characters.

The answer is one object with exactly these 20 fields, every one required, and no other field.

  decision
    exactly one of: FORM_HYPOTHESIS, INSUFFICIENT_EVIDENCE

  subject
    at most 80 characters

  target_actor_if_supported
    at most 200 characters
    The narrowest actor the statements support, or the exact string UNKNOWN_NOT_SUPPORTED if they name none.

  observed_need
    at most 400 characters

  candidate_intervention_class
    at most 300 characters

  hypothesis_statement
    at most 600 characters

  supported_dimensions, unsupported_dimensions
    exactly these names, spelled exactly: PROBLEM_OR_NEED, RECURRENCE_OR_FREQUENCY, ECONOMIC_VALUE, WILLINGNESS_TO_PAY, BUYER_OR_BUDGET_EXISTENCE, MARKET_ACTIVITY, TREND_OR_CHANGE, SOLUTION_GAP, SOLUTION_DISSATISFACTION, COMPETITIVE_SUPPLY, AUDIENCE_OR_USAGE, DISTRIBUTION_SIGNAL, REGULATORY_OR_STRUCTURAL_DRIVER, FEASIBILITY_SIGNAL

  supporting_evidence_ids, supporting_claim_ids
    at most 20 elements
    the ids supplied to you, copied verbatim. No prose, no description, no partial id.

  source_families
    at most 10 elements
    the family names supplied to you as a packet fact, copied verbatim.

  independence_status, reliability_status
    at most 300 characters

  evidence_bound_reasoning_summary
    at most 900 characters

  critical_uncertainties
    at most 12 elements, each from 1 to 500 characters
    One uncertainty per element.

  commercial_claims_supported
    at most 8 elements, each at most 300 characters
    One proposition per element; the reasoning belongs in evidence_bound_reasoning_summary.

  commercial_claims_not_supported
    at most 14 elements, each at most 300 characters
    One proposition per element; the reasoning belongs in evidence_bound_reasoning_summary.

  recommended_next_evidence
    at most 8 elements, each at most 300 characters

  confidence_classification
    exactly one of: EXPLORATORY

  statement_classifications
    at most 24 elements, each an object with exactly these 2 fields, every one required, and no other field:
      statement: at most 300 characters
      classification: exactly one of: OBSERVED_OR_EVIDENCE_SUPPORTED, HYPOTHESIS_TO_VALIDATE, UNKNOWN_REQUIRES_EVIDENCE

These are limits on FORM, never on how much you may refuse to conclude. A shorter answer that
names more unknowns is a better answer here than a longer one that names fewer.
```

## Prompt v1.1.0 to v1.2.0

```
old   second-opportunity-synthesis-prompt@1.1.0
      2f60c61f63cda410b9f60e3eafd9676f983e7ff0220245c03c88136511ac7e82
new   second-opportunity-synthesis-prompt@1.2.0
      1677cbe53e83e644fa15e5492cf88e3ec578538351924f2b3a504e27f3a0878d

system region            f44f1d22... -> dd418805...
output-contract block    cebe0967673a27b55296248f8549bc0dcd35b961d3826e3a116ef4dc801da24f
trusted context, TED statements, task   byte-identical to v1.1.0
```

The semantic diff (`second-opportunity-synthesis-prompt-v3.md`): the first 92 lines, the v1.0.0
system text, are unchanged, and the first changed line is 96. Four lines are removed, the v1.1.0
stanzas for the 500 and the 300 limits, whose limits and guidance are restated. Fifty-one lines are
added. **The change is confined to the output-contract block.** Research, evidence-boundary,
refusal, commercial-claim and confidence semantics are unchanged. The human-review requirement lives
in the persistence policy, which is unchanged. v1.0.0 and v1.1.0 still render the bytes they sent.

## The schema still decides

Synthetic answers against the live validator:

| case | answer | result |
|---|---|---|
| A | summary 899 characters | passes |
| B | summary 900 characters | passes |
| C | summary 901 characters | `evidence_bound_reasoning_summary: 901 characters exceeds maxLength 900` |
| D | one uncertainty of 500 characters | passes |
| E | one uncertainty of 501 characters | refused |
| F | one commercial statement of 300 characters | passes |
| G | one commercial statement of 301 characters | refused |
| H | 13 uncertainties; 25 classified statements | refused, `items exceeds maxItems` |

**Stating a bound does not enforce it; the validator does.** No post-processing is possible in the
V3 runner either, and gate 73 checks that by reading the runner as a syntax tree:

- there is no slice anywhere in it;
- the parsed answer is bound once;
- nothing is written into it or deleted from it;
- no method other than a read is called on it, or on any part of it.

The runner's own tests hand it a 901-character summary and it is refused, which no trimming could
allow.

## Execution packet V3

```
id / version            SECOND-OPPORTUNITY-SYNTH-EXEC-V3 v3
digest                  c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2
predecessor             V2 d27f2896..., EXECUTION_SCHEMA_REJECTED_NO_RETRY, approval consumed
consumed packets        V1 570657e1..., V2 d27f2896...

representation          2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72, 3604 characters
provider / route        anthropic, POST https://api.anthropic.com/v1/messages, synchronous, no beta header
routes not used         MESSAGE_BATCHES_BETA, anthropic-claude-subscription
model                   claude-sonnet-5 (STRONG_MODEL)
thinking                DISABLED, {"type": "disabled"}
MAX_OUTPUT_TOKENS       128000, the operator's selection; not based on V2's 3914
timeout                 60.0 s, unchanged since V1; V2's 35.5 s changed nothing
calls                   1; retries 0; no fallback, continuation or repair model
prompt                  1.2.0 1677cbe5..., rendered by output-constraint-renderer@1.0.0
schema / gate           v1.1.0 ec789d1b... / v1.1.0, neither changed
post-processing         truncation, item dropping, rewriting, auto-summary, splitting,
                        normalisation: all false
completion policy       tool_use complete; max_tokens and model_context_window_exceeded fail
                        closed at stage 3, before any parse; refusal and anything else fail closed
stages                  the ten, in V2's order
persistence             only after deterministic acceptance and a separate human approval
```

### Cost, recomputed

```
request body            22124 characters = V2's 20623 + 1501 from the longer system region
input token estimate    12825  (22124 / 2.1565 x 1.25, rounded up; V2's method, unchanged)
worst-case input cost   0.02565
worst-case output cost  1.28     (all 128000 output tokens)
worst-case total cost   1.30565
execution cost ceiling  1.30565  (the worst case itself; no headroom policy exists)
V2's ceiling            1.303908; +0.001742, x1.0013, all of it input
pricing                 anthropic-published-2026-09-02, 0.002 input / 0.01 output per 1000 tokens
```

V2 estimated 11954 input tokens and used 8939, so the held method covered its actual input and is
unchanged. V2's 3914 output tokens do not size V3's envelope. **A worst case is a bound computed
before the call and is not what a call costs.**

### Approval

```
OPERATOR_EXECUTION_APPROVAL_RECORDED   false
NEW_APPROVAL_REQUIRED                  true
PREVIOUS_APPROVAL_REUSABLE             false
```

An approval lives beside the packet, in `second-opportunity-synthesis-execution-approval-v3.json`,
which does not exist. The operator's decision to align the prompt is not an approval to execute it,
and V2's approval is spent.

## Retention, verified without a provider

The V3 runner carries V2's retention and its post-call fail-safe unchanged. Ten terminal paths are
verified against synthetic transports:

- success
- a provider output-limit stop
- a timeout
- a provider refusal
- an unsupported stop reason
- a parse failure
- a schema failure
- a semantic failure
- a provenance failure
- a human-review-ready success

Eight properties are verified the same way:

- usage retained
- request id retained
- digests retained
- terminal outcome retained
- a volunteered reasoning block stripped
- a credential shape redacted
- no fixture constructs the real transport
- the fail-safe keeps the bytes when judging fails

Gate 73 refuses a packet naming a test that does not exist.

## Guards, before any socket

```
V1's digest       refused   EXECUTION_APPROVAL_ALREADY_CONSUMED
V2's digest       refused   EXECUTION_APPROVAL_ALREADY_CONSUMED
an unseen digest  permitted
V3's digest       OPERATOR_APPROVAL_NOT_RECORDED
```

The dry verification, run with a tripwire on the real transport's constructor, which never fired:

```
01_EXECUTION_PACKET_SHA256          c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2
03_V1 / V2 / V3_APPROVAL_CONSUMED   True / True / False
04_REPRESENTATION                   2528a56a..., 3604 characters
05_PROMPT_SHA256                    1677cbe53e83e644fa15e5492cf88e3ec578538351924f2b3a504e27f3a0878d
05_UNSTATED_GENERATION_CONSTRAINTS  0
06_OUTPUT_SCHEMA_SHA256             ec789d1b...
07_PROVIDER_POSTURE                 APPROVED
08_TED_EXTERNAL_MODEL_TRANSMISSION  PERMITTED_WITH_CONDITIONS, live packet gate AVAILABLE
09_REQUEST                          thinking {'type': 'disabled'}, max_tokens 128000, 22124 characters
11_WORST_CASE_CALL_COST             1.30565
12_ALL_BOUND_FIELDS_MATCH           True
13_RETENTION_READY                  True
OPERATOR_APPROVAL                   OPERATOR_APPROVAL_NOT_RECORDED
verified. Nothing sent. An approval naming this digest is required to execute.
```

The runner's drift check is the renderer's own rule over the exact text it would send: it finds 0
unstated constraints in v1.2.0 and 24 in v1.1.0.

## Gates 72 and 73

**Gate 72**, `render_second_opportunity_output_constraint_alignment.py --check`, recomputes the
alignment rather than reading it:

- the operator's words against their digest;
- the V2 facts from what V2 retained, and the history against its digests;
- the contract against the live schema;
- the renderer and the v1.2.0 section, as syntax trees;
- the inventory and the classification from the schema;
- the drift property, by mutating the schema;
- the post-processing prohibitions;
- the prompt document against the live render;
- the accounting.

**Gate 73**, `render_second_opportunity_execution_packet_v3.py --check`, recomputes the packet:

- the digest over the bound fields;
- the predecessors and their spent approvals;
- the prompt against the alignment;
- the contract and the representation;
- the route, the thinking and the envelope;
- the completion policy against V2's;
- the calls and the timeout;
- the cost, from the rebuilt body and the held price;
- the boundaries against the tests that verify them;
- the accounting;
- the single call site and the absence of post-processing;
- the runner's pinned values and its guards.

## Probe

**197 violations caught, 0 escaped, 18 of 18 positive controls, every file proved
restored**, and both gates passing afterwards in process, in a fresh interpreter and under
`--check`. 194 were refused by the check written for them and 3 by render drift,
exactly the three hand-edited pages.

The record cases (165) edit on disk the alignment record, the prompt document, packet V3, an
approval for V3, V2's record, response, approval and packet, V1's packet and record, and prompts v1
and v2. Each packet edit re-binds the packet's digest and lets the runner's pinned digest follow
it, so the content check decides. The code cases (29, plus 2 controls) edit live code and run the whole gate in a
fresh interpreter started with `-B`. They cover:

- the schema: the 900 raised so V2 would pass, the summary made optional, a research sentence
  reworded;
- the prompt module: the classification requirement softened, 900 hard-coded beside the schema,
  the block written by hand, v1.1.0's block reused;
- the renderer: a bound written into it, a `json` import, narrative lengths dropped, only the
  failed field rendered;
- the V3 runner: a retry loop, a continuation call, blindness to V2's record, refusing every
  digest, the drift check disabled, a truncation, a rewrite, an item dropped, a field deleted, a
  summary through `update`, a statement split, schema after semantics, another model, 3914
  output tokens;
- V2's runner with its guard disabled, and an adapter that no longer reads `tool_use` as
  complete.

Every item of section 32's list is among them: 900 raised to fit V2, 1200 chosen because V2
returned 1113, 1113 truncated to 900, V2's answer summarised, the field made optional, semantic
detail reduced, 900 hard-coded, the prompt still omitting 900, the schema moved under an unchanged
prompt and the reverse, only the failed field audited, V2's answer treated as a candidate, V2's
approval reused, V2's consumption reset, another model, the batch route, the subscription route,
thinking enabled, `max_tokens` moved from 128000, a retry, a continuation, the TED representation
changed, a model call, a provider request, a canonical mutation, V3 marked approved.

The controls:

- the shipped records validate;
- the schema is unchanged;
- the renderer states 900 and the other narrative bounds;
- a schema fixture moved to 950 moves the rendering;
- 900 characters pass and 901 fail;
- V1's and V2's guards refuse their digests;
- V3's unseen digest awaits approval;
- the dry runner verifies and stops;
- no real transport is constructed;
- a note reworded in any of the three records binds nothing;
- a later mission's approval naming V3 is accepted;
- a comment or a docstring edit in live code passes.

**The probe found three holes in this mission's own gates, over three runs.**

1. **First run.** `V2_OUTPUT_USE` accepted an appended line: *a maxLength of 1200 from V2's 1113
   characters* sat beside the refusals without contradicting them. Gate 72 now requires that block
   word for word and refuses any other key.
2. **Second run.** Neither gate read V2's own history for a promotion. The rejected answer could be
   marked a candidate in V2's response, or given a human-review packet in V2's record, and both
   gates passed. Gate 72 and gate 73 now refuse both by rule. Gate 72 also pins every historical
   record by digest, because section 2 says none of them is ever rewritten.
3. **Third run.** Nothing escaped.

## Accounting

```
model calls              0
provider requests        0
Messages API requests    0
token-count requests     0
TED bytes sent           0
documentation fetches    0
canonical mutations      0
Opportunities created    0
credential values read   0
```

Nothing was sent to Anthropic, and the new prompt was not tested against it.

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

Counted before any work on the branch and again after the final pytest run.

## Verification

`ruff format --check` and `ruff check` clean over 1028 files. `mypy` clean over 201 files.
Contracts, catalog and source registry clean.

**3853 bare-python tests. 4170 pytest tests**, 13 skipped, with the database unchanged across
29 tenant tables. **214 new tests**: 92 on the renderer and gate 72, 75 on gate 73, 47 on the V3
runner. **73 CI gates**, two new: gate 72 (the prompt states every generation-relevant bound the
live schema enforces) and gate 73 (packet V3 is V2's call with the aligned prompt, and matches the
live code).

## Outcome and next

**`SECOND_OPPORTUNITY_EXECUTION_PACKET_V3_READY_FOR_OPERATOR_APPROVAL`.**

**Next is one operator decision, and it is not a mission's to take.** Approving
`SECOND-OPPORTUNITY-SYNTH-EXEC-V3` v3 by its digest
`c7b8553d540332163b6f2fa4d63c82467680d79cee2b7d5988cc7c4d61f554b2`, recorded by a later mission
beside the packet in `second-opportunity-synthesis-execution-approval-v3.json`, authorises exactly
one request through `run_second_opportunity_execution_v3.py --execute`:

- the synchronous route, with thinking disabled at 128000 and prompt v1.2.0;
- the ten ordered stages;
- an Opportunity hypothesis persisted only after deterministic acceptance and a separate human
  approval.

**Do not execute V3 without that approval, do not approve it on the operator's behalf, do not reuse
V1's or V2's approval, and do not persist Opportunity #2.** Mission 1.84.9 was not started.
