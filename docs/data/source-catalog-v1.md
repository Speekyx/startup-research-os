# Source Catalog V1

**Status:** Authoritative record of the initial candidate catalog.
**Catalog version:** 1.5
**Reviewed:** 2026-08-30 by `mission-1.9.2`
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
| `APPROVED_WITH_CONDITIONS` | 5 — eurostat, fred, gdelt, openalex, world-bank |
| `REQUIRES_REVIEW` | 13 — bluesky, discord, google-trends, huggingface, npm-registry, pypi, reddit, stack-exchange, ted-eu, twitch, usaspending, wikimedia-pageviews, x-twitter |
| `RESTRICTED` | 8 — apple-app-store, github, google-play, hacker-news, meta-instagram, pinterest, product-hunt, steam |
| `PROHIBITED` | 3 — spotify, tiktok, youtube |
| `SUSPENDED` | 0 |
| `DRAFT` | 0 |

**Collector-eligible from the catalog alone: 0 of 29.**

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
- Signal and behaviour coverage are recorded for every source except the three PROHIBITED ones (§23) and the four whose documentation could not be retrieved, which have no basis to cite.
- Mission 1.8 audited every approving review against the assessed use and downgraded three that rested on silence rather than on a grant: `pypi` (four of six required activities unaddressed), `npm-registry` (three, after two assessments were corrected to what their evidence actually says) and `wikimedia-pageviews` (two, after a documentation-site footer was corrected to not be a data licence). Every Mission 1.7 review version is preserved.
- Five sources are in an approving state and four are collector-eligible in a verified environment. GDELT joined the economic three by having its attribution, resource-scope and access obligations expressed as machine-verified conditions; no gate was relaxed to admit it.
- The gdelt-doc-api access profile had no endpoint_url until Mission 1.9, so the host allowlist any GDELT collector derives from the registry was empty and no request could have been made. Found by trying to use the registration rather than by reading it.
- GDELT does not state a timezone for the WEB-NGRAM DATE column anywhere on the dataset announcement or the data index, and no first-party statement was found. Mission 1.9.1 recorded it as UTC; review 3 does not assert it and carries it as an open question (H-29). The value is preserved as the source label so that answering it later costs no re-collection.
- No mapping from the CLD2 language names GDELT emits (ALBANIAN, some titlecase, some with underscores) to language tags was found, so no language code is derived from LANG (H-30). Separately, how far back the WEB-NGRAM publication directory stays retrievable is undocumented, so no historical backfill window is assumed (H-31).

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
| `hacker-news` | community | public api, public web | yes | no | **not permitted** | **not permitted** | **not permitted** | not addressed | **not permitted** | documented | PSEUDONYMOUS | `RESTRICTED` | **no** |
| `huggingface` | developer | public api | yes | no | not addressed | not addressed | not addressed | not addressed | not addressed | documented | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `meta-instagram` | social | official api | yes | yes | conditional | conditional | conditional | conditional | **not permitted** | UNKNOWN | IDENTIFIABLE | `RESTRICTED` | **no** |
| `npm-registry` | developer | public api | yes | no | not addressed | conditional | permitted | not addressed | not addressed | UNKNOWN | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `openalex` | knowledge | dataset download, public api | yes | no | permitted | permitted | permitted | permitted | permitted | UNKNOWN | IDENTIFIABLE | `APPROVED_WITH_CONDITIONS` | **no** |
| `pinterest` | product_discovery | official api | yes | yes | **not permitted** | **not permitted** | **not permitted** | **not permitted** | **not permitted** | UNKNOWN | IDENTIFIABLE | `RESTRICTED` | **no** |
| `product-hunt` | product_discovery | official api | yes | yes | **not permitted** | conditional | not addressed | not addressed | not addressed | UNKNOWN | PSEUDONYMOUS | `RESTRICTED` | **no** |
| `pypi` | developer | public api | yes | no | not addressed | conditional | not addressed | not addressed | not addressed | UNKNOWN | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `reddit` | community | official api | yes | yes | unclear | conditional | not assessed | not assessed | not assessed | UNKNOWN | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `spotify` | content_platform | official api | yes | yes | **not permitted** | **not permitted** | **not permitted** | **not permitted** | **not permitted** | UNKNOWN | UNKNOWN | `PROHIBITED` | **no** |
| `stack-exchange` | forum | dataset download, official api | yes | no | unclear | conditional | not addressed | not addressed | unclear | UNKNOWN | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `steam` | gaming | official api | yes | yes | not addressed | conditional | conditional | not addressed | **not permitted** | documented | PSEUDONYMOUS | `RESTRICTED` | **no** |
| `ted-eu` | public_procurement | dataset download, official api | yes | no | permitted | permitted | permitted | permitted | permitted | UNKNOWN | IDENTIFIABLE | `REQUIRES_REVIEW` | **no** |
| `tiktok` | social | official api | yes | yes | **not permitted** | **not permitted** | **not permitted** | not assessed | **not permitted** | UNKNOWN | IDENTIFIABLE | `PROHIBITED` | **no** |
| `twitch` | creator | official api | yes | yes | not assessed | not assessed | not assessed | not assessed | not assessed | UNKNOWN | PSEUDONYMOUS | `REQUIRES_REVIEW` | **no** |
| `usaspending` | public_procurement | official api | yes | no | not addressed | not addressed | not addressed | not addressed | not addressed | UNKNOWN | UNKNOWN | `REQUIRES_REVIEW` | **no** |
| `wikimedia-pageviews` | knowledge | dataset download, official api | yes | no | permitted | conditional | not addressed | not addressed | conditional | documented | NONE_EXPECTED | `REQUIRES_REVIEW` | **no** |
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
| external model transmission | not assessed |
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

- policy review for use profile 'commercial-multi-tenant-research-v1' is RESTRICTED

---

### Bluesky — `bluesky`

Social platform on the open AT Protocol, with a public firehose that needs no key. REQUIRES_REVIEW: the Terms of Service were retrieved and are silent on automated access, the API and AI processing.

- **Family:** social
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-31 · next 2027-02-27

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-30 | `mission-1.7` | `REQUIRES_REVIEW` | 2 |
| 2 ← current | 2026-08-31 | `mission-1.15` | `REQUIRES_REVIEW` | 3 |

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
| external model transmission | not assessed |
| personal data handling | unclear |
| attribution required | not addressed |

**Reviewer notes**

The verdict does not change and the question does. v1 asked whether a developer terms document exists separate from the user Terms of Service; it does -- Bluesky's own documentation domain names 'Bluesky Developer Guidelines' -- and it could not be retrieved: the canonical URL redirects permanently to bsky.network and that host returned an empty body. No mirror, cache or third-party copy was consulted, because a retrieval failure leaves a question unresolved rather than licensing a substitute. The Terms of Service were re-retrieved at their current version, updated effective 15 September 2025 after v1 was written, and remain silent on all ten activities that matter to a third party reading public records. Bluesky is therefore still the catalog's sharpest illustration of technical openness without a governing grant -- but the open question is now one retrievable document rather than four unknowns.

**Open questions**

- Retrieve the Bluesky Developer Guidelines. The document is named by Bluesky's own documentation domain at https://docs.bsky.app/docs/support/developer-guidelines, which redirects permanently to https://bsky.network/docs/support/developer-guidelines and returned an empty body on 2026-08-31. This is the single question standing between Bluesky and an assessable verdict.
- Determine whether Bluesky publishes documented rate limits for the public AppView and the firehose. None were found in the documents read here or in v1.
- Determine what obligations follow from the Terms' acknowledgement that deletion may not propagate across the network. A downstream holder of a deleted post is exactly the case that sentence describes, and it creates an obligation the Terms do not specify.

**Official evidence (3)**

- [Bluesky Terms of Service (current version)](https://bsky.social/about/support/tos) — `OFFICIAL_TERMS`, retrieved 2026-08-31, section: Whole document
  - Re-retrieved on 2026-08-31 following the terms update announced for 15 September 2025. The document remains silent, for a third party reading public records, on automated access and crawling, API use, commercial use, storage or caching, derived analytics, machine-learning inference, embeddings, model training, redistribution and rate limits. It addresses deletion only, stating that because of the AT Protocol's decentralised nature Bluesky cannot control or force other services and developer applications.
- [Bluesky Developer Guidelines](https://bsky.network/docs/support/developer-guidelines) — `OFFICIAL_TERMS`, retrieved 2026-08-31, section: Retrieval failure
  - Named by Bluesky's documentation domain as the guidelines developers who federate apps or services on the AT Protocol must follow to communicate with Bluesky services. The canonical URL docs.bsky.app/docs/support/developer-guidelines returned HTTP 301 to bsky.network/docs/support/developer-guidelines, and that URL returned an empty body on 2026-08-31. The documentation root at bsky.network links to no terms, guidelines or legal document. The document's existence is established; its content is not.
- [Bluesky: Updated Terms and Policies](https://bsky.social/about/blog/08-14-2025-updated-terms-and-policies) — `OFFICIAL_TERMS`, retrieved 2026-08-31, section: Effective dates
  - Announces updated Terms of Service, Privacy Policy and Copyright Policy effective 15 September 2025 and updated Community Guidelines effective 15 October 2025. The announcement addresses regulatory compliance and names no developer, API, commercial-use or machine-learning provision, and links to no developer terms document.

**Blocked by**

- policy review for use profile 'commercial-multi-tenant-research-v1' is REQUIRES_REVIEW

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
| external model transmission | not assessed |
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

- policy review for use profile 'commercial-multi-tenant-research-v1' is REQUIRES_REVIEW
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
| 1 | 2026-09-01 | `mission-1.17` | `APPROVED_WITH_CONDITIONS` | 1 |

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
| external model transmission | not assessed |
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
| 1 | 2026-09-01 | `mission-1.17` | `APPROVED_WITH_CONDITIONS` | 1 |

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
| external model transmission | not assessed |
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

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-30 | `mission-1.7` | `APPROVED_WITH_CONDITIONS` | 1 |
| 2 | 2026-08-30 | `mission-1.8` | `APPROVED_WITH_CONDITIONS` | 1 |
| 3 ← current | 2026-08-30 | `mission-1.9.2` | `APPROVED_WITH_CONDITIONS` | 4 |
| 1 | 2026-09-01 | `mission-1.17` | `APPROVED_WITH_CONDITIONS` | 4 |
| 2 | 2026-09-02 | `mission-1.29` | `APPROVED_WITH_CONDITIONS` | 5 |

**Required conditions** — all must be satisfied before a collector may run

| Key | Verified by | Checks | Condition |
|---|---|---|---|
| `gdelt-attribution` | `CAPABILITY` | `source-attribution-display` | Every product surface derived from GDELT carries a citation to the GDELT Project and a link to https://www.gdeltproject.org/, as its terms require on use and on redistribution. |

None of these is satisfied *by the catalog*, and none can be: satisfaction is environment state, recorded by a verifier that says what it checked (`sros-source verify`). `APPROVED_WITH_CONDITIONS` means a collector MAY be designed, never that one may run.

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `PUBLIC_API` | gdelt-doc-api | nothing | — | **UNKNOWN** | `FREE` |
| `DATASET_DOWNLOAD` | gdelt-web-ngram-files | nothing | — | **UNKNOWN** | `FREE` |

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
| external model transmission | not assessed |
| personal data handling | not addressed |
| attribution required | conditional |

**Conditions**

- Cite the GDELT Project and link to https://www.gdeltproject.org/ on any surface derived from this source, and on any redistribution.

**Reviewer notes**

Verdict, rights basis and obligation all UNCHANGED. What is new is a capability and an access route, and recording those is substantive review work rather than a configuration edit -- reviews 1 and 2 assessed news events, themes, entity mentions, tone, timestamps and geography reached over the DOC API, and a term frequency reached as a published file is none of those things. ASSESSED HERE: the WEB-NGRAM 1gram and 2gram datasets, DATASET_DOWNLOAD access to data.gdeltproject.org/gdeltv3/web/ngrams/, and the four published columns DATE, LANG, NGRAM and COUNT. The rights basis is re-cited rather than re-argued: the terms grant 'unlimited and unrestricted use ... of any kind without fee' over ALL DATASETS RELEASED BY the GDELT Project, and these are datasets it releases, so the same DIRECT_GRANT covers them and no licence identifier exists to name. CONTENT ORIGIN. The file is GDELT's own count over its own index and contains no publisher title, URL, image or sentence -- PLATFORM_LICENSED. The news material it counts belongs to publishers who granted nothing and stays THIRD_PARTY and refused. An aggregate ABOUT third-party material is not third-party material, and the distinction is the same one review 2 relied on. 1GRAM AND 2GRAM ARE BOTH APPROVED, as separate resources rather than as one family. The governance model is identical for both -- same grant, same origin, same four columns, same absence of any link to an article -- and the length difference has nothing to hang a distinction on: neither file carries a position, a document id or a URL, so no fragment can be attached to the article it came from. That is precisely what disqualifies the other two ngram products, and it is why a two-word phrase here is further from an excerpt than a seven-word snippet there. Separate entries so that withdrawing 2gram later is a deletion rather than a re-derivation. POSITIVELY REJECTED, having been read: Web News NGrams 3.0 (gdeltv3/webngrams/) carries pre/post contextual snippets and the article url; the quadgram TOC (gdeltv5/weblegacy/) carries title, img and url and keys its counts to a per-document DOCID. Both are publisher content by the same rule that rejected the DOC API's ArtList mode in Mission 1.9, and being newer or more prominently announced does not change it. A CORRECTION TO THE RECORD. GDELT does ask researchers to 'switch their searches to use these ngram files instead of the search APIs for the time being', and Mission 1.9.1 read that as support for the WEB-NGRAM path. It is not: the sentence appears in the post announcing the QUADGRAM dataset and refers to that dataset, which this review rejects. The half that does carry over is the reason -- GDELT describes its legacy search infrastructure as struggling during a migration to Spanner -- and that is why the DOC API is deferred. This review's case for WEB-NGRAM rests on the dataset's own documentation and its observed structure, not on a recommendation that was about something else. PERSONAL DATA. Structurally there is none: four columns, no name field, no author, no identifier, no profile. A lexical term can nonetheless BE a person's name, carrying one number and no link to any article. That is recorded rather than resolved -- whether it is personal data in the regulatory sense is jurisdiction, which is H-12 and deferred project-wide. The classification stays PSEUDONYMOUS; reading one dataset's structure as a statement about the source would be the wrong move in the permissive direction. VOLUME. 96 buckets a day and two files each, each file spanning every language GDELT monitors. The review approves a bounded subset rather than the dataset, and the bound is recorded in the compliance configuration where it is checkable.

**Open questions**

- Determine whether GDELT publishes rate limits anywhere on its own site, for either route; none were found and none is invented, so both profiles record the limit as unknown.
- Determine whether the extracted entity mentions on the DOC API route constitute personal data under the project's own framing; the terms do not address personal data at all, and the source is classified PSEUDONYMOUS on the shape of the data rather than on a statement by the project.
- Determine the timezone of the WEB-NGRAM DATE column. Neither the dataset announcement nor the data page states one, so this review does not assert UTC; the collector must preserve the source label verbatim so that answering this later costs no re-collection.
- Determine whether GDELT publishes a mapping from the CLD2 language names it emits (ALBANIAN, and a few in titlecase or with underscores) to language tags. None was found, so the source label is preserved and no code is guessed.
- Determine how long WEB-NGRAM files stay retrievable at the publication path. The announcement states coverage from 2019-01-01 to present and says nothing about how far back the directory itself reaches, so no historical backfill window is assumed.

**Official evidence (4)**

- [The GDELT Project - About / Terms of Use](https://www.gdeltproject.org/about.html) — `OFFICIAL_TERMS`, retrieved 2026-08-30, section: Terms of Use
  - The page states that all datasets released by the GDELT Project are available for unlimited and unrestricted use for any academic, commercial or governmental use of any kind without fee, and that the datasets may be redistributed, rehosted, republished and mirrored in any form. The single stated obligation is that any use or redistribution include a citation to the GDELT Project and a link to https://www.gdeltproject.org/. The grant is general and does not single out AI or machine-learning processing either to permit or to forbid it; model_processing is recorded as PERMITTED on the strength of 'any kind', and the absence of an AI-specific clause is noted rather than read as a restriction.
- [The GDELT Project - Announcing The Web News Ngram Datasets (WEB-NGRAM)](https://blog.gdeltproject.org/announcing-the-web-news-ngram-datasets-web-ngram/) — `OFFICIAL_API_DOCS`, retrieved 2026-08-30, section: Dataset description and file format
  - The operator's own announcement of the dataset, published 2019-09-30 and linked from the GDELT data page as its documentation. It states the publication path 'http://data.gdeltproject.org/gdeltv3/web/ngrams/YYYYMMDDHHMMSS.1gram/2gram.txt.gz'; that every 15 minutes two gzipped UTF-8 files are produced, one for unigrams and one for bigrams, typically 7-10, 22-25, 37-40 and 52-55 minutes after the hour; that each row represents a unique language/word/phrase, is tab delimited and has no header row; and that the four columns are DATE ('The date in YYYYMMDDHHMMSS format'), LANG ('The human-readable language name as output by CLD2'), NGRAM ('The word or phrase') and COUNT ('The number of times the word/phrase was mentioned in articles of that language published in that given 15 minute interval'). Coverage at release is stated as 42 billion words in 142 languages from 2019-01-01 to present. No timezone is stated for DATE, and none is inferred here. Each file spans every language rather than being partitioned by one, which is why a job cannot request fewer languages than a file contains.
- [The GDELT Project - Data](https://www.gdeltproject.org/data.html) — `OFFICIAL_API_DOCS`, retrieved 2026-08-30, section: GDELT WEB-NGRAM
  - The operator's dataset index lists WEB-NGRAM as a current product -- 'Global online news ngrams in 152 languages' -- and links to the announcement above as its documentation. The language count is higher than the 142 the 2019 announcement states, so the dataset has grown; both figures are recorded with their dates rather than one being chosen. The page states no timezone for GDELT timestamps anywhere, which is why review 3 leaves the DATE timezone as an open question instead of asserting UTC.
- [The GDELT Project - Using The New Web NGrams Dataset To Find Relevant Coverage](https://blog.gdeltproject.org/using-the-new-web-ngrams-dataset-to-find-relevant-coverage/) — `OFFICIAL_API_DOCS`, retrieved 2026-08-30, section: Legacy search infrastructure and the quadgram dataset
  - Published 2026-06-30. The operator states that 'While the transition of our search and API infrastructure to Spanner is still underway, our existing legacy search infrastructure is struggling to handle the ever-growing volume of searches', and asks that 'Researchers should try to switch their searches to use these ngram files instead of the search APIs for the time being until we have completed our migration to Spanner'. Read carefully, that recommendation names the QUADGRAM dataset the same post announces -- per-minute files at storage.googleapis.com/data.gdeltproject.org/gdeltv5/weblegacy/ngrams/, whose ngrams file keys quadgram counts to a per-document DOCID and whose companion toc.json.gz carries title, img and url. This review rejects that dataset and does NOT claim GDELT recommended WEB-NGRAM. What the document does establish first-party is the state of the legacy search infrastructure, which is the reason the DOC API route is deferred rather than retried.

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
| external model transmission | not assessed |
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

- policy review for use profile 'commercial-multi-tenant-research-v1' is RESTRICTED

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
| external model transmission | not assessed |
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

- policy review for use profile 'commercial-multi-tenant-research-v1' is RESTRICTED

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
| external model transmission | not assessed |
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

- policy review for use profile 'commercial-multi-tenant-research-v1' is REQUIRES_REVIEW

---

### Hacker News — `hacker-news`

Technology and startup discussion. Useful for early product launches and developer-audience reaction.

- **Family:** community
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `RESTRICTED` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-31 · next 2027-08-31

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-29 | `mission-1.0` | `REQUIRES_REVIEW` | 1 |
| 2 | 2026-08-29 | `mission-1.3` | `REQUIRES_REVIEW` | 2 |
| 3 ← current | 2026-08-31 | `mission-1.15` | `RESTRICTED` | 2 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `PUBLIC_API` | firebase-api | nothing | — | **UNKNOWN** | `UNKNOWN` |
| `PUBLIC_WEB` | site-crawl | nothing | — | 1/30s (documented) | `FREE` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | **not permitted** |
| api use | unclear |
| browser automation | not assessed |
| commercial use | **not permitted** |
| storage | **not permitted** |
| retention | not addressed |
| redistribution | **not permitted** |
| derived analytics | **not permitted** |
| model processing | not addressed |
| external model transmission | not assessed |
| personal data handling | not addressed |
| attribution required | not addressed |

**Reviewer notes**

The clearest demonstration in the catalog of the rule that technical accessibility is not permission. The Hacker News API is published on GitHub, documented, needs no key, and states 'There is currently no rate limit' -- an invitation by every engineering measure. The governing Y Combinator Terms of Use, which bring news.ycombinator.com in scope explicitly, prohibit 'any data mining, robots, scraping or similar data gathering or extraction methods' and prohibit reproducing, creating derivative works from or exploiting any portion of the Site for any commercial purposes. Both halves of this engine's use are named. v2 recorded REQUIRES_REVIEW because the governing terms had not been retrieved; they have been now, and they answer the question against us. The MIT licence on the API's GitHub repository covers that repository's documentation, not the content Hacker News serves.

**Open questions**

- Whether Y Combinator would grant written permission for automated collection of Hacker News content for a commercial research product. The Terms prohibit the activity and describe no permission route, so this is operator correspondence rather than a document to retrieve.

**Official evidence (2)**

- [Y Combinator Terms of Use](https://www.ycombinator.com/legal/) — `OFFICIAL_TERMS`, retrieved 2026-08-31, section: Terms of Use; prohibited conduct
  - States that use of certain components of the Site is subject to additional terms including the Hacker News Guidelines at news.ycombinator.com/newsguidelines.html, which places Hacker News within this document's scope. Prohibits engaging in or using any data mining, robots, scraping or similar data gathering or extraction methods. Separately prohibits displaying, distributing, licensing, reproducing, duplicating, copying, creating derivative works from, modifying, selling, reselling, exploiting or transferring any portion of the Site for any commercial purposes, excepting a user's own content.
- [Hacker News API](https://github.com/HackerNews/API) — `OFFICIAL_API_DOCS`, retrieved 2026-08-31, section: Overview; rate limits
  - Documents a public Firebase-backed API requiring no key and states 'There is currently no rate limit'. Carries no terms of use and addresses none of commercial use, storage, automated collection, derived analytics or machine learning. The repository's MIT licence applies to the repository, which contains documentation rather than Hacker News content.

**Blocked by**

- policy review for use profile 'commercial-multi-tenant-research-v1' is RESTRICTED

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
| external model transmission | not assessed |
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

- policy review for use profile 'commercial-multi-tenant-research-v1' is REQUIRES_REVIEW

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
| external model transmission | not assessed |
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

- policy review for use profile 'commercial-multi-tenant-research-v1' is RESTRICTED

---

### npm public registry — `npm-registry`

The JavaScript package registry. Its terms grant replication through the public API in as many words, which makes it the clearest permitted developer-ecosystem source in the catalog.

- **Family:** developer
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-30 | `mission-1.7` | `APPROVED_WITH_CONDITIONS` | 1 |
| 2 ← current | 2026-08-30 | `mission-1.8` | `REQUIRES_REVIEW` | 1 |

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
| commercial use | not addressed |
| storage | permitted |
| retention | not addressed |
| redistribution | not addressed |
| derived analytics | not addressed |
| model processing | not addressed |
| external model transmission | not assessed |
| personal data handling | not addressed |
| attribution required | not addressed |

**Reviewer notes**

DOWNGRADED on audit. Two assessments in version 1 overstated the evidence they cited. 'Commercial packages are welcomed expressly' is about what may be PUBLISHED TO npm, not about commercial reuse of registry data by a third party; and the right to 'copy, publish and analyze content and share its analyses' is granted to npm, which version 1's own evidence note said in so many words before the assessment recorded it as a permission of ours. What the terms genuinely grant is narrow and real and is unchanged here: 'You may replicate data from the Public Registry using the Public APIs' -- replication, which is storage, plus API access. With commercial_use, derived_analytics and model_processing all unaddressed, three of the six materially required activities have no grant. Corrected rather than defended: npm's replication grant remains the clearest sentence any source in this catalog offers, and it does not reach as far as version 1 read it.

**Open questions**

- Determine whether any npm or GitHub document positively permits commercial reuse of public registry metadata by a third-party product.
- Determine whether derived analytics over registry metadata by a party other than npm is addressed anywhere.
- Determine whether model processing of registry metadata is addressed.
- Determine whether the terms address retention of replicated registry data, and whether a package unpublished upstream must be removed downstream.
- Retained from version 1 as obligations that would apply IF a grant is found: use the public registry API only, never the website; and stay far below the five million requests a month the terms name as unreasonable.

**Official evidence (1)**

- [npm Open Source Terms](https://docs.npmjs.com/policies/open-source-terms) — `OFFICIAL_TERMS`, retrieved 2026-08-30, section: Acceptable Use; Public Registry; Content
  - Effective 10 March 2022. The terms prohibit automating access to, use of or monitoring of the Website with a web crawler, browser plug-in or other program that is not a web browser, and then grant an explicit exception: data from the Public Registry may be replicated using the Public APIs per the agreement. Commercial packages are welcomed expressly, the text naming everything from hobby projects to competitive products and enterprise tooling. On volume the terms say the infrastructure must not be strained with an unreasonable number of requests and state that under no circumstances are five million requests in a single month-long period by any single individual, organisation or group of affiliated companies remotely reasonable, directing higher-volume users to the sales team. npm also reserves for itself the right to copy, publish and analyse content and share its analyses, which is a statement about npm's rights and not a grant of ours.

**Blocked by**

- policy review for use profile 'commercial-multi-tenant-research-v1' is REQUIRES_REVIEW

---

### OpenAlex — `openalex`

Open catalog of scholarly works, authors, institutions and concepts, published CC0. A learning and emerging-topic source whose licence carries no attribution obligation at all.

- **Family:** knowledge
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `APPROVED_WITH_CONDITIONS` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 ← current | 2026-08-30 | `mission-1.7` | `APPROVED_WITH_CONDITIONS` | 1 |
| 1 | 2026-09-01 | `mission-1.17` | `APPROVED_WITH_CONDITIONS` | 1 |

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
| external model transmission | not assessed |
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
- **State:** `RESTRICTED` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-31 · next 2027-08-31

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-30 | `mission-1.7` | `REQUIRES_REVIEW` | 0 |
| 2 ← current | 2026-08-31 | `mission-1.15` | `RESTRICTED` | 2 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | pinterest-api | auth, oauth, account, dev app, approval | `PINTEREST_APP_ID`, `PINTEREST_APP_SECRET` | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | **not permitted** |
| api use | conditional |
| browser automation | not assessed |
| commercial use | **not permitted** |
| storage | **not permitted** |
| retention | **not permitted** |
| redistribution | **not permitted** |
| derived analytics | **not permitted** |
| model processing | **not permitted** |
| external model transmission | not assessed |
| personal data handling | unclear |
| attribution required | not addressed |

**Reviewer notes**

The verdict changed on retrieved first-party evidence, and it changed in the direction nobody hoped for. Mission 1.7 called Pinterest the catalog's strongest DESIRE candidate -- saving something is an expression of want with no complaint and no purchase attached -- and Mission 1.15 retrieved the developer guidelines that v1 could not reach. They close it. Four clauses each independently incompatible with this engine: no storage of API information at all ('call the API each time'), automated extraction prohibited, ML training prohibited, and API information usable only to serve and evaluate ads ON Pinterest. The fifth names the product directly -- platform insights, benchmarking and competitor research require explicit written authorization. RESTRICTED rather than PROHIBITED because a written authorization is a route Pinterest itself describes; it is an external commercial action and not something a reviewer can resolve. A definite no is worth more than a hopeful maybe: this closes the portfolio's best DESIRE hypothesis on evidence instead of leaving it open on silence.

**Open questions**

- Whether Pinterest grants explicit written authorization for platform insights, benchmarking or competitor research features, and on what commercial terms. The guidelines name that authorization as the only route; obtaining one is an external action, not a review finding.

**Official evidence (2)**

- [Pinterest Developer Guidelines](https://policy.pinterest.com/en/developer-guidelines) — `OFFICIAL_TERMS`, retrieved 2026-08-31, section: Storage; Prohibited uses
  - Prohibits storing information accessed through Pinterest Materials including the API, directing developers to call the API on each access instead, with an exception only for campaign analytics about an account the developer holds or has been granted access to. Lists among prohibited uses: automated scraping or data extraction except as expressly permitted; using Pinterest Materials to train, fine-tune or otherwise develop AI or machine-learning models except as expressly permitted; and attempting or claiming to provide platform insights, benchmarking or competitor research features without explicit written authorization. States that API information may not be used except to serve and evaluate the performance of ads on Pinterest, and that information from the API may not be shared or sold to a third party.
- [Pinterest Developer and API Terms of Service (landing page)](https://developers.pinterest.com/terms/) — `OFFICIAL_TERMS`, retrieved 2026-08-31, section: Retrieval failure
  - Reached on 2026-08-31 and returned navigation and footer links only, with no policy text -- the same failure Mission 1.7 recorded. The substantive guidelines were obtained instead from policy.pinterest.com, a first-party Pinterest policy host reached directly. No mirror, cache or third-party copy was used.

**Blocked by**

- policy review for use profile 'commercial-multi-tenant-research-v1' is RESTRICTED

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
| external model transmission | not assessed |
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

- policy review for use profile 'commercial-multi-tenant-research-v1' is RESTRICTED

---

### Python Package Index (PyPI) — `pypi`

The Python package index. Its terms address API abuse specifically and prohibit narrow, named misuses rather than automated access as such.

- **Family:** developer
- **Coverage:** PARTIAL, languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-30 | `mission-1.7` | `APPROVED_WITH_CONDITIONS` | 1 |
| 2 ← current | 2026-08-30 | `mission-1.8` | `REQUIRES_REVIEW` | 1 |

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
| external model transmission | not assessed |
| personal data handling | conditional |
| attribution required | not addressed |

**Reviewer notes**

DOWNGRADED from APPROVED_WITH_CONDITIONS, on audit rather than on new evidence. The Mission 1.7 review recorded four of the six activities the assessed use materially requires -- commercial_use, storage, derived_analytics and model_processing -- as NOT_ADDRESSED, and approved the source anyway. Its own notes described the basis as 'the absence of a prohibition covering us plus the presence of a documented API', which is the move source-registry-v1.md §1 rule 2 and Mission 1.7 §12 forbid by name. The single cited document contains prohibitions and no grant of any kind: PyPI is the only source in the catalog that reached an approving state with NOT ONE required activity positively permitted. Nothing about PyPI's terms changed; the reading of them did. Version 1 is preserved as the record of what was concluded and on what basis, because the useful history is that the reasoning was written down correctly and acted on incorrectly.

**Open questions**

- Determine whether any PyPI or PSF document positively permits commercial reuse of package metadata by a third-party product. The Terms of Service read on 2026-08-30 prohibit specific misuses and grant nothing.
- Determine whether storage of replicated package metadata is addressed anywhere in PyPI's own documents.
- Determine whether derived analytics over package metadata, and model processing of it, are addressed. Both are unaddressed in the Terms of Service and both are required by the assessed use.
- Determine whether the published bulk dataset carries different and possibly more explicit terms than the API.
- Retained from review version 1 as obligations that would apply IF a grant is found: pace requests so they cannot be characterised as excessively frequent, and never extract maintainer contact details for any purpose resembling recruitment, which the terms name specifically.

**Official evidence (1)**

- [PyPI Terms of Service](https://policies.python.org/pypi.org/Terms-of-Use/) — `OFFICIAL_TERMS`, retrieved 2026-08-30, section: API; Acceptable Use
  - Effective 25 February 2025, superseding the earlier Terms of Use. The terms state that abuse or excessively frequent requests to PyPI via the API may result in temporary or permanent suspension of an account's API access, that API tokens may not be shared in order to exceed PyPI's rate limitations, and that the API may not be used to download data or content for spamming purposes, including selling PyPI users' personal information to recruiters, headhunters and job boards. All API activity is stated to remain subject to the Terms of Service and the Privacy Policy. Automated access is therefore not prohibited as such; what is prohibited is named narrowly, and the personal-information clause bears directly on maintainer contact details.

**Blocked by**

- policy review for use profile 'commercial-multi-tenant-research-v1' is REQUIRES_REVIEW

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
| external model transmission | not assessed |
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

- policy review for use profile 'commercial-multi-tenant-research-v1' is REQUIRES_REVIEW

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
| external model transmission | not assessed |
| personal data handling | not assessed |
| attribution required | not assessed |

**Reviewer notes**

Assessed and closed. Four of the activities this system requires -- storage, aggregation into a database, derived analytics transferred onward, and model processing -- are each prohibited by name, and the prohibition on aggregate and derivative data closes the usual fallback of keeping only statistics. No condition could be written that would make this use permissible, so no condition is written; PROHIBITED is the verdict rather than RESTRICTED because nothing in the assessed use case survives.

**Official evidence (1)**

- [Spotify Developer Terms of Service](https://developer.spotify.com/terms) — `OFFICIAL_TERMS`, retrieved 2026-08-30, section: Restrictions; Streaming and Commercial Use
  - Effective 15 May 2025. The terms state that the developer may not store, aggregate or create compilations or databases of Spotify Content other than as strictly necessary to operate the developer's own application, and separately direct the developer not to use the Spotify Platform or any Spotify Content to train a machine learning or AI model or otherwise ingest Spotify Content into such a model. They further prohibit using any robot, spider, site search or retrieval application or other tool to retrieve, duplicate or index any portion of the Spotify Service or Spotify Content, playlist data included, and prohibit transferring Spotify Content to third parties including as aggregate, anonymous or derivative data. The licence granted is limited to operating an application for private personal use on approved devices.

**Blocked by**

- policy review for use profile 'commercial-multi-tenant-research-v1' is PROHIBITED

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
| 1 | 2026-09-01 | `mission-1.18` | `APPROVED_WITH_CONDITIONS` | 3 |
| 2 | 2026-09-02 | `mission-1.23` | `APPROVED_WITH_CONDITIONS` | 4 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | stack-exchange-api | api key, dev app | `STACK_EXCHANGE_API_KEY` | **UNKNOWN** | `UNKNOWN` |
| `DATASET_DOWNLOAD` | stack-exchange-data-dump | nothing | — | **UNKNOWN** | `FREE` |

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
| external model transmission | not assessed |
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

- policy review for use profile 'commercial-multi-tenant-research-v1' is REQUIRES_REVIEW

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
| external model transmission | not assessed |
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

- policy review for use profile 'commercial-multi-tenant-research-v1' is RESTRICTED

---

### Tenders Electronic Daily (EU public procurement) — `ted-eu`

The EU's official public procurement journal. Contract award notices record what a public body actually bought, from which supplier, at what value -- a TRANSACTION rather than a listed price, which is the evidence class the portfolio has never had. REQUIRES_REVIEW: five of six load-bearing activities are granted explicitly and machine-learning processing is not addressed.

- **Family:** public_procurement
- **Coverage:** PARTIAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-31 · next 2027-08-31

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-31 | `mission-1.15` | `REQUIRES_REVIEW` | 2 |
| 2 | 2026-08-31 | `mission-1.15.1` | `REQUIRES_REVIEW` | 4 |
| 3 | 2026-08-31 | `mission-1.15.2` | `REQUIRES_REVIEW` | 3 |
| 4 | 2026-08-31 | `mission-1.15.3` | `REQUIRES_REVIEW` | 7 |
| 5 ← current | 2026-08-31 | `mission-1.15.4` | `REQUIRES_REVIEW` | 4 |
| 1 | 2026-08-31 | `mission-1.15.5` | `APPROVED_WITH_CONDITIONS` | 4 |
| 2 | 2026-08-31 | `mission-1.15.6` | `APPROVED_WITH_CONDITIONS` | 4 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `DATASET_DOWNLOAD` | ted-bulk-xml | nothing | — | **UNKNOWN** | `FREE` |
| `OFFICIAL_API` | ted-search-api | nothing | — | **UNKNOWN** | `FREE` |
| `OFFICIAL_API` | ted-open-data-sparql | nothing | — | **UNKNOWN** | `FREE` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | permitted |
| api use | permitted |
| browser automation | not assessed |
| commercial use | permitted |
| storage | permitted |
| retention | permitted |
| redistribution | permitted |
| derived analytics | permitted |
| model processing | permitted |
| external model transmission | not assessed |
| personal data handling | conditional |
| attribution required | conditional |

**Conditions**

- Attribution is required for reused editorial material under CC BY 4.0, and changes must be indicated. The Publications Office logo may not be used without prior consent.
- Notices publish contact details of contracting authorities and successful tenderers -- names, addresses, email addresses, telephone and fax numbers. A minimisation profile must discard the entire contact block: the engine needs the award value, the buyer and supplier organisation names, the CPV classification and the dates, and needs no natural person's contact details for any assessed purpose.
- Only electronically signed notices published in the Supplement to the Official Journal are authentic; online documents are not necessarily exact reproductions. Any claim derived from TED must be attributed to TED's published notice rather than asserted as the authentic award.
- The legal notice states that additional rights may need clearing where content depicts identifiable private individuals or includes third-party works, and that content not owned by the EU may require permission from the rightholder. The reuse grant is therefore not a blanket grant over everything inside a notice, and a minimisation profile is a compliance requirement rather than a preference.
- Industrial property -- patents, trademarks, registered designs, logos and names, including the TED and SIMAP logos -- is excluded from the Commission's reuse policy and is not licensed. Supplier and buyer NAMES appear in award notices as facts about a procurement; using them as trademarks is a different act and is outside the grant.
- Article 6(2)(b): the reuser is obliged NOT TO DISTORT the original meaning or message of the documents. This is the condition with the most direct bearing on the claim layer: an OBSERVED restatement of a TED award notice must say what the notice says, and a derived signal must not be presented in a way that changes what the procurement record means. It is a legal obligation as well as an epistemic one.
- Article 2(4): nothing in the Decision authorises reuse of documents in a manner calculated to deceive or to defraud. The only prohibition in the Decision that concerns the MANNER of use rather than the class of document.
- Article 6(2)(c): the Commission accepts no liability for any consequence stemming from the reuse. Read with TED's authenticity condition, any claim derived from a notice is a claim about what TED published and never a warranted statement about the underlying contract.
- The machine-processing permission established by this review is SCOPED to inference, extraction, classification and structured analysis over reused notices -- the engine's assessed need. MODEL TRAINING was not assessed and is not authorised here: the Decision does not distinguish methods, but training raises the Article 2(2)(b) third-party-rights question in a materially different form and the engine does not need it. Embeddings are likewise unassessed for implementation and blocked independently by D-12.
- The licence that governs a TED resource must be resolved from THAT resource's own first-party record, and never carried across from another. The data.europa.eu catalogue declares dct:license = COM_REUSE (the European Commission reuse notice, which resolves by skos:exactMatch to Commission Decision 2011/833/EU) on EVERY distribution of the ted-1 dataset, including the bulk XML download; the search API's own OpenAPI 'Terms of Usage' section resolves to the same TED legal notice. Twelve distributions of the SEPARATE ted-csv dataset, published by DG GROW rather than by the Publications Office, declare CC BY 4.0 instead -- a licence whose Section 4 expressly grants extraction and re-utilisation of a substantial portion of a database's contents. Those twelve files licence themselves and nothing else. They do not licence the XML corpus, the bulk packages or the search API, and the same catalogue applies the two licences to OVERLAPPING coverage -- ted-contract-award-notices-2017-2021.zip is CC BY 4.0 while ted-contract-award-notices-2018-2023.zip is COM_REUSE -- so the favourable one may not be selected by choosing a filename.
- The documented PURPOSE of an official route is not a grant of a database right. The Publications Office states that the Search API 'allows access to published procurement notices for analysis and reuse', that it is 'primarily targeted at data reusers', and names commercial organisations integrating TED data into platforms among its users; the TED Open Data Service says the data is published 'for analysis and re-use' and offers a 'Connect your app' button to keep an application updated with live results. That is first-party evidence of INTENDED USE and it is recorded as such. It is not a statement about the sui generis database right, which H-36A and H-36B still leave open, and no route may be authorised on it alone. Any future authorisation must rest on the route's intended-use evidence AND on a resolution of the database-right question appropriate to the volume being taken.

**Reviewer notes**

A fresh first-party review of TED's two OFFICIAL query routes, prompted by a change in the project's real use case rather than by new rights evidence. NO ASSESSMENT AND NO VERDICT CHANGES.

WHY THIS VERSION EXISTS. Reviews v1 to v4 assessed a demanding use case: commercial multi-tenant SaaS, repeated collection at corpus scale, potentially substantial dataset reuse. The system's actual current use is narrower -- one developer, local, private, not publicly exposed, no redistribution, no resale, no training, aggressively minimised storage. That does not change the source's terms, and this review does not pretend it does. What it changes is which question is worth asking: not 'may we mirror the corpus commercially' but 'do the official query routes document a purpose that covers narrow local research'.

WHAT THE OPERATOR SAYS ITS ROUTES ARE FOR. The Search API 'allows access to published procurement notices for analysis and reuse', is 'primarily targeted at data reusers', requires no authentication, and names 'Commercial Organisations: Integrating TED data into platforms to provide added-value services' and 'Researchers: Analysing public procurement trends and patterns' among its users. The TED Open Data Service publishes the data 'for analysis and re-use', invites use 'in your research and applications', and offers a 'Connect your app' button whose stated purpose is to 'run your query and retrieve live results directly into Excel, Power BI, or any application that can get data from the web'. Analysis, reuse, application integration, commercial use, repeated access and automated access are each named by the operator about its own route.

WHAT THAT IS, AND IS NOT. It is exactly the evidence Mission 1.15.4 section 5 and section 6 ask for, and it is the reason the Search API is not being treated as a loophole: the authorisation argument rests on what TED says the route is for, not on the route transferring smaller chunks. It is NOT a statement about the sui generis database right. Nothing on either route mentions it, and an operator describing what its service is for is not the same act as a right holder licensing a right in a collection. H-36A and H-36B are unchanged, and a condition records the distinction so a later reader cannot collapse the two.

WHAT ALSO CAME OUT OF IT. The Search API supports FIELD SELECTION, so minimisation at acquisition is technically possible rather than aspirational. The Open Data Service's coverage is recent and partial -- eForms from March 2023, Standard Forms a proof-of-concept slice of six form types -- which bounds what transaction research it could support. And the operator warns about two response-contract traps of its own accord: lots duplicate rows, and multilingual notices duplicate rows.

VERDICT UNCHANGED. REQUIRES_REVIEW. Every assessment is byte-identical to v4, H-34 stays CLOSED PERMITTED, all ten v4 conditions are carried forward verbatim and an eleventh records that a route's documented purpose is not a database-right grant. The bulk packages route gains nothing from this review and stays exactly where Mission 1.15.3 left it.

**Open questions**

- H-36A: whether a sui generis database right SUBSISTS in the TED notice corpus is NOT ESTABLISHED, in either direction. Directive 96/9/EC Article 7(1) gives the right to the MAKER of a database who shows qualitatively and/or quantitatively a substantial investment in obtaining, verification or presentation of the contents. No first-party document retrieved identifies a maker or asserts such an investment. The data.europa.eu DCAT record for ted-1 names dct:publisher = Publications Office of the European Union and carries NO dct:creator at all; notices are filed by contracting authorities across the Union, so who assembled the collection in the Article 7(1) sense is a question the catalogue does not answer. Article 11 then makes subsistence depend on the maker's nationality or establishment. This is a legal question about facts nobody has published, not a retrieval gap.
- H-36B: whether the applicable right holder GRANTS or WAIVES the extraction and re-utilisation the engine needs is NOT ADDRESSED for either route under consideration. Directive 96/9/EC Article 7(3) provides that the right may be transferred, assigned or granted under contractual licence -- so a licence CAN carry it, and the licence that governs both routes does not. Every ted-1 distribution including the bulk XML download declares COM_REUSE, whose authority record asserts skos:exactMatch to Commission Decision 2011/833/EU, which Mission 1.15.2 read in full and which contains no database-right provision. The search API's OpenAPI 'Terms of Usage' section contains exactly one item, a link to the same TED legal notice. Sharpening the question: the SAME publisher's catalogue declares CC BY 4.0 -- whose Section 4 expressly licenses extraction and re-utilisation of a substantial portion -- on twelve distributions of the ted-csv dataset, including contract award notices for 2020, 2021 and 2022, while applying COM_REUSE to thirty-six others that OVERLAP them in coverage. Whether that difference is a deliberate rights decision or catalogue-record drift is exactly what a first-party clarification would settle.
- Rate limits, refined again and still not closed. The Search API's own documentation publishes VOLUME limits per query -- pagination mode 15,000 retrievable notices, 250 per page, 10,000 fields per page; iteration/scroll mode 250 per page, 10,000 fields per page and no limit on the number of retrievable notice documents. Nothing published states a REQUEST-RATE or concurrency limit for the Search API, for the TED SPARQL endpoint, or for the bulk packages. No fair-use statement was found for the SPARQL endpoint at all. A collector must therefore throttle conservatively on its own rather than be handed a number nobody published.
- Open Data Service coverage is recent and partial, which bounds what transaction research it can support rather than what it may do. The Publications Office documents eForms notices from 1 March 2023 to current day minus one (eProcurement Ontology v4), and Standard Forms only from 28 August 2023 to 26 January 2024 -- 'A limited number of XML notices are available in Cellar. These were produced during the initial TED Open Data Service Pipeline proof of concept', form types F3, F6, F21, F22, F23 and F25, with support for the remaining form types and SDK 1.14 'coming in 2026'. Whether the Search API's own coverage is deeper than the RDF service's was not established.

**Official evidence (4)**

- [TED Developer Docs -- Search API (intended purpose and audiences)](https://docs.ted.europa.eu/api/latest/search.html) — `OFFICIAL_API_DOCS`, retrieved 2026-08-31, section: Search API; Available Operations; Who Uses This API
  - THE OPERATOR STATES WHAT THE ROUTE IS FOR, which is the evidence Mission 1.15.4 section 5 requires and which 'an API exists' is not. Verbatim: 'The Search API allows access to published procurement notices for analysis and reuse, promoting transparency.' And: 'The Search API provides access to published notices via expert queries and enables bulk downloads of notices in XML format for reuse or analysis. Note that this API is primarily targeted at data reusers and does not require authentication, making it openly accessible to any system or user.' A 'Who Uses This API' section names four audiences, and the first two are decisive for this project: 'Commercial Organisations: Integrating TED data into platforms to provide added-value services for vendors and buyers' and 'Researchers: Analysing public procurement trends and patterns'; also 'Developers: Creating transparency tools or reusing public data'. So ANALYSIS, REUSE, APPLICATION INTEGRATION, COMMERCIAL USE and AUTOMATED ACCESS are each named by the operator about its own route. NONE of it mentions the sui generis database right, extraction of substantial parts or re-utilisation in the Directive 96/9/EC sense, so it is evidence of intended use and not a rights grant over the collection.
- [TED Open Data Service (data.ted.europa.eu) -- home and help text](https://data.ted.europa.eu/) — `OFFICIAL_API_DOCS`, retrieved 2026-08-31, section: Home; Help; footer
  - AN OFFICIAL EU SERVICE WHOSE STATED PURPOSE IS REUSE. The site heads itself 'TED Open Data Service -- Explore and reuse EU public procurement data' and says: 'We organise this information as a knowledge graph and publish it for analysis and re-use. We invite you to explore, understand and use this information in your research and applications.' The Help text says it 'lets you explore the entire collection of public procurement data published by the Publications Office of the EU' and that users may 'write SPARQL queries to extract custom datasets across many notices'. On repeated and automated access it is explicit: 'For SELECT queries, the Connect your app button gives you the link, and the commands, to run the same query from your own tools. You can use this URL to run your query and retrieve live results directly into Excel, Power BI, or any application that can get data from the web', and the August 2026 changelog offers the same request 'as a cURL, wget or PowerShell command'. Results download as JSON, CSV, TSV, Spreadsheet, XML, Turtle, RDF/XML and N-Triples. The footer's Legal Notice links to https://ted.europa.eu/en/legal-notice -- the SAME document that governs the bulk route, so this service adds no new licence and inherits the Decision. NOTE, recorded rather than relied on: the operator's own word for what a query does is 'extract', and it invites extraction of custom datasets across many notices. That is a statement about intended use of the service, not a statement about rights in the collection, and it does not close H-36.
- [TED Open Data documentation -- connecting, SPARQL endpoint and current data availability](https://docs.ted.europa.eu/ODS/latest/index.html) — `OFFICIAL_API_DOCS`, retrieved 2026-08-31, section: index; connecting/index; connecting/sparql; data_availability; querying/tips
  - THE ROUTE, AND ITS LIMITS. 'The Publications Office collects a wealth of public procurement data through the notices published in the Supplement of the Official Journal of the EU (OJS). This data is made available to the public as Linked Open Data (LOD) as well as other formats.' The documented endpoint is 'The TED SPARQL EndPoint: https://data.ted.europa.eu/'; the connecting page explains that 'Cellar uses the Virtuoso EndPoint application', and the service front-end issues its queries against https://publications.europa.eu/webapi/rdf/sparql. Documented ways to connect are the endpoint directly, Microsoft Excel with 'a permanent link to your query and update the data from within Excel whenever you wish', and Jupyter/Python. COVERAGE IS RECENT AND PARTIAL: eForms from 1 March 2023 to current day minus one (ePO v4); Standard Forms only 28 August 2023 to 26 January 2024, where 'A limited number of XML notices are available in Cellar. These were produced during the initial TED Open Data Service Pipeline proof of concept', form types F3, F6, F21, F22, F23, F25, with the rest 'coming in 2026'. TWO RESPONSE-CONTRACT WARNINGS the operator gives itself: results repeat per LOT ('it can look like data with the same notice number is duplicated'), and notices published in several languages appear several times unless the query filters language. The editor's currency-conversion snippet carries an explicit caveat -- rates are approximate, applied at the latest available rate rather than the rate at publication, so 'do not rely on the result for precise or legally meaningful figures'.
- [TED Open Data documentation -- downloading notices using the Search API](https://docs.ted.europa.eu/ODS/latest/reuse/search-api.html) — `OFFICIAL_API_DOCS`, retrieved 2026-08-31, section: Search modes; Limits; Request body of the notice search endpoint
  - FIELD SELECTION IS SUPPORTED, WHICH MAKES MINIMISATION AT ACQUISITION POSSIBLE. The documented request body carries 'fields: Fields to return for each notice' alongside query, page, limit, scope, paginationMode and iterationNextToken. Mission 1.15.4 section 14 requires that a collector not collect first and minimise later where the official query supports field selection, and this route does. Two modes are documented: pagination 'Allows the retrieval of up to 15000 notice documents for a given query' with 250 notices and 10,000 fields per page; and iteration/scroll, which 'Allows the retrieval of all notice documents for a given query, without limitations' -- 250 per page, 10,000 fields per page, and 'There is no limit on the number of retrievable notice documents.' No request-rate or concurrency limit is stated anywhere. The response carries the total match count and, per result, the requested fields plus URLs for the formats and languages the notice is available in.

**Blocked by**

- policy review for use profile 'commercial-multi-tenant-research-v1' is REQUIRES_REVIEW

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
| external model transmission | not assessed |
| personal data handling | **not permitted** |
| attribution required | not assessed |

**Reviewer notes**

Status unchanged at PROHIBITED and now directly evidenced rather than inferred. This is the case Mission 1.3 §22 describes exactly: an official research API exists, and it is restricted to qualified non-commercial researchers at eligible institutions in eligible regions. Startup Research OS is a commercial multi-tenant SaaS and fails the eligibility criteria on their own terms. An official API existing is not an official API being available to us.

**Official evidence (1)**

- [TikTok Research Tools — eligibility and application](https://developers.tiktok.com/products/research-api/) — `OFFICIAL_API_DOCS`, retrieved 2026-08-29, section: Who can apply?
  - The Research Tools are the documented mechanism for accessing public TikTok data, and their eligibility criteria exclude this use case on two independent grounds. Applicants must be affiliated with an academic institution in the US, EEA, UK or Switzerland, a not-for-profit or independent research institution in the EU, or an academic/not-for-profit body in Brazil studying online youth safety. Applicants must also 'be independent from commercial interests and be able to conduct research on a not-for-profit or non-commercial basis pursuant to a public-interest mission'. Approval additionally requires a defined research proposal, disclosed funding and evidence of ethical review.

**Blocked by**

- policy review for use profile 'commercial-multi-tenant-research-v1' is PROHIBITED

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
| external model transmission | not assessed |
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

- policy review for use profile 'commercial-multi-tenant-research-v1' is REQUIRES_REVIEW

---

### USAspending.gov (US federal award data) — `usaspending`

US federal contract and grant awards: who received public money, from which agency, for how much. The same TRANSACTION evidence class as TED. REQUIRES_REVIEW: no licence or terms document could be retrieved.

- **Family:** public_procurement
- **Coverage:** PARTIAL, countries ['US'], languages ['en']
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-31 · next 2027-08-31

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | usaspending-api | nothing | — | **UNKNOWN** | `UNKNOWN` |

**Assessment**

| Activity | Verdict |
|---|---|
| automated access | not addressed |
| api use | not addressed |
| browser automation | not assessed |
| commercial use | not addressed |
| storage | not addressed |
| retention | not addressed |
| redistribution | not addressed |
| derived analytics | not addressed |
| model processing | not addressed |
| external model transmission | not assessed |
| personal data handling | not addressed |
| attribution required | not addressed |

**Reviewer notes**

Registered because it is the second lawful-looking route to WILLINGNESS_TO_PAY as a transaction, and REQUIRES_REVIEW because looking lawful is not being permitted. Three first-party locations were tried and none carried a licence: the API root, the about page (which returned no content) and the operating agency's own repository README. The DATA Act sentence establishes that the data must be publicly ACCESSIBLE, which is a statement about publication and not a grant of reuse rights to a commercial product. This is a weaker position than TED, where a reuse grant was retrieved verbatim, and the difference is exactly the one the registry exists to keep visible.

**Open questions**

- Retrieve a licence or terms-of-use document for USAspending data. The API root at api.usaspending.gov states that the data is open source and provided to the public as part of the DATA Act but carries no licence text; usaspending.gov/about returned no content on 2026-08-31; and the operating agency's GitHub README states the same DATA Act sentence with no licence, terms, attribution requirement or rate limit.
- Determine whether US federal works' copyright status is asserted anywhere first-party for this dataset. A general legal principle is not a source document, and no verdict may rest on one.
- Determine documented rate limits for the public API.

**Official evidence (2)**

- [USAspending API root](https://api.usaspending.gov/) — `OFFICIAL_API_DOCS`, retrieved 2026-08-31, section: Overview
  - Describes comprehensive US government spending data covering awards -- who received federal contracts or grants, with geographic and agency breakdowns -- and account-level data. States that the data is open source and provided to the public as part of the DATA Act which requires it to be publicly accessible. Carries no licence, terms of use, registration requirement, rate limit, or statement about commercial use, storage, redistribution, analytics or machine learning.
- [usaspending-api repository README](https://github.com/fedspendingtransparency/usaspending-api/blob/master/README.md) — `OFFICIAL_API_DOCS`, retrieved 2026-08-31, section: Retrieval outcome
  - The operating agency's own repository documentation repeats that the data is open source and provided to the public as part of the DATA Act, and states no software licence, copyright notice, terms of use, rate limit or attribution requirement. https://www.usaspending.gov/about returned no page content on 2026-08-31 and is recorded as a retrieval failure.

**Blocked by**

- policy review for use profile 'commercial-multi-tenant-research-v1' is REQUIRES_REVIEW

---

### Wikimedia Analytics (Pageviews) — `wikimedia-pageviews`

Per-article view counts across Wikimedia projects. Measures attention directly and requires no complaint, which makes it the clearest instrument in the catalog for curiosity and emerging-interest signals.

- **Family:** knowledge
- **Coverage:** GLOBAL
- **Retention if collected:** raw 30d (baseline), normalized 365d (baseline)
- **State:** `REQUIRES_REVIEW` — **collector eligible from the catalog alone: no**
- **Last reviewed:** 2026-08-30 · next 2027-02-26

**Review history**

| Version | Reviewed | By | State | Evidence |
|---|---|---|---|---|
| 1 | 2026-08-30 | `mission-1.7` | `APPROVED_WITH_CONDITIONS` | 3 |
| 2 ← current | 2026-08-30 | `mission-1.8` | `REQUIRES_REVIEW` | 4 |
| 1 | 2026-09-02 | `mission-1.19` | `APPROVED_WITH_CONDITIONS` | 5 |
| 2 | 2026-09-02 | `mission-1.29` | `APPROVED_WITH_CONDITIONS` | 5 |

**Access profiles** (how, not whether)

| Method | Label | Requires | Secret references | Rate limit | Cost |
|---|---|---|---|---|---|
| `OFFICIAL_API` | wikimedia-analytics-api | nothing | — | 200/60s (documented) | `FREE_WITH_LIMITS` |
| `DATASET_DOWNLOAD` | wikimedia-dumps | nothing | — | **UNKNOWN** | `FREE` |

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
| external model transmission | not assessed |
| personal data handling | not addressed |
| attribution required | conditional |

**Reviewer notes**

DOWNGRADED, and the reason is a misreading corrected rather than a policy that changed. Version 1 cited the Analytics API documentation as labelling its content CC BY-SA 4.0; that page carries 'Content: CC BY-SA 4.0 · Code: MIT-0', which is the standard footer describing THE DOCUMENTATION SITE and not a statement about the data the API returns. With that removed, storage and model_processing have no grant behind them and both are required by the assessed use. CC BY-SA 4.0 was retrieved during this mission to test whether the licence supplies them. Section 2 does grant reproduction and the production of Adapted Material, commercially and with no text-and-data-mining restriction -- FOR LICENSED MATERIAL. Whether aggregate pageview COUNTS are Licensed Material is exactly the open question version 1 recorded as H-24, and either answer to it is a determination about what copyright subsists in, which source-registry-v1.md §0 states this system does not make. Resolving H-24 in our own favour to reach eligibility is the one thing Mission 1.8 §18 forbids, so the source fails closed and the licence is recorded so the next reviewer has both halves of the question in front of them. What is NOT in doubt is commercial reuse, which the Foundation's terms permit in their own words, and the documented rate limits, which stand.

**Open questions**

- H-24, now the blocking question rather than a refinement: determine whether aggregate pageview counts are Licensed Material under CC BY-SA 4.0. If they are, Section 2 grants storage and the production of Adapted Material and this source is approvable. If they are not, a separate basis is needed for holding and processing them.
- Determine whether the Wikimedia Foundation addresses storage or retention of pageview data by a reuser anywhere in its own documents. Neither the Terms of Use nor the API access policy does.
- Determine whether model processing of Wikimedia data is addressed by any Foundation document.
- Determine whether Wikimedia Enterprise is REQUIRED rather than merely offered for a commercial reuser at this volume; the APIs overview presents it as the route for high-volume commercial reuse without stating a threshold.
- Retained from version 1 as obligations that would apply IF a grant is found: send a descriptive User-Agent in the format the User-Agent Policy prescribes, stay within the documented 200 requests per minute and honour HTTP 429, and carry CC BY-SA attribution wherever article content is surfaced.

**Official evidence (4)**

- [Wikimedia Foundation Terms of Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use) — `OFFICIAL_TERMS`, retrieved 2026-08-30, section: Reuse; Licensing of Content; Refraining from Certain Activities
  - Effective 7 June 2023. The Foundation states that the licences applied to project content do allow commercial uses of contributions provided the use complies with the terms of the respective licence, and that text is licensed CC BY-SA 4.0 and GFDL. Attribution may be satisfied by a hyperlink or URL to the article contributed to. The terms prohibit automated uses that are abusive or disruptive, that violate applicable acceptable-usage policies, or that have not been approved by the community, and state that by using the APIs the user agrees to abide by the User-Agent Policy, the Robot Policy and API:Etiquette. Commercial reuse is therefore permitted; the constraint is on HOW automated access is conducted, not on whether the result may be sold.
- [Wikimedia APIs - Rate limits](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits) — `OFFICIAL_API_DOCS`, retrieved 2026-08-30, section: Rates by client type
  - Limits are enforced per minute across the Action API and the REST APIs: 10 requests per minute for a client identified only by IP address, 200 for an unauthenticated client sending a User-Agent, 200 for a new authenticated account, 2000 for an established editor, and exemption for bot-flagged and approved clients. Exceeding a limit returns HTTP 429 with a Retry-After header; where no such header is present the documentation directs clients to wait at least five seconds or apply exponential back-off. The page states these limits are new in 2026 and subject to change.
- [Wikimedia Foundation User-Agent Policy](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy) — `OFFICIAL_ACCESS_CONTROL`, retrieved 2026-08-30, section: Format
  - Automated clients must send an informative User-Agent identifying the client, its version and contact information, in the form 'CoolBot/0.0 (https://example.org/coolbot/; coolbot@example.org) generic-library/0.0'. The policy states that scripts should use an informative User-Agent string with contact information or they may be blocked without notice, and directs clients not to copy a browser user agent and not to use a generic one such as curl or python-requests.
- [Creative Commons Attribution-ShareAlike 4.0 International — Legal Code](https://creativecommons.org/licenses/by-sa/4.0/legalcode) — `OFFICIAL_LICENCE`, retrieved 2026-08-30, section: Section 1 (Adapted Material); Section 2 (Scope — Licence grant)
  - Section 2 grants the licensee the right to 'reproduce and Share the Licensed Material, in whole or in part' and to 'produce, reproduce, and Share Adapted Material', with no exclusion of commercial purposes and no restriction on text and data mining or automated processing. Adapted Material is defined in Section 1 as material derived from or based upon the Licensed Material in a manner requiring permission under the Copyright and Similar Rights held by the Licensor. Retrieved to test whether the licence supplies the storage and model-processing grants the Wikimedia terms do not state. It supplies them FOR LICENSED MATERIAL, and whether aggregate pageview counts are Licensed Material is the unresolved question.

**Blocked by**

- policy review for use profile 'commercial-multi-tenant-research-v1' is REQUIRES_REVIEW

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
| 1 | 2026-09-01 | `mission-1.17` | `APPROVED_WITH_CONDITIONS` | 1 |
| 2 | 2026-09-02 | `mission-1.29` | `APPROVED_WITH_CONDITIONS` | 2 |

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
| external model transmission | not assessed |
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
| external model transmission | not assessed |
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

- policy review for use profile 'commercial-multi-tenant-research-v1' is REQUIRES_REVIEW
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
| external model transmission | not assessed |
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

- policy review for use profile 'commercial-multi-tenant-research-v1' is PROHIBITED

---
