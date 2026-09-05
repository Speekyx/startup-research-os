# Broadened Apparatus Search V1

**Mission 1.58 — Broadened Apparatus Search V1 — recorded 2026-09-05.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_independence_route.py`.

Supersedes the selection in `docs/data/independence-capable-route-feasibility-v1.json`.

## The operator decision — `WITHDRAW_ROUTE_A_AND_BROADEN`

`ROUTE-A-ATMOSPHERIC-CO2-FIXED-SITE` withdrawn by `thibchm`: *the route does not serve the product*.

**What this changes.** Mission 1.57 recorded subject relevance as a PREFERENCE, because its own brief listed it under preferences and omitted it from the selection rule. The operator has made it BINDING. That is a rule change, not a correction: Mission 1.57's reasoning was sound under the rule it was given, and its selection was flagged with exactly this reservation before approval was sought.

**What it does not change.**

- the structural finding, which is about where measurement occurs and is unaffected by which route is preferred
- the negative controls, which still fail
- the independence proof standard
- the FRAME_INSIDE_THE_DEFINITION trap
- the value-inspection rule

*It passed every gate it was measured against, and its epistemic analysis stands. What changed is which gates apply. Recording it as an error would misdescribe both the analysis and the decision.*

## The amended gate set

15 gates carried forward, 1 added.

### Gate 16 — `PRODUCT_RELEVANCE`

The measured construct must bear on at least one Opportunity dimension this system already defines. A route that exercises the aggregation machinery on a quantity the product will never research proves the mechanism and calibrates nothing transferable.

**How it is checked.** The construct must map to a named dimension in the existing vocabulary -- AUDIENCE_OR_USAGE, COMPETITIVE_SUPPLY, MARKET_ACTIVITY, PROBLEM_OR_NEED, ECONOMIC_VALUE, BUYER_OR_BUDGET_EXISTENCE -- with the bound sentence that dimension requires. A construct mapping to nothing fails.

**What it costs.** It is a real narrowing, and it may make the conjunction empty. Mission 1.57 established that product-relevant quantities are overwhelmingly platform-mediated and platform-mediated quantities are measured once. This gate intersects that finding directly, and the honest possibility is that very few routes survive both.

## The conjunction

**A quantity that (a) exists independently of any single measurer, (b) has at least two documented independent measurement apparatuses, and (c) bears on an Opportunity dimension.**

Mission 1.57's law says (a) rules out everything a platform records, and (c) is mostly satisfied by exactly the things platforms record. The two conditions pull in opposite directions, and the search is for the intersection rather than for a good source.

## Classes surveyed

| class | world quantity | two apparatuses | dimension | verdict |
| --- | --- | --- | --- | --- |
| `INTERNET_WIDE_ACTIVE_SCANNING` | YES | YES | AUDIENCE_OR_USAGE and COMPETITIVE_SUPPLY | **PURSUED** |
| `WEB_CRAWL_TECHNOLOGY_SURVEYS` | YES | PARTIALLY | AUDIENCE_OR_USAGE | **REJECTED** |
| `PACKAGE_AND_REGISTRY_DOWNLOADS` | NO | NO | AUDIENCE_OR_USAGE | **REJECTED** |
| `CERTIFICATE_TRANSPARENCY_LOGS` | YES | NO | COMPETITIVE_SUPPLY | **REJECTED** |
| `JOB_POSTINGS_AND_VACANCY_STATISTICS` | YES | YES | MARKET_ACTIVITY | **REJECTED** |
| `BUSINESS_REGISTERS_AND_COMPANY_FORMATION` | NO | NO | COMPETITIVE_SUPPLY | **REJECTED** |
| `APP_STORE_AND_PLATFORM_CATALOGUES` | NO | NO | COMPETITIVE_SUPPLY | **REJECTED** |

- **`INTERNET_WIDE_ACTIVE_SCANNING`** — The internet is the object, not a publisher. Nobody publishes how many hosts run a service, so every apparatus must generate the number by probing -- which is what makes two of them two MEASUREMENTS rather than two copies.
- **`WEB_CRAWL_TECHNOLOGY_SURVEYS`** — Each crawler defines its own site population -- a top-N list from one ranking, or its own crawl frontier -- so the frame sits inside the metric definition. FRAME_INSIDE_THE_DEFINITION again, and one prominent crawler takes its origin list from a single platform's dataset, which is a common upstream for the FRAME even where the crawling is independent.
- **`PACKAGE_AND_REGISTRY_DOWNLOADS`** — A registry's own download log is the only apparatus that can measure downloads from that registry. Every derived statistics service consumes it, which is common upstream. Source-exclusive in the Mission 1.56 sense.
- **`CERTIFICATE_TRANSPARENCY_LOGS`** — Several independent log operators, and they carry the SAME certificate submitted to each. Reading a published value from two places is not measuring it twice.
- **`JOB_POSTINGS_AND_VACANCY_STATISTICS`** — An official employer survey measures VACANCIES and a postings index measures POSTINGS. Genuinely independent producers of two different constructs, which is section 24's trap: independence without the same proposition is useless.
- **`BUSINESS_REGISTERS_AND_COMPANY_FORMATION`** — One authoritative register per jurisdiction, and every aggregator consumes it. The register is the upstream producer, exactly as the national statistical institute is for population.
- **`APP_STORE_AND_PLATFORM_CATALOGUES`** — Platform-exclusive by construction, and the platforms are governance-restricted here in any case.

## The new trap — `READING_A_PUBLISHED_VALUE_IS_NOT_MEASURING_IT`

Two apparatuses that each retrieve an authoritative published record are two READINGS of one fact, not two measurements. Measurement requires that the apparatus GENERATE the value by interacting with the world, so that two apparatuses can legitimately disagree.

It is the sharpest available test for this whole search, and it is the reason the scanning class works where every earlier candidate failed. Ask: if the two apparatuses disagree, is that a fact about the world or a bug? For two readers of one published number, a disagreement is a bug. For two scanners probing the internet, a disagreement is a real difference in coverage, timing or fingerprinting -- which is exactly what independent corroboration is supposed to tolerate.

*Found by: certificate transparency logs, which look like many independent witnesses and are many copies of one submission.*

## The candidate — `ROUTE-D-INTERNET-WIDE-SERVICE-PRESENCE`

> the number of publicly reachable IPv4 hosts responding on a defined TCP port with a protocol-defined service banner, observed within a defined reference window

Unit `hosts`, frame the public IPv4 address space, excluding reserved and special-use ranges. Dimension: AUDIENCE_OR_USAGE, with the bound sentence that a reachable host is not an installation, a customer or a user.

### Why the independence argument is structural here

Population figures have an upstream PRODUCER -- the national statistical institute measures once and everyone else distributes. Host counts have none. Nobody publishes how many hosts run a service, so there is no common upstream measurement available to be republished, and each apparatus must generate its value by probing.

**Consequence.** The failure mode that killed World Bank plus FRED, World Bank plus Eurostat, and every platform pair is not merely absent here; it is structurally unavailable.

*Still to document.* That neither service ingests the other's scan data. Both describe their own infrastructure; one states its provenance affirmatively and the other does so only by omission.

### Gate results

| gate | verdict |
| --- | --- |
| `1_same_external_construct` | **PASS** |
| `2_exact_canonical_subject` | **PASS** |
| `3_metric_definition_compatibility` | **PASS_IF_NARROWED** |
| `4_unit_compatibility` | **PASS** |
| `5_time_compatibility` | **UNKNOWN** |
| `6_population_or_frame` | **PASS** |
| `7_each_alone_entails` | **PASS** |
| `8_no_shared_upstream` | **PASS** |
| `9_different_production` | **PASS** |
| `10_first_party_lineage_documentation` | **PARTIAL** |
| `11_reliability_reviewability` | **PASS** |
| `12_governance_feasibility` | **UNKNOWN** |
| `13_threshold_freezable` | **PASS** |
| `14_falsifiable_both_ways` | **PASS** |
| `15_structurally_useful` | **PASS** |
| `16_product_relevance` | **PASS** |

Each vendor's product fingerprinting is proprietary, so 'hosts running product X' is two different operational definitions and no deterministic equivalence is published. The route survives only if the construct is narrowed to something the PROTOCOL defines rather than the vendor -- a service responding on a defined port with a protocol-defined handshake. Both apparatuses document banner grabbing and protocol parsing, so the narrowed construct is available on both sides. Taking the vendor label instead would be the CPI-basket failure in a new domain.

### Open gates

**Gate 3.** a construct narrow enough that both apparatuses are measuring the same thing. Each vendor's product fingerprinting is proprietary, so 'hosts running product X' is two operational definitions with no published equivalence between them.

*Closable by:* freezing the construct on what the PROTOCOL defines -- a service responding on a defined port with a protocol-defined handshake -- which both sides document as banner grabbing and protocol parsing, rather than on a vendor product label

**Gate 5.** a documented reference window on apparatus B. Two snapshot censuses of a continuously changing population need a shared definition of 'as of when', and one side publishes its cadence while the other's cadence article was not retrievable.

*Closable by:* retrieving one named first-party document -- the 'Data Update Cycles' article -- and establishing whether each record carries an observation timestamp and whether a calendar-day snapshot is defined

**Gate 12.** a policy review for both apparatuses, and for apparatus A a paid commercial licence. Terms for apparatus B were not retrieved.

*Closable by:* the ordinary source-registration and local-private-research-v1 review, plus a purchasing decision

**Gate 10.** an affirmative first-party statement from apparatus B that it does not ingest third-party scan data

*Closable by:* further first-party documentation, or written enquiry

**Selected: False.** Three gates are open and the gate set is conjunctive. Mission 1.57's own rule -- a pair qualifies only if ALL mandatory gates pass -- is not weakened because this route is the best one found and because the operator asked for a broadened search to produce something. Selecting on twelve of sixteen would be exactly the outcome-chasing this whole arc has refused.

## Outcome — `PRODUCT_RELEVANT_INDEPENDENCE_CLASS_IDENTIFIED_GATES_OPEN`

Broadening the search found one class that satisfies the full conjunction -- a world quantity, two documented independent apparatuses, and a real Opportunity dimension -- and no route in it qualifies yet. Three gates are open, each named, each closable by a bounded next step, and none of them is epistemic in the way that killed every previous candidate.

No route is selected. Section 46 of the Mission 1.57 rules permits selection only when every mandatory gate passes, and three do not.

## What broadening bought

**Before.** The only route passing every gate measured a quantity the product will never research, and the honest reading was that inside this portfolio there was no alternative.

**After.** There is an alternative, and it is outside the portfolio. It is product-relevant, its independence rests on a STRUCTURAL asymmetry rather than on a documentary coincidence, and what blocks it is a retrievable document, a policy review and a purchase.

**The asymmetry worth carrying forward.** Nobody publishes how many hosts run a service. That single fact is what makes two scanners two measurements, and it is a better independence argument than any pair of organisational statements -- because it cannot be undone by one of the two changing its data-sourcing policy.

Mission 1.57 said platform-recorded quantities are measured once. That stands. What this mission adds is the complement: a quantity is independently measurable exactly when NO party is in a position to publish it authoritatively, and the internet as a whole is such a quantity even though every host on it belongs to somebody.

## Counters

| counter | value |
| --- | --- |
| `research_data_requests` | **0** |
| `first_party_method_doc_requests` | **7** |
| `governance_doc_requests` | **1** |
| `measurement_values_fetched` | **0** |
| `model_calls` | **0** |
| `embeddings` | **0** |
| `canonical_mutations` | **0** |
| `sources_registered` | **0** |
| `reviews_created` | **0** |
| `collectors_implemented` | **0** |
| `threshold_registrations_created` | **0** |
| `claims_created` | **0** |
| `evidence_created` | **0** |
| `reliability_assessments_created` | **0** |
| `independence_groups_created` | **0** |
| `scores_created` | **0** |
| `opportunity_changes` | **0** |
| `mission_1_56_claim_modified` | **False** |
| `reference_profile` | **UNCALIBRATED** |
| `problem_family` | **PARKED** |

## Next — Mission 1.59 — Internet-Wide Service-Presence Route Gate Closure V1

Mission 1.57 recommended governance first for a route whose epistemics were closed. Here the epistemics are NOT closed: gate 5 decides whether the two apparatuses measure one proposition at all. Buying a licence for a route that then fails time alignment would be paying to discover a semantic problem.

It should:

- retrieve apparatus B's data-update-cycle documentation and establish whether a defined reference window and per-record observation timestamp exist
- retrieve apparatus B's data-use terms
- seek an affirmative first-party statement from apparatus B about third-party scan data, and record UNKNOWN if none is found
- freeze the narrowed protocol-defined construct, or report that it cannot be narrowed without a vendor fingerprint
- re-run all sixteen gates and either select or report which remain open

It must not:

- fetch a measurement value, a host count or a result count, which would destroy the PREREGISTERED classification permanently
- accept a vendor product label as the metric definition
- treat an absence of a reference to third-party data as an affirmative statement
- register a source or create a review, which belongs to the governance mission after the epistemics close

