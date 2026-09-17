# Mission 1.85.10 report: post-model operator review of the 9 REPORTED_FAILED_ATTEMPT disagreements (N08-B-PILOT)

**Outcome: `WAITING_FOR_POST_MODEL_OPERATOR_REVIEW`.**

The review tooling is ready, and the operator's review folder is prepared outside the repository. **No choice is
recorded**: only the operator can make one, in the local page, and has not yet.

Counters for this mission:
- provider calls 0;
- model inferences 0;
- HOLDOUT records opened 0;
- reruns 0;
- new AI annotations 0;
- Signals, Claims, Evidence and Opportunities created 0.

The blind annotation is byte-for-byte unchanged. No evaluation packet, approval, prompt or threshold was created
or changed.

Start: `main` at `a861682` (Mission 1.85.9 and the PR #185 transport repair).

## 1. The nine disagreements

The set is **derived, not typed**. It is every accepted pilot extraction that marked `REPORTED_FAILED_ATTEMPT`
PRESENT on a record the blind single-human reference marked ABSENT. The derivation is computed from the committed
run summary and annotation, then checked against the committed evaluation's list; any difference refuses.

| # | normalized_record_id | Blind reference | Model | Model quotes |
|---|---|---|---|---|
| 1 | `17064c93-71cf-5474-ba7f-39ccd516782f` | ABSENT | PRESENT | 2 |
| 2 | `1a659352-390f-5c53-97de-0f725d017f46` | ABSENT | PRESENT | 2 |
| 3 | `203268d4-baf6-5410-a001-cf77843e96e3` | ABSENT | PRESENT | 1 |
| 4 | `37bf2146-b9fc-5e5a-b35b-d59f5f6bfc57` | ABSENT | PRESENT | 1 |
| 5 | `9f91eeea-25e6-5a9e-89e6-54d4490ecd7c` | ABSENT | PRESENT | 1 |
| 6 | `ac423fe4-a4b4-589d-ac49-96932ed51d54` | ABSENT | PRESENT | 1 |
| 7 | `bf04af60-1364-5fd0-8f4f-a8104d131aff` | ABSENT | PRESENT | 2 |
| 8 | `d6bff833-780d-55d3-a5ad-1effebb8a328` | ABSENT | PRESENT | 1 |
| 9 | `e35f990d-117a-59d1-b54e-5165632378bf` | ABSENT | PRESENT | 2 |

None of the nine carries an original note.

## 2. Workflow

```
semantic_disagreement_review.py prepare --out <outside the repository> --operator-id operator-a   (done)
semantic_disagreement_review.py serve <folder>        the operator reviews the 9 records
semantic_disagreement_review.py lint <working file>   checks the choices against fresh inputs
semantic_disagreement_review.py import <working file> writes the committed review
semantic_disagreement_review.py check                 CI: the committed review still binds and reproduces
```

**Model quotes without the out-of-repository run file.** The committed run summary already holds each accepted
finding's offsets and the sha256 of its text. `prepare` cuts each quote from the frozen DEVELOPMENT surface and
refuses if its digest differs. All 13 quotes matched. The full run record is neither read nor copied.

**What the local page shows**, for each record:
- the complete exact surface, with the model's quotes highlighted;
- a card headed `BLIND HUMAN REFERENCE — DO NOT EDIT` with the ABSENT state and whether a note existed;
- the model result: PRESENT, each quote with its offsets, line and 300 characters of context on each side;
- the frozen definition in effect during the run, quoted from the repository and never re-written:
  - the label-set definition (`first-person-semantic-labels@1.0.0`);
  - the prompt's REPORTED_FAILED_ATTEMPT paragraph and its "WHAT NEVER COUNTS" list
    (`first-person-semantic-extraction-prompt@1.0.0`);
  - the annotation holder rule (quoted, attributed, negated or hypothetical text is ABSENT).

**How choices are made:**
- four choices, with no default and no bulk path:
  - `HUMAN_REFERENCE_CONFIRMED_MODEL_OVERREAD`;
  - `POST_MODEL_HUMAN_REVISION` (note required);
  - `LABEL_DEFINITION_AMBIGUOUS` (note required);
  - `UNRESOLVED`;
- every click is saved at once, with undo and resume;
- a note repeating 40 or more consecutive characters of the question is refused, so no source text reaches the
  committed review through a note.

**Boundary:**
- `127.0.0.1` only, with a Host check, a session token and a nonce-based CSP;
- no external asset and nothing logged;
- the material and working file live outside the repository, and `prepare` and `serve` refuse a folder inside it.

## 3. Provenance separation

`sros_semantic_extraction_contract.post_model_review` defines the review class:
- `provenance = POST_MODEL_OPERATOR_REVIEW`, `blind = false` on every decision and on the committed review;
- `replaces_original_reference = false`;
- a working file or review carrying `no_model_output_seen`, `no_model_assistance_used`, `attestation` or
  `reference_origin` is refused (`BLIND_ATTESTATION_NOT_PERMITTED`), and so is any other provenance;
- the original `stack-overflow-semantic-annotations-development-operator-a-v1.json` is only ever read.

Its sha256 is `449ff10f...` before and after, and it keeps its blind attestation (`no_model_output_seen: true`),
which remains true of that file.

**Binding.** Every review binds:
- packet `5f96b418...`;
- approval `77cdea89...`;
- run summary `d9c9a0c0...`;
- pilot evaluation `da468421...`;
- blind annotation `449ff10f...`;
- label definition `first-person-semantic-labels@1.0.0` (definition text digest `41905c88...`);
- prompt `53bcc87f...`.

Every decision binds its record's surface digest and a digest of the model's accepted findings for the label
(ids, offsets and text digests). A changed input makes the review `STALE`, never silently carried forward.

## 4. Counts and recommendations

**Not yet available.** No choice is recorded:

```text
HUMAN_REFERENCE_CONFIRMED_MODEL_OVERREAD = 0
POST_MODEL_HUMAN_REVISION               = 0
LABEL_DEFINITION_AMBIGUOUS              = 0
UNRESOLVED / undecided                  = 9
```

The recommendation rule was frozen in code before any choice existed, and applies only when all nine carry a
resolved choice:
- a choice **dominates** when its count is the largest of the three, ties giving each;
- dominant overread gives `PROMPT_OR_EXTRACTION_CONTRACT_PRECISION_REVISION_REQUIRED`;
- dominant revision gives `REFERENCE_REVIEW_OR_ADJUDICATION_REQUIRED`;
- dominant ambiguity, or ambiguity on at least a third of the records, gives `LABEL_DEFINITION_DECISION_REQUIRED`.

Several may apply. **Nothing is revised automatically.**

On completion, `import` also writes a `POST_MODEL_REVIEW_DIAGNOSTIC`, explicitly marked as post hoc, not
preregistered, not the Mission 1.85.9 gate result and not certification. It recomputes the false-PRESENT rate with
post-model revisions counted as PRESENT, once with ambiguous cases counted as false PRESENT and once with them
excluded.

## 5. Mission 1.85.9 is unchanged

- `semantic-extraction-pilot-evaluation-development-v1.json` is still sha256 `da468421...`, and
  `evaluate_semantic_extraction_pilot.py --check` still passes.
- The preregistered reading stays **`PILOT_OUTSIDE_PROPOSED_BOUND`**: 9 false PRESENT of 18, one-sided upper 95%
  0.709 against 0.20, against the blind single-human reference.
- The committed review records that reading in `mission_1_85_9_gate_unchanged`. No post-model result can turn it
  into a pass.

## 6. Transport repair verified (PR #185)

`b4cd404` is on `main`:
- `UrllibTransport.post_json` wraps `OSError` (other than timeouts) and `http.client.HTTPException` as
  `TransportError`, which the Anthropic adapter maps to a retryable `ProviderTemporaryError`;
- the exchange runs on a worker thread, bounded by a total deadline checked before every body read, and raises
  `TimeoutError` past it.

Its 12 tests passed locally. They use a loopback socket server, and `urlopen` is patched only to rewrite https to
http. Covered cases:
- resets before and during the response;
- a raw reset from `urlopen` and from `read`;
- a trickling body and trickling headers;
- a silent server;
- the adapter's mapping of a reset and of the deadline.

No provider was called to verify it. **The transport repair and the semantic review are separate concerns**, and
neither authorises a rerun.

## 7. Not done, deliberately

- No new evaluation packet, approval, rerun of the remaining 22 or of all 46.
- No prompt, threshold or label-definition change.
- No edit to the blind annotation.
- No HOLDOUT, no production persistence, no N08-C.

## 8. Tests and CI

`packages/semantic-extraction/python/tests/test_post_model_review.py`, 14 tests. No provider, model or database:

- **Unchanged inputs:** the blind annotation and the pilot evaluation are byte-for-byte unchanged, the evaluation
  still reproduces, and the gate reading is still `PILOT_OUTSIDE_PROPOSED_BOUND`.
- **Review set:** exactly the nine exact ids, bound to the packet, approval, evaluation, annotation and label
  definition, with 13 findings; the frozen definition is quoted.
- **Server boundary:** the page binds `127.0.0.1` and refuses a foreign Host (421) and a missing token (403); the
  page references no external URL.
- **No automatic choice:** repeated reads create no decision, and there is no bulk endpoint.
- **Scope:** a record outside the review set cannot be decided.
- **Saving and binding:**
  - a click is saved;
  - `NOTE_REQUIRED` is enforced;
  - a wrong surface or findings digest is refused;
  - choices resume after a restart, and undo works;
  - a decision carries provenance, `blind: false` and `decided_by`.
- **Notes:** a note pasting the question is refused.
- **Provenance:** a disguised blind attestation or a relabelled provenance is refused.
- **Staleness:** a changed binding or surface digest makes the review `STALE`.
- **Completeness:** an unresolved or partial review stays `INCOMPLETE` and derives no recommendation.
- **Recommendation rule:** dominant overread, dominant revision, a tie, and substantial ambiguity.
- **Committed review:** a complete review reproduces through `check`, carries no quote or surface text, labels its
  diagnostic post hoc and non-preregistered, and a tampered decision fails `check`.
- **No provider:** the review scripts import no network or provider client, and the whole review flow runs with a
  tripwire on the provider transport.

Local gates are recorded in the PR. The new CI step, `Semantic extraction post-model review is current`, reads
committed artifacts only.

**Next:** the operator opens the local page and reviews the nine records. Nothing else starts before that review.
