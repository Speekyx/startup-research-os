# Which held subject is the second-Opportunity candidate?

Generated from `second-opportunity-candidate-selection-v1.json`. Do not edit by hand.

**SECOND_OPPORTUNITY_REQUIRES_SUBJECT_NARROWING** — selected `None`; best held evidence packet `ted-eu:CPV-division:92`; best second-Opportunity candidate `None`; next 1.81 Procurement Subject-Grain Narrowing V1.

no candidate passes every load-bearing gate: the only frontier candidate, ted-eu:CPV-division:92, is the best held evidence packet and is a CATEGORY whose held cohorts span at least six distinct CPV classes, so a hypothesis at its grain would be a disjunction of unrelated service markets and no product intervention is grounded; every other candidate is vetoed

## Candidates

| subject | scope | rows | scorable | counting dimensions | reliabilities | formable | egress | intervention grain | actionable grain | dominance | veto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `ted-eu:CPV-division:92` | CATEGORY | 10 | 10 | BUYER_OR_BUDGET_EXISTENCE, ECONOMIC_VALUE, MARKET_ACTIVITY | 0.5: 5, 0.55: 5 | True | UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS | `TOO_BROAD_TO_BE_ACTIONABLE` | `REQUIRES_NARROWER_SUBJECT_DISCOVERY` | FRONTIER | **VETOED** |
| `ted-eu:CPV-division:90` | CATEGORY | 2 | 2 | BUYER_OR_BUDGET_EXISTENCE, ECONOMIC_VALUE, MARKET_ACTIVITY | 0.5: 1, 0.55: 1 | True | UNAVAILABLE_FOR_EXTERNAL_SYNTHESIS | `TOO_BROAD_TO_BE_ACTIONABLE` | `REQUIRES_NARROWER_SUBJECT_DISCOVERY` | DOMINATED | **VETOED** |
| `subject:kubernetes` | PRODUCT | 13 | 12 | AUDIENCE_OR_USAGE | 0.65: 6, 0.6: 6, NONE: 1 | False | AVAILABLE | `PLAUSIBLE_BUT_REQUIRES_SYNTHESIS` | `NOT_ACTIONABLE` | FRONTIER | **VETOED** |
| `subject:podman` | PRODUCT | 12 | 12 | AUDIENCE_OR_USAGE | 0.65: 6, 0.6: 6 | False | AVAILABLE | `PLAUSIBLE_BUT_REQUIRES_SYNTHESIS` | `NOT_ACTIONABLE` | FRONTIER | **VETOED** |
| `world-bank:metric-geography:SP.POP.TOTL|DE` | GEOGRAPHY | 2 | 0 | none | NONE: 2 | False | AVAILABLE | `NOT_ESTABLISHED` | `NOT_ACTIONABLE` | DOMINATED | **VETOED** |
| `world-bank:metric-geography:SP.POP.TOTL|FR` | GEOGRAPHY | 2 | 0 | none | NONE: 2 | False | AVAILABLE | `NOT_ESTABLISHED` | `NOT_ACTIONABLE` | DOMINATED | **VETOED** |
| `gdelt:lexical-term:ENGLISH|climate` | UNDETERMINED | 1 | 0 | none | NONE: 1 | False | AVAILABLE | `NOT_ESTABLISHED` | `NOT_ACTIONABLE` | DOMINATED | **VETOED** |
| `gdelt:lexical-term:ENGLISH|climate|weather` | UNDETERMINED | 1 | 0 | none | NONE: 1 | False | AVAILABLE | `NOT_ESTABLISHED` | `NOT_ACTIONABLE` | DOMINATED | **VETOED** |
| `gdelt:lexical-term:ENGLISH|weather` | UNDETERMINED | 1 | 0 | none | NONE: 1 | False | AVAILABLE | `NOT_ESTABLISHED` | `NOT_ACTIONABLE` | DOMINATED | **VETOED** |

## Ordinal fields

| subject | EVIDENCE_BREADTH | SCORABLE_BREADTH | COUNTING_DIMENSION_DIVERSITY | SOURCE_DIVERSITY | COMMERCIAL_INFORMATION | PROBLEM_INFORMATION | PRODUCT_RELEVANCE | SEMANTIC_SPECIFICITY | PROVENANCE_DIVERSITY | INDEPENDENCE | HYPOTHESIS_FORMABILITY | GOVERNANCE_DISTANCE_TO_SYNTHESIS | NEW_ACQUISITION_REQUIRED | OPERATOR_JUDGMENT_REQUIRED | ARCHITECTURE_WORK_REQUIRED | OVERINTERPRETATION_RISK |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `ted-eu:CPV-division:92` | HIGH | HIGH | HIGH | LOW | MEDIUM | NONE | UNKNOWN | LOW | LOW | UNKNOWN | YES | LOW | NO | YES | YES | HIGH |
| `ted-eu:CPV-division:90` | LOW | MEDIUM | HIGH | LOW | LOW | NONE | UNKNOWN | LOW | LOW | UNKNOWN | YES | LOW | NO | YES | YES | HIGH |
| `subject:kubernetes` | HIGH | HIGH | LOW | LOW | NONE | NONE | LOW | HIGH | LOW | UNKNOWN | NO | NONE | YES | NO | NO | MEDIUM |
| `subject:podman` | HIGH | HIGH | LOW | LOW | NONE | NONE | LOW | HIGH | LOW | UNKNOWN | NO | NONE | YES | NO | NO | MEDIUM |
| `world-bank:metric-geography:SP.POP.TOTL|DE` | LOW | LOW | LOW | LOW | NONE | NONE | LOW | HIGH | LOW | UNKNOWN | NO | NONE | YES | NO | NO | HIGH |
| `world-bank:metric-geography:SP.POP.TOTL|FR` | LOW | LOW | LOW | LOW | NONE | NONE | LOW | HIGH | LOW | UNKNOWN | NO | NONE | YES | NO | NO | HIGH |
| `gdelt:lexical-term:ENGLISH|climate` | LOW | LOW | LOW | LOW | NONE | NONE | LOW | LOW | LOW | UNKNOWN | NO | NONE | YES | NO | NO | HIGH |
| `gdelt:lexical-term:ENGLISH|climate|weather` | LOW | LOW | LOW | LOW | NONE | NONE | LOW | LOW | LOW | UNKNOWN | NO | NONE | YES | NO | NO | HIGH |
| `gdelt:lexical-term:ENGLISH|weather` | LOW | LOW | LOW | LOW | NONE | NONE | LOW | LOW | LOW | UNKNOWN | NO | NONE | YES | NO | NO | HIGH |

Frontier ['ted-eu:CPV-division:92', 'subject:kubernetes', 'subject:podman']; dominated ['ted-eu:CPV-division:90', 'world-bank:metric-geography:SP.POP.TOTL|DE', 'world-bank:metric-geography:SP.POP.TOTL|FR', 'gdelt:lexical-term:ENGLISH|climate', 'gdelt:lexical-term:ENGLISH|climate|weather', 'gdelt:lexical-term:ENGLISH|weather']; vetoed ['ted-eu:CPV-division:92', 'ted-eu:CPV-division:90', 'subject:kubernetes', 'subject:podman', 'world-bank:metric-geography:SP.POP.TOTL|DE', 'world-bank:metric-geography:SP.POP.TOTL|FR', 'gdelt:lexical-term:ENGLISH|climate', 'gdelt:lexical-term:ENGLISH|climate|weather', 'gdelt:lexical-term:ENGLISH|weather'].

kubernetes and podman sit on the frontier because they name a product and division 92 names a category; semantic specificity is a dominance field, so the richer packet does not dominate them. Both are vetoed on formability, which is the gate a frontier place does not waive. The frontier is what the stated rule produces, not what the author first wrote: the first draft listed both as dominated by division 92.

## What division 92 establishes, and does not

- **Establishes.** TED published, in its eforms contract-and-award resource, bounded sets of CONTRACT_NOTICE and CONTRACT_AWARD_NOTICE notices classified under CPV division 92 whose stated TOTAL_VALUE amounts at notice scope differ from one another (contrasts of 86,897,500 EUR; 16,581,256 EUR; 14,695,337 EUR; 1,774,223.99 EUR; 15,000,000 SEK); contracting authorities exist in this category; classified procurement activity exists
- **Does not establish.** actual expenditure (BT-161 includes options and renewals and may never be exercised); willingness to pay for any proposed product; market size; product demand; a buyer for an unspecified future SaaS; addressable revenue; unmet need; dissatisfaction; a solution gap; which of the six-plus service classes any of it concerns
- **A synthesis could say.** that EU contracting authorities publish procurement in recreational, cultural and sporting services with widely differing notice values, i.e. an active commercial category with buyers who publish what they buy
- **It could not say.** what is bought, by whom, for what need, whether any of it is underserved, or which service market a product would enter; the hypothesis would name a disjunction of film, sports, museum, artistic and news-agency services

## Egress

EGRESS_REVIEW_REQUIRED_BEFORE_SYNTHESIS: **True**. external_model_transmission NOT_ASSESSED under local-private-research-v1. Decided here: False. permission to send a bounded representation to a model and evidence sufficiency are separate questions; a candidate is selected on its evidence and blocked on its egress

## Narrowing

the 177 held division-92 notices carry their CPV class codes on every record: at least six classes with seven or more notices each (motion picture and video services, sports facility operation, museum services, news agency services, artistic services, sound technician services); a class-grain cohort is a re-derivation over held NormalizedRecords, not an acquisition a class-grain cohort derivation (the procurement-value-contrast extractor groups by division), a class-grain subject key in the grouping procedure, currency-pure cohorts as Mission 1.41 requires, and a re-run of the preparation runner; the two reviewed TED reliability scopes carry no classification division and would bind unchanged (Mission 1.40, 1.42)

**Next: Procurement Subject-Grain Narrowing V1.** held data only: derive CPV-class-grain cohorts from the held division-92 NormalizedRecords, define class-grain subject keys in the grouping procedure, re-run the preparation runner, and re-select among the class-grain packets against the same gates; no acquisition, no model, no egress decision, no Opportunity
