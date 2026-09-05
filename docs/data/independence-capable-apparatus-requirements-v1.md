# Independence-Capable Apparatus — Requirements V1

**Mission 1.57 — Independence-Capable Evidence Route Feasibility V1 — recorded 2026-09-05.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_independence_route.py`.

Folds forward `docs/data/falsifiable-evidence-apparatus-requirements-v1.json`.

## What changed, and what did not

**Then.** Mission 1.48 specified an apparatus pair and recorded that no pair could be used, because source attribution was proposition identity: a second apparatus produced its own Claim and could neither join a support group nor contradict anything.

**Now.** ADR-036 puts source-independent propositions in the INFERRED layer and Mission 1.56 persisted one. Two apparatuses can now reach ONE Claim.

**Unchanged.** Semantics and provenance. The INFERRED layer fixes Claim IDENTITY. It does not make two measurements of different things the same thing, and it does not make a republication independent.

*It is the one way this mission could go wrong: reopening a route Mission 1.46 refuted on provenance, on the grounds that the architecture changed.*

## What an apparatus is

Not: a website, an API, a URL, a company, a dataset page.

But: `measurement_producer`, `measurement_method`, `upstream input lineage`, `operational metric definition`, `population or frame`, `time semantics`, `unit`, `publication route`.

Two URLs are not two apparatuses. Two companies are not automatically two apparatuses. Two APIs are not automatically independent. Independence is a property of measurement lineage.

## The fifteen mandatory gates

|  | gate | rule |
| --- | --- | --- |
| 1 | `SAME_EXTERNAL_CONSTRUCT` | Both apparatuses measure the same external phenomenon, not two proxies for one inferred latent concept. |
| 2 | `EXACT_CANONICAL_SUBJECT` | The same canonical entity, population or category, matched by exact equality. No fuzzy matching, no embeddings, no model mapping. |
| 3 | `METRIC_DEFINITION_COMPATIBILITY` | Identical definitions, or a documented deterministic equivalence. Pageviews and users, questions and demand, award values and payments, downloads and installations, requests and unique visitors, intention and adoption are each two things. |
| 4 | `UNIT_COMPATIBILITY` | The same unit, or an exact reviewed deterministic conversion. No conversion is strongly preferred. |
| 5 | `TIME_COMPATIBILITY` | The same exact reference period or point semantics. Overlap is not alignment, and a 1 January stock is not a midyear estimate. |
| 6 | `POPULATION_OR_FRAME_COMPATIBILITY` | The same defined population, frame or geography. Different populations are complementary, never contradictory. |
| 7 | `EACH_ALONE_ENTAILS_THE_CLAIM` | Either measurement alone must suffice to evaluate SUPPORTS or CONTRADICTS. A pair that needs a conjunction to mean anything is one measurement in two halves. |
| 8 | `NO_SHARED_UPSTREAM_MEASUREMENT` | Affirmative evidence about lineage. Republisher, mirror, a vendor consuming the same official feed, one source quoting the other, or two databases receiving one measurement are all rejected. UNKNOWN stays UNKNOWN. |
| 9 | `DIFFERENT_MEASUREMENT_PRODUCTION` | Genuinely distinct measurement processes. Two transformations of one upstream observation do not qualify. |
| 10 | `FIRST_PARTY_LINEAGE_DOCUMENTATION` | Independence must be supportable from first-party documentation for BOTH sides. Not a forum summary, not a blog asserting independence, not an inference from organisation names. |
| 11 | `RELIABILITY_REVIEWABILITY` | First-party methodology accessible enough for a human to perform the exact five-field reliability review later, for BOTH eventual scopes. Mission 1.47 paid for learning this late. |
| 12 | `GOVERNANCE_FEASIBILITY` | A lawful, policy-compatible future acquisition path must be plausible. Public availability is not permission, and an unregistered source is NOT_YET_REVIEWED rather than approved. |
| 13 | `THRESHOLD_FREEZABLE_INDEPENDENTLY_OF_RESULTS` | The threshold must be settable without looking at either future measurement. PREREGISTERED, SOURCE_NATIVE or EXTERNAL_NORM preferred; POST_HOC is a limitation to record, not a plan. |
| 14 | `FALSIFIABLE_IN_BOTH_DIRECTIONS` | Observations must exist that would yield SUPPORTS and observations that would yield CONTRADICTS. No monotone existential. |
| 15 | `STRUCTURALLY_USEFUL` | Two independent supports must be able to form more than one provenance group, and disagreeing directions must be able to sit on one Claim. Demonstrated symbolically against the current Claim identity, not asserted. |

## The independence proof standard

Insufficient:

- they are separate organisations
- no dependency was found
- the data look different
- different hostnames, different APIs, different licences
- a third party describes them as independent

Required, all four:

- A does not obtain its measured value from B
- B does not obtain its measured value from A
- neither simply republishes a common upstream measurement
- the underlying observations are generated through distinct processes

Partial evidence yields **UNKNOWN**. It is a failure to establish the proof this mission requires, and it is not converted into independence by the absence of a counterexample.

## Named traps

| trap | rule |
| --- | --- |
| `GEOGRAPHIC_INDEPENDENCE` | Two national agencies measuring two different countries are independent producers of different propositions. Independence without the same proposition is useless here, and both properties are mandatory. |
| `SURVEY_INDEPENDENCE` | Two genuinely independent surveys can still fail semantic equivalence on sampling frame, question wording, response mode, weighting, reference date or population. |
| `MARKET_DATA_INDEPENDENCE` | Two vendors publishing one price that both take from the official feed are one measurement. |
| `STATISTICAL_AGENCY` | Trace the series. If one republishes the other it is DEPENDENT; if both receive data from the same national agency it is COMMON_UPSTREAM; only genuinely separate inputs can be independent. |
| `SAME_APPARATUS_REVISION` | Two revisions, or two snapshots, from one apparatus are one measurement process correcting itself, never two witnesses. |
| `ESTIMATE_VERSUS_MEASUREMENT` | Do not mix MEASURED, ESTIMATED and PREDICTED without an explicit equivalence decision, and do not call two modelled estimates independent when both consume one dataset. |
| `COMPLEMENTARITY` | Search interest and sales, pageviews and questions, stars and downloads, postings and salaries, award value and vendor revenue. Each pair may support one Opportunity and neither measures one proposition. Verdict COMPLEMENTARY_NOT_CORROBORATING. |
| `FRAME_INSIDE_THE_DEFINITION` | An apparatus that measures 'share within its own network' has put its own frame into the metric definition. A proposition admitting two such apparatuses must define the event class as a DISJUNCTION of their frames, which relocates source attribution from the subject of the sentence into its predicate. Mission 1.47 found this once and named it; it recurs wherever a measurement is defined relative to the measurer's own reach. |

## No value may be fetched during feasibility

**No candidate measurement VALUE may be fetched during feasibility research. Methodology and schema documentation only.**

If a route is selected, the next mission must be able to register the threshold BEFORE either measurement enters this system. PREREGISTERED is defined against RETRIEVAL, so a value retrieved during feasibility work makes an honest PREREGISTERED classification impossible for ever afterwards.

*The route becomes POST_HOC permanently, and the whole point of preferring it over the held-data pilot is lost.*

