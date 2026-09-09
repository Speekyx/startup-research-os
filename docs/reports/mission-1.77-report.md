# Mission 1.77 — The resource was in the lineage all along

**Outcome: `RELIABILITY_APPLICABILITY_ROOT_CAUSE_REVISED`.**

Mission 1.76 said the Wikimedia evidence could not state its measurement resource. It can,
on every row, from a fact the collector wrote at acquisition. What never resolved was the
Opportunity path, which read a column that is NULL by design and called the result a fact
about the corpus.

---

## Report

```
START_COMMIT                        = 540ed6e
BRANCH                              = sprint-1/mission-1.77
MIGRATION_HEAD                      = 0036_grant_use_profile_vocabulary (measured)
PRODUCTION_SCOPE_BEFORE             = NONE (the Opportunity path builds no scope)
RESOLVER_RESULT_BEFORE              = NOT_INVOKED (every row read from a NULL column)
MISSING_SCOPE_FACT                  = none; the fact 1.76 called missing is persisted on 325/325 RawRecords
HISTORICAL_RESOLUTION_PATH          = DIAGNOSTIC_RECONSTRUCTION (1.36.1, 1.44.1, from raw-record provenance)
CURRENT_PRODUCTION_RESOLUTION_PATH  = NONE_STORED_COLUMN_READ -> LINEAGE_LATE_RESOLUTION
PATH_DIFFERENCE                     = 1.76 read the resource from proposition facts; the runners read nothing
ROOT_CAUSE                          = no late resolution on the Opportunity path; 1.76 read the wrong layer
RESOURCE_BINDING_DEPENDS_ON_CURRENT_MUTABLE_CONFIG = NO
BINDING_BASIS                       = A  EXPLICIT_PERSISTED_RESOURCE
SELECTED_OPTION                     = A
WIKIMEDIA_OPPORTUNITY_EVIDENCE_ROWS = 6      STACK_EXCHANGE_OPPORTUNITY_ROWS = 1
WIKIMEDIA_DETAILED_SCOPE_ROWS       = 18     WIKIMEDIA_CONVERGENT_SCOPE_ROWS = 18
TED_CONTROL_ROWS                    = 12
DETAILED_RESOLVED_BEFORE / AFTER    = 0 / 18      DETAILED_RELIABILITY   = 0.65  e2419f13
CONVERGENT_RESOLVED_BEFORE / AFTER  = 0 / 18      CONVERGENT_RELIABILITY = 0.6   19e0ce16
STACK_EXCHANGE_BEFORE / AFTER       = NO_APPLICABLE_ASSESSMENT / NO_APPLICABLE_ASSESSMENT
TED_BEFORE / AFTER                  = 12 resolved / 12 resolved (0.5 x6, 0.55 x6)
SCORABLE_EVIDENCE_BEFORE / AFTER    = 0 / 48
SCORABLE_OPPORTUNITY_LINKED_EVIDENCE_BEFORE / AFTER = 0 / 6
RELIABILITY_ASSESSMENTS_BEFORE / AFTER = 4 / 4    basis rows 12 / 12
INDEPENDENCE_GROUPS_BEFORE / AFTER  = 0 / 0
PERSISTED_SCORES_BEFORE / AFTER     = ABSENT / ABSENT
OPPORTUNITY_LIMITATION              = OPPORTUNITY_LIMITATION_RECONCILIATION_REQUIRED (STOP, revision 1 untouched)
VIOLATIONS_CAUGHT / ESCAPED         = 65 / 0    positive controls 5 of 5
PRIMARY_OUTCOME                     = RELIABILITY_APPLICABILITY_ROOT_CAUSE_REVISED
NEXT_MISSION                        = 1.78 Opportunity Limitation Reconciliation V1
```

Preconditions verified: tree clean, `main` == `origin/main` at `540ed6e`, Mission 1.76.7
recorded V2 / `V2_VALID_FOR_REFUTATION_BUT_NOT_INDEPENDENT_SUPPORT` / dual support NO /
construct false / corpus false / measurements 0; Q1 `CLASS_SELECTED` with construct and run
false; Globalping 12/0/0 `COUNTERPART_RESOLVED`; migration head `0036`; canonical baseline
325/325/33/44/45/58, INFERRED 1, thresholds 1, derivations 1, refusals 0, assessments 4,
independence groups 0, Opportunities 1 / revisions 1 / links 7, embeddings 0, scores ABSENT,
sources 29, profiles 2. Measured, and unchanged at the end.

## The production failure, reproduced by code

`run_opportunity_preparation.py` and `run_opportunity_synthesis.py` selected
`e.reliability` and set `reliability_status = RESOLVED if non-null else
NO_APPLICABLE_ASSESSMENT`. They constructed no `ReliabilityScope` and never called
`resolve_reliability`. Since ADR-026 Decision 2 keeps that column NULL on every generated
row, every row of every source read NON_SCORABLE, including the twelve TED rows whose
reviewed reliability every diagnostic since 1.15.13 has resolved. **The scorability report
was a report about a column.**

## Why the historical missions resolved and 1.76 did not

Missions 1.36.1 and 1.44.1 rebuilt the scope from `raw_records.provenance ->> 'resource_id'`
through `signal_inputs`. Mission 1.76 rebuilt it from `claims.proposition_facts.resource_id`,
which carries the resource for the TED, World Bank and GDELT kinds and, by ADR-035 and
ADR-036, deliberately not for the Wikimedia and Stack Exchange kinds. A proposition fact says
WHAT is asserted; the resource says WHICH measurement produced the witness. 1.76 found the
key absent at the claim layer and wrote *"resource_id is absent from the whole acquisition
lineage"*. Its report's narrower sentence, that the lineage carries no `resource_id` COLUMN,
is true. The generalisation is false: `acquisition.raw_records.provenance.resource_id` is
present on 325 of 325 records.

**So both historical claims are true.** The historical resolution succeeded; the Opportunity
path could not bind, because the Opportunity path binds nothing. What 1.76 was wrong about
is the lineage sentence and the proposed repair, which mapped the collector lineage to a
committed constant, the hard-coded source exception section 10 forbids. What 1.76 was right
about is that a reviewed assessment exists and that the corpus is one deterministic step from
scorable evidence. The step was the consumer's, not the data's.

## The lineage, layer by layer

| layer | resource identity | immutable |
|---|---|---|
| `scoring.evidence` | not carried | yes |
| `research.claim_revisions` | not carried | yes |
| `research.claims` | `proposition_facts.resource_id` on 17 of 44, by kind | yes |
| `nlp.signals` | `scope.resource_id` on 0 of 33 | yes |
| `nlp.signal_inputs` | names the RawRecord (260 of 260 carry `raw_record_id` and `record_kind_id`) | yes |
| `acquisition.normalized_records` | not carried (0 of 325); `collector_id` on 325 | yes |
| `acquisition.raw_records` | **`provenance.resource_id` on 325 of 325**, beside `collector_id`, `collector_version`, `authorization_issued_at`, `use_profile` | yes |
| collector code, registry | current mutable configuration | **not read** |

The RawRecord's provenance is written by the collector from
`context.authorized_dataset(...).resource_id`, after `authorize_resource`, before the
transport opens a socket, and it is never updated. **Binding basis A**. None of the eight
insufficient bases was relied on, and the expected string
`metrics/pageviews/per-article/en.wikipedia.org` was a verification target that the lineage
re-derived, never an implementation authority.

**Could several resources fit?** 58 of 58 Evidence rows reach exactly one distinct lineage
resource; 0 are ambiguous and 0 absent. Where a lineage reached two, the rule builds no scope
(`NONE_LINEAGE_AMBIGUOUS`) and the row stays NON_SCORABLE, proven by a unit test rather than
by the corpus, which does not contain the case.

## The rule, stated once

`sros_evidence_reliability.lineage.scope_from_lineage(source_id, claim_type,
proposition_facts, lineage_resource_ids, lineage_record_kind_ids)`: exactly one distinct
resource and one distinct record kind reachable from the Signal's inputs build the five-part
scope; anything else refuses. It takes no `resource_id` parameter, so a caller that knows a
resource from a collector constant, from the assessment it hopes to match, or from *the only
registered resource* has nowhere to put it. It names no source and imports nothing that reads
current configuration; the gate scans the source for both.

**Options.** A (propagate the persisted fact) selected. B (derive from a collector contract)
rejected: no such contract is persisted, and building one is the lookup table section 10
forbids. C (a new binding relation) rejected: a second authority for a fact
`acquisition.raw_records` already represents canonically. D (do not repair) rejected: identity
is recoverable, explicitly, on every row.

## Through the real resolver, twice

| scope | rows | via claim facts (1.76) | via lineage | reliability | assessment |
|---|---|---|---|---|---|
| Wikimedia detailed | 18 (6 on the Opportunity) | 0 | **18** | 0.65 | `e2419f13` v1 HUMAN_REVIEW |
| Wikimedia convergent | 18 | 0 | **18** | 0.6 | `19e0ce16` v1 HUMAN_REVIEW |
| Wikimedia INFERRED `metric_threshold_state` | 1 | 0 | 0 | — | none, correctly |
| TED procurement contrast | 6 | 6 | 6 | 0.5 | `3de2af10`, unchanged |
| TED classification witnessed | 6 | 6 | 6 | 0.55 | `d1afa4be`, unchanged |
| Stack Exchange, both kinds | 2 (1 on the Opportunity) | 0 | 0 | — | none; the operator declined in 1.36.1 |
| World Bank, GDELT | 7 | 0 | 0 | — | no assessment exists |

Same resolver, same four candidates: 12 resolved one way, 48 the other. Every binding's
assessment scope equals the row's on all five parts; the two Wikimedia kinds resolve two
different assessments; a Stack Exchange row cannot borrow either.

## Scorability, kept apart

```
ASSESSMENT_EXISTS      YES  4 current, unchanged
ASSESSMENT_APPLIES     YES  48 of 58 rows through lineage; NO for 10
EVIDENCE_IS_SCORABLE   YES  48 through EvidenceFacets.is_scorable fed the late value; 0 through the column
AGGREGATION_CAN_RUN    YES  34 Claims COMPLETE, read-only, UNCALIBRATED / DIAGNOSTIC_ONLY / NOT_AN_OPPORTUNITY_SCORE
SCORE_IS_PERSISTED     NO   scoring.scores does not exist
```

The aggregation diagnostic is identical to reliability pass-through on 34 of 34 Claims, with
one support group each, `max(members)` receiving up to four, established independence 0,
`reliability` the limiting component everywhere, level 1. Mission 1.43's structural result
stands: one provenance group cannot distinguish the full aggregator from pass-through, and
Wikimedia's witnesses share one publisher, one pipeline and one counting rule.

## The repair, and where it stops

Both Opportunity runners now build the lineage scope per row, call the real resolver, and
carry the outcome and the binding; the synthesis runner also computes the eligibility a
citation is written with and the reliability limitation from the cited rows instead of
hard-coding `ELIGIBLE_CONTEXT` and *"no reviewed reliability applies"*. Invoked in memory
against the deployment, preparation reports 48 scoring / 10 context and the docker packet
14 rows with 12 scoring; nothing was written. `opportunity-preparation-v1.json` was **not**
regenerated: it is the Mission 1.28 to 1.34 record of a 28-row corpus, pinned by eight tests
as history, and regenerating it belongs with the reconciliation below.

**The canonical limitation is stale and was not edited.** Revision 1 of the docker
Opportunity, written 2026-09-02, says *no reviewed reliability applies*. The 0.65 assessment
was created 2026-09-03 and the 0.6 one 2026-09-04. Resolved late, 6 of its 7 rows carry a
reviewed reliability. That is a canonical row, so section 17 governs:
**`OPPORTUNITY_LIMITATION_RECONCILIATION_REQUIRED`**, STOP, revision 1 untouched, no
revision 2. The three derived carriers of the false sentence and the stale limitation gained
one forward pointer each, rendered where the record has a page, and still carry their
sentences: history was pointed at, not rewritten.

## Verification

- Probe: **65 deliberate violations, 65 caught, 0 escaped**, plus **5 of 5 positive
  controls**, thirteen files restored byte for byte. Two escapes found and closed on the
  first run: a resolver signature widened inside the package escaped because the gate asked
  the imported module rather than its source, so the signature and the five-part scope are
  now asserted over the AST of `model.py`; and a runner mutated into a syntax error crashed
  the gate instead of being refused, so a module that does not parse is now a refusal.
- **Two controls are INVERTED and they are the point.** A proven REPAIRED outcome is
  accepted, and a Stack Exchange row resolving against an assessment of its OWN scope is
  accepted, so the gate enforces consistency rather than pinning the repository to this
  mission's verdict. A third control found a defect in the probe itself: the second Stack
  Exchange row is a different proposition kind and needs an assessment of its own.
- One 1.76 test re-pointed rather than deleted: `test_every_evidence_row_is_currently_unscorable`
  counted the stored column and its name asserted a fact about the corpus.
- **3517 bare-python tests** across 9 packages; **287 pytest tests** with the database
  unchanged across 29 tenant tables; `ruff format --check`, `ruff check`, mypy over the 14
  package paths; contract and catalog `--check`; all **56** CI gates, one of them new.
- Canonical baseline identical before and after every run in this mission.

## What did not happen

No Wikimedia, Stack Exchange, TED, World Bank, GDELT or Globalping call; no target request;
no web discovery; no mailbox read; no email; no GitHub issue; no model call; no embedding. No
assessment, basis row, independence group, score, revision, migration, backfill or
historical row rewritten. Q1 still selected without a construct or a run; Globalping still
12/0/0; V2 still valid for refutation and not for support.

## Remaining limitation

The canonical Opportunity carries a limitation that is false today, and reconciling it needs
a new revision from an attended synthesis run. The seventh linked row, Stack Exchange, stays
NON_SCORABLE because the operator declined that review, so the hypothesis can never be wholly
scorable on this evidence. Every scorable Claim still has one provenance group, so no
calibration is unlocked. Scorable is not scored.

## Next

**Mission 1.78 — Opportunity Limitation Reconciliation V1**: one attended synthesis run over
the docker packet through the repaired path, writing revision 2 beside revision 1 with a
computed reliability limitation, and regenerating the preparation record from the current
58-row corpus with its eight tests re-pointed. Not Globalping: the apparatus arc is parked on
a semantic limit that no bounded move here changes. Not calibration: one provenance group per
Claim, unchanged. It must not persist a score, create an independence group, edit revision 1,
or select a construct.

## The 52 answers

1. `540ed6e`. 2. `sprint-1/mission-1.77`. 3. `0036_grant_use_profile_vocabulary`, measured.
4. 325/325/33/44/45/58, INFERRED 1, thresholds 1, derivations 1, refusals 0, assessments 4
(basis 12), groups 0, Opportunities 1/1/7, embeddings 0, scores ABSENT, sources 29, profiles
2, profile UNCALIBRATED, Problem-Family PARKED; unchanged. 5. Six detailed Wikimedia rows on
the docker Opportunity (`platform_counted_content_request_change`), beside one Stack Exchange
row. 6. None: the production path built no scope. 7. None; the path asked for no fact.
8. Not invoked; every row read NO_APPLICABLE_ASSESSMENT from a NULL column. 9. wikimedia
-pageviews / `metrics/pageviews/per-article/en.wikipedia.org` / content_request_count /
OBSERVED / `platform_counted_content_request_change`, 0.65. 10. Same with
`..._witnessed`, 0.6. 11. They read raw-record provenance through signal inputs. 12. It read
nothing; 1.76's audit read proposition facts. 13. Evidence → Claim revision → Claim → Signal →
signal_inputs → NormalizedRecord → RawRecord, every link persisted. 14. `scoring.evidence
.source_id`, `signal_inputs.source_id`, `raw_records.source_id`. 15. `raw_records
.collector_id` and `collector_version`, and the same on normalized records. 16. `acquisition
.raw_records.provenance.resource_id`, 325 of 325. 17. Explicit. 18. Provenance written once at
acquisition from the authorized dataset, with `authorization_issued_at`, `use_profile` and
`review_version` beside it. 19. None; the collector module and the registry are not read.
20. No: 58 of 58 rows reach exactly one; ambiguity refuses, proven by test. 21. A selected, B
and C and D rejected with reasons. 22. A. 23. The fact exists, is immutable, is one join away
and needs no new authority. 24. No; the gate scans for one. 25. No; asserted over the
resolver's source. 26. 0 → 18. 27. 0.65. 28. `e2419f13-c031-44d5-837c-c56a867baf34` v1.
29. 0 → 18, 0.6, `19e0ce16-957f-4543-9b15-738a77b13060` v1. 30. NO_APPLICABLE_ASSESSMENT
both ways. 31. 12 resolved both ways, 0.5 and 0.55 unchanged. 32. 0 → 48. 33. 0 → 6.
34. Read-only, 34 Claims, identical to pass-through, 0 established independence, not
persisted. 35. None; no scores table. 36. Yes, since 2026-09-03. 37. No; STOP,
`OPPORTUNITY_LIMITATION_RECONCILIATION_REQUIRED`. 38. 0. 39. 0. 40. 0. 41. 0. 42. 0. 43. 0.
44. 0. 45. Q1 CLASS_SELECTED, construct false, run false, before and after. 46. 12/0/0
COUNTERPART_RESOLVED, before and after. 47. Identical on every counter. 48. 65 caught, 0
escaped, 5 of 5 controls. 49. 3517 bare-python, 287 pytest, database unchanged, ruff, mypy,
contracts, catalog, 56 gates, all green. 50. `RELIABILITY_APPLICABILITY_ROOT_CAUSE_REVISED`.
51. The canonical limitation is stale, the Stack Exchange row stays unscorable, one
provenance group everywhere, no score. 52. Mission 1.78, Opportunity Limitation
Reconciliation V1.
