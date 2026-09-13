# Mission 1.84.12: Semantic-Policy Prompt Alignment, Stages 6 to 9 Preflight and Execution Packet V4

**`SECOND_OPPORTUNITY_EXECUTION_PACKET_V4_READY_FOR_OPERATOR_APPROVAL`**

The operator kept schema v1.1.0 and semantic gate v1.3.0 unchanged. They asked for the prompt to state
the generation-relevant rules of that gate, above all two:
- a source's name is provenance, not evidence;
- an OBSERVED statement is atomic and directly supported, so it never joins alternatives.

They also asked for stages 6 to 9 to be proved with the real machinery before any further call is
prepared. **Nothing was done to make V3 pass.** V3 was not replayed, not whitelisted and not used to
render a word.

**Prompt v1.3.0 now states every class-A rule of the unchanged gate.** Those rules are rendered from
the gate's first-class policy objects. The approved TED representation does not move.

**The V4 runner's stages 6 to 9 were run over synthetic answers**, with gate v1.3.0, the provenance
reading and the canonical `OpportunityHypothesis` constructor, and nothing stubbed:
- a valid answer reaches stage 9;
- each failure stops at its own stage.

**Execution packet V4 is frozen and unapproved.** No model was called.

```
START_COMMIT                        d796f4f118ddf32cf490efe180b41cffc7d387f6
BRANCH                              sprint-1/mission-1.84.12

SEMANTIC_GATE_CHANGED               false  (second-opportunity-output-gate@1.3.0, cc3c4902...)
OUTPUT_SCHEMA_CHANGED               false  (second-opportunity-synthesis-output@1.1.0, ec789d1b...)
PROMPT_V1_2_CHANGED                 false  (1677cbe5...)
PROMPT_V1_3_SHA256                  a62fa218ab04e7da5b050ec40dcf2450c749dafd34262fe8c83e9fbc040acc5a
SEMANTIC RULE CENSUS                53 rules: A 30, B 12, C 4, D 7
UNSTATED CLASS-A RULES              prompt v1.2.0: 17    prompt v1.3.0: 0
REPRESENTATION_SHA256               2528a56a... (3604 characters, unchanged)
STAGES 6 TO 9, SYNTHETIC            DETERMINISTIC_STAGE_6_TO_9_PATH_READY (not evidence)
EXECUTION_PACKET_V4_SHA256          7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b
EXECUTION_COST_CEILING_V4           1.312398
OPERATOR_EXECUTION_APPROVAL_RECORDED false
PRIMARY_OUTCOME                     SECOND_OPPORTUNITY_EXECUTION_PACKET_V4_READY_FOR_OPERATOR_APPROVAL
```

## The operator's decisions, carried as data (§0)

The ten lines of §0 are carried verbatim in
`semantic_generation_rules.OPERATOR_DECISION_SEMANTIC_PROMPT_ALIGNMENT`. The alignment record carries
them, packet V4 binds them in its digest, and CI gates 79 and 81 refuse a copy that is shortened or
reworded:

- `KEEP_OUTPUT_SCHEMA_V1_1_0_UNCHANGED`
- `KEEP_SEMANTIC_GATE_V1_3_0_UNCHANGED`
- `DO_NOT_REPAIR_GATE_TO_RESCUE_V3`
- `DO_NOT_WHITELIST_V3`
- `DO_NOT_TREAT_SOURCE_METADATA_AS_FACTUAL_SUPPORT`
- `ALIGN_THE_PROMPT_WITH_GENERATION_RELEVANT_SEMANTIC_GATE_RULES`
- `OBSERVED_STATEMENTS_MUST_BE_ATOMIC_AND_DIRECTLY_SUPPORTED`
- `OBSERVED_DISJUNCTIONS_MUST_BE_SPLIT_OR_DOWNCLASSIFIED`
- `SOURCE_NAME_OR_PUBLISHER_LABEL_COUNTS_AS_FACTUAL_SUPPORT = false`
- `SOURCE_METADATA_MUST_NOT_LICENSE_DOMAIN_ASSERTIONS = true`

## History, unchanged and reconfirmed (§2, §3)

**Gate 79 pins fifteen merged artifacts by their text digest**, and a single edited byte refuses it:
- V1's and V2's packets and records;
- V3's packet, approval, record and response;
- prompt v1.2.0's record;
- Mission 1.84.10's replay record;
- the v1.2.0 and v1.3.0 freeze records;
- the v1.3.0 replay record;
- the source-metadata decision;
- ADR-040.

**The facts this mission rests on are read back from those records**, not restated:

| fact | value |
|---|---|
| gate v1.1.0 on V3 | 5 reasons |
| gate v1.2.0 on V3 | 1 reason, on the term `tender` |
| gate v1.3.0 on V3 | 1 failed field, `statement_classifications[7].statement` |
| its findings | `DISJUNCTIVE_OBSERVED_STATEMENT_REQUIRES_EXPLICIT_SUPPORT_POLICY`, `SOURCE_METADATA_LABEL_IS_NOT_FACTUAL_SUPPORT` |
| every other field under v1.3.0 | passes |
| V3 | historically rejected, not a candidate, not persistable, no human-review packet, approval consumed |

`V3_REPLAYED = false`, `V3_WHITELISTED = false`, `V3_TEXT_USED_TO_RENDER = false`. The historical
sentence is used in one place only: the exposure check, which proves it is **absent** from the prompt.

## What did not move (§4, §5, §16)

- **Gate v1.3.0 is byte-identical.** Its implementation digest is still
  `cc3c490268e6f64a0b2107c2fb0c2fe6a1b1c71ab44c353419cd7d86c4485bf3`, and CI gate 77 still validates.
  `SEMANTIC_GATE_CHANGED = false`.
- **Schema v1.1.0** is still `ec789d1b...`. `OUTPUT_SCHEMA_CHANGED = false`.
- **Prompt v1.2.0** is still `1677cbe5...`. `second_opportunity.py` was not opened for writing, and
  prompt v1.3.0 is a new module beside it.

## The census of the gate's semantic rules (§6 to §8)

`second-opportunity-semantic-rule-census@1.0.0` lists **53 deterministic rules** of gate v1.3.0. Each
one records:
- its component, fields and disposition;
- what it accepts and refuses;
- whether the model controls it;
- whether prompt v1.2.0 states it, quoting the exact v1.2.0 text where it does;
- its class and its enforcement;
- the canonical source of its policy;
- its instruction, and the refusal signature by which a gate refusal is attributed to it.

| class | meaning | rules |
|---|---|---|
| A | `MUST_BE_EXPLICIT_IN_PROMPT` | 30 (13 stated by v1.2.0, **17 not**) |
| B | `STRUCTURAL_AND_ALREADY_EXPRESSED_BY_OUTPUT_CONTRACT` | 12 |
| C | `VALIDATOR_ONLY_NOT_USEFUL_AS_GENERATION_PROSE` | 4 |
| D | `INTERNAL_SAFETY_RULE_NOT_TO_BE_EXPOSED_AS_AN_EVASION_RECIPE` | 7 |

Enforcement:
- `GATE_ENFORCED` 38;
- `GATE_MECHANISM` 14;
- `INSTRUCTION_BEYOND_THE_GATE` 1: `OBSERVED_IS_ATOMIC_AND_DIRECTLY_SUPPORTED`, which the prompt states
  and the gate cannot check.

**The census is complete, and CI proves it both ways.**
- **Every refusal site is mapped.** Every place in the gate's modules that can refuse is mapped to a
  census rule by its (module, function, line), pinned by the implementation digest: **46 sites, 46
  mapped, 0 unmapped**. An enforced rule that no site produces refuses the gate.
- **Every refusal is claimed exactly once.** **41 synthetic fixtures** drive the real gate. Each
  refusal they produce, with audit findings split by field, is claimed by exactly one rule signature:
  - 53 claimed, 0 unclaimed, 0 claimed twice;
  - all 38 enforced rules reached.

**The 17 class-A rules prompt v1.2.0 left unstated:**
- the non-empty lists: `NEXT_EVIDENCE_NOT_EMPTY`, `CLASSIFICATIONS_NOT_EMPTY`;
- `SOMETHING_REMAINS_UNKNOWN`;
- `SUBJECT_IS_THE_PACKET_IDENTITY`;
- the citations: at least one Evidence and one Claim, each Evidence cited with its Claim;
- `SUPPORTED_AND_UNSUPPORTED_DISJOINT`;
- how a field's text is read: `FIELD_SHAPE_KEPT`, `FIELD_TEXT_READ_BY_ITS_DISPOSITION`;
- `ADDED_CONCEPTS_NOT_ASSERTED`;
- the two source-name rules;
- `OBSERVED_DISJUNCTION_FAILS_CLOSED`;
- `NOTHING_PROMOTED_TO_A_CONCLUSION`;
- `NOT_SUPPORTED_ITEM_NEVER_CLAIMS_SUPPORT`;
- `OBSERVED_IS_ATOMIC_AND_DIRECTLY_SUPPORTED`.

**Class D is named and never rendered.** Its seven rules cover:
- the inflection policy;
- the verbatim support predicates;
- the clause-scoped denial reading;
- the request and uncertainty patterns;
- the gated vocabulary lists;
- the label matching order;
- the disjunction boundary reading.

None of their phrase lists, regular expressions or normaliser rules reaches the prompt. The propositions
they enforce are rendered as propositions.

## The renderer (§9, §15)

`render_semantic_generation_rules` reads one object, `SemanticGenerationPolicy`, built from the gate's
own first-class objects:
- `SECOND_OPPORTUNITY_FIELD_POLICY`;
- the classification dispositions;
- the forbidden concepts;
- the transformation names;
- the source-metadata decision;
- the observed-statement disjunction policy;
- the census.

**It reads no answer, no execution history and no source text.** It refuses a digit, so every number
the model reads comes from the schema or the packet. It states every rule as a proposition about what
the answer may assert. The policy digest is `e5bf9a9c...`; the block is 91 lines, `7f37fab4...`.

**Drift is checked both ways.**
- Each of the **10 class-A mutations** moves the rendered block: census instruction, classification
  label and meaning, an added concept, a concept's definition, the disjunction connectives,
  disposition wording, a field's disposition, and the two metadata rules.
- **None of the 9 class-D mutations** moves it: certainty, denial and external-knowledge markers,
  concept phrases, forbidden terms, inflection rules, support predicates, validation words, and the
  mechanism rationale.

The structure was sufficient, so `SEMANTIC_PROMPT_POLICY_SURFACE_REQUIRES_ARCHITECTURE_DECISION` did
not arise.

## Source names are provenance (§10, §13, §14)

The system region states the rule generally:
- a publisher name, source name, registry display name, dataset title, provider label or provenance
  label identifies where data came from;
- it may support a statement about provenance, naming the source by its whole label;
- it never supports a domain proposition, a number or a forbidden concept through anything inside it.

**The model can tell a name from content.** Prompt v1.3.0 adds a `SOURCE NAMES` section to the trusted
context, listing the registry labels that occur, whole, in this packet's supplied statements:

```
"ted-eu"                                              provenance label
"Tenders Electronic Daily (EU public procurement)"   registry display name
"Tenders Electronic Daily"                            source name
"notices/eforms-contract-and-award"                   provenance label
```

- **Each string is the registry's own and already occurs in the approved representation**, so the
  section adds no source content. `SOURCE_ORIGIN_VISIBLE_TO_MODEL = true`, and
  `SOURCE_ORIGIN_NOT_VISIBLE_ENOUGH_TO_MODEL` did not arise.
- **A packet source with no declared names is refused by name**, because its statements cannot be
  split.
- **The representation did not move**: `2528a56a...`, 3604 characters.
  `APPROVED_TED_EGRESS_REPRESENTATION_CHANGED` did not arise.
- **The system region names no publisher, never contains "Tenders Electronic Daily", never names V3
  and never contains the word `tender`.** It is identical for the synthetic packet and for TED.

## Observed statements and alternatives (§11, §12)

The prompt says, as propositions:
- an item classified `OBSERVED_OR_EVIDENCE_SUPPORTED` states exactly one proposition, and a source
  content statement states that proposition itself;
- sharing words with a supplied statement is not support;
- such an item never joins alternatives with "or" or "either ... or";
- **each alternative is written as its own item, or the joined statement is classified
  `HYPOTHESIS_TO_VALIDATE` or `UNKNOWN_REQUIRES_EVIDENCE`**;
- incomplete support is never OBSERVED.

**"or" is not banned globally.** The rule concerns OBSERVED items only. Alternatives denied together,
and every other field, may use the word in its ordinary sense. Gate 79 checks the stated connectives
against the frozen detector: both are detected when joining alternatives, and neither when denied
together.

## Prompt v1.3.0 (§16, §17, §18)

```
system    = prompt v1.2.0's system region + "\n" + the semantic block + "\n"
trusted   = prompt v1.2.0's trusted context + "\n\n" + SOURCE NAMES
untrusted = prompt v1.2.0's, unchanged (the TED statements)
task      = prompt v1.2.0's, unchanged
```

The semantic diff, derived by gate 79:

| region | added | removed |
|---|---|---|
| system | 85 lines | 0 |
| trusted context | 11 lines | 0 |
| untrusted | none | none |
| task | none | none |

**Proved unchanged:**
- the TED content;
- the trusted Evidence and Claim listing;
- the task;
- the schema-constraint block;
- the commercial boundaries;
- the confidence paragraph.

v1.2.0's system region and trusted context are byte-identical prefixes. Prompt v1.2.0 stated all 30
generation-relevant schema bounds, and so does v1.3.0.

**`UNSTATED_GENERATION_RELEVANT_SEMANTIC_RULES = 0`.**
- A rule v1.2.0 stated is found by its exact quoted text.
- Any other class-A rule is found by its rendered lines, in order, inside the system region.
- The same check finds 17 in v1.2.0.
- The V4 runner runs this check before any request and refuses on drift.

## The seven compliance cases (§19)

| case | what the prompt now says | gate v1.3.0 |
|---|---|---|
| A | a source name containing a domain word never yields an OBSERVED fact of that word | the word inside the name: **passes the gate**; a gated word inside the name: refused |
| B | an atomic OBSERVED statement a source content statement establishes | passes |
| C | an OBSERVED statement never joins alternatives | refused |
| D | two statements rather than one joined statement | passes |
| E | incomplete support gives HYPOTHESIS_TO_VALIDATE or UNKNOWN_REQUIRES_EVIDENCE | both pass |
| F | a publisher's name may appear, whole, as provenance | passes |
| G | a forbidden concept may appear as not supported or unknown, never as observed | observed: refused; not supported: passes |

**Case A is recorded honestly.** "Contracts occur." under a source named *Contracts Weekly* passes the
gate:
- `contract` is not gated vocabulary, and the gate audits vocabulary, not propositions;
- the prompt states the rule, and it is the one rule enforced by instruction only
  (`INSTRUCTION_BEYOND_THE_GATE`);
- the human review at stage 10 is what would catch it.

The gated-word variant, where a gated term occurs only inside a name, is refused.

## Stages 6 to 9, preflight (§21 to §23)

**Gate 80 runs the V4 runner's own `validate_execution` over synthetic responses, with the real
machinery and nothing stubbed:**
- gate v1.3.0, which the runner does not let anyone replace;
- the real trusted context and metadata channel;
- the real provenance reading;
- the real `OpportunityHypothesis` constructor;
- a tripwire on the real transport.

| fixture | what | stops at |
|---|---|---|
| `A_VALID` | a well-formed answer | **none**: 6, 7 and 8 pass, 9 `ELIGIBLE_FOR_HUMAN_REVIEW_ONLY`, 10 `REQUIRED_NOT_PERFORMED` |
| `B_SEMANTIC_FAILURE` | an OBSERVED statement joining alternatives | 6 |
| `B2_STRAY_ID_REFUSED_BY_THE_GATE` | a cited Evidence id the packet does not carry | 6, never 7 |
| `C_EVIDENCE_BOUNDARY_FAILURE` | the gate is handed a packet wider than the approval, and the answer cites the extra row | 7 |
| `D_ATTRIBUTION_FAILURE` | an empty request-id header | 8 |
| `E_PERSISTENCE_ELIGIBILITY_FAILURE` | a source name the hypothesis model reads as a word | 9 |

For every failure, the later stages are `NOT_REACHED`. **`DETERMINISTIC_STAGE_6_TO_9_PATH_READY`.**
**A synthetic pass is not evidence**: it shows the stages work on a well-formed answer and nothing
about what a model will write.

**What building it found.**

- **V3's stage 7 was redundant under gate v1.3.0.** The refusals it could make are:
  - a cited id outside the packet;
  - a missing audit;
  - a failed audit field.

  Gate v1.3.0 makes each of them first, at stage 6 (fixture B2). So V3's stage 7 could never fail
  once stage 6 had passed. **V4's stage 7 reads the approved boundary** (`APPROVED_EVIDENCE_IDS`,
  `APPROVED_CLAIM_IDS`, `APPROVED_EVIDENCE_TO_CLAIM`) from the digest-bound packet, not from the object
  the gate was handed. It is gate v1.3.0's own v1.4.0 audit, with no failed field.
- **V3's stage 9 refused nothing.** It set `ELIGIBLE_FOR_HUMAN_REVIEW_ONLY` unconditionally; the AST
  shows no refusal there. **V4's stage 9 constructs the canonical `OpportunityHypothesis` in memory**,
  as persistence would, and persists nothing.
- **It found a real divergence (fixture E).**
  - The gate accepts a source name as a name, even a name that contains a guard term, such as
    *Profitability Review*.
  - The hypothesis model's own prose guard (`claim-guard@1.2.0`) refuses the word *profitability* in
    the reasoning summary.
  - Without stage 9, such an answer would have reached a human and failed only at persistence.
  - TED's labels carry no guard term, which was checked.
- **Stage 8 reads the request id by header name** (`request-id`, `anthropic-request-id`,
  `x-request-id`). Absent is recorded as `NOT_EXPOSED`, and empty is refused.

## Retention and terminal paths (§24)

The V4 runner tests define every path packet V4 names, and gate 81 refuses a path no test defines.

**Eleven paths:**
- success;
- a provider output limit;
- a timeout;
- a provider refusal;
- an unsupported stop reason;
- a parse failure;
- a schema failure;
- a semantic failure;
- a provenance failure;
- **a persistence-eligibility failure (new)**;
- a human-review-ready success.

**Ten properties:**
- usage;
- request id;
- digests;
- **cost (new)**;
- **the stage table (new)**;
- the terminal outcome;
- no hidden reasoning;
- secrets redacted;
- no network;
- the post-call fail-safe.

## The consumed guards (§25)

- The V4 runner reads V1's, V2's and V3's records through V3's guard, then its own. The V1, V2 and V3
  digests are each refused with `EXECUTION_APPROVAL_ALREADY_CONSUMED` before anything else.
- V4's unseen digest is not refused.
- The packet builder checked this against the live code, the runner's verification checks it, and
  gate 81 checks it.

## Execution packet V4 (§26 to §31)

`SECOND-OPPORTUNITY-SYNTH-EXEC-V4`, version 4. It is V3's call with prompt v1.3.0 and gate v1.3.0 at
stage 6. **Nothing else changed.**

```
EXECUTION_PACKET_ID                 SECOND-OPPORTUNITY-SYNTH-EXEC-V4
VERSION                             4
SHA256                              7832b3bc7092bf040cb8f32187ba0055ad0428dd66a3ae8050fac7e25316f16b
predecessor                         SECOND-OPPORTUNITY-SYNTH-EXEC-V3 c7b8553d... (EXECUTION_SEMANTIC_GATE_REJECTED_NO_RETRY, consumed)
subject                             ted-eu:CPV-class:9261

provider / route                    anthropic, POST https://api.anthropic.com/v1/messages
                                    (synchronous Messages API, Commercial Terms, no beta header)
model                               claude-sonnet-5
thinking                            DISABLED ({"type": "disabled"})
max_tokens                          128000
calls / retries                     1 / 0
timeout                             60.0 s, not streamed

schema                              second-opportunity-synthesis-output@1.1.0  ec789d1b...
semantic gate                       second-opportunity-output-gate@1.3.0      cc3c4902...
prompt                              second-opportunity-synthesis-prompt@1.3.0 a62fa218...
representation                      2528a56a...  3604 characters
approved evidence                   6 Evidence rows and their Claims, bound in the digest

human review required               true
canonical persistence               ONLY_AFTER_DETERMINISTIC_STAGES_1_TO_9_AND_SEPARATE_HUMAN_APPROVAL
OPERATOR_EXECUTION_APPROVAL_RECORDED false
NEW_APPROVAL_REQUIRED               true
PREVIOUS_APPROVAL_REUSABLE          false
```

**Cost, recomputed from the new request body (§28).** No token-count call was made. The body was built
by the live adapter and never sent:

```
REQUEST_BODY_CHARACTERS_V4   27946   (V3 22124, rebuilt exactly, + 5822 from the prompt)
INPUT_TOKEN_ESTIMATE_V4      16199   (ceil(27946 / 2.1565 x 1.25))
OUTPUT_TOKEN_CEILING         128000
TOTAL_TOKEN_CEILING          144199
pricing                      anthropic-published-2026-09-02, 0.002 / 0.01 per 1k (held)
INPUT_WORST_CASE_COST_V4     0.032398
OUTPUT_WORST_CASE_COST_V4    1.28
EXECUTION_COST_CEILING_V4    1.312398   (headroom policy: NONE_HELD)
V3's ceiling                 1.30565    (+0.006748, x1.0052)
```

**Two figures were observed and not used.**
- V3 estimated 12825 input tokens and used 9491, so the held method covered it and is unchanged.
- V3 used 3880 output tokens. That does not size V4: `max_tokens` stays at the operator's 128000, and
  `V3_OBSERVED_OUTPUT_TOKENS` is listed among what the ceiling is not based on.
- V3 took 34.358 s. The timeout stays 60.0 s: the transport is not streamed, and the timeout may end
  the call before the token ceiling does.

**The digest binds 101 fields, and the packet carries exactly 48 more.** The packet's key set is
closed:
- An extra field refuses gate 81, so an "approved" flag nobody reviewed cannot ride along.
- So does a missing field.
- **An approval recorded by this mission refuses gate 81.** Preparing a packet authorises nothing.

## The V4 runner (§32, §33)

`run_second_opportunity_execution_v4.py` **verifies by default and executes only with `--execute`**.
Its dry verification ran on the preparing machine, against the research database, and found:

```
01 packet digest                 7832b3bc... (the one it was prepared for)
03 V1 / V2 / V3 consumed         True / True / True        V4 consumed   False
04 representation                2528a56a...  3604 characters, 6 approved Evidence rows
05 prompt                        a62fa218...
05 unstated schema bounds        0          unstated class-A rules    0
05 metadata / trusted channels   6f9186a5... / 015181aa...
06 schema / gate implementation  ec789d1b... / cc3c4902...
07 provider posture              APPROVED
08 TED transmission / live gate  PERMITTED_WITH_CONDITIONS / AVAILABLE
09 request thinking / max_tokens {"type": "disabled"} / 128000, body 27946 characters
11 worst case                    1.312398
13 retention ready               True
OPERATOR_APPROVAL                OPERATOR_APPROVAL_NOT_RECORDED
```

**`--execute` refuses with `OPERATOR_APPROVAL_NOT_RECORDED` before a transport is constructed.**

**No post-processing (§33).** Gate 81 reads the runner's syntax tree:
- no slice anywhere;
- stages 6 to 9 only read the parsed answer, which is bound exactly once and never written, deleted or
  called on with anything but a read;
- one model call site, in no loop, in a function called once.

**Stage 6 is fixed.** `validate_execution` takes `(result, context)` and nothing else, so no stand-in
gate can judge a real answer.

## CI gates 79, 80 and 81

- **Gate 79** (`render_second_opportunity_semantic_prompt_alignment.py`) re-derives the alignment
  record and the prompt v1.3.0 record whole. It refuses:
  - a moved merged artifact;
  - gate v1.3.0, the schema or prompt v1.2.0 changed;
  - a reconfirmed V3 fact that is not the one recorded;
  - an unmapped refusal site, or an enforced rule no site produces;
  - a fixture refusal claimed by no rule or by two, or an enforced rule no fixture reaches;
  - a v1.2.0 quotation v1.2.0 does not contain;
  - a class-A rule left unstated;
  - a class-A mutation that does not move the block, or a class-D mutation that does;
  - a digit, a pattern, the historical sentence, V3's name or a hard-coded source name in the system
    region;
  - a source name that is not already in the approved representation;
  - a moved representation, task or TED statement.
- **Gate 80** (`render_second_opportunity_stage_6_9_preflight.py`) re-derives the preflight record. It
  refuses:
  - a fixture that stops at another stage, or reaches a later one;
  - a valid fixture that does not reach stage 9;
  - an injectable semantic gate;
  - a runner that cannot refuse at 6, 7, 8 or 9;
  - the real transport constructed.
- **Gate 81** (`render_second_opportunity_execution_packet_v4.py`) re-derives packet V4 from the
  authenticated snapshot and the live code, requires gates 79 and 80 to validate, and refuses:
  - bound fields that do not hash to the digest;
  - a spent digest;
  - an approval recorded by the preparing mission;
  - V1, V2 or V3 edited, their consumption reset, or V3 a candidate;
  - a route, model, thinking configuration, `max_tokens`, completion policy, timeout, retention or
    persistence policy that moved from V3;
  - a request body the snapshot does not rebuild;
  - a ceiling that is not the recomputed worst case;
  - a retention path no test defines;
  - a runner with two call sites, post-processing, an injectable gate, another digest, a blind guard,
    or a guard that refuses an unseen digest;
  - an unreviewed field;
  - any preparation call, TED byte or canonical counter.

## Probe (§34)

**205 violations caught, 0 escaped, 26 of 26 positive controls, every file proved restored.**
`VIOLATIONS_ESCAPED = 0`, `POSITIVE_CONTROLS_FAILED = 0`.

What caught the violations:

- 176 were refused by the gates' own rules.
- 13 were refused by gate v1.3.0's semantics.
- 5 were refused by the V4 runner's stages.
- 4 were refused by render drift.
- 3 were refused by callables that raise.
- 4 were refused by an exception outside the attacked gate's own error class:
  - three came from gate 76's snapshot authentication, which gate 79 stands on. Prompt v1.2.0, the
    schema or the TED serialisation was edited, and the authenticated snapshot no longer rebuilt V3's
    prompt or representation;
  - one came from the transport tripwire, when a transport was built while judging.

The families, all refused:

- **Packet V4** (gate 81, 77 cases). Each edit was re-digested, so the substantive rule, not the
  digest, had to catch it. There were raw edits too. The edits covered:
  - the approval flags, the outcome and V3's digest;
  - a bound field edited or deleted, an unreviewed field added and an unbound one deleted;
  - retries, calls, thinking, `max_tokens`, the timeout and streaming;
  - V3's ceiling, estimate or body length kept, the worst case understated, headroom invented, a
    cheaper price;
  - prompt v1.2.0 or gate v1.1.0 named;
  - the gate, schema, representation, approved boundary or channels moved;
  - the stage names and conditions;
  - persistence, retention and post-processing;
  - the predecessors and their consumption;
  - the decisions and the records' digests;
  - what verification found, the accounting and the counters;
  - web, hidden reasoning, a fallback or repair model, the batch route, another model, a beta header,
    native structured output, and an unknown stop reason accepted.
- **Approvals** (gate 81, 2 cases): one recorded by this mission; one from a later mission naming
  another digest.
- **The alignment record** (gate 79, 38 cases) and **the prompt v1.3.0 record** (gate 79, 12 cases).
  Both are derived whole. The edits covered:
  - the census classes;
  - the refusal-site and coverage figures;
  - the drift and exposure checks;
  - the source origin;
  - the compliance verdicts, including case A overclaimed as gate-refused;
  - V3 replayed or whitelisted;
  - the decision, the merged digests, the prompt text and its regions.
- **The preflight record** (gate 80, 15 cases).
- **History on disk** (11 cases):
  - V1's and V3's packets with an approval written inside;
  - V2's and V3's consumption reset;
  - a V3 review packet;
  - V3's reasons trimmed;
  - V3's approval reused;
  - prompt v1.2.0's record edited;
  - Mission 1.84.11's replay and freeze records edited;
  - V3 authorising further calls, caught by gate 81's own rule.
- **Rendered pages** (4 cases).
- **Live code, in a fresh interpreter** (25 cases):
  - prompt v1.2.0, the schema, the TED serialisation and gate v1.3.0's disjunction detector;
  - the renderer's layout, the disjunction connectives, the disjunction rule reversed, and "or"
    banned in every field;
  - the block or the SOURCE NAMES section dropped;
  - the TED publisher or V3's sentence written into the prompt;
  - a TED statement or the task changed;
  - in the runner: an injectable gate, gate v1.2.0 at stage 6, stage 7 reading the gate's packet, an
    empty request id accepted, stage 9 made unconditional, a transport built, the answer trimmed, a
    second call site, the guard bypassed, the ceiling raised, and another digest pinned.
- **Semantics** (13 cases) and **stages** (5 cases):
  - OBSERVED statements joining alternatives with "or", with "either ... or", and three at once;
  - a forbidden concept;
  - an unsupplied number;
  - a gated word supplied only inside the source's name;
  - a NOT-supported item claiming support;
  - a hypothesis promoted to a conclusion;
  - a wrong subject;
  - empty classifications or next evidence;
  - Evidence without its Claim;
  - a confidence above exploratory;
  - fixtures B, B2, C, D and E, each at its own stage.
- **Callables** (3 cases):
  - a source with no declared names;
  - a digit reaching the block;
  - prompt v1.3.0 rendered without its metadata channel.

**The positive controls:**
- the shipped gates 79, 80 and 81;
- five fields packet V4's digest does not bind: its `$comment`, a note, the preparation date,
  `digest_covers`, and the approval note reworded with its five separations kept;
- comments in the renderer, the V4 runner and its tests;
- the six semantic controls:
  - the good answer;
  - the alternatives split into atomic statements;
  - the joined statement downclassified to HYPOTHESIS and to UNKNOWN;
  - "or" in a prose field;
  - the publisher's name, whole, as provenance;
- `A_VALID` eligible for review only;
- the runner:
  - refusing V1, V2 and V3 but not V4;
  - finding no approval;
  - finding 17 unstated rules in v1.2.0 and 0 in v1.3.0;
  - refusing `--execute` before any transport.

**Mission 1.84.11's mis-specified control is not repeated.** Gates 79 and 80 derive their records
whole, so no field of theirs was used as a control. A reworded `$comment` there is a violation, and it
was caught. The historical 28 of 29 stands as recorded.

**Two things changed before the counted run, reported as they happened.**
- **Writing the probe exposed a gap.** Packet V4 could carry a field that was neither bound nor
  checked. Gate 81 now closes the packet's key set, and the probe's "unreviewed field added" and
  "unbound field deleted" cases test it.
- **The first run stopped on the probe's own defect.** One case remapped the first Evidence row to the
  second row's Claim, and that changed nothing, because both rows cite the same Claim. The first run
  stopped there, before any summary. The case was fixed, the probe's preflight now refuses any case
  that changes nothing, and the probe was run again, whole. The figures above are from that second
  run.

## Accounting (§38)

```
MODEL_CALLS                0
PROVIDER_REQUESTS          0
MESSAGES_API_REQUESTS      0
TOKEN_COUNT_API_REQUESTS   0
TED_BYTES_SENT             0
CANONICAL_MUTATIONS        0
Opportunities created      0
```

## Canonical state (§35)

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

- `ruff format --check` and `ruff check` are clean over 1070 files on the final tree, and `mypy` over
  209.
- Contracts, catalog and source registry are clean.
- **3853 bare-python tests and 4812 pytest tests** pass, 13 skipped, with the database unchanged
  across 29 tenant tables.
- **105 new tests**: 43 on the census, renderer and prompt, and 62 on the V4 runner.
- **81 CI gates**, three of them new, all run locally with no failure.

Gate 81's closed key set and the documentation came after the full run above. So on the final tree,
all 81 gates, ruff, and the V4 runner and renderer tests were run again.

## Outcome and stop (§36, §41)

**`SECOND_OPPORTUNITY_EXECUTION_PACKET_V4_READY_FOR_OPERATOR_APPROVAL`.** No STOP condition arose:
- the policy surface was sufficient;
- the source origin is visible;
- the representation did not move;
- the stages 6 to 9 path is ready.

**The approval surface is the one above.** An approval would be a separate record,
`second-opportunity-synthesis-execution-approval-v4.json`, beside the packet. It would name
`SECOND-OPPORTUNITY-SYNTH-EXEC-V4`, version 4 and digest `7832b3bc...`, with the decision
`APPROVE_EXACTLY_ONE_EXECUTION`.

**What the operator would be approving, stated plainly:**
- **One call, with no retry, at a worst case of 1.312398.** The expected cost is far lower: V3 cost
  0.057782.
- **The same TED bytes as V3.** The prompt is longer by 5822 characters, all of it rules and names
  already present in the representation.
- **One rule the gate cannot check.** A statement like "Contracts occur." under a name that contains
  the word is ruled out by the prompt and by the human review, not by the gate.
- **A pass that is not a persistence.** An answer that passes stages 1 to 9 becomes eligible for
  human review and nothing more. Persisting it needs a second, separate approval.

**V4 was not executed, and no approval was recorded.** Do not re-execute V3, do not treat its answer
as a candidate, and do not persist Opportunity #2. Mission 1.84.13 was not started.
