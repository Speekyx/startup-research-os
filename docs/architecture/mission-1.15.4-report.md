# Mission 1.15.4 — TED-EU Local Private Research / Official Access Route Review

**Date:** 2026-08-31 · **Branch:** `sprint-1/mission-1.15.4` · **Scope:** one
source, one narrowed use case, no authorisation created.

**The routes' documented purpose covers what we want to do. H-36 is untouched by
that. And the thing that actually blocks us turned out to be our own model.**

**TED stays `REQUIRES_REVIEW` at review v5.** No
`AcquisitionAuthorizationContext` exists and none can be built.

---

## 0. What this mission found

It set out to authorise a narrow official route for local private research. It
found the evidence for the route, and then discovered that **every approval in
this registry is an answer to a use case the model never records** — so there is
nowhere to put a second, narrower answer.

That is worth more than a TED authorisation would have been, and it was only
visible because a source finally needed two answers at once.

---

# The §36 questions

## What is the real current TED use case?

Local, private research by one developer. Not publicly exposed, no external
customers, no redistribution, no resale, no model training, no embeddings,
aggressively minimised storage, analysis and machine extraction/classification
only, official routes only.

## Is the application currently local/private?

**Yes**, per the operator's own statement of the use case.

## Does local/private use itself create permission?

**No**, and nothing in this mission rests on it. Permission comes from the
source. What the narrower use changes is *which question is worth asking* — not
*may we mirror the corpus commercially*, but *do the official query routes
document a purpose that covers narrow local research*.

## Was any claimed Publications Office response excluded as non-authoritative?

**Yes.** A file at `Downloads/ted-eu-publications-office-response.txt` describes a
written reply. It is a user transcription and says so itself:

> *"This file is NOT a verbatim copy of the original email"*

> *"The response therefore confirms, **according to the user who received it**,
> that repeated reuse is authorised."*

| | |
|---|---|
| Classification | `USER_SUPPLIED / NON_AUTHORITATIVE` |
| Cited as Publications Office evidence | **no** |
| Copied into the repository | **no** |
| Entered as registry evidence | **no** |
| Deleted | **no** — §32 says do not delete user data automatically |

A test now asserts that **no source in the catalog** carries an
`OPERATOR_CORRESPONDENCE` evidence row, at any review version. It is a **tripwire,
not a validator** — a test that tried to *validate* an operator response would be
a specification for forging one. The first real response will be a visible diff.

## Which first-party TED documents were freshly reviewed?

| Document | |
|---|---|
| `docs.ted.europa.eu/api/latest/search.html` | Search API purpose and audiences |
| `data.ted.europa.eu` | TED Open Data Service, home and help |
| `docs.ted.europa.eu/ODS/latest/…` | index, audience, connecting, SPARQL endpoint, data availability, query tips |
| `docs.ted.europa.eu/ODS/latest/reuse/search-api.html` | modes, limits, request body |
| `ted.europa.eu/en/simap/developers-corner-for-reusers` | reuser entry point |

All on Publications Office domains. No mirror, cache, archive, search snippet or
third-party blog was used.

## What does the TED Search API say its intended purpose is?

> *"The Search API allows access to published procurement notices **for analysis
> and reuse**, promoting transparency."*

> *"…provides access to published notices via expert queries and enables bulk
> downloads of notices in XML format **for reuse or analysis**. Note that this API
> is **primarily targeted at data reusers** and does not require authentication,
> making it **openly accessible to any system or user**."*

## Does TED explicitly mention analysis?

**Yes**, repeatedly, on both routes.

## Does TED explicitly mention reuse?

**Yes**, repeatedly, on both routes.

## Does TED explicitly contemplate application integration?

**Yes.** *"Commercial Organisations: **Integrating TED data into platforms** to
provide added-value services for vendors and buyers"*, and the Open Data
Service's **Connect your app** button.

## Does TED explicitly contemplate repeated/updated access?

**Yes**, and this is the most explicit statement of the set:

> *"You can use this URL to run your query and **retrieve live results directly
> into Excel, Power BI, or any application that can get data from the web**."*

The Excel guide adds *"a permanent link to your query"* which you may *"update…
whenever you wish"*, and the changelog offers the request as a cURL, wget or
PowerShell command.

## Does TED contemplate commercial users or value-added applications?

**Yes, by name.** *"Commercial Organisations … to provide **added-value
services**"*, listed first among four audiences.

## What does the TED Open Data Service permit/intend?

> *"We organise this information as a knowledge graph and **publish it for
> analysis and re-use**. We invite you to explore, understand and use this
> information in **your research and applications**."*

> *"…or **write SPARQL queries to extract custom datasets across many notices**."*

Documented endpoint `https://data.ted.europa.eu/`; the front-end issues queries
against Cellar's Virtuoso endpoint at
`https://publications.europa.eu/webapi/rdf/sparql`. No authentication documented,
no rate limit published, no fair-use statement found. **Its footer's Legal Notice
links to `ted.europa.eu/en/legal-notice`** — the same document that governs the
bulk route, so the service adds no new licence and inherits the Decision in both
directions.

## Is the Search API route supportable for `LOCAL_PRIVATE_RESEARCH`?

**On the evidence, yes. On the model, it cannot be expressed.** See below.

## Is the Open Data Service route supportable?

**Same answer**, on the same evidence and the same obstacle.

## Is bulk XML supportable?

**No, and it was not made the default** (§12). Mission 1.15.3 established the
highest database-right exposure there — a monthly package is ~427 MB — and
nothing found here speaks to repeated substantial extraction. **Public
downloadability alone is insufficient.**

## Is full corpus mirroring still blocked?

**Yes**, unconditionally.

## Does H-36A remain open?

**Yes. NOT ESTABLISHED**, in either direction. Nothing retrieved names a maker or
asserts a substantial investment.

## Does H-36B remain open for broad corpus extraction?

**Yes. NOT ADDRESSED.** Nothing on either route mentions the sui generis right.

## Can narrow route authorization exist while broad TED remains unresolved?

**Not in the current model, and it should not be faked.** This is §26, and the
answer is empirical:

```text
build_authorization('ted-eu')  ->  AcquisitionNotAuthorizedError
    reasons:
      - policy review is REQUIRES_REVIEW
```

**One reason, and it is not about the route, the resource, the use profile or the
evidence.** `evaluate_eligibility` has no parameter for any of them, and
searching the contracts and acquisition packages for `use_profile`,
`deployment_profile`, `LOCAL_PRIVATE` or `MULTI_TENANT` returns **zero matches**.

The registry already narrows carefully **below** an approving source —
`authorize_resource` refuses by default and allows only what no rule objected to.
But all of it hangs below the gate, and the gate asks one question about the
source.

**The finding underneath is not about TED.** Every review here already assessed a
use case; `source-review-guide.md` tells reviewers to, and `docs/CLAUDE.md`
forbids narrowing it to rescue a source. **The use case is nowhere in the data
model.** Twenty-nine sources carry approval states that answer an unrecorded
question. That cost nothing while one product was being assessed. TED is the
first source whose product has two shapes at once, and the model has one slot.

The three available hacks are each worse than the gap, and the reasons are in
`route-scoped-source-authorization-gap-v1.md` §4.

## Did TED's global verdict change?

**No.** `REQUIRES_REVIEW`.

## Was a route/use-profile-specific authorization created?

**No.** The profile is *defined* in the gap document and *authorised* nowhere.
There is no compliance configuration for `ted-eu`, asserted by test — a
compliance entry for a blocked source would be preparation dressed as permission.

## What exact resource is covered?

**None is authorised.** The profile that *would* be, if the extension existed:

```text
profile     LOCAL_PRIVATE_RESEARCH
routes      TED Search API · TED Open Data Service (SPARQL)
resource    contract award notices and contract notices, eForms,
            1 March 2023 onwards
fields      notice id · publication date · award/contract date · buyer org ·
            supplier org · CPV · procurement classification · monetary amount ·
            MONETARY AMOUNT TYPE · currency · country/region · award status
excluded    every natural-person field · the whole contact block · logos ·
            unrelated full text · bulk XML packages · the ted-csv subset ·
            any resource not named
```

## What exact use profile is covered?

**None, in the registry.** `LOCAL_PRIVATE_RESEARCH` is a name this mission gave a
thing the model cannot store.

## Can `AcquisitionAuthorizationContext` be constructed?

**No.** `AcquisitionNotAuthorizedError: policy review is REQUIRES_REVIEW`. The
attempt is run as a test so the refusal cannot rot.

## Does authorization fail for public/commercial deployment?

**Yes** — everything fails, so this does too. Under the proposed extension it
would fail *by name*: a profile the review does not name is refused, so deploying
publicly requests a profile nothing has approved rather than silently inheriting
one.

## Does authorization fail for bulk mirroring?

**Yes.**

## Does authorization fail for model training?

**Yes**, and separately: condition 9 scopes machine processing to inference,
extraction, classification and structured analysis, and says training is not
authorised. Unchanged (§23).

## Is D-12 still open?

**Yes.** No embeddings. Being local is not a reason to embed (§24).

## Is personal-data minimisation unchanged?

**Yes** (§13, §18). A local deployment justifies collecting no more personal data
than a commercial one.

## What transaction fields could a future collector retain?

Notice id · publication date · contract/award date · buyer organisation ·
supplier organisation · CPV · procurement classification · monetary amount ·
**monetary amount type** · currency · country/region · award status.

**Requested through the Search API's `fields` parameter**, so minimisation happens
*at* acquisition. §14 forbids collect-first-minimise-later where the official
query supports field selection, and this one does.

## What fields must it discard?

Natural-person names · personal email · telephone · fax · personal address · the
entire contact block · unrelated full text · logos · personal identifiers.

## Were any collectors implemented?

**No.** No API client, no SPARQL client, no downloader, no parser, no Celery
task. Asserted against `IMPLEMENTED_COLLECTORS`, against the file tree for any
module whose stem contains `ted` or `sparql`, and against `SPARQLWrapper`
anywhere in the repository.

## Was any TED research data collected?

**No.** Route documentation is policy evidence; procurement notices are research
data, and none was fetched. No SPARQL query was issued.

## Were any RawRecords/NormalizedRecords/Signals created?

**No.** Zero rows with `source_id = 'ted-eu'`, asserted live.

## Were Claims/Evidence created?

**No.**

## Were reliability assessments created?

**No.** 0 (§25).

## Were Opportunities created?

**No.** 0.

## Was scoring performed?

**No.**

## Did the existing 12 / 12 / 7 / 7 / 7 remain unchanged?

**Yes.** RawRecords 12, NormalizedRecords 12, Signals 7, Claims 7,
ClaimRevisions 7, Evidence 7, Reliability 0, Opportunities 0, Embeddings 0,
Scores 0. Verdict distribution unchanged: 5 / 13 / 8 / 3 across 29 sources.

## If an official local route is authorization-ready, is the next mission a narrowly-scoped TED Official API Collector V1?

**It is not authorization-ready, so no.**

## If not, what exact blocker remains?

**Two, and they are independent.**

| # | Blocker | Owner | Shape |
|---|---|---|---|
| **1** | **H-36A/H-36B** — no first-party statement on the database right | Publications Office | Send the drafted request; failing that, legal review |
| **2** | **The registry has no use-profile dimension** | us | An ADR and a mission: record `assessed_use_profile`, one current review per profile, thread it through the gate, have the runtime declare its profile |

Blocker 2 is the new one, and it is the one that would still stand even if the
Publications Office replied favourably tomorrow **scoped to narrow local
research** — because there would be nowhere to record a narrow approval.

**Recommended order:** send the clarification (one email, already written); start
the governance extension, which is useful for every future source and not just
TED; and review `usaspending` (H-35) in parallel, since waiting on a reply is not
work.

---

## 1. Two things worth recording

**The strongest evidence in the mission proves the wrong thing, and that is the
whole discipline.** Four separate Publications Office documents say the routes
exist for analysis, reuse, application integration and commercial value-added
services. It is genuinely excellent intended-use evidence. It says nothing about
the sui generis database right, because an operator describing what its service
is for is not a right holder licensing a right in a collection. Condition 11
exists so that a reader arriving later, finding four enthusiastic documents,
cannot reach the conclusion this mission declined to.

**The operator's own word is `extract`.** The Open Data Service invites users to
*"extract custom datasets across many notices"* — the Directive's verb, in an
invitation, from the publisher. It is recorded because it is striking, and it is
load-bearing for nothing. Reading it as a licence would be the same error as
reading the CC0 metadata dedication onto the notice corpus, which Mission 1.15.3
refused.

## 2. Gates

| Gate | Result |
|------|--------|
| Zero-dependency suites | 515 tests, 8 packages, pass |
| Pytest suites | **7 pre-existing failures**, unrelated — see below |
| Mission 1.15.4 tests | 45 new, pass |
| `validate_source_registry` | pass — 29 sources, 0 warnings |
| All other validators | pass |
| Generated catalog documents `--check` | current |
| `ruff` / `mypy` | pass |

### The pre-existing failure

`test_world_bank_normalizer.py::TestPersistence` — 7 tests, all
`CheckViolation: normalized_records_normalized_after_collection_check`.

**Not caused by this mission**, verified by stashing every change and reproducing
on a clean tree. The cause is a fixture time bomb:
`normalization_fixtures.py` pins `NORMALIZED_AT = 2026-08-31 09:00 UTC`, while the
`seeded_raw` fixture runs the **real** collector, which stamps `collected_at` from
the real clock. The database's `CHECK (normalized_at >= collected_at)` is correct;
the constant was a snapshot, and the wall clock passed it at 09:00 UTC today. It
passed at 08:20 and fails permanently from 09:00 onward.

It is the same lesson as `testing-strategy.md` §36 — *a local snapshot is not a
test invariant* — in the time dimension. Flagged as a separate task rather than
fixed here, because a governance mission is the wrong place to change a
normalizer test fixture.

## 3. Where TED stands

**Better understood, equally blocked, and blocked by one more thing than
yesterday.**

The routes are documented and the documentation is good. The database-right
question is unchanged and still needs a person. And a second blocker appeared
that has nothing to do with TED: the registry cannot say *"this source, this
route, this use profile, yes — and that one, no"*.

That second blocker is the mission's real product. It affects every source, it
was invisible while the project had one product shape, and the honest response
was to write it down rather than to flip a verdict and hope nobody read the
conditions.
