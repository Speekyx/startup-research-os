# Demand-Side Source Priority V1

**Authoritative.** Mission 1.15 §22, §23. Which source to pursue next, and why.

**Qualitative and ordinal only.** These are P0/P1/P2 buckets with stated
reasoning. There is no weighted formula, no numeric source score, and there will
not be one: a weighting nobody reviewed would be the arbitrary coefficient
Mission 1.14 spent a whole mission refusing, wearing a different name.

**This is not an OpportunityScore.** It ranks *work to do*, not business value.

---

## 0. The rule this applies

> **Prefer the source that creates the FIRST usable evidence for a missing
> family over the source that creates the tenth version of a covered one.**

The portfolio has five approving sources and they cover the same shape of thing:
published aggregate context. A sixth macroeconomic series would add precision to
something already covered. The first source that observes a purchase, or a
person's difficulty, changes what the engine can answer at all.

Applied concretely: `Pain`, `Desire`, `WTP`, `Pricing`, `Competition`,
`Retention` and `User behaviour` each have **no approving source**. Any of them
outranks a sixth entry in `trend`.

## 1. The factors

Named so the reasoning can be argued with, not to be multiplied together.

| Factor | Question |
|--------|----------|
| **Unique family coverage** | Would this be the FIRST usable source for a family? |
| **Permission confidence** | How much of the activity matrix is granted, on retrieved first-party evidence? |
| **Blocker type** | Is what stands in the way a *document to retrieve*, a *decision to take*, or a *commercial negotiation*? |
| **Implementation complexity** | Bulk files and documented APIs are cheap; authenticated, paginated, rate-limited surfaces are not |
| **Access stability** | Is the access route published and versioned, or discretionary? |
| **Personal-data risk** | How much minimisation work stands between the record and a lawful one? |

**Blocker type is the factor that decides most of this ranking.** A source
blocked by a document nobody has fetched is a different kind of problem from one
blocked by a commercial negotiation, and the registry has never distinguished
them explicitly before.

## 2. The ranking

### P0 — `ted-eu`

**The only P0, and the gap between it and everything else is large.**

| Factor | Assessment |
|--------|------------|
| Unique family coverage | **First and only lawful route to WILLINGNESS_TO_PAY as a transaction.** Also the only registered `competition` candidate that is not RESTRICTED |
| Permission confidence | **Highest of any blocked source in the catalog.** Five of six load-bearing activities granted in one retrieved sentence |
| Blocker type | **One named activity** — `model_processing` — resolvable by retrieving one more first-party instrument |
| Implementation complexity | Low. Daily and monthly bulk XML, no sign-in, plus a documented read-only search API |
| Access stability | High. A statutory publication with a legal obligation behind it, not a discretionary API |
| Personal-data risk | Real and boundable. Contact blocks are present and must be discarded by minimisation; the fields the engine needs contain no natural person |

**Why this beats every alternative.** No other blocked source has five of six
activities granted. No other candidate offers an evidence class the portfolio has
never held. And its blocker is the cheapest kind there is — a document to fetch,
not a negotiation to open or a decision nobody is empowered to take.

**What it will not do, kept in view.** Public-sector buying above EU publication
thresholds. Nothing about consumers, nothing about SaaS pricing, nothing about
individuals. It would be the portfolio's first WTP evidence and still not be
evidence of consumer willingness to pay.

### P1 — `bluesky`, `usaspending`

Both blocked by exactly one retrievable document.

**`bluesky`** — the developer guidelines exist and returned an empty body. If
they permit third-party reading of public records for a commercial product, it
becomes the first plausible `pain` and `user_behaviour` candidate, on a protocol
built for independent consumers. If they do not, the catalog's most-cited
open question closes for good. Either answer is worth having; the current state —
knowing the document exists and not what it says — is the worst of the three.

**`usaspending`** — a second transaction source, weaker than TED because nothing
granting reuse has been retrieved. Its value is partly as corroboration: two
independent procurement systems agreeing about a category of spend is a
different evidential position from one.

### P2 — `reddit`, `stack-exchange`

Both unreachable from this environment, both high-value, both entirely
unadvanced.

Reddit is probably the richest pain and product-comparison corpus in existence
and Stack Exchange the clearest record of developer difficulty. Neither moved.
P2 not because they matter less but because **the next action is not a review** —
it is obtaining the terms from an environment that can reach those hosts, and
for Reddit very likely a commercial agreement after that.

### Not pursued — `pinterest`, `hacker-news`

Both `RESTRICTED` on retrieved evidence this round. Pinterest describes a route
(explicit written authorization for competitor-research features) and that is a
commercial negotiation, not review work. Hacker News describes none.

Neither should be revisited without a new first-party grant. A different endpoint
under the same governing terms does not change a policy restriction.

### Not pursued — everything else

`google-trends`, `twitch`, `huggingface`, `discord`, `x-twitter` were not
reviewed this round and are neither closer nor further than before. The app
stores, `product-hunt`, `steam`, `github`, `meta-instagram` remain `RESTRICTED`
and were not re-opened.

## 2.1 What Mission 1.15.1 changed

The P0 recommendation below was executed as Mission 1.15.1 and **did not close**.
`ted-eu` stays P0, and the reasoning under "Blocker type" got sharper rather than
weaker.

**The governing instrument is now named and proven**: Commission Decision
2011/833/EU, cited by TED's own legal notice. That was the guess in the row
below; it is now a fact.

**Its text could not be retrieved.** Five first-party EUR-Lex addresses returned
empty bodies. So the blocker moved from *"a document to fetch, if we can work out
which one"* to *"this exact document, from an environment that renders EUR-Lex"*
— which is the same class of blocker, smaller.

**A second question surfaced (H-36).** Whether the reuse grant reaches the sui
generis database right, given that the access route is bulk extraction of
substantial portions. It bears on `automated_access` and `redistribution` rather
than `model_processing`, so **it could block `ted-eu` even if H-34 closes
favourably**. That is new risk, honestly recorded, and it does not change the
ranking: both questions are likely answered by the same retrieval.

## 2.2 What Mission 1.15.2 changed

**H-34 closed PERMITTED.** Commission Decision 2011/833/EU was retrieved from the
Publications Office Cellar and read in full. Article 3(2) defines reuse by
*purpose* — *"the use of documents … for commercial or non-commercial purposes
other than the initial purpose"* — and enumerates no acts, so the method of use
does not enter. All six load-bearing activities are now positively granted.

**And `ted-eu` is still blocked**, because H-36 did not close. The Decision
contains no occurrence of *sui generis*, *extraction*, *re-utilisation* or
Directive 96/9/EC. It governs **documents**; the collection they sit in is never
mentioned.

**The blocker changed kind.** It was *"retrieve a document"*. It is now *"decide
a legal question the documents do not answer"* — which is more expensive, and
which is why `ted-eu` staying P0 is now a weaker claim than it was.

**A collector route was not forced.** Bulk XML and the search API are analysed
separately (§29) and both are unresolved, with different exposure: bulk is the
paradigm case of extracting substantial parts, the search API less obviously so.
Choosing bulk now because it is convenient would be choosing the more exposed
route before knowing whether the exposure is real.

## 3. The recommendation

**Superseded by Mission 1.15.2.** The Decision was retrieved and read. H-34
closed PERMITTED; H-36 did not close, and the Decision does not address database
rights at all.

**The next action is no longer a retrieval.** It is a first-party clarification
from the Publications Office on whether it asserts or waives database rights in
TED, and failing that a legal review of whether a documents reuse policy carries
the database right by implication. That is the first item in this document's
history that a further document search cannot answer, because the documents have
been read.

Three outcomes, all useful:

| If | Then |
|----|------|
| It grants ML processing | `ted-eu` becomes `APPROVED_WITH_CONDITIONS` and the portfolio has its first WTP source. A collector mission follows immediately |
| It prohibits it | `ted-eu` is `RESTRICTED` and the largest gap is confirmed closed by that route. Knowing costs one retrieval |
| It is silent | The verdict stands, and the question moves to legal review — which is a named, routable action rather than an open unknown |

**Building a collector for a `REQUIRES_REVIEW` source is not an option**, and not
because a rule forbids it. The eligibility gate would refuse the job, the
authorization context would refuse to construct, and the collector would be code
that cannot run — which is the gate working exactly as designed.

**A collector for anything else would be worse.** No other source is closer, and
the five approving sources already have collectors or do not need one for this
gap.
