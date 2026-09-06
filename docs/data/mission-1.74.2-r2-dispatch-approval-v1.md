# Mission 1.74.2 — The second enquiry approved, and the ceiling that comes with it

Generated from `globalping-r2-dispatch-approval-v1.json`. Do not edit by hand.

**Execution status: `PENDING_MANUAL_OPERATOR_ACTION`**

## What was approved

| | |
|---|---|
| enquiry | `GP-R2-Q1` |
| mechanism | `OPERATOR_MANUAL_EMAIL` |
| channel | `PROVIDER_DESIGNATED_TERMS_CHANNEL` |
| recipient | `legal@globalping.io` |
| subject | Terms scope: HEAD measurements of publicly reachable third-party websites |
| sender | `PLACEHOLDER_PERMITTED_FOR_MANUAL_SEND_ONLY` |
| maximum sends | **1** |
| approved content hash | `713d62c91ac56934…` |
| approval hash | `90fd201d9d1abd06…` |

The approval hash binds `approves`, `approved_content_sha256`, `mechanism`, `recipient`, `approved_subject`, `maximum_sends`, and excludes `approval_sha256`, `execution`, `recorded_at`, `sender`.

## Three fields of four, and the cost was stated in advance

Mission 1.65 stated this cost in advance and it recurs here: under a manual mail send the sender genuinely is not determined until the send, so the hash pins three fields of four. Pinning the fourth would produce a different approval that SUPERSEDES this one rather than editing it.

the R1 approval bound every field, because a public repository and a GitHub identity are determined before the act. An email channel is not. The difference is a property of the CHANNEL, and it is the same property that decides the verification ceiling below.

## The ceiling inverts against Mission 1.74.1

- byte verification possible: **False**
- levels reachable: `OPERATOR_ATTESTED`

Mission 1.66 established it: a manual outbound send happens in a mail client nothing in this repository can observe, so no guard can establish that the message left. Mission 1.74.1 escaped that ceiling because a public issue has a durable public URL. This channel has no such artifact, so the honest maximum is an attestation, and the record says that rather than implying an upgrade path that does not exist.

**Upgrade path.** NONE for this channel. A future mission may only record OPERATOR_ATTESTED. Importing a sent-message artifact from the operator's own mailbox was considered and refused in Mission 1.66: it would replace an attestation with an inference and require an access nobody requested.

## An approval is not an execution

| | |
|---|---|
| sends made | 0 |
| emails sent by this repository | 0 |
| mail connector used | False |
| mailbox searched | False |
| operator attestation recorded | False |
| attestation level | None |

a connector present in the runtime is not channel authorisation. An automated send of identical text to the identical recipient would still be a DIFFERENT action, because the channel is one of the bound fields and the sender would be a mailbox the operator never named.

## Two approvals, and they are not one

- R1 is approved separately in `docs/data/globalping-r1-dispatch-approval-v1.json`, edited by this mission: **False**.
- each names its own enquiry, its own mechanism and its own recipient, and each authorises exactly one act. Neither may be used to justify the other.
- Residuals closed by this mission: **0**. An approval to ask is not an answer.

The packet still reads `send_status: NOT_AUTHORIZED`, unchanged.

## Nothing moved

| | |
|---|---|
| EMAILS_SENT | 0 |
| MAIL_CONNECTOR_EXECUTIONS | 0 |
| MAILBOX_SEARCHES | 0 |
| PROVIDER_CONTACTS | 0 |
| ENQUIRIES_SENT | 0 |
| PUBLIC_POSTS | 0 |
| GLOBALPING_API_EXECUTIONS | 0 |
| CANONICAL_MUTATIONS | 0 |
| MODEL_CALLS | 0 |

**Next: the operator sends one email to legal@globalping.io with the approved subject and the frozen body, and separately posts the R1 issue.** Performed by OPERATOR; this repository may not perform it.
