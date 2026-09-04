# Mission 1.42 — Second Pilot Convergent Evidence Reliability Review Preparation V1

**Primary outcome: `READY_FOR_SECOND_PILOT_RELIABILITY_REVIEW`** (§30 A).

**0 ReliabilityAssessments created. 0 basis rows persisted. 0 network requests.
0 model calls. Every canonical research counter unchanged.**

Artifacts:
[second-pilot-convergent-reliability-review-packet-v1.json](../data/second-pilot-convergent-reliability-review-packet-v1.json),
[second-pilot-convergent-reliability-review-packet-v1.md](../data/second-pilot-convergent-reliability-review-packet-v1.md).

---

## §0 — The one thing the brief got wrong, and why it is not outcome C

The brief expected **4 Evidence rows across 2 Claims**. The live deployment
holds **6 rows across 4 Claims**, resolving to **exactly one** reliability scope,
which is exactly the expected five-part scope, returning
`NO_APPLICABLE_ASSESSMENT`.

§30 C is `SECOND_PILOT_RELIABILITY_SCOPE_DRIFT` *"if the live Evidence rows do
not match the expected five-part scope"*. They match it. What differs is the
**count of rows inside that one scope**, and the cause is the scope contract
working: **a reliability scope carries no classification division and no
currency**, so it reaches every convergent Claim from this measurement — the
division-90 one and the SEK one included, not only the two multi-Evidence
division-92 Claims Mission 1.41 created.

This is the same property Mission 1.40 recorded from the other side, when the
existing TED assessment bound to the new division-92 *detailed* claim for exactly
the same reason.

**It is reported prominently rather than absorbed**, because it changes what the
operator is being asked to stand behind: one judgement here binds six rows across
four Claims and two CPV divisions, and the division-90 Claim's only witness is
the Signal derived in Mission 1.15.10, before the second pilot existed. A mission
that quietly delivers a wider corpus than its brief described has changed the
question without saying so.

---

## §31 — Final report

### The scope

**1. How many real convergent Evidence rows exist?** **6.**

**2. How many convergent Claims?** **4**, of which **2** carry more than one
Evidence row.

| claim | rev | evidence | class | currency | division | witness records |
|---|---|---|---|---|---|---:|
| `02248c91-a384-442d-8c78-80ba4c1bd2b1` | 1 | `a77d8ea7-16f7-4259-831d-163c637ffccc` | CONTRACT_AWARD_NOTICE | EUR | 92 | 12 |
| `02248c91-…` | 1 | `cf9f792d-9811-43b7-b089-dcf3e835225a` | CONTRACT_AWARD_NOTICE | EUR | 92 | 14 |
| `bf4e4b48-fdf9-48f6-9c69-2178eb361e18` | 1 | `09bfc370-59d2-4aca-83b8-cf717a1cc329` | CONTRACT_NOTICE | EUR | 92 | 17 |
| `bf4e4b48-…` | 1 | `1ad1dc6d-7528-4527-bccd-0a09f47112ac` | CONTRACT_NOTICE | EUR | 92 | 20 |
| `6389d1bf-6dea-47e8-8508-dcf009fe352d` | 1 | `ce349b01-1ea4-4d11-b162-e745e2c82163` | CONTRACT_NOTICE | SEK | 92 | 2 |
| `73e834c4-ddad-4093-9727-79720e074b4b` | 1 | `b7dc27bf-53c8-4e80-9c83-5980c80fa46c` | CONTRACT_AWARD_NOTICE | EUR | **90** | 3 |

**3. How many distinct reliability scopes?** **One.** Measured by grouping the
six rows on the five-part key, not assumed from the fact that one proposition
kind was expected.

**4. Exact five-part scope?**

```text
source_id         ted-eu
resource_id       notices/eforms-contract-and-award
record_kind_id    procurement_notice
claim_type        OBSERVED
proposition_kind  source_published_classification_value_contrast_witnessed
```

**5. Exact affected Claim ids?** The four in the table above.

**6. Exact affected Evidence ids?** The six in the table above.

**7. Current resolver result?** `NO_APPLICABLE_ASSESSMENT`, `reliability = None`,
produced by the real `resolve_reliability` over the two live assessments. All six
rows stay `NON_SCORABLE`, and both multi-Evidence Claims stay `UNAVAILABLE`.

### Why the existing 0.5 does not answer this

**8. Why does the existing TED 0.5 not bind?** Its `proposition_kind` is
`source_reported_procurement_value_contrast`. The other four scope fields are
identical — same source, same resource, same record kind, same `OBSERVED` claim
type — and **that is the point**: four of five matching is as inapplicable as
none matching, and a resolver that matched on "closest" would leak here first.
One field is the whole difference, and a test exercises it in both directions.

**9. What semantic difference exists between detailed and convergent Claims?**
The detailed claim asserts that within a **named** set of notices, the largest
stated amount exceeded the smallest. The convergent claim asserts that the source
published **at least one bounded set** of notices in a named class and division
whose stated amounts stand in the named relation. Cohort membership moved from
**proposition identity** to **witness provenance** (ADR-035); it was not
discarded, and the witness records above are recovered from lineage.

**10. Which underlying measurement semantics are shared?** Same source, resource
and record kind. Same BT-161 amount and the same companion currency field. Same
reading direction — what TED *stated*, never what any buyer paid (§13 remains
binding; nothing in this mission uses price, revenue, willingness-to-pay,
realised payment or market-size language). Same conformance boundary: TED
validates where BT-161 may appear and never whether it is correct.

**11. Which reliability questions are new?** Four, and none of them has a
documentary answer:

- an **existential is monotone** — once a qualifying cohort is published, no
  later notice can falsify it. Whether that makes the proposition more dependable
  or merely **harder to falsify** is a judgement, and those are not the same
  thing;
- it carries **no period**, because H-37 leaves TED's publication-date semantics
  unestablished;
- it asserts about a **class**, so it inherits whatever the classification's own
  correctness is worth;
- **two cohorts are asserted to witness one proposition**, which is an SROS step
  that does not exist for the detailed claim at all.

### The documents

**12. Which authoritative documents were inspected?** The four already held on
the existing TED assessment, all first-party eForms SDK 1.15.1: the BT-161
business-term definition, the `fields.json` BT-161-NoticeResult entry, the 60
business rules naming BT-161, and BT-195–BT-198 on withholding. **Nothing new was
retrieved, because nothing new was needed** — the convergent proposition reads the
same field of the same notices.

**13. Which existing documentary basis rows remain applicable?** **Three,
REUSED.** The BT-161 definition defines what the amount means, unchanged by
whether the cohort is named. The field repository is *more* load-bearing now: the
companion currency field is what makes a currency-pure cohort expressible at all.
And the 60 rules — none of which concerns the amount's correctness — state an
identical limitation under either proposition.

**14. Which are only partially applicable?** **One: BT-195–BT-198 withholding.**
The fact is unchanged; its **weight** is not. Under the detailed claim,
withholding bounds what a named cohort represents. Under an existential it cannot
falsify the claim at all. How much that matters is a reviewer's call, and the
packet says so instead of deciding it.

**15. Which are not applicable?** **None.** Every held document still bears on
the measurement; what changed is the proposition, not the field being read.

### Failure modes

**16. What source-level failure modes exist?** Three. A stated amount can be
wrong and still conform, because no rule checks correctness. A result value can
be lawfully withheld. And **a published notice may be corrected, amended or
superseded** — for which nothing held is documented and no mitigation exists.

**17. What SROS convergence/interpreter failure modes exist?** Six, across four
origins. Two currencies compared as one distribution and a per-lot value compared
with a whole-notice value (EXTRACTOR). A notice's classification projected to the
wrong division (NORMALIZER). Two cohorts treated as witnessing one proposition
when they do not, and one witness counted twice (CONVERGENCE_CONTRACT) — **the
first of these does not exist for the detailed proposition**. And the acquisition
window shaping which cohorts exist (COLLECTOR).

**18. Which failure modes are already mitigated?** Eight of nine. Currency and
amount scope are cohort-key fields since extractor 1.1.0, backed by the
validation that still refuses a forced mixture; a multi-division notice joins
**no** cohort rather than the first listed; the convergence contract has ten
fixed identity fields, is deterministic, and refuses unclassified facts;
`witness_key` plus Mission 1.41's Evidence-identity repair prevent double
counting; and the existential wording bounds the window risk to how a reader
summarises it.

**19. What remains unknown?** Four open questions, led by the one with real
weight: **whether TED permits a published BT-161 to be corrected, and whether a
corrected notice supersedes an earlier one in this resource.** No document, no
mitigation, and it bears directly on whether a witnessing cohort still witnesses.
The others: whether an assigned CPV code can change after publication; whether a
period-free existential is more dependable or merely harder to falsify; and how
often division-92 notices withhold their result values, which is not measurable
from the source's own documentation.

### What does not substitute for a judgement

**20. Is currency grain now correctly bounded?** **Yes.** Mission 1.41 made
currency and amount scope part of the cohort key, and Mission 1.41 §6 verified
rather than argued it: the historical division-90 Signal re-derived with
magnitude, currency, direction, amount types, scopes and codes all identical.

**21. Does that imply reliability?** **No.** It establishes that the
implementation does what its specification says. It establishes nothing about how
dependable TED's source-reported amounts are. The engineering validation inputs
are recorded in the packet in their own block, flagged
`may_be_used_as_reliability_basis: false`, and a test asserts no candidate basis
row is one of our own missions. **Rewarding the system numerically because its
tests pass is precisely the error this separation exists to prevent.**

**22. Does `DISJOINT` overlap imply independence?** **No.** Independence is
`UNKNOWN` on all six rows with **0** independence groups. Two publication windows
are temporal separation; the publisher, the collection mechanism, the methodology
and the population are shared. No `EvidenceIndependenceGroup` was created.

**23. Did software suggest a reliability value?** **No.** Every judgement field
is `null` or empty, and the generator has no code path that could fill one.

**24. Did software suggest a numeric range?** **No.** The scale is `[0.0, 1.0]`
with `threshold_labels: null`, because the architecture defines no threshold
vocabulary. A test scans the whole packet — with `$comment` and `$note` keys
stripped, so the sentences stating the rule cannot fail the rule — for
*recommended reliability*, *suggested reliability*, *reliability range* and the
three threshold adjectives.

**25. Was reviewer inferred?** **No.** Not from a git author, a PR author, an OS
username, the existing assessment, or this conversation. A test asserts the name
on the existing other-scope assessment appears nowhere in the worksheet.

### What did not move

**26. Was any ReliabilityAssessment persisted?** **No.** 2 before, 2 after.

**27. Were any basis rows persisted?** **No.** 6 before, 6 after.

**28. Was the existing TED assessment changed?** **No.** Version 1,
`superseded_at` NULL. A different scope is a different question, not a revision
of somebody else's answer.

**29. Did any Evidence reliability column change?** **No.**
`scoring.evidence.reliability` is NULL on all 39 rows, before and after
(ADR-026 Decision 2: reliability binds late).

**30. Did any reliability leak occur?** **No.** **6 leak checks run, 0 leaks.**
Each probe varies only `proposition_kind` and holds every other field
byte-identical; each resolves if and only if the kinds are equal.

**31. Were model calls made?** **0.** 0.00 USD.

**32. Was research data acquired?** **0 network requests of any kind**, TED
included. The frozen category selection is untouched, hash and all.

**33. Did any canonical research counter change?** **No.**

| counter | before | after |
|---|---:|---:|
| RawRecords / NormalizedRecords | 325 / 325 | 325 / 325 |
| Signals | 33 | 33 |
| Claims | 37 | 37 |
| ClaimRevisions | 38 | 38 |
| Evidence | 39 | 39 |
| Evidence with reliability written | 0 | 0 |
| ReliabilityAssessments / basis rows | 2 / 6 | 2 / 6 |
| EvidenceIndependenceGroups | 0 | 0 |
| Opportunities / revisions / links | 1 / 1 / 7 | 1 / 1 / 7 |
| Embeddings / Scores | 0 / 0 | 0 / 0 |
| Registered sources / Scope relations | 29 / 0 | 29 / 0 |

**34. Is the aggregation profile still UNCALIBRATED?** **Yes.**
`REFERENCE_PROFILE_V1` is `UNCALIBRATED` with no half-lives. **Reliability review
is not calibration**, no calibration labels were created, and no parameter was
fitted.

**35. Are both real multi-Evidence Claims still UNAVAILABLE?** **Yes**, for
exactly the reason this mission exists: the convergent proposition kind has no
applicable assessment, so non-scorable rows are excluded before grouping and
`max(members)` still never sees two members.

**36. Is Problem-Family still PARKED?** **Yes.** `PARK_PROBLEM_FAMILY_CLASSIFIER`
stands; nothing here touches it, and a test asserts the packet does not name the
relation.

**37. Is the operator worksheet ready?** **Yes** — in both the JSON packet and
the markdown. One scope, one question 1 (`YES / NO`), four blank judgement
fields, seven unchecked confirmations, and a stated consequence for **NO**: leave
the assessment absent, the six rows stay `NON_SCORABLE`, and that is the designed
behaviour rather than a gap.

**38. Recommended next action?** **A human decision, and nothing else.** Per §32,
the mission STOPS here. If the operator answers **NO**, the scope keeps no
assessment and future corpus expansion continues without inventing a value. If
the operator answers **YES** and supplies a reliability, a reviewer, a rationale
and a stated limitation, the next mission is **Mission 1.42.1 — Second Pilot
Operator Reliability Decision V1**, which may persist exactly one assessment and
then run the first real scorable multi-Evidence diagnostic. **It is not started
automatically.**

---

## What this mission did not do

No reliability value assigned, recommended or ranged. The TED `0.5` not copied,
not averaged with anything, and not treated as a baseline — it appears only as
other-scope historical context, with `is_the_scope_under_review: false`. No
`EvidenceIndependenceGroup` created. No cohort grain changed, no convergence
contract changed, no TED re-acquisition. No calibration labels, no fitted
parameters, no Opportunity Score, no ranking, no second Opportunity. No frontend,
no model call, no embedding. Problem-family inference stays parked, and Mission
1.42.1 has not begun.

## Tests

**34 new tests** across two files under
`packages/evidence-reliability/python/tests/`. The packet tests assert what the
document says; the state tests assert what the mission did to the repository
around it. Both read checked-in artifacts rather than the live deployment,
because CI's integration job starts from an empty database and a counter test
there would be permanently red or loosened until it verified nothing
(`testing-strategy.md` §68).
