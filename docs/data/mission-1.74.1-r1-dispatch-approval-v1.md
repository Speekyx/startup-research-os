# Mission 1.74.1 — One enquiry approved, and nothing posted

Generated from `globalping-r1-dispatch-approval-v1.json`. Do not edit by hand.

**Execution status: `PENDING_MANUAL_OPERATOR_ACTION`**

## What was approved

| | |
|---|---|
| enquiry | `GP-R1-Q1` |
| mechanism | `OPERATOR_MANUAL_GITHUB_ISSUE` |
| target | `jsdelivr/globalping` |
| identity | `@Speekyx` |
| title | HTTP measurement: is a 3xx response returned without following the redirect? |
| maximum public posts | **1** |
| approved content hash | `9eb7454581b65ccb…` |
| approval hash | `bcddd2b85a1a7be8…` |

The approval hash binds `approves`, `approved_content_sha256`, `mechanism`, `target_repository`, `identity`, `approved_title`, `maximum_public_posts`, and excludes `approval_sha256`, `execution`, `recorded_at`.

the ONYPHE envelope bound a PLACEHOLDER sender, because under manual email the sender is not determined until the send, and Mission 1.65 stated that cost in advance: the hash pinned three fields of four. Here the destination is a public repository rather than a mailbox, so mechanism, target, identity and title are all determined before the act. The cost stated there does not recur here.

## The approval is not in the document it approves

Mission 1.66. An approval flag written into the frozen packet would change the artifact the operator read, and the packet's own validator asserts that the packet records no approval. That field means THIS DOCUMENT RECORDS NO APPROVAL and never that no approval exists.

The packet still reads `send_status: NOT_AUTHORIZED`, `operator_approval_recorded: False`, `sent: False` — unchanged, and its file hash is recorded here so an edit is detectable.

## An approval is not an execution

| | |
|---|---|
| public posts made | 0 |
| issue URL | None |
| issue created by this repository | False |
| `gh issue create` invoked | False |
| GitHub API calls by this repository | 0 |
| operator attestation recorded | False |
| attestation level | None |

Mission 1.66 could reach only OPERATOR_ATTESTED because a manual email send happens inside a mail client nothing here can observe. A public GitHub issue has a durable public URL, so once the operator supplies it the posted title and body can be compared against the approved ones. The ceiling that arc hit is a property of the CHANNEL rather than of manual sending.

**Upgrade path.** the operator posts the issue and supplies its URL; a later mission retrieves it, compares the posted title and body against this approval, and records BYTE_VERIFIED. Until then the status stays PENDING_MANUAL_OPERATOR_ACTION.

## What this approval does not cover

- **R2 is not approved.** the operator approved GP-R1-Q1 only, and an approval of one action is not an approval of another that happens to have been prepared alongside it.
- Its packet still reads `NOT_AUTHORIZED`.
- Residuals closed by this mission: **0**. An approval to ask is not an answer.

## Nothing moved

| | |
|---|---|
| PUBLIC_POSTS | 0 |
| GITHUB_ISSUES_CREATED | 0 |
| GH_INVOCATIONS | 0 |
| EMAILS_SENT | 0 |
| PROVIDER_CONTACTS | 0 |
| ENQUIRIES_SENT | 0 |
| MAILBOX_SEARCHES | 0 |
| GLOBALPING_API_EXECUTIONS | 0 |
| CANONICAL_MUTATIONS | 0 |
| MODEL_CALLS | 0 |

**Next: the operator posts one public issue on jsdelivr/globalping and supplies its URL.** Performed by OPERATOR; this repository may not perform it.
