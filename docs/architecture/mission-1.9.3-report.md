# Mission 1.9.3 — the GDELT WEB-NGRAM collector, and two real records

**Sprint 1 / Mission 1.9.3** · 2026-08-30
**Status:** **Complete.** `gdelt-web-ngram@1.0.0` is implemented, enabled in this
deployment, and has collected two real observations from one reviewed file.
**Nothing was normalized, embedded, scored or turned into a signal**, and six
World Bank records are byte-for-byte unchanged.

---

## 1. Collector architecture

The World Bank precedent, followed where it applies and diverging where the
source genuinely differs.

| | World Bank | GDELT WEB-NGRAM |
|---|---|---|
| transport | `Transport.get` — buffered JSON | `StreamingTransport.download` — bounded chunks |
| unit | a page of a paginated API | one published file |
| request | indicators, countries, years | gram kinds, exact source bucket labels |
| scope bound | pages, records | **the reviewed 8 files/job**, plus records |
| identity | `source\|resource\|geography\|period` | `source\|resource\|DATE\|LANG\|NGRAM` |
| event time | the start of the period | **none** — see §10 |

**Three things became shared, each because two collectors proved it:**
`build_raw_record` (retention, attribution, identity, the condition snapshot),
`code_for_status` (the retry classification — two copies is how one of them
quietly starts retrying a 404) and a variadic `observation_key`.

**There is no "bulk source engine".** §39 warned against it and two sources are
not a pattern. What is shared is what both actually needed.

## 2. Streaming design

`HttpxTransport.download` was added rather than replacing `get`. The audit §13
asks for found that `get` buffers a complete body and decodes it as **text**,
which is right for a JSON API and wrong twice for a gzipped file: the decode
corrupts the bytes, and a file of unknown size is held whole before anyone can
object to it.

It is a **separate protocol** (`StreamingTransport`) rather than a method on
`Transport`, so no existing fake grows a method it does not use. `HttpxTransport`
implements both.

**Every rule `get` enforces is enforced in `download`, in the same order** — host
allowlist, https, no redirect followed. A second entry point that checked less
would be the escape the first one closes; the redirect refusal is now one shared
method so the two cannot drift.

One incidental fix: the client's `Accept` header was fixed at
`application/json`, a request for a representation GDELT does not publish.

## 3. Request and bucket model

```python
WebNgramRequest(buckets=(...), grams=("1gram",), languages=(), ngrams=(), ngram_prefix=None)
```

Five fields, and **none of them is a host, a path, a filename or a query**. A
test asserts the field set exactly, because a behavioural test would pass against
a request that grew a `path` nobody had used yet.

Bucket labels are validated syntactically and returned **unchanged**: fourteen
digits, a real calendar date, a minute on the published quarter-hour grid, zero
seconds. All four are deterministic and **none requires knowing the timezone** —
which is the point (§10).

## 4. Filename construction

```text
<validated bucket>.<reviewed gram kind>.txt.gz
```

Both parts are validated before they meet. A gram kind outside `GRAM_KINDS`
raises when the **request is constructed**, before any authorization runs, so
there is no spelling of `3gram` that reaches a filename.

## 5. Authorization flow

```text
build_authorization  →  authorize_job_size  →  resolve route by LABEL
                     →  authorize_resource  →  first socket
```

Every refusal above the last line costs **zero network calls**, asserted against
the fake transport's own request log rather than a mock's call count — a refusal
one line too late would still fail.

**The route is resolved by label, not by `access[0]`.** GDELT carries two
profiles and the first is the deferred DOC API. The allowlist this collector
passes down is `{data.gdeltproject.org}` and nothing else: the source's own other
host is unreachable from here.

## 6. Job-size enforcement

`context.authorize_job_size(request.file_count)`, once for the whole request.

**Once, not per file.** Per-file would let a nine-file request through as nine
one-file successes. **And refused whole, never split** — silently turning nine
files into two permitted jobs would be the collector granting itself a ceiling
the review did not.

The string `max_files_per_job` **does not appear** in the collector's source, and
a test asserts that: the number lives in governance and the collector has no
constant of its own that could drift from it.

## 7. Operational bounds

| Bound | Default | Catches |
|---|---|---|
| `max_compressed_bytes` | 32 MiB | an unexpectedly enormous file |
| `max_decompressed_bytes` | 512 MiB | **amplification** the compressed ceiling cannot see |
| `max_line_bytes` | 4 KiB | a file with **no newline**, which would grow the buffer until the worker died while every other bound read as satisfied |
| `max_rows_scanned` | 20,000,000 | a runaway scan |
| `max_records` | 5,000 | a runaway persist |

All labelled `INTERNAL_SAFETY_POLICY`, on the dataclass and in every record's
provenance. **None is a quota anybody published.** A bound with a value below 1
is refused, and a decompressed ceiling below the compressed one is refused
because gzip does not shrink data on the way out.

## 8. Gzip handling

`zlib.decompressobj(31)` — gzip framing, not raw deflate — so a body that is not
gzip fails immediately rather than producing plausible rubbish. That is what
stops an HTML error page arriving with HTTP 200 from being read as an ngram file.

A stream ending before its trailer is a **truncated download**, reported as such
and contributing nothing: the rows already read are not a complete file. Valid
framing over nothing is a real, empty file and not a fault.

## 9. The strict row parser

Exactly four tab-separated fields. **No column shifting, no concatenation, no
guessing.** A five-field row is not a row with a longer ngram.

**A malformed row is fatal for its file**, which contributes nothing. The
alternative — skip and continue — was rejected: the contract is documented
first-party and observed, so a deviation means the contract changed or the file
is not the one requested, and both need a person. That is the stance
`world_bank._parse` already takes towards an unexpected envelope.

**Our own ceilings are the deliberate exception.** Hitting `max_records` or
`max_rows_scanned` truncates, **keeps** what was accepted, and records which
bound stopped it. A source-contract violation discards; an operational ceiling
truncates and says so.

Strict UTF-8, never `errors="replace"`: a replacement character would become part
of an ngram's identity and fingerprint, indistinguishable from a term GDELT
published.

## 10. `DATE` semantics

The bucket label, **verbatim**, with `bucket_resolution_minutes: 15` and
`bucket_timezone: null` beside it and a note saying why.

**`observed_at` is `NULL`.** It is a `TIMESTAMPTZ`, so writing anything means
naming a zone, and GDELT documents none — that is **H-29**. Every candidate value
would be an assumption stored as a fact, in the column a reader trusts most.

Preserving the label makes answering H-29 later a **re-derivation over records
already held**, not a re-collection. The cheap fix stays cheap.

Downstream must read `observed_at IS NULL` as *this project has not established
an event time*, not as *none exists*.

## 11. `LANG` semantics

The CLD2 human-readable **name**, verbatim, in `payload.lang` and in
`provenance.source_language_label` with
`language_representation: "SOURCE_NATIVE_CLD2_NAME"`.

**Never geography.** Spanish is not Spain; the row says nothing about where. No
`geography` key exists in the payload or the provenance and a test asserts its
absence.

**`content_language` stays `NULL`.** That column is read as a code, this project's
canonical form is a BCP-47 tag, and no published mapping from CLD2 names to tags
was found (**H-30**). A name sitting there would be a guess wearing the clothes
of a fact. This is the pattern `CanonicalGeography.unclassified` already sets:
the canonical slot stays empty, the source value is preserved where it is
identity-bearing.

## 12. `NGRAM` semantics

The term, verbatim. **Not a theme, not an entity, not a topic, not a keyword
intent.** No classification is applied and no model is consulted — asserted by
walking the module's imports rather than by grepping its prose, because the
docstring says "does not embed" and a substring scan would fail on it.

## 13. `COUNT` semantics

An arbitrary-precision integer, stored as a canonical decimal **string** for the
reason the World Bank value is one: the fingerprint is computed in Python and the
payload re-read from `JSONB`, and the two must agree byte for byte about a record
nobody changed. `float(` does not appear in the collector.

It is not a score, a strength, a popularity or a signal. `9007199254740993`
survives exactly — a float round-trip would have returned `...92`, and a fixture
carries that number so the test would see it.

## 14. Local filtering

Three filters — exact languages, exact ngrams, a lexical prefix — applied **after
parsing**.

**Filtering decides which rows are persisted and changes nothing a stored
observation claims.** A test asserts that the same row yields a byte-identical
payload, fingerprint and record id whether it arrived through a filter or not.

Every record carries `local_filter` with `applied_by: "collector"`, so nobody can
mistake our narrowing for the source's. The job reports `rows_scanned` alongside
`rows_matched` for the same reason: the real acquisition scanned **223,342** rows
and kept **2**, and reporting only "2" would describe a file that does not exist.

## 15. RawRecord semantics

One record is **one row**, not one file. The real file held 223,342 observations
that revise independently; storing the blob would mean one changed count
invalidated all of them.

## 16. Identity and fingerprinting

```text
key    gdelt|web-ngrams/1gram|20260830091500|ENGLISH|climate
hash   sha256 over the canonical payload, which includes COUNT
id     uuid5(namespace, workspace | key | hash)
```

`COUNT` is content, not identity — which is what makes a corrected count a
*revision*. The resource is in the key, so a term in both files is two
observations rather than a collision (§26 forbids counting spaces in the term).
No clock is in any of the three.

### 16.1 The key separator is escaped, not forbidden — see §31

## 17. Rights basis

`DIRECT_GRANT` on every descriptor, **licence absent**, both built from the
authorized dataset entry and never from anything a caller says. No licence string
is hard-coded in the collector and a test greps for the four fabrications
ADR-018 names.

## 18. Attribution

Rendered from the obligation review 3 recorded. **The collector has no parameter
for it**, so there is nothing to pass, and rendering fails closed. The notice does
not appear in the collector's source — asserted on the rendered sentence rather
than on the domain, because the domain appears in comments naming the host this
collector may *not* reach.

## 19. Retention

`collected_at + 30 days`, governance-resolved, `retention_basis: "baseline"`.
`build_raw_record` has no expiry parameter.

## 20. Personal-data handling

No new field and **no detection**. A lexical ngram may equal a person's name; the
collector does not look, does not resolve, and does not attach an article. Such a
record holds a name, one number, and no link to anything. Whether that is
personal data in the regulatory sense is **H-12**, deferred project-wide.

## 21. Persistence and transactions

| | |
|---|---|
| per file | **atomic** — all accepted rows or none |
| per job | one transaction over the files that completed |
| across files | **not** all-or-nothing, and it does not claim to be |

§33 is explicit that claiming atomicity across eight independent downloads would
be claiming something the architecture does not provide. A failed file is
reported in `files_failed` while the others persist.

## 22. Retry, pacing, cancellation

Retried: timeout, connection failure, 429, 5xx — bounded at three attempts.
**Never retried:** a 404, invalid gzip, a malformed row, an authorization refusal.

**A 404 means the requested bucket is unavailable.** There is no discovery
crawler and no walk to adjacent dates: H-31 leaves the directory's historical
extent unestablished, and a collector that hunted for a file that exists would be
reporting the hunt.

Pacing is two seconds between downloads, 24 requests per job,
`INTERNAL_SAFETY_POLICY`. **The DOC API's 429 is not carried across** — §35 is
explicit that they are different routes.

Cancellation is checked before each file and the honesty is stated in the
docstring: an in-flight download may finish within its own timeout; what is
guaranteed is that no new file starts.

## 23. Celery and orchestration

`acquire.collect.gdelt_web_ngram`, on the **existing** acquisition queue. A
separate task name rather than a `source_id` parameter, because the two carry
different request vocabularies and one task taking a union of both would validate
neither.

**No authorization travels in the payload.** The job loads the registry, builds
the authorization and checks the operational switch at execution time — a test
smuggles `authorization` and `max_files_per_job` into a payload and confirms they
shortcut nothing.

The orchestrator needed **no change**: `acquisition_block` derives from
`implemented_collectors`, so registering the collector propagated on its own.

## 24. Fake tests

**105 tests** in `test_gdelt_web_ngram_collector.py` plus 29 in
`test_gdelt_web_ngram_job.py`, all against fixture files, none touching GDELT.
The fixtures cover Unicode, multiple languages, a zero count, a count beyond
float precision, and twelve malformed shapes.

The fixture module says in its first paragraph that these are **fixtures, not
captured responses** — the distinction Mission 1.9.1 refused to blur when it
would not fabricate a `TimelineTone` envelope. Synthetic data is permitted here
precisely because the contract is documented and observed.

The streaming assertions are made against a transport that genuinely yields
chunks. The strongest of them is the amplification test: a 2 MB expansion aborted
at a 50 KB ceiling, which **can only pass if decompression is incremental**.

## 25. Live smoke

Opt-in behind `SROS_ENABLE_GDELT_WEB_NGRAM_SMOKE_TESTS=1`, absent from CI, with
the bucket named explicitly by the operator. One bucket, one resource, one
filter, **nothing persisted**, no crawl.

**It failed on first contact, and §31 is what it found.**

## 26. Controlled real acquisition

```text
one file · 20260830091500.1gram.txt.gz · ENGLISH · {climate, weather} · cap 10
```

```json
{"persisted": {"new": 2, "unchanged": 0, "revised": 0},
 "requests_made": 1, "files_requested": 1, "files_processed": 1,
 "rows_scanned": 223342, "rows_matched": 2, "succeeded": true}
```

GDELT was enabled first through `sros-source enable` — never direct SQL.

| | before | after |
|---|---|---|
| eligible | yes | yes |
| resource-ready | yes | yes |
| implemented | **no** | **yes** |
| enabled | no | **yes** |

Every §53 fact verified against the database: `source_id`, collector version,
resource, `DIRECT_GRANT` with `licence: null`, the exact DATE label, the exact
LANG label, no geography anywhere, the exact ngram, the exact integer count,
`observed_at NULL`, `content_language NULL`, attribution present, 30-day
retention, complete provenance, correct workspace and session.

## 27. Repeat-acquisition idempotency

The identical request, run again: **`0 new, 2 unchanged`**, two rows in the
table. At-least-once delivery is safe. This does not claim exactly-once, and the
second run really did re-download and re-scan all 223,342 rows.

## 28. Tenant isolation

Two disposable workspaces. A workspace cannot read another's records with no
`WHERE` clause; a write naming another tenant raises
`InsufficientPrivilege` from the policy's `WITH CHECK`; a query with no tenant
filter returns only this tenant's rows.

## 29. World Bank regression

Snapshotted before anything changed and re-checked after the full suite **and**
the real acquisition. Every row serialised whole — ids, hashes, payloads,
timestamps, session links, provenance — and compared.

| | before | after |
|---|---|---|
| World Bank raw | 6 | 6 — **byte-for-byte identical** |
| World Bank normalized | 6 | 6 — **byte-for-byte identical** |

The `observation_key` change (§31) is a no-op on every World Bank part, which is
why no committed key moved.

## 30. CI

| | |
|---|---|
| full suite | **1,111 tests + 233 subtests across 6 packages**, green |
| new | 105 collector + 29 job + 3 worker tests |
| GDELT network traffic in CI | **zero** — the live suite is opt-in |
| validators | all five green |
| generated documents | all four in sync |
| ruff, ruff format, mypy strict, contract `--check` | clean |
| post-suite | 20 tenant and 14 global tables unchanged |

## 31. Issues found

### 31.1 The key separator, found by the live smoke test

105 fixture tests passed. The first real file failed:

```text
INVALID_RESPONSE: a row's NGRAM contains the observation-key separator '|'
```

`observation_key` joins with `|` and **refused** a part containing one — a rule
written in Mission 1.5, when every part was an identifier, a country code or a
year. **News text contains pipes**, so GDELT publishes terms that do, and the
parser was discarding an entire 223,342-row file of legitimate observations
because of our own key format.

**No fixture caught it and none was going to**: the fixtures were written by
someone who did not expect a pipe in a word, which is the same someone who wrote
the rule.

Three fixes were rejected before the fourth:

| Considered | Rejected because |
|---|---|
| skip such rows | the system silently dropping real data to protect an internal format |
| move the separator | **any printable character can appear in a term** |
| hash the parts | removes the readability the key exists for |
| **escape the separator** | keeps the guarantee without deciding what a source may say |

`\\` → `\\\\`, then `|` → `\\|`. Every part written before the change contains
neither character, so no committed key moved — asserted rather than assumed.

### 31.2 The access route, found by writing a persistence assertion

`build_raw_record` read `context.access[0]`, correct while one source had one
profile. **GDELT's first profile is the deferred DOC API**, so every WEB-NGRAM
record would have recorded `PUBLIC_API` on `api.gdeltproject.org` for a file
downloaded over `DATASET_DOWNLOAD` from somewhere else — a false provenance fact
about the one route this work deliberately avoided. The access label is now
required rather than inferred.

### 31.3 A retry could have duplicated a file's rows

`_read_file` yielded observations. A mid-stream failure is retryable, and the
caller had already built drafts from the rows read before it — so the retry would
re-read the file and deliver them again. **Duplicated observations produced by
the mechanism meant to make the fetch reliable.** It returns a list now, so a
retried attempt discards everything the failed one produced.

Found by the fake transport raising eagerly where the real one raises lazily,
which also revealed that the `download` call sat outside the `try` and escaped
the retry loop entirely.

### 31.4 Two tests were relying on the deployment

`test_a_job_refuses_a_source_whose_collector_is_not_enabled` and its neighbour
passed for as long as nobody had run `sros-source enable gdelt`, and went red the
moment §43 did. They now set the state they need through a `disabled_gdelt`
fixture that restores it. `testing-strategy.md` §10, walked into again.

## 32. Remaining blockers

**Unchanged:** D-03, D-08, D-10, D-12, H-12, H-13, H-22 to H-26,
PROFILE-NOT-CALIBRATED.

**H-27 — open.** No DOC API timeline envelope has ever been observed and none was
fabricated. Nothing waits on it: the WEB-NGRAM route is the one that works.

**H-29 — open, and now load-bearing.** The `DATE` timezone is unestablished, so
`observed_at` is `NULL` on every GDELT record. Any temporal analysis of these
observations has to answer it first; the bucket label is preserved so the answer
costs no re-collection.

**H-30 — open.** No CLD2-name-to-language-tag mapping, so `content_language` is
`NULL`. A normalizer will have to decide what a canonical language is here.

**H-31 — open.** The directory's historical extent is undocumented, so there is
no backfill and no crawl.

**Eurostat** is still eligible with no authorised resource and no collector.

## 33. Next-mission readiness

**Normalizing GDELT is the next mission, and it is not trivial.** The collector's
job was to preserve; a normalizer's job is to decide what a preserved thing
structurally represents, and three of the four fields have an open question
attached:

- **`DATE`** cannot become a `CanonicalPeriod` with a timezone until H-29 is
  answered. A normalizer that picked UTC would put the assumption exactly where
  `normalized-record-v1.md` says it must not go.
- **`LANG`** cannot become a language tag until H-30 is answered. The
  `unclassified` pattern exists for geography and there is no language equivalent
  yet.
- **`COUNT`** is a `NumericObservation` with **no `unit_of_measure`** — it is a
  frequency, not a magnitude — and `normalized-record-v1.md` requires a unit the
  source publishes or `NOT_PUBLISHED`. That is answerable, and it should be
  answered deliberately rather than in passing.
- **`NGRAM`** has no canonical slot at all. `RecordKind.NUMERIC_OBSERVATION`
  identifies by metric, period and geography; a term is none of those, and there
  is no geography. **This is a real gap in the normalized model**, and it should
  get a gap analysis before a schema change, the way Mission 1.7 §47 required.

---

## Explicit answers

| Question | Answer |
|---|---|
| Is the GDELT WEB-NGRAM collector implemented? | **Yes** |
| What collector version? | **`gdelt-web-ngram@1.0.0`** |
| Is GDELT still eligible? | **Yes**, unchanged. No gate was relaxed |
| Is it resource-ready? | **Yes** — `web-ngrams/1gram` and `web-ngrams/2gram` |
| Is it implemented? | **Yes**, added to `IMPLEMENTED_COLLECTORS` as the last step |
| Is it enabled? | **Yes, in this deployment**, through `sros-source enable`. The catalog record still enables nothing |
| Are both 1gram and 2gram supported? | **Yes**, and only those |
| Can any other GDELT dataset be downloaded? | **No.** An unreviewed gram kind fails when the request is constructed; every other product has no entry, no family and no path |
| Can a job request more than 8 files? | **No.** Refused whole, before any socket, and never split |
| Can a caller supply arbitrary paths or URLs? | **No.** No field exists for one, on the request or in the task payload |
| Is the download streaming and bounded? | **Yes** — chunked, with compressed, decompressed and line ceilings |
| Are gzip amplification limits enforced? | **Yes.** A 2 MB expansion aborts at a 50 KB ceiling, which only an incremental decompressor can do |
| What is one RawRecord? | **One row**: one gram kind, one bucket, one language, one term, one count |
| What is its observation identity? | `gdelt\|web-ngrams/1gram\|20260830091500\|ENGLISH\|climate` — source-native, with `\|` escaped inside parts |
| Is DATE treated as UTC? | **No.** No timezone is attached anywhere. H-29 is open and `observed_at` is `NULL` |
| Is LANG ever treated as geography? | **No**, and a test asserts no geography key exists |
| Is NGRAM treated as a topic or theme? | **No.** It is `lexical_ngram` and nothing classified it |
| Is COUNT treated as a signal? | **No.** It is `source_measured_frequency`, and `nlp.signals` is empty |
| Is DIRECT_GRANT preserved with no licence? | **Yes**, on every record, from the authorized dataset entry |
| Is attribution preserved? | **Yes**, rendered from the obligation and failing closed |
| Is retention governance-derived? | **Yes** — 30 days, `basis: baseline`, no collector parameter |
| Is duplicate delivery safe? | **Yes**, and it is not exactly-once. The second run wrote nothing |
| Did live smoke succeed? | **Yes — after it found a real defect on its first run.** See §31.1 |
| Did controlled acquisition succeed? | **Yes.** 1 file, 223,342 rows scanned, 2 persisted |
| How many real GDELT RawRecords exist? | **2** |
| Did repeat acquisition create duplicates? | **No.** `0 new, 2 unchanged` |
| Did World Bank data survive byte-for-byte? | **Yes.** 6 raw and 6 normalized, identical |
| Were GDELT records normalized? | **No.** Zero, and no normalizer exists |
| Were any signals created? | **No.** Zero |
| Were embeddings generated? | **No.** Zero. No model, no Qdrant, no provider call |
| Were Claims or Evidence generated? | **No.** Zero |
| Was scoring performed? | **No.** Still blocked on D-03 |
| Is the next mission safe to normalize GDELT? | **Yes to start it, no to finish it blindly.** Three of four fields carry an open question and `NGRAM` has no canonical slot at all — see §33 |

---

## What was hard, and what I would flag to a reviewer

**The live smoke test earned its entire cost on its first run.** 105 fixture
tests were green and the first real file was rejected outright, by a rule written
a mission before GDELT existed. The lesson is not that fixtures are weak — they
cover truncated gzip and amplification, which no live test can produce on demand
— it is narrower: **a fixture proves the parser handles what its author imagined.**

**The fix's shape mattered more than the fix.** Skipping the offending rows would
have been the system quietly discarding real observations to protect an internal
format, and it would have passed every test.

**Two of the four defects came from a source having a second access profile.**
`access[0]` was correct for as long as one collector existed, in two different
places. Neither was reachable before this mission and both are now impossible.

**The honest limits are in the report rather than smoothed over**: cancellation
does not interrupt an in-flight request, persistence is not atomic across files,
and `observed_at` is `NULL` because nobody has established a timezone — which
will make the next mission harder and is the correct state to hand it.

**What I did not do:** no normalizer, no signal, no embedding, no claim, no
evidence, no score, no second source collector, no DOC API work, and no crawl for
data nobody asked for.
