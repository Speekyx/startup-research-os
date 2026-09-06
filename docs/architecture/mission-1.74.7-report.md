# Mission 1.74.7 — The provider answered, and R1 closed

**Outcome: `R1_CLOSED_PROVIDER_DECLARED_RIGHTS_SCOPE_REMAINS`.** An organisation member
answered the exact frozen question on the provider's own issue tracker. R1 moves to
`R1_PASS_PROVIDER_DECLARED_NO_REDIRECT`, C6 to `PASS`, and the tally from 10/2/0 to
**11 PASS / 1 PARTIAL / 0 FAIL**. **The counterpart is still not qualified.**

---

## 0. What arrived

| | |
|---|---|
| repository | `jsdelivr/globalping` |
| issue | [#907](https://github.com/jsdelivr/globalping/issues/907) |
| comment | [#issuecomment-5559554359](https://github.com/jsdelivr/globalping/issues/907#issuecomment-5559554359) |
| author | `jimaek`, `author_association: MEMBER` |
| posted at | `2026-09-06T13:32:15Z` |
| retrieval | `RAW_GITHUB_REST_API_READ` |
| reply digest | `a73b60fd64c1061e…` |

## 1. Frozen before it was read

The reply lives in `globalping-r1-provider-reply-v1.json`, which declares itself a source,
carries `contains_interpretation: false`, and holds no verdict and no evidence level. The
reasoning lives in `globalping-r1-reply-review-v1.json`, which cites the source **by hash**
and never restates its text.

That split is not ceremony. A single document holding both the evidence and the conclusion
can adjust the first to suit the second, and nothing in it would show the adjustment. The
gate refuses the interpretation being written into the source, refuses the review restating
the reply, and refuses either naming a digest the other does not hold.

## 2. A supplied string is a claim

The instruction quoted the reply. The stored comment differs from that quotation by **one
trailing space**.

It changes no meaning, and that is exactly why it is recorded. A record that adopted the
quotation silently here would have adopted it just as silently somewhere it mattered. The
frozen text is the stored bytes; the quotation is kept beside it, with the difference named.

## 3. Both halves, examined separately

> the redirect response is returned — `ESTABLISHED`
> the redirect is not followed — `ESTABLISHED`

The second clause is explicit and needs no help. The first is anaphoric: read alone, "the
response" could denote the final response after a redirect had been followed.

**The second clause forecloses that reading.** If the redirect is not followed there is no
post-redirect response for the phrase to denote, so the referent is forced rather than
chosen — the reading does not depend on charity toward the answer. The two clauses settle
each other, and the review records the weakness before recording why it does not survive.

## 4. A solicited answer is not a statement somebody found

Mission 1.74 refused to upgrade on an incidental maintainer remark in an issue about output
formatting. **That refusal is untouched**, and the guard enforcing it is byte-identical: no
entry in `provider_statements_found` may carry a closing level.

What closed R1 is a different kind of thing, and it lives in its own block. The new level,
`R1_A2_SOLICITED_RESPONSIVE_PROVIDER_ANSWER`, is defined by five conditions the gate checks
one at a time — **solicited**, **responsive to the exact predicate**, **attributable to the
provider**, **durable and citable**, **retrieved without a summarising extraction**. Failing
any one drops it back to the incidental level.

Adding a closing level is the move most open to motivated reasoning here, so the
justification is a condition **written before the answer existed**. Mission 1.74's own
review recorded what would close R1:

> one documented sentence, or one answer through the provider's technical channel

The channel was established first-party in the same mission and the enquiry was addressed to
it. The condition was set in advance and it is met.

## 5. Declared, not documented

The frozen discriminator named `R1_PASS_DOCUMENTED_NO_REDIRECT`. The verdict recorded is
`R1_PASS_PROVIDER_DECLARED_NO_REDIRECT`.

The **decision** is honoured exactly: the discriminator said an answer naming "the initial
3xx is returned" maps to PASS, and it does. The **label** is narrowed, because the
specification still contains zero occurrences of "redirect" and calling this DOCUMENTED
would claim a surface that does not exist. The gate now refuses the DOCUMENTED verdict
whenever no reviewed surface documents the behaviour.

**What stays open at PASS is written into the record**: the behaviour is declared and not
specified, so a future change would contradict no published document and this verdict would
not detect it. Asking the provider to document it is a separate act and was not performed.

## 6. The tally moved and the verdict did not

| | before | after |
|---|---|---|
| R1 | `R1_PARTIAL_IMPLEMENTATION_ONLY` | `R1_PASS_PROVIDER_DECLARED_NO_REDIRECT` |
| C6 | `PARTIAL` | **`PASS`** |
| C9 | `PARTIAL` | `PARTIAL` |
| tally | 10 / 2 / 0 | **11 / 1 / 0** |
| verdict | `COUNTERPART_UNRESOLVED` | `COUNTERPART_UNRESOLVED` |

Qualification needs all twelve mandatory dimensions PASS. **A better tally is not a
verdict.** No quantity class was selected, no construct created, no independence group
exists, and Q1 is still not viable — a closed residual removes a reason not to proceed and
supplies no reason to proceed.

Four records were **superseded, never edited**: the redirect review, the closure, the
qualification and the decision. Each gained one appended forward pointer, and the gate
asserts live that the predecessors still read 10/2/0, two residuals remaining, and
`R1_PARTIAL_IMPLEMENTATION_ONLY` — so a later edit that backdated this closure into Mission
1.74 fails here.

## 7. Two defects surfaced by the first legitimate transition

**The R1 dispatch could never have reached `BYTE_VERIFIED`.** Mission 1.74.1 defined the
upgrade as a raw read of the issue body; Mission 1.74.3's gate refused **every** GitHub API
call by this repository. The gate demanded a comparison and forbade the only mechanism that
produces one. The counter is now split: the **write** half keeps the refusal at zero, and
the **read** half is not merely permitted but **required to be at least one whenever
`raw_body_compared` is true** — a comparison with no read compared nothing. Value preserved,
name and comparison changed, exactly as in 1.74.3.

With that resolved, the read this mission needed anyway performed the comparison:
`posted_body_sha256` equals the `approved_body_sha256` recorded **before** the post, the
title matches character for character, and R1's dispatch reaches `BYTE_VERIFIED`. The
paragraph break that Mission 1.74.3 suspected was a conversion artifact **was** one — it
suspected correctly and refused the upgrade anyway, which is what made the refusal worth
anything.

**The closure record asserted things that had become false.** Its gate pinned
`enquiries_sent == 0`, `operator_approval_recorded` false and `provider_contacted` false —
constants from a mission where nothing had been sent. They are now live cross-checks against
the dispatch records, which is strictly stronger: the closure record can no longer say
anything about dispatch that the dispatch records do not already say. `provider_contacted`
is true **for R1 only**, on a reply that demonstrates receipt, and the gate refuses it
overruling R2's own record, which still reads false.

## 8. Bounded to R1

R2 was not examined, its dispatch state was not altered, no reply to it is claimed, no
measurement was run, no target was requested, no class or construct was selected, and no
independence group was created. A reply about redirects establishes nothing about Terms
scope, and the two questions went to different channels for that reason.

## 9. Verification

- Gates probed with **95 deliberate violations, 95 caught** — 92 by rule, 3 by drift —
  **0 escaped**, plus **4 of 4 positive controls**.
- **One escape was found and closed.** Deleting the solicited-answer block raised a bare
  `KeyError` rather than a refusal, so the residuals gate now converts a missing field
  into a refusal the way the dispatch gates already did.
- **13 of the new module's 43 tests run the gate's own checks against mutated records**
  rather than reading its source — including one per condition of the new evidence level,
  because a five-condition rule that is only checked as a block is a one-condition rule.
- **The controls are the point**: a future documented sentence must still close R1 the
  ORIGINAL way, and R1 must still be representable back at `OPERATOR_ATTESTED` with no
  comparison — a gate that only accepts the state we happen to be in is not a gate.
- **One case matters most**: the incidental statement from Mission 1.74 **still** cannot be
  graded as closing. Adding a closing level must not have widened the old guard, and both a
  probe case and a test mutate that record specifically to prove it.
- **3029 bare-python tests**; both runners green; `ruff format --check`, `ruff check` and mypy
  through `uv`; all **48** CI gates, **no new gate** — the gates that govern these records
  already existed and were extended.

## 10. Next

**R2 is the only residual left**, and its email is an attested dispatch with an unconfirmed
delivery. If a reply arrives it is frozen verbatim before anything interprets it, exactly as
this one was. If a non-delivery report arrives instead, that dispatch moves to `FAILED` and
a third recipient would need its own review and approval.

Documenting the redirect behaviour would still be an improvement over a declaration, and
asking for it would be a new enquiry needing its own approval.

**Mission 1.75 was not started.**
