# Mission 1.56 — First Deterministic Inferred Claim Persistence Pilot V1

**Outcome: `FIRST_DETERMINISTIC_INFERRED_CLAIM_PERSISTED`.**
One attended write, approved against a frozen manifest hash, and the evaluator
returned **`CONTRADICTS`**.

---

## 0. The result in one paragraph

Signal `064d12bf-e7bb-56e7-a90c-bdd08e89d2ac` measured **912** requests. The
registered bound was **`GTE 1000`**. So the target proposition — *the change in
content requests for the English Wikipedia article Kubernetes, requester class
`user`, all access channels, between the UTC days 2024-03-03 and 2024-03-04, is
at least 1000 requests* — is **refuted by its own witness**.

That is the pilot succeeding. §1 of the brief forbids defining success as
SUPPORTS, the manifest declared all four evaluator results legitimate before the
evaluation ran, and a pilot that could only have succeeded one way would have
been measuring the threshold rather than the measurement.

## 1. What moved

    threshold_registrations           0 -> 1
    claims (INFERRED)                 0 -> 1
    claim_revisions                  44 -> 45
    evidence                         57 -> 58
    claim_derivations                 0 -> 1
    proposition_evaluation_refusals   0 -> 0
    every other counter                  unchanged

`raw_records`, `normalized_records`, `signals`, `reliability_assessments`,
`opportunities`, `opportunity_revisions`, `opportunity_evidence_links`,
`embeddings` and `sources` are all exactly where they were. No migration. The
evaluator and the orchestrator were not touched.

## 2. The first `CONTRADICTS` row, and the case that is still unreached

Both halves belong in the same sentence.

Mission 1.48 measured all 57 Evidence rows, found every one `SUPPORTS`, and
established why: `direction` is proposition identity at the OBSERVED layer, so an
interpreter there cannot emit a contradicting row about a Claim it already
restated. `EvidenceDirection.SUPPORTS` appears exactly once in the interpreters
package as a hard-coded literal, and `CONTRADICTS` appears nowhere. ADR-036
removes direction from identity at the INFERRED layer. The census now reads:

    SUPPORTS      57
    CONTRADICTS    1

**And the contradiction CASE is still unreached.** Contradiction enters the
aggregation arithmetic when ONE Claim carries evidence in both directions.
`claims_carrying_both_directions` is **0**. This Claim has one witness, and it can
never have a second: only Wikimedia's own logs can measure requests to a
Wikipedia article. That is the `SOURCE_INDEPENDENCE_IS_PARTIAL` limitation, and
it was disclosed to the operator **before** approval rather than explained
afterwards.

Reporting the first half alone would say the contradiction machinery has run. It
has not. What changed is that the direction became expressible.

## 3. The approval, and why the manifest was not edited afterwards

The operator typed `APPROVE MISSION 1.56 PILOT 7545b5aa…`. `run_inferred_pilot.py`
recomputes the SHA-256 of the canonical manifest and refuses anything else —
demonstrated by a run against a deliberately wrong hash, which wrote **0 rows**.

**The manifest still reads `AWAITING_OPERATOR_APPROVAL`, and that is deliberate.**
Marking it `APPROVED` would change its bytes and therefore its hash, and a frozen
document that no longer answers to the hash it was frozen at is not frozen. The
validator now refuses any other status for exactly that reason, and the CI gate
re-checks the hash recorded in the execution record against the manifest on disk
— so a later edit turns the gate **red** instead of leaving the word *approved*
beside a document nobody approved.

## 4. PREREGISTERED was impossible, not unchosen

ADR-037 §23 defines PREREGISTERED as `threshold.recorded_at < witness.retrieved_at`.

    measurement retrieved   2026-09-01T21:03:47.090178Z   (read from acquisition.raw_records)
    bound recordable        2026-09-05 at the earliest

So the relation is false at every instant at which this bound could be recorded.
A test hands the **real** evaluator a PREREGISTERED registration with exactly
these timings and gets `UNKNOWN / PREREGISTRATION_TIMING_INCONSISTENT` — refused
rather than silently downgraded, because a downgrade would repair somebody's
claim about when they decided.

`POST_HOC` is therefore not the cautious choice; it is the only representable one.

**The disclosure that matters** is written into the manifest rather than left out
of it: the value 912 was visible before the bound was chosen, because the
measurement has been held since Mission 1.19. For held data it always is, which
is exactly why POST_HOC exists. The bound sits **above** the measurement, so the
pilot cannot be read as fitted to produce a favourable result, and both
directions were acceptable before it was chosen.

Calibration eligibility is `false`, derived from the status by the real property
rather than copied — migration 0034 stores no `calibration_eligible` column
because two authorities for one fact eventually disagree. **Provenance changes
eligibility and never entailment**: 912 genuinely fails to reach 1000.

## 5. Ordering, and what it prevents

Phase A commits the threshold registration **before** the evaluator is
constructed. Registering a bound on the way past would be the analyst choosing
the number while the comparison is running, and `_require_threshold` in the
orchestrator already refuses a derivation citing a registration that does not
exist — so the failure would have been a write, not a refusal.

## 6. The statement, and the derivation's lineage

The Claim reads:

> content_request_daily_change:en.wikipedia.org:user:all-access for kubernetes
> over global in 2024-03-03/2024-03-04 is at least 1000 requests.

Composed from the target and nothing else, as Mission 1.55 designed. It names no
witness, no measurement and no source, so a second witness would append Evidence
rather than a ClaimRevision.

The derivation names the observation it reasoned from —
`97dec365-7ee8-4c93-947f-36fd9abf1d1b`, the detailed OBSERVED restatement — and
it was selected **structurally** rather than by a manifest field. The Signal
witnesses two OBSERVED Claims; the detailed one carries the same two day labels
the target does, and Mission 1.43's convergent existential deliberately carries
none, because there the labels are witness rather than identity. No field was
added to the manifest to encode a fact the rows already state.

## 7. Idempotency, demonstrated

The whole evaluation and persistence ran a second time: status **`REUSED`**, 0
rows created, every counter identical. That is checked in the run and re-checked
by the CI gate against the recorded counters.

## 8. No reliability was invented, and the near miss is the test

Through the **real** resolver, over all four current assessments and their real
basis rows: **`NO_APPLICABLE_ASSESSMENT`**, reliability `None`.

| assessment | value | shared | differs on |
|---|---|---|---|
| wikimedia `platform_counted_content_request_change` | 0.65 | 3 of 5 | `claim_type`, `proposition_kind` |
| wikimedia `…_change_witnessed` | 0.6 | 3 of 5 | `claim_type`, `proposition_kind` |
| ted-eu (two scopes) | 0.5, 0.55 | 0 of 5 | all five |

Both differences on the near miss are real: a threshold proposition is a
different question from a restatement of the count, and an INFERRED derivation is
a different question from an OBSERVED one. Reaching for the nearest number would
have answered neither.

Consequence: the Evidence is `NON_SCORABLE`, aggregation is `UNAVAILABLE`, no
score, no rank, `REFERENCE_PROFILE_V1` still `UNCALIBRATED`. **That is the
designed behaviour** — the system stays capable of producing no score, which is
what makes a score mean something when one appears.

## 9. A pre-existing defect, repaired rather than masked

Running the full pytest set surfaced a failure with nothing to do with this
mission. `test_ted_operator_acceptance.py` ran `fetchone()` with **no `ORDER BY`**
over the two residual-exposure acceptance rows (review v2 from Mission 1.15.6.1
and v3 from Mission 1.46) and asserted version 2 — so it passed or failed on
whichever row the planner returned first. Its sibling had already been re-pointed
for the second row; this one was missed.

It now asserts the property over **every** row — right source, right profile,
right condition, recorded by the operator, condition satisfied — plus that no two
review versions share a `verifier_version`, which is exactly what a replay of an
older acknowledgement would look like. Vacuous on an empty database, like its
sibling, because CI starts with no registry loaded.

## 10. What this run did not do

No acquisition, no source added, no second candidate, no threshold tweaked after
the outcome, no reclassification of POST_HOC, no ReliabilityAssessment, no
reliability copied or defaulted, no calibration, no Score, no ranking, no
Opportunity touched, no independence group, no embedding, no model call, no
network request, no migration, no change to the evaluator or the orchestrator,
`UNATTENDED_PRODUCTION_READY` still false, Problem-Family still PARKED.

## 11. Verification

| | |
|---|---|
| CI gates | 25, all green (8 validators, 17 render checks) |
| bare-python | 1400 tests across 9 packages |
| pytest | 3310 tests across 9 packages |
| validator probe | 76 deliberate violations, 76 caught, each by its own gate |
| approval guard | wrong hash refused, 0 rows written |

The probe counts only violations refused by the check they were written for. A
manifest mutation also invalidates the execution record's hash, so a probe that
accepted that as a pass would have measured one check 60 times — the shape
Mission 1.53 shipped once and recorded.

## 12. What comes next

**Not a second pilot, and not calibration.** A second candidate from the same
family would repeat this one exactly, and calibration is still blocked by the
arithmetic Mission 1.43 established: with one provenance group the full
aggregator is algebraically the pass-through baseline.

What this run makes newly answerable is the question Mission 1.48 could not ask.
The contradiction case now needs only **a second witness disagreeing about one
threshold proposition**, and the INFERRED layer is the first place in this
repository where two witnesses can reach one Claim at all. The target is an
**independence-capable evidence route** — unchanged since 1.78, and worth
strictly more than it was before this pilot ran.
