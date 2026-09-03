# Mission 1.33 — Commercial Dimension Source Feasibility V1

**Outcome:** `COMMERCIAL_SOURCE_GRAIN_MISMATCH` (§21 D)

**Branch:** `sprint-1/mission-1.33`
**Desk review:** [`commercial-dimension-source-feasibility-v1.md`](../data/commercial-dimension-source-feasibility-v1.md)
**Matrix:** [`commercial-dimension-source-feasibility-v1.json`](../data/commercial-dimension-source-feasibility-v1.json)

---

## 0. The finding

**The sources that can name Docker carry no commercial semantics; the sources
that carry commercial semantics cannot name Docker.**

Five of twenty-nine sources publish an identifier that names the container
platform. Two are already in the packet and are epistemically exhausted. The
other three are blocked, and for two of them the blocker is a finding about the
PURPOSE of the use, which the active profile does not change — so a governance
mission would spend itself re-deriving a conclusion already on file.

Meanwhile the sources with genuine `MARKET_ACTIVITY`,
`BUYER_OR_BUDGET_EXISTENCE` and `ECONOMIC_VALUE` warrants observe procurement
CATEGORIES and macroeconomic aggregates. TED is authorized, collected,
normalized, extracted and already producing Evidence — and its subject key is
`ted-eu:CPV-division:90`, a two-digit procurement category that cannot name a
software product at any depth.

That is outcome D, and it turns the next step from a source question into an
architecture question.

---

## 1. The twenty-three answers

### 1. How many registered sources were reviewed?

**29**, every one in the catalog. The matrix is generated against
`source-catalog-v1.json` and refuses to emit if it does not cover exactly the
registered set, so a source cannot be skipped by omission.

### 2. How many can identify Docker at appropriate grain?

**5**: `github`, `product-hunt`, `reddit`, `stack-exchange`,
`wikimedia-pageviews`.

A further **7** reach Docker only as a MENTION — a word in text, a topical
match, or a related-but-different artifact: `gdelt`, `google-trends`,
`hacker-news`, `huggingface`, `npm-registry`, `openalex`, `pypi`. The remaining
**17** cannot reach it at all.

### 3. How many could support at least one missing commercial dimension?

**3**, and all three are blocked:

| Source | Dimension(s) | Blocker |
|---|---|---|
| `github` | COMPETITIVE_SUPPLY, FEASIBILITY_SIGNAL | governance, decisively |
| `product-hunt` | COMPETITIVE_SUPPLY | governance, needs a company's permission |
| `reddit` | SOLUTION_DISSATISFACTION | governance unknown, plus a missing inference layer |

### 4. How many are currently governance-authorized?

**8** hold a `local-private-research-v1` review, and all eight are
`APPROVED_WITH_CONDITIONS`: `eurostat`, `fred`, `gdelt`, `openalex`,
`stack-exchange`, `ted-eu`, `wikimedia-pageviews`, `world-bank`.

**Of the three candidates in question 3: zero.**

### 5. How many require governance work?

**21 have no local-profile review at all**, and ADR-027 means they are refused at
the gate today whatever their terms say — approval never transfers between
profiles.

That number is easy to misread as twenty-one opportunities. For the candidates
that matter it is not. GitHub's and Product Hunt's commercial findings are about
the **purpose** of the use, and the deployment-model invariant says plainly that
**local deployment never implies non-commercial use**. A local review would meet
the same clause and fail on it.

So the honest split is: 21 missing reviews, of which **2 are predictably
adverse**, **1 is genuinely unknown** (`reddit`, whose terms could not be
retrieved), and the remaining 18 concern sources that are wrong-grain or
wrong-domain anyway.

### 6. How many require collector implementation?

**24 of 29.** Five collectors exist: `gdelt`, `stack-exchange`, `ted-eu`,
`wikimedia-pageviews`, `world-bank`. All three candidates lack one.

### 7. Which sources are wrong-grain?

**23**, split into two verdicts because the reasons differ:

- **`WRONG_GRAIN` (13)** — the identifier exists but is too coarse or names
  something else: `bluesky`, `discord`, `eurostat`, `fred`, `gdelt`,
  `google-trends`, `npm-registry`, `openalex`, `pypi`, `ted-eu`, `usaspending`,
  `world-bank`, `x-twitter`.
- **`WRONG_DOMAIN` (10)** — the identifier is precise and names a different class
  of thing entirely: `apple-app-store`, `google-play`, `huggingface`,
  `meta-instagram`, `pinterest`, `spotify`, `steam`, `tiktok`, `twitch`,
  `youtube`.

The distinction matters because an App Store id is *beautifully* precise. Its
problem is not resolution, and lumping it with CPV divisions would obscure that.

### 8. Which source is best for `SOLUTION_GAP`?

**None.** Nothing in the portfolio observes the absence of an adequate solution.

This is the same wall Mission 1.32 hit from the other side, and the dimension's
own `never_means` is why: *that absence of evidence of a solution is evidence of
its absence*. Every candidate route — unanswered questions, empty search results,
a thin package ecosystem — is an absence of evidence. A source that could support
it would have to observe somebody trying and failing to find a solution, and no
registered source publishes that.

### 9. Which is best for `SOLUTION_DISSATISFACTION`?

**`reddit`**, and it is blocked twice.

Mission 1.32 established that a request for help is not dissatisfaction. A
discussion forum is different in kind: it carries evaluative statements about
named tools, and a post saying a specific product became unusable for a stated
reason is dissatisfaction with what somebody uses today. A subreddit is also a
publisher-assigned identifier, structurally comparable to a Stack Overflow tag.

Blocker one is governance and is genuinely **unknown** rather than adverse — the
Data API Terms, Developer Terms and Responsible Builder Policy could not be
retrieved, and `commercial_use` is `UNCLEAR`. Blocker two is harder: telling an
evaluative complaint from a request for help inside free text is a semantic
reading, an `INFERRED` path that does not exist and whose nearest relative is
PARKED. **A successful Reddit governance mission would deliver a corpus nothing
can currently read.**

### 10. Which is best for `COMPETITIVE_SUPPLY`?

**`github`**, and it is the strongest unclaimed commercial dimension available
anywhere in the portfolio.

A public repository IS a supplied solution — somebody built a thing and published
it where anyone can take it — which is a direct, deterministic answer to *who
already serves this need*. The grain is excellent: `moby/moby`, `docker/compose`,
`docker/cli` are exact, publisher-assigned identifiers.

And the Acceptable Use Policies section 7 is an allowlist that applies
*"regardless of whether the information was scraped, collected through our API,
or obtained otherwise"*, permitting research use **only if resulting publications
are open access**. SROS produces proprietary insights. The one thing that would
move this is not a review: it is a commitment to publish GitHub-derived outputs
open access, which is a product decision and is recorded as an observation, not a
recommendation.

### 11. Which is best for `MARKET_ACTIVITY`?

**`ted-eu`** — and not at Docker grain, which is the whole mission in one answer.

TED is `APPROVED_WITH_CONDITIONS` locally, has a collector, a normalizer, an
extractor and a derived Signal, and its Evidence already maps to
`MARKET_ACTIVITY`, `BUYER_OR_BUDGET_EXISTENCE` and `ECONOMIC_VALUE`. Every piece
of the pipeline exists. The single thing it cannot do is name Docker.

### 12. Can any source support `BUYER_OR_BUDGET_EXISTENCE` at Docker grain?

**No.** `ted-eu` and `usaspending` observe real buyers with real authority to
award, at a procurement classification grain.

USAspending carries an extra trap worth naming: a recipient name could match
`Docker, Inc.`. The canonical subject registry says in its own words that
`subject:docker` is the container platform and **NOT the company**, so a contract
awarded to a vendor is evidence about that vendor.

### 13. Can any source support `ECONOMIC_VALUE` at Docker grain?

**No**, for the same reason and with the same two sources. Money moves in the
bounded activity those notices describe; the bounded activity is a category.

### 14. Can any source support `WILLINGNESS_TO_PAY` at Docker grain?

**No — and none at any grain.** The answer is `NONE`, and it is not a gap in this
review.

The taxonomy had already committed to the strict reading before the mission
asked. `WILLINGNESS_TO_PAY` requires evidence that a specific actor paid or
committed to pay, and its `never_means` names the three near-misses verbatim:

> a listed price, which is an ask and not a transaction · a budget line, which is
> a capacity and not a decision · a public contract total, which includes options
> and renewals and may be lawfully withheld

So a pricing page would establish an offered price and stop. The closest thing
the portfolio holds is a TED award total, and Mission 1.15.12 established from
the Publications Office's own SDK that it includes options and renewals and is
not what a buyer paid.

### 15. Is the current subject-grain architecture itself limiting evidence combination?

**Yes, and it is the binding constraint.**

`CanonicalSubject` carries `subject_id`, `display_name`, `description` and
`identifiers` — and **no scope field**. `subject_for()` returns one subject per
rendered key; a packet holds one `subject`. There is one namespace with one level
in it, so an Evidence row belongs to exactly one subject and an Opportunity's
subject is the subject of every row supporting it.

Two observations make the gap concrete:

- **SROS already models GEOGRAPHIC scope on an Opportunity and models no SUBJECT
  scope at all.** `MarketScope` is a closed union of
  `GLOBAL | REGION | COUNTRY | MULTI_COUNTRY`, and the first Opportunity carries
  `GLOBAL` with the limitation recorded on the row. Nothing comparable exists for
  product versus category versus market.
- **The dimension vocabulary already assumes an answer.** `MARKET_ACTIVITY` asks
  about *"the bounded scope observed"* and `ECONOMIC_VALUE` about *"the bounded
  activity observed"*. Those questions were written expecting an observation to
  carry its own scope. The packet model has nowhere to put it, so a TED
  observation's scope collapses into the packet's single subject — and the only
  way to keep the claim honest is to keep the observation out entirely.

Both limitations are real. **The source limitation would survive any
architecture** — no registered source publishes an identifier that both names
Docker and carries commercial semantics. **The architectural one is what makes it
fatal**: commercial evidence in this portfolio exists at category and market
scope, and the engine cannot use evidence at a broader scope *at all* — not
weakly, not with a caveat, not as context.

### 16. What is the top candidate source?

**For acquisition today: none.**

`github` has the best grain and the strongest dimension in the review and is
`NOT_RECOMMENDED`, because its restriction is decisive and purpose-based.

**Conditional on a multi-scope architecture, `ted-eu` is PRIORITY_1 by a
distance** — authorized, collected, normalized, extracted, carrying three
commercial dimensions, waiting only for a way to say what scope it observes.
Which CPV division covers the relevant IT services is for that mission to
establish from TED's own published vocabulary; this review asserts none, in
keeping with the collector's own rule that no CPV code is expanded.

### 17. Exact next governance/implementation action?

Neither. **Model the scope an Evidence row OBSERVES separately from the subject
an Opportunity is ABOUT** — see question 23.

Acquiring first would produce Evidence in its own packet that can never join
`subject:docker`, which is how a packet grows without a hypothesis becoming any
better supported.

### 18. Were any network acquisitions performed?

**No.** No collector ran, no socket opened, and no external document was
retrieved. Every fact in the review comes from committed repository artifacts:
`source-catalog-v1.json`, the review records inside it, the canonical subject
registry, the dimension definitions and the engine's own source. Where a fact
could only be established by querying a source — whether Product Hunt lists
Docker, which CPV division covers IT services — the review says so rather than
guessing.

### 19. Were any model calls made?

**No.** Zero calls, zero cost. No inference was used to bridge a grain gap, and
the matrix names no similarity, embedding, fuzzy match or edit distance as a
mechanism.

### 20. Did any canonical counters change?

**No. All thirteen verified against the live database and unchanged:**

| Counter | Expected | Actual |
|---|---:|---:|
| RawRecords | 148 | **148** |
| NormalizedRecords | 148 | **148** |
| Signals | 28 | **28** |
| Claims | 28 | **28** |
| ClaimRevisions | 29 | **29** |
| Evidence | 28 | **28** |
| EvidenceIndependenceGroups | 0 | **0** |
| ReliabilityAssessments | 1 | **1** |
| Opportunities | 1 | **1** |
| OpportunityHypothesisRevisions | 1 | **1** |
| Opportunity hypothesis/evidence links | 7 | **7** |
| Embeddings | 0 | **0** |
| Registered sources | 29 | **29** |

`scoring.scores` still does not exist. Latest migration is still `0031`, and no
migration was added.

### 21. Is scoring still blocked?

**Yes.** D-03 is untouched, no `CALIBRATED` profile exists, and every row in the
Docker packet is still `NON_SCORABLE` with `MISSING_RELIABILITY`. No
`ReliabilityAssessment` was created (§17), and the count stands at the one row
Mission 1.16 wrote for the TED scope.

### 22. Is Problem-Family still PARKED?

**Yes.** `PARK_PROBLEM_FAMILY_CLASSIFIER` stands and production inference remains
`NOT_AUTHORISED`. The relation is named once in the matrix — in the Reddit row,
to say that the extraction path it would need is parked — and a test asserts that
every mention of it says so.

### 23. Recommended next mission?

**Multi-Scope Opportunity Evidence Architecture V1**, which is §16's alternative
and §23's rule for a dominant grain mismatch.

> Model the scope an Evidence row OBSERVES separately from the subject an
> Opportunity is ABOUT, so that `PRODUCT`, `CATEGORY`, `MARKET` and `GEOGRAPHY`
> can each be stated without claiming they are identical. Decide what a
> hypothesis may and may not conclude from evidence observed at a broader scope
> than its own subject — the answer is unlikely to be *nothing* and is certainly
> not *the same as its own scope*.

Only after that does an acquisition mission make sense, and `ted-eu` is waiting
for it with every piece already built.

**If that mission is declined**, the honest fallback is Reliability / Scoring
Eligibility Foundation: the Docker packet's eight rows are all `NON_SCORABLE` for
want of a reviewed reliability, and improving what the system can conclude from
the evidence it HAS does not depend on acquiring more. Commercial evidence
acquisition stays recorded as a longer-term portfolio gap.

---

## 2. What this mission deliberately did not do

- **Did not change any source's governance verdict.** The matrix copies the
  `local_review` and `commercial_review` columns from the catalog and asserts
  that it read the same catalog version, so a review that moves makes the
  artifact stale in a checkable way rather than quietly wrong.
- **Did not add an identifier to the canonical subject registry.** `docker` still
  holds exactly two, from `wikimedia-pageviews` and `stack-exchange`, and the
  registry still holds exactly three subjects.
- **Did not attach category evidence to a product subject.** The temptation was
  concrete — TED has the dimensions the packet lacks and is fully built — and
  taking it would have been the subject-identity weakening §9 forbids, reached
  through the packet builder instead of through the registry.
- **Did not implement a scope hierarchy.** §10 asked whether one is needed and
  §16 says to record it as a future mission. Nothing here models `PRODUCT`,
  `CATEGORY` or `MARKET`.
- **Did not invent a dimension**, did not credit any source with
  `WILLINGNESS_TO_PAY`, and did not create a `ReliabilityAssessment`.

---

## 3. Tests

[`test_source_feasibility.py`](../../packages/opportunity-engine/python/tests/test_source_feasibility.py),
34 tests. A desk review produces a document, and a document can say anything;
what these hold is the structure that makes it checkable.

- **Every registered source is answered**, with a verdict from the vocabulary, a
  stated identifier grain and a named blocker. Coverage is checked against the
  catalog rather than against a literal.
- **The three questions stay apart.** A right-grain source may be refused (and at
  least one is, or the distinction is untested); an authorized, collected source
  may be useless (and at least one is); a source with no local review is refused
  whatever its commercial verdict says.
- **A dimension needs a warrant.** Every named dimension exists in the taxonomy,
  carries a written warrant and at least three stated limits, and a row naming no
  dimension may carry no warrant prose. The limits QUOTE the dimension's own
  `never_means` verbatim rather than paraphrasing it.
- **Price is not willingness to pay**, no row claims WTP, a buyer or a value at
  this grain, and the taxonomy's own three near-misses are asserted.
- **A broad category is not the subject**: the procurement sources are `NO` at
  grain, TED is recorded as capable-and-mis-scoped rather than useless, and the
  registry gained no identifier.
- **The prose agrees with the matrix.** The §2 table is checked row by row
  against the JSON — verdicts, dimensions, collector marks — and the counts the
  prose states are recomputed.

Two of my own tests were too crude and were narrowed rather than deleted, both
instances of `testing-strategy.md` §23. A scan forbidding the word *embedding*
failed on the sentence that forbids embeddings, so it now reads the per-source
rows where a mechanism would actually be proposed. A scan forbidding
`SAME_PROBLEM_FAMILY` failed on the row that names it in order to refuse it, and
was replaced with the stronger positive assertion that every mention says PARKED.

---

## 4. CI-equivalent verification

| Gate | Result |
|---|---|
| `generate.py --check` | ok |
| `run_python_tests.py` | all suites passed, 571 tests across 8 packages |
| `validate_schema.py` | 9 invariant groups, 43 tables |
| `migrate.py --plan` | well formed, ledger at 0031 |
| `validate_source_registry.py` | 29 sources, 42 evidence records, 0 warnings |
| `validate_compliance_capabilities.py` | 34 conditions, 13 approving pairs |
| `validate_normalization.py` / `validate_signals.py` / `validate_claims.py` | 9 / 7 / 11 boundary groups |
| `validate_evidence_aggregation.py` | 8 checks, scoring still blocked |
| network-client and collector-in-governance grep guards | no offenders |
| `ruff check` / `ruff format --check` | clean |
| `mypy` (13 packages) | no issues |
| generated-doc `--check` steps (4) | all match |
| `run_pytest_suites.py` | passed across 9 packages; database unchanged |
