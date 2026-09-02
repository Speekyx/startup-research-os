# PROJECT MANIFEST — Startup Research OS

Version: 1.43
Status: Foundation
Owner: Speekyx (GitHub: `@Speekyx`)
Repository: startup-research-os
Last amended: 2026-09-02 (Sprint 1 / Mission 1.20)

---

# Version History

This manifest is amended in place with an explicit version bump and a changelog
entry. Git history plus this section provide the traceability that
`docs/CLAUDE.md` §Change control requires.

## 1.43 — 2026-09-02 (Sprint 1 / Mission 1.20)

Authorized by the Mission 1.20 brief §0-§33.

**OUTCOME S0, AND THIS ONE CLOSES A DIRECTION.** A deliberately narrow Stack
Overflow acquisition -- 89 real questions tagged `docker` over one pre-registered
month -- produced **0 Signals, 0 Claims, 0 Evidence**. 89 more observations and
not one more Signal, which is the honest shape of the mission.

**THE FINDING IS NOT "NO REPEATS WERE FOUND".** Three questions share **182
characters** of exact, stable, tool-specific Docker daemon diagnostic -- far more
than any signature rule would demand -- and the shared string ends at `exec: "`,
exactly where the wrapper stops and the failure begins. After it the source's own
bytes read `permission denied`, `no such file or directory` and `executable file
not found in $PATH`. **Describing those as a file mode, a missing path and a
`$PATH` lookup is an ANALYST reading rather than a source-native fact** (Mission
1.21 §0); the deterministic finding is that the suffixes diverge and no approved
normalization rule can collapse them into one problem identity. **Support is 3 at every
prefix length up to 182 and 1 from 184.** A rule needs a length, and every length
is either the envelope or the instance. Across all 89 questions **no error line
of 40 characters or more repeats verbatim in two of them**, and every key that
does have support (`no such file or directory` 5, `connection refused` 3, `exit
code 1` 3, `ValueError` 2) is a string any tool in any language emits.

**WHY THIS S0 SETTLES WHAT MISSION 1.18's DID NOT.** That failure had an
explanation -- a language tag selects a subject -- and the fix was to narrow.
This mission made that move, the narrow corpus delivered exactly what a signature
rule wants, and it failed for a deeper reason: **a diagnostic names the ENVELOPE,
and what makes two failures the same is underneath it.** So the failure is not in
the acquisition. **What follows is a PROJECT DECISION and not a proof** (Mission
1.21 §0): 89 questions cannot establish that no narrower corpus could ever expose
a source-native identifier. What 1.18 and 1.20 establish is that the current
approach has reached a **semantic boundary**, and the decision taken on that
evidence is that **the project will not spend another mission seeking
repeated-problem identity by deterministic Stack Exchange query narrowing.** The remaining directions are semantic INFERENCE --
forbidden today and an `INFERRED` claim by construction -- or a source with
**explicit issue identity**, where the publisher links two reports of one fault
and the judgement sits with somebody who has the context. The second is smaller
and more honest, and every registered candidate of that shape is `RESTRICTED`.

**THE ACQUISITION WAS PRE-REGISTERED IN ITS OWN COMMIT**, before any question
content was read, so git history shows the order rather than the report asserting
it. Docker was selected on stated criteria and needed no tie-break: Kubernetes is
a platform rather than a tool, and Podman's volume would have made the window a
guess -- and a guess returning eight questions produces an S0 that tests nothing.
No count query was run to compare candidates, because that is selection on
expected yield.

**TWO OVERSTATEMENTS CORRECTED FIRST, both in prose.** A TED award notice does
not state *what one public buyer paid one supplier*: BT-161 is the value of ALL
contracts awarded, options and renewals included, published rather than paid and
lawfully withholdable (Mission 1.15.12). Corrected in four current documents;
ADR-029 keeps its argument and gains a dated note, and the applied migrations,
the catalog review notes and the historical reports are left as records. And *"the
portfolio observes no PERSON"* was too broad -- what is missing is a **stable
requester identity across repeated interactions**, and the repair is the sentence
rather than an acquisition.

**No governance delta, no collector bump, no new record kind.** Changing the
value of an authorised query parameter is the same activity on the same resource,
and the tag restriction belongs to acquisition and provenance rather than to the
shape of one question. **Counts: 148/148 records, 26/26/26/26 Signals, Claims,
Revisions and Evidence, 1 assessment, 0 opportunities.** Zero identity fields
acquired, no similarity measure used anywhere in the analysis, existing sources
untouched, and no existing assertion needed repointing -- which is what an S0
should look like from the outside

## 1.42 — 2026-09-02 (Sprint 1 / Mission 1.19)

Authorized by the Mission 1.19 brief §0-§32.

**OUTCOME S1, and the blocker was a question somebody had already written down.**
Wikimedia Analytics pageviews joins the portfolio approved, collected,
normalized, derived from, claimed and evidenced: **21 RawRecords, 21
NormalizedRecords all VALID, 18 Signals, 18 OBSERVED Claims, 18 Evidence rows**,
every one NON_SCORABLE. Mission 1.18 was S0 because a truthful derivation did not
exist; this one is S1 because it does.

**H-24 IS ANSWERED, AND THE ANSWER WAS ONE PAGE AWAY IN THE OPERATOR'S OWN
DOCUMENTATION.** Mission 1.8 downgraded this source on a named question: are
aggregate pageview COUNTS Licensed Material under CC BY-SA? That framing had one
possibility it did not consider. The Analytics API access policy carries a
section headed *Data licensing* whose entire content is *"Data provided by the
API is available under the CC0 1.0 license"* -- not the documentation-site footer
Mission 1.7 misread, but a dedicated heading about the data the API returns.

**CC0 1.0 IS THE STRONGEST BASIS IN THE PORTFOLIO, and it is the first instrument
here to waive the sui generis database right BY NAME** -- the right that has
blocked TED for eleven missions. It resolves nothing about TED; it shows what a
resolution looks like. Storage, retention, commercial use, derived analytics and
model processing come from one instrument.

**THE OBLIGATIONS RUN THE OTHER WAY, AND THAT IS THE STRUCTURAL FIRST.** Every
earlier source imposed conditions on the OUTPUT. CC0 imposes none. What Wikimedia
imposes is a condition on the REQUEST -- the API requires a User-Agent and clients
without one *"may be blocked without notice"* -- so the collector gained a fifth
gate that refuses to open a socket when the transport would send an identity the
review did not declare. `source-client-identification` was built because a
condition named it, in that order (ADR-028), and Mission 1.8's assertion that no
such capability existed moved rather than being deleted.

**ATTRIBUTION IS A COURTESY HERE, NOT A CONDITION** -- a portfolio first. CC0
imposes none, a credit is rendered anyway because a derived surface should say
where its numbers came from, and **no condition asserts a duty the licence does
not create**, so a later reader can tell the two apart.

**A FIFTH RECORD KIND AND A FOURTH QUANTITY FAMILY.** `content_request_count`
(migration 0025), named for a SHAPE and saying REQUEST rather than VIEW because
the operator's definition is *"a request ... that receives a response of 200 OK or
304"* and "view" implies a person looked. `audience.class` is REQUIRED: the same
item on the same day carries a different count for `user` than for `all-agents`.
`CONTENT_REQUEST_VOLUME` (ADR-032, migration 0026) exists because widening
`MEASURED_SERIES` would not have cost `metric` its meaning the way a procurement
value would -- **it would have cost the FAMILY its meaning**, by making a
page-request change and a population change the same kind of quantity.

**THE CONFOUNDER IS IN THE RECORD, NOT IN A CAVEAT.** Both members of a
`content-request-change` are the SAME item, so every item-level confounder
cancels exactly -- which is why the cross-item contrast was considered and NOT
implemented. The calendar does not cancel, and the sample shows it: 2024-03-02
and 03-03 are a weekend and both larger articles fall ~40 per cent. That makes an
INFERENCE unsound rather than the subtraction untrue, and the signal type, the
migration and every Claim say so in their own words.

**Runner-up recorded rather than discarded.** `npm-registry` has higher marginal
novelty on adoption and fails rule 8: its Open-Source Terms grant replication via
the Public APIs and say nothing about `derived_analytics` or `model_processing`.
Its retrieved evidence is written down so a later mission starts from documents
rather than repeating the retrieval. `pypi` is third: no official download-count
route, and a documented history of over-approval in this repository.

**Two Mission 1.18 overstatements corrected first (§0).** Fifteen questions are
fifteen published observations, **not fifteen people** -- author identity was
never acquired, so the repair is the sentence. And *"no source observes the same
subject twice"* was too broad: GDELT and World Bank both re-observe a stream. The
precise gap is **no Evidence establishing repeated comparable USER-PROBLEM
instances for one narrowly defined problem**, and it is still open.

**A latent validator defect, exposed by the third migration to widen one
constraint.** `strip_constraint` stopped only at a depth-zero comma, which never
occurs inside a folded `ALTER TABLE ... ADD CONSTRAINT` -- so stripping a
superseded definition deleted every later ALTER with it, and a closed enum with a
CHECK reported none. Fixed at the scanner. **Counts: 59/59 records, 26/26/26/26
Signals, Claims, Revisions and Evidence, 1 assessment, 0 opportunities.** No
reliability invented, Gateway defect untouched and its tripwire grew to eight

## 1.41 — 2026-09-02 (Sprint 1 / Mission 1.18, completed)

Authorized by the Mission 1.18 brief. **Supersedes 1.40, which reported the same
mission when only its governance half was done.** Stack Exchange now has a
collector, a record kind, a normalizer and real normalized data.

**OUTCOME S0: zero Signals, zero Claims, zero Evidence, and that is the result.**
Not blocked, not deferred, not insufficient data -- a derivation was considered
against 15 real questions and correctly produced nothing.

**A tag is a SUBJECT, not a PROBLEM, and the sample proves it rather than the
argument.** 15 questions, 35 distinct tags, **three** tags appearing more than
once, **no two questions sharing a complete tag set**, and no repeated quoted
identifier in any title. `python` is on all 15 because it is what the query asked
for. `google-cloud-platform` groups duplicate Eventarc processing, a `setup.py`
type error and Google Docs text extraction. `deep-learning` groups the same
`setup.py` error and a backpropagation question. **One question is in both
cohorts**, which one repeated problem cannot be. Getting past that would take
semantic inference over question text -- an INFERRED step this mission does not
authorise. **The cohort was not weakened and no second query was run to find a
friendlier sample.**

**A fourth record kind, and the first named for a SHAPE.** `community_question`
(migration 0024, one registry row, no schema change). Not
`stack_exchange_question`: a question on a public Q&A site is a shape other
sources share, and naming the kind after the first source to reach it would make
the vocabulary a list of vendors. The SITE is a field; the source is provenance.
Widening any of the three existing kinds would have made it worse for a new
source's sake.

**`stack-exchange-question@1.0.0`, and every record is VALID -- which no adapter
here had achieved.** GDELT is `PARTIAL` for H-29 and H-30, TED for H-37; nothing
is open here. **The first adapter whose period is `ESTABLISHED` on the source's
own evidence**: a Unix epoch second is an unambiguous instant, so `observed_at` is
a real moment for the first time in this repository. The payload states its own
limits -- the tags carry the site's scheme, `accepted_answer_semantics` says the
asker accepted an answer and not that the problem is resolved, `engagement`
counters are *"not importance, not demand, not market size"*, and `author` is
`null` because it was never acquired. A record carrying `owner`, `last_editor` or
`comments` is REFUSED at normalization rather than stripped, and a record with no
canonical URL is refused because CC BY-SA needs the link.

**Two defects the tests found in paths the real data never took**: the normalizer's
failure constructor read `record.raw_record_id`, which `RawRecordView` does not
have, so every refusal would have raised `AttributeError` instead of a
`NormalizationFailure`; and a missing body reached a `QualityReason` member that
does not exist. The second was fixed by NOT adding the member -- the kind does not
require a body, no existing code would truthfully name the absence, and a wrong
code where a consumer branches is worse than `question.body: null`.

**Counts: 38 RawRecords, 38 NormalizedRecords, 8/8/8/8 Signals, Claims, Revisions
and Evidence unchanged, 1 assessment, 0 opportunities.** Six existing equality
assertions were repointed because the repository genuinely grew from three record
kinds and three normalizers to four of each; none was weakened to a containment.
TED, World Bank and GDELT untouched; the historical 23 RawRecords not backfilled;
the Gateway profile bug not fixed; no 403 retried

## 1.40 — 2026-09-01 (Sprint 1 / Mission 1.18, governance only)

Authorized by the Mission 1.18 brief §1-§50.

**Stack Exchange APPROVES under `local-private-research-v1`, and no collector was
built.** The governance half is complete and the implementation half is not
started -- an outcome the brief's §37 did not list, stated plainly rather than
dressed as one of its four.

**The first approving review for a community-content source, and the first where
the positive rights come from a CONTENT LICENCE rather than a platform's terms.**
The two layers stay apart: the API Terms decide ACCESS and are silent on storage,
analytics and commercial use, and silence is recorded as silence; CC BY-SA 4.0
decides REUSE and grants commercial use, which mattered because local is not
non-commercial. The API carve-out removes an obstacle and **grants nothing** --
read as a standalone licence it would be a grant by absence.

**ShareAlike is AVOIDED by the profile, not answered by the review.** The
obligation attaches to Adapted Material that is SHARED and this profile shares
nothing, so the classification question did not have to be decided. Carried open,
because a review quietly relying on "we do not publish" is one deployment change
away from being wrong.

**`PLATFORM_LICENSED` was the closest call and is argued rather than set.** Users
own the content, but `THIRD_PARTY` means *separate permission from the owner is
required* -- and CC BY-SA already reaches us, so there is nobody left to ask.
Classified `THIRD_PARTY`, the resource is refused by its own scope and the source
is approving but unreachable: the wrong answer for a right-sounding reason.

**Evidence provenance is stated exactly.** The Public Network Terms and API Terms
were **operator-supplied** because this environment received HTTP 403 for both;
the Responsible AI policy was retrieved directly and is **normatively empty for a
third party** -- every operative sentence has Stack as its subject. **No 403 was
retried and no header was varied.**

**Personal data is the point of the record here for the first time.** Owner,
account, profile and comment objects are excluded AT ACQUISITION through the API's
own filter. The Data Dump route was **registered so that it could be refused by
name**, because deleting it would falsify a fact about the source to obtain a
permission.

**A gap the first CC BY-SA source exposed:** `AttributionElement` cannot express
the per-item link CC BY-SA requires, and the gap reaches World Bank and Eurostat
too. Recorded, not fixed -- a closed enum needs an ADR. Research counts unchanged
at 23/23/8/8/8, 1 assessment, 0 opportunities. No research data collected

## 1.39 — 2026-09-01 (Sprint 1 / Mission 1.17)

Authorized by the Mission 1.17 brief §1-§31.

**The registry and the runtime now agree, and no approval was inherited to get
there.** Five sources -- `world-bank`, `gdelt`, `eurostat`, `fred`, `openalex` --
gained a `local-private-research-v1` review, each version 1 of its own profile
line. **ADR-027 is unchanged and no fallback was added**, which the result proves
in both directions: `ted-eu` is still approving locally and REFUSED commercially,
and the five were refused locally until the work was done.

**Evidence reused, decisions not.** Three licence documents were re-retrieved on
2026-09-01 and confirmed unchanged (World Bank CC BY 4.0, Eurostat under Decision
2011/833/EU, GDELT's unlimited-use grant). FRED and OpenAlex refused this
environment with HTTP 403; their evidence is days old and inside the 365-day
interval, and both failures are recorded in the reviews rather than omitted.

**Four ELIGIBLE, one still BLOCKED.** OpenAlex approves and stays blocked on two
unsatisfied conditions, which is approving and eligible being different facts
rather than a failure. **OpenAlex is also the one place the local profile is
STRICTER**: it carries scholarly authorship, so `personal_data_handling` moves to
`PERMITTED_WITH_CONDITIONS` under a MINIMISED posture. Four of five were narrower
everywhere and one was not, which is why a per-profile review is not a formality.

**A gap the contract itself had named is closed for this profile.** GDELT's
context was handing collectors all three routes including the unreviewed DOC API;
`docs/CLAUDE.md` said *"restricting it is a review act"*. The local entry now
blocks `gdelt-doc-api` and `gdelt-bulk-files` **by name** (ADR-028). A narrowing
that exists only in the review text is not a narrowing.

**Two defects exposed.** `sros-source load` derived condition and evidence row ids
without the profile, so two reviews of one source sharing a condition key
collided on the primary key -- fixed generically rather than by renaming
conditions, because two profiles legitimately impose the same obligation. And the
Gateway's profile-blindness got **six times bigger** and was found in a **second
endpoint**; both are asserted as defects so they fail when fixed.

**Correction to 1.16:** all 23 RawRecords lack `use_profile` in provenance, TED's
eleven included -- no collector writes it. Research counts unchanged at
23/23/8/8/8/8, 1 assessment, 0 opportunities. No research API was called

## 1.38 — 2026-09-01 (Sprint 1 / Mission 1.16)

Authorized by the Mission 1.16 brief §0-§35.

**No source was added, and the measured blocker is the mission's product.** Ten
sources cover `problem` or `desire`; six are `RESTRICTED` on retrieved terms and
four are `REQUIRES_REVIEW`. Stack Exchange was selected on the brief's criteria
and could not proceed: the two documents its review needs are served behind an
anti-bot interstitial, and this environment cannot reach the host at all. Reddit
is equally unreachable. **No bypass was attempted, and no review was written on
unread documents** -- uncertainty is never permission.

**`problem` is nominally covered and substantively is not.** TED is the only
approving source carrying it, and what TED observes is a public buyer's
procurement need, not a user finding a tool frustrating.

**The larger finding, which nobody had noticed.** The runtime declares
`SROS_USE_PROFILE=local-private-research-v1` and **exactly one review in the
registry is under that profile**. `build_authorization('world-bank',
'local-private-research-v1')` is **REFUSED**, and so are gdelt, eurostat, fred
and openalex. **The deployment holds 15 of 23 RawRecords and 7 of 8 Evidence rows
it could not re-collect today** -- they were gathered before ADR-027 existed and
their provenance carries no `use_profile` at all. The gate is working exactly as
designed; what is missing is the review nobody has written for the profile the
runtime actually declares. It also caps every future source mission silently.

**Also corrected (§0):** the 1.15.13 authorship record. The rationale and stated
limitation were **AI-assisted in wording** and adopted by the reviewer; the
number was the reviewer's alone. The persisted assessment is untouched.

Nothing collected, created or changed. Counts identical: 23/23/8/8/8/8, 1
assessment, 0 opportunities, 0 embeddings, 0 scores. H-36A, H-36B, H-37, H-38
untouched

## 1.37 — 2026-09-01 (Sprint 1 / Mission 1.15.13)

Authorized by the Mission 1.15.13 brief §1-§30.

**The first ReliabilityAssessment in the system, and the first evidence score.**
Mission 1.15.12 stopped at an act the contract reserves to an accountable
person; this mission built the write path for it and then stopped again, at the
person.

**The tool has no defaults, and that is its whole design.** `reliability`,
`reviewed_by`, `rationale` and `stated_limitation` are refused when blank, with
no suggestion, fallback or derivation anywhere in the file. **The packet is
facts and the file is judgement:** `--packet` prints the four retrieved
documents Mission 1.15.12 established and emits a template whose basis rows are
filled and whose judgement fields are empty. A test asserts no packet contains a
`reliability` key at all.

**Recorded: `HUMAN_REVIEW`, 0.5, by `thibchm`**, over the TED procurement scope,
resting on 4 document-backed basis rows. The reviewer was shown that the
contract uses `0.5 because unknown` as its own example of a non-judgement, and
kept the value: the submitted rationale is a two-sided argument rather than a
shrug, and the stated limitation bounds it.

**The Evidence is now SCORABLE, and `q_i = min(components)` did exactly what it
is for.** Relevance, directness, extraction confidence and freshness are 1.0;
reliability is 0.5; the engine names **reliability** as the limiting component.
`evidence_score` 50.0, support 0.5, uncertainty 0.5. **The level stayed 1**,
blocked by the category gate Mission 1.15.11 deliberately left at
`UNCATEGORISED` and by unknown independence — reliability alone cannot reach
Level 4.

**Nothing was persisted downstream and nothing is calibrated.** The score
required `allow_uncalibrated` explicitly, carries its own warning, and no score
row was written. `reference-v1` stays `UNCALIBRATED` and D-03's remaining
blockers are untouched: a human review is not a calibration however careful.

**A refusal real use found.** The reviewer first submitted `<MON IDENTITÉ
RÉELLE>` as an identity. A blank was refused and a placeholder was recorded, so
the field that says who is accountable was worse protected against a template
shape than against nothing. Now refused. Counts: research data unchanged at
23/23/8/8/8/8, **ReliabilityAssessments 0 → 1**, opportunities 0, embeddings 0,
scores 0. No LLM as reviewer. H-36A, H-36B, H-37, H-38 untouched

## 1.36 — 2026-09-01 (Sprint 1 / Mission 1.15.12)

Authorized by the Mission 1.15.12 brief §1-§44.

**The first reliability review against real Evidence, and the first to reach the
end of the framework and stop. Outcome B: no assessment created.**

**What the specification said, read from the Publications Office's own eForms SDK
1.15.1.** `TOTAL_VALUE` is **BT-161**, notice-level, non-repeatable, and its
definition is *"The value of all contracts awarded in this notice, **including
options and renewals**"* — so the figure is not what was paid and not necessarily
what will be. Anything downstream reading it as revenue or a price is wrong at
the source, before any interpretation layer is involved. The normalizer's own
description said less than that and is corrected.

**The finding with the sharpest bearing on a contrast.** BT-161 carries a privacy
block (BT-195 to BT-198): the value may be **lawfully withheld** from immediate
publication and released later. A cohort built from published values covers the
**published subset**, and its maximum and minimum are the extremes of what was
published rather than of what was awarded. The missingness is not random, and an
extreme is the statistic most exposed to it.

**TED validates conformance, never truth.** 60 published rules name BT-161 and
every one is a presence, absence or notice-type constraint. There is a rule that
it must not appear in a prior information notice; there is none that the amount
is correct.

**Why no number exists to record.** `DOCUMENTED_METHOD` requires the document to
supply the value and eForms states no error rate or completeness bound;
`CALIBRATED_EMPIRICALLY` requires outcome data that does not exist;
`HUMAN_REVIEW` requires a named accountable reviewer, and a model may not stand
in for one. The contract closes the last door outright: *"No threshold labels…
No categorical mapping. Not from source type, not from evidence level, not from
anything."* **The same shape as the TED database-right acceptance** — one act
reserved to a person, and a mission that performed it anyway would defeat the
design rather than complete it.

**The inventory was re-measured, not assumed.** Mission 1.14's "7 Evidence rows,
3 scopes" is now **8 rows, 4 scopes**; TED is the fourth and overlaps none. The
count rose because a new kind of QUESTION was asked, not because observations
arrived.

**Everything orthogonal stayed orthogonal.** `observation_category`
`UNCATEGORISED`, `independence_state` `UNKNOWN`, `evidence_level` 1, all
untouched. Reliability was derived from none of the five 1.0 values around it,
guaranteed structurally: `resolve_reliability` takes scope, candidates and
supplied, and an AST test asserts the package names no confidence, level, support
or approval-state identifier. Counts unchanged at 23/23/8/8/8/8, **0
ReliabilityAssessments**, 0 opportunities, 0 embeddings, 0 scores. No LLM, no TED
API call. H-36A, H-36B, H-37 and H-38 untouched

## 1.35 — 2026-09-01 (Sprint 1 / Mission 1.15.11)

Authorized by the Mission 1.15.11 brief §1-§44.

**The TED Signal interpreted, and the sentence is the enforcement.** A fourth
template on the existing interpreter — **`observed-signal-restatement@1.1.0`**,
not a TED-specific one, because a template is specific to a Signal type and never
to a publisher. One `OBSERVED` Claim, one revision, one Evidence row, through the
production path, idempotent on redelivery.

**What the Claim says, and the three words that keep it honest.** *"…within a
bounded set of 3 `CONTRACT_AWARD_NOTICE` notices classified under `CPV` division
`90`, the largest `TOTAL_VALUE` amount at `NOTICE` scope stated in `EUR` exceeded
the smallest by 686545.02."* Shortened to *"division 90 contracts vary by
686545.02"* it becomes a claim about a population nobody sampled, and **"within a
bounded set of 3"** is what stops it. No market, no demand, no willingness to
pay, no price, no average, no trend — and no date, because H-37 is open and the
acquisition window bounded RETRIEVAL rather than the proposition.

**The cohort membership is the identity; the amount is wording.** A revised
amount appends a revision, a fourth qualifying notice is a different proposition.
The three member values are NOT copied into the Claim: they are reachable through
Evidence → Signal → `signal_inputs` → `normalized_records`, and one fact in two
places eventually disagrees with itself.

**`observation_category` stayed `UNCATEGORISED`, and it was the closest call.** A
contract award notice records a purchase, which is `MARKET_ACTIVITY`'s own first
example, and `MARKET_ACTIVITY` is the **only** gate to `EvidenceLevel` 4. What
this row carries is a maximum minus a minimum over published notices, and a
spread is a property of records rather than economic activity. Recorded as an
open question rather than settled in passing.

**Support 3 is still one source.** `independence_state` `UNKNOWN`, one Evidence
row naming one `source_id`, `evidence_level` 1, reliability **NULL** and the row
`NON_SCORABLE`. `derivation_confidence = 1.0` was not allowed to become any of
reliability, claim probability or market confidence.

**No interpretation-support threshold was invented**, because the Claim adds no
inference beyond the Signal and the contract already forbids arbitrary ones. The
seven existing Claims keep `1.0.0` and gained no revision. Counts: 23 raw, 23
normalized, 8 signals, **8 claims, 8 revisions, 8 evidence**, 0 opportunities, 0
reliability assessments, 0 embeddings, 0 scores. No LLM was called

## 1.34 — 2026-09-01 (Sprint 1 / Mission 1.15.10)

Authorized by the Mission 1.15.10 brief §1-§43.

**The Decimal invariant repaired, and the first real TED Signal.** Phase A bumped
the collector to **`ted-search-api@1.1.0`**: `json.loads(..., parse_float=Decimal)`
plus `canonical_number` on the way out, so a fractional tender value reaches jsonb
as an exact fixed-point **string** instead of a binary float. `parse_int` stays
unset, because a JSON integer was never at risk and wrapping it would change a
value that had no problem. The normalizer is **not** bumped and now declares
`supported_collector_versions = {"1.0.0", "1.1.0"}`: its own output is unchanged,
so bumping it would announce a difference that does not exist.

**A bounded acquisition designed for comparability, not for volume.** One CPV
division, one day (2023-03-01), award notices only, all declared before execution. The
first execution was **broader than declared**: `cpv_division` reached the
dataclass, the query and the idempotency key but `from_payload` never read it. A
narrowing that exists only in the caller's intent is not a narrowing, and the
test that now guards it asserts **the composed query string**, which is the only
artefact the source ever sees.

**One `TRANSACTION_VALUE` Signal.** Three award notices in CPV division 90, EUR
total values 73 415.22, 440 000 and 759 960.24, magnitude **686 545.02**
`ABSOLUTE_DIFFERENCE`, `NON_TEMPORAL`, direction `NOT_APPLICABLE`. Two notices in
the same window were excluded for being denominated in PLN or spanning a second
division, which is the comparability rule doing real work.

**Real data corrected the extractor.** The cohort scope carried only the first
member's CPV codes — invisible when every cohort had one member, plainly wrong
with three members and four codes, because the scope is what tells a reader which
market the contrast describes. Now the union of all members' codes;
**`procurement-value-contrast@1.0.1`**, the `1.0.0` row deleted after checking
the FK closure and the Signal re-derived rather than left beside its successor.

**H-36A, H-36B, H-37 and H-38 all untouched.** Counts: 23 raw (11 TED), 23
normalized (11 TED), **8 signals (1 TED)**, 7 claims, 7 evidence, 0
opportunities, 0 reliability assessments, 0 embeddings. Nothing interprets the
TED Signal: no Claim cites it and no Evidence references it

## 1.33 — 2026-09-01 (Sprint 1 / Mission 1.15.9)

Authorized by the Mission 1.15.9 brief §1-§39 and by ADR-029.

**A third Signal quantity family, and a derivation that correctly produced
nothing.** Mission 1.15.8 added the `procurement_notice` record kind and the
Signal contract binds the family to the record kind of every input, so nothing
mapped and the Signal layer was structurally unable to say anything about
procurement. `TRANSACTION_VALUE` (ADR-029, migration 0023) closes that:
it carries an amount semantic, a currency and a procurement classification and
**no metric**, which is exactly why `MEASURED_SERIES` could not be widened.

**`procurement-value-contrast@1.0.0`**, the fourth extractor. A **non-temporal**
cohort spread: basis `NONE`, direction `NOT_APPLICABLE`, no bound, no date read.
Members are ordered by amount, never by time. Four monetary semantics never mix,
two currencies never mix, nothing is converted, and no `price_paid` exists.

**It is not willingness-to-pay, and the distinction is enforced rather than
described.** That a named buyer paid a named supplier a stated amount is
established; that a market exists or that a comparable buyer would pay a
comparable amount for a different product is not.

**The real run produced ZERO Signals, and that was the correct answer for the
observations held.** (Superseded by 1.34, which acquired observations that do
form a cohort; the reasoning below is unchanged and is why.) Three
normalized notices inspected, two carrying an eligible paired amount, **two
cohorts formed, neither meeting the minimum support of two** -- the two EUR award
totals are in CPV divisions 90 and 66, cleaning and insurance, which are two
markets. Eight derivation runs recorded, no row written.

**H-37 and H-38 both remain OPEN.** The derivation avoids depending on either and
neither is closed by that. Counts unchanged: 15 raw, 15 normalized, 7 signals, 7
claims, 7 evidence, and no TED signal, claim or evidence exists

## 1.32 — 2026-09-01 (Sprint 1 / Mission 1.15.8)

Authorized by the Mission 1.15.8 brief §3-§45.

**The third record kind, and the first canonical procurement notices.**
`procurement_notice` (migration 0022) joins `numeric_observation` and
`lexical_frequency_observation` for the reason the second one was added: a notice
is a DOCUMENT carrying typed monetary facts, organisations in roles and several
distinct dates, and widening either existing kind to hold it would give a World
Bank figure an award status. It carries no `observation.value`, deliberately —
a notice has no single measurement.

**`ted-search-api-notice@1.0.0`**, the third normalizer. **One notice, one
record; lots are structured data inside it.** Four monetary semantics under their
own names with no `price_paid` and no currency conversion; amounts paired with a
currency only where there is one of each, because the source declares arrays and
states nothing about positional correspondence (**H-38**); every language kept
with no canonical display value; CPV codes as identifiers with no invented
sector; the `links` block left in the raw record.

**A published DATE does not become a moment.** `publication-date` is
`2023-03-01+01:00` — a day, an offset, and no time. The period is that day with
NAIVE bounds and **`observed_at` is NULL**. `ESTABLISHED` was considered and
refused: its definition requires the source or authoritative documentation to
state the timezone, and an offset inside one value is data rather than a
statement about what it means. Recorded as **H-37**, with the source value
preserved so closing it is a re-derivation rather than a re-collection.

**Three real notices normalized** through the production job path; a second run
persisted nothing. `73415.22` survives the whole path exactly. Raw 15 (3 TED),
normalized 15 (3 TED), and **every downstream count unchanged**: 7 Signals, 7
Claims, 7 Evidence, 0 Opportunities, 0 embeddings, 0 scores, all pre-existing and
none of them TED's. **No TED Signal, Claim or Evidence exists.** H-36A and H-36B
untouched

## 1.31 — 2026-09-01 (Sprint 1 / Mission 1.15.7)

Authorized by the Mission 1.15.7 brief §4-§8 (Phase A, resource governance) and
§9-§44 (Phase B, the collector and one bounded real acquisition).

**The first TED acquisition, and the first concrete TED resource.** TED had been
`AUTHORIZATION_READY` since Mission 1.15.6.1 and uncollectable, because a
source-level approval is not a resource-level one: the compliance entry
authorised `"datasets": []`, so every resource failed closed. Phase A authorised
**one** — `notices/eforms-contract-and-award`, eForms contract notices and
contract award notices published from 2023-03-01, through the Search API — on
Commission Decision 2011/833/EU as a `NAMED_LICENCE` with `PLATFORM_LICENSED`
content origin, and on nothing new. `resource_ready` moved NO to YES.

**`ted-search-api@1.0.0`**, the third implemented collector. Four gates before a
socket: bounds, route, resource, fields. One route with **no fallback** —
`ted-open-data-sparql` is authorised, is in the context, and is not implemented.
Bounds with **no defaults** at every level including the job payload, because
TED's rate limit is UNKNOWN and the operator acceptance behind this source is
conditioned on the queries being bounded. **No exhaustion mode**: the API's
`ITERATION` scroll retrieves every notice for a query with no limit, and the
collector sends `PAGE_NUMBER` and never a token. Four monetary semantics kept
apart under their own names, **no `price_paid`**, **no currency conversion**, no
language chosen, no lot collapsed.

**The API contract was established from first-party sources only** — the
service's own OpenAPI document and its own `checkQuerySyntax` mode, which
validates a query without executing it and retrieved no notices. It also settled
two things that could only have been guessed: the API omits a field entirely
when a notice has no value for it, so exactly one field per notice is required;
and it adds a `links` object to every notice regardless of the field selection,
which was inspected before any record was accepted and contains only the
notice's own URLs per language and format.

**One real bounded acquisition**: one HTTP request, one page, one day's window,
**3 RawRecords**. Re-run identically: 0 new, 3 unchanged. Raw records 12 to 15.

**H-36A remains NOT ESTABLISHED. H-36B remains NOT ADDRESSED.** No legal
clearance. Bulk XML, the historical CSV and the commercial profile refused
exactly as before. **No NormalizedRecord, Signal, Claim, Evidence, Opportunity,
embedding or score was created**, and the recorded human decision is byte-for-byte
the row Mission 1.15.6.1 wrote

## 1.30 — 2026-08-31 (Sprint 1 / Mission 1.15.6)

Authorized by the Mission 1.15.6 brief §4 (condition classification), §5-§6 (the
residual risk stays human and is not recorded), §7-§9 (route and field
enforcement), §10-§13 (the compliance blueprint and fail-closed rules), §14
(condition state goal), §18-§23 (persistence, scope, review changes, runtime
enforcement, provenance), §29-§32 (tests, validation, documentation, report) and
§33 (stop after the report).

| Change | Section | Authority |
|--------|---------|-----------|
| **The authorization carries only the routes the review authorised** | Canonical invariants | ADR-028, §7, §22. `context.access` held EVERY registered access profile, because an access profile is a fact about a source and the context had nothing to filter it with. TED is the first approving source whose review refuses one of its own real routes by name, and the refused route is the full bulk corpus whose database-right exposure is the open question. Its context would have handed a collector that route with its endpoint -- and the transport's host allowlist is derived from `context.access`, so the blocked host would have been allowlisted with it. Not hypothetical: it was the behaviour |
| **`AccessRestriction` could not carry it, and the reason generalises** | Engineering Principles | §7. `ACCESS_METHOD` passes when the registry records EXACTLY the approved access profiles -- a statement about the SOURCE. TED really is reachable by bulk XML: the packages are published, documented and downloadable without signing in. Making the check pass would have meant deleting a true row from the registry, which is **falsifying a fact about a source in order to obtain a permission**. The review's actual requirement is a statement about US, and the two questions both deserve to exist |
| **Two conditions moved from HUMAN_CONFIRMATION to CAPABILITY, and the rule behind it is general** | Engineering Principles | §4, §21, ADR-028. `ted-official-route-only` and `ted-personal-data-minimisation` described objective properties of a collector that does not exist, which produced a **bootstrap**: nothing could be authorised until a person confirmed behaviour, and nobody could confirm behaviour until the collector existed -- a loop whose natural break is *write the collector first*. Neither was ever about code. Both are properties of the CONFIGURATION handed to authorization. **No new taxonomy**: `ConditionVerification` still has five values, and `CAPABILITY` already means *a named gate is implemented and refuses what it must, checked against this source's real configuration* |
| **The boundary is stated with the rule, because the rule without it is an excuse** | Engineering Principles | §4, §5. A judgement, a risk acceptance, a legal conclusion or a promise about future conduct stays `HUMAN_CONFIRMATION`, and `source-review-guide.md` §9 is unchanged: *do not reword a legal obligation until it sounds checkable*. The new rule sits upstream of it -- ask first whether the condition was ever about a legal obligation at all |
| **Minimisation is a control at acquisition, never a filter afterwards** | Engineering Principles | §8, §9. `DataMinimisationProfile` had held the allowed and excluded categories since Mission 1.4 and **nothing consulted them**; `permits()` had no caller in the gate. `authorize_fields` refuses an excluded field BY NAME, an unreviewed field, and a request that states no selection. The Search API's `fields` parameter makes selection possible, so collect-then-filter is not available as an excuse: a request that discarded the contact block afterwards retrieved it. There is deliberately no method that removes fields from a collected record, and a test asserts the public callables are exactly `{permits, refusals}` |
| **Absent means unasked, in the third place it now appears** | Blocked work | §13, ADR-028. `route_authorization = None` means no route restriction was REVIEWED for that (source, profile) -- the same reading `max_files_per_job = None` already has. The four other approving sources are unchanged and that is a **named** gap rather than a silent one: **GDELT carries a second, deferred DOC API profile no review assessed**, and its context still hands a collector both. Restricting it is a review act, not a configuration edit, and §21 forbade doing it here |
| **A capability reports unimplemented when its restriction does not exist** | Engineering Principles | `source-route-binding` fails rather than passes on a missing `route_authorization`. A capability that returned no failures for a source with nothing configured would satisfy its condition BY HAVING NO RULES, which is the shape `testing-strategy.md` §31 already warns about for validators, arriving through the capability door |
| **Local review v2, appended; v1 untouched** | Product Shape | §20. The reclassification is a versioned policy artefact, so it was appended rather than written over. v2 carries every assessment, condition, open question and evidence row of v1 unchanged and differs in **exactly two** condition classifications, asserted by computing the changed set rather than by checking the two that were meant to move. v1 still records that both were `HUMAN_CONFIRMATION` when it was written |
| **The registry gained the route it had already authorised** | Product Shape | §7. The local review authorises the TED Open Data Service and the registry recorded no access profile for it, so an authorised route had no endpoint, no rate-limit record and nothing to check a host against. `ted-open-data-sparql` was registered: `OFFICIAL_API`, no authentication, rate limit **UNKNOWN** -- a fact about reachability, which grants nothing |
| **The validator walked one profile out of two, and now walks both** | Engineering Principles | Checks 3, 6, 9 and 10 of `validate_compliance_capabilities.py` read `source.review` -- the legacy profile only. It surfaced immediately: the two new capabilities, named only by TED's local review, were reported as registered-but-unused because the validator could not see that review at all. A condition existing only under a second profile had been checked by nothing |
| **The compliance loader deduplicated on the wrong key** | Engineering Principles | `SourceCompliance` has been keyed by (source, profile) since Mission 1.15.5 and `get` has looked it up that way since 1.15.5, but `load_compliance` still refused a second entry for the same source as a duplicate -- so the second profile's configuration, which is the whole point of the key, could not be loaded. TED is the first source that would ever have two |
| **THE RESIDUAL DATABASE-RIGHT ACCEPTANCE STAYS HUMAN, AND NOTHING WAS RECORDED** | Blocked work | §5, §6. Not reclassified, and it must not be: it is a person deciding to carry a risk nobody resolved, not a property of anything. The human branch is reached BEFORE any configuration is consulted, so no route authorization, minimisation profile or capability can answer it; the database still refuses a hand-set boolean. Asserted four ways, including by forging a `CAPABILITY` rewrite of the condition. **The operator supplied no acceptance and none exists.** The exact statement a later explicit action must record is written down in `ted-eu-authorization-bootstrap-v1.md` §6.2, and writing it down is not recording it -- neither is the existence of this mission, nor the fact that the deployment is local |
| **The persistence mechanism already existed and was not extended** | Engineering Principles | §18. `registry.source_condition_verifications` (migration 0007) carries source, condition, actor, decision, rationale, reference and time; the review id comes through `condition_id`, and the **use profile** through that review's `assessed_use_profile` (migration 0021). Profile scoping is therefore structural: an acceptance against TED's local review cannot reach the commercial profile, because the commercial review does not carry the condition it would clear. **No CLI verb writes a human confirmation and none was built** -- a command that records them is one flag away from a script that records them |
| **TED policy is unchanged in every dimension** | Blocked work | §3. Commercial profile `REQUIRES_REVIEW`; local profile `APPROVED_WITH_CONDITIONS`; H-36A NOT ESTABLISHED and H-36B NOT ADDRESSED under both; model training not authorised; embeddings blocked by D-12; redistribution NOT PERMITTED; bulk XML and `ted-csv` blocked at the route gate and again at the resource gate. TED did not become globally APPROVED and did not become eligible |
| **Nothing was collected, built or scored** | Forbidden During Foundation | §16, §17, §27, §33. No TED collector, HTTP client, SPARQL client, parser, normalizer or worker -- asserted against the file tree and against `SPARQLWrapper`. No network call: both new capabilities run against configuration alone. **Nothing was written to and nothing removed from any research table**, confirmed by the suite's own leak checks across 24 tenant tables and 17 global ones. TED rows 0 |
| **A recorded count did not match the database it was recorded about** | Engineering Principles | §27 asked that RawRecords 12, NormalizedRecords 12, Signals 7, Claims 7, ClaimRevisions 7 and Evidence 7 be preserved. **In this repository's local PostgreSQL every one of them is 0**, before this mission and after it -- checked with row security off, so it is not an RLS artefact. Nothing here deleted them: no test asserts those figures and none ever has, and they appear only as prose carried forward from Mission 1.5 onward. `README.md` §Research data does not travel either already states the rule that explains it -- collected research lives in whichever local PostgreSQL produced it and does not travel through git -- so **the numbers describe the database those missions ran in, not this one**. Recorded rather than quietly restated, and reproducing them here means re-running collection, normalization, derivation and interpretation |

## 1.29 — 2026-08-31 (Sprint 1 / Mission 1.15.5)

Authorized by the Mission 1.15.5 brief §4 (the required concept), §8-§10
(persistence, legacy profile, currentness), §12-§16 (runtime declaration,
context, gate, fail-closed, isolation), §20-§24 (TED as validation case),
§27-§29 (contracts, migration), §38 (ADR), §49 (documentation) and §51 (stop
after the report).

| Change | Section | Authority |
|--------|---------|-----------|
| **A verdict has a subject: `AssessedUseProfile`** | Canonical invariants | ADR-027. Every review already answered a question about a USE -- `assessed_use_case` is a required field and the catalog has said "a COMMERCIAL multi-tenant SaaS" since Mission 1.0 -- but the answer had no IDENTITY, so it could not be required, compared or matched and the gate never saw it. This corrects Mission 1.15.4's framing, which said the model never recorded the use case: it recorded it, and could not USE it |
| **Two registered profiles, and no more** | Canonical invariants | §5, §6. `commercial-multi-tenant-research-v1` is what every review from Mission 1.0 to 1.15.4 actually assessed and what a future public deployment must satisfy; `local-private-research-v1` is the current runtime. `PUBLIC_COMMERCIAL_SERVICE` was NOT created as a third: it is the first one under the name the historical prose already used, and two near-identical profiles would be the proliferation §5 warns against. A registry rather than a closed enum, because nothing branches exhaustively on it |
| **`commercial_purpose` is TRUE on both profiles** | Canonical invariants | The rule most easily taken backwards. Local deployment does not make the use non-commercial, so a commercial-use right still has to be positively granted by the source's own evidence. Asserted on every registered profile by test |
| **Currentness is per (source, profile)** | Engineering Principles | §10. Each profile keeps its own append-only version line; version 1 under a second profile is a FIRST review of a new question, not a duplicate. The database constraint moved from UNIQUE (source_id, review_version) to (source_id, assessed_use_profile, review_version), and the eligibility view emits one row per pair |
| **The gate requires the profile, with no default** | Engineering Principles | §14, §15. `evaluate_eligibility`, `build_authorization` and `verify_source` all take it second and positional. A required argument is a better guard than an assertion: mypy found all 68 call sites before anything ran, and `use_profile_id=None` meaning "the current review" would have been one careless edit from a silent fallback (`testing-strategy.md` §44) |
| **Nothing falls back, anywhere** | Blocked work | §15, §16. A missing profile raises, an unknown one is refused, a profile with no review is refused -- and none is resolved against another profile or against the source's legacy verdict. Compliance configuration is keyed by (source, profile) too, so one profile cannot borrow another's resource scope or minimisation profile |
| **The runtime declares its profile and never infers it** | Canonical invariants | §12, §34, §35. `SROS_USE_PROFILE`, read at the entry point and passed down. Never from an environment name, the host, a container, a user count or the absence of billing: a profile is a governance fact and those are infrastructural ones, and the same binary in the same container can be operated under either. There is NO default, because the convenient default is the narrow local profile -- exactly the one an operator running a public service would most want assumed for them |
| **`SourceRecord.review` survives as the LEGACY accessor, fenced** | Engineering Principles | It keeps every document, validator and rendered catalog written before ADR-027 true. It is not an authorization input, and an AST test asserts the three gate modules never read it -- because `.review` reads more naturally than `.review_for(profile)`, which is precisely how the mistake would be made |
| **55 historical reviews migrated with nothing rewritten** | Engineering Principles | §8, §9, §29. All attached to the legacy profile, recorded as a MIGRATION INTERPRETATION of their scope rather than a new policy conclusion -- and not a guess: the catalog's own prose has said it since Mission 1.0. The verdict distribution is asserted unchanged at 5 / 13 / 8 / 3. Review row ids keep the historical derivation for the legacy profile, because rows hang off them -- conditions, and the condition VERIFICATIONS that record who checked what and when |
| **TED holds two current verdicts at once** | Product Shape | §20, §46, §47. `REQUIRES_REVIEW` under the commercial profile and `APPROVED_WITH_CONDITIONS` under the local one, both true. The local review rests on the same Decision granting the six load-bearing activities, the operator's own published intended-use documentation for its two query routes, and the structural fact that the Article 7(2)(b) re-utilisation limb is not engaged by a use that redistributes nothing |
| **H-36 was NOT resolved, and the review says so** | Blocked work | §21, §23. H-36A stays NOT ESTABLISHED and H-36B stays NOT ADDRESSED under BOTH profiles. A profile changes the exposure and the acts performed; it does not change the law. Bulk XML and the ted-csv subset are excluded by name under every profile, so profile support did not become a loophole (§24) |
| **Approving is still not eligible, and it names why** | Blocked work | §48. `build_authorization` for TED under the local profile refuses with three outstanding HUMAN_CONFIRMATION conditions, one of them a named operator's acceptance of the residual database-right exposure. No verifier can satisfy them, by design: a residual-risk acceptance that code could satisfy would be a judgement nobody made. The machine-checkable condition, attribution, is SATISFIED |
| **Nothing was collected, built or scored** | Forbidden During Foundation | §41-§43, §51. No collector, no API client, no SPARQL client, no TED module anywhere -- asserted against the file tree. RawRecords 12, NormalizedRecords 12, Signals 7, Claims 7, ClaimRevisions 7, Evidence 7 unchanged. Reliability 0, Opportunities 0, embeddings 0, scores 0, TED rows 0 |

## 1.28 — 2026-08-31 (deployment model)

Authorized by the operator directly, as standing guidance for all future
missions rather than by a mission brief.

| Change | Section | Authority |
|--------|---------|-----------|
| **The deployment model is recorded: LOCAL-FIRST / SINGLE-OPERATOR** | Canonical invariants | Operator directive, 2026-08-31. The application runs locally for its developer/operator and is not intended to be offered as a public multi-tenant SaaS. Placed FIRST among the canonical invariants because it frames the ones that depend on it: it decides what every source review's assessed use case is about, and it is why the tenancy rule survives having one operator |
| **Local deployment does NOT imply NON_COMMERCIAL_USE** | Canonical invariants | The load-bearing half, and the one most easily taken backwards. The research this system produces is used to discover, evaluate and launch **commercial** SaaS and web products, so the deployment is local and the purpose is commercial -- two independent facts. Taking it backwards would produce exactly the narrowed assessed use case §Source governance forbids. **Commercial-use rights are still reviewed wherever they apply** |
| **Public redistribution and customer-facing rights are out of scope** | Canonical invariants | Unless the deployment model changes. A source review that grants them is not wrong; a review that DEPENDS on them is out of scope. If the deployment ever becomes public, customer-facing, sold, subscription-based or multi-tenant, the commercial profile must be reviewed again from the top -- it is unreviewed today and must not be reached by drift |
| **Workspace and row-level security are preserved** | Canonical invariants | Being a single operator today is not a concrete reason to remove a tenant boundary, and re-adding one later is far more expensive than keeping it. A pointer was added to §Tenancy, where the question is most likely to be raised |
| **No billing, customer accounts, team collaboration or cloud scaling** | Forbidden During Foundation | Unless a mission explicitly requires it. Application UX and deployment are optimised for one local operator |
| **The LOCAL_PRIVATE_RESEARCH profile is local, not non-commercial** | Blocked work | Mission 1.15.4 defined it in `route-scoped-source-authorization-gap-v1.md` and could not authorise it, because every approval in the registry answers a use case the model does not record. It must not be renamed or read as a non-commercial profile when `assessed_use_profile` is built. Nothing in the TED reviews rests on non-commercial status: `commercial_use` is PERMITTED there on its own evidence, from v1 |

No code, no schema, no registry state. Documentation only.

## 1.27 — 2026-08-31 (Sprint 1 / Mission 1.15.4)

Authorized by the Mission 1.15.4 brief §1-§2 (the changed real-world use case),
§4-§6 (first-party route research), §25-§26 (source review architecture and the
critical question), §32 (fake response guard), §35 (documentation) and §39 (stop
after the report).

| Change | Section | Authority |
|--------|---------|-----------|
| **A user summary was excluded before any policy reasoning** | Engineering Principles | Mission 1.15.4 §32. A file describing a written Publications Office reply exists outside the repository and is a transcription that says so in its own second paragraph. Classified USER_SUPPLIED / NON_AUTHORITATIVE: not cited, not copied in, not entered as evidence, **not deleted**. A test asserts that **no source in the catalog** carries an `OPERATOR_CORRESPONDENCE` evidence row at any version -- a tripwire rather than a validator, because a test that tried to VALIDATE an operator response would be a specification for forging one (`testing-strategy.md` §40) |
| **Local private use creates no permission** | Engineering Principles | Mission 1.15.4 §1, §27. The use case got smaller and the source stayed blocked. The review names and refuses each forbidden conclusion verbatim -- "TED has no database rights", "local projects do not need permission", "because the API is public, all reuse is allowed", "because TED wants reuse, H-36 is irrelevant" -- because every one of them is reachable from the evidence gathered and every one is wrong |
| **The official routes' intended purpose is documented, first-party** | Product Shape | Mission 1.15.4 §5, §6. The Search API "allows access to published procurement notices for analysis and reuse", is "primarily targeted at data reusers", requires no authentication, and names "Commercial Organisations: Integrating TED data into platforms to provide added-value services" and "Researchers: Analysing public procurement trends and patterns" among its users. The TED Open Data Service publishes data "for analysis and re-use", invites use "in your research and applications", and offers a **Connect your app** button to "retrieve live results directly into Excel, Power BI, or any application that can get data from the web". Analysis, reuse, application integration, commercial use, repeated access and automated access are each named by the operator about its own route |
| **Documented purpose is NOT a database-right grant** | Blocked work | Mission 1.15.4 §13, §9. Condition 11 records the distinction. Nothing on either route mentions the sui generis right, and an operator describing what its service is for is not a right holder licensing a right in a collection. The Search API is nowhere framed as a way around H-36: the argument rests on documented purpose, never on the route transferring smaller chunks. The Open Data Service's own invitation to "extract custom datasets across many notices" uses the Directive's verb, is recorded, and closes nothing |
| **Minimisation is possible AT acquisition, and coverage is bounded** | Engineering Principles | Mission 1.15.4 §14. The Search API request body carries a `fields` parameter, so "collect first, minimise later" is not available as an excuse on this route. Coverage is recent and partial: eForms from 1 March 2023 to current day minus one; Standard Forms only 28 August 2023 to 26 January 2024, a documented "proof of concept" slice of form types F3, F6, F21, F22, F23, F25. Recorded so a collector does not discover it from an empty result set |
| **THE BLOCKER MOVED, and it is ours: every approval answers a use case the model never records** | Blocked work | Mission 1.15.4 §25, §26. `build_authorization('ted-eu')` returns exactly one reason, "policy review is REQUIRES_REVIEW", and no route, resource or profile argument exists that could change it; searching the contracts and acquisition packages for `use_profile`, `deployment_profile`, `LOCAL_PRIVATE` or `MULTI_TENANT` returns **zero matches**. The finding is not about TED. Twenty-nine sources carry approval states that answer an unrecorded question, which cost nothing while one product was being assessed. TED is the first source whose product has two shapes at once, and the model has one slot |
| **The three ways to hack it are each worse than the gap** | Engineering Principles | Mission 1.15.4 §26. Flipping the verdict makes the eligibility view, the validators, the portfolio and the coverage tables all report TED approving for the commercial multi-tenant use case that is still unresolved -- the silent migration §8 exists to prevent, with conditions as prose next to a boolean that says otherwise. Two current reviews means two answers to one question. A use-profile condition still needs the flip to get past the gate, and inherits its failure whole |
| **The minimal extension is proposed, not built** | Blocked work | Mission 1.15.4 §26, §35. Record `assessed_use_profile` on a review (every existing one is COMMERCIAL_MULTI_TENANT, which is what they DID assess -- labelling, not a new claim); allow one current review per profile; thread the profile through `evaluate_eligibility` and `build_authorization`; have the runtime DECLARE its profile from configuration rather than infer it, so a profile the review does not name is refused. It touches the most safety-critical function in the repository and needs an ADR and a mission of its own |
| **Review v5 records the routes and moves nothing else** | Engineering Principles | Mission 1.15.4 §10, §12. Every activity assessment is byte-identical between v4 and v5; the verdict stays REQUIRES_REVIEW; all ten v4 conditions are carried forward verbatim and an eleventh is added. H-34 stays CLOSED PERMITTED and was not reopened. Bulk XML stays blocked -- public downloadability alone is insufficient and nothing found here speaks to repeated substantial extraction. `ted-csv` stays a separate review |
| **Nothing was collected, built, claimed or scored** | Forbidden During Foundation | Mission 1.15.4 §26-§31, §39. No collector, no API client, no SPARQL client -- asserted against the file tree and against `SPARQLWrapper` anywhere in the repository. No compliance configuration for a blocked source. RawRecords 12, NormalizedRecords 12, Signals 7, Claims 7, ClaimRevisions 7, Evidence 7 unchanged. Reliability assessments 0, Opportunities 0, embeddings 0, scores 0, TED rows 0. Verdict distribution unchanged: 5 / 13 / 8 / 3 |

## 1.26 — 2026-08-31 (Sprint 1 / Mission 1.15.3)

Authorized by the Mission 1.15.3 brief §2 (resolve or externalise H-36), §3
(exhaust first-party evidence), §5-§8 (dataset licence and rights metadata),
§10 (H-36A / H-36B), §18-§22 (clarification and legal packet), §38
(documentation) and §40 (stop after the report).

| Change | Section | Authority |
|--------|---------|-----------|
| **The dataset-level licence exists, and it is the Decision** | Product Shape | Mission 1.15.3 §5, §8. The Publications Office's own DCAT-AP record for `ted-1` on data.europa.eu declares `dct:license = COM_REUSE` on **every** distribution, including *"Last daily editions of procurement notices in bulk download"*. The `COM_REUSE` authority concept carries `skos:exactMatch` to `http://data.europa.eu/eli/dec/2011/833/oj`. So the machine-readable licence on the bulk route resolves, **by the publisher's own assertion**, to the instrument Mission 1.15.2 read in full and found silent. The dataset node itself carries no licence, no `dct:rights` and **no `dct:creator`** |
| **Both access routes are governed by the same silence** | Product Shape | Mission 1.15.3 §13, §14. The TED Search API's OpenAPI document contains a "Terms of Usage" section whose entire content is a link to the TED legal notice. Bulk XML and the API are therefore governed by the same instrument, and the enclosing chain -- TED notice, Publications Office notice, europa.eu notice, the 20,015-character data.europa.eu notice, the bulk page, the package HTTP headers, the API specification -- contains **zero** occurrences of *sui generis*, *database right*, *extraction*, *re-utilisation* or Directive 96/9/EC |
| **`appliesTo licence-domain/DATA` is not a database-right grant** | Engineering Principles | Mission 1.15.3 §8. The tempting over-read, refused on the vocabulary's own text: `DATA` is defined in the same authority table as a *"set of values of qualitative or quantitative variables"* -- a subject class, not a class of right. The whole `licence-domain` scheme is `CODE`, `DATA`, `METADATA`, `W_LIT_ART` and a placeholder, so **there is no `DATABASE` domain** and the absence is not a deliberate choice either. `CC_BY_4_0` carries the identical two values |
| **H-36 split into H-36A and H-36B** | Blocked work | Mission 1.15.3 §10. **H-36A -- does the right subsist? NOT ESTABLISHED either way**: Directive 96/9/EC Article 7(1) gives it to a MAKER showing SUBSTANTIAL INVESTMENT, and nothing retrieved names one; the catalogue names a *publisher*, notices are filed by contracting authorities across the Union, and Article 11 makes subsistence turn on facts about that maker. **H-36B -- is it granted? NOT ADDRESSED for both routes**: Article 7(3) confirms the right can be granted by contractual licence, and `COM_REUSE` does not |
| **CC BY 4.0 was found on TED-derived data, recorded in full, and not relied on** | Engineering Principles | Mission 1.15.3 §7, §15. The same portal declares CC BY 4.0 -- whose Section 4 expressly grants the right *"to extract, reuse, reproduce, and Share all or a substantial portion of the contents of the database"* -- on **12 of 48** distributions of the separate `ted-csv` dataset published by DG GROW, including award notices for 2020-2022. Not relied on for two reasons that both matter: it is a different dataset under a different publisher, and the assignment **overlaps** its own COM_REUSE files (`ted-contract-award-notices-2017-2021.zip` is CC BY 4.0, `ted-contract-award-notices-2018-2023.zip` is COM_REUSE). Selecting the favourable licence would be **selecting a licence by selecting a filename**. Condition 10 forbids carrying a licence across resources |
| **Mission 1.15.2's bulk-versus-API reasoning corrected** | Engineering Principles | Mission 1.15.3 §14. That review judged the search API "less obviously a substantial part … and correspondingly less exposed". The API's own specification documents a **scroll mode with no limit on the number of retrievable notices**, and Article 7(5) reaches repeated and systematic extraction of insubstantial parts regardless. Both routes stay unresolved, the gap is smaller than recorded, and **no route was preferred** |
| **No PSI or open-data chain exists** | Engineering Principles | Mission 1.15.3 §12. Directive (EU) 2019/1024 appears nowhere in any TED or Publications Office material. The single occurrence of Directive 2003/98/EC is inside the data.europa.eu **privacy** statement, cited as a legal basis for processing personal data in operating the portal -- not as a reuse-rights chain for TED content. Recorded as separate legal context, never as controlling evidence |
| **The blocker became a drafted, unsent message** | Blocked work | Mission 1.15.3 §17-§21, Outcome C. `ted-eu-database-right-clarification-request-v1.md` addresses `op-copyright@publications.europa.eu`, the route TED's own legal notice publishes for SIMAP copyright issues, with `GROW-D2@ec.europa.eu` for the CSV question. **Nothing was sent, and nothing claims to have been**: there is no `sent_at` anywhere and a test asserts it. `ted-eu-h36-legal-review-packet-v1.md` holds the established facts and five questions with **no legal conclusion**, and records the unfavourable outcome in advance so it reads as a question rather than as advocacy |
| **A structural guard must not match its own source** | Engineering Principles | Mission 1.15.3. The no-network assertion was first written as a substring scan and **failed on its own list of forbidden substrings** -- the third time this pattern has appeared, after the normalization guard and Mission 1.13's vocabulary guard. Rewritten over the AST, which cannot match its own literals and also catches `import httpx as h`. Separately, a documentation assertion failed because Markdown wraps at 80 columns and split the phrase it looked for; all document assertions now go through one whitespace-normalising helper (`testing-strategy.md` §38, §39) |
| **Nothing was collected, built, claimed or scored** | Forbidden During Foundation | Mission 1.15.3 §27-§32, §40. No collector, no normalizer, no TED module anywhere in the acquisition package -- asserted against the file tree as well as the registry. HEAD requests read package headers (16.7 MB daily, 427 MB monthly) and **no package body was downloaded**; whether a licence travels inside the archives is recorded as unestablished rather than worked around. RawRecords 12, NormalizedRecords 12, Signals 7, Claims 7, ClaimRevisions 7, Evidence 7 unchanged. Reliability assessments 0, Opportunities 0, embeddings 0, scores 0. Verdict distribution unchanged: 5 / 13 / 8 / 3. USAspending was not re-reviewed |

## 1.25 — 2026-08-31 (Sprint 1 / Mission 1.15.2)

Authorized by the Mission 1.15.2 brief §2 (resolve H-34 and H-36), §3 (retrieval
is the mission), §7 (resolve the definition of reuse), §15 (database rights are
mandatory), §24 (verdict rules), §44 (documentation) and §46 (stop after the
report).

| Change | Section | Authority |
|--------|---------|-----------|
| **The governing Decision was retrieved and read in full** | Product Shape | Mission 1.15.2 §3, §5. EUR-Lex failed again -- six representations across two missions. The text came from the **Publications Office's own Cellar repository**, addressed by the Cellar identifier the Publications Office publication record itself publishes: four pages, Articles 1-13, 16,748 characters. A first-party representation reached by following the publisher's own identifiers, not a mirror |
| **H-34 CLOSED PERMITTED: reuse is defined by PURPOSE, not by METHOD** | Product Shape | Mission 1.15.2 §7, §12. Article 3(2): reuse "means the use of documents by persons or legal entities of documents, for commercial or non-commercial purposes other than the initial purpose for which the documents were produced". The definition enumerates no acts. Article 4 makes all in-scope documents available on that footing; Article 6(2)'s permitted conditions -- attribution, non-distortion, non-liability -- contain nothing about method; the Article 2(2) exclusions are classes of DOCUMENT; and the only manner-of-use prohibition in the instrument is Article 2(4)'s reuse "calculated to deceive or to defraud". **This is not silence about machine learning** -- it is a grant whose operative term is broad enough that method does not enter |
| **The permission is scoped, and training is not authorised** | Forbidden During Foundation | Mission 1.15.2 §13, §14. Inference, extraction, classification and structured analysis are within the grant. Model training was NOT assessed: the Decision does not distinguish methods, but training raises Article 2(2)(b)'s third-party-rights exclusion in a materially different form and the engine does not need it. Embeddings stay unassessed for implementation and blocked by D-12. Both recorded as a CONDITION, because a single PERMITTED field cannot carry a boundary |
| **Article 6(2)(b) makes non-distortion a legal obligation** | Engineering Principles | Mission 1.15.2. The reuser is obliged "not to distort the original meaning or message of the documents" -- the condition with the most direct bearing on the claim layer. An OBSERVED restatement of an award notice must say what the notice says, which the interpretation contract already required epistemically and the Decision now requires legally |
| **H-36 did NOT close, and the unknown became an established absence** | Blocked work | Mission 1.15.2 §15, §23. The full text contains **zero** occurrences of "sui generis", "extraction", "re-utilisation" or Directive 96/9/EC; its two occurrences of "database" are an exclusion for unpublished research and an example inside the definition of structured data. The Decision is framed throughout around DOCUMENTS (Articles 1, 2(1), 3(1)); the collection they sit in is never mentioned. Article 2(2)(a) excludes industrial property by name and the database right is not in that list -- the instrument neither grants over it nor excludes it, it **does not reach it** |
| **Six granted activities and a blocked source, at once** | Blocked work | Mission 1.15.2 §24. Permitted plus unresolved gives REQUIRES_REVIEW. All six load-bearing activities are now positively granted and `ted-eu` is still blocked, which is uncomfortable and correct: **the remaining question is not an activity in the matrix**, it is whether a different body of rights sits over the same data. A favourable H-34 was not allowed to override an unresolved H-36 |
| **The blocker changed kind, and got more expensive** | Blocked work | Mission 1.15.2 §42. It was "retrieve a document". It is now "decide a legal question the documents do not answer" -- the first item in the human-review queue a further document search cannot settle, because the documents have been read. Bulk XML and the search API are analysed separately and both are unresolved with different exposure; **no collector route was forced** |
| **A review test must name the version it is testing** | Engineering Principles | Mission 1.15.2. Seven tests from Missions 1.15 and 1.15.1 failed when v3 landed, every one correct when written. A FINDING is asserted against its version and a DURABLE PROPERTY against the current review; pinning keeps the append-only history checked instead of relaxing the old assertions away (`testing-strategy.md` §37) |
| **Nothing was collected, built, claimed or scored** | Forbidden During Foundation | Mission 1.15.2 §34-§38, §46. No collector, no TED RawRecord or NormalizedRecord -- asserted live. RawRecords 12, NormalizedRecords 12, Signals 7, Claims 7, ClaimRevisions 7, Evidence 7 unchanged. Reliability assessments 0, Opportunities 0, embeddings 0, scores 0. Verdict distribution unchanged: 5 / 13 / 8 / 3. USAspending was not re-reviewed (§43) |

## 1.24 — 2026-08-31 (Sprint 1 / Mission 1.15.1)

Authorized by the Mission 1.15.1 brief §2 (resolve H-34 only), §5 (establish the
governing instrument), §16 (three valid outcomes), §35 (documentation) and §37
(stop after the report).

| Change | Section | Authority |
|--------|---------|-----------|
| **The governing instrument is named and the link is PROVEN** | Product Shape | Mission 1.15.1 §5. TED's own legal notice states that the Commission's reuse policy "is implemented by the Commission Decision of 12 December 2011 on the reuse of Commission documents" and links its ELI address. Mission 1.15's open question guessed at "the Publications Office's reuse decision, or another first-party instrument"; the instrument now has a name, a date, a publisher and a canonical URL. §5 required proving the link rather than assuming a generic EU open-data statement applies, and it is proven |
| **H-34 stays OPEN because the instrument could not be read** | Blocked work | Mission 1.15.1 §16, Outcome C. Five first-party EUR-Lex addresses -- the ELI URL, the ELI English URL, the CELEX text URL, the CELEX HTML URL and the Official Journal PDF -- each returned an empty body. The Publications Office copyright notice does not restate it and is silent on text and data mining, machine learning and automated processing; the TED Developer Docs link back to the same legal notice |
| **An unread document is a weaker basis than observed silence** | Engineering Principles | Mission 1.15.1 §3, §7. The grant reads "can be freely reused, for commercial or non-commercial purposes". The operative word is REUSED, and its scope is defined in the instrument that would not render. Reading it as covering machine-learning inference would mean assuming a definition from a document nobody has opened -- which is worse than inferring from silence, because silence is at least established |
| **A search-engine summary of the Decision was refused as evidence** | Engineering Principles | Mission 1.15.1 §4. A search restricted to EU domains returned a summary describing the Decision's articles, and it was the one thing in the mission that would have closed the question. No part of the review rests on it, and a test asserts every evidence URL is a first-party EU host |
| **A new question surfaced: does the grant reach the sui generis DATABASE right?** | Blocked work | Mission 1.15.1 §9, H-36. TED is a database and the documented route is bulk XML -- extraction and re-utilisation of substantial portions. The database right is independent of copyright and nothing retrieved addresses it. It bears on `automated_access` and `redistribution` rather than `model_processing`, so it could block TED **even if H-34 closes favourably**. Recorded as a new open question rather than used to downgrade Mission 1.15's findings: a question nobody has answered is not evidence that an earlier review was wrong |
| **Two conditions added, none weakened** | Engineering Principles | Mission 1.15.1 §11, §12, §13. The legal notice states that additional rights may need clearing where content depicts identifiable private individuals, and that industrial property including logos and names is excluded from the reuse policy. **The reuse grant is not a blanket grant over everything inside a notice**, which makes minimisation a compliance requirement rather than a preference. Mission 1.15's minimisation and authenticity conditions are intact and asserted by test |
| **Every activity assessment is byte-identical between v1 and v2** | Engineering Principles | Mission 1.15.1 §19. A re-review that could not close its question must not quietly move findings it did not re-establish. `v1.assessments == v2.assessments` is one assertion and it catches the whole class |
| **Nothing was collected, built, claimed or scored** | Forbidden During Foundation | Mission 1.15.1 §27-§32, §37. No collector, no TED RawRecord or NormalizedRecord -- asserted live against the database. RawRecords 12, NormalizedRecords 12, Signals 7, Claims 7, ClaimRevisions 7, Evidence 7 unchanged. Reliability assessments 0, Opportunities 0, embeddings 0, scores 0. Verdict distribution unchanged: 5 / 13 / 8 / 3 |

## 1.23 — 2026-08-31 (Sprint 1 / Mission 1.15)

Authorized by the Mission 1.15 brief §2 (find lawful demand-side sources), §4-§6
(priority candidates), §12 (the WTP gap), §21-§23 (coverage and priority), §42
(documentation) and §44 (stop after the report).

| Change | Section | Authority |
|--------|---------|-----------|
| **WILLINGNESS_TO_PAY gained its first lawful candidates, and neither is approved** | Product Shape | Mission 1.15 §12. `ted-eu` and `usaspending` record contract awards -- what a buyer paid a named supplier -- which is a TRANSACTION and not a LISTED_PRICE. WTP had **no registered candidate at all** before this round. Both are REQUIRES_REVIEW: a first candidate is not a first source |
| **`ted-eu` is the closest any blocked source has come, and one silence holds it** | Blocked work | Mission 1.15. One retrieved sentence grants five of the six load-bearing activities -- "the procurement notices ... can be freely reused, for commercial or non-commercial purposes" -- which is a GRANT rather than an absence of prohibition. `model_processing` is NOT_ADDRESSED and rule 8 blocks whatever the other five say. Recording it otherwise would be the narrowing of the assessed use Mission 1.8 forbids: this product includes LLM processing, and a permission for a smaller product is a permission for a product we are not building |
| **Two hopeful maybes became definite noes on retrieved evidence** | Engineering Principles | Mission 1.15 §5, §6, §7. Pinterest -- the catalog's best DESIRE hypothesis since Mission 1.7 -- prohibits storing API information at all ("call the API each time"), prohibits automated extraction and ML training, and requires explicit written authorization for competitor-research features, which names this product. Hacker News publishes an API stating "There is currently no rate limit" while Y Combinator's Terms prohibit "data mining, robots, scraping" and commercial derivative works. Both RESTRICTED |
| **Technical accessibility is still not permission, demonstrated three times** | Engineering Principles | Mission 1.15 §18. A keyless public API paired with a non-approving verdict for `hacker-news`, `bluesky` and `ted-eu`, each for a different reason: prohibited, silent, and granted-but-for-one-activity. Asserted by test rather than left to prose |
| **A failed retrieval changes nothing** | Engineering Principles | Mission 1.15 §18. Reddit and Stack Exchange were unreachable and gained **no review version in either direction**. No mirror, cached copy, alternative page or community summary was used to infer terms; no bot protection was encountered and no bypass attempted. A search result carrying substantive-looking Pinterest quotes was NOT treated as evidence until the document itself was fetched from a first-party host |
| **Bluesky's open question narrowed from four unknowns to one document** | Blocked work | Mission 1.15 §5. Its developer guidelines exist -- named by Bluesky's own documentation domain -- and returned an empty body. The user Terms, re-retrieved at the version effective 15 September 2025, remain silent on all ten activities. Review v2 records the same verdict and a materially better question (H-33) |
| **A source family for sources whose primary record is a purchase** | Product Shape | Mission 1.15, migration 0020. `public_procurement` rather than `economic_data`: World Bank and Eurostat publish statistics ABOUT economies, TED publishes individual transactions within one. Filing them together would have made the coverage report say the portfolio has had commercial evidence since Mission 1.5, which it has not |
| **No approving source observes an individual doing anything** | Blocked work | Mission 1.15 §21, `demand-side-source-coverage-v1.md`. Six of eight business families have no approving source and two -- Pricing and Retention -- have no registered candidate at all. The two families that do have one have a weak one: `openalex` for distribution is scholarly-record discovery, `gdelt` for user behaviour is news-corpus activity. Retention's obstacle is structural rather than legal: it needs the same subject observed twice, and everything in the portfolio is an aggregate or a one-shot public record. **No proxy is proposed**, because a proxy nobody can validate is worse than an acknowledged gap |
| **Nothing was collected and nothing became eligible** | Forbidden During Foundation | Mission 1.15 §31, §32. No collector, no RawRecords, no NormalizedRecords, no Signals. RawRecords 12, NormalizedRecords 12, Signals 7, Claims 7, Evidence 7 unchanged. Reliability assessments 0, Opportunities 0, embeddings 0, scores 0. A correct review concluding that candidates remain blocked is worth more than a false approval |

## 1.22 — 2026-08-31 (Sprint 1 / Mission 1.14)

Authorized by the Mission 1.14 brief §2 (define what reliability means), §5-§6
(find the smallest valid reusable scope), §31-§32 (gap analysis then contract),
§48 (documentation) and §50 (stop after the report).

| Change | Section | Authority |
|--------|---------|-----------|
| **Reliability is assessed per MEASUREMENT x PURPOSE, never per source** | Engineering Principles | Mission 1.14 §3, §5, [ADR-026](docs/architecture/adr/ADR-026-reliability-assessment-scope-and-binding.md). A five-part scope — source, resource, record kind, claim type, proposition kind — matched in full or not at all. `world-bank` alone matches nothing, so the framework's own example resolves with no special case: a population record used for a demand proposition has a different proposition kind and matches nothing. **The purpose-relativity is structural, not documented** |
| **The purpose vocabulary already existed** | Product Shape | Mission 1.14 §5. `proposition_kind` is the `proposition_facts` discriminator Mission 1.13.1 added so two proposition shapes could not collide in a hash. It names what a claim asserts IN KIND, which is exactly what "purpose" means in "reliability is purpose-relative". **Seven Evidence rows collapse to three scopes**, and stay three however many observations arrive — the ratio that justifies the design |
| **Compliance is not reliability, enforced rather than stated** | Engineering Principles | Mission 1.14 §4. An APPROVED source does not produce better evidence and a RESTRICTED one does not produce worse. A separate `epistemic` schema with no policy column, and an AST test over string literals that excludes docstrings so the paragraph explaining the rule cannot fail it |
| **A value rests on retrieved first-party documents, and states what bounds it** | Engineering Principles | Mission 1.14 §7, §24. "The publisher is reputable" is a sentence, not a basis: `REVIEWER_DOCUMENTED_JUDGEMENT` is permitted alongside documents and refused alone, by a deferred trigger. `stated_limitation` is required — a reliability with no stated failure mode is a number nobody can argue with. Full documents are never stored, the same 1000-character discipline `registry.source_policy_evidence` uses |
| **There is no MODEL_GUESSED origin, and closure is the point** | Forbidden During Foundation | Mission 1.14 §8, §43. Three origins: HUMAN_REVIEW, DOCUMENTED_METHOD, CALIBRATED_EMPIRICALLY. A model may help a reviewer read documentation and may not be the epistemic source, and a vocabulary with nowhere to record a guess is what makes that enforceable rather than merely stated |
| **Unknown is the absence of a row, never a value** | Engineering Principles | Mission 1.14 §10. `0.5 because unknown`, `0.8 because reputable`, `1.0 because official` and `0.0 because we do not know` are all measurements, and `q_i = min(components)` must never see one nobody made. **The system stays capable of producing no score**, which is what makes a score mean something when one appears |
| **Zero, one and many are all defined, and many is refused** | Engineering Principles | Mission 1.14 §18. Never the closest — "closest" needs a distance nobody defined. Never the maximum — optimism with a mechanism. Never the mean — averaging two competing reviewed judgements produces a third nobody made. A partial unique index makes the many-case unreachable and the resolver refuses anyway, because a guard that trusts another guard is one schema change away from trusting nothing |
| **Resolved late, bound explicitly** | Product Shape | Mission 1.14 §19, §20, ADR-026 Decision 2. Copying the value forward loses where it came from; binding to "latest" rewrites yesterday's score silently. A result records which assessment id and version produced each number, so re-running against current assessments is identifiable AS a recomputation. Does not resolve D-08; refuses to make it harder |
| **Outcome B: no assessment was written, and all seven rows stay NON_SCORABLE** | Blocked work | Mission 1.14 §23, §43. §8 says a model may not be the epistemic source of an assessment and §43 says reliability cannot come from "Claude thinks World Bank is reliable" — so writing one here would have meant fabricating a reviewer, which is worse than producing no score. The report names the three scopes a reviewer would need and what documents each requires. **Aggregation returns UNAVAILABLE, uncertainty mass 1.0, and that is success** |
| **D-03 lost one blocker and kept four** | Blocked work | Mission 1.14 §21. Resolved: the definition of reliability and who may set one. Still open: no reviewed value for any scope in use, no CALIBRATED profile, no authorised half-life, and level thresholds that are structural minimums rather than fitted values. Reliability governance is not calibration and does not become it by being careful |

## 1.21 — 2026-08-31 (Sprint 1 / Mission 1.13.1)

Authorized by the Mission 1.13.1 brief §2 (implement the pipeline), §3 (one
interpreter family), §21-§22 (run log and GAP-5), §31 (interpret the seven real
Signals), §44 (orchestration), §47 (documentation) and §50 (stop after the
report).

| Change | Section | Authority |
|--------|---------|-----------|
| **The first complete Signal → Claim → Evidence pipeline exists, and it produced real Claims** | Product Shape | Mission 1.13.1 §2, §31. `observed-signal-restatement@1.0.0` interpreted all **seven** real Signals into **7 OBSERVED Claims, 7 revisions and 7 Evidence rows** — 4 World Bank, 2 GDELT frequency-change, 1 GDELT contrast. Every statement names its source and says "reported that"; none asserts demand, interest, attention or a market |
| **The interpreter is structurally OBSERVED, not defaulted** | Engineering Principles | Mission 1.13.1 §5. `_CLAIM_TYPE` is a module constant, `interpret()` takes no claim-type parameter, and `validate_claims.py` fails the build on any `ClaimType.X` attribute access in the package where X is not OBSERVED — over the **AST**. A Signal type with no template is `UNSUPPORTED_SIGNAL_TYPE`; there is no generic prose path, because a sentence nobody specified is a proposition nobody reviewed |
| **Attribution is what makes it OBSERVED** | Engineering Principles | Mission 1.13.1 §9. "Germany's population increased" is not OBSERVED from a World Bank record; "World Bank Open Data reported that…" is, and they have different falsifiers. The geography is the SOURCE's own name, never our canonical code. Three attribution facts come from the contributing normalized records because the Signal's scope does not carry them, and disagreement between them is refused rather than resolved |
| **H-29 and H-30 are enforced in the wording, and in the AST** | Blocked work | Mission 1.13.1 §25, §26. GDELT claims say "source bucket" and "the preceding source bucket", never a clock or a date; `observed_at` is written NULL. They say "under source language label ENGLISH", never "in English", and `canonical_tag` is never read. Both asserted by `validate_claims.py` over call arguments and timezone-call names, and probed against deliberate violations. **H-29 and H-30 remain open** |
| **A guard whose subject is arbitrary text needs an exemption** | Engineering Principles | Mission 1.13.1 §10. The vocabulary guard became TOKEN matching over the interpreter's own prose, with **quoted source data exempt**: a GDELT term is arbitrary text, and `market`, `demand` and `pain` are ordinary English words a news corpus contains. Refusing `the term "demand" appeared 12 more times` would refuse the most faithful restatement available — the exact thing the guard protects. The template is the primary protection; no template contains the word |
| **Identity excludes the magnitude, so a revised source figure appends a revision** | Product Shape | Mission 1.13.1 §11, §12, §29. The proposition key is over the facts, so 187,180 becoming 187,200 is the SAME proposition worded differently and revision 2 is appended. Revision 1 is never modified. For a contrast, where `direction` is NOT_APPLICABLE, the relation comes from the SIGN of the magnitude and IS part of identity while the value is not. `proposition_facts` stores the preimage: a hash nobody can verify is an identity nobody can dispute (ADR-025) |
| **A refused interpretation gets a run record, never a Claim; GAP-5 is resolved** | Product Shape | Mission 1.13.1 §21, §22, [ADR-025](docs/architecture/adr/ADR-025-claim-interpretation-run-and-considered-inputs.md). `research.claim_interpretation_runs` holds one row per EXECUTION, written in the claims' transaction. `research.claim_interpretation_inputs` records every Signal a run CONSIDERED with its role — CITED, EXCLUDED, REFUSED — and why: "three of forty considered were supporting" is a different fact from "three supporting Signals exist". EXCLUDED (never attempted) and REFUSED (attempted and rejected) stay apart |
| **Reliability was not invented, and the consequence was reported** | Blocked work | Mission 1.13.1 §17, §30. Reliability is purpose-relative and D-03 is blocked, so it is written NULL. Every one of the seven Evidence rows is therefore `NON_SCORABLE` with `MISSING_RELIABILITY`, aggregation returns `UNAVAILABLE` and no score was persisted. That is the honest answer; filling it in to make a number appear is the failure the framework's §6 exists to prevent |
| **A validator was probed before being believed** | Engineering Principles | Mission 1.13.1. `validate_claims.py` printed eleven `ok` lines on its first run, which is what a validator that checks nothing also prints. A probe applied **11 deliberate violations** — one per rule — to the real files and all eleven were caught. The probe found its own infinite loop first: it walked up from `__file__` looking for `.git` from outside the repository |
| **Existing data is untouched and the additions are additive** | Forbidden During Foundation | Mission 1.13.1 §38, §41, §43. RawRecords 12, NormalizedRecords 12, Signals 7 and signal_inputs 14, all **byte-for-byte unchanged** under a content digest taken before and after. Opportunities 0, embeddings 0, scores 0. No LLM, no network, no embedder — asserted over every import in the layer |

## 1.20 — 2026-08-31 (Sprint 1 / Mission 1.13)

Authorized by the Mission 1.13 brief §4 (decide whether a new entity is needed),
§41 (gap analysis before migration), §42 and §55 (documentation), §53 (synthetic
tests), §56 (report) and §57 (stop after the report).

| Change | Section | Authority |
|--------|---------|-----------|
| **A Claim may precede its Opportunity** | Product Shape | Mission 1.13 §17, [ADR-024](docs/architecture/adr/ADR-024-claim-precedes-opportunity.md), Ontology V2.2 §17.3. The schema said `claims.opportunity_id NOT NULL` while the pipeline runs Signal → Claim → Opportunity, which made the intended pipeline **unrepresentable**: a Claim about a source fact exists before anybody has conceived of the product it might justify. Migration 0016 drops the constraint; a Claim now belongs to **at most one** Opportunity, and may belong to none |
| **A machine may not store an assertion nothing supports** | Engineering Principles | Mission 1.13 §22, ADR-024. Enforced twice — a `DEFERRABLE INITIALLY DEFERRED` constraint trigger (migration 0016) and `NO_SUPPORTING_SIGNAL` in `build_claim`. Three exemptions, each reasoned: `HYPOTHESIS` **by definition** (requiring evidence would make the category unusable, pushing unsupported ideas into `INFERRED` — the exact failure), `MANUAL` because a person asserting and then looking is the ordinary research motion, `WITHDRAWN` because a withdrawn claim's evidence may be gone |
| **The interpretation step got no new entity** | Product Shape | Mission 1.13 §4. A `ClaimCandidate` table would be a second place an assertion can live, and an assertion outside `research.claims` escapes every rule in the contract — including the evidence requirement. The step produces an unpersisted `ClaimDraft`, written as claim + revision + evidence in one transaction or not at all |
| **A model is a reasoning mechanism, never the evidence** | Engineering Principles | Mission 1.13 §20. A `MODEL_DERIVED` claim citing no Signal is refused exactly as a deterministic one is; the model's contribution is provenance, never a row in `scoring.evidence`. `DETERMINISTIC` **forbids** a model version, because that word promises the claim can be regenerated. No chain-of-thought is stored and there is nowhere to put one |
| **Identity is the proposition, and never a vector** | Engineering Principles | Mission 1.13 §17, §39. `proposition_key` is sha256 over the canonical facts asserted, unique per workspace: two interpreters wording one fact differently produced **one** claim. Not the prose, not the research session, and **not an embedding** — D-12 stays open, and two claims whose prose differs by "DE"/"FR" are different claims no distance threshold reliably separates |
| **GDELT lexical frequency alone never satisfies a demand claim** | Engineering Principles | Mission 1.13 §46. Not weakly, not with low relevance, not with a caveat. News coverage is journalists publishing; demand is people wanting and paying — a low relevance score models it as *a little bit of the right thing*, and it is none of the right thing. `UNSUPPORTED_INTERPRETATION` refuses market vocabulary in an `OBSERVED` claim |
| **A CHECK that evaluates to NULL is not a CHECK** | Engineering Principles | Mission 1.13. Migration 0016's `claims_interpreter_complete_check` spelled "all three or none" as `(all NULL) OR (all non-blank)`, which returns **NULL** on a half-filled row — and a CHECK accepts NULL. Half an interpreter identity was written without complaint. Found by a probe written to disbelieve it, fixed forward by migration 0017 with `num_nonnulls(...) IN (0, 3)` |
| **Nothing was interpreted, and nothing moved** | Forbidden During Foundation | Mission 1.13 §51. **Claims 0, Evidence 0, Opportunities 0.** RawRecords 12, NormalizedRecords 12, Signals 7, all byte-for-byte unchanged. No embeddings, no scoring, no LLM call, and `packages/claim-model` reaches no network, no model, no embedder and no database |

## 1.19 — 2026-08-30 (Sprint 1 / Mission 1.12.1)

Authorized by the Mission 1.12.1 brief §3 (register one type), §10 (decide gap
semantics), §34-§35 (optional bounded controlled acquisition), §47
(documentation) and §49 (stop after the report).

| Change | Section | Authority |
|--------|---------|-----------|
| **The first source-relative temporal extractor exists, and it produced real signals** | Product Shape | Mission 1.12.1 §2, §34. `lexical-frequency-change@1.0.0` is the third extractor and the first whose window basis is `ORDERED_PERIODS`. One bounded controlled acquisition — 2 files against a reviewed ceiling of 8, 370,468 rows scanned, 4 matched — produced **two real signals** (`climate` 48→59, `weather` 33→42) **and two real gap refusals** in the same run |
| **A gap is never bridged** | Engineering Principles | Mission 1.12.1 §10, [ADR-023](docs/architecture/adr/ADR-023-source-bucket-adjacency.md). A pair derives only when its labels are **exactly one published bucket apart**; anything else is `NON_CONTIGUOUS_SOURCE_BUCKETS`, a value no existing reason could express. The step is computed in **label space** — components advanced and formatted back into a label — so nothing becomes an instant, and the arithmetic is licensed by the Mission 1.12 certification rather than by the format |
| **An absent term is absent, never a zero** | Engineering Principles | Mission 1.12.1 §11, ADR-023. A term with no observation in a bucket did not occur zero times there; GDELT publishing `0` is a measurement and silence is not. Zero-filling is the most natural thing to do to sparse lexical data and is wrong in a way nothing downstream can detect — a signal saying a term fell by 55 would be indistinguishable from a real collapse in coverage |
| **Order is asked for, never inferred** | Engineering Principles | Mission 1.12.1 §7. The extractor calls the Mission 1.12 certification for its source AND its resource AND checks the label scheme before comparing anything. `web-ngrams/chargram` sits in the same directory with the same label shape and is refused. A new AST gate fails the build if any extractor calls `astimezone`, `now`, `utcnow`, `localtime` or passes `tzinfo=` |
| **H-29 is untouched, and the model enforces it** | Blocked work | Mission 1.12.1 §8. `ORDERED_PERIODS` carries **no window bounds**, `observed_at` stays `NULL` — a database CHECK refuses otherwise — and no cross-source comparison is possible. H-29 and H-30 both remain open |
| **A CHECK caught the model rather than the code** | Engineering Principles | Mission 1.12.1. Migration 0013's `groups_derived + groups_refused <= groups_considered` encoded an assumption the third extractor falsified: a group pairing within itself derives one pair and refuses another. The counters were right and the constraint was wrong, and migration 0015 replaces it forward. Second time this table's arithmetic has caught a real modelling error |

## 1.18 — 2026-08-30 (Sprint 1 / Mission 1.12)

Authorized by the Mission 1.12 brief §2 (four questions kept apart), §3
(first-party sources only), §10 (populate the certification if H-32 closes), §21
(documentation) and §24 (stop after the report).

| Change | Section | Authority |
|--------|---------|-----------|
| **H-32 is CLOSED: the WEB-NGRAM stream is ordered** | Blocked work | Mission 1.12 §5, §6, [ADR-022](docs/architecture/adr/ADR-022-web-ngram-source-relative-order.md). Three first-party artifacts: GDELT's own BigQuery analysis over `gdelt-bq.gdeltv2.web_1grams` reads `SUBSTR(DATE,0,8)` as a calendar day and `ORDER BY DATE ASC` to chart a nine-month series; `MASTERFILELIST.TXT` is published in ascending label order at **15-minute** resolution across 7.6 years; `LASTUPDATE.TXT` names the maximal label as the newest publication. Mission 1.11 refused the same conclusion on an *inference about the mechanism* and was right to — what changed is the evidence, not the standard |
| **H-29 is still OPEN, and now for a sharper reason** | Blocked work | Mission 1.12 §8. GDELT **does** document UTC — for **Web News NGrams 3.0** (`gdeltv3/webngrams/`, table `webngrams`), whose `date` means "the JSON timestamp when the article was seen". Ours (`gdeltv3/web/ngrams/`, table `web_1grams`) is the **15-minute bucket the counts aggregate**: different path, table, format, cadence and meaning. A timing observation against the CDN's `last-modified` header was available and **refused** — it measures a storage object against this machine's clock, from one sample |
| **A certification is scoped to a publication STREAM, never a label shape** | Engineering Principles | Mission 1.12 §10, §11. `ORDER_ESTABLISHED_WITHOUT_TIMEZONE` holds one `TemporalOrderCertification` naming its source, its **resources exactly**, its label scheme, its review version, its basis and its scope; the constructor refuses one with no basis or no resources. `ObservationInput` gained `resource_id` because `source_id` alone could not express the scope — and the same directory publishes an unreviewed `chargram` file that a prefix match on `web-ngrams/` would have covered silently |
| **H-31 answered, and refined into the two questions it was** | Blocked work | Mission 1.12 §9. **Semantic coverage** is 2019-01-01, documented since the announcement; **current directory extent** begins at `20190101000000`, read bounded from `MASTERFILELIST.TXT`. The second is an observation and not a retention guarantee: GDELT commits to none, so no backfill window may still be assumed |
| **Nothing was derived, and nothing moved** | Forbidden During Foundation | Mission 1.12 §15, §16, §17, §24. No extractor was written, no production Signal created, and all five stored signal identities were **recomputed** from their stored lineage and reproduce byte-for-byte. The two GDELT normalized records keep `timezone_state = NOT_ESTABLISHED` and `observed_at = NULL`; the one real lexical signal stays `SAME_PERIOD_LABEL` / `NOT_APPLICABLE`. **Temporally permitted is not extractor specified** |

## 1.17 — 2026-08-30 (Sprint 1 / Mission 1.11.1)

Authorized by the Mission 1.11.1 brief §4 (resolve refusal observability before
implementing), §37 and §38 (real extraction over existing records), §51
(documentation) and §54 (stop after the report).

| Change | Section | Authority |
|--------|---------|-----------|
| **The pipeline reaches Signals, and five real ones exist** | Product Shape | Mission 1.11.1 §37, §38. `numeric-period-change@1.0.0` derived four from the six World Bank observations (two series, adjacent periods); `lexical-frequency-contrast@1.0.0` derived one from the two GDELT observations. Both deterministic, both offline, `derivation_confidence` 1.0. Eight raw and eight normalized records byte-for-byte unchanged |
| **PARTIAL was proven usable in production** | Engineering Principles | Mission 1.11.1 §22. Both GDELT inputs carry `PERIOD_TIMEZONE_NOT_ESTABLISHED` and `LANGUAGE_NOT_MAPPED`, neither is a fact a within-bucket contrast requires, and both contributed with **no withheld facts**. No quality string is branched on anywhere in either extractor: the model evaluates required facts against each record's own reasons |
| **A refused derivation gets a run record, never a Signal** | Engineering Principles | Mission 1.11.1 §4, [ADR-021](docs/architecture/adr/ADR-021-signal-derivation-run-log.md). `nlp.signal_derivation_runs` holds one row per **execution**, written in the same transaction as the signals it emitted: N considered, M derived, K refused and why. `research.research_jobs` was the closest existing home and has no result column and a different transaction. A redelivery writes a second run row and zero new signals, because the signals are what is idempotent |
| **H-32 is respected by construction, not by a check** | Blocked work | Mission 1.11.1 §16. The lexical extractor's grouping key carries the **exact bucket label**, so two buckets never share a group and no ordering between them is required, asserted or possible. No frequency change, growth, decline or rolling window exists, and no GDELT signal can carry a direction — enforced by a database CHECK as well as by the model |
| **Signal derivation became its own pipeline capability** | Product Shape | Mission 1.11.1 §43, §44. `SIGNAL_DERIVATION` sits between normalization and NLP extraction with a **derived** block, and `signal.derive` routes to the acquisition queue like `normalize.`. `NLP_EXTRACTION` stays blocked by D-12, whose stated reason — embedding model versioning — is true of classification and clustering and **false** of deterministic arithmetic. Planner version 1.3.0, the first change to the stage GRAPH |
| **The extractor computes and the model checks** | Engineering Principles | Mission 1.11.1 §5. `packages/signal-model` contains no extractor and `validate_signals.py` fails the build if one appears, walking the AST. Neither package may import a network client, a model or an embedder. D-03 and D-12 untouched: zero embeddings, claims, evidence, opportunities and scores |

## 1.16 — 2026-08-30 (Sprint 1 / Mission 1.11)

Authorized by the Mission 1.11 brief §32 (gap analysis before any persistence
change), §34 (model and schema changes only), §49 (documentation) and §51 (stop
before extractors).

| Change | Section | Authority |
|--------|---------|-----------|
| **A Signal is a DERIVATION, and one observation is not one** | Engineering Principles | Mission 1.11 §37, [ADR-020](docs/architecture/adr/ADR-020-signal-derivation-model.md). At least **two distinct source observations** must contribute, and distinctness is over `observation_key` rather than over the row id — counting rows would let a normalizer version bump manufacture a contrast out of one observation. Two rows sharing a key are refused as `AMBIGUOUS_OBSERVATION_LINEAGE`: **D-08 is failed closed on, not solved** |
| **The Signal family stops classifying demand** | Engineering Principles | Mission 1.11 §5, §6, GAP-2. `nlp.signals.signal_family` had CHECKed `PAIN / DESIRE / BEHAVIORAL / MARKET` since Mission 0.1, which asserted that every signal is evidence of demand. Neither derivation the two real sources support is: a GDELT term count may equally be a news event, a crisis, a celebrity or the weather. Renamed `quantity_family`, `LEXICAL_FREQUENCY | MEASURED_SERIES`. **Ontology V2 §3.6 is unchanged**; three things called "signal family" now have three names |
| **Order and global instant were separated, and neither is granted to GDELT** | Blocked work | Mission 1.11 §12, §13. `SOURCE_RELATIVE_ORDER` and `COMPARABLE_INSTANT` are different required facts needing different evidence. H-29 blocks the second; the new **H-32** blocks the first — the argument for granting it is an inference about GDELT's publication mechanism, not a retrieved statement, and H-32 is strictly weaker and separately answerable. Label EQUALITY needs no timezone, so a within-bucket contrast is derivable and a frequency change is not |
| **The database refuses what the documents forbid** | Engineering Principles | Mission 1.11 §34, §40. `observed_at` is `NULL` unless the basis is `COMPARABLE_INSTANTS`; a direction other than `NOT_APPLICABLE` requires an ordered basis; a `DETERMINISTIC` signal may carry no model version; a magnitude is `NUMERIC` and unbounded rather than a float on `[0,1]`. Thirteen constraints verified by the constraint that refused, in rolled-back transactions |
| **Two pre-existing defects closed, both named first** | Engineering Principles | Mission 1.11 §31, GAP-12 and GAP-13. `scoring.evidence.signal_id` was a single-column FK that migration 0005 left behind, so evidence in one workspace could name a signal in another. And the `demand_signal_type` entries `nlp.signals` pointed at were written only by a development seed, which made the table writable on a developer's machine and unwritable on the empty database CI starts from |
| **A registered signal type is vocabulary, and no extractor exists** | Forbidden During Foundation | Mission 1.11 §41. Two `signal_type` entries, each justified by records this repository holds. `SIGNAL_EXTRACTORS` is **empty**, `nlp.signals` and `nlp.signal_inputs` hold **0 rows**, and the eight real Raw and eight real Normalized records are byte-for-byte unchanged. No embedding, no cluster, no claim, no opportunity, no score |

## 1.15 — 2026-08-30 (Sprint 1 / Mission 1.10.1)

Authorized by the Mission 1.10.1 brief §39 (documentation), §25 (register only
after tests pass) and §42 (stop before signals).

| Change | Section | Authority |
|--------|---------|-----------|
| **A second source is normalized, and the first non-numeric shape exists in the database** | Product Shape | Mission 1.10.1 §27. `gdelt-web-ngram-lexical@1.0.0` produced two canonical lexical frequency observations from the two real RawRecords. Six World Bank normalized records are byte-for-byte unchanged, and the record kind, the value objects and every decision came from Mission 1.10 rather than being made while implementing |
| **Two known absences are stated per record rather than filled in** | Engineering Principles | Mission 1.10.1 §6, §8. Every GDELT normalized record is **PARTIAL**, carrying `PERIOD_TIMEZONE_NOT_ESTABLISHED` and `LANGUAGE_NOT_MAPPED`. **H-29 and H-30 stay open**; the exact source label and the exact CLD2 name survive, so answering either later is a normalizer version bump over records already held rather than a re-collection. `observed_at` and `content_language` are `NULL` |
| **Source text is preserved verbatim, and the helper that did not is separated** | Engineering Principles | Mission 1.10.1 §9. The first draft read the term through a trimming helper, so a term GDELT published with an edge space would have been stored as a different term — invisibly, in the payload, the fingerprint and the identity. `_source_text` (verbatim, for what the source said) is now distinct from `_text` (trimmed, for what this codebase wrote) |
| **A structural test greps the AST, never the prose** | Engineering Principles | Mission 1.10.1, `testing-strategy.md` §23. Two checks — never convert a timezone, embed no language table — failed on the docstrings that explain those very rules. The tempting fix is to weaken the assertion until it passes; the right one is to walk the imports, the attribute names and the string constants, which is stricter and cannot be defeated by an explanation |
| **`only_unnormalized` stayed meaningful when a second adapter arrived** | Engineering Principles | Mission 1.10.1 §26. The filter had been applied only when exactly one normalizer was registered and dropped otherwise — correct per record, because idempotent persistence classifies a re-read as UNCHANGED, and silently wrong in bulk: a workspace holding more raw records than the batch bound would re-read its first page every pass and never reach the rest. It now carries one lineage per adapter, matched on the collector that wrote the record |

## 1.14 — 2026-08-30 (Sprint 1 / Mission 1.10)

Authorized by the Mission 1.10 brief §14 (change the model only where the gap
analysis proves it necessary), §20 (documentation) and §22 (stop before the
normalizer).

| Change | Section | Authority |
|--------|---------|-----------|
| **The canonical model has a second shape, and the first one is untouched** | Engineering Principles | Mission 1.10 §6, [ADR-019](docs/architecture/adr/ADR-019-lexical-frequency-observation.md). `lexical_frequency_observation` — one occurrence count for one lexical term, one language, one period, and **no geography key at all**. Widening `numeric_observation` to fit would have let a World Bank record exist without a geography, which is the existing model getting worse for a new source's sake. The record-kind registry had its first real use and no table was altered |
| **A canonical period can say its timezone is unestablished** | Engineering Principles | Mission 1.10 §4. `ESTABLISHED` keeps timezone-aware bounds — the Mission 1.6 rule, unchanged and still enforced — and `NOT_ESTABLISHED` carries **naive** bounds, which is what a wall-clock reading with no zone actually is. `observed_at` becomes `NULL` rather than an invented offset. Serialised only when it is not `ESTABLISHED`, so every payload written before this is byte-identical |
| **A canonical language can stay unmapped, visibly** | Engineering Principles | Mission 1.10 §5. `CanonicalLanguage`, shaped after `CanonicalGeography`: source label, source scheme, mapping state, canonical tag. `unmapped()` is the counterpart of `unclassified()`, and the constructor refuses a tag without a mapping and a mapping without a tag. **Resemblance is not a mapping** — `ENGLISH` looks like `en`, and the first CLD2 name that does not would be silently wrong |
| **Two open questions became statable rather than papered over** | Blocked work | Mission 1.10 §4, §5. **H-29** (the GDELT bucket timezone) and **H-30** (no CLD2-to-tag mapping) both stay open, and the model changes exist so a record can *say* they are open. Answering either later is a normalizer version bump over records already held, not a re-collection |
| **A vocabulary entry is not an adapter** | Forbidden During Foundation | Mission 1.10 §22. Migration 0011 inserts the record-kind row so the model can describe the shape and the database can refuse an unregistered one. `NORMALIZER_REGISTRY` and `IMPLEMENTED_NORMALIZERS` gained **nothing**, no GDELT record was normalized, and the standing rule was sharpened rather than broken: a kind exists because DATA exists; an adapter exists because CODE exists |

## 1.13 — 2026-08-30 (Sprint 1 / Mission 1.9.3)

Authorized by the Mission 1.9.3 brief §61 (documentation), §40 (register the
collector only after the tests pass) and §43 (deliberate enablement for one
controlled acquisition).

| Change | Section | Authority |
|--------|---------|-----------|
| **A second collector exists, and the first for a non-economic source** | Product Shape | Mission 1.9.3 §40. `gdelt-web-ngram@1.0.0` streams a published gzipped file, parses four columns strictly and persists one RawRecord per row. It was added to `IMPLEMENTED_COLLECTORS` as the LAST step, after its conformance suite passed — the same order Mission 1.5 used. Eligible, resource-ready, implemented and enabled remain four separate facts, and GDELT satisfied them in that order across three missions |
| **`acquisition.raw_records` holds a second source** | Product Shape | Mission 1.9.3 §51. One controlled real acquisition: one reviewed file, one explicit source bucket, a two-term lexical filter, **223,342 rows scanned and 2 persisted**. The scan count is reported alongside the match count because saying only "2" would describe a file that does not exist. Six World Bank records are byte-for-byte unchanged |
| **Streaming acquisition entered the transport, bounded three ways** | Engineering Principles | Mission 1.9.3 §13, §14. `StreamingTransport.download` is a second entry point enforcing the same host allowlist, https requirement and redirect refusal as `get` — a second door that checked less would be the escape the first one closes. Compressed bytes, decompressed bytes and line length are separate ceilings; the middle one catches amplification the first cannot see, and the third catches a file with no newline that every other bound reads as satisfied. **All three are `INTERNAL_SAFETY_POLICY` and travel into provenance labelled as ours** |
| **A live smoke test found what 105 fixture tests could not** | Engineering Principles | Mission 1.9.3 §50, `testing-strategy.md` §20. `observation_key` refused any part containing its `\|` separator — safe while every part was an identifier or a year, and wrong the moment a source published real text. News contains pipes, so GDELT does, and the parser was discarding a whole file of legitimate observations. **The separator is escaped now rather than forbidden**: skipping rows would drop real data for an internal format, there is no character to move the separator to, and hashing would remove the readability the key exists for. No committed key changed, and a test asserts it |
| **A latent provenance defect surfaced when a source had two routes** | Engineering Principles | Mission 1.9.3 §10, §27. `build_raw_record` read `context.access[0]`, correct while one source had one profile. GDELT's first profile is the **deferred** DOC API, so every WEB-NGRAM record would have recorded `PUBLIC_API` on `api.gdeltproject.org` for a file downloaded over `DATASET_DOWNLOAD` from elsewhere. The access route is now a required argument rather than an inference |
| **GDELT is enabled in this deployment; it is still not normalizable** | Forbidden During Foundation | Mission 1.9.3 §43, §56. Enabled through `sros-source enable`, never by direct SQL. **No GDELT normalizer exists**, `NormalizedRecords` for it are zero, and World Bank remains the only normalized source. `COUNT` is what GDELT counted: no signal, no embedding, no claim, no evidence and no score was produced from it |

## 1.12 — 2026-08-30 (Sprint 1 / Mission 1.9.2)

Authorized by the Mission 1.9.2 brief §32 (documentation), §3 (a new review
version rather than a rewrite) and §10 (gap analysis before the profile changed).
Additive: reviews 1 and 2 are untouched and no verdict moved.

| Change | Section | Authority |
|--------|---------|-----------|
| **A source has a concrete authorized resource for the second time** | Product Shape | Mission 1.9.2 §7, §22. GDELT review 3 authorises `web-ngrams/1gram` and `web-ngrams/2gram` over a reviewed `DATASET_DOWNLOAD` route on one directory of `data.gdeltproject.org`. `context.datasets` had been empty since Mission 1.7, so every GDELT resource failed closed — correctly, on a question nobody had answered. **No collector was written, none is enabled, and zero GDELT records exist** |
| **Resource-ready is a fourth fact, separate from eligible, implemented and enabled** | Forbidden During Foundation | Mission 1.9.2 §23. A source can pass the eligibility gate while every resource it could ask for is refused, and for two missions "eligible" was the most specific word available for GDELT in exactly that state. `sros-source readiness` derives all four and stores none — a persisted copy of a derivation is the thing `source-registry-v1.md` §3 refuses for eligibility |
| **How much became a governance question, alongside what** | Engineering Principles | Mission 1.9.2 §15. GDELT publishes two files every fifteen minutes since 2019 and its terms limit none of it, so a reviewed ceiling exists in configuration where it can be checked (`max_files_per_job`), and a bound with no stated basis is refused at load time. **`None` means no ceiling was reviewed, not that any size is fine** — every earlier source is in that state, and spelling it `unlimited` would turn an unasked question into an answer |
| **Two silent holes in the resource gate were closed** | Engineering Principles | Mission 1.9.2 §22. An **unestablished rights basis** had been checked only inside the licence-allowlist rule, so a descriptor with no basis passed for every source enumerating no licences — including GDELT, the one source authorised by a direct grant. And `require_dataset_family` refused a resource that could not say what it is while admitting one that said something nobody had reviewed. Both were reachable only by a hand-made descriptor, which is the standing the transport's host check already has |
| **The DOC API route is deferred, not withdrawn** | Blocked work | Mission 1.9.2 §24. **H-27 is still open** and no timeline envelope has ever been observed. The profile, the capture script and the response-contract document are all kept, because deleting them would make a later un-deferral look like a new approval. **H-28 is resolved** in both halves: the model in Mission 1.9.1, the entries here |
| **A first-party claim from Mission 1.9.1 was corrected** | Authoritative Documents | Mission 1.9.2 §4. GDELT does ask researchers to use "these ngram files instead of the search APIs", and Mission 1.9.1 read that as support for WEB-NGRAM. The sentence is in the post announcing the **quadgram** dataset and refers to that one, which review 3 rejects for carrying `title`, `img`, `url` and a per-document `DOCID`. The half that stands is GDELT describing its own legacy search infrastructure as struggling, which is why the DOC API is deferred |

## 1.11 — 2026-08-30 (Sprint 1 / Mission 1.8)

Authorized by the Mission 1.8 brief §3 (PyPI resolution), §4 (do not generalise
the exception) and §30 (documentation).

| Change | Section | Authority |
|--------|---------|-----------|
| **Silence is not permission became a mechanism** | Engineering Principles | Mission 1.8 §4, `source-registry-v1.md` §1 rule 8. The rule had existed as prose since Mission 1.0 and nothing read it; Mission 1.7 approved a source with four of the six materially required activities recorded `NOT_ADDRESSED`, on a review whose own notes described the basis as "the absence of a prohibition covering us plus the presence of a documented API". `validate_source_registry` now enforces it, and the check was written against the uncorrected catalog so it could be seen to fail first |
| **Three Mission 1.7 approvals were withdrawn on audit** | Product Shape | Mission 1.8 §3. `pypi`, `npm-registry` and `wikimedia-pageviews` each rested on silence rather than on a grant. Nothing about the platforms changed; the reading of their documents did. Five sources are approving where eight were, and every superseded review is preserved |
| **A second source became collector-eligible** | Product Shape | Mission 1.8 §7, §18. `gdelt` joins `world-bank`, `eurostat` and `fred` — the first non-economic source to reach the gate. Its one reviewed obligation moved from `HUMAN_CONFIRMATION`, which no verifier can clear, to a `CAPABILITY` checked by the generic attribution verifier Mission 1.4 built. **No gate was relaxed and no collector was implemented** |
| **The portfolio got narrower, and that is reported rather than smoothed** | Product Shape | Mission 1.8 §23. The economic share of approving sources rose from 37% to 60%, `entertainment` lost its only approving source, and eight of sixteen signal families now have none. A coverage number that improves when the governance behind it gets stricter is measuring the wrong thing |

## 1.10 — 2026-08-30 (Sprint 1 / Mission 1.7)

Authorized by the Mission 1.7 brief §48 (documentation) and §47 (schema changes
only after a gap analysis). Additive: no existing verdict was rewritten.

| Change | Section | Authority |
|--------|---------|-----------|
| **The source universe is 27 sources across 14 families, and consumer families are represented** | Product Shape | Mission 1.7 §50. Fourteen candidates were added and every one carries a current review; `gaming`, `creator` and `knowledge` are new families. The registry is no longer biased toward economic and developer data *as a catalog* |
| **Every consumer-facing family is registered and none is approving** | Product Shape | Mission 1.7 §40, and the finding the expansion exists to surface. `social`, `community`, `gaming`, `creator` and `app_store` hold eleven sources between them and not one reaches an approving state. That is a fact about platform terms, not about the review, and it is measurable rather than asserted: `source-signal-coverage-v1.md` is generated from the registry and CI-checked |
| **Source signal coverage is a first-class, non-scoring attribute** | Engineering Principles | Mission 1.7 §4, [ADR-017](docs/architecture/adr/ADR-017-source-signal-coverage.md). Sixteen signal families, each projecting the canonical `user_motivation` entry it corresponds to where one exists. Behaviour coverage reuses Ontology V2 §3.4 unchanged and defines no second vocabulary. **Coverage is potential, never permission, and carries no weight of any kind** — a numeric column here would be D-03 by another name |
| **The canonical taxonomies are fully seeded** | Extensible Taxonomies | Ontology V2 §3.3 and §3.4 specify seventeen motivations and seventeen behaviours as initial canonical entries; migration 0004 had loaded three and one. The remainder arrived in 0010 as `INSERT`s, which is what §14.3 requires of a registry |

**Unchanged, deliberately:** no collector was implemented, no platform content
was collected, no source became collector-eligible, evidence aggregation remains
uncalibrated and D-12 is still open.

## 1.9 — 2026-08-30 (Sprint 1 / Mission 1.6)

Authorized by the Mission 1.6 brief §61 (documentation) and §57 (schema changes
only where the existing semantics are genuinely incompatible).

| Change | Section | Authority |
|--------|---------|-----------|
| `docs/data/normalized-record-v1.md` added to the authoritative chain | Authoritative Documents | Mission 1.6 §5, §61. It defines the canonical observation every later stage reads, so every signal, claim and score eventually rests on it |
| `docs/data/world-bank-normalizer-v1.md` added to the authoritative chain | Authoritative Documents | Mission 1.6 §61. The reference adapter, and the record of what may and may not be inferred while producing a canonical observation |
| **The Raw to Normalized boundary exists, and one source crosses it** | Product Shape | Mission 1.6 §37, §38. `acquisition.normalized_records` holds six canonical numeric observations derived from the six real World Bank raw records. Every one carries complete lineage, its attribution obligation, a governance-resolved expiry and a structural quality state |
| **Normalizable is a fourth fact, separate from eligible, enabled and implemented** | Forbidden During Foundation | Mission 1.6 §36. A collector says what was fetched; a normalizer says what it structurally represents, and one never implies the other. Eurostat is collector-eligible with neither |

## 1.8 — 2026-08-30 (Sprint 1 / Mission 1.5)

Authorized by the Mission 1.5 brief §55 (documentation) and §51 (schema changes
only where the existing model cannot represent the requirement).

| Change | Section | Authority |
|--------|---------|-----------|
| `docs/data/world-bank-collector-v1.md` added to the authoritative chain | Authoritative Documents | Mission 1.5 §55. It is the reference architecture every later collector follows, and the record of what one source's data may be used for |
| **The first collector exists, and one source is collected from** | Forbidden During Foundation | Mission 1.5 §3, §48. Sprint 0 forbade collectors during foundation; Sprint 0 is complete and the governance chain that had to precede one (D-07, the compliance layer, the authorization boundary) is in place. **World Bank only.** Eurostat is collector-eligible and deliberately has no collector |
| **`acquisition.raw_records` is no longer empty** | Product Shape | Mission 1.5 §48, §49. One controlled acquisition of six World Bank observations. Every record carries complete provenance, a governance-derived expiry and its attribution obligation |

## 1.7 — 2026-08-29 (Sprint 1 / Mission 1.4)

Authorized by the Mission 1.4 brief §41 (documentation) and §40 (schema
changes only where the existing model cannot express the requirement).

| Change | Section | Authority |
|--------|---------|-----------|
| `docs/data/acquisition-authorization-v1.md` added to the authoritative chain | Authoritative Documents | Mission 1.4 §41. `source-registry-v1.md` §4 requires conditions to be checkable and specifies no mechanism for checking one; this document specifies it, and every future collector is gated by it |
| **Collector eligibility is reachable, and two sources reach it** | Blocked work | Mission 1.4 §23, [ADR-016](docs/architecture/adr/ADR-016-compliance-capabilities-and-acquisition-authorization.md). `world-bank` and `eurostat` pass the gate in a verified environment; `fred` is design-eligible and blocked on a runtime credential. **No collector is implemented and none is enabled** — three separate facts, and the block on writing a collector moved from "no source has passed" to "this specific source has not" |

## 1.6 — 2026-08-29 (Sprint 1 / Mission 1.2)

Authorized by the Mission 1.2 brief §3 (create Ontology V2.1) and §49
(documentation). A-13 was explicitly authorised for resolution.

| Change | Section | Authority |
|--------|---------|-----------|
| `docs/domain/opportunity-ontology-v2.1.md` becomes the current ontology | Authoritative Documents | Mission 1.2 §3. V2 is retained as a historical record and is not deleted; V2.1 inherits §1–§16 unchanged and adds §17 (Claim) |
| `docs/domain/claim-model-v1.md` added to the authoritative chain | Authoritative Documents | Mission 1.2 §49. The Claim is the unit `evidence-aggregation-framework-v1.md` operates on, so its model is authoritative by construction |
| **A-13 resolved** | Blocked work | Mission 1.2 §44, [ADR-015](docs/architecture/adr/ADR-015-claim-persistence-and-versioning.md). Claim exists as a persisted entity with stable identity and append-only revisions; evidence references it. **Production scoring remains unavailable**: no `CALIBRATED` profile exists, which is a separate gate |

## 1.5 — 2026-08-29 (Sprint 1 / Mission 1.1)

Authorized by the Mission 1.1 brief §48 (documentation) and §40 (D-03 resolution
criteria).

| Change | Section | Authority |
|--------|---------|-----------|
| `docs/domain/evidence-aggregation-framework-v1.md` added to the authoritative chain | Authoritative Documents | Mission 1.1 §48. `scoring-framework-v1.1.md` §13 names this document as the precondition for `services/scoring`, so it is authoritative by construction |
| **D-03 resolved at the FRAMEWORK level** | Blocked work | Mission 1.1 §40, [ADR-014](docs/architecture/adr/ADR-014-evidence-aggregation-reference-implementation.md). The algorithm is defined and has a reference implementation. **No parameter was calibrated**, no profile is `CALIBRATED`, and `services/scoring` stays unavailable for production research. Framework Defined and Profile Calibrated are separate gates |
| **A-13 opened** | Blocked work | Aggregation is claim-centric and no Claim entity exists in the ontology or the schema. Recorded rather than resolved: it requires an ontology version and an ADR |

## 1.4 — 2026-08-29 (Sprint 1 / Mission 1.0)

Authorized by the Mission 1.0 brief §40 (documentation) and §45 (decision
resolution). Additive, plus one resolution.

| Change | Section | Authority |
|--------|---------|-----------|
| `docs/data/source-registry-v1.md` added to the authoritative chain | Authoritative Documents | Mission 1.0 §40. `data-principles.md` §13 requires a pre-integration record for every source and specifies no structure for it; this document specifies it, and every future collector is gated by it |
| **D-07 resolved** | Blocked work | Mission 1.0 §45. The source registry and its per-source review records now exist ([ADR-013](docs/architecture/adr/ADR-013-source-registry-governance.md)). Resolution of the blocker is not approval of any source: thirteen candidates are registered and zero are collector-eligible |

## 1.3 — 2026-08-29 (Sprint 0 / Mission 0.4)

Authorized by the Mission 0.4 brief §24 (create the evaluation framework) and
§39 (documentation). Additive only: no existing statement is changed.

| Change | Section | Authority |
|--------|---------|-----------|
| `docs/ai/evaluation-framework-v1.md` added to the authoritative chain | Authoritative Documents | Mission 0.4 §24. `llm-reasoning-rules.md` §10 requires evaluation datasets and defines none; this document specifies them, so leaving it outside the chain would put an authoritative-by-nature document where the boot sequence never looks |

## 1.2 — 2026-08-27 (Sprint 0 / Mission 0.1.2)

Authorized by explicit human decision. See
`docs/architecture/mission-0.1.2-decisions.md`.

| Change | Section | Authority |
|--------|---------|-----------|
| Authoritative ontology becomes **V2** | Authoritative Documents | Ontology V2 — resolves D-01, A-06, A-11, A-05, A-07, A-08 |
| Research lifecycle named: `ResearchProject` → `ResearchSession` (+ `ResearchContext` snapshot) | Product Shape | Ontology V2 §11 |
| `research run` retired as a domain term | Product Shape | Ontology V2 §11.5 |
| Domain taxonomies split into closed enums and extensible registries | Engineering Principles | Ontology V2 §14 |

## 1.1 — 2026-08-27 (Sprint 0 / Mission 0.1.1)

Authorized by explicit human decision. See
`docs/architecture/mission-0.1.1-decisions.md` for the full register.

| Change | Section | Authority |
|--------|---------|-----------|
| **BullMQ removed** from the locked stack; **Celery** added as the job framework | Technology Stack | ADR-004 — resolves the blocking contradiction C-01 |
| Multi-tenancy stated as a foundational property | Product Shape (new) | ADR-005 |
| Authoritative document chain points to ontology **V1.1** and scoring **V1.1** | Authoritative Documents | Mission 0.1.1 §7–8 |
| Data Retention Policy V1 added as authoritative | Authoritative Documents | Mission 0.1.1 §12 |
| LLM access declared provider-agnostic | Technology Stack | ADR-006 |
| Deployment declared local-first | Technology Stack | ADR-007 |

## 1.0 — initial foundation manifest

---

# Vision

Startup Research OS is an AI-powered Opportunity Research Engine.

Its purpose is to discover, analyze, score, validate and plan digital product opportunities across every major market.

The system must support opportunities in:

- B2B
- B2C
- Gaming
- Entertainment
- Education
- AI
- Creator Economy
- Developer Tools
- Social Products
- Utility Apps
- Marketplaces
- Hobby Products

The system is evidence-driven.

It is NOT a random startup idea generator.

---

# Mission

Transform public market signals into structured opportunity intelligence.

Pipeline:

Raw Signals
→ Data Collection
→ Normalization
→ NLP
→ Signal Extraction
→ Opportunity Discovery
→ Evidence Evaluation
→ Scoring
→ Market Intelligence
→ Competition Analysis
→ Execution Planning

---

# Success Criteria

The platform must eventually be able to:

- discover opportunities automatically
- explain why an opportunity exists
- distinguish observations from hypotheses
- rank opportunities
- adapt scoring to different markets
- generate MVP plans
- generate Go-To-Market strategies
- continuously improve from collected data

---

# Engineering Principles

Every implementation must follow these principles.

## Evidence First

Evidence before conclusions.

## Explainability

Every important score should be explainable.

## Version Everything

Foundational specifications are versioned.

## Modular Design

Every service must have a single responsibility.

## Extensible Taxonomies

Domain taxonomies are registries, not database enums. Adding a product type, a
motivation or a distribution channel must never require a schema migration.
Closed enums are reserved for values that code branches on exhaustively.
See Ontology V2 §14.

## Testability

Every important behavior must be testable.

## Security First

Security cannot be postponed.

## Cost Awareness

Choose the simplest reliable solution before expensive AI calls.

---

# Authoritative Documents

These documents define the project.

1. PROJECT_MANIFEST.md
2. docs/CLAUDE.md
3. docs/domain/opportunity-ontology-v2.2.md
4. docs/domain/scoring-framework-v1.1.md
5. docs/domain/evidence-confidence-framework-v1.md
6. docs/ai/llm-reasoning-rules.md
7. docs/data/data-principles.md

Additionally authoritative:

- docs/data/data-retention-policy-v1.md
- docs/ai/evaluation-framework-v1.md (added in 1.3)
- docs/data/source-registry-v1.md (added in 1.4)
- docs/domain/evidence-aggregation-framework-v1.md (added in 1.5)
- docs/domain/claim-model-v1.md (added in 1.6)
- docs/data/acquisition-authorization-v1.md (added in 1.7)
- docs/data/world-bank-collector-v1.md (added in 1.8)
- docs/data/normalized-record-v1.md (added in 1.9)
- docs/data/world-bank-normalizer-v1.md (added in 1.9)
- Accepted ADRs in docs/architecture/adr/

No implementation may silently contradict them.

## Superseded specifications

The following are **historical records**, retained for traceability. They are no
longer current and must not be used as the basis for implementation:

- `docs/domain/opportunity-ontology-v1.md` — superseded by V1.1
- `docs/domain/opportunity-ontology-v1.1.md` — superseded by V2
- `docs/domain/opportunity-ontology-v2.md` — superseded by V2.1. V2.1 inherits
  §1–§16 unchanged and refers to V2 for their text, so a reference to
  `opportunity-ontology-v2.md §N` with `N <= 16` still resolves correctly
- `docs/domain/opportunity-ontology-v2.1.md` — superseded by V2.2. V2.2 inherits
  V2.1 in full and amends **one sentence** (§17.3: a Claim belongs to at most one
  Opportunity, and may belong to none), so every other reference to
  `opportunity-ontology-v2.1.md §N` resolves unchanged in V2.2
- `docs/domain/scoring-framework-v1.md` — superseded by V1.1

Historical reports and audits (`docs/architecture/mission-0.1-report.md`,
`docs/architecture/specification-audit.md`) legitimately reference V1 and the
pre-1.1 stack. They are records of what was true when they were written and are
not rewritten.

---

# Technology Stack

Frontend:
- Next.js
- TypeScript
- Tailwind
- shadcn/ui

Backend:
- FastAPI
- Python

Jobs and asynchronous work (amended in 1.1 — ADR-004):
- Celery
- Redis as broker and result backend

Infrastructure:
- Docker
- Docker Compose (local-first — ADR-007)
- Turborepo
- pnpm

Storage:
- PostgreSQL
- Redis
- Qdrant

Data:
- Playwright (Python API)

AI access (ADR-006):
- Provider-agnostic LLM Gateway
- No business service depends on a provider-specific SDK
- Logical tiers: FAST_MODEL, BALANCED_MODEL, STRONG_MODEL, EMBEDDING_MODEL

ML:
- BGE-M3
- HDBSCAN

## Runtime boundaries

TypeScript is used for the frontend only (`apps/web`, `packages/*`).

Python is the primary backend, data, jobs and ML runtime. There is no Node
worker tier.

**Removed in 1.1:** BullMQ. It is a Node-only library and could not be consumed
by the Python workers that the ML stack requires. See ADR-004 for the full
rationale.

---

# Product Shape

Added in 1.1.

Startup Research OS is a **multi-tenant SaaS**, designed as such from the
foundation. The tenant boundary is the **Workspace**:

```text
User → Workspace → ResearchProject → ResearchSession → Opportunity
                                          |
                                          +-- ResearchContext snapshot
```

Every primary domain resource carries `workspace_id`. Authentication and
authorization are not yet implemented; the contracts that allow them to be added
without a data migration are established in ADR-005.

**Canonical lifecycle names (Ontology V2 §11).** `ResearchProject` is the
persistent research objective. `ResearchSession` is the **only** persisted
execution entity. `ResearchContext` is an input specification stored as an
immutable snapshot on the session, not an independent entity. The term
`research run` is retired; historical documents that use it mean
`ResearchSession`.

---

# Repository Philosophy

The repository should always remain understandable.

Folders must have clear ownership.

Documentation is considered production code.

Every architectural decision must eventually be documented through ADRs.

---

# Forbidden During Foundation

Until Sprint 0 is complete:

Do NOT implement:

- business logic
- collectors
- NLP pipelines
- scoring algorithms
- dashboards
- authentication features
- monetization
- user-facing workflows

Foundation only.

## Status of this list (amended in 1.9)

Sprint 0 is complete, and two entries have been reached in Sprint 1. They are
recorded here rather than struck out, because what unblocked them is specific
and the rest of the list is still in force.

**Collectors.** One exists, for one source, since Mission 1.5. It became
permissible only after the chain that had to precede it: the Source Registry
(D-07, Mission 1.0), the review round that produced an approving verdict on
evidence (1.3), and the compliance capabilities and authorization boundary that
make a collector unable to run without a governance decision behind it (1.4). A
collector for a source that has not been through that chain is still forbidden,
and the orchestrator refuses to plan one.

**Normalization**, added in 1.9, is not on this list and never was: the
forbidden entry is *NLP pipelines*, and normalization is the stage before one.
It maps a source observation to a canonical structure and stops. It performs no
tokenization, no embedding, no classification and no clustering, and CI asserts
each of those mechanically rather than by review.

**Deterministic signal derivation**, added in 1.11.1, is not on this list and
never was: the forbidden entry is *NLP pipelines*, and these two extractors
tokenize nothing, embed nothing, classify nothing and cluster nothing. They
subtract exact decimals and compare exact labels. `validate_signals.py` asserts
each of those mechanically by walking every import.

**Pairwise GDELT frequency change was implemented in 1.12.1**, with a gap policy
and a rule for a missing bucket (ADR-023). **Rolling windows, moving averages
and momentum are still not written**: each needs its own decision about what a
gap means for that operation, and temporally permitted is still not extractor
specified.

**Cross-source temporal alignment stays forbidden** while H-29 is open, along
with `observed_at`, `TIMESTAMPTZ` conversion and any wall-clock "as of" claim.
Classification, embedding and clustering stay blocked by D-12.

**Deterministic OBSERVED claim interpretation was implemented in 1.13.1**, by
`observed-signal-restatement@1.0.0` and by nothing else, against the Mission
1.13 contract rather than by revising it. Seven real Claims exist.

**`INFERRED`, `PREDICTED` and `RECOMMENDED` generation is still forbidden**, and
is not partially written: there is no module, no branch and no parameter that
would select one. An inference needs a stated reasoning step, and adding one is
a version bump with a document behind it. `validate_claims.py` fails the build
on any non-`OBSERVED` claim type constructed in the interpretation package, over
the AST.

**`MODEL_DERIVED` remains unused**, and the layer imports no model, network
client or embedder — asserted over every import.

**Opportunity formation stays forbidden.** Making `opportunity_id` nullable
removed a precondition; it granted no permission, and Mission 1.13.1 created no
Opportunity. An Opportunity groups Claims that describe one addressable thing,
and deciding which Claims those are is a mission of its own.

**The seven Claims establish nothing about a market.** No pain, no desire, no
willingness to pay, no pricing power, no competition gap, no distribution
feasibility, no retention, no revenue potential. They are factual, source-level
claims about two publications, and every Evidence row behind them is
`NON_SCORABLE` today.

**Reliability is governed since 1.14 and no value has been reviewed.** The
contract, the scope, the basis requirement, the versioning and the fail-closed
resolver exist; `epistemic.reliability_assessments` holds zero rows. Writing one
would have meant a model standing in for a reviewer, which the mission forbids
and which is worse than producing no score. A reviewer needs three assessments —
one per scope in use — and `evidence-reliability-review-guide-v1.md` §9 says what
documents each would require.

**Reliability does not solve missing evidence families.** Even a reviewed value
for all seven rows decides whether the evidence the system HAS can be scored. It
says nothing about whether that evidence bears on anything anybody wants to
know.

**Everything else on the list is unchanged.** NLP pipelines are blocked by D-12,
scoring algorithms by the absence of a `CALIBRATED` profile, and authentication
by ADR-005 being unimplemented.

---

# Required Mindset

Act like a long-term engineering team.

Prioritize maintainability over speed.

When uncertain:

- inspect
- explain
- propose
- document

Never silently invent architecture.