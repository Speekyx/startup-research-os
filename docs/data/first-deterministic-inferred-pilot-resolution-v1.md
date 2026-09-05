# First Deterministic Inferred Pilot — Downstream Resolution V1

**Mission 1.56 — First Deterministic Inferred Claim Persistence Pilot V1 — recorded 2026-09-05. Rows written: 0.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_inferred_pilot.py`.

Claim `c79f58bb-2241-4908-800b-5765a51cbb95`.

## The reliability scope

- `source_id`: wikimedia-pageviews
- `resource_id`: metrics/pageviews/per-article/en.wikipedia.org
- `record_kind_id`: content_request_count
- `claim_type`: INFERRED
- `proposition_kind`: metric_threshold_state

## Reliability — `NO_APPLICABLE_ASSESSMENT`

4 current assessments offered, resolved value **None**.

| assessment | value | fields shared | differs on |
| --- | --- | --- | --- |
| `d1afa4be` | 0.55 | 0 of 5 | `source_id`, `resource_id`, `record_kind_id`, `claim_type`, `proposition_kind` |
| `3de2af10` | 0.5 | 0 of 5 | `source_id`, `resource_id`, `record_kind_id`, `claim_type`, `proposition_kind` |
| `e2419f13` | 0.65 | 3 of 5 | `claim_type`, `proposition_kind` |
| `19e0ce16` | 0.6 | 3 of 5 | `claim_type`, `proposition_kind` |

The reviewed Wikimedia 0.65 shares source, resource and record kind with this scope. It differs on claim_type AND proposition_kind, and both halves are real: a threshold proposition is a different question from a restatement of the count, and an INFERRED derivation is a different question from an OBSERVED one. Reaching for the nearest number would have answered neither.

## Aggregation — `UNAVAILABLE`

Profile `reference-v1` (UNCALIBRATED), raw 1, scorable 0, non-scorable 1, support groups 0, contradiction groups 0, level 0, score None.

- missing: 800f1421-dcef-4656-9c2a-e3bef039282d: MISSING_RELIABILITY

Reliability is purpose-relative and resolved late from a reviewed assessment. None applies to this new scope, so the Evidence is NON_SCORABLE and the aggregation is UNAVAILABLE. That is the designed behaviour: the system stays capable of producing no score, which is what makes a score mean something when one appears.

## The direction that had never existed

| direction | rows |
| --- | --- |
| `CONTRADICTS` | 1 |
| `SUPPORTS` | 57 |

Claims carrying a contradiction: **1**. Claims carrying BOTH directions: **0**.

**What this settles.** Mission 1.48 measured 57 Evidence rows and found every one of them SUPPORTS, then established why: `direction` is proposition identity at the OBSERVED layer, so an interpreter there cannot emit a contradicting row about a Claim it already restated. The INFERRED layer removes direction from identity, and this is the first CONTRADICTS row in the repository.

**What it does NOT settle.** The CONTRADICTION CASE is still unreached. Contradiction enters the arithmetic when one Claim carries evidence in both directions, and this Claim carries one row. `claims_carrying_both_directions` is the counter to watch, and it is still 0. A second witness disagreeing about the SAME threshold proposition is what would move it, and this proposition can never have one -- only Wikimedia's logs can measure requests to a Wikipedia article, which is the SOURCE_INDEPENDENCE_IS_PARTIAL limitation the operator was asked to weigh before approving.

