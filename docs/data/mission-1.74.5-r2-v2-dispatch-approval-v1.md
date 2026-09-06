# Mission 1.74.5 — The second approval, and the first one stays spent

Generated from `globalping-r2-v2-dispatch-approval-v1.json`. Do not edit by hand.

**Execution status: `PENDING_MANUAL_OPERATOR_ACTION`**

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
| execution | `DISPATCH_ATTEMPTED_DELIVERY_FAILED` | `PENDING_MANUAL_OPERATOR_ACTION` |
| provider contacted | False | False |
| approval hash | `90fd201d9d1abd06…` | `41590d55b9626fce…` |

the recipient differs, and the recipient is a bound field, so this authorises a different action rather than extending a spent one. The two approvals name different content digests and neither can stand in for the other.

The earlier approval was reused: **False**. Its attempt reinterpreted as delivered: **False**.

## The ceiling belongs to the medium

still a manual mail send, so still Mission 1.66's ceiling: the send happens in a mail client nothing in this repository can observe. The channel changed from the designated address to the published one and the OBSERVABILITY did not, because the ceiling is a property of the medium rather than of the address.

Reachable: `OPERATOR_ATTESTED`. Upgrade path: NONE for this channel. A future mission may record OPERATOR_ATTESTED and nothing above it.

## Nothing has been performed

| | |
|---|---|
| send attempts | 0 |
| sends made | 0 |
| deliveries confirmed | 0 |
| provider contacted | False |
| emails sent by this repository | 0 |
| mail connector used | False |
| mailbox searched | False |
| operator attestation | False |
| attestation level | None |

The packet still reads `send_status: NOT_AUTHORIZED`, unchanged, and records no approval of its own.

**Next: the operator sends one email to d@globalping.io with the approved subject and the frozen body, from a mailbox of their choosing, then attests to it.** Performed by OPERATOR; this repository may not perform it.
