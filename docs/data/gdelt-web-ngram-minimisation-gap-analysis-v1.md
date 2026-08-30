# GDELT WEB-NGRAM Minimisation Gap Analysis V1

**Status:** Analysis record. Produced by Mission 1.9.2 §10, **before** GDELT's
minimisation profile changed.
**Date:** 2026-08-30
**Reads:** the observed WEB-NGRAM contract in
[`gdelt-response-contract-v1.md`](gdelt-response-contract-v1.md) §9.5, the
committed `data_minimisation` block for `gdelt` in
[`source-compliance-v1.json`](source-compliance-v1.json), and the three other
sources' profiles for comparison.
**Related:** [`acquisition-authorization-v1.md`](acquisition-authorization-v1.md) §4,
[`gdelt-compliance-v1.md`](gdelt-compliance-v1.md) §6,
[`gdelt-web-ngram-review-v1.md`](gdelt-web-ngram-review-v1.md).

---

## 0. The question this answers

A minimisation profile says **what a collector may ask for**. GDELT's committed
one was written for the DOC API:

```json
"allowed":  ["event_identifier", "theme_identifier", "entity_mention",
             "tone_score", "observation_period", "geography", "content_origin"],
"excluded": ["article_full_text", "publisher_content", "personal_data",
             "user_identifier"]
```

The WEB-NGRAM file has four columns. **How many of them does that profile
cover?** The answer determines whether this is a configuration edit or a
reviewed addition, and §10 requires it to be settled before either.

## 1. The four observed fields

From the one capped file inspection Mission 1.9.1 performed, confirmed field by
field against GDELT's own announcement (§4 of the review):

| Column | Source definition (verbatim, GDELT) | What it is |
|---|---|---|
| `DATE` | "The date in YYYYMMDDHHMMSS format." | the 15-minute bucket stamp, identical to the filename |
| `LANG` | "The human-readable language name as output by CLD2." | a language **name**, not a code, not a place |
| `NGRAM` | "The word or phrase." | one word (`1gram`) or two (`2gram`) |
| `COUNT` | "The number of times the word/phrase was mentioned in articles of that language published in that given 15 minute interval." | an occurrence count GDELT computed |

## 2. Field by field against the committed categories

Each row asks one question: **does an existing category mean this, or does it
merely sound like it?**

### 2.1 `DATE` → `observation_period` — **covered, reuse**

`observation_period` is already allowed for GDELT and is the same category
Eurostat, FRED and World Bank use for the interval an observation belongs to. A
15-minute bucket is an interval an observation belongs to. The category's
meaning does not have to stretch to reach it.

**One thing it must not become.** `observation_period` is a *period*, and the
value here is the period's label. It is not the moment an article was published
and it is not the moment we fetched anything. §14 of the mission is explicit and
the category already carries that meaning for three other sources.

**Verdict: reuse, unchanged.** No addition.

### 2.2 `LANG` → nothing covers it — **new category required**

There are two candidates in the committed profile and both are wrong.

| Candidate | Why it fails |
|---|---|
| `geography` | **Language is not geography.** Spanish is not Spain; Arabic is not one country; the WEB-NGRAM row says nothing about where anything happened. `registry/models.py` already records the same separation for `coverage`: "Countries and languages are kept apart deliberately." Writing `LANG` into `geography` would put a fabricated place into every record |
| `entity_mention` | a language is not an entity the source extracted from coverage |

The project already has a **canonical slot** for this fact, and it is not in the
minimisation vocabulary yet: `content_language`, a real column on both
`RawRecordDraft` and `NormalizedRecordDraft` since Missions 1.5 and 1.6. The
category should be named after the field it authorises, so that a reader can see
the authorisation and the destination line up.

**Verdict: add `content_language`.** It names an existing canonical field, so it
introduces a word to the minimisation vocabulary and no new concept to the model.

**What it does not settle.** GDELT emits `ALBANIAN`, not `sq`. That is a
*representation* question for a future normalizer, answered in the review (§13):
no first-party mapping from CLD2 names to language tags is published, so the
source label is preserved verbatim and nothing is guessed. Authorising the
category does not authorise inventing a code for it.

### 2.3 `NGRAM` → nothing covers it — **new category required**

Three candidates, and this is where the profile would most easily be stretched
into a lie.

| Candidate | Why it fails |
|---|---|
| `theme_identifier` | a GDELT theme is a code from GDELT's own taxonomy (`TAX_FNCACT`, `PROTEST`), assigned by GDELT's classifier. An ngram is a word that occurred. **Nothing classified it.** Recording a word as a theme would assert that the source made a judgment it did not make |
| `entity_mention` | an entity is a resolved person, organisation or place. `dhe` is Albanian for "and". A word is not an entity, and the classifier that would decide whether one is did not run |
| `publisher_content` | already **excluded**, correctly. See §3 |

None of the three means "a term the source observed". §11 asks for the smallest
truthful category, and the truthful thing to say is exactly what the column is.

**Verdict: add `lexical_ngram`** — a term of one or two words, observed by the
source in coverage it monitored, carrying no classification, no topic assignment
and no article of origin.

The name says `ngram` rather than `term` or `keyword` on purpose: it is the unit
GDELT publishes, and a reader who sees it in a provenance record can go and find
the file it came from.

### 2.4 `COUNT` → nothing covers it — **new category required**

| Candidate | Why it fails |
|---|---|
| `tone_score` | a different measurement entirely |
| `observation_value` | not in GDELT's profile at all — and it is the category the *economic* sources use for a measured quantity with a `unit_of_measure`. A frequency has no unit in that sense, and borrowing the category would put a count where a reader expects a magnitude |

But the decisive reason to name this one precisely is **§12's warning**, which
is a warning about a mistake this repository has already almost made once. In
Mission 1.9 the `ArtList` mode was rejected partly because counting the articles
it returned would have measured `MAXRECORDS` — *our* request — and presented it
as a measurement of the world. A category called `observation_value` does not
guard against that. A category whose name says whose measurement it is does.

**Verdict: add `source_measured_frequency`** — a count of occurrences the source
computed over its own corpus.

It is explicitly **not**:

- the number of files or rows our job downloaded;
- the number of results a query returned (there is no query — see §5);
- a popularity, interest or attention score;
- a signal, an evidence weight or any input to an Opportunity Score.

The last one matters and is not hypothetical. `COUNT` is the first
source-published number in this system that *looks* like a trend measure, and
D-03 is still open. Naming it `source_measured_frequency` keeps the sentence
"this is what GDELT counted" attached to the number wherever it travels.

## 3. What stays excluded, and why nothing changes there

| Excluded category | Still excluded | Why |
|---|---|---|
| `article_full_text` | yes | the file contains none |
| `publisher_content` | yes | the file contains none |
| `personal_data` | yes | see §4 — the reason is subtler than for the other three |
| `user_identifier` | yes | there are no users in this dataset at all |

**These exclusions are not made redundant by the file's shape.** The file
contains no publisher content, so nothing has to be filtered out of it. But the
exclusions are the rule that governs *the source*, not this one dataset, and
GDELT publishes other products — NGrams 3.0 has `pre`/`post` snippets and a
`url`; the quadgram TOC has `title`, `img` and `url`. Removing the exclusions
because one authorised dataset does not need them would remove the rule that
keeps the others out.

## 4. `personal_data`, stated carefully

§19 asks the question properly: **distinguish the dataset's structure from its
possible lexical contents.**

**Structurally there is no personal data.** Four columns, none of which is a
name field, an author, a handle, an identifier or a profile. Nothing in the row
is *about* a person.

**A lexical term can nonetheless be a person's name.** A `1gram` may be
`MACRON`; a `2gram` may be `Emmanuel Macron`. That is not a defect in the
dataset and it is not something a collector can prevent by asking differently —
the file is a published aggregate and arrives whole.

What is true about such a row:

- it carries a name and **one number**, and nothing else;
- it is not linked to an article, a URL, an author or a document id;
- it is an aggregate over an entire language's coverage in a 15-minute window,
  not an observation about an individual;
- the name appears because news outlets published it, which is what GDELT's
  review already recorded as the reason the source is `PSEUDONYMOUS` rather than
  `NONE_EXPECTED`.

**The exclusion therefore stays and means what it says**: no collector may
request or retain a personal-data *field*, and there is none to request. Whether
a name occurring as an ngram is personal data in the regulatory sense is a
jurisdiction question, and jurisdiction is **H-12**, deferred project-wide since
Mission 1.3. This review does not resolve it and does not pretend to; it records
the exposure precisely so that whoever resolves H-12 can see what it applies to.

**No classification changes.** GDELT stays `PSEUDONYMOUS`. Downgrading it to
`NONE_EXPECTED` because the ngram file has no identifier column would be reading
one dataset's structure as a statement about the source.

## 5. One thing the profile does not have a category for, deliberately

Nothing here authorises **a query**. There is no query on this path: the file is
published on a fixed schedule and downloaded whole, so there is no term we send
and therefore no field for one.

That absence is worth recording because the DOC API path had the opposite
problem — [`gdelt-resource-model-v1.md`](gdelt-resource-model-v1.md) §5 had to
canonicalise *our* query into the observation identity, and two phrasings of one
research question produced two identities. A category for "the query we sent"
was never added, and on this path it never needs to be.

## 6. Result

| Field | Category | Status |
|---|---|---|
| `DATE` | `observation_period` | **reused**, unchanged |
| `LANG` | `content_language` | **added** |
| `NGRAM` | `lexical_ngram` | **added** |
| `COUNT` | `source_measured_frequency` | **added** |

Three additions, one reuse. The seven DOC API categories are **kept**: the DOC
API path is deferred, not withdrawn (§24 of the mission), and deleting the
categories that describe it would make a later un-deferral look like a new
approval.

**Nothing was mapped approximately.** Each of the three additions was reached by
first showing that every existing candidate asserts something the source did not
do — a classification that no classifier made, a place that is a language, a
measurement whose owner is unstated.
