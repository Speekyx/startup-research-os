# Source Catalog V1

**Status:** Authoritative record of the initial candidate catalog.
**Catalog version:** 1.1
**Reviewed:** 2026-08-29 by `mission-1.3`
**Governed by:** [`source-registry-v1.md`](source-registry-v1.md)

> **GENERATED FILE.** Rendered from `source-catalog-v1.json` by
> `sros-source render`, and checked in CI. Edit the JSON, not this file.

---

## The assessed use case

Every assessment below is scoped to one use, stated once:

> Automated collection of public content by Startup Research OS, a COMMERCIAL multi-tenant SaaS, for storage, derived analytics and LLM processing to produce opportunity intelligence. Every assessment below is scoped to that use. An assessment does not transfer to non-commercial or academic use, and a permission granted for a narrower purpose does not widen to this one.

An assessment does not transfer. A source that permits academic research has not permitted this, and a permission granted for a narrower purpose does not widen to cover it.

## Summary

| Approval state | Sources |
|----------------|---------|
| `APPROVED` | 0 |
| `APPROVED_WITH_CONDITIONS` | 3 — world-bank, eurostat, fred |
| `REQUIRES_REVIEW` | 4 — reddit, hacker-news, stack-exchange, google-trends |
| `RESTRICTED` | 4 — product-hunt, github, apple-app-store, google-play |
| `PROHIBITED` | 2 — youtube, tiktok |
| `SUSPENDED` | 0 |
| `DRAFT` | 0 |

**Collector-eligible from the catalog alone: 0 of 13.**

This document is the **catalog view**: what the reviews say, with no condition verified. It is generated from a JSON file and committed, so it cannot depend on the machine it was rendered on -- and whether a condition holds depends on what is deployed and configured. A catalog can never assert its own conditions satisfied, so every source carrying one is shown blocked here.

For the environment view -- the same reviews with the verifiers actually run -- use `sros-source eligibility` or `sros-source conditions <source>`. The two can legitimately disagree, and only the second answers *may a collector run here*.

Either way, **no collector exists** and `collector_enabled` is false for every source. Passing the gate says a collector MAY be built.

### Limitations of this review

- Reddit's governing policy documents (Data API Terms, Developer Terms, Responsible Builder Policy) could not be retrieved: redditinc.com is blocked by this environment's browsing policy. Reddit stays REQUIRES_REVIEW with those documents named.
- Stack Exchange's Public Network Terms of Service and Consolidated Responsible AI policy could not be retrieved: stackoverflow.com served an anti-bot interstitial for those paths and this review did not attempt to bypass it (§8).
- No assessment here is a legal opinion. Where a conclusion would require legal judgment, the recorded value is UNCLEAR or NOT_ADDRESSED and human review is required.
- No source data was collected. Only official documentation ABOUT the sources was read.
- Three sources are APPROVED_WITH_CONDITIONS. None is collector-eligible: every condition is unsatisfied because the capabilities they require do not exist yet.

---

## Assessment table

Activities are assessed separately, because their conditions differ. A source may permit automated API access and forbid commercial use, and only a per-activity reading can say so.

| Source | Family | Access | Official API | Auth | Commercial | Automation | Storage | Retention | Redistribution | Rate limits | Personal data | State | Eligible |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `reddit` | community | official api | yes | yes | unclear | conditional | not assessed | not assessed | not assessed | UNKNOWN | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `hacker-news` | community | public api, public web | yes | no | not addressed | conditional | not addressed | not addressed | **not permitted** | documented | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `stack-exchange` | forum | official api | yes | no | unclear | conditional | not addressed | not addressed | unclear | UNKNOWN | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `product-hunt` | product_discovery | official api | yes | yes | **not permitted** | conditional | not addressed | not addressed | not addressed | UNKNOWN | PSEUDONYMOUS | `RESTRICTED` | **no** |
| `github` | developer | official api | yes | yes | **not permitted** | conditional | conditional | not addressed | **not permitted** | documented | PSEUDONYMOUS | `RESTRICTED` | **no** |
| `apple-app-store` | app_store | rss or feed | no | no | conditional | conditional | not addressed | not addressed | **not permitted** | UNKNOWN | PSEUDONYMOUS | `RESTRICTED` | **no** |
| `google-play` | app_store | official api | yes | yes | not addressed | conditional | not addressed | not addressed | not addressed | UNKNOWN | PSEUDONYMOUS | `RESTRICTED` | **no** |
| `youtube` | content_platform | official api | yes | yes | not addressed | conditional | conditional | conditional | **not permitted** | UNKNOWN | PSEUDONYMOUS | `PROHIBITED` | **no** |
| `tiktok` | social | official api | yes | yes | **not permitted** | **not permitted** | **not permitted** | not assessed | **not permitted** | UNKNOWN | IDENTIFIABLE | `PROHIBITED` | **no** |
| `google-trends` | search_trends | official api | yes | yes | not assessed | not assessed | not assessed | not assessed | not assessed | UNKNOWN | NONE_EXPECTED | `REQUIRES_REVIEW` | **no** |
| `world-bank` | economic_data | public api | yes | no | permitted | permitted | permitted | permitted | conditional | UNKNOWN | NONE_EXPECTED | `APPROVED_WITH_CONDITIONS` | **no** |
| `eurostat` | economic_data | public api | yes | no | conditional | permitted | permitted | permitted | conditional | UNKNOWN | NONE_EXPECTED | `APPROVED_WITH_CONDITIONS` | **no** |
| `fred` | economic_data | official api | yes | yes | conditional | permitted | permitted | permitted | conditional | UNKNOWN | NONE_EXPECTED | `APPROVED_WITH_CONDITIONS` | **no** |

---

## Per-source detail

### Reddit — `reddit`

Threaded discussion communities. A primary candidate for PAIN and DESIRE signals because complaints and feature requests are stated in the users' own words.

- **Family:** community
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-29 | `mission-1.0` | `REQUIRES_REVIEW` | 0 |
| 2 ← current | 2026-08-29 | `mission-1.3` | `REQUIRES_REVIEW` | 1 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | reddit-data-api | auth, oauth, account, dev app, approval | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | conditional |
| api use | conditional |
| browser automation | not assessed |
| commercial use | unclear |
| storage | not assessed |
| retention | not assessed |
| redistribution | not assessed |
| derived analytics | not assessed |
| model processing | not assessed |
| personal data handling | not assessed |
| attribution required | not assessed |

**Reviewer notes**

Status unchanged at REQUIRES_REVIEW; the rate limit moves from UNKNOWN to documented, which is a real improvement. The three governing policy documents are named but were not retrieved: redditinc.com is blocked by this environment's browsing policy, so the Data API Terms, Developer Terms and Responsible Builder Policy could not be read. That is an environment limitation, not a statement about Reddit, and it is recorded as such. No fallback to scraping was considered: difficulty obtaining API terms is not a reason to bypass them.

**Open questions**

- Retrieve the Reddit Data API Terms (https://redditinc.com/policies/data-api-terms), the Developer Terms and the Responsible Builder Policy from an environment that can reach redditinc.com.
- Determine whether a commercial multi-tenant SaaS is eligible for free-tier access or requires a separate commercial agreement — the wiki's phrase 'those eligible for free access usage' implies a condition it does not state.
- Determine the data retention and deletion obligations that apply when a Reddit user deletes content, and whether model processing of Reddit content is addressed.

**Official evidence (1)**

- [Reddit Data API Wiki](https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki) — `OFFICIAL_API_DOCS`, retrieved 2026-08-29, section: Rules; Rate limits
  - Use of the Data API is subject to the Responsible Builder Policy, the Developer Terms and the Data API Terms, and the wiki directs prospective users to contact Reddit to request access. Clients must authenticate with a registered OAuth token; traffic not using OAuth or login credentials is blocked. A descriptive User-Agent in a specified format is required. The documented free-tier limit is 100 queries per minute per OAuth client id, averaged over a ten-minute window — and the wording is 'those ELIGIBLE FOR free access usage', which implies an eligibility condition the wiki does not itself define.

**Blocked by**

- policy review is REQUIRES_REVIEW

---

### Hacker News — `hacker-news`

Technology and startup discussion. Useful for early product launches and developer-audience reaction.

- **Family:** community
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-29 | `mission-1.0` | `REQUIRES_REVIEW` | 1 |
| 2 ← current | 2026-08-29 | `mission-1.3` | `REQUIRES_REVIEW` | 2 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `PUBLIC_API` | firebase-api | nothing | — | **UNKNOWN** | `UNKNOWN` |
| `PUBLIC_WEB` | site-crawl | nothing | — | 1/30s (documented) | `FREE` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | conditional |
| api use | conditional |
| browser automation | **not permitted** |
| commercial use | not addressed |
| storage | not addressed |
| retention | not addressed |
| redistribution | **not permitted** |
| derived analytics | not addressed |
| model processing | not addressed |
| personal data handling | not addressed |
| attribution required | not addressed |

**Reviewer notes**

Status unchanged at REQUIRES_REVIEW, but the assessment underneath it changed materially. Browser automation and public-web collection move to NOT_PERMITTED: the Terms of Use prohibit scraping and data mining in plain words. The official Firebase API is a separate, expressly authorised mechanism and remains available. What is unresolved is narrow and specific: the ToS also prohibits creating derivative works based on Site Content 'except as expressly authorized', and nothing states whether publishing the API extends that authorisation to commercial storage and derived analytics. Silence is not permission, so the source stays blocked.

**Open questions**

- Ask api@ycombinator.com — the contact the API documentation itself publishes — whether providing the official API authorises commercial storage and derived analytics of the returned Site Content, given the derivative-works clause in the Terms of Use.
- Determine whether any retention or deletion obligation applies to API-obtained items when a user deletes their account, given that YC reserves the right to refuse to delete submissions and comments.

**Official evidence (2)**

- [Hacker News API — official documentation](https://github.com/HackerNews/API) — `OFFICIAL_API_DOCS`, retrieved 2026-08-29, section: Overview; URI and Versioning
  - Y Combinator publishes an official read-only API in partnership with Firebase, explicitly to make public Hacker News data available in near real time. No authentication is required and the documentation states there is currently no rate limit. The documentation covers items, users and update feeds and is silent on commercial use, storage, retention and redistribution.
- [Y Combinator Terms of Use](https://www.ycombinator.com/legal/) — `OFFICIAL_TERMS`, retrieved 2026-08-29, section: Site Content, Software and Trademarks
  - The Terms of Use prohibit, except as expressly authorised by Y Combinator, modifying, copying, framing, SCRAPING, selling, distributing or creating derivative works based on the Site or Site Content, and state that 'in connection with your use of the Site you will not engage in or use any data mining, robots, scraping or similar data gathering or extraction methods'. Circumventing an IP block is separately prohibited.

**Blocked by**

- policy review is REQUIRES_REVIEW

---

### Stack Exchange — `stack-exchange`

Question-and-answer network including Stack Overflow. Questions are explicit statements of unsolved problems, which is a direct PAIN signal.

- **Family:** forum
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-29 | `mission-1.0` | `REQUIRES_REVIEW` | 0 |
| 2 ← current | 2026-08-29 | `mission-1.3` | `REQUIRES_REVIEW` | 1 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | stack-exchange-api | api key, dev app | `STACK_EXCHANGE_API_KEY` | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | conditional |
| api use | conditional |
| browser automation | not assessed |
| commercial use | unclear |
| storage | not addressed |
| retention | not addressed |
| redistribution | unclear |
| derived analytics | not addressed |
| model processing | unclear |
| personal data handling | not addressed |
| attribution required | permitted |

**Reviewer notes**

Status unchanged at REQUIRES_REVIEW, with attribution now established as a hard requirement. The API Terms of Use were retrieved; the Public Network Terms of Service and the Consolidated Responsible AI policy were NOT — stackoverflow.com served an anti-bot interstitial for those paths, and this review did not attempt to bypass it. The existence of a paid Stack Data Licensing product alongside a free API is itself a signal that commercial and model-processing use may require a separate agreement, but a signal is not a term, and the review does not treat it as one.

**Open questions**

- Retrieve the Public Network Terms of Service (https://stackoverflow.com/legal/terms-of-service/public) and the Consolidated Responsible AI policy (https://stackoverflow.com/legal/consolidated-responsible-ai-policy) from an environment those paths serve, and assess commercial reuse, storage and model processing against them.
- Determine the precise attribution obligations that CC BY-SA imposes on derived analytics, and whether share-alike reaches aggregated outputs.
- Determine whether Stack Data Licensing is the required route for this use case, and if so what it covers.

**Official evidence (1)**

- [Stack Exchange, Inc. API Terms of Use](https://stackoverflow.com/legal/api-terms-of-use) — `OFFICIAL_TERMS`, retrieved 2026-08-29, section: API Attribution; Stack Exchange Trademark and Brand Guidelines; Termination
  - Attribution is mandatory and specific: all applications must VISUALLY INDICATE that the Stack Exchange Network is the source of content provided through the API, and applications indexed by search engines must follow the attribution rules in the Terms of Service. Exceptions must be requested in advance. Logos may be used unmodified for identification only. The API Terms are silent on commercial use, storage, retention and model processing. The site footer states that user contributions are licensed under CC BY-SA, and the site navigation offers a separate commercial 'Stack Data Licensing' product and a Consolidated Responsible AI policy — both of which suggest that commercial and AI use are governed elsewhere than in these API terms.

**Blocked by**

- policy review is REQUIRES_REVIEW

---

### Product Hunt — `product-hunt`

Daily product launches with community voting and comments. A direct view of what is being built and how it is received.

- **Family:** product_discovery
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `RESTRICTED` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-29 | `mission-1.0` | `RESTRICTED` | 1 |
| 2 ← current | 2026-08-29 | `mission-1.3` | `RESTRICTED` | 1 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | graphql-v2 | auth, oauth, account, dev app | `PRODUCT_HUNT_CLIENT_ID`, `PRODUCT_HUNT_CLIENT_SECRET` | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | conditional |
| api use | conditional |
| browser automation | not assessed |
| commercial use | **not permitted** |
| storage | not addressed |
| retention | not addressed |
| redistribution | not addressed |
| derived analytics | not addressed |
| model processing | not addressed |
| personal data handling | not addressed |
| attribution required | not addressed |

**Conditions**

- Commercial use requires prior written permission from Product Hunt.

**Reviewer notes**

Status unchanged at RESTRICTED and now precisely evidenced. Mission 1.0 inferred the restriction; the documentation states it explicitly. Non-commercial use is permitted, our assessed use is commercial, and the platform names the route to change that. This is the textbook RESTRICTED case: a materially narrower use is permitted, not ours.

**Open questions**

- If Product Hunt launch data becomes necessary, request commercial API permission from hello@producthunt.com and record the response as OPERATOR_CORRESPONDENCE evidence before any collection.

**Official evidence (1)**

- [Product Hunt API v2 documentation](https://api.producthunt.com/v2/docs) — `OFFICIAL_API_DOCS`, retrieved 2026-08-29, section: Welcome to the Product Hunt API 2.0; Accessing Endpoints; May I use the API for my business?
  - The documentation states twice, in plain words, that 'the Product Hunt API must not be used for commercial purposes' and that 'if you would like to use it for your business, please contact us at hello@producthunt.com'. Access requires an OAuth access token; Product Hunt reserves the right to rate-limit any application it considers outside fair use, and faster access requires contacting them.

**Blocked by**

- policy review is RESTRICTED

---

### GitHub — `github`

Code hosting with public repository metadata and issue trackers. Issues are explicit problem statements from a developer audience.

- **Family:** developer
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `RESTRICTED` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-29 | `mission-1.0` | `REQUIRES_REVIEW` | 2 |
| 2 ← current | 2026-08-29 | `mission-1.3` | `RESTRICTED` | 1 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | rest-api-unauthenticated | nothing | — | 60/3600s (documented) | `FREE_WITH_LIMITS` |
| `OFFICIAL_API` | rest-api-authenticated | auth, api key, account | `GITHUB_API_TOKEN` | 5000/3600s (documented) | `FREE_WITH_LIMITS` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | conditional |
| api use | conditional |
| browser automation | **not permitted** |
| commercial use | **not permitted** |
| storage | conditional |
| retention | not addressed |
| redistribution | **not permitted** |
| derived analytics | **not permitted** |
| model processing | not addressed |
| personal data handling | conditional |
| attribution required | not addressed |

**Reviewer notes**

Status LOWERED from REQUIRES_REVIEW to RESTRICTED. The Acceptable Use Policies enumerate the permitted uses of information obtained from GitHub, and the enumeration is explicitly indifferent to how the information was obtained — so using the official API does not widen it. The open-access condition on the research permission is the decisive detail: Startup Research OS is a commercial multi-tenant SaaS producing proprietary insights, which is exactly the case that permission excludes. A narrower use is permitted; ours is not.

**Open questions**

- If GitHub data becomes necessary, determine whether GitHub offers a commercial data licence or an enterprise arrangement covering this use — the Acceptable Use Policies do not mention one.

**Official evidence (1)**

- [GitHub Acceptable Use Policies](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies) — `OFFICIAL_TERMS`, retrieved 2026-08-29, section: 7. Information Usage Restrictions; 8. Privacy
  - Section 7 is an ALLOWLIST and it applies 'regardless of whether the information was scraped, collected through our API, or obtained otherwise'. It permits two uses: researchers may use public non-personal information for research purposes ONLY IF any resulting publications are open access, and archivists may use public information for archival purposes. It separately states that scraping does not refer to collection through the API, and forbids using information from the Service for spamming purposes including selling personal information. Commercial market research producing proprietary insights appears in neither permitted use.

**Blocked by**

- policy review is RESTRICTED

---

### Apple App Store — `apple-app-store`

iOS application listings, ratings and customer reviews. Reviews are a dense source of complaints about existing products.

- **Family:** app_store
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `RESTRICTED` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-29 | `mission-1.0` | `RESTRICTED` | 1 |
| 2 ← current | 2026-08-29 | `mission-1.3` | `RESTRICTED` | 1 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `RSS_OR_FEED` | itunes-rss | nothing | — | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | conditional |
| api use | conditional |
| browser automation | not assessed |
| commercial use | conditional |
| storage | not addressed |
| retention | not addressed |
| redistribution | **not permitted** |
| derived analytics | not addressed |
| model processing | not addressed |
| personal data handling | not addressed |
| attribution required | conditional |

**Reviewer notes**

Status unchanged at RESTRICTED, with the reason now specific. The distinction Mission 1.3 §18 asks for holds: the documented public mechanism exists to promote store content and earn affiliate commission, and App Store Connect governs one's own apps. Neither is a licence for market-research collection and derived analytics over the catalogue. What is permitted is materially narrower than the assessed use case.

**Open questions**

- Determine whether Apple offers any documented mechanism for third-party app metadata, ratings or reviews for market research, and under what terms; none was found in the affiliate search API documentation.

**Official evidence (1)**

- [iTunes Search API — Apple Services Performance Partners](https://performance-partners.apple.com/search-api) — `OFFICIAL_API_DOCS`, retrieved 2026-08-29, section: Overview; Searching; Terms and conditions
  - The documented public search mechanism is published under the Apple Services Performance Partners (affiliate) programme. Its stated purpose is to search store content and DISPLAY THE RESULTS IN YOUR WEBSITE, and it states that developers may use promotional content from the API 'only to promote store content and not for entertainment purposes', with assets kept proximate to a store badge. The guidance is oriented to being 'commissioned for partner links'. No mechanism for bulk market research over third-party app metadata, ratings or reviews is documented here, and App Store Connect concerns a developer's own apps.

**Blocked by**

- policy review is RESTRICTED

---

### Google Play — `google-play`

Android application listings, ratings and reviews.

- **Family:** app_store
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `RESTRICTED` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-29 | `mission-1.0` | `REQUIRES_REVIEW` | 0 |
| 2 ← current | 2026-08-29 | `mission-1.3` | `RESTRICTED` | 1 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | android-publisher-api | auth, oauth, account, dev app | `GOOGLE_PLAY_SERVICE_ACCOUNT` | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | conditional |
| api use | conditional |
| browser automation | not assessed |
| commercial use | not addressed |
| storage | not addressed |
| retention | not addressed |
| redistribution | not addressed |
| derived analytics | not addressed |
| model processing | not addressed |
| personal data handling | not addressed |
| attribution required | not addressed |

**Reviewer notes**

Status changed from REQUIRES_REVIEW to RESTRICTED. The distinction Mission 1.3 §19 asks for is confirmed by the documentation: the Play Developer API is an app-management API for a developer's own apps, not a market-data API. A materially narrower use is authorised and ours is not. The only remaining route would be collecting the public store pages, which this review does not pursue and does not document.

**Open questions**

- Determine whether Google offers any authorised mechanism — a data licence or otherwise — for third-party Play listing, rating or review data for market research. None is documented in the Play Developer API.

**Official evidence (1)**

- [Google Play Developer API](https://developers.google.com/android-publisher) — `OFFICIAL_API_DOCS`, retrieved 2026-08-29, section: Google Play Developer APIs; Subscriptions and In-App Purchases; Publishing API
  - Every documented capability concerns the caller's OWN applications: catalog and in-app product management, purchase and subscription status, uploading new versions, assigning releases to tracks, and creating or modifying one's own Play Store listings. No documented mechanism returns third-party application metadata, ratings or reviews for market research.

**Blocked by**

- policy review is RESTRICTED

---

### YouTube — `youtube`

Video platform with comments and engagement metrics. Comments carry desire and complaint signals for consumer products.

- **Family:** content_platform
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (source), normalized 30d (source)
  - Basis: YouTube API Services Developer Policies require API data to be deleted or refreshed within 30 calendar days. The project baseline allows 12 months for normalized observations (data-retention-policy-v1.md §2.2); the source rule is stricter and therefore wins (§1). Raw is already 30 days at baseline and is restated here so the whole constraint reads in one place.
- **State:** `PROHIBITED` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-29 | `mission-1.0` | `REQUIRES_REVIEW` | 1 |
| 2 ← current | 2026-08-29 | `mission-1.3` | `PROHIBITED` | 1 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | youtube-data-api-v3 | auth, api key, account, dev app | `YOUTUBE_API_KEY` | **UNKNOWN** | `FREE_WITH_LIMITS` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | conditional |
| api use | conditional |
| browser automation | **not permitted** |
| commercial use | not addressed |
| storage | conditional |
| retention | conditional |
| redistribution | **not permitted** |
| derived analytics | **not permitted** |
| model processing | not addressed |
| personal data handling | conditional |
| attribution required | not addressed |

**Reviewer notes**

Status LOWERED from REQUIRES_REVIEW to PROHIBITED. This is the largest change in the mission and it goes the opposite way from an approval. Startup Research OS aggregates API data across channels it does not own, to produce market insight for readers who are not those channels' content owners. The Data Aggregation policy addresses that arrangement directly and forbids it. The 30-day retention override is retained rather than removed: current evidence supports it, and a PROHIBITED source keeping an accurate retention record costs nothing while removing it would lose a verified fact.

**Open questions**

- None material to the verdict. Should YouTube data ever be needed, the route is a content licensing agreement with YouTube, not a change to this assessment.

**Official evidence (1)**

- [YouTube API Services — Developer Policies](https://developers.google.com/youtube/terms/developer-policies) — `OFFICIAL_TERMS`, retrieved 2026-08-29, section: III.E.4 Storage and Refresh of API Data; Data Aggregation
  - Two findings. First, the 30-day rule Mission 1.0 recorded is CONFIRMED and sharpened: an API Client must not store statistics retrieved as Non-Authorized Data for more than 30 days, and Authorized Data other than the enumerated exceptions may be stored for no longer than 30 calendar days, after which it must be deleted or refreshed. Second, and decisive for this use case, the Data Aggregation section states 'Do not aggregate API Data' except for channels under the same content owner pursuant to a YouTube content licensing agreement, with such aggregates viewable only by that content owner, and separately 'Do not aggregate API Data or otherwise use API Data or YouTube API Services to gain insights into YouTube's usage, revenue, or any other aspects of YouTube's business.'

**Blocked by**

- policy review is PROHIBITED

---

### TikTok — `tiktok`

Short-form video platform. Candidate for consumer trend and desire signals.

- **Family:** social
- **Coverage:** PARTIAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `PROHIBITED` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-29 | `mission-1.0` | `PROHIBITED` | 1 |
| 2 ← current | 2026-08-29 | `mission-1.3` | `PROHIBITED` | 1 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | research-api | auth, oauth, account, dev app, approval | `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET` | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | **not permitted** |
| api use | **not permitted** |
| browser automation | **not permitted** |
| commercial use | **not permitted** |
| storage | **not permitted** |
| retention | not assessed |
| redistribution | **not permitted** |
| derived analytics | **not permitted** |
| model processing | not assessed |
| personal data handling | **not permitted** |
| attribution required | not assessed |

**Reviewer notes**

Status unchanged at PROHIBITED and now directly evidenced rather than inferred. This is the case Mission 1.3 §22 describes exactly: an official research API exists, and it is restricted to qualified non-commercial researchers at eligible institutions in eligible regions. Startup Research OS is a commercial multi-tenant SaaS and fails the eligibility criteria on their own terms. An official API existing is not an official API being available to us.

**Official evidence (1)**

- [TikTok Research Tools — eligibility and application](https://developers.tiktok.com/products/research-api/) — `OFFICIAL_API_DOCS`, retrieved 2026-08-29, section: Who can apply?
  - The Research Tools are the documented mechanism for accessing public TikTok data, and their eligibility criteria exclude this use case on two independent grounds. Applicants must be affiliated with an academic institution in the US, EEA, UK or Switzerland, a not-for-profit or independent research institution in the EU, or an academic/not-for-profit body in Brazil studying online youth safety. Applicants must also 'be independent from commercial interests and be able to conduct research on a not-for-profit or non-commercial basis pursuant to a public-interest mission'. Approval additionally requires a defined research proposal, disclosed funding and evidence of ethical review.

**Blocked by**

- policy review is PROHIBITED

---

### Google Trends — `google-trends`

Relative search interest over time and geography. The most direct available proxy for demand attention.

- **Family:** search_trends
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-29 | `mission-1.0` | `REQUIRES_REVIEW` | 1 |
| 2 ← current | 2026-08-29 | `mission-1.3` | `REQUIRES_REVIEW` | 1 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | trends-api-alpha | auth, api key, account, dev app, approval | `GOOGLE_TRENDS_API_KEY` | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | not assessed |
| api use | not assessed |
| browser automation | **not permitted** |
| commercial use | not assessed |
| storage | not assessed |
| retention | not assessed |
| redistribution | not assessed |
| derived analytics | not assessed |
| model processing | not assessed |
| personal data handling | not addressed |
| attribution required | not assessed |

**Conditions**

- The undocumented endpoints behind the Trends web interface must not be called, and no unofficial client library may be used.

**Reviewer notes**

Status unchanged at REQUIRES_REVIEW, and the reason has changed for the better: Mission 1.0 recorded that no official API existed, and one now does. It is not generally available and its terms are not published, so nothing about the assessed use case can yet be established. The Mission 1.0 condition holds unchanged and is reaffirmed here: the undocumented endpoints behind trends.google.com are not an option, and an unofficial library that happens to work is not an authorisation.

**Open questions**

- Apply to the Google Trends API alpha programme and obtain its terms of use; only then can commercial use, storage, retention and redistribution be assessed.

**Official evidence (1)**

- [Introducing the Google Trends API (alpha)](https://developers.google.com/search/blog/2025/07/trends-api) — `OFFICIAL_API_DOCS`, retrieved 2026-08-29, section: Announcement; Data available
  - An official Google Trends API now exists, announced 24 July 2025, and it is in ALPHA: 'the API will be available only to a very limited number of testers', with access by application to the alpha programme. It offers consistently scaled search interest data over 1800 days with daily, weekly, monthly and yearly aggregation and region/sub-region restriction. The announcement lists business use among the expected use cases but is a blog post, not a terms document, and no terms of use for the API were published with it.

**Blocked by**

- policy review is REQUIRES_REVIEW

---

### World Bank Open Data — `world-bank`

Country-level development and economic indicators. Market-context data for MarketScope reasoning, with no personal data.

- **Family:** economic_data
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `APPROVED_WITH_CONDITIONS` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-29 | `mission-1.0` | `REQUIRES_REVIEW` | 1 |
| 2 ← current | 2026-08-29 | `mission-1.3` | `APPROVED_WITH_CONDITIONS` | 1 |

**Required conditions** — all must be satisfied before a collector may run

| Key | Verified by | Checks | Condition |
|---|---|---|---|
| `attribution-surface` | `CAPABILITY` | `source-attribution-display` | A product surface exists that displays the required World Bank attribution and a statement of any modifications, on every view derived from this source. |
| `dataset-licence-allowlist` | `CAPABILITY` | `dataset-licence-filter` | The collector requests only datasets whose recorded licence is CC-BY 4.0 or ODbL, and skips every other licence. |
| `microdata-excluded` | `ACCESS_METHOD` | `indicators-api-only` | The Microdata Library is excluded from every request path. |

None of these is satisfied *by the catalog*, and none can be: satisfaction is environment state, recorded by a verifier that says what it checked (`sros-source verify`). `APPROVED_WITH_CONDITIONS` means a collector MAY be designed, never that one may run.

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `PUBLIC_API` | indicators-api-v2 | nothing | — | **UNKNOWN** | `FREE` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | permitted |
| api use | permitted |
| browser automation | not addressed |
| commercial use | permitted |
| storage | permitted |
| retention | permitted |
| redistribution | conditional |
| derived analytics | permitted |
| model processing | permitted |
| personal data handling | not addressed |
| attribution required | permitted |

**Conditions**

- Collect only datasets labelled CC-BY 4.0 or ODbL.
- Never collect from the Microdata Library: its licence permits statistical and scientific research only and forbids redistribution without written agreement.
- Attribute the World Bank and indicate any modifications, including translations.
- If any ODbL dataset is used, honour its share-alike obligation on redistribution.

**Reviewer notes**

Status raised from REQUIRES_REVIEW to APPROVED_WITH_CONDITIONS. Mission 1.0 could not establish the licence; the Data Catalog licensing page was retrieved this mission and is explicit that CC-BY 4.0 permits commercial use with attribution. The conditions exist because the SAME platform also distributes Microdata under a research-only licence and third-party data under external terms, so an approval that covered 'World Bank' as a whole would be wrong. It covers CC-BY 4.0 indicator data and nothing else.

**Open questions**

- Confirm per dataset, at collection time, which licence applies — the licence is a dataset property and the catalog records it per dataset, not per platform.

**Official evidence (1)**

- [World Bank Data Catalog — Data Access and Licensing](https://datacatalog.worldbank.org/public-licenses) — `OFFICIAL_LICENCE`, retrieved 2026-08-29, section: Creative Commons Attribution 4.0 (CC-BY 4.0); Microdata Research License; License Specified Externally; Custom License
  - CC-BY 4.0 is the DEFAULT licence for datasets the World Bank itself produces and distributes as open data, and it permits copying, modification and distribution in any format FOR ANY PURPOSE, INCLUDING COMMERCIAL USE, provided appropriate credit is given and changes are indicated. Additional mandatory terms impose mediation and UNCITRAL arbitration for disputes. Crucially the page states that many datasets carry OTHER licences: ODbL adds a share-alike obligation on redistribution; the Microdata Research License permits statistical and scientific research only and forbids redistribution without prior written agreement; and 'License Specified Externally' and 'Custom License' datasets carry third-party terms. Licensing is therefore per dataset, not per platform.

**Blocked by**

- review conditions not satisfied: attribution-surface, dataset-licence-allowlist, microdata-excluded

---

### Eurostat — `eurostat`

European statistical data. Market-context data for EU MarketScope values, with no personal data.

- **Family:** economic_data
- **Coverage:** PARTIAL, languages ['en', 'de', 'fr']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `APPROVED_WITH_CONDITIONS` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-29 | `mission-1.0` | `REQUIRES_REVIEW` | 1 |
| 2 ← current | 2026-08-29 | `mission-1.3` | `APPROVED_WITH_CONDITIONS` | 1 |

**Required conditions** — all must be satisfied before a collector may run

| Key | Verified by | Checks | Condition |
|---|---|---|---|
| `attribution-surface` | `CAPABILITY` | `source-attribution-display` | A product surface displays the Eurostat citation — dataset DOI and access date — on every view derived from this source. |
| `geographic-exclusion` | `CAPABILITY` | `eurostat-geographic-filter` | The collector excludes data for countries outside the EU, EFTA and official acceding/candidate countries. |
| `trade-data-exclusion` | `CAPABILITY` | `eurostat-trade-exclusion` | The collector excludes the named Liechtenstein, Switzerland and Austria trade-data exceptions. |

None of these is satisfied *by the catalog*, and none can be: satisfaction is environment state, recorded by a verifier that says what it checked (`sros-source verify`). `APPROVED_WITH_CONDITIONS` means a collector MAY be designed, never that one may run.

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `PUBLIC_API` | sdmx-web-services | nothing | — | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | permitted |
| api use | permitted |
| browser automation | not addressed |
| commercial use | conditional |
| storage | permitted |
| retention | permitted |
| redistribution | conditional |
| derived analytics | permitted |
| model processing | permitted |
| personal data handling | not addressed |
| attribution required | permitted |

**Conditions**

- Exclude data for countries outside the EU, EFTA and official acceding/candidate countries from any commercial use.
- Exclude the named trade-data exceptions (Liechtenstein and Switzerland as declaring countries from 1995 for HS/SITC/BEC/NSTR; Austria at CN 8-digit).
- Cite the dataset DOI and the access date; state any modification with the Eurostat non-responsibility disclaimer.

**Reviewer notes**

Status raised from REQUIRES_REVIEW to APPROVED_WITH_CONDITIONS. Mission 1.0 could not retrieve the copyright notice; it was retrieved this mission. The geographic exclusion is the condition that matters: our assessed use is commercial, and data for non-EU/EFTA/candidate countries may NOT be reused commercially. That is a mechanical filter, not a caveat to remember.

**Open questions**

- Record the SDMX endpoint base URL and its documented query-size and rate limits, which the copyright notice does not cover.

**Official evidence (1)**

- [Eurostat — Copyright notice and free re-use of data](https://ec.europa.eu/eurostat/web/main/help/copyright-notice) — `OFFICIAL_LICENCE`, retrieved 2026-08-29, section: General principles; Exceptions; How to re-use Eurostat material for commercial purposes; How to cite Eurostat products
  - Reuse of statistical data, metadata and publications for COMMERCIAL or non-commercial purposes is authorised provided the source is acknowledged, under the Commission reuse Decision of 12 December 2011. There is no special procedure and no written licence required. The exceptions are enumerated and material: data identified as belonging to sources other than Eurostat; publications whose copyright is partly or wholly third-party; DATA FOR COUNTRIES OTHER THAN EU, EFTA and official acceding/candidate countries (the page names the USA, Japan and China) which must be removed before commercial reuse; and specific trade data declared by Liechtenstein, Switzerland and Austria. Citation must give the dataset DOI and the access date, and modifications must be stated with a disclaimer.

**Blocked by**

- review conditions not satisfied: attribution-surface, geographic-exclusion, trade-data-exclusion

---

### FRED (Federal Reserve Economic Data) — `fred`

US and international economic time series held by the Federal Reserve Bank of St. Louis.

- **Family:** economic_data
- **Coverage:** PARTIAL, countries ['US'], languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `APPROVED_WITH_CONDITIONS` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-29 | `mission-1.0` | `REQUIRES_REVIEW` | 0 |
| 2 ← current | 2026-08-29 | `mission-1.3` | `APPROVED_WITH_CONDITIONS` | 1 |

**Required conditions** — all must be satisfied before a collector may run

| Key | Verified by | Checks | Condition |
|---|---|---|---|
| `fred-api-key` | `CONFIG_REFERENCE` | `FRED_API_KEY` | A FRED API key is configured in the environment. |
| `fred-endorsement-notice` | `CAPABILITY` | `source-attribution-display` | The product prominently displays the exact notice the terms require. |
| `copyrighted-series-excluded` | `CAPABILITY` | `fred-copyright-series-filter` | The collector excludes every series whose notes contain 'Copyright', or records per-owner permission for it. |

None of these is satisfied *by the catalog*, and none can be: satisfaction is environment state, recorded by a verifier that says what it checked (`sros-source verify`). `APPROVED_WITH_CONDITIONS` means a collector MAY be designed, never that one may run.

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | fred-api | auth, api key, account | `FRED_API_KEY` | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | permitted |
| api use | permitted |
| browser automation | not addressed |
| commercial use | conditional |
| storage | permitted |
| retention | permitted |
| redistribution | conditional |
| derived analytics | permitted |
| model processing | permitted |
| personal data handling | not addressed |
| attribution required | permitted |

**Conditions**

- Display verbatim: 'This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.'
- Exclude every series whose notes contain 'Copyright', unless permission has been obtained from that series' owner and recorded.
- Do not use FRED, ALFRED or Federal Reserve Bank in a hostname, do not use their marks, and do not imply endorsement.

**Reviewer notes**

Status raised from REQUIRES_REVIEW to APPROVED_WITH_CONDITIONS. The terms are clear and the conditions are unusually concrete — one of them is an exact sentence that must appear in the product. The third-party-series carve-out is the substantive limit: FRED redistributes series it does not own, and API access grants no rights over those. It is mechanically detectable, which is why it is a condition rather than an open question.

**Open questions**

- Determine whether any series the research use case needs is copyrighted; if so, the owner must be contacted individually — the Bank cannot grant that permission.

**Official evidence (1)**

- [FRED® API Terms of Use](https://fred.stlouisfed.org/docs/api/terms_of_use.html) — `OFFICIAL_TERMS`, retrieved 2026-08-29, section: Property Rights; Prohibitions; Requirements
  - Access to the FRED API is licensed, and the terms were retrieved in full this mission (Mission 1.0 received HTTP 403). Property Rights is the decisive section: data series available through the API MAY BE OWNED BY THIRD PARTIES, the Bank's provision of the API does not override those owners' copyrights, and 'before using data series owned by third parties for anything other than your own personal use, you must contact the data owner to obtain permission'. Copyrighted series are identifiable: they contain the word 'Copyright' in their notes and can be found via the fred/series/search request. Requirements include a MANDATORY notice — 'This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis' — placed prominently on the application. Prohibitions include using FRED marks in a hostname, implying endorsement, removing proprietary notices, and replicating the essential user experience of the FRED website. Rate and bandwidth limits may be imposed at the Bank's discretion.

**Blocked by**

- review conditions not satisfied: copyrighted-series-excluded, fred-api-key, fred-endorsement-notice

---
