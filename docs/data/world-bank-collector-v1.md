# World Bank Collector V1

**Status:** Authoritative. Created in Mission 1.5, the first real collector.
**Version:** 1.0 (`world-bank-indicators@1.0.0`)
**Date:** 2026-08-30
**Governs:** how World Bank indicator data is acquired, identified, attributed
and retained — and, by example, how every later collector must be built.
**Related:** [`acquisition-authorization-v1.md`](acquisition-authorization-v1.md),
[`source-registry-v1.md`](source-registry-v1.md),
[`raw-record-gap-analysis-v1.md`](raw-record-gap-analysis-v1.md),
[`data-principles.md`](data-principles.md),
[`data-retention-policy-v1.md`](data-retention-policy-v1.md).

---

## 0. What this collector may do, and how that was decided

Nothing here decides anything about World Bank policy. Mission 1.3 read the Data
Catalog licensing page and reached `APPROVED_WITH_CONDITIONS`; Mission 1.4 built
the capabilities its three conditions require and the source became
collector-eligible. This collector consumes that decision and does not
re-interpret it.

    Mission 1.3   the review, and three conditions
    Mission 1.4   the capabilities, and an AcquisitionAuthorizationContext
    Mission 1.5   a collector that cannot run without one

---

## 1. The four rules

**It cannot run without an authorization.** `collect` takes an
`AcquisitionAuthorizationContext` as its first positional parameter, with no
default and no overload that omits it. `build_authorization` produced it, which
means the canonical gate passed. A collector that could construct its own would
be a collector that could approve itself, and a structural test asserts the
signature rather than trusting it.

**It cannot reach a URL a caller chose.** A `WorldBankRequest` names indicators,
countries and years. There is no field for a path, a host or a query fragment, so
there is nothing through which one could be smuggled. Indicator and country codes
are validated because they become path segments.

**Every resource is authorised before a socket opens.** For each indicator the
collector looks up the **authorized dataset entry** — licence, dataset family and
content origin come from governance, never from the caller — builds a
`ResourceDescriptor` from it, and calls `context.authorize_resource(...)`. A
refusal ends that indicator with **zero** network calls.

**The host comes from the registry.** The allowlist is derived from the access
profile the review approved. There is no hard-coded fallback domain, redirects
are not followed, and a source with no recorded endpoint authorises no host at
all rather than defaulting to a guess.

---

## 2. Scope

Only the access mechanism the registry authorises: `indicators-api-v2`, the
PUBLIC_API access profile at `https://api.worldbank.org/v2/`.

Not used, and not reachable from any argument: the Microdata Library, DataBank
scraping, arbitrary World Bank pages, browser automation, undocumented
endpoints, bulk downloads.

### The authorized dataset set is deliberately small

Three indicator series, in
[`source-compliance-v1.json`](source-compliance-v1.json). A resource with no
entry has no recorded licence, family or content origin, so the resource gate has
nothing to clear it against and denies it.

The licence on each entry rests on the Data Catalog statement that CC-BY 4.0 is
the **default** licence for datasets the World Bank itself produces — not on a
per-series licence page, because none was retrieved. Mission 1.3 recorded exactly
this as an open question: *"Confirm per dataset, at collection time, which
licence applies."* Until a reviewer closes it, widening the list means re-opening
the review rather than appending a line.

---

## 3. The request model

```text
WorldBankRequest(indicators, countries, start_year, end_year, per_page)
```

Intent, not a URL. The collector composes
`country/{countries}/indicator/{indicator}` with `format`, `per_page`, `page` and
an optional `date` range, and the transport joins that to the authorized base.

---

## 4. HTTP transport

One file — `collection/transport.py` — is allowed to import an HTTP client, and
CI enforces that. Mission 1.0's blanket ban on network clients in this package
was **narrowed rather than deleted**, the same move Mission 1.2 made with the
D-03 guard: naming where the network is says more than asserting it is absent.

| Property | Value |
|---|---|
| Connect timeout | 5s |
| Read timeout | 20s |
| Total timeout | 30s |
| Redirects | **not followed** — a redirect is the documented way out of a host allowlist |
| Response ceiling | 8 MiB |
| User agent | identifies this client, so it can be contacted if it misbehaves |
| Body logging | never, by default |

`httpx` is imported **inside** the function that needs it, so the registry model,
the compliance layer and every zero-dependency validator still run with nothing
installed (ADR-009).

---

## 5. Pacing — ours, not theirs

Mission 1.3 found no documented World Bank rate limit, and Mission 1.4 records
`rate_limit.known == False` on the authorization context. That does not change.

What exists is **our own** pacing: one request every 250ms, at most 50 in a
single job. It is a local safety measure chosen because we do not know what the
source tolerates, and its `basis` field says so in words. A source that has not
said what it tolerates is a reason to go slower, not faster — and an internal
limit must never be written down as if the source had published it.

---

## 6. Retries and bounds

Retried: `NETWORK_TIMEOUT`, `RATE_LIMITED`, `TEMPORARY_UPSTREAM`,
`PERSISTENCE_FAILURE`. Up to three attempts.

Never retried: `UPSTREAM_CLIENT_ERROR`, `INVALID_RESPONSE`, `PARSING_FAILURE`,
`RESOURCE_NOT_PERMITTED`, `AUTHORIZATION_REJECTED`, `CANCELLED`. The same request
produces the same rejection, and repeating it is how a rate limit becomes a ban.

Every bound is finite and has a default: 10 pages, 5 000 records, an optional
deadline. Pagination is a bounded `range`, not a `while True`. A source that
keeps answering "page 1" while page 2 was requested is reported as a fault rather
than looped over until a limit hides it.

---

## 7. What a RawRecord is

**One logical source observation** — one indicator, one geography, one period —
not one HTTP response. A page carries fifty observations that revise
independently; storing the page would mean one changed value invalidates
forty-nine unchanged ones.

Three identities, kept apart:

| | |
|---|---|
| `observation_key` | WHICH observation: `source\|resource\|geography\|period`. Never the value, never the retrieval time |
| `content_hash` | WHAT the source said: sha256 over the canonical payload, which includes the identifying facts **and** the value |
| record id | which row: uuid5 of workspace, key and hash |

From that, idempotency and revision follow without further machinery:

```text
same key, same hash   →  UNCHANGED.  No new row; last_seen_at moves
same key, new hash    →  REVISED.    New row; the previous one is superseded
new key               →  NEW
```

The retrieval timestamp is deliberately **outside** the fingerprint. Hashing it
would make every retrieval a revision, which is how an idempotent collector
becomes one that grows a table forever.

---

## 8. Provenance

Every record answers the §19 questions without anyone reading a URL string.
Promoted to columns because auditors filter by them: `review_version`,
`correlation_id`, `collector_id`, `collector_version`, `observation_key`,
`observed_at`. In the `provenance` JSONB: access profile and method, approval
state, resource and dataset family, indicator, geography, period, licence and its
basis, content origin, the rendered attribution, the request path and page, and
**the condition snapshot** — which of the source's review conditions were
satisfied at the moment of collection.

`observed_at` is event time, at the resolution the source gave. A World Bank
period is a year, so it is the start of that year, and the period string survives
verbatim in the payload. `data-principles.md` §9: trend analysis computed on
ingestion timestamps produces artifacts that look exactly like real market
movements.

---

## 9. Attribution and retention

Both come from the authorization context, and `build_draft` has **no parameter**
for either — a collector has nothing to pass even if it wanted to.

Attribution is rendered by the Mission 1.4 capability from the obligation the
review recorded: World Bank credit, the dataset's licence, and a modification
statement where the data is modified. Rendering **fails closed**: a resource
whose licence the obligation requires and which the dataset entry does not carry
raises rather than producing a record with no credit attached.

`expires_at` is the resolved raw-retention window — 30 days, the project
baseline. Resolution already took the stricter of baseline and override, in that
direction only, so a collector cannot lengthen it.

---

## 10. Errors

Ten normalised codes (`AcquisitionErrorCode`), so the orchestrator branches on a
meaning rather than on a third party's exception class. A failure carries a
message this codebase wrote and safe diagnostic context — a status code, a page
number, a resource id. **Never** a response body, a header, a stack trace or a
library's own exception text: a driver has no obligation to keep secrets out of
its messages, and a connection string with a password in it has reached a log
that way in more than one project.

---

## 11. Eligible, implemented, enabled

Three facts, and this collector needs all three.

| Fact | Where | Now |
|---|---|---|
| collector-eligible | `registry.source_eligibility`, derived | yes |
| collector implemented | `sros_acquisition.IMPLEMENTED_COLLECTORS` | yes, and only World Bank |
| collector enabled | `registry.sources.collector_enabled` | yes, set deliberately via `sros-source enable` |

Every **persisting** path checks the operational switch — the Celery job and the
CLI's `collect`. The non-persisting `smoke` command does not, because a
connectivity check is not a collection.

---

## 12. Operating it

```bash
sros-acquisition world-bank validate --indicator SP.POP.TOTL
```

Reaches no network. Answers whether a collection would be permitted and which
indicators are authorized resources.

```bash
SROS_ENABLE_WORLD_BANK_SMOKE_TESTS=1 sros-acquisition world-bank smoke \
  --indicator SP.POP.TOTL --country FR --workspace <id>
```

One tiny live request, non-persisting. The flag is required and CI never sets it.

```bash
SROS_ENABLE_WORLD_BANK_SMOKE_TESTS=1 sros-acquisition world-bank collect \
  --indicator SP.POP.TOTL --country FR --start-year 2018 --end-year 2020 \
  --workspace <id> --session <id> --max-records 10
```

Bounded and persisted. Requires the switch to be on.

No command accepts a URL, a host or a query fragment.

---

## 13. What this collector does not do

Normalization (§36 — Mission 1.6 owns it; parsing a response into raw records is
not the same thing), claim extraction, evidence creation, embeddings, clustering
and scoring. It parses a documented response into observations and stops.

---

## 14. Still open

- **The dataset allowlist is three series.** Widening it requires closing Mission
  1.3's per-dataset licence question, not editing a list.
- **A distributed rate limiter.** Pacing is per process. Several workers
  collecting from one source concurrently would each pace themselves, which is
  a real thing to want and is not yet a measured problem.
- **Object storage (D-10).** Payloads are stored inline because they are a few
  hundred bytes. A source with large payloads needs the decision made.
- **Cancellation mid-request.** No new request starts after a cancellation or a
  deadline; a request already in flight runs to its timeout. Nothing here claims
  otherwise.
