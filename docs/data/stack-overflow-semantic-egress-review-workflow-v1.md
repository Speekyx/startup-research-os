# Stack Overflow semantic egress review workflow (v1)

Mission 1.85.6. How the human operator decides, record by record, whether the exact DEVELOPMENT surface may
be transmitted to the approved inference provider.

Policy `REVIEW_OR_EXCLUDE_NO_REDACTION` is defined in `sros_semantic_extraction_contract.egress` and is
unchanged:
- a pattern trigger is a reason to look, never a finding that personal data exists;
- zero triggers does not mean safe;
- only a `HUMAN_OPERATOR` decision approves;
- a deterministic transport-integrity rule may only exclude, and it dominates any human choice;
- nothing is redacted, rewritten or masked;
- every decision is bound to the exact `surface_sha256`, and a decision bound to another surface derives back
  to `EGRESS_REVIEW_REQUIRED`;
- `EGRESS_REVIEW_REQUIRED` is derived, never recorded.

The tooling makes no decision. It records the choices the operator clicks.

## 1. Prepare (needs `DATABASE_URL`)

```
uv run python infrastructure/scripts/semantic_egress_review.py prepare --out C:\sros-egress\operator-a --operator-id operator-a
```

- The folder must be outside the repository. It receives:
  - `review-material.json`, which holds the exact surfaces and trigger matches of every record whose derived
    state is `EGRESS_REVIEW_REQUIRED`;
  - an empty working file, `egress-decisions-working-<operator>.json`.
- A mechanically excluded record is not offered.
- An existing working file is never overwritten.

## 2. Review in the local page (no database)

```
uv run python infrastructure/scripts/semantic_egress_review.py serve C:\sros-egress\operator-a
```

Open `http://127.0.0.1:8765/`.

**How the page is protected**
- The server binds 127.0.0.1 only and refuses a request whose Host is not loopback.
- It requires a per-session token on every API call.
- It sends a Content-Security-Policy with `default-src 'none'` and `connect-src 'self'`.
- It loads no external script, style, font or image, and logs no request.

**What each record shows**
- The header: position (`12 / 49`), `normalized_record_id`, shortened `surface_sha256`, surface length, and
  the trigger summary by category.
- The exact surface that would be transmitted, unaltered, with trigger matches highlighted locally.
- A trigger table: pattern, line, and the matched text with its surrounding context.

**Decisions**
- Approve:
  - `EGRESS_APPROVED / TRIGGER_REVIEWED_NOT_PERSONAL`;
  - `EGRESS_APPROVED / TRIGGER_REVIEWED_PUBLIC_REFERENCE`, which is disabled for a record with a
    `secret_like` trigger.

  For a zero-trigger record, only `TRIGGER_REVIEWED_NOT_PERSONAL` is offered, meaning the operator read the
  surface and found nothing personal. No new reason exists.
- Exclude: `EGRESS_EXCLUDED` with `CONTAINS_PERSONAL_IDENTIFIER`, `CONTAINS_SECRET_LIKE_VALUE` or
  `OPERATOR_DISCRETION`.
- Undo is available.

Each click is saved at once, with `decision_origin = HUMAN_OPERATOR`, the operator id, a timestamp and the
exact surface digest. Stop the server and serve again to resume.

**Optional zero-trigger bulk.** The "Zero-trigger set" screen lists every undecided zero-trigger record with
its digest and the `record_set_sha256`. Nothing is accepted until the operator types the exact confirmation
sentence and clicks.
- The server refuses a set that contains a triggered record, or that is not exactly the current zero-trigger
  set.
- A record in the bulk set cannot also have an individual decision.

Deciding each zero-trigger record individually is equally valid.

## 3. Lint (needs `DATABASE_URL`)

```
uv run python infrastructure/scripts/semantic_egress_review.py lint C:\sros-egress\operator-a\egress-decisions-working-operator-a.json
```

Lint re-scans the held records and prints every problem. It never repairs anything. It checks:
- the split and holdout: DEVELOPMENT only, no holdout id;
- the working format, scan version, pattern-table digest, surface version and policy;
- the operator id: non-empty and not model-like;
- the reviewable set;
- per decision: the surface digest, a human origin, `decided_by` matching the operator, a timezone-aware
  timestamp, and a recordable decision with a compatible reason;
- the `secret_like` rule;
- bulk decisions: sorted ids, set digest, reason, confirmation, coverage, zero triggers;
- no record decided both individually and in bulk;
- no persisted `EGRESS_REVIEW_REQUIRED`.

## 4. Import (needs `DATABASE_URL`)

```
uv run python infrastructure/scripts/semantic_egress_review.py import C:\sros-egress\operator-a\egress-decisions-working-operator-a.json
```

Import refuses unless lint passes and every reviewable record is decided. It then:
1. merges the decisions into `docs/data/stack-overflow-semantic-egress-decisions-development-v1.json`, keeping
   ids, digests, states, reasons, origin, operator and time, but no surface text and no confirmation
   sentence;
2. rebuilds the scan and eligibility;
3. re-renders the evaluation packet.

The runner pin then has to be updated in a reviewed commit. Exclusions are a complete answer: nothing needs to
be approved.

Merging decisions authorises no provider call. The packet stays blocked on the remaining operator decisions.
