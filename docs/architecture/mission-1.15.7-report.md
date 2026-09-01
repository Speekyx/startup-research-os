# Mission 1.15.7 — TED-EU Official Search API Collector V1

**Sprint 1. Two phases, in order.** Phase A authorised one concrete resource.
Phase B wrote `ted-search-api@1.0.0` and ran one bounded real acquisition.

**3 RawRecords exist. Nothing downstream does.** No NormalizedRecord, no Signal,
no Claim, no Evidence, no Opportunity, no embedding, no score. **H-36A remains
`NOT ESTABLISHED`. H-36B remains `NOT ADDRESSED`.** No legal clearance was
obtained, claimed or implied.

---

## 1. The two states that were confused, and why Phase A came first

**Source authorization was ready at mission start.** `build_authorization(
'ted-eu', 'local-private-research-v1')` built a context, four of four conditions
satisfied, `AUTHORIZATION_READY` = YES.

**`resource_ready` was NO**, and not for want of a permission. TED's compliance
entry authorised `"datasets": []`, so `context.authorized_dataset(...)` returned
`None` for every resource and `authorize_resource` denied every descriptor for
want of a rights basis and a dataset family. A collector holding that context
would have been refused everything it asked for.

That is the distinction `acquisition-authorization-v1.md` §11 exists for and the
one Mission 1.9.2 separated into its own field: source-level approval is not
resource-level approval. **So the first act of a collector mission was a
governance act**, which is what Mission 1.15.6.1's own report predicted, and
writing the client first would have been the sequence §12 of that mission's
brief exists to forbid.

## 2. Phase A — the resource

| | |
|---|---|
| `resource_id` | **`notices/eforms-contract-and-award`** |
| Contains | eForms **contract notices** (`cn-standard`) and **contract award notices** (`can-standard`) |
| Date scope | **from 2023-03-01**, the documented start of eForms publication |
| `dataset_family` | `ted-search-api-notices` |
| Route | `ted-search-api` |
| `rights_basis` | `NAMED_LICENCE` — Commission Decision 2011/833/EU |
| `content_origin` | `PLATFORM_LICENSED` |
| Profile | `local-private-research-v1`, review v2, and nothing else |

**The id follows the registry's convention rather than the brief's suggestion.**
GDELT's are `web-ngrams/1gram`, World Bank's `indicator/SP.POP.TOTL`: a
collection and a member, source-relative, no source prefix. The brief proposed
`ted-eforms-contract-and-award-notices-search-api` and said to follow existing
conventions if they implied another id. They did. **No query is encoded in it** —
a resource id naming a date window would make every window a new, unreviewed
resource.

### 2.1 The basis, and the classification that decided the mission

The rights basis is the reviewed evidence and nothing new: Decision 2011/833/EU
(read in full in Mission 1.15.2), TED's own legal notice naming it, the
`COM_REUSE` metadata resolving to it, the Search API's published intended use,
local review v2, the route authorization, and the operator's recorded
acceptance.

**`PLATFORM_LICENSED` versus `THIRD_PARTY` was the load-bearing call**, because
`third_party_denied` is true in TED's resource scope: `THIRD_PARTY` would have
refused the resource and stopped the mission at §7.

The documentary link runs at both ends — Article 1 covers what the Publications
Office holds on the Commission's behalf, Article 2(1) what it publishes through
websites and dissemination tools, TED is operated by the Publications Office, and
TED's legal notice names the Decision. Article 2(2)(b) excludes documents the
Commission cannot license *"in view of intellectual property rights of third
parties"*, which is a class of **document**; nothing retrieved across Missions
1.15.1–1.15.4 places procurement notices in it, and this entry asserts nothing
about a document that is.

### 2.2 What it does not establish

H-36A **NOT ESTABLISHED**. H-36B **NOT ADDRESSED**. Not a legal clearance. Not
authorisation for broad extraction. Not reachable from the commercial profile.
And the acceptance it rests on is **conditional and says so**: bounded queries,
field minimisation at acquisition, no redistribution — *"si l'une de ces
conditions cesse d'être vraie, cette acceptation cesse de s'appliquer."*

### 2.3 The gate, proved before any code

```text
notices/eforms-contract-and-award   ted-search-api-notices    ALLOWED
packages/daily-2026-09-01           ted-bulk-xml-daily        REFUSED
packages/monthly-2026-08            ted-bulk-xml-monthly      REFUSED
csv/contract-awards-2018-2023       ted-csv-historical        REFUSED
notices/mystery                     (no family)               REFUSED
same resource, THIRD_PARTY origin                             REFUSED
same resource, no rights basis                                REFUSED
commercial-multi-tenant-research-v1                           REQUIRES_REVIEW
```

`resource_ready` moved to **YES** and the operator-facing next step moved from
*authorise a concrete resource* to *implement a collector*.

## 3. Phase B — the API contract, from first-party sources only

**Was first-party documentation sufficient? Yes, once the right document was
found.** `docs.ted.europa.eu` gives the endpoint and the method and points at a
Swagger interface; the Swagger configuration names `/api-v3.yaml`; that OpenAPI
document — published by the same service — carries the complete request schema,
response schema, error shapes and the documented limits. No third-party tutorial
was used and **no field name was guessed**.

```text
POST https://api.ted.europa.eu/v3/notices/search      no authentication
body: query, fields, page, limit, scope, paginationMode, checkQuerySyntax
response: notices[], totalNoticeCount, iterationNextToken, timedOut
limits (PAGE_NUMBER): 15 000 retrievable, 250 per page, 10 000 fields per page
```

**The query language was established by asking the API**, through its own
`checkQuerySyntax` mode, which the documentation says checks syntax while *"the
search query is not executed"* — and which returned `{"notices":[]}` to every
probe, retrieving no procurement records. It settled the date literal
(`YYYYMMDD`), the space-separated `IN (a b)` list, `SORT BY` without a direction,
and — because value validation also runs at check time — that `cn-standard` and
`can-standard` are values the source recognises.

**Two things it settled that could only otherwise have been guessed:**

- **the API omits a field entirely when a notice has no value for it.** The real
  acquisition requested 24 native fields and received 8. So exactly one field per
  notice is **required** — `publication-number` — and everything else is
  optional. Absent is the key not being there, not a null;
- **the API adds a `links` object to every notice regardless of the field
  selection.** See §6.

## 4. What is requested, and the mapping

14 conceptual fields map to **24 native fields**, all verified present in both
the request enum and the response schema. The closed table is in
`ted-eu-search-api-collector-v1.md` §3.1. Highlights:

| Conceptual | Native |
|---|---|
| `notice_id` | `publication-number`, `notice-identifier`, `notice-version` |
| `monetary_amount` | `total-value`, `tender-value`, `estimated-value-lot`, `framework-maximum-value-lot` |
| `currency` | the four matching `*-cur` companions |
| `buyer_organisation_name` | `organisation-name-buyer` |
| `supplier_organisation_name` | `organisation-name-tenderer` |

**Are personal/contact fields excluded before acquisition? Yes.** The eight
excluded conceptual fields have no row in the mapping table and cannot acquire
one: the gate refuses them alone and hidden among approved fields, before the
table is consulted. **Does `authorize_fields` run before request composition?
Yes**, and the tests prove it with a transport that raises if it is reached at
all — a test asserting only the return value would pass just as happily if the
request had already gone out.

## 5. The bounds, the route and the modes

**Query bounds are mandatory: `date_start`, `date_end`, `max_pages`,
`max_records`, `page_size`.** `TedSearchBounds()` is a `TypeError`,
`TedSearchRequest()` is a `TypeError`, and `TedSearchJobPayload` refuses a
payload missing any of them. `WorldBankJobPayload` defaults its ceilings and is
right to — that source publishes its page size and a rate limit. TED publishes
neither, and the acceptance behind this source is conditioned on the queries
being bounded, so a default here would be a number nobody reviewed on the one
source where it matters most.

**Can it execute with no bounds? No. Can it paginate until exhaustion? No.**
`_pages` is `range(1, max_pages + 1)`; the module contains no `while` loop; the
body never carries `paginationMode: ITERATION` or an `iterationNextToken`. An AST
test asserts all three over the one method that composes the body — scoped to
that method rather than the file, because the module and the bounds *explain* why
scroll mode is refused and a substring scan would fail on the explanation.

**UNKNOWN rate limits** are handled by conservative client behaviour that says
whose it is: one second between requests, at most twenty per job, `origin =
INTERNAL_SAFETY_POLICY`, recorded in every record's provenance as
`rate_limit: UNKNOWN`. No quota is invented.

**Does V1 ever fall back to ODS? No.** `ted-open-data-sparql` is authorised, is
in the context, and is not implemented; when the Search API route is removed the
collector refuses rather than reaching for it. **Bulk XML? Unreachable** — it is
not in `context.access`, so it has no endpoint and no host to allowlist.
**Historical CSV? Refused** at the resource gate by family.

**The transport obtains the host from the endpoint the registry records for the
authorised route**, checked again inside the transport as the last step before a
socket. The module names no TED host of its own.

## 6. `links`, and the §14 inspection

The API returned a `links` object on every notice. It was **not requested** and
no `fields` value suppresses it.

It was inspected before the records were accepted. It contains the URLs of the
notice itself, per format and per language — `pdf`, `pdfs`, `html`,
`htmlDirect`, `xml`, each keyed by 24 language codes. Scanned across the whole
payload: **zero email addresses, zero telephone numbers, and no key containing
`contact`, `person`, `address`, `street`, `postal`, `tel`, `fax` or `ubo`.**

**No natural-person field was requested and none was received.** `links` is
preserved verbatim, because a RawRecord that dropped part of what the source
returned would not be raw, and downstream deletion is explicitly not the control
here — the `fields` parameter is, and it governs everything it can. It is ~94% of
each record's bytes, which is a size fact and is named in the response contract
so no reader is surprised by it.

## 7. Identity, lots, languages, money

**RawRecord identity is source-native**: `publication-number`, plus
`notice-identifier` and `notice-version` **where the source publishes them** —
and for the three real notices it published neither, so the key rests on the
publication number alone rather than on a placeholder that would make two
notices look alike. Never page position, never result order.

**Lots** are preserved: one notice is one record, parallel per-lot arrays arrive
intact, nothing deduplicates on the notice number, and a one-element array is
unwrapped only for identity reads.

**Languages**: the Search API request carries no language selector — there is no
such parameter in its schema — so V1 makes no language decision and stores the
multilingual objects as they arrived.

**Monetary semantics**: four amounts under four names, each with its own currency
companion. **Was `price_paid` created? No**, asserted over the AST. **Was
currency converted? No** — no rate, no table, no arithmetic on an amount; a
three-lot notice with `["EUR", "EUR", "SEK"]` keeps SEK. `monetary_amount_type`
maps to no separate native field because TED carries the semantic in the field
name, and it is *required* alongside `monetary_amount` rather than optional.

**`observed_at` is left NULL, deliberately.** `publication-date` is in the
payload and is not promoted to the canonical instant: no mission has established
TED's temporal semantics, and a plausible instant is worse than a declared
absence.

## 8. The production path, and what cannot bypass it

```text
runtime use profile -> read_human_decisions -> resolve_effective_verifications
  -> build_authorization -> resource -> route -> fields -> bounds
  -> collector -> transport -> RawRecord persistence
```

`run_ted_search_job` runs exactly that, in the caller's tenant transaction, and
checks `collector_enabled` before anything is fetched. **No authorization context
is manufactured by hand**; `collect` takes one positionally with no default and
there is no convenience constructor.

**Can it execute under `commercial-multi-tenant-research-v1`? No** — that review
is `REQUIRES_REVIEW` and the authorization does not build, so there is nothing to
hand a collector.

`acquisition_cli.py:_context` was **not** touched: TED does not use it, and
Mission 1.15.6.3 recorded why redesigning it is its own decision. The gateway's
SQL-view distinction was not touched either.

## 9. The real acquisition

| | |
|---|---|
| Query | `(notice-type IN (cn-standard can-standard)) AND (publication-date>=20230301) AND (publication-date<=20230301) SORT BY publication-date` |
| Route | `ted-search-api` · `https://api.ted.europa.eu/` |
| Fields | 24 native, from 14 conceptual |
| Window | 2023-03-01 → 2023-03-01 (one day) |
| Bounds | `max_pages=1`, `max_records=3`, `page_size=3` |
| HTTP requests | **1** |
| Notices returned | 3 |
| **RawRecords persisted** | **3 new** |
| Payload size | 4 764 – 4 778 bytes each |
| Timestamp | 2026-09-01T05:32:59Z |
| Natural-person fields | **none requested, none received** |

**Re-run identically: 0 new, 3 unchanged, 0 revised**, same idempotency key, same
record ids, nothing superseded. Acquisition is idempotent through the existing
persistence semantics; nothing TED-specific was invented for it.

Enabling the collector in this deployment (`sros-source enable ted-eu`) was a
separate, deliberate operator act, refused by the CLI until eligibility and an
implemented collector both held.

## 10. Local counts, before and after

| | before | after |
|---|---|---|
| `acquisition.raw_records` | 12 | **15** |
| — of which `ted-eu` | 0 | **3** |
| `acquisition.normalized_records` | 12 | 12 |
| — of which `ted-eu` | 0 | **0** |
| `nlp.signals` | 7 | 7 |
| `research.claims` / `claim_revisions` | 7 / 7 | 7 / 7 |
| `scoring.evidence` | 7 | 7 |
| `research.opportunities` | 0 | 0 |
| `epistemic.reliability_assessments` | 0 | 0 |
| `nlp.embedding_provenance` | 0 | 0 |
| human decision rows | 1 | **1** |

**The recorded human decision is unchanged**: same `verified_at`
(2026-09-01T04:29:04.074626Z), same verifier `local-operator`, same result
`SATISFIED`, same 1 683-character reason. **No governance row was written by this
mission.**

Only RawRecords were created, and only for TED.

## 11. Tests

`test_ted_search_api_collector.py`, **107 cases, no network and no database**,
with `ted_search_fixtures.py`: a contract notice, an award notice, a three-lot
notice, a notice with no monetary block, a notice with no identity, and four
malformed responses. Every fixture value is invented and organisation-level, and
a test asserts no fixture carries a natural-person field — a fixture is where a
contact block would most plausibly arrive without anybody deciding to add one.

Coverage: resource governance; route binding and the absence of a fallback; field
minimisation including every excluded field alone and in company; bounds at both
the request and the job-payload level; the expert query; response handling; raw
identity; contract drift; provenance, pacing and retention; and the whole
production sequence with the persisted decision supplied rather than a merged
verification set.

**Twenty-five existing tests were inverted, not deleted**, across ten files: each
asserted a state this mission was authorised to change. Where a guard protected
two properties, the surviving one was kept — *there is still no TED normalizer*
is this mission's own stop condition, and deleting
`test_no_ted_collector_or_normalizer_exists` would have lost it. Recorded as
`testing-strategy.md` §54.

## 11.1 A defect the acquisition surfaced, found and not fixed

The gateway's `/api/v1/sources` endpoint **returns `ted-eu` twice**, with two
different verdicts, and pairs each with the same source-level
`collector_enabled`.

`registry.source_eligibility` became one row per **(source, profile)** in
Mission 1.15.5. The endpoint joins it on `source_id` alone, so the first source
reviewed under two profiles is duplicated — and once the collector was enabled,
one of those rows read `collector_enabled: true` beside
`collector_eligible: false`, a pair the database would refuse.

**The database is correct.** `require_eligibility_for_collector` (migration
0021) looks up the row for the profile enablement was granted under, found zero
blocking reasons for `local-private-research-v1`, and allowed it. The view has
both rows and both are right.

**The duplication predates this mission** — it has existed since Mission 1.15.5
created TED's second review — and enabling the collector only made its second
symptom visible.

**This is the third appearance of one defect: a verdict reported with no
subject.** ADR-027 gave verdicts a subject; Mission 1.15.6 fixed four CLI
reporting commands; Mission 1.15.6.3 fixed readiness. The HTTP layer was never
re-checked.

**Not fixed here, deliberately.** Which profile the endpoint should answer about
is a design decision with no default — it takes no profile parameter — and §21
of this brief says the gateway's view-reading is intentional and not this
mission's to change. The test now asserts the **defect** rather than the
property it can no longer hold, so it fails the day the endpoint is fixed and
the comment explaining it gets deleted along with it.

## 12. Answers

| Question | Answer |
|---|---|
| Source authorization ready at start? | **Yes** — 4/4 conditions, context builds |
| Why was `resource_ready` NO? | `"datasets": []`; a source approval is not a resource approval |
| Exact resource added? | eForms contract + contract award notices, from 2023-03-01, via the Search API |
| Canonical id? | `notices/eforms-contract-and-award` |
| Families? | `cn-standard`, `can-standard` |
| Date scope? | 2023-03-01 onward |
| Route? | `ted-search-api` only |
| Rights basis? | `NAMED_LICENCE` — Decision 2011/833/EU, `PLATFORM_LICENSED` |
| H-36A changed? | **No — NOT ESTABLISHED** |
| H-36B changed? | **No — NOT ADDRESSED** |
| `resource_ready` now? | **YES**, for this resource only |
| Contract established? | POST `/v3/notices/search`, from the OpenAPI document and `checkQuerySyntax` |
| First-party docs sufficient? | Yes |
| Fields requested? | 24 native from 14 conceptual |
| Personal fields excluded before acquisition? | **Yes** — no mapping row exists for them |
| `authorize_fields` before composition? | **Yes**, proved with a raising transport |
| Mandatory bounds? | date window, `max_pages`, `max_records`, `page_size` |
| Can it run unbounded? | **No** — `TypeError`, and the job payload refuses |
| Can it paginate to exhaustion? | **No** — no `while`, no `ITERATION`, no token |
| UNKNOWN rate limit? | conservative pacing labelled `INTERNAL_SAFETY_POLICY` |
| Falls back to ODS? | **No** |
| Reaches bulk XML? | **No** — absent from `context.access` |
| Reaches historical CSV? | **No** — family refused |
| Transport host? | from the authorised route's registered endpoint |
| Collector id/version? | `ted-search-api@1.0.0` |
| RawRecord identity? | `publication-number` (+ identifier/version where published) |
| Lots? | preserved; nothing deduplicated on the notice number |
| Languages? | no selector exists; nothing chosen; objects stored whole |
| Monetary semantics? | four names kept apart |
| `price_paid` created? | **No** |
| Currency converted? | **No** |
| Retention? | platform baseline, 30 days raw, from the context |
| Idempotent? | **Yes** — 0 new / 3 unchanged on re-run |
| Executes without authorization? | **No** |
| Executes under the commercial profile? | **No** |
| Offline fixtures added? | **Yes**, sanitized and invented |
| All tests/gates pass? | **Yes** — §13 |
| Real smoke attempted? | **Yes**, and it succeeded |
| Records returned / persisted? | 3 / 3 |
| Natural-person fields present? | **None** |
| NormalizedRecords / Signals / Claims / Evidence? | **None** |
| Opportunities / embeddings / scores? | **None** |

**Final state:** SOURCE AUTHORIZATION **yes** · RESOURCE READY **yes** ·
COLLECTOR IMPLEMENTED **yes** · REAL RAW ACQUISITION **yes (3 records)** ·
NORMALIZER READY **no**.

## 13. Validation

| Check | Result |
|---|---|
| zero-dependency suites | 515 tests across 8 packages |
| pytest suites | 7 packages, all pass (acquisition: 1 311 + 11 skipped) |
| seven validators | schema, source registry, compliance capabilities, normalization, signals, claims, evidence aggregation — OK |
| contract generation `--check` | current |
| catalog render `--check` | matches |
| `ruff check` / `ruff format --check` | clean, 440 files |
| `mypy` | no issues, 142 source files |
| environment template secret check | OK |
| `assert_registry_grants_nothing` | OK |

## 14. Next

**Sprint 1 — Mission 1.15.8, TED Raw → Normalized V1.** Three RawRecords exist
and nothing can read them yet. The mapping from a TED notice to a canonical
record is the next question, and it starts with the ones this mission
deliberately left open: what a `publication-date` with a `+01:00` offset and no
established timezone semantics means, whether a multilingual name object becomes
one canonical name or several, and how four monetary semantics survive
normalization without being flattened into one.
