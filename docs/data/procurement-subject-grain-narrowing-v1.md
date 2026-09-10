# Narrowing the procurement subject from the division to the group

Generated from `procurement-subject-grain-narrowing-v1.json`. Do not edit by hand.

**PROCUREMENT_NARROWING_REQUIRES_DEEPER_CPV_GRAIN** — re-selection `SECOND_OPPORTUNITY_REQUIRES_SUBJECT_NARROWING`; best narrow held packet `ted-eu:CPV-group:925`; selected `None`; next 1.82 Procurement Subject Semantics and Class-Grain Narrowing V1.

the closest of the six named outcomes, and it fits imperfectly, which the record says: the group-grain cohorts are truthful, formable and scorable, and no group is selectable at its grain because the held data cannot decide its actionability. Descending is possible and was dry-run at grains 4 and 5; it does not by itself supply the missing input, which is the vocabulary's label. So the one further grain-level mission this outcome licenses must carry that label as a semantic input, and a blind descent is refused here.

## The grain

Held token: eight decimal digits, no check digit, no separator; scheme 'CPV'; label null on every held entry. Narrowing level 3 (group). the Common Procurement Vocabulary's own published structure names its levels by successive digits: division (2), group (3), class (4), category (5). This repository had named only the division before this mission (CPV_DIVISION_LENGTH); the level names are the vocabulary's, adopted in CPV_LEVELS with that basis stated, and no held token carries a level name. Mission 1.80's prose used 'class' for five-digit prefixes, which the vocabulary calls categories; corrected here.

## The held corpus

177 held notices (115 CONTRACT_NOTICE, 62 CONTRACT_AWARD_NOTICE), 100 carrying more than one CPV code, 89 in one division, 125 with a paired TOTAL_VALUE. Primary/additional status: UNAVAILABLE. Membership model C4_REFUSE_AMBIGUOUS_NOTICE: at grain L a notice joins the cohort of the one L-digit prefix shared by every code it carries that is at least L digits deep; a code shallower than L must be an ancestor of that prefix; every code must share the division; otherwise the notice joins no cohort at grain L

| group | held notices | notice types | values | derived cohorts | refused | signals | claims | evidence | scorable | formable | egress |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `ted-eu:CPV-group:921` | 9 | {'CONTRACT_NOTICE': 6, 'CONTRACT_AWARD_NOTICE': 3} | 7 | 3 | 1 | 3 | 5 | 6 | 6 | True | UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS |
| `ted-eu:CPV-group:922` | 2 | {'CONTRACT_AWARD_NOTICE': 1, 'CONTRACT_NOTICE': 1} | 2 | 0 | 2 | 0 | 0 | 0 | 0 | False | None |
| `ted-eu:CPV-group:923` | 20 | {'CONTRACT_NOTICE': 12, 'CONTRACT_AWARD_NOTICE': 8} | 13 | 3 | 2 | 3 | 5 | 6 | 6 | True | UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS |
| `ted-eu:CPV-group:924` | 4 | {'CONTRACT_AWARD_NOTICE': 2, 'CONTRACT_NOTICE': 2} | 2 | 0 | 2 | 0 | 0 | 0 | 0 | False | None |
| `ted-eu:CPV-group:925` | 21 | {'CONTRACT_NOTICE': 12, 'CONTRACT_AWARD_NOTICE': 9} | 19 | 4 | 1 | 4 | 6 | 8 | 8 | True | UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS |
| `ted-eu:CPV-group:926` | 21 | {'CONTRACT_NOTICE': 17, 'CONTRACT_AWARD_NOTICE': 4} | 17 | 3 | 2 | 3 | 5 | 6 | 6 | True | UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS |

## The derivation

C_RE_DERIVE_FROM_HELD_NORMALIZED_RECORDS through `procurement-value-contrast@1.2.0` with parameters {'amount_type': 'TOTAL_VALUE', 'cpv_grain': 3}; floor 2 from the procedure; 13 cohorts derived, 10 refused; 13 Signals, 21 Claims (13 detailed, 8 witnessed), 26 Evidence, 26 scorable. a reliability scope is measurement by purpose: source, resource, record kind, claim type and proposition kind. It carries no classification division (Missions 1.40 and 1.42 recorded that it binds divisions 90 and 92 alike) and it carries no classification level: the group-grain rows are the same measurement (BT-161 stated total values on the same resource and record kind) restated under the same two proposition kinds, with the level as a fact inside the proposition rather than a new kind of proposition. The reviewed limitations (options and renewals inside BT-161, unverified by TED; correction and supersession unestablished) are true of a group cohort exactly as of a division one.

## Information gain

descending is possible from held data at grains 4 and 5 and produces smaller cohorts of the same three dimensions; it changes nothing about whether a subject at that grain names one market, one service or one buyer need, because the held records carry codes and no labels at any level and the code structure splits at every level until the leaf. The structural too-broad test Mission 1.80 applied to the division is necessary and is not sufficient: applied blindly it descends to eight-digit codes and singleton cohorts. The next grain-level step is warranted only with the vocabulary's own labels for the held groups and classes as a semantic input, which is a documentation read and not an acquisition, and which this mission was not permitted to perform.

## Re-selection

no candidate passes every load-bearing gate: the four group packets are formable, scorable at reviewed reliabilities and narrower than the division, and each is a category whose held cohort still spans several classes and whose label is not held, so actionable grain cannot be established from held data; every other candidate is vetoed as in Mission 1.80

Frontier ['subject:kubernetes', 'subject:podman', 'ted-eu:CPV-division:92', 'ted-eu:CPV-group:921', 'ted-eu:CPV-group:923', 'ted-eu:CPV-group:925', 'ted-eu:CPV-group:926']; vetoed ['gdelt:lexical-term:ENGLISH|climate', 'gdelt:lexical-term:ENGLISH|climate|weather', 'gdelt:lexical-term:ENGLISH|weather', 'subject:kubernetes', 'subject:podman', 'ted-eu:CPV-division:90', 'ted-eu:CPV-division:92', 'ted-eu:CPV-group:921', 'ted-eu:CPV-group:923', 'ted-eu:CPV-group:925', 'ted-eu:CPV-group:926', 'world-bank:metric-geography:SP.POP.TOTL|DE', 'world-bank:metric-geography:SP.POP.TOTL|FR'].

Counters: signals 33 to 46, claims 44 to 65, evidence 58 to 84; every other counter unchanged; second run persisted 0.

**Next: Procurement Subject Semantics and Class-Grain Narrowing V1.** one bounded documentation mission: read the vocabulary's own labels for the six held groups and fourteen held classes from the Publications Office authority register, one concept per fetch as Mission 1.40 did; decide per group whether an exploratory category hypothesis is adoptable; derive class-grain cohorts from held records only where the label makes the class a coherent subject; re-select. No research-data acquisition, no model, no egress decision, no Opportunity.
