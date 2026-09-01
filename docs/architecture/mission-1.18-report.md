# Mission 1.18 — Stack Exchange Problem & Solution-Seeking Evidence

**Sprint 1. Authorized by the Mission 1.18 brief §1-§50.**

> ## MISSION 1.18 IS IN PROGRESS
>
> **Completed:** the review, the ADR-031 attribution correction, the collector,
> one real bounded acquisition, 15 RawRecords and verified idempotency.
>
> **Not started:** the `community_question` record kind, normalization,
> inspection of the real questions, the Signal feasibility decision, and any
> Claim or Evidence. **This report does not claim completion**; §10 records
> exactly what remains.

**The review approves: `APPROVED_WITH_CONDITIONS` under
`local-private-research-v1`, ELIGIBLE, resource-ready — and the collector now
exists and has run.**

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

## 7. Signals, Claims, Evidence

**None, and none was designed — deliberately.** The Signal semantics depend on
inspecting real questions, and that inspection has not been done. Designing a
cohort rule against imagined data is exactly what the brief warns against.

| | |
|---|---|
| Signals | 0 |
| OBSERVED Claims | 0 |
| Evidence rows | 0 |
| Observation category, independence, reliability, scorability | not reached |

---

## 8. Boundaries

| | |
|---|---|
| INFERRED Claims | **0** |
| Opportunities | **0** |
| Embeddings | **0** |
| Product / market / WTP scores | **0** |
| TED, World Bank, GDELT semantics or data | **unchanged**, and none was collected |
| Gateway backlog | not fixed; its duplicate-row tripwire grew to seven sources, as predicted |

### Counts before and after

| | Before | After |
|---|---|---|
| RawRecords | 23 | **38** (+15 Stack Overflow) |
| NormalizedRecords | 23 | 23 — **not normalized yet** |
| Signals / Claims / ClaimRevisions / Evidence | 8 / 8 / 8 / 8 | 8 / 8 / 8 / 8 |
| ReliabilityAssessments | 1 | 1 |
| Opportunities / Embeddings / Scores | 0 | 0 |

The 15-record gap between raw and normalized is the honest state of a mission in
progress, not a defect: nothing has been normalized because the record kind has
not been decided.

Catalog counts changed: 63 reviews, 99 evidence records, 43 conditions, one new
access profile, one new compliance entry.

### Did all gates pass?

**Yes** — zero-dependency suites, all pytest suites, seven validators, contract
generation `--check`, all four generated-document checks, ruff, mypy,
environment-template secret check, `assert_registry_grants_nothing`.

Three existing tests needed repointing because the registry genuinely changed. One
of them, the eligibility-view condition count, had been maintained by appending
`| {"ted-eu"}` by hand — it is now **derived across every profile**, because the
hand-added set was about to become the growth tripwire its own comment warned
against.

---

## 9. Why this pass stopped where it did

The remaining work is a **new record kind**, a normalizer, the empirical
inspection of real questions, a Signal semantic designed against them, a
deterministic extractor with hard negatives, and a claim and evidence path. TED
needed Missions 1.15.8 through 1.15.11 for the equivalent, and each found
something that changed the design.

The collector half is finished and tested; the rest benefits from being done with
the same care rather than compressed to finish a report.

---

## 10. Exactly what remains for Mission 1.18

1. **`community_question` record-kind decision.** A question is a community
   solution-seeking document and fits none of `numeric_observation`,
   `lexical_frequency_observation` or `procurement_notice`. A vocabulary
   extension is likely and follows the canonical migration rules.
2. **Normalization** of the 15 real records, preserving question identity, tags,
   the source timestamp with its real semantics, answer metadata, the canonical
   link and the licence — and treating an accepted answer as *the asker accepted
   an answer*, never as *solved*.
3. **Inspection of the real normalized questions.** What tag combinations look
   like, how specific titles are, whether a deterministic cohort is constructible
   without semantic inference, and what the false positives are.
4. **The Signal feasibility decision**, which is genuinely open. A tag identifies
   a subject, not a problem: `python` is not a cohort. **Zero Signals is a
   legitimate answer** and must not be worked around.
5. **Signal implementation only if defensible**, minimum support >= 2, hard
   negatives.
6. **OBSERVED Claim and Evidence only if a real Signal exists.**
7. **Final update of this report.**

Nothing above is blocked. The data is in the database and the governance is
settled.
