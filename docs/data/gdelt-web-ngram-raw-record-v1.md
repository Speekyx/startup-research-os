# GDELT WEB-NGRAM RawRecord V1

**Status:** **In use.** Two real records exist, collected 2026-08-30.
**Date:** 2026-08-30 (Mission 1.9.3)
**Related:** [`gdelt-web-ngram-collector-v1.md`](gdelt-web-ngram-collector-v1.md),
[`normalized-record-v1.md`](normalized-record-v1.md) (the stage after this one,
which GDELT has **not** reached),
[`raw-record-gap-analysis-v1.md`](raw-record-gap-analysis-v1.md).

---

## 0. One record is one row of one file

Not one file, and not one HTTP response. A WEB-NGRAM file holds hundreds of
thousands of observations that revise independently — the real file this was
verified against held 223,342 — and storing the blob would mean a single changed
count invalidated all of them, and that nothing downstream could address an
observation without re-parsing a megabyte.

```text
(resource kind, DATE, LANG, NGRAM)  →  one RawRecord, whose content is COUNT
```

## 1. Identity — three things, kept apart

```text
observation_key   gdelt|web-ngrams/1gram|20260830091500|ENGLISH|climate
content_hash      sha256 over the canonical payload, which includes COUNT
record id         uuid5(namespace, workspace | key | content_hash)
```

**`COUNT` is content, not identity.** That is what makes a corrected count a
*revision* of this observation rather than a different observation, and it is the
whole reason the two are separate fields.

**The resource is in the key.** A term appearing in both the unigram and the
bigram file is two observations, not a collision — §26 forbids leaning on the
space count in `NGRAM` to tell them apart, because a two-word entry in a unigram
file would be a contract violation and inferring the kind from the text would
hide it.

**The retrieval time is in none of them.** Hashing it would make every retrieval
a revision, which turns an idempotent collector into one that grows a table
forever.

### 1.1 The separator is escaped, not forbidden

`observation_key` joins its parts with `|` and used to **refuse** any part
containing one. That was safe while every part was an identifier, a country code
or a year.

**The first real WEB-NGRAM file broke it.** News text contains pipes, so GDELT
publishes terms containing them, and the parser was discarding an entire file of
legitimate observations because of our own key format. The live smoke test found
it; no fixture had, because the fixtures were written by someone who did not
expect it either.

Forbidding was the wrong shape of answer: **any printable character can appear in
a term**, so there is no separator to move to; skipping such rows would drop real
data; and hashing would remove the readability the key exists for. The parts are
escaped instead — `\` → `\\`, then `|` → `\|` — which keeps the guarantee that
distinct part sequences produce distinct keys without deciding what a source may
say.

Every part of every record written before the change contains neither character,
so the escaping is a no-op on all of them and no committed key moved.

## 2. The payload

```json
{
  "source_id": "gdelt",
  "resource_id": "web-ngrams/1gram",
  "gram_kind": "1gram",
  "date": "20260830091500",
  "lang": "ENGLISH",
  "ngram": "climate",
  "count": "55"
}
```

**`count` is a string.** For the reason the World Bank value is one: the
fingerprint is computed in Python and the payload is re-read from `JSONB`, and
the two must agree byte for byte about a record nobody changed. It never passes
through a float, and Python's arbitrary-precision `int` means a count beyond
2⁵³ arrives exact.

**Seven keys, and no eighth.** No url, no title, no author, no image, no domain,
no person — asserted, not assumed.

## 3. `observed_at` is NULL, and that is the point

`observed_at` is a `TIMESTAMPTZ`. Writing anything into it means naming a zone,
and **GDELT documents no timezone for the WEB-NGRAM `DATE` column** — not on the
dataset announcement, not on the data index. That is **H-29**.

So the column stays empty and the bucket label survives verbatim in the payload
and in provenance, alongside a recorded 15-minute resolution and an explicit
`bucket_timezone: null` with a note saying why.

**Answering H-29 later is a re-derivation over records already held**, not a
re-collection. That is the whole value of preserving the label: the cheap fix
stays cheap.

It also means downstream must not read `observed_at` as "no event time exists".
It means *this project has not established one*, which is a different statement
and the one the data supports.

## 4. `content_language` is NULL for the same shape of reason

GDELT emits `ALBANIAN`, `ENGLISH`, a few in titlecase, some with underscores —
CLD2 human-readable **names**. This project's canonical language representation
is a BCP-47 tag, and no published mapping between the two was found (**H-30**).

`content_language` is a column a reader takes for a code. A name sitting in it
would be a guess wearing the clothes of a fact, so it stays empty and the exact
label lives in `payload.lang`, where it is identity-bearing, and in
`provenance.source_language_label` with
`language_representation: "SOURCE_NATIVE_CLD2_NAME"`.

This is the pattern `CanonicalGeography.unclassified` already sets: **the
canonical slot stays empty and the source value is preserved.**

And `LANG` is never geography. Spanish is not Spain; the row says nothing about
where anything happened; there is no `geography` key in the payload or the
provenance, and a test asserts its absence.

## 5. Provenance — every §27 question, without parsing a URL

| Group | Keys |
|---|---|
| source and review | `source_id`, `review_version`, `approval_state`, `condition_snapshot`, `authorization_issued_at` |
| route | `access_profile`, `access_method`, `endpoint`, `received_filename` |
| resource and rights | `resource_id`, `dataset_family`, `rights_basis`, `licence` (**null**), `content_origin`, `licence_basis` |
| the observation | `gram_kind`, `source_bucket_label`, `bucket_resolution_minutes`, `bucket_timezone` (**null**, with a note), `source_language_label`, `language_representation`, `source_ngram` |
| obligations | `attribution`, `retention_days`, `retention_basis` |
| bounds | `acquisition_bounds` (the reviewed 8), `operational_bounds` (`INTERNAL_SAFETY_POLICY`), `pacing_origin` |
| what we did | `local_filter` with `applied_by: "collector"` |

**`rights_basis` is recorded next to `licence`.** A record carrying only
`licence: null` would be indistinguishable from one whose licence nobody
established; `DIRECT_GRANT` says the question was asked and answered.

Plus the row's own columns: `workspace_id`, `research_session_id`,
`correlation_id`, `collector_id`, `collector_version`, `collected_at`,
`expires_at`, `source_reference`, `acquisition_method`.

## 6. Retention and attribution are not the collector's to choose

`expires_at` is `collected_at + 30 days`, the governance-resolved raw window.
`build_raw_record` has **no parameter** for an expiry and none for an attribution
string, so a collector has nothing to pass even if it wanted to.

The attribution notice is rendered from the obligation GDELT review 3 recorded,
and rendering **fails closed**: a resource whose licence the obligation required
and whose entry did not carry one would raise rather than produce a record with
no credit attached.

## 7. Personal data

No new field, and no detection. A lexical ngram may happen to equal a person's
name — `MACRON` is a valid unigram — and the collector does not look, does not
resolve, and does not attach an article.

What such a record holds is a name, one number, and no link to any article,
author or document. Whether that is personal data in the regulatory sense is
jurisdiction, which is **H-12** and deferred project-wide since Mission 1.3.
`personal_data` and `user_identifier` remain excluded categories.

## 8. What has NOT happened to these records

They are `RawRecords` and nothing more.

| | |
|---|---|
| normalized | **no.** `IMPLEMENTED_NORMALIZERS == {world-bank}` |
| turned into a signal | **no.** `nlp.signals` is empty |
| embedded | **no.** `nlp.embedding_provenance` is empty |
| a claim, evidence, or a score | **no.** All zero, and scoring is still blocked on D-03 |

`COUNT` is what GDELT counted. It is not a trend, not attention, not demand, and
not evidence of anything until a later stage says so under its own review.
