# Mission 1.73 — An independent HTTP counterpart, two questions short

Generated from `quantity-class-selection-decision-v3.json` and the qualification
records. Do not edit by hand.

**Primary outcome: `COUNTERPART_FOUND_REQUEST_CONTRACT_UNRESOLVED`**

**Selected counterpart: NONE. Selected quantity class: NONE.**

## Candidates

| candidate | operator | status |
|---|---|---|
| Globalping | Volentio JSD (jsDelivr) | `SERIOUS` |
| urlscan.io | urlscan GmbH | `PRE_GATE_FAILED` |
| RIPE Atlas | RIPE NCC | `PRE_GATE_FAILED` |

3 discovered, 1 serious of a cap of 5, 0 qualified. 26 of 30 documentation requests, 11 of which returned nothing usable and are counted.

## Who produces the observation

**`PROVIDER_OPERATED_OPEN_SOURCE_ENGINE`.** the provider authors the probe software and coordinates the network; the hardware and the network position are community-hosted. The measurement is performed by the provider's unmodified code at a volunteer's location, which is neither the provider's own datacentre nor customer-executed code.

- reseller or pass-through: **False**
- a proxy for an SROS request: **False**
- shares an observation upstream with SROS: **False**
- SROS initiates the job: **True**, and that makes the measurement SROS-produced: **False**

## The two residuals

| id | dimension | residual |
|---|---|---|
| R1 | C6_REQUEST_CONTRACT_RECONSTRUCTABILITY | redirect behaviour is absent from the specification |
| R2 | C9_RIGHTS_FEASIBILITY | Permitted Use is scoped to 'your internet infrastructure' and rights not expressly granted are reserved |

Neither requires a new search: one documented sentence from the provider, or one question through the enquiry channel this project has used before, a dedicated governance review, or a provider statement.

## Why this outcome and not the others

outcome D names request semantics as the blocker, and there are TWO independent unresolved mandatory gates: the request contract and the rights scope. Reporting D alone would let a reader conclude that one documented sentence about redirects unlocks the route, which is not true. Both residuals are named in the record and in the secondary outcomes, and Mission 1.74 must close both.

| outcome | refused because |
|---|---|
| A_INDEPENDENT_HTTP_COUNTERPART_QUALIFIED | two mandatory dimensions are PARTIAL, and §45 makes that block qualification |
| B_QUALIFIED_Q1_SELECTED | §48's conditions are conjunctive and one is unmet, so selecting Q1 would preregister an experiment on a route nobody has qualified -- the same refusal Mission 1.69 made when it declined to select on an expected answer |
| C_EPISTEMICALLY_QUALIFIED_ACCESS_REVIEW_REQUIRED | C claims the epistemic requirements all pass and only access or terms remain. The request contract is an EPISTEMIC gate and it is unresolved, so C would overstate what was established |
| F_RESULT_SURFACE_INCOMPATIBLE | a transport-only result path was established under HEAD |
| G_LINEAGE_UNRESOLVED | the producer was established on the provider's own README and source |
| H_COMMERCIAL_PURPOSE_GAP | H requires an OTHERWISE VIABLE route blocked by the intended use. This route is not otherwise viable, because the request contract is also open -- and the terms do not clearly block the use either, they fail to grant it |
| I_NO_COMPATIBLE_COUNTERPART_IDENTIFIED | it would understate badly. An independent, directable, transport-level producer with legible missingness and prospective temporal semantics WAS identified, and reporting I would send the next mission searching for something it already holds -- the mistake Mission 1.69 refused when it declined outcome H |

## Q1

| condition | met |
|---|---|
| sros governance track ready | True |
| one external counterpart qualified | False |
| independent production plausible | True |
| common http world state family exists | True |

**NOT_YET_STRATEGICALLY_VIABLE**, failing on `one_external_counterpart_qualified`. Q1 stays `PROMISING_BUT_ROUTE_QUALIFICATION_REQUIRED`.

**Resolved this mission:**

- an operator-directable external HTTP producer exists and was identified on first-party evidence, which no earlier mission in this arc had found
- its measurement lineage is established: community-hosted probes running the provider's unmodified code, with no third-party measurement upstream
- a transport-only result path exists, achieved by choosing HEAD rather than by trusting a provider filter
- prospective temporal addressability is satisfied by construction, which dissolves the historical-snapshot problem that decided Missions 1.59, 1.62 and 1.70
- per-result job statuses distinguish apparatus failure from target observation, with the provider naming `offline` itself
- a bounded 500-target pilot fits inside the free unauthenticated rate
- the terms were read in full, and the commercial clause that looks decisive in isolation is scoped to consumer users

**Still unresolved:**

- redirect behaviour is absent from the counterpart's specification, so the request contract cannot be frozen as equivalent
- Permitted Use is scoped to the user's own infrastructure and rights not expressly granted are reserved
- no second candidate reached a complete package, so nothing corroborates the shape of this one

## Nothing moved

| | |
|---|---|
| COUNTERPART_API_EXECUTIONS | 0 |
| TARGET_HTTP_REQUESTS | 0 |
| SROS_FETCHER_RUNS | 0 |
| EXTERNAL_MEASUREMENT_JOBS | 0 |
| TARGET_VALUE_EXPOSURES | 0 |
| ACCOUNTS_CREATED | 0 |
| TRIALS | 0 |
| CREDENTIAL_READS | 0 |
| SOURCES_REGISTERED | 0 |
| CLAIMS_CREATED | 0 |
| EVIDENCE_CREATED | 0 |
| INDEPENDENCE_GROUPS_CREATED | 0 |
| MODEL_CALLS | 0 |
