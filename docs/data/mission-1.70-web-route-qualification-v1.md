# Mission 1.70 — Fixed-corpus web route qualification

Generated from `quantity-class-selection-decision-v2.json` and the route records.
Do not edit by hand.

**Primary outcome: `FIXED_CORPUS_WEB_REQUIRES_OPERATOR_CONTROLLED_ROUTE`**

**Class status: `PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED`. Selected class: NONE.**

## Routes

| route | status | produces its own observations |
|---|---|---|
| COMMON_CRAWL | `ROUTE_PLAUSIBLE_REQUIRES_CONSTRUCT_DETAIL` | True |
| HTTP_ARCHIVE | `ROUTE_PLAUSIBLE_REQUIRES_CONSTRUCT_DETAIL` | True |
| SROS_BOUNDED_HTTP_FETCHER | `ROUTE_UNRESOLVED` | WOULD, IF BUILT AND AUTHORISED |

## Q1 strategic conditions

| condition | state |
|---|---|
| 1 population architecture valid | NOT_SATISFIED |
| 2 common crawl route at least plausible | SATISFIED |
| 3 second route at least plausible or governed operator fetcher | SATISFIED_FOR_HTTP_ARCHIVE |
| 4 two routes produce their own http observations | SATISFIED |
| 5 same http world state family plausible | PLAUSIBLE_CONDITIONAL |
| 6 temporal preselection plausible | SATISFIED |
| 7 commercial purpose not blocked on both routes | NOT_ESTABLISHED |
| 8 future construct freezable without values | BLOCKED_BY_1 |

**Verdict: NOT_STRATEGICALLY_VIABLE**, failing on condition 1, the population architecture.

## Request-contract compatibility

| field | Common Crawl | HTTP Archive | classification |
|---|---|---|---|
| `METHOD` | NOT_DOCUMENTED | NOT_DOCUMENTED | UNKNOWN |
| `SCHEME` | NOT_DOCUMENTED | NOT_DOCUMENTED | UNKNOWN |
| `HOST` | NOT_DOCUMENTED | the page URL under test | UNKNOWN |
| `SNI` | NOT_DOCUMENTED | NOT_DOCUMENTED | UNKNOWN |
| `USER_AGENT` | CCBot/2.0 (https://commoncrawl.org/faq/) | a desktop Chrome string and an emulated Moto G4 mobile Chrome string | DIFFERENT_AND_LOAD_BEARING |
| `ACCEPT_HEADERS` | NOT_DOCUMENTED | NOT_DOCUMENTED | UNKNOWN |
| `REDIRECT_POLICY` | a fetch_redirect field records the target of a redirect | the main document is the first HTML request AFTER redirects | DIFFERENT_AND_LOAD_BEARING |
| `JS_EXECUTION` | not documented; a crawler fetch | real browsers execute JavaScript | DIFFERENT_AND_LOAD_BEARING |
| `COOKIES` | NOT_DOCUMENTED | NOT_DOCUMENTED | UNKNOWN |
| `CACHE` | NOT_DOCUMENTED | empty cache, logged out | UNKNOWN |
| `DNS` | NOT_DOCUMENTED | NOT_DOCUMENTED | UNKNOWN |
| `IP_VERSION` | IPv6 is used; reverse DNS not yet supported there | NOT_DOCUMENTED | UNKNOWN |
| `GEOGRAPHY_VANTAGE` | NOT_DOCUMENTED | Google Cloud Platform locations based in the USA | DIFFERENT_AND_LOAD_BEARING |
| `TIMEOUT` | a truncation reason of time implies a bound | NOT_DOCUMENTED | UNKNOWN |
| `RETRY` | NOT_DOCUMENTED | a retry_count is recorded per test | UNKNOWN |

**REQUEST_CONTRACT_COMPATIBILITY_NOT_ESTABLISHED** — 4 load-bearing differences and 11 unknowns.

## Rights

| route | classification |
|---|---|
| COMMON_CRAWL | `ROUTE_RIGHTS_REVIEW_REQUIRED` |
| HTTP_ARCHIVE | `UNKNOWN` |

Commercial-purpose compatibility: **NOT_ESTABLISHED_ON_EITHER_ROUTE**.

## The operator route

**REQUIRES_DEDICATED_REVIEW.** Every source in the registry is a named publisher, and a fixed-corpus fetcher measures many third-party sites none of which is a registered source. The source-governance model has no shape for 'a corpus of arbitrary public sites', and inventing one in passing is the change-control shape docs/CLAUDE.md refuses.

*The honest residual:* An operator fetcher fixes OUR side of the population problem. It does not fix the archive's, so a pair would still need one archive whose attempt-level coverage is documented. That is the question the next mission inherits.

## What changed and what did not

**Resolved this mission:**

- HTTP Archive exposes structured response headers and text bodies, which Mission 1.69 left open
- HTTP Archive's main-document row binds to the first HTML request AFTER redirects
- HTTP Archive carries attempt-level metadata: retry_count, tested_url, visited
- Common Crawl's index fields, including that its coverage surface carries HTTP status codes
- Common Crawl's columnar schema semantics for fetch_status, fetch_redirect and content_truncated
- Common Crawl's terms position on commercial use
- that the population question has a definite answer for the external pair

**Still unresolved:**

- Common Crawl's URL selection mechanism
- whether either route's coverage means attempted or captured
- whether HTTP Archive represents failed tests
- artifact immutability on both sides
- HTTP Archive's data licence
- eleven of fifteen request-contract fields

## Registry

Unchanged at 15. A candidate rule was offered and not added: `COVERAGE_SEMANTICS_MUST_DISTINGUISH_ATTEMPT_FROM_SUCCESS`.

Mission 1.67 set the standard when it adopted the previous candidate: a second independent instance in a DIFFERENT SHAPE. Common Crawl and HTTP Archive are two apparatuses in the same class exhibiting the same shape once. That is one instance seen twice.

## Nothing moved

| | |
|---|---|
| TARGET_VALUE_EXPOSURES | 0 |
| CRAWLS | 0 |
| TARGET_HTTP_REQUESTS | 0 |
| COMMON_CRAWL_INDEX_QUERIES | 0 |
| WARC_WAT_WET_DOWNLOADS | 0 |
| BIGQUERY_EXECUTIONS | 0 |
| CREDENTIAL_READS | 0 |
| MAILBOX_SEARCHES | 0 |
| SOURCES_REGISTERED | 0 |
| GOVERNANCE_APPROVALS | 0 |
| CONSTRUCTS_FROZEN | 0 |
| PREDICATES_CHOSEN | 0 |
| CRAWLERS_IMPLEMENTED | 0 |
| MODEL_CALLS | 0 |
