# Mission 1.36.1 — Docker Operator Reliability Decisions V1

**Outcome: `OPERATOR_CONFIRMATION_REQUIRED`** (§25 B).

The operator's three decisions were carried faithfully. The one assessment they
authorise is written, validated end to end through the real recording workflow,
and **not persisted**, because that workflow requires a confirmation typed by a
person and §7 forbids bypassing the guard that enforces it.

**One command stands between this mission and outcome A**, and it is §29 below.

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
It is written verbatim into the review object and rendered verbatim by the
workflow's dry run. The operator's text, unedited:

> The Wikimedia pageview measurement has documented first-party counting rules
> that explicitly define which requests are included and excluded, and automated
> traffic is classified using user-agent and custom-pattern detection. The
> measurement therefore has a documented methodology and a bounded meaning for
> the proposition that Wikimedia counted changes in requests to the Docker
> article.

**Persisted to the database: no** — see question 10.

**8. Exact limitation persisted?**
Same status, same verbatim handling:

> Automated traffic detection is heuristic, and the retrieved Wikimedia
> documentation does not establish a complete revision/backfill policy for
> historical pageview values. Historical measurements may therefore be affected
> by classification changes or later revisions.

**9. Which documentary basis rows were persisted?**
Two are prepared, reused verbatim from the Mission 1.36 packet with no
replacement documentation retrieved. **Zero are persisted yet.**

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
**No, and that is the outcome.** The recording tool holds the confirmation the
contract depends on:

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
to prevent. §7 forbids the bypass by name, so the mission stops here and hands
the operator the command.

**11. Exact new assessment id/version?**
**None.** No id was allocated, because nothing was inserted. On confirmation the
tool will write `version 1` — a new scope line, not a supersession of TED's.

**12. Did all six Wikimedia Evidence rows resolve it?**
Not yet. All six return `NO_APPLICABLE_ASSESSMENT` today. The dry run confirms
the scope key they compute is the scope key the review declares, so the six are
what will resolve when the assessment exists.

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
No. The §10 negative checks ran the **real** resolver, offering the TED
assessment to each of the three Docker scopes: **3 checks, 0 leaks.** This is the
check worth running rather than assuming, because the TED assessment **shares
`claim_type: OBSERVED` with all three Docker scopes** — every Evidence row in
this repository is OBSERVED, so that field discriminates nothing, and it is
exactly where a leak would begin if matching were ever partial, nearest or fuzzy.
It is not: all five fields must match.

**16. How many Docker rows resolve reliability now?** **0 of 8.**

**17. How many remain `MISSING_RELIABILITY`?** **8 of 8**, every one
`NON_SCORABLE`.

**18. How many are scoring-eligible?** **0.**

**19. Were Evidence rows themselves modified?**
No. This mission issued no `UPDATE` against `scoring.evidence`. Reliability is
resolved late by design (ADR-026); the row is never rewritten when an assessment
appears.

**20. Did any reliability column become non-NULL?**
No. `scoring.evidence.reliability` is `NULL` on all 28 rows, Docker's 8 included,
and stays `NULL` after the operator confirms.

**21. Did a diagnostic aggregation run?**
**No, and skipping it was required rather than convenient.** §15 makes the
diagnostic conditional on at least one Evidence row becoming scorable. None did,
because no assessment was persisted. Running it anyway would have produced an
aggregation over eight `NON_SCORABLE` rows — a number computed from nothing, in
an artifact that would later be read as a result.

**22. Exact diagnostic results?** None, per question 21.

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
| 2 | reviewed reliability for scopes actually used | **OPEN** |
| 3 | `CALIBRATED` aggregation profile | **OPEN** |
| 4 | temporal half-life | **OPEN** globally; not required by these claims, which are all `EVERGREEN` |
| 5 | fitted Evidence-level thresholds | **OPEN** |

**Blocker 2 is OPEN, not PARTIAL, and the difference is the point.** §19
anticipated `PARTIAL` — Wikimedia reviewed, Stack Exchange unknown — and that
describes the state **after** the operator confirms. Nothing is persisted, so
zero of the three scopes in use has a reviewed value today. Reporting PARTIAL now
would be reporting a future.

**D-03 is not resolved**, and would not be resolved by the confirmation either.

**29. Canonical counters before/after?**
Verified against the live database after the refused `--apply`. **Every counter
is unchanged**, which §24 anticipates: *do not force counters if persistence is
blocked by the confirmation mechanism.*

| counter | before | after | expected after confirmation |
|---|---:|---:|---:|
| RawRecords | 148 | **148** | 148 |
| NormalizedRecords | 148 | **148** | 148 |
| Signals | 28 | **28** | 28 |
| Claims | 28 | **28** | 28 |
| ClaimRevisions | 29 | **29** | 29 |
| Evidence | 28 | **28** | 28 |
| Evidence with non-NULL reliability | 0 | **0** | 0 |
| EvidenceIndependenceGroups | 0 | **0** | 0 |
| ReliabilityAssessments | 1 | **1** | 2 |
| Reliability basis rows | 4 | **4** | 6 |
| Opportunities | 1 | **1** | 1 |
| OpportunityHypothesisRevisions | 1 | **1** | 1 |
| Opportunity evidence links | 7 | **7** | 7 |
| Embeddings | 0 | **0** (`nlp.embedding_provenance` empty) | 0 |
| Scores | 0 | **0** (`scoring.scores` absent) | 0 |
| Registered sources | 29 | **29** | 29 |
| Scope relations | 0 | **0** | 0 |

**30. Recommended next mission?**
**Not 1.37 yet.** §27 makes Mission 1.37 — Evidence Aggregation Calibration
Strategy V1 — the next mission, and its premises include *one Wikimedia
`HUMAN_REVIEW` assessment* and *real scorable Evidence*. Neither is true until
§29 below is executed. So:

1. The operator runs the confirmation command and confirms.
2. The resolution report is regenerated, and outcome A —
   `DOCKER_RELIABILITY_PARTIALLY_REVIEWED` — is recorded with the real ids.
3. **Then** Mission 1.37 begins, on premises that hold.

§27's standing instruction applies whatever happens: **do not spend another
mission trying to force Stack Exchange reliability.** The operator has decided
the available documentation is insufficient, and the publisher's methodology
pages are unreachable from this environment because the site's robots policy
blocks the crawler. The route that remains open is the one Mission 1.18 used —
the operator supplying the documents.

---

## §29 — What the operator must run

The review file is [docs/data/docker-wikimedia-reliability-review-v1.json](../data/docker-wikimedia-reliability-review-v1.json).

**The first version of this section printed a command that does not run, and the
operator hit it.** Two reasons, and the first hides the second: `DATABASE_URL`
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
still reporting no leak.

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
— 28 tests over §23's list, asserting **what is true**, not what will be true
after a confirmation that has not happened. A test claiming six rows resolve
would be asserting a future.

Two of them are worth naming. One asserts every `basis_type` in the review file
**and in the Mission 1.36 packet** is a real `ReliabilityBasisType` member — the
defect above, now caught by the contract rather than by the next mission that
tries to use those rows. The other asserts the recording tool still refuses
without a terminal: **a guard removed to make a pipeline pass is a guard that
never was.**
