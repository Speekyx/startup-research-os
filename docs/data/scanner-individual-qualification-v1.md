# Mission 1.67 — Individual apparatus qualification

Generated from `scanner-individual-qualification-v1.json`, the two candidate
packages and `qualified-apparatus-readiness-v4.json`. Do not edit by hand.

**Primary outcome: `NO_NEW_QUALIFYING_APPARATUS_IDENTIFIED_WITHIN_BOUNDED_SEARCH`**

COMPLETE does not mean QUALIFIED. A well-documented failure is successful
mission output.

## Verdicts

| apparatus | verdict | decisive gate |
|---|---|---|
| Rapid7 Project Sonar | `INDIVIDUALLY_NOT_QUALIFIED` | `A3_PROTOCOL_NATIVE_OBSERVATION_EXPOSURE` |
| Shodan | `INDIVIDUALLY_NOT_QUALIFIED` | `A2_OBSERVATION_ADDRESSABLE_EXPOSURE` |

In one line each:

- **Rapid7 Project Sonar** — The apparatus states its TCP studies include SSH; the only retrievable dataset covering arbitrary TCP ports carries SYN responses and no response bytes.
- **Shodan** — The database is documented as updated in real time, the filter reference documents no time or date filter, and the only historical surface is a bounded per-address lookup — so a window cannot be chosen in the request.

## Blocker distribution

| dimension | candidates |
|---|---|
| observation addressability | 1 |
| protocol native exposure | 1 |
| retrievable frame | 0 |
| configuration time addressability | 0 |
| configuration heterogeneity | 0 |
| lineage | 0 |
| documentation retrievability | 4 |

The four documentation counts are prescreen hits that never became serious candidates. They are a fact about this mission's reach rather than a finding about those apparatuses, in the shape Mission 1.60 recorded — so they are reported apart from the two established epistemic blockers rather than added to them.

## Packages

### Rapid7 Project Sonar

**INDIVIDUALLY_NOT_QUALIFIED** — decisive gate `A3_PROTOCOL_NATIVE_OBSERVATION_EXPOSURE`.

| gate | status |
|---|---|
| `A1_ACTIVE_MEASUREMENT_PRODUCER` | PASS |
| `A2_OBSERVATION_ADDRESSABLE_EXPOSURE` | PARTIAL |
| `A3_PROTOCOL_NATIVE_OBSERVATION_EXPOSURE` | FAIL |
| `A4_OBSERVATION_TIME_DOCUMENTED` | PARTIAL |
| `A5_FRAME_DOCUMENTED` | PARTIAL |
| `A6_NON_VALUE_DOCUMENTATION_AVAILABLE` | PASS |
| `A7_AFFIRMATIVE_MEASUREMENT_LINEAGE` | PARTIAL |
| `A8_RELIABILITY_REVIEWABLE` | NOT_EVALUATED_AFTER_DECISIVE_FAIL |
| `A9_PRODUCT_RELEVANT` | PASS |
| `configuration_membership_tcp_22` | UNKNOWN |
| `configuration_time_addressability` | NOT_EVALUATED_AFTER_DECISIVE_FAIL |
| `configuration_frame_uniformity` | NOT_EVALUATED_AFTER_DECISIVE_FAIL |
| `sampling` | PARTIAL |
| `vantage` | NOT_EVALUATED_AFTER_DECISIVE_FAIL |
| `retention` | UNKNOWN |
| `access` | SPECIAL_ACCESS |

**Repeated-service discriminator.** Service S at address A:port P is observed
during W and again after W. Can an acquisition restricted to W still recover the
observation from W? — `OBSERVATION_EVENT_APPEND`

Each study run publishes its own separately named, separately addressed file, so a later run produces a new artifact rather than mutating an earlier one.

**What its own documents say.**

*A1_ACTIVE_MEASUREMENT_PRODUCER* — PASS

> Project Sonar is a security research project by Rapid7 that conducts internet-wide surveys across different services and protocols
>
> Project Sonar gathers data in two stages: In the first stage, all public IPv4 addresses (about 3.6 billion of them, excluding those opted-out) are scanned
>

Reading: An affirmative statement that the apparatus itself probes Internet targets, not an 'our database contains Internet services' formulation. §12 satisfied.

*A2_OBSERVATION_ADDRESSABLE_EXPOSURE* — PARTIAL

> 2018-06-15-1529049662-fdns_aaaa.json.gz
>
> https://us.api.insight.rapid7.com/opendata/studies/{study_id}/{filename}/
>

Reading: The ADDRESSING MECHANISM is the right shape and is the strongest seen anywhere in this arc: a study publishes individually named, individually addressed files carrying a date and a Unix timestamp, listed per study in sonarfile_set, so an artifact is selected BEFORE any measurement value is retrieved. That is §13's own PASS example, an immutable dated scan snapshot. What is missing is the SEMANTICS: no retrieved first-party sentence defines what the date and the timestamp in a filename denote — study start, study completion, or publication — and a window W can only be mapped onto an artifact whose date is defined. PARTIAL rather than PASS, and PARTIAL rather than FAIL, because the structure is present and the definition is absent.

*A3_PROTOCOL_NATIVE_OBSERVATION_EXPOSURE* — FAIL

> SYN scan results for common TCP services across all of IPv4
>
> Project Sonar runs numerous TCP studies every month. The output from these is a GZIP compressed CSV that contains the IP addresses that responded positively to the SYN for the port in question.
>
> Sonar scans a growing number of TCP and UDP services. TCP studies include SSH, SMB, Telnet, RDP, Mongo, Redis, CouchDB, and more.
>

Reading: The apparatus states that its TCP studies include SSH. The one retrievable dataset covering arbitrary TCP ports carries SYN responses only — which addresses answered on a port, and not one byte the peer sent. The frozen construct requires an identification string beginning with the literal prefix SSH- before negotiation, and a SYN response cannot carry it. The datasets that DO carry response content are HTTP, HTTPS and the two certificate sets, and §16 forbids transferring their raw-response semantics to a TCP/22 resource.

*A4_OBSERVATION_TIME_DOCUMENTED* — PARTIAL

> name
>
> fingerprint
>
> size
>
> updated_at
>

Reading: The file-information response carries updated_at, which is a property of the FILE and not of an observation. No retrieved document defines observation timestamp semantics for a TCP study record — and the TCP record is a CSV of addresses, which carries no per-observation timestamp at all.

### Shodan

**INDIVIDUALLY_NOT_QUALIFIED** — decisive gate `A2_OBSERVATION_ADDRESSABLE_EXPOSURE`.

| gate | status |
|---|---|
| `A1_ACTIVE_MEASUREMENT_PRODUCER` | PASS |
| `A2_OBSERVATION_ADDRESSABLE_EXPOSURE` | FAIL |
| `A3_PROTOCOL_NATIVE_OBSERVATION_EXPOSURE` | NOT_EVALUATED_AFTER_DECISIVE_FAIL |
| `A4_OBSERVATION_TIME_DOCUMENTED` | NOT_EVALUATED_AFTER_DECISIVE_FAIL |
| `A5_FRAME_DOCUMENTED` | PARTIAL |
| `A6_NON_VALUE_DOCUMENTATION_AVAILABLE` | PASS |
| `A7_AFFIRMATIVE_MEASUREMENT_LINEAGE` | NOT_EVALUATED_AFTER_DECISIVE_FAIL |
| `A8_RELIABILITY_REVIEWABLE` | NOT_EVALUATED_AFTER_DECISIVE_FAIL |
| `A9_PRODUCT_RELEVANT` | PASS |
| `configuration_membership_tcp_22` | UNKNOWN |
| `configuration_time_addressability` | NOT_EVALUATED_AFTER_DECISIVE_FAIL |
| `configuration_frame_uniformity` | HETEROGENEITY_OBSERVED |
| `sampling` | PARTIAL |
| `vantage` | NOT_EVALUATED_AFTER_DECISIVE_FAIL |
| `retention` | PARTIAL |
| `access` | ACCOUNT_REQUIRED |

**Repeated-service discriminator.** Service S at address A:port P is observed
during W and again after W. Can an acquisition restricted to W still recover the
observation from W? — `MAINTAINED_SERVICE_STATE`

The search surface documents no window restriction and the database is documented as updated in real time; the 90-day banner history is reachable only once an address is already known.

**What its own documents say.**

*A1_ACTIVE_MEASUREMENT_PRODUCER* — PASS

> the crawlers work 24/7 and update the database in real-time.
>
> Generate a random IPv4 address
>
> Generate a random port to test from the list of ports that Shodan understands
>
> the crawlers don't scan incremental network ranges. The crawling is performed completely random to ensure a uniform coverage of the Internet.
>
> The algorithm is designed to randomly crawl the Internet once a week.
>

Reading: Own crawler infrastructure and an explicit target-selection algorithm. §12 satisfied.

## Pair readiness

Total apparatuses **6**, qualified **0**, minimum required **2**.

**PAIR_ANALYSIS_NOT_READY**

| apparatus | verdict | blocking | new |
|---|---|---|---|
| Netlas | `INDIVIDUALLY_NOT_QUALIFIED` | A8 | no |
| ONYPHE | `INDIVIDUALLY_UNRESOLVED` | B2, B4 | no |
| LeakIX | `INDIVIDUALLY_NOT_QUALIFIED` | B2 | no |
| The Shadowserver Foundation | `INDIVIDUALLY_NOT_QUALIFIED` | B4 | no |
| Rapid7 Project Sonar | `INDIVIDUALLY_NOT_QUALIFIED` | A3 | yes |
| Shodan | `INDIVIDUALLY_NOT_QUALIFIED` | A2 | yes |

## Where the arc stands

**Target.** two apparatuses whose independent measurements can reach one Claim, so the aggregator stops being algebraically identical to the B-2 pass-through baseline

**Distance.** two qualified apparatuses short of two

**What this mission added.** Two complete packages for apparatuses nobody in this arc had evaluated, failing at two different gates — and, for the first time, an apparatus whose TEMPORAL OBJECT is right. Project Sonar publishes dated, immutable, individually addressed per-study artifacts, which is what Missions 1.59, 1.62 and 1.66.2 all failed to find. It fails on the other half of the conjunction.

**The shape that recurred.** Both halves of the requirement have now been seen separately and never together: apparatuses with raw protocol capture publish a maintained current state, and the apparatus with immutable dated snapshots publishes no raw capture for this protocol.

## Nothing moved

| | |
|---|---|
| MEASUREMENT_API_EXECUTIONS | 0 |
| COUNT_ENDPOINT_EXECUTIONS | 0 |
| HOSTS_FETCHED | 0 |
| BANNERS_FETCHED | 0 |
| TRIALS | 0 |
| PURCHASES | 0 |
| CREDENTIAL_READS | 0 |
| MAILBOX_SEARCHES | 0 |
| ENQUIRIES_SENT | 0 |
| SOURCES_REGISTERED | 0 |
| RELIABILITY_VALUES_ASSIGNED | 0 |
| MODEL_CALLS | 0 |
| EMBEDDINGS | 0 |
| PAIRS_SELECTED | 0 |
