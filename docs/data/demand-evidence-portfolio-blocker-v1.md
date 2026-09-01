# Demand and Problem Evidence — Portfolio Blocker V1

**Authoritative.** Mission 1.16. Why no source was added, measured against the
registry rather than against memory.

**Two blockers, and the second is larger than the one the mission went looking
for.**

1. **No source covering `problem` or `desire` has an approving review under any
   profile.** Six are `RESTRICTED` on retrieved terms; four are
   `REQUIRES_REVIEW`, and the three worth advancing are blocked on documents this
   environment cannot retrieve.
2. **The runtime declares `local-private-research-v1`, and exactly one review in
   the whole registry is under that profile.** World Bank and GDELT — which hold
   15 of the 23 RawRecords and 7 of the 8 Evidence rows — are **BLOCKED** today.

---

## 1. The coverage matrix, computed from the registry

29 registered sources. Current reviews, by profile:

| Profile | APPROVED_WITH_CONDITIONS | RESTRICTED | REQUIRES_REVIEW | PROHIBITED |
|---|---|---|---|---|
| `commercial-multi-tenant-research-v1` | 5 | 8 | 13 | 3 |
| **`local-private-research-v1`** | **1** | 0 | 0 | 0 |

Signal-family coverage of the approving sources:

| Family | Approving sources | Other registered candidates |
|---|---|---|
| `commercial` | eurostat, fred, gdelt, ted-eu, world-bank | app stores, google-trends, hacker-news … |
| `trend` | eurostat, fred, gdelt, openalex, ted-eu, world-bank | many |
| `community` | gdelt | bluesky, hacker-news, reddit, steam |
| `curiosity` | gdelt, openalex | google-trends, reddit, wikimedia-pageviews |
| `social` | gdelt | bluesky, reddit |
| `developer_activity` | openalex | github, hacker-news, huggingface, npm-registry |
| `discovery` | openalex | bluesky, google-trends, hacker-news |
| `learning` | openalex | pypi, stack-exchange, wikimedia-pageviews |
| `competition` | ted-eu | steam, usaspending |
| **`problem`** | **ted-eu only** | app stores, bluesky, github, hacker-news, stack-exchange, steam |
| **`desire`** | **none** | app stores, product-hunt, reddit, steam |
| `creativity` | none | github, huggingface |
| `entertainment` | none | app stores, steam, wikimedia-pageviews |
| `collection` | none | steam |

**`problem` is nominally covered and substantively is not.** TED is the only
approving source carrying it, and what TED observes is a public buyer's
procurement need expressed as a contract award. That is a real problem signal
about institutional purchasing; it is not a user finding a tool frustrating, and
treating one as evidence of the other is the substitution this portfolio exists
to avoid.

## 2. Blocker 1 — the demand and problem candidates

Ten sources cover `problem` or `desire`. Every one of them, with its current
verdict:

| Source | State | Why it does not become the answer |
|---|---|---|
| `apple-app-store` | `RESTRICTED` | terms reviewed and restrictive |
| `google-play` | `RESTRICTED` | terms reviewed and restrictive |
| `hacker-news` | `RESTRICTED` | Y Combinator terms prohibit data mining, scraping and commercial derivative works. `automated_access` `NOT_PERMITTED` |
| `github` | `RESTRICTED` | `commercial_use` and `derived_analytics` both `NOT_PERMITTED` |
| `product-hunt` | `RESTRICTED` | `commercial_use` `NOT_PERMITTED` |
| `steam` | `RESTRICTED` | terms reviewed and restrictive |
| `stack-exchange` | `REQUIRES_REVIEW` | **the strongest semantic fit, and the blocker is unchanged.** See §2.1 |
| `reddit` | `REQUIRES_REVIEW` | the Data API terms are unfetchable from this environment; `storage`, `derived_analytics` and `model_processing` are all `NOT_ASSESSED` |
| `bluesky` | `REQUIRES_REVIEW` | every one of the six load-bearing activities is `NOT_ADDRESSED`; its docs redirect to technical material that governs none of them |
| `ted-eu` | `REQUIRES_REVIEW` under commercial | already collected, under the *local* profile, and it is the source this mission is told not to deepen |

### 2.1 Stack Exchange, and why it was the right candidate to try

It is the best semantic fit in the registry for this mission's target. A question
is solution-seeking by construction rather than by interpretation; the answers and
their acceptance make repeated problems visible; there is an official API and a
CC BY-SA licence on content.

Its Mission 1.15 review left three open questions, two of which need documents
that stackoverflow.com served behind an anti-bot interstitial. **That was retried
in this mission and the environment cannot reach the host at all** — neither
`stackoverflow.com/legal/terms-of-service/public` nor `api.stackexchange.com`.

**No bypass was attempted**, and none would have been acceptable: §7 and §8 of the
brief forbid it, and `source-registry-v1.md` rule 2 is that uncertainty is never
permission. An approval written on terms nobody could read would be exactly the
approval the registry exists to prevent.

**What would move it:** retrieving those two documents from an environment that
serves them, and assessing `commercial_use`, `storage`, `derived_analytics` and
`model_processing` against them. That is a review act with a first-party
retrieval, not an engineering one.

## 3. Blocker 2 — the profile the runtime actually declares

`infrastructure/compose/.env` sets `SROS_USE_PROFILE=local-private-research-v1`,
and a worker resolves the profile from that declaration: `run_acquisition_job`
takes `use_profile=None` meaning *ask the runtime*, and there is deliberately no
default.

**Exactly one source in the registry has a review under that profile: `ted-eu`.**

So today:

```text
sros-source --use-profile local-private-research-v1 eligibility world-bank
  world-bank: BLOCKED
    - no policy review exists for use profile 'local-private-research-v1'

sros-source --use-profile local-private-research-v1 authorization world-bank
  REFUSED: no acquisition authorization for world-bank
    - no policy review exists for use profile 'local-private-research-v1'
```

The same is true of `gdelt`, `eurostat`, `fred` and `openalex`.

### 3.1 Why this is not a defect in the gate

The gate is doing precisely what ADR-027 built it to do. *"Never transfer
approval between profiles… Nothing falls back."* Those five sources were
reviewed for a **public multi-tenant SaaS**, and nobody has yet written down what
they permit for **this** deployment. The gate refuses rather than guessing, which
is right.

### 3.2 Why it matters anyway

**The deployment holds real data it could not re-collect today.** 15 of 23
RawRecords and 7 of 8 Evidence rows come from World Bank and GDELT, gathered in
Missions 1.5 to 1.11 — **before ADR-027 existed**. Their provenance carries no
`use_profile` at all, which is the visible trace of having been collected under a
model that had no such concept.

Nothing improper happened: those collections were authorised under the rules in
force, and the profile mechanism was introduced afterwards. But the registry now
says something the pipeline's own history does not, and that gap will be
discovered by whoever next tries to refresh a World Bank series and finds the job
refused.

**It also silently caps portfolio expansion.** Any new source, however good its
commercial review, is blocked at runtime until somebody assesses it for the local
profile. That work is a review act per source, and it is now on the critical path
for every future source mission.

## 4. What was deliberately not done

- **No source was forced.** §10 of the brief is explicit, and every candidate
  fails on a term nobody has read or a term that has been read and refuses.
- **No anti-bot system was bypassed**, no browser was impersonated, no
  undocumented endpoint was probed.
- **No review was written on unread documents.** Stack Exchange stays
  `REQUIRES_REVIEW` with its three open questions unchanged.
- **No local-profile review was written for World Bank or GDELT.** It would
  unblock them and it is a governance act with its own evidence requirements, not
  a side effect of a source-expansion mission.
- **No existing data was touched.** TED, World Bank and GDELT rows, semantics and
  counts are unchanged.

## 5. The two missions this splits into

**A. `local-private-research-v1` reviews for the collected sources.** Assess
World Bank, GDELT and the other approving sources against the *actual* local use,
so the registry stops contradicting the pipeline's own history. Smallest, most
urgent, and unblocks everything downstream of it.

**B. Stack Exchange review completion.** Retrieve the two documents from an
environment that serves them and close the three open questions. If they approve,
it is the best `problem` and solution-seeking source in the registry, and this
mission's engineering work becomes available immediately.

**They are ordered.** B without A produces an approving commercial review for a
source the runtime still refuses.
