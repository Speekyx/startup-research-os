# Mission 1.85.17 report: the single-human adjudicated reference is recorded (N08-B-PILOT)

**Outcome: `SINGLE_HUMAN_ADJUDICATED_REFERENCE_RECORDED`.**

operator-a reread all 46 EGRESS_APPROVED DEVELOPMENT records under `single-operator-adjudication-protocol@1.1.0`,
then adjudicated every cell whose readings differed or were UNCERTAIN. The reference is committed and labelled
for what it is.

    reference         SINGLE_HUMAN_ADJUDICATED_REFERENCE: not consensus, not inter-human, not blind, not certification
    original          blind annotation 449ff10f... unchanged; it remains the reference every earlier reading used
    provider calls    0      model inferences 0      HOLDOUT records 0      canonical writes 0

## 1. The reread

`stack-overflow-semantic-reread-development-operator-a-v1.json`: protocol 1.1.0, `NO_MANDATORY_DELAY`, started
2026-09-19T11:23:36+04:00 and completed 15:17:39. It is not blind to model output (the attestation says so), and
it is not a second annotator.

Intra-rater agreement, original blind label against reread, over one person and 46 records:

| Label | Raw agreement | Cohen's kappa | Main shift |
|---|---|---|---|
| REPORTED_FAILED_ATTEMPT | 0.478 | 0.113 | 19 ABSENT -> PRESENT, 3 PRESENT -> ABSENT, 2 UNCERTAIN -> PRESENT |
| NEGATIVE_EVALUATION_OF_NAMED_SOLUTION | 0.674 | 0.043 | 14 ABSENT -> PRESENT, 1 UNCERTAIN -> PRESENT |

The reread reads PRESENT far more often. That matches the direction of the Mission 1.85.13 post-model review, where
the operator revised 9 of 9 new disagreements to PRESENT. **Why cannot be separated here.** The reread followed
exposure to the model and to those reviews, so the blind annotation may have been too strict, or the model may
have shaped the reread. Both are possible, and this is one person's consistency, never reliability.

## 2. The adjudication

39 cells were queued:
- 24 REPORTED_FAILED_ATTEMPT, of which 2 were UNCERTAIN;
- 15 NEGATIVE_EVALUATION, of which 1 was UNCERTAIN.

| Final state matches | REPORTED_FAILED_ATTEMPT | NEGATIVE_EVALUATION |
|---|---|---|
| the reread | 21 | 15 |
| the original blind label | 3 | 0 |

No cell was left UNCERTAIN. Each decision states a reason and is bound to the readings it was made on.

## 3. The reference

`stack-overflow-semantic-single-human-adjudicated-reference-development-v1.json` (and its `.md` page), 46 records,
two labels:

| Label | Original blind | Adjudicated |
|---|---|---|
| REPORTED_FAILED_ATTEMPT | 15 PRESENT / 29 ABSENT / 2 UNCERTAIN | 36 PRESENT / 10 ABSENT / 0 UNCERTAIN |
| NEGATIVE_EVALUATION_OF_NAMED_SOLUTION | 0 PRESENT / 45 ABSENT / 1 UNCERTAIN | 15 PRESENT / 31 ABSENT / 0 UNCERTAIN |

**NEGATIVE_EVALUATION now has positive-class support (15)**, where the blind annotation had none. The contract's
composition floor of 4 PRESENT is met on this reference. Since it is one person's adjudication, that says nothing
about how reliably the label is read.

No evaluation was re-run against this reference. Every Mission 1.85.9 and 1.85.12 reading stays as recorded
against the blind annotation. Whether any future reading uses the adjudicated reference is an operator decision
for a later mission, and it must name the reference strength.

## 4. A defect found before commit: reasons can quote the source

Before committing, each adjudication reason was compared with the source text, without printing either. 4 of the
39 reasons contain 30 or more characters verbatim from the Stack Overflow question, and one is a 136-character
quotation. The Mission 1.85.15 design committed reasons as text. Committing these would have put source text in
the repository.

**Fix.** `committed_adjudication` keeps a reason as `operator_note_sha256` and `operator_note_length` only; the
full text stays in the local working file (`%TEMP%\sros-adjudication`). The fix is idempotent, so `check`
re-renders committed decisions unchanged. A test asserts that no `operator_note` text reaches the committed
reference. The reference was regenerated from the unchanged working file; no decision changed.

**The earlier post-model reviews were checked the same way**: at most 28 characters overlap in the Mission
1.85.13 review and 0 in Mission 1.85.10, which is incidental wording and not quotation. They are unchanged.

## 5. What was not done

No prompt, extraction contract, label definition, threshold, packet or approval changed. No provider call, no
rerun, no HOLDOUT, no Signal, Claim, Evidence or Opportunity. N08-C was not started. The original blind
annotation, both reviews and packet v5 are byte for byte unchanged.

## 6. Next

An operator decision, not a run. Two options:
- **re-evaluate the existing prompt 1.1.0 outputs** against this reference offline, reported as
  SINGLE_HUMAN_ADJUDICATED and alongside, never instead of, the blind-reference readings;
- **leave the pilot readings as they are.**

A new prompt or packet should wait until that choice is made, because the blind reference and the adjudicated one
now disagree on 36 of 92 cells.
