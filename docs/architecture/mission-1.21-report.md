# Mission 1.21 — Source-Native Issue Identity Evidence

**Sprint 1. Authorized by the Mission 1.21 brief §0-§38.**

> ## EXPLICIT ISSUE IDENTITY ROUTE = BLOCKED BY SOURCE GOVERNANCE
>
> **The structure exists.** Three public trackers document a publisher-declared
> canonical duplicate relation as issue state. Mission 1.20's proposed next route
> is real, and this mission found it.
>
> **The access does not.** Every candidate publishing a usable data licence also
> publishes a robots directive disallowing the API path, and the only deployment
> whose directive permits the API path publishes no data licence at all.
>
> **0 acquisitions, 0 records, 0 Signals, 0 Claims, 0 Evidence, and the catalog
> unchanged at 29 sources.** The whole output is one Authoritative document and
> the tests that pin it, so the next mission starts from retrieved documents
> rather than from a search.
>
> Per §32: both deterministic routes are now exhausted, and **Mission 1.22 should
> be Semantic Problem Equivalence / INFERRED Claims V1.**

Candidate landscape:
[`issue-identity-candidates-v1.md`](../data/issue-identity-candidates-v1.md).
Pre-registration:
[`mission-1.21-acquisition-preregistration.md`](mission-1.21-acquisition-preregistration.md),
committed in `824469b`.

---

## 1. PRE-FLIGHT — were the two Mission 1.20 corrections made?

**Yes, both, in prose and without acquiring anything.**

**A. Root-cause descriptions.** The 1.20 report described the three Docker
examples as *a file mode*, *a path absent from the image* and *a PATH lookup*.
Useful sentences for a reader; **not source-native structured facts, and not the
product of any deterministic step.** The table now separates the source's own
bytes from the analyst reading of them, and the deterministic finding is restated
without that column:

1. three records share the exact 182-character wrapper;
2. their suffixes diverge;
3. **no approved deterministic normalization rule can justify collapsing those
   suffixes into one problem identity.**

Corrected in the 1.20 report, `docs/CLAUDE.md`, `PROJECT_MANIFEST.md`, the Stack
Exchange source document and the comment above `OCI_ROOT_CAUSES` in the test
module. The sample itself is untouched.

**B. "Not fixable by narrowing further".** That claimed more than 89 questions
can carry: an experiment cannot establish that no conceivable narrower corpus
would ever expose a source-native identifier. The wording is now the project
decision it actually is — **the project will not spend another mission trying to
obtain repeated-problem identity by deterministic Stack Exchange query
narrowing** — resting on the finding that the current approach has reached a
semantic boundary.

---

## 2. DISCOVERY

### What shapes were considered

| Shape | Relation, from first-party API documentation | Passes §5 |
|---|---|---|
| **Bugzilla** | `dupe_of` — *"The bug ID of the bug that this bug is a duplicate of. If this bug isn't a duplicate of any bug, this will be null."* | **yes** |
| **Launchpad** | `duplicate_of_link` and `duplicates_collection_link` — *"MultiJoin of bugs which are dupes of this one"* | **yes** |
| **Debian BTS** | `merge` / `merged-with` | **yes** |
| **Jira** | `duplicates` issue link | weakly — a link type, not a field on the issue |
| **GitLab** | duplicate closing is a quick action and a system note | **no** — no canonical field |
| **GitHub** | `state_reason` records closure as duplicate; the TARGET is not a documented field | **no**, and it is `RESTRICTED` and was not reopened (§4) |

**The existing registry contained no usable candidate.** Only `github` carries
`issue-reports`, and §4 forbids reopening a restricted source because its data
model is attractive. No new governing evidence was sought for it and none
appeared in passing.

### Winner, runner-up, third

| | Identity relation | Data licence | Minimisation | Access directive | Verdict |
|---|---|---|---|---|---|
| **TDF Bugzilla** | `dupe_of` | **CC BY-SA 4.0** on the deployment | **`include_fields`, verified** | **`Disallow: /`; `/rest/` not allowed** | RESTRICTED |
| **Launchpad** | both directions | metadata *"freely for any purpose"* | **none — 41 fields, allowlist ignored** | **`Disallow: /api/`; names Claude agents; `ai-input=no`** | RESTRICTED |
| **Mozilla Bugzilla** | `dupe_of` | **not addressed** | `include_fields` | `Disallow: /`, `Crawl-delay: 30` | not registered |

Also examined: **Debian BTS** (real merges, no BTS data licence, `Disallow: /`)
and **bugzilla.kernel.org** — **the only deployment whose robots directive
permits the API path**, and it publishes no data licence at all. The one open
door leads to a room with no permissions in it.

### Why the winner won, and then lost

**TDF won the data question outright.** Its own front page states that all
contributions to The Document Foundation Bugzilla are released under **CC BY-SA
4.0** — a licence on the *tracker*, which is the §11 distinction made by the
operator rather than by us. TDF states licences **per property**: website CC
BY-SA 3.0, wiki CC BY-SA 3.0 Unported, Bugzilla CC BY-SA 4.0. Three properties,
three statements, three versions — nobody copied a footer.

**And minimisation would have been the best in the catalog.** A probe returned
exactly the six requested fields:

```json
{"bugs": [{"status": "CLOSED", "dupe_of": null, "product": "LibreOffice",
           "resolution": "FIXED", "component": "LibreOffice", "id": 29381}]}
```

No reporter, no assignee, no CC list, no comments — absent from the wire.

**It lost on the access layer, and that layer is separate by this repository's
own doctrine.** Mission 1.18 established it for Stack Exchange: *the API Terms
decide ACCESS, the content licence decides REUSE.* There the API Terms supplied
the access grant. **TDF publishes no API terms at all, and its only access
statement is negative** — `robots.txt` is `User-agent: * / Disallow: /` followed
by an allowlist of six CGI paths, none of them `/rest/`.

**The file is curated, not boilerplate.** It allows `/show_bug.cgi` while
disallowing `/show_bug.cgi*ctype=*`, and disallows `/page.cgi*id=user_activity*`
specifically. Somebody was making choices, and `/rest/` is not among the ones
they made.

Reading the licence as covering the fetch would be grant-by-absence where the
operator did not leave an absence — the reading rule 8 of the registry contract
forbids by name.

**This is an SROS POLICY DECISION, not a legal conclusion** (Mission 1.22 §0).
What is established is that **no sufficient positive access basis for the
intended automated route was established under this repository's own rules**, and
that **the published robots directive disallows that route**. Together those make
the source fail closed here.

**Nothing here claims that robots.txt by itself makes REST access unlawful.**
That is a legal question this system does not decide (`source-registry-v1.md` §0:
this is not a legal decision engine). A different operator, a different posture or
an answer from TDF could all change the SROS decision without anything about the
law having changed. The fail-closed outcome stands and its basis is ours.

---

## 3. GOVERNANCE

**Local-private assessment: `RESTRICTED` for both candidates**, with
`automated_access` and `api_use` `NOT_PERMITTED`. No commercial-profile decision
was inherited and none exists for either.

**Neither is registered in the catalog, and that is a second finding** (§7.1). A
registered source must carry a LEGACY-profile review: `SourceRecord.review` is
typed `PolicyReview | None`, but eighteen tests and two generated documents assume
it is present, because every source registered before now was first assessed
commercially. These two were assessed only under `local-private-research-v1` --
the first time that shape has arisen.

**TDF Bugzilla**, everything the profile needs, granted — and unreachable:

| | |
|---|---|
| Rights basis | CC BY-SA 4.0, stated on the deployment |
| Commercial-purpose use | **PERMITTED** |
| Storage / retention / derived analytics | **PERMITTED** |
| Model processing | `NOT_ASSESSED` — the deterministic design needed none, and §9 says not to demand a permission the work does not use |
| Official API | Bugzilla REST, no authentication, `include_fields` verified |
| Public-only guarantee | structural: the API documents that authentication exists *"to see non-public information"*, and this deployment holds no credential |
| Personal data | would have been **absent from the wire** |
| **Automated access** | **NOT_PERMITTED** — the deployment's robots directive |

**Launchpad**, two independent blockers, and the second is the durable one:

- **Access.** `robots.txt` disallows `/api/` for every agent, names **ClaudeBot,
  Claude-User and Claude-SearchBot** in an AI-agent block list with `Disallow: /`
  and `DisallowAITraining: /`, and sets `Content-Signal: ai-train=no, search=yes,
  ai-input=no`.
- **Minimisation.** A probe returned **41 fields including `owner_link`**, and a
  field allowlist changed nothing. There is no field selection for an entry, so
  acquiring the relation means fetching a person link and discarding it — the
  practice Mission 1.18 refused by name.

**Permission can change with a message; an API's field model cannot.** That is
why the second blocker is recorded as the more important one.

**Unresolved rights, written down and not asked.** Whether TDF intends its robots
directive to cover programmatic REST use is the whole verdict there, since every
other assessment is favourable. **No message has been sent to any operator**, no
`OPERATOR_CORRESPONDENCE` evidence exists anywhere in the catalog, and a test
asserts it.

---

## 4. RESOURCE, PRE-REGISTRATION, REAL DATA

**Pre-registration committed before any substantive issue content,
duplicate-bearing corpus or duplicate-density result was inspected** (`824469b`),
naming the deployment, resource `bug/LibreOffice/Writer`, the window, the caps,
the field allowlist and the two-step design. It is kept as written.

**Two minimal metadata-only reachability probes had already occurred**, and this
report originally said the commit came "before content inspection" without that
qualifier — too absolute for what had happened (Mission 1.22 §0). The probes are
unchanged, disclosed in the section below, and were feasibility checks against
§5 and §12 rather than inspections of issue content.

**No acquisition was performed.** The review refused the route before the
acquisition step, which is the gate working in the order it is supposed to.

**The `summary` field was deliberately excluded from the allowlist**, and the
reasoning survives the mission: `dupe_of` is the entire identity relation, so
leaving the text behind would have made §26's "text similarity is insufficient"
structurally true rather than promised. A hard negative you cannot violate is
better than one you agree not to.

### A process failure of ours, disclosed

**Two probe requests reached TDF's `/rest/` before its robots.txt was read.**
`limit=2`, metadata only — six fields, no summaries, no comments — made as
feasibility checks against §5 and §12.

That was the wrong order. **No request has been made since the directive was
read**, no acquisition was performed, nothing was persisted, and no record from
this source exists in any database.

**The corrective rule:** robots.txt is part of reachability checking and is read
**before** the first probe, not after. It is recorded in the source review and
asserted by a test, so it is not a promise made once in prose.

---

## 5. SIGNAL / CLAIM / EVIDENCE

**None of any kind**, and the mission never reached the question. There was no
acquisition, so there was no corpus, so §21's inspection and §22's S0/S1 decision
did not arise.

**No ReliabilityAssessment** (§29). The 18 Wikimedia Evidence rows keep their
`UNCATEGORISED` / `UNKNOWN` / level 1 / `NON_SCORABLE` state exactly as Mission
1.19 left them, and nothing was scored.

---

## 6. BOUNDARIES

| | |
|---|---|
| Reporter / person inference | **none** — no identity acquired, and no claim exists to be wrong |
| Text similarity, fuzzy matching, embeddings | **none** — no code, no corpus |
| INFERRED Claims | **0** — recommending Mission 1.22 is not beginning it, asserted by test |
| Opportunities / embeddings / scores | **0** |
| Existing sources | **unchanged** — nothing recollected or mutated |
| Mission 1.18 and 1.20 S0 results | **untouched** |
| GitHub | **not reopened** |
| Backlog (§28) | **not touched** |

---

## 7. QUALITY

### Counts before and after

| | Before | After |
|---|---|---|
| RawRecords | 148 | **148** |
| NormalizedRecords | 148 | **148** |
| Signals / Claims / ClaimRevisions / Evidence | 26 / 26 / 26 / 26 | **26 / 26 / 26 / 26** |
| ReliabilityAssessments | 1 | **1** |
| Opportunities / Embeddings / Scores | 0 | **0** |
| Registered sources | 29 | **29** |

**No number moved at all**, which is the right shape for a mission whose product
is a governance finding rather than data.

### 7.1 A registration attempted and reverted, with the blast radius counted

The two candidates were briefly registered before it emerged that a registered
source must carry a legacy-profile review. **Registering them would have meant
making that review optional catalog-wide** — a change to what a registered source
IS, breaking eighteen tests and two generated documents — which is an
architectural change that belongs in its own mission with an ADR rather than in a
source mission's diff (`docs/CLAUDE.md` §Change control).

**So the registration was reverted rather than made to fit**, and the two rows
were removed from the local database. The FK closure was read first, and the
blast radius was counted rather than assumed:

| | |
|---|---|
| `registry.sources` | −2 |
| `source_access_profiles` / `source_policy_reviews` / `source_signal_coverage` | −2 each |
| `source_capabilities` | −9 |
| `source_policy_evidence` | −6 |
| **Every research table** | **unchanged** — 148 / 148 / 26 / 26 / 26 / 26 / 1 |

**The follow-up is named rather than left implicit:** decide whether a source may
be registered under a modern profile only, and if so, make the legacy review
optional everywhere it is assumed.

### Did all gates pass?

Zero-dependency suites, all pytest suites, the seven validators plus
`check_env_template` and `assert_registry_grants_nothing`, contract generation
`--check`, the four generated-document checks, ruff, ruff format, mypy, and the
two CI inline grep guards.

`test_issue_identity_route_blocked.py` pins the decision: that the relation is
real, that both sources are `RESTRICTED` with the robots evidence recorded, that
a content licence did not grant the fetch, that no collector or record kind was
created, that the probes are disclosed, and that no operator was contacted.

---

## 8. ARCHITECTURAL CONSEQUENCE

**Both deterministic routes to repeated-problem identity are now exhausted, and
they failed for three different reasons:**

1. **Text-derived identity, broad** (Mission 1.18): the only key was a tag, and a
   tag is a subject.
2. **Text-derived identity, narrow** (Mission 1.20): exact tool-specific
   diagnostics were plentiful and they name the error envelope, not the failure.
3. **Source-native identity** (this mission): the relation exists and is
   documented in three trackers, and **no deployment carrying it can be reached
   under this profile.**

The third failure is the least expected and the most informative. It is not that
publishers do not record issue identity — they do, carefully, and one of them
licenses the result under CC BY-SA 4.0. It is that **a generous content licence
and a permissive access posture are two different documents**, and this
repository has treated them as separate layers since Mission 1.18. This is the
first time the separation blocked a source whose licence was perfect.

**So the next architectural mission is semantic INFERENCE**, per §32 — and it
arrives with its difficulty already measured rather than assumed. It must decide
whether two failure descriptions are the same problem, which is:

- an **`INFERRED` Claim by construction**, needing a stated reasoning step and a
  contract for what a model may assert;
- currently **forbidden**, deliberately and by name in `docs/CLAUDE.md`;
- the thing Missions 1.18 and 1.20 proved deterministic text cannot do, and
  Mission 1.21 proved no reachable publisher will do for us.

**Two doors are worth leaving unlocked**, both recorded and neither pursued: a
question to The Document Foundation about whether its robots directive is meant
to cover REST use, and `bugzilla.kernel.org`, whose directive permits the API
path and whose data carries no licence — a governance question of exactly the
kind this repository knows how to ask.

**And one house-keeping question** (§7.1): whether the catalog should accept a
source reviewed under a modern profile only. It blocked this mission's
registration and it will block the next one that finds a candidate this way.

**Nothing about this mission's result makes inference safe.** It makes it the
next thing that has to be designed carefully, which is a different statement.
