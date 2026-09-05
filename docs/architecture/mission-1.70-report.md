# Mission 1.70 — Fixed-Corpus Web Route Qualification V1

**Outcome: `FIXED_CORPUS_WEB_REQUIRES_OPERATOR_CONTROLLED_ROUTE`.** Q1 kept both
producers and lost the population. No class selected, no construct frozen, registry
unchanged at 15.

---

## 0. Coverage is published on both routes, and neither says what it means

Mission 1.69 ended one question away. Q1 had two independently established producers,
dated artifacts on both sides, raw responses with headers on one, and — the property no
scanner ever offered — **coverage published rather than hidden**. What it could not do
was point either apparatus at a corpus, so a joint population had to be a frozen corpus
intersected with two independently determined coverages. Coverage is metadata, both
sides publish it, and a restriction rule could in principle be frozen before any value
is retrieved. Whether that is an honest preregistration was the open question.

It is not, and the reason is not the one the question anticipated.

| route | what its coverage surface says | what it does not say |
|---|---|---|
| Common Crawl | `status`: *"the HTTP status code returned when fetching the page"*; columnar `fetch_status`: *"HTTP response status code"*, plus `fetch_redirect` and `content_truncated` taking `length`, `time`, `disconnect`, `unspecified` | whether a URL fetched unsuccessfully, or never captured at all, has a row |
| HTTP Archive | one row per page **tested**; `retry_count`, `tested_url`, `visited` inside a metadata blob | the pages table has **no failure column**, and no field is a test status |

**Both leave attempted-versus-successful coverage undocumented, at the same time.** So
the co-coverage rule can be written before retrieval and still not be preregistered,
because what it selects on is undefined.

## 1. That is a different problem from a hidden frame

A hidden discovery frame means you cannot say which items were **eligible**. This means
you cannot say whether an item's **absence** is a fact about the world or a fact about
the apparatus.

A joint population would therefore carry a denominator neither publisher can describe,
and every proposition resting on it would inherit that. **Temporal ordering is necessary
and never sufficient**, and that sentence is the reusable half of this mission: a rule
written first is preregistered only if what it selects on is defined. Calling
co-coverage preregistered because the rule came first would repeat the hidden-frame
mistake one layer along, in a place where it is harder to see.

## 2. Five strategies, five rejections, and the two that hurt

| strategy | verdict |
|---|---|
| P1 provider-native intersection | needs a directable apparatus; neither is |
| P2 frozen C + planned target coverage | needs a target list neither publishes |
| P3 frozen C + attempted coverage | needs an attempted set neither publishes |
| P4 frozen C + realized successful coverage | **selects the population on the measurement's own outcome** |
| P5 missingness-preserving | needs the missingness to be **legible**, which is the missing fact |

P4 is the one that would have worked mechanically, and it is the one the discipline
exists to refuse. P5 is the one this arc would most like to have, and it fails on
exactly the fact §1 names.

## 3. The decision, and the two overstatements refused in opposite directions

**`EXTERNALLY_FROZEN_POPULATION_REQUIRES_OPERATOR_FETCHER`.**

**Calling the architecture INVALID was available and refused.** That would assert that
coverage **is** success-conditioned. No retrieved page establishes it —
**undocumented is not established-as-outcome-dependent**, and this arc has refused the
symmetric shortcut four times in the other direction.

**Calling it UNRESOLVED was available and refused.** The question did close in one
direction: an operator-run fetcher supplies directability and legible missingness *by
construction*, which is precisely what both external routes lack. Reporting UNRESOLVED
would send the next mission back to a search that is finished.

The primary outcome follows the same logic. **The gap is symmetric across both routes**,
so naming either one as individually insufficiently specified would attribute to one
side a fact true of both.

## 4. The request contract was tabulated before any verdict was issued

Fifteen fields. **4 `DIFFERENT_AND_LOAD_BEARING`, 11 `UNKNOWN`, 0 `MATCHABLE`** — so
`REQUEST_CONTRACT_COMPATIBILITY_NOT_ESTABLISHED`, and the shared world-state family is
recorded `SAME_HTTP_WORLD_STATE_FAMILY_PLAUSIBLE_CONDITIONAL` rather than asserted.

**A browser page load is not a crawler fetch**, and HTTP Archive says so about itself:
`is_main_document` is *"the first HTML request after redirects"*, so the row is not the
response to the requested URL. **No redirect predicate binding was chosen here**,
because that choice belongs to a construct nobody has frozen — and choosing it now would
be freezing half a construct while reporting that none was frozen.

## 5. Two smaller refusals that keep the record honest

**Common Crawl's URL selection stays `NOT_ESTABLISHED_THIS_MISSION`.** A search summary
offered an answer and was not used. That is the Mission 1.63 guard, met again — and the
budget was not spent chasing it, because the population question decides the route
whichever way selection resolves.

**A date is not immutability, on either side.** Both are recorded `PARTIAL`, and
`TEMPORAL_COMPATIBILITY_PLAUSIBLE_NOT_ESTABLISHED` follows.

## 6. Rights are feasibility and were not turned into approval

> CC strongly recommends that you obtain the advice of legal counsel before making any
> use, including commercial use

**A recommendation to seek advice is not a grant**, so `ROUTE_RIGHTS_REVIEW_REQUIRED`.
HTTP Archive's licence is absent from its FAQ and its homepage, so `UNKNOWN` — not a
guess in either direction, and not the favourable one. Commercial-purpose compatibility
is `NOT_ESTABLISHED_ON_EITHER_ROUTE`. **0 sources registered, 0 governance mutated, 0
approvals.**

## 7. The operator route is an architecture, and nothing ran

`REQUIRES_DEDICATED_REVIEW`, with the conditions a future review would have to settle
written down. `INDEPENDENCE_ARCHITECTURE_PLAUSIBLE` and **explicitly not independent
because we would run it** — running an apparatus ourselves supplies directability, not
provenance independence, and the record says which one it supplies. Implemented
**false**, crawled **false**, HTTP measurement requests **0**.

The honest residual is recorded rather than smoothed: an operator fetcher is one
apparatus, and a second independent producer for the same construct is still needed.

## 8. Nothing was selected, and the artifact does not exist

Q1 stays `PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED`, unchanged. No class selected, no
construct frozen, no predicate chosen — and **`selected-quantity-class-v1.json` does not
exist**, which the validator enforces both ways: §41 makes the artifact conditional on
strategic viability, so its presence is refused here and its absence is refused in the
positive control where viability holds.

`COVERAGE_SEMANTICS_MUST_DISTINGUISH_ATTEMPT_FROM_SUCCESS` was offered and **not added**.
Two routes exhibiting one shape is one instance, and the standard Mission 1.67 set for
itself is a second instance **in a different shape**. **Registry unchanged at 15.**

Mission 1.69's decision record was not edited, and the validator refuses any record
claiming it was.

## 9. Nothing moved

| | |
|---|---|
| target-value exposures, measurement values, crawls, target HTTP requests | 0 |
| index queries, WARC/WAT/WET downloads, BigQuery executions, HAR downloads | 0 |
| API executions, dataset downloads, count endpoints | 0 |
| trials, purchases, accounts, credential reads | 0 |
| mailbox searches, enquiries sent | 0 |
| sources registered, governance mutations, governance approvals | 0 |
| canonical mutations, thresholds, Claims, Evidence, independence groups, reliability values | 0 |
| model calls, embeddings, migrations | 0 |
| constructs frozen, predicates chosen, pairs selected, crawlers implemented | 0 |

11 of 20 first-party requests, 4 navigation searches, **0 failed**. ONYPHE stays
`NOT_CHECKED_AFTER_DISPATCH`; Netlas stays unresolved with nothing decoded or guessed;
the scanner arc stays parked. **`PAIR_ANALYSIS_NOT_READY`.**

The canonical baseline was measured live before the work and **re-measured after the
database-backed suites** — every counter identical, drift `none`.

## 10. Verification

- Validator probed with **136 deliberate violations, 136 caught** — 133 by rule, 3 by
  drift — plus **5 of 5 positive controls**: an unresolved population architecture, a
  valid pre-value co-coverage architecture, a valid missingness-preserving one, a
  strategically viable Q1 with its artifact and no construct, and an alternative
  no-selection outcome. **The fourth was then checked to be discriminating rather than
  vacuous**: with the artifact removed it is refused by name.
- **`testing-strategy.md` §23 for the eleventh time.** A guard refusing any number under
  a reliability-named key fired on `reliability_assessments`, which is a database row
  count. Repaired by scoping the guard to three **named** census blocks — never by
  loosening what it compares — and the exemption is safe only because every
  reliability-named entry in the third block is in the hard-zero list, which a test now
  asserts rather than assumes.
- Five ruff findings fixed **by hand**, the SIM102 collapse included, and the probe
  re-run afterwards to confirm every guard still fires.
- **One defect in my own tests**, found by reading them rather than by a failure: a check
  on the pages table used a no-op `.replace()` and a substring that asserted nothing
  structural. Replaced with a check over the table's actual columns and its
  `failure_indicator_present` flag.
- **One accuracy defect corrected**: a test asserted a longer spelling of the
  commercial-compatibility value than the record carries. The record was right.
- **104 new tests**; **2311 bare-python tests**; all pytest suites passed with the
  database unchanged across 29 tenant tables; all **40** CI gates.

## 11. Next

**Mission 1.71 — Bounded HTTP Measurement Governance & Apparatus Design V1.** The
question is no longer which external pair to qualify. It is whether an operator-run
bounded fetcher is governance-acceptable, and what an apparatus contract would have to
say about coverage semantics the operator controls — which is the one thing both
external routes could not supply.

**No construct is frozen there either, and broad class discovery does not restart.**

**Mission 1.71 was not started.**
