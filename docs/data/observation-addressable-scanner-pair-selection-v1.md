# Observation-Addressable Scanner Pair Selection V1

**Mission 1.60 — Observation-Addressable Scanner Pair Selection V1 — recorded 2026-09-05.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_scanner_pair_selection.py`.

## Outcome — `APPARATUS_LINEAGE_NOT_AFFIRMATIVELY_ESTABLISHED`

The anchor apparatus requalified on the two gates that killed the previous pairs -- its observation window is selectable in the request and its predicate is expressible against a queryable raw banner -- and it still does not individually qualify, because first-party documentation does not affirmatively establish that no external measurement feed is load-bearing for its host observations. No partner reached pair analysis, so no pair was constructed.

Selected pair: **None**.

### Why this outcome

**The imperfect fit.** Outcome G is defined for the case where a promising PAIR exists and lineage remains unproven. Here there is a promising ANCHOR and no pair. The clause is half-satisfied.

It names the blocker that is ESTABLISHED rather than merely unexplored, and the one that sits upstream of every partner question: no partner can rescue an anchor whose own measurement lineage is unproven. It is also the blocker that is precisely actionable, by reading or by one written enquiry.

*NO_OBSERVATION_ADDRESSABLE_PARTNER_IDENTIFIED asserts that the anchor qualifies. It does not, and recording that it does would be exactly the overstatement this arc keeps refusing.*

*ANCHOR_APPARATUS_INVALIDATED overstates it in the other direction. Neither blocking gate is a refutation: A7 is an unproven negative and A8 is a set of operational questions nobody has asked.*

No partner was qualified either, and every partner failed at documentation retrieval rather than at a substantive gate. That is a co-blocker and it is reported beside this outcome rather than folded into it.

## Gate summary

| gate | verdict |
| --- | --- |
| `A1` | **PASS** |
| `A2` | **PASS** |
| `A3` | **PASS** |
| `A4` | **PASS** |
| `A5` | **PASS_WITH_STATED_BOUNDS** |
| `A6` | **PASS** |
| `A7` | **PARTIAL** |
| `A8` | **PARTIAL** |
| `A9` | **PASS** |

PASS **6**, with bounds **1**, PARTIAL **2**. Individually qualifies: **False**.

Section 39. Pairs are generated only between individually qualifying apparatuses, and none was available on either side.

## Window and threshold

Window width selected: **False**. Section 23. A width may only be fixed once a pair exists and its cadences impose a minimum comparable interval. Choosing one now would be choosing a number for a route that does not exist.

Duplicate rule: a host observed several times inside the window counts once; a host observed once satisfying the predicate qualifies for the window even if it later stops responding.

**Host-level membership is existential within the window, and the CLAIM is a count against a bound. COUNT(distinct qualifying addresses in window) >= X can be contradicted by a count below X. Host-level monotonicity is not Claim-level monotonicity, and confusing the two would have hidden a real falsifiability problem or invented one.**

Threshold selected: **False**. Preregistrable: **NOT_DETERMINABLE_WITHOUT_A_PAIR**.

The anchor alone supports the required ordering: its observation window is selectable before retrieval, so a threshold registered at T3 would precede any retrieval at T4. Whether the pair supports it depends on a partner that does not yet exist.

## Structural fixtures

**same target identity.** one source-independent TargetProposition P; a witness above the bound and a witness below it, each annotated with a different synthetic scanner id → identical proposition_key.

**independent support.** same P, both witnesses SUPPORTS, both KNOWN_INDEPENDENT → 2 provenance groups.

**contradiction.** same P, one SUPPORTS and one CONTRADICTS → one Claim carrying both directions, one group per direction.

**The diagnostic.** *If the two report different counts for the frozen window, could that be a legitimate result of independent measurement, or must one have misread the other?*

`LEGITIMATE_INDEPENDENT_MEASUREMENT_DIFFERENCE_POSSIBLE` — Each apparatus generates its observations by probing, so a difference can be coverage, packet loss, vantage or timing within the window.

**That answer holds only for a pair sharing one population and one window definition. A difference caused by different frames or different time semantics is not a measurement difference at all -- it is two propositions being compared, which is what the last two missions failed on. Only the first kind is legitimate.**

## Positive against negative observation

A successful identification is strong evidence that the service was reachable from that measurement path at that time. A failure to observe is ambiguous: offline, packet loss, ACL, scan exclusion, rate limiting, routing, sampling or measurement failure.

The route counts POSITIVE observed addresses. Non-observation must never be read as the host being definitely absent, and pair equivalence therefore concerns the count-generation procedures rather than per-host negative truth.

## Counters

| counter | value |
| --- | --- |
| `first_party_doc_requests` | **10** |
| `budget` | **15** |
| `research_data_requests` | **0** |
| `target_measurement_requests` | **0** |
| `target_host_record_requests` | **0** |
| `target_count_requests` | **0** |
| `facets_fetched` | **0** |
| `trials_started` | **0** |
| `purchases` | **0** |
| `queries_executed` | **0** |
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

- **the anchor is stronger than it was.** It now passes A2 on two independent mechanisms and A3 in the strongest exposure class. The gates that killed the last two pairs are not what blocks it.
- **the blockers changed kind.** They are no longer about what the apparatus measures or how it exposes it. A7 is a sentence its documentation does not contain; A8 is a set of operational questions nobody has asked. Both are closable by reading or asking rather than by finding a different apparatus.
- **the requirement registry.** Nine reusable rules from Missions 1.47 to 1.59 now sit in one record with the mission that paid for each, so route discovery reads a registry rather than a chain of reports. Every one of them was learned AFTER a pair had been chosen.
- **the partner gap is documentation not apparatus.** Three partner candidates were left at a documentation wall rather than at a verdict. That is a fact about this mission's reach and it is what the next one should attack first.

## Next — Mission 1.61 — Anchor Lineage Confirmation and Partner Documentation Retrieval V1

Section 63. On APPARATUS_LINEAGE_NOT_AFFIRMATIVELY_ESTABLISHED the instruction is not to buy access, and to target the missing lineage proof. Two things block, both are documentation problems, and neither needs a new apparatus class.

It should:

- prepare an operator-approved written enquiry to the anchor asking whether host-level service observations are produced by its own probes and whether any external measurement dataset is load-bearing for the presence or absence of a service on a host
- ask the same operational questions a reliability reviewer would: retry behaviour, duplicate handling within a window, address identity counting, and what a missing record means
- pin the anchor's port coverage for port 22 to the window, since the port list is documented as expanding over time
- retrieve working documentation paths for the three partner candidates left at a wall, applying A1 and A2 first
- establish the anchor's vantage model, which was recorded as NOT_ESTABLISHED before pairing rather than after

It must not:

- fetch a measurement value, a host count, a host record, a facet or a result total
- execute a service search query against target data
- start a trial, demo console or search preview that reveals target observations, because a zero-cost trial destroys preregistration exactly as a paid one would
- purchase access
- revive the dropped current-state apparatus or search for another query syntax for it
- accept a vendor product label as the metric definition
- read an absence of a reference to third-party data as an affirmative statement
- register a source or create a governance review

