# Mission 1.83.1 — The operator answered, and the registry did exactly what they said

**Outcome: `TED_EGRESS_PERMITTED_WITH_CONDITIONS_AND_ELIGIBILITY_RESTORED`.**

The operator approved `TED-EGRESS-OPPSYNTH-V1` version 1 by its digest, adopting all eight frozen
conditions and accepting the residual exposure for one bounded scope. This mission verified the
approval against the packet rather than trusting it, appended a review successor rather than
editing v3, re-pointed the compliance configuration by performing the re-check, and re-recorded
both human confirmations from the operator's own words.

Every gate now passes and **zero bytes left the machine**. A permission is a gate state, not an
act.

---

## Report

```
START_COMMIT                = 78ce9d0        BRANCH = sprint-1/mission-1.83.1
MIGRATION_HEAD              = 0036_grant_use_profile_vocabulary (measured)

DECISION_PACKET_ID          = TED-EGRESS-OPPSYNTH-V1
DECISION_PACKET_VERSION     = 1              VERSION_UNCHANGED = true
DECISION_PACKET_SHA256 stated / recomputed  = f27c3446… / f27c3446…, and they agree
PACKET_EDITED               = false          approval_recorded on the packet = false
ACCEPTANCE_SHA256           = ea589bba5f8be85e1052f205a4b94301c1d0cef9f8ccc93c747015ce820a6908

REPRESENTATION_SHA256 approved / re-measured = 2528a56a… / 2528a56a…, unchanged

REVIEW_BEFORE / AFTER       = v3 / v4        V3_CONTENT_CHANGED = false
ASSESSMENTS_MOVED           = 1 (external_model_transmission)
external_model_transmission = absent in v3, resolving NOT_ASSESSED  ->  PERMITTED_WITH_CONDITIONS
CONDITIONS                  = 18 -> 28       REQUIRED_CONDITIONS = 4 -> 5
OPEN_QUESTIONS              = 7 -> 10
CONDITION_ADDED             = ted-external-model-transmission-accepted (HUMAN_CONFIRMATION)

COMPLIANCE_PINNED           = 3 -> 4, by performing the re-check
CAPABILITY_CONDITIONS_BYTE_IDENTICAL = true

CONDITIONS_SATISFIED        = 5 of 5   (3 CAPABILITY, 2 HUMAN_CONFIRMATION)
HUMAN_CONFIRMATIONS_RECORDED = 2, resting on 1 operator statement
VERIFIER_VERSION            = ted-v4-egress-approval-v1

ELIGIBILITY                 = BLOCKED -> ELIGIBLE
SOURCE_TRANSMISSION         = PERMITTED_WITH_CONDITIONS
PROFILE_EGRESS              = PERMITTED_TO_APPROVED_PROVIDERS
PROVIDER_POSTURE            = APPROVED
INFERENCE_AUTHORIZATION     = AUTHORIZED
SELECTED_PACKET_GATE        = UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS -> AVAILABLE
BYTES_TRANSMITTED           = 0

MODEL_TRAINING = NOT_ASSESSED   FINE_TUNING = NOT_ASSESSED   EMBEDDINGS = NOT_ASSESSED
PUBLIC_REDISTRIBUTION = NOT_PERMITTED   CUSTOMER_FACING_SOURCE_DATA = NOT_PERMITTED
COMMERCIAL_PROFILE = REQUIRES_REVIEW, unchanged and not inherited

MODEL_CALLS = 0   OPPORTUNITY_CREATED = 0   CANONICAL_RESEARCH_MUTATION = 0
SOURCE_REVIEWS              = 70 -> 71, the one append
VIOLATIONS_CAUGHT / ESCAPED = 52 / 0        positive controls 3 of 3
PRIMARY_OUTCOME             = TED_EGRESS_PERMITTED_WITH_CONDITIONS_AND_ELIGIBILITY_RESTORED
NEXT_MISSION                = 1.84 Second Opportunity Bounded Synthesis V1
```

## The approval was verified, not trusted

A quoted digest is recomputed and never copied. Copying it would make the approval name whatever
the message said rather than whatever the packet is, so both values are kept and the gate refuses
them disagreeing. The recomputation matched, the version was still 1, and the packet file's own
bytes still hashed to what the approval recorded.

**The packet was not edited.** Its `approval_recorded` still reads false, which means *this
document records no approval* and never that none exists. The approval lives beside it, because
marking a frozen document approved changes the bytes that were approved.

**The acceptance is the operator's words.** Recorded verbatim, hashed, and required to name the
packet id, the recomputed digest, the decision, the subject and the representation digest. Nothing
was reworded, tidied or completed: the words accepted have to be exactly the words reviewed.

## Appended, never edited

The committed catalog was read out of git and compared review by review. Nine reviews before, ten
after, exactly one added, none removed, and **zero pre-existing reviews changed by a single byte**.
No other field of the source moved and no other source was touched. Review v3's `superseded_at`
went from null to a timestamp, which is the supersession mechanism rather than an edit.

**Exactly one assessment moved.** v3 does not declare `external_model_transmission` at all, so
absent meant unasked and the loader resolved it to `NOT_ASSESSED`. v4 declares
`PERMITTED_WITH_CONDITIONS`. Every other assessment is byte-identical, checked field by field.

The eight adopted conditions were carried into v4 **verbatim**, each labelled with the packet id,
version and digest it came from. A condition reworded on the way into the registry is a condition
the operator did not adopt.

**The new required condition is separate, not a widening.**
`ted-external-model-transmission-accepted` sits beside
`ted-database-right-residual-exposure-accepted` rather than replacing it, because that acceptance
was written for **bounded queries** through the authorised acquisition routes, and a transmission
to a processor is neither a query nor the same counterparty. Widening an existing human acceptance
to cover a new act is what Mission 1.83 refused to do on the operator's behalf; appending a second
condition is what doing it honestly looks like.

Three open questions were added, and each says what the permission does **not** resolve: H-36A is
still not established, the instrument still enumerates no acts and so still does not address
onward transmission, and whether this generalises to another packet is deliberately unanswered.

## The configuration was re-pointed by doing the re-check

A compliance configuration is pinned to a review version because a re-review can change what a
condition **means**. Bumping the number is honest only when the conditions the configuration
answers are unchanged, and that was asserted against the catalog rather than assumed: the three
capability conditions are byte-identical between v3 and v4, and the one condition v4 adds is
`HUMAN_CONFIRMATION`, which no configuration can answer and none here pretends to.

Had the successor added a capability condition, re-pointing would have verified something else.

## Five conditions, satisfied by two different kinds of act

| condition | kind | satisfied by |
|---|---|---|
| `ted-attribution` | CAPABILITY | `capability:source-attribution-display` |
| `ted-official-route-only` | CAPABILITY | `capability:source-route-binding` |
| `ted-personal-data-minimisation` | CAPABILITY | `capability:source-field-minimisation` |
| `ted-database-right-residual-exposure-accepted` | HUMAN_CONFIRMATION | `local-operator` |
| `ted-external-model-transmission-accepted` | HUMAN_CONFIRMATION | `local-operator` |

The machine pass reported both human conditions `UNKNOWN` and **left them untouched**, in its own
words: *a machine pass does not answer a human condition, and no longer clears one either*.

**Two rows rest on one statement, and the record says so.** The operator wrote one approval and it
covers both the database-right residual and the onward transmission. Splitting it into two invented
sentences would record two acts where there was one, so both rows carry the same text and the same
`verifier_version`, `ted-v4-egress-approval-v1`. That identifier names **which text** was signed,
and it is deliberately not the v3 one, which belongs to a materially different statement about a
materially different act.

## What the permission is, and what it is not

Every gate now passes, measured through the repository's own tooling. The selected packet's own
gate moved from `UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS` to `AVAILABLE`, and the representation was
re-measured after the append and is **identical** to the one the operator approved. An approval
naming a payload the repository no longer produces would be an approval of something else.

**Nothing was sent.** No packet was serialised for a provider, no request was composed, and zero
bytes left this machine. The next mission may transmit; this one records that it may.

Nothing was widened. Training, fine-tuning and embeddings each keep the state they had, and the
successor says so in a condition of its own. Redistribution and customer access stay
`NOT_PERMITTED`, and the commercial profile stays `REQUIRES_REVIEW` and does not inherit anything.
The operator's own list of ten things this does not authorise is carried whole into both the
approval record and the review.

## What did not move

Every canonical research counter is identical before and after. The only rows this mission wrote
are governance rows, and they are the point: one review, five conditions, five verifications.

```
RawRecords 325   NormalizedRecords 325   Signals 60   Claims 91   revisions 92
Evidence 112   assessments 4   independence groups 0   Opportunities 1
revisions 2   links 14   scores ABSENT   embeddings 0
source reviews 70 -> 71
```

## A known consequence, recorded rather than repaired

`docs/data/opportunity-preparation-v4.json` records every TED packet's egress block as
`UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS` with the `NOT_ASSESSED` reason. That was true when Mission
1.82 wrote it and is no longer the live state.

It was **not** regenerated. A historical preparation is never rewritten, which is why v1, v2 and v3
are byte-identical across four missions; the next preparation run writes v5, and it belongs to the
mission that needs it. Regenerating in passing would also change twenty-one packets' blocks as a
side effect of a governance act.

For the same reason the Mission 1.82 and Mission 1.83 records were left alone. Each says what it
measured at its own moment, and both remain true about that moment.

## Adversarial probe

Fifty-two deliberate violations and three positive controls, each mutating a shipped record byte
for byte and restoring it afterwards.

```
VIOLATIONS_CAUGHT = 52    VIOLATIONS_ESCAPED = 0    CONTROLS = 3 of 3
```

Most cases are shapes a **fabricated approval** would take: a copied hash, a moved version, an
edited packet with both digests re-pointed to hide it, an acceptance nobody wrote, an acceptance
edited after it was hashed, a verifier clearing a human condition, a review rewritten rather than
appended.

**The probe found its own defect first.** It rewrote the frozen packet on every case, which changes
its bytes, so the gate's file-digest check caught all three controls. A case that does not touch a
document must leave it alone, or the probe is testing its own serializer. Repaired, and the three
cases that legitimately edit the packet now re-point both digests, so the refusal has to come from
a rule about the content rather than from the outer guard.

**Then the controls found a real defect in the gate.** It hard-coded the five conditions this
repository happens to carry, so a successor adding none was unrepresentable, and worse, the gate
was asserting the state we are in rather than the property that matters. It now derives the set
from the catalog and checks the property: every condition v3 required survives, the record reports
exactly what the catalog carries, and a human condition is satisfied by a human.

**And a second over-constraint went with it.** The gate demanded that several human confirmations
rest on one statement, which forbids the legitimate case where an operator writes two. The flag is
not checkable on its own; the identifier for which text was signed is. One statement carries one
identifier, several carry several, and a record claiming one while pointing at two texts is now
refused too. That is stricter than the boolean it replaces, and it added two more refusal cases.

## Eleven test files were re-pointed, not deleted

Forty-three tests failed on the append, and every one of them was a tripwire this arc installed
for exactly this moment. They pinned a count, a mission name or a condition set that was true when
it was written.

- **`test_transmission_governance.py`** asserted TED's egress stays `NOT_ASSESSED`. What it
  protects is that Mission 1.29 recorded nothing and that no later mission recorded it without a
  person, so it now asserts that any review answering the activity carries a `HUMAN_CONFIRMATION`
  condition for it.
- **`test_ted_authorization_bootstrap.py`** asserted *exactly one* human decision remained. It now
  asserts that everything outstanding **is** a human decision, which survives however many there
  are, and the verification count follows the review.
- **`test_ted_operator_acceptance.py`**, **`test_effective_verification.py`**,
  **`test_cli_readiness_decisions.py`** and **`test_ted_search_api_collector.py`** each supplied
  one recorded decision, for the one human condition that existed. A fixture supplying one of two
  describes a deployment where the operator answered half the questions, and reports its own gap
  as a gate failure. Two helpers in `conftest.py` now derive the required and the human condition
  keys from the catalog, beside `current_review_version`, which exists for the same reason.
- **`test_ted_official_reuse_response.py`** asserted the condition set is *unchanged* across a
  bump. The property is that a bump never **drops** one; equality also says a review may never
  require anything more, which is a different and false claim.
- **`test_ted_local_private_research.py`** counted correspondence **citations** rather than
  documents. TED still carries exactly one correspondence document, and now three reviews cite it.
- **`test_inference_execution_boundary.py`** scanned refusals for the word *model*, and a
  condition key now contains it. The property is that acquisition is never refused for an
  **assessment** about model use, so a list of unsatisfied condition keys is exempt: it names what
  a person has not recorded, not what a review decided.

A test asserting a count forever is a test asserting the registry may never grow.

## Verification

All 63 CI gates pass, one of them new. `ruff format --check` and `ruff check` are clean, mypy
reports no issues across the CI package paths, and contract generation and the source catalog both
pass `--check`. The source registry validator passes over 29 sources. The bare-python runner
reports 3732 tests across 9 packages. The pytest suites report 3393 passed with the database
unchanged across 29 tenant tables.

## Next

**Mission 1.84 — Second Opportunity Bounded Synthesis V1.** Regenerate the preparation as v5 so the
egress blocks describe the live state, then run one attended bounded synthesis over the selected
packet through the approved route, under a frozen output gate, and persist an Opportunity
hypothesis only if that gate accepts it.

It must not transmit any packet other than the approved digest, widen the purpose, create
embeddings, train, fine-tune, score, rank or acquire research data.

**Permission makes synthesis reachable and does not make it correct.** The Evidence still
establishes market activity, buyer or budget existence and economic value, and still establishes no
demand, no willingness to pay and no unmet need.
