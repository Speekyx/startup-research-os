# GDELT Resource Model V1

**Status:** §1–§7 describe the DOC API path, **still specified and still not
committed**: H-27 is open and that route is now **deferred**. §8 describes the
WEB-NGRAM path, whose contract *is* observed — and as of Mission 1.9.2 it is
**committed**. The governance round §8.4 set out has been carried out; see
[`gdelt-web-ngram-resource-v1.md`](gdelt-web-ngram-resource-v1.md) for what was
actually authorised.
**Date:** 2026-08-30
**Produced by:** Mission 1.9.1 §17–§22.
**Related:** [`gdelt-response-contract-v1.md`](gdelt-response-contract-v1.md),
[`gdelt-compliance-v1.md`](gdelt-compliance-v1.md),
[`acquisition-rights-basis-gap-analysis-v1.md`](acquisition-rights-basis-gap-analysis-v1.md),
[ADR-018](../architecture/adr/ADR-018-acquisition-rights-basis.md).

---

## 0. What was blocking this, and what no longer is

Mission 1.9 found `context.datasets` empty for GDELT, so `authorized_dataset(…)`
returned `None` for everything and no draft could be built. Two things stood in
the way:

| Blocker | Status |
|---|---|
| **H-28** — the model required a named licence, and GDELT names none | **closed.** ADR-018 |
| **H-27** — nobody knows what a timeline response looks like | **open** |

H-28 was the harder one and it is done: a resource can now record that a
**direct terms grant** authorises it, without inventing a licence identifier.

## 1. The first mode: `TimelineTone`

On the evidence available, and to be confirmed against the fixture.

| | |
|---|---|
| **Why** | tone over time maps onto the committed minimisation profile *exactly* — `tone_score` plus `observation_period` — and returns no publisher content |
| **Not `ArtList`** | its fields are publisher references and headline text; Mission 1.9 §10 keeps it out |
| **Not `TimelineVol`** | volume as a *percentage of all monitored coverage* is a ratio against a denominator we do not hold, and the profile has no category for it |
| **`TimelineVolRaw`** | §4 below — a real measurement, and a governance question |

**If the fixture shows `TimelineTone` cannot be represented within the current
categories, it is not forced.** §11 is explicit, and the blocker would be
documented instead.

## 2. Content origin — the distinction that has to be right

GDELT timeline metrics are **produced by GDELT** from its index of worldwide
news. They are aggregate measurements over coverage, not the coverage itself.

| Artefact | Origin | Available? |
|---|---|---|
| a tone average for a time bucket | GDELT's own computation | `PLATFORM_LICENSED` |
| an article count for a bucket | GDELT's own computation | `PLATFORM_LICENSED` |
| the articles counted | publishers | `THIRD_PARTY` — refused |
| headline, image, body | publishers | refused, and excluded by the minimisation profile |

**Do not read this as "GDELT content is platform-licensed".** The metric is;
what it describes is not. `third_party_denied` stays on, and a resource whose
origin is unrecorded stays refused — an aggregate *about* third-party material
is not third-party material, and that distinction is doing real work rather than
being a formality.

## 3. The dataset entry, ready to commit

Once §4 of the response contract is filled in:

```json
{
  "resource_id": "doc-api/timeline-tone",
  "dataset_family": "DOC_API_TIMELINE_TONE",
  "content_origin": "PLATFORM_LICENSED",
  "rights_basis": "DIRECT_GRANT",
  "basis": "GDELT's terms grant unlimited and unrestricted use for any academic, commercial or governmental use of any kind without fee, naming no licence. Retrieved 2026-08-30; recorded in the Mission 1.7 review evidence."
}
```

**No `licence` key**, and its absence is enforced rather than conventional:
`AuthorizedDataset` refuses a `DIRECT_GRANT` that carries one (ADR-018).

`dataset_family` is per mode because `require_dataset_family` is on: the review
assessed the DOC API for a specific capability set, GDELT publishes more, and a
resource that cannot say which family it belongs to has not been assessed.

## 4. `TimelineVolRaw` — a governance question, not a technical one

§12 forbids authorising it automatically, and the reason is subtle enough to
state carefully.

**Its count is a real GDELT measurement**, unlike an `ArtList` count. `MAXRECORDS`
is documented as ignored in timeline modes, so the number is GDELT's own and not
an artefact of our request bound. The objection that killed the `ArtList`
workaround does not apply.

**The minimisation profile still has no category for it.** The committed
`allowed` list is `event_identifier`, `theme_identifier`, `entity_mention`,
`tone_score`, `observation_period`, `geography`, `content_origin`. A count of
matching articles is none of those, and `norm` — the total monitored — is
another.

So the honest position is: **not authorised, and cheap to authorise properly.**
It needs a reviewed addition to the minimisation profile naming a
coverage-volume category, which is governance work of the kind Mission 1.8 did,
not a collector decision. §12 permits the first collector to support
`TimelineTone` only, and it should.

Recording the temptation, since it will recur: adding the category *while*
writing the collector would be the collector widening its own permissions, which
is the shape of failure the whole authorization boundary exists to prevent.

## 5. Observation identity — a weaker guarantee, stated as one

§21 asks for this to be documented rather than papered over.

World Bank's key is `source | indicator | geography | period` and every part is
the source's own: the indicator code is a series identifier GDELT has no
equivalent of.

A GDELT timeline observation is identified by:

```text
gdelt | doc-api/timeline-tone | <canonical query> | <bucket start>
```

**The query is ours.** Two research questions phrased differently produce
different keys for the same underlying coverage, and no dedup across them is
possible or attempted. That is a materially weaker guarantee than World Bank's
and it is not disguised: deriving identity from an article title instead would
be the instability §19 warns about, and there is nothing else on offer.

The bucket start also needs its **resolution** recorded alongside it, because
GDELT chooses the step from the span (15-minute under 72 hours, hourly to a
week, daily beyond). A bucket start with no resolution is ambiguous.

### 5.1 Query canonicalisation

Deterministic and syntactic only (§22).

**Does** normalise: surrounding whitespace, internal whitespace runs, and the
parameter encoding the transport applies — harmless transport differences must
not produce different identities.

**Does not** normalise: case inside quoted phrases, operator order, or anything
requiring interpretation. Two differently phrased queries may legitimately be
different questions, and **no LLM rewrites a query** — claiming two phrasings
mean the same thing is a semantic judgment nothing here is entitled to make.

## 6. Pacing

`rate_limit_known` stays **false** on both profiles. GDELT publishes no quota,
and the HTTP 429 observed in Mission 1.9 proves throttling exists without
revealing its shape.

A future collector needs conservative local pacing marked as **our** policy —
never as GDELT's published limit. The fixture-capture script already models the
posture: two requests, fifteen seconds apart, and a 429 met by stopping rather
than by shortening the pause.

No runtime pacing is built here. There is no collector to pace, and §23 warns
against overengineering one that does not exist.

## 7. What is left

1. **H-27** — capture the two fixtures. `capture_gdelt_fixtures.py` is ready.
2. Fill in §4 and §5 of the response contract from them.
3. Commit the §3 dataset entry, confirmed against the observed envelope.
4. Decide `TimelineVolRaw` (§4) — a reviewed minimisation category, or leave it
   documented and unauthorised.
5. Then Mission 1.9.2 builds the collector.

Steps 1 to 4 are governance and capture. Only step 5 is engineering.

---

## 8. The WEB-NGRAM path, added after H-27 reproduced

The DOC API failed from a second independent environment, and GDELT's own
documentation says why: its legacy search infrastructure is under strain during a
Spanner migration, and it asks researchers to **use ngram files instead of the
search APIs**.

The contract is recorded in
[`gdelt-response-contract-v1.md`](gdelt-response-contract-v1.md) §9. What matters
for the resource model:

### 8.1 It answers three problems §1–§7 could only mitigate

| Problem on the DOC API path | On the WEB-NGRAM path |
|---|---|
| publisher content had to be filtered out | **the file contains none** — four columns, no title, URL, image or sentence |
| the count risked being request-bounded | **no query is issued**; the file is a published aggregate GDELT computed |
| identity depended on *our* query (§5) | **`(DATE, LANG, NGRAM)` is source-native** — the §5 weakness disappears |
| host unreachable from two environments | `data.gdeltproject.org` returns 301 from here |

### 8.2 The dataset entry it would need

```json
{
  "resource_id": "web-ngrams/1gram",
  "dataset_family": "WEB_NGRAM_UNIGRAM",
  "content_origin": "PLATFORM_LICENSED",
  "rights_basis": "DIRECT_GRANT",
  "basis": "GDELT's terms grant unlimited and unrestricted use for any academic, commercial or governmental use of any kind without fee, naming no licence. The WEB-NGRAM files are datasets released by the GDELT Project and are therefore inside that grant."
}
```

`DIRECT_GRANT` and **no licence key** — the rights basis is unchanged from §3,
because the grant is over everything GDELT releases and this is one of those
things. **H-28 stays closed and this path needs nothing new from it.**

### 8.3 What it cannot inherit

**Not the `gdelt-doc-api` access profile.** This is `data.gdeltproject.org` over
`DATASET_DOWNLOAD` — the `gdelt-bulk-files` profile, which deliberately records
no `endpoint_url` and therefore authorises no host. Stretching the API profile to
cover a different host over a different method would be precisely the
"source-level approval widened into a resource grant" §10 forbids.

**Not the current capability list.** The Mission 1.7 review recorded news
events, themes, entity mentions, tone, timestamps and geography. A term
frequency is none of them.

**Not the current minimisation profile.** No category covers a term or a count,
and `LANG` is not `geography`.

### 8.4 Therefore: a review version, not a config edit

**All four steps were carried out in Mission 1.9.2**, and step 5 was not. What
follows is the plan as written; what was actually committed —
including one thing the plan got wrong — is in
[`gdelt-web-ngram-resource-v1.md`](gdelt-web-ngram-resource-v1.md).

The plan's `resource_id`/`dataset_family` in §8.2 above were `web-ngrams/1gram`
and `WEB_NGRAM_UNIGRAM`; the committed family follows the lowercase convention
World Bank's `indicators` established, and there are **two** entries rather than
one because §20 of the mission required 1gram and 2gram to be assessed
separately. The plan also assumed a language restriction would be the volume
control; the observed contract says otherwise, because each file spans every
language.

The honest sequence, and none of it is collector code:

1. **Re-review GDELT** against the ngram datasets — a new review version
   recording the capability (term frequencies), the access route
   (`gdelt-bulk-files`, with its endpoint) and the verdict. The rights grant is
   unchanged and re-cited rather than re-argued.
2. **Add a reviewed minimisation category** for a term and its frequency, and
   decide the language/term restriction there — 96 buckets a day across 142
   languages is a bulk-data vacuum unless the profile bounds it.
3. **Record `endpoint_url`** on `gdelt-bulk-files`.
4. **Commit the §8.2 dataset entry.**
5. Then a collector.

Steps 1–4 are governance. Only step 5 is engineering, and it is smaller than the
DOC API collector would have been: a gzipped tab-delimited file with four columns
and no pagination.

### 8.5 What is explicitly NOT recommended

**Web News NGrams 3.0** and the **quadgram TOC** files. Both carry publisher
content — 3.0 has `pre`/`post` snippets of up to seven words plus the article
`url`; the TOC has `title` and `img`. They are out for the same reason `ArtList`
is, and being newer or more prominent does not change that.
