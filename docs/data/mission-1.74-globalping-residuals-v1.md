# Mission 1.74 — Two residuals, two questions, nothing sent

Generated from `quantity-class-selection-decision-v4.json` and the residual reviews.
Do not edit by hand.

**Primary outcome: `GLOBALPING_TWO_PROVIDER_CLARIFICATIONS_REQUIRED`**

## The two residuals

| id | verdict | closed | enquiry |
|---|---|---|---|
| R1 | `R1_PARTIAL_IMPLEMENTATION_ONLY` | False | True |
| R2 | `R2_PARTIAL_COMMERCIAL_ALLOWED_THIRD_PARTY_SCOPE_UNRESOLVED` | False | True |

What moved even though neither closed:

- **R1** — the absence is now CHECKED across five first-party surfaces rather than one, no provider test asserts the behaviour, and a maintainer statement was found that presupposes redirect responses are returned
- **R2** — R2-A closed positively on the provider's own FAQ answer, and R2-B is now a characterised ambiguity rather than an unread document: the one incorporating hook was followed and repeats the same narrow framing

## R2 splits, and only one half closes

- **commercial use** — `PERMITTED_WITHIN_TERMS`, on the provider's own answer: *"Yes, we support commercial use of Globalping within the limits of our terms of service."*
- **third-party target scope** — `UNRESOLVED`

nothing prohibits it and nothing grants it. The one textual hook that could have widened the scope -- the Terms defining Globalping by reference to the Website -- was followed, and the incorporated description repeats the same 'your infrastructure' framing. So the ambiguity is not an unread page; it is the document saying the same narrow thing twice while prohibiting nothing.

## The twelve dimensions, recomputed

| dimension | status | recomputed |
|---|---|---|
| `C1_DIRECTABLE_TARGET` | `PASS` | False |
| `C2_OWN_MEASUREMENT_PRODUCTION` | `PASS` | False |
| `C3_TERMINAL_SUBMISSION_ACCOUNTING` | `PASS` | False |
| `C4_TRANSPORT_LEVEL_RESULT_SURFACE` | `PASS` | False |
| `C5_PROSPECTIVE_TEMPORAL_ADDRESSABILITY` | `PASS` | False |
| `C6_REQUEST_CONTRACT_RECONSTRUCTABILITY` | `PARTIAL` | True |
| `C7_VANTAGE_REVIEWABILITY` | `PASS` | False |
| `C8_RESULT_MINIMIZATION` | `PASS` | False |
| `C9_RIGHTS_FEASIBILITY` | `PARTIAL` | True |
| `C10_INDEPENDENCE_PLAUSIBILITY` | `PASS` | False |
| `C11_BOUNDED_PILOT_FEASIBILITY` | `PASS` | False |
| `C12_SAME_HTTP_WORLD_STATE_FAMILY` | `PASS` | False |

**10 PASS, 2 PARTIAL, 0 FAIL.** Tally changed: **False**. Passing dimensions reopened: **0**.

What the mission added even though the tally did not move:

- R1's absence is checked across five first-party surfaces instead of one
- no provider test asserts redirect behaviour, which §9 asked and nobody had answered
- a provider maintainer statement was found that presupposes redirect responses are returned
- R2-A is closed positively on the provider's own words
- R2-B is a characterised ambiguity rather than an unread page
- both provider channels are established first-party rather than guessed
- two enquiry packets are frozen and hashed, awaiting an operator decision

## Why this outcome and not the others

| outcome | refused because |
|---|---|
| A_QUALIFIED_Q1_SELECTED | two mandatory dimensions are PARTIAL, and §36 makes PARTIAL block |
| B_QUALIFIED | same; qualification requires all twelve mandatory dimensions PASS |
| C_ONE_RESIDUAL_REMAINS | both R1 and R2 remain unresolved, so exactly one is not the state |
| E_REDIRECT_CLOSED_RIGHTS_REMAINS | R1 did not close; the evidence level is implementation-observed |
| F_RIGHTS_CLOSED_REDIRECT_REMAINS | R2 did not close either. Its commercial half closed and its third-party target half did not, and §25 requires both |
| G_PROVIDER_TERMS_BLOCK | §61 forbids using it from ambiguity. Prohibited Use does not prohibit the activity, and an ambiguous Permitted Use section is not an explicit prohibition |
| H_REDIRECT_CONTRACT_INCOMPATIBLE | nothing establishes an incompatible documented behaviour. Every signal points at not following redirects, which is what the SROS side would want; what is missing is the commitment, not the compatibility |

## The two frozen enquiries

| id | residual | channel | hash | status |
|---|---|---|---|---|
| GP-R1-Q1 | R1 | `PUBLIC_TECHNICAL_CHANNEL` | `9eb7454581b65ccb…` | **NOT_AUTHORIZED** |
| GP-R2-Q1 | R2 | `PROVIDER_DESIGNATED_TERMS_CHANNEL` | `713d62c91ac56934…` | **NOT_AUTHORIZED** |

§29. R1 is a technical contract question suited to the provider's public issue tracker; R2 is a Terms question and the Terms themselves designate legal@globalping.io. Two provider-designated channels are genuinely required, so one packet could not have carried both without sending a Terms question to a technical channel.

**Enquiries sent: 0. Operator approval recorded: False. Provider contacted: False.**

## Q1

`PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED`, unchanged (False). Failing on `one_external_counterpart_qualified`.

Independence: `INDEPENDENCE_ARCHITECTURE_PLAUSIBLE`, 0 groups, `PAIR_ANALYSIS_NOT_READY`.

## Nothing moved

| | |
|---|---|
| GLOBALPING_API_EXECUTIONS | 0 |
| GLOBALPING_MEASUREMENTS_CREATED | 0 |
| TARGET_HTTP_REQUESTS | 0 |
| SROS_FETCHER_RUNS | 0 |
| ACCOUNTS_CREATED | 0 |
| TOKENS_CREATED | 0 |
| CREDENTIAL_READS | 0 |
| ENQUIRIES_SENT | 0 |
| PROVIDER_CONTACTS | 0 |
| ALTERNATIVE_COUNTERPARTS_EVALUATED | 0 |
| CLAIMS_CREATED | 0 |
| INDEPENDENCE_GROUPS_CREATED | 0 |
| MODEL_CALLS | 0 |
