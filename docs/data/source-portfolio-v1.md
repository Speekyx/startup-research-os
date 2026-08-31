# Source portfolio V1

**Status:** Recommendation. Produced by Mission 1.7 §38–§40, revised by
Mission 1.8 after three of the five newly approving sources were downgraded on
audit.
**Date:** 2026-08-30 (revised)
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

Twenty-seven registered sources. **Five in an approving state. Four
collector-eligible, one collector implemented, one collector enabled.**

Mission 1.8 audited every approving review against the assessed use and
downgraded three that rested on silence rather than on a grant — `pypi`,
`npm-registry` and `wikimedia-pageviews`. The register is more honest and the
portfolio is narrower, and both halves of that are reported here.

The bias is not in the catalog. It is in what may be used, and it got worse:

| | Registered | Approving |
|---|---|---|
| economic data | 3 of 27 (11%) | **3 of 5 (60%)** |
| social / community / gaming / creator / app store | 11 of 27 (41%) | **0 of 5 (0%)** |
| developer | 4 of 27 | **0 of 5** |
| knowledge / news | 3 of 27 | 2 of 5 |

**Every consumer-facing family is registered and none is approving**, and the
developer family joined them when npm and PyPI were downgraded. The approving
set is now three statistics agencies, one scholarly catalog and one news
monitor.

### 1.1 Eight of sixteen signal families have no usable source

`desire`, `entertainment`, `creativity`, `competition`, `collection`,
`personalization`, `status`, `problem`.

`entertainment` joined that list in Mission 1.8: Wikimedia Pageviews was its
only approving source, and the downgrade took it. **The portfolio's answer to
desire-driven discovery got weaker, not stronger, and the reason is that the
answer had been resting on a misreading.**

Two observations still stand from Mission 1.7. `problem` is uncovered, so the
business pain detector this project was told not to become is not currently
something it *could* become. And `personalization` and `status` have no
registered source at all — a discovery gap rather than a governance one, and
still the only one of its kind.

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
| `gdelt` | **Collector-eligible since Mission 1.8, and RESOURCE-READY since Mission 1.9.2.** The most permissive terms in the catalog by a distance, free, no key, and the only approving source touching `social` and `community`. Two authorised resources now exist — `web-ngrams/1gram` and `web-ngrams/2gram` — on a reviewed `DATASET_DOWNLOAD` route | Nothing governance-side. It is a pure implementation task, and a smaller one than it was: a gzipped four-column file with no pagination, no query construction and no envelope ambiguity |

**"Nothing governance-side" was optimistic when Mission 1.8 wrote it**, and the
correction is worth keeping. Mission 1.9 found that GDELT's reviewed API route
and its authorised data categories did not intersect, and Mission 1.9.1 found the
route unreachable from two independent environments. What made the sentence true
was a **second governance round** — a new review version, a reviewed access
route, three minimisation categories, two dataset entries and an acquisition
ceiling. Eligibility was never the last gate; it was the third of four.

One entry, where Mission 1.7 had two. `wikimedia-pageviews` was the other and is
now `REQUIRES_REVIEW`; it returns to this tier the moment **H-24** is answered,
and its compliance work is already specified in
[`wikimedia-pageviews-compliance-v1.md`](wikimedia-pageviews-compliance-v1.md).

### MEDIUM

| Source | Why | What it needs first |
|---|---|---|
| `eurostat` | Already eligible and already unblocked since Mission 1.4. Zero governance work remains | Nothing. A pure implementation task |
| `openalex` | CC0 removes every licensing question at once, and it leads consumer behaviour by years | `OPENALEX_CONTACT_EMAIL` configured; a spend ceiling decided, since the API is metered |

### LOW

| Source | Why |
|---|---|
| `fred` | Eligible only where `FRED_API_KEY` is configured, and overlaps `world-bank` heavily. A third macroeconomic source is the least valuable addition available |

### BLOCKED — do not implement

`reddit`, `stack-exchange`, `hacker-news`, `google-trends`, `bluesky`,
`huggingface`, `twitch`, `discord`, `x-twitter`, `pinterest`, `product-hunt`,
`github`, `apple-app-store`, `google-play`, `steam`, `meta-instagram`,
`youtube`, `tiktok`, `spotify`, **`npm-registry`**, **`pypi`**,
**`wikimedia-pageviews`**.

Twenty-two of twenty-seven, three of them added by Mission 1.8's audit. The orchestrator will refuse to plan acquisition for
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

In order of effect per unit of work. The list changed materially in Mission 1.8:
the compliance-configuration item at the top is **done** for GDELT and is why it
is eligible, and answering one legal question now outranks everything else.

1. **Answer H-24** — are aggregate Wikimedia pageview counts Licensed Material
   under CC BY-SA 4.0? It is the only thing standing between the portfolio and
   its single best `curiosity`, `entertainment` and `trend` source, and the
   compliance work behind it is already specified.
2. **Find a grant for the developer ecosystem.** npm and PyPI were the whole of
   `developer_activity` coverage and both are now pending. npm's replication
   grant is real and narrow; what is missing is any statement about commercial
   reuse, derived analytics or model processing.
3. **Retrieve the four unreachable documents** (`x-twitter`, `discord`,
   `twitch`, `pinterest`) from an ordinary browser session.
4. **Ask Bluesky one question** — whether a developer terms document exists
   separate from the user ToS.
5. **Decide MODEL-01** — whether the registry can express federated sources.

Note what is absent: "approach Steam", "buy an X tier". Both are legitimate
vendor conversations with cost and lead time, and neither is the cheapest next
move.

## 5.2 What Mission 1.15 changed about this document

The list in §5 was written before the demand-side round. Three of its items have
moved and one has been superseded.

**Item 4 is answered.** Bluesky *does* publish a developer terms document
separate from the user ToS — its own documentation domain names "Bluesky
Developer Guidelines". It could not be retrieved (301 to `bsky.network`, empty
body). The question is no longer *does one exist* but *what does it say*, which
is a narrower and more actionable thing to ask.

**Item 3 lost `pinterest`.** The document was retrieved from
`policy.pinterest.com` and it closes the source: no storage of API information at
all, automated extraction prohibited, and platform-insights or competitor-research
features requiring explicit written authorization. Pinterest was this document's
best DESIRE hypothesis; it is now RESTRICTED on evidence.

**A new item outranks all five.** `ted-eu` — EU public procurement — has five of
the six load-bearing activities granted in a single retrieved sentence and one
activity, `model_processing`, unaddressed. It would be the portfolio's first
WILLINGNESS_TO_PAY source, and WTP is a family that had *no registered candidate
at all* until this round. Retrieving one more first-party instrument is the
cheapest remaining move by a wide margin.

See `demand-side-source-priority-v1.md` for the full ranking and
`demand-side-source-coverage-v1.md` for what each family actually has.

**The shape of the finding is unchanged, and worth restating.** This document has
said since Mission 1.7 that the portfolio is strong on published aggregate
context and empty on individual behaviour. Mission 1.15 examined nine sources and
did not change that. What it changed is how much of the emptiness is *known* to
be closed rather than merely unexplored.

## 5.3 What Mission 1.15.2 changed about this document

The `ted-eu` item added in §5.2 has moved, and not in the direction the effort
suggested.

**H-34 closed PERMITTED.** Commission Decision 2011/833/EU was read in full from
the Publications Office Cellar. Reuse is defined by *purpose* and not by
*method*, so machine processing of reused notices falls inside the grant. All six
load-bearing activities are now positively granted.

**`ted-eu` is still `REQUIRES_REVIEW`**, blocked by one question the Decision
does not touch: whether the reuse framework reaches the sui generis database
right, given that the documented route is bulk extraction of substantial parts
(H-36).

**What that costs this document's ranking.** The cheapest-next-move logic in §5
assumed TED's blocker was a document to fetch. It is now a legal question the
documents do not answer, and legal questions are slower and less certain than
retrievals. `ted-eu` remains the portfolio's only route to transaction-class
evidence and its expected time-to-usable got worse, not better.

## 5.1 What Mission 1.9.2 changed about this document

The HIGH row above now says something it could not before: **GDELT has a
concrete authorised resource.** That is a fourth fact, distinct from eligible,
implemented and enabled, and this document had no way to express it — which is
why the row read "a pure implementation task" for two missions while the resource
layer refused every request GDELT could have made.

`sros-source readiness` reports all four now. The portfolio's tiers are still
qualitative judgements about value; the readiness columns are derived facts about
state, and keeping them apart is the point.

## 6. What Mission 1.8 changed about this document

Mission 1.7 recommended `wikimedia-pageviews` and `gdelt` as the two HIGH
priorities and said the cheapest large win was compliance configuration for
both. Half of that was right: GDELT's configuration took an afternoon and made
it eligible. The other half was resting on a misreading of Wikimedia's evidence,
and the audit that found it also removed `entertainment` from the covered list.

**A recommendation that survives contact with an audit is worth more than one
that does not have to.** This one did not, entirely, and the revision is the
record of that.

### 5.4 Update after Mission 1.15.3 — the blocker is now a message

`ted-eu` moved from *"a legal question the documents do not answer"* to *"a legal
question with a named addressee and a drafted message"*.

The first-party dataset material is exhausted. The Publications Office's own DCAT
record attaches `dct:license = COM_REUSE` to **every** `ted-1` distribution
including the bulk XML download, and that licence carries `skos:exactMatch` to
Commission Decision 2011/833/EU — the instrument already read in full and already
known to contain no database-right provision. The search API's OpenAPI "Terms of
Usage" section resolves to the same TED legal notice. Neither route has a
database-right grant, and **neither route has a different answer**.

H-36 is now tracked as **H-36A** (subsistence: not established, because nothing
names a maker or a substantial investment — the catalogue names a *publisher* and
carries no creator) and **H-36B** (grant: not addressed).

One fact sharpens it without resolving it: the same portal declares **CC BY 4.0**
— whose Section 4 expressly grants extraction and re-utilisation of a substantial
portion — on 12 of 48 distributions of the separate `ted-csv` dataset published by
DG GROW, inconsistently and over coverage that overlaps the `COM_REUSE` files.
Not relied on, and asked about instead.

`ted-eu` remains `REQUIRES_REVIEW` at review v4, remains the portfolio's only
route to transaction-class willingness-to-pay evidence, and remains
collector-ineligible. The next action is to send
`ted-eu-database-right-clarification-request-v1.md`, which is prepared and
**unsent**.

