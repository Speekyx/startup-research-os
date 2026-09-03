# Mission 1.36 — Docker Evidence Reliability Review Preparation V1

**Outcome:** `READY_FOR_OPERATOR_RELIABILITY_REVIEW` (§29 A)

**Branch:** `sprint-1/mission-1.36`
**Review packet:** [`docker-evidence-reliability-review-packet-v1.md`](../data/docker-evidence-reliability-review-packet-v1.md)
**Machine-readable:** [`docker-evidence-reliability-review-packet-v1.json`](../data/docker-evidence-reliability-review-packet-v1.json)

---

## 0. The finding, and the thing software did not do

**Three reliability scopes, not two** — and that is the mission's substantive
result. §0 warns against assuming two because two source families exist, and
counting produced three: the two Stack Exchange signal types persist **different
proposition kinds**, so they share four of five scope fields and are still two
different reliability questions.

**No reliability value appears anywhere.** Not a number, not a range, not a
recommendation, not an adjective ranking a source. Every judgement field is
`null` or empty, and a test enumerates the packet to prove it. **Zero assessments
were created**, and all fourteen counters are unchanged.

---

## 1. The twenty-six answers

### 1. How many distinct reliability scopes exist across the 8 Docker rows?

**Three.** Computed from the persisted rows rather than assumed, by grouping on
the exact five-part key.

### 2. What are the exact five fields for each?

| # | `source_id` | `resource_id` | `record_kind_id` | `claim_type` | `proposition_kind` |
|---|---|---|---|---|---|
| 1 | `stack-exchange` | `questions/stackoverflow` | `community_question` | `OBSERVED` | `community_site_published_questions_carrying_tag` |
| 2 | `stack-exchange` | `questions/stackoverflow` | `community_question` | `OBSERVED` | `community_site_questions_without_accepted_answer` |
| 3 | `wikimedia-pageviews` | `metrics/pageviews/per-article/en.wikipedia.org` | `content_request_count` | `OBSERVED` | `platform_counted_content_request_change` |

### 3. Which Evidence ids bind to each?

Scope 1: `16a8c39c…9cae` (1 row). Scope 2: `17735944…22aa` (1 row) — Mission
1.32's eighth row. Scope 3: six rows, `13a5eadb…2074`, `1b93db71…7bc49`,
`487f62c6…0003`, `516182ff…5c75`, `6cf92ad6…430b`, `f1e0b7a4…dce1`.

**1 + 1 + 6 = 8**, and a test asserts every row belongs to exactly one scope.

### 4. Which signal types collapse into the same scope, if any?

**None collapse.** §1 permits it and requires it to be reported; here the two
Stack Exchange signal types (`community_question_volume` and
`community_question_without_accepted_answer_volume`) resolve to **different
proposition kinds**, so §1's other branch applies and they stay separate.

Scope 3 holds six rows under one signal type, `content_request_change` — six
observations of one measurement, which is the ordinary case.

`signal_type_id` is not part of scope identity: whether the interpreter read the
Signal correctly is `extraction_confidence`, a different field answering a
different question.

### 5. Which authoritative methodology documents were reviewed?

**For scope 3, two, both retrieved 2026-09-03:**

- `Research:Page view` (meta.wikimedia.org) — sections *Definition* and *Tagging*.
- `Data Platform / Data Lake / Traffic / Pageviews` (wikitech.wikimedia.org) —
  section *Events and known problems since 2015-05-01*.

**For scopes 1 and 2, none.** `api.stackexchange.com` and `stackoverflow.com`
are not accessible to this environment's fetcher and the site's robots policy
blocks the crawler. **No retry with a varied header, no mirror, no cached copy,
no third-party summary.** Mission 1.18 met the same wall and the operator
resolved it by supplying the documents; that route remains available.

What those scopes rest on instead is first-party and already held: the
acquisition provenance the collector recorded from the API's own responses, and
the source semantics the normalizer stores in every record.

### 6. What factual methodology findings apply to each scope?

**Scope 3.** A request counts only if it meets *all* of: HTTP 200 or 304; a WMF
wiki host; no `preview=1`; not an auto-called Special page; and either
`pageview=1` or the MIME-type and URL-path requirements. Explicitly excluded:
edit attempts, edit previews, preview pages, auto-triggered Special pages, and
API requests other than mobile app requests. Automated traffic is tagged where
the user agent *"is identified as a spider by ua-parser and additional custom
regex based identification"* — pattern matching against known signatures, which
matches what the collector recorded: `user` is the source's own class for traffic
it did not detect as automated, and the operator documents that detection as
heuristic.

**Scopes 1 and 2.** `tagged=docker`, `site=stackoverflow`, a field filter id,
`page=1`, `page_size=100`, window 2024-03-01 to 2024-03-31, quota 299 of 300
after the call. **One page of size 100 returned 89 records** — below the bound,
so the set was exhausted and the retrieval was not truncated. 88 carry the site's
own tag. For scope 2, the flag was present on all 88, and every record carries
the source's sentence: *the asker marked an answer accepted; not a statement that
the problem is objectively resolved*.

Per §8, these were **cited from existing provenance and not re-acquired**.

### 7. What failure modes were identified?

Each with the §9 columns — supported by documentation, how it could misrepresent
the claim, mitigation or bound, residual unknown. Full tables in the JSON.

**Scope 3:** automated traffic classified as `user`; a user-agent population
shift (the publisher records a 2016 Windows/Chrome-41 incident); **historical
values changing after publication**; the calendar moving an adjacent-day
difference.

**Scopes 1 and 2:** retagging after creation; deletion removing questions from
results; pagination incompleteness (**closed** for this window by provenance);
creation-timestamp instability; and for scope 2 specifically, **acceptance state
changing after publication** and **late acceptance biasing a recent window**.

Only two of these are supported by documentation. The rest are open — which is
itself the finding for the Stack Exchange scopes.

### 8. What remains unknown?

**Scope 3, and this is the largest gap:** the publisher's **revision and backfill
practice is not documented** on the pages retrieved. An absence of documentation,
not evidence of stability. Mission 1.19's re-run reported `revised: 0`, which is
one observation and not a policy.

**Scopes 1 and 2:** whether tags can be edited after creation; whether deleted
questions are excluded; **whether an accepted answer can be un-accepted or
changed**; whether a retrieval represents state at retrieval time or event time;
whether any time-to-acceptance distribution is published. Open because the
documentation is unreachable, not because nobody asked.

### 9. Were any reliability values suggested by software?

**No.** This is the assertion the test file exists for. The packet carries no
number in any judgement position, no range, no recommendation, and no adjective
ranking a source. `reliability` is `null` in all three scopes, and `null` is
documented as *no assessment exists* rather than as a default.

The scale is stated as `[0.0, 1.0]` with **no threshold labels** — the
architecture defines no meaning for `0.9` or `0.7` and this packet invents none.

### 10. Were any reliability values supplied by the operator?

**No.** None was requested in this run, and §15 makes stopping here the
successful outcome rather than an incomplete one.

### 11. Was `reviewed_by` human/accountable?

Not applicable — no assessment exists. The contract requires it: a
`HUMAN_REVIEW` assessment with nobody named is refused, and the worksheet asks
for reviewer identity as its own question.

### 12. Were any assessments persisted?

**No.** `epistemic.reliability_assessments` still holds exactly one row, the TED
assessment from Mission 1.16, unmodified.

### 13. Exact assessment ids/versions?

None created. The existing one is `3de2af10-60d1-4e3e-a9b6-d67e2345e020`
version 1, scope `ted-eu | notices/eforms-contract-and-award |
procurement_notice | OBSERVED | source_reported_procurement_value_contrast`.

**It matches no Docker scope**, and the packet records why. It differs on **four
of the five** fields and shares the fifth, `claim_type: OBSERVED` — every row in
this repository is `OBSERVED`, so that field discriminates nothing on its own.
**That shared field is exactly where a leak would start if matching were ever
partial or nearest-match.** It is not: all five must match, and four mismatches
are as final as five.

*(My first draft of the packet said it matched on zero fields. A test caught
that; it was corrected, and the corrected version makes a better point than the
overstatement did.)*

### 14. How many Docker rows resolve reliability before/after?

**0 before, 0 after.** All three scopes resolve `NO_APPLICABLE_ASSESSMENT`.

### 15. How many remain `MISSING_RELIABILITY`?

**All 8.**

### 16. How many become scoring-eligible?

**None.** Nothing changed, because no judgement was supplied.

### 17. Were Evidence rows themselves modified?

**No.** `scoring.evidence.reliability` is `NULL` on every row and stays that way
by design (§18) — reliability is resolved late, and a value written onto the row
would be a second answer to a question the resolver already answers.

Verified: **0 rows carry a non-NULL reliability.**

### 18. Was the aggregation profile calibrated?

**No** (§19). `REFERENCE_PROFILE_V1` remains `UNCALIBRATED`. Reliability review
is not calibration, and the packet says so in the operator's own reminders so the
two cannot be reported as one step.

### 19. Did any diagnostic aggregation run?

**No** (§22). It is conditional on at least one row becoming scorable through
operator review, and none did.

### 20. Was an Opportunity Score created?

**No.** `scoring.scores` still does not exist.

### 21. Was ranking performed?

**No.**

### 22. Did independence change?

**No** (§23). `UNKNOWN` on all 8 rows, 0 `EvidenceIndependenceGroups`. A scope
relation or a reliability value establishes nothing about independence, and this
continues to cap evidence levels independently of reliability — a limitation the
packet states rather than leaves implicit.

### 23. Is Problem-Family still PARKED?

**Yes.** `PARK_PROBLEM_FAMILY_CLASSIFIER`, production `NOT_AUTHORISED`. Nothing
in this mission touched it.

### 24. Did research canonical counters change?

**No.** All verified against the live database:

| Counter | Expected | Actual |
|---|---:|---:|
| RawRecords / NormalizedRecords | 148 / 148 | **148 / 148** |
| Signals / Claims / Evidence | 28 each | **28 each** |
| ClaimRevisions | 29 | **29** |
| EvidenceIndependenceGroups | 0 | **0** |
| ReliabilityAssessments | 1 | **1** |
| Reliability basis rows | 4 | **4** |
| Opportunities / revisions / links | 1 / 1 / 7 | **1 / 1 / 7** |
| Embeddings / Scores | 0 / 0 | **0 / 0** |
| Registered sources | 29 | **29** |
| Scope relations | 0 | **0** |

### 25. Which D-03 blockers remain?

Reported independently, as §20 requires. **Do not collapse them.**

| # | Blocker | State |
|---|---|---|
| 1 | Definition of reliability and authority to set it | **RESOLVED** (Mission 1.14) |
| 2 | Reviewed values for scopes actually in use | **OPEN.** One assessment exists, for a TED scope. **All three Docker scopes are unreviewed**, so 8 of 8 rows are `NON_SCORABLE`. This mission prepared the question and did not answer it. |
| 3 | A `CALIBRATED` aggregation profile | **OPEN**, untouched |
| 4 | Authorised temporal half-life where applicable | **OPEN.** Every Docker claim is `EVERGREEN`, so no half-life is required for *these* rows — that is a property of this corpus, not a resolution. |
| 5 | Evidence-level thresholds fitted to outcome data | **OPEN**, untouched |

**Four of five remain open.** Even every Docker scope receiving a value would
move only blocker 2 — and would still not make production scoring ready.

### 26. Recommended next mission?

**None. Stop and request the operator's reliability decisions** (§31).

That is the mission's designed end. The packet and the worksheet are ready; three
scopes await a judgement that only an accountable person may make; and §16 is
explicit that asking for this mission, having accepted a TED value before, or
saying *continue* are none of them a reliability review.

**One thing worth flagging before that review.** For scopes 1 and 2 the
publisher's documentation could not be retrieved here, so several questions a
reviewer would want answered are open — most importantly whether an accepted
answer can later change. If the operator can supply those documents, as in
Mission 1.18, the review for those two scopes becomes materially better founded.
If not, answering **NO** to worksheet question 1 for them is a correct and
expected outcome, and leaving the reliability absent is the designed behaviour
rather than a failure.

**After the review, whatever it decides:** if any scope receives a value, the
next mission is **Evidence Aggregation Calibration Strategy V1** — not ranking,
and not scoring. If none does, the reliability gap is documented and the project
should consider the second pilot Opportunity that Mission 1.35 recommended, in a
domain with a published product taxonomy.

---

## 2. Tests

38 in
[`test_reliability_review_packet.py`](../../packages/opportunity-engine/python/tests/test_reliability_review_packet.py);
391 in the package.

The load-bearing ones are negative: no number in any judgement position, no
adjective ranking a source, no model origin, no threshold labels, and a
judgement block holding no numeric value of any type. The rest hold the scope
arithmetic, the exclusions that keep reliability from becoming a source
coefficient (`signal_type_id`, governance state), the upstream requirements for a
`HUMAN_REVIEW` assessment, and the state that must not have moved.

**One test caught a factual error in my own document** — the TED comparison
claiming zero shared fields — and it was corrected rather than the test loosened.

**A scan was narrowed for the fourth time across four missions**, and this time
the fix was generalised rather than patched: `$comment` keys are stripped at any
depth before scanning, because **a `$comment` is where a rule is written and a
rule may name the values it forbids, while a field may not**. That is
`testing-strategy.md` §23 turned into a reusable distinction instead of a
case-by-case exception.

---

## 3. CI-equivalent verification

| Gate | Result |
|---|---|
| `generate.py --check` | ok |
| `run_python_tests.py` | all suites passed |
| `validate_schema.py` / `migrate.py --plan` | ok, ledger at 0031 |
| `validate_source_registry.py` / `validate_compliance_capabilities.py` | ok |
| `validate_normalization.py` / `validate_signals.py` / `validate_claims.py` | ok |
| `validate_evidence_aggregation.py` | scoring still blocked |
| `ruff check` / `ruff format --check` | clean |
| `mypy` (13 packages) | no issues |
| generated-doc `--check` steps (4) | all match |
| `run_pytest_suites.py` | passed across 9 packages; database unchanged |
