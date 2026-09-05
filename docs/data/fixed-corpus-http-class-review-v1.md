# Mission 1.69 — Fixed-corpus HTTP observation, reviewed

Generated from `fixed-corpus-http-class-review-v1.json`. Do not edit by hand.

**Verdict: `PROMISING_REQUIRES_ROUTE_QUALIFICATION`**

## The architecture that was hoped for

Freeze corpus C at T0. Apparatus A observes every eligible item in C during W. Apparatus B independently observes every eligible item in C during W. Both report the same deterministic predicate P.

*Why it mattered:* It would define the population by C instead of by each provider's hidden discovery frame, which is the blocker that recurred from Mission 1.58 to Mission 1.68.

## What was delivered

| property | delivered |
|---|---|
| independent production | YES, on both sides, first-party. |
| dated artifacts | YES, on both sides. |
| raw response and headers | YES for Common Crawl, whose WARC stores the raw response including HTTP header information. For HTTP Archive the full WebPageTest result is available as a payload and whether headers are separately queryable was not established. |
| coverage inspectable | YES. HTTP Archive publishes one row per page tested with its crawl date, so exactly which URLs were tested in a month is knowable. Common Crawl publishes per-crawl indexes. |
| apparatus directable at C | False |
| apparatus directable at C reason | Neither apparatus can be pointed at a corpus we choose. Common Crawl selects its own URLs and HTTP Archive takes its list from the Chrome UX Report. |

## The load-bearing finding

> Common Crawl's dataset is a sample of the web, and we do not generally archive any entire website but a randomly selected subset of it.

*Source:* https://commoncrawl.org/faq

This is the apparatus stating its own sampling in the plainest possible terms. A frozen corpus C is therefore covered by Common Crawl as a random subset, not exhaustively — so the joint population over C is C intersected with two independently determined coverages, and it is determined by what each provider happened to crawl rather than by C.

**Why this is not fatal.** Coverage is METADATA, not a measurement value, and both apparatuses publish it. A rule restricting the population to items both covered could in principle be frozen before any value is retrieved. Whether that is an honest preregistration or a population chosen after looking is exactly the question this mission leaves open.

**Why it is not waved away.** §25 wants the window frozen before values and §24 wants the population externally controlled. This satisfies the first and only half of the second, and calling that solved would repeat the hidden-frame mistake in a new place.

## Request semantics

A shared domain list does not make a shared measurement. These would have to be
reconciled before any proposition is frozen:

- user agent: CCBot against a Chrome string
- rendering: real browsers executing JavaScript against a crawler fetch, so a header-level predicate survives and a rendered-content predicate does not
- vantage: a US datacentre against an unstated Common Crawl vantage
- URL identity: home-page oriented against arbitrary URLs
- desktop and mobile are two HTTP Archive populations
- redirect policy, not stated on the pages read

## The operator route, assessed and not built

**What it would solve.** It covers exactly C by construction, removing one of the two coverage frames and leaving a single alignment question instead of two.

**Safeguards it would require.**

- frozen code version
- frozen request contract
- separate measurement lineage
- append-only raw observations
- no sight of the external apparatus's values before its own run where ordering is load-bearing

**Governance complexity.** SUBSTANTIAL, and recorded rather than minimised. It would make this repository an active measurement party against third parties, with robots, rate-limit and politeness obligations it has never had.

Crawled: False. Implemented: False.

## The one load-bearing question

Whether a population can be frozen honestly when neither apparatus can be directed at the frozen corpus, so the joint population is the corpus intersected with two independently determined coverages.
