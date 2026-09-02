# Mission 1.18 — Stack Exchange Problem & Solution-Seeking Evidence

**Sprint 1. Authorized by the Mission 1.18 brief §1-§50.**

> ## OUTCOME S0 — ZERO SIGNALS, AND THAT IS THE RESULT
>
> Stack Exchange is approved, collected and normalized: 15 RawRecords, 15
> NormalizedRecords, a fourth record kind and a fourth normalizer. **The 15 real
> questions were then read, and they carry no repeated problem a deterministic
> rule could see.** So the mission produced **0 Signals, 0 Claims, 0 Evidence** —
> not blocked, not deferred, not insufficient data, but a derivation considered
> against real data that correctly produced nothing.
>
> §7 records the tag structure that decided it, so the decision can be checked
> rather than taken.

**The review approves: `APPROVED_WITH_CONDITIONS` under
`local-private-research-v1`, ELIGIBLE, resource-ready. The collector and the
normalizer both exist and have both run.**

Full review: [`stack-exchange-questions-v1.md`](../data/stack-exchange-questions-v1.md).

---

## 1. Review

### What were the three previously open questions?

Read from the canonical review, not this brief:

1. Retrieve the Public Network Terms of Service and the Consolidated Responsible
   AI policy from an environment those paths serve, and assess commercial reuse,
   storage and model processing against them.
2. Determine the precise attribution obligations CC BY-SA imposes on derived
   analytics, and whether share-alike reaches aggregated outputs.
3. Determine whether Stack Data Licensing is the required route for this use
   case, and if so what it covers.

### Which documents closed them, and how were they obtained?

| Document | Obtained | Result |
|---|---|---|
| Public Network Terms of Service | **operator-supplied** (this environment: HTTP 403) | closed Q1's licence and storage limbs |
| API Terms of Use | **operator-supplied** (this environment: HTTP 403) | closed Q1's access limb, and Q3 |
| Consolidated Responsible AI policy | **retrieved directly**, HTTP 200 | closed Q1's model limb, by being empty |

### Was any anti-bot protection bypassed?

**No.** One ordinary HTTPS request per document, with a truthful User-Agent naming
the project. Two returned 403 and **neither was retried**; no header was varied to
look like a browser and no alternative path to the same text was sought.

An approval written on text obtained by circumvention would have been
indistinguishable from a correct one until it mattered, which is the whole reason
the rule exists.

### What is the new verdict?

**`APPROVED_WITH_CONDITIONS`** under `local-private-research-v1`, version 1 of its
own profile line. The commercial profile stays `REQUIRES_REVIEW` — its questions
about redistribution and customer-facing access are exactly the ones ShareAlike
would bite on, and this mission did not ask them.

### Is commercial-purpose local research positively permitted?

**Yes, and the basis is the content licence rather than the platform's terms.**
Subscriber Content is CC BY-SA 4.0, which permits reproduction and adaptation for
any purpose including commercial. That mattered because **local is not
non-commercial**: the research evaluates commercial products, so the right had to
be granted rather than assumed away by the deployment being a laptop.

### Storage? Derived analytics? Model inference? Training? Embeddings?

| | |
|---|---|
| Storage | **PERMITTED.** The Terms' storage restriction expressly excludes *"other than Subscriber Content or content made available via the Stack Overflow API"*, and CC BY-SA grants reproduction |
| Derived analytics | **PERMITTED_WITH_CONDITIONS**, under the licence's grant to produce Adapted Material |
| Model inference | **PERMITTED_WITH_CONDITIONS** — reading and classifying licensed text is use within that same grant |
| Model training | **not assessed and not authorised.** The profile forbids it, so the review did not reach for a basis it does not need |
| Embeddings | **not authorised.** Profile, and D-12 |

**The API Terms are silent on storage, analytics and commercial use, and the
silence is recorded as silence.** The two layers stay apart: the API Terms decide
**access**, the licence decides **reuse**. The API carve-out removes an obstacle
and grants nothing — read as a standalone licence it would be a grant by absence,
which rule 8 of the registry contract forbids.

### Is Stack Data Licensing required?

**Not for this exact path, on these documents — and that is the whole finding.**
It does not generalise to *"never required"*. A different volume, purpose or route
could be governed differently, and the existence of a paid product is neither a
prohibition on the free API nor a permission for anything.

### What conditions apply?

`stack-exchange-attribution`, `stack-exchange-official-api-only`,
`stack-exchange-personal-data-minimisation` — all three CAPABILITY-verified and
all three **satisfied**.

---

## 2. Two calls the review turned on

### ShareAlike is avoided by the profile, not answered by the review

CC BY-SA's ShareAlike obligation attaches to Adapted Material that is **Shared**,
and this profile shares nothing. So the classification question — *is a derived
analytic artefact Adapted Material at all* — **did not have to be decided**, and
was not.

Carried as an open question rather than closed, because a review that quietly
relied on *"we do not publish"* without writing it down would be one deployment
change away from being wrong. **The moment any output is published, this review
must be redone.**

### `PLATFORM_LICENSED`, which decided whether the resource is reachable at all

The content is written by users and Stack Exchange does not own it. But the enum
is not asking who owns it: `THIRD_PARTY` means *"separate permission from the
owner is required"*, and that permission already exists and already reaches us —
each contributor grants CC BY-SA to everyone, and there is nobody left to ask.

`PLATFORM_LICENSED`'s own test is *"the reviewed terms cover it"*, and the Public
Network Terms cover Subscriber Content explicitly by naming its licence.

Classified `THIRD_PARTY`, the resource is refused by `third_party_denied` and the
source is **approving but unreachable** — the wrong answer for a right-sounding
reason. It is argued in the compliance entry rather than set.

---

## 3. Resource and access

| | |
|---|---|
| Resource | `questions/stackoverflow`, family `stack-exchange-questions` |
| Site | **Stack Overflow only.** ~180 other network sites are not authorised and are not assumed to carry equal opportunity value |
| Route | `stack-exchange-api`, `https://api.stackexchange.com/2.3/` — official API only |
| Licence | CC-BY-SA-4.0, rights basis `NAMED_LICENCE` |
| Refused by name | the **Data Dump** (route authorisation *and* excluded family), plus users, Teams, chat, jobs, companies |
| Personal data acquired | **none.** `owner` and every field under it, `last_editor` and `comments` are excluded at acquisition |
| Attribution | two obligations from two documents — see below |
| Bounds | required and defaulted nowhere; the real values used are in §6 |
| Quota/backoff | the registry records the rate limit `UNKNOWN`, but the API returns `quota_remaining`, `quota_max` and `backoff` and those ARE honoured — §5 |

**The Data Dump route was registered in this mission so that it could be
refused.** It genuinely exists, and deleting it to keep the registry tidy would
falsify a fact about the source to obtain a permission (ADR-028). The validator
enforced this directly: *"a route authorisation that names a permitted path
without refusing an excluded one records a preference, not a restriction."*

**Attribution is two obligations, not one said twice.** The API Terms require the
product surface to *"visually indicate that the Stack Exchange Network is the
source"* — owed because of how the data was reached. CC BY-SA requires attribution
and a licence identifier — owed because of what the data is.

### A gap the first CC BY-SA source exposed

CC BY-SA also requires *"a URI or hyperlink to the Licensed Material"*, and
`AttributionElement` has **no member for a per-item link**. `DATASET_DOI` is the
nearest and is wrong.

**The gap is not specific to this source** — World Bank and Eurostat are CC BY 4.0
and carry the same requirement with the same three elements. Adding a member to a
closed enum needs an ADR, and doing it as a side effect of a source mission is the
change-control violation `docs/CLAUDE.md` describes. Recorded as an open question;
the per-question URL is already in the allowed field list, so the data a future
element would render is held.

---

## 4. The attribution gap was real, and it was the worse shape

**Outcome B.** `AttributionElement` could not express the per-item link CC BY-SA
requires, and `stack-exchange-attribution` reported **SATISFIED anyway** —
because `source-attribution-display` verifies that the *declared* elements render
and has no knowledge of what a licence requires. A correct mechanism check across
an incomplete list, which is worse than a failing one.

**ADR-031** adds `SOURCE_ITEM_LINK`: generic, not source-specific, not
licence-specific, supplied per item because a fixed link would attribute every
item to one place.

**Two existing designs caught my own mistakes while I made them.** The
conformance probe builds "every element supplied" and mine was not in it, so it
failed for a source whose configuration was correct. And `_without` removes one
element by explicit branch rather than a name table *"because a table hides a
missing entry as a silent no-op"* — its docstring made that claim in Mission 1.4,
and this is the first time it was tested. It held.

**World Bank and Eurostat carry the same obligation and are NOT declared.** Their
collectors supply no per-item link, so declaring it would fail closed on sources
this mission was told not to modify. Recorded as a finding with a named
follow-up.

**The source is still ELIGIBLE**, now over an obligation that is complete rather
than under-declared.

---

## 5. The collector

**`stack-exchange-questions@1.0.0`**, official API only, one site, no fallback.

| | |
|---|---|
| Route | `stack-exchange-api`, by label; the Data Dump is blocked and absent from the context |
| Site | `stackoverflow`, a **constant and not a parameter** — a `site` argument would make the authorised scope a runtime choice |
| Bounds | `from_date`, `to_date`, `page_size`, `max_pages`, `max_records` all **required**; `StackExchangeBounds()` is a `TypeError` |
| Two ceilings | `page_size <= 100` is the **source's**; `max_pages <= 20` is **ours**, enforced separately |
| Identity | the source's own `question_id`, scoped by site — never a title, a hash or a page position |
| Quota | `quota_remaining` / `quota_max` read from the envelope and recorded |
| Backoff | **obeyed**, not merely logged — it is the one rate instruction this source publishes |
| Failure | a non-200, an error envelope or a non-JSON body is a refused acquisition. **No HTML fallback exists** |

### The filter is the API's own, and the first one was an HTTP 400

Field minimisation happens **at acquisition**, through Stack Exchange's
`/filters/create` method. The first attempt used an invented filter id and the
API returned 400 — a better outcome than a plausible-looking string that silently
selected the wrong fields.

The real filter was derived once from `base=default`, `include=question.body;
question.link; question.content_license; question.accepted_answer_id`,
`exclude=question.owner; question.last_editor; question.comments;
question.answers; question.closed_by`, and **verified by reading it back**:
`question.owner` is absent from `included_fields`.

**An owner arriving anyway is a failure, not a cleanup.** A collector that
quietly dropped it would report success over data it should never have received.

### `use_profile` provenance was a small generic change, and was made

Mission 1.17 found it absent from every RawRecord. `build_raw_record` already has
the context, so the profile is now recorded on **new** records. **Historical
records are not backfilled** — they were written under a model with no such
concept, and inventing the field for them would assert something nobody recorded.

---

## 6. The real bounded acquisition

Deliberately small, and deliberately **not** tuned to produce a Signal.

```text
site         stackoverflow          endpoint   https://api.stackexchange.com/2.3/
tagged       python                 filter     !SyjNl4V)kvv2kw3Qt6
window       2024-03-04 to 2024-03-05          order asc, sort creation
page_size    10    max_pages 2      max_records 15
```

| | |
|---|---|
| HTTP requests | **2** |
| Items returned | 16 |
| RawRecords persisted | **15 new** (`max_records` stopped it mid-page) |
| `quota_remaining` / `quota_max` | **294 / 300** |
| `backoff` | none returned |
| `has_more` | **`true`** — and collection stopped anyway, at `max_pages` |
| Owner fields received | **none** |

**Idempotency verified**: the identical acquisition re-run gave
`new: 0, unchanged: 15, revised: 0`.

A persisted record, read back:

```text
key         stack-exchange|stackoverflow|78098368
reference   https://stackoverflow.com/questions/78098368/python-multithreading-i-o-operation
use_profile local-private-research-v1
licence     CC-BY-SA-4.0
attribution Stack Exchange Network CC BY-SA 4.0 https://stackoverflow.com/questions/78098368/...
payload     answer_count, body, content_license, creation_date, is_answered,
            last_activity_date, link, question_id, score, tags, title, view_count
owner       absent
```

**The `has_more: true` line is worth reading twice.** The source said there was
more and the collector stopped, because `max_pages` is a ceiling rather than a
suggestion. That is the no-crawl-until-exhaustion property, demonstrated on real
data rather than asserted.

### A guard caught a real omission

`assert_registry_grants_nothing` refused a database holding raw records for a
source this codebase *"cannot collect from"* — true of `IMPLEMENTED_COLLECTORS`
and false of the repository. The collector existed and had not been declared. The
guard was right and the set was wrong.

---

## 7. The record kind, the normalizer, and the Signal decision

### Which record kind, and why a fourth one?

**`community_question`** — migration 0024, one registry row, **no schema change**.
`acquisition.normalized_records` already carries `payload JSONB` and a
`record_kind_id` with a foreign key into `registry.registry_entries`, so the
storage existed and what was missing was permission to use it.

None of the three existing kinds could hold a question without getting worse for
the sake of a new source. A question carries no measured value, so
`numeric_observation` would have to make `observation.value_state` meaningless for
it; it counts no term, so `lexical_frequency_observation` would have to lose its
term and its language; it is nobody's procurement, so `procurement_notice` would
have to make monetary amounts optional and give a question a buyer.

**It is named for a SHAPE, not for a vendor.** `stack_exchange_question` would
have made the record-kind vocabulary a list of sources. A question asked on a
public Q&A site is a shape other sources share; the SITE is a field and the source
is provenance. This is the first kind in the repository for which that distinction
had to be made deliberately, and it is the one design decision here that a later
source will either thank or curse.

### What does one normalized record assert?

*Stack Exchange published this public question on Stack Overflow with these source
fields.* That is the whole assertion. `stack-exchange-question@1.0.0`, run over all
15 records, idempotent — and after a later code fix, a forced re-normalization
returned `unchanged: 15, conflicted: 0`, which proves the output byte-identical
rather than asserting it.

Four things the payload refuses to say, each written into the record rather than
left to a reader's discipline:

| In the record | Says, in the record itself |
|---|---|
| `tags.scheme: stack-exchange-tags:stackoverflow` | the site's vocabulary, never mapped to a taxonomy of ours |
| `answers.accepted_answer_semantics` | *"the asker marked an answer accepted; not a statement that the problem is objectively resolved"* |
| `engagement.semantics` | *"source counters, carried unpromoted: not importance, not demand, not market size"* |
| `author: null` | not omitted for tidiness — never acquired |

**Every record is `VALID`, and no adapter here had produced that before.** Every
GDELT record is `PARTIAL` because H-29 and H-30 are open; every TED record is
`PARTIAL` because H-37 is. Nothing is open here — and this is **the first adapter
whose period is `ESTABLISHED` on the source's own evidence**. A Unix epoch second
is an unambiguous instant, unlike TED's offset-without-a-time or GDELT's unzoned
bucket, so `observed_at` is a real moment for the first time in this repository.

A raw record carrying `owner`, `last_editor` or `comments` is **refused at
normalization** rather than stripped: the collector refuses such a *response* and
this refuses such a *record*, because they are different moments and a record
already in the database can only be caught here. A record with no canonical URL is
refused too — CC BY-SA requires the link, so a record that cannot be attributed is
never normalized into one that cannot be displayed.

### What do the real questions actually look like?

Read from the database, not from the design:

| Fact | Value |
|---|---|
| Questions | 15 |
| Distinct tags | 35 |
| Tags on 2 or more questions | **3** |
| Questions sharing a complete tag set | **0** |
| Repeated quoted identifier in a title | **0** |
| Title word on 3 or more questions | `python` — the query term, and nothing else |
| Accepted answer | 3 of 15 |
| Score | between -2 and 1 |

The three repeated tags are the entire cohort space, and each one fails:

- **`python` — all 15.** It is the term the query asked for. A cohort built on it
  is a property of the retrieval, not a finding about the world: it says *these
  are the questions we asked for.*
- **`google-cloud-platform` — 3.** Eventarc firing duplicate Cloud Run processes
  (`78098392`), a `setup.py` `install_requires` type error (`78098469`), and
  extracting text from a Google Doc (`78098567`).
- **`deep-learning` — 2.** The same `setup.py` packaging error (`78098469`) and
  whether padded rows affect backpropagation (`78098740`).

**`78098469` sits in both cohorts**, which is the sharpest available evidence that
these groupings are about subject and not about problem: one question cannot be
two repeated problems.

### Is a Signal derivable? No — Outcome S0

**A tag identifies a SUBJECT. It does not identify a PROBLEM.** Every
deterministic rule available over this sample — shared tag, shared tag pair,
shared title token — groups questions that share a technology and nothing else.
Getting past that would take semantic inference over question text, which is an
INFERRED step this mission does not authorise and which no Signal may rest on.

So the derivation was considered and produced nothing:

| | |
|---|---|
| Signals | **0** |
| OBSERVED Claims | **0** |
| Evidence rows | **0** |
| ReliabilityAssessment | **0** — none was created, and none applies |

**Three things that were not done, and each was available.** The cohort was not
weakened until something appeared — a support threshold lowered until it produces
output is a threshold that measures the analyst. A second, friendlier query was
not run. And no `INFERRED` path was opened to rescue the result.

**What would change the answer is a different acquisition shape, not a different
rule**: many questions about ONE narrow tool, where a repeated concrete failure
could actually recur. That is a mission with its own bounded acquisition and its
own review of what the query selects for — not a parameter on this one.

The tag structure above is pinned in `TestWhyNoSignalIsDefensible`, by question
id. A mission that declines to produce data owes the tests that fix why, or it is
indistinguishable from one that forgot.

---

## 8. Two defects the tests found after the data was already correct

Both were in code paths the 15 real records never took, which is exactly why they
survived a successful production run.

- **`record.raw_record_id` does not exist** — `RawRecordView` calls it
  `record_id`. Every refusal path in the normalizer would have raised
  `AttributeError` instead of the `NormalizationFailure` it was written to raise.
  All 15 records were well-formed, so nothing ever reached it.
- **`QualityReason.OPTIONAL_FIELD_MISSING` does not exist.** A missing question
  body would have crashed. The fix is not to add the member: the record kind does
  not require a body, and `NormalizationQualityReason` has no member that would
  truthfully name the absence. Reaching for the nearest one would put a wrong code
  where a consumer branches, and adding a member to a generated closed enum is a
  contract change with an ADR behind it that no record in the real sample calls
  for. A missing body now leaves the record `VALID` with `question.body: null`,
  where the absence is visible in the data itself.

The adapter consequently has **no `PARTIAL` branch at all**, and that is stated in
the code rather than left as an accident: a record either carries the four facts
the kind requires, or it is refused above.

---

## 9. Boundaries

| | |
|---|---|
| INFERRED Claims | **0** |
| Opportunities | **0** |
| Embeddings | **0** |
| Product / market / WTP / pricing / MRR scores | **0** |
| ReliabilityAssessments created | **0** |
| Other Stack Exchange sites, Data Dump, users, Teams, chat, jobs, companies | **not touched, and refused by name** |
| The two HTTP 403s | **not retried**, no header varied, no alternative route sought |
| TED, World Bank, GDELT semantics or data | **unchanged**; nothing recollected, nothing rewritten |
| The historical 23 RawRecords | **not backfilled** with `use_profile` |
| Gateway profile bug | **not fixed**; its duplicate-row tripwire grew to seven sources, as predicted |

### Counts before and after

| | Before | After |
|---|---|---|
| RawRecords | 23 | **38** (+15 Stack Overflow) |
| NormalizedRecords | 23 | **38** (+15, all `VALID`) |
| Record kinds | 3 | **4** |
| Normalizers | 3 | **4** |
| Signals / Claims / ClaimRevisions / Evidence | 8 / 8 / 8 / 8 | **8 / 8 / 8 / 8** |
| ReliabilityAssessments | 1 | 1 |
| Opportunities / Embeddings / Scores | 0 | 0 |

Normalized coverage by source and kind, read back:
`world-bank / numeric_observation / VALID / 6`,
`gdelt / lexical_frequency_observation / PARTIAL / 6`,
`ted-eu / procurement_notice / PARTIAL / 11`,
`stack-exchange / community_question / VALID / 15`.

### Did all gates pass?

**Yes.** Zero-dependency suites (555 tests across 8 packages), all pytest suites
(7 packages, including 1,464 acquisition tests), the seven validators plus
`check_env_template` and `assert_registry_grants_nothing`, contract generation
`--check`, all four generated-document checks, ruff check, ruff format --check,
and mypy over all 146 source files.

**Six existing tests were repointed because the repository genuinely changed**, and
none was weakened. Three in the earlier pass, for registry counts the new source
moved. Three more here: `IMPLEMENTED_NORMALIZERS` and `NORMALIZER_REGISTRY` grew
from three entries to four, and `RECORD_KINDS` from three to four. Each remains an
**equality** rather than a containment, because a fifth kind appearing without a
source that needs it is exactly what those assertions exist to catch.

`assert_registry_grants_nothing` had already caught a real omission in the earlier
pass: raw records existed for a source `IMPLEMENTED_COLLECTORS` said this codebase
could not collect from. The guard was right and the declaration was missing.

---

## 10. What Mission 1.18 establishes, and what it does not

**Establishes.** That Stack Exchange questions can be lawfully acquired under the
local profile on a content licence rather than a platform's terms; that a
community question has a canonical shape this system can hold without damaging the
three kinds that came before it; that a public Q&A tag is a subject and not a
problem, on real data rather than on argument; and that the pipeline can be run
end to end and correctly stop before asserting anything.

**Does not establish.** Any pain, desire, willingness to pay, pricing power,
competition gap, distribution feasibility, retention or revenue potential. What
the sample contains is **15 distinct published solution-seeking observations**,
each asked once, in one bounded window about one tag.

**It is not 15 people, and this report originally said it was.** Author identity
was deliberately never acquired, so the deployment cannot count distinct askers
and must not word itself as though it could — the correct repair is the sentence,
not an acquisition. Corrected in Mission 1.19 §0.

The `problem` family gained a source that is **collected and normalized** and
still gained **no evidence**, and the honest reading is that the portfolio's
demand-side gap is unchanged.

---

## 11. The next portfolio gap

**No source is selected here**, because selecting one is a review act with its own
mission and its own retrieved evidence.

The gap this mission measured is not the one it set out to close. Mission 1.16
found six of eight business evidence families with no approving source; Stack
Exchange was chosen for `problem`, and it now demonstrates the sharper version of
that finding: **`problem` now has an approving, collected, normalized source and
still no evidence**, because what a public Q&A site publishes is *somebody asked
how to do something*, one time each.

So the gap with the most leverage is no longer *find a source for `problem`*.

**The first wording of that gap was too broad, and Mission 1.19 §0 narrowed it.**
It read *"no source in the portfolio observes the same subject twice"*, which
contradicts semantics this repository already implements:
`lexical-frequency-change@1.0.0` compares the SAME lexical stream across adjacent
source buckets, and `numeric-period-change@1.0.0` compares the SAME
source-reported metric across periods. Repeated observation of an entity is not
what is missing.

The precise gap is: **SROS holds no Evidence establishing repeated comparable
USER-PROBLEM instances for one narrowly defined problem.** A frequency series and
a metric series both re-observe a stream; neither re-observes a user encountering
the same difficulty. Distinguishing a one-off question from a recurring failure
needs the second thing, and nothing in the portfolio produces it. No proxy is
proposed, because a proxy nobody can validate is worse than an acknowledged gap.

Two shapes could close it and both are review questions, not engineering ones: a
source that publishes the same entity's state on a schedule, or an acquisition
design over an existing approving source that deliberately observes one narrow
subject repeatedly. Whichever is chosen, `WILLINGNESS_TO_PAY` and `PRICING` remain
where Mission 1.16 left them — the second with no registered candidate at all.
