# Mission 1.79 — The first Opportunity is not entitled to the budget

**Outcome: `SECOND_OPPORTUNITY_EXPLORATION_IS_NEXT_BOUNDED_MOVE`.**

Six linked rows became scorable and the docker hypothesis did not become one word stronger.
Every move that would add a dimension it lacks is blocked by a judgement, a parked relation,
a restricted source class or an architectural grain mismatch; every move that is executable
adds rows to one saturated shape. The corpus holds one packet with a different shape, and
looking at it is the highest-information bounded move.

---

## Report

```
START_COMMIT                      = 170dd64
MIGRATION_HEAD                    = 0036_grant_use_profile_vocabulary (measured)
CURRENT_OPPORTUNITY_ID            = 06113a8b-a83d-423d-8046-18f87d7dbc01
CURRENT_REVISION_ID / NUMBER      = 8739e7ab-940b-408c-a5e8-7f6675d1597c / 2  (revision 1 efca07a9 still readable)
TOTAL_EVIDENCE / SCORABLE         = 58 / 48
CURRENT_LINKED / SCORABLE / NON   = 7 / 6 / 1
CURRENT_SCORABLE_SOURCES          = 1 (wikimedia-pageviews)
CURRENT_SCORABLE_SOURCE_FAMILIES  = 1 (knowledge)
CURRENT_SCORABLE_DIMENSIONS       = AUDIENCE_OR_USAGE (+ TREND_OR_CHANGE, which never counts)
CURRENT_INDEPENDENCE_GROUPS       = 0        CURRENT_PROFILE_CALIBRATION_STATE = UNCALIBRATED
CURRENT_SCORE_STATE               = ABSENT
PACKET_SCORING_READY              = true     AGGREGATION_PROFILE_CALIBRATED = false
PERSISTED_SCORING_AUTHORIZED      = false    INDEPENDENCE_ESTABLISHED = false
COMMERCIAL_VALIDATION_ESTABLISHED = false
SCORABLE_ROWS / SOURCES / FAMILIES / COUNTING_DIMENSIONS / PROVENANCE_GROUPS = 6 / 1 / 1 / 1 / 1
SCORABLE_DIMENSION_DIVERSITY      = false
M1_RESULT = VETOED (EXECUTABLE_AFTER_OPERATOR_JUDGMENT, bottleneck BOTH)
M2_RESULT = VETOED (RESEARCH_REQUIRED_BEFORE_EXECUTION, parked relation), on the frontier
M3_RESULT = FRONTIER, not selected (EXECUTABLE_AFTER_GOVERNANCE_WORK, then acquisition)
M4_RESULT = VETOED (rows without a dimension or a source)
M5_RESULT = VETOED, PARKED (no deciding predicate emerged since 1.76.7)
M6_RESULT = SELECTED (EXECUTABLE_NOW_HELD_DATA_ONLY)
PARETO_FRONTIER                   = M2, M3, M6        DOMINATED = M1, M4, M5 (M1, M4 by M6; M5 by M3)
VETOED_CANDIDATES                 = M1, M2, M4, M5
CURRENT_OPPORTUNITY_MARGINAL_INFORMATION_VALUE = LOW   SECOND_OPPORTUNITY_EXPLORATION_VALUE = MEDIUM
SELECTED_NEXT_MOVE                = M6_SECOND_OPPORTUNITY
PRIMARY_OUTCOME                   = SECOND_OPPORTUNITY_EXPLORATION_IS_NEXT_BOUNDED_MOVE
RECOMMENDED_NEXT_MISSION          = 1.80 Second Opportunity Candidate Selection V1
CANONICAL_MUTATION = 0   EXTERNAL_ACTIONS = 0   MODEL_CALLS = 0   MEASUREMENTS = 0
VIOLATIONS_CAUGHT / ESCAPED       = 46 / 0    positive controls 4 of 4
```

Preconditions verified: tree clean, `main` == `origin/main` at `170dd64`, Missions 1.77 and
1.78 merged, current reader returns revision 2 and the historical reader revision 1,
preparation v2 current and v1 preserved, counters as reconciled (1 / 2 / 14, assessments 4,
groups 0, scores ABSENT, embeddings 0), Q1 CLASS_SELECTED without construct or run,
Globalping 12/0/0, V2 selected with corpus false and measurements 0. All re-measured.

## Scoring-ready is not scoring

`scoring_ready` is `scoring_eligible_rows >= 2`, a property of the packet, and the docker
packet reads true at 12 of 14. It is not calibrated (`REFERENCE_PROFILE_V1` UNCALIBRATED),
not an authorisation to persist or rank (no scores table exists), not independence (0 groups,
UNKNOWN on every linked row) and not commercial validation (no commercial dimension on the
subject). Five questions, five gates, one answer each.

## What the six scorable rows are

Six adjacent-day request differences for one Wikipedia article under one heuristic
requester class, each resolved at 0.65 against one assessment, each with one support group
of UNKNOWN provenance, all sharing one publisher, one pipeline and one counting rule.
**One source, one family, one counting dimension, one provenance shape.** The second counting
dimension the Opportunity has, PROBLEM_OR_NEED, sits on the one row that is not scorable. So
`SCORABLE_DIMENSION_DIVERSITY` is false: six scorable rows are not six kinds of evidence, and
they are not six observations either.

## The dimension matrix

Supported and scorable: AUDIENCE_OR_USAGE (and TREND_OR_CHANGE, excluded from diversity
because every derived row carries change). Supported as context only: PROBLEM_OR_NEED.
Unsupported inference, deliberately: RECURRENCE_OR_FREQUENCY (88 questions are neither 88
people nor one problem 88 times) and SOLUTION_GAP (an unaccepted question is an absence of
evidence of a solution). Absent: dissatisfaction, market activity, buyer or budget, economic
value, willingness to pay, competitive supply, distribution, regulatory driver, feasibility.
Severity and adoption have no taxonomy member and were not manufactured.

## Six candidates

| | status | the finding |
|---|---|---|
| **M1** Stack Exchange scorable | after operator judgement | the operator answered NO in 1.36.1 for want of reachable documentation, and nothing new is held; the bottleneck is **BOTH**, and a scorable count of published questions would change no decision. Vetoed: a weak proposition made numerically usable. |
| **M2** problem strength | research required | the dimensions the hypothesis needs most, behind a closed deterministic route (1.20, 1.21), a parked classifier (1.27) and a restricted source class (1.22). On the frontier and vetoed. |
| **M3** commercial for docker | after governance, then acquisition | no held docker row carries a commercial dimension; the sources that do observe CATEGORY scopes, and no reviewed relation binds docker to one (1.35, registry empty); product-grain sources are RESTRICTED (1.33). The most decision-relevant candidate and the least reachable. Frontier. |
| **M4** the seven uncited rows | after operator judgement | six convergent re-reads of the same six measurements and one zero-dimension row: no dimension, no provenance, no scorability change. Vetoed: rows without a dimension or a source. |
| **M5** Q1 independence | parked | nothing merged since 1.76.7 reveals a predicate that decides rather than samples; Globalping's qualification is not independence. Dominated by M3 on every field, which the gate noticed and the author had not. |
| **M6** second Opportunity | executable now | the corpus holds one packet with a different shape: `ted-eu:CPV-division:92`, 10 rows, all scorable at reviewed 0.5 and 0.55, three commercial counting dimensions, formable, behind one governance question (ted-eu egress NOT_ASSESSED) and a CATEGORY-scope subject. Selected. |

**The trade-off, stated.** M3 carries the single most decision-relevant dimension for the
existing hypothesis and loses on reachability, not value: two governance decisions and an
acquisition, against a grain mismatch Mission 1.33 found architectural. M6 reaches three
commercial dimensions from rows already held, reviewed and scorable, with one governance
question in front of synthesis and none in front of selection. An executable move that opens
a second hypothesis defeats a theoretically better move that cannot start.

**Dominance was recomputed by the gate, twice against the author.** The first record left
M2 off the frontier; nothing dominates its dimension and semantic gains, so it belongs there,
vetoed. The second record did not list M5 as dominated; M3 dominates it on every field and
strictly on three. Both corrections went into the record, not into the gate.

## Three tests

- **Stack Exchange.** With a valid assessment, PROBLEM_OR_NEED would become the packet's
  second scorable counting dimension. Still unsupported after that: recurrence, severity,
  dissatisfaction, solution gap, actor, buyer, budget, willingness to pay, competitive supply,
  distribution, feasibility, independence. It would change the product decision less than a
  commercial or problem-strength dimension. Bottleneck **BOTH**, and the leftover non-scorable
  row is not the next row to fix.
- **Wikimedia saturation.** Six uncited same-shape rows are held. Same family, independence
  unestablished, same dimensions, one support group per Claim so the aggregator is the
  pass-through (1.43, re-measured in 1.77). More Wikimedia is dominated.
- **Second Opportunity.** Marginal value of the first: **LOW**. Exploration value: **MEDIUM**,
  not HIGH, because the leading held candidate is a procurement category whose product
  relevance is uncertain and whose synthesis waits on an egress decision, and the other held
  candidates (kubernetes, podman) are the docker shape with fewer dimensions. Diminishing
  returns: yes. Sunk effort counted: no.

## Verification

- Probe: **46 deliberate violations, 46 caught, 0 escaped**, plus **4 of 4 positive
  controls**: a Stack Exchange winner whose bottleneck is reliability alone, a commercial
  winner, the shipped second-Opportunity winner and the no-move outcome, so the gate enforces
  the selection rule rather than this mission's verdict. One control was itself wrong at first:
  it constructed a Stack Exchange winner that M6 dominated, and the gate refused it correctly.
- **3560 bare-python tests**; pytest suites green with the database unchanged; `ruff format
  --check`, `ruff check`, mypy over 198 files; contract and catalog `--check`; all **58** CI
  gates, one of them new.
- Counters identical before and after: nothing canonical moved, no model, no external call.

## Next

**Mission 1.80 — Second Opportunity Candidate Selection V1**: held data first, rank the held
non-docker packets as candidates for a bounded Opportunity preparation, select exactly one
candidate subject, record its blockers, and STOP before any model synthesis and before any
Opportunity is created. It must not create Opportunity #2, call a model, acquire data, decide
the ted-eu egress question on the operator's behalf, or score or rank. **It was not started.**
