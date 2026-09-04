# Deterministic Inferred Claim Contract V1

**Mission 1.50 — recorded 2026-09-04. Decision: ADR-037, building on ADR-036.**

> **This document is GENERATED.** Edit
> `deterministic-inferred-claim-contract-v1.json` and re-run
> `infrastructure/scripts/render_deterministic_inferred_contract.py`.

## Primary outcome — `DETERMINISTIC_INFERRED_CLAIM_CONTRACT_READY`

All four mandatory questions are resolved and the implementation boundary is precise. The contract needs an additive schema extension, fully specified here, because the repository has no durable structured place for a derivation record: the only per-(signal, claim) table it owns hangs off an interpretation run that carries `expires_at` and cascades on delete, so a Claim would outlive its own reasoning.

**Schema necessity: `BOTH_REQUIRED`.**

| area | verdict |
| --- | --- |
| `CLAIM_STORAGE` | NO_CHANGE_REQUIRED -- `research.claims` already carries claim_type, interpretation_kind, proposition_key and proposition_facts, and ADR-036 established that INFERRED + DETERMINISTIC is representable today. |
| `EVIDENCE_STORAGE` | NO_CHANGE_REQUIRED -- `scoring.evidence` already carries signal_id, claim_id, direction, independence_state and source_id, which is exactly the attachment the contract needs. |
| `DERIVATION_PROVENANCE` | SCHEMA_REQUIRED |
| `THRESHOLD_PROVENANCE` | SCHEMA_REQUIRED |
| `EVALUATION_AUDIT` | COVERED_BY_DERIVATION_PROVENANCE -- a separate audit table would be a second authority for the same fact. |

## The four mandatory questions

### Q1 — Where does derivation / reasoning provenance live?

**Selected: model B.**

| model | verdict | why |
| --- | --- | --- |
| **A** Reuse `origin_detail` for both provenance and reasoning | `REJECTED` | It is the Mission 1.15.4 failure shape exactly: one free-text field answering two independent questions. `origin_detail` currently answers *where did this Claim come from* on all 43 Claims, with sentences such as 'Restated from signal <id> (content-request-change@1.0.0).' A derivation reasoning step answers *why does this measurement satisfy this proposition*. Putting both there means no reader and no query can tell which question a given sentence answers, and the field acquires two canonical authorities. |
| **B** Keep `origin_detail` as origin, add explicit derivation provenance | `SELECTED` | It preserves ONE canonical semantic responsibility per field. `origin_detail` keeps answering where the Claim came from -- for an INFERRED Claim it would say which evaluator produced it, exactly as it says which interpreter restated a Signal today. The derivation record answers the separate question, in structured form, and is the thing a later calibration mission can query. |
| **C** Use an existing structured field or run record | `REJECTED_ON_A_MEASURED_FACT` | `research.claim_interpretation_inputs` is the closest existing structure: one row per (run, signal) carrying role, claim_id, reason_code and detail, 64 rows live. It cannot be the canonical derivation authority, and the reason is checkable rather than aesthetic. It hangs off `research.claim_interpretation_runs`, ALL 12 of whose rows carry a populated `expires_at` roughly 90 days out, and the foreign key from inputs to runs is **ON DELETE CASCADE**. So when a run expires and is removed, every input row goes with it -- and the Claim would outlive the record of how it was derived. **A retention-bounded execution log cannot hold durable epistemic provenance.** `proposition_facts` was also considered and rejected: it is the preimage of the proposition KEY, so putting derivation facts there would make them identity. |
| **D** No persistent reasoning representation yet | `REJECTED` | ADR-036 requires that a source-independent Claim carry derivation provenance (invariant I13), and `claim-epistemic-semantics-v1.md` §4 requires an INFERRED claim to say what reasoning work it did. A Claim whose reasoning exists only in a prose sentence cannot be re-verified, and a deterministic derivation that cannot be replayed is not deterministic in any useful sense. |

### Q2 — How does Evidence attach to the INFERRED Claim?

**Selected: model A — Direct Signal -> INFERRED Claim Evidence, with derivation provenance recorded separately.**

Existing architectural intent already says so. `claim-epistemic-semantics-v1.md` §4: an INFERRED claim carries *'the Signals it reasoned from, as Evidence'*. That is exact and unambiguous, so it is treated as intent rather than reopened. It also reuses the Evidence contract unchanged, preserves the full RawRecord chain, and feeds the aggregator that already consumes Evidence.

| model | verdict | why |
| --- | --- | --- |
| **A** | `SELECTED` | Signal is the witness; Evidence carries SUPPORTS or CONTRADICTS relative to the fixed proposition; derivation provenance separately records HOW the Signal was evaluated. The two answer different questions and neither substitutes for the other. |
| **B** | `REJECTED` | Claim-to-Claim relation with Evidence left on the OBSERVED Claim. The aggregator consumes Evidence, not Claim relations, so this would need proxy Evidence anyway -- more machinery for the same result, and a second place the epistemic chain lives. |
| **C** | `REDUNDANT` | Direct Evidence PLUS a Claim-to-Claim relation. The relation would restate what Evidence plus derivation provenance already say. Rejected as a second authority rather than as wrong. |
| **D** | `REJECTED` | A new Evidence subtype. The strong presumption against it holds: current Evidence semantics represent the relationship exactly, because direction is already claim-relative. |

*why both:* Evidence attachment answers WHICH observation bears on this Claim and in which direction. Derivation provenance answers HOW that direction was determined, under which rule, against which threshold, and on what equivalence basis. Collapsing them would make the aggregator's input carry an audit trail it does not read, or leave the audit trail unrecorded.

### Q3 — Where does the deterministic evaluator live?

**Selected: model A — a new package, specified here and NOT created.**

The interpreters live in `services/nlp/python/sros_nlp/interpreters/` and `validate_claims.py` fails the build on any non-OBSERVED `ClaimType` access there, over the AST. Hosting the INFERRED evaluator in that package would require weakening that guard, and **a guard removed to let new work through is a guard that never was**. A separate package keeps the OBSERVED interpreter exactly as narrow as it is.

*why not claim model:* `claim-model` owns what a Claim IS -- the model and `proposition_key`. An evaluator is a PRODUCER. The repository already keeps that separation: the OBSERVED interpreters are not in `claim-model` either.

*why not evidence aggregation:* That package must not name a source and must not know about Claims beyond the items handed to it; an AST test asserts no registered source id appears in it. An evaluator reads source-native measurements, so it cannot live there.

*why not opportunity engine:* Wrong layer entirely, and §11 forbids the evaluator from doing Opportunity work.

Proposed package: `packages/inferred-claim-evaluator` — **not created**.

- allowed dependencies: `sros-contracts`, `sros-claim-model`, `sros-signal-model`
- forbidden dependencies:
  - `sros_acquisition` — a component able to read the source registry could decide its own authorization -- the argument that put `semantic-equivalence` in its own package
  - `sros_llm_gateway` — a package that cannot import a provider cannot call one by accident, and §32 requires 0 model calls
  - `sros_evidence_aggregation` — the evaluator emits Evidence; it must not also aggregate it, or scoring and evidence production become one step
  - `sros_opportunity` — separation from Opportunity synthesis

*All three allowed dependencies are already in the bare-python runner's suite list, so the package would join it without a workspace-wide install. Mission 1.47's CI failure remains load-bearing.*

*No package directory, no module and no production code was created. §38 forbids creating production package code merely to host tests, so this mission's contract tests live in `claim-model` (identity) and `evidence-aggregation` (aggregation) -- the packages that already own the rules being proved.*

### Q4 — Where and how is threshold provenance recorded and enforced?

**Selected: model C — a dedicated parameter-registration record, referenced by the derivation.**

A threshold has its own lifecycle, independent of any Claim: it must be frozen BEFORE the measurements it will be compared against, and one registered threshold may be referenced by many derivations over time. Putting it on the Claim would tie a parameter's registration moment to a Claim that does not exist yet, which is the wrong way round.

*why not on claim:* It would make the registration inseparable from the first Claim that used it, and would invite the status to drift into proposition identity.

*why not in the derivation record:* The derivation record is per evaluation. A threshold referenced by three evaluations would be registered three times, and three registrations of one parameter can disagree.

*why not identity:* `M >= 100` with a PREREGISTERED threshold and `M >= 100` with a POST_HOC threshold are THE SAME PROPOSITION. They assert the same thing about the world and have the same falsifier. What differs is calibration eligibility, which is a fact about how the bound was chosen and not about what is being claimed. Making provenance identity would fork one proposition into several.

## §2 — The derivation provenance record

Binds to **CLAIM_REVISION**. A threshold proposition can stay the same while the derivation rule version, the inputs or the rationale change. Binding to the Claim would let a later derivation silently rewrite the reasoning behind an earlier revision; binding to the revision keeps the append-only guarantee the claim model already gives statements. §19.

Granularity: **ONE_RULE_PLUS_MANY_EVALUATIONS**. §20. A single Claim-level rationale is insufficient the moment two sources take different Evidence directions: one prose sentence cannot explain both why A supports and why C contradicts. So the rule is registered once and each evaluation is its own record.

| field | audit question it answers |
| --- | --- |
| `derivation_rule_id` | which rule was applied? |
| `derivation_rule_version` | which version of it, so the result can be replayed? |
| `evaluator_version` | which code produced this, distinct from the rule it applied? |
| `claim_revision_id` | which exact revision of which Claim does this reasoning belong to? |
| `input_signal_id` | which observation was evaluated? |
| `input_observed_claim_id` | which source-attributed Claim, where one was used as input; nullable |
| `measurement_value` | what value was compared? A witness fact, never proposition identity |
| `threshold_registration_id` | which registered threshold was it compared against? |
| `evaluation_result` | SUPPORTS, CONTRADICTS, NOT_APPLICABLE or UNKNOWN? |
| `semantic_equivalence_basis_id` | on what basis was this measurement judged to measure the Claim's quantity? |
| `interpretation_kind` | deterministic or model-derived? |
| `model_version` | which model, if any? Expected NULL for deterministic, and the existing CHECK constraint already enforces the pairing |
| `rationale` | what does this say in a sentence a person can read? |
| `created_at` | when was this evaluation performed? |

**Deliberately absent.**

- `derivation_confidence` — §16. `110 >= 100` is exact. A confidence on an exact entailment would be a number nobody fitted, invented because a numeric column exists elsewhere.
- `reliability` — reliability is a property of the source's measurement against a scope, resolved late from an assessment. It has no place in a derivation record.
- `independence` — independence is an Evidence provenance property and is evaluated separately (ADR-036 invariant I10).
- `calibration_eligible` — derivable from the referenced threshold registration's status. Storing it would create a second authority that can disagree with the first.

## §4 / §25 — The threshold registration record

| field | audit question it answers |
| --- | --- |
| `threshold_registration_id` | which registration? |
| `operator` | which comparison? GTE, GT, LTE, LT |
| `threshold_value` | what bound? |
| `unit` | in what unit, so the bound is comparable at all? |
| `metric_definition_id` | a bound on WHAT quantity? |
| `scope` | which subject, population and time bound does this registration apply to? |
| `provenance_status` | PREREGISTERED, SOURCE_NATIVE, EXTERNAL_NORM, POST_HOC or UNKNOWN? |
| `recorded_at` | when was the bound frozen? The timestamp the preregistration rule compares |
| `provenance_reference` | where did the bound come from -- the norm, the source document, or the registering decision? |
| `recorded_by` | who or what froze it? |

| status | meaning | calibration eligible |
| --- | --- | --- |
| `PREREGISTERED` | The bound was frozen and recorded by this system before the measurements it will be compared against became available to the decision process. | **yes** |
| `SOURCE_NATIVE` | The bound is supplied by the source itself as part of its own measurement contract, so it was not chosen by this project at all. | **yes** |
| `EXTERNAL_NORM` | The bound comes from a separately authoritative external rule, standard or regulation, independent of this project and of the source. | **yes** |
| `POST_HOC` | The bound was selected after candidate measurements were available to the decision process. | **no** |
| `UNKNOWN` | The timing or origin of the bound cannot be established from what is recorded. | **no** |

### §23 — What preregistered means, exactly

    threshold_registration.recorded_at < observation.retrieved_at, for every measurement the derivation evaluates.

**Retrieved, not published.** The bias preregistration guards against is the ANALYST'S, and an analyst can only be influenced by data that reached them. A measurement may have been public for years before this system retrieved it, and a bound frozen in that window was not chosen with knowledge of it. Using `published_at` would mark such a bound POST_HOC for a hindsight that did not occur.

*Not commit time either:* A commit records when a file changed, not when a measurement became available to the decision process, and the two can differ in either direction. It is evidence about the bound's recording, not about the comparison the rule needs.

**The limit, stated rather than hidden.** This relation is NECESSARY and machine-checkable. It is NOT SUFFICIENT to exclude human foreknowledge: a person could have read a public figure outside this system before registering the bound, and no timestamp in this repository can detect that. So PREREGISTERED means *this system did not hold the measurement when the bound was frozen*, and it does not mean *nobody knew*. A future calibration mission must not read it as the stronger claim.

## §3 — Structured facts versus prose

Machine-auditable: `derivation_rule_id`, `derivation_rule_version`, `operator`, `threshold_value`, `measurement_value`, `evaluation_result`, `threshold provenance_status`, `input_signal_id`, `semantic_equivalence_basis_id`.

Human-readable: `rationale` — An explanation for a reader, generated deterministically from the structured facts by the evaluator's own template. It is never the only record of a load-bearing fact, and it is never a second authority for one.

**Every load-bearing fact has exactly ONE canonical authority, and it is the structured field. The rationale may RESTATE structured facts in a sentence; it may not CARRY one that appears nowhere else, and nothing may read it back as data.**

*The rationale is template-owned and deterministic. §32 forbids model-generated prose here, and a generated sentence would also break the replay guarantee.*

## §12 — Evaluation results and their mapping

| result | condition | persisted Evidence |
| --- | --- | --- |
| **SUPPORTS** | equivalence established AND the measurement satisfies the operator against the threshold | EvidenceDirection.SUPPORTS |
| **CONTRADICTS** | equivalence established AND the measurement does not satisfy it | EvidenceDirection.CONTRADICTS |
| **NOT_APPLICABLE** | semantic equivalence FAILS -- a different population, unit, period, adjustment or metric definition | NO EVIDENCE ROW. The measurement bears on a different proposition. |
| **UNKNOWN** | equivalence can be neither established nor refuted from what is documented | NO DIRECTIONAL EVIDENCE ROW. |

**UNKNOWN is not neutral.** UNKNOWN must not become a NEUTRAL Evidence row. `NEUTRAL` asserts that an observation bears on the Claim without bearing either way, which is a positive finding; UNKNOWN says we could not establish that it bears on it at all. The existing interpretation contract already refuses to generate NEUTRAL rows for the same reason.

**A mismatch is not a contradiction.** NOT_APPLICABLE must never become CONTRADICTS. A measurement of a different quantity is not a disagreement about this one -- Mission 1.46's midyear de facto against 1 January usually-resident population is the real case.

*NOT_APPLICABLE and UNKNOWN produce a derivation record with that result and NO Evidence row, so the refusal is auditable rather than invisible. This mirrors ADR-021 and ADR-025: a refused derivation gets a run record and never a Signal or a Claim.*

## §13 — Measurement equivalence

Required over: canonical subject, metric definition, time bound, population, geography, unit, adjustment, methodology semantics.

**Established: BOTH.** A reviewed equivalence basis is registered once per (metric definition, source-native measurement) pair, because judging that two publishers measure the same quantity is a documentary judgement a person makes. The evaluator then checks deterministically, per measurement, that the specific record matches the registered basis on subject, period, population and unit. The review answers *can these ever be compared*; the per-measurement check answers *is THIS record one of them*.

*The evaluator must never infer equivalence from matching identifiers, labels or field names. Mission 1.46 found a shared year label covering two different reference dates, and Mission 1.30's registry established the standard: exact equality against a reviewed entry, with no distance, stem, synonym table or embedding.*

*Absence of a registered basis yields UNKNOWN, never SUPPORTS and never a guess.*

## §14 — What is source-independent and what is not

- Claim identity: **SOURCE_INDEPENDENT**
- Evidence witness: **SOURCE_SPECIFIC**
- Reliability scope: **SOURCE_SPECIFIC**
- Independence: **EVIDENCE_PROVENANCE_PROPERTY**

> M >= 100 at T, under definition D and unit U

| source | measurement | direction | reliability scope |
| --- | ---: | --- | --- |
| A | 110 | **SUPPORTS** | scope A |
| B | 105 | **SUPPORTS** | scope B |
| C | 90 | **CONTRADICTS** | scope C |

**One Claim, three source-specific witnesses, three reliability scopes, one proposition. Two of them agree and one disagrees, and the Claim's meaning is unchanged by any of it.**

## §15 / §16 / §17 — Reliability, derivation validity, interpretation confidence

Reliability scope unchanged: `source_id`, `resource_id`, `record_kind_id`, `claim_type`, `proposition_kind`.

NO_APPLICABLE_ASSESSMENT for every source and scope, because a new INFERRED proposition_kind with claim_type INFERRED matches no existing assessment. That is correct, and no reliability work was done in this mission.

*The implementation must not inherit OBSERVED reliability, adjacent proposition reliability, or another source's value.*

**Whether the source's 110 is dependable is a human judgement against documentary basis. Whether 110 satisfies `>= 100` is exact. They are different kinds of quantity and no coefficient combines them.**

### `interpretation_confidence`

> Confidence that THIS WORDING faithfully states what the cited Signals showed. Never a market confidence and never an EvidenceScore.

Mandatory for automated claims: **True**. `build_claim` refuses an automated claim with `interpretation_confidence is None`, citing INTERPRETER_PROVENANCE_INCOMPLETE: *'an automatically generated claim states how confident its interpretation was. That is confidence the SENTENCE reads the Signals correctly, and it is not an evidence strength'*. The column is nullable with a [0,1] CHECK; the model is what makes it mandatory.

**Answer: C.** It is confidence in the SEMANTIC-EQUIVALENCE MAPPING, not in the arithmetic. The field asks whether the wording faithfully states what the cited Signals showed. For an OBSERVED restatement that is the whole job, and the interpreters set 1.0 because *'a template applied to structured facts is certain it read them correctly'*. For a deterministic INFERRED threshold Claim there is an ADDITIONAL step the OBSERVED case does not have: asserting that the source-native measurement is a measurement of the Claim's quantity under its definition and unit. That assertion is exactly what the field's documented meaning covers, and it is a real judgement rather than an exact one.

*Setting 1.0 would assert certainty that the equivalence mapping is right, which is not established by the arithmetic being exact. §16 warns against it and the warning is correct: the derivation being exact says nothing about whether the wording faithfully reads the Signal.*

Semantic gap: **False**. INTERPRETATION_CONFIDENCE_SEMANTIC_GAP is deliberately NOT reported. The field's documented meaning accommodates deterministic INFERRED without strain, and it lands on the one genuinely uncertain step in the derivation. No change to the field, its constraint or its semantics is required or proposed.

## §22 — Idempotency

| entity | key | basis |
| --- | --- | --- |
| `derived_claim` | `workspace_id + proposition_key` | The existing convention. `_persist_one` looks a draft up by `proposition_key` and attaches Evidence to whatever Claim it finds, which is what lets several witnesses reach one Claim at all. |
| `evidence` | `workspace_id + claim_id + signal_id` | Mission 1.41's repair. `extraction_method` was REMOVED from the deciding key because Evidence identity is epistemic while the procedure that produced it is provenance -- otherwise an evaluator version bump would INSERT a duplicate row, which is the defect that bit twice in Missions 1.32 and 1.40. |
| `derivation_record` | `workspace_id + claim_revision_id + input_signal_id + derivation_rule_version` | Deliberately DIFFERENT from the Evidence key, and the difference is the point. Evidence must not duplicate when the rule version changes, because the epistemic relation is unchanged. A derivation record MUST be distinct per rule version, because replaying a different rule is a different piece of reasoning about the same relation. Same shape as the claim/revision split: the relation is stable, the reasoning is versioned. |

Must prevent: duplicate Evidence rows, duplicate evaluations, duplicate derived Claims.

*merge distinct derivations accidentally -- two rule versions over one signal are two records, not one overwritten.*

## §11 — Evaluator responsibility

**It must:**

- receive a source-native measurement witness
- validate measurement-equivalence eligibility
- locate a registered threshold definition
- evaluate the deterministic predicate
- emit an INFERRED ClaimDraft
- emit an Evidence direction relative to that Claim
- emit derivation provenance

**It must not:**

- score reliability
- decide independence
- call a model
- create or touch an Opportunity
- choose a threshold after seeing measurements
- infer latent behaviour
- perform source governance
- acquire data

## §26 — Fixtures

**A — two independent supports.** `M >= 100`, threshold `PREREGISTERED`, measurements 110 and 105. Same proposition key: **True**. **2 support groups**, strength **0.8** against a strongest member of 0.6.

**B — contradiction.** Same Claim identity: **True**. Contradiction 0.5, masses 0.3 / 0.2 / 0.3 / 0.2 summing to **1.0**.

**C — semantic mismatch.** Result **NOT_APPLICABLE**, Evidence rows **0**, derivation record **True**. The refusal is recorded so it is auditable, and no Evidence row exists to reach the aggregator.

**D — unknown equivalence.** Result **UNKNOWN**, Evidence rows **0**, derivation record **True**. UNKNOWN never becomes SUPPORTS and never becomes a NEUTRAL row.

**E — dependent republication.** 1 support group at 0.6; became independent corroboration: **False**.

**F — post-hoc threshold.** Result **SUPPORTS**, logically valid **True**, calibration eligible **False**. §5. The Claim is logically supported and the bound was chosen with hindsight. Provenance changes calibration eligibility, never logical entailment.

## Historical compatibility, counters and budget

Claims **43**, revisions **44**, Evidence **57** — unchanged. OBSERVED identity changed: **False**. Migrations created: **0**. INFERRED Claims created: **0**.

Purely additive. No existing Claim, Evidence row or proposition identity is touched, and `validate_claims.py`, `SourceBoundary` and `proposition_key` are all unmodified.

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
| inferred_claims | 0 | 0 |
| scores | ABSENT | ABSENT |

Model calls **0**, 0.00 USD, embeddings **0**, Problem-Family **PARKED**, source selected **NONE**, migration created **False**.

## Next mission

**Mission 1.51 -- Deterministic Derivation Provenance Schema V1**

§44's branch for a ready contract that requires a schema extension. The two records specified here -- derivation provenance and threshold registration -- must exist before an evaluator can write anything, and implementing the evaluator first would mean holding its output nowhere.

Scope: Implement only the frozen schema contract: the two additive tables, their constraints, and their idempotency keys. No evaluator, no INFERRED Claim, no source.

It must not: create an INFERRED Claim, implement the evaluator, select a source, acquire data, weaken validate_claims.py.

*Mission 1.51 was not started.*

