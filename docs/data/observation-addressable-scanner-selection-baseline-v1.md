# Observation-Addressable Scanner Selection — Baseline V1

**Mission 1.60 — Observation-Addressable Scanner Pair Selection V1 — recorded 2026-09-05.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_scanner_pair_selection.py`.

Mission 1.59 merged as PR #102 at `b7fac0a`, migration head `0035_refusal_provenance`, branch `sprint-1/mission-1.60`.

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

## Carried forward

**Dropped:** Censys — `DROPPED_FOR_THIS_ROUTE`.

SNAPSHOT_TIME_SEMANTICS_NOT_ALIGNABLE. Its queryable dataset is a merged current state whose searchable time field records when a record last CHANGED, with the per-service observation time documented as unsearchable. Established from its own documentation on both halves.

*This is a settled mismatch, not an unknown. Section 4 of the Mission 1.60 brief forbids searching for another query syntax, inventing a freshness tolerance, or buying a higher access tier in the hope that observation timestamps become queryable.*

**Anchor:** Netlas — `ANCHOR_CANDIDATE_B`, not `SELECTED_APPARATUS_B`, `APPROVED_APPARATUS_B`.

Its load-bearing records expose an actual scan_date, which is the property the failed apparatus lacked.

**Construct** (RFC 4253 section 4.2):

> The number of DISTINCT public IPv4 addresses from which, during a defined observation window, a TCP connection to port 22 was accepted and the peer sent an identification string whose literal prefix is `SSH-` before protocol negotiation.

Properties: `SOURCE_INDEPENDENT`, `VENDOR_INDEPENDENT`, `FINGERPRINT_INDEPENDENT`, `CVE_INDEPENDENT`.

**`OBSERVATION_ADDRESSABLE_EXPOSURE`** — HARD_PRE_SELECTION_GATE, from Mission 1.59.

An apparatus qualifies only if a FUTURE observation can be attributed to a predefined observation window from its published or legitimately available acquisition surface, BEFORE any measurement value is retrieved.

It is **not**: scans frequently; updates often; has a last-updated field; has a current-state database; publishes historical results; claims continuous scanning.

## Documentation ledger

**10 of 15 retrievals.** Research-data requests **0**, target measurement requests **0**, counts **0**, trials **0**, purchases **0**.

|  | kind | apparatus | target | established |
| --- | --- | --- | --- | --- |
| 1 | FETCH | anchor B | `https://docs.netlas.io/api-reference/` | a custom query syntax accepting arbitrary field filters and bracket range syntax, plus an `indices` request parameter that selects a particular data-collection DATE. Window selection therefore happens in the REQUEST rather than after retrieval. |
| 2 | FETCH | anchor B | `https://docs.netlas.io/knowledge-base/query-language/` | date and numeric ranges via `[ TO ]` and one-sided `<`, `>`, `<=`, `>=`; port filtering; and a queryable `*.banner` field with wildcard and prefix matching. |
| 3 | SEARCH | partner discovery | `web` | navigational only. Also surfaced a first-party Netlas fact: daily scan volumes are downloadable as JSON files, which is an observation partition by window. |
| 4 | FETCH | partner candidate | `https://www.onyphe.io/docs` | HTTP 301 to another host |
| 5 | FETCH | partner candidate | `https://www.onyphe.com/docs` | HTTP 404 |
| 6 | FETCH | partner candidate | `https://www.shadowserver.org/what-we-do/network-reporting/api-documentation/` | the technical documentation has moved to an external wiki; the page itself carries none of the data model. |
| 7 | FETCH | partner candidate | `https://github.com/The-Shadowserver-Foundation/api_utils/wiki/Reports-API` | the substantive wiki pages did not load. One usable first-party sentence: some APIs are public and most are private for partners and direct data consumers. |
| 8 | FETCH | partner candidate | `https://docs.leakix.net/docs/api/intro/` | HTTP 404 |
| 9 | CARRIED | anchor B | `docs.netlas.io/knowledge-base/scanning-technology/` | retrieved in Mission 1.58 and re-read from the artifact: own purpose-built scanners, the full IPv4 space excluding reserved and special-use ranges, a curated list of over 1000 TCP ports plus selected UDP ports, no IPv6, roughly thirty application-layer protocols identified by banner grabbing and protocol parsing. |
| 10 | CARRIED | anchor B | `docs.netlas.io/knowledge-base/field-reference/responses/` | retrieved in Mission 1.59 and re-read from the artifact: each document is a single service response collected during scanning, keyed by (uri, ip); `scan_date` records when the scanning that generated it occurred; `@timestamp` is the index time. |

**Queries executed: 0. Target measurement retrieved: False.** Documentation pages describe query grammar and field meanings. Example queries in the grammar documentation illustrate syntax and were read as syntax; none was executed and no result set was requested.

