# Mission 1.84 — One inference prepared to the last byte, and none executed

**Outcome: `SECOND_OPPORTUNITY_SYNTHESIS_EXECUTION_PACKET_READY_FOR_OPERATOR_APPROVAL`.**

The preparation was regenerated as v5 so the egress blocks describe the live governance, the
approved payload was reconstructed with the production serializer and found **byte-identical** to
the one the operator approved, and one execution packet was frozen: one provider, one model, one
prompt, one call, one cost ceiling, and an output contract that stops for a human before anything
is persisted.

**`OPERATOR_EXECUTION_APPROVAL_RECORDED = false`.** Nothing was sent, and the TED egress approval
is not an approval of this call.

---

## Report

```
START_COMMIT                 = f477eab       BRANCH = sprint-1/mission-1.84
MIGRATION_HEAD               = 0036_grant_use_profile_vocabulary (measured)

PREPARATION_BEFORE / AFTER   = v4 / v5       V4_CONTENT_CHANGED = false
PACKETS                      = 21            FORMABLE = 14
FIELDS_THAT_MOVED            = 1 (external_synthesis), on 13 packets
SELECTED_PACKET_EGRESS       = AVAILABLE, refusal_reasons []

SUBJECT                      = ted-eu:CPV-class:9261 (Sports facilities operation services)
PACKET_ID                    = e218b56a8f938f4d5f7fc961e7f0c2cfe184c4396395334140c6199b48316592
REPRESENTATION_SCHEMA        = opportunity-transmission-representation@1.0.0
REPRESENTATION_SHA256        = 2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72
APPROVED_SHA256              = 2528a56a…, and they are the same string
REPRESENTATION_CHANGED       = false         HARD_STOP_TRIGGERED = false
CLAIM_COUNT = 5   EVIDENCE_COUNT = 6   CHARACTER_COUNT = 3604
ALLOWLIST_VIOLATIONS = 0   PERSONAL_DATA_FIELDS = 0   RAW_SOURCE_PAYLOAD = 0

ELIGIBLE_PROVIDER_ROUTES     = 1  (anthropic, API route under the Commercial Terms)
PROVIDER_POSTURE             = APPROVED      REGISTER_DERIVED = true, no vendor hard-coded
EXCLUDED_BY_THE_REGISTER     = gemini NOT_APPROVED, fake NEVER_PRODUCTION
AVAILABLE_TEXT_MODELS        = 1  (claude-sonnet-5 on STRONG_MODEL)
UNCONFIGURED_TIERS           = FAST_MODEL, BALANCED_MODEL (provider binds the string "null")
MODEL_SELECTION              = deterministic; no smaller approved model exists to prefer

PROMPT_ID                    = second-opportunity-synthesis-prompt   PROMPT_VERSION = 1.0.0
PROMPT_SHA256                = af5289494416139d302eed704c12b9c53ab2547dca336e2ca4a834ec936c5080
BASE_PROMPT_VERSION          = 1.0.0 -> 1.1.0 (the reliability sentence is the packet's now)
SUPPLIED_STATEMENTS          = 6, all in the untrusted region, each labelled evidence= claim=

OUTPUT_SCHEMA                = second-opportunity-synthesis-output@1.0.0, 20 required fields
OUTPUT_GATE                  = second-opportunity-output-gate@1.0.0
BASE_GATE                    = opportunity-synthesis-persistence-gate@1.0.0 -> @1.1.0
CONFIDENCE_CLASSIFICATION    = EXPLORATORY, a closed enum of one
NUMERIC_CONFIDENCE_REQUESTED = false         SCORE_REQUESTED = false
VALIDATION_STAGES            = 8, ordered
HUMAN_OUTPUT_REVIEW_REQUIRED = true

CHARS_PER_TOKEN              = 2.1565  (measured: 12868 docker wire chars / 5967 reported tokens)
WIRE_CHARACTERS              = 15742   RAW_ESTIMATE = 7300.0   MULTIPLIER = 1.25
INPUT_TOKEN_ESTIMATE         = 9125    MAX_OUTPUT_TOKENS = 3000   TOTAL_TOKEN_CEILING = 12125
PRICING_VERSION              = anthropic-published-2026-09-02 (held configuration)
WORST_CASE_CALL_COST         = 0.04825 cost units
EXECUTION_COST_CEILING       = 0.10 cost units
MAX_MODEL_CALLS              = 1   max_retries = 0   REQUEST_TIMEOUT = 60.0s
TEST_REQUESTS_SENT           = 0

TRAINING = false  FINE_TUNING = false  EMBEDDINGS = false
WEB = false       TOOLS = false        EXTERNAL_RETRIEVAL = false
HIDDEN_REASONING             = NOT RETAINED, and not requested

EXECUTION_PACKET_ID          = SECOND-OPPORTUNITY-SYNTH-EXEC-V1   VERSION = 1
EXECUTION_PACKET_SHA256      = 570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92
OPERATOR_EXECUTION_APPROVAL_RECORDED = false

MODEL_CALLS = 0   BYTES_SENT = 0   TOKENS_SENT = 0   PROVIDER_REQUESTS = 0
RESEARCH_DATA_FETCHES = 0   NETWORK_DISCOVERY_CALLS = 0
CANONICAL_RESEARCH_MUTATION = 0   OPPORTUNITIES_CREATED = 0   SCORES = 0

raw_records 325 / with resource_id 325   signals 60   claims 91   revisions 92
evidence 112   assessments 4   independence groups 0
opportunities 1   opportunity revisions 2   evidence links 14
scoring.scores ABSENT   embeddings 0   source reviews 71
Every counter identical to the section 1 preconditions.

TESTS                        = 3785 bare-python across 9 packages; 3431 pytest
CI_GATES                     = 63 -> 64
VIOLATIONS_CAUGHT / ESCAPED  = 75 / 0        positive controls 8 of 8
PRIMARY_OUTCOME              = SECOND_OPPORTUNITY_SYNTHESIS_EXECUTION_PACKET_READY_FOR_OPERATOR_APPROVAL
NEXT                         = an operator decision on SECOND-OPPORTUNITY-SYNTH-EXEC-V1
```

---

## The hard stop was not triggered, and that is a measurement rather than an assumption

Section 5 makes one thing non-negotiable: if the payload this mission reconstructs is not the
payload the operator approved, the mission stops with `APPROVED_TED_EGRESS_REPRESENTATION_CHANGED`
and never recovers by reserialising, by updating the approval, or by arguing that the meaning is
unchanged.

The packet was rebuilt through the current deterministic path — the live eligibility gate, the
current grouping procedure, the current subject registry — and serialized by
`serialize_packet_for_model`, the **production** function rather than a copy of it. The digest is
`2528a56a…`, which is the string the operator's approval names. Six Evidence rows, five Claims,
3604 characters, zero allowlist violations and zero personal-data fields, exactly as Mission 1.83
measured them.

It could have gone the other way. Mission 1.83.1 appended a source review, Mission 1.82 changed
the subject vocabulary, and the reliability path moved in Mission 1.77. Any of those could have
moved a byte. **A digest that has to be recomputed to be believed is the only kind worth
recording.**

---

## Three stale assertions, generalised rather than bypassed

All three date from Mission 1.31, all three were true when written, and all three were made false
by Mission 1.77's late reliability resolution. None was weakened to admit this packet.

**The persistence gate demanded `NON_SCORABLE` / `MISSING_RELIABILITY`.** Every row in the corpus
was non-scorable when that was written. Reliability now resolves from lineage, so 12 of the docker
packet's 14 rows and 6 of the TED packet's 6 are scoring-eligible — and the check would have
refused a **truthful** output, for its own subject as well as for this one. It reads the packet
now and demands the truthful statement either way, plus a refusal of any claim that a score
exists. `opportunity-synthesis-persistence-gate@1.0.0` to `@1.1.0`.

**`EXTERNAL_KNOWLEDGE_MARKERS` is a container vocabulary.** It is the right check and the wrong
list for any other subject: a model writing about sports facilities reaches for pools, gyms,
memberships, bookings and councils, and none of those words is in the docker list. It is a
parameter now, defaulting to the frozen constant, so **every existing caller behaves
identically** and this packet supplies its own 62 markers. The rule is unchanged: a word is
permitted exactly when a supplied statement contains it.

**The task template told the model that every row is NON_SCORABLE, as a packet FACT.** A prompt
that states a falsehood about the packet is worse than one that omits it, because the gate then
requires the model to repeat it. The sentence is derived from the packet now, and the base prompt
version moves to 1.1.0. Mission 1.31.1 recorded the hash it actually sent; that record is history
and was not rewritten.

**`synthesis_prompt_hash()` did not move**, because it hashes the TEMPLATE rather than the
rendered bytes. That is why this mission's `PROMPT_SHA256` is computed over the rendered regions
instead: a digest that two different packets share does not identify what would be sent.

---

## The provider was derived, and the model was the only one there is

Section 9 forbids a hard-coded vendor. The gate recomputes the eligible set from the current
register, and the packet is refused if it names a provider the register does not approve — so the
answer would change on its own if the register did. Today exactly one route qualifies: `gemini`
is `NOT_APPROVED` on its assessed unpaid route, which trains on submitted content, and `fake` is
`NEVER_PRODUCTION` by name.

**A vendor is not a route**, so the packet names the route it means: the Anthropic API under the
Commercial Terms of Service, with consumer products recorded as a DIFFERENT route that is not
assessed. A sibling route cannot inherit an assessment nobody made.

The model universe is the deployment's held configuration and nothing else. No network discovery,
no model list fetched, no price invented. `LLM_TIER_FAST` and `LLM_TIER_BALANCED` both bind the
literal string `"null"`, which `TierBinding.configured` reads as unconfigured, and the embedding
tier is local and forbidden here — so **there is no smaller approved model to prefer**, and
nothing was chosen for being the strongest. Section 12's operator stop was not reached because
the choice was not a choice.

---

## Only the parameters that exist

Section 21 says not to invent unsupported parameters. `LlmRequest` was read rather than assumed,
and it carries thirteen fields: tier, task, prompt template id and version, variables, response
schema, prompt, workspace, research session, correlation id, timeout, max retries and whether
structured output is required. **There is no temperature, no top_p, no seed and no
reasoning_effort.**

So the packet freezes what exists and records the rest as `null` **with a note saying null means
the Gateway does not expose it, never that a default was silently accepted**. The gate enforces
both directions: a non-null parameter must be a field the request type carries, and a null one
must not be — otherwise a real knob could be frozen as absent.

`max_retries = 0`, overriding the Gateway's own default of 2 and this deployment's
`LLM_MAX_RETRIES=2`, because **a retry is a second call and this packet authorises one**. A
timeout is not permission to retry, and the record says so.

---

## The budget rests on the one measured pair this repository has

No tokenizer package is installed and none was fetched, so the estimate is a ratio rather than a
count. Mission 1.31.1's provider response reported 5967 input tokens for the docker prompt; that
prompt was re-rendered here at 12868 wire characters, giving 2.1565 characters per token. The TED
prompt is 15742 wire characters, so 7300 raw, and 1.25× conservative gives 9125.

**The limitation is recorded rather than smoothed.** The docker prompt now re-renders one sentence
differently, because the reliability sentence is derived from the packet. A ratio is robust to a
one-sentence difference and the multiplier covers more than that — and the pair is a measurement
of a slightly different string, which is what the record says.

**No test request was sent to size the budget.** Section 22 forbids it and the counter is 0.

The prices are the deployment's configured pricing table at version
`anthropic-published-2026-09-02`. The worst case is 0.04825 cost units and the ceiling is 0.10 —
roughly twice, so one oversized call is covered and a second call is not. **The cost unit is
provider-agnostic by ADR-006** and the record says so, which is what makes the ceiling enforceable
without asserting a currency. The session budget of 5 units over 120 calls is not what stops this
becoming several calls; a per-execution ceiling is.

---

## What the gate cannot name is why a human is still required

The output contract freezes one schema, one gate and eight ordered validation stages, and states
plainly that **lexical filtering does not prove semantic safety**. A hypothesis that distorts the
evidence without using a named phrase is exactly what the gate cannot catch.

So `HUMAN_OUTPUT_REVIEW_REQUIRED = true`, before canonical persistence and after every
deterministic gate has passed. The subject is recorded
`SEMANTICALLY_COHERENT_BUT_PRODUCT_LINK_UNKNOWN` with overinterpretation risk HIGH, and this is
the repository's first synthesis over a procurement record. Mission 1.31 also shows the cost of the
opposite mistake: a gate accepted on lexical grounds is a gate that has not read the answer.

`confidence_classification` is a closed enum whose only member is `EXPLORATORY`. **A self-reported
certainty is not a probability**, so the field is a label rather than a number, and no required
output field is a score.

The five forbidden transformations are stated in **both** halves — what the packet establishes and
what it is not — because a model told only what to avoid does not know what it may say. A stated
`TOTAL_VALUE` including options and renewals is not money anybody paid; published notices are not
market demand; a contracting authority is not a software buyer; an economic value is not
willingness to pay; activity in a bounded set is not product-market fit.

---

## An approval lives beside the thing it approves

`OPERATOR_EXECUTION_APPROVAL_RECORDED = false`, and the note beside it says two things rather than
one. **This document records no approval** — never that none exists. And **no old approval
authorises this call**: the TED egress decision permitted the material to leave, which is a
different act from executing this model with this prompt at this cost.

The digest binds the packet id and version, the egress decision it rests on, the subject and
selected packet, the preparation version, the purpose, the representation schema and digest, the
provider and posture, the model and tier, the prompt identity and digest, every generation
parameter, the token and cost ceilings, the call limit, the timeout, the output schema and gate
versions, the persistence policy, the six capability negatives and the failure outcome. It
excludes itself, the preparation date, the explanatory notes and the preparation accounting — so
**an approval recorded beside this packet does not move it, and a changed prompt, model, parameter
or ceiling does.**

---

## Adversarial probe

**75 deliberate violations, 75 caught, 0 escaped. 8 positive controls, 8 accepted.**

Every case edits the real documents, runs the real validator and restores; the probe asserts every
file is byte-restored afterwards. Two rules learned in Mission 1.83.1 are built in: a case writes
only documents whose parsed content changed, so the untouched frozen records keep their bytes; and
a case that edits a digest-bound field **repoints the digest first**, unless the case is about the
digest — otherwise the digest check refuses everything and every other rule goes untested.

The cases attack the payload (a moved representation, an approval edited to match it, another
subject, another purpose), the route (an unapproved provider, a deterministic claim while the
register approves two), the parameters (a retry, a second call, an invented temperature, a real
parameter frozen as unsupported), the budget (a ceiling below the worst case, a missing pricing
version, a test request), the boundaries (each of the six capabilities, retained reasoning, an
approval written inside, persistence without human review), the contract (a numeric confidence, a
dropped validation stage, a reordered one, human review dropped or weakened, a gate changed
without its version) and the accounting (a model call, a transmitted byte, research acquisition,
canonical mutation, a rewritten v4).

**One control was withdrawn, and the gate was right.** It added a sixth forbidden transformation
to the contract document alone. The gate refused it — *the contract carries a transformation the
code does not* — which is exactly the drift this gate exists to catch: a rule in the record that
the executable prompt does not carry. A real sixth transformation is a code change with its own
version bump. It was replaced by a control over a list the gate READS rather than pins: the
operator's exclusion list growing must not break a packet that already excludes everything on it.

The other controls prove a higher ceiling, a longer timeout, a larger output allowance with its
cost recomputed, a second packet version, a stricter retention posture, more required provenance,
and **a register approving a different single provider** are all still accepted. The last one
matters most: it proves the gate checks posture rather than a vendor it happens to know.

---

## Two assertions re-pointed, and the branch nobody had tested

`test_the_prompt_is_versioned_and_hashed` pinned `SYNTHESIS_PROMPT_VERSION == "1.0.0"`. A test
pinning a version asserts the prompt may never be corrected, so it was re-pointed rather than
deleted — and the **procedure** version is now asserted UNCHANGED beside it, which is the half a
bump could quietly take with it.

`test_the_reliability_sentence_is_the_packet_s_own` is new, and it exists because the fixture
packet in that file is entirely context-eligible, so `NON_SCORABLE` is the truthful sentence for
it and the existing assertion still passes. What was missing was any test that the **other** branch
exists at all. It now drives a scoring-eligible packet through the real renderer and asserts the
output says SCORABLE, says neither `NON_SCORABLE` nor `MISSING_RELIABILITY`, and still says
scoring-ready is not scored.

---

## What did not move

Preparation v4 is the pre-decision view and was **not rewritten**: it is superseded by v5 and
still on disk, still hashing to what Mission 1.83 measured, and the gate refuses a record claiming
otherwise. Mission 1.83's own gate still reads it, correctly, as the preparation of its day.

The first Opportunity is untouched at 1 hypothesis, 2 revisions and 14 evidence links. Q1 and the
Globalping arc are unchanged. The candidate selection is unchanged. No source review was appended,
no condition was verified, no eligibility state moved. Every canonical research counter is
identical to the section 1 preconditions, measured against the live database rather than quoted.

---

## Verification

`ruff format --check` and `ruff check` clean over 975 files. `mypy` clean over 199 source files
across the 14 CI package paths. Contracts, rendered catalog and review results all in sync. Source
registry validation passed: 29 sources, 45 evidence records, 0 warnings. **All 64 CI gates run
green locally**, the new one included. 3785 bare-python tests across 9 packages; 3431 pytest tests,
with the database reported unchanged across 29 tenant tables.

---

## Next

**One operator decision, and it is not this mission's to take.**
`SECOND-OPPORTUNITY-SYNTH-EXEC-V1` version 1, digest
`570657e1a862a96742925f6a5e5a17b0e1860bf9f2f0b8315fa33c560496da92`, is frozen and unapproved.
Approving it authorises exactly one model call, on one provider route, with one prompt, under one
cost ceiling, retaining what the record names and nothing else.

If it is approved, **Mission 1.84.1 — Second Opportunity Synthesis Execution V1** performs exactly
one inference, runs the eight ordered validation stages, and persists an Opportunity hypothesis
**only** if every gate accepts it *and* a named human has reviewed the output. If it is refused,
nothing here is wasted: the payload, the prompt and the contract stay frozen and the record says
which act was declined.

**Do not execute the model without that approval**, do not widen the purpose, do not transmit
another packet, and do not treat a passing gate as a reason to skip the human.
