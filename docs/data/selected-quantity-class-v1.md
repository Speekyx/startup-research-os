# Q1 selected, and no construct with it

Generated from `selected-quantity-class-v1.json`, `quantity-class-selection-decision-v6.json` and `http-construct-candidate-evaluation-v1.json`. Do not edit by hand.

**Q1_SELECTED_CONSTRUCT_CONTRACT_REQUIRES_DECISION**

| state | |
|---|---|
| CLASS_SELECTED | **True** |
| CONSTRUCT_SELECTED | **False** |
| RUN_AUTHORIZED | **False** |

The distinction the artifact exists to carry.

## The class

`Q1` — Fixed-corpus HTTP / HTML observation, on two routes:

- SROS bounded HTTP fetcher
- Globalping HTTP measurement

the class question is whether two apparatuses can independently produce this world-state unit over a corpus we freeze. They can. The construct question is whether one exact predicate means the same thing measured from two vantages, and it does not follow from the first.

## The three candidates

| candidate | verdict |
|---|---|
| HEAD_3XX_RESPONSE_OVER_FROZEN_CORPUS | `BLOCKED_ON_VANTAGE` |
| HEAD_RESPONSE_RECEIVED | `REJECTED` |
| HEAD_NON_ERROR_STATUS | `REJECTED_ON_SEMANTICS_BEFORE_VANTAGE` |

## Vantage is what stops all three

**VANTAGE_IS_PROPOSITION_UNDERSPECIFICATION_NOT_MEASUREMENT_NOISE**

for a target behind a CDN or GeoDNS, the response genuinely differs by client geography, ASN and resolver. So 'target T returns a 3xx status' has no truth value until a vantage is named: the two apparatuses are not noisy witnesses of one fact, they are accurate witnesses of two. That is different from timing jitter, which a window absorbs, and it cannot be handled by corpus selection because which targets vary by vantage is not knowable before measuring -- and selecting on it after measuring is outcome selection.

'if the two apparatuses disagree, is that a fact about the world or a bug?' For geo-varying targets it is a fact about the world -- about a DIFFERENT world-state than the proposition names. Corroboration is supposed to tolerate noise, not to absorb an undefined subject.

| resolution | cost |
|---|---|
| `V1_VANTAGE_IN_PROPOSITION_IDENTITY` | no shared Claim, so no independence and no contradiction. Defeats the purpose. |
| `V2_UNIVERSAL_OVER_A_DEFINED_VANTAGE_CLASS` | the SUPPORTS direction is nearly vacuous, since two samples cannot establish a universal over a class -- only refute it. V must also be defined independently of who observes, or the predicate enumerates its own witnesses. |
| `V3_EXPLICIT_TOLERANCE` | it must say why divergence is noise rather than underspecification, and no retrieved document supports that for CDN-fronted targets. Adopting it would record an artefact as a finding. |

each has a real and different cost, and choosing among them decides what the eventual Evidence MEANS. Picking the one that makes a construct appear would be selecting a semantics for its convenience, which is the shape §20 puts vantage second to prevent.

## What did not happen

| | |
|---|---|
| construct selected | None |
| corpus frozen | False |
| measurements executed | 0 |
| independence groups | 0 |
| independence state | `INDEPENDENCE_ARCHITECTURALLY_CAPABLE` |

**Next: OPERATOR_DECISION_ON_THE_VANTAGE_SEMANTICS_OF_THE_CONSTRUCT_CONTRACT.** V1, V2 or V3 in http-construct-candidate-evaluation-v1.json
