# The Globalping residuals — one closed, one open

Generated from `quantity-class-selection-decision-v5.json` and the residual reviews.
Do not edit by hand.

**Primary outcome: `GLOBALPING_REDIRECT_CONTRACT_CLOSED_RIGHTS_SCOPE_REMAINS`**

## The two residuals

| id | verdict | closed | enquiry |
|---|---|---|---|
| R1 | `R1_PASS_PROVIDER_DECLARED_NO_REDIRECT` | True | True |
| R2 | `R2_PARTIAL_COMMERCIAL_ALLOWED_THIRD_PARTY_SCOPE_UNRESOLVED` | False | True |

What moved:

- **R1** (**closed**) — the enquiry was sent, an organisation member answered the exact question directly, and both required semantics are established. The behaviour is now provider-declared rather than only implementation-observed.
- **R2** (still open) — unchanged by this mission. R2-A remains closed on the provider's FAQ and R2-B remains unresolved; the v2 enquiry was sent and no reply has arrived.

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
| `C6_REQUEST_CONTRACT_RECONSTRUCTABILITY` | `PASS` | True |
| `C7_VANTAGE_REVIEWABILITY` | `PASS` | False |
| `C8_RESULT_MINIMIZATION` | `PASS` | False |
| `C9_RIGHTS_FEASIBILITY` | `PARTIAL` | False |
| `C10_INDEPENDENCE_PLAUSIBILITY` | `PASS` | False |
| `C11_BOUNDED_PILOT_FEASIBILITY` | `PASS` | False |
| `C12_SAME_HTTP_WORLD_STATE_FAMILY` | `PASS` | False |

**11 PASS, 1 PARTIAL, 0 FAIL.** Tally changed: **True**. Passing dimensions reopened: **0**.

**Verdict: `COUNTERPART_UNRESOLVED`.** qualification needs all twelve mandatory dimensions PASS. C9 is PARTIAL on R2, and PARTIAL blocks. A better tally is not a verdict.

What this mission added:

- R1 closed on a solicited, responsive, attributable provider answer
- the reply is frozen verbatim in its own record before any interpretation reads it
- the posted issue body was compared byte for byte against the frozen packet, so the reply is attached to the question this project asked rather than to a paraphrase
- C6 moves from PARTIAL to PASS and the tally from 10/2/0 to 11/1/0
- the verdict does not move, because one residual remains

## Why this outcome and not the others

| outcome | refused because |
|---|---|
| A_QUALIFIED_Q1_SELECTED | C9 is still PARTIAL, and §36 makes PARTIAL block |
| B_QUALIFIED | same; qualification requires all twelve mandatory dimensions PASS |
| C_ONE_RESIDUAL_REMAINS | true but weaker than the state. Exactly one residual does remain, and the outcome below says WHICH, which is the difference between a count and a fact |
| D_TWO_CLARIFICATIONS_REQUIRED | R1 closed on a solicited provider answer, so two is no longer the count |
| F_RIGHTS_CLOSED_REDIRECT_REMAINS | the mirror image of what happened; R2's third-party half is still unresolved |
| G_PROVIDER_TERMS_BLOCK | §61 forbids using it from ambiguity. Prohibited Use does not prohibit the activity, and an ambiguous Permitted Use section is not an explicit prohibition |
| H_REDIRECT_CONTRACT_INCOMPATIBLE | the opposite was established: the provider states it returns the redirect response and does not follow it, which is the behaviour the SROS side wants |

## The two frozen enquiries

| id | residual | channel | hash | the packet's own field | dispatch |
|---|---|---|---|---|---|
| GP-R1-Q1 | R1 | `PUBLIC_TECHNICAL_CHANNEL` | `9eb7454581b65ccb…` | `NOT_AUTHORIZED` | **SENT** |
| GP-R2-Q1 | R2 | `PROVIDER_DESIGNATED_TERMS_CHANNEL` | `713d62c91ac56934…` | `NOT_AUTHORIZED` | **SENT (v2 packet)** |

A packet's own `send_status` means THIS DOCUMENT RECORDS NO AUTHORIZATION and never that none exists. The approvals live beside the packets, and the dispatch column reads from them.

§29. R1 is a technical contract question suited to the provider's public issue tracker; R2 is a Terms question and the Terms themselves designate legal@globalping.io. Two provider-designated channels are genuinely required, so one packet could not have carried both without sending a Terms question to a technical channel.

**Enquiries sent: 2. Operator approval recorded: True. R1 reply received: True. R2 reply received: False.**

Provider contacted: **True**. R1 only. The public issue carries a provider reply, which is receipt demonstrated rather than inferred. R2's email remains an attested dispatch with an unconfirmed delivery, and its own record still reads provider_contacted false.

## Q1

`PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED`, unchanged (False). Failing on `one_external_counterpart_qualified`.

Independence: `INDEPENDENCE_ARCHITECTURE_PLAUSIBLE`, 0 groups, `PAIR_ANALYSIS_NOT_READY`.

## What Mission 1.74 did not do, and this mission still has not

These count MISSION 1.74's own actions and are carried forward unchanged. The enquiries were sent later, by the operator, and are counted in the dispatch records rather than here.

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
