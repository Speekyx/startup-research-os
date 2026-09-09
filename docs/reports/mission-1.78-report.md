# Mission 1.78 — Revision 2, by supersession

**Outcome: `OPPORTUNITY_REVISION_2_RECONCILED_TO_CURRENT_SCORABILITY`.**

A historical revision may remain true about what the system believed then. A new revision
must be true about what the system can establish now. Revision 1 stays as written; revision 2
carries the same hypothesis over the same seven cited rows, with the one stale sentence
replaced by one computed from the current resolver, and nothing stronger.

---

## Report

```
START_COMMIT                         = f8c91e6
BRANCH                               = sprint-1/mission-1.78
MIGRATION_HEAD                       = 0036_grant_use_profile_vocabulary (measured)
OPPORTUNITY_ID                       = 06113a8b-a83d-423d-8046-18f87d7dbc01
REVISION_1_ID                        = efca07a9-b283-473a-887b-a2ae82989bbe   created 2026-09-02T19:51:57Z
REVISION_2_ID                        = 8739e7ab-940b-408c-a5e8-7f6675d1597c   created 2026-09-09T21:16:39Z
REVISION_REASON                      = RELIABILITY_APPLICABILITY_RECONCILIATION
TOTAL_EVIDENCE / SCORABLE / NON      = 58 / 48 / 10
OPPORTUNITY_LINKED / SCORABLE / NON  = 7 / 6 / 1
PREPARATION_V1_EVIDENCE_CENSUS       = 28 rows, 0 scoring  (historical, sha256 6aab7daf…)
PREPARATION_V2_EVIDENCE_CENSUS       = 58 rows, 48 scoring (current, supersedes v1)
PREPARATION_V1_CURRENT / V2_CURRENT  = false / true
OPPORTUNITIES_BEFORE / AFTER         = 1 / 1
OPPORTUNITY_REVISIONS_BEFORE / AFTER = 1 / 2
OPPORTUNITY_LINKS_BEFORE / AFTER     = 7 / 14   (links are revision-specific)
REVISION_1_CURRENT_BEFORE / AFTER    = true / false   REVISION_2_CREATED = true
REV2_LINKED / SCORABLE / NONSCORABLE = 7 / 6 / 1
REV2_DIMENSIONS                      = AUDIENCE_OR_USAGE, PROBLEM_OR_NEED, TREND_OR_CHANGE
REV2_SOURCE_FAMILIES                 = forum, knowledge
REV2_RELIABILITY_DISTRIBUTION        = {0.65: 6, NONE: 1}
REV2_INDEPENDENCE_STATE              = UNKNOWN on 7 of 7
REV1_SCORING_READY / REV2            = false / true, per the packet contract (see §13 below)
PERSISTED_SCORES_BEFORE / AFTER      = ABSENT / ABSENT
RELIABILITY_ASSESSMENTS_BEFORE/AFTER = 4 / 4      INDEPENDENCE_GROUPS_BEFORE / AFTER = 0 / 0
VIOLATIONS_CAUGHT / ESCAPED          = 47 / 0     positive controls 4 of 4
PRIMARY_OUTCOME                      = OPPORTUNITY_REVISION_2_RECONCILED_TO_CURRENT_SCORABILITY
NEXT_MISSION                         = 1.79 Post-Reconciliation Evidence Priority V1
```

Preconditions verified: tree clean, `main` == `origin/main` at `f8c91e6`, Mission 1.77 present
with `RELIABILITY_APPLICABILITY_ROOT_CAUSE_REVISED`; the late-resolution path re-measured
through the canonical runner (58 / 48 / 7 / 6, the same as reported); assessments 4,
independence groups 0, scores ABSENT, embeddings 0; `REFERENCE_PROFILE_V1` UNCALIBRATED; Q1
CLASS_SELECTED with construct and run false; Globalping 12/0/0; V2 selected and
`V2_VALID_FOR_REFUTATION_BUT_NOT_INDEPENDENT_SUPPORT`, corpus false, measurements 0.

## Revision 1, audited before anything was written

| statement | classification |
|---|---|
| *Every supporting Evidence row is ELIGIBLE_CONTEXT, NON_SCORABLE and MISSING_RELIABILITY: no reviewed reliability applies, so this hypothesis can contribute to no score.* | `STALE_DUE_TO_RELIABILITY_RESOLUTION_FIX` |
| the independence, market-scope, Stack Exchange and Wikimedia-calendar limitations | `NOT_RELATED_TO_1_77`, kept verbatim |
| the reasoning summary's last sentence, *…UNKNOWN independence and MISSING_RELIABILITY across all 7 rows, so no scoring or confidence claim can be attached* | `STALE_DUE_TO_RELIABILITY_RESOLUTION_FIX` on its reliability half; the independence half is still true and stays |
| hypothesis statement, target actor, observed need, candidate intervention, supported and unsupported dimensions, twelve uncertainties | `STILL_TRUE`, carried verbatim |

**Why stale.** The revision was written 2026-09-02; the detailed Wikimedia assessment (0.65,
`e2419f13`) was created 2026-09-03 and the convergent one (0.6, `19e0ce16`) 2026-09-04, and
Mission 1.77 made the Opportunity path resolve reliability late from lineage. Read through
that path today, 6 of the 7 cited rows bind to `e2419f13` at 0.65; the Stack Exchange row
stays `NO_APPLICABLE_ASSESSMENT` because the operator declined that review in 1.36.1.

## What revision 2 is, and is not

**The same hypothesis.** All seven statement fields are byte-identical to revision 1, a gate
refuses any difference, and `model_version` is NULL: no model was called, for a rewrite or
for anything else. Reliability changed whether six rows may enter quantitative aggregation;
it did not change what any of them establishes, and six scorable rows establish no buyer, no
budget, no recurrence, no severity, no adoption, no willingness to pay and no independence.

**The same seven rows.** Links are **revision-specific** — `UNIQUE (workspace_id,
revision_id, evidence_id)` with an `ON DELETE CASCADE` foreign key to the revision — so
revision 2 carries its own seven link rows with the eligibility each row holds NOW: six
`ELIGIBLE_SCORING`, one `ELIGIBLE_CONTEXT`. The current docker packet holds 14 rows; the
seven others (six witnessed convergent claims from Mission 1.43 and the unaccepted-answer
count from 1.32, all created after revision 1) are recorded as
`REQUIRES_NEW_SEMANTIC_JUDGEMENT_BEFORE_INCLUSION` and **not linked**. Relevance to the
hypothesis is a synthesis judgement this reconciliation does not make.

**One new sentence.** *6 of 7 supporting Evidence rows carry a reviewed reliability (0.65),
resolved late from their acquisition lineage and bound to the assessment that produced it
(ADR-026, Mission 1.77); 1 remains NON_SCORABLE with no applicable assessment
(stack-exchange). Scorable is not scored: REFERENCE_PROFILE_V1 is UNCALIBRATED, no Score
exists in this repository, none is persisted, and no ranking exists.* Computed from the
links, and the gate checks the counts against them. The independence, market-scope, Stack
Exchange and calendar limitations survive unchanged.

**Structured provenance**, in `procedure_version` because the revisions table has no reason
column and the pipe-separated convention is what revision 1 already used:
`opportunity-reliability-reconciliation@1.0.0 | reason=RELIABILITY_APPLICABILITY_RECONCILIATION
| prior_revision=efca07a9… | mission_finding=docs/data/wikimedia-measurement-scope-binding-v1.json
| resolver=sros_evidence_reliability.lineage | preparation=opportunity-preparation@2.0.0 |
preparation_record=docs/data/opportunity-preparation-v2.json | census=rows:58,scoring:48 |
linked=7`, `created_by mission-1.78`.

## Current pointer

There is no explicit current-revision column. The current revision is the highest `revision`
for the Opportunity, served by the canonical index `(workspace_id, opportunity_id, revision
DESC)`, and `research.opportunities` itself carries no revision pointer to move. Measured:
`ORDER BY revision DESC LIMIT 1` returns `8739e7ab` / 2; `WHERE revision = 1` returns
`efca07a9` exactly, byte-identical to its pre-reconciliation read. Both are pytest tests now,
written relationally so they pass on an empty CI database.

## Scoring readiness, per the contract and not per the wish

`SufficiencyResult.scoring_ready` is `scoring_eligible_rows >= 2`, a property of the PACKET.
The docker packet has 12 scoring rows, so it reads **true**; the revision-1 packet had 0, so
it read false. It authorises nothing: `REFERENCE_PROFILE_V1` is UNCALIBRATED, no scores table
exists and no score was computed or persisted. **Two defects surfaced by the first packet that
was ever scoring-ready**, both the recurring shape of a sentence written when its value could
only be one thing: the property's docstring read *always False while any row lacks a reviewed
reliability*, which described the corpus rather than the rule; and the sufficiency reason
string hard-coded *formable and not scoring-ready* beside a value that now reads true. The
docstring now says what the code has done since Mission 1.28, and the sentence follows the
property. No rule changed.

## History, kept

`opportunity-preparation-v1.json` hashes to `6aab7daf1f222dead72e03baebee43468a9b9d4381d9ee5fefbcb78dd9f09b31`
before and after, still says `mission 1.28` and 28 rows, and carries no pointer because a
pointer would have changed its bytes; the current record `opportunity-preparation-v2.json`
points back at it instead. Revision 1 is identical in every field after the reconciliation
and still carries its stale sentence, which is what makes revision 2 a correction by
supersession rather than a rewrite. The reconciliation script describes an existing
revision 2 instead of writing a third, and a second `--apply` is refused.

## Verification

- Probe: **47 deliberate violations, 47 caught, 0 escaped**, plus **4 of 4 positive
  controls**, six files restored byte for byte. **One control INVERTED**: a packet whose
  scorable rows fall below the contract's minimum is accepted as not scoring-ready, and a
  wholly scorable citation set is accepted when every row genuinely resolves, so the gate
  enforces the contract rather than this mission's numbers.
- **3539 bare-python tests**; the pytest suites green with **the database unchanged by the
  run across 29 tenant tables**; `ruff format --check`, `ruff check`, mypy over 198 files;
  contract and catalog `--check`; all **57** CI gates, one of them new.
- Canonical baseline: 325/325/33/44/45/58, INFERRED 1, thresholds 1, derivations 1, refusals
  0, assessments 4 (basis 12), independence groups 0, embeddings 0, scores ABSENT, sources 29,
  reviews 70 — identical before and after. Opportunities 1 → 1, revisions 1 → 2, links 7 → 14.

## What did not happen

No research API, web discovery, Gmail, email, provider contact, Globalping or target request;
no model call; no embedding. No RawRecord, NormalizedRecord, Signal, Claim, ClaimRevision,
Evidence, ReliabilityAssessment, threshold, derivation, refusal, source, review, independence
group or score. Revision 1 not updated, not deleted, not renamed, its timestamps untouched. No
new Opportunity. Q1, Globalping and V2 exactly where 1.76.7 left them.

## Remaining limitations

Six of seven cited rows are scorable and all seven sit in one provenance shape with
independence UNKNOWN, so aggregation over them would be the reliability pass-through and no
calibration is unlocked. The seventh row stays NON_SCORABLE unless the operator reviews the
Stack Exchange scope they declined. Seven rows of the current packet await a semantic
judgement before they can be cited. Scorable is not scored.

## Next

**Mission 1.79 — Post-Reconciliation Evidence Priority V1**: a bounded prioritization over the
current Opportunity state asking what the highest-information bounded move is now that six
linked rows are genuinely scorable, comparing at least (A) the Stack Exchange exact scope, (B)
missing commercial / buyer / WTP evidence, (C) a new decision-relevant dimension, (D) held but
unused evidence relevant to this Opportunity, including the seven uncited packet rows, and (E)
parked Q1 only if a deterministic construct has emerged from existing artifacts. Do not assume
A because it is the remaining non-scorable row, and do not assume B because it is attractive;
measure information gain. Not scoring, not calibration. **Mission 1.79 was not started.**

## The 53 answers

1. `f8c91e6`. 2. `sprint-1/mission-1.78`. 3. `0036_grant_use_profile_vocabulary`, measured.
4. 325/325/33/44/45/58, INFERRED 1, thresholds 1, derivations 1, refusals 0, assessments 4
(basis 12), groups 0, Opportunities 1, revisions 1 → 2, links 7 → 14, embeddings 0, scores
ABSENT, sources 29, profiles 2, profile UNCALIBRATED. 5. `06113a8b-a83d-423d-8046-18f87d7dbc01`.
6. `efca07a9-b283-473a-887b-a2ae82989bbe`. 7. *Every supporting Evidence row is
ELIGIBLE_CONTEXT, NON_SCORABLE and MISSING_RELIABILITY: no reviewed reliability applies, so
this hypothesis can contribute to no score.* 8. Written 2026-09-02 before the 0.65 and 0.6
assessments of 2026-09-03/04, and the path now resolves late: 6 of 7 rows bind. 9. The
hypothesis, actor, need, intervention, dimensions, uncertainties, and the independence,
market-scope, Stack Exchange and calendar limitations. 10. The reliability limitation, and the
reliability half of the reasoning summary's last sentence. 11. No, byte-identical. 12. No,
sha256 `6aab7daf…` before and after. 13. 58 rows, 48 scoring, 10 context, 10 packets, 3
formable. 14. The 14-row docker packet: 7 cited by revision 1, 7 requiring a semantic
judgement. 15. The same 7 as revision 1. 16. 6, Wikimedia detailed at 0.65 `e2419f13`. 17. 1,
Stack Exchange. 18. 6 RESOLVED via the lineage scope, 1 NO_APPLICABLE_ASSESSMENT. 19.
NO_APPLICABLE_ASSESSMENT, unchanged. 20. RESOLVED, 0.65, one assessment. 21. AUDIENCE_OR_USAGE,
PROBLEM_OR_NEED, TREND_OR_CHANGE. 22. forum, knowledge. 23. UNKNOWN on 7 of 7, 0 groups.
24. Yes. 25. Not applicable. 26. No. 27. Yes. 28. `8739e7ab-940b-408c-a5e8-7f6675d1597c`.
29. 2. 30. `RELIABILITY_APPLICABILITY_RECONCILIATION`, in `procedure_version` with the prior
revision id, the 1.77 finding, the resolver, the preparation record and the census. 31.
Revision-specific: unique per (revision, evidence), cascading from the revision. 32. +7.
33. Highest `revision` per Opportunity, by the canonical index; no pointer column. 34. Yes,
`8739e7ab` / 2. 35. Yes, `efca07a9`, identical. 36. false (0 scoring rows). 37. true per the
packet contract (12 ≥ 2). 38. `scoring_ready = scoring_eligible_rows >= 2`, a packet property
that authorises nothing; the profile is UNCALIBRATED and no score exists. 39. None. 40. None
run; the 1.77 diagnostic already established pass-through identity and it was not needed to
verify a limitation. 41. No, 4 → 4. 42. No, 0 → 0. 43. No; only revisions and links moved.
44. CLASS_SELECTED, construct false, run false, before and after. 45. 12/0/0
COUNTERPART_RESOLVED, before and after. 46. 0. 47. 0. 48. 0. 49. 47 caught, 0 escaped, 4 of 4
controls. 50. 3539 bare-python, pytest suites green with the database unchanged, ruff, mypy,
contracts, catalog, 57 gates. 51. `OPPORTUNITY_REVISION_2_RECONCILED_TO_CURRENT_SCORABILITY`.
52. One provenance shape, UNKNOWN independence, one non-scorable row, seven uncited rows,
nothing scored. 53. Mission 1.79, Post-Reconciliation Evidence Priority V1.
