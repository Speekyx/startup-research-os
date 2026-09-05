# First Deterministic Inferred Pilot — Write Manifest V1

**Mission 1.56 — First Deterministic Inferred Claim Persistence Pilot V1 — recorded 2026-09-05. Status: AWAITING_OPERATOR_APPROVAL.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_inferred_pilot.py`.

**SHA-256 `7545b5aaa240cd397dba0fcc08be11f2d84bd87448d10f7aaf165e941b6b4add`**

One attended canonical write. One threshold registration, one evaluator execution over frozen inputs, and one persistence transaction down whichever path the evaluator's own result selects. Nothing else.

*deliberately. §14 forbids it, because a manifest that already knew the answer would be a manifest written around it.*

## The target proposition

> The change in content requests for the English Wikipedia article Kubernetes, from requester class user over all access channels, between the UTC days 2024-03-03 and 2024-03-04, is at least 1000 requests.

| fact | value |
| --- | --- |
| `proposition` | `metric_threshold_state` |
| `claim_type` | `INFERRED` |
| `canonical_subject_id` | `kubernetes` |
| `metric_definition_id` | `content_request_daily_change:en.wikipedia.org:user:all-access` |
| `time_bound` | `2024-03-03/2024-03-04` |
| `population_or_geography` | `global` |
| `unit` | `requests` |
| `threshold_operator` | `GTE` |
| `threshold_value` | `1000` |

Key `e452cf18200011aa65da75ebea5a0036bd49b2a365612dc3bbb2db8963ba2684`, recomputed from these facts by the validator.

Carries no `source_id`, `measurement value`, `direction`, `signal id`.

## The Signal

- `signal_id`: 064d12bf-e7bb-56e7-a90c-bdd08e89d2ac
- `source_id`: wikimedia-pageviews
- `measurement_value`: 912
- `unit`: requests
- `period_labels`: ['2024-03-03', '2024-03-04']
- `content_id`: Kubernetes
- `audience_class`: user

*the deterministic (source_id, signal_id) tie-break of §5, applied after all 18 members of the passing family tied on every preference criterion*

## The threshold registration

`GTE 1000 requests`, provenance **POST_HOC**, recorded by `thibchm`.

**Why POST_HOC.** SROS has held this measurement since Mission 1.19. PREREGISTERED requires `threshold.recorded_at < measurement.retrieved_at`, which no threshold recorded today can satisfy against an already-held measurement. §7 makes that explicit and POST_HOC is the honest classification.

PREREGISTERED attempted: **False**. It is not merely unavailable, it is impossible by construction for held data, and recording it would assert that this system did not hold the measurement when the bound was frozen -- which is false and checkable.

- SOURCE_NATIVE: Rejected. Wikimedia publishes counts and no threshold, so nothing in the source's measurement contract supplies this bound.
- EXTERNAL_NORM: Rejected. The project holds no reviewed external norm defining a request-change threshold for an encyclopedia article.
- UNKNOWN: Rejected. The origin and timing of this bound are perfectly well established -- an operator chose it today -- and §7 forbids using UNKNOWN to avoid recording POST_HOC honestly.

**The disclosure that matters.** The measurement value 912 was visible before the bound was chosen, because it has been held since Mission 1.19 and the candidate inventory read it. That is unavoidable for held data and is exactly why POST_HOC exists. The bound sits ABOVE the measurement, so the pilot cannot be read as fitted to produce a favourable result -- and both directions were acceptable before it was chosen.

### PREREGISTERED is not merely unavailable, it is arithmetically impossible

ADR-037 §23. PREREGISTERED requires `threshold.recorded_at < witness.retrieved_at`, and the evaluator enforces it at gate 3.

- measurement retrieved at `2026-09-01T21:03:47.090178+00:00`
- threshold recordable no earlier than 2026-09-05, the day this manifest was written. The row does not exist yet and will be recorded later still.

`recorded_at < retrieved_at` is false at every instant at which this bound could be recorded. So a PREREGISTERED label would be REFUSED with PREREGISTRATION_TIMING_INCONSISTENT rather than silently downgraded -- which means POST_HOC is not the cautious choice here, it is the only representable one.

Calibration eligible **False**. POST_HOC changes calibration eligibility and never logical entailment. Whatever the evaluator concludes is as true as the arithmetic makes it.

## Equivalence

Basis `first-deterministic-inferred-pilot-equivalence-v1`, verdict **EQUIVALENT**, 8 dimensions, interpretation confidence **0.9**, reviewed by `thibchm`.

## Allowed persistence paths

| if the evaluator returns | path | writes |
| --- | --- | --- |
| `SUPPORTS`, `CONTRADICTS` | **DIRECTIONAL** | `research.claims`, `research.claim_revisions`, `scoring.evidence`, `research.claim_derivations` |
| `NOT_APPLICABLE`, `UNKNOWN` | **REFUSAL** | `research.proposition_evaluation_refusals` |

**All four results are legitimate. Success is not defined as SUPPORTS.**

## Canonical mutation envelope

`threshold_registrations` **+1**, then exactly one of:

| counter | directional max | refusal max |
| --- | --- | --- |
| `claims` | +1 | +0 |
| `claim_revisions` | +1 | +0 |
| `evidence` | +1 | +0 |
| `claim_derivations` | +1 | +0 |
| `proposition_evaluation_refusals` | +0 | +1 |

Every other counter: **unchanged**. On violation: `PILOT_MUTATION_ENVELOPE_VIOLATION, and the mission stops`.

## What this pilot will not do

- create a ReliabilityAssessment -- the new five-field INFERRED scope will resolve NO_APPLICABLE_ASSESSMENT and the Evidence will be NON_SCORABLE, which is the correct outcome
- copy, inherit or default any reliability value
- create a calibration label or change REFERENCE_PROFILE_V1
- persist any Score or change any ranking
- create an EvidenceIndependenceGroup
- attach anything to the existing Opportunity
- mark UNATTENDED_PRODUCTION_READY true
- acquire data, select a source, or call a model
- run a second candidate

## The limitation the operator should weigh

**`SOURCE_INDEPENDENCE_IS_PARTIAL`.** Only Wikimedia's own logs can measure requests to a Wikipedia article, so this proposition can never accumulate an independent second witness. The pilot proves the canonical path end to end; it does not demonstrate the multi-witness value ADR-036 was built for.

World Bank population change is the one held family naming a quantity that exists independently of any measurer. It was excluded because the source publishes NO unit for SP.POP.TOTL -- `unit_state = NOT_PUBLISHED` -- and inferring `persons` is forbidden. Fixing that needs documentation this mission may not fetch.

## Approval

    APPROVE MISSION 1.56 PILOT 7545b5aaa240cd397dba0fcc08be11f2d84bd87448d10f7aaf165e941b6b4add

Until approved: threshold_registrations stays 0 and no canonical row is written.

