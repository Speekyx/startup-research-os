# Mission 1.43 — Calibration Reference Corpus Expansion V1

**Primary outcome: `CALIBRATION_REFERENCE_CORPUS_MEANINGFULLY_EXPANDED`** (§40 A).

**Secondary: `NEW_CORPUS_SHAPE_NON_SCORABLE_MISSING_RELIABILITY`** (§40 C) — the
new proposition kind is a new reliability scope, and none was invented.

**0 network requests. 0 model calls. 0 embeddings. 0 new RawRecords,
NormalizedRecords or Signals. 0 ReliabilityAssessments. 0 independence groups.
0 scores.**

| counter | before | after |
|---|---:|---:|
| Claims | 37 | **43** |
| ClaimRevisions | 38 | **44** |
| Evidence | 39 | **57** |
| Claims with more than one Evidence | 2 | **8** |
| max Evidence per Claim | 2 | **4** |
| proposition kinds | 8 | **9** |
| everything else | — | unchanged |

Artifacts: [plan](../data/calibration-corpus-expansion-plan-v1.json) (frozen in
its own commit) ·
[baseline](../data/calibration-corpus-baseline-v1.json) ·
[run](../data/calibration-corpus-expansion-run-v1.json) ·
[shape after](../data/calibration-corpus-shape-after-v1.json).

---

## The finding that reframes the mission

Measured across all 37 Claims before any work, through the real resolver and the
real aggregator:

```text
claims with more than one support group                    0
claims where the aggregator differs from B-2 pass-through  0
```

**With exactly one support group, the full aggregator is not merely empirically
equal to the reliability pass-through baseline — it is algebraically identical to
it.** Saturation computes `S = 1 - prod(1 - g)` over groups; for a single group
that is the group's strength; group strength is `max(members)`; and B-2 reports
the reliability-limited strongest item, which is the same maximum over the same
`q` values.

So **no quantity of additional single-group Evidence can ever make them differ.**
The aggregation layer becomes measurable only when a Claim carries more than one
provenance group — which needs **established independence** — or when
**contradiction** opens the other side of the mass decomposition.

That was written into the frozen plan before the expansion ran, and a §37 fixture
confirms the converse: given two `KNOWN_INDEPENDENT` items, `support_strength`
**exceeds** the pass-through value. The mechanism works. This corpus just gives it
nothing to work on.

---

## §41 — Final report

### The baseline and the gaps

**1. Exact live baseline?** 325/325 RawRecords and NormalizedRecords, 33 Signals,
37 Claims, 38 ClaimRevisions, 39 Evidence, 0 independence groups, 3
ReliabilityAssessments with 10 basis rows, 1 Opportunity with 1 revision and 7
links, 0 Embeddings, 0 Scores, `scoring.scores` absent, 29 sources, 0 scope
relations, and `scoring.evidence.reliability` NULL on all 39 rows. Verified
before any work.

**2. Calibration-shape matrix before expansion?** Eight proposition kinds across
five source families, **every** Evidence row `SUPPORTS`, `UNCATEGORISED`,
`UNKNOWN` independence, every Claim `EVERGREEN` with no `claim_feature`, and
`reliability` the limiting component on 28 of 28 scorable Claims. Multi-Evidence
existed only as two TED convergent Claims with two witnesses each.

**3. Which missing shapes were highest-value?** `ESTABLISHED_INDEPENDENCE`,
`CONTRADICTION`, `TEMPORALITY` and `CLAIM_FEATURE_DIVERSITY` are all **CRITICAL**
— each is a mechanism no real Claim has ever exercised, so no parameter governing
it can be evaluated. `MULTI_EVIDENCE` is **HIGH**: it runs, over a degenerate
single-group case.

**4. Which sources were live-governance eligible?** Read from the deployment
under `local-private-research-v1`, not from an earlier report: **eurostat, fred,
ted-eu, world-bank**. Wikimedia, Stack Exchange, GDELT and OpenAlex are
`APPROVED_WITH_CONDITIONS` with conditions **unsatisfied in this deployment**, so
acquisition from them is blocked today. Twenty-one sources have no review under
this profile at all.

**5. Which candidate routes were evaluated?** Six: Wikimedia, TED under another
CPV division, World Bank, Stack Exchange, GDELT, and Eurostat/FRED.

**6. Which were rejected and why?**

- **TED under another division → `TOO_SIMILAR_TO_CURRENT_CORPUS`.** It would have
  been immediately **scorable**, which is exactly what made it tempting, and it
  repeats the same proposition kind, reliability scope, unknown-provenance
  grouping, `q` limiter and EVERGREEN semantics. By the finding above it cannot
  make the aggregator differ from the baseline. Choosing it because a number
  would appear is choosing the appearance of progress.
- **GDELT → `TOO_SIMILAR_TO_CURRENT_CORPUS`**, and acquisition-blocked.
- **Stack Exchange → `GOVERNANCE_BLOCKED`**, three conditions unsatisfied.
- **World Bank → `QUALIFIED_ALTERNATIVE`**: the same structural move with fewer
  witnesses per proposition.
- **Eurostat / FRED → `QUALIFIED_ALTERNATIVE`**, and the most interesting entry
  in the matrix: a second statistical agency publishing about the same subject as
  World Bank is the portfolio's **only visible route to a second provenance
  group**. It needs a resource authorisation, a collector, a normalizer and an
  extractor — several missions.

**7. Which route was selected?** The **Wikimedia convergent existential over
day-pairs**, derived from Signals already held.

**8. Why is it materially different from the current TED shape?** Different
source family, different proposition kind, different measurement mechanism
(counted HTTP requests versus published procurement amounts), different domain,
and — the part no other route offered — **group cardinality above two**.

**9. Was a secondary route selected?** **No.** §6 permits one only if the first
cannot address more than one high-priority shape and the second is nearly free;
neither held.

### What was preregistered, and what happened

**10. Exact preregistered target?** `TARGET_A`: at least one real Claim with two
or more Evidence rows, from a source family other than public procurement, under
a proposition kind not in the corpus. `TARGET_B`: at least one Claim with **more
than two** Evidence rows. Both semantic; neither a row count.

**11. Exact source/resource?** `wikimedia-pageviews`,
`metrics/pageviews/per-article/en.wikipedia.org`.
**12. Exact scope?** PRODUCT-level subjects (`Docker_(software)`, `Kubernetes`,
`Podman`) under the platform's own requester class `user`.
**13. Exact bounds?** No acquisition; the 18 held `content_request_change`
Signals and nothing else; 0 new records, 0 new normalized records, 0 new Signals.

**14. Was existing data reusable?** **Yes — and it was the only open door.**
Wikimedia acquisition is currently governance-blocked, so §20's "existing data
first" was not merely the cheaper choice here.

**15. Network requests made?** **0.**
**16. Records acquired/reused?** 0 acquired; 18 Signals reused.
**17. New NormalizedRecords?** 0. **18. New Signals?** 0.
**19. New Claims?** **6.** **20. New ClaimRevisions?** **6.**
**21. New Evidence?** **18.**

**22. New proposition kinds?** One:
`platform_counted_content_request_change_witnessed`.
**23. New source families represented?** In the **multi-Evidence** shape:
`encyclopedia_readership` joins `public_procurement`, so that shape goes from one
family to two.
**24. New reliability scopes?** One, and it has no assessment.
**25. Was reliability already applicable?** **No —
`NO_RELIABILITY_SCOPE_YET`.** The existing Wikimedia `0.65` binds the *detailed*
kind; a new `proposition_kind` is a new scope, and §15 forbids widening it.
**26. New ReliabilityAssessments?** **0.**

### The new Claims

**27. Any multi-Evidence Claim created?** **Six.**

| claim | item | direction | witnesses |
|---|---|---|---:|
| `e740d102` | Docker_(software) | INCREASING | **4** |
| `1324d79c` | Kubernetes | INCREASING | 3 |
| `9bda8081` | Kubernetes | DECREASING | 3 |
| `a4809b1a` | Podman | INCREASING | 3 |
| `dff657c2` | Podman | DECREASING | 3 |
| `39449935` | Docker_(software) | DECREASING | 2 |

**28–29. Exact ids and counts?** Above. **30. Directions?** All `SUPPORTS`; the
Claim's own `direction` fact (INCREASING / DECREASING) is *proposition identity*,
not Evidence direction — an increase and a decrease are two assertions, not a
disagreement.

**31. Any real contradiction?** **No —
`NO_REAL_CONTRADICTION_CASE_OBSERVED`, and the counter stays 0.** A decrease does
not contradict an increase: under the detailed kind direction is part of
proposition identity, so they are different propositions; under an existential a
counterexample does not falsify. Manufacturing one would have meant redefining
contradiction to fit a counter, which §8 forbids by name.
**32.** Not applicable.

**33. Any established independence?** **No, and `UNKNOWN` remains correct.** Every
witness comes from one publisher, one collection mechanism and one documented
counting method; different days are temporal separation. **0 EvidenceIndependenceGroups
created.** **34.** Not applicable.

**35. Any temporal Claim?** **No**, and the reason is architectural rather than
incidental: **every OBSERVED restatement is a historical fact about what a source
published, and a historical fact does not decay.** Wikimedia's day buckets are
documented UTC, so the source *does* establish timestamps — and that still does
not make the Claim temporally sensitive. Temporal sensitivity belongs to the
INFERRED layer, which is deliberately unbuilt. Converting an existential to
populate a counter is what §10 forbids.
**36–37.** `EVERGREEN`, no `claim_feature`.
**38. Any half-life assigned?** **No.**

### The aggregation diagnostic

**39. `raw_evidence_count`?** 4, 3, 3, 3, 3, 2.
**40. `scorable_evidence_count`?** **0 on all six.** The scope has no reviewed
reliability, and non-scorable items are excluded before grouping.
**41. Runtime provenance groups?** 0, for the same reason.
**42. Did `max(members)` process more than one item?** **Not for these Claims** —
the structure exists and the numeric path is closed until a reviewer looks at the
scope. It still processes two items on the two TED Claims from Mission 1.42.1.
**43. Did saturation process more than one independent group?** **No**, nowhere in
the corpus.

**44–50.** For the six new Claims: no `q`, no limiting component, no masses, no
Evidence Score, aggregation status `UNAVAILABLE` with `MISSING_RELIABILITY`. The
two TED Claims are unchanged at `q = 0.55`, limited by reliability, masses
0.55/0/0/0.45, EvidenceScore 55.0, level 1.

**51. Comparison to reliability pass-through?**
`IDENTICAL_TO_RELIABILITY_PASS_THROUGH` wherever it can be computed.
**52. Any case where the aggregator differs?** **None — 0 before, 0 after.**
**53. Why?** Because every Claim has exactly one support group, and with one
group the two are algebraically the same quantity. Not a corpus accident.

### Feasibility, before and after

**54–62.**

| | before | after |
|---|---:|---:|
| Claims | 37 | 43 |
| Evidence | 39 | 57 |
| Claims with more than one Evidence | 2 | **8** |
| max Evidence per Claim | 2 | **4** |
| distinct group cardinalities | {1, 2} | **{1, 2, 3, 4}** |
| scorable multi-Evidence Claims | 2 | 2 |
| contradiction cases | 0 | 0 |
| established-independence cases | 0 | 0 |
| temporal cases | 0 | 0 |
| source families in the multi-Evidence shape | 1 | **2** |
| proposition kinds | 8 | **9** |
| limiting components | {reliability} | {reliability} |
| distinct reliability values | {0.5, 0.55, 0.65} | unchanged |

**63. Are leakage-safe calibration splits now plausible?** **No.** Mission 1.37's
rule groups by `(reliability_scope, proposition_kind, subject_key)`, and the six
new Claims share one scope and one kind, so they form **one** additional group
that is entirely non-scorable. The scorable corpus still splits into the same two
groups it did before. More Claims did not become more independent units.

**64. Human calibration labels created?** **No.** **65. Parameters fitted?**
**No.** **66. Any profile CALIBRATED?** **No** — `REFERENCE_PROFILE_V1` is still
`UNCALIBRATED`. **67. Opportunity created or revised?** **No**, 1/1/7 untouched.
**68. Ranking?** **No.** **69. Model calls?** **0**, 0.00 USD. **70. Embeddings?**
**0.** **71. Problem-Family?** Still **PARKED**.

**72. Exact canonical counters before/after?** In the table at the top; only
Claims, ClaimRevisions and Evidence moved, and the run refuses to commit if any
other counter does — a guard that runs before the transaction is committed rather
than a check afterwards.

**73. Recommended next mission?** **Not** *Human Calibration Reference Set*, and
that is the substantive recommendation. Labelling this corpus would ask a person
to compare cases the aggregator itself cannot distinguish, because with one
provenance group everywhere the full aggregator and the pass-through baseline
return the same number by construction.

Two narrower missions come first, in this order:

1. **A reliability review preparation for the new scope**
   (`wikimedia-pageviews | … | platform_counted_content_request_change_witnessed`),
   which would make six real multi-Evidence Claims scorable — including one with
   **four** witnesses, the largest group this corpus has ever formed.
2. **An independence-capable route**, which the gap matrix identifies as
   Eurostat or FRED beside World Bank: a second statistical agency publishing
   about the same subject is the only visible path to a second provenance group,
   and therefore to the aggregation layer having anything to calibrate.

---

## What this mission did not do

No contradiction manufactured, no independence manufactured, no temporality
manufactured, no proposition identity weakened, no semantic similarity, no
embeddings, no model, no acquisition, no half-life, no threshold changed, no
profile calibrated, no Opportunity, no ranking, and Docker was not the expansion
route — it appears only as one of three items the held Wikimedia Signals already
covered.

## The convergence contract

`platform-counted-content-request-change-witnessed@1.0.0`. Identity:
`proposition`, `source_id`, `content_platform`, `content_id`, `audience_class`,
`direction`. Witness: `period_label_from`, `period_label_to`.

The classification is the ADR-035 test applied field by field. **`audience_class`
stays identity** because Mission 1.19 made it REQUIRED precisely so that the same
item over the same period cannot carry two different counts under one name;
dropping it here would undo that decision from the other end. **`direction` stays
identity** for the reason the procurement contract's `relation` does.

Mission 1.39 wrote the projection as a single hard-wired pair *"so a reader can
see that exactly one route exists"*. It is now a **table**, so a reader can still
see every route at once, and there is still no fallback: five of the historical
kinds have no contract and do not converge.

## Tests

**30 new**, and 858 across 8 packages now.

**§37's requirement is met by a fixture class that executes every reporting
expression this mission added against non-empty, real-shaped inputs** — a group
with three members, two `KNOWN_INDEPENDENT` groups, and a contradicting item —
none of which the live corpus contains. It is a testing requirement and not a
licence to fabricate canonical rows: nothing there is persisted.

**It earned its place immediately.** This mission's own shape-measurement script
read `result.level.evidence_level`, where the attribute is `result.level.level`.
It failed on the first run because the data was not empty — the same class of
defect as Mission 1.42.1's `group.members`, caught this time before it shipped.

**Three pre-existing tests were re-pointed rather than deleted**, all of the same
shape: a count that can legitimately grow is deployment state. Two pinned the
corpus totals in the shared feasibility audit; the third asserted that *exactly
one* convergence contract is registered, and the property that made it worth
asserting is that **convergence is opt-in per kind with no default and no
fallback**, which is what it checks now.
