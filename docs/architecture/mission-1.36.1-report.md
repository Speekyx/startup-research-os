# Mission 1.36.1 — Docker Operator Reliability Decisions V1

**Outcome: `DOCKER_RELIABILITY_PARTIALLY_REVIEWED`** (§25 A).

The mission itself reached `OPERATOR_CONFIRMATION_REQUIRED` (§25 B) and stopped
there: the one assessment the operator's decisions authorise was written and
validated end to end, and **not persisted**, because the recording workflow
requires a confirmation typed by a person and §7 forbids bypassing the guard that
enforces it.

**The operator then confirmed at a terminal on 2026-09-03**, so this report
records outcome A with the real ids. Both states are kept: how the mission
stopped is the part worth preserving, and the answers below say which facts were
true at which point.

It is **`PARTIALLY`** and never `DOCKER_EVIDENCE_SCORING_ELIGIBILITY_READY`,
because two of the three reliability scopes in use are deliberately unreviewed.

---

## §0 — Drift check: NO DRIFT

Before anything else, the three scopes the operator decided about were re-derived
from the live database and compared to the Mission 1.36 packet.

| scope | rows | matches packet |
|---|---:|---|
| `stack-exchange` · `…published_questions_carrying_tag` | 1 | yes, all five fields |
| `stack-exchange` · `…questions_without_accepted_answer` | 1 | yes, all five fields |
| `wikimedia-pageviews` · `platform_counted_content_request_change` | 6 | yes, all five fields |

1 + 1 + 6 = 8, every Docker Evidence row in exactly one scope. Had a single field
moved, the operator's decisions would have been about something else and the
mission would have stopped at `RELIABILITY_SCOPE_DRIFT_DETECTED`.

---

## §26 — The thirty questions

**1. Were Scope 1 and Scope 2 kept unassessed?**
Yes. No `ReliabilityAssessment` exists for either, and none was created. The
resolver returns `NO_APPLICABLE_ASSESSMENT` for both, which is the designed
behaviour.

**2. Was their NO decision recorded without creating a numeric assessment?**
Yes, in [docker-reliability-operator-decisions-v1.md](../data/docker-reliability-operator-decisions-v1.md)
§1, as prose. The document states in its own words that the decision means **no
human reliability judgement exists** and does **not** mean `reliability = 0`,
`reliability = 0.5`, low reliability, or an unreliable source. **A refusal
recorded as data would be a value**, and the next reader would use it as one.

**3. Was Scope 3 unchanged from Mission 1.36?**
Yes, all five fields byte-identical:

```text
source_id         wikimedia-pageviews
resource_id       metrics/pageviews/per-article/en.wikipedia.org
record_kind_id    content_request_count
claim_type        OBSERVED
proposition_kind  platform_counted_content_request_change
```

**4. Was reliability exactly 0.65?**
Yes. Not normalised, not rounded, not rescaled, and not relabelled: the
reliability contract defines no threshold vocabulary, so the value is not
*good*, *medium*, *high* or *65% confident* anywhere in this mission's output. A
test scans for those words.

**5. Was reviewer exactly `thibchm`?** Yes.

**6. Was origin `HUMAN_REVIEW`?** Yes, and it carries no
`calibration_dataset_ref` — the contract refuses one on this origin, and
`CALIBRATED_EMPIRICALLY` is what a calibration reference belongs to.

**7. Exact rationale persisted?**
**Yes, verbatim.** The operator's text, unedited, byte-identical in the review
object and in `epistemic.reliability_assessments`:

> The Wikimedia pageview measurement has documented first-party counting rules
> that explicitly define which requests are included and excluded, and automated
> traffic is classified using user-agent and custom-pattern detection. The
> measurement therefore has a documented methodology and a bounded meaning for
> the proposition that Wikimedia counted changes in requests to the Docker
> article.

**8. Exact limitation persisted?**
**Yes, verbatim**, and it is required rather than optional: a reliability with no
stated failure mode is a number nobody can argue with.

> Automated traffic detection is heuristic, and the retrieved Wikimedia
> documentation does not establish a complete revision/backfill policy for
> historical pageview values. Historical measurements may therefore be affected
> by classification changes or later revisions.

**9. Which documentary basis rows were persisted?**
**Two**, reused verbatim from the Mission 1.36 packet with no replacement
documentation retrieved. Basis rows went 4 to 6.

| basis type | document | section | retrieved |
|---|---|---|---|
| `MEASUREMENT_METHODOLOGY` | Research:Page view | Definition; Tagging | 2026-09-03 |
| `KNOWN_LIMITATION` | Data Platform / Data Lake / Traffic / Pageviews | Events and known problems since 2015-05-01 | 2026-09-03 |

**This mission had to repair them before they could be used, and that is a real
defect Mission 1.36 shipped.** Its `candidate_basis_rows` carried `basis_type`
values — `OFFICIAL_METHODOLOGY`, `FIRST_PARTY_RESPONSE_AT_COLLECTION`,
`FIRST_PARTY_MODEL_SEMANTICS` — that are **not members of
`ReliabilityBasisType`**. The rows a packet prepares exist to record an
assessment, and these could not have recorded one: `ReliabilityBasisType(...)`
raises on all three. Nothing caught it because the packet is a JSON document and
the enum lives in the contracts package.

The repair maps each to a real member, following the one precedent in the
repository (the TED assessment): a document defining **how** a measurement is
computed is `MEASUREMENT_METHODOLOGY`, a document recording **what can go wrong**
is `KNOWN_LIMITATION`, and a record of how a corpus was assembled is
`CORPUS_CONSTRUCTION_METHOD`. And `authoritative_documents[].basis_type` was
renamed `document_kind`, because that field is a narrative list of what was read
— **including a document that was NOT read** — and reusing the contract's field
name for it is what made an invalid value look valid.

**10. Was explicit human confirmation satisfied legitimately?**
**Yes — by the operator, and not by this mission.** The recording tool holds the
confirmation the contract depends on:

```python
CONFIRMATION = "record it"
...
except EOFError:
    return _fail(
        "no terminal to confirm on. A reliability assessment is a human decision "
        "and this is not a step a pipeline runs"
    )
```

Run with `--apply` in this environment, it printed exactly that refusal and wrote
nothing. **The guard is the only thing that makes `reviewed_by` mean anything**:
a run that piped `record it` into it would produce a row attributed to a person
who did not type it, which is the failure the whole reliability contract is built
to prevent. §7 forbids the bypass by name, so **the mission stopped there** and
handed the operator the command.

**It was then satisfied the only way it can be**: the operator ran it at a
terminal and typed `record it`. So the answer is yes, legitimately, and by a
person rather than by this mission.

**11. Exact new assessment id/version?**
`e2419f13-c031-44d5-837c-c56a867baf34`, **version 1**. A new scope line, **not a
supersession of TED's** — `3de2af10-…` is still version 1 with `superseded_at`
NULL, because a different scope is a different question and not a revision of
somebody else's answer.

**12. Did all six Wikimedia Evidence rows resolve it?**
**Yes, all six**, each binding that one assessment id at version 1, origin
`HUMAN_REVIEW`, reviewer `thibchm`. One scope, one assessment, six bindings: six
different ids would have meant the scope key was not doing its job.

**13. Which exact Evidence ids?**

| scope | Evidence ids |
|---|---|
| Wikimedia (6) | `13a5eadb-977d-4de0-9c35-d0ff53442074`, `1b93db71-eaed-45c5-a2fa-9e4edea7bc49`, `487f62c6-2fcf-4790-9773-6e99214d0003`, `516182ff-0122-4d13-9d8a-92bb38065a75`, `6cf92ad6-77ed-4126-b356-41e65856430b`, `f1e0b7a4-d570-429a-91a4-fadff84cdce1` |
| Stack Exchange scope 1 (1) | `16a8c39c-d72a-4252-9c67-7be2165e9cae` |
| Stack Exchange scope 2 (1) | `17735944-da2f-4469-837f-8f3fe71922aa` |

**14. Did any Stack Exchange Evidence resolve it?**
No, and it must not: the Wikimedia assessment's scope differs from both Stack
Exchange scopes on `source_id`, `resource_id`, `record_kind_id` and
`proposition_kind` — four of five fields.

**15. Did TED resolve it?**
No. The §10 negative checks ran the **real** resolver, offering every current
assessment to each of the three Docker scopes: **6 checks, 0 leaks** — three
before the confirmation and six after, because a second assessment doubles the
ways one could leak. This is the
check worth running rather than assuming, because the TED assessment **shares
`claim_type: OBSERVED` with all three Docker scopes** — every Evidence row in
this repository is OBSERVED, so that field discriminates nothing, and it is
exactly where a leak would begin if matching were ever partial, nearest or fuzzy.
It is not: all five fields must match.

**16. How many Docker rows resolve reliability now?** **6 of 8.**

**17. How many remain `MISSING_RELIABILITY`?** **2 of 8** — the Stack Exchange
pair, still `NON_SCORABLE`, which is the operator's decision working rather than
a gap.

**18. How many are scoring-eligible?** **6**, for a diagnostic run over an
`UNCALIBRATED` profile. **Scoring-eligible is not scoreable in production**: D-03
is not resolved and `services/scoring` stays blocked.

**19. Were Evidence rows themselves modified?**
No. This mission issued no `UPDATE` against `scoring.evidence`. Reliability is
resolved late by design (ADR-026); the row is never rewritten when an assessment
appears.

**20. Did any reliability column become non-NULL?**
**No, and this is the answer worth reading twice.** `scoring.evidence.reliability`
is `NULL` on all 28 rows, Docker's 8 included, **after** the confirmation as
before it. Six rows resolve `0.65` and not one of them stores it: the resolver
produces the number and the binding at read time (ADR-026 Decision 2), so a score
can name the assessment and version it used, and a stale copy cannot outlive the
assessment it came from.

**21. Did a diagnostic aggregation run?**
**Not during the mission, and yes afterwards.** §15 makes it conditional on at
least one row becoming scorable; while nothing was persisted none was, and
running it over eight `NON_SCORABLE` rows would have produced a number computed
from nothing. After the confirmation the precondition is met, so it ran:
`allow_uncalibrated=True`, the real `aggregate()`, one JSON artifact and **no
database row**.

**22. Exact diagnostic results?**
[docker-diagnostic-aggregation-v1.json](../data/docker-diagnostic-aggregation-v1.json).
Every entry carries **UNCALIBRATED / DIAGNOSTIC ONLY / NOT AN OPPORTUNITY
SCORE**.

**Eight Evidence rows sit on eight distinct Claims**, so these are eight
single-record aggregations rather than one eight-record aggregation. Reliability
resolving does not turn six observations of one Wikipedia article into an
aggregation.

| | six Wikimedia claims | two Stack Exchange claims |
|---|---|---|
| aggregation status | `COMPLETE` | `UNAVAILABLE` |
| evidence considered / scorable | 1 / 1 | 1 / 0 |
| `q` | `0.650` | none |
| limiting component | **`reliability`** | none; `MISSING_RELIABILITY` |
| support strength | 0.65 | 0.0 |
| contradiction strength | 0.0 | 0.0 |
| supported mass | 0.65 | 0.0 |
| conflict mass | 0.0 | 0.0 |
| uncertainty mass | 0.35 | **1.0** |
| Evidence level | **1**, Weak Signal | **0** |
| binding | `e2419f13-…` v1 `HUMAN_REVIEW` | none |
| profile | `reference-v1@1.0.0` `UNCALIBRATED` | same |

**`reliability` is the limiting component on all six**, because
`q = min(components)` and relevance, directness, extraction confidence and
freshness are all `1.0`. The score is a restatement of one human judgement, not a
corroboration of it — the same shape Mission 1.15.13 found for TED at a different
number.

**Level stayed 1, and reliability could not have raised it.** The blocked reasons
name the two gates: *Repeated Signal needs 2 supporting groups of established
independence, found 0*, and Market Evidence needs a record categorised
`MARKET_ACTIVITY`. Neither is something a reliability value touches.

**23. Was the profile still `UNCALIBRATED`?**
Yes. `REFERENCE_PROFILE_V1` is unchanged. **Reliability review is not
calibration** and does not become it by accumulating assessments: a reviewed
value says how dependable a measurement is, and calibration is fitting the
aggregation's own constants against outcome data that does not exist here.

**24. Was an Opportunity Score created?**
No. `scoring.scores` **does not exist as a table**, which is a stronger fact than
zero rows.

**25. Was ranking performed?** No. Nothing in this mission orders, weights or
compares Opportunities.

**26. Did independence change?**
No. `UNKNOWN` on all 8 Docker rows, `scoring.evidence_independence_groups` holds
0 rows, and none was created. Independence continues to cap evidence levels for
reasons reliability cannot touch — **a reviewed 0.65 would not make six
observations of one Wikipedia article six independent findings.**

**27. Is Problem-Family still PARKED?** Yes. No classifier ran, no candidate pair
was generated, no `SAME_PROBLEM_FAMILY` judgement was made.

**28. D-03 blocker states?**

| # | blocker | state |
|---|---|---|
| 1 | reliability definition / authority | **RESOLVED** |
| 2 | reviewed reliability for scopes actually used | **PARTIAL** |
| 3 | `CALIBRATED` aggregation profile | **OPEN** |
| 4 | temporal half-life | **OPEN** globally; not required by these claims, which are all `EVERGREEN` |
| 5 | fitted Evidence-level thresholds | **OPEN** |

**Blocker 2 became PARTIAL when the operator confirmed, and not before.** While
nothing was persisted it was **OPEN**: zero of the three scopes in use had a
reviewed value, and reporting PARTIAL then would have been reporting a future.
`PARTIAL` is now exactly right — Wikimedia reviewed, both Stack Exchange scopes
unknown — which is the shape §19 anticipated.

**D-03 is not resolved**, and one reviewed value moves none of the other four
blockers. The diagnostic aggregation demonstrates that precisely: it runs, and it
runs `UNCALIBRATED`.

**29. Canonical counters before/after?**
All three columns are **measured against the live database**, not predicted. The
middle one is the state the mission itself left, where §24's instruction applied
— *do not force counters if persistence is blocked by the confirmation
mechanism* — and the right-hand one is the state after the operator confirmed.

| counter | before | mission end | after confirmation | §24 expected |
|---|---:|---:|---:|---:|
| RawRecords | 148 | 148 | **148** | 148 |
| NormalizedRecords | 148 | 148 | **148** | 148 |
| Signals | 28 | 28 | **28** | 28 |
| Claims | 28 | 28 | **28** | 28 |
| ClaimRevisions | 29 | 29 | **29** | 29 |
| Evidence | 28 | 28 | **28** | 28 |
| Evidence with non-NULL reliability | 0 | 0 | **0** | 0 |
| EvidenceIndependenceGroups | 0 | 0 | **0** | 0 |
| ReliabilityAssessments | 1 | 1 | **2** | 2 |
| Reliability basis rows | 4 | 4 | **6** | 4 + 2 |
| Opportunities | 1 | 1 | **1** | 1 |
| OpportunityHypothesisRevisions | 1 | 1 | **1** | 1 |
| Opportunity evidence links | 7 | 7 | **7** | 7 |
| Embeddings | 0 | 0 | **0** (`nlp.embedding_provenance` empty) | 0 |
| Scores | 0 | 0 | **0** (`scoring.scores` absent) | 0 |
| Registered sources | 29 | 29 | **29** | 29 |
| Scope relations | 0 | 0 | **0** | 0 |

**Two counters moved and fifteen did not**, which is what a reliability review is
supposed to look like. Nothing was acquired, no Signal or Claim or Evidence was
created, no Opportunity revision appeared, and no score exists. The one row that
would tempt a reader is *Evidence with non-NULL reliability*, which stays **0**
after the confirmation for the reason question 20 gives.

**30. Recommended next mission?**
**Mission 1.37 — Evidence Aggregation Calibration Strategy V1**, and its premises
now hold. §27 lists them: a functioning reliability framework, one TED
`HUMAN_REVIEW` assessment, one Wikimedia `HUMAN_REVIEW` assessment, real scorable
Evidence, and an explicitly uncalibrated aggregation profile. All five are true
as of the confirmation, and the last one is the mission's subject.

**The diagnostic above is the argument for 1.37 rather than a substitute for it.**
Six claims score `0.650` with `reliability` as the limiting component, so the
number is a restatement of one person's judgement passed through equations whose
constants were never fitted. 1.37 must determine how calibration can rest on
reference or outcome data rather than on guessed constants.

After that, **select a second pilot subject from a different domain.** Docker
must not become the only long-term benchmark, and Mission 1.35 already found the
specific reason it is a poor one: it sits in no published classification.

§27's standing instruction applies whatever happens: **do not spend another
mission trying to force Stack Exchange reliability.** The operator has decided
the available documentation is insufficient, and the publisher's methodology
pages are unreachable from this environment because the site's robots policy
blocks the crawler. The route that remains open is the one Mission 1.18 used —
the operator supplying the documents.

---

## §29 — What the operator ran

The review file is [docs/data/docker-wikimedia-reliability-review-v1.json](../data/docker-wikimedia-reliability-review-v1.json).

**The first version of this section printed a command that does not run, and the
operator hit it before this was corrected.** Two reasons, and the first hides the second: `DATABASE_URL`
lives in `infrastructure/compose/.env` rather than in the shell, so the tool
refuses with *DATABASE_URL is not set. This writes to a deployment, not to the
tree* — and behind that refusal, a bare `python` cannot import `psycopg`, which
the script imports only after the `DATABASE_URL` check. `sros_contracts` resolves
through the script's own `sys.path` insert, so the missing dependency is the one
that is actually installed rather than vendored. Run it through `uv`.

PowerShell, in one tab:

```powershell
$env:DATABASE_URL = ((Select-String -Path infrastructure\compose\.env -Pattern '^DATABASE_URL=' | Select-Object -First 1).Line -replace '^DATABASE_URL=', '')
```

```powershell
uv run --package sros-nlp python infrastructure/scripts/record_reliability_assessment.py --review-file docs/data/docker-wikimedia-reliability-review-v1.json --apply
```

It prints the assessment and asks for a confirmation. **Type `record it`.**
Anything else aborts and writes nothing.

Then, to see what changed:

```powershell
uv run --package sros-nlp python infrastructure/scripts/report_docker_reliability_resolution.py
```

Expected afterwards: six Wikimedia rows `RESOLVED` at `0.65` against one new
assessment, two Stack Exchange rows still `NO_APPLICABLE_ASSESSMENT`,
`scoring.evidence.reliability` still `NULL` on every row, and the negative checks
still reporting no leak. **That is exactly what it reported.**

**A third defect surfaced there, and only because a row finally resolved.**
`report_docker_reliability_resolution.py` read `binding.assessment_version`,
which is not a field — the attribute is `version`. Every binding had been `None`
while nothing resolved, so the branch was unreachable and the wrong name sat
there looking fine. **The same shape as the basis-type defect above**: code that
could not have worked, unnoticed because the path was never taken. Fixed, and the
report now also carries the binding's origin and reviewer.

---

## What this mission did not do

- **No number was chosen, suggested, bounded or normalised by software.** `0.65`
  arrived from the operator and was carried unchanged. §21's expectation holds:
  **0 model calls, 0.00 USD.** No model was asked to evaluate, explain, sanity
  check or justify the value.
- **No packet average.** There is no mean reliability, no overall Docker
  reliability, no *Docker confidence* and no *Docker 65%*. `0.65` belongs to one
  scope; the other two remain unknown, and **unknown is not a low number**.
- **No acquisition** (§22). No RawRecord, no NormalizedRecord, no Wikimedia
  refresh, no Stack Exchange refresh, no Docker taxonomy search.
- **No governance change** (§20). No source review touched, no
  `external_model_transmission` decision, no profile change. Reliability is not
  governance.
- **No independence groups**, no scope relations, no Opportunity revision, no
  score, no ranking, no second Opportunity.

## A second finding, from checking rather than assuming

`docker-evidence-reliability-review-packet-v1.json` is **generated** from
`reliability_review_findings.json` and the live database, and **CI has no
`--check` step for it.** The repository has four such steps — the source catalog,
the review results, the signal coverage and the aggregation sensitivity doc — and
this packet is not among them.

It had already drifted. The basis-type repair edited the findings; the packet
kept the old shape until this mission regenerated it, and regenerating it broke a
Mission 1.36 test that read `authoritative_documents[].basis_type`. **The test
was right to break** and it is the best illustration of why the field was
renamed: it looks for a document marked `UNREACHABLE`, and a reliability basis is
by definition a document that **was** retrieved. A document nobody could read had
been carrying the contract's field name.

The test now reads `document_kind`, and the packet is verified reproducible: a
regeneration from the corrected findings produces a byte-identical file. **A
`--check` step for it belongs in CI** and is left for a mission that may change
CI, since §20 and the mission's scope do not cover it.

## Tests

[test_operator_reliability_decisions.py](../../packages/opportunity-engine/python/tests/test_operator_reliability_decisions.py)
— **38 tests** over §23's list plus §15, asserting **what is true**.

Its first version was written before the confirmation, so it asserted that
nothing resolved and that TED was the only assessment: correct then, and a test
claiming six rows resolve would have been asserting a future. **Exactly two
assertions were re-pointed** at the new present, and every other one is unchanged
— because everything else really did stay put, which is the finding rather than
an accident.

Four of them are worth naming.

- Every `basis_type` in the review file **and in the Mission 1.36 packet** is a
  real `ReliabilityBasisType` member. That is the first defect, now caught by the
  contract rather than by the next mission that tries to use those rows.
- The recording tool still refuses without a terminal: **a guard removed to make
  a pipeline pass is a guard that never was.**
- All six resolved rows bind **one** assessment id. Six ids would mean the scope
  key was not doing its job.
- The diagnostic aggregation carries **UNCALIBRATED / DIAGNOSTIC ONLY / NOT AN
  OPPORTUNITY SCORE** on every entry, persists nothing, and reports eight
  single-record aggregations rather than one eight-record one.
