# The current evidence surface, measured

Generated from `opportunity-evidence-breadth-audit-v1.json`. Do not edit by hand.

Measured from the live canonical deployment during Mission 1.76. Nothing was acquired and nothing was written.

## The one Opportunity

**subject:docker** — target actor `UNKNOWN_NOT_SUPPORTED`, market scope `GLOBAL`.

- **supported dimensions (2):** `AUDIENCE_OR_USAGE`, `PROBLEM_OR_NEED`
- **unsupported dimensions (12):** `BUYER_OR_BUDGET_EXISTENCE`, `COMPETITIVE_SUPPLY`, `DISTRIBUTION_SIGNAL`, `ECONOMIC_VALUE`, `FEASIBILITY_SIGNAL`, `MARKET_ACTIVITY`, `RECURRENCE_OR_FREQUENCY`, `REGULATORY_OR_STRUCTURAL_DRIVER`, `SOLUTION_DISSATISFACTION`, `SOLUTION_GAP`, `WILLINGNESS_TO_PAY`, `TREND_OR_CHANGE`

### Named limitations, in the record's own words

1. Every supporting Evidence row is ELIGIBLE_CONTEXT, NON_SCORABLE and MISSING_RELIABILITY: no reviewed reliability applies, so this hypothesis can contribute to no score.
2. independence_state is UNKNOWN for every supporting row. Two source families is diversity, never established independence, and the row count is not a count of independent findings.
3. market_scope is recorded GLOBAL because the column is NOT NULL and the evidence establishes no geography. Ontology V2 §4 defines GLOBAL as the ABSENCE of a geographic restriction; it is not a claim about a worldwide market.
4. The Stack Exchange count is a count of published questions, not of people, and not evidence that any two of them share a problem: that relation is PARKED (Mission 1.27).
5. The Wikimedia rows are day-over-day request differences under the platform's own heuristic requester class. Two of the six are decreases, and the calendar does not cancel.

## Evidence lineages

Breadth is a count of KINDS, not of rows. Ten lineages carry 58 rows.

| source | proposition kind | rows | claims | reliability written | on the Opportunity |
|---|---|---|---|---|---|
| `wikimedia-pageviews` | `platform_counted_content_request_change_witnessed` | 18 | 6 | 0 | 0 |
| `wikimedia-pageviews` | `platform_counted_content_request_change` | 18 | 18 | 0 | 6 |
| `ted-eu` | `source_published_classification_value_contrast_witnessed` | 6 | 4 | 0 | 0 |
| `ted-eu` | `source_reported_procurement_value_contrast` | 6 | 6 | 0 | 0 |
| `world-bank` | `source_reported_metric_period_change` | 4 | 4 | 0 | 0 |
| `gdelt` | `source_reported_term_frequency_change` | 2 | 2 | 0 | 0 |
| `stack-exchange` | `community_site_questions_without_accepted_answer` | 1 | 1 | 0 | 0 |
| `wikimedia-pageviews` | `metric_threshold_state` | 1 | 1 | 0 | 0 |
| `stack-exchange` | `community_site_published_questions_carrying_tag` | 1 | 1 | 0 | 1 |
| `gdelt` | `source_reported_term_frequency_contrast` | 1 | 1 | 0 | 0 |

## Reviewed reliability that exists

| source | proposition kind | resource | reliability |
|---|---|---|---|
| `ted-eu` | `source_published_classification_value_contrast_witnessed` | `notices/eforms-contract-and-award` | 0.55 |
| `ted-eu` | `source_reported_procurement_value_contrast` | `notices/eforms-contract-and-award` | 0.5 |
| `wikimedia-pageviews` | `platform_counted_content_request_change` | `metrics/pageviews/per-article/en.wikipedia.org` | 0.65 |
| `wikimedia-pageviews` | `platform_counted_content_request_change_witnessed` | `metrics/pageviews/per-article/en.wikipedia.org` | 0.6 |

## Held records that feed no signal

| source | record kind | collector | normalized | feeding no signal |
|---|---|---|---|---|
| `ted-eu` | `procurement_notice` | `ted-search-api` | 188 | 120 |
| `stack-exchange` | `community_question` | `stack-exchange-questions` | 104 | 16 |
| `wikimedia-pageviews` | `content_request_count` | `wikimedia-pageviews-per-article` | 21 | 0 |
| `gdelt` | `lexical_frequency_observation` | `gdelt-web-ngram` | 6 | 0 |
| `world-bank` | `numeric_observation` | `world-bank-indicators` | 6 | 0 |

## Governance under `local-private-research-v1`

**8 of 29 registered sources have a review under this profile.** An absent review is a refusal and never a reason to consult another profile.

| source | family | approval | blocking reasons | collector enabled |
|---|---|---|---|---|
| `eurostat` | economic_data | `APPROVED_WITH_CONDITIONS` | — | False |
| `fred` | economic_data | `APPROVED_WITH_CONDITIONS` | — | False |
| `gdelt` | news | `APPROVED_WITH_CONDITIONS` | review conditions not satisfied: gdelt-attribution | False |
| `openalex` | knowledge | `APPROVED_WITH_CONDITIONS` | review conditions not satisfied: openalex-contact-configured, openalex-spend-bounded | False |
| `stack-exchange` | forum | `APPROVED_WITH_CONDITIONS` | review conditions not satisfied: stack-exchange-attribution, stack-exchange-official-api-only, stack-exchange-personal-data-minimisation | False |
| `ted-eu` | public_procurement | `APPROVED_WITH_CONDITIONS` | — | True |
| `wikimedia-pageviews` | knowledge | `APPROVED_WITH_CONDITIONS` | review conditions not satisfied: wikimedia-aggregate-only, wikimedia-client-identification, wikimedia-official-api-only | False |
| `world-bank` | economic_data | `APPROVED_WITH_CONDITIONS` | — | False |

## Canonical baseline

| | |
|---|---|
| migration head | `0036_grant_use_profile_vocabulary` |
| raw_records | 325 |
| normalized_records | 325 |
| signals | 33 |
| claims | 44 |
| claim_revisions | 45 |
| evidence | 58 |
| inferred_claims | 1 |
| threshold_registrations | 1 |
| claim_derivations | 1 |
| proposition_evaluation_refusals | 0 |
| reliability_assessments | 4 |
| evidence_independence_groups | 0 |
| opportunities | 1 |
| opportunity_revisions | 1 |
| opportunity_evidence_links | 7 |
| embeddings | 0 |
| registered_sources | 29 |
| use_profiles | 2 |


## Forward pointer

Appended by Mission 1.77; nothing above it changed. See `docs/data/wikimedia-measurement-scope-binding-v1.json`.

evidence_lineages.with_reliability counts the stored scoring.evidence.reliability column, which is NULL by design (ADR-026 Decision 2). Resolved late from lineage, 48 of the 58 rows carry a reviewed reliability and 6 of the 7 Opportunity-linked rows do. The audit's numbers were true of the column and were read as true of the corpus.
