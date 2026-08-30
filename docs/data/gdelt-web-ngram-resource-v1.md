# GDELT WEB-NGRAM Resource V1

**Status:** **Committed.** Two authorised resources exist in
[`source-compliance-v1.json`](source-compliance-v1.json), and GDELT is the second
source in the catalog to have any.
**Date:** 2026-08-30 (Mission 1.9.2)
**Related:** [`gdelt-web-ngram-review-v1.md`](gdelt-web-ngram-review-v1.md),
[`gdelt-resource-model-v1.md`](gdelt-resource-model-v1.md) §8,
[`acquisition-authorization-v1.md`](acquisition-authorization-v1.md),
[ADR-016](../architecture/adr/ADR-016-compliance-capabilities-and-acquisition-authorization.md),
[ADR-018](../architecture/adr/ADR-018-acquisition-rights-basis.md).

---

## 0. What changed

Before this mission, `context.datasets` was empty for GDELT.
`authorized_dataset(...)` returned `None` for everything, so no collector could
build a descriptor, and the resource model was failing closed exactly as
designed — on a question nobody had answered.

The question was *what is one GDELT resource*, and it had been blocked on H-27
because the answer depended on which DOC API mode a collector would use. Review 3
answered it from a different direction: **a published file, not an API mode.**

## 1. The two entries

```json
{
  "resource_id": "web-ngrams/1gram",
  "name": "GDELT WEB-NGRAM unigrams",
  "dataset_family": "web-ngrams-1gram",
  "rights_basis": "DIRECT_GRANT",
  "content_origin": "PLATFORM_LICENSED",
  "basis": "GDELT's terms grant 'unlimited and unrestricted use ...' over ALL DATASETS RELEASED BY the GDELT Project, naming no licence instrument. ..."
}
```

and the same shape for `web-ngrams/2gram` / `web-ngrams-2gram`.

**No `licence` key on either.** Under `DIRECT_GRANT` the model refuses one, and
that refusal is the whole of ADR-018: `"OTHER"`, `"GDELT Terms Licence"`,
`"NONE"` and `"N/A"` are four different lies, and any of them would reach every
record's provenance indistinguishable from `CC-BY-4.0`.

**`PLATFORM_LICENSED`, and the distinction is doing real work.** GDELT's count
over its own index is GDELT's. The news it counted belongs to publishers who
granted nothing, is `THIRD_PARTY`, and `third_party_denied` stays on. An
aggregate *about* third-party material is not third-party material — the same
reasoning Mission 1.9.1 recorded for a tone average, applied to a frequency.

## 2. The access route

| | |
|---|---|
| profile | `gdelt-web-ngram-files` |
| method | `DATASET_DOWNLOAD` |
| endpoint | `https://data.gdeltproject.org/gdeltv3/web/ngrams/` |
| host authorised | `data.gdeltproject.org`, and only through this profile |
| credentials | none documented, none referenced |
| rate limit | **unknown**, and not invented |

### 2.1 Why the endpoint is a directory and not the site root

§6 of the mission: *do not give the profile a source-wide root if a narrower path
can represent the reviewed dataset.* A root of `https://data.gdeltproject.org/`
would authorise every bulk product GDELT publishes — including Web News NGrams
3.0, one directory across, which this review rejected.

### 2.2 The path boundary is fail-closed by construction

No new rule was needed, and that is worth stating because the temptation was to
write one.

`HttpxTransport` composes every request as `base_url + path.lstrip("/")`, and
`HttpRequest` refuses a path containing `..` or one that looks like a URL. So
with the base above:

| Attempt | Result |
|---|---|
| `../webngrams/x.gz` | **refused** — `path must not traverse` |
| `https://storage.googleapis.com/...` | **refused** — `path is a path, not a URL` |
| `/gdeltv3/webngrams/x.gz` | flattened *into* the authorised directory: `.../gdeltv3/web/ngrams/gdeltv3/webngrams/x.gz` |

The narrow endpoint is therefore an enforced boundary rather than a documented
intention, and the assertions live in `test_gdelt_web_ngram.py`.

### 2.3 What the profile replaced

`gdelt-bulk-files`, registered by Mission 1.7 as a placeholder that named the
bulk route in general and **deliberately carried no endpoint**, so it authorised
no host. Mission 1.9 asserted that absence so that "adding one is a decision
somebody takes rather than a line somebody copies".

Review 3 is that decision, and what it authorises is narrower than the
placeholder's name. Replacing rather than filling in leaves nothing for a later
mission to quietly widen.

## 3. The reviewed acquisition bound

```json
"acquisition_bounds": { "max_files_per_job": 8, "basis": "..." }
```

GDELT emits 96 buckets a day, two files per bucket, from 2019-01-01 to present.
Ingesting that is the bulk-data vacuum this system is not.

**Eight files** is two hours of one ngram kind, or one hour of both — enough for a
bounded look at a moving window, far short of a corpus.

**The unit is the file** because that is the unit GDELT publishes and the unit a
request costs. It bounds bytes, request count and load in one number, which is
why one number was enough.

**The ceiling belongs to the review.** A collector that chose its own bound would
be setting its own permissions. `context.authorize_job_size(n)` is how a
collector asks, and a job that does not state its size is refused — the same
asymmetry `ResourceDescriptor` is built on.

### 3.1 Two bounds considered and not written

**A time window.** It constrains nothing `max_files_per_job` does not, and the
job it would restrict hardest — a few files sampled across two years — is the
*cheaper* one for the source. A control with no rationale is a control that gets
removed by whoever first finds it inconvenient.

**A language allowlist.** This is the more interesting rejection, and it comes
straight from the observed contract: **each file spans every language GDELT
monitors.** `LANG` is a data column, not a partition. A job therefore cannot
request fewer languages than a file contains, so language is not a dimension of
the request at all.

Which languages are *retained* is a real question — and it is a research decision
and a normalizer's concern, not a term of the grant, which restricts no language.
Encoding it here would present a product choice as a legal conclusion, which §16
warns against.

That is §16's distinction, made concrete:

| | |
|---|---|
| **authorized maximum scope** | every language GDELT publishes — the grant restricts none |
| **operational request scope** | not expressible in languages: the file is the unit |
| **retention scope** | a research decision for the collector mission, bounded by the minimisation profile |

## 4. What a future collector may and may not do

It **may**, holding an `AcquisitionAuthorizationContext` for GDELT:

- build a descriptor from `authorized_dataset("web-ngrams/1gram")` or
  `.../2gram` — and from nothing else;
- fetch up to `max_files_per_job` files under the authorised directory, after
  `authorize_job_size` returns no refusals;
- retain `observation_period`, `content_language`, `lexical_ngram` and
  `source_measured_frequency`;
- keep raw records for 30 days and normalized for 365 — governance-resolved, not
  chosen;
- carry the citation and link on every derived surface.

It **may not**:

- reach any other host, path or dataset;
- construct a descriptor from anything a caller claims;
- interpret `LANG` as geography, or map it to a language code;
- assert a timezone for `DATE`;
- treat `COUNT` as a signal, a score, or a measurement of anything other than
  what GDELT counted;
- decide its own volume ceiling.

## 5. What is still not authorised

| | |
|---|---|
| any DOC API mode | H-27 — no envelope has ever been observed |
| Web News NGrams 3.0 | publisher snippets plus the article URL |
| the quadgram files and their TOC | per-document `DOCID`, plus `title`, `img`, `url`; and a host no review has assessed |
| any other GDELT bulk product | not assessed by any review |
| `storage.googleapis.com` | not on any GDELT access profile |
| a `3gram` or longer | GDELT publishes no such WEB-NGRAM file here, and §4 of the review does not extend automatically |

Each of the first four is refused by two independent mechanisms: no enumerated
entry to build a descriptor from, and a family allowlist that refuses one built
by hand anyway.
