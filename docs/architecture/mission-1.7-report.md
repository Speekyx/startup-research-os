# Mission 1.7 — Consumer, Entertainment, Social and Emerging-Trend Source Expansion

**Date:** 2026-08-30
**Branch:** `sprint-1/mission-1.7`
**Status:** Complete. No collector implemented, no platform content collected.

**Deliverables:**
[`source-expansion-consumer-social-v1.md`](../data/source-expansion-consumer-social-v1.md) ·
[`source-signal-coverage-v1.md`](../data/source-signal-coverage-v1.md) (generated) ·
[`source-portfolio-v1.md`](../data/source-portfolio-v1.md) ·
[`source-coverage-gap-analysis-v1.md`](../data/source-coverage-gap-analysis-v1.md) ·
[ADR-017](adr/ADR-017-source-signal-coverage.md) ·
migration `0010_source_signal_coverage.sql`

---

## 1. Source discovery methodology

Twenty-six platforms examined, fourteen registered. Every governance verdict
rests on a document retrieved from the source's own site on 2026-08-30.

Search and community discussion were used to **find** candidate documents and
never to establish what one says. The evidence type enum has no value for a blog
post, so the registry structurally cannot store one as the basis of an approval
— which is the rule doing work rather than being quoted.

Where a document could not be retrieved, the source carries **no evidence**, the
verdict is `REQUIRES_REVIEW`, and the exact document is named. Four sources are
in that state for environmental reasons and two more remain there from Mission
1.3. No alternative access route was considered for any of them: difficulty
obtaining terms is not a reason to bypass them.

## 2. Opportunity and signal philosophy

The catalog after Mission 1.3 held thirteen sources, and the three that reached
an approving state were all macroeconomic statistics agencies. That is the
honest outcome of a real review, and it produces a research engine that can only
see what national accounts can see.

This round asked which signal families the system can see **at all** — and the
second half of that question, which it cannot, turned out to be the finding.

## 3. New source candidates

Fourteen registered:

| Family | Sources |
|---|---|
| news | `gdelt` |
| knowledge | `wikimedia-pageviews`, `openalex` |
| developer | `npm-registry`, `pypi`, `huggingface` |
| social | `bluesky`, `x-twitter`, `meta-instagram` |
| gaming | `steam` |
| creator | `twitch` |
| community | `discord` |
| product_discovery | `pinterest` |
| content_platform | `spotify` |

`gaming`, `creator` and `knowledge` are new families, added as registry rows
rather than by migration of an enum (Ontology V2 §14.3).

**Two candidates were deliberately not registered.** Mastodon and Lemmy are
federated: one protocol, thousands of independently-governed instances, no
single terms document. §16 forbids flattening that into "Mastodon is allowed",
and the registry's unit is a source whose review can *conclude*. Registering
them would create identities whose review never can. The modelling gap is §26
below and **H-13** in the queue.

## 4. Re-reviewed existing sources

One verdict was re-reviewed against a current document: `google-trends`, review
version 3. The official Trends API remains an **alpha** — announced as such on
Google's own developer blog — so access is granted rather than open and the
verdict holds at `REQUIRES_REVIEW`.

That is §8's case of new authoritative evidence **confirming** rather than
changing a verdict, and it is recorded as a new review version because
substantive work was done (§27).

`reddit` and `stack-exchange` were retried and remain unreachable from this
environment, for exactly the reasons Mission 1.3 recorded. Their reviews were
**not** re-versioned: a failed retrieval is not substantive review work, and
issuing a new version for it would inflate the history with a round that
established nothing. The retry itself is recorded in the catalog's known
limitations, because a blocker confirmed to persist is worth more to the next
reviewer than silence.

The remaining ten existing sources were not re-examined and say so: the
generated results document now distinguishes sources carrying a review from this
round from those carrying an earlier verdict, because **a verdict that was not
revisited is not a verdict that was reconfirmed**.

## 5. Official documentation evidence

Forty evidence records across the catalog, twenty-nine of them cited by current
reviews. The documents that decided a verdict:

| Source | Document | What it settled |
|---|---|---|
| `gdelt` | Terms of Use | "unlimited and unrestricted use for any academic, commercial, or governmental use of any kind without fee" |
| `wikimedia-pageviews` | WMF Terms of Use (2023-06-07) | the licences "do allow commercial uses"; API use bound by the User-Agent, Robot and Etiquette policies |
| `wikimedia-pageviews` | Rate limits page | 10/min unidentified, 200/min with a User-Agent, 2000/min established |
| `openalex` | API reference | "all data is CC0"; free tier, key raises the budget tenfold, pay-as-you-go above |
| `npm-registry` | Open Source Terms (2022-03-10) | website automation prohibited; "You may replicate data from the Public Registry using the Public APIs" |
| `pypi` | Terms of Service (2025-02-25) | API abuse and personal-information harvesting prohibited by name; automated access is not |
| `spotify` | Developer Terms (2025-05-15) | may not store, aggregate or create databases; may not train a model; no robots or spiders |
| `steam` | Web API Terms | grant is to "distribute Steam Data to end users for their personal use via your Application"; 100,000 calls/day |
| `meta-instagram` | Platform Terms (2026-02-03) | sale or licensing of Platform Data prohibited; app review required |
| `bluesky` | Terms of Service (2025-08-14) | **silent** on automated access, the API and AI training |
| `huggingface` | Terms of Service (2022-09-15) | **silent** on automated access and commercial reuse of Hub metadata |
| `twitch` | API reference | OAuth 2.0 and a registered app — the ACCESS model, not the permission |
| `google-trends` | Trends API announcement | still alpha |

## 6. Source-by-source verdicts

| State | Count | Sources |
|---|---|---|
| `APPROVED` | **0** | — |
| `APPROVED_WITH_CONDITIONS` | **8** | `eurostat`, `fred`, `gdelt`, `npm-registry`, `openalex`, `pypi`, `wikimedia-pageviews`, `world-bank` |
| `RESTRICTED` | **6** | `apple-app-store`, `github`, `google-play`, `meta-instagram`, `product-hunt`, `steam` |
| `REQUIRES_REVIEW` | **10** | `bluesky`, `discord`, `google-trends`, `hacker-news`, `huggingface`, `pinterest`, `reddit`, `stack-exchange`, `twitch`, `x-twitter` |
| `PROHIBITED` | **3** | `spotify`, `tiktok`, `youtube` |

Five of the fourteen new candidates reached an approving state. **None became
collector-eligible** — §26 explains why, and it is not a technicality.

### The two results worth reading twice

**Bluesky and Hugging Face are the most technically accessible sources in the
catalog and both are blocked.** Bluesky publishes a public firehose its own
documentation says needs no API key; Hugging Face publishes open endpoints with
exact numeric rate limits per tier. Both are `REQUIRES_REVIEW` because their
terms address **none** of the assessed activities, and silence is not permission
(`source-registry-v1.md` §1 rule 2). The distance between "we can reach this
trivially" and "we may use it" is the entire point of the registry.

Hugging Face has a near-miss that had to be resisted. Its ToS **does** grant
broad rights — public repositories grant every user a licence to use, reproduce
and make derivative works. That grant runs between *users* and covers repository
*content*; what this system would collect is platform metadata (download counts,
likes, trending placement), which no clause mentions. Reading the content grant
as covering metadata would be inferring permission from an adjacent one — the
move §12 forbids by name.

**Steam is the expensive verdict.** The terms were read; they permit automated
API access with a key, storage in a disclosed country, and distribution to end
users through an Application. Our use is none of those. `RESTRICTED`, and the
consequence is that `competition` and `collection` — which Steam is nearly alone
in exposing — have no usable source at all.

## 7. AI and LLM processing implications

§10 asks that "AI use" not be treated as one activity. The documents themselves
rarely make the distinction:

| What the documents did | Count |
|---|---|
| Prohibited model training **by name** | 1 (`spotify`) |
| Granted use broadly enough to cover processing, without mentioning AI | 2 (`gdelt`, `openalex`) |
| Said **nothing** about model processing | 7 |
| Could not be read | 4 |

**Ten of fourteen are `NOT_ADDRESSED`.** The distinctions §10 asks for —
training versus embeddings versus inference versus summarisation — are almost
never drawn by source documents, and drawing them in the review would invent
structure the evidence does not have.

The two `PERMITTED` values rest on general grants ("any kind"; CC0) rather than
AI-specific language, and each review says so in its notes rather than burying
it. A grant written before this question was current may not have contemplated
it, and a reader should be able to see that the permission is general.

The instructive case is `huggingface`: an AI platform whose 2022 Terms of
Service do not address AI processing of its own platform metadata.

## 8. Storage and retention implications

No source imposed a retention limit stricter than the project baseline, so no
new `source_retention_policies` override was written. The baseline stands: 30
days raw, 365 normalized.

Storage is `NOT_ADDRESSED` on seven of the fourteen. Where nothing is documented,
nothing was invented (§13).

One documented obligation has no home in the current model, and it is recorded
rather than solved: Bluesky's Terms acknowledge that deletion **may not
propagate** across the network. A downstream holder of a deleted post is exactly
the case that sentence describes, and it creates an obligation the Terms do not
specify. **H-18.**

## 9. Commercial-use implications

| Verdict | Count | Notable |
|---|---|---|
| `PERMITTED` | 3 | `gdelt`, `wikimedia-pageviews`, `openalex` |
| `PERMITTED_WITH_CONDITIONS` | 2 | `npm-registry`, `meta-instagram` |
| `NOT_PERMITTED` | 1 | `spotify` |
| `NOT_ADDRESSED` | 3 | `pypi`, `steam`, `huggingface` |
| `NOT_ASSESSED` | 5 | the four unreachable documents, plus `twitch` |

**`npm-registry` and `pypi` share a verdict and not a footing**, and this is
worth stating because the labels are identical. npm *grants* replication through
the public API in as many words. PyPI *prohibits* a short list of named misuses
and says nothing about whether a commercial product may be built on the data —
its `commercial_use` is `NOT_ADDRESSED`. The approving state there rests on the
absence of a prohibition that reaches us plus a documented API, which is
materially weaker than a grant.

## 10. Personal-data implications

Six of fourteen carry `IDENTIFIABLE` or higher: `bluesky`, `discord`,
`meta-instagram`, `pinterest`, `x-twitter`, `openalex`.

The last is the surprising one. OpenAlex is CC0 — the strongest licensing
position in the catalog — and it is a corpus of **named researchers with
institutional affiliations**. A CC0 licence settles copyright and says nothing
about privacy. Recording it as `NONE_EXPECTED` because the licence is permissive
would conflate two unrelated questions.

`jurisdiction_review_required` is true on every source in the catalog and no
code sets it false. Nothing here assessed GDPR applicability (**H-12**, still
open).

## 11. Authentication and access models

| Model | Sources |
|---|---|
| None documented | `gdelt`, `wikimedia-pageviews` (UA required, not auth), `openalex`, `npm-registry`, `pypi`, `bluesky`, `huggingface` |
| API key | `steam` |
| OAuth + registered app | `twitch`, `discord`, `spotify`, `x-twitter`, `pinterest`, `meta-instagram` |
| Vendor approval / app review | `meta-instagram`, `pinterest`, `x-twitter` |

Nothing here obtained a credential, submitted an application or accepted an
agreement (§44). Every required next action is in the queue.

Rate limits are recorded **only where documented**: `wikimedia-pageviews`
(200/min), `huggingface` (500 API requests per 5-minute window, anonymous),
`steam` (100,000/day). Elsewhere `UNKNOWN`, including `gdelt` and `pypi`, whose
own documentation publishes none. An invented number is worse than none because
a collector would trust it.

Registering Steam surfaced a small API gap: the gateway serialised `requests`
and `period_seconds` but not `daily_quota`, so a documented 100,000-calls-a-day
limit was served with every number null — which reads as "no limit is
documented" and is the opposite of what the registry holds. Fixed.

## 12–13. Signal and behaviour coverage taxonomy

ADR-017 and the gap analysis carry the reasoning. The short version:

**Eleven of the sixteen signal families §4 names already exist verbatim in
`user_motivation`**, and **all seventeen behaviours §5 names are Ontology V2
§3.4's canonical list unchanged**. So behaviour coverage introduces **no new
vocabulary at all** and references `user_behavior` directly.

Signal families needed their own registry — a source does not *have* a
motivation, and coupling the two would mean every new motivation silently
appeared on every source's profile. But each entry records the canonical entry
it projects, so the correspondence is data rather than a coincidence of
spelling. Five record `NULL`: four because no counterpart exists, and `desire`
because its counterpart is the **closed enum** demand-signal family, which a
registry pointer structurally cannot reference. Manufacturing a registry so the
pointer would resolve would have reclassified a closed enum as extensible — a
material ontology change, made silently, to satisfy a foreign key.

Migration 0010 also loaded the canonical entries the ontology always specified
and 0004 never seeded: sixteen of seventeen behaviours, fourteen of seventeen
motivations.

## 14–20. The diversity matrix and what it shows

[`source-signal-coverage-v1.md`](../data/source-signal-coverage-v1.md) is
generated from the catalog and CI-checked, so it cannot drift.

### Coverage, counting only sources in an approving state (§23)

| | |
|---|---|
| **Covered** (2+ sources) | `trend` (8), `commercial` (5), `discovery` (4), `curiosity` (3), `developer_activity` (3), `learning` (3) |
| **One source only** | `entertainment`, `social`, `community` |
| **UNCOVERED** | `desire`, `creativity`, `competition`, `collection`, `personalization`, `status`, `problem` |

**Seven of sixteen families have no usable source.** Two observations about
that list:

**`problem` is uncovered.** The system Mission 1.7 was told not to become — a
business pain detector — is not currently something it *could* become. Every
source exposing stated problems is blocked or pending. Worth saying plainly,
because the brief's framing assumes pain coverage is the default needing
balance, and here it is not the default and does not exist.

**`personalization` and `status` have no registered source at all**, blocked or
otherwise. Every other uncovered family is blocked on a verdict; these two are
blocked on the catalog containing nothing that exposes them. That is a discovery
gap rather than a governance one, and the only one of its kind.

### Behaviour coverage is worse than family coverage

Of seventeen canonical behaviours, approving sources record **seven**:

```text
recorded    automate  collaborate  consume  create  discover  discuss  learn
missing     buy  collect  compare  compete  customize  play  predict  sell  share  track
```

The first row is things people *read, write or install*. The second is things
people *do*. `play`, `compete`, `collect` and `customize` — the four carrying
the desire-driven categories §24 asks about — have no approving source, and
neither does `share`.

### Portfolio balance (§40)

| | Registered | Approving |
|---|---|---|
| `economic_data` | 3 of 27 (11%) | **3 of 8 (37%)** |
| `knowledge`, `news`, `developer` | 9 | 5 |
| `social`, `community`, `gaming`, `creator`, `app_store` | **11** | **0** |

**Every consumer-facing family is registered and none is approving.** The
registered figure looks healthy and is the less meaningful one; what the system
may actually collect from is the second column.

This is the bias §40 asked to be reported rather than the one it hoped for, and
it is a fact about platform terms rather than about the review.

## 21. Major gaps

1. **Behaviour, entirely.** Ten of seventeen behaviours have no approving source.
2. **Gaming and creator have nothing**, not even a promising candidate — Steam
   is `RESTRICTED` and Twitch's agreement could not be read.
3. **User discussion has nothing.** Every source of people describing problems
   in their own words is blocked or pending.
4. **`personalization` and `status`** are not exposed by anything registered.
5. **Federated protocols cannot be modelled** (H-13).

## 22. Alternatives to blocked sources

§41 asks for lawful alternatives rather than attachment to brands. What was
actually found:

| Blocked | Alternative found | Status |
|---|---|---|
| Reddit, X (user discussion) | **Bluesky** — open protocol, public firehose, no key | Blocked on silence, not refusal. One question would settle it |
| Google Trends (search interest) | **Wikimedia pageviews** — direct attention measure, documented limits | **Approving.** The one genuine substitution this round produced |
| YouTube, TikTok (culture and trend) | **GDELT** — theme and entity volume over time | **Approving**, though it measures coverage rather than behaviour |
| Scholarly and emerging topics | **OpenAlex** — CC0 | **Approving** |
| GitHub (developer activity) | **npm registry**, **PyPI** | **Approving** |
| Steam (gaming) | **nothing** | No lawful alternative exposes player behaviour |
| YouTube, TikTok, Twitch (creator) | **nothing** | Partial only, via `huggingface` model publication, itself pending |

Four real substitutions, and two need groups where the honest answer is that no
alternative exists.

## 23. Human and vendor action queue

[`source-human-review-queue-v1.md`](../data/source-human-review-queue-v1.md)
now holds **24 items**, twelve added here. Nobody was contacted, no application
submitted, no agreement accepted, no plan purchased (§44).

The three highest-value:

- **H-18 (Bluesky)** — does a developer terms document exist separate from the
  user ToS? One answer settles the most open social platform available.
- **H-22 (five approved sources)** — compliance configuration for `gdelt` and
  `wikimedia-pageviews` would move two sources from approving to eligible
  without a line of collector code. Configuration, not code.
- **H-13 (federated)** — decides whether the registry can ever hold an open
  social protocol.

## 24. Source portfolio and 25. Collector priority

[`source-portfolio-v1.md`](../data/source-portfolio-v1.md) groups by need and
gives qualitative tiers (§39 — no fake precision, and these never leave that
document).

**HIGH:** `wikimedia-pageviews`, `gdelt`. Both approving, both free, both
needing no credential, and both covering families nothing else covers.
**MEDIUM:** `openalex`, `eurostat`, `npm-registry`.
**LOW:** `pypi`, `fred`.
**BLOCKED:** nineteen of twenty-seven.

**The highest-value next task is not a collector.** Both HIGH sources are
blocked on the same missing thing — a capability that can verify an attribution
obligation — and `source-attribution-display` already exists and describes
itself as shared and parameterised. What the five newly approved sources lack is
a `source-compliance-v1.json` entry. That is what Mission 1.4 did for the
economic three, it is configuration rather than code, and it converts an entire
approving tier into a usable one.

## 26. Registry mutation hardening (§31, §32)

`test-data-isolation-audit-v1.md` §6 named this gap rather than closing it: the
post-suite leak check finds tenant tables by looking for a `workspace_id`
column, so `registry.*` was outside it **by construction**. Three acquisition
modules mutate the registry, one by turning a collector on.

`infrastructure/testing/registry_state.py` closes it. Two design choices matter:

**Content, not counts.** The failure that had to be caught is count-stable —
`UPDATE registry.sources SET collector_enabled = TRUE` moves no row count. Each
row is reduced to `to_jsonb(row)` minus bookkeeping columns and hashed.

**Too strict is a failure mode, not the safe side.** The check proved this on
its own first run: eight conditions came back "changed" after a completely clean
suite, because `satisfied_at` and `satisfaction_reference` are a projection of
the append-only verification log and move whenever it grows. `satisfied` — the
governance fact — was identical in all eight. A check that fails every run is a
check somebody deletes, which lands you back at the permissive failure with
extra steps. The derived columns are excluded, `satisfied` is not, and a test
asserts that boundary **from both sides**.

The two checks partition the tables between them and neither keeps a list: the
tenant check takes every table *with* a `workspace_id`, this one every table
*without*. A table added by a future migration is watched by exactly one of them
from the moment it exists.

### What it found before it had a green run

Not a test bug. `sros-source verify --apply` folds the git-ignored
`infrastructure/compose/.env` into its process and the pytest fixture did not,
so on a machine with `FRED_API_KEY` configured the two disagreed: the CLI
recorded FRED's credential condition `SATISFIED`, and the next `pytest` run
recorded it `UNSATISFIED` and quietly took FRED out of eligibility. Both were
behaving correctly and answering the same question in different environments.
Fixed by folding the same file in the fixture.

### §32 assertions, after the full suite

```text
database unchanged by the run, across 20 tenant tables
global tables unchanged by the run, across 14 tables; 18 appended to 1 append-only table
```

Source ids, review histories, conditions and operational switches all unchanged;
no test-created registry residue. The only growth is the verification log, which
is append-only by design and is the one table permitted to grow.

## 27. Tests and CI

| | |
|---|---|
| New | `test_registry_state.py` — 20 tests, most needing no database |
| Updated | 9 assertions across 4 modules that had frozen the Mission 1.3 catalog |
| New gate | `render_signal_coverage.py --check` in CI |

**Nine stale absolutes were converted to properties**, which is the same class of
defect Mission 1.6.1 §13 catalogued. Each had encoded a snapshot rather than the
rule it was standing in for:

| Was | Is |
|---|---|
| `total == 9` conditions | every condition is attributable, keyed uniquely, and on an approving review |
| `len(review_history) >= 2` | history is ordered, distinct and never rewritten |
| every first review is `mission-1.0` | the *thirteen Mission 1.0 sources'* first reviews are, and every first review is version 1 |
| approving set `== {world-bank, eurostat, fred}` | every approving review declares conditions |
| `superseded == len(catalog)` | `current + superseded == total reviews` |
| families seeded in migration 0004 | families seeded in **any** migration |
| `rate_limit_known` implies `rate_limit_requests` | implies **some** documented dimension — Steam publishes a daily quota and no rate |

The gateway's expected-table list was updated by hand, which is correct: it is
hand-written on purpose so a new table fails until somebody states whether it is
tenant data. These two are global.

### A migration depended on development seed data

Caught by CI, not by me, and the reason is worth recording. Migration 0010
pointed `signal_family` entries at `user_motivation:problem` — an entry written
by `infrastructure/db/seed/0002_registry_seed.sql`, which is **development-only
and runs after every migration**. The foreign key resolved on a machine seeded
months earlier and failed on the first empty database it met.

Every local check passed because every local check ran against an
incrementally-migrated database. The fix is that migration 0010 now inserts all
seventeen motivations and all seventeen behaviours itself, with
`ON CONFLICT DO NOTHING`, so it depends on nothing a seed provides. Verified by
applying all ten migrations to a genuinely empty database — twice, once with
`--seed` and once without — in a scratch database, so the six records were never
at risk.

`validate_schema.py` now asserts it mechanically, with no database: every
`maps_to` target must be inserted by some **migration**, not merely by a seed.
Its first version was wrong in both directions — it printed `ok` before knowing
its own result, and its regex matched quoted pairs inside CHECK constraints, so
it failed on its own baseline. It now parses the INSERT column lists and reads
values by name. **Probed against the exact defect that shipped**, which it
catches and names.

### A validator was conflating two different UNKNOWNs

`validate_compliance_capabilities` required every condition on an approving
review to resolve to something other than `UNKNOWN`. A `HUMAN_CONFIRMATION`
condition resolves `UNKNOWN` **by design** — no verifier can establish one and
none in this repository writes one — so the check would have rejected any
approving review carrying one. That was invisible until now because no approving
review did.

Rejecting them would force every legal obligation into prose, which §28 forbids
by name. The check now separates:

- a condition naming a capability or access restriction that **does not exist**
  — still an error, and still blocking;
- a `HUMAN_CONFIRMATION` condition — reported, still blocking eligibility, not
  an error.

**Probed before being trusted.** Two deliberate violations were injected — a
`CAPABILITY` and an `ACCESS_METHOD` naming something unregistered — and both are
still caught. A validator that has only ever passed proves nothing.

## 28. Existing-data survival (§46)

Verified field by field, not by row count:

```text
six raw records, six normalized records
values 67158348  67382061  67601110  82905782  83092962  83160871
identical to the values Mission 1.6.1 recorded
no float artifact in any payload · all collector_version 1.1.0
every raw record has a normalized row · every normalized row keeps its session
six distinct content hashes · every quality VALID
```

A count would not have noticed a nulled session link, which is exactly how the
Mission 1.6 damage went unnoticed.

## 29. New issues

- **MODEL-01 / H-13** — the registry cannot express a federated source. Three
  resolutions, none free, none decided here.
- **Bluesky's deletion propagation** — an obligation acknowledged by the source
  and specified by nothing (H-18).
- **The `signal_family` registry can drift from `user_motivation`.** Nothing
  forces the projection to stay complete, and it cannot be forced: five entries
  legitimately have none, so "unmapped" cannot be made an error (ADR-017 §Cons).
- **`maps_to_*` is a general facility introduced for one registry.** Every other
  registry carries two columns it never uses.
- **Coverage is a judgment.** `basis` makes it re-checkable, not objective. Two
  reviewers could differ on whether Steam reviews evidence `problem`.

## 30. Remaining blockers

Unchanged: **D-03** (no calibrated profile, scoring unavailable), **D-08**
(which normalized revision downstream should read), **D-10**, **D-12** (NLP and
embeddings), **PROFILE-NOT-CALIBRATED**, **H-12** (jurisdiction and GDPR).

Added: **H-13** through **H-24**.

## 31. Mission 1.8 readiness

**Safe to begin.** The registry is larger, every verdict rests on a retrieved
document, coverage is measurable and CI-checked, global registry state is
test-safe, and the six raw and six normalized records are unchanged.

The most useful first move is **not** a collector: compliance configuration for
`gdelt` and `wikimedia-pageviews` converts the two highest-priority sources from
approving to eligible, and is configuration rather than code.

---

## The questions §51 asks explicitly

| Question | Answer |
|---|---|
| How many sources are registered? | **27** |
| How many new candidates were added? | **14** |
| How many are `APPROVED`? | **0** |
| How many are `APPROVED_WITH_CONDITIONS`? | **8** |
| How many are collector-eligible? | **3** in an environment with capabilities verified and `FRED_API_KEY` set (`world-bank`, `eurostat`, `fred`); **2** without it; **0** from the catalog alone. No new source is among them |
| How many are `RESTRICTED`? | **6** |
| How many are `REQUIRES_REVIEW`? | **10** |
| How many are `PROHIBITED`? | **3** |
| Which sources can provide user-discussion signals? | None usable. `bluesky`, `reddit`, `hacker-news`, `stack-exchange`, `discord`, `x-twitter` are all pending or blocked |
| Which can provide desire/entertainment signals? | `desire`: **none**. `entertainment`: `wikimedia-pageviews` alone |
| Which can provide gaming signals? | **None.** `steam` is `RESTRICTED`, `twitch` unread |
| Which can provide creator signals? | **None.** `youtube` and `tiktok` are `PROHIBITED`, `twitch` unread |
| Which can provide trend/search signals? | `wikimedia-pageviews`, `gdelt`, `openalex`, `npm-registry`, `pypi` and the economic three — the best-covered family, 8 sources |
| Can the portfolio discover opportunities with low Pain Score? | **Partly, and for the first time.** `wikimedia-pageviews` measures attention with no complaint, purchase or review required. It sees interest in a *subject*; it does not see people *doing* things, and 10 of 17 behaviours have no approving source |
| Is X/Twitter usable? | **Unknown.** The Developer Agreement returned HTTP 402 to this environment. Not assessed, not refused |
| Is Reddit usable? | **Unknown**, unchanged. `redditinc.com` still unreachable here |
| Is Steam usable? | **No.** `RESTRICTED`: the grant covers distributing data to end users through an Application, not accumulating and analysing it |
| Is Twitch usable? | **Unknown.** The API docs were read; the Developer Services Agreement could not be |
| Are there viable alternatives when those are blocked? | **For four need groups, yes** — Wikimedia for search interest, GDELT for culture and trend, OpenAlex for emerging topics, npm and PyPI for developer activity. **For gaming and creator, no** |
| Were any collectors implemented? | **No** |
| Was any platform research data collected? | **No.** Only official documentation *about* sources was retrieved |
| Did the existing World Bank records survive unchanged? | **Yes** — six raw, six normalized, values identical to Mission 1.6.1, session links intact |
| Are registry mutations now test-safe? | **Yes.** 14 global tables watched by content; the full suite leaves all of them unchanged |
| Is Evidence Aggregation still uncalibrated? | **Yes.** Untouched. No source carries a reliability weight (§35) |
| Is D-12 still open? | **Yes.** No embeddings, no NLP, no signal extraction |
| Which sources should Mission 1.8 implement first? | `wikimedia-pageviews`, then `gdelt` — but their **compliance configuration** first, which is the cheaper and larger win |
| Is Mission 1.8 safe to begin? | **Yes** |

---

## Validation

**All 10 migrations applied to an empty database, with and without `--seed`** · RLS green · **846 pytest across
6 packages** · 337 zero-dependency · ruff check + format · mypy strict (113
files) · contract generation `--check` · `validate_schema` ·
`validate_source_registry` (27 sources, 29 evidence records, **0 warnings**) ·
`validate_compliance_capabilities` · `validate_evidence_aggregation` ·
`validate_normalization` · `assert_registry_grants_nothing` ·
`sros-source render --check` · `render_review_results.py --check` ·
**`render_signal_coverage.py --check`** · tsc (contracts + web) · eslint ·
`next build`

Post-suite: **20 tenant tables and 14 global tables unchanged**, 18 rows
appended to the append-only verification log.
