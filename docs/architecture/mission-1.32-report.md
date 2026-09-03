# Mission 1.32 — Docker Commercial Evidence Completion V1

**Outcome:** `COMMERCIAL_EVIDENCE_CREATED_NO_OPPORTUNITY_DIMENSION` (§20 B)

**Branch:** `sprint-1/mission-1.32`
**Governed by:** [`answer-acceptance-semantics-v1.md`](../data/answer-acceptance-semantics-v1.md),
[ADR-034](adr/ADR-034-community-question-volume-signal-family.md),
[ADR-023](adr/ADR-023-source-bucket-adjacency.md)

---

## 0. What this mission was asked to do, and what it found

The Docker Opportunity packet was formable and thin: seven Evidence rows across
two counting dimensions, `AUDIENCE_OR_USAGE` and `PROBLEM_OR_NEED`, and nothing
commercial. The mission asked whether the **already-held** Stack Exchange corpus
could support `SOLUTION_GAP` or `SOLUTION_DISSATISFACTION` from a field it was
already carrying: `has_accepted_answer`.

It can support neither, and the reason is not that the data is thin. It is that
the field measures **one person's action** and both dimensions require a
statement about **a solution**. The measurement is real, bounded and worth
holding; the inference from it to a commercial dimension is the exact one the
taxonomy's own `never_means` clauses forbid.

So the mission produced a valid Signal, Claim and Evidence row, and mapped it to
**no dimension at all**. That is outcome B, and §9 named it in advance as a
legitimate result rather than a failure.

**The assessment was frozen first.** `answer-acceptance-semantics-v1.md` was
written and committed before any Signal existed, and it records the decision
`NO_EXISTING_DIMENSION` against both candidates. This ordering is the whole
point of §0: a dimension chosen after seeing that the packet needed one is not a
finding, it is a rationalisation.

---

## 1. The twenty-eight questions

### 1. What does `has_accepted_answer` mean?

That the **asker** of a question clicked the accept control on one of its
answers. Only the asker (or a moderator, in rare interventions) can do this. The
normalizer already carries the source's own sentence in the payload beside the
value:

> the asker marked an answer accepted; not a statement that the problem is
> objectively resolved

### 2. What does it not mean?

Six things, each of which a reader reaches for:

- **Not that the problem is unsolved.** The asker may have solved it elsewhere,
  lost interest, or never returned. `false` reports a non-action by one person.
- **Not that anyone is dissatisfied.** Nobody in these records evaluates
  anything. Dissatisfaction is a stated attitude toward a thing used; a question
  is not one.
- **Not that existing tools are inadequate**, and not a commercial solution gap.
- **Not willingness to pay**, and not the existence of a buyer or a budget.
- **Not recurrence.** Two unaccepted questions are not evidence of one recurring
  problem: that relation is `SAME_PROBLEM_FAMILY`, which is **PARKED**
  (Mission 1.27).
- **Not a rate.** The count is a set, not a share; see question 11.

### 3. Was the held Docker corpus complete for this derivation?

Yes, and it was checked rather than assumed. The retrieval asked for a page size
of 100 and 89 records came back, so the retrieval terminated below its own bound
and was not truncated. The page size is **read from provenance** by the runner,
never hard-coded: a script that assumed 100 would be asserting the very thing the
check exists to test.

`has_accepted_answer` was present on **all 88** eligible records. Zero withheld
the field, so §3's refusal path was not exercised on real data — it is exercised
by tests instead.

### 4. What was the eligible population?

**88 questions**: the records from the `tagged=docker` retrieval that actually
carry the tag `docker` in their own tag list.

89 records were returned and 88 carry the tag. **What the query asked for and
what the source says are different facts**, and the extractor counts the second.
The one record that does not carry the tag is outside the population regardless
of why the API returned it.

### 5. How many had an accepted answer?

**34.**

### 6. How many did not?

**54**, which decomposes into two facts the Signal deliberately unions:

| | count |
|---|---|
| answered, no answer accepted | 38 |
| zero answers received | 16 |
| **no accepted answer (the Signal)** | **54** |
| accepted answer present | 34 |
| acceptance flag absent | 0 |
| **eligible population** | **88** |

The split is recorded in the frozen assessment because the union alone cannot
support a solution claim and the 16 look like they might. They do not: see
question 15.

### 7. At what source state/time is that statement valid?

Two different times, named separately, because conflating them would make the
claim false:

- The **questions** were created between source timestamps `1709280363` and
  `1709612094` (Unix seconds, the source's own labels, carried unconverted).
- The **acceptance state** is whatever it was when SROS collected the record,
  which is later and may be much later. A question created in March 2024 could
  have had an answer accepted in 2025 and would count as accepted here.

The claim therefore says *"at the source state observed"* and never *"during"*
that window.

### 8. Was a Signal created?

Yes. One.

### 9. Exact Signal type?

`community_question_without_accepted_answer_volume`, registered by migration
[`0031`](../../infrastructure/db/migrations/0031_community_question_without_accepted_answer_signal_type.sql).

It reuses the existing quantity family `COMMUNITY_QUESTION_VOLUME` (ADR-034)
rather than creating a new one: this is a **different measurement over the same
kind of quantity**, and a second family would assert that the two counts are
incommensurable when they are directly comparable.

It is a separate signal **type** rather than a parameter on
`community_question_volume`, because "how many questions carry this tag" and
"how many carry it without an accepted answer" are different propositions, and a
parameter that silently changes what a Signal asserts is a hidden behaviour with
a name.

### 10. Was a Claim created?

Yes. One Claim, with **two revisions** — see question 11.

### 11. Exact bounded Claim?

Revision 2, the current one:

> Stack Exchange published 54 questions carrying its own tag "docker" on
> "stackoverflow", created between source timestamps "1709280363" and
> "1709612094", that had no answer marked accepted by their asker at the source
> state observed.

**Revision 1 said something subtly wrong and is preserved.** It read *"Of the
questions carrying its own tag `docker` on `stackoverflow` created between source
timestamps T1 and T2, 54 had no answer marked accepted…"*. Every word of that is
true and the sentence is still wrong: **"Of the questions…, 54" is shaped like a
numerator**, and it names no denominator. A reader supplying one would reach for
88 — which is not the population in that span, because T1..T2 bounds the 54
*themselves* and the last accepted question falls outside them.

The interpreter moved from `1.3.0` to `1.4.1` in this mission: `1.4.0` added the
seventh template, and `1.4.1` corrected its wording. The claim history is
append-only and both revisions are in `research.claim_revisions`.

### 12. Was Evidence created?

Yes. One row, `scoring.evidence` 27 → 28.

Not two, though it briefly was. See §2 below.

### 13. Which Opportunity dimension, if any?

**None.** `signal-type-dimension-map@1.0.0` maps this type to `frozenset()`.

That is different from an unmapped type. `map_signal_type` returns `None` for a
type nobody has decided about and a registered mapping with zero dimensions for
one somebody decided carries none. This is the second kind, and its rationale is
recorded beside the mapping.

### 14. Why is that mapping justified?

Against `SOLUTION_GAP`, its own `never_means` settles it:

> that absence of evidence of a solution is evidence of its absence

An unaccepted question is exactly that absence. The dimension was written to
exclude this reasoning, and reading the field into it would require rewriting the
dimension — which §20 forbids ("Do not change taxonomy definitions to obtain A").

Against `SOLUTION_DISSATISFACTION`: the asker is not evaluating a product. There
is no object of dissatisfaction anywhere in the record, and no dissatisfaction
datum to read. A question is a request for help, not a verdict on a tool.

Against `RECURRENCE_OR_FREQUENCY`: reading 54 unaccepted questions as one
recurring problem requires deciding that some of them are *the same problem*.
That is `SAME_PROBLEM_FAMILY`, and it is PARKED.

### 15. What does it explicitly NOT establish?

Beyond question 2's list, one case deserves naming because it is the strongest:
**the 16 questions with zero answers.** They look like the sharpest possible
evidence of a gap — nobody could even answer. They still do not reach
`SOLUTION_GAP`:

- a question can go unanswered because it is unclear, duplicated, too specific,
  or badly timed;
- and the community's non-answer is not a statement that no solution exists.

Isolating the sharper subset does not rescue the inference. It makes the same
inference over a smaller set.

### 16. Did Docker Evidence count change?

Yes. The packet went **7 → 8** rows.

It nearly went to 9 by accident: the new row initially formed its own tenth
packet because `subject_key` only recognised `community_question_volume`. Fixed
in `source-native-subject-grouping@1.2.0`; see §2.

### 17. Did counting-dimension count change?

**No.** Still exactly two: `AUDIENCE_OR_USAGE` and `PROBLEM_OR_NEED`.

This is the arithmetic that makes outcome B honest. A row mapping to zero
dimensions adds to the packet's **size** and never to its **diversity**, so it
cannot move sufficiency by existing.

### 18. Is the packet still formable?

Yes. `HYPOTHESIS_FORMABLE`, under `opportunity-sufficiency@1.0.0` unchanged
(≥ 2 eligible rows, ≥ 2 distinct counting dimensions). It was formable before
this mission and is formable after, for the same two reasons.

`scoring_ready` remains **false**.

### 19. Is it still egress-authorized?

Yes. `AVAILABLE`, by the same deterministic check as Mission 1.29. **Nothing was
serialised and nothing was sent** — the check was evaluated, not acted on.

### 20. Is reliability still unresolved?

Yes. `epistemic.reliability_assessments` holds **1** row, unchanged, and it is
not for any Docker Evidence. All 8 rows in the packet are `ELIGIBLE_CONTEXT`;
**0** are `ELIGIBLE_SCORING`.

No `ReliabilityAssessment` was manufactured to make the new row count for more
than context.

### 21. Is independence still UNKNOWN/dependent?

Yes — for **8 of 8** rows now instead of 7 of 7.

The new row is, if anything, the least independent in the packet: it is a
**second measurement over the same 88 records** that produced the existing
`community_question_volume` row. Two numbers from one corpus are one finding
counted twice, which is precisely what the independence rules exist to prevent.
`scoring.evidence_independence_groups` holds 0 rows.

### 22. Were any model calls made?

**No.** Zero calls, zero cost. The extractor and the interpreter are both
deterministic, and neither imports an HTTP client, a provider SDK, a database
driver, the LLM Gateway, or the parked semantic-equivalence package — asserted
over the AST, not by inspection.

### 23. Was an Opportunity revision created?

**No.** `OPPORTUNITY_REVISION_NOT_YET_WARRANTED`.

The existing hypothesis stands at revision 1 with its 7 cited Evidence rows. The
new row maps to no dimension, so revising the hypothesis to cite it would add a
citation that supports none of its statements. Evidence changing is not, by
itself, a reason to revise.

### 24. Was scoring performed?

**No.** Scoring remains blocked (D-03); the evidence-aggregation guard still
reports *"framework defined; parameters NOT calibrated; production scoring
blocked"*.

### 25. Was ranking performed?

**No.** There is one Opportunity and nothing to rank it against, and ranking is
downstream of scoring in any case.

### 26. Is Problem-Family still PARKED?

Yes. `PARK_PROBLEM_FAMILY_CLASSIFIER` stands and production remains
`NOT_AUTHORISED`. No module in `sros_opportunity` imports
`semantic_equivalence`, and neither does the new extractor.

The temptation was real here: 54 unaccepted questions about Docker invite the
question "how many are the same problem?", and that question is exactly the
parked relation.

### 27. Canonical counters before/after?

| Counter | Before | After |
|---|---:|---:|
| RawRecords | 148 | **148** |
| NormalizedRecords | 148 | **148** |
| Signals | 27 | **28** |
| Claims | 27 | **28** |
| ClaimRevisions | 27 | **29** |
| Evidence | 27 | **28** |
| EvidenceIndependenceGroups | 0 | **0** |
| ReliabilityAssessments | 1 | **1** |
| Opportunities | 1 | **1** |
| OpportunityHypothesisRevisions | 1 | **1** |
| OpportunityHypothesisEvidence links | 7 | **7** |
| Embedding provenance rows | 0 | **0** |
| Registered sources | 29 | **29** |
| Latest migration | 0030 | **0031** |

**RawRecords and NormalizedRecords are unchanged**, which is the load-bearing
row: §12 forbade new acquisition, and the entire measurement came from records
already held.

**ClaimRevisions grew by two** while Claims grew by one, because the wording
correction created revision 2 of the new claim. That is the append-only history
working as designed.

### 28. Recommended next mission?

§22's rule for outcome B: *recommend the narrowest next source capable of
answering a genuine commercial dimension for `subject:docker`, preferring already
reviewed / authorized sources.*

**The honest answer is that no already-reviewed source can do it, and the reason
is a grain mismatch rather than a permission gap.** The commercial dimensions the
packet lacks — `ECONOMIC_VALUE`, `BUYER_OR_BUDGET_EXISTENCE`, `MARKET_ACTIVITY`,
`COMPETITIVE_SUPPLY`, `WILLINGNESS_TO_PAY` — need a source that satisfies **both**
conditions, and the 29 reviewed sources split cleanly:

- **Commercial-capable and collector-eligible, but wrong grain.** The two
  `public_procurement` sources publish subject vocabularies that do not name
  products. TED's own subject key in the current packet set is literally
  `ted-eu:CPV-division:90` — a two-digit CPV division. A CPV division can never
  name Docker, so a TED notice cannot join the docker packet without inflating
  what "the subject" means. The same holds for `usaspending` and PSC codes, and
  the macro sources (`world-bank`, `fred`, `eurostat`) have no product grain at
  all.
- **Right grain, but RESTRICTED.** `github`, `product-hunt`, `apple-app-store`,
  `google-play` and `steam` all publish identifiers at product grain and are all
  `RESTRICTED`. GitHub's is the clearest: its Acceptable Use Policies enumerate
  permitted uses as an allowlist, explicitly indifferent to whether information
  came from the API, and commercial market research producing proprietary
  insights is in neither permitted use.

So the recommended next mission is **not an acquisition**:

> **Mission 1.33 — Commercial Dimension Source Feasibility V1.**
> Answer one bounded question over the existing registry: *which reviewed source
> can publish a commercial-dimension observation at the grain of one canonical
> subject?* Produce a per-source verdict with the identifier vocabulary named,
> and if the answer is that none can, record that as the finding.

This is deliberately narrower than "acquire a commercial source". Acquiring
before the grain question is answered produces Evidence in its own packet that
can never join `subject:docker`, which is how a packet grows without a hypothesis
getting any better supported. The mission is a desk review of documents already
in the repository; it reaches no network and needs no new authorization.

If that review finds a workable source, the acquisition mission follows it. If it
finds none, the remaining honest move is the Reliability / Scoring Eligibility
foundation, which §22 names as the fallback once breadth is not the limiting
factor.

---

## 2. Two defects this mission introduced and fixed

Both are recorded because each is a general mechanism, not a typo.

### 2.1 A version bump duplicated an Evidence row

Evidence idempotency keys on `(workspace_id, claim_id, signal_id,
extraction_method)`, and `extraction_method` embeds the interpreter version.
Correcting the claim **wording** moved the interpreter `1.4.0 → 1.4.1`, so the
re-run did not recognise the existing row: it inserted a second one. Two Evidence
rows asserting the same relation between the same Signal and the same Claim,
differing only by the version of the deterministic interpreter that phrased them.

It could not stay. A packet counts Evidence rows, so one measurement would have
looked like two findings in every future packet build over this subject.

The stale row was deleted under a guard that read the FK closure first
(`scoring.evidence → research.opportunity_hypothesis_evidence`, CASCADE) and
refused unless it could show zero Opportunity hypotheses cited it and exactly one
successor survived. Both held.

**The general lesson:** a version identifier inside an idempotency key means a
re-derivation after any version change is an INSERT, not a no-op. `scoring.evidence`
has no `superseded_at`, so there was no supersession to record and deletion was
the only instrument available.

### 2.2 The new Evidence formed its own packet

`subject_key` recognised `community_question_volume` and nothing else, so the new
row got a source-native key of its own and became a tenth packet — a Docker
measurement sitting outside the Docker packet.

Fixed in `source-native-subject-grouping@1.2.0` by listing both signal types
explicitly rather than prefix-matching `community_question_*`: a future
`community_question_…` type might legitimately be about something else, and would
have joined this packet by accident.

**The general lesson:** which *measurement* was taken over a subject is not part
of the subject's identity. Grouping keys must be updated when a second
measurement over the same subject arrives, and nothing else in the pipeline
signals that they need to be.

---

## 3. Tests

Three files, 68 tests added, all passing.

- [`test_answer_acceptance_evidence.py`](../../packages/opportunity-engine/python/tests/test_answer_acceptance_evidence.py)
  — the frozen assessment exists and decides; the mapping is empty *and
  registered*; each forbidden implication asserted separately; the real packet
  went 7 → 8 with counting dimensions unchanged; a zero-dimension row can never
  make a packet formable; the parked classifier stays unreachable.
- [`test_community_question_acceptance.py`](../../services/nlp/python/tests/test_community_question_acceptance.py)
  — the extractor. A missing flag refuses **even when two good records remain**;
  a non-boolean value counts as absent; an untagged record's missing flag does
  not block; accepted questions are excluded; truncation is judged on the whole
  retrieval and not the counted subset; the window carries `NONE` basis and
  `NOT_APPLICABLE` direction.
- [`test_claim_interpreter.py`](../../services/nlp/python/tests/test_claim_interpreter.py)
  — the restatement. It asserts a set and never a share; the window binds to
  *created*, the acceptance state to *observed*; the words `unanswered`,
  `unsolved`, `unresolved`, `outstanding`, `gap`, `dissatisf`, `pain`, `demand`
  and `need` appear nowhere in the statement.

### Tests repaired, none weakened

Six existing assertions failed because this mission legitimately changed what
they pinned. Each was repaired by keeping the property and dropping the
incidental number:

| Test | Was | Now |
|---|---|---|
| `test_independence_is_still_unknown_across_two_families` | `"7 of 7"` | derived from the packet's own size |
| `test_exactly_one_evidence_row_was_added` | `== 27` (a global count read as a delta) | renamed; `>= 27` plus `eligible_context == inspected` and `eligible_scoring == 0` |
| `test_the_run_records_the_registry_it_grouped_under` | grouping `== "…@1.1.0"` | `== GROUPING_PROCEDURE_VERSION` |
| `test_the_interpretation_is_deterministic_and_names_no_model` | `== "1.3.0"` | `== INTERPRETER_VERSION` |
| `test_it_is_observed_and_deterministic` | `== "1.3.0"` | `== INTERPRETER_VERSION` |
| `test_claim_revision_and_evidence_are_written_together` | `== "1.3.0"` | `== INTERPRETER_VERSION` |
| `test_the_existing_extractors_are_untouched` | 6-name equality | 7-name equality, the new name commented |

The last one is the only test that was *supposed* to fail: it is a deliberate
equality over the extractor registry, and it exists so that a seventh extractor
cannot appear without somebody writing down that it should.

The sufficiency rule was **not** touched: `opportunity-sufficiency@1.0.0`,
frozen, still pinned as a literal because a test that read it from the module
could not tell if it moved.

---

## 4. CI-equivalent verification

All run locally, all passing:

| Gate | Result |
|---|---|
| `generate.py --check` | ok, 2 artifacts |
| `run_python_tests.py` | OK |
| `validate_schema.py` | 9 invariant groups, 43 tables |
| `migrate.py --plan` | well formed, ledger at 0031 |
| `validate_source_registry.py` | 29 sources, 42 evidence records, 0 warnings |
| `validate_compliance_capabilities.py` | 34 conditions, 13 approving pairs |
| `validate_normalization.py` | 9 boundary groups |
| `validate_signals.py` | 7 boundary groups |
| `validate_claims.py` | 11 boundary groups |
| `validate_evidence_aggregation.py` | 8 checks, scoring still blocked |
| network-client grep guard | no offenders |
| collector-in-governance grep guard | no offenders |
| `ruff check` / `ruff format --check` | clean, 575 files |
| `mypy` (13 packages) | no issues, 185 source files |
| `sros-source render --check` and 3 other generated docs | all match |
| `run_pytest_suites.py` | passed across 9 packages; database unchanged across 26 tenant tables |

TypeScript gates were not re-run: no TypeScript changed, and the contracts
generator's `--check` confirms the shared schema is untouched.
