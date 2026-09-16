# Stack Overflow semantic annotation and adjudication workflow v1 (N08-B)

Mission 1.85.4. This is how real humans produce the DEVELOPMENT reference labels that N08-A requires. No
model, assistant, subagent or heuristic may fill a label, suggest one, or see a working copy.

## What the tooling can and cannot establish

It can refuse a pack that is incomplete or inconsistent, cites text not in the surface, or declares a
non-human origin. **It cannot prove a human typed the labels.** That rests on:
- the attestation block each annotator signs;
- the operator's statement in the mission report that records who annotated.

Every document that reports these labels repeats that limit.

## Annotator steps

1. **Prepare a working copy outside the repository.**
   ```
   uv run python infrastructure/scripts/semantic_annotation.py prepare \
     --annotator-id <your id> --origin HUMAN_OPERATOR|HUMAN_EXPERT|HUMAN_NON_EXPERT --out <dir outside the repo>
   ```
   - The command writes `pack-development-<id>.json`, with your deterministic record order and an unfilled attestation.
   - It writes `surfaces/NNN-<record id>.txt`: the exact text you judge, rendered from the held record.
   - It refuses any folder inside the repository, a non-human origin, and holdout.
2. **Keep models out of the folder.**
   - Do not open it with Claude Code or any other assistant.
   - Do not paste its contents into a chat tool.
   - Do not sync it to a service with AI features.
   - Do not look at another annotator's file.
3. **Easiest: use the interactive form.**
   ```
   uv run python infrastructure/scripts/semantic_annotation.py label <dir>/pack-development-<id>.json
   ```
   It shows each question from `surfaces/`, asks the eight questions one by one (`o` yes, `n` no, `?` not sure, `t` show the text again, `q` quit), checks every pasted quote against the text immediately, and saves after each record; run it again to resume. At the end it asks the four attestation statements and sets each to true only if you answer `o`. It never proposes an answer and needs no database. Editing the JSON by hand (below) remains possible.
   **Label every record.** Cells use `PRESENT`, `ABSENT` or `UNCERTAIN`; see contract §5–§6 for the definitions.
   - **Extractable labels.** `PRESENT` needs `evidence: [{"quote": "<exact text>", "occurrence": 1}]`.
     - `NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` also needs `subject: {"quote": "<exact name>", "occurrence": 1}`.
     - Copy quotes exactly from the surface file. The tool computes offsets.
   - **`UNCERTAIN`** needs a `note`.
   - **Incidence labels** (annotation-only and blocked) take a state only, with no evidence and no subject.
   - **Holder rule.** Only the asker's own statements count. Quoted, attributed, negated or hypothetical text is `ABSENT`.
4. **Lint until it passes.**
   ```
   uv run python infrastructure/scripts/semantic_annotation.py lint <dir>/pack-development-<id>.json
   ```
5. **Sign the attestation.** Set every flag to `true` only if it is true, and set `attested_at` and the two annotation timestamps.
6. **The operator imports the pack.**
   ```
   uv run python infrastructure/scripts/semantic_annotation.py import <dir>/pack-development-<id>.json
   ```
   - Only states, offsets and digests are committed, as `stack-overflow-semantic-annotations-development-<id>-v1.json`.
   - Quotes and notes stay in the working copy.
   - A second import of the same annotator, or of an identical pack, is refused.

## Composition and agreement

```
uv run python infrastructure/scripts/semantic_annotation.py analyse
```
- **Before two annotators exist,** the command prints `HUMAN_LABELS_PENDING` and writes nothing.
- **Once two exist, it writes:**
  - per-label state counts and prevalence;
  - Cohen's κ in two forms (three states, and PRESENT/ABSENT), and Krippendorff's α;
  - raw, positive-specific and negative-specific agreement, prevalence and bias indices, and PABAK;
  - span agreement (exact, overlap, character Jaccard) and subject agreement;
  - the adjudication queue.
- **No threshold is applied.** The composition gate and the κ floor are reported with their status `PROPOSED_NOT_AUTHORISED`, and the verdict is `GATE_NOT_AUTHORISED` until the operator authorises them.

## Adjudication

**Which (record, label) pairs are queued:**
- the states differ;
- any annotator marked `UNCERTAIN`;
- both marked `PRESENT` but the evidence spans do not overlap;
- both marked `PRESENT` on the negative-evaluation label but the subjects do not overlap.

Incidence labels are queued only when their states differ. Agreed cells are not re-reviewed.

**Who adjudicates.** Either a third human who is not one of the annotators (`THIRD_HUMAN`), or a recorded joint session (`JOINT_SESSION`). The adjudicator reads rendered surfaces from their own folder outside the repository, and never model output.

**File:** `stack-overflow-semantic-adjudication-development-v1.json`. It records:
- `split`, `method`, `adjudicator_id`, `adjudicator_origin` (human), `participants`;
- `inputs` (annotator file digests);
- `queue_sha256`;
- `model_output_consulted: false`;
- `items`, each with the original states, a `resolution`, a `resolved_state` and `resolved_spans`.

**Resolutions:**
- `RESOLVED_TO_EXISTING_STATE`: the resolved state must be one an annotator gave.
- `RESOLVED_AFTER_REREAD`: needs a recorded note.
- `UNRESOLVED_KEPT_UNCERTAIN`: the state stays `UNCERTAIN`.

**What happens to the files.** Annotation files are never edited. The reference is recomputed as agreed cells plus adjudicated items, and anything unresolved stays `UNCERTAIN`.

## Holdout

The holdout pack is not prepared, rendered, linted, imported or analysed by any N08-B command. Every
development command refuses a holdout path, a holdout split and any record of the holdout split.
Holdout labelling is an N08-C step, after the prompt is frozen.
