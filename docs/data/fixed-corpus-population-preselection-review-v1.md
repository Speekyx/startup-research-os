# Mission 1.70 — Can a common web population be frozen honestly?

Generated from `fixed-corpus-population-preselection-review-v1.json`.
Do not edit by hand.

**Decision: `EXTERNALLY_FROZEN_POPULATION_REQUIRES_OPERATOR_FETCHER`**

## What each route's coverage actually means

| route | classification | targeted | attempted | captured |
|---|---|---|---|---|
| COMMON_CRAWL | `UNKNOWN_BETWEEN_CRAWLED_SET_AND_SUCCESSFULLY_FETCHED_SET` | False | False | True |
| HTTP_ARCHIVE | `UNKNOWN_BETWEEN_ATTEMPTED_SET_AND_SUCCESSFULLY_FETCHED_SET` | False | PARTIAL | True |

Why, in each case:

- **COMMON_CRAWL** — the index describes captures, and neither the CDXJ page nor the columnar schema states whether a URL fetched unsuccessfully or never captured appears at all
- **HTTP_ARCHIVE** — the pages table is one row per page TESTED and carries no failure column; the metadata blob carries retry_count, tested_url and visited, which are attempt-level, but no test status

## The metadata boundary is navigable and the semantic one is not

A projection can return a coverage list without reading a status column. It cannot tell you whether membership in that list means attempted or captured, and that is what a population rule needs.

| route | classification | measurement fields in the coverage surface |
|---|---|---|
| COMMON_CRAWL | `YES_WITH_FIELD_LEVEL_PROJECTION` | `status`, `fetch_status`, `content_truncated` |
| HTTP_ARCHIVE | `YES_WITH_FIELD_LEVEL_PROJECTION` | `payload`, `response_headers`, `response_body` |

## The five strategies

| strategy | verdict |
|---|---|
| `P1_provider_native_intersection` | UNAVAILABLE |
| `P2_frozen_C_plus_planned_target_coverage` | UNAVAILABLE |
| `P3_frozen_C_plus_attempted_coverage` | UNAVAILABLE |
| `P4_frozen_C_plus_realized_successful_coverage` | AVAILABLE_AND_HIGH_RISK |
| `P5_missingness_preserving` | UNAVAILABLE_ON_THE_EXTERNAL_PAIR |

- **P1_provider_native_intersection** — membership is projectable before values and its MEANING is undocumented on both sides, so §37 condition 3 — coverage definition is explicit — cannot be met.
- **P2_frozen_C_plus_planned_target_coverage** — neither route publishes a target list before a crawl or a run, so there is no planned-target membership to intersect with.
- **P3_frozen_C_plus_attempted_coverage** — the attempted set is not reconstructable on Common Crawl and only partially so on HTTP Archive, where a page that never succeeded may not appear at all.
- **P4_frozen_C_plus_realized_successful_coverage** — this is the only intersection actually constructible, and §7 says not to accept it without a rigorous reason that it is not outcome-conditioned for the predicate family. No such reason exists, because the inclusion criteria are undocumented on both sides.
- **P5_missingness_preserving** — it is the architecture that would preserve a frozen C and it needs OBSERVED, ATTEMPTED_NO_USABLE_RESPONSE and NOT_ATTEMPTED to be distinguishable. Neither route documents that distinction, so an absent entity cannot be told apart from a failed one.

## Why this decision

- **why not A** — three of the seven conditions are UNKNOWN, and §37 says an unknown condition blocks A outright.
- **why not B** — the missingness-preserving architecture is the right shape and it needs legible missingness, which neither route provides.
- **why not D** — D asserts that realized co-coverage IS post-hoc and invalid. What was established is that the inclusion criteria are UNDOCUMENTED on both sides. Asserting invalidity would claim more than the evidence, and this repository has refused that conversion since Mission 1.60.
- **why not E** — the question did close, in one direction. An externally frozen population with distinguishable missingness cannot be obtained from either archive, because neither can be directed at a corpus and neither publishes attempt-level membership. Reporting it as unresolved would discard that.
- **why C** — an operator-run fetcher supplies both missing properties by construction — it covers exactly the corpus it is given, and it records every attempt including the failures. That is not a preference for building something; it is what the two gaps happen to require.

## What this does not establish

- that Common Crawl or HTTP Archive coverage IS outcome-conditioned
- that no other population architecture exists
- that an operator fetcher is authorised, feasible in practice, or independent
