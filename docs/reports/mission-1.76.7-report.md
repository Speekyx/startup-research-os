# Mission 1.76.7 — V2 is sound for refutation, and the support half is out of reach

**Outcome: `V2_VALID_FOR_REFUTATION_BUT_NOT_INDEPENDENT_SUPPORT`.**

The operator selected the semantic model. It can be made truthful, and it does not deliver
the thing this arc has been pursuing.

---

## Report

```
START_COMMIT                     = de5816a
OPERATOR_VANTAGE_DECISION        = V2
Q1_SELECTED                      = yes (CLASS_SELECTED)
CONSTRUCT_SELECTED               = no
VANTAGE_CLASSES_EVALUATED        = 3  (VC-A external tuples, VC-B singleton, VC-C external concrete)
SELECTED_VANTAGE_CLASS           = NONE
CLASS_CARDINALITY                = not fixed; no class selected
MEMBERSHIP_RULE                  = not frozen
FRAME_INDEPENDENT                = achievable (VC-A and VC-C), at a cost
SROS_VANTAGE_CAPABILITY          = SINGLE_DEPLOYMENT_VANTAGE
GLOBALPING_VANTAGE_CAPABILITY    = MULTIPLE_SELECTABLE_VANTAGES
SROS_FULL_CLASS_COVERAGE         = NO
GLOBALPING_FULL_CLASS_COVERAGE   = ATTEMPTABLE_NOT_GUARANTEED, and sampling not deciding
SUPPORT_MODEL                    = U1_COMPLETE_CLASS_WITNESS (selected, unattainable here)
REFUTATION_MODEL                 = one in-scope predicate-false observation; SOUND
PARTIAL_POSITIVE_HANDLING        = REFUSED (U3)
DUAL_INDEPENDENT_SUPPORT_REACHABLE = NO
CONTRADICTION_REACHABLE          = NO
EVIDENCE_MODEL_CHANGE_REQUIRED   = no new EvidenceDirection member; one refusal reason code
CORPUS_FROZEN                    = no
MEASUREMENTS                     = 0
CANONICAL_MUTATION               = 0 across every counter
PRIMARY_OUTCOME                  = V2_VALID_FOR_REFUTATION_BUT_NOT_INDEPENDENT_SUPPORT
NEXT_MISSION                     = an operator comparison against Mission 1.77
```

Preconditions verified: tree clean, `main` == `origin/main` at `de5816a`, migration head
`0036`, Q1 `CLASS_SELECTED` with construct and run false, no construct artifact, no corpus, no
run, Globalping 12/0/0 recounted from the gates, canonical baseline unchanged at
325/325/33/44/45/58/4/0/1/1/0/1.

## The decision is a transition, not a correction

Mission 1.76.6 offered three resolutions and chose none. That record still reads
`which_was_chosen: null`, and the gate refuses a version that backdates it. **A later operator
decision is a new fact, not a repair of an earlier honest record.**

## The dilemma: a class member is abstract or concrete, and neither works

This is the finding.

**If members are abstract** — a country, an ASN, a (country, ASN) tuple — the class is
apparatus-independent and finite and decidable before the run. But a member is a *set* of
concrete hosts with different resolvers and paths, so **one probe inside a member is a sample
of that member, not a decision of it.** No finite observation establishes *"for all v in V"*;
it establishes *"for the concrete hosts we happened to use."*

**If members are concrete** — this probe, that host — the universal becomes decidable by
observation. But the only concrete vantages either apparatus occupies are the ones the
*apparatus* defines, which is §4's frame guard: a frame chosen from apparatus identity or
availability.

**And this is not a topology problem.** Adding vantages to the SROS fetcher would let it sweep
more members, and each sweep would still sample an abstract member rather than decide it. The
limit is the logical form of a universal over classes, not the size of the fleet.

That is why **`V2_REQUIRES_MULTI_VANTAGE_OPERATOR_APPARATUS` is refused as the primary
outcome**: reporting it would send the next mission to build an apparatus that does not fix
the problem.

## Three classes, mapping the space

| class | apparatus-independent | support | verdict |
|---|---|---|---|
| **VC-A** finite (country, ASN) tuples from external registries | yes | unattainable — members are sampled | `VALID_FOR_REFUTATION_ONLY` |
| **VC-B** the SROS deployment vantage | **no** | degenerate | `REFUSED_TWICE_OVER` |
| **VC-C** concrete locations named by an external registry | yes | unobservable — neither apparatus is there | `DEFINABLE_BUT_UNOBSERVABLE` |

**VC-B is refused twice over**, and the second reason is the one worth keeping: it defines the
class by apparatus identity, *and* **a universal over a singleton is just the proposition with
a vantage qualifier attached — which is V1, the model the operator explicitly rejected.** Any
class of cardinality one collapses V2 into V1.

So `V2_FRAME_CANNOT_BE_DEFINED_WITHOUT_APPARATUS_DEPENDENCE` is also refused, because it is
false: VC-A and VC-C are both defined without naming either apparatus. **The frame can be
defined independently. What an independent frame costs is the ability to support the
universal.**

## Support semantics: the truthful model is the unattainable one

**U1 — complete-class witness** is selected. An Evidence item supports the universal only if
its apparatus independently observed every required member and every member satisfied the
predicate.

It is **unattainable here**, and the record says so. Selecting the truthful model and
recording that it cannot be met is the honest pair; selecting an attainable but false model
would not be.

**U3 — partial positive support is refused.** *"Some evidence in favour of all"* is not
evidence for a universal, and this repository has no logical semantics that would justify it.
Worse here: for an abstract-member class a positive observation does not even establish its
own member, so the partial support would be partial support for something never observed.

**U2 — member evidence plus a derivation is sound and does not solve the goal.** If the two
apparatuses each cover part of V, the universal is established by **one derivation over a
pooled observation set**. That is not two independent witnesses of one proposition; it is one
conclusion drawn from both. **Pooling is the opposite of the duplication independence
requires**, and counting it as corroboration would manufacture agreement out of division of
labour.

## Refutation is sound, and two refutations agree

One genuine predicate-false observation, from a concrete vantage inside a member of V, under
the frozen request contract, refutes the universal. Both apparatuses can produce one.

Five states are kept apart from it and none may refute: `NOT_OBSERVED`, `APPARATUS_FAILURE`,
`VANTAGE_UNAVAILABLE`, `REQUEST_FAILED_BEFORE_WORLD_STATE_OBSERVED`, `PREDICATE_NOT_EVALUABLE`.
**Turning missingness into contradiction is the failure this arc has refused since Mission
1.71** — a probe that was not available says nothing about the target.

But **two refutations agree.** They exercise no disagreement, so refutation alone does not
reach the SUPPORTS-versus-CONTRADICTS case.

## What the apparatuses actually are

| | capability | basis |
|---|---|---|
| SROS fetcher | `SINGLE_DEPLOYMENT_VANTAGE` | its own contract: *"two processes on one machine share code, configuration, vantage, resolver and network path"*, and *"a bounded pilot on one operator machine"* |
| Globalping | `MULTIPLE_SELECTABLE_VANTAGES` | qualification gate C7: selectable by continent, region, country, state, city, ASN, network and tags, each result carrying its probe's location |

**The fetcher was not redesigned into a probe network**, and no probe availability was checked
— that would be an external call *and* would make the class depend on availability.

## The shortfall, stated plainly

```
SROS_CAN_INDEPENDENTLY_SUPPORT_V2       = NO
GLOBALPING_CAN_INDEPENDENTLY_SUPPORT_V2 = NO
DUAL_INDEPENDENT_SUPPORT_REACHABLE      = NO
CONTRADICTION_REACHABLE                 = NO
```

Globalping cannot either — it can attempt every member of an abstract class, and each
observation is still a sample of its member.

And **the contradiction case is not reachable under V2**, which is worth saying because it is
the thing the arc was chasing: SUPPORTS-versus-CONTRADICTS needs one apparatus to legitimately
*support* while the other contradicts. No admissible SUPPORTS item exists, so the pair can
produce agreement-on-refutation or incompleteness, and not disagreement.

**Globalping being qualified does not solve the independent-support calibration goal under
V2.** That is the finding, and §11 forbids hiding it.

## What V2 does deliver

A semantically truthful universal proposition; sound refutation from a single in-scope
counterexample; honest missingness kept apart from predicate-false; and a target-level shape
with no denominator to select — Mission 1.76.6's finding, preserved and not reopened to make
V2 easier.

## The evidence model needs almost nothing

`CONTRADICTS` is usable for a genuine in-scope predicate-false observation. `SUPPORTS` is
usable only for a complete-class witness, which does not exist here.

The missing state is an apparatus that swept some members and found the predicate true at all
of them: it has neither supported the universal nor contradicted it. Forcing that into
SUPPORTS is U3; into CONTRADICTS is false; and NEUTRAL asserts that the observation bears
without bearing either way, which is a positive finding this is not.

**The smallest extension is a refusal reason code for an incomplete class sweep** — migration
0035 already holds refusals with a reason code and a candidate target, so **no new table and
no new `EvidenceDirection` member is required.**

## Verification

- Probe: **129 deliberate violations, 129 caught, 0 escaped**, plus **4 of 4 positive
  controls**, five files restored byte for byte.
- **One escape found and closed**: a class defined as *"the vantages both apparatuses
  successfully measured"* slipped past a `\bsuccessful\b` word-boundary pattern that
  *"successfully"* does not match. Widened to the stem.
- **Two controls are INVERTED and they are the point.** The READY outcome must stay
  expressible for a pair that could reach it, and the incomplete-sweep state must stay
  sayable — a gate that could only express this mission's negative would decide the next
  mission by refusing its positive.
- **3484 bare-python tests**; both runners green; `ruff format --check`, `ruff check`, mypy
  over 197 files; contract and catalog `--check`; all **55** CI gates, one of them new.

## What did not happen

No vantage class selected, no construct, no target named, no corpus frozen, no predicate
frozen. Zero Globalping API calls, zero target HEAD requests, zero SROS fetcher runs, zero
robots requests, zero DNS probes, zero measurement values. Zero RawRecords, Signals, Claims,
Evidence, independence groups, threshold registrations, derivations, refusals, scores,
embeddings or migrations.

## Next

**Mission 1.76.8 is not recommended yet.** Freezing a construct and a corpus would prepare an
experiment whose SUPPORT direction cannot be recorded truthfully.

The operator decision is a comparison: **continue the apparatus arc, or return to M1.**

- What would change the answer is **a construct whose predicate is decided rather than sampled
  by one observation from a member** — a different construct, not a different class. No fleet
  size delivers it for abstract members.
- The executable alternative is unchanged: **M1, the Wikimedia measurement scope binding**,
  which Mission 1.76 placed in TIER 1 and which nothing since has displaced.

**Mission 1.77 was not started.**
