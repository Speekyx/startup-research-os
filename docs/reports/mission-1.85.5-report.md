# Mission 1.85.5 report: single-human reference pilot mode (N08-B)

**Outcome: `SINGLE_HUMAN_REFERENCE_RECORDED_OPERATOR_DECISIONS_PENDING`.**

One genuine human DEVELOPMENT annotation now counts as a `SINGLE_HUMAN_REFERENCE`, a named and weaker
evidence standard for a development pilot. It does not count as inter-annotator gold. The development packet
moves from `BLOCKED_HUMAN_LABELS` to `BLOCKED_OPERATOR_DECISIONS`. What still blocks it is the operator's own
decisions: egress review, the pilot thresholds, the retry reading and the cost ceiling.

Start: `main` at `0f0025a`. The brief named `7b1b267` (the Mission 1.85.4 merge). Two follow-ups had been
merged on top of it since:
- #177, the interactive annotation form;
- #178, the import of operator-a's annotation.

This mission builds on both, because the one human reference it assesses is the file #178 committed.

Counters for this mission:
- provider calls 0;
- model inferences 0;
- Stack Overflow text egress 0;
- AI annotations produced 0;
- human labels written by any tool, agent or model 0;
- holdout records opened 0;
- production findings, Signals, Claims, Evidence, independence states and scores 0.

## 1. Why the evidence standard was reduced

The Mission 1.85.4 protocol requires at least two independent human annotators plus adjudication before a
reference counts. The operator recorded three facts:
- no second independent human annotator is available;
- they will not purchase external annotation;
- no second human may be fabricated, and no model, Claude Code, subagent or heuristic may stand in for one.

Without a change, N08 would stay blocked indefinitely on a person who does not exist. The alternatives were
worse:
- **Relabelling a model's output as `HUMAN_*`** would make the human origins mean nothing.
- **Letting the operator annotate twice under two ids** would present one person's consistency as agreement
  between people.

The reduction is therefore explicit and named. The weaker reference gets its own strength, its own result
scope and its own list of claims it may not make. Nothing about the stronger path was relaxed.

**No second human exists.** The repository holds exactly one committed human annotation file,
`stack-overflow-semantic-annotations-development-operator-a-v1.json`:
- reference origin `HUMAN_OPERATOR`;
- 50 DEVELOPMENT records;
- all four attestation statements true;
- imported by `semantic-annotation-importer@1.0.0` in #178.

A test pins that this is the only file.

**No AI impersonation occurred.**
- No model, agent or heuristic produced, suggested or reviewed any label.
- The operator labelled every record with the interactive form (#177), which proposes no answer.
- The assistant never viewed the surfaces or the working pack. It only ran `lint` and `import` on the
  finished pack, whose output is refusal codes and file names.
- When the operator pasted one sentence from a record and asked whether it qualified, the assistant declined
  to answer for that sentence and gave only invented examples on different situations.
- No `AI_ASSISTED_PROVISIONAL` annotation was produced in this mission, and none exists in the repository.
  A test asserts no file matches `*provisional*`.

## 2. Three reference strengths

`sros_semantic_extraction_contract/reference.py` (`semantic-reference-strength@1.0.0`) defines the strengths.

| Strength | What it is | What it may be used for |
|---|---|---|
| `SINGLE_HUMAN_REFERENCE` | exactly one valid, attested, complete human DEVELOPMENT annotation, and no refused file | a DEVELOPMENT pilot: `RESULT_SCOPE = DEVELOPMENT_PILOT`, result label `PILOT_NOT_CERTIFICATION` |
| `MULTI_HUMAN_REFERENCE` | two or more valid human files from distinct annotators, plus adjudication | the Mission 1.85.4 path, unchanged and preferred |
| `AI_ASSISTED_PROVISIONAL` | a model annotation | diagnostics only; never a human gate, never human agreement |
| `NO_HUMAN_REFERENCE` | anything else | nothing |

`assess_reference` re-checks every committed file before it counts: the importer id, a human origin, a
non-model annotator id, a valid attestation and ordered timestamps, the exact DEVELOPMENT record set, every
surface digest against the corpus, and every cell labelled with no quote or note text. A file edited after
import, or an AI file dropped beside the human one, is refused. **A refused file blocks both gates.** A
reference set with an invalid member is never trimmed to its valid part.

The human origins keep their meaning. `HUMAN_OPERATOR`, `HUMAN_EXPERT` and `HUMAN_NON_EXPERT` still mean that
a person labelled the records. Only the number of such people changes what may be concluded.

## 3. Agreement metrics

`analyse_single_human_reference` writes
`stack-overflow-semantic-single-human-reference-composition-development-v1.json`. It is a composition report,
not an agreement report. Every inter-annotator metric is the string `NOT_APPLICABLE_SINGLE_ANNOTATOR`:
- Cohen's kappa;
- Krippendorff's alpha;
- positive-specific agreement;
- negative-specific agreement;
- span agreement between humans;
- subject agreement between humans.

**None is encoded as 0**, because a zero would claim a disagreement was measured. The rest of the report
follows the same rule:
- **The adjudication queue size** is `NOT_APPLICABLE_SINGLE_ANNOTATOR`, and no queue file exists.
- **The agreement-floor gate** is `REQUIRES_MULTI_HUMAN_REFERENCE` with verdict
  `NOT_APPLICABLE_SINGLE_ANNOTATOR`.
- **The composition gate** is still read from the contract with its status, so its verdict is
  `GATE_NOT_AUTHORISED`.

`analyse_composition` is untouched. It still refuses fewer than two files, and with two or more it still
computes the pairwise and alpha measures. `semantic_annotation.py analyse` routes the cases:
- zero files: pending;
- one file: the single-human composition;
- two or more: the existing report and queue.

It never generates a second annotation.

## 4. Threshold partition

`docs/data/semantic-extraction-threshold-partition-v1.json` partitions the Mission 1.85.4 threshold decision
package without changing it. The source package digest is pinned, `values_changed` is false, and every entry
keeps its proposed value and `PROPOSED_NOT_AUTHORISED`.

| Bucket | Entries |
|---|---|
| `SINGLE_HUMAN_PILOT_VALID` (10) | both false-PRESENT rates, read as development point estimates and bounds; min true PRESENT and ABSENT; mechanical unsupported assertions; validator acceptance; unnecessary abstention; run-to-run flip rate; the composition gate read on the one human's cells; recall (descriptive); cost and latency |
| `REQUIRES_MULTI_HUMAN_REFERENCE` (4) | inter-annotator kappa; both false-PRESENT rates as certified against adjudicated gold; the gold composition gate |
| `REQUIRES_HOLDOUT` (9) | every criterion whose pass condition is defined on HOLDOUT |

The kappa floor is never a pilot threshold.

A pilot reading is never PASS or FAIL. Each authorised pilot criterion reports one of:
- `PILOT_WITHIN_PROPOSED_BOUND`;
- `PILOT_OUTSIDE_PROPOSED_BOUND`;
- `PILOT_INSUFFICIENT_SUPPORT`.

Each reading carries `REFERENCE_STRENGTH = SINGLE_HUMAN_REFERENCE` and `RESULT_SCOPE = DEVELOPMENT_PILOT`.
The pilot thresholds need their own operator decision (`AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT`, revise, or
reject), and none has been recorded.

## 5. AI provisional path (defined, not executed)

`sros_semantic_extraction_contract/provisional.py` defines where a model annotation would live and what it
may do. None was made.
- **Storage:** its own glob, `stack-overflow-semantic-provisional-ai-annotations-development-*-v1.json`,
  which the human glob never matches. It is never imported through `semantic_annotation.py import`, whose
  validator refuses any non-human origin.
- **What a valid file carries:**
  - origin `AI_ASSISTED_PROVISIONAL`;
  - strength `AI_ASSISTED_PROVISIONAL`;
  - use `DIAGNOSTIC_ONLY`;
  - DEVELOPMENT records only;
  - no attestation block, since a model cannot attest to not using a model.

  A file that claims a human origin is refused.
- **Use:** its only use is `diagnostic_disagreements`, which lists the cells where it and the single human
  differ, to locate ambiguous label definitions. The output states:
  - `is_human_agreement: false`;
  - `human_labels_changed: 0`;
  - inter-annotator agreement `NOT_APPLICABLE_SINGLE_ANNOTATOR`.

  It reads both documents and changes neither.
- **Running one** is a future mission. It would need its own provider authorisation, like any model call.

## 6. Evaluation packet

The packet is re-rendered as version 2 (`packet_sha256` `894d8532...`). Its new `reference` block states:
- `REFERENCE_STRENGTH` `SINGLE_HUMAN_REFERENCE`, `RESULT_SCOPE` `DEVELOPMENT_PILOT`, result label
  `PILOT_NOT_CERTIFICATION`;
- pilot gate satisfied, multi-human gate not satisfied;
- `ai_annotations_used_as_reference` 0;
- the six inter-annotator metrics as `NOT_APPLICABLE_SINGLE_ANNOTATOR`;
- the prohibited claims;
- `holdout_policy` `HOLDOUT_REQUIRES_MULTI_HUMAN_OR_NEW_OPERATOR_DECISION` and
  `holdout_reference_permitted` false;
- the threshold partition digest, with the thresholds read set to `SINGLE_HUMAN_PILOT_VALID`.

**Status.** `BLOCKED_HUMAN_LABELS` now means no human reference gate is satisfied. The new
`BLOCKED_OPERATOR_DECISIONS` means a human reference exists and operator decisions remain. The current
blockers are:
1. `EGRESS_REVIEW_PENDING`: 0 approved, 1 excluded, 49 review required;
2. `THRESHOLDS_NOT_AUTHORISED` for the single-human pilot thresholds;
3. `RETRY_INTERPRETATION_NOT_RATIFIED`;
4. `COST_CEILING_NOT_ACCEPTED`.

With no human reference, the packet keeps the Mission 1.85.4 blockers `HUMAN_LABELS_PENDING` and
`ADJUDICATION_PENDING`. A multi-human reference still reads every contract threshold.

**Runner.** `run_semantic_extraction_evaluation.py` is re-pinned to the new digest and adds two refusals:
- `READY_WITHOUT_A_HUMAN_REFERENCE`: a READY packet whose strength is not single- or multi-human;
- `SINGLE_HUMAN_REFERENCE_OVERCLAIMED`: a single-human packet without the pilot scope or label, with holdout
  permitted, or with any AI annotation used as a reference.

An approval must now also carry an `accepted_reference_strength` equal to the packet's. The run record copies
`REFERENCE_STRENGTH`, `RESULT_SCOPE` and the result label. **Execution still requires the separate,
packet-scoped operator approval file, and none exists.** Merging this mission authorises no provider call.

**No result on this path may claim** any of the following:
- `INTER_HUMAN_RELIABILITY`;
- `VALIDATED_HUMAN_CONSENSUS`;
- `GENERALISATION_TO_HOLDOUT`;
- `PRODUCTION_READINESS`;
- `CALIBRATED_SEMANTIC_ACCURACY`.

## 7. HOLDOUT

HOLDOUT stays isolated.
- `holdout_reference_permitted(strength)` takes no other parameter and returns true only for
  `MULTI_HUMAN_REFERENCE`. A single-human holdout would need a recorded operator decision and a change to
  that function in the same reviewed diff.
- The importer still raises `HoldoutAccessError` for any holdout split.
- No holdout annotation exists, and the holdout pack is unchanged (digest pinned).

## 8. Roadmap

N08 moves to `SINGLE_HUMAN_REFERENCE_RECORDED_OPERATOR_DECISIONS_PENDING`, with a new phase `N08-B-PILOT`. It
becomes `DEVELOPMENT_PILOT_SINGLE_HUMAN_REFERENCE` only when the packet is READY, and N08 is never DONE on
this path. D-12 stays OPEN, and the other roadmap nodes are unchanged.

## 9. What conclusions are now weaker

A development pilot scored against one person's labels can show:
- whether the extractor runs within bounds;
- whether its payloads validate;
- how often it abstains;
- how its PRESENT and ABSENT calls line up with that person's reading.

It cannot show whether the label definitions are clear enough that two people would apply them the same way,
because no agreement was measured. The consequences:
- **A disagreement between model and reference may be the person's reading, not the model's error.** Without
  adjudication, UNCERTAIN cells stay UNCERTAIN and nothing resolves them.
- **False-PRESENT and recall figures are estimates against one reading.** They are not rates against
  validated gold.
- **The composition counts describe one annotator's labels** in an enriched query window. They are not
  prevalence.
- **Nothing generalises to HOLDOUT**, to other sources or to production.

## 10. What stronger certification still requires

- a second independent human annotation of the DEVELOPMENT split, then the unchanged agreement report,
  adjudication by a third human or a recorded joint session, and the kappa floor decided by the operator;
- a separate operator decision on the thresholds that require a multi-human reference;
- holdout labelling by at least two humans, or a new recorded operator decision that changes
  `holdout_reference_permitted`, before any holdout evaluation;
- the egress review, retry ratification, cost ceiling acceptance and a packet-scoped approval for any run.

## 11. Verification

Local runs before the pull request, with CI as the merge gate:
- `ruff check`, `ruff format --check` and `mypy` on the contract package: clean;
- bare runner: 3966 tests across 10 packages, all passing (new: `test_reference_strength.py`, 14 tests);
- pytest `packages/semantic-extraction`: 25 passed, including the updated packet assertions and two new
  runner tests;
- pytest `packages/opportunity-engine`: 4096 passed (roadmap N08 status set extended);
- pytest `services/research-orchestrator`: 97 passed;
- suites that read `docs/CLAUDE.md` or the roadmap, rerun after the version entries: inferred-claim-evaluator
  2470 passed, evidence-reliability 352 passed, acquisition 134 passed;
- all 99 `--check` render commands named in `ci.yml`: current, with the packet
  `BLOCKED_OPERATOR_DECISIONS`.

What the new tests prove:

| Requirement | Test |
|---|---|
| one real human satisfies only the pilot gate | `test_one_real_human_satisfies_only_the_pilot_gate` (the committed operator-a file, read-only) |
| one human cannot satisfy the multi-human gate | `test_one_human_cannot_satisfy_the_multi_human_gate_even_with_an_adjudication_file` |
| AI provisional satisfies neither human gate | `test_ai_provisional_satisfies_neither_human_gate`, alone and beside the human |
| a model-like annotator id is refused by the human importer | `test_a_model_like_annotator_id_is_still_refused_by_the_human_importer` |
| multi-human behaviour unchanged | `test_multi_human_behaviour_is_unchanged` (synthetic structural copies, never committed) |
| single-human metrics are NOT_APPLICABLE, not zero | `test_inter_annotator_metrics_are_not_applicable_and_never_zero` |
| HOLDOUT blocked by default | `test_holdout_stays_blocked_by_default` |
| execution still needs a separate operator approval | `test_a_ready_single_human_packet_still_needs_a_separate_operator_approval`, `test_a_reference_that_is_not_human_or_overclaims_is_refused`, the extended approval matrix |

## 12. Next

The next step is operator decisions, on the pilot path:
- egress review of the development records;
- the single-human pilot thresholds;
- the retry reading;
- the cost ceiling.

Then, separately, a packet-scoped approval. **Do not run the model, produce an AI annotation, treat the pilot
as certification, open holdout, or create Opportunity #2.**
