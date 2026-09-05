# Mission 1.66.1 — ONYPHE Manual Dispatch Attestation Recording V1

**Outcome: `ONYPHE_MANUAL_DISPATCH_ATTESTED`.** The operator sent the approved
enquiry manually — seven minutes after Mission 1.66 merged reporting it as
awaiting execution — and attested to it afterwards. **This repository still sent
nothing.**

This is the first outward action in the project's history to have been completed
at all. It was completed by a person.

---

## 0. What this mission records, and what it refuses to

An event that happened outside the repository, after a mission had honestly
reported that it had not yet happened.

That ordering is the whole design problem. The temptation is to make the earlier
record agree with the later fact, and it must be refused: **Mission 1.66 recorded a
moment, and a later event does not correct a mission that observed honestly.**

## 1. Preconditions

| fact | value |
|---|---|
| PR #109 | MERGED at `dcf6a387ae98…` |
| local main == origin/main | yes, `dcf6a38` |
| working tree | clean |
| migration head | `0035_refusal_provenance` |

Both frozen hashes recomputed from the artifacts as stored:

```
content   0b39ef325fd42836a3b65284a7386cbca7ae8f22afcb9629d5574e0ff0f23e9f   MATCH
envelope  12a62853706a3c65f04859577fa3e9f2d4efaeca99cbf16badf759a55b4fe0d2   MATCH
```

**Baseline: every counter matched, drift `none`.** An attestation about bytes that
have since moved attests to nothing, which is why the hashes are recomputed before
the attestation is read rather than after.

## 2. History is a chain, not a correction

| state | established by | record |
|---|---|---|
| `CONTENT_APPROVED` | Mission 1.61 / 1.65 | the frozen enquiry |
| `DISPATCH_APPROVED` | Mission 1.65 | `onyphe-dispatch-envelope-v1` |
| `APPROVED_AWAITING_MANUAL_EXECUTION` | Mission 1.66 | `onyphe-enquiry-dispatch-execution-v1` |
| `OPERATOR_ATTESTED_SENT` | Mission 1.66.1 | `onyphe-manual-dispatch-attestation-v1` |

Mission 1.66's execution record still reads `APPROVED_AWAITING_MANUAL_EXECUTION`,
its verdict still reads outcome B, and its baseline is untouched. **Both were true
when it ran.**

**The stale-record hazard was closed without falsifying anything.** A reader
meeting the Mission 1.66 record alone would take a historical state for the
current one, so that record gains **one appended forward pointer** naming this
attestation — and nothing else in it changes. It renders on the page:

> **Superseded by `onyphe-manual-dispatch-attestation-v1`**, which records *SENT,
> OPERATOR_ATTESTED*. At the time Mission 1.66 ran, nothing had been established
> as sent. That was true then, and it is still a true statement about that moment.

That is Mission 1.58's shape — a withdrawn selection appended to rather than
edited away.

**The alternative was rejected explicitly, and it is worth naming.** Mutating the
status to `SENT` would have required editing Mission 1.66's validator (its verdict
cross-check) and four of its tests, so that a just-merged mission's guarantees
described a different file. **A guard edited so that new work can pass is a guard
that never was.** The brief's deliverable 3 is satisfied by the pointer: the
artifact is updated, and what it says about its own moment is not.

## 3. The attestation

| field | approved | attested |
|---|---|---|
| recipient | `contact@onyphe.io` | `contact@onyphe.io` |
| channel | `OPERATOR_MANUAL_SEND` | `OPERATOR_MANUAL_SEND` |
| sender | `OPERATOR_CHOSEN_MAILBOX_AT_SEND_TIME` | `thib.chm@gmail.com` |
| subject | the frozen subject | identical |
| send count | 1 | 1 |
| sent at | — | `2026-09-05T21:57:00+04:00` |
| message id | — | `NOT_AVAILABLE` |

**Verdict: `EXECUTION_MATCHES_APPROVED_DISPATCH`.**

**The sender matched nothing, on purpose.** Its verdict is
`ALLOWED_BY_APPROVED_PLACEHOLDER` rather than `MATCH`, because the envelope
deliberately bound a placeholder instead of a mailbox — under a manual send the
sender genuinely is not determined until the operator sends. Naming it now is the
placeholder resolving as designed.

**A missing message id is allowed and explained.** A webmail send commonly exposes
none to the sender. Refusing to record the send for want of one would punish an
honest report, and inventing something shaped like a provider's identifier would
fabricate provenance for the one field nobody can check.

## 4. The weakest link carries the most consequential fact

Every other link in this chain answers to arithmetic:

- the content answers to a hash;
- the approval names that hash;
- the action the approval authorises is fixed by seven bound fields.

**The one fact that the message actually left rests on a person saying so**, because
that is the only evidence that exists for it. No sent-message artifact was
imported, and this repository never observed the send.

So the level is `OPERATOR_ATTESTED` and explicitly **not** `BYTE_VERIFIED`, and
the record states what the upgrade would take: the exact sent message imported and
hashed under the Mission 1.65 content boundary, compared against `0b39ef32…`. **A
weaker level stated with its upgrade path is a position; one stated without is a
shrug.**

**And the distinction is enforced rather than merely refused.** A positive probe
case supplies an attestation with an imported artifact and a body hash equal to the
approved content — and it is **accepted**. A gate that says no to every upgrade is
not enforcing a distinction.

*One note on provenance.* The brief mentions that the operator previously supplied
the sent Gmail message. No such artifact reached this session or the repository, so
the attestation's source is recorded as `OPERATOR_STATEMENT`. That changes nothing
about the outcome — the brief reaches the same conclusion — but the record says
what it actually rests on.

## 5. The stated cost that was actually paid

Mission 1.65 wrote this down before anyone could know whether it would matter:

> This envelope's hash binds content, recipient and channel but NOT the exact
> sender. Three of the four are pinned rather than four.

The message came from `thib.chm@gmail.com`. Nothing was breached: the approved
action never named which mailbox it would come from, and the sender is recorded
here as execution provenance. **A cost stated in advance and then incurred exactly
as described is the cheapest evidence available that the reasoning was honest
rather than decorative.**

The frozen envelope learned nothing from the send. Its placeholder is not
replaced, it is not marked sent, its dispatch count is still zero. It records the
permission; the attestation records the event.

## 6. A defect in this mission's own gate

The probe reported **157 of 157 caught** — and that number was hiding something.

One case set the reply status to `CHECKED_NONE_FOUND` while leaving
`mailbox_searched: false`. It was reported as caught. It was caught by **render
drift**: the status appears on the generated page, so the page no longer matched
its record. Re-render, and the case passes.

**A case caught by drift is a case a re-render releases.** And this one mattered:
*checked and found nothing* is a materially stronger claim than *not checked*, and
it is exactly the upgrade a later mission would be tempted to make.

Two repairs:

1. **A rule.** A claim about what is in a mailbox must be backed by having looked.
   `CHECKED_NONE_FOUND` and `RECEIVED_PENDING_REVIEW` now require
   `mailbox_searched`.
2. **A probe methodology.** Record mutations now go through `validate()` directly
   rather than through `--check`, so render drift can never stand in for a rule.
   Only hand-edits to generated pages use `--check`, where drift is the correct
   catcher.

Final split: **152 caught by rule, 5 by drift**, and the five are exactly the
byte-level edits to generated or frozen documents.

## 7. Nothing else moved

| | |
|---|---|
| emails sent by this repository, connector executions | 0 |
| mailbox searches, follow-ups, replies frozen, replies interpreted | 0 |
| measurement queries, counts, hosts, banners, trials, purchases | 0 |
| canonical mutations, sources, reviews, reliability values | 0 |
| model calls, embeddings, migrations | 0 |

**A sent question is not an answer**, and the sentence three missions have
repeated is finally being used for the case it was written for. ONYPHE stays B2
PARTIAL, with datascan port membership and post-30-day location fields UNKNOWN.

The reply status is `NOT_CHECKED_AFTER_DISPATCH` and explicitly **not**
`NO_RESPONSE_EXISTS`. The mailbox was not searched: nothing asked for it, and
reading it would have replaced an attestation with an inference.

Netlas is untouched — content approval valid, recipient unestablished, nothing
guessed and no obfuscation decoded, and the ONYPHE approval was not reused for it.
**Qualified 0 of 4, so `PAIR_ANALYSIS_NOT_READY`.**

## 8. Verification

- Validator probed with **157 deliberate violations, 157 caught** (152 by rule, 5
  by drift), plus **one positive case** asserting a legitimate `BYTE_VERIFIED`
  upgrade is accepted.
- **57 tests** in `test_dispatch_attestation.py`; **1935 bare-python tests** pass.
- CI gate **35**: `render_dispatch_attestation.py --check`.
- Baseline re-measured after all work: unchanged.

## 9. Next

**Wait.** A provider reply, or an address for Netlas, and neither is ours to
produce. §31 forbids creating a mission merely to poll a mailbox, and nothing here
polls one.

When a reply arrives it is **frozen verbatim first** — sender, received time,
thread, a pointer to the dispatch it answers — and reviewed in a mission of its
own, because a provider's words and this project's reading of them must stay
distinguishable. That review is what could move B2, the datascan port set and the
post-30-day retention question, and only after somebody has read it.

**Mission 1.67 was not started.**
