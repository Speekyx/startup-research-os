# GDELT DOC API Response Contract V1

**Status:** **Partially established.** The two DOC API timeline contracts remain
unobserved (**H-27**, now reproduced in two independent environments) and that
route is **deferred** as of GDELT review 3. A third contract — the WEB-NGRAM
dataset — **was** observed, is recorded in §9, and was **confirmed against
GDELT's own documentation** in Mission 1.9.2; §10 records the confirmation, two
things the documentation does not say, and one claim in §9 that had to be
corrected.
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
| **WEB-NGRAM `1gram`/`2gram`** | **observed** — §9.5, one capped file inspection |

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

---

## 9. Legacy DOC API availability, and the Web NGrams alternative

Added after the DOC API capture failed in a **second independent environment**.

### 9.1 The failure is not local to one machine

| Environment | TimelineTone | TimelineVolRaw |
|---|---|---|
| CI / agent environment | `ConnectTimeout` | `ConnectTimeout` |
| operator's Windows development machine | `ConnectTimeout` | `ConnectTimeout` |

Two independent networks, same result, against a control (`api.worldbank.org`)
that returns HTTP 200 from the same client. **No workaround was attempted** —
no proxy, no mirror, no identity rotation, no rate-limit evasion (§5).

### 9.2 GDELT's own documentation explains it

First-party, retrieved 2026-08-30:

> the transition of our search and API infrastructure to Spanner is still
> underway, our existing legacy search infrastructure is struggling to handle the
> ever-growing volume

and, in the same post:

> Researchers should try to switch their searches to use these ngram files
> instead of the search APIs for the time being

**The API we were trying to reach is one GDELT is actively asking people to stop
using.** That reframes H-27: it is not a transient outage to wait out, and
continuing to retry the DOC API would be pushing against infrastructure its
operator says is under strain.

### 9.3 The bulk host is reachable — the API host is not

Measured from the same client, seconds apart:

| Host | Result |
|---|---|
| `api.gdeltproject.org` — DOC API | **`ConnectTimeout`** |
| `data.gdeltproject.org` — bulk datasets | **HTTP 301**, reachable |
| `storage.googleapis.com` — GDELT bucket | HTTP 403 on the bare bucket, reachable |
| `api.worldbank.org` — control | HTTP 200 |

These are different network paths. Nothing about the DOC API's unreachability
says anything about the dataset host.

### 9.4 Three ngram datasets, and only one is usable

GDELT publishes several, and they differ in exactly the way that matters here.

| Dataset | Fields | Publisher content? |
|---|---|---|
| **Web News NGrams 3.0** (`gdeltv3/webngrams/`) | `date, ngram, lang, type, pos, pre, post, url` | **YES** — `pre`/`post` are contextual snippets "typically up to 7 words", plus the article `url` |
| **quadgram TOC** (`gdeltv5/weblegacy/ngrams/`) | `ID, date, img, lang, title, url` | **YES** — `title` is the headline, plus `img` and `url` |
| **WEB-NGRAM 1gram/2gram** (`gdeltv3/web/ngrams/`) | `DATE, LANG, NGRAM, COUNT` | **NO** |

The first two carry exactly what disqualified `ArtList`: headline text, image
references, article URLs, and in NGrams 3.0 a running snippet of the article
itself. Both are **out**, for the same reason and without further analysis.

### 9.5 WEB-NGRAM 1gram/2gram — contract observed

One file inspection, streamed with a hard byte cap, decompressed in memory,
**nothing persisted**.

```text
GET https://data.gdeltproject.org/gdeltv3/web/ngrams/20260830091500.1gram.txt.gz
HTTP 200 · content-type text/plain · gzip · strict UTF-8 decode OK
```

Tab-delimited, **four columns, no header row**:

```text
DATE             LANG        NGRAM      COUNT
20260830091500   ALBANIAN    dhe        676
20260830091500   ALBANIAN    e          1142
```

The `2gram` file is identical in shape, with a two-word `NGRAM`:

```text
20260830091500   ALBANIAN    do të      104
```

| Column | Meaning |
|---|---|
| `DATE` | the 15-minute bucket, `YYYYMMDDHHMMSS`. **No timezone** — see §10.1, and `gdelt-web-ngram-temporal-evidence-v1.md` §3 |
| `LANG` | language name, uppercased. **Not geography** |
| `NGRAM` | one word (`1gram`) or a two-word phrase (`2gram`) |
| `COUNT` | times mentioned in articles of that language in that bucket |

Published every 15 minutes, ~7–10 minutes after each quarter. GDELT documents
coverage as "42 billion words of news coverage in 142 languages spanning
January 1, 2019 to present".

### 9.6 Why this is a better fit than any DOC API mode

**No publisher content, structurally.** Not "we filter it out" — the file does
not contain a title, a URL, an image or a sentence. There is nothing to
minimise away, which is a stronger position than any filter.

**The count is real and is not request-bounded.** This is the objection that
killed the `ArtList` count and that `MAXRECORDS` only partially answered for
timelines: here we issue no query at all. We download a published aggregate
GDELT computed over everything it monitored. The number cannot be an artefact of
our request because our request does not influence it.

**The identity is source-native.** `(DATE, LANG, NGRAM)` is a natural key the
source itself defines. That **resolves the §21 weakness outright** — the DOC API
path had `(our query, mode, bucket)` and the query was ours, so two phrasings of
one research question forked the identity. Here there is no query.

**It is reachable**, which the DOC API is not from two environments.

### 9.7 What it still needs — none of it code

Three gaps, and none is a blocker in the H-27 sense.

**A different access path.** This is `data.gdeltproject.org` over
`DATASET_DOWNLOAD`, which is the **`gdelt-bulk-files`** profile — not
`gdelt-doc-api`. Mission 1.9 §54 put bulk files out of scope, and the profile
deliberately records no `endpoint_url` so it authorises no host. **The
`gdelt-doc-api` profile does not authorise this dataset and must not be
stretched to.**

**A minimisation category.** The committed profile allows `event_identifier`,
`theme_identifier`, `entity_mention`, `tone_score`, `observation_period`,
`geography`, `content_origin`. A term and its frequency are none of those, and
`LANG` is not `geography` — the project is explicit that language is not
geography. Authorising this needs a reviewed addition naming a term-frequency
category, which is governance work of the kind Mission 1.8 did.

**A review version.** The Mission 1.7 review recorded GDELT's capabilities as
news events, themes, entity mentions, tone, timestamps and geography. Ngram
frequency is none of them. The *rights* grant carries over unchanged — the terms
cover "all datasets **released by** the GDELT Project" and this is one — but the
**capability and access facts are new**, and §27 calls that substantive review
work.

### 9.8 Volume, which minimisation has to answer

96 buckets a day, two files each, global across 142 languages. The `1gram` slice
read here was over a megabyte gzipped before the cap and the `2gram` over four.

A collector that ingested all of it would be the "bulk-data vacuum" the brief
warns against. The obvious shape is a reviewed restriction — specific languages,
and terms drawn from a research context — decided at review time rather than by
the collector. **That decision belongs in the minimisation profile**, which is
the third gap above and not a separate problem.

---

## 10. The observed contract, checked against the operator's documentation

Mission 1.9.2 §4. §9.5 was read off a file. This section is the same contract
read off GDELT's own announcement, retrieved 2026-08-30 from
`https://blog.gdeltproject.org/announcing-the-web-news-ngram-datasets-web-ngram/`
(published 2019-09-30, linked from the GDELT data page as this dataset's
documentation).

**They agree, field for field.**

| Column | GDELT's own words |
|---|---|
| `DATE` | "The date in YYYYMMDDHHMMSS format. This is included in the file to make it easier to load the ngrams as-is into a database for analysis." |
| `LANG` | "The human-readable language name as output by CLD2. Most language names are in all uppercase, though a few like Korean appear in titlecase and some may have underscores." |
| `NGRAM` | "The word or phrase." |
| `COUNT` | "The number of times the word/phrase was mentioned in articles of that language published in that given 15 minute interval." |

> Each row represents a unique language/word/phrase and is tab delimited with the
> following columns (there is no header row)

Cadence, verbatim: two files every 15 minutes, "typically around 7-10 minutes
after the hour, 22-25 minutes after the hour, 37-40 minutes after the hour and
52-55 minutes after the hour". Coverage at release: "42 billion words of news
coverage in 142 languages spanning January 1, 2019 to present". The current data
index says **152 languages**; both figures are recorded with their dates rather
than one being chosen.

### 10.1 Two things the documentation does NOT say

**No timezone.** `DATE` is `YYYYMMDDHHMMSS` and neither the announcement nor the
data page states UTC anywhere. §9.5 above recorded it as UTC; **that was not
established** and is now an open question on review 3. The collector must
preserve the source label verbatim, which makes answering it later a
re-derivation rather than a re-collection.

> **Mission 1.12 re-checked and confirms this.** The words UTC, GMT, timezone
> and "time zone" appear nowhere on the announcement, and the data page states
> none for any dataset. GDELT **does** document UTC for **Web News NGrams 3.0**
> (`gdeltv3/webngrams/`), whose `date` means "the JSON timestamp when the article
> was seen" rather than a 15-minute aggregation bucket. Different path, table,
> format, cadence and meaning: **H-29 stays open**
> ([`gdelt-web-ngram-temporal-evidence-v1.md`](gdelt-web-ngram-temporal-evidence-v1.md) §3).
>
> The §9.5 table above has been corrected; it still said UTC.

**No directory retention.** Coverage runs from 2019 to present; how far back the
publication directory itself reaches is unstated, so no historical backfill
window may be assumed.

> **Mission 1.12 answered the extent and not the retention.** A bounded read of
> `MASTERFILELIST.TXT` shows the current index beginning at `20190101000000` --
> the directory reaches back to the dataset's first bucket **today**. GDELT
> publishes no retention commitment, so that is an observation and not a
> guarantee, and no backfill window may still be assumed (H-31, refined).
>
> The same index lists a **third** file per bucket, `chargram`, which the
> announcement does not document and no review has assessed. It is not
> authorised and not covered by the ordering certification.

### 10.2 A correction to §9.2

§9.2 quotes GDELT asking researchers to "switch their searches to use these ngram
files instead of the search APIs", and Mission 1.9.1 read that as first-party
support for the WEB-NGRAM path.

**It is not.** The sentence appears in the post announcing the **quadgram**
dataset — per-minute files on `storage.googleapis.com` under
`gdeltv5/weblegacy/ngrams/`, whose `ngrams` file keys quadgram counts to a
per-document `DOCID` and whose companion `toc.json.gz` carries `title`, `img` and
`url`. "These ngram files" means those, and GDELT review 3 **rejects** that
dataset for exactly the content §9.4 already identified.

What stands unchanged is the other half of §9.2 — GDELT describing its own legacy
search infrastructure as struggling during a Spanner migration. That is a
statement about infrastructure, it is why the DOC API route is **deferred**, and
it needed no support from the recommendation.

The case for WEB-NGRAM rests on §9.5, §9.6 and §10 above: its own documentation
and its own observed structure.

### 10.3 One more fact, and it decides the acquisition bound

**Each file spans every language.** `LANG` is a data column, not a partition —
which the observed file's shape already implied and the documentation confirms.

A job therefore cannot request fewer languages than a file contains, so language
is not a dimension of the request at all, and the volume bound is counted in
files. See [`gdelt-web-ngram-resource-v1.md`](gdelt-web-ngram-resource-v1.md) §3.
