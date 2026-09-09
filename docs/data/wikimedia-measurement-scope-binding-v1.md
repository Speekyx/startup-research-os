# Wikimedia measurement scope binding — the resource was there all along

Generated from `wikimedia-measurement-scope-binding-v1.json`. Do not edit by hand.

**RELIABILITY_APPLICABILITY_ROOT_CAUSE_REVISED**

Mission 1.76 diagnosed that 'resource_id is absent from the whole acquisition lineage' and proposed binding the Wikimedia lineage to a committed collector constant. The first statement is false on the held data: every one of the 325 RawRecords carries provenance.resource_id, reachable from any Evidence row through its Signal's inputs, and the real resolver resolves all 36 Wikimedia rows through that join with no source named anywhere. The proposed repair was therefore unnecessary, and it is the hard-coded source exception section 10 forbids. What was actually wrong is a different defect that 1.76 did not name: the Opportunity production path never resolves reliability at all. It reads scoring.evidence.reliability, which ADR-026 Decision 2 keeps NULL by design, so every row of every source read NON_SCORABLE whatever the reviewed assessments said, TED included.

## The production failure, frozen

| | |
|---|---|
| PRODUCTION_SCOPE_BEFORE | NONE: the path constructs no five-part scope for any row |
| RESOLVER_RESULT_BEFORE | NOT_INVOKED: every row reads NO_APPLICABLE_ASSESSMENT from a NULL column, for all five sources |
| MISSING_SCOPE_FACT | none. The path asks for no fact at all; what is missing is the late resolution ADR-026 Decision 2 requires. The fact 1.76 called missing, the resource, is persisted on every RawRecord. |

## The apparent contradiction

| | |
|---|---|
| HISTORICAL_RESOLUTION_PATH | `DIAGNOSTIC_RECONSTRUCTION` |
| CURRENT_PRODUCTION_RESOLUTION_PATH | `NONE_STORED_COLUMN_READ (before this mission); LINEAGE_LATE_RESOLUTION (after)` |
| PATH_DIFFERENCE | 1.36.1 and 1.44.1 read the resource from acquisition provenance through signal lineage; 1.76 read it from proposition facts, which carry it for some kinds and not others; the Opportunity runners read neither and resolved nothing. |
| ROOT_CAUSE | two defects, neither of them a missing fact. (1) The Opportunity path performs no late resolution, so its scorability report is a report about a NULL column. (2) Mission 1.76's diagnostic reconstructed the scope from the wrong layer and generalised the absence it found there to the whole lineage. |

## Where the resource lives

**YES** — `acquisition.raw_records.provenance.resource_id, reached through nlp.signal_inputs.raw_record_id`, EXPLICIT, binding basis `EXPLICIT_PERSISTED_RESOURCE`, depends on current mutable configuration: **NO**.

| layer | resource identity | immutable |
|---|---|---|
| `scoring.evidence` | NOT_CARRIED | True |
| `research.claim_revisions` | NOT_CARRIED | True |
| `research.claims` | CARRIED_FOR_SOME_KINDS_ONLY | True |
| `nlp.signals` | NOT_CARRIED | True |
| `nlp.signal_inputs` | NOT_CARRIED, but names the RawRecord that carries it | True |
| `acquisition.normalized_records` | NOT_CARRIED (provenance.resource_id on 0 of 325) | True |
| `acquisition.raw_records` | EXPLICIT_PERSISTED (325 of 325) | True |
| `collector code and registry` | CURRENT_MUTABLE_CONFIGURATION | False |

## Options

| option | verdict | why |
|---|---|---|
| A. Propagate the existing persisted resource fact through scope construction | `SELECTED` | the fact exists on every RawRecord, is immutable, is reachable by one join from any Evidence row, and needs no new authority; the smallest truthful implementation |
| B. Derive resource identity at scope-construction time from an immutable collector contract | `REJECTED` | no collector-to-resource contract is persisted; building one would be the collector-constant lookup table section 10 forbids, and it is unnecessary because A exists |
| C. Introduce a generic explicit measurement-resource binding relation | `REJECTED` | it would be a second authority for a fact acquisition.raw_records already represents canonically; section 9 forbids creating one |
| D. Do not repair because exact identity is not recoverable | `REJECTED` | identity is recoverable, explicitly, on 58 of 58 rows |

## Controls, through the real resolver

| scope | rows | before | after | reliability | assessment |
|---|---|---|---|---|---|
| Wikimedia detailed | 18 | 0 | 18 | 0.65 | `e2419f13` |
| Wikimedia convergent | 18 | 0 | 18 | 0.6 | `19e0ce16` |
| Stack Exchange | 2 | `NO_APPLICABLE_ASSESSMENT` | `NO_APPLICABLE_ASSESSMENT` | — | — |
| TED | 12 | 12 | 12 | 0.5 / 0.55 | unchanged |

## Scorability, kept apart

| | |
|---|---|
| ASSESSMENT_EXISTS | YES: 4 current assessments, 12 basis rows, unchanged |
| ASSESSMENT_APPLIES | YES for 48 of 58 rows through lineage; NO for 10 (Stack Exchange 2, World Bank 4, GDELT 3, Wikimedia INFERRED 1) |
| EVIDENCE_IS_SCORABLE | YES for 48 rows through the existing EvidenceFacets.is_scorable when fed the late-resolved value; 0 rows through the stored column |
| AGGREGATION_CAN_RUN | YES, read-only: 34 Claims COMPLETE under REFERENCE_PROFILE_V1 with allow_uncalibrated=True |
| SCORE_IS_PERSISTED | NO: scoring.scores does not exist and nothing wrote a score |

Scorable Evidence 0 → 48; Opportunity-linked 0 → 6. Assessments 4 → 4, independence groups 0 → 0, scores ABSENT → ABSENT.

## The stale limitation

**OPPORTUNITY_LIMITATION_RECONCILIATION_REQUIRED.** Revision 1 of `06113a8b` still reads: *Every supporting Evidence row is ELIGIBLE_CONTEXT, NON_SCORABLE and MISSING_RELIABILITY: no reviewed reliability applies, so this hypothesis can contribute to no score.* the detailed Wikimedia assessment (0.65) was created 2026-09-03T11:53Z and the convergent one (0.6) 2026-09-04T06:51Z, both after the revision; resolved late, 6 of the 7 linked rows carry a reviewed reliability. Action: **STOP**; the historical revision was not edited.

**Remaining limitation.** The canonical Opportunity still carries a limitation that is false today, and reconciling it needs a new revision from an attended synthesis run. The seventh linked row, Stack Exchange, stays NON_SCORABLE because the operator declined that review, so the hypothesis can never be wholly scorable on this evidence. Every scorable Claim still has one provenance group, so the aggregator is still numerically the pass-through baseline and no calibration is unlocked. Scorable is not scored: no score exists.

**Next: Opportunity Limitation Reconciliation V1.** one attended synthesis run over the docker packet through the repaired path, writing revision 2 beside revision 1 with a computed reliability limitation, and regenerating the preparation record from the current 58-row corpus with its eight tests re-pointed
