# Mission 1.74.5 — The second approval, and the first one stays spent

Generated from `globalping-r2-v2-dispatch-approval-v1.json`. Do not edit by hand.

**Execution status: `SENT`**, recorded by Mission 1.74.6. The approval above was recorded by Mission 1.74.5; approving and performing are separate acts and this page carries both.

## What was approved

| | |
|---|---|
| enquiry | `GP-R2-Q1` v2 |
| mechanism | `OPERATOR_MANUAL_EMAIL` |
| recipient | `d@globalping.io` |
| channel | `PROVIDER_PUBLISHED_GENERAL_CONTACT_CHANNEL` |
| subject | Terms scope: HEAD measurements of publicly reachable third-party websites |
| sender | `PLACEHOLDER_PERMITTED_FOR_MANUAL_SEND_ONLY` |
| maximum sends | **1** |
| approved content hash | `987f3ff57ce661c6…` |
| approval hash | `41590d55b9626fce…` |

## The quoted digest was recomputed, not copied

the operator's message carries a digest, and copying it would make the approval name whatever the instruction said rather than whatever the packet is. Recomputing turns a quoted string into a check: if the two had disagreed the approval would have been refused rather than recorded.

Stated `987f3ff57ce661c6…`, recomputed `987f3ff57ce661c6…`, and the gate refuses them disagreeing.

## The sender stays open, at the operator's instruction

the operator stated the sending mailbox is chosen at execution time, which is the same property Mission 1.65 recorded in advance for a manual mail send: the sender is not determined until the send. The cost is unchanged -- this approval pins the action apart from the mailbox it leaves from.

## A second approval, not a renewal

| | first | second |
|---|---|---|
| recipient | `legal@globalping.io` | `d@globalping.io` |
| execution | `DISPATCH_ATTEMPTED_DELIVERY_FAILED` | `SENT` |
| provider contacted | False | False |
| approval hash | `90fd201d9d1abd06…` | `41590d55b9626fce…` |

the recipient differs, and the recipient is a bound field, so this authorises a different action rather than extending a spent one. The two approvals name different content digests and neither can stand in for the other.

The earlier approval was reused: **False**. Its attempt reinterpreted as delivered: **False**.

## The ceiling belongs to the medium

still a manual mail send, so still Mission 1.66's ceiling: the send happens in a mail client nothing in this repository can observe. The channel changed from the designated address to the published one and the OBSERVABILITY did not, because the ceiling is a property of the medium rather than of the address.

Reachable: `OPERATOR_ATTESTED`. Upgrade path: NONE for this channel. A future mission may record OPERATOR_ATTESTED and nothing above it.

## What was performed

| | |
|---|---|
| send attempts | 1 |
| sends made | 1 |
| deliveries confirmed | 0 |
| provider contacted | False |
| provider replied | False |
| emails sent by this repository | 0 |
| mail connector used | False |
| mailbox searched | False |
| operator attestation | True |
| attestation level | OPERATOR_ATTESTED |

## A send is not a delivery

| | |
|---|---|
| sent at | `2026-09-06T19:39:00+04:00` |
| sender | `thib.chm@gmail.com` |
| recipient | `d@globalping.io` |
| body used, per the attestation | `THE_FROZEN_PACKET_BODY` |
| body compared by this repository | False |
| message id | None |
| **delivery** | **`UNCONFIRMED`** |
| delivery established by | None |

the attestation states that a message was sent and says nothing about whether it arrived. The operator instructed that the strongest justified state be recorded and that successful delivery not be inferred -- and this arc has already shown the difference, because the v1 message to legal@globalping.io was also sent before it bounced.

**a contact means something reached the provider, and only delivery would establish that. The dispatch is attested and the delivery is not, so marking a contact here would put an event in the record that nobody observed.**

The attestation covers that a message was sent, that it was sent exactly once, the sending mailbox, the recipient, the subject, the stated send time, that the frozen body was used. It does not cover delivery, receipt by a person, the bytes that actually left the mail client, a reply.

### The sender is attested, not checked

the approval deliberately left the sender unbound, so no field of it constrains the mailbox and no artifact here records one. The mailbox is known because the operator said so, and that is the whole of the evidence for it. Mission 1.74.5 stated that cost in advance; this is the record of paying it.

Written back into the approval: **False**. back-filling the approval's sender field would make an unpinned field look pinned and make this mailbox read as approved in advance, which it was not. The approval keeps its placeholder and the execution carries the real address.

### The approval is spent

it authorised exactly one send and one was made. A second send to this recipient, including a resend after a bounce that has not happened yet, is a second use of a one-use approval and needs its own.

The packet still reads `send_status: NOT_AUTHORIZED`, unchanged, and records no approval of its own.

**Next: the operator waits, and if a reply arrives forwards it so it can be frozen verbatim before anything interprets it; if a non-delivery report arrives instead, that is attested and this dispatch moves to FAILED.** Performed by OPERATOR; this repository may not perform it.
