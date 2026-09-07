# GP-R2-B-Q1 — approved, and sent once

Generated from `globalping-r2b-dispatch-approval-v1.json`. Do not edit by hand.

**Execution status: `SENT`**, recorded by Mission 1.76.4. An approval says an action MAY be performed; this records that one WAS. It does not record that the reply arrived.

## What was approved

| | |
|---|---|
| enquiry | `GP-R2-B-Q1` v1 |
| mechanism | `OPERATOR_MANUAL_REPLY_IN_EXISTING_EMAIL_THREAD` |
| subject | Terms scope: HEAD measurements of publicly reachable third-party websites |
| recipient | `DETERMINED_BY_THE_THREAD_NOT_SUPPLIED` |
| maximum outward replies | **1** |
| approved content hash | `fe312c37b8622e5a…` |
| approval hash | `7df1876ca1e11000…` |

## The digest was recomputed and the body compared

the instruction carries a digest, and copying it would make the approval name whatever the instruction said rather than whatever the packet is. Recomputing turns a quoted string into a check that could have failed.

the instruction restated the body in full. A restatement is a claim, and this arc has already found a supplied quotation differing from stored bytes by a trailing space. The comparison is byte for byte and it passed.

Body byte-identical to the frozen packet: **True**.

## The thread is bound, not an address

it is not a value. The mechanism is a reply inside an established thread, which inherits its recipient, and the sender of the message being answered is still NOT_ESTABLISHED. Binding a sentinel would make the digest read as though an address had been pinned. What is bound instead is the THREAD, by three digests.

| bound | value |
|---|---|
| thread subject | Terms scope: HEAD measurements of publicly reachable third-party websites |
| prior enquiry digest | `987f3ff57ce661c6…` |
| prior reply digest | `be3845f89b636b96…` |

## What this approval does not authorise

| | |
|---|---|
| a new standalone email | **no** |
| a different thread | **no** |
| a modified body | **no** |
| a second send | **no** |
| any gmail connector action | **no** |
| any mailbox read | **no** |
| any globalping measurement | **no** |
| any other provider contact | **no** |

### And what it does not lift

- still unauthorised, and explicitly excluded above. The earlier sender remains NOT_ESTABLISHED, and this approval does not change that or depend on it.
- a reply to this reply arrives in the same thread and inherits the same problem. Approving the question does not improve the evidentiary standing of its answer.

## What was performed

| | |
|---|---|
| outward replies made | 1 |
| send attempts | 1 |
| deliveries confirmed | 1 |
| provider contacted | True |
| provider replied | True |
| operator attestation | True |
| attestation level | OPERATOR_ATTESTED |
| mail connector used | False |
| mailbox read | False |
| emails sent by this repository | 0 |

Mission 1.66's ceiling, unchanged: a manual reply happens in a mail client nothing in this repository can observe. The channel is a thread rather than a fresh message and the OBSERVABILITY is identical, because the ceiling is a property of the medium.

## A send is not a delivery

| | |
|---|---|
| sent at | `2026-09-07T19:19:30+04:00` |
| sender | `thib.chm@gmail.com` |
| recipient | None |
| recipient comparison | `NOT_APPLICABLE` |
| body used, per the attestation | `THE_FROZEN_PACKET_BODY` |
| body compared by this repository | False |
| message id | None |
| **delivery** | **`CONFIRMED`** |
| delivery established by | A_PROVIDER_REPLY_ANSWERING_THIS_MESSAGE_S_OWN_BOUNDED_QUESTION |

to answer the question the correspondent had to receive it, and the answer is responsive to THIS message rather than to the thread in general. That is what establishes delivery; the send attestation never could.

unchanged, and still not what established the delivery. Silence from an unexamined mailbox establishes nothing; a responsive answer does.

**Provider contacted: true. The message reached the provider's published contact channel and was answered from it, so both reasons this field was false have been removed: delivery is established, and the correspondent is established as the provider's own published address rather than an unknown party. It became true on evidence, not on the passage of time.**

The attestation covers that a reply was sent, that it was sent exactly once, that it was sent as a reply in the established thread, the sending mailbox, the subject, the stated send time, that the frozen body was used. It does not cover delivery, receipt by a person, who received it, the bytes that actually left the mail client, a reply to it.

### No recipient was attested

the operator stated none, and a reply in a thread does not type one -- it inherits whatever address the thread carries. The sender of the message being answered is still NOT_ESTABLISHED, so this record cannot say who received the reply and does not guess. What IS established is the thread it went into.

the approval bound a sentinel rather than an address, deliberately, so there is no approved recipient for an attested one to match. Reporting a MATCH here would invent an agreement between two things neither of which is an address.

### The sender is attested, not checked

the approval binds no sender at all -- a reply in a thread has no typed address on either end -- so no field of it constrains the mailbox and no artifact here records one. The mailbox is known because the operator said so, and that is the whole of the evidence for it.

Written back into the approval: **False**. the approval's binding fields are what the operator approved, and the sender is not among them. Writing it back would move the approval digest and make a field that was never approved read as though it had been.

### The reply followed its approval

the approval record was committed at 2026-09-07T01:12:27+04:00 and merged at 01:21:45+04:00; the attested send is 2026-09-07T19:19:30+04:00, about eighteen hours later. The ordering is checkable from the repository's own history rather than asserted, which matters because an execution recorded before its approval would be an approval written to fit an act already taken.

### The approval is spent

it authorised exactly one outward reply and one was made. A second reply, including a resend after a bounce that has not happened, is a second use of a one-use approval and needs its own.

### A reply came back, and it is frozen elsewhere

Frozen verbatim in `docs/data/globalping-r2b-provider-reply-v1.json` before anything read it, and cited by hash `9810e841d386278e…`. What it means is decided in a separate reviewed record, because a document holding both the evidence and the conclusion can adjust the first to suit the second.

**Next: wait. If a reply arrives it is frozen verbatim in its own record before anything interprets it; if a non-delivery report arrives, this execution moves to DISPATCH_ATTEMPTED_DELIVERY_FAILED and this approval is spent either way.** Performed by OPERATOR; this repository may not perform it.
