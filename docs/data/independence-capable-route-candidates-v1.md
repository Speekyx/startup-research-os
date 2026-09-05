# Independence-Capable Route — Candidates V1

**Mission 1.57 — Independence-Capable Evidence Route Feasibility V1 — recorded 2026-09-05.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_independence_route.py`.

## The registered portfolio

**29 sources registered**, 8 with a local review, 21 without one. Eligible with no outstanding condition: `eurostat`, `fred`, `world-bank`, `ted-eu`.

*Governance was read for completeness. It is not what decided this mission, and saying so matters: the binding constraint turned out to sit upstream of every governance question.*

## The 10 held apparatuses

| source | record kind | proposition kind | measures |
| --- | --- | --- | --- |
| `gdelt` | `lexical_frequency_observation` | `source_reported_term_frequency_change` | occurrences of a lexical term in GDELT's own news ngram stream |
| `gdelt` | `lexical_frequency_observation` | `source_reported_term_frequency_contrast` | relative occurrence of two terms in GDELT's own ngram stream |
| `stack-exchange` | `community_question` | `community_site_published_questions_carrying_tag` | questions published on Stack Overflow carrying a site tag |
| `stack-exchange` | `community_question` | `community_site_questions_without_accepted_answer` | the subset of those whose asker accepted no answer |
| `ted-eu` | `procurement_notice` | `source_reported_procurement_value_contrast` | published award totals in a CPV cohort |
| `ted-eu` | `procurement_notice` | `source_published_classification_value_contrast_witnessed` | the existential over such cohorts |
| `wikimedia-pageviews` | `content_request_count` | `platform_counted_content_request_change` | day-over-day change in requests to a named article |
| `wikimedia-pageviews` | `content_request_count` | `platform_counted_content_request_change_witnessed` | the existential over such changes |
| `wikimedia-pageviews` | `content_request_count` | `metric_threshold_state` | the Mission 1.56 INFERRED threshold proposition |
| `world-bank` | `numeric_observation` | `source_reported_metric_period_change` | period change in a WDI indicator |

**Exactly ONE subject is observed by two apparatuses, and it is the same one Mission 1.47 found: docker.**

## The one held pair

`wikimedia-pageviews / platform_counted_content_request_change` against `stack-exchange / community_site_published_questions_carrying_tag`, on `docker`.

**Verdict `COMPLEMENTARY_NOT_CORROBORATING`.** A content request is something a READER's client makes of a server. A published question is something a PERSON writes about being stuck. These are two phenomena, and the only proposition admitting both is one that names neither -- which is the near-tautology Mission 1.47 already constructed and refused.

*The Opportunity engine's own mapping rationale, written in Mission 1.30, already says PROBLEM_OR_NEED and AUDIENCE_OR_USAGE are different questions and neither implies the other.*

ADR-036 removed the identity blocker that stopped these two ever reaching one Claim. It did not make a request a question.

## Negative controls

| control | verdict | gates failed | basis |
| --- | --- | --- | --- |
| `world_bank_plus_fred` | **DEPENDENT_REPUBLICATION** | 8 | Mission 1.46, from FRED's own metadata: Source World Bank, Release World Development Indicators, Source Code SP.POP.TOTL, and a suggested citation reading 'World Bank ... retrieved from FRED'. |
| `world_bank_plus_eurostat` | **COMMON_UPSTREAM_SOURCE and SEMANTIC_MISMATCH** | [5, 6, 8] | Mission 1.46, from both publishers' own documentation: the World Bank's indicator metadata lists Eurostat among its sourceOrganization entries, and Eurostat's ESMS metadata states population data are collected from National Statistical Institutes under Regulation (EU) No 1260/2013. Separately, the World Bank counts the de facto population at midyear and Eurostat the usually resident population on 1 January. |
| `wikimedia_alternative_publication_route` | **SAME_MEASUREMENT_UPSTREAM** | 8 | The metric is generated from Wikimedia's own request logs. Any dump, wrapper, mirror or dashboard republishes that one measurement. |
| `vendor_quoting_a_republisher` | **DEPENDENT_REPUBLICATION** | 8 | Section 26. Two vendors publishing one price both taken from the official feed are one measurement. |

## Bounded external discovery

Required **True**. Research-data requests **0**, methodology-document requests **6**, measurement values fetched **0**.

| apparatus class | two independent processes plausible | why |
| --- | --- | --- |
| `PHYSICAL_ATMOSPHERIC_QUANTITY_AT_A_FIXED_SITE` | **YES** | Separate instruments, separate laboratories and separate calibration scales can sample the same air. |
| `SHARE_OF_WEB_TRAFFIC_BY_TECHNOLOGY` | **NO** | Each apparatus measures share WITHIN ITS OWN NETWORK, so the frame sits inside the metric definition. |
| `NATIONAL_POPULATION_STOCK` | **NO** | Mission 1.46's structural finding: the measurement happens once, at the national producer, and international publishers are distribution layers over it. |
| `GEOPHYSICAL_EVENT_MAGNITUDE` | **YES** | Separate seismic station networks compute magnitude for one event from separate inputs. |
| `CONSUMER_PRICE_LEVEL` | **PARTIALLY** | An official agency basket and an independently collected online price index use separate inputs, and they measure different baskets under different weighting. Section 25's trap applies before independence is even reached. |

## Candidate routes

### `ROUTE-A-ATMOSPHERIC-CO2-FIXED-SITE`

Metric: dry-air mole fraction of carbon dioxide at the site, monthly mean. Unit `ppm (micromole of CO2 per mole of dry air)`. Provenance relation **KNOWN_INDEPENDENT**. Semantic verdict **EQUIVALENT_WITH_A_STATED_SCALE_LIMITATION**.

**Independence basis.**

- apparatus B's own site states that it operates an independent sampling network rather than obtaining data from apparatus A
- apparatus A's own methodology page describes apparatus B's data as independent and uses it for comparison, and comparison for validation is not consumption
- the two report on DIFFERENT calibration scales, which is the sharpest available evidence that neither is a republication of the other: a republished series would carry the originator's scale
- separate instruments and separate analysis laboratories are documented on both sides

*Limitation.* The two programmes share the SITE, and apparatus A provides in-kind field support there. That is a shared LOCATION and shared logistics, not a shared measurement: two instruments sampling the same air produce two measurements. But it means their ERRORS are not independent -- a site-level artefact would move both -- and provenance independence is not error independence. This belongs in the eventual reliability review and in the Claim's stated limitations, not in the independence verdict.

**Blockers.**

- neither apparatus is a registered source
- no local-private-research-v1 review exists for either
- no collector and no normalizer exists for either
- the record kind a mole-fraction observation would need does not exist

### `ROUTE-B-WEB-TECHNOLOGY-SHARE`

Metric: share of observed web activity attributable to the technology. Unit `percent`. Provenance relation **UNKNOWN**. Semantic verdict **NOT_EQUIVALENT**.

**Why rejected.** Suppose the independence proof were assembled and passed. It would still not rescue the route. Apparatus A's own documentation states its statistics describe activity ONLY on its own network, and apparatus B measures only traffic reaching its own infrastructure. So each measures 'share within my own reach', the frame sits inside the metric definition, and the only proposition admitting both would define the event class as a disjunction of the two networks -- which relocates source attribution from the subject of the sentence into its predicate. Mission 1.47 found exactly this shape once, and a proposition that LOOKS source-independent and is not is worse than one that is openly attributed.

*A second, independent failure.* Apparatus B publishes under a non-commercial licence. This deployment is local and its purpose is commercial, and local deployment never implies non-commercial use. Recorded separately so the semantic failure is not read as the only one.

### `ROUTE-C-NATIONAL-POPULATION-STOCK`

Metric: resident population stock at a reference date. Unit `persons`. Provenance relation **UNKNOWN**. Semantic verdict **NOT_ESTABLISHED**.

**Why rejected.** Two reasons, and the first is sufficient. Its lineage could not be documented first-party in this mission, and section 15 forbids recording independence on partial evidence -- so the honest verdict is UNKNOWN, and section 46 forbids selecting a route whose independence is UNKNOWN. Independently, the held evidence points the other way: Mission 1.46 established from the publishers' own metadata that international population figures are built from national producers' data, which is common upstream rather than a second measurement. Nothing here overturns that.

## Decision matrix

| criterion | `A` | `B` | `C` |
| --- | --- | --- | --- |
| `SAME_SUBJECT` | PASS | PASS | PASS |
| `SAME_METRIC` | PASS | FAIL | UNKNOWN |
| `SAME_UNIT` | PASS | PASS | PASS |
| `SAME_TIME` | PASS | PASS | UNKNOWN |
| `SAME_POPULATION` | PASS | FAIL | UNKNOWN |
| `EACH_ALONE_EVALUATES_FULL_CLAIM` | PASS | PASS | PASS |
| `FALSIFIABLE` | PASS | PASS | PASS |
| `NO_LATENT_BRIDGE` | PASS | FAIL | UNKNOWN |
| `MEASUREMENT_LINEAGE_A_DOCUMENTED` | PASS | PASS | PASS |
| `MEASUREMENT_LINEAGE_B_DOCUMENTED` | PASS | UNKNOWN | FAIL |
| `NO_DIRECT_REPUBLICATION` | PASS | UNKNOWN | UNKNOWN |
| `NO_COMMON_UPSTREAM_MEASUREMENT` | PASS | UNKNOWN | UNKNOWN |
| `INDEPENDENCE_ESTABLISHED` | PASS | UNKNOWN | UNKNOWN |
| `RELIABILITY_REVIEWABLE_A` | PASS | PASS | PASS |
| `RELIABILITY_REVIEWABLE_B` | PASS | UNKNOWN | UNKNOWN |
| `GOVERNANCE_A` | UNKNOWN | UNKNOWN | UNKNOWN |
| `GOVERNANCE_B` | UNKNOWN | FAIL | UNKNOWN |
| `THRESHOLD_PREREGISTRABLE` | PASS | PASS | PASS |
| `STRUCTURALLY_IDENTIFYING` | PASS | FAIL | PASS |
| `SEMANTICALLY_USEFUL` | PASS | FAIL | UNKNOWN |

GOVERNANCE_A and GOVERNANCE_B read UNKNOWN for Route A rather than FAIL because neither apparatus is registered and no review exists. That is an unasked question, not a refusal, and section 29 forbids creating the review here.

