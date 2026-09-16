# Mission 1.85.1: First-Person Structured Evidence Source Qualification

**`NO_GO_OPERATOR_DECISION_REQUIRED`**

Roadmap node **N01** asked one question: using retrieved first-party documentation only, can any source in
F-REVIEW (reviews with a platform-native rating) or F-ISSUE (issue trackers with native labels, state or
duplicate relations) be approved under `local-private-research-v1` for an official route that exposes
deterministic structured evidence?

**No.** Eight candidates were frozen before retrieval and evaluated against the same six activities. None
is eligible. Six have an official route that exposes exactly the structured field SROS wants and the other
two expose it partly, so **the data shape is not the blocker; permission is.** No source is selected, no review is appended, nothing is
registered, and Mission 1.85.2 is not the source-implementation mission. It needs an operator decision.

```
START_COMMIT        ca84449e8c2b12486c2c7d01b40c31529be0ab80  (merged main after PR #172)
FREEZE_COMMIT       0eee973b1a7e63a7cf2e60edd867147a9dd50c07  (candidate set, pushed before retrieval)
BRANCH              sprint-1/mission-1.85.1

candidates 8 (4 registered, 4 unregistered)   eligible 0   selected NONE
research-data requests 0   model calls 0   reviews appended 0   sources registered 0
decisive clauses re-read from retrieved bytes  18 of 18 verified
```

## 1. The frozen candidate set

Frozen in `docs/data/first-person-source-candidates-v1.json` and pushed before any documentation was
retrieved (`frozen_set_sha256 c2f01894...`). No correction was made after retrieval.

| Candidate | Registered | Family | Why it was plausible |
|---|---|---|---|
| `github` | yes | F-ISSUE | documented issues endpoint with labels, state, `state_reason`, reactions |
| `steam` | yes | F-REVIEW | documented user-reviews route with a recommendation flag per review |
| `google-play` | yes | F-REVIEW | documented reviews resource with a star rating per review |
| `apple-app-store` | yes | F-REVIEW | documented customer-reviews resource with a rating per review |
| `gitlab-com` | no | F-ISSUE | documented issues API with labels, state, upvotes |
| `codeberg` | no | F-ISSUE | documented Forgejo issues API on a non-profit public forge |
| `kernel-org-bugzilla` | no | F-ISSUE | Bugzilla REST exposes `dupe_of`; an earlier landscape recorded `/rest/` allowed by robots |
| `trustpilot` | no | F-REVIEW | documented API with a star rating per review |

The unregistered four avoid repeating the Mission 1.21 dead ends (TDF Bugzilla, Launchpad, Mozilla,
Debian). kernel.org was re-checked because its only recorded gap was an unaddressed licence.

## 2. How the evidence was gathered and checked

Five read-only agents retrieved current first-party documents on 2026-09-16: GitHub, Steam, Google Play,
Apple, and the four alternatives. A sixth agent prepared the N05 brief. The main agent was the only writer.

**A retrieval summary is not a document.** The agents' retrieval tool returns model-summarised text, so the
main agent re-read every clause a verdict depends on from the retrieved bytes. The script removed markup,
collapsed whitespace and searched for the exact decisive wording. All 18 raw reads returned HTTP 200, and
every decisive phrase was found. Two needed a second look:
- GitHub's research clause contains a markdown link inside the sentence.
- kernel.org writes "Attribution ShareAlike" without a hyphen.

Each raw read's SHA-256 is recorded. Evidence rows that were not re-read carry `SUMMARISED_FETCH`, and none
of them supports a decisive reason alone.

**Documentation only.** No review, issue, bug or business-unit endpoint was called. A test asserts that no
raw-read path is a data endpoint.

The complete record, with URL, title, publisher, retrieval time, section, paraphrased proposition, stance
and the activity it bears on, is `docs/data/first-person-source-qualification-v1.json`.

## 3. Six-activity matrix

Verdicts under `local-private-research-v1`. Approval requires PERMITTED or PERMITTED_WITH_CONDITIONS on
first-party evidence for every activity. Silence is `NOT_ADDRESSED`; a question needing legal judgement is
`UNCLEAR`.

| Candidate | automated access | API use | commercial use | storage | derived analytics | model processing |
|---|---|---|---|---|---|---|
| github | PERMITTED_WITH_CONDITIONS | PERMITTED_WITH_CONDITIONS | UNCLEAR | NOT_ADDRESSED | UNCLEAR | NOT_ADDRESSED |
| steam | UNCLEAR | UNCLEAR | UNCLEAR | UNCLEAR | UNCLEAR | NOT_ADDRESSED |
| google-play | NOT_ADDRESSED | NOT_ADDRESSED | NOT_ADDRESSED | NOT_PERMITTED | NOT_ADDRESSED | NOT_ADDRESSED |
| apple-app-store | NOT_PERMITTED | NOT_PERMITTED | UNCLEAR | NOT_ADDRESSED | UNCLEAR | NOT_ADDRESSED |
| gitlab-com | NOT_PERMITTED | UNCLEAR | NOT_ADDRESSED | NOT_ADDRESSED | NOT_ADDRESSED | NOT_ADDRESSED |
| codeberg | NOT_PERMITTED | NOT_ADDRESSED | UNCLEAR | UNCLEAR | UNCLEAR | NOT_ADDRESSED |
| kernel-org-bugzilla | UNCLEAR | NOT_ADDRESSED | UNCLEAR | UNCLEAR | UNCLEAR | NOT_ADDRESSED |
| trustpilot | NOT_PERMITTED | NOT_PERMITTED | NOT_PERMITTED | NOT_PERMITTED | NOT_PERMITTED | NOT_PERMITTED |

**Model processing is approved for no candidate**, and only Trustpilot addresses it (by prohibiting it).
**Storage and derived analytics are approved for no candidate either**, and those are the two activities a
local research corpus cannot do without.

## 4. Official-route matrix

| Candidate | Official resource | Access | Structured field | Native duplicate / parent | Historical | Stable ids |
|---|---|---|---|---|---|---|
| github | `GET /repos/{o}/{r}/issues` | public; token raises limits | `state`, `state_reason`, labels (repo-defined), reactions (meaning undocumented) | close reason only; **target not on read routes**; `parent_issue_url` | `state=all`, `since` | yes |
| steam | `GET store.steampowered.com/appreviews/{appid}?json=1` | public, no key documented | `voted_up` (documented positive recommendation); totals; `review_score` (formula undocumented) | none | `day_range` capped at 365; completeness undocumented | yes |
| google-play | `GET androidpublisher/v3/applications/{pkg}/reviews` | **account-bound, own apps only** | `starRating` 1-5 | none | **last week only** | yes |
| apple-app-store | `GET /v1/apps/{id}/customerReviews` | **account-bound, own apps only** | `rating` 1-5 | none | list endpoint | yes |
| gitlab-com | `GET /api/v4/projects/:id/issues` | public | state, labels, upvotes | `closed_as_duplicate_of`, `moved_to_id` | `created_after`, `updated_after` | yes |
| codeberg | `GET /api/v1/repos/{o}/{r}/issues` | public reads not documented | state, labels | none | `since`, `before` | yes |
| kernel-org-bugzilla | `GET /rest/bug` | public reads (upstream docs) | status, resolution, keywords | `dupe_of` | history `new_since` | yes |
| trustpilot | `GET /v1/business-units/{id}/all-reviews` | **paid business account, own business** | `stars` (meaning undocumented in prose) | none | all reviews | yes |

Storage and deletion obligations, pagination and rate limits per route are in the record.

## 5. Eligibility and the decisive reasons

| Candidate | Eligible | Decisive reason (raw-verified evidence) |
|---|---|---|
| github | no | AUP §7 limits every use of GitHub information, "regardless of whether" it was scraped or collected through the API, to research on **public, non-personal information** whose publications are **open access**, or to archiving. AUP §6 forbids reproducing or exploiting the Service without written permission, and the Terms reserve every right not expressly granted. |
| steam | no | No document grants a third party any activity. The Steam Web API Terms grant distribution to end users "for their personal use", and Steam Data is Valve's property. The Subscriber Agreement licenses personal, non-commercial use, forbids exploiting content "for any commercial purpose", and bars "non-human-controlled systems". Whether these govern the review route needs legal judgement. |
| google-play | no | The only rating route serves a developer's **own app** and only reviews "within the last week". The Google APIs Terms forbid building databases or permanent copies of API content. robots disallows `/store/getreviews`. |
| apple-app-store | no | The rating route returns reviews "for your app". The Media Services Terms forbid any automated process that performs "measurement, analysis, or monitoring" of content or services, and limit use to "personal, noncommercial purposes". |
| gitlab-com | no | The API Terms prohibit "bulk collection or scraping of information" through the APIs, which is the SROS route. robots disallows `/api/v*`. |
| codeberg | no | robots disallows `/api/` for every agent. No API or reuse grant exists, and contributors own their content. |
| kernel-org-bugzilla | no | No terms exist for the Bugzilla host. The CC BY-SA statement covers content on www.kernel.org, and whether it reaches third-party bug reports is not stated. A robots file that does not disallow a path grants nothing. The host now serves an anti-scraping challenge (summarised retrieval, not decisive). |
| trustpilot | no | The consumer terms prohibit "text mining, data mining or web scraping" for any purpose and commercial exploitation. robots disallows the whole API host. The API covers only a paying business's own reviews. |

## 6. Selection

**No candidate is eligible, so none is selected.** The deterministic selection rule (most unsupported
business dimensions unlocked through structured fields, fewest new ontology assumptions, then the simpler
official route) was never reached. **No least-bad source was chosen.**

Because nothing is selected, deliverables 7 and 8 (structured fields and deterministic propositions of the
selected source) are empty by design. §4 records, per candidate, what each route **would** have exposed.

## 7. Source reviews

**No `local-private-research-v1` review was appended and no source was registered.**
- A blocking local review changes no gate outcome. ADR-027 already refuses a source with no review under
  the declared profile.
- Several verdicts are `UNCLEAR` on questions that need legal judgement, and a review must not settle
  those.
- Registering an unregistered source only to record a refusal would be the speculative catalog entry the
  brief forbids.

The source catalog and every historical review are byte-identical.

## 8. The GitHub special case

The brief anticipated that GitHub might be blocked only by its open-access publication condition. **It is
not.** Committing to open-access publication would leave three blockers standing:
- §7's research permission covers only **non-personal** information, and issues carry usernames.
- Storage and model processing would still have no grant.
- The canonical duplicate target is not exposed on read routes.

No product change was made, and none is proposed as a workaround.

## 9. Operator decision required

No implementation mission for a first-person source can start until the operator chooses the next
strategic path.

- **A. Start N08:** an authorised first-person text semantic-extraction contract. It needs a D-12
  decision, external-model-transmission reviews and human reference labels. It makes already-approved
  first-person text usable, starting with the Stack Exchange questions SROS already holds.
- **B. A documented product decision** that would satisfy a source's publication or licensing condition.
  This mission found **no single condition** whose satisfaction alone would qualify a candidate. B is
  therefore not currently actionable without further qualification.
- **Also left open by the evidence:** written permission from an operator such as Valve, Trustpilot or
  Codeberg. Requesting it is an outward action that needs its own approval.

## 10. Constraints Mission 1.85.2 must inherit

Mission 1.85.2 cannot be a source-implementation mission. Whatever it is:
- **It must not collect** from any of the eight candidates, and must not treat robots silence, an
  own-account API or a summarised page as permission.
- **It must not reopen these verdicts** without newly retrieved first-party evidence or operator
  correspondence.
- **It must not change the product** to satisfy a publication condition without a recorded operator
  decision.
- **N05 is independent of the source decision** and is the recommended content of Mission 1.85.2 (§11).

## 11. N05 minimal repair brief

**Current behaviour.** In `packages/evidence-aggregation/python/sros_evidence_aggregation`:
- `independence.py` `_group_key` gives each `KNOWN_DEPENDENT` lineage its own `DECLARED_DEPENDENT` group.
- `engine.py` saturates every group.
- `levels.py` computes `independent_groups = [g for g in support_groups if g.kind is not GroupKind.UNKNOWN]`.

A worked example (every q = 0.6):

| Inputs | Groups | Strength | Level |
|---|---|---|---|
| 2 records in lineage g1 + 2 in g2 | 2 declared-dependent | 0.84 | **2** "2 supporting group(s) of established independence" |
| 4 unknown | 1 unknown bucket | 0.60 | 1 |
| 2 known independent | 2 independent | 0.84 | 2 |

**Declaring dependence currently scores exactly like proving independence, and better than unknown.** No
live data is affected: all 112 evidence rows are `UNKNOWN` and no production code writes a dependent state.

**Intended invariant.** Framework §10 counts groups "of established independence". "Repeated means separate
observations, not separate copies." `KNOWN_DEPENDENT` establishes membership in a lineage, not independence
between lineages. So: **a declared-dependent group is one origin, distinct declared origins are not
established as independent of each other, and only `INDEPENDENT` groups count toward the repeated-signal
and multi-source thresholds.**

**Minimal safe repair (Option A, recommended).**
1. `levels.py`: count `g.kind is GroupKind.INDEPENDENT` only.
2. Keep the existing unknown-only blocked message byte-identical.
3. Add a separate clause naming declared-dependent lineages that do not count.

Saturation, the four masses, grouping, and Levels 4 and 5 are unchanged. The counted set becomes a subset of
the old one, so **no result can become stronger**. Bump `ALGORITHM_VERSION` 1.0.0 → 1.1.0 in a second
commit, after a byte-identical replay.

**Rejected here (Option B).** Also collapsing lineages in saturation would lower contradiction strength and
**raise** a score in a verified case (9.6 → 24). It is a calibratable semantic choice, not a repair.

**Affected.**
- **Code:** `levels.py` (line 143, blocked messages, docstrings), comments in `independence.py`,
  `masses.py` `ALGORITHM_VERSION`.
- **Tests and pins:** new tests in `test_evidence_aggregation.py`. Its reproducibility fixture moves from
  level 3 to 2.
- **Framework text:** §7 and §10, the calibration strategy §2, the `docs/CLAUDE.md` aggregation invariant.
- **Generated docs:** `evidence-aggregation-sensitivity-v1.md`, header only if the version is bumped.
- **Strings to preserve:** three `docs/data` resolution artifacts pin unknown-only blocked strings, and
  tests elsewhere assert the substring "established independence".

**Differential cases required** (Option A):

| # | Case | Before → after |
|---|---|---|
| 1 | all unknown | level 1 → 1, reason text byte-identical |
| 2 | dependent g1 + unknown | 1 → 1, message gains the declared-dependent clause |
| 3 | g1 ×2, g2 ×2 | **2 → 1** |
| 4 | three lineages across two families | **3 → 1** |
| 5 | two known independent | 2 → 2 |
| 6 | independent + dependent | **2 → 1** |
| 7 | three independent across two families + one dependent | 3 → 3 |
| 8 | ten copies in one lineage | 1 → 1 |
| 9 | contradiction from two lineages against unknown support | masses unchanged |
| 10 | contradiction only | unchanged |
| 11 | a single dependent `MARKET_ACTIVITY` record | level 4 → 4 (Levels 4/5 untouched) |
| 12 | the reproducibility fixture | 3 → 2; forward and reversed canonical JSON equal |
| 13 | shuffled inputs for every case | identical canonical JSON |
| 14 | masses sum to one | holds everywhere |
| 15 | live replay: every pinned aggregation artifact, sensitivity `--check`, real rows | byte-identical before the version bump |

**Out of scope for the repair:**
- Levels 4/5 accepting dependent provenance.
- The saturation operator, `max()` within a group, the masses and the score.
- Profile thresholds and calibration status.
- Contract enums, migrations and the gateway.
- Dependence detection (N06) and any writer of dependent or independent states.
- The opportunity engine's separate independence model.
- Historical artifacts recording algorithm 1.0.0.

## 12. Verification

- **`test_first_person_source_qualification.py` checks:**
  - the frozen digest recomputes, and every frozen candidate is evaluated exactly once;
  - registration state matches the catalog, and every evidence row is first-party and official;
  - raw-verified rows match a complete raw read, and no raw read hit a data endpoint;
  - the six activities are assessed separately, and every verdict other than silence cites evidence;
  - no approval without a granting document, and eligibility follows the stated rule;
  - every decisive reason rests on a raw-verified document;
  - the outcome follows from the candidates, and the roadmap agrees with the record.
- **Roadmap test:** `test_business_evidence_roadmap.py` still passes with N01 marked
  `NO_GO_OPERATOR_DECISION_REQUIRED`, N02 unbound, and N05 assigned to 1.85.2.
- **Unchanged:** the source catalog and every historical review (no diff), and the canonical research
  counters (read before and after).
- **Locally:**
  - ruff format and check are clean over 1192 files;
  - the source registry validates (29 sources, 45 evidence records, 0 warnings);
  - the three documentation gates re-derive;
  - `git diff` against main shows 0 lines in the source catalog;
  - the opportunity-engine suite passes **4091 tests** (4035 before, plus the 56 new ones);
  - no new or edited file contains a carriage return.
- **Not run:** no semantic-generation probe was needed for these changed files.

**Stopped here.** No source selected, no collector, no research data, no model call, no V11, no
Opportunity #2. Mission 1.85.2 was not started.
