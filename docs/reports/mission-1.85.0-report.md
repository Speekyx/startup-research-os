# Mission 1.85.0: Business Evidence Acquisition Roadmap

**`BUSINESS_EVIDENCE_ROADMAP_READY_FIRST_PERSON_STRUCTURED_SOURCES_NEXT`**

Mission 1.84 is closed for the current TED packet (operator decision D4). This mission answers one
question: **what evidence-acquisition capabilities must SROS add so that it can identify real product
opportunities, rather than only prove that a market or procurement activity exists?**

It is a research-architecture transition, not another gate mission. Nothing was collected, no model
was called, and no source review, reliability assessment, independence group, score or Opportunity was
created.

```
START_COMMIT        76cecfeb9c470b8b95801375dbd74cd56e83828d  (merged main after PR #171)
BRANCH              sprint-1/mission-1.85.0

PROVIDER_CALLS 0   MODEL_INFERENCES 0   NEW EXTERNAL DATA PERSISTED 0   V11 NO   OPPORTUNITY #2 NO
roadmap artifact    docs/data/business-evidence-acquisition-roadmap-v1.json
consistency test    packages/opportunity-engine/python/tests/test_business_evidence_roadmap.py
```

**The answer in five lines.**

- SROS holds evidence for **3 of 20** business dimensions (market activity, buyer existence, economic
  value), all from one signal type over TED at CPV-division scope. Two more are partial. **15 are
  unsupported**, including every one that distinguishes an opportunity from an activity: frustration,
  recurrence, workaround, willingness to pay, switching, solution gap, competitor weakness, feature
  demand, unmet need.
- The missing dimensions are blocked **twice**: by governance (every registered first-person source is
  RESTRICTED or unreviewed under the local profile) and by the absence of any authorised way to read
  first-person **text** (D-12, egress, the PARKED problem-family relation).
- The only route that does not wait for the second blocker is **first-person evidence exposed as a
  source-native structured field**: a reviewer's own star rating, a tracker's own label, a publisher's
  own duplicate link. That makes **product reviews (F-REVIEW)** and **public issue trackers (F-ISSUE)**
  the first families to qualify.
- Before evidence from several sources can be scored, the engine has a **latent hazard** to fix:
  `levels.py` counts dependent groups as groups of established independence.
- **Mission 1.85.1 is governance qualification, not a collector**: retrieve first-party terms for a
  frozen candidate list in F-REVIEW and F-ISSUE and select exactly one source, or record the no-go.

## How the work was divided

Five read-only agents worked in parallel; the main agent verified their load-bearing claims against the
code and the database (read-only) and was the only writer.

| Agent | Question | Verified by the main agent |
|---|---|---|
| A | What does held evidence support, per source? | signal-type mapping; per-source counts |
| B | Which source families could fill the gaps, and what blocks them? | catalog ids, verdicts |
| C | Can the ontology represent first-person business evidence? | `EvidenceDimension`, guard token list |
| D | Why 4 assessments, 0 groups, no scores? What must exist first? | `levels.py`, `independence.py`, SQL facts |
| E | Which score components are ready? | scoring framework, engine prohibitions |

## 1. Current evidence coverage

Canonical counters, read-only on 2026-09-16:

```
raw 325  normalized 325  signals 60  claims 91  revisions 92  evidence 112 (111 SUPPORTS, 1 CONTRADICTS)
reliability assessments 4 current   independence groups 0   opportunities 1 (2 revisions)   scores absent
every evidence row: independence_state UNKNOWN, reliability column NULL (late binding)
```

Signal types map to evidence dimensions in `sros_opportunity/mapping.py`
(`signal-type-dimension-map@1.0.0`). Four of the seven implemented signal types map to nothing.

| Business dimension | Evidence dimension | Coverage | Held by | Bound |
|---|---|---|---|---|
| market activity | MARKET_ACTIVITY | **SUPPORTED** | ted-eu | award totals of one CPV division; not market size |
| buyer existence | BUYER_OR_BUDGET_EXISTENCE | **SUPPORTED** | ted-eu | public-sector authorities; never "would buy THIS" |
| economic value | ECONOMIC_VALUE | **SUPPORTED** | ted-eu | BT-161 includes options and renewals |
| pain | PROBLEM_OR_NEED | PARTIAL | stack-exchange | one count of help questions under one tag |
| existing spend | none | PARTIAL | ted-eu | proxy only; not realised expenditure |
| frustration, frequency, recurrence, severity, workaround, economic cost of pain, willingness to pay, switching intent, adoption intent, retention, solution gap, competitor weakness, review sentiment, feature demand, unmet need | various or none | **NOT SUPPORTED** | none | |

By source: **world-bank** (4 signals) and **gdelt** (3) map to no dimension; **wikimedia-pageviews**
(18) maps to AUDIENCE_OR_USAGE and TREND_OR_CHANGE, neither of which is among the 20 and the second of
which never counts; **stack-exchange** (2) supplies the partial pain; **ted-eu** (33) supplies all three
supported dimensions.

## 2. Current source inventory

29 sources are registered. **8 hold a `local-private-research-v1` review** (eurostat, fred, gdelt,
openalex, stack-exchange, ted-eu, wikimedia-pageviews, world-bank), and ADR-027 refuses the other 21 at
the gate whatever their terms say. **5 have a collector and a normalizer**, and they are exactly the
five holding data.

| Group | Sources | State |
|---|---|---|
| Collected | world-bank, gdelt, wikimedia-pageviews, stack-exchange, ted-eu | local APPROVED_WITH_CONDITIONS, collector and normalizer |
| Approved, not built | eurostat, fred, openalex | local APPROVED_WITH_CONDITIONS; openalex has two unsatisfied conditions |
| RESTRICTED | apple-app-store, google-play, steam, github, hacker-news, meta-instagram, pinterest, product-hunt | commercial profile; no local review |
| PROHIBITED | spotify, tiktok, youtube | commercial profile |
| REQUIRES_REVIEW | bluesky, discord, google-trends, huggingface, npm-registry, pypi, reddit, twitch, usaspending, x-twitter | terms missing, unreachable or silent |

Every registered first-person source (reviews, community, developer, product feedback) is in the last
three rows.

## 3. Missing business dimensions

The 15 unsupported dimensions fall into three groups, and the grouping is what decides the order of work.

| Group | Dimensions | What would supply them |
|---|---|---|
| **Structured first-person** | frustration and review sentiment (as a rating), recurrence and frequency (as a declared duplicate), feature demand (as a label or vote) | a source-native field, read deterministically into an OBSERVED claim |
| **Text first-person** | pain beyond counts, workaround, switching intent, competitor weakness, stated willingness to pay, unmet need, severity | reading what a person wrote: an INFERRED, model-derived step that is not authorised |
| **Structural** | retention, economic cost of pain, adoption intent, existing spend | no public statement measures them directly; they stay unsupported or proxied |

## 4. Candidate source families

Facts below are what the repository records. Anything not recorded is `NOT_ESTABLISHED` and needs a
documentation-review mission; no general knowledge is presented as established.

| Family | Registered | Governance today | Deterministic path | Needs text reading for |
|---|---|---|---|---|
| **F-REVIEW** reviews with a rating | apple-app-store, google-play, steam | RESTRICTED on purpose clauses; no local review; SaaS review sites unregistered | reviews of one listing in one rating band in one window | pain, switching, feature demand |
| **F-ISSUE** issue trackers | github | github RESTRICTED (AUP open-access condition); TDF Bugzilla robots-blocked, Launchpad without field selection, kernel.org without licence; others unassessed | issues under the tracker's own label; publisher-declared duplicates | workaround, severity |
| F-QA community Q&A | stack-exchange | local approval for stackoverflow only; both Docker reliability scopes declined | question counts, accepted-answer state | workaround |
| F-DISCUSSION | reddit, hacker-news, bluesky, x-twitter, discord | reddit terms never retrieved; HN RESTRICTED | vote and comment counts only | every business dimension |
| F-FEATURE-BOARD | none | unregistered | votes on one request | pain |
| F-PRODUCT-LAUNCH | product-hunt | RESTRICTED (no commercial use without permission) | vote counts | frustration |
| F-JOBS | none | unregistered | postings under a native category | pain |
| F-PROCUREMENT | ted-eu, usaspending | ted-eu usable; usaspending REQUIRES_REVIEW | existing | none |
| F-STATISTICS-TRENDS | world-bank, eurostat, fred, openalex, wikimedia-pageviews, gdelt, google-trends | mostly usable | existing | none |

Independence characteristics are uniform and unwelcome: **every first-person source measures a
platform-recorded quantity**, so a second route to the same platform is a copy, and one platform is one
apparatus. Copied reviews, reposts, crossposts and event cascades are the dominant dependence modes.

## 5. Source-to-dimension matrix

S = strong, W = weak, `.` = none. `*` = reachable only through text reading (roadmap node N08); cells
without `*` are reachable deterministically from a source-native field once the source is qualified.
Generated from the roadmap artifact, so the two cannot diverge.

| Dimension | REVIEW | ISSUE | QA | DISCUSSION | FEATURE-BOARD | PRODUCT-LAUNCH | JOBS | PROCUREMENT | STATISTICS-TRENDS |
|---|---|---|---|---|---|---|---|---|---|
| market activity | . | . | . | . | . | . | . | S | W |
| buyer existence | . | . | . | . | . | . | S | S | . |
| economic value | . | . | . | . | . | . | . | S | . |
| pain | S* | S | S | S* | W* | . | W* | . | . |
| existing spend | W | . | . | W* | . | . | W | W | . |
| frustration | S | . | . | S* | . | W* | . | . | . |
| frequency | . | S | . | . | . | . | . | . | W |
| recurrence | . | S | . | . | W | . | . | . | . |
| severity | . | W* | . | . | . | . | . | . | . |
| workaround | . | S* | W* | S* | . | . | . | . | . |
| economic cost of pain | . | . | . | . | . | . | W | . | . |
| willingness to pay | . | . | . | W* | . | . | . | . | . |
| switching intent | W* | . | . | S* | . | . | . | . | . |
| adoption intent | . | . | . | W* | . | S | . | . | W |
| retention | . | . | . | . | . | . | . | . | . |
| solution gap | . | W | . | . | . | . | . | . | . |
| competitor weakness | S | . | . | S* | . | . | . | . | . |
| review sentiment | S | . | . | S* | . | . | . | . | . |
| feature demand | S* | S | W | S* | S | W | . | . | . |
| unmet need | W | W | . | S* | W | . | . | . | . |

Reading down the columns: F-DISCUSSION is the richest family and almost all of it is `*`. F-REVIEW and
F-ISSUE together reach frustration, review sentiment, competitor weakness, recurrence, frequency and
feature demand **without** text reading, which no other combination does.

## 6. Ontology compatibility

**Verdict: first-person business evidence fits the existing layers where it is a source-native structured
fact; it needs registry entries and one quantity-family ADR, not a new claim type, direction or
evidence table. Anything that reads free text is blocked, and the blocker is authorisation, not
storage.**

How a single review is represented: a Signal requires at least two observations, so a single review is
never a Signal. The correct shape is an **aggregate over a source-native field** — reviews of one listing
in one rating band in one window — restated as an OBSERVED claim (*"{source} published N reviews of
listing "X" carrying rating "1" on its own "5"-point scale, created between T1 and T2"*). It maps to
SOLUTION_DISSATISFACTION, precisely the datum the accepted-answer flag lacked (Mission 1.32). It
establishes neither pain, nor willingness to pay, nor distinct people.

| Example | Classification | Structure |
|---|---|---|
| negative review (rating) | new registry entries | kind `product_review`; rating-band volume signal; OBSERVED; SUPPORTS; SOLUTION_DISSATISFACTION |
| positive review (rating) | new registry entries | same kind, high band; **maps to no dimension** |
| competitor complaint | registry entries (direct to that product); scope ADR to reach a category opportunity | as above, scope = competitor PRODUCT |
| feature request (tracker label) | new registry entries | kind `issue_report`; label volume signal; PROBLEM_OR_NEED |
| repeated complaint | blocked | same-problem identity is the PARKED relation; a publisher-declared duplicate is the one exception |
| complaint (free text) | text contract required | INFERRED, model-derived |
| explicit pain statement | text contract required | INFERRED; PROBLEM_OR_NEED |
| workaround | text contract required | PROBLEM_OR_NEED + SOLUTION_GAP, bounded |
| price complaint | text contract required | SOLUTION_DISSATISFACTION; never willingness to pay |
| explicit willingness to pay | text contract + taxonomy bump | a stated hypothetical is **not** WILLINGNESS_TO_PAY |
| existing paid solution | text contract + subject resolution | WILLINGNESS_TO_PAY (self-reported paid) + COMPETITIVE_SUPPLY |
| switching statement | text contract + scope + subject resolution | two products in one row, one `scope_id` today |
| abandonment or churn | text contract required | SOLUTION_DISSATISFACTION only if a reason is stated |

**Real gaps** (the roadmap artifact carries each with its minimal change):

| Id | Gap | Minimal change |
|---|---|---|
| G1 | no record kind for a review, post or tracker issue (`community_question` means a request for help) | registry migration, `RECORD_KINDS` entry, adapter |
| G2 | no quantity family for counts of reviews or issues | ADR on the ADR-034 test, CHECK-widening migration |
| G3 | no authorised contract for model-derived classification of first-person text | ADR (D-12, model-derived Signal and INFERRED contract), egress reviews, human labels |
| G4 | a stated willingness to pay has no dimension | taxonomy `@1.1.0` stated-intent member; no migration |
| G5 | scope admission has no product-to-product or narrower-into-broader edge | ADR plus registry bump |
| G6 | a problem cannot be an Opportunity subject | ADR gated on human labels (PARKED) |
| G7 | a product named in text cannot resolve to a canonical subject | ADR for reviewed aliases or model-derived linking |
| G8 | a single quote has no lineage-preserving Evidence form | deferred |
| G9 | the OBSERVED vocabulary guard lacks complaint, churn, cancel and switch words | extend with the first review or issue kind |

**Not gaps:** ClaimType, EvidenceDirection, EvidenceObservationCategory (it already lists
STATED_OPINION, REPORTED_BEHAVIOUR and review volume under OBSERVED_BEHAVIOUR), the independence states,
a star rating as an OBSERVED fact, the rating cutoff as a fingerprinted parameter, and severity,
workaround, feature demand, retention and switching intent — each is covered by an existing member or
correctly maps to nothing.

## 7. Independence readiness

**Why 0 groups.** No code path writes an independence group or a non-UNKNOWN state. The only
interpreter hard-codes `UNKNOWN`; `create_independence_group` exists and only tests call it. All 112
rows are `UNKNOWN`, so each claim's supporting evidence collapses into one group, and with one group the
aggregator is algebraically the pass-through baseline (Mission 1.43). `KNOWN_INDEPENDENT` needs the
four-clause proof standard, which no held pair meets because every held source measures a quantity only
its own platform records.

**A latent hazard, verified in the code.** `independence.py` gives each `KNOWN_DEPENDENT` lineage its own
group, and `levels.py` counts every group that is not the unknown bucket as a group of **established
independence**:

```python
independent_groups = [g for g in support_groups if g.kind is not GroupKind.UNKNOWN]
```

So a detector that finds two clusters of copies turns one unknown bucket into two
`DECLARED_DEPENDENT` groups, which then reach Level 2 and combine through saturation, although nobody
showed the two clusters are independent of each other. **Marking evidence as dependent would make it
look stronger.** Nothing writes a dependent state today, so nothing is wrong today; the fix (N05) must
land before any detector (N06) does.

**Dependence rules, designed and not activated.** Each keys on an exact or source-native fact, may only
move a record from `UNKNOWN` to `KNOWN_DEPENDENT`, and never infers independence from a different
platform, URL, timestamp or handle. No embeddings (D-12).

| Rule | Keys on |
|---|---|
| D-EXACT | normalised text hash within one source |
| D-REPOST | platform-native parent or crosspost field, or identical link plus text hash |
| D-SYNDICATION | publisher-declared canonical URL, or identical body hash across outlets |
| D-REVIEW-COPY | identical review body hash above a minimum length, across listings or platforms |
| D-THREAD | shared root thread or issue, or a publisher-declared duplicate, for claims restating the root only |
| D-SAME-AUTHOR | a per-source pseudonymous author key plus the same proposition |
| D-EVENT | explicit citation of one addressable event URL or native event id |

**What the schema lacks for them.** `scoring.evidence_independence_groups` has `id, workspace_id,
claim_id, basis, origin_reference, detection_method, created_at, created_by`: one group per origin per
claim fits, with `detection_method` holding `rule@version`. Missing: acquisition lineage fields (text
hash, native parent, root, declared canonical URL, duplicate-of; `raw_records.parent_record_id` exists
and is filled on **0 of 325** rows), a structured rule-version column, a cross-claim origin id, a place
for a `KNOWN_INDEPENDENT` proof, member roles and supersession.

**One user repeating a claim** cannot be detected, because author identity is deliberately never
acquired. The minimum would be a per-source keyed pseudonym computed at collection, never joined across
sources, behind a privacy review. It is not proposed for Mission 1.85.1.

## 8. Reliability readiness

**Why 4 assessments.** A reliability assessment is human-only, scoped to measurement × purpose (source,
resource, record kind, claim type, proposition kind), one current per scope, and bound late: the
evidence row's reliability column is empty on all 112 rows and is resolved at read time. The four are
the Wikimedia and TED detailed and witnessed scopes. The operator declined both Stack Exchange scopes
for insufficient documentation.

**For a new family.** Every new proposition kind is a new scope that resolves
`NO_APPLICABLE_ASSESSMENT` until a named person reviews it, which is correct. A review platform's scope
would be, for example, `(platform, reviews/public-listing, product_review, OBSERVED,
platform_published_reviews_in_rating_band)`. The reviewer needs first-party documentation of what counts
as a review, moderation and filtering, edit and deletion policy, fake-review and incentive policy, and
what the API returns against what exists. **A platform that does not document its filtering produces a
complete outcome with no row**, as Stack Exchange did. And reliability there describes how faithfully a
platform reports its own moderated corpus, never customer sentiment in the world.

## 9. Scoring readiness

**No score component is READY.**

| Component | Status (binding first) |
|---|---|
| Opportunity Score | IMPLEMENTATION (no weights, A-01 open, no crosswalk), EVIDENCE |
| Evidence Score | INDEPENDENCE (equals the pass-through baseline), RELIABILITY, IMPLEMENTATION (UNCALIBRATED; claim-level only) |
| Execution Score | IMPLEMENTATION (no formula), EVIDENCE |
| Research Completeness | IMPLEMENTATION (research space undefined) |
| Model Confidence | IMPLEMENTATION (self-reported model confidence refused) |
| Problem | RELIABILITY (Stack Exchange scopes declined), INDEPENDENCE |
| Market | INDEPENDENCE (one publisher), EVIDENCE, IMPLEMENTATION (every row UNCATEGORISED) |
| Momentum | IMPLEMENTATION (no half-life), EVIDENCE |
| Engagement | EVIDENCE (a request is not a reader), INDEPENDENCE |
| Desire, Utility, Retention, Virality, Competition Gap, Monetization, Distribution, Feasibility, Learning Value, per-market scores | EVIDENCE |

What ranking and selection need that does not exist: family formulas; weights and profiles; a versioned
crosswalk from the 12 scoring dimensions to the 14 evidence dimensions (six scoring dimensions have no
evidence dimension at all); an opportunity-level rollup across claims; a comparison procedure that does
not collapse score families and can say "not distinguishable"; a rule for comparing a PRODUCT-scope and
a CATEGORY-scope hypothesis; a scores schema and a recomputation policy (D-08); and a second persisted
hypothesis. The opportunity engine forbids ranking in its current version, and production scoring is
unavailable until a profile is CALIBRATED.

**The first honest comparison** (non-persisted, labelled UNCALIBRATED) becomes meaningful only when two
hypotheses share at least one counting evidence dimension at a comparable scope, and at least one
compared claim has two groups of established independence or evidence in both directions. Today the two
candidates share zero dimensions, so the honest output would be a side-by-side coverage list with no
numbers.

## 10. Dependency graph

```
N01 source qualification (F-REVIEW, F-ISSUE)            [1.85.1]
 └─ N02 record kind + quantity family ADR (G1 G2 G9)    [1.85.2]
     ├─ N03 collector, normalizer, extractor, OBSERVED template   [1.85.3]
     │   ├─ N07 human reliability review per new scope
     │   ├─ N10 taxonomy v1.1 + scope-admission ADR (G4 G5 G7)
     │   └─ N12 multiple formable hypotheses across ≥2 counting dimensions  (needs N07, N10)
     │       └─ N13 scoring crosswalk, formulas, weights, rollup, comparison procedure
     └─ N04 acquisition lineage fields for dependence
         └─ N06 deterministic dependence detection  (needs N05)
N05 level-hazard decision and engine fix                 [parallel, before N06]
N08 semantic extraction contract (G3)                    [parallel, operator decisions + human labels]
 └─ N09 second first-person family  (needs N03)
     └─ N11 INFERRED source-independent propositions from two apparatuses  (needs N06)
N14 calibration reference set + CALIBRATED profile  (needs N11, N12, N13)
 └─ N15 ranking and selection of one opportunity
```

**Critical path:** N01 → N02 → N03 → N07 → N12 → N13 → N14 → N15.
**Critical branches:** independence N02 → N04 → N06 → N11 → N14; second apparatus N08 → N09 → N11.

The requested chain maps onto it directly: *multiple evidence-backed opportunities* is N12;
*independence groups* is N06 and N11; *reliability* is N07; *scoring* is N13 and N14; *ranking* and
*selection* are N15. **Independence is on the path to selection twice**: calibration is impossible while
every claim has one group.

## 11. Recommended implementation order

By dependency, not by ease:

1. **N01 — Mission 1.85.1.** Qualify first-person structured sources. Nothing downstream can be built on
   a source that cannot be approved, and the families were chosen because they unlock missing dimensions
   without N08.
2. **N05 — can run beside it.** Decide and fix the level hazard. It is small, needs no source, and must
   precede any dependence writer.
3. **N02**, then **N03 and N04 together** for the one qualified source, adding the lineage fields at the
   same time as the collector so dependence facts are captured from the first record rather than
   back-filled.
4. **N07** — a human reliability review of the new scope, or its documented refusal.
5. **N06** — deterministic dependence detection (D-EXACT, D-REPOST, D-THREAD first, because they key on
   facts the source publishes).
6. **N08 — operator track, started early because it is long.** The semantic extraction contract needs a
   D-12 decision, egress reviews and human reference labels; F-DISCUSSION and most text dimensions wait
   on it.
7. **N10**, then **N12**: at least two hypotheses across two counting business dimensions.
8. **N09 and N11**: a second first-person apparatus and source-independent propositions, which is what
   finally makes the aggregator differ from the baseline.
9. **N13, N14, N15**.

**What is deliberately not next:** another market-size or activity source (F-PROCUREMENT,
F-STATISTICS-TRENDS), more Stack Overflow questions (F-QA adds no dimension and its reliability scopes
were declined), and F-DISCUSSION (richest, but every business dimension in it needs N08 and its terms
were never retrieved).

## 12. The exact scope of Mission 1.85.1

**Mission 1.85.1 — First-Person Structured Evaluation Source Qualification V1.**

**Goal.** Establish, on retrieved first-party documents, whether at least one source in F-REVIEW or
F-ISSUE can be approved under `local-private-research-v1` for a documented official route that exposes a
source-native rating, label or duplicate relation; select exactly one, or record a documented no-go.

**In scope**

1. **Freeze the candidate list before any retrieval.** The registered `apple-app-store`, `google-play`,
   `steam` and `github`, plus at most four unregistered candidates named in the brief. Unregistered names
   are unverified until retrieved.
2. **Retrieve documentation only:** first-party terms, API documentation, robots directives and
   licences. No research-data request.
3. **For each candidate, record:**
   - the six activity assessments (automated access, API use, commercial use, storage, derived
     analytics, model processing);
   - the route, field selection and rate limits;
   - whether the official route exposes the rating, label or duplicate field.
4. **Append a `local-private-research-v1` review only where retrieved evidence supports a verdict.**
   Silence is `NOT_ADDRESSED`, never permission.
5. **Register an unregistered candidate** only if its review can be written on retrieved evidence.
6. **Select exactly one source and resource,** with its exposed structured fields and the proposition it
   could support deterministically.

**Out of scope:** any collector, normalizer, extractor, record kind or migration; any research-data
request; any model call or embedding; reliability assessments, independence groups, scores or
opportunities; TED synthesis; gates v1.2.0 to v1.6.0.

**Stop rule.** If no candidate reaches an approving local verdict with all six activities granted, stop
and hand the operator a two-way decision: start the semantic-extraction contract track (N08) so that
F-QA or F-DISCUSSION text becomes usable, or take a documented product decision that would satisfy
GitHub's open-access publication condition.

**Done when:**

- every frozen candidate has a recorded outcome with first-party citations;
- one source and resource is selected, or the no-go is recorded;
- roadmap node N01 is marked done and N02's family is fixed.

## Schema and ontology changes that are actually necessary

**None in Mission 1.85.1.** For the first qualified source:

- a new record kind (G1);
- one quantity-family ADR with its CHECK migration (G2);
- the guard vocabulary extension (G9);
- acquisition lineage fields for dependence (N04);
- the level-hazard engine fix (N05), which is code rather than schema.

Everything else (G3 to G8) is deferred behind its own decision.

## Verification

- The roadmap artifact is checked against the repository by
  `test_business_evidence_roadmap.py` (26 tests):
  - every named source exists in the catalog and every named dimension in `EvidenceDimension`;
  - every supported dimension is one a signal type actually maps to, with a staleness alarm for the
    dimensions recorded as missing;
  - the dependency graph is acyclic and every path step depends on the previous one;
  - no score component is READY, and no dependence rule yields independence;
  - Mission 1.85.1's scope excludes implementation and models.
- Locally: ruff format and check clean over 1190 files; the source registry validates (29 sources, 45
  evidence records, 0 warnings); the three gates that read documentation re-derive (convergence
  contract, signal coverage, the V10 stage 6 diagnostic); the opportunity-engine suite passes
  **4035 tests** (4009 before, plus the 26 new ones). No other code changed, so the other suites and the
  semantic-generation probes were not re-run; CI runs every gate.
- The canonical counters above were read before and after, unchanged.

## Recorded debt, not fixed here

- Cross-field intervention-vocabulary displacement (gate v1.6.0).
- Inherited assertion pronoun continuation (gates v1.4.0 to v1.6.0).
- Lexical intervention-class grounding is not semantic validity.
- **Documentation drift found by the agents:**
  - `mapping.py` and `dimensions.py` docstrings miscount empty mappings;
  - `demand-side-source-coverage-v1.md` still calls TED a willingness-to-pay candidate and says nothing
    is implemented;
  - several `docs/CLAUDE.md` Stack Exchange statements predate its approval;
  - D-03 blocker 5 and the calibration plan still cite an outcome-resolution target and a Brier score
    that Mission 1.37 rejected;
  - the scoring README contradicts the aggregation framework on decay and levels;
  - `MARKET_ACTIVITY` means different things as an observation category and as an evidence dimension;
  - `calibration-feasibility-audit-v1.json` measured 57 evidence rows and is stale against 112.

**Stopped here.** No source was collected, no review appended, no synthesis run, no Opportunity #2, and
Mission 1.85.1 was not started.
