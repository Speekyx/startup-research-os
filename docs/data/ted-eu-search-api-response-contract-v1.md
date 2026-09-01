# TED-EU Search API Response Contract V1

**Authoritative.** Mission 1.15.7. What the TED Search API accepts, what it
returns, which parts are required, and which observed behaviour was established
by asking it rather than by assuming.

**Every fact here comes from a first-party source**: the API's own OpenAPI
document at `https://api.ted.europa.eu/api-v3.yaml` (published by the same
service, linked from its own Swagger configuration), the Publications Office
documentation at `docs.ted.europa.eu`, and the API's own
`checkQuerySyntax` mode, which validates a query **without executing it**. No
third-party tutorial was used and no field name was guessed.

---

## 1. The endpoint

```text
POST https://api.ted.europa.eu/v3/notices/search
Content-Type: application/json
```

**No authentication.** The documentation states the API *"does not require
authentication, making it openly accessible to any system or user"*. Openness is
not permission and never was — the permission is the review, the route
authorization and the resource entry.

**POST, not GET.** The parameters travel in a JSON body, so `Transport.get`
cannot express this call. Mission 1.15.7 added `JsonRequest` and the
`JsonPostTransport` protocol to `collection/transport.py`, which remains the
only file in the package permitted to reach a network.

## 2. The request body

`PublicExpertSearchRequestV1`, verbatim from the OpenAPI document:

| Field | Type | Default | Used by the collector |
|---|---|---|---|
| `query` | string, `minLength: 1` | — | **yes**, composed, never caller-supplied |
| `fields` | array of enum | — | **yes**, the mapped native selection |
| `page` | integer, `minimum: 1` | `1` | **yes**, bounded by `max_pages` |
| `limit` | integer | `10` | **yes**, `page_size` |
| `scope` | `LATEST` / `ACTIVE` / `ALL` | `ALL` | **yes**, stated as `ALL` |
| `checkQuerySyntax` | boolean | `false` | stated as `false` |
| `paginationMode` | `PAGE_NUMBER` / `ITERATION` | `PAGE_NUMBER` | **stated**, never defaulted |
| `onlyLatestVersions` | boolean | `false` | not sent |
| `iterationNextToken` | string | — | **never sent** |

**`fields` is required and must not be empty**, enforced by the API itself:

```text
{"message":"Validation error","error":[{"objectName":"publicExpertSearchRequestV1",
 "field":"fields","message":"must not be empty"}]}
```

That is worth recording rather than merely obeying. The minimisation profile
already refuses an unstated selection — *"a request naming no field is not a
request"* — and the source refuses it too. Two independent refusals of the same
shape.

**`paginationMode` is stated rather than left to its default.** Naming the mode
we are in is what keeps a change to it visible in a diff.

## 3. The documented limits

Quoted from the API's own documentation. **These are the SOURCE's limits**, not
ours, and they are checked before the request so a breach costs no round trip:

| Mode | Retrievable notices | Notices per page | Fields per page |
|---|---|---|---|
| `PAGE_NUMBER` | **15 000** | **250** | **10 000** |
| `ITERATION` | *no limit* | 250 | 10 000 |

Fields-per-page is `len(fields) x limit`. With the reviewed 24-field selection
the largest page TED allows gives `24 x 250 = 6000`, so **that limit cannot
currently bind** — the check is kept because the field selection is the thing
most likely to grow, and the failure it would otherwise produce arrives from the
source after the request rather than from us before it.

**`ITERATION` is the mode this collector must not have.** It exists to retrieve
*every* notice for a query with no limit, which is the corpus mirroring the
review refuses and the exhaustion iterator §37 forbids. The collector sends
`PAGE_NUMBER` and never sends a token, and a test asserts both over the AST of
the one method that composes the body.

## 4. The expert query language

Established against `checkQuerySyntax`, which the API documents as checking the
syntax while *"the search query is not executed"* — and which returned
`{"notices":[],"totalNoticeCount":null}` for every probe, retrieving nothing.

| Construct | Verified |
|---|---|
| comparison | `publication-date>=20230301` |
| date literal | `YYYYMMDD`, no separators |
| list membership | `notice-type IN (cn-standard can-standard)` — **space-separated, not commas** |
| boolean | `AND`, with parentheses |
| ordering | `SORT BY publication-date`; a trailing `ASC` is a syntax error |

**Value validation happens at check time too**, which is how the notice-type
vocabulary was confirmed rather than assumed:

```text
notice-type=this-is-not-a-real-value
  -> QUERY_UNSUPPORTED_FIELD_VALUE, fieldName "notice-type"
not-a-real-field=1
  -> QUERY_UNKNOWN_FIELD, fieldName "not-a-real-field"
```

`cn-standard` and `can-standard` passed that same validation, so they are values
the source recognises.

The query the collector composes:

```text
(notice-type IN (cn-standard can-standard))
  AND (publication-date>=YYYYMMDD)
  AND (publication-date<=YYYYMMDD)
  SORT BY publication-date
```

**No caller supplies it.** A raw query parameter would be a caller-supplied
scope, and the families, the window and the ordering are the reviewed shape of
the resource.

## 5. The response

`ExpertSearchResponse`:

| Field | Type | Required by the collector |
|---|---|---|
| `notices` | array of `NoticeResponse` | **yes** — its absence is contract drift, not an empty page |
| `totalNoticeCount` | integer | optional; must be an integer if present |
| `iterationNextToken` | string | ignored |
| `timedOut` | boolean | ignored in V1 |

### 5.1 Required versus optional, per notice

**Required: `publication-number`, and nothing else.** A notice without it has no
source-native identity, so no record can be built for it: the record id derives
from the observation key, and an unidentified notice would either collide with
another or have an identity invented for it. The collector fails the whole page.

**Everything else is optional, and this was observed rather than assumed.** The
API **omits a field entirely when the notice has no value for it**. The first
real acquisition requested 24 native fields and received 8 of them plus `links`:
a contract award notice carries `total-value`, one without a published amount
carries no `total-value` key at all.

That is the behaviour the layer above must be built against: **absent is not
zero and not null-with-a-value** — it is the key not being there.

### 5.2 Value shapes

The schema declares some fields scalar and some arrays, and both occur:

| Shape | Example | Meaning |
|---|---|---|
| scalar string | `"publication-number": "125972-2023"` | one value |
| scalar number | `"total-value": 73415.22` | one amount |
| array | `"classification-cpv": ["90911200", "90911300"]` | real multiplicity |
| object keyed by language | `"organisation-name-buyer": {"eng": [...], "fra": [...]}` | multilingual |

A one-element array is unwrapped **only** where an identity field is read. A
longer array is never reduced: it is several lots, several CPV codes or several
languages, and collapsing it would lose them.

### 5.3 `links` arrives unrequested

**The API adds a `links` object to every notice regardless of the `fields`
selection.** It was not requested and cannot be suppressed by any `fields`
value.

It was **inspected before the records were accepted** (Mission 1.15.7 §14), and
it contains exactly one thing: the URLs of the notice itself, in each published
format, per language.

```json
"links": {"pdf": {"BUL": "https://ted.europa.eu/bg/notice/125972-2023/pdf", ...},
          "html": {...}, "htmlDirect": {...}, "pdfs": {...}, "xml": {...}}
```

Scanned across the whole payload: **zero email addresses, zero telephone
numbers, and no key containing `contact`, `person`, `address`, `street`,
`postal`, `tel`, `fax` or `ubo`.** It carries no natural-person information.

**It is preserved verbatim, and that is deliberate.** A RawRecord that dropped
part of what the source returned would not be raw, and there is no method in the
collector that removes a field from a collected notice — the primary control is
the `fields` parameter, which works for everything it governs. It is ~94% of
each record's bytes, which is a size fact rather than a governance one, and it
is named here so a reader is not surprised by it.

### 5.4 Identity fields may be absent

`notice-identifier` and `notice-version` were requested and **were not returned**
for any notice in the first real acquisition. The identity therefore rests on
`publication-number` alone for those records, which is what
`TedNotice.key` does: it appends the identifier and the version **where the
source published them** and omits them otherwise, rather than substituting a
placeholder that would make two different notices look alike.

## 6. Errors

| Status | Documented shape | Collector behaviour |
|---|---|---|
| 400 | `QuerySyntaxErrorError`, `QueryUnknownFieldError`, `QueryUnsupportedFieldValueError`, `QueryUnsupportedFieldOperationError`, `UnsupportedValueException`, iteration-token errors | classified failure, no record |
| 429 | — | `RATE_LIMITED` |
| 5xx | — | `TEMPORARY_UPSTREAM` |
| non-JSON body | — | `INVALID_RESPONSE` |

**The response body never enters the failure detail.** A 400 from the expert
query parser echoes the query back, and a third party's text may contain
anything; the mapped message and the status number are ours
(`collection/errors.py` `code_for_status`).

## 7. Contract drift

A required structural field disappearing produces a **visible failure**, never
nulls:

- `notices` missing entirely → refusal naming it a response-contract change;
- `notices` not a list → the same;
- a notice entry that is not an object → the same;
- `totalNoticeCount` present and not an integer → the same;
- a notice without `publication-number` → the same.

The distinction the wording protects is between *the API changed* and *there
were no results*. `{"notices": []}` is the second and is a success with zero
records.

## 8. Versioning

TED versions its API in the URL (`v3`) and states that **the field list is
excluded from that versioning**: *"addition, removal or update of a fields will
not change the versioning."* So a field vanishing is not a breaking change by
TED's own contract, and the collector must not treat a missing optional field as
an error — which is why exactly one field is required and the rest are not.

## 9. Rate limits

**UNKNOWN.** The registry records it as unknown, the documentation publishes
none, and none is invented. The collector's pacing — one second between
requests, at most twenty requests per job — is an `INTERNAL_SAFETY_POLICY`
labelled as such in every record's provenance. It is conservative client
behaviour towards a source whose tolerance is not published, and it is not a
claim about what TED permits.
