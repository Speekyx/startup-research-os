# Mission 1.85.16 report: single-operator reread without a mandatory delay (N08-B-PILOT)

**Outcome: `SINGLE_OPERATOR_REREAD_READY_NO_MANDATORY_DELAY`.**

This mission changes one protocol decision: when the reread may start. Nothing else moves.

    protocol          single-operator-adjudication-protocol@1.1.0 (supersedes 1.0.0 for future rereads)
    delay             minimum_delay_policy NO_MANDATORY_DELAY  (1.0.0: MANDATORY_24_HOURS_AFTER_LAST_POST_MODEL_DECISION)
    decided by        operator-a, Mission 1.85.16
    output            still SINGLE_HUMAN_ADJUDICATED_REFERENCE; no stronger blindness claimed
    provider calls    0      model inferences 0      HOLDOUT records 0      canonical writes 0

## 1. The previous policy

Protocol 1.0.0 (Mission 1.85.15) required the reread to start no earlier than 24 hours after the operator's last
post-model decision, which gave 2026-09-19T23:57:02+04:00. The requirement was enforced twice:
- `reread` refused to ask anything before that time;
- `import-reread` refused a pack that started earlier (`REREAD_STARTED_BEFORE_THE_MINIMUM_DELAY`).

## 2. The operator's decision

For this DEVELOPMENT-only workflow, operator-a removed the mandatory wait. They accept that:
- the reread is not blind to prior model exposure, and is not a second annotation;
- the output stays SINGLE_HUMAN_ADJUDICATED_REFERENCE, which is not consensus, inter-human reliability or
  certification, and does not replace the original blind annotation;
- the prior model exposure is still disclosed.

Their reason: the delay only lets memory fade, and for this workflow waiting 12 to 24 hours costs more than it
buys. **Removing it claims no stronger blindness**; `claims_stronger_blindness: false` is recorded.

## 3. Why it has no effect on Claude or any model

The delay governed when a human may start relabelling. No model runs anywhere in this protocol: not in the
reread, not in the adjudication, not in the reference build. The prompt, the extraction contract, packet v5 and
every approval are unchanged, and no request is sent. A test asserts that neither the protocol module nor the
script imports a provider, gateway, socket or HTTP client.

## 4. The methodological trade-off

What is lost is memory decay. A reread made soon after the reviews will recall them more, so reread-versus-original
agreement may be higher than a delayed one would show. That number is already labelled intra-rater, one person's
consistency, and is never reported as reliability. The remaining protections are unchanged, and the adjudication
step shows every reading explicitly anyway.

## 5. Protocol 1.0.0 against 1.1.0

| | 1.0.0 (historical) | 1.1.0 (current) |
|---|---|---|
| minimum delay | 24 h after the last post-model decision | none (`NO_MANDATORY_DELAY`) |
| pack field | `earliest_permitted_start` | `minimum_delay_policy` |
| `reread` start | refused before the earliest time | immediate |
| import | refuses an earlier start | no time rule; the actual start time is still required and timezone-aware |
| committed reread | carries `earliest_permitted_start` | carries `protocol_decision` (who, when, why, supersedes 1.0.0) |

**1.0.0 is not rewritten.** Its constant, its `earliest_reread` rule and its validation branch are kept. A 1.0.0
pack still validates only under its own delay, which a test proves. The Mission 1.85.15 report gains a
supersession note and nothing else.

**The start time is still recorded.** `annotation_started_at` is written when the form opens and must be
timezone-aware at import, as before. Only its use as a gate is gone. The reading identifier
`SAME_OPERATOR_DELAYED_REREAD` is kept for continuity; the delay itself is now carried by `minimum_delay_policy`.

## 6. Every other control is unchanged

Each item below is asserted by a test:
- all 46 EGRESS_APPROVED DEVELOPMENT records, only the two extractable labels;
- a fresh deterministic order, different from the original;
- no previous label, evidence span, review decision or model answer in the pack or its folder;
- the original form: no default, no bulk path, every pasted quote checked, resume;
- the attestation still requires `prior_model_exposure_acknowledged`, and still refuses blind attestation keys;
- the committed reread is `blind_to_model_outputs: false` and `is_a_second_annotator: false`;
- adjudication rules, reference labelling and intra-rater reporting are unchanged;
- the original blind annotation `449ff10f...` is byte for byte unchanged.

## 7. The prepared pack had to be regenerated

The pack prepared in Mission 1.85.15 was bound to protocol 1.0.0 and carried
`earliest_permitted_start: 2026-09-19T23:57:02+04:00`. It held 0 decisions.

It was **not patched**. The folder was moved aside to `%TEMP%\sros-reread-v1.0-superseded` (not deleted), and a
new pack was prepared under 1.1.0 in `%TEMP%\sros-reread`: 46 records, 0 decisions, no start time yet. The tools
now refuse a 1.0.0 pack by name for both `reread` and `import-reread` and tell the operator to prepare a new one.

## 8. Start the reread now

From the repository root. No database is needed:

```powershell
uv run python infrastructure/scripts/single_operator_adjudication.py reread "$env:TEMP\sros-reread\reread-pack-operator-a.json"
```

`q` stops, and running the same command resumes. After the reread comes `import-reread` (with `DATABASE_URL`),
then `prepare-adjudication`, `adjudicate` and `import-adjudication`, as in the Mission 1.85.15 report.

## 9. Tests and CI

`test_single_operator_adjudication.py`, now 24 tests:
- **new:** the reread starts immediately and records its start; a 1.0.0 pack is refused, never patched; an
  immediate reread (28 seconds after the last review) validates; `import-reread` accepts it and records
  `NO_MANDATORY_DELAY`, the non-blind flags and the disclosure; 1.0.0 keeps its own delay rule;
- **changed:** the early-start refusal case became the missing-start and naive-start timestamp cases.

The CI step `Single-operator adjudication is consistent with what is committed` is unchanged. Every CI gate command,
mypy, and the pytest suites of the touched packages were run before commit.

## 10. What was not done

0 provider calls, 0 inferences, 0 reruns, 0 HOLDOUT records, 0 packets, 0 approvals, 0 Signals, Claims, Evidence
or Opportunities. No change to label definitions, prompts 1.0.0 or 1.1.0, the extraction contract, annotation or
adjudication rules, the original blind annotation, the Mission 1.85.10 and 1.85.13 reviews, packet v5 or any
threshold. N08-C was not started, and the reread was not performed.
