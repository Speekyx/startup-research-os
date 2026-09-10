# second-opportunity-synthesis-output@1.0.0

Generated from `second-opportunity-synthesis-output-contract-v1.json`. Do not edit by hand.

Mission 1.84. One machine-readable schema and one deterministic gate, both frozen before execution. Lexical filtering does not prove semantic safety and this contract does not claim it does: what it cannot name is why the execution stops for a human.

- schema `second-opportunity-synthesis-output@1.0.0` `9f8e3849fb0223f5a4c41466d8d8aed994e1d86d446a52e9eca1fd28d80f65e9`
- gate `second-opportunity-output-gate@1.0.0`
- base gate `opportunity-synthesis-persistence-gate@1.1.0`, base audit `opportunity-synthesis-audit@1.2.0`
- 20 required fields

## Required fields

- `decision`
- `subject`
- `target_actor_if_supported`
- `observed_need`
- `candidate_intervention_class`
- `hypothesis_statement`
- `supported_dimensions`
- `unsupported_dimensions`
- `supporting_evidence_ids`
- `supporting_claim_ids`
- `source_families`
- `independence_status`
- `reliability_status`
- `evidence_bound_reasoning_summary`
- `critical_uncertainties`
- `commercial_claims_supported`
- `commercial_claims_not_supported`
- `recommended_next_evidence`
- `confidence_classification`
- `statement_classifications`

Added by this contract: `recommended_next_evidence`, `confidence_classification`, `statement_classifications`.

## The mission's field names against this repository's vocabulary

| asked for | carried by |
|---|---|
| `subject_key` | subject |
| `hypothesis` | hypothesis_statement |
| `observed_facts` | observed_need + evidence_bound_reasoning_summary |
| `proposed_intervention_hypothesis` | candidate_intervention_class |
| `unsupported_or_unknown_assumptions` | unsupported_dimensions + commercial_claims_not_supported |
| `evidence_boundaries` | supporting_evidence_ids + supporting_claim_ids + independence_status + reliability_status |
| `commercial_unknowns` | commercial_claims_not_supported |
| `problem_unknowns` | critical_uncertainties |
| `validation_questions` | critical_uncertainties |
| `recommended_next_evidence` | recommended_next_evidence (added by this contract) |
| `confidence_classification` | confidence_classification (added by this contract) |

## Confidence

Classifications: `EXPLORATORY`.

a self-reported certainty is not a probability, so the field is a closed enum of one rather than a number. No score is requested, computed or persisted anywhere.

## Validation order

1. transport success
2. provider response shape
3. exact structured-output parse
4. schema validation
5. semantic output gate
6. evidence-boundary gate
7. attribution and no-distortion gate
8. canonical persistence eligibility

a failure at any stage persists no Opportunity. The output is never repaired by a second model call, and a refusal is recorded rather than retried.

## Two stale checks, generalised rather than weakened

the gate required the output to preserve NON_SCORABLE / MISSING_RELIABILITY. Every row in the corpus was non-scorable when Mission 1.31 wrote it; Mission 1.77 resolved reliability from lineage, so 12 of 14 docker rows and 6 of 6 TED rows are scoring-eligible. It now reads the packet and demands the truthful statement either way, plus a refusal of any claim that a score exists.

a module constant listing container-ecosystem words: the right check and the wrong list for any other subject. It is a parameter now, defaulting to the frozen list, so every existing caller behaves identically and this packet supplies its own.

Base gate opportunity-synthesis-persistence-gate@1.0.0 to **opportunity-synthesis-persistence-gate@1.1.0**. Weakened: False.

## Forbidden transformations

| name | the packet establishes | it is NOT |
|---|---|---|
| `REALISED_SPEND` | a stated TOTAL_VALUE at notice scope, including options and renewals | money anybody paid |
| `MARKET_DEMAND` | that authorities published notices under one CPV class | market demand, appetite or adoption |
| `SOFTWARE_BUYER` | that a contracting authority published a notice | a buyer, customer or prospect for a software product |
| `WILLINGNESS_TO_PAY` | an economic value stated in a published notice | willingness to pay or a budget for software |
| `PRODUCT_MARKET_FIT` | that activity exists in a bounded set of notices | product-market fit, a validated market or a proven need |

## Independence

independence is UNKNOWN for all six rows and there are 0 independence groups, so an output describing several independent sources is refused.

## Human review

**HUMAN_OUTPUT_REVIEW_REQUIRED = True**, by the named local operator, after the response passes every deterministic gate and before canonical persistence.

the subject is SEMANTICALLY_COHERENT_BUT_PRODUCT_LINK_UNKNOWN and its overinterpretation risk is recorded HIGH. The gate refuses what it can name; a hypothesis that distorts the evidence without using a named phrase is exactly what it cannot name, and this is the repository's first synthesis over a procurement record. Mission 1.31 also shows the cost of the opposite mistake: a gate accepted on lexical grounds is a gate that has not read the answer.

Lexical filtering is not semantic safety: True.
