# Mission 1.72 — Public HTTP observation governance

Generated from `public-http-observation-governance-decision-v1.json` and the policy
records. Do not edit by hand.

**GOV-1: `PUBLIC_HTTP_OBSERVATION_TRACK_ADOPTED`**, conditionally (True), under ADR-039.

## The condition, which is what makes it defensible

the track is available only while the retained material is transport-level. The moment response bodies or a publisher's expressive content are retained, the retained thing IS the publisher's material and SOURCE_COLLECTION_GOVERNANCE applies instead.

Satisfied by GOV-3: **True** (`BODY_PERSISTENCE_DEFAULT_DISABLED`). The track would not have been adoptable at all.

## Is the distinction real, or a smaller name for the same act?

| question | answer |
|---|---|
| if the page's content were entirely different and the transport outcome identical, would the observation change? | **no** |
| if the transport outcome differed and the page content were identical, would it change? | **yes** |

the observation is a function of the transport interaction rather than of the publisher's expressive content, so what is appropriated differs. That is a difference in kind and not in degree.

## Models evaluated

| model | adopted |
|---|---|
| MODEL_A_SOURCE_COLLECTION_ONLY | False |
| MODEL_B_PUBLIC_HTTP_OBSERVATION_TRACK | True |
| MODEL_C_PER_TARGET_OPERATOR_REVIEW | False |
| MODEL_D_NO_GOVERNED_ROUTE | False |

Why, for each:

- **MODEL_A_SOURCE_COLLECTION_ONLY** — it is not merely laborious, it is structurally unavailable. source-registry-v1.md §1 rule 8 requires a GRANT for six named activities on retrieved authoritative evidence, and for a target that has never published terms addressing automated access there is no document to retrieve. Every activity reads NOT_ADDRESSED and rule 2 forbids a path from 'we could not check' to 'we may proceed'. The corpus collapses to the 29 registered sources, which is Mission 1.71's finding.
- **MODEL_B_PUBLIC_HTTP_OBSERVATION_TRACK** — the two activities differ in WHAT IS APPROPRIATED, and the difference is testable rather than verbal. See distinguishing_test.
- **MODEL_C_PER_TARGET_OPERATOR_REVIEW** — it is not wrong, it is at the wrong layer. For a target publishing no terms the operator would be reviewing nothing, which reproduces Model A's evidentiary problem in a form that LOOKS like review while having no basis -- worse than Model A, because it manufactures the appearance of a judgement. The part of it that is real -- is this target public, safe, known to be excluded -- is mechanical, and it survives as GOV-4's preflight.
- **MODEL_D_NO_GOVERNED_ROUTE** — it would be the honest answer if the two activities could not be distinguished. They can be, on the repository's own material, so leaving it undecided would repeat the move Mission 1.71 refused: treating an absence of a decision as though it were a decision.

## Precedence

the track is determined by the DECLARED RETENTION PROFILE, not by the caller's stated intent. If the profile retains a response body, publisher expressive content, or any material whose value to us is what the publisher wrote, SOURCE_COLLECTION_GOVERNANCE_APPLIES.

Caller may choose its track: **False**. When both could apply: **SOURCE_COLLECTION wins**.

*How it is enforced:* the retention policy's persisted classes are an allowlist that contains no body class, so a body-retaining configuration is not expressible in the observation track's own contract rather than being forbidden by a note beside it

The observation track may not be used for:

- article ingestion
- document corpus acquisition
- page-content research
- web scraping for ideation
- news ingestion
- forum ingestion
- dataset ingestion
- commercial content harvesting
- general-purpose site crawling

## The five decisions

| | decision | resolved by |
|---|---|---|
| GOV-1 | `PUBLIC_HTTP_OBSERVATION_TRACK_ADOPTED` | ADR-039 and public-http-observation-governance-decision-v1.json |
| GOV-2 | `R1_RESPECT_DISALLOW` | public-http-robots-policy-v1.json |
| GOV-3 | `D2_ALLOWLISTED_HEADERS_AND_STATUS with BODY_PERSISTENCE_DEFAULT DISABLED` | public-http-data-minimization-policy-v1.json and public-http-retention-policy-v1.json |
| GOV-4 | `PREFLIGHT_CLASSIFICATION_WITH_A_FROZEN_EXCLUSION_REGISTRY` | public-http-target-policy-v1.json and its exclusion registry contract |
| GOV-5 | `BOUNDED_HTTP_LOAD_PROFILE_V1, every value a project policy default` | bounded-http-load-profile-v1.json |

## Robots, condition by condition

| condition | outcome | stricter than RFC 9309 |
|---|---|---|
| `ROBOTS_2XX_PARSEABLE` | `EVALUATE_RULES` | False |
| `ROBOTS_3XX_WITHIN_LIMIT` | `FOLLOW_AND_EVALUATE` | False |
| `ROBOTS_3XX_BEYOND_LIMIT` | `TARGET_EXCLUDED` | True |
| `ROBOTS_404_OR_410` | `TARGET_PROCEEDS` | False |
| `ROBOTS_OTHER_4XX` | `TARGET_PROCEEDS` | False |
| `ROBOTS_401_OR_403` | `TARGET_EXCLUDED` | True |
| `ROBOTS_5XX` | `TARGET_EXCLUDED` | False |
| `ROBOTS_NETWORK_FAILURE` | `TARGET_EXCLUDED` | False |
| `ROBOTS_TIMEOUT` | `TARGET_EXCLUDED` | True |
| `ROBOTS_UNPARSEABLE_LINES` | `EVALUATE_PARSEABLE_RULES` | False |
| `ROBOTS_OVER_PARSE_LIMIT` | `EVALUATE_FIRST_500_KIB` | False |
| `ROBOTS_DISALLOWED_FOR_OUR_TOKEN` | `TARGET_EXCLUDED` | False |
| `ROBOTS_ALLOWED_FOR_OUR_TOKEN` | `TARGET_PROCEEDS` | False |

Standard read rather than recalled: **True** (https://www.rfc-editor.org/rfc/rfc9309.html).

## What is retained

| data class | capture | persist | retention |
|---|---|---|---|
| TRANSPORT_METADATA | True | True | RUN_SCOPED |
| REQUEST_METADATA | True | True | RUN_SCOPED |
| RESPONSE_STATUS | True | True | RUN_SCOPED |
| RESPONSE_HEADERS | True | ALLOWLIST_ONLY | RUN_SCOPED |
| RESPONSE_BODY | True | False | NOT_PERSISTED |
| REDIRECT_METADATA | True | MINIMIZED | RUN_SCOPED |
| DNS_METADATA | True | True | RUN_SCOPED |
| TIMING_METADATA | True | True | RUN_SCOPED |
| POLICY_METADATA | True | True | RUN_SCOPED |

Body persistence: **DISABLED**, and not persisting is the same as not receiving: **False**.

## Targets

| class | proceeds |
|---|---|
| `ELIGIBLE_PUBLIC_TARGET` | True |
| `POLICY_EXCLUDED` | False |
| `ROBOTS_EXCLUDED` | False |
| `KNOWN_OPT_OUT` | False |
| `AUTH_REQUIRED` | False |
| `DESTINATION_SAFETY_BLOCKED` | False |
| `UNSUPPORTED_SCHEME` | False |
| `OPERATOR_EXCLUDED` | False |
| `KNOWN_AUTOMATION_RESTRICTION` | False |
| `UNKNOWN_POLICY_CONDITION` | False |

Unknown terms: **TARGET_TERMS_NOT_INDIVIDUALLY_REVIEWED**. that this target's terms were not individually read. It asserts nothing about what they say in either direction.

An excluded target is removed from the corpus: **False**. the corpus records the population INTENT and the preflight records the governance decisions taken over it. Deleting excluded targets would merge two different facts and would shrink N, which is exactly the defect that closed the external routes in Mission 1.70.

## Nothing is authorized

- run authorization required: **True**
- granted by this mission: **False**
- fetcher implemented: **False**
- second independent route still required: **True**
- external legal conclusion: **NO_EXTERNAL_LEGAL_CONCLUSION**
