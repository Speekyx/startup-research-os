# Mission 1.47 — Cross-Apparatus Proposition Convergence Feasibility V1

**Primary outcome: `FORMALLY_VALID_BUT_INFORMATIONALLY_WEAK`. No route selected.**

The one-sentence finding: **the only proposition both held apparatuses
independently entail is one so weak that it discards exactly what each apparatus
measures.** Strengthen it in any direction that carries information and only one
apparatus supports it. So the convergence that is available is not worth
building, and the convergence that would be worth building is not available.

Recorded beside it: `CROSS_APPARATUS_EVIDENCE_IS_COMPLEMENTARY_NOT_CORROBORATING`,
`CONVERGENCE_CONTRACT_ARCHITECTURE_GAP`, `PROVENANCE_INDEPENDENCE_NOT_ESTABLISHED`,
and `SINGLE_ROOT_CAUSE_BLOCKS_TWO_INDEPENDENT_GATES`.

---

## Setup

**1. Was main fully merged through Mission 1.46?** Yes. `main` is at `d1deb1f`,
which is *Merge pull request #89 from Speekyx/sprint-1/mission-1.46*.

**2. Exact commit baseline?** `d1deb1f0347de1e5ba18f9a97a31de67a0a9abdb`.

**3. Dedicated branch?** Yes, `sprint-1/mission-1.47`, branched from `main` at
that commit.

**4. Exact research counters before?** RawRecords **325**, NormalizedRecords
**325**, Signals **33**, Claims **43**, ClaimRevisions **44**, Evidence **57**,
ReliabilityAssessments **4**, reliability basis rows **12**, IndependenceGroups
**0**, Opportunities **1**, Opportunity revisions **1**, Opportunity evidence
links **7**, Embeddings **0**, registered sources **29**, `scoring.scores`
**absent**. All fifteen match the brief's stated expectation exactly.

**5. Exact aggregation counters before?** Scorable multi-Evidence Claims **8**,
max Evidence per Claim **4**, Claims with established independence **0**,
contradiction cases **0**, temporally sensitive Claims **0**,
`REFERENCE_PROFILE_V1` **UNCALIBRATED**, Evidence rows with a stored
`reliability` **0**.

---

## The apparatus inventory

**6. Apparatuses currently represented?** **Nine, over four sources.** An
apparatus is `(source_id, proposition_kind)` and not a source, because
`wikimedia-pageviews` and `ted-eu` each operate two over one corpus. Counting
sources would have reported four where nine exist, and would have merged two
reliability scopes the contract already holds apart.

| source | proposition kind | claims | evidence |
|---|---|---:|---:|
| gdelt | `source_reported_term_frequency_change` | 2 | 2 |
| gdelt | `source_reported_term_frequency_contrast` | 1 | 1 |
| stack-exchange | `community_site_published_questions_carrying_tag` | 1 | 1 |
| stack-exchange | `community_site_questions_without_accepted_answer` | 1 | 1 |
| ted-eu | `source_published_classification_value_contrast_witnessed` | 4 | 6 |
| ted-eu | `source_reported_procurement_value_contrast` | 6 | 6 |
| wikimedia-pageviews | `platform_counted_content_request_change` | 18 | 18 |
| wikimedia-pageviews | `platform_counted_content_request_change_witnessed` | 6 | 18 |
| world-bank | `source_reported_metric_period_change` | 4 | 4 |

Generated into `cross-apparatus-holdings-baseline-v1.json` by
`measure_cross_apparatus_holdings.py`, **before** any pair was considered.

**7. Exact operational measurement of each?**

- **Wikimedia** counts HTTP content requests under its own `Research:Page view`
  definition — a conjunction of status, host and header conditions with an
  enumerated exclusion list — partitioned into UTC day buckets, with the
  requester class assigned by ua-parser plus custom regex.
- **Stack Exchange** publishes questions composed by people, carrying tags
  assigned by askers and community curators from the site's own vocabulary.
- **TED** publishes eForms notice fields, principally BT-161 award totals.
- **GDELT** publishes lexical n-gram frequency over a news corpus.
- **World Bank** publishes annual indicator series values.

**8. Subject-overlap matrix?** Measured across all nine, via the reviewed
canonical subject registry under exact equality:

| subject | wikimedia Evidence | stack-exchange Evidence | cross-apparatus |
|---|---:|---:|---|
| `docker` | 12 | 2 | **YES** |
| `kubernetes` | 12 | 0 | no |
| `podman` | 12 | 0 | no |

GDELT (`climate`, `weather`), TED (CPV divisions 90 and 92) and World Bank
(`SP.POP.TOTL` over DEU and FRA) share no subject with anything, including each
other.

**9. Time-overlap matrix?** Wikimedia detailed holds whole UTC day buckets
`2024-03-01 .. 2024-03-07`. Wikimedia witnessed holds **no period at all** —
`period_label`, `period_label_from` and `period_label_to` are all null, so it is
an unbounded existential. Stack Exchange holds `2024-03-01T08:06:03Z ..
2024-03-05T04:17:20Z` (tag) and `.. 04:14:54Z` (unaccepted). TED and World Bank
overlap nothing.

**10. Which candidate pairs reached serious review?** Exactly one:
**wikimedia-pageviews + stack-exchange over `docker`**. No other pair shares a
subject, so no other pair had anything to review.

**11. Was Docker actually the only cross-apparatus shared subject?** **Yes, and
it was measured rather than assumed.** The brief forbade pre-selecting the pair,
so the overlap was computed first. The registry had already recorded why the
other two fail, in Mission 1.30 and not for this mission: kubernetes is mapped
*"for completeness of the registry; NO Evidence reaches this identifier today,
because the questions this deployment holds under it arrived through a
`tagged=docker` query and are a biased subset rather than a count"*, and podman
because *"this deployment holds no questions carrying it"*.

**12. Exact subject identity mapping?**
`wikimedia-pageviews:content:en.wikipedia.org|Docker_(software)` and
`stack-exchange:community-tag:stackoverflow|docker`, both to canonical subject
`docker`, by exact equality of rendered identifier keys. No distance, no token
overlap, no stem, no synonym table, no embedding, no model.

---

## Time

**13. Exact period alignment?** **The windows overlap and are NOT aligned.**
Stack Exchange begins 8h06m into 2024-03-01 and ends 4h17m into 2024-03-05;
Wikimedia holds whole UTC days. Aligning them would need sub-daily Wikimedia
counts and the finest grain held is a day, so **no exactly-aligned bounded
period exists for any quantitative comparison.** Both windows are contained in
March 2024, and containment is weaker than alignment.

**14. Any deterministic temporary aggregation needed?** **No.** An existential
over a containing period is entailed by a single qualifying observation inside
it, so no sum or monthly aggregate is required and §10's permission is never
invoked.

**15. Was completeness sufficient for it?** **No, and this is reported even
though the aggregation was not needed** — reporting only *not needed* would
leave a reader believing the aggregate was available and merely unused. §10
permits summing held daily counts to an exact March 2024 window only *"if the
complete required daily observations are actually held"*. This deployment holds
**7 of the 31 days**. No monthly aggregate was manufactured.

---

## The propositions

**16. Candidate proposition A?** `P-A1`:

> At least one public platform recorded, during March 2024, an event of a defined
> class that it attributes to the subject `docker`.

The event class has exactly one definition under which both apparatuses qualify,
and it is a **disjunction**: a content request counted under Wikimedia's own
pageview definition for `Docker_(software)` under requester class `user`, **or** a
question published on `stackoverflow` carrying the site's own tag `docker`.

**17. Evidence A alone supports full proposition?** **YES.**

**18. Evidence B alone supports full proposition?** **YES.**

**19. Does proposition require both jointly?** **No** — for `P-A1`. That is what
makes it formally valid, and §8's conjunction is satisfied: A alone YES, B alone
YES, jointly NO, latent NO.

**20. Is that complementarity rather than corroboration?** For `P-A1`
specifically, **no** — both bear on one proposition. But it holds only at the
existential floor. One step above it (`P-A2`, "activity was higher in one
sub-period than another") the two split into `AUDIENCE_OR_USAGE` and
`PROBLEM_OR_NEED` and become complementary, and the strengthened form is refused
as `SHARED_SUBJECT_NOT_SAME_PROPOSITION`. **The gate passes only where the
proposition has already discarded the distinction.**

Three other candidates were tested and refused:

| candidate | A alone | B alone | both jointly | latent | verdict |
|---|---|---|---|---|---|
| `P-A1` | YES | YES | NO | NO | `FORMALLY_VALID_BUT_INFORMATIONALLY_WEAK` |
| `P-A2` | NO | NO | YES | NO | `SHARED_SUBJECT_NOT_SAME_PROPOSITION` |
| `P-B1` | NO | NO | YES | NO | `JOINT_CONJUNCTION_NOT_CORROBORATION` |
| `P-C1` | NO | NO | NO | YES | `CROSS_APPARATUS_CONVERGENCE_REQUIRES_INFERRED_BRIDGE` |

**21. Does proposition contain a latent construct?** `P-A1`: **no.** Each side is
a directly observed publication or counting event. `P-C1` ("Developers showed
interest in Docker") does, is recorded **in order to be refused**, and is marked
`NOT_OBSERVED`. No inference bridge was implemented or proposed.

**22. Any human/person promotion?** **None.** `user` is Wikimedia's own class
name for traffic not identified as automated by ua-parser plus custom regex, and
it does not mean human, person, reader or customer. A Stack Exchange question is
not one unique person: author identity was never acquired, so distinct askers
cannot be counted. Tests scan candidate statements offered as OBSERVED for
"people viewed", "users experienced", "developers" and "customers".

**23. Any demand/adoption/popularity/pain promotion?** **None.** Scanned in the
assertion position only, because a candidate recorded in order to be refused may
name the construct it is refused for — and a scan that could not tell those apart
would forbid recording the refusal. A companion test asserts `P-C1` really does
contain such a term, so the first test cannot pass vacuously.

**24. Any source attribution removed?** **No — and the interesting answer is that
it was RELOCATED.** `P-A1`'s subject is genuinely source-independent: *"at least
one public platform"* names no publisher. Its **predicate** is not, because the
only definition of the qualifying event class enumerates the two publishers' own
mechanisms. So attribution moves from the subject of the sentence into the
definition of its predicate, where it is harder to see. **A proposition that
looks source-independent and is not is worse than one that is openly
attributed.**

---

## The contract

**25. Is a source-independent OBSERVED convergence contract semantically valid?**
Semantically, for `P-A1`, yes in the limited sense above. Architecturally, no.

**26. Exact candidate identity fields?** `canonical_subject_id`,
`event_class_definition_id`, `period_bound`, `claim_type`.

**27. Exact witness fields?** `source_id`, `resource_id`,
`source_native_subject_id`, `source_platform`, `period_label_from`,
`period_label_to`, `audience_class`.

**28. Are they complete/disjoint?** **Disjoint yes, complete NO — and the
incompleteness is the finding.** `audience_class` is REQUIRED on the
`content_request_count` kind precisely so that one item over one period cannot
carry two different counts under one name (Mission 1.19). It has no counterpart
on the Stack Exchange side, so it can only be a witness fact here — which means
the identity set cannot say which requester class the proposition is about, while
the Wikimedia apparatus cannot state a count without one. **A fact load-bearing
for one witness and absent for the other cannot be demoted to witness without the
proposition losing the ability to say what it is about.** §19 rejects it.

**29. Current convergence contract capable?**
**`CAN_CURRENT_CONVERGENCE_CONTRACT_EXPRESS_CROSS_APPARATUS_PROPOSITION` — NO**,
on two independent structural refusals, proved through the real constructor
rather than asserted:

- `PropositionConvergenceContract.__post_init__` raises unless `source_id` is in
  `identity_fields` — *"`source_id` is always identity for an OBSERVED claim.
  Attribution is part of the proposition."*
- `SourceBoundary` has exactly one member, `SAME_SOURCE_AND_RESOURCE`, and its
  docstring says the absence is deliberate: *"A cross-source value is
  deliberately absent rather than present-and-unused. An enum member nobody may
  pass is an invitation."*

Nothing was implemented, no enum member added, no guard relaxed.

**30. Observation-category compatibility?** All 57 Evidence rows in the corpus
carry `observation_category = UNCATEGORISED`, including all 14 Docker rows, and
all 57 carry `independence_state = UNKNOWN`. So **no existing category was
coerced and no new one invented** — the field that would have been coerced
carries no distinction to coerce. The complementarity lives in the Opportunity
engine's signal-type-to-dimension map, not on the Evidence row.

---

## Independence

**31. Apparatus A provenance?** HTTP requests arriving at Wikimedia servers,
counted under the operator's own documented pageview definition, classified
heuristically by ua-parser plus custom regex, delivered by the first-party
Analytics API.

**32. Apparatus B provenance?** Questions composed and published by people on
stackoverflow.com, tagged from the site's own vocabulary by askers and curators,
delivered by the first-party Stack Exchange API.

**33. Shared upstream?** **None documented, and none plausible.** No shared event
feed, no republished values, no cross-import, no common measurement producer.

**34. Independence state justified?** **`UNKNOWN`, and deliberately not
`KNOWN_INDEPENDENT`.** §13 permits the latter only where documentary evidence
establishes genuinely distinct measurement lineages, and forbids converting *"no
dependency found"* into independence. This deployment holds first-party
documentation of Wikimedia's lineage and **none** for Stack Exchange. **One
lineage documented and one not is not a documented distinction between two.**

**This is materially different from Mission 1.46 and the difference decides what
a future mission may attempt.** There, independence was **refuted** by a
documented common upstream — FRED republishes the World Bank series by its own
declaration — which closed the direction permanently. Here nothing suggests a
shared upstream; what is missing is affirmative documentation of one side. **An
unknown can be resolved by a retrievable document. A documented common producer
cannot.**

**35. First-party basis?** Wikimedia's `Research:Page view` definition, held
since Mission 1.19. For Stack Exchange: **nothing, and no request was made.** Its
publisher documentation is unreachable because the site's robots policy blocks
this environment's fetcher (recorded in Mission 1.36's packet). No retry, header
variation, mirror, cached copy or third-party summary may stand in for a
first-party document, and none was attempted.

---

## Reliability

**36. Reliability scope A?** `wikimedia-pageviews | platform_counted_content_request_change`
resolves **RESOLVED**, `0.65`, `HUMAN_REVIEW`. The witnessed scope resolves
**RESOLVED**, `0.6`, `HUMAN_REVIEW`.

**37. Reliability scope B?** Both Stack Exchange scopes resolve
**`NO_APPLICABLE_ASSESSMENT`**.

**38. Would new proposition require new reliability reviews?** **Yes, on both
sides, and this is where the mission's two failures turn out to be one.** A
cross-apparatus proposition carries a new `proposition_kind`, so it is a new
five-part scope; neither `0.65` nor `0.6` transfers, and no value is inherited by
proposition similarity.

Worse: **the Stack Exchange side needs exactly the judgement the operator has
already declined.** In Mission 1.36.1 the operator answered **NO** on both Stack
Exchange scopes, recorded as prose rather than as a value, because the available
documentation is insufficient — **the same robots-blocked documentation that
leaves independence `UNKNOWN` here.** So gate 6 and reliability readiness fail
for one cause, and it is a cause a mission cannot clear, because it is a
publisher's access policy and bypassing it is out of bounds.

---

## Complementarity

**39. Complementary Opportunity dimensions?** Wikimedia maps to
`AUDIENCE_OR_USAGE` and `TREND_OR_CHANGE`; Stack Exchange maps to
`PROBLEM_OR_NEED`. **Overlap: none.**

**The codebase recorded this before the mission asked.** The Opportunity engine's
own mapping rationale for `community_question_volume` says `PROBLEM_OR_NEED` is
*"a genuinely different question from the one `AUDIENCE_OR_USAGE` answers: that
one says something attended to a subject, this one says somebody said they were
stuck on it, **and neither implies the other**."* Written in Mission 1.30, not
for this mission.

**40. Would putting these Evidence on one Claim be false corroboration?** **For
any proposition that carries information, yes.** The tempting sentence — *people
are reading about Docker and asking about Docker, so two independent lines of
evidence agree* — is `P-B1`, a conjunction, and neither witness alone entails it.
The grouping machinery would happily have made two groups out of it: a test
demonstrates that `group_by_independence` groups by provenance and has never
heard of the Claim, so it **cannot** refuse a conjunction. The refusal has to
happen upstream in the proposition semantics, which is exactly why §12 orders the
gates that way.

---

## Decision

**41. Any formally valid but weak proposition?** **Yes — `P-A1`, and it is the
primary outcome.** `FORMAL_CONVERGENCE_VALIDITY` is VALID;
`PROPOSITION_INFORMATION_VALUE` is NEAR_TAUTOLOGICAL. It says that two platforms
published something about Docker in a month chosen because this corpus holds
Docker data.

**42. Calibration information value?** `STRUCTURALLY_IDENTIFYING` **YES** — two
`KNOWN_INDEPENDENT` items form two groups and saturation would exceed
`max(g_A, g_B)`, the first case where the full aggregator differs from B-2.
`SEMANTICALLY_USEFUL` **NO** — a calibration case asks a reviewer which of two
evidence sets is better supported, and asking that about a near-tautology
measures the reviewer's patience rather than the aggregator. **Both reported,
because reporting only the first would present a structural exercise as an
epistemic gain.**

**43. Any pair passing all §26 gates?** **No. Five pass, three fail.**

| # | gate | result |
|---:|---|---|
| 1 | exact subject identity | PASS |
| 2 | compatible period | PASS_BY_WEAKNESS |
| 3 | each source alone supports full proposition | PASS |
| 4 | no latent inference | PASS |
| 5 | no complementary-only structure | PASS_AT_THIS_STRENGTH_ONLY |
| 6 | established independence | **FAIL** |
| 7 | convergence contract representable | **FAIL** |
| 8 | not merely a misleading pseudo-market construct | **FAIL** |

**44. Selected route?** **NONE.** §26 forbids a least-bad fallback and §25
forbids a weighted score, so the slot is left empty rather than filled with the
closest candidate.

**45. If none, exact failure reason?** The proposition that passes semantics is
near-tautological (gate 8); independence is not established because one side's
measurement lineage is undocumented (gate 6); and the convergence contract cannot
represent a cross-apparatus proposition without losing a fact (gate 7).

**Why `FORMALLY_VALID_BUT_INFORMATIONALLY_WEAK` and not the other three.** The
architecture gap and the independence gap are both real and both **downstream**.
Reporting either as the primary outcome would imply that fixing it unlocks the
route — widen the contract, or retrieve one document — when neither would help:
the proposition would still be near-tautological. Mission 1.46 refused outcome B
for exactly this reason, and the rule it set governs here. And
`COMPLEMENTARY_NOT_CORROBORATING` as written says the apparatuses *"do not
independently support the same Claim"*, which is **false** of the one candidate
that passes semantics — they do; it is just not worth anything.

---

## What did not happen

**46. Research data requests?** **0.**

**47. Documentation requests?** **0** apparatus documentation requests and **0**
governance document requests. Every apparatus fact used was already held. Zero
requests of any kind were made in this mission.

**48. Model calls?** **0**, 0.00 USD.

**49. Embeddings?** **0.** No semantic classifier, no similarity, no vector
retrieval.

**50. Canonical data mutations?** **None.** All fifteen counters identical before
and after, verified against the live deployment. The pytest suite's own leak
check reports *"database unchanged by the run, across 26 tenant tables"* and
*"global tables unchanged by the run, across 17 tables"*.

**51. Independence groups persisted?** **0**, before and after.

**52. Calibration labels?** **0.**

**53. Parameter fitting?** **None.**

**54. `REFERENCE_PROFILE_V1` state?** **UNCALIBRATED.**

**55. Scores?** **None.** `scoring.scores` still does not exist.

**56. Opportunity changes?** **None.** 1 Opportunity, 1 revision, 7 evidence
links, exactly as before.

**57. Problem-Family status?** **PARKED.**

**58. Workspace-test issue encountered?** **No.** Inspected before the canonical
test pass, as §33 requires: exactly the two seeded workspaces (`dev` and
`dev-other`) and **0 orchestration-probe rows**. No cleanup was needed, none was
performed, and the clean uninterrupted run passed with both leak checks green. No
test was disabled, weakened, skipped or xfailed, and **no failure was masked by a
blind rerun**.

**59. Exact canonical counters after?** Identical to question 4: 325 / 325 / 33 /
43 / 44 / 57 / 4 / 12 / 0 / 1 / 1 / 7 / 0 / 29 / absent.

**60. Primary outcome?** **`FORMALLY_VALID_BUT_INFORMATIONALLY_WEAK`.**

---

## Next

**61. Recommended next mission?** **Not Mission 1.48 as §38 describes it**, and
Mission 1.48 was **not started**.

§38 is explicit for outcome D: do not implement the weak proposition merely to
make the aggregator produce a different number; look for a better proposition
family **or a contradiction-capable route**. That pointer leads somewhere this
mission's data can speak to.

**The structural observation worth carrying forward.** Mission 1.43 established
that only **established independence** or **contradiction** can make the full
aggregator differ from the B-2 pass-through baseline. This mission found that the
propositions easiest to converge across apparatuses are **existentials** — and an
existential is **monotone**: a counterexample does not falsify it, so an
existential can never produce a contradiction case. The propositions that **can**
be contradicted are point or universal claims, and those are exactly the ones
only one apparatus supports. **So the same property of this corpus blocks both
roads out of the B-2 identity at once.**

The recommended mission therefore asks what **type** of measurement apparatus
would be needed, rather than which held pair can be made to fit: one observing
the same phenomenon as an apparatus already held, with a **documented measurement
lineage**, capable of producing a **falsifiable point claim** rather than an
existential. That is the only shape that can yield either a second provenance
group or a contradiction.

Not recommended: adding sources at random, widening the convergence contract,
implementing `P-A1`, or acquiring more Wikimedia or Stack Exchange data. None of
them touches the finding.

---

## §34 — `DEPLOYMENT_LOCAL_HUMAN_CONFIRMATIONS_REQUIRE_MIGRATION_CHECKLIST`

Recorded, not repaired. TED's local review v3 acceptance is a
`HUMAN_CONFIRMATION` verification living in this deployment's database. It is
**not portable through git**: a clone does not carry it, and TED would be
INELIGIBLE under `local-private-research-v1` in a fresh deployment until a named
operator recorded it again. **No replay mechanism was created and none is
proposed** — `record_ted_operator_acceptance.py` still refuses against v3, and its
own guard says the acceptance has to be made again by a person rather than
replayed. A deployment or migration checklist is required whenever this system is
stood up elsewhere, and that is a future deployment concern rather than a Mission
1.47 repair.

---

## Artifacts

| file | what it is |
|---|---|
| `docs/data/cross-apparatus-holdings-baseline-v1.json` | §0 apparatus inventory, **generated from the live deployment before any pair was considered** |
| `infrastructure/scripts/measure_cross_apparatus_holdings.py` | measures it; reads only; `--check` is an operator gate, **deliberately not in CI** because it measures a deployment and CI starts empty (Mission 1.37) |
| `docs/data/cross-apparatus-convergence-feasibility-v1.json` | the authored feasibility record |
| `docs/data/cross-apparatus-convergence-feasibility-v1.md` | rendered from it |
| `infrastructure/scripts/render_cross_apparatus_convergence_feasibility.py` | renders and **validates**; wired into CI |
| `packages/evidence-aggregation/python/tests/test_cross_apparatus_convergence.py` | 77 unittest tests |

**The validator was probed rather than trusted.** Twelve deliberate violations
were fired at `validate()` and all twelve were caught: a selected route with no
passing gate, all eight gates forced to PASS under a non-feasible outcome, the
outcome forced to A while gates fail, an outcome outside the §36 vocabulary, a
latent construct in a candidate offered as OBSERVED, a moved research counter,
research data acquired, model calls, Problem-Family unparked, a truncated gate
list, a conjunction recorded as corroboration, and `all_eight` lying about the
gate results. An unreachable guard reads as protection while protecting nothing.

**Non-empty fixtures for all five shapes §35 names** —
`VALID_SAME_PROPOSITION_INDEPENDENT`, `COMPLEMENTARY_ONLY`,
`LATENT_INFERENCE_REQUIRED`, `JOINT_CONJUNCTION_NOT_CORROBORATION`,
`UNKNOWN_INDEPENDENCE` — so every branch executes. Missions 1.36.1, 1.42.1, 1.43
and 1.44 each shipped a branch no data had ever entered, and each was found by
real data rather than by a passing suite.

## Gates run

- `run_python_tests.py`: **1063 tests across 8 packages, OK** (77 new).
- `run_pytest_suites.py`: **245 passed across 9 packages**; database unchanged
  across 26 tenant tables; global tables unchanged across 17.
- `ruff check .` — all checks passed. `ruff format --check .` — 662 files
  formatted.
- All eight generated-document `--check` steps in sync, including the new one.
- `validate_source_registry` (29 sources, 45 evidence records, 0 warnings),
  `validate_signals`, `validate_claims`, `validate_normalization` — all passed.
