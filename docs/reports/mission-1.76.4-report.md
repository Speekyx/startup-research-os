# Mission 1.76.4 — The reply was sent, and a person is the only witness to it

**Outcome: `R2_B_REPLY_SENT_OPERATOR_ATTESTED_DELIVERY_UNCONFIRMED`.**

The operator sent the approved `GP-R2-B-Q1` once by hand, as a reply in the existing thread,
and attested to it. No mailbox was read, no connector used, and this repository sent nothing.

---

## Report

```
EXECUTION_STATUS             = SENT   (was PENDING_MANUAL_OPERATOR_ACTION)
OUTWARD_REPLIES_MADE         = 1      SEND_ATTEMPTS = 1
SENT_AT                      = 2026-09-07T19:19:30+04:00
ATTESTED_SENDER              = thib.chm@gmail.com
ATTESTED_RECIPIENT           = null   (a reply types none)
RECIPIENT_COMPARISON         = NOT_APPLICABLE
ATTESTATION_LEVEL            = OPERATOR_ATTESTED
BYTE_VERIFICATION_POSSIBLE   = false
DELIVERY_STATUS              = UNCONFIRMED     DELIVERIES_CONFIRMED = 0
PROVIDER_CONTACTED           = false           PROVIDER_REPLIED = false
MESSAGE_ID                   = null
APPROVAL_SHA256              = 7df1876ca1e11000…  (unchanged)
APPROVAL_EXHAUSTED           = true
EMAILS_SENT_BY_THIS_REPO     = 0   MAILBOX_READS = 0   CONNECTOR_EXECUTIONS = 0
R2_B_BEFORE / AFTER          = THIRD_PARTY_TARGET_SCOPE_UNRESOLVED / unchanged
GLOBALPING_PASS_PARTIAL_FAIL = 11 / 1 / 0
COUNTERPART_STATUS           = COUNTERPART_UNRESOLVED
```

## The execution moved and the approval did not

`approval_sha256` is **byte-identical**: `7df1876ca1e11000…` before the send and after it.
That is not a coincidence — the digest excludes the execution, the recorded date, itself and
the recipient precisely so the record can carry a performance without becoming a different
approval.

It is also the strongest check available here. **An execution that moved the approval digest
would be an approval rewritten to fit an act already taken**, and the gate recomputes the
digest live rather than trusting the stored value. Mission 1.76.3 recorded the approval;
this mission recorded the execution, and `mission` still reads `1.76.3` while
`recorded_by_mission` reads `1.76.4`. **A later mission that fills in an execution does not
become the approval's author.**

## The ordering is read off the repository's own history

The approval was committed at `2026-09-07T01:12:27+04:00` and merged at `01:21:45+04:00`.
The attested send is `2026-09-07T19:19:30+04:00`, about eighteen hours later.

That matters because the one thing an approval record must never be is a document written to
fit something already done. Here the ordering is **checkable from git rather than asserted**,
and the gate refuses a send time earlier than the approval's recorded date.

The timestamp carries an explicit offset, and the gate refuses one without: a naked local
time names no instant, and this record is read by people who are not in the operator's
timezone and cannot ask.

## A send is not a delivery

The attestation establishes an act by the sender. It is silent on the outcome at the
receiver. So `deliveries_confirmed` is **0**, the delivery status reads **`UNCONFIRMED`**,
and **`provider_contacted` stays false**.

**This arc supplies its own proof the two come apart**: the v1 message to
`legal@globalping.io` was also sent, and then it bounced.

And here `provider_contacted` is false for a **second and independent reason**. Who is on the
other end of this thread is `NOT_ESTABLISHED`, so even a confirmed delivery would not
establish that the *provider* was contacted. Two reasons, either alone sufficient.

**Silence is not an observation.** The record does not say no bounce was reported — that
would imply someone checked a mailbox. It says nothing here looked, and the approval excluded
looking by name.

**The state can still move.** A later bounce reaches `DISPATCH_ATTEMPTED_DELIVERY_FAILED`; a
confirmation needs its own source, and the gate refuses one whose source is the attestation
of *sending*. One new rule was added for a hazard this channel introduces: **a later message
in a thread would not confirm delivery of this one**, because a subsequent message
establishes that somebody wrote in the thread, not that any particular earlier message
arrived. The two are close enough to be conflated and different enough to matter.

## Nobody knows who received it, and none was guessed

`attested_recipient` is **null**. A reply in a thread types no address — it inherits whatever
the thread carries — and the sender of the message being answered is still `NOT_ESTABLISHED`.

So `recipient_comparison` reads **`NOT_APPLICABLE`** rather than `MATCH`. The approval bound a
sentinel, so there is no approved address for an attested one to agree with, and **reporting
a match would invent an agreement between two things neither of which is an address.** The
gate refuses an attested recipient outright, including the sentinel itself.

What *is* recorded is that the reply went into the bound thread — on the operator's word, and
the record says that is the whole of the evidence for it. The three digests that bind the
thread are properties of documents this repository holds; that the mail client's thread is
that conversation is not one of them.

## The sender is attested, not checked, and it was not written back

The approval binds **no sender at all** — a reply in a thread has no typed address on either
end — so no field of it constrains the mailbox and no artifact here records one. The mailbox
is known because the operator said so.

It was deliberately **not** written back into the approved action. Doing so would move the
approval digest and make a field the operator never approved read as though they had. The
gate refuses any `sender` key appearing in the action.

## Nothing was invented to fill a field

No message id — the only route to one runs through a mailbox the approval excluded, so the
field is null rather than plausible. No body comparison — that would need the same mailbox.
No reply recorded, and the gate refuses one: **a reply is a document, and it would be frozen
verbatim in its own record before anything interpreted it.**

`BYTE_VERIFIED` stays unreachable. The channel changed from a fresh message to a thread and
the **observability did not**, because the ceiling is a property of the medium.

## The approval is spent

It authorised exactly one outward reply and one was made. A second reply — including a resend
after a bounce that has not happened — is a second use of a one-use approval and needs its
own. All three approvals in this arc are now exhausted: one by a bounce, one by a send, one
by this reply.

## Verification

- Probe: **120 deliberate violations, 120 caught, 0 escaped**, plus **4 of 4 positive
  controls**, nine files restored byte for byte.
- **The control that matters is INVERTED.** Mission 1.76.3 proved `SENT` was reachable while
  the record was pending; this proves the **pending state is still representable** now that
  the record has left it. A gate that only accepts the state we happen to be in is not a gate.
- The other two controls keep a **bounce** representable and a **delivery confirmed by an
  independent source** representable — a gate that could only express one outcome would force
  the next one to be recorded as something it is not.
- **Four assertions from Mission 1.76.3 were re-pointed rather than deleted.** Each pinned the
  state the repository happened to be in — that the execution was pending and empty — rather
  than the property that made it correct. A test asserting the execution is forever pending is
  a test asserting the approved action may never be performed.
- **3296 bare-python tests**; both runners green; `ruff format --check`, `ruff check`, mypy
  over 197 files; contract and catalog `--check`; all **52** CI gates.

## What did not move

R2-B stays `THIRD_PARTY_TARGET_SCOPE_UNRESOLVED`, C9 stays `PARTIAL`, the tally stays 11/1/0
and the verdict stays `COUNTERPART_UNRESOLVED`. **A sent question is not an answer**, and the
gate asserts that too.

The frozen `GP-R2-B-Q1` packet is byte-identical and still reads `NOT_AUTHORIZED`. `GP-R2-Q1`
v1 and v2, both their approvals and both their execution records are untouched, and the
frozen R2 reply still carries `sufficient_for_provider_authority: false`.

Zero emails sent by this repository, zero Gmail reads or writes, zero connector calls, zero
GitHub writes, zero provider contacts, zero measurements, zero target requests, zero research
API calls, zero model calls, zero embeddings, zero Claims, zero Evidence, zero independence
groups, zero scores, zero canonical mutations, zero migrations.

## Next

**Wait.** No deadline was agreed with the provider, and inventing one would be our own
schedule dressed as theirs. If a reply arrives it is frozen verbatim in its own record before
anything interprets it. If a non-delivery report arrives, this execution moves to
`DISPATCH_ATTEMPTED_DELIVERY_FAILED` and the approval is spent either way.

**Silence would close nothing.** R2-B is unresolved because no statement establishes
third-party target scope; a provider that never answers has still made no statement.

Separately and still open: establishing who sent the earlier reply — which this send neither
lifts nor depends on, and which asking again does not settle.

**Mission 1.77 was not started.**
