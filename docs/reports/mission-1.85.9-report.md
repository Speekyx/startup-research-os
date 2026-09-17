# Mission 1.85.9 report: packet-scoped approval, single execution and DEVELOPMENT evaluation (N08-B-PILOT)

**Outcome: `DEVELOPMENT_PILOT_EXECUTED_PARTIAL_RESULTS_READY_FOR_OPERATOR_REVIEW`.**

Operator `operator-a` approved exactly one DEVELOPMENT pilot execution of one packet. It was recorded, validated
and executed once through the canonical runner. The run made **24 provider calls**:
- 23 records returned schema-valid answers the validator accepted;
- the 24th call hung, then failed with a network reset;
- the runner stopped as designed, keeping the partial run;
- the remaining 22 records were never attempted.

The approval is spent. **Nothing was rerun.**

Every result below is `DEVELOPMENT_PILOT` and `PILOT_NOT_CERTIFICATION`. It is measured against a
`SINGLE_HUMAN_REFERENCE`, which is the pilot reference and not absolute truth.

    packet     5f96b418e75374b098b44b7fe3ba756a5155af94f92cd607ea251fa131d18c0e  (version 4)
    approval   77cdea89eba08f768b135e099478884d82b2120f8d0fab13e5f8f018b0b48d95
    executed   2026-09-17T13:00:40+00:00 to 13:14:38+00:00, anthropic / claude-sonnet-5
    calls      24 of at most 92; 0 schema retries
    cost       $2.440713 charged of $9.000000 (27.12%), of which $0.195657 is reported usage

Start: `main` at `49e84c6`. Pre-execution freeze commit on the branch: `479a056`, pushed and verified by ref
before the approval existed.

## 1. Phase 0: immutable preflight

Recomputed from the files, not quoted. All 28 checks passed:

| Check | Result |
|---|---|
| Packet exists, version 4, status READY, blockers `[]` | ok |
| Recorded, recomputed and freshly rendered digest all equal `5f96b418...` | ok |
| Operator decisions, decision package, threshold decisions | ok |
| Retry policy rule and retry implementation (`request.py`) | ok |
| Provider verification, prompt, strict and canonical tool schemas | ok |
| Human reference, egress eligibility, threshold partition | ok |
| Cost facts: request-size file digest and every bound copied from the package | ok |
| Ceiling 9.000000; 46 approved / 4 excluded / 0 review; 46 expected / 92 max calls | ok |
| Reference strength, provider / model, HOLDOUT excluded, 0 repeatability runs | ok |
| No approval and no attempt record before this mission | ok |

The database-backed checks were also rerun against the live database: egress eligibility (46 / 4) and request
sizes (46 records) both matched. The packet did not change, so `APPROVED_PACKET_CHANGED_REAPPROVAL_REQUIRED` did
not arise.

## 2. Runner audit, before any approval

Reading the runner before approving it found gaps that would have cost the single execution. Each was fixed and
tested in the pre-execution commit `479a056`, and none touches a bound artifact (the packet digest is unchanged):

1. **The credential could never reach the runner.** It read `ANTHROPIC_API_KEY` from the process only, and never
   loaded the git-ignored compose `.env` that the V9 and V10 runners use. The runner now loads it with
   `setdefault`, **only after** the approval, provider verification, ceiling preflight, spent-attempt and
   output-directory checks. The value is never read or printed.
2. **The approval did not bind provider, model, record count or scope.** `check_approval` now requires
   `approved_provider`, `approved_model`, `approved_record_count` and
   `approval_scope = ONE_DEVELOPMENT_PILOT_EXECUTION` to equal the packet's.
3. **A response cut at `max_tokens` could be retried.** The gateway checks required keys before the runner
   reads `stop_reason`, so a truncated tool payload surfaced as a schema failure. The runner now reads the
   provider's completion signal first: `max_tokens` and refusals are never retried.
4. **A structurally incomplete finding was not retried**, although the ratified reading says it should be. The
   gateway checks only top-level keys, so a finding missing a required key reached the validator. Validator
   refusals `PAYLOAD_NOT_AN_OBJECT`, `UNKNOWN_OR_MISSING_KEY` and `UNKNOWN_EXTRACTION_STATE` are now classed as
   schema failures. No such case occurred in the run.
5. **The run record lacked what the audit needs:**
   - per-call number, retry number and elapsed time;
   - per-record surface digest;
   - validated offsets;
   - approval digest, provider, model and run timing.

   All are now recorded.
6. **An unclassified exception would have lost the run.** Any other exception now writes the partial run, charges
   the documented maximum for the call, and stops with `UNEXPECTED_ERROR`. **This path is what preserved the run.**
7. **The evaluation rules did not exist.** `evaluate_semantic_extraction_pilot.py` froze them in code before
   execution (section 7), with tests on synthetic runs.

A dress rehearsal (`test_pilot_execution_rehearsal.py`) runs `main --execute` end to end on a scripted
transport. It exercises the real approval gate, provider verification, ceiling, ADR-033 authorization, gateway,
strict adapter, validator and retry rule, including the `max_tokens` and schema-retry paths. It passed first
time.

## 3. Phase 1 and 2: approval recorded and validated

`docs/data/semantic-extraction-evaluation-approval-development-v1.json`, sha256 `77cdea89...`,
`approved_at` **2026-09-17T17:00:16+04:00** (the actual time of recording).

It names:
- packet id, version 4 and the full digest;
- `approved_by = operator-a`;
- decision `APPROVE_EXACTLY_ONE_EVALUATION_RUN` and scope `ONE_DEVELOPMENT_PILOT_EXECUTION`;
- reference strength, result scope and label;
- provider `anthropic`, model `claude-sonnet-5`, 46 records;
- ceiling `"9.000000"`;
- acceptance of the retry interpretation and of the retention bound as bound in that packet;
- a `not_authorised` list.

Statement recorded: *"This approval authorises exactly one DEVELOPMENT pilot execution of the named packet and no
other packet, split, repeatability run, HOLDOUT run, or production persistence."*

The runner's own functions validated it before any secret existed in the process:
- `verify_packet` ok;
- `check_approval` ok;
- provider verification ok;
- ceiling preflight ok;
- no attempt record;
- a wrong approval digest refused with `APPROVAL_FILE_DIGEST_MISMATCH`.

The key was absent from the environment throughout.

## 4. Phase 4: the single execution

```
run_semantic_extraction_evaluation.py --execute --approval-sha256 77cdea89... --output-dir <outside the repository>
```

- **Attempt record** written before the first request:
  `docs/data/semantic-extraction-evaluation-attempt-development-v1.json`, `ATTEMPT_STARTED` at 13:00:40 UTC,
  naming the packet and the approval.
- **Calls 1 to 23**: one record each; HTTP 200, `stop_reason tool_use`, reported usage, validator accepted.
  Latency 2.1 to 5.2 s.
- **Call 24** (record `3d0568c4...`): no response for **763 s**, then `ConnectionResetError`. The runner recorded
  it (no status, transport error class, elapsed time) and charged the documented maximum ($2.245056), because no
  usage was reported. It then stopped with `UNEXPECTED_ERROR`, writing the partial run.
- **Not attempted**: 22 records. No retry was made, and the ratified reading forbids one on a network error. The
  approval is spent. **No rerun**, and a second `--execute` is refused before the credential or any transport
  (tested).
- The full run record, which holds the model payloads and their verbatim quotes, stays outside the repository as
  the packet's logging policy requires.

Why the stop happened (recorded, not fixed here; a separate task is suggested):
- `UrllibTransport` wraps `URLError` and `TimeoutError`, but not a raw `ConnectionResetError`, so it reached the
  runner unclassified instead of as a provider error;
- `urllib`'s timeout applies per socket operation, not to the whole request, so a stalled connection outlived the
  240 s bound.

Had the reset been classified as a provider error, the ratified policy would have recorded that one record as
failed, with no retry, and continued to the next record. The conservative stop cost the pilot half its records.

## 5. Run execution

| Fact | Value |
|---|---|
| Approved / attempted / accepted / not attempted | 46 / 24 / 23 / 22 |
| Provider calls | 24 |
| Schema retries | 0 |
| Validator refusals / schema failures / provider errors / output limit / model refusals | 0 / 0 / 0 / 0 / 0 |
| Unexpected error (network reset) | 1 |
| Bounded stop | `UNEXPECTED_ERROR` |
| Run elapsed | 838.1 s |
| Call latency median / p95 (nearest rank) / max | 3.21 s / 5.17 s / 763.1 s |
| Input / output tokens reported | 68,060 / 4,175 (23 calls; any cache tokens are folded into input by the recorder, and no `cache_control` was sent) |
| Cost charged | **$2.440713** = $0.195657 reported usage + $2.245056 conservative charge for call 24 |
| Ceiling consumed | 27.12% of $9.000000 |
| Canonical writes | 0 |

Per-call charges range from $0.005775 to $0.013825. The ledger authorised every call before sending it.

## 6. Evaluation (Phase 6)

Rules from `evaluate_semantic_extraction_pilot.py@1.0.0`, committed in `479a056` before the run. Over the 46
approved records, with each record read per label as follows:
- `NOT_ATTEMPTED` or `NO_VALID_OUTPUT` when there is no accepted extraction;
- `ABSTAIN` for `ABSTAINED_TEXT_INSUFFICIENT`;
- otherwise `PRESENT` when a finding of that label was accepted, and `ABSENT` when not.

**This is a partial run.** The 23 evaluated records are the first 23 in packet order, not a random sample.

### Readings

| Item | Reading | Basis |
|---|---|---|
| `false_present_rate_upper_95::REPORTED_FAILED_ATTEMPT` | **PILOT_OUTSIDE_PROPOSED_BOUND** | 9 false PRESENT of 18 PRESENT calls on human-decided records (support 18, required 15); point 0.50; one-sided Clopper-Pearson upper 95% **0.709** against bound 0.20 |
| `false_present_rate_upper_95::NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` | PILOT_INSUFFICIENT_SUPPORT | 0 PRESENT calls (30 required) |
| `min_true_present_and_min_true_absent::REPORTED_FAILED_ATTEMPT` | PILOT_WITHIN_PROPOSED_BOUND | true PRESENT 9, true ABSENT 5 |
| `min_true_present_and_min_true_absent::NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` | PILOT_INSUFFICIENT_SUPPORT | reference PRESENT 0 |
| `mechanical_unsupported_assertions_accepted::all` | PILOT_WITHIN_PROPOSED_BOUND | 25 accepted findings, 0 whose span differs from the returned quote |
| `validator_acceptance_rate::all` | PILOT_WITHIN_PROPOSED_BOUND | 23 / 24 = 0.958 (bound 0.95); the one miss is the network reset, not a refusal |
| `unnecessary_abstention_rate_on_gold_decided::all` | PILOT_WITHIN_PROPOSED_BOUND | 0 abstentions in 46 decided cells with valid output |
| `composition_gate::REPORTED_FAILED_ATTEMPT, DEVELOPMENT` | PILOT_WITHIN_PROPOSED_BOUND | reference 15 PRESENT / 29 ABSENT |
| `composition_gate::NEGATIVE_EVALUATION_OF_NAMED_SOLUTION, DEVELOPMENT` | PILOT_INSUFFICIENT_SUPPORT | reference 0 PRESENT / 45 ABSENT (reference set insufficient) |
| `recall::REPORTED_FAILED_ATTEMPT` | descriptive, no bound | 9 / 15 = 0.60 over all 46; **all 6 misses are unattempted records**; on attempted records 9 / 9 |
| `recall::NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` | PILOT_INSUFFICIENT_SUPPORT | undefined: no reference PRESENT |
| `cost_and_latency::all` | descriptive, no bound | section 5 |
| `run_to_run_label_flip_rate` | **not evaluated** | `REJECT_FOR_THE_PILOT`, `REJECT_FOR_THIS_FIRST_PILOT`; no additional run |

No `PILOT_INSUFFICIENT_SUPPORT` is read as a pass or a fail, and no threshold moved after the results.

### REPORTED_FAILED_ATTEMPT

| | Value |
|---|---|
| Reference over 46: PRESENT / ABSENT / UNCERTAIN | 15 / 29 / 2 |
| Reference over the 23 accepted records: PRESENT / ABSENT / UNCERTAIN | 9 / 14 / 0 |
| Model: PRESENT / ABSENT / ABSTAIN / no valid output / not attempted | 18 / 5 / 0 / 1 / 22 |
| True PRESENT / false PRESENT / true ABSENT | 9 / 9 / 5 |
| Missed reference PRESENT | 6, all on unattempted records; 0 model ABSENT on a human PRESENT |
| Recall | 0.60 over 46; 1.00 on accepted records |
| False-PRESENT point estimate / upper 95 | 0.50 / 0.709 |
| Unnecessary abstention | 0 of 23 decided cells |

### NEGATIVE_EVALUATION_OF_NAMED_SOLUTION

| | Value |
|---|---|
| Reference over 46: PRESENT / ABSENT / UNCERTAIN | **0** / 45 / 1 |
| Model: PRESENT / ABSENT / ABSTAIN / no valid output / not attempted | 0 / 23 / 0 / 1 / 22 |
| True ABSENT / false PRESENT | 23 / 0 |
| Recall | undefined |
| Composition | insufficient |
| Every unsupported item | `PILOT_INSUFFICIENT_SUPPORT` |

This is the known reference limitation, not a model failure.

### Validator

- Acceptance 23 / 24.
- 0 refusals of any code.
- 25 accepted findings, every one mechanically supported: each validator span equals a quote the model returned.

## 7. Disagreements for operator review

From `semantic-extraction-pilot-evaluation-development-v1.md` (ids only, no text):

| Category | Count | Records |
|---|---|---|
| `REPORTED_FAILED_ATTEMPT` model PRESENT / human ABSENT | **9** | `17064c93`, `1a659352`, `203268d4`, `37bf2146`, `9f91eeea`, `ac423fe4`, `bf04af60`, `d6bff833`, `e35f990d` |
| `REPORTED_FAILED_ATTEMPT` model ABSENT / human PRESENT | 0 | |
| Model abstention / human decided | 0 | |
| Human UNCERTAIN | 2 (`REPORTED_FAILED_ATTEMPT`), 1 (`NEGATIVE_EVALUATION_OF_NAMED_SOLUTION`) | all on unattempted records |
| `NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` disagreements | 0 | |
| Validator refusals / schema failures | 0 / 0 | |
| Stopped (network reset) | 1 | `3d0568c4` |
| Not attempted | 22 | listed in the evaluation page |

Neither side is declared wrong. The 9 disagreements are exactly the question for the operator: did the model
over-read a failed attempt, or did the blind human annotation under-mark one? If a label is revisited after
seeing model output, that is post-model review or adjudication. It must be recorded as such, and the original
blind attestation must not be rewritten. **The annotation was not modified in this mission.**

## 8. What can be concluded

- The frozen pipeline works on real traffic:
  - the prompt, strict forced tool, provider route, validator, cost ledger and run record behaved as bound;
  - 23 of 23 answered records were schema-valid and mechanically grounded;
  - there were no abstentions, no refusals, no schema failures and no retries.
- Cost per record is far below the planning estimate: about $0.0085 per record against a planning average of
  about $0.018. The ceiling was never approached by real usage.
- On the attempted records, `REPORTED_FAILED_ATTEMPT` finds every human PRESENT (9 of 9). Half of its PRESENT
  calls fall on records the single human marked ABSENT, which puts the preregistered false-PRESENT bound clearly
  outside (upper 0.709 against 0.20), with more than the required support.
- `NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` made no PRESENT call on 23 records the human marked ABSENT.

## 9. What cannot be concluded

- Nothing about the 22 unattempted records, or whether the readings would hold over all 46. The 23 are the first
  in packet order, not a sample.
- Nothing certified: no inter-human reliability, no consensus gold, no HOLDOUT generalisation, no production
  readiness, no calibrated semantic accuracy.
- Whether the 9 disagreements are model errors or reference errors; a single human is not ground truth.
- Anything about `NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` positives (none in the reference) or repeatability (not
  evaluated).
- Anything about business evidence: no finding became a Signal, Claim, Evidence, Opportunity or score.

## 10. Is the extractor promising enough for another development iteration?

**Yes for the machinery, with a precision problem to understand first.** Structure, grounding, abstention and
cost are all good. The live question is precision on `REPORTED_FAILED_ATTEMPT`: 9 model-PRESENT / human-ABSENT
cases in 23 records.

Before any new run, the operator's review of those 9 cases decides the next step:
- if the human reference holds, the label definition in the prompt needs tightening;
- if some cases are ambiguous, the label definition itself needs a decision.

Separately:
- the transport defect (unclassified reset, per-operation timeout) should be fixed so that one network failure
  costs one record rather than half the run;
- any further run needs a new packet digest and a new explicit approval.

## 11. Artifacts and boundaries

Committed:
- the approval and the attempt record;
- `semantic-extraction-pilot-run-development-v1.json`: the run summary with no source text; quotes are digests
  and offsets, request ids are digests, and a leak check found 0 of 25 quotes and no request id;
- `semantic-extraction-pilot-evaluation-development-v1.json` and `.md`;
- the evaluator, a CI step `Semantic extraction pilot evaluation is current` (reads artifacts only), and the
  roadmap N08 status.

Not committed: the full run record and the runner console output, both outside the repository.

Zero, verified:
- HOLDOUT records opened;
- repeatability runs;
- reruns;
- other models or providers;
- prompt revisions;
- Signals, Claims, Evidence, Opportunities or scores;
- canonical writes;
- secrets committed;
- N08-C work.

## 12. Tests and CI

Tests never call a provider: the new ones read the committed artifacts, or use scripted transports and synthetic
runs.

New tests:
- `test_pilot_execution_rehearsal.py` (3): the full `main --execute` rehearsal, a second execution refused
  before any transport, and an in-repository output directory refused before the credential loads;
- `test_pilot_evaluator.py` (4): Clopper-Pearson against the rule of three; reference-mirroring,
  constant-PRESENT, constant-ABSTAIN and all-refused runs; summaries carrying no source text;
- `test_pilot_run_artifacts.py` (6), from the committed artifacts:
  - the approval names exactly the approved packet and one execution;
  - the attempt and summary name this packet and approval;
  - one run within bounds, no HOLDOUT, no repeat, no canonical writes;
  - no source text or request id committed;
  - the evaluation reproduces byte for byte;
  - a second `--execute` with the real approval is refused before the key, the compose `.env` or any transport,
    all tripwired.

Re-pointed, not deleted: five Mission 1.85.8 assertions that no approval or attempt existed now assert the spent
state (one approval naming this packet, an attempt record, other digests refused). The approval matrix gained the
provider, model, count and scope cases.

Local gates before commit:

| Gate | Result |
|---|---|
| `ruff format --check` / `ruff check` / `mypy` | 1249 files / all passed / no issues in 242 files |
| Zero-dependency runner | 3981 tests |
| pytest semantic-extraction / llm-gateway / orchestrator | 78 / 171 (2 skipped) / 97 |
| pytest inferred-claim-evaluator / evidence-reliability / roadmap / acquisition | 2470 / 352 / 87 / 134 |
| Egress eligibility and request-size `--check` (database) | ok |
| Every `--check` step in `ci.yml` | 101 run, 0 flagged |
| The 7 CI validators | all ok |

CI: see the PR. The added CI step reads committed artifacts only, and no CI step can execute the runner.

**N08 is not DONE.** The next step is the operator's review of these results. Any further execution needs a new
packet digest and a new explicit approval.
