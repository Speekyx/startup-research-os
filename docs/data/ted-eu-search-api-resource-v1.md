# TED-EU Search API Resource V1

**Authoritative.** Mission 1.15.7, Phase A. The first concrete TED resource, and
the boundary of what it authorises.

**State: `resource_ready` = YES**, for one resource, under one profile, through
one route. **H-36A remains `NOT ESTABLISHED`. H-36B remains `NOT ADDRESSED`.**
No legal clearance was obtained, claimed or implied.

---

## 1. Why a resource had to be authorised before any code

TED reached `AUTHORIZATION_READY` in Mission 1.15.6.1 and stayed uncollectable,
because a source-level approval is not a resource-level one
(`acquisition-authorization-v1.md` §11). The compliance entry authorised
`"datasets": []`, so `context.authorized_dataset(...)` returned `None` for every
resource and `authorize_resource` denied every descriptor for want of a rights
basis and a dataset family.

That is the state Eurostat has been in since Mission 1.4 and GDELT was in for two
missions. The blocker was never a permission. It was that **nothing had said
which concrete thing may be fetched**, and the mission report said so:

> Ce qui reste avant un collecteur n'est plus une permission, c'est une
> ressource.

## 2. The resource

| | |
|---|---|
| `resource_id` | **`notices/eforms-contract-and-award`** |
| Name | TED eForms contract notices and contract award notices (Search API, from 2023-03-01) |
| `dataset_family` | `ted-search-api-notices` |
| `rights_basis` | `NAMED_LICENCE` |
| `licence` | Commission Decision 2011/833/EU on the reuse of Commission documents |
| `content_origin` | `PLATFORM_LICENSED` |
| Profile | `local-private-research-v1` only |
| Review | local **v2** |
| Route | `ted-search-api` |

**The id follows the registry's own convention**, not the mission brief's
suggested string. GDELT's resources are `web-ngrams/1gram`, World Bank's are
`indicator/SP.POP.TOTL`: a collection and a member, source-relative, with no
source prefix — the source is already the key the entry hangs off. The brief
proposed `ted-eforms-contract-and-award-notices-search-api` and said to follow
existing conventions if they implied another exact id. They did.

**The id carries no query.** No date, no CPV, no country, no page size. A
resource id naming a window would make every window a new resource and every
resource unreviewed; the bounds live in the collector configuration, which
refuses to run without them.

## 3. What it contains, and what it is not

**Contains:** eForms **contract notices** (`cn-standard`) and **contract award
notices** (`can-standard`), published from **1 March 2023** onward, reachable
through the TED Search API.

**Is not**, and each of these is a thing somebody could otherwise read it as:

| Not | Why it matters |
|---|---|
| all of TED | the notice families are named, and the collector refuses any other |
| the historical corpus | eForms publication starts 2023-03-01 and the bounds refuse an earlier window |
| every notice family | prior information notices, design contests and the rest are outside it |
| the bulk packages | `ted-bulk-xml-daily` and `ted-bulk-xml-monthly` stay excluded families, refused by name |
| the `ted-csv` historical subset | a separate DG GROW dataset with its own unresolved licence question |
| a mirror | the collector has no exhaustion mode and no unbounded configuration |

## 4. The rights basis, stated precisely

The resource rests on evidence already reviewed, and adds none:

- **Commission Decision 2011/833/EU**, retrieved in full from the Publications
  Office's own Cellar repository in Mission 1.15.2. Article 1 covers documents
  held by the Commission or on its behalf by the Publications Office; Article
  2(1) covers documents published by the Publications Office through websites
  and dissemination tools;
- **TED's own legal notice**, which names that Decision as the instrument under
  which its notices are reusable;
- the **`COM_REUSE`** dataset metadata, whose authority concept carries
  `skos:exactMatch` to the same Decision;
- the **Search API's published intended use** — *"for analysis and reuse"*,
  *"primarily targeted at data reusers"* — which is intended-use evidence and
  **not** a rights grant, as review condition 11 already records;
- **local review v2**, `APPROVED_WITH_CONDITIONS`, four conditions satisfied;
- the **route authorization** from Mission 1.15.6;
- the **operator's recorded acceptance** of the residual exposure.

### 4.1 Why `PLATFORM_LICENSED` and not `THIRD_PARTY`

This is the load-bearing classification, because `third_party_denied` is true in
TED's resource scope and `THIRD_PARTY` would have refused the resource and
stopped the mission.

**The documentary link runs at both ends.** The Decision covers what the
Publications Office publishes through its websites; TED is operated by the
Publications Office and publishes these notices through one; and TED's legal
notice names the Decision. Mission 1.15.2 read the instrument and closed H-34
`PERMITTED` on exactly that chain.

**Article 2(2)(b) is real and does not reach here.** The Decision excludes
documents the Commission cannot allow the reuse of *"in view of intellectual
property rights of third parties"*. That is a class of **document**, not a
statement that procurement notices are third-party owned, and nothing retrieved
across Missions 1.15.1–1.15.4 places them in it. A document the Publications
Office cannot license is outside this resource, and this entry asserts nothing
about one.

### 4.2 What the basis does NOT establish

Written out because each is reachable from the material above and each is wrong:

| Not established | |
|---|---|
| *"TED's database rights are resolved"* | **H-36A is NOT ESTABLISHED** — nothing determines whether a sui generis right subsists, or who would hold it |
| *"the right was granted or waived"* | **H-36B is NOT ADDRESSED** for broad extraction |
| *"a lawyer cleared this"* | no legal review exists, and the operator's own acknowledgement says so |
| *"broad extraction is authorised"* | the acceptance is conditioned on **bounded** queries, and the collector cannot run unbounded |
| *"this reaches the commercial profile"* | it does not exist there; that review is `REQUIRES_REVIEW` |

**The acceptance this rests on is conditional and says so**: bounded,
purpose-scoped queries; field minimisation at acquisition; nothing
redistributed. *"Si l'une de ces conditions cesse d'être vraie, cette
acceptation cesse de s'appliquer."* If any of the three stops holding, the basis
for this resource stops with it.

## 5. Activity scope

Permitted, and each already assessed `PERMITTED` by local review v2: official
automated API acquisition; bounded local storage; derived private analysis,
classification and structured machine processing.

**Not authorised here and refused elsewhere:** redistribution, resale, customer
access, public serving, model training, embeddings (D-12 open), bulk mirroring.
This entry widens none of them and could not: they are refused by the review and
by the gates, not by this document.

## 6. The gate, proved rather than asserted

Run through `build_authorization('ted-eu', 'local-private-research-v1')` with the
persisted operator decision:

```text
notices/eforms-contract-and-award  ted-search-api-notices     ALLOWED
packages/daily-2026-09-01          ted-bulk-xml-daily         REFUSED  family excluded by the review
packages/monthly-2026-08           ted-bulk-xml-monthly       REFUSED  family excluded by the review
csv/contract-awards-2018-2023      ted-csv-historical         REFUSED  family excluded by the review
notices/mystery                    (no family)                REFUSED  unclassified is not known to fall outside
notices/eforms-contract-and-award  THIRD_PARTY content        REFUSED  platform approval grants nothing over it
notices/eforms-contract-and-award  no rights basis            REFUSED  cannot say what authorises it
```

The last two matter as much as the first: the entry is allowed because of what
it records, and an entry recording less is refused.

## 7. What changed, and what did not

**Changed:** `resource_ready` for `ted-eu` under `local-private-research-v1`
moved from **NO** to **YES**, and the operator-facing next step moved from
*authorise a concrete resource* to *implement a collector* — which Phase B then
did.

**Unchanged:** the review, its four conditions, the route authorization, the
minimisation profile, the recorded acceptance, H-36A, H-36B, the commercial
profile's `REQUIRES_REVIEW`, and every excluded family and blocked route.

## 8. Next

The collector is `ted-eu-search-api-collector-v1.md`. The response contract it
parses is `ted-eu-search-api-response-contract-v1.md`. **No normalizer exists**,
and the mapping from these notices to canonical records is Mission 1.15.8.
