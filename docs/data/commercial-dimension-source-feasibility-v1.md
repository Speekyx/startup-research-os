# Commercial dimension source feasibility V1

**Status:** Desk review. Authored by Mission 1.33, 2026-09-03.
**Machine-readable matrix:** [`commercial-dimension-source-feasibility-v1.json`](commercial-dimension-source-feasibility-v1.json)
**Outcome:** `COMMERCIAL_SOURCE_GRAIN_MISMATCH`
**Governed by:** [ADR-027](../architecture/adr/ADR-027-use-profile-scoped-source-permission.md),
[`source-registry-v1.md`](source-registry-v1.md),
[`canonical-subject-registry-v1.json`](canonical-subject-registry-v1.json)

---

## 0. What this document is, and what it is not

It answers one question over the 29 registered sources: **which of them could
produce an observation at the grain of `subject:docker` that would support a
commercial Opportunity dimension?**

Three things it is not:

- **Not an authorization.** Every governance column is COPIED from
  `source-catalog-v1.json`. No verdict in this document changes any source's
  standing, and a feasibility verdict is not a permission.
- **Not an acquisition plan.** Nothing was collected. Where a fact about a
  source's catalogue could only be established by querying it, this document
  says so rather than guessing.
- **Not a ranking of Opportunities.** §14's priorities rank SOURCES for future
  work, ordinally, with no score and no weights.

**No acquisition, no model call, no new canonical record.** Every counter is
unchanged.

---

## 1. The finding, in one paragraph

The portfolio splits cleanly, and neither half can close the gap. **The sources
that can name Docker carry no commercial semantics; the sources that carry
commercial semantics cannot name Docker.** Five sources can identify Docker at an
acceptable grain — two are already in the packet and are epistemically exhausted,
and the other three are governance-blocked for a reason that a governance mission
would not clear. The sources with genuine `MARKET_ACTIVITY`,
`BUYER_OR_BUDGET_EXISTENCE` and `ECONOMIC_VALUE` warrants — TED above all, which
is fully built and already producing Evidence — observe procurement CATEGORIES,
and no depth of that vocabulary reaches a software product.

That is outcome D, and it makes the next step an architecture question rather
than a source question.

---

## 2. The matrix

`grain` is whether the source publishes an identifier that NAMES the container
platform: **YES**, **MENTION** (reachable only as a word, a topic, or a related
but different artifact), or **NO**.

| Source | Family | Grain | Dimension(s) it could support | Local review | Collector | Verdict |
|---|---|---|---|---|---|---|
| `github` | developer | **YES** | COMPETITIVE_SUPPLY, FEASIBILITY_SIGNAL | NONE | — | `RESTRICTED` |
| `product-hunt` | product_discovery | **YES** | COMPETITIVE_SUPPLY | NONE | — | `RESTRICTED` |
| `reddit` | community | **YES** | SOLUTION_DISSATISFACTION | NONE | — | `UNKNOWN_REQUIRES_REVIEW` |
| `stack-exchange` | forum | **YES** | — | v2 APPROVED_WITH_CONDITIONS | ✔ | `NO_VALID_COMMERCIAL_DIMENSION` |
| `wikimedia-pageviews` | knowledge | **YES** | — | v2 APPROVED_WITH_CONDITIONS | ✔ | `NO_VALID_COMMERCIAL_DIMENSION` |
| `gdelt` | news | MENTION | — | v2 APPROVED_WITH_CONDITIONS | ✔ | `WRONG_GRAIN` |
| `npm-registry` | developer | MENTION | — | NONE | — | `WRONG_GRAIN` |
| `pypi` | developer | MENTION | — | NONE | — | `WRONG_GRAIN` |
| `openalex` | knowledge | MENTION | — | v1 APPROVED_WITH_CONDITIONS | — | `WRONG_GRAIN` |
| `hacker-news` | community | MENTION | — | NONE | — | `RESTRICTED` |
| `google-trends` | search_trends | MENTION | — | NONE | — | `WRONG_GRAIN` |
| `huggingface` | developer | MENTION | — | NONE | — | `WRONG_DOMAIN` |
| `ted-eu` | public_procurement | NO | — | v2 APPROVED_WITH_CONDITIONS | ✔ | `WRONG_GRAIN` |
| `usaspending` | public_procurement | NO | — | NONE | — | `WRONG_GRAIN` |
| `world-bank` | economic_data | NO | — | v2 APPROVED_WITH_CONDITIONS | ✔ | `WRONG_GRAIN` |
| `fred` | economic_data | NO | — | v1 APPROVED_WITH_CONDITIONS | — | `WRONG_GRAIN` |
| `eurostat` | economic_data | NO | — | v1 APPROVED_WITH_CONDITIONS | — | `WRONG_GRAIN` |
| `bluesky` | social | NO | — | NONE | — | `WRONG_GRAIN` |
| `x-twitter` | social | NO | — | NONE | — | `WRONG_GRAIN` |
| `discord` | community | NO | — | NONE | — | `WRONG_GRAIN` |
| `apple-app-store` | app_store | NO | — | NONE | — | `WRONG_DOMAIN` |
| `google-play` | app_store | NO | — | NONE | — | `WRONG_DOMAIN` |
| `steam` | gaming | NO | — | NONE | — | `WRONG_DOMAIN` |
| `spotify` | content_platform | NO | — | NONE | — | `WRONG_DOMAIN` |
| `youtube` | content_platform | NO | — | NONE | — | `WRONG_DOMAIN` |
| `twitch` | creator | NO | — | NONE | — | `WRONG_DOMAIN` |
| `tiktok` | social | NO | — | NONE | — | `WRONG_DOMAIN` |
| `meta-instagram` | social | NO | — | NONE | — | `WRONG_DOMAIN` |
| `pinterest` | product_discovery | NO | — | NONE | — | `WRONG_DOMAIN` |

**5 YES, 7 MENTION, 17 NO. 3 rows name a dimension. All three are blocked.**

Per-source grain notes, epistemic warrants, the full list of what each would not
establish, and the primary blocker are in the JSON.

---

## 3. The structural fact behind most of the table

**Twenty-one of the twenty-nine sources have no `local-private-research-v1`
review at all.** The runtime declares that profile, and ADR-027 says approval
never transfers between profiles — not to another profile, and not to a source's
legacy verdict. So those twenty-one are refused at the gate today for a reason
that has nothing to do with their terms.

Eight have one, and all eight are `APPROVED_WITH_CONDITIONS`: `eurostat`, `fred`,
`gdelt`, `openalex`, `stack-exchange`, `ted-eu`, `wikimedia-pageviews`,
`world-bank`.

It would be easy to read that as *twenty-one missing reviews, therefore
twenty-one opportunities*. For the three candidates that matter it is not, and
§4 and §5 say why: their commercial-profile findings are about the PURPOSE of
the use, and the local profile does not change the purpose. The deployment-model
invariant states it directly — **local deployment never implies
`NON_COMMERCIAL_USE`**, and SROS's research is used to launch commercial
products.

---

## 4. GitHub — the best grain in the portfolio, and a decisive restriction

**The Docker entity.** A repository full name is an exact, publisher-assigned
identifier, and the Docker organisation publishes the platform's own
repositories: `moby/moby`, `docker/compose`, `docker/cli`. The repository topic
`docker` exists as a coarser handle. This is as good a subject identifier as
anything in the portfolio, and it is better than the Stack Overflow tag in one
respect: a repository is a single artifact with one owner, where a tag is a label
many people apply.

**What the route exposes.** The catalog records `repository-metadata`,
`issue-reports`, `timestamps`, `language`, `release-history`. Rate limits are
documented: 60 requests per hour unauthenticated, 5,000 authenticated.

**Which dimensions that could actually support — justified one at a time.**

- **`COMPETITIVE_SUPPLY`** — *"Is there evidence about who already serves this
  need?"* A public repository IS a supplied solution: somebody built a thing and
  published it where anyone can take it. Enumerating maintained repositories in a
  space is a direct, deterministic answer to that question. **This is the
  strongest unclaimed commercial dimension available to SROS anywhere.**
- **`FEASIBILITY_SIGNAL`** — *"Is there evidence bearing on whether an
  intervention could be built and operated?"* Working implementations demonstrate
  buildability. Weaker than the first, and real.
- **`SOLUTION_DISSATISFACTION` — refused.** An issue is a defect report against a
  named artifact. That is not the same as an evaluative statement that the
  artifact is inadequate for the reporter's need, and separating the two means
  reading prose — an `INFERRED` step that does not exist and is not authorised.
- **`WILLINGNESS_TO_PAY`, `BUYER_OR_BUDGET_EXISTENCE`, `MARKET_ACTIVITY`,
  `ECONOMIC_VALUE` — refused.** None of them appears anywhere in repository
  metadata. Stars are not money, and a fork is not a purchase.

**Why governance marks it RESTRICTED.** Acceptable Use Policies section 7 is an
**allowlist**, and it applies *"regardless of whether the information was
scraped, collected through our API, or obtained otherwise"*. It permits two uses:
research, **only if any resulting publications are open access**; and archival.
Commercial market research producing proprietary insights is in neither.

**Is the restriction absolute for this use case?** For the use as it stands, yes,
and the local profile does not soften it. The AUP condition attaches to the
OUTPUT — publications must be open access — not to where the software runs.
`local-private-research-v1` changes the deployment and leaves the output
proprietary, so a local-profile review would meet the same allowlist and fail on
the same clause. **A narrower use is permitted; ours is not.** The one thing that
would move it is not a review at all: it is a commitment that outputs derived
from GitHub are published open access, which is a product decision and is
recorded here as an observation, not a recommendation.

**Is the existing review stale or incomplete?** Not stale: v2 was reviewed
2026-08-29 with a 180-day interval, next due 2027-02-25. Incomplete in two
specific ways, neither of which changes the verdict. First, there is **no
local-profile review**, so the source has no standing under the active profile at
all. Second, the AUP states that collection through the API *"is governed by the
Terms of Service instead"*, and **the Terms of Service have never been
retrieved** — v1 recorded that and v2 resolved the question by noting the
allowlist is method-indifferent, which is sound for the allowlist and leaves a
named governing document unread.

---

## 5. Product Hunt — right grain, and a wall with a doorbell

**Can it identify Docker?** At product grain, yes: a launch post is a listing
with a stable identifier, which is the right shape for enumerating tools.
**Whether the platform lists Docker itself, and which adjacent tools it carries,
was not verified** — establishing that would mean querying the API this review
may not use, and guessing would be worse than the gap.

**What it could support.** `COMPETITIVE_SUPPLY`, and nothing else. A catalog of
launched products records who has shipped something into a space.

**What the presence of products in a catalog does NOT establish**, each stated
separately because each is a tempting read: not market demand (a listing records
a launch, not a want); not product quality; not dissatisfaction; not commercial
success; not revenue. Upvotes are a site counter, and the dimension's own
`never_means` forbids reading a crowded space as closed.

**The blocker.** The API documentation states twice, in plain words, that *"the
Product Hunt API must not be used for commercial purposes"* and directs business
users to `hello@producthunt.com`. Non-commercial use is permitted; ours is
commercial under **both** profiles. So this is not a missing review either — the
route is written permission from a company, obtained by operator correspondence,
which is a human act performed outside this repository. No source in the catalog
carries an `OPERATOR_CORRESPONDENCE` evidence row today, and that tripwire exists
so the first one is a visible diff.

---

## 6. npm, PyPI and the package ecosystems

**Neither registry contains Docker.** The platform is not distributed through
npm, and what npm carries is packages that *drive* Docker — `dockerode` and its
relatives. PyPI is the closest near-miss in the whole portfolio: the `docker`
package there is the official Docker SDK for Python, published by the platform's
own vendor.

**And it is still a miss.** A Python client library is a DIFFERENT ARTIFACT from
the platform it talks to. Its download count measures adoption of the SDK by
Python programs; reading that as adoption of Docker would substitute one thing
for another, which is exactly what the canonical subject registry exists to
prevent. The registry's `docker` entry lists two identifiers, each with a written
basis, and neither was accepted because it resembled the word.

**Merging the ecosystem is the move to refuse.** *All packages that integrate
with Docker* is a coherent and useful set, and it is a **category**, not the
subject. Joining it to `subject:docker` would need a canonical relationship model
— *this package is about that product* — that does not exist and that §10 is
about.

**What they could support, if the grain problem were solved at category scope:**
`COMPETITIVE_SUPPLY` (how many maintained packages serve a need) and
`DISTRIBUTION_SIGNAL` (a registry is a reachable channel). **Download counts do
not establish paying customers, demand for a new product, a buyer count, or
willingness to pay** — a download is a machine fetching a file, and CI systems
fetch a great many.

**Governance is separately unresolved and the two registries are not
equivalent.** npm's terms grant *"You may replicate data from the Public Registry
using the Public APIs"*, which is the clearest single sentence any source in this
catalog offers — with commercial use, derived analytics and model processing all
unaddressed, so rule 8 blocks. PyPI is the one source that once reached an
approving state with **not one** required activity positively permitted; its
cited document contains prohibitions and no grant. Neither has a local-profile
review.

---

## 7. App stores, marketplaces and the rest of the wrong domain

`apple-app-store`, `google-play`, `steam`, `spotify`, `youtube`, `twitch`,
`tiktok`, `meta-instagram` and `pinterest` catalogue consumer apps, games, music,
video and visual discovery. **Docker is developer infrastructure and appears in
none of them at any grain.**

They are marked `WRONG_DOMAIN` rather than `WRONG_GRAIN` because the problem is
not that their identifiers are too coarse — an App Store id is beautifully
precise — but that they identify a different class of thing. Several of them are
also `RESTRICTED` or `PROHIBITED`; that does not need to be reached.

**Forcing these into the Docker Opportunity because their identifiers happen to
be product-shaped is the specific error §7 names**, and it is worth naming
because product-grain is exactly the property this mission was hunting for.

---

## 8. Community sources beyond Stack Exchange

**Reddit is the one genuine candidate, and it is blocked twice.**

A subreddit is a source-native, publisher-assigned identifier, structurally
comparable to a Stack Overflow tag — the one identifier in the portfolio that
could plausibly join the canonical subject on the same basis the tag did.

Epistemically it offers something Stack Exchange does not. Mission 1.32
established that **a request for help is not dissatisfaction**; a discussion forum
carries EVALUATIVE statements about named tools, and a post saying a specific
product became unusable for a stated reason is dissatisfaction with what somebody
uses today. That is `SOLUTION_DISSATISFACTION`'s actual question. It would not
establish that the complainers would switch, that a complaint is representative,
that no adequate solution exists, or any count of people — author identity is not
acquired anywhere in this system.

**Blocker one, governance: genuinely UNKNOWN rather than adverse.** The Data API
Terms, the Developer Terms and the Responsible Builder Policy could not be
retrieved; `commercial_use` is `UNCLEAR`; there is no local-profile review.

**Blocker two, and it is the harder one: extraction.** Distinguishing an
evaluative complaint from a request for help inside free text is a semantic
reading. That is an `INFERRED` path that does not exist, and its nearest relative
`SAME_PROBLEM_FAMILY` is **PARKED**. A Reddit governance mission that succeeded
would deliver a corpus nothing can currently read.

**Hacker News** is `RESTRICTED` on the same purpose-based footing as GitHub: the
Y Combinator Terms prohibit data mining, robots and scraping over Site content
and prohibit commercial derivative works. It also has no product identifier — a
story is about a URL, and the subject is recoverable only by reading text.

**Discord** gates message content behind a privileged intent nobody has applied
for, and every assessed activity is `NOT_ASSESSED`. **Bluesky** and **X** carry no
product-grain identifier and their governing documents were unreachable.

---

## 9. Procurement and economic sources — real commercial semantics, wrong scope

This is the half of the portfolio that has what the Docker packet lacks.

**TED is the case worth stating carefully, because it is fully built.** It is
`APPROVED_WITH_CONDITIONS` under the local profile, has an implemented collector,
an implemented normalizer, an implemented extractor and one Signal already
derived, and its Evidence maps to `MARKET_ACTIVITY`,
`BUYER_OR_BUDGET_EXISTENCE` and `ECONOMIC_VALUE`. Every part of the pipeline
exists.

**And its subject vocabulary is a two-digit CPV division.** The packet the engine
already built for it has the subject key `ted-eu:CPV-division:90`. A CPV division
is a procurement CATEGORY; the vocabulary does not name products at any depth,
and the collector deliberately expands no CPV code into a label. TED cannot name
Docker, and no condition, review or collector change would let it.

**USAspending has the same problem plus a trap.** Its recipient names could match
`Docker, Inc.` — and the canonical subject registry says in its own words that
`subject:docker` is the container platform and **NOT the company**. A contract
awarded to a vendor is evidence about that vendor, not about the platform, and
attaching it would be exactly the subject-identity weakening §9 forbids.

**World Bank, FRED and Eurostat** are economy-scale series. There is no depth of
those vocabularies at which a software product appears. Two of them have working
collectors, which makes the point sharper: **the limitation is the vocabulary,
not the plumbing and not the permission.**

**Recorded as backlog and NOT used here:** a future Opportunity at a broader
market or category scope could legitimately consume these sources. That is §10's
subject, and nothing in this mission attaches any of it to `subject:docker`.

---

## 10. Is the limitation the sources, or the scope model?

**Both, and the architectural one is binding.**

The engine's model is flat. `CanonicalSubject` carries `subject_id`,
`display_name`, `description` and `identifiers` — and **no scope field**.
`subject_for()` returns one subject id per rendered key. A packet holds one
`subject`. So **an Evidence row belongs to exactly one subject, and an
Opportunity's subject is the subject of every row supporting it.** There is one
namespace and one level in it.

The sharpest way to see the gap: **SROS already models GEOGRAPHIC scope on an
Opportunity and models no SUBJECT scope at all.** `MarketScope` is a closed union
of `GLOBAL | REGION | COUNTRY | MULTI_COUNTRY`, and the first Opportunity carries
`GLOBAL` with the limitation recorded on the row. Nothing comparable exists for
*product versus category versus market*.

Sharper still: **the dimension vocabulary already anticipated scoped
observation.** `MARKET_ACTIVITY` asks *"Is there evidence of transactions,
tenders or commercial exchange in the bounded scope observed?"* and
`ECONOMIC_VALUE` asks whether money moves *"in the bounded activity observed"*.
Those questions were written expecting an observation to carry its own bounded
scope. The packet model has nowhere to put it, so a TED observation's scope —
one CPV division — collapses into the packet's single subject, and the only way
to keep the claim honest is to keep the observation out.

So the two answers are:

- **A genuine source limitation.** No registered source publishes an identifier
  that both names Docker and carries commercial semantics. That is true
  independently of any architecture and would not be fixed by a scope model.
- **An architectural scope-model limitation, and it is the one that binds.**
  Commercial evidence in this portfolio exists at category and market scope. The
  engine cannot represent an Evidence row whose scope is broader than the
  Opportunity's subject, so it cannot use that evidence *at all* — not weakly,
  not with a caveat, not as context.

**Neither is solved by silently attaching broader Evidence to Docker.** A
container-tooling procurement statistic is not a statement about Docker, and
recording it as one would be the subject-identity weakening §9 forbids, arrived
at through the packet builder instead of through the registry.

A hierarchy — Docker → container development tooling → developer tooling — is
**not implemented here** and must not be. What this mission records is that the
question is architectural, that the vocabulary half of the system already assumes
an answer, and that the missing piece is a way for an Evidence row to say what
scope it observes and for a hypothesis to say which scopes it is entitled to
lean on.

---

## 11. What each candidate could and could not support

Collected in one place, because the second column is what stops a feasibility
document becoming a wish list. Every row's full list is in the JSON.

| Candidate | Could support | Could NOT support |
|---|---|---|
| `github` | COMPETITIVE_SUPPLY, FEASIBILITY_SIGNAL | that competitors are weak; that a crowded space is closed; market share; revenue; dissatisfaction; WTP; a buyer |
| `product-hunt` | COMPETITIVE_SUPPLY | demand; quality; satisfaction; commercial success; revenue |
| `reddit` | SOLUTION_DISSATISFACTION | that they would switch; that a complaint is representative; SOLUTION_GAP; WTP; any count of people |
| `ted-eu` *(category scope only)* | MARKET_ACTIVITY, BUYER_OR_BUDGET_EXISTENCE, ECONOMIC_VALUE | anything at `subject:docker` |
| `npm` / `pypi` *(category scope only)* | COMPETITIVE_SUPPLY, DISTRIBUTION_SIGNAL | paying customers; demand; buyer count; WTP |

---

## 12. Willingness to pay

**No registered source can support `WILLINGNESS_TO_PAY` at Docker grain, and none
can at any grain.** The answer is `NONE`, and it is not a gap in this review.

The taxonomy had already committed to the strict reading before this mission
asked. `WILLINGNESS_TO_PAY` asks *"Is there evidence a specific actor paid, or
committed to pay, for something addressing this need?"*, and its `never_means`
names the three near-misses verbatim:

> a listed price, which is an ask and not a transaction · a budget line, which is
> a capacity and not a decision · a public contract total, which includes options
> and renewals and may be lawfully withheld

So a pricing page would establish an **offered price** and stop there. A revenue
figure, if one existed anywhere in this portfolio, would be revenue for somebody
else's product and would say nothing about a proposed SROS intervention. The
closest thing the portfolio holds is a TED award total, and Mission 1.15.12
established that it includes options and renewals and is not what a buyer paid.

---

## 13. Buyer and budget existence

`ted-eu` and `usaspending` genuinely observe an identifiable buyer with authority
to award and a published value. That is `BUYER_OR_BUDGET_EXISTENCE` and
`ECONOMIC_VALUE` doing exactly what they were defined for.

**At a procurement classification grain, and that is not this subject.** The
mismatch is stated rather than smoothed: the buyer is real, the budget is real,
and what they bought is described by a category code that does not name products.
Attaching such Evidence to `subject:docker` would assert a subject identity
nobody established.

---

## 14. Qualitative priority

Ordinal only. No score, no weights. Ranked on subject-grain fit, epistemic value,
governance feasibility, implementation effort and external-synthesis feasibility.

- **PRIORITY_1 — none, unconditionally.** No source is worth acquiring for
  `subject:docker` in the architecture as it stands.
- **PRIORITY_1, CONDITIONAL on a multi-scope architecture — `ted-eu`.** If an
  Evidence row could declare a category scope, TED becomes the highest-value
  target in the portfolio by a distance: authorized, collected, normalized,
  extracted, and carrying three commercial dimensions. Which CPV division covers
  the relevant IT services is for that mission to establish from TED's own
  published vocabulary; this document does not assert one, in keeping with the
  collector's own rule that no CPV code is expanded.
- **PRIORITY_2 — `reddit`.** Best remaining grain-plus-dimension pair. Two
  independent blockers, one of which needs an inference capability that is
  separately unavailable.
- **PRIORITY_3 — `product-hunt`.** Right grain, one clean dimension, and a
  blocker only a company can lift.
- **NOT_RECOMMENDED — `github`**, despite having the best grain and the strongest
  dimension in the review. The restriction is decisive and purpose-based, and
  recommending a governance mission against it would spend a mission to
  re-derive a conclusion already on file.
- **NOT_RECOMMENDED — everything else**, for the reasons in the matrix.

---

## 15. Recommendation

**`NO_CURRENT_SOURCE_CAN_CLOSE_DOCKER_COMMERCIAL_DIMENSION`.**

No source is nominated for acquisition. Naming one would mean either recommending
a governance mission whose answer is already on file (GitHub, Product Hunt), or
acquiring a corpus nothing can read (Reddit), or attaching category evidence to a
product subject (TED).

The recommended next mission is therefore **Multi-Scope Opportunity Evidence
Architecture V1** — §16's alternative, and the one the evidence points at:

> Model the scope an Evidence row OBSERVES separately from the subject an
> Opportunity is ABOUT, so that `PRODUCT`, `CATEGORY`, `MARKET` and `GEOGRAPHY`
> can each be stated without claiming they are identical. Decide what a
> hypothesis may and may not conclude from evidence observed at a broader scope
> than its own subject — the answer is unlikely to be *nothing* and is certainly
> not *the same as its own scope*.

Only after that does an acquisition mission make sense, and TED is waiting for it
with every piece already built.

**If the architecture mission is declined**, the honest fallback is Reliability /
Scoring Eligibility Foundation: the Docker packet's eight rows are all
`NON_SCORABLE` for want of a reviewed reliability, and improving what the system
can conclude from the evidence it HAS does not depend on acquiring more.
Commercial evidence acquisition stays recorded as a longer-term portfolio gap.
