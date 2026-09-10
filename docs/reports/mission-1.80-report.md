# Mission 1.80 — The best packet is not a candidate

**Outcome: `SECOND_OPPORTUNITY_REQUIRES_SUBJECT_NARROWING`.**

Nine held subjects were examined as candidates for a second Opportunity exploration, and
exactly one of them carries evidence worth building on. It is a procurement category, its
held notices span at least six distinct service classes, and a hypothesis at its grain would
name a disjunction of unrelated markets. So the richest packet in the corpus is the best held
evidence packet and is not a second-Opportunity candidate, and no other subject is one either.

---

## Report

```
START_COMMIT                        = c19f8d4
MIGRATION_HEAD                      = 0036_grant_use_profile_vocabulary (measured)
CURRENT_OPPORTUNITY_ID              = 06113a8b-a83d-423d-8046-18f87d7dbc01
CURRENT_REVISION_ID / NUMBER        = 8739e7ab-940b-408c-a5e8-7f6675d1597c / 2
CANDIDATE_UNIVERSE                  = 9 packets (every non-docker packet of preparation v2)
CANDIDATES_EXAMINED                 = 9      FORMABLE 2      SCORABLE_ROWS_TOTAL 36 of 44
BEST_HELD_EVIDENCE_PACKET           = ted-eu:CPV-division:92 (10 rows, 10 scorable, 3 commercial counting dims)
BEST_SECOND_OPPORTUNITY_CANDIDATE   = none
SELECTED_SUBJECT / SCOPE / PACKET   = none / none / none
TED_92  rows 10  scorable 10  detailed 5 at 0.5  witnessed 5 at 0.55  independence UNKNOWN
TED_92  subject_type CATEGORY  grain TOO_BROAD_TO_BE_ACTIONABLE  actionable REQUIRES_NARROWER_SUBJECT_DISCOVERY
TED_92  product_relevance UNKNOWN  semantic_specificity LOW  egress UNAVAILABLE (NOT_ASSESSED)
TED_92  held notices 177: CN 115 / CAN 62; classes 92111 26, 92610 21, 92521 16, 92400 13, 92312 12, 92370 7
TED_90  rows 2 (dominated by 92)   KUBERNETES 13/12 not formable   PODMAN 12/12 not formable
WORLD_BANK DE/FR 2/0 no dimension   GDELT climate / climate|weather / weather 1/0 no dimension
PARETO_FRONTIER                     = ted-eu:CPV-division:92, subject:kubernetes, subject:podman
DOMINATED                           = TED 90 (by 92); WB DE, WB FR (by kubernetes); 3 GDELT (by 92)
VETOED                              = all 9
REPRESENTATION_CHECK                = TED 92: 8 claims, 4378 chars, 0 violations; TED 90: 2 claims, 1777 chars, 0 violations (in memory, not sent)
EGRESS_REVIEW_REQUIRED_BEFORE_SYNTHESIS = true   egress decided here = false (not granted, not denied)
PRIMARY_OUTCOME                     = SECOND_OPPORTUNITY_REQUIRES_SUBJECT_NARROWING
RECOMMENDED_NEXT_MISSION            = 1.81 Procurement Subject-Grain Narrowing V1 (held data only)
OPPORTUNITIES 1 -> 1   REVISIONS 2 -> 2   LINKS 14 -> 14   ASSESSMENTS 4 -> 4   GROUPS 0 -> 0   SCORES ABSENT
API_CALLS 0   RAW_RECORDS 0   MODEL_CALLS 0   EMBEDDINGS 0   SOURCE_REVIEWS_APPENDED 0   CANONICAL_MUTATIONS 0
VIOLATIONS_CAUGHT / ESCAPED         = 46 / 0    positive controls 4 of 4
```

Preconditions verified: tree clean, `main` == `origin/main` at `c19f8d4`, Mission 1.79's record
present, preparation v2 current under `--check`, revision 2 current and revision 1 readable,
counters as reconciled (1 / 2 / 14, assessments 4, groups 0, scores ABSENT, embeddings 0),
Q1 CLASS_SELECTED without construct or run, Globalping 12/0/0, V2 selected with corpus false
and measurements 0. All re-measured, none quoted.

## The universe is the held packets, and nothing else

The candidate universe is every packet of the current preparation other than docker's: two
TED divisions, kubernetes, podman, two World Bank population series, three GDELT terms. Each
carries exactly the size, scorable count, dimensions, reliabilities, formability and egress
the preparation gives it, and the gate recomputes all of it from the preparation and the
reconciliation. Nothing was merged: kubernetes is not docker, CPV 90 is not CPV 92, climate is
not weather. Nothing was narrowed: a CPV class is not a packet, so it is not a candidate.

## What division 92 establishes

TED published bounded sets of CONTRACT_NOTICE and CONTRACT_AWARD_NOTICE notices under CPV
division 92 whose stated TOTAL_VALUE amounts differ from one another, at 86.9M EUR, 16.6M EUR,
14.7M EUR, 1.77M EUR and 15M SEK. Contracting authorities exist in this category and publish
what they buy. That is BUYER_OR_BUDGET_EXISTENCE, ECONOMIC_VALUE and MARKET_ACTIVITY, on ten
rows resolving to two reviewed reliabilities, and it is formable.

**What it does not establish is written into the record as boundaries, not caveats.** A
BT-161 value includes options and renewals and may never be exercised, so it is not spend. It
is not willingness to pay, not market size, not demand, and a contracting authority is not a
buyer for a SaaS nobody has specified. And it says nothing about which of the six-plus
service classes any of it concerns: 26 held notices are motion picture and video services,
21 sports facility operation, 16 museum services, 13 news agency services, 12 artistic
services, 7 sound technician services. A hypothesis at division grain would be a disjunction
of those, which is the shape Mission 1.47 refused for a proposition and applies to a subject
just the same. So the intervention grain is TOO_BROAD_TO_BE_ACTIONABLE and the actionable
grain is REQUIRES_NARROWER_SUBJECT_DISCOVERY.

An exploratory category hypothesis was considered and not adopted, for the same reason: it
would read that EU authorities buy recreational, cultural and sporting services at widely
differing values, which names no need, no buyer type, no product and no class.

## The others

- **CPV 90** is the same shape on two rows and eleven notices, dominated by 92.
- **Kubernetes and podman** are the docker shape minus its second dimension: one counting
  dimension, not formable, and Mission 1.79 already found the shape saturated. They sit on the
  frontier because they name a product where division 92 names a category, and semantic
  specificity is a dominance field. Both are vetoed on formability, which a frontier place
  does not waive.
- **World Bank DE and FR** report population changes and map to no dimension. A population
  change is not demand.
- **GDELT climate, climate|weather, weather** report term-frequency changes and map to no
  dimension. Publication is producer behaviour, not audience.

## The frontier corrected the author

The first draft recorded kubernetes and podman as dominated by division 92. Under the rule
the record itself states, they are not: semantic specificity is one of the fields, they are
HIGH on it and division 92 is LOW. The gate recomputed the frontier, the record was corrected
to match the rule, and the rule was not narrowed to match the record. The frontier is three
candidates, and all three are vetoed.

## Egress

ted-eu external_model_transmission is NOT_ASSESSED under local-private-research-v1. The
record says `EGRESS_REVIEW_REQUIRED_BEFORE_SYNTHESIS = true` and decides nothing: not granted,
not denied, no review appended. No candidate is vetoed for egress alone, and the gate refuses
a record that vetoes a formable actionable candidate on that ground. The representation test
of section 17 was run in memory over the real claim statements of both TED packets through
the transmission allowlist, with zero violations and nothing sent.

## Why no selection

A candidate passes only if it clears every gate, and actionable grain is one of them. Both
formable candidates are categories at too-broad grain; every other candidate is not formable
or carries no decision-relevant dimension. Selecting the richest packet regardless would
optimise for Opportunity count, which section 22 forbids. The best held evidence packet and
the best second-Opportunity candidate are therefore two different answers, and the record
says why.

## Verification

- Probe: **46 deliberate violations, 46 caught, 0 escaped**, plus **4 of 4 positive
  controls**: a valid CPV winner as an exploratory category hypothesis, a valid non-TED winner
  with kubernetes made formable in the preparation, the shipped narrowing outcome, and the
  no-actionable-candidate outcome. One case was first caught for the wrong reason (a stale
  vetoed list rather than the selection basis) and was corrected so the rule it targets is the
  one that fires.
- **21 new unittest cases**; all bare-python suites; pytest suites green with the database
  unchanged; `ruff format --check`, `ruff check`, mypy; contract and catalog `--check`; all
  **59** CI gates, one of them new.
- Counters identical before and after: nothing canonical moved, no model, no external call, no
  acquisition, no assessment, no score, no source review.

## Next

**Mission 1.81 — Procurement Subject-Grain Narrowing V1**, held data only: derive
CPV-class-grain cohorts from the 177 held division-92 notices, define class-grain subject keys
in the grouping procedure, re-run the preparation runner, and re-select among the class-grain
packets against the same gates. It must not acquire data to narrow, call a model, decide the
ted-eu egress question, create an Opportunity, or score or rank. The egress review comes after
a subject exists, not before. **It was not started.**
