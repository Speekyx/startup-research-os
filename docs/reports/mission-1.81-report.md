# Mission 1.81 — Narrower is not actionable

**Outcome: `PROCUREMENT_NARROWING_REQUIRES_DEEPER_CPV_GRAIN`.**

The division was narrowed into CPV groups from held data alone, through the existing
procedure with its grain as a required parameter. Four group packets came out formable and
scorable at the reviewed TED reliabilities, and none of them is a second-Opportunity
candidate: each is a category one level down whose held cohort still spans several classes,
and no held record carries a label for any level, so the held data cannot say what a group
is. The outcome fits imperfectly and the record says so: descending is possible and was
dry-run two levels further, and it does not supply the missing input, which is semantic.

---

## Report

```
START_COMMIT                        = 34fc556          BRANCH = sprint-1/mission-1.81
MIGRATION_HEAD                      = 0036_grant_use_profile_vocabulary (measured)
DIVISION_92_HELD_NOTICES            = 177 (CN 115 / CAN 62; windows A 94 / B 83)
CPV_TOKEN_FORMAT                    = eight digits, no check digit, label null on all 608 entries
NARROWING_LEVEL / NAME              = 3 / group (CPV_LEVELS = {2 division, 3 group, 4 class, 5 category})
NOTICE_CPV_CARDINALITY_DISTRIBUTION = 1:77 2:29 3:20 4:16 5:14 6:3 7:1 8:4 9:2 10:2 11:1 12:1 13:2 16:2 22:1 36:1 45:1
MULTI_CPV_NOTICES                   = 100        PRIMARY/ADDITIONAL STATUS = UNAVAILABLE
AMBIGUOUS_MEMBERSHIP_NOTICES        = 91 (88 across divisions, 3 across groups); unspecified at group 9
MEMBERSHIP_MODEL_SELECTED           = C4_REFUSE_AMBIGUOUS_NOTICE
NARROW_COHORT_COUNT                 = 4 with signals (921, 923, 925, 926); 922 and 924 held and refused (1 member each)
NARROW_COHORTS  921: 9 notices, 3 signals   923: 20, 3   925: 21, 4   926: 21, 3   922: 2, 0   924: 4, 0
DERIVATION_MODEL                    = C_RE_DERIVE_FROM_HELD_NORMALIZED_RECORDS (every division signal spans 2 to 6 groups)
EXISTING_SIGNAL_TYPES_REUSED        = procurement_value_contrast (procurement-value-contrast@1.2.0, cpv_grain=3)
NEW_SIGNAL_TYPE_CREATED             = false
MINIMUM_REQUIRED_BY_PROCEDURE       = 2          COHORTS_REFUSED_FOR_INSUFFICIENT_INPUT = 10
NEW_SIGNALS / CLAIMS / REVISIONS / EVIDENCE = 13 / 21 (13 detailed, 8 witnessed) / 21 / 26
SCORABLE_NEW_EVIDENCE / NONSCORABLE = 26 / 0   (13 at 0.5 via 3de2af10, 13 at 0.55 via d1afa4be; scope unchanged)
PREPARATION_VERSION_BEFORE / AFTER  = opportunity-preparation@2.0.0 / @3.0.0 (v1, v2 byte-identical)
FORMABLE_NARROW_PACKETS             = 4          ACTIONABLE_NARROW_PACKETS = 0
PARETO_FRONTIER                     = CPV-division:92, CPV-group:921, 923, 925, 926, kubernetes, podman
DOMINATED                           = CPV-division:90, WB DE, WB FR, 3 GDELT      VETOED = all 13
BEST_NARROW_HELD_PACKET             = ted-eu:CPV-group:925 (8 rows, 4 cohorts)
BEST_SECOND_OPPORTUNITY_CANDIDATE   = none      SELECTED_SUBJECT / SCOPE = none / none
ACTIONABLE_GRAIN (each group)       = REQUIRES_NARROWER_SUBJECT_DISCOVERY
SELECTION_BASIS                     = no candidate at a selectable grain; groups are bare codes with no held label
TED_EGRESS_STATE                    = NOT_ASSESSED     EGRESS_REVIEW_REQUIRED_BEFORE_SYNTHESIS = true, not decided
OPPORTUNITY_CREATED = 0   MODEL_CALLS = 0   EXTERNAL_ACTIONS = 0
CANONICAL_MUTATION_SUMMARY          = signals 33->46, claims 44->65, revisions 45->66, evidence 58->84; everything else unchanged
IDEMPOTENT_SECOND_RUN               = true (13 skipped as existing witness, 0 signals, 0 claims, 0 evidence)
VIOLATIONS_CAUGHT / ESCAPED         = 44 / 0    positive controls 6 of 6
PRIMARY_OUTCOME                     = PROCUREMENT_NARROWING_REQUIRES_DEEPER_CPV_GRAIN
NEXT_MISSION                        = 1.82 Procurement Subject Semantics and Class-Grain Narrowing V1
```

Preconditions verified: tree clean, `main` == `origin/main` at `34fc556`, Mission 1.80 merged,
one Opportunity at revision 2 with 14 links, 4 assessments, 0 groups, no scores table, 325
RawRecords, 58 Evidence, 70 reviews, migration head 0036. All re-measured.

## The grain is what the held token says it is

A held CPV code is eight digits with no check digit and a null label, on every one of the
608 code entries across the 177 notices. Its depth is its leading digits before the trailing
zeros. The repository had named one level, the division (two digits). The vocabulary's own
structure names the levels by successive digits, and the extractor now carries that as
`CPV_LEVELS` with the basis stated. **Mission 1.80's prose used "class" for five-digit
prefixes, which the vocabulary calls categories, and its labels were recalled rather than
held.** Both are corrected in the record; the codes and counts stand.

## Membership is decided by codes, before any value is read

No held entry marks a code as main or additional, so primary status is UNAVAILABLE and the
model that needs it is refused. A notice may carry several codes: 100 of 177 do, and 88 carry
a code from another division. The extractor has refused a notice across divisions since its
first version, and the smallest truthful rule at group grain is the same one applied one level
down: a notice joins the cohort of the one group prefix shared by every code deep enough to
name a group, a shallower code must be an ancestor of that prefix, and any other shape joins
no cohort. That leaves 77 group-specified notices in six groups, 91 ambiguous and 9
unspecified. Nothing was deduplicated to make the tally sum to 177; it sums because every
notice is in exactly one of those states. Value-missing notices stay in their group's
membership and contribute no amount.

**The division packet's ten rows were never derived from 177 notices.** They come from the
89 single-division notices, because the other 88 were already refused at the division.

## The derivation is a re-derivation

Every one of the five division-92 Signals spans between two and six groups, so its magnitude is
a spread across groups and no child can carry it: reuse and filtering were refused on that
measurement. The existing extractor gained `cpv_grain` as a required parameter, like
`amount_type`, because the signal model refuses a declared parameter left unstated. The key,
the amount eligibility, the floor of two, the currency and scope rules and the contrast are
unchanged; only which prefix the members must share moves. The level and its code are written
into the Signal scope, the claim template states them in the sentence and carries them as
identity facts, and the convergence contract declares them conditional identity, so a group
cohort witnesses its own broader claim and never the division's.

Over the two frozen Mission 1.40 windows, 23 group cohorts were keyed, 13 derived and 10
refused at the procedure's own floor, one member each, four of them non-EUR singletons. Thirteen
Signals, thirteen detailed Claims, eight witnessed Claims, twenty-six Evidence rows, all
scorable: the reliability scope carries neither division nor level, and the reviewed
limitations on BT-161 are true of a group cohort exactly as of a division one. No scope was
broadened, narrowed or created. The second execution met every persisted witness and created
nothing.

## Narrower is not actionable

The re-selection ran Mission 1.80's gates over the v3 preparation, with one refinement: a
category one level below the coarsest reads MEDIUM specificity rather than LOW, because it is
narrower than its parent and still not a product. The four groups join the frontier on that
field and lose nothing to the division; and every one is vetoed. Each is a CATEGORY whose held
cohort spans two to five classes, and no held record says what the group is, so the structural
rule Mission 1.80 applied to the division applies one level down and nothing held overrides it.
A bare code is not a subject a hypothesis can be written about, and the gate now refuses a
group with no held label at a selectable grain.

**The information-gain test says why descending alone will not fix it.** Grains 4 and 5 were
dry-run: fourteen and six cohorts, smaller and of the same three dimensions. The structural
too-broad test terminates only at leaf codes, so applied blindly it descends to eight-digit
codes and singleton cohorts. The deciding input is the vocabulary's label, which is a
documentation read this mission was not permitted to perform.

## Verification

- Probe: **44 deliberate violations, 44 caught, 0 escaped**, plus **6 of 6 positive controls**:
  a valid finer-grain cohort, valid multi-membership handling, a valid insufficient-input
  refusal, a valid selected narrower candidate once a label is held and the grain earned, the
  shipped deeper-narrowing outcome, and the idempotent re-run. One probe case edited the v1
  preparation outside the restore set on its first run and every later case was caught by
  drift rather than by its rule; the file was restored from git, the restore set widened, and
  the run repeated with every case caught by its own rule.
- Two defects found by running: the scope validation first rejected an ancestor code beside a
  finer one, and the prefix rule first treated a shallower sibling as an ancestor; both were
  found at grain 5, neither touched the persisted grain-3 rows, and both are tested.
- **3610 bare-python tests**; nlp, claim-model, opportunity-engine and evidence-aggregation
  suites green; pytest suites green with the database unchanged; `ruff format --check`,
  `ruff check`, mypy over 198 files; contract and catalog `--check`; all **60** CI gates, one
  new.
- Counters: RawRecords, NormalizedRecords, assessments, groups, Opportunities, revisions, links,
  reviews, scores and embeddings identical before and after; Signals, Claims, revisions and
  Evidence moved by exactly the derivation.
- **Two things CI caught on the first push, and the first was my own miss.** A Mission 1.30
  test asserted that the v1 preparation record carries the live grouping version; v1 has been
  a frozen historical record since Mission 1.78, so the pin asserted the procedure may never
  move, and the local pytest tail I read cut the failing line off. Re-pointed to the literal v1
  recorded plus the current record carrying the module constant, and the full local run
  re-read to its last line. And the secret scanner flagged the run record's proposition keys,
  SHA-256 strings beside the word key; they are not copied into the record any more, because
  the claim id reaches them.

## Next

**Mission 1.82 — Procurement Subject Semantics and Class-Grain Narrowing V1**, one bounded
documentation mission: read the vocabulary's own labels for the six held groups and fourteen
held classes from the Publications Office authority register, one concept per fetch as Mission
1.40 did for divisions; decide per group whether an exploratory category hypothesis is
adoptable; derive class-grain cohorts from held records only where a label makes the class a
coherent subject; re-select under the same gates. No research-data acquisition, no model, no
egress decision, no Opportunity, no descent below the class without testing information gain.
**It was not started.**
