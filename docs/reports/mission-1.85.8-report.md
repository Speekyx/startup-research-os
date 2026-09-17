# Mission 1.85.8 report: record operator decisions and freeze the ready packet (N08-B-PILOT)

**Outcome: `READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL`.**

The operator's explicit decisions are recorded exactly as given, validated strictly, and bound into a frozen
DEVELOPMENT evaluation packet:
- 9 pilot thresholds authorised;
- the run-to-run flip rate rejected for this first pilot;
- the retry reading ratified;
- the $9.000000 hard ceiling accepted.

Every non-operator gate was already satisfied, so the packet is now `READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL`.

    packet    semantic-extraction-evaluation-packet-development, version 4
    sha256    5f96b418e75374b098b44b7fe3ba756a5155af94f92cd607ea251fa131d18c0e

**NO EXECUTION HAS BEEN AUTHORISED.** Recording decisions, re-rendering and merging grant no provider or model
execution authority. The next action is a separate, explicit operator approval naming this exact digest.

Start: `main` at `dfb81ab`.

Counters for this mission:
- provider calls 0;
- model inferences 0;
- API key reads 0;
- Stack Overflow text sent anywhere 0;
- `run_semantic_extraction_evaluation.py --execute` invocations from a shell 0;
- approval files created 0;
- attempt records created 0;
- HOLDOUT records opened 0;
- model predictions, AI provisional annotations and semantic findings 0;
- Signals, Claims and Evidence 0;
- N08-C: not started.

## 1. Recorded decisions

Operator id: `operator-a`. Timestamp `decided_at`: **`2026-09-17T15:37:35+04:00`**. It is the actual local
timezone-aware time at which the decisions were written, not an earlier one.

File: `docs/data/semantic-extraction-operator-decisions-development-v1.json`, sha256
`ac2bb1d977f0f7fb9ffaa133aa9564f93b7c499b15956f4b06ad1bef2ba94994`. Its `$comment` now says the decisions are
the operator's own, transcribed on their instruction, and authorise no run.

### A. Pilot thresholds

| Item | Decision | Revised value | Note recorded |
|---|---|---|---|
| `false_present_rate_upper_95::NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` | `AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT` | none | zero reference PRESENT; `PILOT_INSUFFICIENT_SUPPORT` is an acceptable expected outcome; authorisation does not turn insufficient evidence into success |
| `false_present_rate_upper_95::REPORTED_FAILED_ATTEMPT` | `AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT` | none | none |
| `min_true_present_and_min_true_absent::each extractable label` | `AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT` | none | NEGATIVE_EVALUATION_OF_NAMED_SOLUTION cannot satisfy the PRESENT half and may yield insufficient support |
| `mechanical_unsupported_assertions_accepted::all` | `AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT` | none | kept at 0 |
| `validator_acceptance_rate::all` | `AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT` | none | kept at 0.95 |
| `unnecessary_abstention_rate_on_gold_decided::all` | `AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT` | none | kept at 0.10; metric id not renamed; "gold" means the single-human decided reference, as preregistered |
| `run_to_run_label_flip_rate::each extractable label` | **`REJECT_FOR_THE_PILOT`** | none | `repeatability_disposition = REJECT_FOR_THIS_FIRST_PILOT`; single pinned execution; repeatability later under separately approved runs; no additional model calls; the metric stays in future methodology |
| `composition_gate::each extractable label, each split` | `AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT` | none | min_present 4 and min_absent 4 kept, not weakened; NEGATIVE_EVALUATION_OF_NAMED_SOLUTION expected insufficient |
| `recall::each extractable label` | `AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT` | none | descriptive only; zero reference PRESENT reports undefined or insufficient, not 0 |
| `cost_and_latency::all` | `AUTHORISE_FOR_THE_SINGLE_HUMAN_PILOT` | none | descriptive operational measurements, not quality criteria |

The three notes the brief did not supply (items 2, 4 and 5 beyond "keep") were not invented: item 2 has none, and
items 4 and 5 record only the kept value.

### B. Retry

`operator_decision = RATIFY`, `revised_reading = null`. The ratified reading, recorded in `operator_note`:
- at most ONE retry per record;
- retry ONLY if the forced-tool payload is missing, invalid against the strict schema, or structurally incomplete;
- no retry on a deterministic validator refusal, an HTTP, provider or network error, a timeout, a provider
  refusal, `max_tokens`, or a schema-valid answer that looks incorrect;
- no provider fallback and no model fallback.

### C. Hard ceiling

`operator_decision = ACCEPT`, `accepted_hard_ceiling_usd = "9.000000"` (a string, which is what the package
and the runner compare), `revised_hard_ceiling_usd = null`.

Basis recorded: 46 approved, 46 expected calls, 92 maximum calls, planning $0.838035, conservative $3.032986,
retry worst case $6.065972, accepted $9.000000. The old $206.5452 bound is not used.

## 2. Strict validation, before any rendering

`sros_semantic_extraction.decisions.decision_record_problems` is new. It refuses a decision record, and never
repairs it, when:
- a made decision has no `decided_by`, or its `decided_at` is not a timezone-aware ISO timestamp;
- a threshold, retry or ceiling decision is outside its vocabulary;
- a threshold item appears twice;
- `REVISE` has no revised value, or a revised value is present without `REVISE`;
- the repeatability item has no disposition, a `REJECT` carries a disposition other than
  `REJECT_FOR_THIS_FIRST_PILOT`, or another item carries a disposition;
- a retry `REVISE` has no revised reading, or a revised reading is present without `REVISE`;
- an `ACCEPT` names a ceiling other than the proposed string, or carries a revised ceiling.

`operator_decision_blockers` now reports every such problem as `OPERATOR_DECISIONS_INVALID`, so a malformed
record can never produce a READY packet. The earlier check only looked at the disposition when the flip rate
was authorised; a rejection is now checked too.

A mission-specific script then compared the file with the brief, value by value, before anything was rendered:
10 items, 10 resolved, 9 authorised, flip rate rejected with its disposition, no revised value, retry exactly
`RATIFY`, ceiling exactly `ACCEPT` `"9.000000"`, `decided_by = operator-a`, timezone-aware `decided_at`.

Result: **0 problems, 0 operator-decision blockers.** Nothing needed repair, so nothing was changed.

## 3. Re-render

| Artifact | Change |
|---|---|
| `semantic-extraction-operator-decision-package-development-v1.json` | `decision_state` now mirrors the recorded decisions: operator, timestamp, each threshold decision and disposition, retry and ceiling decisions, accepted ceiling, and `record_problems` (empty). Facts unchanged. sha256 `9001c4ec...` |
| `semantic-extraction-operator-decision-package-development-v1.md` | shows the recorded decisions instead of hard-coded "blank" |
| `semantic-extraction-evaluation-packet-development-v1.json` | version 3 to **4**, mission 1.85.8; new `retry_policy` block; `operator_decisions` extended; status READY; blockers `[]` |
| `run_semantic_extraction_evaluation.py` | `EXPECTED_PACKET_SHA256` re-pinned from `63c7302d...` to `5f96b418...` |
| `business-evidence-acquisition-roadmap-v1.json` | N08 mission 1.85.8, status `READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL`, phase `N08-B-PILOT-FREEZE`; not DONE |

The packet gains two bindings the brief asked for:
- **`retry_policy`**: id `semantic-extraction-schema-failure-retry-policy`, version 1.0.0, the reading, the
  in-class and out-of-class lists, `implemented_as`, `provider_fallback` and `model_fallback` null, the
  operator's decision, `rule_sha256` over the rule, and `implementation_sha256` of
  `sros_semantic_extraction/request.py` (where `may_retry` and `MAX_SCHEMA_RETRIES_PER_RECORD` live). Changing
  the rule or its implementation changes the packet digest.
- **`operator_decisions`**: `decided_by`, `decided_at`, the threshold decisions alone with their own
  `threshold_decisions_sha256`, the authorised and rejected lists, retry and ceiling decisions, the accepted
  ceiling, and `additional_repeatability_runs_authorised: 0`.

Every `--check` renderer passes after the re-render (section 8).

## 4. The frozen packet

**Packet SHA-256: `5f96b418e75374b098b44b7fe3ba756a5155af94f92cd607ea251fa131d18c0e`** (version 4).

| Bound fact | Value |
|---|---|
| Status | `READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL`, blockers `[]` |
| Reference | `SINGLE_HUMAN_REFERENCE` / `DEVELOPMENT_PILOT` / `PILOT_NOT_CERTIFICATION`; holdout not included and not permitted |
| Provider / model | `anthropic` / `claude-sonnet-5`, forced strict tool, thinking disabled, max 4096 output tokens, 240 s, 0 transport retries, no fallback |
| Records | 46 `EGRESS_APPROVED`, 4 `EGRESS_EXCLUDED`, 0 review required |
| Calls | 46 expected, 92 maximum |
| Cost | planning $0.838035, conservative $3.032986, retry worst case $6.065972, one documented-maximum call $2.245056 |
| Accepted hard ceiling | **$9.000000** (`hard_ceiling_usd_approved`) |

Bound digests:

| Binding | sha256 |
|---|---|
| Retry policy rule (`semantic-extraction-schema-failure-retry-policy@1.0.0`) | `1515359ed300780c1a9668b71d772ca592a44cc1ae4938ea5aac01a628480105` |
| Retry implementation (`request.py`) | `329106a02627bad1d0922105c6ea9c40c5d1e0e14b9a3c9b50d6b0948c314c3d` |
| Threshold decisions | `2cbae12aa1eb6341d2b2109951dfad170e14de927a00a2d88109cc3ec3cbe0b3` |
| Operator decisions file | `ac2bb1d977f0f7fb9ffaa133aa9564f93b7c499b15956f4b06ad1bef2ba94994` |
| Decision package | `9001c4ecf1d65c366cbbf4ece3ae09a25454dede000db6e95f66f33485da0d0b` |
| Provider verification | `342d9a537ba49465f412b6686f9e03dcef4a0f39617972dd2738d472e6d717ce` |
| Prompt (`first-person-semantic-extraction-prompt@1.0.0`) | `53bcc87f0c761f28326bdbeda37e1018a5e2e3ff71711d9705c3542f940221b9` |
| Tool strict schema | `f7f7683018b081ca95b846e61017a5c8e14844aca8c3f1d78061f37053a99382` |
| Tool canonical schema | `2724bcdfbac72ee300f9c31601e6ad75bb846fed52e4214e6163bfd17333518a` |
| Human reference (`operator-a` annotation) | `449ff10f8a60217bbf4b7887254cf81b492fdba962b39283f39d2acdf1a9fa3c` |
| Egress eligibility | `299ebc0bbdc115d1d7250cb53e5426541ac195879e35658ac317d6efe1258640` |
| Threshold partition | `6b6ff60fa238c9b890dd881fc81f641241ec8bdc3b3e7f186cd32f4652029ccf` |

The packet digest covers every field except `$comment`, `packet_sha256` and `status_note`. A test shows that
changing the decisions file by one second of `decided_at`, or appending one byte to the retry implementation,
changes the digest.

## 5. Why READY is honest

Every other gate was already satisfied and is recomputed on every render:
- one valid human annotation file and no refused file (`SINGLE_HUMAN_REFERENCE`);
- 46 approved records and 0 still under review;
- cost facts cover exactly the approved set;
- provider verification `VERIFIED`, model `ACTIVE`, prices established, within its 180-day interval.

Only the operator-decision blockers were left, and they are now empty. A test proves the status still flips to
`BLOCKED_OPERATOR_DECISIONS` when a single other gate fails (unestablished pricing), or when the decisions are
blank.

## 6. The runner still cannot execute

- **No approval exists.** `docs/data/semantic-extraction-evaluation-approval-development-v1.json` is absent, and
  so is the attempt record. No file matching `semantic-extraction-evaluation-approval*` exists.
- **Without an approval the runner refuses** before any key, transport or attempt record:
  - `--execute` with no digest: `APPROVAL_SHA256_NOT_SUPPLIED`;
  - `--execute --approval-sha256 <any>`: `OPERATOR_APPROVAL_NOT_RECORDED`.

  The test replaces `os.environ` with a tripwire that fails on any read of `ANTHROPIC_API_KEY`, and
  `UrllibTransport.__init__` with one that fails if a transport is built. Neither fires, and no attempt record
  appears.
- **A stale approval cannot execute.** An approval naming the previous digest `63c7302d...` is refused with
  `OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET`, whether it names version 3 or version 4. So is an approval naming
  the new digest with the old version.
- **Only the exact digest passes the approval gate.** A synthetic approval written to a pytest temporary
  directory (never the repository) naming `5f96b418...`, version 4 and the accepted `"9.000000"` passes
  `check_approval`. The same approval naming $206.5452 is refused. The test calls `check_approval` only; it never
  calls `execute` or `main` with an approval.
- **Merging grants nothing.** `operator_approval_recorded` is false, `approval_requirements.merge_is_not_approval`
  is true, and the approval must name `packet_sha256`.

A dry run (`run_semantic_extraction_evaluation.py` without `--execute`) printed the v4 digest and status and
exited 0: "no transport was built and nothing was sent".

## 7. A defect found on the way, and fixed at its cause

The first local run of the semantic-extraction suite stopped on
`test_egress_review_server.py::TestBoundary::test_a_foreign_host_or_missing_token_is_refused` with
`ConnectionAbortedError: [WinError 10053]`. The full suite passed straight after, and the test passed 15 times out
of 15 on its own. That was not taken as a fix.

The cause is in `infrastructure/scripts/semantic_egress_review.py`. Every POST refusal (421, 403, 415, 404)
answered without reading the request body. On Windows, closing a socket that still holds unread request bytes
sends a reset, and the client can lose the refusal it was sent. That is a race, so it shows up only sometimes.

`do_POST` now reads the bounded body (at most 1 MB, as before) before any answer. Behaviour is otherwise
unchanged, and the server still binds loopback only. The egress server file then passed 5 of 5 runs.

## 8. Tests and gates

Local, before commit:

| Gate | Result |
|---|---|
| `ruff format --check` / `ruff check` | 1242 files formatted / all checks passed |
| `mypy` over the 16 CI packages | no issues in 242 source files |
| Zero-dependency runner | 3981 tests across 10 packages |
| `pytest` semantic-extraction | 65 passed |
| `pytest` llm-gateway / research-orchestrator | 171 passed, 2 skipped / 97 passed |
| `pytest` inferred-claim-evaluator / evidence-reliability | 2470 passed / 352 passed |
| Roadmap and N08 ontology-fit tests | 87 passed |
| Acquisition document tests | 134 passed |
| Egress eligibility and request-size `--check` (database) | ok: 46 approved, 4 excluded; 46 records |
| Every `--check` step in `ci.yml` | 100 run, 0 flagged |
| The 7 CI validators | all ok |

After the version entries (manifest 1.173, `docs/CLAUDE.md` 1.174), everything that reads those files was run
again and passed:
- zero-dependency runner, 3981 tests;
- inferred-claim-evaluator 2470 and evidence-reliability 352;
- semantic-extraction 65;
- roadmap 87 and acquisition 134;
- 100 `--check` steps with 0 flagged.

Test changes:
- **re-pointed, not deleted**, because they asserted the pre-decision state:
  - `test_the_committed_decisions_are_blank_and_nothing_decided_them` became
    `test_the_committed_decisions_are_exactly_the_operators`;
  - `test_unresolved_decisions_keep_the_packet_blocked` now renders a packet from an in-memory blank decisions
    file and still gets `BLOCKED_OPERATOR_DECISIONS`;
  - `test_the_committed_packet_verifies_and_is_blocked` now asserts READY with no blockers;
  - `test_execute_refuses_a_blocked_packet_before_reading_an_approval` keeps its property with a blocked copy of
    the packet;
  - the two "committed packet cannot execute" tests now expect the approval refusals, with the key and
    transport tripwires above;
  - the roadmap test admits `READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL`, and still refuses DONE;
- **new** (`TestRecordedDecisionsAndFrozenPacket`, 8 tests):
  - 11 malformed decision records are each refused;
  - 9 thresholds authorised, flip rate rejected, 0 additional runs;
  - retry ratified and bound by digest;
  - READY only when every other gate holds;
  - any bound artifact change moves the digest;
  - a previous-digest approval is invalid;
  - only the exact digest passes the approval gate;
  - merge grants nothing.

CI: CI_PLACEHOLDER

## 9. What this mission did not do

- It did not create an approval file or any equivalent.
- It did not run `--execute` from a shell or read an API key.
- It did not call Anthropic, send Stack Overflow text anywhere, or open HOLDOUT.
- It did not create model predictions, AI provisional annotations, semantic findings, Signals, Claims or Evidence.
- It did not start N08-C.
- It did not weaken any threshold, rename any metric, or double the budget.
- N08 is not DONE.

**NO EXECUTION HAS BEEN AUTHORISED.** The next action is a separate explicit operator approval naming packet
`5f96b418e75374b098b44b7fe3ba756a5155af94f92cd607ea251fa131d18c0e`.
