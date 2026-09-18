# Mission 1.85.14 report: second blind human reference and inter-human reliability preparation (N08-B-PILOT)

**Outcome: `WAITING_FOR_SECOND_BLIND_HUMAN_ANNOTATION`.**

Mission 1.85.13 showed that the single blind reference is too weak to decide the next extraction change. After
seeing the model's evidence, the operator revised it on 10 of the 15 records reviewed. Revisions made after
seeing a model are not a reference, so this mission prepares what would be one: **an independent second blind
human annotation**, and an agreement analysis frozen before that annotation exists.

    scope             the 46 EGRESS_APPROVED DEVELOPMENT records, all of them (not only the contested ones)
    shown             the frozen surface and the original annotation questions, nothing else
    agreement         frozen in code; computes nothing until operator-b is imported
    provider calls    0      model inferences 0      HOLDOUT records 0      canonical writes 0

No prompt, contract, packet, approval, repeatability run or production evidence was created. N08-C was not
started.

## 1. Phase A: history preserved

| Artifact | Result |
|---|---|
| Mission 1.85.9 and 1.85.12 evaluations (`--check`, both pilots) | reproduce byte for byte |
| Mission 1.85.10 post-model review (`check`) | reproduces |
| Mission 1.85.13 balanced review (`check`) | reproduces, status COMPLETE |
| Prompt-revision diagnostics, RFA regression spec, packet v5 renderer | current |
| operator-a blind annotation | `449ff10f...`, byte for byte |
| Prompt 1.0.0 `53bcc87f...`, prompt 1.1.0 `a4b96eb3...` | unchanged |
| Provider executions after Mission 1.85.12 | 0 |

No historical metric or annotation was rewritten.

## 2. Phase B to E: the second annotator's workflow

**Nothing new was invented for the annotator.** operator-b uses the same tooling operator-a used:
- `semantic_annotation.py prepare`, `label`, `lint` and `import`;
- the same blank pack, with all 400 cells `UNLABELLED`;
- the same interactive form, with the same eight questions and the same quote checks.

That form was committed on 2026-09-17 at 00:07 (+04:00), before operator-a annotated and before any model had
run. **It carries no prompt 1.0 or 1.1 wording**, which a test asserts, so no reconstruction was needed.

### What changed, and only this

**A record scope.** `prepare --scope egress-approved` limits the pack to exactly the 46 `EGRESS_APPROVED`
DEVELOPMENT records.
- The pack carries the scope's name and the sha256 of its ids.
- It carries **nothing that says why** a record is in scope.
- `lint` and `import` validate against that scope, and refuse a pack whose scope digest no longer matches the
  committed eligibility.

All 46 are annotated, not only the disputed ones: asking operator-b about the contested records alone would tell
them which records were contested.

**A second annotator must be a new annotator.** `prepare` refuses an id that already has an imported
annotation, so operator-a cannot be prepared again as a second reading.

**Scoped provenance in the committed file.** A scoped annotation additionally records:
- `record_scope` and `record_scope_ids_sha256`;
- `blind_to_model_outputs` and `blind_to_other_annotators`, which restate the annotator's own signed attestation
  (`no_model_output_seen`, `did_not_see_other_annotators_labels`) and add no claim the attestation lacks;
- `blindness_basis`, which says exactly what the blindness rests on.

operator-a's committed file is unaffected.

**Packet v5 pinned.** The packet renderer used to read every `...annotations-development-*-v1.json` by pattern.
Importing operator-b would therefore have re-rendered the historical, spent packet v5 into a different packet,
with two annotations, a non-single reference and new blockers. The renderer now names the one annotation v5
bound, operator-a. Its bytes are unchanged, and `--check` and the runner dry run still pass. A future packet
decides its own reference.

### What operator-b sees, and what they cannot

The prepared folder holds exactly two things: the working pack and a `surfaces/` folder of 46 rendered question
texts. It contains, and a test scans for:

| Hidden | Why it cannot reach them |
|---|---|
| operator-a labels and evidence spans | the pack is built from the blank pack; no other annotator's file is read |
| model labels, quotes, predictions of prompt 1.0 or 1.1 | no run summary, evaluation or model artifact is read by `prepare` or `label` |
| Mission 1.85.10 and 1.85.13 reviews | not read |
| disagreement status, regression-set membership, false-PRESENT or false-negative history | not read; the order is operator-b's own deterministic shuffle, seeded by their id |
| evaluator metrics, agreement so far | nothing is computed until the annotation is imported |

The form asks each question, accepts only an explicit answer (no default, no "all", no bulk path), checks every
pasted quote against the surface, saves after each record, and resumes where it stopped.

**What the tooling cannot do: make a person blind.** It controls what it shows, not what someone has already
seen. **operator-b must be a different person from operator-a**, someone who has not seen:
- this model's outputs;
- operator-a's labels;
- the reviews.

The attestation is the annotator's own statement. The importer refuses the file unless every flag is literally
true, so it must be answered truthfully. If no such person is available, the right outcome is to say so, not to
annotate as operator-b.

### Privacy

- The exact question text stays in the local folder, outside the repository.
- The committed file holds states, offsets, digests and bounded metadata. Quotes and notes stay local.
- No provider, gateway, socket or HTTP client is on this path, which a test asserts.

## 3. Phase F and G: the frozen agreement, not yet run

`infrastructure/scripts/inter_human_agreement.py` is committed **before** operator-b's annotation exists.
- **Inputs**: its only annotation inputs are named files: operator-a's original blind file (digest pinned) and
  operator-b's.
- **Refused inputs**: a post-model review offered as either side (it carries `provenance`/`blind`), the same
  annotator twice, a non-human origin, an unattested blind flag, and a B without its scope.
- **Record set**: it compares the records both labelled (46).

For each label it reports:
- the 3×3 A/B confusion table;
- raw agreement (three-state, and PRESENT/ABSENT with UNCERTAIN excluded and counted);
- PRESENT-specific and ABSENT-specific agreement;
- UNCERTAIN counts (A only, B only, both);
- Cohen's kappa and Krippendorff's alpha, each three-state and PRESENT/ABSENT;
- span agreement (identical, overlapping, mean character Jaccard) where both marked PRESENT;
- subject agreement for the label that needs a subject.

**Class imbalance is not hidden.** Each label states whether both annotators reached the contract's own
composition floor of 4 PRESENT. `NEGATIVE_EVALUATION_OF_NAMED_SOLUTION`, where operator-a has **0 PRESENT**, will be
reported as positive-class support insufficient: its kappa and alpha must not be read as positive-class
reliability.

**Before operator-b is imported**, `--check` reports `WAITING_FOR_SECOND_BLIND_HUMAN_ANNOTATION` and **fails if
any agreement artifact already exists**. So no partial comparison can be computed, committed or shown.

## 4. Phase H and I: disagreements for a later adjudication

Once operator-b is imported, the script derives, mechanically and ids only:
- `A_PRESENT_B_ABSENT`;
- `A_ABSENT_B_PRESENT`;
- `A_OR_B_UNCERTAIN`;
- `SPAN_ONLY`: both PRESENT, spans do not overlap;
- `SUBJECT_ONLY`: spans overlap, subjects do not.

These go to `stack-overflow-semantic-a-b-disagreements-development-v1.json`, marked `adjudicated: false`.

Nothing is adjudicated, no consensus reference is created, operator-a is not overwritten, operator-b is not
preferred, and no model output is ever a vote. A shared UNCERTAIN is kept as an open item, so even two identical
files would still send the UNCERTAIN records to adjudication.

The outcome after the annotation will be `SECOND_BLIND_HUMAN_REFERENCE_COMPLETE_ADJUDICATION_REQUIRED`. The
`...NO_EXTRACTABLE_DISAGREEMENT` status exists only for literally zero open items. Even then it does not
certify: every threshold in the contract is still `PROPOSED_NOT_AUTHORISED`.

### Post-model reviews stay outside

The Mission 1.85.10 and 1.85.13 reviews are read **only** into a separately labelled block,
`post_hoc_diagnostic_not_part_of_agreement`. For each reviewed record it lists the post-model decision,
operator-b's blind state, and whether A and B disagree. A test forges every review decision and shows the
agreement numbers do not move, only the post-hoc block does.

## 5. Phase J: engineering debt carried forward, untouched

1. **Packet v5 metadata path.** `operator_decisions.package` names the v1 decision-package file while its digest
   binds v2. v5 is historical and spent and is not mutated. This mission pinned v5's annotation input and did
   not touch that field. Before any packet v6, the renderer must write the correct path for the new packet
   without altering v5's bytes.
2. **Validator refusal.** Mission 1.85.12's one `QUOTE_NOT_IN_SURFACE`, on the reference-UNCERTAIN record
   `db663e12`, stays separate engineering debt. It is not needed here.

## 6. How operator-b starts

On this machine, from the repository root in PowerShell, with the database running. `prepare` reads the held
surfaces, so it needs `DATABASE_URL`:

```powershell
$env:DATABASE_URL = ((Get-Content infrastructure\compose\.env | Select-String '^DATABASE_URL=').Line -replace '^DATABASE_URL=','')
```

```powershell
uv run python infrastructure/scripts/semantic_annotation.py prepare --annotator-id operator-b --origin HUMAN_OPERATOR --out "$env:TEMP\sros-operator-b" --scope egress-approved
```

Then **operator-b** annotates. The form is in French, needs no database, and resumes where it stopped:

```powershell
uv run python infrastructure/scripts/semantic_annotation.py label "$env:TEMP\sros-operator-b\pack-development-operator-b.json"
```

Afterwards, `lint` then `import` (both need `DATABASE_URL`), then `inter_human_agreement.py --write`.

## 7. Tests and CI

`test_second_blind_annotation.py` (17 tests):
- operator-a's annotation and every evaluation and review reproduce unchanged;
- packet v5 is pinned to the annotation it bound and still renders byte for byte;
- operator-b starts with 46 `UNLABELLED` records, no timestamps, an unsigned attestation, and a folder holding
  only the pack and 46 surfaces;
- the prepared material contains no operator-a label, model output, review decision, disagreement or
  regression-set term, and the form's questions mention no prompt, model, agreement or review;
- there is no default and no bulk answer, a saved record survives, and the session resumes at the next one;
- HOLDOUT cannot be opened, and the 46 contain no HOLDOUT id;
- an annotator with an imported annotation cannot be prepared again;
- the agreement cannot run before operator-b is imported, and an agreement written early fails `--check`;
- identical annotations give full agreement but keep shared UNCERTAIN open;
- disagreements are derived by kind, and the confusion table sums to 46;
- `NEGATIVE_EVALUATION` positive-class support is reported as insufficient;
- post-model reviews never change the agreement, and a review offered as B is refused;
- B must be a different, attested-blind, human, scoped annotation;
- no source text in the committed agreement;
- no provider or network path in the annotation and agreement tools.

The Mission 1.85.4 `analyse` command now compares annotators on the records they share. It used to fail on two
files of different scope.

New CI step: `Inter-human agreement is absent until the second blind annotation, then current`.

**N08 is not DONE and N08-C was not started.** The next step is operator-b's blind annotation, by a person who
has not seen the model or operator-a's labels. Then the frozen agreement, then a human adjudication mission.
