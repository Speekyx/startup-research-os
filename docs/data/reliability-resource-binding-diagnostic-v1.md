# Which registered resource produced this measurement?

Generated from `reliability-resource-binding-diagnostic-v1.json`. Do not edit by hand.

**UNCALIBRATED · DIAGNOSTIC_ONLY · NOT_AN_OPPORTUNITY_SCORE**

Measured 2026-09-09T20:30:45+00:00 by `mission-1.77`, nothing written.

## The rule

- resource: the ONE distinct acquisition.raw_records.provenance.resource_id reachable through nlp.signal_inputs.raw_record_id for the Evidence row's Signal
- record kind: the ONE distinct nlp.signal_inputs.record_kind_id for the Signal
- ambiguity: zero distinct resources -> NONE_LINEAGE_ABSENT; more than one distinct resource or record kind -> NONE_LINEAGE_AMBIGUOUS; either way no scope is built and the resolver reports that the row cannot state its scope

## Where identifiers are persisted

| table | identifier | rows carrying it | rows |
|---|---|---|---|
| `scoring.evidence` | `source_id` | 58 | 58 |
| `research.claims` | `proposition_facts.resource_id` | 17 | 44 |
| `nlp.signals` | `scope.resource_id` | 0 | 33 |
| `nlp.signal_inputs` | `record_kind_id` | 260 | 260 |
| `nlp.signal_inputs` | `raw_record_id` | 260 | 260 |
| `acquisition.normalized_records` | `provenance.resource_id` | 0 | 325 |
| `acquisition.normalized_records` | `collector_id` | 325 | 325 |
| `acquisition.raw_records` | `provenance.resource_id` | 325 | 325 |
| `acquisition.raw_records` | `collector_id` | 325 | 325 |
| `acquisition.raw_records` | `collector_version` | 325 | 325 |
| `acquisition.raw_records` | `provenance.authorization_issued_at` | 325 | 325 |

## Per scope, the real resolver twice

| source | proposition kind | rows | on Opportunity | via claim facts | via lineage | reliability |
|---|---|---|---|---|---|---|
| `gdelt` | `source_reported_term_frequency_change` | 2 | 0 | 0 | 0 | — |
| `gdelt` | `source_reported_term_frequency_contrast` | 1 | 0 | 0 | 0 | — |
| `stack-exchange` | `community_site_published_questions_carrying_tag` | 1 | 1 | 0 | 0 | — |
| `stack-exchange` | `community_site_questions_without_accepted_answer` | 1 | 0 | 0 | 0 | — |
| `ted-eu` | `source_published_classification_value_contrast_witnessed` | 6 | 0 | 6 | 6 | 0.55 |
| `ted-eu` | `source_reported_procurement_value_contrast` | 6 | 0 | 6 | 6 | 0.5 |
| `wikimedia-pageviews` | `metric_threshold_state` | 1 | 0 | 0 | 0 | — |
| `wikimedia-pageviews` | `platform_counted_content_request_change` | 18 | 6 | 0 | 18 | 0.65 |
| `wikimedia-pageviews` | `platform_counted_content_request_change_witnessed` | 18 | 0 | 0 | 18 | 0.6 |
| `world-bank` | `source_reported_metric_period_change` | 4 | 0 | 0 | 0 | — |

Rows 58, exactly one lineage resource on 58, ambiguous 0, absent 0. Resolved via claim facts 12, via lineage 48; Opportunity-linked 0 → 6.

## Aggregation, read-only

Profile `REFERENCE_PROFILE_V1` (UNCALIBRATED), 34 Claims, 0 differing from reliability pass-through, 0 with established independence, persisted: False.

## Counters

| counter | before | after |
|---|---|---|
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
| opportunities | 1 | 1 |
| opportunity_revisions | 1 | 1 |
| opportunity_evidence_links | 7 | 7 |
| threshold_registrations | 1 | 1 |
| claim_derivations | 1 | 1 |
| proposition_evaluation_refusals | 0 | 0 |
| embeddings | 0 | 0 |
| scores_table | ABSENT | ABSENT |
