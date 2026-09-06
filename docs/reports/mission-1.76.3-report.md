# Mission 1.76.3 — One reply approved, and nothing sent

**Outcome: `R2_B_DISPATCH_APPROVED_AWAITING_MANUAL_OPERATOR_ACTION`.**

The operator approved exactly one manual reply of `GP-R2-B-Q1` in the existing thread. This
repository sent nothing, read no mailbox, used no connector, and moved no verdict.

---

## Report

```
APPROVES                     = GP-R2-B-Q1 v1
MECHANISM                    = OPERATOR_MANUAL_REPLY_IN_EXISTING_EMAIL_THREAD
APPROVED_CONTENT_SHA256      = fe312c37b8622e5abbdaaa541d00189c5a4a2f78b7082d3f70a034b7413da4dc
APPROVAL_SHA256              = 7df1876ca1e110004a4bd93f3e83a30036b3238a2beac3708b83c8e52188de7d
RECIPIENT                    = DETERMINED_BY_THE_THREAD_NOT_SUPPLIED (not bound)
MAX_OUTWARD_REPLIES          = 1
EXECUTION_STATUS             = PENDING_MANUAL_OPERATOR_ACTION
OUTWARD_REPLIES_MADE         = 0
SEND_ATTEMPTS                = 0
PROVIDER_CONTACTED           = false
OPERATOR_ATTESTATION         = false
ATTESTATION_LEVEL            = null
BYTE_VERIFICATION_POSSIBLE   = false
EMAILS_SENT_BY_THIS_REPO     = 0
MAILBOX_READS                = 0
CONNECTOR_EXECUTIONS         = 0
R2_B_BEFORE / AFTER          = THIRD_PARTY_TARGET_SCOPE_UNRESOLVED / unchanged
GLOBALPING_PASS_PARTIAL_FAIL = 11 / 1 / 0
COUNTERPART_STATUS           = COUNTERPART_UNRESOLVED
RESIDUALS_CLOSED             = 0
```

## The digest was recomputed, and the body was compared

The approval arrived carrying both a content hash and the approved body in full. Copying
either would make the approval name whatever the instruction said rather than whatever the
packet is.

So the hash was **recomputed** from the packet's own `hash_covers` fields as stored, and it
equals both the quoted value and the packet's own `content_sha256`. The body was compared
**byte for byte** against the frozen packet body, and it matched. Both the stated and the
recomputed values are kept, and the gate refuses them disagreeing — which turns a quoted
string into a check that could have failed.

**It could have.** Mission 1.74.7 found a supplied quotation differing from the stored bytes
by a trailing space. That difference changed no meaning and was recorded anyway, because a
record that adopted a quotation silently there would have done so just as silently here.

## The approval sits beside the packet, and the packet still reads `NOT_AUTHORIZED`

Mission 1.66 settled that marking a frozen document APPROVED changes the artifact the
operator read. Here it would not even have moved the packet's digest, which covers seven
binding fields and not that one — and it would still have changed the bytes.

So the packet is **byte-identical**, and its `send_status: NOT_AUTHORIZED` with
`operator_approval_recorded: false` still reads correctly, because that field means **THIS
DOCUMENT RECORDS NO AUTHORIZATION** and never that none exists. The packet's own gate
asserts exactly that, and it stayed green throughout.

Both statements are true at once, which is why the gate now refuses a record claiming the
approval lives inside the packet — that was the probe's one escape, and it is closed.

## The recipient is still not an address, and the digest still says so

The action is bound by seven fields: the enquiry, the packet version, the content digest,
the mechanism, the subject, the thread binding and the reply limit. The digest excludes
itself, the execution status, the recorded date and **the recipient**.

The recipient is not omitted; it is **not a value**. The mechanism is a reply inside an
established thread, which inherits its recipient, and the sender of the message being
answered is still `NOT_ESTABLISHED` — Mission 1.76.1 attempted the mailbox read and the
connector refused it. Binding the sentinel would make the digest read as though an address
had been pinned, which is worse than binding nothing: **an unpinned field that looks pinned
is the field a later reader stops checking.**

What is bound instead is the **thread**, by three digests — its subject, the prior enquiry
packet's hash and the prior reply's body hash. The gate refuses an `@` in the recipient, a
recipient inside `hash_covers`, and a record claiming the recipient is bound.

## The operator's exclusions are stored as structure, not as prose

The approval named eight things it does not authorise: a new standalone email, a different
thread, a modified body, a second send, any Gmail connector action, any mailbox read, any
Globalping measurement, any other provider contact.

All eight are recorded as fields, every one `false`, and the gate refuses any of them flipped
true **or dropped**. A list that can be shortened is a list a later reading widens by
forgetting, and this approval will be read again when a reply arrives.

Two things it explicitly does not lift are recorded beside them. The mailbox read that would
establish the earlier sender stays unauthorised — and this approval neither changes that nor
depends on it. And the attribution of whatever comes back is unimproved: a reply to this
reply arrives in the same thread and inherits the same problem. **Approving a question does
not improve the evidentiary standing of its answer.**

## An approval is not an execution, and this is where a fictional record is cheapest

Once the approval exists, every field an execution record needs is already known — the
subject, the body, the thread, the limit. A record could fill itself in completely and be
entirely fictional.

So the execution reads `PENDING_MANUAL_OPERATOR_ACTION` with every counter at zero, no
attestation, no attestation level and no provider contact. `SENT` is reachable only through
an explicit operator attestation, and this repository cannot reach it by any other route.

**`BYTE_VERIFIED` stays unreachable, and the reason is the medium rather than the channel's
novelty.** A manual reply happens in a mail client nothing here can observe. That this
channel is a thread rather than a fresh message changes the addressing and not the
observability, so the reachable set is exactly `["OPERATOR_ATTESTED"]` and the upgrade path
reads **NONE** — worth saying, because a new channel invites the thought that its properties
might be new too.

## It is a third approval, not a renewal, and the gate asserts that live

Two approvals precede this one. The first was spent by an attempt that bounced; the second
by the one send it authorised. Neither reaches this packet, and the gate checks it against
the records as they stand rather than against a snapshot: each spent approval must still
answer to its own hash, must not name this packet's digest, must not name this question id,
and must not share this approval's digest.

So an edit that quietly retargeted a spent approval at this packet fails here rather than
passing quietly. Eight probe cases attack the spent approvals rather than this one, and all
eight are refused.

## Verification

- Probe: **169 deliberate violations, 169 caught, 0 escaped**, plus **4 of 4 positive
  controls**, nine files restored byte for byte.
- **One escape was found and closed by adding a rule**: a record could claim the approval was
  recorded inside the packet while the packet said otherwise, and nothing refused the
  contradiction.
- **Packet mutations repair the approval's file hash before the gate sees them**, so the
  content checks have to do the work instead of hiding behind the outer file-hash guard —
  Mission 1.74.6's shape.
- **The controls are the point.** The legitimate `SENT` / `OPERATOR_ATTESTED` transition must
  stay representable, because a gate that only accepts the state we happen to be in is not a
  gate. So must a bounce, because a gate that can only express success would force the next
  failure to be recorded as something it is not — and this arc supplies its own proof that a
  reply can fail to deliver. And re-dating the record must **not** refuse, because the digest
  excludes the recorded date by design.
- **3234 bare-python tests**; both runners green; `ruff format --check`, `ruff check`, mypy
  over 197 files; contract and catalog `--check`; all **52** CI gates, one of them new.

## What did not move

R2-B stays `THIRD_PARTY_TARGET_SCOPE_UNRESOLVED`, C9 stays `PARTIAL`, the tally stays 11/1/0
and the verdict stays `COUNTERPART_UNRESOLVED`. **An approval to ask is not an answer**, and
the gate asserts that too.

`GP-R2-Q1` v1 and v2, both their approvals, both execution records, the frozen reply and the
`GP-R2-B-Q1` packet are untouched. Zero emails, zero Gmail reads or writes, zero connector
calls, zero GitHub writes, zero public posts, zero provider contacts, zero measurements, zero
target requests, zero research API calls, zero model calls, zero embeddings, zero Claims, zero
Evidence, zero independence groups, zero scores, zero source registrations, zero governance
mutations, zero canonical mutations, zero migrations.

## Next

**One operator action, performed outside this repository:** send exactly one manual reply in
the existing thread, with the approved subject and the frozen body, then attest to it. This
repository may not perform it, and an attestation is the only evidence this channel can
produce.

Separately and still open: establishing who sent the earlier reply. This approval does not
lift it, does not depend on it, and asking again does not settle it.

**Mission 1.77 was not started.**
