# Mission 1.84.19: Provider-Strict Tool Schema Projection, Local Contract Preservation & Execution Packet V7

**`SECOND_OPPORTUNITY_EXECUTION_PACKET_V7_READY_FOR_OPERATOR_APPROVAL`**

V6 was refused at stage 5 on one root key the closed contract does not declare. The operator kept the
contract, the gate, the prompt and the headroom policy, and asked for the provider's strict tool use
over a deterministic projection of the contract, with the full contract still deciding stage 5 locally.

- **Strict tool use fits the execution architecture.** The provider documents it for `claude-sonnet-5`
  on the Messages API, with `"strict": true` at the top level of the tool definition, no beta header,
  and forced `tool_choice` still available.
- **The projection keeps the whole shape and drops what the provider does not document enforcing.**
  Every property name, every required list, every type and enum, the uuid format and every object
  closed with `additionalProperties: false` are sent. The 30 lengths, counts and patterns the provider
  does not document enforcing are not sent, and each one is still enforced by schema v1.2.0 at local
  stage 5.
- **The projection was frozen, committed and pushed, and found on the remote, before any V7 artifact
  existed.**
- **Packet V7 is V6's call with a strict tool, frozen and unapproved.** Its request body differs from
  V6's in exactly two places: the tool's input schema and the strict flag.
- **Nothing was sent.** 0 model calls, 0 provider requests, 0 token-count requests, 0 TED bytes, 0
  canonical mutation.

```
START_COMMIT        893893ab8a392e22c494853ed84383995d57f36e
BRANCH              sprint-1/mission-1.84.19
FREEZE_COMMIT       57154affb934516650b84480c2438a75c9b9a5a5  (pushed, found by ls-remote at 2026-09-13T20:30:52Z)

PACKET              SECOND-OPPORTUNITY-SYNTH-EXEC-V7 v7
                    51023d0d2ed780db4c7d5018a289939e7c9c83061f8768051ef1cd7b8ae674e8
APPROVAL            none recorded; NEW_APPROVAL_REQUIRED = true

PRIMARY_OUTCOME     SECOND_OPPORTUNITY_EXECUTION_PACKET_V7_READY_FOR_OPERATOR_APPROVAL
```

## The operator's decision

Ten lines, carried as data in gate 92's record and bound into nothing else:

```
KEEP_OUTPUT_SCHEMA_V1_2_0_UNCHANGED
KEEP_SEMANTIC_GATE_V1_4_0_UNCHANGED
KEEP_PROMPT_V1_5_0_SEMANTICS_UNCHANGED
KEEP_GENERATION_HEADROOM_4_OVER_5_UNCHANGED
DO_NOT_REMOVE_ADDITIONAL_PROPERTIES_FALSE
DO_NOT_ALLOW_UNKNOWN_FIELDS
DO_NOT_POST_PROCESS_UNKNOWN_FIELDS_AWAY
INVESTIGATE_AND_PREPARE_PROVIDER_STRICT_TOOL_USE
USE_A_DETERMINISTIC_PROVIDER_STRICT_SCHEMA_PROJECTION_IF_REQUIRED
KEEP_THE_FULL_LOCAL_SCHEMA_V1_2_0_AS_THE_AUTHORITATIVE_STAGE_5_CONTRACT
```

## V6, reconfirmed from what it kept

Re-derived from V6's committed record and its retained answer, not quoted from the Mission 1.84.18
report:

```
outcome                  EXECUTION_SCHEMA_REJECTED_NO_RETRY, approval consumed
provider requests        1   model calls 1   retries 0
stop reason              tool_use
tokens                   12903 in, 3637 out, 0 thinking, 16540 total
actual cost              0.062176
root keys                21: all 20 declared, plus "parameter name": "value"
summary                  1169 characters (target 1200, hard maximum 1500)
stages                   1 to 4 passed, 5 failed, 6 to 10 not reached
live v1.2.0 violation    <root>: unknown field 'parameter name'; additionalProperties is false
```

- **Schema v1.2.0 re-run over the retained answer gives the same one violation, verbatim.**
- `OBSERVED_UNKNOWN_PROPERTY_EVENTS_V6 = 1`. `PROVIDER_UNKNOWN_PROPERTY_RATE = NOT_ESTABLISHED`: one
  event is one event, and no rate follows from it.
- V6's answer was not replayed through the projection, repaired or reclassified. It chose nothing in
  the projection, which is a pure function of the contract and the reviewed profile.

## The provider's own documentation

Four first-party pages, read on 2026-09-13 (8 requests: each page read twice, both reads giving the same
SHA-256), recorded by gate 92 with 27 propositions located by line and quoted verbatim:

| id | page | bytes | sha256 |
|---|---|---|---|
| E01 | `build-with-claude/structured-outputs.md` | 110492 | `4e500fed...` |
| E02 | `agents-and-tools/tool-use/strict-tool-use.md` | 40202 | `96c6f324...` |
| E03 | `implement-tool-use.md`, redirected to `define-tools.md` | 37555 | `58d22e8f...` |
| E04 | `about-claude/models/overview.md` | 38176 | `87e737a5...` |

What they establish:

```
strict tool use supported        yes, claude-sonnet-5 on the Claude API
guarantee                        within the supported subset, with documented exceptions
strict flag location             tool definition top level, beside name, description, input_schema
beta header                      none required
forced tool_choice               compatible (restricted only under manual extended thinking,
                                 and on Fable 5.1 and Mythos 5.1)
synchronous Messages API         compatible; the route and its commercial terms are unchanged

supported keywords               type (7 types), properties, items, required,
                                 additionalProperties (false only), enum, const, format
                                 (uuid among the supported formats), minItems 0 or 1, description
not supported                    minLength, maxLength, maxItems, minimum, maximum,
                                 exclusiveMinimum, exclusiveMaximum, multipleOf,
                                 additionalProperties other than false
pattern                          a partial regex subset; "simple" counted quantifiers are supported
                                 and complex ones are not, and neither is defined
```

The documented exceptions are carried as caveats, each with its handling: a refusal or a `max_tokens`
stop may not match the schema (stage 3 reads the stop reason before any parse), enum capitalization is
not guaranteed (stage 5 compares enum members exactly), the internal complexity limits cannot be
verified without a request, and the first request's grammar compilation latency is not documented.

**Nothing in the documentation contradicts the architecture**, so
`PROVIDER_STRICT_TOOL_CAPABILITY_REQUIRES_ARCHITECTURE_DECISION` was not reached.

## Two schema identities

```
canonical output contract   second-opportunity-synthesis-output@1.2.0
                            7d67bad3df06691ba46a4dcc65cbf186bc5825a87719e985637aec68640e1b66  (4906 characters)
                            decides stage 5 locally, unchanged
provider strict projection  second-opportunity-provider-strict-input-schema@1.0.0
                            87028f451205494a948e83740e73b9ca59ce3243f54e24c123b7cc2354c69783  (4249 characters)
                            what the strict tool carries, and nothing more
capability profile          anthropic-strict-tool-capability@1.0.0
                            7f3ed84547d163c330d637f6a0171b527017399bb6738cdcccc55cad08b24313
projector                   anthropic-strict-input-schema-projector@1.0.0
                            packages/llm-gateway/python/sros_llm_gateway/providers/anthropic_strict.py
                            4eef60b03ac48caf72e337af7e9e1ad07b05d3fe3d14412dfe7ce7287679f02e
projection tests            fe4abd1cd6512ef70f237bb9ab5dbfc19a657bc5983436fe04ec6c21e0f115d9
```

**The projection is not a successor contract, not a weaker stage 5, not a persistence contract, not a
semantic gate, and not authority to discard a constraint.** `PROVIDER_STRICT_SUBSET_COMPLIANCE` is what
strict mode can guarantee; `FULL_CANONICAL_SCHEMA_COMPLIANCE` is `LOCAL_STAGE_5_ONLY`.

The projector is a pure function of the schema and the profile. It reads no file, no model output and
no execution record, lives in `providers/` because vendor knowledge lives only there (ADR-006), and
leaves the plain adapter untouched. An object whose `additionalProperties` is not `false`, or a keyword
the profile has no rule for, is a blocker and the projection refuses to exist.

## Constraint accounting

Over the 75 constraints `constraint_inventory` finds in schema v1.2.0:

```
PROVIDER_ENFORCED                             44
LOCAL_ONLY                                    30
REPRESENTED_IN_DESCRIPTION_AND_LOCAL_ONLY      1   (the UNKNOWN_NOT_SUPPORTED sentinel)
UNSUPPORTED_ARCHITECTURE_BLOCKER               0
CANONICAL_CONSTRAINTS_ACCOUNTED_FOR          100_PERCENT
```

| behaviour | projection | local stage 5 |
|---|---|---|
| root property set | the 20 canonical names, equal | the 20 names |
| required set | equal at every object | equal |
| `additionalProperties` | `false` at every object | `false` at every object |
| `maxLength` | not sent | enforced, the summary's 1500 included |
| `maxItems` | not sent | enforced |
| `pattern` | not sent (all three carry a counted quantifier) | enforced |
| `enum` | sent, members unchanged | enforced, exact |
| `format: uuid` | sent, provider-enforced | an annotation to the local validator |
| descriptions | sent unchanged | annotations |

**8 removed constraints are not stated in prompt v1.5.0**: 3 patterns, 3 copied `maxLength`s on id
elements and 2 vocabulary `maxItems`. Each is still enforced at local stage 5, and gate 92 names them.
Every removed bound on text the model composes is stated in words by prompt v1.5.0, so
`DESCRIPTION_TRANSFORMATION = NOT_APPLIED`: the SDK convenience of copying removed bounds into
descriptions is not an API requirement, and it would be a second rendering of the same number.

## What the projection simulations showed

Twelve synthetic cases, run with the local validator over both schemas (the projection's uuid format is
provider-enforced and only annotated locally, and nothing here stands in for a provider request):

| case | projection | contract |
|---|---|---|
| a valid answer | PASS | PASS |
| an extra root key `"parameter name": "value"` | FAIL | FAIL |
| a required field missing, a wrong type, a bad enum member, an extra nested key | FAIL | FAIL |
| a 1500-character summary | PASS | PASS |
| a 1501-character summary | PASS | FAIL |
| 25 statement classifications | PASS | FAIL |
| an empty uncertainty list, a bad source-family slug, an uppercase uuid | PASS | FAIL |

**The contract is stricter than the projection, and never weaker.**

## The request

```
strict flag         tools[0].strict = true, beside name, description and input_schema; not inside the schema
tool_choice         {"type": "tool", "name": "emit_structured_output"}, forced, unchanged
tools               exactly one
beta headers        none
thinking            {"type": "disabled"}
max_tokens          128000
```

**The body differs from V6's in exactly two places**, rebuilt through both runners over the same
authenticated snapshot:

```
differences      tools[0].input_schema: changed
                 tools[0].strict: added
unchanged        model, max_tokens, system, messages, thinking, tool_choice,
                 tools[0].name, tools[0].description
V6 body          31967 characters, tool schema 7d67bad3... (the contract)
V7 body          31326 characters, tool schema 87028f45... (the projection)   -641
```

`STRICT_REQUEST_BODY_HAS_UNAPPROVED_DRIFT` was not reached.

## The prompt

**Prompt v1.5.0, byte-identical to V6's** (`0713eb80...`).

```
PROMPT_TEXT_CHANGED            false
PROMPT_SEMANTICS_CHANGED       false
EXECUTION_BINDING_CHANGED      true   (bound to V7's digest, beside a strict tool)
EXTRA_PROPERTY_WARNING_ADDED   false
```

No warning about extra properties was written for V6. Strict decoding, not wording, is the mechanism
under test, and the prompt already states the closed object in words.

## What did not move

- **Schema v1.2.0** (`7d67bad3...`), `additionalProperties: false`, the summary's 1500 and 1200.
- **Gate v1.4.0** (`eb03899b...`), frozen at `402a698`.
- **The headroom policy**, 4/5.
- **The TED representation**, `2528a56a...`, 3604 characters.
- **The route**: `anthropic`, `POST https://api.anthropic.com/v1/messages`, `claude-sonnet-5`, thinking
  disabled, 128000, one call, no retry, 60.0 s.
- **The completion policy**, the retention paths and properties, and the persistence policy, which now
  also names the strict-projection record and its freeze commit as provenance.
- **The ten stages**, V6's exactly. Strict decoding is not a stage.

## The freeze

```
commit        57154affb934516650b84480c2438a75c9b9a5a5
              "Mission 1.84.19: freeze the provider-strict projection of schema v1.2.0 before V7"
push          sprint-1/mission-1.84.19
verified      git ls-remote origin refs/heads/sprint-1/mission-1.84.19 printed that SHA,
              at 2026-09-13T20:30:52Z, before the V7 runner, gate 93 or packet V7 existed
STRICT_PROJECTION_FREEZE_PUSH_VERIFIED_BEFORE_V7 = true
```

The freeze commit carries gate 92, the projector, its tests and the record. V6's process deviation, a
freeze whose push failed and was misread, is not inherited: this push was verified by its ref before
anything depended on it, and the probe verified it again from the remote.

## V7's stages, on synthetic answers

Through the V7 runner's own `validate_execution`, with no transport:

| fixture | summary | must stop at | stopped at |
|---|---|---|---|
| A_VALID | 237 | stage 9 | stage 9, accepted for human review only |
| B_SEMANTIC_FAILURE | 237 | 6 | 6 |
| B2_STRAY_ID_REFUSED_BY_THE_GATE | 237 | 6 | 6 |
| C_EVIDENCE_BOUNDARY_FAILURE | 237 | 7 | 7 |
| D_ATTRIBUTION_FAILURE | 237 | 8 | 8 |
| E_PERSISTENCE_ELIGIBILITY_FAILURE | 235 | 9 | 9 |
| F_LONG_SUMMARY_POSITIVE | 1189 | stage 9 | stage 9 |
| G_LONG_SUMMARY_SEMANTIC_NEGATIVE | 1216 | 6 | 6 |
| H_SUMMARY_AT_THE_NEW_BOUND | 1500 | stage 9 | stage 9 |
| I_SUMMARY_ONE_OVER_THE_NEW_BOUND | 1501 | 5 | 5 |
| **J_EXTRA_ROOT_PROPERTY_REFUSED_AT_LOCAL_STAGE_5** | 237 | **5** | **5** |

**The case strict decoding should make impossible is still refused locally**: an answer carrying
`"parameter name": "value"` beside the twenty declared fields stops at stage 5 with V6's exact
violation, and nothing after it runs. The runner tests prove it for that key and for another, and that
the answer is kept whole.

## Retention

The V7 runner keeps V6's retention paths and properties unchanged, each named by a V7 runner test that
gate 93 requires to exist: success, output limit, timeout, refusal, unsupported stop reason, parse,
schema, semantic, provenance and persistence-eligibility failures, human-review-ready success; usage,
request id, digests, cost, stage table, terminal outcome, stripped reasoning, redacted credentials, no
real transport, and the post-call fail-safe. The artifact also records `PROVIDER_STRICT_MODE` and the
projection's digest.

## Cost, recomputed

```
request body             31326 characters  (V6 31967, -641)
input token estimate     18158  (31326 / 2.1565 x 1.25)
output token ceiling     128000
total token ceiling      146158
input worst case         0.036316
output worst case        1.28
total worst case         1.316316
execution cost ceiling   1.316316  (headroom policy: NONE_HELD)
previous ceiling (V6)    1.31706   (-0.000744)
```

**V6's 1.31706 was not copied.** The multiplier's margin over the raw estimate is 3631 tokens, which
covers the documented 474 tool-use tokens. **The system prompt strict mode adds has no documented token
count**, so it is recorded as `NOT_ESTABLISHED` rather than as covered. V6 estimated 18530 input tokens
and used 12903.

## Residual risks, disclosed

- **First-request grammar compilation.** The provider compiles a grammar from the tool schema on first
  use, caches it for 24 hours, and times compilation out at 180 seconds; the latency of a first
  compilation is not documented. The request timeout is 60 seconds, so V7's one request may end at the
  timeout, fail-closed and not retried, before anything is generated.
- **Internal complexity limits** are not verifiable without a request. The explicit ones hold (1 strict
  tool, 0 optional parameters, 0 union types); a schema too complex to compile is a 400 error the one
  approved request would spend.
- **Strict decoding is documented, not observed.** No request was made, so nothing here shows that a
  strict tool prevents an undeclared key in practice. Stage 5 does not depend on it.

## Packet V7

```
EXECUTION_PACKET_ID                 SECOND-OPPORTUNITY-SYNTH-EXEC-V7
VERSION                             7
SHA256                              51023d0d2ed780db4c7d5018a289939e7c9c83061f8768051ef1cd7b8ae674e8
predecessor                         V6 969128dd...  EXECUTION_SCHEMA_REJECTED_NO_RETRY, consumed
predecessor schema violation        UNKNOWN_ROOT_PROPERTY
output schema                       second-opportunity-synthesis-output@1.2.0  7d67bad3...
full canonical stage 5              REQUIRED_OUTPUT_SCHEMA_V1_2_0_LOCAL
semantic gate                       second-opportunity-output-gate@1.4.0  eb03899b...
prompt                              second-opportunity-synthesis-prompt@1.5.0  0713eb80...
summary                             hard maximum 1500, target 1200, ratio 4/5
representation                      2528a56a...
provider strict mode                true, FORCED_STRICT_TOOL_USE
provider strict schema              second-opportunity-provider-strict-input-schema@1.0.0  87028f45...
capability profile                  anthropic-strict-tool-capability@1.0.0  7f3ed845...
projector / tests                   4eef60b0... / fe4abd1c...
freeze commit                       57154aff...
route                               anthropic, POST https://api.anthropic.com/v1/messages
model                               claude-sonnet-5, thinking DISABLED
MAX_OUTPUT_TOKENS / CALLS / RETRIES 128000 / 1 / 0
timeout                             60.0 s
EXECUTION_COST_CEILING              1.316316
human review                        required
canonical persistence               only after stages 1 to 9 and a separate human approval
RESIDUAL_SEMANTIC_LIMITATION_ACCEPTED_FOR_V7   false
OPERATOR_EXECUTION_APPROVAL_RECORDED           false
NEW_APPROVAL_REQUIRED                          true
PREVIOUS_APPROVAL_REUSABLE                     false
```

The digest binds V6's fields without V6's residual-risk flag, plus the strict mechanism, the
projection's and profile's ids and digests, the projector's and tests' digests, the projection record's
digest and its freeze commit, the full-contract stage 5 requirement, the request-body differential and
V7's own residual-risk flag. It excludes itself, the date, the notes, V6's observation and
reconfirmation, the synthetic preflight, the freeze-push record, the prompt decision, what verification
found and the accounting.

**V7's runner** is V6's with the strict adapter, the frozen projection recomputed and refused unless
both its digest and the profile's are the frozen ones, and a check of the built body's tool. Its stage 5
is the full schema v1.2.0, read from its syntax by gate 93. It refuses V1's to V6's digests through V6's
guard before its own, and accepts an unseen one. **Its verification ran once against the research
database, sending nothing**, and found exactly the values the packet records: representation
`2528a56a...` (3604 characters), prompt `0713eb80...`, 0/0/0 unstated constraints, rules and targets,
the strict tool `FROZEN_PROJECTION_STRICT_FORCED`, a 31326-character body, a worst case of 1.316316,
V1 to V6 consumed, V7 not, and `OPERATOR_APPROVAL_NOT_RECORDED`.

## CI gates 92 and 93

**Gate 92** (`render_second_opportunity_provider_strict_projection.py`, committed with the freeze)
re-derives the projection record: every capability finding from its quoted documentation, every
constraint's disposition, the invariants, the simulations and the freeze pins.

**Gate 93** (`render_second_opportunity_execution_packet_v7.py`) re-derives packet V7. It refuses:
- bound fields that do not hash to the digest, a spent digest, an unreviewed or missing field, or an
  approval recorded by the mission that prepared the packet;
- V1 to V6 edited or their consumption reset, or V6's refusal re-derived as anything but its one
  undeclared field;
- a contract, gate, headroom policy or prompt that moved from V6, or post-processing to fit;
- strict fields that are not gate 92's frozen ones, or a moved freeze commit or push record;
- a request body that differs from V6's anywhere but the strict flag and the projected schema, a strict
  flag inside the schema, a second tool or an unforced one;
- a route, model, thinking, max_tokens, completion, timeout, retention or persistence policy moved;
- a ceiling other than the worst case recomputed from the new body, V6's included;
- a residual-risk acceptance carried over;
- a synthetic answer that does not stop where it must, the extra-root-key case included;
- a runner with more than one call site, post-processing, an injectable gate, a stage 5 other than the
  full contract, another adapter, another digest, a special case for the key V6 carried, or one that
  would execute V1 to V6 again;
- any preparation call, TED byte or canonical counter that moved.

## Probe (section 38)

**The probe's first run found a defect in gate 93, and it was fixed before the run that counts.** The
probe tripwires the real transport's constructor for its whole duration. Its first run stopped at the
shipped-state control: gate 93's `_check_request` built a plain `AnthropicProvider` to compare headers
with the strict one and passed no transport, so the adapter constructed a real `UrllibTransport`.
Nothing was sent, since only the headers were read, but section 38 requires that no network transport
be constructed. The comparison adapter now gets the runner's `_NoSend` transport, and gate 93 and its 57
tests pass again.

**The second run caught every violation and escaped none, but two were caught by a crash rather than
by a rule.** With the projection opened (`additionalProperties: true`) or a `maxLength` sent, the strict
adapter itself refused to build the body with `ProviderInvalidRequestError`, and gate 93 let that
exception through unnamed. A refusal nobody names reads like a broken gate. Gate 93 now turns the
adapter's refusal, and the runner's refusal of a projection or profile that is not the frozen one, into
`STRICT_TOOL_USE_INCOMPATIBLE_WITH_EXECUTION_ARCHITECTURE`, and a 58th test covers it. The run below is
the third.

**One sibling is recorded, not changed.** One assertion in the frozen projector tests
(`test_anthropic_strict.py`, `test_no_beta_header_is_added`) builds
`AnthropicProvider(api_key="k")` the same way. It sends nothing and runs only in the unit suite. The file
is part of the freeze (`fe4abd1c...`), and editing it would move the frozen test digest after V7 was
prepared on it. A later mission may fix it with a new freeze.

**76 violations caught, 0 escaped, 28 of 28 positive controls, every file proved restored.**
`VIOLATIONS_ESCAPED = 0`, `POSITIVE_CONTROLS_FAILED = 0`. 75 were refused by a named rule of gate 93
(which runs gates 88, 89, 91 and 92 inside it), 1 by render drift, 0 by a crash. The real transport's
constructor was tripwired for the whole run, and no provider, model or token-count request was made.

**Data, edited on disk and judged by gate 93's full validation** (50 cases; every bound edit to packet V7
was re-digested, so the digest could not be what refused it):
- V6's history: its undeclared key deleted from the retained answer, V6 reclassified as valid, its
  violation emptied, its consumption reset, its packet and its approval edited;
- packet V7: the projection named as the canonical contract, full canonical compliance attributed to
  strict mode, the canonical digest moved, unknown keys filtered away, strict mode off, the mechanism
  back to plain forced tool use, the projection's or the profile's digest moved, V6's answer used to
  choose the projection, a prompt warning for V6, the prompt said changed, the semantic gate or the
  source metadata or the TED representation moved, another model, thinking enabled or named adaptive, a
  retry in the packet or in the request, each of the six fallback and continuation flags, the residual
  risk or V6's process deviation inherited, the freeze push unverified or the freeze commit moved, a
  provider, model or token-count call during preparation, V7 marked approved or a previous approval
  reusable, V6's 1.31706 copied, a beta header, the differential forged, a canonical counter moved, V6's
  digest replayed as V7's, and a bound field moved without its digest;
- approvals beside V7: V6's approval reused, and an approval recorded by this mission;
- gate 92's record: full canonical compliance attributed to the provider, a string length claimed
  provider-enforced, and the record emptied (strict tool use with no compatibility audit behind it).

**Live code, edited and judged in a fresh interpreter** (25 cases):
- the V7 runner: local stage 5 removed, stage 5 judged by the projection, unknown keys filtered before
  stage 5, `"parameter name"` special-cased, a stage 6 violation hidden, the projection gaining an
  undeclared property, dropping a required one, changing an enum, widening a type, opened, or carrying
  a `maxLength`, and V1's to V6's consumed guards bypassed;
- the strict adapter: strict placed inside `input_schema`, strict false, a second tool, the
  compatibility audit skipped; the plain adapter's `tool_choice` made `auto`;
- the contract and what judges it: `additionalProperties` true, the 1500 dropped, `maxItems` dropped, the
  1500 moved to 1100, the shared validator's closed-object check removed, a hand-written warning
  appended to prompt v1.5.0, gate v1.4.0 edited, and the projector edited after the freeze (refused by
  gate 92's pins).

**The rendered page**, hand-edited (1 case, by drift).

**The 28 positive controls:**
- the shipped gates 92 and 93, and comments in the V7 runner and in gate 93's tests;
- V6's one-field refusal reproduced by the live validator, the canonical schema and semantic gate
  digests unchanged;
- the projection's root with exactly 20 properties and `additionalProperties: false`, every required
  name preserved;
- an extra root property refused by the projection and by the contract;
- a provider-supported valid answer passing the projection;
- a 1501-character summary that passes the projection and fails the contract;
- through the V7 runner, 1500 reaching stage 9, 1501 and an extra root property stopping at stage 5,
  and a semantically invalid, strict-shaped answer stopping at stage 6;
- V1 to V6 each refused as consumed, and the unseen V7 digest awaiting an approval;
- a V7 `--execute` refused before any network, with `execute()` replaced by a function that raises;
- no network transport constructed during the whole run;
- the freeze commit found on the remote by `git ls-remote` and `git merge-base --is-ancestor` against
  the fetched branch. At that moment local HEAD was the same commit, because nothing after the freeze
  had been committed; the control never read it.

## Accounting

```
MODEL_CALLS                0
PROVIDER_REQUESTS          0
MESSAGES_API_REQUESTS      0
TOKEN_COUNT_API_REQUESTS   0
TED_BYTES_SENT             0
CANONICAL_MUTATIONS        0
documentation requests     8 (4 first-party pages, each read twice)
```

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

## Verification

- `ruff format --check` and `ruff check` are clean over 1129 files, and `mypy` over 215.
- Contracts, catalog and source registry are clean.
- **3877 bare-python tests and 5643 pytest tests** pass, 13 skipped. The database is unchanged across
  29 tenant tables; the global tables are unchanged across 17, with 11 rows appended by the suites to
  1 append-only table, as the checker reports.
- **199 new tests**: 24 on the strict adapter and the projector, 33 on gate 92, 84 on the V7 runner and
  58 on gate 93. **2 tests re-pointed** from a pinned list of `providers/` modules to the property each
  protects (no subscription route, no local inference provider), because the strict adapter is a new
  module there and the properties still hold.
- **93 CI gates**, two of them new (92 and 93), all run locally with no failure.
- The V7 runner's verification ran once against the research database and sent nothing.
- The canonical counters were read before and after the full run, and they are unchanged.

## Next

**Stop.** V7 is frozen and unapproved, and this mission authorised no inference.

Approving `SECOND-OPPORTUNITY-SYNTH-EXEC-V7` by its digest `51023d0d...`, recorded beside the packet by
a later mission, authorises exactly one request on the synchronous route with a strict forced tool over
the frozen projection, thinking disabled at 128000, the ten ordered stages with the full schema v1.2.0
at stage 5, and an Opportunity hypothesis persisted only after deterministic acceptance and a separate
human approval. The approval must say whether it accepts the residual semantic limitation again; V6's
acceptance expired with V6, and so did its process deviation.

One call will be one observation: whether strict decoding prevents an undeclared key is documented and
has not been observed, and stage 5 decides either way. **Do not execute V7 without that approval, do not
approve it on the operator's behalf, do not reuse V1's to V6's approvals, and do not persist Opportunity
#2.** Mission 1.84.20 was not started.
