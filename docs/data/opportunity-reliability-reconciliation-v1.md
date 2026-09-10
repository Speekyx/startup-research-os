# Opportunity reliability reconciliation — revision 2, by supersession

Generated from `opportunity-reliability-reconciliation-v1.json`. Do not edit by hand.

Opportunity `06113a8b-a83d-423d-8046-18f87d7dbc01` (`subject:docker`): revision 1 of 2026-09-02 stays as written; revision 2 of 2026-09-09 carries the same hypothesis over the same 7 cited rows with the stale reliability sentences replaced. Reason `RELIABILITY_APPLICABILITY_RECONCILIATION`.

## What Mission 1.77 made false, and what replaced it

| revision 1 | classification |
|---|---|
| Every supporting Evidence row is ELIGIBLE_CONTEXT, NON_SCORABLE and MISSING_RELIABILITY: no reviewed reliability applies, so this hypothesis can contribute to no score. | `STALE_DUE_TO_RELIABILITY_RESOLUTION_FIX` |
| independence_state is UNKNOWN for every supporting row. Two source families is diversity, never established independence, and the row count is not a count of independent findings. | `NOT_RELATED_TO_1_77` |
| market_scope is recorded GLOBAL because the column is NOT NULL and the evidence establishes no geography. Ontology V2 §4 defines GLOBAL as the ABSENCE of a geographic restriction; it is not a claim about a worldwide market. | `NOT_RELATED_TO_1_77` |
| The Stack Exchange count is a count of published questions, not of people, and not evidence that any two of them share a problem: that relation is PARKED (Mission 1.27). | `NOT_RELATED_TO_1_77` |
| The Wikimedia rows are day-over-day request differences under the platform's own heuristic requester class. Two of the six are decreases, and the calendar does not cancel. | `NOT_RELATED_TO_1_77` |

**Revision 2 limitations:**

1. 6 of 7 supporting Evidence rows carry a reviewed reliability (0.65), resolved late from their acquisition lineage and bound to the assessment that produced it (ADR-026, Mission 1.77); 1 remains NON_SCORABLE with no applicable assessment (stack-exchange). Scorable is not scored: REFERENCE_PROFILE_V1 is UNCALIBRATED, no Score exists in this repository, none is persisted, and no ranking exists.
2. independence_state is UNKNOWN for every supporting row. Two source families is diversity, never established independence, and the row count is not a count of independent findings.
3. market_scope is recorded GLOBAL because the column is NOT NULL and the evidence establishes no geography. Ontology V2 §4 defines GLOBAL as the ABSENCE of a geographic restriction; it is not a claim about a worldwide market.
4. The Stack Exchange count is a count of published questions, not of people, and not evidence that any two of them share a problem: that relation is PARKED (Mission 1.27).
5. The Wikimedia rows are day-over-day request differences under the platform's own heuristic requester class. Two of the six are decreases, and the calendar does not cancel.

## The cited rows, through the current resolver

| evidence | source | eligibility rev 1 → now | reliability | scorable | independence |
|---|---|---|---|---|---|
| `13a5eadb` | `wikimedia-pageviews` | ELIGIBLE_CONTEXT → ELIGIBLE_SCORING | 0.65 | True | UNKNOWN |
| `16a8c39c` | `stack-exchange` | ELIGIBLE_CONTEXT → ELIGIBLE_CONTEXT | — | False | UNKNOWN |
| `1b93db71` | `wikimedia-pageviews` | ELIGIBLE_CONTEXT → ELIGIBLE_SCORING | 0.65 | True | UNKNOWN |
| `487f62c6` | `wikimedia-pageviews` | ELIGIBLE_CONTEXT → ELIGIBLE_SCORING | 0.65 | True | UNKNOWN |
| `516182ff` | `wikimedia-pageviews` | ELIGIBLE_CONTEXT → ELIGIBLE_SCORING | 0.65 | True | UNKNOWN |
| `6cf92ad6` | `wikimedia-pageviews` | ELIGIBLE_CONTEXT → ELIGIBLE_SCORING | 0.65 | True | UNKNOWN |
| `f1e0b7a4` | `wikimedia-pageviews` | ELIGIBLE_CONTEXT → ELIGIBLE_SCORING | 0.65 | True | UNKNOWN |

In the current packet and not cited: 7 rows, each requiring a semantic judgement this reconciliation does not make.

## Census

| | |
|---|---|
| Evidence, total / scorable / non-scorable | 58 / 48 / 10 |
| linked, total / scorable / non-scorable | 7 / 6 / 1 |
| linked dimensions | `AUDIENCE_OR_USAGE`, `PROBLEM_OR_NEED`, `TREND_OR_CHANGE` |
| linked source families | forum, knowledge |
| linked reliability distribution | `{'0.65': 6, 'NONE': 1}` |
| linked independence | UNKNOWN |
| packet scoring-ready per contract | True — SufficiencyResult.scoring_ready = scoring_eligible_rows >= 2, a property of the PACKET; it authorises nothing, REFERENCE_PROFILE_V1 is UNCALIBRATED and no score is persisted |

## Counters

| counter | before | after |
|---|---|---|
| opportunities | 1 | 1 |
| opportunity_revisions | 1 | 2 |
| opportunity_evidence_links | 7 | 14 |
| raw_records | 325 | 325 |
| normalized_records | 325 | 325 |
| signals | 33 | 33 |
| claims | 44 | 44 |
| claim_revisions | 45 | 45 |
| evidence | 58 | 58 |
| evidence_reliability_written | 0 | 0 |
| reliability_assessments | 4 | 4 |
| reliability_assessment_basis_rows | 12 | 12 |
| independence_groups | 0 | 0 |
| threshold_registrations | 1 | 1 |
| claim_derivations | 1 | 1 |
| proposition_evaluation_refusals | 0 | 0 |
| embeddings | 0 | 0 |
| sources | 29 | 29 |
| source_reviews | 70 | 70 |
| scores_table | ABSENT | ABSENT |
