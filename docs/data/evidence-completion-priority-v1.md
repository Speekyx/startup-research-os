# The priority decision

Generated from `evidence-completion-priority-v1.json`. Do not edit by hand.

**Outcome: `NEXT_BOUNDED_EVIDENCE_MOVE_SELECTED` — M1.**

No numeric score was issued. a priority number here would be a weighted sum of judgements nobody calibrated, and it would look exactly like a measurement. The tiers say what they mean and the lexicographic order says which criterion decided.

## Tiers

| tier | candidates |
|---|---|
| TIER_1_EXECUTABLE_DECISION_CHANGING | `M1` |
| TIER_2_EXECUTABLE_MAJOR_BREADTH | — |
| TIER_3_BOUNDED_UNBLOCKING_THEN_HIGH_VALUE | `M3`, `M6` |
| TIER_4_USEFUL_BUT_INCREMENTAL | `M2`, `M4`, `M5` |
| TIER_5_NOT_CURRENTLY_ACTIONABLE | — |

**Tier 2 is empty.** no candidate both adds a currently absent decision-relevant dimension AND is executable now. M6 would add one and is not executable; every executable candidate completes scorability rather than adding a dimension. That emptiness is the finding, not a gap in the analysis: the registered portfolio cannot currently reach the dimensions this hypothesis is missing.

## Lexicographic criteria, fixed before the candidates were read

1. expected information gain
2. adds a missing dimension before more of the same
3. governance readiness
4. held data or an existing collector before new implementation
5. independence potential
6. direct product or commercial relevance
7. smallest bounded engineering or review surface

## Dominance

| pair | dominates | why |
|---|---|---|
| M1 over M2 | True | no worse on every load-bearing criterion and strictly better on information gain (DECISION_CHANGING against LOW_INCREMENTAL_GAIN) and on subject relationship (DIRECT against NOT_THE_SAME_SUBJECT) |
| M1 over M4 | True | strictly better on gain, subject relationship and independence potential |
| M1 over M5 | True | strictly better on gain and independence potential, equal on the rest |
| M1 over M3 | False | M3 is strictly better on independence potential and requires no code. M1 is strictly better on gain and needs no external action. Neither dominates, and the TIER separates them rather than a tie-break. |
| M1 over M6 | False | M6 is strictly better on adding a missing DIMENSION, which M1 does not do at all. M1 is strictly better on gain, governance readiness, collector readiness and engineering surface. Neither dominates. |
| anything over M1 | False | no candidate is no-worse than M1 on every load-bearing criterion. M3 and M6 each beat it on one criterion and lose on several. |

## Selection

**Uniquely dominant: False.** dominance is not the selection rule; it is the veto. §14 forbids selecting a DOMINATED candidate, and M1 is dominated by nothing. Selection is then by tier, and M1 is the only member of TIER 1 -- the only candidate that is both executable now and targets a currently named sufficiency blocker.

the Docker hypothesis was compared on its measured breadth against every other subject holding Evidence. Having an Opportunity row is not a priority criterion, and M2 and M4 -- both attached to no Opportunity -- were ranked on their own terms and lost on information gain.

## Next: Mission 1.77 — Wikimedia Measurement Scope Binding V1

- **target subject:** the Wikimedia pageview Evidence lineage, including the six rows on the only Opportunity
- **target property:** `SCORABILITY`
- **target source:** wikimedia-pageviews, already held
- **external action required:** False
- **canonical mutation expected:** writing reliability onto held Evidence rows, which IS a canonical mutation and is why it belongs to the next mission rather than to this one

a reviewed reliability for exactly this measurement and purpose already exists and does not apply, because the Evidence cannot state its resource identity. The corpus is one deterministic binding away from its first scorable evidence.

**What it can establish.**

- that a reviewed reliability applies to the held Wikimedia Evidence
- that aggregation over the Opportunity's Wikimedia rows is reachable
- that the Opportunity's first stated epistemic limitation is no longer true as written

**What it cannot establish.**

- independence: independence_state stays UNKNOWN and no group may be created
- any new evidence dimension; the hypothesis stays at two supported dimensions
- willingness to pay, buyer existence, or any commercial dimension
- that the packet is wholly scorable, because its Stack Exchange row has no assessment
- a score: aggregation becoming reachable is not aggregation being run

## Globalping, as a dependency

State `COUNTERPART_UNRESOLVED`, C9 `PARTIAL`. Selectable now: **False**. no route is qualified while C9 is PARTIAL.

What a future qualification could unlock: an independently produced HTTP measurement, which is the only route currently visible to genuine evidence independence rather than source diversity.

Checked externally by this mission: **False**.
