# Mission 1.74.2 — The second enquiry approved, and the ceiling that comes with it

**Outcome: `R2_DISPATCH_APPROVED_AWAITING_MANUAL_OPERATOR_ACTION`.** The operator
approved dispatch of **GP-R2-Q1** by `OPERATOR_MANUAL_EMAIL` to `legal@globalping.io`.
This repository sent nothing, used no connector and searched no mailbox.

---

## 0. What the operator approved

| | |
|---|---|
| enquiry | `GP-R2-Q1` |
| mechanism | `OPERATOR_MANUAL_EMAIL` |
| channel | `PROVIDER_DESIGNATED_TERMS_CHANNEL` |
| recipient | `legal@globalping.io` — the address the Terms designate in §16 |
| subject | Terms scope: HEAD measurements of publicly reachable third-party websites |
| sender | `PLACEHOLDER_PERMITTED_FOR_MANUAL_SEND_ONLY` |
| maximum sends | **1** |

## 1. The rules invert against Mission 1.74.1, and that is the finding

```
R1  public GitHub issue   every field pinned      BYTE_VERIFIED reachable
R2  manual email          sender NOT pinned       BYTE_VERIFIED unreachable
```

**Both differences are properties of the CHANNEL**, not of manual sending, and that is
why this is a separate gate rather than the same one pointed at another file. A gate
that accepted the same evidence for both would be asserting something false about one
of them.

### Three fields of four, and the cost was stated in advance

Mission 1.65 wrote it down before anyone knew whether it would matter: under a manual
mail send **the sender genuinely is not determined until the send**, so the hash pins
three fields of four. Mission 1.66.1 then paid exactly that cost — the ONYPHE send
matched on recipient, channel and subject, and the sender matched nothing, admitted
under `ALLOWED_BY_APPROVED_PLACEHOLDER`.

Mission 1.74.1 escaped it, because a public repository and a GitHub identity are
determined before the act. **Here it recurs.** Pinning the fourth field would produce a
different approval that supersedes this one rather than editing it — and the validator
refuses a real mailbox in the sender field for exactly that reason.

### `BYTE_VERIFIED` is unreachable, and the record says so rather than implying a path

Mission 1.74.1 could reach it because a public issue has a durable public URL. **A mail
client's outbox is something no guard here can observe**, which is what Mission 1.66
established. So the honest maximum for this channel is `OPERATOR_ATTESTED`, the reachable
set is exactly that one level, and the upgrade path reads **NONE**.

Importing a sent-message artifact from the operator's own mailbox was considered and
refused, on Mission 1.66's reasoning: it would replace an attestation with an inference
and require an access nobody requested.

**This gate therefore REFUSES `BYTE_VERIFIED`, where the R1 gate requires that it be
possible.** A test asserts the two gates disagree on that field, because if they ever
agreed one of them would be wrong.

## 2. The connector was available throughout and was not used

There is a mail connector in this runtime. One call would have produced matching text, a
matching recipient and a verifying content hash — **and a different action**, because the
channel is one of the bound fields and the sender would be a mailbox the operator never
named. Mission 1.66 identified this as the quiet way an approval gets exceeded; the
record names it, the accounting counts zero, and the validator refuses a record that
admits it.

**A connector present in the runtime is still not channel authorisation.**

## 3. Two approvals, and they are not one

Each names its own enquiry, its own mechanism and its own recipient, and each authorises
exactly one act. Neither may be used to justify the other.

The R1 approval's **binding fields are untouched and its digest still recomputes**. It
gained exactly one appended field: a forward pointer naming this record, which is the
Mission 1.66.1 shape — the stale-record hazard closed by appending rather than by editing
what an earlier record established. Its scope block still says *this approval does not
cover R2*, which remains true.

Because the packets are never edited, **the R1 gate stayed green throughout**: its check
that the R2 packet still reads `NOT_AUTHORIZED` is a check that the packet was not
edited, and the discipline is what keeps it valid.

## 4. An approval to ask is not an answer

R2's verdict is unchanged at
`R2_PARTIAL_COMMERCIAL_ALLOWED_THIRD_PARTY_SCOPE_UNRESOLVED`, no residual closed, the
qualification was not recomputed, and the tally is still 10 PASS / 2 PARTIAL / 0 FAIL
with `COUNTERPART_UNRESOLVED`. Mission 1.74's closure still reads `enquiries_sent: 0`
and `residuals_remaining: 2` — true when it ran, and still true.

## 5. Nothing moved

| | |
|---|---|
| emails sent, mail connector executions, mailbox searches | 0 |
| public posts, GitHub issues, `gh` invocations | 0 |
| provider contacts, enquiries sent | 0 |
| Globalping API executions, measurements, target HTTP requests | 0 |
| accounts, tokens, credential reads, documentation requests | 0 |
| sources registered, canonical mutations, Claims, Evidence, scores | 0 |
| model calls, embeddings, migrations | 0 |

ONYPHE still `NOT_CHECKED_AFTER_DISPATCH`, Netlas still pending, the scanner arc still
parked, ADR-039 untouched.

## 6. Verification

- Gate probed with **108 deliberate violations, 108 caught** — 104 by rule, 4 by drift —
  **0 escaped**, plus **4 of 4 positive controls**.
- **One control's name claimed more than it tested and was corrected rather than kept.**
  It was called a pinned-sender supersession and never pinned the sender — which this
  gate must refuse outright, since a pinned sender belongs in `hash_covers` and would be a
  different approval. Renamed to what it proves: an approval superseded before any send.
  Mission 1.65's rule applied to a probe's own honesty rather than to a record's.
- **A missing field is a refusal, not a crash**, carried forward from Mission 1.74.1 and
  proved again with five cases.
- **The R1 gate was re-run after the forward pointer was appended** and stays green, with
  its `approval_sha256` unchanged.
- **58 new tests**; **2853 bare-python tests**; both test runners green; `ruff format --check`, `ruff check` and mypy
  all through `uv`; all **46** CI gates.

## 7. Next

**Two acts now wait on a person, and neither belongs to this repository.**

- Send **one** email to `legal@globalping.io` with the approved subject and the frozen
  body, from whichever mailbox you choose — the placeholder permits it, and the sender is
  recorded afterwards rather than pinned in advance.
- Post **one** public issue on `jsdelivr/globalping` for R1.
- Then attest to each. R1 can additionally reach `BYTE_VERIFIED` with its issue URL;
  **R2 cannot, and no later mission may claim otherwise.**

**Mission 1.75 was not started.**
