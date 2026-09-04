# Mission 1.49 — Source-Independent Claim Semantics & Contradiction Reachability V1

**Primary outcome: `SOURCE_INDEPENDENT_PROPOSITIONS_BELONG_TO_INFERRED_LAYER`.
Decision recorded as ADR-036.**

The layer already exists, it was defined for exactly this, and nobody has built
it. `claim-epistemic-semantics-v1.md` §4 defines `INFERRED` as a claim that
*"asserts something about the world that the measurement is evidence for, and
that the source did not itself report"* — the source-independent proposition,
verbatim, written in Mission 1.13 several missions before anything needed it.

**No new `ClaimType`. No subtype. No migration.**

---

## Setup

**1. Was Mission 1.48 merged?** Yes — PR #91, **12/12 SUCCESS**, merged. Verified
against Git rather than taken from the brief.

**2. Exact main commit?** `a7dba31e5c1981c289c65257dcbd828130bc2650`, matching the
brief's stated head. All eight Mission 1.48 artifacts verified present on `main`;
tree clean; `docs/CLAUDE.md` 1.82, `PROJECT_MANIFEST.md` 1.81.

**3. Dedicated branch?** `sprint-1/mission-1.49`, from that commit.

**4. Exact baseline counters?** Verified by re-running Mission 1.48's generated
baseline against the live deployment — **it still matches, so drift is zero**:
325 / 325 / 33 / 43 / 44 / 57, ReliabilityAssessments 4, basis 12,
IndependenceGroups 0, Opportunity 1 / 1 / 7, Embeddings 0, sources 29, stored
reliability 0, `scoring.scores` ABSENT, profile UNCALIBRATED, Problem-Family
PARKED. Aggregation shape unchanged: 8 scorable multi-Evidence Claims, max 4
Evidence per Claim, max 1 support group, 0 contradiction groups, 0 cases where
the aggregator differs from B-2.

---

## What INFERRED already means

**5. Existing ClaimTypes?** `OBSERVED`, `INFERRED`, `PREDICTED`, `RECOMMENDED`,
`HYPOTHESIS`. A closed enum.

**6. Any real INFERRED Claims?** **None.** All 43 live Claims are `OBSERVED`, all
43 are `interpretation_kind = DETERMINISTIC`, and **0 carry a `model_version`**.

**7. Existing documented meaning of INFERRED?** *"Derived analytically from one or
more observations"* (ontology §7 and the generated contract), and §4 of the
epistemic semantics: *"Asserts something about the world that the measurement is
evidence for, and that the source did not itself report."* An INFERRED claim
carries the Signals it reasoned from as Evidence, a **rationale** — the reasoning
step in a sentence — and an interpretation confidence.

**8. Does INFERRED imply LLM use today?** **No**, and the taxonomy refutes it
twice.

- **By type.** `INFERRED` is *derived analytically*; **`PREDICTED`** is *a
  model-generated estimate*. The model-associated type is PREDICTED.
- **By axis.** `claim_type` is the epistemic category; `interpretation_kind` is
  the procedure (`DETERMINISTIC` / `MODEL_DERIVED`). Migration 0016's CHECK
  constraint ties `interpretation_kind` to the presence of a `model_version` —
  **not** to `claim_type`. The axes are orthogonal in SQL, not merely in prose.

And the semantics document says the consequence outright: *"A deterministic
extractor can produce an `INFERRED`-type claim, and an LLM can produce an
`OBSERVED`-type one."*

**9. Can deterministic inference be INFERRED?** **Yes.** `INFERRED` +
`interpretation_kind = DETERMINISTIC` is representable in the current schema
today, with no migration. It has simply never been written.

**10. Exact OBSERVED semantics?** Truth condition: the named source published,
counted or reported the stated thing. Falsifier: it did not. `source_id` is
**proposition identity**.

**11. Exact source-independent semantics?** Truth condition: the stated condition
holds of the external phenomenon. Falsifier: an incompatible observation under
equivalent measurement semantics. `source_id` is **witness provenance**.

**12. Why must OBSERVED retain `source_id`?** For an OBSERVED claim the
attribution *is* the claim (Mission 1.38). Removing it would not merge two Claims
about one fact — it would rewrite what all 43 existing Claims mean.

---

## The four models

**13. Candidate models evaluated?** All four, on ten qualitative dimensions with
no weighted score.

**14. Model A — INFERRED WORLD CLAIM: PREFERRED.** The reasoning step is stated
rather than hidden, which is the whole difference between an inference and a
fabrication. Purely additive: existing OBSERVED Claims keep their meaning and
become the inputs. And the type already exists with exactly these semantics.

**15. Model B — CROSS-SOURCE OBSERVED CONVERGENCE: REJECTED.** It fails the
question §2 said not to answer by implementation convenience — *can something be
OBSERVED if no single source observed that proposition?* The repository already
wrote the refutation:

> **An `OBSERVED` claim that should have been `INFERRED` is a fabrication with a
> citation attached.**

Such a Claim would drop its attribution while **keeping** every citation, which
makes it worse than an honest inference rather than milder.

**16. Model C — DETERMINISTIC MEASUREMENT CLAIM: UNNECESSARY.** Semantically
sound, and it solves a solved problem: the deterministic-versus-model distinction
is exactly what `interpretation_kind` carries, orthogonally. A sixth ClaimType
would put one distinction in two places — the defect Mission 1.13 fixed by
dropping `evidence.claim_type`.

**17. Model D — DELIBERATELY ABSENT: REJECTED.** Taken seriously, because §2
forbade dismissing it merely because the aggregator could not otherwise be
calibrated. Rejected for a different reason: **it is not actually the
conservative option.** The layer is already defined in three places, so choosing
absence does not decline to build something — it leaves a defined capability
permanently unbuilt. And its cost must be stated: the system stays unable to say
that two sources disagree, the one signal that tells an operator to go and look.

**18. Preferred model?** **A.** **19. Why?** Answered above, and recorded in
ADR-036 with the alternatives and their rejection reasons.

---

## Identity

**20. Exact THRESHOLD_STATE proposition identity?** `claim_type`, `proposition`,
`canonical_subject_id`, `metric_definition_id`, `time_bound`,
`population_or_geography`, `unit`, `threshold_operator`, `threshold_value`.

**21. Exact witness facts?** `source_id`, `resource_id`,
`source_native_metric_id`, `source_native_subject_id`, `measurement_value`,
`measurement_timestamp`, `methodology_version`, `record_locator`.

**22. Is threshold in identity?** **Yes.** `M >= 100` and `M >= 200` have
different falsifiers, so they are different propositions.

**23. Is measurement value in identity?** **No — the load-bearing exclusion.** If
it were, 110 from source A and 105 from source B would produce two Claims, which
is Mission 1.48's failure reproduced one layer up. The value is what a witness
reports; the threshold is what the Claim asserts.

**24. Is `source_id` in identity?** **No, for this layer.** A proposition about
the phenomenon cannot be keyed by publisher. **This does not apply retroactively
to OBSERVED.**

**25. Where is `source_id` preserved?** In every Evidence row's witness
provenance, and through the full existing chain Evidence → Signal →
signal_inputs → NormalizedRecord → RawRecord → Source. **Source independence of
the proposition is never provenance loss.**

**26. Can Source A=110 and B=105 support the same Claim?** **Yes** — proved
against the real `proposition_key`: with the measurement value excluded, both
produce the identical key.

**27. Can Source B=90 contradict it?** **Yes**, and it lands on the same Claim
for the same reason.

**28. Can the real `EvidenceDirection` represent this?** **Yes, unchanged.**
`SUPPORTS` and `CONTRADICTS` already exist and already flow through the
aggregator. Direction is Evidence direction relative to a fixed proposition —
the precise inversion of the OBSERVED layer, where Mission 1.48 found `direction`
*is* identity.

---

## Gates

**29. Is semantic mismatch NOT_APPLICABLE?** **Yes**, never CONTRADICTS. A
measurement of a different quantity bears on a different proposition and is
refused before attachment.

**30. Is dependent republication kept non-independent?** **Yes** — demonstrated
through the real aggregator: one group, strength 0.6, no exceedance.

**31. Measurement-equivalence gate?** Required over metric definition, subject,
time, population, geography, unit, adjustment and methodology semantics, **before**
attachment.

**32. Independence gate?** Separate, evaluated on Evidence provenance, and kept
**out** of Claim identity — a proposition must not become a different proposition
because a reviewer learned something about provenance. **A source can be
independent and measure something different; a source can measure the same thing
and be a republication. Both gates are required and neither implies the other.**

---

## Reliability

**33. Reliability scope semantics?** Unchanged: `source_id`, `resource_id`,
`record_kind_id`, `claim_type`, `proposition_kind`.

**34. Does reliability remain source-specific?** **Yes, and this resolves the
apparent conflict.** Claim **identity** and Evidence reliability **scope** are
different things. The proposition is source-independent; the Evidence is still a
particular source's measurement, and *how dependably does this source's
measurement support this kind of proposition* stays source-relative. A new
`proposition_kind` with `claim_type = INFERRED` is a **new** scope, so every such
row resolves `NO_APPLICABLE_ASSESSMENT` until a human reviews it. **No value is
inherited by proposition similarity, and none was assigned.**

**35. Derivation validity separate from reliability?** **Yes, and they must never
be multiplied.** Whether 110 is dependable is a human judgement against
documentary basis; whether 110 entails `>= 100` is exact. No coefficient combines
them, and inventing one would let a sound derivation look doubtful because its
input is uncertain — which uncertainty mass already represents correctly.

**36. Derivation provenance required?** **Yes**: rule id and version, input
signal or claim ids, preregistered parameters, threshold provenance status,
timestamp, claim type, interpretation kind.

**37. Threshold preregistration rule?** `PREREGISTERED`, `SOURCE_NATIVE` and
`EXTERNAL_NORM` are calibration-eligible. `POST_HOC` and `UNKNOWN` are not.

**38. Post-hoc threshold calibration eligibility?** **Ineligible.** The Claim is
not false because its bound was chosen late, but a threshold picked to make a
case work measures the analyst. `UNKNOWN` is ineligible rather than assumed
preregistered — **uncertainty is never permission.**

---

## Architecture

**39. Need a new interpreter layer?** No — a **separate evaluator** (option B).
`validate_claims.py` fails the build on any non-OBSERVED `ClaimType` access in the
interpretation package, and **that guard is correct and was left untouched**.
Putting source-independent evaluation there would require weakening it, and *a
guard removed to let new work through is a guard that never was.*

**40. Need a derivation service?** Plausibly, as a later shape of the evaluator.
Not decided here.

**41. Need a ClaimRelation?** Not required today. The preferred attachment links
the Signal and its OBSERVED provenance to the source-independent Claim; a
relation is more machinery than the case needs.

**42. Is cross-source OBSERVED convergence still needed?**
**`NO_LONGER_NEEDED_FOR_WORLD_PROPOSITIONS`.** Mission 1.47's finding that the
contract structurally refuses them becomes a **feature rather than a gap**:
it is the mechanism keeping OBSERVED honest. `SourceBoundary` was not touched.

**43. Existing historical Claims unchanged?** **Yes.** 43 Claims, 44 revisions,
57 Evidence keep their proposition identities and meaning. **0 identities
rewritten, 0 migrations recommended.**

**44. ADR number and decision?** **ADR-036 — A source-independent proposition is
an INFERRED Claim.** Status Accepted.

**45. Semantic invariants?** All fifteen (I1–I15) recorded and enforced by the
validator.

---

## Fixtures

**46. Independent-support fixture?** Yes, through the real aggregator: 110 and
105, both `KNOWN_INDEPENDENT`.

**47. Group count?** **2 support groups, strength 0.8** against a strongest
member of 0.6 — **the first shape in this repository that would make the full
aggregator differ from the B-2 baseline.**

**48. Contradiction fixture?** Yes: 110 SUPPORTS and 90 CONTRADICTS, on **one**
Claim identity.

**49. Real aggregator contradiction result?** support 0.6, contradiction 0.5,
masses **0.3 / 0.2 / 0.3 / 0.2** summing to **1.0**.

**50. Semantic mismatch fixture?** `NOT_APPLICABLE`, not CONTRADICTS — Mission
1.46's real case of *de facto* midyear against *usually resident* 1 January
population. It never reaches the aggregator, and the test says so rather than
pretending to execute it.

**51. Dependent-republication fixture?** One group, 0.6, `became_corroboration`
false — Mission 1.46's FRED case. A companion test shows the same two rows under
established independence **do** exceed, so the contrast is demonstrated rather
than asserted.

**52. Post-hoc-threshold fixture?** `POST_HOC`, calibration-ineligible.

---

## What did not happen

**53. Research data requests?** **0.** **54. Documentation requests?** **0**
apparatus and **0** governance — zero of every kind.
**55. Canonical mutations?** **None.** All 16 counters identical; the pytest leak
check reports the database unchanged across 26 tenant tables and global tables
unchanged across 17.
**56. Reliability changes?** **None.** No value assigned, suggested or copied.
**57. Calibration changes?** **None.** `REFERENCE_PROFILE_V1` still UNCALIBRATED.
**58. Model calls?** **0**, 0.00 USD. **59. Embeddings?** **0.**
**60. Opportunity changes?** **None** — 1 / 1 / 7.
**61. Problem-Family status?** **PARKED.**
**62. Zero-dependency tests?** **1175 across 8 packages**, run with bare `python`
using the exact CI runner **before commit** (§34).
**63. Pytest?** **245 across 9 packages**, all passing.
**64. Workspace isolation?** Inspected before the canonical pass: 2 seeded
workspaces, **0 orchestration probes**. No cleanup needed; clean run, both leak
checks green, no test weakened and no failure masked.
**65. Exact counters after?** Identical to question 4.
**66. Primary outcome?**
**`SOURCE_INDEPENDENT_PROPOSITIONS_BELONG_TO_INFERRED_LAYER`.**

---

## §40 — Next

**67. Recommended next mission?** **Mission 1.50 — Deterministic Inferred Claim
Contract V1.** The minimum **additive** implementation contract for
source-attributed OBSERVED inputs → deterministic derivation → source-independent
INFERRED Claim, with derivation provenance and no model use.

It must decide four things this mission deliberately left open:

- **Where the reasoning step lives.** `ClaimDraft.rationale` exists, is wired
  through `_persist_one`, and lands in `research.claims.origin_detail`. It is
  populated on all 43 Claims — with a **provenance** sentence such as *"Restated
  from signal `<id>` (content-request-change@1.0.0)."*, not a reasoning step,
  because an OBSERVED restatement has none. Whether a reasoning step may share a
  column named `origin_detail` is the Mission 1.15.4 shape: one field answering a
  question that is two.
- Whether Evidence attaches directly or a derivation relation is required.
- Where the evaluator lives, given that `validate_claims.py` must stay untouched.
- How a threshold's preregistration status is recorded and enforced.

**Mission 1.50 was not started.**

---

## Artifacts and gates

| file | what it is |
|---|---|
| `ADR-036-source-independent-claim-semantics.md` | the decision, with alternatives and open questions |
| `source-independent-claim-semantics-v1.json` / `.md` | the record and its rendering |
| `render_source_independent_claim_semantics.py` | renders and **validates**; wired into CI |
| `test_source_independent_claim_semantics.py` (evidence-aggregation) | fixtures A/B/D through the real aggregator; C and E asserted, not faked |
| `test_source_independent_identity.py` (claim-model) | the identity rules against the real `proposition_key` |

**The validator was probed rather than trusted: 22 deliberate violations, 22
caught** — `source_id` back in the source-independent identity, `source_id`
dropped from witness provenance, the measurement value made identity, the
threshold removed, direction made identity, OBSERVED losing `source_id`, two
preferred models, no preferred model, a post-hoc threshold made
calibration-eligible, a semantic mismatch marked CONTRADICTS, a republication
marked independent, a republication split into two groups, a contradiction split
across two Claims, masses not summing to one, a historical identity rewritten, a
migration recommended, an invariant dropped, a counter moved, a source selected,
model calls, Problem-Family unparked, and an outcome outside §38.

Gates: `ruff check` and `ruff format --check` clean over 675 files; all ten
generated-document `--check` steps in sync including the new one;
`validate_source_registry`, `validate_signals`, `validate_claims`,
`validate_normalization` all passing.

Governance: `docs/CLAUDE.md` 1.82 → 1.83, `PROJECT_MANIFEST.md` 1.81 → 1.82.
