# Mission 1.66 — Approved Dispatch Execution V1

**Outcome: `ONYPHE_APPROVED_DISPATCH_AWAITING_MANUAL_EXECUTION`.** The operator's
approval arrived, was verified against a recomputed envelope hash, and is recorded
as an approval. The action it authorises has not been performed. **Nothing was
sent**, and §28 B says directly that this is not a failure.

---

## 0. The question this mission exists to answer

Not *may the enquiry be sent* — Mission 1.65 settled that. The question is
**whether it was**, and the honest answer today is no.

That distinction is the mission. A permission is not an event, and the gap between
them is exactly where a dispatch log stops describing what happened and starts
describing what was allowed.

## 1. Preconditions

| fact | value |
|---|---|
| PR #108 | MERGED at `f6fee37b7e8e…` |
| operator-reported main | `f6fee37`, agrees with git |
| local main == origin/main | yes |
| working tree | clean |
| migration head | `0035_refusal_provenance` |

The brief states the expected commit. It was **checked against git rather than
accepted**: a brief reporting a commit is a claim about the repository, and the
repository is the authority on it.

Both frozen hashes recomputed from the artifacts as stored on the merged main:

```
content   0b39ef325fd42836a3b65284a7386cbca7ae8f22afcb9629d5574e0ff0f23e9f   MATCH
envelope  12a62853706a3c65f04859577fa3e9f2d4efaeca99cbf16badf759a55b4fe0d2   MATCH
operator  12a62853706a3c65f04859577fa3e9f2d4efaeca99cbf16badf759a55b4fe0d2   MATCH
```

**Baseline: every counter matched, drift `none`.** 325 / 325 / 33, 44 Claims, 45
revisions, 58 Evidence, 1 INFERRED, 1 threshold, 1 derivation, 0 refusals,
SUPPORTS 57 / CONTRADICTS 1, 4 reliability assessments, 0 independence groups,
Opportunity 1 / 1 / 7, 29 sources, no scores table.

## 2. An approval is not an execution

The two are unusually easy to merge here, and the reason is worth stating plainly:
**once the approval exists, every field an execution record needs is already
known.** Recipient, subject, body and channel are all frozen in the envelope the
approval names. A dispatch record could therefore fill itself in completely,
consistently, and be entirely fictional.

So the artifact keeps them apart:

| section | says |
|---|---|
| `operator_approval` | an operator said this exact action MAY be performed, naming it by a hash |
| `execution` | somebody performed it |

and `SENT` is reachable only through an explicit operator confirmation **plus an
actual sender mailbox that no frozen document contains**. That second requirement
is what makes the first non-trivial: the sender is the one fact the approval
cannot supply, because the envelope deliberately froze a placeholder.

Every execution field reads `null`, and that is the mission's result rather than
missing work.

## 3. The repository cannot verify a manual send

Missions 1.36.1 and 1.42.1 both stopped at the same boundary: a value was
authorised and the keystroke was not. **There, the keystroke happened inside the
repository**, so a terminal guard could require a person to be present, and
`record_reliability_assessment.py` refusing on `EOFError` was a real check.

A manual outbound send happens in a mail client nothing here can observe. **No
guard can establish it.** The repository can record what the operator attests, and
the only honest response is to make the attestation level explicit:

```
NOT_APPLICABLE_NOTHING_SENT   OPERATOR_ATTESTED   BYTE_VERIFIED   NOT_AVAILABLE
```

`BYTE_VERIFIED` requires a body hash equal to the approved content hash. An
attestation may never be promoted into proof by relabelling.

**And the check discriminates rather than merely refusing.** The probe includes a
positive case: an execution reporting a byte-verified send with the correct body
hash is **accepted**. A gate that says no to everything is not a gate.

## 4. The approval was not written into the document it approves

Mission 1.56 settled this shape for a frozen manifest: marking a document APPROVED
changes the bytes that were approved.

Here it is sharper, because the envelope hash covers only the seven binding
fields — so an `approval_recorded: true` **would not have moved the hash at all**.
It would still have changed the artifact the operator read, which is the thing
that matters. The approval therefore lives in the execution record.

**A guard now does a second job.** Mission 1.65's validator asserts the envelope's
`approval_recorded` is false. It wrote that to mean *this mission stops before
approval*; it now also keeps the approval out of the frozen document. The field
means **this document records no approval**, never that no approval exists
anywhere — and that sentence is written into the record so a later reader cannot
derive the second from the first.

The sender placeholder is likewise not replaced. The envelope records what was
**approved**; the actual mailbox is what was **used**, and those are two facts.

## 5. The connector that was available the whole time

A mail-capable connector sits in this runtime. The content is approved, the
recipient is established, and one call would have produced a completed dispatch
with matching body, matching recipient, and a hash that still verifies.

**It would have been a different action.** `outbound_channel` is one of the seven
fields the approved hash binds, so an automated send carrying identical text to
the identical recipient is not the approved action by another route. And it would
have been an outward action on the operator's behalf, from a mailbox they never
named.

`CONNECTOR_EXECUTIONS = 0`. The route to authorising one is a re-frozen envelope
binding `AUTHORIZED_CONNECTOR` and an exact sender, carrying a different hash,
approved separately — never a reinterpretation of this approval.

## 6. Integrity checks, frozen before any send

The only time such a standard means anything.

| field | must equal | on mismatch |
|---|---|---|
| recipient | `contact@onyphe.io` | `RECIPIENT_DIVERGENCE` |
| channel | `OPERATOR_MANUAL_SEND` | `CHANNEL_DIVERGENCE` |
| subject | the frozen subject | `SUBJECT_DIVERGENCE` |
| body | `0b39ef32…f0f23e9f` | not the approved action |
| send count | 1 | `DUPLICATE_DISPATCH_OCCURRED` |

**A sent message cannot be unsent**, so a duplicate is reported rather than tidied
away. And a divergence never repairs the historical envelope: the envelope records
what was approved, and a divergence is a fact about the execution.

## 7. Two absences recorded as the weaker true claim

**The approval's exact time is `NOT_ESTABLISHED`**, with a lower bound that is
actually true: `2026-09-05T17:09:39Z`, the merge of PR #108, before which the hash
the approval names did not exist on main. A timestamp nobody can check is worth
less than a bound that holds.

**No mailbox was searched.** The record says only that the repository holds no
provider reply and that the operator's mailbox was not read — never that no reply
exists. §2 asks for an operator statement as dispatch evidence and nothing asks
for a mailbox to be searched, so searching it would have been an access nobody
requested, and it would have replaced an attestation with an inference. *Empty
because nobody looked* and *empty because somebody looked* stay different facts.

## 8. Nothing moved

| | |
|---|---|
| enquiries sent, connector executions, follow-ups | 0 |
| mailbox searches, replies frozen, replies interpreted | 0 |
| first-party retrievals, measurement queries, counts, hosts, banners | 0 |
| trials, purchases | 0 |
| canonical mutations, sources, reviews, reliability values | 0 |
| model calls, embeddings, migrations | 0 |

ONYPHE stays B2 PARTIAL with port membership and post-30-day location fields
UNKNOWN. Netlas stays A7 PASS / A8 PARTIAL, its Mission 1.61 content approval
valid, its recipient unestablished, nothing guessed and no obfuscation decoded.
**Qualified 0 of 4, so `PAIR_ANALYSIS_NOT_READY`.**

Email provenance is repository evidence. It is not a RawRecord, a Signal, a Claim
or an Evidence row, and no source was registered because a provider was contacted.

## 9. Verification

- Validator probed with **193 deliberate violations, 193 caught**, plus **one
  positive case** asserting a correctly evidenced send is accepted. Every case
  asserts it mutated the bytes first.
- Two defects in the probe itself were found and fixed: a tuple index that wrote
  `null` into a record, and a positive control that moved one record without the
  other so it was refused by cross-record consistency rather than by the rule
  under test. The second is the more interesting: **a positive control that fails
  for the wrong reason proves nothing.**
- One improvement to the validator followed from the first: a record file that is
  not a JSON object is now refused **by name**, rather than failing three frames
  down with a message that says nothing about which file was wrong.
- **58 tests** in `test_dispatch_execution.py`; **1878 bare-python tests** pass.
- CI gate **34**: `render_dispatch_execution.py --check`, recomputing both hashes
  on every run.

## 10. Next

**`STOP_AWAITING_MANUAL_EXECUTION`.** The next action is outside this repository.

The operator sends the packet at
[`onyphe-enquiry-dispatch-packet-v1.md`](../data/onyphe-enquiry-dispatch-packet-v1.md),
once, manually, to the approved recipient, and reports back: that it was sent, the
exact sender mailbox, that the send was manual, and that it happened once.
Optionally the time, the message id and the provider — **optional deliberately**,
because a webmail send may expose no message id to the sender at all, and refusing
to record the send for want of one would punish an honest report.

The execution record then moves to `SENT` under the checks frozen above.

**No mission is needed until that happens**, and §31 forbids creating one merely
to poll a mailbox. Netlas is independent: when the operator supplies the exact
address displayed at `netlas.io/legal`, that envelope completes, is hashed, and
gets its own approval string. **Mission 1.67 was not started.**
