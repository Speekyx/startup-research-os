# Mission 1.85.11 report: REPORTED_FAILED_ATTEMPT precision revision and the next DEVELOPMENT packet (N08-B-PILOT)

**Outcome: `READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL`.**

The precision problem the pilot demonstrated is corrected **in the extraction prompt only**:
- the label meaning, the tool schema, the other label, the thresholds, the retry policy and the cost ceiling are
  unchanged;
- prompt `first-person-semantic-extraction-prompt@1.1.0` adds a three-anchor procedure for
  `REPORTED_FAILED_ATTEMPT`, and 1.0.0 is frozen.

The next DEVELOPMENT packet is rendered, and **no approval exists for it**:

    packet   semantic-extraction-evaluation-packet-development, version 5
    sha256   6b27bccbc22c7051be9d8f1df4dd22a4635d0f664d4b4fa05ede820e90a72a7e
    status   READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL, blockers []

Counters for this mission:
- provider calls 0;
- model inferences 0;
- Stack Overflow text egress 0, including into this agent's own context;
- reruns 0;
- HOLDOUT records opened 0;
- new AI annotations 0;
- Signals, Claims, Evidence and Opportunities created 0;
- approvals created 0.

Start: `main` at `23bb1ee`.

## 1. Historical evidence preserved (Phase A)

Verified before any change and again after:

| Artifact | State |
|---|---|
| Blind annotation `...operator-a-v1.json` | sha256 `449ff10f...`, unchanged |
| Mission 1.85.9 evaluation | `evaluate_semantic_extraction_pilot.py --check` ok, sha256 `da468421...`; reading `PILOT_OUTSIDE_PROPOSED_BOUND` |
| Mission 1.85.10 review | `semantic_disagreement_review.py check` ok, COMPLETE, `390caada...` |
| Review counts | 9 `HUMAN_REFERENCE_CONFIRMED_MODEL_OVERREAD`; 0 revision; 0 ambiguous |
| Packet v4 | `...packet-development-v1.json`, file `0fbc4357...`, packet `5f96b418...`: frozen, no longer re-rendered, checked by digest |
| Approval `77cdea89...` and its attempt record | frozen and spent |
| Package v1, request sizes v1 | frozen, checked by digest |
| PR #185 transport repair | present (`OSError`/`HTTPException` wrapped; total deadline) |

**How history is kept while the current artifacts move on.** Everything that depends on the prompt is written to
new files:
- request sizes v2;
- decision package v2;
- packet `...-v2.json` (version 5);
- the runner's approval and attempt paths, now `-v2`.

The v1 files are pinned by digest in the renderers' `--check`, which now fails if any of them changes.

The review tool's frozen-definition reader was pointed at `prompt_v1_0_0.py`. It extracts the identical text, so
its label-definition digest (`41905c88...`) and the review's `check` are unchanged.

## 2. The finding that motivates the change

The operator reviewed all nine `REPORTED_FAILED_ATTEMPT` model-PRESENT / blind-ABSENT disagreements after seeing
the model's quotes, and confirmed the blind ABSENT on all nine. No case was a human under-marking, and none was
ambiguous under the frozen definition.

The first correction is therefore operational precision in the instructions, not a redefinition.

## 3. Failure-mode analysis (Phase C), aggregate only

`analyse_rfa_precision_patterns.py` reads the frozen surfaces locally and rebuilds each quote from committed
offsets, verifying its digest. It computes coarse deterministic features and commits **counts only**:
`semantic-extraction-rfa-failure-mode-analysis-development-v1.json`.

No text entered this agent's context: only these counts were printed.

| Feature (share of quotes) | Over-reads (13 quotes, 9 records) | Model on reference positives (12) | Human reference spans (15) |
|---|---|---|---|
| explicit "tried/attempted/tested" verb | 3 | 2 | **9** |
| error token | **7** | 2 | 3 |
| error with no attempt language | **3** | 1 | **0** |
| inside a code or quoted region | **3** | 3 | **0** |
| attempt and failure language in one quote | 5 | 3 | 5 |
| desire or goal phrasing | 0 | 0 | 5 |

Abstract taxonomy, which changes no label:
1. **Error or log material standing in for an attempt.** The model quoted error output or code, which the human
   reference never used as the evidence.
2. **Implicit attempts.** Ordinary usage, a setup or a state description was read as a tried remedy, without
   explicit attempt language.
3. **Inferred link.** The failure was tied to an action by position or context rather than by the asker's own words.

These are coarse English regular expressions over a small sample. They point at the instruction's weakness and
establish nothing about any individual record.

## 4. Why the label definition was not changed (Phase B)

`first-person-semantic-labels@1.0.0` and its canonical `REPORTED_FAILED_ATTEMPT` definition are byte-identical
(tested). There were no human revisions and no ambiguities, so the review supplies no evidence against the
definition, only against how the prompt operationalised it.

The prompt is now stricter than the validator: the label set still permits code evidence (`evidence_may_be_in_code`).
That is deliberate. The validator stays the structural gate, and no contract or schema change was needed.

## 5. The prompt revision (Phase D, F)

Only the `REPORTED_FAILED_ATTEMPT` block changed. Everything before it, the whole
`NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` block, `WHAT NEVER COUNTS`, `HOW TO ANSWER` and the task instructions are
byte-identical (tested).

The 1.0.0 sentence *"The evidence may be error output inside a code block."* is removed, and this text is added
after the unchanged definition sentences:

```text
Report it only when the asker's own words establish all three:
A. ATTEMPT: the asker performed or tried a concrete action (a command, change, configuration, workaround, procedure or other specific step).
B. FAILURE: that action did not achieve what the asker intended (it failed, gave a wrong result, had no effect, or produced an error).
C. LINK: the text itself ties that failure to that same action.
If A, B or C is only implied, or needs inference from context or from the order of text, code and errors, it is not established: produce no REPORTED_FAILED_ATTEMPT finding.
None of these is an attempt on its own: wanting or asking how to do something; using or having a tool, library or configuration; code shown in the question; a description of the current state or environment; an error, log or stack trace with no stated attempt. By themselves, statements like "I am using X", "I have X configured", "My app gives error Y", "X behaves like Y", "How can I make X do Y?" and "Why does X do Y?" do not count.
Error output may support FAILURE but never establishes ATTEMPT. The evidence_quote must be the shortest contiguous passage of the asker's own words that shows both the attempted action and its failure; an error message or a code block alone is not enough. When in doubt, produce no finding for this type.
Invented illustrations: "I tried clearing the cache and restarting, but the page still shows the old version" counts. "I am on version 3 and get a timeout error" does not. "How do I turn the cache off?" does not.
```

| Prompt | Version | sha256 |
|---|---|---|
| historical, frozen in `prompt_v1_0_0.py` | 1.0.0 | `53bcc87f0c761f28326bdbeda37e1018a5e2e3ff71711d9705c3542f940221b9` |
| current, `prompt.py` | **1.1.0** | `a4b96eb3b92d19573bd008fd8690df11fa5e0638f50ffa95d36845415448dde7` |

The system region grew by 1,477 characters. The bias is toward precision: *"When in doubt, produce no finding for
this type."*

## 6. Evidence representation audit (Phase E)

On the 15 blind-reference PRESENT spans over the 46 approved records:
- every record is a single span;
- the longest span is 366 characters, against a quote maximum of 400;
- 0 spans exceed the maximum, and 0 records need a window over it.

Every legitimate reference positive fits one contiguous quote of 8 to 400 characters, so **the tool schema is
unchanged** (strict `f7f76830...`). No `RFA_EVIDENCE_REPRESENTATION_DECISION_REQUIRED`. The prompt's evidence
rule (the shortest passage showing both attempt and failure) is therefore expressible.

## 7. Regression specification (Phase H)

`semantic-extraction-rfa-regression-spec-development-v1.json` (sha256 `20e6da82...`) holds ids and surface digests
only, and is bound into packet v5:

| Set | Records | Desired next-run behaviour | Reported as |
|---|---|---|---|
| `KNOWN_OVERREAD` | 9 (the Mission 1.85.10 reviewed records) | `REPORTED_FAILED_ATTEMPT` is not PRESENT | records still PRESENT, records without valid output |
| `POSITIVE_SENSITIVITY` | 15 (every approved blind-reference PRESENT) | positives are still found; precision is not bought by answering ABSENT | true PRESENT, missed PRESENT, recall, descriptive |

`is_threshold: false`, `is_certification: false`, `rewrites_mission_1_85_9: false`, `sent_to_provider: false`.

**Positive-sensitivity safeguards (Phase H):**
- the preregistered pilot thresholds are unchanged and still apply, including
  `min_true_present_and_min_true_absent`, which an all-ABSENT answer fails;
- the positive-sensitivity set is reported separately so that a precision gain cannot hide a recall collapse.

No new threshold was invented.

## 8. Anti-overfitting controls (Phase I)

- The prompt contains none of the regression ids, 8-character prefixes or surface and findings digest prefixes;
  it does not say "misclassified" or "previous run" (tested).
- The added text is general. Its three illustrations are invented. A local check of all 318 five-word sequences of
  the revised block found 0 in any of the 50 DEVELOPMENT surfaces (HOLDOUT not opened).
- The regression set lives only in the offline specification and the future evaluation.

## 9. Request size and cost (Phase K)

Measured offline exactly as in Mission 1.85.7, with the runner's own prompt, strict tool and body builder. No
token-counting call. File `semantic-extraction-request-size-development-v2.json`, sha256 `55fdbe78...`.

| | v1 (prompt 1.0.0) | v2 (prompt 1.1.0) |
|---|---|---|
| Request body bytes, total | 322,746 | **391,884** |
| median / p95 / max | 6,237.5 / 10,747 / 20,532 | 7,740.5 / 12,250 / 22,035 |
| Per-record delta | | **+1,503 bytes on every one of the 46** |

| Cost fact (package v2) | v1 | v2 |
|---|---|---|
| EXPECTED_CALLS / MAX_CALLS_WITH_RETRY | 46 / 92 | 46 / 92 |
| Planning estimate | $0.838035 | $0.898863 |
| Conservative one-pass bound | $3.032986 | $3.185090 |
| Retry worst case | $6.065972 | $6.370179 |
| One documented-maximum call | $2.245056 | $2.245056 |
| Proposed hard ceiling | $9.000000 | **$9.000000** |

Retry worst case plus one maximum call is $8.615235, within the operator's accepted $9.000000. **The ceiling is kept,
and there is no `COST_CEILING_REDECISION_REQUIRED`.** The operator decisions file is unchanged (`ac2bb1d9...`) and
validates against package v2 with 0 problems and 0 blockers.

## 10. The next DEVELOPMENT packet (Phase J, L, M)

Packet **version 5**, file `docs/data/semantic-extraction-evaluation-packet-development-v2.json`:

**Packet SHA-256: `6b27bccbc22c7051be9d8f1df4dd22a4635d0f664d4b4fa05ede820e90a72a7e`**

| Bound fact | Value |
|---|---|
| Status | `READY_FOR_PACKET_SCOPED_OPERATOR_APPROVAL`, blockers `[]` |
| Scope | the same 46 EGRESS_APPROVED DEVELOPMENT records, 4 excluded; a clean full run, not a resumption of records 24 to 46 |
| Reference | `SINGLE_HUMAN_REFERENCE` / `DEVELOPMENT_PILOT` / `PILOT_NOT_CERTIFICATION`; HOLDOUT excluded |
| Provider / model | `anthropic` / `claude-sonnet-5` (verification `342d9a53...`, unchanged) |
| Prompt | 1.1.0 `a4b96eb3...` |
| Tool | unchanged: strict `f7f76830...`, canonical `2724bcdf...` |
| Retry policy | unchanged: rule `1515359e...`, implementation `329106a0...` |
| Threshold decisions / operator decisions | `2cbae12a...` / `ac2bb1d9...` (unchanged) |
| Decision package | v2 `c4c72ff3...` |
| Egress eligibility | `299ebc0b...` (unchanged) |
| Calls | 46 expected, 92 maximum; 0 repeatability runs |
| Accepted ceiling | $9.000000 |
| `supersedes` | packet v4 `5f96b418...` and approval `77cdea89...` (`SPENT_BY_THE_MISSION_1_85_9_ATTEMPT`); Mission 1.85.9 result unchanged |
| `development_diagnostics` | regression spec `20e6da82...`, post-model review `390caada...`; not a threshold, not sent to the provider |

The runner is re-pinned to `6b27bccb...` and its approval and attempt paths are the `-v2` files. **No approval file
exists** for version 5.

Operator decisions carried forward: the pilot thresholds, the ratified retry reading and the accepted $9.000000
ceiling are reused. Nothing they depend on changed: the same items, the same retry policy, and a ceiling the new
cost still fits. `run_to_run_label_flip_rate` stays rejected, and the next run is, again, a single execution with no
repeatability run.

## 11. The spent approval cannot unlock the new packet

Tested:
- `check_approval(packet v5, approval-v1, 77cdea89...)` is refused with
  `OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET`;
- `main --execute` with the old digest is refused with `OPERATOR_APPROVAL_NOT_RECORDED`, because no v2 approval
  exists;
- pointed at the old approval file, `main --execute` is refused with `OPERATOR_APPROVAL_DOES_NOT_NAME_THIS_PACKET`;
- all of these refusals happen before the key, the compose `.env` or any transport.

## 12. Tests and CI

`packages/semantic-extraction/python/tests/test_prompt_revision.py` has 12 tests:
- **Prompt versions:** 1.0.0 frozen at `53bcc87f...`; 1.1.0 is a new digest bound in the packet.
- **Unchanged meaning:** the label-set definition is byte-identical; everything outside the RFA block, the
  `NEGATIVE_EVALUATION_OF_NAMED_SOLUTION` semantics and its subject requirement, and the task instructions are
  unchanged.
- **Revised procedure:** the three anchors; inference refused; error alone, state or configuration alone and
  how-to alone are insufficient; the six guardrail patterns; the evidence rule requiring attempt plus failure; the
  1.0.0 error-evidence sentence gone.
- **No leakage:** no regression id, prefix or digest in the prompt.
- **History:** the blind annotation, 1.85.9 evaluation, 1.85.10 review, v4 packet, spent approval, sizes v1 and
  package v1 are byte-for-byte unchanged, and the evaluation and review still reproduce.
- **New packet:** a new digest, READY, superseding v4, with no approval; the spent approval refused.
- **Sizes and cost:** they use prompt 1.1.0 with a uniform positive delta; the package binds sizes v2 and the packet
  binds package v2; the ceiling is kept and fits.
- **Regression spec:** 9 plus 15 records, offline, not a threshold, bound and current.
- **Scope:** records, model, tool, retry, reference and repeatability unchanged.
- **Analysis artifact:** counts only; the evidence audit shows 0 over the quote maximum.
- **No provider:** the runner dry run and the renderers run with a tripwire on the provider transport.

Re-pointed, not deleted: six earlier tests that treated the v1 approval, attempt and packet as current now assert
them as history, and assert that version 5 has none.

A new CI step, `Semantic extraction RFA regression specification is current`, reads artifacts only. The packet and
package `--check` steps now also fail if any frozen v1 artifact changes.

Local gates are recorded in the PR.

**Next:** a separate, explicit operator approval naming packet
`6b27bccbc22c7051be9d8f1df4dd22a4635d0f664d4b4fa05ede820e90a72a7e`. Until then, nothing is executed.
