# Mission 1.20 — Narrow-Tool Repeated Problem Evidence

**Sprint 1. Authorized by the Mission 1.20 brief §0-§33.**

> ## OUTCOME S0 — AND THIS ONE CLOSES A DIRECTION
>
> A deliberately narrow acquisition — 89 real Stack Overflow questions tagged
> `docker`, over one pre-registered month — produced **0 Signals, 0 Claims, 0
> Evidence.**
>
> **The finding is not "no repeats were found".** Three questions share **182
> characters** of exact, stable, tool-specific Docker daemon diagnostic — far
> more than §12 asks for. They are three unrelated failures. The shared string
> ends at `exec: "`, which is exactly where the wrapper stops and the actual
> problem begins.
>
> Mission 1.18's S0 could be blamed on the acquisition: a language tag selects a
> subject. **This mission removed that explanation and failed anyway**, for a
> deeper reason. Per §15, no further mission should attempt repeated-problem
> detection with another deterministic Stack Exchange acquisition.

Pre-registration:
[`mission-1.20-acquisition-preregistration.md`](mission-1.20-acquisition-preregistration.md),
committed in `b521c74` **before any question content was read**.

---

## 1. PRE-FLIGHT

### Was the TED wording corrected?

**Yes.** Four current authoritative documents said, in one phrasing or another,
that a TED award notice records *what a buyer paid a named supplier*. Mission
1.15.12 had already established the opposite from the Publications Office's own
eForms SDK 1.15.1: **BT-161 is the value of all contracts awarded in the notice,
options and renewals included.** It is a PUBLISHED value — not money paid, not
necessarily one supplier, not realised expenditure, not revenue, not a price, not
willingness to pay — and it can be lawfully withheld (BT-195 to BT-198), so any
cohort covers the published subset.

| Document | Status | Action |
|---|---|---|
| `mission-1.19-report.md` portfolio table | current | corrected, with the reason inline |
| `docs/CLAUDE.md` §Demand-side sources | current authoritative | corrected |
| `docs/data/ted-eu-transaction-signals-v1.md` | **Authoritative** | corrected |
| `docs/data/source-human-review-queue-v1.md` | current | corrected |
| `ADR-029` | accepted ADR | **note appended, argument untouched** |
| migrations 0020 / 0023 | applied | **left** — an applied migration is never edited |
| `source-catalog-v1.json` review notes | review record | **left** — rewriting it rewrites what a review said |
| `mission-1.15.9-report.md`, manifest changelog | historical | **left** |

**ADR-029 was handled differently on purpose.** An ADR is the record of a
decision, and this is a later finding about one of its premises rather than a
reversal of the decision. The table row is narrowed and a dated note explains
what changed and what did not: the family name, the reasoning against
`MEASURED_SERIES`, and the refusal of `WILLINGNESS_TO_PAY` all stand.

**No TED data was modified.**

### Was the "no PERSON" overstatement corrected?

**Yes.** The Mission 1.19 report read *"the portfolio now observes an
interaction, and still observes no PERSON"*. That is not true: a Stack Exchange
question is a human-authored solution-seeking utterance and the portfolio holds
15 of them, now 104.

The corrected sentence is that the portfolio observes **no stable requester
identity across repeated interactions** — a pageview is one request and Wikimedia
publishes no link between two, and Stack Exchange author identity was
deliberately not acquired.

**The repair is the sentence.** Acquiring identity to make the old wording true
would invert the minimisation posture both reviews rest on, and §25 forbids it by
name.

---

## 2. ACQUISITION DESIGN

### Which tool, and why before inspecting content

**Docker.** Stack Overflow tag `docker`. Wikimedia counterpart
`Docker_(software)`, for which Mission 1.19 already holds seven days of
independent per-item request counts.

Selected on §4's six criteria, and **no tie-break was needed** because the three
candidates do not satisfy them equally:

- **Kubernetes fails criterion 1.** §1 asks for one narrowly defined *tool*, and
  Kubernetes is a platform whose tag spans manifests, controllers, kubectl, Helm
  and vendor distributions. Choosing it would have been a smaller version of
  Mission 1.18's mistake rather than a fix for it.
- **Podman fails criterion 5, honestly.** It is arguably the narrowest entity of
  the three. Its question volume is low enough that a pre-registered window would
  have been a guess with no basis — and since §6 forbids extending a window
  afterwards, a guess returning eight questions would have produced an S0 that
  tests nothing. A sample too small to falsify anything is a badly designed
  experiment, not a strict one.
- **Docker satisfies all six.**

**Nothing rests on expected problem frequency**, which §4 forbids twice. No count
query was run to compare candidates: running one would have been the selection
§4 prohibits. Criterion 5 was satisfied by choosing the WINDOW rather than by
preferring a busy tool.

**Stated as a limitation rather than hidden**: the `docker` tag is used for the
wider container tooling around the engine — Compose, BuildKit, Desktop. Docker is
one tool more than Kubernetes is and less than Podman is, and whether that
residual breadth defeated the experiment is answered in §4 below: it did not, and
the failure happens for an entirely different reason.

### The bounds, fixed before reading anything

```text
site         stackoverflow          tagged       docker
from_date    2024-03-01             to_date      2024-03-31
page_size    100                    max_pages    2
max_records  200                    filter       !SyjNl4V)kvv2kw3Qt6 (unchanged)
```

**The window is the month containing Mission 1.19's Wikimedia window for
`Docker_(software)`.** Two corpora about the same entity over an overlapping
period is what makes the future convergence provenance meaningful at all, and it
is a reason that exists before any question is read.

### Governance delta: none

Same source, profile, resource `questions/stackoverflow`, route
`stack-exchange-api`, collector `stack-exchange-questions@1.0.0` unbumped, same
field set, same API filter.

**Filtering by one tag is inside the authorised resource, and the check was not a
formality.** The review authorised *questions on `stackoverflow`, through the
official API, in bounded queries*; `tagged` is an existing bound Mission 1.18
already used with the value `python`; it reaches the query the source receives;
and the compliance entry records no tag allowlist of any kind. Changing the VALUE
of an authorised query parameter is the same activity on the same resource.

---

## 3. REAL DATA

| | |
|---|---|
| HTTP requests | **1** |
| `has_more` | **false** — the whole month fit in one page |
| Items seen | 89 |
| RawRecords | **89 new** |
| Quota | 299 / 300 remaining |
| `backoff` | none returned |
| Idempotency | identical re-run → `new: 0, unchanged: 89, revised: 0` |
| NormalizedRecords | **89**, kind `community_question`, all `VALID` |
| Identity fields acquired | **0** — verified in SQL across all 89 records |

**No new record kind and no collector bump.** §8 and §10: the tag restriction
belongs to acquisition and provenance, not to the shape of one question, and a
different query-parameter value is not a semantic change. Provenance carries
`tagged`, `use_profile`, `date_window`, `page_size`, `max_pages` and
`max_records`.

**Mission 1.18's `python` sample is untouched** at 15 records, and its S0 remains
true for its own acquisition.

---

## 4. EMPIRICAL ANALYSIS

Deterministic text inspection only. No embedding, no similarity measure, no
model judgement of equivalence — which is precisely why the conclusion is that
those are what the problem would need.

### The corpus

89 questions, 140 distinct tags, 88 carrying `docker`. **56 of 89 carry at least
one error-bearing line of 40 characters or more** — a corpus in which a repeated
signature genuinely could have appeared.

### What repeated, and what it cost

**Exact error lines of 40+ characters appearing verbatim in two distinct
questions: ZERO.** With instance-specific numbers masked as well: **zero.**

The only candidate with real specificity is a Docker daemon error shared by three
questions:

```text
Error response from daemon: failed to create task for container: failed to create
shim task: OCI runtime create failed: runc create failed: unable to start
container process: exec: "
```

**182 characters, identical, exact, stable and tool-specific.** This is more than
§12 asks for. And here is what the three questions were actually about:

| Question | After `exec: "` | The real problem |
|---|---|---|
| `78086542` | `/usr/src/app/entrypoint.sh": permission denied` | a file mode |
| `78099519` | `/app/.venv/bin/pipenv": stat …: no such file or directory` | a path absent from the image |
| `78099680` | `gunicorn": executable file not found in $PATH` | a PATH lookup |

**The shared string ends exactly where the failure begins.** Those 182 characters
are runc saying *I could not start the process*; everything after is *why*.

### Support and specificity trade off directly

| Prefix length | Maximum distinct questions sharing it |
|---|---|
| 40 → 182 | **3** — the signature is the wrapper |
| 183 | 2 — and that 2 is an accident: two of the three paths merely both begin with `/` |
| 184 and beyond | **1** — every question is alone |

**Two characters past the wrapper, the signature is unique.** A rule needs a
length, and every length is either the envelope or the instance. There is nothing
in between to choose.

### Hard negatives, all from the real sample

| Candidate key | Distinct questions | Why it is not a problem |
|---|---|---|
| tag `docker` | **88 of 89** | §13: tool identity is necessary and never sufficient |
| `no such file or directory` | 5 | a POSIX errno message every tool emits |
| `connection refused` | 3 | generic networking |
| `exit code 1` | 3 | weaker than an HTTP status: the default failure code of every program that does not choose one |
| HTTP 500 | 3 | §12's named negative |
| `ValueError` | 2 | `78086521` is a pyspark traceback inside library code; `78098246` raises its own `ValueError('No starting port for the application')`. Same class, no relationship |
| `permission denied` | 2 | generic |

**No vendor error code repeats.** `P1001` (Prisma) appears once. No CVE, no
`errno`, no signal name.

### Could deterministic equivalence be defended?

**No, and the reason is not about text processing.** Deciding that *permission
denied on an entrypoint* and *binary not on PATH* are different problems, while
two different missing binaries would be the same one, is a judgement about
meaning. No case rule, whitespace rule, number-masking rule or punctuation rule
reaches it — and §14 forbids the one operation that would appear to: removing
words until unrelated errors collapse together.

---

## 5. OUTCOME — S0

**0 Signals, 0 Claims, 0 Evidence.** No new record kind, no new signal type, no
extractor, no ADR.

Three things were available and were not done: the cohort was not weakened, a
second query was not run on any tag or window, and no `INFERRED` path was opened.

### Why this S0 closes a direction and Mission 1.18's did not

Mission 1.18's failure had an available explanation: it selected by `python`, and
a language tag selects a subject. The obvious next move was to narrow the
acquisition, and §14 of that mission's own review said so.

**Mission 1.20 made that move and failed for a different reason.** The narrow
acquisition worked exactly as designed: it delivered a corpus with real, exact,
stable, tool-specific diagnostics — the best case §12 describes. The diagnostics
still do not identify problems, because a diagnostic names the **envelope** and
what makes two failures the same is underneath it.

**So the failure is not in the acquisition, and a third acquisition would not
address it.** Per §15, this direction is closed: the next architectural choice is
semantic **INFERENCE** over question text, or a source carrying **explicit issue
identity** — a defect tracker where the same fault has an id, rather than a
question forum where the same fault has a paragraph.

---

## 6. CLAIM / EVIDENCE

**None**, because no Signal exists. Nothing about category, independence,
reliability or scorability arises.

**No ReliabilityAssessment was created**, and the 18 Wikimedia Evidence rows keep
their `UNCATEGORISED` / `UNKNOWN` / level 1 / `NON_SCORABLE` state exactly as
Mission 1.19 left them (§23, §26).

**No convergence machinery.** The conceptual correspondence is recorded and
nothing rests on it: `docker` on Stack Overflow ↔ `Docker_(software)` on English
Wikipedia, two corpora over overlapping periods. Whether two separately governed
source families jointly support a higher-level inference is a later question, and
this mission asserts no relationship, no independence and no combination.

---

## 7. BOUNDARIES

| | |
|---|---|
| Distinct QUESTIONS vs distinct PEOPLE | respected — no identity acquired, and no claim about reporters exists to be wrong |
| INFERRED Claims | **0** |
| Opportunities | **0** |
| Embeddings | **0** |
| Scores | **0** |
| Similarity measures used in the analysis | **none** — exact string comparison throughout |
| Second query on any tag or window | **none** |
| World Bank, GDELT, TED, Wikimedia | **unchanged** |
| Mission 1.18's `python` acquisition | **unchanged**, 15 records |
| Gateway defect, `SOURCE_ITEM_LINK` follow-up, historical `use_profile`, TED H-36/37/38, npm rights gap | **not touched** |

---

## 8. QUALITY

### Counts before and after

| | Before | After |
|---|---|---|
| RawRecords | 59 | **148** (+89) |
| NormalizedRecords | 59 | **148** (+89, all `VALID`) |
| Signals | 26 | **26** |
| Claims / ClaimRevisions / Evidence | 26 / 26 / 26 | **26 / 26 / 26** |
| ReliabilityAssessments | 1 | **1** |
| Opportunities / Embeddings / Scores | 0 | **0** |

Normalized coverage: `world-bank / numeric_observation / VALID / 6`, `gdelt /
lexical_frequency_observation / PARTIAL / 6`, `ted-eu / procurement_notice /
PARTIAL / 11`, `stack-exchange / community_question / VALID / 104`,
`wikimedia-pageviews / content_request_count / VALID / 21`.

**89 more observations and not one more Signal**, which is the honest shape of
this mission.

### Did all gates pass?

**Yes.** Zero-dependency suites (555 tests across 8 packages), all pytest suites
across 7 packages, the seven validators plus `check_env_template` and
`assert_registry_grants_nothing`, contract generation `--check`, all four
generated-document checks, ruff check, ruff format, mypy — **and the two CI
inline grep guards** (network client outside the transport; collectors outside
the collection package), which Mission 1.19 learned to run locally after CI
caught one of them.

**No existing assertion needed repointing.** Nothing was added to any registry,
vocabulary or enum, so nothing that counts them changed — which is what an S0
should look like from the outside.

The new suite, `test_narrow_tool_problem_signature.py`, encodes the decision
rather than a behaviour: the 182-character prefix, the three divergent root
causes, the support curve, and each hard negative with its real support count.
Its own no-similarity check is asserted over the AST's imports rather than the
file's text, because the module has to name the techniques it excludes.

---

## 9. The architectural consequence

**The deterministic route has now failed under both broad and narrow
acquisition**, and the two failures are different:

- **Broad (Mission 1.18):** the only available key was a tag, and a tag is a
  subject. Fixable in principle by narrowing.
- **Narrow (Mission 1.20):** exact tool-specific diagnostics were available and
  plentiful, and they name the error envelope rather than the failure. **Not
  fixable by narrowing further** — a narrower tool yields fewer questions and the
  same envelopes.

So the next work should **not** be another Stack Exchange query. Two directions
remain, and choosing between them is a decision with its own mission:

- **Semantic INFERENCE.** A layer that judges whether two failure descriptions
  are the same problem. That is an `INFERRED` claim by construction — it needs a
  stated reasoning step, a contract for what a model may assert, and evidence
  rules for a claim no deterministic process could regenerate. Everything about
  it is currently forbidden, deliberately.
- **A source with explicit issue identity.** A defect tracker publishes an issue
  id, and two reports of one fault are linked by the SOURCE rather than by us.
  The equivalence judgement moves to the publisher, where somebody with context
  made it. Every registered candidate of that shape is `RESTRICTED` on retrieved
  terms today, which makes this a governance question rather than a modelling
  one.

**The second is the smaller step and the honest one**, because it moves the
judgement to whoever is qualified to make it instead of manufacturing it. Neither
is started here.

`WILLINGNESS_TO_PAY` and `PRICING` remain where Mission 1.16 left them, the
second still with no registered candidate at all.
