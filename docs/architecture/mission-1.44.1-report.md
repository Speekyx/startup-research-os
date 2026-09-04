# Mission 1.44.1 — Wikimedia Convergent Operator Reliability Decision V1

**Primary outcome: `WIKIMEDIA_CONVERGENT_OPERATOR_RELIABILITY_DECISION_PERSISTED`**
(§24 A), reached by way of **`OPERATOR_CONFIRMATION_REQUIRED`**: the mission
prepared everything, stopped at the typed-confirmation guard, and the operator ran
the command and typed it.

**Secondary outcome, and §18 requires it be said plainly:
`AGGREGATION_MECHANISM_STILL_UNIDENTIFIABLE_FROM_REAL_CORPUS`.** Six Claims became
scorable, `max(members)` received four real items for the first time, and the full
aggregator agrees with the Mission 1.37 B-2 pass-through baseline on all six —
because every Claim still has exactly one provenance group, and Mission 1.43
proved that identity is algebraic rather than incidental.

```text
ReliabilityAssessments  3 -> 4          basis rows  10 -> 12
convergent rows RESOLVED  18/18         evidence.reliability written  0
scorable multi-Evidence Claims  2 -> 8  max(members) received  4, 3, 3, 3, 3, 2
leak checks  36 run, 0 leaks            independence groups  0
```

Artifacts:
[the completed review](../data/wikimedia-convergent-operator-reliability-review-v1.md)
·
[resolution and diagnostic](../data/wikimedia-convergent-reliability-resolution-v1.json)
·
[feasibility audit](../data/calibration-feasibility-audit-v1.json).

---

## §25 — Final report

### The baseline and the question asked

**1. Did the live baseline match Mission 1.44?** **Yes**, every counter checked
before any work: 18 Evidence rows across 6 Claims, all `NON_SCORABLE`, all six
Claims `UNAVAILABLE`, 3 current assessments, 10 basis rows, and the scope
resolving `NO_APPLICABLE_ASSESSMENT` in both directions.

**2. Exact five-part scope?**

```text
source_id         wikimedia-pageviews
resource_id       metrics/pageviews/per-article/en.wikipedia.org
record_kind_id    content_request_count
claim_type        OBSERVED
proposition_kind  platform_counted_content_request_change_witnessed
```

Byte-identical to the scope Mission 1.44 prepared. **It carries no article, no
direction, no requester class, no period and no witness count**, which is why one
judgement binds all 18 rows rather than six judgements binding three each.

### The operator's answers, carried and not adjusted

**3. Exact ordinal profile?**

| dimension | state |
|---|---|
| `MEASUREMENT_DEFINITION` | `DOCUMENTED_AND_BOUNDED` |
| `SOURCE_SIDE_VALIDATION` | `DOCUMENTED_WITH_UNBOUNDED_LIMITATION` |
| `HISTORICAL_MUTABILITY` | `PARTIALLY_DOCUMENTED` |
| `COMPLETENESS_AND_MISSINGNESS` | `PARTIALLY_DOCUMENTED` |
| `SOURCE_SIDE_CHECKABILITY` | `NOT_ESTABLISHED` |

Mission 1.44 pre-filled exactly one of these — `SOURCE_SIDE_CHECKABILITY`, the
only state software may assert, because *no document in this basis addresses this
question* is a checkable claim about the corpus. **The reviewer confirmed it and
supplied the other four.** `HISTORICAL_MUTABILITY` came back
`PARTIALLY_DOCUMENTED`, which is precisely the judgement Mission 1.44 refused to
make on the reviewer's behalf: an incident list with no revision policy is
*something and not enough*, and how much is enough is not a fact.

**4. Exact six materiality answers?**

| dimension | what is not established | documented | material? |
|---|---|---|---|
| `HISTORICAL_MUTABILITY` | whether a published daily value may later be revised, and whether a consumer could tell | `PARTIAL` | **YES** |
| `SOURCE_SIDE_VALIDATION` | whether requester-class tagging may be re-applied retroactively | `PARTIAL` | **YES** |
| `HISTORICAL_MUTABILITY` | whether a systematic reclassification would remove EVERY witness at once | `NOT_ESTABLISHED` | **NO** |
| `MEASUREMENT_DEFINITION` | whether the definition or tagging rules changed across the 2024-03 periods | `NOT_ESTABLISHED` | **NO** |
| `SOURCE_SIDE_CHECKABILITY` | how long a published daily value stays retrievable | `NOT_ESTABLISHED` | **UNSURE** |
| `COMPLETENESS_AND_MISSINGNESS` | whether any witness date falls inside a known-problem entry | `NOT_ESTABLISHED` | **UNSURE** |

**Two `UNSURE` answers survive as `UNSURE`.** Not `YES`, not `NO`, not *low
confidence*, not `0.5`. Both are carried into the stated limitation rather than
quietly resolved, for the reason Mission 1.42.1 recorded: a reviewer who cannot
yet tell whether an unknown matters has said something real.

**5. Exact four hard-stop answers?** All four **NO**:
`MEASUREMENT_SEMANTICS_NOT_ESTABLISHED`, `PROPOSITION_EXCEEDS_MEASUREMENT`,
`AUTHORITATIVE_DOCUMENTS_CONTRADICT`, `SOURCE_OBSERVATIONS_NOT_RECOVERABLE`.

**The fourth is worth reading twice, and it is not a contradiction.**
`SOURCE_SIDE_CHECKABILITY` is `NOT_ESTABLISHED` while
`SOURCE_OBSERVATIONS_NOT_RECOVERABLE` is `NO`. The first says the held basis does
not establish long-term checkability; the second would be the stronger claim that
the observations are **known** to be unrecoverable. The reviewer answered the
weaker fact and the stronger claim separately, and **software derived neither from
the other**.

**6. Exact numeric gate?** `NUMERIC_JUDGEMENT_PERMITTED`. **Recorded, never
recomputed.** The rubric defines the gate as a judgement rather than an arithmetic
function over the five ordinal states, and the two `YES` materiality answers did
not automatically refuse it, because rubric §13 forbids blocking on every unknown.

**7. Exact human reliability value?** **`0.6`**.

**8. Exact reviewer?** **`thibchm`**, supplied by the operator. Not inferred from a
git author, a PR author, an OS username, the existing assessments, or this
conversation.

**9. Was the rationale explicitly human-approved?** **Yes.** The text was prepared
as a **draft** by the assistant and recorded in the review artifact so the reviewer
could read the exact wording before it became theirs. The persistence workflow
printed the file and required the reviewer to type a confirmation stating that what
it contains is their judgement. **That keystroke is what converted a draft into a
review**, and the artifact says so in its own `rationale_and_limitation_note`.

**10. Exact persisted rationale?**

> The reliability judgement is based on first-party Wikimedia documentation that
> defines the pageview measurement, requester-class tagging rules, documented
> exclusions, and known-problem history.
>
> The measurement definition is documented and bounded for this proposition, while
> requester classification relies on documented heuristic tagging. Historical
> revision behaviour and completeness are only partially documented, and
> source-side long-term checkability is not established.
>
> I consider the documentary basis sufficient to permit a numeric reliability
> judgement while preserving unresolved questions concerning retroactive
> revision/reclassification and long-term retrievability.

**11. Was the limitation explicitly human-approved?** **Yes**, by the same
keystroke and the same mechanism.

**12. Exact persisted limitation?**

> The held documentation does not fully establish how historical pageview values or
> requester classifications may be revised or reprocessed after publication, nor
> how a consumer would detect such changes.
>
> Long-term retrievability of historical daily values remains unestablished, and it
> is also unresolved whether any reviewed witness date coincides with a documented
> known-problem period.
>
> Multiple witnesses share the same publisher, counting methodology,
> requester-classification mechanism and pipeline, so witness cardinality does not
> establish independent corroboration.

**The third paragraph is the one convergence introduced.** It is the reviewer
answering, in the assessment itself, the question Mission 1.44 raised: four
witnesses of one methodology do not insure against a methodology-level failure.

### The number is the operator's, and it is not a copy

**`0.6` is not `0.65`, not `0.55`, not `0.5`**, and a test asserts all three — the
shapes a nudging or averaging bug would take. It was not rounded, not rescaled, not
derived from the ordinal ranks, not anchored to the detailed Wikimedia value
sitting one scope field away, and not copied from the convergent TED scope.

**An arithmetic check for averaging was written, it failed, and it was removed
rather than the operator's value being questioned.** `0.6` happens to be exactly
the midpoint of `0.65` and `0.55`. That is a coincidence of two numbers, not
evidence of derivation: the reviewer supplied the value against the recorded
ordinal profile, the two historical values belong to different scopes, and
**software cannot prove the provenance of a number from the number**. Asserting the
negative would have been asserting something unknowable, so the test asserts only
what is checkable — that the value is not any of the three it might have been
copied from.

### What was persisted

**13. Exact rubric id/version?** `human-reliability-assessment-rubric` / `1.0.0`,
read from the rubric module rather than typed.

**14. Historical `0.65` unchanged?** **Yes.** Assessment `e2419f13-…` v1,
`superseded_at` NULL, reliability `0.65`, untouched. So are the TED `0.5`
(`3de2af10-…`) and the TED convergent `0.55` (`d1afa4be-…`). **Nothing was
superseded**, because a different `proposition_kind` is a different question rather
than a revision of somebody else's answer, and `_next_version` correctly found no
same-scope row.

**15. Historical rubric provenance unchanged?** **Yes.** Both pre-rubric
assessments still read `review_rubric_id = NULL` and `review_rubric_version =
NULL`. **That is the true answer for them**, not a missing one: they were reviewed
before the rubric existed, and backfilling would fabricate the provenance the
column was added to record.

**16. New assessment id/version?** `19e0ce16-957f-4543-9b15-738a77b13060`,
**version 1**, recorded `2026-09-04T06:51:19.661075+00:00`.

**17. Origin?** `HUMAN_REVIEW`.

**18. Basis rows persisted?** **2.** Repository total 10 → **12**.

**19. Exact basis documents?**

| document | section | basis type | applicability |
|---|---|---|---|
| [Research:Page view](https://meta.wikimedia.org/wiki/Research:Page_view) | Definition; Tagging | `MEASUREMENT_METHODOLOGY` | **REUSED** |
| [Data Platform / Data Lake / Traffic / Pageviews](https://wikitech.wikimedia.org/wiki/Data_Platform/Data_Lake/Traffic/Pageviews) | Events and known problems since 2015-05-01 | `KNOWN_LIMITATION` | **PARTIALLY_APPLICABLE** |

Both were already held on the detailed Wikimedia assessment. **No SROS engineering
validation is among them**, and a test enforces it: the convergence contract's
determinism, the witness-key duplicate guard, the Evidence idempotency repair and
passing CI establish that the implementation does what its specification says, and
nothing about how dependable the platform's counting is.

**20. Any network request?** **No. Zero.** Nothing was fetched: the convergent
proposition reads the same measurement through the same rules, so both held
documents still describe it.

**21. Any model call?** **No. Zero. 0.00 USD.**

### Resolution, and the eighteen rows

**22. Did all 18 rows resolve?** **Yes. 18 of 18 `RESOLVED`**, through the real
resolver, to one assessment id.

**23. Exact binding?** Every row carries the same one:

```text
assessment_id           19e0ce16-957f-4543-9b15-738a77b13060
assessment_version      1
reliability             0.6
origin                  HUMAN_REVIEW
reviewed_by             thibchm
review_rubric_id        human-reliability-assessment-rubric
review_rubric_version   1.0.0
```

**The binding names everything needed to reconstruct the number**, which is why
Mission 1.42.1 added the two provenance keys to it.

**24. Any leak to the detailed Wikimedia scope?** **No.** The detailed `0.65`
shares `source_id`, `resource_id`, `record_kind_id` **and** `claim_type` with the
scope under review — four of five — and differs only on `proposition_kind`. That
alone is sufficient, and it was exercised through the real resolver in both
directions rather than asserted.

**25. Any other reliability leak?** **No. 36 leak checks run, 0 leaks.** The
resolver was offered each of the four current assessments against every proposition
kind in the corpus, and resolved in exactly the cases where all five scope fields
were identical. Four current assessments is four sets of ways to leak, which is why
the count grew from Mission 1.44's 30.

**26. Persisted Evidence reliability columns still NULL?** **Yes.**
`scoring.evidence.reliability` is NULL on **all 57 rows**, before and after.
Eighteen rows resolve a number and **not one stores it**: reliability binds late
(ADR-026 Decision 2), so a score names the assessment and version it used, and a
copy on the row could outlive the assessment it came from.

### The aggregation, and what it did not show

**27. Did all six multi-Evidence Claims become scorable?** **Yes**, all six
`COMPLETE`.

**28–33. Counts, per Claim.**

| Claim | article | direction | raw | scorable | `max(members)` received | groups | collapsed |
|---|---|---|---|---|---|---|---|
| `e740d102` | `Docker_(software)` | INCREASING | 4 | 4 | **4** | 1 | 3 |
| `1324d79c` | `Kubernetes` | INCREASING | 3 | 3 | **3** | 1 | 2 |
| `9bda8081` | `Kubernetes` | DECREASING | 3 | 3 | **3** | 1 | 2 |
| `a4809b1a` | `Podman` | INCREASING | 3 | 3 | **3** | 1 | 2 |
| `dff657c2` | `Podman` | DECREASING | 3 | 3 | **3** | 1 | 2 |
| `39449935` | `Docker_(software)` | DECREASING | 2 | 2 | **2** | 1 | 1 |

**30. Did `max(members)` receive 4 real items?** **Yes**, once. **31. Three?**
**Yes**, four times. **32. Two?** **Yes**, once. Group cardinality above two had
never occurred in this repository: Mission 1.42.1 was the first time it received
*two*.

**33. Runtime group count per Claim?** **One**, on all six. Every witness of a
Claim lands in the single `__unknown_independence__` group.

**34. Independence state?** `UNKNOWN` on all 18 rows.

**35. Independence groups?** **0**, in these Claims and in the whole deployment.

**§12 — four witnesses is not corroboration, and this is where it must be said.**
The multi-evidence mechanism genuinely ran:
`MULTI_EVIDENCE_PROCESSING_OCCURRED / NO_INDEPENDENT_CORROBORATION` on all six. The
witnesses share one publisher, one counting methodology, one
requester-classification mechanism and one pipeline; different days are temporal
separation, not epistemic independence. **Cardinality 4 raises observed volume, not
evidence strength**, and nothing in this report may be read as saying otherwise.

**36. `q` components?** `relevance` 1.0, `directness` 1.0, **`reliability` 0.6**,
`extraction_confidence` 1.0, `freshness` 1.0 — on every one of the 18
contributions.

**37. `q` values?** **`0.6`** on all 18.

**38. Limiting components?** **`reliability`, on 18 of 18** — and on **34 of 34**
scorable Claims corpus-wide. `q = min(components)` and every other factor is `1.0`,
so the score is a restatement of one human judgement rather than a corroboration of
it.

**39. Support strength?** `0.6`. **40. Contradiction strength?** `0.0`.

**41. Four masses?** `supported_mass` **0.6**, `contradicted_mass` **0.0**,
`conflict_mass` **0.0**, `uncertainty_mass` **0.4** — identical on all six.

**42. EvidenceScore?** **60.0** on all six. **Not a probability, not calibrated,
not persisted.**

**43. EvidenceLevel?** **1, "Weak Signal"**, on all six.

**44. Blockers?** The same three everywhere:

- *Repeated Signal needs 2 supporting groups of established independence, found 0
  (plus 1 unknown-provenance group, which does not count)*
- *Market Evidence needs a supporting record categorised `MARKET_ACTIVITY` or
  `DIRECT_VALIDATION` with established provenance*
- *Direct Validation needs a supporting record categorised `DIRECT_VALIDATION` with
  established provenance*

**Reliability reaches none of the three.** Four witnesses did not move the level,
and the blocked reason says exactly why in the aggregator's own words.

### The finding §18 requires

**45. Full aggregator versus B-2?** `IDENTICAL_TO_RELIABILITY_PASS_THROUGH` on all
six, baseline `0.6`.

**46. Any case where they differ?** **No.**

**47. If not, the algebraic reason.** Saturation over support groups is
`S = 1 - prod(1 - g)`. With exactly **one** group that product has one factor, so
`S` is that group's strength. Group strength is `max(members)`, and every member's
`q` is reliability-limited at the same `0.6`. B-2 reports the reliability-limited
strongest item, which is the same maximum over the same values. **The two are
therefore the same number by construction, not by coincidence**, and no quantity of
additional single-group Evidence can make them differ. Mission 1.43 established
this before any of this data existed; Mission 1.44.1 is the first mission to
observe it with cardinalities of three and four.

**48. Claims with more than one support group?** **0.**

**49. Contradiction cases?** **0.** A decrease does not contradict an increase:
under this kind `direction` is proposition identity, and under an existential a
counterexample does not falsify.

**50. Established-independence cases?** **0.**

**51. Temporal cases?** **0.** All 34 scorable Claims are `EVERGREEN` with no
`claim_feature`, and the reason is architectural rather than incidental: every
`OBSERVED` restatement is a historical fact about what a source published, and a
historical fact does not decay.

> **`AGGREGATION_MECHANISM_STILL_UNIDENTIFIABLE_FROM_REAL_CORPUS`.**
> Support groups per Claim = 1 everywhere, and contradiction cases = 0. Under §18
> that is reported explicitly, and **calibration is not recommended because the
> scorable count increased.** Eight scorable multi-Evidence Claims that all agree
> exactly with a pass-through baseline are eight instances of one measurement, not
> a dataset.

### Corpus shape after the decision

**52. Scorable multi-Evidence Claims before/after?** **2 → 8.** Multi-Evidence
Claims themselves are unchanged at **8**: what moved is scorability, not structure.

**53. Max scorable Evidence cardinality?** **4** (was 2).

**54. Reliability-value distribution?** `{0.5: 6, 0.55: 4, 0.6: 6, 0.65: 18}` — a
fourth value, and **not a fourth kind of thing**. All four are reviewed
`HUMAN_REVIEW` reliability values, so Mission 1.37's finding stands: the target
variable is still reviewed reliability, and the echo hazard is still the whole
dataset.

**55. Limiting-component distribution?** `{reliability: 34}`. Unchanged in kind.

### What was deliberately not done

**56. Was any calibration label created?** **No.**

**57. Any parameter fitted?** **No.**

**58. Did the profile remain `UNCALIBRATED`?** **Yes.** `reference-v1` @ `1.0.0`,
status `UNCALIBRATED`, thresholds untouched.

**59. Any Score persisted?** **No.** `scoring.scores` does not exist as a table.
The diagnostic is a JSON artifact and writes no database row.

**60. Any Opportunity change?** **No.** 1 Opportunity, 1 hypothesis revision, 7
evidence links, all unchanged.

**61. Ranking?** **None.** Nothing was ranked, ordered by score, or compared.

**62. Embeddings?** **None.** `nlp.embedding_provenance` holds 0 rows; no
embedding, vector similarity or semantic retrieval was used anywhere.

**63. Problem-Family status?** **Still PARKED.** Not unparked, not revisited.

**64. Exact canonical counters before/after?**

| counter | before | after |
|---|---|---|
| RawRecords | 325 | **325** |
| NormalizedRecords | 325 | **325** |
| Signals | 33 | **33** |
| Claims | 43 | **43** |
| ClaimRevisions | 44 | **44** |
| Evidence | 57 | **57** |
| `scoring.evidence.reliability` non-NULL | 0 | **0** |
| ReliabilityAssessments (current) | 3 | **4** |
| ReliabilityAssessments superseded | 0 | **0** |
| Reliability basis rows | 10 | **12** |
| Independence groups | 0 | **0** |
| Opportunities / revisions / evidence links | 1 / 1 / 7 | **1 / 1 / 7** |
| Registered sources | 29 | **29** |
| Embeddings | 0 | **0** |
| `scoring.scores` | absent | **absent** |

**Two counters moved and thirteen did not**, which is the same shape Mission 1.42.1
reported and the strongest available evidence that a reliability decision changes
what can be read rather than what is held.

**65. Recommended next mission?** See §26 below. **Not calibration.**

---

## §26 — The next strategic mission

**Do not recommend human calibration yet**, and the reason is question 47 rather
than a preference. Without a second provenance group or a contradiction case, the
full aggregator is algebraically indistinguishable from reliability pass-through,
and labelling this corpus would ask a person to compare cases the aggregator itself
cannot distinguish.

**The target is ESTABLISHED INDEPENDENCE.** Recommended:
**Mission 1.45 — Independent Statistical Evidence Route Feasibility V1**. The gap
matrix identifies **Eurostat or FRED beside World Bank** — a second statistical
agency publishing about the same subject is the only visible path to a second
provenance group, and both are eligible under `local-private-research-v1` today.

**It was not started.** The brief forbids starting it automatically, and this
mission stops here.

---

## What this mission did not establish

- **Not calibration.** `REFERENCE_PROFILE_V1` stays `UNCALIBRATED` and `0.6` fits
  no parameter.
- **Not a probability** that any of the six Claims is true.
- **Not source-wide.** The scope is five fields; `wikimedia-pageviews` alone matches
  nothing, and the detailed proposition keeps its own `0.65`.
- **Not an audience score.** A request is what a reader makes of a server, and
  `user` is the platform's own class name for traffic not identified as automated by
  ua-parser plus custom regex. It does not mean human, person, reader or customer.
- **Not a product score.** It says nothing about Docker, Kubernetes or Podman, and
  the scope carries no article at all.
- **Not independent corroboration.** Eighteen rows, six Claims, one provenance
  group each, zero independence groups.
