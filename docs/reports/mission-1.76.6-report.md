# Mission 1.76.6 — Q1 selected, and no construct with it

**Outcome: `Q1_SELECTED_CONSTRUCT_CONTRACT_REQUIRES_DECISION`.**

The brief was issued as Mission 1.76.5. That number was already spent by the R2-B closure
merged in [#133](https://github.com/Speekyx/startup-research-os/pull/133), and its report
path exists, so this is **1.76.6** and the successor the brief proposes becomes 1.76.7.

---

## Report

```
START_COMMIT                 = 082beda
GLOBALPING_PASS_PARTIAL_FAIL = 12 / 0 / 0   (recounted from the gates, not read from the tally)
COUNTERPART_STATUS           = COUNTERPART_RESOLVED
MIGRATION_HEAD               = 0036_grant_use_profile_vocabulary
Q1_BEFORE                    = PROMISING_REQUIRES_ROUTE_QUALIFICATION, not selectable
Q1_AFTER                     = STRATEGICALLY_VIABLE on a different route pair
QUANTITY_CLASS_SELECTED      = Q1 — Fixed-corpus HTTP / HTML observation
CONSTRUCT_CANDIDATES         = A (HEAD_3XX), B (HEAD_RESPONSE_RECEIVED), C (HEAD_NON_ERROR)
TARGET_LEVEL_MODEL           = PREFERRED
CORPUS_LEVEL_MODEL           = REJECTED (count/rate and existential, for different reasons)
VANTAGE_SEMANTICS            = UNRESOLVED — three coherent resolutions, none chosen
CANDIDATE_A                  = BLOCKED_ON_VANTAGE
CANDIDATE_B                  = REJECTED
CANDIDATE_C                  = REJECTED_ON_SEMANTICS_BEFORE_VANTAGE
SELECTED_CONSTRUCT           = NONE
PREDICATE                    = not frozen
E_RULE / P_RULE              = not frozen
DENOMINATOR_RULE             = N is the frozen manifest; 0 targets removable for any outcome
REQUEST_COMPARABILITY        = 10 MUST_MATCH, 2 MAY_DIFFER, 1 PROVENANCE, 2 UNRESOLVED
INFERRED_CLAIM_COMPATIBILITY = COMPATIBLE (identity, refusals, grouping)
EVALUATOR_CHANGE_REQUIRED    = YES — CATEGORICAL_MEMBERSHIP_EVALUATOR, secondary
INDEPENDENCE_CAPABILITY      = INDEPENDENCE_ARCHITECTURALLY_CAPABLE, 0 groups
CORPUS_FROZEN                = NO
MEASUREMENTS_EXECUTED        = 0
CANONICAL_MUTATION           = 0 across every counter
PRIMARY_OUTCOME              = Q1_SELECTED_CONSTRUCT_CONTRACT_REQUIRES_DECISION
NEXT_MISSION                 = an operator decision on vantage semantics, then 1.76.7
```

Canonical baseline measured before work and unchanged after: RawRecords 325, Normalized 325,
Signals 33, Claims 44, Revisions 45, Evidence 58, Reliability 4, IndependenceGroups 0,
thresholds 1, derivations 1, refusals 0, Opportunities 1.

## The premise that changed, in the record's own words

`quantity-class-selection-decision-v5.json` did not merely decline to select. It wrote down
**why**, and named the exact blocker:

> the qualification verdict is what gates a selection, and it did not move. C9 is PARTIAL on
> R2, so the tally improved and nothing downstream became available.

C9 is PASS. So the selection v5 refused is made — and the gate asserts the premise **live**,
recounting the twelve dimensions rather than reading the tally, so a selection cannot outlive
a qualification that was quietly reopened.

## The 1.76 priority: narrowed, not overturned

Mission 1.76 recorded the Globalping route as a **dependency, never a candidate**, with
`selectable_now: false` and the reason `no route is qualified while C9 is PARTIAL` — and it
predicted the value: *"the only route currently visible to genuine evidence independence
rather than source diversity."*

| criterion | M1 Wikimedia | HTTP construct | favours |
|---|---|---|---|
| SCORABILITY_REPAIR | binds the reviewed 0.65 | none | **M1** |
| NEW_EVIDENCE_DIMENSION | none — same kind, same publisher | a transport-level observation | HTTP |
| ESTABLISHED_INDEPENDENCE_POTENTIAL | none — one publisher | the only visible route | HTTP |
| CONTRADICTION_POTENTIAL | none — one witness | yes, under a target-level shape | HTTP |
| EXECUTION_READINESS | executable now over held data | no construct, no corpus, no fetcher | **M1** |

**Neither dominates, and they are not competing for the same slot.** M1's TIER 1 placement
rested on being the only candidate *both executable now and aimed at a named blocker*, and
that is untouched: the HTTP route is still not executable. What changed is that it is no
longer **unselectable** — so it re-enters as a parallel contract track. Reporting
`MISSION_1_77_REMAINS_HIGHER_PRIORITY` as the primary outcome would say the class question
went unanswered, and it did not.

## Why the class passes and the construct does not

The class question is whether two apparatuses can independently produce this world-state unit
over a corpus we freeze. They can, and the Q1 package is re-graded on a **different route
pair** — v1 graded Common Crawl and HTTP Archive, which Mission 1.70 closed. v1 is not
re-graded in place; it keeps its verdict on its own routes and gains one forward pointer.

The construct question is whether one exact predicate means the same thing measured from two
vantages. It does not follow from the first, and it did not close.

## Vantage is proposition underspecification, not measurement noise

This is the finding, and it stops all three candidates.

Both apparatuses **state** their vantage — which is already better than Mission 1.70, where
`GEOGRAPHY_VANTAGE` was `DIFFERENT_AND_LOAD_BEARING` because one side stated it and the other
did not. Stating it removes the ignorance. It does not remove the difference.

For a target behind a CDN or GeoDNS, the response genuinely differs by client geography, ASN
and resolver. So *"target T returns a 3xx status"* has **no truth value until a vantage is
named**: the two apparatuses are not noisy witnesses of one fact, they are accurate witnesses
of two. That is different in kind from timing jitter, which an observation window absorbs.

**Mission 1.58's test applied:** *if the two apparatuses disagree, is that a fact about the
world or a bug?* Here it is a fact about the world — about a **different** world-state than
the proposition names. Corroboration is supposed to tolerate noise, not to absorb an
undefined subject.

And it cannot be handled by corpus selection, because which targets vary by vantage is not
knowable before measuring, and selecting on it afterwards is outcome selection.

Three coherent resolutions, each with a real and different cost:

| | effect | cost |
|---|---|---|
| **V1** vantage in proposition identity | two propositions, two Claims | no shared Claim, so no independence and no contradiction |
| **V2** universal over a defined vantage class | a disagreement *refutes* rather than manufacturing a contradiction | the SUPPORTS direction is nearly vacuous, and the class must be defined independently of who observes |
| **V3** explicit tolerance | the proposition names no vantage | must say why divergence is noise, and nothing establishes that for CDN-fronted targets |

**None was chosen.** V2 is preferred on current evidence and is recorded as a preference, not
a decision — because each choice decides what the eventual Evidence *means*, and picking the
one that makes a construct appear is choosing a semantics for its convenience.

**V2 carries a trap that had to be named**: a universal over *"every vantage observed"* makes
the proposition's content depend on which apparatuses happened to look. That is
`FRAME_INSIDE_THE_DEFINITION` — Mission 1.47's relocation of source attribution into the
predicate, which Mission 1.57 added to the registry as a trap. V2 survives only with a vantage
class defined independently of its observers.

## Target-level, not a corpus aggregate

Decided first, because it decides what the denominator question even is.

**Target-level has no denominator to select.** One preregistered proposition per frozen
target; the corpus is a bounded set of independently attempted target propositions; every
target keeps a terminal record whether it was evaluable or not, and an unevaluable one
produces a refusal row rather than a silent absence — a shape the repository already has in
migration 0035 and ADR-038.

**Corpus count or rate fails the way Mission 1.70 failed.** Each apparatus can only count over
the targets *it* could evaluate, and the two evaluable sets differ. Restricting to the
intersection is co-coverage selection, which 1.70 refused outright; not restricting means two
counts over two populations. Evaluability is also not independent of the predicate — a host
that is down cannot be observed returning 3xx — so conditioning on it is not harmless.

**Corpus existential fails differently**: it is monotone, so it can never be contradicted.
Mission 1.48 established that the propositions easiest to converge across apparatuses are
exactly the ones that cannot produce the contradiction case.

**And target-level is what unlocks the thing this whole arc has been for**: two witnesses on
one source-independent proposition, so one may SUPPORT while the other CONTRADICTS. Mission
1.48 found that structurally unreachable; Mission 1.56 said it needs a second witness
disagreeing about one proposition.

## The three candidates

**A — HEAD_3XX.** Transport-level on both, redirect-following pinnable, and class membership
defined by RFC 9110 rather than by us. `BLOCKED_ON_VANTAGE`, and worse than the others on it:
geo-routing is *commonly implemented as a 3xx*, so this candidate is concentrated on exactly
the failure. **Not preferred merely because R1 work already exists**, and the record says so.

**B — HEAD_RESPONSE_RECEIVED.** Rejected. It needs a target's non-response, a network-path
outcome and an apparatus failure separated *equivalently on both sides*. Each apparatus
separates its own failure well — the fetcher by `APPARATUS_FAILURE_NOT_A_WORLD_FACT`, the
provider by `offline`, which the provider itself defines as a probe that was not available.
Neither separates a network-path outcome from a target outcome, and the two take different
paths, so the unseparated residue differs between them and lands inside the predicate.

**C — HEAD_NON_ERROR_STATUS.** Rejected **before vantage**, on semantics. `status < 400`
treats a nominal code as a magnitude: 301 is not less than 404 in any sense the predicate
uses, and the ordering is an artifact of the numbering. A threshold evaluator would accept the
integer and produce a verdict — which is precisely the smuggling, because **the evaluator
accepting integers is not evidence that the quantity is one.**

## The field that would have broken it silently

`REDIRECT_FOLLOWING`. R1 established the provider returns the response and does not follow.
The SROS fetcher's own load profile records that **redirects count toward the origin budget**,
so following is available to it. A 3xx predicate compared across that difference would compare
a redirect response on one side against whatever the redirect led to on the other — and
nothing in either apparatus's defaults prevents it. The construct contract must pin it
`DISABLED` on both.

Ten fields are `MUST_MATCH`, and the gate refuses any of them demoted — a different path or a
different query is a different proposition whatever else matches. Two may differ **because
independence requires it**: timeout, and the DNS resolution path, whose divergence the
provider makes observable by reporting `resolvedAddress`. User agent is witness provenance
only; requiring one string would require one apparatus to impersonate the other.

## A categorical evaluator is required, and it is the second blocker

The existing evaluator is `THRESHOLD_STATE`: a measurement against a registered bound. Class
membership is not that, and the two-sided range defining the 3xx class is the class
*definition* rather than a threshold anybody registered.

The gap is **small and additive** — the same four-gate shape with a registered class
definition where the threshold evaluator has a bound, needing no change to Claim identity,
Evidence, the refusal store or the aggregator. It is reported as a finding and not routed
around.

It is **not** the primary blocker, which is why the outcome is not
`Q1_SELECTED_CATEGORICAL_EVALUATOR_REQUIRED`: that outcome is for when the evaluator gap is
the *only* blocker, and the contract decision determines whether the predicate is categorical
at all.

## Verification

- Probe: **149 deliberate violations, 149 caught, 0 escaped**, plus **4 of 4 positive
  controls**, ten files restored byte for byte.
- **Two escapes found and closed**: a differing PATH and a differing QUERY were not refused,
  because the gate pinned only method and redirect policy. Both are named in the brief's own
  probe list, and both now fail against the full ten-field `MUST_MATCH` set.
- **Two controls are INVERTED.** A later mission must still be able to select a construct, and
  the no-construct state must remain expressible — a gate that could only express one of those
  would decide the next mission by refusing the other.
- **Seven gates and seven test assertions were re-pointed rather than deleted.** Each pinned a
  filesystem absence to its own mission's historical verdict: *my decision record selected
  nothing, therefore the repository's selection artifact must not exist.* The first half is a
  fact that stays true; the second is a claim that no later mission may ever select. Each now
  keeps its own assertion and checks that whatever selection exists is well formed and
  authorises no run — which is strictly more than the absence check did.
- **3431 bare-python tests**; both runners green; `ruff format --check`, `ruff check`, mypy
  over 197 files; contract and catalog `--check`; all **54** CI gates, one of them new.

## What did not happen

No construct, no corpus, no predicate, no threshold, no measurement. Zero Globalping API
calls, zero target HEAD requests, zero SROS fetcher runs, zero robots requests, zero Common
Crawl or HTTP Archive queries, zero provider contacts, zero mailbox reads. Zero RawRecords,
Signals, Claims, Evidence, independence groups, threshold registrations, derivations,
refusals, scores, embeddings or migrations.

`INDEPENDENCE_ARCHITECTURALLY_CAPABLE`, **0 groups** — a qualified pair is not a persisted
independence judgement, which is what Mission 1.73's qualification says about itself.

Product relevance is bounded at **MODERATE** and the promotion `HTTP status → demand → market
size → WTP` is refused by name.

## Next

**One operator decision: the vantage semantics of the construct contract — V1, V2 or V3.**
V2 is preferred on current evidence, with its cost stated in advance rather than discovered
later.

If V2 is chosen, **Mission 1.76.7 — Frozen HTTP Corpus & Dual-Apparatus Request Contract V1**
may freeze the corpus rule, the target set, the request contract, the window and the run
configuration, and **must still execute zero measurements** until separate operator approval.
The categorical evaluator is a small mission of its own and comes before any evaluation, not
before the contract.

If none is chosen, the executable move remains M1 — Wikimedia measurement scope binding — and
it was never displaced.

**Mission 1.77 was not started.**
