# Candidate evidence-completion moves

Generated from `evidence-completion-candidate-moves-v1.json`. Do not edit by hand.

Generated only from facts the repository already holds. No source was discovered and nothing was acquired.

| id | move | subject relation | contribution | gain | governance | collector |
|---|---|---|---|---|---|---|
| **M1** | Bind the Wikimedia measurement resource so the reviewed reliability resolves | `DIRECT` | `RELIABILITY_OR_SCORABILITY_COMPLETION` | `DECISION_CHANGING` | `NOT_APPLICABLE_NO_ACQUISITION` | `HELD_DATA_ALREADY_AVAILABLE` |
| **M2** | Apply the already-resolving TED reliability to its Evidence rows | `NOT_THE_SAME_SUBJECT` | `RELIABILITY_OR_SCORABILITY_COMPLETION` | `LOW_INCREMENTAL_GAIN` | `NOT_APPLICABLE_NO_ACQUISITION` | `HELD_DATA_ALREADY_AVAILABLE` |
| **M3** | Reliability review for the Stack Exchange tagged-question scope | `DIRECT` | `RELIABILITY_OR_SCORABILITY_COMPLETION` | `MODERATE_BREADTH_GAIN` | `READY_WITH_EXISTING_CONDITIONS` | `HELD_DATA_ALREADY_AVAILABLE` |
| **M4** | Derive claims from the 120 held TED normalized records that feed no signal | `NOT_THE_SAME_SUBJECT` | `MORE_SAME_DIMENSION_SAME_LINEAGE` | `LOW_INCREMENTAL_GAIN` | `READY_NOW` | `HELD_DATA_ALREADY_AVAILABLE` |
| **M5** | Derive claims from the 16 held Stack Exchange records that feed no signal | `DIRECT` | `MORE_SAME_DIMENSION_SAME_LINEAGE` | `LOW_INCREMENTAL_GAIN` | `READY_WITH_EXISTING_CONDITIONS` | `HELD_DATA_ALREADY_AVAILABLE` |
| **M6** | Bounded LOCAL governance review for one developer-ecosystem source | `UNDETERMINED` | `NEW_DECISION_RELEVANT_DIMENSION` | `UNKNOWN` | `BOUNDED_REVIEW_REQUIRED` | `COLLECTOR_NOT_IMPLEMENTED_BUT_RESOURCE_READY` |

## M1 — Bind the Wikimedia measurement resource so the reviewed reliability resolves

- **subject:** wikimedia content ids: Docker_(software), Kubernetes, Podman
- **relevance to the Opportunity:** six of the seven Evidence rows linked to the only Opportunity are Wikimedia pageview rows
- **source:** `wikimedia-pageviews` (knowledge), assessed under `local-private-research-v1`
- **independence potential:** `UNKNOWN`
- **commercial relevance:** `NOT_ESTABLISHED`
- **evidence value / scorability / reliability work:** `HIGH` / `NON_SCORABLE_TODAY` / `NONE_THE_REVIEW_ALREADY_EXISTS`
- **external action required:** False

**Why it could change a decision.** no aggregation is possible over this hypothesis at all today. After the move, aggregation over its Wikimedia rows is possible, and the Opportunity's leading stated limitation stops being true as written.

**Why it might fail.** if resource identity turns out not to be deterministically recoverable for every held Wikimedia record, the binding would be an assignment rather than a derivation, and assigning a resource to a record that does not state one is inventing lineage. The move must refuse in that case rather than proceed.

**Blockers.**

- the seventh linked Evidence row is stack-exchange, whose scope has no assessment, so the packet becomes PARTLY scorable and not wholly
- resource_id is absent from the whole acquisition lineage and appears only in the assessment and, for other sources, inside proposition_facts
- the 34 Wikimedia claims are frozen and their proposition_key is derived from proposition_facts, so editing them to add resource_id would change claim identity. The move must resolve at read time from the committed collector constant rather than rewriting frozen claims

## M2 — Apply the already-resolving TED reliability to its Evidence rows

- **subject:** EU public procurement notices, CPV division 90
- **relevance to the Opportunity:** none: no TED Evidence row is linked to the Opportunity
- **source:** `ted-eu` (public_procurement), assessed under `local-private-research-v1`
- **independence potential:** `UNKNOWN`
- **commercial relevance:** `DIRECT_MARKET_ACTIVITY_SIGNAL`
- **evidence value / scorability / reliability work:** `MODERATE` / `RESOLVES_TODAY_BUT_UNWRITTEN` / `NONE_THE_REVIEW_ALREADY_EXISTS_AND_ALREADY_RESOLVES`
- **external action required:** False

**Why it could change a decision.** it could not, today. It would prepare TED evidence for a hypothesis that does not exist yet.

**Why it might fail.** it cannot fail; it is simply not decision-relevant now

**Blockers.**

- no Opportunity consumes TED Evidence

## M3 — Reliability review for the Stack Exchange tagged-question scope

- **subject:** stackoverflow tag 'docker'
- **relevance to the Opportunity:** the seventh and only non-Wikimedia Evidence row on the Opportunity
- **source:** `stack-exchange` (forum), assessed under `local-private-research-v1`
- **independence potential:** `PLAUSIBLE_DISTINCT_LINEAGE_REVIEW_REQUIRED`
- **commercial relevance:** `DIRECT_PROBLEM_OR_NEED_SIGNAL`
- **evidence value / scorability / reliability work:** `HIGH` / `NON_SCORABLE_TODAY` / `A_FULL_REVIEW_WITH_DOCUMENT_BACKED_BASIS`
- **external action required:** True

**Why it could change a decision.** it would make the Opportunity's only problem-or-need row scorable, which no other move does.

**Why it might fail.** the reviewer may conclude the measurement's scope cannot be bounded, and a refusal is a legitimate outcome of a review.

**Blockers.**

- an assessment must rest on at least one retrieved first-party document, so this requires an external documentation retrieval next mission

## M4 — Derive claims from the 120 held TED normalized records that feed no signal

- **subject:** EU public procurement notices
- **relevance to the Opportunity:** none
- **source:** `ted-eu` (public_procurement), assessed under `local-private-research-v1`
- **independence potential:** `KNOWN_DEPENDENT`
- **commercial relevance:** `DIRECT_MARKET_ACTIVITY_SIGNAL`
- **evidence value / scorability / reliability work:** `LOW` / `WOULD_RESOLVE` / `NONE`
- **external action required:** False

**Why it could change a decision.** it could not; MORE ROWS IS NOT MORE INFORMATION

**Why it might fail.** not applicable

## M5 — Derive claims from the 16 held Stack Exchange records that feed no signal

- **subject:** stackoverflow questions
- **relevance to the Opportunity:** same dimension as the Opportunity's existing problem-or-need row
- **source:** `stack-exchange` (forum), assessed under `local-private-research-v1`
- **independence potential:** `KNOWN_DEPENDENT`
- **commercial relevance:** `DIRECT_PROBLEM_OR_NEED_SIGNAL`
- **evidence value / scorability / reliability work:** `LOW` / `NON_SCORABLE_TODAY` / `A_FULL_REVIEW`
- **external action required:** False

**Why it could change a decision.** it could not

**Why it might fail.** not applicable

**Blockers.**

- the same missing assessment as M3

## M6 — Bounded LOCAL governance review for one developer-ecosystem source

- **subject:** Docker as a software ecosystem
- **relevance to the Opportunity:** would target dimensions the Opportunity explicitly records as unsupported
- **source:** `github, npm-registry, pypi or huggingface` (developer), assessed under `local-private-research-v1`
- **independence potential:** `PLAUSIBLE_DISTINCT_LINEAGE_REVIEW_REQUIRED`
- **commercial relevance:** `INDIRECT_PRODUCT_CONTEXT`
- **evidence value / scorability / reliability work:** `UNKNOWN` / `NOT_REACHED` / `A_FULL_REVIEW_AFTER_A_GOVERNANCE_REVIEW`
- **external action required:** True

**Why it could change a decision.** it targets dimensions the Opportunity names as unsupported, which is where the hypothesis is actually thin.

**Why it might fail.** the review may refuse, the subject relation may not be establishable, and three sequential steps is not one bounded mission.

**Blockers.**

- no LOCAL policy review exists for any developer-family source
- no collector is implemented for any of them
- the subject relation to the current Docker subject is UNDETERMINED

## The registered-source gap

the eight sources reviewed under local-private-research-v1 are two knowledge sources, one forum, one news source, one procurement source and three economic-data sources. None measures what an actor would pay, and procurement value is not willingness to pay for a product hypothesis.

Dimensions no reviewed source currently reaches: `WILLINGNESS_TO_PAY`, `BUYER_OR_BUDGET_EXISTENCE for the Docker subject`, `SOLUTION_DISSATISFACTION`, `SOLUTION_GAP`.

## Eliminated before ranking

- **M7** — An independent Globalping measurement experiment. C9 remains PARTIAL and the counterpart is COUNTERPART_UNRESOLVED, so no route is qualified. It is recorded as a DEPENDENCY, not a candidate: a future qualification could unlock an independent measurement, and this mission may not select it.
- **M8** — Any unregistered source that could supply willingness-to-pay. no registered source can speak to WILLINGNESS_TO_PAY for this hypothesis, and this mission may not introduce one. Recorded as REGISTERED_SOURCE_GAP.


## Forward pointer

Appended by Mission 1.77; nothing above it changed. See `docs/data/wikimedia-measurement-scope-binding-v1.json`.

M1's blocker 'resource_id is absent from the whole acquisition lineage' is FALSE: every RawRecord carries provenance.resource_id, reachable through signal_inputs, and the real resolver resolves all 36 Wikimedia rows through it. The proposed fix (map the collector lineage to the committed WM_RESOURCE_ID constant) is unnecessary and is the hard-coded source exception Mission 1.77 forbids. What was actually missing is late resolution on the Opportunity path, which read a NULL column.
