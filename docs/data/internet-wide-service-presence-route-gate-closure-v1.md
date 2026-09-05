# Internet-Wide Service Presence — Route Gate Closure V1

**Mission 1.59 — Internet-Wide Service-Presence Route Gate Closure V1 — recorded 2026-09-05.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_service_presence_route.py`.

## Outcome — `SNAPSHOT_TIME_SEMANTICS_NOT_ALIGNABLE`

The two apparatuses publish different kinds of temporal object. One is a stream of observations each carrying the time it was made; the other is a maintained current state whose searchable time field records when a record last changed. No time-selection rule can be frozen before values are retrieved, so the pair cannot support a preregistered threshold proposition.

Selected route: **None**. Section 50 assigns an actionability level only to a route that passed. None did.

## The sixteen gates, recomputed

|  | gate | was | is | reason |
| --- | --- | --- | --- | --- |
| 1 | `SAME_EXTERNAL_CONSTRUCT` | PASS | PASS | both apparatuses probe the public IPv4 space for responding services |
| 2 | `EXACT_CANONICAL_SUBJECT` | PASS | PASS | a named protocol is an exact subject |
| 3 | `METRIC_DEFINITION_COMPATIBILITY` | PASS_IF_NARROWED | **UNKNOWN** | the construct is now defined protocol-natively against RFC 4253 and needs no vendor fingerprint, which resolves the semantic half. What is not established is that either apparatus exposes a query surface deciding that predicate rather than its own assigned service label. |
| 4 | `UNIT_COMPATIBILITY` | PASS | PASS | hosts on both sides, no conversion |
| 5 | `TIME_COMPATIBILITY` | UNKNOWN | **FAIL** | established from first-party documentation on both sides: a stream of timestamped observations against a merged current state whose searchable time is a last-change time, with no documented aggregate observation-window selector. The only remaining pairing procedure is the retrospective one section 18 forbids. |
| 6 | `POPULATION_OR_FRAME` | PASS | **UNKNOWN** | REOPENED. One apparatus documents that under high service density its service data represents a SAMPLING of service details, so its record is not necessarily a census of that host's services. Vantage-relative reachability was also never established for either side. Section 28 forbids calling a partial frame internet-wide. |
| 7 | `EACH_ALONE_ENTAILS` | PASS | PASS | either count alone decides a threshold |
| 8 | `NO_SHARED_UPSTREAM` | PASS | PASS | no authoritative published host-presence count exists to be republished, and no load-bearing common measurement upstream was found |
| 9 | `DIFFERENT_MEASUREMENT_PRODUCTION` | PASS | PASS | separate scanners, separate port lists, separate parsing |
| 10 | `FIRST_PARTY_LINEAGE_DOCUMENTATION` | PARTIAL | PARTIAL | strengthened on apparatus B from an absence to a positive statement about the load-bearing records, and still short of an affirmative statement that no external measurement feed is load-bearing |
| 11 | `RELIABILITY_REVIEWABILITY` | PASS | **UNKNOWN** | REOPENED. Section 52. Both publish methodology, and the narrowed metric now depends on how each decides a wire-level predicate. Whether that decision procedure is documented well enough for a human to review its dependability is not established, and one side's fingerprinting is proprietary. |
| 12 | `GOVERNANCE_FEASIBILITY` | UNKNOWN | UNKNOWN | section 34 forbids the governance review in this mission, so this gate was not targeted and could not close |
| 13 | `THRESHOLD_FREEZABLE` | PASS | **FAIL** | REOPENED as a consequence of gate 5. A threshold can only be frozen before both retrievals if the observations it will be compared against can be identified in advance, and they cannot. |
| 14 | `FALSIFIABLE_BOTH_WAYS` | PASS | PASS | a host count against a bound admits observations on either side |
| 15 | `STRUCTURALLY_USEFUL` | PASS | PASS | demonstrated on synthetic fixtures below |
| 16 | `PRODUCT_RELEVANCE` | PASS | PASS | observable service presence across a defined public frame bears on AUDIENCE_OR_USAGE and COMPETITIVE_SUPPLY, and the protocol narrowing did not detach it: the construct did not have to name a product to remain interesting |

PASS **9**, FAIL **2**, UNKNOWN **4**, PARTIAL **1**. Reopened: [6, 11, 13].

Section 30. Three gates that passed a mission ago now read worse under fuller information. That is the audit process working, not the mission failing: they were passing on less evidence than they are now failing on.

## Structural fixtures

**Same Claim identity.** one source-independent TargetProposition P; witness A carries a value above the bound, witness B below it → identical proposition_key for both witness shapes.

the protocol narrowing did not sneak scanner identity into Claim identity. Scanner identity is witness provenance, and the same Claim accepts both measurements.

**Independent support.** same P, both witnesses SUPPORTS, both KNOWN_INDEPENDENT → 2 provenance groups; control: both UNKNOWN gives 1 group.

**The diagnostic.** *If apparatus A and B disagree, is that potentially a fact about the world or necessarily a bug?*

`POTENTIALLY_A_REAL_MEASUREMENT_DIFFERENCE` — each apparatus generates its observations by probing, so a difference can be coverage, timing or vantage rather than a transcription error

**And the caveat this mission adds.** That answer is only meaningful once the observations can be attributed to a common window. Under this pair they cannot, so a disagreement could ALSO be an artefact of one side's searchable timestamp meaning last-change rather than last-observed. A contradiction produced that way would be an artefact recorded as a finding, which is why gate 5 is not negotiable.

## Threshold

Selected **False**. Section 40. The acquisition contract is not governed or frozen, and choosing a bound now would be choosing a number for a route that does not qualify.

Preregistrable for this pair: **NO**. For the class: **YES, for a pair whose apparatuses both expose observation-addressable data**.

## Counters

| counter | value |
| --- | --- |
| `first_party_document_requests` | **8** |
| `budget` | **12** |
| `measurement_endpoints_called` | **0** |
| `measurement_values_fetched` | **0** |
| `paid_access_purchased` | **0** |
| `trials_started` | **0** |
| `model_calls` | **0** |
| `model_cost_usd` | **0.0** |
| `embeddings` | **0** |
| `canonical_mutations` | **0** |
| `sources_registered` | **0** |
| `governance_reviews_created` | **0** |
| `collectors_implemented` | **0** |
| `normalizers_implemented` | **0** |
| `threshold_registrations_created` | **0** |
| `claims_created` | **0** |
| `evidence_created` | **0** |
| `reliability_assessments_created` | **0** |
| `reliability_values_assigned` | **0** |
| `independence_groups_created` | **0** |
| `scores_created` | **0** |
| `opportunity_changes` | **0** |
| `mission_1_56_claim_modified` | **False** |
| `reference_profile` | **UNCALIBRATED** |
| `problem_family` | **PARKED** |

## What survives

- **the protocol native construct.** A service-presence metric can be defined against a published standard with no vendor taxonomy, and the definition is written source-free so any future pair can be asked for it.
- **the new apparatus requirement.** OBSERVATION_ADDRESSABLE_EXPOSURE. An apparatus qualifies only if a future observation can be attributed to a defined window from its published surface, BEFORE any value is retrieved. This is not the same as scanning often, and Mission 1.58 could not have known to ask for it.
- **the diagnostic that generalises.** A dataset can be excellent and still be the wrong temporal object. A maintained current-state view answers what is running now; a preregistered threshold proposition asks what was observed during a window. Both are legitimate products and only one of them can witness this kind of Claim.
- **the lineage advance.** Apparatus B's provenance moved from an absence of a denial to a positive statement about the load-bearing records, which carries forward if it appears in a future pair.

## Next — Mission 1.60 — Observation-Addressable Scanner Pair Selection V1

Section 67. On SNAPSHOT_TIME_SEMANTICS_NOT_ALIGNABLE the instruction is to drop the pair, not the class, and not to pay for governance or access. The class survives: the structural independence argument is untouched and the protocol-native construct is now written down.

It should:

- add OBSERVATION_ADDRESSABLE_EXPOSURE as a gate applied BEFORE a pair is selected, so the next pair is not chosen and then discovered to be the wrong temporal object
- ask the vantage and frame questions before selection too, since gate 6 reopened on a sampling disclosure that was there to be read
- carry the protocol-native construct forward unchanged rather than redefining it
- carry apparatus B forward as a candidate side, since its exposure model is the one that fits
- seek a second observation-addressable scanner and establish its lineage affirmatively

It must not:

- fetch a measurement value, a host count or a result total
- purchase access or start a trial that exposes target measurements
- accept a vendor product label as the metric definition
- read an absence of a reference to third-party data as an affirmative statement
- register a source or create a governance review
- restore the withdrawn physical-science route

