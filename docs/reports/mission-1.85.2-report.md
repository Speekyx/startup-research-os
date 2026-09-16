# Mission 1.85.2 report: evidence aggregation independence-level safety repair (roadmap N05)

**Outcome: `N05_REPAIRED_ALGORITHM_1_1_0`.** Levels 2 and 3 now count only `INDEPENDENT` groups. No mass,
saturation, score, count, warning or explanation moved; no level rose; the 112 evidence rows are unchanged
and all `UNKNOWN`. Mission 1.85.2 fixes N05 and nothing else.

Start: `main` at `053f1b1`. No network, no provider or model call, no source retrieval or review, no catalog
change, no collector, no new evidence, no independence writer, no dependence detector, no persistence
mutation, no scoring profile activation, no calibration, no Opportunity #2, no V11, no Mission 1.84 gate
reopened. Four read-only agents (A semantics, B adversarial, C reproducibility and history, D documentation);
the main agent was the only writer.

## 1. Root cause

`levels.py` built the Level 2 and Level 3 counts from every support group that was not the unknown bucket:

```python
independent_groups = [g for g in support_groups if g.kind is not GroupKind.UNKNOWN]
```

`independence.py` makes three kinds of group: `INDEPENDENT` (one per `KNOWN_INDEPENDENT` record),
`DECLARED_DEPENDENT` (one per declared lineage), and one `UNKNOWN` bucket per direction. The filter therefore
counted a declared-dependent lineage as a group of **established independence**. Two lineages of copies read
as a Repeated Signal; three lineages across two families read as Strong Multi-Source.

A `KNOWN_DEPENDENT` declaration proves that some records share one origin. It proves nothing about whether
that origin is independent of any other lineage. The hazard was latent: no row carries `KNOWN_DEPENDENT`
today, so no live result was affected, but a future dependence detector (N06) would have inflated levels the
moment it wrote one.

## 2. Old semantics and new invariant

| | algorithm 1.0.0 | algorithm 1.1.0 |
|---|---|---|
| counted toward Levels 2 and 3 | `INDEPENDENT` and `DECLARED_DEPENDENT` | `INDEPENDENT` only |
| unknown bucket | excluded | excluded (unchanged) |
| grouping, group strength, saturation | as defined | unchanged |
| masses, `evidence_score` | as defined | unchanged |
| Levels 4 and 5 | category plus provenance | unchanged (debt, §10) |

**Invariant.** Only groups of established independence count toward an evidence level threshold, and a
declared-dependent lineage is not one. Lineages still contribute their strength to `support_strength`
(saturation), exactly as the unknown bucket does.

## 3. Exact implementation

- `levels.py`: the filter is `g.kind is GroupKind.INDEPENDENT`. A new `_declared_dependent_clause` appends,
  only when a supporting lineage exists, the bounded sentence
  `; N declared-dependent lineage group(s) do not count: each is one origin, and distinct lineages are not
  established as independent of each other` to the Level 2 and Level 3 blocked reasons. It carries a count and
  never a lineage id. The existing unknown-only wording is untouched.
- `masses.py`: `ALGORITHM_VERSION = "1.1.0"`, with a comment naming N05. The sensitivity doc was regenerated;
  only its 14 algorithm-version lines changed.
- `independence.py`, `profile.py`: comment and docstring aligned (§7).
- Commits: `5d84bb1` (predecessor record), `9c8c120` (semantic repair and tests), `f00c541` (version 1.1.0),
  and the documentation and report commit.

## 4. Option B rejected

Option B would merge dependent lineages or change saturation during mass aggregation. It was rejected by
operator decision, and the evidence supports it: N05 is a **level** defect. Masses and scores never read the
level, so fixing the level cannot disturb them, while changing saturation would move every score that holds a
lineage and reopen the calibration question. Option A is the smallest change that removes the inflation, and
it can only lower a level.

## 5. Phase 1: predecessor replay under 1.0.0

Before any semantic change, `evidence_independence_level_replay.py --record-predecessor` ran under algorithm
1.0.0 and wrote `docs/data/evidence-aggregation-independence-level-predecessor-v1.json`
(sha256 `8e69aef5...`): 24 cases, each checked order-invariant over forward, reversed and six seeded shuffles,
with per-case digests, plus the canonical output of all 91 real claims over 112 rows, read in a read-only
transaction. The script refuses to run under any other version and refuses to overwrite the record. A
`--compare` against the unchanged code was byte-identical before `levels.py` was touched. The record is
historical and immutable.

## 6. Differential results

Levels are 1.0.0 → 1.1.0. Every case keeps its masses, score, groups, counts, warnings and explanation
byte-identical to the predecessor (`test_non_level_fields_are_byte_identical`).

| # | case | level | result |
|---|---|---|---|
| 1 | all UNKNOWN | 1 → 1 | blocked reason byte-identical |
| 2 | DD lineage + UNKNOWN | 1 → 1 | "found 1" → "found 0", plus the lineage clause |
| 3 | g1×2 + g2×2 DD | 2 → 1 | as required |
| 4 | three DD lineages, two families | 3 → 1 | as required |
| 5 | two INDEPENDENT | 2 → 2 | unchanged |
| 6 | INDEPENDENT + DD | 2 → 1 | as required |
| 7 | three INDEPENDENT (two families) + DD | 3 → 3 | unchanged |
| 8 | ten copies, one lineage | 1 → 1 | unchanged |
| 9 | DD contradiction vs UNKNOWN support | 1 → 1 | masses unchanged (score 9.6) |
| 10 | contradiction only | 0 → 0 | unchanged |
| 11 | DD MARKET_ACTIVITY | 4 → 4 | unchanged |
| 12 | reproducibility fixture | 3 → 2 | forward and reversed canonical JSON identical |
| 13 | shuffles | | identical output for every case, 8 orders each |
| 14 | masses sum to one | | every case |
| 15 | live and predecessor replay | | identical before the bump; after it only authorised level and reason fields, 91/91 real claims identical apart from `algorithm_version` |

**Adversarial cases (A01 to A12).** A03 one independent + two lineages 2 → 1; A04 two independent + lineages
3 → 2; A06 mixed states with contradiction 3 → 1; A12 three lineages + two independent 3 → 2. A01, A02, A05,
A07, A08, A09, A10, A11 unchanged (0, 1, 3, 5, 1, 1, 1, 3). A seeded 300-trial model check asserts Levels 2
and 3 equal the level implied by the `INDEPENDENT` count alone; agent B ran 3,000 further fuzz inputs and
found no result stronger than under 1.0.0.

## 7. Documentation changes

- `evidence-aggregation-framework-v1.md`: version 1.1, algorithm 1.1.0, amendment note; §8 renamed
  "Saturation across contribution groups" and says which groups enter it; §10 rows 2 and 3 say `INDEPENDENT`
  only, with a paragraph excluding declared-dependent lineages; §12 says the algorithm version moves with the
  equations or the structural rules.
- `profile.py` docstring and `independence.py` comment aligned.
- `docs/CLAUDE.md`: one invariant line; version 1.165.
- `PROJECT_MANIFEST.md`: version 1.164.
- Roadmap: N05 `status: DONE` with a result pointer. N01 stays `NO_GO_OPERATOR_DECISION_REQUIRED`, N02 stays
  unbound, N08 is not implemented.
- **Not changed, by decision.** The calibration strategy §2 and §9 contain nothing made false and are a
  preregistered record. Unrelated stale scoring documents are recorded as debt, not rewritten.

## 8. History and pins

Historical artifacts naming algorithm 1.0.0 are untouched, including every earlier sensitivity output and
Mission 1.84 record. The predecessor record is pinned by per-case digests that the tests recompute. The
profile still defaults its `algorithm_version` to the module constant.

## 9. Tests, gates and probe

- New: `tests/independence_level_cases.py` (shared case definitions) and `tests/test_independence_level_repair.py`
  (18 unittest tests, many subtests).
- evidence-aggregation 520 passed (1,083 subtests); evidence-reliability 352 passed; roadmap and qualification
  tests 82 passed; bare runner 3,895 tests across 9 packages; `ruff format --check` and `ruff check` clean;
  sensitivity `--check` ok; aggregation guard 8 checks ok; replay `--compare` ok.
- **Mutation probe** (unittest suite, sensitivity check and replay compare as the gate; every file restored and
  proved by digest): see §9.1.

### 9.1 Probe result

Final run: **11 caught, 1 equivalent mutant, 2 of 2 controls passed**; after the run every probed file was
byte-identical to the committed version (digest and `git diff` against HEAD).

| mutation | caught by |
|---|---|
| filter reverted to `is not UNKNOWN` | unittest |
| Level 3 alone counts lineages | unittest |
| lineage clause dropped | unittest |
| clause names lineage ids | unittest |
| unknown-only wording changed | unittest |
| lineage described as an independent source | unittest |
| families counted from independent items only | unittest (seeded model check) |
| algorithm version back to 1.0.0 | sensitivity `--check` |
| saturation exponent changed | unittest (predecessor non-level fields) |
| predecessor level rewritten | unittest (digest) |
| predecessor version rewritten | unittest |

The one survivor, `len({f for f in families if f}) >= min + (1 if not independent_groups else 0)`, is an
**equivalent mutant**: `families` is already filtered to non-empty values, and the added term applies only when
there are no independent groups, where the conjunction's first operand is already false. It cannot change any
output, so it is not an escape; a first run that used it alone was replaced by the non-equivalent families
mutation above, which is caught. No commit was made while the probe ran.

## 10. Canonical counters and remaining debt

Counters before and after, read only: raw 325, normalized 325, signals 60, claims 91, claim revisions 92,
evidence 112 (all `UNKNOWN`), reliability assessments 4, independence groups 0, opportunities 1, hypothesis
revisions 2, hypothesis evidence 14, embeddings 0, source policy reviews 71, scores absent. No independence
state was written.

Debt, recorded and not fixed:

1. Level 3 counts **families** from every scorable supporting item, including DD and UNKNOWN ones (A05 stays
   level 3 with its second family only from a lineage).
2. Levels 4 and 5 accept `KNOWN_DEPENDENT` as established provenance.
3. `engine.py` copies `profile.algorithm_version` with no mismatch check.
4. `missing_requirements` ordering depends on input order for non-scorable items.
5. The contract spec's "§10, §13" pointer should name §7; framework §0 maps A-04 to a stale section.
6. `calibration-feasibility-audit-v1.json` is stale and would drift on a manual `--check`.
7. Unrelated stale scoring documents noted in Mission 1.85.0.

**Next.** N05 is closed. N01 still needs the operator's A or B decision; nothing here starts N02, N06 or N08.
Mission 1.85.3 was not started.
