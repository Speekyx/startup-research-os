# Mission 1.46 — Independent Statistical Evidence Route Feasibility V1

**Primary outcome: `COMMON_UPSTREAM_SOURCE_PREVENTS_INDEPENDENCE`** (§34 C).

Both candidate routes fail, and **each fails on more than one gate**. FRED
republishes the exact World Bank series this repository already holds. Eurostat
is named *by the World Bank* as one of its own sources for that series — and
measures a different population on a different date anyway.

**No route was selected. §25 forbids a least-bad fallback, so none was taken.**

```text
research data requests    0        statistical documentation requests  5 (1 METADATA_ONLY)
model calls               0        governance document requests        0
independence groups       0        research counters                   unchanged
```

The mandatory precondition was completed first: the operator's TED local review
v3 acceptance is recorded, and **17 of 17 post-write checks passed**.

Artifacts:
[feasibility record](../data/independent-statistical-route-feasibility-v1.md)
·
[holdings baseline](../data/statistical-holdings-baseline-v1.json).

---

## §35 — Final report

### The precondition

**1. Did the branch contain the full state through Mission 1.45?** **Yes.** All
six commits 1.43 → 1.45; the Wikimedia convergence contract; the convergent human
reliability assessment; rubric provenance on 2 assessments; TED local v3 and
commercial v6; migration 0033 applied (33 total); 2 `OPERATOR_CORRESPONDENCE`
evidence rows; `docs/CLAUDE.md` 1.79 and `PROJECT_MANIFEST.md` 1.78.

**2. Was PR-stack state used without requiring premature merges?** **Yes.**
Nothing was merged and no PR was reordered.

**3. Did TED local review v3 exist?** **Yes**, with its four conditions.

**4. Was operator acceptance legitimately recorded for v3?** **Yes.** Exactly one
new `HUMAN_CONFIRMATION` row, written through `record_verifications(conn, records)`
with a `ConditionVerificationRecord` — the supported domain API. `verifier`
`local-operator`, `result` `SATISFIED`, `reference`
`docs/data/ted-eu-official-reuse-response-v1.md`, and the operator's text stored
**byte-for-byte**, asserted by comparing the persisted `reason` against the
supplied text rather than by inspection.

`verifier_version` is **`ted-v3-official-reuse-acknowledgement-v1`**. Mission 1.45
had defined no canonical v3 identifier, so the preferred shape applied.
`acknowledgement-v1` was **not** reused: that identifier names the materially
different v2 text, and this field records *which acknowledgement was signed*
rather than a program version.

The v2 acceptance was not replayed, `record_ted_operator_acceptance.py` was not
repointed, no boolean was set directly, no ad-hoc SQL ran, and nothing was
recorded under the commercial profile.

**5. Did TED become eligible again under `local-private-research-v1`?** **Yes.**
All four v3 conditions `SATISFIED`, zero unsatisfied, no blocking reasons, and
`build_authorization('ted-eu', 'local-private-research-v1')` returns a context at
**review v3**.

**6. Did TED commercial remain `REQUIRES_REVIEW`?** **Yes.**

**One operational consequence, recorded rather than acted on.** A verification
row lives only in `registry.source_condition_verifications` — it does not travel
by git, which is exactly why `record_ted_operator_acceptance.py` was written for
the v2 acceptance. **The v3 acceptance therefore exists only in this deployment**,
and a second machine would need the operator to record it there too. No v3 replay
script was written: the brief forbids repointing the v2 one, and creating a new
one was not asked for and is a decision about a carefully-argued script rather
than a side effect of this mission.

The other checks held: the context carries only `ted-search-api` and
`ted-open-data-sparql`; `ted-bulk-xml` is absent; all eight personal-data fields
stay excluded and none is allowed; `redistribution` is `NOT_PERMITTED` locally;
H-36A existence stays `NOT_ESTABLISHED` with no `NO_RIGHT_EXISTS`; the H-36
reading is Mission 1.45's reconciled one; TED's `0.5` and `0.55` are unchanged and
unsuperseded; **17 of 17.**

### Baselines

**7. Exact research baseline?** Verified against the deployment and matching the
brief on every value: RawRecords **325**, NormalizedRecords **325**, Signals
**33**, Claims **43**, ClaimRevisions **44**, Evidence **57**,
ReliabilityAssessments **4**, basis rows **12**, independence groups **0**,
Opportunities/revisions/links **1 / 1 / 7**, Embeddings **0**, sources **29**,
`scoring.scores` **absent**, `REFERENCE_PROFILE_V1` **UNCALIBRATED**,
Problem-Family **PARKED**.

**8. Exact aggregation baseline?** Confirmed against the live deployment via the
audit's own `--check`: scorable multi-Evidence Claims **8**, maximum real Evidence
cardinality **4**.

**9. Claims with >1 support group?** **0.**
**10. Cases differing from B-2?** **0.** Established independence **0**,
contradiction **0**, temporal **0**.

### Holdings (§0, measured before selection)

**11. Current World Bank holdings?** 6 RawRecords, 6 NormalizedRecords, **one
metric — `SP.POP.TOTL`** at `indicator/SP.POP.TOTL`, geographies `DEU` and `FRA`,
periods 2018/2019/2020, 4 Claims, 4 Evidence rows. All four Evidence rows carry
`reliability = NULL`, `independence_state = UNKNOWN`, no group — **`NON_SCORABLE`**.

**12. Current Eurostat holdings?** **Nothing.** 0 RawRecords, 0 Claims, 0 Evidence.
**13. Current FRED holdings?** **Nothing.** 0 / 0 / 0.

The baseline was frozen *before* any candidate was considered, because a candidate
chosen first and justified afterwards against whatever is held is a
rationalisation.

### Governance (§1, read live)

**14–16. World Bank, Eurostat, FRED.** All three **`APPROVED_WITH_CONDITIONS`
under `local-private-research-v1` with zero unsatisfied conditions and no blocking
reasons.** World Bank: `attribution-surface`, `dataset-licence-allowlist`,
`microdata-excluded`. Eurostat: `attribution-surface`, `geographic-exclusion`,
`trade-data-exclusion`. FRED: `copyrighted-series-excluded`, `fred-api-key`
(configured), `fred-endorsement-notice`.

**Governance is not the blocker, and saying so matters.** A mission that reported
an engineering gap as its finding would be reporting the second obstacle and
hiding the first.

**17. Exact resource readiness?** Eight facts, not collapsed:

| | eligible | resource registered | resource authorised | collector | normalizer | extractor | interpreter | reliability scope |
|---|---|---|---|---|---|---|---|---|
| `world-bank` | yes | yes | yes (3) | yes | yes | yes | yes | **no** |
| `eurostat` | yes | **no** | **no** | **no** | **no** | **no** | **no** | **no** |
| `fred` | yes | **no** | **no** | **no** | **no** | **no** | **no** | **no** |

World Bank's three authorised resources are `indicator/SP.POP.TOTL`,
`indicator/NY.GDP.MKTP.CD`, `indicator/IT.NET.USER.ZS`.

### The candidates

**18. World Bank metrics considered?** `SP.POP.TOTL` — the only one held, and the
only one for which a same-proposition partner was plausible. The other two
authorised indicators were not pursued because no partner survived provenance for
the first.

**19. Eurostat metrics considered?** Population under the `demo_pop` domain
("Population on 1 January").

**20. FRED series considered?** `SPPOPTOTLDEU` (guessed, **HTTP 404**, does not
exist) and then **`POPTOTDEA647NWDB`**, "Population, Total for Germany".

**21. Which pairs reached serious review?** Both: `world-bank + fred` and
`world-bank + eurostat`.

**22–25. Semantics, geography, time, unit.**

| | World Bank `SP.POP.TOTL` | Eurostat population | FRED `POPTOTDEA647NWDB` |
|---|---|---|---|
| **concept** | de facto population, "all residents regardless of legal status or citizenship" | **usually resident** population | *the World Bank series* |
| **reference date** | **midyear** estimates | **1 January** (or 31 Dec previous year) | midyear |
| **geography** | `DEU`, `FRA`, kind COUNTRY, canonical `DE`/`FR` | same two countries, Eurostat geo codes | Germany |
| **unit** | persons, `unit_state` NOT_PUBLISHED, integers | integer persons | "Persons, Not Seasonally Adjusted" |
| **frequency** | annual | annual | annual |

### Upstream provenance (§5 — the decisive section)

**26. Upstream provider for World Bank?** From the World Bank's own indicator
metadata, `sourceOrganization`, four sources:

> World Population Prospects, United Nations (UN) … publisher: UN Population
> Division; Statistical databases and publications from national statistical
> offices, National Statistical Offices (NSOs) … ; **Eurostat: Demographic
> Statistics, Eurostat (ESTAT) … publisher: Eurostat**; Population and Vital
> Statistics Report (various years), United Nations (UN) … publisher: UN
> Statistics Division

**The World Bank does not produce this measurement.** For EU member states it
reaches the World Bank through the national statistical offices *and through
Eurostat*.

**27. Upstream provider for the Eurostat candidate?** From Eurostat's own ESMS
metadata: *"Population data are collected by Eurostat from National Statistical
Institutes"*, transmitted under **Regulation (EU) No 1260/2013**. **Eurostat
compiles and disseminates; it does not enumerate Germany's population.** The
producers are Destatis and INSEE.

**28. Upstream provider for the FRED candidate?** FRED's own series page: Source
**"World Bank"**, Release **"World Development Indicators"**, **Source Code
`SP.POP.TOTL`**, and a suggested citation reading *"World Bank, Population, Total
for Germany [POPTOTDEA647NWDB], **retrieved from** FRED"*.

**29. Does any FRED candidate directly source World Bank?** **Yes, by the
publisher's own declaration.** It is not a similar series; it is *the* series,
carrying the identical source note word for word.

**30. Does any Eurostat candidate share a World Bank upstream?** **Yes, twice
over.** Eurostat is a *named source of* the World Bank series, and underneath both
sit the same national statistical institutes.

### The two gates (§7)

**31. Any pair semantically equivalent?** **Yes — `world-bank + fred`**, and that
is precisely the problem: it matches because it is the same measurement.

**32. Any pair provenance-independent?** **No. Neither.**

**33. Any pair YES + YES?** **No.**

| pair | same proposition? | independent provenance? | verdict |
|---|---|---|---|
| `world-bank + fred` | **YES** | **NO** | `DEPENDENT_REPUBLICATION` |
| `world-bank + eurostat` | **NO** | **NO** | `COMMON_UPSTREAM_SOURCE` |

**34. Any candidate rejected only because provenance is unknown?** **No.** Neither
was rejected on an *unknown* — both were rejected on provenance the publishers
themselves **document**. That distinction matters: an unknown could be resolved by
more reading, and these cannot.

**35. Any candidate rejected because same upstream?** **Both.**

**36. Any candidate rejected because of semantic mismatch?** **`world-bank +
eurostat`**, independently of its provenance failure: de facto vs usually
resident, and midyear vs 1 January. **A shared year label is not a shared
reference date** — §16's trap exactly.

### Claim architecture (§10)

**37. Does cross-source convergence fit OBSERVED Claims?** **Not as they stand.**
The held Claims are source-attributed — *"World Bank Open Data reported that
`SP.POP.TOTL` for `Germany` increased between `2018` and `2019` by 187180"* — and
`proposition_facts` carries `source_id = world-bank` as **proposition identity**.
Two publishers cannot both support one source-attributed proposition.

**38. Or does it require an INFERRED Claim?** **The question was not reached, and
that is the honest answer.** Two routes would have existed — a deterministic
multi-source OBSERVED convergence contract in the ADR-035 line, or an INFERRED
Claim — and **`INDEPENDENT_ROUTE_REQUIRES_INFERRED_STATISTICAL_CLAIM` is
deliberately NOT the outcome**: the blocker sits upstream of the Claim
architecture, not inside it. Reporting B would misattribute the failure to a layer
that never got a chance to fail.

**39. Is a new convergence contract needed?** Not decidable from here, and not
decided. It would only become the question once a genuinely independent pair
existed. **Source attribution was not proposed for deletion** — Mission 1.38
established that removing `source_id` merges unrelated observations.

**40. Is a geography mapping needed?** **No, and `STATISTICAL_GEOGRAPHY_MAPPING_REQUIRED`
is not reported.** The held records already carry canonical ISO-3166-1-alpha-2
codes from a reviewed table, and a country-level alignment would have been
defensible. The routes died upstream of it.

**41. Is unit conversion needed?** **No.** Both are counts of persons at scale 1.
**42. Is the conversion already canonically supported?** Moot — **nothing was
converted, because nothing was compared.** No FX, no deflator, no rescaling.

### Reliability and scorability (§20)

**43. Applicable assessment for candidate A?** **`NO_APPLICABLE_ASSESSMENT`.** No
reliability exists for `world-bank` at `source_reported_metric_period_change`; its
four Evidence rows are `NON_SCORABLE`.
**44. Candidate B?** `NO_APPLICABLE_ASSESSMENT` for both Eurostat and FRED — no
Evidence exists at all.

**45. Would future Evidence be immediately scorable?** **No.** A perfect
independence route would still have been `NON_SCORABLE_MISSING_RELIABILITY`, which
§20 says is acceptable. It is recorded so a future mission budgets for the human
review rather than discovering it after acquiring data. **No assessment was
created.**

### Architecture (§22)

**46. Can the current independence model represent two real groups?** **Yes,
without any architecture change.** `_group_key` puts a `KNOWN_INDEPENDENT` item in
its **own** group keyed by `evidence_id`, so two such rows on one Claim form two
groups and enter saturation as `S = 1 - (1 - g_A)(1 - g_B)`, which can differ from
`max(g_A, g_B)`. Proven here on non-empty fixtures for **all three** states, so
every branch executes; Mission 1.43's arithmetic was not rediscovered.

`EvidenceIndependenceState` still has exactly three members and **no fourth was
invented**. (The constructor also refuses `KNOWN_INDEPENDENT` together with an
`independence_group_id`, because a group id asserts a shared lineage.)

**The model is not the gap. What is missing is a real source pair entitled to
inhabit the shape.**

**47. Was any independence group persisted?** **No. 0 before, 0 after.**

### What was and was not done

**48. Any research data fetched?** **`RESEARCH_DATA_REQUESTS = 0`.**

**49. Any metadata-only requests?** **One**, recorded explicitly: the World Bank
indicator metadata endpoint, which returns the indicator's description and source
list and **no observations**. **No RawRecord was persisted.**

**50. Documentation requests?** **`STATISTICAL_DOCUMENTATION_REQUESTS = 5`**
(World Bank indicator page; World Bank indicator metadata; a FRED URL that 404'd;
the FRED series page; Eurostat ESMS metadata). `GOVERNANCE_DOCUMENT_REQUESTS = 0`.
One navigational web search located the correct FRED series id after a guess
returned 404; **it established nothing** — every finding cites the first-party page
it led to (§4).

**51–55. Any RawRecord / Signal / Claim / Evidence / ReliabilityAssessment
created?** **None.**
**56. Any calibration label?** **No.**
**57. Any parameter fitted?** **No.**
**58. Did `REFERENCE_PROFILE_V1` remain UNCALIBRATED?** **Yes.**
**59. Any Score?** **No** — `scoring.scores` does not exist.
**60. Any Opportunity change?** **No** — 1 / 1 / 7.
**61. Model calls?** **Zero. 0.00 USD.**
**62. Embeddings?** **Zero**, and no similarity machinery was used to decide any
equivalence (§11). Every judgement is document-backed and auditable.
**63. Problem-Family status?** **PARKED.**

**64. Exact canonical counters before/after?** **Unchanged, every one**, verified
after the TED gate completion and again at the end: 325 / 325 / 33 / 43 / 44 / 57 /
4 / 12 / 0 / 1 / 1 / 7 / 0 / 29, `scoring.scores` absent.

**65. Candidate matrix?** Above, and frozen in the feasibility record.

**66. Selected route, if any?** **None.**

**67. Exact independence documentary basis?** Three first-party documents,
retrieved 2026-09-04: the World Bank indicator metadata `sourceOrganization`
field; the FRED series page for `POPTOTDEA647NWDB` (Source, Release, Source Code,
suggested citation); the Eurostat ESMS metadata for the population domain
(reference date, and collection from National Statistical Institutes under
Regulation (EU) No 1260/2013).

**68. Exact remaining engineering gap?** For the record rather than as a
recommendation: Eurostat and FRED each need a registered and authorised resource,
a collector and a normalizer — none of which exists. **`STATISTICAL_RESOURCE_OR_COLLECTOR_GAP`
is not the outcome**, because the routes failed on provenance and semantics before
that gap was ever load-bearing.

**69. Primary outcome?** **`COMMON_UPSTREAM_SOURCE_PREVENTS_INDEPENDENCE`.**

**70. Recommended next mission?** See below.

---

## The structural finding

**The two failures have one cause, and it is not bad luck.**

For official macro statistics the international publishers are **distribution
layers over national producers**:

```text
Destatis / INSEE          the measurement happens ONCE, here
        |
        +-- transmitted under Regulation (EU) 1260/2013 --> Eurostat
        |                                                      |
        +-- via NSOs ------------------------------------------+--> World Bank WDI
                                                                        |
                                                                        +--> FRED
```

So **"add a second statistical publisher" cannot produce a second provenance group
for a national aggregate, however many publishers are added.** Every one of them is
a route to the same measurement. Independence over this evidence family would
require two genuinely different measurement *apparatuses* observing the same
phenomenon — not two republications of one national submission.

That is a more useful result than a route would have been, because it closes a
direction rather than one pair.

---

## §36 — Next

**Not an acquisition mission**, and **not calibration.**

Acquiring Eurostat or FRED population would add real rows that cannot become a
second provenance group — corpus expansion of exactly the kind Mission 1.43 proved
cannot help. And Mission 1.43's algebraic finding is untouched: with one provenance
group the full aggregator remains the B-2 pass-through baseline, so labelling would
ask a person to compare cases the aggregator cannot distinguish.

**§14's qualified alternative: none inside the eligible statistical portfolio.**
The `economic_data` family eligible under `local-private-research-v1` is exactly
`{world-bank, eurostat, fred}` — the three publishers just shown to share
producers. There is no fourth to promote, and naming one would mean reaching
outside the eligible set or inventing a candidate. **A slot was left empty rather
than filled**, which is what §25 asks for.

**The question worth a mission** is upstream of any acquisition: whether a bounded
proposition can be defined that two **genuinely different measurement apparatuses
already in this corpus** both bear on, without weakening proposition identity. This
repository already holds separate apparatuses — a platform counting content
requests, a community publishing questions, a procurement journal publishing award
values. That is a proposition-design and convergence-contract question in the
ADR-035 line, and it may conclude that the INFERRED layer is required — a decision
this mission does not make.

**It was not started.**

---

## Repairs

**Four of Mission 1.15.6.1's acceptance tests failed on the v3 record**, and every
one kept its property and dropped the incidental number. They asserted that
exactly ONE acceptance exists and that it is scoped to review **v2** — written
when v2 was the only version there had ever been.

The property they guard is *§19: one decision, not a history of changes of mind.*
**Two acceptances of two materially different statements are not a change of
mind**; two acceptances of the SAME statement would be. So the assertions are now
per review version: at most one acceptance each, every version owning its own row,
no version inheriting another's, and the current review satisfied only if a
decision was made *about it*. The profile scope — never commercial — was left
absolute, because that genuinely must not depend on the deployment.

The same shape as Missions 1.31.1, 1.32, 1.38, 1.40, 1.41, 1.45: **a test asserting
a count that can legitimately grow is a test asserting the project never
progresses** (`testing-strategy.md` §68).

## What this mission did not establish

- **Not that Eurostat or FRED are poor sources.** Both are eligible today with
  zero unsatisfied conditions and both document their statistics carefully. What
  they are not, for this measurement, is *independent of the World Bank*.
- **Not that no independence-capable route exists anywhere.** This is a finding
  about one measurement family over two candidate pairs.
- **Not a contradiction.** No two values were compared, and nothing was labelled
  `CONTRADICTS`.
- **Not a reliability judgement**, and not an architecture gap: the model can hold
  two groups today.
