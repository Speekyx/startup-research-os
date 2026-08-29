# Mission 1.3 — Completion Report

**Mission:** Source Review Completion & First Collector-Eligible Sources
**Sprint:** 1
**Date:** 2026-08-29
**Branch:** `sprint-1/mission-1.3`
**Outcome:** 13 sources re-reviewed · 6 verdicts changed · **3 `APPROVED_WITH_CONDITIONS`** · **0 collector-eligible**
**Introduces:** migration `0006_review_conditions`, `ConditionVerification`, review versioning in the catalog, [`source-review-results-v1.md`](../data/source-review-results-v1.md), [`source-human-review-queue-v1.md`](../data/source-human-review-queue-v1.md)

---

## 1. Review methodology

Every source was assessed against the **unchanged** Mission 1.0 use case:
automated collection of public content by a **commercial multi-tenant SaaS**,
for storage, derived analytics and LLM processing. Narrowing it would have made
approvals easier and the approvals meaningless.

Each source was reviewed by retrieving its current primary documentation —
terms of service, developer terms, API terms, licensing pages — and assessing
eleven activities separately. Model recall was not used as evidence; where a
document could not be retrieved, that is recorded as a limitation rather than
filled in.

Three rules governed the whole round:

**Technical possibility is not permission.** An endpoint that responds proves
nothing about whether the assessed use is authorised.

**No circumvention.** Two sources served bot checks or were unreachable. Neither
was bypassed, and neither absence was treated as a licence to scrape instead.

**Silence is not permission.** Where documents did not address an activity, the
recorded value is `NOT_ADDRESSED` and the source stays blocked.

## 2. Documentation consulted

| Source | Document retrieved |
|---|---|
| World Bank | Data Catalog — Data Access and Licensing |
| Eurostat | Copyright notice and free re-use of data |
| FRED | FRED® API Terms of Use *(HTTP 403 in Mission 1.0; retrieved this time)* |
| Hacker News | Official API documentation **and** Y Combinator Terms of Use |
| GitHub | GitHub Acceptable Use Policies §7 |
| Stack Exchange | API Terms of Use *(ToS and AI policy blocked — see §15)* |
| YouTube | YouTube API Services Developer Policies |
| Product Hunt | Product Hunt API v2 documentation |
| Apple App Store | iTunes Search API (Performance Partners) |
| Google Play | Google Play Developer API |
| Reddit | Reddit Data API Wiki *(policy documents unreachable — see §15)* |
| Google Trends | Google Trends API alpha announcement |
| TikTok | TikTok Research Tools eligibility |

## 3. Review versioning

Every source now carries a **two-version review history**. Mission 1.0's review
became version 1 and was not modified; Mission 1.3's is version 2. Older
versions are marked `superseded_at` in the database and remain readable.

The catalog format gained a `reviews` list, replacing the single `review`
object. The old shape still loads as a one-entry history, so an older catalog
means the same thing it always did.

Why it matters, stated once: the useful record is not "the verdict is X". It is
"Mission 1.0 concluded X, Mission 1.3 found Y, because document Z became
available". Overwriting destroys exactly the part a reader needs in order to
trust the current verdict.

## 4. Source-by-source results

Full detail: [`source-review-results-v1.md`](../data/source-review-results-v1.md)
and the rendered [`source-catalog-v1.md`](../data/source-catalog-v1.md).

| Source | 1.0 → 1.3 | Why |
|---|---|---|
| **World Bank** | `REQUIRES_REVIEW` → **`APPROVED_WITH_CONDITIONS`** | CC-BY 4.0 is the default licence and permits commercial use with attribution. Conditions exist because Microdata and third-party datasets on the same platform do not |
| **Eurostat** | `REQUIRES_REVIEW` → **`APPROVED_WITH_CONDITIONS`** | Commercial reuse authorised with acknowledgement, no written licence needed. Conditions cover the enumerated exclusions — notably non-EU/EFTA country data |
| **FRED** | `REQUIRES_REVIEW` → **`APPROVED_WITH_CONDITIONS`** | Terms retrieved this time. Licensed, with an exact mandatory notice and a real carve-out for third-party copyrighted series |
| **YouTube** | `REQUIRES_REVIEW` → **`PROHIBITED`** | The Data Aggregation policy forbids aggregating API data across channels one does not own, which is precisely this use case |
| **GitHub** | `REQUIRES_REVIEW` → **`RESTRICTED`** | §7 is an allowlist — open-access research and archival — and applies regardless of API or scraping. Commercial proprietary analytics is in neither |
| **Google Play** | `REQUIRES_REVIEW` → **`RESTRICTED`** | The Developer API manages your own apps. No documented mechanism returns third-party listing or review data |
| Hacker News | `REQUIRES_REVIEW` (held) | Scraping now clearly `NOT_PERMITTED`; the official API is separately authorised, but commercial derived analytics is unaddressed |
| Stack Exchange | `REQUIRES_REVIEW` (held) | Attribution established as mandatory; commercial and AI use governed by documents that could not be retrieved |
| Reddit | `REQUIRES_REVIEW` (held) | Rate limit now documented (100 QPM free tier); the three governing policies unreachable from this environment |
| Google Trends | `REQUIRES_REVIEW` (held) | An official API now exists — in alpha, by application, terms unpublished |
| Product Hunt | `RESTRICTED` (held) | Documentation states twice that the API must not be used for commercial purposes |
| Apple App Store | `RESTRICTED` (held) | The public search API is an affiliate mechanism for promoting store content |
| TikTok | `PROHIBITED` (held) | Research Tools require non-commercial status and an eligible institution |

**Six verdicts changed: three raised, three lowered.** The three that moved down
are the load-bearing result of the mission — YouTube, GitHub and Google Play were
all open questions, and each turned out to have a published policy that excludes
this use case rather than one that permits it.

## 5–10. Eligibility results by state

| State | Sources | Collector-eligible |
|---|---|---|
| `APPROVED` | — | — |
| `APPROVED_WITH_CONDITIONS` | world-bank, eurostat, fred | **no** — conditions unsatisfied |
| `RESTRICTED` | product-hunt, github, apple-app-store, google-play | no |
| `REQUIRES_REVIEW` | reddit, hacker-news, stack-exchange, google-trends | no |
| `PROHIBITED` | youtube, tiktok | no |

**Zero collector-eligible**, run through the canonical gate rather than declared.

That is not a contradiction with three approving reviews. `APPROVED_WITH_CONDITIONS`
says a collector **may be designed**; every condition those three carry is
currently unsatisfied because the capabilities they require do not exist. The
three are blocked by *exactly one* reason each — their unsatisfied conditions —
with every other gate condition cleared. That is the §24 mechanism working, and
a test asserts it.

**§32's bootstrap set is partly unmet, and was not forced.** Economic/official
data is covered. Developer/technical community is not: GitHub is `RESTRICTED`,
Hacker News and Stack Exchange remain open questions. User discussion is not:
Reddit remains an open question. The brief says a category may remain
unavailable, and one does.

## 11. Retention implications

**The YouTube 30-day override is retained.** It was re-verified against the
current Developer Policies and holds: Non-Authorized Data must not be stored
beyond 30 days, and other stored data must be deleted or refreshed after 30
calendar days. It is kept even though YouTube is now `PROHIBITED` — a verified
fact costs nothing to keep, and removing it would lose it.

No new override was created. The three approving sources are economic statistics
and the project baseline (30 days raw, 365 normalized) applies unchanged.

## 12. Attribution implications

All three approving sources require attribution, and each requires a different
thing:

- **World Bank** — credit plus a statement of any modifications, including
  translations.
- **Eurostat** — the dataset DOI and the access date; modifications stated with
  a non-responsibility disclaimer.
- **FRED** — an exact sentence, verbatim: *"This product uses the FRED® API but
  is not endorsed or certified by the Federal Reserve Bank of St. Louis."*

All three are captured as the `attribution-surface` / `fred-endorsement-notice`
conditions, so no collector can run before a surface exists that can display
them.

## 13. Authentication and vendor approval

| Source | Required next action | Taken? |
|---|---|---|
| FRED | API key (`FRED_API_KEY`) | not configured |
| Reddit | Request Data API access; establish commercial eligibility | **not contacted** |
| Product Hunt | Request commercial permission from `hello@producthunt.com` | **not contacted** |
| Hacker News | Ask `api@ycombinator.com` about commercial derived analytics | **not contacted** |
| Google Trends | Apply to the alpha programme | **not submitted** |
| Stack Exchange | Determine whether Stack Data Licensing is the required route | not pursued |

§37 asks for the required action to be *recorded*, not taken. No message was
sent and no agreement was entered.

## 14. Data-minimisation profiles

Defined for the three approving sources, all of which are numeric economic
series (§39). Needed: indicator/series identifier, value, period, unit,
geography, dataset licence. **Not needed and not to be requested:** any personal
data, any user identifier, any microdata record.

`PersonalDataRisk` is `NONE_EXPECTED` for all three. That is not a coincidence
and not a workaround — they are the sources where the personal-data question
does not arise, which is part of why they were the ones that could be approved
under a still-unresolved jurisdiction question (§38, H-12).

## 15. Human-review queue

[`source-human-review-queue-v1.md`](../data/source-human-review-queue-v1.md) —
twelve items, each with the exact document, the exact question and the exact
next action. No entry says "ask a lawyer" without saying what to ask.

Two are retrieval failures worth naming precisely, because each has a different
cause and neither is a claim about the platform:

- **Reddit (H-1):** `redditinc.com` is blocked by *this environment's* browsing
  policy. The documents were named but not read.
- **Stack Exchange (H-3):** `stackoverflow.com` served an anti-bot interstitial
  for the ToS and AI-policy paths. Not bypassed (§8).

## 16. Orchestrator impact

Verified against the loaded registry. The planner reads
`registry.source_eligibility` and reports:

```text
eligible sources: (none)
ACQUISITION: no source has passed the governance gate (13 registered, 0 collector-eligible)
  eurostat (APPROVED_WITH_CONDITIONS): review conditions not satisfied: …
  apple-app-store (RESTRICTED): policy review is RESTRICTED
dispatchable jobs: ()
```

The distinction §41 asks for holds: an approving source is blocked by its named
conditions, not by its state, and the reasons differ per source. Even if a
source became eligible, no acquisition job could run — **eligible** and
**collector implemented** are different, and neither exists.

## 17. Tests

`services/acquisition/python/tests`: **68 tests**, up from 40. Twenty-eight new,
covering review versioning, the mutation-resistance of earlier reviews, that a
changed verdict cites evidence retrieved for it, conditional eligibility in both
directions, stale-review fail-closed, Python↔SQL agreement, the retained YouTube
override, zero `collector_enabled`, zero `raw_records`, and the absence of any
collector or data-fetching client.

The test worth naming is
`test_an_approving_review_is_still_blocked_by_its_conditions`. It asserts each
approving source is blocked by *exactly one* reason and that the reason is its
conditions — so a future change that accidentally clears the condition gate
fails loudly instead of quietly making three sources collectable.

## 18. CI and validation

New drift check: `render_review_results.py --check`. `quality-gates.md` §1
records eight new gates.

Every gate below was run and passed, against a database **rebuilt from empty**:

| Check | Result |
|---|---|
| `migrate --apply --seed` from empty | **6 migrations**, 2 seeds |
| `run_python_tests.py` (zero-dep) | 310 tests, 5 packages |
| `run_pytest_suites.py` | all 6 packages |
| `validate_schema.py` | 8 invariant groups, **31 tables** |
| `validate_source_registry.py` | 13 sources, 14 evidence records, 0 warnings |
| `validate_evidence_aggregation.py` | 8 checks, 0 warnings |
| `assert_registry_grants_nothing.py` | 13 registered, **0 eligible, 0 enabled, 0 raw records** |
| `sros-source render --check` | catalog in sync |
| `render_review_results.py --check` | results in sync |
| Python ↔ SQL eligibility | **0 divergences across 13 sources** |
| `ruff` / `mypy` (7 packages) | clean; 84 source files |
| `tsc`, `eslint`, `next build`, TS conformance | clean; 21 tests |

## 19. Issues found

**A schema gap, documented before it was closed (§45).** Review conditions were
a `TEXT[]` of prose — readable, unevaluable. Adequate while every review was
blocking anyway; useless the moment one approved. Migration `0006` gives each
condition a row with a stated verification kind. The prose column stays as the
reviewer's summary.

**A real bug in the deterministic evidence id.** `_row_id("evidence", source,
url, title)` did not include the review version, so a re-review citing the same
URL re-parented the Mission 1.0 row instead of creating a new one — leaving the
new review with no evidence, which the SQL gate then blocked on for a reason
that was not true. **Found by the Python↔SQL agreement check**, which is exactly
what §29 asks that check to do. Fixed; the same document cited by two reviews is
now two records with two retrieval dates.

**A lost grant.** `DROP VIEW` discards the view's privileges, so recreating
`registry.source_eligibility` in migration 0006 silently removed the runtime
role's SELECT. The orchestrator failed on its next plan with *permission denied*.
Re-granted in the same migration, with a comment saying why.

**The local stack went down mid-mission.** Docker Desktop stopped, which
manifested as a hung migration rather than a clear error. Restarted; the
non-fatal `sailor-ingest.sock` warning it printed on startup is unrelated to
this project.

**Vocabulary correction.** Nine reviews were drafted with severity words for
`PersonalDataRisk` (`LOW`/`MEDIUM`/`HIGH`). The contract vocabulary is a
*classification* — `NONE_EXPECTED`, `PSEUDONYMOUS`, `IDENTIFIABLE`,
`SENSITIVE_POSSIBLE`, `UNKNOWN` — which describes what kind of data may be
present rather than how bad it would be. Corrected to the contract values.

## 20. Remaining blockers

| Blocker | Status |
|---|---|
| **Collector conditions unsatisfied** | 9 conditions across 3 sources. Each needs a capability that does not exist |
| **Vendor actions outstanding** | 5 sources need a request, application or agreement (§13) |
| **Calibration** | Open. No `CALIBRATED` profile; production scoring unavailable |
| **D-08** | Open. Recomputation policy |
| **D-12** | Open. No embeddings, no NLP, no semantic deduplication — untouched |
| **A-12** | Open. `MarketScope` untouched |
| **Opportunity identity resolution** | Open |
| **Jurisdiction / GDPR** | Open (H-12). Requires legal input |

**Nothing new opened.**

## 21. Readiness for Mission 1.4

Ready. The database rebuilds from empty, every gate is green, and the review
round leaves a defensible starting position: three sources whose terms permit
this use case with enumerated conditions, and nine machine-checkable conditions
that say precisely what a first collector would have to be able to do.

What a next mission cannot assume: that any source is collectable today. None
is.

---

## Explicit answers

| Question | Answer |
|---|---|
| How many sources were reviewed? | **All 13**, each with a new review version |
| How many changed status? | **6** — 3 raised, **3 lowered** |
| Which sources are collector-eligible? | **None** |
| Which remain blocked? | All 13 |
| Why is each blocked? | 3 by unsatisfied conditions; 4 `RESTRICTED`; 4 `REQUIRES_REVIEW`; 2 `PROHIBITED`. Per-source reasons in §4 and the results document |
| Did any source become APPROVED without authoritative evidence? | **No.** None reached `APPROVED` at all. The three approving reviews each cite a retrieved first-party licensing or terms document |
| Were unofficial/private endpoints treated as acceptable? | **No.** The Google Trends undocumented endpoints remain explicitly excluded; two blocked documents were not bypassed |
| Are retention constraints mechanically represented? | **Yes.** The YouTube 30-day override is stored, re-verified, and resolved by `min()` so it can only shorten |
| Are review histories preserved? | **Yes.** Two versions per source; version 1 unmodified, superseded in the database, asserted by tests |
| Are data-minimisation profiles defined? | **Yes**, for the three approving sources (§14) |
| Did any collector get implemented? | **No**, and a test asserts no collector module and no data-fetching client exists |
| Was any platform research data collected? | **No.** Only official documentation *about* the sources was read. `raw_records` is empty, asserted in CI |
| Is Evidence Aggregation still uncalibrated? | **Yes.** Untouched |
| Is production scoring still blocked? | **Yes.** No `CALIBRATED` profile, no `services/scoring` implementation |
| Is D-12 still open? | **Yes.** No embeddings, no NLP, no clustering |
| Is Mission 1.4 safe to begin? | **Yes** |

## Mission boundary

Stopped here, as §49 requires. **Mission 1.4 was not begun.** No collector was
implemented, no platform content was collected, no technical restriction was
bypassed, and `collector_enabled` is false for all thirteen sources.

The honest one-line summary: three sources now have terms that permit this use
case, nobody can collect from them yet, and the nine conditions standing in the
way are written down precisely enough to build against.
