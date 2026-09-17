# Mission 1.85.6 report: local egress review interface and human decision import (N08-B-PILOT)

**Outcome: `WAITING_FOR_HUMAN_EGRESS_REVIEW` at merge of the tooling (#180), then `EGRESS_REVIEW_COMPLETE_OPERATOR_DECISIONS_REMAIN` after the operator's review was imported (§7).**

The operator can now review every DEVELOPMENT record that needs an egress decision in a local page, and import
the result through a strict validator. The tooling is complete. No egress decision has been made: the operator
has not reviewed the records yet, and this mission does not review them in their place.

Egress is therefore not complete. The committed decision file is unchanged (no decision), eligibility is
unchanged, and the packet is unchanged: status `BLOCKED_OPERATOR_DECISIONS`, digest `894d8532...`.

Start: `main` at `b422b76`.

Counters for this mission:
- provider calls 0;
- model inferences 0;
- Stack Overflow text egress 0;
- egress decisions made by any tool, agent or model 0;
- human decisions imported 0;
- AI annotations 0;
- holdout records opened 0;
- human reference annotation changes 0;
- thresholds authorised 0;
- ceiling accepted: no;
- approvals created 0;
- production findings, Signals, Claims and Evidence 0.

## 1. Current egress state, recomputed

`build_semantic_egress_eligibility.py --check` passes on current `main`, and the counts match Mission 1.85.4.

| Quantity | Value |
|---|---|
| DEVELOPMENT records | 50 |
| Mechanically excluded (`SURFACE_CONTAINS_TRANSPORT_DELIMITER`) | 1 |
| Human-approved | 0 |
| `EGRESS_REVIEW_REQUIRED` | 49 |
| Records with at least one trigger (all 50) | 22 |
| of which the excluded record | 1 |
| Review-required records with a trigger | 21 |
| Review-required records with zero triggers | 28 |
| Review-required records with a `secret_like` trigger | 3 |

**Triggers by category**, as matches and as records with at least one match:

| Category | Matches | Records |
|---|---|---|
| `url` | 23 | 12 |
| `url_with_userinfo` | 1 | 1 |
| `email_like` | 1 | 1 |
| `ipv4_like` | 12 | 8 |
| `ipv6_like` | 0 | 0 |
| `user_home_path` | 17 | 3 |
| `at_handle` | 14 | 3 |
| `long_token_like` | 8 | 4 |
| `secret_like` | 5 | 3 |

These are review triggers. None is a finding that a record contains personal data.

## 2. How the interface works

`infrastructure/scripts/semantic_egress_review.py` wraps the pure module
`sros_semantic_extraction_contract/egress_review.py`. The policy stays in `egress.py`, and eligibility is still
derived only by `derive_egress_eligibility`. The workflow is documented in
`docs/data/stack-overflow-semantic-egress-review-workflow-v1.md`.

```
prepare -> serve (local page) -> working decision file -> lint -> import -> rebuilt eligibility and packet
```

**`prepare --out DIR --operator-id ID`**
- Refuses a folder inside the repository, a placeholder or model-like operator id, and an existing working
  file.
- Reads the held records, recomputes the scan, and selects the records whose derived state is
  `EGRESS_REVIEW_REQUIRED`. The mechanically excluded record is never offered.
- Writes `review-material.json` (exact surfaces, trigger matches with context, surface segments for
  highlighting) and an empty working file.

**`serve DIR`**
- Uses `http.server` from the standard library.
- **Network:**
  - bound to `127.0.0.1`, with no host option;
  - refuses a request whose Host is not loopback (421);
  - requires a per-session token on every API call (403) and JSON on every POST (415).
- **Page protections:** CSP `default-src 'none'` with nonce scripts and styles and `connect-src 'self'`, no
  referrer, no caching, and no request logging.
- **Page content:** no external asset of any kind, no CDN and no third-party JavaScript. It shows:
  - progress `n / 49`;
  - the record id, shortened digest, surface length and trigger summary;
  - the complete exact surface, labelled as the transmitted surface and unaltered, with matches highlighted
    locally;
  - a trigger table with pattern, line and matched text in context.
- **Decision buttons** exist only for the contract's recordable pairs:
  - two approving reasons, with `TRIGGER_REVIEWED_PUBLIC_REFERENCE` disabled on a `secret_like` record;
  - three excluding reasons;
  - for a zero-trigger record, only `TRIGGER_REVIEWED_NOT_PERSONAL` is offered as the approving reason, and
    no new reason was introduced.
- **Saving:** every click calls `make_decision`, which applies the contract's rules. The result is saved
  atomically to the working file with `decision_origin = HUMAN_OPERATOR`, the operator id, a timestamp and
  the surface digest. Undo is available.
- **The optional zero-trigger bulk screen:**
  - lists the undecided zero-trigger records, their digests and the `record_set_sha256`;
  - records nothing until the operator types the exact sentence "I reviewed exactly these N zero-trigger
    records and approve them" and clicks;
  - refuses a set with a triggered record, or a set that is not exactly the current zero-trigger set.
- **Resume:** closing and serving again restores every saved choice. Undecided records stay undecided, and a
  decision bound to a different digest is shown as stale and does not count.

**`lint WORKING` and `import WORKING`** re-scan the held records and call `validate_working_decisions`, which
refuses and never repairs. It checks:
- the split: DEVELOPMENT only, no holdout id;
- the working format, scan version, pattern-table digest, surface version and policy;
- the operator id;
- the reviewable set;
- the surface digest of every decision;
- a human origin, with `decided_by` equal to the operator;
- a timezone-aware timestamp;
- decision and reason compatibility;
- the `secret_like` rule;
- the bulk set: sorted ids, digest, reason, confirmation, coverage, zero triggers;
- no record decided both individually and in bulk;
- no persisted `EGRESS_REVIEW_REQUIRED`.

`import` also requires every reviewable record to be decided. It then:
1. merges the decisions into `docs/data/stack-overflow-semantic-egress-decisions-development-v1.json`, keeping
   ids, digests, states, reasons, origin, operator and time, with no surface text and no confirmation sentence;
2. re-parses the merged document with `egress.load_decisions`;
3. rebuilds the scan and eligibility;
4. re-renders the packet.

**On the real data**, after `prepare` into `C:\sros-egress\operator-a`:
- `prepare` reported 49 records, 21 with triggers and 28 without;
- `lint` reported the working file valid with 49 undecided;
- `import` refused with `REVIEW_INCOMPLETE` (49 records without a human decision) and wrote nothing.

The page was exercised in the local browser on a **synthetic** folder only:
- one individual decision;
- a bulk click refused as `BULK_CONFIRMATION_MISSING`;
- a confirmed bulk of the synthetic zero-trigger pair;
- no console error.

The real review material was not displayed to the assistant.

## 3. Human decisions imported

None. The operator has not yet reviewed the 49 records. Final counts are unchanged:

```
EGRESS_APPROVED        = 0
EGRESS_EXCLUDED        = 1   (mechanical, transport delimiter)
EGRESS_REVIEW_REQUIRED = 49
```

No placeholder approval was created. When the operator finishes, `import` will produce
`EGRESS_REVIEW_REQUIRED = 0`, with whatever split between approved and excluded the operator chose. Excluding
every record is a complete answer.

## 4. Proof no text left the machine

- **No network client:** `semantic_egress_review.py` imports no network client (`urllib`, `http.client`,
  `socket`, `requests`, `httpx`), no provider SDK and no gateway. A test asserts this from the syntax tree.
- **Loopback only:** the only listening socket is `http.server` on `127.0.0.1`, and a test asserts both the
  bound address and the absence of any all-interfaces literal or host option.
- **No outside requests from the page:** it contains no `http://`, `https://`, `src=`, `<link`, `@import` or
  CDN reference, and its CSP forbids any connection but to itself.
- **No model call:** no provider call was made and no approval or attempt file exists
  (`semantic-extraction-evaluation-approval-development-v1.json` and
  `semantic-extraction-evaluation-attempt-development-v1.json` are absent, asserted by test).
- **Review material stays local:** it lives only in `C:\sros-egress\operator-a` and the session scratchpad
  (synthetic). The repository diff contains no surface text.

## 5. Packet blocker state

The packet is unchanged: `BLOCKED_OPERATOR_DECISIONS`, `packet_sha256` `894d8532...`, with four blockers:
1. `EGRESS_REVIEW_PENDING` (0 approved, 1 excluded, 49 review required);
2. `THRESHOLDS_NOT_AUTHORISED` for the single-human pilot thresholds, whose values are unchanged from Mission
   1.85.5;
3. `RETRY_INTERPRETATION_NOT_RATIFIED`;
4. `COST_CEILING_NOT_ACCEPTED`.

**The retry reading** is kept as the proposed operator direction and is neither recorded as ratified nor used:
- at most one retry, and only on an invalid forced-tool or schema payload;
- no retry on a validator refusal, a provider or network error, or a schema-valid answer that looks wrong;
- no provider fallback.

After a complete import, only the egress blocker can disappear. The packet will not become READY while the
other three remain.

## 6. Tests

**New unittest `packages/semantic-extraction-contract/python/tests/test_egress_review.py`** (14 tests,
synthetic surfaces): a prepared file holds no decision, zero triggers are listed and never decided, and no
decision is built in a loop.

| Requirement | Test |
|---|---|
| deterministic exclusion dominates a human approval | `test_deterministic_exclusion_dominates_a_human_approval` |
| bulk needs the exact confirmation | `test_bulk_needs_the_exact_confirmation_sentence` |
| triggered records cannot enter bulk | `test_a_triggered_record_cannot_enter_a_zero_trigger_bulk` |
| secret-like needs individual `TRIGGER_REVIEWED_NOT_PERSONAL` | `test_secret_like_approval_needs_an_individual_not_personal_review` |
| stale digest refused, and derives back to review-required | `test_a_stale_surface_digest_is_refused` |
| import refuses HOLDOUT | `test_holdout_is_refused` |
| invalid decision and reason pairs refused, not repaired | `test_invalid_decision_reason_combinations_are_refused_not_repaired` |
| origin, operator, timestamp and duplicate checks | `test_origin_operator_timestamp_and_duplicates_are_checked` |
| every record decided gives 0 review-required | `test_every_record_decided_leaves_nothing_review_required`, `test_exclusion_is_a_complete_answer` |

**New pytest `packages/semantic-extraction/python/tests/test_egress_review_server.py`** (9 tests, a real
loopback server on synthetic material):

| Requirement | Test |
|---|---|
| loopback bind | `test_the_server_binds_loopback_only` |
| no external network path or asset | `test_no_external_network_path_or_asset` |
| prepare refuses a folder inside the repository | `test_prepare_refuses_a_directory_inside_the_repository` |
| foreign host and missing token refused | `test_a_foreign_host_or_missing_token_is_refused` |
| no decision without an action | `test_no_decision_appears_without_an_action` |
| resume preserves choices | `test_a_click_is_saved_and_survives_a_restart` |
| server refuses what the contract refuses | `test_the_server_refuses_what_the_contract_refuses` |
| bulk needs confirmation and zero triggers | `test_bulk_needs_explicit_confirmation_and_zero_triggers` |
| the packet still cannot execute | `test_the_committed_packet_is_not_ready_and_no_approval_exists` |

**Local runs before the pull request**, with CI as the merge gate:
- `ruff check`, `ruff format --check` and `mypy` on the contract package: clean;
- bare runner: 3980 tests across 10 packages, all passing;
- pytest `packages/semantic-extraction`: 34 passed (25 existing, 9 new);
- pytest `packages/opportunity-engine`: 4096 passed;
- pytest `services/research-orchestrator`: 97 passed;
- `build_semantic_egress_eligibility.py --check`: ok, with `EGRESS_EXCLUDED` 1 and `EGRESS_REVIEW_REQUIRED` 49;
- all 99 `--check` render commands named in `ci.yml`: current;
- suites that read `docs/CLAUDE.md` or the roadmap, rerun after the version entries, one package at a time:
  inferred-claim-evaluator 2470, evidence-reliability 352, opportunity-engine roadmap 31, acquisition 134, all
  passing.

## 7. Operator review completed and imported

After the tooling merged (#180), the operator reviewed all 49 records in the local page. The assistant did not
view the review material, the surfaces or the working file content. It ran:
- `lint`: `ok the working file is valid; complete`;
- `import`: 49 individual decisions and 0 bulk decisions, all `decision_origin = HUMAN_OPERATOR` and
  `decided_by = operator-a`, each bound to its surface digest.

**Eligibility, rebuilt deterministically:**

```
EGRESS_APPROVED        = 46   (28 TRIGGER_REVIEWED_NOT_PERSONAL, 18 TRIGGER_REVIEWED_PUBLIC_REFERENCE)
EGRESS_EXCLUDED        = 4    (2 CONTAINS_PERSONAL_IDENTIFIER, 1 CONTAINS_SECRET_LIKE_VALUE, both human;
                               1 SURFACE_CONTAINS_TRANSPORT_DELIMITER, deterministic)
EGRESS_REVIEW_REQUIRED = 0
```

The mechanically excluded record stays excluded. Every approved record carries a human origin, and every
approved record with a `secret_like` trigger has basis `TRIGGER_REVIEWED_NOT_PERSONAL`, as asserted by
`TestCommittedDevelopmentDecisions`. The committed decision file holds ids, digests, states, reasons, origin,
operator and time, and no surface text.

**Packet.** It was re-rendered to `packet_sha256` `9040fd62...` and the runner pin was updated.
- The `EGRESS_REVIEW_PENDING` blocker is gone.
- The status stays `BLOCKED_OPERATOR_DECISIONS`, with three blockers:
  1. `THRESHOLDS_NOT_AUTHORISED` (single-human pilot thresholds);
  2. `RETRY_INTERPRETATION_NOT_RATIFIED`;
  3. `COST_CEILING_NOT_ACCEPTED`.
- The execution bounds now reflect 46 approved records:
  - `max_calls` 92, one call plus at most one schema retry per record;
  - planning estimate $2.5435;
  - hard ceiling $206.5452, every call at the full context window.
- No approval or attempt file exists.

**Outcome after import: `EGRESS_REVIEW_COMPLETE_OPERATOR_DECISIONS_REMAIN`.** Roadmap N08 moves to that status
and is not DONE.

Still 0 provider calls and 0 egress: approval to transmit is a precondition for a future run, not a run.

## 8. Next

The remaining operator decisions are the single-human pilot thresholds, the retry ratification and the hard
ceiling acceptance. Then comes a separate packet-scoped approval of exactly one run.

**Do not call a provider, change an egress decision without a new review, open holdout, or treat the pilot as
certification.**
