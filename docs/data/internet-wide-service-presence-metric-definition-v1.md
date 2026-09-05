# Internet-Wide Service Presence — Metric Definition V1

**Mission 1.59 — Internet-Wide Service-Presence Route Gate Closure V1 — recorded 2026-09-05. Gate 3.**

> **This document is GENERATED.** Edit the JSON and re-run
> `infrastructure/scripts/render_service_presence_route.py`.

**The problem.** Each scanning vendor ships its own proprietary fingerprint database, so 'hosts running product X' names two different operational classifiers with no published equivalence between them.

**The refusal.** Matching vendor labels is not metric equivalence. Two vendors may both label a host PRODUCT-X while using different signatures, different version rules, different banner fields and different post-processing. A construct resting on that agreement rests on a coincidence of two proprietary opinions.

**And the alternative that was refused.** Choosing one vendor as the semantic authority. That would put a classifier inside the metric definition, which is the FRAME_INSIDE_THE_DEFINITION failure Mission 1.57 named, one layer down: instead of the measurer's reach it is the measurer's taxonomy.

## Fact classification

**PROTOCOL_NATIVE**

- the TCP port a connection was accepted on
- the bytes a server sends unprompted on connection, where a published standard fixes their form
- completion of a standard-defined handshake step

**VENDOR_DERIVED**

- the service or product name a scanner assigns
- the software version a scanner extracts
- product family and category labels
- vulnerability associations attached to a fingerprint

**LATENT_INFERENCE**

- installations
- users
- customers
- adoption
- market share

VENDOR_DERIVED facts may remain witness metadata. They may not enter Claim identity, the metric definition or the meaning of a threshold.

## The construct — `public_ipv4_protocol_responsive_host_count`

> The number of distinct public IPv4 addresses from which, during a defined observation window, a TCP connection to port 22 was accepted and the peer sent an identification string beginning with the literal prefix `SSH-` terminated by CR LF, before any negotiation.

**Protocol basis: RFC 4253, The Secure Shell (SSH) Transport Layer Protocol, section 4.2, Protocol Version Exchange.**

The server sends `SSH-protoversion-softwareversion SP comments CR LF` immediately upon connection and before key exchange begins, and the standard states that other lines a server may send MUST NOT begin with `SSH-`.

The predicate is decided by a literal prefix on the first bytes a server sends, fixed by an IETF standard rather than by any vendor. Two implementations parsing it will agree on what the predicate ASKS even where their coverage differs.

*Falsifier.* A host that accepts the connection and does not send an identification string with that prefix does not count. Both apparatuses would be evaluating that same condition.

Vendor fingerprint required: **False**. Classifier inside the definition: **False**.

## What it means, and what it does not

> The count is evidence about the externally observable presence of a network-accessible service speaking a defined protocol across the defined public IPv4 frame, at a defined time.

It is **not**:

- an installation count, because one host may serve many or none, and hosts not publicly reachable are invisible
- a user count
- a customer count
- a subscription or revenue figure
- demand
- adoption
- market share
- a count of any particular vendor's software, because the protocol is spoken by many implementations

AUDIENCE_OR_USAGE and COMPETITIVE_SUPPLY, and it survives the narrowing because observable service presence across a defined public frame is exactly the kind of externally checkable supply signal those dimensions ask about. It would NOT survive if the construct had to name a product to be interesting.

## Apparatus mapping

**apparatus_a_censys**

- `can_express_port_predicate`: YES
- `can_express_protocol_native_banner_predicate`: NOT_ESTABLISHED
- `detail`: Its documented queryable surface is a merged host state with per-service fields including a service name assigned by Censys. Whether a query can be written that decides the RFC-defined prefix condition on the raw first bytes, rather than trusting the assigned service name, is not established from the documentation retrieved.
- `additional_finding`: Under high service density the documentation states that service data shown represents a SAMPLING of service details. A sampled record is not a census, and a count built on it would not be a count of the defined population.

**apparatus_b_netlas**

- `can_express_port_predicate`: YES
- `can_express_protocol_native_banner_predicate`: LIKELY_NOT_ESTABLISHED
- `detail`: Its response documents capture banners and are queryable by field, which is the right shape for a banner-prefix predicate, but the documentation retrieved does not establish that the raw identification string is exposed as a queryable field independent of its own protocol parsing.

## Gate 3 — `UNKNOWN`

**Blocker.** The CONSTRUCT is definable protocol-natively and needs no vendor fingerprint, which is the reusable half. What is not established is that either apparatus exposes a query surface deciding that predicate rather than its own assigned service label. Section 8 requires that both be evaluating the same predicate; a construct nobody can ask for is not yet a shared predicate.

*Why not FAIL.* Section 9 fails gate 3 when the common meaning REQUIRES a proprietary fingerprint or a union of two classifiers. It does not: the meaning is fixed by an IETF standard. What is missing is evidence about the query surfaces, which is a documentation question rather than a semantic one.

*Why not PASS.* Section 8 requires that both apparatuses would be evaluating the same predicate. That is not shown, and asserting it from the fact that both parse banners would be exactly the inference from plausibility this arc has refused four times.

## What is reusable

**A protocol-native service-presence construct is available for this class. Any pair of active scanners can be asked for it, and it needs no vendor taxonomy.**

Requirement on a future pair: Each apparatus must expose a query surface that decides a standard-defined wire predicate, rather than only its own assigned service name.

The narrowing also REMOVES a shared upstream. A vulnerability-flavoured or version-flavoured construct would have pulled a common CVE database into the load-bearing path on both sides, which would have been a common upstream for the metric's meaning even though the scanning stayed independent. A protocol-prefix predicate depends on no such shared artefact.

