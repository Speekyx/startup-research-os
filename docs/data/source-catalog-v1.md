# Source Catalog V1

**Status:** Authoritative record of the initial candidate catalog.
**Catalog version:** 1.0.0
**Reviewed:** 2026-08-29 by `mission-1.0`
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
| `APPROVED_WITH_CONDITIONS` | 0 |
| `REQUIRES_REVIEW` | 10 — reddit, hacker-news, stack-exchange, github, google-play, youtube, google-trends, world-bank, eurostat, fred |
| `RESTRICTED` | 2 — product-hunt, apple-app-store |
| `PROHIBITED` | 1 — tiktok |
| `SUSPENDED` | 0 |
| `DRAFT` | 0 |

**Collector-eligible: 0 of 13.**

No source is collector-eligible. That is the expected result of a first pass and not a failure: Mission 1.0 §31 asks for correctness over the number of approvals, and a registry in which every platform came back approved would mean the gate was not doing anything.

### Limitations of this review

- Reddit and Stack Exchange documentation could not be retrieved from this environment: both hosts are unreachable through the available fetch path. Their assessments rest on no evidence and are REQUIRES_REVIEW with the exact documents named.
- No assessment here is a legal opinion. Where a conclusion would require legal judgment, the recorded value is UNCLEAR or NOT_ADDRESSED and a human review is required.
- No source data was collected. Only official documentation about the sources was read.

---

## Assessment table

Activities are assessed separately, because their conditions differ. A source may permit automated API access and forbid commercial use, and only a per-activity reading can say so.

| Source | Family | Access | Official API | Auth | Commercial | Automation | Storage | Retention | Redistribution | Rate limits | Personal data | State | Eligible |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `reddit` | community | official api | yes | yes | not assessed | not assessed | not assessed | not assessed | not assessed | UNKNOWN | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `hacker-news` | community | public api, public web | yes | no | not assessed | conditional | not assessed | not assessed | not assessed | documented | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `stack-exchange` | forum | official api | yes | no | not assessed | not assessed | not assessed | not assessed | not assessed | UNKNOWN | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `product-hunt` | product_discovery | official api | yes | yes | **not permitted** | conditional | not addressed | not addressed | not addressed | UNKNOWN | PSEUDONYMOUS | `RESTRICTED` | **no** |
| `github` | developer | official api | yes | yes | unclear | conditional | not assessed | not assessed | not assessed | documented | IDENTIFIABLE | `REQUIRES_REVIEW` | **no** |
| `apple-app-store` | app_store | rss or feed | no | no | not assessed | unclear | not assessed | not assessed | not assessed | UNKNOWN | PSEUDONYMOUS | `RESTRICTED` | **no** |
| `google-play` | app_store | official api | yes | yes | not assessed | not assessed | not assessed | not assessed | not assessed | UNKNOWN | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `youtube` | content_platform | official api | yes | yes | conditional | conditional | conditional | conditional | **not permitted** | UNKNOWN | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `tiktok` | social | official api | yes | yes | **not permitted** | **not permitted** | **not permitted** | **not permitted** | **not permitted** | UNKNOWN | IDENTIFIABLE | `PROHIBITED` | **no** |
| `google-trends` | search_trends | official api | yes | yes | not assessed | not assessed | not assessed | not assessed | not assessed | UNKNOWN | NONE_EXPECTED | `REQUIRES_REVIEW` | **no** |
| `world-bank` | economic_data | public api | yes | no | not assessed | permitted | not assessed | not assessed | not assessed | UNKNOWN | NONE_EXPECTED | `REQUIRES_REVIEW` | **no** |
| `eurostat` | economic_data | public api | yes | no | not assessed | not assessed | not assessed | not assessed | not assessed | UNKNOWN | NONE_EXPECTED | `REQUIRES_REVIEW` | **no** |
| `fred` | economic_data | official api | yes | yes | not assessed | not assessed | not assessed | not assessed | not assessed | UNKNOWN | NONE_EXPECTED | `REQUIRES_REVIEW` | **no** |

---

## Per-source detail

### Reddit — `reddit`

Threaded discussion communities. A primary candidate for PAIN and DESIRE signals because complaints and feature requests are stated in the users' own words.

- **Family:** community
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | reddit-data-api | auth, oauth, account, dev app, approval | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | not assessed |
| api use | not assessed |
| browser automation | not assessed |
| commercial use | not assessed |
| storage | not assessed |
| retention | not assessed |
| redistribution | not assessed |
| derived analytics | not assessed |
| model processing | not assessed |
| personal data handling | not assessed |
| attribution required | not assessed |

**Reviewer notes**

No evidence could be gathered: redditinc.com and reddit.com are unreachable from this environment. Reddit's 2023 API changes are widely understood to have introduced paid tiers and restrictions on automated use, which makes an unverified assumption particularly unsafe here. Nothing is assessed; every activity is NOT_ASSESSED rather than assumed.

**Open questions**

- Retrieve and assess the Reddit Data API Terms at https://www.redditinc.com/policies/data-api-terms
- Retrieve and assess the Reddit Developer Terms at https://www.redditinc.com/policies/developer-terms
- Determine the current API pricing tiers and whether a commercial tier is required for this use
- Determine documented rate limits for the applicable tier
- Determine whether content may be retained, and for how long
- Determine whether use of content for model processing is addressed
- Determine attribution requirements

**Official evidence (0)**

None. This assessment rests on no retrieved document, which is why it
cannot approve anything.

**Blocked by**

- policy review is REQUIRES_REVIEW
- policy review has no evidence

---

### Hacker News — `hacker-news`

Technology and startup discussion. Useful for early product launches and developer-audience reaction.

- **Family:** community
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `PUBLIC_API` | firebase-api | nothing | — | **UNKNOWN** | `UNKNOWN` |
| `PUBLIC_WEB` | site-crawl | nothing | — | 1/30s (documented) | `FREE` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | conditional |
| api use | not assessed |
| browser automation | not addressed |
| commercial use | not assessed |
| storage | not assessed |
| retention | not assessed |
| redistribution | not assessed |
| derived analytics | not assessed |
| model processing | not assessed |
| personal data handling | not assessed |
| attribution required | not assessed |

**Conditions**

- Any crawl of news.ycombinator.com must honour Crawl-delay: 30 and must not touch the disallowed action endpoints

**Reviewer notes**

The only evidence gathered is robots.txt, which is an access directive rather than a licence. It establishes a crawl rate and a set of forbidden paths; it says nothing about commercial reuse, retention or model processing. Automated access is PERMITTED_WITH_CONDITIONS on that narrow basis alone. Everything that would be needed to approve collection remains unassessed.

**Open questions**

- Confirm the terms governing the official Firebase API at https://github.com/HackerNews/API
- Determine whether Y Combinator publishes terms addressing commercial reuse of Hacker News content
- Determine whether retention or redistribution is addressed anywhere
- Determine whether use for model processing is addressed

**Official evidence (1)**

- [Hacker News robots.txt](https://news.ycombinator.com/robots.txt) — `OFFICIAL_ACCESS_CONTROL`, retrieved 2026-08-29, section: User-agent: *
  - Publishes Crawl-delay: 30 for all user agents and disallows the action endpoints /collapse, /context, /fave, /flag, /hide, /login, /logout, /r, /reply, /submitlink, /vote and /x. No Allow directives are present.

**Blocked by**

- policy review is REQUIRES_REVIEW

---

### Stack Exchange — `stack-exchange`

Question-and-answer network including Stack Overflow. Questions are explicit statements of unsolved problems, which is a direct PAIN signal.

- **Family:** forum
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | stack-exchange-api | api key, dev app | `STACK_EXCHANGE_API_KEY` | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | not assessed |
| api use | not assessed |
| browser automation | not assessed |
| commercial use | not assessed |
| storage | not assessed |
| retention | not assessed |
| redistribution | not assessed |
| derived analytics | not assessed |
| model processing | not assessed |
| personal data handling | not assessed |
| attribution required | not assessed |

**Reviewer notes**

No evidence could be gathered: api.stackexchange.com and stackoverflow.com are unreachable from this environment. Stack Exchange content is understood to carry a Creative Commons licence with attribution requirements, and attribution obligations attach to derived works in ways that must be read before any collection. Nothing is assessed.

**Open questions**

- Retrieve and assess the API documentation and quota rules at https://api.stackexchange.com/docs
- Retrieve and assess the content licence at https://stackoverflow.com/help/licensing, including which Creative Commons version applies to which date ranges and what attribution it requires
- Determine whether the licence permits commercial redistribution of derived analytics and under what attribution
- Determine whether use for model processing is addressed
- Determine the documented request quota and its period

**Official evidence (0)**

None. This assessment rests on no retrieved document, which is why it
cannot approve anything.

**Blocked by**

- policy review is REQUIRES_REVIEW
- policy review has no evidence

---

### Product Hunt — `product-hunt`

Daily product launches with community voting and comments. A direct view of what is being built and how it is received.

- **Family:** product_discovery
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `RESTRICTED` — **collector eligible: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | graphql-v2 | auth, oauth, account, dev app | `PRODUCT_HUNT_CLIENT_ID`, `PRODUCT_HUNT_CLIENT_SECRET` | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | conditional |
| api use | conditional |
| browser automation | not addressed |
| commercial use | **not permitted** |
| storage | not addressed |
| retention | not addressed |
| redistribution | not addressed |
| derived analytics | not addressed |
| model processing | not addressed |
| personal data handling | not assessed |
| attribution required | not addressed |

**Conditions**

- API access is permitted only for non-commercial use under the published documentation
- Commercial use requires prior written agreement obtained by contacting Product Hunt

**Reviewer notes**

RESTRICTED, and the restriction is decisive rather than procedural. The API documentation states plainly that the API must not be used for commercial purposes and directs business users to contact Product Hunt. Startup Research OS is a commercial product, so the documented default excludes it. The path forward is operator correspondence, not a technical workaround; until such an agreement exists and is recorded as evidence, this source is not collectable.

**Open questions**

- Whether Product Hunt will grant a commercial-use agreement for this use case, and on what terms
- Whether storage, retention and redistribution are addressed in a separate terms document not reviewed here

**Official evidence (1)**

- [Product Hunt API v2 documentation](https://api.producthunt.com/v2/docs) — `OFFICIAL_API_DOCS`, retrieved 2026-08-29, section: Introduction / usage
  - States that the API is accessible only with a provided access token obtained via OAuth or a developer token, that Product Hunt reserves the right to rate-limit applications it considers outside fair use without stating numeric limits, and that the API must not be used for commercial purposes, directing business users to contact hello@producthunt.com.

**Blocked by**

- policy review is RESTRICTED

---

### GitHub — `github`

Code hosting with public repository metadata and issue trackers. Issues are explicit problem statements from a developer audience.

- **Family:** developer
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

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
| browser automation | unclear |
| commercial use | unclear |
| storage | not assessed |
| retention | not assessed |
| redistribution | not assessed |
| derived analytics | unclear |
| model processing | not assessed |
| personal data handling | conditional |
| attribution required | not assessed |

**Conditions**

- Documented primary and secondary rate limits must be respected; the collector must consume the recorded values rather than its own
- Information from GitHub must not be used for spam, unsolicited email, or the sale of personal information
- Profile data must not be retained beyond what the research objective requires

**Reviewer notes**

The technical picture is solid and documented; the permission picture is not. Two findings block approval. First, the Acceptable Use Policies separate scraping from API access and permit research use of scraped public information only where resulting publications are open access -- a condition a commercial product does not meet, and whose scope relative to API use is genuinely ambiguous. Second, the API terms live in the Terms of Service, which was not retrieved. GitHub profiles carry real names and locations, so the personal-data risk is IDENTIFIABLE rather than pseudonymous.

**Open questions**

- Read the API terms in the GitHub Terms of Service (Section H) and determine whether commercial use of API data for this purpose is permitted
- The Acceptable Use Policies permit research use only where resulting publications are open access. Determine whether that clause governs commercial analytical use, or only the scraping route it appears within
- Determine whether storage and retention of API responses are addressed anywhere
- Determine whether use for model processing is addressed

**Official evidence (2)**

- [Rate limits for the REST API](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) — `OFFICIAL_API_DOCS`, retrieved 2026-08-29, section: Primary rate limits / Secondary rate limits
  - Unauthenticated requests are limited to 60 per hour; requests authenticated with a personal access token to 5,000 per hour. Secondary limits cap concurrent requests at 100, endpoint cost at 900 points per minute, CPU time at 90 seconds per 60 seconds of real time, and content-creating requests at 80 per minute and 500 per hour.
- [GitHub Acceptable Use Policies](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies) — `OFFICIAL_TERMS`, retrieved 2026-08-29, section: Information Usage Restrictions / Scraping and API Usage Restrictions
  - Defines scraping as automated extraction via the Service and states explicitly that scraping does not refer to collection through the API, which is governed by the Terms of Service instead. Permits researchers to use public non-personal information for research only if resulting publications are open access, and permits archival use. Prohibits using information from the Service for spam, unsolicited email, or selling personal information such as to recruiters or job boards. No effective date is stated on the page.

**Blocked by**

- policy review is REQUIRES_REVIEW

---

### Apple App Store — `apple-app-store`

iOS application listings, ratings and customer reviews. Reviews are a dense source of complaints about existing products.

- **Family:** app_store
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `RESTRICTED` — **collector eligible: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `RSS_OR_FEED` | itunes-rss | nothing | — | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | unclear |
| api use | not assessed |
| browser automation | **not permitted** |
| commercial use | not assessed |
| storage | not assessed |
| retention | not assessed |
| redistribution | not assessed |
| derived analytics | unclear |
| model processing | not assessed |
| personal data handling | not assessed |
| attribution required | not assessed |

**Conditions**

- No scraping of Apple properties under any access method
- Any use must go through an approved Apple feed, and that feed's own terms must be reviewed first

**Reviewer notes**

RESTRICTED. Apple states directly that information must not be scraped from Apple sites including the App Store, and that rankings must not be created from such information -- the second half matters here, because ranking opportunities is what this system does. The clause sits in the App Store Review Guidelines, which govern apps rather than external services, so it is strong evidence of Apple's position rather than a term that plainly binds this system. That ambiguity is exactly why the state is RESTRICTED and not PROHIBITED: the correct next step is reading the terms that do bind a non-app consumer, not assuming either answer.

**Open questions**

- Guideline 4.5.1 governs apps distributed on the App Store. Determine whether an equivalent restriction binds a third-party service that is not an App Store app -- the Apple Media Services Terms and the site terms of use need reading
- Determine the current iTunes/App Store RSS feed endpoints and whether their terms permit this use
- Determine whether App Store Connect API access is relevant, noting it is scoped to a developer's own apps

**Official evidence (1)**

- [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) — `OFFICIAL_TERMS`, retrieved 2026-08-29, section: 4.5.1 Apple Sites and Services
  - States that apps may use approved Apple RSS feeds such as the iTunes Store RSS feed, but may not scrape any information from Apple sites including apple.com, the iTunes Store, the App Store, App Store Connect and the developer portal, and may not create rankings using that information. The guideline addresses apps distributed on the App Store rather than third-party services generally.

**Blocked by**

- policy review is RESTRICTED

---

### Google Play — `google-play`

Android application listings, ratings and reviews.

- **Family:** app_store
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible: no**
- **Last reviewed:** 2026-08-29 · next 2027-02-25

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | android-publisher-api | auth, oauth, account, dev app | `GOOGLE_PLAY_SERVICE_ACCOUNT` | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | not assessed |
| api use | not assessed |
| browser automation | not assessed |
| commercial use | not assessed |
| storage | not assessed |
| retention | not assessed |
| redistribution | not assessed |
| derived analytics | not assessed |
| model processing | not assessed |
| personal data handling | not assessed |
| attribution required | not assessed |

**Reviewer notes**

Not researched in this mission. The decisive question is not a policy nuance but a capability one: if the publisher API only exposes a developer's own applications, then no approved path exists for collecting competitor reviews, and no policy reading changes that. Recorded as REQUIRES_REVIEW with that question first.

**Open questions**

- Read the Google Play Developer API terms at https://developers.google.com/android-publisher/terms
- Confirm whether the Play Developer API exposes reviews for applications the caller does not own -- if it does not, this source has no lawful automated access path for this use and the correct state is RESTRICTED
- Read the Google Terms of Service provisions on automated access to Google properties
- Determine whether any official mechanism exists for third-party access to Play listing and review data

**Official evidence (0)**

None. This assessment rests on no retrieved document, which is why it
cannot approve anything.

**Blocked by**

- policy review is REQUIRES_REVIEW
- policy review has no evidence

---

### YouTube — `youtube`

Video platform with comments and engagement metrics. Comments carry desire and complaint signals for consumer products.

- **Family:** content_platform
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (source), normalized 30d (source)
  - Basis: YouTube API Services Developer Policies require API data to be deleted or refreshed within 30 calendar days. The project baseline allows 12 months for normalized observations (data-retention-policy-v1.md §2.2); the source rule is stricter and therefore wins (§1). Raw is already 30 days at baseline and is restated here so the whole constraint reads in one place.
- **State:** `REQUIRES_REVIEW` — **collector eligible: no**
- **Last reviewed:** 2026-08-29 · next 2026-11-27

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
| commercial use | conditional |
| storage | conditional |
| retention | conditional |
| redistribution | **not permitted** |
| derived analytics | conditional |
| model processing | not addressed |
| personal data handling | conditional |
| attribution required | conditional |

**Conditions**

- Data obtained through the API must not be stored longer than 30 calendar days; it must be deleted or refreshed within that window
- A user deletion request must be honoured as soon as possible and within 7 calendar days
- No scraping of YouTube or Google properties, and no use of scraped YouTube data obtained elsewhere
- YouTube must be shown as the source wherever its content is displayed, per the Branding Guidelines
- Aggregation across channels is restricted to channels under the same content owner

**Reviewer notes**

The best-documented candidate in this catalog, and still not approvable. The 30-day storage cap, the scraping prohibition, the branding requirement and the aggregation limits are all explicit and workable. What blocks approval is a single silence: the developer policies do not address processing API data with a language model, and this system's entire purpose is to do that. Silence is not permission (source-registry-v1.md §6), so the state is REQUIRES_REVIEW and the question is named. The review interval is shortened to 90 days because these policies were updated recently and change often.

**Open questions**

- The policies do not address use of API data for machine learning or model processing. Since this system processes collected text with LLMs, that silence is material and needs a decision before any collection
- Determine the numeric default quota for the Data API and record it as a documented rate limit
- Confirm whether comment text counts as Authorized or Non-Authorized Data for the 30-day rule

**Official evidence (1)**

- [YouTube API Services - Developer Policies](https://developers.google.com/youtube/terms/developer-policies) — `OFFICIAL_TERMS`, retrieved 2026-08-29, section: Storage and Caching / Commercial Use / Scraping / Attribution
  - Non-Authorized Data may be stored no longer than 30 calendar days and Authorized Data must be deleted or refreshed within 30 days, with user deletion requests honoured within 7 days. Clients must not scrape YouTube or Google applications, nor use scraped YouTube data obtained elsewhere. Commercial use is permitted in enumerated forms while selling API access or selling ads against API data without independent value requires prior written approval. Clients must display YouTube Brand Features as the source and must not obscure YouTube attribution. Quotas exist and extensions require an API Compliance Audit; no numeric limit is stated. Machine learning and model training are not addressed. Page states 'Last updated 2026-06-24 UTC'.

**Blocked by**

- policy review is REQUIRES_REVIEW

---

### TikTok — `tiktok`

Short-form video platform. Candidate for consumer trend and desire signals.

- **Family:** social
- **Coverage:** PARTIAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `PROHIBITED` — **collector eligible: no**
- **Last reviewed:** 2026-08-29 · next 2027-08-29

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
| retention | **not permitted** |
| redistribution | **not permitted** |
| derived analytics | **not permitted** |
| model processing | **not permitted** |
| personal data handling | **not permitted** |
| attribution required | not assessed |

**Reviewer notes**

PROHIBITED for this system's assessed use, and the finding is unambiguous rather than cautious. The Research API requires applicants to be independent from commercial interests and to conduct research on a not-for-profit or non-commercial basis, and eligibility is limited to academic institutions and non-profit research bodies in named regions. Startup Research OS is a commercial product and meets none of those criteria. There is no reading of these terms under which this system qualifies, and the correct response is to stop considering TikTok through this route rather than to look for a technical alternative -- scraping would breach the same terms more clearly, not less.

**Open questions**

- Whether TikTok offers any commercial data product that would permit this use. If one exists it is a different source and needs its own registry entry and its own review

**Official evidence (1)**

- [TikTok Research API](https://developers.tiktok.com/products/research-api/) — `OFFICIAL_API_DOCS`, retrieved 2026-08-29, section: Eligibility / application requirements
  - Access is limited to academic institutions in the US, EEA, UK or Switzerland, to not-for-profit or independent research institutions in the EU, and to academic or not-for-profit organisations in Brazil studying online youth safety. Applicants must submit a research proposal, must demonstrate a public-interest mission, and must be independent from commercial interests and able to conduct the research on a not-for-profit or non-commercial basis. Approval takes up to four weeks. Researchers must commit to data security and confidentiality requirements including protecting personal data.

**Blocked by**

- policy review is PROHIBITED

---

### Google Trends — `google-trends`

Relative search interest over time and geography. The most direct available proxy for demand attention.

- **Family:** search_trends
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible: no**
- **Last reviewed:** 2026-08-29 · next 2026-11-27

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
| personal data handling | not assessed |
| attribution required | not assessed |

**Conditions**

- Unofficial Trends endpoints used by the web interface must not be called. They are not a published API, and using them is precisely the brittle bypass this registry exists to prevent

**Reviewer notes**

An official API was announced in alpha in July 2025, which means access is limited and its terms were not retrievable here. The important entry is the condition: the widely used approach of calling the undocumented endpoints behind trends.google.com is not an option for this system. It is unpublished, unstable and outside any granted permission, and preferring a durable authorised path over a convenient bypass is a standing rule (Mission 1.0 §30). Data itself carries no personal information, which is why the personal-data risk is NONE_EXPECTED.

**Open questions**

- Determine whether the Google Trends API has left alpha and what the current access and approval process is
- Determine the terms governing the Trends API, including commercial use, storage and redistribution
- Determine documented quotas

**Official evidence (1)**

- [Google Search Central Blog archive](https://developers.google.com/search/blog) — `OFFICIAL_API_DOCS`, retrieved 2026-08-29, section: July 2025 post index
  - The blog archive lists a July 2025 announcement titled 'Introducing the Google Trends API (alpha)', indicating that an official Trends API exists but was in alpha with limited availability rather than generally available. The announcement's terms were not retrieved.

**Blocked by**

- policy review is REQUIRES_REVIEW

---

### World Bank Open Data — `world-bank`

Country-level development and economic indicators. Market-context data for MarketScope reasoning, with no personal data.

- **Family:** economic_data
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible: no**
- **Last reviewed:** 2026-08-29 · next 2027-08-29

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
| commercial use | not assessed |
| storage | not assessed |
| retention | not assessed |
| redistribution | not assessed |
| derived analytics | not assessed |
| model processing | not assessed |
| personal data handling | not assessed |
| attribution required | not assessed |

**Reviewer notes**

The closest candidate to approvable, and still short of it. The API is documented, unauthenticated and explicitly needs no key, so automated access and API use are PERMITTED on documented evidence. What is missing is the licence: the documentation page points at terms of use without stating them, and this data is widely but not universally open -- some series carry third-party rights. Approval waits on reading the licence, which is a short task rather than a legal one. Personal-data risk is NONE_EXPECTED: these are country aggregates.

**Open questions**

- Read the World Bank Terms of Use at https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets and the Open Data licence, and record which licence applies and what attribution it requires
- Confirm whether commercial reuse and redistribution of derived analytics are permitted under that licence
- Identify which indicators carry third-party rights that the World Bank licence does not cover

**Official evidence (1)**

- [About the Indicators API Documentation](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation) — `OFFICIAL_API_DOCS`, retrieved 2026-08-29, section: API basic call structure
  - Documents the base URL https://api.worldbank.org/v2/ and states that API keys and other authentication methods are no longer necessary to access the API. No rate limits or usage restrictions are stated on the page. The page refers to the website terms of use without reproducing them, and states no licence or attribution requirement for the data itself.

**Blocked by**

- policy review is REQUIRES_REVIEW

---

### Eurostat — `eurostat`

European statistical data. Market-context data for EU MarketScope values, with no personal data.

- **Family:** economic_data
- **Coverage:** PARTIAL, languages ['en', 'de', 'fr']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible: no**
- **Last reviewed:** 2026-08-29 · next 2027-08-29

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `PUBLIC_API` | sdmx-web-services | nothing | — | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | not assessed |
| api use | not assessed |
| browser automation | not assessed |
| commercial use | not assessed |
| storage | not assessed |
| retention | not assessed |
| redistribution | not assessed |
| derived analytics | not assessed |
| model processing | not assessed |
| personal data handling | not assessed |
| attribution required | not assessed |

**Reviewer notes**

The web services page confirms that SDMX 2.1 services exist and that datasets refresh twice daily, and states nothing about authentication, limits or reuse. The reuse notice exists elsewhere on the site; an attempt to retrieve it at the expected copyright URL returned 404, so the correct current location has to be found rather than assumed. Nothing is assessed.

**Open questions**

- Read the Eurostat copyright and free re-use notice, which the web services page references from the Help menu but does not link on the page reviewed
- Record the SDMX endpoint base URL and the API user guide reference
- Determine documented query-size and rate limits, which SDMX services commonly impose
- Confirm attribution requirements under the applicable Commission reuse decision

**Official evidence (1)**

- [Eurostat - Data web services](https://ec.europa.eu/eurostat/web/main/data/web-services) — `OFFICIAL_API_DOCS`, retrieved 2026-08-29, section: Web services overview
  - States that SDMX 2.1 web services and Eurostat statistics web services are available with linked user guides, and that Eurostat datasets are updated twice a day at 11:00 and 23:00 CET. The page lists no endpoint base URL, states nothing about authentication or rate limits, and does not carry the reuse or copyright terms, which it references from a separate Help entry.

**Blocked by**

- policy review is REQUIRES_REVIEW

---

### FRED (Federal Reserve Economic Data) — `fred`

US and international economic time series held by the Federal Reserve Bank of St. Louis.

- **Family:** economic_data
- **Coverage:** PARTIAL, countries ['US'], languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible: no**
- **Last reviewed:** 2026-08-29 · next 2027-08-29

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | fred-api | auth, api key, account | `FRED_API_KEY` | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | not assessed |
| api use | not assessed |
| browser automation | not assessed |
| commercial use | not assessed |
| storage | not assessed |
| retention | not assessed |
| redistribution | not assessed |
| derived analytics | not assessed |
| model processing | not assessed |
| personal data handling | not assessed |
| attribution required | not assessed |

**Reviewer notes**

The terms page could not be retrieved: the host returned 403 to this environment. The specific risk worth naming is that FRED redistributes series owned by third parties under their own licences, so a single blanket conclusion about 'FRED data' would be wrong even if the FRED terms themselves were permissive. Nothing is assessed.

**Open questions**

- Retrieve and assess the FRED API Terms of Use at https://fred.stlouisfed.org/docs/api/terms_of_use.html, which returned HTTP 403 from this environment
- Determine whether commercial use and redistribution of derived series are permitted
- Determine which series are third-party and therefore carry separate terms that FRED's own terms do not cover
- Determine attribution requirements and documented rate limits

**Official evidence (0)**

None. This assessment rests on no retrieved document, which is why it
cannot approve anything.

**Blocked by**

- policy review is REQUIRES_REVIEW
- policy review has no evidence

---
