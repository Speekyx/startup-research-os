# After the reconciliation, what is the next bounded move?

Generated from `post-reconciliation-evidence-priority-v1.json`. Do not edit by hand.

**SECOND_OPPORTUNITY_EXPLORATION_IS_NEXT_BOUNDED_MOVE** — selected `M6_SECOND_OPPORTUNITY`, next 1.80 Second Opportunity Candidate Selection V1.

## Scoring-ready is not scoring

| | |
|---|---|
| PACKET_SCORING_READY | True |
| AGGREGATION_PROFILE_CALIBRATED | False |
| PERSISTED_SCORING_AUTHORIZED | False |
| INDEPENDENCE_ESTABLISHED | False |
| COMMERCIAL_VALIDATION_ESTABLISHED | False |

## The scorable shape

6 scorable rows, 1 source, 1 family, 1 counting dimension, 1 provenance shape. Scorable dimension diversity: **False**. six scorable rows carry one counting dimension from one source in one family; the second counting dimension the Opportunity has (PROBLEM_OR_NEED) sits on the one row that is not scorable

## Dimension matrix

| dimension | classification |
|---|---|
| AUDIENCE_OR_USAGE | `SUPPORTED_SCORABLE` |
| PROBLEM_OR_NEED | `SUPPORTED_CONTEXT_ONLY` |
| TREND_OR_CHANGE | `SUPPORTED_SCORABLE` |
| RECURRENCE_OR_FREQUENCY | `UNSUPPORTED_INFERENCE` |
| SEVERITY_OR_COST (brief name) | `NOT_APPLICABLE` |
| SOLUTION_GAP | `UNSUPPORTED_INFERENCE` |
| SOLUTION_DISSATISFACTION | `ABSENT` |
| COMMERCIAL_ACTIVITY (brief name) -> MARKET_ACTIVITY | `ABSENT` |
| BUYER_OR_ACTOR_IDENTITY (brief name) -> BUYER_OR_BUDGET_EXISTENCE | `ABSENT` |
| BUDGET_OR_SPEND (brief name) -> ECONOMIC_VALUE | `ABSENT` |
| WILLINGNESS_TO_PAY | `ABSENT` |
| MARKET_ACTIVITY | `ABSENT` |
| ADOPTION (brief name) | `NOT_APPLICABLE` |
| COMPETITIVE_SUPPLY | `ABSENT` |
| DISTRIBUTION_SIGNAL | `ABSENT` |
| REGULATORY_OR_STRUCTURAL_DRIVER | `ABSENT` |
| FEASIBILITY_SIGNAL | `ABSENT` |

## Candidates

| candidate | status | dimension | scorability | sources | independence | commercial | impact | cost | dependency | result |
|---|---|---|---|---|---|---|---|---|---|---|
| `M1_STACK_EXCHANGE_RELIABILITY` | `EXECUTABLE_AFTER_OPERATOR_JUDGMENT` | NONE | LOW | NONE | NONE | NONE | LOW | MEDIUM | HUMAN | **VETOED** |
| `M2_PROBLEM_STRENGTH` | `RESEARCH_REQUIRED_BEFORE_EXECUTION` | HIGH | LOW | MEDIUM | NONE | NONE | HIGH | HIGH | ARCHITECTURE | **VETOED** |
| `M3_COMMERCIAL_BUYER_WTP` | `EXECUTABLE_AFTER_GOVERNANCE_WORK` | HIGH | MEDIUM | HIGH | POTENTIAL | HIGH | CRITICAL | HIGH | ACQUISITION | **FRONTIER** |
| `M4_HELD_UNUSED_EVIDENCE` | `EXECUTABLE_AFTER_OPERATOR_JUDGMENT` | NONE | NONE | NONE | NONE | NONE | LOW | LOW | HUMAN | **VETOED** |
| `M5_Q1_INDEPENDENCE` | `PARKED` | NONE | NONE | HIGH | POTENTIAL | NONE | MEDIUM | HIGH | ARCHITECTURE | **VETOED** |
| `M6_SECOND_OPPORTUNITY` | `EXECUTABLE_NOW_HELD_DATA_ONLY` | HIGH | HIGH | HIGH | NONE | HIGH | HIGH | LOW | NONE | **SELECTED** |

Frontier ['M2_PROBLEM_STRENGTH', 'M3_COMMERCIAL_BUYER_WTP', 'M6_SECOND_OPPORTUNITY']; dominated ['M1_STACK_EXCHANGE_RELIABILITY', 'M4_HELD_UNUSED_EVIDENCE', 'M5_Q1_INDEPENDENCE']; vetoed ['M1_STACK_EXCHANGE_RELIABILITY', 'M2_PROBLEM_STRENGTH', 'M4_HELD_UNUSED_EVIDENCE', 'M5_Q1_INDEPENDENCE'].

M3 carries the single most decision-relevant dimension for the existing hypothesis and is the only frontier candidate other than the winner. It loses on reachability, not on value: it needs a governance decision on a product-grain source or a reviewed category relation nobody found an authority for, and then an acquisition, against a grain mismatch Mission 1.33 found architectural. M6 reaches three commercial dimensions from rows already held, reviewed and scorable, with one governance question in front of synthesis and none in front of selection. An executable move that opens a second hypothesis defeats a theoretically better move that cannot start.

## Three tests

- **Stack Exchange.** Bottleneck `BOTH`: MISSING_RELIABILITY is real (NO_APPLICABLE_ASSESSMENT, declined by the operator for want of reachable documentation) and WEAK_PROPOSITION_INFORMATION is the larger half: 'questions were published' is the proposition whatever its reliability, and a scorable version of it changes no decision
- **Wikimedia saturation.** More same-shape rows dominated: True. another witness of one publisher's counting rule raises observed volume and not evidence strength; it cannot add a dimension, a family, a provenance group or a falsifier
- **Second Opportunity.** Marginal value of the first `LOW`, exploration value `MEDIUM`. every move that would add a dimension the docker hypothesis lacks is blocked by an operator judgement, a parked relation, a restricted source class or an architectural grain mismatch; every move that is executable adds rows to one saturated shape the leading held candidate is a CATEGORY-scope procurement subject whose product relevance is uncertain and whose synthesis is behind one egress decision; the other held candidates are the docker shape with fewer dimensions

**Next: Second Opportunity Candidate Selection V1.** held data first: rank the held non-docker packets as candidates for a bounded Opportunity preparation, select exactly one candidate subject, record its blockers (for the leading candidate, ted-eu external_model_transmission NOT_ASSESSED and a CATEGORY-scope subject), and STOP before any model synthesis and before any Opportunity is created
