# Mission 1.40 — Second Pilot TED Category Multi-Evidence Acquisition V1

**Outcome: `SECOND_PILOT_REAL_MULTI_EVIDENCE_NOT_OBSERVED`** (§42 B).

The taxonomy was retrieved, the category and windows were frozen, the acquisition
ran to plan — and **window A produced no Signal at all**, because both its cohorts
mixed currencies and the extractor refused them. Division 92 therefore has **one**
witness, not two.

**The convergence contract was never the blocker.** It was never reached with two
witnesses to test it.

§37 forbids widening the period, switching category, weakening the predicate or
regrouping after inspecting values. None of those was done.

---

## Two things this mission found that are worth more than the outcome

### 1. A duplicate Evidence row, created by this run and removed

Re-running interpretation over the pre-existing division-90 Signal wrote a
**second Evidence row on the existing detailed Claim**, differing from the first
only by interpreter version:

```text
ev=d48e9694  signal=97ff6d37  observed-signal-restatement@1.1.0  2026-09-01
ev=fc4a2a9c  signal=97ff6d37  observed-signal-restatement@1.4.1  2026-09-03
```

Same Signal. Same cohort. Same witness. This is **§13's forbidden case verbatim**
— *"same Signal/Claim relation → interpreter version bump"* — and Mission 1.32's
known defect: the Evidence idempotency key embeds `extraction_method`, which
embeds the interpreter version.

It briefly made the corpus report **`claims with >1 evidence: 1`**, which would
have been a false positive of exactly the thing this mission exists to create,
and which a later calibration mission would have taken for real data.

**Removed.** The row was created by this run minutes earlier, is not history, and
was not among the 7 Evidence rows the Opportunity cites (checked before
deleting; only `research.opportunity_hypothesis_evidence` references
`scoring.evidence`). The original `1.1.0` row was kept.

**The duplicate-witness guard did not prevent it**, because it protects the
convergent path and this was the detailed path — a pre-existing route that
Mission 1.32 already documented and nobody has repaired.

### 2. The extractor's cohort key does not contain what its docstring says

`group_key`'s docstring reads *"One key per comparable cohort. Five dimensions,
each load-bearing"* and names **notice class, amount scope, currency and CPV
division**. The key actually built is:

```text
source_id · record_kind_id · resource_id · notice_class · cpv_division
```

**Amount scope and currency are not in it.** They are validated *after* grouping
and refuse the **whole cohort**:

> this cohort mixes ['EUR', 'PLN']. Two currencies are never one distribution,
> and there is no reviewed rate that could make them one

The refusal is right. Its *granularity* is what cost this mission: a
currency-mixed division is discarded entirely instead of splitting into one
cohort per currency. Division 92 across the EU is currency-heterogeneous, so:

| window | cohort | outcome |
|---|---|---|
| A | CONTRACT_AWARD_NOTICE | **REFUSED** — mixes EUR, PLN |
| A | CONTRACT_NOTICE | **REFUSED** — mixes DKK, EUR |
| B | CONTRACT_AWARD_NOTICE | **derived**, 14 records contributed |
| B | CONTRACT_NOTICE | **REFUSED** — mixes CZK, EUR, SEK |

**Had currency been a grouping dimension, as its own docstring says, window A
would very likely have yielded EUR cohorts and this mission would have
succeeded.** That is the single most actionable finding here.

**It was not fixed.** §11 forbids altering the detailed Signal to support
convergence, and changing a grouping key after seeing which data it rejected is
the shape §37 and §41 both refuse.

---

## §43 — The fifty-nine questions

**1. Was TED authorized?** Yes. Review v2 `APPROVED_WITH_CONDITIONS` under
`local-private-research-v1`, resource `notices/eforms-contract-and-award` via
`ted-search-api-notices`. **The authorised resource carries no CPV restriction** —
the division is a query parameter — and `cpv_code`, `monetary_amount`,
`monetary_amount_type` and `currency` are all in the minimisation allowlist.

**2–3. Which taxonomy, which version?** Common Procurement Vocabulary, published
by the **Publications Office of the European Union**, dataset
`http://publications.europa.eu/resource/dataset/cpv`, **version 2008 (LATEST)**,
originating body DG GROW. Governing instrument: **Commission Regulation (EC) No
213/2008**, OJ L 74, 15.3.2008. Retrieved 2026-09-03.

**A bulk extraction was retrieved and refused.** A division table pulled in one
pass from the EUR-Lex HTML was internally inconsistent: it gave `90000000-8`
where this repository's own division-90 data uses a different check digit, and
labelled `92000000` *"Miscellaneous services"*, which the authority register
contradicts. **Every label below was instead verified one concept per fetch**
against `https://publications.europa.eu/resource/authority/cpv/cpv/<code>`.

**4. Which categories were considered?**

| code | official label | verdict |
|---|---|---|
| `92000000` | Recreational, cultural and sporting services | **SELECT** |
| `80000000` | Education and training services | qualified alternative |
| `55000000` | Hotel, restaurant and retail trade services | qualified alternative |
| `85000000` | Health and social work services | qualified alternative |
| `72000000` | IT services: consulting, software development, Internet and support | excluded, developer domain |
| `90000000` | Sewage, refuse, cleaning and environmental services | excluded, existing pilot |

**5. Selection rule?** Six ordinal criteria applied in order, frozen in advance,
**no numeric score**: official CPV identity · non-developer domain · not the
existing pilot · in a preferred non-developer commercial area · furthest from
both existing subjects (the declared tie-break) · collector compatibility with no
semantic remapping.

**6–8. Selected?** CPV division **92**, code `92000000`, official label
**"Recreational, cultural and sporting services"**.

**9. Why non-developer?** The official label names recreation, culture and sport.
It contains no software, no IT service and no developer activity.

**10. SubjectScopeType?** `CATEGORY`. A CPV division is a class a contracting
authority assigns to its own contract; it contains procurements, never products
(Mission 1.35), so `PRODUCT` would be a fabrication.

**11. MarketScope?** **None set.** Geography is a separate axis — CATEGORY answers
WHAT, MarketScope answers WHERE — and TED's coverage was not folded into the
subject scope.

**12–14. Frozen before acquisition?** Yes, both, in
[second-pilot-ted-category-selection-v1.json](../data/second-pilot-ted-category-selection-v1.json),
hash `d473b49e7bdc63dd8e65cce100b74dda84891bf0393158003af3747c2b35aa2f`. Windows:
**A = 2023-03-01 … 2023-03-07**, **B = 2023-03-08 … 2023-03-14**, by the rule *the
first two consecutive non-overlapping seven-day windows from the start of eForms
coverage*. No result count was inspected before freezing.

**15–16. Route and query?** `ted-search-api-notices`, the reviewed expert query
with `classification-cpv=92*`, notice types `can-standard`/`cn-standard`, bounds
`max_pages=2, max_records=100, page_size=50`. No bulk route, no scraping, no
undocumented endpoint.

**17–18. Records and completeness?** **94** (window A) and **83** (window B), 177
total. Both **`COMPLETE_BOUNDED_QUERY`**: each second page returned fewer notices
than the page size, which is how the collector detects exhaustion. Neither hit a
bound.

**19–21. Cohorts?** Preregistered as *one witness cohort per frozen publication
window*, because the extractor's cohort key carries no period and a single
derivation over both windows would produce one cohort. **Four candidate cohorts**
(two notice classes × two windows). **One** passed: window B's award cohort.
Three were refused for mixed currencies.

**22. Signal ids?** One new Signal: `4e8ee7f7-e3b4-5c56-917c-ec11e6b480c5`
(division 92, window B, 14 contributing records). Window A produced none.

**23. Detailed Claims unchanged in semantics?** Yes. `notice_ids` is still
identity on `source_reported_procurement_value_contrast`, no template changed, no
historical proposition key moved.

**24–26. Convergent proposition, Claim, key?**
`source_published_classification_value_contrast_witnessed`. Two convergent Claims
were created — `02248c91` (division 92) and `73e834c4` (division 90) — **each with
revision 1**.

**27–30. Evidence count, ids, witness keys, distinctness?**
**One Evidence row each.** The mission's target was ≥2 and it was not reached.
Both witnesses are distinct from each other, but they are in **different**
divisions and therefore different Claims: division is proposition identity.

**31. ObservationOverlap?** Not computed between two witnesses of one Claim,
because no Claim has two.

**32–33. Independence?** `UNKNOWN` on every new row. **No independence group was
created**, and `scoring.evidence_independence_groups` still holds 0 rows.

**34–35. Did the existing TED ReliabilityAssessment bind?**
**Yes for the detailed Claims, no for the convergent ones**, and this is the
reliability contract working exactly as specified. Its scope is
`(ted-eu, notices/eforms-contract-and-award, procurement_notice, OBSERVED,
source_reported_procurement_value_contrast)` — **it carries no classification
division**, so it binds to the *new division-92 detailed Claim* as readily as to
division 90's. It does not bind to either convergent Claim, because
`proposition_kind` differs, and `NO_APPLICABLE_ASSESSMENT` is correct.

**No new ReliabilityAssessment was created.** Two, six basis rows, unchanged.

**36–41. Aggregation?**
**The real aggregator never received more than one Evidence for any new Claim**,
so no mechanism saw more than one input. `raw_evidence_count = 1` on each. The
detailed Claims are `COMPLETE` (reliability resolved `0.5`); both convergent
Claims are `UNAVAILABLE` with `MISSING_RELIABILITY`.

**42–44. Diagnostic result, labelling, pass-through comparison?**
No multi-record diagnostic exists to report.
**`PASS_THROUGH_COMPARISON_UNAVAILABLE`** — with one Evidence row per Claim, the
aggregator and the reliability pass-through are trivially identical, which is the
Mission 1.37 state unchanged rather than a new measurement. The profile remains
`UNCALIBRATED`.

**45. Contradiction?** **`NO_REAL_CONTRADICTION_CASE_YET`.** None was sought.

**46. Opportunity dimensions?** The convergent proposition kind has **no
registered mapping**, and none was added. §26: leave it unmapped rather than
assume the detailed kind's mapping carries over.

**47–52. Opportunity, score, ranking, labels, parameters, CALIBRATED?** None,
none, none, none, none, no.

**53. ReliabilityAssessments created?** None.

**54. Model calls?** **0.** **55. Embeddings?** **0.**

**56. Problem-Family?** Still `PARKED`.

**57. Calibration feasibility before → after?**

| | before | after |
|---|---:|---:|
| Claims | 28 | **31** |
| Evidence | 28 | **31** |
| **Claims with >1 Evidence** | **0** | **0** |
| maximum Evidence per Claim | 1 | **1** |
| scorable claims | 19 | **20** |
| contradiction / independence-established / temporal cases | 0 | **0** |
| distinct proposition kinds (scorable) | 2 | **2** |
| distinct source ids (scorable) | 2 | **2** |
| support-strength variation | `0.5`×1, `0.65`×18 | `0.5`×**2**, `0.65`×18 |

**The one counter this mission existed to move did not move.** The corpus gained
a second commercial domain and a second `0.5` row; it gained no multi-record
Claim.

**58. Canonical counters?**

| counter | before | after | why |
|---|---:|---:|---|
| RawRecords | 148 | **325** | 177 division-92 notices |
| NormalizedRecords | 148 | **325** | all 177 normalized |
| Signals | 28 | **29** | one cohort qualified |
| Claims | 28 | **31** | 1 detailed + 2 convergent |
| ClaimRevisions | 29 | **32** | one per new Claim |
| Evidence | 28 | **31** | one per new Claim, after removing the duplicate |
| ReliabilityAssessments / basis | 2 / 6 | **2 / 6** | none created |
| Opportunities / revisions / links | 1 / 1 / 7 | **1 / 1 / 7** | untouched |
| EvidenceIndependenceGroups | 0 | **0** | none manufactured |
| Embeddings / Scores | 0 / 0 | **0 / 0** | — |
| Registered sources / Scope relations | 29 / 0 | **29 / 0** | — |

**59. Recommended next mission?** Below.

---

## §44 — Recommended next mission

**Mission 1.41 — Procurement Cohort Currency Grain Repair V1.** Narrow, and
upstream of everything else.

The extractor's cohort key must be reconciled with its own docstring: **currency
and amount scope are named as load-bearing dimensions and are not in the key**,
so a currency-mixed division is refused whole rather than split. Three of four
real cohorts died on that, and the fix is a *grouping* change, not a weakening —
the refusal that fires today would still fire for a genuinely mixed cohort,
because there would no longer be one.

That mission should: state whether the key or the docstring is wrong; if the key,
add currency and amount scope with a version bump; **prove historical
reproducibility** — the existing division-90 Signal must still derive identically,
or its Claim's identity moves; and only then re-attempt a bounded acquisition.

**It should also repair the interpreter-version duplicate** (finding 1), which is
independent of currency and has now bitten twice. A re-interpretation under a new
interpreter version must be a no-op for an unchanged Signal and Claim, and today
it is an INSERT.

**Do not re-pick the category or the windows.** Division 92 is frozen and still
correct; what failed is a grain in the extractor, and a second acquisition should
follow the repair rather than replace it.

---

## Artifacts

| | |
|---|---|
| [second-pilot-ted-category-selection-v1.json](../data/second-pilot-ted-category-selection-v1.json) | the frozen selection, taxonomy provenance, windows and partition rule |
| [second-pilot-acquisition-run-v1.json](../data/second-pilot-acquisition-run-v1.json) | what was requested and persisted |
| [second-pilot-pipeline-run-v1.json](../data/second-pilot-pipeline-run-v1.json) | normalization, per-window derivation, interpretation |
| [calibration-feasibility-audit-v1.json](../data/calibration-feasibility-audit-v1.json) | regenerated against the real deployment |
| `infrastructure/scripts/run_second_pilot_acquisition.py` | takes no category or window argument, by design |
| `infrastructure/scripts/run_second_pilot_pipeline.py` | derivation scoped per frozen window |

The convergent interpreter is now **wired into the production interpretation job**
(§1), with the projection isolated in one small function so the decision is
visible in a diff. One Signal legitimately witnesses two Claims across distinct
Claims, and never twice within one — tested against the real repository before
the first real acquisition ran.
