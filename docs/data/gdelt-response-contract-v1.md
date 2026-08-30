# GDELT DOC API Response Contract V1

**Status:** **Incomplete.** Two of the three contracts this document exists to
record are not established, and the missing pair is **H-27**.
**Date:** 2026-08-30
**Produced by:** Mission 1.9.1 §3, §4, §8, §9.
**Capture tool:** `infrastructure/scripts/capture_gdelt_fixtures.py`
**Related:** [`gdelt-raw-record-gap-analysis-v1.md`](gdelt-raw-record-gap-analysis-v1.md),
[`gdelt-compliance-v1.md`](gdelt-compliance-v1.md),
[`gdelt-resource-model-v1.md`](gdelt-resource-model-v1.md).

---

## 0. What is and is not established

| Contract | Status |
|---|---|
| `ArtList` envelope | **observed** — one live response, Mission 1.9 |
| Mode semantics, parameters, time-step rules | **documented** by GDELT, Mission 1.9.1 §3 |
| `TimelineTone` envelope | **NOT established** — H-27 |
| `TimelineVolRaw` envelope | **NOT established** — H-27 |

**No envelope in this document was reconstructed from prose.** Where a shape was
not observed it is recorded as not observed, and no fixture was written.

## 1. Endpoint and parameters (documented)

```text
https://api.gdeltproject.org/api/v2/doc/doc
```

Now recorded as `endpoint_url` on the `gdelt-doc-api` access profile — Mission
1.9 found it absent, which left the host allowlist every collector derives from
the registry **empty**.

| Parameter | Values |
|---|---|
| `QUERY` | search expression; supports `domain:`, `theme:`, `tone:` operators |
| `MODE` | `ArtList`, `TimelineVol`, `TimelineVolRaw`, `TimelineTone`, `ToneChart`, image and word-cloud modes |
| `FORMAT` | HTML by default; `json` available |
| `TIMESPAN` | `1d`, `1week`, `3months`, … |
| `STARTDATETIME` / `ENDDATETIME` | `YYYYMMDDHHMMSS` |
| `MAXRECORDS` | default 75, max 250 |
| `SORT` | `DateDesc`, `DateAsc`, `ToneDesc`, `ToneAsc`, `HybridRel` |
| `TIMELINESMOOTH` | moving window, 1–30 steps |

### 1.1 Two documented facts that shape the design

**`MAXRECORDS` does not apply to timeline modes.** GDELT: *"This option only
applies to the ArticleList and various ImageCollage modes, it is ignored in all
other modes."*

That is what separates a timeline count from an `ArtList` count. Mission 1.9
rejected counting `ArtList` results because `MAXRECORDS` caps them, so the count
would measure our request bound rather than GDELT's index — **a timeline count
is not subject to that cap and is GDELT's own measurement.**

**Time-step is derived from the span, not chosen.** GDELT: *"For time spans of
less than 72 hours, the timeline uses a time step of 15 minutes … for time spans
from 72 hours to one week it uses an hourly resolution and for time spans of
greater than a week it uses a daily resolution."*

A future RawRecord must therefore record the bucket's resolution, because the
same query over two spans produces buckets of different width.

## 2. Mode semantics (documented)

| Mode | What GDELT says it returns |
|---|---|
| `TimelineTone` | *"instead of coverage volume it displays the average 'tone' of all matching coverage, from extremely negative to extremely positive"* |
| `TimelineVol` | volume as a **percentage** of all coverage GDELT monitored in each step |
| `TimelineVolRaw` | *"the actual number of articles per time interval that matched the query"*, plus a `norm` field recording the total monitored |
| `ArtList` | a list of matching articles |

## 3. `ArtList` — observed, and out of scope

```json
{"articles": [
  {"url": "…", "url_mobile": "…", "title": "…",
   "seendate": "20260829T171500Z", "socialimage": "…",
   "domain": "ksat.com", "language": "English",
   "sourcecountry": "United States"}
]}
```

**Recorded here so it is not re-derived, and it remains unavailable** (§10 of the
Mission 1.9.1 brief). `title` and `socialimage` are publisher content, excluded
by name from the minimisation profile; `url`, `url_mobile` and `domain` are
publisher references the profile does not list. What survives is `seendate` and
`sourcecountry` — two dimensions and no measurement.

Mission 1.9's finding stands: `ArtList` must not become the first collector
merely because its shape is known.

## 4. `TimelineTone` — NOT established

**This is the mode the first collector should use**, on the evidence available:
tone over time maps onto the committed minimisation profile exactly —
`tone_score` plus `observation_period` — and contains no publisher content
whatever.

Its JSON envelope is unknown. Specifically **not** documented anywhere
first-party: the container key, the series structure, the timestamp
representation, the tone value representation, and whether query metadata is
echoed.

**Nothing is guessed.** A parser written against invented names would be
validated by fixtures composed from the same invention.

## 5. `TimelineVolRaw` — NOT established

Semantics are documented (§2) and the envelope is not: the count field name, the
`norm` field's exact placement, and the bucket representation are all unknown.

Its governance question is separate and is §6 below.

## 6. Why the contracts could not be captured

Two independent walls, either of which is sufficient.

**GDELT does not publish the JSON schema.** Its announcement documents the
parameters and the modes' semantics and states that JSON output exists, without
listing field names.

**No reachable environment.** Across Missions 1.9 and 1.9.1, sixteen attempts
over two routes returned `ConnectTimeout`, `ECONNRESET`, `HTTP 429` and
`ECONNREFUSED`, while `api.worldbank.org` returned HTTP 200 from the same client
moments apart. The one `ArtList` response was obtained through a proxied route
before that route also began refusing.

Per Mission 1.9.1 §5, **no attempt was made to work around it** — no proxy, no
rotated identity, no undocumented mirror. A block is a limit, not an obstacle.

## 7. How to close H-27

```bash
python infrastructure/scripts/capture_gdelt_fixtures.py
```

Run it from **any** development environment that can reach
`api.gdeltproject.org`. It issues exactly two requests, fifteen seconds apart,
to the one approved host, and writes four files:

```text
services/acquisition/python/tests/fixtures/gdelt/
    timelinetone.json          response bytes, verbatim
    timelinetone.meta.json     endpoint, mode, params, capture time, status,
                               content type, byte length, sha256 of the bytes
    timelinevolraw.json
    timelinevolraw.meta.json
```

It writes nothing on failure and says so. `--dry-run` prints the exact requests
without issuing them.

**The hash is over the captured bytes**, not over a re-serialised Python object:
a hash of a reconstruction proves only that the reconstruction is stable.

These are **test fixtures establishing an external contract, never RawRecords**.
Nothing in the capture path opens a database connection.

Once committed, this document's §4 and §5 are filled in from the fixtures, and
[`gdelt-resource-model-v1.md`](gdelt-resource-model-v1.md) §3 becomes a config
entry.

## 8. What must not be done instead

Mission 1.9.1 §36 is unambiguous: **if authentic fixtures cannot be obtained,
stop and report H-27 blocked. Do not satisfy the mission by creating fake
fixtures.**

That includes fixtures reconstructed from this document. Everything above §3 is
GDELT's prose about its own behaviour, which establishes *semantics* and is not
a substitute for a response.
