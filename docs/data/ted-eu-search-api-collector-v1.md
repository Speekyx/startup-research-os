# TED-EU Search API Collector V1

**Authoritative.** Mission 1.15.7 Phase B, revised by Mission 1.15.10 Phase A.
`ted-search-api@1.1.0`: what it may do, what it cannot do, and where each limit
is enforced.

**Three real bounded acquisitions have run**, one under 1.0.0 and two under
1.1.0, one HTTP request and one page each. The notices they collected have since
been normalized (Mission 1.15.8) and one Signal has been derived from them
(Missions 1.15.9 and 1.15.10). **Still no Claim, no Evidence, no Opportunity, no
embedding, no score.**

---

## 1. Identity

| | |
|---|---|
| Collector | `ted-search-api`, version `1.1.0` |
| Previous version | `1.0.0`, superseded by the repair in §5.1; records collected under it are still readable, see §5.2 |
| Module | `sros_acquisition/collection/ted_search_api.py` |
| Route | `ted-search-api`, and no other |
| Resource | `notices/eforms-contract-and-award`, and no other |
| Profile | whatever the runtime declares; only `local-private-research-v1` authorises anything |
| Job | `run_ted_search_job` in `collection/job.py` |

## 2. Four gates, all before a socket

```text
bounds    -> a query with no ceiling is refused, and no default supplies one
route     -> taken from context.access BY LABEL, never hard-coded
resource  -> context.authorize_resource, built from the context's own entry
fields    -> context.authorize_fields, on the CONCEPTUAL names
```

Each refusal costs **zero** network calls, and the tests prove that with a
transport that raises if it is reached at all — a test asserting only the return
value would pass just as happily if the request had already gone out.

### 2.1 The route

Resolved out of `context.access` by label. After Mission 1.15.6 that tuple
carries only reviewed routes, so `ted-bulk-xml` is not in it, has no endpoint,
and cannot be reached. The transport host allowlist is derived from the endpoint
the registry records, and the module names no TED host of its own.

**`context.access[0]` is not used**, and the reason is on record:
`GdeltWebNgramCollector._route` documents the hazard, and TED is the source for
which it stopped being hypothetical.

### 2.2 No fallback

`ted-open-data-sparql` **is** an authorised route and **is** in the context. This
collector does not implement it and does not fall back to it. If the Search API
fails, the collection fails.

A fallback between two authorised routes sounds harmless and is not: it turns a
route the review reasoned about into a route the runtime picked, and the next
fallback added is the one to a route the review refused. There is no code path
to ODS, to bulk XML, to the historical CSV, to HTML or to any undocumented
endpoint.

## 3. Field minimisation, at acquisition

The order is mandatory and is the order in the code:

```text
conceptual selection -> context.authorize_fields(...) -> map to native -> compose -> network
```

Never collect-then-filter. The Search API has a `fields` parameter, so a request
that took the contact block and discarded it afterwards **would have retrieved
the contact block**, and the obligation is about what is retrieved. There is
deliberately no method in this module that removes a field from a collected
notice.

### 3.1 The mapping

Policy authorises **conceptual** fields; TED returns **source-native** ones. The
table is closed: a native field no conceptual field maps to cannot be requested.

| Conceptual | TED fields | Why |
|---|---|---|
| `notice_id` | `publication-number`, `notice-identifier`, `notice-version` | identity as TED identifies it; the version distinguishes a corrected notice from the one it corrects |
| `publication_date` | `publication-date` | the field the bounded query filters on |
| `award_date` | `winner-decision-date` | a different event from the contract date, never inferred from it |
| `contract_date` | `contract-conclusion-date` | likewise |
| `buyer_organisation_name` | `organisation-name-buyer` | an ORGANISATION, not a person |
| `supplier_organisation_name` | `organisation-name-tenderer` | likewise |
| `cpv_code` | `classification-cpv` | as published; not expanded or rolled up |
| `procurement_classification` | `contract-nature`, `notice-type`, `form-type` | requested rather than assumed from the query, so a record is not classified by the filter that fetched it |
| `monetary_amount` | `total-value`, `tender-value`, `estimated-value-lot`, `framework-maximum-value-lot` | **four different things, kept apart** |
| `monetary_amount_type` | *(carried by the field name)* | see §5 |
| `currency` | `total-value-cur`, `tender-value-cur`, `estimated-value-cur-lot`, `framework-maximum-value-cur-lot` | one companion per amount, matched by name |
| `country_code` | `organisation-country-buyer`, `place-of-performance-country-lot` | where the buyer is and where the work happens are two questions |
| `region_code` | `place-of-performance-subdiv-lot` | the NUTS subdivision as published |
| `award_status` | `winner-selection-status` | absence would otherwise be indistinguishable from not asking |

24 native fields. Every one appears both in the API's `fields` enum and in its
response schema, checked against the OpenAPI document.

### 3.2 The excluded block

`contact_point`, `contact_name`, `contact_email`, `contact_telephone`,
`contact_fax`, `postal_address`, `natural_person_name`, `personal_identifier`
have **no row in the table** and cannot acquire one by accident: the minimisation
gate refuses them before the table is consulted, alone and hidden among approved
fields, and a conceptual field with no mapping stops the request rather than
being quietly dropped.

The one field that arrives unrequested — `links` — was inspected and carries
only per-language URLs of the notice itself
(`ted-eu-search-api-response-contract-v1.md` §5.3).

## 4. Bounds

**`TedSearchBounds` has no defaults.** `TedSearchBounds()` is a `TypeError`, and
so is `TedSearchRequest()`. `TedSearchJobPayload` refuses a payload that omits
any of `date_start`, `date_end`, `max_pages`, `max_records`, `page_size`.

`WorldBankJobPayload` defaults its ceilings and is right to: that source
publishes its page size and a rate limit. TED publishes neither, and the operator
acceptance this source rests on is **itself conditioned on the queries being
bounded**. A default here would be a number nobody reviewed, on the one source
where that matters most.

Refused at construction: a window starting before `2023-03-01`; a reversed
window; any ceiling below 1; a page size over TED's documented 250; a record cap
over TED's documented 15 000; a `page_size x field_count` over 10 000.

**There is no exhaustion mode.** `_pages` is `range(1, max_pages + 1)`. The
module contains no `while` loop, the request body never carries
`paginationMode: ITERATION` or an `iterationNextToken`, and an AST test asserts
all three over the method that composes the body.

Collection also stops early, and says which bound stopped it: `max_records`
reached, last page of the window, no further notices, `max_pages` reached.

## 5. Monetary semantics

**No `price_paid` exists anywhere in this module**, asserted over the AST.

TED publishes four different amounts under four names, each with its own currency
companion, and they are not interchangeable: a total value, a tender value, an
estimated lot value and a framework maximum. **The type is the field name** —
which is why `monetary_amount_type` maps to no separate native field and is
nonetheless *required* alongside `monetary_amount`: a collector that cannot say
which kind of amount it retrieved has not retrieved a usable one, and requesting
amounts without it is refused.

**No currency is converted.** No rate, no table, no arithmetic on an amount, no
normalisation to EUR. A three-lot notice with `["EUR", "EUR", "SEK"]` keeps SEK.

### 5.1 Exact decimals, and the version bump that came with them

`1.0.0` parsed the response with a bare `json.loads`, so every JSON number
carrying a fractional part became a **binary float**. The manifest's invariant
is that a number crossing a boundary keeps its decimal identity, and a float
does not: `0.1 + 0.2` is the standard demonstration, and a tender value is
exactly the kind of number where the last cents are the point.

`1.1.0` parses with `parse_float=Decimal` and then renders each `Decimal` back
through `canonical_number`, so what reaches jsonb is a **fixed-point string**:

```text
1.0.0   "value": 73415.22        jsonb_typeof -> number   (a float, already lossy)
1.1.0   "value": "73415.22"      jsonb_typeof -> string   (exact, as published)
```

`parse_int` is deliberately **not** set. An integer in JSON is already exact in
Python, and wrapping it would change the shape of a value that was never at
risk. Integers therefore stay `number` in jsonb, and only fractional values
become strings. That asymmetry is intentional and is asserted by the tests.

This is a **payload-shape change**, which is why it is a version bump and not a
patch: a record collected under `1.0.0` and one collected under `1.1.0` for the
same notice do not have byte-identical payloads.

### 5.2 What the bump does NOT do

It does not invalidate anything already collected. The normalizer declares
`supported_collector_versions = {"1.0.0", "1.1.0"}` and reads both shapes, and
it is **not** itself bumped, because its own output is unchanged: it already
went through `canonical_number` on the way out. The float-era records remain
readable and remain lossy, and re-collecting a notice under `1.1.0` supersedes
the old payload through the ordinary revision path, not through a migration.

## 6. Narrowing by CPV division

`cpv_division` is a **two-digit** string. It is not a filter applied after the
fact: it is rendered into the expert query itself, as
`(classification-cpv=90*)`, and joined to the date bounds with `AND`. What the
service sees is already narrowed, which is the only place narrowing counts —
a client-side filter would still have asked TED for everything.

It is part of the idempotency key, so the same window at two different
divisions is two different acquisitions rather than one that quietly changed
meaning.

**A notice can carry codes from more than one division**, and TED matches it if
any of them match. Narrowing to `90` therefore returns notices that are partly
about something else, and it does **not** return every notice that touches
division 90 in a window if the query bound the window differently. Neither is a
defect; both are what a prefix match on a repeated field means.

## 7. Raw identity, lots and languages

**Identity is source-native.** `publication-number`, plus `notice-identifier` and
`notice-version` where the source publishes them. Never page position, never
result order, never a local sequence. The same notice retrieved on page 1 and on
page 3 is one record; a corrected notice at version 2 is a different object from
version 1.

**Lots are preserved and never collapsed.** One notice is one record, and its
parallel per-lot arrays arrive intact. Nothing deduplicates on the notice number;
a one-element array is unwrapped only for identity reads, and a longer one never
is.

**No language is chosen.** The Search API request carries no language selector —
there is no such parameter in its schema — so V1 makes no language decision.
Multilingual objects (`{"eng": [...], "fra": [...]}`) are stored as they arrived.

**`observed_at` is left NULL, deliberately.** `publication-date` is a real
published date and is *in the payload*. It is not promoted to the canonical
instant, because no mission has established TED's temporal semantics — no
timezone, no certification. H-29's discipline applied to a second source before
anybody needs it: a plausible instant is worse than a declared absence.

## 8. Provenance

Every record carries, through `build_raw_record` and not through anything this
collector invents: source, access profile, access method, endpoint, review
version, approval state, resource id, dataset family, licence, rights basis,
content origin, licence basis, rendered attribution, retention days and basis,
the condition snapshot, the authorization issue time and the authorised
minimisation set.

The collector adds its own vocabulary under those: publication number, notice
identifier and version, the exact expert query, the requested conceptual and
native field lists, the notice types, the date window, the page,
`pagination_mode`, `rate_limit: UNKNOWN` and
`acquisition_bounds_origin: INTERNAL_SAFETY_POLICY`.

Collector keys are merged **under** the governance facts, so none can shadow a
review version or a rights basis by choosing a name.

## 9. Rate limiting and pacing

TED's rate limit is **UNKNOWN** and stays that way. `TED_PACING` is one second
between requests and at most twenty requests per job, `origin =
INTERNAL_SAFETY_POLICY`, with a basis recorded on the policy itself. Timeouts,
the redirect refusal and the response ceiling come from the shared transport
config. **None of it is a claim about a TED quota.**

## 10. Failure handling

Missing use profile; authorization refused; missing human decision; unauthorized
resource, route or field; missing bounds; timeout; connection failure; non-2xx;
429; malformed JSON; unexpected response shape; missing identity; contract drift
— each produces a classified `AcquisitionFailure` and **no record**. A page that
fails mid-collection keeps the drafts already built and reports the failure
beside them; nothing valid-looking is persisted from an invalid response.

## 11. The production path

```text
runtime use profile
  -> read persisted human decisions   (read_human_decisions, via the tenant connection)
  -> resolve effective verification   (machine live, human from persistence)
  -> build AcquisitionAuthorizationContext
  -> authorize the concrete resource
  -> authorize the route
  -> authorize the field set
  -> validate the bounds
  -> collector
  -> transport
  -> RawRecord persistence
```

`run_ted_search_job` runs exactly that. **No authorization context is
manufactured by hand**, and the collector takes one positionally with no default.

The job also checks `collector_enabled` before anything is fetched: eligibility
says *may we*, enablement says *is it switched on here*, and a job must not take
that decision on an operator's behalf.

## 12. The real acquisitions

### 12.1 The first, Mission 1.15.7, under `1.0.0`

| | |
|---|---|
| Query | `(notice-type IN (cn-standard can-standard)) AND (publication-date>=20230301) AND (publication-date<=20230301) SORT BY publication-date` |
| Route | `ted-search-api`, `https://api.ted.europa.eu/` |
| Fields | 24 native, from 14 conceptual |
| Window | 2023-03-01 to 2023-03-01, one day |
| Bounds | `max_pages=1`, `max_records=3`, `page_size=3` |
| HTTP requests | **1** |
| Notices returned | 3 |
| RawRecords persisted | **3 new** |
| Payload size | 4 764 – 4 778 bytes each |
| Natural-person fields requested | **none** |
| Natural-person data received | **none** |

Re-run identically: **0 new, 3 unchanged**. Same idempotency key, same record
ids, nothing superseded.

### 12.2 Mission 1.15.10, under `1.1.0`

Two executions, because the first one exposed a defect described in §12.3.

| | 12.2a, as executed | 12.2b, as declared |
|---|---|---|
| CPV division declared | `90` | `90` |
| CPV division **in the query** | *absent* | `(classification-cpv=90*)` |
| Window | 2023-03-01, one day | 2023-03-01, one day |
| Notice types | `can-standard` | `can-standard` |
| HTTP requests | **1** | **1** |
| RawRecords | 3 new, 1 revised | 4 new |
| Natural-person data received | **none** | **none** |

12.2b re-run identically: **0 new, unchanged**.

The window and division were chosen **before execution** for comparability, not
for volume: a Signal in this family needs at least two amounts of the same amount
type, scope, currency and notice class, and 2023-03-01 in division 90 was picked
because that exact day already held the one division-90 EUR award total the
system had, so it was where a cohort could plausibly grow.

Every value in the table above is read back from `raw_records.provenance`. The
**bounds are the exception**: they are declared in the job payload and recorded
nowhere, which is a gap in the record rather than a property of the acquisition. The 1.15.9 attempt on a different division had returned no qualifying
cohort at all, and that was recorded as a valid result rather than widened away.

### 12.3 The defect 12.2a exposed, and why it is written down here

`cpv_division` reached the dataclass, the composed query and the idempotency key,
but `TedSearchJobPayload.from_payload` **never read it**. The declared
acquisition and the executed one therefore disagreed, and the executed one was
**broader**: it asked TED for every notice type in the window, not only division
90.

Nothing downstream was corrupted — the extra notices are ordinary TED notices,
lawfully within the same authorised resource and the same bounds — but a
narrowing that exists only in the caller's intent is not a narrowing. The gate
that now protects this asserts the **composed query string**, which is the only
artefact the source ever sees, rather than the dataclass field, which the source
never sees.

## 13. Retention

TED-specific retention is `NOT_ADDRESSED` — no restriction was found on either
official route. The platform baseline applies: **30 days raw**, taken from the
context, with no parameter in this collector that could widen it.

## 14. What this collector cannot do

- reach `ted-open-data-sparql`, the bulk packages or the historical CSV;
- run without an `AcquisitionAuthorizationContext`;
- run under `commercial-multi-tenant-research-v1`, which refuses at the gate;
- run without bounds;
- paginate to exhaustion;
- request an excluded, unknown or unreviewed field;
- accept a caller-supplied query, URL, host or resource id;
- convert a currency, flatten an amount, choose a language or collapse a lot;
- create a NormalizedRecord, a Signal, a Claim, Evidence, an Opportunity, an
  embedding or a score.
