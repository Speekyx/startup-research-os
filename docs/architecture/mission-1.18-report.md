# Mission 1.18 — Stack Exchange Problem & Solution-Seeking Evidence

**Sprint 1. Authorized by the Mission 1.18 brief §1-§50.**

**The review approves. `APPROVED_WITH_CONDITIONS` under
`local-private-research-v1`, ELIGIBLE, resource-ready — and no collector was
built.**

That is an outcome §37 did not list, and it is stated plainly rather than dressed
as one of the four: the governance half of the mission is complete and the
implementation half is not started. **No research data was collected; counts are
unchanged.**

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
| Bounds | not yet defined; there is no collector |
| Quota/backoff | rate limit recorded `UNKNOWN`; the context says *"throttle conservatively; no limit is invented"* |

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

## 4. Real data

### Was the official API reachable?

**Yes** — `api.stackexchange.com/2.3/info?site=stackoverflow` returned HTTP 200
from this environment. Earlier missions' failures were the WebFetch tool, not the
network.

**So acquisition is not blocked by the environment.** It is blocked by there being
no collector.

| | |
|---|---|
| Requests for research data | **0** |
| RawRecords / NormalizedRecords | **0 / 0** |
| Record kind | none created |
| Revisions / idempotency | not reached |

---

## 5. Signals, Claims, Evidence

**None, and none was designed.** The Signal semantics work (§26–§32 of the brief)
depends on seeing real question data — what tags look like, whether a
deterministic problem-pattern cohort is achievable at all without semantic
inference — and inventing it against imagined data would be the opposite of what
those sections ask for.

| | |
|---|---|
| Signals | 0 |
| OBSERVED Claims | 0 |
| Evidence rows | 0 |
| Observation category, independence, reliability, scorability | not reached |

---

## 6. Boundaries

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
| RawRecords / NormalizedRecords | 23 / 23 | 23 / 23 |
| Signals / Claims / ClaimRevisions / Evidence | 8 / 8 / 8 / 8 | 8 / 8 / 8 / 8 |
| ReliabilityAssessments | 1 | 1 |
| Opportunities / Embeddings / Scores | 0 | 0 |

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

## 7. Why this mission stopped where it did

The brief's §11 says not to split automatically, and it is right that the
foundations exist. But the remaining work is a collector, a **new record kind** for
a community-content document, a normalizer, a Signal semantic that has to be
designed against real data, a deterministic extractor with hard negatives, a claim
template and an evidence path. TED needed Missions 1.15.7 through 1.15.11 for the
equivalent, and each of those found something that changed the design.

**Producing that quickly would have meant producing it without the care every
comparable mission had.** The review is the part that gates everything and is
finished; the implementation is the part that benefits from being done properly.

Stated as its own outcome rather than claimed as one of §37's four, because the
honest shape of this result is *governance complete, implementation not started*.

---

## 8. Next

**Mission 1.18.1 — Stack Exchange questions collector and normalizer.** Everything
it needs is in place: eligible, resource-ready, route-bound, field-minimised,
attribution configured, API reachable. It should stop after real bounded
acquisition and normalization, and leave the Signal design to a mission that can
look at real questions first.

**Then the Signal question, which is the genuinely hard one** and which
§27 of this brief framed correctly: a tag identifies a subject, not a problem.
`python` is not a cohort. Whether a deterministic repeated-problem cohort exists
without semantic inference is an open question that real data will answer, and
**zero Signals is a legitimate answer** to it.

**And do not deepen Stack Exchange past that.** §49 is right: after it produces
evidence, the next question is which source adds the next genuinely different
dimension. `desire` still has no approving source, and `problem` will then have
exactly one substantive one.
