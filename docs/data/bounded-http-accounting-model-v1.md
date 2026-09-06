# Mission 1.71 — The accounting model

Generated from `bounded-http-terminal-outcome-taxonomy-v1.json` and the missingness
contract. Do not edit by hand.

**`corpus_manifest_count == terminal_target_records_count`**

Exactly one terminal record per manifest item per governed run. No item disappears,
and a retry is a child attempt rather than a new population member.

## Terminal outcomes

| terminal | furthest stage certified | missingness class | attempted |
|---|---|---|---|
| `TARGET_EXCLUDED_PRE_RUN` | SCHEDULED | `NOT_ATTEMPTED_POLICY` | False |
| `SCHEME_NOT_PERMITTED` | SCHEDULED | `NOT_ATTEMPTED_POLICY` | False |
| `ROBOTS_DISALLOWED` | SCHEDULED | `NOT_ATTEMPTED_POLICY` | False |
| `POLICY_SKIPPED` | SCHEDULED | `NOT_ATTEMPTED_POLICY` | False |
| `RUN_ABORTED_BEFORE_ATTEMPT` | SCHEDULED | `NOT_ATTEMPTED_POLICY` | False |
| `DESTINATION_SAFETY_REJECTED` | SCHEDULED | `NOT_ATTEMPTED_SAFETY` | False |
| `DNS_FAILURE` | ATTEMPTED | `ATTEMPTED_NO_CONNECTION` | True |
| `DNS_TIMEOUT` | ATTEMPTED | `ATTEMPTED_NO_CONNECTION` | True |
| `CONNECT_FAILURE` | ATTEMPTED | `ATTEMPTED_NO_CONNECTION` | True |
| `CONNECT_TIMEOUT` | ATTEMPTED | `ATTEMPTED_NO_CONNECTION` | True |
| `TLS_FAILURE` | ATTEMPTED | `ATTEMPTED_TLS_FAILURE` | True |
| `READ_TIMEOUT` | ATTEMPTED | `ATTEMPTED_NO_HTTP_RESPONSE` | True |
| `HTTP_PROTOCOL_FAILURE` | ATTEMPTED | `ATTEMPTED_NO_HTTP_RESPONSE` | True |
| `REDIRECT_POLICY_STOP` | RESPONSE_RECEIVED | `HTTP_RESPONSE_NOT_EVALUABLE` | True |
| `RESPONSE_LIMIT_EXCEEDED` | RESPONSE_RECEIVED | `HTTP_RESPONSE_NOT_EVALUABLE` | True |
| `HTTP_RESPONSE_RECEIVED` | RESPONSE_RECEIVED | `OBSERVATION_AVAILABLE` | True |
| `INTERNAL_FETCHER_ERROR` | APPARATUS_FAILED | `APPARATUS_FAILURE_NOT_A_WORLD_FACT` | False |

**17 terminals over 8 missingness classes.** Every terminal maps to exactly one
class, and no class is unreachable.

Why, for each:

- **TARGET_EXCLUDED_PRE_RUN** — the operator placed it in TARGET_POLICY_EXCLUSION_SET before the run, with a recorded reason
- **SCHEME_NOT_PERMITTED** — the manifest URL carries a scheme outside http and https
- **ROBOTS_DISALLOWED** — reachable only when ROBOTS_POLICY is RESPECT_DISALLOW; under a different policy this terminal cannot occur, which is one reason the policy is architectural
- **POLICY_SKIPPED** — any other pre-run policy refusal, with its rule named on the record
- **RUN_ABORTED_BEFORE_ATTEMPT** — the operator aborted; §41 requires the item to take this state rather than vanish
- **DESTINATION_SAFETY_REJECTED** — the target resolved to an address class the network safety contract refuses, so no connection was opened
- **DNS_FAILURE** — resolution was attempted and returned no usable answer
- **DNS_TIMEOUT** — resolution was attempted and did not answer within the bound
- **CONNECT_FAILURE** — a connection to a validated address was attempted and refused or failed
- **CONNECT_TIMEOUT** — a connection was attempted and did not establish within the bound
- **TLS_FAILURE** — kept separate from CONNECT_FAILURE because a TLS refusal is a different fact about the target from an unreachable port, and a later construct may treat them differently
- **READ_TIMEOUT** — the connection established and no complete response arrived within the bound
- **HTTP_PROTOCOL_FAILURE** — bytes arrived and did not parse as an HTTP response
- **REDIRECT_POLICY_STOP** — responses WERE received -- the 3xx hops -- and the chain stopped on max hops or a destination the safety contract refuses, so no terminal response exists for the predicate
- **RESPONSE_LIMIT_EXCEEDED** — a response began and exceeded a header, body or total byte cap, so what was captured is known to be incomplete
- **HTTP_RESPONSE_RECEIVED** — a complete response was received within every bound. Whether it is PREDICATE_EVALUABLE is not the apparatus's to say
- **INTERNAL_FETCHER_ERROR** — the apparatus itself failed. Folding this into ATTEMPTED_NO_HTTP_RESPONSE would record 'the target did not answer' when what happened is 'we broke', and those are different facts about different systems

## What the apparatus cannot certify

whether a received response is evaluable depends on what the predicate needs -- a header the capture policy kept, a body the capture policy may not have stored. The apparatus can certify that a complete response arrived and what it captured; it cannot certify evaluability against a predicate that does not exist yet.

Determined by: **THE_CONSTRUCT, over the apparatus's records**.

## Missingness classes

| class | means | counts as attempted |
|---|---|---|
| `NOT_ATTEMPTED_POLICY` | the apparatus decided not to ask | False |
| `NOT_ATTEMPTED_SAFETY` | the apparatus refused to ask, to protect the operator machine | False |
| `ATTEMPTED_NO_CONNECTION` | asked, and nothing was reachable | True |
| `ATTEMPTED_TLS_FAILURE` | asked, reachable, and the secure channel did not establish | True |
| `ATTEMPTED_NO_HTTP_RESPONSE` | asked, connected, and no complete HTTP response arrived | True |
| `HTTP_RESPONSE_NOT_EVALUABLE` | responses arrived and no usable terminal response exists | True |
| `OBSERVATION_AVAILABLE` | a complete response was received within every bound | True |
| `APPARATUS_FAILURE_NOT_A_WORLD_FACT` | our failure, carrying no information about the target | False |

**One class was added beyond the required minimum: `APPARATUS_FAILURE_NOT_A_WORLD_FACT`.** §14 lists a minimum. An internal fetcher error placed in ATTEMPTED_NO_HTTP_RESPONSE would record a fact about the target that never happened, and a denominator built on it would silently absorb our own defects as the world's silence.

## Denominators a later construct can state

| counter | definition | computable by the apparatus |
|---|---|---|
| N_population | the frozen corpus manifest count | True |
| A_attempted | items whose missingness class counts_as_attempted | True |
| R_response_observed | items reaching stage RESPONSE_RECEIVED | True |
| E_predicate_evaluable | items whose captured observation satisfies what the predicate needs | False |
| P_positive | items satisfying the predicate | False |

Which classes enter the denominator: **NOT_CHOSEN_BY_THIS_MISSION**. §14 says a future construct chooses how these states affect its denominator. Choosing here would freeze half a construct while reporting that none was frozen.

## Why this is the whole point

Mission 1.70 closed the external pair because neither Common Crawl nor HTTP Archive documents whether an attempted-and-failed URL appears in what it publishes. An apparatus that stored only responses would reproduce that defect in a system we control, which would be worse: the same opacity, with nobody else to attribute it to.
