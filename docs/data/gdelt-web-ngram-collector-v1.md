# GDELT WEB-NGRAM Collector V1

**Status:** **Implemented.** `gdelt-web-ngram@1.0.0`, the second collector and
the first for a non-economic source.
**Date:** 2026-08-30 (Mission 1.9.3)
**Code:** `sros_acquisition.collection.gdelt_web_ngram`
**Related:** [`world-bank-collector-v1.md`](world-bank-collector-v1.md) (the
reference architecture), [`gdelt-web-ngram-review-v1.md`](gdelt-web-ngram-review-v1.md),
[`gdelt-web-ngram-resource-v1.md`](gdelt-web-ngram-resource-v1.md),
[`gdelt-web-ngram-raw-record-v1.md`](gdelt-web-ngram-raw-record-v1.md),
[`acquisition-authorization-v1.md`](acquisition-authorization-v1.md).

---

## 0. What it collects, and what it refuses

Two resources, both authorised by GDELT review 3:

```text
web-ngrams/1gram    https://data.gdeltproject.org/gdeltv3/web/ngrams/<DATE>.1gram.txt.gz
web-ngrams/2gram    https://data.gdeltproject.org/gdeltv3/web/ngrams/<DATE>.2gram.txt.gz
```

It refuses, by construction rather than by check: `3gram` and longer, Web News
NGrams 3.0, the quadgram files and their TOC, `ArtList`, every DOC API mode, and
every other GDELT product. A gram kind outside `GRAM_KINDS` cannot even be put
into a request — the `ValueError` is raised when the request is *constructed*, so
there is no spelling of `3gram` that reaches a filename.

## 1. The shape, against the World Bank precedent

| | World Bank | GDELT WEB-NGRAM |
|---|---|---|
| transport | `Transport.get` — buffered JSON | `StreamingTransport.download` — bounded byte chunks |
| unit | a page of a paginated API | one published file |
| request names | indicators, countries, years | gram kinds and exact source bucket labels |
| bound on scope | pages and records | **the reviewed 8 files per job**, plus records |
| identity | `source \| resource \| geography \| period` | `source \| resource \| DATE \| LANG \| NGRAM` |
| event time | the start of the period | **none** — the timezone is unestablished |

**What is shared is shared because two collectors proved it**, not because a
third might: `build_raw_record` (governance-derived retention, attribution,
identity and the condition snapshot), `code_for_status` (the retry
classification) and `observation_key`. There is no "bulk source engine" between
them, because two sources are not yet a pattern.

## 2. The order every collection runs in

```text
    build_authorization(source, compliance)   ← the gate; raises, or there is no context
        ↓
    context.authorize_job_size(file_count)    ← the REVIEWED ceiling, 8 files
        ↓
    resolve the gdelt-web-ngram-files route   ← by LABEL, never access[0]
        ↓
    for each gram kind:
        context.authorize_resource(descriptor built FROM the authorized dataset)
        ↓  for each bucket:
        transport.download(...)               ← the first socket, and not before
```

**Every refusal above the download line costs zero network calls**, and the tests
assert that against the transport's own request log rather than a mock's call
count — a refusal that happened one line too late would still fail.

**The job size is checked once for the whole request**, not per file. Checking it
per file would let a nine-file request through as nine one-file successes, and
splitting it would be the collector granting itself a ceiling the review did not.

### 2.1 The route is resolved by label

`context.access[0]` would have worked. GDELT carries **two** profiles and the
first is the deferred DOC API, so `access[0]` would have authorised
`api.gdeltproject.org` for a file download the day the profile order changed.
The allowlist this collector passes to the transport is `{data.gdeltproject.org}`
and nothing else — the source's own other host is unreachable from here.

The same defect reached `build_raw_record`, where it was not hypothetical: every
record would have recorded `PUBLIC_API` / `gdelt-doc-api` as its acquisition
method. The access label is now a required argument rather than an inference.

## 3. Two ceilings, different in kind

| | Origin | Enforced by |
|---|---|---|
| **8 files per job** | GDELT **review 3** | `context.authorize_job_size` |
| compressed bytes, decompressed bytes, line length, rows scanned, records kept | **ours** | `NgramBounds`, labelled `INTERNAL_SAFETY_POLICY` |
| 2 s between downloads, 24 requests per job | **ours** | `WEB_NGRAM_PACING`, same label |

`NgramBounds.ORIGIN` and `PacingPolicy.origin` both read `INTERNAL_SAFETY_POLICY`
and both travel into every record's provenance. Nothing here is a quota anybody
published: **GDELT documents no rate limit for this route**, and the HTTP 429
Mission 1.9 saw came from `api.gdeltproject.org`, which is a different route
whose limit says nothing about this one.

**A collector cannot redefine the reviewed ceiling** — the string
`max_files_per_job` does not appear in its source, and a test asserts that.

## 4. Streaming, and the three ceilings that make it safe

`HttpxTransport.download` yields bounded chunks through the same boundary as
`get`: the host allowlist, the https requirement and the refusal to follow a
redirect are all enforced in the same order, because a second entry point that
checked less would be the escape the first one closes.

The collector feeds those chunks to `zlib.decompressobj(31)` — gzip framing, not
raw deflate, so a body that is not gzip fails immediately rather than producing
plausible rubbish. That is what stops an HTML error page being read as an ngram
file.

| Ceiling | Catches |
|---|---|
| compressed bytes | an unexpectedly enormous file |
| decompressed bytes | **amplification** — kilobytes on the wire becoming megabytes |
| line length | a file with no newline in it, which would otherwise grow the buffer until the worker died while every other bound still read as satisfied |

A stream that ends before the gzip trailer is a **truncated download**, reported
as such rather than treated as a short file.

**The file is streamed; the matches are collected.** The largest thing alive from
the file itself is one line — a 223,342-row real file yielded two records without
ever being held. The matched subset is returned as a list rather than yielded,
and that is a retry-safety decision: a generator would have handed its caller the
rows read before a mid-stream failure, and the retry would then deliver them a
second time.

## 5. The parser

Exactly four tab-separated fields. **No column shifting, no concatenation, no
guessing.** A five-field row is not a row with a longer ngram; it is a row from a
file whose contract is not the one this parser was written against.

**A malformed row is fatal for its file** and the file contributes nothing.
Skipped rows were the alternative and were rejected: the contract is documented
first-party and observed, so a deviation means the contract changed or the file
is not the one requested — and both need a person, which is the stance
`world_bank._parse` already takes towards an unexpected envelope.

Our own ceilings are the deliberate exception. Hitting `max_records` or
`max_rows_scanned` **truncates and keeps** what was accepted, and the file report
says which bound stopped it. **A source-contract violation discards; an
operational ceiling truncates and says so.**

### 5.1 The four fields

| Field | Kept as | Never |
|---|---|---|
| `DATE` | the bucket label verbatim, plus a recorded 15-minute resolution | a timezone. **H-29 is open** and `observed_at` is `None` |
| `LANG` | the CLD2 language **name** verbatim, in the payload | a geography, a country, or a guessed language tag. **H-30 is open** and `content_language` stays `NULL` |
| `NGRAM` | the term verbatim, strict UTF-8 | a theme, an entity, a topic, a keyword intent |
| `COUNT` | an arbitrary-precision integer, stored as a canonical decimal string | a float, a score, a strength, a signal |

**`content_language` stays empty on purpose.** It is a column a reader takes for
a code; GDELT emits a name; no published mapping between them was found. That is
the pattern `CanonicalGeography.unclassified` already sets — the canonical slot
stays empty and the source value is preserved where it is identity-bearing.

**Strict UTF-8, never `errors="replace"`.** A replacement character would become
part of an ngram, part of its identity and part of its fingerprint, and the
corruption would be indistinguishable from a term GDELT actually published.

## 6. Local filtering

A WEB-NGRAM file spans every language GDELT monitors. The collector supports
three **local** filters applied after parsing: exact language labels, exact
ngrams, and a lexical prefix.

**Filtering decides which observed rows are persisted and changes nothing a
stored observation claims.** The same row produces a byte-identical payload,
fingerprint and record id whether it arrived through a filter or not, and a test
asserts exactly that.

Every record's provenance carries `local_filter` with `applied_by: "collector"`,
so nobody can later mistake our narrowing for the source's. The job report
carries `rows_scanned` alongside `rows_matched` for the same reason: the
controlled acquisition scanned 223,342 rows and kept 2, and saying only "2" would
describe a file that does not exist.

**No semantic filtering.** No LLM, no embedding, no model — asserted by walking
the module's imports rather than by grepping its prose.

## 7. Failures, retries and cancellation

| Situation | Code | Retried |
|---|---|---|
| timeout, connection failure | `NETWORK_TIMEOUT` / `TEMPORARY_UPSTREAM` | yes, bounded |
| HTTP 429 | `RATE_LIMITED` | yes, bounded |
| HTTP 5xx | `TEMPORARY_UPSTREAM` | yes, bounded |
| **HTTP 404 — bucket not published** | `UPSTREAM_CLIENT_ERROR` | **no** |
| invalid or truncated gzip | `PARSING_FAILURE` / `INVALID_RESPONSE` | **no** |
| malformed row | `INVALID_RESPONSE` | **no** |
| authorization or job-size refusal | `AUTHORIZATION_REJECTED` | **no** |

**A 404 means the requested source bucket is unavailable.** It is not a cue to
try adjacent dates until something works: there is no discovery crawler, H-31
leaves the directory's historical extent unestablished, and a collector that
hunted for a file that exists would be reporting the hunt rather than the request.

**Cancellation is honest.** It is checked before each file, and an in-flight
download may finish within its own timeout. What is guaranteed is that no new
file starts.

## 8. Transactions

| | |
|---|---|
| per file | **atomic.** A file either contributes all its accepted rows or none |
| per job | persistence is **one transaction** over the accepted rows of the files that completed |
| across files | **not** all-or-nothing, and it does not claim to be |

A file that fails is reported in `files_failed` while the others persist. §33 is
explicit that claiming atomicity across eight independent downloads would be
claiming something the architecture does not provide.

## 9. Idempotency

Duplicate Celery delivery is safe and this does not claim exactly-once. The
record id is `uuid5(namespace, workspace | key | fingerprint)` and none of those
is a clock, so:

```text
first delivery    NEW
second delivery   UNCHANGED   (the row is found and a timestamp moves)
revised COUNT     REVISED     (a new row; the previous one is superseded, not overwritten)
```

Verified live: the same controlled request run twice produced `2 new` then
`2 unchanged`, with two rows in the table.

## 10. Where it runs

`acquire.collect.gdelt_web_ngram`, on the existing acquisition queue. A separate
task name rather than a `source_id` parameter on the World Bank one: the two
carry different request vocabularies, and a single task taking a union of both
would validate neither.

**No authorization travels in the payload.** The job loads the registry, builds
the authorization and checks the operational switch at execution time, every
time — so a source suspended between planning and execution is not collected
because a planner had already decided it could be, and the reviewed ceiling is
re-checked against the configuration in force now.

## 11. What this collector does not do

- **normalize.** GDELT has no normalizer; `IMPLEMENTED_NORMALIZERS` is
  `{world-bank}` and GDELT `NormalizedRecords` are zero.
- interpret, classify, extract claims, embed or score.
- reach any host but `data.gdeltproject.org`, or any path but the reviewed
  directory.
- decide its own volume ceiling, its own retention or its own attribution.
- serve the DOC API. **H-27 is still open** and no timeline envelope has ever
  been observed; writing a parser against invented field names is what Mission
  1.9 refused to do, and that refusal stands.
