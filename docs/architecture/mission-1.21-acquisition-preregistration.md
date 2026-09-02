# Mission 1.21 — Acquisition pre-registration

**Committed BEFORE any issue content was inspected.** Mission 1.21 §16, the same
discipline Mission 1.20 used, and the point of a separate commit is that git
history shows the order rather than the report asserting it.

**What had been touched before this document was written**, stated exactly: two
reachability probes. `bugs.documentfoundation.org/rest/bug?...&limit=2` returned
two bug ids with their status, resolution, product and component — no summaries,
no bodies, no comments — and `api.launchpad.net/1.0/bugs/1` returned one public
bug's field list. Both were feasibility checks against §5 and §12, both are
recorded in
[`issue-identity-candidates-v1.md`](../data/issue-identity-candidates-v1.md), and
neither inspected issue content or duplicate structure.

**No duplicate-density query was run.** Choosing bounds by first asking how many
duplicates a window contains is the selection §16 forbids.

---

## 1. Source and resource

| | |
|---|---|
| Source | `documentfoundation-bugzilla` (new registration) |
| Deployment | `https://bugs.documentfoundation.org/` |
| Route | Bugzilla REST API, `/rest/bug`, no authentication |
| Resource | `bug/LibreOffice/Writer` |
| Visibility | **public bugs only** — unauthenticated Bugzilla returns no restricted bug, and no credential exists to change that |
| Data licence | CC BY-SA 4.0, stated by the deployment |

**Product `LibreOffice`, component `Writer`.** One component of one application,
chosen because it is a single clearly-scoped part of one product — the same
narrowness argument Mission 1.20 applied to a tool — and **not** because of
anything known about its duplicate rate, which was not measured.

## 2. The field allowlist, and what it excludes

```text
include_fields = id, dupe_of, product, component, status, resolution,
                 creation_time, is_open
```

**Excluded, and absent from the wire rather than dropped afterwards:**
`creator`, `creator_detail`, `assigned_to`, `assigned_to_detail`, `cc`,
`cc_detail`, `qa_contact`, `mentors`, `comments`, `attachments`, `history`,
`flags`, `see_also`, `url`, `whiteboard`, `keywords`, `groups`.

**`summary` is deliberately NOT acquired**, and this is the design decision worth
arguing rather than assuming.

§12 says to acquire a summary only if genuinely required. It is not: `dupe_of` is
the entire identity relation, and a Claim can name the canonical bug by its id
and its canonical URL. Leaving the summary behind costs nothing and buys the
strongest possible form of §26's hard negatives — **a text-similarity rule cannot
be written against this corpus because no text was acquired.** The impossibility
is structural rather than promised.

**`severity` and `priority` are not acquired either.** Nothing in the identity
relation needs them, and §20 forbids asserting severity outside source semantics;
a field that is not held cannot be misread.

## 3. Bounds, fixed now

```text
step 1   product=LibreOffice  component=Writer
         creation_time >= 2024-01-01   and < 2024-07-01
         limit 200   max_pages 2   max_records 300
         include_fields as above; no resolution or status filter

step 2   the DISTINCT non-null `dupe_of` targets named by step 1,
         fetched by id, same include_fields, capped at 300 ids and 2 requests
```

**Why no `resolution=DUPLICATE` filter**, even though §16 permits one. Filtering
to duplicates would return the duplicate side of every cluster and none of the
canonical bugs, and §23 counts a cluster from **distinct issue identities the
publisher links into one canonical identity** — so the canonical bug has to be
reachable. An unfiltered window is also the honest test of §22: whatever the
sample contains is the answer.

**Why step 2 is not a widening.** It fetches exactly the bug ids the SOURCE
itself named in step 1's `dupe_of` values. It adds no search, no new predicate
and no new window; it resolves references the first request already returned. It
is capped, and it is declared here rather than reached for afterwards.

## 4. What this pre-registration forbids for the rest of the mission

- no second window, product or component;
- no widening because no cluster appeared;
- no resolution or status filter added after seeing the result;
- no acquisition of `summary`, `comments` or any person field;
- no third request beyond the declared caps;
- no text-similarity, fuzzy-matching or model judgement of equivalence anywhere.

**If the sample contains no canonical cluster with support ≥ 2, that is outcome
S0** and it is the mission's answer.

## 5. The relation's meaning, fixed before any code

From the official Bugzilla REST documentation:

> `dupe_of` (int) — *"The bug ID of the bug that this bug is a duplicate of. If
> this bug isn't a duplicate of any bug, this will be null."*

`A.dupe_of = X` means **the publisher has classified A as a duplicate of X.** It
does not mean SROS proved they are equivalent, that the classification is
objectively correct, that two different people reported it, that many users are
affected, that the problem is severe, that it remains current, or that anyone
would pay to solve it.

**Chains are not resolved transitively in V1.** If `A → B` and `B → C`, nothing
in the retrieved documentation states that A's canonical issue is C, and §15
forbids inventing graph semantics. A chain is recorded and reported; it does not
silently collapse.
