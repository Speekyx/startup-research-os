# Source-Native Issue Identity — Candidate Landscape V1

**Authoritative.** Mission 1.21 §4-§8. Which public defect trackers expose a
publisher-declared canonical-duplicate relation, and which of those can actually
be acquired under `local-private-research-v1`.

**The requirement that decides everything here:** SROS must not decide that two
reports mean the same thing. The SOURCE must already have said so, as issue
state.

> **Result: The structure exists. The access does not.** Every
> candidate that publishes a usable data licence also publishes a robots
> directive that disallows the API path, and the one deployment whose directive
> permits it publishes no data licence at all. **EXPLICIT ISSUE IDENTITY ROUTE =
> BLOCKED BY SOURCE GOVERNANCE.**

**This document was first written before the access layer was checked**, and its
earlier revision named a winner. The correction is kept in git history rather
than smoothed over: reading the licence before reading the access directive is
the process failure §4 of the report records.

---

## 1. The structural gate, applied first

§5 admits a candidate only if its documented data model carries an explicit
source-native identity relation — `dupe_of`, `duplicate_of`, `merged_into` or
equivalent — recorded as **actual issue state**. A "possible duplicate"
suggestion, a similarity endpoint, a shared label or a shared component is
excluded by name.

| Shape | Relation, from first-party API documentation | Passes §5 |
|---|---|---|
| **Bugzilla** | `dupe_of` (int) — *"The bug ID of the bug that this bug is a duplicate of. If this bug isn't a duplicate of any bug, this will be null."* | **yes** |
| **Launchpad** | `duplicate_of_link` (writeable, *"Link to a bug … Duplicate Of"*) and `duplicates_collection_link` (*"MultiJoin of bugs which are dupes of this one"*) | **yes** |
| **Debian BTS** | `merge` / `merged-with` — the maintainer merges reports into one | **yes** |
| **Jira** | `duplicates` / `is duplicated by` issue links | yes, weaker — a link type rather than a field on the issue |
| **GitLab** | closing an issue as a duplicate is a quick action and a system note | **no** — no canonical field in the documented model |
| **GitHub** | `state_reason` records that an issue was closed as a duplicate | **no** — the CLOSE REASON is state; the canonical TARGET is not a documented field. And `github` is `RESTRICTED` and was not reopened (§4) |

**Three shapes pass the structural gate**, which answers the question Mission
1.20 left open: **publisher-declared issue identity is real and is documented.**
The obstacle is somewhere else.

---

## 2. The five-column view

| Deployment | Identity relation | Data licence | Minimisation at acquisition | Operator access directive | Verdict |
|---|---|---|---|---|---|
| **TDF Bugzilla** (LibreOffice) | `dupe_of` | **CC BY-SA 4.0**, stated on the deployment | **`include_fields`, verified** | **`Disallow: /`; `/rest/` not allowed** | assessed RESTRICTED |
| **Launchpad** (Ubuntu) | `duplicate_of_link` **and** `duplicates_collection_link` | metadata *"freely for any purpose"* | **none — 41 fields, allowlist ignored** | **`Disallow: /api/`; names Claude agents; `ai-input=no`** | assessed RESTRICTED |
| **Mozilla Bugzilla** | `dupe_of` | **not addressed** | `include_fields` | `Disallow: /`, `Crawl-delay: 30` | not pursued |
| **Debian BTS** | merges | **not addressed** | — | `Disallow: /` for `*` | not pursued |
| **kernel.org Bugzilla** | `dupe_of` | **not addressed** | `include_fields` | **allows `/rest/`** | not pursued |

**Read the last two columns together.** The two deployments that grant the most
are the two that most clearly forbid the fetch, and the only deployment whose
robots directive permits the API path is one that never licensed its data.

---

## 3. The Document Foundation Bugzilla — everything favourable except the fetch

`https://bugs.documentfoundation.org/rest/` · **not registered** (see §7) · assessed **RESTRICTED**

**The data side is the best in the catalog for this purpose.** The deployment's
own front page states:

> "Please note that all contributions to The Document Foundation Bugzilla are
> considered to be released under the Creative Commons Attribution-ShareAlike
> 4.0 International License, unless otherwise specified."

**A licence on the tracker, not on the tracker software** — the §11 distinction,
made by the operator rather than by us. And TDF states licences **per property**:
the LibreOffice website is CC BY-SA 3.0, the TDF Wiki is CC BY-SA 3.0 Unported,
the Bugzilla is CC BY-SA 4.0. Three properties, three statements, three
versions. Nobody copied a footer.

**Minimisation would have been the best the catalog has seen.** A live probe
returned exactly the six requested fields and nothing else:

```json
{"bugs": [{"status": "CLOSED", "dupe_of": null, "product": "LibreOffice",
           "resolution": "FIXED", "component": "LibreOffice", "id": 29381}]}
```

No reporter, no assignee, no CC list, no comments — absent from the wire rather
than filtered afterwards.

**And the access layer refuses.** `robots.txt` is `User-agent: * / Disallow: /`
followed by an allowlist of six specific CGI paths. `/rest/` is not among them.

The file is **curated, not boilerplate**: it allows `/show_bug.cgi` while
disallowing `/show_bug.cgi*ctype=*`, and disallows `/page.cgi*id=user_activity*`
specifically. Somebody was making choices in that file, and `/rest/` is not in
the set they chose.

**A content licence is not an access grant, and Mission 1.18 established that
here first.** For Stack Exchange the licence decided reuse and the *API Terms*
decided access. TDF publishes no API terms at all, and its only access statement
is negative. Reading the licence as covering the fetch would be exactly the
grant-by-absence that rule 8 of the registry contract forbids.

**One question would change the verdict**, and it is written down rather than
assumed: does TDF intend the robots directive to cover programmatic REST use, or
is it aimed at page crawlers? **No message has been sent**, and nothing here
implies one was.

---

## 4. Launchpad — two blockers, and the second is the durable one

`https://api.launchpad.net/1.0/` · **not registered** (see §7) · assessed **RESTRICTED**

**Structurally the richest model surveyed.** A duplicate carries
`duplicate_of_link`; the canonical bug carries `duplicates_collection_link` and
`number_of_duplicates`. Nothing else lets the canonical issue enumerate its own
duplicates.

**The rights split is the most elegant this catalog has recorded**, and it lands
exactly where this mission's minimisation does. From *Bugs copyright*:

> "All bug comments are the property of the people who created them. Metadata and
> statistics generated by the Launchpad Bug Tracker are the property of Canonical
> Ltd and may be used freely for any purpose as long as accreditation and the
> Launchpad URL are given along with that data."

A positive grant over the metadata a duplicate relation lives in, freely and for
any purpose — with comments, which this mission does not want, expressly outside
it.

**Blocker 1, access.** `robots.txt` disallows `/api/` for every user agent, names
**ClaudeBot, Claude-User and Claude-SearchBot** in a long AI-agent block list
with `Disallow: /` and `DisallowAITraining: /`, and sets `Content-Signal:
ai-train=no, search=yes, ai-input=no`. `ai-input=no` is an explicit signal
against using the content as input to an AI system, which is what this deployment
would be.

**Blocker 2, minimisation, and it does not depend on permission.** A probe
returned **41 fields including `owner_link`**, and supplying a field allowlist
returned 41 fields again. The API has no field selection for an entry.

So acquiring the relation means receiving a person link on every request and
discarding it — the practice Mission 1.18 refused by name: *a request that
fetched the owner object and discarded it has still fetched it.*

**Blocker 2 is the one to remember.** Permission can change with a message; an
API's field model cannot.

---

## 5. Mozilla, Debian, kernel.org

- **Mozilla Bugzilla** — same `dupe_of`, same `include_fields`, largest corpus,
  and no first-party statement licensing bug content. The Websites &
  Communications Terms say content is *"generally made available … through open
  licenses such as Creative Commons"* and *"in most cases we ask"* — a
  description of practice, not a grant. `NOT_ADDRESSED` blocks under rule 8, and
  robots.txt is `Disallow: /` with `Crawl-delay: 30` besides. **Not a criticism
  and not permanent**: it is the difference between a foundation that put a
  licence line on its tracker and one that has not been asked.
- **Debian BTS** — `merged-with` is genuine publisher-declared identity. The
  Debian WWW Pages License covers `www.debian.org`; nothing found licenses BTS
  report content, and `robots.txt` disallows everything for every agent except
  five named search engines.
- **bugzilla.kernel.org** — **the only deployment whose robots directive permits
  the API path**: `Allow: /` with disallows on `*.cgi` patterns, which `/rest/`
  is not. It publishes no data licence at all, so commercial use, storage and
  derived analytics are each `NOT_ADDRESSED`. The one door that is open leads to
  a room with no permissions in it.

---

## 6. What this landscape establishes

**The explicit-identity route exists and is not reachable.** Three trackers
document a canonical duplicate relation as issue state; every one of them fails
the local-private profile on the access layer, the licence layer, or the
minimisation layer — and the failures are not correlated in a way that leaves a
gap to walk through.

**The pattern is worth stating on its own**, because it will recur: an operator
can license its content generously and still not want automated agents fetching
it, and those are two different documents saying two different things. This
repository has treated access and reuse as separate layers since Mission 1.18.
This is the first time the separation blocked a source whose licence was
perfect.

**No message has been sent to any operator.** The two questions that would change
the verdicts are written down in §3 and §4 above, and writing a question down is
not asking it.

---

## 7. Why neither candidate is registered in the catalog

**Not an omission, and worth naming because it is a real constraint the
repository has never met before.**

A source registered today must carry a review under the LEGACY profile.
`SourceRecord.review` is typed `PolicyReview | None`, so the MODEL allows a
source without one — but eighteen tests and two generated documents assume it is
present, because every source registered before now was first assessed under the
commercial profile and later re-assessed locally.

These two were assessed **only** under `local-private-research-v1`, which is the
first time that shape has arisen. Registering one would mean making the
legacy-profile review optional catalog-wide: a change to what a registered source
IS, touching the generated review-results and coverage documents and the tests
that guard them.

**That is an architectural change and it belongs in its own mission with an
ADR**, not in the diff of a source mission — the change-control rule
`docs/CLAUDE.md` §Change control states. So the evidence lives here, in an
Authoritative document, and the catalog is untouched at 29 sources.

**The follow-up is named rather than left implicit:** decide whether a source may
be registered under a modern profile only, and if so, make the legacy review
optional everywhere it is assumed. Until then, a candidate assessed only under a
modern profile is recorded in a document like this one.
