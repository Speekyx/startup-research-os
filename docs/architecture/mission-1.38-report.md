# Mission 1.38 — Second Pilot Multi-Evidence Claim Foundation V1

**Outcome: `MULTI_EVIDENCE_CLAIM_ARCHITECTURE_GAP`** (§44 E).

**The one-sentence result:** convergence is one proposition fact away, and that
fact is exactly the one that says **what was measured** — so no source can
produce a multi-Evidence Claim, and the blocker is not source-side.

Nothing was acquired. Every canonical counter is unchanged.

---

## §0 — What the inspection found, before any candidate was considered

Two facts decided the mission, and both were read from the code and the live
catalog rather than from earlier reports.

**The persistence layer already supports N Evidence on one Claim.**
`_persist_one` in `claim_repositories.py` looks a draft up by `proposition_key`
and, when a claim exists, calls `_persist_evidence` against that claim id. The
database, the repository and the aggregation framework are all written for N —
framework §1 asks *"Given several Evidence records bearing on one Claim"*.

**The interpreter can never produce two drafts with the same key.** All seven
templates in `observed_restatement.py` put `source_id` in their proposition
facts, **plus the measurement's own identity**:

| proposition | measurement-identifying facts |
|---|---|
| `source_reported_metric_period_change` | `metric_id`, `geography_source_code` |
| `platform_counted_content_request_change` | `content_id`, `audience_class` |
| `community_site_published_questions_carrying_tag` | `community_site`, `community_tag` |
| `community_site_questions_without_accepted_answer` | `community_site`, `community_tag` |
| `source_reported_term_frequency_change` | `term`, `gram_size` |
| `source_reported_term_frequency_contrast` | `term_a`, `term_b` |
| `source_reported_procurement_value_contrast` | `notice_ids`, `classification_codes` |

Every one also pins the period labels. So two Signals converge **only if they are
the same measurement**, which §13 forbids by name.

**Measured against the live database:** 28 Claims, 28 distinct proposition keys,
and the closest pairs differ by **exactly one fact**. In twelve pairs that fact is
`content_id` — same platform, same audience class, same period pair, same
direction, different article. Those are Docker, Podman and Kubernetes on the same
day, and merging them is precisely what removing the field would do.

---

## §5 — The candidate matrix

Governance read from the live catalog under `local-private-research-v1`. **Four
sources are eligible, resource-ready and collector-implemented**: `gdelt`,
`stack-exchange`, `ted-eu`, `wikimedia-pageviews`. Twenty-two are blocked at the
eligibility gate, including every consumer, gaming, creator and app-store route
§33 would prefer.

| Candidate | Domain | Taxonomy | Governance | Verdict |
|---|---|---|---|---|
| TED CPV division other than 90 | procurement of a non-developer category | **CPV, official EU** | ELIGIBLE | `NO_MULTI_EVIDENCE_PATH` |
| non-developer Stack Exchange site + tag | consumer hobby Q&A | site tag vocabulary, source-native | ELIGIBLE | `NO_MULTI_EVIDENCE_PATH` |
| consumer/gaming Wikipedia article | consumer / entertainment | **none usable** | ELIGIBLE | `WRONG_GRAIN` |
| consumer lexical term via GDELT | news coverage | **none** | ELIGIBLE | `WRONG_GRAIN` |
| Steam / App Store / Google Play / Product Hunt product | gaming and consumer apps | store category, would qualify | **BLOCKED AT THE GATE** | `GOVERNANCE_BLOCKED` |
| second developer-tooling subject | same as Docker | none | ELIGIBLE | `TOO_SIMILAR_TO_DOCKER` |

Full matrix with every §5 column in
[second-pilot-selection-v1.json](../data/second-pilot-selection-v1.json). No
numeric score anywhere — §3 forbids one, and a test asserts no candidate field
holds a number.

**The pattern is the finding.** The two candidates that pass taxonomy and
governance fail on the architecture. The two that pass the architecture check
vacuously fail on taxonomy. The one with the best domain diversity is blocked at
the gate, and §4 makes that a hard stop — no scraping workaround, no unofficial
mirror, no anti-bot circumvention.

---

## §45 — The forty-six questions

**1–5. Which candidates, domains, scope types, taxonomies, governance status?**
See the matrix above and the artifact. Six candidates: procurement CATEGORY,
community-Q&A PRODUCT/CATEGORY, consumer PRODUCT via Wikimedia, an UNDETERMINED
lexical term, a store-listed consumer PRODUCT, and a second developer tool.

**6. Which candidate was selected?** **None.** §34 freezes a selection so
acquisition can be held to it; acquisition would have been pointless.

**7. Why?** Because no candidate can reach the mission's load-bearing requirement,
and the reason is identical for all of them.

**8. Why were the alternatives rejected?**
Store platforms: blocked at the eligibility gate. Wikimedia and GDELT: no
published taxonomy classifies the subject — Mission 1.35 excluded Wikipedia
categories by name and established that a term is not a category. A second
developer tool: §1 and §6 refuse engineering convenience, and it would contribute
nothing — twelve existing claim pairs already differ from Docker's only by
`content_id`. TED and Stack Exchange: the architecture.

**9. Is it materially different from Docker?** Not applicable; none selected.

**10–11. Canonical subject id and taxonomy basis?** None created. §35's procedure
was not invoked.

**12–15. Source routes, acquisition, completeness, Signal types?** **No
acquisition was performed**, so no route was used, no completeness question
arises, and no Signal type was created or reused.

**16–18. Preregistered proposition, key, mapped Signals?**
None was frozen. §9 requires the convergence rule to be frozen *before*
acquisition results are inspected; freezing one that no source can satisfy would
be preregistering a shape rather than a rule.

**19–25. Claim id, Evidence count, ids, distinctness, reliability, independence?**
No Claim was created. Existing state unchanged: 28 Claims, 28 Evidence rows, one
row per Claim.

**26–29. Which aggregation mechanism saw more than one input?**
**None.** `max(members)` still never has more than one member, support saturation
still receives one group, and contradiction still receives nothing. §22 asks for
the exact mechanism exercised; the honest answer is that none was, and no run was
staged to make it look otherwise.

**30–31. Diagnostic aggregation result? Still UNCALIBRATED?**
No new aggregation was run. `REFERENCE_PROFILE_V1` is `UNCALIBRATED`.

**32. How does it compare to reliability pass-through?**
**`IDENTICAL_TO_PASS_THROUGH`**, unchanged from Mission 1.37: 19 of 19 scorable
claims.

**33. Did a commercial Opportunity dimension gain support?** No.

**34–39. Opportunity, score, ranking, calibration labels, parameters, CALIBRATED
profile?** None, none, none, none, none, none.

**40. New ReliabilityAssessments?** None. Two, unchanged.

**41. Model calls?** **0.** **42. Embeddings?** **0**, and none were considered:
§41 forbids embeddings, vector similarity and model equivalence for the
convergence decision, and the decision was made from the fact sets themselves.

**43. Is Problem-Family still PARKED?** Yes. §40's merge route was never
considered.

**44. What changed in the calibration feasibility audit?**
**Nothing, and the artifact is byte-identical** — `--check` passes. Before and
after are the same measurement, which is the honest answer to §37's question:

> **DID WE MOVE FROM ZERO CALIBRATION-USEFUL SHAPES?** **No.**

Claims 28 → 28 · Evidence 28 → 28 · Claims with >1 Evidence **0 → 0** · maximum
Evidence per Claim **1 → 1** · scorable multi-record Claims 0 → 0 · contradiction
cases 0 → 0 · independence-established 0 → 0 · temporal cases 0 → 0 · proposition
kinds 2 → 2 · leakage groups 2 → 2 · support-strength variation 2 values → 2
values.

**45. Canonical counters before/after?** Read from the live deployment.

| counter | before | after |
|---|---:|---:|
| RawRecords | 148 | **148** |
| NormalizedRecords | 148 | **148** |
| Signals | 28 | **28** |
| Claims | 28 | **28** |
| ClaimRevisions | 29 | **29** |
| Evidence | 28 | **28** |
| EvidenceIndependenceGroups | 0 | **0** |
| ReliabilityAssessments | 2 | **2** |
| Reliability basis rows | 6 | **6** |
| Opportunities / revisions / links | 1 / 1 / 7 | **1 / 1 / 7** |
| Embeddings | 0 | **0** |
| Scores | 0 (`scoring.scores` absent) | **0** |
| Registered sources | 29 | **29** |
| Scope relations | 0 | **0** |

Every one matches §38's expected baseline, and none moved.

**46. Recommended next mission?** See below.

---

## The gap, stated precisely

It is **not** that `proposition_key` is wrong. It is that **every implemented
interpretation is a one-to-one restatement of one Signal**, so a Claim is
isomorphic to its Signal by construction. Mission 1.37 found the symptom — one
Evidence per Claim — and this is the cause.

**Half of the behaviour is correct and must not be repaired.** For an OBSERVED
claim, attribution *is* the claim (Mission 1.13.1). *"Wikimedia counted X"* and
*"Stack Exchange published Y"* are two different propositions, and merging them
across sources would be wrong rather than merely permissive. **Deleting
`source_id` is not the fix.**

**A concrete convergence that should be possible, and is not.** Two *disjoint*
TED notice cohorts in one CPV division and period, each showing a stated-total
contrast, each independently establishing *"TED published award notices in
division X whose stated totals differ"*. Neither cohort is privileged. They
cannot converge because `notice_ids` **and** `classification_codes` are in the
proposition facts, so cohort membership *is* the proposition.

**This mission did not remove those two fields**, and that is §8 and §44 E
working: *do not weaken identity to avoid E*. Removing identity fields while also
acquiring would be designing the Claim after seeing which records would
conveniently merge — the thing §9 forbids by name.

---

## §46 — Recommended next mission

**Mission 1.39 — Proposition Convergence Contract V1**, and no acquisition until
it lands. §46: *repair only the exact proposition identity/convergence gap before
more acquisition.*

It must decide four things, and this mission deliberately answered none of them:

1. Whether a bounded **existence or contrast proposition over a source-native
   class** is a legitimate `OBSERVED` claim, or whether it requires the
   `INFERRED` layer that `docs/CLAUDE.md` records as deliberately unbuilt — *"no
   module for it, no branch to reach and no parameter that would select one"*.
2. Which identity fields such a proposition may omit **without letting unrelated
   observations collapse**, stated as a rule rather than per template. The Docker
   and Podman claims are the test case any rule must survive.
3. How two Evidence rows over an **overlapping population** are marked, given
   that Mission 1.32 established a second measurement over one corpus is not a
   second finding, and independence stays `UNKNOWN`.
4. Whether the convergence rule can be **deterministic and source-bounded**,
   since §41 forbids embeddings, similarity and model equivalence for it.

**Carry candidate A forward.** A TED CPV division other than 90 is the only
candidate that fails on the architecture *alone* rather than also on taxonomy,
governance or commercial path. Choosing the division still needs the official CPV
table retrieved first: Mission 1.33 recorded that the collector deliberately
expands no CPV code into a label, so naming one here from memory would be doing
exactly what the collector refuses.

**Do not return to Docker**, and do not re-run this selection until the
convergence contract exists — the matrix would come back identical.

---

## Artifacts

| | |
|---|---|
| [second-pilot-selection-v1.json](../data/second-pilot-selection-v1.json) | the candidate matrix and the blocking finding |
| [test_second_pilot_selection.py](../../packages/evidence-aggregation/python/tests/test_second_pilot_selection.py) | 29 tests |

The tests parse `observed_restatement.py` **over the AST** rather than scanning
its text, so a docstring naming a fact cannot be mistaken for one
(`testing-strategy.md` §23), and they assert the finding against the real
interpreter and the real repository rather than against the document that
describes them. A document claiming every template pins the measurement identity
is worth nothing the moment a template stops doing so.
