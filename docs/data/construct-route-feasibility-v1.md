# Mission 1.68 — Construct reachability matrix

Generated from `construct-route-feasibility-v1.json`. Do not edit by hand.

A cell says whether an apparatus could plausibly witness that construct. A
**plausible route** names an apparatus with a first-party basis and unresolved
questions. It is not a qualified apparatus.

| construct | Censys | Netlas | LeakIX | Shadowserver | ONYPHE | Rapid7 Project Sonar | Shodan |
|---|---|---|---|---|---|---|---|
| `C0_SSH_IDENTIFICATION` | unresolved | **plausible** | temporal | frame | unresolved | predicate | temporal |
| `C1_TCP22_SYN_RESPONSIVENESS` | unresolved | unresolved | temporal | frame | predicate | **plausible** | temporal |
| `C2_HTTP_RESPONSE_TO_IP_ADDRESSED_GET` | unresolved | predicate | temporal | frame | unresolved | **plausible** | temporal |
| `C3_TLS_CERTIFICATE_OBSERVATION` | lineage | unresolved | temporal | frame | unresolved | **plausible** | temporal |
| `C4_DNS_RECORD_CONFIGURATION` | unresolved | unresolved | temporal | frame | unresolved | **plausible** | temporal |

| construct | plausible routes |
|---|---|
| `C0_SSH_IDENTIFICATION` | 1 |
| `C1_TCP22_SYN_RESPONSIVENESS` | 1 |
| `C2_HTTP_RESPONSE_TO_IP_ADDRESSED_GET` | 1 |
| `C3_TLS_CERTIFICATE_OBSERVATION` | 1 |
| `C4_DNS_RECORD_CONFIGURATION` | 1 |

## What survives a change of predicate

### Global blockers, unchanged by any construct

- **Shodan** — temporal architecture: a real-time-updated database with no documented time or date filter and per-address-only history
- **LeakIX** — temporal: indexing, first-detection and last-detection dates, none of which is an observation event
- **Shadowserver** — frame: a requester retrieves only their own networks
- **Censys Platform surface** — temporal: a LAST-observed service timestamp, and history reached only after a host is found

### Construct-specific blockers that correctly disappeared

- **Rapid7 Project Sonar** — Mission 1.67 blocked Sonar on A3 because its arbitrary-TCP resource carries no response bytes. That blocker is construct-specific and does NOT apply to a transport-level predicate, which is the whole point of §3. Sonar becomes the strongest single route in the arc under C1.
- **Netlas_banner_fidelity** — One of Netlas's ten A8 topics ceases to be load-bearing for a predicate that reads no banner. The other nine are global and survive.

### Construct-specific blockers that appeared

- **Netlas_on_web_ports** — Domain-addressed queries, up to 100,000 virtual sites per address, and each redirect hop stored separately are not a problem for a non-web-port construct and are decisive for C2. On every port other than 80 and 443 Netlas sends requests by IP address without domain names.

### Elevated rather than removed

- **vantage** — §16. Moving from a banner predicate to a SYN predicate makes vantage MORE important, not less: a port may respond from one scanner region and not another, and with no application response in the record there is nothing to detect the difference with. Recorded as VANTAGE_COMPATIBILITY_REQUIRED rather than folded into reliability.

## Independence

**INDEPENDENCE_NOT_DISPROVEN.** No construct was rejected on lineage grounds except C3 for Censys, whose certificate collection mixes Certificate Transparency transcription with its own scanning. Sonar, Netlas, Censys and ONYPHE each state that they operate their own scanning infrastructure. Shared TOOLING — several derive from the same family of internet-scanning software — is not shared DATA, and conflating them would be the error in the opposite direction.

*Not established:* That any two of them are independent. That is the next mission's work and no pair was compared here.
