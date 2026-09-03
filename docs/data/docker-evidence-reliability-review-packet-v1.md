# Docker Evidence reliability review packet V1

**Status:** Review preparation. Prepared by Mission 1.36, 2026-09-03.
**Machine-readable packet:** [`docker-evidence-reliability-review-packet-v1.json`](docker-evidence-reliability-review-packet-v1.json)
**Outcome:** `READY_FOR_OPERATOR_RELIABILITY_REVIEW`
**Assessments created:** **0.** Every judgement field is blank and stays blank.

---

## 0. What this is, and what software may not do

Reliability answers one question: **how dependable is THIS MEASUREMENT for THIS
PROPOSITION KIND?** Not how permitted the source is, not how well known, not how
carefully we read it, not how much it bears on the claim.

This document prepares that question for the three scopes the Docker Opportunity's
Evidence binds to. It contains **no reliability value, no range, no
recommendation, and no adjective ranking a source** — because none of those is
software's to write. `reliability: null` means **no assessment exists**; it does
not mean `0.0`, `0.5`, or *unknown so assume the middle*.

The scale is `[0.0, 1.0]` with **no threshold labels**. The architecture defines
no meaning for `0.9` or `0.7`, and this packet invents none.

---

## 1. Three scopes, not two

§0 warns against assuming there are two scopes because there are two source
families. There are **three**, and the reason is worth stating.

| # | source | resource | record kind | claim type | proposition kind | rows |
|---|---|---|---|---|---|---:|
| 1 | `stack-exchange` | `questions/stackoverflow` | `community_question` | `OBSERVED` | `community_site_published_questions_carrying_tag` | 1 |
| 2 | `stack-exchange` | `questions/stackoverflow` | `community_question` | `OBSERVED` | `community_site_questions_without_accepted_answer` | 1 |
| 3 | `wikimedia-pageviews` | `metrics/pageviews/per-article/en.wikipedia.org` | `content_request_count` | `OBSERVED` | `platform_counted_content_request_change` | 6 |

**Scopes 1 and 2 share four of five fields and differ only in
`proposition_kind`.** Same source, same resource, same record kind, same claim
type — and two different reliability questions, because *how many questions carry
this tag* and *how many carry it without an accepted answer* are different
propositions whose dependability can genuinely differ. The second rests on an
acceptance flag that may move over time; the first does not.

§1 permits two signal types to collapse onto one scope and requires it to be
reported. **Here they did not collapse**, and splitting them was not a choice —
the persisted proposition kinds differ.

`signal_type_id` is deliberately **not** part of scope identity. Whether the
interpreter read the Signal correctly is `extraction_confidence`, a different
field answering a different question.

**Every one of the 8 Docker rows binds to exactly one of these three.** 1 + 1 + 6.

---

## 2. Current state

All three scopes resolve `NO_APPLICABLE_ASSESSMENT`. All 8 rows are
`NON_SCORABLE` with `MISSING_RELIABILITY`, `scoring.evidence.reliability` is
`NULL` as designed, and reliability is resolved late rather than written onto the
row.

**The existing TED assessment applies to none of them** and must not be
inherited. It differs on **four of the five** fields — and shares the fifth,
which is the interesting part:

| | TED assessment | any Docker scope | |
|---|---|---|---|
| `source_id` | `ted-eu` | `stack-exchange` / `wikimedia-pageviews` | differs |
| `resource_id` | `notices/eforms-contract-and-award` | different | differs |
| `record_kind_id` | `procurement_notice` | `community_question` / `content_request_count` | differs |
| `proposition_kind` | `source_reported_procurement_value_contrast` | different | differs |
| `claim_type` | `OBSERVED` | `OBSERVED` | **shared** |

Every Evidence row in this repository is `OBSERVED`, so `claim_type` discriminates
nothing on its own. **That shared field is precisely where a leak would start if
scope matching were ever partial, nearest-match or fuzzy.** It is not: a scope
matches only when all five fields match exactly, and four mismatches are as final
as five.

§16 is explicit: asking for this mission, having previously accepted a TED value,
approving the project, saying *continue*, or choosing Docker as the pilot are
**none of them** a reliability review. Each scope needs its own judgement.

---

## 3. Scope 3 — Wikimedia per-article request counts (6 rows)

**Documentation: RETRIEVED.**

**What is measured.** A count of REQUESTS for one named article on one project
for one UTC day, restricted to the platform's `user` requester class, differenced
across two adjacent days.

**What the documentation says.** A request counts only if it meets *all* of:
HTTP 200 or 304; a WMF wiki host; no `preview=1`; not an automatically-called
Special page; and either `pageview=1` or the MIME-type and URL-path
requirements. Explicitly excluded: edit attempts, edit previews, preview pages,
auto-triggered Special pages, and API requests other than mobile app requests.
Automated traffic is tagged where the user agent *"is identified as a spider by
ua-parser and additional custom regex based identification"* — **pattern matching
against known signatures**.

That matches what the collector recorded at acquisition time: `user` is the
source's own class for traffic it did not attribute to a self-identified bot or
detect as automated, and the operator documents that detection as heuristic.

**Failure modes** (full table in the JSON): automated traffic classified as
`user`; a user-agent population shift — the publisher records a 2016 incident
where a Windows update made Chrome 41 agents appear to request Main pages;
**historical values changing after publication**; and the calendar moving an
adjacent-day difference.

**The largest open question:** the publisher's **revision and backfill practice
is not documented** on the pages retrieved. That is an absence of documentation,
not evidence of stability. Mission 1.19's re-run reported `revised: 0`, which is
one observation and not a policy.

---

## 4. Scopes 1 and 2 — Stack Exchange (1 row each)

**Documentation: PARTIAL — publisher documentation unreachable.**

`api.stackexchange.com` and `stackoverflow.com` are **not accessible to this
environment's fetcher, and the site's robots policy blocks the crawler.** No
retry with a varied header was attempted, no mirror or cached copy was consulted,
and no third-party summary was substituted. Mission 1.18 met the same wall and
the operator resolved it by supplying the documents; **that route remains
available and is the recommended one.**

**What is held anyway, and it is first-party.** The collector recorded, from the
API's own responses at collection time: `tagged=docker`, `site=stackoverflow`, a
field filter id, `page=1`, `page_size=100`, the date window 2024-03-01 to
2024-03-31, and the quota before and after. One page of size 100 returned **89**
records — below the bound, so the set was exhausted and **the retrieval was not
truncated**. 88 carry the site's own `docker` tag. The acceptance flag was
present on all 88.

Every normalized record also carries the source's own sentence beside the flag:
*the asker marked an answer accepted; not a statement that the problem is
objectively resolved.*

**Failure modes with documentary support: one.** The union of *answered but
unaccepted* (38) and *no answers at all* (16) is fully characterised, because the
split is recorded and recomputable from held records.

**Pagination incompleteness is CLOSED** for this window by provenance.

**Open, and open because the documentation is unreachable rather than because
nobody asked:**

- Can a question's tags be edited after creation?
- Are deleted questions excluded from API results?
- **Can an accepted answer be un-accepted or changed later?** This is the central
  reliability question for scope 2.
- Does a retrieval represent state at retrieval time or at event time?
- Is there any published distribution of time-to-acceptance?

---

## 5. Operator worksheet

**Nothing below is prefilled, and question 1 is a real question.** If the answer
is NO, leaving the reliability absent is the correct action, not a failure — the
Evidence stays `NON_SCORABLE`, which is the designed behaviour.

Complete one block per scope you are prepared to judge. Judge none, one, two or
all three.

```text
SCOPE ______________________________________________
  (source_id, resource_id, record_kind_id, claim_type, proposition_kind)

1. Do I have enough documented information to judge THIS measurement for
   THIS proposition kind?                                    YES / NO

2. If NO  -> stop here. Leave the reliability absent.

3. Reliability value in [0.0, 1.0]        ____________

4. Rationale, in my own words             ______________________________
                                          ______________________________

5. Stated limitation — the failure mode
   this value does NOT cover              ______________________________

6. Reviewer identity                      ____________

7. I confirm this value is NOT:
     [ ] a source-quality score
     [ ] a legal or governance approval score
     [ ] "0.5 because unknown"
     [ ] model-generated
     [ ] a calibrated probability
```

**Reminders.** You are not scoring Stack Exchange or Wikimedia; a source may hold
several different assessments. The two Stack Exchange scopes may legitimately
receive different values, or one may be judgeable and the other not. The TED
assessment is not inheritable. And a value here **does not calibrate the
aggregation profile** and does not make production scoring ready.

---

## 6. What a value would and would not unlock

A reviewed assessment for a scope would let the resolver bind reliability for
that scope's rows, which can move them from `NON_SCORABLE` toward
scoring-eligible.

It would **not**:

- calibrate the aggregation profile, which stays `UNCALIBRATED`;
- make production scoring ready;
- create an Opportunity score, or permit ranking;
- change independence, which stays `UNKNOWN` on all 8 rows with no
  `EvidenceIndependenceGroups` — and that continues to cap evidence levels
  independently of reliability;
- change any source's governance standing.

Reliability review is not calibration, and the two must not be reported as one
step.
