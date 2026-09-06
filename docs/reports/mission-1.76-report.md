# Mission 1.76 — Opportunity evidence breadth prioritization

**Primary outcome: `NEXT_BOUNDED_EVIDENCE_MOVE_SELECTED` — candidate M1.**

    MORE ROWS IS NOT MORE INFORMATION.

Nothing was acquired, no model was called, no embedding was made, and the canonical
research state is byte-identical before and after.

---

## The finding

The only Opportunity's first named limitation says **"no reviewed reliability applies, so
this hypothesis can contribute to no score."**

That reads as *nobody has reviewed this*. **A reviewed assessment already exists**, at
0.65 and 0.6, for exactly the measurement and purpose its six Wikimedia rows carry. It
does not apply for a different reason: the Evidence **cannot state its resource identity**,
so the repository's own `resolve_reliability` returns `NO_APPLICABLE_ASSESSMENT` with the
detail *"this evidence record cannot state its measurement-and-purpose scope"*.

Run against held data, the same function **resolves cleanly for TED** — whose claims carry
`resource_id` in their `proposition_facts` — and fails for Wikimedia and Stack Exchange,
whose claims do not, and whose acquisition lineage carries no `resource_id` column at all.

So the corpus is **one deterministic binding away from its first scorable evidence**, and
the blocker was mis-stated as a missing review.

## The required output

```
SUBJECTS_AUDITED                    = 9
OPPORTUNITIES_AUDITED               = 1
CLAIMS_AUDITED                      = 44
EVIDENCE_ROWS_AUDITED               = 58
DISTINCT_EVIDENCE_DIMENSIONS        = 10   (proposition kinds, not rows)
SCORABLE_EVIDENCE_ROWS              = 0
NON_SCORABLE_EVIDENCE_ROWS          = 58
ESTABLISHED_INDEPENDENCE_GROUPS     = 0
CANDIDATE_MOVES_CONSIDERED          = 8
CANDIDATE_MOVES_ELIGIBLE_FOR_PRIORITY = 6
TIER_1_COUNT                        = 1
TIER_2_COUNT                        = 0
TOP_CANDIDATE                       = M1
TOP_CANDIDATE_TARGET_DIMENSION      = none; it targets SCORABILITY
TOP_CANDIDATE_SOURCE                = wikimedia-pageviews, already held
TOP_CANDIDATE_INFORMATION_GAIN      = DECISION_CHANGING
TOP_CANDIDATE_GOVERNANCE_STATE      = NOT_APPLICABLE_NO_ACQUISITION
TOP_CANDIDATE_COLLECTOR_STATE       = HELD_DATA_ALREADY_AVAILABLE
TOP_CANDIDATE_INDEPENDENCE_POTENTIAL = UNKNOWN
TOP_CANDIDATE_BLOCKERS              = the seventh linked row has no assessment;
                                      resource_id is absent from the lineage;
                                      frozen claims may not be rewritten
DOMINATED_BY_ANOTHER                = false
NEXT_BOUNDED_MISSION                = 1.77 Wikimedia Measurement Scope Binding V1
```

## The 52 answers

| # | question | answer |
|---|---|---|
| 1 | start commit | `9b7e1d9` |
| 2 | branch | `sprint-1/mission-1.76` |
| 3 | migration head | `0036_grant_use_profile_vocabulary` |
| 4 | canonical baseline | matches the expected values exactly; see the table below |
| 5 | subjects audited | 9 subject tokens: `Docker_(software)`, `Kubernetes`, `Podman`, `docker` (SO tag), CPV divisions `90` and `92`, `SP.POP.TOTL`, `climate`, `weather` |
| 6 | opportunities audited | 1 |
| 7 | current hypothesis | `subject:docker`, target actor `UNKNOWN_NOT_SUPPORTED`, 2 supported and 12 unsupported dimensions |
| 8 | claims by subject | 44 claims; 25 wikimedia, 10 ted-eu, 4 world-bank, 3 gdelt, 2 stack-exchange |
| 9 | evidence by subject | 58 rows; 37 wikimedia, 12 ted-eu, 4 world-bank, 3 gdelt, 2 stack-exchange |
| 10 | evidence dimensions | 10 distinct proposition kinds; **every row is `UNCATEGORISED` on `observation_category`** |
| 11 | source families | 5 under LOCAL: knowledge, forum, news, public_procurement, economic_data |
| 12 | scorable / non-scorable | **0 / 58** |
| 13 | reliability coverage | 4 assessments covering 4 of the 10 lineages; **none applied** |
| 14 | established independence groups | **0** |
| 15 | sufficiency blockers | 5, quoted verbatim in the audit page; the first is the scorability one |
| 16 | held-but-unused data | 120 of 188 TED and 16 of 104 Stack Exchange normalized records feed no signal |
| 17 | implemented collectors | 5 (`wikimedia-pageviews-per-article`, `ted-search-api`, `stack-exchange-questions`, `gdelt-web-ngram`, `world-bank-indicators`); **only `ted-eu` is enabled**, under LOCAL |
| 18 | eligible under LOCAL | 8 of 29 sources reviewed; 4 with zero unsatisfied conditions (eurostat, fred, ted-eu, world-bank) |
| 19 | resource-ready | the same 4; the other 4 carry unsatisfied conditions |
| 20 | candidate moves generated | 8, of which 2 eliminated before ranking |
| 21 | contribution classes | 1 dimension move, 3 scorability moves, 2 more-of-the-same, 2 not-established |
| 22 | which add new dimensions | **only M6**, and it is not executable |
| 23 | which add more of the same | M4 and M5 |
| 24 | independence potential | UNKNOWN (M1, M2), PLAUSIBLE_REVIEW_REQUIRED (M3, M6), KNOWN_DEPENDENT (M4, M5) |
| 25 | governance readiness | see the candidate page; none borrowed from another profile |
| 26 | collector readiness | M1–M5 held data; M6 has no collector |
| 27 | commercial relevance | no candidate claims a buyer or a price |
| 28 | information gain | DECISION_CHANGING (M1), MODERATE (M3), LOW (M2, M4, M5), UNKNOWN (M6) |
| 29 | priority tier | T1: M1. T3: M3, M6. T4: M2, M4, M5. **T2 empty** |
| 30 | dominance | M1 dominates M2, M4, M5; neither dominates between M1 and M3, or M1 and M6 |
| 31 | top candidate | **M1** |
| 32 | uniquely dominant | **no** |
| 33 | if not, why not | M3 beats it on independence potential, M6 on adding a dimension. Dominance is the veto, not the selection rule: M1 is dominated by nothing and is the only member of tier 1 |
| 34 | exact target | **SCORABILITY**, not a dimension |
| 35 | exact subject | the Wikimedia pageview lineage, including the six rows on the Opportunity |
| 36 | exact source | `wikimedia-pageviews`, already held |
| 37 | what it can establish | that a reviewed reliability applies; that aggregation becomes reachable |
| 38 | what it cannot | independence, any new dimension, willingness to pay, whole-packet scorability, or a score |
| 39 | external action next mission | **no** |
| 40 | source newly registered | **no** |
| 41 | governance changed | **no** |
| 42 | research API called | **no** |
| 43 | model call | **no** |
| 44 | embedding | **no** |
| 45 | Claim/Evidence/Opportunity mutation | **no** |
| 46 | independence group created | **no** |
| 47 | Globalping before/after | unchanged: 11 PASS / 1 PARTIAL / 0 FAIL, `COUNTERPART_UNRESOLVED`, not checked externally |
| 48 | canonical counters | identical, see below |
| 49 | mutation probe | **46 attempted, 46 caught, 0 escaped, 3 of 3 controls** |
| 50 | tests | see below |
| 51 | primary outcome | `NEXT_BOUNDED_EVIDENCE_MOVE_SELECTED` |
| 52 | recommended next | Mission 1.77 — Wikimedia Measurement Scope Binding V1 |

## Why M1 and not the alternatives

**Docker was not privileged for having an Opportunity row.** M2 and M4 attach to no
Opportunity and were ranked on their own terms; they lost on information gain, not on
lacking a row. And the Docker hypothesis was measured against every other subject holding
Evidence — Kubernetes and Podman carry Wikimedia rows of the same lineage, and the TED,
World Bank and GDELT subjects carry different lineages that no hypothesis consumes.

**Tier 2 is empty, and that emptiness is the finding.** No candidate both adds a currently
absent decision-relevant dimension *and* is executable now. M6 would add one and needs a
governance review, a collector and a normalizer first. Every executable candidate completes
scorability rather than adding a dimension.

**M1 is not uniquely dominant, and the record says so.** §14 makes dominance a **veto**, not
the selection rule: a dominated candidate cannot win, and M1 is dominated by nothing. The
tier then decides, and M1 is alone in tier 1.

## TED, separated as §17 requires

TED's 12 Evidence rows are `source_reported_procurement_value_contrast` and
`source_published_classification_value_contrast_witnessed` over CPV divisions 90 and 92.
They establish **MARKET_ACTIVITY**: that a contracting authority published notices whose
reported values differ.

They do **not** establish willingness to pay, actual spend, a framework maximum, or a
buyer for any product hypothesis, and this mission does not collapse those. Their subject
relationship to the Docker hypothesis is **NOT_THE_SAME_SUBJECT** — cleaning and sanitation
procurement is not the Docker subject, and looking commercially interesting is not a
relation.

## The registered-source gap

No source reviewed under `local-private-research-v1` can reach `WILLINGNESS_TO_PAY`,
`BUYER_OR_BUDGET_EXISTENCE` for this subject, `SOLUTION_DISSATISFACTION` or `SOLUTION_GAP`.
The eight reviewed sources are two knowledge sources, one forum, one news source, one
procurement source and three economic-data sources.

The developer-ecosystem sources that could speak to a Docker subject — `github`,
`npm-registry`, `pypi`, `huggingface` — have **no review under LOCAL at all**, and under
Mission 1.75's contract an absent review is a refusal. `github` is RESTRICTED under the
commercial profile, which says nothing about LOCAL and was not borrowed.

This gap is **recorded, not filled**: no source was discovered and none was invented.

## Two corrections the gate forced

**The score check refused a sentence.** The first version refused any field whose name ended
in `_score`, which caught `why_no_score` — the record explaining that it issues none. The
word is not what is dangerous; a **number** posing as a priority is. The check now refuses a
numeric value in a scoring-shaped field and lets the record say what it does not do.

**UNKNOWN is not a small gain.** The first version ranked the gain classes by list position,
which put `UNKNOWN` below `LOW_INCREMENTAL_GAIN` and refused M6's tier-3 placement. But
UNKNOWN is an *unbounded* gain, and ordering it below "a little" asserts exactly what
UNKNOWN denies. It is now excluded from the comparison, and a candidate placed above another
across it must name the criterion that placed it.

## Verification

- Probe: **46 deliberate violations, 46 caught, 0 escaped**, plus **3 of 3 positive
  controls**, six files restored byte for byte.
- The controls are the point: besides the committed state, a **tie** and a
  **no-actionable-candidate** outcome must both remain expressible. A gate that only
  accepts the answer we happened to reach is not a gate.
- All seventeen violation classes §25 names are covered, several by more than one case.
- **3083 bare-python tests**; both runners green; `ruff format --check`, `ruff check`, mypy
  over 197 files; contract generation `--check`; source catalog `--check`; all **49** CI
  gates, one of them new.

## Canonical state

| | before | after |
|---|---|---|
| RawRecords / Normalized | 325 / 325 | 325 / 325 |
| Signals | 33 | 33 |
| Claims / revisions | 44 / 45 | 44 / 45 |
| Evidence | 58 | 58 |
| INFERRED Claims | 1 | 1 |
| threshold_registrations / claim_derivations / refusals | 1 / 1 / 0 | 1 / 1 / 0 |
| ReliabilityAssessments | 4 | 4 |
| EvidenceIndependenceGroups | 0 | 0 |
| Opportunities / revisions / links | 1 / 1 / 7 | 1 / 1 / 7 |
| Embeddings | 0 | 0 |
| Registered sources / use profiles | 29 / 2 | 29 / 2 |
| migration head | `0036` | `0036` |

## Next

**Mission 1.77 — Wikimedia Measurement Scope Binding V1.** One move, category A of §24:
reuse held data through the repository's own deterministic path. Map the held collector
lineage to the committed resource constant, apply `resolve_reliability`, and write the
resolved value onto the Evidence rows it resolves for.

It **can** establish that a reviewed reliability applies and that aggregation becomes
reachable. It **cannot** establish independence, any new dimension, willingness to pay,
whole-packet scorability, or a score. It requires **no external action**, and its canonical
mutation is why it belongs to that mission and not to this one.

**Mission 1.77 was not started.**
