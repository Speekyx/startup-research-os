# GP-R2-B-Q1 — approved, and not sent

Generated from `globalping-r2b-dispatch-approval-v1.json`. Do not edit by hand.

**Execution status: `PENDING_MANUAL_OPERATOR_ACTION`.** An approval says an action MAY be performed. Nothing has been.

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

## Nothing has been performed

| | |
|---|---|
| outward replies made | 0 |
| send attempts | 0 |
| provider contacted | False |
| provider replied | False |
| operator attestation | False |
| attestation level | None |
| mail connector used | False |
| mailbox read | False |
| emails sent by this repository | 0 |

Mission 1.66's ceiling, unchanged: a manual reply happens in a mail client nothing in this repository can observe. The channel is a thread rather than a fresh message and the OBSERVABILITY is identical, because the ceiling is a property of the medium.

**Next: the operator sends exactly one manual reply in the existing thread, with the approved subject and the frozen body, then attests to it.** Performed by OPERATOR; this repository may not perform it.
