# Mission 1.9.2 — GDELT has a concrete authorized resource, and no collector

**Sprint 1 / Mission 1.9.2** · 2026-08-30
**Status:** **Complete.** GDELT review 3 authorises two WEB-NGRAM resources on a
reviewed `DATASET_DOWNLOAD` route. **No collector was written, no GDELT record
was persisted, and nothing was normalized, embedded, scored or turned into a
signal.** H-27 stays open; the DOC API route is deferred rather than withdrawn.

---

## 1. Why the DOC API path was deprioritized

Not because it was hard. Because its operator says it is under strain, and
because two independent networks cannot reach it.

| | |
|---|---|
| `api.gdeltproject.org` | `ConnectTimeout` from the agent environment **and** from the operator's own Windows machine |
| control (`api.worldbank.org`) | HTTP 200 from the same client, moments apart |
| GDELT's own words, retrieved 2026-08-30 | "our existing legacy search infrastructure is struggling to handle the ever-growing volume of searches" while "the transition of our search and API infrastructure to Spanner is still underway" |

**H-27 was never a technical blocker in the ordinary sense.** It is the absence
of two saved JSON responses, and Mission 1.9.1 refused to fabricate them. What
Mission 1.9.2 adds is that continuing to press for them is pressing against
infrastructure the operator describes as struggling — so the route is
**deferred**, not abandoned and not retried.

**Deferred means the profile stays**, with its endpoint, on an approved review,
with no authorised resource on it. §24 asked for exactly that, and the reason is
worth stating: deleting the profile, the capture script or the response-contract
document would make a later un-deferral look like a new approval. The Spanner
migration will finish.

## 2. GDELT re-review methodology

`source-review-guide.md`, in order, producing **review version 3**. Reviews 1 and
2 are byte-identical and remain in the history — §3 forbids rewriting them, and
`test_review_three_is_current_and_the_earlier_two_are_intact` asserts it.

**What made a new version necessary rather than a configuration edit:**

| Fact | Reviews 1–2 | Review 3 |
|---|---|---|
| capability | news events, themes, entity mentions, tone, timestamps, geography | **plus `term-frequency`** |
| access route | `PUBLIC_API` on `api.gdeltproject.org` | **plus `DATASET_DOWNLOAD` on `data.gdeltproject.org/gdeltv3/web/ngrams/`** |
| verdict | `APPROVED_WITH_CONDITIONS` | **unchanged** |
| rights basis | `DIRECT_GRANT`, no licence | **unchanged** |
| every per-activity assessment | — | **unchanged** |

A rights grant is not an access authorisation. The grant carried over untouched
and the capability and route did not, and recording those is substantive review
work — the same distinction Mission 1.9 drew for `ArtList`.

Full reasoning: [`gdelt-web-ngram-review-v1.md`](../data/gdelt-web-ngram-review-v1.md).

## 3. First-party WEB-NGRAM evidence

Four documents, all the operator's own, all recorded on review 3 with absolute
URLs. An evidence record whose document cannot be re-opened cannot be re-checked.

| Document | Establishes |
|---|---|
| `gdeltproject.org/about.html` — Terms of Use | the grant, and the citation obligation |
| `blog.gdeltproject.org/announcing-the-web-news-ngram-datasets-web-ngram/` | the file path, the four columns with GDELT's own definitions, the 15-minute cadence, 142 languages from 2019-01-01 |
| `gdeltproject.org/data.html` | WEB-NGRAM is a current product — "Global online news ngrams in **152** languages" |
| `blog.gdeltproject.org/using-the-new-web-ngrams-dataset-to-find-relevant-coverage/` | the legacy-search statement — **and one correction, §3.2** |

### 3.1 The announcement confirms the observed contract, field for field

Mission 1.9.1 read the contract off a file. This mission read it off the
operator's documentation. They agree:

| Column | GDELT's own words |
|---|---|
| `DATE` | "The date in YYYYMMDDHHMMSS format." |
| `LANG` | "The human-readable language name as output by CLD2." |
| `NGRAM` | "The word or phrase." |
| `COUNT` | "The number of times the word/phrase was mentioned in articles of that language published in that given 15 minute interval." |

**152 languages now against 142 at release.** Both figures are recorded with
their dates rather than one being chosen — the larger would assert currency this
review did not verify, the smaller a limit that no longer holds.

### 3.2 The correction

Mission 1.9.1 quoted GDELT asking researchers to "switch their searches to use
these ngram files instead of the search APIs" and read it as first-party support
for the WEB-NGRAM path.

**It is not.** Read in place, the sentence is in the post announcing the
**quadgram** dataset — per-minute files on `storage.googleapis.com` under
`gdeltv5/weblegacy/ngrams/`, whose ngrams file keys quadgram counts to a
per-document `DOCID` and whose companion `toc.json.gz` carries `title`, `img` and
`url`. "These ngram files" means those, and **review 3 rejects that dataset**.

What survives is the other half — GDELT describing its own legacy search
infrastructure as struggling — and that half is a statement about infrastructure,
not a recommendation about datasets. It is why §1 defers the DOC API and it
needed no support from the recommendation.

**The case for WEB-NGRAM rests on its own documentation and its own observed
structure.** Recorded in the review notes, in the response contract §10.2 and
here, rather than quietly dropped.

## 4. Access profile

| | |
|---|---|
| label | `gdelt-web-ngram-files` |
| method | `DATASET_DOWNLOAD` |
| host | `data.gdeltproject.org` |
| credentials | none documented, none referenced |
| rate limit | **unknown**, and not invented |

It **replaces** `gdelt-bulk-files`. That placeholder named the bulk route in
general and deliberately carried no `endpoint_url`, so it authorised no host at
all; Mission 1.9 asserted the absence "so that adding one is a decision somebody
takes rather than a line somebody copies". Review 3 is that decision, and what it
authorises is narrower than the placeholder's name — so the profile is renamed
rather than filled in, and nothing is left for a later mission to widen.

`gdelt-doc-api` keeps its own endpoint and the ngram route borrows nothing from
it.

## 5. Endpoint and path scope

```text
https://data.gdeltproject.org/gdeltv3/web/ngrams/
```

The directory, not the site root. A root would have authorised every bulk product
GDELT publishes — including Web News NGrams 3.0, **one directory across**, which
this review rejects.

**The boundary is fail-closed by construction, and needed no new rule.**
`HttpxTransport` composes `base_url + path.lstrip("/")`, and `HttpRequest`
refuses `..` and anything that looks like a URL:

| Attempt | Result |
|---|---|
| `../webngrams/x.gz` | **refused** — `path must not traverse` |
| `https://storage.googleapis.com/...` | **refused** — `path is a path, not a URL` |
| `/gdeltv3/webngrams/x.gz` | flattened **into** the authorised directory |

Three hosts are named in §5 of the brief as things not to authorise. None is:
`api.gdeltproject.org` is on its own profile and reaches nothing new,
`storage.googleapis.com` is on no profile at all, and the derived host set is
asserted as an **equality** so a third appearing fails the suite.

## 6. Direct-grant rights basis

`DIRECT_GRANT`, unchanged, **no licence key on either resource**.

> all datasets released by the GDELT Project are available for unlimited and
> unrestricted use for any academic, commercial, or governmental use of any kind
> without fee

The WEB-NGRAM files are datasets GDELT releases, so the grant reaches them
without argument. **H-28 needed nothing new and stays closed**, which was the
point of building the rights-basis model in Mission 1.9.1 before there was a
resource to apply it to.

**No licence identifier was invented.** `"OTHER"`, `"GDELT Terms Licence"`,
`"NONE"` and `"N/A"` are four different lies and the model refuses all of them
under a direct grant. `test_no_licence_identifier_was_invented` asserts nobody
reached for one anyway.

The three `NAMED_LICENCE` sources are untouched, and a direct grant still cannot
satisfy a licence allowlist.

## 7. The observed dataset contract

```text
DATE             LANG        NGRAM      COUNT
20260830091500   ALBANIAN    dhe        676
20260830091500   ALBANIAN    do të      104     (2gram)
```

Tab-delimited, gzipped, four columns, **no header row**. Two files every fifteen
minutes. **No title, no URL, no image, no sentence, no document id, no position.**

Not "we filter publisher content out" — there is none in the file. That is a
stronger position than any filter, because there is nothing to fail to remove.

## 8. Minimisation gap analysis

Written **before** the profile changed, as §10 requires:
[`gdelt-web-ngram-minimisation-gap-analysis-v1.md`](../data/gdelt-web-ngram-minimisation-gap-analysis-v1.md).

| Field | Category | Status |
|---|---|---|
| `DATE` | `observation_period` | **reused** |
| `LANG` | `content_language` | **added** |
| `NGRAM` | `lexical_ngram` | **added** |
| `COUNT` | `source_measured_frequency` | **added** |

**Nothing was mapped approximately.** Each addition was reached by first showing
that every existing candidate asserts something the source did not do:

| Rejected candidate | What it would have asserted |
|---|---|
| `geography` for `LANG` | a place, where there is a language |
| `theme_identifier` for `NGRAM` | a classification no classifier made |
| `entity_mention` for `NGRAM` | a resolution no resolver ran |
| `observation_value` for `COUNT` | a measurement whose owner is unstated |

The seven DOC API categories are **kept**, because that route is deferred rather
than withdrawn.

## 9. `NGRAM` semantics

A term of one or two words, as the source emitted it. Carries **no
classification, no topic assignment and no article of origin**. A collector must
not infer a theme from it.

The name says `ngram` rather than `term` or `keyword` on purpose: it is the unit
GDELT publishes, so a reader who meets it in a provenance record can go and find
the file it came from.

## 10. `COUNT` semantics

An occurrence count **GDELT computed over its own corpus**. It is not the number
of files or rows our job fetched, not the size of a result set, not a popularity
score, and **not a signal**.

The category name has to keep saying whose number it is, and the reason is not
hypothetical: Mission 1.9 rejected `ArtList` partly because counting the articles
it returned would have measured `MAXRECORDS` — *our request* — and presented it
as a measurement of the world. `observation_value` does not guard against that.
`source_measured_frequency` does.

**This is the first source-published number in the system that looks like a trend
measure, and D-03 is still open.**

On this route the objection cannot arise at all: **no query is issued.** The file
is a published aggregate, so our request cannot influence the number — which is
the same fact that gives the observation a source-native identity,
`(DATE, LANG, NGRAM)`, rather than one containing our own query string.

## 11. Language semantics

`LANG` is a **CLD2 human-readable language name** — `ALBANIAN`, mostly uppercase,
a few titlecase, some with underscores.

**It is never geography.** Spanish is not Spain, Arabic is not one country, and
the row says nothing about where anything happened. The registry model already
keeps countries and languages apart; `content_language` is a real field on both
`RawRecordDraft` and `NormalizedRecordDraft`, and the category is named after it
so the authorisation and the destination line up.

**No language code is guessed.** The project's canonical form is a BCP-47 tag and
GDELT publishes no mapping from CLD2 names to tags, so the source label is
preserved verbatim — the same treatment `CanonicalGeography.unclassified` gives a
code nobody can map. Whether such a mapping exists is **H-30**.

## 12. Time-bucket semantics

The value is the **15-minute bucket label**, `YYYYMMDDHHMMSS`, identical to the
filename. The bucket's resolution is 15 minutes and the label marks its start. It
is **not** an article's publication time and not our fetch time.

**The timezone is not documented, and this review does not assert it.** Neither
the announcement nor the data page states one. Mission 1.9.1 recorded UTC; that
was not established, and §10.1 of the response contract now says so. The
collector must preserve the source label verbatim, which makes answering **H-29**
later a re-derivation over records already held rather than a re-collection.

This is a place where the mission brief and the evidence disagreed. §14 states
the bucket is UTC; the operator's documentation does not say so anywhere. The
brief's structure is honoured — bucket start, resolution, source label all
defined — and the one field that could not be established is carried as an open
question instead of being filled in.

## 13. Personal-data implications

§19 asks the question the right way round: **structure against contents.**

**Structurally there is none.** Four columns, no name field, no author, no handle,
no identifier, no profile. Nothing in a row is *about* a person.

**A lexical term can be a person's name.** `MACRON` is a valid `1gram`;
`Emmanuel Macron` is a valid `2gram`. A collector cannot prevent it by asking
differently — the file arrives whole. Such a row carries a name, one number, and
no link to any article, author or document.

**The classification does not change.** GDELT stays `PSEUDONYMOUS` with
`contains_user_identifiers` true. Downgrading it to `NONE_EXPECTED` because *one*
dataset has no identifier column would be reading a dataset's structure as a
statement about the source, in the permissive direction.

**Whether that is personal data in the regulatory sense is jurisdiction**, which
is **H-12** and deferred project-wide since Mission 1.3. This mission records the
exposure precisely rather than resolving it, so whoever resolves H-12 can see
what it applies to. `personal_data` and `user_identifier` stay excluded.

## 14. Acquisition bounds

```json
"acquisition_bounds": { "max_files_per_job": 8, "basis": "..." }
```

96 buckets a day, two files each, since 2019, and **nothing in the terms limits
how much of it is taken.** Eight files is two hours of one ngram kind or one hour
of both — a bounded look at a moving window, far short of a corpus.

Three properties, each of them the point:

- **the ceiling belongs to the review.** A collector choosing its own bound would
  be setting its own permissions;
- **a bound with no stated basis is refused at load time**, because a number
  nobody can re-check survives every later review by looking deliberate;
- **`None` means no ceiling was reviewed, not that any size is fine.** Every
  earlier source is in that state, and spelling it `unlimited` would turn an
  unasked question into an answer.

`context.authorize_job_size(n)` is how a collector asks, and a job that does not
state its size is refused.

### 14.1 Two bounds considered and not written

**A time window** constrains nothing `max_files_per_job` does not, and the job it
would restrict hardest — a few files sampled across two years — is the *cheaper*
one for the source.

**A language allowlist** was rejected on a fact from the observed contract:
**each file spans every language GDELT monitors.** `LANG` is a data column, not a
partition, so a job cannot request fewer languages than a file contains and
language is not a dimension of the request at all.

That is §16's distinction, and this is what it resolves to:

| | |
|---|---|
| authorized maximum scope | every language GDELT publishes — the grant restricts none |
| operational request scope | not expressible in languages: the **file** is the unit |
| retention scope | a research decision for the collector mission, bounded by minimisation |

Encoding a language choice here would have presented a product decision as a term
of the grant.

## 15. `1gram` / `2gram` decision

**Both approved, as separate resources.** §20 permitted authorising only `1gram`
if a material governance difference existed. None does, and the finding rests on
structure rather than on word count:

**Neither file carries a position or a document identifier.** NGrams 3.0 has
`pos` and `url`; the quadgram file has `DOCID`; WEB-NGRAM has neither. A phrase
here cannot be attached to the article it came from, cannot be located within it,
and is not ordered relative to anything — it is a frequency in an unordered table
aggregated over an entire language's coverage in fifteen minutes. **That is
further from an excerpt than a seven-word snippet with a URL, not closer to one.**

Mission 1.9.1's PR left this open as "a judgment a reviewer should make
explicitly rather than inherit". This mission is that review and it made it.

**Two entries rather than one family**, so withdrawing `2gram` later is a
deletion rather than a re-derivation. **No generalisation to `3gram` or beyond**:
the family allowlist refuses one, and at some length a phrase does become an
excerpt.

## 16. Excluded GDELT datasets

| Dataset | Why | Refused by |
|---|---|---|
| **Web News NGrams 3.0** | `pre`/`post` snippets of ~7 words **plus the article `url`** | no entry; excluded family |
| **quadgram + TOC** | `title`, `img`, `url`, and counts keyed to a per-document `DOCID` | no entry; excluded family; **and a host no review has assessed** |
| **DOC API `ArtList`** | publisher `title` and `socialimage` | no entry; excluded family |
| **DOC API timeline modes** | H-27 — never observed | no entry |
| any other bulk product | not assessed | no entry; family allowlist |
| a `3gram` or longer | not published here, not assessed | no entry; family allowlist |

Each is refused by **two independent mechanisms**: no enumerated entry to build a
descriptor from, and a family allowlist that refuses one built by hand anyway.

The four read-and-rejected families are named in `excluded_dataset_families` even
though the allowlist makes that redundant — **an empty exclusion list would say
nobody had looked.**

## 17. Attribution

Unchanged, and reused rather than restated. One condition, `gdelt-attribution`,
verified by `CAPABILITY: source-attribution-display` — the generic verifier
Mission 1.8 bound it to when it moved off `HUMAN_CONFIRMATION`, which no verifier
can ever clear.

Both elements are fixed strings the terms prescribe, so neither is supplied per
artefact:

```text
SOURCE_CREDIT   The GDELT Project
EXACT_NOTICE    Any use or redistribution of the data must include a citation to
                the GDELT Project and a link to this website
                (https://www.gdeltproject.org/).
```

The obligation is identical on both routes because the terms make no distinction
between them. **No attribution text was duplicated into any code.**

## 18. Retention

Governance-resolved project baseline: **30 days raw, 365 normalized**, no source
override. GDELT's terms address retention nowhere, and §17 is explicit that a
source limit must not be invented — silence means the baseline applies, which is
the baseline working rather than a gap.

**No RawRecords were created**, so nothing carries an expiry yet.

## 19. Resource authorization

Every §22 case, proved in `test_gdelt_web_ngram.py`:

| Case | Outcome |
|---|---|
| `web-ngrams/1gram`, built from its entry | **allowed** |
| `web-ngrams/2gram`, built from its entry | **allowed** |
| a family the review never assessed (`web-ngrams-3gram`) | refused |
| another source's family (`indicators`) | refused |
| no family stated | refused |
| Web News NGrams 3.0 | refused |
| the quadgram file and its TOC | refused |
| the DOC API `ArtList` mode | refused |
| `THIRD_PARTY` | refused |
| `UNKNOWN` origin | refused |
| **no rights basis** | refused |
| cross-source descriptor | refused |
| an unreviewed `resource_id` | **no entry to build a descriptor from** |

### 19.1 Two holes this mission found and closed

Both were reachable only by a hand-made descriptor — a collector builds one
*from* an authorised entry, which always carries these fields. They were fixed
anyway, on the argument the transport already makes: *a guard that only exists
further up is a guard a future caller can route around.*

**An unestablished rights basis passed.** It had been checked only inside the
licence-allowlist rule, so a descriptor with **no basis at all** was allowed for
every source whose scope enumerates no licences — Eurostat, FRED, and pointedly
**GDELT, the one source authorised by a direct grant rather than a licence**.
"Nothing established" read as approval on exactly the source where the basis is
the whole story. The rule is now unconditional, because every other rule answers
a question a particular review may or may not have asked and *what authorises
this at all* is not one of those.

**An unreviewed dataset family passed.** `require_dataset_family` refused a
resource that could not say what it is; it admitted one that said something
nobody had reviewed, because a family no reviewer had rejected was
indistinguishable from one a reviewer had approved. `allowed_dataset_families`
answers the other question. `None` on the other three sources — unchanged
behaviour.

Both were **observed failing before being fixed**, and the probe output is in the
mission's working notes.

## 20. Acquisition-readiness diagnostic

```text
source                 elig  rsrc  impl  enab  next step
eurostat               yes   no    no    no    authorise a concrete resource
fred                   yes   no    no    no    authorise a concrete resource
gdelt                  yes   yes   no    no    implement a collector
world-bank             yes   yes   yes   no    enable the collector in this deployment
```

`sros-source readiness`. **GDELT is exactly the state §23 predicted**: eligible
yes, resource-ready yes, implemented no, enabled no.

**`resource_ready` is the fact that did not exist.** Between Missions 1.7 and
1.9.1 GDELT was eligible with an empty `datasets` tuple — the gate said yes, the
resource layer refused everything, and "eligible" was the most specific word
available. It read as further along than it was. Eurostat is in that state today
and the diagnostic now says so out loud.

**Nothing is stored.** A persisted `resource_ready` would be a copy of a
derivation, which is the argument `source-registry-v1.md` §3 already makes for
eligibility being a view; a test asserts no migration defines such a column.

`resource_ready` is not `bool(datasets)`. It re-runs the gate against a descriptor
built from each entry, so an entry that is enumerated *and refused by its own
scope* surfaces as a gap in a diagnostic instead of on a first request.

**One incidental fix.** `sros-source show` had printed "COLLECTOR ENABLED: no. No
collector exists for any source" since Mission 1.4. That stopped being true when
Mission 1.5 built one, and the line had been saying it for four missions.

## 21. Registry safety

The post-suite comparison is by **content**, not row count, because
`UPDATE registry.sources SET collector_enabled = TRUE` moves no rows:

```text
database unchanged by the run, across 20 tenant tables
global tables unchanged by the run, across 14 tables;
12 appended to 1 append-only table(s)
```

The one growing table is `registry.source_condition_verifications`, which is
append-only by design — twelve verifications for twelve conditions across five
approving sources.

Review history, conditions, source states and operational switches are all
unchanged except for this mission's committed edits.

## 22. Tests and CI

**No new CI job.** The rules live inside gates that already run.

| | |
|---|---|
| new module | `test_gdelt_web_ngram.py` — **65 tests** across nine classes |
| full suite | **972 tests + 233 subtests across 6 packages**, green |
| zero-dependency suites | 337 tests across 5 packages |
| validators | all five green |
| generated documents | all four in sync under `--check` |
| ruff / ruff format / mypy strict | clean, 301 files, 114 source files |
| TypeScript conformance | 0 failures |

### 22.1 Eight passing tests went red, and none of them was wrong

Each was a **correct statement about a state review 3 deliberately left**:
the bulk profile had no endpoint, GDELT had no dataset entry, `datasets` was
empty. Every one was rewritten in place to assert the new truth and to carry a
docstring naming the old one and the decision that moved it — four were renamed,
because a name describing the old state is worse than no name.

Three more failed for a different reason and needed a different fix: the
capability probe baseline and three `test_compliance` control descriptors left
`rights_basis` unset, so the new unconditional rule refused them. Control cases
have to pass for the reason they are testing, so each now carries a basis with a
comment saying why.

One counted: `len(denial_reasons) == 2` was stale the moment a third rule ran,
while the behaviour it names — report every refusal, not the first — was working
exactly as before. It is now a property. That is `testing-strategy.md` §13's
fourth recurrence and it is recorded as §19.

### 22.2 A generated document had been stating something impossible

`source-review-results-v1.md` renders "N of 27 sources carry a review from X; M
of those are first reviews of a new candidate". `M` was counted across the
**whole catalog** rather than across this round, so Mission 1.8 rendered
**"4 of 27 … 10 of those"** and this mission, which re-reviewed a single source,
would have rendered **"1 of 27 … 10 of those"**.

Nobody had noticed, because 10-of-4 is only slightly wrong and 10-of-1 is
obviously wrong. The generator now intersects the two sets and says something
different when the intersection is empty. **A generated document exists to stop
drift and cannot do that while stating arithmetic nobody can believe** — this is
the same class of defect as the `sros-source show` line in §20, found the same
way: by changing something nearby and reading the output.

## 23. Existing-data survival

Snapshotted **before any change** and re-checked after the full suite. Every row
of both tables serialised whole — ids, hashes, payloads, timestamps, session
links, provenance — and hashed:

| Table | Before | After | Digest |
|---|---|---|---|
| `acquisition.raw_records` | 6, `world-bank` | 6, `world-bank` | `8cc3f165c71b612e…` **identical** |
| `acquisition.normalized_records` | 6, `world-bank` | 6, `world-bank` | `7df90e096c883f4b…` **identical** |

`nlp.signals` 0 · `nlp.embedding_provenance` 0 · `research.claims` 0 ·
`research.claim_revisions` 0 · `scoring.evidence` 0 — before and after.

**Byte-for-byte identical**, and the row lists compare equal as well as the
digests.

## 24. Remaining blockers

**Open and unchanged:** D-03, D-08, D-10, D-12, H-12, H-13, H-22 to H-26,
PROFILE-NOT-CALIBRATED.

**H-27 — open, reclassified.** No timeline envelope has ever been observed and
none was fabricated. Nothing now waits on it: it blocks the DOC API route, which
is deferred, rather than blocking a collector.

**H-28 — resolved**, both halves. The model in Mission 1.9.1 (ADR-018), the
entries here. The queue records it rather than deleting it.

**H-29, H-30, H-31 — new, and none blocks anything.** Is `DATE` UTC (nothing
first-party says); is there a CLD2-name-to-language-tag mapping (none found); how
far back does the publication directory reach (unstated). Each names what would
answer it, and each is survivable because the collector preserves source labels
verbatim — so answering them later is a re-derivation, not a re-collection.

**Eurostat has no authorised resource.** Collector-eligible since Mission 1.4
with `datasets` empty. That is the gate working, and the readiness diagnostic now
says it rather than leaving it to be discovered.

## 25. Collector readiness

**Yes, for WEB-NGRAM specifically**, and it is a smaller collector than the DOC
API one would have been: a gzipped tab-delimited file with four columns, no
pagination, no query construction and no envelope ambiguity.

What a collector mission would receive, already decided and none of it its own to
choose:

| | |
|---|---|
| route | `gdelt-web-ngram-files`, `data.gdeltproject.org/gdeltv3/web/ngrams/` |
| resources | `web-ngrams/1gram`, `web-ngrams/2gram` |
| fields | `observation_period`, `content_language`, `lexical_ngram`, `source_measured_frequency` |
| ceiling | 8 files per job |
| retention | 30 / 365, governance-resolved |
| attribution | the citation and link, from configuration |
| identity | `(DATE, LANG, NGRAM)` — source-native |

What it must **not** do: interpret `LANG` as geography, map it to a language
code, assert a timezone for `DATE`, treat `COUNT` as a signal, reach any other
host or dataset, or choose its own volume ceiling.

---

## Explicit answers

| Question | Answer |
|---|---|
| Does H-27 remain open? | **Yes.** No `TimelineTone` or `TimelineVolRaw` fixture exists and none was fabricated. It is reclassified as deferred, not closed |
| Is the DOC API still the recommended first collector path? | **No.** Deferred: unreachable from two environments, and its operator describes the infrastructure as struggling |
| Is WEB-NGRAM officially reviewed now? | **Yes** — GDELT review version 3, `mission-1.9.2`, with four first-party evidence records |
| Which WEB-NGRAM resources are approved? | **`web-ngrams/1gram` and `web-ngrams/2gram`**, as separate entries |
| What exact host/path is authorized? | **`https://data.gdeltproject.org/gdeltv3/web/ngrams/`** — the directory, not the site root, and the transport cannot compose a path out of it |
| Does the direct GDELT grant still apply? | **Yes**, unchanged. The terms cover "all datasets released by the GDELT Project" and these are |
| Was any licence invented? | **No.** `DIRECT_GRANT` with no licence key; the model refuses one, and none was attempted |
| How are DATE, LANG, NGRAM and COUNT represented? | `observation_period`, `content_language`, `lexical_ngram`, `source_measured_frequency` — one reuse and three additions, each reached by ruling out every existing candidate |
| Is LANG ever treated as geography? | **No**, and a test asserts it. Language is not geography |
| Is COUNT treated as a signal? | **No.** It is the source's own measurement over its own corpus, named so the sentence travels with the number. No signal exists |
| Are publisher snippets/URLs/headlines still refused? | **Yes.** `article_full_text` and `publisher_content` stay excluded, `third_party_denied` stays on, and the authorised file contains none of it to begin with |
| Are Web News NGrams 3.0 and the TOC dataset refused? | **Yes**, each by two independent mechanisms, and both were read and rejected rather than merely omitted |
| Are acquisition bounds defined? | **Yes** — 8 files per job, with a stated basis, refused at load time without one, and enforced through `authorize_job_size` |
| Does GDELT now have at least one concrete authorized resource? | **Yes, two.** It is the second source in the catalog to have any |
| Is GDELT still collector-eligible? | **Yes**, unchanged. No gate was relaxed to keep it there |
| Is GDELT implemented? | **No.** `IMPLEMENTED_COLLECTORS == {"world-bank"}`, and no `gdelt` module exists in the collection package |
| Is GDELT enabled? | **No.** `collector_enabled` is false |
| Were any GDELT research records persisted? | **No. Zero raw, zero normalized.** No file was fetched in this mission at all — the contract came from Mission 1.9.1's single capped inspection and from GDELT's documentation |
| Did World Bank data survive unchanged? | **Yes, byte-for-byte.** Six raw and six normalized, digests identical before and after |
| Is the next mission safe to implement the WEB-NGRAM collector? | **Yes.** The route, the resources, the fields, the ceiling, the retention and the attribution are all decided. What remains is engineering, and it is smaller than the DOC API collector would have been |

---

## What was hard, and what I would flag to a reviewer

**The best evidence in Mission 1.9.1 turned out to be about a different
dataset.** GDELT really does ask researchers to use ngram files instead of the
search APIs, and the sentence really is first-party — it just names the quadgram
dataset, which this review rejects for carrying `title`, `img`, `url` and a
per-document `DOCID`. Nothing forced me to re-read the post; the case for
WEB-NGRAM would have looked stronger with the quote in it. It is recorded as a
correction in three places instead.

**The brief and the documentation disagreed about UTC.** §14 states the `DATE`
column is a 15-minute **UTC** bucket. Neither GDELT page states a timezone
anywhere, and I could not find one. The semantics §14 asks for are all defined,
and the one field that could not be established is an open question rather than
an assertion — the collector preserves the raw label, so this costs nothing to
answer later.

**Two silent holes surfaced from writing the §22 matrix rather than from reading
the code.** A descriptor with no rights basis passed for every source without a
licence allowlist, which is to say for GDELT specifically. Both holes were
reachable only by hand — but that is the standing the transport's host check has
too, and it is checked anyway.

**The 2gram question I left open in the last PR had to be answered here.** The
answer is that a two-word phrase with no position, no document id and no URL is
further from an excerpt than a seven-word snippet with one — a structural finding
rather than a judgment about length. A reviewer who disagrees should say so
before a collector exists, because withdrawing `2gram` afterwards is more
expensive than not authorising it now.

**Two incidental defects surfaced from reading output rather than code.** A CLI
line had told every reader "no collector exists for any source" since Mission 1.5
built one, and a generated governance document had been claiming ten first
reviews out of four. Both are small; both had been true-looking for several
missions; neither would have been found by a test, because no test asserted on
prose.

**What I did not do:** no collector, no file fetched, no record persisted, no
normalizer, no signal, no vector, no claim, no evidence, no score.
