# Mission 1.30 — Targeted Evidence Completion V1

**Outcome: `TARGETED_EVIDENCE_COMPLETION_SUCCESS`.**

The `docker` packet is **`HYPOTHESIS_FORMABLE`** and
**`AVAILABLE_FOR_EXTERNAL_SYNTHESIS`**, on 7 Evidence rows across two source
families carrying two counting dimensions. **Nothing was acquired**, no model was
called, and the frozen sufficiency rule was not touched.

| | Before | After |
|---|---|---|
| RawRecords / NormalizedRecords | 148 / 148 | **148 / 148** |
| Signals / Claims / ClaimRevisions / Evidence | 26 / 26 / 26 / 26 | **27 / 27 / 27 / 27** |
| ReliabilityAssessments | 1 | **1** |
| Opportunities / Embeddings / Scores | 0 / 0 / 0 | **0 / 0 / 0** |
| Registered sources | 29 | **29** |
| packets formable | 0 of 9 | **1 of 9** |
| model calls / cost | 0 / 0.00 USD | **0 / 0.00 USD** |

---

## §23 — The nineteen questions

**1. Which source family?** `stack-exchange` (forum), **reused with no new
acquisition**.

**2. Why over the alternatives?** Twenty-nine sources are registered and **eight
have a review under `local-private-research-v1`**; approval never transfers, so
the other twenty-one are unreachable without a review mission. Of the eight, five
have a collector. Of those five, three cannot name Docker, Kubernetes or Podman
at all; `wikimedia-pageviews` already supplies the packets' only dimension and
would add nothing; and `gdelt` could match the terms but maps to **no dimension**,
because a lexical frequency change measures what media organisations published.
**The candidate set was one.** `github`, `npm-registry`, `pypi` and `hacker-news`
are what a reader reaches for first, and all four are `REQUIRES_REVIEW` with no
local review at all.

**3. Which subjects?** `docker`. Kubernetes and Podman were targeted and **not
reached** — see question 11.

**4. RawRecords acquired?** **Zero**, and that is the finding rather than a
shortcut. Mission 1.20 already collected `tagged=docker` over 2024-03-01 →
2024-03-31, and that retrieval **provably did not truncate**: one page with
`page_size = 100` returned **89** records, and a short page means the result set
was exhausted. §7 says collect the minimum needed and prefer fewer; fewer than
zero was not available.

**5. NormalizedRecords?** Zero new. 89 already-normalized records contributed.

**6. Signal type?** `community_question_volume`, family
`COMMUNITY_QUESTION_VOLUME` (**ADR-034**, migration `0030`), extractor
`community-question-volume@1.0.0`. **1 Signal**, magnitude **88**,
`OBSERVATION_COUNT`, window basis `NONE`, direction `NOT_APPLICABLE`.

**7. Claims?** One OBSERVED Claim through `observed-signal-restatement@1.3.0`:

> Stack Exchange published 88 questions carrying its own tag "docker" on
> "stackoverflow", created between source timestamps "1709280363" and
> "1709612240".

**8. Dimension added?** `PROBLEM_OR_NEED`.

**9. Why justified?** The dimension asks whether some actor is blocked, burdened
or unserved. A public question on a Q&A site is, by the site's own design, a
person stating they are stuck and asking for help. It is a genuinely different
question from the one the existing evidence answers: `AUDIENCE_OR_USAGE` says
*something attended to this subject*, this says *somebody said they were stuck on
it*, and neither implies the other.

**10. What it explicitly does NOT establish.** Not how many **people** — author
identity is never acquired, so distinct askers cannot be counted. Not that the
questions **share a problem**, which is the relation Mission 1.27 parked. Not
`RECURRENCE_OR_FREQUENCY`, which would require the previous point and is
therefore deliberately absent from the mapping. Not severity, difficulty, or that
anything is unsolved. Not demand, market size, adoption, buyers or willingness to
pay. And **the tag is a SUBJECT, not a problem** (Mission 1.18).

**11. Evidence rows per target, before → after.**

| subject | before | after | counting dimensions before → after |
|---|---|---|---|
| `docker` | 6 | **7** | 1 → **2** |
| `kubernetes` | 6 | 6 | 1 → 1 |
| `podman` | 6 | 6 | 1 → 1 |

**12. Counting dimensions.** `docker`: `AUDIENCE_OR_USAGE` → `AUDIENCE_OR_USAGE`
+ `PROBLEM_OR_NEED`. The others unchanged.

**13. Did a packet become formable?** **Yes — `subject:docker`.** 7 eligible
rows, 2 counting dimensions, source families `forum` and `knowledge`.

**14. Is it egress-authorized?** **Yes.** `wikimedia-pageviews` is `PERMITTED`
and `stack-exchange` is `PERMITTED_WITH_CONDITIONS`, both from Missions 1.23 and
1.29. The check was the deterministic gate only; **nothing was serialised or
sent**.

**15. Model calls?** **None.** **16. Opportunities?** **None.**
**17. Scoring or ranking?** **None.** **18. Problem-family inference?**
**Still PARKED**, and a test asserts the package cannot reach it.

**19. Next mission?** Below.

---

## Why Kubernetes and Podman were not reached

**A truncated count is not a count, and this is the mission's sharpest
constraint.** §7 caps new acquisition at 30 RawRecords. A complete count of
`kubernetes` questions in a one-month window is far above that, so any retrieval
inside the cap would be censored by **our own bound** — and a count capped at 30
that returns 30 has a magnitude which is the bound, carrying no information about
the world at all, while *reading as a larger number* than a complete count of 88.

That is why the extractor **refuses** rather than qualifying. It is ADR-021's
rule — a blocked derivation produces no Signal, never a Signal with a warning
attached — applied to a failure mode that counting introduces and change never
had.

`podman` is plausibly under 30 and was considered seriously. It was declined
because the outcome did not depend on it, the acquisition CLI has no
`stack-exchange` subcommand so it would have needed new live-acquisition
machinery, and a query returning exactly the cap would have produced 30 records
supporting nothing.

---

## A source-native inconsistency that decided the count

One of the 89 records — question `78089171` — was returned by a `tagged=docker`
query and its **own stored tag list contains no `docker`**:
`["kubernetes", "next.js", "dockerfile", "environment-variables"]`.

So *questions the query returned* (89) and *questions carrying the tag* (88) are
different quantities. **This mission counts the second**, because the Claim says
*carrying the site's own tag* and the tag list is the site's own vocabulary
recorded per record. Counting 89 would have counted a question the site does not
label `docker`.

It also settles Kubernetes independently: two `kubernetes`-tagged questions sit
in the corpus, and they arrived through a `docker` query. **They are a biased
subset, not a count**, and no volume Signal may be derived from them.

---

## §4 — Canonical subject identity, and why it is not the parked relation

Mission 1.28's grouping is **source-scoped by construction**: a `SubjectKey`
begins with the source id, so a Wikimedia packet and a Stack Exchange packet
could never merge however obviously they concerned the same thing. That is the
right default, and this mission extended it in the one way §4 permits.

`canonical-subject-registry-v1.json` maps **exact rendered keys** onto a
canonical subject, each entry naming the source, the identifier and a stated
basis. Matching is by **equality and nothing else** — no distance, no token
overlap, no stem, no synonym table, no threshold — and a test asserts that
`Docker`, `de.wikipedia.org|Docker_(software)`, `serverfault|docker` and
`docker-compose` all fail to match.

**It is not `SAME_PROBLEM_FAMILY` under another name, and the difference is not
one of degree.** That relation asks whether two OBSERVATIONS express the same
problem: a judgement about meaning, made per pair, at scale. This asserts that
two IDENTIFIERS, in two published vocabularies, name the same SUBJECT — decided
once by a person reading two pages, written down with its basis, and checkable by
anybody who reads the same two pages.

The registry also records what it **refuses**: there is no subject uniting
Docker, Podman and Kubernetes, and `docker-compose` is not folded into `docker`.
Both are named in `deliberately_absent`, because 25 held questions carry
`docker-compose` and that is exactly the number that makes an unjustified merge
tempting.

---

## ADR-034 — why a fifth quantity family

`CONTENT_REQUEST_VOLUME` was the near miss and rejecting it is the substance.
Both are counts over a bounded period with no metric and no geography, and the
fields would have fitted.

**A request is something a READER makes of a server. A question is something a
PERSON publishes about being stuck.** Widening that family would not have cost a
FIELD its meaning the way a procurement value would have cost `metric` its
meaning — it would have cost the FAMILY its meaning, and every consumer branching
exhaustively on it would have treated a pageview and a request for help alike
without deciding to.

`PROBLEM_VOLUME`, `PROBLEM_FREQUENCY`, `USER_PAIN_VOLUME`, `COMMUNITY_DEMAND` and
`UNMET_NEED_VOLUME` were all available names and all are wrong: a family named
for problems would have made the parked relation look answered by a count.

`facts.py` gained `_TEMPORAL_KINDS` so the new record kind supplies the temporal
facts and **not** `EXACT_NUMERIC_VALUE` — a question carries no measured value,
and folding it into `_COUNTING_KINDS` would have granted it one by omission. That
is the same trap Mission 1.19 avoided when it separated `_COUNTING_KINDS` from
`_BOTH_KINDS`.

---

## §13, §14, §16 — what did not move

**Reliability.** The new row is `ELIGIBLE_CONTEXT` like every other:
reliability NULL, `NON_SCORABLE`, `MISSING_RELIABILITY`. **No
ReliabilityAssessment was manufactured**, `eligible_scoring` is still **0**, and
the packet is formable and explicitly not scoring-ready.

**Independence.** The packet spans two source families and every row is still
`independence_state = UNKNOWN`. The packet says so in its own words — *"the count
of rows is not a count of independent findings"* — and the phrase *multiple
independent sources* remains structurally unreachable.

**The sufficiency rule.** `opportunity-sufficiency@1.0.0`, unchanged.
`TREND_OR_CHANGE` still does not count. Nothing was merged, no minimum lowered,
and the dimension mapping was written and justified **before** the packet was
inspected — recorded in `targeted-evidence-completion-v1.md`, which was committed
before any Signal existed.

---

## §20 — Tests

**33 new tests** in `test_targeted_evidence_completion.py` covering: the
selection recorded first; deterministic subject identity and every near-miss
refused; no similarity machinery in the registry module; the three subjects not
merged; the parked classifier unreachable; the dimension mapping's positive
warrant and its negative boundaries; no commercial dimension claimed;
`ELIGIBLE_CONTEXT` not promoted; independence still UNKNOWN; the frozen
sufficiency rule unchanged; a pageview-only packet still insufficient; no
Opportunity; no model call; and reproducible packet construction.

**Six existing tests were updated, none weakened**, and four were made stricter.
Two closed-set assertions in `test_signal_model.py` gained the new family and
type with their reasoning — kept as **equalities**, so adding a member stays a
visible act. The extractor registration test likewise. Two Mission 1.28 totals
that pinned `26` now assert the total **agrees with the report's own row list**,
which catches a run that inspected fewer rows than it enumerated and previously
could not. And Mission 1.29's *"no packet is formable"* became a direct assertion
of the property it was protecting: **packets that are AVAILABLE and still
insufficient exist**, so egress authorization demonstrably does not imply
evidence sufficiency.

Repository totals: **141** in the opportunity package, 571 zero-dependency, all
pytest suites across 9 packages, **0 failures**. Nine validators, contract
generation `--check`, four generated-document checks, ruff, ruff format, mypy,
both CI greps and `migrate --plan` pass.

---

## §22 — Outcome and §NEXT-STEP

**`TARGETED_EVIDENCE_COMPLETION_SUCCESS`.** One packet moved from
`HYPOTHESIS_INSUFFICIENT_EVIDENCE` to `HYPOTHESIS_FORMABLE` through legitimate
new Evidence, with no gate changed to obtain it.

The NEXT-STEP RULE fires: the `docker` packet is **formable and
egress-authorized**, so the recommendation is

> **Mission 1.31 — First Bounded Opportunity Synthesis V1**

and it is **not started**.

Two things a synthesis mission should carry into its brief, from here:

- **The packet is formable and NOT scoring-ready.** Every row is
  `ELIGIBLE_CONTEXT`; a hypothesis formed over it can cite evidence and can
  contribute to no score, and D-03 still blocks scoring for unrelated reasons.
- **Two source families is not two independent sources.** Independence is
  `UNKNOWN` on all seven rows, and any synthesis prompt must be given the
  packet's own independence sentence rather than a count of families.

If breadth is wanted before synthesis, the narrowest next evidence move is a
single bounded `tagged=podman` Stack Exchange query over 2024-03-01 → 2024-03-31
with `page_size` set at the §7 cap — pre-registering that a full page means
truncation and therefore no Signal. Kubernetes is out of reach at that bound and
would need a raised one, decided deliberately.
