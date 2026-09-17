# Mission 1.85.13 report: balanced post-model review of the prompt 1.1.0 disagreements (N08-B-PILOT)

**Outcome: `WAITING_FOR_PROMPT_1_1_BALANCED_OPERATOR_REVIEW`.**

The prompt 1.1.0 run disagreed with the blind reference in two directions, and only one of them had ever been
reviewed. This mission prepares a review of **both**, corrects a counting error in the Mission 1.85.12 report,
and stops. The operator has not reviewed anything yet.

    review set     9 never-reviewed false PRESENT + 6 false negative = 15 records
    reused         7 Mission 1.85.10 judgements, unchanged and not re-asked
    model calls    0      reruns 0      HOLDOUT records 0      canonical writes 0

No model was called, no packet was created, no approval exists, the prompt was not revised, the label
definition was not revised, and the blind annotation was not touched.

## 1. Phase A: history verified

Recomputed, not quoted:

| Artifact | Result |
|---|---|
| Mission 1.85.9 evaluation (`--check`) | reproduces |
| Mission 1.85.10 post-model review (`check`) | reproduces, status COMPLETE |
| Mission 1.85.12 evaluation and prompt-revision diagnostics (`--check`) | reproduce |
| Packet v5 renderer and RFA regression spec (`--check`) | current |
| Prompt 1.0.0 `53bcc87f...` / prompt 1.1.0 `a4b96eb3...` | unchanged |
| Blind annotation `449ff10f...` | byte-for-byte unchanged |
| Approval v2 `9fc8fac7...` | spent by its attempt record |
| Provider executions since Mission 1.85.12 | 0 (2 attempt records, 2 run summaries, 46 calls in the v2 run) |

Nothing historical was modified.

## 2. Phase B and C: the counting error, and what is true

**The Mission 1.85.12 report said**: of the 16 current false PRESENT, "the operator confirmed 9 of them in
Mission 1.85.10; the other 7 are unreviewed."

**That subtracts a count instead of intersecting sets.** Mission 1.85.10 reviewed 9 records; prompt 1.1.0
**corrected two of them** (`ac423fe4`, `d6bff833`), which therefore left the false-PRESENT set. So:

    CURRENT_FALSE_PRESENT                          = 16
      previously reviewed and STILL false PRESENT  =  7
      never reviewed                               =  9
    CURRENT_FALSE_NEGATIVE                         =  6
    BALANCED_REVIEW_SET                            = 15

The distinction that was lost: **records that were historically reviewed** is not the same set as **records
that were historically reviewed and are still disagreements in the current run**.

Everything else in Mission 1.85.12 stands: 16 false PRESENT, 9 true PRESENT, recall 0.60, upper 0.798,
`PILOT_OUTSIDE_PROPOSED_BOUND`, and the packet, run and evaluation artifacts. **Its evaluation was not
rewritten.** The correction is an erratum at the end of `docs/reports/mission-1.85.12-report.md`, plus the two
interpretation sentences that carried the wrong count.

A regression test refuses the shortcut: `test_subtracting_the_historical_review_count_is_not_the_intersection`
asserts that 16 − 9 = 7 is **not** the answer, that the intersection is 7 and the never-reviewed set is 9, and
that exactly 2 reviewed records left the set.

## 3. Phase B: the sets, derived mechanically

Derived from the blind annotation, the Mission 1.85.12 run summary and its evaluation, using the frozen
evaluator's own `model_call`, then checked against the committed evaluation's disagreement lists. Nothing was
typed by hand.

### The nine never-reviewed false PRESENT (reference ABSENT, model PRESENT)

| # | Record |
|---|---|
| 1 | `3194f76d-a845-54c5-9a14-bd0520da6cbb` |
| 2 | `3d0568c4-5876-5863-921b-2c0fc3d3e27a` |
| 3 | `42642469-23b7-5a7a-b897-5052012d9fd3` |
| 4 | `58966c7e-425d-59de-85ce-116ae98309ab` |
| 5 | `6dfbef0a-3a64-5fd1-9433-21f7cdb01402` |
| 6 | `7eed79ff-81d0-50c1-94c2-3a1b6fa3b4a8` |
| 7 | `88376fa5-5cd3-58f9-b099-bad69077b0f7` |
| 8 | `c128f807-cbdf-512b-bbde-30a00a9fdb39` |
| 9 | `f53c6872-b340-5e5b-845c-e8b2bd3147d8` |

`3d0568c4` is the record whose call stalled in Mission 1.85.9, so prompt 1.0.0 never answered it.

### The six false negatives (reference PRESENT, model ABSENT)

| # | Record |
|---|---|
| 1 | `4a3fc738-bb4a-5992-bb2e-2e422b9f4a00` |
| 2 | `96054702-3d78-55b0-b5b9-ed63e611c6d7` |
| 3 | `b7996f9d-72fe-5544-a30a-ce9270edfe09` |
| 4 | `e2162aae-f496-58d4-b905-73e4b0164a66` |
| 5 | `e9edbbaa-5331-5584-8d3e-847c8f759551` |
| 6 | `f876b0be-fa18-5b60-9fdd-b505e7529413` |

Five of these six were PRESENT under prompt 1.0.0 and became ABSENT under 1.1.0; the sixth
(`e2162aae`) was never attempted in the partial Mission 1.85.9 run.

**No record appears on both sides**, and no other record is reviewable: the tool derives the set and the
working file refuses a decision for anything else.

## 4. Phase D and E: the review, and why it is balanced

Mission 1.85.10 asked one question: did the model over-read? Asking only that again would ask the operator
about half the problem while the other half — 6 reference positives the model now misses — went unexamined,
and the answer would read as though prompt 1.1.0 only had a precision problem.

So the review has two sides, each with its own choices, because "the model over-read" and "the model
under-read" are different judgements:

| Side | Shown | Choices |
|---|---|---|
| `NEW_FALSE_PRESENT` (9) | frozen surface, blind ABSENT, model PRESENT, the model's accepted quotes rebuilt from offsets and digest-verified, the frozen label definition and the prompt 1.1.0 three-anchor rule | `HUMAN_REFERENCE_CONFIRMED_MODEL_OVERREAD`, `POST_MODEL_HUMAN_REVISION_TO_PRESENT`, `LABEL_DEFINITION_AMBIGUOUS`, `UNRESOLVED` |
| `FALSE_NEGATIVE` (6) | frozen surface, blind PRESENT with the operator's **own evidence span** rebuilt and digest-verified, the model's `NO_FINDING_ESTABLISHED` answer, the same frozen definitions | `HUMAN_REFERENCE_CONFIRMED_MODEL_UNDERREAD`, `POST_MODEL_HUMAN_REVISION_TO_ABSENT`, `LABEL_DEFINITION_AMBIGUOUS`, `UNRESOLVED` |

- **No default and no bulk path.** A blank working file holds zero decisions, the page preselects nothing, and
  `/api/decide_all`, `/api/bulk` and `/api/accept_all` do not exist.
- **A choice from the wrong side is refused** (`CHOICE_NOT_AVAILABLE_ON_THIS_SIDE`).
- **A note is required** for either revision and for ambiguity, and a note that pastes 40 consecutive
  characters of the question is refused.
- **Loopback only**: `127.0.0.1`, a Host check, a per-session token, a strict CSP, no external asset, no
  telemetry, nothing logged. The material with the exact surfaces is written **outside the repository**.

### The seven prior judgements are reused, never re-asked

The 7 records Mission 1.85.10 already judged `HUMAN_REFERENCE_CONFIRMED_MODEL_OVERREAD` are recorded as
`PRIOR_REVIEW_REUSED_RECORD_LEVEL_JUDGEMENT`, with the original decision, operator and timestamp. They are not
in the review set, no new timestamp is invented for them, and the Mission 1.85.10 artifact is untouched. The
binding they rest on is unchanged: same frozen surface, same blind reference, same label definition. New
decisions carry `MISSION_1_85_13_NEW_REVIEW`, and the two origins are distinguished everywhere they are
counted.

### Provenance

Every new decision is `POST_MODEL_OPERATOR_REVIEW` with `blind = false`. It never replaces or edits the blind
reference, and a blind attestation key (`no_model_output_seen`, `attestation`, `reference_origin`, …) is
refused outright. Each decision is bound to the packet v5 digest, the approval v2 digest, the run summary and
evaluation digests, the prompt 1.1.0 digest, the label-definition digest, the blind annotation digest, the
Mission 1.85.10 review digest, the record's surface digest, and the model output digest. A changed binding
makes the review `STALE` rather than carrying it forward.

The model output digest covers the **whole accepted extraction**, not just this label's findings: a false
negative has no `REPORTED_FAILED_ATTEMPT` finding at all, so binding to an empty list would let a changed
answer pass unnoticed.

## 5. Phase F and G: what happens once the operator finishes

Nothing is computed until all 15 records carry a choice and none is `UNRESOLVED`. Then the tool writes, per
side, the counts of confirmations, revisions, ambiguity and unresolved, plus a combined record-level
diagnostic: the 16 current false PRESENT split into 7 prior-reviewed persistent cases and 9 newly reviewed
ones with their outcomes, and the 6 false negatives with theirs. It is labelled post-hoc and not
preregistered, and it **does not rewrite any Mission 1.85.12 metric**.

Recommendations are derived mechanically from a rule frozen before any decision exists, and **none is acted
on**:

| Condition | Recommendation |
|---|---|
| confirmed over-reads dominant (≥ half the resolved decisions on that side) | `RFA_PRECISION_REMAINS_MODEL_OR_EXTRACTION_CONTRACT_PROBLEM` |
| confirmed under-reads dominant | `RFA_PROMPT_1_1_OVERCONSTRAINS_TRUE_POSITIVES` |
| both strong (≥ two thirds, and ≥ 2 each) | `PROMPT_ONLY_REVISION_INSUFFICIENT_CONSIDER_STRUCTURED_EXTRACTION_CONTRACT` |
| revisions ≥ a third of the 15 | `REFERENCE_REVIEW_OR_ADJUDICATION_REQUIRED` |
| ambiguity ≥ a third of the 15 | `LABEL_DEFINITION_DECISION_REQUIRED` |

Several may apply at once. No prompt 1.2.0 is prepared, and no contract is changed.

## 6. Design option: structured anchor extraction

**This is a design note for the operator, not an implementation.** It becomes the live question only if the
completed review confirms both persistent false positives and genuine false negatives.

Today the contract is direct:

    question surface  ->  model  ->  REPORTED_FAILED_ATTEMPT PRESENT/ABSENT + one evidence quote

The label's own definition is a **conjunction**: an attempt, its failure, and a link between them. Prompt 1.1.0
stated that conjunction in words and asked the model to apply it internally; the model still returns a single
verdict, and nothing can check which part of the conjunction it thought it had.

A structured alternative would ask for the parts and validate the conjunction outside the model:

    surface -> model -> { attempt_quote, failure_quote, link_quote_or_relation }
            -> deterministic validation: every anchor is present in the surface, the anchors are distinct,
               and the relation is expressed in the asker's own words
            -> only then may an RFA finding exist

What it could buy:
- **an over-read becomes visible as a missing anchor** rather than as a disputed verdict, so a precision
  failure is mechanically detectable rather than a matter of opinion;
- **an under-read becomes inspectable**: a record with an attempt and a failure but no link is a different
  failure from one with no attempt at all, and the current contract cannot tell them apart;
- the validator, which already refuses quotes that are not in the surface, would gain something to check.

What it costs, stated honestly:
- a schema change, a new tool version, a new prompt, a new packet and a new approval;
- more output tokens per record and probably more validator refusals at first;
- **it does not settle a disagreement about meaning.** If the human and the model disagree about whether a
  sentence reports an attempt at all, structured anchors relocate that disagreement into the attempt anchor
  rather than resolving it;
- a conjunction enforced deterministically can only reduce PRESENT calls, so it would need the recall question
  answered first.

**Nothing here is implemented, no schema is versioned, and this is not a recommendation.**

## 7. Repeatability

**Not measured, not authorised, and not started.** No execution packet exists and none was created.

Whether it is decision-relevant:
- **It would matter** for judging small movements. Two of the nine over-reads were corrected and two of the six
  false negatives sit close to the anchors; a difference of one or two records cannot be separated from
  run-to-run variance without a second run.
- **It would not explain the finding.** 16 false PRESENT of 25 PRESENT calls, and 6 of 15 reference positives
  missed, are systematic, not marginal. **Variance may explain a few records; it must not be used to dismiss a
  precision and recall problem of this size without evidence.**
- Measuring it costs a new packet digest, a new approval and one more full run at about $0.44. That is the
  operator's decision, and this mission does not ask for it.

## 8. Engineering debt, recorded and not fixed

**A. Validator refusal (Mission 1.85.12).** One record, `db663e12`, was refused `QUOTE_NOT_IN_SURFACE`: the
model returned three `REPORTED_FAILED_ATTEMPT` findings and at least one quote was not in the frozen surface.
Its blind reference is UNCERTAIN, so it is not part of the RFA disagreement analysis and is **deliberately not
mixed into it**. It is an engineering question about the model's quoting, and the retry policy correctly did
not retry a validator refusal. Not fixed here; the review tooling does not depend on it.

**B. Packet v5 metadata path.** `operator_decisions.package` names the v1 decision-package filename while
`package_sha256` is the v2 package's digest. Packet v5 is historical and spent, so it is **not mutated**. The
defect is in a hard-coded string in `render_semantic_extraction_packet.py`. Before any packet v6 is approved,
the renderer must be fixed in a way that keeps packet v5 reproducible, which means the fix has to be scoped to
the new packet's rendering rather than applied retroactively.

## 9. Proof of the boundaries

| Counter | Value |
|---|---|
| Provider calls, model inferences | 0 |
| Stack Overflow text egress | 0 (review material stays outside the repository; committed artifacts carry ids, digests and counts only) |
| Reruns, execution packets, approvals | 0 |
| HOLDOUT records opened | 0 |
| New AI annotations | 0 |
| Signals, Claims, Evidence, Opportunities, scores, canonical writes | 0 |
| Prompt, label definition or blind annotation changes | 0 |
| N08-C work | 0 |

A test parses the review script and the contract module and asserts neither imports a provider, a gateway, a
socket or an HTTP client, that neither mentions `--execute`, and that a full review flow builds no transport.

## 10. Tests and CI

`test_balanced_post_model_review.py` (19 tests):
- Mission 1.85.9, 1.85.10 and 1.85.12 artifacts all reproduce, and the blind reference digest is unchanged;
- the sets derive as 16 / 6 / 7 / 9 / 15, with the exact ids;
- the subtraction shortcut is refused by name;
- no record is on both sides, and no other record is reviewable;
- no default, no bulk path, and a cross-side choice is refused;
- a click is bound to the surface and model output it was shown, and survives a restart;
- a note quoting the question is refused;
- post-model provenance cannot masquerade as blind, and a forged review origin is refused;
- stale bindings and a moved surface make the review `STALE`;
- an incomplete review derives no recommendations and no combined diagnostic;
- the frozen recommendation rule, on synthetic complete reviews;
- a complete committed review reproduces, leaks no text, and a tampered decision fails `check`;
- no provider client on the review path, and the whole flow builds no transport.

New CI step: `Semantic extraction balanced post-model review is current` (artifacts only; no database, no
provider).

## 11. What the operator does next

One command opens the review page, after preparing the material outside the repository:

```bash
uv run python infrastructure/scripts/balanced_disagreement_review.py serve "$env:TEMP/sros-balanced-review"
```

If the material is not prepared yet, prepare it first (it reads the held surfaces, so `DATABASE_URL` must be
set):

```bash
uv run python infrastructure/scripts/balanced_disagreement_review.py prepare --out "$env:TEMP/sros-balanced-review" --operator-id operator-a
```

Then review all 15 records, and import the result:

```bash
uv run python infrastructure/scripts/balanced_disagreement_review.py import "$env:TEMP/sros-balanced-review/balanced-review-working-operator-a.json"
```

**N08 is not DONE. N08-C was not started.** The next architectural decision — prompt, extraction contract, label
definition or repeatability — comes only after this balanced human review.
