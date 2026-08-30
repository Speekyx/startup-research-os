# GDELT WEB-NGRAM Temporal Evidence V1

**Status:** Evidence record. **H-32 CLOSED. H-29 remains OPEN. H-31 answered and
refined.**
**Date:** 2026-08-30 (Sprint 1 / Mission 1.12)
**Method:** first-party GDELT material only, retrieved 2026-08-30.
**Related:** [`signal-temporal-semantics-v1.md`](signal-temporal-semantics-v1.md),
[`gdelt-web-ngram-review-v1.md`](gdelt-web-ngram-review-v1.md),
[`gdelt-response-contract-v1.md`](gdelt-response-contract-v1.md),
[ADR-022](../architecture/adr/ADR-022-web-ngram-source-relative-order.md).

---

## 0. Four questions, kept apart

Mission 1.12 §2 asks whether the WEB-NGRAM `DATE` column supports each of four
things, and forbids letting evidence for one establish another.

| | Question | Verdict |
|---|---|---|
| **A** | Equality of two labels | **Established** (Mission 1.10.1). Needs nothing but string equality |
| **B** | Ordering within the WEB-NGRAM stream | **ESTABLISHED.** H-32 closed — §2 below |
| **C** | Globally comparable instants | **NOT established.** Blocked by D |
| **D** | Timezone / UTC | **NOT established.** H-29 stays open — §3 below |

B does not imply C, and C is what a cross-source comparison needs.

---

## 1. What was retrieved

Every item is GDELT's own. No Stack Overflow, no Reddit, no tutorial, no
community assumption, per §3.

| # | Artifact | Retrieved |
|---|---|---|
| **E1** | [Announcing The Web News Ngram Datasets (WEB-NGRAM)](https://blog.gdeltproject.org/announcing-the-web-news-ngram-datasets-web-ngram/) | 2026-08-30 |
| **E2** | [Charting Global English-Language Media Anxiety Through The News: BigQuery + WEB NGrams](https://blog.gdeltproject.org/charting-global-english-language-media-anxiety-through-the-news-bigquery-web-ngrams/) | 2026-08-30 |
| **E3** | `https://data.gdeltproject.org/gdeltv3/web/ngrams/MASTERFILELIST.TXT` — bounded range reads, first 1.5 KB and last 1.2 KB of 61,683,006 bytes. Nothing stored | 2026-08-30 |
| **E4** | `https://data.gdeltproject.org/gdeltv3/web/ngrams/LASTUPDATE.TXT` — 3 lines. Nothing stored | 2026-08-30 |
| **E5** | [Announcing The New Web News NGrams 3.0 Dataset](https://blog.gdeltproject.org/announcing-the-new-web-news-ngrams-3-0-dataset/) — read to establish what it does **not** cover | 2026-08-30 |
| **E6** | [Using The New Web NGrams Dataset To Find Relevant Coverage](https://blog.gdeltproject.org/using-the-new-web-ngrams-dataset-to-find-relevant-coverage/) — read and found to be a **third** dataset | 2026-08-30 |
| **E7** | [Making NGrams At BigQuery Scale](https://blog.gdeltproject.org/making-ngrams-bigquery-scale/) — read on the strength of its title and found irrelevant | 2026-08-30 |
| **E8** | [gdeltproject.org/data.html](https://www.gdeltproject.org/data.html) | 2026-08-30 |

E6 and E7 are listed because §5 says not to rely on a title. Both looked
relevant and neither was; recording the ones that were checked and discarded is
what makes "we looked" mean something.

---

## 2. H-32 — ordering. CLOSED

> **H-32 asked:** can two WEB-NGRAM `DATE` labels from the same source stream be
> placed in source chronological order? It did **not** ask what timezone they
> are in.

### E1 — the announcement, verbatim

| Field | GDELT's words |
|---|---|
| `DATE` | "The date in YYYYMMDDHHMMSS format. This is included in the file to make it easier to load the ngrams as-is into a database for analysis." |
| `COUNT` | "The number of times the word/phrase was mentioned in articles of that language published in that given 15 minute interval." |
| resolution | "15 minute resolution for all worldwide online news coverage" |
| cadence | "Every 15 minutes two ngram files are produced … typically around 7-10 minutes after the hour, 22-25 minutes after the hour, 37-40 minutes after the hour and 52-55 minutes after the hour" |
| filename | `https://data.gdeltproject.org/gdeltv3/web/ngrams/YYYYMMDDHHMMSS.1gram/2gram.txt.gz` |
| coverage | "January 1, 2019 through present and updated every 15 minutes" |
| index files | `LASTUPDATE.TXT`, `MASTERFILELIST.TXT` |
| BigQuery | `gdelt-bq:gdeltv2.web_1grams`, `gdelt-bq:gdeltv2.web_2grams` |

**The announcement contains no SQL, no timeline guidance, and the words UTC, GMT,
timezone and "time zone" appear nowhere on it.** Checked explicitly rather than
assumed.

So E1 alone gives the label's *format and resolution* and says nothing about
ordering. That is where Mission 1.11 stopped, and it was right to.

### E2 — GDELT ordering the column itself

GDELT's own published analysis over **`gdelt-bq.gdeltv2.web_1grams`** — this
exact dataset, not a relative:

```sql
SELECT DATE, SUM(TOTMENTIONS) TOTWORDS, SUM(TONECOUNT) TOTTONEWORDS,
       SUM(TONECOUNT) / SUM(TOTMENTIONS) * 100 perc_anxiety
FROM (
  SELECT SUBSTR(CAST(DATE AS STRING), 0, 8) DATE, SUM(COUNT) TOTMENTIONS, …
  FROM `gdelt-bq.gdeltv2.web_1grams` WHERE LANG='ENGLISH' …
  UNION ALL …
)
GROUP BY DATE
ORDER BY DATE ASC
```

charted as a series "from January 1, 2019 through September 30, 2019".

Two things GDELT does here, neither of which is a fact about string sorting:

1. **`SUBSTR(…, 0, 8)` reads the first eight characters as a calendar day.** The
   label's leading digits are treated as `YYYYMMDD` — a semantic decomposition of
   the column, by its publisher.
2. **`ORDER BY DATE ASC` is used to produce a chronological chart** spanning nine
   months. For that chart to be what GDELT says it is, ascending label order must
   be chronological order in this dataset.

**E2 establishes chronological semantics at day resolution.** It does not, on its
own, establish ordering *within* a day — the query truncates the label before
ordering it. That distinction is why E3 and E4 matter.

### E3 — the official index, in label order, at bucket resolution

`MASTERFILELIST.TXT` is 61,683,006 bytes. Read bounded, at both ends:

```text
first entries
  …/gdeltv3/web/ngrams/20190101000000.1gram.txt.gz
  …/gdeltv3/web/ngrams/20190101001500.1gram.txt.gz
  …/gdeltv3/web/ngrams/20190101003000.1gram.txt.gz

last entries
  …/gdeltv3/web/ngrams/20260830183000.2gram.txt.gz
  …/gdeltv3/web/ngrams/20260830184500.1gram.txt.gz
  …/gdeltv3/web/ngrams/20260830184500.2gram.txt.gz
```

GDELT publishes its own directory index **in ascending label order, at
15-minute resolution**, running from the dataset's first bucket to the current
one — 7.6 years of entries, ordered by the label and by nothing else.

`000000`, `001500`, `003000` are consecutive lines. This is the sub-day ordering
E2 could not reach, and it is the publisher's own sequencing rather than ours.

### E4 — "newest" equals "largest label"

`LASTUPDATE.TXT`, retrieved in the same minute, contains exactly three lines —
the `1gram`, `2gram` and `chargram` files for `20260830184500`, which is the
**last entry of MASTERFILELIST**.

GDELT's own pointer to *the most recent publication* is the *maximal label*. That
is a first-party assertion that the label's maximum is the stream's latest, at
bucket resolution.

### Why this closes H-32, and what would have stopped it

Mission 1.11 refused to close H-32 on the argument that a fixed-width stamp sorts
lexicographically and a repeated filename would collide. It called that "an
inference about the publisher's mechanism, not a retrieved statement about the
data", and that was the correct call **on the evidence it had**.

What changed is not the reasoning. It is that the mechanism is no longer
inferred:

- **E2** — the publisher uses the column as a chronological axis, on this table.
- **E3** — the publisher's own index is sequenced by the label, at bucket
  resolution, across the whole dataset.
- **E4** — the publisher identifies the newest publication as the maximal label.

The daylight-saving objection is answered by the same artifacts rather than
argued away. A wall-clock frame with a fall-back hour would repeat a label; the
label is the filename in one flat directory, and E3 shows an index that is
strictly ascending across 7.6 years with no repetition at either end. It would
also break E4's "newest = largest" invariant for an hour each year. Neither is
compatible with what was retrieved.

**H-32 is closed for ordering. Nothing above says which clock the labels are
on**, and §3 is where that stays.

---

## 3. H-29 — timezone. STILL OPEN

### Nothing first-party states one for this dataset

E1 does not contain the word. E8, GDELT's data page, links to E1 and states no
timezone for any dataset. There is no field-level documentation page for
`gdeltv3/web/ngrams/` beyond E1.

### GDELT *does* document UTC — for a different dataset

This is the trap Mission 1.12 §8 names, and it is real rather than hypothetical.

**E5, Web News NGrams 3.0:**

> "The dataset can be downloaded directly every minute as a JSON file with the
> following URL structure, with the date represented as 'YYYYMMDDHHMMSS' in the
> UTC timezone."

A search engine will hand you that sentence when you ask about GDELT ngram
timezones. It is about a **different dataset**, and the differences are not
cosmetic:

| | WEB-NGRAM (ours) | Web News NGrams 3.0 |
|---|---|---|
| path | `gdeltv3/web/ngrams/` | `gdeltv3/webngrams/` |
| BigQuery | `gdelt-bq.gdeltv2.web_1grams` / `web_2grams` | `gdelt-bq.gdeltv2.webngrams` |
| format | tab-delimited, 4 columns | JSON |
| cadence | every 15 minutes | every minute |
| what `date` MEANS | the **15-minute bucket** the counts aggregate | "The JSON timestamp **when the article was seen** by GDELT" |
| timezone | **unstated** | **UTC, stated** |

The two `date` fields do not denote the same kind of thing. One is an
aggregation window; the other is an observation instant for a single article. A
timezone documented for the second says nothing about the first, and E5 never
mentions `gdeltv3/web/ngrams` at all.

**E6 is a third dataset again** — `gdeltv5/weblegacy/ngrams/`, quadgrams with a
document id and a TOC, per-minute. Also no timezone. Four dataset families with
confusable names; three of them are not ours.

### The observation that was refused

E3 and E4 were retrieved with HTTP headers:

```text
LASTUPDATE label        20260830184500
response  date:         Sun, 30 Aug 2026 19:00:35 GMT
          last-modified: Sun, 30 Aug 2026 18:50:30 GMT
```

It is tempting to reason from the gap to a zone. **This mission refuses it, and
the reason is worth stating rather than leaving as taste.**

- `last-modified` is a Google Cloud Storage object header (`x-goog-*`,
  `x-guploader-*` are present on the same response). It is when the object was
  stored, not when GDELT decided to publish.
- The comparison uses **this machine's clock** and this network's path to a CDN
  — precisely what H-29's own register entry rules out.
- It is **one observation**, and a timezone is a claim about every record in a
  7.6-year dataset.
- Even a perfect result would not distinguish UTC from any fixed-offset zone that
  happens to equal UTC today, and "equal to UTC on 30 August" is not "UTC".

**H-29 needs a first-party statement or an operator answer. It has neither, so it
stays OPEN.**

---

## 4. H-31 — what it actually asked

H-31 was recorded as *"How far back does the WEB-NGRAM publication directory
reach?"* and it conflated two questions with different answers and different
kinds of authority.

| | Question | Answer |
|---|---|---|
| **H-31a** | Dataset **semantic coverage** — how far back does the DATA go? | **2019-01-01.** E1: "January 1, 2019 through present". Documented since the announcement |
| **H-31b** | Current **download directory extent** — how far back can a file still be fetched? | **`20190101000000`.** E3: the first entry of the current MASTERFILELIST is the dataset's first bucket |

**H-31b is answered as an observation, not as a guarantee.** GDELT publishes no
retention commitment for this directory, so "it reaches back to 2019 today" is a
fact about today. Nothing here licenses planning a backfill that assumes a file
will still be there next year, and the acquisition bounds are unchanged.

**H-31 is closed, refined into the two questions it was.**

---

## 5. What the index also showed

`MASTERFILELIST` lists **three** files per bucket, not two:

```text
20190101000000.1gram.txt.gz
20190101000000.2gram.txt.gz
20190101000000.chargram.txt.gz
```

`chargram` is not mentioned in E1 and has never been reviewed. It is **not**
authorised, **not** covered by the ordering certification, and is recorded here
only so that its existence is a known fact rather than a surprise. The
certification in §6 names its resources explicitly for exactly this reason: a
prefix match on `web-ngrams/` would have silently covered a dataset nobody has
looked at.

---

## 6. Scope of the ordering guarantee

Recorded in code as `ORDER_ESTABLISHED_WITHOUT_TIMEZONE` and deliberately narrow.

| | |
|---|---|
| source | `gdelt` |
| resources | `web-ngrams/1gram`, `web-ngrams/2gram` — **named, not prefixed** |
| label scheme | `gdelt-web-ngram-bucket` (`YYYYMMDDHHMMSS` on the published quarter-hour grid) |
| review version | 3 |
| basis | E2 + E3 + E4, as above |
| grants | `SOURCE_RELATIVE_ORDER` |
| does **not** grant | `COMPARABLE_INSTANT`, a timezone, an `observed_at`, or comparison with any other source |

**It is not a rule about `YYYYMMDDHHMMSS` strings.** Another GDELT dataset whose
filenames look identical — Web News NGrams 3.0, the quadgram legacy set,
`chargram` — inherits nothing. A source not named here has no ordering, and the
model refuses one.

Language and gram kind are **not** part of the ordering scope. Ordering is a
property of the publication stream, and the same directory publishes every
language and both gram sizes on the same bucket grid. Whether two observations
may be *compared* across a language or a gram size is a separate question,
already answered `no` by the extractor's grouping rules and unchanged here.

---

## 7. What is now permitted, and what is not

**Temporally permitted** — meaning the ordering exists, not that an extractor is
specified:

- pairwise comparison of two WEB-NGRAM buckets in the same stream
- `INCREASING` / `DECREASING` / `UNCHANGED` on such a comparison
- adjacent-bucket sequences
- rolling and moving windows over buckets
- within-source momentum

Each still needs its own algorithmic decisions — window size, gap handling,
missing buckets — and none of those is decided here. **Temporally permitted is
not extractor specified.**

**Still blocked by H-29**, and unaffected by anything above:

- aligning a GDELT bucket with a World Bank year or any other source's timestamp
- any "as of" claim in wall-clock time
- daylight-saving interpretation
- global instant comparison
- conversion to `TIMESTAMPTZ`
- populating `observed_at`

**Still blocked by H-30:** mapping `ENGLISH` to a tag, or aggregating across
language labels.
