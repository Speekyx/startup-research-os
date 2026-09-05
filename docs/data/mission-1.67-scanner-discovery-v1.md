# Mission 1.67 — Scanner discovery, prescreen and document ledger

Generated from `scanner-discovery-universe-v1.json`,
`scanner-candidate-prescreen-v1.json` and
`mission-1.67-documentation-ledger-v1.json`. Do not edit by hand.

## Search bounds

- Apparatus class: **INTERNET_WIDE_ACTIVE_MEASUREMENT**
- Discovery hits: **22**
- Serious candidates: **2** of a budget of 6
- First-party document requests: **24** of 36
- Search-navigation requests: **12**

**Exhaustive:** no. This mission ran a bounded search under a fixed document budget. That no qualifying apparatus was found does not establish that none exists.

## Discovery universe

| apparatus | classification | basis |
|---|---|---|
| Rapid7 Project Sonar | `NEW_SERIOUS_CANDIDATE` | `FIRST_PARTY_DOCUMENTS_RETRIEVED` |
| Shodan | `NEW_SERIOUS_CANDIDATE` | `FIRST_PARTY_DOCUMENTS_RETRIEVED` |
| BinaryEdge | `DOCUMENTATION_NOT_RETRIEVABLE_FOR_QUALIFICATION` | `FOUR_LIVE_RETRIEVALS_ALL_NON_TECHNICAL_OR_FAILED` |
| ZoomEye | `DOCUMENTATION_NOT_RETRIEVABLE_FOR_QUALIFICATION` | `THREE_LIVE_RETRIEVALS_ALL_UNUSABLE` |
| Criminal IP | `DOCUMENTATION_NOT_RETRIEVABLE_FOR_QUALIFICATION` | `TWO_LIVE_RETRIEVALS_BOTH_403` |
| FOFA | `DOCUMENTATION_NOT_RETRIEVABLE_FOR_QUALIFICATION` | `TWO_LIVE_RETRIEVALS_BOTH_EMPTY_SHELLS` |
| Netlas | `DUPLICATE_EXISTING_APPARATUS` | `REPOSITORY_ARTIFACTS_MISSIONS_1_60_TO_1_65` |
| ONYPHE | `DUPLICATE_EXISTING_APPARATUS` | `REPOSITORY_ARTIFACTS_MISSIONS_1_62_TO_1_66_2` |
| LeakIX | `DUPLICATE_EXISTING_APPARATUS` | `REPOSITORY_ARTIFACTS_MISSION_1_62` |
| Shadowserver | `DUPLICATE_EXISTING_APPARATUS` | `REPOSITORY_ARTIFACTS_MISSION_1_62` |
| Censys | `DUPLICATE_EXISTING_APPARATUS` | `REPOSITORY_ARTIFACTS_MISSIONS_1_58_AND_1_59` |
| scans.io / Internet-Wide Scan Data Repository | `DISCOVERED_NOT_EVALUATED` | `PROJECT_HYPOTHESIS_NOT_ESTABLISHED` |
| GreyNoise | `DISCOVERED_NOT_EVALUATED` | `PROJECT_HYPOTHESIS_NOT_ESTABLISHED` |
| RIPE Atlas | `DISCOVERED_NOT_EVALUATED` | `PROJECT_HYPOTHESIS_NOT_ESTABLISHED` |
| CAIDA Ark | `DISCOVERED_NOT_EVALUATED` | `PROJECT_HYPOTHESIS_NOT_ESTABLISHED` |
| Measurement Lab | `DISCOVERED_NOT_EVALUATED` | `PROJECT_HYPOTHESIS_NOT_ESTABLISHED` |
| SANS Internet Storm Center / DShield | `DISCOVERED_NOT_EVALUATED` | `PROJECT_HYPOTHESIS_NOT_ESTABLISHED` |
| Alpha Strike Labs | `DISCOVERED_NOT_EVALUATED` | `PROJECT_HYPOTHESIS_NOT_ESTABLISHED` |
| Hunter.how | `DISCOVERED_NOT_EVALUATED` | `PROJECT_HYPOTHESIS_NOT_ESTABLISHED` |
| Odin | `DISCOVERED_NOT_EVALUATED` | `PROJECT_HYPOTHESIS_NOT_ESTABLISHED` |
| Netcraft | `DISCOVERED_NOT_EVALUATED` | `PROJECT_HYPOTHESIS_NOT_ESTABLISHED` |
| SecurityTrails | `DISCOVERED_NOT_EVALUATED` | `PROJECT_HYPOTHESIS_NOT_ESTABLISHED` |

## Prescreen

A hit becomes a serious candidate only once active measurement is plausible,
first-party method documentation is retrievable, and product relevance is
plausible. The documentation pre-gate runs first.

| candidate | docs retrievable | documents | verdict |
|---|---|---|---|
| Rapid7 Project Sonar | True | 6 | `SERIOUS` |
| Shodan | True | 5 | `SERIOUS` |
| BinaryEdge | False | 0 | `DOCUMENTATION_NOT_RETRIEVABLE_FOR_QUALIFICATION` |
| ZoomEye | False | 0 | `DOCUMENTATION_NOT_RETRIEVABLE_FOR_QUALIFICATION` |
| Criminal IP | False | 0 | `DOCUMENTATION_NOT_RETRIEVABLE_FOR_QUALIFICATION` |
| FOFA | False | 0 | `DOCUMENTATION_NOT_RETRIEVABLE_FOR_QUALIFICATION` |

### What a prescreen rejection does not establish

- **BinaryEdge** — Nothing about the apparatus. This is a fact about what this environment could retrieve, in the shape Mission 1.60 recorded for three candidates that later documented fully.
- **ZoomEye** — Nothing about the apparatus.
- **Criminal IP** — Nothing about the apparatus. A search summary reported field-level detail for this candidate and it was not used, in either direction.
- **FOFA** — Nothing about the apparatus.

## Retrieval-summary guard

A search summary is not a quotation. This mission met the Mission 1.63 shape
twice, and neither summary was used.

### BinaryEdge

*The summary reported:* Substantive technical content — scanning engine minions and modules, output mangling, and host data up to six months — attributed to docs.binaryedge.io paths.

*The live documents returned:* Three separate paths on that host each 301-redirected to one non-technical Coalition customer notice, which itself returned HTTP 403.

*Reading:* The index a search engine holds is not the document the host currently serves. Nothing from that summary was used to close any gate.

### Criminal IP

*The summary reported:* A confirmed_time field with an example timestamp, a banner search endpoint, and scan cadence figures.

*The live documents returned:* HTTP 403 on both attempted first-party documentation paths.

*Reading:* Recorded as documentation not retrievable from this environment. None of the summary's load-bearing wording was used, in either direction.

## Document ledger

12 carried load-bearing content, 4 returned nothing usable, and 8 failed. All of them are counted.

| n | candidate | url | outcome |
|---|---|---|---|
| 1 | Rapid7 Project Sonar | `https://sonardata.rapid7.com/about/` | `RETRIEVED_LOAD_BEARING` |
| 2 | Rapid7 Project Sonar | `https://www.rapid7.com/research/project-sonar/` | `RETRIEVED_LOAD_BEARING` |
| 3 | Shodan | `https://help.shodan.io/the-basics/what-is-shodan` | `RETRIEVED_LOAD_BEARING` |
| 4 | BinaryEdge | `https://docs.binaryedge.io/` | `FAILED` |
| 5 | Rapid7 Project Sonar | `https://sonardata.rapid7.com/changelog/` | `RETRIEVED_NO_LOAD_BEARING_CONTENT` |
| 6 | Shodan | `https://developer.shodan.io/api` | `RETRIEVED_LOAD_BEARING` |
| 7 | BinaryEdge | `https://help.coalitioninc.com/hc/en-us/articles/48928737389979-What-the-BinaryEdge-scanner-does-and-why-Coalition-may-scan-your-internet-facing-systems` | `FAILED` |
| 8 | ZoomEye | `https://www.zoomeye.ai/doc` | `RETRIEVED_NO_LOAD_BEARING_CONTENT` |
| 9 | Shodan | `https://help.shodan.io/mastery/data_timeline` | `RETRIEVED_LOAD_BEARING` |
| 10 | Shodan | `https://book.shodan.io/behind-the-scenes/crawler-algorithm/` | `RETRIEVED_LOAD_BEARING` |
| 11 | Rapid7 Project Sonar | `https://sonardata.rapid7.com/apihelp/` | `RETRIEVED_LOAD_BEARING` |
| 12 | Rapid7 Project Sonar | `https://github.com/rapid7/sonar/wiki/Analyzing-Datasets` | `RETRIEVED_LOAD_BEARING` |
| 13 | Shodan | `https://www.shodan.io/search/filters` | `RETRIEVED_LOAD_BEARING` |
| 14 | Rapid7 Project Sonar | `https://sonardata.rapid7.com/` | `RETRIEVED_LOAD_BEARING` |
| 15 | Rapid7 Project Sonar | `https://github.com/rapid7/sonar/wiki/TCP` | `RETRIEVED_LOAD_BEARING` |
| 16 | BinaryEdge | `https://docs.binaryedge.io/search/` | `FAILED` |
| 17 | BinaryEdge | `https://docs.binaryedge.io/SEv2/glossary/` | `FAILED` |
| 18 | ZoomEye | `https://zoomeye.org/api/doc` | `FAILED` |
| 19 | ZoomEye | `https://www.zoomeye.hk/doc?channel=api` | `FAILED` |
| 20 | Criminal IP | `https://www.criminalip.io/developer/api/get-ip-data` | `FAILED` |
| 21 | FOFA | `https://en.fofa.info/api` | `RETRIEVED_NO_LOAD_BEARING_CONTENT` |
| 22 | Criminal IP | `https://www.criminalip.io/developer/api/get-banner-search` | `FAILED` |
| 23 | FOFA | `https://en.fofa.info/api/stats/statistical` | `RETRIEVED_NO_LOAD_BEARING_CONTENT` |
| 24 | Shodan | `https://developer.shodan.io/api/trends` | `RETRIEVED_LOAD_BEARING` |
