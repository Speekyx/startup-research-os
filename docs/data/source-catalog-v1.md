# Source Catalog V1

**Status:** Authoritative record of the initial candidate catalog.
**Catalog version:** 1.2
**Reviewed:** 2026-08-30 by `mission-1.7`
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
| `APPROVED_WITH_CONDITIONS` | 8 — eurostat, fred, gdelt, npm-registry, openalex, pypi, wikimedia-pageviews, world-bank |
| `REQUIRES_REVIEW` | 10 — bluesky, discord, google-trends, hacker-news, huggingface, pinterest, reddit, stack-exchange, twitch, x-twitter |
| `RESTRICTED` | 6 — apple-app-store, github, google-play, meta-instagram, product-hunt, steam |
| `PROHIBITED` | 3 — spotify, tiktok, youtube |
| `SUSPENDED` | 0 |
| `DRAFT` | 0 |

**Collector-eligible from the catalog alone: 0 of 27.**

This document is the **catalog view**: what the reviews say, with no condition verified. It is generated from a JSON file and committed, so it cannot depend on the machine it was rendered on -- and whether a condition holds depends on what is deployed and configured. A catalog can never assert its own conditions satisfied, so every source carrying one is shown blocked here.

For the environment view -- the same reviews with the verifiers actually run -- use `sros-source eligibility` or `sros-source conditions <source>`. The two can legitimately disagree, and only the second answers *may a collector run here*.

Either way, **no collector exists** and `collector_enabled` is false for every source. Passing the gate says a collector MAY be built.

### Limitations of this review

- Reddit's governing policy documents (Data API Terms, Developer Terms, Responsible Builder Policy) still could not be retrieved: redditinc.com remains blocked by this environment's browsing policy. Retried 2026-08-30; the Mission 1.3 verdict and its open questions stand unchanged.
- Stack Exchange's Public Network Terms of Service and Consolidated Responsible AI policy still could not be retrieved: stackoverflow.com remains unreachable from this environment. Retried 2026-08-30; the Mission 1.3 verdict stands.
- The X (Twitter) Developer Agreement and Policy returned HTTP 402 Payment Required to this environment on 2026-08-30. That is an environment limitation, not a statement by X.
- The Discord Developer Terms of Service returned HTTP 403 Forbidden on 2026-08-30.
- The Twitch Developer Services Agreement could not be read: two attempts returned the page navigation without the agreement text. The Twitch API documentation WAS retrieved and establishes the access model only.
- The Pinterest Developer and API terms did not return their text on 2026-08-30.
- No assessment here is a legal opinion. Where a conclusion would require legal judgment, the recorded value is UNCLEAR or NOT_ADDRESSED and human review is required.
- No source data was collected. Only official documentation ABOUT the sources was read, and no candidate platform was queried for content.
- Twelve sources are in an approving state and NONE is collector-eligible. The nine conditions carried by the economic three are satisfied by capabilities Mission 1.4 built; the eleven carried by the five sources approved in Mission 1.7 name verifications that no capability implements, because no collector exists for any of them.
- Signal and behaviour coverage are recorded for every source except the three PROHIBITED ones (§23) and the four whose documentation could not be retrieved, which have no basis to cite.

---

## Assessment table

Activities are assessed separately, because their conditions differ. A source may permit automated API access and forbid commercial use, and only a per-activity reading can say so.

| Source | Family | Access | Official API | Auth | Commercial | Automation | Storage | Retention | Redistribution | Rate limits | Personal data | State | Eligible |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `apple-app-store` | app_store | rss or feed | no | no | conditional | conditional | not addressed | not addressed | **not permitted** | UNKNOWN | PSEUDONYMOUS | `RESTRICTED` | **no** |
| `bluesky` | social | public api | yes | no | not addressed | not addressed | not addressed | unclear | not addressed | UNKNOWN | IDENTIFIABLE | `REQUIRES_REVIEW` | **no** |
| `discord` | community | official api | yes | yes | not assessed | not assessed | not assessed | not assessed | not assessed | UNKNOWN | IDENTIFIABLE | `REQUIRES_REVIEW` | **no** |
| `eurostat` | economic_data | public api | yes | no | conditional | permitted | permitted | permitted | conditional | UNKNOWN | NONE_EXPECTED | `APPROVED_WITH_CONDITIONS` | **no** |
| `fred` | economic_data | official api | yes | yes | conditional | permitted | permitted | permitted | conditional | UNKNOWN | NONE_EXPECTED | `APPROVED_WITH_CONDITIONS` | **no** |
| `gdelt` | news | dataset download, public api | yes | no | permitted | permitted | permitted | not addressed | conditional | UNKNOWN | PSEUDONYMOUS | `APPROVED_WITH_CONDITIONS` | **no** |
| `github` | developer | official api | yes | yes | **not permitted** | conditional | conditional | not addressed | **not permitted** | documented | PSEUDONYMOUS | `RESTRICTED` | **no** |
| `google-play` | app_store | official api | yes | yes | not addressed | conditional | not addressed | not addressed | not addressed | UNKNOWN | PSEUDONYMOUS | `RESTRICTED` | **no** |
| `google-trends` | search_trends | official api | yes | yes | not assessed | not addressed | not assessed | not assessed | not assessed | UNKNOWN | NONE_EXPECTED | `REQUIRES_REVIEW` | **no** |
| `hacker-news` | community | public api, public web | yes | no | not addressed | conditional | not addressed | not addressed | **not permitted** | documented | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `huggingface` | developer | public api | yes | no | not addressed | not addressed | not addressed | not addressed | not addressed | documented | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `meta-instagram` | social | official api | yes | yes | conditional | conditional | conditional | conditional | **not permitted** | UNKNOWN | IDENTIFIABLE | `RESTRICTED` | **no** |
| `npm-registry` | developer | public api | yes | no | permitted | conditional | permitted | not addressed | not addressed | UNKNOWN | PSEUDONYMOUS | `APPROVED_WITH_CONDITIONS` | **no** |
| `openalex` | knowledge | dataset download, public api | yes | no | permitted | permitted | permitted | permitted | permitted | UNKNOWN | IDENTIFIABLE | `APPROVED_WITH_CONDITIONS` | **no** |
| `pinterest` | product_discovery | official api | yes | yes | not assessed | not assessed | not assessed | not assessed | not assessed | UNKNOWN | IDENTIFIABLE | `REQUIRES_REVIEW` | **no** |
| `product-hunt` | product_discovery | official api | yes | yes | **not permitted** | conditional | not addressed | not addressed | not addressed | UNKNOWN | PSEUDONYMOUS | `RESTRICTED` | **no** |
| `pypi` | developer | public api | yes | no | not addressed | conditional | not addressed | not addressed | not addressed | UNKNOWN | PSEUDONYMOUS | `APPROVED_WITH_CONDITIONS` | **no** |
| `reddit` | community | official api | yes | yes | unclear | conditional | not assessed | not assessed | not assessed | UNKNOWN | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `spotify` | content_platform | official api | yes | yes | **not permitted** | **not permitted** | **not permitted** | **not permitted** | **not permitted** | UNKNOWN | UNKNOWN | `PROHIBITED` | **no** |
| `stack-exchange` | forum | official api | yes | no | unclear | conditional | not addressed | not addressed | unclear | UNKNOWN | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `steam` | gaming | official api | yes | yes | not addressed | conditional | conditional | not addressed | **not permitted** | documented | PSEUDONYMOUS | `RESTRICTED` | **no** |
| `tiktok` | social | official api | yes | yes | **not permitted** | **not permitted** | **not permitted** | not assessed | **not permitted** | UNKNOWN | IDENTIFIABLE | `PROHIBITED` | **no** |
| `twitch` | creator | official api | yes | yes | not assessed | not assessed | not assessed | not assessed | not assessed | UNKNOWN | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `wikimedia-pageviews` | knowledge | public api | yes | no | permitted | conditional | not addressed | not addressed | conditional | documented | NONE_EXPECTED | `APPROVED_WITH_CONDITIONS` | **no** |
| `world-bank` | economic_data | public api | yes | no | permitted | permitted | permitted | permitted | conditional | UNKNOWN | NONE_EXPECTED | `APPROVED_WITH_CONDITIONS` | **no** |
| `x-twitter` | social | official api | yes | yes | not assessed | not assessed | not assessed | not assessed | not assessed | UNKNOWN | IDENTIFIABLE | `REQUIRES_REVIEW` | **no** |
| `youtube` | content_platform | official api | yes | yes | not addressed | conditional | conditional | conditional | **not permitted** | UNKNOWN | PSEUDONYMOUS | `PROHIBITED` | **no** |

---

## Per-source detail

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

### Bluesky — `bluesky`

Social platform on the open AT Protocol, with a public firehose that needs no key. REQUIRES_REVIEW: the Terms of Service were retrieved and are silent on automated access, the API and AI processing.

- **Family:** social
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `PUBLIC_API` | bluesky-public-appview | nothing | — | **UNKNOWN** | `FREE_WITH_LIMITS` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | not addressed |
| api use | not addressed |
| browser automation | not addressed |
| commercial use | not addressed |
| storage | not addressed |
| retention | unclear |
| redistribution | not addressed |
| derived analytics | not addressed |
| model processing | not addressed |
| personal data handling | unclear |
| attribution required | not addressed |

**Reviewer notes**

The most instructive result in this expansion. Technically this is the most open social platform available -- an event stream of all public activity, reachable with no key, on a protocol designed for independent consumers. And it is REQUIRES_REVIEW, because the Terms of Service are SILENT on every activity that matters and silence is not permission (source-registry-v1.md §1 rule 2). The distance between 'we can reach this trivially' and 'we may use it' is the entire point of the registry, and no source in the catalog illustrates it better. Coverage IS recorded, because the capabilities are documented and the portfolio analysis has to be able to show what a blocked source would have contributed; coverage is potential and has never been permission.

**Open questions**

- Determine whether Bluesky publishes a developer or API terms document separate from the user Terms of Service. The user Terms address the relationship with account holders and say nothing to a third party reading public records.
- Determine whether Bluesky publishes documented rate limits for the public AppView and the firehose. None were found in the documents read here.
- Determine what obligations follow from the Terms' acknowledgement that deletion may not propagate across the network. A downstream holder of a deleted post is exactly the case that sentence describes, and it creates an obligation the Terms do not specify.
- Determine whether the assessed commercial use is addressed anywhere in Bluesky's own documents.

**Official evidence (2)**

- [Bluesky Terms of Service](https://bsky.social/about/support/tos) — `OFFICIAL_TERMS`, retrieved 2026-08-30, section: Your Content; Deletion
  - Effective 14 August 2025. The Terms contain no provision addressing automated access, crawling, scraping, bots or use of the API, and none addressing use of user content for machine-learning or AI model training. On content they state that Bluesky will not sell user content without permission first, and grant Bluesky rights to use content to promote and market its services and to develop, operate and enhance them -- rights held by Bluesky, not granted to third parties. On deletion they state that reasonable efforts will be made to remove content if an account is deleted, and note that because of the AT Protocol's decentralised nature complete deletion across the network may not always be possible.
- [AT Protocol](https://atproto.com/) — `OFFICIAL_API_DOCS`, retrieved 2026-08-30, section: Overview; Firehose
  - The protocol site describes an open data network in which posts, likes, follows and profiles are public JSON records, and documents a public event stream for all public activity at wss://jetstream1.us-east.bsky.network/subscribe, stating explicitly that no API key is required. It describes self-hosting and independent operators. It addresses no terms of use, no rate limits and no governance of access, because it documents a protocol rather than a service.

**Blocked by**

- policy review is REQUIRES_REVIEW

---

### Discord — `discord`

Real-time community chat. REQUIRES_REVIEW: the Developer Terms of Service returned HTTP 403 to this environment.

- **Family:** community
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | discord-api | auth, oauth, account, dev app | `DISCORD_BOT_TOKEN` | **UNKNOWN** | `UNKNOWN` |

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

No evidence. Beyond the retrieval failure there is a prior question that may make the policy question moot: most Discord content sits in private servers, so even a permissive policy would expose a small and self-selected sample. The personal-data exposure is correspondingly high -- real-time conversation among identifiable accounts. Both points are recorded so that whoever finishes this review knows the outcome may not be worth the effort even if the terms turn out to allow it.

**Open questions**

- Retrieve the Discord Developer Terms of Service. https://support-dev.discord.com/hc/articles/8562894815383-Discord-Developer-Terms-of-Service returned HTTP 403 Forbidden to this environment on 2026-08-30.
- Determine what the Developer Terms say about storing and retaining Discord data, which is understood to be constrained but was not read.
- Determine whether the Message Content privileged intent could be granted for an analytics use case, and what the approval process requires.
- Determine whether commercial use of Discord data by a third-party product is permitted at all.

**Official evidence (0)**

None. This assessment rests on no retrieved document, which is why it
cannot approve anything.

**Blocked by**

- policy review is REQUIRES_REVIEW
- policy review has no evidence

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

### The GDELT Project — `gdelt`

Global news monitoring: events, themes, tone and entity mentions extracted from worldwide news coverage. A trend and emerging-culture source whose terms are unusually permissive.

- **Family:** news
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `APPROVED_WITH_CONDITIONS` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Required conditions** — all must be satisfied before a collector may run

| Key | Verified by | Checks | Condition |
|---|---|---|---|
| `gdelt-attribution` | `HUMAN_CONFIRMATION` | `Record who confirmed the attribution surface, when, and which product views were inspected.` | A person has confirmed that the product surfaces derived from GDELT carry a citation to the GDELT Project and a link to https://www.gdeltproject.org/, as its terms require on use and on redistribution. |

None of these is satisfied *by the catalog*, and none can be: satisfaction is environment state, recorded by a verifier that says what it checked (`sros-source verify`). `APPROVED_WITH_CONDITIONS` means a collector MAY be designed, never that one may run.

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `PUBLIC_API` | gdelt-doc-api | nothing | — | **UNKNOWN** | `FREE` |
| `DATASET_DOWNLOAD` | gdelt-bulk-files | nothing | — | **UNKNOWN** | `FREE` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | permitted |
| api use | permitted |
| browser automation | not addressed |
| commercial use | permitted |
| storage | permitted |
| retention | not addressed |
| redistribution | conditional |
| derived analytics | permitted |
| model processing | permitted |
| personal data handling | not addressed |
| attribution required | conditional |

**Conditions**

- Cite the GDELT Project and link to https://www.gdeltproject.org/ on any surface derived from this source, and on any redistribution.

**Reviewer notes**

The most permissive terms in the catalog, and the only new source whose commercial-use answer is a direct quotation rather than an inference. The verdict is APPROVED_WITH_CONDITIONS rather than APPROVED solely because attribution is a stated obligation and the mechanism requires every condition to be represented as a checkable row. The condition is HUMAN_CONFIRMATION because no collector exists for this source and the attribution capability that would verify it mechanically is parameterised for a collector that has not been written.

**Open questions**

- Determine whether GDELT publishes rate limits for the DOC API anywhere on its own site; none were found on the documentation page read here, so the limit is recorded as unknown.
- Determine whether the extracted entity mentions constitute personal data under the project's own framing; the terms do not address personal data at all.

**Official evidence (1)**

- [The GDELT Project - About / Terms of Use](https://www.gdeltproject.org/about.html) — `OFFICIAL_TERMS`, retrieved 2026-08-30, section: Terms of Use
  - The page states that all datasets released by the GDELT Project are available for unlimited and unrestricted use for any academic, commercial or governmental use of any kind without fee, and that the datasets may be redistributed, rehosted, republished and mirrored in any form. The single stated obligation is that any use or redistribution include a citation to the GDELT Project and a link to https://www.gdeltproject.org/. The grant is general and does not single out AI or machine-learning processing either to permit or to forbid it; model_processing is recorded as PERMITTED on the strength of 'any kind', and the absence of an AI-specific clause is noted rather than read as a restriction.

**Blocked by**

- review conditions not satisfied: gdelt-attribution

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

### Google Trends — `google-trends`

Relative search interest over time and geography. The most direct available proxy for demand attention.

- **Family:** search_trends
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-29 | `mission-1.0` | `REQUIRES_REVIEW` | 1 |
| 2 | 2026-08-29 | `mission-1.3` | `REQUIRES_REVIEW` | 1 |
| 3 ← current | 2026-08-30 | `mission-1.7` | `REQUIRES_REVIEW` | 1 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | trends-api-alpha | auth, api key, account, dev app, approval | `GOOGLE_TRENDS_API_KEY` | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | not addressed |
| api use | conditional |
| browser automation | not addressed |
| commercial use | not assessed |
| storage | not assessed |
| retention | not assessed |
| redistribution | not assessed |
| derived analytics | not assessed |
| model processing | not assessed |
| personal data handling | not addressed |
| attribution required | not assessed |

**Reviewer notes**

Re-reviewed against a current first-party document and the verdict holds at REQUIRES_REVIEW. The blocker is unchanged in substance and now has a current citation: the official Trends API is still an alpha, announced as such, and access is granted rather than open. This is the case §8 describes as a verdict that does not change -- new authoritative evidence was read and it confirmed the existing finding rather than justifying a move. No unofficial route was considered: the absence of an open API is not a reason to scrape the web interface.

**Open questions**

- Apply to the Google Trends API alpha programme and record the outcome. The API remains alpha as of the announcement retrieved on 2026-08-30, and access is not open.
- Obtain the terms that govern the alpha, which were not reachable without programme access, and assess commercial use, storage and redistribution against them.
- Determine whether search-interest indices may be stored and redistributed as derived analytics, which no document read to date addresses.

**Official evidence (1)**

- [Introducing the Google Trends API (alpha)](https://developers.google.com/search/blog/2025/07/trends-api) — `OFFICIAL_API_DOCS`, retrieved 2026-08-30, section: Announcement; availability
  - Google's own developer blog announces the Trends API as an alpha release providing programmatic access to Search Trends data. The post presents it as an alpha rather than a generally available product, so access is granted through a programme rather than open to any developer. The announcement does not state the terms governing use of the returned data, so nothing about commercial use, storage or redistribution can be established from it.

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

### Hugging Face Hub — `huggingface`

Model, dataset and application hub. REQUIRES_REVIEW: the Terms of Service were retrieved and address neither automated access nor commercial reuse of Hub metadata.

- **Family:** developer
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `PUBLIC_API` | huggingface-hub-api | nothing | — | 500/300s (documented) | `FREE_WITH_LIMITS` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | not addressed |
| api use | not addressed |
| browser automation | not addressed |
| commercial use | not addressed |
| storage | not addressed |
| retention | not addressed |
| redistribution | not addressed |
| derived analytics | not addressed |
| model processing | not addressed |
| personal data handling | not addressed |
| attribution required | not addressed |

**Reviewer notes**

Technically the most accessible source in this expansion after Bluesky -- documented open endpoints, published numeric rate limits, no key needed for public reads -- and it does not reach an approving state, for the same reason Bluesky does not. Every governance question is NOT_ADDRESSED. Being explicit about the near-miss: the ToS DOES contain a broad licence grant, but it runs between users and covers repository content, while what this system would collect is platform metadata that no clause mentions. Reading that grant as covering metadata would be inferring permission from an adjacent one, which is the specific move §12 forbids.

**Open questions**

- Determine whether Hugging Face publishes any document addressing automated collection and commercial reuse of Hub METADATA. The Terms of Service address the relationship between users and the platform and the licence between users, and neither speaks to a third party building a commercial product on download counts and trending data.
- Determine whether the 2022 Terms have been superseded. Every other source reviewed in this round carries a materially more recent document, and a four-year-old ToS on a platform that changed this much is itself a question.
- Determine whether the per-user repository licence extends to platform-generated metadata, or stops at repository content. The wording covers content only, and the distinction decides whether anything is granted here at all.

**Official evidence (2)**

- [Hugging Face Terms of Service](https://huggingface.co/terms-of-service) — `OFFICIAL_TERMS`, retrieved 2026-08-30, section: Content; Repositories
  - Effective 15 September 2022. The Terms contain no provision addressing automated access, scraping or use of the public API, none restricting or permitting commercial use of Hub content or metadata, none addressing rate limits, and none addressing training models on Hub data. On public repositories they state that setting a repository public grants each User a perpetual, irrevocable, worldwide, royalty-free, non-exclusive licence to use, display, publish, reproduce, distribute and make derivative works. That grant concerns repository CONTENT between users; it does not address platform metadata such as download counts, likes or trending placement, which is what this system would collect.
- [Hugging Face Hub - API and Rate limits](https://huggingface.co/docs/hub/rate-limits) — `OFFICIAL_API_DOCS`, retrieved 2026-08-30, section: Rate limit tiers
  - The Hub documents open endpoints for retrieving information about models, datasets and Spaces, and states that all API calls are subject to Hub-wide rate limits. Limits are enforced over five-minute fixed windows across three buckets: 500 API requests for an anonymous client per IP address, 1000 for a free authenticated user, 2500 for PRO and higher for organisation plans. Exceeding a limit returns HTTP 429 with standard RateLimit headers. The figures are stated as current in September 2025 and the anonymous and free tiers are marked subject to change.

**Blocked by**

- policy review is REQUIRES_REVIEW

---

### Meta Platforms (Instagram and Facebook APIs) — `meta-instagram`

Instagram and Facebook platform APIs. RESTRICTED: the Platform Terms were read, they authorise use only as the developer documentation permits, and they prohibit selling or licensing Platform Data.

- **Family:** social
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `RESTRICTED` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | meta-graph-api | auth, oauth, account, dev app, approval | `META_APP_ID`, `META_APP_SECRET` | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | conditional |
| api use | conditional |
| browser automation | not addressed |
| commercial use | conditional |
| storage | conditional |
| retention | conditional |
| redistribution | **not permitted** |
| derived analytics | conditional |
| model processing | not addressed |
| personal data handling | conditional |
| attribution required | not assessed |

**Reviewer notes**

RESTRICTED, and the reasoning has two independent legs. On policy: use is authorised only as the developer documentation permits and the sale or licensing of Platform Data is prohibited, which reaches the output of a commercial intelligence product directly. On capability: the APIs are built to serve accounts a developer owns or manages, so even a permissive reading would not yield the public-behaviour sample this system needs. The second leg is the more decisive and is recorded first in the open questions, because establishing it would close the source without any further legal reading.

**Open questions**

- Determine whether any Meta API exposes PUBLIC content from accounts the developer does not own or manage. The prior question is a capability one and it may settle the source: if no such endpoint exists, the policy analysis is moot for market research.
- Determine whether market-intelligence output derived from Platform Data and sold to customers constitutes granting a licence to Platform Data, which is prohibited.
- Determine what 'authorized applicable purposes stated in Meta's developer documentation' includes, and whether third-party market research is among them.

**Official evidence (1)**

- [Meta Platform Terms](https://developers.facebook.com/terms/) — `OFFICIAL_TERMS`, retrieved 2026-08-30, section: Permitted use; Data deletion; Prohibited conduct; App review
  - Effective 3 February 2026. The terms authorise use of Platform Data only to the extent authorised by the terms themselves and by the applicable developer policies and documentation. They prohibit the sale or purchase of Platform Data and the granting of related licences. They require Platform Data to be updated or deleted promptly on request and deleted as soon as reasonably possible once it is no longer needed for a legitimate business purpose, when the service ceases, when Meta requests it, when a user requests it, or when the law requires it. Aggregated, masked or de-personalised data that can no longer be associated with a particular user, browser or device is treated differently and appears exempt from some deletion requirements. Meta may require app review or approval and may suspend apps for non-compliance.

**Blocked by**

- policy review is RESTRICTED

---

### npm public registry — `npm-registry`

The JavaScript package registry. Its terms grant replication through the public API in as many words, which makes it the clearest permitted developer-ecosystem source in the catalog.

- **Family:** developer
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `APPROVED_WITH_CONDITIONS` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Required conditions** — all must be satisfied before a collector may run

| Key | Verified by | Checks | Condition |
|---|---|---|---|
| `npm-api-only` | `HUMAN_CONFIRMATION` | `Record who confirmed that only the registry API is reached. No collector exists for this source, so there is no request path to inspect mechanically yet.` | Collection uses the public registry API exclusively; no path reads npmjs.com as a web page. |
| `npm-volume-bounded` | `HUMAN_CONFIRMATION` | `Record the ceiling chosen, the reasoning, and where it is enforced.` | A person has confirmed a monthly request ceiling well below the five million the terms name as unreasonable. |

None of these is satisfied *by the catalog*, and none can be: satisfaction is environment state, recorded by a verifier that says what it checked (`sros-source verify`). `APPROVED_WITH_CONDITIONS` means a collector MAY be designed, never that one may run.

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `PUBLIC_API` | npm-registry-api | nothing | — | **UNKNOWN** | `FREE_WITH_LIMITS` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | conditional |
| api use | permitted |
| browser automation | **not permitted** |
| commercial use | permitted |
| storage | permitted |
| retention | not addressed |
| redistribution | not addressed |
| derived analytics | permitted |
| model processing | not addressed |
| personal data handling | not addressed |
| attribution required | not addressed |

**Conditions**

- Use the public registry API only. Crawling the website is prohibited by the same document that permits the API.
- Stay far below the documented five-million-requests-per-month ceiling, and treat that figure as an outer bound rather than a budget.

**Reviewer notes**

The clearest permission in this expansion, and it is worth being precise about what it does and does not settle. The terms distinguish the WEBSITE from the PUBLIC REGISTRY and permit exactly one of them to be automated, which is a distinction a reader skimming for 'is scraping allowed' would get backwards. What remains open is everything downstream of collection: retention, redistribution and personal data are all unaddressed, so the approving state covers acquisition and not publication.

**Open questions**

- Determine whether the terms address retention of replicated registry data, and whether a package unpublished upstream must be removed downstream. The Open Source Terms are silent on both.
- Determine whether redistribution of package metadata in a user-facing product is addressed. The replication grant covers obtaining the data and does not state what may then be shown.
- Determine whether maintainer names and email addresses in package metadata require minimisation; the terms treat them as content and do not address them as personal data.

**Official evidence (1)**

- [npm Open Source Terms](https://docs.npmjs.com/policies/open-source-terms) — `OFFICIAL_TERMS`, retrieved 2026-08-30, section: Acceptable Use; Public Registry; Content
  - Effective 10 March 2022. The terms prohibit automating access to, use of or monitoring of the Website with a web crawler, browser plug-in or other program that is not a web browser, and then grant an explicit exception: data from the Public Registry may be replicated using the Public APIs per the agreement. Commercial packages are welcomed expressly, the text naming everything from hobby projects to competitive products and enterprise tooling. On volume the terms say the infrastructure must not be strained with an unreasonable number of requests and state that under no circumstances are five million requests in a single month-long period by any single individual, organisation or group of affiliated companies remotely reasonable, directing higher-volume users to the sales team. npm also reserves for itself the right to copy, publish and analyse content and share its analyses, which is a statement about npm's rights and not a grant of ours.

**Blocked by**

- review conditions not satisfied: npm-api-only, npm-volume-bounded

---

### OpenAlex — `openalex`

Open catalog of scholarly works, authors, institutions and concepts, published CC0. A learning and emerging-topic source whose licence carries no attribution obligation at all.

- **Family:** knowledge
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `APPROVED_WITH_CONDITIONS` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Required conditions** — all must be satisfied before a collector may run

| Key | Verified by | Checks | Condition |
|---|---|---|---|
| `openalex-contact-configured` | `CONFIG_REFERENCE` | `OPENALEX_CONTACT_EMAIL` | A contact address is configured for OpenAlex requests, so traffic is attributable to us as the documentation asks. |
| `openalex-spend-bounded` | `HUMAN_CONFIRMATION` | `Record who set the ceiling, what it is, and where it is enforced.` | A person has confirmed a spending ceiling for the metered API, since usage above the free allowance is billed per call. |

None of these is satisfied *by the catalog*, and none can be: satisfaction is environment state, recorded by a verifier that says what it checked (`sros-source verify`). `APPROVED_WITH_CONDITIONS` means a collector MAY be designed, never that one may run.

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `PUBLIC_API` | openalex-rest-api | nothing | `OPENALEX_CONTACT_EMAIL` | **UNKNOWN** | `FREE_WITH_LIMITS` |
| `DATASET_DOWNLOAD` | openalex-snapshot | nothing | — | **UNKNOWN** | `FREE` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | permitted |
| api use | conditional |
| browser automation | not addressed |
| commercial use | permitted |
| storage | permitted |
| retention | permitted |
| redistribution | permitted |
| derived analytics | permitted |
| model processing | permitted |
| personal data handling | not addressed |
| attribution required | not addressed |

**Conditions**

- Identify the client with a contact address so requests are attributable, as the documentation asks.
- Bound spend: the API is metered above a free allowance and returns a per-call cost.

**Reviewer notes**

CC0 is the strongest licensing position available: it removes the attribution, redistribution and model-processing questions that dominate every other source in this catalog. The conditions are therefore not about permission at all but about cost control and courtesy, which is an unusual and worth-noting shape. Personal-data risk is recorded as IDENTIFIABLE rather than NONE_EXPECTED because named authors with institutional affiliations are the substance of the corpus; a CC0 licence is not a privacy clearance.

**Open questions**

- Determine the exact free daily allowance, the allowance with a free key, and the per-call price above it. The help page describes the tiers without stating the numbers, and an unofficial figure must not be recorded here.
- Determine whether author records constitute personal data requiring minimisation. CC0 settles the licensing question and says nothing about the privacy one; author names, affiliations and identifiers are present.

**Official evidence (1)**

- [OpenAlex Help Center - API reference](https://help.openalex.org/api/) — `OFFICIAL_API_DOCS`, retrieved 2026-08-30, section: Overview; Authentication; Pricing
  - The documentation states that all OpenAlex data is CC0, that basic use is free and requires no account, that a free API key raises the daily budget tenfold, and that heavier usage is pay-as-you-go with a cost_usd figure returned per call. CC0 places the data in the public domain, which permits commercial use, storage, redistribution and model processing without an attribution obligation; the conditions that remain are operational rather than licensing, being the daily budget and the cost of exceeding it.

**Blocked by**

- review conditions not satisfied: openalex-contact-configured, openalex-spend-bounded

---

### Pinterest — `pinterest`

Visual discovery and saving platform. REQUIRES_REVIEW: the Developer Terms could not be retrieved from this environment.

- **Family:** product_discovery
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | pinterest-api | auth, oauth, account, dev app, approval | `PINTEREST_APP_ID`, `PINTEREST_APP_SECRET` | **UNKNOWN** | `UNKNOWN` |

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

Pinterest is the strongest candidate in the catalog for DESIRE signals specifically -- saving something is an expression of want with no complaint and no purchase attached, which is exactly the signal shape §24 asks whether the portfolio can detect. That is a reason to finish the review with some priority, and it is not a reason to assume the answer. No evidence was gathered and every activity is NOT_ASSESSED.

**Open questions**

- Retrieve the Pinterest Developer and API terms from https://developers.pinterest.com/terms/. The developer site was reached on 2026-08-30 but the terms document itself did not return its text.
- Determine whether the API exposes aggregate interest or trend data usable without access to individual user accounts.
- Determine whether commercial use by a third-party analytics product is permitted, and what the app review process requires.
- Determine what the terms say about storage, retention and machine-learning processing, treating them separately.

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

### Python Package Index (PyPI) — `pypi`

The Python package index. Its terms address API abuse specifically and prohibit narrow, named misuses rather than automated access as such.

- **Family:** developer
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `APPROVED_WITH_CONDITIONS` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Required conditions** — all must be satisfied before a collector may run

| Key | Verified by | Checks | Condition |
|---|---|---|---|
| `pypi-pacing` | `HUMAN_CONFIRMATION` | `Record the pacing chosen and the reasoning, given that no documented limit exists to derive it from.` | A person has confirmed a request pacing policy for PyPI, since the terms state a consequence for excessive frequency without publishing a number. |
| `pypi-no-contact-harvesting` | `HUMAN_CONFIRMATION` | `Record who confirmed the minimisation and which fields are dropped.` | Maintainer contact details are discarded at normalisation and never surfaced, in line with the terms' prohibition on downloading data to sell users' personal information. |

None of these is satisfied *by the catalog*, and none can be: satisfaction is environment state, recorded by a verifier that says what it checked (`sros-source verify`). `APPROVED_WITH_CONDITIONS` means a collector MAY be designed, never that one may run.

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `PUBLIC_API` | pypi-json-api | nothing | — | **UNKNOWN** | `FREE_WITH_LIMITS` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | conditional |
| api use | conditional |
| browser automation | not addressed |
| commercial use | not addressed |
| storage | not addressed |
| retention | not addressed |
| redistribution | not addressed |
| derived analytics | not addressed |
| model processing | not addressed |
| personal data handling | conditional |
| attribution required | not addressed |

**Conditions**

- Pace requests so they cannot be characterised as excessively frequent, since the stated consequence is suspension.
- Never extract maintainer contact details for any purpose resembling recruitment or solicitation; the terms name that use specifically.

**Reviewer notes**

Approving, but on a narrower basis than npm: PyPI's terms prohibit specific misuses rather than granting a specific use, so the approving state rests on the absence of a prohibition covering us plus the presence of a documented API, and commercial reuse itself is NOT_ADDRESSED. That is a materially weaker footing than npm's explicit replication grant, and the two should not be read as equivalent because both came out APPROVED_WITH_CONDITIONS.

**Open questions**

- Determine whether the Terms of Service address commercial reuse of package metadata anywhere. The document read here addresses API abuse and acceptable use without stating whether a commercial product may be built on the data.
- Determine whether PyPI publishes any numeric rate limit. None was found; 'excessively frequent' is the only guidance and it is not a number a collector can be built against.
- Determine whether the bulk dataset published elsewhere carries different terms from the API.

**Official evidence (1)**

- [PyPI Terms of Service](https://policies.python.org/pypi.org/Terms-of-Use/) — `OFFICIAL_TERMS`, retrieved 2026-08-30, section: API; Acceptable Use
  - Effective 25 February 2025, superseding the earlier Terms of Use. The terms state that abuse or excessively frequent requests to PyPI via the API may result in temporary or permanent suspension of an account's API access, that API tokens may not be shared in order to exceed PyPI's rate limitations, and that the API may not be used to download data or content for spamming purposes, including selling PyPI users' personal information to recruiters, headhunters and job boards. All API activity is stated to remain subject to the Terms of Service and the Privacy Policy. Automated access is therefore not prohibited as such; what is prohibited is named narrowly, and the personal-information clause bears directly on maintainer contact details.

**Blocked by**

- review conditions not satisfied: pypi-no-contact-harvesting, pypi-pacing

---

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

### Spotify — `spotify`

Music and podcast streaming. Assessed and PROHIBITED: the Developer Terms forbid storing or aggregating Spotify Content and forbid using it to train a model, in those words.

- **Family:** content_platform
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `PROHIBITED` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | spotify-web-api | auth, oauth, account, dev app | `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` | **UNKNOWN** | `FREE_WITH_LIMITS` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | **not permitted** |
| api use | conditional |
| browser automation | **not permitted** |
| commercial use | **not permitted** |
| storage | **not permitted** |
| retention | **not permitted** |
| redistribution | **not permitted** |
| derived analytics | **not permitted** |
| model processing | **not permitted** |
| personal data handling | not assessed |
| attribution required | not assessed |

**Reviewer notes**

Assessed and closed. Four of the activities this system requires -- storage, aggregation into a database, derived analytics transferred onward, and model processing -- are each prohibited by name, and the prohibition on aggregate and derivative data closes the usual fallback of keeping only statistics. No condition could be written that would make this use permissible, so no condition is written; PROHIBITED is the verdict rather than RESTRICTED because nothing in the assessed use case survives.

**Official evidence (1)**

- [Spotify Developer Terms of Service](https://developer.spotify.com/terms) — `OFFICIAL_TERMS`, retrieved 2026-08-30, section: Restrictions; Streaming and Commercial Use
  - Effective 15 May 2025. The terms state that the developer may not store, aggregate or create compilations or databases of Spotify Content other than as strictly necessary to operate the developer's own application, and separately direct the developer not to use the Spotify Platform or any Spotify Content to train a machine learning or AI model or otherwise ingest Spotify Content into such a model. They further prohibit using any robot, spider, site search or retrieval application or other tool to retrieve, duplicate or index any portion of the Spotify Service or Spotify Content, playlist data included, and prohibit transferring Spotify Content to third parties including as aggregate, anonymous or derivative data. The licence granted is limited to operating an application for private personal use on approved devices.

**Blocked by**

- policy review is PROHIBITED

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

### Steam (Valve) — `steam`

PC game store and community. The obvious gaming source, and RESTRICTED: the API grant is to distribute Steam Data to end users through an application, which is not a licence to accumulate and analyse it.

- **Family:** gaming
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `RESTRICTED` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | steam-web-api | auth, api key, account | `STEAM_WEB_API_KEY` | None/Nones (documented) | `FREE_WITH_LIMITS` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | conditional |
| api use | conditional |
| browser automation | not addressed |
| commercial use | not addressed |
| storage | conditional |
| retention | not addressed |
| redistribution | **not permitted** |
| derived analytics | not addressed |
| model processing | not addressed |
| personal data handling | conditional |
| attribution required | conditional |

**Reviewer notes**

RESTRICTED rather than REQUIRES_REVIEW, and the distinction is deliberate: the terms were retrieved and read, they plainly permit some assessed activities -- automated API access with a key, storage subject to a disclosed location, distribution to end users -- and the activity this system needs is outside the grant they make. That is the definition of RESTRICTED. It is also the most consequential verdict in this expansion, because Steam is the single richest gaming source available and the portfolio has no substitute that reaches player behaviour directly.

**Open questions**

- Determine whether accumulating Steam Data into an analytical corpus, as opposed to distributing it to end users through an Application, falls inside the granted licence. The grant is framed around distribution to end users for personal use and this system's use is neither.
- Determine whether derived market intelligence sold to customers is 'presenting Steam Data so that it appears to be available from a third party'. The prohibition's scope decides whether any user-facing output is possible.
- Determine whether Valve offers a commercial or data-partner arrangement covering analytical use, and what it requires. No such route was found in the terms read here.

**Official evidence (1)**

- [Steam Web API Terms of Use](https://steamcommunity.com/dev/apiterms) — `OFFICIAL_TERMS`, retrieved 2026-08-30, section: Licence; Restrictions; Rate limit
  - The terms grant permission to implement the Steam Web API in an Application and to distribute Steam Data to end users for their personal use via that Application. They require that Steam Data be stored in a country identified in the developer's privacy policy, that the Valve name, logos and links be implemented in accordance with the API documentation, and that the API key be kept confidential and not shared. They limit the developer to one hundred thousand calls to the Steam Web API per day, and prohibit presenting Steam Data, or permitting it to be presented, so that it appears to be available from a third party. Commercial use as such is not addressed; the grant is framed around an Application distributing data to its end users for personal use.

**Blocked by**

- policy review is RESTRICTED

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

### Twitch — `twitch`

Live streaming, predominantly gaming. REQUIRES_REVIEW: the Developer Services Agreement could not be read, though the API documentation was.

- **Family:** creator
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | twitch-helix-api | auth, oauth, account, dev app | `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET` | **UNKNOWN** | `UNKNOWN` |

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

The API documentation was retrieved and establishes the access model; the document that would establish PERMISSION was not. That split is worth stating plainly, because a reviewer who read only the API docs would find a well-documented, openly described API and could easily mistake that for a permission. Every policy activity stays NOT_ASSESSED. Twitch matters to the portfolio as the strongest available creator-economy and live-gaming source, which is a reason to finish the review and not a reason to assume its outcome.

**Open questions**

- Retrieve the Twitch Developer Services Agreement from https://legal.twitch.com/legal/developer-agreement/. Two attempts on 2026-08-30 returned the page navigation without the agreement text.
- Determine what the agreement says about storing and retaining Twitch data, and whether a caching limit applies.
- Determine whether commercial use of Twitch data by a third-party analytics product is permitted.
- Determine what the agreement says about aggregation, derived analytics and machine-learning processing, treating them separately.
- Determine the documented rate limits, which the API documentation references without stating.

**Official evidence (1)**

- [Twitch API - Reference](https://dev.twitch.tv/docs/api/) — `OFFICIAL_API_DOCS`, retrieved 2026-08-30, section: Authentication; Concepts
  - The documentation states that the Twitch API uses OAuth 2.0 for authentication and that extension endpoints require JSON Web Tokens. It refers readers to a concepts page for how Twitch handles rate limits without stating any numeric limit on the page retrieved. It establishes that a registered application and OAuth credentials are required; it establishes nothing about permitted use, which is governed by the Developer Services Agreement.

**Blocked by**

- policy review is REQUIRES_REVIEW

---

### Wikimedia Analytics (Pageviews) — `wikimedia-pageviews`

Per-article view counts across Wikimedia projects. Measures attention directly and requires no complaint, which makes it the clearest instrument in the catalog for curiosity and emerging-interest signals.

- **Family:** knowledge
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `APPROVED_WITH_CONDITIONS` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Required conditions** — all must be satisfied before a collector may run

| Key | Verified by | Checks | Condition |
|---|---|---|---|
| `wikimedia-user-agent` | `HUMAN_CONFIRMATION` | `Record who confirmed the outbound User-Agent, and against which client version. No collector exists for this source, so there is nothing yet to inspect mechanically.` | Every request carries a User-Agent naming the client, its version and a contact address, per the Wikimedia User-Agent Policy. |
| `wikimedia-attribution` | `HUMAN_CONFIRMATION` | `Record who confirmed the attribution surface and which views were inspected.` | Product surfaces that display Wikimedia article content, as distinct from aggregate view counts, carry CC BY-SA attribution and a link to the article. |

None of these is satisfied *by the catalog*, and none can be: satisfaction is environment state, recorded by a verifier that says what it checked (`sros-source verify`). `APPROVED_WITH_CONDITIONS` means a collector MAY be designed, never that one may run.

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `PUBLIC_API` | wikimedia-analytics-api | nothing | — | 200/60s (documented) | `FREE_WITH_LIMITS` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | conditional |
| api use | conditional |
| browser automation | not addressed |
| commercial use | permitted |
| storage | not addressed |
| retention | not addressed |
| redistribution | conditional |
| derived analytics | permitted |
| model processing | not addressed |
| personal data handling | not addressed |
| attribution required | conditional |

**Conditions**

- Send a descriptive User-Agent naming the client and a contact address, in the format the User-Agent Policy prescribes.
- Stay within the documented per-minute rate limit and honour HTTP 429 with its Retry-After header.
- Attribute Wikimedia content and honour CC BY-SA where article content, as opposed to aggregate view counts, is surfaced.

**Reviewer notes**

Commercial reuse is permitted in the Foundation's own words, which is rare and is the reason this source reaches an approving state on first review. What is conditional is the manner of access: the User-Agent Policy is explicit, the rate limits are published, and both are obligations rather than courtesies. The open question about whether view COUNTS carry CC BY-SA is left open rather than resolved in our favour -- a chart of numbers is plausibly not a derivative of the licensed text, but plausibly is not a finding.

**Open questions**

- Determine whether aggregate pageview COUNTS are themselves subject to CC BY-SA, or whether the licence attaches only to article text. The Analytics API documentation labels its content CC BY-SA 4.0 without distinguishing the two, and the answer changes whether attribution is required on a chart of view counts.
- Determine whether the Foundation's storage and retention expectations for pageview data are addressed anywhere in its own documents; neither the Terms of Use nor the API access policy addresses storage by a reuser.
- Determine whether Wikimedia Enterprise is REQUIRED rather than merely offered for a commercial reuser at this volume; the APIs overview presents it as the route for high-volume commercial reuse without stating a threshold at which it becomes mandatory.

**Official evidence (3)**

- [Wikimedia Foundation Terms of Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use) — `OFFICIAL_TERMS`, retrieved 2026-08-30, section: Reuse; Licensing of Content; Refraining from Certain Activities
  - Effective 7 June 2023. The Foundation states that the licences applied to project content do allow commercial uses of contributions provided the use complies with the terms of the respective licence, and that text is licensed CC BY-SA 4.0 and GFDL. Attribution may be satisfied by a hyperlink or URL to the article contributed to. The terms prohibit automated uses that are abusive or disruptive, that violate applicable acceptable-usage policies, or that have not been approved by the community, and state that by using the APIs the user agrees to abide by the User-Agent Policy, the Robot Policy and API:Etiquette. Commercial reuse is therefore permitted; the constraint is on HOW automated access is conducted, not on whether the result may be sold.
- [Wikimedia APIs - Rate limits](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits) — `OFFICIAL_API_DOCS`, retrieved 2026-08-30, section: Rates by client type
  - Limits are enforced per minute across the Action API and the REST APIs: 10 requests per minute for a client identified only by IP address, 200 for an unauthenticated client sending a User-Agent, 200 for a new authenticated account, 2000 for an established editor, and exemption for bot-flagged and approved clients. Exceeding a limit returns HTTP 429 with a Retry-After header; where no such header is present the documentation directs clients to wait at least five seconds or apply exponential back-off. The page states these limits are new in 2026 and subject to change.
- [Wikimedia Foundation User-Agent Policy](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy) — `OFFICIAL_ACCESS_CONTROL`, retrieved 2026-08-30, section: Format
  - Automated clients must send an informative User-Agent identifying the client, its version and contact information, in the form 'CoolBot/0.0 (https://example.org/coolbot/; coolbot@example.org) generic-library/0.0'. The policy states that scripts should use an informative User-Agent string with contact information or they may be blocked without notice, and directs clients not to copy a browser user agent and not to use a generic one such as curl or python-requests.

**Blocked by**

- review conditions not satisfied: wikimedia-attribution, wikimedia-user-agent

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

### X (Twitter) — `x-twitter`

Short-form social platform. REQUIRES_REVIEW: the Developer Agreement and Policy could not be retrieved from this environment, which returned HTTP 402.

- **Family:** social
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | x-api-v2 | auth, oauth, account, dev app, approval | `X_API_KEY`, `X_API_SECRET` | **UNKNOWN** | `UNKNOWN` |

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

No evidence was gathered and every activity is NOT_ASSESSED. The governing document returned HTTP 402 Payment Required to this environment, which is an environment limitation and not a statement by X; it is recorded as such rather than treated as a refusal. Nothing about commercial use, storage, retention, redistribution or model processing can be asserted, and the widely-held understanding that X restricts these is not evidence and is not recorded as any. No scraping route was considered: difficulty obtaining the terms is not a reason to bypass them.

**Open questions**

- Retrieve the X Developer Agreement and Policy from https://developer.x.com/en/developer-terms/agreement-and-policy in an environment that can reach it. This environment received HTTP 402 Payment Required for that URL on 2026-08-30.
- Determine which access tier a commercial multi-tenant SaaS requires and what it costs.
- Determine what the agreement says about storage and retention of X Content, and about deletion obligations when a user deletes a post.
- Determine what the agreement says about using X Content for machine learning or AI model training, separately from what it says about analysis.
- Determine whether off-platform aggregate analysis and derived analytics are permitted, and whether derived output may be shown to customers.

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
