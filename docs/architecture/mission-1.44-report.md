# Mission 1.44 — Wikimedia Convergent Evidence Reliability Review Preparation V1

**Primary outcome: `READY_FOR_WIKIMEDIA_CONVERGENT_RELIABILITY_REVIEW`** (§38 A).

**0 ReliabilityAssessments. 0 basis rows. 0 network requests. 0 model calls.
0 embeddings. Every canonical counter unchanged.**

Artifacts:
[packet](../data/wikimedia-convergent-reliability-review-packet-v1.md) ·
[.json](../data/wikimedia-convergent-reliability-review-packet-v1.json).

---

## The two things this scope forced that the TED one did not

**1. The near miss is closer here, and the number is more inviting.** For TED,
the almost-match was one TED assessment against another. Here it is the **same
publisher, the same resource, the same record kind and the same claim type**,
with a reviewed `0.65` sitting exactly one field away. `proposition_kind` is the
only difference, and it is sufficient — verified through the real resolver in
both directions and by **30 leak checks with 0 leaks**, probing every proposition
kind in the corpus rather than a chosen few.

**2. "Something and not enough" is a judgement, and "nothing" is a fact.** Mission
1.42 could assert `NOT_ESTABLISHED` for TED's mutability because the held basis
said **nothing** about correction. Here the basis says **something**: a dated
known-problems list records that a 2016 user-agent classification incident
occurred. It still does not state a revision policy. Whether an incident list
without a policy is `PARTIALLY_DOCUMENTED` or `NOT_ESTABLISHED` is a judgement
about whether what *is* documented is enough — so **software left
`HISTORICAL_MUTABILITY` blank**, which is exactly where a helpful generator would
have filled it in. A test holds that line.

Software asserted **one** state, `SOURCE_SIDE_CHECKABILITY = NOT_ESTABLISHED`,
because the review's basis is two documents and neither addresses what the source
exposes for inspection or for how long. That is a checkable claim about the
corpus, not a judgement about sufficiency.

---

## §39 — Final report

### The scope

**1. Live baseline?** 325/325 RawRecords and NormalizedRecords, 33 Signals, 43
Claims, 44 ClaimRevisions, 57 Evidence, 8 Claims with more than one Evidence, max
4 per Claim, 0 independence groups, 3 assessments with 10 basis rows, 1
Opportunity with 1 revision and 7 links, 0 Embeddings, 0 Scores,
`scoring.scores` absent, 29 sources, `scoring.evidence.reliability` NULL
throughout. Verified before any work.

**2. Convergent Wikimedia Evidence rows?** **18.** **3. Claims?** **6.**

**4. Evidence cardinality per Claim?** **{4, 3, 3, 3, 3, 2}** — Docker_(software)
INCREASING carries four.

**5. Distinct reliability scopes?** **One**, measured by grouping the 18 rows on
the five-part key.

**6. Exact five-part scope?**

```text
source_id         wikimedia-pageviews
resource_id       metrics/pageviews/per-article/en.wikipedia.org
record_kind_id    content_request_count
claim_type        OBSERVED
proposition_kind  platform_counted_content_request_change_witnessed
```

**7. Current resolver result?** `NO_APPLICABLE_ASSESSMENT` on all 18 rows.

**The scope carries no article, no direction, no requester class, no period and
no witness count**, so this is **one** question rather than six — and a Claim
with four witnesses is not thereby a more dependable measurement. Cardinality
belongs to aggregation; reliability belongs to measurement crossed with
proposition.

### Why 0.65 does not answer it

**8. Exact existing detailed Wikimedia scope?** Same source, resource, record
kind and claim type, with `proposition_kind = platform_counted_content_request_change`.

**9. Why does its 0.65 not bind?** Because all five fields must match and one
does not. There is no closest-match logic, no fallback, and no source-wide
coefficient to fall back on — a scope naming only the publisher matches nothing
by construction.

**10. Almost-match leak checks?** **30**, bidirectional: each live assessment
probed against every proposition kind in the corpus, and each live assessment
probed against the scope under review. **11. Any leaks?** **0.**

### The contract

**12. Exact convergence contract?**
`platform-counted-content-request-change-witnessed@1.0.0`. Inspected, not
modified.

**13. Proposition identity facts?** `proposition`, `source_id`,
`content_platform`, `content_id`, `audience_class`, `direction`.
**14. Witness identity facts?** `period_label_from`, `period_label_to`.

**15. Semantic difference?** The detailed claim names one adjacent day-pair; the
convergent one asserts that **at least one** such pair stands in the named
direction. The day labels moved from proposition identity to witness provenance —
not discarded: they stay on the Signal and are recoverable through Evidence →
Signal → `signal_inputs` → `normalized_records`, and the packet lists the witness
observation keys per row.

**16. What does it establish?** That the platform counted, for the named item
under the named requester class, at least one pair of adjacent published day
buckets standing in the named direction.

**17. What does it explicitly NOT establish?** How many such pairs exist, what
proportion of the item's history they are, that the direction is typical or
continuing, any trend or momentum, that a person read anything, audience size or
interest or demand or adoption, that the witnesses are independent, or that the
calendar is controlled for.

**Witness count is not prevalence**, and the packet says so where a reader will
meet it.

### The documents

**18. Which first-party documents were inspected?** The two already attached to
the detailed assessment: **`Research:Page view`** (Definition; Tagging,
`MEASUREMENT_METHODOLOGY`) and **`Data Platform / Data Lake / Traffic /
Pageviews`** (Events and known problems since 2015-05-01, `KNOWN_LIMITATION`).

**19. Was anything fetched?** **No. 0 network requests.** The convergent
proposition reads the same measurement through the same rules, so nothing new was
needed — and fetching to enlarge a basis is not review.

**20. REUSED?** `Research:Page view`. It defines what a pageview *is* and how
requester classes are tagged, and it is if anything **more** load-bearing here,
because `audience_class` is one of the six identity fields the contract keeps.

**21. PARTIALLY_APPLICABLE?** The known-problems document, and the reason is a
two-directional weight change worth stating rather than summarising away. Under
an existential a **localised** problem matters *less*, because only one surviving
witness is needed. A **systematic** reclassification matters *more*, because the
several witnesses of one convergent Claim share a methodology and their
independence is UNKNOWN — so they can all fail together. Which reading governs is
the reviewer's; the packet records both.

**22. NOT_APPLICABLE?** **None.** Both documents still describe the measurement
being read.

### Factual findings

**23. Measurement definition?** A pageview is an explicit conjunction of
HTTP-status, host and header conditions with an enumerated exclusion list.

**24. Source-side validation?** Automated traffic is tagged by **ua-parser plus
custom regex** — pattern matching. The platform documents its own detection
rather than asserting the remainder is human, and `user` is its own class name.
**It is never translated to human, person, reader or customer**, and a test
scans for that.

**25. Historical mutability?** A dated known-problems list exists and records a
2016 user-agent classification incident. **A revision or backfill policy is not
stated**, nor how a consumer would tell that a published value had changed.

**26. Completeness and missingness?** The exclusion list is enumerated and the
known-problems list is dated. Whether that list is complete, and whether any of
the six 2024-03 witness dates falls inside an entry, is not established — the
held finding names a 2016 incident and this review did not enumerate the list.

**27. Source-side checkability?** Neither held document addresses retention or
long-term availability.

**28. Which states was software allowed to assign?** **Exactly one:**
`SOURCE_SIDE_CHECKABILITY = NOT_ESTABLISHED`, justified as a claim about what the
basis contains.

**29. Which remain human judgement?** The other four —
`MEASUREMENT_DEFINITION`, `SOURCE_SIDE_VALIDATION`, `HISTORICAL_MUTABILITY`,
`COMPLETENESS_AND_MISSINGNESS` — each documented in the packet with *why* it was
left blank.

**30. Exact material unknowns?** Six, each with a documentary status:

| unknown | dimension | status |
|---|---|---|
| whether a published value may be revised, and whether a consumer could tell | `HISTORICAL_MUTABILITY` | PARTIAL |
| whether requester-class tagging may be re-applied retroactively | `SOURCE_SIDE_VALIDATION` | PARTIAL |
| whether a systematic reclassification would remove **every** witness at once | `HISTORICAL_MUTABILITY` | NOT_ESTABLISHED |
| whether the definition or tagging rules changed across the 2024-03 periods | `MEASUREMENT_DEFINITION` | NOT_ESTABLISHED |
| how long a published daily value remains retrievable | `SOURCE_SIDE_CHECKABILITY` | NOT_ESTABLISHED |
| whether any witness date falls inside a known-problems entry | `COMPLETENESS_AND_MISSINGNESS` | NOT_ESTABLISHED |

The third is the one convergence *introduces* rather than inherits.

**31. Were any materiality answers supplied?** **No.** Each carries the question
and `YES / NO / UNSURE` blank.

**32. Any hard stop mechanically established?** **No.** All four are listed with
`factual_trigger_present` and `reviewer_decision` blank. **A limitation is not a
hard stop**: each makes a value unavailable because the question has no answer,
never because the answer would be low.

### What software did not do

**33. Numeric gate answered?** **No — `UNANSWERED`.**
**34. Reliability suggested?** **No.** **35. Range?** **No.**
**36. Reviewer inferred?** **No**, and a test asserts the existing reviewer's
name appears nowhere in the worksheet.
**37. Was 0.65 used as a recommendation?** **No.** It appears only under
`historical_other_scope_context` and in the rule blocks that forbid using it —
and a test scans every other field for it, plus every field *name* for
anchor-shaped words like `recommended`, `candidate_value`, `anchor`, `baseline`
and `prior`.

**38. Any ReliabilityAssessment persisted?** **No**, 3 before and after.
**39. Any basis row persisted?** **No**, 10 before and after.
**40. Were historical rubric fields changed?** **No.** The detailed Wikimedia
assessment keeps `review_rubric_id = NULL`, which is **true rather than missing**
— it predates the rubric, and backfilling would fabricate provenance.

**41. Do all 18 rows remain NON_SCORABLE?** **Yes.**
**42. Are all six Claims still UNAVAILABLE?** **Yes**, with
`MISSING_RELIABILITY`. No `q`, no support strength, no Evidence Score, no level
change. That is correct, not a gap.

**43. Independence states?** `UNKNOWN` on all 18.
**44. Independence groups?** **0**, and none created. Different days, different
articles and different directions do not establish independence: one publisher,
one collection method and one counting methodology remain shared provenance.

**45. Contradiction cases created?** **0.** An INCREASING and a DECREASING Claim
are different propositions, not a disagreement, and every Evidence row `SUPPORTS`
its own Claim.
**46. Temporal Claims created?** **0.**

**47. Any canonical counter changed?** **No.**
**48. Network requests?** **0.** **49. Model calls?** **0**, 0.00 USD.
**50. Embeddings?** **0.** **51. Scores?** **0**; `scoring.scores` still absent.
**52. `REFERENCE_PROFILE_V1`?** Still `UNCALIBRATED`.
**53. Problem-Family?** Still **PARKED**.

**54. Is the human worksheet ready?** **Yes** — in both the JSON packet and the
markdown: the scope, the five-state vocabulary, four blank dimensions and one
justified pre-filled absence, six materiality questions, four hard stops, the
gate options with `UNANSWERED`, and blank reliability, rationale, limitation,
reviewer and timestamp. It also records that a future assessment for this scope
**can** carry `human-reliability-assessment-rubric@1.0.0`, because migration 0032
added the columns.

**55. Recommended next action?** **A human review of this scope under the rubric,
and nothing else automatically.** If the gate comes back
`NUMERIC_JUDGEMENT_PERMITTED` with a value, reviewer, rationale and limitation, a
later mission may persist exactly one assessment — and **six real multi-Evidence
Claims become scorable, including the first with four witnesses.**

After that, **do not proceed to calibration.** Mission 1.43's finding still
governs: with one provenance group the full aggregator is algebraically identical
to the reliability pass-through baseline, and these six Claims each have one. The
next strategic mission remains an **independence-capable evidence route** —
Eurostat or FRED beside World Bank — which needs its own governance, collector
and semantic work.

---

## A defect the §37 fixture found on its first run

`ReliabilityBinding.to_json()` called `self.reviewed_at.isoformat()` on a field
four generators already pass as `None`. It had never crashed because **no live
binding had ever been serialised**: every row in the scope under review resolves
to no assessment, so the resolved branch is unreachable from this corpus.

The type said `datetime`; the codebase treated it as optional in four places.
Repaired both ways — the declaration now says `datetime | None`, and the
reporting path serialises `null` instead of raising, because a report that dies
on an absent optional field turns a missing timestamp into a missing report. This
mission's own builder now reads the real column too.

**Third occurrence of the same shape in three missions** — after Mission 1.36.1's
`binding.assessment_version` and Mission 1.42.1's `group.members`. §37 exists
because of them, and it worked.

## Tests

**45 new**, 903 across 8 packages. The `BranchesTheLiveResolverNeverEnters` class
forces the resolved-binding path, the rubric-stamped provenance path and the
two-assessments-for-one-scope refusal, none of which the live corpus reaches.

**One test needed the `testing-strategy.md` §23 repair on its first run** — a scan
for `0.65` failed on the sentence *"NOT an assertion that the existing 0.65 is
near the right answer"*, which is the rule doing the work. It now excludes the
declared rule blocks and separately asserts that those blocks **do** name the
value, so the rule cannot quietly disappear.

The packet's `--check` stays an **operator** gate rather than a CI step: it
measures a deployment, and CI's integration job starts from an empty database
(the distinction Mission 1.37 recorded).
