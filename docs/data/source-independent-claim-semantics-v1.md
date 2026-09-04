# Source-Independent Claim Semantics V1

**Mission 1.49 — recorded 2026-09-04. Decision: ADR-036.**

> **This document is GENERATED.** Edit
> `source-independent-claim-semantics-v1.json` and re-run
> `infrastructure/scripts/render_source_independent_claim_semantics.py`.

## Primary outcome — `SOURCE_INDEPENDENT_PROPOSITIONS_BELONG_TO_INFERRED_LAYER`

The layer already exists, it was defined for exactly this, and nobody has built it. `claim-epistemic-semantics-v1.md` §4 defines INFERRED as a claim that 'asserts something about the world that the measurement is evidence for, and that the source did not itself report' -- which is the source-independent proposition, verbatim, written in Mission 1.13 before the question was asked. No new ClaimType, no subtype and no schema change is required.

Claim-type naming verdict: **`INFERRED_IS_SEMANTICALLY_CORRECT`**.

## The correction that decides it

*Assumption refused:* **INFERRED means model-generated.**

- The taxonomy separates them BY TYPE. `INFERRED` is documented as *derived analytically from one or more observations*; `PREDICTED` is *a model-generated estimate*. The model-associated type is PREDICTED, not INFERRED.
- The taxonomy separates them BY AXIS. `claim_type` is the epistemic category and `interpretation_kind` is the procedure -- DETERMINISTIC or MODEL_DERIVED -- and migration 0016's CHECK constraint ties `interpretation_kind` to the presence of a `model_version`, NOT to `claim_type`. So the two axes are orthogonal by construction.
- The semantics document says it outright: *'A deterministic extractor can produce an INFERRED-type claim, and an LLM can produce an OBSERVED-type one.'* `ClaimOrigin.INFERRED` and `ClaimType.INFERRED` are explicitly named as different fields answering different questions.

**Consequence.** `INFERRED` + `interpretation_kind = DETERMINISTIC` is representable in the current schema today, with no migration. It has simply never been written: all 43 live Claims are OBSERVED, all 43 are DETERMINISTIC, and 0 carry a model_version.

*Measured:* live claim types {'OBSERVED': 43}, interpretation kinds {'DETERMINISTIC': 43}, claims with a model version **0**.

## §1 — The two propositions

### `OBSERVED_SOURCE_ATTRIBUTED_PROPOSITION`

- **Truth condition.** The named source published, counted or reported the stated thing.
- **Falsifier.** The source did not publish, count or report it as claimed.
- **`source_id`.** PROPOSITION IDENTITY
- For an OBSERVED claim the attribution IS the claim (Mission 1.38). 'Wikimedia counted X' and 'Stack Exchange published Y' are two propositions with two different falsifiers. Removing `source_id` would not merge two Claims about one fact; it would rewrite what all 43 existing Claims mean.

### `SOURCE_INDEPENDENT_PROPOSITION`

- **Truth condition.** The stated condition holds of the external phenomenon, not of any publisher.
- **Falsifier.** An incompatible observation under equivalent measurement semantics.
- **`source_id`.** WITNESS PROVENANCE, never proposition identity
- Moving from 'a source reported X' to 'X is the case' is an inference, and §4 requires the assumption to be written down. Without it, the same sentence is *'an OBSERVED claim that quietly dropped its attribution'*.

## §26 — Model comparison

| model | verdict | semantic honesty | historical compatibility | provenance preservation | corroboration reachability | contradiction reachability | reliability compatibility | deterministic rule compatibility | model egress requirement | implementation complexity | calibration usefulness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **A** INFERRED WORLD CLAIM | **PREFERRED** | STRONG | STRONG | STRONG | STRONG | STRONG | STRONG | STRONG | NONE | MEDIUM | STRONG |
| **B** CROSS-SOURCE OBSERVED CONVERGENCE | **REJECTED** | WEAK | MEDIUM | STRONG | STRONG | WEAK | MEDIUM | STRONG | NONE | MEDIUM | MEDIUM |
| **C** DETERMINISTIC MEASUREMENT CLAIM | **UNNECESSARY** | STRONG | STRONG | STRONG | STRONG | STRONG | MEDIUM | STRONG | NONE | WEAK | STRONG |
| **D** DELIBERATELY ABSENT | **REJECTED** | STRONG | STRONG | STRONG | NONE | NONE | STRONG | NOT_APPLICABLE | NONE | NONE | NONE |

**A — INFERRED WORLD CLAIM: PREFERRED.** The reasoning step is stated rather than hidden, which is the whole difference between an inference and a fabrication. It is purely additive: existing OBSERVED Claims keep their meaning and become the INPUTS. And the type already exists with exactly these semantics, so the change is a contract and an evaluator rather than a taxonomy amendment.

**B — CROSS-SOURCE OBSERVED CONVERGENCE: REJECTED.** It fails on the question §2 said not to answer by implementation convenience: can something be OBSERVED if no single source observed THAT proposition? No. The repository already wrote the refutation, in a document that predates the question by many missions: **'An OBSERVED claim that should have been INFERRED is a fabrication with a citation attached.'** A source-independent proposition filed as OBSERVED is precisely an OBSERVED claim that dropped its attribution -- and it would drop it while KEEPING the citations, which is what makes it worse than an honest inference rather than better.

**C — DETERMINISTIC MEASUREMENT CLAIM: UNNECESSARY.** It is semantically sound and it solves a problem that is already solved. The distinction it would encode -- deterministic derivation versus model inference -- is exactly what `interpretation_kind` carries, on an axis orthogonal to `claim_type`. Adding a sixth ClaimType would put one distinction in two places, and `ClaimType` is a closed enum whose amendment needs a new ontology version. **A second answer to a question already answered eventually disagrees with the first.**

**D — DELIBERATELY ABSENT: REJECTED.** It was taken seriously, because §2 forbids dismissing it merely because the aggregator could not then be calibrated, and epistemic conservatism is a real virtue here. It is rejected for a different reason: **it is not actually the conservative option.** The INFERRED layer is already DEFINED in the ontology, in the generated contract and in the epistemic semantics document. Choosing D does not decline to build something; it leaves a defined capability permanently unbuilt while the system keeps producing propositions that cannot corroborate or contradict. And it would not be honest about the cost: the system would remain unable to say that two sources disagree, which is the one signal that tells an operator to go and look.

## §4 — Which inferences may create a source-independent proposition

| kind | can create one | note |
| --- | --- | --- |
| `DETERMINISTIC_DERIVATION` | **YES** | Exact, reproducible from the inputs and the parameters alone. Carries `interpretation_kind = DETERMINISTIC`, no model and no prompt. This is the only kind Mission 1.50 should implement. |
| `RULE_BASED_INFERENCE` | **YES_WITH_A_STATED_RULE** | Deterministic, but the RULE is a judgement somebody made. It needs its own provenance and review, and it must not be smuggled in as part of the comparison. |
| `STATISTICAL_INFERENCE` | **NOT_YET** | Would require parameters this project has never fitted and a calibrated profile that does not exist. Out of scope. |
| `MODEL_ASSISTED_INFERENCE` | **PERMITTED_BY_SEMANTICS_NOT_BY_THIS_MISSION** | The semantics already allow it -- `MODEL_DERIVED` interpretation of an INFERRED claim -- with the model as provenance and never as evidence. Mission 1.50 must not use it. |
| `GENERATIVE_SYNTHESIS` | **NO** | A latent behavioural construct. Not a derivation from measurements at all, and §14's invariant forbids promoting it silently. This is the act that must never be confused with `110 >= 100`. |

**`110 >= 100` and 'developers want Docker' are both called inference in ordinary speech and are not the same epistemic act. The first is a comparison whose result anyone can recompute from the inputs; the second invents a construct the measurement never observed. Filing both under one word is how the second acquires the credibility of the first.**

## §8 / §9 / §10 — Identity for the source-independent layer

*Nothing here applies retroactively to OBSERVED Claims.*

**Proposition identity:** `claim_type`, `proposition`, `canonical_subject_id`, `metric_definition_id`, `time_bound`, `population_or_geography`, `unit`, `threshold_operator`, `threshold_value`

**Witness provenance:** `source_id`, `resource_id`, `source_native_metric_id`, `source_native_subject_id`, `measurement_value`, `measurement_timestamp`, `methodology_version`, `record_locator`

| fact | in identity? | why |
| --- | --- | --- |
| threshold | **True** | `M >= 100` and `M >= 200` are different propositions with different falsifiers. The threshold is what the Claim asserts. |
| measurement value | **False** | This is the load-bearing exclusion. If the observed value were identity, 110 from source A and 105 from source B would produce two different Claims -- which is the exact failure Mission 1.48 diagnosed, reproduced one layer up. The value is what a WITNESS reports; the threshold is what the CLAIM asserts. |
| `source_id` | **False** | A source-independent proposition is about the phenomenon. If `source_id` were identity, two sources could never share the Claim and the whole layer would be pointless. |
| direction | **False** | SUPPORTS and CONTRADICTS are Evidence direction relative to a FIXED proposition, not facts about which proposition it is. This is the precise inversion of the OBSERVED layer, where Mission 1.48 found `direction` IS identity -- and it is why the same measurement stream that cannot contradict at the OBSERVED layer can contradict at this one. |

**Provenance is preserved.** In the witness provenance of every Evidence row, and through the full existing chain: Evidence -> Signal -> signal_inputs -> NormalizedRecord -> RawRecord -> Source. **Source independence of the PROPOSITION must never mean provenance loss.**

## §18 — The evaluation function

`evaluate_measurement_against_claim(claim, measurement) -> SUPPORTS | CONTRADICTS | NOT_APPLICABLE | UNKNOWN`

| outcome | condition |
| --- | --- |
| **SUPPORTS** | measurement semantics are equivalent to the Claim's AND value satisfies the threshold operator |
| **CONTRADICTS** | measurement semantics are equivalent to the Claim's AND value does not satisfy the threshold operator |
| **NOT_APPLICABLE** | measurement semantics are NOT equivalent -- a different population, unit, period, adjustment or metric definition. The measurement bears on a different proposition and must not be attached |
| **UNKNOWN** | measurement-equivalence or provenance cannot be established. Attaches nothing rather than guessing |

*Every branch is a comparison over canonical values under a declared equivalence. Nothing here needs a model, and a probability would be a number nobody fitted.*

## §12 / §13 — Two gates, and neither implies the other

**Measurement equivalence** over: metric definition, subject, time, population, geography, unit, adjustment, methodology semantics.

A source can be independent and measure something DIFFERENT, in which case its disagreement is not disagreement. A source can measure exactly the same thing and be a REPUBLICATION, in which case its agreement is not corroboration. **Both gates are required and neither implies the other**, which is Mission 1.46 and Mission 1.47 stated as one rule.

**Independence is a property of Evidence provenance, never of Claim identity.** One source-independent Claim may carry Evidence that is UNKNOWN, KNOWN_INDEPENDENT and KNOWN_DEPENDENT at once, and its MEANING does not change. Only the aggregation over it changes.

*Putting independence in Claim identity would make the same proposition become a different proposition when a reviewer learned something about provenance, which is a fact about our knowledge rather than about the world.*

## §14 / §15 — Reliability

Scope is unchanged and stays source-relative: `source_id`, `resource_id`, `record_kind_id`, `claim_type`, `proposition_kind`.

**Why that is compatible.** Claim IDENTITY and Evidence reliability SCOPE are different things, and this is the resolution of the apparent conflict. The Claim's proposition is source-independent; the Evidence attached to it is still a particular source's measurement, and reliability still asks *how dependably does THIS source's measurement support THIS kind of proposition*. That question is still source-relative, so the five-part scope is unchanged.

A source-independent proposition_kind, and `claim_type = INFERRED`, both differ from every existing scope. So every Evidence row attached to such a Claim would resolve NO_APPLICABLE_ASSESSMENT until a human reviews that scope. **No value is inherited by proposition similarity**, and none is assigned here.

- **MEASUREMENT_RELIABILITY** — How dependable is the source's measurement? A human judgement against documentary basis.
- **DERIVATION_VALIDITY** — Does 110 entail >= 100? Exact, deterministic, and either true or false.

**They must never be multiplied.** They are different kinds of quantity and there is no coefficient that combines them. Multiplying an exact entailment by a reviewed reliability would produce a number that is neither, and would let a sound derivation look doubtful because its input is uncertain -- which the four-mass decomposition already represents correctly through uncertainty mass.

## §16 / §17 — Derivation provenance and preregistration

- `derivation_rule_id`
- `derivation_rule_version`
- `input_signal_ids and/or input_claim_ids`
- `preregistered parameters including the threshold`
- `threshold_provenance_status`
- `created_at`
- `claim_type`
- `interpretation_kind`

*`ClaimDraft.rationale` exists in the model, is wired through `_persist_one`, and lands in `research.claims.origin_detail`. It is populated on all 43 live Claims -- with a PROVENANCE sentence such as *'Restated from signal <id> (content-request-change@1.0.0).'*, not a reasoning step, because an OBSERVED restatement has no reasoning step to record. Whether a reasoning step may share a column named `origin_detail` is a design question for Mission 1.50: it is the shape Mission 1.15.4 warned about, one field answering a question that is two. **It is recorded and not repaired here.***

| threshold provenance | meaning | calibration eligible |
| --- | --- | --- |
| `PREREGISTERED` | the threshold was frozen and recorded BEFORE any candidate measurement was inspected | **yes** |
| `SOURCE_NATIVE` | the threshold is published by the source itself or by an external standard the source names | **yes** |
| `EXTERNAL_NORM` | the threshold comes from a named external norm, standard or regulation independent of this project | **yes** |
| `POST_HOC` | the threshold was chosen after inspecting candidate measurements | **no** |
| `UNKNOWN` | the provenance of the threshold is not recorded | **no** |

A POST_HOC or UNKNOWN threshold may still produce a Claim -- the proposition is not false because its bound was chosen late -- but it is CALIBRATION_INELIGIBLE. A threshold picked to make a case work measures the analyst, and Mission 1.24 refused a rule rewritten after the fact for the same reason: a rule rewritten after seeing the result was never binding.

*UNKNOWN is calibration-ineligible rather than assumed preregistered. Uncertainty is never permission.*

## §19 / §28 — Where the evaluation lives

**Option B.**

- A: existing interpreter framework -- REFUSED
- B: a separate evaluator -- PREFERRED
- C: a Claim derivation service -- a plausible later shape of B
- D: the Opportunity engine -- REFUSED, wrong layer entirely
- E: nowhere yet -- rejected, since the semantics are now decided

**Why separate.** `validate_claims.py` fails the build on any `ClaimType.X` access in the interpretation package where X is not OBSERVED, over the AST. That guard is CORRECT and must be left alone: it is what keeps the source-attributed OBSERVED contract from being widened by accident. Putting source-independent evaluation in the same package would require weakening it, and **a guard removed to let new work through is a guard that never was**. A separate evaluator keeps the OBSERVED interpreter exactly as narrow as it is.

Future boundary: `OBSERVED source fact -> deterministic evaluation -> INFERRED source-independent Claim -> Evidence SUPPORTS/CONTRADICTS -> aggregation`

Evidence attachment: Option 2 -- Evidence links the SIGNAL and its OBSERVED provenance to the source-independent Claim. Option 1 loses the reasoning step's inputs; option 3 (a ClaimRelation) is more machinery than the case needs today and is recorded as a possible refinement rather than a requirement.

## §20 — Cross-source OBSERVED convergence, reconsidered

**`NO_LONGER_NEEDED_FOR_WORLD_PROPOSITIONS`.** Mission 1.47 wanted a cross-source OBSERVED convergence contract because it was the only visible route to two Evidence rows on one Claim. With the INFERRED layer decided, world-level propositions have a correct home and the contract is not needed for them. What remains legitimately OBSERVED is what a source itself observed.

*`SourceBoundary` still has one member and was not touched. Mission 1.47's finding that the contract structurally refuses cross-source propositions is now a FEATURE rather than a gap: it is the mechanism keeping OBSERVED honest.*

## §24 — Semantic invariants

- **I1.** Existing OBSERVED Claims remain source-attributed.
- **I2.** `source_id` remains proposition identity for OBSERVED.
- **I3.** A source-independent Claim's proposition identity must not contain `source_id`.
- **I4.** A source-independent Claim's provenance must still carry `source_id` per witness.
- **I5.** The observed measurement value is a witness fact, never THRESHOLD_STATE proposition identity.
- **I6.** Threshold operator and threshold value are proposition identity.
- **I7.** Evidence direction is relative to the fixed proposition, never part of its identity.
- **I8.** Different measurements may SUPPORT or CONTRADICT the same source-independent Claim.
- **I9.** Semantic measurement equivalence is required before attachment.
- **I10.** Independence is evaluated separately from semantic equivalence, and neither implies the other.
- **I11.** Reliability remains source-scoped and five-part.
- **I12.** No reliability inheritance by proposition similarity.
- **I13.** No source-independent Claim without derivation provenance.
- **I14.** No latent construct silently promoted to deterministic inference.
- **I15.** Historical Claims remain immutable in meaning.

## §25 — Fixtures

**A — independent corroboration.** `M >= 100`, witnesses 110 and 105, both KNOWN_INDEPENDENT → **2 support groups**, strength **0.8** against a strongest member of 0.6. The first shape in this repository that would make the full aggregator differ from the B-2 baseline.

**B — contradiction.** Same Claim identity: **True**. Support 0.6, contradiction 0.5, masses 0.3 / 0.2 / 0.3 / 0.2 summing to **1.0**. Both witnesses inhabit ONE Claim because the measurement value is not identity. That is the whole architectural point, demonstrated.

**C — semantic mismatch.** Expected **NOT_APPLICABLE**, not CONTRADICTS. Mission 1.46's real case. A shared year label is not a shared reference date, and a measurement of a different quantity is not a disagreement about this one. It never reaches the aggregator.

**D — dependent republication.** 1 support group, strength 0.6, became corroboration: **False**. Mission 1.46's FRED case. Both attach to the Claim and collapse into ONE group, so republication raises observed volume and not evidence strength.

**E — post-hoc threshold.** `POST_HOC`, calibration eligible: **False**. The Claim is not false; it is ineligible as a calibration case.

## §21 — Historical compatibility

Claims **43**, revisions **44**, Evidence **57** — all unchanged. Proposition identities rewritten: **0**. Migrations recommended: **0**.

The decision is purely ADDITIVE. Every existing Claim keeps its proposition identity, its meaning and its Evidence, and becomes an INPUT to the new layer rather than being reinterpreted by it. No migration that changes the meaning of a historical Claim is recommended, now or later.

## Counters and budget

| counter | before | after |
| --- | ---: | ---: |
| raw_records | 325 | 325 |
| normalized_records | 325 | 325 |
| signals | 33 | 33 |
| claims | 43 | 43 |
| claim_revisions | 44 | 44 |
| evidence | 57 | 57 |
| reliability_assessments | 4 | 4 |
| reliability_basis_rows | 12 | 12 |
| independence_groups | 0 | 0 |
| opportunities | 1 | 1 |
| opportunity_revisions | 1 | 1 |
| opportunity_evidence_links | 7 | 7 |
| embeddings | 0 | 0 |
| registered_sources | 29 | 29 |
| evidence_with_stored_reliability | 0 | 0 |
| scores | ABSENT | ABSENT |

Model calls **0**, 0.00 USD, embeddings **0**, Problem-Family **PARKED**, source selected **NONE**.

## Next mission

**Mission 1.50 -- Deterministic Inferred Claim Contract V1** — The minimum ADDITIVE implementation contract for: source-attributed OBSERVED inputs -> deterministic derivation -> source-independent INFERRED Claim, with derivation provenance and no model use.

It must decide:

- whether the reasoning step may share `origin_detail` or needs its own column
- whether Evidence attaches directly or a derivation relation is required
- where the evaluator lives, given that `validate_claims.py` must stay untouched
- how a threshold's preregistration status is recorded and enforced

It must not: use a model, widen SourceBoundary, add a ClaimType member, alter proposition_key, touch an existing Claim.

*Mission 1.50 was not started.*

