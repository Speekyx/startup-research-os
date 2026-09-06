# Mission 1.73 — The counterpart qualification matrix

Generated from `independent-http-counterpart-qualification-v1.json`.
Do not edit by hand.

**Candidate: Globalping (Volentio JSD (jsDelivr)).**
**Verdict: `COUNTERPART_UNRESOLVED`.**

| dimension | status | mandatory |
|---|---|---|
| `C1_DIRECTABLE_TARGET` | `PASS` | True |
| `C2_OWN_MEASUREMENT_PRODUCTION` | `PASS` | True |
| `C3_TERMINAL_SUBMISSION_ACCOUNTING` | `PASS` | True |
| `C4_TRANSPORT_LEVEL_RESULT_SURFACE` | `PASS` | True |
| `C5_PROSPECTIVE_TEMPORAL_ADDRESSABILITY` | `PASS` | True |
| `C6_REQUEST_CONTRACT_RECONSTRUCTABILITY` | `PARTIAL` | True |
| `C7_VANTAGE_REVIEWABILITY` | `PASS` | True |
| `C8_RESULT_MINIMIZATION` | `PASS` | True |
| `C9_RIGHTS_FEASIBILITY` | `PARTIAL` | True |
| `C10_INDEPENDENCE_PLAUSIBILITY` | `PASS` | True |
| `C11_BOUNDED_PILOT_FEASIBILITY` | `PASS` | True |
| `C12_SAME_HTTP_WORLD_STATE_FAMILY` | `PASS` | True |

**10 PASS, 2 PARTIAL, 0 FAIL, 0 UNKNOWN.** No score.

*§45: a PARTIAL on a mandatory dimension blocks qualification. Two mandatory dimensions are PARTIAL, and they are independent of each other.*

*And why it is not a rejection:* ten of twelve dimensions PASS on first-party evidence, including every one that closed the external routes in Mission 1.70: the population is directable, the producer is independent, missingness is nameable, the result is transport-level, and the temporal object is prospective by construction. Reporting this as a failure would discard what was established.

Why, for each:

- **C1_DIRECTABLE_TARGET** — the operator supplies the target and the request. The spec defines the target as 'A publicly reachable measurement target.' and the request object carries `path`, `query` and an optional `host` override. The provider selects no sample and runs no discovery.
- **C2_OWN_MEASUREMENT_PRODUCTION** — the probe README states the platform 'relies on a globally distributed network of community-hosted probes, allowing anyone to run network testing commands like ping or traceroute from any location', and the probe source dispatches the HTTP request itself through undici. The measurement is not obtained from anybody else.
- **C3_TERMINAL_SUBMISSION_ACCOUNTING** — a measurement returns an `id` and `probesCount` -- 'The actual number of probes that performed the measurement tests' -- and each test carries a status of `in-progress`, `finished`, `failed` or `offline`. `offline` is defined as a test 'where the requested probe was not available to run the test', which is apparatus missingness named by the provider rather than inferred by us.
- **C4_TRANSPORT_LEVEL_RESULT_SURFACE** — the finished HTTP result requires `statusCode`, `statusCodeName`, `headers`, `rawHeaders`, `resolvedAddress` and `timings`. That is a transport-level surface and it does not require reading page content.
- **C5_PROSPECTIVE_TEMPORAL_ADDRESSABILITY** — `createdAt` and `updatedAt` are REQUIRED on the measurement response -- 'The date and time when the measurement was created' and 'when the measurement was last updated'. The measurement is created prospectively by us, so §20's prospective window is satisfied without any historical dataset.
- **C6_REQUEST_CONTRACT_RECONSTRUCTABILITY** — ten fields are documented -- method (HEAD, GET, OPTIONS, default HEAD), host override, path, query, additional headers with Host and User-Agent reserved, protocol, port, resolver, ipVersion and timeout -- and the probe may not be modified, so the contract is fixed and uniform across the frame. What is missing is redirect behaviour.
  - *residual:* the 124,793-byte specification contains ZERO occurrences of the word redirect, and the result schema carries one statusCode and one header set with no hop array. The probe source dispatches through `undici.Client.dispatch()`, which does not follow redirects -- but that is an observed implementation and not a documented contract, and §25 names 'undocumented redirects' as exactly the case where equivalence may not be assumed.
- **C7_VANTAGE_REVIEWABILITY** — locations are selectable by continent, region, country, state, city, ASN, network and tags, and each result carries its probe's location. Classification: MULTIPLE_SELECTABLE_REGIONS.
- **C8_RESULT_MINIMIZATION** — and the mechanism is better than a field filter: with the default `HEAD` method there is no response body to receive, and `rawBody` is documented as 'The raw HTTP response body or `null` if there was no body in response.' Minimization is achieved by choosing the request rather than by trusting the provider to omit a field.
- **C9_RIGHTS_FEASIBILITY** — the Terms of Use were read in full from the provider's own repository. Prohibited Use does NOT prohibit commercial use or automated access, and the commercial restriction that exists sits under the heading 'If you are a consumer user:' with a separate liability clause addressing business users -- so it is not the blanket prohibition it looks like in isolation.
  - *residual:* §2 Permitted Use describes the platform as one that 'allows you to monitor, debug, and benchmark YOUR internet infrastructure', and §3 reserves 'all rights that are not expressly granted'. Measuring a frozen corpus of third-party sites is not our own infrastructure, and a reservation clause makes the absence of an express grant weigh more rather than less.
- **C10_INDEPENDENCE_PLAUSIBILITY** — different operator, different code, different network positions, and no shared HTTP observation upstream: the probes make live requests rather than reading Common Crawl, HTTP Archive or anything SROS produced. §31 applies -- SROS choosing the target does not make the measurement SROS-produced.
- **C11_BOUNDED_PILOT_FEASIBILITY** — the spec states 250 free tests per hour for an unauthenticated user, so the 500-target cap in BOUNDED_HTTP_LOAD_PROFILE_V1 fits inside the profile's own six-hour MAX_RUN_DURATION without credits, an account or a paid plan.
- **C12_SAME_HTTP_WORLD_STATE_FAMILY** — both apparatuses can observe an HTTP response status and named response headers for a defined request against a defined target. Classification: SAME_HTTP_WORLD_STATE_FAMILY_PLAUSIBLE. No exact predicate is chosen.

## The request contract

| field | classification | SROS can construct an equivalent |
|---|---|---|
| `http_method` | CONFIGURABLE | True |
| `url_scheme` | CONFIGURABLE | True |
| `port` | CONFIGURABLE | True |
| `path` | CONFIGURABLE | True |
| `query` | CONFIGURABLE | True |
| `host_header` | CONFIGURABLE | True |
| `sni` | DERIVABLE | False |
| `user_agent` | FIXED_AND_DOCUMENTED | True |
| `accept` | CONFIGURABLE | True |
| `accept_language` | CONFIGURABLE | True |
| `accept_encoding` | CONFIGURABLE | True |
| `cookies` | NOT_APPLICABLE | False |
| `authentication` | NOT_APPLICABLE | True |
| `redirects` | UNKNOWN | False |
| `javascript_execution` | NOT_APPLICABLE | True |
| `cache` | UNKNOWN | False |
| `dns_behaviour` | CONFIGURABLE | True |
| `ip_version` | CONFIGURABLE | True |
| `vantage` | CONFIGURABLE | True |
| `timeout` | CONFIGURABLE | True |
| `retries` | NOT_APPLICABLE | True |

**REQUEST_CONTRACT_COMPATIBILITY_UNRESOLVED**, on one field: `redirects`.

the 124,793-byte specification contains zero occurrences of the word redirect. the probe dispatches through undici.Client.dispatch(), which does not follow redirects — and that is an implementation rather than a contract (False).

*a measurement contract must be frozen and reconstructable by a later reader. An undocumented default can change without notice, and if the counterpart began following redirects while SROS did not, both routes would still report a status and the divergence would be invisible in the data. Mission 1.70 killed the external pair on a redirect semantic that WAS documented; this one is not.*

## Minimization

**TRANSPORT_ONLY_RESULT_PATH_AVAILABLE.** the default method is HEAD, and a HEAD response has no body to return. The result field is documented as 'The raw HTTP response body or `null` if there was no body in response.' So the minimization is achieved by the REQUEST rather than by asking the provider to omit a field.

## Rights

**DEDICATED_GOVERNANCE_REVIEW_REQUIRED.** Access: `PUBLIC_NO_ACCOUNT`.

The clause that looks decisive in isolation sits under *"If you are a consumer user:"*, and reading it as a blanket prohibition is refused: **False**.

What does bite: measuring a frozen corpus of third-party websites is not monitoring OUR infrastructure, and §3 reserves 'all rights that are not expressly granted to you under these Terms'. A reservation clause makes the absence of an express grant weigh more rather than less. It is a prohibition: **False**. It is a grant: **False**.
