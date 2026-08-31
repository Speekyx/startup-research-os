# Mission 1.15 — Demand-Side Source Portfolio Expansion V1

**Date:** 2026-08-31 · **Branch:** `sprint-1/mission-1.15` · **Scope:** source
discovery and policy review.

**Nine sources examined. Two verdicts changed. Two sources registered. Zero
approvals, zero collectors, zero rows collected.**

Willingness to pay went from **no registered candidate at all** to two, both
carrying transaction-class evidence, one blocked on a single named activity.

---

## 0. What this round found

The portfolio has been strong on published aggregate context and empty on
individual behaviour since Mission 1.7. This round tested whether that was a
gap in *review effort* or a gap in *what is lawfully available*.

**It is mostly the second.** The platforms that observe people — social,
discussion, app stores, discovery — are precisely the platforms whose governing
terms most directly prohibit automated commercial collection. Two of them said
so explicitly this round, in documents nobody had retrieved before.

The one genuinely new opening came from a direction the portfolio had never
looked: **public procurement**. A contract award notice records what a buyer
paid a named supplier, which is a `TRANSACTION` and not a `LISTED_PRICE`.

---

# The questions (§43)

## What demand-side evidence families are currently missing?

Six of eight have no approving source; two have no registered candidate at all.
Counts read from `registry.source_signal_coverage` joined to the current review.

| Family | Registered | Approving | Eligible |
|--------|-----------:|----------:|---------:|
| Pain | 9 | **0** | 0 |
| Desire | 5 | **0** | 0 |
| Willingness to pay | 2 *(new, transaction-class)* | **0** | 0 |
| Pricing | **0** | 0 | 0 |
| Competition | 3 | **0** | 0 |
| Distribution | 10 | 1 | 0 |
| Retention | **0** | 0 | 0 |
| User behaviour | 5 | 1 | 0 |

Both `1`s are weaker than the digit suggests. Distribution's is `openalex`, whose
`discovery` coverage is scholarly-record discovery rather than a marketing
channel. User behaviour's is `gdelt`, whose `social` coverage is news-corpus
activity — journalists publishing, not users acting.

**Read strictly, no approving source observes an individual doing anything.**

Willingness to pay is counted separately from the `commercial` signal family on
purpose. That family has 13 registered sources and four approving —
`world-bank`, `eurostat`, `fred`, `gdelt` — all of which publish macroeconomic
aggregates or news coverage. Counting them as willingness-to-pay evidence would
be exactly the conflation §12 exists to prevent. The 2 above are the
transaction-class candidates only.

## Which existing registered sources were re-reviewed?

Three: `pinterest` (v1 → v2), `hacker-news` (v2 → v3), `bluesky` (v1 → v2).

## Which new sources were investigated?

Public procurement as a family, reaching `ted-eu` (EU Tenders Electronic Daily)
and `usaspending` (US federal awards). Both registered.

## Which new sources were registered?

`ted-eu` and `usaspending`, both `REQUIRES_REVIEW`, under a new
`public_procurement` source family (migration 0020).

The family is new deliberately. Filing them under `economic_data` would have put
them beside World Bank and Eurostat, which publish statistics *about* economies
— and made the coverage report say the portfolio has had commercial evidence
since Mission 1.5, which it has not.

## Did any verdict change?

Two.

| Source | Before | After |
|--------|--------|-------|
| `pinterest` | REQUIRES_REVIEW | **RESTRICTED** |
| `hacker-news` | REQUIRES_REVIEW | **RESTRICTED** |

`bluesky` kept its verdict and gained a version, because the *question* changed
materially even though the answer did not.

## What first-party evidence caused each change?

**Pinterest** — `policy.pinterest.com/en/developer-guidelines`, retrieved
2026-08-31. Five independently disqualifying findings:

> *"you may not store any information accessed through any Pinterest Materials
> including the API. Instead, call the API each time you need to access
> information."*

> *"Using any automated means or form of scraping or data extraction to access
> information from Pinterest, except as expressly permitted"*

> *"Using any Pinterest Materials to train, fine-tune, or otherwise improve or
> develop any artificial intelligence or machine learning models"*

> *"Don't use information from our API except to serve and evaluate the
> performance of ads on Pinterest."*

> *"Attempting or claiming to provide platform insights, benchmarking, or
> competitor research features unless you have explicit written authorization
> from Pinterest."*

The first alone settles it: this engine's first layer preserves what arrived. The
last one names the product.

**Hacker News** — `ycombinator.com/legal/`, retrieved 2026-08-31. The Terms bring
`news.ycombinator.com` into scope explicitly, then:

> *"you will not engage in or use any data mining, robots, scraping or similar
> data gathering or extraction methods"*

> *"you agree not to display, distribute, license, perform, publish, reproduce,
> duplicate, copy, create derivative works from, modify, sell, resell, exploit,
> transfer or upload for any commercial purposes, any portion of the Site"*

Both halves of the assessed use are named.

## Were any terms inaccessible?

Yes — eight retrievals failed, and each is recorded on the review it belongs to.

| Document | Outcome |
|----------|---------|
| Bluesky Developer Guidelines | 301 to `bsky.network`, **empty body** |
| `stackoverflow.com/legal/api-terms-of-use` | Host unreachable |
| `api.stackexchange.com/docs` | Host unreachable |
| `redditinc.com/policies/data-api-terms` (and `www.`) | Host unreachable |
| `developers.pinterest.com/terms/` | Navigation and footer only |
| `usaspending.gov/about` | No page content |
| `data.europa.eu` TED dataset page | Title only |
| `ted.europa.eu/en/simap/reuse-of-ted-data` | HTTP 404 |

Two of these were resolved by fetching the same document from a different
**first-party** host — Pinterest's policy site, TED's legal notice. That is not
a mirror; it is the publisher's own document at its own address.

## Was any bot protection encountered?

**No.** The failures were redirects to empty bodies, hosts this environment
cannot reach, and JavaScript-rendered pages. No CAPTCHA, no interstitial, no
rate-limit block.

## Was any bypass attempted?

**No.** No mirror, no cached copy, no archive, no alternative page read to infer
missing terms, no spoofed credential, no login.

One case is worth naming because it was the temptation. A search result for
Pinterest returned substantive-looking quotes from the developer terms — the
storage clause among them. **That was not treated as evidence.** The verdict
waited until the document itself was fetched from `policy.pinterest.com`. Search
engines locate documents; they do not establish permission.

## How many sources are registered now?

**29**, up from 27.

## What is the exact verdict distribution?

| Verdict | Count |
|---------|------:|
| `REQUIRES_REVIEW` | 13 |
| `RESTRICTED` | **8** *(was 6)* |
| `APPROVED_WITH_CONDITIONS` | 5 |
| `PROHIBITED` | 3 |

## Which sources are collector-eligible?

**None**, for any demand-side family. `world-bank` is the only source that is
eligible, resourced and implemented — and it covers aggregate economic context,
not demand.

## Which source can now provide PAIN?

**None.** Nine registered — `apple-app-store`, `bluesky`, `github`,
`google-play`, `hacker-news`, `reddit`, `stack-exchange`, `steam`, `ted-eu` —
zero approving. The strongest are `reddit` and `stack-exchange`, both unreachable
this round and both unmoved.

## Which can provide DESIRE?

**None.** Five registered — `apple-app-store`, `google-play`, `product-hunt`,
`reddit`, `steam` — and this round *removed* the best hope: Pinterest was the
catalog's strongest desire candidate since Mission 1.7 and is now `RESTRICTED` on
evidence.

## Which can provide WTP?

**None yet — but two candidates now exist where there were none.** `ted-eu` and
`usaspending`, both `REQUIRES_REVIEW`.

## Which can provide PRICING?

**None, and no candidate exists.** Every source carrying listed prices — the app
stores, Product Hunt — is `RESTRICTED`. `ted-eu` carries award values, which is a
price *paid for a specific contract* rather than a published catalogue price:
related, and a different family.

## Which can provide COMPETITION?

**None approving.** Three registered — `steam`, `ted-eu` and `usaspending` — all
blocked. `product-hunt`, the natural fit, is `RESTRICTED`.

`gdelt` is approving and is **not** counted: it records no `competition`
coverage, and reading company mentions in news as competitive position is exactly
the interpretive leap the claim contract prevents.

## Which can provide DISTRIBUTION?

**None eligible.** Ten registered, one approving — `openalex`, whose `discovery`
coverage is scholarly-record discovery. **Attention is not acquisition
feasibility**: nothing here says a channel can be bought into at a knowable
cost.

## Which can provide RETENTION?

**None, and no candidate exists.** The obstacle is structural rather than legal:
retention needs the same subject observed twice, and everything in the portfolio
is an aggregate or a one-shot public record. A count at two times is two counts.

**No proxy is proposed.** A proxy nobody can validate is worse than an
acknowledged gap.

## Which can provide USER_BEHAVIOUR?

**Nothing that observes an individual.** Five registered — `bluesky`, `gdelt`,
`hacker-news`, `reddit`, `steam` — and the one approving entry is `gdelt`, whose
`social` coverage is news-corpus activity. Every source that observes a person is
`RESTRICTED` or `REQUIRES_REVIEW`.

## Is Bluesky usable?

**No — outcome C.** `REQUIRES_REVIEW` v2, blocked on one named document.

The user Terms were re-retrieved at their current version (updated effective
15 September 2025, after v1) and remain silent, for a third party reading public
records, on all ten activities that matter. The only thing they address is
deletion.

**v1's first open question is now answered: a developer terms document does
exist.** Bluesky's own documentation domain names *Bluesky Developer Guidelines*.
It returned an empty body. The question went from *four unknowns* to *one
retrievable document* — recorded as H-33.

## Is Pinterest usable?

**No — outcome D.** `RESTRICTED`. The use is incompatible with the assessed use
case on four counts, and the fifth names competitor research specifically.
`RESTRICTED` rather than `PROHIBITED` because Pinterest describes a route:
explicit written authorization. That is a commercial negotiation, not review
work.

## Is Reddit usable?

**Unchanged and unknown — outcome C.** Both `redditinc.com` addresses were
unreachable. Its review gained **no version**, because a failed retrieval is not
evidence. Reddit is probably the single richest pain and product-comparison
corpus in existence, and it is exactly as far away as it was.

## Is Hacker News usable?

**No — outcome D.** `RESTRICTED` v3. The clearest demonstration in the catalog
that technical accessibility is not permission: a documented API, no key, *"There
is currently no rate limit"* — and governing terms that prohibit both the
collection method and the commercial output.

The MIT licence on the API's GitHub repository covers **that repository**, which
contains documentation, not Hacker News content.

## Is Stack Exchange usable?

**Unchanged and unknown — outcome C.** Both hosts unreachable, no version
recorded.

## Is Google Trends usable?

**Not reviewed this round — outcome C, unchanged.** Its v3 review records the
official API as alpha-limited by application with no published terms (H-6). The
two priority candidates plus the WTP gap consumed the round.

## Are there lawful alternatives for blocked platforms?

**For willingness to pay, yes — and that is this round's one real finding.**
Public procurement is a lawful, published, bulk-downloadable route to transaction
evidence, and no blocked platform was needed to reach it.

**For pain, desire, retention and user behaviour, no alternative was found.**
Those families need individual behaviour, and the sources that observe
individuals are the ones with restrictive terms. There is no open-data
substitute for a person describing their problem.

## Were personal-data risks reviewed?

Yes, per source.

`ted-eu` is the notable one: notices publish contact names, addresses, emails,
telephone and fax numbers of contracting authorities and successful tenderers.
That is exactly the class §24 says not to collect, in a source that is otherwise
the round's best candidate. Recorded as `IDENTIFIABLE` with a mandatory
minimisation condition.

## Were minimisation requirements defined?

Yes, for `ted-eu`, as a review condition rather than a later note:

> the engine needs the award value, the buyer and supplier organisation names,
> the CPV classification and the dates, and needs **no natural person's contact
> details** for any assessed purpose — the entire contact block is discarded.

A second condition records that only electronically signed notices in the
Official Journal Supplement are authentic, so any claim must be attributed to
TED's published notice rather than asserted as the authentic award.

## Did any source become newly collector-ready?

**No.** Nothing became approving, so nothing became eligible, so nothing became
ready. `sros-source readiness` reports every source except `world-bank` as
failing the eligibility gate.

## Were any collectors implemented?

**No.** Tests assert that neither new source appears in `IMPLEMENTED_COLLECTORS`
or `IMPLEMENTED_NORMALIZERS`.

## Was any external research data collected?

**No.** Documents were retrieved for *review*; none was stored as a RawRecord and
none entered the pipeline. Reading terms of service is not acquisition, and no
Claim was generated from any of it.

## Did the existing 12 / 12 / 7 / 7 / 7 remain unchanged?

**Yes.**

| Table | Count |
|-------|------:|
| `acquisition.raw_records` | 12 |
| `acquisition.normalized_records` | 12 |
| `nlp.signals` | 7 |
| `research.claims` | 7 |
| `research.claim_revisions` | 7 |
| `scoring.evidence` | 7 |

The pytest post-suite check reports the database unchanged across 24 tenant
tables and 16 global tables.

## Were any reliability assessments created?

**No.** `epistemic.reliability_assessments` = 0. Source review asks *may we use
this*; reliability review asks *how dependable is this measurement for this
proposition*. Different processes, deliberately not mixed.

## Were any Opportunities created?

**No.** 0.

## Were embeddings generated?

**No.** 0. D-12 stays open.

## Was scoring performed?

**No.** No EvidenceScore, no OpportunityScore, no source score. The priority
ranking is ordinal buckets with stated reasoning — P0/P1/P2 — and deliberately
carries no numbers.

## Which ONE source should Mission 1.15.1 implement first, and why?

**None — and that is the recommendation.**

Mission 1.15.1 should **retrieve the one document standing between `ted-eu` and
an approving verdict**, not build a collector.

The question is narrow: does the Publications Office's reuse decision, or another
first-party instrument, address machine-learning processing of reused notices?
(H-34.)

| If | Then |
|----|------|
| It grants ML processing | `ted-eu` becomes `APPROVED_WITH_CONDITIONS`. The portfolio has its first WTP source and a collector mission follows immediately |
| It prohibits it | `ted-eu` is `RESTRICTED` and the largest gap is confirmed closed by that route. Knowing costs one retrieval |
| It is silent | The verdict stands and the question routes to legal review — a named action rather than an open unknown |

**Why not build a collector anyway.** Not because a rule forbids it: the
eligibility gate would refuse the job, the authorization context would refuse to
construct, and the collector would be code that cannot run. That is the gate
working.

**Why `ted-eu` and not something else.** It is the only source in the catalog
with five of six load-bearing activities granted on retrieved evidence. It would
be the first source for a family that had no candidate at all a week ago. Its
access route is bulk XML with no sign-in. And its blocker is the cheapest kind
there is — a document to fetch, not a negotiation to open.

---

## 1. The outcome categories (§40)

| Source | Outcome |
|--------|---------|
| `ted-eu` | **C** — REQUIRES_REVIEW, one named missing grant (H-34) |
| `bluesky` | **C** — REQUIRES_REVIEW, one named missing document (H-33) |
| `usaspending` | **C** — REQUIRES_REVIEW, no licence retrievable (H-35) |
| `reddit` | **C** — unchanged; hosts unreachable |
| `stack-exchange` | **C** — unchanged; hosts unreachable |
| `google-trends` | **C** — unchanged; not reviewed this round |
| `pinterest` | **D** — RESTRICTED; use incompatible |
| `hacker-news` | **D** — RESTRICTED; use incompatible |

**No source reached A or B, and none was forced toward one.**

## 2. What this round is worth

It made the portfolio smaller and more accurate.

Two families that looked open were closed on evidence. One family that had
nothing gained two candidates. Nothing became usable.

§39 says a correct review concluding that all candidates remain blocked is
preferable to a false approval. This round is that, with one addition: the
*shape* of the blockage is now known. Pain and desire are blocked by platform
terms that will not change without commercial agreements. Willingness to pay is
blocked by one unanswered question about one document. Retention is blocked by
physics — nothing in the portfolio observes the same subject twice.

Those are three different problems and they were one undifferentiated gap before.

## 3. Gates

| Gate | Result |
|------|--------|
| Zero-dependency suites | 515 tests, 8 packages, pass |
| Pytest suites | 7 packages, pass; database unchanged across 24 tenant and 16 global tables |
| `validate_source_registry` | pass — **29 sources, 40 evidence records**, 0 warnings |
| `validate_schema` | pass — 9 invariant groups, 40 tables |
| `validate_claims` · `validate_signals` · `validate_normalization` | pass |
| `validate_compliance_capabilities` · `validate_evidence_aggregation` | pass |
| Generated documents `--check` | catalog, review results and signal coverage all current |
| New tests | 37, over the recorded catalog; **none contacts a platform** |

## 4. Open questions added

| Id | Question |
|----|----------|
| **H-33** | Bluesky publishes developer guidelines that cannot be retrieved |
| **H-34** | Does the EU's reuse framework address ML processing of TED notices? *(the P0 blocker)* |
| **H-35** | USAspending publishes no licence or terms document |

**H-5 closed** — whether Hacker News's API authorises commercial derived
analytics. The Terms make it moot: the collection method is prohibited whatever
the API's publication implies about the output.
