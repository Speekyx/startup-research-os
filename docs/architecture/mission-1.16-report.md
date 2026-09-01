# Mission 1.16 — Demand and Problem Evidence Source Expansion

**Sprint 1. Authorized by the Mission 1.16 brief §0-§35.**

**No source was added, under §10: no candidate has an authorised path.** The
mission's product is the measured blocker, and it has two layers — the second
larger than the one the mission set out to find.

**Nothing was collected, created or changed.** Counts are identical before and
after. **H-36A, H-36B, H-37, H-38 untouched.**

Full analysis: [`demand-evidence-portfolio-blocker-v1.md`](../data/demand-evidence-portfolio-blocker-v1.md).

---

## 0. The pre-flight correction (§0)

`docs/architecture/mission-1.15.13-report.md` and
`docs/data/ted-eu-evidence-reliability-operator-review-v1.md` said the rationale
and stated limitation were *"written by the operator"* and *"in the reviewer's own
words"*. Corrected: the **wording was AI-assisted** and the reviewer read, adopted
and submitted it.

What did not change is the part that decides the origin: **the number was the
reviewer's alone**. No model selected, derived, defaulted or recommended it, and
the tool has no mechanism that could. `evidence-reliability-review-guide-v1.md`
§5 draws the line in the same place — a model may draft a paraphrase you then
check, and may not be the epistemic source of the judgement — so `HUMAN_REVIEW`
remains correct.

**The persisted assessment was not touched**: same value, reviewer, scope, basis,
confirmation and version, still current, verified after the edit.

---

## 1. The gap that was targeted

Evidence of **real user problems, unmet needs, solution-seeking, frustration with
current tools, switching intent and product demand** — the families the current
portfolio does not observe.

### What current coverage exists?

Measured from the registry, not from the historical "six of eight" statement.

29 registered sources. **Five approve under `commercial-multi-tenant-research-v1`;
one approves under `local-private-research-v1`.**

| Family | Approving sources |
|---|---|
| `commercial`, `trend` | eurostat, fred, gdelt, openalex, ted-eu, world-bank |
| `community`, `social` | gdelt |
| `curiosity` | gdelt, openalex |
| `developer_activity`, `discovery`, `learning` | openalex |
| `competition` | ted-eu |
| **`problem`** | **ted-eu only** |
| **`desire`** | **none** |
| `creativity`, `entertainment`, `collection` | none |

**`problem` is nominally covered and substantively is not.** TED observes a
public buyer's procurement need expressed as a contract award. That is a real
problem signal about institutional purchasing and it is not a user finding a tool
frustrating — treating one as evidence of the other is precisely the substitution
this portfolio exists to prevent.

---

## 2. Candidates considered, and why each loses

Ten sources cover `problem` or `desire`. Every one:

| Source | State | Why it loses |
|---|---|---|
| `hacker-news` | `RESTRICTED` | `automated_access` **`NOT_PERMITTED`**; YC terms prohibit data mining, scraping and commercial derivative works |
| `github` | `RESTRICTED` | `commercial_use` and `derived_analytics` both **`NOT_PERMITTED`** |
| `product-hunt` | `RESTRICTED` | `commercial_use` `NOT_PERMITTED` |
| `apple-app-store`, `google-play`, `steam` | `RESTRICTED` | terms retrieved and restrictive |
| **`stack-exchange`** | `REQUIRES_REVIEW` | **the one worth trying — see §3** |
| `reddit` | `REQUIRES_REVIEW` | Data API terms unfetchable here; `storage`, `derived_analytics`, `model_processing` all `NOT_ASSESSED` |
| `bluesky` | `REQUIRES_REVIEW` | all six load-bearing activities `NOT_ADDRESSED`; docs redirect to technical material governing none of them |
| `ted-eu` | already collected | the source the brief says not to deepen |

Ranked on the brief's §5 criteria, **Stack Exchange won and Reddit was second.**
Stack Exchange wins on semantic directness — a question is solution-seeking by
construction rather than by interpretation, and acceptance marks make repeated
problems visible — and on having an official API and a CC BY-SA licence on
content. Reddit loses to it on structured-data quality and on directness: a
subreddit thread needs interpretation before it is a problem statement, where a
Stack Exchange question is one by its own schema.

---

## 3. Why the selected candidate could not proceed

Stack Exchange's Mission 1.15 review left three open questions, two needing
documents that `stackoverflow.com` served behind an anti-bot interstitial.

**Retried in this mission. The environment cannot reach the host at all** —
neither `stackoverflow.com/legal/terms-of-service/public` nor
`api.stackexchange.com`. Reddit's `redditinc.com` is equally unreachable.

**No bypass was attempted.** §7 and §8 forbid it, and `source-registry-v1.md`
rule 2 settles it independently: *uncertainty is never permission*. An approval
written on terms nobody could read is exactly the approval the registry exists to
prevent, and it would have been indistinguishable from a correct one until it
mattered.

Stack Exchange therefore stays `REQUIRES_REVIEW` with its three open questions
**unchanged**. Nothing was written down about it that was not already known.

---

## 4. The second blocker, which nobody had noticed

**The runtime declares `local-private-research-v1`, and exactly one review in the
registry is under that profile: `ted-eu`.**

```text
sros-source --use-profile local-private-research-v1 authorization world-bank
  REFUSED: no acquisition authorization for world-bank
    - no policy review exists for use profile 'local-private-research-v1'
```

The same for `gdelt`, `eurostat`, `fred` and `openalex`.

### This is the gate working, and it still matters

ADR-027 is explicit: *"Never transfer approval between profiles… Nothing falls
back."* Those five were reviewed for a **public multi-tenant SaaS**, and nobody
has written down what they permit for **this** deployment. Refusing rather than
guessing is right.

**But the deployment holds real data it could not re-collect today.** 15 of 23
RawRecords and 7 of 8 Evidence rows are World Bank and GDELT, gathered in
Missions 1.5 to 1.11 — before ADR-027 existed. Their provenance carries **no
`use_profile` at all**, which is the visible trace of a model that had no such
concept yet.

Nothing improper happened; those collections were authorised under the rules then
in force. But the registry now says something the pipeline's own history does
not, and the discovery is currently scheduled for whoever next tries to refresh a
World Bank series.

**And it caps expansion silently.** Any new source, however good its commercial
review, is refused at runtime until somebody assesses it for the local profile.
That is now on the critical path for every future source mission — including the
one this mission was supposed to be.

---

## 5. Answers to the remaining §33 questions

Most are answered by there being no source, and the honest form of each is short.

| | |
|---|---|
| Which source was selected? | **None.** §10 applies |
| Official access path, use profile, resource, fields, bounds | **not reached** |
| Was any personal data acquired? | **No.** No acquisition of any kind occurred |
| Records collected / normalized | **0 / 0** |
| Signal semantic, minimum support, Signals created | **not reached; 0** |
| OBSERVED Claims created | **0** |
| Evidence rows created | **0** |
| Reliability applied | none; no new scope exists to assess |
| Scorable | not applicable |
| INFERRED Claims created | **0** |
| Opportunities created | **0** |
| Scores created | **0** |
| TED / World Bank / GDELT semantics changed | **none** |
| Did all gates pass? | **yes** |

### Counts before and after

| | Before | After |
|---|---|---|
| RawRecords | 23 (gdelt 6, ted-eu 11, world-bank 6) | **23**, identical |
| NormalizedRecords | 23 | 23 |
| Signals | 8 | 8 |
| Claims / ClaimRevisions | 8 / 8 | 8 / 8 |
| Evidence | 8 | 8 |
| ReliabilityAssessments | 1 | 1 |
| Opportunities / Embeddings / Scores | 0 | 0 |

### Gates

```text
zero-dependency suites            555 tests, 8 packages      exit 0
all pytest suites                 7 packages                 exit 0
seven validators                                             exit 0
contract generation --check                                  exit 0
all four generated-document checks                           exit 0
ruff check / ruff format --check                             exit 0
mypy                              144 source files           exit 0
environment-template secret check                            exit 0
assert_registry_grants_nothing                               exit 0
```

No code changed, so the gates confirm the documentation edits broke nothing
rather than exercising anything new.

---

## 6. Next mission

The brief's §34 asks for iterative source expansion. That loop cannot start yet,
and the reason is §4 rather than §3.

**A. `local-private-research-v1` reviews for the already-collected sources.**
Assess World Bank and GDELT — and then the other approving sources — against the
actual local use, so the registry stops contradicting the pipeline's own history
and a refresh stops being refused. It is the smallest of the two, the most urgent,
and it unblocks everything downstream.

**B. Stack Exchange review completion.** Retrieve the Public Network Terms of
Service and the Consolidated Responsible AI policy from an environment that
serves them, and close the three open questions against them. If they approve,
this mission's engineering work becomes available immediately and the `problem`
family gets its first substantive source.

**They are ordered, and the order is the finding.** B before A produces an
approving commercial review for a source the runtime still refuses — which is
exactly the shape of the surprise this mission ran into.

**What should not happen next** is picking a less suitable source because it is
easier to authorise. The gap is `problem` and `desire`; a fourth `trend` source
would enlarge the corpus and change nothing about what the system can conclude.
