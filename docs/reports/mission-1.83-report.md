# Mission 1.83 — Three gates were already open, and the fourth was never asked

**Outcome: `TED_EGRESS_REVIEW_READY_FOR_OPERATOR_DECISION`.**

The selected procurement candidate cannot reach synthesis because one field in one source
review reads `NOT_ASSESSED`. This mission asked what the held authority establishes about
changing that, reconstructed the exact object that would leave, and stopped. It appended no
review, recorded no approval and called no model. What it produced is a frozen decision packet,
`TED-EGRESS-OPPSYNTH-V1`, whose digest an operator approval would have to cite.

The finding underneath is that the blocker is smaller than it looks and is not a documentary
gap. A model may already read this material, the profile already permits this class of egress,
and the provider posture is already approved on its own contract text. What is missing is an
answer to a question nobody put.

---

## Report

```
START_COMMIT                = 5a543e1        BRANCH = sprint-1/mission-1.83
MIGRATION_HEAD              = 0036_grant_use_profile_vocabulary (measured)

SELECTED_SUBJECT            = ted-eu:CPV-class:9261
SELECTED_LABEL              = Sports facilities operation services
SELECTED_PACKET             = e218b56a8f938f4d5f7fc961e7f0c2cfe184c4396395334140c6199b48316592

CURRENT_TED_REVIEW_ID       = 7fbbe3ce-37d5-56c6-8be7-655cf212ef64
CURRENT_TED_REVIEW_VERSION  = 3
CURRENT_TED_PROFILE         = local-private-research-v1
CURRENT_TED_APPROVAL_STATE  = APPROVED_WITH_CONDITIONS
EXTERNAL_MODEL_TRANSMISSION_BEFORE = NOT_ASSESSED

PROCESSING_PURPOSE          = bounded external inference for Opportunity hypothesis synthesis

REPRESENTATION_SCHEMA       = opportunity-transmission-representation@1.0.0
REPRESENTATION_SHA256       = 2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72
CLAIM_COUNT                 = 5              CHARACTER_COUNT = 3604
RAW_PAYLOAD_PRESENT         = false          PERSONAL_DATA_PRESENT = false
NOTICE_BODY_PRESENT         = false

MODEL_TRAINING              = NOT_ASSESSED   FINE_TUNING = NOT_ASSESSED
EMBEDDINGS                  = NOT_ASSESSED

HELD_AUTHORITY_COUNT        = 7
NEW_DOCUMENTATION_FETCHES   = 0              RESEARCH_DATA_FETCHES = 0

COMMERCIAL_REUSE            = PERMITTED
DERIVED_ANALYTICS           = PERMITTED
EXTERNAL_MODEL_TRANSMISSION = NOT_ASSESSED, and this mission does not answer it
MODEL_INFERENCE             = PERMITTED
PUBLIC_REDISTRIBUTION       = NOT_PERMITTED

ATTRIBUTION_REQUIRED        = true
ATTRIBUTION_CONDITIONS      = source acknowledgement per Article 6(2)(a), already satisfied as a
                              property of the payload; no boilerplate injected
DERIVED_OUTPUT_STATUS       = PERMITTED_AS_A_NEW_WORK_SUBJECT_TO_THE_REUSE_CONDITIONS

HUMAN_JUDGEMENT_REQUIRED    = true
OPERATOR_DECISION_PACKET_CREATED = true
DECISION_PACKET_ID          = TED-EGRESS-OPPSYNTH-V1
DECISION_PACKET_VERSION     = 1
DECISION_PACKET_SHA256      = f27c34460f413def15c260e72fd2261a1fba666b574e9e2ee60bf7ef38a39577

SOURCE_REVIEW_APPENDED      = false
EXTERNAL_MODEL_TRANSMISSION_AFTER = NOT_ASSESSED

MODEL_CALLS = 0   OPPORTUNITY_CREATED = 0   CANONICAL_RESEARCH_MUTATION = 0
VIOLATIONS_CAUGHT / ESCAPED = 42 / 0        positive controls 7 of 7
PRIMARY_OUTCOME             = TED_EGRESS_REVIEW_READY_FOR_OPERATOR_DECISION
NEXT_ACTION                 = the operator answers TED-EGRESS-OPPSYNTH-V1
```

Preconditions verified: tree clean, `main` == `origin/main` at `5a543e1`, Mission 1.82 merged
as PR #141 recording `PROCUREMENT_SEMANTIC_SUBJECT_CANDIDATE_SELECTED` with egress review
required, and every canonical counter re-measured against the live database rather than carried
from the last report.

## The blocker is one field, and three of four gates are already open

ADR-033 keeps four questions apart, and this mission's first act was to read all four rather
than the one the brief named.

| question | field | where | state |
|---|---|---|---|
| may a model READ this material? | `model_processing` | TED review v3 | **PERMITTED** |
| may it LEAVE this deployment? | `external_model_transmission` | TED review v3 | **NOT_ASSESSED** |
| what does the processor DO with it? | provider posture | provider register | **APPROVED** |
| does this deployment permit that egress? | `external_model_egress` | the local profile | **PERMITTED_TO_APPROVED_PROVIDERS** |

The reading permission is not open-ended. Condition 9 of that review scopes machine processing
to inference, extraction, classification and structured analysis, states that training was not
assessed and is not authorised, and records embeddings as unassessed and separately blocked. The
profile says the same thing from the other side, with `model_inference` true and `model_training`
and `embeddings` false.

So the object that refuses is a single unanswered field, and the live gate says so in its own
words: the packet is `UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS` for exactly one reason, and that reason
ends *"an open question an operator can close, not a prohibition"*.

## What would leave, measured rather than described

The packet was reconstructed through the current deterministic preparation path and the bytes
were produced by the production serializer rather than by a copy of it. The decision object
handed to that function was a measurement fixture, never persisted and never transmitted; the
real gate was evaluated separately and refuses, and both facts are in the record.

| measure | value |
|---|---|
| packet id | `e218b56a…`, the current preparation's |
| evidence rows | 6 |
| claim statements | 5 |
| characters | 3604 |
| representation violations | 0 |
| personal-data fields | 0 |

Nine top-level keys, all inside the production allowlist, and 28 leaf values in total. Scanning
every leaf found no email address, no telephone number, no postal code, no URL, no notice
identifier and no free-text body. **The payload carries the CODE and not the label** Mission 1.82
retrieved, which follows from that mission's own rule: a label is display metadata and the code
is the identity.

**The character count was recomputed and it changed.** Mission 1.82 recorded 3252; the figure
now is 3604. That mission measured a stand-in payload, substituting a placeholder for the
packet's real dimension-bound sentence and serializing compactly where the production function
uses indented, sorted output. Neither difference changes what would be sent, because nothing was
sent, and both change the number. The Mission 1.82 record was **not** rewritten: it says what it
measured, and this record is the pointer.

## What the held authority establishes, and where it stops

Seven documents, no new fetch, and the reason no fetch would help is mechanical rather than a
judgement about effort. Commission Decision 2011/833/EU was read in full in Mission 1.15.2 and
re-retrieved on 2026-09-04, and the held text contains **zero** occurrences of *processor*,
*transmit*, *transfer*, *sub-licence* and *automated*. Its two occurrences of *third part* are
the Article 2(2)(b) intellectual-property exclusion. **The instrument enumerates no acts at
all**, which is exactly why H-34 closed PERMITTED, and it is why a further first-party page
cannot address an act the framework does not speak in.

Four arguments point toward permission and each is recorded as insufficient alone.

- **Reuse is defined by purpose.** Article 3(2) enumerates no acts, so method does not enter.
  That establishes method is not a bar. It does not establish that a new counterparty is not one.
- **The publisher answered in writing.** Case 2026-COP-201 states that TED notices and metadata
  may be reused for commercial and non-commercial purposes provided the source is acknowledged,
  that the database-copyright question should not prevent reuse, and that retrieval method is
  not relevant. The retrieval sentence answers **acquisition**, and reading it as covering egress
  would answer this mission's question with a sentence that was not addressed to it.
- **The object carries no TED text.** Five sentences this repository composed about aggregates,
  naming no notice, no buyer and no supplier. A bounded representation lowers exposure and does
  not answer whether the act is within the grant.
- **A processor is not the public.** So the re-utilisation limb is not obviously engaged, and
  *not obviously engaged* is the honest phrasing rather than a finding.

## Two things defeat mechanical closure, and one of them is the operator's own sentence

**The acceptance is scoped to bounded queries, in the operator's words.** The current v3
verification reads *"I accept the residual database-right exposure for bounded queries through
the authorised official routes under `local-private-research-v1`, review v3."* A transmission to
a third party is not a bounded query, and it reaches a new counterparty with an exposure that is
still open. Mission 1.29 made this argument against the v2 acceptance and refused to record a
TED egress decision on the strength of it. The 2026-09-04 reply made the residual **smaller** and
left the acceptance's scope exactly where its author wrote it. This repository may not widen a
human acceptance on the operator's behalf.

**The instrument does not address the act.** Moving from an act-free grant to
`PERMITTED_WITH_CONDITIONS` is a reading, and a reading is judgement. H-36A is still not
established in either direction, the reply is the publisher's guidance rather than an
adjudication, and the legal notice disclaims being legal advice in its own words.

So the project's own rule applies: an objective property of configuration is verified
mechanically, and a legal conclusion or a risk acceptance is confirmed by a person.

## What was not done

No source review was appended. **Launching a review mission is authorization to investigate and
never authorization to grant the result**, and approval is not inferred from the mission having
been launched. No reviewer is recorded, no option is defaulted, and the frozen packet records no
approval inside itself, so the bytes an operator reads will not move when they answer.

Nothing was widened in passing. Training, fine-tuning and embeddings each keep the state they
have; the record says explicitly that an inference decision widens none of them, and the reason
is condition 9's own: training raises the third-party-rights question in a materially different
form and the engine does not need it. Redistribution and customer-facing access stay
`NOT_PERMITTED`, and the commercial profile is recorded as out of scope rather than left to be
inferred.

Attribution was neither injected nor dropped. The obligation is real, it maps onto Article
6(2)(a) as asserted by the publisher's reply, and it is **already met**: three of the five
statements open *"Tenders Electronic Daily (EU public procurement) reported that"* and two open
*"The source \"ted-eu\" published"*. Adding licence boilerplate would change the bytes an approval
would name in order to assert what the payload already says.

## The decision packet

`TED-EGRESS-OPPSYNTH-V1`, version 1, digest
`f27c34460f413def15c260e72fd2261a1fba666b574e9e2ee60bf7ef38a39577`. The digest binds the packet
id and version, the source, the profile, the activity, the purpose, the subject, the packet id,
the representation schema and digest and boundary, the eight negative states, the conditions,
the held authority, the open questions and the option **names**. It excludes itself, the
preparation date and the option prose, so recording an approval beside the packet does not move
it, and re-wording an explanation cannot pass as a re-hash of the same decision.

Eight conditions travel with any permission, and the provider condition names a **property**
rather than a vendor: a source review states what a provider must commit to, and the provider
register decides which providers commit to it. Three options are offered, each with its cost
stated, and **none is defaulted**. The cost of permitting is written down rather than discovered
later: appending a review version orphans the v3 condition verifications, including the
`HUMAN_CONFIRMATION` acceptance, so TED becomes ineligible until the operator records it again.

## Adversarial probe

Forty-two deliberate violations and seven positive controls, each mutating a shipped record byte
for byte and restoring it afterwards.

```
VIOLATIONS_CAUGHT = 42    VIOLATIONS_ESCAPED = 0    CONTROLS = 7 of 7
```

**The controls found a real defect in this mission's own gate.** Two of them describe a world in
which the authority settles the activity mechanically, and both were refused, because the gate
demanded a residual unconditionally: *"nothing is recorded as defeating mechanical closure, yet
the outcome asks a person"*. A gate that can only ever say *ask a person* would force a future
mechanical finding to be recorded as something it is not. The requirement is now conditional in
**both** directions, which is stricter than what it replaced: a record may not name a residual
that defeats closure while also recording that no judgement is required.

Two other checks were restructured for the same reason before the probe ran. A representation
that fails its contract and a payload carrying unexpected personal data are each one of the seven
acceptable outcomes, so the gate refuses a violation beside an outcome that claims none, and a
violation outcome with nothing wrong, rather than refusing the state outright.

## Verification

All 62 CI gates pass, one of them new. `ruff format --check` and `ruff check` are clean, mypy
reports no issues across the CI package paths, and contract generation and the source catalog
both pass `--check`. The bare-python runner reports 3696 tests across 9 packages. The pytest
suites report 3393 passed across the same 9 packages, with the database unchanged across 29
tenant tables. Canonical counters were measured before and after and are identical.

## Next

**The operator answers `TED-EGRESS-OPPSYNTH-V1`.** Nothing in this repository can answer it, and
no further reading would change that.

- **PERMIT_WITH_EXACT_CONDITIONS** leads to **Mission 1.83.1 — TED Egress Operator Decision
  Persistence V1**, which must verify the packet digest before writing a review successor, and
  must also re-record the operator's acceptance, because appending orphans it.
- **DEFER** leaves the field `NOT_ASSESSED` and the candidate's synthesis route closed. Nothing
  else is blocked by it.
- **REFUSE** records a decision rather than an open question, and parks this candidate's external
  synthesis route.
