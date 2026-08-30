# Source portfolio V1

**Status:** Recommendation. Produced by Mission 1.7 §38–§40.
**Date:** 2026-08-30
**Governed by:** [`source-registry-v1.md`](source-registry-v1.md)
**Measured from:** [`source-signal-coverage-v1.md`](source-signal-coverage-v1.md)
(generated) and [`source-review-results-v1.md`](source-review-results-v1.md)
(generated)

---

## 0. What this is

A recommendation for which sources future missions should build collectors for,
grouped by **what the system needs to be able to see** rather than by platform.

It is not a ranking of source quality, it contains no weights, and it is not an
input to any score. §39 asks for implementation priority and is explicit that
this is not opportunity scoring; the two are different questions about different
objects and the tiers below never leave this document.

---

## 1. The state it starts from

Twenty-seven registered sources. Eight in an approving state. **Three
collector-eligible, one collector implemented, one collector enabled.**

The bias is not in the catalog. It is in what may be used:

| | Registered | Approving |
|---|---|---|
| economic data | 3 of 27 (11%) | **3 of 8 (37%)** |
| social / community / gaming / creator / app store | 11 of 27 (41%) | **0 of 8 (0%)** |
| knowledge / news / developer | 9 of 27 | 5 of 8 |

**Every consumer-facing family is registered and none is approving.** That
single row is the finding of Mission 1.7, and it is a finding about platform
terms rather than about the review: `social`, `community`, `gaming`, `creator`
and `app_store` contain eleven sources, and each one is `PROHIBITED`,
`RESTRICTED`, or blocked because a document was silent or unreachable.

### 1.1 Seven of sixteen signal families have no usable source

`desire`, `creativity`, `competition`, `collection`, `personalization`,
`status`, `problem`.

Two of those deserve comment.

**`problem` is uncovered.** The system Mission 1.7 was told not to become — a
business pain detector — is not currently something it *could* become. Every
source that exposes stated problems (`reddit`, `stack-exchange`, `hacker-news`,
the app stores, `github`, `steam`, `bluesky`) is blocked or pending. This is
worth stating plainly because the mission's framing assumes pain coverage is the
default that needs balancing, and in this portfolio it is not the default and
does not exist.

**`personalization` and `status` have no registered source at all**, blocked or
otherwise. Every other uncovered family is blocked on a verdict; these two are
blocked on the catalog containing nothing that exposes them. That is a discovery
gap rather than a governance one, and it is the only one of its kind.

---

## 2. Portfolio by need

### FOUNDATIONAL MARKET CONTEXT

| | |
|---|---|
| **Usable now** | `world-bank` (implemented, enabled), `eurostat`, `fred` (both eligible, neither implemented) |
| **Promising** | — |
| **Blocked** | — |
| **Missing** | Nothing. This is the only need group that is complete, and it is complete because statistics agencies publish licences |

### KNOWLEDGE, CULTURE AND PUBLIC INTEREST

| | |
|---|---|
| **Usable now** | `wikimedia-pageviews`, `openalex`, `gdelt` — approving, conditions unverified |
| **Promising** | — |
| **Blocked** | — |
| **Missing** | Nothing structural. This group did not exist before this mission and is now the second-strongest |

### DEVELOPER ECOSYSTEM

| | |
|---|---|
| **Usable now** | `npm-registry`, `pypi` |
| **Promising** | `huggingface` — silent terms; one clarifying document would settle it |
| **Blocked** | `github` (`RESTRICTED`) |
| **Missing** | Non-JavaScript, non-Python ecosystems. Both approved registries are single-language |

### USER DISCUSSION

| | |
|---|---|
| **Usable now** | **nothing** |
| **Promising** | `bluesky` — technically the most open social platform available, blocked only by silence |
| **Blocked** | `reddit`, `stack-exchange` (documents unreachable), `hacker-news` (operator clarification), `discord` (403), `x-twitter` (402) |
| **Missing** | Any usable source of people describing problems in their own words |

### CONSUMER DESIRE

| | |
|---|---|
| **Usable now** | **nothing** |
| **Promising** | `pinterest` — saving is an expression of want with no complaint and no purchase attached, which is the cleanest desire signal any candidate offers. Terms unread |
| **Blocked** | `apple-app-store`, `google-play`, `product-hunt`, `steam` (all `RESTRICTED`) |
| **Missing** | Wishlist, save and pre-order behaviour from any source |

### GAMING

| | |
|---|---|
| **Usable now** | **nothing** |
| **Promising** | **nothing** |
| **Blocked** | `steam` (`RESTRICTED`), `twitch` (agreement unread) |
| **Missing** | Everything. `competition` and `collection` rest entirely on Steam, and Steam is outside its own grant for this use |

### CREATOR ECONOMY

| | |
|---|---|
| **Usable now** | **nothing** |
| **Promising** | `huggingface` (creation of models and datasets is authored work, partially) |
| **Blocked** | `youtube` (`PROHIBITED`), `tiktok` (`PROHIBITED`), `twitch` (unread) |
| **Missing** | Any source of what individual creators publish and how audiences respond |

### SEARCH AND TREND

| | |
|---|---|
| **Usable now** | `wikimedia-pageviews` — article views are a direct attention measure |
| **Promising** | `google-trends` — official API still alpha, access granted rather than open |
| **Blocked** | — |
| **Missing** | Purchase-intent search, which Wikipedia views do not approximate |

### PRODUCT AND COMPETITION

| | |
|---|---|
| **Usable now** | `gdelt` (company and product mentions in coverage) |
| **Promising** | — |
| **Blocked** | `product-hunt`, `apple-app-store`, `google-play` (all `RESTRICTED`) |
| **Missing** | Pricing, ratings and launch data. `gdelt` sees what is *written about* products, not the products |

---

## 3. Collector implementation priority

Qualitative tiers. §39 forbids fake precision and these are not scores; two
sources in the same tier are not equal, and a tier does not divide.

Priority weighs eligibility, signal diversity, API stability, compliance
complexity, cost, implementation complexity and overlap. Where those pull in
different directions the tie is broken by **what the portfolio cannot currently
see**, because a fourth economic source adds less than a first source of any
uncovered family.

### HIGH

| Source | Why | What it needs first |
|---|---|---|
| `wikimedia-pageviews` | The only approving source that measures *attention* directly. Covers `curiosity`, `trend`, `discovery`, `entertainment` and `learning` from one stable, well-documented API with published limits and no key. It is also the single best answer to §24 | The User-Agent and attribution conditions verified |
| `gdelt` | The most permissive terms in the catalog, by a distance, and the only approving source touching `social` and `community`. Free, no key, bulk files available | Its attribution condition verified |

Both are HIGH for the same structural reason: they are approving, they are
cheap, and they cover families nothing else covers. Neither needs a credential,
a vendor conversation or a paid tier.

### MEDIUM

| Source | Why | What it needs first |
|---|---|---|
| `openalex` | CC0 removes every licensing question at once. Overlaps `wikimedia-pageviews` on `learning` and `discovery`, which is why it is not HIGH, and it leads consumer behaviour by years | `OPENALEX_CONTACT_EMAIL` configured; a spend ceiling decided, since the API is now metered |
| `eurostat` | Already eligible and already unblocked. Zero governance work remains | Nothing. It is a pure implementation task |
| `npm-registry` | The only source in the catalog with an explicit replication grant. Narrow — one language ecosystem — which is what keeps it out of HIGH | Its API-only and volume conditions verified |

### LOW

| Source | Why |
|---|---|
| `pypi` | Approving on the weaker footing described in the expansion record: commercial use is `NOT_ADDRESSED` rather than permitted, and no numeric rate limit is published to build against |
| `fred` | Eligible only where `FRED_API_KEY` is configured, and overlaps `world-bank` heavily. A third macroeconomic source is the least valuable addition available |

### BLOCKED — do not implement

`reddit`, `stack-exchange`, `hacker-news`, `google-trends`, `bluesky`,
`huggingface`, `twitch`, `discord`, `x-twitter`, `pinterest`, `product-hunt`,
`github`, `apple-app-store`, `google-play`, `steam`, `meta-instagram`,
`youtube`, `tiktok`, `spotify`.

Nineteen of twenty-seven. The orchestrator will refuse to plan acquisition for
any of them and `sros-source enable` will refuse to switch one on, so this row
is a summary of a mechanism rather than a request for restraint.

### 3.1 The highest-value work is not a collector

Two sources are HIGH and both are blocked on the same missing thing: a
**capability that can verify an attribution obligation**, and one that can
verify how a client identifies itself.

`source-attribution-display` already exists and is described in its own
registration as shared and parameterised. What the five newly approved sources
lack is a `source-compliance-v1.json` entry describing their obligations. That
is configuration rather than code, it is what Mission 1.4 did for the economic
three, and doing it for `gdelt` and `wikimedia-pageviews` would move two
sources from approving to eligible without a line of collector code.

**That is the cheapest large improvement available to Mission 1.8**, and it is
worth more than any single collector: it converts an entire approving tier into
a usable one.

---

## 4. Answering the question this portfolio exists for

> Can this source mix discover an opportunity with almost no pain signal?

**Partly, and for the first time.**

Before this mission the answer was no, with nothing to argue about: three
macroeconomic sources cannot see a person wanting anything.

`wikimedia-pageviews` changes it. Article views measure attention with no
complaint, no purchase and no review required — someone reading about a hobby,
a game or a technique leaves a record of interest and nothing else. Combined
with `gdelt`'s theme volume and `openalex`'s concept emergence, the portfolio
can now observe a topic rising in public attention before any product exists.

Against the §24 examples:

| Example | Detectable now? | With what |
|---|---|---|
| AI image creation | **partly** | `openalex` concept emergence, `huggingface` model publication (pending), `wikimedia` article views |
| Prediction games, fantasy sports | **weakly** | `wikimedia` views on the underlying sport or event only |
| Avatar customization | **no** | `personalization` has no registered source |
| Quizzes, learning games | **weakly** | `wikimedia` and `openalex` see the subject, never the play |
| Hobby trackers | **partly** | `wikimedia` views on the hobby; nothing on tracking behaviour |
| Fan communities | **no** | `community` rests on `gdelt` entity mentions, which see coverage of a community and not the community |
| Collection tools | **no** | `collection` is uncovered; only `steam` exposes it and `steam` is `RESTRICTED` |
| Creative generators | **partly** | `openalex`, `huggingface` (pending) |
| Social challenges | **no** | Requires social platforms; none is approving |

**Five of nine are no or weak**, and the pattern in the failures is consistent:
the portfolio can see *interest in a subject* and cannot see *people doing
things*. Attention is covered; behaviour is not.

Of the seventeen canonical behaviours, the approving sources record **seven**:

```text
recorded    automate  collaborate  consume  create  discover  discuss  learn
missing     buy  collect  compare  compete  customize  play  predict  sell
            share  track
```

Read the second row as a list of verbs. Every one of them is something a person
*does*, and the first row is almost entirely things a person *reads, writes or
installs*. `play`, `compete`, `collect` and `customize` — the four that carry
the desire-driven product categories §24 asks about — have no approving source
at all, and even `share`, the most basic social act, has none.

That is a sharper statement of the gap than the family table gives, and it
points at the same place: **Steam and the social platforms are where behaviour
lives**, and none of them is usable.

---

## 5. What would change the picture most

In order of effect per unit of work, and none of it is a collector:

1. **Compliance configuration for `gdelt` and `wikimedia-pageviews`** — converts
   the two HIGH sources from approving to eligible. Config, not code.
2. **Retrieve the four unreachable documents** (`x-twitter`, `discord`,
   `twitch`, `pinterest`) from an ordinary browser session. Four verdicts are
   currently `NOT_ASSESSED` for environmental reasons, and `twitch` plus
   `pinterest` are the entry points to gaming-creator and desire respectively.
3. **Ask Bluesky one question** — whether a developer terms document exists
   separate from the user ToS. A single answer would settle the most open social
   platform available.
4. **Decide MODEL-01** — whether the registry can express federated sources. It
   is the difference between having zero and several open social protocols.
5. **Establish whether Meta exposes public content at all** — a capability
   question that would close a source without legal reading.

Note what is absent: "approach Steam", "buy an X tier". Both are legitimate and
both are vendor conversations with cost and lead time, and neither is the
cheapest next move.
