# Internet-Wide Service Presence — Lineage Review V1

**Mission 1.59 — Internet-Wide Service-Presence Route Gate Closure V1 — recorded 2026-09-05. Gate 10.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_service_presence_route.py`.

Gate 5 failed on documentation from both sides before gate 10 was worked. Section 67 drops the pair on that outcome, so further budget on apparatus A's lineage would have been spent on a route already being dropped.

**Still worth doing.** Apparatus B's lineage, because its observation-based exposure is exactly what the next pair needs and its lineage evidence carries forward.

*A completed gate-10 determination for the pair. Saying so matters: an unfinished check reported as a finished one is the shape this arc has refused since Mission 1.46.*

## Evidence hierarchy

| level | meaning |
| --- | --- |
| `LEVEL_1_STRONG` | first-party technical methodology explicitly states the values or records are produced by the organisation's own active scans or probes |
| `LEVEL_2_SUFFICIENT_IF_COMPLETE` | first-party architecture and method documents jointly establish own probing, own observations, own count construction, and no external measurement feed in the load-bearing path |
| `LEVEL_3_INSUFFICIENT` | marketing wording such as 'we scan the internet', without enough detail to identify which dataset or value it refers to |
| `LEVEL_4_NOT_EVIDENCE` | no mention of third-party feeds |

## Apparatus A

- `affirmative`: True
- `level`: LEVEL_1
- `basis`: Its own methodology page states that all published data derives from its own internet-wide scanning operations, describes its own scanning subnets, and describes completing protocol handshakes itself.
- `carried_from`: Mission 1.58
- `advanced_by_this_mission`: False
- `why_not_advanced`: gate 5 had already dropped the pair

## Apparatus B

- `affirmative`: PARTIAL
- `level`: between LEVEL_2 and LEVEL_4, and closer to LEVEL_2 than Mission 1.58 could establish
- `what_mission_1_58_had`: A first-party statement that it operates its own purpose-built scanning infrastructure, plus an ABSENCE of any reference to third-party scan data. Mission 1.58 recorded the absence as an absence.
- `what_this_mission_added`:
  - its responses field reference states that each document is a single service response COLLECTED DURING SCANNING, which ties the load-bearing record to its own scanning rather than to an unspecified database
  - `scan_date` is documented as when the internet-wide scanning activity that GENERATED the captured response occurred, which is a positive statement about the origin of the record rather than about the organisation's capabilities
  - its documentation separates primary internet scan data from auxiliary enrichment drawn from DNS registries, WHOIS and certificate sources, so the external inputs it does use are named and are not host-state measurements
- `why_this_is_still_not_PASS`: Section 22. None of it is an affirmative statement that no external measurement feed is load-bearing for host observations. What moved is the quality of the evidence, from an absence of a denial to a positive statement about the load-bearing records. That is a real upgrade and it is not closure.
- `what_would_close_it`: A first-party technical statement that host-level observations and banners in the responses collection are produced by its own probes and by no external measurement provider. If public documentation is exhausted, a written enquiry.
- `advanced_by_this_mission`: True

## Shared auxiliary inputs

| input | classification | impact |
| --- | --- | --- |
| routable IPv4 address space | `SAMPLING_FRAME_INPUT` | tells each apparatus WHICH addresses may exist, not which hosts run a service. Compatible with independent measurement. |
| the protocol standard itself | `FINGERPRINT_DEFINITION` | a shared definition of what counts is what MAKES the two comparable. It is the opposite of a provenance problem. |
| DNS registry, WHOIS and certificate enrichment | `AUXILIARY_METADATA` | not load-bearing for a protocol-native host-presence count |
| a common CVE database | `MEASUREMENT_UPSTREAM_IF_USED` | would be load-bearing for a vulnerability-flavoured metric on BOTH sides, and the protocol-native narrowing removes it from the path entirely. Recorded because a later mission tempted to make the metric more interesting by adding a version or vulnerability condition would reintroduce a shared upstream without noticing. |

There is no authoritative published count of hosts running a service, so neither apparatus can be copying one. That is STRUCTURAL_NON_REPUBLICATION and it is not the same thing as APPARATUS_LINEAGE_ESTABLISHED, which is what gate 10 asks for. Section 24 keeps them apart, and this record does too.

## Vantage and frame

**Status `NOT_ESTABLISHED for this pair`.** Reachability is measured from somewhere. Two scanners probing from different networks may see different populations because of geofencing, routing, firewalls, rate limiting, anycast and network ACLs.

*Why it was not pursued.* gate 5 had already dropped the pair

**For the next pair.** The target population must say whether it means globally publicly reachable or reachable from a named vantage. If reachability is materially vantage-relative and no governed equivalence exists, gate 6 reopens and SAME_POPULATION can become FAIL. It must be asked BEFORE a pair is selected rather than discovered after.

One apparatus documents that under high service density its service data represents a SAMPLING of service details. A sampled record is not a census, and a partial frame must not be described as internet-wide.

## Gate 10 — `PARTIAL`

Affirmative A **True**, affirmative B **False**, common measurement upstream **none found**.

- apparatus A: its methodology page states all published data derives from its own internet-wide scanning operations
- apparatus B: its scanning-technology page states it operates its own purpose-built scanning infrastructure; its responses field reference states each document is a single service response collected during scanning, with scan_date recording when the scanning activity that generated it occurred

## Written enquiry

Prepared **True**, sent **False**.

> For the service-response dataset your search interface exposes, are the underlying host observations and banners produced by your organisation's own active scanning infrastructure, or are host-level observations or counts sourced in whole or in material part from another measurement provider? Separately, is any external measurement dataset load-bearing for the presence or absence of a service on a host, as distinct from enrichment such as registry, WHOIS or certificate metadata?

It asks for facts about lineage rather than for the word independent, which invites interpretation rather than information. And it separates measurement from enrichment, because the answer to those two is different and a single question would blur them.

