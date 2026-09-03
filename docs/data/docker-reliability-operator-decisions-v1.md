# Docker reliability — the operator's decisions

**Status:** Recorded by Mission 1.36.1, 2026-09-03.
**Reviewer:** `thibchm`
**Outcome:** `DOCKER_RELIABILITY_PARTIALLY_REVIEWED`. The mission reached
`OPERATOR_CONFIRMATION_REQUIRED` and stopped there; the operator confirmed at a
terminal on 2026-09-03 and **one assessment is now recorded**. Two of the three
scopes in use remain deliberately unassessed, which is why this is `PARTIALLY`
and not `DOCKER_EVIDENCE_SCORING_ELIGIBILITY_READY`.

---

## 0. What was decided

Mission 1.36 prepared three reliability scopes. The operator reviewed all three
and decided differently about them, which is exactly what a per-scope judgement
is for.

| Scope | Decision | Result |
|---|---|---|
| 1 · `stack-exchange` / `…published_questions_carrying_tag` | **NO** | no assessment |
| 2 · `stack-exchange` / `…questions_without_accepted_answer` | **NO** | no assessment |
| 3 · `wikimedia-pageviews` / `platform_counted_content_request_change` | **YES** | `0.65`, HUMAN_REVIEW, **recorded** |

**No scope drift.** All three five-part keys were re-verified against the live
database and against the Mission 1.36 packet before anything else. Had one
differed, the operator's decisions would have been about something else and this
mission would have stopped.

---

## 1. Scopes 1 and 2 — the NO decision

The operator does **not** consider the currently available authoritative
methodology documentation sufficient to make an accountable reliability
judgement.

**What that means, and what it does not.** It means **no human reliability
judgement exists** for these scopes. It does **not** mean:

- `reliability = 0`
- `reliability = 0.5`
- low reliability
- an unreliable source

Those are all measurements, and the point of a NO is that nobody made one. The
reliability stays `NULL` and the resolver returns `NO_APPLICABLE_ASSESSMENT`,
which is the designed behaviour rather than a gap.

**No row was created for them.** Not a numeric assessment, not a placeholder, not
a documentary-only assessment. A refusal recorded as data would be a value, and
the next reader would treat it as one.

**Scope 1's unresolved questions** — whether tags may change after publication;
whether deleted questions disappear from later retrievals; whether a retrieval
represents current state or event-time state.

**Scope 2's unresolved questions** — whether accepted-answer state can later
change; whether an accepted answer can be removed or replaced; whether a
retrieval represents collection-time or event-time state; possible
late-acceptance effects.

Both sets are open because the publisher's documentation is unreachable from this
environment, and Mission 1.36 recorded that rather than substituting a
third-party summary.

---

## 2. Scope 3 — the YES decision

**Scope**

```text
source_id         wikimedia-pageviews
resource_id       metrics/pageviews/per-article/en.wikipedia.org
record_kind_id    content_request_count
claim_type        OBSERVED
proposition_kind  platform_counted_content_request_change
```

**Judgement**

```text
reliability   0.65
reviewed_by   thibchm
origin        HUMAN_REVIEW
```

**Rationale, in the reviewer's words**

> The Wikimedia pageview measurement has documented first-party counting rules
> that explicitly define which requests are included and excluded, and automated
> traffic is classified using user-agent and custom-pattern detection. The
> measurement therefore has a documented methodology and a bounded meaning for
> the proposition that Wikimedia counted changes in requests to the Docker
> article.

**Stated limitation, in the reviewer's words**

> Automated traffic detection is heuristic, and the retrieved Wikimedia
> documentation does not establish a complete revision/backfill policy for
> historical pageview values. Historical measurements may therefore be affected
> by classification changes or later revisions.

**Documentary basis** — reused verbatim from the Mission 1.36 packet, with no
replacement documentation retrieved:

| basis type | document | section |
|---|---|---|
| `MEASUREMENT_METHODOLOGY` | Research:Page view | Definition; Tagging |
| `KNOWN_LIMITATION` | Data Platform / Data Lake / Traffic / Pageviews | Events and known problems since 2015-05-01 |

**`0.65` is the operator's number.** Software did not choose it, suggest it,
bound it or normalise it, and it carries **no label**: the reliability contract
has no threshold vocabulary, so it is not *good*, *medium*, *high* or
*65% confident*.

---

## 3. What `0.65` will and will not do

It belongs to **one** reliability scope. Six Evidence rows matching that scope do
not turn it into a Docker-wide coefficient:

- there is no average reliability, no overall Docker reliability, no mean
  Evidence Score, no *Docker confidence*, and no *Docker 65%*;
- scopes 1 and 2 remain **unknown**, and unknown is not a low number;
- it does not calibrate anything — the aggregation profile stays `UNCALIBRATED`;
- it does not establish independence, which stays `UNKNOWN` on all eight rows
  with no groups, and that continues to cap evidence levels for reasons
  reliability cannot touch;
- it changes no source's governance standing.

---

## 4. Why this mission stopped, and how it was unblocked

**The operator confirmed on 2026-09-03 and the assessment is now recorded.** This
section is kept as written, because how it stopped is the part worth preserving:
the guard is the contract, not an obstacle to it.

The recording tool requires a confirmation **typed by a person**, and refuses
when there is no terminal:

> no terminal to confirm on. A reliability assessment is a human decision and
> this is not a step a pipeline runs

That guard exists precisely so an automated run cannot record a human judgement,
and Mission 1.36.1 §7 forbids bypassing it. Piping the confirmation string in
would defeat the one control that makes `reviewed_by` mean anything.

So the review file is written, validated end to end through the real workflow,
and **left for the operator to confirm**.

**Two things the invocation needs, and both were missing from this document's
first version.** `DATABASE_URL` lives in `infrastructure/compose/.env` and not in
the shell, and the tool refuses without it — *this writes to a deployment, not to
the tree*. And a bare `python` finds `sros_contracts` through the script's own
`sys.path` insert but **not `psycopg`**, which is imported after that refusal, so
the first error hides the second. Run it through `uv`.

PowerShell, in one tab:

```powershell
$env:DATABASE_URL = ((Select-String -Path infrastructure\compose\.env -Pattern '^DATABASE_URL=' | Select-Object -First 1).Line -replace '^DATABASE_URL=', '')
```

```powershell
uv run --package sros-nlp python infrastructure/scripts/record_reliability_assessment.py --review-file docs/data/docker-wikimedia-reliability-review-v1.json --apply
```

It will print the assessment and ask you to type `record it`. Anything else
aborts and writes nothing.

**After you confirm**, this reports what changed:

```powershell
uv run --package sros-nlp python infrastructure/scripts/report_docker_reliability_resolution.py
```

Expected: six Wikimedia rows `RESOLVED` at `0.65` against one new assessment,
two Stack Exchange rows still `NO_APPLICABLE_ASSESSMENT`,
`scoring.evidence.reliability` still `NULL` on every row, and the negative checks
still showing no leak.

**That is exactly what it reported.** Assessment
`e2419f13-c031-44d5-837c-c56a867baf34`, version 1, `HUMAN_REVIEW`, `thibchm`, two
document-backed basis rows, no calibration reference. Six rows `RESOLVED` at
`0.65` binding that one id, two still `NO_APPLICABLE_ASSESSMENT`, and the
negative checks now run **six** rather than three, because a second assessment
doubles the ways one could leak, and still find none.

---

## 5. State as this mission leaves it

Verified against the live database after the operator confirmed:

| | before | after |
|---|---:|---:|
| ReliabilityAssessments | 1 | **2** |
| Reliability basis rows | 4 | **6** |
| Docker rows `RESOLVED` | 0 | **6** |
| Docker rows `NO_APPLICABLE_ASSESSMENT` | 8 | **2** |
| `scoring.evidence.reliability` non-NULL | 0 | **0** |
| Negative resolver checks run / leaks | 3 / 0 | **6 / 0** |
| Opportunities / revisions / links | 1 / 1 / 7 | **1 / 1 / 7** |
| Scores | 0 | **0** (`scoring.scores` absent) |

Two rows of that table are the ones to read twice.
`scoring.evidence.reliability` is **still NULL on every row**, because
reliability binds late (ADR-026 Decision 2): the resolver produces the number and
the binding at read time, and the Evidence row is never rewritten. And the
**Opportunity did not move** — reliability changing does not change what a
hypothesis said.

## 6. The diagnostic aggregation

§15's precondition became true, so it ran: `allow_uncalibrated=True`, over the
real `aggregate()`, writing
[docker-diagnostic-aggregation-v1.json](docker-diagnostic-aggregation-v1.json)
and **no database row**. Every entry carries the three required words:
**UNCALIBRATED, DIAGNOSTIC ONLY, NOT AN OPPORTUNITY SCORE.**

**Eight Evidence rows sit on eight distinct Claims**, so these are eight
single-record aggregations rather than one eight-record aggregation. Reliability
resolving does not turn six observations of one Wikipedia article into an
aggregation, and summing them would invent a claim nobody made.

| | six Wikimedia claims | two Stack Exchange claims |
|---|---|---|
| status | `COMPLETE` | `UNAVAILABLE` |
| `q` | `0.650` | none |
| limiting component | **`reliability`** | none; `MISSING_RELIABILITY` |
| support strength | 0.65 | 0 |
| contradiction strength | 0.0 | 0.0 |
| supported mass | 0.65 | 0.0 |
| uncertainty mass | 0.35 | **1.0** |
| Evidence level | **1**, Weak Signal | **0** |

**The reviewed value is exactly what the score is made of.** `q = min(components)`
and relevance, directness, extraction confidence and freshness are all `1.0`, so
`reliability` is the limiting component on all six. That is the same shape
Mission 1.15.13 found for TED at a different number, and it is the honest result:
the score is a restatement of one human judgement, not a corroboration of it.

**Level stayed 1, and reliability could not have raised it.** The blocked reasons
say why: *Repeated Signal needs 2 supporting groups of established independence,
found 0*, and Market Evidence needs a record categorised `MARKET_ACTIVITY`. Both
gates are about things a reliability value does not touch.
