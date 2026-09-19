# Mission 1.85.15 report: single-operator adjudication protocol (N08-B-PILOT)

**Outcome: `WAITING_FOR_SINGLE_OPERATOR_DELAYED_REREAD`.**

> **Superseded in part by Mission 1.85.16.** `single-operator-adjudication-protocol@1.1.0` supersedes the
> mandatory 24-hour delay of 1.0.0 for future rereads, by the operator's decision recorded in
> `docs/reports/mission-1.85.16-report.md`. Everything else below still holds. This report describes 1.0.0 as it
> was, and the delay it required is not rewritten away.

Mission 1.85.14 prepared a second blind annotation for operator-b, a different person who has seen neither the
model nor operator-a's labels. The operator confirmed that no such person exists. The operator cannot fill that
role: they have seen their own blind labels, the model's outputs and both post-model reviews, and the importer
requires the blind attestation to be literally true.

The operator chose single-operator adjudication. This mission builds that protocol and names its output for what
it is.

    protocol          single-operator-adjudication-protocol@1.0.0
    output            SINGLE_HUMAN_ADJUDICATED_REFERENCE
    is                one person's adjudicated reading, built from a blind reading, a delayed reread and reviews
    is not            consensus, inter-human reliability, blind, certification, a replacement of the original
    provider calls    0      model inferences 0      HOLDOUT records 0      canonical writes 0

No prompt, contract, packet, approval or repeatability run was created. N08-C was not started. The operator-b
tooling from Mission 1.85.14 stays in place for a genuine second person.

## 1. What cannot be built, and what can

A second blind reading needs a reader who has not seen the answers. None is available, so **inter-human
agreement cannot be measured**, and nothing in this mission reports it.

What can be built is narrower and still useful:

1. **A delayed reread.** The operator labels the two extractable labels again with the previous labels hidden.
   It is blind to the earlier labels at the time of reading. It is **not** blind to model output, and the record
   says so.
2. **An adjudication.** Only where the readings disagree, or one of them is UNCERTAIN, the operator sees every
   reading and decides a final state with a reason.
3. **A labelled reference.** A new file, beside the original blind annotation, never in place of it.

## 2. Step 1: the delayed reread

| Property | Value |
|---|---|
| Records | all 46 EGRESS_APPROVED DEVELOPMENT records, not only the contested ones |
| Labels | REPORTED_FAILED_ATTEMPT and NEGATIVE_EVALUATION_OF_NAMED_SOLUTION only |
| Order | a fresh deterministic shuffle (`operator-a-delayed-reread`), different from the original order |
| Shown | the frozen surface and the original questions for those two labels |
| Hidden | the operator's earlier labels, spans and notes; the reviews; the model's answers |
| Earliest start | **2026-09-19T23:57:02+04:00**, 24 h after the last post-model decision |

**Why all 46.** Rereading only the contested records would tell the reader which ones were contested.

**Why a delay.** The operator's last exposure to model output on these records is the last post-model decision
(2026-09-18T23:57:02+04:00). A reread started the same evening would mostly recall that session. The delay is
derived from the committed reviews, not typed in. The `reread` command refuses to ask anything before it, and the
importer refuses a pack whose start time is earlier.

**The attestation discloses rather than claims.** Four flags, in French, each answered explicitly:
- previous labels and reviews not consulted during the reread;
- no AI assistance used;
- answers given from the displayed text only;
- **prior model exposure acknowledged.** This one is a disclosure, and it must be true.

The importer refuses the blind attestation keys (`no_model_output_seen`, `did_not_see_other_annotators_labels`).
The committed reread carries `blind_to_model_outputs: false` and `is_a_second_annotator: false`.

**The form is the original one.** `annotation_session.run_session` gained two optional parameters: a label subset
and a replacement attestation wording. Its default behaviour is unchanged, so operator-b would see exactly what
Mission 1.85.14 prepared. No default answer, no bulk answer, every pasted quote checked against the surface, a save
after each record, and resume where it stopped.

The committed file (`stack-overflow-semantic-reread-development-operator-a-v1.json`) holds states, offsets,
digests and bounded metadata. Its name deliberately does not match the blind-annotation pattern, so no tool can
mistake it for a second annotator.

## 3. Step 2: adjudication, and only where needed

A cell goes to adjudication when its readings differ or any of them is UNCERTAIN. The readings are:
- `ORIGINAL_BLIND`: operator-a's blind label (`449ff10f...`, unchanged);
- `DELAYED_REREAD`: the reread;
- `POST_MODEL_REVIEW`: the state implied by the latest post-model decision, for REPORTED_FAILED_ATTEMPT only.

**A floor, before the reread exists.** If the reread repeated every original label exactly, 13 cells would still
go to adjudication:
- 10 REPORTED_FAILED_ATTEMPT cells where a post-model review contradicted the blind label (9 revised to PRESENT
  and 1 revised to ABSENT in Mission 1.85.13);
- 3 UNCERTAIN cells (`5d0a1e34` REPORTED_FAILED_ATTEMPT, `db663e12` both labels).

The 7 Mission 1.85.10 over-reads and the 5 confirmed under-reads agree with the blind label and are not
adjudicated. Every cell where the reread disagrees with the original adds to the queue.

**The adjudication session.** For each cell the operator sees the surface, every reading, the human spans, the
post-model decision and its note, and prompt 1.1.0's quotes. This step is post-model by design, and the output
says so. Each decision needs:
- a final state (PRESENT, ABSENT or UNCERTAIN);
- a reason in the operator's own words (required, at most 600 characters);
- for PRESENT, a span (one of the human spans offered, or a pasted quote checked against the surface);
- for a PRESENT NEGATIVE_EVALUATION, a subject.

Each decision is bound to the readings it was made on. If the reread or a review changes afterwards, the decision
is refused as `STALE_ADJUDICATION`.

## 4. Step 3: the reference, and how it is labelled

`build_reference` produces, for each of the 46 records and both labels, a state and its basis:
- `CONSISTENT_ORIGINAL_REREAD_AND_REVIEW`: every reading agreed, so the original state and spans are kept;
- `ADJUDICATED_BY_THE_SINGLE_OPERATOR`: the adjudicated state and spans.

The file declares `reference_strength: SINGLE_HUMAN_ADJUDICATED_REFERENCE` and sets `is_consensus`,
`is_inter_human`, `is_blind`, `replaces_original_blind_annotation` and `certification` all to `false`. It refuses
to build unless every queued cell is decided, and only those.

Reread versus original is reported as `INTRA_RATER_DELAYED_REREAD` with `is_inter_human_reliability: false`:
the confusion table, raw agreement, Cohen's kappa and Krippendorff's alpha. It is one person's consistency across
a day, and nothing more.

The pilot stays `PILOT_NOT_CERTIFICATION`. No threshold moves from PROPOSED_NOT_AUTHORISED.

## 5. How the operator proceeds (PowerShell)

From the repository root, with the database running. The commands that read the held surfaces need
`DATABASE_URL`, and only that line is read from the compose file:

```powershell
$env:DATABASE_URL = ((Get-Content infrastructure\compose\.env | Select-String '^DATABASE_URL=').Line -replace '^DATABASE_URL=','')
```

Prepare the reread (writes outside the repository):

```powershell
uv run python infrastructure/scripts/single_operator_adjudication.py prepare-reread --out "$env:TEMP\sros-reread"
```

The reread, **not before 2026-09-19T23:57:02+04:00**. No database; it resumes where it stopped:

```powershell
uv run python infrastructure/scripts/single_operator_adjudication.py reread "$env:TEMP\sros-reread\reread-pack-operator-a.json"
```

Then, with `DATABASE_URL` set: `import-reread "$env:TEMP\sros-reread\reread-pack-operator-a.json"`, then
`prepare-adjudication --out "$env:TEMP\sros-adjudication"`, then `adjudicate "$env:TEMP\sros-adjudication"` (no
database), then `import-adjudication "$env:TEMP\sros-adjudication"`. `check` verifies whatever is committed at each
stage.

## 6. Tests and CI

`test_single_operator_adjudication.py` (19 tests, synthetic surfaces, no database):
- the original blind annotation is byte for byte unchanged, and the delay is derived from the reviews;
- the reread pack holds the 46 records and the 2 labels, all UNLABELLED, in a new order, with no earlier label,
  span, review decision or model output, and the folder holds only the pack and the surfaces;
- the reread asks nothing before the delay, and asks after it;
- a complete reread commits as a same-operator reading, not blind to the model, not a second annotator;
- an early start, a missing disclosure, a blind attestation key, a missing record, an unlabelled cell, an
  UNCERTAIN without a note and a PRESENT without a span are each refused, never repaired;
- only disagreeing or UNCERTAIN cells are queued (13 for an identical reread), and a disagreeing reread adds its
  cell;
- an adjudication needs a reason, a span for PRESENT and a timezone-aware time;
- the reference covers 46 records, is never consensus, inter-human, blind or certification, and refuses a
  missing or stale decision;
- intra-rater agreement is never labelled inter-human;
- the committed reference reproduces, carries no text, and a tampered decision fails `check`;
- no provider or network path in the protocol module or the script.

New CI step: `Single-operator adjudication is consistent with what is committed`.

**N08 is not DONE and N08-C was not started.** The next step is the operator's delayed reread.
