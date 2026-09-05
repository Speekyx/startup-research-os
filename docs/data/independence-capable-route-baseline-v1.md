# Independence-Capable Route — Baseline V1

**Mission 1.57 — Independence-Capable Evidence Route Feasibility V1 — recorded 2026-09-05.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_independence_route.py`.

## Precondition

Mission 1.56 merged as PR #99 at `6b7c8f4`, migration head `0035_refusal_provenance`, branch `sprint-1/mission-1.57`. ADR-036 / ADR-037 / ADR-038 all Accepted.

*Verified from git and the live database, not from the mission brief.*

## Counters

| counter | value |
| --- | --- |
| `raw_records` | **325** |
| `normalized_records` | **325** |
| `signals` | **33** |
| `claims` | **44** |
| `claim_revisions` | **45** |
| `evidence` | **58** |
| `inferred_claims` | **1** |
| `threshold_registrations` | **1** |
| `claim_derivations` | **1** |
| `proposition_evaluation_refusals` | **0** |
| `reliability_assessments` | **4** |
| `reliability_basis_rows` | **12** |
| `independence_groups` | **0** |
| `opportunities` | **1** |
| `opportunity_revisions` | **1** |
| `opportunity_evidence_links` | **7** |
| `embeddings` | **0** |
| `sources` | **29** |
| `scoring_scores` | **ABSENT** |
| `reference_profile` | **UNCALIBRATED** |
| `problem_family` | **PARKED** |
| `drift` | **none** |

## Evidence direction census

`SUPPORTS` **57**, `CONTRADICTS` **1**, Claims carrying both directions **0**.

The direction became representable in Mission 1.56 and the contradiction CASE has still not occurred. Contradiction enters the aggregation arithmetic only when one Claim carries evidence in both directions.

## The first INFERRED Claim

> content_request_daily_change:en.wikipedia.org:user:all-access for kubernetes over global in 2024-03-03/2024-03-04 is at least 1000 requests.

- `claim_id`: c79f58bb-2241-4908-800b-5765a51cbb95
- `claim_revision_id`: 6fdef1b1-fc4f-4406-bd7e-e8a633d8a7a2
- `proposition_key`: e452cf18200011aa65da75ebea5a0036bd49b2a365612dc3bbb2db8963ba2684
- `evidence_id`: 800f1421-dcef-4656-9c2a-e3bef039282d
- `evidence_direction`: CONTRADICTS
- `signal_id`: 064d12bf-e7bb-56e7-a90c-bdd08e89d2ac
- `threshold`: GTE 1000 requests, POST_HOC
- `derivation_id`: 52dbc32b-56ff-4e0c-9ebc-efe0740b4aec
- `input_observed_claim_id`: 97dec365-7ee8-4c93-947f-36fd9abf1d1b
- `measurement_value`: 912
- `reliability_resolution`: NO_APPLICABLE_ASSESSMENT
- `scorability`: NON_SCORABLE
- `provenance_groups`: 1

## Why it is not the route

**`SOURCE_EXCLUSIVE_METRIC`.** The metric is generated from Wikimedia's own request logs. A second Wikimedia endpoint, a dump, an API wrapper, a mirror, a republisher or a derived dashboard is another PUBLICATION of one measurement, not a second measurement. The number of publication routes is a fact about distribution and says nothing about how many times the quantity was measured.

*No alternative Wikimedia interface was searched for, and this Claim is not a candidate for a second witness.*

## What Mission 1.56 did and did not establish

Established:

- source-independent proposition identity works canonically, on a real row rather than a fixture
- EvidenceDirection.CONTRADICTS can exist on a real INFERRED Claim
- a future second witness can target the SAME proposition key, because source, measurement value and direction are all excluded from Claim identity
- the persistence path is real rather than fixture-only

Not established:

- independence
- corroboration
- aggregation conflict
- calibration
- anything about a market

## The two exits from the B-2 identity

**Corroboration.** one source-independent Claim, at least two supporting Evidence items, at least two ESTABLISHED independent provenance groups

**Contradiction.** one source-independent Claim, at least one SUPPORTS and at least one CONTRADICTS Evidence item

Two genuinely independent apparatuses measuring the SAME construct against the SAME frozen threshold produce corroboration if both measurements fall the same side and contradiction if they fall on opposite sides. The route does not have to predict which, which is exactly what keeps it free of outcome-chasing.

