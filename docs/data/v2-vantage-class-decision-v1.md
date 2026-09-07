# V2 — sound for refutation, out of reach for support

Generated from `v2-vantage-class-decision-v1.json`. Do not edit by hand.

**V2_VALID_FOR_REFUTATION_BUT_NOT_INDEPENDENT_SUPPORT**

The operator selected V2 after Mission 1.76.6 chose nothing. That record still reads `which_was_chosen: null`, which was true at its completion.

## FOR ALL v IN V

`FOR ALL v IN V: predicate(target, request, v)`, where V must be finite, preregistrable, and decidable before any measurement.

## The dilemma

a vantage class member is either ABSTRACT or CONCRETE, and neither works. Abstract members are apparatus-independent and are SAMPLED rather than decided by one observation, so the universal cannot be supported. Concrete members are decided by one observation, and the only concrete vantages either apparatus occupies are the ones the apparatus defines -- which is the frame guard.

**Is this a topology problem? False.** it survives any number of operator probes. Adding vantages to SROS would let it sweep more members, and each sweep would still SAMPLE an abstract member rather than decide it. The limit is the logical form of a universal over classes, not the size of the fleet.

## Three classes, and the hole between them

| class | apparatus-independent | support | verdict |
|---|---|---|---|
| `VC_A_EXTERNAL_GEOGRAPHIC_TUPLE_SET` | True | `U1_UNATTAINABLE` | `VALID_FOR_REFUTATION_ONLY` |
| `VC_B_SINGLETON_OPERATOR_VANTAGE` | False | `DEGENERATE` | `REFUSED_TWICE_OVER` |
| `VC_C_EXTERNALLY_ENUMERATED_CONCRETE_VANTAGES` | True | `UNOBSERVABLE_BY_THIS_PAIR` | `DEFINABLE_BUT_UNOBSERVABLE` |

## What each apparatus actually is

| | capability | full class coverage |
|---|---|---|
| SROS fetcher | `SINGLE_DEPLOYMENT_VANTAGE` | no |
| Globalping | `MULTIPLE_SELECTABLE_VANTAGES` | attemptable, not guaranteed |

one apparatus can be pointed at many vantages and the other occupies one. That is a fact about the pair as it stands, recorded rather than designed around.

## Support and refutation

| | |
|---|---|
| SROS can independently support | False |
| Globalping can independently support | False |
| dual independent support reachable | False |
| contradiction reachable | False |

the SUPPORTS-versus-CONTRADICTS case needs one apparatus to legitimately SUPPORT while the other CONTRADICTS. No admissible SUPPORTS item exists, so the pair can produce agreement-on-refutation or incompleteness, and not disagreement.

**What V2 does deliver:**

- a semantically truthful universal proposition
- sound refutation from a single in-scope counterexample
- honest missingness, kept apart from predicate-false
- a target-level shape with no denominator to select

**What it does not: the independent-support calibration goal this arc has pursued since Mission 1.78. Globalping being qualified does not solve it under V2.**

**Next: OPERATOR_COMPARISON_OF_THE_APPARATUS_ARC_AGAINST_MISSION_1_77.** Globalping does not currently solve the independent-support calibration goal under V2. It is qualified, the semantics are sound, and the support half is out of reach.
