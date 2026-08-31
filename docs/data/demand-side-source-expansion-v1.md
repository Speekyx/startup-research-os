# Demand-Side Source Expansion V1

**Authoritative.** Mission 1.15. What was reviewed, what was retrieved, what
changed, and what could not be reached.

Companions: `demand-side-source-coverage-v1.md` (the gap, family by family),
`demand-side-source-priority-v1.md` (what to do next),
`source-review-guide.md` (how a review is conducted).

---

## 0. What this round was for

Mission 1.14 concluded that reliability governance had made the existing
evidence honestly scorable-in-principle, and that the binding constraint was
elsewhere: **the portfolio has no evidence about people.** Seven claims about
what two publications reported cannot become evidence of demand however well
they are assessed.

So this round asked one question of every candidate:

> Can we lawfully collect something that observes what people want, struggle
> with, buy, compare or repeatedly use?

**Nine sources examined. Two verdicts changed. Two sources registered. Zero
approvals.**

## 1. What changed

| Source | Before | After | Cause |
|--------|--------|-------|-------|
| `pinterest` | REQUIRES_REVIEW v1 | **RESTRICTED v2** | Developer guidelines retrieved |
| `hacker-news` | REQUIRES_REVIEW v2 | **RESTRICTED v3** | Governing Y Combinator Terms retrieved |
| `bluesky` | REQUIRES_REVIEW v1 | REQUIRES_REVIEW **v2** | Terms re-retrieved; the open question narrowed |
| `ted-eu` | — | **REQUIRES_REVIEW v1** (new) | Registered |
| `usaspending` | — | **REQUIRES_REVIEW v1** (new) | Registered |

No review was rewritten. Every superseded version stays readable, which is what
makes the change legible rather than merely applied.

## 2. Pinterest — the best desire hypothesis, closed

Mission 1.7 called Pinterest *"the strongest candidate in the catalog for DESIRE
signals specifically — saving something is an expression of want with no
complaint and no purchase attached."* It also recorded that the developer terms
could not be retrieved and that every activity was therefore `NOT_ASSESSED`.

This round retrieved them, from `policy.pinterest.com/en/developer-guidelines` —
a first-party Pinterest policy host, reached directly. `developers.pinterest.com`
again returned navigation and footer only.

**Five independently disqualifying findings:**

| Finding | Consequence |
|---------|-------------|
| *"you may not store any information accessed through any Pinterest Materials including the API. Instead, call the API each time you need to access information."* | This engine's architecture **is** storage. RawRecords preserve what arrived; that is the first layer |
| *"Using any automated means or form of scraping or data extraction to access information from Pinterest, except as expressly permitted"* | Automated collection is a listed prohibited use |
| *"Using any Pinterest Materials to train, fine-tune, or otherwise improve or develop any artificial intelligence or machine learning models, except as expressly permitted"* | Model training prohibited |
| *"Don't use information from our API except to serve and evaluate the performance of ads on Pinterest."* | The permitted purpose is advertising **on Pinterest**. Our assessed use is not that |
| *"Attempting or claiming to provide platform insights, benchmarking, or competitor research features unless you have explicit written authorization from Pinterest."* | **This names the product.** Startup Research OS is a competitor-research feature |

**RESTRICTED rather than PROHIBITED**, because Pinterest itself describes a
route: explicit written authorization. That is a commercial negotiation and an
external action, not something a reviewer can resolve by reading further.

The first clause alone would settle it. A source that forbids storing what its
API returns cannot feed a pipeline whose first layer preserves what arrived.

## 3. Hacker News — technical openness, governing prohibition

The clearest demonstration in the catalog of *technical accessibility is not
permission*.

**What the API says.** `github.com/HackerNews/API` documents a public
Firebase-backed API, no key, and states: *"There is currently no rate limit."*
By every engineering measure this is an invitation. The repository carries an
MIT licence — **on the repository**, which contains documentation, not Hacker
News content.

**What the governing terms say.** Y Combinator's Terms of Use bring
`news.ycombinator.com` explicitly into scope, and then:

> *"you will not engage in or use any data mining, robots, scraping or similar
> data gathering or extraction methods"*

> *"you agree not to display, distribute, license, perform, publish, reproduce,
> duplicate, copy, create derivative works from, modify, sell, resell, exploit,
> transfer or upload for any commercial purposes, any portion of the Site"*

Both halves of the assessed use are named: automated collection, and commercial
derivative work. **RESTRICTED (v3).**

Mission 1.7's v2 recorded `REQUIRES_REVIEW` because the governing terms had not
been retrieved. They have been, and they answer the question against us. That is
the review process working: a source moves off `REQUIRES_REVIEW` when evidence
arrives, in whichever direction the evidence points.

## 4. Bluesky — the question got smaller, not the answer better

The verdict does not change. What changed is that v1's first open question is now
answered, and the remaining one is a single retrievable document.

**v1 asked:** does Bluesky publish a developer or API terms document separate
from the user Terms of Service?

**Answer: yes.** Bluesky's own documentation domain names *Bluesky Developer
Guidelines* — the guidelines developers who federate apps or services on the AT
Protocol must follow to communicate with Bluesky services.

**And it could not be retrieved.** `docs.bsky.app/docs/support/developer-guidelines`
returns HTTP 301 to `bsky.network/docs/support/developer-guidelines`, and that
URL returned an empty body on 2026-08-31. The documentation root at
`bsky.network` links to no terms, guidelines or legal document at all.

**No mirror, cache or third-party copy was consulted.** A retrieval failure
leaves a question unresolved; it does not license a substitute (§18).

The Terms of Service were re-retrieved at their current version — updated
effective 15 September 2025, after v1 was written — and remain silent, for a
third party reading public records, on all ten activities that matter. The only
thing they address is deletion, and only to say that because of the AT Protocol's
decentralised nature Bluesky cannot control other services.

Bluesky stays the sharpest illustration in the catalog of the distance between
*we can reach this trivially* and *we may use it*. The distance is now one
document wide.

## 5. Reddit and Stack Exchange — unreachable, unresolved

Both hosts refused to serve to this environment:

| Source | URLs attempted | Outcome |
|--------|----------------|---------|
| `reddit` | `redditinc.com/policies/data-api-terms`, `www.redditinc.com/policies/data-api-terms` | Host unreachable |
| `stack-exchange` | `stackoverflow.com/legal/api-terms-of-use`, `api.stackexchange.com/docs` | Host unreachable |

**No bypass was attempted.** No mirror, no cached copy, no alternative page read
in order to infer the missing terms, no community summary treated as evidence.
Both verdicts stand at `REQUIRES_REVIEW` exactly as before, and both reviews are
**unchanged** — a failed retrieval is not new evidence and does not justify a new
version.

This is worth stating plainly because both are high-value: Reddit is probably the
single richest pain and product-comparison corpus in existence, and Stack
Exchange is the clearest record of developer difficulty anywhere. Neither is
closer to usable than it was.

## 6. Willingness to pay — the first lawful route

WTP had **zero** registered candidates. It now has two, and both carry a
different evidence class from anything the portfolio has held.

```text
LISTED_PRICE    what somebody asked for      -- a pricing page
TRANSACTION     what somebody paid           -- a contract award notice
```

### TED (Tenders Electronic Daily) — `REQUIRES_REVIEW`, five of six granted

The EU's official public procurement journal. Contract award notices record what
a public body bought, from which supplier, at what value.

The legal notice at `ted.europa.eu/en/legal-notice` grants, in one sentence:

> *"Unless otherwise noted, the procurement notices published in the Supplement
> to the Official Journal of the European Union can be freely reused, for
> commercial or non-commercial purposes."*

That is a **grant**, not an absence of prohibition — the distinction Mission 1.8
made the eligibility gate turn on. Editorial content is CC BY 4.0 with attribution
and indication of changes; metadata is CC0 1.0. Bulk XML packages are published
daily and monthly, downloadable without signing in, alongside a documented
read-only search API.

Five of the six load-bearing activities are positively permitted:
`automated_access`, `api_use`, `commercial_use`, `storage`, `derived_analytics`.

**`model_processing` is not addressed**, and under rule 8 that blocks whatever
the other five say. The legal notice names machine learning, text mining,
training and inference nowhere.

**Recording it as anything else would be the narrowing Mission 1.8 forbids.**
This engine's product includes LLM processing — the gateway exists, the reasoning
rules govern it — and describing a smaller product to rescue a source yields a
permission for a product we are not building.

Two conditions the review records rather than defers:

- **Personal data.** Notices publish contact names, addresses, emails, telephone
  and fax numbers of contracting authorities and successful tenderers. A
  minimisation profile must discard the entire contact block: the engine needs
  the award value, the organisation names, the CPV classification and the dates,
  and needs no natural person's contact details for any assessed purpose.
- **Authenticity.** Only electronically signed notices in the Official Journal
  Supplement are authentic; online documents are *"not necessarily exact
  reproductions"*. Any claim derived from TED must be attributed to TED's
  published notice rather than asserted as the authentic award.

### USAspending — `REQUIRES_REVIEW`, no licence retrievable

US federal contract and grant awards. The same transaction class, and a weaker
evidential position: three first-party locations were tried and none carried a
licence.

- `api.usaspending.gov/` — states the data *"is open source and provided to the
  public as part of the DATA Act"*, with no licence, terms, rate limit or
  statement on commercial use, storage, redistribution, analytics or ML.
- `usaspending.gov/about` — returned no page content. Retrieval failure.
- The operating agency's own repository README — repeats the DATA Act sentence
  and states no licence, terms, attribution requirement or rate limit.

**The DATA Act sentence establishes that the data must be publicly
*accessible*.** That is a statement about publication, not a grant of reuse
rights to a commercial product — the same distinction that keeps Bluesky's
public firehose from being permission.

A reviewer might reasonably expect US federal works to be uncopyrighted. That is
a general legal principle, not a source document, and **no verdict may rest on
one** (§16).

## 7. What was not pursued, and why

| Family | Position |
|--------|----------|
| **Pricing** | No lawful structured source found. Every candidate carrying listed prices — the app stores, Product Hunt — is `RESTRICTED`, and none was re-opened because no new first-party grant was found |
| **Retention** | No candidate exists, and the obstacle is structural rather than legal: retention needs the same subject observed twice, and everything in the portfolio is an aggregate or a one-shot public record. **No proxy is proposed**, because a proxy nobody can validate is worse than an acknowledged gap |
| `google-trends`, `twitch`, `huggingface`, `discord`, `x-twitter` | Not reviewed this round. Each would need its own retrieval, and the two priority candidates plus the WTP gap consumed the round. None is closer or further than before |

Existing `RESTRICTED` and `PROHIBITED` verdicts were **not** re-opened. A
different endpoint under the same governing terms does not change a policy
restriction, and no new first-party grant was found for any of them (§29).

## 8. Retrieval failures, in full

Recorded because an unresolved question must stay visible as unresolved.

| Document | Outcome |
|----------|---------|
| Bluesky Developer Guidelines | 301 to `bsky.network`, empty body |
| `developers.pinterest.com/terms/` | Navigation and footer only; resolved via `policy.pinterest.com` |
| `stackoverflow.com/legal/api-terms-of-use` | Host unreachable |
| `api.stackexchange.com/docs` | Host unreachable |
| `redditinc.com/policies/data-api-terms` | Host unreachable |
| `usaspending.gov/about` | No page content |
| `data.europa.eu` TED dataset page | Title only |
| `ted.europa.eu/en/simap/reuse-of-ted-data` | HTTP 404; resolved via the legal notice |

**No bot protection was encountered, and no bypass of any kind was attempted.**
No mirror, cached copy, alternative page, spoofed credential or community summary
was used to establish any finding.

Search engines were used to *locate* documents — the Bluesky developer
guidelines, the Pinterest policy host, the TED legal notice. Every verdict rests
on a document that was then retrieved directly from a first-party host, and one
search result carrying substantive-looking Pinterest quotes was **not** treated
as evidence until the document itself was fetched.

## 9. What this round did to the portfolio

It made it smaller and more accurate.

Two families that looked open were closed on evidence. One family that had
nothing gained two candidates. Nothing became usable.

That is the correct outcome when the terms say what they say, and it is worth
more than an approval that would not survive being read. The registry exists so
that the difference between *we hope* and *we may* is visible, and this round
mostly converted hope into knowledge.
