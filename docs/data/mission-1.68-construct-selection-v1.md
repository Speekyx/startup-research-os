# Mission 1.68 — Product-relevant measurement construct selection

Generated from `construct-selection-decision-v1.json`,
`product-relevant-construct-comparison-v1.json` and the five construct packages.
Do not edit by hand.

**Primary outcome: `NO_PRODUCT_RELEVANT_CONSTRUCT_WITH_TWO_ROUTES_IDENTIFIED`**

**Selected construct: NONE.** Every candidate failed hard condition 3. Each has exactly one plausible apparatus route, and §44 permits selection only at two or more. §30 forbids selecting the least bad to make progress, and C1 — the closest — would have been exactly that choice.

## Comparison

| construct | relevance | population | routes | verdict |
|---|---|---|---|---|
| `C0_SSH_IDENTIFICATION` | MODERATE | IP_ADDRESS | 1 (Netlas) | NOT_STRUCTURALLY_VIABLE |
| `C1_TCP22_SYN_RESPONSIVENESS` | MODERATE | IP_ADDRESS | 1 (Rapid7 Project Sonar) | NOT_STRUCTURALLY_VIABLE |
| `C2_HTTP_RESPONSE_TO_IP_ADDRESSED_GET` | MODERATE | IP_ADDRESS | 1 (Rapid7 Project Sonar) | NOT_STRUCTURALLY_VIABLE |
| `C3_TLS_CERTIFICATE_OBSERVATION` | WEAK | IP_ADDRESS | 1 (Rapid7 Project Sonar) | NOT_STRUCTURALLY_VIABLE |
| `C4_DNS_RECORD_CONFIGURATION` | WEAK | DOMAIN_NAME | 1 (Rapid7 Project Sonar) | NOT_STRUCTURALLY_VIABLE |

## The pattern across rows

**Every construct has exactly ONE plausible route, and it is a DIFFERENT apparatus each time.**

| construct | its one route |
|---|---|
| `C0_SSH_IDENTIFICATION` | Netlas |
| `C1_TCP22_SYN_RESPONSIVENESS` | Rapid7 Project Sonar (sonar.tcp) |
| `C2_HTTP_RESPONSE_TO_IP_ADDRESSED_GET` | Rapid7 Project Sonar (HTTP study) |
| `C3_TLS_CERTIFICATE_OBSERVATION` | Rapid7 Project Sonar (certificate studies) |
| `C4_DNS_RECORD_CONFIGURATION` | Rapid7 Project Sonar (FDNS/RDNS studies) |

The apparatuses are individually capable and pairwise disjoint. They are not failing to measure; they are failing to measure THE SAME THING as each other, on the same population, with the same temporal object.

**Why it happens.** A commercial scanner product sells SERVICES — what is running where — because that is what its customers buy. A service record presupposes a response. The discovery stage, which port answered, is an internal step these products do not publish as a separately addressable artifact. Sonar publishes it because it is a research dataset rather than a search product.

*It is consistent with the evidence gathered and it is not established that no apparatus publishes such a surface. Several cells are UNRESOLVED rather than BLOCKED, and one documented sentence could move them.*

## The propositions, at the observation level

### `C0_SSH_IDENTIFICATION`

**Proposition.** TCP port 22 accepted a connection AND, before protocol negotiation, the peer emitted an identification string beginning with the literal prefix SSH-

- population: public IPv4 address space (`IP_ADDRESS`)
- unit: distinct public IPv4 address
- deduplication: IPv4 address
- window: the time at which the probe that generated the response occurred, selectable before retrieval
- relevance: `MODERATE_PRODUCT_RELEVANCE`

**What it does not establish.**

- not the number of SSH servers on the Internet
- not the number of organisations running SSH
- not adoption, market share or installations
- not that the service is reachable from anywhere else

### `C1_TCP22_SYN_RESPONSIVENESS`

**Proposition.** a TCP SYN sent to port 22 received a positive response

- population: public IPv4 address space (`IP_ADDRESS`)
- unit: distinct public IPv4 address
- deduplication: IPv4 address
- window: the probe time of the scan that produced the response, selectable before retrieval
- relevance: `MODERATE_PRODUCT_RELEVANCE`

**What it does not establish.**

- NOT that an SSH server is running — this is the single most important non-claim, and the construct must never be relabelled by the protocol conventionally assigned to the port
- not that any protocol was spoken at all
- not that a service is installed, deployed or in use
- not a count of hosts, organisations, devices or customers

### `C2_HTTP_RESPONSE_TO_IP_ADDRESSED_GET`

**Proposition.** a request of exactly the form `GET / HTTP/1.1` with the Host header set to the target IP address, sent to TCP port 80, received a syntactically valid HTTP response status line

- population: public IPv4 address space (`IP_ADDRESS`)
- unit: distinct public IPv4 address
- deduplication: IPv4 address
- window: the probe time of the scan that produced the response, selectable before retrieval
- relevance: `MODERATE_PRODUCT_RELEVANCE`

**What it does not establish.**

- not the number of websites — virtual hosting means one address may serve many, and an IP-addressed request reaches only the default one
- not adoption of any web technology
- not a count of companies, users or customers
- not comparable with any hostname-addressed measurement

### `C3_TLS_CERTIFICATE_OBSERVATION`

**Proposition.** a TLS handshake attempt on a fixed port received a certificate

- population: public IPv4 address space (`IP_ADDRESS`)
- unit: distinct public IPv4 address
- deduplication: IPv4 address
- window: probe time, selectable before retrieval
- relevance: `WEAK_PRODUCT_RELEVANCE`

**What it does not establish.**

- not a purchase, a subscription or a customer relationship
- not adoption of a certificate authority's product
- not the number of sites, since one address may present many certificates by SNI
- CT-log presence is not an active measurement and is not a substitute for one

### `C4_DNS_RECORD_CONFIGURATION`

**Proposition.** the name resolved to a record with the stated property

- population: a defined set of domain names (`DOMAIN_NAME`)
- unit: distinct domain name
- deduplication: domain name
- window: resolution time, selectable before retrieval
- relevance: `WEAK_PRODUCT_RELEVANCE`

**What it does not establish.**

- not that the domain's owner is a customer of anyone
- not adoption, spend or market share
- not comparable with any IP-population measurement

## The one that came closest

**`C1_TCP22_SYN_RESPONSIVENESS`.** One well-documented route with dated immutable per-port artifacts, and a second route that is UNRESOLVED rather than BLOCKED on two separate apparatuses.

*What would change it:* A first-party sentence stating whether Netlas or Censys represents a port that accepted a TCP connection and returned no application data. If either does, C1 has two routes.

*Why it was not selected anyway:* Because that sentence was not found, and selecting on the expectation that it exists would preregister an experiment on a route nobody has established.

## Registry

Unchanged at 15. A candidate rule was offered and not added: `A_PUBLISHED_SURFACE_IS_THE_SALEABLE_OBSERVATION_NOT_THE_MEASUREMENT_PIPELINE`.

It is a real and reusable observation, and it is supported here by one apparatus class evaluated in one mission. APPARATUS_CONFIGURATION_MUST_BE_UNIFORM_ACROSS_THE_FRAME was offered by Mission 1.66.2 and adopted only when Mission 1.67 found a second independent instance in a different shape. The same standard applies to this one, and it has one shape so far.

## What held evidence bought

Eleven retrievals answered a seven-apparatus, five-construct matrix. Mission 1.67 spent twenty-four on two apparatuses. The difference is the held records.

## Nothing moved

| | |
|---|---|
| MEASUREMENT_VALUES_RETRIEVED | 0 |
| TARGET_VALUE_EXPOSURES | 0 |
| API_EXECUTIONS | 0 |
| DATASET_DOWNLOADS | 0 |
| TRIALS | 0 |
| CREDENTIAL_READS | 0 |
| MAILBOX_SEARCHES | 0 |
| SOURCES_REGISTERED | 0 |
| THRESHOLDS_REGISTERED | 0 |
| CLAIMS_CREATED | 0 |
| EVIDENCE_CREATED | 0 |
| RELIABILITY_VALUES_ASSIGNED | 0 |
| PAIRS_SELECTED | 0 |
| MODEL_CALLS | 0 |
