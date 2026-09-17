# Mission 1.85.12 report: prompt 1.1.0 full DEVELOPMENT pilot and precision-revision evaluation (N08-B-PILOT)

**Outcome: `PROMPT_1_1_DEVELOPMENT_PILOT_RESULTS_READY_FOR_OPERATOR_REVIEW`.**

Operator `operator-a` approved exactly one DEVELOPMENT evaluation execution of packet v5. The approval was
recorded, validated and consumed by one clean full run through the canonical runner:
- all 46 approved records were attempted;
- 45 answers were accepted by the validator and 1 was refused;
- there were no retries, no provider errors and no bounded stop.

The approval is spent. **Nothing was rerun.**

**Headline: prompt 1.1.0 did not improve `REPORTED_FAILED_ATTEMPT` precision on this evidence.**
- The full-run false-PRESENT reading is still outside the proposed bound.
- Only 2 of the 9 known over-reads were corrected.
- 6 of the 15 blind-reference positives were lost.

Every result is `DEVELOPMENT_PILOT` and `PILOT_NOT_CERTIFICATION`, measured against the same
`SINGLE_HUMAN_REFERENCE`.

    packet     6b27bccbc22c7051be9d8f1df4dd22a4635d0f664d4b4fa05ede820e90a72a7e  (version 5)
    approval   9fc8fac724bdfa54a2967aaab668524f778ed476e6a1668a596efd6ac57c9974
    approved   2026-09-17T21:16:21+04:00 by operator-a
    executed   2026-09-17T17:17:03+00:00 to 17:19:25+00:00, anthropic / claude-sonnet-5, prompt 1.1.0
    calls      46 of at most 92; 0 schema retries
    cost       $0.4421406 of $9.000000 (4.91%), all from reported usage

Start state: `main` at `72420c3` (merge of PR #188). The pre-execution commit `b8bad36` on the branch was pushed
and verified by ref before the approval existed.

## 1. Phase 0: immutable preflight

These checks were recomputed from the files, not quoted.

| Check | Result |
|---|---|
| Packet version 5, status `READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL`, blockers `[]` | ok |
| Recorded, recomputed and runner-pinned digest all equal the approved `6b27bccb...` | ok |
| Packet renderer `--check` (fresh render) | ok |
| Prompt 1.1.0 `a4b96eb3...`; prompt 1.0.0 still `53bcc87f...` | ok |
| Label set `first-person-semantic-labels@1.0.0` and contract digest, same as v4 | ok |
| Strict and canonical tool schema digests, same as v4 | ok |
| Provider, model and route unchanged from v4; `fallback_provider` null | ok |
| Retry policy block identical to v4; implementation file digest `329106a0...` | ok |
| Thresholds, retry and ceiling decisions identical to v4; decisions file `ac2bb1d9...` | ok |
| Ceiling `9.000000`; retry worst case + one documented maximum ≤ ceiling | ok |
| 46 `EGRESS_APPROVED` DEVELOPMENT records, the same set as v4; HOLDOUT excluded; 0 review required | ok |
| All 46 live surfaces match their packet digest (database) | ok |
| Egress eligibility, request sizes and RFA analysis `--check` (database) | ok |
| Provider verification `VERIFIED`, within its review interval | ok |
| Repeatability runs authorised = 0 | ok |
| No v2 approval, no v2 attempt | ok |
| Packet v4 file `0fbc4357...` and digest `5f96b418...` unchanged | ok |
| Approval v1 `77cdea89...` spent by its attempt record | ok |
| Mission 1.85.9 evaluation reproduces and still reads `PILOT_OUTSIDE_PROPOSED_BOUND` | ok |
| Mission 1.85.10 post-model review reproduces | ok |
| Blind annotation `449ff10f...` unchanged; regression spec `20e6da82...` current | ok |

**One label defect was found and deliberately left in place.**
- **What is wrong**: in packet v5, `operator_decisions.package` names
  `...decision-package-development-v1.json`, but `package_sha256` is `c4c72ff3...`, the digest of the **v2**
  package. The digest, which is what binds, is correct.
- **Why it is harmless**: no code reads the path, and the decisions it points to are byte-identical to v4.
- **Where it comes from**: a hard-coded string in `render_semantic_extraction_packet.py`.
- **Why it was not fixed**: fixing it would change the packet digest and so require a new approval.
- **Status**: recorded for a later mission.

`APPROVED_PACKET_CHANGED_REAPPROVAL_REQUIRED` did not arise.

## 2. Phase 1: pre-execution rehearsal

Scripted transports only; no key was read and no provider was contacted. The existing suites passed:
- semantic-extraction 108, which includes the Mission 1.85.9 rehearsal;
- llm-gateway 183, with 2 skipped;
- the zero-dependency runner, 3993 tests.

A new rehearsal, `test_prompt_1_1_execution_rehearsal.py` (4 tests), drives `main --execute` on the committed v5
packet's own price, documented per-call maximum and $9 ceiling. It uses synthetic records and a whole-request
deadline shortened to 0.3 s.

| Required property | Rehearsed |
|---|---|
| Approval gate works | real `check_approval`, provider verification, ceiling preflight, ADR-033 authorization |
| Stale v4 approval cannot unlock v5 | refused `OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET` before any transport or attempt record |
| Cost ceiling enforced | 4 unreported calls at $2.245056 are allowed (8.980224 ≤ 9); the 5th is refused `COST_CEILING_WOULD_BE_CROSSED` and never sent |
| Schema retry semantics | a payload missing `extraction_state` is retried once, then accepted |
| No schema retry on provider/network errors | a reset, a stall and an HTTP 529 are each `PROVIDER_ERROR`, with 1 attempt and no retry |
| Connection reset mapped through the gateway | the **real** `UrllibTransport` wraps a raw `ConnectionResetError` → `TransportError` → `ProviderTemporaryError` |
| Total request deadline bounded | the **real** transport stops a 2 s stall at the 0.3 s deadline → `ProviderTimeoutError` |
| One record's failure does not consume another's retry | the record after the failures keeps retry 0 → 1 |
| No fallback provider or model | one URL, one model, one registered provider; packet and policy fallbacks null |
| Second execution with a spent v5 approval | refused `EVALUATION_APPROVAL_ALREADY_SPENT` before any transport |

**The current semantics were confirmed, not changed.** A classified record-level provider or network failure
costs that one record:
- it is recorded, charged the documented maximum, and not retried;
- the run then continues to the next record.

With the $9 ceiling, up to four such failures fit before the ceiling stops the run.

**The rehearsal passed first time. No defect was found, so
`EXECUTION_IMPLEMENTATION_CHANGE_REQUIRES_NEW_PACKET_REVIEW` did not arise.** No runner, gateway, prompt,
schema, validator, cost-ledger, retry, adapter, packet-renderer or transport code changed in this mission.

**Evaluation rules frozen before the run** (commit `b8bad36`):
- `evaluate_semantic_extraction_pilot.py` gains pilot `V2` (the packet v5 files). Its Mission 1.85.9 rules are
  unchanged, and the V1 evaluation still reproduces byte for byte.
- `evaluate_prompt_revision_diagnostics.py` defines the regression diagnostics and the valid-overlap
  comparison. It was tested on synthetic runs, including a reference-mirroring prompt and a
  "precision by answering ABSENT" prompt.

## 3. Phases 2 and 3: approval recorded and validated

`docs/data/semantic-extraction-evaluation-approval-development-v2.json`, sha256 `9fc8fac7...`, has
`approved_at` **2026-09-17T21:16:21+04:00**, the actual time of recording.

It records:
- packet id, version 5 and the full digest;
- `operator-a` as approver;
- `APPROVE_EXACTLY_ONE_EVALUATION_RUN` and `ONE_DEVELOPMENT_PILOT_EXECUTION`;
- provider `anthropic`, model `claude-sonnet-5`, 46 records;
- ceiling `"9.000000"`;
- `SINGLE_HUMAN_REFERENCE` / `DEVELOPMENT_PILOT` / `PILOT_NOT_CERTIFICATION`;
- the ratified `semantic-extraction-schema-failure-retry-policy@1.0.0`;
- 0 repeatability runs, HOLDOUT prohibited, production persistence prohibited;
- a clean full run, not a continuation.

Statement recorded verbatim: *"This approval authorises exactly one full DEVELOPMENT evaluation execution of packet
6b27bccbc22c7051be9d8f1df4dd22a4635d0f664d4b4fa05ede820e90a72a7e and no other packet, split, continuation,
rerun, repeatability run, HOLDOUT run, or production persistence."*

The runner's own functions validated it before the credential was in the process:
- `verify_packet`, `check_approval` (file digest, packet digest, version, provider, model, count, ceiling,
  scope, reference strength), provider verification and ceiling preflight: all ok;
- no prior attempt;
- a wrong digest was refused `APPROVAL_FILE_DIGEST_MISMATCH`;
- the spent v1 approval was refused `OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET`.

The key was absent from the environment throughout.

## 4. Phase 4: the single execution

```
run_semantic_extraction_evaluation.py --execute --approval-sha256 9fc8fac7... --output-dir <outside the repository>
```

- **Attempt record** written exclusively before the first request:
  `semantic-extraction-evaluation-attempt-development-v2.json`, `ATTEMPT_STARTED` at 17:17:03 UTC, naming the
  packet and the approval. It was normalised to LF after the run; the content is unchanged.
- **46 calls, one per record, in packet order**:
  - every call returned HTTP 200 with `stop_reason tool_use` and reported usage;
  - 45 answers were accepted;
  - 1 (`db663e12`) was refused `QUOTE_NOT_IN_SURFACE`, not retried (a validator refusal is outside the retry
    class).
- **No provider error, timeout, reset, `max_tokens` stop, model refusal or schema failure occurred.** No
  run-fatal condition arose.
- It was a clean full run of prompt 1.1.0 over all 46 records. It was not a continuation of Mission 1.85.9's
  records 24 to 46 and not a targeted regression call set. The prompt carries no regression-set id, text or
  digest (Mission 1.85.11).
- The full run record, with model payloads and verbatim quotes, stays outside the repository.

## 5. Run execution

| Fact | Value |
|---|---|
| Approved / attempted / accepted / validator refused / not attempted | 46 / 46 / 45 / 1 / 0 |
| Provider calls / schema retries / provider errors | 46 / 0 / 0 |
| Bounded stop | none |
| Run elapsed | 142.6 s |
| Call latency median / p95 (nearest rank) / max | 2.84 s / 4.18 s / 18.03 s |
| Input / output tokens reported | 165,633 / 7,068 (cache fields folded into input; none requested) |
| Cost | **$0.4421406**, all reported usage; per call $0.006824 to $0.024090 |
| Ceiling consumed | 4.91% of $9.000000 |
| Canonical writes | 0 |

The ledger authorised every call before sending it.

## 6. Evaluation (Phase 6)

These are the rules from `evaluate_semantic_extraction_pilot.py@1.0.0`, frozen in Mission 1.85.9. They were
applied to the new run over all 46 records against the same blind annotation (unchanged).

| Item | Reading | Basis |
|---|---|---|
| `false_present_rate_upper_95::REPORTED_FAILED_ATTEMPT` | **PILOT_OUTSIDE_PROPOSED_BOUND** | 16 false PRESENT of 25 PRESENT calls on decided records (support 25, required 15); point 0.64; one-sided Clopper-Pearson upper 95% **0.798** against 0.20 |
| `false_present_rate_upper_95::NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` | PILOT_INSUFFICIENT_SUPPORT | 0 PRESENT calls (30 required) |
| `min_true_present_and_min_true_absent::REPORTED_FAILED_ATTEMPT` | PILOT_WITHIN_PROPOSED_BOUND | true PRESENT 9, true ABSENT 13 |
| `min_true_present_and_min_true_absent::NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` | PILOT_INSUFFICIENT_SUPPORT | reference PRESENT 0 |
| `mechanical_unsupported_assertions_accepted::all` | PILOT_WITHIN_PROPOSED_BOUND | 32 accepted findings, 0 unsupported |
| `validator_acceptance_rate::all` | PILOT_WITHIN_PROPOSED_BOUND | 45 / 46 = 0.978 (bound 0.95) |
| `unnecessary_abstention_rate_on_gold_decided::all` | PILOT_WITHIN_PROPOSED_BOUND | 0 abstentions in 89 decided cells with valid output |
| `composition_gate::REPORTED_FAILED_ATTEMPT, DEVELOPMENT` | PILOT_WITHIN_PROPOSED_BOUND | reference 15 PRESENT / 29 ABSENT |
| `composition_gate::NEGATIVE_EVALUATION_OF_NAMED_SOLUTION, DEVELOPMENT` | PILOT_INSUFFICIENT_SUPPORT | reference 0 PRESENT / 45 ABSENT |
| `recall::REPORTED_FAILED_ATTEMPT` | descriptive, no bound | 9 / 15 = 0.60 |
| `recall::NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` | PILOT_INSUFFICIENT_SUPPORT | undefined |
| `cost_and_latency::all` | descriptive, no bound | section 5 |
| `run_to_run_label_flip_rate` | **not evaluated** | rejected for the pilot; no additional run |

No `PILOT_INSUFFICIENT_SUPPORT` is read as a pass or a fail, and no threshold moved.

## 7. Phase 8: full REPORTED_FAILED_ATTEMPT performance (46 records)

| | Value |
|---|---|
| Reference PRESENT / ABSENT / UNCERTAIN | 15 / 29 / 2 |
| Model PRESENT / ABSENT / ABSTAIN / no valid output / not attempted | 26 / 19 / 0 / 1 / 0 |
| True PRESENT / false PRESENT / true ABSENT / false negative (model ABSENT, reference PRESENT) | 9 / 16 / 13 / 6 |
| Recall | 9 / 15 = 0.60 |
| Precision on decided records | 9 / 25 = 0.36 |
| False-PRESENT point estimate / upper 95 | 0.64 / 0.798 |
| Unnecessary abstention | 0 |
| Validator acceptance | 45 / 46 |

Reference UNCERTAIN records:
- `5d0a1e34`: model PRESENT;
- `db663e12`: no valid output (the validator refusal).

The 16 false PRESENT are listed by id in `semantic-extraction-pilot-evaluation-development-v2.md`. They include:
- 7 of the 9 known over-reads;
- `3d0568c4`, the record whose call stalled in Mission 1.85.9.

## 8. Phase 10: NEGATIVE_EVALUATION_OF_NAMED_SOLUTION

| | Value |
|---|---|
| Reference PRESENT / ABSENT / UNCERTAIN | **0** / 45 / 1 |
| Model PRESENT / ABSENT / no valid output | 0 / 45 / 1 |
| True ABSENT / false PRESENT | 45 / 0 |
| Recall / composition / false-PRESENT reading | undefined / insufficient / `PILOT_INSUFFICIENT_SUPPORT` |

The reference still contains no positive, so every unsupported item stays insufficient. That is the known
reference limitation, not a model failure.

**No visible regression in its negative behaviour:**
- 0 PRESENT calls on 45 answered records, where Mission 1.85.9 had 0 on 23;
- on the 23-record overlap, all 23 stay ABSENT under both prompts.

## 9. Phase 7: RFA targeted regression diagnostics

These are `POST_MODEL_DEVELOPMENT_REGRESSION_DIAGNOSTIC` results, from
`semantic-extraction-rfa-regression-spec-development-v1.json`. They are not thresholds and not certification.
Pilot success was not redefined around them.

### A. KNOWN_OVERREAD (9)

| Record | Prompt 1.0.0 | Prompt 1.1.0 | Status |
|---|---|---|---|
| `17064c93` | PRESENT | PRESENT | persistent |
| `1a659352` | PRESENT | PRESENT | persistent |
| `203268d4` | PRESENT | PRESENT | persistent |
| `37bf2146` | PRESENT | PRESENT | persistent |
| `9f91eeea` | PRESENT | PRESENT | persistent |
| `ac423fe4` | PRESENT | **ABSENT** | corrected |
| `bf04af60` | PRESENT | PRESENT | persistent |
| `d6bff833` | PRESENT | **ABSENT** | corrected |
| `e35f990d` | PRESENT | PRESENT | persistent |

**Prior over-reads 9; corrected 2; persistent 7; abstained 0; unavailable 0.**

### B. POSITIVE_SENSITIVITY (15)

- 15 evaluated: 9 PRESENT retained, 6 missed as ABSENT, 0 abstentions, 0 unavailable.
- Descriptive recall 0.60.
- Missed: `4a3fc738`, `96054702`, `b7996f9d`, `e2162aae`, `e9edbbaa`, `f876b0be`.

## 10. Phase 9: valid prompt 1.0.0 against prompt 1.1.0 comparison

Mission 1.85.9 was partial, with 23 accepted records of 46. The comparison therefore uses only records where
both runs have an accepted extraction: **23 records**, all of Mission 1.85.9's accepted set.
**This is not an independent test set.** Prompt 1.1.0 was revised after the nine over-reads, which lie inside
this overlap.

### REPORTED_FAILED_ATTEMPT on the overlap (recomputed from the committed summaries)

| Measure | Prompt 1.0.0 | Prompt 1.1.0 | Delta |
|---|---|---|---|
| Model PRESENT (decided records) | 18 | 11 | -7 |
| Reference PRESENT | 9 | 9 | 0 |
| True PRESENT | 9 | 4 | **-5** |
| False PRESENT | 9 | 7 | **-2** |
| Reference PRESENT recovered (recall) | 9/9 = 1.00 | 4/9 = 0.444 | -0.556 |
| Precision | 0.50 | 0.364 | -0.136 |
| False-PRESENT rate (descriptive upper 95) | 0.50 (0.709) | 0.636 (0.865) | +0.136 |

Changed classifications:

| Change | Count | Records |
|---|---|---|
| PRESENT → ABSENT | 7 | 2 over-reads corrected (`ac423fe4`, `d6bff833`); 5 true positives lost (`4a3fc738`, `96054702`, `b7996f9d`, `e9edbbaa`, `f876b0be`) |
| PRESENT → ABSTAIN | 0 | |
| ABSENT → PRESENT | 0 | |
| ABSENT → ABSTAIN | 0 | |

Unchanged: 11 PRESENT → PRESENT and 5 ABSENT → ABSENT.

**Records outside the overlap** (22 answered records Mission 1.85.9 never reached): 9 false PRESENT, 5 true
PRESENT, 6 true ABSENT, 1 missed, 1 PRESENT on a reference UNCERTAIN. Prompt 1.1.0's over-reading is not
confined to the records it was revised against.

## 11. Phase 11: interpretation, three questions kept apart

**A. Did precision improve? No.**
- Full run: false PRESENT 16 of 25 (0.64), upper 0.798, still `PILOT_OUTSIDE_PROPOSED_BOUND`.
- On the comparable overlap: false PRESENT fell only from 9 to 7, and precision fell from 0.50 to 0.36, because
  true PRESENT fell faster.

**B. Did recall collapse? Partly.**
- Full-run recall is 0.60 (9 of 15), and all 6 misses are model ABSENT on a human PRESENT. Under prompt 1.0.0
  there were 0 such misses on attempted records.
- On the overlap, recall fell from 9/9 to 4/9.
- The label did not go to ABSENT everywhere: 26 PRESENT calls remain. But the revision cost sensitivity without
  buying precision.

**C. Did the nine known over-reads improve? Barely.**
- 2 of 9 were corrected and 7 persist.
- This is developmental regression evidence only, and it is weak.

These three answers are not combined into one accuracy score.

## 12. What can be concluded

- **The machinery is sound on real traffic, and the transport fix held.**
  - One clean full run of 46 records: every call HTTP 200 and `tool_use`, 45 of 46 accepted, 0 unsupported
    accepted findings, 0 retries, 0 provider errors.
  - $0.44 against a $9 ceiling (4.9%); no call exceeded 18 s.
- **Prompt 1.1.0's three-anchor instruction did not make the model stop marking these records PRESENT.**
  - It removed some PRESENT calls, but more of the removals were true positives than over-reads.
  - Measured against the blind single-human reference, the revision is worse than prompt 1.0.0 on the
    comparable records.
- **`NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` shows no visible regression.**
- **Mission 1.85.9 = `PILOT_OUTSIDE_PROPOSED_BOUND` remains historically true**, and so does its evaluation
  byte for byte.

## 13. What cannot be concluded

- Nothing certified: no inter-human reliability, consensus gold, HOLDOUT generalisation, production readiness or
  calibrated semantic accuracy.
- **Whether the 16 disagreements are model errors or reference errors.** A single blind human is the pilot
  reference, not ground truth. The operator confirmed 9 of them in Mission 1.85.10; the other 7 are unreviewed.
- **How stable these calls are.** No repeatability run was authorised, so run-to-run variance is unmeasured. A
  change of a few records per label cannot be separated from sampling noise in the model.
- Anything about `NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` positives.
- Whether a different prompt, a label-definition change or a different extraction contract would do better.
- Anything about business evidence: no finding became a Signal, Claim, Evidence, Opportunity or score.

## 14. Does further prompt development appear necessary?

**Precision on `REPORTED_FAILED_ATTEMPT` is still the open problem.** Prompt 1.1.0 did not solve it and cost
recall. So prompt wording alone may not be the lever, and the next step is not obviously another prompt
revision.

The results raise these questions for the operator (none acted on):
- whether the 7 new unreviewed disagreements should get the same post-model review the first 9 received;
- whether the label definition itself, rather than its prompt operationalisation, is where the model and the
  human diverge;
- whether run-to-run variance should be measured before any further prompt change is judged.

**The next development decision is the operator's and was not made here.** No prompt 1.2.0 was prepared.

## 15. Phase 12 and 13: historical immutability and no production promotion

The following are all byte-identical and reproduce:
- Mission 1.85.9 report, evaluation and run summary;
- Mission 1.85.10 review;
- packet v4;
- the spent approval v1 and its attempt;
- prompt 1.0.0;
- the blind annotation.

Zero, verified:

| Item | Count |
|---|---|
| HOLDOUT records opened or sent | 0 (the 46 records are a subset of DEVELOPMENT, asserted by test) |
| Repeatability runs, reruns, other models or providers | 0 |
| Prompt revisions | 0 |
| Signals, Claims, Evidence, Opportunities, OpportunityRevisions, OpportunityEvidenceLinks, scores | 0 |
| Canonical writes | 0 |
| Secrets committed | 0 |
| Source text or request ids in committed artifacts | 0 (leak check: 0 of 35 returned quotes, 0 of 46 request ids) |
| N08-C work | 0 |

## 16. Artifacts

Committed:
- `semantic-extraction-evaluation-approval-development-v2.json` and `...-attempt-development-v2.json`;
- `semantic-extraction-pilot-run-development-v2.json`: the summary, with no source text;
- `semantic-extraction-pilot-evaluation-development-v2.json` and `.md`;
- `semantic-extraction-prompt-revision-diagnostics-development-v1.json` and `.md`;
- `evaluate_prompt_revision_diagnostics.py` and the V2 pilot in `evaluate_semantic_extraction_pilot.py`;
- a CI step `Semantic extraction prompt revision diagnostics are current` (artifacts only);
- roadmap N08 status `PROMPT_1_1_DEVELOPMENT_PILOT_RESULTS_READY_FOR_OPERATOR_REVIEW` (not DONE).

Not committed: the full run record and the runner console output, both outside the repository.

## 17. Tests and CI

Tests never call a provider.

New tests:
- `test_prompt_1_1_execution_rehearsal.py` (4): section 2.
- `test_prompt_revision_diagnostics.py` (4): synthetic runs, including reference-mirroring and all-ABSENT
  prompts; ids and counts only; V1 reproduces byte for byte.
- `test_prompt_1_1_run_artifacts.py` (7), from the committed artifacts:
  - the approval names exactly packet v5, one execution, and the verbatim statement;
  - the attempt and summary name v5 and its approval;
  - one clean full run within bounds, with no HOLDOUT, no repeat and no canonical writes;
  - no source text or request id;
  - the evaluation, diagnostics and V1 evaluation reproduce;
  - the comparison uses only the valid overlap;
  - a second `--execute` with the real v5 approval is refused `EVALUATION_APPROVAL_ALREADY_SPENT` before the
    key, the compose `.env` or any transport, all tripwired, and the spent v4 approval unlocks nothing.

Re-pointed, not deleted:
- 7 assertions that no v5 approval or attempt existed now assert the spent state;
- the roadmap status test accepts the new status.

CI cannot execute the provider (`test_no_workflow_executes_a_run`).

Local gates before commit: see the PR description.

**N08 is not DONE. N08-C was not started.** Any further execution needs a new packet digest and a new explicit
approval.

## Decision summary for the operator

    RFA full DEVELOPMENT: false PRESENT 16/25 (0.64), upper 0.798 -> PILOT_OUTSIDE_PROPOSED_BOUND; recall 9/15
    Known over-reads corrected: 2/9
    Positive sensitivity retained: 9/15
    Comparable v1.0 -> v1.1 false positives: 9 -> 7
    Comparable v1.0 -> v1.1 true positives: 9 -> 4
    Threshold result: RFA OUTSIDE; NEGATIVE_EVALUATION INSUFFICIENT_SUPPORT (0 PRESENT on 45, no regression)
    Actual cost: $0.4421406 of $9.000000 (4.91%)
    Execution complete/partial: complete (46/46 attempted, 45 accepted, 1 validator refusal, 0 retries)
