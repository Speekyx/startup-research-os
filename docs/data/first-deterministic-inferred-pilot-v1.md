# First Deterministic Inferred Pilot — Execution Record V1

**Mission 1.56 — First Deterministic Inferred Claim Persistence Pilot V1 — executed 2026-09-05. Status: EXECUTED.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_inferred_pilot.py`.

## Approval

Manifest SHA-256 `7545b5aaa240cd397dba0fcc08be11f2d84bd87448d10f7aaf165e941b6b4add`, approved by `thibchm`.

The operator approved a specific document. This record names its hash so a later reader can check that the manifest in the repository is the one that was approved, rather than a manifest that agrees with this record.

*Its status still reads AWAITING_OPERATOR_APPROVAL, deliberately. Marking it APPROVED would change its bytes and therefore its hash, and a frozen document that no longer answers to the hash it was frozen at is not frozen.*

## The evaluator returned `CONTRADICTS`

> Measurement 912 requests does not satisfy the bound >= 1000 registered as POST_HOC, under equivalence basis first-deterministic-inferred-pilot-equivalence-v1.

Refusal reason **None**, calibration eligible **False**, evaluations **1**, re-runs with adjusted inputs **0**, model calls **0**, network requests **0**.

Proposition key `e452cf18200011aa65da75ebea5a0036bd49b2a365612dc3bbb2db8963ba2684`.

## The bound

`5df908f7-123a-4913-b7a1-2a5f07255e97`, provenance **POST_HOC**, recorded 2026-09-05T07:38:38.351865+00:00 by `thibchm`, created by this run **True**.

Phase A commits before the evaluator is constructed, so the bound was not chosen while the measurement was being compared against it.

## What was written

|  | value |
| --- | --- |
| `path` | `DIRECTIONAL` |
| `status` | `PERSISTED` |
| `claim_id` | `c79f58bb-2241-4908-800b-5765a51cbb95` |
| `claim_revision_id` | `6fdef1b1-fc4f-4406-bd7e-e8a633d8a7a2` |
| `derivation_id` | `52dbc32b-56ff-4e0c-9ebc-efe0740b4aec` |
| `evidence_id` | `800f1421-dcef-4656-9c2a-e3bef039282d` |
| `refusal_id` | `None` |
| `claim_created` | `True` |
| `derivation_created` | `True` |
| `evidence_created` | `True` |
| `refusal_created` | `False` |
| `conflict` | `None` |

## The replay

Status **REUSED**, rows created **0**.

Running the whole evaluation and persistence again changed nothing. Idempotency is demonstrated rather than asserted.

## Counters

| counter | before | after | after replay |
| --- | --- | --- | --- |
| `raw_records` | 325 | 325 | 325 |
| `normalized_records` | 325 | 325 | 325 |
| `signals` | 33 | 33 | 33 |
| `claims` | 43 | 44 | 44 |
| `claim_revisions` | 44 | 45 | 45 |
| `evidence` | 57 | 58 | 58 |
| `reliability_assessments` | 4 | 4 | 4 |
| `threshold_registrations` | 0 | 1 | 1 |
| `claim_derivations` | 0 | 1 | 1 |
| `proposition_evaluation_refusals` | 0 | 0 | 0 |
| `opportunities` | 1 | 1 | 1 |
| `opportunity_revisions` | 1 | 1 | 1 |
| `opportunity_evidence_links` | 7 | 7 | 7 |
| `embeddings` | 0 | 0 | 0 |
| `sources` | 29 | 29 | 29 |

INFERRED Claims **0 -> 1**.

## What this run did not do

- create a ReliabilityAssessment -- the new five-field INFERRED scope will resolve NO_APPLICABLE_ASSESSMENT and the Evidence will be NON_SCORABLE, which is the correct outcome
- copy, inherit or default any reliability value
- create a calibration label or change REFERENCE_PROFILE_V1
- persist any Score or change any ranking
- create an EvidenceIndependenceGroup
- attach anything to the existing Opportunity
- mark UNATTENDED_PRODUCTION_READY true
- acquire data, select a source, or call a model
- run a second candidate

## The limitation, restated after the fact

**`SOURCE_INDEPENDENCE_IS_PARTIAL`.** Only Wikimedia's own logs can measure requests to a Wikipedia article, so this proposition can never accumulate an independent second witness. The pilot proves the canonical path end to end; it does not demonstrate the multi-witness value ADR-036 was built for.

