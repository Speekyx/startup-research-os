# Observation-Addressable Apparatus Contract V1

**Mission 1.60 — Observation-Addressable Scanner Pair Selection V1 — recorded 2026-09-05.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_scanner_pair_selection.py`.

## Individual hard gates

|  | gate | rule |
| --- | --- | --- |
| A1 | `ACTIVE_MEASUREMENT_PRODUCER` | It generates service observations by probing the network. Not a republisher, and not a reader of another scanner's dataset. |
| A2 | `OBSERVATION_ADDRESSABLE_EXPOSURE` | A future observation can be selected by its actual observation timestamp or window from the published acquisition surface. Not a last-change timestamp, not an ingestion timestamp unless demonstrably identical to observation, not current-state only. |
| A3 | `PROTOCOL_NATIVE_OBSERVATION_EXPOSURE` | It exposes enough source-native information to decide the common predicate. A vendor-assigned product label alone FAILS. |
| A4 | `OBSERVATION_TIME_DOCUMENTED` | First-party documentation defines the timestamp semantics. |
| A5 | `FRAME_DOCUMENTED` | The address population actually probed is documented. |
| A6 | `NON_VALUE_DOCUMENTATION_AVAILABLE` | All of the above can be established without fetching a target measurement. |
| A7 | `AFFIRMATIVE_MEASUREMENT_LINEAGE` | First-party evidence positively establishes own probing and own observation generation. An absence of third-party references is insufficient. |
| A8 | `RELIABILITY_REVIEWABLE` | Enough methodology is available to later perform the exact five-field reliability review. No value assigned now. |
| A9 | `PRODUCT_RELEVANT` | The exposed measurement remains useful for bounded AUDIENCE_OR_USAGE or COMPETITIVE_SUPPLY reasoning. |

## Addressability is about the boundary

**The operator must be able to define WINDOW = [T0, T1) BEFORE retrieval, and then request observations whose observation timestamp falls inside it — without first inspecting the observations to discover which filter would be convenient.**

Passing shapes:

- an API filter on a documented scan timestamp
- an export or index partitioned by observation date
- an immutable snapshot with a documented observation interval
- an archive where the observation-time range is part of the request identity

Failing shapes:

- current state plus last_changed
- current state plus indexed_at
- latest only
- retrieve the whole set, then inspect per-row observation dates
- choose the closest timestamp after downloading
- an observation timestamp that exists on the record but cannot be queried

**The loophole this closes.** A dataset may carry perfect per-row observation timestamps and still FAIL. If the only procedure is download, inspect, filter, then the measurements were retrieved before the window was operationally selected — and for a preregistered route that is too late.

Acceptable time objects: `OBSERVATION_EVENT_STREAM`, `IMMUTABLE_SCAN_SNAPSHOT_WITH_DEFINED_INTERVAL`, `OBSERVATION_PARTITION_BY_WINDOW`. Rejected: `MAINTAINED_CURRENT_STATE_LAST_CHANGE, however excellent the database`.

## Protocol predicate exposure classes

| class | meaning |
| --- | --- |
| `RAW_IDENTIFICATION_STRING` | the apparatus exposes the bytes the peer sent, queryable |
| `STRUCTURED_PROTOCOL_FIELD` | a parsed field whose definition is fixed by the standard |
| `DETERMINISTIC_EQUIVALENT_FIELD` | documentation proves an exposed field is exactly equivalent to the predicate |
| `PROPRIETARY_CLASSIFIER_ONLY` | REJECTED |
| `NOT_EXPOSED` | REJECTED |
| `UNKNOWN` | REJECTED |

## Metadata against measurement

Permitted: schema definitions, filter documentation, field names, time semantics, query grammar.

Forbidden: host records, service banners, counts, IP addresses, facets, aggregations, measurement totals.

**A query returning only a count still returns a measurement value about the target population. It is not metadata because only a number came back.**

**A zero-cost trial, demo console, search preview or sample explorer destroys preregistration exactly as a paid one would. Access cost is irrelevant to epistemic contamination.**

## The requirement registry

| requirement | from | rule |
| --- | --- | --- |
| `SOURCE_EXCLUSIVE_METRIC` | Mission 1.56 | A quantity that exists only because a platform recorded it can be measured only by that platform. A second publication route is a second copy, never a second measurement. |
| `RELIABILITY_REVIEWABILITY` | Mission 1.47 | A theoretically ideal apparatus whose methodology cannot be reviewed is not useful, and the check belongs before selection rather than after. |
| `FRAME_INSIDE_THE_DEFINITION` | Mission 1.57 | An apparatus measuring share within its own reach has put its frame inside the metric. A proposition admitting two such apparatuses relocates source attribution into its predicate. |
| `AFFIRMATIVE_LINEAGE_REQUIRED` | Mission 1.57 | Independence needs positive first-party evidence from BOTH sides. An absence of a reference to third-party data is an absence, not a statement. |
| `PRODUCT_RELEVANCE` | Mission 1.58 | The construct must bear on a named Opportunity dimension. A route that exercises the machinery on a quantity the product will never research calibrates nothing transferable. |
| `READING_A_PUBLISHED_VALUE_IS_NOT_MEASURING_IT` | Mission 1.58 | Two apparatuses that each retrieve an authoritative published record are two readings of one fact. Measurement requires generating the value by interacting with the world, so that two apparatuses can legitimately disagree. |
| `OBSERVATION_ADDRESSABLE_EXPOSURE` | Mission 1.59 | A future observation must be attributable to a defined window from the published surface, before any value is retrieved. Not the same as scanning often. |
| `THE_TEMPORAL_OBJECT_TEST` | Mission 1.59 | A dataset can be excellent and still be the wrong temporal object. A maintained current-state view answers what is running now; a preregistered threshold proposition asks what was observed during a window. |
| `SAMPLING_IS_LOAD_BEARING` | Mission 1.59 | A sampled population is not a census. Two apparatuses cannot be compared as one count unless both expose the same population definition, and V1 implements no estimator to bridge them. |
| `ENUMERATED_EXCEPTIONS_MAKE_A_LINEAGE_CLAIM_CHECKABLE` | Mission 1.61 | An affirmative lineage statement is exhaustive only if its exceptions are enumerated and closed. 'We collect everything ourselves, and the only exceptions are X and Y' can be checked against the load-bearing predicate; 'our data comes from scans, sensors, blocklists and many other sources' cannot, because the list does not end. The second is LEVEL 1 however confidently it asserts its own scanning. |
| `LINEAGE_EXHAUSTIVENESS_IS_NOT_FRAME_EXHAUSTIVENESS` | Mission 1.61 | That every record was produced by the apparatus's own probing says nothing about which addresses it reached. A7 asks who produced the observation; A5 asks which addresses were probed. A lineage sentence must never be cited for coverage, and an apparatus can satisfy A7 completely while probing an incomplete or sampled frame. |
| `THE_RETRIEVABLE_FRAME_IS_NOT_THE_MEASURED_FRAME` | Mission 1.62 | An apparatus can measure the whole internet and expose to any given requester only a slice of it. What bounds a Claim is the frame the acquisition surface EXPOSES, never the frame the apparatus MEASURES. Where the exposed slice is defined by who is asking, two requesters retrieve two different populations and no single proposition about the whole can be witnessed through it. |
| `DEFAULT_DATA_SURFACE_MUST_NOT_OVERRIDE_QUALIFIED_EXPOSURE_PATH` | Mission 1.62 | Where an apparatus qualifies only through a non-default observation-addressable surface, a collector must bind explicitly to that surface. A default surface that silently returns the latest state is the rejected temporal object, and a collector omitting the selector reads it while a record elsewhere says the gate passed. This governs implementation, where OBSERVATION_ADDRESSABLE_EXPOSURE governs selection. |
| `APPARATUS_CONFIGURATION_MUST_BE_TIME_ADDRESSABLE` | Mission 1.63 | A load-bearing scan-configuration fact, such as which ports a scan covered, must be attributable to the same observation period the measurement will come from, and attributable BEFORE retrieval. A configuration list published as a current reference establishes what is true today and binds no window. OBSERVATION_ADDRESSABLE_EXPOSURE governs when the OBSERVATION happened; this governs when the CONFIGURATION applied, and an apparatus can expose a perfect observation timestamp while leaving you unable to say whether it was probing the port during that window. |

*Apply these BEFORE selecting a pair. Every one of them was discovered after a pair had already been chosen, and each cost a mission to learn.*

