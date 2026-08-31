# Demand-Side Source Coverage V1

**Authoritative.** Mission 1.15 §21. The eight business evidence families the
product actually needs, against the registry as it stands.

Read with `demand-side-source-expansion-v1.md` (what was reviewed and why) and
`demand-side-source-priority-v1.md` (what to do next).

---

## 0. What this document is for

`source-signal-coverage-v1.md` is generated from the catalog and answers *what
could each source expose*. This one answers a narrower and more uncomfortable
question:

> **For each thing the product must eventually know about people and markets,
> how many sources may we lawfully use today?**

The two are different because **coverage is potential and has never been
permission** (ADR-017). A source that could provide the best pain evidence in
the catalog contributes nothing if we may not collect it.

Four columns, and only the last one counts for anything:

| Column | Means |
|--------|-------|
| **Registered** | The catalog knows the source could provide this family |
| **Approving** | Its current review is `APPROVED` or `APPROVED_WITH_CONDITIONS` |
| **Eligible** | It passes the eligibility gate — approving *and* every condition satisfied |
| **Implemented** | A collector exists |

## 1. How a business family maps to the registry

The registry records **signal families** (`problem`, `desire`, `commercial`, …).
This document is about **business evidence families**, and the two are not the
same vocabulary. The mapping is stated here so the counts below can be audited
rather than trusted:

| Business family | Signal families counted |
|-----------------|-------------------------|
| Pain | `problem` |
| Desire | `desire` |
| Willingness to pay | **none — see §3** |
| Pricing | **none exists** |
| Competition | `competition` |
| Distribution | `discovery` |
| Retention | **none exists** |
| User behaviour | `social`, `community` |

**Willingness to pay has no signal family, and that is the finding rather than an
oversight.** The nearest is `commercial`, and it is much broader: 13 registered
sources carry it, four of them approving — `world-bank`, `eurostat`, `fred`,
`gdelt`. Those four publish macroeconomic aggregates and news coverage. Counting
them as willingness-to-pay evidence would be exactly the conflation §12 of the
mission exists to prevent.

## 2. The table

Registry state at 2026-08-31, 29 sources. Read from
`registry.source_signal_coverage` joined to the current review, not written by
hand.

| Business family | Registered | Approving | Eligible | Implemented |
|-----------------|-----------:|----------:|---------:|------------:|
| **Pain** | 9 | **0** | 0 | 0 |
| **Desire** | 5 | **0** | 0 | 0 |
| **Willingness to pay** | 2 *(transaction-class)* | **0** | 0 | 0 |
| **Pricing** | **0** | 0 | 0 | 0 |
| **Competition** | 3 | **0** | 0 | 0 |
| **Distribution** | 10 | 1 | 0 | 0 |
| **Retention** | **0** | 0 | 0 | 0 |
| **User behaviour** | 5 | 1 | 0 | 0 |

**Six of eight families have no approving source. Two have no registered
candidate at all. Nothing is eligible or implemented anywhere.**

The two `1`s are worth naming, because both are weaker than the digit suggests:

- **Distribution** — `openalex`, whose `discovery` coverage is scholarly record
  discovery. That is not a marketing channel, and **attention is not acquisition
  feasibility** (§14).
- **User behaviour** — `gdelt`, whose `social` coverage is news-corpus activity.
  Nobody's behaviour is observed; journalists publishing is not users acting.

Read strictly, **no approving source observes an individual doing anything.**

## 3. Family by family

### Pain — 9 registered, 0 approving

Sources whose records state a difficulty in a user's own words.

`apple-app-store`, `bluesky`, `github`, `google-play`, `hacker-news`, `reddit`,
`stack-exchange`, `steam`, `ted-eu`.

| Blocker | Sources |
|---------|---------|
| **RESTRICTED** — use incompatible | `apple-app-store`, `github`, `google-play`, `hacker-news` *(v3, this mission)*, `steam` |
| **REQUIRES_REVIEW** — terms unretrievable | `reddit`, `stack-exchange` |
| **REQUIRES_REVIEW** — terms silent | `bluesky` *(v2, this mission)* |
| **REQUIRES_REVIEW** — organisational need, never individual pain | `ted-eu` |

**This is the family the product most needs and the one furthest from having
anything.** Every strong candidate is a discussion or review platform, and those
are exactly where governing terms are most restrictive.

### Desire — 5 registered, 0 approving

Saving, wishlisting, upvoting, following — wanting something, with no complaint
and no purchase attached.

`apple-app-store`, `google-play`, `product-hunt`, `reddit`, `steam` — all
`RESTRICTED` except `reddit`, whose terms could not be retrieved.

**Mission 1.15 closed this family's best hypothesis.** Pinterest was called the
catalog's strongest desire candidate in Mission 1.7 and is now `RESTRICTED` on
retrieved evidence. It does not appear in the count above because its catalog
entry records `discovery` and `social` coverage rather than `desire` — the
hypothesis was about what Pinterest *could* have provided, and the review closed
it before the coverage was ever recorded.

### Willingness to pay — 2 transaction-class candidates, 0 approving

**The family Mission 1.14 named as the largest gap.** It had no candidate able to
evidence a payment before this round.

| Source | Verdict | Evidence class | Blocker |
|--------|---------|----------------|---------|
| `ted-eu` | REQUIRES_REVIEW *(v5)* | **TRANSACTION** | H-34 **closed PERMITTED**; blocked solely by the sui generis database right. Mission 1.15.3 found the dataset-level licence — `COM_REUSE` on every distribution including bulk XML — and it resolves by `skos:exactMatch` to the same Decision, which does not address database rights. Split into **H-36A** (does the right subsist? not established) and **H-36B** (is it granted? not addressed). A clarification request is written and unsent |
| `usaspending` | REQUIRES_REVIEW *(new)* | **TRANSACTION** | No licence or terms document retrievable |

```text
LISTED_PRICE     what somebody asked for       -- a pricing page
TRANSACTION      what somebody paid            -- a contract award notice
```

The distinction is the whole point of §12. Every previous candidate could only
ever have evidenced the first.

**What they cannot evidence, stated plainly.** Both are *public-sector* buying
above publication thresholds. Neither says anything about consumers, about SaaS
pricing, about individuals, or about small purchases. They would be the
portfolio's first WTP evidence and would still not be evidence of consumer
willingness to pay.

### Pricing — 0 registered, 0 approving

**No candidate exists.** A source publishing what products cost, lawfully and in
a structured form, has not been found. Every source carrying listed prices — the
app stores, Product Hunt — is `RESTRICTED`.

`ted-eu` carries award values, which is a price paid for a specific contract
rather than a published catalogue price. Related, and a different family.

### Competition — 3 registered, 0 approving

`steam`, `ted-eu`, `usaspending`.

`gdelt` is approving and is **not** counted: it records no `competition`
coverage, and reading company mentions in news as competitive position would be
the interpretive leap the claim contract exists to prevent.

`product-hunt` — launches and categories, the natural fit — is `RESTRICTED`.

### Distribution — 10 registered, 1 approving

`bluesky`, `google-trends`, `hacker-news`, `huggingface`, `npm-registry`,
`openalex`, `product-hunt`, `pypi`, `reddit`, `wikimedia-pageviews`.

The one approving entry is `openalex`, whose `discovery` coverage is scholarly
records. **Attention is not acquisition feasibility**: nothing here says a
channel can be bought into at a knowable cost.

### Retention — 0 registered, 0 approving

**No candidate exists, and the obstacle is structural rather than legal.**

Retention needs *the same subject observed twice*. Everything in the portfolio is
either an aggregate (a pageview count, an indicator value, a term frequency) or a
one-shot public record (a post, a notice). A count at two times is two counts. A
topic staying visible is not retention either.

Any future proxy must be labelled `PROXY` and kept separate from direct
retention, per §13. **None is proposed here**, because a proxy nobody can
validate is worse than an acknowledged gap.

### User behaviour — 5 registered, 1 approving

`bluesky`, `gdelt`, `hacker-news`, `reddit`, `steam`.

The approving one is `gdelt`, and its `social` coverage is news-corpus activity —
journalists publishing, not users acting. Every source that observes an
individual is `RESTRICTED` or `REQUIRES_REVIEW`.

## 3. What the approving five actually cover

The five approving sources — `world-bank`, `eurostat`, `fred`, `gdelt`,
`openalex` — cover:

| Family | Approving sources |
|--------|-------------------|
| `trend` | 5 |
| `commercial` | 4 |
| `curiosity` | 2 |
| `community`, `developer_activity`, `discovery`, `learning`, `social` | 1 each |

Read against §2, the shape is unambiguous: **the portfolio is complete on
published aggregate context and empty on individual behaviour.** Four sources
publish statistics about economies; one publishes counts of terms in a news
corpus; one publishes scholarly records. None of them observes a person doing
anything.

## 4. The honest summary

```text
families the product needs                     8
families with an approving source              2   (neither is eligible, and
                                                    both are weaker than the
                                                    digit suggests -- see §2)
families with an eligible source               0
families with a collector                      0

families with no registered candidate at all   2   (Pricing, Retention)
families where no approving source observes
  an individual doing anything                 8
```

Mission 1.15 changed two things, and neither is an approval:

- **Willingness to pay went from 0 registered candidates to 2**, both carrying
  transaction-class evidence, one of them blocked on a single named activity.
- **Two hopeful maybes became definite noes** (`pinterest`, `hacker-news`), on
  retrieved first-party evidence.

A correct review concluding that candidates remain blocked is worth more than a
false approval (§39). This document exists so that the cost of that correctness
stays visible rather than being absorbed into a count of registered sources.

---

## Update after Mission 1.15.4 — transaction class, registered and still not eligible

`ted-eu` is the portfolio's only WILLINGNESS_TO_PAY candidate of **transaction**
class, and its state is now precise in all three dimensions §29 asks for:

| | |
|---|---|
| **Registered** | **yes** — `ted-eu`, review v5 |
| **Approving** | **no** — `REQUIRES_REVIEW`, unchanged since v1 |
| **Eligible** | **no** — the gate refuses with one reason, *"policy review is REQUIRES_REVIEW"* |

**This is still not a direct willingness-to-pay source, and the distinction is the
one Mission 1.15 drew.** What TED could support, if ever authorised, is
`TRANSACTION_CLASS_PUBLIC_PROCUREMENT_EVIDENCE`: what a named public buyer
awarded to a named supplier, at a reported value, for a classified category, on a
date. Whether that bears on anybody's willingness to pay is an interpretation
question for a later stage, and no Claim was created here.

Mission 1.15.4 found strong first-party evidence that TED's two **official query
routes** are documented for analysis, reuse and application integration — and
that changes nothing about the coverage row, because the blocker was never the
route.

