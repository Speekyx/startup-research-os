# GDELT WEB-NGRAM Review V1

**Status:** The reasoning behind **GDELT review version 3**, committed in
[`source-catalog-v1.json`](source-catalog-v1.json).
**Date:** 2026-08-30 (Mission 1.9.2)
**Verdict:** `APPROVED_WITH_CONDITIONS` — **unchanged**. Reviews 1 and 2 are
untouched and remain in the history.
**Related:**
[`gdelt-web-ngram-minimisation-gap-analysis-v1.md`](gdelt-web-ngram-minimisation-gap-analysis-v1.md),
[`gdelt-web-ngram-resource-v1.md`](gdelt-web-ngram-resource-v1.md),
[`gdelt-compliance-v1.md`](gdelt-compliance-v1.md),
[`gdelt-response-contract-v1.md`](gdelt-response-contract-v1.md) §9,
[`source-review-guide.md`](source-review-guide.md).

---

## 0. Why a new version and not a configuration edit

The rights basis did not change. The verdict did not change. The obligation did
not change. Two things did, and both are review facts:

| Fact | Reviews 1–2 | Review 3 |
|---|---|---|
| capability | news events, themes, entity mentions, tone, timestamps, geography | **plus term frequency** |
| access route | `PUBLIC_API` on `api.gdeltproject.org` | **plus `DATASET_DOWNLOAD` on `data.gdeltproject.org/gdeltv3/web/ngrams/`** |

`source-registry-v1.md` §8 is explicit that a source's registered access profiles
are what the review approved, and Mission 1.7's review recorded neither of these.
Adding an endpoint and a dataset entry without a review version would have made
the configuration say something the review does not — which is the shape of every
failure Mission 1.8 audited.

**A rights grant is not an access authorisation.** The two have been kept apart
since Mission 1.0, and this is the first case where one carried over unchanged
while the other genuinely had to be established.

## 1. Following the review guide

`source-review-guide.md` in order, with what each step produced.

### Step 1 — the use case is unchanged

Automated collection by a commercial multi-tenant SaaS, for storage, derived
analytics and LLM processing. Same as every other review in the catalog, which
is what makes the materiality check in `validate_source_registry` meaningful.

### Step 2 — how the source can be reached

Two routes, and this step is where most of the work happened.

| Route | Method | Host | Status after review 3 |
|---|---|---|---|
| `gdelt-doc-api` | `PUBLIC_API` | `api.gdeltproject.org` | reviewed, approved, **deferred** — see §7 |
| `gdelt-web-ngram-files` | `DATASET_DOWNLOAD` | `data.gdeltproject.org` | reviewed, approved, **the recommended first route** |

The second profile **replaces** the `gdelt-bulk-files` placeholder Mission 1.7
registered. That placeholder named the bulk route in general and deliberately
carried no `endpoint_url`, so it authorised no host at all. Review 3 assessed one
dataset family on one path, and a profile still labelled "bulk files" while
pointing at the ngram directory would have misdescribed its own scope to the next
reader.

### Step 3 — the source's own documents

Four, all first-party, all recorded as evidence on review 3 with absolute URLs.
See §2.

### Step 4 — each activity separately

**Every assessment is unchanged from review 2**, and re-verified against the same
Terms of Use. The terms make one statement about everything GDELT releases, so
nothing about a different dataset moves a per-activity answer:

- `automated_access`, `api_use`, `commercial_use`, `storage`,
  `derived_analytics`, `model_processing` — `PERMITTED`
- `redistribution`, `attribution_required` — `PERMITTED_WITH_CONDITIONS`
- `browser_automation`, `retention`, `personal_data_handling` — `NOT_ADDRESSED`

The six the assessed use materially requires are all positively granted, which is
the check Mission 1.8 made mechanical.

### Step 5 — personal data

`PSEUDONYMOUS`, unchanged. See §6 — this is the step where the ngram dataset asks
a question the DOC API did not.

### Step 6 — retention

`NOT_ADDRESSED`, unchanged. The terms say nothing about retention, so the project
baseline applies: 30 days raw, 365 normalized, with no source override. §17 of
the mission is explicit that a source retention limit must not be invented, and
none was.

### Step 7 — the state

`APPROVED_WITH_CONDITIONS`, unchanged, for the same single reason: attribution is
a stated obligation, and every condition has to be a checkable row.

### Step 9 — the condition

One, carried forward verbatim from review 2 including its verification:

```text
gdelt-attribution   CAPABILITY   source-attribution-display
```

Mission 1.8 moved this from `HUMAN_CONFIRMATION` — which no verifier can ever
clear — to the generic capability the economic sources already use. Review 3
reuses it rather than restating it, which is what §18 asks: the obligation is
identical for both routes because the terms make no distinction between them.

## 2. First-party evidence

Four documents. Every one is the operator's own, retrieved 2026-08-30, and
recorded with an absolute URL — an evidence record whose document cannot be
re-opened cannot be re-checked.

### 2.1 Terms of Use — the grant

`https://www.gdeltproject.org/about.html`

> all datasets released by the GDELT Project are available for unlimited and
> unrestricted use for any academic, commercial, or governmental use of any kind
> without fee

> any use or redistribution of the data must include a citation to the GDELT
> Project and a link to this website (https://www.gdeltproject.org/)

**Re-cited, not re-argued.** The grant is over what GDELT *releases*; the
WEB-NGRAM files are released by GDELT; so the grant reaches them, and the rights
basis is the same `DIRECT_GRANT` reviews 1 and 2 recorded. **H-28 needed nothing
new** and stays closed.

### 2.2 The dataset announcement — the contract

`https://blog.gdeltproject.org/announcing-the-web-news-ngram-datasets-web-ngram/`
· published 2019-09-30 · linked from the GDELT data page as this dataset's
documentation

| Fact | Verbatim |
|---|---|
| path | `http://data.gdeltproject.org/gdeltv3/web/ngrams/YYYYMMDDHHMMSS.1gram/2gram.txt.gz` |
| cadence | "Every 15 minutes two ngram files are produced (one for unigrams and one for bigrams), typically around 7-10 minutes after the hour, 22-25 minutes after the hour, 37-40 minutes after the hour and 52-55 minutes after the hour" |
| shape | "Each row represents a unique language/word/phrase and is tab delimited with the following columns (there is no header row)" |
| `DATE` | "The date in YYYYMMDDHHMMSS format. This is included in the file to make it easier to load the ngrams as-is into a database for analysis." |
| `LANG` | "The human-readable language name as output by CLD2. Most language names are in all uppercase, though a few like Korean appear in titlecase and some may have underscores." |
| `NGRAM` | "The word or phrase." |
| `COUNT` | "The number of times the word/phrase was mentioned in articles of that language published in that given 15 minute interval." |
| coverage | "42 billion words of news coverage in 142 languages spanning January 1, 2019 to present" |

This **confirms the contract Mission 1.9.1 observed** field for field, from the
other direction. One was read off a file; this was read off the operator's
documentation; they agree.

**Two things the document does not say**, both recorded as open questions rather
than filled in:

- **no timezone.** `DATE` is `YYYYMMDDHHMMSS` and nothing states UTC. See §5.
- **no retention of the files themselves.** Coverage runs from 2019 to present;
  how far back the publication directory reaches is not stated, so no historical
  backfill window is assumed.

### 2.3 The data index — the dataset is current

`https://www.gdeltproject.org/data.html`

Lists WEB-NGRAM as a current product — "Global online news ngrams in 152
languages" — and links to the announcement as its documentation.

**152 here against 142 in the 2019 announcement.** The dataset grew. Both figures
are recorded with their dates rather than one being chosen, because picking the
larger would assert currency this review did not verify and picking the smaller
would assert a limit that no longer holds. It changes nothing about scope: the
grant restricts no language and the acquisition bound is not counted in
languages (§4).

The page also states **no timezone anywhere**, which is the second half of why §5
leaves that question open.

### 2.4 The legacy-search post — why the DOC API is deferred, and one correction

`https://blog.gdeltproject.org/using-the-new-web-ngrams-dataset-to-find-relevant-coverage/`
· published 2026-06-30

> While the transition of our search and API infrastructure to Spanner is still
> underway, our existing legacy search infrastructure is struggling to handle the
> ever-growing volume of searches

> Researchers should try to switch their searches to use these ngram files
> instead of the search APIs for the time being until we have completed our
> migration to Spanner

**The correction.** Mission 1.9.1 read the second sentence as first-party support
for the WEB-NGRAM path. Read in place, it is not: the post announces the
**quadgram** dataset — per-minute files at
`storage.googleapis.com/data.gdeltproject.org/gdeltv5/weblegacy/ngrams/`, whose
`ngrams` file keys quadgram counts to a per-document `DOCID` and whose companion
`toc.json.gz` carries `title`, `img` and `url`. "These ngram files" means those.

**This review rejects that dataset** (§3) and does not claim GDELT recommended
the one it approves.

What survives the correction is the **first sentence**, and it is the load-bearing
half: GDELT describes its own legacy search infrastructure as struggling during a
migration. That is why the DOC API is deferred rather than retried, and it is a
statement about infrastructure rather than a recommendation about datasets.

**The case for WEB-NGRAM stands on its own documentation and its observed
structure.** Nothing in it needed the recommendation to be about it.

## 3. The three ngram datasets, and why only one survives

GDELT publishes several ngram products and they differ in exactly the way that
decides this review.

| Dataset | Path | Fields | Verdict |
|---|---|---|---|
| **WEB-NGRAM `1gram`/`2gram`** | `data.gdeltproject.org/gdeltv3/web/ngrams/` | `DATE, LANG, NGRAM, COUNT` | **approved** |
| Web News NGrams **3.0** | `data.gdeltproject.org/gdeltv3/webngrams/` | `date, ngram, lang, type, pos, pre, post, url` | **rejected** |
| quadgram + TOC | `storage.googleapis.com/.../gdeltv5/weblegacy/ngrams/` | `DOCID, QUADGRAM, COUNT` + `ID, date, img, lang, title, url` | **rejected** |

**Both rejections are for publisher content**, the same rule that disqualified the
DOC API's `ArtList` mode in Mission 1.9:

- **NGrams 3.0** carries `pre` and `post` — contextual snippets of about seven
  words — *plus the article `url`*. The URL is what makes the snippet an excerpt
  of an identified document rather than a statistic.
- **the quadgram pair** carries `title` and `img` in its table of contents, and
  its counts are keyed to a `DOCID` that joins back to it. It is per-document by
  construction.

Being newer, or more prominently announced, or the one GDELT recommended, does
not change what is in the file. Neither was analysed further and both are named
in `excluded_dataset_families` so that the record shows they were **read and
rejected** rather than merely left out.

**The quadgram files are also on a different host.** `storage.googleapis.com` is
not authorised by any GDELT access profile and no review has assessed it, so that
dataset is out on two independent grounds.

## 4. `1gram` and `2gram` — both, and why that is a finding rather than a default

§20 of the mission asks whether both can use the same compliance model, and
warns against over-generalising to ngram sizes nobody reviewed.

**Both are approved, as separate resources.** The governance model is identical:
same grant, same content origin, same four columns, same cadence, same absence of
any link to an article.

The only difference is that a `2gram` row is a longer fragment of published text
than a `1gram` row, and the honest question is whether two adjacent words are
publisher content. This review's answer is **no**, and it rests on a structural
fact rather than on a word count:

**Neither file carries a position or a document identifier.** NGrams 3.0 has
`pos` and `url`; the quadgram file has `DOCID`. WEB-NGRAM has neither. A phrase in
this file cannot be attached to the article it came from, cannot be located within
it, and is not ordered relative to any other phrase — it is a frequency in an
unordered table aggregated over an entire language's coverage in a fifteen-minute
window. That is further from an excerpt than a seven-word snippet with a URL, not
closer to one.

**They are two entries rather than one family** so that withdrawing `2gram` later
is a deletion rather than a re-derivation.

**No generalisation to `3gram` or beyond.** GDELT publishes no such WEB-NGRAM
file that this review found, the family allowlist refuses one, and the reasoning
above does not automatically extend — at some length a phrase becomes an excerpt,
and where that line sits is a question for whoever proposes to cross it.

## 5. `DATE`, `LANG`, `NGRAM`, `COUNT` — the semantics a collector must preserve

The category each field is authorised under is settled in the minimisation gap
analysis. What follows is what a future collector must *keep* about each.

### 5.1 `DATE` — a bucket, not a moment

- the value is the **15-minute bucket label**, `YYYYMMDDHHMMSS`, identical to the
  filename;
- the bucket's **resolution is 15 minutes** and the label marks its start;
- it is **not** the publication time of any article, and not the time we fetched
  anything;
- **the timezone is not documented.** Neither the announcement nor the data page
  states one. Mission 1.9.1 recorded it as UTC and this review does not confirm
  that — it is an open question on review 3.

**The source label must be preserved verbatim**, which is what makes the open
question cheap: resolving it later is a re-derivation, not a re-collection. The
same reasoning `CanonicalGeography.unclassified` already applies to a code nobody
can map.

### 5.2 `LANG` — a language, and never a place

- the value is a **CLD2 human-readable language name**: `ALBANIAN`, mostly
  uppercase, a few in titlecase, some with underscores;
- it is authorised under `content_language`, which is a real field on both
  `RawRecordDraft` and `NormalizedRecordDraft`;
- **it must never be written into `geography`.** Spanish is not Spain, Arabic is
  not one country, and the row says nothing about where anything happened. The
  registry model already keeps countries and languages apart for exactly this
  reason.

**No language code is guessed.** The project's canonical representation is a
BCP-47 tag, and GDELT publishes no mapping from CLD2 names to tags. §13 of the
mission says preserve the source label honestly when a deterministic mapping is
unavailable, and one is unavailable, so the label is preserved. Whether GDELT
publishes such a mapping anywhere is an open question on the review.

### 5.3 `NGRAM` — a term the source observed

One word or two, exactly as GDELT emitted it. **Nothing classified it**: it is
not a theme, not an entity, not a topic, and a collector must not infer one from
it. Its encoding is UTF-8 and Mission 1.9.1 verified that by strict decode after
a console rendered `të` as `t?` — the mangling was the console's, and recording
it as a source quirk would have been a fabricated fact.

### 5.4 `COUNT` — GDELT's measurement, and nobody else's

The number of times the term appeared in articles of that language in that
bucket, **computed by GDELT over its own index**. It is not:

- the number of files or rows our job fetched;
- the size of a result set — **there is no query on this route at all**;
- a popularity, attention or interest score;
- a signal, an evidence weight, or an input to an Opportunity Score.

The last point is why the category is named `source_measured_frequency`. This is
the first source-published number in the system that *looks* like a trend
measure, and D-03 is still open.

## 6. Personal data — structure against contents

§19 asks the question the right way round.

**Structurally there is none.** Four columns, none of which is a name, an author,
a handle, an identifier or a profile. Nothing in a row is *about* a person.

**A lexical term can be a person's name.** `MACRON` is a valid `1gram`;
`Emmanuel Macron` is a valid `2gram`. A collector cannot prevent it by asking
differently — the file is a published aggregate and arrives whole.

What such a row actually is: a name, one number, no article, no URL, no author,
no document id, aggregated over an entire language's coverage in fifteen minutes.

**The classification does not change.** GDELT stays `PSEUDONYMOUS` with
`contains_user_identifiers` true — that was recorded for entity mentions on the
DOC API route and it remains the honest reading here. Downgrading the source to
`NONE_EXPECTED` because *one* of its datasets has no identifier column would be
reading a dataset's structure as a statement about the source, in the permissive
direction.

**Whether a name occurring as an ngram is personal data in the regulatory sense
is jurisdiction**, which is **H-12** and has been deferred project-wide since
Mission 1.3. This review does not resolve it and does not pretend to; it records
the exposure precisely, so that whoever resolves H-12 can see exactly what it
applies to.

## 7. The DOC API route — deferred, not withdrawn

**H-27 is still open**, and nothing in this mission closes it. No `TimelineTone`
or `TimelineVolRaw` envelope has ever been observed, `api.gdeltproject.org`
returned `ConnectTimeout` from two independent environments, and GDELT documents
its legacy search infrastructure as struggling.

What changed is the **classification, not the verdict**:

| | |
|---|---|
| approval | unchanged — the route is reviewed and approved |
| profile | **kept**, with its endpoint |
| authorised resources on it | **none**, and none was invented |
| status | **deferred**: no longer the candidate for the first collector |

The profile is kept rather than deleted for a specific reason: **deleting it
would make a later un-deferral look like a new approval.** The capture script,
the response-contract document and the H-27 queue entry are all kept for the
same reason — the migration will finish, and when it does the work already done
should still be there.

## 8. What this review does NOT authorise

Stated positively so that a later reader does not have to infer it:

- **no collector.** GDELT is not in `IMPLEMENTED_COLLECTORS` and
  `collector_enabled` is false;
- **no research data.** Zero GDELT `RawRecords`, zero `NormalizedRecords`;
- **no normalization.** No adapter exists for what the file contains;
- **no signal, embedding, claim, evidence or score** derived from anything here;
- **no third ngram dataset**, no other GDELT bulk product, no `storage.googleapis.com`;
- **no DOC API mode**;
- **no unbounded acquisition.** The reviewed ceiling is in
  [`gdelt-web-ngram-resource-v1.md`](gdelt-web-ngram-resource-v1.md) §3.

## 9. Open questions carried on review 3

Five, and each names what would answer it.

1. **Rate limits.** None published for either route. Recorded as unknown rather
   than guessed, on both profiles.
2. **Entity mentions and personal data** on the DOC API route. Carried from
   review 2, unchanged.
3. **The `DATE` timezone.** Not stated on either first-party page read. The
   collector must preserve the source label so that answering this costs no
   re-collection.
4. **A CLD2-name-to-language-tag mapping.** None found. Until one is, the source
   label is preserved and no code is guessed.
5. **How far back the publication directory reaches.** Coverage is documented from
   2019-01-01; directory retention is not. No historical backfill window is
   assumed.

None of the five blocks a collector. They are the things a collector must not
quietly decide for itself.
