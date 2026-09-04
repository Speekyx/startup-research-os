# Independent statistical evidence — route feasibility

**`independent-statistical-route-feasibility@1.0.0`**, Mission 1.46. Rendered from the authored record; edit the JSON, not this page.

**Primary outcome: `COMMON_UPSTREAM_SOURCE_PREVENTS_INDEPENDENCE`.**

NONE. Both candidate routes fail, and each fails on more than one gate. Section 25 forbids a least-bad fallback, so no route is frozen and no acquisition is preregistered.

---

## The rule that decided it

DIFFERENT PUBLISHERS ARE NOT INDEPENDENT EVIDENCE. Independence is a fact about the measurement lineage, not about the API hostname, the organisation name, the database or the publication page. Both candidates were rejected on lineage that the publishers themselves document.

## The two-gate matrix

Only **YES + YES** qualifies (§7).

| pair | same proposition? | independent provenance? | verdict |
|---|---|---|---|
| `world-bank + fred` | **YES** | **NO** | `DEPENDENT_REPUBLICATION` |
| `world-bank + eurostat` | **NO** | **NO** | `COMMON_UPSTREAM_SOURCE` |

## Provenance chains

*Who produced the measurement, not who published the endpoint (§5).*

### `world-bank/SP.POP.TOTL`

**Publisher:** World Bank · **Dataset:** World Development Indicators

Stated sources:

- World Population Prospects, United Nations (UN), publisher: UN Population Division
- Statistical databases and publications from national statistical offices, National Statistical Offices (NSOs), publisher: National Statistical Offices
- Eurostat: Demographic Statistics, Eurostat (ESTAT), publisher: Eurostat
- Population and Vital Statistics Report (various years), United Nations (UN), publisher: UN Statistics Division

**Underlying producer.** NOT the World Bank. For EU member states the measurement originates with the national statistical institutes and reaches the World Bank through the NSOs and through Eurostat, both of which the World Bank names.

*Basis:* World Bank indicator metadata endpoint, sourceOrganization field, retrieved 2026-09-04. METADATA_ONLY: the endpoint returns the indicator's description and source list and no observations.

### `eurostat/population`

**Publisher:** Eurostat · **Dataset:** European demographic statistics (demo_pop domain)

Stated sources:

- Population data are collected by Eurostat from National Statistical Institutes
- Member States transmit population data under Regulation (EU) No 1260/2013

**Underlying producer.** The national statistical institutes of the Member States. Eurostat compiles and disseminates what they transmit under a legal obligation; it does not itself enumerate the population of Germany or France.

*Basis:* Eurostat ESMS metadata for population (demo_pop_esms), retrieved 2026-09-04.

### `fred/POPTOTDEA647NWDB`

**Publisher:** Federal Reserve Bank of St. Louis (FRED) · **Dataset:** World Development Indicators

Stated sources:

- Source: World Bank
- Release: World Development Indicators
- Source Code: SP.POP.TOTL

**Underlying producer.** The World Bank series this repository already holds. FRED is the distribution layer and says so: its own suggested citation reads 'World Bank, Population, Total for Germany [POPTOTDEA647NWDB], retrieved from FRED'.

*Basis:* FRED series page for POPTOTDEA647NWDB, retrieved 2026-09-04.

## The candidate pairs

### world-bank + fred — `DEPENDENT_REPUBLICATION`

- **A:** World Bank SP.POP.TOTL, Population total, Germany, annual
- **B:** FRED POPTOTDEA647NWDB, Population Total for Germany, annual, persons, not seasonally adjusted

**Same proposition? YES.** Trivially yes, and that is exactly the problem. FRED's own page names Source Code SP.POP.TOTL and reproduces the World Bank source note word for word -- 'Total population is based on the de facto definition of population ... The values shown are midyear estimates.' It is not a similar measurement; it is the SAME series.

**Independent provenance? NO.** Direct republication, documented by the publisher. FRED names the World Bank as Source, World Development Indicators as Release, and SP.POP.TOTL as Source Code, and its suggested citation credits the World Bank as the author and FRED only as the retrieval point.

**If forced, independence would be `KNOWN_DEPENDENT`.** Section 13 answers this case by name: a candidate series identifying the World Bank as its source is KNOWN_DEPENDENT for a World Bank comparison, and the St. Louis Fed API endpoint is not independent production. Adding it would put two copies of one measurement into one Claim and, because independence would be KNOWN_DEPENDENT rather than established, they would collapse into one group anyway -- producing exactly the pass-through result this arc is trying to escape, at the cost of a false corroboration claim.

### world-bank + eurostat — `COMMON_UPSTREAM_SOURCE`

- **A:** World Bank SP.POP.TOTL, Population total, Germany and France, annual, DE FACTO population, MIDYEAR estimates
- **B:** Eurostat population, Germany and France, annual, USUALLY RESIDENT population, on 1 JANUARY

**Same proposition? NO.** Two independent mismatches, either of which is disqualifying. POPULATION UNIVERSE: the World Bank counts the DE FACTO population, 'all residents regardless of legal status or citizenship'; Eurostat's recommended definition is the USUALLY RESIDENT population. REFERENCE DATE: the World Bank publishes MIDYEAR estimates; Eurostat publishes population 'on 1 January of the year in question (or on 31 December of the previous year)'. A shared year label is not a shared reference date, which is the section 16 trap exactly.

**Independent provenance? NO.** The World Bank names 'Eurostat: Demographic Statistics' as one of its four stated sources for SP.POP.TOTL. So for EU member states Eurostat is UPSTREAM OF the World Bank series rather than beside it. And underneath both sits the same producer: Eurostat compiles what the national statistical institutes transmit under Regulation (EU) No 1260/2013, and the World Bank separately names 'Statistical databases and publications from national statistical offices'. For Germany and France the measurement originates in one place and reaches this repository by two paths.

**If forced, independence would be `UNKNOWN, and it would have to stay UNKNOWN`.** It fails BOTH gates of section 7 independently. Even if the semantics could be reconciled -- and they cannot be without changing what the proposition asserts -- the provenance is shared, and section 6 requires the absence of a documented common upstream series before KNOWN_INDEPENDENT may be recorded. The documented common upstream is not absent; it is named by the World Bank itself.

## The structural finding

THE TWO FAILURES HAVE ONE CAUSE, AND IT IS NOT BAD LUCK. For official macro statistics the international publishers are DISTRIBUTION LAYERS over national producers. FRED republishes the World Bank; the World Bank compiles the UN Population Division, the national statistical offices and Eurostat; Eurostat compiles what the national statistical institutes transmit under a Regulation. The measurement of how many people live in Germany is produced ONCE, by Destatis, and every one of these publishers is a route to that one measurement. So 'add a second statistical publisher' cannot yield a second provenance group for a national aggregate, however many publishers are added. Independence over this evidence family would require two genuinely different measurement APPARATUSES observing the same phenomenon, not two republications of one national submission.

## Governance and readiness

GOVERNANCE IS NOT THE BLOCKER, AND SAYING SO MATTERS. All three sources are eligible today with zero unsatisfied conditions. Eurostat and FRED have a real RESOURCE and COLLECTOR gap -- zero authorised datasets and no collector -- but that gap was never reached, because both routes failed on provenance and semantics first. A mission that reported the engineering gap as the finding would be reporting the second obstacle and hiding the first.

| source | SOURCE_ELIGIBLE | RESOURCE_REGISTERED | RESOURCE_AUTHORISED | COLLECTOR_IMPLEMENTED | NORMALIZER_IMPLEMENTED | SIGNAL_EXTRACTOR_IMPLEMENTED | CLAIM_INTERPRETER_AVAILABLE | RELIABILITY_SCOPE_REVIEWED |
|---|---|---|---|---|---|---|---|---|
| `world-bank` | yes | yes | yes | yes | yes | yes | yes | **no** |
| `eurostat` | yes | **no** | **no** | **no** | **no** | **no** | **no** | **no** |
| `fred` | yes | **no** | **no** | **no** | **no** | **no** | **no** | **no** |

## Geography

GEOGRAPHY IS NOT THE BLOCKER HERE. The held World Bank records carry geography kind COUNTRY with source codes DEU and FRA and canonical ISO-3166-1-alpha-2 codes DE and FR, already mapped by a reviewed table. Eurostat publishes the same two countries under its own geo codes. A country-level alignment would be defensible and would not have needed a new mapping table. STATISTICAL_GEOGRAPHY_MAPPING_REQUIRED is NOT reported: the routes died upstream of it. An aggregate route -- EU27, euro area, 'Europe' -- would be a different question and was not pursued, because no held World Bank record is an aggregate.

## Unit

UNIT IS NOT THE BLOCKER EITHER, AND NO CONVERSION WAS CONTEMPLATED. The World Bank records carry unit_state NOT_PUBLISHED with integer person counts; FRED states 'Persons, Not Seasonally Adjusted' for the same series. Both are counts of people at scale 1, so no scaling, no FX, no deflator and no rescaling would have been required. Nothing was converted, because nothing was compared.

## Temporal

TIME BASIS IS A REAL BLOCKER FOR THE EUROSTAT PAIR. World Bank SP.POP.TOTL is a MIDYEAR estimate; Eurostat population is on 1 JANUARY. Those are different reference instants for the same year label, and the section 16 example list names this shape directly. For the FRED pair the time basis matches perfectly -- because it is the same series.

## Revision

Both publishers revise. The World Bank's held records carry source_last_updated 2026-07-13, and Eurostat republishes as Member States retransmit under Regulation (EU) No 1260/2013. Divergent same-period values between two publishers of the SAME lineage would be a vintage difference rather than a disagreement about the world, and would not be a contradiction. Nothing was recorded as CONTRADICTS and no two values were compared.

## Reliability

- **`world-bank`** — NO_APPLICABLE_ASSESSMENT. The four held World Bank Evidence rows carry reliability NULL and are NON_SCORABLE. No assessment exists for source_reported_metric_period_change under world-bank.
- **`eurostat`** — NO_APPLICABLE_ASSESSMENT. No Evidence exists.
- **`fred`** — NO_APPLICABLE_ASSESSMENT. No Evidence exists.

A perfect independence route would still have been NON_SCORABLE_MISSING_RELIABILITY, and section 20 says that is acceptable. It is recorded here so a future mission budgets for the human review rather than discovering it after acquisition. NO ASSESSMENT WAS CREATED.

## Claim architecture

The held World Bank Claims are OBSERVED and source-attributed: 'World Bank Open Data reported that "SP.POP.TOTL" for "Germany" increased between "2018" and "2019" by 187180.' Their proposition_facts carry source_id = world-bank as PROPOSITION IDENTITY.

**TWO PUBLISHERS CANNOT BOTH SUPPORT ONE SOURCE-ATTRIBUTED OBSERVED PROPOSITION, because the publisher is part of what the proposition asserts. A second source would form its own Claim, not a second Evidence row on this one.**

- A. A deterministic MULTI-SOURCE OBSERVED convergence contract asserting a bounded fact common to both source reports, in the shape ADR-035 established for the single-source case. This would need a new proposition kind; it must NOT be reached by deleting source_id from the existing one, which Mission 1.38 established would merge unrelated observations.
- B. An INFERRED Claim asserting a bounded real-world statistical proposition that both publishers bear on.

NEITHER WAS NEEDED, because no pair reached this question. Had a semantically equivalent and provenance-independent pair existed, route A would have been attempted first and route B would have required the INFERRED layer this repository has deliberately not built. Section 10's INDEPENDENT_ROUTE_REQUIRES_INFERRED_STATISTICAL_CLAIM is therefore NOT the outcome: the blocker is upstream of the Claim architecture, not inside it.

## Can the model represent two groups?

THE MODEL IS READY AND IS NOT THE GAP. `_group_key` in the aggregation package puts a KNOWN_INDEPENDENT item in its OWN group keyed by evidence_id, so two KNOWN_INDEPENDENT Evidence rows on one Claim form TWO groups and enter saturation as S = 1 - (1 - g_A)(1 - g_B), which can differ from max(g_A, g_B). Mission 1.43 already proved that with fixtures and this mission did not rediscover it. EvidenceIndependenceState has exactly three members and no fourth was invented. Note the constructor refuses KNOWN_INDEPENDENT together with an independence_group_id, because a group id asserts a shared lineage.

**What is missing:** A REAL SOURCE PAIR ENTITLED TO THAT SHAPE. Nothing was persisted: 0 independence groups before and after.

## A qualified alternative

**NONE INSIDE THE ELIGIBLE STATISTICAL PORTFOLIO. The economic_data family eligible under local-private-research-v1 is exactly {world-bank, eurostat, fred} -- the three publishers this mission has just shown to share producers. There is no fourth eligible statistical source to promote, so naming one would mean either reaching outside the eligible set or inventing a candidate.**

The alternative is a DIFFERENT KIND of second measurement rather than a different publisher of the same one: an observation produced by a genuinely separate apparatus that bears on the same bounded proposition. This repository already holds examples of separate apparatuses -- a platform counting content requests, a community publishing questions, a procurement journal publishing award values -- and the open question is whether any of them can bear on the SAME bounded proposition as a statistical series without weakening it. That is a proposition-design question, not a source-acquisition question, and section 14 forbids broadening into a source expansion mission here.

Deliberately. Section 36 asks for a next step only where a route is feasible, and inventing an acquisition target to fill the slot is the shape section 25 refuses.

## Network activity

- **`RESEARCH_DATA_REQUESTS` = 0**
- `STATISTICAL_DOCUMENTATION_REQUESTS` = 5, of which `METADATA_ONLY` = 1
- `GOVERNANCE_DOCUMENT_REQUESTS` = 0

  - data.worldbank.org/indicator/SP.POP.TOTL -- indicator documentation page
  - api.worldbank.org/v2/indicator/SP.POP.TOTL?format=json -- METADATA_ONLY: indicator description and source list, NO observations, no RawRecord persisted
  - fred.stlouisfed.org/series/SPPOPTOTLDEU -- HTTP 404, series does not exist
  - fred.stlouisfed.org/series/POPTOTDEA647NWDB -- series documentation page
  - ec.europa.eu/eurostat/cache/metadata/en/demo_pop_esms.htm -- Eurostat ESMS reference metadata

One navigational web search was used to locate the correct FRED series identifier after a guessed one returned 404. It established nothing: every finding cites the first-party page it led to, per section 4.

## What this is not

- NOT a finding that Eurostat or FRED are poor sources. Both are eligible under local-private-research-v1 today with zero unsatisfied conditions, and both publish carefully documented statistics.
- NOT a claim that no independence-capable route exists anywhere. It is a finding about ONE measurement family, population, over TWO candidate pairs.
- NOT a contradiction finding. No two values were compared and nothing was labelled CONTRADICTS.
- NOT a reliability judgement. No ReliabilityAssessment was created, changed or consulted as a reason to prefer a route.
- NOT an architecture gap. The independence model can already represent two groups on one Claim; what is missing is a real source pair entitled to inhabit it.

## Next

**NOT an acquisition mission, and NOT a calibration mission.**

- *Why not acquisition:* Section 36: COMMON_UPSTREAM_SOURCE_PREVENTS_INDEPENDENCE means do not continue with that pair. Acquiring Eurostat or FRED population would add real rows that cannot become a second provenance group, which is corpus expansion of exactly the kind Mission 1.43 proved cannot help.
- *Why not calibration:* Mission 1.43's algebraic finding is untouched. With one provenance group the full aggregator remains the B-2 pass-through baseline, so a labelling mission would ask a person to compare cases the aggregator cannot distinguish.

Whether a bounded proposition can be defined that two GENUINELY DIFFERENT MEASUREMENT APPARATUSES already in this corpus both bear on, without weakening proposition identity. That is a proposition-design and convergence-contract question in the ADR-035 line, and it is upstream of any acquisition. It may conclude that the INFERRED layer is required, which is a separate decision this mission does not make.
