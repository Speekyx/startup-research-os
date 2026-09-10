# Operator decision on TED-EGRESS-OPPSYNTH-V1

Generated from `ted-egress-operator-decision-v1.json`. Do not edit by hand.

**PERMIT_WITH_EXACT_CONDITIONS**, by thibchm (NAMED_LOCAL_OPERATOR), on 2026-09-10.

Mission 1.83.1. The operator's decision on TED-EGRESS-OPPSYNTH-V1, recorded BESIDE the frozen packet and never inside it. Marking a frozen document approved changes the bytes that were approved, so the packet is byte-identical and its own approval_recorded still reads false, which means THIS DOCUMENT RECORDS NO APPROVAL and never that none exists.

## The packet this names

- id `TED-EGRESS-OPPSYNTH-V1`, version 1
- digest stated `f27c34460f413def15c260e72fd2261a1fba666b574e9e2ee60bf7ef38a39577`
- digest recomputed `f27c34460f413def15c260e72fd2261a1fba666b574e9e2ee60bf7ef38a39577`
- they agree: **true**

the stated and the recomputed digest are both kept, and the gate refuses them disagreeing. Copying the operator's quoted hash would have made the approval name whatever the message said rather than whatever the packet is; recomputing turns a quoted string into a check that could have failed.

## Scope

- `source_id` = ted-eu
- `use_profile_id` = local-private-research-v1
- `activity` = external_model_transmission
- `processing_purpose` = bounded external inference for Opportunity hypothesis synthesis
- `subject` = ted-eu:CPV-class:9261
- `representation_schema` = opportunity-transmission-representation@1.0.0
- `representation_sha256` = 2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72

## What it does not authorise

- model training
- fine-tuning
- embeddings
- public redistribution
- resale
- customer-facing TED source-data access
- another TED packet
- another processing purpose
- commercial-multi-tenant-research-v1
- transmission to a provider whose current reviewed posture is not APPROVED

## The acceptance, verbatim

recorded verbatim as the operator wrote it. Nothing was reworded, tidied, completed or improved: the words accepted must be exactly the words reviewed.

```
I approve:

DECISION_PACKET_ID = TED-EGRESS-OPPSYNTH-V1
DECISION_PACKET_VERSION = 1
DECISION_PACKET_SHA256 = f27c34460f413def15c260e72fd2261a1fba666b574e9e2ee60bf7ef38a39577

DECISION = PERMIT_WITH_EXACT_CONDITIONS

I adopt all eight conditions frozen in the decision packet.

I accept the residual database-right / onward-transmission risk for the exact
bounded external-model inference described by this packet.

This approval is limited strictly to:

source = ted-eu
use_profile = local-private-research-v1
activity = external_model_transmission
purpose = bounded external inference for Opportunity hypothesis synthesis
subject = ted-eu:CPV-class:9261
representation = opportunity-transmission-representation@1.0.0
representation_sha256 =
2528a56a4a9e873bfd04662aeb52916eb80faafe10ab085e716cbdcee77c5b72

It does NOT authorize:

- model training
- fine-tuning
- embeddings
- public redistribution
- resale
- customer-facing TED source-data access
- another TED packet
- another processing purpose
- commercial-multi-tenant-research-v1
- transmission to a provider whose current reviewed posture is not APPROVED
```

Digest `ea589bba5f8be85e1052f205a4b94301c1d0cef9f8ccc93c747015ce820a6908`.

**Spent.** this approval authorises ONE review successor for ONE scope. A second packet, a second subject, a second purpose or a changed representation needs its own decision, and the digest is what makes that arithmetic rather than a rule somebody must remember.
