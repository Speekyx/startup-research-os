# Mission 1.69 — Independent Product-Relevant Quantity Class Selection V1

**Outcome:
`FIXED_CORPUS_WEB_MEASUREMENT_PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED`.** Eight
quantity classes evaluated outside the scanner class. No class selected, and one is now
one question away.

---

## 0. Most quantities have exactly one possible measurer

| class | producers of the class's own unit |
|---|---|
| Q0 internet scanning | 2 (Sonar, Netlas) — parked for a different reason |
| Q1 fixed-corpus HTTP | **2** (Common Crawl, HTTP Archive) |
| Q2 package downloads | 1 (the registry) |
| Q3 code activity | 1 (the forge) |
| Q4 publication activity | 1 (the registration agency) |
| Q5 procurement | 0 of its own — one submitted document, many publishers |
| Q6 public attention | 1 per event class, and the events differ |
| Q7 DNS configuration | **2** (OpenINTEL, Sonar FDNS) — weak relevance |

Five classes have one producer and one has none of its own. **That is Missions 1.46 and
1.57's law recurring in five domains it had never been tested in**, and each was
confirmed on the producer's or aggregator's own words rather than reasoned about:

> This table is populated through the Linehaul project by streaming download logs from
> PyPI to BigQuery.

> Activity archives for dates starting 1/1/2015 are recorded from the Events API.
> … JSON encoded events as reported by the GitHub API

> We don't index journals directly — we harvest Crossref and friends, so get in there
> first.

**The exceptions are the three classes nobody is positioned to publish authoritatively**:
what services answer on the internet, what a web server returns for a defined request,
and what a resolver receives for a defined query. Each can only be established by asking.
That is not a coincidence — it is Mission 1.58's condition, now tested across eight
classes instead of asserted.

## 1. Preconditions and budget

PR #113 merged at `ad1175a`, main synced, tree clean, registry at 15, and no
selected-construct artifact from Mission 1.68. **Baseline measured live: every counter
matched §0 exactly**, and re-measured after the database-backed suites, identical.

14 of 24 first-party requests, 4 navigation searches, 8 serious classes of a permitted 8,
and **0 requests spent reopening the scanner class against a cap of 2**. Seven repository
findings were reused without re-retrieval; new requests went only where a class-specific
question had no recorded answer.

## 2. Q1 has two established independent producers, which is a first

Common Crawl fetches pages itself:

> CCBot identifies itself in its `UserAgent` string as: CCBot/2.0
> (https://commoncrawl.org/faq/)

> CCBot is now run on dedicated IP address ranges with reverse DNS

> the raw response is stored. This not only includes the response itself…but also the
> HTTP header information.

HTTP Archive loads each page itself:

> a private instance of WebPageTest with private test agents, which are the actual
> browsers that test each web page

> one row per page tested in the HTTP Archive. Pages are tested on a monthly basis

**§36 demanded first-party evidence on both sides rather than an inference from the
organisations being different, and this is it.** Neither is documented as ingesting the
other. Both publish dated artifacts. Both publish which items they covered. One stores
the raw response with its headers.

Nothing in the arc so far has had two of those at once.

## 3. And the fixed-corpus advantage is half delivered

§6 hoped a frozen corpus would replace each provider's hidden discovery frame. What
arrived:

| property | delivered |
|---|---|
| independent production | yes, both sides, first-party |
| dated artifacts | yes, both sides |
| raw response and headers | yes for Common Crawl; open for HTTP Archive |
| coverage inspectable | **yes** — which no scanner offered |
| apparatus directable at the corpus | **no** |

The load-bearing sentence is the apparatus's own:

> Common Crawl's dataset is a sample of the web, and we do not generally archive any
> entire website but a randomly selected subset of it.

And HTTP Archive's population comes from the Chrome UX Report — *"websites actively
visited by Chrome users"* — which is stable, published, and not ours to freeze.

So a joint population over a frozen corpus C is **C intersected with two independently
determined coverages**.

**Why that is not fatal.** Coverage is metadata, not a measurement value, and both
apparatuses publish it. A rule restricting the population to items both covered could in
principle be frozen before any value is retrieved.

**Why it is not waved away.** Whether that is an honest preregistration or a population
chosen after looking is exactly the question. Calling it solved would repeat the
hidden-frame mistake in a new place.

## 4. Nothing was selected, and both overstatements were refused

**Outcome B was available.** §50's outcome I explicitly does not select the class, and
selecting Q1 on the expectation that the population question resolves would preregister
an experiment on an architecture nobody has established. **§35's tie-break preference for
Q1 was not exercised**, because a tie-break may not push a class through a failed gate.

**Outcome H was also refused, in the other direction.** H says no class has two credible
independent routes. Q1 has two. Reporting H would have understated what was established
and sent the next mission hunting routes it already holds.

**Q7 has two independent producers and weak relevance.** Strengthening that relevance
would mean reading a DNS record as a customer relationship, which §22 forbids. It cannot
reach strategic viability while that is true, and the honest record says so rather than
promoting it.

## 5. The validator forced a real distinction into the model

Its first version counted own-measurement routes as producers, and refused the public
attention record: Wikimedia and a search engine both measure their own events perfectly,
and **a search is not a content request**.

That was a sentence in §20 and is now a per-route field recording whether a route
produces **this class's** world-state unit, plus a check over it. Under the corrected
definition five classes have one producer, one has none, and three have two.

**A rule that only lived in prose became one the build enforces**, and it was the
validator refusing a record of mine that made it happen.

## 6. The Mission 1.68 candidate rule was examined and not adopted

`A_PUBLISHED_SURFACE_IS_THE_SALEABLE_OBSERVATION_NOT_THE_MEASUREMENT_PIPELINE` needed a
second independent instance. Three candidates were checked and each is better described
by a rule the registry already has — `SOURCE_EXCLUSIVE_METRIC` for the registry case, and
the mirror trap for the two aggregators.

The standard applied is the one Mission 1.67 set for itself: a second instance **in a
different shape**. **Registry unchanged at 15**, and growth was not forced.

## 7. The scanner arc is parked, not refuted

`SCANNER_CLASS_RESULT` stays as Mission 1.68 wrote it, the status is
`PARKED_BUT_REOPENABLE_ON_NEW_FIRST_PARTY_EVIDENCE`, and the three reopening conditions
are written down: an ONYPHE reply, the Netlas operational questions closing, or a
positive first-party answer to Mission 1.68's one-sentence question.

The validator refuses any record that rewrites it into impossibility, and refuses an edit
to Mission 1.68's own decision record.

## 8. Nothing moved

| | |
|---|---|
| measurement values, crawls, HTTP measurement requests | 0 |
| dataset downloads, BigQuery executions, API executions | 0 |
| package, repository, publication, procurement, trend, DNS queries | 0 |
| trials, accounts, credential reads | 0 |
| mailbox searches, enquiries sent | 0 |
| sources registered, source reviews mutated, governance mutations | 0 |
| canonical mutations, thresholds, Claims, Evidence, reliability values | 0 |
| model calls, embeddings, migrations | 0 |
| constructs frozen, pairs selected | 0 |

ONYPHE stays `NOT_CHECKED_AFTER_DISPATCH`. Netlas stays unresolved.
**`PAIR_ANALYSIS_NOT_READY`.**

## 9. Verification

- Validator probed with **127 deliberate violations, 127 caught** — 124 by rule, 3 by
  drift — plus **4 of 4 positive controls**: a complementary-only class, a two-producer
  viable class, a properly evidenced selection with its artifact, and an alternative
  no-selection outcome.
- **`testing-strategy.md` §23 for the tenth time.** A guard compared a field to the
  literal `"NO"` and refused a value reading *"NO. Neither can be pointed at a corpus we
  choose."* Repaired by splitting the verdict into a boolean beside its reason, rather
  than loosening the comparison to a prefix match — which would have left the next
  explanatory sentence free to break it again.
- Five SIM102 nests collapsed **by hand**, each with exactly one statement inside, and
  the probe re-run afterwards to confirm every guard still fires.
- Two accuracy defects in my own text corrected: a test named for two classes asserting
  three, and records saying "two" where the count is three once the scanner class is
  counted honestly.
- **56 new tests**; **2207 bare-python tests**; all pytest suites passed with the
  database unchanged across 29 tenant tables; all **39** CI gates.

## 10. Next

**Mission 1.70 — Fixed-Corpus Web Route Qualification V1**, scoped to Q1's unresolved
routes only, per §53's outcome-I branch. It must answer the population question first,
then Common Crawl's URL selection, dataset immutability on both sides, HTTP Archive's
redirect and header handling, the two licences, and whether an operator-run bounded
fetcher is a governance-acceptable second route.

**No construct is frozen there either**, and broad class discovery does not restart.

**Mission 1.70 was not started.**
