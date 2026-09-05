# Internet-Wide Service Presence — Gate Closure Baseline V1

**Mission 1.59 — Internet-Wide Service-Presence Route Gate Closure V1 — recorded 2026-09-05.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_service_presence_route.py`.

Mission 1.58 merged as PR #101 at `7cfcd88`, migration head `0035_refusal_provenance`, branch `sprint-1/mission-1.59`.

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

`SUPPORTS` **57**, `CONTRADICTS` **1**, Claims carrying both **0**.

## The route under evaluation — `ROUTE-D-INTERNET-WIDE-SERVICE-PRESENCE`

*Section 1. Mission 1.59 evaluates the route Mission 1.58 found. Swapping in a pair that is easier to document would be answering a different question and calling it closure.*

**Censys** (Censys, Inc.) — the Censys Platform host dataset and its search API.

- construct: hosts and the services observed on them across the public IPv4 space
- scan model: its own scanners attempt a small number of connections to every IPv4 address, then complete protocol handshakes

**Netlas** (Netlas.io) — the Netlas responses collection and its search API.

- construct: service responses captured while sweeping the IPv4 space against a curated port list
- scan model: its own purpose-built scanners, banner grabbing and protocol parsing across roughly thirty application-layer protocols

Product relevance: AUDIENCE_OR_USAGE and COMPETITIVE_SUPPLY, bounded by the sentence that a reachable host is not an installation, a customer, a user, a subscription, revenue, demand or adoption.

## Starting gate state

| gate | state |
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

Gates targeted: [3, 5, 10].

Section 34 forbids the governance review, and gate 12 is a governance question. It stays UNKNOWN by construction, which means no selection was reachable in this mission even before the epistemic work began. That is stated up front rather than discovered at the end.

## Documentation ledger

**8 of 12 requests used.** Measurement endpoints called **0**, measurement values fetched **0**, paid access purchased **0**.

|  | kind | target | sought | established |
| --- | --- | --- | --- | --- |
| 1 | SEARCH | `docs.netlas.io` | data update cycles and scan timestamp semantics |  |
| 2 | FETCH | `https://docs.netlas.io/knowledge-base/field-reference/responses/` | timestamp and observation-time semantics of response records | two temporal fields: @timestamp is the index time, scan_date is when the scanning activity that generated the response occurred. Each document is a single service response collected during scanning, keyed by (uri, ip): a discrete point-in-time observation rather than a merged state. |
| 3 | FETCH | `https://docs.censys.com/docs/platform-data-definitions` | host and service timestamp semantics | HTTP 404 |
| 4 | SEARCH | `docs.censys.com` | observed_at and last_updated_at semantics | observed_at marks when a service was obtained by a Censys scan and is NOT searchable, because service observation timestamps change too rapidly to publish. The searchable host-level last_updated_at reflects the time of the latest CHANGE, and a host observed daily for five days without change carries a last_updated_at from five days ago. |
| 5 | FETCH | `https://docs.censys.com/docs/platform-historical-data` | whether point-in-time snapshots are selectable | per-host timelines preserve a snapshot per scan and permit comparing two scan events, with access windows bounded by plan tier. This is per-host inspection, not an aggregate window selector. |
| 6 | FETCH | `https://docs.censys.com/docs/platform-host-dataset` | how the queryable dataset is constructed in time terms | the queryable dataset is a MERGED CURRENT STATE built from individual scans. host.services.scan_time marks when a service was LAST observed. No mechanism is documented for restricting an aggregate count to services observed within a specified past window. Under high density, service data represents a SAMPLING of service details. |
| 7 | FETCH | `https://www.rfc-editor.org/rfc/rfc4253` | the standard-defined protocol version exchange | RFC 4253 section 4.2: the server sends SSH-protoversion-softwareversion SP comments CR LF immediately on connection and before any negotiation, and other server output lines must not begin with SSH-. |
| 8 | FETCH | `https://docs.netlas.io/knowledge-base/` | an affirmative statement that host observations come from its own scanning | the index page carries no such statement, and it separates primary internet scan data from auxiliary enrichment drawn from DNS registries, WHOIS and certificate sources. |

**Target measurement retrieved: False.** Documentation pages describe record structure and field meanings. No page consulted stated a host count for any protocol, and no query was run.

