# Mission 1.48 — Falsifiable Evidence Apparatus Gap Definition V1

**Primary outcome: `CONTRADICTION_CLAIM_IDENTITY_ARCHITECTURE_GAP`.**

The contradiction machinery is fully functional and structurally unreachable.
And the identity fact responsible — **source attribution** — is the same one that
blocked corroboration in Mission 1.47. **One identity decision closes both roads
out of the B-2 baseline**, so the binding constraint is not a missing apparatus,
and no apparatus can remove it.

---

## Setup

**1. Was Mission 1.47 merged?** Yes. PR #90, **12/12 checks SUCCESS**, merged.
Both commits (`a079804`, `14c801c`) verified reachable from `main`, and all seven
expected artifacts verified present on `main`.

**2. Exact main commit?** `3ca3864dbf785682e3b7f99691b05a20ee4adbb9`.

**3. Dedicated branch?** `sprint-1/mission-1.48`, from that commit. Mission 1.47's
branch was not reused and nothing was amended.

**4. Exact baseline counters?** RawRecords **325**, NormalizedRecords **325**,
Signals **33**, Claims **43**, ClaimRevisions **44**, Evidence **57**,
ReliabilityAssessments **4**, basis rows **12**, IndependenceGroups **0**,
Opportunities **1**, revisions **1**, evidence links **7**, Embeddings **0**,
registered sources **29**, Evidence with stored reliability **0**,
`scoring.scores` **ABSENT**. All sixteen match the brief. No drift.

**5. Exact aggregation shape?** Claims with Evidence **43**, scorable **34**,
scorable multi-Evidence **8**, max Evidence per Claim **4**, max support groups
on one Claim **1**, Claims with more than one support group **0**, Claims with
any contradiction group **0**, **aggregator differs from B-2 in 0 cases**.
`REFERENCE_PROFILE_V1` **UNCALIBRATED**.

---

## §0 — Reconstructed from live code, not from mission reports

**6. Why can one support group not distinguish the aggregator from B-2?**
Saturation over one group is that group's strength; group strength is `max()`
over its members; B-2 is the reliability-limited strongest supporting item — the
same maximum over the same `q` values. Equal by **algebra**, so no quantity of
additional single-group Evidence can separate them.

§0 forbade quoting Mission 1.43 for this, so it was re-derived: the real
`aggregate()` was run over all 43 live Claims with reliability resolved through
the real resolver, and B-2 was computed independently. **0 differing cases.**

**7. What are the two structural routes out?** A second **established
independent** support group, or a real **contradiction**. Both were exercised on
non-persisted fixtures through the real aggregator:

- two `KNOWN_INDEPENDENT` supports → 2 groups, and `S = 1-(1-g_A)(1-g_B)` exceeds
  `max(g_A, g_B)`.
- one SUPPORTS + one CONTRADICTS → support 0.6, contradiction 0.5, masses
  0.3 / 0.2 / 0.3 / 0.2 summing to **1.0**.

**The machinery is not the gap.** It works exactly as specified and has never
been reached.

---

## Falsifiability

**8. What project-local definition was adopted?** A Claim is falsifiable here when
it states an exact subject, measured property, bounded period, population, unit,
truth conditions and falsifier conditions — and, decisively, **when there exists
an observation that would count as CONTRADICTS without changing proposition
identity.** That last clause is architecture-aware on purpose: a proposition can
be philosophically falsifiable and unfalsifiable *here*, because identity decides
which Claim an observation attaches to.

**9. Which families were evaluated?** Seven: `EXACT_POINT_VALUE`,
`THRESHOLD_STATE`, `EXACT_DIRECTION`, `BOUNDED_CATEGORY_STATE`,
`RATE_OR_PROPORTION`, `SOURCE_ATTRIBUTED_EXISTENTIAL_WITNESS`,
`SOURCE_ATTRIBUTED_HISTORICAL_RESTATEMENT`. Eight qualitative criteria each, with
**no weighted numeric score** — §5 allows five states and nothing else.

**10. Which are monotone?** The two the project **already implements**:
`SOURCE_ATTRIBUTED_EXISTENTIAL_WITNESS` and
`SOURCE_ATTRIBUTED_HISTORICAL_RESTATEMENT`. That is the trade-off in one line —
the best model fit and the best matchability, and no falsifier at all.

**11. Which can admit contradiction?** `EXACT_POINT_VALUE`, `THRESHOLD_STATE`,
`BOUNDED_CATEGORY_STATE` and `RATE_OR_PROPORTION` in principle.
`EXACT_DIRECTION` is `NOT_APPLICABLE` rather than weak, and the reason is
structural: `direction` **is** proposition identity, so the contradicting
observation forms a different Claim.

**12. Exact falsifier for each serious family?** Recorded per family in
`falsifiability-vs-convergence-tradeoff-v1.json`. For the preferred family: a
source-native measurement of M for E at T, under definition D and unit U, whose
value is `< X`.

**13. Preferred proposition family?** **`THRESHOLD_STATE`** — *Metric M for entity
E at time T is >= X, under a named operational definition and unit.*

**14. Why?** It is the only family that is falsifiable **and** tolerant of the
measurement noise two genuinely independent apparatuses always produce. An
`EXACT_POINT_VALUE` claim is contradicted by a rounding difference, which
manufactures false contradictions and makes independent corroboration nearly
impossible — two honest apparatuses rarely publish the identical number. A
threshold lets both SUPPORT it while still admitting a real falsifier, so it
serves **both** routes, which no other family does.

**The cost is recorded rather than discounted.** X is *ours*, not the source's,
so it introduces a governance question the other families lack. This project
already refuses "an arbitrary number wearing the costume of a rule", and a
threshold chosen after seeing the data would be exactly that. **X must be frozen
before the second measurement is retrieved.**

---

## §6 — Apparatus requirements

**15–23.** The full specification is in
`falsifiable-evidence-apparatus-requirements-v1.md`. It is written **from the
evidence requirement backwards** and names no source, vendor, API or product —
enforced by a validator. In brief:

| requirement | must be |
|---|---|
| **16. subject granularity** | exact, externally identifiable, matched to a reviewed registry entry by **exact equality** — no distance, stem, synonym table or embedding |
| **17. time granularity** | a period whose boundaries the **source defines**, not the extent of what was retrieved; alignable by exact equality of a defined interval, never by overlap or containment |
| **18. unit semantics** | explicitly published, and identical to the partner's or connected by a deterministic reviewed equivalence. No conversion, normalisation or rescaling |
| **19. population/geography** | explicitly published and identical or reviewed-equivalent. **A shared label is not a shared population** |
| **20. methodology documentation** | DOCUMENTED, first-party, and **RETRIEVABLE by this deployment through a lawful route** |
| **21. lineage documentation** | DOCUMENTED, with the upstream producer IDENTIFIED and **different** from the partner's |
| **22. revision policy** | DOCUMENTED_OR_BOUNDED — a silently restatable measurement makes a contradiction indistinguishable from a revision |
| **23. checkability** | a reviewer can check what the source said, or the source documents that it cannot be checked. Either is reviewable; silence is not |

**24. Reliability-reviewability gate?** Promoted to a **first-class** search
criterion: first-party measurement definition, methodology and known limitations
available and retrievable; a reviewer able to identify the five-part reliability
scope; documentation lawfully retainable.

Mission 1.47 paid for learning this late. One robots-blocked methodology page
left independence `UNKNOWN` **and** was the reason the operator declined both
Stack Exchange reliability scopes in Mission 1.36.1 — **a single inaccessible
document disqualified an otherwise strong apparatus on two separate gates.**
Retrievability is therefore checked *before* an apparatus is a candidate, not
after its data looks useful.

**25. Independence-capable pair template?** and **26. Contradiction-capable pair
template?** Both recorded generically, no source named. Independence requires no
republication, no shared upstream producer, neither consuming the other's values,
genuinely distinct measurement processes, and first-party documentary support.
**Organisational separation is explicitly insufficient**: Mission 1.46 found one
publisher reproducing another's series verbatim, source code and all.

---

## §9 / §10 — The architecture finding

**27. Can current Claim identity represent contradiction?** **No.** Three
independent blockers:

1. **`direction` is a proposition fact** in all three implemented templates, and
   `proposition_key()` names direction among the facts a proposition is about. An
   INCREASING and a DECREASING observation produce different keys, hence two
   Claims. *Live evidence:* three Claim pairs in the corpus differ **only** in
   direction.
2. **No interpreter can emit `CONTRADICTS`.** `EvidenceDirection.SUPPORTS`
   appears **exactly once** in the whole interpreters package, as a hard-coded
   literal; `CONTRADICTS` appears nowhere. *Live evidence:* all 57 Evidence rows
   are SUPPORTS.
3. **`source_id` is a proposition fact on all 43 Claims**, so the cross-source
   case cannot arise: two observations form two Claims before their values are
   ever compared.

**28. Does source attribution block cross-source contradiction?** **Yes, and this
is the deepest of the three.** *"Source A reported X"* and *"Source B reported
Y"* are both **true simultaneously**, whatever X and Y are. They are two facts
about two publications, not a disagreement about the world.

**29. Would a source-independent INFERRED Claim be required?** **Yes — option A.**
A proposition like *"Metric M for E at T is X"* asserts about the **world**, so
two measurements of it can genuinely disagree. It is INFERRED by construction,
because moving from *a source reported X* to *X is the case* is an inference
step. Option B (a governed cross-source OBSERVED convergence contract) is smaller
but inherits Mission 1.47's near-tautology problem. Option C (a new claim type)
is the largest. Option D: none found. **Nothing was implemented and `source_id`
was not removed.**

**30. Any architecture gap?** Yes, and it is the primary outcome. **The
unification:** corroboration needs two observations on one Claim; contradiction
needs two observations on one Claim; source attribution in proposition identity
forbids both. Mission 1.47's `CONVERGENCE_CONTRACT_ARCHITECTURE_GAP` and this
mission's finding are **the same fact seen from two sides**.

**The consequence that decides the next mission:** a new apparatus interprets to
facts carrying its own `source_id`, produces its own `proposition_key`, and lands
on its own Claim — where it can neither join a support group nor contradict
anything. **Acquiring one would add rows and change nothing.** That is why
`BOTH_ROUTES_REQUIRE_NEW_MEASUREMENT_APPARATUS` is deliberately *not* the
outcome: it would send the next mission looking for a candidate that cannot be
used.

**This is not a bug.** Source attribution is correct for an OBSERVED claim and
Mission 1.38 established why: for an OBSERVED claim the attribution **is** the
claim. The gap is that the project has no *other* claim layer, and the one that
would carry a source-independent proposition is deliberately unbuilt.

---

## Fixtures

**31. Positive contradiction fixture?** Yes, non-persisted, through the real
aggregator.

**32. Real aggregator contradiction output?** support_strength **0.6**,
contradiction_strength **0.5**, supported_mass **0.3**, contradicted_mass
**0.2**, conflict_mass **0.3**, uncertainty_mass **0.2** — summing to **1.0**.

**33. Positive independent-support fixture?** Yes, retained as a regression
guard.

**34. Real group count?** **2** support groups, with saturation exceeding
`max(g_A, g_B)` for fixture-owned strengths. Two `UNKNOWN` items collapse to
**1** group, and three `UNKNOWN` items still collapse to **1** — UNKNOWN is never
promoted.

All fixture reliability values are fixture-owned (0.6, 0.5) and no reviewed value
was copied or suggested.

---

## Portfolio

**35. Current portfolio requirements matrix?** All nine held apparatuses scored on
eight properties. **`FALSIFIABLE_POINT_CLAIM` is NO for all nine, and
`CONTRADICTION_CAPABLE` is NO for all nine.**

**36. Any held apparatus qualifies?** **No.** Every implemented proposition kind
is either a source-attributed historical restatement or a monotone existential —
precisely the two families marked unfalsifiable. This is not a coincidence of the
corpus: it is what the only implemented interpreter produces.

**37. Any registered-but-unheld class promising?** **No.** Live eligibility
measured: **7 eligible of 29**, 5 with collectors, 22 blocked at the gate. Three
candidates recorded, none `PROMISING_FROM_EXISTING_DOCUMENTATION`:

- `eurostat` — `KNOWN_MISMATCH`. Good apparatus shape; Mission 1.46 established it
  is **upstream of** the World Bank for the held series.
- `fred` — `KNOWN_MISMATCH`. Republishes the exact series already held, by its own
  declaration.
- `usaspending` — `INSUFFICIENT_INFORMATION`. A different jurisdiction's
  contracts, so complementary rather than corroborating.

**The two whose shape fits best are the two Mission 1.46 already refuted on
provenance** — the same answer arriving from a different direction.

**38. Was any source selected?** **No**, and the record says so explicitly.

---

## Route and value

**39. Which route is strategically preferable?** **`NEITHER_CURRENTLY_ACTIONABLE`.**
Both require two observations on one Claim, which proposition identity forbids, so
neither becomes actionable by acquiring anything.

**40. Why?** Once unblocked, **independent corroboration** is preferable, on
tractability rather than value: it needs exact alignment plus established
independence, while contradiction needs all of that **and an actual disagreement**
between two apparatuses agreeing on everything else — a fact about the world that
cannot be arranged in advance. *A mission can plan for corroboration; it can only
hope for contradiction.* The asymmetry worth recording is that contradiction is
the more **informative** outcome when it occurs, because it is the only case that
tells the operator something is wrong.

**41. Structurally identifying?** **YES** — two independent supports give two
groups and saturation exceeding `max`; a support/contradict pair gives non-zero
contradiction and conflict mass, which no real Claim has produced.

**42. Semantically useful?** **YES** — unlike Mission 1.47's existential, a
threshold claim carries information a person would act on. Both are required and
Mission 1.47 showed they can diverge.

---

## What did not happen

**43. Research data requests?** **0.**
**44. Documentation requests?** **0** apparatus and **0** governance. Zero
requests of any kind.
**45. Canonical data mutations?** **None.** All sixteen counters identical, and
the pytest leak check reports the database unchanged across 26 tenant tables and
global tables unchanged across 17.
**46. Reliability changes?** **None.** No value assigned, suggested or copied; a
test asserts no reviewed value appears in the reviewability gate.
**47. Calibration changes?** **None.**
**48. Model calls?** **0**, 0.00 USD.
**49. Embeddings?** **0.** No semantic matching.
**50. Opportunity changes?** **None** — 1 / 1 / 7.
**51. Problem-Family state?** **PARKED.**
**52. Workspace isolation status?** Inspected **before** the canonical pass: 2
seeded workspaces (`dev`, `dev-other`), **0 orchestration probes**. No cleanup
needed or performed; the clean uninterrupted run passed with both leak checks
green. No test disabled, weakened or skipped, and no failure masked by a rerun.
**53. Zero-dependency tests?** **1124 across 8 packages**, run with bare `python`
using the exact CI runner **before commit**, as §33 requires.
**54. Pytest?** **245 across 9 packages**, all passing.
**55. Exact counters after?** Identical to question 4.
**56. Primary outcome?** **`CONTRADICTION_CLAIM_IDENTITY_ARCHITECTURE_GAP`.**

---

## §39 — Next

**57. Recommended next mission?** **Not candidate discovery**, even though this
record freezes the specification one would use. No apparatus can exercise either
route while source attribution is proposition identity, so a discovery mission
would end by finding a good candidate that cannot be used.

Recommended instead: **a narrow Claim-semantics and contradiction-reachability
design mission**, before any data search. It must decide whether a
source-independent proposition belongs in the INFERRED layer, in a governed
cross-source OBSERVED convergence contract, or in neither — and decide it as a
semantics question with an ADR behind it, never as an edit to a template.

**The apparatus specification is not wasted.** It is deliberately reusable as a
search specification, and it becomes actionable the moment the semantics question
is settled. **Mission 1.49 was not started.**

**§34** — `DEPLOYMENT_LOCAL_HUMAN_CONFIRMATIONS_REQUIRE_MIGRATION_CHECKLIST`
carried forward unchanged as existing operational debt. No replay mechanism was
created and `record_ted_operator_acceptance.py` was not modified.

---

## Artifacts and gates

| file | what it is |
|---|---|
| `falsifiable-evidence-apparatus-gap-baseline-v1.json` | §0, generated by running the **real aggregator** over the live corpus |
| `measure_falsifiable_apparatus_gap_baseline.py` | measures it; reads only; **deliberately not in CI** (measures a deployment) |
| `falsifiability-vs-convergence-tradeoff-v1.json` | §11, the seven proposition families |
| `falsifiable-evidence-apparatus-requirements-v1.json` / `.md` | the apparatus specification and the architecture finding |
| `render_falsifiable_apparatus_requirements.py` | renders and **validates**; wired into CI |
| `test_falsifiable_apparatus_gap.py` (evidence-aggregation) | aggregator fixtures and artifact invariants |
| `test_contradiction_claim_identity.py` (claim-model) | the identity proof, in the package owning `proposition_key` |

**The validator was probed rather than trusted.** Fifteen deliberate violations,
fifteen caught: a monotone family marked falsifiable or contradiction-capable, a
monotone preferred family, an unevaluated preferred family, a numeric weighted
score, an outcome outside §37, more than three candidates, a selected source, a
candidate state outside the vocabulary, an empty requirement, a specification
naming a source, a moved counter, research data acquired, model calls, and
Problem-Family unparked.

**A §23 trap was met and fixed structurally.** The first draft of the
no-named-source guard was a substring scan and it **refused this mission's own
record** on the word *documented*, because `ted` is inside it. Repaired with
token boundaries — the same fix Mission 1.13.1 made so that `supermarket` is not
`market`. A scan that fails on the prose doing the work is the recurring shape,
and loosening it until it passes is how a structural check stops checking.

Gates: `ruff check` and `ruff format --check` clean over 669 files; all nine
generated-document `--check` steps in sync including the new one;
`validate_source_registry`, `validate_signals`, `validate_claims`,
`validate_normalization` all passing.

Governance: `docs/CLAUDE.md` 1.81 → 1.82, `PROJECT_MANIFEST.md` 1.80 → 1.81.
