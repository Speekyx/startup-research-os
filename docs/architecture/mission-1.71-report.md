# Mission 1.71 — Bounded HTTP Measurement Governance & Apparatus Design V1

**Outcome: `BOUNDED_HTTP_FETCHER_APPARATUS_CONTRACT_READY_DEDICATED_POLICY_REQUIRED`.**
The apparatus semantics close completely. The governance shape does not, and what is
missing is named rather than vague.

---

## 0. The design's own temptation was the one to watch

Mission 1.70 closed the external pair because neither Common Crawl nor HTTP Archive
documents whether an attempted-and-failed URL appears in what it publishes. The obvious
repair is to run the fetcher ourselves.

The obvious repair has a trap in it that is easy to miss: **an apparatus we control could
reproduce exactly that defect, in a system where nobody else could be blamed for it.** A
fetcher that stored only responses would publish as little about what it tried as Common
Crawl does — the same opacity, self-inflicted.

So the deliverable is not the fetcher. It is the accounting invariant:

```
corpus_manifest_count == terminal_target_records_count
```

Exactly one terminal record per manifest item per governed run. **17 terminal outcomes
over 8 missingness classes, a total mapping, and no unreachable class.** An item never
attempted stays in the population. A retry is a child attempt, not a new member. An abort
turns every remaining item into `RUN_ABORTED_BEFORE_ATTEMPT` rather than letting it vanish.

## 1. Two corrections the design made to itself

**An apparatus failure is not the target's silence.** §14 lists seven missingness classes
as a minimum. An `INTERNAL_FETCHER_ERROR` filed under `ATTEMPTED_NO_HTTP_RESPONSE` would
record that the target did not answer, when what happened is that we broke. An eighth class
was added — `APPARATUS_FAILURE_NOT_A_WORLD_FACT` — because a denominator built on the
seven would absorb our own defects as the world's silence.

**The apparatus cannot certify predicate evaluability, so it does not claim to.** §13 lists
`PREDICATE_EVALUABLE` as a stage. It is not one a fetcher can reach: whether a received
response is evaluable depends on what the predicate needs, and no predicate exists. The
apparatus tops out at `RESPONSE_RECEIVED` plus what it captured.

| counter | computable by |
|---|---|
| N population, A attempted, R response-observed | the apparatus |
| E predicate-evaluable, P positive | **the construct** |

And which classes enter the denominator is `NOT_CHOSEN_BY_THIS_MISSION`, because choosing
would freeze half a construct while reporting that none was frozen.

## 2. The governance finding is the gate working

The dominant blocker is not any single rubric row, and it was located in the repository's
own rules rather than asserted.

The existing gate governs collection from a **registered source**. Routed through it, a
corpus of arbitrary public sites is refused target by target:

- `source-registry-v1.md` §1 rule 1 — public visibility is not permission
- rule 2 — uncertainty is never permission; silence produces `NOT_ADDRESSED`
- rule 8 — a grant is required for six named activities, and `NOT_ADDRESSED` on any one blocks
- `acquisition-authorization-v1.md` §1 rule 5 — each resource is authorised separately

**Not because a publisher objected, but because nobody asked.** That is the gate working.

**And the collapse it forces is the finding.** Restricting the corpus to targets that *do*
hold a review means restricting it to the 29 registered sources — which destroys exactly
the directability that made the operator route worth designing.

## 3. The mechanism is ordinary; the use is not established

Mission 1.70 asserted that the mechanism is not novel. Here is the concrete evidence:
**Missions 1.59 to 1.70 performed bounded, identified, one-off HTTP GETs against third
parties holding no source review at all**, routinely, under each mission's documentation
budget — Common Crawl's and HTTP Archive's own pages included.

**And the distinction that survives it is stated rather than glossed.** The request is
identical; the destination of the result is not. A documentation read informs a human
judgement recorded in a mission document. A measurement becomes Evidence under a Claim, at
corpus scale. So the precedent establishes that the *act* is ordinary and does not
establish that the *use* is governed.

## 4. What is retained decides which regime applies

This is why data minimization is not a side policy. Retaining response bodies retains the
publisher's content, which is squarely what rule 8 governs. Retaining a status line and
named headers is closer to a record of our own request and its transport outcome.

**That is a distinction, not a legal conclusion**, and the bound is written into the record
beside it: nothing here asserts that a header-only capture escapes any obligation.

## 5. Five named decisions, none settled here

| id | decision |
|---|---|
| GOV-1 | is this a governed activity **distinct from source collection**, and under what track |
| GOV-2 | `ROBOTS_POLICY` |
| GOV-3 | body capture and the retention regime |
| GOV-4 | the target-exclusion procedure |
| GOV-5 | the numeric load bounds |

GOV-1 is dominant and **ADR-level**: it decides whether the other four are settings or
blockers, and a design mission inventing a governance shape in passing is the change-control
shape `docs/CLAUDE.md` refuses.

GOV-2 is **architectural rather than a setting**, which is why it blocks rather than waits:
a robots-respecting apparatus needs a robots retrieval stage, a terminal outcome, a request
budget and a missingness class of its own. The decision changes what the apparatus *is*.

GOV-5's bounds are **mandatory and deliberately unset**. No retrieved document establishes
a figure, and inventing one is the invented number rule 7 refuses, wearing the costume of a
bound.

## 6. The rubric, and the outcomes refused

**13 pass in principle, 3 require a dedicated policy, 0 blocked, 0 unknown.** No numerical
score.

- **A was refused** because three rows genuinely require a decision nobody has taken.
- **D was refused** because target-specific review is downstream of the shape question
  rather than the dominant blocker.
- **F was refused** because the repository's own documents are sufficient to name the gap
  precisely — this is not insufficient documentation.
- **G was refused, and deliberately.** No current rule prohibits the architecture. **The
  absence of a shape is not a prohibition**, and reporting one would convert *nobody has
  decided* into *the project has refused* — the same overstatement this arc declined when
  it refused to call an unproven negative a refutation.

## 7. Self-operation is directability, never independence

`INDEPENDENCE_ARCHITECTURE_PLAUSIBLE`, never `INDEPENDENT_EVIDENCE_GROUP_READY`. **0
independence groups.**

**Two local processes are not two independence groups.** They share code, configuration,
vantage, resolver and network path — one apparatus run twice — and counting them as two
would manufacture corroboration out of repetition, which is exactly what the aggregator's
unknown-provenance collapse exists to prevent.

Nine counterpart requirements are frozen. **0 counterparts evaluated, ranked or selected.**
Common Crawl and HTTP Archive keep Mission 1.70's verdicts verbatim, and **the operator
apparatus does not repair their records retroactively** — designing an apparatus that
publishes attempt semantics says nothing about what somebody else's apparatus published.

## 8. The candidate registry rule was reviewed and not added

Designing **around** a failure mode is not observing a second instance of it. If it counted,
every registry rule could be promoted by writing a contract that respects it, and the
registry would record our intentions rather than what apparatuses actually do.

The rule is genuinely useful and this mission's whole missingness contract rests on it.
**That is not the standard.** Registry unchanged at **15**, and a validator check refuses
any record that counts this mission's own design as an instance.

## 9. Zero external documentation requests, and that is a decision

0 of 12. No gate here turns on a sentence that had to be quoted. The one class of external
fact the design needs — the exact numeric address ranges §6 blocks — is **deferred to the
named IANA registries at implementation rather than transcribed from recall**: a governance
artifact carrying recalled CIDR blocks would breach rule 4 and rule 7 at once, and a stale
or mistyped block is a silent hole in the very guard that exists to prevent one.

## 10. Nothing moved

| | |
|---|---|
| target HTTP requests, crawls, browser runs, curl/wget executions | 0 |
| Common Crawl index queries and downloads, BigQuery, HAR downloads | 0 |
| measurement API executions, target-value exposures | 0 |
| accounts, trials, purchases, credential reads | 0 |
| mailbox searches, enquiries sent | 0 |
| sources registered, governance mutations, governance approvals | 0 |
| corpora created, runs executed, crawlers implemented | 0 |
| thresholds, Claims, Evidence, independence groups, reliability, scores | 0 |
| model calls, embeddings, migrations | 0 |

Baseline measured live before the work: every counter matched §0 exactly, migration head
`0035_refusal_provenance`, drift `none`. ONYPHE stays `NOT_CHECKED_AFTER_DISPATCH`, Netlas
stays pending, the scanner arc stays parked, Q1 stays
`PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED`. **`PAIR_ANALYSIS_NOT_READY`.**

## 11. Verification

- Validator probed with **224 deliberate violations, 224 caught** — 221 by rule, 3 by
  drift — plus **6 of 6 positive controls**.
- **The controls are variants rather than the shipped bytes**, which is the improvement over
  previous missions: a governance-feasible-but-unauthorized apparatus, a blocked outcome
  named on a rule, a corpus with approved query strings, a run manifest carrying an image
  digest, an unresolved independence architecture — and **a terminal taxonomy with every
  outcome renamed and the invariant intact**. That last one is the point: §12 says the
  wording is normalizable and the invariant is what matters, so a validator that refused a
  renamed taxonomy would be checking my prose rather than the property.
- **§58 was honoured after Mission 1.70 shipped a formatting failure to CI.** Both
  `ruff format --check` and `ruff check` were run through `uv`, not `ruff check` alone, and
  the four gates that need the project environment were run with `uv run` rather than bare
  `python` — an environment mismatch is not a product defect.
- **120 new tests**; **2431 bare-python tests**; all pytest suites passed with the database
  unchanged across 29 tenant tables; all **41** CI gates.

## 12. Next

**Mission 1.72 resolves only the named policy decisions, GOV-1 first.** Whether bounded
public-HTTP observation over an unreviewed corpus is a governed activity distinct from
source collection decides whether the other four are settings or blockers, and it is an ADR
with a change-control trail rather than a field somebody adds.

**Do not search counterpart routes until the apparatus itself is governance feasible**, and
do not restart quantity-class discovery.

**Mission 1.72 was not started.**
