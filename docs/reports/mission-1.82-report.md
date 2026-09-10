# Mission 1.82 — What the codes mean, and the one subject that survives knowing it

**Outcome: `PROCUREMENT_SEMANTIC_SUBJECT_CANDIDATE_SELECTED`.**

Mission 1.81 ended holding four formable group packets it could not judge, because every one
of the 608 held CPV entries carries a null label and a bare code cannot be actionable or not.
This mission bought the missing input from the vocabulary's own register, one concept at a
time, over a universe of codes frozen and committed before the first fetch. Then it derived
the class grain over every frozen class the procedure admits, re-selected across all 27
candidates, and one class came out carrying no veto: `ted-eu:CPV-class:9261`, "Sports
facilities operation services". It beat its own group by being strictly more specific at
exactly the same six Evidence rows, and its equally broad sibling by naming one activity
where the sibling names two. Nothing about a market was decided.

---

## Report

```
START_COMMIT                = f8c428c          BRANCH = sprint-1/mission-1.82
MIGRATION_HEAD              = 0036_grant_use_profile_vocabulary (measured)
FREEZE_COMMIT               = 34d85f6 (the lookup universe, committed before any retrieval)

FROZEN_GROUP_CODES          = 921, 922, 923, 924, 925, 926                       (6)
FROZEN_CLASS_CODES          = 9211, 9213, 9222, 9231, 9233, 9235, 9236, 9251,
                              9252, 9253, 9261, 9262                             (12)
LOOKUP_UNIVERSE_SHA256      = 4ace701c3ee9f27716d3d5e8f67d8933ea043a4844ffe89ff905a967d4624d83
FIRST_PARTY_AUTHORITY       = European Union Publications Office, EU Vocabularies CPV authority register
VOCABULARY_VERSION          = 2008          VOCABULARY_LANGUAGE = en
DOCUMENTATION_FETCHES       = 19            RESEARCH_DATA_FETCHES = 0
GROUP_LABELS_RESOLVED / UNRESOLVED = 6 / 0  CLASS_LABELS_RESOLVED / UNRESOLVED = 12 / 0
THIRD_PARTY_FALLBACKS       = 0             LABELS_INFERRED_FROM_NEIGHBOURS = 0

CLASS_COHORTS_KEYED / DERIVED / REFUSED = 29 / 14 / 15 (all 15 INSUFFICIENT_INPUT_OBSERVATIONS)
NEW_SIGNALS / CLAIMS / CLAIM_REVISIONS / EVIDENCE = 14 / 26 / 26 / 28
NEW_EVIDENCE_SCORABLE / NONSCORABLE = 28 / 0  (14 at 0.5 via 3de2af10, 14 at 0.55 via d1afa4be)
RELIABILITY_ASSESSMENTS_DELTA = 0           INDEPENDENCE_GROUPS_DELTA = 0
SECOND_RUN_NEW_ROWS         = 0             (14 skipped as existing witness)
PREPARATION_BEFORE / AFTER  = opportunity-preparation@3.0.0 / @4.0.0 (v1, v2, v3 byte-identical)

BEST_GROUP_PACKET           = ted-eu:CPV-group:925 (8 rows; a count, and it is vetoed on coherence)
BEST_CLASS_PACKET           = ted-eu:CPV-class:9261
BEST_HELD_PACKET            = ted-eu:CPV-division:92 (10 rows, vetoed on grain for the third mission)
BEST_SECOND_OPPORTUNITY_CANDIDATE = ted-eu:CPV-class:9261
PARETO_FRONTIER             = CPV-class:9261, CPV-division:92, kubernetes, podman
VETOED                      = 18 of 27 (both divisions, 4 groups, 5 classes, kubernetes, podman,
                              3 GDELT terms, 2 World Bank series)
DOMINATED                   = 23 of 27
SELECTED_SUBJECT / LEVEL / CODE = ted-eu:CPV-class:9261 / class / 9261 (concept 92610000)
SELECTED_LABEL              = Sports facilities operation services
SELECTED_PACKET             = e218b56a8f938f4d5f7fc961e7f0c2cfe184c4396395334140c6199b48316592
SELECTION_BASIS             = the only frontier candidate carrying no veto; one stated meaning,
                              6 rows derived at that exact code, all scorable
EGRESS_REVIEW_REQUIRED_BEFORE_SYNTHESIS = true, NOT_ASSESSED, not decided here

OPPORTUNITY_CREATED = 0   MODEL_CALLS = 0   EMBEDDINGS = 0
SCORES = ABSENT           GLOBALPING_MEASUREMENTS = 0
CANONICAL_MUTATION_SUMMARY  = signals 46->60, claims 65->91, revisions 66->92, evidence 84->112;
                              everything else unchanged
VIOLATIONS_CAUGHT / ESCAPED = 54 / 0        positive controls 7 of 7
PRIMARY_OUTCOME             = PROCUREMENT_SEMANTIC_SUBJECT_CANDIDATE_SELECTED
NEXT_MISSION                = 1.83 Selected Procurement Candidate Egress Review V1
```

Preconditions verified: tree clean, `main` == `origin/main` at `f8c428c`, Mission 1.81 merged
as PR #140, 325 RawRecords, 325 NormalizedRecords, 46 Signals, 65 Claims, 66 ClaimRevisions,
84 Evidence, 4 assessments, 0 independence groups, 1 Opportunity at revision 2 with 14 links,
70 source reviews, no scores table, 0 embeddings, migration head 0036. All re-measured, and
all re-measured again after the derivation.

## The universe was frozen before a single label was read

The order matters more than the retrieval. A label is a persuasive thing: read "Sporting
services" first and it is very easy to decide, afterwards, that group 926 was always the one
worth looking up. So the codes came first. `infrastructure/scripts/freeze_cpv_lookup_universe.py`
asks the production membership rule itself — the extractor's own `_cpv_prefix` at grains 3 and
4 — which prefixes form a cohort over the 177 held division-92 notices, writes the answer with
no labels in it, and hashes it. That artifact was committed as `34d85f6` before the first
fetch, and its digest is quoted in the vocabulary record and in the main record. Zero codes
were added after labels were read; zero were removed.

The freeze then cost something, which is how you know it was doing work. Three class codes,
9221, 9232 and 9237, appear on held notices (3, 4 and 8 of them) and are not in the frozen
universe, because each appears only alongside another class code and `C4_REFUSE_AMBIGUOUS_NOTICE`
gives them no cohort at grain 4. Widening the freeze to cover them would have been a structural
excuse for going back to the register after seeing what the first eighteen labels said. They
are recorded with their counts instead, so the gap is visible, and any future mission that
changes the membership model has to re-freeze before it looks them up.

## Eighteen documents, eighteen labels, no summaries

Each concept was fetched on its own from
`https://publications.europa.eu/resource/authority/cpv/cpv/<code>`, the pattern Mission 1.40
established. The register answers in RDF/XML: the concept document itself, carrying
`skos:prefLabel` in the requested language, `owl:versionInfo` 2008, `skos:broader` and
`skos:inScheme`. Mission 1.63's rule that a retrieval summary is not a document is met by the
medium here rather than by care, because nothing summarising sits between the register and the
record. Every raw response was hashed and the digest stored beside its label; all eighteen
digests differ.

Every retrieved `skos:broader` agrees with the mechanical code hierarchy. That agreement is
recorded as a corroboration and nothing more. The hierarchy is still established by the CPV
token's own digit structure, exactly as Mission 1.81 left it, and no label was inferred from
a neighbouring code.

## The class grain was derived whole, and judged afterwards

Fourteen of the 29 keyed class cohorts produced Signals. The other fifteen were refused for
the same reason at the same threshold: `MINIMUM_COHORT_MEMBERS = 2`, re-read from the extractor
rather than assumed. Every frozen class the procedure admits was derived, including the
two-row ones and including the classes whose labels turned out to name nothing a product could
plausibly enter. The semantic and actionability gates ran afterwards, over records that
already existed, so no measurement in this repository exists because a label read well.

Fourteen Signals became 14 detailed Claims and 12 witnessed ones, which is why claims and
evidence do not move in step. Two pairs of class cohorts from the two acquisition windows
converge on one broader proposition each, and that is the Mission 1.39 convergence contract
operating at a grain it had not previously reached. All 28 Evidence rows resolve through the
unchanged lineage path onto the two existing TED assessments, because a reliability scope is
source, resource, record kind, claim type and proposition kind, and carries no classification
level at all. No assessment was created. A reviewer could still decide that a finer level is a
different measurement purpose deserving its own scope, and nothing here forecloses that.

Three non-EUR cohorts were refused at the floor rather than converted: SEK at 9231, CZK at
9252, SEK at 9261. Currency has been a cohort key dimension since
`procurement-value-contrast@1.1.0`, so two currencies are two cohorts and neither an FX
conversion nor a cross-currency contrast was performed. Contract notices and award notices
stay apart for the same structural reason, and BT-161's limitations are preserved: a stated
total value includes options and renewals and is not realised expenditure.

The second run persisted nothing. Fourteen Signals were skipped as existing witnesses, zero
Claims and zero Evidence were created, and the grain-3 records reproduce byte-identically.

## Semantic coherence entered as a field, not as a tie-break

Mission 1.81's frontier could not separate two categories that were equally broad and equally
specific, because the only thing distinguishing them is what their labels mean. That is
precisely what the retrieval bought, so it entered the dominance model as a tenth field with a
three-point scale, applied to every candidate before the frontier was recomputed.

The scale asks what a subject *means*. `SINGLE_DOMAIN` names one activity, `RELATED_ACTIVITIES`
joins activities inside one domain or ends in an open remainder, `UNRELATED_ACTIVITIES` names
materially unrelated markets. It is not attractiveness, not trend, not perceived profitability,
not apparent software potential. A subject can be perfectly coherent and commercially dull, and
this field would not know. Candidates with no official classification label, such as a bare
product term, are marked not applicable, and the field decides nothing for or against them.

## The groups, once they had names

All six were re-evaluated before anything descended, and the labels settled Mission 1.81's
question in three different directions.

| Group | Official label | Notices | Evidence | Coherence | Actionable grain |
|---|---|---|---|---|---|
| 921 | Motion picture and video services | 9 | 6 | RELATED_ACTIVITIES | exploratory category hypothesis |
| 922 | Radio and television services | 2 | 0 | RELATED_ACTIVITIES | NOT_ACTIONABLE |
| 923 | Entertainment services | 20 | 6 | UNRELATED_ACTIVITIES | requires narrower subject |
| 924 | News-agency services | 4 | 0 | SINGLE_DOMAIN | NOT_ACTIONABLE |
| 925 | Library, archives, museums and other cultural services | 21 | 8 | UNRELATED_ACTIVITIES | requires narrower subject |
| 926 | Sporting services | 21 | 6 | SINGLE_DOMAIN | exploratory category hypothesis |

Two groups reach the exploratory gate once labelled, and that is Mission 1.81's blocker
resolved. Two are disjunctions their own labels expose, 925's most plainly of all, since it
ends "and other cultural services" — a category whose name admits it is a remainder. Two are
coherent and empty, and a coherent subject with no Evidence is not actionable; 924 is the clean
demonstration that coherence alone selects nothing.

That makes Outcome C of the brief half true, and it was refused as the primary outcome on
exactly that ground. Group grain did become actionable for two groups. Deeper narrowing was
not thereby unnecessary.

## Why a class beat its group, and why the other one did not

A class does not win for being narrower. It wins only where narrowing costs no Evidence and
buys precision, and both group-class pairs were computed on that rule.

Narrowing 926 to 9261 costs nothing: the same six rows, the same three counting dimensions,
the same two reviewed reliabilities, and a label that names one activity instead of a domain.
The class wins. Narrowing 921 to 9211 costs two of six rows, and the class label ends in an
open "and related services", so it buys less precision than it costs; neither wins the
selection and both stay unvetoed, dominated by 9261.

Against its equally broad sibling 9252, "Museum services and preservation services of
historical sites and buildings", 9261 wins on coherence alone: six rows each, same
dimensions, same reliabilities, one label naming one activity and the other naming two. That
comparison is the reason the semantic field exists.

Small cohorts were recorded honestly. Seven class candidates rest on one to three cohorts, and
for each of them procedural validity and evidential breadth are stated as two separate facts.
A two-observation contrast is valid under the procedure and it is not thereby strong. No
minimum N was invented to make that point.

## What was selected, and what was not claimed

`ted-eu:CPV-class:9261` passes all nine gates that this mission can decide: exact code
identity, an authoritative label, Evidence derived at that exact grain, a formable packet, an
adoptable exploratory hypothesis, product relevance that is not invented, no parked relation,
no new acquisition needed to know what the subject is, and no unsupported problem or product
inference. The tenth is not a gate this mission may close: TED's
`external_model_transmission` is `NOT_ASSESSED` under `local-private-research-v1`, an open
question an operator can close and not a prohibition. Its bounded representation was assembled
in memory, at 3252 characters with 5 claims and 0 violations, and was not sent anywhere.

What was established is that EU contracting authorities publish procurement classified under
this code at stated total values that differ widely within bounded sets of notices, and that
the code has exactly one stated meaning. What was not claimed: that operating sports
facilities is a good market, that its buyers want software, that anyone would pay for such a
thing, that the domain is underserved, or that a product belongs here at all. Overinterpretation
risk on the selected candidate is recorded HIGH, and the classification is
`SEMANTICALLY_COHERENT_BUT_PRODUCT_LINK_UNKNOWN`, which is a description of a research decision
and not a score.

The richest packet and the best candidate are still different things. Division 92 holds the
most rows of any procurement packet, at ten, and it means the least; it has been vetoed on
grain for three missions running. The selected class holds six rows of the same shape about a
subject with one stated meaning.

Grain 5 was not descended to. It was dry-run by Mission 1.81 and is not persisted here, and
since a subject was selected at grain 4 there is nothing a further descent would resolve.

## Adversarial probe

Thirty refusal cases and eight positive controls, each mutating a shipped artifact byte for
byte and restoring it afterwards.

```
VIOLATIONS_CAUGHT = 54    VIOLATIONS_ESCAPED = 0    CONTROLS = 7 of 7
```

It found two real defects.

**Case 13 escaped**: EUR compared to SEK without authority. The gate had a `currency_semantics`
block in the record and never read it, so a record could assert no cross-currency contrast
while the run beneath it contained one. `_check_semantics` now verifies the claim against the
cohorts themselves: every non-EUR cohort in the re-run record must be refused, and the record
must name each one.

**Control F crashed the gate** with a `TypeError` when an unresolved concept left a label
`None` and the identity check tried a substring test on it. Fixed by guarding the check and,
more importantly, by making the unresolved case explicit: a candidate whose concept the
register did not answer for may carry no label and may not adopt an exploratory hypothesis,
because that gate turns on what the subject means.

Control H was withdrawn rather than fixed. It tried to make a group win by writing a better
ordinal onto it, and the gate refused it because it recomputes that field from the packet. It
is not one of the eight controls the brief requires, and a control that cannot pass a correct
gate is not a control; the probe docstring now records why.

## Appendix — the candidate table (§46)

Every serious TED group and class candidate. `COMM` is commercial information, `PROB`
problem information, `RISK` overinterpretation risk. Independence is UNKNOWN and
provenance shapes is 1 for every one of them, so both are stated once here rather than
repeated in eighteen rows. Egress state is `UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS`
throughout, for the same reason: TED transmission is NOT_ASSESSED.

| SUBJECT_KEY | LEVEL | CODE | OFFICIAL_LABEL | NOTICES | SIG | CLM | EVID | SCOR | DIMS | RELIABILITY | FORM | COHERENCE | PRODUCT_RELEVANCE | ACTIONABLE_GRAIN | COMM | PROB | RISK | DOMINANCE | VETO |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `ted-eu:CPV-group:921` | group | `921` | Motion picture and video services | 9 | 3 | 5 | 6 | 6 | BUYE/ECON/MARK | 0.5x3, 0.55x3 | yes | RELATED_ACTIVITIES | SEMANTICALLY_COHERENT_BUT_PRODUCT_LINK_UNKNOWN | `ACTIONABLE_ONLY_AS_EXPLORATORY_CATEGORY_HYPOTHESIS` | MEDIUM | NONE | HIGH | DOMINATED | **NOT_VETOED** |
| `ted-eu:CPV-group:922` | group | `922` | Radio and television services | 2 | 0 | 0 | 0 | 0 | none | none | no | RELATED_ACTIVITIES | TOO_THIN | `NOT_ACTIONABLE` | NONE | NONE | HIGH | DOMINATED | **VETOED** |
| `ted-eu:CPV-group:923` | group | `923` | Entertainment services | 20 | 3 | 5 | 6 | 6 | BUYE/ECON/MARK | 0.5x3, 0.55x3 | yes | UNRELATED_ACTIVITIES | TOO_BROAD | `REQUIRES_NARROWER_SUBJECT_DISCOVERY` | MEDIUM | NONE | HIGH | DOMINATED | **VETOED** |
| `ted-eu:CPV-group:924` | group | `924` | News-agency services | 4 | 0 | 0 | 0 | 0 | none | none | no | SINGLE_DOMAIN | TOO_THIN | `NOT_ACTIONABLE` | NONE | NONE | HIGH | DOMINATED | **VETOED** |
| `ted-eu:CPV-group:925` | group | `925` | Library, archives, museums and other cultural services | 21 | 4 | 6 | 8 | 8 | BUYE/ECON/MARK | 0.5x4, 0.55x4 | yes | UNRELATED_ACTIVITIES | TOO_BROAD | `REQUIRES_NARROWER_SUBJECT_DISCOVERY` | MEDIUM | NONE | HIGH | DOMINATED | **VETOED** |
| `ted-eu:CPV-group:926` | group | `926` | Sporting services | 21 | 3 | 5 | 6 | 6 | BUYE/ECON/MARK | 0.5x3, 0.55x3 | yes | SINGLE_DOMAIN | SEMANTICALLY_COHERENT_BUT_PRODUCT_LINK_UNKNOWN | `ACTIONABLE_ONLY_AS_EXPLORATORY_CATEGORY_HYPOTHESIS` | MEDIUM | NONE | HIGH | DOMINATED | **NOT_VETOED** |
| `ted-eu:CPV-class:9211` | class | `9211` | Motion picture and video tape production and related services | 8 | 2 | 4 | 4 | 4 | BUYE/ECON/MARK | 0.5x2, 0.55x2 | yes | RELATED_ACTIVITIES | SEMANTICALLY_COHERENT_BUT_PRODUCT_LINK_UNKNOWN | `ACTIONABLE_ONLY_AS_EXPLORATORY_CATEGORY_HYPOTHESIS` | MEDIUM | NONE | HIGH | DOMINATED | **NOT_VETOED** |
| `ted-eu:CPV-class:9213` | class | `9213` | Motion picture projection services | 1 | 0 | 0 | 0 | 0 | none | none | no | SINGLE_DOMAIN | TOO_THIN | `NOT_ACTIONABLE` | NONE | NONE | HIGH | DOMINATED | **VETOED** |
| `ted-eu:CPV-class:9222` | class | `9222` | Television services | 1 | 0 | 0 | 0 | 0 | none | none | no | SINGLE_DOMAIN | TOO_THIN | `NOT_ACTIONABLE` | NONE | NONE | HIGH | DOMINATED | **VETOED** |
| `ted-eu:CPV-class:9231` | class | `9231` | Artistic and literary creation and interpretation services | 9 | 2 | 4 | 4 | 4 | BUYE/ECON/MARK | 0.5x2, 0.55x2 | yes | RELATED_ACTIVITIES | SEMANTICALLY_COHERENT_BUT_PRODUCT_LINK_UNKNOWN | `ACTIONABLE_ONLY_AS_EXPLORATORY_CATEGORY_HYPOTHESIS` | MEDIUM | NONE | HIGH | DOMINATED | **NOT_VETOED** |
| `ted-eu:CPV-class:9233` | class | `9233` | Recreational-area services | 5 | 1 | 2 | 2 | 2 | BUYE/ECON/MARK | 0.5x1, 0.55x1 | yes | SINGLE_DOMAIN | SEMANTICALLY_COHERENT_BUT_PRODUCT_LINK_UNKNOWN | `ACTIONABLE_ONLY_AS_EXPLORATORY_CATEGORY_HYPOTHESIS` | MEDIUM | NONE | HIGH | DOMINATED | **NOT_VETOED** |
| `ted-eu:CPV-class:9235` | class | `9235` | Gambling and betting services | 2 | 0 | 0 | 0 | 0 | none | none | no | RELATED_ACTIVITIES | TOO_THIN | `NOT_ACTIONABLE` | NONE | NONE | HIGH | DOMINATED | **VETOED** |
| `ted-eu:CPV-class:9236` | class | `9236` | Pyrotechnic services | 1 | 0 | 0 | 0 | 0 | none | none | no | SINGLE_DOMAIN | TOO_THIN | `NOT_ACTIONABLE` | NONE | NONE | HIGH | DOMINATED | **VETOED** |
| `ted-eu:CPV-class:9251` | class | `9251` | Library and archive services | 7 | 2 | 4 | 4 | 4 | BUYE/ECON/MARK | 0.5x2, 0.55x2 | yes | RELATED_ACTIVITIES | SEMANTICALLY_COHERENT_BUT_PRODUCT_LINK_UNKNOWN | `ACTIONABLE_ONLY_AS_EXPLORATORY_CATEGORY_HYPOTHESIS` | MEDIUM | NONE | HIGH | DOMINATED | **NOT_VETOED** |
| `ted-eu:CPV-class:9252` | class | `9252` | Museum services and preservation services of historical sites and buildings | 9 | 3 | 5 | 6 | 6 | BUYE/ECON/MARK | 0.5x3, 0.55x3 | yes | RELATED_ACTIVITIES | SEMANTICALLY_COHERENT_BUT_PRODUCT_LINK_UNKNOWN | `ACTIONABLE_ONLY_AS_EXPLORATORY_CATEGORY_HYPOTHESIS` | MEDIUM | NONE | HIGH | DOMINATED | **NOT_VETOED** |
| `ted-eu:CPV-class:9253` | class | `9253` | Botanical and zoological garden services and nature reserve services | 3 | 1 | 2 | 2 | 2 | BUYE/ECON/MARK | 0.5x1, 0.55x1 | yes | RELATED_ACTIVITIES | SEMANTICALLY_COHERENT_BUT_PRODUCT_LINK_UNKNOWN | `ACTIONABLE_ONLY_AS_EXPLORATORY_CATEGORY_HYPOTHESIS` | MEDIUM | NONE | HIGH | DOMINATED | **NOT_VETOED** |
| `ted-eu:CPV-class:9261` | class | `9261` | Sports facilities operation services | 16 | 3 | 5 | 6 | 6 | BUYE/ECON/MARK | 0.5x3, 0.55x3 | yes | SINGLE_DOMAIN | SEMANTICALLY_COHERENT_BUT_PRODUCT_LINK_UNKNOWN | `ACTIONABLE_ONLY_AS_EXPLORATORY_CATEGORY_HYPOTHESIS` | MEDIUM | NONE | HIGH | FRONTIER | **NOT_VETOED** |
| `ted-eu:CPV-class:9262` | class | `9262` | Sport-related services | 2 | 0 | 0 | 0 | 0 | none | none | no | RELATED_ACTIVITIES | TOO_THIN | `NOT_ACTIONABLE` | NONE | NONE | HIGH | DOMINATED | **VETOED** |

Current blockers, by group of candidates:

- **The nine formable ones**, 921, 926, 9211, 9231, 9233, 9251, 9252, 9253 and 9261: TED egress is NOT_ASSESSED, an operator decision recorded and not taken, and no problem, intervention or willingness-to-pay evidence exists at any grain.
- **The nine unformable ones**, 922, 924, 9213, 9222, 9235, 9236 and 9262 plus what they imply for 923 and 925: no cohort reaches the procedure's floor of two members, so no packet forms; 923 and 925 do form packets and are blocked instead on a label that names unrelated markets.

## Verification

All 61 CI gates pass. `ruff format --check` and `ruff check` are clean, mypy reports no issues
across the 198 source files in the 14 CI package paths, and contract generation and the source
catalog both pass `--check`. The bare-python runner reports 3647 tests across 9 packages. The
pytest suites report 293 passed with the database unchanged across 29 tenant tables. Canonical
counters were re-measured from the database after every step rather than carried from the run
records.

## Next

**Mission 1.83 — Selected Procurement Candidate Egress Review V1.** Review only whether the
bounded representation of the selected packet may be transmitted to a configured external model
under `local-private-research-v1`, and record the decision. It must not call the model,
synthesize a hypothesis, create an Opportunity, acquire research data, descend to a finer CPV
grain, or score anything.
